#!/usr/bin/env python3
# GenSource build_graph v0.10.1 - 图实体化投影：账本 -> knowledge_graph/{nodes,edges}.json
# 铁律：图 = f(账本)，LLM 不写图。gate 每次跑自动重投影 + E56-E59 校验。
# 本脚本只做 100% 确定性投影（读账本 -> 排序 -> 写 JSON），零语义判断（doc 99）。
import argparse, csv, hashlib, json, os, re, sys

ID_RE = re.compile(r'C-\d{5}-\d{5}-[0-9a-f]{8}')

def read_tsv(path):
    rows = []
    if not os.path.isfile(path):
        return []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='\t'):
            if not r or all(c == '' for c in r):
                continue
            rows.append([c.strip() for c in r])
    return rows

def col_opt(h, name):
    try:
        return h.index(name)
    except ValueError:
        return None

def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def edge_id(edge_type, frm, to, attrs):
    return hashlib.md5((edge_type + '|' + frm + '|' + to + '|' + canon(attrs)).encode()).hexdigest()[:16]

def build(session, write=False):
    """确定性投影。返回 (nodes, edges) 已排序 list。write=True 时写 knowledge_graph/ 两文件。"""
    S = session
    sink = read_tsv(os.path.join(S, 'sink_inventory.tsv'))
    src = read_tsv(os.path.join(S, 'source_inventory.tsv'))
    finv = read_tsv(os.path.join(S, 'file_inventory.tsv'))
    led = read_tsv(os.path.join(S, 'check_point_ledger.tsv'))
    cand = read_tsv(os.path.join(S, 'candidates.tsv'))
    fe = read_tsv(os.path.join(S, 'flow_edges.tsv'))
    pr = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
    mf = []
    mfp = os.path.join(S, 'findings', 'machine-fields.json')
    if os.path.isfile(mfp):
        try:
            mf = json.load(open(mfp, encoding='utf-8'))
        except Exception as ex:
            # v0.11.0 (E-13): 解析失败必须中止投影（不静默置空）
            print('FATAL: machine-fields.json parse failed: %s' % str(ex)[:120])
            raise SystemExit(1)
    mf_map = {}
    if isinstance(mf, list):
        for x in mf:
            if isinstance(x, dict) and x.get('candidate_id'):
                mf_map[str(x['candidate_id'])] = x

    sir = sink[1:] if len(sink) > 1 else []
    sor = src[1:] if len(src) > 1 else []
    fir = finv[1:] if len(finv) > 1 else []
    ledh = led[0] if led else []
    ledr = led[1:] if len(led) > 1 else []
    ch = cand[0] if cand else []
    cr = cand[1:] if len(cand) > 1 else []
    fer = fe[1:] if len(fe) > 1 else []
    prh = pr[0] if pr else []
    prr = pr[1:] if len(pr) > 1 else []

    sink_ids, src_ids = set(), set()
    pr_scopes = []
    if prh:
        o_i, c_i, s_i = col_opt(prh, 'operator'), col_opt(prh, 'criterion'), col_opt(prh, 'scope')
        for r in prr:
            if o_i is not None and s_i is not None and len(r) > max(o_i, s_i) and r[o_i] and r[s_i]:
                crit = r[c_i] if c_i is not None and len(r) > c_i else ''
                pr_scopes.append((r[o_i], crit, r[s_i]))

    from collections import defaultdict
    led_by_basis = defaultdict(list)
    for r in ledr:
        if len(r) > 5 and r[0]:
            led_by_basis[r[0]].append(r)

    def basis_status(basis_id, node_type, type_key):
        for (op, crit, scope) in pr_scopes:
            # v0.10.1 自然拼接：sink_type 原值自带 SINK- 前缀；S2 scope=sink_type，S3 scope=sink_type-via-fn
            if node_type == 'sink' and (scope == type_key or scope.startswith(type_key + '-via-')):
                return ('pruned', op, crit or scope)
            if node_type == 'source' and scope == 'SOURCE-' + type_key:
                return ('pruned', op, crit or scope)
        rows = led_by_basis.get(basis_id, [])
        if not rows:
            return ('unchecked', '', '')
        terms = [r[5] for r in rows]
        if terms and all(t in ('disproved', 'not_applicable') for t in terms):
            reasons = sorted(set(r[6] for r in rows if len(r) > 6 and r[6]))
            return ('pruned', '', ';'.join(reasons)[:200])
        if terms and all(t == 'blocked' for t in terms):
            # v0.11.0 (M13): 全行 blocked -> 节点 blocked（原误归 unchecked）
            return ('blocked', '', '')
        if any(t in ('candidate', 'confirmed') for t in terms):
            return ('candidate', '', '')
        return ('unchecked', '', '')

    nodes = []
    for r in sir:
        if len(r) < 3 or not r[0]:
            continue
        sid = r[0]
        sink_ids.add(sid)
        st, pb, prn = basis_status(sid, 'sink', r[2])
        n = {'id': 'sink:' + sid, 'type': 'sink',
             'attrs': {'file_line': r[1] if len(r) > 1 else '', 'sink_type': r[2], 'symbol': r[3] if len(r) > 3 else ''},
             'status': st}
        if st == 'pruned' and pb:
            n['pruned_by'] = pb
        if st == 'pruned' and prn:
            n['pruned_reason'] = prn
        nodes.append(n)
    for r in sor:
        if len(r) < 3 or not r[0]:
            continue
        sid = r[0]
        src_ids.add(sid)
        st, pb, prn = basis_status(sid, 'source', r[2])
        n = {'id': 'source:' + sid, 'type': 'source',
             'attrs': {'file_line': r[1] if len(r) > 1 else '', 'entry_type': r[2], 'symbol': r[3] if len(r) > 3 else ''},
             'status': st}
        if st == 'pruned' and pb:
            n['pruned_by'] = pb
        if st == 'pruned' and prn:
            n['pruned_reason'] = prn
        nodes.append(n)
    for r in fir:
        if len(r) < 2 or not r[0]:
            continue
        nodes.append({'id': 'file:' + r[0], 'type': 'file',
                      'attrs': {'lang': r[2] if len(r) > 2 else '', 'type': r[1] if len(r) > 1 else ''},
                      'status': 'active'})
    cpidx = {}
    if ledh:
        for k in ('basis_id', 'direction', 'mechanism', 'check_point_id', 'candidate_ids', 'terminal_state', 'reason'):
            v = col_opt(ledh, k)
            if v is not None:
                cpidx[k] = v
    def cell(row, key, default=''):
        return row[cpidx[key]] if key in cpidx and len(row) > cpidx[key] else default
    for r in ledr:
        if not ledh or len(r) < 4:
            continue
        cp_id = cell(r, 'check_point_id')
        if not cp_id:
            continue
        nodes.append({'id': 'checkpoint:' + cp_id, 'type': 'checkpoint',
                      'attrs': {'direction': cell(r, 'direction'), 'mechanism': cell(r, 'mechanism'), 'basis_id': cell(r, 'basis_id')},
                      'status': cell(r, 'terminal_state')})
    loc_to_sids = {}
    for r in sir:
        if len(r) > 1 and r[1]:
            loc_to_sids.setdefault(r[1], []).append(r[0])
    ci = {}
    if ch:
        for k in ('candidate_id', 'location', 'sink_type', 'severity_hypothesis_initial', 'root_cause_group_id', 'verdict', 'report_record_ref'):
            v = col_opt(ch, k)
            if v is not None:
                ci[k] = v
    def ccell(row, key, default=''):
        return row[ci[key]] if key in ci and len(row) > ci[key] else default
    for r in cr:
        if not ci or len(r) < 2:
            continue
        cid = ccell(r, 'candidate_id')
        if not cid:
            continue
        nodes.append({'id': 'candidate:' + cid, 'type': 'candidate',
                      'attrs': {'location': ccell(r, 'location'), 'sink_type': ccell(r, 'sink_type'),
                                'severity': ccell(r, 'severity_hypothesis_initial'), 'rcg_id': ccell(r, 'root_cause_group_id')},
                      'status': ccell(r, 'verdict')})
        ref = ccell(r, 'report_record_ref')
        if ref:
            fm = mf_map.get(cid, {})
            nodes.append({'id': 'finding:' + ref, 'type': 'finding',
                          'attrs': {'candidate_id': cid, 'severity': fm.get('severity', ''),
                                    'confidence': fm.get('confidence', ''), 'evidence_grade': fm.get('evidence_grade', '')},
                          'status': 'active'})

    edges, eset = [], set()
    def add_edge(t, frm, to, attrs):
        eid = edge_id(t, frm, to, attrs)
        if eid in eset:
            return
        eset.add(eid)
        edges.append({'id': eid, 'edge_type': t, 'from': frm, 'to': to, 'attrs': attrs})
    for r in fer:
        if len(r) < 3 or not r[0] or not r[1]:
            continue
        # v0.11.3 run-19 修复：source='-' 的边没有真实源端点（无路径或源在未分析批次/跨模块未实体化），
        # 不入图——图是漏洞路径图；TSV 仍保留该行（E68 终态 sink 边闭合读 TSV 口径）
        if r[0] == '-':
            continue
        attrs = {}
        for k, i in (('direction', 2), ('hops', 3), ('evidence_refs', 4), ('judged_by', 5), ('timestamp', 6)):
            if len(r) > i and r[i]:
                attrs[k] = r[i]
        add_edge('flow', 'source:' + r[0], 'sink:' + r[1], attrs)
    file_ids = {r[0] for r in fir if len(r) > 0 and r[0]}
    for r in ledr:
        if not ledh or len(r) < 4:
            continue
        # v0.10.1：basis 边只对挖掘方向行建（fix_presence 行的 basis 是 CVE 知识锚点，非图节点）
        if cell(r, 'direction') not in ('backward', 'forward', 'terminal'):
            continue
        basis = cell(r, 'basis_id')
        cp_id = cell(r, 'check_point_id')
        if not basis or not cp_id:
            continue
        prefix = 'sink:' if basis in sink_ids else ('source:' if basis in src_ids else ('file:' if basis in file_ids else 'basis:'))
        attrs = {}
        for k in ('direction', 'mechanism'):
            v = cell(r, k)
            if v:
                attrs[k] = v
        add_edge('basis', prefix + basis, 'checkpoint:' + cp_id, attrs)
        cands = cell(r, 'candidate_ids')
        for cid in ID_RE.findall(cands):
            add_edge('derived', 'checkpoint:' + cp_id, 'candidate:' + cid, {'via': 'ledger_candidate_ids'})
    for r in cr:
        if not ci or len(r) < 2:
            continue
        cid = ccell(r, 'candidate_id')
        if not cid:
            continue
        loc = ccell(r, 'location')
        if loc in loc_to_sids:
            for sid in loc_to_sids[loc]:
                add_edge('derived', 'sink:' + sid, 'candidate:' + cid, {'via': 'location_match'})
        ref = ccell(r, 'report_record_ref')
        if ref:
            add_edge('derived', 'candidate:' + cid, 'finding:' + ref, {'via': 'report_record_ref'})

    nodes.sort(key=lambda n: n['id'])
    edges.sort(key=lambda e: e['id'])
    if write:
        kg = os.path.join(S, 'knowledge_graph')
        os.makedirs(kg, exist_ok=True)
        with open(os.path.join(kg, 'nodes.json'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(nodes, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
        with open(os.path.join(kg, 'edges.json'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(edges, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    return nodes, edges

def serialize_pair(nodes, edges):
    return (json.dumps(nodes, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n' +
            json.dumps(edges, sort_keys=True, ensure_ascii=False, separators=(',', ':')))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--check', action='store_true',
                    help='reproject to memory and compare with existing files; exit 1 on mismatch')
    args = ap.parse_args()
    nodes, edges = build(args.session, write=not args.check)
    if args.check:
        npath = os.path.join(args.session, 'knowledge_graph', 'nodes.json')
        epath = os.path.join(args.session, 'knowledge_graph', 'edges.json')
        have = ''
        try:
            have = open(npath, encoding='utf-8').read() + '\n' + open(epath, encoding='utf-8').read()
        except Exception:
            have = ''
        ok = (have == serialize_pair(nodes, edges))
        print('GRAPH-CHECK: ' + ('consistent' if ok else 'MISMATCH'))
        sys.exit(0 if ok else 1)
    print('nodes=%d edges=%d' % (len(nodes), len(edges)))

if __name__ == '__main__':
    main()

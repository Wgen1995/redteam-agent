#!/usr/bin/env python3
# GenSource WU decompose v0.6.1 - batch pipeline + module dispatch + WU status
import argparse, csv, os

def read_tsv(path):
    rows = []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='\t'):
            if r: rows.append(r)
    return rows

def col_opt(h, name):
    try:
        return h.index(name)
    except ValueError:
        return None

def main():
    raise SystemExit(
        "FATAL: wu_decompose is retired. Dispatch only via "
        "python3 contracts/sdwr/session.py drive --session {S}"
    )
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--batch-size', type=int, default=10)
    ap.add_argument('--wu-size', type=int, default=15)
    args = ap.parse_args()
    S, bs, ws = args.session, args.batch_size, args.wu_size
    sinks = read_tsv(os.path.join(S, 'sink_inventory.tsv'))
    sir = sinks[1:] if sinks else []
    # v0.11.2 消消乐落地（doc 98/106）：排除类级剪枝（a2_verified=true 的 S2/S3）剪掉的 sink——剪掉的类不再派 WU
    pr = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
    pruned_types = set()
    if len(pr) > 1:
        h = pr[0]
        o_i, s_i, a_i = col_opt(h, 'operator'), col_opt(h, 'scope'), col_opt(h, 'a2_verified')
        for r in pr[1:]:
            if o_i is not None and s_i is not None and len(r) > max(o_i, s_i) and r[o_i] in ('S2', 'S3') and r[s_i].startswith('SINK-'):
                verified = a_i is not None and len(r) > a_i and r[a_i] == 'true'
                if verified:
                    pruned_types.add(r[s_i])
    if pruned_types:
        sir = [r for r in sir if not any(r[2] == t or t.startswith(r[2] + '-via-') for t in pruned_types)]
    # Group by sink_type, then by module (directory) for large projects
    # v0.9.3 文件级 WU（shell tool 成功要素：1 文件 1 subagent）
    # 关键认知：wu_size=50 的「上下文装得下」≠「分析得动」——50 个复杂污点链让 subagent 超负荷偷懒
    # 文件是自然上下文内聚单元：一个文件的所有 sink（通常 2-5 个）分析得动
    clusters = {}
    for r in sir:
        fname = r[1].rsplit(':', 1)[0] if len(r) > 1 and ':' in r[1] else 'unknown'
        clusters.setdefault(fname, []).append(r)
    import hashlib
    wus = []
    wu_seq = 0
    # v0.11.0 (doc 102 P0.3 / F-E2E-16): 1 文件 = 1 WU 恒成立——删除按 wu_size 切分
    # （大文件 sink>15 仍 1 WU：文件内聚优先；wu_size 参数废弃仅兼容 CLI）
    for st in sorted(clusters.keys()):
        group = clusters[st]
        cid = hashlib.md5(st.encode()).hexdigest()[:8]
        wu_seq += 1
        sid_list = ';'.join(r[0] for r in group)
        loc_list = ';'.join(r[1] for r in group)
        wus.append(['WU-%04d' % wu_seq, st, sid_list, loc_list, len(group), 'pending', 'CL-' + cid])
    batch_num = 0
    for i in range(0, len(wus), bs):
        batch_num += 1
        for j in range(i, min(i+bs, len(wus))):
            wus[j].append('B%03d' % batch_num)
    # Create batch directories
    for bn in range(1, batch_num + 1):
        os.makedirs(os.path.join(S, 'batches', 'B%03d' % bn), exist_ok=True)
    with open(os.path.join(S, 'wu_manifest.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['wu_id','sink_type','sink_ids','sink_locations','sink_count','status','cluster_id','batch_num'])
        for r in wus: w.writerow(r)
    with open(os.path.join(S, 'batch_progress.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['batch_num','status','wus_total','wus_done','findings_count'])
        for bn in range(1, batch_num + 1):
            count = sum(1 for r in wus if r[7] == 'B%03d' % bn)
            w.writerow(['B%03d' % bn, 'pending', count, 0, 0])
    open(os.path.join(S, 'live_findings_index.md'), 'w', encoding='utf-8').write('# Live Findings Index\n\n| Batch | Finding | Severity | Location |\n|---|---|---|---|\n')
    # v0.10.0 graph_snapshot（图演进轨迹：每批快照节点状态统计）
    # v0.10.1 加 graph_nodes/graph_edges 列：剪枝推进 → 计数递减 = 消消乐进度可见
    open(os.path.join(S, 'graph_snapshot.tsv'), 'w', encoding='utf-8').write('batch\tunchecked\tcandidate\tdisproved\tnot_applicable\tblocked\tflow_edges\tpruning_rules\tgraph_nodes\tgraph_edges\n')
    open(os.path.join(S, 'flow_edges.tsv'), 'w', encoding='utf-8').write('source_id\tsink_id\tdirection\thops\tevidence_refs\tjudged_by\ttimestamp\n')
    # v0.9.4 progress_board（multica 启示：文件态看板——进度可见性的主载体，人看它不依赖 todo）
    open(os.path.join(S, 'progress_board.md'), 'w', encoding='utf-8').write('# 进度看板（每批完成追加一行）\n\n| Batch | 状态 | 发现数 | 备注 |\n|---|---|---|---|\n')
    # v0.11.3 扫雷信息板（doc 115 信息级联：事实/线索/断点三区 + 精查清单）
    open(os.path.join(S, 'mine_scan_board.md'), 'w', encoding='utf-8').write(
        '# 扫雷信息板（每批追加；WU 派发时附带相关条目，DEFINE 判据必须对照）\n\n'
        '## fact（确定性事实——工具可复验，必须带 file:line 证据）\n\n'
        '| id | 内容 | 证据(file:line) | 发现 WU | 状态 |\n|---|---|---|---|---|\n'
        '## clue（判定线索——LLM 发现可独立复核的基准，结论仍独立下）\n\n'
        '| id | 内容 | 证据 | 适用 sink 类 | 状态 |\n|---|---|---|---|---|\n'
        '## break（已确认断点——负向级联；下游引用时仍需一次独立复核）\n\n'
        '| id | 路径段 | 证据 | 状态 |\n|---|---|---|---|\n'
        '## 精查清单（雷邻：雷的 flow 链上游未查检查点）\n\n'
        '| checkpoint_id | 原因 | 关联雷(sink_id) |\n|---|---|---|\n')
    # v0.10.1 图实体化（doc 99）：图先于分析存在——初始投影（全 unchecked 节点，边仅 basis）
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_graph
    try:
        ns, es = build_graph.build(S, write=True)
        print('graph nodes=%d edges=%d' % (len(ns), len(es)))
    except Exception as ex:
        # v0.11.0 (E-14): 图初始化失败必须中止 session 初始化（不静默跳过）
        print('FATAL: graph init failed: %s' % str(ex))
        raise SystemExit(1)
    print('WU=%d batches=%d (wu_size=%d batch_size=%d)' % (len(wus), batch_num, ws, bs))

if __name__ == '__main__':
    main()

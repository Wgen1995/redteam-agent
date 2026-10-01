#!/usr/bin/env python3
# GenSource run-toolkit（v0.11.3 run-19）：批闭包——scratch 合并 + 账本回填 + 图重投影 + 快照/看板/批进度/gate_progress
# 铁律：必须先 verify_batch.py 全绿再 close（禁止带病闭包）
# Usage: python3 close_batch.py --session DIR --batch BNNN [--dry-run]
import argparse, csv, os, subprocess, sys

def read_tsv(path):
    rows = []
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='	'):
            if r: rows.append(r)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--batch', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    S = os.path.abspath(args.session)
    wm = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
    h = wm[0]
    i_wu, i_ids, i_bn, i_st = h.index('wu_id'), h.index('sink_ids'), h.index('batch_num'), h.index('status')
    batch_wus = [r for r in wm[1:] if len(r) > i_bn and r[i_bn] == args.batch]
    led = read_tsv(os.path.join(S, 'check_point_ledger.tsv'))
    led_rows = led[1:]
    au_global = read_tsv(os.path.join(S, 'audit_log.tsv')) or [[]]
    fe_global = read_tsv(os.path.join(S, 'flow_edges.tsv')) or [[]]
    au_rows = au_global[1:]
    fe_rows = fe_global[1:]
    batch_sids = set()
    for wu in batch_wus:
        batch_sids.update(x for x in wu[i_ids].split(';') if x)
    au_rows = [r for r in au_rows if len(r) < 2 or r[1] not in batch_sids]
    fe_rows = [r for r in fe_rows if len(r) < 2 or r[1] not in batch_sids]
    SHARD_HEADER = ['sink_id', 'verdict', 'five_segment_evidence', 'evidence_refs', 'reviewed_at']
    pfx = os.path.join(S, 'batches', args.batch)
    for wu in batch_wus:
        wuid = wu[i_wu]
        part_shards = sorted(f for f in os.listdir(pfx)
                             if f.startswith(wuid + '-p') and f.endswith('.tsv')
                             and '-audit' not in f and '-flow' not in f)
        if part_shards and not args.dry_run:
            merged = [SHARD_HEADER]
            for f in part_shards:
                x = read_tsv(os.path.join(pfx, f))
                if x and x[0] == SHARD_HEADER:
                    merged.extend(x[1:])
            with open(os.path.join(pfx, wuid + '.tsv'), 'w', encoding='utf-8', newline='') as f:
                csv.writer(f, delimiter='	').writerows(merged)
        for stem, collect in (('-audit', au_rows), ('-flow', fe_rows)):
            for f in sorted(os.listdir(pfx)):
                if f.startswith(wuid) and f.endswith(stem + '.tsv'):
                    rows_x = read_tsv(os.path.join(pfx, f))
                    if rows_x and len(rows_x) > 1:
                        collect.extend(rows_x[1:])
    if not args.dry_run:
        def ts_of(r):
            try:
                return r[6].replace('Z', '+00:00') if len(r) > 6 and r[6] else '0000'
            except Exception:
                return '0000'
        au_rows = sorted(au_rows, key=ts_of)
        with open(os.path.join(S, 'audit_log.tsv'), 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter='	').writerows([au_global[0]] + au_rows)
        with open(os.path.join(S, 'flow_edges.tsv'), 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter='	').writerows([fe_global[0]] + fe_rows)
    shard_map = {}
    for wu in batch_wus:
        sh = read_tsv(os.path.join(pfx, wu[i_wu] + '.tsv'))
        if sh is None:
            print('FATAL: shard missing', wu[i_wu]); sys.exit(2)
        for r in sh[1:]:
            if len(r) >= 5:
                shard_map[r[0]] = (r[1], r[3], r[4])
    n_cand = n_disp = n_block = 0
    new_led = [led[0]]
    blocked_basis = []
    for r in led_rows:
        sid, st = r[0], (r[5] if len(r) > 5 else '')
        if sid in shard_map and st == '未检查':
            verdict, refs, ts2 = shard_map[sid]
            if verdict == 'candidate':
                n_cand += 1
                r[5] = 'candidate'
                r[6] = ''  # 1.3 簇关联后补 cluster_conclusion:clusters/...
            elif verdict == 'disproved':
                n_disp += 1
                r[5] = 'disproved'
                first_ref = refs.split(',')[0].strip() if refs else ''
                r[6] = 'disproved_safe:' + first_ref if first_ref else 'disproved_safe:no_ref'
            else:
                n_block += 1
                r[5] = 'blocked'
                r[6] = 'budget:wu_trace_limit'
                blocked_basis.append(sid)
            r[7] = ts2
        new_led.append(r)
    if not args.dry_run:
        with open(os.path.join(S, 'check_point_ledger.tsv'), 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter='	').writerows(new_led)
        if blocked_basis:
            fw = set()
            if os.path.isfile(os.path.join(S, 'failed_wus.txt')):
                fw = {ln.strip() for ln in open(os.path.join(S, 'failed_wus.txt'), encoding='utf-8') if ln.strip()}
            with open(os.path.join(S, 'failed_wus.txt'), 'a', encoding='utf-8') as f:
                for b in blocked_basis:
                    if b not in fw:
                        f.write(b + '\n')
        subprocess.run(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build_graph.py'), '--session', S],
                       capture_output=True, timeout=300)
        ns, es = 0, 0
        try:
            import json
            g = json.load(open(os.path.join(S, 'knowledge_graph/nodes.json'), encoding='utf-8'))
            ns = len(g.get('nodes', []))
            e = json.load(open(os.path.join(S, 'knowledge_graph/edges.json'), encoding='utf-8'))
            es = len(e.get('edges', []))
        except Exception:
            pass
        st_map = {}
        for r in new_led[1:]:
            if len(r) > 5:
                st_map[r[5]] = st_map.get(r[5], 0) + 1
        fe = read_tsv(os.path.join(S, 'flow_edges.tsv'))
        n_fe = max(0, len(fe) - 1) if fe else 0
        ts = subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()
        snap_line = '%s\t%s\t%s\t%s\t%s\t%s\t%d\t1\t%d\t%d\n' % (
            args.batch, st_map.get('未检查', 0), st_map.get('candidate', 0), st_map.get('disproved', 0),
            st_map.get('not_applicable', 0), st_map.get('blocked', 0), n_fe, ns, es)
        with open(os.path.join(S, 'graph_snapshot.tsv'), 'a', encoding='utf-8', newline='') as f:
            f.write(snap_line)
        bp = read_tsv(os.path.join(S, 'batch_progress.tsv'))
        for r in bp[1:]:
            if r[0] == args.batch:
                r[1] = 'completed'
                r[3] = str(len(batch_wus))
                r[4] = str(n_cand)
        with open(os.path.join(S, 'batch_progress.tsv'), 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter='	').writerows(bp)
        for r in wm[1:]:
            if r[i_wu] in [w[i_wu] for w in batch_wus]:
                r[i_st] = 'completed'
        with open(os.path.join(S, 'wu_manifest.tsv'), 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter='	').writerows(wm)
        gp_line = '1.2-batch-%s\tbatch_closed\tpass\t%s\n' % (args.batch, ts)
        with open(os.path.join(S, 'gate_progress.tsv'), 'a', encoding='utf-8', newline='') as f:
            f.write(gp_line)
        pb_line = '| %s | completed | %d | candidate=%d disproved=%d blocked=%d |\n' % (
            args.batch, n_cand, n_cand, n_disp, n_block)
        with open(os.path.join(S, 'progress_board.md'), 'a', encoding='utf-8', newline='') as f:
            f.write(pb_line)
    print('closed %s: candidate=%d disproved=%d blocked=%d (dry=%s)' % (args.batch, n_cand, n_disp, n_block, args.dry_run))

if __name__ == '__main__':
    main()

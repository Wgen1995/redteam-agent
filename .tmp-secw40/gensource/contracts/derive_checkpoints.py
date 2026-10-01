#!/usr/bin/env python3
# GenSource 确定性检查点派生 v0.5.0
# Usage: python3 derive_checkpoints.py --session DIR
import argparse, csv, os

def read_tsv(path):
    rows = []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='\t'):
            if r: rows.append(r)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    args = ap.parse_args()
    S = args.session
    sinks = read_tsv(os.path.join(S, 'sink_inventory.tsv'))
    sources = read_tsv(os.path.join(S, 'source_inventory.tsv'))
    files = read_tsv(os.path.join(S, 'file_inventory.tsv'))
    # v0.11.0 (doc 102 P0.2): 清单文件缺失即中止（不静默派生 0 检查点）
    if not sinks or not sources or not files:
        print('FATAL: missing inventory (sink/source/file). Run enumerate.py first.')
        raise SystemExit(1)
    sir, sor, fir = sinks[1:], sources[1:], files[1:]
    rows = []; seq = 0
    # v0.11.3 run-19 修复：数据行必须 8 字段（含 concluded_at 空位）——表头 8 列而旧代码只写 7 字段，
    # gate E22 时序检查（r[7]）对短行静默跳过，终态时间戳校验整体失效
    for r in sir:
        seq += 1
        rows.append([r[0], 'backward', 'needs_analysis', 'CP-%06d' % seq, '', '\u672a\u68c0\u67e5', '', ''])
    for r in sor:
        seq += 1
        rows.append([r[0], 'forward', 'pattern_driven', 'CP-%06d' % seq, '', '\u672a\u68c0\u67e5', '', ''])
    fws = {r[1].rsplit(':',1)[0] for r in sir if ':' in r[1]}
    fwe = {r[1].rsplit(':',1)[0] for r in sor if ':' in r[1]}
    for r in fir:
        seq += 1
        p, ft, fb = r[0], r[1], r[4]
        # v0.11.0: prefilter 条件对拍 enumerate 的真实探测（binary_flag 真值 + image/binary/archive/doc 类型）
        if p not in fws and p not in fwe and (fb == 'binary' or ft in ('image','binary','archive','doc')):
            rows.append([p, 'terminal', 'prefilter', 'CP-%06d' % seq, '', 'not_applicable', 'prefilter_no_exec:'+ft+':0\u547d\u4e2d\u8bc1\u636e', ''])
        else:
            rows.append([p, 'terminal', 'deep_scan', 'CP-%06d' % seq, '', '\u672a\u68c0\u67e5', '', ''])
    with open(os.path.join(S, 'check_point_ledger.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['basis_id','direction','mechanism','check_point_id','candidate_ids','terminal_state','reason','concluded_at'])
        for r in rows: w.writerow(r)
    print('checkpoints=%d (bw=%d fw=%d term=%d)' % (len(rows), len(sir), len(sor), len(fir)))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# GenSource run-toolkit（v0.11.3 run-19）：注释误报确定性预筛器
# 对 sink 清单每行机械分类：trivial_comment（整行注释，保守判据）/ needs_llm
# 只输出候选分类与行原文，不产生 verdict——verdict 由主代理逐行确认后经 fastlane.py 落盘
# Usage: python3 classify_trivial.py --session DIR --source SRC
import argparse, csv, os, re

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--source', required=True)
    args = ap.parse_args()
    S = os.path.abspath(args.session)
    sinks = []
    with open(os.path.join(S, 'sink_inventory.tsv'), encoding='utf-8', newline='') as f:
        rd = csv.reader(f, delimiter='	')
        next(rd, None)
        for r in rd:
            if len(r) > 3:
                sinks.append((r[0], r[1], r[2], r[3]))
    stat = {'trivial_comment': 0, 'needs_llm': 0, 'missing': 0}
    out = []
    for sid, loc, stype, sym in sinks:
        fname, ln_s = loc.rsplit(':', 1)
        try:
            ln = int(ln_s)
        except Exception:
            stat['needs_llm'] += 1
            continue
        p = os.path.join(args.source, fname)
        if not os.path.isfile(p):
            stat['missing'] += 1
            out.append((sid, loc, stype, 'missing', ''))
            continue
        lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
        if ln < 1 or ln > len(lines):
            stat['missing'] += 1
            out.append((sid, loc, stype, 'missing', ''))
            continue
        line = lines[ln - 1]
        stripped = line.strip()
        cls = 'needs_llm'
        # 保守注释判定：只有整行注释或 token 明确位于注释区才 trivial；含任何代码残留的行进 LLM
        is_comment = False
        if stripped.startswith(('//', '#')):
            is_comment = True
        elif stripped.startswith('*') and not stripped.startswith('*/'):
            is_comment = True
        elif stripped.startswith('<!--'):
            is_comment = True
        elif stripped.startswith('/*'):
            tail = stripped[2:]
            idx = tail.find('*/')
            if idx < 0 or tail[idx + 2:].strip() == '':
                is_comment = True
        elif '//' in line and sym and line.index('//') < line.find(sym):
            is_comment = True
        if is_comment:
            cls = 'trivial_comment'
        stat[cls] = stat.get(cls, 0) + 1
        out.append((sid, loc, stype, cls, line[:160]))
    with open(os.path.join(S, 'classify_result.tsv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='	')
        w.writerow(['sink_id', 'loc', 'sink_type', 'class', 'line'])
        for row in out:
            w.writerow(row)
    print('sinks=%d trivial_comment=%d needs_llm=%d missing=%d' % (
        len(sinks), stat['trivial_comment'], stat['needs_llm'], stat['missing']))
    print('full result -> %s/classify_result.tsv' % S)

if __name__ == '__main__':
    main()

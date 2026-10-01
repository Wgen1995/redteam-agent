#!/usr/bin/env python3
# GenSource run-toolkit（v0.11.3 run-19）：快车道落盘器
# 主代理已逐行 Read 确认的注释误报 sink，机械生成三件套行并入 WU 文件
# 使用：1) classify_trivial.py 全量分类；2) 主代理 Read 该批 trivial_comment 行逐条确认；3) 写确认清单（每行一个 sink_id）
# 4) python3 fastlane.py --session DIR --batch BNNN --confirmed <sink_ids 文件>
import argparse, csv, os, subprocess, sys

def read_tsv(path):
    rows = []
    if not os.path.isfile(path):
        return []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='	'):
            if r: rows.append(r)
    return rows

def write_tsv(path, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f, delimiter='	').writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--batch', required=True)
    ap.add_argument('--confirmed', required=True)
    args = ap.parse_args()
    S = os.path.abspath(args.session)
    ts = subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()
    confirmed = set()
    for ln in open(args.confirmed, encoding='utf-8'):
        s = ln.strip()
        if s: confirmed.add(s)
    if not confirmed:
        print('empty confirmed list'); sys.exit(1)
    cls = {}
    for r in read_tsv(os.path.join(S, 'classify_result.tsv'))[1:]:
        if len(r) > 4 and r[3] == 'trivial_comment':
            cls[r[0]] = (r[1], r[2], r[4])
    cp_of = {}
    for r in read_tsv(os.path.join(S, 'check_point_ledger.tsv'))[1:]:
        if len(r) > 3 and r[1] == 'backward':
            cp_of[r[0]] = r[3]
    wm = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
    h = wm[0]
    i_wu, i_ids, i_bn = h.index('wu_id'), h.index('sink_ids'), h.index('batch_num')
    wu_sinks = {}
    for r in wm[1:]:
        if len(r) > i_bn and r[i_bn] == args.batch:
            wu_sinks[r[i_wu]] = [x for x in r[i_ids].split(';') if x]
    by_wu = {}
    bad = []
    for sid in confirmed:
        loc, stype, line_txt = cls.get(sid, (None, None, ''))
        if loc is None:
            bad.append(sid + ' not in trivial classification')
            continue
        owner = next((w for w, ids in wu_sinks.items() if sid in ids), None)
        if owner is None:
            bad.append(sid + ' not in batch ' + args.batch)
            continue
        by_wu.setdefault(owner, []).append((sid, loc, stype, line_txt))
    if bad:
        print('BAD:'); [print(' -', b) for b in bad]; sys.exit(2)
    SHARD_H = ['sink_id', 'verdict', 'five_segment_evidence', 'evidence_refs', 'reviewed_at']
    AUDIT_H = ['check_point_id', 'basis_id', 'direction', 'result', 'evidence_type', 'evidence_ref', 'reviewed_at']
    FLOW_H = ['source_id', 'sink_id', 'direction', 'hops', 'evidence_refs', 'judged_by', 'timestamp']
    total = 0
    for wu, items in by_wu.items():
        pfx = os.path.join(S, 'batches', args.batch)
        sh = read_tsv(os.path.join(pfx, wu + '.tsv'))
        if sh and sh[0] != SHARD_H:
            sh = [SHARD_H]
        elif not sh:
            sh = [SHARD_H]
        existing_sids = {r[0] for r in sh[1:] if r}
        for sid, loc, stype, line_txt in items:
            if sid in existing_sids:
                continue
            short = line_txt[:100].replace('	', ' ')
            sh.append([sid, 'disproved',
                       'source:not-attainable - hit line is a comment, not executable code|propagation:none - no code on a comment line|sanitizers:n/a - no taint path exists|sink:not-a-sink - pattern match is comment text (verified: ' + short + ')|disproof_checked:direct evidence - line is comment text',
                       loc, ts])
        write_tsv(os.path.join(pfx, wu + '.tsv'), sh)
        au = read_tsv(os.path.join(pfx, wu + '-audit.tsv'))
        if au and au[0] != AUDIT_H:
            au = [AUDIT_H]
        elif not au:
            au = [AUDIT_H]
        au_sids = {r[1] for r in au[1:] if len(r) > 1}
        for sid, loc, stype, line_txt in items:
            if sid in au_sids:
                continue
            cp = cp_of.get(sid, '')
            au.append([cp, sid, 'backward', 'hit line is a comment (verified read): ' + line_txt[:120], 'direct', loc, ts])
        write_tsv(os.path.join(pfx, wu + '-audit.tsv'), au)
        fl = read_tsv(os.path.join(pfx, wu + '-flow.tsv'))
        if fl and fl[0] != FLOW_H:
            fl = [FLOW_H]
        elif not fl:
            fl = [FLOW_H]
        fl_sids = {r[1] for r in fl[1:] if len(r) > 1}
        for sid, loc, stype, line_txt in items:
            if sid in fl_sids:
                continue
            fl.append(['-', sid, 'no_path', '0', loc, 'fastlane-main', ts])
        write_tsv(os.path.join(pfx, wu + '-flow.tsv'), fl)
        total += len(items)
    print('fastlane wrote %d sinks across %d WUs at %s' % (total, len(by_wu), ts))

if __name__ == '__main__':
    main()

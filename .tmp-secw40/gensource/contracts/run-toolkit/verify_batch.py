#!/usr/bin/env python3
# GenSource run-toolkit（v0.11.3 run-19）：批级机械校验——与 gate E71/E68/E21/E18 同口径的批范围前置检查
# Usage: python3 verify_batch.py --session DIR --source SRC --batch BNNN
import argparse, csv, os, re, sys

VERDICTS = ('candidate', 'disproved', 'blocked')
HEADER = ['sink_id', 'verdict', 'five_segment_evidence', 'evidence_refs', 'reviewed_at']
REF_RE = re.compile(r'([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+\.(?:java|py|go|js|ts|php|c|h|cpp|hpp|md|xml|properties|jsp)):(\d+)')

def read_tsv(path):
    rows = []
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.reader(f, delimiter='	'):
            if r: rows.append(r)
    return rows

_line_cache = {}

def file_lines(src, rel):
    if rel.startswith('./'):
        rel = rel[2:]
    key = (src, rel)
    if key not in _line_cache:
        p = os.path.join(src, rel)
        n = None
        if os.path.isfile(p):
            try:
                n = sum(1 for _ in open(p, encoding='utf-8', errors='replace'))
            except Exception:
                n = None
        _line_cache[key] = n
    return _line_cache[key]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--source', required=True)
    ap.add_argument('--batch', required=True)
    args = ap.parse_args()
    S = os.path.abspath(args.session)
    problems = []
    wm = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
    if wm is None:
        print('FATAL: wu_manifest missing'); sys.exit(2)
    h = wm[0]
    i_wu, i_ids, i_bn = h.index('wu_id'), h.index('sink_ids'), h.index('batch_num')
    batch_wus = [r for r in wm[1:] if len(r) > i_bn and r[i_bn] == args.batch]
    led = read_tsv(os.path.join(S, 'check_point_ledger.tsv'))
    cp_of = {}
    for r in (led[1:] if led and len(led) > 1 else []):
        if len(r) > 3 and r[1] == 'backward': cp_of[r[0]] = r[3]
    fe = read_tsv(os.path.join(S, 'flow_edges.tsv'))
    flow_sinks = {}
    for r in (fe[1:] if fe and len(fe) > 1 else []):
        if len(r) > 1 and r[1]:
            flow_sinks.setdefault(r[1], []).append(r[2] if len(r) > 2 else '')
    au = read_tsv(os.path.join(S, 'audit_log.tsv'))
    audit_cps = {r[0] for r in (au[1:] if au and len(au) > 1 else []) if r}
    pfx = os.path.join(S, 'batches', args.batch)
    if not os.path.isdir(pfx):
        print('FATAL: batch dir missing'); sys.exit(2)
    for fn in os.listdir(pfx):
        if fn.endswith('-audit.tsv'):
            x = read_tsv(os.path.join(pfx, fn))
            for r in (x[1:] if x and len(x) > 1 else []):
                if r: audit_cps.add(r[0])
        elif fn.endswith('-flow.tsv'):
            x = read_tsv(os.path.join(pfx, fn))
            for r in (x[1:] if x and len(x) > 1 else []):
                if len(r) > 1 and r[1]:
                    flow_sinks.setdefault(r[1], []).append(r[2] if len(r) > 2 else '')
    for wu in batch_wus:
        wu_id = wu[i_wu]
        ids = [x for x in wu[i_ids].split(';') if x]
        sh = read_tsv(os.path.join(pfx, wu_id + '.tsv'))
        if sh is None:
            part_shards = sorted(f for f in os.listdir(pfx)
                                 if f.startswith(wu_id + '-p') and f.endswith('.tsv')
                                 and '-audit' not in f and '-flow' not in f)
            if part_shards:
                sh = [HEADER]
                for f in part_shards:
                    x = read_tsv(os.path.join(pfx, f))
                    if x is None:
                        problems.append('%s: part missing %s' % (wu_id, f))
                    elif x[0] != HEADER:
                        problems.append('%s: part header bad %s: %s' % (wu_id, f, x[0]))
                    else:
                        sh.extend(x[1:])
            else:
                problems.append('%s: shard missing' % wu_id); continue
        if sh[0] != HEADER:
            problems.append('%s: header bad %s' % (wu_id, sh[0])); continue
        rows = sh[1:]
        got_ids = [r[0] for r in rows if r]
        if len(rows) != len(ids):
            problems.append('%s: row count %d != %d' % (wu_id, len(rows), len(ids)))
        if set(got_ids) != set(ids):
            problems.append('%s: sink set mismatch (missing %s extra %s)' % (wu_id, set(ids) - set(got_ids), set(got_ids) - set(ids)))
        for r in rows:
            if len(r) < 5:
                problems.append('%s: row short %s' % (wu_id, r)); continue
            sid = r[0]
            if r[1] not in VERDICTS:
                problems.append('%s: %s verdict illegal %r' % (wu_id, sid, r[1]))
            segs = r[2].split('|')
            if len(segs) != 5 or any(not s.strip() for s in segs):
                problems.append('%s: %s five-segment incomplete' % (wu_id, sid))
            if not r[4]:
                problems.append('%s: %s reviewed_at empty' % (wu_id, sid))
            refs = list(REF_RE.finditer(r[3]))
            if not refs:
                problems.append('%s: %s no file:line refs' % (wu_id, sid))
            for ref in refs:
                n = file_lines(args.source, ref.group(1))
                if n is None:
                    problems.append('%s: %s ref file missing %s' % (wu_id, sid, ref.group(1)))
                elif int(ref.group(2)) > n:
                    problems.append('%s: %s ref line out of range %s' % (wu_id, sid, ref.group(0)))
            if sid not in flow_sinks:
                problems.append('%s: %s no flow edge' % (wu_id, sid))
            cp = cp_of.get(sid)
            if cp and cp not in audit_cps:
                problems.append('%s: %s CP %s no audit row' % (wu_id, sid, cp))
    if problems:
        print('PROBLEMS: %d' % len(problems))
        for p in problems[:60]:
            print(' -', p)
        sys.exit(1)
    print('BATCH %s OK: %d WUs, %d sinks verified' % (args.batch, len(batch_wus), sum(len([x for x in r[i_ids].split(';') if x]) for r in batch_wus)))

if __name__ == '__main__':
    main()

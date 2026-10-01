#!/usr/bin/env python3
# GenSource Gate-1 verifier (v0.4.0). Host-run, read-only vs session artifacts.
# Usage: python3 gate-1.py --session DIR --source SRC [--expect EXPECTED]
# Writes DIR/gate_record.md. Exit 0 iff gate_result=pass (or selftest match with --expect).
import argparse, csv, hashlib, json, os, re, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_graph  # v0.10.1 图实体化投影（E56-E59 用）


def cjs(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

SIGNAL_CLASSES = {'SINK-SENSITIVE-EXPOSE','SINK-LOGGING-INSUFF','SINK-AUTHN-BYPASS','SINK-BRUTE-FORCE','SINK-OBSERVABLE-DIFF','SINK-STATE-CONCURRENT','SINK-MEM-INDEX'}

SIGNAL = r'SINK-(SENSITIVE-EXPOSE|LOGGING-INSUFF|AUTHN-BYPASS|BRUTE-FORCE|OBSERVABLE-DIFF|STATE-CONCURRENT|MEM-INDEX)'
# 真实用户反馈驱动的修复：findings/V{N}.md 的排名式文件名在批式流水线下无法在
# 确认候选当轮立即确定（排名要见到全部候选才能算），会导致后出现的高危 finding
# 逼所有已产出文件重命名。改为文件名=candidate_id（阶段1起就唯一、立即可用），
# V{N} 只作为 report.md 生成时机械回填进标题行的展示排名——见 report-delivery/
# SKILL.md Part 1/Part 2 拆分。candidate_id 格式见 candidate-discovery/SKILL.md
# 9b1：C-{sink_sort_order:05d}-{source_sort_order:05d}-{sink_id_sig8}。
FINDING_FILE_RE = re.compile(r'^C-\d{5}-\d{5}-[0-9a-f]{8}-.*\.md$')
FINDING_LINK_RE = r'\[查看\]\(findings/C-\d{5}-\d{5}-[0-9a-f]{8}-[^)]+\.md\)'
CAND_COLS = ['candidate_id','location','sink_type','severity_hypothesis_initial','root_cause_group_id','lifecycle_state','verdict','cluster_ref','verification_record_ref','report_record_ref','created_at','discovery_source','path','start_line','end_line','discovery_reasoning_note']  # v0.11.0 (C1): 16 列——复活 E32 机械门
MF_KEYS = {'candidate_id','location','sink_type','severity','root_cause_group_id','verdict','confidence','evidence_grade','runtime_tier'}
THR = {6:0.6, 5:0.7, 4:0.7, 3:0.8, 2:0.8, 1:0.8}
ID_RE = re.compile(r'C-\d{5}-\d{5}-[0-9a-f]{8}')
REF_RE = re.compile(
    r'((?:[A-Za-z0-9_.-]+/)*(?:Dockerfile[A-Za-z0-9_.-]*|'
    r'[A-Za-z0-9_.-]+\.(?:java|py|go|js|ts|php|c|h|cpp|hpp|md|xml|properties|jsp|'
    r'yml|yaml|sql|sh|toml|ini|cfg|conf|env|json|txt))):(\d+)(?:-(\d+))?'
)
# 真实 dvpwa 冒烟跑暴露：Dockerfile.app/docker-compose.yml/run.py/recreate.sh 这类
# 根目录文件（无子目录前缀）+ 配置类扩展名（yml/sql/sh 等）此前完全不在匹配范围内——
# 旧正则强制要求至少一段 "dir/" 前缀，且扩展名白名单只有 java/py/go/js/ts/php 等
# 传统源码后缀，导致这类文件级候选即使证据引用完全正确也被判定"引用密度不足"。
# 现在 dir/ 前缀改为可选（零到多段），扩展名白名单补上常见配置类型，并单独识别
# 没有常规扩展名的 Dockerfile 系列文件名。
CLUSTER_RE = re.compile(r'clusters/([A-Za-z0-9_.-]+\.md)')

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
    return h.index(name) if name in h else None

def col(h, name, fallback=None):
    if name in h:
        return h.index(name)
    if name == 'sort_order' and '排序序' in h:
        return h.index('排序序')
    if fallback is not None:
        return fallback
    raise KeyError(name)

def parse_ts(t):
    if not t:
        return None
    t = t.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(t)
    except Exception:
        return None

class Gate:
    def __init__(self, session, source, expect=None):
        self.S = session
        self.src = source
        self.expect = expect
        self.rows = []  # (name, output, verdict)
        self.linecache = {}

    def file_lines(self, relpath):
        if relpath.startswith('./'):
            relpath = relpath[2:]  # v0.11.1 E-18: 前缀判断（lstrip 字符集会吃 hidden 目录首点）
        if relpath in self.linecache:
            return self.linecache[relpath]
        p = os.path.join(self.src, relpath)
        n = None
        if os.path.isfile(p):
            try:
                n = sum(1 for _ in open(p, encoding='utf-8', errors='replace'))
            except Exception:
                n = None
        self.linecache[relpath] = n
        return n

    def add(self, name, out, ok):
        v = '成立' if ok else 'FAIL'
        self.rows.append((name, str(out), v))
        return ok

    def run(self):
        S = self.S
        # ---- load ----------------
        led = read_tsv(os.path.join(S, 'check_point_ledger.tsv'))
        if not led:
            led = [[], []]
        sinks = read_tsv(os.path.join(S, 'sink_inventory.tsv'))
        srcs = read_tsv(os.path.join(S, 'source_inventory.tsv'))
        files = read_tsv(os.path.join(S, 'file_inventory.tsv'))
        cand = read_tsv(os.path.join(S, 'candidates.tsv'))
        alog = read_tsv(os.path.join(S, 'audit_log.tsv'))
        ledh, ledr = (led[0], led[1:]) if led and len(led) > 1 else ([], [])
        sih, sir = (sinks[0], sinks[1:]) if len(sinks) > 1 else ([], [])
        soh, sor = (srcs[0], srcs[1:]) if len(srcs) > 1 else ([], [])
        fih, fir = (files[0], files[1:]) if len(files) > 1 else ([], [])
        ch, cr = (cand[0], cand[1:]) if len(cand) > 1 else ([], [])
        ah, ar = (alog[0], alog[1:]) if len(alog) > 1 else ([], [])
        try:
            mf = json.load(open(os.path.join(S, 'findings/machine-fields.json'), encoding='utf-8'))
        except Exception:
            mf = []
        # v0.11.1 C8: vs 死变量已删（E14 用 candidates.tsv+machine-fields+report.md 三事实源，不读本文件；本文件由宿主 shell 对账）
        report = open(os.path.join(S, 'report.md'), encoding='utf-8').read() if os.path.isfile(os.path.join(S, 'report.md')) else ''
        rs = open(os.path.join(S, 'run-state.md'), encoding='utf-8').read() if os.path.isfile(os.path.join(S, 'run-state.md')) else ''
        clusters = [f for f in os.listdir(os.path.join(S, 'clusters')) if f.endswith('.md')] if os.path.isdir(os.path.join(S, 'clusters')) else []
        # ---------------- 图实体化（v0.11.0 E-17 修正：gate 严格只读，不写盘不自愈） ----------------
        # E58 语义：图文件与账本内存投影比对，不一致（手改/陈旧）FAIL；重投影由 SKILL 流程显式跑 build_graph.py
        self._kg_snap = ''
        try:
            kg = os.path.join(S, 'knowledge_graph')
            for fn in ('nodes.json', 'edges.json'):
                p = os.path.join(kg, fn)
                if os.path.isfile(p):
                    self._kg_snap += open(p, encoding='utf-8').read() + '\n'
            self._b1 = build_graph.build(S, write=False)
        except Exception as ex:
            self._b1 = ('ERR', str(ex)[:120])
        # ---------------- E1 ----------------
        e1 = sum(1 for r in ledr if len(r) > 5 and r[5] == '未检查') if ledr else 'ERR(缺账本)'
        self.add('planned==terminal', e1, e1 == 0)
        # ---------------- E2/E3 ----------------
        back = {r[0] for r in ledr if len(r) > 1 and r[1] == 'backward'}
        fwd = {r[0] for r in ledr if len(r) > 1 and r[1] == 'forward'}
        e2 = len({r[0] for r in sir} - back)
        e3 = len({r[0] for r in sor} - fwd)
        self.add('sink 回溯覆盖', e2, e2 == 0)
        self.add('source 前向覆盖', e3, e3 == 0)
        # ---------------- E4 ----------------
        ab = {r[1] for r in ar if len(r) > 2 and r[2] == 'backward'}
        e4a = len({r[0] for r in sir} - ab)
        e4b = len(ab - {r[0] for r in sir})
        self.add('audit 双向覆盖', str(e4a) + '/' + str(e4b), e4a == 0 and e4b == 0)
        # ---------------- E5 ----------------
        vfiles = [f for f in os.listdir(os.path.join(S, 'findings')) if FINDING_FILE_RE.match(f)] if os.path.isdir(os.path.join(S, 'findings')) else []
        e5a = len(vfiles)
        e5b = len(mf)
        vcol = col_opt(ch, 'verdict')
        e5c = sum(1 for r in cr if vcol is not None and r[vcol] == 'confirmed') if vcol is not None else 'ERR(无verdict列)'
        e5d = len(re.findall(FINDING_LINK_RE, report))
        e5t = 0
        for x in mf:
            # v0.11.2 fail-closed（run-18 暴露）：非法 confidence/tier 值（如 'high' 字符串）计 FAIL，不崩溃
            try:
                tier = int(x.get('runtime_tier') or 6)
            except (TypeError, ValueError):
                e5t += 1
                continue
            try:
                conf = float(x.get('confidence') or 0)
            except (TypeError, ValueError):
                e5t += 1
                continue
            if conf < THR.get(tier, 0.6):
                e5t += 1
            if tier == 6 and x.get('evidence_grade') != 'direct':
                e5t += 1
        ok5 = (e5a == e5b == e5c == e5d) and e5t == 0
        self.add('四相等+阈值', '/'.join(map(str, [e5a, e5b, e5c, e5d, e5t])), ok5)
        # ---------------- E6 ----------------
        fw_path = os.path.join(S, 'failed_wus.txt')
        e6 = 'missing'
        if os.path.isfile(fw_path):
            e6 = sum(1 for _ in open(fw_path, encoding='utf-8'))
        blocked_basis = {r[0] for r in ledr if len(r) > 5 and r[5] == 'blocked'}
        e6b = len(blocked_basis)
        fw_set = set()
        if os.path.isfile(fw_path):
            fw_set = {ln.strip() for ln in open(fw_path, encoding='utf-8') if ln.strip()}
        e6c = len(blocked_basis - fw_set)
        ok6 = e6 != 'missing' and e6 == e6b and e6c == 0
        self.add('failed 清单去真空', '/'.join(map(str, [e6, e6b, e6c])), ok6)
        # ---------------- E7 ----------------
        e7 = open(os.path.join(S, 'check_point_ledger.tsv'), encoding='utf-8').read().count('未检查') if os.path.isfile(os.path.join(S, 'check_point_ledger.tsv')) else 'ERR(缺账本)'
        self.add('账本零残留', e7, e7 == 0)
        # ---------------- E8 ----------------
        e8 = 0
        for r in ledr:
            if len(r) > 6 and r[5] == 'not_applicable':
                d = r[1] if len(r) > 1 else ''
                reason = r[6] if len(r) > 6 else ''
                if d in ('backward', 'forward'):
                    if not reason.startswith(('false_rule_hit:', 'disproved_safe:', 'cluster_conclusion:')):
                        e8 += 1
                elif d == 'terminal':
                    if not reason.startswith(('prefilter_no_exec:', 'false_rule_hit:', 'disproved_safe:')):
                        e8 += 1
        self.add('反伪闭合(全方向)', e8, e8 == 0)
        # ---------------- E9 ----------------
        e9 = len(clusters)
        self.add('簇产物存在', e9, e9 > 0)
        # ---------------- E10 ----------------
        e10a = 0
        e10b = 0
        for r in ledr:
            if len(r) <= 6:
                continue
            d, st, reason = r[1], r[5], r[6]
            if st == 'disproved':
                if not reason.startswith(('cluster_conclusion:', 'disproved_safe:', 'false_rule_hit:')):
                    e10a += 1
                elif reason.startswith('disproved_safe:'):
                    if not REF_RE.search(reason):
                        e10a += 1
            if st == 'blocked' and not reason.startswith(('budget:', 'user_decision:', 'permission:')):
                e10b += 1
        self.add('全终态理由封闭', str(e10a) + '/' + str(e10b), e10a == 0 and e10b == 0)
        # ---------------- E11 ----------------
        try:
            inv_locs = {r[col(sih, 'file:line')] for r in sir if len(r) > 1}
            # 真实 dvpwa 冒烟跑暴露：文件级终态候选（sink_type=FILE，如 Dockerfile.app/
            # docker-compose.yml 这类配置误用发现）的 location 根本不在 sink_inventory
            # 里——它们锚定的是文件本身，不是某个 sink 命中。此前 E11 只豁免
            # divergent_reasoning，file 候选被误判反查失败。豁免条件：location 的路径部分
            # 命中 file_inventory.tsv 的清单路径。
            file_paths = {r[col(fih, 'path')] for r in fir if len(r) > 1} if fih else set()
            e11 = 0
            for c in cr:
                p = c[col(ch, 'candidate_id')].split('-')
                if len(p) != 4 or p[0] != 'C':
                    e11 += 1
                    continue
                sseq, sseq2, sig = p[1], p[2], p[3]
                loc = c[col(ch, 'location')]
                st = c[col(ch, 'sink_type')]
                # v0.11.4 run-19: divergent_reasoning 候选（A5 假设走流水线产出）的锚定合法性由 E27 假设锚点强制保证——
                # 其位置是假设锚点而非枚举 sink 命中，豁免清单位置检查（sig 仍按 file:line:sink_type 校验）
                ds_idx = col_opt(ch, 'discovery_source')
                is_divergent = ds_idx is not None and ds_idx < len(c) and c[ds_idx] == 'divergent_reasoning'
                is_file_terminal = st == 'FILE' and loc.rsplit(':', 1)[0] in file_paths
                if loc not in inv_locs and not is_divergent and not is_file_terminal:
                    e11 += 1
                    continue
                f, ln = loc.rsplit(':', 1)
                sig_candidates = [hashlib.md5((f + ':' + ln + ':' + st).encode()).hexdigest()[:8],
                                  hashlib.md5((f + ':' + ln).encode()).hexdigest()[:8]]
                if is_file_terminal:
                    sig_candidates.append(hashlib.md5(loc.encode()).hexdigest()[:8])
                if sig not in sig_candidates:
                    e11 += 1
        except Exception as ex:
            e11 = 'ERR:' + str(ex)[:40]
        self.add('候选 ID 反查', e11, e11 == 0)
        # ---------------- E12 ----------------
        arts = ['audit_log.tsv', 'verification-summary.md', 'failed_wus.txt', 'findings/machine-fields.json', 'candidates.tsv', 'check_point_ledger.tsv', 'report.md', 'knowledge_graph/nodes.json', 'knowledge_graph/edges.json']
        e12 = sum(1 for a in arts if not os.path.isfile(os.path.join(S, a))) + (0 if clusters else 1)
        self.add('产物存在性', e12, e12 == 0)
        # ---------------- E13 ----------------
        e13 = 0
        for r in sir:
            if len(r) > 2 and re.search(SIGNAL, r[2]):
                e13 += 1
        self.add('信号级禁入', e13, e13 == 0)
        # ---------------- E14 ----------------
        vcol2 = col_opt(ch, 'verdict')
        confirmed = {c[col(ch, 'candidate_id')] for c in cr if vcol2 is not None and c[vcol2] == 'confirmed'}
        mf_ids = {x.get('candidate_id') for x in mf}
        vnum_bad = sum(1 for i in mf_ids if re.match(r'^V\d+$', str(i)))
        e5d_n = len(re.findall(FINDING_LINK_RE, report))
        e14 = 0
        e14 += len(confirmed ^ mf_ids)
        if e5d_n > 0 and not confirmed:
            e14 += 1
        e14 += vnum_bad
        self.add('三事实源一致性', e14, e14 == 0)
        # ---------------- E16 ----------------
        e16 = 0
        for f in clusters:
            txt = open(os.path.join(S, 'clusters', f), encoding='utf-8').read()
            if '## 攻击模式对抗表' not in txt:
                e16 += 1
        self.add('对抗表存在', e16, e16 == 0)
        # ---------------- E17 ----------------
        e17 = 0
        if ch != CAND_COLS:
            e17 += 1
        for x in mf:
            if set(x.keys()) != MF_KEYS:
                e17 += 1
        if sih[:4] != ['sink_id', 'file:line', 'sink_type', 'symbol']:
            e17 += 1
        if soh[:5] != ['source_id', 'file:line', 'entry_type', 'symbol', 'param']:
            e17 += 1
        # v0.11.0 E-21/D11/D12: 全部账本 header 契约校验（LLM 调换列序=读错列=假 pass 的封堵）
        if ledh and ledh[:8] != ['basis_id', 'direction', 'mechanism', 'check_point_id', 'candidate_ids', 'terminal_state', 'reason', 'concluded_at']:
            e17 += 1
        plh = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
        if len(plh) > 0 and plh[0][:7] != ['operator', 'criterion', 'scope', 'evidence', 'judged_by', 'timestamp', 'a2_verified']:
            e17 += 1
        feh = read_tsv(os.path.join(S, 'flow_edges.tsv'))
        if len(feh) > 0 and feh[0][:7] != ['source_id', 'sink_id', 'direction', 'hops', 'evidence_refs', 'judged_by', 'timestamp']:
            e17 += 1
        if ah and ah[:7] != ['check_point_id', 'basis_id', 'direction', 'result', 'evidence_type', 'evidence_ref', 'reviewed_at']:
            e17 += 1
        gph = read_tsv(os.path.join(S, 'gate_progress.tsv'))
        if len(gph) > 0 and gph[0][:4] != ['sub_task', 'gate_eq', 'result', 'timestamp']:
            e17 += 1
        bph = read_tsv(os.path.join(S, 'batch_progress.tsv'))
        if len(bph) > 0 and bph[0][:5] != ['batch_num', 'status', 'wus_total', 'wus_done', 'findings_count']:
            e17 += 1
        wmh = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
        if len(wmh) > 0 and wmh[0][:8] != ['wu_id', 'sink_type', 'sink_ids', 'sink_locations', 'sink_count', 'status', 'cluster_id', 'batch_num']:
            e17 += 1
        self.add('schema 全等', e17, e17 == 0)
        # ---------------- E18 ----------------
        e18 = 0
        seen = set()
        def resolve_ref(ref):
            nonlocal e18
            key = 'r:' + ref
            if key in seen:
                return
            seen.add(key)
            m = REF_RE.search(ref)
            if m:
                path, ln = m.group(1), int(m.group(2))
                n = self.file_lines(path)
                if n is None or ln > n:
                    e18 += 1
                return
            m2 = CLUSTER_RE.search(ref)
            if m2:
                if m2.group(1) not in clusters:
                    e18 += 1
        for r in ledr:
            if len(r) > 6:
                resolve_ref(r[6])
        for r in ar:
            if len(r) > 5:
                resolve_ref(r[5])
        for c in cr:
            for nm in ('cluster_ref', 'verification_record_ref', 'report_record_ref'):
                idx = col_opt(ch, nm)
                if idx is not None and idx < len(c):
                    resolve_ref(c[idx] or '')
        self.add('引用可解析', e18, e18 == 0)
        # ---------------- E19 ----------------
        usage = {}
        for r in ledr:
            if len(r) > 6:
                for ref in REF_RE.findall(r[6]):
                    key = ref[0] + ':' + ref[1]
                    usage[key] = usage.get(key, 0) + 1
                for m in CLUSTER_RE.finditer(r[6]):
                    key = 'clusters/' + m.group(1)
                    usage[key] = usage.get(key, 0) + 1
        e19 = sum(1 for v in usage.values() if v > 50)
        e19w = sum(1 for v in usage.values() if 10 < v <= 50)
        self.add('证据唯一性', str(e19) + '(告警' + str(e19w) + ')', e19 == 0)
        # ---------------- E20 ----------------
        mcap = re.search(r'^runtime_verification:\s*(\w+)', rs, re.M)
        cap = 6
        if mcap and mcap.group(1) == 'allowed':
            cap = 1
        e20 = sum(1 for x in mf if int(x.get('runtime_tier') or 6) < cap)
        self.add('档位诚实', e20, e20 == 0)
        # ---------------- E21 ----------------
        acp = {r[0] for r in ar if len(r) > 0}
        e21 = sum(1 for r in ledr if len(r) > 3 and r[5] in ('candidate', 'disproved', 'blocked', 'not_applicable', 'fix_present', 'fix_absent') and r[3] not in acp)
        self.add('推导链强制', e21, e21 == 0)
        # ---------------- E22 时序检查（v0.11.0 E-22: 缺时间戳不得绕过——终态行必填 concluded_at） ----------------
        e22 = 0
        atime = {}
        for r in ar:
            if len(r) > 6:
                atime[r[0]] = parse_ts(r[6])
        for r in ledr:
            if len(r) > 7 and r[5] in ('candidate', 'disproved', 'blocked', 'not_applicable', 'fix_present', 'fix_absent'):
                ct = parse_ts(r[7])
                if ct is None:
                    e22 += 1
                    continue
                ot = atime.get(r[3])
                # v0.11.1 E-22: 被引用观察行缺时间戳也 FAIL（两字段必填）
                if ot is None:
                    e22 += 1
                elif ot > ct:
                    e22 += 1
        self.add('时序检查', e22, e22 == 0)
        # ---------------- E23 WU 闭合（v0.11.0 C5/D4 重写: 扫描 batches/B*/WU-*.tsv，分片 sink_id 并集==sink 清单） ----------------
        e23 = 0
        shard_sids = set()
        shard_count = 0
        bdir = os.path.join(S, 'batches')
        if os.path.isdir(bdir):
            for bname in sorted(os.listdir(bdir)):
                bpath = os.path.join(bdir, bname)
                if not os.path.isdir(bpath):
                    continue
                for fn in sorted(os.listdir(bpath)):
                    if re.match(r'WU-\d{4}\.tsv$', fn):
                        shard_count += 1
                        w = read_tsv(os.path.join(bpath, fn))
                        for r in w[1:]:
                            if len(r) > 0 and r[0]:
                                shard_sids.add(r[0])
        # 类级剪枝（S2/S3）的 sink 豁免（不派 WU）
        pruned_sinks23 = set()
        pl23 = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
        if len(pl23) > 1:
            ph23 = pl23[0]
            o_i23, s_i23 = col_opt(ph23, 'operator'), col_opt(ph23, 'scope')
            a2c23 = col_opt(ph23, 'a2_verified')
            for r in pl23[1:]:
                if o_i23 is not None and s_i23 is not None and len(r) > max(o_i23, s_i23) and r[o_i23] in ('S2', 'S3') and r[s_i23].startswith('SINK-'):
                    verified = a2c23 is not None and len(r) > a2c23 and r[a2c23] == 'true'
                    if not verified:
                        continue
                    scope = r[s_i23]
                    for srow in sir:
                        if len(srow) > 2 and (scope == srow[2] or scope.startswith(srow[2] + '-via-')):
                            pruned_sinks23.add(srow[0])
        all_sids = {r[0] for r in sir if len(r) > 0}
        expected_sids = all_sids - pruned_sinks23
        if shard_count == 0 and not expected_sids:
            e23 = 0
        else:
            e23 = len(expected_sids ^ shard_sids)
        self.add('WU 闭合', e23, e23 == 0)
        # ---------------- E27/E28 ----------------
        hyps = [r for r in ledr if len(r) > 1 and (r[1] == 'hypothesis' or (len(r) > 2 and r[2] == 'divergent_reasoning'))]
        e27 = 0
        for r in hyps:
            reason = r[6] if len(r) > 6 else ''
            if not REF_RE.search(reason):
                e27 += 1
        self.add('假设锚点强制', e27, e27 == 0)
        self.add('假设上限', len(hyps), len(hyps) <= 20)
        # ---------------- B10 枚举锚定 ----------------
        e10b2 = 0
        missing_classes = []
        try:
            ktext = open(os.path.join(self.knowledge, 'sinks/_index.md'), encoding='utf-8').read() if hasattr(self, 'knowledge') else ''
            kclasses = set(re.findall(r'SINK-[A-Z0-9-]+', ktext)) - SIGNAL_CLASSES
            inv_classes = {r[2] for r in sir if len(r) > 2}
            zero = set()
            zp = os.path.join(S, 'zero_hit_classes.tsv')
            if os.path.isfile(zp):
                zero = {ln.strip() for ln in open(zp, encoding='utf-8') if ln.strip()}
            ldir = os.path.join(S, 'logs')
            if os.path.isdir(ldir):
                for fn in os.listdir(ldir):
                    if fn.startswith('sinks_') and fn.endswith('.log'):
                        p = os.path.join(ldir, fn)
                        # v0.11.3 run-19 修复：类名直接取文件名（旧代码 'SINK-'+fn[...] 双写前缀致零命中类全漏算）；
                        # 且 PATTERN_UNAVAILABLE（本语言无模式）同样计入零命中——枚举输出即封闭，不依赖 agent 转写
                        head = open(p, encoding='utf-8', errors='replace').read(200)
                        if head.startswith(('ZERO_HITS_WARRANT_REVIEW', 'PATTERN_UNAVAILABLE')):
                            zero.add(fn[len('sinks_'):-len('.log')])
            missing_classes = sorted(kclasses - inv_classes - zero)
            e10b2 = len(missing_classes)
        except Exception:
            e10b2 = 'ERR'
        self.add('枚举锚定(类集合)', e10b2, e10b2 == 0)
        # ---------------- E11b 候选ID确定性强制 ----------------
        e11b = 0
        try:
            inv_locs = {r[1] for r in sir if len(r) > 1}
            ds_idx = col_opt(ch, 'discovery_source')
            for c in cr:
                cid = col(ch, 'candidate_id')
                loc = col(ch, 'location')
                if cid is not None and cid < len(c):
                    idval = c[cid]
                    m = re.match(r'^C-\d{5}-\d{5}-[0-9a-f]{8}$', idval)
                    if not m:
                        e11b += 1
                    elif loc is not None and loc < len(c) and c[loc] not in inv_locs:
                        # v0.11.4 run-19：divergent_reasoning 候选（A5 假设产物）位置是假设锚点非枚举 sink，豁免
                        is_divergent2 = ds_idx is not None and ds_idx < len(c) and c[ds_idx] == 'divergent_reasoning'
                        if not is_divergent2:
                            e11b += 1
        except Exception:
            e11b = 'ERR'
        self.add('候选ID确定性强制', e11b, e11b == 0)
        # ---------------- B12 候选类型一致性 ----------------
        e12b2 = 0
        try:
            inv2 = {r[2] for r in sir if len(r) > 2}
            for c in cr:
                if c[col(ch, 'sink_type')] not in inv2:
                    e12b2 += 1
        except Exception:
            e12b2 = 'ERR'
        self.add('候选类型一致性', e12b2, e12b2 == 0)
        # ---------------- E28 WU 派发记录 ----------------
        e28 = 0
        wu_path = os.path.join(S, 'wu_dispatch.tsv')
        wu_skip = re.search(r'wu_skip_reason\s*:\s*(\S+)', rs)
        if os.path.isfile(wu_path):
            wu = read_tsv(wu_path)
            if len(wu) < 2:
                e28 = 1
            else:
                vcol = col_opt(wu[0], 'verified') if wu else None
                if vcol is not None:
                    for wr in wu[1:]:
                        if vcol >= len(wr) or not wr[vcol]:
                            e28 += 1
        elif not wu_skip:
            e28 = 1
        self.add('WU 派发记录', e28, e28 == 0)
                # ---------------- B18 V文件完整性 ----------------
        e18b = 0
        fd2 = os.path.join(S, 'findings')
        if os.path.isdir(fd2):
            for fn in os.listdir(fd2):
                if FINDING_FILE_RE.match(fn):
                    t = open(os.path.join(fd2, fn), encoding='utf-8', errors='replace').read()
                    secs = ['识别信息', '漏洞摘要', '调用链', 'CVSS', '详细分析', '语义变迁', '证据分级', '三态结论']
                    nsec = sum(1 for s in secs if s in t)
                    refs = len(REF_RE.findall(t))
                    nlines = t.count('\n')
                    cidm = re.search(r'C-\d{5}-\d{5}-[0-9a-f]{8}', t)
                    if nsec < 5 or refs < 3 or nlines < 40 or not cidm:
                        e18b += 1
        self.add('V文件完整性', e18b, e18b == 0)
        # ---------------- E32 候选推理非工具原文（v0.11.0 C1 复活 + B24 fail-closed） ----------------
        e32 = 'ERR'
        try:
            e32 = 0
            ridx = col_opt(ch, 'discovery_reasoning_note')
            if ridx is None:
                e32 = 1  # C1: 16 列 schema 下该列必须存在
            else:
                for c in cr:
                    note = (c[ridx] if ridx < len(c) else '') or ''
                    if not note.strip():
                        e32 += 1  # B24: 空推理说明 FAIL
                    elif re.match(r'^(WARNING|ERROR|INFO)[\s:]', note.strip(), re.I):
                        e32 += 1  # B24: 大小写不敏感防 warn:/Warning 绕过
        except Exception:
            e32 = 'ERR'
        self.add('候选推理非工具原文', e32, e32 == 0)
        # ---------------- E35 finding 文件名格式 ----------------
        e35 = 0
        fd3 = os.path.join(S, 'findings')
        if os.path.isdir(fd3):
            for fn in os.listdir(fd3):
                if fn.startswith('C-') and fn.endswith('.md') and fn != 'machine-fields.json':
                    if not re.match(r'C-\d{5}-\d{5}-[0-9a-f]{8}-[a-z]+-SINK-[A-Z0-9-]+-[A-Za-z0-9_.]+-\d+\.md$', fn):
                        e35 += 1
        self.add('finding 文件名格式', e35, e35 == 0)
        # ---------------- E36 枚举来源强制（v0.11.0 E-16: fail-closed——知识基线缺失不得静默 PASS） ----------------
        e36 = 'ERR'
        try:
            e36 = 0
            sih2 = sinks[0] if sinks else []
            # Check: sink_type values must be from knowledge table (no self-invented names)
            ktext2 = open(os.path.join(self.knowledge, 'sinks/_index.md'), encoding='utf-8').read() if hasattr(self, 'knowledge') else ''
            if not ktext2:
                e36 = 'ERR(知识基线不可读)'
            else:
                known_classes = set(re.findall(r'SINK-[A-Z0-9-]+', ktext2)) - SIGNAL_CLASSES
                for r in sir:
                    if len(r) > 2 and r[2] not in known_classes:
                        e36 += 1
        except Exception:
            e36 = 'ERR'
        self.add('枚举来源强制(禁自造类)', e36, e36 == 0)
        # ---------------- E38 batch_progress 完成率 ----------------
        e38 = 0
        try:
            bp_path = os.path.join(S, 'batch_progress.tsv')
            if os.path.isfile(bp_path):
                bp = read_tsv(bp_path)
                if len(bp) <= 1:
                    e38 = 1  # 空 batch_progress = 批循环未执行
                else:
                    total = len(bp) - 1
                    done = sum(1 for r in bp[1:] if len(r) > 1 and r[1] == 'completed')
                    if done < total:
                        e38 = total - done
        except Exception:
            e38 = 'ERR'
        self.add('batch_progress 完成率', e38, e38 == 0)
        # ---------------- E39 短路质量检查 ----------------
        e39 = 0
        try:
            bp_path = os.path.join(S, 'batch_progress.tsv')
            if os.path.isfile(bp_path):
                bp = read_tsv(bp_path)
                if len(bp) > 1:
                    total_findings = sum(int(r[4]) for r in bp[1:] if len(r) > 4 and r[4].isdigit())
                    if total_findings == 0:
                        # All batches produced 0 findings - check audit_log has real observations
                        al = read_tsv(os.path.join(S, 'audit_log.tsv'))
                        audit_rows = len(al) - 1 if al else 0
                        if audit_rows == 0:
                            e39 = 1  # No findings AND no audit = empty short-circuit
        except Exception:
            e39 = 'ERR'
        self.add('短路质量检查', e39, e39 == 0)
        # ---------------- E53 候选边支撑（v0.11.0 M3: loc 全匹配——同位置多 sink 全部参与判定） ----------------
        e53 = 0
        try:
            flow_rows = read_tsv(os.path.join(S, 'flow_edges.tsv'))
            flow_reachable = set()
            for fr in flow_rows[1:]:
                if len(fr) > 2 and fr[2] == 'reachable':
                    flow_reachable.add(fr[1] if len(fr) > 1 else '')
            loc_to_sids = {}
            for r in sir:
                if len(r) > 1 and r[1]:
                    loc_to_sids.setdefault(r[1], []).append(r[0])
            ds_idx53 = col_opt(ch, 'discovery_source')
            for c in cr:
                if vcol2 is not None and vcol2 < len(c) and c[vcol2] == 'confirmed':
                    loc = c[col(ch, 'location')]
                    # v0.11.4 run-19：divergent_reasoning 候选（A5 假设产物）位置是假设锚点非枚举 sink，边支撑由假设行证据保证
                    if ds_idx53 is not None and ds_idx53 < len(c) and c[ds_idx53] == 'divergent_reasoning':
                        continue
                    sids = loc_to_sids.get(loc, [])
                    if not sids or not any(s in flow_reachable for s in sids):
                        e53 += 1
        except Exception:
            e53 = 'ERR'
        self.add('候选边支撑', e53, e53 == 0)
        # ---------------- E54 剪枝 A2 复核（v0.10.0） ----------------
        e54 = 0
        try:
            pl2 = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
            a2col = col_opt(pl2[0], 'a2_verified') if len(pl2) > 1 else None
            if a2col is not None:
                for r in pl2[1:]:
                    if a2col >= len(r) or r[a2col] not in ('true', 'false'):
                        e54 += 1
            else:
                e54 = len(pl2) - 1 if len(pl2) > 1 else 0
        except Exception:
            e54 = 'ERR'
        self.add('剪枝 A2 复核', e54, e54 == 0)
        # ---------------- E55 flow 边两端节点存在 ----------------
        e55 = 0
        try:
            flow_rows2 = read_tsv(os.path.join(S, 'flow_edges.tsv'))
            sink_ids = {r[0] for r in sir}
            src_ids = {r[0] for r in sor}
            for fr in flow_rows2[1:]:
                if len(fr) > 1 and fr[0] and fr[1]:
                    # v0.11.3 run-19：source='-' 的边（未实体化源：无路径或源在未分析批次/跨模块）只验 sink 端
                    if fr[0] == '-':
                        if fr[1] not in sink_ids:
                            e55 += 1
                        continue
                    if fr[0] not in src_ids or fr[1] not in sink_ids:
                        e55 += 1
        except Exception:
            e55 = 'ERR'
        self.add('flow 边节点存在', e55, e55 == 0)
        # ---------------- E56-E59 图实体化（v0.10.1 doc 99） ----------------
        # E56 图节点投影完整性：gate 独立重算节点集 == build_graph 投影（防 build bug）
        # E57 图边投影完整性：gate 独立重算边集 == build_graph 投影
        # E58 图投影确定性：图文件 == 账本投影（防手改/陈旧），build 两次一致（防非确定）
        # E59 图边端点存在：每条边 from/to 在节点集（GenCPT host-missing 悬空边教训）
        e56 = 'ERR'; e57 = 'ERR'; e58 = 'ERR'; e59 = 'ERR'
        try:
            def g_edge_id(t, frm, to, attrs):
                return hashlib.md5((t + '|' + frm + '|' + to + '|' + cjs(attrs)).encode()).hexdigest()[:16]
            if self._b1 and self._b1[0] != 'ERR':
                b_nodes, b_edges = self._b1[0], self._b1[1]
                b2n, b2e = build_graph.build(S, write=False)
                canon1 = build_graph.serialize_pair(b_nodes, b_edges)
                canon2 = build_graph.serialize_pair(b2n, b2e)
                # 七规约：解析对 CRLF 透明——快照规范化后再比对
                snap_norm = self._kg_snap.replace('\r\n', '\n').rstrip('\n')
                e58 = 0 if (canon1 == canon2 and canon1 == snap_norm) else 1
                # ---- gate 侧独立重算（第二份实现，固定列序路径，与 build_graph 列名路径互补） ----
                pr_rows = []
                pl2 = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
                if len(pl2) > 1:
                    ph = pl2[0]
                    o_i, c_i, s_i = col_opt(ph, 'operator'), col_opt(ph, 'criterion'), col_opt(ph, 'scope')
                    for r in pl2[1:]:
                        if o_i is not None and s_i is not None and len(r) > max(o_i, s_i) and r[o_i] and r[s_i]:
                            crit = r[c_i] if c_i is not None and len(r) > c_i else ''
                            pr_rows.append((r[o_i], crit, r[s_i]))
                led_by = {}
                for r in ledr:
                    if len(r) > 5 and r[0]:
                        led_by.setdefault(r[0], []).append(r)
                def g_status(basis_id, ntype, tkey):
                    for (op, crit, scope) in pr_rows:
                        if ntype == 'sink' and (scope == tkey or scope.startswith(tkey + '-via-')):
                            return ('pruned', op, crit or scope)
                        if ntype == 'source' and scope == 'SOURCE-' + tkey:
                            return ('pruned', op, crit or scope)
                    rows = led_by.get(basis_id, [])
                    if not rows:
                        return ('unchecked', '', '')
                    terms = [r[5] for r in rows]
                    if terms and all(t in ('disproved', 'not_applicable') for t in terms):
                        return ('pruned', '', ';'.join(sorted(set(r[6] for r in rows if len(r) > 6 and r[6])))[:200])
                    if terms and all(t == 'blocked' for t in terms):
                        return ('blocked', '', '')  # v0.11.1 E-06: 与 build_graph basis_status 同步
                    if any(t in ('candidate', 'confirmed') for t in terms):
                        return ('candidate', '', '')
                    return ('unchecked', '', '')
                exp_nodes = set()
                for r in sir:
                    if len(r) < 3 or not r[0]:
                        continue
                    st, pb, prn = g_status(r[0], 'sink', r[2])
                    n = {'id': 'sink:' + r[0], 'type': 'sink',
                         'attrs': {'file_line': r[1] if len(r) > 1 else '', 'sink_type': r[2], 'symbol': r[3] if len(r) > 3 else ''},
                         'status': st}
                    if st == 'pruned' and pb:
                        n['pruned_by'] = pb
                    if st == 'pruned' and prn:
                        n['pruned_reason'] = prn
                    exp_nodes.add(cjs(n))
                for r in sor:
                    if len(r) < 3 or not r[0]:
                        continue
                    st, pb, prn = g_status(r[0], 'source', r[2])
                    n = {'id': 'source:' + r[0], 'type': 'source',
                         'attrs': {'file_line': r[1] if len(r) > 1 else '', 'entry_type': r[2], 'symbol': r[3] if len(r) > 3 else ''},
                         'status': st}
                    if st == 'pruned' and pb:
                        n['pruned_by'] = pb
                    if st == 'pruned' and prn:
                        n['pruned_reason'] = prn
                    exp_nodes.add(cjs(n))
                for r in fir:
                    if len(r) < 2 or not r[0]:
                        continue
                    exp_nodes.add(cjs({'id': 'file:' + r[0], 'type': 'file',
                                       'attrs': {'lang': r[2] if len(r) > 2 else '', 'type': r[1] if len(r) > 1 else ''},
                                       'status': 'active'}))
                for r in ledr:
                    if len(r) < 4 or not r[0] or not r[3]:
                        continue
                    exp_nodes.add(cjs({'id': 'checkpoint:' + r[3], 'type': 'checkpoint',
                                       'attrs': {'direction': r[1] if len(r) > 1 else '', 'mechanism': r[2] if len(r) > 2 else '', 'basis_id': r[0]},
                                       'status': r[5] if len(r) > 5 else ''}))
                loc2sids = {}
                for r in sir:
                    if len(r) > 1 and r[1]:
                        loc2sids.setdefault(r[1], []).append(r[0])
                mfmap = {str(x.get('candidate_id')): x for x in mf if isinstance(x, dict) and x.get('candidate_id')}
                for r in cr:
                    if len(r) < 2 or not r[0]:
                        continue
                    cid = r[0]
                    exp_nodes.add(cjs({'id': 'candidate:' + cid, 'type': 'candidate',
                                       'attrs': {'location': r[1] if len(r) > 1 else '', 'sink_type': r[2] if len(r) > 2 else '',
                                                 'severity': r[3] if len(r) > 3 else '', 'rcg_id': r[4] if len(r) > 4 else ''},
                                       'status': r[6] if len(r) > 6 else ''}))
                    ref = r[9] if len(r) > 9 else ''
                    if ref:
                        fm = mfmap.get(cid, {})
                        exp_nodes.add(cjs({'id': 'finding:' + ref, 'type': 'finding',
                                           'attrs': {'candidate_id': cid, 'severity': fm.get('severity', ''),
                                                     'confidence': fm.get('confidence', ''), 'evidence_grade': fm.get('evidence_grade', '')},
                                           'status': 'active'}))
                exp_edges = set()
                def aedge(t, frm, to, attrs):
                    eid = g_edge_id(t, frm, to, attrs)
                    exp_edges.add(cjs({'id': eid, 'edge_type': t, 'from': frm, 'to': to, 'attrs': attrs}))
                flow_rows = read_tsv(os.path.join(S, 'flow_edges.tsv'))
                for r in (flow_rows[1:] if len(flow_rows) > 1 else []):
                    if len(r) < 3 or not r[0] or not r[1]:
                        continue
                    # v0.11.3 run-19：与 build_graph 同口径——source='-' 的边不入图（无真实源端点）
                    if r[0] == '-':
                        continue
                    attrs = {}
                    for k, i in (('direction', 2), ('hops', 3), ('evidence_refs', 4), ('judged_by', 5), ('timestamp', 6)):
                        if len(r) > i and r[i]:
                            attrs[k] = r[i]
                    aedge('flow', 'source:' + r[0], 'sink:' + r[1], attrs)
                sink_ids_g = {r[0] for r in sir}
                src_ids_g = {r[0] for r in sor}
                file_ids_g = {r[0] for r in fir if len(r) > 0 and r[0]}
                for r in ledr:
                    if len(r) < 4 or not r[0] or not r[3]:
                        continue
                    if r[1] not in ('backward', 'forward', 'terminal'):
                        continue
                    basis, cp_id = r[0], r[3]
                    prefix = 'sink:' if basis in sink_ids_g else ('source:' if basis in src_ids_g else ('file:' if basis in file_ids_g else 'basis:'))
                    attrs = {}
                    if len(r) > 1 and r[1]:
                        attrs['direction'] = r[1]
                    if len(r) > 2 and r[2]:
                        attrs['mechanism'] = r[2]
                    aedge('basis', prefix + basis, 'checkpoint:' + cp_id, attrs)
                    cands = r[4] if len(r) > 4 else ''
                    for cc in ID_RE.findall(cands):
                        aedge('derived', 'checkpoint:' + cp_id, 'candidate:' + cc, {'via': 'ledger_candidate_ids'})
                for r in cr:
                    if len(r) < 2 or not r[0]:
                        continue
                    cid = r[0]
                    loc = r[1] if len(r) > 1 else ''
                    if loc in loc2sids:
                        for sid in loc2sids[loc]:
                            aedge('derived', 'sink:' + sid, 'candidate:' + cid, {'via': 'location_match'})
                    ref = r[9] if len(r) > 9 else ''
                    if ref:
                        aedge('derived', 'candidate:' + cid, 'finding:' + ref, {'via': 'report_record_ref'})
                got_nodes = {cjs(n) for n in b_nodes}
                got_edges = {cjs(e) for e in b_edges}
                e56 = len(exp_nodes ^ got_nodes)
                e57 = len(exp_edges ^ got_edges)
                node_ids = {n['id'] for n in b_nodes}
                e59 = sum(1 for e in b_edges if e['from'] not in node_ids or e['to'] not in node_ids)
        except Exception:
            pass
        self.add('图节点投影完整性', e56, e56 == 0)
        self.add('图边投影完整性', e57, e57 == 0)
        self.add('图投影确定性', e58, e58 == 0)
        self.add('图边端点存在', e59, e59 == 0)
        # ---------------- v0.11.0 新方程批（doc 102 P1 G9-G15） ----------------
        # ---------------- E60 flow 边值域（M5/B09） ----------------
        e60 = 0
        try:
            for fr in flow_rows2[1:]:
                if len(fr) < 3 or not fr[0] or not fr[1]:
                    continue
                if fr[2] not in ('reachable', 'blocked_at', 'no_path'):
                    e60 += 1
                if fr[2] == 'reachable':
                    ev = fr[4] if len(fr) > 4 else ''
                    if not ev or not REF_RE.search(ev):
                        e60 += 1
                hops = fr[3] if len(fr) > 3 else ''
                if not hops:
                    e60 += 1  # v0.11.1 B-N3: hops 必填（整数或 '-'）
                elif hops != '-' and not hops.isdigit():
                    e60 += 1
        except Exception:
            e60 = 'ERR'
        self.add('flow 边值域', e60, e60 == 0)
        # ---------------- E61 V 文件候选映射（M4） ----------------
        e61 = 0
        try:
            ref_to_cid = {}
            for c in cr:
                if vcol2 is not None and vcol2 < len(c) and c[vcol2] == 'confirmed':
                    ref = c[col(ch, 'report_record_ref')] if len(c) > col(ch, 'report_record_ref') else ''
                    cid = c[col(ch, 'candidate_id')]
                    if not re.match(r'^V\d{2}$', ref):
                        e61 += 1
                    if ref and ref in ref_to_cid and ref_to_cid[ref] != cid:
                        e61 += 1
                    if ref:
                        ref_to_cid[ref] = cid
            for c in cr:
                if vcol2 is not None and vcol2 < len(c) and c[vcol2] == 'confirmed':
                    ref = c[col(ch, 'report_record_ref')] if len(c) > col(ch, 'report_record_ref') else ''
                    cid = c[col(ch, 'candidate_id')]
                    # 文件名前缀 = candidate_id（不是 report_record_ref 的 V{N}——文件名
                    # 在阶段2确认当轮立即写死，V{N} 排名只在 report.md 最终合并时才能
                    # 算出并回填进标题行，见 report-delivery/SKILL.md Part 1/Part 2）。
                    matched = [f for f in vfiles if f.startswith(cid + '-')]
                    if not matched:
                        e61 += 1
                    else:
                        try:
                            vtxt = open(os.path.join(S, 'findings', matched[0]), encoding='utf-8', errors='replace').read()
                            if cid not in vtxt:
                                e61 += 1
                            elif ref and not re.search(r'#\s*' + re.escape(ref) + r'\b', vtxt.splitlines()[0] if vtxt else ''):
                                e61 += 1  # 标题行 # V{N} 必须与 report_record_ref 一致（Part 2 机械回填的产物）
                        except Exception:
                            e61 += 1
        except Exception:
            e61 = 'ERR'
        self.add('V 文件候选映射', e61, e61 == 0)
        # ---------------- E62 剪枝边一致性（M14） ----------------
        e62 = 0
        try:
            pruned_src_types = set()
            pl3 = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
            if len(pl3) > 1:
                ph3 = pl3[0]
                o_i3, s_i3 = col_opt(ph3, 'operator'), col_opt(ph3, 'scope')
                a2c3 = col_opt(ph3, 'a2_verified')
                for r in pl3[1:]:
                    if o_i3 is not None and s_i3 is not None and len(r) > max(o_i3, s_i3) and r[o_i3] == 'S1' and r[s_i3].startswith('SOURCE-'):
                        verified = a2c3 is not None and len(r) > a2c3 and r[a2c3] == 'true'
                        if verified:
                            pruned_src_types.add(r[s_i3][len('SOURCE-'):])
            if pruned_src_types:
                src_entry = {r[0]: r[2] for r in sor if len(r) > 2}
                for fr in flow_rows2[1:]:
                    if len(fr) > 2 and fr[0] in src_entry and src_entry[fr[0]] in pruned_src_types and fr[2] == 'reachable':
                        e62 += 1
        except Exception:
            e62 = 'ERR'
        self.add('剪枝边一致性', e62, e62 == 0)
        # ---------------- E63 账本枚举封闭（B10/B11） ----------------
        e63 = 0
        valid_dir = {'backward', 'forward', 'terminal', 'fix_presence', 'hypothesis'}
        valid_term = {'未检查', 'candidate', 'disproved', 'not_applicable', 'blocked', 'unconfirmed', 'fix_present', 'fix_absent'}
        for r in ledr:
            if len(r) > 1 and r[1] not in valid_dir:
                e63 += 1
            if len(r) > 5 and r[5] not in valid_term:
                e63 += 1
        self.add('账本枚举封闭', e63, e63 == 0)
        # ---------------- E64 证据密度下限（B06/B12 换皮第四变体） ----------------
        e64 = 0
        terminal_total = 0
        terminal_noev = 0
        for r in ledr:
            if len(r) > 6 and r[5] in ('disproved', 'not_applicable'):
                terminal_total += 1
                reason = r[6]
                if reason.startswith('prefilter_no_exec:'):
                    continue
                if not REF_RE.search(reason) and not CLUSTER_RE.search(reason):
                    terminal_noev += 1
        if terminal_total > 0 and terminal_noev / terminal_total > 0.2:
            e64 = terminal_noev
        self.add('证据密度下限', e64, e64 == 0)
        # ---------------- E65 簇覆盖上限（B06 空壳簇：行数>500 或引用 basis 数>100；v0.11.1 B-N1/N2 修正） ----------------
        e65 = 0
        basis_id_list65 = sorted({r[0] for r in ledr if len(r) > 0 and r[0]}, key=len, reverse=True)
        for f in clusters:
            try:
                content = open(os.path.join(S, 'clusters', f), encoding='utf-8', errors='replace').read()
                nlines = content.count(chr(10)) + 1
                if nlines > 500:
                    e65 += 1
                    continue
                # 全行数范围做 basis 计数（≤50 行的小簇也不逃逸；分块 alternation 防编译爆炸）
                if basis_id_list65:
                    found = set()
                    for i in range(0, len(basis_id_list65), 500):
                        chunk = basis_id_list65[i:i + 500]
                        pat = re.compile('|'.join(re.escape(s) for s in chunk))
                        for m in pat.finditer(content):
                            found.add(m.group(0))
                            if len(found) > 100:
                                break
                        if len(found) > 100:
                            break
                    if len(found) > 100:
                        e65 += 1
            except Exception:
                pass
        self.add('簇覆盖上限', e65, e65 == 0)
        # ---------------- E67 reviewer 派发痕迹（G-09/C7） ----------------
        e67 = 0
        llm_subtasks = ['0.5', '1.2', '1.3', '1.4', '1.5b', '2.1', '2.2', '3.1']
        for st in llm_subtasks:
            p = os.path.join(S, 'reviews', st + '-review.md')
            if not os.path.isfile(p):
                e67 += 1
            else:
                try:
                    t2 = open(p, encoding='utf-8', errors='replace').read()
                    if 'PASS' not in t2 and 'FAIL' not in t2:
                        e67 += 1
                except Exception:
                    e67 += 1
        self.add('reviewer 派发痕迹', e67, e67 == 0)
        # ---------------- E68 终态 sink 边闭合（G-10: disproved/NA 无边闭合通道封堵） ----------------
        e68 = 0
        try:
            flow_any = set()
            for fr in flow_rows2[1:]:
                if len(fr) > 1 and fr[1]:
                    flow_any.add(fr[1])
            pruned_sinks68 = set()
            pl68 = read_tsv(os.path.join(S, 'pruning_ledger.tsv'))
            if len(pl68) > 1:
                ph68 = pl68[0]
                o_i68, s_i68 = col_opt(ph68, 'operator'), col_opt(ph68, 'scope')
                a2c68 = col_opt(ph68, 'a2_verified')
                for r in pl68[1:]:
                    if o_i68 is not None and s_i68 is not None and len(r) > max(o_i68, s_i68) and r[o_i68] in ('S2', 'S3') and r[s_i68].startswith('SINK-'):
                        verified = a2c68 is not None and len(r) > a2c68 and r[a2c68] == 'true'
                        if not verified:
                            continue
                        scope = r[s_i68]
                        for srow in sir:
                            if len(srow) > 2 and (scope == srow[2] or scope.startswith(srow[2] + '-via-')):
                                pruned_sinks68.add(srow[0])
            for r in ledr:
                if len(r) > 5 and r[1] == 'backward' and r[5] in ('candidate', 'disproved', 'blocked'):
                    sid = r[0]
                    if sid in pruned_sinks68:
                        continue
                    reason = r[6] if len(r) > 6 else ''
                    if reason.startswith(('false_rule_hit:', 'prefilter_no_exec:')):
                        continue
                    if sid not in flow_any:
                        e68 += 1
        except Exception:
            e68 = 'ERR'
        self.add('终态 sink 边闭合', e68, e68 == 0)
        # ---------------- E69 合并守恒（G-03/E24: 候选行集==ledger candidate_ids 引用并集） ----------------
        e69 = 0
        try:
            cand_ids = {r[0] for r in cr if len(r) > 0 and r[0]}
            ledger_cids = set()
            for r in ledr:
                if len(r) > 4 and r[4]:
                    ledger_cids.update(ID_RE.findall(r[4]))
            e69 = len(cand_ids ^ ledger_cids)
        except Exception:
            e69 = 'ERR'
        self.add('合并守恒', e69, e69 == 0)
        # ---------------- E70 audit_log 追加单调性（G-19: 补写过去时间戳必破坏） ----------------
        e70 = 0
        try:
            prev_ts = None
            for r in ar:
                ts_col = None
                for cand_col_name in ('reviewed_at', 'timestamp', 'observed_at'):
                    if ah and cand_col_name in ah:
                        ts_col = ah.index(cand_col_name)
                        break
                if ts_col is None:
                    break
                if len(r) > ts_col and r[ts_col]:
                    t = parse_ts(r[ts_col])
                    if t is not None:
                        if prev_ts is not None and t < prev_ts:
                            e70 += 1
                        prev_ts = t
        except Exception:
            e70 = 'ERR'
        self.add('audit_log 追加单调性', e70, e70 == 0)
        # ---------------- E71 WU 分片质量（v0.11.2 升级: schema 三合一——header/verdict 枚举/行数守恒） ----------------
        # run-18-spring 验尸：19/42 分片 schema 坏（5 种 header）、8 个行数不守恒、verdict 列错位——subagent 输出无机械约束
        e71 = 0
        try:
            wm71 = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
            if len(wm71) > 1:
                h71 = wm71[0]
                sid_col = col_opt(h71, 'sink_ids')
                wid_col = col_opt(h71, 'wu_id')
                if sid_col is None or wid_col is None:
                    e71 = 'ERR(wu_manifest schema)'
                else:
                    for r in wm71[1:]:
                        if len(r) <= max(sid_col, wid_col):
                            continue
                        expected = len([s for s in r[sid_col].split(';') if s])
                        bn = r[col_opt(h71, 'batch_num')] if col_opt(h71, 'batch_num') is not None and len(r) > col_opt(h71, 'batch_num') else ''
                        shard = os.path.join(S, 'batches', bn, r[wid_col] + '.tsv')
                        if os.path.isfile(shard):
                            srows = read_tsv(shard)
                            # ① header 必须 5 列权威 schema
                            if len(srows) > 0 and srows[0][:5] != ['sink_id', 'verdict', 'five_segment_evidence', 'evidence_refs', 'reviewed_at']:
                                e71 += 1
                                continue
                            data = [x for x in srows[1:] if x and any(x)]
                            # ② 行数守恒
                            if len(data) != expected:
                                e71 += 1
                            # ③ verdict 枚举封闭（列错位/字符串污染即 FAIL）
                            for x in data:
                                if len(x) < 2 or x[1] not in ('candidate', 'disproved', 'blocked'):
                                    e71 += 1
        except Exception:
            e71 = 'ERR'
        self.add('WU 分片质量', e71, e71 == 0)
        # ---------------- E73 分片回填对账（v0.11.2 run-18 验尸: 42 分片 0 回填——分片产出后必须回填 ledger 终态） ----------------
        e73 = 0
        try:
            shard_sids73 = set()
            bdir73 = os.path.join(S, 'batches')
            if os.path.isdir(bdir73):
                for bname in sorted(os.listdir(bdir73)):
                    for fn in sorted(os.listdir(os.path.join(bdir73, bname))):
                        if re.match(r'WU-\d{4}\.tsv$', fn):
                            for x in read_tsv(os.path.join(bdir73, bname, fn))[1:]:
                                if x and x[0]:
                                    shard_sids73.add(x[0])
            led_term73 = {}
            for r in ledr:
                if len(r) > 1 and r[1] == 'backward':
                    led_term73[r[0]] = r[5] if len(r) > 5 else ''
            for s in shard_sids73:
                if led_term73.get(s, '未检查') == '未检查':
                    e73 += 1
        except Exception:
            e73 = 'ERR'
        self.add('分片回填对账', e73, e73 == 0)
        # ---------------- E74 发现索引对账（v0.11.2 run-18 验尸: 6 findings 但 live index 0 行） ----------------
        e74 = 0
        try:
            lfi_path = os.path.join(S, 'live_findings_index.md')
            idx_rows = 0
            if os.path.isfile(lfi_path):
                idx_rows = sum(1 for l in open(lfi_path, encoding='utf-8', errors='replace') if l.startswith('|') and l.strip() and 'Batch' not in l and '---' not in l)
            n_findings = len(vfiles) if 'vfiles' in dir() else 0
            if n_findings > 0 and idx_rows < n_findings:
                e74 = n_findings - idx_rows
        except Exception:
            e74 = 'ERR'
        self.add('发现索引对账', e74, e74 == 0)
        # ---------------- v0.11.3 扫雷信息级联三方程（doc 115 §5 机械兜底：防级联滥用） ----------------
        # E75 信息板格式：fact/clue/break 每条必须含可解析 file:line 证据（无证据条目=空口判定入口，FAIL）
        # E76 结论隔离：信息板数据行禁止出现 candidate/disproved/blocked/confirmed 结论词（定理 1 机械化——结论入板=错误级联入口，FAIL）
        # E77 级联覆盖：reachable 边的上游未查检查点必须全部出现在已派 WU 或精查清单（雷邻一个不漏）
        e75 = 0
        e76 = 0
        e77 = 0
        try:
            board_rows = []  # (section, cols)
            bp = os.path.join(S, 'mine_scan_board.md')
            if os.path.isfile(bp):
                section = ''
                for ln in open(bp, encoding='utf-8', errors='replace'):
                    ln = ln.rstrip('\r\n')
                    m = re.match(r'^##\s*(\S+)', ln.strip())
                    if m:
                        section = m.group(1).strip()
                        continue
                    if ln.strip().startswith('|') and '---' not in ln:
                        cols = [c.strip() for c in ln.strip().strip('|').split('|')]
                        if cols and cols[0] in ('id', 'checkpoint_id'):
                            continue  # 表头行
                        board_rows.append((section, cols, ln))
            # E75：fact/clue/break 区数据行的证据列（第 3 列）必须含 file:line
            for sec, cols, _ln in board_rows:
                if sec.startswith(('fact', 'clue', 'break')):
                    if len(cols) < 3 or not REF_RE.search(cols[2]):
                        e75 += 1
            # E76：全部数据行禁止结论词（单词边界精确匹配，防子串巧合）
            concl_re = re.compile(r'\b(candidate|disproved|blocked|confirmed)\b')
            for sec, cols, _ln in board_rows:
                if concl_re.search(_ln):
                    e76 += 1
            # E77：flow_edges 中 direction=reachable 的边，其 evidence_refs 链上文件 + source 的未查检查点
            # 必须出现在精查清单（checkpoint_id）或已派 WU（文件 WU 状态非 pending）
            fe77 = read_tsv(os.path.join(S, 'flow_edges.tsv'))
            fe77h, fe77r = (fe77[0], fe77[1:]) if len(fe77) > 1 else ([], [])
            if fe77h:
                c_src, c_dir, c_ev = col_opt(fe77h, 'source_id'), col_opt(fe77h, 'direction'), col_opt(fe77h, 'evidence_refs')
                # ledger 索引：basis_id -> (terminal_state, check_point_id)
                led_idx = {}
                for r in ledr:
                    if len(r) > 5:
                        led_idx.setdefault(r[0], []).append((r[5], r[3] if len(r) > 3 else ''))
                # 精查清单 checkpoint 集合
                fine_list = set()
                for sec, cols, _ln in board_rows:
                    if sec.startswith('精查') and cols and cols[0]:
                        fine_list.add(cols[0])
                # WU 派发映射：文件名 -> status
                wm77 = read_tsv(os.path.join(S, 'wu_manifest.tsv'))
                wm77r = wm77[1:] if len(wm77) > 1 else []
                wu_status = {}
                for r in wm77r:
                    if len(r) > 5 and r[1]:
                        wu_status[r[1]] = r[5]
                # source_id -> 所属文件（source_inventory file:line 前缀）
                src_file = {}
                for r in sor:
                    if len(r) > 1 and r[0] and ':' in r[1]:
                        src_file[r[0]] = r[1].rsplit(':', 1)[0]
                for r in fe77r:
                    if c_src is None or c_dir is None or c_ev is None or len(r) <= max(c_src, c_dir, c_ev):
                        continue
                    if r[c_dir] != 'reachable':
                        continue
                    upstream = set()
                    if r[c_src]:
                        upstream.add(r[c_src])
                    if c_ev < len(r):
                        for fm in REF_RE.finditer(r[c_ev]):
                            f_ref = fm.group(1)
                            if f_ref.startswith('./'):
                                f_ref = f_ref[2:]  # 与 file_lines 同口径：./ 前缀规范化
                            upstream.add(f_ref)
                    for basis in upstream:
                        rows_b = led_idx.get(basis, [])
                        if not rows_b:
                            continue  # 账本无此行（无检查点），不追责
                        for st77, cpid in rows_b:
                            if st77 != '未检查':
                                continue
                            cov_wu = False
                            if basis in wu_status and wu_status[basis] != 'pending':
                                cov_wu = True
                            else:
                                # source 检查点按所属文件找 WU；文件检查点按文件路径找 WU
                                f77 = src_file.get(basis, basis)
                                if f77 in wu_status and wu_status[f77] != 'pending':
                                    cov_wu = True
                            if cpid not in fine_list and not cov_wu:
                                e77 += 1
        except Exception:
            e75 = 'ERR'
            e76 = 'ERR'
            e77 = 'ERR'
        self.add('信息板格式', e75, e75 == 0)
        self.add('信息板结论隔离', e76, e76 == 0)
        self.add('级联覆盖', e77, e77 == 0)
        # ---------------- E72 看板行数（G-17: 进度可见性机械存在性） ----------------
        e72 = 0
        try:
            bp72 = read_tsv(os.path.join(S, 'batch_progress.tsv'))
            done_batches = sum(1 for r in bp72[1:] if len(r) > 1 and r[1] == 'completed')
            pb72 = os.path.join(S, 'progress_board.md')
            board_lines = 0
            if os.path.isfile(pb72):
                board_lines = sum(1 for _ in open(pb72, encoding='utf-8', errors='replace'))
            if done_batches > 0 and board_lines < done_batches + 2:
                e72 = done_batches + 2 - board_lines
        except Exception:
            e72 = 'ERR'
        self.add('看板行数', e72, e72 == 0)
        # ---------------- E52 簇引用真实性 ----------------
        # cluster_conclusion 引用的簇文件必须真实包含该检查点的 basis_id（词边界精确匹配，防子串巧合）
        # 注（v0.11.0 B04 修正）：本方程只保证「引用与内容相符」，语义真假归 reviewer/A2（不宣称根治换皮）
        e52 = 0
        try:
            cluster_content = {}
            for f in clusters:
                try:
                    cluster_content[f] = open(os.path.join(S, 'clusters', f), encoding='utf-8', errors='replace').read()
                except Exception:
                    cluster_content[f] = ''
            for r in ledr:
                if len(r) > 6 and r[6] and r[6].startswith('cluster_conclusion:'):
                    m = CLUSTER_RE.search(r[6])
                    if m and m.group(1) in cluster_content:
                        basis = r[0] if r else ''
                        if basis and not re.search(r'(?<![0-9a-f])' + re.escape(basis) + r'(?![0-9a-f])', cluster_content[m.group(1)]):
                            e52 += 1
        except Exception:
            e52 = 'ERR'
        self.add('簇引用真实性', e52, e52 == 0)
        # ---------------- E51 run_fingerprint 检查（v0.11.0 F-E2E-12: 重算比对，不只验非空） ----------------
        e51 = 0
        fp_m = re.search(r'run_fingerprint\s*:\s*(\S+)', rs)
        if not fp_m or fp_m.group(1) in ('null', 'None', ''):
            e51 = 1
        else:
            # 重算（v0.11.1 与 §7 A 类权威口径完全一致：sha256[:16] + json.dumps sort_keys + 按 candidate_id 排序）
            try:
                core = [{k: x.get(k, '') for k in ('candidate_id', 'location', 'sink_type', 'severity', 'root_cause_group_id', 'verdict')}
                        for x in mf if isinstance(x, dict)]
                core.sort(key=lambda x: str(x.get('candidate_id', '')))
                recomputed = hashlib.sha256(json.dumps(core, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
                if recomputed != fp_m.group(1):
                    e51 = 1
            except Exception:
                e51 = 'ERR'
        self.add('run_fingerprint 检查', e51, e51 == 0)
        # ---------------- E50 剪枝判据落盘 ----------------
        e50 = 0
        pl_path = os.path.join(S, 'pruning_ledger.tsv')
        if os.path.isfile(pl_path):
            pl = read_tsv(pl_path)
            for r in pl[1:]:
                if len(r) < 4 or not r[0] or not r[1] or not r[2] or not r[3]:
                    e50 += 1
        else:
            e50 = 1
        self.add('剪枝判据落盘', e50, e50 == 0)
        # ---------------- E49 枚举对账（v0.11.0 E-20: 结构对账——logs 滤 test 去重后行数==清单行数） ----------------
        e49 = 0
        try:
            ldir49 = os.path.join(S, 'logs')
            if os.path.isdir(ldir49):
                total_log = 0
                for fn in os.listdir(ldir49):
                    if fn.startswith('sinks_') and fn.endswith('.log'):
                        p = os.path.join(ldir49, fn)
                        try:
                            content = open(p, encoding='utf-8', errors='replace').read(500)
                            if content.startswith(('ZERO_HITS_WARRANT_REVIEW', 'PATTERN_UNAVAILABLE')):
                                continue
                            seen_keys = set()
                            for line in open(p, encoding='utf-8', errors='replace'):
                                line = line.strip()
                                if not line:
                                    continue
                                parts = line.split(':', 2)
                                if len(parts) < 2:
                                    continue
                                path = parts[0]
                                if path.startswith('./'):
                                    path = path[2:]
                                if '/test/' in path or path.startswith('test/'):
                                    continue
                                seen_keys.add(path + ':' + parts[1])
                            total_log += len(seen_keys)
                        except Exception:
                            pass
                e49 = abs(total_log - len(sir))
        except Exception:
            e49 = 'ERR'
        self.add('枚举对账', e49, e49 == 0)
        # ---------------- E48 批进度记录检查 ----------------
        # todo 是宿主会话工具（GenSource 无法强制），进度可见性的强制解是文件态：
        # gate_progress 必须含 1.2 批进度行（每 5 批至少 1 条），数量 >= ceil(completed_batches/5)
        e48 = 0
        gp_path48 = os.path.join(S, 'gate_progress.tsv')
        completed_batches = 0
        bp48_path = os.path.join(S, 'batch_progress.tsv')
        if os.path.isfile(bp48_path):
            bp48 = read_tsv(bp48_path)
            completed_batches = sum(1 for r in bp48[1:] if len(r) > 1 and r[1] == 'completed')
        if completed_batches > 0:
            expected_progress_rows = (completed_batches + 4) // 5  # ceil(batches/5)
            progress_rows = 0
            if os.path.isfile(gp_path48):
                gp48 = read_tsv(gp_path48)
                progress_rows = sum(1 for r in gp48[1:] if r and '1.2' in str(r[0]) and 'batch' in str(r[0]).lower())
            if progress_rows < expected_progress_rows:
                e48 = expected_progress_rows - progress_rows
            # v0.9.4 progress_board 行数检查（文件态看板）
            pb_path = os.path.join(S, 'progress_board.md')
            if os.path.isfile(pb_path):
                pb_rows = sum(1 for ln in open(pb_path, encoding='utf-8', errors='replace') if ln.strip().startswith('| B'))
                if pb_rows < expected_progress_rows:
                    e48 += expected_progress_rows - pb_rows
        self.add('批进度记录检查', e48, e48 == 0)
        # ---------------- E43 批数合理性（v0.11.0 F-E2E-15: 删硬编码 50，改冻结清单动态对账） ----------------
        # 对账常数一律从冻结清单动态推导（host-reconciliation:6）：batch_progress 批数 == wu_manifest.batch_num 唯一值
        e43 = 0
        bp_path43 = os.path.join(S, 'batch_progress.tsv')
        wm_path43 = os.path.join(S, 'wu_manifest.tsv')
        if os.path.isfile(bp_path43) and os.path.isfile(wm_path43):
            bp43 = read_tsv(bp_path43)
            wm43 = read_tsv(wm_path43)
            bp_batches = {r[0] for r in bp43[1:] if len(r) > 0 and r[0]}
            if len(wm43) > 1:
                bn_col = col_opt(wm43[0], 'batch_num')
                if bn_col is None:
                    e43 = 'ERR(wu_manifest 无 batch_num 列)'
                else:
                    wm_batches = {r[bn_col] for r in wm43[1:] if len(r) > bn_col and r[bn_col]}
                    e43 = len(bp_batches ^ wm_batches)
            else:
                e43 = len(bp_batches)
        self.add('批数合理性', e43, e43 == 0)
        # ---------------- E44 候选同根因合并（v0.11.0 G-14 恢复: 同 RCG+同文件+同 sink_type+行距≤10 必须合并） ----------------
        # 同位置重复（原判据）+ 相邻行疑似重复实例；家族实例散布（行距大）不误杀（run-7 教训）
        e44 = 0
        try:
            rcg_idx = col_opt(ch, 'root_cause_group_id')
            loc_idx = col_opt(ch, 'location')
            st_idx = col_opt(ch, 'sink_type')
            path_idx = col_opt(ch, 'path')
            sl_idx = col_opt(ch, 'start_line')
            if rcg_idx is not None and loc_idx is not None:
                seen_rcg_loc = set()
                rows = [c for c in cr if rcg_idx < len(c) and loc_idx < len(c) and c[rcg_idx] and c[loc_idx]]
                for c in rows:
                    key = (c[rcg_idx], c[loc_idx])
                    if key in seen_rcg_loc:
                        e44 += 1
                    seen_rcg_loc.add(key)
                # v0.11.1 G-N1: 相邻行同族检查限定 confirmed 候选（disproved/not_applicable 的近邻对合法）
                # 同 RCG+同文件+同 sink_type 且 start_line 差 ≤10 且行号不同
                if st_idx is not None and path_idx is not None and sl_idx is not None:
                    by_key = {}
                    for c in rows:
                        if vcol2 is not None and vcol2 < len(c) and c[vcol2] != 'confirmed':
                            continue
                        if st_idx < len(c) and path_idx < len(c) and sl_idx < len(c) and c[sl_idx].isdigit():
                            k2 = (c[rcg_idx], c[path_idx], c[st_idx])
                            by_key.setdefault(k2, []).append(int(c[sl_idx]))
                    for k2, lines in by_key.items():
                        sl = sorted(set(lines))
                        for i in range(1, len(sl)):
                            if 0 < sl[i] - sl[i-1] <= 10:
                                e44 += 1
                                break
        except Exception:
            e44 = 'ERR'
        self.add('候选同根因合并', e44, e44 == 0)
        # ---------------- E45 blocked 双轨一致（v0.11.0 G-15: 双向互查） ----------------
        e45 = 0
        bp_path45 = os.path.join(S, 'batch_progress.tsv')
        bp_blocked = 0
        if os.path.isfile(bp_path45):
            bp45 = read_tsv(bp_path45)
            bp_blocked = sum(1 for r in bp45[1:] if len(r) > 1 and r[1] == 'blocked')
        led_blocked = sum(1 for r in ledr if len(r) > 5 and r[5] == 'blocked')
        # v0.11.4 run-19 修正：只查「batch 标 blocked 而账本无」方向——sink 级 budget blocked（unconfirmed 映射）
        # 由 E6 failed_wus 对账承担，不再与批级 blocked 混为一谈
        if bp_blocked > 0 and led_blocked == 0:
            e45 = bp_blocked
        self.add('blocked 双轨一致', e45, e45 == 0)
        # ---------------- E46 audit_log ID 合法 ----------------
        e46 = 0
        led_ids = {r[3] for r in ledr if len(r) > 3}
        for r in ar:
            if len(r) > 0 and r[0] and not r[0].startswith('check_point_id'):
                if r[0] not in led_ids:
                    e46 += 1
        self.add('audit_log ID 合法', e46, e46 == 0)
        # ---------------- E47 gate_progress 全覆盖 ----------------
        e47 = 0
        gp_path = os.path.join(S, 'gate_progress.tsv')
        if os.path.isfile(gp_path):
            gp = read_tsv(gp_path)
            gp_subs = {r[0] for r in gp[1:] if r and len(r) > 2 and r[2] and ('pass' in r[2].lower() or 'skip' in r[2].lower())}
            expected = {'0.1', '0.2', '0.3', '0.4', '0.5', '1.1', '1.2', '1.3', '1.4', '1.5b', '2.1', '2.2', '3.1', '3.2'}
            e47 = len(expected - gp_subs)
        else:
            e47 = 14
        self.add('gate_progress 全覆盖', e47, e47 == 0)
        # ---------------- E42 簇引用强制 ----------------
        e42 = 0
        for r in ledr:
            if len(r) > 6 and r[6]:
                reason = r[6]
                if reason.startswith('cluster_conclusion:'):
                    # 必须引用具体簇文件（clusters/xxx.md），否则是批量贴标换皮
                    if not CLUSTER_RE.search(reason):
                        e42 += 1
        self.add('簇引用强制', e42, e42 == 0)
        # ---------------- E41 A2 独立验证硬门（v0.11.0 G-08/B07/C2: 验文件派发痕迹，不验 run-state 字符串） ----------------
        e41 = 0
        g2n_path = os.path.join(S, 'gate2_notes.md')
        if not os.path.isfile(g2n_path):
            e41 = 1
        else:
            try:
                g2n_txt = open(g2n_path, encoding='utf-8', errors='replace').read()
                if 'not executed' in g2n_txt.lower():
                    e41 = 1
                for gate_name in ('V0', 'V1', 'V2', 'V3'):
                    if gate_name not in g2n_txt:
                        e41 += 1
                # run-state.gate2_notes 必须引用该文件（G-08: 字符串与文件绑定）
                g2n_ref = re.search(r'gate2_notes\s*:\s*(\S[^\n]*)', rs)
                if not g2n_ref or 'gate2_notes.md' not in g2n_ref.group(1):
                    e41 += 1
                # 内容级时序（mtime 对复制/归档脆弱）：A2 必须引用其验证的终稿
                if 'verification-summary' not in g2n_txt:
                    e41 += 1
            except Exception:
                e41 = 'ERR'
        self.add('A2 独立验证硬门', e41, e41 == 0)
        # ---------------- E40 禁批量采样闭合（v0.11.1 B-N4/N5: 负向闭合——backward/forward 全终态 reason 必须带引用；不再枚举偷懒措辞） ----------------
        e40 = 0
        try:
            for r in ledr:
                if len(r) > 6 and r[6]:
                    if r[1] not in ('backward', 'forward'):
                        continue
                    if r[5] not in ('candidate', 'disproved', 'not_applicable'):
                        continue  # blocked 的 budget:/user_decision:/permission: 是合法阻塞理由
                    reason = r[6]
                    if reason.startswith('prefilter_no_exec:'):
                        continue  # 机械预筛排除：证据=0 命中 grep 输出（logs），非 file:line
                    mm = REF_RE.search(reason)
                    if not mm and not CLUSTER_RE.search(reason):
                        e40 += 1  # 无引用=换皮变体
                    elif mm:
                        fl = self.file_lines(mm.group(1))
                        if fl is None or int(mm.group(2)) > fl:
                            e40 += 1  # 引用行不存在
        except Exception:
            e40 = 'ERR'
        self.add('禁批量采样闭合', e40, e40 == 0)
        # ---------------- E37 gate_progress 痕迹 ----------------
        e37 = 0 if os.path.isfile(os.path.join(S, 'gate_progress.tsv')) else 1
        self.add('gate_progress 痕迹', e37, e37 == 0)
        # ---------------- E33 fix_presence 禁止派生 ----------------
        # v0.11.0 (M18/G-01): fix_presence 是 direction 列(r[1])，原查 r[2]=mechanism 恒 0 空转
        e33 = sum(1 for r in ledr if len(r) > 1 and r[1] == 'fix_presence')
        self.add('fix_presence 禁止派生', e33, e33 == 0)
        # ---------------- E26 A5 痕迹（v0.11.0 G-16 收紧: skip_reason 必须注册枚举，与 E41 对称） ----------------
        e26 = 0
        a5_ref = re.search(r'a5_round\s*:\s*(\S+)', rs) or re.search(r'a5_skip_reason\s*:\s*(\S+)', rs)
        if not (hyps or a5_ref):
            e26 = 1
        else:
            skip_m = re.search(r'a5_skip_reason\s*:\s*"?([A-Za-z0-9_-]+)"?', rs)
            if skip_m:
                # 注册枚举（enum-registry a5_skip_reason）: 其余值拒绝（与 E41 拒 not executed 对称）
                if skip_m.group(1) not in ('a5_executed_in_prior_run', 'budget_depleted', 'no_sinks_matched', 'user_decision_blocked'):
                    e26 = 1
            round_m = re.search(r'a5_round\s*:\s*(\d+)', rs)
            if round_m and int(round_m.group(1)) > 0 and not hyps:
                e26 = 1  # 声称跑了 A5 但账本无 hypothesis 行
        self.add('A5 痕迹强制', e26, e26 == 0)
        # ---------------- E27 缺失检查类（v0.11.0 G-04: 独立变量 e27b，不再与假设锚点碰撞） ----------------
        e27b = 0
        mc = sum(1 for r in sir if len(r) > 2 and r[2] == 'SINK-MISSING-CHECK')
        skip_mc = re.search(r'missing_check_skip_reason\s*:\s*(\S+)', rs)
        if mc == 0 and not skip_mc:
            e27b = 1
        self.add('缺失检查类强制', e27b, e27b == 0)
        # ---------------- E25 run_status 一致性（v0.11.0 E-25: 移到全部方程后，gate_fail 必须含全部结果） ----------------
        rs_status = re.search(r'^run_status:\s*(\w+)', rs, re.M)
        # ---------------- v0.11.6 时序化新方程（子任务时刻可满足的产物检查） ----------------
        # 初始化产物：capability-profile.md + run-state.md 均存在
        e_init = 0
        for fn in ('capability-profile.md', 'run-state.md'):
            if not os.path.isfile(os.path.join(S, fn)):
                e_init += 1
        self.add('初始化产物', e_init, e_init == 0)
        # 威胁语境产物：threat-context.md + attack-surface-map.md 存在且威胁语境含保守继续策略
        e_threat = 0
        for fn in ('threat-context.md', 'attack-surface-map.md'):
            if not os.path.isfile(os.path.join(S, fn)):
                e_threat += 1
        tc_txt = open(os.path.join(S, 'threat-context.md'), encoding='utf-8', errors='replace').read() if os.path.isfile(os.path.join(S, 'threat-context.md')) else ''
        if 'conservative_continue' not in tc_txt:
            e_threat += 1
        self.add('威胁语境产物', e_threat, e_threat == 0)
        # 黄金自检通过：进程内对黄金夹具跑 selftest（--expect 同口径）；自身是夹具时视为通过（避免递归）
        e_golden = 0
        try:
            fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gate-selftest')
            fx_s = os.path.join(fx, 'fixture')
            fx_src = os.path.join(fx, 'fixture-src')
            fx_exp = os.path.join(fx, 'expected-gate.txt')
            if os.path.realpath(S) == os.path.realpath(fx_s):
                e_golden = 0  # 自检对象即黄金夹具本身
            elif os.path.isfile(os.path.join(fx_s, 'check_point_ledger.tsv')) and os.path.isfile(fx_exp):
                sub = Gate(fx_s, fx_src, expect=fx_exp)
                sub.knowledge = self.knowledge
                subok = sub.run()
                # 镜像 main() 的 E78 追加行（golden 期望含 gate 执行痕迹行）
                grl_fx = read_tsv(os.path.join(fx_s, 'gate_run_log.tsv'))
                last_by_mode_fx = {}
                for rr in grl_fx[1:]:
                    if len(rr) > 1 and rr[0]:
                        last_by_mode_fx[rr[0]] = rr[1]
                gp_fx = read_tsv(os.path.join(fx_s, 'gate_progress.tsv'))
                e78_fx = 0
                for rr in gp_fx[1:]:
                    if len(rr) > 2 and rr[2] and 'pass' in rr[2].lower():
                        mode = str(rr[0]).split('-')[0]
                        if mode not in last_by_mode_fx or last_by_mode_fx[mode] != 'pass':
                            e78_fx += 1
                sub.rows.append(('gate 执行痕迹', str(e78_fx), '成立' if e78_fx == 0 else 'FAIL'))
                exp = open(fx_exp, encoding='utf-8').read().splitlines()
                got = ['| %d | %s | %s | %s |' % (i, nm, out, v) for i, (nm, out, v) in enumerate(sub.rows, 1)]
                exprows = [ln for ln in exp if re.match(r'^\| \d+ \|', ln)]
                if not subok or got != exprows:
                    e_golden = 1
            else:
                e_golden = 1
        except Exception:
            e_golden = 'ERR'
        self.add('黄金自检通过', e_golden, e_golden == 0)
        gate_fail = any(v == 'FAIL' for _, _, v in self.rows)
        e25 = 0
        if rs_status and rs_status.group(1) == 'completed' and gate_fail:
            e25 = 1
        self.add('run_status 一致性', e25, e25 == 0)
        # ---------------- verdict ----------------
        allok = all(v == '成立' for _, _, v in self.rows)
        return allok

    def gap_report(self):
        S = self.S
        out = ['', '## rework 缺口精确清单（前 100 条 + 总数）', '']
        try:
            led = read_tsv(os.path.join(S, 'check_point_ledger.tsv'))
            ledr = led[1:] if len(led) > 1 else []
            sinks = read_tsv(os.path.join(S, 'sink_inventory.tsv'))
            sir = sinks[1:] if len(sinks) > 1 else []
            srcs = read_tsv(os.path.join(S, 'source_inventory.tsv'))
            sor = srcs[1:] if len(srcs) > 1 else []
            un = [r[3] for r in ledr if len(r) > 5 and r[5] == '未检查']
            out.append('未检查 check_point_id（前100）:')
            out.extend(un[:100])
            out.append('未检查总数: %d' % len(un))
            back = {r[0] for r in ledr if len(r) > 1 and r[1] == 'backward'}
            fwd = {r[0] for r in ledr if len(r) > 1 and r[1] == 'forward'}
            miss_sink = [r[0] for r in sir if r[0] not in back]
            miss_src = [r[0] for r in sor if r[0] not in fwd]
            out.append('')
            out.append('未覆盖 sink_id（前100）:')
            out.extend(miss_sink[:100])
            out.append('未覆盖 source_id（前100）:')
            out.extend(miss_src[:100])
            bad = []
            for r in ledr:
                if len(r) <= 6:
                    continue
                d, st, reason = r[1], r[5], r[6]
                if d in ('backward', 'forward') and st == 'disproved' and not reason.startswith(('cluster_conclusion:', 'disproved_safe:', 'false_rule_hit:')):
                    bad.append(r[3] + ' ' + reason[:60])
                elif st == 'blocked' and not reason.startswith(('budget:', 'user_decision:', 'permission:')):
                    bad.append(r[3] + ' ' + reason[:60])
                elif st == 'not_applicable' and d == 'terminal' and not reason.startswith(('prefilter_no_exec:', 'false_rule_hit:', 'disproved_safe:')):
                    bad.append(r[3] + ' ' + reason[:60])
            out.append('')
            out.append('非法理由行（前100）:')
            out.extend(bad[:100])
            out.append('非法理由总数: %d' % len(bad))
            # E35 文件名诊断
            badnames = []
            fd4 = os.path.join(S, 'findings')
            if os.path.isdir(fd4):
                for fn in os.listdir(fd4):
                    if fn.startswith('C-') and fn.endswith('.md'):
                        if not re.match(r'C-\d{5}-\d{5}-[0-9a-f]{8}-[a-z]+-SINK-[A-Z0-9-]+-[A-Za-z0-9_.]+-\d+\.md$', fn):
                            badnames.append(fn)
            if badnames:
                out.append('')
                out.append('文件名格式不符（应为 {candidate_id}-{severity}-{sink_type}-{file}-{line}.md）:')
                out.extend(badnames[:100])
                out.append('文件名格式不符总数: %d' % len(badnames))
        except Exception as ex:
            out.append('缺口导出异常: ' + str(ex)[:100])
        return out

SUBTASK_MAP = {
    # v0.11.6 run-19-opencode 冒烟修复：映射按「子任务完成时刻可满足」重排——
    # 终态方程（planned==terminal/WU 闭合/产物存在性）只在终态全量 gate 检查，不挂在早期子任务上
    # （旧映射导致 opencode agent 在 0.1/0.2/0.4/0.5/1.1 中途 gate 必 FAIL 而无所适从）
    '0.1': ['初始化产物'],
    '0.2': ['黄金自检通过'],
    '0.3': ['信号级禁入', '枚举锚定(类集合)', '枚举来源强制(禁自造类)'],
    '0.4': ['sink 回溯覆盖', 'source 前向覆盖', '账本枚举封闭', '反伪闭合(全方向)'],
    '0.5': ['威胁语境产物'],
    '1.1': ['批数合理性'],
    '1.2': ['反伪闭合(全方向)', '全终态理由封闭', '引用可解析', '证据唯一性', '推导链强制', '时序检查', '禁批量采样闭合', '簇引用强制', '图节点投影完整性', '图边投影完整性', '图投影确定性', '图边端点存在', 'flow 边值域', '剪枝边一致性', '账本枚举封闭', '证据密度下限', '簇覆盖上限', 'reviewer 派发痕迹', '终态 sink 边闭合', '合并守恒', 'audit_log 追加单调性', 'WU 分片质量', '分片回填对账', '看板行数', 'V 文件候选映射', 'WU 派发记录', 'audit_log ID 合法', 'gate_progress 全覆盖', 'blocked 双轨一致', '批进度记录检查', '信息板格式', '信息板结论隔离', '级联覆盖'],
    # v0.11.6 opencode 冒烟修复：1.3/1.4 挂批循环完成方程——无分片即 FAIL，机械封堵「跳过批循环伪造终态」
    # （冒烟实证：agent 0 分片直接造 candidates.tsv/clusters，若 gate 不拦则伪闭合成立）
    '1.3': ['对抗表存在', 'WU 闭合', '分片回填对账', '终态 sink 边闭合'],
    '1.4': ['候选 ID 反查', '三事实源一致性', '候选ID确定性强制', '候选类型一致性', 'WU 闭合', '推导链强制'],
    '1.5b': ['假设锚点强制', '假设上限'],
    '2.1': ['四相等+阈值', 'audit 双向覆盖', '档位诚实', '候选推理非工具原文'],
    '2.2': ['V文件完整性', 'finding 文件名格式'],
    '3.1': ['四相等+阈值', '三事实源一致性'],
    '3.2': ['run_status 一致性', 'A2 独立验证硬门', 'gate_progress 痕迹', 'batch_progress 完成率', '剪枝 A2 复核', '候选边支撑', 'flow 边节点存在', '簇引用真实性', 'run_fingerprint 检查', '剪枝判据落盘', '枚举对账', '批数合理性', '候选同根因合并', '信息板格式', '信息板结论隔离', '级联覆盖'],
}
STAGE_MAP = {
    'g0': ['初始化产物', '黄金自检通过', 'schema 全等', '信号级禁入', '枚举锚定(类集合)', '枚举来源强制(禁自造类)', '威胁语境产物', '批数合理性'],
    'g1': ['planned==terminal', 'sink 回溯覆盖', 'source 前向覆盖', '反伪闭合(全方向)', '簇产物存在', '全终态理由封闭', '引用可解析', '证据唯一性', '推导链强制', '时序检查', 'WU 闭合', '假设锚点强制', '假设上限', '缺失检查类强制', 'fix_presence 禁止派生', '候选推理非工具原文', '候选ID确定性强制', '禁批量采样闭合', '图节点投影完整性', '图边投影完整性', '图投影确定性', '图边端点存在', '簇引用强制', 'flow 边值域', '剪枝边一致性', '账本枚举封闭', '证据密度下限', '簇覆盖上限', 'reviewer 派发痕迹', '终态 sink 边闭合', '合并守恒', 'audit_log 追加单调性', 'WU 分片质量', '分片回填对账', '发现索引对账', '看板行数', 'V 文件候选映射', 'WU 派发记录', 'audit_log ID 合法', 'gate_progress 全覆盖', 'blocked 双轨一致', '批进度记录检查', '信息板格式', '信息板结论隔离', '级联覆盖'],
    'g2': ['候选 ID 反查', '三事实源一致性', 'schema 全等', 'audit 双向覆盖', '档位诚实', 'A5 痕迹强制', 'V文件完整性', '候选ID确定性强制'],
    'g3': ['四相等+阈值', 'failed 清单去真空', '账本零残留', '对抗表存在', 'run_status 一致性', 'finding 文件名格式', 'gate_progress 痕迹', 'batch_progress 完成率', '短路质量检查', '图节点投影完整性', '图边投影完整性', '图投影确定性', '图边端点存在', 'A2 独立验证硬门', '剪枝 A2 复核', '候选边支撑', 'flow 边节点存在', '簇引用真实性', 'run_fingerprint 检查', '剪枝判据落盘', '枚举对账', '批数合理性', '候选同根因合并', '信息板格式', '信息板结论隔离', '级联覆盖'],
}
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--source', required=True)
    ap.add_argument('--expect')
    ap.add_argument('--stage', choices=['g0', 'g1', 'g2', 'g3'])
    ap.add_argument('--subtask', choices=['0.1', '0.2', '0.3', '0.4', '0.5', '1.1', '1.2', '1.3', '1.4', '1.5b', '2.1', '2.2', '3.1', '3.2'])
    ap.add_argument('--knowledge')
    args = ap.parse_args()
    know = args.knowledge or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'knowledge')
    g = Gate(args.session, args.source, args.expect)
    g.knowledge = know
    try:
        allok = g.run()
    except Exception as ex:
        # v0.11.1 E-15: 保留已跑方程结果 + 追加异常行（不覆写全表为单行）
        g.rows.append(('gate 执行异常', str(ex)[:120], 'FAIL'))
        allok = False
    rows = g.rows
    if args.subtask:
        keep = SUBTASK_MAP[args.subtask]
        rows = [r for r in g.rows if r[0] in keep]
        allok = all(v == '成立' for _, _, v in rows)
    elif args.stage:
        keep = STAGE_MAP[args.stage]
        rows = [r for r in g.rows if r[0] in keep]
        allok = all(v == '成立' for _, _, v in rows)
    # ---------------- v0.11.3 E78 gate 执行痕迹（仅全量 gate 检查：gate_progress 的 pass 必须对应 gate_run_log 真实 pass——防伪造） ----------------
    if not args.subtask and not args.stage:
        e78 = 0
        try:
            grl_path78 = os.path.join(args.session, 'gate_run_log.tsv')
            if not os.path.isfile(grl_path78):
                e78 = 1  # 从未跑过 gate
            else:
                grl78 = read_tsv(grl_path78)
                last_by_mode = {}
                for r in grl78[1:]:
                    if len(r) > 1 and r[0]:
                        last_by_mode[r[0]] = r[1] if len(r) > 1 else ''
                gp78 = read_tsv(os.path.join(args.session, 'gate_progress.tsv'))
                for r in gp78[1:]:
                    if len(r) > 2 and r[2] and 'pass' in r[2].lower():
                        mode = str(r[0]).split('-')[0]
                        if mode not in last_by_mode or last_by_mode[mode] != 'pass':
                            e78 += 1
        except Exception:
            e78 = 'ERR'
        g.rows.append(('gate 执行痕迹', str(e78), '成立' if e78 == 0 else 'FAIL'))
        allok = allok and (e78 == 0)
    lines = ['# Gate Record — Gate-1 对账（v0.4.5' + ((' ' + args.stage) if args.stage else '') + '）', '', '| # | 等式 | 输出 | 判定 |', '|---|---|---|---|']
    # v0.7.8 codex 启示：证据封印——audit_log 引用的证据文件算 sha256 写入 gate_record，宿主重放比对 hash 防事后篡改
    import hashlib as _hl
    seal_lines = []
    seal_errors = []
    try:
        alog2 = read_tsv(os.path.join(args.session, 'audit_log.tsv'))
        ev_files = set()
        for rr in (alog2[1:] if len(alog2) > 1 else []):
            if len(rr) > 5 and rr[5]:
                m = REF_RE.search(rr[5])
                if m:
                    ev_files.add(m.group(1))
        sealed = sorted(ev_files)
        for fp in sealed[:200]:
            p = os.path.join(args.source, fp)
            if os.path.isfile(p):
                try:
                    h = _hl.sha256(open(p, 'rb').read()).hexdigest()[:16]
                    seal_lines.append('%s %s' % (fp, h))
                except Exception as ex:
                    seal_errors.append('%s %s' % (fp, str(ex)[:60]))  # v0.11.1 E-26: 封印失败显式披露
    except Exception as ex:
        seal_errors.append('audit_log 解析失败: ' + str(ex)[:80])
    if seal_errors:
        lines.append('')
        lines.append('## 证据封印异常（v0.11.1 披露）')
        lines.append('```')
        lines += seal_errors[:20]
        lines.append('```')
    if seal_lines:
        lines.append('')
        lines.append('## 证据封印（v0.7.8 codex 启示：宿主重放比对 hash 防篡改）')
        lines.append('```')
        lines += seal_lines
        lines.append('```')
    for i, (name, out, v) in enumerate(rows, 1):
        lines.append('| %d | %s | %s | %s |' % (i, name, out, v))
    lines.append('')
    lines.append('gate_result: ' + ('pass' if allok else 'rework'))
    lines.append('')
    # ---------------- v0.11.3 E78: gate 执行痕迹——每次 gate 运行追加 gate_run_log.tsv ----------------
    # 目的：gate_progress 的 pass 行必须与 gate 真实判定对账（run-18-aiohttp 伪造「3.2 pass」实为 FAIL）
    # gate_run_log 是 gate 的输出产物（判定留痕），不是 session 分析产物——不违反 gate 只读原则
    try:
        import csv as _csv
        grl_path = os.path.join(args.session, 'gate_run_log.tsv')
        mode_id = args.subtask or args.stage or 'full'
        fail_names = ';'.join(name for name, _, v in rows if v == 'FAIL')
        ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        new_row = [mode_id, ('pass' if allok else 'rework'), ts, fail_names]
        exists = os.path.isfile(grl_path)
        with open(grl_path, 'a', encoding='utf-8', newline='\n') as f:
            w = _csv.writer(f, delimiter='\t')
            if not exists:
                w.writerow(['mode', 'gate_result', 'timestamp', 'fail_equations'])
            w.writerow(new_row)
    except Exception:
        pass
    if not allok:
        gap = g.gap_report()
        lines += gap
        txt = '\n'.join(lines) + '\n'
    else:
        txt = '\n'.join(lines) + '\n'
    with open(os.path.join(args.session, 'gate_record.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    print(txt)
    if args.expect:
        exp = open(args.expect, encoding='utf-8').read().splitlines()
        got = [ln for ln in lines if re.match(r'^\| \d+ \|', ln)]
        exprows = [ln for ln in exp if re.match(r'^\| \d+ \|', ln)]
        expgr = 'gate_result: pass' in exp
        match = (got == exprows) and (expgr == allok)
        print('SELFTEST: ' + ('PASS' if match else 'FAIL'))
        sys.exit(0 if match else 1)
    sys.exit(0 if allok else 1)

if __name__ == '__main__':
    main()
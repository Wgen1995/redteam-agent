# -*- coding: utf-8 -*-
"""黄金回归总驱动（批次 1 T13）——41 命令全覆盖。

缺金样门槛（批次 3 评审·审计#7）：默认缺金样=FAIL 不落盘（防 CI 首跑/漏提交
误建档判绿）；--bless 显式建档（INIT）。在场金样漂移即 FAIL，语义不变。"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
GOLD = os.path.join(HERE, "golden")
TS = "2026-09-23T07:00:00Z"
A64 = "a" * 64

READ_CMDS = [
    ["validate"], ["verify-chain"], ["next-id", "intents", "INT", "g1"],
    ["unconsumed-facts"], ["pending-intents"], ["matrix-gaps"],
    ["converge-check"], ["intent-status", "INT-g1-0001"], ["matrix-get", "web.admin-panel"],
    ["scope-check", "shop.example"], ["budget-check"], ["cleanup-checklist"],
    ["hash-recheck"], ["matrix-audit"], ["state-rebuild"], ["set-replay-state", "status"],
    ["ledger-scope-coverage"], ["ledger-tree-check"], ["ledger-replay-summary"],
    ["ledger-terminal-gate"], ["redact-scan"],
]

WRITE_CMDS = ["add-goal", "add-scope", "add-intent", "set-intent-status", "add-fact",
              "add-finding", "supersede-finding", "add-asset", "add-cred", "set-cred-status",
              "add-edge", "add-evidence", "amend-scope", "matrix-set", "matrix-freeze",
              "append-timeline", "approve", "budget-log", "checkpoint", "matrix-init"]

VALS = {
    "--target": "shop2.example", "--objective": "回归目标", "--auth-doc": "auth/g.pdf",
    "--auth-sha256": A64, "--signer": "client-cso", "--valid-from": "2026-09-01",
    "--valid-until": "2026-09-30", "--budget": "1M;1000;10", "--model-tier": "strong",
    "--guard-tier": "T3", "--timestamp": TS, "--matcher": "api.shop.example",
    "--note": "golden", "--account": "admin", "--title": "回归意图",
    "--detail": "回归明细", "--engine": "web-blackbox",
    "--score": "0.5", "--via": "CNPEN-SD-01", "--dedup-key": "golden-key",
    "--budget-share": "0.1", "--id": "INT-g1-0002", "--status": "active",
    "--intent-id": "INT-g1-0001", "--confidence": "C3", "--impact": "中",
    "--description-brief": "回归描述", "--type": "subdomain", "--value": "api.shop.example",
    "--role": "operator", "--username-ref": "op1", "--secret-ref": "{{vault:cred-2}}",
    "--scope-asset": "AST-g1-0002", "--permitted-actions": "read",
    "--source-id": "F-g1-0001", "--target-id": "INT-g1-0001",
    "--network-position": "internet", "--repro-command": "curl -s https://api.shop.example/x",
    "--repro-kind": "single", "--content-hash-raw": "c" * 64, "--content-hash-norm": "d" * 64,
    "--amendment-of": "S-g1-0001", "--attack-surface": "web.api", "--vuln-class": "inj.sql",
    "--state": "?", "--reason": "golden", "--actor": "CLI", "--phase": "P3",
    "--event": "golden-event", "--revert-cmd": "", "--command-hash": "b" * 64,
    "--decision": "approved", "--approver": "user", "--token-delta": "100",
    "--requests-delta": "1", "--hours-delta": "0.1", "--dollars-delta": "0",
    "--scope": "goal", "--finding-id": "FD-g1-0001", "--evidence-id": "EV-g1-0001",
    "--observed-at": TS, "--session": "golden-s",  # 批次 3 T4：checkpoint --session 必填
}
KIND_BY_CMD = {"add-scope": "include", "add-cred": "static-cred", "add-intent": "recon",
               "add-fact": "info", "add-edge": "spawns"}


def run_cli(gd, name, args):
    return subprocess.run([sys.executable, CLI, name, "--goal-dir", gd] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


# 批次 3 T2：tanyin-phases 确定性面（无 goal-dir，读仓库 phases/phases.yaml）——金样走同一机制
PHASES_CLI = os.path.join(HERE, "..", "cli", "tanyin-phases")
PHASES_CMDS = [["validate"]]

# 批次 4 T12：denominator-ready 四断言 PASS 面（phases 面，validate 先例）——
# prep_denominator 补 fact 使 ①-④ 全过（计划 Step4 有意刷新预案的落地形态：
# norm=PASS 行含 planted=0 found=0；原 G-g1 FAIL 形状由
# tests/test_phases_gate.test_fixture_fail_list_shape 断言承载，不再锁 norm）。
DENOM_TS = "2026-09-24T13:00:00Z"
PHASES_DENOM = [("phases-denominator-ready",
                 [sys.executable, PHASES_CLI, "denominator-ready", "--goal-dir", "<GD>"])]


def prep_denominator(gd):
    # ①补第二来源：新 intent（origin=recon-event 直达 pending）+两 in_scope 资产各一条 fact
    r = run_cli(gd, "add-intent", ["--title=补源B", "--engine=web-blackbox", "--kind=recon",
                                   "--origin=recon-event", "--budget-share=1;1;1",
                                   "--timestamp=" + DENOM_TS])
    assert r.returncode == 0, r.stdout + r.stderr
    for tgt in ("shop.example", "admin-internal.shop.example"):
        r = run_cli(gd, "add-fact", ["--intent-id=INT-g1-0003", "--kind=info",
                                     "--target=" + tgt, "--detail=补第二来源",
                                     "--confidence=0.9", "--timestamp=" + DENOM_TS])
        assert r.returncode == 0, r.stdout + r.stderr
    # ②A2-A8 不适用理由（A1 非空=root-domain+subdomain 在档）
    for k in range(2, 9):
        r = run_cli(gd, "add-fact", ["--intent-id=INT-g1-0001", "--kind=info",
                                     "--target=asset-class:A%d" % k,
                                     "--detail=不适用：批注理由", "--confidence=0.9",
                                     "--timestamp=" + DENOM_TS])
        assert r.returncode == 0, r.stdout + r.stderr
    # ④planted=0 披露 fact（target=canary:recon）
    r = run_cli(gd, "add-fact", ["--intent-id=INT-g1-0001", "--kind=info",
                                 "--target=canary:recon",
                                 "--detail=客户暂不配合植入（披露）",
                                 "--confidence=0.9", "--timestamp=" + DENOM_TS])
    assert r.returncode == 0, r.stdout + r.stderr

# 批次 4 T5：tanyin-replay 确定性面（engine 面——三态判定产物可金样化）。
# 夹具无 evidence/ 目录（计划注释与实况不符）：prep_engine 预铸 EV-g1-0001 卡片
# （autodrive 预处理先例）；Host=10.10.9.9 命中夹具 scope include 10.10.0.0/16（免 DNS）。
REPLAY_CLI = os.path.join(HERE, "..", "cli", "tanyin-replay")
REPLAY_CARD = ("---\nid: EV-g1-0001\nnetwork_position: internet\n"
               "raw_request: |\n  GET /x HTTP/1.1\n  Host: 10.10.9.9\n"
               "expected: {}\npair_group: \n---\n## 摘\n")
ENGINE_CMDS = [("replay-envdiff", [sys.executable, REPLAY_CLI, "replay", "--goal-dir", "<GD>",
                                   "--id=EV-g1-0001", "--scheme=http", "--port=1",
                                   "--timeout=2", "--timestamp=2026-09-24T09:00:00Z"])]

# 批次 4 T7 前置（图谱驱动增补 71d3b7c）：图查询三命令确定性面（graph 面，replay-envdiff 先例）。
# prep_graph 预织图：parent/attack 边经 CLI 落账；可达表面上空格行直写 matrix.tsv
# （prep_engine 直写文件先例——空态行无法经 matrix-set 铸造，state 空=REJECT）。
GRAPH_CMDS = [
    ["graph-neighbors", "--asset=AST-g1-0002", "--depth=2"],
    ["graph-paths", "--from=CRED-g1-0001", "--to=AST-g1-0002"],
    ["graph-horizon", "--from=AST-g1-0001"],
]


def prep_graph(gd):
    ts = "2026-09-24T11:00:00Z"
    for kind, src, dst in (("parent", "AST-g1-0001", "AST-g1-0002"),
                           ("attack", "FD-g1-0001", "AST-g1-0002")):
        r = run_cli(gd, "add-edge", ["--kind=" + kind, "--source-id=" + src,
                                     "--target-id=" + dst, "--provenance=golden-graph",
                                     "--timestamp=" + ts])
        assert r.returncode == 0, r.stdout + r.stderr
    with open(os.path.join(gd, "matrix.tsv"), "a", encoding="utf-8", newline="\n") as f:
        f.write("admin-internal.shop.example\tinj.sql\t\t\t\t2\t\t\n")


# 批次 4 T11：session-viz 投影确定性面（viz 面，replay-envdiff 先例）——
# --data-only=数据岛 JSON（sort_keys 确定性）；夹具=diff-authz（身份矩阵视图非空）。
# projector 零回写：只读夹具副本，无 prep、无写账本动作。
VIZ_CLI = os.path.join(HERE, "..", "cli", "tanyin-viz")
VIZ_FIX = os.path.join(HERE, "fixtures", "diff-authz")
VIZ_CMDS = [("viz-data", [sys.executable, VIZ_CLI, "render", "--goal-dir", "<GD>",
                           "--data-only"])]

# 批次 4 评审收尾（C-1）：diff-authz 真实 add-evidence 铸造工件上 hash-recheck
# PASS 面（viz 面 fresh_of 同构——夹具副本只读校验零 prep；输出无墙钟=确定性；
# norm 单源=ledger/norm.py 写/查同款的回归锚）。
RECHECK_CMDS = [("diff-hash-recheck", [sys.executable, CLI, "hash-recheck",
                                       "--goal-dir", "<GD>"])]


# 批次 4 T9：vuln-agent 适配器确定性面（engine 面，replay-envdiff 先例）。
# norm=submission.json 规范化重 dump——提交内容确定性（POC 时间取自源 md，无墙钟入提交）；
# operations.log 审计附件不入 norm。out-dir=<GD>（夹具副本上直写，存量面零触碰）。
VULN_ADAPTER = os.path.join(HERE, "..", "engines", "vuln-agent", "adapter.py")
VULN_FIXOUT = os.path.join(HERE, "fixtures", "engine", "vuln-agent-out")
ADAPTER_CMDS = [("engine-vuln-adapter", [sys.executable, VULN_ADAPTER,
                                         "--intent-id=INT-g1-0099", "--out-dir", "<GD>",
                                         "--source", VULN_FIXOUT])]


# 批次 4 T10：nuclei adopt 面——验签先于归一化，依赖 openssl（缺=ENV SKIP，
# test_supply_chain skipUnless 同口径；出口验收⑧「openssl 例 skip=ENV」）。
NUCLEI_ADAPTER = os.path.join(HERE, "..", "engines", "nuclei", "adapter.py")
NUCLEI_JSONL = os.path.join(HERE, "fixtures", "engine", "nuclei-jsonl", "sample.jsonl")
NUCLEI_CMDS = [("engine-nuclei-adopt", [sys.executable, NUCLEI_ADAPTER,
                                        "--intent-id=INT-g1-0100", "--out-dir", "<GD>",
                                        "--jsonl-file", NUCLEI_JSONL])]


# 批次 5 T11：tanyin-knowledge 确定性面（kn 面——非 ledger 入口，ADAPTER_CMDS 先例同型）。
# prep_knowledge=临时目录 init+预置 fixtures/knowledge 合法 formal 页（PR-0001/EN-0001）；
# 无墙钟入产物（export created 取 last_verified；match --today 显式）→ 双跑字节一致。
KN_CLI = os.path.join(HERE, "..", "cli", "tanyin-knowledge")
KN_FIX = os.path.join(HERE, "fixtures", "knowledge")
KN_CMDS = [
    ("kn-export", [sys.executable, KN_CLI, "export", "--knowledge-dir", "<GD>"]),
    ("kn-match", [sys.executable, KN_CLI, "match", "--knowledge-dir", "<GD>",
                  "--client=CLIENT-01", "--asset=shop.example", "--today=2026-09-24"]),
]


def prep_knowledge(gd):
    r = subprocess.run([sys.executable, KN_CLI, "init", "--knowledge-dir", gd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    for sub in ("precedents", "entities"):
        os.makedirs(os.path.join(gd, sub), exist_ok=True)
    for rel in ("precedents/PR-0001.md", "entities/EN-0001.md"):
        shutil.copyfile(os.path.join(KN_FIX, rel), os.path.join(gd, rel))


def norm_kn(stdout, gd):
    """kn 面归一：stdout + graph.ndjson 全文（导出行确定性=字节级回归面）。"""
    g = os.path.join(gd, "graph.ndjson")
    graph = open(g, encoding="utf-8").read() if os.path.isfile(g) else ""
    return stdout.strip() + chr(10) + "--" + chr(10) + graph.strip()


def run_engine(cmd, gd):
    return subprocess.run([gd if c == "<GD>" else c for c in cmd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def norm_adapter(gd):
    """适配器面归一：submission.json 排序重 dump（提交自身确定性，无墙钟/临时路径）。"""
    with open(os.path.join(gd, "submission.json"), encoding="utf-8") as f:
        return json.dumps(json.load(f), ensure_ascii=False, sort_keys=True)


def prep_engine(gd):
    d = os.path.join(gd, "evidence")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "EV-g1-0001.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(REPLAY_CARD)


def norm_engine(text, gd):
    """判定行归一：剥连接层 detail（错误消息平台相关/逐次可变）与 gd 临时路径；
    判定产物 seq 文件名不入 norm（只增不覆盖，序号随跑数变）。"""
    j = json.loads(text.strip().splitlines()[-1])
    keep = {k: j.get(k) for k in ("id", "verdict", "matched", "status", "results", "extracted")}
    keep["suggest"] = j.get("suggest", "").replace(gd, "<GD>")
    return json.dumps(keep, ensure_ascii=False, sort_keys=True)


def run_phases(args):
    return subprocess.run([sys.executable, PHASES_CLI] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def fresh(tmp):
    d = os.path.join(tmp, "G-g1")
    if os.path.exists(d):
        shutil.rmtree(d)
    return shutil.copytree(FIX, d)


def fresh_of(tmp, src, name):
    """任意夹具副本（viz 面：diff-authz；fresh 的泛化形态）。"""
    d = os.path.join(tmp, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    return shutil.copytree(src, d)


OVERRIDE = {
    "add-intent": {"--origin": "entity", "--budget-share": "100;10;1"},
    "add-fact": {"--confidence": "0.9"},
    "add-finding": {"--exploitation-status": "suspected", "--scope-check": "in_scope",
                    "--affected-asset-id": "AST-g1-0002", "--evidence-ids": "EV-g1-0001"},
    "supersede-finding": {"--id": "FD-g1-0002", "--superseded-by": "FD-g1-0001"},
    "add-edge": {"--kind": "proves", "--source-id": "INT-g1-0001", "--target-id": "FD-g1-0001",
                 "--provenance": "P3"},
    "add-evidence": {"--source-type": "command"},
    "amend-scope": {"--kind": "include", "--approval": "AP-g1-0001"},
    "matrix-freeze": {},
}
PRE_OPS = {"supersede-finding": [["@craft-supersede"]]}
FIXTURE_PREP = {"add-goal": ["goals.tsv"]}


def autodrive(name, gd):
    for op in PRE_OPS.get(name, []):
        if op[0] == "@craft-supersede":
            sys.path.insert(0, os.path.join(HERE, "..", "cli"))
            from ledger.core import esc, unesc
            from ledger.schemas import TABLES
            p = os.path.join(gd, "findings.tsv")
            rows = [[unesc(c) for c in l.split(chr(9))] for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
            si = TABLES["findings.tsv"].index("status")
            ki = TABLES["findings.tsv"].index("dedup_key")
            rows[0][si] = "active"
            r2 = list(rows[0])
            r2[0] = "FD-g1-0002"
            r2[ki] = rows[0][ki]
            rows.append(r2)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(chr(10).join(chr(9).join(esc(c) for c in r) for r in rows) + chr(10))
        else:
            run_cli(gd, op[0], op[1:])
    if name == "matrix-freeze":  # 预解冻：清全部 frozen_at，冻结盖戳才可正例
        p = os.path.join(gd, "matrix.tsv")
        lines = [l.split(chr(9)) for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
        for r in lines:
            if len(r) >= 8:
                r[7] = ""
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(chr(10).join(chr(9).join(r) for r in lines) + chr(10))
    for kill in FIXTURE_PREP.get(name, []):
        p = os.path.join(gd, kill)
        if os.path.exists(p):
            os.remove(p)
    ov = OVERRIDE.get(name, {})
    args = ["--timestamp=" + TS] + [k + "=" + v for k, v in ov.items()]
    if name == "matrix-init":
        open(os.path.join(gd, "matrix.tsv"), "w", encoding="utf-8").close()
    r = None
    for _ in range(12):
        r = run_cli(gd, name, args)
        m = re.search("必填参数缺失或为空: (--[a-z0-9-]+)", r.stdout + r.stderr)
        if not m:
            return args, r
        p = m.group(1)
        v = OVERRIDE.get(name, {}).get(p, VALS.get(p))
        if p == "--kind":
            v = KIND_BY_CMD.get(name, "info")
        if v is None:
            v = "x"
        args.append(p + "=" + v)
    return args, r


def norm_read(text):
    ts = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
    return ts.sub("TS", text).strip()


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="黄金回归：双跑确定性+金样比对；缺金样默认 FAIL，--bless 显式建档")
    ap.add_argument("--bless", action="store_true",
                    help="缺金样时落盘建档（INIT）；默认缺金样=FAIL 不落盘")
    return ap.parse_args(argv)


def gate_golden(gp, text, label, bless, fails, inits, drift):
    """金样门槛（批次 3 评审·审计#7）：缺金样无 --bless=FAIL 不落盘；--bless=INIT
    落盘；在档漂移=FAIL（bless 不豁免）。空白容忍比对=原三处就地语义。"""
    if not os.path.exists(gp):
        if bless:
            with open(gp, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            inits.append(label)
        else:
            fails.append(label + "(缺金样，须 --bless 显式建档)")
        return
    if open(gp, encoding="utf-8").read().strip() != text.strip():
        fails.append(label + "(" + drift + ")")


def norm_state(gd):
    ts = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
    parts = []
    for t in sorted(os.listdir(gd)):
        if not os.path.isfile(os.path.join(gd, t)):
            continue
        body = open(os.path.join(gd, t), encoding="utf-8").read()
        parts.append("== " + t + " ==")
        parts.extend(sorted(ts.sub("TS", l) for l in body.splitlines() if l.strip()))
    return chr(10).join(parts)


def main(argv=None):
    bless = parse_args(argv).bless
    fails, inits = [], []
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        for spec in READ_CMDS:
            name = spec[0]
            a1 = run_cli(FIX, name, spec[1:])
            gd2 = fresh(t2)
            a2 = run_cli(gd2, name, spec[1:])
            o1, o2 = norm_read(a1.stdout), norm_read(a2.stdout)
            if o1 != o2:
                fails.append(name + "(不确定性)")
                continue
            gp = os.path.join(GOLD, "read-" + name + ".norm")
            gate_golden(gp, o1, name, bless, fails, inits, "输出漂移")
        for name in WRITE_CMDS:
            outs = []
            for t in (t1, t2):
                gd = fresh(t)
                args, r = autodrive(name, gd)
                outs.append((args, r.returncode, norm_state(gd), norm_read(r.stdout)))
            (args, rc, s1, o1) = outs[0]
            (_, _, s2, o2) = outs[1]
            if rc != 0:
                fails.append(name + "(驱动未收敛 rc=%d)" % rc)
                continue
            if s1 != s2:
                fails.append(name + "(状态不确定性)")
                continue
            gp = os.path.join(GOLD, "write-" + name + ".state")
            gate_golden(gp, o1 + chr(10) + s1, name, bless, fails, inits, "状态漂移")
        for spec in PHASES_CMDS:
            a1 = run_phases(spec)
            a2 = run_phases(spec)
            o1, o2 = norm_read(a1.stdout), norm_read(a2.stdout)
            if a1.returncode != 0 or o1 != o2:
                fails.append("phases-" + spec[0] + "(不确定性或非零退出)")
                continue
            gp = os.path.join(GOLD, "phases-" + spec[0] + ".norm")
            gate_golden(gp, o1, "phases-" + spec[0], bless, fails, inits, "输出漂移")
        for label, spec in PHASES_DENOM:   # 批4 T12：四断言 PASS 面（goal-dir 面，engine 面双副本同构）
            outs = []
            for t in (t1, t2):
                gd = fresh_of(t, FIX, "G-g1")   # 目录名=goal_id：与 fresh 同名（新 id 前缀 INT-g1-*）
                prep_denominator(gd)
                a = run_engine(spec, gd)
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(a.stdout)
            if outs is None:
                fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(label + "(不确定性)")
                continue
            gp = os.path.join(GOLD, label + ".norm")
            gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
        for label, spec in ENGINE_CMDS:
            outs = []
            for t in (t1, t2):
                gd = fresh(t)
                prep_engine(gd)
                a = run_engine(spec, gd)
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(norm_engine(a.stdout, gd))
            if outs is None:
                fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(label + "(不确定性)")
                continue
            gp = os.path.join(GOLD, label + ".norm")
            gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
        for spec in GRAPH_CMDS:
            name = spec[0]
            outs = []
            for t in (t1, t2):
                gd = fresh(t)
                prep_graph(gd)
                a = run_cli(gd, name, spec[1:])
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(norm_read(a.stdout))
            if outs is None:
                fails.append(name + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(name + "(不确定性)")
                continue
            gp = os.path.join(GOLD, "graph-" + name + ".norm")
            gate_golden(gp, outs[0], "graph-" + name, bless, fails, inits, "输出漂移")
        for label, spec in VIZ_CMDS:
            outs = []
            for t in (t1, t2):
                gd = fresh_of(t, VIZ_FIX, "diff-authz")
                a = run_engine(spec, gd)
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(a.stdout)
            if outs is None:
                fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(label + "(不确定性)")
                continue
            gp = os.path.join(GOLD, label + ".norm")
            gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
        for label, spec in RECHECK_CMDS:   # 批4 评审收尾：diff-authz hash-recheck PASS 面
            outs = []
            for t in (t1, t2):
                gd = fresh_of(t, VIZ_FIX, "diff-authz")
                a = run_engine(spec, gd)
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(a.stdout)
            if outs is None:
                fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(label + "(不确定性)")
                continue
            gp = os.path.join(GOLD, label + ".norm")
            gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
        for faces, openssl_gated in ((ADAPTER_CMDS, False), (NUCLEI_CMDS, True)):
            if openssl_gated and shutil.which("openssl") is None:
                for label, _ in faces:
                    print("SKIP " + label + "(ENV: openssl 缺失——验签面不可跑，skipUnless 同口径)")
                continue
            for label, spec in faces:
                outs = []
                for t in (t1, t2):
                    gd = fresh(t)
                    a = run_engine(spec, gd)
                    if a.returncode != 0:
                        outs = None
                        break
                    outs.append(norm_adapter(gd))
                if outs is None:
                    fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                    continue
                if outs[0] != outs[1]:
                    fails.append(label + "(不确定性)")
                    continue
                gp = os.path.join(GOLD, label + ".norm")
                gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
        for label, spec in KN_CMDS:   # 批次 5 T11：kn 面（tanyin-knowledge 确定性导出/匹配）
            outs = []
            for t in (t1, t2):
                gd = os.path.join(t, "kn-lib")
                shutil.rmtree(gd, ignore_errors=True)
                prep_knowledge(gd)
                a = run_engine(spec, gd)
                if a.returncode != 0:
                    outs = None
                    break
                outs.append(norm_kn(a.stdout, gd))
            if outs is None:
                fails.append(label + "(非零退出 rc=%d)" % a.returncode)
                continue
            if outs[0] != outs[1]:
                fails.append(label + "(不确定性)")
                continue
            gp = os.path.join(GOLD, label + ".norm")
            gate_golden(gp, outs[0], label, bless, fails, inits, "输出漂移")
    for n in inits:
        print("INIT " + n)
    if fails:
        for f in fails:
            print("FAIL " + f)
        return 1
    print("PASS golden: %d 读面 + %d 写面 + %d phases 面 + %d engine 面 + %d graph 面 + %d adapter 面 + %d viz 面 + %d recheck 面 + %d kn 面 全部锁定且确定"
          % (len(READ_CMDS), len(WRITE_CMDS), len(PHASES_CMDS) + len(PHASES_DENOM),
             len(ENGINE_CMDS), len(GRAPH_CMDS),
             len(ADAPTER_CMDS) + len(NUCLEI_CMDS), len(VIZ_CMDS), len(RECHECK_CMDS),
             len(KN_CMDS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

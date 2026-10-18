# -*- coding: utf-8 -*-
"""演进飞轮①评测棘轮 gate 钉测（设计 docs/design/evolution-flywheel-v1.md 第 4 齿·宪法#43）。

python3 -m unittest tests.test_capability_gate
律：纯 stdlib、3.9 兼容、全本地夹具零外联（无 docker/无网/无 LLM——scorer 对
夹具会话纯函数回归=裁决 I 既定通道）。

四层钉：
  ①避坑卡 schema（knowledge/ 卡型扩 negative）——front matter 校验/读写往返/
    cp-index 家族兼容读（经典六列+扩列两形）/CP 编号空间跨索引连续/种子库
    只读纪律（R7）/仓内 schema 件在场（SCHEMA.md+ng-index.tsv 表头，cp-index
    本体 50 行六列冻结钉——W3 舰在树件零触碰）。
  ②变更检测——git base..worktree 对能力件 pathspec（技法卡/避坑卡/提示词文件
    phases+SKILL.md/工具卡 tools.lock）±行即命中；无关文件零误报；未跟踪新卡
    在案；无变更=changed False。
  ③GT-scorecard 复跑（D2 件复用）——subprocess 实跑 tests/eval_range_recall.py
    对夹具 battle 会话+GT（同 GT 同 scorer 口径）；误报=活发现集内重放证伪
    （FD REJECTED/EV not-reproduced）；聚合=微平均（总命中/总 GT）。
  ④棘轮判决——delta 计算/阈值语义（回退>阈值才拒）/-baseline 棘轮只紧不松/
    rc 契约（0 过 1 拒 2 环境）/无变更秒过（不触碰 suite）/--hook 单行 terse 形态。
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
GATE = os.path.join(REPO, "scripts", "capability_gate.py")
SEED = os.path.join(REPO, "knowledge")

sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger.schemas import TABLES  # noqa: E402  测试侧单源表头（生产件零依赖 cli）

_spec = importlib.util.spec_from_file_location("capability_gate", GATE)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


# --------------------------------------------------------------- 夹具构造 --

def _tsv(path, table, rows):
    cols = TABLES[table]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")


def _ev_card(ev_id, marker):
    return ("---\nid: %s\ntitle: 夹具证据 %s\nsource_type: command\n"
            "observed_at: 2026-10-19T00:00:00Z\nnetwork_position: intranet\n"
            "preconditions: []\nexpected:\n  matchers:\n    - type: word\n"
            "    words:\n      - %s\ncleanup: ''\npair_group: \n---\n"
            "## 摘录\n200 ok %s\n" % (ev_id, ev_id, marker, marker))


def make_session(sess, marker="GTTEST-01", asset="http://svc-test:8001/search",
                 probe=False, fd_rejected=False, extra_gt_marker=None,
                 findings_n=1):
    """最小可评分会话：1 资产+1 意图+N 发现+1 证据卡+重放 VERIFIED 行。
    probe=True → replay-probe not-reproduced（发现证伪=误报面）；
    fd_rejected=True → replay:FD:REJECTED；extra_gt_marker → GT 多一条无命中
    （recall=1/2）。"""
    os.makedirs(os.path.join(sess, "evidence"), exist_ok=True)
    _tsv(os.path.join(sess, "assets.tsv"), "assets.tsv",
         [{"id": "AST-0001", "type": "web", "value": asset,
           "in_scope": "in_scope", "schema_version": 1,
           "created": "2026-10-19T00:00:00Z"}])
    _tsv(os.path.join(sess, "creds.tsv"), "creds.tsv", [])
    _tsv(os.path.join(sess, "intents.tsv"), "intents.tsv",
         [{"id": "INT-0001", "title": "t", "detail": "d", "status": "done",
           "engine": "manual", "kind": "scan", "schema_version": 1,
           "created": "2026-10-19T00:00:00Z"}])
    _tsv(os.path.join(sess, "facts.tsv"), "facts.tsv", [])
    _tsv(os.path.join(sess, "E-index.tsv"), "E-index.tsv",
         [{"id": "EV-0001", "title": "夹具证据", "source_type": "command",
           "observed_at": "2026-10-19T00:00:00Z", "network_position": "intranet",
           "repro_command": "GET /", "repro_kind": "single",
           "content_hash_raw": "a" * 8, "content_hash_norm": "a" * 8,
           "card_path": "evidence/EV-0001.md", "schema_version": 1,
           "created": "2026-10-19T00:00:00Z"}])
    frows = []
    for i in range(1, findings_n + 1):
        frows.append({"id": "FD-%04d" % i, "intent_id": "INT-0001",
                      "title": "夹具发现 %d" % i, "confidence": "C1",
                      "impact": "中", "exploitation_status": "verified",
                      "vuln_ref": "CWE-79", "scope_check": "in_scope",
                      "description_brief": "b", "reproducible_steps": "s",
                      "affected_asset_id": "AST-0001",
                      "evidence_ids": "EV-0001", "status": "active",
                      "schema_version": 1, "created": "2026-10-19T00:00:00Z"})
    _tsv(os.path.join(sess, "findings.tsv"), "findings.tsv", frows)
    tl = [{"event": "replay:EV-0001:VERIFIED", "timestamp":
           "2026-10-19T00:00:00Z", "actor": "warrior", "phase": "P4",
           "prev_hash": "GENESIS", "hash": "h1", "schema_version": 1}]
    if probe:
        tl.append({"event": "replay-probe EV-0001 verdict=not-reproduced",
                   "timestamp": "2026-10-19T00:01:00Z", "actor": "warrior",
                   "phase": "P4", "prev_hash": "h1", "hash": "h2",
                   "schema_version": 1})
    if fd_rejected:
        tl.append({"event": "replay:FD-0001:REJECTED",
                   "timestamp": "2026-10-19T00:02:00Z", "actor": "warrior",
                   "phase": "P4", "prev_hash": "h2", "hash": "h3",
                   "schema_version": 1})
    _tsv(os.path.join(sess, "timeline.tsv"), "timeline.tsv", tl)
    with open(os.path.join(sess, "evidence", "EV-0001.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(_ev_card("EV-0001", marker))
    planted = [{"id": "GT-01", "endpoint": asset, "marker": marker}]
    if extra_gt_marker:
        planted.append({"id": "GT-02", "endpoint": asset,
                        "marker": extra_gt_marker})
    return {"planted": planted}


def make_battle(root, n, **kw):
    """battle-N 家目录（suite=root/battles；GT=root/gt/<gen>.json=battle.py 同源）。"""
    gen = "G-t%d" % n
    sess = os.path.join(root, "battles", "battle-%d" % n, gen)
    gt = make_session(sess, **kw)
    os.makedirs(os.path.join(root, "gt"), exist_ok=True)
    with open(os.path.join(root, "gt", gen + ".json"), "w", encoding="utf-8") as f:
        json.dump(gt, f, ensure_ascii=False)
    return os.path.join(root, "battles", "battle-%d" % n)


def make_repo(td):
    """临时 git 仓：基线提交含能力件三面+无关件（变更检测夹具）。"""
    repo = os.path.join(td, "repo")
    os.makedirs(repo)
    subprocess.run(["git", "init", "-q", repo], check=True)
    for k, v in (("user.email", "gate@test"), ("user.name", "gate-test")):
        subprocess.run(["git", "-C", repo, "config", k, v], check=True)
    os.makedirs(os.path.join(repo, "knowledge", "concepts"))
    os.makedirs(os.path.join(repo, "phases"))
    with open(os.path.join(repo, "knowledge", "cp-index.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\n"
                "CP-0001\t夹具技法\tKP-0001\ttopic\tlearned\t2026-10-01\n")
    with open(os.path.join(repo, "knowledge", "concepts", "CP-0001.md"), "w",
              encoding="utf-8") as f:
        f.write("---\nid: CP-0001\nkind: technique\ntitle: 夹具技法\n---\nbody\n")
    with open(os.path.join(repo, "phases", "P0.md"), "w", encoding="utf-8") as f:
        f.write("# P0 门方法论\n")
    with open(os.path.join(repo, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("# skill\n")
    with open(os.path.join(repo, "tools.lock"), "w", encoding="utf-8") as f:
        f.write("format_version=1\n")
    with open(os.path.join(repo, "unrelated.txt"), "w", encoding="utf-8") as f:
        f.write("x\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-qm", "base"], check=True)
    return repo


def _append(path, line):
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line)


def run_gate(args):
    return subprocess.run([sys.executable, GATE] + args, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120)


# ------------------------------------------------------- ① 避坑卡 schema --

class TestNegativeCardSchema(unittest.TestCase):

    def fm(self, **over):
        base = {"id": "CP-0051", "kind": "negative", "title": "SQLmap 默认参数在反代限流场景必卡死",
                "failure_path": "直跑 sqlmap --batch 不退避，撞限流 429 循环",
                "conditions": "目标前置反代带全局限流（响应含 429/Retry-After）时",
                "ledger_ref": "battle-28/timeline.tsv:631",
                "vuln_class": "wstg-inpv:inj", "status": "learned",
                "last_verified": "2026-10-19"}
        base.update(over)
        return base

    def test_validate_ok(self):
        self.assertEqual(gate.validate_negative_card(self.fm()), [])

    def test_validate_bad_fields(self):
        problems = gate.validate_negative_card(
            self.fm(kind="technique", failure_path="",
                    ledger_ref="口述无出处", status="bogus"))
        joined = "; ".join(problems)
        self.assertIn("kind", joined)
        self.assertIn("failure_path", joined)
        self.assertIn("ledger_ref", joined)
        self.assertIn("status", joined)

    def test_write_read_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            kd = os.path.join(td, "knowledge")
            os.makedirs(kd)
            p1 = gate.write_negative_card(kd, self.fm(), body="## 失败路径\n见上\n")
            self.assertTrue(p1.endswith("CP-0051.md"))
            idx = os.path.join(kd, gate.NEGATIVE_DIR, gate.NEG_INDEX_NAME)
            self.assertTrue(os.path.isfile(idx))
            with open(idx, encoding="utf-8") as f:
                lines = f.read().splitlines()
            self.assertEqual(lines[0].split("\t"),
                             list(gate.CP_INDEX_BASE_COLS + gate.NEG_INDEX_EXT_COLS))
            cards = gate.read_negative_cards(kd)
            self.assertEqual(len(cards), 1)
            self.assertEqual(cards[0]["id"], "CP-0051")
            self.assertEqual(cards[0]["kind"], "negative")
            self.assertEqual(cards[0]["ledger_ref"], "battle-28/timeline.tsv:631")
            self.assertEqual(cards[0]["failure_path"], self.fm()["failure_path"])

    def test_id_continues_cp_namespace_across_indexes(self):
        with tempfile.TemporaryDirectory() as td:
            kd = os.path.join(td, "knowledge")
            os.makedirs(os.path.join(kd, "concepts"))
            with open(os.path.join(kd, "cp-index.tsv"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\n"
                        "CP-0001\ta\tKP-0001\tt\tlearned\t2026-10-01\n"
                        "CP-0002\tb\tKP-0001\tt\tlearned\t2026-10-01\n")
            self.assertEqual(gate.next_negative_id(kd), "CP-0003")
            gate.write_negative_card(kd, self.fm(id=""))
            self.assertEqual(gate.next_negative_id(kd), "CP-0004")

    def test_index_family_reader_accepts_classic_and_extended(self):
        with tempfile.TemporaryDirectory() as td:
            classic = os.path.join(td, "cp-index.tsv")
            with open(classic, "w", encoding="utf-8", newline="\n") as f:
                f.write("id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\n"
                        "CP-0001\ta\tKP\tt\tlearned\t2026-10-01\n")
            rows = gate.read_index_family(classic)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], "CP-0001")
            self.assertEqual(rows[0].get("kind", ""), "")   # 经典形无扩列=空
            ext = os.path.join(td, "ng-index.tsv")
            with open(ext, "w", encoding="utf-8", newline="\n") as f:
                f.write("\t".join(gate.CP_INDEX_BASE_COLS + gate.NEG_INDEX_EXT_COLS)
                        + "\nCP-0051\tx\t\t\tlearned\t2026-10-19\tnegative\tfp"
                          "\tcond\tbattle-1/facts.tsv:9\n")
            rows2 = gate.read_index_family(ext)
            self.assertEqual(rows2[0]["kind"], "negative")
            self.assertEqual(rows2[0]["ledger_ref"], "battle-1/facts.tsv:9")

    def test_write_rejects_seed_root(self):
        with self.assertRaises(gate.SeedFrozenError):
            gate.write_negative_card(SEED, self.fm())

    def test_seed_schema_files_present_and_cp_index_frozen(self):
        schema = os.path.join(SEED, gate.NEGATIVE_DIR, "SCHEMA.md")
        self.assertTrue(os.path.isfile(schema))
        with open(schema, encoding="utf-8") as f:
            doc = f.read()
        self.assertIn("kind: negative", doc)
        self.assertIn("ledger_ref", doc)
        idx = os.path.join(SEED, gate.NEGATIVE_DIR, gate.NEG_INDEX_NAME)
        self.assertTrue(os.path.isfile(idx))
        with open(idx, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)                    # 表头零数据行（蒸馏归 W5）
        self.assertEqual(lines[0].split("\t"),
                         list(gate.CP_INDEX_BASE_COLS + gate.NEG_INDEX_EXT_COLS))
        with open(os.path.join(SEED, "cp-index.tsv"), encoding="utf-8") as f:
            cp = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(cp), 51)                      # 表头+50 行=W3 舰冻结钉
        self.assertEqual(cp[0].split("\t"), list(gate.CP_INDEX_BASE_COLS))




# ---------------------------------------------------------- ② 变更检测 --

class TestChangeDetection(unittest.TestCase):

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = make_repo(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_no_changes(self):
        r = gate.detect_changes(self.repo)
        self.assertFalse(r["changed"])
        self.assertEqual(r["files"], [])

    def test_cp_index_line_change_hits_technique_surface(self):
        _append(os.path.join(self.repo, "knowledge", "cp-index.tsv"),
                "CP-0002\t新技法\tKP-0001\tt\tlearned\t2026-10-19\n")
        r = gate.detect_changes(self.repo)
        self.assertTrue(r["changed"])
        self.assertIn("knowledge/cp-index.tsv", r["surfaces"]["technique_cards"])

    def test_prompt_and_tool_surfaces(self):
        _append(os.path.join(self.repo, "phases", "P0.md"), "新增段\n")
        _append(os.path.join(self.repo, "tools.lock"), "newtool\tv1\td\ts\n")
        r = gate.detect_changes(self.repo)
        self.assertIn("phases/P0.md", r["surfaces"]["prompt_files"])
        self.assertIn("tools.lock", r["surfaces"]["tool_lock"])
        self.assertNotIn("knowledge/cp-index.tsv", r["files"])

    def test_skill_md_counts_as_prompt_file(self):
        _append(os.path.join(self.repo, "SKILL.md"), "路由新增\n")
        r = gate.detect_changes(self.repo)
        self.assertIn("SKILL.md", r["surfaces"]["prompt_files"])

    def test_untracked_new_card_detected(self):
        with open(os.path.join(self.repo, "knowledge", "concepts", "CP-0099.md"),
                  "w", encoding="utf-8") as f:
            f.write("---\nid: CP-0099\n---\n")
        r = gate.detect_changes(self.repo)
        self.assertTrue(r["changed"])
        self.assertIn("knowledge/concepts/CP-0099.md", r["files"])

    def test_unrelated_file_only_not_a_capability_change(self):
        _append(os.path.join(self.repo, "unrelated.txt"), "more\n")
        r = gate.detect_changes(self.repo)
        self.assertFalse(r["changed"])


# ------------------------------------------- ③ GT-scorecard 复跑+误报面 --

class TestScorecard(unittest.TestCase):

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.td.name, "suite")
        os.makedirs(self.root)

    def tearDown(self):
        self.td.cleanup()

    def test_recall_from_real_scorer_subprocess(self):
        make_battle(self.root, 1)
        sc = gate.scorecard(REPO, os.path.join(self.root, "battles"),
                            gt_dir=os.path.join(self.root, "gt"))
        self.assertEqual(sc["battles"][0]["n"], 1)
        self.assertEqual(sc["battles"][0]["recall"], 1.0)
        self.assertEqual(sc["battles"][0]["hits"], 1)
        self.assertEqual(sc["battles"][0]["total"], 1)
        self.assertEqual(sc["aggregate"]["recall"], 1.0)

    def test_micro_average_across_battles(self):
        make_battle(self.root, 1)                                        # 1/1
        make_battle(self.root, 2, extra_gt_marker="GTMISS-02")           # 1/2
        sc = gate.scorecard(REPO, os.path.join(self.root, "battles"),
                            gt_dir=os.path.join(self.root, "gt"))
        self.assertEqual(len(sc["battles"]), 2)
        self.assertEqual(sc["aggregate"]["hits"], 2)
        self.assertEqual(sc["aggregate"]["total"], 3)
        self.assertAlmostEqual(sc["aggregate"]["recall"], 2 / 3, places=4)

    def test_false_positive_counting_probe_and_rejected(self):
        make_battle(self.root, 1, probe=True, fd_rejected=True)
        fp, active = gate.fp_of_session(
            os.path.join(self.root, "battles", "battle-1", "G-t1"))
        self.assertEqual((fp, active), (1, 1))   # 证伪双信号同一发现不双计
        make_battle(self.root, 2)
        fp2, active2 = gate.fp_of_session(
            os.path.join(self.root, "battles", "battle-2", "G-t2"))
        self.assertEqual((fp2, active2), (0, 1))   # 干净会话零误报
        fp3, active3 = gate.fp_of_session(
            os.path.join(self.td.name, "no-such-session"))
        self.assertEqual((fp3, active3), (0, 0))    # 缺表=零发现零误报

    def test_probe_also_kills_recall(self):
        make_battle(self.root, 1, probe=True)
        sc = gate.scorecard(REPO, os.path.join(self.root, "battles"),
                            gt_dir=os.path.join(self.root, "gt"))
        self.assertEqual(sc["battles"][0]["recall"], 0.0)   # 精度门=证伪不计
        self.assertEqual(sc["battles"][0]["fp"], 1)
        self.assertEqual(sc["battles"][0]["fp_rate"], 1.0)

    def test_fp_of_session_headerless_real_shape(self):
        # 真实 battle 会话=无表头冻结列序（schemas.py TABLES 单源；本测裸写钉）
        with tempfile.TemporaryDirectory() as td:
            s = os.path.join(td, "G-real")
            os.makedirs(s)
            with open(os.path.join(s, "findings.tsv"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("FD-0001\tINT-1\tt\tC1\t中\tverified\t\t\tCWE-79"
                        "\tin_scope\tb\ts\tAST-1\tEV-1\t\t\tactive\t1"
                        "\t2026-10-19T00:00:00Z\n")
                f.write("FD-0002\tINT-1\tt\tC1\t中\tverified\t\t\tCWE-79"
                        "\tin_scope\tb\ts\tAST-1\tEV-2\t\t\tactive\t1"
                        "\t2026-10-19T00:00:00Z\n")
            with open(os.path.join(s, "timeline.tsv"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("2026-10-19T00:00:00Z\tw\tP4\treplay:EV-1:VERIFIED"
                        "\t\tGENESIS\th1\t1\n")
                f.write("2026-10-19T00:01:00Z\tw\tP4\treplay-probe EV-1 "
                        "verdict=not-reproduced\t\th1\th2\t1\n")
            fp, active = gate.fp_of_session(s)
            self.assertEqual((fp, active), (1, 2))

    def test_gen_prefers_exact_main_dir_over_backups(self):
        # 真实 battle 家目录含 .bak-preReplay/.corrupt-keep 备份族——主代优先
        with tempfile.TemporaryDirectory() as td:
            home = os.path.join(td, "battle-29")
            for g in ("G-r30.bak-preReplay", "G-r30"):
                os.makedirs(os.path.join(home, g))
            self.assertEqual(gate._gen_of(home), "G-r30")

    def test_frozen_column_indices_match_tables(self):
        # 列位漂移钉：冻结列位须与 schemas.py TABLES 逐位一致（schema bump=红）
        self.assertEqual(TABLES["findings.tsv"].index("id"), gate._FI_ID)
        self.assertEqual(TABLES["findings.tsv"].index("evidence_ids"), gate._FI_EV)
        self.assertEqual(TABLES["findings.tsv"].index("control_evidence_ids"),
                         gate._FI_CEV)
        self.assertEqual(TABLES["findings.tsv"].index("status"), gate._FI_STATUS)
        self.assertEqual(len(TABLES["findings.tsv"]), gate._FINDINGS_W)
        self.assertEqual(TABLES["timeline.tsv"].index("event"), gate._TI_EVENT)
        self.assertEqual(len(TABLES["timeline.tsv"]), gate._TIMELINE_W)

    def test_missing_gt_battle_skipped_with_reason(self):
        make_battle(self.root, 1)
        os.remove(os.path.join(self.root, "gt", "G-t1.json"))
        sc = gate.scorecard(REPO, os.path.join(self.root, "battles"),
                            gt_dir=os.path.join(self.root, "gt"))
        self.assertEqual(sc["battles"], [])
        self.assertEqual(sc["skipped"][0]["reason"], "no-gt")


# ------------------------------------------------- ④ delta+棘轮判决+rc --

class TestDeltaVerdict(unittest.TestCase):

    def agg(self, recall, fp_rate):
        return {"recall": recall, "fp_rate": fp_rate, "hits": 0, "total": 0,
                "fp": 0, "active": 0}

    def test_delta_math(self):
        d = gate.compute_delta(self.agg(0.9, 0.1), self.agg(0.8, 0.2))
        self.assertAlmostEqual(d["recall"]["delta"], -0.1, places=6)
        self.assertAlmostEqual(d["fp_rate"]["delta"], 0.1, places=6)
        self.assertEqual(d["recall"]["before"], 0.9)

    def test_verdict_reject_on_recall_regression(self):
        d = gate.compute_delta(self.agg(0.9, 0.1), self.agg(0.8, 0.1))
        v, reasons = gate.verdict_of(d, 0.0, 0.0)
        self.assertEqual(v, "reject")
        self.assertTrue(reasons)

    def test_verdict_threshold_tolerance(self):
        d = gate.compute_delta(self.agg(0.9, 0.1), self.agg(0.8, 0.1))
        v, _ = gate.verdict_of(d, 0.15, 0.0)      # 回退 0.1 ≤ 阈值 0.15
        self.assertEqual(v, "pass")

    def test_verdict_reject_on_fp_regression(self):
        d = gate.compute_delta(self.agg(0.9, 0.1), self.agg(0.9, 0.25))
        v, reasons = gate.verdict_of(d, 0.0, 0.0)
        self.assertEqual(v, "reject")
        self.assertTrue(any("误报" in r for r in reasons))

    def test_verdict_pass_when_no_regression(self):
        d = gate.compute_delta(self.agg(0.8, 0.1), self.agg(0.9, 0.05))
        v, reasons = gate.verdict_of(d, 0.0, 0.0)
        self.assertEqual(v, "pass")
        self.assertEqual(reasons, [])


class TestMainGate(unittest.TestCase):
    """e2e：rc 契约 0/1/2+delta JSON 落盘+秒过+棘轮更新律+--hook 形态。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = make_repo(self.td.name)
        self.root = os.path.join(self.td.name, "suite")
        os.makedirs(self.root)
        self.suite = os.path.join(self.root, "battles")
        self.gt = os.path.join(self.root, "gt")
        self.baseline = os.path.join(self.td.name, "baseline.json")
        self.out = os.path.join(self.td.name, "delta.json")

    def tearDown(self):
        self.td.cleanup()

    def _write_baseline(self, recall, fp_rate):
        gate.write_baseline(self.baseline, {
            "schema_version": 1, "arm": "tanyin", "battles": [],
            "aggregate": {"recall": recall, "fp_rate": fp_rate, "hits": 0,
                          "total": 0, "fp": 0, "active": 0}})

    def _args(self):
        return ["--repo", self.repo, "--suite", self.suite, "--gt-dir", self.gt,
                "--baseline", self.baseline, "--out", self.out]

    def test_no_changes_fast_pass_without_touching_suite(self):
        r = run_gate(self._args() + ["--suite", os.path.join(self.td.name, "nope")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.out, encoding="utf-8") as f:
            d = json.load(f)
        self.assertFalse(d["changes"]["changed"])
        self.assertEqual(d["eval"]["mode"], "skipped-no-changes")
        self.assertEqual(d["verdict"], "pass")

    def test_reject_on_regression_rc1(self):
        make_battle(self.root, 1, extra_gt_marker="GTMISS-02")   # after=0.5
        self._write_baseline(1.0, 0.0)
        _append(os.path.join(self.repo, "knowledge", "cp-index.tsv"),
                "CP-0002\t新\tKP\tt\tlearned\t2026-10-19\n")
        r = run_gate(self._args())
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        with open(self.out, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual(d["verdict"], "reject")
        self.assertTrue(d["reasons"])
        self.assertAlmostEqual(d["eval"]["after"]["recall"], 0.5, places=4)

    def test_pass_when_metrics_hold_rc0(self):
        make_battle(self.root, 1)
        self._write_baseline(1.0, 0.0)
        _append(os.path.join(self.repo, "tools.lock"), "newtool\tv1\td\ts\n")
        r = run_gate(self._args())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.out, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual(d["verdict"], "pass")
        self.assertEqual(d["eval"]["mode"], "baseline-vs-rerun")

    def test_collect_first_when_no_baseline(self):
        make_battle(self.root, 1)
        _append(os.path.join(self.repo, "phases", "P0.md"), "x\n")
        r = run_gate(self._args())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.out, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual(d["verdict"], "collect-first")
        self.assertTrue(os.path.isfile(self.baseline))
        with open(self.baseline, encoding="utf-8") as f:
            b = json.load(f)
        self.assertEqual(b["aggregate"]["recall"], 1.0)

    def test_update_baseline_refuses_regression_ratchet(self):
        make_battle(self.root, 1, extra_gt_marker="GTMISS-02")   # 0.5<1.0
        self._write_baseline(1.0, 0.0)
        with open(self.baseline, "rb") as f:
            before = f.read()
        _append(os.path.join(self.repo, "tools.lock"), "t\tv\td\ts\n")
        r = run_gate(self._args() + ["--update-baseline"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        with open(self.baseline, "rb") as f:
            self.assertEqual(f.read(), before)      # 棘轮只紧不松：拒降

    def test_update_baseline_accepts_improvement(self):
        make_battle(self.root, 1)
        self._write_baseline(0.5, 0.2)
        _append(os.path.join(self.repo, "tools.lock"), "t\tv\td\ts\n")
        r = run_gate(self._args() + ["--update-baseline"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.baseline, encoding="utf-8") as f:
            b = json.load(f)
        self.assertEqual(b["aggregate"]["recall"], 1.0)

    def test_env_error_rc2_when_nothing_scoreable(self):
        make_battle(self.root, 1)
        os.remove(os.path.join(self.root, "gt", "G-t1.json"))
        self._write_baseline(1.0, 0.0)
        _append(os.path.join(self.repo, "tools.lock"), "t\tv\td\ts\n")
        r = run_gate(self._args())
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_hook_mode_terse_single_line(self):
        make_battle(self.root, 1, extra_gt_marker="GTMISS-02")
        self._write_baseline(1.0, 0.0)
        _append(os.path.join(self.repo, "tools.lock"), "t\tv\td\ts\n")
        r = run_gate(self._args() + ["--hook"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("capability-gate:"))
        self.assertIn("REJECT", lines[0])


if __name__ == "__main__":
    unittest.main()

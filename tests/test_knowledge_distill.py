# -*- coding: utf-8 -*-
"""W5 知识环·蒸馏管线 v1 钉测（设计 docs/design/evolution-flywheel-v1.md 第 2 齿·宪法#43）。

python3 -m unittest tests.test_knowledge_distill
律：纯 stdlib、3.9 兼容、全本地夹具零外联（无 docker/无网/无 LLM——LLM 离线态
规则蒸馏 v1=确定性纯函数，不调真模型）。

五层钉：
  ① battle 数据装载——battle-N 名形/G-* 主代优选（.bak 备份族不夺位）/三表
    （findings/timeline/facts）无表头为主形+带表头形同吃/物理行号=ledger_ref
    锚（行号指回的物理行真含该行数据）/settle-report 解析（recall+MISSING）。
  ② 技法卡草案（cp 六列）——高置信模式（同 CWE 多例 verified+带证据）成卡/
    阈下不成/superseded·suspected 不计/无 CWE 不猜。
  ③ 避坑卡草案（ng 扩列含 ledger_ref）——误报路径（FD 重放 REJECTED+EV
    not-reproduced 双信号）/漏报族（MISSING 家族计数）/负面披露（facts
    不适用·未部署形）/verified 不产避坑。
  ④ 草案纪律——不自动入 cp-index/ng-index（棘轮门管入册）/人工确认位
    （review_status: pending+确认清单节）/确定性（同输入两跑逐字节一致）/
    编号预演跨索引连续。
  ⑤ CLI——python3 -m cli.knowledge distill rc 契约（0 成/2 用法环境）/
    confirm 走 write_negative_card 锚接口（review_status: accept 门+种子库
    R7 拒写）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, REPO)

from cli.knowledge import distill as D  # noqa: E402


# --------------------------------------------------------------- 夹具构造 --

FD_COLS = 19
TL_COLS = 8
FT_COLS = 8


def fd_row(i, gen="r1", cwe="CWE-79", status="active", exploit="verified",
           ev=None, title=None):
    ev = ev if ev is not None else "EV-%s-%04d" % (gen, i)
    title = title or ("反射 XSS：/search?q= 回显（fixture-%02d）" % i)
    vuln_ref = ("AST-1+" + cwe) if cwe else "AST-1"
    return ["FD-%s-%04d" % (gen, i), "INT-1", title, "C1", "中", exploit, "",
            "", vuln_ref, "in_scope", "证据摘要", "复现步骤", "AST-1", ev, "",
            "findings-cards/x.md", status, "2", "2026-10-20T10:00:00Z"]


def tl_row(ts, event, actor="CLI", phase="P4"):
    return [ts, actor, phase, event, "", "p" * 64, "h" * 64, "2"]


def ft_row(i, gen="r1", kind="info", target="range.local", detail="拓扑=8 服务"):
    return ["F-%s-%04d" % (gen, i), "INT-1", kind, target, detail, "1.0", "2",
            "2026-10-20T09:28:00Z"]


def _tsv(path, rows, header=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if header:
            f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(c) for c in r) + "\n")


FD_HEAD = ["id", "intent_id", "title", "confidence", "impact",
           "exploitation_status", "auth_context", "dedup_key", "vuln_ref",
           "scope_check", "description_brief", "reproducible_steps",
           "affected_asset_id", "evidence_ids", "control_evidence_ids",
           "card_path", "status", "schema_version", "created"]
TL_HEAD = ["timestamp", "actor", "phase", "event", "revert_cmd", "prev_hash",
           "hash", "schema_version"]
FT_HEAD = ["id", "intent_id", "kind", "target", "detail", "confidence",
           "schema_version", "created"]


def make_battle(root, n=1, gen="G-r1", findings=None, timeline=None, facts=None,
                settle=None, bak_gen=None, header=False):
    """最小 battle 家目录。<suite>/battle-N/G-<gen>/（会话）+settle-report.txt。"""
    bd = os.path.join(root, "battle-%d" % n)
    sess = os.path.join(bd, gen)
    hd = FD_HEAD if header else None
    _tsv(os.path.join(sess, "findings.tsv"), findings or [], header=hd)
    _tsv(os.path.join(sess, "timeline.tsv"), timeline or [],
         header=TL_HEAD if header else None)
    _tsv(os.path.join(sess, "facts.tsv"), facts or [],
         header=FT_HEAD if header else None)
    if bak_gen:
        bs = os.path.join(bd, bak_gen)
        _tsv(os.path.join(bs, "findings.tsv"), [fd_row(99)])
        _tsv(os.path.join(bs, "timeline.tsv"), [])
        _tsv(os.path.join(bs, "facts.tsv"), [])
    if settle is not None:
        with open(os.path.join(bd, "settle-report.txt"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(settle)
    return bd


def kdir(root, cp_rows=(("CP-0001", "SQL 注入测试域", "KP-1", "pack", "core",
                         "2026-09-24"),)):
    """运行时知识库夹具（cp-index 六列+可选 ng 扩列行）。"""
    kd = os.path.join(root, "knowledge")
    os.makedirs(kd, exist_ok=True)
    with open(os.path.join(kd, "cp-index.tsv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\n")
        for r in cp_rows:
            f.write("\t".join(r) + "\n")
    return kd


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "cli.knowledge"] + list(args),
                          cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def read_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ======================================================= ① battle 装载 ==

class TestLoadBattle(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="distill-t-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_battle_name_validation(self):
        bad = os.path.join(self.root, "not-a-battle")
        os.makedirs(bad)
        with self.assertRaises(D.DistillError):
            D.load_battle(bad)
        self.assertFalse(os.path.isdir(os.path.join(self.root, "missing")))

    def test_missing_dir_is_env_error(self):
        with self.assertRaises(D.DistillError):
            D.load_battle(os.path.join(self.root, "battle-9"))

    def test_main_gen_pick_backup_not_first(self):
        bd = make_battle(self.root, 5, gen="G-r30",
                         findings=[fd_row(1, gen="r30")],
                         timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")],
                         bak_gen="G-r30.bak-preReplay")
        bat = D.load_battle(bd)
        self.assertEqual(bat["gen"], "G-r30")

    def test_ledger_ref_lines_point_at_physical_rows(self):
        """行号锚回读：ledger_ref 指向的物理行真含那条 FD/F 行（可回放核验律）。"""
        rows = [fd_row(1), fd_row(2, cwe="CWE-89"), fd_row(3)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0002:VERIFIED")]
        ft = [ft_row(1), ft_row(2, detail="未部署侦察诱饵：不适用（披露）")]
        bd = make_battle(self.root, 1, findings=rows, timeline=tl, facts=ft)
        bat = D.load_battle(bd)
        fpath = os.path.join(bd, bat["gen"], "findings.tsv")
        with open(fpath, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for fr in bat["findings"]:
            self.assertIn(fr["id"], lines[fr["line"] - 1].split("\t")[0])
        self.assertEqual(bat["findings"][1]["line"], 2)
        self.assertEqual(bat["timeline"][-1]["line"], 2)

    def test_header_form_tables_same_eats(self):
        """带表头形（夹具/新工具产）同吃：数据行从物理第 2 行起，行号不漂。"""
        rows = [fd_row(1), fd_row(2)]
        bd = make_battle(self.root, 2, findings=rows,
                         timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")],
                         facts=[ft_row(1)], header=True)
        bat = D.load_battle(bd)
        self.assertEqual(len(bat["findings"]), 2)
        self.assertEqual(bat["findings"][0]["line"], 2)

    def test_settle_report_parse(self):
        settle = ("verify-chain: PASS\nrecall=0.5 (2/4)\n"
                  "MISSING\tidor-01\nMISSING\tidor-02\nMISSING\trole-01\n")
        bd = make_battle(self.root, 3, findings=[fd_row(1)],
                         timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")],
                         settle=settle)
        bat = D.load_battle(bd)
        self.assertTrue(bat["settled"])
        self.assertEqual(bat["recall"], 0.5)
        self.assertEqual(bat["recall_hits"], 2)
        self.assertEqual(bat["recall_total"], 4)
        self.assertEqual(bat["missing"], ["idor-01", "idor-02", "role-01"])

    def test_no_settle_is_unsetted_honest(self):
        bd = make_battle(self.root, 4, findings=[fd_row(1)],
                         timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        bat = D.load_battle(bd)
        self.assertFalse(bat["settled"])
        self.assertEqual(bat["missing"], [])


# ==================================================== ② 技法卡草案 ==

class TestTechniqueDrafts(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="distill-t-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.kd = kdir(self.root)

    def _run(self, findings, **kw):
        bd = make_battle(self.root, kw.pop("n", 1), findings=findings, **kw)
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        return bd, out, rep

    def test_high_confidence_pattern_makes_draft(self):
        f = [fd_row(1), fd_row(2), fd_row(3)]
        bd, out, rep = self._run(
            f, timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        self.assertEqual(rep["counts"]["technique_drafts"], 1)
        draft = rep["drafts"][0]
        fm = D.parse_front(D._read_text(draft["path"]))
        for col in ("id", "title", "source_id", "source_topic", "status", "updated"):
            self.assertTrue(str(fm.get(col, "")).strip(), "cp 六列缺 %s" % col)
        self.assertEqual(fm["source_id"], "battle-1")
        self.assertIn("CWE-79", fm["title"])
        self.assertEqual(fm["kind"], "technique-draft")
        self.assertTrue(fm["id"].startswith("CP-"))
        self.assertLessEqual(len(fm["title"]), 60)

    def test_below_threshold_no_draft(self):
        bd, out, rep = self._run(
            [fd_row(1)], timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        self.assertEqual(rep["counts"]["technique_drafts"], 0)
        self.assertFalse(os.path.exists(os.path.join(out, "techniques")))

    def test_superseded_and_suspected_not_counted(self):
        f = [fd_row(1, status="superseded"), fd_row(2, status="superseded"),
             fd_row(3, exploit="suspected"), fd_row(4)]
        bd, out, rep = self._run(
            f, timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        self.assertEqual(rep["counts"]["technique_drafts"], 0)

    def test_no_cwe_not_guessed(self):
        f = [fd_row(1, cwe=None), fd_row(2, cwe=None)]
        bd, out, rep = self._run(
            f, timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        self.assertEqual(rep["counts"]["technique_drafts"], 0)

    def test_similar_existing_noted_for_human_dedup(self):
        """cp-index 已有同域卡 → 草案记 similar_existing 供人工去重。"""
        self.kd = kdir(self.root, cp_rows=(
            ("CP-0001", "XSS 跨站脚本三型测试域（反射/存储/DOM）", "KP-1",
             "pack", "core", "2026-09-24"),))
        bd, out, rep = self._run(
            [fd_row(1), fd_row(2)],
            timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        draft = rep["drafts"][0]
        fm = D.parse_front(D._read_text(draft["path"]))
        self.assertIn("CP-0001", fm.get("similar_existing", ""))


# ====================================================== ③ 避坑卡草案 ==

class TestPitfallDrafts(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="distill-t-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.kd = kdir(self.root)

    def _run(self, **kw):
        bd = make_battle(self.root, kw.pop("n", 1), **kw)
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        return bd, out, rep

    def _fm(self, rep, i):
        return D.parse_front(D._read_text(rep["drafts"][i]["path"]))

    def test_fp_pitfall_from_fd_replay_rejected(self):
        f = [fd_row(1, cwe="CWE-89"),
             fd_row(2, cwe="CWE-89"),
             fd_row(3, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:VERIFIED"),
              tl_row("2026-10-20T12:00:00Z",
                     "replay:FD-r1-0003:REJECTED note=环境态差异锁死")]
        bd, out, rep = self._run(findings=f, timeline=tl)
        fp = [d for d in rep["drafts"] if d["kind"] == "pitfall-fp"]
        self.assertEqual(len(fp), 1)
        fm = D.parse_front(D._read_text(fp[0]["path"]))
        self.assertEqual(fm["kind"], "negative")
        for k in ("id", "kind", "title", "failure_path", "conditions",
                  "ledger_ref", "vuln_class", "status", "last_verified"):
            self.assertTrue(str(fm.get(k, "")).strip(), "避坑必填缺 %s" % k)
        self.assertEqual(fm["ledger_ref"], "battle-1/findings.tsv:3")
        self.assertIn("FD-r1-0003", fm["failure_path"])
        self.assertIn("锁死", fm["failure_path"] + fm["conditions"])
        self.assertEqual(fm["vuln_class"], "wstg-inpv")

    def test_fp_pitfall_from_probe_not_reproduced(self):
        f = [fd_row(1, cwe="CWE-639"), fd_row(2, cwe="CWE-639")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z",
                     "replay-probe EV-r1-0001 verdict=not-reproduced")]
        bd, out, rep = self._run(findings=f, timeline=tl)
        fp = [d for d in rep["drafts"] if d["kind"] == "pitfall-fp"]
        self.assertEqual(len(fp), 1)
        fm = D.parse_front(D._read_text(fp[0]["path"]))
        self.assertEqual(fm["ledger_ref"], "battle-1/findings.tsv:1")
        self.assertEqual(fm["vuln_class"], "wstg-authz")

    def test_verified_findings_no_fp_pitfall(self):
        f = [fd_row(1), fd_row(2)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:VERIFIED"),
              tl_row("2026-10-20T11:30:00Z", "replay-probe EV-r1-0002 verdict=reproduced")]
        bd, out, rep = self._run(findings=f, timeline=tl)
        self.assertEqual(rep["counts"]["pitfall_fp"], 0)

    def test_latest_replay_verdict_wins(self):
        """同 FD 多次重放取末值：REJECTED 后翻 VERIFIED=不产避坑。"""
        f = [fd_row(1, cwe="CWE-89"), fd_row(2, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:REJECTED"),
              tl_row("2026-10-20T12:00:00Z", "replay:FD-r1-0001:VERIFIED"),
              tl_row("2026-10-20T12:30:00Z", "replay:FD-r1-0002:VERIFIED")]
        bd, out, rep = self._run(findings=f, timeline=tl)
        self.assertEqual(rep["counts"]["pitfall_fp"], 0)

    def test_missing_family_pitfall_anchored_at_battle_end(self):
        settle = ("recall=0.5 (2/4)\nMISSING\tidor-01\nMISSING\tidor-02\n"
                  "MISSING\trole-01\nMISSING\trole-02\nMISSING\tweakpass-01\n")
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T18:00:00Z", "report done")]
        bd, out, rep = self._run(findings=[fd_row(1)], timeline=tl, settle=settle)
        miss = [d for d in rep["drafts"] if d["kind"] == "pitfall-miss"]
        self.assertEqual(len(miss), 2)  # idor(2)+role(2)；weakpass(1) 阈下
        fams = {D.parse_front(D._read_text(d["path"]))["source_topic"]: d
                for d in miss}
        for tt, d in fams.items():
            fm = D.parse_front(D._read_text(d["path"]))
            self.assertEqual(fm["ledger_ref"], "battle-1/timeline.tsv:2")
            self.assertEqual(fm["kind"], "negative")
        idor = [d for d in miss if "idor" in d["path"]][0]
        fm = D.parse_front(D._read_text(idor["path"]))
        self.assertIn("2", fm["failure_path"])
        self.assertEqual(fm["vuln_class"], "wstg-authz")

    def test_negative_fact_disclosure_pitfall(self):
        ft = [ft_row(1), ft_row(2, detail="未部署侦察诱饵：不适用（披露）"),
              ft_row(3, detail="资产面不适用理由：无独立 ip 型资产需单列")]
        bd, out, rep = self._run(
            findings=[fd_row(1)],
            timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")], facts=ft)
        fct = [d for d in rep["drafts"] if d["kind"] == "pitfall-fact"]
        self.assertEqual(len(fct), 2)
        fm = D.parse_front(D._read_text(fct[0]["path"]))
        self.assertEqual(fm["ledger_ref"], "battle-1/facts.tsv:2")
        self.assertEqual(fm["kind"], "negative")

    def test_negative_fact_skips_meta_and_submatrix_rows(self):
        """canary:/asset-class: 元披露与 submatrix 负结果置态（逐面系统生成
        闭包）不成卡——人审队列不被样板刷屏；跳过计数入报告。"""
        ft = [ft_row(1, target="canary:recon",
                    detail="未部署侦察诱饵：召回率口径不适用（披露）"),
              ft_row(2, target="asset-class:A2",
                    detail="不适用理由：无独立 ip 型攻击面需单列"),
              ft_row(3, target="svc-admin/admin/orders",
                    detail="svc-admin/admin/orders×wstg-apit 负结果置态："
                           "主类承载，余类不适用（单用途处理器面）"),
              ft_row(4, target="svc-api-gw",
                    detail="r5 XXE 阴性：/xml POST 501——XXE 通道不可达"),
              ft_row(5, target="172.28.0.2:8008",
                    detail="files：47 路径全 404——真实入口未发现，待深挖")]
        bd, out, rep = self._run(
            findings=[fd_row(1)],
            timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")], facts=ft)
        fct = [d for d in rep["drafts"] if d["kind"] == "pitfall-fact"]
        self.assertEqual(len(fct), 2)  # 只剩 XXE 阴性+入口未发现两条真负面
        skipped = json.dumps(rep["skipped"], ensure_ascii=False)
        self.assertIn("meta/submatrix", skipped)

    def test_no_session_no_missing_anchor_honest_skip(self):
        """无会话战（directive-only）：漏报族无账本锚=诚实跳过并记因，不造卡。"""
        bd = os.path.join(self.root, "battle-7")
        os.makedirs(bd)
        with open(os.path.join(bd, "settle-report.txt"), "w",
                  encoding="utf-8") as f:
            f.write("findings.tsv 不存在——战未毕或未开铸\n")
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertEqual(rep["counts"]["pitfall_drafts"], 0)
        self.assertTrue(any("no-session" in s.get("reason", "")
                            for s in rep["skipped"]))


# ==================================================== ④ 草案纪律 ==

class TestDraftDiscipline(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="distill-t-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.kd = kdir(self.root)

    def test_no_auto_index_write(self):
        """棘轮门管入册：蒸馏只落草案，不碰 cp-index/ng-index/negative/。"""
        before_cp = D._read_text(os.path.join(self.kd, "cp-index.tsv"))
        f = [fd_row(1), fd_row(2)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0002:REJECTED")]
        settle = "recall=0.5 (1/2)\nMISSING\tidor-01\nMISSING\tidor-02\n"
        bd = make_battle(self.root, 1, findings=f, timeline=tl, settle=settle,
                         facts=[ft_row(2, detail="未部署诱饵：不适用")])
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertGreater(rep["counts"]["pitfall_drafts"], 0)
        self.assertEqual(D._read_text(os.path.join(self.kd, "cp-index.tsv")),
                         before_cp)
        self.assertFalse(os.path.exists(os.path.join(self.kd, "ng-index.tsv")))
        self.assertFalse(os.path.exists(os.path.join(self.kd, "negative")))
        for d in rep["drafts"]:
            self.assertTrue(d["path"].startswith(os.path.abspath(out)))

    def test_drafts_carry_confirmation_slot(self):
        f = [fd_row(1), fd_row(2)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:REJECTED")]
        bd = make_battle(self.root, 2, findings=f, timeline=tl)
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertGreater(len(rep["drafts"]), 0)
        for d in rep["drafts"]:
            text = D._read_text(d["path"])
            fm = D.parse_front(text)
            self.assertEqual(fm.get("review_status"), "pending")
            self.assertIn("人工确认位", text)
            self.assertIn("确认", text)

    def test_determinism_same_input_twice(self):
        f = [fd_row(1), fd_row(2), fd_row(3, cwe="CWE-89"), fd_row(4, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0004:REJECTED")]
        settle = "recall=0.5 (2/4)\nMISSING\tidor-01\nMISSING\tidor-02\n"
        bd = make_battle(self.root, 3, findings=f, timeline=tl, settle=settle)
        o1, o2 = os.path.join(self.root, "o1"), os.path.join(self.root, "o2")
        D.distill_battle(bd, out=o1, knowledge_dir=self.kd)
        D.distill_battle(bd, out=o2, knowledge_dir=self.kd)
        for base in ("distill-report.json",):
            self.assertEqual(D._read_text(os.path.join(o1, base)),
                             D._read_text(os.path.join(o2, base)))
        n1 = sorted(os.listdir(os.path.join(o1, "techniques")))
        n2 = sorted(os.listdir(os.path.join(o2, "techniques")))
        self.assertEqual(n1, n2)
        for nm in n1:
            self.assertEqual(D._read_text(os.path.join(o1, "techniques", nm)),
                             D._read_text(os.path.join(o2, "techniques", nm)))

    def test_id_preview_cross_index_continuous(self):
        self.kd = kdir(self.root, cp_rows=(
            ("CP-0001", "a", "KP-1", "p", "core", "2026-09-24"),
            ("CP-0002", "b", "KP-1", "p", "core", "2026-09-24")))
        os.makedirs(os.path.join(self.kd, "negative"))
        with open(os.path.join(self.kd, "negative", "ng-index.tsv"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("id\ttitle\tsource_id\tsource_topic\tstatus\tupdated\t"
                    "kind\tfailure_path\tconditions\tledger_ref\n")
            f.write("CP-0007\t避坑\tbattle-0\tt\tlearned\t2026-10-01\t"
                    "negative\tfp\tcond\tbattle-0/findings.tsv:1\n")
        f = [fd_row(1), fd_row(2)]
        bd = make_battle(self.root, 4, findings=f,
                         timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")])
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertEqual(rep["drafts"][0]["id_preview"], "CP-0008")

    def test_redistill_replaces_stale_drafts(self):
        """重蒸馏=确定性重生成：自家旧草案清掉重写，不积陈货（同出目录幂等）。"""
        f = [fd_row(1), fd_row(2)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:REJECTED")]
        ft = [ft_row(1, detail="不适用：无独立面")]
        bd = make_battle(self.root, 6, findings=f, timeline=tl, facts=ft)
        out = os.path.join(self.root, "out")
        rep1 = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertTrue(any(d["kind"] == "pitfall-fact" for d in rep1["drafts"]))
        # 换输入：负面披露行撤走+误报行撤走 → 重蒸馏后旧草案文件必须消失
        make_battle(self.root, 6, findings=[fd_row(1), fd_row(2)],
                    timeline=[tl_row("2026-10-20T09:00:00Z", "add-goal G-1")],
                    facts=[])
        rep2 = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        self.assertFalse(any(d["kind"] == "pitfall-fact" for d in rep2["drafts"]))
        self.assertFalse(any(d["kind"] == "pitfall-fp" for d in rep2["drafts"]))
        for kind_dir in ("techniques", "pitfalls"):
            for nm in os.listdir(os.path.join(out, kind_dir)):
                self.assertIn(nm, [os.path.basename(d["path"])
                                   for d in rep2["drafts"]],
                              "陈货残留: %s/%s" % (kind_dir, nm))

    def test_report_counts_consistent_with_files(self):
        f = [fd_row(1), fd_row(2), fd_row(3, cwe="CWE-639")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0003:REJECTED")]
        bd = make_battle(self.root, 5, findings=f, timeline=tl,
                         facts=[ft_row(2, detail="不适用：未部署诱饵")])
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        on_disk = len(os.listdir(os.path.join(out, "techniques"))) + \
            len(os.listdir(os.path.join(out, "pitfalls")))
        self.assertEqual(on_disk, len(rep["drafts"]))
        self.assertEqual(rep["counts"]["technique_drafts"] +
                         rep["counts"]["pitfall_drafts"], len(rep["drafts"]))
        self.assertEqual(rep["battle"], "battle-5")
        self.assertEqual(rep["gen"], "G-r1")


# ======================================================== ⑤ CLI ==

class TestCli(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="distill-t-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.kd = kdir(self.root)

    def test_distill_cli_rc0_and_outputs(self):
        f = [fd_row(1), fd_row(2)]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0001:REJECTED")]
        bd = make_battle(self.root, 1, findings=f, timeline=tl)
        out = os.path.join(self.root, "out")
        r = run_cli("distill", bd, "--out", out, "--knowledge-dir", self.kd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "distill-report.json")))
        self.assertIn("battle-1", r.stdout)
        self.assertIn("未自动入册", r.stdout)

    def test_distill_cli_usage_errors_rc2(self):
        r = run_cli("distill")
        self.assertEqual(r.returncode, 2)
        r2 = run_cli("distill", os.path.join(self.root, "battle-404"))
        self.assertEqual(r2.returncode, 2)
        r3 = run_cli("nope")
        self.assertEqual(r3.returncode, 2)

    def test_confirm_pending_draft_refused_rc1(self):
        f = [fd_row(1, cwe="CWE-89"), fd_row(2, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0002:REJECTED")]
        bd = make_battle(self.root, 2, findings=f, timeline=tl)
        out = os.path.join(self.root, "out")
        D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        draft = os.path.join(out, "pitfalls",
                             sorted(os.listdir(os.path.join(out, "pitfalls")))[0])
        r = run_cli("confirm", draft, "--knowledge-dir", self.kd,
                    "--reviewer", "tester")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.kd, "negative")))

    def test_confirm_accepted_draft_writes_via_anchored_interface(self):
        """飞轮接口锚：confirm→write_negative_card 一函落卡+索引行 upsert。"""
        f = [fd_row(1, cwe="CWE-89"), fd_row(2, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z",
                     "replay:FD-r1-0002:REJECTED note=环境态锁死")]
        bd = make_battle(self.root, 3, findings=f, timeline=tl)
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        pit = [d for d in rep["drafts"] if d["kind"] == "pitfall-fp"][0]
        text = D._read_text(pit["path"]).replace(
            "review_status: pending", "review_status: accept", 1)
        with open(pit["path"], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        r = run_cli("confirm", pit["path"], "--knowledge-dir", self.kd,
                    "--reviewer", "tester")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = D.read_negative_cards_for_test(self.kd)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["kind"], "negative")
        self.assertEqual(cards[0]["vuln_class"], "wstg-inpv")
        self.assertTrue(cards[0]["ledger_ref"].startswith("battle-3/"))
        with open(os.path.join(self.kd, "negative", "ng-index.tsv"),
                  encoding="utf-8") as fh:
            idx = fh.read()
        self.assertIn(cards[0]["id"], idx)
        self.assertIn("tester", D._read_text(
            os.path.join(self.kd, "negative", cards[0]["id"] + ".md")))

    def test_report_subcommand_aggregates_suite(self):
        """suite 蒸馏总报：逐 battle distill-report.json 聚合计数+跳过无蒸馏战。"""
        for n, cwes in ((1, ["CWE-79", "CWE-79"]), (2, ["CWE-89", "CWE-89"])):
            f = [fd_row(i, gen="r%d" % n, cwe=cwes[i - 1]) for i in (1, 2)]
            tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1")]
            bd = make_battle(self.root, n, gen="G-r%d" % n, findings=f, timeline=tl)
            D.distill_battle(bd, knowledge_dir=self.kd)  # 缺省 out=<battle>/distill
        out = os.path.join(self.root, "suite-report.json")
        r = run_cli("report", self.root, "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        doc = read_json(out)
        self.assertEqual(doc["counts"]["technique_drafts"], 2)
        self.assertEqual(doc["counts"]["battles_distilled"], 2)
        self.assertEqual(doc["battles"][0]["battle"], "battle-1")
        # 无蒸馏产物战（battle-9 空目录）不炸、入 skipped
        os.makedirs(os.path.join(self.root, "battle-9"), exist_ok=True)
        r2 = run_cli("report", self.root, "--out", out)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        doc2 = read_json(out)
        self.assertTrue(any(s.get("battle") == "battle-9"
                            for s in doc2["skipped"]))

    def test_confirm_seed_repo_frozen_rc2(self):
        f = [fd_row(1, cwe="CWE-89"), fd_row(2, cwe="CWE-89")]
        tl = [tl_row("2026-10-20T09:00:00Z", "add-goal G-1"),
              tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0002:REJECTED")]
        bd = make_battle(self.root, 4, findings=f, timeline=tl)
        out = os.path.join(self.root, "out")
        rep = D.distill_battle(bd, out=out, knowledge_dir=self.kd)
        pit = [d for d in rep["drafts"] if d["kind"] == "pitfall-fp"][0]
        text = D._read_text(pit["path"]).replace(
            "review_status: pending", "review_status: accept", 1)
        with open(pit["path"], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        seed = os.path.join(REPO, "knowledge")
        r = run_cli("confirm", pit["path"], "--knowledge-dir", seed,
                    "--reviewer", "tester")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("种子库", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()

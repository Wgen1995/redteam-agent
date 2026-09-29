# -*- coding: utf-8 -*-
"""批次 7 T16：战场件三件。红=首战真实检出 8/20 账面 0/20（GT 键=127.0.0.1:800x 形 vs
在环 svc-* 命名→20 项全失配）+terminal-gate 冻结断言按 latest 行（P3 置格会话 P5 不可达）。

三件：
① scorer URL 归一化匹配——_norm_endpoint（只归语法：小写 host/剥默认端口/query 排序/
  去尾斜杠）+_canon_host（语义别名一律 GT 顶层 host_aliases 显式声明，禁猜测式映射）；
  score() 两侧先归一后比对（首战 0/20 键失配根因修复）。
② GT 键口径 RUNBOOK 显著位新节（tests/range/RUNBOOK.md 首屏后第一节）——测试钉死
  口径节在盘+ground-truth.json host_aliases 声明位在盘。
③ terminal-gate 冻结断言改「freeze 时在场行」——freeze 后 matrix-set 追加行 frozen_at
  恒空，latest 行取锚使 P3 置格会话 P5 门不可达（首战工具缝①）；改全表任意 frozen_at
  非空行，未冻结仍 FAIL（收紧不放水）。
"""
import os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from eval_range_recall import score   # noqa: E402  既有纯函数形（T16 前无归一化函数）
from ledger.schemas import TABLES     # noqa: E402
from tests.test_dryrun_p0p2 import (  # noqa: E402  夹具单源
    A64, TS, fresh_drydir, ledger)


def row(t, **kw):
    """schema 全字段行铸造（缺省空串）——纯 score() 面用，不落盘。"""
    mf = TABLES[t]
    return [str(kw.get(f, "")) for f in mf]


class TestNorm(unittest.TestCase):
    """①URL 归一+②别名统一（计划骨架名以实文件为准对齐——R-T16-1/2）。"""

    def test_syntax_normalization(self):
        import eval_range_recall as m
        self.assertEqual(
            m._norm_endpoint("HTTP://In.Example:80/a/?b=2&a=1"),
            "in.example/a?a=1&b=2",
            "小写 host+剥默认端口+query 排序+去尾斜杠"
            "（R-T16-1：计划字面 in.example/a/?a=1 与其实现片段两处不符——"
            "漏 &b=2 且 /a/ 未去尾斜杠；按片段口径 /a/→/a+query 排序）")
        self.assertEqual(m._norm_endpoint("svc-crm/api/x/"), "svc-crm/api/x",
                         "无 scheme 资产键形+去尾斜杠")
        self.assertEqual(m._norm_endpoint("HTTP://In.Example:8003/x"),
                         "in.example:8003/x", "非默认端口保留")

    def test_alias_unification(self):
        import eval_range_recall as m
        aliases = {"svc-crm": ["127.0.0.1:8003"]}
        self.assertEqual(m._canon_host("127.0.0.1:8003", aliases), "svc-crm",
                         "别名→canonical")
        self.assertEqual(m._canon_host("svc-crm", aliases), "svc-crm",
                         "canonical 自身幂等")
        self.assertEqual(m._canon_host("other.host:99", aliases), "other.host:99",
                         "未声明别名不猜映射（禁猜测式）")
        self.assertEqual(m._canon_host("x", None), "x", "host_aliases None 容错")

    def test_first_battle_mismatch_reproduced_then_fixed(self):
        """首战反例：GT 键 127.0.0.1:8003 形 × finding 资产 svc 键——别名声明后必 MATCH。"""
        gt = {"host_aliases": {"svc-crm": ["127.0.0.1:8003"]},
              "planted": [{"id": "sqli-01", "endpoint": "http://127.0.0.1:8003/api/x",
                           "marker": "TANYIN-MARKER-1"}]}
        rows = {
            "findings.tsv": [row("findings.tsv", id="FD-1", status="active",
                                 affected_asset_id="AST-1", evidence_ids="EV-1")],
            "assets.tsv": [row("assets.tsv", id="AST-1", value="svc-crm/api/x")],
            "creds.tsv": [], "intents.tsv": [], "facts.tsv": [],
            "E-index.tsv": [row("E-index.tsv", id="EV-1")],
            # 批次 9 精度门：命中前置=重放 VERIFIED 在案（G-52 纵深）
            "timeline.tsv": [row("timeline.tsv", ts=TS, actor="CLI", phase="P4",
                                 event="replay:EV-1:VERIFIED")],
        }
        cards = {"EV-1": {"expected": {"matchers": [
            {"type": "word", "words": ["TANYIN-MARKER-1"]}]}}}
        recall, missing = score(rows, cards, gt)
        self.assertEqual(missing, [],
                         "红现状：键失配 0 匹配（首战账面 0/20 根因）；missing=%r" % missing)
        self.assertEqual(recall, 1.0)


class TestRunbookGtKeySection(unittest.TestCase):
    """②GT 键口径显著位（RUNBOOK 首屏后第一节）+GT host_aliases 声明位在盘。"""

    def test_runbook_has_gt_key_section_upfront(self):
        p = os.path.join(ROOT, "tests", "range", "RUNBOOK.md")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        first_sec = text.find("\n## ")
        head, rest = text[:first_sec], text[first_sec:]
        self.assertIn("GT 键口径", rest[:800],
                      "GT 键口径节须为正文第一节（首屏后显著位）")
        self.assertIn("host_aliases", rest[:800], "口径节须点名 host_aliases 声明通道")
        self.assertTrue(head.strip(), "首屏（标题+定位块）仍在")

    def test_ground_truth_declares_host_aliases(self):
        import json
        p = os.path.join(ROOT, "tests", "range", "ground-truth.json")
        with open(p, encoding="utf-8") as f:
            gt = json.load(f)
        self.assertIn("host_aliases", gt, "GT 顶层 host_aliases 声明位（T16）")
        self.assertTrue(all(isinstance(v, list) and v for v in gt["host_aliases"].values()),
                        "别名映射形 canonical→[别名…]（非空清单）")


class TestTerminalGateFreezeAnchor(unittest.TestCase):
    """③terminal-gate 冻结锚=「freeze 时在场行」（首战工具缝①）。

    最小矩阵：--surfaces=s0+单类临时词表=1 格（gap 清零只置 1 格）；tier0 须 goals 行
    （add-goal 八问落账，argv 单源=test_dryrun_p0p2 STEPS P0 形）。"""

    VOCAB = "version: b7-t16-test\n- wstg-info\n"

    def _seed(self, td, name):
        gd = fresh_drydir(td, name)
        rc, out, err = ledger(gd, "add-goal", [
            "--target=dryrun.example", "--objective=T16 终门自检",
            "--auth-doc=auth/dry.pdf", "--auth-sha256=" + A64, "--signer=self",
            "--valid-from=2026-09-01", "--valid-until=2026-09-30",
            "--budget=2M;50000;40", "--model-tier=strong", "--guard-tier=T3",
            "--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        vf = os.path.join(td, name + "-vocab.md")
        with open(vf, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.VOCAB)
        return gd, vf

    def _init(self, gd, vf):
        rc, out, err = ledger(gd, "matrix-init",
                              ["--surfaces=s0", "--vocab=" + vf, "--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)

    def test_freeze_then_set_still_passes_terminal_gate(self):
        """红=工具缝①：freeze 后 matrix-set 追加行 frozen_at 恒空→latest 行取锚→P5 不可达。"""
        td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, td, True)
        gd, vf = self._seed(td, "G-tg")
        self._init(gd, vf)
        rc, out, err = ledger(gd, "matrix-freeze", ["--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        rc, out, err = ledger(gd, "matrix-set", [
            "--attack-surface=s0", "--vuln-class=wstg-info", "--state=x",
            "--reason=authz-diff: 置格修订", "--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        rc, out, err = ledger(gd, "ledger-terminal-gate", [])
        self.assertEqual(rc, 0,
                         "红现状：P3 置格后锚点断言 FAIL（P5 不可达）\n" + out + err)

    def test_never_frozen_still_fails(self):
        td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, td, True)
        gd, vf = self._seed(td, "G-tg2")
        self._init(gd, vf)
        rc, out, err = ledger(gd, "ledger-terminal-gate", [])
        self.assertEqual(rc, 1, "未冻结仍 FAIL（断言收紧不得放水）\n" + out + err)
        self.assertIn("锚点未冻结", out)


if __name__ == "__main__":
    unittest.main()

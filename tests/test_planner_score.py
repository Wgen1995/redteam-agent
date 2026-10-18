# -*- coding: utf-8 -*-
"""功能5/8·补件一：五因子优先级引擎 planner_score（TDD 红测试先行）。

设计源：docs/design/2026-10-20-priority-planner-design.md 补件一——
  score = 0.40·可达性(可达空格=1,不可达=0.3)
        + 0.20·凭据就绪(该面有 CRED 活链=1)
        + 0.15·线索新鲜(近期 fact 引用该资产=1,衰减)
        + 0.15·矩阵饥渴(该漏洞类×该面历史上零覆盖=1)
        + 0.10·历史收益(该类面过去命中过 findings=1)
纯机械可解释（禁 LLM 裁量排序）：因子值全部账本可查；权重可配文件（goal 目录
planner.json）；金样钉死同输入同序（排序=确定性函数）。

Ruling（本模块裁定，写测试即写契约）：
- R-SCO-1 可达性因子复用 graph_cmds.reachable_gap_cells 单源（起点=scope-root
  资产集，converge 同口径）——不重造 BFS。
- R-SCO-2 凭据就绪=该面上有 status=active 的 CRED 直接锚定（scope_asset→资产
  value==表面）。
- R-SCO-3 线索新鲜=fact.target==表面 的最新事实年龄衰减：≤1 天=1，1-7 天线性
  衰减到 0，>7 天=0（对同面多 fact 取最鲜）。
- R-SCO-4 矩阵饥渴=该 (表面×漏洞类) 键全历史行（含被覆盖旧态）零非空 state=1。
- R-SCO-5 历史收益=该漏洞类经 matrix.intent_id 归因命中过 findings（类级信号，
  任意表面）=1。
- R-SCO-6 排序键=(-score, attack_surface, vuln_class)——同分按行键字典序，
  同输入同序钉死。

跑法：python3 -m unittest tests.test_planner_score -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger.core import Session, write_tsv  # noqa: E402
from ledger import planner_score as PS  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-20T08:00:00Z"

# ---- 受控夹具：3 资产（1 可达子域/1 不可达子域）× 5 矩阵行（4 空格+2 历史覆盖）
ASSETS = [
    ["AST-0001", "root-domain", "shop.example", "", "1", "2", ""],
    ["AST-0002", "subdomain", "admin.shop.example", "", "1", "2", ""],
    ["AST-0003", "subdomain", "vpn.shop.example", "", "1", "2", ""],
]
EDGES = [
    ["E-0001", "parent", "AST-0001", "AST-0002", "planner-score-fixture", "2", ""],
]
MATRIX = [
    # 历史覆盖行在前，最新空格行在后（事件溯源 latest_by 取尾行）
    ["admin.shop.example", "inj.sql", "x", "历史覆盖", "INT-0010", "2",
     "2026-10-01T00:00:00Z", ""],
    ["admin.shop.example", "inj.sql", "", "", "", "2", "", ""],
    ["admin.shop.example", "wstg-inpv", "", "", "", "2", "", ""],
    ["admin.shop.example", "wstg-inj", "x", "类收益锚点", "INT-0009", "2",
     "2026-10-02T00:00:00Z", ""],
    ["vpn.shop.example", "wstg-inpv", "", "", "", "2", "", ""],
    ["vpn.shop.example", "wstg-inj", "", "", "", "2", "", ""],
]
CREDS = [
    ["CRED-0001", "password", "admin", "u1", "{{vault:cred-1}}", "AST-0002",
     "", "", "", "", "active", "", "", "2", "", ""],
    ["CRED-0002", "password", "vpn", "u2", "{{vault:cred-2}}", "AST-0003",
     "", "", "", "", "expired", "", "", "2", "", ""],
]
FACTS = [
    ["F-0001", "INT-0001", "info", "admin.shop.example", "新鲜线索", "0.9",
     "2", "2026-10-20T07:00:00Z"],
    ["F-0002", "INT-0001", "info", "vpn.shop.example", "陈旧线索", "0.9",
     "2", "2026-10-01T00:00:00Z"],
]
FINDINGS = [
    ["FD-0001", "INT-0009", "历史注入命中", "C3", "低", "ruled_out", "",
     "AST-0002+CWE-89", "CWE-89", "in_scope", "历史命中锚点", "step1",
     "AST-0002", "", "", "", "superseded", "2", "2026-10-02T00:00:00Z"],
]
INTENTS = [
    ["INT-0001", "侦察", "", "done", "web-blackbox", "recon", "entity",
     "0.8", "", "", "0.1", "", "", "", "", "2", ""],
    ["INT-0009", "历史注入", "", "done", "web-blackbox", "matrix-test",
     "entity", "", "", "", "0.1", "", "", "", "", "2", ""],
    # INT-0010=历史覆盖行锚点（无 findings——与 INT-0009 收益锚点隔离）
    ["INT-0010", "旧覆盖", "", "done", "web-blackbox", "matrix-test",
     "entity", "", "", "", "0.1", "", "", "", "", "2", ""],
]


def _mkgoal(tmp, name="G-t"):
    gd = shutil.copytree(FIX, os.path.join(tmp, name))
    for tname, rows in (("assets.tsv", ASSETS), ("edges.tsv", EDGES),
                        ("matrix.tsv", MATRIX), ("creds.tsv", CREDS),
                        ("facts.tsv", FACTS), ("findings.tsv", FINDINGS),
                        ("intents.tsv", INTENTS)):
        write_tsv(os.path.join(gd, tname), [list(r) for r in rows])
    return gd


class TestFiveFactors(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)
        self.rows = {(r["attack_surface"], r["vuln_class"]): r
                     for r in PS.rank_gaps(Session(self.gd), TS)}

    def _f(self, surface, vclass):
        return self.rows[(surface, vclass)]["factors"]

    def test_factor_values_reachable_fresh_cred_hungry_cell(self):
        f = self._f("admin.shop.example", "wstg-inpv")
        self.assertAlmostEqual(f["reachability"], 1.0)
        self.assertAlmostEqual(f["cred_ready"], 1.0)
        self.assertAlmostEqual(f["clue_fresh"], 1.0)
        self.assertAlmostEqual(f["matrix_hunger"], 1.0)
        self.assertAlmostEqual(f["historical_yield"], 0.0)

    def test_factor_values_historical_coverage_kills_hunger(self):
        f = self._f("admin.shop.example", "inj.sql")
        self.assertAlmostEqual(f["matrix_hunger"], 0.0, msg="历史覆盖行在案")

    def test_factor_values_unreachable_face(self):
        f = self._f("vpn.shop.example", "wstg-inpv")
        self.assertAlmostEqual(f["reachability"], 0.3)
        self.assertAlmostEqual(f["cred_ready"], 0.0, msg="expired CRED 不算活链")
        self.assertAlmostEqual(f["clue_fresh"], 0.0, msg="19 天前线索衰减归零")

    def test_factor_values_class_level_yield(self):
        f = self._f("vpn.shop.example", "wstg-inj")
        self.assertAlmostEqual(f["historical_yield"], 1.0,
                               msg="wstg-inj 类经 INT-0009 命中过 findings")


class TestGoldenOrder(unittest.TestCase):
    """金样钉死：同输入同序（排序=纯机械确定性函数，禁 LLM 裁量）。"""

    GOLDEN_ORDER = [
        ("admin.shop.example", "wstg-inpv"),
        ("admin.shop.example", "inj.sql"),
        ("vpn.shop.example", "wstg-inj"),
        ("vpn.shop.example", "wstg-inpv"),
    ]
    GOLDEN_SCORES = ["0.9000", "0.7500", "0.3700", "0.2700"]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def test_order_and_scores_pinned(self):
        rows = PS.rank_gaps(Session(self.gd), TS)
        self.assertEqual([(r["attack_surface"], r["vuln_class"]) for r in rows],
                         self.GOLDEN_ORDER)
        self.assertEqual(["%.4f" % r["score"] for r in rows], self.GOLDEN_SCORES)

    def test_render_rank_bytes_pinned(self):
        text = PS.render_rank(PS.rank_gaps(Session(self.gd), TS))
        self.assertEqual(text, (
            "#count=4\n"
            "admin.shop.example\twstg-inpv\t0.9000\t1.0000\t1.0000\t1.0000\t1.0000\t0.0000\n"
            "admin.shop.example\tinj.sql\t0.7500\t1.0000\t1.0000\t1.0000\t0.0000\t0.0000\n"
            "vpn.shop.example\twstg-inj\t0.3700\t0.3000\t0.0000\t0.0000\t1.0000\t1.0000\n"
            "vpn.shop.example\twstg-inpv\t0.2700\t0.3000\t0.0000\t0.0000\t1.0000\t0.0000\n"))

    def test_same_input_same_order(self):
        a = PS.rank_gaps(Session(self.gd), TS)
        b = PS.rank_gaps(Session(self.gd), TS)
        self.assertEqual(a, b, "同输入必须同序同值（实时=回放特例律）")


class TestFreshnessDecay(unittest.TestCase):
    def test_decay_curve(self):
        day = 86400.0
        self.assertEqual(PS.clue_freshness(0.0), 1.0)
        self.assertEqual(PS.clue_freshness(-5.0), 1.0)          # 未来钟=满鲜
        self.assertEqual(PS.clue_freshness(day), 1.0)
        self.assertAlmostEqual(PS.clue_freshness(day + 3 * day), 0.5)
        self.assertAlmostEqual(PS.clue_freshness(7 * day), 0.0)
        self.assertEqual(PS.clue_freshness(70 * day), 0.0)


class TestWeightsConfig(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def test_default_weights(self):
        self.assertEqual(PS.load_config(self.gd)["weights"], PS.DEFAULT_WEIGHTS)

    def test_weights_file_overrides_order(self):
        with open(os.path.join(self.gd, "planner.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"weights": {"reachability": 0.0, "cred_ready": 0.0,'
                    ' "clue_fresh": 0.0, "matrix_hunger": 0.5,'
                    ' "historical_yield": 0.5}}')
        cfg = PS.load_config(self.gd)
        rows = PS.rank_gaps(Session(self.gd), TS, weights=cfg["weights"])
        self.assertEqual([(r["attack_surface"], r["vuln_class"]) for r in rows], [
            ("vpn.shop.example", "wstg-inj"),      # hunger+yield=1.0
            ("admin.shop.example", "wstg-inpv"),   # hunger=0.5（同分按行键序）
            ("vpn.shop.example", "wstg-inpv"),     # hunger=0.5
            ("admin.shop.example", "inj.sql"),     # 0.0
        ])

    def test_bad_configs_fail_loud(self):
        def _w(text):
            with open(os.path.join(self.gd, "planner.json"), "w",
                      encoding="utf-8") as f:
                f.write(text)
            return PS.load_config(self.gd)
        self.assertRaises(ValueError, _w, '{"weights": {"reachability": -0.1}}')
        self.assertRaises(ValueError, _w, '{"weights": {"no_such_factor": 0.5}}')
        self.assertRaises(ValueError, _w,
                          '{"weights": {"reachability": 0.9, "cred_ready": 0.9}}')
        self.assertRaises(ValueError, _w, '{not json')
        self.assertRaises(ValueError, _w, '{"debounce_ms": 0}')


if __name__ == "__main__":
    unittest.main()

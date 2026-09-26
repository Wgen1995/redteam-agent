# -*- coding: utf-8 -*-
"""批次6 T12：tanyin-report 聚合器——13 表→聚合投影（确定性+终态 B 判据+ENV 缺表）。

夹具惯例=G-g1 复制（R-T10-2 共享夹具零触碰）；预算耗尽经 CLI budget-log 铸造
（不用手改表，计划 Step1 注记）；时间戳一律字面量 ISO8601。"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import report_agg  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")
TS = "2026-09-24T09:00:00Z"


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class TestAggregate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mint_finding(self, gd):
        """经 CLI 铸一条 active finding（引用夹具既有 EV/AST/INT，零手改表）。"""
        r = run(LEDGER, "add-finding", "--goal-dir", gd,
                "--intent-id=INT-g1-0002", "--title=聚合投影测试结论",
                "--confidence=C1", "--impact=高", "--exploitation-status=verified",
                "--scope-check=in_scope", "--description-brief=聚合器投影面测试",
                "--reproducible-steps=匿名 GET /admin/orders;响应含订单列表",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=EV-g1-0001",
                "--timestamp=2026-09-23T04:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return "FD-g1-0002"

    def test_projection_on_fixture(self):
        d = report_agg.aggregate(self.gd, TS)
        self.assertTrue(set(d) >= {"goal", "scope_summary", "findings", "matrix",
                                   "coverage", "budget_terminal", "tier_disclosure",
                                   "limits"})
        self.assertEqual(d["budget_terminal"], "normal")
        self.assertEqual(d["goal"]["id"], "G-g1-0001")
        ss = d["scope_summary"]
        self.assertEqual(ss["counts"]["include"], 2)
        self.assertEqual(ss["counts"]["exclude"] + ss["counts"]["oob"]
                         + ss["counts"]["account-grant"], 0)
        self.assertEqual(ss["amendment_heads"], ["S-g1-0001", "S-g1-0002"])
        self.assertEqual(len(d["matrix"]["filled"]), 2)
        self.assertEqual(d["matrix"]["empty"], [("web.api", "inj.sql")])
        self.assertEqual(d["matrix"]["gaps"], ["web.api/inj.sql"])
        self.assertEqual(d["coverage"]["gates_passed"], ["P0", "P1", "P2", "P3"])
        self.assertEqual(d["coverage"]["intents_open"], 1)
        self.assertEqual(d["coverage"]["intents_closed"], 1)
        self.assertEqual(d["tier_disclosure"]["guard_tier"], "T3")
        self.assertEqual(d["limits"]["empty_matrix_cells"], ["web.api/inj.sql"])

    def test_findings_projection_shape(self):
        fid = self._mint_finding(self.gd)
        d = report_agg.aggregate(self.gd, TS)
        rows = [f for f in d["findings"] if f["id"] == fid]
        self.assertEqual(len(rows), 1)
        f = rows[0]
        self.assertEqual(set(f), {"id", "title", "tech_sev", "biz_impact",
                                  "replay_state", "asset", "verified"})
        self.assertEqual(f["tech_sev"], "C1")
        self.assertEqual(f["biz_impact"], "高")
        self.assertEqual(f["replay_state"], "unverified")   # 无重放事件
        self.assertEqual(f["asset"], "AST-g1-0002")
        self.assertTrue(f["verified"])

    def test_deterministic(self):
        self.assertEqual(json.dumps(report_agg.aggregate(self.gd, TS), sort_keys=True),
                         json.dumps(report_agg.aggregate(self.gd, TS), sort_keys=True))

    def test_missing_table_env(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(EnvironmentError):
                report_agg.aggregate(d, TS)          # 13 表缺=ENV 2 非 FAIL

    def test_budget_exhausted_flag(self):
        r = run(LEDGER, "budget-log", "--goal-dir", self.gd, "--token-delta=3000000",
                "--requests-delta=0", "--hours-delta=0", "--scope=goal",
                "--timestamp=2026-09-23T05:00:00Z")   # CLI 铸造耗尽行（>2M 上限）
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(report_agg.aggregate(self.gd, TS)["budget_terminal"],
                         "exhausted")

    def test_cli_out_deterministic_bytes(self):
        out1 = os.path.join(self.tmp, "dd1.json")
        out2 = os.path.join(self.tmp, "dd2.json")
        for out in (out1, out2):
            r = run(REPORT, "aggregate", "--goal-dir", self.gd,
                    "--timestamp=" + TS, "--out=" + out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out1, "rb") as f1, open(out2, "rb") as f2:
            self.assertEqual(f1.read(), f2.read())    # 两跑逐字节一致

    def test_cli_missing_table_exit_two(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(REPORT, "aggregate", "--goal-dir", d, "--timestamp=" + TS)
            self.assertEqual(r.returncode, 2)         # 缺表=ENV 2 非 FAIL

    def test_cli_usage_exit_two(self):
        r = run(REPORT, "unknown-sub", "--goal-dir", self.gd)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

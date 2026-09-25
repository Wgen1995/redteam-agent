# -*- coding: utf-8 -*-
"""T2 静态指标接入测试：M12 双锚互证（裁决 E）+ runner 注册面 + M10 扫描面。"""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_dual_anchor  # noqa: E402

APPROVALS = [  # 列序=schemas TABLES["approvals.tsv"]
    ["AP-g1-0001", "h1", "knowledge-approved", "批次5-执行者", "2026-09-24T09:30:00Z", "STG-0001", "2"],
    ["AP-g1-0002", "h2", "approved", "人", "2026-09-24T09:31:00Z", "无关", "2"],
]
LOG = "# log\n2026-09-24T09:30:00Z|approve|STG-0001|approver=批次5-执行者\n"

class TestDualAnchor(unittest.TestCase):
    def test_matched(self):
        r = evals_dual_anchor.check(APPROVALS, LOG)
        self.assertEqual(r["matched"], [("STG-0001", "2026-09-24T09:30:00Z", "批次5-执行者")])
        self.assertEqual(r["missing_in_ledger"], [])
        self.assertEqual(r["missing_in_knowledge"], [])
    def test_orphan_ledger(self):
        rows = APPROVALS + [["AP-g1-0003", "h3", "knowledge-approved", "人", "2026-09-24T09:32:00Z", "STG-0009", "2"]]
        r = evals_dual_anchor.check(rows, LOG)
        self.assertEqual(r["missing_in_knowledge"], ["STG-0009"])
    def test_orphan_knowledge(self):
        r = evals_dual_anchor.check(APPROVALS, LOG + "2026-09-24T09:33:00Z|approve|STG-0002|approver=人\n")
        self.assertEqual(r["missing_in_ledger"], ["STG-0002"])
    def test_runner_registered(self):
        from ledger import evals_metrics
        self.assertIn("dual-anchor", evals_metrics._RUNNERS)

class TestStaticRunners(unittest.TestCase):
    def test_runners_registered(self):
        from ledger import evals_metrics
        for name in ("golden", "unittest", "report-scan", "dual-anchor"):
            self.assertIn(name, evals_metrics._RUNNERS)

class TestM10Scan(unittest.TestCase):
    """M10 面：泄漏样本必被拦截（token 赋值形态），脱敏文本零泄漏。"""
    LEAK = "# 草稿\ntoken=sk-live-abc123\n"
    CLEAN = "# 草稿\ntoken=<redacted>\n"  # 报告文本模式 {{vault:}} 残留亦判泄漏——用 <redacted>
    def test_leak_blocked(self):
        from ledger import special
        self.assertNotEqual(list(special.scan_text(self.LEAK)), [])
    def test_clean_zero_leak(self):
        from ledger import special
        self.assertEqual(list(special.scan_text(self.CLEAN)), [])

if __name__ == "__main__":
    unittest.main()

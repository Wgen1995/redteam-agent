# -*- coding: utf-8 -*-
"""v0.5b G3：干净重跑协议聚合面（同任务书同字典 N≥3——n=1 叙事→统计面）。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "rerun", os.path.join(HERE, "..", "scripts", "rerun.py"))
rerun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerun)


class TestRerunAggregate(unittest.TestCase):
    def test_parse_recall_line(self):
        self.assertEqual(rerun.parse_recall("recall=0.41 (23/56)"), (0.41, 23, 56))
        self.assertIsNone(rerun.parse_recall("no score here"))

    def test_parse_from_report_text(self):
        nl = chr(10)
        text = nl.join(["verify-chain: PASS", "recall=0.66 (37/56)", "FD 28", ""])
        self.assertEqual(rerun.parse_recall(text), (0.66, 37, 56))

    def test_aggregate(self):
        agg = rerun.aggregate([0.66, 0.62, 0.57])
        self.assertEqual(agg["n"], 3)
        self.assertAlmostEqual(agg["mean"], 0.6167, places=4)
        self.assertEqual(agg["min"], 0.57)
        self.assertEqual(agg["max"], 0.66)
        self.assertGreater(agg["std"], 0.03)

    def test_aggregate_empty(self):
        self.assertEqual(rerun.aggregate([])["n"], 0)

    def test_verdict_words_single_vs_multi(self):
        self.assertEqual(rerun.verdict(1), "单样本（n=1 无统计效力，RT-0023 教训）")
        self.assertIn("mean", rerun.verdict(3))


if __name__ == "__main__":
    unittest.main()

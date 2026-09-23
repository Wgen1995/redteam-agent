# -*- coding: utf-8 -*-
"""批次 3 评审收尾（审计#7）：run_golden 缺金样 --bless 显式建档门槛。

金样回归进 CI 后，"缺金样自动 INIT 落盘"副作用会把 CI 首跑/漏提交金样
误判为绿——门槛：无 --bless 且缺金样=FAIL 不落盘；--bless 才 INIT。
只测 gate_golden/parse_args 纯函数面，不跑 42 面全量（那是 run_golden 本体职责）。"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_golden   # noqa: E402 （同目录；discover -s tests 可导入）


class TestBlessGate(unittest.TestCase):
    def test_missing_golden_fails_without_bless(self):
        """缺金样+无 --bless：FAIL 且不落盘（防误建档）。"""
        with tempfile.TemporaryDirectory() as d:
            gp = os.path.join(d, "read-x.norm")
            fails, inits = [], []
            run_golden.gate_golden(gp, "PASS", "read-x", False, fails, inits, "输出漂移")
            self.assertEqual(fails, ["read-x(缺金样，须 --bless 显式建档)"])
            self.assertEqual(inits, [])
            self.assertFalse(os.path.exists(gp), "无 --bless 不得落盘金样")

    def test_missing_golden_inits_with_bless(self):
        """缺金样+--bless：INIT 落盘，内容=实测归一化输出。"""
        with tempfile.TemporaryDirectory() as d:
            gp = os.path.join(d, "write-x.state")
            fails, inits = [], []
            run_golden.gate_golden(gp, "OK\n== goals.tsv ==\na\tTS", "write-x",
                                   True, fails, inits, "状态漂移")
            self.assertEqual(fails, [])
            self.assertEqual(inits, ["write-x"])
            with open(gp, encoding="utf-8") as f:
                self.assertEqual(f.read(), "OK\n== goals.tsv ==\na\tTS")

    def test_present_golden_drift_fails(self):
        """在场金样漂移：FAIL（bless 与否都拦——--bless 只管缺档建档）。"""
        for bless in (False, True):
            with tempfile.TemporaryDirectory() as d:
                gp = os.path.join(d, "phases-x.norm")
                with open(gp, "w", encoding="utf-8", newline="\n") as f:
                    f.write("旧基线\n")
                fails, inits = [], []
                run_golden.gate_golden(gp, "新输出", "phases-x", bless, fails, inits, "输出漂移")
                self.assertEqual(fails, ["phases-x(输出漂移)"], "bless=%s 须 FAIL" % bless)
                self.assertEqual(inits, [])
                with open(gp, encoding="utf-8") as f:
                    self.assertEqual(f.read(), "旧基线\n", "漂移不得覆盖在档金样")

    def test_present_golden_match_passes(self):
        """在场金样一致：零 FAIL 零 INIT（空白容忍=原比对语义）。"""
        with tempfile.TemporaryDirectory() as d:
            gp = os.path.join(d, "read-y.norm")
            with open(gp, "w", encoding="utf-8", newline="\n") as f:
                f.write("PASS\n")
            fails, inits = [], []
            run_golden.gate_golden(gp, "PASS\n", "read-y", False, fails, inits, "输出漂移")
            self.assertEqual((fails, inits), ([], []))


class TestBlessFlagWiring(unittest.TestCase):
    def test_parse_args_flag(self):
        """--bless 旗标接线：缺省 False，显式传入 True。"""
        self.assertFalse(run_golden.parse_args([]).bless)
        self.assertTrue(run_golden.parse_args(["--bless"]).bless)


if __name__ == "__main__":
    unittest.main()

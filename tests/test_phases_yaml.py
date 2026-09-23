# -*- coding: utf-8 -*-
"""批次 3 T1/T2：phases.yaml 解析器与 schema 校验器测试。
范式：读仓库真实 phases/phases.yaml；篡改例写临时文件，不动本体。"""
import os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
import io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import phases_engine as pe

YAML_PATH = os.path.join(ROOT, "phases", "phases.yaml")
GATES9 = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")


class TestParse(unittest.TestCase):
    def test_loads_repo_yaml(self):
        data = pe.load_phases(YAML_PATH)
        self.assertEqual(str(data["format_version"]), "2")
        self.assertEqual(data["initial"], "P0")
        self.assertEqual([str(s) for s in data["states"]], list(GATES9))
        self.assertEqual(len(data["back_edges"]), 3)

    def test_constants_block(self):
        c = pe.load_phases(YAML_PATH)["constants"]
        self.assertEqual(len(c), 8)
        self.assertEqual(str(c["restart_context_threshold"]), "0.75")
        self.assertEqual(str(c["single_active_session"]), "true")

    def test_gate_asserts_shape(self):
        g = pe.load_phases(YAML_PATH)["gates"]
        self.assertEqual(set(g), set(GATES9))
        a0 = g["P0"]["exit"]["assert"]
        self.assertEqual(a0[0]["cmd"], "ledger-validate --tables goals,scope,creds")
        self.assertEqual(str(a0[0]["expect"]), "PASS")
        self.assertEqual(len(g["P4"]["exit"]["assert"]), 5)   # 21 条断言分布 P0=3/P1=3/P2=2/P3=1/P4=5/P5=3/P5.5=1/P6.0=1/P6=2
        ev = g["P3"]["events"]
        self.assertEqual(set(ev), {"asset-added", "cred-obtained", "scope-amended"})

    def test_folded_duty_is_string(self):
        duty = pe.load_phases(YAML_PATH)["gates"]["P0"]["duty"]
        self.assertIsInstance(duty, str) and self.assertIn("ledger-add-goal", duty)

    def test_syntax_error_fail_closed(self):
        with self.assertRaises(pe.PhasesSyntaxError):
            pe.parse_yaml("a: [unclosed")
        with self.assertRaises(pe.PhasesSyntaxError):
            pe.parse_yaml("no colon line")

    def test_comment_and_quote(self):
        d = pe.parse_yaml("k: \"v # not comment\"  # real comment\nj: [a, b]")
        self.assertEqual(d["k"], "v # not comment")
        self.assertEqual(d["j"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()

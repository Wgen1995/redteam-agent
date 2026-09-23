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

from ledger import registry

KNOWN = registry.all_commands() | {"tanyin-report", "tanyin-redact"}


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


class TestValidate(unittest.TestCase):
    def test_all_commands_face_41(self):
        """Interfaces 承诺单源=41 基名（裁决：四个原生带 ledger- 前缀的校验命令计入
        基名——无无前缀孪生；双前缀别名不进基名集）。"""
        face = registry.all_commands()
        self.assertEqual(len(face), 41)
        for native in ("ledger-scope-coverage", "ledger-tree-check",
                       "ledger-replay-summary", "ledger-terminal-gate"):
            self.assertIn(native, face)
        self.assertNotIn("ledger-add-goal", face)   # 双前缀别名剔出基名集

    def test_repo_yaml_valid(self):
        errs = pe.validate_phases(pe.load_phases(YAML_PATH), KNOWN)
        self.assertEqual(errs, [])

    def test_tampered_version(self):
        d = pe.load_phases(YAML_PATH); d["format_version"] = "3"
        self.assertTrue(any("format_version" in e for e in pe.validate_phases(d, KNOWN)))

    def test_tampered_constant(self):
        d = pe.load_phases(YAML_PATH); d["constants"]["restart_context_threshold"] = "0.9"
        self.assertTrue(any("restart_context_threshold" in e
                            for e in pe.validate_phases(d, KNOWN)))

    def test_unknown_assert_cmd(self):
        d = pe.load_phases(YAML_PATH)
        d["gates"]["P0"]["exit"]["assert"][0]["cmd"] = "ledger-no-such-cmd"
        self.assertTrue(any("不在命令面" in e for e in pe.validate_phases(d, KNOWN)))

    def test_missing_gate(self):
        d = pe.load_phases(YAML_PATH); del d["gates"]["P6.0"]
        self.assertTrue(any("P6.0" in e for e in pe.validate_phases(d, KNOWN)))

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def test_cli_validate_exit_codes(self):
        import subprocess
        cli = os.path.join(ROOT, "cli", "tanyin-phases")
        r = subprocess.run([sys.executable, cli, "validate"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0)
        self.assertIn("PASS", r.stdout)
        with open(YAML_PATH, encoding="utf-8") as f:
            bad_text = f.read().replace("format_version: 2", "format_version: 3", 1)
        bad = os.path.join(self.td.name, "bad.yaml")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(bad_text)
        r = subprocess.run([sys.executable, cli, "validate", "--phases=" + bad],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("format_version", r.stdout)


if __name__ == "__main__":
    unittest.main()

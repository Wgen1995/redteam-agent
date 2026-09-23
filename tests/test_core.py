# -*- coding: utf-8 -*-
"""批次 1 地基测试（T1+T2）——python3 -m unittest tests.test_core"""
import os, sys, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core
import unittest

FIX = os.path.join(HERE, "fixtures", "G-g1")

class T1Core(unittest.TestCase):
    def test_escape_roundtrip(self):
        s = "a" + chr(9) + "b" + chr(13) + "c" + chr(10) + "d;e" + chr(92) + "f"
        self.assertEqual(core.unesc(core.esc(s)), s)
        self.assertNotIn(chr(9), core.esc(s))

    def test_schemas_frozen(self):
        self.assertEqual(len(core.TABLES), 13)
        self.assertEqual(sum(len(v) for v in core.TABLES.values()), 147)
        self.assertIn("schema_version", core.TABLES["timeline.tsv"])
        self.assertIn("frozen_at", core.TABLES["matrix.tsv"])
        self.assertIn("material", core.TABLES["creds.tsv"])

    def test_next_id_mints(self):
        rows = [["INT-g1-0002"], ["INT-g1-0009"]]
        self.assertEqual(core.next_id(rows, "INT", "g1"), "INT-g1-0010")
        self.assertEqual(core.next_id([], "INT", "g1"), "INT-g1-0001")

class T2Fixture(unittest.TestCase):
    def test_fixture_validate_clean(self):
        errs = core.Session(FIX).validate()
        self.assertEqual(errs, [])

    def test_chain_tamper_detected(self):
        s = core.Session(FIX)
        s.data["timeline.tsv"][1][3] = s.data["timeline.tsv"][1][3] + "X"
        ok, bad = s.verify_chain()
        self.assertFalse(ok)
        self.assertEqual(bad, 2)

    def test_cli_validate_exit0(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "..", "cli", "tanyin-ledger"),
                            "validate", "--goal-dir", FIX], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cli_tamper_exit1(self):
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(FIX, os.path.join(td, "G-g1"))
            p = os.path.join(td, "G-g1", "timeline.tsv")
            lines = open(p, encoding="utf-8").read().splitlines()
            lines[1] = lines[1].replace("add-scope", "add-scopX")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(chr(10).join(lines) + chr(10))
            r = subprocess.run([sys.executable, os.path.join(HERE, "..", "cli", "tanyin-ledger"),
                                "verify-chain", "--goal-dir", os.path.join(td, "G-g1")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 1)

if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""matrix-init（特殊 1/1）测试——P1 门基线铸造。"""
import os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")

def run_cmd(args, goal_dir):
    # 入口约定：cmd --goal-dir <dir> 其余参数
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", goal_dir] + args[1:],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

class MatrixInit(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.g = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        open(os.path.join(self.g, "matrix.tsv"), "w", encoding="utf-8").write("")

    def tearDown(self):
        self.td.cleanup()

    def test_happy_init(self):
        r = run_cmd(["matrix-init", "--timestamp=2026-09-23T06:00:00Z"], self.g)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        sys.path.insert(0, os.path.join(HERE, "..", "cli"))
        from ledger import core
        s = core.Session(self.g)
        rows = s.rows("matrix.tsv")
        self.assertEqual(len(rows), 2 * 12)
        ok, bad = s.verify_chain()
        self.assertTrue(ok)
        v = run_cmd(["validate", "--goal-dir", self.g], self.g)
        self.assertEqual(v.returncode, 0)

    def test_reject_already_init(self):
        r1 = run_cmd(["matrix-init", "--timestamp=2026-09-23T06:00:00Z"], self.g)
        self.assertEqual(r1.returncode, 0)
        before = open(os.path.join(self.g, "matrix.tsv"), "rb").read()
        r2 = run_cmd(["matrix-init", "--timestamp=2026-09-23T06:05:00Z"], self.g)
        self.assertEqual(r2.returncode, 1)
        self.assertIn("REJECT", r2.stdout)
        after = open(os.path.join(self.g, "matrix.tsv"), "rb").read()
        self.assertEqual(before, after)

    def test_missing_timestamp_rejected(self):
        r = run_cmd(["matrix-init"], self.g)
        self.assertEqual(r.returncode, 2)

if __name__ == "__main__":
    unittest.main()
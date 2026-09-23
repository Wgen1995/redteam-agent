# -*- coding: utf-8 -*-
"""tanyin-guard（批次 2 T1/T2）测试。"""
import os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "..", "cli", "tanyin-guard")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable

def g(gd, *args):
    return subprocess.run([PY, GUARD, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

# 跨平台命令载体：py -c pass（/bin/echo、/bin/sh 仅 POSIX，Windows 上 FileNotFoundError）
NOOP = [PY, "-c", "pass"]
ECHO_SECRET = [PY, "-c", "import os,sys; sys.stdout.write('s=' + os.environ.get('TY_CRED_SECRET', ''))"]

class GuardExec(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def test_in_scope_passes_with_ticket(self):
        before = len(open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").readlines())
        r = g(self.gd, "exec", "--", *(NOOP + ["ping api.shop.example"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").readlines()
        self.assertEqual(len(after), before + 1)
        self.assertIn("request-ticket", after[-1])
    def test_out_of_scope_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["touch evil.example"]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("界外目标", r.stdout)
    def test_deny_list_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["shutdown"]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("deny-list", r.stdout)

class GuardVault(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        os.makedirs(os.path.join(self.gd, "vault"), exist_ok=True)
        with open(os.path.join(self.gd, "vault", ".key"), "w", encoding="utf-8", newline="\n") as f:
            f.write("k1")
    def tearDown(self):
        self.td.cleanup()
    def test_deploy_inject_tokenize(self):
        r = g(self.gd, "deploy-vault", "--cred=7", "--username=admin", "--secret=TopSecret-9")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(self.gd, "vault", "cred-7.enc"), encoding="utf-8") as f:
            enc = f.read()
        self.assertNotIn("TopSecret", enc)
        r2 = g(self.gd, "inject", "--cred=7", "--timestamp=2026-09-23T08:00:00Z", "--", *(ECHO_SECRET))
        self.assertEqual(r2.returncode, 0)
        self.assertIn("s={{vault:cred-7}}", r2.stdout)
        self.assertNotIn("TopSecret", r2.stdout)
    def test_missing_entry_rejected(self):
        r = g(self.gd, "inject", "--cred=99", "--", *(NOOP + ["x"]))
        self.assertEqual(r.returncode, 1)

if __name__ == "__main__":
    unittest.main()

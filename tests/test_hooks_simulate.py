# -*- coding: utf-8 -*-
"""hooks/simulate.py（批次 2 T7·Tier 2 宿主 hook 模拟器）测试。

SECW-3 差距清单：simulate 只做 deny-list 匹配、无 scope 界外解析——
Tier 2 语义（hooks/*.md 三模板同源声明）= deny-list 比对 + scope 解析，
阻断=非零退出码 + timeline hook-block 事件；fail-closed。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "hooks", "simulate.py")
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TAB = chr(9)


def sim(gd, host, *cmd):
    return subprocess.run([PY, SIM, "--goal-dir", gd, "--host", host, "--"] + list(cmd),
                          capture_output=True, text=True)


def ledger(gd, cmd):
    return subprocess.run([PY, LEDGER, cmd, "--goal-dir", gd], capture_output=True, text=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def tearDown(self):
        self.td.cleanup()

    def timeline(self):
        p = os.path.join(self.gd, "timeline.tsv")
        return [l.split(TAB) for l in open(p).read().splitlines() if l.strip()]


class SimScope(Base):
    def test_out_of_scope_domain_blocked(self):
        r = sim(self.gd, "dsh", "curl", "http://canary.abcd1234.tanyin-test/")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stdout)
        self.assertIn("canary.abcd1234.tanyin-test", r.stdout)
        self.assertTrue(self.timeline()[-1][3].startswith("hook-block"), self.timeline()[-1][3])
        self.assertIn("hook:dsh", self.timeline()[-1][1])
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_out_of_scope_ip_blocked(self):
        r = sim(self.gd, "opencode", "curl", "http://192.0.2.9/")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stdout)
        self.assertIn("192.0.2.9", r.stdout)
        self.assertTrue(self.timeline()[-1][3].startswith("hook-block"))

    def test_in_scope_domain_passes(self):
        r = sim(self.gd, "dsh", "curl", "http://api.shop.example/")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS hook(dsh)", r.stdout)

    def test_in_scope_cidr_passes(self):
        r = sim(self.gd, "codex", "curl", "http://10.10.3.4/")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS hook(codex)", r.stdout)

    def test_no_host_arg_passes(self):
        r = sim(self.gd, "dsh", "/bin/echo", "hello")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS hook(dsh)", r.stdout)

    def test_fail_closed_missing_scope_table(self):
        os.remove(os.path.join(self.gd, "scope.tsv"))
        r = sim(self.gd, "dsh", "curl", "http://api.shop.example/")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stdout)


class SimDenyList(Base):
    def test_deny_list_still_blocked(self):
        r = sim(self.gd, "dsh", "/bin/echo", "shutdown")
        self.assertEqual(r.returncode, 1)
        self.assertIn("BLOCKED", r.stdout)
        self.assertIn("deny", r.stdout)
        self.assertTrue(self.timeline()[-1][3].startswith("hook-block"))


class SimUsage(unittest.TestCase):
    def test_bad_usage_rc2(self):
        r = subprocess.run([PY, SIM, "--goal-dir", "x"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_bad_host_rc2(self):
        r = subprocess.run([PY, SIM, "--goal-dir", ".", "--host", "nope", "--", "ls"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

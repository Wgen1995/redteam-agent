# -*- coding: utf-8 -*-
"""tanyin-egress（批次 2 T3）测试。"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
EG = os.path.join(HERE, "..", "cli", "tanyin-egress")
GUARD = os.path.join(HERE, "..", "cli", "tanyin-guard")
CANARY = os.path.join(HERE, "..", "cli", "tanyin-canary")
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable

def eg(gd, *a):
    return subprocess.run([PY, EG, a[0], "--goal-dir", gd] + list(a[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

def guard(gd, *a):
    return subprocess.run([PY, GUARD, a[0], "--goal-dir", gd] + list(a[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

class Egress(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def test_compile_determinism(self):
        self.assertEqual(eg(self.gd, "compile").returncode, 0)
        a = open(os.path.join(self.gd, "egress.acl"), "rb").read()
        eg(self.gd, "compile")
        self.assertEqual(a, open(os.path.join(self.gd, "egress.acl"), "rb").read())
    def test_snapshot_sections(self):
        eg(self.gd, "compile")
        with open(os.path.join(self.gd, "egress.acl"), encoding="utf-8") as f:
            t = f.read()
        for want in ("default deny", "allow *.shop.example", "allow 10.10.0.0/16",
                     "[dns-pinning]", "pin *.shop.example", "[oob]", "[infra]", "allow-infra pypi.org"):
            self.assertIn(want, t)
    def test_verify_drift_after_scope_amend(self):
        eg(self.gd, "compile")
        self.assertEqual(eg(self.gd, "verify").returncode, 0)
        r = subprocess.run([PY, LEDGER, "add-scope", "--goal-dir", self.gd,
                            "--kind=include", "--matcher=newhost.example",
                            "--timestamp=2026-09-23T09:00:00Z"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        v = eg(self.gd, "verify")
        self.assertEqual(v.returncode, 1)
        self.assertIn("漂移", v.stdout)
        self.assertIn("recompile", v.stdout)
    def test_canary_tier3_real_acl(self):
        eg(self.gd, "compile")
        subprocess.run([PY, CANARY, "deploy", "--goal-dir", self.gd, "--seed=s1"], capture_output=True)
        r = subprocess.run([PY, CANARY, "probe", "--goal-dir", self.gd, "--tier=3"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        j = json.loads(r.stdout)
        self.assertEqual((j["status"], j["blocked"], j["total"]), ("pass", 5, 5))
        with open(os.path.join(self.gd, "canary", "targets.tsv"), encoding="utf-8") as f:
            decoy = [l.split(chr(9))[1] for l in f][0]
        with open(os.path.join(self.gd, "egress.acl"), "a", encoding="utf-8", newline="") as f:
            f.write("allow " + decoy + chr(10))
        r2 = subprocess.run([PY, CANARY, "probe", "--goal-dir", self.gd, "--tier=3"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r2.returncode, 1)
        self.assertEqual(json.loads(r2.stdout)["status"], "fail")
    def test_single_source_exclude_denies_and_guard_rejects(self):
        """洞 1：账本=执法策略单一事实源——同一 scope.tsv 驱动 Tier3 deny 行与 Tier1 REJECT，
        消除两层解释矛盾（红：当前 Tier1 半边放行被排除主机）。"""
        r = subprocess.run([PY, LEDGER, "add-scope", "--goal-dir", self.gd,
                            "--kind=exclude", "--matcher=prod.shop.example",
                            "--timestamp=2026-09-23T09:40:00Z"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(eg(self.gd, "compile").returncode, 0)
        acl = open(os.path.join(self.gd, "egress.acl"), encoding="utf-8").read()
        self.assertIn("deny prod.shop.example", acl)
        g1 = guard(self.gd, "exec", "--", *([PY, "-c", "pass", "ping", "prod.shop.example"]))
        self.assertEqual(g1.returncode, 1, g1.stdout + g1.stderr)
        self.assertIn("exclude", g1.stdout.lower())
        g2 = guard(self.gd, "exec", "--", *([PY, "-c", "pass", "ping", "api.shop.example"]))
        self.assertEqual(g2.returncode, 0, g2.stdout + g2.stderr)

    def test_oob_row_compiles_allow_oob(self):
        r = subprocess.run([PY, LEDGER, "add-scope", "--goal-dir", self.gd,
                            "--kind=oob", "--matcher=cb.example",
                            "--timestamp=2026-09-23T09:45:00Z"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(eg(self.gd, "compile").returncode, 0)
        acl = open(os.path.join(self.gd, "egress.acl"), encoding="utf-8").read()
        self.assertIn("allow-oob cb.example", acl)

    def test_dryrun(self):
        r = eg(self.gd, "dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("deny-by-default", r.stdout)

if __name__ == "__main__":
    unittest.main()

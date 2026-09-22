# -*- coding: utf-8 -*-
"""tanyin-egress（批次 2 T3）测试。"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
EG = os.path.join(HERE, "..", "cli", "tanyin-egress")
CANARY = os.path.join(HERE, "..", "cli", "tanyin-canary")
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable

def eg(gd, *a):
    return subprocess.run([PY, EG, a[0], "--goal-dir", gd] + list(a[1:]), capture_output=True, text=True)

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
        t = open(os.path.join(self.gd, "egress.acl")).read()
        for want in ("default deny", "allow *.shop.example", "allow 10.10.0.0/16",
                     "[dns-pinning]", "pin *.shop.example", "[oob]", "[infra]", "allow-infra pypi.org"):
            self.assertIn(want, t)
    def test_verify_drift_after_scope_amend(self):
        eg(self.gd, "compile")
        self.assertEqual(eg(self.gd, "verify").returncode, 0)
        r = subprocess.run([PY, LEDGER, "add-scope", "--goal-dir", self.gd,
                            "--kind=include", "--matcher=newhost.example",
                            "--timestamp=2026-09-23T09:00:00Z"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        v = eg(self.gd, "verify")
        self.assertEqual(v.returncode, 1)
        self.assertIn("漂移", v.stdout)
        self.assertIn("recompile", v.stdout)
    def test_canary_tier3_real_acl(self):
        eg(self.gd, "compile")
        subprocess.run([PY, CANARY, "deploy", "--goal-dir", self.gd, "--seed=s1"], capture_output=True)
        r = subprocess.run([PY, CANARY, "probe", "--goal-dir", self.gd, "--tier=3"], capture_output=True, text=True)
        j = json.loads(r.stdout)
        self.assertEqual((j["status"], j["blocked"], j["total"]), ("pass", 5, 5))
        decoy = [l.split(chr(9))[1] for l in open(os.path.join(self.gd, "canary", "targets.tsv"))][0]
        with open(os.path.join(self.gd, "egress.acl"), "a") as f:
            f.write("allow " + decoy + chr(10))
        r2 = subprocess.run([PY, CANARY, "probe", "--goal-dir", self.gd, "--tier=3"], capture_output=True, text=True)
        self.assertEqual(r2.returncode, 1)
        self.assertEqual(json.loads(r2.stdout)["status"], "fail")
    def test_dryrun(self):
        r = eg(self.gd, "dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("deny-by-default", r.stdout)

if __name__ == "__main__":
    unittest.main()

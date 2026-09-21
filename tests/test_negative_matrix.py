# -*- coding: utf-8 -*-
"""负向矩阵交叉复核（批次 1 T14）——写前拒收后账本字节不变（独立于 W/Q 组测试的第二重验证）。"""
import os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "--timestamp=2026-09-23T07:00:00Z"

CASES = [
    ("add-fact", ["--intent-id=INT-g1-9999", "--kind=info", "--target=x.example", "--detail=d", "--confidence=0.5", TS]),
    ("add-intent", ["--title=坏意图", "--engine=web-blackbox", "--kind=recon", "--origin=bad", "--budget-share=1;1;1", TS]),
    ("matrix-set", ["--attack-surface=web.none", "--vuln-class=inj.sql", "--state=x", "--reason=r", TS]),
]

class NegativeMatrix(unittest.TestCase):
    def test_rejects_leave_ledger_untouched(self):
        for name, args in CASES:
            with tempfile.TemporaryDirectory() as td:
                gd = shutil.copytree(FIX, os.path.join(td, "G-g1"))
                snap = {f: open(os.path.join(gd, f), "rb").read() for f in os.listdir(gd)}
                r = subprocess.run([sys.executable, CLI, name, "--goal-dir", gd] + args,
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, name + " 应 exit 1: " + r.stdout)
                self.assertIn("REJECT", r.stdout + r.stderr, name)
                after = {f: open(os.path.join(gd, f), "rb").read() for f in os.listdir(gd)}
                self.assertEqual(snap, after, name + " 拒收后账本必须字节不变")

if __name__ == "__main__":
    unittest.main()
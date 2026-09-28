# -*- coding: utf-8 -*-
"""批次 8 T8（G-43）：Tier2 hooks/simulate.py 接线单源——字面 deny_hit(joined) 升
deny_forms 归一比对（「Tier1/Tier2 同源执法」承诺的另一半）。
红=rm -r -f / 经 hook 放行（rc=0）；绿=BLOCKED deny。
"""
import os, subprocess, sys, tempfile, unittest, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SIM = os.path.join(ROOT, "hooks", "simulate.py")
FIX = os.path.join(HERE, "fixtures", "G-g1")


class TestTier2SingleSource(unittest.TestCase):
    def _run(self, gd, cmd):
        return subprocess.run([sys.executable, SIM, "--goal-dir", gd, "--host", "dsh",
                               "--"] + cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def test_normalized_deny_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            gd = os.path.join(d, "G")
            shutil.copytree(FIX, gd)
            r = self._run(gd, ["rm", "-r", "-f", "/"])
            self.assertEqual(r.returncode, 1, "归一形 rm -fr / 必须 BLOCKED: %s %s" % (r.stdout, r.stderr))
            self.assertIn("deny", r.stdout)
            tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
            self.assertIn("hook-block", tl)

    def test_benign_passes(self):
        with tempfile.TemporaryDirectory() as d:
            gd = os.path.join(d, "G")
            shutil.copytree(FIX, gd)
            r = self._run(gd, ["ls", "-la", "."])
            self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""批次 8 T5（M12）：tanyin-replay 链式多请求——EV 有序序列执行（单报文扩展）。
红=--chain 不存在（落 usage）；绿=逐步执行+步标记+env-diff 中止（有序性证据：
step2 不被执行）。
"""
import json, os, subprocess, sys, tempfile, unittest, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
FIX = os.path.join(HERE, "fixtures", "G-g1")


class TestReplayChain(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = os.path.join(self.td.name, "G")
        shutil.copytree(FIX, self.gd)

    def _run(self, *args):
        return subprocess.run([sys.executable, REPLAY, "replay", "--goal-dir", self.gd] + list(args),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_chain_runs_ordered_and_aborts_on_env_diff(self):
        r = self._run("--chain=EV-g1-0001,EV-g1-0001", "--timeout=1")
        self.assertNotEqual(r.returncode, 2, "链式面必须存在（非 usage）: %s" % r.stderr)
        tl = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("replay-chain step=1/2 id=EV-g1-0001", tl)
        self.assertNotIn("step=2/2", tl, "首步未闭合（env-diff/REJECT）后不得执行后续步（fail-closed）")
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertTrue(out.get("aborted"))
        self.assertEqual(out["chain"][0]["rc"] != 0 or out["chain"][0]["verdict"] == "env-diff", True)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""P0 诚实性加固批（会诊③·审计缺口①）：链头锚定 anchor 命令。

无密钥哈希链防意外不防故意——改 TSV+重算全链全绿。anchor 把账本面
git commit（消息带行数+链头），可选 push remote：无声改账从此须重写
已推送历史。门过自动锚=TANYIN_ANCHOR_AUTO=1。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"


def run(gd, *args, **kw):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


class TestAnchor(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_anchor_commits_with_head(self):
        r = run(self.d, "anchor", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("anchor commit=", r.stdout)
        self.assertIn("rows=", r.stdout)
        log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=self.d,
                             capture_output=True, text=True).stdout
        self.assertIn("anchor rows=", log)
        self.assertIn("head=", log)

    def test_anchor_idempotent_and_new_rows_new_commit(self):
        run(self.d, "anchor", "--timestamp=" + TS)
        c1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d,
                            capture_output=True, text=True).stdout
        r = run(self.d, "append-timeline", "--actor=CLI", "--phase=P4",
                "--event=checkpoint unit", "--revert-cmd=none",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        run(self.d, "anchor", "--timestamp=" + TS)
        c2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d,
                            capture_output=True, text=True).stdout
        self.assertNotEqual(c1, c2, "新行未产生新锚")

    def test_anchor_does_not_break_chain(self):
        run(self.d, "anchor", "--timestamp=" + TS)
        r = run(self.d, "verify-chain")
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()

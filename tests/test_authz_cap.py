# -*- coding: utf-8 -*-
"""批次5 T5：AUTHZ_DIFF_PAIR_CAP=24 代码常量+add-intent 同端点计数写前拒收（R6/G-20）。

钉子四面：模块常量锚定 24；同端点（asset+kind 计数键，经 dedup_key 前缀）第 cap+1
条 REJECT（消息含计数与 cap 值）；--cap 覆盖通道（evals 重放，G-3 同型）+1-1000 校验；
per-endpoint 语义（他端点不计数）。
R-T5-1：铸造通道=循环调 add-intent（计划原文形态）；标题逐一差异化避开 dedup_key
判重（(asset)+"+authz-diff+"+title 三元组键）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
TS = "2026-09-24T08:00:00Z"


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestAuthzCap(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_constant_value_anchored(self):
        from ledger import write_cmds
        self.assertEqual(write_cmds.AUTHZ_DIFF_PAIR_CAP, 24)

    def _mint(self, title, asset="AST-g1-0002", extra=()):
        return run(self.d, "add-intent", "--title=" + title, "--engine=web-blackbox",
                   "--kind=authz-diff", "--origin=entity", "--cred=CRED-g1-0001",
                   "--actions=read", "--asset=" + asset, "--budget-share=1;1;1",
                   "--timestamp=" + TS, *extra)

    def test_25th_same_endpoint_rejected(self):
        for i in range(24):
            r = self._mint("对%02d" % i)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self._mint("第25条")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        self.assertIn("AUTHZ_DIFF_PAIR_CAP", r.stderr)
        self.assertIn("count=24", r.stderr)
        self.assertIn("cap=24", r.stderr)

    def test_cap_override_channel(self):
        for i in range(3):
            r = self._mint("覆盖对%02d" % i)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self._mint("第4条", extra=("--cap=3",))
        self.assertEqual(r.returncode, 1)
        self.assertIn("count=3", r.stderr)
        self.assertIn("cap=3", r.stderr)
        r = self._mint("第4条", extra=("--cap=4",))   # 覆盖通道放行（evals 可重放）
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cap_validation(self):
        r = self._mint("坏cap", extra=("--cap=0",))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        r = self._mint("坏cap2", extra=("--cap=abc",))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        r = self._mint("坏cap3", extra=("--cap=1001",))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    def test_other_endpoint_not_counted(self):
        for i in range(3):
            r = self._mint("端点A对%02d" % i)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self._mint("端点B首条", asset="AST-g1-0001", extra=("--cap=3",))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)   # 他端点不计数（per-endpoint）


if __name__ == "__main__":
    unittest.main()

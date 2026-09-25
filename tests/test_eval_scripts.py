# -*- coding: utf-8 -*-
"""批次5 T18：出口 eval 两件自检——双知识库抽查（§9.4 四判据机检化）+反向验证
零命中（脏/净双向断言）。测试本身防「永远 FAIL/永远 PASS」两种坏实现：对种子库
必须绿（exit 0）、对脏夹具必须红（exit 1 且点名无跨客户残留判据）、双向断言
必须双向成立。eval 脚本内部在临时副本上执行探针（种子库/夹具零写热）。"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SEED = os.path.join(ROOT, "knowledge")
FIX = os.path.join(HERE, "fixtures", "G-g1")
DIRTY = os.path.join(HERE, "fixtures", "knowledge-dirty")


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class TestEvalScripts(unittest.TestCase):
    def test_spotcheck_green_on_seed(self):
        seed_log = os.path.join(SEED, "log.md")
        with open(seed_log, "rb") as f:
            before = f.read()
        r = run(os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                "--knowledge-dir", SEED, "--today", "2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("spotcheck PASS", r.stdout)
        with open(seed_log, "rb") as f:
            self.assertEqual(f.read(), before,
                             "spotcheck 写热种子库（须副本执行）")

    def test_spotcheck_detects_dirty_fixture(self):
        r = run(os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                "--knowledge-dir", DIRTY, "--today", "2026-09-24")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("spotcheck FAIL", r.stdout)
        self.assertIn("无跨客户残留", r.stdout, "脏夹具须点名跨客户残留判据")

    def test_spotcheck_external_cve_criterion_green(self):
        r = run(os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                "--knowledge-dir", SEED, "--origin", "external",
                "--today", "2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("spotcheck PASS", r.stdout)

    def test_spotcheck_env_error_exit_two(self):
        r = run(os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                "--knowledge-dir", os.path.join(HERE, "fixtures", "no-such-dir"),
                "--today", "2026-09-24")
        self.assertEqual(r.returncode, 2)
        self.assertIn("环境问题", r.stderr)

    def test_reverse_verify_eval_both_ways(self):
        r = run(os.path.join(HERE, "eval_reverse_verify.py"), "--goal-dir", FIX)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("dirty=detected", r.stdout)
        self.assertIn("clean=zero-hits", r.stdout)


if __name__ == "__main__":
    unittest.main()

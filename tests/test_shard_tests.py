# -*- coding: utf-8 -*-
"""W2·CI 护栏（e7a6d5f1）——测试分片并行: scripts/shard_tests.py 单测。

分片律（确定性优先）：
- 划分基元 = 测试模块（tests/test*.py 文件，unittest 发现 pattern 同源）——
  单模块不跨片（模块内用例共享夹具状态）；
- 排序后轮转派片（index % n）——同仓状态下片集恒等（可重跑/可比对），
  片大小差 ≤1（计数均衡；时长均衡属后续按历史计时加权，v1 不做）；
- 非测试件（webui_login.py 夹具/run_golden.py/eval_*.py）不入片。
"""
import os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "shard_tests.py")
PY = sys.executable


def run_shard(spec, mode="--list"):
    return subprocess.run([PY, SCRIPT, mode, "--shard=" + spec],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def shard_modules(spec):
    r = run_shard(spec)
    assert r.returncode == 0, r.stdout + r.stderr
    return [m for m in r.stdout.split() if m]


class ShardPartition(unittest.TestCase):
    def test_union_covers_all_disjoint(self):
        """并集=全部测试模块，两两不相交（分片不丢不重）。"""
        all_mods = shard_modules("1/1")
        self.assertGreater(len(all_mods), 50, "须以真实测试面为基线")
        union = []
        for i in (1, 2, 3, 4):
            part = shard_modules("%d/4" % i)
            union += part
        self.assertEqual(sorted(union), sorted(all_mods))
        self.assertEqual(len(union), len(set(union)), "片间不得重复")

    def test_module_atomic_no_split(self):
        """单模块只属一片（模块名不出现于两片）。"""
        seen = {}
        for i in (1, 2, 3):
            for m in shard_modules("%d/3" % i):
                self.assertNotIn(m, seen, m + " 跨片")
                seen[m] = i

    def test_helpers_excluded(self):
        """非 test*.py 件（夹具/金样/评估器）不入片。"""
        mods = shard_modules("1/1")
        for name in ("tests.webui_login", "tests.run_golden", "tests.normalize",
                     "tests.eval_range_recall", "tests.make_fixtures"):
            self.assertNotIn(name, mods)


class ShardDeterminism(unittest.TestCase):
    def test_repeat_invocation_identical(self):
        """同片两次调用输出恒等（CI 重跑可比对）。"""
        a = run_shard("2/5").stdout
        b = run_shard("2/5").stdout
        self.assertEqual(a, b)

    def test_balance_within_one(self):
        """片大小差 ≤1（计数轮转均衡）。"""
        sizes = [len(shard_modules("%d/4" % i)) for i in (1, 2, 3, 4)]
        self.assertLessEqual(max(sizes) - min(sizes), 1, sizes)


class ShardUsageErrors(unittest.TestCase):
    def test_zero_shard_rejected(self):
        self.assertEqual(run_shard("0/4").returncode, 2)

    def test_over_range_rejected(self):
        self.assertEqual(run_shard("5/4").returncode, 2)

    def test_malformed_spec_rejected(self):
        for bad in ("a/b", "2", "2/x", "/4", "3/0"):
            self.assertEqual(run_shard(bad).returncode, 2, bad)


class ShardRunMode(unittest.TestCase):
    def test_run_empty_shard_exit_zero(self):
        """空片（片号合法但片号>模块数）--run 直接 rc0 不进 unittest。"""
        r = run_shard("999/1000", mode="--run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("empty", (r.stdout + r.stderr).lower())

    def test_run_propagates_unittest_exit_code(self):
        """--run 透传 unittest 退出码（真门禁语义；--only 用他件防自递归）。"""
        r = subprocess.run(
            [PY, SCRIPT, "--run", "--shard=1/1", "--only=tests.test_ui_copy"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Ran ", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()

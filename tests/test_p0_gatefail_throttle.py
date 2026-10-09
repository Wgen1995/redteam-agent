# -*- coding: utf-8 -*-
"""P0 诚实性加固批（会诊/RT-0024）：gate-fail 轮询去重。

b26 实锤：gateloop 每秒打门，同因失败复铸 gate-fail——终局 596/1422=42%
机械噪声。新语义：同 phase+assert+reason 的失败已是 timeline 最新 gate 事件
且仍为 gate-fail => 不复铸（FAIL 返回值不变）；reason 变化或隔 gate-exit
=> 照铸。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "..", "cli", "tanyin-phases")
FIX = os.path.join(HERE, "fixtures", "G-g1")


def gate(gd, phase, ts):
    return subprocess.run([sys.executable, PH, "gate", "--goal-dir", gd,
                           "--phase=" + phase, "--timestamp=" + ts],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def gf_count(gd):
    with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
        return sum(1 for ln in f if "gate-fail" in ln)


class TestGateFailThrottle(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        # G-g1：P4 可过（全 C3 无重放义务），P5 必失败（矩阵空格未清）
        r = gate(self.d, "P4", "2026-09-24T10:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_three_identical_failures_mint_one_row(self):
        for i in (1, 2, 3):
            r = gate(self.d, "P5", "2026-09-24T10:0%d:00Z" % i)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stdout)
        self.assertEqual(gf_count(self.d), 1)

    def test_first_failure_mints(self):
        r = gate(self.d, "P5", "2026-09-24T10:01:00Z")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(gf_count(self.d), 1)


if __name__ == "__main__":
    unittest.main()

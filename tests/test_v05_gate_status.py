# -*- coding: utf-8 -*-
"""v0.5a F1/F2：gate-status 只读 API + gateloop 预检决策（架构/工程专家项）。

F1：tanyin-phases status——读 timeline 推各门态（PASS/FAIL/PENDING），零断言
零铸事件（b26 型轮询副作用的读侧根治）。F2：驱动侧只在 begin/proc-exit/
soft-stall 三时机跑全量门（should_full_gate 纯函数）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "..", "cli", "tanyin-phases")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import gateloop_core as gc  # noqa: E402


def ph(gd, *args):
    return subprocess.run([sys.executable, PH, "status", "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def gate(gd, phase, ts):
    return subprocess.run([sys.executable, PH, "gate", "--goal-dir", gd,
                           "--phase=" + phase, "--timestamp=" + ts],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def tl_rows(gd):
    with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
        return sum(1 for _ in f)


class TestGateStatus(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_pending_and_passed(self):
        r = ph(self.d, "--phase=P4")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("phase=P4", r.stdout)
        self.assertIn("result=PENDING", r.stdout)   # 夹具无门事件=全 PENDING
        self.assertEqual(gate(self.d, "P2", "2026-09-24T10:00:00Z").returncode, 0)
        r = ph(self.d, "--phase=P2")
        self.assertIn("result=PASS", r.stdout)       # 真过门后 status 见 PASS

    def test_readonly_no_timeline_writes(self):
        before = tl_rows(self.d)
        ph(self.d, "--phase=P4")
        ph(self.d)
        self.assertEqual(tl_rows(self.d), before)

    def test_fail_after_real_gate(self):
        g = gate(self.d, "P4", "2026-09-24T10:00:00Z")
        self.assertEqual(g.returncode, 0, g.stdout)
        r = ph(self.d, "--phase=P4")
        self.assertIn("result=PASS", r.stdout)
        g = gate(self.d, "P5", "2026-09-24T10:01:00Z")
        self.assertEqual(g.returncode, 1)
        r = ph(self.d, "--phase=P5")
        self.assertIn("result=FAIL", r.stdout)

    def test_bad_phase_usage(self):
        r = ph(self.d, "--phase=X9")
        self.assertEqual(r.returncode, 2)


class TestShouldFullGate(unittest.TestCase):
    def test_first_check_runs(self):
        self.assertTrue(gc.should_full_gate(first=True, proc_exited=False,
                                            soft_stalled=False, status_pass=False))

    def test_status_pass_short_circuits(self):
        self.assertFalse(gc.should_full_gate(first=True, proc_exited=False,
                                             soft_stalled=False, status_pass=True))

    def test_poll_between_does_not_run(self):
        self.assertFalse(gc.should_full_gate(first=False, proc_exited=False,
                                             soft_stalled=False, status_pass=False))

    def test_exit_or_softstall_runs(self):
        self.assertTrue(gc.should_full_gate(first=False, proc_exited=True,
                                            soft_stalled=False, status_pass=False))
        self.assertTrue(gc.should_full_gate(first=False, proc_exited=False,
                                            soft_stalled=True, status_pass=False))


if __name__ == "__main__":
    unittest.main()

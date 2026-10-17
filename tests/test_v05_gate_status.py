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


class TestGateOrderSingleSource(unittest.TestCase):
    """W2 枚举单源化①：cmd_status 门序=core.GATE_ORDER 单源派生（禁第二份枚举）。

    红现状：phases_engine.cmd_status 手抄 seq 缺 P6.0（清理门）——timeline 已有
    gate-exit:P6.0 PASS 事件时 status 仍不报该门、--phase=P6.0 被拒 rc=2，
    webui 清理门灯恒 PENDING（05 评审 F1 点名的活 bug）。"""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _append_p60_pass(self):
        # cmd_status 只读事件词（不做链校验）——按表列形追加一行 gate-exit:P6.0
        with open(os.path.join(self.d, "timeline.tsv"), "a", encoding="utf-8",
                  newline="\n") as f:
            f.write("2026-09-24T10:00:00Z\t总控\tP6.0\t"
                    "gate-exit:P6.0 asserts=2 result=PASS\t\tx\ty\t2\n")

    def test_status_reports_p60_row(self):
        self._append_p60_pass()
        r = ph(self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("phase=P6.0", r.stdout, "status 须报清理门 P6.0 行（GATE_ORDER 在册门）")
        self.assertIn("result=PASS", r.stdout)

    def test_phase_p60_accepted(self):
        self._append_p60_pass()
        r = ph(self.d, "--phase=P6.0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("result=PASS", r.stdout)

    def test_status_row_count_equals_gate_order(self):
        from ledger import core
        r = ph(self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rows = [ln for ln in r.stdout.splitlines() if ln.startswith("STATUS	phase=")]
        self.assertEqual(len(rows), len(core.GATE_ORDER),
                         "全量 status 行数=GATE_ORDER 门数（九门单源），实得 %d 行" % len(rows))

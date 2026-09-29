# -*- coding: utf-8 -*-
"""批次5 T4：set-replay-state --timestamp 必填（G-23 墙钟退役）。

钉子三面：缺 --timestamp=用法错误 exit 2；timeline 重放事件行与 findings 联动行
created 一律取参数时间戳（禁墙钟）；h_set_replay_state 函数体 _now() 零命中。
R-T4-1：findings 联动用例改 --id=FD-g1-0001 直指——计划原文 EV-g1-0001 在 G-g1
夹具 linked_finding 为空（不触发 findings 联动行）；EV 通道另设用例只断 timeline。
R-T3-1 同型：run() 形态 --goal-dir 紧随命令（入口 argv[2] 约束）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T09:15:00Z"


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestReplayTimestamp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_missing_timestamp_usage_error(self):
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--timestamp", r.stderr)

    def test_empty_timestamp_usage_error(self):
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--timestamp", r.stderr)

    def test_rows_carry_given_timestamp(self):
        # FD 直指：timeline 重放事件行 + findings 联动行 created 均取参数（不再墙钟）
        r = run(self.d, "set-replay-state", "--id=FD-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        tl = open(os.path.join(self.d, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("replay:FD-g1-0001:VERIFIED", tl)
        self.assertIn(TS, tl)   # 事件行时间戳=参数
        fd = open(os.path.join(self.d, "findings.tsv"), encoding="utf-8").read()
        self.assertIn(TS, fd)   # 联动行 created=参数（不再墙钟）

    def test_ev_path_timeline_carries_timestamp(self):
        # EV 通道（linked_finding 空，不触 findings）：重放事件行仍取参数时间戳
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        tl = open(os.path.join(self.d, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn(TS, tl)

    def test_no_wallclock_in_replay_path(self):
        src = open(os.path.join(HERE, "..", "cli", "ledger", "check_cmds.py"),
                   encoding="utf-8").read()
        i = src.find("def h_set_replay_state")
        j = src.find("\ndef ", i + 1)
        self.assertNotIn("_now()", src[i:j], "set-replay-state 路径残留墙钟")


class TestReplayConflictGuard(unittest.TestCase):
    """批次 9 三轮战复核收口（缝⑪/G-52）：P4 门拦下 not-reproduced 后，
    set-replay-state --state=VERIFIED 不得越过复放实证改判——最新探针裁决为
    not-reproduced 且无更晚 reproduced 行 ⇒ REJECT rc=1；无探针行（批次 5
    手工核验证通道）保持放行不破坏既有语义。"""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _inject_probe(self, verdict, ts):
        r = run(self.d, "append-timeline", "--actor=子代理", "--phase=P4",
                "--event=replay-probe EV-g1-0001 verdict=%s" % verdict,
                "--revert-cmd=none", "--timestamp=" + ts)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_verified_blocked_after_not_reproduced(self):
        self._inject_probe("not-reproduced", "2026-09-29T16:00:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("not-reproduced", r.stderr + r.stdout)

    def test_repaired_blocked_after_not_reproduced(self):
        self._inject_probe("not-reproduced", "2026-09-29T16:00:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=REPAIRED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_later_reproduced_unblocks(self):
        self._inject_probe("not-reproduced", "2026-09-29T16:00:00Z")
        self._inject_probe("reproduced", "2026-09-29T16:30:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_rejected_and_manual_channel_unaffected(self):
        self._inject_probe("not-reproduced", "2026-09-29T16:00:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=REJECTED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        r2 = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                 "--timestamp=" + TS)   # 无探针行的手工通道（G-g1 原始态语义）
        self.assertEqual(r2.returncode, 1, r.stdout + r2.stderr)  # 上一行已注 REJECTED 探针仍在


if __name__ == "__main__":
    unittest.main()

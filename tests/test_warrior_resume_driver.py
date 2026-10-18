# -*- coding: utf-8 -*-
"""dsh P0 采纳③：续跑驱动（对照 docs/research/2026-10-20-dsh-orchestration-inventory.md
A 表#6 / §③ goal 状态机+轮转驱动 / §⑧-3；dsh 出处
dsh-goal-round-driver/lib/index.js:11-18,105-164,125-131）。

我方停序(yield→stop→预算→时间窗→停滞)是「停」，本件补「续」——停滞
重生后从哪续、续几轮、何时判死的状态机（四相 armed/disarmed/blocked/
complete + 轮计硬上限 + 断点 + 防幻觉续跑提示）。

纯函数律：只读 goal 目录盘上账本（timeline/intents/tool-executions），
产出续跑指令包不落盘不调 LLM。轮计单源=盘上 timeline warrior-start 行数
（每次重生 loop.run() 必落此行——重启不重置轮计）。

跑法：python3 -m unittest tests.test_warrior_resume_driver -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger.timeline import append_tl_locked               # noqa: E402
from warrior import resume_driver as rd                    # noqa: E402
from warrior.ledger_io import LedgerIO                     # noqa: E402
from tests.test_warrior_repair import write_exec, r_running  # noqa: E402

W = "warrior:W-1"
NOW = "2026-10-20T12:00:00Z"
IID = "INT-g1-0002"          # fixture 中唯一 pending 意图


class TestResumeDriver(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.addCleanup(shutil.rmtree, self.gd)
        self.io = LedgerIO(self.gd, W)

    def _tl(self, event, ts="2026-10-20T10:00:00Z", actor=W):
        append_tl_locked(self.gd, ts, event, actor=actor,
                         phase="P-lifecycle")

    def _claim(self, lease_min=120):
        ok, _ = self.io.claim(IID, lease_min, "2026-10-20T11:00:00Z")
        self.assertTrue(ok)

    # ---- 四相状态机 ----

    def test_armed_with_active_lease_and_rounds_left(self):
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W, "2026-10-20T09:00:00Z")
        self._tl("warrior-start battle=B warrior=%s" % W, "2026-10-20T11:00:00Z")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.phase, "armed")
        self.assertTrue(d.resume)
        self.assertEqual(d.rounds_started, 2, "轮计=盘上 warrior-start 行数")
        self.assertEqual(d.rounds_remaining, d.max_goal_rounds - 2)

    def test_round_limit_blocks_even_with_lease(self):
        """dsh goal-round-driver:125-131 同律：轮计达硬上限→block(round-limit)。"""
        self._claim()
        for h in ("08", "09", "10"):
            self._tl("warrior-start battle=B warrior=%s" % W,
                     "2026-10-20T%s:00:00Z" % h)
        d = rd.build_resume_directive(self.gd, W, max_goal_rounds=3,
                                      now_ts=NOW)
        self.assertEqual(d.phase, "blocked")
        self.assertEqual(d.block_code, "round-limit")
        self.assertFalse(d.resume)

    def test_disarmed_after_stop_signal(self):
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W)
        self._tl("warrior-stop warrior=%s reason=stop-signal halt" % W,
                 "2026-10-20T11:30:00Z")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.phase, "disarmed")
        self.assertFalse(d.resume)
        self.assertIn("stop-signal", d.disarm_reason)

    def test_restart_after_stop_rearms(self):
        """停后又有新 warrior-start（重启）→ 重新 armed（dsh resume 同哲学）。"""
        self._tl("warrior-stop warrior=%s reason=stop-signal halt" % W,
                 "2026-10-20T09:30:00Z")
        self._tl("warrior-start battle=B warrior=%s" % W,
                 "2026-10-20T10:00:00Z")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.phase, "armed")

    def test_stall_last_keeps_armed(self):
        """停滞重生正是续跑场景：末生命周期行=warrior-stall → armed。"""
        self._tl("warrior-start battle=B warrior=%s" % W)
        self._tl("warrior-stall warrior=%s detail=no-progress" % W,
                 "2026-10-20T11:45:00Z")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.phase, "armed")
        self.assertTrue(d.resume)

    def test_complete_when_nothing_left(self):
        self._claim()          # pending→active→done 合法箭头链
        ok, _ = self.io.complete(IID, "2026-10-20T11:30:00Z", reason="收口")
        self.assertTrue(ok)
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.phase, "complete")
        self.assertFalse(d.resume)

    def test_rounds_counted_only_from_own_actor(self):
        for _ in range(2):
            self._tl("warrior-start battle=B warrior=%s" % W)
        for _ in range(3):
            self._tl("warrior-start battle=B warrior=warrior:W-9",
                     actor="warrior:W-9")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.rounds_started, 2, "他者 start 不计入我的轮计")

    # ---- 断点（从哪续）----

    def test_breakpoint_takes_over_active_lease(self):
        self._claim()
        self._tl("warrior-progress warrior=%s intent=%s turn=2 op=scan "
                 "out=found" % (W, IID), "2026-10-20T11:50:00Z")
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.breakpoint["intent_id"], IID)
        self.assertEqual(d.breakpoint["mode"], "reclaim-lease",
                         "接管自己活租约（loop.py:309 同哲学）")
        self.assertIn("op=scan", d.breakpoint["last_event"])

    def test_breakpoint_falls_back_to_claimable(self):
        self._tl("warrior-start battle=B warrior=%s" % W)
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.breakpoint["intent_id"], IID)
        self.assertEqual(d.breakpoint["mode"], "claim-new")

    def test_dangling_executions_listed_for_breakpoint_intent(self):
        self._claim()
        write_exec(self.gd, [
            r_running("EX-%s-t1-c0" % IID),
            r_running("EX-INT-g1-0001-t9-c9"),      # 他人/已 done 意图的悬空
            ["EX-%s-t1-c1" % IID, "dig", "completed",
             "2026-10-20T01:00:00Z", "2026-10-20T01:01:00Z", "0", ""]])
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertEqual(d.dangling, ["EX-%s-t1-c0" % IID],
                         "只列断点意图的悬空执行（精确归位）")

    # ---- 续跑指令包 ----

    def test_prompt_carries_anti_hallucination_and_rounds(self):
        """dsh goal-round-driver:11-18 同哲学：以盘上态为准，不信此前叙述。"""
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W)
        self._tl("warrior-progress warrior=%s intent=%s turn=3 op=enum"
                 % (W, IID), "2026-10-20T11:55:00Z")
        d = rd.build_resume_directive(self.gd, W, max_goal_rounds=5,
                                      now_ts=NOW)
        self.assertIn("<goal_round>", d.prompt)
        self.assertIn("以盘上账本为准", d.prompt)
        self.assertIn("别信战士自述", d.prompt)
        self.assertIn("第 1/5 轮", d.prompt)
        self.assertIn(IID, d.prompt)
        self.assertIn("op=enum", d.prompt, "断点末事件进指令包")

    def test_prompt_lists_dangling_with_idempotent_guidance(self):
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W)
        write_exec(self.gd, [r_running("EX-%s-t1-c0" % IID)])
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertIn("EX-%s-t1-c0" % IID, d.prompt)
        self.assertIn("结果未知", d.prompt)
        self.assertIn("仅幂等才重试", d.prompt)

    def test_prompt_no_dangling_says_none(self):
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W)
        d = rd.build_resume_directive(self.gd, W, now_ts=NOW)
        self.assertIn("无悬空", d.prompt)

    # ---- 纯函数律 ----

    def test_directive_is_pure_no_disk_mutation(self):
        self._claim()
        self._tl("warrior-start battle=B warrior=%s" % W)
        write_exec(self.gd, [r_running("EX-%s-t1-c0" % IID)])
        snap = {}
        for name in os.listdir(self.gd):
            p = os.path.join(self.gd, name)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    snap[name] = f.read()
        rd.build_resume_directive(self.gd, W, now_ts=NOW)
        for name, before in snap.items():
            with open(os.path.join(self.gd, name), "rb") as f:
                self.assertEqual(f.read(), before, "%s 零改写" % name)


if __name__ == "__main__":
    unittest.main()

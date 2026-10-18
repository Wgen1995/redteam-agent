# -*- coding: utf-8 -*-
"""评审打回复盘：规划者 I-1/I-2/I-3/I-4+M-5 修复（TDD 红测试先行）。

评审源：docs/reviews/2026-10-20-review-sentinel-planner.md §二——
  I-1 REJECT 走 stderr（_run 只捕 stdout→拒绝原因全空、dedup 竞速合并
     分支死代码、竞速真发生=RuntimeError 杀常驻循环，run() 无兜底）
  I-2 TANYIN_APPROVAL_KEY 在场时 _redispatch 机械审批必崩（须 --sig 签名）
  I-3 事件驱动闭环未接线（收卡惰性触发 + CLI start/trigger 两入口）
  I-4 sweep O(I×N)（万格同构基准 8s+→头部一趟聚合+Session 全 sweep 复用）
  M-5 _reach_set 图构建重复两次（自建 _build 后 reachable_gap_cells 又建）

跑法：python3 -m unittest tests.test_planner_fixes -v
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import time
import unittest

try:
    from unittest import mock
except ImportError:                                    # pragma: no cover
    mock = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)

from ledger import registry                            # noqa: E402
from ledger import planner_loop as PL                  # noqa: E402
from ledger import replacer as RP                      # noqa: E402
from ledger.core import Session, TABLES                # noqa: E402
from ledger import timeline as TL                      # noqa: E402
from tests.test_planner_loop import _mkgoal, FakeClock  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-20T10:00:00Z"
_IT = TABLES["intents.tsv"].index("title")
_ID = TABLES["intents.tsv"].index("detail")
_IS = TABLES["intents.tsv"].index("status")
_EV = TABLES["timeline.tsv"].index("event")

BAD_KIND_ARGS = ["--title=x", "--detail=d", "--engine=web-blackbox",
                 "--kind=bogus", "--origin=adjacency", "--budget-share=1;1;1",
                 "--timestamp=" + TS]


def run(gd, cmd, *args):
    """CLI 级既有入口（同 test_planner_replacer.run 单源口径）。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    if rc != 0:
        raise AssertionError("%s rc=%d: %s" % (cmd, rc, buf.getvalue()))
    return buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def rows(self, t):
        return Session(self.gd).rows(t)


# ============================================================ I-1 stderr 捕获 ==

class TestRunCapturesRejection(Base):
    """I-1：write_cmds._wrap 把 REJECT 写 stderr——_run 只捕 stdout 则
    坏参数时 out=''（拒绝原因全空）。修法=stdout+stderr 合并捕获。"""

    def test_planner_run_carries_reject_reason(self):
        rc, out = PL._run(self.gd, "add-intent", list(BAD_KIND_ARGS))
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out)
        self.assertIn("kind 不在枚举", out, "拒绝原因须随合并文本带回（排障面）")

    def test_replacer_run_carries_reject_reason(self):
        rc, out = RP._run(self.gd, "add-intent", list(BAD_KIND_ARGS))
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out)
        self.assertIn("kind 不在枚举", out)


# ======================================================== I-1 dedup 竞速合并 ==

class TestDedupRaceMerged(Base):
    """I-1：竞速合并分支曾是死代码（"dedup_key" 判在空 out 上）——模拟
    并发战士在 existing 快照之后、add-intent 落账之前先铸同 dedup 卡：
    真命中=合并不 raise（RuntimeError 会杀死常驻循环/炸 sweep）。"""

    def _race_lookup(self, race_args):
        """首见 add-intent 时先经真通道铸 race_args 卡（=并发方先落账）。"""
        real_lookup = registry.lookup
        state = {"raced": False}

        def fake(cmd):
            h = real_lookup(cmd)
            if cmd == "add-intent" and not state["raced"]:
                state["raced"] = True
                rc = h(self.gd, list(race_args))
                self.assertEqual(rc, 0, "竞速方先铸须成功")
            return h
        return fake

    def test_assess_race_merges_instead_of_raising(self):
        race_title = PL.intent_title("admin.shop.example", "inj.sql")
        race_args = ["--title=" + race_title, "--detail=竞速方先落",
                     "--engine=web-blackbox", "--kind=matrix-test",
                     "--origin=adjacency", "--budget-share=1;1;1",
                     "--priority=0.9000", "--timestamp=" + TS]
        with mock.patch.object(registry, "lookup",
                               self._race_lookup(race_args)):
            added = PL.assess(self.gd, TS)            # 不得 raise（I-1）
        titles = sorted(r[_IT] for r in self.rows("intents.tsv")
                        if r[_IT].startswith("planner: "))
        both = sorted([PL.intent_title("admin.shop.example", "inj.sql"),
                       PL.intent_title("admin.shop.example", "wstg-inpv")])
        self.assertEqual(titles, both,
                         "竞速卡并入（回放特例律），另一空格本轮照常派")
        self.assertEqual(len(added), 1)
        raced = [r for r in self.rows("intents.tsv")
                 if r[_IT] == race_title][-1]
        self.assertIn("竞速方先落", raced[_ID], "在账的=竞速方铸的卡（真合并）")

    def test_continue_card_race_merges_instead_of_raising(self):
        run(self.gd, "add-intent", "--title=半程卡", "--detail=剩余: 补测",
            "--engine=web-blackbox", "--kind=matrix-test",
            "--origin=recon-event", "--budget-share=1;1;1",
            "--priority=0.5", "--timestamp=" + TS)
        iid = [r[0] for r in self.rows("intents.tsv")
               if r[_IT] == "半程卡"][-1]
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=active",
            "--timestamp=" + TS)
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=blocked",
            "--reason=预算中断", "--timestamp=" + TS)
        race_args = ["--title=续接: 半程卡", "--detail=竞速方先落",
                     "--engine=web-blackbox", "--kind=matrix-test",
                     "--origin=recon-event", "--budget-share=1;1;1",
                     "--priority=0.5", "--timestamp=" + TS]
        with mock.patch.object(registry, "lookup",
                               self._race_lookup(race_args)):
            out = RP.sweep(self.gd, TS)               # 不得 raise（I-1）
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["continue-closeout"])
        cont = [r for r in self.rows("intents.tsv")
                if r[_IT] == "续接: 半程卡"]
        self.assertEqual(len(cont), 1, "竞速续接卡并入，恰一张（幂等）")
        self.assertIn("竞速方先落", cont[-1][_ID])


# ======================================================== I-1 run() 兜底 ==

class TestRunSurvivesRoundCrash(Base):
    """I-1：run() 无兜底——单轮异常直接杀死常驻循环。修法=异常记事件
    入账本（append-timeline 既有通道，可回放）后继续轮询。"""

    def test_run_records_event_and_survives(self):
        clock = FakeClock()
        loop = PL.PlannerLoop(self.gd, ts_fn=lambda: TS,
                              mono=clock.mono, sleep=clock.sleep,
                              poll_interval=0.1)
        orig = loop._round
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("round-1 崩（探针）")
            return orig()

        loop._round = flaky
        TL.append_tl_locked(self.gd, TS, "战士写回: 新线索", "warrior:W-1", "P3")
        n = loop.run(max_rounds=2)
        self.assertEqual(n, 2, "常驻循环不死于单轮异常")
        self.assertEqual(len(calls), 2)
        evs = [r[_EV] for r in self.rows("timeline.tsv")]
        self.assertTrue(any(e.startswith("planner-round-fail") for e in evs),
                        "单轮异常须记事件入账本: %r" % evs[-5:])
        self.assertTrue(any("round-1" in e for e in evs),
                        "事件须带异常原因（排障面）")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""dsh P0 采纳①：崩溃尾修复（对照 docs/research/2026-10-20-dsh-orchestration-inventory.md
A 表#2 / §③ / §⑧-1；dsh 出处 session/types/repair.js:15-77,84-189）。

哲学同源=不丢不假完成：悬空 execution_id（tool-executions.tsv 运行行无
终态）→ 崩溃判定 + 合成收尾（状态升 orphaned-not-lost + timeline 一行
「结果未知,仅幂等才重试,有副作用先验证外部状态」——重试权交模型但给
幂等判据，不静默重跑（误报源）不静默丢弃（漏报源））。

纯函数律：只读盘上会话态，产出计划不落盘（接线位见 repair.py 头注）。

跑法：python3 -m unittest tests.test_warrior_repair -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger.core import Session                      # noqa: E402
from ledger.timeline import append_tl_locked         # noqa: E402
from warrior import repair as wr                     # noqa: E402

W = "warrior:W-1"


def write_exec(gd, rows):
    """按 AsyncExecPool._persist 同律写 7 列 TSV（仅测试面落盘）。"""
    with open(os.path.join(gd, "tool-executions.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("\t".join(str(c) for c in r) + "\n")


def r_running(eid="EX-IN-a-t1-c0", card="nmap", sub="2026-10-20T01:00:00Z"):
    return [eid, card, "running", sub, "", "", ""]


def r_done(eid="EX-IN-a-t1-c1", card="dig"):
    return [eid, card, "completed", "2026-10-20T01:00:00Z",
            "2026-10-20T01:01:00Z", "0", ""]


class TestRepair(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.addCleanup(shutil.rmtree, self.gd)

    def _tl(self, event, ts, actor=W):
        append_tl_locked(self.gd, ts, event, actor=actor, phase="P-lifecycle")

    # ---- 崩溃判定 ----

    def test_no_state_file_returns_none(self):
        self.assertIsNone(wr.plan_repair(self.gd), "无 tool-executions.tsv=无崩溃尾")

    def test_all_terminal_rows_returns_none(self):
        write_exec(self.gd, [r_done(),
                             ["EX-IN-a-t1-c2", "curl", "failed",
                              "2026-10-20T01:00:00Z",
                              "2026-10-20T01:01:00Z", "7", ""],
                             ["EX-IN-a-t1-c3", "nmap", "orphaned",
                              "2026-10-20T01:00:00Z", "", "", ""]])
        self.assertIsNone(wr.plan_repair(self.gd),
                          "completed/failed/orphaned 全终态=无悬空")

    def test_orphaned_pool_marker_is_terminal_not_dangling(self):
        """AsyncExecPool 孤儿对账已标 orphaned 的行不再触发修复（不双修）。"""
        write_exec(self.gd, [["EX-IN-a-t1-c0", "nmap", "orphaned",
                              "2026-10-20T01:00:00Z", "", "", ""]])
        self.assertIsNone(wr.plan_repair(self.gd))

    def test_running_rows_verdict_crashed_with_ids(self):
        write_exec(self.gd, [r_running("EX-IN-a-t1-c0"),
                             r_running("EX-IN-a-t2-c0"), r_done()])
        plan = wr.plan_repair(self.gd)
        self.assertIsNotNone(plan)
        self.assertTrue(plan.crashed)
        self.assertEqual(plan.dangling_ids,
                         ["EX-IN-a-t1-c0", "EX-IN-a-t2-c0"])

    # ---- 合成收尾：状态行 ----

    def test_dangling_marked_orphaned_not_lost_not_faked(self):
        write_exec(self.gd, [[
            "EX-IN-a-t1-c0", "nmap", "running", "2026-10-20T01:00:00Z",
            "", "", "tmp/spill-nmap-abc.txt"]])
        plan = wr.plan_repair(self.gd)
        by = {r["execution_id"]: r for r in plan.repaired_rows}
        r = by["EX-IN-a-t1-c0"]
        self.assertEqual(r["status"], "orphaned-not-lost")
        self.assertEqual(r["rc"], "", "结果未知——rc 不假填（不假完成）")
        self.assertEqual(r["spill_path"], "tmp/spill-nmap-abc.txt",
                         "spill 指针不丢（不丢）")
        self.assertEqual(r["submitted_ts"], "2026-10-20T01:00:00Z")
        self.assertEqual(r["finished_ts"], plan.ts,
                         "收尾时戳=计划时戳（确定性）")

    def test_terminal_rows_pass_through_unchanged(self):
        done = r_done()
        write_exec(self.gd, [r_running(), done])
        plan = wr.plan_repair(self.gd)
        by = {r["execution_id"]: r for r in plan.repaired_rows}
        self.assertEqual(by["EX-IN-a-t1-c1"]["status"], "completed")
        self.assertEqual(by["EX-IN-a-t1-c1"]["rc"], "0")

    # ---- 合成收尾：timeline 一行 ----

    def test_single_timeline_line_carries_idempotent_retry_guidance(self):
        write_exec(self.gd, [r_running("EX-IN-a-t1-c0"),
                             r_running("EX-IN-a-t2-c0")])
        plan = wr.plan_repair(self.gd)
        self.assertIsInstance(plan.timeline_event, str)
        for eid in ("EX-IN-a-t1-c0", "EX-IN-a-t2-c0"):
            self.assertIn(eid, plan.timeline_event, "悬空 id 必须点名")
        self.assertIn("orphaned-not-lost", plan.timeline_event)
        self.assertIn("结果未知", plan.timeline_event)
        self.assertIn("仅幂等才重试", plan.timeline_event)
        self.assertIn("有副作用先验证外部状态", plan.timeline_event)
        self.assertIn("warrior-repair", plan.timeline_event)

    def test_ts_reuses_last_real_timeline_event(self):
        """dsh repair.js:84-189 同律——合成事件时戳复用最后真实事件。"""
        write_exec(self.gd, [r_running()])
        self._tl("warrior-progress warrior=%s intent=INT-g1-0002 turn=2 "
                 "op=scan", "2026-10-20T05:30:00Z")
        plan = wr.plan_repair(self.gd)
        self.assertEqual(plan.ts, "2026-10-20T05:30:00Z")

    def test_ts_falls_back_to_dangling_submitted_when_timeline_empty(self):
        gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, gd)
        Session(gd)                       # 空会话：13 表齐但 timeline 零行
        write_exec(gd, [r_running("EX-IN-a-t1-c0", sub="2026-10-20T02:00:00Z"),
                        r_running("EX-IN-a-t2-c0", sub="2026-10-20T03:00:00Z")])
        plan = wr.plan_repair(gd)
        self.assertEqual(plan.ts, "2026-10-20T02:00:00Z",
                         "无真实事件可复用时取最早悬空提交钟（确定性）")

    # ---- 幂等与鲁棒 ----

    def test_already_repaired_timeline_returns_none(self):
        write_exec(self.gd, [r_running("EX-IN-a-t1-c0")])
        self._tl("warrior-repair verdict=orphaned-not-lost dangling=1 "
                 "ids=EX-IN-a-t1-c0 指导=结果未知,仅幂等才重试",
                 "2026-10-20T06:00:00Z")
        self.assertIsNone(wr.plan_repair(self.gd),
                          "同一批悬空已修过=不重复修（幂等律）")

    def test_partial_prior_repair_still_plans_new_dangling(self):
        write_exec(self.gd, [r_running("EX-IN-a-t1-c0"),
                             r_running("EX-IN-a-t2-c0")])
        self._tl("warrior-repair verdict=orphaned-not-lost dangling=1 "
                 "ids=EX-IN-a-t1-c0 指导=结果未知", "2026-10-20T06:00:00Z")
        plan = wr.plan_repair(self.gd)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.dangling_ids, ["EX-IN-a-t2-c0"],
                         "只修新悬空，旧账不重开")

    def test_malformed_rows_skipped(self):
        write_exec(self.gd, [["只有三列", "x", "running"],
                             r_running("EX-IN-a-t1-c0")])
        plan = wr.plan_repair(self.gd)
        self.assertEqual(plan.dangling_ids, ["EX-IN-a-t1-c0"],
                         "列数坏行跳过不炸（解析面 fail-soft，判定面精确）")

    def test_empty_state_file_returns_none(self):
        write_exec(self.gd, [])
        self.assertIsNone(wr.plan_repair(self.gd))

    # ---- 纯函数律 ----

    def test_plan_is_pure_no_disk_mutation(self):
        write_exec(self.gd, [r_running()])
        self._tl("warrior-progress op=scan", "2026-10-20T05:00:00Z")
        with open(os.path.join(self.gd, "tool-executions.tsv"), "rb") as f:
            exec_before = f.read()
        with open(os.path.join(self.gd, "timeline.tsv"), "rb") as f:
            tl_before = f.read()
        wr.plan_repair(self.gd)
        with open(os.path.join(self.gd, "tool-executions.tsv"), "rb") as f:
            self.assertEqual(f.read(), exec_before, "状态文件零改写")
        with open(os.path.join(self.gd, "timeline.tsv"), "rb") as f:
            self.assertEqual(f.read(), tl_before, "timeline 零改写")

    def test_apply_plan_then_replan_is_none(self):
        """接线后落盘 repaired_rows（池同律格式）→ 二次计划=None（闭环）。"""
        write_exec(self.gd, [r_running("EX-IN-a-t1-c0"), r_done()])
        plan = wr.plan_repair(self.gd)
        write_exec(self.gd, [[r["execution_id"], r["card"], r["status"],
                              r["submitted_ts"], r["finished_ts"],
                              r["rc"], r["spill_path"]]
                             for r in plan.repaired_rows])
        self.assertIsNone(wr.plan_repair(self.gd),
                          "收尾落盘后无悬空——修复是一次性闭环")


if __name__ == "__main__":
    unittest.main()

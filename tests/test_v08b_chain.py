# -*- coding: utf-8 -*-
"""v0.8 Task B：链式 todolist 稳定器——prereq 前置链 + chain-create/chain-advance/chain-ls。

设计裁决（与计划原文的两处偏差，详见 write_cmds.py 探知注记 13-15）：
- 「intents.tsv 加 prereq 列」→ prereq 以 detail 单元格内 [prereq:INT-…] 标记承载
  （先例=批次 7 T13 facts [no-consume:] 标记：13 表列集冻结→自由文本唯一承载位；
  schemas.json 机械生成禁手改+28 个夹具 17 列，物理加列=read_tsv 全炸）。
  默认无标记=无前置；事件溯源整行复制天然携带；读 TSV 即态（不蒸发律）。
- 命令不经 HANDLERS 注册（45 基名命令面冻结绊线：test_phases_yaml/selfcheck/
  SKILL.md 三处会红）——先例=批次 5 T15 reverse-verify 的 REVERSE_VERIFY 导出式；
  CHAIN_HANDLERS 签名 (goal_dir, rest)->exit_code 与在册命令同构，集成期并入
  _IMPL 一行即获双前缀别名+goal 写锁。
- 链步骤间边：_EDGE_DIR 执法 spawns=goals→intents（INT→INT 非法）→ 每步补
  goal→step spawns 边 + 相邻步 cross_ref 边（全走既有 EDGE_KINDS 与既有写边
  校验/铸行路径，无新边类型=不 bump schema_version）。

测试四象限（计划 Task B 节）：无前置放行 / 前置未终态 Reject（查询+写入双保险）/
前置终态放行 / 重启后链状态可恢复（读 TSV 即态）。
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import write_cmds  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-11T09:00:00Z"


def _ts(minute):
    return "2026-10-11T09:%02d:00Z" % minute


CHAIN_BASE = ("--engine=web-blackbox", "--kind=recon", "--origin=llm",
              "--budget-share=100;10;1")


class ChainTestBase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        self.n_intents0 = len(self.intent_rows())
        self.n_edges0 = len(self.edge_rows())

    def tearDown(self):
        shutil.rmtree(self.d)

    def call(self, name, *params):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = write_cmds.CHAIN_HANDLERS[name](self.d, list(params))
        return rc, out.getvalue(), err.getvalue()

    def call_registered(self, name, *params):
        # 既有在册命令（set-intent-status 双保险验证用）——同签名直调
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = write_cmds.HANDLERS[name](self.d, list(params))
        return rc, out.getvalue(), err.getvalue()

    def intent_rows(self):
        p = os.path.join(self.d, "intents.tsv")
        return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines()
                if l.strip()]

    def edge_rows(self):
        p = os.path.join(self.d, "edges.tsv")
        return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines()
                if l.strip()]

    def timeline_text(self):
        p = os.path.join(self.d, "timeline.tsv")
        return open(p, encoding="utf-8").read()

    def col(self, row, field):
        return row[TABLES["intents.tsv"].index(field)]

    def latest_intents(self):
        out = {}
        for r in self.intent_rows():
            out[r[0]] = r
        return out

    def mk_chain(self, titles=("端口扫描", "服务识别", "漏洞验证"), minute=0):
        rc, out, err = self.call("chain-create", *CHAIN_BASE,
                                 "--steps=" + "|".join(titles),
                                 "--timestamp=" + _ts(minute))
        self.assertEqual(rc, 0, err)
        head = out.splitlines()[0].split("\t")[1]
        steps = [r[0] for r in self.latest_intents().values()
                 if r[0] not in ("INT-g1-0001", "INT-g1-0002")]
        steps.sort(key=lambda i: int(i.rsplit("-", 1)[1]))
        self.assertEqual(steps[0], head)
        return steps

    def advance(self, iid, status, minute, reason=""):
        params = ["--id=" + iid, "--status=" + status, "--timestamp=" + _ts(minute)]
        if reason:
            params.append("--reason=" + reason)
        return self.call("chain-advance", *params)


class TestChainCreate(ChainTestBase):
    def test_mints_prereq_chain_and_edges(self):
        head, s2, s3 = self.mk_chain()
        latest = self.latest_intents()
        # 三步 candidate；head 无标记，后续步 detail=[prereq:前一步]
        self.assertEqual(self.col(latest[head], "status"), "candidate")
        self.assertEqual(self.col(latest[head], "detail"), "")
        self.assertEqual(self.col(latest[s2], "detail"), "[prereq:" + head + "]")
        self.assertEqual(self.col(latest[s3], "detail"), "[prereq:" + s2 + "]")
        self.assertEqual(len(self.intent_rows()), self.n_intents0 + 3)
        # 边：goal→每步 spawns + 相邻步 cross_ref（既有 EDGE_KINDS，无新类型）
        ek = TABLES["edges.tsv"].index("kind")
        es, ed = TABLES["edges.tsv"].index("source_id"), TABLES["edges.tsv"].index("target_id")
        ep = TABLES["edges.tsv"].index("provenance")
        new_edges = self.edge_rows()[self.n_edges0:]
        spawns = [r for r in new_edges if r[ek] == "spawns"]
        cross = [r for r in new_edges if r[ek] == "cross_ref"]
        self.assertEqual(len(spawns), 3)
        self.assertEqual({r[ed] for r in spawns}, {head, s2, s3})
        self.assertEqual(len(cross), 2)
        self.assertEqual({(r[es], r[ed]) for r in cross}, {(head, s2), (s2, s3)})
        for r in new_edges:
            self.assertEqual(r[ep], "chain-create")
        # 全部仍在既有边枚举内
        self.assertTrue({r[ek] for r in new_edges} <= write_cmds.EDGE_KINDS)
        self.assertIn("chain-create", self.timeline_text())

    def test_steps_at_least_two(self):
        rc, out, err = self.call("chain-create", *CHAIN_BASE, "--steps=孤步",
                                 "--timestamp=" + TS)
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", err)

    def test_duplicate_title_in_chain_rejected(self):
        rc, out, err = self.call("chain-create", *CHAIN_BASE,
                                 "--steps=重复步|重复步", "--timestamp=" + TS)
        self.assertEqual(rc, 1)
        self.assertIn("dedup", err)
        self.assertEqual(len(self.intent_rows()), self.n_intents0)  # 零写入

    def test_bad_kind_budget_rejected(self):
        rc, _, err = self.call("chain-create", "--engine=e", "--kind=bad-kind",
                               "--origin=llm", "--budget-share=1;1;1",
                               "--steps=a|b", "--timestamp=" + TS)
        self.assertEqual(rc, 1)
        self.assertIn("kind", err)
        rc, _, err = self.call("chain-create", *CHAIN_BASE[:-1],
                               "--budget-share=abc", "--steps=a|b",
                               "--timestamp=" + TS)
        self.assertEqual(rc, 1)
        self.assertIn("budget_share", err)


class TestAdvanceFourQuadrants(ChainTestBase):
    def test_no_prereq_passes(self):
        # 象限①：head 无前置 → 放行
        head, s2, _ = self.mk_chain()
        rc, out, err = self.advance(head, "pending", 10)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.col(self.latest_intents()[head], "status"), "pending")

    def test_prereq_not_terminal_rejected_both_paths(self):
        # 象限②：前置未终态 → Reject（chain-advance 与 set-intent-status 双保险）
        head, s2, s3 = self.mk_chain()
        rc, _, err = self.advance(s2, "pending", 10)
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", err)
        self.assertIn("前置", err)
        rc, _, err = self.call_registered("set-intent-status", "--id=" + s2,
                                          "--status=pending",
                                          "--timestamp=" + _ts(11))
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", err)
        self.assertIn("前置", err)
        # Reject=零写入：intents/timeline 均不变
        self.assertEqual(len(self.intent_rows()), self.n_intents0 + 3)
        self.assertEqual(self.col(self.latest_intents()[s2], "status"), "candidate")

    def test_prereq_terminal_passes(self):
        # 象限③：前置终态（done）→ 放行
        head, s2, _ = self.mk_chain()
        for i, st in enumerate(("pending", "active", "done")):
            rc, _, err = self.advance(head, st, 10 + i)
            self.assertEqual(rc, 0, err)
        rc, _, err = self.advance(s2, "pending", 20)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.col(self.latest_intents()[s2], "status"), "pending")

    def test_rejected_prereq_also_terminal(self):
        # 终态={done,rejected}（状态机无出边单源推导）——rejected 前置同样放行
        # （candidate→rejected 为合法箭头；active→rejected 不沿状态机）
        head, s2, _ = self.mk_chain()
        rc, _, err = self.advance(head, "rejected", 10, reason="计划废弃")
        self.assertEqual(rc, 0, err)
        rc, _, err = self.advance(s2, "pending", 20)
        self.assertEqual(rc, 0, err)

    def test_state_machine_still_enforced(self):
        head, _, _ = self.mk_chain()
        rc, _, err = self.advance(head, "active", 10)  # candidate→active 跳态
        self.assertEqual(rc, 1)
        self.assertIn("状态机", err)

    def test_non_chain_intent_rejected(self):
        # 非链上步骤（无标记且未被引用）不得走 chain-advance
        rc, _, err = self.advance("INT-g1-0002", "active", 10)
        self.assertEqual(rc, 1)
        self.assertIn("非链", err)


class TestChainLs(ChainTestBase):
    def test_frontier_filter_and_listing(self):
        head, s2, s3 = self.mk_chain()
        rc, out, err = self.call("chain-ls")
        self.assertEqual(rc, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("#chains=1"))
        self.assertIn("#frontier=1", lines[0])
        rows = {}
        for ln in lines[1:]:
            c = ln.split("\t")
            rows[c[2]] = c  # c: head,seq,id,title,status,prereq,prereq_st,frontier
        # 查询侧过滤：head（无前置）在 frontier；s2/s3 前置未终态 → frontier=no
        self.assertEqual(rows[head][7], "yes")
        self.assertEqual(rows[s2][7], "no")
        self.assertEqual(rows[s3][7], "no")
        self.assertEqual(rows[s2][5], head)
        self.assertEqual(rows[head][4], "candidate")
        # --chain 过滤
        rc, out, _ = self.call("chain-ls", "--chain=" + head)
        self.assertEqual(rc, 0)
        self.assertEqual(len([l for l in out.splitlines() if l.startswith(head + "\t")]), 3)
        rc, out, _ = self.call("chain-ls", "--chain=INT-g1-0001")
        self.assertEqual(rc, 0)
        self.assertTrue(out.splitlines()[0].startswith("#chains=0"))
        # head 终态后：head 出局（终态非 frontier），s2 入 frontier
        for i, st in enumerate(("pending", "active", "done")):
            self.advance(head, st, 10 + i)
        rc, out, _ = self.call("chain-ls")
        lines = out.splitlines()
        self.assertIn("#frontier=1", lines[0])
        rows = {l.split("\t")[2]: l.split("\t") for l in lines[1:]}
        self.assertEqual(rows[head][7], "no")   # done=终态不再占 frontier
        self.assertEqual(rows[head][4], "done")
        self.assertEqual(rows[s2][7], "yes")

    def test_empty_goal_dir_zero_chains(self):
        rc, out, err = self.call("chain-ls")
        self.assertEqual(rc, 0, err)
        self.assertTrue(out.splitlines()[0].startswith("#chains=0"))


class TestRestartRecovery(ChainTestBase):
    def test_chain_state_survives_restart(self):
        # 象限④：不蒸发律——每次命令调用都从磁盘重建 Session（=重启语义），
        # 链状态全部来自 intents.tsv 的 [prereq:] 标记与 status 列。
        head, s2, s3 = self.mk_chain()
        for i, st in enumerate(("pending", "active", "done")):
            self.advance(head, st, 10 + i)
        # 「重启」后：chain-ls 读 TSV 重建链；s3 仍被未终态的 s2 拦住
        rc, out, err = self.call("chain-ls")
        self.assertEqual(rc, 0, err)
        rows = {l.split("\t")[2]: l.split("\t") for l in out.splitlines()[1:]}
        self.assertEqual(rows[head][4], "done")
        self.assertEqual(rows[s2][7], "yes")
        self.assertEqual(rows[s3][7], "no")
        rc, _, err = self.advance(s3, "pending", 30)
        self.assertEqual(rc, 1)
        self.assertIn("前置", err)
        # s2 走完终态后 s3 放行——门态完全由 TSV 推导
        for i, st in enumerate(("pending", "active", "done")):
            rc, _, err = self.advance(s2, st, 40 + i)
            self.assertEqual(rc, 0, err)
        rc, _, err = self.advance(s3, "pending", 50)
        self.assertEqual(rc, 0, err)
        # 物理承载断言：prereq 标记在 intents.tsv detail 列（TSV 即态）
        latest = self.latest_intents()
        self.assertEqual(self.col(latest[s2], "detail"), "[prereq:" + head + "]")
        self.assertEqual(self.col(latest[s3], "detail"), "[prereq:" + s2 + "]")


if __name__ == "__main__":
    unittest.main()

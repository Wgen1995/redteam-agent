# -*- coding: utf-8 -*-
"""功能5/8·补件三：重派四分类器 replacer（TDD 红测试先行）。

设计源：docs/design/2026-10-20-priority-planner-design.md 补件三——意图终态时
纯机械判（trace 行数+终态标记+产出计数，不 LLM）：
  纯故障重派：trace 零执行+传输故障标记 → 原卡重入池
  接续收口  ：跑了部分断（有产出有终态未达）→ 续接卡带已得结论+剩余步骤
  边界固化  ：否定收口（此路不通）→ 写收口事实，不重派
  完成      ：正常终态

Ruling（写测试即写契约）：
- R-REP-1 「trace 零执行」账本口径=产出计数（facts+findings 归因）与矩阵置格
  归因皆零——timeline 生命周期行（add-intent/状态迁移）不算执行：纯故障卡也有
  领卡行。传输故障标记=blocked 行 reason 前缀 transport-fault（先例=lease-expired
  理由词承载）。
- R-REP-2 纯故障重派动作=先铸 approve 行（approver=planner:replacer，机械审批，
  timeline 全审计）再 blocked→active（--owner=planner:replacer --lease-min=1）：
  原卡内容零改动重入在途集（_AUTHZ_DIFF_ACTIVE 口径）；到期后任意战士经既有
  takeover 重授。不冒充 lease-expired（ dishonest 复活禁）。
- R-REP-3 blocked 其余情形（有产出/非传输故障停摆）=接续收口：续接卡经既有
  add-intent 通道（dedup_key 机械判重=幂等），detail 承载已得结论+剩余步骤；
  原 blocked 卡不动（事件溯源全审计）。
- R-REP-4 边界固化=经既有 add-fact 写收口事实（kind=info，detail 前缀 收口事实:，
  幂等判重=同 intent 已有收口事实不再写）；不重派。
- R-REP-5 lease-expired 回收行=既有自动复活律管辖，重派器不越权（classify=None）。
- R-REP-6 完成=done，零写入。

跑法：python3 -m unittest tests.test_planner_replacer -v
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger import registry  # noqa: E402
from ledger.core import Session, TABLES  # noqa: E402
from ledger import replacer as RP  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
_IS = TABLES["intents.tsv"].index("status")
_IT = TABLES["intents.tsv"].index("title")
_ID = TABLES["intents.tsv"].index("detail")
_IK = TABLES["intents.tsv"].index("kind")
_IP = TABLES["intents.tsv"].index("priority")


def run(gd, cmd, *args):
    """CLI 级既有入口（registry.lookup=goal 写锁包装的执法链），stdout 捕获。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    if rc != 0:
        raise AssertionError("%s 失败 rc=%d: %s" % (cmd, rc, buf.getvalue()))
    return buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self._tmp.name, "G-t"))
        self._n = [0]

    def ts(self):
        self._n[0] += 1
        return "2026-10-20T09:%02d:00Z" % self._n[0]

    def mk(self, title, kind="recon", origin="recon-event", detail="剩余: 逐项打点"):
        run(self.gd, "add-intent",
            "--title=" + title, "--detail=" + detail, "--engine=web-blackbox",
            "--kind=" + kind, "--origin=" + origin, "--budget-share=1;1;1",
            "--priority=0.5", "--timestamp=" + self.ts())
        s = Session(self.gd)
        iid = [r[0] for r in s.rows("intents.tsv") if r[_IT] == title][-1]
        return iid

    def to(self, iid, status, reason=""):
        args = ["--id=" + iid, "--status=" + status, "--timestamp=" + self.ts()]
        if reason:
            args.append("--reason=" + reason)
        run(self.gd, "set-intent-status", *args)

    def latest(self, iid):
        rows = [r for r in Session(self.gd).rows("intents.tsv") if r[0] == iid]
        return rows[-1] if rows else None

    def rows(self, t):
        return Session(self.gd).rows(t)


class TestClassify(Base):
    def test_done_is_complete(self):
        iid = self.mk("正常收口")
        self.to(iid, "active")
        self.to(iid, "done")
        v = RP.classify(Session(self.gd), iid)
        self.assertEqual(v["verdict"], "complete")
        self.assertEqual(v["outputs"], 0)
        self.assertGreaterEqual(v["trace_lines"], 3, "生命周期行须计入 trace")

    def test_pure_fault_signature(self):
        iid = self.mk("断线卡")
        self.to(iid, "active")
        self.to(iid, "blocked", "transport-fault: llmpool 全断")
        v = RP.classify(Session(self.gd), iid)
        self.assertEqual(v["verdict"], "fault-redispatch")
        self.assertEqual(v["outputs"], 0)

    def test_fault_marker_with_outputs_is_continue(self):
        iid = self.mk("半程断线卡")
        self.to(iid, "active")
        run(self.gd, "add-fact", "--intent-id=" + iid, "--kind=info",
            "--target=shop.example", "--detail=已探明管理面", "--confidence=0.9",
            "--timestamp=" + self.ts())
        self.to(iid, "blocked", "transport-fault: 半程断")
        v = RP.classify(Session(self.gd), iid)
        self.assertEqual(v["verdict"], "continue-closeout")
        self.assertEqual(v["outputs"], 1)

    def test_rejected_is_boundary(self):
        iid = self.mk("死路卡", origin="entity")
        self.to(iid, "rejected", "此路不通: WAF 拦截一切 payload")
        v = RP.classify(Session(self.gd), iid)
        self.assertEqual(v["verdict"], "boundary-solidify")

    def test_blocked_no_marker_is_continue(self):
        iid = self.mk("停摆卡")
        self.to(iid, "active")
        self.to(iid, "blocked", "预算中断")
        self.assertEqual(RP.classify(Session(self.gd), iid)["verdict"],
                         "continue-closeout")

    def test_lease_expired_not_replacer_business(self):
        iid = self.mk("租约卡")
        self.to(iid, "active")
        self.to(iid, "blocked", "lease-expired")
        self.assertIsNone(RP.classify(Session(self.gd), iid),
                          "R-REP-5：lease-expired 归自动复活律管辖")

    def test_non_terminal_is_none(self):
        iid = self.mk("在途卡")
        self.assertIsNone(RP.classify(Session(self.gd), iid))
        self.to(iid, "active")
        self.assertIsNone(RP.classify(Session(self.gd), iid))


class TestSweepActions(Base):
    def test_complete_writes_nothing(self):
        iid = self.mk("正常卡")
        self.to(iid, "active")
        self.to(iid, "done")
        before = (len(self.rows("intents.tsv")), len(self.rows("facts.tsv")),
                  len(self.rows("timeline.tsv")), len(self.rows("approvals.tsv")))
        out = RP.sweep(self.gd, self.ts())
        after = (len(self.rows("intents.tsv")), len(self.rows("facts.tsv")),
                 len(self.rows("timeline.tsv")), len(self.rows("approvals.tsv")))
        self.assertEqual(before, after, "完成分类零写入（R-REP-6）")
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["complete"])

    def test_fault_redispatch_reactivates_original_card(self):
        iid = self.mk("断线卡")
        self.to(iid, "active")
        self.to(iid, "blocked", "transport-fault: egress 断连")
        out = RP.sweep(self.gd, self.ts())
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["fault-redispatch"])
        row = self.latest(iid)
        self.assertEqual(row[_IS], "active", "原卡重入在途集")
        self.assertIn("[owner:planner:replacer]", row[_ID])
        self.assertIn("[lease:", row[_ID], "R-REP-2：短租约到期可被战士 takeover")
        aps = [r for r in self.rows("approvals.tsv")
               if r[TABLES["approvals.tsv"].index("decision")] == "approved"
               and "replacer" in r[TABLES["approvals.tsv"].index("note")]]
        self.assertEqual(len(aps), 1, "机械审批恰一行（全审计）")
        # 幂等：active 非终态，二扫不再动作
        RP.sweep(self.gd, self.ts())
        aps2 = [r for r in self.rows("approvals.tsv")
                if "replacer" in r[TABLES["approvals.tsv"].index("note")]]
        self.assertEqual(len(aps2), 1)

    def test_continue_closeout_card_carries_conclusions(self):
        iid = self.mk("半程卡", kind="matrix-test", detail="剩余: 补测注入变体")
        self.to(iid, "active")
        run(self.gd, "add-fact", "--intent-id=" + iid, "--kind=info",
            "--target=admin.shop.example", "--detail=已探明 admin 面存在",
            "--confidence=0.9", "--timestamp=" + self.ts())
        self.to(iid, "blocked", "预算中断")
        out = RP.sweep(self.gd, self.ts())
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["continue-closeout"])
        cont = [r for r in self.rows("intents.tsv")
                if r[_IT] == "续接: 半程卡"]
        self.assertEqual(len(cont), 1, "续接卡恰一张")
        crow = cont[-1]
        self.assertEqual(crow[_IK], "matrix-test", "kind 沿原卡")
        self.assertEqual(crow[_IP], "0.5", "priority 沿原卡")
        for frag in ("续接 " + iid, "已探明 admin 面存在", "剩余: 补测注入变体"):
            self.assertIn(frag, crow[_ID])
        # 幂等：二扫不重复铸续接卡（dedup_key 机械判重）
        RP.sweep(self.gd, self.ts())
        self.assertEqual(len([r for r in self.rows("intents.tsv")
                              if r[_IT] == "续接: 半程卡"]), 1)

    def test_boundary_solidify_writes_closeout_fact(self):
        iid = self.mk("死路卡", origin="entity", detail="探过了")
        self.to(iid, "rejected", "此路不通: WAF 拦截")
        out = RP.sweep(self.gd, self.ts())
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["boundary-solidify"])
        fk, fd = (TABLES["facts.tsv"].index("intent_id"),
                  TABLES["facts.tsv"].index("detail"))
        facts = [r for r in self.rows("facts.tsv") if r[fk] == iid]
        self.assertEqual(len(facts), 1, "收口事实恰一条")
        self.assertTrue(facts[0][fd].startswith("收口事实"), facts[0][fd])
        self.assertIn("此路不通: WAF 拦截", facts[0][fd])
        self.assertEqual([r for r in self.rows("intents.tsv")
                          if r[_IT].startswith("续接:")], [], "否定收口不重派")
        # 幂等
        RP.sweep(self.gd, self.ts())
        self.assertEqual(len([r for r in self.rows("facts.tsv") if r[fk] == iid]), 1)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""战士运行时·账本消费层（W5 战士 MVP）——ledger_io。

零复制消费：写全经 ledger.registry.lookup（goal 写锁包装的既有执法链），
租约语义全用既有 set-intent-status --owner/--lease-min（W2·01P0-2），
prereq/租约解析单源引 ledger.write_cmds（不私铸第二实现）。
timeline 事件行经 ledger.timeline.append_tl_locked（llmpool/tools 同款
基础设施先例——actor=warrior:<id>）。

跑法：python3 -m unittest tests.test_warrior_ledger_io -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger.core import Session, TABLES  # noqa: E402
from warrior import ledger_io  # noqa: E402

_INTENT_COLS = TABLES["intents.tsv"]

W = "warrior:W-1"
T0 = "2026-10-20T08:00:00Z"


class TestLedgerIO(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.io = ledger_io.LedgerIO(self.gd, W)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _cell(self, iid, col):
        rows = [r for r in Session(self.gd).rows("intents.tsv")
                if r[0] == iid]
        return rows[-1][_INTENT_COLS.index(col)] if rows else None

    def test_claimable_lists_pending_only(self):
        ids = [i["id"] for i in self.io.claimable_intents()]
        self.assertIn("INT-g1-0002", ids)
        self.assertNotIn("INT-g1-0001", ids)

    def test_claim_writes_owner_and_lease(self):
        ok, why = self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        self.assertTrue(ok, why)
        self.assertIn("[owner:warrior:W-1]", self._cell("INT-g1-0002",
                                                        "detail"))
        self.assertIn("[lease:2026-10-20T08:30:00Z]",
                      self._cell("INT-g1-0002", "detail"))

    def test_claim_conflict_returns_false(self):
        ok, _ = self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        self.assertTrue(ok)
        other = ledger_io.LedgerIO(self.gd, "warrior:W-2")
        ok2, why2 = other.claim("INT-g1-0002", lease_min=30,
                                ts="2026-10-20T08:10:00Z")
        self.assertFalse(ok2)
        self.assertIn("租约", why2)

    def test_holds_semantics_live_and_expired(self):
        self.io.claim("INT-g1-0002", lease_min=10, ts=T0)
        self.assertTrue(self.io.holds("INT-g1-0002",
                                      ts="2026-10-20T08:05:00Z"))
        self.assertFalse(self.io.holds("INT-g1-0002",
                                       ts="2026-10-20T08:11:00Z"))
        # 他主持有
        other = ledger_io.LedgerIO(self.gd, "warrior:W-2")
        self.assertFalse(other.holds("INT-g1-0002",
                                     ts="2026-10-20T08:05:00Z"))

    def test_owner_of_latest_row(self):
        self.io.claim("INT-g1-0002", lease_min=10, ts=T0)
        owner, expiry = self.io.owner_of("INT-g1-0002")
        self.assertEqual(owner, W)
        self.assertEqual(expiry, "2026-10-20T08:10:00Z")

    def test_complete_sets_done(self):
        self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        ok, why = self.io.complete("INT-g1-0002",
                                   ts="2026-10-20T08:20:00Z")
        self.assertTrue(ok, why)
        self.assertEqual(self._cell("INT-g1-0002", "status"), "done")

    def test_block_records_reason(self):
        self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        ok, why = self.io.block("INT-g1-0002",
                                ts="2026-10-20T08:20:00Z",
                                reason="budget-cap")
        self.assertTrue(ok, why)
        self.assertEqual(self._cell("INT-g1-0002", "status"), "blocked")
        self.assertEqual(self._cell("INT-g1-0002", "reason"), "budget-cap")

    def test_write_routes_through_locked_ledger(self):
        ok, why = self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        self.assertTrue(ok, why)
        rc, out = self.io.write("add-fact", {
            "intent-id": "INT-g1-0002", "kind": "info",
            "target": "shop.example", "detail": " warrior 观察",
            "confidence": "0.8", "timestamp": "2026-10-20T08:05:00Z"})
        self.assertEqual(rc, 0, out)
        facts = Session(self.gd).rows("facts.tsv")
        self.assertTrue(any(r[3] == "shop.example" for r in facts))

    def test_add_tl_lands_row_and_keeps_chain(self):
        self.io.add_tl("warrior-start battle=B", ts=T0)
        from ledger.core import cmd_verify_chain
        self.assertEqual(cmd_verify_chain(self.gd), 0)
        tl = Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any(r[1] == W and "warrior-start" in r[3]
                            for r in tl))

    def test_prereq_chain_serializes_claimable(self):
        # R2 串行链：chain-create 三步，仅 frontier 逐个可领
        rc, out = self.io.write("chain-create", {
            "engine": "web-blackbox", "kind": "recon", "origin": "llm",
            "budget-share": "100;5;0.5",
            "steps": "probe A|probe B|probe C", "timestamp": T0})
        self.assertEqual(rc, 0, out)
        rows = Session(self.gd).rows("intents.tsv")
        step1 = sorted(r[0] for r in rows
                       if r[1] == "probe A")[0]
        step2 = sorted(r[0] for r in rows
                       if r[1] == "probe B")[0]
        # 步 2 提升被 prereq 门拒（写入侧既有执法——前置未终态不进 frontier）
        rc2, out2 = self.io.write("set-intent-status", {
            "id": step2, "status": "pending", "timestamp": T0})
        self.assertNotEqual(rc2, 0, "前置未终态不得进 frontier")
        # 步 1 提升后 claimable 仅步 1（步 2 仍 candidate）
        self.io.write("set-intent-status", {"id": step1, "status": "pending",
                                            "timestamp": T0})
        titles = [i["title"] for i in self.io.claimable_intents()]
        self.assertIn("probe A", titles)
        self.assertNotIn("probe B", titles)
        # 步 1 完成 → 步 2 可提升可领
        self.io.claim(step1, lease_min=30, ts=T0)
        self.io.complete(step1, ts="2026-10-20T08:30:00Z")
        rc3, out3 = self.io.write("set-intent-status", {
            "id": step2, "status": "pending", "timestamp": T0})
        self.assertEqual(rc3, 0, out3)
        titles = [i["title"] for i in self.io.claimable_intents()]
        self.assertIn("probe B", titles)

    def test_my_active_intents_for_resume(self):
        self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        mine = self.io.my_active_intents(ts="2026-10-20T08:05:00Z")
        self.assertEqual([i["id"] for i in mine], ["INT-g1-0002"])
        # 租约过期后不再算持有（须等回收/接管）
        self.assertEqual(self.io.my_active_intents(
            ts="2026-10-20T08:40:00Z"), [])

    def test_priority_orders_claimable(self):
        # 高 priority 在前（intents.priority 列，G-24 K1 算分回填）
        rc, _ = self.io.write("add-intent", {
            "title": "低优先试探", "engine": "web-blackbox",
            "kind": "recon", "origin": "recon-event",
            "budget-share": "10;1;0.1",
            "priority": "0.1", "timestamp": T0})
        self.assertEqual(rc, 0)
        rc, _ = self.io.write("add-intent", {
            "title": "高优先主攻", "engine": "web-blackbox",
            "kind": "recon", "origin": "recon-event",
            "budget-share": "10;1;0.1",
            "priority": "0.9", "timestamp": T0})
        self.assertEqual(rc, 0)
        titles = [i["title"] for i in self.io.claimable_intents()]
        self.assertLess(titles.index("高优先主攻"),
                        titles.index("低优先试探"))


if __name__ == "__main__":
    unittest.main()

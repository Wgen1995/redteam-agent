# -*- coding: utf-8 -*-
"""战士运行时·预算计量（W5 战士 MVP）——token 入 budget.tsv + 触帽停。

跑法：python3 -m unittest tests.test_warrior_budget -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger.core import Session  # noqa: E402
from warrior import budget as wbudget  # noqa: E402
from warrior.ledger_io import LedgerIO  # noqa: E402

W = "warrior:W-1"
T0 = "2026-10-20T08:00:00Z"


class TestBudgetMeter(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.io = LedgerIO(self.gd, W)
        self.io.claim("INT-g1-0002", lease_min=30, ts=T0)
        self.n0 = len(Session(self.gd).rows("budget.tsv"))

    def tearDown(self):
        shutil.rmtree(self.gd)

    def test_charge_lands_budget_row(self):
        m = wbudget.BudgetMeter(self.io, token_cap=1000)
        m.charge("INT-g1-0002", prompt_tokens=300, completion_tokens=50,
                 ts="2026-10-20T08:01:00Z", note="model=m1 turn=1")
        rows = Session(self.gd).rows("budget.tsv")
        self.assertEqual(len(rows), self.n0 + 1)
        row = rows[-1]
        self.assertEqual(row[1], "350")            # token_delta
        self.assertEqual(row[2], "1")              # requests_delta
        self.assertEqual(row[5], "INT-g1-0002")    # scope
        self.assertIn("model=m1", row[6])

    def test_accumulation_and_remaining(self):
        m = wbudget.BudgetMeter(self.io, token_cap=1000)
        m.charge("INT-g1-0002", 300, 50, ts="2026-10-20T08:01:00Z")
        m.charge("INT-g1-0002", 400, 100, ts="2026-10-20T08:02:00Z")
        self.assertEqual(m.used_tokens, 850)
        self.assertEqual(m.remaining_tokens, 150)
        self.assertFalse(m.exhausted())

    def test_cap_exhaustion_flag(self):
        m = wbudget.BudgetMeter(self.io, token_cap=500)
        m.charge("INT-g1-0002", 300, 50, ts="2026-10-20T08:01:00Z")
        self.assertFalse(m.exhausted())
        m.charge("INT-g1-0002", 300, 50, ts="2026-10-20T08:02:00Z")
        self.assertTrue(m.exhausted(), "700>500 触帽")

    def test_charge_without_intent_scopes_goal(self):
        m = wbudget.BudgetMeter(self.io, token_cap=1000)
        m.charge("", 10, 5, ts="2026-10-20T08:00:30Z")
        rows = Session(self.gd).rows("budget.tsv")
        self.assertEqual(rows[-1][5], "goal")

    def test_total_charge_count(self):
        m = wbudget.BudgetMeter(self.io, token_cap=1000)
        for i in range(3):
            m.charge("INT-g1-0002", 10, 5,
                     ts="2026-10-20T08:0%d:00Z" % i)
        self.assertEqual(m.requests, 3)


if __name__ == "__main__":
    unittest.main()

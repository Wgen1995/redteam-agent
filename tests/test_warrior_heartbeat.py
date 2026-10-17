# -*- coding: utf-8 -*-
"""战士运行时·心跳与停滞（W5 战士 MVP）。

心跳=每 N 分钟 timeline 心跳行（P-lifecycle 基础设施轨）；停滞=无进展行
超时 → StallDetected（自杀重生信号，租约超时回收既有机制接管）。

跑法：python3 -m unittest tests.test_warrior_heartbeat -v
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
from warrior import heartbeat as whb  # noqa: E402
from warrior.ledger_io import LedgerIO  # noqa: E402
from tests.test_warrior_fake_model import FakeClock  # noqa: E402

W = "warrior:W-1"


def iso(epoch):
    import datetime
    return datetime.datetime.fromtimestamp(
        epoch, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TestHeartbeat(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.io = LedgerIO(self.gd, W)
        self.clock = FakeClock(start=1770000000.0)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _hb(self, interval_min=5, stall_min=15):
        return whb.Heartbeat(self.io, interval_min=interval_min,
                             stall_min=stall_min, now=self.clock)

    def test_first_beat_lands_timeline_row(self):
        hb = self._hb()
        self.assertTrue(hb.beat(intent="INT-x",
                                extra="tokens=100"))
        tl = Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any("warrior-heartbeat" in r[3] for r in tl[-2:]))

    def test_beat_throttled_within_interval(self):
        hb = self._hb(interval_min=5)
        self.assertTrue(hb.beat(intent="INT-x"))
        self.clock.advance(60 * 3)
        self.assertFalse(hb.beat(intent="INT-x"), "3<5min 不重复心跳")
        self.clock.advance(60 * 3)
        self.assertTrue(hb.beat(intent="INT-x"), "6≥5min 再跳")

    def test_progress_resets_stall_window(self):
        hb = self._hb(stall_min=15)
        hb.beat(intent="INT-x")
        self.clock.advance(60 * 10)
        hb.progress()
        self.clock.advance(60 * 14)
        hb.check_stall(intent="INT-x")      # 距进展 14<15min：不抛
        self.clock.advance(60 * 2)
        with self.assertRaises(whb.StallDetected):
            hb.check_stall(intent="INT-x")

    def test_no_progress_since_start_stalls(self):
        hb = self._hb(stall_min=15)
        hb.beat(intent="INT-x")
        self.clock.advance(60 * 16)
        with self.assertRaises(whb.StallDetected) as cm:
            hb.check_stall(intent="INT-x")
        self.assertIn("INT-x", str(cm.exception))

    def test_iso_helper_epoch_to_z(self):
        self.assertEqual(whb.iso_of(1770000000.0),
                         "2026-02-02T02:40:00Z")


if __name__ == "__main__":
    unittest.main()

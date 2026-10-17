# -*- coding: utf-8 -*-
"""战士运行时·定向转向钩子（W5 战士 MVP · 质量律 R5）。

say 定向意图=steer（对话派活过门后的定向注入）；kill=stop 扩展。
事件行单源由本模块铸造：warrior-steer target=<id> text=<…> /
warrior-stop warrior=<id> reason=<…>（actor=总控，对话层先例）。

跑法：python3 -m unittest tests.test_warrior_steer -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from warrior import steer  # noqa: E402

W = "warrior:W-1"
T0 = "2026-10-20T08:00:00Z"


class TestSteer(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def test_write_and_read_steer_for_target(self):
        steer.write_steer(self.gd, W, "优先打 admin 面板", ts=T0)
        st = steer.scan(self.gd, W, after_idx=0)
        self.assertEqual(st.steers, ["优先打 admin 面板"])
        self.assertIsNone(st.stop_reason)

    def test_other_warrior_steer_ignored(self):
        steer.write_steer(self.gd, "warrior:W-2", "别人的活", ts=T0)
        st = steer.scan(self.gd, W, after_idx=0)
        self.assertEqual(st.steers, [])

    def test_stop_signal_read(self):
        steer.write_stop(self.gd, W, reason="operator-halt", ts=T0)
        st = steer.scan(self.gd, W, after_idx=0)
        self.assertEqual(st.stop_reason, "operator-halt")

    def test_scan_respects_after_idx(self):
        steer.write_steer(self.gd, W, "第一条", ts=T0)
        idx_after_first = steer.scan(self.gd, W, after_idx=0).seen_idx
        steer.write_steer(self.gd, W, "第二条",
                          ts="2026-10-20T08:05:00Z")
        st = steer.scan(self.gd, W, after_idx=idx_after_first)
        self.assertEqual(st.steers, ["第二条"])

    def test_event_line_shape(self):
        steer.write_steer(self.gd, W, "转向甲", ts=T0)
        steer.write_stop(self.gd, W, reason="halt", ts=T0)
        from ledger.timeline import read_rows
        evs = [r[3] for r in read_rows(self.gd)]
        self.assertTrue(any(e.startswith(
            "warrior-steer target=warrior:W-1 text=转向甲") for e in evs))
        self.assertTrue(any(e.startswith(
            "warrior-stop warrior=warrior:W-1 reason=halt") for e in evs))


if __name__ == "__main__":
    unittest.main()

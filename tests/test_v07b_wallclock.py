# -*- coding: utf-8 -*-
"""v0.7b wall_clock 双轨：clock-sync 事件轨+断连窗口检出（纯函数面）。"""
import datetime
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import wallclock as wc  # noqa: E402


def _row(ev):
    return {"event": ev, "ts": "2026-10-11T10:00:00Z"}


class TestDetectGaps(unittest.TestCase):
    def test_empty_track_no_gaps(self):
        self.assertEqual(wc.detect_gaps([_row("probe")]), [])

    def test_gap_detected(self):
        rows = [
            _row("clock-sync wall=2026-10-11T10:00:00Z phase=P0"),
            _row("clock-sync wall=2026-10-11T12:30:00Z phase=P4"),
        ]
        gaps = wc.detect_gaps(rows, min_sec=900)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0][1], 9000)

    def test_small_gap_ignored(self):
        rows = [
            _row("clock-sync wall=2026-10-11T10:00:00Z phase=P0"),
            _row("clock-sync wall=2026-10-11T10:05:00Z phase=P1"),
        ]
        self.assertEqual(wc.detect_gaps(rows, min_sec=900), [])

    def test_malformed_wall_ignored(self):
        rows = [
            _row("clock-sync wall=notatime phase=P0"),
            _row("clock-sync wall=2026-10-11T12:00:00Z phase=P4"),
        ]
        self.assertEqual(wc.detect_gaps(rows, min_sec=900), [])


class TestFormat(unittest.TestCase):
    def test_event_format(self):
        ev = wc.event_text("P0", "battle-init")
        self.assertTrue(ev.startswith("clock-sync wall="))
        self.assertIn("phase=P0", ev)
        self.assertIn("note=battle-init", ev)
        # wall 值必须是可解析 ISO
        wall = ev.split("wall=")[1].split()[0]
        datetime.datetime.fromisoformat(wall.replace("Z", "+00:00"))


if __name__ == "__main__":
    unittest.main()

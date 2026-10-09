# -*- coding: utf-8 -*-
"""runner 看门狗四件套单测（b10 TDD）。

纯函数面：cli/ledger/watchdog.py——分级击杀/指数退避/指令注入/自适应节流。"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'cli'))
from ledger import watchdog  # noqa: E402


class TestStallGrade(unittest.TestCase):
    def test_ok_below_soft(self):
        self.assertEqual(watchdog.stall_grade(0), 'ok')
        self.assertEqual(watchdog.stall_grade(179.9), 'ok')

    def test_soft_at_and_above(self):
        self.assertEqual(watchdog.stall_grade(180), 'soft')
        self.assertEqual(watchdog.stall_grade(300), 'soft')

    def test_hard_at_and_above(self):
        self.assertEqual(watchdog.stall_grade(480), 'hard')
        self.assertEqual(watchdog.stall_grade(3600), 'hard')

    def test_custom_thresholds(self):
        self.assertEqual(watchdog.stall_grade(60, soft=50, hard=100), 'soft')
        self.assertEqual(watchdog.stall_grade(100, soft=50, hard=100), 'hard')


class TestBackoffDelay(unittest.TestCase):
    def test_schedule_30_120_480_cap(self):
        self.assertEqual(watchdog.backoff_delay(1), 30)
        self.assertEqual(watchdog.backoff_delay(2), 120)
        self.assertEqual(watchdog.backoff_delay(3), 480)
        self.assertEqual(watchdog.backoff_delay(9), 480)

    def test_first_restart_no_delay_semantics(self):
        self.assertEqual(watchdog.backoff_delay(0), 0)

    def test_custom_base(self):
        self.assertEqual(watchdog.backoff_delay(1, base=10), 10)
        self.assertEqual(watchdog.backoff_delay(2, base=10), 40)


class TestReadDirective(unittest.TestCase):
    def test_missing_file_is_none(self):
        text, digest = watchdog.read_directive('/nonexistent/directive.txt', None)
        self.assertIsNone(text)
        self.assertIsNone(digest)

    def test_new_content_detected_once(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write('强度放宽：允许低速扫描')
            path = f.name
        try:
            text1, d1 = watchdog.read_directive(path, None)
            self.assertIn('强度放宽', text1)
            text2, d2 = watchdog.read_directive(path, d1)
            self.assertIsNone(text2)
            self.assertEqual(d2, d1)
            with open(path, 'w') as f:
                f.write('补令2：扩范围 10.0.0.0/24')
            text3, d3 = watchdog.read_directive(path, d1)
            self.assertIn('补令2', text3)
            self.assertNotEqual(d3, d1)
        finally:
            os.unlink(path)


class TestAdaptiveTick(unittest.TestCase):
    def test_active_floors_to_one_sec(self):
        self.assertEqual(watchdog.next_tick(True, tick=10.0), 1.0)

    def test_idle_returns_tick(self):
        self.assertEqual(watchdog.next_tick(False, tick=10.0), 10.0)

    def test_floor_param(self):
        self.assertEqual(watchdog.next_tick(True, tick=30.0, floor=2.0), 2.0)


if __name__ == '__main__':
    unittest.main()

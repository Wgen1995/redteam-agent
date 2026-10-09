# -*- coding: utf-8 -*-
"""gateloop 核单测（b11）。"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'cli'))
from ledger import gateloop_core as gc  # noqa: E402


class TestBuildGatePrompt(unittest.TestCase):
    def test_p0_carries_mission_and_scope_law(self):
        p = gc.build_gate_prompt("任务书正文", "P0")
        self.assertIn("任务书正文", p)
        self.assertIn("P0", p)
        self.assertIn("phases/P0.md", p)
        self.assertIn("禁止推进到下一门", p)
        self.assertNotIn("续跑", p)  # P0 无续跑导语

    def test_p1_plus_has_resume_preamble(self):
        p = gc.build_gate_prompt("任务书正文", "P3")
        self.assertIn("恢复协议", p)
        self.assertIn("phases/P3.md", p)

    def test_bad_phase_raises(self):
        with self.assertRaises(ValueError):
            gc.build_gate_prompt("x", "P5")


class TestGateArgv(unittest.TestCase):
    def test_form_is_phase_flag(self):
        self.assertEqual(gc.gate_argv("/tmp/g", "P2"),
                         ["gate", "--goal-dir", "/tmp/g", "--phase", "P2"])

    def test_bad_phase_raises(self):
        with self.assertRaises(ValueError):
            gc.gate_argv("/tmp/g", "P9")


class TestNextPhase(unittest.TestCase):
    def test_seq_walk(self):
        self.assertEqual(gc.next_phase([]), "P0")
        self.assertEqual(gc.next_phase(["P0"]), "P1")
        self.assertEqual(gc.next_phase(["P0", "P1", "P2", "P3"]), "P4")

    def test_done_after_p4(self):
        self.assertIsNone(gc.next_phase(["P0", "P1", "P2", "P3", "P4"]))

    def test_garbage_tolerated(self):
        self.assertEqual(gc.next_phase(["P0", "PX", "P1"]), "P2")


if __name__ == '__main__':
    unittest.main()

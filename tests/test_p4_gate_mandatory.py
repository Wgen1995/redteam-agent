# -*- coding: utf-8 -*-
"""批次4 T3：P4 重放门断言转强制——expect 文本去 SKIP 后 gate 不再记 skip。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PHASES_CLI = os.path.join(ROOT, "cli", "tanyin-phases")
YAML = os.path.join(ROOT, "phases", "phases.yaml")


class TestP4GateMandatory(unittest.TestCase):
    def test_yaml_expect_no_skip_marker(self):
        text = open(YAML, encoding="utf-8").read()
        self.assertNotIn("批次 4 前=SKIP", text, "P4 断言 expect 仍含 SKIP 标记（批4 已转强制）")
        self.assertIn("ledger-replay-summary", text)

    def test_protocol_retired_note(self):
        text = open(os.path.join(ROOT, "phases", "PROTOCOL.md"), encoding="utf-8").read()
        self.assertIn("已退役", text, "PROTOCOL §1 SKIP 判定行须标注已退役（2026-09-24 批4）")


if __name__ == "__main__":
    unittest.main()

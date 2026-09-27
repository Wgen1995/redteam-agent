# -*- coding: utf-8 -*-
"""批次 7 T1：账本写路径原子化（C1）。红=半写中断旧内容零损反例——
现状 core.py:55 open(w) 原地截断：写途中崩溃=旧账本丢失（专家 SIGKILL 8/8 丢史根因）。"""
import os, sys, tempfile, unittest
from unittest import mock
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))
from ledger import core
from ledger.write_cmds import Ctx
from ledger.core import Session

class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)

    def test_write_tsv_replace_crash_keeps_old_intact(self):
        p = os.path.join(self.d.name, "timeline.tsv")
        core.write_tsv(p, [["a", "b"], ["c", "d"]])
        with open(p, "rb") as f:
            old = f.read()
        with mock.patch("os.replace", side_effect=OSError(5, "模拟 replace 前夕崩溃")):
            with self.assertRaises(OSError):
                core.write_tsv(p, [["x", "y"]])
        with open(p, "rb") as f:
            self.assertEqual(f.read(), old, "旧账本零损（原子性定义：要么旧版要么新版）")
        self.assertFalse(os.path.exists(p + ".tmp"), "tmp 残留必须清扫（撕裂态 A 源头）")

    def test_ctx_write_file_replace_crash_keeps_old_intact(self):
        gd = os.path.join(self.d.name, "G-at"); os.makedirs(gd)
        Session(gd)  # 夹具空会话即可（Ctx 只需 dir）
        ctx = Ctx(gd)
        ctx.write_file("attachments/x.txt", "v1")
        p = os.path.join(gd, "attachments", "x.txt")
        with open(p, "rb") as f:
            old = f.read()
        with mock.patch("os.replace", side_effect=OSError(5, "boom")):
            with self.assertRaises(OSError):
                ctx.write_file("attachments/x.txt", "v2")
        with open(p, "rb") as f:
            self.assertEqual(f.read(), old)
        self.assertFalse(os.path.exists(p + ".tmp"))

    def test_write_tsv_lf_discipline_unchanged(self):
        p = os.path.join(self.d.name, "t.tsv")
        core.write_tsv(p, [["a", "b"]])
        with open(p, "rb") as f:
            self.assertNotIn(b"\r", f.read(), "LF 字节纪律不回退")

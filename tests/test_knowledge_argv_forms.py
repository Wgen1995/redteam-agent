# -*- coding: utf-8 -*-
"""批次5 T19：tanyin-knowledge argv 双形态归一（R-T19-2）——P6 duty 命令化五步与
出口补充判定命令按计划原文均取 --key value 空格形态，且入口 parse_kdir 已双形态
（--knowledge-dir X 与 = 形两收）；子命令参数解析仅收 = 形=文档命令不可跑（lint
空格形实况 TypeError 裸崩 rc1，出口补充判定「lint --today 2026-09-24 exit 0」不可
满足）。归一后空格形并入既有 query_cmds.parse_kv 单源（账本 44 面零触碰）；= 形
行为零变（既有知识库 53 例+金样 kn 三面回归背书）。探针在 tmp 副本跑（种子库零写热）。"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class TestArgvDualForm(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = os.path.join(self.td.name, "knowledge")
        shutil.copytree(SEED, self.d)

    def tearDown(self):
        self.td.cleanup()

    def test_lint_space_form_today(self):
        r = kn("lint", "--knowledge-dir", self.d, "--today", "2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_match_space_form_args(self):
        r = kn("match", "--knowledge-dir", self.d, "--client", "CLIENT-01",
               "--asset", "CTF 练习靶场 PHP 应用（占位符化组件描述；真平台与端口已脱敏）",
               "--today", "2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PR-0001", r.stdout, "[expired] 标注行亦为可检索形态")

    def test_bare_flag_clean_usage_error(self):
        # 裸旗标（后无值）= 归一为 =1；lint 对非法时间值走 KnowledgeError=体面 exit 2
        r = kn("lint", "--knowledge-dir", self.d, "--today")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("环境问题", r.stderr)

    def test_equals_form_unchanged(self):
        r = kn("lint", "--knowledge-dir=" + self.d, "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()

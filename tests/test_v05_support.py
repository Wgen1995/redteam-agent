# -*- coding: utf-8 -*-
"""v0.5a F6/F7/F8：launchd 模板+caffeinate / 命令面单源 / GT 出仓（SRE+兼容+eval integrity）。"""
import os, plistlib, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import selfcheck  # noqa: E402


class TestLaunchdTemplate(unittest.TestCase):
    def test_plist_parses_with_keepalive(self):
        p = os.path.join(ROOT, "install", "launchd", "com.tanyin.runner.plist")
        with open(p, "rb") as f:
            pl = plistlib.load(f)
        self.assertTrue(pl.get("KeepAlive"))
        self.assertIn("ProgramArguments", pl)
        self.assertTrue(pl["ProgramArguments"])


class TestCommandFaceSingleSource(unittest.TestCase):
    def test_skill_index_sync_extractor(self):
        # 抽取器：从 SKILL.md 文本抽命令索引词集
        text = ("## 命令索引（45 条）\n写 2：add-goal add-scope\n"
                "校验 1：validate anchor（注释不计）\n")
        s = selfcheck.skill_index_commands(text)
        self.assertEqual(s, {"add-goal", "add-scope", "validate", "anchor"})

    def test_repo_skill_indexes_agree(self):
        a = selfcheck.skill_index_commands(
            open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read())
        b = selfcheck.skill_index_commands(
            open(os.path.join(ROOT, ".opencode", "skills", "tanyin", "SKILL.md"),
                 encoding="utf-8").read())
        self.assertEqual(a, b, "根 SKILL 与 .opencode SKILL 命令索引漂移")


class TestGtOutOfRepo(unittest.TestCase):
    def test_mission_clean(self):
        self.assertFalse(selfcheck.mission_clean("看 tests/range/ground-truth.json"))
        self.assertFalse(selfcheck.mission_clean("ground-truth 路径在 /x"))
        self.assertTrue(selfcheck.mission_clean("正常任务书，无真相泄漏"))


if __name__ == "__main__":
    unittest.main()

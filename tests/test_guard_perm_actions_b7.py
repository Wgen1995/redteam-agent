# -*- coding: utf-8 -*-
"""批次 7 T15：permitted_actions 执法接线（High：零执法——grep guard/replay/enforce
对 permitted_actions 零引用，凭据越权动作无门）+guard --timeout 通道（Medium：60s
硬超时无参数收口）。

裁决（R-T15，详见 HANDOFF）：
- 多值分隔与 write_cmds._mv 同语义=分号（计划片段 split(",") 按计划自身「以 _mv
  实现对齐」条款纠正）；covered=全部生效 account-grant 行 permitted_actions 并集
  （write_cmds add-cred 覆盖校验 :1086-1088 同口径）。
- 门链次序=deny-list → scope → permitted_actions → request-ticket；拒绝事件词
  guard-reject permitted-actions 落账（append_tl 单通道）。
- 夹具=tests/fixtures/G-g1 拷贝（fresh 目录 add-scope 撞 Tier0 硬门，R-T11-1 同律；
  既有凭据 CRED-g1-0001 直接补 account-grant 行，免 add-cred 闭合链）。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger.enforce import permitted_actions_covered
from ledger import core

GUARD = os.path.join(ROOT, "cli", "tanyin-guard")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T12:00:00Z"
TAB = chr(9)
PY = sys.executable
NOOP = [PY, "-c", "pass"]


def g(gd, sub, *args):
    return subprocess.run([PY, GUARD, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def ledger(gd, cmd, *args):
    return subprocess.run([PY, LEDGER, cmd, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestPermActions(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-pa"))
        # 夹具：既有凭据 CRED-g1-0001 补 account-grant(read) 覆盖行
        # （_scope_common：kind=account-grant 须 account＋permitted_actions＋matcher）
        # matcher=语法占位（grant.example）——防撞 load_scope 同 matcher 修正键（R-T15）
        r = ledger(self.gd, "add-scope", "--kind=account-grant",
                   "--matcher=grant.example", "--account=CRED-g1-0001",
                   "--permitted-actions=read", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unit_covered_semantics(self):
        s = core.Session(self.gd)
        self.assertTrue(permitted_actions_covered(s, "CRED-g1-0001", "read"))
        self.assertFalse(permitted_actions_covered(s, "CRED-g1-0001", "write"),
                         "覆盖=并集精确命中，非子串")
        self.assertFalse(permitted_actions_covered(s, "CRED-g1-404", "read"),
                         "无 grant 行=无覆盖")

    def test_unit_multi_value_semicolon_union(self):
        """多值分隔与 write_cmds._mv 同语义（分号）——第二 grant 行并入并集。"""
        r = ledger(self.gd, "add-scope", "--kind=account-grant", "--matcher=grant.example",
                   "--account=CRED-g1-0001", "--permitted-actions=probe;deploy",
                   "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = core.Session(self.gd)
        self.assertTrue(permitted_actions_covered(s, "CRED-g1-0001", "probe"))
        self.assertTrue(permitted_actions_covered(s, "CRED-g1-0001", "deploy"))
        self.assertFalse(permitted_actions_covered(s, "CRED-g1-0001", "readprobe"),
                         "分号分隔并集，禁子串假阳性")

    def test_guard_rejects_uncovered_action(self):
        r = g(self.gd, "exec", "--cred=CRED-g1-0001", "--action=write", "--", *NOOP)
        self.assertEqual(r.returncode, 1, "红现状：write 对只读 cred 照跑 rc=0（零执法）: "
                         + r.stdout + r.stderr)
        self.assertIn("permitted-actions", r.stdout)
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("guard-reject permitted-actions", tl, "拒绝必须留痕")
        self.assertIn("cred=CRED-g1-0001", tl)
        self.assertIn("action=write", tl)

    def test_guard_rejects_cred_without_grant_row(self):
        r = g(self.gd, "exec", "--cred=CRED-g1-404", "--action=read", "--", *NOOP)
        self.assertEqual(r.returncode, 1, "无 account-grant 行=无覆盖面")
        self.assertIn("account-grant", r.stdout)
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            self.assertIn("guard-reject permitted-actions", f.read())

    def test_guard_allows_covered_action(self):
        r = g(self.gd, "exec", "--cred=CRED-g1-0001", "--action=read", "--", *NOOP)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("request-ticket", tl, "过审照常取票（门链不断）")
        self.assertNotIn("guard-reject permitted-actions", tl)

    def test_inject_requires_action_with_cred(self):
        r = g(self.gd, "inject", "--cred=1", "--", "echo", "x")
        self.assertEqual(r.returncode, 2, "inject+cred 缺 --action=usage 错（凭据必有意图动作）: "
                         + r.stdout + r.stderr)


class TestTimeout(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-to"))

    def test_timeout_channel(self):
        r = g(self.gd, "exec", "--timeout=1", "--", PY, "-c", "import time; time.sleep(5)")
        self.assertNotEqual(r.returncode, 0, "超时=非零（红现状：硬 60s，1s 不生效）: "
                            + r.stdout + r.stderr)
        self.assertIn("timeout", (r.stdout + r.stderr).lower(), "输出须点名 timeout")

    def test_timeout_invalid_exit_2(self):
        r = g(self.gd, "exec", "--timeout=abc", "--", "echo", "x")
        self.assertEqual(r.returncode, 2, "非整数=usage 错")
        r = g(self.gd, "exec", "--timeout=9999", "--", "echo", "x")
        self.assertEqual(r.returncode, 2, "超上限 600=usage 错")
        r = g(self.gd, "exec", "--timeout=0", "--", "echo", "x")
        self.assertEqual(r.returncode, 2, "下界 1（0=usage 错）")


if __name__ == "__main__":
    unittest.main()

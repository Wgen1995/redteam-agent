# -*- coding: utf-8 -*-
"""批次 6 T6：tanyin-selfcheck 六项静态验证+guided 手测引导+交战区分离机检（TDD 红→绿）。

六项：cmd-index / encoding / phases-schema / layout / lock-verify / golden。
仓内自检形态全过=exit 0（openssl 缺→lock-verify rc=2，全绿出口随 max=2——ENV 语义）。"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import selfcheck  # noqa: E402

SIX = ["cmd-index", "encoding", "phases-schema", "layout", "lock-verify", "golden",
       "skill-index-sync"]  # v0.5a F7：第七检查（根/.opencode SKILL 索引同集）


class TestStatic(unittest.TestCase):
    def test_repo_mode_all_pass(self):
        rc, items = selfcheck.run_static(None, None, REPO)
        names = [n for n, _, _ in items]
        self.assertEqual(names, SIX)
        self.assertEqual(rc, 0, items)   # 仓内自检形态全过（openssl 缺→lock-verify rc=2 仍全绿出口=2）

    def test_encoding_catches_bom(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.md"), "wb") as f:
                f.write(b"\xef\xbb\xbfbad")
            self.assertEqual(selfcheck.check_encoding(d), 1)

    def test_encoding_catches_crlf(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.py"), "wb") as f:
                f.write(b"a\r\nb\n")
            self.assertEqual(selfcheck.check_encoding(d), 1)

    def test_encoding_clean_dir_ok(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "ok.md"), "wb") as f:
                f.write("正常\n".encode("utf-8"))
            self.assertEqual(selfcheck.check_encoding(d), 0)

    def test_layout_separation(self):
        with tempfile.TemporaryDirectory() as d0:
            # 交战区在安装树内=layout rc=1（§3.4 反例）
            self.assertEqual(
                selfcheck.check_layout(os.path.join(d0, "ir"), os.path.join(d0, "ir", "home")), 1)
            # 分居形态=0
            self.assertEqual(
                selfcheck.check_layout(os.path.join(d0, "ir"), os.path.join(d0, "home")), 0)

    def test_cmd_index_catches_unknown_tool(self):
        with tempfile.TemporaryDirectory() as d:
            ph = os.path.join(d, "phases")
            os.makedirs(ph)
            with open(os.path.join(ph, "PX.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("先跑 tanyin-nosuchtool frobnicate 再收工\n")
            self.assertEqual(selfcheck.check_cmd_index(d), 1)

    def test_cmd_index_catches_unregistered_sub(self):
        with tempfile.TemporaryDirectory() as d:
            ph = os.path.join(d, "phases")
            os.makedirs(ph)
            with open(os.path.join(ph, "PX.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("py -3 cli/tanyin-ledger no-such-command\n")
            self.assertEqual(selfcheck.check_cmd_index(d), 1)

    def test_cmd_index_known_reference_ok(self):
        with tempfile.TemporaryDirectory() as d:
            ph = os.path.join(d, "phases")
            os.makedirs(ph)
            with open(os.path.join(ph, "PX.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("py -3 cli/tanyin-ledger validate\n")
            self.assertEqual(selfcheck.check_cmd_index(d), 0)

    def test_known_commands_covers_live_ledger_face(self):
        # 冻结面 ⊇ registry 现役面——新增命令忘记登记=本测试红（机械 tripwire）
        from ledger import registry
        self.assertTrue(set(registry.all_commands()) <= set(selfcheck.KNOWN_COMMANDS["ledger"]))


class TestGuided(unittest.TestCase):
    def test_guided_output_contract(self):
        txt = selfcheck.run_guided("walcode")
        for key in ("安装命令", "能力探测", "冒烟清单", "回传模板", "probe_results", "未实测"):
            self.assertIn(key, txt)

    def test_guided_reflects_verification_label(self):
        self.assertIn("静态验证+待实测", selfcheck.run_guided("walcode"))
        self.assertIn("本仓可实测", selfcheck.run_guided("dsh"))

    def test_unknown_host(self):
        with self.assertRaises(SystemExit):
            selfcheck.run_guided("nonexistent")   # exit 2 用法错误


if __name__ == "__main__":
    unittest.main()

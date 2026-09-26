# -*- coding: utf-8 -*-
"""批次 6 T8：五宿主矩阵落地——宿主模板直读+AGENTS 系统级注入（渲染/幂等/护栏）。"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import hosts_matrix  # noqa: E402

REPO = os.path.dirname(HERE)
FIVE = ("dsh", "opencode", "codex", "walcode", "codebuddy")


class TestTemplates(unittest.TestCase):
    def test_all_five_valid(self):
        for h in FIVE:
            d = hosts_matrix.host_compat(REPO, h)
            self.assertIn(d["egress_default_tier"], (1, 3))
            self.assertTrue(d["compat"])

    def test_blind_spot_hosts_marked(self):
        for h in ("walcode", "codebuddy"):
            self.assertIn("待实测", hosts_matrix.host_compat(REPO, h)["verification"])
            self.assertEqual(hosts_matrix.host_compat(REPO, h)["egress_default_tier"], 1)

    def test_unknown_host_red(self):
        with self.assertRaises(FileNotFoundError):
            hosts_matrix.host_compat(REPO, "no-such-host")

    def test_tier3_hosts(self):
        for h in ("dsh", "opencode", "codex"):
            self.assertEqual(hosts_matrix.host_compat(REPO, h)["egress_default_tier"], 3)


class TestInject(unittest.TestCase):
    def test_idempotent_block(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "AGENTS.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("# host config\n")
            block = hosts_matrix.render_agents_inject(REPO, "dsh")
            hosts_matrix.inject_agents(p, block)
            with open(p, encoding="utf-8") as f:
                first = f.read()
            hosts_matrix.inject_agents(p, block)
            with open(p, encoding="utf-8") as f:
                self.assertEqual(f.read(), first)   # 二次注入零变更
            self.assertIn("<!--TANYIN:BEGIN-->", first)
            self.assertIn("<!--TANYIN:END-->", first)
            self.assertIn("Tier 3", first)          # 档位事实披露在块内（铁律 5）
            self.assertTrue(first.startswith("# host config"))   # 既有内容保留

    def test_inject_len_capped(self):
        block = hosts_matrix.render_agents_inject(REPO, "dsh")
        self.assertLess(len(block), 8000, "常驻注入 <2K token 量级护栏（≈4 char/token）")

    def test_blind_spot_disclosure_in_block(self):
        # 盲区宿主：Tier 1 保守披露+待实测标注进注入块（G-38 待实测回传后升档）
        block = hosts_matrix.render_agents_inject(REPO, "walcode")
        self.assertIn("Tier 1", block)
        self.assertIn("待实测", block)

    def test_lf_and_utf8(self):
        # LF 字节纪律：注入后文件无 CRLF
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "AGENTS.md")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("# host config\n")
            hosts_matrix.inject_agents(p, hosts_matrix.render_agents_inject(REPO, "dsh"))
            with open(p, "rb") as f:
                self.assertNotIn(b"\r", f.read())


if __name__ == "__main__":
    unittest.main()

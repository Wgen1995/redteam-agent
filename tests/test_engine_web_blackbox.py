# -*- coding: utf-8 -*-
"""批次4 T7：web-blackbox 引擎结构 lint——预算/段映射/命令引用/关键语义在场。"""
import os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ENG = os.path.join(ROOT, "engines", "web-blackbox")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import registry  # noqa: E402

KNOWN = registry.all_commands() | {
    "tanyin-guard", "tanyin-canary", "tanyin-egress", "tanyin-redact",
    "tanyin-budgetctl", "tanyin-phases", "tanyin-ledger",
    "tanyin-report", "tanyin-viz", "tanyin-replay"}


def tokens(text):
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk + (len(text) - cjk + 3) // 4


def read(*p):
    return open(os.path.join(ENG, *p), encoding="utf-8").read()


class TestWebBlackboxEngine(unittest.TestCase):
    def test_manifest_fields(self):
        text = read("MANIFEST.md")
        for f in ("name", "kind", "version", "适用场景", "参数", "产物路径", "超时",
                  "重试策略", "幂等键", "纪律能力声明", "工具依赖", "验签公钥"):
            self.assertIn(f, text, "MANIFEST 缺字段 " + f)
        self.assertIn("kind: skill", text)

    def test_skill_budget_and_mapping(self):
        text = read("SKILL.md")
        self.assertLess(tokens(text), 2000, "引擎 SKILL ≤2K 恒载")
        for kind in ("recon", "surface", "matrix-test", "deep-dive", "authz-diff"):
            self.assertIn(kind, text, "kind→段映射缺 " + kind)

    def test_four_segments_budget(self):
        for seg, cap in (("recon", 1500), ("surface", 1500), ("test", 1500), ("differential", 1500)):
            text = read("phases", seg + ".md")
            self.assertLess(tokens(text), cap, seg + " 段 ≤1.5K")
        self.assertIn("authz-diff", read("phases", "differential.md"), "差分段须挂 authz-diff")

    def test_differential_semantics(self):
        text = read("phases", "differential.md")
        for kw in ("pair_group", "对照组", "单变量", "两次", "errorCode", "authz-diff:",
                   "auth_context", "幂等读", "account-grant"):
            self.assertIn(kw, text, "差分段缺关键语义 " + kw)

    def test_recon_a1_a8_channels(self):
        text = read("phases", "recon.md")
        for i in range(1, 9):
            self.assertIn("A%d" % i, text, "recon 段 A1-A8 通道表缺 A%d" % i)
        for t in ("cloud-storage", "human-factor"):
            self.assertIn(t, text, "G-12 新 type 未入 recon 落账表")

    def test_patterns_exist(self):
        ok = read("patterns", "submission-ok.md")
        for f in ("intent_id", "engine", "status", "facts", "findings", "assets",
                  "edges", "creds", "operations_log", "pair_group", "expected_matcher"):
            self.assertIn(f, ok)

    def test_referenced_commands_known(self):
        for dirpath, _dirs, files in os.walk(ENG):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                text = open(os.path.join(dirpath, fn), encoding="utf-8").read()
                for m in re.finditer(r"(?:ledger-|tanyin-)([a-z][a-z0-9-]*)", text):
                    self.assertIn(m.group(0).rstrip("-"), KNOWN | registry.all_commands(),
                                  "%s 引用未知命令: %s" % (fn, m.group(0)))

    def test_horizon_coupling(self):
        """图谱驱动增补 71d3b7c：horizon 可达空格驱动侦察/测试段（最小咬合）。"""
        for seg in ("recon", "test"):
            self.assertIn("graph-horizon", read("phases", seg + ".md"),
                          seg + " 段须挂 graph-horizon 可达空格驱动（设计增补 71d3b7c）")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""批次 3 T9/T10：常驻集 <2K token + SKILL 结构 lint + 命令索引一致性 + 九门 md 齐备。"""
import os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import registry

SKILL = os.path.join(ROOT, "SKILL.md")
PHASES = os.path.join(ROOT, "phases")
GATES9 = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")
KNOWN = registry.all_commands() | {
    "tanyin-guard", "tanyin-canary", "tanyin-egress", "tanyin-redact",
    "tanyin-budgetctl", "tanyin-phases", "tanyin-ledger",
    "tanyin-report", "tanyin-viz", "tanyin-replay",
    "ledger-add-edge", "ledger-matrix-freeze",  # SKILL 速查里可能带前缀引用
}


def estimate_tokens(text):
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    other = len(text) - cjk
    return cjk + (other + 3) // 4


class TestSkillResident(unittest.TestCase):
    def test_under_2k_tokens(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        t = estimate_tokens(text)
        self.assertLess(t, 2000, "常驻集 %d token 超预算（设计 §11 批次 3 出口）" % t)

    def test_eight_mandatory_sections(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        for kw in ("铁律", "九门循环", "P3 演进循环", "命令索引", "恢复协议",
                   "受管重启", "干跑", "路由表"):
            self.assertIn(kw, text, "常驻集缺节: " + kw)
        self.assertNotIn("TODO", text)
        self.assertNotIn("TBD", text)

    def test_command_index_covers_41(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        for name in registry.all_commands():
            self.assertIn(name, text, "命令索引缺: " + name)

    def test_referenced_commands_known(self):
        """SKILL.md+phases/*.md 引用命令 ⊆ 已知命令面（§10.3 静态验证①先行）。"""
        files = [SKILL] + [os.path.join(PHASES, n + ".md") for n in GATES9]
        for path in files:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for m in re.finditer(r"(?:ledger-|tanyin-)([a-z][a-z0-9-]*)", text):
                cand = m.group(0).rstrip("-")
                self.assertIn(cand, KNOWN | registry.all_commands(),
                              "%s 引用未知命令: %s" % (os.path.basename(path), cand))


class TestPhasesMd(unittest.TestCase):
    def test_nine_files_exist_with_structure(self):
        for g in GATES9:
            path = os.path.join(PHASES, g + ".md")
            self.assertTrue(os.path.isfile(path), "缺 " + path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for sec in ("## duty", "## entry", "## exit", "## 回边"):
                self.assertIn(sec, text, "%s 缺节 %s" % (g, sec))
            self.assertIn("tanyin-phases gate", text, "%s 未声明过门方式" % g)

    def test_p3_md_mandatory_sections(self):
        with open(os.path.join(PHASES, "P3.md"), encoding="utf-8") as f:
            text = f.read()
        for kw in ("entity", "concept", "precedent", "adjacency", "llm",   # 风暴五路
                   "asset-added", "cred-obtained", "scope-amended",       # 三事件
                   "converge-check", "restart",                           # 收敛+重启
                   "recon-event", "submatrix"):
            self.assertIn(kw, text, "P3.md 缺: " + kw)

    def test_yaml_asserts_consistent_with_md(self):
        """P0.md 里出现的断言命令 ⊆ phases.yaml P0.exit.assert 的命令集（声明层单源）。"""
        sys.path.insert(0, os.path.join(ROOT, "cli"))
        from ledger import phases_engine as pe
        data = pe.load_phases()
        for g in GATES9:
            with open(os.path.join(PHASES, g + ".md"), encoding="utf-8") as f:
                text = f.read()
            for a in data["gates"][g]["exit"]["assert"]:
                head = str(a["cmd"]).split()[0].replace("ledger-", "")
                self.assertIn(head, text.replace("ledger-", ""),
                              "%s.md 未提及本门断言命令 %s" % (g, head))


if __name__ == "__main__":
    unittest.main()

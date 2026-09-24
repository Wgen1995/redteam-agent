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


class TestBatch4Wiring(unittest.TestCase):
    """批次 4 T14：总控接线收口（SKILL 路由/P3 回边全语义/P4 重放协议）。"""

    def test_route_table_lists_three_engines(self):
        text = open(SKILL, encoding="utf-8").read()
        for eng in ("web-blackbox", "vuln-agent", "nuclei"):
            self.assertIn(eng, text, "路由表缺引擎 " + eng)
        self.assertNotIn("（批次 4）", text, "批次标记应摘除（已交付）")

    def test_p3_authz_diff_backedge_full_semantics(self):
        text = open(os.path.join(PHASES, "P3.md"), encoding="utf-8").read()
        self.assertIn("kind=authz-diff", text)
        self.assertNotIn("本批登记 creds 即止", text, "批次 4 前占位语应替换")

    def test_p4_replay_protocol_references_driver(self):
        text = open(os.path.join(PHASES, "P4.md"), encoding="utf-8").read()
        self.assertIn("tanyin-replay", text)

    def test_skill_budget_still_under_2k(self):
        text = open(SKILL, encoding="utf-8").read()
        self.assertLess(estimate_tokens(text), 2000)


class TestBatch4Handoff(unittest.TestCase):
    """批次 4 T14 移交件：triggers-catalog 序列/优先级调度 fb72cd5/契约勘误/台账终态。"""

    def test_skill_p0_records_triggers_catalog(self):
        text = open(SKILL, encoding="utf-8").read()
        self.assertIn("triggers-catalog", text,
                      "SKILL P0 序列须承载 triggers-catalog 事件落账（PROTOCOL §6①）")

    def test_p3_dispatch_priority_formula(self):
        text = open(os.path.join(PHASES, "P3.md"), encoding="utf-8").read()
        for kw in ("severity_expect", "asset_value", "exploitability", "Top-K"):
            self.assertIn(kw, text, "P3.md 派发规则缺优先级调度要素 " + kw)

    def test_triggers_catalog_v2_highrisk_row(self):
        text = open(os.path.join(PHASES, "TRIGGERS.md"), encoding="utf-8").read()
        self.assertIn("version: triggers-v2", text)
        self.assertIn("高危", text)
        self.assertIn("即时横向", text)

    def test_contracts09_eight_subcommands(self):
        t = open(os.path.join(ROOT, "contracts", "09-cli-surface.md"),
                 encoding="utf-8").read()
        self.assertIn("7→**8**", t)
        for sub in ("validate", "gate", "restart", "resume-kit", "cached",
                    "rebuild-state", "denominator-ready", "trigger-audit"):
            self.assertIn(sub, t, "契约 09 tanyin-phases 子命令缺 " + sub)

    def test_contract01_priority_erratum(self):
        t = open(os.path.join(ROOT, "contracts", "01-ledger-schema.md"),
                 encoding="utf-8").read()
        self.assertIn("intents.priority", t)
        self.assertIn("severity_expect", t)

    def test_contract07_nday_verify_mapping_note(self):
        t = open(os.path.join(ROOT, "contracts", "07-submission.md"),
                 encoding="utf-8").read()
        self.assertIn("nday-verify", t)
        self.assertIn("无 web-blackbox 段映射", t, "G-18 注记缺位（T14 收口回注）")

    def test_cli_readme_batch4_section(self):
        t = open(os.path.join(ROOT, "cli", "README.md"), encoding="utf-8").read()
        self.assertIn("批次 4", t)
        for kw in ("trigger-audit", "tanyin-replay", "tanyin-viz",
                   "recon-deploy", "severity_expect"):
            self.assertIn(kw, t, "cli/README 批次 4 节缺 " + kw)

    def test_b4_discovery_notes_ledger(self):
        p = os.path.join(ROOT, "docs", "design", "2026-09-24-b4-discovery-notes.md")
        self.assertTrue(os.path.isfile(p), "批 4 探知项台账缺位")
        t = open(p, encoding="utf-8").read()
        for g in ("G-16", "G-17", "G-18", "G-19", "G-20", "G-21", "G-22",
                  "G-23", "G-24", "G-25", "G-26"):
            self.assertIn(g + " ", t + chr(10), "台账缺 " + g)
        self.assertIn("已闭环", t)

    def test_b3_ledger_batch4_closure_notes(self):
        t = open(os.path.join(ROOT, "docs", "design", "2026-09-24-b3-discovery-notes.md"),
                 encoding="utf-8").read()
        self.assertIn("已闭环·批次 4", t,
                      "b3 台账 G-2/G-12/G-13 须就地注记批次 4 闭环（追加注记不改历史行）")

    def test_differential_pg_mint_doctrine_fixed(self):
        """R-T8-2 移交：PG 铸号教义=pair_group 列现序+1（next-id 只扫 id 列不见存量）。"""
        t = open(os.path.join(ROOT, "engines", "web-blackbox", "phases",
                              "differential.md"), encoding="utf-8").read()
        self.assertIn("pair_group 列现序+1", t)


if __name__ == "__main__":
    unittest.main()

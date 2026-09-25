# -*- coding: utf-8 -*-
"""批次5 T1：契约 14 知识库 schema+工具面 12 员的结构钉子（test_contract_backfill 同型只读 lint）。"""
import os, re, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
C14 = os.path.join(ROOT, "contracts", "14-knowledge-schema.md")
C09 = os.path.join(ROOT, "contracts", "09-cli-surface.md")
CREADME = os.path.join(ROOT, "contracts", "README.md")

def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

class TestContract14(unittest.TestCase):
    def test_file_and_title(self):
        t = _read(C14)
        self.assertIn("# 契约 14 · 知识库 schema", t)

    def test_six_page_kinds_with_frontmatter_tables(self):
        t = _read(C14)
        for sec in ("技法页（concepts/CP-*.md）", "先例页（precedents/PR-*.md）",
                    "实体页（entities/EN-*.md）", "复盘页（retros/RT-*.md）",
                    "模式页（patterns/PT-*.md）", "业务页（business/BZ-*.md）"):
            self.assertIn(sec, t, "缺节: " + sec)
        # 先例页三元组三字段（client/scope_asset/window）+ applied_patterns（四门槛①载体）
        self.assertIn("client", t); self.assertIn("scope_asset", t)
        self.assertIn("window", t); self.assertIn("applied_patterns", t)

    def test_staging_machine_and_four_gates(self):
        t = _read(C14)
        for w in ("staged", "lint-passed", "approved", "rejected", "formal",
                  "复现≥2", "跨目标有效", "人工审批", "无指纹泄漏"):
            self.assertIn(w, t)

    def test_id_prefix_and_graph_line_schema(self):
        t = _read(C14)
        self.assertIn("KP-", t)  # 前缀表
        self.assertIn('"predicate"', t)  # graph.ndjson 行 schema（示例行内嵌）
        self.assertIn("CLIENT-", t)  # CLIENT-NN 形态约束

    def test_vocab_versionization(self):
        t = _read(C14)
        self.assertIn("vocab_version", t)
        self.assertIn("WSTG-v4.2", t)

    def test_license_discipline(self):
        t = _read(C14)
        self.assertIn("MIT", t)  # 外部语料许可纪律（VulnClaw/BugHunter/Threatswarm/CEP）

class TestToolFace12(unittest.TestCase):
    def test_tool_table_counts_12(self):
        n = len(re.findall(r"^\| \d+ \| tanyin-", _read(C09), re.M))
        self.assertEqual(n, 12, "工具表应 12 行（tanyin-knowledge 增补）")

    def test_erratum_note_present(self):
        t = _read(C09)
        self.assertIn("tanyin-knowledge", t)

    def test_readme_registers_c14(self):
        self.assertIn("14-knowledge-schema", _read(CREADME))

class TestContractV3Sweep(unittest.TestCase):
    """批次5 T2：契约 v3 首批集中清账六笔的结构钉子（doc-only）。"""

    def test_c04_constants_gain_two(self):
        t = _read(os.path.join(ROOT, "contracts", "04-phases.md"))
        self.assertIn("authz_diff_pair_cap", t)   # R6/G-20
        self.assertIn("restart_rate_minutes", t)  # G-3（批3 T6 常量回注）

    def test_c04_gate_fail_vocab_note(self):
        t = _read(os.path.join(ROOT, "contracts", "04-phases.md"))
        self.assertIn("gate-fail:", t)  # G-7 事件词汇补注

    def test_g16_g19_closed_notes(self):
        # R-T2-1：计划原断言为裸串「G-16」/「G-19」，但两串已在批次 4 勘误注记中
        # 在册（06-evidence-cards.md R1 注/G-18 注）——裸串断言先绿、无判别力，
        # 按 TDD「Test passes? Fix test」强化为结案标记；断言意图（结案注记在场）不变。
        self.assertIn("G-16 结案", _read(os.path.join(ROOT, "contracts", "06-evidence-cards.md")))
        self.assertIn("G-19 结案", _read(os.path.join(ROOT, "contracts", "07-submission.md")))

    def test_c09_canary_dryrun_note(self):
        t = _read(C09)
        self.assertIn("只 compile", t)  # G-8 干跑口径注记（deploy 不 probe）

if __name__ == "__main__":
    unittest.main()

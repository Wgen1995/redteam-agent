# -*- coding: utf-8 -*-
"""批次6 T18：文档即契约——真人复核流程/台账四节/契约 09 勘误/交付 README 在场断言。

计划 T18 Step 1 测试骨架全兑现+加强：10 页记录行计数/契约 09 工具面勘误/cli README
批次 6 节/HANDOFF R11 行/不造数据断言（记录表复核列初始态=待真人填写，禁预填结论）。
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def rd(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class TestHumanReviewDoc(unittest.TestCase):
    def test_ten_pages_listed_with_columns(self):
        txt = rd("docs", "HUMAN-REVIEW.md")
        for pg in ("CP-0001", "CP-0008", "PR-0001", "PR-0002"):
            self.assertIn(pg, txt)
        for col in ("复核人", "结论", "日期"):
            self.assertIn(col, txt)
        self.assertIn("复核人不得为本批次执行者", txt)     # 真人≠执行者纪律成文

    def test_ten_rows_present(self):
        txt = rd("docs", "HUMAN-REVIEW.md")
        import re
        rows = [ln for ln in txt.splitlines()
                if re.match(r"^\|\s*(CP|PR)-\d{4}\s*\|", ln)]
        self.assertEqual(len(rows), 10, "在库 10 页=CP-0001..0008+PR-0001..0002 逐页一行")
        for pg in ("CP-%04d" % i for i in range(1, 9)):
            self.assertTrue(any(pg in r for r in rows), pg)

    def test_process_four_sections(self):
        txt = rd("docs", "HUMAN-REVIEW.md")
        for sec in ("范围", "判据", "记录", "争议升级"):
            self.assertIn(sec, txt)
        self.assertIn("review-checklist", txt)            # 判据=既有 checklist 同口径
        self.assertIn("四门槛", txt)

    def test_no_fabricated_review(self):
        """不造数据：记录表复核人列初始态=待真人填写，禁预填 approve 结论。"""
        txt = rd("docs", "HUMAN-REVIEW.md")
        self.assertIn("待真人填写", txt)
        for ln in txt.splitlines():
            if ln.startswith("| CP-") or ln.startswith("| PR-"):
                self.assertIn("待真人填写", ln)


class TestDiscoveryNotes(unittest.TestCase):
    def test_discovery_notes_structure(self):
        txt = rd("docs", "design", "2026-09-24-b6-discovery-notes.md")
        for sec in ("计划原文誊录", "状态归并台账", "新增探知项", "移交清单"):
            self.assertIn(sec, txt)
        for g in ("G-22", "G-25", "G-32", "G-33", "G-5", "G-11", "G-36"):
            self.assertIn(g, txt)

    def test_g36_g41_registered(self):
        txt = rd("docs", "design", "2026-09-24-b6-discovery-notes.md")
        for g in ("G-36", "G-37", "G-38", "G-39", "G-40", "G-41"):
            self.assertIn(g, txt)
        # 出口 #16 七项全量：已收口或遗留+理由+去向
        for g in ("G-4", "G-5", "G-11", "G-22", "G-25", "G-32", "G-33"):
            self.assertIn(g, txt)


class TestBackfillDocs(unittest.TestCase):
    def test_contract09_erratum(self):
        txt = rd("contracts", "09-cli-surface.md")
        self.assertIn("批次 6", txt)
        self.assertIn("tanyin-evals", txt)
        for tool in ("tanyin-install", "tanyin-selfcheck", "tanyin-report", "tanyin-budgetctl"):
            self.assertIn(tool, txt)
        self.assertIn("--egress-log", txt)                # canary probe 注记

    def test_cli_readme_batch6(self):
        txt = rd("cli", "README.md")
        self.assertIn("批次 6", txt)
        for tool in ("tanyin-evals", "tanyin-install", "tanyin-selfcheck", "tanyin-report"):
            self.assertIn(tool, txt)

    def test_handoff_r11_row(self):
        txt = rd("docs", "HANDOFF.md")
        self.assertIn("R11", txt)                         # 法务过审记录行载体
        self.assertIn("真人复核", txt)                    # 前置义务兑现行载体


if __name__ == "__main__":
    unittest.main()

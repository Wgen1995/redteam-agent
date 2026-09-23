# -*- coding: utf-8 -*-
"""批次 3 T13：契约 02a 回注（G-6/G-10）+探知项台账落盘+README 批次3节的结构钉子。
TDD 先红后绿：本文件先行（红=回注/落盘缺位），交付后转绿。纯只读 lint——不动 fixtures/。
十键表与 state_md.KEY_ORDER 单源对齐——防契约与实现双份清单漂移。"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import state_md   # noqa: E402 （KEY_ORDER 单一实现源）

C02A = os.path.join(ROOT, "contracts", "02a-command-signatures-draft.md")
CREADME = os.path.join(ROOT, "contracts", "README.md")
NOTES = os.path.join(ROOT, "docs", "design", "2026-09-24-b3-discovery-notes.md")
CLI_README = os.path.join(ROOT, "cli", "README.md")
ERRATA_HEAD = "## v2 勘误补记（2026-09-24·批次 3 施工期·G-6/G-10 裁决）"


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _errata():
    t = _read(C02A)
    i = t.find(ERRATA_HEAD)
    assert i >= 0, "02a 缺 G-6/G-10 勘误补记节"
    return t[i:]


class Test02aBackfill(unittest.TestCase):
    def test_errata_section_and_channel(self):
        """G-6/G-10 回注走微版本勘误通道（同批次 G-1·契约⑨先例），不升 schema_version。"""
        e = _errata()
        self.assertIn("微版本勘误", e)
        self.assertIn("schema_version 保持 =2", e)

    def test_state_md_ten_keys_single_source(self):
        """勘误十键表与 state_md.KEY_ORDER 逐键同序（单源对齐，防漂移）。"""
        rows = re.findall(r"^\|\d+\|([a-z_]+)\|", _errata(), re.M)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows, list(state_md.KEY_ORDER))

    def test_checkpoint_signature_params(self):
        """G-10：checkpoint 终局签名——必填 --timestamp/--session + 六可选参数全在册。"""
        e = _errata()
        sig = next(l for l in e.splitlines() if "签名（终局）" in l)
        body = sig.replace("`", "")
        head = body.split("[", 1)[0]           # 可选段之前=必填参数区
        self.assertIn("--timestamp=", head)
        self.assertIn("--session=", head)
        for tok in ("--phase", "--event", "--release", "--round", "--note", "--spawn"):
            self.assertIn(tok, body)
        self.assertIn("OK<TAB>revision=<n>", e)   # 输出 schema 不变承诺在册

    def test_contract_readme_errata_index(self):
        """contracts/README.md 勘误补记索引登记 02a 回注（通道对齐 G-1 先例）。"""
        t = _read(CREADME)
        self.assertIn("02a", t)
        self.assertIn("G-6", t)
        self.assertIn("G-10", t)


class TestDiscoveryNotes(unittest.TestCase):
    def test_ledger_g1_through_g15(self):
        """探知项台账 G-1..G-15 全量在册+状态归并口径（已回注/常量暂代）可检索。"""
        self.assertTrue(os.path.isfile(NOTES), "docs/design/2026-09-24-b3-discovery-notes.md 未落盘")
        t = _read(NOTES)
        for i in range(1, 16):
            self.assertIn("G-%d" % i, t, "台账缺 G-%d" % i)
        self.assertIn("已回注", t)      # G-6/G-10 终态
        self.assertIn("常量暂代", t)    # G-3/G-4 终态

    def test_plan_table_transcribed(self):
        """计划「探知项」节 G-1..G-11 原文誊录在册（T13 Files 节明文，防转写漂移）。"""
        t = _read(NOTES)
        self.assertIn("| G-1 | **工具面 10→11**", t)
        self.assertIn("| G-11 | **token 估算器口径**", t)
        self.assertIn("RESTART_RATE_MINUTES=10", t)


class TestCliReadmeBatch3(unittest.TestCase):
    def test_batch3_section(self):
        """cli/README.md 批次 3 节：七子命令面+state.md v2 十键速览在册。"""
        t = _read(CLI_README)
        self.assertIn("批次 3", t)
        for sub in ("validate", "gate", "restart", "resume-kit", "cached",
                    "rebuild-state", "denominator-ready"):
            self.assertIn(sub, t)
        self.assertIn("state.md v2", t)


if __name__ == "__main__":
    unittest.main()

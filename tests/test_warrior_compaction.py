# -*- coding: utf-8 -*-
"""dsh P0 采纳②：检查点压缩（对照 docs/research/2026-10-20-dsh-orchestration-inventory.md
A 表#3 / §1.5 / §⑧-2；dsh 出处 dsh-compaction-basic/lib/index.js:15-17,236-356）。

同源三件=0.8×窗口触发阈值公式 / 0.16 近尾原文保留 / 固定 8 节结构
（Pending Jobs+Next Step 两节防丢任务线索）。纯函数版：素材超阈值时
产出压缩包+原文指针，不真调 LLM——LLM 道留 summarizer 注入位。

跑法：python3 -m unittest tests.test_warrior_compaction -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from warrior import compaction as wc                       # noqa: E402
from warrior.context import estimate_tokens                # noqa: E402


def line(n_chars=90, tag="x"):
    return (tag * n_chars)[:n_chars]


class TestThreshold(unittest.TestCase):
    """dsh compaction-basic:15-17 同公式：min(窗×0.8, 窗−保留−头寸)。"""

    def test_plain_window(self):
        self.assertEqual(wc.threshold_tokens(24000), 19200)

    def test_reserved_and_headroom_cap(self):
        self.assertEqual(
            wc.threshold_tokens(100000, reserved_completion=8192,
                                headroom_tokens=65536),
            min(80000, 100000 - 8192 - 65536))

    def test_needs_compaction_bool(self):
        self.assertFalse(wc.needs_compaction(19200, 24000))
        self.assertTrue(wc.needs_compaction(19201, 24000))


class TestCompactionPackage(unittest.TestCase):
    def _materials(self, n_tl=40, n_facts=10):
        facts = ["F-g1-%04d | INT-g1-0002 | %s | tgt%d | 细节%d | conf=0.9"
                 % (i, "info" if i % 2 else "service", i, i)
                 for i in range(1, n_facts + 1)]
        tl = ["warrior-progress warrior=warrior:W-1 intent=INT-g1-0002 "
              "turn=%d op=scan out=%s" % (i, line(40, "o"))
              for i in range(1, n_tl + 1)]
        return facts, tl

    def test_under_threshold_returns_none(self):
        facts, tl = self._materials(n_tl=2, n_facts=2)
        self.assertIsNone(
            wc.build_compaction(intent="意图 x", facts=facts, timeline=tl,
                                window_tokens=100000),
            "素材未超 0.8 阈值=不压缩（零行为漂移）")

    def test_eight_dsh_sections_in_order(self):
        facts, tl = self._materials()
        pkg = wc.build_compaction(intent="意图 x", facts=facts, timeline=tl,
                                  window_tokens=1000)
        self.assertIsNotNone(pkg)
        self.assertEqual(list(pkg.sections.keys()), list(wc.SECTIONS))
        self.assertEqual(wc.SECTIONS, (
            "Primary Request and Intent", "Key Technical Concepts",
            "Files and Code", "Errors and Fixes", "Pending Jobs",
            "Current Work", "Next Step", "Critical Context"))
        pos = [pkg.text.index("## " + s) for s in wc.SECTIONS]
        self.assertEqual(pos, sorted(pos), "8 节渲染顺序固定（dsh 243-278）")

    def test_intent_lands_in_primary_request(self):
        facts, tl = self._materials()
        pkg = wc.build_compaction(intent="INT-g1-0002 admin 未授权",
                                  facts=facts, timeline=tl, window_tokens=1000)
        self.assertIn("INT-g1-0002 admin 未授权",
                      pkg.sections["Primary Request and Intent"])

    def test_kinds_histogram_in_concepts(self):
        facts, tl = self._materials(n_facts=4)
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=1000)
        self.assertIn("service:2", pkg.sections["Key Technical Concepts"])
        self.assertIn("info:2", pkg.sections["Key Technical Concepts"])

    def test_errors_and_fixes_captures_failure_lines(self):
        facts, tl = self._materials()
        tl = tl + ["model-fail reason=channel-429 attempts=2",
                   "tool 通道异常: exit 7"]
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=800)
        self.assertIn("model-fail", pkg.sections["Errors and Fixes"])
        self.assertIn("通道异常", pkg.sections["Errors and Fixes"])

    def test_pending_jobs_prevents_thread_loss(self):
        facts, tl = self._materials()
        tl = tl + ["intent-pending IN-x1 reason=await-cred",
                   "intent-blocked IN-x2 reason=lease-expired"]
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=800)
        pj = pkg.sections["Pending Jobs"]
        self.assertIn("IN-x1", pj, "pending 线索不丢（§⑧-2 防丢线）")
        self.assertIn("IN-x2", pj, "blocked 线索不丢")

    def test_next_step_pins_ledger_authority(self):
        facts, tl = self._materials()
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=1000)
        ns = pkg.sections["Next Step"]
        self.assertIn("Pending Jobs", ns, "续跑起点=在途线索节")
        self.assertIn("timeline", ns, "断点锚=盘上 timeline 末行")

    def test_current_work_is_last_timeline_line_verbatim(self):
        facts, tl = self._materials()
        tl = tl + ["warrior-progress op=verify target=acme.com"]
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=1000)
        self.assertIn("warrior-progress op=verify target=acme.com",
                      pkg.sections["Current Work"])

    def test_recent_tail_retained_verbatim_at_16pct(self):
        """0.16×窗 token 的近尾原文逐字保留（dsh retainRatio 同源）。"""
        n, w = 40, 1000
        tl = [line(90, "t%02d" % i) for i in range(n)]   # 每行 30 token
        pkg = wc.build_compaction(intent="i", facts=[], timeline=tl,
                                  window_tokens=w)
        self.assertIsNotNone(pkg)
        # 保留预算=0.16×1000=160 tok；从尾累积 30tok/行 → 6 行（≥160）
        self.assertEqual(pkg.retained_tail, tl[-6:])
        for orig, kept in zip(tl[-6:], pkg.retained_tail):
            self.assertIs(orig, kept, "近尾原文逐字（不做任何改写）")

    def test_summary_must_be_smaller_than_shadowed(self):
        """dsh 护栏（compaction-basic:601）：摘要≥被遮蔽内容=拒绝，不产包。"""
        tiny_head = [line(90, "a")]                       # 30 tok
        huge_tail = ["y" * 2313]                          # 771 tok
        with self.assertRaises(wc.CompactionRefused):
            wc.build_compaction(intent="i", facts=[], timeline=[],
                                briefing="\n".join(tiny_head + huge_tail),
                                window_tokens=1000)

    def test_pointers_to_originals_in_critical_context(self):
        facts, tl = self._materials(n_facts=10, n_tl=20)
        pkg = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                  window_tokens=500)
        self.assertIsNotNone(pkg)
        self.assertEqual(pkg.pointers["facts_count"], 10)
        self.assertEqual(pkg.pointers["timeline_count"], 20)
        cc = pkg.sections["Critical Context"]
        self.assertIn("facts.tsv", cc)
        self.assertIn("timeline.tsv", cc)
        self.assertIn("以盘上账本为准", cc, "防幻觉律随包下发")

    def test_deterministic_same_input_same_output(self):
        facts, tl = self._materials()
        a = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                window_tokens=1000)
        b = wc.build_compaction(intent="i", facts=facts, timeline=tl,
                                window_tokens=1000)
        self.assertEqual(a.text, b.text)
        self.assertEqual(a.retained_tail, b.retained_tail)
        self.assertEqual(a.pointers, b.pointers)

    def test_llm_summarizer_injection_seam(self):
        """LLM 道注入位：summarizer 可整体接管 8 节（默认 None=确定性抽取，
        本测试只验证缝——零 LLM 真调）。"""
        facts, tl = self._materials()
        fake = lambda sections: {          # noqa: E731 —— 测试面假 LLM
            k: ("LLM:" + v) if k == "Primary Request and Intent" else v
            for k, v in sections.items()}
        pkg = wc.build_compaction(intent="意图 z", facts=facts, timeline=tl,
                                  window_tokens=1000, summarizer=fake)
        self.assertTrue(pkg.sections["Primary Request and Intent"]
                        .startswith("LLM:"))
        self.assertIn("意图 z", pkg.sections["Primary Request and Intent"],
                      "假 LLM 收到确定性骨架为底（不另起炉灶）")


if __name__ == "__main__":
    unittest.main()

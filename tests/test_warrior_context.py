# -*- coding: utf-8 -*-
"""战士运行时·上下文工程（W5 战士 MVP · 质量律 R1/R3）。

R1 一意图一脑：build() 每次全新组装，builder 零跨意图状态；血缘经账本行
（facts/intents/timeline）传入，绝不携带聊天史。R3 压缩器：facts 节超窗 →
冷折叠（ARTEX Compactor cold-digest 移植）——最旧段折叠成计数摘要行，
最新 fold_keep 条原文保留；token 估算入 ContextResult 供 budget 计量。

节序（固定）：protocol(SKILL.md 原样) → intent → facts(可折叠) → resume
(timeline 末 K 行摘要=断点续跑) → corrections(上轮工具失败紧凑信号) →
steers(定向指令)。

跑法：python3 -m unittest tests.test_warrior_context -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from warrior import context  # noqa: E402


SKILL_STUB = "# 探隐 SKILL\n九门循环 P0-P6……\n"


class TestContext(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        shutil.copy(os.path.join(FIX, "facts.tsv"),
                    os.path.join(self.gd, "facts.tsv"))
        shutil.copy(os.path.join(FIX, "timeline.tsv"),
                    os.path.join(self.gd, "timeline.tsv"))
        self.skill = os.path.join(self.gd, "SKILL.md")
        with open(self.skill, "w", encoding="utf-8") as f:
            f.write(SKILL_STUB)
        self.cb = context.ContextBuilder(self.gd, skill_path=self.skill,
                                         ctx_tokens=4000)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _intent(self, iid="INT-g1-0001", title="子域枚举", detail="crt.sh+被动"):
        return {"id": iid, "title": title, "detail": detail, "status": "pending"}

    def test_protocol_section_skill_md_verbatim(self):
        r = self.cb.build(self._intent())
        self.assertIn(SKILL_STUB.strip(), r.text)
        self.assertEqual(r.sections["protocol"], SKILL_STUB.strip())

    def test_intent_section_carries_detail(self):
        r = self.cb.build(self._intent(detail="递归爆破二级域名"))
        self.assertIn("INT-g1-0001", r.text)
        self.assertIn("递归爆破二级域名", r.text)

    def test_r1_fresh_context_no_cross_intent_facts(self):
        # 意图 0001 的 facts 绝不进意图 0002 的上下文（防串味律）
        r2 = self.cb.build(self._intent(iid="INT-g1-0002"))
        self.assertNotIn("shop.example", r2.text.split("resume")[-1])

    def test_relevant_facts_included_for_own_intent(self):
        r1 = self.cb.build(self._intent(iid="INT-g1-0001"))
        self.assertIn("shop.example", r1.text)
        self.assertIn("nginx/1.25", r1.text)

    def test_r3_cold_fold_over_window(self):
        # 数据量逼折叠：追加 30 条长事实，ctx_tokens=120 之下必超窗
        with open(os.path.join(self.gd, "facts.tsv"), "a",
                  encoding="utf-8") as f:
            for i in range(30):
                f.write("F-g1-9%03d\tINT-g1-0001\tinfo\tt%d.example\t"
                        "枚举批次 %d 的观察记录——%s\t0.9\t2\t"
                        "2026-09-23T03:00:00Z\n"
                        % (i, i, i, "观察细节" * 8))
        cb = context.ContextBuilder(self.gd, skill_path=self.skill,
                                    ctx_tokens=120)
        r = cb.build(self._intent(iid="INT-g1-0001"))
        self.assertTrue(r.folded)
        self.assertIn("cold-digest", r.text)
        # 最旧段折叠：fixture 期事实原文不再整段在场；最新事实保留原文
        self.assertNotIn("12 子域", r.text)
        self.assertIn("t29.example", r.text)

    def test_no_fold_below_window(self):
        r = self.cb.build(self._intent(iid="INT-g1-0001"))
        self.assertFalse(r.folded)
        self.assertNotIn("cold-digest", r.text)

    def test_resume_section_from_timeline_tail(self):
        # fixture timeline 无本意图行 → 空 resume 也成立；手工补一行后再测
        with open(os.path.join(self.gd, "timeline.tsv"), "a",
                  encoding="utf-8") as f:
            f.write("2026-09-23T02:00:00Z\twarrior:W-1\tP3\t"
                    "warrior-progress INT-g1-0001 turn=2 op=tool card=dig"
                    "\t\t" + "0" * 64 + "\t" + "1" * 64 + "\t2\n")
        r = self.cb.build(self._intent(iid="INT-g1-0001"))
        self.assertIn("warrior-progress INT-g1-0001", r.text)

    def test_corrections_and_steers_sections(self):
        r = self.cb.build(self._intent(), corrections=["dig rc=1 timeout"],
                          steers=["优先 admin 面板"])
        self.assertIn("dig rc=1 timeout", r.text)
        self.assertIn("优先 admin 面板", r.text)

    def test_estimated_tokens_positive_and_monotonic(self):
        r_small = self.cb.build(self._intent(detail="短"))
        r_big = self.cb.build(self._intent(detail="长" * 500))
        self.assertGreater(r_small.estimated_tokens, 0)
        self.assertGreater(r_big.estimated_tokens, r_small.estimated_tokens)


if __name__ == "__main__":
    unittest.main()

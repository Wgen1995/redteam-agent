# -*- coding: utf-8 -*-
"""战士运行时·知识库上下文（VulnClaw kb_context 移植·战士化）。

两件移植面：
① 技法卡按意图关联检索：knowledge/concepts CP-0001..0050（50 张）为语料，
  意图 title/detail+本意图 facts 行为关联信号——确定性打分（拉丁 token+
  CJK 二元组，title/vuln_class/source_topic/applicability 分权），命中才
  注入 R1 上下文新节「## 技法卡」，零命中=零注入（VulnClaw 降级律同源：
  检索任何失败静默为空，绝不炸主循环）；
② SKILL 按门路由瘦身：协议节不再整册注入——按当前门（timeline 末行
  phase 列）路由：骨架保留（铁律/命令索引/路由表等）+逐门详令节
  （九门循环/P3 演进循环）让位给 phases/<门>.md 的 duty 节单门单载；
  门未知/文件缺失/duty 缺失=原文回退（不炸不改）。

R1 律：检索不缓存跨意图查询结果——一意图一检索；模块级只缓存卡片索引
（纯数据面，目录指纹键控）。

跑法：python3 -m unittest tests.test_warrior_kb_context -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger import llmpool_wire  # noqa: E402
from tests.test_warrior_fake_model import FakeModelServer  # noqa: E402
from tools import install as tool_install  # noqa: E402
from warrior import context as wctx  # noqa: E402
from warrior import kb_context  # noqa: E402
from warrior import loop as wloop  # noqa: E402

W = "warrior:W-1"
DONE = '{"op":"done","reason":"完成"}'

STUB_SKILL_KB = ("# 探隐 SKILL\n\n## 铁律\n单写者。\n\n"
                 "## 九门循环\nP0-P6 概览与过门详令。\n\n"
                 "## P3 演进循环\n六步每轮。\n\n"
                 "## 命令索引\n50 条。\n\n## 路由表\n当前门单门单载。\n")


def _intent(iid="INT-g1-0002", title="admin 面板未授权访问",
            detail="authz-diff"):
    return {"id": iid, "title": title, "detail": detail, "status": "pending"}


class TestCardCorpus(unittest.TestCase):
    def test_load_cards_fifty_from_repo_corpus(self):
        cards = kb_context.load_cards()
        self.assertEqual(len(cards), 50)
        self.assertEqual(cards[0]["id"], "CP-0001")
        self.assertEqual(cards[-1]["id"], "CP-0050")
        self.assertTrue(all(c.get("title") for c in cards))

    def test_load_cards_missing_dir_degrades_to_empty(self):
        self.assertEqual(kb_context.load_cards(kb_dir="/nonexistent-kb"), [])


class TestIntentAssociation(unittest.TestCase):
    def test_sql_intent_ranks_sqli_card_top(self):
        cards = kb_context.retrieve({"id": "i", "title": "SQL 注入联合查询探测",
                                     "detail": "", "status": "pending"})
        self.assertTrue(cards)
        self.assertEqual(cards[0]["id"], "CP-0001")

    def test_authz_intent_associates_auth_card(self):
        cards = kb_context.retrieve(_intent())
        self.assertIn("CP-0024", [c["id"] for c in cards])

    def test_unrelated_intent_retrieves_nothing(self):
        cards = kb_context.retrieve({"id": "i", "title": "整理笔记与归档",
                                     "detail": "写周报", "status": "pending"})
        self.assertEqual(cards, [])

    def test_retrieve_extra_text_extends_signal(self):
        # 意图文本无信号，facts 行文本（extra_text）独立命中
        cards = kb_context.retrieve(
            {"id": "i", "title": "面板观察", "detail": "",
             "status": "pending"}, extra_text="服务指纹 nginx 反向代理 子域")
        self.assertTrue(any(c["id"] == "CP-0042" for c in cards),
                        "侦察域卡经 facts 信号关联")

    def test_retrieve_deterministic_and_tie_broken_by_id(self):
        kb = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, kb)
        for cid in ("CP-9002", "CP-9001"):
            with open(os.path.join(kb, cid + ".md"), "w",
                      encoding="utf-8") as f:
                f.write("---\nid: %s\nkind: technique\ntitle: 注入探测域\n"
                        "vuln_class: wstg:inj\n---\n## 适用条件\nx\n"
                        % cid)
        intent = {"id": "i", "title": "注入探测", "detail": "",
                  "status": "pending"}
        first = kb_context.retrieve(intent, kb_dir=kb)
        again = kb_context.retrieve(intent, kb_dir=kb)
        self.assertEqual([c["id"] for c in first], ["CP-9001", "CP-9002"])
        self.assertEqual(first, again, "同信号同结果（确定性检索）")


class TestSectionBuild(unittest.TestCase):
    def test_section_header_card_and_fields(self):
        sec = kb_context.build_kb_section(
            {"id": "i", "title": "SQL 注入联合查询探测", "detail": "",
             "status": "pending"})
        self.assertTrue(sec.startswith("## 技法卡"))
        self.assertIn("CP-0001", sec)
        self.assertIn("适用:", sec)
        self.assertIn("转向:", sec)

    def test_section_empty_on_no_match_and_on_missing_kb(self):
        intent = {"id": "i", "title": "整理笔记与归档", "detail": "写周报",
                  "status": "pending"}
        self.assertEqual(kb_context.build_kb_section(intent), "")
        self.assertEqual(
            kb_context.build_kb_section(_intent(), kb_dir="/nonexistent-kb"),
            "")

    def test_section_top_k_respected(self):
        sec = kb_context.build_kb_section(
            {"id": "i", "title": "SQL 注入联合查询探测", "detail": ""},
            top_k=1)
        self.assertEqual(sec.count("- **"), 1)


class TestSkillGateRouting(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            self.skill = f.read()

    def test_slim_drops_per_gate_sections_keeps_core(self):
        slim = kb_context.slim_skill_by_gate(self.skill, "P3")
        self.assertNotIn("## 九门循环", slim)
        self.assertNotIn("## P3 演进循环", slim)
        self.assertIn("## 铁律", slim)
        self.assertIn("## 命令索引", slim)
        self.assertIn("## 路由表", slim)
        self.assertLess(len(slim), len(self.skill), "门路由后净瘦身")

    def test_slim_appends_single_gate_duty(self):
        slim = kb_context.slim_skill_by_gate(self.skill, "P3")
        self.assertIn("## 当前门详令", slim)
        self.assertIn("phases/P3.md", slim)
        self.assertIn("unconsumed-facts", slim, "duty 节内容单门单载")

    def test_slim_falls_back_to_original_on_unknown_gate(self):
        for gate in ("", "P99", "sidebar"):
            self.assertEqual(
                kb_context.slim_skill_by_gate(self.skill, gate), self.skill)

    def test_gate_of_goal_from_timeline_tail(self):
        gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, gd)
        self.assertEqual(kb_context.gate_of(gd), "")
        shutil.copy(os.path.join(FIX, "timeline.tsv"),
                    os.path.join(gd, "timeline.tsv"))
        self.assertEqual(kb_context.gate_of(gd), "P3")


class TestContextIntegration(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.skill = os.path.join(self.gd, "SKILL.md")
        with open(self.skill, "w", encoding="utf-8") as f:
            f.write(STUB_SKILL_KB)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def test_kb_off_keeps_legacy_shape(self):
        cb = wctx.ContextBuilder(self.gd, skill_path=self.skill,
                                 ctx_tokens=8000)
        r = cb.build(_intent())
        self.assertNotIn("技法卡", r.text)
        self.assertNotIn("当前门详令", r.text)
        self.assertNotIn("kb", r.sections)
        self.assertEqual(r.sections["protocol"], STUB_SKILL_KB.strip())

    def test_kb_on_injects_cards_and_slims_protocol(self):
        cb = wctx.ContextBuilder(self.gd, skill_path=self.skill,
                                 ctx_tokens=8000, kb=True)
        r = cb.build(_intent())
        self.assertIn("## 技法卡", r.text)
        self.assertIn("CP-0024", r.text, "授权意图关联认证授权卡")
        self.assertIn("kb", r.sections)
        self.assertNotIn("P0-P6 概览", r.sections["protocol"])
        self.assertNotIn("六步每轮", r.sections["protocol"])
        self.assertIn("## 铁律", r.sections["protocol"])
        self.assertIn("## 当前门详令", r.sections["protocol"])
        self.assertIn("unconsumed-facts", r.sections["protocol"])

    def test_kb_on_no_match_injects_nothing(self):
        cb = wctx.ContextBuilder(self.gd, skill_path=self.skill,
                                 ctx_tokens=8000, kb=True)
        r = cb.build({"id": "INT-g1-0009", "title": "整理笔记与归档",
                      "detail": "写周报", "status": "pending"})
        self.assertNotIn("## 技法卡", r.text)
        self.assertEqual(r.sections.get("kb", "x"), "")

    def test_kb_section_survives_fold_budget(self):
        # 技法卡节不属 facts 折叠面：极小窗下折叠发生但卡节仍在
        cb = wctx.ContextBuilder(self.gd, skill_path=self.skill,
                                 ctx_tokens=200, kb=True)
        r = cb.build(_intent())
        self.assertIn("CP-0024", r.text)


class _OkSpawn(object):
    def __call__(self, argv):
        return 0, "ok-out", ""


class TestLoopIntegration(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.state = os.path.join(self.gd, "..",
                                  os.path.basename(self.gd) + "-cards.tsv")
        for n in ("curl", "dig"):
            ok, why = tool_install.install(n, "2026-10-18T10:00:00Z",
                                           state_path=self.state)
            self.assertTrue(ok, why)
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _run(self, kb=None):
        self.srv.set_scripts({"m1": [{"content": DONE}]})
        channels = [{"name": "m1", "model": "m1",
                     "base_url": self.srv.base, "api_key": "k"}]
        pool = llmpool_wire.attach(self.gd, env={})
        args = dict(goal_dir=self.gd, battle_name="B-x", channels=channels,
                    pool=pool, warrior_id=W, max_intents=3, max_turns=6,
                    token_cap=100000, tool_spawn=_OkSpawn(),
                    tool_state_path=self.state, ctx_tokens=8000)
        if kb is not None:
            args["kb"] = kb
        return wloop.WarriorLoop(**args).run()

    def _first_ctx(self):
        return json.dumps(self.srv.requests[0]["messages"],
                          ensure_ascii=False)

    def test_loop_default_kb_injects_cards(self):
        rep = self._run()
        self.assertEqual(rep.status, "no-intents")
        ctx = self._first_ctx()
        self.assertIn("## 技法卡", ctx)
        self.assertIn("CP-", ctx)

    def test_loop_kb_opt_out(self):
        rep = self._run(kb=False)
        self.assertEqual(rep.status, "no-intents")
        self.assertNotIn("技法卡", self._first_ctx())


if __name__ == "__main__":
    unittest.main()

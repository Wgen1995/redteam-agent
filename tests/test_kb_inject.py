# -*- coding: utf-8 -*-
"""W5 知识环·知识注入回路（kb_inject）——91 卡存量接进战士简报。

蒸馏入册首转（docs/audits/2026-10-20-distill-registration-audit.md §八）之后，
「注入」齿=W5 领地：本测钉死注入回路四件——
① 检索器：输入=当前意图（类 kind/表面 surface/引擎 engine）+矩阵上下文
   （matrix.tsv 本意图行的 surface×vuln_class 族），输出=相关卡引用集——
   技法卡按类簇匹配（卡 vuln_class wstg 族 ∩ 意图信号族），避坑卡按漏报族
   匹配（卡 vuln_class 族 ∩ 信号族；同表面历史漏报族优先加分）；
② 卡数帽：每简报 ≤ max_cards（缺省 5，goal 配置可调），防简报爆炸；
   零命中=零注入不硬塞；
③ 审计：注入了哪几张进哪仗哪士，落 goal 目录 kb-injections.tsv（追加审计
   行；同意图同卡集幂等不重落）；未领取意图（dry-run 面）不落审计行；
④ 开关：goal 配置 kb-inject.json（enabled 缺省 true=默认开；坏 JSON 降级
   缺省不炸简报）。

注入式参考裁定（docs/design/2026-10-20-graphled-master-verdict.md:104）：
注入=「供参考」——AI 是指挥官，卡是情报，打法自主（不剥夺判断）。

跑法：python3 -m unittest tests.test_kb_inject -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cli"))

from warrior import kb_inject  # noqa: E402

SKILL_STUB = "# 探隐 SKILL\n九门循环 P0-P6……\n"
T0 = "2026-09-23T03:00:00Z"
ZERO64 = "0" * 64
ONE64 = "1" * 64


# ---------------------------------------------------------------- 语料夹具 --

def _md(front, body="## 适用条件\nx\n"):
    lines = ["---"]
    for k, v in front.items():
        lines.append("%s: %s" % (k, v))
    lines.append("---")
    lines.append(body)
    return "\n".join(lines) + "\n"


def _tech(cid, vc, title, applicability="同型 Web 靶场战", topic=""):
    return {"id": cid, "kind": "technique", "title": title, "vuln_class": vc,
            "applicability": applicability, "status": "learned",
            "source_id": "KP-0011", "source_topic": topic or
            "distill/battle-38/CWE-89", "cost_hint": "1"}


def _neg(cid, vc, title, fam, failure_path, conditions, source_id="battle-27"):
    if fam in ("jwt", "csrf", "idor", "role"):
        topic = "distill/battle-27/miss/" + fam
    elif fam == "fp":
        topic = "distill/battle-29/fp"
    else:
        topic = "distill/battle-24/fact"
    return {"id": cid, "kind": "negative", "title": title,
            "vuln_class": vc, "failure_path": failure_path,
            "conditions": conditions, "ledger_ref":
            "%s/timeline.tsv:696" % source_id, "status": "learned",
            "source_id": source_id, "source_topic": topic}


def _mk_kb(root):
    os.makedirs(os.path.join(root, "concepts"))
    os.makedirs(os.path.join(root, "negative"))
    cards = [
        _tech("CP-9101", "wstg-inpv:inj.sql",
              "CWE-89 SQL 注入 高置信打法（battle-38·4 例全验证）",
              topic="distill/battle-38/CWE-89"),
        _tech("CP-9102", "wstg-inpv:cmdi", "CWE-94 命令注入 高置信打法",
              topic="distill/battle-37/CWE-94"),
        _tech("CP-9103", "wstg-authz", "CWE-284 访问控制 高置信打法",
              topic="distill/battle-30/CWE-284"),
        _tech("CP-9104", "wstg-sess:csrf", "CWE-352 CSRF 高置信打法",
              topic="distill/battle-25/CWE-352"),
        _tech("CP-9105", "wstg-info:recon", "侦察方法论域卡"),
        _tech("CP-9106", "wstg-inpv:ssti", "CWE-1336 SSTI 高置信打法"),
        _tech("CP-9107", "wstg-inpv:file", "CWE-98 文件包含 高置信打法"),
        _tech("CP-9108", "wstg-inpv:ssrf", "CWE-918 SSRF 高置信打法"),
        _tech("CP-9109", "wstg-inpv:xxe", "CWE-611 XXE 高置信打法"),
        _tech("CP-9110", "wstg-inpv:deserialize", "CWE-502 反序列化 高置信打法"),
        _neg("CP-9201", "wstg-sess", "漏报族 jwt：battle-27 全战 2 条缺", "jwt",
             "GT 类 jwt 共 2 条全缺（recall=0.7）",
             "同靶型同窗口再战时——先核 jwt 通道是否铺面（target=svc-shop）"),
        _neg("CP-9202", "wstg-sess", "漏报族 csrf：battle-27 全战 2 条缺", "csrf",
             "GT 类 csrf 共 2 条全缺（recall=0.7）",
             "同靶型同窗口再战时——先核 csrf 通道是否铺面"),
        _neg("CP-9203", "wstg-authz", "漏报族 idor：battle-28 全战 6 条缺", "idor",
             "GT 类 idor 共 6 条全缺（recall=0.46）",
             "同靶型同窗口再战时——先核 idor 通道（target=svc-shop）",
             source_id="battle-28"),
        _neg("CP-9204", "wstg-apit", "重放证伪：/login 无速率限制", "fp",
             "发现判 verified 后被重放证伪",
             "同判定通道（vuln_ref=CWE-307+同证据形态）再出结论时先重放",
             source_id="battle-29"),
        _neg("CP-9205", "wstg-info", "负面披露：47 路径全 404", "fact",
             "files：47 路径全 404——真实入口未发现",
             "同部署形态/同靶型时——排兵前先读 facts 披露（target=svc-files）",
             source_id="battle-25"),
    ]
    for c in cards:
        d = "concepts" if c["kind"] == "technique" else "negative"
        with open(os.path.join(root, d, c["id"] + ".md"), "w",
                  encoding="utf-8") as f:
            f.write(_md(c))
    return root


def _intent(iid="INT-g1-0100", title="注入类全家族实证", detail="probe 实测",
            kind="matrix-test", engine="web-blackbox"):
    return {"id": iid, "title": title, "detail": detail, "status": "pending",
            "kind": kind, "engine": engine}


class KbInjectTestBase(unittest.TestCase):
    def setUp(self):
        self.kb = _mk_kb(tempfile.mkdtemp(prefix="kbinj-kb-"))
        self.gd = tempfile.mkdtemp(prefix="kbinj-goal-")
        self.addCleanup(shutil.rmtree, self.kb, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.gd, ignore_errors=True)


# ================================================================ 语料面 ==

class TestCorpus(KbInjectTestBase):
    def test_load_runtime_cards_techniques_and_negatives(self):
        tech, neg = kb_inject.load_runtime_cards(self.kb)
        self.assertEqual([c["id"] for c in tech][:2], ["CP-9101", "CP-9102"])
        self.assertEqual(len(tech), 10)
        self.assertEqual(len(neg), 5)
        self.assertTrue(all(c["kind"] == "negative" for c in neg))

    def test_load_runtime_cards_missing_root_degrades_empty(self):
        self.assertEqual(kb_inject.load_runtime_cards("/nonexistent-kb"), ([], []))

    def test_distill_maps_imported_nonempty(self):
        # 家族/CWE→wstg 映射单源复用 cli.knowledge.distill（缺=环境烂，测试红）
        self.assertTrue(kb_inject.FAMILY_TO_WSTG)
        self.assertTrue(kb_inject.CWE_TO_WSTG)
        self.assertEqual(kb_inject.FAMILY_TO_WSTG.get("jwt"), "wstg-sess")


# ============================================================ 信号收集面 ==

class TestGatherSignal(KbInjectTestBase):
    def _write_matrix(self, rows):
        with open(os.path.join(self.gd, "matrix.tsv"), "w",
                  encoding="utf-8") as f:
            for surf, fam, iid in rows:
                f.write("%s\t%s\t\t\t%s\t2\t\t\n" % (surf, fam, iid))

    def test_matrix_rows_tied_to_intent_give_families_and_surfaces(self):
        self._write_matrix([("svc-shop", "wstg-inpv", "INT-g1-0100"),
                            ("svc-shop", "wstg-sess", "INT-g1-0100"),
                            ("svc-admin", "wstg-authz", "INT-g1-0200")])
        sig = kb_inject.gather_signal(self.gd, _intent())
        self.assertEqual(sig["surfaces"], ["svc-shop"])
        self.assertEqual(sig["families"], ["wstg-inpv", "wstg-sess"])

    def test_no_matrix_tie_falls_back_to_text_scan(self):
        sig = kb_inject.gather_signal(self.gd, _intent(
            title="SQL 注入联合探测", detail="CWE-89 七变体"))
        self.assertIn("wstg-inpv", sig["families"])

    def test_family_token_word_boundary_not_substring(self):
        # 「enrollment」含 role 子串但不得触发 role 族（词边界律）
        sig = kb_inject.gather_signal(self.gd, _intent(
            title="enrollment 面整理", detail=""))
        self.assertNotIn("wstg-authz", sig["families"])

    def test_engine_hint_feeds_families(self):
        sig = kb_inject.gather_signal(self.gd, _intent(
            title="自动盲注波次", engine="sqlmap"))
        self.assertIn("wstg-inpv", sig["families"])

    def test_zero_signal_intent(self):
        sig = kb_inject.gather_signal(self.gd, _intent(
            title="整理笔记与归档", detail="写周报"))
        self.assertEqual(sig["families"], [])
        self.assertEqual(sig["surfaces"], [])


# =============================================================== 检索面 ==

class TestRetrieve(KbInjectTestBase):
    def _sig(self, families=(), surfaces=(), text=""):
        return {"kind": "matrix-test", "engine": "web-blackbox",
                "families": sorted(families), "surfaces": sorted(surfaces),
                "text": text or " ".join(sorted(families) + sorted(surfaces))}

    def test_technique_cards_match_by_class_cluster(self):
        sel = kb_inject.retrieve(self.kb, self._sig(families=["wstg-inpv"]))
        ids = [c["id"] for c in sel]
        self.assertIn("CP-9101", ids, "类簇命中=inj.sql 技法卡")
        self.assertNotIn("CP-9105", ids, "无关族不硬塞")
        self.assertTrue(all(c["kind"] == "technique" for c in sel))

    def test_negative_miss_card_matches_by_fn_family(self):
        sel = kb_inject.retrieve(self.kb, self._sig(families=["wstg-sess"]))
        neg_ids = [c["id"] for c in sel if c["kind"] == "negative"]
        self.assertIn("CP-9201", neg_ids, "漏报族 jwt 经 wstg-sess 族匹配")
        self.assertIn("CP-9202", neg_ids)

    def test_same_surface_miss_family_ranks_first(self):
        # 同表面历史漏报族优先：idor 卡 conditions 提到 svc-shop → 排最前
        sel = kb_inject.retrieve(self.kb, self._sig(
            families=["wstg-authz"], surfaces=["svc-shop"]))
        self.assertEqual(sel[0]["id"], "CP-9203")

    def test_fact_card_matches_via_surface_mention(self):
        sel = kb_inject.retrieve(self.kb, self._sig(surfaces=["svc-files"]))
        self.assertIn("CP-9205", [c["id"] for c in sel],
                      "负面披露卡按表面命中")

    def test_card_cap_default_five_and_configurable(self):
        sel = kb_inject.retrieve(self.kb, self._sig(families=["wstg-inpv"]))
        self.assertLessEqual(len(sel), 5, "卡数帽=5 防简报爆炸")
        sel2 = kb_inject.retrieve(self.kb, self._sig(families=["wstg-inpv"]),
                                  max_cards=2)
        self.assertLessEqual(len(sel2), 2, "卡数帽可配")

    def test_zero_signal_zero_injection(self):
        sel = kb_inject.retrieve(self.kb, self._sig())
        self.assertEqual(sel, [], "零命中=零注入不硬塞")

    def test_deterministic_order_tie_by_id(self):
        a = kb_inject.retrieve(self.kb, self._sig(families=["wstg-inpv"]))
        b = kb_inject.retrieve(self.kb, self._sig(families=["wstg-inpv"]))
        self.assertEqual([c["id"] for c in a], [c["id"] for c in b])


# =============================================================== 节面 ==

class TestSection(KbInjectTestBase):
    def _sel(self):
        sig = {"kind": "matrix-test", "engine": "web-blackbox",
               "families": ["wstg-sess"], "surfaces": ["svc-shop"],
               "text": "wstg-sess svc-shop"}
        return kb_inject.retrieve(self.kb, sig)

    def test_section_shape_reference_marking_and_cp_source(self):
        sec = kb_inject.build_section(self._sel())
        self.assertIn("相关打法", sec)
        self.assertIn("相关避坑", sec)
        self.assertIn("供参考", sec, "裁定 104：注入=供参考，打法自主")
        self.assertIn("CP-9201", sec)
        self.assertIn("漏报族 jwt", sec)
        self.assertIn("battle-27", sec, "出处可回放（源战号）")
        self.assertIn("适用:", sec)
        self.assertIn("要点:", sec)

    def test_section_reference_not_full_card_body(self):
        sec = kb_inject.build_section(self._sel())
        self.assertNotIn("## 适用条件", sec, "不整卡全文——引用面=名+关键行+出处")

    def test_section_empty_on_zero_selection(self):
        self.assertEqual(kb_inject.build_section([]), "")


# =============================================================== 配置面 ==

class TestConfig(KbInjectTestBase):
    def test_default_on_without_config_file(self):
        cfg = kb_inject.load_config(self.gd)
        self.assertTrue(cfg["enabled"])
        self.assertEqual(cfg["max_cards"], 5)

    def test_config_can_disable(self):
        with open(os.path.join(self.gd, "kb-inject.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"enabled": False}, f)
        self.assertFalse(kb_inject.load_config(self.gd)["enabled"])

    def test_config_max_cards_override(self):
        with open(os.path.join(self.gd, "kb-inject.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"max_cards": 3}, f)
        self.assertEqual(kb_inject.load_config(self.gd)["max_cards"], 3)

    def test_broken_json_degrades_to_default_not_crash(self):
        with open(os.path.join(self.gd, "kb-inject.json"), "w",
                  encoding="utf-8") as f:
            f.write("{not json")
        cfg = kb_inject.load_config(self.gd)
        self.assertTrue(cfg["enabled"], "坏配置降级缺省，不炸简报")

    def test_default_kb_root_honors_tanyin_home(self):
        old = os.environ.get("TANYIN_HOME")
        os.environ["TANYIN_HOME"] = self.gd
        try:
            self.assertEqual(kb_inject.default_kb_root(),
                             os.path.join(self.gd, "knowledge"))
        finally:
            if old is None:
                del os.environ["TANYIN_HOME"]
            else:
                os.environ["TANYIN_HOME"] = old


# =============================================================== 审计面 ==

class TestAudit(KbInjectTestBase):
    def _sel(self):
        sig = {"families": ["wstg-sess"], "surfaces": ["svc-shop"],
               "text": "wstg-sess svc-shop", "kind": "matrix-test",
               "engine": "web-blackbox"}
        return kb_inject.retrieve(self.kb, sig)

    def _rows(self):
        with open(os.path.join(self.gd, "kb-injections.tsv"),
                  encoding="utf-8") as f:
            return [ln.split("\t") for ln in f.read().splitlines() if ln]

    def test_audit_rows_one_per_card_with_battle_warrior_intent(self):
        sel = self._sel()
        n = kb_inject.audit_injections(
            self.gd, battle="battle-42", goal="G-r43",
            warrior="warrior:W-7", intent_id="INT-g1-0100", selection=sel,
            now=lambda: 0)
        self.assertEqual(n, len(sel), "一卡一行")
        rows = self._rows()
        self.assertEqual(rows[0][0], "ts", "首行=表头")
        body = rows[1:]
        self.assertEqual(len(body), len(sel))
        for r, c in zip(body, sel):
            self.assertEqual(r[1], "battle-42")
            self.assertEqual(r[3], "warrior:W-7")
            self.assertEqual(r[4], "INT-g1-0100")
            self.assertEqual(r[5], c["id"])

    def test_audit_idempotent_same_intent_same_cardset(self):
        sel = self._sel()
        kb_inject.audit_injections(self.gd, "battle-42", "G-r43",
                                   "warrior:W-7", "INT-g1-0100", sel,
                                   now=lambda: 0)
        n2 = kb_inject.audit_injections(self.gd, "battle-42", "G-r43",
                                        "warrior:W-7", "INT-g1-0100", sel,
                                        now=lambda: 0)
        self.assertEqual(n2, 0, "同意图同卡集不重落（回合幂等）")
        self.assertEqual(len(self._rows()), len(sel) + 1)

    def test_audit_new_cardset_appends(self):
        sig1 = {"families": ["wstg-sess"], "surfaces": [], "text": "s",
                "kind": "", "engine": ""}
        sig2 = {"families": ["wstg-inpv"], "surfaces": [], "text": "i",
                "kind": "", "engine": ""}
        s1 = kb_inject.retrieve(self.kb, sig1)[:2]
        s2 = kb_inject.retrieve(self.kb, sig2)[:2]
        kb_inject.audit_injections(self.gd, "b", "g", "w", "INT-1", s1,
                                   now=lambda: 0)
        n = kb_inject.audit_injections(self.gd, "b", "g", "w", "INT-1", s2,
                                       now=lambda: 0)
        self.assertEqual(n, len(s2), "卡集变=新审计组")


# ============================================================ 装配接线面 ==

class TestContextWiring(KbInjectTestBase):
    def setUp(self):
        super().setUp()
        from warrior import context
        self.context = context
        self.skill = os.path.join(self.gd, "SKILL.md")
        with open(self.skill, "w", encoding="utf-8") as f:
            f.write(SKILL_STUB)
        # 账本夹具：intents（含租约 owner 标）+matrix（本意图 wstg 族）+timeline
        with open(os.path.join(self.gd, "intents.tsv"), "w",
                  encoding="utf-8") as f:
            f.write("INT-g1-0100\t注入类全家族实证（SQLi/LFI）\t"
                    "probe 实测 [owner:warrior:W-7]"
                    "[lease:2026-09-23T12:00:00Z]\tactive\tweb-blackbox\t"
                    "matrix-test\t\t\t\t\t\t\t\t\t2\t2\t%s\n" % T0)
            f.write("INT-g1-0200\t整理笔记与归档\t写周报\tpending\t"
                    "manual\trecon\t\t\t\t\t\t\t\t\t2\t2\t%s\n" % T0)
        with open(os.path.join(self.gd, "matrix.tsv"), "w",
                  encoding="utf-8") as f:
            f.write("svc-shop\twstg-inpv\t\t\tINT-g1-0100\t2\t\t\n")
            f.write("svc-shop\twstg-sess\t\t\tINT-g1-0100\t2\t\t\n")
        with open(os.path.join(self.gd, "timeline.tsv"), "w",
                  encoding="utf-8") as f:
            f.write("2026-09-23T02:00:00Z\twarrior:W-7\tP3\t"
                    "warrior-progress INT-g1-0100 turn=1\t\t"
                    "%s\t%s\t2\n" % (ZERO64, ONE64))

    def _build(self, intent, **kw):
        root = kw.pop("kb_inject_root", self.kb)
        cb = self.context.ContextBuilder(
            self.gd, skill_path=self.skill, ctx_tokens=8000, kb=True,
            kb_inject_root=root, **kw)
        return cb.build(intent)

    def test_build_appends_inject_section_at_briefing_tail(self):
        r = self._build(_intent())
        self.assertIn("相关打法", r.text)
        self.assertIn("相关避坑", r.text)
        self.assertIn("CP-9101", r.text)
        self.assertTrue(r.text.rstrip().endswith("——需全文按 CP 号到知识库引用"),
                        "注入节=简报尾部（任务节之后）")
        self.assertIn("kb_inject", r.sections)

    def test_build_writes_audit_rows_for_claimed_intent(self):
        self._build(_intent())
        p = os.path.join(self.gd, "kb-injections.tsv")
        self.assertTrue(os.path.isfile(p), "落 goal 目录 kb-injections.tsv")
        with open(p, encoding="utf-8") as f:
            rows = [ln.split("\t") for ln in f.read().splitlines() if ln]
        self.assertEqual(rows[0][0], "ts")
        self.assertTrue(any(r[1] == "" for r in rows[1:]),
                        "battle 列缺省=goal 目录不在 battles/ 下")
        self.assertTrue(all(r[3] == "warrior:W-7" for r in rows[1:]),
                        "战士=租约 owner（哪士）")
        self.assertTrue(all(r[4] == "INT-g1-0100" for r in rows[1:]))

    def test_build_audit_idempotent_across_turns(self):
        self._build(_intent())
        self._build(_intent())          # 第二回合同卡集
        p = os.path.join(self.gd, "kb-injections.tsv")
        with open(p, encoding="utf-8") as f:
            n = len([ln for ln in f.read().splitlines() if ln])
        self.assertLessEqual(n, 6, "回合间幂等（表头+≤5 卡行不翻倍）")

    def test_build_unclaimed_intent_no_audit_rows(self):
        # dry-run 面：意图未被领取（无 owner 标）→ 简报可预览但不落审计
        r = self._build(_intent(iid="INT-g1-0200", title="整理笔记与归档",
                                detail="写周报", kind="recon",
                                engine="manual"))
        self.assertNotIn("相关打法", r.text, "零命中零注入")
        self.assertFalse(os.path.exists(
            os.path.join(self.gd, "kb-injections.tsv")))

    def test_build_config_off_no_injection_no_audit(self):
        with open(os.path.join(self.gd, "kb-inject.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"enabled": False}, f)
        r = self._build(_intent())
        self.assertNotIn("相关打法", r.text)
        self.assertFalse(os.path.exists(
            os.path.join(self.gd, "kb-injections.tsv")))

    def test_build_kb_flag_off_no_injection(self):
        cb = self.context.ContextBuilder(
            self.gd, skill_path=self.skill, ctx_tokens=8000, kb=False,
            kb_inject_root=self.kb)
        r = cb.build(_intent())
        self.assertNotIn("相关打法", r.text)

    def test_build_missing_runtime_kb_degrades_silent(self):
        r = self._build(_intent(), kb_inject_root="/nonexistent-kb")
        self.assertNotIn("相关打法", r.text)
        self.assertNotIn("kb_inject", r.sections)

    def test_build_injection_counts_into_fixed_budget(self):
        # 注入节属固定节：极小窗下 facts 折叠让位，注入节仍在
        cb = self.context.ContextBuilder(
            self.gd, skill_path=self.skill, ctx_tokens=2000, kb=True,
            kb_inject_root=self.kb)
        r = cb.build(_intent())
        self.assertIn("相关打法", r.text)


# ============================================================ 真库锚 ==

class TestRealRuntimeCorpus(unittest.TestCase):
    REAL = os.path.join(os.path.expanduser("~"), ".tanyin", "knowledge")

    @unittest.skipUnless(os.path.isdir(os.path.join(REAL, "concepts")),
                         "运行时库 ~/.tanyin/knowledge 不在（CI 面）")
    def test_ninety_one_cards_stock(self):
        tech, neg = kb_inject.load_runtime_cards(self.REAL)
        self.assertEqual(len(tech), 71, "50 种子+21 蒸馏技法")
        self.assertEqual(len(neg), 20, "20 避坑（漏报 9+证伪 2+披露 9）")
        self.assertTrue(all(c.get("vuln_class") for c in neg),
                        "避坑卡全带 vuln_class（检索注入面同源）")


if __name__ == "__main__":
    unittest.main()

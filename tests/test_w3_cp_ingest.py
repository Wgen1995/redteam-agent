# -*- coding: utf-8 -*-
"""W3 技法入库一致性测试:VulnClaw@3b71e26 specialized 专题全量蒸馏技法卡。

语料实测 50 专题(corpus-audit-research 记 47 为低估;快照=3b71e26 v0.4.0),
已取 8(CP-0001..0008,批次5 T17 sqli/xss/ssrf/ssti/deserialize/cmdi/cors/
open-redirect),本批入库余 42(CP-0009..CP-0050,字母序=编号序)+ CP 索引
knowledge/cp-index.tsv(编号/主题/来源/状态)供 W3 框架引用。
法律敏感律: 攻击性内容只写方法论+靶场验证示例,不提供现成武器——本测试钉死
逐卡 legal 标注在场 + 武器特征黑名单零命中 + 逐步骤纪律标注(哪步涉 L3/外发/回滚)。
.research/ 为 gitignore 语料: 专题全集以本文件常量锚定;语料在场时做实地互证。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SEED = os.path.join(ROOT, "knowledge")
CONCEPTS = os.path.join(SEED, "concepts")
CP_INDEX = os.path.join(SEED, "cp-index.tsv")
CORPUS = os.path.join(ROOT, ".research", "repos", "VulnClaw",
                      "vulnclaw", "skills", "specialized")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")

# 已入库 8 专题(批次5 T17,源卡无 source_topic 字段——索引补齐映射)
TAKEN = {
    "redteam-sqli-detail-pack": "CP-0001",
    "redteam-xss-detail-pack": "CP-0002",
    "redteam-ssrf-detail-pack": "CP-0003",
    "redteam-ssti-detail-pack": "CP-0004",
    "redteam-deserialize-detail-pack": "CP-0005",
    "redteam-cmdi-detail-pack": "CP-0006",
    "redteam-cors-miscfg-detail-pack": "CP-0007",
    "redteam-open-redirect-detail-pack": "CP-0008",
}
# 本批 42 专题(字母序=编号序,CP-0009 起)
NEW_TOPICS = (
    "ai-mcp-security", "android-pentest", "client-reverse", "crypto-toolkit",
    "ctf-crypto", "ctf-misc", "ctf-web", "cve-triage", "hackerone",
    "intranet-pentest-advanced", "osint-recon", "pentest-tools",
    "rapid-checklist", "redteam-ad-detail-pack", "redteam-api-detail-pack",
    "redteam-auth-detail-pack", "redteam-cache-poison-detail-pack",
    "redteam-clickjacking-detail-pack", "redteam-cloud-detail-pack",
    "redteam-code-audit-detail-pack", "redteam-container-detail-pack",
    "redteam-crypto-detail-pack", "redteam-csrf-detail-pack",
    "redteam-cve-lookup", "redteam-cve-validation",
    "redteam-evasion-detail-pack", "redteam-file-detail-pack",
    "redteam-injection-detail-pack", "redteam-logic-detail-pack",
    "redteam-mobile-detail-pack", "redteam-network-detail-pack",
    "redteam-payload-detail-pack", "redteam-postex-detail-pack",
    "redteam-recon-detail-pack", "redteam-recon-intake",
    "redteam-reverse-detail-pack", "redteam-subdomain-takeover-detail-pack",
    "redteam-web-detail-pack", "redteam-xxe-detail-pack",
    "secknowledge-skill", "web-pentest", "web-security-advanced",
)
ALL_TOPICS = sorted(tuple(TAKEN) + NEW_TOPICS)
VOCAB_KEYS = ("wstg-info", "wstg-conf", "wstg-idnt", "wstg-authn", "wstg-authz",
              "wstg-sess", "wstg-inpv", "wstg-errh", "wstg-cryp", "wstg-busl",
              "wstg-clnt", "wstg-apit")
REQUIRED_FM = ("id", "kind", "class", "title", "vocab_version", "vuln_class",
               "applicability", "cost_hint", "last_verified", "status",
               "source_id")
DISCIPLINE_KEYS = ("L3", "外发", "回滚")
SECTION_HEADERS = ("## 场景", "## 步骤", "## 工具引用", "## 纪律标注",
                   "## 证据标准", "## 边界")
# 现成武器特征黑名单(法律敏感律: 方法论可以,武器不行)
WEAPON_MARKERS = ("<?php", "php://filter", "eval($_GET", "<script>alert",
                  "bash -i", "rm -rf ", "/etc/passwd", "powershell -enc",
                  "msfvenom", "nc -e ")
STEP_RE = re.compile(r"^\d+\. .+【纪律:[^】]*】\s*$")
IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def read_page(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("---")
    fm = {}
    for ln in head.splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            fm[k.strip()] = v.strip()
    return fm, body


def new_card_paths():
    out = []
    for n in range(9, 51):
        p = os.path.join(CONCEPTS, "CP-%04d.md" % n)
        if os.path.isfile(p):
            out.append(p)
    return out


def read_index():
    with open(CP_INDEX, encoding="utf-8") as f:
        rows = f.read().splitlines()
    return rows[0].split("\t"), [r.split("\t") for r in rows[1:] if r]


class TestW3CpIngest(unittest.TestCase):

    def test_corpus_topics_anchored(self):
        # 语料在场 → 内嵌全集与实地目录互证(gitignore 环境降级为常量锚)
        if not os.path.isdir(CORPUS):
            self.skipTest("corpus .research 在 gitignore 外(常量锚定)")
        actual = sorted(d for d in os.listdir(CORPUS)
                        if os.path.isdir(os.path.join(CORPUS, d)))
        self.assertEqual(actual, ALL_TOPICS,
                         "专题全集与语料实地不符(常量需随语料勘误更新)")

    def test_every_topic_has_card_and_numbering_continuous(self):
        cols, rows = read_index()
        ids = [r[0] for r in rows]
        self.assertEqual(len(rows), 50, "索引须 50 行(8 已取+42 本批)")
        self.assertEqual(ids, ["CP-%04d" % n for n in range(1, 51)],
                         "编号须 CP-0001..CP-0050 连续无洞")
        topics = [r[3] for r in rows]
        self.assertEqual(sorted(topics), ALL_TOPICS, "索引专题集=全集")
        self.assertEqual(len(set(topics)), 50, "专题→卡一对一不重复")
        for r in rows:
            p = os.path.join(CONCEPTS, r[0] + ".md")
            self.assertTrue(os.path.isfile(p), "缺卡文件: " + r[0])

    def test_index_shape_and_fields_match_frontmatter(self):
        cols, rows = read_index()
        self.assertEqual(cols, ["id", "title", "source_id", "source_topic",
                                "status", "updated"])
        for r in rows:
            self.assertEqual(len(r), 6, "六列齐: " + r[0])
            fm, _ = read_page(os.path.join(CONCEPTS, r[0] + ".md"))
            self.assertEqual(r[1], fm.get("title"), "索引主题=卡 title: " + r[0])
            self.assertEqual(r[2], fm.get("source_id"), "索引来源=卡 source_id")
            self.assertEqual(r[4], fm.get("status"), "索引状态=卡 status")
            self.assertEqual(r[5], fm.get("last_verified"),
                             "updated=卡 last_verified(确定性重生成锚)")
            self.assertTrue(r[3] in ALL_TOPICS, "source_topic 在全集内")

    def test_new_cards_schema_complete(self):
        paths = new_card_paths()
        self.assertEqual(len(paths), 42, "本批新卡恰 42 张")
        for p in paths:
            fm, _ = read_page(p)
            for f in REQUIRED_FM:
                self.assertTrue(fm.get(f), "缺必填字段 %s @ %s" % (f, p))
            self.assertEqual(fm["kind"], "technique")
            self.assertEqual(fm["class"], "K5")
            self.assertIn(fm["status"], ("core", "learned", "demoted"))
            self.assertIn(fm["cost_hint"], ("1", "2", "3"))
            self.assertEqual(fm["vocab_version"], "WSTG-v4.2")
            self.assertEqual(fm["source_id"], "KP-0006")
            self.assertEqual(fm["id"], os.path.basename(p)[:-3], "id=文件名")
            self.assertTrue(fm.get("source_topic") in NEW_TOPICS,
                            "source_topic 须为本批专题: " + p)
            for vc in fm["vuln_class"].split(";"):
                self.assertTrue(vc.split(":", 1)[0] in VOCAB_KEYS,
                                "vuln_class 越表 %r @ %s" % (vc, p))

    def test_new_cards_discipline_annotated_per_step(self):
        for p in new_card_paths():
            fm, body = read_page(p)
            for h in SECTION_HEADERS:
                self.assertIn("\n" + h, "\n" + body, "缺节 %s @ %s" % (h, p))
            sec = body.partition("## 步骤")[2].partition("## ")[0]
            steps = [ln for ln in sec.splitlines() if re.match(r"^\d+\. ", ln)]
            self.assertGreaterEqual(len(steps), 3, "步骤≥3 @ " + p)
            for ln in steps:
                self.assertRegex(ln, STEP_RE, "步骤须带【纪律:…】尾标: " + ln)
            disc = body.partition("## 纪律标注")[2].partition("## ")[0]
            for k in DISCIPLINE_KEYS:
                self.assertIn(k, disc, "纪律标注缺 %s @ %s" % (k, p))

    def test_new_cards_legal_annotation_no_weapons(self):
        for p in new_card_paths():
            fm, body = read_page(p)
            self.assertEqual(fm.get("legal"), "methodology-only",
                             "legal 标注缺/错 @ " + p)
            self.assertIn("法律敏感", body, "边界的法律敏感句在场 @ " + p)
            for m in WEAPON_MARKERS:
                self.assertNotIn(m, body, "现成武器形态 %r 入库 @ %s" % (m, p))
            self.assertIsNone(IP_RE.search(fm.get("title", "") + body),
                              "IP 形态残留 @ " + p)

    def test_index_deterministically_regenerable(self):
        # 从卡文件全量重建索引逐字段比对(漂移即红)
        cols, rows = read_index()
        rebuilt = []
        for r in rows:
            fm, _ = read_page(os.path.join(CONCEPTS, r[0] + ".md"))
            topic = fm.get("source_topic") or next(
                t for t, i in TAKEN.items() if i == r[0])
            rebuilt.append([fm["id"], fm["title"], fm["source_id"], topic,
                            fm["status"], fm["last_verified"]])
        self.assertEqual(rebuilt, rows, "索引与卡文件漂移(须重生成)")

    def test_seed_lint_clean_with_fifty_pages(self):
        # 种子库只读纪律: tmp 副本跑 lint,50 页全过机器门
        seed_log = os.path.join(SEED, "log.md")
        with open(seed_log, "rb") as f:
            before = f.read()
        with tempfile.TemporaryDirectory() as td:
            d = os.path.join(td, "knowledge")
            shutil.copytree(SEED, d)
            r = subprocess.run([sys.executable, KN, "lint",
                                "--knowledge-dir=" + d,
                                "--today=2026-10-18"],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        self.assertIn("50", r.stdout, "lint 须覆盖 50 页 concepts")
        with open(seed_log, "rb") as f:
            self.assertEqual(f.read(), before,
                         "种子库 log.md 被写热(测试隔离泄漏)")


if __name__ == "__main__":
    unittest.main()

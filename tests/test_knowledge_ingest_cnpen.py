# -*- coding: utf-8 -*-
"""批次5 T16：CNPEN 82 五类素材入库（双知识库之一）——降级登记通道。

计划原文：素材执行期从客户素材库拷入（knowledge/sources/cnpen/ 五类=测试全景图/
思路复盘/测试记录 T1-T55/31 份黑盒漏洞单/BurpPOC 合集）；素材不可得=降级登记
不造数据（T17 G-35 同型：SOURCES 落 origin 行+note=待补）。执行期核验：五类素材
均不在仓（素材库在仓外且属禁碰区）——本文件钉死降级态契约：五笔语源登记在案、
零蒸馏页产出（不造数据）、种子库 lint 全绿；词表基线/client 形态两断言作前向
钉子（批次 6+ 素材就位补蒸馏页时仍须过）。
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")
SOURCES = os.path.join(SEED, "sources", "SOURCES.tsv")
CATEGORIES = ("panorama", "retro", "records", "vuln-sheets", "burp-poc")
FORMAL_ZONES = ("concepts", "precedents", "entities", "retros", "business",
                "patterns/core", "patterns/learned", "staging/pages", "targets")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def iter_md(*zones):
    out = []
    for z in zones:
        d = os.path.join(SEED, z)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".md"):
                    out.append(os.path.join(d, fn))
    return out


def read_page(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("---")
    fm = {}
    for ln in head.splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            fm[k.strip()] = v.strip()
    return fm, body


class TestCnpenIngest(unittest.TestCase):
    def test_sources_registered_five_origins(self):
        self.assertTrue(os.path.isfile(SOURCES), "SOURCES.tsv 缺失")
        rows = open(SOURCES, encoding="utf-8").read()
        self.assertEqual(rows.count("\tcnpen\t"), 5, "CNPEN 五类语源各一笔")
        self.assertIn("proprietary", rows)     # 自有语料许可形态注记
        for cat in CATEGORIES:
            self.assertIn(cat, rows, "缺类别行: " + cat)

    def test_pending_rows_marked_no_sha(self):
        # 降级登记行：素材缺位 → sha256 占位 "-"、note 含「待补」（G-35 同型）
        for ln in open(SOURCES, encoding="utf-8").read().splitlines():
            cells = ln.split("\t")
            if len(cells) >= 7 and cells[1] == "cnpen":
                self.assertEqual(cells[3], "-", "未就位语源不得伪造 sha256: " + ln[:40])
                self.assertIn("待补", cells[5], "降级行须带待补注记: " + ln[:40])

    def test_no_fabricated_pages(self):
        # 不造数据：零页引用 CNPEN 语源（正式区蒸馏页零产出——素材就位前禁虚构）
        kp_ids = set()
        for ln in open(SOURCES, encoding="utf-8").read().splitlines():
            cells = ln.split("\t")
            if len(cells) >= 7 and cells[1] == "cnpen":
                kp_ids.add(cells[0])
        self.assertTrue(kp_ids)
        for p in iter_md(*FORMAL_ZONES):
            fm, _ = read_page(p)
            self.assertNotIn(str(fm.get("source_id", "")), kp_ids,
                             "页 %s 引用未就位 CNPEN 语源（涉嫌造数据）" % p)

    def test_lint_passes_on_seed(self):
        kn("init", "--knowledge-dir=" + SEED)   # 幂等：补齐空类目目录后 lint 才可跑
        r = kn("lint", "--knowledge-dir=" + SEED, "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_vocab_baseline_is_wstg_only(self):
        # 前向钉子：防 CNPEN 过拟合——全部页 vuln_class 均为 wstg-* 键或 wstg-XX:sub 形
        for p in iter_md("concepts", "precedents"):
            fm, _ = read_page(p)
            for vc in str(fm.get("vuln_class", "")).split(";"):
                if vc:
                    self.assertTrue(vc.startswith("wstg-"), "%s 私有类 %r" % (p, vc))

    def test_no_raw_client_residue(self):
        # 前向钉子：§9.4 判据③前置——precedents client 字段一律 CLIENT-NN 形态
        for p in iter_md("precedents"):
            fm, _ = read_page(p)
            self.assertRegex(fm.get("client", ""), r"^CLIENT-\d{2,}$")

    def test_downgrade_documented(self):
        # 降级登记通道在案：sources/cnpen/README.md 说明五类预期落位与待补状态
        p = os.path.join(SEED, "sources", "cnpen", "README.md")
        self.assertTrue(os.path.isfile(p), "降级登记 README 缺失")
        t = open(p, encoding="utf-8").read()
        for cat in CATEGORIES:
            self.assertIn(cat, t, "README 未列类别: " + cat)
        self.assertIn("待补", t)


if __name__ == "__main__":
    unittest.main()

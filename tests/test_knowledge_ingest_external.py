# -*- coding: utf-8 -*-
"""批次5 T17：外部语料入库——VulnClaw 47 专题 skill（MIT）首批 8 detail-pack 蒸馏
+ 2 warstory 先例页（占位符化零残留）+ experience 人审门流程注记 + BugHunter/
Threatswarm/CEP 三源缺素材降级登记（G-35）。

VulnClaw 本地只读源=.research/repos/VulnClaw（HEAD 3b71e26；MIT Copyright (c)
2026 UncleC）；四段映射：Domain→applicability/覆盖域表→vuln_class 词表键/
Boundaries→正文边界节/Pivot Hints→failure_modes/Exit Evidence→judgment。
CVE 边界：执行期未联网核验 → 全部页不写 cve_refs 只写方法论内容（R11 离线通道），
待核验清单登记于 LICENSE.note。
"""
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")
SOURCES = os.path.join(SEED, "sources", "SOURCES.tsv")
DOMAIN_RE = re.compile(r"(?i)\b[a-z0-9][a-z0-9-]*\.(example|test|com|net|org|cn|io|co|dev|app|info|biz|xyz|shop|api|local|internal|cloud|online|site|top|vip|edu|gov)\b")
IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


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


class TestExternalIngest(unittest.TestCase):
    def test_vulnclaw_license_note(self):
        p = os.path.join(SEED, "sources", "vulnclaw", "LICENSE.note")
        self.assertTrue(os.path.isfile(p), "LICENSE.note 缺失")
        t = open(p, encoding="utf-8").read()
        self.assertIn("MIT", t)
        self.assertIn("UncleC", t)

    def test_vulnclaw_source_registered_real_sha(self):
        rows = open(SOURCES, encoding="utf-8").read()
        self.assertEqual(rows.count("\tvulnclaw\t"), 1, "vulnclaw 语源恰一笔")
        for ln in rows.splitlines():
            cells = ln.split("\t")
            if len(cells) >= 7 and cells[1] == "vulnclaw":
                self.assertEqual(cells[4], "MIT")
                self.assertRegex(cells[3], r"^[0-9a-f]{64}$", "真实 sha256 锚")
                self.assertIn("3b71e26", cells[5], "HEAD 指纹注记")

    def test_eight_detail_pack_pages(self):
        pages = iter_md("concepts")
        titles = " ".join(read_page(p)[0].get("title", "") for p in pages)
        for kw in ("SQL", "XSS", "SSRF", "SSTI", "反序列化", "命令注入", "CORS", "开放重定向"):
            self.assertIn(kw, titles, "缺 detail-pack 蒸馏页: " + kw)
        self.assertGreaterEqual(len(pages), 8, "concepts 至少 8 页")

    def test_warstory_precedents_sanitized(self):
        pr = iter_md("precedents")
        self.assertGreaterEqual(len(pr), 2, "warstory 先例页 ≥2")
        src = "".join(open(p, encoding="utf-8").read() for p in pr)
        self.assertNotIn("nssctf", src.lower())       # 真平台域名零残留
        self.assertNotIn("NSSCTF{", src)              # flag 零残留

    def test_cve_marks_complete(self):
        # R11 正向钉：cve_refs 非空页必须 cve_verified 逐个覆盖（本批全空=离线通道）
        for p in iter_md("concepts", "precedents"):
            fm, _ = read_page(p)
            refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c]
            verified = set()
            for v in fm.get("cve_verified", []) or []:
                pass
            for c in refs:
                self.assertIn(c, verified, "%s CVE 未核验 %s" % (p, c))

    def test_experience_process_annotated(self):
        t = open(os.path.join(SEED, "checklists", "review-checklist.md"),
                 encoding="utf-8").read()
        self.assertIn("experience", t)
        self.assertIn("Lessons remain pending", t, "人审门原文模式注记在场")
        self.assertIn("0.88", t, "近重复合并阈值登记（G-30）")

    def test_external_missing_sources_degraded(self):
        # G-35 降级登记：三源缺素材 → SOURCES 落 origin 行+note=待补，不阻塞
        rows = open(SOURCES, encoding="utf-8").read()
        for origin in ("bughunter", "threatswarm", "cep"):
            hit = [ln for ln in rows.splitlines()
                   if "\t%s\t" % origin in ln]
            self.assertTrue(hit, "缺降级登记行: " + origin)
            self.assertIn("待补", hit[0])

    def test_no_domain_or_ip_shapes_in_new_pages(self):
        # 全部正式页（含新增蒸馏页）零真域名/IP 形态（与 lint DOMAIN_RE/IP_RE 同源）
        for p in iter_md("concepts", "precedents", "business"):
            t = open(p, encoding="utf-8").read()
            m = DOMAIN_RE.search(t) or IP_RE.search(t)
            self.assertIsNone(m, "%s 残留敏感形态 %r" % (p, m.group(0) if m else ""))

    def test_lint_passes_on_seed(self):
        r = kn("lint", "--knowledge-dir=" + SEED, "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()

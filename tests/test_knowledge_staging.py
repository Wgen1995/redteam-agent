# -*- coding: utf-8 -*-
"""批次5 T10：语源登记（source-register sha256+KP 递增+origin 枚举）+staging 状态机
（staging.tsv 十列 R8）+lint 机器检查四件（契约14 schema/脱敏哨兵 special.scan_text
单源/dedup_key 查重 R10/词表版本 R14+CVE 核验标记 R11）。"""
import hashlib, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
FIX = os.path.join(HERE, "fixtures", "knowledge")
TS = "2026-09-24T12:00:00Z"

ALL_PAGES = ("STG-0001", "STG-0002", "STG-0003", "STG-0004", "STG-0005")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class KnowledgeCase(unittest.TestCase):
    def make_kdir(self, pages=ALL_PAGES, register=True):
        """init 过的干净运行时副本（R7：测试一律 fixtures 副本，绝不指向种子库）。"""
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        self.assertEqual(kn("init", "--knowledge-dir=" + d).returncode, 0)
        if register:
            r = kn("source-register", "--knowledge-dir=" + d,
                   "--path=" + os.path.join(FIX, "raw-sample.txt"),
                   "--origin=cnpen", "--license=proprietary", "--note=CNPEN 复盘",
                   "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for p in pages:
            shutil.copyfile(os.path.join(FIX, "pages", p + ".md"),
                            os.path.join(d, "staging", "pages", p + ".md"))
        return d


class TestSourceRegister(KnowledgeCase):
    def test_source_register_sha_and_id(self):
        d = self.make_kdir(pages=(), register=False)
        r = kn("source-register", "--knowledge-dir=" + d,
               "--path=" + os.path.join(FIX, "raw-sample.txt"),
               "--origin=cnpen", "--license=proprietary", "--note=CNPEN 复盘",
               "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("KP-0001", r.stdout)
        with open(os.path.join(d, "sources", "SOURCES.tsv"), encoding="utf-8") as f:
            row = f.read()
        self.assertIn("cnpen", row)
        # R-T10-1：计划草图「64a 前缀在场」系笔误（夹具 sha 不可能恰为 64 个 a）——
        # 按意图强化为全值断言（对原始字节流式 sha256）
        self.assertIn(sha256_file(os.path.join(FIX, "raw-sample.txt")), row)
        with open(os.path.join(d, "log.md"), encoding="utf-8") as f:
            self.assertIn("|source-register|KP-0001|", f.read())

    def test_register_origin_enum_reject(self):
        d = self.make_kdir(pages=(), register=False)
        r = kn("source-register", "--knowledge-dir=" + d,
               "--path=" + os.path.join(FIX, "raw-sample.txt"),
               "--origin=github", "--license=MIT", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("origin", r.stderr)

    def test_register_kp_increments(self):
        d = self.make_kdir(pages=(), register=False)
        for i in ("", "2"):
            r = kn("source-register", "--knowledge-dir=" + d,
                   "--path=" + os.path.join(FIX, "raw-sample.txt"),
                   "--origin=internal", "--license=MIT", "--note=" + i,
                   "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = kn("source-register", "--knowledge-dir=" + d,
               "--path=" + os.path.join(FIX, "raw-sample.txt"),
               "--origin=internal", "--license=MIT", "--timestamp=" + TS)
        self.assertIn("KP-0003", r.stdout)


class TestStagingLint(KnowledgeCase):
    def test_lint_flags_each_failure_class(self):
        d = self.make_kdir()
        r = kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        for kw in ("STG-0002", "泄漏形态", "STG-0003", "dedup", "STG-0004", "cve_verified",
                   "STG-0005", "vocab_version"):
            self.assertIn(kw, r.stdout)

    def test_clean_page_passes_and_transitions(self):
        d = self.make_kdir(pages=("STG-0001",))
        r = kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        with open(os.path.join(d, "staging", "staging.tsv"), encoding="utf-8") as f:
            st = f.read()
        cols = st.splitlines()[0].split("\t")
        self.assertEqual(cols, ["staging_id", "page_id", "class", "title", "source_id",
                                "status", "checksum", "created", "approved_by", "approved_at"])
        self.assertIn("lint-passed", st)
        self.assertIn("STG-0001", st)
        with open(os.path.join(d, "log.md"), encoding="utf-8") as f:
            self.assertIn("|lint|STG-0001|pass", f.read())

    def test_lint_timestamp_required(self):
        # G-23 同律：进产物时间戳显式传入，禁墙钟
        d = self.make_kdir(pages=("STG-0001",))
        r = kn("lint", "--knowledge-dir=" + d)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--timestamp", r.stderr)

    def test_lint_missing_frontmatter_flagged(self):
        d = self.make_kdir(pages=())
        with open(os.path.join(d, "staging", "pages", "STG-0009.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("没有 front-matter 的裸文本\n")
        r = kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("STG-0009", r.stdout)


class TestScanTextSingleSource(unittest.TestCase):
    """special.scan_text 纯文本 API（T10 单源化；scan_text_file 改调它行为零变——
    redact 面回归由金样 read-redact-scan 与 test_redact_injection 承载）。"""

    def test_scan_text_returns_line_numbered_hits(self):
        sys.path.insert(0, os.path.join(ROOT, "cli"))
        from ledger import special
        hits = special.scan_text("ok line\ntoken=abcdefghijklmnop\n")
        self.assertIn(("token 赋值", 2), [(n, ln) for n, ln, _c in hits])
        hits2 = special.scan_text("x {{vault:cred-1}} y\n")
        self.assertIn(("占位符残留", 1), [(n, ln) for n, ln, _c in hits2])

    def test_scan_text_file_delegates_byte_identical(self):
        sys.path.insert(0, os.path.join(ROOT, "cli"))
        from ledger import special
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        p = os.path.join(tmp, "s.txt")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("a\ntoken=abcdefghijklmnopqrst\n{{vault:cred-2}}\n")
        leaks = special.scan_text_file(p, "s.txt")
        rels = [loc for loc, _m in leaks]
        self.assertIn("s.txt:2:1", rels)   # 明文模式带列号（原行为）
        self.assertIn("s.txt:3", rels)     # 占位符不带列号（原行为）
        msgs = [m for _l, m in leaks]
        self.assertIn("报告残留占位符（P5 占位符零泄漏）", msgs)
        self.assertTrue(any(m.startswith("明文凭据模式:") for m in msgs))


if __name__ == "__main__":
    unittest.main()

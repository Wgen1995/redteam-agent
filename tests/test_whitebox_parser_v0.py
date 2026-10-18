# -*- coding: utf-8 -*-
"""W4 白盒车道A 解析器 v0 + GenSift .pattern 翻译（#15-3 裁决: 方言(b)）。

钉死四件事:
① ERE→Python re 翻译: POSIX 括号类显式展开（[[:space:]] 及混合括号形态
   [[:space:](=,]）,不认识的语法跳过并记录——诚实,不猜;
② fixtures 迁 CI: pos 命中集=manifest expected_patterns（GenSift grep -E 实跑
   口径）,neg 零命中——翻译件语义等价的回归基准;
③ 谱图工件: codegraph.jsonl（符号表+调用边,每条带 file:line+签名哈希）+
   pattern-hits.jsonl + digest 事实一条——确定性: 同输入逐字节同输出（金样钉死）;
④ 密度律: 引擎不写账本——出目录只有工件+digest,无任何 .tsv 账本行。
"""
import filecmp
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE = os.path.join(ROOT, "engines", "whitebox")
STAGING_PATTERNS = os.path.join(ROOT, "knowledge", "staging", "gensift-intake",
                                "classes", "patterns")
FIX = os.path.join(HERE, "fixtures", "whitebox")
SRC_TREE = os.path.join(FIX, "src-tree")
FROZEN_PATTERNS = os.path.join(FIX, "patterns")
GOLDEN = os.path.join(FIX, "golden")

sys.path.insert(0, ENGINE)
import parser_v0 as wb  # noqa: E402


def sha256_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def line_of(path, needle):
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if needle in line:
                return i
    raise AssertionError("needle not found: %r in %s" % (needle, path))


class TestEreTranslation(unittest.TestCase):
    """① POSIX 类翻译 + 未知语法跳过记录。"""

    def test_standalone_posix_class_expanded(self):
        py, reason = wb.translate_ere(r"a[[:space:]]b")
        self.assertIsNone(reason)
        self.assertTrue(re.search(py, "a b"))
        self.assertTrue(re.search(py, "a\tb"))
        self.assertFalse(re.search(py, "axb"))

    def test_posix_class_inside_bigger_bracket(self):
        # CI-P12 原文形态: 类 token 与字面字符同处一个括号表达式
        py, reason = wb.translate_ere(r"(^|[[:space:](=,])eval\(")
        self.assertIsNone(reason)
        rx = re.compile(py)
        self.assertTrue(rx.search(" eval("))
        self.assertTrue(rx.search("=eval("))
        self.assertTrue(rx.search("x,eval("))
        self.assertFalse(rx.search("model.eval("))

    def test_unknown_posix_class_skipped_with_reason(self):
        py, reason = wb.translate_ere(r"[[:graph:]]x")
        self.assertIsNone(py)
        self.assertIn("[:graph:]", reason)

    def test_unknown_letter_escape_skipped_with_reason(self):
        # GNU \b/\q 类 Python re 不认的字面转义: 编译失败=诚实跳过,不猜语义
        for bad in (r"\<word", r"\q(x"):
            py, reason = wb.translate_ere(bad)
            self.assertIsNone(py, bad)
            self.assertTrue(reason, bad)

    def test_residual_posix_token_never_survives(self):
        # 防静默错译: [[:space:]] 在 Python 原样可编译但语义=字面字符集——
        # 翻译后若仍有 [:xx:] token 一律判失败
        py, reason = wb.translate_ere(r"[[:space:]]")
        self.assertIsNone(reason)
        self.assertNotIn("[:", py)

    def test_frozen_files_fully_translated(self):
        compiled, skipped = wb.translate_pattern_dir(FROZEN_PATTERNS)
        rows = sum(len(p["patterns"]) for p in wb.load_pattern_dir(FROZEN_PATTERNS))
        self.assertEqual(len(compiled), rows)
        self.assertEqual(skipped, [], "冻结 8 件应零跳过")

    def test_staging_corpus_honesty(self):
        # 59 件全量: 每行要么翻译成功要么带理由跳过——无第三态、无静默
        files = wb.load_pattern_dir(STAGING_PATTERNS)
        self.assertEqual(len(files), 59)
        compiled, skipped = wb.translate_pattern_dir(STAGING_PATTERNS)
        rows = sum(len(p["patterns"]) for p in files)
        self.assertEqual(len(compiled) + len(skipped), rows)
        for s in skipped:
            for k in ("class", "lang", "pattern_id", "ere", "reason"):
                self.assertIn(k, s)


class TestFixtureRegression(unittest.TestCase):
    """② fixtures 迁 CI: 对账口径照 classes/fixture-spec.md §3。"""

    ENUM = os.path.join(FIX, "enum")

    @classmethod
    def setUpClass(cls):
        cls.compiled, cls.skipped = wb.translate_pattern_dir(FROZEN_PATTERNS)
        cls.by_key = {}
        for c in cls.compiled:
            cls.by_key.setdefault((c["class"], c["lang"]), []).append(c)

    def _manifest_rows(self, cls_dir, lang):
        mpath = os.path.join(self.ENUM, cls_dir, lang, "manifest.tsv")
        with open(mpath, encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("\t")
            col_file = header.index("file")
            col_kind = header.index("kind")
            col_exp = header.index("expected_patterns")
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) > col_exp:
                    yield parts[col_file], parts[col_kind], parts[col_exp]

    def _scan(self, cls_dir, lang, rel):
        path = os.path.join(self.ENUM, cls_dir, lang, rel)
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        pats = self.by_key[(cls_dir, lang)]
        return {h["pattern_id"] for h in wb.scan_lines(os.path.join(cls_dir, lang, rel),
                                                        lines, pats)}

    def test_pos_hit_set_equals_manifest_expected(self):
        n = 0
        for cls_dir, lang in wb.enum_fixture_langs(self.ENUM):
            for rel, kind, exp in self._manifest_rows(cls_dir, lang):
                if kind != "pos":
                    continue
                hits = self._scan(cls_dir, lang, rel)
                expected = set(x for x in exp.split("\u3001") if x)
                self.assertTrue(hits, "%s/%s/%s pos 必须命中≥1" % (cls_dir, lang, rel))
                self.assertEqual(hits, expected,
                                 "%s/%s/%s 命中集≠manifest expected" % (cls_dir, lang, rel))
                n += 1
        self.assertGreaterEqual(n, 49, "代表子集 pos 覆盖（8 类×lang 实选 49 件）")

    def test_neg_zero_hits(self):
        for cls_dir, lang in wb.enum_fixture_langs(self.ENUM):
            for rel, kind, exp in self._manifest_rows(cls_dir, lang):
                if kind != "neg":
                    continue
                hits = self._scan(cls_dir, lang, rel)
                self.assertEqual(hits, set(),
                                 "%s/%s/%s neg 必须零命中" % (cls_dir, lang, rel))

    def test_noise_hits_are_valid_ids_only(self):
        # noise 允许命中不计对账——只钉命中 id 均为本类合法 id（无跨类污染）
        valid = {c["pattern_id"] for c in self.compiled}
        for cls_dir, lang in wb.enum_fixture_langs(self.ENUM):
            ids = {c["pattern_id"] for c in self.by_key[(cls_dir, lang)]}
            for rel, kind, exp in self._manifest_rows(cls_dir, lang):
                if kind != "noise":
                    continue
                hits = self._scan(cls_dir, lang, rel)
                self.assertTrue(hits <= ids, (cls_dir, lang, rel, hits))
                self.assertTrue(hits <= valid)


class TestCodegraphGolden(unittest.TestCase):
    """③+④ 谱图工件/确定性/密度律（CLI 全流程,金样钉死）。"""

    @classmethod
    def setUpClass(cls):
        cls.out1 = tempfile.mkdtemp()
        cls.out2 = tempfile.mkdtemp()
        for out in (cls.out1, cls.out2):
            r = subprocess.run([sys.executable, os.path.join(ENGINE, "parser_v0.py"),
                                "--source-dir", SRC_TREE, "--out-dir", out,
                                "--patterns-dir", FROZEN_PATTERNS],
                               capture_output=True, text=True)
            assert r.returncode == 0, r.stdout + r.stderr
        def _load(name):
            with open(os.path.join(cls.out1, name), encoding="utf-8") as f:
                return [json.loads(l) for l in f]
        cls.graph = _load("codegraph.jsonl")
        cls.hits = _load("pattern-hits.jsonl")
        with open(os.path.join(cls.out1, "digest.json"), encoding="utf-8") as f:
            cls.digest = json.load(f)

    def _sym(self, **kw):
        got = [g for g in self.graph if g["record"] == "symbol"
               and all(g.get(k) == v for k, v in kw.items())]
        return got

    def test_python_symbols_with_signature_hash(self):
        line = line_of(os.path.join(SRC_TREE, "app.py"), "def handler")
        got = self._sym(lang="python", name="handler")
        self.assertEqual(len(got), 1)
        s = got[0]
        self.assertEqual((s["file"], s["line"]), ("app.py", line))
        self.assertEqual(s["kind"], "function")
        self.assertEqual(s["qualname"], "handler")
        self.assertEqual(s["signature"], "handler(name)")
        self.assertEqual(s["sig_sha256"], sha256_text("handler(name)"))
        self.assertRegex(s["sig_sha256"], r"^[0-9a-f]{64}$")

    def test_python_class_method_qualified(self):
        got = self._sym(lang="python", name="query")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["qualname"], "Api.query")
        self.assertEqual(got[0]["kind"], "method")
        self.assertEqual(got[0]["signature"], "query(self, name)")

    def test_java_symbols(self):
        cls = self._sym(lang="java", name="UserService")
        self.assertEqual(len(cls), 1)
        self.assertEqual(cls[0]["kind"], "class")
        self.assertEqual(cls[0]["file"], "services/UserService.java")
        line = line_of(os.path.join(SRC_TREE, "services", "UserService.java"),
                       "boolean resetPassword")
        m = self._sym(lang="java", name="resetPassword")
        self.assertEqual((m[0]["line"], m[0]["kind"]), (line, "method"))
        self.assertEqual(m[0]["qualname"], "UserService.resetPassword")
        self.assertEqual(m[0]["signature"], "resetPassword(String token)")

    def test_ts_symbols(self):
        for name, kind in (("parseXml", "function"), ("loadRaw", "function"),
                           ("Auditor", "class")):
            got = self._sym(lang="ts", name=name)
            self.assertEqual((len(got), got[0]["kind"]), (1, kind), name)
        m = self._sym(lang="ts", name="audit")
        self.assertEqual(m[0]["qualname"], "Auditor.audit")

    def test_call_edges(self):
        def call(**kw):
            return [g for g in self.graph if g["record"] == "call"
                    and all(g.get(k) == v for k, v in kw.items())]
        self.assertEqual(len(call(file="app.py", caller="Api.query", callee="execute")), 1)
        self.assertEqual(len(call(file="app.py", caller="handler", callee="Api")), 1)
        self.assertEqual(len(call(file="services/UserService.java",
                                  caller="UserService.findUser", callee="executeQuery")), 1)
        self.assertEqual(len(call(file="util.ts", caller="fetchAvatar", callee="fetch")), 1)
        self.assertEqual(len(call(file="util.ts", caller="Auditor.audit", callee="log")), 1)
        edge = call(file="app.py", caller="handler", callee="Api")[0]
        self.assertIn("sig_sha256", edge)
        self.assertRegex(edge["sig_sha256"], r"^[0-9a-f]{64}$")

    def test_pattern_hits_artifact(self):
        def hit(**kw):
            return [h for h in self.hits if all(h.get(k) == v for k, v in kw.items())]
        line = line_of(os.path.join(SRC_TREE, "app.py"), "cur.execute")
        self.assertEqual(len(hit(**{"class": "sqli", "lang": "python",
                                    "pattern_id": "S-P01",
                                    "file": "app.py", "line": line})), 1)
        jline = line_of(os.path.join(SRC_TREE, "services", "UserService.java"),
                        "DocumentBuilderFactory.newInstance")
        self.assertEqual(len(hit(**{"class": "xxe", "lang": "java",
                                    "pattern_id": "X-J01",
                                    "file": "services/UserService.java",
                                    "line": jline})), 1)
        self.assertEqual(len(hit(**{"class": "xxe", "lang": "java",
                                    "pattern_id": "X-J02",
                                    "file": "services/UserService.java",
                                    "line": jline})), 1,
                         "同一行多 pattern 双命中都要落")
        aline = line_of(os.path.join(SRC_TREE, "services", "UserService.java"),
                        "resetPassword")
        self.assertEqual(len(hit(**{"class": "authn", "lang": "java",
                                    "pattern_id": "AN-J01",
                                    "file": "services/UserService.java",
                                    "line": aline})), 1)
        self.assertEqual(len(hit(**{"class": "ssrf", "lang": "ts",
                                    "pattern_id": "SS-T01", "file": "util.ts"})), 1)
        self.assertEqual(len(hit(**{"class": "proto-pollution", "lang": "ts",
                                    "pattern_id": "PP-T11", "file": "util.ts"})), 1)
        self.assertEqual(len(hit(**{"class": "sqli", "lang": "ts",
                                    "pattern_id": "S-T02", "file": "util.ts"})), 1)
        for h in self.hits:  # 密值纪律: 命中行原文不入工件（secrets 类防泄露）
            self.assertNotIn("line_text", h)
            self.assertNotIn("matched", h)

    def test_digest_fact_shape(self):
        d = self.digest
        self.assertEqual(d["kind"], "codegraph-digest")
        self.assertTrue(d["parser_version"].startswith("whitebox-parser/"))
        n_sym = sum(1 for g in self.graph if g["record"] == "symbol")
        n_call = sum(1 for g in self.graph if g["record"] == "call")
        self.assertEqual(d["symbol_count"], n_sym)
        self.assertEqual(d["edge_count"], n_call)
        with open(os.path.join(self.out1, "codegraph.jsonl"), "rb") as f:
            raw = f.read()
        self.assertEqual(d["codegraph_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(d["pattern_hits_count"], len(self.hits))
        self.assertEqual(d["files"]["python"], 1)
        self.assertEqual(d["files"]["java"], 1)
        self.assertEqual(d["files"]["ts"], 1)
        self.assertEqual(d["patterns"]["files"], 8)
        self.assertEqual(d["patterns"]["skipped"], [])
        self.assertEqual(d["patterns"]["translated"], d["patterns"]["rows"])

    def test_density_law_engine_never_writes_ledger(self):
        # 密度律: 只有 L0 文件/L1 入口经总控入账;引擎出目录无任何账本文件
        names = sorted(os.listdir(self.out1))
        self.assertEqual(names, ["codegraph.jsonl", "digest.json", "pattern-hits.jsonl"])
        for root, _dirs, files in os.walk(self.out1):
            for f in files:
                self.assertFalse(f.endswith(".tsv"), f)
        with open(os.path.join(self.out1, "digest.json"), encoding="utf-8") as f:
            raw = f.read()
        self.assertEqual(raw.count("\n"), 0, "digest=事实一条(单 JSON 对象)")

    def test_no_absolute_paths_in_outputs(self):
        for name in ("codegraph.jsonl", "pattern-hits.jsonl", "digest.json"):
            with open(os.path.join(self.out1, name), encoding="utf-8") as f:
                body = f.read()
            self.assertNotIn(self.out1, body)
            self.assertNotIn(SRC_TREE, body)
            self.assertNotIn("/Users/", body)
            self.assertNotIn("/tmp/", body)

    def test_determinism_two_runs_byte_identical(self):
        for name in ("codegraph.jsonl", "pattern-hits.jsonl", "digest.json"):
            self.assertTrue(filecmp.cmp(os.path.join(self.out1, name),
                                        os.path.join(self.out2, name), shallow=False),
                            name + " 两跑必须逐字节同输出")

    def test_golden_pinned(self):
        for name in ("codegraph.jsonl", "pattern-hits.jsonl", "digest.json"):
            gpath = os.path.join(GOLDEN, name)
            self.assertTrue(os.path.isfile(gpath), "金样缺失: " + name)
            self.assertTrue(filecmp.cmp(os.path.join(self.out1, name), gpath, shallow=False),
                            name + " 输出漂移(有意变更须随提交更新金样并归因)")


if __name__ == "__main__":
    unittest.main()

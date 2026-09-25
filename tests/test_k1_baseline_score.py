# -*- coding: utf-8 -*-
"""批次5 T12：K1 严重度期望基线表落表（12 wstg 全行+4 子类示范，方法论映射评定
人审冻结）+ tanyin-knowledge score 只读算分（三因子可审计复算+查表次序
细类→wstg 类→缺省 0.5+告警；Top-K 仍归总控，铁律 7/契约 09 §4 边界 2）。"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")
FIX = os.path.join(HERE, "fixtures", "G-g1")
BASELINE = os.path.join(SEED, "methodology", "k1-baseline.tsv")
WSTG12 = ("wstg-info", "wstg-conf", "wstg-idnt", "wstg-authn", "wstg-authz",
          "wstg-sess", "wstg-inpv", "wstg-errh", "wstg-cryp", "wstg-busl",
          "wstg-clnt", "wstg-apit")
BASELINE_COLS = "vuln_class\tseverity_expect\tcost_hint\trationale_brief\tvocab_version"


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def read_vocab():
    vocab = set()
    with open(os.path.join(ROOT, "shared", "VOCAB.md"), encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln.startswith("- wstg-"):
                vocab.add(ln[2:])
    return vocab


class TestK1Baseline(unittest.TestCase):
    def test_baseline_covers_vocab_exactly(self):
        vocab = read_vocab()
        self.assertEqual(len(vocab), 12, "词表应 12 类")
        with open(BASELINE, encoding="utf-8") as f:
            rows = [l.split("\t") for l in f.read().splitlines()[1:] if l]
        keys = {r[0] for r in rows}
        self.assertTrue(vocab <= keys, "VOCAB 缺行: %s" % (vocab - keys))
        extra = {k for k in keys if not (k in vocab or ":" in k)}
        self.assertFalse(extra, "VOCAB 外行: %s" % extra)
        self.assertEqual(len(rows), 16, "12 全类+4 子类示范行")
        for r in rows:
            self.assertEqual(len(r), 5, "行须五列: %r" % (r,))
            if ":" in r[0]:
                self.assertIn(r[0].split(":", 1)[0], vocab, "细类行须父类前缀: %r" % (r,))
            self.assertIn(r[1], ("0.3", "0.5", "0.6", "0.7", "0.8", "0.9"),
                          "severity_expect 值域: %r" % (r,))
            self.assertIn(r[2], ("1", "2", "3"), "cost_hint 值域: %r" % (r,))
            self.assertEqual(r[4], "WSTG-v4.2", "vocab_version 同源: %r" % (r,))

    def test_wstg_map_present(self):
        p = os.path.join(SEED, "methodology", "k1-wstg-map.tsv")
        with open(p, encoding="utf-8") as f:
            rows = [l for l in f.read().splitlines()[1:] if l]
        self.assertEqual(len(rows), 12, "WSTG 12 类各一行映射")
        for l in rows:
            self.assertEqual(len(l.split("\t")), 3, "三列键映射: " + l)


class TestScore(unittest.TestCase):
    def test_score_deterministic_on_fixture(self):
        args = ("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
                "--vuln-class=wstg-authz", "--asset=AST-g1-0002", "--today=2026-09-24")
        r = kn(*args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(set(out), {"severity_expect", "asset_value", "exploitability",
                                    "priority", "sources"})
        self.assertEqual(out["severity_expect"], 0.9, "K1 基线 wstg-authz 行")
        self.assertLessEqual(out["priority"], 1.0)
        src = out["sources"]
        for k in ("severity_row", "asset_value_source", "reach_count", "active_creds",
                  "match_hits", "warnings"):
            self.assertIn(k, src, "sources 可审计复算字段缺 " + k)
        self.assertEqual(src["severity_row"], "wstg-authz")
        r2 = kn(*args)
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(r.stdout, r2.stdout, "score 双跑须字节一致（禁墙钟）")

    def test_subclass_preferred_over_category(self):
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
               "--vuln-class=wstg-inpv:inj.sql", "--asset=AST-g1-0002",
               "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["sources"]["severity_row"], "wstg-inpv:inj.sql",
                         "查表次序：细类行优先于父类")
        self.assertEqual(out["severity_expect"], 0.9)

    def test_unknown_class_defaults_with_warning(self):
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
               "--vuln-class=wstg-none:xx", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("baseline-miss", r.stdout, "缺省告警行")
        out = json.loads(r.stdout)
        self.assertEqual(out["severity_expect"], 0.5, "缺省 0.5")
        self.assertTrue(out["sources"]["warnings"])

    def test_today_required(self):
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
               "--vuln-class=wstg-authz")
        self.assertEqual(r.returncode, 2, "先例命中因子窗口判定须显式 --today（G-34）")

    def _minimal_goal(self, assets_rows=(), creds_rows=()):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        if assets_rows:
            with open(os.path.join(d, "assets.tsv"), "w", encoding="utf-8",
                      newline="\n") as f:
                for r_ in assets_rows:
                    f.write("\t".join(r_) + "\n")
        if creds_rows:
            with open(os.path.join(d, "creds.tsv"), "w", encoding="utf-8",
                      newline="\n") as f:
                for r_ in creds_rows:
                    f.write("\t".join(r_) + "\n")
        return d

    def test_asset_value_from_meta_bv(self):
        # assets.meta bv:<0-1> 人标业务价值；缺省 0.5（未标=不加分，P3 勘误对齐）
        d = self._minimal_goal(assets_rows=[["AST-t1-0001", "root-domain", "corp.example",
                                             "bv:0.8", "1", "2", "2026-09-01"]])
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + d,
               "--vuln-class=wstg-authz", "--asset=corp.example", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["asset_value"], 0.8)
        self.assertEqual(out["exploitability"], 0.4, "scope-root 可达=0.4，无凭据无先例")
        self.assertEqual(round(out["priority"], 4), round(0.9 * 0.8 * 0.4, 4))

    def test_default_asset_value_when_unmarked(self):
        d = self._minimal_goal()
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + d,
               "--vuln-class=wstg-authz", "--asset=nowhere", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["asset_value"], 0.5)
        self.assertEqual(out["exploitability"], 0.0)

    def test_creds_and_precedent_hit_factors(self):
        # 0.3×(active creds>0) + 0.3×(先例命中>0)——运行时库+最小 goal 双因子合成
        d = self._minimal_goal(
            assets_rows=[["AST-t1-0001", "root-domain", "corp.example", "bv:0.8",
                          "1", "2", "2026-09-01"]],
            creds_rows=[["CRED-t1-0001", "session", "admin", "{{vault:u1}}",
                         "{{vault:c1}}", "corp.example", "", "", "", "", "active",
                         "", "", "2", "2026-09-01", ""]])
        lib = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, lib, ignore_errors=True)
        self.assertEqual(kn("init", "--knowledge-dir=" + lib).returncode, 0)
        page = ("---\n"
                "id: PR-0001\n"
                "kind: precedent\n"
                "class: K2\n"
                "title: 因子合成先例\n"
                "client: CLIENT-07\n"
                "scope_asset: corp.example\n"
                "window: 2026-01-01..2026-12-31\n"
                "outcome: 1 处\n"
                "---\n"
                "## 摘要\n")
        with open(os.path.join(lib, "precedents", "PR-0001.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(page)
        r = kn("score", "--knowledge-dir=" + lib, "--goal-dir=" + d,
               "--vuln-class=wstg-authz", "--asset=corp.example", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["exploitability"], 1.0, "0.4 可达+0.3 凭据+0.3 先例命中")
        self.assertIn("PR-0001", json.dumps(out["sources"]["match_hits"]),
                      "命中页入 sources 可审计")


class TestLintBaselineGate(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)

    def _write_baseline(self, body):
        p = os.path.join(self.d, "methodology", "k1-baseline.tsv")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)

    def test_coverage_gap_fails_lint(self):
        # K1 lint 断言：VOCAB 每 wstg-* 键恰一行——缺行 FAIL
        self._write_baseline(BASELINE_COLS + "\nwstg-info\t0.3\t1\t侦察\tWSTG-v4.2\n")
        r = kn("lint", "--knowledge-dir=" + self.d, "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("K1", r.stdout)
        self.assertIn("wstg-authz", r.stdout, "指名缺行键")

    def test_out_of_vocab_row_fails_lint(self):
        body = BASELINE_COLS + "\n"
        for k in WSTG12:
            body += "%s\t0.5\t2\t占位\tWSTG-v4.2\n" % k
        body += "not-a-vocab-key\t0.5\t2\t越界行\tWSTG-v4.2\n"
        self._write_baseline(body)
        r = kn("lint", "--knowledge-dir=" + self.d, "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("K1", r.stdout)
        self.assertIn("not-a-vocab-key", r.stdout)

    def test_full_table_passes_lint(self):
        body = BASELINE_COLS + "\n"
        for k in WSTG12:
            body += "%s\t0.5\t2\t占位\tWSTG-v4.2\n" % k
        self._write_baseline(body)
        r = kn("lint", "--knowledge-dir=" + self.d, "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("K1", r.stdout)

    def test_no_baseline_skips_gate(self):
        # init 运行时库无基线文件 → 不判 K1（种子库/发行库才断言；批次 6 安装器拷贝）
        r = kn("lint", "--knowledge-dir=" + self.d, "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("K1", r.stdout)


if __name__ == "__main__":
    unittest.main()

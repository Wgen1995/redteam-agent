# -*- coding: utf-8 -*-
"""批次5 T11：approve/commit（状态机+index 重生成）/export（graph.ndjson 确定性重建，
两次执行字节一致）/match（三元组全同+窗口过期失效+跨客户永不命中+--today 必填 G-34+
[stale] R11）/neighbors（A8 外推入口）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
FIX = os.path.join(HERE, "fixtures", "knowledge")
TS = "2026-09-24T12:00:00Z"
TS2 = "2026-09-24T13:00:00Z"

PAGE_OK = """---
id: STG-0001
kind: technique
class: K5
title: 门禁测试技法页
vocab_version: WSTG-v4.2
vuln_class: wstg-inpv
applicability: 测试流水线用
cost_hint: 1
last_verified: 2026-09-01
status: learned
source_id: KP-0001
staging_status: staged
---
## 要点

approve/commit 全链走查页。
"""


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class KnowledgeCase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)

    def make_lib(self):
        """export/match/neighbors 用：init+注册语源+预置正式区合法页（PR-0001/EN-0001）。"""
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)
        r = kn("source-register", "--knowledge-dir=" + self.d,
               "--path=" + os.path.join(FIX, "raw-sample.txt"),
               "--origin=internal", "--license=MIT", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for rel in ("precedents/PR-0001.md", "entities/EN-0001.md"):
            dst = os.path.join(self.d, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(FIX, rel), dst)
        return self.d

    def make_clean(self):
        """commit 流水线用：init+注册语源的干净运行时库。"""
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)
        r = kn("source-register", "--knowledge-dir=" + self.d,
               "--path=" + os.path.join(FIX, "raw-sample.txt"),
               "--origin=internal", "--license=MIT", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.d

    def write_page(self, name="STG-0001", text=PAGE_OK, title=None):
        t = text.replace("id: STG-0001", "id: " + name) if name != "STG-0001" else text
        if title:
            lines = t.splitlines()
            t = "\n".join("title: " + title if ln.startswith("title:") else ln
                          for ln in lines) + "\n"
        p = os.path.join(self.d, "staging", "pages", name + ".md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)


class TestApproveCommit(KnowledgeCase):
    def test_commit_moves_and_regenerates_index(self):
        # 走完 register→手写页→lint→approve→commit：concepts/CP-0001.md 在场、
        # staging/pages 清空、index.md 计数含 K5=1
        d = self.make_clean()
        self.write_page()
        self.assertEqual(kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS).returncode, 0)
        r = kn("approve", "--knowledge-dir=" + d, "--page=STG-0001",
               "--approver=评审人", "--timestamp=" + TS2)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(d, "staging", "staging.tsv"), encoding="utf-8") as f:
            st = f.read()
        self.assertIn("approved", st)
        self.assertIn("评审人", st)
        r = kn("commit", "--knowledge-dir=" + d, "--page=STG-0001", "--timestamp=" + TS2)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cp = os.path.join(d, "concepts", "CP-0001.md")
        self.assertTrue(os.path.isfile(cp), "页文件未迁至类目录")
        body = open(cp, encoding="utf-8").read()
        self.assertIn("id: CP-0001", body)
        self.assertNotIn("staging_status", body)
        self.assertEqual(os.listdir(os.path.join(d, "staging", "pages")), [])
        idx = open(os.path.join(d, "index.md"), encoding="utf-8").read()
        self.assertIn("K5 concepts: 1 页", idx)
        ov = open(os.path.join(d, "overview.md"), encoding="utf-8").read()
        self.assertIn("WSTG-v4.2", ov)
        with open(os.path.join(d, "log.md"), encoding="utf-8") as f:
            lg = f.read()
        self.assertIn("|approve|STG-0001|approver=评审人", lg)
        self.assertIn("|commit|CP-0001|from=STG-0001", lg)

    def test_approve_rejects_staged(self):
        # 状态机：staged →(lint)→ lint-passed →(approve)→ approved；脏页停在 staged
        d = self.make_clean()
        shutil.copyfile(os.path.join(FIX, "pages", "STG-0002.md"),
                        os.path.join(d, "staging", "pages", "STG-0002.md"))
        kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS)
        r = kn("approve", "--knowledge-dir=" + d, "--page=STG-0002",
               "--approver=x", "--timestamp=" + TS2)
        self.assertEqual(r.returncode, 1)
        self.assertIn("状态机", r.stderr)

    def test_commit_requires_approved(self):
        d = self.make_clean()
        self.write_page()
        kn("lint", "--knowledge-dir=" + d, "--timestamp=" + TS)
        r = kn("commit", "--knowledge-dir=" + d, "--page=STG-0001", "--timestamp=" + TS2)
        self.assertEqual(r.returncode, 1)
        self.assertIn("状态机", r.stderr)

    def test_commit_dedup_final_check_rejects(self):
        # R10 防御纵深：同 dedup_key 重复 commit=REJECT（lint 组告警逐页放行 lint-passed，
        # 终检执法点在 commit——合法走完 approve 的第二页仍拦）
        d = self.make_clean()
        self.write_page("STG-0001", title="同题页")
        self.write_page("STG-0002", title="同题页")
        self.assertEqual(kn("lint", "--knowledge-dir=" + d,
                            "--timestamp=" + TS).returncode, 1)  # dedup 重复组 FAIL
        for pg in ("STG-0001", "STG-0002"):
            self.assertEqual(kn("approve", "--knowledge-dir=" + d, "--page=" + pg,
                                "--approver=评审人", "--timestamp=" + TS2).returncode, 0)
        self.assertEqual(kn("commit", "--knowledge-dir=" + d, "--page=STG-0001",
                            "--timestamp=" + TS2).returncode, 0)
        r = kn("commit", "--knowledge-dir=" + d, "--page=STG-0002", "--timestamp=" + TS2)
        self.assertEqual(r.returncode, 1)
        self.assertIn("dedup", r.stderr)


class TestExportMatch(KnowledgeCase):
    def test_export_deterministic_bytes(self):
        d = self.make_lib()
        self.assertEqual(kn("export", "--knowledge-dir=" + d).returncode, 0)
        g = os.path.join(d, "graph.ndjson")
        with open(g, "rb") as f:
            first = f.read()
        self.assertEqual(kn("export", "--knowledge-dir=" + d).returncode, 0)
        with open(g, "rb") as f:
            self.assertEqual(first, f.read())
        text = first.decode("utf-8")
        self.assertIn('"predicate"', text)
        self.assertIn('"subject":"vendor-portal"', text)

    def test_match_triple_strict_and_window(self):
        d = self.make_lib()
        r = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-01",
               "--asset=shop.example", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PR-0001", r.stdout)
        r2 = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-01",
                "--asset=shop.example", "--today=2027-01-01")
        self.assertEqual(r2.returncode, 0)
        self.assertNotIn("PR-0001	", r2.stdout)
        self.assertIn("[expired]", r2.stdout)

    def test_match_scope_multi_value_substring(self):
        d = self.make_lib()
        r = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-01",
               "--asset=vendor-portal", "--today=2026-09-24")
        self.assertIn("PR-0001", r.stdout)

    def test_match_cross_client_never_matches(self):
        d = self.make_lib()
        r = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-02",
               "--asset=shop.example", "--today=2026-09-24")
        self.assertNotIn("PR-0001", r.stdout)
        self.assertIn("matched=0", r.stdout)

    def test_match_today_required(self):
        d = self.make_lib()
        r = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-01", "--asset=x")
        self.assertEqual(r.returncode, 2)

    def test_match_stale_annotation(self):
        # R11：cve_verified 的 verified_at 距 --today 超 365 天=stale 降权标注
        d = self.make_lib()
        page = """---
id: PR-0002
kind: precedent
class: K2
title: CVE 旧核验先例
client: CLIENT-01
scope_asset: legacy-portal
window: 2026-01-01..2026-12-31
triples:
  - [legacy-portal, exposes, admin-panel]
outcome: 1 处
cve_refs: CVE-2020-0001
cve_verified:
  - {cve: CVE-2020-0001, source: NVD, verified_at: 2024-01-01}
cost_hint: 2
last_verified: 2026-09-01
status: core
source_id: KP-0001
---
## 摘要
"""
        with open(os.path.join(d, "precedents", "PR-0002.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(page)
        r = kn("match", "--knowledge-dir=" + d, "--client=CLIENT-01",
               "--asset=legacy-portal", "--today=2026-09-24")
        self.assertIn("PR-0002", r.stdout)
        self.assertIn("[stale]", r.stdout)

    def test_neighbors_from_graph(self):
        d = self.make_lib()
        self.assertEqual(kn("export", "--knowledge-dir=" + d).returncode, 0)
        r = kn("neighbors", "--knowledge-dir=" + d, "--entity=vendor-portal")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("EN-", r.stdout)

    def test_neighbors_requires_export_first(self):
        d = self.make_lib()
        r = kn("neighbors", "--knowledge-dir=" + d, "--entity=vendor-portal")
        self.assertEqual(r.returncode, 2)
        self.assertIn("export", r.stderr)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""批次5 T13：四门槛晋升 promote（复现≥2/跨目标/人工审批在场/零指纹——机械核验
缺口清单化）+demote（≥2 反证+防护拦截/代码修复分类）+lint 保鲜（--freshness-days
180 陈旧清单，exit 0 附告警；match [stale] 降权联动=R11 既有）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
TS = "2026-09-24T12:00:00Z"

PATTERN_CLEAN = (
    "---\n"
    "id: PT-0001\n"
    "kind: pattern\n"
    "use: ok-sample\n"
    "vuln_class: wstg-authz\n"
    "sample_brief: 越权差分取样模式\n"
    "vocab_version: WSTG-v4.2\n"
    "status: learned\n"
    "last_verified: 2026-09-01\n"
    "---\n"
    "## 样例\n"
    "模式正文（脱敏占位符化）。\n"
)

PATTERN_DIRTY = PATTERN_CLEAN.replace("模式正文（脱敏占位符化）。",
                                     "模式正文：曾在 client-admin.example 实证。")

PRECEDENT_T = (
    "---\n"
    "id: %s\n"
    "kind: precedent\n"
    "class: K2\n"
    "title: 引用先例 %s\n"
    "client: %s\n"
    "scope_asset: asset-%s\n"
    "window: 2026-01-01..2026-12-31\n"
    "triples:\n"
    "  - [surface, exposes, panel]\n"
    "outcome: 2 处\n"
    "applied_patterns: [PT-0001]\n"
    "cost_hint: 2\n"
    "last_verified: 2026-09-01\n"
    "status: core\n"
    "source_id: KP-0001\n"
    "---\n"
    "## 摘要\n"
)


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class PromoteCase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)

    def put_pattern(self, text=PATTERN_CLEAN, name="PT-0001"):
        p = os.path.join(self.d, "patterns", "learned", name + ".md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def put_precedent(self, pid, client):
        p = os.path.join(self.d, "precedents", pid + ".md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(PRECEDENT_T % (pid, pid, client, pid.lower()))

    def put_promote_approval(self, page="PT-0001"):
        """门槛③载体：log.md approve for=promote 行（R9 ③=在场检查；人审流程落库）。"""
        with open(os.path.join(self.d, "log.md"), "a", encoding="utf-8",
                  newline="\n") as f:
            f.write("2026-09-24T11:00:00Z|approve|%s|for=promote approver=评审人\n" % page)

    def promote(self, page="PT-0001", ts=TS):
        args = ["promote", "--knowledge-dir=" + self.d, "--page=" + page]
        if ts:
            args.append("--timestamp=" + ts)
        return kn(*args)


class TestPromote(PromoteCase):
    def test_four_gates_each_blocks(self):
        # 逐一构造缺口：0/1 引用→①缺；2 引用同客户→②缺；无 approve 行→③缺；
        # 页含真域名→④缺
        def case(gate):
            self.setUp.__func__(self)
            if gate == "复现":
                self.put_pattern()
                self.put_precedent("PR-0001", "CLIENT-01")
            elif gate == "跨目标":
                self.put_pattern()
                self.put_precedent("PR-0001", "CLIENT-01")
                self.put_precedent("PR-0002", "CLIENT-01")
            elif gate == "人工审批":
                self.put_pattern()
                self.put_precedent("PR-0001", "CLIENT-01")
                self.put_precedent("PR-0002", "CLIENT-02")
            else:  # 指纹泄漏
                self.put_pattern(PATTERN_DIRTY)
                self.put_precedent("PR-0001", "CLIENT-01")
                self.put_precedent("PR-0002", "CLIENT-02")
                self.put_promote_approval()
            return self.promote()

        for gate in ("复现", "跨目标", "人工审批", "指纹泄漏"):
            r = case(gate)
            self.assertEqual(r.returncode, 1, gate + ": " + r.stdout + r.stderr)
            self.assertIn(gate, r.stdout, gate + " 缺口未指名")
            self.assertIn("REJECT", r.stdout)

    def test_all_gates_pass_moves_to_core(self):
        self.put_pattern()
        self.put_precedent("PR-0001", "CLIENT-01")
        self.put_precedent("PR-0002", "CLIENT-02")
        self.put_promote_approval()
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        core = os.path.join(self.d, "patterns", "core", "PT-0001.md")
        self.assertTrue(os.path.isfile(core), "页未迁 patterns/core")
        self.assertFalse(os.path.isfile(
            os.path.join(self.d, "patterns", "learned", "PT-0001.md")))
        with open(core, encoding="utf-8") as f:
            moved = f.read()
        self.assertIn("status: core", moved, "status 字段未改 core")
        self.assertNotIn("status: learned", moved)
        with open(os.path.join(self.d, "log.md"), encoding="utf-8") as f:
            lg = f.read()
        self.assertIn("|promote|PT-0001|learned->core refs=2 clients=2", lg)

    def test_promote_requires_learned_zone(self):
        # 已在 core 的页不再 promote（目标态幂等拒收）；无页同律
        p = os.path.join(self.d, "patterns", "core", "PT-0001.md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(PATTERN_CLEAN)
        r = self.promote()
        self.assertEqual(r.returncode, 1)

    def test_promote_requires_timestamp(self):
        self.put_pattern()
        r = self.promote(ts="")
        self.assertEqual(r.returncode, 2, "G-23：时间戳必填（禁墙钟）")


class TestDemote(PromoteCase):
    def demote(self, refuting, note):
        return kn("demote", "--knowledge-dir=" + self.d, "--page=PT-0001",
                  "--refuting=" + refuting, "--note=" + note, "--timestamp=" + TS)

    def test_demote_needs_two_refutations_and_class(self):
        self.put_pattern()
        r = self.demote("EV-g1-0001", "误报")
        self.assertEqual(r.returncode, 1, "单反证拒收")
        r = self.demote("EV-g1-0001;EV-g1-0002", "仅备注无分类词")
        self.assertEqual(r.returncode, 1, "note 缺降级分类词拒收")
        r2 = self.demote("EV-g1-0001;EV-g1-0002", "证据归因：防护拦截")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.d, "patterns", "demoted", "PT-0001.md")),
            "页未迁 patterns/demoted")
        dm = os.path.join(self.d, "patterns", "demoted", "PT-0001.md")
        with open(dm, encoding="utf-8") as f:
            moved = f.read()
        self.assertIn("status: demoted", moved)
        with open(os.path.join(self.d, "log.md"), encoding="utf-8") as f:
            lg = f.read()
        self.assertIn("|demote|PT-0001|refuting=EV-g1-0001;EV-g1-0002", lg)

    def test_demote_from_core_zone(self):
        p = os.path.join(self.d, "patterns", "core", "PT-0001.md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(PATTERN_CLEAN)
        r = self.demote("EV-a;EV-b", "代码修复后复测失效")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.isfile(p), "core 区页未移出")


class TestFreshness(PromoteCase):
    def test_freshness_report(self):
        # last_verified 距 --today 超 freshness-days（缺省 180）→ stale 清单（exit 0 告警）
        self.put_pattern()
        old = (PATTERN_CLEAN.replace("id: PT-0001", "id: PT-0002")
               .replace("vuln_class: wstg-authz", "vuln_class: wstg-sess")
               .replace("last_verified: 2026-09-01", "last_verified: 2025-01-01"))
        self.put_pattern(old, name="PT-0002")
        r = kn("lint", "--knowledge-dir=" + self.d, "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, "stale=告警不判 FAIL: " + r.stdout)
        self.assertIn("stale", r.stdout)
        self.assertIn("PT-0002", r.stdout, "指名陈旧页")
        self.assertNotIn("PT-0001\t", r.stdout)
        self.assertIn("PASS n=", r.stdout)

    def test_freshness_days_override(self):
        self.put_pattern()
        r = kn("lint", "--knowledge-dir=" + self.d, "--today=2026-09-24",
               "--freshness-days=7")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("stale", r.stdout, "PT-0001 24 天 > 7 天须命中")
        self.assertIn("PT-0001", r.stdout)

    def test_lint_timestamp_only_still_works(self):
        # 既有调用面（仅 --timestamp）零回归：无 --today 则不跑保鲜
        self.put_pattern()
        r = kn("lint", "--knowledge-dir=" + self.d, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("stale", r.stdout)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""批次5 T6：trigger-audit ②逐对配对（G-27 cred 物理列消费）+④高危即时横向机检
（triggers-v2 承诺兑现——横向 intent 引用 FD-id 或 lateral: 披露 fact）。

Ruling（④基线冲突，契约随行）：G-g1 基线含 FD-g1-0001（impact=高）且无横向闭包——
④机检落地后凡断言全绿的用例先补 target=lateral:FD-g1-0001 披露 fact（test_trigger_audit.py
setUp 同律）；tests/test_trigger_audit.py 三处 PASS 断言随行适配，零夹具/金样改动。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PHASES_CLI = os.path.join(ROOT, "cli", "tanyin-phases")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T12:00:00Z"
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger.phases_engine import trigger_audit  # noqa: E402


def run(cli, gd, sub, *args):
    return subprocess.run([sys.executable, cli, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def add_session_cred(gd, ordinal):
    """铸造 kind=session CRED（G-g1 现有 1 条→序号自 2 起；secret_ref N=行序号）。"""
    r = run(LEDGER, gd, "add-cred", "--kind=session", "--role=operator",
            "--username-ref=op%d" % ordinal, "--secret-ref={{vault:cred-%d}}" % ordinal,
            "--parent-cred=CRED-g1-0001", "--timestamp=" + TS)
    assert r.returncode == 0, r.stdout + r.stderr
    return "CRED-g1-%04d" % ordinal


def add_authz_intent(gd, cred_id, title):
    r = run(LEDGER, gd, "add-intent", "--title=" + title, "--engine=web-blackbox",
            "--kind=authz-diff", "--origin=entity", "--budget-share=1;1;1",
            "--cred=" + cred_id, "--timestamp=" + TS)
    assert r.returncode == 0, r.stdout + r.stderr


def disclose_lateral(gd, fid):
    """④披露通道：target=lateral:<FD-id> fact（facts.target 自由文本，零 schema 变更）。"""
    r = run(LEDGER, gd, "add-fact", "--intent-id=INT-g1-0001", "--kind=info",
            "--target=lateral:" + fid, "--detail=披露：高危 finding 轮内已横向排查（批5 T6）",
            "--confidence=0.9", "--timestamp=" + TS)
    assert r.returncode == 0, r.stdout + r.stderr


class TestTriggerAuditV2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    # ---- ② 逐对配对（G-27 后半）--------------------------------------------

    def test_pairing_per_cred_not_global(self):
        """两个 session CRED 只有其一有逐对 authz-diff：旧全局口径闭、新逐对口径 FAIL 指名缺口。"""
        cred_a = add_session_cred(self.d, 2)
        cred_b = add_session_cred(self.d, 3)
        add_authz_intent(self.d, cred_a, "差分A")
        fails, _ = trigger_audit(self.d)
        self.assertTrue(any("CRED" in f and "逐对" in f for f in fails),
                         "②逐对口径未生效: %r" % fails)
        self.assertTrue(any(cred_b in f for f in fails), "缺口未指名 " + cred_b)
        self.assertFalse(any(cred_a in f for f in fails), "已逐对配对的 %s 不应入缺口" % cred_a)

    def test_pairing_pass_when_each_cred_covered(self):
        """每个 CRED 各有 cred=<cid> 的 authz-diff intent → ② 全闭（④基线先行披露）。"""
        cred_a = add_session_cred(self.d, 2)
        cred_b = add_session_cred(self.d, 3)
        add_authz_intent(self.d, cred_a, "差分A")
        add_authz_intent(self.d, cred_b, "差分B")
        disclose_lateral(self.d, "FD-g1-0001")
        fails, _ = trigger_audit(self.d)
        self.assertEqual(fails, [], "②逐对全覆盖+④披露后应零缺口: %r" % fails)

    def test_pairing_deferred_fact_channel_kept(self):
        """延后 fact 通道不变：cred=<cid> 缺 intent 时 target=authz-diff:<cid> fact 闭②。"""
        cred_a = add_session_cred(self.d, 2)
        disclose_lateral(self.d, "FD-g1-0001")
        r = run(LEDGER, self.d, "add-fact", "--intent-id=INT-g1-0001", "--kind=info",
                "--target=authz-diff:" + cred_a, "--detail=只读会话显式延后差分",
                "--confidence=0.9", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fails, _ = trigger_audit(self.d)
        self.assertFalse(any("cred-obtained" in f for f in fails), "%r" % fails)

    # ---- ④ 高危即时横向（triggers-v2 承诺兑现）-----------------------------

    def test_highrisk_finding_needs_lateral_intent_or_disclosure(self):
        """impact=高 finding 无横向 intent 无披露 fact → ④ FAIL 指名 FD-id；补披露 fact → 过。"""
        r = run(LEDGER, self.d, "add-finding", "--intent-id=INT-g1-0002",
                "--title=高危横向机检样例", "--confidence=C3", "--impact=高",
                "--exploitation-status=suspected", "--scope-check=in_scope",
                "--description-brief=机检用高危样例", "--reproducible-steps=step1",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=EV-g1-0001",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        new_fid = r.stdout.splitlines()[0].split(chr(9))[1]
        fails, _ = trigger_audit(self.d)
        self.assertTrue(any("横向" in f for f in fails), "④机检未生效: %r" % fails)
        self.assertTrue(any("FD-g1-0001" in f for f in fails), "既有高危行未点名")
        self.assertTrue(any(new_fid in f for f in fails), "新高危行未点名")
        disclose_lateral(self.d, "FD-g1-0001")
        disclose_lateral(self.d, new_fid)
        fails, _ = trigger_audit(self.d)
        self.assertFalse(any("横向" in f for f in fails), "%r" % fails)
        self.assertEqual(fails, [], "%r" % fails)

    def test_highrisk_lateral_intent_channel(self):
        """横向 intent 通道：kind=matrix-test 且 detail 内联 FD-id → ④ 闭。"""
        r = run(LEDGER, self.d, "add-intent", "--title=同型横向排查", "--engine=web-blackbox",
                "--kind=matrix-test", "--origin=adjacency", "--budget-share=1;1;1",
                "--detail=来源 FD-g1-0001 同类资产全量补格", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fails, _ = trigger_audit(self.d)
        self.assertEqual(fails, [], "横向 intent 通道未闭④: %r" % fails)

    def test_low_impact_finding_not_audited(self):
        """impact=中 → ④ 不计数不 FAIL（triggers 目录高危行限定 impact∈{高,high,critical}）。"""
        _, st1 = trigger_audit(self.d)
        r = run(LEDGER, self.d, "add-finding", "--intent-id=INT-g1-0002",
                "--title=中危样例不进审计", "--confidence=C3", "--impact=中",
                "--exploitation-status=suspected", "--scope-check=in_scope",
                "--description-brief=不应触发④", "--reproducible-steps=step1",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=EV-g1-0001",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        new_fid = r.stdout.splitlines()[0].split(chr(9))[1]
        fails, st2 = trigger_audit(self.d)
        self.assertEqual(st1["total"], st2["total"], "中危 finding 不应计入 ④ 审计分母")
        haz = [f for f in fails if "横向" in f]
        self.assertEqual(len(haz), 1, "仅 FD-g1-0001 一条高危缺口: %r" % haz)
        self.assertIn("FD-g1-0001", haz[0])
        self.assertTrue(all(new_fid not in f for f in haz), "中危行被误判: %r" % haz)

    # ---- CLI 清单出口 ------------------------------------------------------

    def test_cli_pass_line_after_full_closure(self):
        """披露后 CLI exit 0，PASS 行 triggers/closed 计数含 ④ 分母。"""
        disclose_lateral(self.d, "FD-g1-0001")
        r = run(PHASES_CLI, self.d, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        self.assertIn("closed=", r.stdout)


if __name__ == "__main__":
    unittest.main()

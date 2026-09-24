# -*- coding: utf-8 -*-
"""批次4 T13：触发器闭包审计——三检查（目录版本/闭包/清单）。

Ruling（argv 契约，R-T1-1 同型）：--goal-dir 紧随命令名（单入口 argv[2] 冻结）。
Ruling（add-cred 契约对齐）：计划参数组（--secret-ref={{vault:cred-11}}/无 parent）违反
repo 闭合律——kind=session 须 --parent-cred、secret_ref N=行序号（G-g1 现有 1 cred→
cred-2）、--permitted-actions 须 account-grant 覆盖（G-g1 无→删该参）。
Ruling（matrix-freeze 幂等口径）：G-g1 基线已冻结（make_fixtures 模拟 P2 冻结）——
rc∈{0,1}（already-frozen=幂等容忍，PROTOCOL §1 判定表同律）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PHASES = os.path.join(ROOT, "cli", "tanyin-phases")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
EGRESS = os.path.join(ROOT, "cli", "tanyin-egress")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:30:00Z"


def run(cli, gd, sub, *args):
    return subprocess.run([sys.executable, cli, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestTriggerAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_catalog_file_versioned(self):
        text = open(os.path.join(ROOT, "phases", "TRIGGERS.md"), encoding="utf-8").read()
        self.assertIn("version: triggers-v1", text)
        for ev in ("asset-added", "cred-obtained", "scope-amended"):
            self.assertIn(ev, text)

    def test_baseline_session_passes(self):
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_catalog_version_mismatch_fails(self):
        r = run(LEDGER, self.gd, "append-timeline", "--actor=总控", "--phase=P0",
                "--event=triggers-catalog triggers-v0", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 1)
        self.assertIn("目录版本", r.stdout + r.stderr)

    def test_asset_added_without_submatrix_fails(self):
        r = run(LEDGER, self.gd, "add-asset", "--type=subdomain", "--value=newapi.shop.example",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 1)
        self.assertIn("newapi.shop.example", r.stdout + r.stderr)
        # 闭环二选一：铸子矩阵行（G-2）→过（matrix-freeze 已冻结基线幂等口径见 Ruling）
        r = run(LEDGER, self.gd, "matrix-freeze", "--timestamp=" + TS)
        self.assertIn(r.returncode, (0, 1), "already-frozen 幂等容忍（G-g1 基线已冻结）")
        r = run(LEDGER, self.gd, "matrix-set", "--attack-surface=newapi.shop.example",
                "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: 闭环",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cred_session_without_authz_candidate_fails(self):
        r = run(LEDGER, self.gd, "add-cred", "--kind=session", "--role=operator",
                "--username-ref=op9", "--secret-ref={{vault:cred-2}}",
                "--parent-cred=CRED-g1-0001", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 1)
        self.assertIn("authz-diff", r.stdout + r.stderr)

    def test_cred_session_deferred_fact_closes(self):
        run(LEDGER, self.gd, "add-cred", "--kind=session", "--role=operator",
            "--username-ref=op9", "--secret-ref={{vault:cred-2}}",
            "--parent-cred=CRED-g1-0001", "--timestamp=" + TS)
        r = run(LEDGER, self.gd, "add-fact", "--intent-id=INT-g1-0001", "--kind=info",
                "--target=authz-diff:CRED-g1-0002", "--detail=本凭据为只读会话，显式延后差分",
                "--confidence=0.9", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_egress_compile_writes_event(self):
        r = run(EGRESS, self.gd, "compile")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tl = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("egress-compile", tl)
        r = run(LEDGER, self.gd, "verify-chain")
        self.assertEqual(r.returncode, 0, "事件入链须一致")


if __name__ == "__main__":
    unittest.main()

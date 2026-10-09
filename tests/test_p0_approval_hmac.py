# -*- coding: utf-8 -*-
"""P0 诚实性加固批（会诊②·审计缺口③）：approve 持钥 HMAC 通道。

旧行为：approver 自由字符串，AI 写者可自落 approvals 行冒充客户。
新行为：TANYIN_APPROVAL_KEY 在场 ⇒ approve 须 --sig=HMAC-SHA256(key,
command_hash)（错/缺均 rc=1）；verify-signoff/--knowledge 验行内
sig= 段。键缺席=legacy（靶场/CI/金样不破坏）。"""
import hashlib, hmac, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"
CH = "a" * 64
KEY = "test-approval-key"


def run(gd, *args, key=None):
    env = dict(os.environ)
    if key is not None:
        env["TANYIN_APPROVAL_KEY"] = key
    else:
        env.pop("TANYIN_APPROVAL_KEY", None)
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env)


def sig(ch, key):
    return hmac.new(hashlib.sha256(key.encode()).digest(), ch.encode(), hashlib.sha256).hexdigest()


class TestApprovalHmac(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_legacy_no_key_still_works(self):
        r = run(self.d, "approve", "--command-hash=" + CH, "--decision=approved",
                "--approver=range-operator", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(self.d, "approve", "--verify-signoff")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_key_requires_sig(self):
        r = run(self.d, "approve", "--command-hash=" + CH, "--decision=approved",
                "--approver=range-operator", "--timestamp=" + TS, key=KEY)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--sig", r.stderr + r.stdout)

    def test_key_wrong_sig_rejected(self):
        r = run(self.d, "approve", "--command-hash=" + CH, "--decision=approved",
                "--approver=range-operator", "--timestamp=" + TS,
                "--sig=" + "f" * 64, key=KEY)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_key_correct_sig_then_verify(self):
        s = sig(CH, KEY)
        r = run(self.d, "approve", "--command-hash=" + CH, "--decision=approved",
                "--approver=range-operator", "--timestamp=" + TS, "--sig=" + s,
                key=KEY)
        self.assertEqual(r.returncode, 0, r.stderr)
        ap = open(os.path.join(self.d, "approvals.tsv"), encoding="utf-8").read()
        self.assertIn("sig=" + s, ap)
        r = run(self.d, "approve", "--verify-signoff", key=KEY)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("持钥验签通过", r.stdout)

    def test_key_forged_row_fails_verify(self):
        # 直铸无签 approved 行（模拟 AI 冒充）：持钥 verify-signoff 必拒
        ap = os.path.join(self.d, "approvals.tsv")
        with open(ap, "a", encoding="utf-8") as f:
            f.write("\t".join(["AP-forged", CH, "approved", "fake-client",
                               TS, "", "2"]) + "\n")
        r = run(self.d, "approve", "--verify-signoff", key=KEY)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("sig", r.stdout)


if __name__ == "__main__":
    unittest.main()

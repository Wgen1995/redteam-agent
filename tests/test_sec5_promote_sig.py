# -*- coding: utf-8 -*-
"""SEC-1 舰 S5（2026-10-15 v0.9.6 执法面升权批）：promote 签名门。

依据 plan SEC-1 舰节 + review 02-security-enforcement.md S5：
promote 四门槛只查库内自洽（③=log.md 在场一行字），挡不住合谋投毒——
被俘战士可 mint 先例 → approvers add 自己 → approve for=promote → 入 core
跨战持久化。

新门（复用 S1 的 TANYIN_APPROVAL_KEY HMAC 通道，键仅操作员侧 env——
runner 白名单已剥离战士面）：
- 键在场 ⇒ tanyin-knowledge approve 须 --sig（HMAC-SHA256(key,
  approve|page|approver|ts)），签名进 log.md 行；promote 须 --sig
  （promote|page|ts）且门槛③升为验签（无签名 approve for=promote 行=缺）；
- lint 拒无签名行（键在场时：approve for=promote / promote 事件行无有效
  sig=FAIL）；键缺席=legacy（靶场/CI 零破坏）；
- EV 链复核钩子：promote --goal-dir=账本目录 ⇒ 复核记录铸上哈希链
  （timeline ev-recheck 行，verify-chain 可验）。
"""
import hashlib
import hmac
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
KN = os.path.join(CLI, "tanyin-knowledge")
GUARD_FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TAB = chr(9)
KEY = "sec5-operator-key"
TS = "2026-09-24T12:00:00Z"

sys.path.insert(0, CLI)
from ledger import core  # noqa: E402

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


def sig(message):
    return hmac.new(hashlib.sha256(KEY.encode()).digest(),
                    message.encode(), hashlib.sha256).hexdigest()


def kn(kdir, *args, key=False):
    env = dict(os.environ)
    if key:
        env["TANYIN_APPROVAL_KEY"] = KEY
    else:
        env.pop("TANYIN_APPROVAL_KEY", None)
    return subprocess.run([PY, KN] + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


class PromoteSigCase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.assertEqual(kn(self.d, "init", "--knowledge-dir=" + self.d).returncode, 0)
        with open(os.path.join(self.d, "approvers.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(TAB.join(("approver", "registered_at")) + "\n")
            f.write(TAB.join(["operator", "2026-09-01T00:00:00Z"]) + "\n")
        p = os.path.join(self.d, "patterns", "learned", "PT-0001.md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(PATTERN_CLEAN)
        for pid, client in (("PR-0001", "CLIENT-01"), ("PR-0002", "CLIENT-02")):
            with open(os.path.join(self.d, "precedents", pid + ".md"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(PRECEDENT_T % (pid, pid, client, pid.lower()))
        self.log_path = os.path.join(self.d, "log.md")

    def put_unsigned_promote_approval(self):
        with open(self.log_path, "a", encoding="utf-8", newline="\n") as f:
            f.write("2026-09-24T11:00:00Z|approve|PT-0001|for=promote approver=评审人\n")

    def promote(self, *extra, **kw):
        return kn(self.d, "promote", "--knowledge-dir=" + self.d,
                  "--page=PT-0001", "--timestamp=" + TS, *extra, **kw)


class TestPromoteSignatureGate(PromoteSigCase):
    def test_promote_without_sig_rejected_when_key_present(self):
        self.put_unsigned_promote_approval()
        r = self.promote(key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--sig", r.stdout + r.stderr)

    def test_promote_wrong_sig_rejected(self):
        self.put_unsigned_promote_approval()
        r = self.promote("--sig=" + "f" * 64, key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("验签失败", r.stdout + r.stderr)

    def test_promote_unsigned_approval_line_rejected(self):
        self.put_unsigned_promote_approval()
        r = self.promote("--sig=" + sig("promote|PT-0001|" + TS), key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("③", r.stdout)
        self.assertIn("签名", r.stdout)

    def test_promote_signed_flow_passes(self):
        """全链持钥流：approve --for=promote --sig 铸行 → promote --sig 入 core。"""
        r = kn(self.d, "approve", "--knowledge-dir=" + self.d, "--page=PT-0001",
               "--approver=operator", "--for=promote",
               "--timestamp=2026-09-24T11:00:00Z",
               "--sig=" + sig("approve|PT-0001|operator|2026-09-24T11:00:00Z"),
               key=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.log_path, encoding="utf-8") as f:
            lg = f.read()
        self.assertIn("for=promote", lg)
        self.assertIn("sig=", lg)
        r2 = self.promote("--sig=" + sig("promote|PT-0001|" + TS), key=True)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.d, "patterns", "core", "PT-0001.md")))
        with open(self.log_path, encoding="utf-8") as f:
            self.assertIn("|promote|PT-0001|", f.read())

    def test_legacy_no_key_promote_still_works(self):
        self.put_unsigned_promote_approval()
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestApproveSignature(PromoteSigCase):
    def _stage_page(self):
        """staging 面：页+staging.tsv 行（status=lint-passed）手工铸。"""
        sp = os.path.join(self.d, "staging", "pages", "STG-0001.md")
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w", encoding="utf-8", newline="\n") as f:
            f.write(PATTERN_CLEAN.replace("id: PT-0001", "id: STG-0001"))
        st = os.path.join(self.d, "staging", "staging.tsv")
        cols = ("staging_id", "page_id", "class", "title", "source_id", "status",
                "checksum", "created", "approved_by", "approved_at")
        with open(st, "w", encoding="utf-8", newline="\n") as f:
            f.write(TAB.join(cols) + "\n")
            f.write(TAB.join(["STG-0001", "STG-0001", "pattern", "t", "KP-0001",
                              "lint-passed", "0" * 16, "2026-09-24T00:00:00Z",
                              "", ""]) + "\n")
        with open(os.path.join(self.d, "approvers.tsv"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(TAB.join(("approver", "registered_at")) + "\n")
            f.write(TAB.join(["operator", "2026-09-01T00:00:00Z"]) + "\n")

    def test_approve_requires_sig_when_key_present(self):
        self._stage_page()
        r = kn(self.d, "approve", "--knowledge-dir=" + self.d, "--page=STG-0001",
               "--approver=operator", "--timestamp=" + TS, key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--sig", r.stdout + r.stderr)

    def test_approve_wrong_sig_rejected(self):
        self._stage_page()
        r = kn(self.d, "approve", "--knowledge-dir=" + self.d, "--page=STG-0001",
               "--approver=operator", "--timestamp=" + TS,
               "--sig=" + "f" * 64, key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_approve_correct_sig_writes_signed_line(self):
        """staging 面持钥流：--sig 验签通过且签名落 log 行。"""
        self._stage_page()
        r = kn(self.d, "approve", "--knowledge-dir=" + self.d, "--page=STG-0001",
               "--approver=operator", "--timestamp=" + TS,
               "--sig=" + sig("approve|STG-0001|operator|" + TS), key=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.log_path, encoding="utf-8") as f:
            lg = f.read()
        self.assertIn("|approve|STG-0001|", lg)
        self.assertIn("sig=" + sig("approve|STG-0001|operator|" + TS), lg)

    def test_legacy_approve_without_key_still_works(self):
        self._stage_page()
        r = kn(self.d, "approve", "--knowledge-dir=" + self.d, "--page=STG-0001",
               "--approver=operator", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestLintUnsignedReject(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.assertEqual(kn(self.d, "init", "--knowledge-dir=" + self.d).returncode, 0)

    def _log_line(self, detail):
        with open(os.path.join(self.d, "log.md"), "a", encoding="utf-8",
                  newline="\n") as f:
            f.write("2026-09-24T11:00:00Z|approve|PT-0001|" + detail + "\n")

    def test_unsigned_promote_approval_line_fails_lint_with_key(self):
        self._log_line("for=promote approver=评审人")
        r = kn(self.d, "lint", "--knowledge-dir=" + self.d, "--timestamp=" + TS, key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("PT-0001", r.stdout)

    def test_unsigned_promote_event_line_fails_lint_with_key(self):
        with open(os.path.join(self.d, "log.md"), "a", encoding="utf-8",
                  newline="\n") as f:
            f.write("2026-09-24T11:00:00Z|promote|PT-0001|learned->core refs=2 clients=2\n")
        r = kn(self.d, "lint", "--knowledge-dir=" + self.d, "--timestamp=" + TS, key=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("promote", r.stdout)

    def test_signed_line_passes_lint_with_key(self):
        s = sig("approve|PT-0001|operator|2026-09-24T11:00:00Z")
        self._log_line("approver=operator for=promote sig=" + s)
        r = kn(self.d, "lint", "--knowledge-dir=" + self.d, "--timestamp=" + TS, key=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_lint_without_key_legacy_pass(self):
        self._log_line("for=promote approver=评审人")
        r = kn(self.d, "lint", "--knowledge-dir=" + self.d, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)


class TestEvChainRecheckHook(PromoteSigCase):
    def test_promote_mints_chain_verifiable_record(self):
        self.put_unsigned_promote_approval()
        gd = tempfile.mkdtemp(prefix="sec5-ev-")
        self.addCleanup(shutil.rmtree, gd, ignore_errors=True)
        shutil.copytree(GUARD_FIX, gd, dirs_exist_ok=True)
        r = self.promote("--goal-dir=" + gd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("ev-recheck", tl)
        self.assertIn("PT-0001", tl)
        ok, _line = core.Session(gd).verify_chain()
        self.assertTrue(ok, "ev-recheck 复核记录铸链后链须完整")


if __name__ == "__main__":
    unittest.main()

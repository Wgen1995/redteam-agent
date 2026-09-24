# -*- coding: utf-8 -*-
"""批次4 T8：role×endpoint 覆盖投影+差分样例对语义。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import authz_matrix, core  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

FIXD = os.path.join(HERE, "fixtures", "diff-authz")


class TestAuthzMatrix(unittest.TestCase):
    def setUp(self):
        self.s = core.Session(FIXD)

    def test_projection_shape(self):
        cov = authz_matrix.coverage(self.s)
        self.assertIn("roles", cov)
        self.assertIn("admin", cov["roles"])
        self.assertIn("user", cov["roles"])
        self.assertTrue(cov["endpoints"], "端点非空")
        total = sum(len(e["roles"]) for e in cov["endpoints"].values())
        covd = sum(1 for e in cov["endpoints"].values()
                   for r in e["roles"].values() if r["covered"])
        self.assertEqual(cov["coverage"], "%d/%d" % (covd, total))


class TestDiffPair(unittest.TestCase):
    """差分样例对：正对（BOLA finding+PG 两 EV+authz-diff: 矩阵行）+负对（fact kind=authz）。"""

    def test_positive_pair(self):
        s = core.Session(FIXD)
        T = TABLES
        fds = [r for r in s.rows("findings.tsv")
               if r[T["findings.tsv"].index("auth_context")].startswith("CRED-")]
        self.assertTrue(fds, "正对须有 auth_context≠空的 finding")
        f0 = fds[0]
        pgs = {r[T["E-index.tsv"].index("pair_group")] for r in s.rows("E-index.tsv")
               if r[T["E-index.tsv"].index("linked_finding")] == f0[0]}
        self.assertEqual(len(pgs), 1, "正对 EV 共享单 PG")
        evs = [r for r in s.rows("E-index.tsv")
               if r[T["E-index.tsv"].index("pair_group")] in pgs]
        self.assertEqual(len(evs), 2, "实验组+对照组两 EV")

    def test_negative_fact(self):
        s = core.Session(FIXD)
        T = TABLES
        neg = [r for r in s.rows("facts.tsv") if r[T["facts.tsv"].index("kind")] == "authz"]
        self.assertTrue(neg, "负对须有 fact kind=authz（回归基线）")

    def test_matrix_authz_rows(self):
        s = core.Session(FIXD)
        T = TABLES
        rows = [r for r in s.rows("matrix.tsv") if r[T["matrix.tsv"].index("reason")].startswith("authz-diff:")]
        self.assertTrue(rows, "矩阵 authz-diff: 行在场")

    def test_authz_intent_direct_pending(self):
        """R5（前置裁决）：kind=authz-diff 直达 pending（origin=entity 亦然）——差分样例对语义前置。"""
        s = core.Session(FIXD)
        T = TABLES
        rows = [r for r in s.rows("intents.tsv")
                if r[T["intents.tsv"].index("kind")] == "authz-diff"
                and r[T["intents.tsv"].index("origin")] == "entity"]
        self.assertTrue(rows, "夹具须有 origin=entity 的 authz-diff intent")
        self.assertTrue(all(r[T["intents.tsv"].index("status")] == "pending" for r in rows),
                        "kind=authz-diff 直达 pending（R5）")

    def test_chain_and_validate(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "validate", "--goal-dir", FIXD], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "verify-chain", "--goal-dir", FIXD], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hash_recheck_pass(self):
        """批次4 评审 C-1 补断言：diff-authz 夹具（真实 add-evidence 铸造）上
        hash-recheck 必 PASS——content_hash_norm 写/查单源（ledger/norm.py）。"""
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "hash-recheck", "--goal-dir", FIXD],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("PASS"), r.stdout)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""功能6 TDD①: 身份矩阵装配(cli/bizlogic/identity_matrix.py)——先失败测试。

设计: docs/design/2026-10-20-bizlogic-layer-design.md §1(地基: 至少三把钥匙)。
血律: RT-0016(发现挂 auth_context=CRED-xxx=越权证明链,断链=白打)——纪律沿用不新造。
单源律: 覆盖投影复用 cli/ledger/authz_matrix.coverage,禁第二份投影。
夹具: tests/fixtures/bizlogic-keys(make_bizlogic_fixture.py 铸造)。
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger import core  # noqa: E402
from ledger import authz_matrix  # noqa: E402
from bizlogic import identity_matrix  # noqa: E402

FIXD = os.path.join(HERE, "fixtures", "bizlogic-keys")
G = "bizlogic-keys"
C = "CRED-" + G


class _Stub(object):
    """rows()-duck 会话: 边界形态(单钥匙/零钥匙/双钥匙)只读面。"""

    def __init__(self, tables):
        self.data = tables

    def rows(self, tname):
        return self.data.get(tname, [])


def _cred(n, kind, role, user, status="active", parent=""):
    return [C + "-%04d" % n, kind, role, user, "{{vault:cred-%d}}" % n,
            "", "", parent, "", "", status, "read", "", "2",
            "2026-10-20T1%d:00:00Z" % n, ""]


class TestCollectIdentities(unittest.TestCase):
    def setUp(self):
        self.s = core.Session(FIXD)

    def test_live_chains_collected_expired_revoked_excluded(self):
        ids = identity_matrix.collect_identities(self.s)
        labels = [i["label"] for i in ids]
        self.assertEqual(labels[0], "anonymous", "未登录=零钥匙恒居首")
        self.assertEqual(sorted(labels[1:]), ["alice", "bob", "carol"],
                         "dave(expired)整链排除;carol 的 revoked 会话排除")

    def test_session_tail_represents_live_chain(self):
        ids = {i["label"]: i for i in identity_matrix.collect_identities(self.s)}
        alice = ids["alice"]
        self.assertEqual(alice["cred_id"], C + "-0004", "活链身份取链尾会话")
        self.assertEqual(alice["chain"], [C + "-0001", C + "-0004"], "static→session 链显形")
        self.assertEqual(alice["kind"], "session")

    def test_broken_parent_falls_back_static_with_note(self):
        ids = {i["label"]: i for i in identity_matrix.collect_identities(self.s)}
        bob = ids["bob"]
        self.assertEqual(bob["cred_id"], C + "-0002",
                         "session 父链 expired=断链不取,静态兜底")
        self.assertTrue(bob.get("chain_broken"), "断链如实注记(不静默)")

    def test_auth_context_is_cred_id_verbatim(self):
        ids = identity_matrix.collect_identities(self.s)
        for i in ids[1:]:
            self.assertTrue(i["auth_context"].startswith("CRED-"),
                            "挂链纪律: auth_context=CRED-{id} 原样(RT-0016)")
        self.assertEqual(ids[0]["auth_context"], "", "未登录=空(契约 01 口径)")

    def test_secret_placeholder_only(self):
        blob = json.dumps(identity_matrix.collect_identities(self.s),
                          ensure_ascii=False)
        self.assertIn("{{vault:cred-", blob, "占位符=唯一凭据形态(契约 03)")


class TestProject(unittest.TestCase):
    def setUp(self):
        self.s = core.Session(FIXD)
        self.p = identity_matrix.project(self.s)

    def test_projection_shape(self):
        self.assertIn("keys", self.p)
        self.assertIn("mode", self.p)
        self.assertIn("missing", self.p)
        self.assertIn("coverage", self.p)
        self.assertEqual(len(self.p["keys"]), 4, "未登录+三把钥匙")

    def test_coverage_single_source_reuse(self):
        cov = authz_matrix.coverage(self.s)
        self.assertEqual(self.p["coverage"], cov["coverage"],
                         "覆盖串=authz_matrix.coverage 单源,禁第二份投影")

    def test_opens_projection_per_key(self):
        keys = {k["label"]: k for k in self.p["keys"]}
        self.assertTrue(keys["alice"]["opens"]["shop.example/orders"]["covered"],
                        "alice 会话 finding 在案→orders 面该角色已开")
        self.assertTrue(keys["carol"]["opens"]["shop.example/admin/users"]["covered"],
                        "负结果 fact=回归基线→该端点全角色视为已开")
        self.assertFalse(keys["carol"]["opens"]["shop.example/orders"]["covered"],
                        "admin 角色在 orders 面无 finding/fact=还缺哪把没开,如实空格")

    def test_mode_triple_on_fixture(self):
        self.assertEqual(self.p["mode"], "triple-keys",
                         "甲/乙/丙三钥匙齐=满配形态")
        self.assertEqual(self.p["missing"], [])

    def test_mode_vertical_only_single_key(self):
        stub = _Stub({"creds.tsv": [_cred(1, "static-cred", "user", "alice")]})
        p = identity_matrix.project(stub)
        self.assertEqual(p["mode"], "vertical-only", "单账号→降级只测垂直面(设计§失败)")
        self.assertTrue(any("peer" in m for m in p["missing"]))

    def test_mode_dual_without_peer(self):
        stub = _Stub({"creds.tsv": [_cred(1, "static-cred", "user", "alice"),
                                    _cred(2, "static-cred", "admin", "carol")]})
        p = identity_matrix.project(stub)
        self.assertEqual(p["mode"], "dual-keys", "可降双钥匙(设计§1)")
        self.assertTrue(any("peer" in m for m in p["missing"]))

    def test_mode_anonymous_only(self):
        p = identity_matrix.project(_Stub({}))
        self.assertEqual(p["mode"], "anonymous-only")
        self.assertEqual(len(p["keys"]), 1)


class TestAuthContextAudit(unittest.TestCase):
    def test_broken_chain_finding_flagged(self):
        s = core.Session(FIXD)
        flags = identity_matrix.audit_auth_context(s)
        self.assertEqual(len(flags), 1, "FD-0002 链断反例恰被点名")
        self.assertEqual(flags[0]["finding"], "FD-" + G + "-0002")
        self.assertEqual(flags[0]["expected_cred"], C + "-0003")
        self.assertEqual(flags[0]["got"], "")

    def test_honest_findings_pass(self):
        stub = _Stub({"intents.tsv": [], "findings.tsv": []})
        self.assertEqual(identity_matrix.audit_auth_context(stub), [])


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""ledger/enforce 单元测试（批次 2 审计修复钉死）——
deny-list 数据化（shared/DENYLIST.md 源+内嵌兜底同份）、load_scope 三集语义、
scope_verdict 判定顺序、amendment 链、主机提取强化形态。
"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import core, enforce  # noqa: E402

TAB = chr(9)
SHARED = os.path.join(HERE, "..", "shared", "DENYLIST.md")


def _row(n, kind, matcher):
    return ["S-t-%04d" % n, kind, matcher, "", "", "", "", "2", "2026-01-01T00:00:00Z"]


def _scope(case, rows):
    """临时 goal 目录写 scope.tsv（9 列，无表头——与夹具同形态）。"""
    td = tempfile.TemporaryDirectory()
    case.addCleanup(td.cleanup)
    p = os.path.join(td.name, "scope.tsv")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(TAB.join(r) + chr(10))
    return td, enforce.load_scope(core.Session(td.name))


class DenyListData(unittest.TestCase):
    def test_file_is_live_source(self):
        with open(SHARED, encoding="utf-8") as f:
            self.assertEqual(enforce.DENY_LIST, enforce.parse_denylist(f.read()))

    def test_file_and_embedded_in_sync(self):
        with open(SHARED, encoding="utf-8") as f:
            self.assertEqual(enforce.parse_denylist(f.read()), enforce.DENY_EMBEDDED)

    def test_fallback_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            got = enforce.load_denylist(root=td)
        self.assertEqual(got, enforce.DENY_EMBEDDED)
        self.assertGreater(len(got), 7)
        for p in ("rm -rf ./", "rm -fr ./", "drop database", "truncate table", ":(){:|:&};:"):
            self.assertIn(p, got)

    def test_variants_hit(self):
        for cmd in ("rm -fr ./x", "rm -rf ./tmp", "drop database prod;", "truncate table users",
                    ":(){:|:&};:", ":(){ :|:& };:", "dd if=/dev/zero of=/dev/sda",
                    "chmod -R 777 /", "init 0", "> /dev/sda"):
            self.assertIsNotNone(enforce.deny_hit(cmd), cmd)

    def test_benign_not_hit(self):
        for cmd in ("echo hello world", "ls -la", "cat report.txt", "--file=report.txt"):
            self.assertIsNone(enforce.deny_hit(cmd), cmd)


class LoadScopeSemantics(unittest.TestCase):
    def test_three_sets_shape(self):
        td, sc = _scope(self, [_row(1, "include", "*.shop.example"),
                                 _row(2, "exclude", "banned.shop.example"),
                                 _row(3, "oob", "cb.example"),
                                 _row(4, "account-grant", "AST-1")])
        self.assertEqual(set(sc), {"include", "exclude", "oob"})
        self.assertEqual(sc["include"], ["*.shop.example"])
        self.assertEqual(sc["exclude"], ["banned.shop.example"])
        self.assertEqual(sc["oob"], ["cb.example"])

    def test_verdict_exclude_priority_over_include(self):
        td, sc = _scope(self, [_row(1, "include", "*.shop.example"),
                                 _row(2, "exclude", "*.prod.shop.example")])
        self.assertEqual(enforce.scope_verdict("banned.shop.example", sc), "in")
        self.assertEqual(enforce.scope_verdict("v2.prod.shop.example", sc), "exclude")
        self.assertEqual(enforce.scope_verdict("other.example", sc), "out")

    def test_verdict_oob_record_not_tested(self):
        td, sc = _scope(self, [_row(1, "include", "*.shop.example"),
                                 _row(2, "oob", "cb.example")])
        self.assertEqual(enforce.scope_verdict("cb.example", sc), "oob")

    def test_amendment_latest_wins(self):
        td, sc = _scope(self, [_row(1, "include", "*.shop.example"),
                                 _row(2, "exclude", "*.shop.example")])
        self.assertEqual(sc["include"], [])
        self.assertEqual(sc["exclude"], ["*.shop.example"])

    def test_out_of_scope_hosts_tuples(self):
        td, sc = _scope(self, [_row(1, "include", "*.shop.example"),
                               _row(2, "exclude", "banned.shop.example"),
                               _row(3, "oob", "cb.example")])
        got = enforce.out_of_scope_hosts(["--target=banned.shop.example",
                                          "api.shop.example",
                                          "cb.example",
                                          "evil.example"], sc)
        self.assertEqual(got, [("banned.shop.example", "exclude"),
                               ("cb.example", "oob"),
                               ("evil.example", "out")])


class ExtractHostsForms(unittest.TestCase):
    def test_host_forms_extracted(self):
        cases = {
            "--target=evil.com": ["evil.com"],
            "--endpoint=https://evil.com/path": ["evil.com"],
            "proxy=evil.com:8080": ["evil.com"],
            "localhost": ["localhost"],
            "127.0.0.1": ["127.0.0.1"],
            "::1": ["::1"],
            "2001:db8::1": ["2001:db8::1"],
            "http://[2001:db8::1]:443/": ["2001:db8::1"],
            "--host=2001:db8::1": ["2001:db8::1"],
            "https://user@api.shop.example/x": ["api.shop.example"],
        }
        for tok, want in cases.items():
            self.assertEqual(enforce.extract_hosts([tok]), want, tok)

    def test_junk_not_hosts(self):
        bs = chr(92)
        for tok in ("sys.stdout.write('x')", "pass", "-c", "1.2.3", "3.14", "--ver=2.0",
                    "C:" + bs + "Users" + bs + "x", "2026-09-23T08:00:00Z"):
            self.assertEqual(enforce.extract_hosts([tok]), [], tok)

    def test_ipv6_vs_v4_cidr_no_crash(self):
        self.assertFalse(enforce.host_in_scope("::1", ["10.10.0.0/16"]))


if __name__ == "__main__":
    unittest.main()

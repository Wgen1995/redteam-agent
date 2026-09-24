# -*- coding: utf-8 -*-
"""批次4 T4：EV 卡片解析+matcher 子集评估（R1）+vault 单源。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cards, matchers  # noqa: E402

CARD = """---
id: EV-g1-0041
title: 管理接口未授权访问-实验组
source_type: command
observed_at: 2026-09-21T10:22:05+08:00
network_position: intranet
preconditions:
  - "持有有效会话 {{vault:cred-3}}"
raw_request: |
  GET /admin/api/users HTTP/1.1
  Host: app.intranet
  Cookie: {{vault:cred-3}}
expected:
  matchers:
    - {type: word, words: ["errorCode:00000"]}
    - {type: status, status: [200]}
  extractors:
    - {type: regex, name: user_count, regex: ['"total":(\\d+)']}
cleanup: ''
pair_group: PG-g1-0007
role: admin
---
## 原始响应摘录（脱敏+定长）与判定依据
200 OK errorCode:00000 "total":42
"""


class TestCards(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.p = os.path.join(tempfile.mkdtemp(), "EV-g1-0041.md")
        open(self.p, "w", encoding="utf-8", newline="\n").write(CARD)

    def test_parse_full_card(self):
        c = cards.parse_ev_card(self.p)
        self.assertEqual(c["id"], "EV-g1-0041")
        self.assertEqual(c["network_position"], "intranet")
        self.assertEqual(c["pair_group"], "PG-g1-0007")
        self.assertEqual(c["role"], "admin")
        self.assertIn("{{vault:cred-3}}", c["raw_request"])
        self.assertEqual(len(c["expected"]["matchers"]), 2)
        self.assertEqual(c["preconditions"], ["持有有效会话 {{vault:cred-3}}"])

    def test_consistency_check(self):
        c = cards.parse_ev_card(self.p)
        row = ["EV-g1-0041", "别的标题", "command", "ts", "internet", "curl -s x", "single",
               "a"*64, "b"*64, "art/1", "evidence/EV-g1-0041.md", "", "PG-g1-0007", "excerpt", "2", "ts"]
        errs = cards.check_consistency(c, row)
        self.assertEqual(len(errs), 2, "network_position+title 两处不同值: %r" % errs)


class TestMatchers(unittest.TestCase):
    EXP = {"matchers": [{"type": "word", "words": ["errorCode:00000"]},
                        {"type": "status", "status": [200]}],
           "extractors": [{"type": "regex", "name": "user_count", "regex": ['"total":(\\d+)']}]}

    def test_all_match_and_extract(self):
        r = matchers.evaluate(self.EXP, 200, {}, 'errorCode:00000 "total":42')
        self.assertTrue(r["matched"])
        self.assertEqual(r["extracted"]["user_count"], "42")

    def test_word_miss(self):
        r = matchers.evaluate(self.EXP, 200, {}, 'errorCode:1 "total":42')
        self.assertFalse(r["matched"])

    def test_status_miss(self):
        r = matchers.evaluate(self.EXP, 403, {}, 'errorCode:00000')
        self.assertFalse(r["matched"])

    def test_word_condition_or(self):
        exp = {"matchers": [{"type": "word", "words": ["a", "b"], "condition": "or"}]}
        self.assertTrue(matchers.evaluate(exp, 200, {}, "只有 b")["matched"])

    def test_unknown_type_rejected(self):
        with self.assertRaises(matchers.MatcherError):
            matchers.evaluate({"matchers": [{"type": "dsl", "dsl": "x"}]}, 200, {}, "")

    def test_empty_expected_is_manual(self):
        r = matchers.evaluate({}, 200, {}, "body")
        self.assertIsNone(r["matched"])


class TestVault(unittest.TestCase):
    def test_secret_roundtrip_single_source(self):
        # T4 Ruling：计划测试文件 8 例 vs commit 模板「9 例」——补 vault 单源直测例
        # （load_key/secret/secrets 冻结接口，T5 重放占位符回注消费；guard 侧由
        # 既有 test_guard CLI 面背书行为零变更）。
        import shutil, tempfile
        from ledger import vault
        gd = tempfile.mkdtemp()
        try:
            os.makedirs(vault.vault_dir(gd))
            with open(os.path.join(vault.vault_dir(gd), ".key"), "w", encoding="utf-8", newline="\n") as f:
                f.write("k9\n")
            payload = vault.enc_payload("k9", "admin" + chr(10) + "s3cr3t-value")
            with open(os.path.join(vault.vault_dir(gd), "cred-3.enc"), "w", encoding="utf-8", newline="\n") as f:
                f.write(payload)
            with open(os.path.join(vault.vault_dir(gd), "manifest.tsv"), "w", encoding="utf-8", newline="\n") as f:
                f.write("3\tcred-3.enc\t" + "h" * 16 + "\txor-sha256\t2\n")
            self.assertEqual(vault.load_key(gd), "k9")
            self.assertEqual(vault.read_cred(gd, "3"), ["admin", "s3cr3t-value"])  # 原实现返回 split 结果（list），行为零变更
            self.assertEqual(vault.secret(gd, "3"), "s3cr3t-value")
            self.assertEqual(vault.secrets(gd), [("3", "s3cr3t-value")])
            self.assertIsNone(vault.load_key(os.path.join(gd, "no-such")))
        finally:
            shutil.rmtree(gd)


if __name__ == "__main__":
    unittest.main()

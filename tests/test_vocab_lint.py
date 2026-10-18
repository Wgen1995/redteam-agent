# -*- coding: utf-8 -*-
"""vocab_lint 测试——词表过滤(62律机检面)。"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from vocab_lint import visible_text, lint_file

class TestVocabLint(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/tmp/_vocab_test.html")

    def _w(self, s):
        self.tmp.write_text(s, encoding="utf-8")
        return lint_file(self.tmp)

    def test_visible_text_strips_script_style(self):
        h = "<html><body>漏洞列表<script>const findings=[1]</script><style>.finding{}</style></body></html>"
        self.assertNotIn("finding", visible_text(h).lower())
        self.assertIn("漏洞", visible_text(h))

    def test_banned_word_in_text_hits(self):
        hits = self._w("<p>共 3 条 findings 待复验</p>")
        self.assertTrue(any(b == "findings" for b, _, _ in hits))

    def test_clean_chinese_no_hits(self):
        self.assertEqual(self._w("<p>共 3 条漏洞待复验</p>"), [])

    def test_identifier_in_script_not_flagged(self):
        hits = self._w("<div>漏洞</div><script>render(findings)</script>")
        self.assertEqual(hits, [])

    def test_placeholder_scanned(self):
        hits = self._w('<input placeholder="搜索 intent">')
        self.assertTrue(any(b == "intent" for b, _, _ in hits))

if __name__ == "__main__":
    unittest.main()

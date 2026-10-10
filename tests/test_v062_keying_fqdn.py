# -*- coding: utf-8 -*-
"""v0.6.2 keying v8：*.range.local 域族剥壳（b30/b36 双疑云零分根因回归钉）。"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval_range_recall as E  # noqa: E402


class TestRangeLocalStrip(unittest.TestCase):
    def test_fqdn_equals_short(self):
        self.assertEqual(E._canon_host("svc-shop.range.local", {}), "svc-shop")
        self.assertEqual(E._canon_host("svc-shop", {}), "svc-shop")

    def test_endpoint_canon_pair(self):
        a = E._canon_endpoint("svc-shop.range.local/item?id=1", {})
        b = E._canon_endpoint("svc-shop/item?id=1", {})
        self.assertEqual(a, b)

    def test_port_preserved(self):
        self.assertEqual(E._canon_host("svc-shop.range.local:8001", {}), "svc-shop:8001")

    def test_unrelated_domain_untouched(self):
        self.assertEqual(E._canon_host("evil.example.com", {}), "evil.example.com")


if __name__ == "__main__":
    unittest.main()

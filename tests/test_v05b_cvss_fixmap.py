# -*- coding: utf-8 -*-
"""v0.5b G2：CVSS v3.1 base 纯函数 + FIX_MAP 扩全（渗透专家项——报告最后一公里）。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cvss  # noqa: E402
from ledger import report_render  # noqa: E402


class TestCvssBase(unittest.TestCase):
    def test_canonical_vectors(self):
        # CVSS v3.1 官方样例：全高危 9.8 / 网络低 Priv 8.8 / 本地中 5.5 档
        self.assertAlmostEqual(cvss.base("N", "L", "N", "N", "U", "H", "H", "H"), 9.8)
        self.assertAlmostEqual(cvss.base("N", "L", "L", "N", "U", "H", "H", "H"), 8.8)

    def test_severity_bands(self):
        self.assertEqual(cvss.severity(9.8), "critical")
        self.assertEqual(cvss.severity(8.8), "high")
        self.assertEqual(cvss.severity(5.5), "medium")
        self.assertEqual(cvss.severity(2.0), "low")
        self.assertEqual(cvss.severity(0.0), "none")

    def test_invalid_metric_raises(self):
        with self.assertRaises(ValueError):
            cvss.base("X", "L", "N", "N", "U", "H", "H", "H")

    def test_fix_map_extended(self):
        for k in ("inj.sql", "inj.xss", "inj.ssrf", "inj.deser", "rce.cmd",
                  "idor", "lfi.path", "redirect.open", "authz.diff", "authn.missing"):
            self.assertIn(k, report_render._FIX_MAP, "FIX_MAP 缺锚: " + k)
            self.assertIn("根治", report_render._FIX_MAP[k])


if __name__ == "__main__":
    unittest.main()

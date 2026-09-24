# -*- coding: utf-8 -*-
"""批次4 T10：tools.lock 加载+ECDSA 验签（openssl 子进程；缺 openssl=ENV skip）。"""
import os, shutil, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
import sys
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain  # noqa: E402

LOCK = os.path.join(ROOT, "tools.lock")
PUB = os.path.join(ROOT, "engines", "nuclei", "release.pub")
HAVE_OPENSSL = shutil.which("openssl") is not None


class TestSupplyChain(unittest.TestCase):
    def test_load_lock_entries(self):
        entries = supply_chain.load_lock(LOCK)
        for k in ("openssl", "nuclei", "nuclei-templates"):
            self.assertIn(k, entries)
        self.assertEqual(len(entries["nuclei-templates"]["commit"]), 40, "模板钉 commit 40hex")

    @unittest.skipUnless(HAVE_OPENSSL, "openssl 缺失=ENV（Windows CI 默认无；canary not-deployed 同型）")
    def test_verify_entries_and_tamper(self):
        entries = supply_chain.load_lock(LOCK)
        for k, e in entries.items():
            ok, reason = supply_chain.verify_entry(e, PUB)
            self.assertTrue(ok, "%s 验签失败: %s" % (k, reason))
        bad = dict(entries["nuclei"])
        bad["sha256"] = "0" * 64
        ok, _ = supply_chain.verify_entry(bad, PUB)
        self.assertFalse(ok, "篡改 sha256 须验签失败")

    def test_missing_openssl_reported_not_crash(self):
        """openssl 缺失=ENV 语义（非崩溃）——monkeypatch 掉 which 全平台可跑。"""
        orig = supply_chain.which
        try:
            supply_chain.which = lambda n: None
            ok, reason = supply_chain.verify_entry(
                {"key": "x", "version": "1", "sha256": "0" * 64, "sig": "00", "commit": ""}, PUB)
        finally:
            supply_chain.which = orig
        self.assertFalse(ok)
        self.assertIn("openssl-missing", reason)


if __name__ == "__main__":
    unittest.main()

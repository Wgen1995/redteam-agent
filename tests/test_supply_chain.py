# -*- coding: utf-8 -*-
"""批次4 T10：tools.lock 加载+ECDSA 验签（openssl 子进程；缺 openssl=ENV skip）。"""
import json, os, shutil, subprocess, sys, tempfile, unittest

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

    def test_verify_entry_nonhex_sig_fail_closed(self):
        """批次4 评审收尾（fail-closed 形式统一）：签名非 hex 不得 raise 崩溃——
        返回失败对（False, 缘由），适配器落 blocked 提交 exit 0（「不过=blocked」契约语义）。"""
        orig = supply_chain.which
        try:
            supply_chain.which = lambda n: "/nonexistent/openssl"  # 隔离 ENV：聚焦 fromhex 分支
            ok, reason = supply_chain.verify_entry(
                {"key": "x", "version": "1", "sha256": "0" * 64, "sig": "zz", "commit": ""}, PUB)
        finally:
            supply_chain.which = orig
        self.assertFalse(ok)
        self.assertIn("非 hex", reason)

    def test_load_lock_non_five_fields_adapter_blocked(self):
        """批次4 评审收尾（fail-closed 形式统一）：tools.lock 非五字段行不得让适配器
        崩溃（ValueError 裸抛=exit 1）——捕获后适配器落 blocked 提交 exit 0。"""
        adapter = os.path.join(ROOT, "engines", "nuclei", "adapter.py")
        jsonl = os.path.join(ROOT, "tests", "fixtures", "engine", "nuclei-jsonl", "sample.jsonl")
        with tempfile.TemporaryDirectory() as td:
            tmp_lock = os.path.join(td, "tools.lock")
            with open(tmp_lock, "w", encoding="utf-8", newline="\n") as f:
                f.write("format_version\t1\nopenssl\t3.4\t" + "0" * 64 + "\n")  # 三字段=非五字段行
            out = os.path.join(td, "out")
            r = subprocess.run([sys.executable, adapter, "--intent-id=INT-x-0001",
                                "--out-dir", out, "--lock", tmp_lock, "--jsonl-file", jsonl],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 0, "非五字段行=blocked 提交 exit 0（不崩溃）：\n"
                             + r.stdout + r.stderr)
            sub = json.load(open(os.path.join(out, "submission.json"), encoding="utf-8"))
            self.assertEqual(sub["status"], "blocked")
            log = open(os.path.join(out, "operations.log"), encoding="utf-8").read()
            self.assertIn("解析失败", log, "log 落 blocked 缘由")

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

# -*- coding: utf-8 -*-
"""批次 7 T7：tools.lock 信任链（C4）。红=专家反例复现：①仓内测试钥与生产锚
release.pub 同信任面——重签篡改行 check_lock=0；②runtime 不比对 nuclei 二进制
digest（在场不符仍 ok=True）。绿=测试钥轮换（与生产锚密码学无关）+信任面隔离
断言（测试钥签名×生产锚=FAIL、×测试锚=PASS）+adapter runtime sha256 比对
（在场即必比，不符=blocked；R-T7-1 锚注入位 pub，缺省=生产锚）。"""
import hashlib, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain

PROD_PUB = os.path.join(ROOT, "engines", "nuclei", "release.pub")
TEST_KEY = os.path.join(ROOT, "tests", "fixtures", "keys", "test-signing-key.pem")
TEST_PUB = os.path.join(ROOT, "tests", "fixtures", "keys", "test-release.pub")
ADAPTER = os.path.join(ROOT, "engines", "nuclei", "adapter.py")


def _entry():
    return {"key": "nuclei", "version": "t0", "sha256": "ab" * 32, "sig": "", "commit": "c0"}


def _pub_der_sha(path, pubin):
    """公钥 DER 指纹（PEM 文本差异——如注释头/编码形——不影响同钥判定）。"""
    cmd = ["openssl", "pkey", "-in", path] + (["-pubin"] if pubin else []) +           ["-pubout", "-outform", "DER"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise AssertionError("openssl 读钥失败 %s: %s" % (path, r.stderr.decode("utf-8", "replace")))
    return hashlib.sha256(r.stdout).hexdigest()


class TestTrustFace(unittest.TestCase):
    def test_fixture_key_pub_differs_from_prod_anchor(self):
        a = _pub_der_sha(TEST_KEY, pubin=False)
        b = _pub_der_sha(PROD_PUB, pubin=True)
        self.assertNotEqual(a, b, "信任面隔离：仓内测试钥公钥≠生产信任锚（专家红：同钥）")

    def test_testkey_sig_rejected_by_prod_anchor(self):
        e = _entry()
        e["sig"] = supply_chain.sign_entry(e, TEST_KEY)
        ok, why = supply_chain.verify_entry(e, PROD_PUB)
        self.assertFalse(ok, "测试钥签名×生产锚必须失败（红现状：同钥重签过验签）: " + why)

    def test_testkey_sig_accepted_by_test_anchor(self):
        e = _entry()
        e["sig"] = supply_chain.sign_entry(e, TEST_KEY)
        ok, why = supply_chain.verify_entry(e, TEST_PUB)
        self.assertTrue(ok, why)


class TestRuntimeDigest(unittest.TestCase):
    def _load_adapter(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("nuc_adapter", ADAPTER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _lock_file(self, td, sha):
        """双键 lock（nuclei/nuclei-templates）以新测试钥签——verify 双键验签门可过，
        让断言聚焦 runtime digest 逻辑本身（R-T7-1：锚注入位 pub=TEST_PUB）。"""
        rows = []
        for key, s in (("nuclei", sha), ("nuclei-templates", "cd" * 32)):
            e = _entry()
            e["key"], e["sha256"] = key, s
            e["sig"] = supply_chain.sign_entry(e, TEST_KEY)
            rows.append("\t".join([e["key"], e["version"], e["sha256"], e["sig"], e["commit"]]))
        lockp = os.path.join(td.name, "tools.lock")
        with open(lockp, "w", encoding="utf-8", newline="\n") as f:
            f.write("key\tversion\tsha256\tsig\tcommit\n" + "\n".join(rows) + "\n")
        return lockp

    def test_tampered_binary_blocked(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        binp = os.path.join(td.name, "nuclei")
        with open(binp, "wb") as f:
            f.write(b"FAKE-BYTES")   # 在场但不符
        lockp = self._lock_file(td, hashlib.sha256(b"PRISTINE-BYTES").hexdigest())
        ok, why = self._load_adapter().verify(lockp, nuclei_path=binp, pub=TEST_PUB)
        self.assertFalse(ok, "runtime 二进制 sha256 与 lock 不符必须 blocked（红现状：不比对）")
        self.assertIn("sha256", why)

    def test_pristine_binary_passes_digest(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        binp = os.path.join(td.name, "nuclei")
        with open(binp, "wb") as f:
            f.write(b"PRISTINE-BYTES")
        lockp = self._lock_file(td, hashlib.sha256(b"PRISTINE-BYTES").hexdigest())
        ok, why = self._load_adapter().verify(lockp, nuclei_path=binp, pub=TEST_PUB)
        self.assertTrue(ok, why)


if __name__ == "__main__":
    unittest.main()

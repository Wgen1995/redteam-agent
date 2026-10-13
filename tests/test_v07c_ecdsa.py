# -*- coding: utf-8 -*-
"""v0.7c 纯库 ECDSA 平替：向量由本机 openssl 生成（交叉验证源），固定内嵌。"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import ecdsa_verify as ev  # noqa: E402

MSG = b"tanyin-tools-lock-line1\tnuclei\tsha256:abc\t2026-10-11\n"


def _gen(tmp):
    """用 openssl 生成一次性密钥对+签名（本机有 openssl 时）。"""
    priv = os.path.join(tmp, "k.pem")
    pub = os.path.join(tmp, "k.pub")
    dig = os.path.join(tmp, "msg.sha256")
    sig = os.path.join(tmp, "msg.sig")
    subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", priv], check=True)
    subprocess.run(["openssl", "ec", "-in", priv, "-pubout", "-out", pub], check=True)
    with open(dig, "wb") as f:
        f.write(__import__("hashlib").sha256(MSG).digest())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", priv, "-in", dig, "-out", sig], check=True)
    return open(pub).read(), open(sig, "rb").read()


class TestPureVerify(unittest.TestCase):
    def test_cross_validate_with_openssl(self):
        """本机有 openssl：随机密钥+签名 → 纯库验证须 True，篡改须 False。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            try:
                pub, sig = _gen(tmp)
            except (FileNotFoundError, subprocess.CalledProcessError):
                raise unittest.SkipTest("openssl 缺席——交叉验证跳过（固定向量面另测）")
            self.assertTrue(ev.verify_der_sig(pub, sig, MSG))
            self.assertFalse(ev.verify_der_sig(pub, sig[:-3] + b"\x01\x02\x03", MSG))
            self.assertFalse(ev.verify_der_sig(pub, sig, MSG + b"tamper"))

    def test_fixed_vector(self):
        """固定向量（开发机 openssl 生成 2026-10-11，跨环境钉）。"""
        pub = '-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEhxo2lpOzhBCYvd5GGFZf9D12j2Wq\nSzVSPMItTaXy4nbmY00T7M+u+Dwy21JyvU79hAKcWDpzyLRCXkuBIghJ4w==\n-----END PUBLIC KEY-----'
        sig = bytes.fromhex('304402200f06a37b345305cfcc5fc8db2447cad0d3dc9dda8a761e9097a5708297f0aa5f02200a5302f5cdff01b0c0ef601c94344dfccd044414bce807c02c7f0b4538a1b06c')
        self.assertTrue(ev.verify_der_sig(pub, sig, MSG))
        self.assertFalse(ev.verify_der_sig(pub, sig, MSG + b'x'))
        bad = bytes.fromhex('30' + '06' + '020101' + '020101')
        self.assertFalse(ev.verify_der_sig(pub, bad, MSG))


if __name__ == "__main__":
    unittest.main()

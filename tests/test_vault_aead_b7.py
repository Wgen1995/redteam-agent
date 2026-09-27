# -*- coding: utf-8 -*-
"""批次 7 T10：vault 加密升级（High：XOR 无 nonce+密钥同盘+密码走 argv）。
红=专家实证：同 key 下 m1^m2==c1^c2（可滚动伪造密文）；篡改无认证；argv 密值。"""
import base64, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import vault

def b64d(s):
    return base64.b64decode(s)


class TestAead(unittest.TestCase):
    K = "unit-test-key"

    def test_roundtrip(self):
        for pt in ("user\nsecret-123", "中文\n值", ""):
            self.assertEqual(vault.dec_payload(self.K, vault.enc_payload(self.K, pt)), pt)

    def test_xor_malleability_broken(self):
        """红：专家 c1^c2==m1^m2 关系——v2 每载荷独立 nonce，关系不成立。"""
        c1 = b64d(vault.enc_payload(self.K, "aaaa"))
        c2 = b64d(vault.enc_payload(self.K, "bbbb"))
        x = bytes(a ^ b for a, b in zip(c1[3:], c2[3:]))   # 跳过 MAGIC 后本应=可预言关系
        m = bytes(a ^ b for a, b in zip(b"aaaa", b"bbbb"))
        self.assertNotEqual(x[:4], m, "nonce 随机化必须打破 c1^c2=m1^m2（红：相等）")

    def test_same_plaintext_two_ciphertexts(self):
        c1 = vault.enc_payload(self.K, "same")
        c2 = vault.enc_payload(self.K, "same")
        self.assertNotEqual(c1, c2, "nonce 语义：同明文异密文")

    def test_tamper_fail_closed(self):
        raw = bytearray(b64d(vault.enc_payload(self.K, "secret-123")))
        raw[-1] ^= 1
        with self.assertRaises(Exception):
            vault.dec_payload(self.K, base64.b64encode(bytes(raw)).decode())

    def test_legacy_payload_still_readable(self):
        """双读过渡裁决：存量 XOR 夹具可读（迁移未完成前不炸）。"""
        legacy = base64.b64encode(
            bytes(a ^ b for a, b in zip("old-format".encode(), vault._keystream(self.K, 10)))).decode()
        self.assertEqual(vault.dec_payload(self.K, legacy), "old-format")

    def test_derive_key_pbkdf2(self):
        k1 = vault.derive_key("pass-phrase", b"salt-1234")
        k2 = vault.derive_key("pass-phrase", b"salt-5678")
        self.assertEqual(len(k1), 64)
        self.assertNotEqual(k1, k2, "盐异键异")


class TestKeyChannel(unittest.TestCase):
    def test_load_key_prefers_external_keyfile(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        kp = os.path.join(td.name, "external.key")
        with open(kp, "w", encoding="utf-8") as f:
            f.write("external-key\n")
        gd = os.path.join(td.name, "G-v")
        os.makedirs(os.path.join(gd, "vault"))
        with open(os.path.join(gd, "vault", ".key"), "w", encoding="utf-8") as f:
            f.write("onsite-key")
        old = os.environ.get("TANYIN_VAULT_KEYFILE")
        os.environ["TANYIN_VAULT_KEYFILE"] = kp
        try:
            self.assertEqual(vault.load_key(gd), "external-key", "外移密钥优先（密钥同盘 High）")
        finally:
            if old is None:
                os.environ.pop("TANYIN_VAULT_KEYFILE", None)
            else:
                os.environ["TANYIN_VAULT_KEYFILE"] = old

    def test_deploy_vault_rejects_secret_in_argv(self):
        """红：密码/密值走 argv（进程列表可读）——改 stdin/env 通道后 argv 形=usage exit 2。"""
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-dv")
        os.makedirs(gd)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-guard"),
                            "deploy-vault", "--goal-dir", gd,
                            "--cred=1", "--username=u", "--secret=topsecret"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, "红现状：--secret argv 被接受")
        self.assertNotIn("topsecret", r.stdout + r.stderr, "密值不得回显")
        # env 通道成功部署
        env = dict(os.environ, TANYIN_VAULT_SECRET="topsecret", TANYIN_VAULT_PASSPHRASE="pp")
        r2 = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-guard"),
                             "deploy-vault", "--goal-dir", gd, "--cred=1", "--username=u"],
                            capture_output=True, text=True, env=env)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        mf = open(os.path.join(gd, "vault", "manifest.tsv"), encoding="utf-8").read()
        self.assertIn("etm-sha256", mf, "v2 算法列")


if __name__ == "__main__":
    unittest.main()

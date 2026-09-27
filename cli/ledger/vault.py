# -*- coding: utf-8 -*-
"""vault 解密单源（批4 T4）——tanyin-guard 原逻辑原样搬家，guard/replay 共用。

冻结接口（T5 重放 {{vault:cred-N}} 占位符回注消费）：load_key/secret/secrets；
read_cred/enc_payload/dec_payload/vault_dir 为同源实现细节（guard thin delegate 调用）。
批次 6 换真加密只改本文件内部实现，签名与返回形状不动。
批次 7 T10（High）：enc/dec 升级 v2=nonce 随机化+EtM(HMAC-SHA256)——专家实证
「同 key 下 m1^m2==c1^c2（密文可滚动伪造）+篡改无认证」双洞收口；PBKDF2 派生
（passphrase→主钥）+密钥外移（TANYIN_VAULT_KEYFILE env 通道优先，vault/.key 回落）。
裁决（双读过渡）：dec_payload 无 MAGIC 前缀=legacy XOR 读（stderr 一次性告警）——
存量夹具零破坏；全量 cutover 登记 b7 台账随生产钥仪式执行。"""
import base64, hashlib, os
import hmac as _hmac
import sys

TAB = chr(9)

# v2 载荷：b64(MAGIC(3B) + nonce(12B) + ct + tag(HMAC-SHA256 32B))
MAGIC = b"TV2"
_LEGACY_WARNED = False


def _subkeys(key):
    """子钥派生：enc_key/mac_key 分域（同一字节串不双用）。"""
    return (hashlib.sha256((key + ":enc").encode()).digest(),
            hashlib.sha256((key + ":mac").encode()).digest())


def vault_dir(gd):
    return os.path.join(gd, "vault")


def _keystream(key, n):
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256((key + ":" + str(counter)).encode()).digest()
        counter += 1
    return out[:n]


def enc_payload(key, plaintext):
    """v2（批次 7 T10）：nonce 随机化+EtM(HMAC-SHA256)——m1^m2=c1^c2 关系消除、
    篡改 fail-closed。签名不变：enc_payload(key, plaintext) -> b64 str。"""
    data = plaintext.encode("utf-8")
    enc_key, mac_key = _subkeys(key)
    nonce = os.urandom(12)
    ks = _keystream(enc_key.hex() + ":" + nonce.hex(), len(data))
    ct = bytes(a ^ b for a, b in zip(data, ks))
    tag = _hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    return base64.b64encode(MAGIC + nonce + ct + tag).decode()


def dec_payload(key, b64):
    """双读过渡（批次 7 T10 裁决）：TV2 前缀=v2 认证读；无前缀=legacy XOR 读
    （stderr 一次性告警——存量夹具零破坏，legacy 退役随生产钥仪式）。"""
    global _LEGACY_WARNED
    raw = base64.b64decode(b64)
    if not raw.startswith(MAGIC):
        if not _LEGACY_WARNED:
            sys.stderr.write("vault legacy XOR 载荷（无认证）——请重部署升级 v2\n")
            _LEGACY_WARNED = True
        data = bytes(a ^ b for a, b in zip(raw, _keystream(key, len(raw))))
        return data.decode("utf-8")
    enc_key, mac_key = _subkeys(key)
    nonce, ct, tag = raw[3:15], raw[15:-32], raw[-32:]
    want = _hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    if not _hmac.compare_digest(tag, want):
        raise ValueError("vault 载荷认证失败（篡改=拒绝，fail-closed）")
    ks = _keystream(enc_key.hex() + ":" + nonce.hex(), len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks)).decode("utf-8")


def derive_key(passphrase, salt):
    """PBKDF2-HMAC-SHA256（stdlib 单源；200k 轮）——passphrase→主钥，防弱口令直用。
    返回 hex 文本（.key 单源存储形态）。"""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 200000).hex()


def load_key(gd):
    # 密钥外移（批次 7 T10）：TANYIN_VAULT_KEYFILE env 通道优先；回落 vault/.key（存量兼容）。
    p = os.environ.get("TANYIN_VAULT_KEYFILE") or os.path.join(vault_dir(gd), ".key")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read().strip()


def read_cred(gd, n):
    key = load_key(gd)
    p = os.path.join(vault_dir(gd), "cred-%s.enc" % n)
    if not key or not os.path.exists(p):
        return None, None
    return dec_payload(key, open(p, encoding="utf-8").read()).split(chr(10), 1)


def secret(gd, n):
    """单凭据真值（T5 重放占位符回注）；缺 key/缺条目/缺密位=None（fail-closed）。"""
    got = read_cred(gd, n)
    return got[1] if isinstance(got, list) and len(got) > 1 else None


def secrets(gd):
    """全部已部署凭据真值 [(cred号, secret)]——以 vault/manifest.tsv 为准
    （exec 与 inject 同源；exec 此前按 creds.tsv 行序编号，与 vault 实际凭据号
    脱节导致真值不脱敏，洞 3）。"""
    out = []
    mp = os.path.join(vault_dir(gd), "manifest.tsv")
    if os.path.exists(mp):
        for l in open(mp, encoding="utf-8").read().splitlines():
            if l.strip():
                n = l.split(TAB)[0]
                _, sec = read_cred(gd, n)
                if sec:
                    out.append((n, sec))
    out.sort(key=lambda t: -len(t[1]))
    return out
# -*- coding: utf-8 -*-
"""vault 解密单源（批4 T4）——tanyin-guard 原逻辑原样搬家，guard/replay 共用。

冻结接口（T5 重放 {{vault:cred-N}} 占位符回注消费）：load_key/secret/secrets；
read_cred/enc_payload/dec_payload/vault_dir 为同源实现细节（guard thin delegate 调用）。
批次 6 换真加密只改本文件内部实现，签名与返回形状不动。"""
import base64, hashlib, os

TAB = chr(9)


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
    data = plaintext.encode("utf-8")
    return base64.b64encode(bytes(a ^ b for a, b in zip(data, _keystream(key, len(data))))).decode()


def dec_payload(key, b64):
    data = base64.b64decode(b64)
    return bytes(a ^ b for a, b in zip(data, _keystream(key, len(data)))).decode("utf-8")


def load_key(gd):
    p = os.path.join(vault_dir(gd), ".key")
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else None


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

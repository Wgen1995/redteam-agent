# -*- coding: utf-8 -*-
"""ecdsa_verify · 纯标准库 P-256 ECDSA 验签（openssl 缺席的零依赖平替，v0.7c）。

只验不签（验签无随机性需求，仿射坐标一次验证性能足够）。签名/公钥均 DER/PEM
与 openssl 兼容（同 supply_chain 契约）。交叉验证：本模块结果须与 openssl pkeyutl 一致
（tests/test_v07c_ecdsa.py 内嵌 openssl 生成的固定向量）。"""
import base64
import hashlib

P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
GX = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
GY = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5


def _inv(x, m):
    return pow(x, -1, m)


def _padd(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        l = (3 * x1 * x1 + A) * _inv(2 * y1, P) % P
    else:
        l = (y2 - y1) * _inv(x2 - x1, P) % P
    x3 = (l * l - x1 - x2) % P
    return x3, (l * (x1 - x3) - y1) % P


def _pmul(k, point):
    r = None
    while k:
        if k & 1:
            r = _padd(r, point)
        point = _padd(point, point)
        k >>= 1
    return r


def _der_ints(data, expect_tag=0x30):
    """极简 DER：取序列体内的两个 INTEGER（签名 (r,s)）。"""
    assert data[0] == expect_tag, "DER tag"
    i = [1]

    def _len():
        j = i[0]
        n = data[j]
        if n < 0x80:
            i[0] = j + 1
            return n
        b = n & 0x7F
        i[0] = j + 1 + b
        return int.from_bytes(data[j + 1:j + 1 + b], "big")

    body = _len() + i[0]
    seq = data[i[0]:body]
    out = []
    j = 0
    while j < len(seq) and len(out) < 2:
        assert seq[j] == 0x02, "INT tag"
        j += 1
        n = seq[j]
        if n < 0x80:
            ln, j = n, j + 1
        else:
            b = n & 0x7F
            ln = int.from_bytes(seq[j + 1:j + 1 + b], "big")
            j += 1 + b
        out.append(int.from_bytes(seq[j:j + ln], "big"))
        j += ln
    return out


def load_pub_pem(pem):
    """PEM SubjectPublicKeyInfo → (x, y)。定位 04||x||y 位串（去开头的 04 无压缩点）。"""
    b64 = "".join(l for l in pem.splitlines() if "-----" not in l)
    der = base64.b64decode(b64)
    raw = None
    for off in range(len(der) - 64):
        if der[off] == 0x04 and der[off - 1] in (0x00, 0x03) and off + 65 <= len(der):
            nxt = der[off + 65:off + 66]
            if off + 65 == len(der) or nxt in (0x00, 0xA0) or off + 65 == len(der):
                raw = der[off:off + 65]
                break
    assert raw and len(raw) == 65 and raw[0] == 4, "pub point"
    return int.from_bytes(raw[1:33], "big"), int.from_bytes(raw[33:65], "big")


def verify_der_digest(pub_pem, sig_der, digest):
    """摘要直验（digest 已是 32B sha256——supply_chain canonical_digest 形）。"""
    x, y = load_pub_pem(pub_pem)
    r, s = _der_ints(sig_der)
    if not (1 <= r < N and 1 <= s < N):
        return False
    z = int.from_bytes(digest, "big")
    w = _inv(s, N)
    u1 = z * w % N
    u2 = r * w % N
    pt = _padd(_pmul(u1, (GX, GY)), _pmul(u2, (x, y)))
    if pt is None:
        return False
    return pt[0] % N == r


def verify_der_sig(pub_pem, sig_der, message):
    return verify_der_digest(pub_pem, sig_der, hashlib.sha256(message).digest())
    """ECDSA-P256 验签（msg 先 sha256）。True/False；格式坏=断言错（fail-loud）。"""
    x, y = load_pub_pem(pub_pem)
    r, s = _der_ints(sig_der)
    if not (1 <= r < N and 1 <= s < N):
        return False
    z = int.from_bytes(hashlib.sha256(message).digest(), "big")
    w = _inv(s, N)
    u1 = z * w % N
    u2 = r * w % N
    pt = _padd(_pmul(u1, (GX, GY)), _pmul(u2, (x, y)))
    if pt is None:
        return False
    return pt[0] % N == r

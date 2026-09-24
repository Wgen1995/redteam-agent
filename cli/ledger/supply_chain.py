# -*- coding: utf-8 -*-
"""tools.lock 供应链锁定+ECDSA 验签（契约 10；批4 T10）。

签名覆盖=行前四字段规范串（键\t版本\tsha256\t）sha256 digest；验签经 openssl 子进程
（python3 stdlib 无 ECDSA——契约 10 终审先例）；fail-closed：openssl 缺失=不可判（ENV）。"""
import hashlib, os, subprocess, tempfile
from shutil import which

FIELDS = ("key", "version", "sha256", "sig", "commit")


def load_lock(path):
    entries = {}
    for ln in open(path, encoding="utf-8").read().splitlines():
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.startswith("#") or ln.startswith("format_version"):
            continue
        parts = ln.split("\t")
        if len(parts) != 5:
            raise ValueError("tools.lock 行非五字段: %r" % ln)
        entries[parts[0]] = dict(zip(FIELDS, parts))
    return entries


def canonical_digest(entry):
    canon = "\t".join([entry["key"], entry["version"], entry["sha256"], ""])
    return hashlib.sha256(canon.encode("utf-8")).digest()


def verify_entry(entry, pubkey_pem):
    """返回 (ok, reason)；一切「不过」形态（含签名非 hex）=失败对非 raise——
    「不过=blocked」契约语义（批次 4 评审收尾 fail-closed 形式统一）。"""
    if which("openssl") is None:
        return False, "openssl-missing（ENV：安装 openssl 后复跑）"
    try:
        sig = bytes.fromhex(entry["sig"])
    except (ValueError, TypeError):
        return False, "sig 非 hex（fail-closed=blocked）: %r" % entry.get("sig", "")[:16]
    with tempfile.TemporaryDirectory() as td:
        dg, sg = os.path.join(td, "d"), os.path.join(td, "s")
        open(dg, "wb").write(canonical_digest(entry))
        open(sg, "wb").write(sig)
        r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin",
                            "-inkey", pubkey_pem, "-sigfile", sg, "-in", dg],
                           capture_output=True, text=True)
        return (r.returncode == 0), (r.stdout + r.stderr).strip()


def sign_entry(entry, privkey_pem):
    """发布侧签名（测试/发布流程用；运行时只验不签）。"""
    with tempfile.TemporaryDirectory() as td:
        dg = os.path.join(td, "d")
        open(dg, "wb").write(canonical_digest(entry))
        r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", privkey_pem, "-in", dg],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError("openssl sign 失败: " + r.stderr.decode("utf-8", "replace"))
        return r.stdout.hex()

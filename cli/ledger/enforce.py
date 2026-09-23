# -*- coding: utf-8 -*-
"""enforce —— Tier 1（tanyin-guard）与 Tier 2（hooks/simulate.py）同源执法逻辑。

SECW-3：hooks 三模板声明「deny-list 比对 + scope 解析」同源语义，此前 simulate.py
只实现 deny-list 半边（SECW-1 盘点差距 1）。抽出单源防两份漂移：
deny-list / scope include 加载 / 主机提取 / 界外判定。scope.tsv 缺失=includes
为空=一切带主机命令界外（fail-closed，契约 11 Tier 2 行）。
"""
import ipaddress

from .schemas import TABLES


DENY_LIST = ["rm -rf /", "shutdown", "reboot", "mkfs", "dd if=", "format ", "> /dev/sd"]


def deny_hit(joined):
    for d in DENY_LIST:
        if d in joined:
            return d
    return None


def load_scope(session):
    sf = TABLES["scope.tsv"]
    ki, mi = sf.index("kind"), sf.index("matcher")
    return [r[mi] for r in session.rows("scope.tsv") if r[ki] == "include"]


def host_in_scope(host, includes):
    if not host:
        return True
    h = host.lower().rstrip(".")
    for m in includes:
        m = m.lower()
        if m.startswith("*."):
            if h == m[2:] or h.endswith("." + m[2:]):
                return True
        elif "/" in m:
            try:
                if ipaddress.ip_address(h) in ipaddress.ip_network(m, strict=False):
                    return True
            except ValueError:
                pass
        elif h == m or h.endswith("." + m):
            return True
    return False


def out_of_scope_hosts(args, includes):
    """按出现序返回 args 中命中的界外主机（去重保序）。"""
    seen, out = set(), []
    for h in extract_hosts(args):
        if h not in seen:
            seen.add(h)
            if not host_in_scope(h, includes):
                out.append(h)
    return out


def extract_hosts(args):
    hosts = []
    for a in args:
        for tok in a.replace(",", " ").split():
            if "://" in tok:
                tok = tok.split("://", 1)[1]
            if "@" in tok:
                tok = tok.split("@")[-1]
            cand = tok.split("/")[0].split(":")[0]
            if cand and ("." in cand or cand.replace(".", "").isdigit()) and not cand.startswith("-"):
                hosts.append(cand)
    return hosts

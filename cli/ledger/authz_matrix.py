# -*- coding: utf-8 -*-
"""身份矩阵 role×endpoint 覆盖投影（§6.5/契约 03 §5.2——不新增表，纯投影）。

T8（批4）交付：coverage(session) 供 tanyin-viz（T11）与检出率 eval 消费。
role 集合=creds 现 active 行 role 去重；端点=type=endpoint 资产；
格覆盖=该 (endpoint,role) 有 auth_context 指向同 role CRED 的 finding，或该端点存在
kind=authz 负结果 fact（回归基线=各角色一致，视为该端点全 role 覆盖）。"""
from .schemas import TABLES


def _cell(table, row, col):
    return row[TABLES[table].index(col)]


def coverage(session):
    s = session
    roles = sorted({_cell("creds.tsv", r, "role") for r in s.rows("creds.tsv")
                    if _cell("creds.tsv", r, "status") == "active"})
    cred_role = {r[0]: _cell("creds.tsv", r, "role") for r in s.rows("creds.tsv")}
    endpoints = sorted({_cell("assets.tsv", r, "value") for r in s.rows("assets.tsv")
                        if _cell("assets.tsv", r, "type") == "endpoint"})
    covered = {}
    for f in s.rows("findings.tsv"):
        ac = _cell("findings.tsv", f, "auth_context")
        if ac.startswith("CRED-"):
            covered.setdefault(_cell("findings.tsv", f, "affected_asset_id"), set()).add(cred_role.get(ac, ""))
    negfacts = {}
    for f in s.rows("facts.tsv"):
        if _cell("facts.tsv", f, "kind") == "authz":
            negfacts.setdefault(_cell("facts.tsv", f, "target"), True)
    ast_value = {r[0]: _cell("assets.tsv", r, "value") for r in s.rows("assets.tsv")}
    out = {"roles": roles, "endpoints": {}, "coverage": ""}
    hit = total = 0
    for ep in endpoints:
        roles_map = {}
        for role in roles:
            fd = next((f[0] for f in s.rows("findings.tsv")
                       if ast_value.get(_cell("findings.tsv", f, "affected_asset_id")) == ep
                       and _cell("findings.tsv", f, "auth_context").startswith("CRED-")
                       and cred_role.get(_cell("findings.tsv", f, "auth_context")) == role), "")
            ok = bool(fd) or ep in negfacts
            roles_map[role] = {"covered": ok, "finding": fd, "fact": "" if fd else "见负结果 fact"}
            total += 1
            hit += 1 if ok else 0
        out["endpoints"][ep] = {"roles": roles_map}
    out["coverage"] = "%d/%d" % (hit, total)
    return out

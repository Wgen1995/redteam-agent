# -*- coding: utf-8 -*-
"""身份矩阵装配(功能6·设计§1 地基)——从账本 CRED 活链收集身份,投影「几把钥匙各能开哪」。

纪律:
- 挂链纪律沿用(RT-0016 血律): 每个身份携带 auth_context=代表凭据行 id 原样;
  audit_auth_context() 复查「intent 挂 CRED 而 finding 空 auth_context」的链断形
  ——只复查不新造记账通道(发现落账走既有 ledger-add-finding 命令面)。
- 覆盖投影单源: 「各能开哪」复用 cli/ledger/authz_matrix.coverage(role×endpoint),
  本模块只做 CRED 活链→钥匙的归并,不重建第二份投影。
- 活链语义(契约 03 §4+终审): status=active 才是活钥匙;session 沿 parent_cred
  上溯,父链任一环非 active/悬引用/环=断链——断链会话不作代表(静态兜底),
  断链如实注记不静默(事件溯源: 失效链不入矩阵,但断链形要留案)。
- 真值永不进账本(契约 03 §1): 身份只携带 secret_ref 占位符({{vault:cred-N}})。

降级(设计§失败怎么办): 单账号→vertical-only(只测未登录 vs 登录垂直面);
零活钥匙→anonymous-only;纯静态无业务流的上层如实标「无业务面」。
"""
from ledger.schemas import TABLES
from ledger import authz_matrix

ANONYMOUS = "anonymous"
_ADMIN_ROLES = ("admin", "administrator", "root", "superuser")


def _cell(table, row, col):
    return row[TABLES[table].index(col)]


def _is_admin(role):
    r = (role or "").strip().lower()
    return r in _ADMIN_ROLES or "admin" in r


def _live_chain(row, by_id):
    """沿 parent_cred 上溯到 static-根: 返回 (链 id 根在前, 断链原因或空)。

    static-cred 自身即根(链=[自己]);session 父环非 active/悬引用/成环=断链。
    """
    seq, seen = [], set()
    cur, broken = row, ""
    while cur is not None:
        cid = cur[0]
        if cid in seen:
            return [], "cycle:" + cid
        seen.add(cid)
        seq.append(cid)
        if _cell("creds.tsv", cur, "kind") == "static-cred":
            break
        parent_id = _cell("creds.tsv", cur, "parent_cred")
        nxt = by_id.get(parent_id)
        if nxt is None:
            broken = "parent-missing:" + str(parent_id)
            break
        if _cell("creds.tsv", nxt, "status") != "active":
            broken = "parent-not-active:" + str(parent_id)
            break
        cur = nxt
    return list(reversed(seq)), broken


def collect_identities(session):
    """活链身份收集: 未登录恒居首;active 凭据按 (role, username_ref) 归并成钥匙。

    代表选取: 活链 session(最新者优先)→活 static-cred;断链成员如实注记。
    返回 dict 列表(label/role/username/kind/cred_id/auth_context/secret_ref/
    chain/tier/chain_broken/created)。
    """
    rows = session.rows("creds.tsv")
    by_id = {r[0]: r for r in rows}
    groups, order = {}, []
    for r in rows:
        if _cell("creds.tsv", r, "status") != "active":
            continue                      # 事件溯源: 非活行不入矩阵
        key = (_cell("creds.tsv", r, "role"), _cell("creds.tsv", r, "username_ref"))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    out = [{"label": ANONYMOUS, "role": ANONYMOUS, "username": "",
            "kind": "none", "cred_id": "", "auth_context": "", "secret_ref": "",
            "chain": [], "tier": "anonymous", "chain_broken": [], "created": ""}]
    for role, username in order:
        members = groups[(role, username)]
        broken_notes, best = [], None
        for r in members:
            chain, why = _live_chain(r, by_id)
            if why:
                broken_notes.append("%s: %s" % (r[0], why))
                continue
            created = _cell("creds.tsv", r, "created")
            rank = (1 if _cell("creds.tsv", r, "kind") == "session" else 0, created)
            if best is None or rank > best[0]:
                best = (rank, r, chain)
        if best is None:
            best = ((0, _cell("creds.tsv", members[-1], "created")), members[-1], [])
        _, rep, chain = best
        label = username or role
        out.append({"label": label, "role": role, "username": username,
                    "kind": _cell("creds.tsv", rep, "kind"),
                    "cred_id": rep[0], "auth_context": rep[0],
                    "secret_ref": _cell("creds.tsv", rep, "secret_ref"),
                    "chain": chain,
                    "tier": "admin" if _is_admin(role) else "regular",
                    "chain_broken": broken_notes,
                    "created": _cell("creds.tsv", rep, "created")})
    return out


def project(session):
    """「几把钥匙各能开哪」投影: collect_identities × authz_matrix.coverage 单源。

    返回 {keys, mode, missing, coverage, roles}: mode∈{triple-keys, dual-keys,
    vertical-only, anonymous-only}(设计§1 三把钥匙/可降双钥匙/单账号降级);
    missing=缺口清单(水平对照 peer/垂直对照 admin)。
    """
    ids = collect_identities(session)
    cov = authz_matrix.coverage(session)
    roles = cov.get("roles", [])
    keys = []
    for i in ids:
        opens = {}
        if i["role"] in roles:
            for ep, cell in (cov.get("endpoints") or {}).items():
                opens[ep] = cell["roles"][i["role"]]
        entry = dict(i)
        entry["opens"] = opens
        keys.append(entry)
    logged = [i for i in ids if i["label"] != ANONYMOUS]
    regulars = [i for i in logged if not _is_admin(i["role"])]
    admins = [i for i in logged if _is_admin(i["role"])]
    missing = []
    if len(regulars) < 2:
        missing.append("peer(水平对照缺第二把同级钥匙)")
    if not admins:
        missing.append("admin(垂直对照缺管理员钥匙)")
    if not logged:
        mode = "anonymous-only"
    elif len(logged) == 1:
        mode = "vertical-only"
    elif len(regulars) >= 2 and admins:
        mode = "triple-keys"
    else:
        mode = "dual-keys"
    return {"keys": keys, "mode": mode, "missing": missing,
            "coverage": cov.get("coverage", "0/0"), "roles": roles}


def audit_auth_context(session):
    """RT-0016 链断复查: intent.cred 非空而 finding.auth_context 空/不符 → 点名清单。

    只读复查(不写账);产出供总控在 P4 前补链——断链 finding 在 authz 门全拦是
    已付过一次的学费,本函数让它在落账当下就被看见。
    """
    intent_cred = {}
    for r in session.rows("intents.tsv"):
        intent_cred[r[0]] = _cell("intents.tsv", r, "cred")
    flags = []
    for f in session.rows("findings.tsv"):
        iid = _cell("findings.tsv", f, "intent_id")
        want = intent_cred.get(iid, "")
        got = _cell("findings.tsv", f, "auth_context")
        if want and got != want:
            flags.append({"finding": f[0], "intent": iid,
                          "expected_cred": want, "got": got})
    return flags

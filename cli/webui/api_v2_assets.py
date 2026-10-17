# -*- coding: utf-8 -*-
"""api_v2_assets（T3·P5.6）——测试资产页签只读投影，路由 /api/v2/assets.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_assets.py（_V2MountHandler）。

数据单源（spec §P5.6：assets+scope 复判）：
  资产表  = assets.tsv（跨代同 id 后代胜——复判可翻案：范围外→授权）
            × findings.tsv affected_asset_id 反指（关联发现链接）
            × timeline request: 行按资产值口径归并（已测请求数）；
  scope 汇总 = scope.tsv 四态计数（include/exclude/oob/account-grant）
            + 修订行计数（amendment_of 非空=扩展审批接入记录）。

请求归并口径（诚实法条，单源于此）：request: 事件目标串（"host/path"）与资产值
token 边界匹配——目标==值 或 目标以 值+"/" 起；网段/裸域无请求=诚实 0，不造数。
授权复判✓=账面 in_scope 列（资产入库即经范围复判，scope-check 单源不在本层复制）。
DSL 搜索（type:/value:/scope:/tested:/findings: + AND/OR/NOT）=页端实现，服务端
全量只读给（页量级=资产数，真全量）。
"""
import os
import re

from ledger import core
from ledger.session_view import list_battles

ROUTE_ASSETS = "/api/v2/assets.json"
ROUTES = {ROUTE_ASSETS: None}                       # 尾部赋真身（前向引用）

_REQ_PAT = re.compile(r"^request: (\S+)")
_IN_SCOPE = ("1", "in_scope", "true")
_OUT_SCOPE = ("0", "out_of_scope", "false")


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_tsv_rows(path, nfields):
    text = _read_text(path)
    if text is None:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        out.append((cols + [""] * nfields)[:nfields] if len(cols) < nfields else cols)
    return out


def _gens(battle_dir):
    """G-* 子目自然序（G-r2<G-r10；server._latest_gen 同律）；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


def _read_int(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None，布尔无语义：%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数：%r" % (name, value))


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir) —— 有战用战，无战回落主账本。"""
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return [], None, str(ledger_dir or "")
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return battles, None, None
    return battles, picked, os.path.join(root, picked["id"])


def _read_dirs(battle_dir, gens):
    if gens:
        return [os.path.join(battle_dir, g) for g in gens]
    return [battle_dir] if battle_dir else []


def _merge_by_id(battle_dir, gens, tname):
    """表行跨代合并：同 id 后代胜，保首现次序 → [(id, cols)]。"""
    nf = len(core.TABLES[tname])
    by_id, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, tname), nf):
            key = cols[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = cols
    return [(k, by_id[k]) for k in order]


def _requests_by_target(battle_dir, gens):
    """timeline request: 行 → {目标串: 次数}（跨代全并，确定性文件序）。"""
    nf = len(core.TABLES["timeline.tsv"])
    i_ev = core.TABLES["timeline.tsv"].index("event")
    out = {}
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), nf):
            m = _REQ_PAT.match(cols[i_ev])
            if m:
                out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def _req_hits(targets, value):
    """token 边界匹配：目标==值 或 目标以 值+"/" 起（host/path 口径）。"""
    v = (value or "").strip()
    if not v:
        return 0
    n = 0
    for t, c in targets.items():
        if t == v or t.startswith(v + "/"):
            n += c
    return n


def _auth_zh(in_scope):
    s = (in_scope or "").strip()
    if s in _IN_SCOPE:
        return "复判✓"
    if s in _OUT_SCOPE:
        return "范围外"
    return "未知"


# ------------------------------------------------------------------ 投影 --

def assets_view(battles_dir=None, battle=None, ledger_dir=None):
    """测试资产页签投影 → {battle, battles, goal, counts, scope, assets[]}。

    assets 每行：id/type/value/in_scope/auth_zh/created/requests/findings[]/
    findings_count。战不存在 → {"error":..., "battles":[...]}；坏战号 ValueError。
    """
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    gens = _gens(battle_dir) if battle_dir else []
    goal = gens[-1] if gens else os.path.basename(os.path.normpath(str(battle_dir or "")))

    ta = {f: i for i, f in enumerate(core.TABLES["assets.tsv"])}
    tfd = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
    assets = _merge_by_id(battle_dir, gens, "assets.tsv")
    findings = _merge_by_id(battle_dir, gens, "findings.tsv")
    targets = _requests_by_target(battle_dir, gens)

    findings_of = {}
    for fid, cols in findings:
        if cols[tfd["status"]].strip() not in ("", "active"):
            continue
        ast = cols[tfd["affected_asset_id"]].strip()
        if ast:
            findings_of.setdefault(ast, []).append(fid)

    out = []
    for aid, cols in assets:
        reqs = _req_hits(targets, cols[ta["value"]])
        fids = findings_of.get(aid, [])
        ins = cols[ta["in_scope"]].strip()
        out.append({
            "id": aid, "type": cols[ta["type"]], "value": cols[ta["value"]],
            "in_scope": ins if ins in _IN_SCOPE + _OUT_SCOPE else "",
            "auth_zh": _auth_zh(ins),
            "created": cols[ta["created"]], "requests": reqs,
            "findings": fids, "findings_count": len(fids),
        })

    # scope 汇总（复判规则面；matcher 匹配判定=scope-check 单源不在本层复制）
    tsc = {f: i for i, f in enumerate(core.TABLES["scope.tsv"])}
    scope = {"include": 0, "exclude": 0, "oob": 0, "account_grant": 0, "amendments": 0}
    for _sid, cols in _merge_by_id(battle_dir, gens, "scope.tsv"):
        kind = cols[tsc["kind"]].strip()
        if kind in scope:
            scope[kind] += 1
        if cols[tsc["amendment_of"]].strip():
            scope["amendments"] += 1

    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles, "goal": goal,
        "counts": {
            "total": len(out),
            "in_scope": sum(1 for a in out if a["in_scope"] in _IN_SCOPE),
            "out_of_scope": sum(1 for a in out if a["in_scope"] in _OUT_SCOPE),
            "tested": sum(1 for a in out if a["requests"] > 0),
            "with_findings": sum(1 for a in out if a["findings_count"] > 0),
            "requests_total": sum(a["requests"] for a in out),
        },
        "scope": scope,
        "assets": out,
    }


def assets_route(query, ledger_dir=None, battles_dir=None):
    """路由层：ValueError=422；error 形=404；正常=200。"""
    try:
        payload = assets_view(battles_dir=battles_dir, battle=query.get("battle"),
                              ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_ASSETS] = assets_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)

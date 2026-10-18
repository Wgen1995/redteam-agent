# -*- coding: utf-8 -*-
"""api_v2_asset_registry（T7·P8-P18 资产库跨任务）——资产登记处只读投影，
路由 /api/v2/asset-registry.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性——同输入两跑逐字节一致）；挂载=ROUTES 单源表由
include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_asset_registry.py（_V2MountHandler）：会话门复用
Handler._session_ok，缺会话=401 JSON。dispatch(path, query, ledger_dir,
battles_dir) 与 api_v2_broadcast 同形（本域不依赖主账本目录，入参原样收下）。

数据单源（spec §P8-P18 资产库跨任务：跨任务资产登记读面）：
  资产表  = battles/*/G-*/assets.tsv——跨代同 id 后代胜（与 P5.6 任务内资产页
            同律：api_v2_assets._merge_by_id 同式本地重实现，口径单源不另造）；
  归并键  = 资产值 value（登记处口径：同值=同一登记对象，任务内 id 可各异）；
  复判    = 账面 in_scope 列（入库即经范围复判——scope-check 单源不在本层复制）；
  发现    = findings.tsv affected_asset_id 反指（status 空/active 活跃行口径）；
  请求    = timeline request: 行目标串与资产值 token 边界匹配（目标==值 或
            目标以 值+"/" 起——host/path 口径，同 P5.6）。

搜索律（q）：子串命中 value/type/资产 id（大小写不敏感）；页端另做本地过滤，
服务端全量只读给（登记处量级=唯一资产值数，真全量）。
"""
import os
import re

from ledger import core
from ledger.session_view import list_battles

ROUTE_REGISTRY = "/api/v2/asset-registry.json"
ROUTES = {ROUTE_REGISTRY: None}                       # 尾部赋真身（前向引用）

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


def _read_dirs(battle_dir, gens):
    if gens:
        return [os.path.join(battle_dir, g) for g in gens]
    return [battle_dir] if battle_dir else []


def _merge_by_id(battle_dir, gens, tname, nfields):
    """表行跨代合并：同 id 后代胜，保首现次序 → [(id, cols)]。"""
    by_id, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, tname), nfields):
            key = cols[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = cols
    return [(k, by_id[k]) for k in order]


_TL = core.TABLES["timeline.tsv"]
_TL_EV = _TL.index("event")
_TL_NF = len(_TL)
_AS = core.TABLES["assets.tsv"]
_AS_VALUE = _AS.index("value")
_AS_TYPE = _AS.index("type")
_AS_SCOPE = _AS.index("in_scope")
_FD = core.TABLES["findings.tsv"]
_FD_ASSET = _FD.index("affected_asset_id")
_FD_STATUS = _FD.index("status")


def _requests_by_target(battle_dir, gens):
    """timeline request: 行 → {目标串: 次数}（跨代全并，确定性文件序）。"""
    out = {}
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), _TL_NF):
            m = _REQ_PAT.match(cols[_TL_EV])
            if m:
                out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def _req_hits(targets, value):
    """token 边界匹配：目标==值 或 目标以 值+"/"+"/" 起（host/path 口径）。"""
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


def _battle_assets(battle_dir):
    """一战 → [{id, value, type, in_scope, auth_zh, findings, requests}]。"""
    gens = _gens(battle_dir)
    assets = _merge_by_id(battle_dir, gens, "assets.tsv", len(_AS))
    findings = _merge_by_id(battle_dir, gens, "findings.tsv", len(_FD))
    targets = _requests_by_target(battle_dir, gens)

    findings_n = {}
    for _fid, cols in findings:
        if cols[_FD_STATUS].strip() not in ("", "active"):
            continue
        ast = cols[_FD_ASSET].strip()
        if ast:
            findings_n[ast] = findings_n.get(ast, 0) + 1

    out = []
    for aid, cols in assets:
        value = cols[_AS_VALUE]
        ins = cols[_AS_SCOPE].strip()
        out.append({
            "id": aid, "value": value, "type": cols[_AS_TYPE],
            "in_scope": ins if ins in _IN_SCOPE + _OUT_SCOPE else "",
            "auth_zh": _auth_zh(ins),
            "findings": findings_n.get(aid, 0),
            "requests": _req_hits(targets, value),
        })
    return out


# ------------------------------------------------------------------ 投影 --

def asset_registry_view(battles_dir=None, q=None):
    """资产登记处投影：跨任务按值归并 → {q, battles, counts, assets[]}。

    assets 每行：value/type/first_battle/battle_count/battles[{id,n,asset_id,
    in_scope,auth_zh,findings,requests}]/findings_count/requests/ids——只读零写入。
    """
    battles = list_battles(battles_dir)
    registry = {}
    for meta in battles:
        battle_dir = os.path.join(str(battles_dir or ""), meta["id"])
        for row in _battle_assets(battle_dir):
            value = row["value"]
            if not value:
                continue
            entry = registry.setdefault(value, {
                "value": value, "type": row["type"], "battles": [],
                "ids": [], "requests": 0, "findings_count": 0,
            })
            entry["battles"].append({
                "id": meta["id"], "n": meta["n"], "asset_id": row["id"],
                "in_scope": row["in_scope"], "auth_zh": row["auth_zh"],
                "findings": row["findings"], "requests": row["requests"],
            })
            entry["ids"].append(row["id"])
            entry["requests"] += row["requests"]
            entry["findings_count"] += row["findings"]

    assets = []
    for value in sorted(registry):
        e = dict(registry[value])
        e["battle_count"] = len(e["battles"])
        e["first_battle"] = e["battles"][0]["id"] if e["battles"] else ""
        assets.append(e)

    if q:
        needle = str(q).strip().lower()
        if needle:
            assets = [a for a in assets if needle in (
                "%s %s %s" % (a["value"], a["type"], " ".join(a["ids"]))).lower()]

    return {
        "q": q or "",
        "battles": battles,
        "counts": {
            "battles": len(battles),
            "assets": len(assets),
            "cross_battle": sum(1 for a in assets if a["battle_count"] >= 2),
            "requests_total": sum(a["requests"] for a in assets),
            "findings_total": sum(a["findings_count"] for a in assets),
        },
        "assets": assets,
    }


def _registry_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = asset_registry_view(battles_dir=battles_dir, q=query.get("q"))
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "资产登记处参数无效: %s" % e}
    return 200, payload


ROUTES[ROUTE_REGISTRY] = _registry_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)

# -*- coding: utf-8 -*-
"""api_v2_coverage（T3·P5.7）——资产覆盖页签只读投影，路由 /api/v2/coverage.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_coverage.py。

覆盖诚实法条的可视化（spec §P5.7）：矩阵=终态门禁分母，本层只投影不裁量。
  热图    = matrix.tsv 长表 → 资产(attack_surface)×意图族(vuln_class) 格阵；
            同格后代行胜（事件溯源：追加行=翻案，d8fe68c 分域门律同构）；
            格状态五态：x=已覆盖 ?=存疑 -=不适用(测过负结果) !=受阻 空=未测；
            深度=该表面 request: 行数 log2(n+1) 对数色阶（未建格不虚造）。
  未测清单= state ∉ {x,-} 的格 + 原因归档（优先序=范围外>预算止>无凭据>
            按态[空=待测/?=存疑/!=受阻]）；范围外=资产账面 out_of_scope，
            预算止/无凭据=reason 文关键词（budget-exhausted|预算 / 凭据|cred|
            401|认证墙|token）——词表单源于此，报告覆盖承诺同口径。
"""
import math
import os
import re

from ledger import core
from ledger.session_view import list_battles

ROUTE_COVERAGE = "/api/v2/coverage.json"
ROUTES = {ROUTE_COVERAGE: None}                      # 尾部赋真身（前向引用）

_REQ_PAT = re.compile(r"^request: (\S+)")
_BUDGET_KEYS = ("budget-exhausted", "budget", "预算")
_CRED_KEYS = ("凭据", "cred", "401", "认证墙", "token")
_STATE_ZH = {"x": "已覆盖", "?": "存疑", "-": "不适用", "!": "受阻", "": "未测"}
_REASON_ZH = {"out_of_scope": "范围外", "no_cred": "无凭据", "budget_stop": "预算止",
              "pending": "待测", "inconclusive": "存疑", "blocked": "受阻",
              "other": "原因见格"}


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


def _merge_by_key(battle_dir, gens, tname, keyfn):
    """行按 keyfn 归并：后代行胜，保首现次序 → [(key, cols)]。"""
    nf = len(core.TABLES[tname])
    by, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, tname), nf):
            k = keyfn(cols)
            if k not in by:
                order.append(k)
            by[k] = cols
    return [(k, by[k]) for k in order]


def _requests_by_target(battle_dir, gens):
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
    """token 边界匹配（api_v2_assets 同口径，单源注释在此）。"""
    v = (value or "").strip()
    if not v:
        return 0
    return sum(c for t, c in targets.items() if t == v or t.startswith(v + "/"))


def _reason_code(state, reason, surface_out_of_scope):
    """原因归档：优先序=范围外 > 预算止 > 无凭据 > 按态。词表单源。"""
    if surface_out_of_scope:
        return "out_of_scope"
    low = (reason or "")
    if any(k in low for k in _BUDGET_KEYS):
        return "budget_stop"
    if any(k in low for k in _CRED_KEYS):
        return "no_cred"
    if state == "":
        return "pending"
    if state == "?":
        return "inconclusive"
    if state == "!":
        return "blocked"
    return "other"


# ------------------------------------------------------------------ 投影 --

def coverage_view(battles_dir=None, battle=None, ledger_dir=None):
    """资产覆盖页签投影 → {battle, battles, goal, counts, matrix_frozen,
    classes, surfaces[{name,requests,depth,in_scope,cells{}}], untested[],
    legend}。战不存在 → {"error":...,"battles":[...]}；坏战号 ValueError。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    gens = _gens(battle_dir) if battle_dir else []
    goal = gens[-1] if gens else os.path.basename(os.path.normpath(str(battle_dir or "")))

    tm = {f: i for i, f in enumerate(core.TABLES["matrix.tsv"])}
    ta = {f: i for i, f in enumerate(core.TABLES["assets.tsv"])}
    nf_tl = len(core.TABLES["timeline.tsv"])
    i_ev = core.TABLES["timeline.tsv"].index("event")

    # 资产复判面（value → in_scope；后代胜）
    scope_of = {}
    for _k, cols in _merge_by_key(battle_dir, gens, "assets.tsv",
                                  lambda c: c[ta["id"]].strip() or None):
        scope_of[cols[ta["value"]].strip()] = cols[ta["in_scope"]].strip()
    targets = _requests_by_target(battle_dir, gens)

    # 矩阵：格键=(surface, vclass)；双序（surface 序×class 序）保首现
    surface_order, class_order = [], []
    cells = {}
    frozen = False
    for _k, cols in _merge_by_key(
            battle_dir, gens, "matrix.tsv",
            lambda c: (c[tm["attack_surface"]].strip(),
                       c[tm["vuln_class"]].strip()) or None):
        s, vc = cols[tm["attack_surface"]].strip(), cols[tm["vuln_class"]].strip()
        if s not in surface_order:
            surface_order.append(s)
        if vc not in class_order:
            class_order.append(vc)
        if cols[tm["frozen_at"]].strip():
            frozen = True
        cells[(s, vc)] = {
            "state": cols[tm["state"]].strip(),
            "reason": cols[tm["reason"]].strip(),
            "intent_id": cols[tm["intent_id"]].strip(),
            "updated": cols[tm["updated"]].strip(),
        }

    surfaces = []
    untested = []
    counts = {"cells": len(cells), "covered": 0, "negative": 0, "blocked": 0,
              "inconclusive": 0, "untested": 0}
    for s in surface_order:
        reqs = _req_hits(targets, s)
        depth = round(math.log2(reqs + 1), 2)
        ins = scope_of.get(s, "")
        row_cells = {}
        for vc in class_order:
            c = cells.get((s, vc))
            if c is None:
                continue                                   # 未建格不虚造
            cc = dict(c)
            cc["state_zh"] = _STATE_ZH.get(c["state"], c["state"] or "未测")
            cc["requests"] = reqs
            cc["depth"] = depth
            row_cells[vc] = cc
            st = c["state"]
            if st == "x":
                counts["covered"] += 1
            elif st == "-":
                counts["negative"] += 1
            else:
                if st == "!":
                    counts["blocked"] += 1
                elif st == "?":
                    counts["inconclusive"] += 1
                else:
                    counts["untested"] += 1
                code = _reason_code(st, c["reason"], ins == "out_of_scope")
                untested.append({
                    "surface": s, "vclass": vc, "state": st,
                    "state_zh": cc["state_zh"], "reason": c["reason"],
                    "reason_code": code, "reason_zh": _REASON_ZH[code],
                    "intent_id": c["intent_id"],
                })
        surfaces.append({"name": s, "requests": reqs, "depth": depth,
                         "in_scope": ins, "cells": row_cells})

    done = counts["covered"] + counts["negative"]
    counts["coverage_pct"] = round(done / counts["cells"] * 100, 1) if counts["cells"] else 0.0
    counts["covered_pct"] = (round(counts["covered"] / counts["cells"] * 100, 1)
                             if counts["cells"] else 0.0)

    # 矩阵冻结=timeline matrix-freeze 行在场（锚点事实，非格行推断）
    if not frozen:
        for d in _read_dirs(battle_dir, gens):
            for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), nf_tl):
                if cols[i_ev].startswith("matrix-freeze"):
                    frozen = True
                    break
            if frozen:
                break

    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles, "goal": goal,
        "counts": counts, "matrix_frozen": frozen,
        "classes": class_order, "surfaces": surfaces, "untested": untested,
        "legend": {"x": "已覆盖", "?": "存疑", "-": "不适用（测过·无此面）",
                   "!": "受阻", "": "未测", "depth": "格色=已测请求数对数色阶",
                   "hatch": "未测格=斜纹"},
    }


def coverage_route(query, ledger_dir=None, battles_dir=None):
    """路由层：ValueError=422；error 形=404；正常=200。"""
    try:
        payload = coverage_view(battles_dir=battles_dir, battle=query.get("battle"),
                                ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_COVERAGE] = coverage_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)

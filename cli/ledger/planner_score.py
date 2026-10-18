# -*- coding: utf-8 -*-
"""五因子优先级引擎（功能5/8·补件一，设计 docs/design/2026-10-20-priority-planner-design.md）。

score = 0.40·可达性 + 0.20·凭据就绪 + 0.15·线索新鲜 + 0.15·矩阵饥渴
        + 0.10·历史收益——各因子 0-1，加权和，权重可配（goal 目录 planner.json）。
落 intents.priority 列（K1 通道复用，零 schema 改）。

纪律（设计补件一）：
- 纯机械可解释，LLM 不参与（排序≠分母律继承）；禁 LLM 裁量排序（可解释律）。
- 因子值全部从账本查（timeline=事件、matrix/creds/facts/findings=态势）。
- 同输入同序（排序=确定性函数；实时=回放特例律，金样钉死）。

Ruling：
- R-SCO-1 可达性复用 graph_cmds.reachable_gap_cells 单源（起点=scope-root 资产集，
  converge-check 同口径），不重造 BFS：可达空格=1.0，不可达=0.3。
- R-SCO-2 凭据就绪=该面上有 status=active 的 CRED 直接锚定
  （latest 行 scope_asset→资产 value==表面，RT-0016 挂链律的反向利用）。
- R-SCO-3 线索新鲜=fact.target==表面 的最新事实年龄衰减：≤1 天=1，1-7 天线性
  衰减到 0，>7 天=0（同面多 fact 取最鲜；未来钟钳满鲜）。
- R-SCO-4 矩阵饥渴=该 (表面×漏洞类) 键全历史行（含被覆盖旧态，事件溯源）零
  非空 state=1——最新行空格但历史碰过=0。
- R-SCO-5 历史收益=该漏洞类经 matrix.intent_id 归因命中过 findings（类级信号，
  任意表面）=1。
- R-SCO-6 排序键=(-score, attack_surface, vuln_class)，同分按行键字典序。
- R-SCO-7 权重校验 fail-loud：因子键须在名单内、值≥0、权和≤1（priority 列
  0-1 浮点硬门，write_cmds add-intent 同判据的前置自守）。
"""
import json
import os

from .enforce import parse_ts
from .graph_cmds import _build, _scope_root_targets, reachable_gap_cells
from .query_cmds import _cell, latest_matrix

CONFIG_NAME = "planner.json"

DEFAULT_WEIGHTS = {
    "reachability": 0.40,
    "cred_ready": 0.20,
    "clue_fresh": 0.15,
    "matrix_hunger": 0.15,
    "historical_yield": 0.10,
}
DEFAULT_DEBOUNCE_MS = 800      # ARTEX plannerLoop 同型（engine.go:800 硬编码同值）
DEFAULT_MAX_ADDS = 3           # 单轮研判最多派多少张意图卡
DEFAULT_ENGINE = "web-blackbox"

REACH_YES = 1.0                # 可达空格
REACH_NO = 0.3                 # 不可达空格（可达先行已有，公式化）

FRESH_FULL_S = 86400.0         # ≤1 天=满鲜
FRESH_ZERO_S = 7.0 * 86400.0   # ≥7 天=归零

_FACTOR_ORDER = ("reachability", "cred_ready", "clue_fresh",
                 "matrix_hunger", "historical_yield")
TAB = chr(9)


# ---------------------------------------------------------------- 线索新鲜衰减

def clue_freshness(age_s):
    """fact 年龄（秒）→ 鲜度 0-1：≤1 天=1；1-7 天线性衰减；≥7 天=0（R-SCO-3）。"""
    if age_s <= FRESH_FULL_S:
        return 1.0
    if age_s >= FRESH_ZERO_S:
        return 0.0
    return 1.0 - (age_s - FRESH_FULL_S) / (FRESH_ZERO_S - FRESH_FULL_S)


# ---------------------------------------------------------------- 权重可配文件

def load_config(goal_dir):
    """goal 目录 planner.json → {weights, debounce_ms, max_adds, engine}。

    缺文件=全缺省；在文件则覆盖对应键（weights 为部分覆盖：缺省因子保留缺省权重）。
    校验 fail-loud（R-SCO-7）：非法 JSON/未知因子/负权重/权和>1/非正防抖窗均
    ValueError——操作员手写配置，错配置宁可拒启不静默。
    """
    cfg = {"weights": dict(DEFAULT_WEIGHTS),
           "debounce_ms": DEFAULT_DEBOUNCE_MS,
           "max_adds": DEFAULT_MAX_ADDS,
           "engine": DEFAULT_ENGINE}
    path = os.path.join(goal_dir, CONFIG_NAME)
    if not os.path.exists(path):
        return cfg
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except ValueError as e:
        raise ValueError("planner.json 非法 JSON: %s" % e)
    if not isinstance(raw, dict):
        raise ValueError("planner.json 须为 JSON 对象")
    if "weights" in raw:
        w = raw["weights"]
        if not isinstance(w, dict):
            raise ValueError("weights 须为对象")
        for k, v in w.items():
            if k not in DEFAULT_WEIGHTS:
                raise ValueError("未知权重因子 %s（合法集=%s）"
                                 % (k, sorted(DEFAULT_WEIGHTS)))
            try:
                fv = float(v)
            except (TypeError, ValueError):
                raise ValueError("权重 %s 非数值: %r" % (k, v))
            if fv < 0:
                raise ValueError("权重 %s 为负: %r" % (k, v))
            cfg["weights"][k] = fv
        total = sum(cfg["weights"].values())
        if total > 1.0 + 1e-9:
            raise ValueError("权重和 %.6f>1（priority 列 0-1 硬门）" % total)
    if "debounce_ms" in raw:
        try:
            d = int(raw["debounce_ms"])
        except (TypeError, ValueError):
            raise ValueError("debounce_ms 须正整数: %r" % (raw["debounce_ms"],))
        if d < 1:
            raise ValueError("debounce_ms 须≥1: %r" % (raw["debounce_ms"],))
        cfg["debounce_ms"] = d
    if "max_adds" in raw:
        try:
            m = int(raw["max_adds"])
        except (TypeError, ValueError):
            raise ValueError("max_adds 须正整数: %r" % (raw["max_adds"],))
        if m < 1:
            raise ValueError("max_adds 须≥1: %r" % (raw["max_adds"],))
        cfg["max_adds"] = m
    if "engine" in raw:
        eng = str(raw["engine"]).strip()
        if not eng:
            raise ValueError("engine 须非空字符串")
        cfg["engine"] = eng
    return cfg


# ---------------------------------------------------------------- 态势因子（账本可查）

def gap_cells(s):
    """最新矩阵空格（latest 行 state 空）——reachable_gap_cells 同口径单源取法。"""
    return sorted((_cell(r, "matrix.tsv", "attack_surface"),
                   _cell(r, "matrix.tsv", "vuln_class"))
                  for r in latest_matrix(s).values()
                  if _cell(r, "matrix.tsv", "state").strip() == "")


def _reach_set(s):
    """可达空格集（R-SCO-1：graph_cmds 单源，scope-root 起点集）。"""
    nodes, _adj = _build(s)
    _reach, reach_gaps, _unreach = reachable_gap_cells(
        s, _scope_root_targets(s, nodes))
    return set(reach_gaps)


def _active_cred_surfaces(s):
    """有 active CRED 直接锚定的表面集（R-SCO-2；creds 事件溯源取 latest 行）。"""
    asset_val = {r[0]: _cell(r, "assets.tsv", "value") for r in s.rows("assets.tsv")}
    latest = {}
    for r in s.rows("creds.tsv"):
        latest[_cell(r, "creds.tsv", "id")] = r
    out = set()
    for r in latest.values():
        if _cell(r, "creds.tsv", "status") != "active":
            continue
        sa = _cell(r, "creds.tsv", "scope_asset")
        if sa in asset_val:
            out.add(asset_val[sa])
    return out


def _surface_freshness(s, ts):
    """表面→最鲜 fact 鲜度（R-SCO-3：target==表面，取同面最鲜）。

    钟解析单源=enforce.parse_ts（ISO8601→epoch 秒，Z/naive 同纳）；研判钟或
    fact.created 不可解析=该 fact 不计入（宽容降读，不炸排序）。
    """
    try:
        ts_epoch = parse_ts(ts)
    except (ValueError, TypeError):
        return {}
    best = {}
    for r in s.rows("facts.tsv"):
        tgt = _cell(r, "facts.tsv", "target")
        if not tgt:
            continue
        try:
            c_epoch = parse_ts(_cell(r, "facts.tsv", "created"))
        except (ValueError, TypeError):
            continue
        f = clue_freshness(ts_epoch - c_epoch)
        if tgt not in best or f > best[tgt]:
            best[tgt] = f
    return best


def _covered_keys(s):
    """全历史有非空 state 的 (表面×类) 键集（R-SCO-4：含被覆盖旧态行）。"""
    return {(_cell(r, "matrix.tsv", "attack_surface"),
             _cell(r, "matrix.tsv", "vuln_class"))
            for r in s.rows("matrix.tsv")
            if _cell(r, "matrix.tsv", "state").strip()}


def _yield_classes(s):
    """命中过 findings 的漏洞类集（R-SCO-5：matrix.intent_id→findings.intent_id）。"""
    hit_intents = {_cell(r, "findings.tsv", "intent_id")
                   for r in s.rows("findings.tsv")}
    return {_cell(r, "matrix.tsv", "vuln_class")
            for r in s.rows("matrix.tsv")
            if _cell(r, "matrix.tsv", "intent_id") in hit_intents}


def factor_snapshot(s, ts):
    """一轮态势的五因子底表（账本查询一次，全格共用）——可解释律的查询面。"""
    return {"reach": _reach_set(s),
            "cred_surfaces": _active_cred_surfaces(s),
            "fresh": _surface_freshness(s, ts),
            "covered": _covered_keys(s),
            "yield_classes": _yield_classes(s)}


def score_factors(snapshot, surface, vclass, weights):
    """单格五因子+加权和（纯函数：快照×格×权重→分，无账本访问）。"""
    factors = {
        "reachability": REACH_YES if (surface, vclass) in snapshot["reach"]
        else REACH_NO,
        "cred_ready": 1.0 if surface in snapshot["cred_surfaces"] else 0.0,
        "clue_fresh": snapshot["fresh"].get(surface, 0.0),
        "matrix_hunger": 0.0 if (surface, vclass) in snapshot["covered"] else 1.0,
        "historical_yield": 1.0 if vclass in snapshot["yield_classes"] else 0.0,
    }
    score = sum(weights.get(k, 0.0) * v for k, v in factors.items())
    return score, factors


def rank_gaps(s, ts, weights=None):
    """全部最新矩阵空格 → 五因子排序行（降序；同分行键字典序，R-SCO-6）。

    行={"attack_surface","vuln_class","score","factors"{五因子}}；同输入同序
    （金样钉死：tests/test_planner_score.py TestGoldenOrder）。
    """
    w = DEFAULT_WEIGHTS if weights is None else weights
    snapshot = factor_snapshot(s, ts)
    out = []
    for surface, vclass in gap_cells(s):
        score, factors = score_factors(snapshot, surface, vclass, w)
        out.append({"attack_surface": surface, "vuln_class": vclass,
                    "score": score, "factors": factors})
    out.sort(key=lambda r: (-r["score"], r["attack_surface"], r["vuln_class"]))
    return out


def render_rank(rows):
    """排行页文本：#count 行 + 表面\t类\t分\t五因子（逐格为什么排这，一眼懂）。"""
    lines = ["#count=%d" % len(rows)]
    for r in rows:
        cells = [r["attack_surface"], r["vuln_class"], "%.4f" % r["score"]]
        cells += ["%.4f" % r["factors"][k] for k in _FACTOR_ORDER]
        lines.append(TAB.join(cells))
    return chr(10).join(lines) + chr(10)

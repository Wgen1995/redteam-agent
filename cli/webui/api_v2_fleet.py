# -*- coding: utf-8 -*-
"""api_v2_fleet（多任务治理舰·件③）——总控数据端点，前缀 /api/v2/。

舰间契约（api_v2_tasks 同律）：本文件=本舰独写；只读投影零写入（一切文件
r 模式，禁 datetime.now——输出确定性：同输入两跑逐字节一致）；挂载=
api_pages._OPTIONAL_MODULES guarded import（落成即并网，半成品不拖垮整机）；
会话门在 server.py 挂载点（本模块零门禁）。

单路由（母舰令：只这一个新 API 文件）：
  GET /api/v2/fleet.json
      → 舰队总控数据面（fleet/fleet_state TSV 单源 + 仗账本四问汇总）：
        halted 全停旗 / cap{cap_soldiers, per_battle_soldiers,
        soldiers_active, headroom, queued} 总并发帽余量 /
        battles[]{battle, goal_dir, state, soldiers, priority, heartbeat_at,
        deadline, four_q{…}} / counts{五态计数}。

四问口径（驾驶舱舰 blueprint 首页四问→仗级汇总；人话词律——「任务」不说
「战」由前端词表负责，本层给结构化事实）：
  ①打出什么漏洞了 = findings 计数（verified/suspected 双色，ruled_out 计
    total 不计双色）；②正在打什么 = intents status=active 标题（≤5 条）；
  ③什么在等我 = intents status=pending/blocked 计数；④花多少钱 =
  budget.tsv token 累计 + 舰队行 usd 已用/帽（册行缺=0 诚实空）。

数据源分界：舰队册=fleet.tsv（supervisor 写）；仗内态势=各仗 goal 目录 TSV
（战士写）。本模块零写入零钟（api_pages 异常包裹=500 JSON 不炸连接层）。
"""
import os

from fleet import fleet_state as fs
from fleet import supervisor as sup
from ledger import core

ROUTE = "/api/v2/fleet.json"
ROUTES = {ROUTE: None}   # 尾部赋真身（前向引用，api_pages 先例）

_RUNNING_TITLES_CAP = 5


def _tsv_rows(path, tname):
    """轻读 TSV→列行（缺件=空；列宽对齐 core.TABLES——api_v2_tasks 同形，
    独立小拷贝防兄弟舰文件耦合）。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return []
    if not text:
        return []
    width = len(core.TABLES[tname])
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = [core.unesc(c) for c in line.split("\t")]
        out.append(cols + [""] * (width - len(cols)))
    return out


def _cell(tname, r, col):
    return r[core.TABLES[tname].index(col)]


def _to_f(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return 0.0


def four_questions(goal_dir, row):
    """单仗四问（确定性文件读：缺账本/缺表=诚实空）。"""
    findings = _tsv_rows(os.path.join(goal_dir, "findings.tsv"),
                         "findings.tsv")
    verified = sum(1 for r in findings
                   if _cell("findings.tsv", r, "exploitation_status")
                   == "verified")
    suspected = sum(1 for r in findings
                    if _cell("findings.tsv", r, "exploitation_status")
                    == "suspected")
    intents = _tsv_rows(os.path.join(goal_dir, "intents.tsv"), "intents.tsv")
    running = [(_cell("intents.tsv", r, "id"),
                _cell("intents.tsv", r, "title")) for r in intents
               if _cell("intents.tsv", r, "status") == "active"]
    pending = sum(1 for r in intents
                  if _cell("intents.tsv", r, "status") == "pending")
    blocked = sum(1 for r in intents
                  if _cell("intents.tsv", r, "status") == "blocked")
    budget = _tsv_rows(os.path.join(goal_dir, "budget.tsv"), "budget.tsv")
    tokens = sum(_to_f(_cell("budget.tsv", r, "token_delta")) for r in budget)
    usd_ledger = sum(_to_f(_cell("budget.tsv", r, "dollars_delta"))
                     for r in budget)
    usd_used = _to_f(row.get("budget_usd")) or usd_ledger
    return {
        "found": {"total": len(findings), "verified": verified,
                  "suspected": suspected},
        "running": {"count": len(running),
                    "intents": [t for _i, t in running][:_RUNNING_TITLES_CAP]},
        "waiting": {"pending": pending, "blocked": blocked},
        "spend": {"tokens_used": int(tokens), "usd_used": round(usd_used, 6),
                  "usd_cap": round(_to_f(row.get("budget_cap_usd")), 6)},
    }


def fleet_view(root):
    """fleet.tsv+fleet-meta+fleet.json → 总控数据面（零写入零钟）。"""
    cfg = sup.load_config(root)
    snap = fs.snapshot(root)
    battles = []
    for row in snap["battles"]:
        battles.append({
            "battle": row["battle"],
            "goal_dir": row["goal_dir"],
            "state": row["state"],
            "soldiers": _soldiers(row["soldiers"]),
            "priority": row["priority"],
            "heartbeat_at": row["heartbeat_at"],
            "deadline": row["deadline"],
            "four_q": four_questions(row["goal_dir"], row),
        })
    active_soldiers = snap["totals"]["active_soldiers"]
    cap = int(cfg["cap_soldiers"])
    return {
        "halted": snap["meta"].get("halted") == "1",
        "cap": {
            "cap_soldiers": cap,
            "per_battle_soldiers": int(cfg["per_battle_soldiers"]),
            "soldiers_active": active_soldiers,
            "headroom": cap - active_soldiers,
            "queued": snap["totals"]["by_state"].get("queued", 0),
        },
        "battles": battles,
        "counts": snap["totals"]["by_state"],
    }


def _soldiers(s):
    try:
        return int(str(s).strip() or 0)
    except ValueError:
        return 0


def dispatch(path, query, ledger_dir, battles_dir=None):
    """/api/v2/fleet.json → (200, 数据面)；非本域路由=None。"""
    if path != ROUTE:
        return None
    root = battles_dir if battles_dir is not None else _default_root()
    return 200, fleet_view(root)


def _default_root():
    """缺省舰队根=battles 根（fleet.tsv 与 registry.json 同址分层）。"""
    from ledger.session_view import default_battles_dir
    return default_battles_dir()


ROUTES[ROUTE] = fleet_view

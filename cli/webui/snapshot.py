# -*- coding: utf-8 -*-
"""webui snapshot（v0.9a T1）——账本只读快照：phases 态/budget 余量/timeline 尾部事件。

投影律（docs/design/tanyin-target-form.md §1/§2）：本模块只读零写入——
复用 phases_engine 只读 status 接口（v0.5a）与 query_cmds.budget_tree（§4.10
预算树上卷），timeline 经 core.Session 读尾。禁 datetime.now（输出确定性）。
"""
import io
from contextlib import redirect_stdout

from ledger import core, phases_engine, query_cmds

TL_FIELDS = len(core.TABLES["timeline.tsv"])
GOAL_FIELDS = ("id", "target", "objective")


def row_to_event(row):
    """timeline 行 → 事件 dict（ts/actor/phase/event + sha 前 8 位）。"""
    pad = list(row) + [""] * (TL_FIELDS - len(row))
    return {"ts": pad[0], "actor": pad[1], "phase": pad[2], "event": pad[3],
            "sha8": pad[core.TABLES["timeline.tsv"].index("hash")][:8]}


def phases_status(goal_dir):
    """复用 phases_engine.cmd_status（只读、零铸事件）→ {门: PASS/FAIL/PENDING}。"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        phases_engine.cmd_status(goal_dir, [])
    out = {}
    for ln in buf.getvalue().splitlines():
        parts = ln.split("\t")
        if len(parts) < 2 or parts[0] != "STATUS":
            continue
        kv = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
        if kv.get("phase") and kv.get("result"):
            out[kv["phase"]] = kv["result"]
    return out


def budget_view(session):
    """budget_tree（只读）→ {维度: {limit/used/left}}；dollars 无限额则缺省。"""
    goal = query_cmds.budget_tree(session).get("goal")
    if not goal:
        return {}
    out = {}
    for k, limit in goal["limit"].items():
        if limit is None:
            continue
        used = goal["used"].get(k, 0.0)
        out[k] = {"limit": limit, "used": used,
                  "left": round(limit - used, 6)}
    return out


def snapshot(goal_dir, tail=3):
    """账本快照 → dict（JSON 可序列化；只读，goal 目录字节不变）。"""
    s = core.Session(goal_dir)
    tl = s.rows("timeline.tsv")
    grows = s.rows("goals.tsv")
    goal = {f: grows[0][core.TABLES["goals.tsv"].index(f)]
            for f in GOAL_FIELDS} if grows else None
    return {
        "goal": goal,
        "phases": phases_status(goal_dir),
        "budget": budget_view(s),
        "events": [row_to_event(r) for r in tl[-tail:]],
        "timeline_rows": len(tl),
    }

# -*- coding: utf-8 -*-
"""wallclock · v0.7b 墙钟事件轨（轻量双轨：场景钟不动，真实墙钟以 clock-sync 入链）。

b31-34 API 断连 2h、b30 冻 7h 均靠人工对表才发现——本模块让断连窗口可机检：
mint_wall_sync 在战斗生命周期点铸一枚；detect_gaps 纯函数供 settle/审计报嫌疑窗口。"""
import datetime
import os
import re

from .phases_engine import _append_event

_WALL_RE = re.compile(r"clock-sync wall=(\S+) phase=(\S+)(?: note=(.*))?$")


def event_text(phase, note=""):
    iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = ["clock-sync wall=%s phase=%s" % (iso, phase)]
    if note:
        parts.append("note=%s" % note)
    return " ".join(parts)


def mint_wall_sync(goal_dir, phase, note=""):
    ev = event_text(phase, note)
    _append_event(goal_dir, "P-lifecycle", ev)
    return ev


def _parse(iso):
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def detect_gaps(rows, min_sec=900):
    """相邻 clock-sync 墙差>min_sec → [(event, gap_sec)]。旧账本无轨=空。"""
    walls = []
    for r in rows:
        ev = r.get("event", "") if isinstance(r, dict) else str(r)
        m = _WALL_RE.search(ev)
        if not m:
            continue
        t = _parse(m.group(1))
        if t is not None:
            walls.append((ev, t))
    out = []
    for (e1, t1), (e2, t2) in zip(walls, walls[1:]):
        gap = (t2 - t1).total_seconds()
        if gap > min_sec:
            out.append((e2, gap))
    return out

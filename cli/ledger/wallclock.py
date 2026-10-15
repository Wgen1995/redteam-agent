# -*- coding: utf-8 -*-
"""wallclock · v0.7b 墙钟事件轨（轻量双轨：场景钟不动，真实墙钟以 clock-sync 入链）。

b31-34 API 断连 2h、b30 冻 7h 均靠人工对表才发现——本模块让断连窗口可机检：
mint_wall_sync 在战斗生命周期点铸一枚；detect_gaps 纯函数供 settle/审计报嫌疑窗口。"""
import datetime
import os
import re

from .phases_engine import _append_event

_WALL_RE = re.compile(r"clock-sync wall=(\S+) phase=(\S+)(?: note=(.*))?$")


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_text(phase, note="", iso=None):
    iso = iso or _now_iso()
    parts = ["clock-sync wall=%s phase=%s" % (iso, phase)]
    if note:
        parts.append("note=%s" % note)
    return " ".join(parts)


def mint_wall_sync(goal_dir, phase, note=""):
    # 签名漂移修复（OPSEC 批收尾）：_append_event 第 4 参 ts 必填（phases_engine
    # 批次后新增）——ts 与 wall= 同刻，单源 _now_iso。
    iso = _now_iso()
    ev = event_text(phase, note, iso)
    _append_event(goal_dir, "P-lifecycle", ev, iso)
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

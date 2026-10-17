# -*- coding: utf-8 -*-
"""定向转向钩子（W5 战士 MVP · 质量律 R5）。

say 定向意图=steer：对话层（mainagent/W6）过门后以 timeline 事件行定向
注入——战士在每轮模型调用前 scan 增量消费；kill=stop 扩展（优雅停信号）。
事件词单源在本模块（writer/reader 同址）：
  warrior-steer target=<warrior-id> text=<单行文本>
  warrior-stop warrior=<warrior-id> reason=<文本>
actor=总控（对话派活先例）、phase=P3。text/reason 白空间折叠成单行（列
安全律——账本行禁换行）。
"""
from ledger.timeline import append_tl_locked, read_rows

ACTOR = "总控"
PHASE = "P3"
_STEER_PREFIX = "warrior-steer target=%s text="
_STOP_PREFIX = "warrior-stop warrior=%s reason="


def _flat(s):
    return " ".join(str(s).split())


def write_steer(goal_dir, target, text, ts):
    append_tl_locked(goal_dir, ts,
                     "warrior-steer target=%s text=%s" % (target, _flat(text)),
                     actor=ACTOR, phase=PHASE)


def write_stop(goal_dir, target, reason, ts):
    append_tl_locked(goal_dir, ts,
                     "warrior-stop warrior=%s reason=%s" % (target,
                                                            _flat(reason)),
                     actor=ACTOR, phase=PHASE)


class SteerState(object):
    """一次 scan 的增量结果：steers（文本列表）/stop_reason/seen_idx。"""

    __slots__ = ("steers", "stop_reason", "seen_idx")

    def __init__(self, steers, stop_reason, seen_idx):
        self.steers = steers
        self.stop_reason = stop_reason
        self.seen_idx = seen_idx


def scan(goal_dir, warrior_id, after_idx):
    """读 timeline 第 after_idx 行之后的定向事件（增量消费面）。"""
    steers, stop_reason = [], None
    rows = read_rows(goal_dir)
    for i, r in enumerate(rows):
        if i < after_idx or len(r) < 4:
            continue
        ev = r[3]
        sp = _STEER_PREFIX % warrior_id
        zp = _STOP_PREFIX % warrior_id
        if ev.startswith(sp):
            steers.append(ev[len(sp):])
        elif ev.startswith(zp):
            stop_reason = ev[len(zp):]
    return SteerState(steers, stop_reason, len(rows))

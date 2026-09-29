# -*- coding: utf-8 -*-
"""批次 10 T5（P2#9）：timeline 铸造单源——五工具 append_tl/EPOCH 缺省收拢于此。

契约：
- chained_row(rows, ts, actor, phase, event, revert='') 纯函数——算 (新行, prev)，
  调用方自持锁/会话时用（check_cmds 形态）；
- append_tl_locked(gd, ts, event, actor, phase, revert='') 自持 goal_lock 写回
  （guard/replay/canary/budgetctl/egress 形态）；
- ts 一律必填——EPOCH/墙钟缺省全数退役（八专家架构 P2：resume-kit 取末行
  或倒退 56 年的两类事故同源）。"""
import os

from . import core
from .schemas import TABLES
from .filelock import goal_lock

_HASH_IDX = TABLES["timeline.tsv"].index("hash")


def chained_row(rows, ts, actor, phase, event, revert=""):
    """算链新行——返回 (row, prev)；row 8 列含 hash。"""
    if not ts:
        raise TypeError("ts 必填——EPOCH/墙钟缺省已退役（批次 10 P2#9）")
    prev = rows[-1][_HASH_IDX] if rows else core.GENESIS
    wo = [ts, actor, phase, event, revert, prev, "2"]
    return [ts, actor, phase, event, revert, prev,
            core.row_hash(prev, wo), "2"], prev


def append_tl_locked(gd, ts, event, actor, phase, revert=""):
    """goal 锁包「读表→算链→写回」全程（批次 7 I-3 锁形单源化）。"""
    if not ts:
        raise TypeError("ts 必填——EPOCH/墙钟缺省已退役（批次 10 P2#9）")
    with goal_lock(gd):
        s = core.Session(gd)
        rows = [list(r) for r in s.rows("timeline.tsv")]
        row, _ = chained_row(rows, ts, actor, phase, event, revert)
        rows.append(row)
        core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)
        return row
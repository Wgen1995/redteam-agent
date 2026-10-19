# -*- coding: utf-8 -*-
"""读面总览投影(P0 T4)——GET /api/overview → 壳侧栏 badge 三数。

读法自释(零假数,纯读零 side effect;快照见 tests/readface/test_overview.py):
- battles 根 = TANYIN_HOME(缺省 ~/.tanyin)/battles——ledger.session_view
  default_battles_dir 单源,与引擎 CLI/scripts 同律。
- active_battles = 根内「执行中」仗数。执行中判读走引擎状态机单源
  webui.api_v2_tasks.tasks_view(docs/design/task-lifecycle-v1.md 12 态→界面
  七态: ARMED/RUNNING/PAUSED 归「执行中」)——本文件零第二份状态机。
- soldiers_running / pending_approvals = 上述执行中仗的当代 goal 目录
  (battle-N/G-* 末代,tasks_view 行 goal 字段)上调 ledger_reader(T2):
  soldiers_now 意图行 status 非终态计数(终态={done,rejected}——写侧链
  前置门 ledger/write_cmds「不到 {done,rejected}」同律);
  approvals_pending 清单长度直取(引擎 cleanup-checklist 同源待审)。
- 无在跑仗/无代目录/根不存在 → 0,不造数。
"""
import os

from fastapi import APIRouter

# 导入序: ledger_reader 导入即把仓根 cli/ 前上 sys.path,webui/ledger 随后可导。
from .. import ledger_reader
from ledger.session_view import default_battles_dir
from webui import api_v2_tasks

router = APIRouter(prefix="/api", tags=["overview"])

# 意图终态(写侧 write_cmds 链前置门同律;引擎未导出常量,此处引用律不复制逻辑)
_TERMINAL_INTENT = frozenset(("done", "rejected"))
# 界面七态里「执行中」标签(ARMED/RUNNING/PAUSED;api_v2_tasks.STATE_FILTERS 词表)
_RUNNING_LABEL = "执行中"


def _running_goal_dirs(battles_dir=None):
    """执行中仗 → 当代 goal 目录列表(battle-N/G-* 末代;无代目录=跳过)。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    out = []
    for b in api_v2_tasks.tasks_view(battles_dir=root)["battles"]:
        if b["state"]["label"] != _RUNNING_LABEL or not b["goal"]:
            continue
        out.append(os.path.join(root, b["battle"], b["goal"]))
    return out


def overview_doc(battles_dir=None):
    """三数投影: {active_battles, soldiers_running, pending_approvals}。"""
    goal_dirs = _running_goal_dirs(battles_dir)
    soldiers = 0
    approvals = 0
    for gd in goal_dirs:
        soldiers += sum(1 for s in ledger_reader.soldiers_now(gd)
                        if s["status"] not in _TERMINAL_INTENT)
        approvals += len(ledger_reader.approvals_pending(gd))
    return {
        "active_battles": len(goal_dirs),
        "soldiers_running": soldiers,
        "pending_approvals": approvals,
    }


@router.get("/overview")
def overview():
    """壳 badge 数据源: 只读聚合,失败面=零(根缺→三零)。"""
    return overview_doc()

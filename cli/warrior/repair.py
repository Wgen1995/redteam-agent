# -*- coding: utf-8 -*-
"""崩溃尾修复（dsh P0 采纳①，纯函数版）。

对照 docs/research/2026-10-20-dsh-orchestration-inventory.md A 表#2/§③/§⑧-1；
dsh 出处 dsh-session/lib/types/repair.js:15-77,84-189。哲学同源=**不丢不假
完成**：崩溃后对悬空执行（tool-executions.tsv 运行行无终态）做确定性合成
收尾——状态升 orphaned-not-lost + timeline 一行指导文案（重试权交模型但
给幂等判据），杜绝恢复期静默重跑（误报源）与静默丢弃（漏报源）。

纯函数律：只读盘上会话态（tool-executions.tsv + timeline），产出修复计划
（崩溃判定 + 合成收尾事件）**不落盘**；同输入同输出（可重放）。零端口
零 LLM。

接线位（等修复舰落舱后总控接 loop；loop.py/executor.py 冻结中，本件零改）：
  loop.run() 落 warrior-start 行之后:
      plan = repair.plan_repair(goal_dir)
      if plan is not None:
          io.add_tl(plan.timeline_event, plan.ts, phase="P-lifecycle")
          # repaired_rows 按 AsyncExecPool._persist 同律原子重写
          # tool-executions.tsv（executor.py 在树冻结——由总控接线落此行）
  停滞重生（StallDetected 后新进程）与断电重启同口进入。

与 dsh repair.js 对照差异声明：
  同=①悬空调用不丢不假完成，合成收尾确定性（时戳复用最后真实事件，
  repair.js:84-189 同律）；②恢复文案面向模型给幂等判据「仅幂等才重试，
  有副作用先验证外部状态」（repair.js:15-24 哲学移植）。
  异=①dsh 有 started/notStarted 两态+interrupted/forked 两因各配文案，
     我方 tool-executions.tsv 只有 running 一态——单态单文案；
  ②dsh 合成 per-call error 结果（code=TOOL_OUTCOME_UNKNOWN）直接进会话
     表面，我方产出计划由接线方落账（模型面经 timeline 指导行+回填机制）；
  ③dsh 合成事件 seq 续接事件日志，我方 timeline 为哈希链，续接由
     append_tl_locked 既有执法承担（本件不碰写面）。
"""
import os

from ledger.timeline import read_rows

#: 工具执行状态文件（AsyncExecPool 同律 7 列；executor.py:247 单源）
EXECUTIONS_NAME = "tool-executions.tsv"
EXECUTION_FIELDS = ("execution_id", "card", "status", "submitted_ts",
                    "finished_ts", "rc", "spill_path")

#: 终态集：completed/failed=正常收口；orphaned=池装载孤儿对账已标
#: （executor.py AsyncExecPool._load 单源）；orphaned-not-lost=本件合成收尾。
TERMINAL_STATUSES = ("completed", "failed", "orphaned", "orphaned-not-lost")

#: 修复事件行前缀（幂等判定锚）
REPAIR_EVENT_PREFIX = "warrior-repair"

#: 幂等重试指导文案（dsh repair.js:15-24 哲学：判据交模型，不盲重试）
RETRY_GUIDANCE = "结果未知,仅幂等才重试,有副作用先验证外部状态"


class RepairPlan(object):
    """崩溃尾修复计划：崩溃判定 + 合成收尾事件（纯数据，接线方落账）。

    crashed=确有未收口悬空；dangling_ids=待修执行 id（文件序）；
    repaired_rows=全量状态行（悬空升 orphaned-not-lost，终态原样）；
    timeline_event=合成收尾事件一行（含全部悬空 id+幂等判据）；
    ts=确定性时戳（最后真实事件时戳，无则最早悬空提交钟）。
    """

    __slots__ = ("crashed", "dangling_ids", "repaired_rows",
                 "timeline_event", "ts")

    def __init__(self, crashed, dangling_ids, repaired_rows,
                 timeline_event, ts):
        self.crashed = bool(crashed)
        self.dangling_ids = list(dangling_ids)
        self.repaired_rows = list(repaired_rows)
        self.timeline_event = timeline_event
        self.ts = ts


def read_executions(goal_dir):
    """读工具执行状态行（7 列 TSV → dict 列表；列数坏行跳过）。

    与 AsyncExecPool._load 同解析律但不做孤儿改写——本件只看，判定权在
    plan_repair（单态源：盘上文件）。
    """
    path = os.path.join(goal_dir, EXECUTIONS_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return []
    rows = []
    for ln in lines:
        if not ln:
            continue
        parts = ln.split("\t")
        if len(parts) != len(EXECUTION_FIELDS):
            continue                      # 列数坏行跳过（fail-soft 解析）
        rows.append(dict(zip(EXECUTION_FIELDS, parts)))
    return rows


def _prior_repair_lines(timeline_rows):
    """既有 warrior-repair 行文本集（幂等锚：行内点名即修过）。"""
    return [r[3] for r in timeline_rows
            if len(r) > 3 and r[3].startswith(REPAIR_EVENT_PREFIX)]


def plan_repair(goal_dir):
    """崩溃判定+合成收尾计划（纯读盘，零写）。

    返回 RepairPlan；无悬空/无状态文件/该批悬空已修过 → None。
    幂等律：timeline 已有 warrior-repair 行点名覆盖的 id 不重开账
    （其状态行仍在 repaired_rows 中升级——状态面幂等安全）。
    """
    rows = read_executions(goal_dir)
    if not rows:
        return None
    non_terminal = [r for r in rows
                    if r["status"] not in TERMINAL_STATUSES]
    if not non_terminal:
        return None
    try:
        timeline_rows = read_rows(goal_dir)
    except Exception:                     # noqa: BLE001 —— 撕裂态 fail-closed
        timeline_rows = []
    covered_lines = _prior_repair_lines(timeline_rows)
    dangling = [r for r in non_terminal
                if not any(r["execution_id"] in line
                           for line in covered_lines)]
    if not dangling:
        return None
    last_ts = timeline_rows[-1][0] if timeline_rows else ""
    ts = last_ts or min((r["submitted_ts"] for r in non_terminal
                         if r["submitted_ts"]), default="")
    repaired = []
    for r in rows:
        if r["status"] in TERMINAL_STATUSES:
            repaired.append(dict(r))
        else:
            r2 = dict(r)
            r2["status"] = "orphaned-not-lost"
            r2["finished_ts"] = r2["finished_ts"] or ts
            repaired.append(r2)           # rc 留空=结果未知（不假完成）
    ids = ",".join(r["execution_id"] for r in dangling)
    event = ("%s verdict=orphaned-not-lost dangling=%d ids=%s 指导=%s"
             % (REPAIR_EVENT_PREFIX, len(dangling), ids, RETRY_GUIDANCE))
    return RepairPlan(True, [r["execution_id"] for r in dangling],
                      repaired, event, ts)

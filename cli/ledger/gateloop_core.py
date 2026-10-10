# -*- coding: utf-8 -*-
"""gateloop 纯函数核（b11 T1）——python 门循环的计算面。

编排见 cli/tanyin-gateloop；本模块零依赖可单测：
  PHASE_SEQ     驱动门序列（=runner 完成判据同口径 P0-P4）
  build_gate_prompt  门提示构造（任务书全文+门范围令+禁推进下一门）
  gate_argv     tanyin-phases gate 参数形（--phase P 契约）
"""

PHASE_SEQ = ["P0", "P1", "P2", "P3", "P4"]

GATE_SCOPE_LAW = (
    "【本回合范围令】当前推进到 {phase} 门。详令按仓根 phases/{phase}.md 执行。"
    "完成本门并通过门禁（tanyin-phases gate --goal-dir <会话目录> --phase {phase}）即止，"
    "禁止推进到下一门——下一门由引擎另行发令。"
)


def build_gate_prompt(mission_text, phase):
    """门提示=任务书全文+范围令（python 掌推进，战士每门一回合）。"""
    if phase not in PHASE_SEQ:
        raise ValueError("phase not in driven seq: %r" % phase)
    law = GATE_SCOPE_LAW.format(phase=phase)
    resume = ""
    if phase != "P0":
        resume = (
            "\n【续跑】本任务状态全落盘于账本（不依赖会话记忆）："
            "先走恢复协议（verify-chain -> state-rebuild -> resume-kit），"
            "再从本门继续，勿重复已落账条目。\n"
        )
    return mission_text.rstrip() + "\n\n" + resume + law


def gate_argv(goal_dir, phase, ts):
    """tanyin-phases gate 参数形（契约实证：--goal-dir 空格形+--phase 等号形+
    --timestamp 等号形必填——b26 两度失明的教训）。"""
    if phase not in PHASE_SEQ:
        raise ValueError("phase not in driven seq: %r" % phase)
    return ["gate", "--goal-dir", goal_dir, "--phase=" + phase, "--timestamp=" + ts]


def next_phase(done_list):
    """从已过门列表推下一门；P4 已过 → None（驱动完成）。"""
    done = [p for p in done_list if p in PHASE_SEQ]
    nxt = PHASE_SEQ[len(done):len(done) + 1]
    return nxt[0] if nxt else None


def should_full_gate(first, proc_exited, soft_stalled, status_pass):
    """v0.5a F2（架构/工程项）：全量门只在该跑的时机跑。

    轮询（每 tick）一律走只读 status；全量 gate（有副作用：断言+可能铸事件）
    仅限：首次进入该门 / 战士进程已退出 / soft-stall（战士疑似本回合干完）。
    status 已 PASS 直接短路（连全量也不必跑——账本已载过门事实）。"""
    if status_pass:
        return False
    return first or proc_exited or soft_stalled

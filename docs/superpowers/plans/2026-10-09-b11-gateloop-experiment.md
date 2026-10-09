# b11 · v0.4 门循环对照实验（gateloop vs runner）

> 日期：2026-10-09 ｜ 状态：已批准（用户"开"）｜ 前置：b10 ｜ 蓝图：architecture-map-v3 路线图 v0.4

## 实验问题
AI 自律推进（SKILL 总控自驱九门）vs Python 门循环驱动（python 掌推进节奏，战士每门一回合）——同靶场同战士同战书，哪个更优？

## 设计
- **臂A（基线）**= b23 数据（BRIEF-template 30面/agent boot/runner 驱动/G-r24，0.66=稳定最佳）。同日重跑可选：若臂B 与基线差 |Δ|<0.05 难裁决，补跑臂A 新场破平局。
- **臂B（实验）**= b26（G-r27）：init 完全同参（同战书同八问同 boot=agent——P0 内容仍战士做，只是推进权移交 python）+ 新驱动 `cli/tanyin-gateloop`：
  - 门序列 P0→P1→P2→P3→P4（=runner 完成判据同口径；P5/P5.5/P6 同 b23 流程后置）
  - 每门：gate --phase PX rc==0 则 SKIP；否则构造门提示（任务书全文+"本回合只推 P{X}，详令 phases/P{X}.md，过门即止禁推进下一门"）→ launch（同 ISOLATION_ENV/进程组）→ 轮询（tick 自适应+soft 观察+hard 击杀+带账重启本门）→ 过门 kill_group → 下一门
  - 复用 b10 watchdog 计算核+runner 的 launch/kill_group/log_event（importlib 载入，单一真源）
- **度量（三项裁决，b24 式裁决文化）**：①score=eval_range_recall v7 ②恢复成本=restarts/stalls/BACKOFF 计数 ③token 成本≈主日志字节+LLM 调用数（opencode run 每门一进程，调用数=Σ每门会话轮）

## 任务
- T0 计划入册
- T1 纯函数核 cli/ledger/gateloop_core.py + 单测（先红）：build_gate_prompt（含任务书+门号+禁推进）/phase 序列/gate 命令参数形
- T2 cli/tanyin-gateloop 编排 + 单测（monkeypatch 假 rc 序列推演门推进状态机）
- T3 b26 init（同 b23 参数）→ gateloop 点火（后台 job）
- T4 盯战 → settle → RT-0024 裁决 → 金样 G-r27 钉测 → HANDOFF/蓝图翻绿 → push

## 风险与诚实条款
- 单样本噪声（RT-0023 教训）：结论只写"本场裁决"不写"定论"；平局即明说
- b23 基线时间漂移（模型/环境随时间变）：caveat 必写；必要时臂A 补跑
- P5.5 人工签发在靶场模式的处理两臂一致（同 b23 后置流程）——驱动差异只存在于 P0-P4 推进权

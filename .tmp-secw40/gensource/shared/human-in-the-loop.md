# 人工介入设计（全自动红线权威）

> 依据：设计 28 号 §7.1。本文件定义"什么时候问人、什么时候禁止问人"。目标：整个 run 至多一次人工提问，默认全自动挖掘。

## 1. 提问白名单（仅两类，整个 run 至多一次）

| 情形 | 问什么 | 不回答时 |
|---|---|---|
| 审计开始前 | 授权范围确认（source_path 是否本次授权目标） | 停止，不猜测 |
| blocked 两情形之一（不存在"预算"这个概念，覆盖率不可谈判；上下文/会话边界耗尽属于自动续跑范畴，不消耗提问名额、不需要问用户） | ①缺关键输入（路径/权限缺失）②动态验证一次性授权 | 保持 blocked，写恢复入口，不编造答案 |

> **提问计数器（v0.3.7）**：每次提问前必须先写 `run-state.md` 的 `human_question_budget` 计数器（`questions` 追加一条记录、`consumed` 加 1）并核对 `consumed < total`，否则禁止提问；整个 run `total=1`。

## 2. 红线禁令（违反即协议缺陷，写入 defects 清单）

1. **禁止中途进度汇报式提问**："已找到 N 个候选，是否继续""是否进入下一阶段""是否继续审计"等一律禁止。进度只写 `live_findings_index.md` 供用户自查。
2. **禁止逐阶段完成确认**：阶段间转移不需要用户点头，按 work-graph 路由自动执行。
3. **禁止把"可以继续"类问题当作阻塞门**：协议要求继续时直接继续。
4. **禁止以历史授权推断本次授权**：动态验证/写目标树等授权必须本次显式给出。

## 3. 威胁语境确认（非阻塞）

阶段0 产出威胁语境后：展示关键业务假设（要害资产/信任边界/攻击者画像/暴露面）→ 直接以保守假设继续（写 `confirmation_policy=conservative_continue` 且 `user_confirmed=conservative_assumption_applied`；两字段取值关系：`confirmation_policy=conservative_continue` 时 `user_confirmed=conservative_assumption_applied`，两值均已登记于 [`../contracts/enum-registry.md`](../contracts/enum-registry.md)）→ 记录"未等用户确认即采用的保守假设清单"及其影响范围，写入报告缺口披露。

## 4. 知识晋升批准（不在主序列）

knowledge-evolution（#16）的知识晋升需要人工批准——该能力周期触发、不在单次审计关键路径上，其批准请求不算入"至多一次提问"预算（非主序列）。

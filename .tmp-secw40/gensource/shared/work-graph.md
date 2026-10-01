# Work Graph（跨能力路由唯一权威）

> 依据：设计 28 号 §2.1。本文件只定义能力之间的控制流；能力内部逻辑由各自 SKILL 定义。发现冲突时以本文件为准。主链 8 行内，不维护第二份完整转换表。

## 主序列转换表

| 当前 | 事件/终态 | 下一动作 |
|---|---|---|
| 阶段0 scope-and-context | 三清单冻结 + 威胁语境保守继续 + `stage_result=completed` | 进入阶段1 |
| 阶段1 candidate-discovery | 阶段1 完成 = worklist 中 inventory+neighborhood+hypothesis 卡均非 unchecked/待唤醒 blocked，且 L2 已跑 | 进入阶段2 |
| 阶段1 candidate-discovery | 零候选仍进阶段3，但必须先 L2（inventory+neighborhood+hypothesis 均非 unchecked/待唤醒 blocked） | 写各下游零输入终态（阶段2 写 `stage_result=not_applicable` 且 `input_count=0`/`records=[]`/非空 `zero_input_reason`），进入阶段3 |
| 阶段2 verification-and-rating | `stage_result=completed` | 进入阶段3 |
| 阶段3 report-delivery | `stage_result=completed` 且 report 完成硬门通过 | run 写 `completed` |
| 任意阶段 | `stage_result=partial` | 补完未完范围（remaining 清单），不重跑已完成分片 |
| 任意阶段 | `stage_result=partial` 且 `gate_result=blocked`（缺人工决定/权限/关键输入） | 停；写恢复入口；至多一次提问（见 human-in-the-loop.md） |
| 阶段1/2 | 执行中发现新线索（新 sink/source/文件） | 追加检查点到账本并重新闭合，不回退已完成结论 |

## 伴生能力路由（事件驱动，不在主序列）

| 触发事件 | 路由目标 |
|---|---|
| `run_mode=incremental` 或复扫 | lifecycle-governance（增量预处理后返回对应主阶段） |
| 依赖漏洞查询/吃SAST结果/导出格式/issue tracker 写入请求 | external-tool-integration（导入信号返回阶段1；导出/写入返回阶段3） |
| 审计周期结束复盘 | knowledge-evolution（需人工批准晋升，不进入漏洞判断主链） |
| 用户显式请求独立 PoC / 独立修复指导 | exploit-proof / remediation-guidance（默认并入 finding 小节，不单独执行） |

## 出口纪律

- 每次阶段转移前，Gate-1 对账（quality-gates.md 七等式）必须通过；对账由宿主 shell 命令执行（contracts/host-reconciliation-commands.md），不是 LLM 自报；
- 零候选也必须先跑完 L2（工作集 inventory+neighborhood+hypothesis 均非 unchecked/待唤醒 blocked）后才能进阶段3；
- 阶段3 完成后，run 写 `completed` 前必须核对：所有适用阶段 `stage_result=completed` 或合法 `not_applicable`，七等式全成立，failed 清单为空或已列入报告。

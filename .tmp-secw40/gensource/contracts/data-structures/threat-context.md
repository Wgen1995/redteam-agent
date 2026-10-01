# 威胁语境结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义 #1 威胁语境文档的稳定字段形状，作为后续范围、候选发现、验证、报告与伴生能力的共同审计前提。  
**生产者**：#1 `scope-and-context`。  
**消费者**：#2-#9、#16、#18，以及报告和外部导出消费方。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。消费方必须保留未知字段，不得改写本结构。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | #1 `scope-and-context` | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前产物完成程度。 |
| `version` | `string` | 是 | #1 `scope-and-context` | 所有消费者 | 语义版本字符串，格式 `MAJOR.MINOR.PATCH`，如 `1.0.0` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | #1 `scope-and-context` | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `overview` | `string` | 是 | #1 `scope-and-context` | #2-#9、#16、#18 | 非空；覆盖系统类型、使用者、要害资产 | 系统用途和关键资产概述。 |
| `threat_model_trust_boundaries_assumptions` | `string` | 是 | #1 `scope-and-context` | #2-#9、#16、#18 | 非空；明确威胁模型、信任边界和假设 | 后续判断共同前提。 |
| `attack_surface_protections_attacker_story` | `string` | 是 | #1 `scope-and-context` | #2-#9、#16、#18 | 非空；包含攻击面、已有防护、现实攻击者故事；适用时说明风险为何不重要 | 为适用性与覆盖投影提供依据。 |
| `severity_calibration` | `array&lt;object&gt;` | 是 | #1 `scope-and-context` | #3-#9、#16、#18 | 恰含枚举注册表 `final_severity` 中的 `critical`、`high`、`medium`、`low` 四项；每项最少为 `{level: string, examples: string[]}`，`examples` 非空 | 仓库专属严重度标尺，不是候选最终定级。 |
| `input_controllability` | `array&lt;object&gt;` | 是 | #1 `scope-and-context` | #2-#9、#16、#18 | 每项最少为 `{input_ref: string, control_class: string, evidence_refs: string[]}`；`control_class` 见枚举注册表 [`input_control_class`](../enum-registry.md#input_control_class) | 输入控制权分类。 |
| `production_vs_test_scope` | `object` | 是 | #1 `scope-and-context` | #2-#9、#16、#18 | 最少为 `{production_runtime_paths: string[], test_demo_dev_paths: string[], classification_basis: string}`；路径不可仅凭名称分类 | 区分生产运行时代码与测试/demo/开发工具。 |
| `generation_basis` | `array&lt;object&gt;` | 是 | #1 `scope-and-context` | 所有下游与报告层 | 每项最少为 `{source_type: string, source_ref: string, independently_verified: boolean, evidence_refs: string[]}`；`source_type` 使用 [`generation_basis_kind`](../enum-registry.md#generation_basis_kind)；每项须经代码或配置证据独立核实，目标自称不得直接作为权威证据 | 统一记录文档、代码信号及语言/框架探测来源和独立核实情况。 |
| `user_confirmed` | `string` | 是 | #1 `scope-and-context` | 所有下游与报告层 | 见枚举注册表 `user_confirmed` | 非阻塞运行默认 `conservative_assumption_applied`（配合 `confirmation_policy=conservative_continue`）；交互模式可为 `confirmed`/`rejected`；不得默认 `blocked_pending_user_input` 阻塞等待。 |

`stage_result=completed` 不代表 `user_confirmed=confirmed`；非交互运行默认保守继续，写 `confirmation_policy=conservative_continue` 且 `user_confirmed=conservative_assumption_applied`（语义与 [`../../skills/scope-and-context/SKILL.md`](../../skills/scope-and-context/SKILL.md) 对齐），不得默认 `blocked_pending_user_input` 阻塞等待。

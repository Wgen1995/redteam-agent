# 知识演进结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义 #16 知识晋升、弃用提议、人工决策、范围归属和证据历史的输入/输出形状。  
**生产者**：调用方与人工授权方写入调用输入；#16 `knowledge-evolution` 只写本阶段提议、执行结果、状态和历史字段。  
**消费者**：人工决策方、知识库写入步骤、#2/#3/#4/#7 等知识库消费方。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。

每次输出必须完整携带调用输入快照：`candidate_pool`、`knowledge_base_snapshot`、`installation_scope`和`human_decision`原样保留；提供了`deprecation_signal`时也原样保留。#16不得改写、裁剪或重排这些字段。阶段A的`human_decision`原样为空数组，阶段B原样携带人工授权方写入的决定数组。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | #16 `knowledge-evolution` | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前知识演进产物完成程度。 |
| `version` | `string` | 是 | #16 `knowledge-evolution` | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | #16 `knowledge-evolution` | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `candidate_pool` | `array&lt;object&gt;` | 是 | 调用方在调用前写入；#16 只读 | 人工决策方、知识库写入步骤 | 每项必须为 `{source_audit_id: string, candidate: object}`；`source_audit_id` 由调用方/编排上下文写入，用于独立场景计数；`candidate` 必须完整满足[`candidate-finding.md`](candidate-finding.md)，不得增加供#16使用的预判信号。#16以`candidate.verification_verdict.value=confirmed`确认状态，将candidate的可泛化语义与`knowledge_base_snapshot`独立比对以判定是否未匹配，并仅从`candidate.verification_baseline`、`candidate.candidate_specific_checklist`等已登记验证字段中实际存在的`evidence_refs`提取证据引用 | 跨审计累积的包装候选输入快照。 |
| `knowledge_base_snapshot` | `array&lt;object&gt;` | 是 | 调用方在调用前写入；#16 只读 | 人工决策方 | 每项最少为 `{knowledge_entry_id: string, knowledge_entry_status: string, hit_count: integer, miss_count: integer, evidence_refs: string[]}`；`knowledge_entry_status` 见枚举注册表同名枚举 | 当前知识库状态输入。 |
| `installation_scope` | `object` | 是 | 调用方在调用前写入；#16 只读 | 人工决策方、知识库写入步骤 | 最少为 `{scope_type: string, scope_id: string, intentional_sharing_configured: boolean}`；`scope_type` 见枚举注册表 `installation_scope_type`；未显式共享时不得分配共享范围 | 部署及隔离边界输入。 |
| `human_decision` | `array&lt;object&gt;` | 是 | 人工授权方写入；#16 只读 | 所有后续消费者 | 每项最少为 `{proposal_id: string, decision: string, reason: string \| null, actor: string, date: date}`；`proposal_id` 是决策记录主键且在数组内唯一，`decision` 见枚举注册表 `human_decision`，`rejected`/`deferred` 时 `reason` 非空，`approved` 时可为 null。阶段 A 尚无人工决定时必须为空数组；阶段 B 收到一项或多项决定后逐项记录 | 人工决策的唯一权威记录，不得由系统伪造或自动批准。 |
| `deprecation_signal` | `array&lt;object&gt;` | 否 | 调用方在调用前写入；#16 只读 | 人工决策方 | 每项最少为 `{knowledge_entry_id: string, signal_type: string, occurrence_count: integer, evidence_refs: string[]}`；`signal_type` 见枚举注册表 `deprecation_signal_type` | 过时或误报信号输入。 |
| `promotion_proposals` | `array&lt;object&gt;` | 是 | #16 `knowledge-evolution` | 人工决策方、知识库写入步骤 | 每项最少为 `{proposal_id: string, candidate_content: string, scenario_summaries: string[], verification_evidence_refs: string[], threshold_calculation: string, proposed_scope: string}`；`proposed_scope` 见枚举注册表 `installation_scope_type`；同一可泛化语义必须来自至少 2 个不同`source_audit_id`，且参与计数的每个`candidate.verification_verdict.value`均为`confirmed`。`scenario_summaries`和`verification_evidence_refs`由#16分别基于包装上下文和candidate既有验证字段派生，仅作为提议输出 | 晋升提议，不等于已写入。 |
| `promotion_decisions` | `array&lt;object&gt;` | 条件必填 | #16 仅在消费真实 `human_decision` 后写入 | 所有后续消费者 | 收到对应人工决定时必填；每项最少为 `{decision_ref: string, resulting_entry_id: string \| null, resulting_status: string \| null}`；`decision_ref` 必须等于顶层 `human_decision` 中对应决策记录的 `proposal_id`，不生成 `decision_id`；其 `decision` 引用枚举注册表 `human_decision`。仅 `decision=approved` 时实际写入知识库，且 `resulting_entry_id` 非空、`resulting_status=active`；`rejected`/`deferred` 只记录决定结果、不写知识库，两个结果字段均为 null | 晋升执行结果，不重复承载人工决定。 |
| `deprecation_proposals` | `array&lt;object&gt;` | 是 | #16 `knowledge-evolution` | 人工决策方、知识库写入步骤 | 每项最少为 `{proposal_id: string, knowledge_entry_id: string, trigger: string, proposed_status: string, reason: string}`；`proposed_status` 引用枚举注册表 `knowledge_entry_status` 且仅可为 `deprecated`/`archived` | 状态标注提议，禁止物理删除。 |
| `deprecation_decisions` | `array&lt;object&gt;` | 条件必填 | #16 仅在消费真实 `human_decision` 后写入 | 所有后续消费者 | 收到对应人工决定时必填；每项最少为 `{decision_ref: string, resulting_status: string}`；`decision_ref` 必须等于顶层 `human_decision` 中对应决策记录的 `proposal_id`，不生成 `decision_id`；其 `decision` 引用枚举注册表 `human_decision`；`resulting_status` 引用枚举注册表 `knowledge_entry_status`。仅 `decision=approved` 时实际写入状态变更；`rejected`/`deferred` 只记录决定结果、不写知识库，`resulting_status` 保持原状态 | 过时处理执行结果，不重复承载人工决定。 |
| `scope_assignment` | `array&lt;object&gt;` | 是 | #16 `knowledge-evolution` | 知识库消费方 | 每项最少为 `{knowledge_entry_id: string, assigned_scope: string, scope_id: string, basis: string}`；`assigned_scope` 见枚举注册表 `installation_scope_type`；仅批准写入的条目可出现；共享范围要求显式共享配置 | 条目最终归属范围。 |
| `evidence_strength_disclosure` | `string` | 是 | #16 `knowledge-evolution` | 所有消费者 | 非空；必须披露自演进机制“架构上存在、运营上未经证明”的证据局限 | 防止夸大知识晋升成熟度。 |
| `knowledge_entry_states` | `array&lt;object&gt;` | 是 | #16 `knowledge-evolution` | 所有知识库消费方 | 每项最少为 `{knowledge_entry_id: string, status: string, evidence_history_ref: string}`；`knowledge_entry_id` 非空且在数组内唯一，`status` 见枚举注册表 `knowledge_entry_status`，`evidence_history_ref` 必须等于同一 `knowledge_entry_id` 的某条 `knowledge_evidence_history.history_id`；新条目状态为 `active`，改变为 `deprecated`/`archived` 必须有对应 `human_decision[].decision=approved` | 可机械关联到具体知识条目的当前状态。 |
| `knowledge_evidence_history` | `array&lt;object&gt;` | 是 | #16 `knowledge-evolution` | 所有其他阶段 | 仅追加；每项最少为 `{history_id: string, knowledge_entry_id: string, recorded_at: datetime, event_type: string, evidence_refs: string[], actor: string, note: string}`；`history_id` 非空且唯一，禁止改写、重排或删除既有条目 | 知识条目证据和决策历史。 |

所有知识状态改变和实际写入都必须由顶层 `human_decision` 中的 `approved` 决定授权；`promotion_decisions` 与 `deprecation_decisions` 仅通过 `decision_ref` 引用该唯一记录并记录执行结果，不得复制决定、理由、actor 或日期。`rejected` 与 `deferred` 只记录结果，不改变条目状态。历史证据只能追加，即使当前阶段产物遵循覆盖式最终态，也必须完整携带既有历史条目。

## 两阶段调用

1. **阶段 A（生成提议）**：#16 消费候选池、知识快照、安装范围和弃用信号，生成 `promotion_proposals`/`deprecation_proposals`。此时 `human_decision=[]`，`promotion_decisions` 与 `deprecation_decisions` 不必填，且不得写知识库。
2. **阶段 B（消费决定）**：人工授权方针对 proposal 写入 `human_decision` 决策记录后，#16 只读消费这些记录，并仅为收到决定的 proposal 写对应 decisions。只有 `approved` 执行知识库写入；`rejected`/`deferred` 仅留痕，不写知识库。

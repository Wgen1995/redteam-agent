# 生命周期台账结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义 #9/#19 对confirmed、存在活攻击面且非informational的finding（包括政策忽略`ignore`）的跨扫描身份、状态处置、复验和覆盖差异记录。  
**生产者**：#9/#19 `lifecycle-governance`。  
**消费者**：#8、#16、#18、后续复扫与人工治理方。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | #9/#19 `lifecycle-governance` | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前台账产物完成程度。 |
| `version` | `string` | 是 | #9/#19 `lifecycle-governance` | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | #9/#19 `lifecycle-governance` | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `finding_id` | `string` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18、后续复扫 | 仅`verification_verdict.value=confirmed`、存在活攻击面且`final_severity!=informational`的记录登记；值必须等于不可变`candidate_id`。`ignore`必须登记并显式处置；informational代码卫生candidate不进入本台账 | finding 语境的等值别名，不产生新 ID。 |
| `finding_fingerprint` | `string` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18、后续复扫 | 非空；**v1 算法**：由以下七组分量的确定性序列化生成——①`unified_semantic_refs`（统一漏洞语义）②`invariant`（不变量/根因语义，取 `root_cause_group_id` 的语义摘要而非 ID 本身）③`entry`（入口类型，取 `entry_ref` 的本体类型）④`sink`（Sink 类型，取 `sink_ref` 的本体类型）⑤`path_edges`（路径边的边类型序列，取 `cross_boundary_path` 各跳的 `edge_kind` 有序列表）⑥`trust_boundary`（信任边界，取 `ontology_trace.trust_boundary_refs`）⑦`asset`（资产，取 `ontology_trace.asset_refs`）。**不含文件路径和行号**——这些在重构后不稳定，不适合作为指纹分量。分组内分量无序，分组间按上述①-⑦顺序排列。用于缩小跨扫描匹配候选集，不替代 `finding_id` | 用于缩小跨扫描匹配候选集，不替代 `finding_id`。重构导致指纹变化时仍须经过语义同根因判断。 |
| `lifecycle_status` | `string` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 见枚举注册表 `lifecycle_status` | finding 当前生命周期状态。 |
| `disposition` | `object` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 首次进入注册表 [`lifecycle_status`](../enum-registry.md#lifecycle_status) 的抑制态子集时必须获得人工授权，并同时含非空 `actor: string`、`reason: string`、`date: date`、`review_date: date`，四项全必填；其他状态可为空对象 | 抑制态人工处置留痕。critical finding 不得自动进入抑制态。 |
| `verification_result` | `object` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 进入注册表 [`lifecycle_status`](../enum-registry.md#lifecycle_status) 的修复态子集时必填，最少为 `{verification_mode: string, result: string, checked_at: datetime, evidence_refs: string[]}`；`result` 见枚举注册表 `lifecycle_verification_result`。`verification_mode=inferred`仅表示独立静态复核确认修复后证据链已断，可产出`result=verified_fixed`，但生命周期初始状态只能为`fixed_unverified`；只有后续`verification_mode=executed`真实动态复验且`result=verified_fixed`可支撑`fixed_verified`。静态证据不足时使用`result=inconclusive` | 修复类状态的独立复验记录。 |
| `identity_match` | `object` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 最少为 `{historical_finding_id: string \| null, fingerprint_prefilter: string, semantic_same_root_cause: boolean \| null, rationale: string}`；首次或无匹配时 ID 为 null 并说明原因 | 两段式跨扫描身份判断。 |
| `coverage_diff` | `object` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 最少为 `{previous_coverage: number \| null, current_coverage: number \| null, delta: number \| null, decreased: boolean \| null, warning: string \| null}`；无法比较时数值为 null 并说明 | 防止发现减少实际源于覆盖下降。 |
| `baseline_delta` | `object` | 是 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 最少为 `{added: integer, resolved: integer, unchanged: integer, updated: integer}`；均为非负整数 | 本轮相对历史基线的计数汇总。 |
| `baseline_revision` | `string` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 非空；`run_mode=incremental` 时必填，记录上次全量/增量审计的源码 revision | 增量运行的基线 revision。 |
| `current_revision` | `string` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | 非空；`run_mode=incremental` 时必填，记录本次审计的源码 revision | 增量运行的当前 revision。 |
| `change_manifest` | `array<object>` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | `run_mode=incremental` 时必填；每项最少为 `{path: string, change_kind: string, evidence_refs: string[]}`；`change_kind` 取值 `added`/`modified`/`deleted`；无变化时写空数组 | 基于 baseline 与 current revision 差异的变化清单。 |
| `staleness_triggers` | `array<object>` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | `run_mode=incremental` 时必填；每项最少为 `{scope_ref: string, trigger_kind: string, rationale: string, evidence_refs: string[]}`；`trigger_kind` 取值 `control_flow_change`（新调用者/路由使未修改函数重新可达）/`new_knowledge_pattern`（#16新增知识模式未曾对照）/`threat_context_change`（#1威胁语境变化）；无触发时写空数组 | 陈旧触发记录——即使代码本地内容未变化，仍可能因控制流/知识/语境变化而不可安全复用。 |
| `recheck_scope` | `array<string>` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | `run_mode=incremental` 时必填；本次必须重新核查的范围引用列表；无时写空数组 | 重新核查范围。Source 变化向下游扩展，Sink 变化反查调用者，新调用者/路由使未修改函数重新可达时必须重查。 |
| `reuse_scope` | `array<object>` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | `run_mode=incremental` 时必填；每项最少为 `{scope_ref: string, reused_from_revision: string, rationale: string}`；无时写空数组 | 直接复用上次结论的范围，每项必须显式标注"本次未重新核查"及复用依据。 |
| `skip_scope` | `array<object>` | 条件必填 | #9/#19 `lifecycle-governance` | #8、#16、#18 | `run_mode=incremental` 时必填；每项最少为 `{scope_ref: string, skip_reason: string}`；无时写空数组 | 本次跳过的范围及跳过理由（如"该范围在 baseline 与 current revision 间无变化且无陈旧触发"）。 |

`finding_fingerprint` 只服务匹配预筛选；重构导致指纹变化时仍须经过语义同根因判断，任何情况下均不得借指纹生成第二套主身份。v1 算法不含文件路径和行号，分量取自语义/不变量/入口/Sink/路径边/信任边界/资产——这些在重构后相对稳定。

## 台账准入与替代持久化

1. `confirmed`只是验证终态，不是台账准入的充分条件。只有同时存在活攻击面且`final_severity!=informational`时，该记录才是finding并进入本台账。
2. `final_severity=ignore`表示活攻击路径成立但按政策忽略，仍是finding，必须进入本台账并获得显式生命周期处置；“忽略”不得实现为删除或跳过状态机。
3. `confirmed+informational`是candidate/code-hygiene item，不得产生`finding_id`或`lifecycle_status`。其完整历史替代持久化在[`candidate-finding.md`](candidate-finding.md)累积记录和#4/#5完整产物中，由#8展示，并在后续复扫重新进入#3/#4；未进入本台账不表示可丢弃。

## 抑制状态维持边界

1. 首次进入 `risk_accepted`、`false_positive`、`duplicate` 或 `wont_fix` 必须由人类明确授权，且 `disposition` 的 `actor`、`reason`、`date`、`review_date` 四字段全部有效；自动判定不得创建新的抑制处置。
2. 对历史基线中已经处于上述抑制态的 finding，只有当前 `confidence_score.value &gt; 8.5`（量纲为 0-10，等价于 &gt;85%）且 `final_severity != critical` 同时成立时，才允许自动维持原抑制状态。`confidence_score` 必须完整复用 [`candidate-finding.md`](candidate-finding.md) 的同名对象，不得降格为数值；自动维持不得改写原人工处置事实。
3. 任一条件不满足时，必须重新呈报给人类处置，不得自动延续抑制；`final_severity=critical` 始终要求人工处理。
4. 自动维持的抑制项仍须纳入定期人工抽样复核。具体频率由运营过程决定，本契约不规定固定周期。

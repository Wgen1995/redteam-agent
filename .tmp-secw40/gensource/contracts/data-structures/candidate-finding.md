# Candidate/Finding 累积结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义同一 candidate 从 #3 创建，经 #4/#5 验证定级、#6 PoC、#7 修复指导到 #8 报告投影的分段累积结构。  
**生产者**：#3、#4/#5、#6、#7、#8 各自仅写所属字段段；#9 仅在生命周期台账登记 `finding_id`。  
**消费者**：#4-#9、#16、#18、报告和外部导出消费方。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。条件必填字段不能以空值冒充完成；不适用时按约束省略或显式记录不适用原因。

## 身份与语义边界

- `candidate_id` 由 #3 一次性创建，此后不可变；采用确定性派生 `C-{sink_seq}-{source_seq}-{sig8}`（见 #3 字段表），不依赖运行时刻、不使用发现顺序，同 revision 跨 run 不变。
- `verification_verdict.value=confirmed` 只是验证终态，表示当前记录的代码事实或风险主张已获证据确认；它本身不等于 finding。可利用漏洞要求六项适用基线全部 `pass`；无活攻击面的代码事实允许 `reachable`/`exploitable`/`impact_there` 为 `fail`/`not_applicable`，但必须 `final_severity=informational`。
- 只有 confirmed、存在活攻击面且 `final_severity!=informational` 的记录才进入 finding 语境和 #9；`finding_id=candidate_id`，仅由 #9 登记，不生成新 ID。`final_severity=ignore`表示有活路径的政策忽略finding，仍进入#9显式处置。
- `confirmed+informational` 是已确认代码卫生candidate/code-hygiene item，不称finding、不产生`finding_id`、不进入PoC、主动漏洞修复或#9。其替代持久化通道是本candidate累积结构与#4/#5完整产物，#8完整展示，后续复扫重新送入#3/#4；不得因未进入#9而删除历史。
- #8 始终以 `candidate_id` 投影，仅对finding只读显示已存在的 #9 `finding_id`别名。
- `unconfirmed` 与 `refuted` 记录仍是 candidate，不得称为 finding，也不得产生 `finding_id`。

## 共享状态与 #3 候选发现字段

## v0.3.7 增补（单一候选账本 + 三记录闭包，设计 36 号 §2）

- **单一候选账本冻结规则**：candidates.tsv 是候选唯一持久物；discovery 字段（candidate_id/location/sink_ref/entry_ref/severity_hypothesis_initial/root_cause_group_id/discovery_reasoning_note/created_at）创建后**冻结**，下游阶段只增列（verification/report 字段）或只读，**禁止改行、禁止回喂、禁止重排**；原子替换（temp+mv）。`description`/`evidence` 等为 discovery 记录（簇结论）内字段，不在 candidates.tsv 顶层列。
- **每候选三记录闭包**：①discovery 记录（阶段1：簇结论引用 cluster_ref + 证据链五段引用）②validation 记录（阶段2：verification-summary 对应段引用）③report 投影记录（阶段3：findings/V{N}.md + machine-fields 行）。三者缺一 = 该候选未闭环 = 对账失败（见 quality-gates 五层闭合 L3/L4）。
- 字段：candidate-finding 各阶段段新增 `cluster_ref`（discovery 段）与 `verification_record_ref`/`report_record_ref`（下游段），写权限按各段所有者。

## v0.3.9 增补（强 schema + 机器字段扩展 + confirmed 阈值 + 配置越界关卡）

- **candidates.tsv 顶层列固定为 16 列**（顺序即权威，Gate-1 方程「四相等+阈值」「候选 ID 反查」「三事实源一致性」按列名解析）：`candidate_id | location | sink_type | severity_hypothesis_initial | root_cause_group_id | lifecycle_state | verdict | cluster_ref | verification_record_ref | report_record_ref | created_at | discovery_source | path | start_line | end_line | discovery_reasoning_note`。`verdict` ∈ `confirmed`/`refuted`/`informational`/`suppressed`（suppressed = FALSE-rules 抑制留痕，需另附 `false_rule_hit` 说明）；三 ref 为顶层列，与对应字段段同步写入、值一致。
- **location 为 `{path}:{line}` 字符串形式**（与冻结清单 file:line 同形），Gate-1「候选 ID 反查」以此为准。
- **「候选 ID 反查」**（Gate-1）：`sink_seq`/`source_seq` 反查冻结清单 UTF-8 字节序排序位置，该位置行的 file:line 必须 == location；`sig8` == md5(file:line:sink_type) 前 8 位（无 sink fallback 为 md5(file:line) 前 8 位）。
- **machine-fields.json 每 confirmed 条目扩展为 9 字段**：原 6 字段（candidate_id/location/sink_type/severity/root_cause_group_id/verdict）+ `confidence` / `evidence_grade` / `runtime_tier`（tier 1-3 动态 / 4-5 半动态 / 6 纯静态）。run_fingerprint 仍只取核心 6 字段（跨版本可比）。
- **confirmed 阈值**（Gate-1「四相等+阈值」扩展判定）：tier 6 须 confidence ≥ 0.6 且三要素证据级全 direct；tier 4/5 须 ≥ 0.7；tier 1-3 须 ≥ 0.8。低于阈值即 FAIL，不得 confirmed。
- **配置越界关卡**（五步链第 4 步显式化）：每个候选验证段必须产出「默认配置可达性」结论（默认配置下前置条件是否满足 + conf/ 或代码默认值的证据行）；CVSS 的 AV/PR/AC 必须与该结论一致；finding 控制评估表新增一行「默认配置可达性」+ 证据引用。
## v0.3.4 增补（端到端就地落盘字段，设计 34 号 §4）

以下字段落实"详情报告每一节在生产时刻就落盘"的机制（生产时刻映射见 report-templates/finding-template.md 的映射表）：

| 字段 | 生产阶段 | 说明 |
|---|---|---|
| `hop_snippet`（证据链五段 source/propagation/sanitizers/sink/disproof_checked 各段每跳） | #3 深扫时 | `{path, start_line, end_line, snippet, highlight_line}`；snippet 为 ±3 行原文，highlight_line 标记关键行。**深扫时写入簇结论，禁止报告阶段重读源码补片段**；报告"调用链"节由此投影 |
| `root_cause_summary` | #4/#5 定级时 | 一句话根因摘要；报告"漏洞摘要"节由此投影 |
| `cvss_breakdown` | #4/#5 定级时 | 八分量逐项中文解释（AV/AC/PR/UI/S/C/I/A 各含取值+理由）；报告"CVSS 评分"节由此投影 |
| `exploit_scenario` | #4/#5（伴生 #6 启用时引用其产物） | 利用方式具体描述；报告"利用方式"节由此投影 |
| `remediation` | #4/#5（引用 fix-patterns） | `{suggestion, code_example, fix_pattern_ref}`；报告"修复建议"节由此投影（伴生 #7 不启用时这是唯一来源） |
| `lifecycle_state` | 各阶段按生命周期推进写入 | `created` / `verified` / `rated` / `reported`；每态对应落盘点（candidates.tsv / verification-summary / findings），无孤儿约束见设计 34 号 §3.1 |

每个阶段产物使用统一stage envelope：`{stage_result, version, resume_context, input_count, records, zero_input_reason?}`。`input_count`是该阶段收到的上游记录数，`records`是本阶段实际产出的记录数组。`input_count=0`时必须写非空`zero_input_reason`且允许`records=[]`；零输入不是candidate/finding/PoC/remediation记录，禁止为维持非空数组而虚构`candidate_id`、`poc_id`或`remediation_scope_id`。`input_count>0`时省略`zero_input_reason`。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | 当前累积产物所属阶段 | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前产物完成程度。 |
| `version` | `string` | 是 | 当前累积产物所属阶段 | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | 当前累积产物所属阶段 | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `input_count` | `integer` | 是 | 当前累积产物所属阶段 | 所有消费者 | 大于等于0；等于实际收到的上游记录数 | stage envelope输入计数。 |
| `records` | `array<object>` | 是 | 当前累积产物所属阶段 | 所有消费者 | 只包含本阶段真实记录；零输入时必须为`[]` | stage envelope记录集合。 |
| `zero_input_reason` | `string` | `input_count=0`时必填 | 当前零输入产物所属阶段 | 调度方、报告 | 非空，并附上游Gate和输入版本引用；不得放入合成记录 | 区分执行后无输入与未执行。 |
| `partial_report_context` | `object` | 条件必填 | 当前`stage_result=partial`的阶段 | #8报告 | 最少含`incomplete_capabilities`、`remaining_scope`、`resume_entry`、`affected_conclusions` | 部分报告的确定性输入。 |
| `candidate_id` | `string` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 全局唯一、创建后不可变；确定性派生 = `C-{sink_seq}-{source_seq}-{sig8}`：`sink_seq`/`source_seq` 为冻结清单按 `LC_ALL=C sort` 排序后的序号，`sig8` 为 `hash(file:line:sink_type)` 前 8 位；**fallback**：多 source 或多 sink 命中时 `sink_seq`/`source_seq` 取冻结清单排序序号最小者；无 sink 候选（业务逻辑/横向差异）`sink_seq` 取该候选所在文件的文件终态检查点排序序、`sig8` 取 `hash(file:line)` 前 8 位（无 `sink_type` 时省略）；不依赖运行时刻、不使用发现顺序 | 全生命周期主身份，同 revision 跨 run 不变。 |
| `created_at` | `string` | 是 | #3 `candidate-discovery`（创建时写入一次） | #4-#9、#16、#18 | ISO 8601 格式的创建时刻；候选创建时间，此后不可变 | 候选创建时间。 |
| `updated_at` | `string` | 是 | 当前累积产物所属阶段（每次覆盖更新） | 所有消费者 | ISO 8601 格式的最近更新时刻；最近一次覆盖更新时间 | 候选最近更新时间。 |
| `discovery_source` | `array&lt;string&gt;` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 非空；值见枚举注册表 `discovery_source`；多机制命中保留全部值 | 发现机制来源。 |
| `entry_ref` | `string` | 条件必填 | #3 `candidate-discovery` | #4-#9、#16、#18 | 有关联入口时必填并引用攻击面地图条目；无入口概念时省略并在 reasoning 说明 | 具体入口引用。 |
| `sink_ref` | `string` | 条件必填 | #3 `candidate-discovery` | #4-#9、#16、#18 | 有关联危险操作点时必填并引用攻击面地图条目；无 sink 概念时省略并在 reasoning 说明 | 具体危险操作引用。 |
| `location` | `object` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 最少为 `{path: string, start_line: integer, end_line: integer, trigger_condition: string, family_distinction: string \| null}` | 展开后的具体实例定位。 |
| `root_cause_group_id` | `string` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 非空；同根因实例共享，独立实例仍分别保留 candidate；确定性派生 = 按（`unified_semantic_ref` + 稳定 `symbol` + 模式 ref）组合派生，跨 run 不变 | 根因去重与代表性 PoC/修复单元。 |
| `discovery_reasoning_note` | `string` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 非空；按机制记录模式引用、预期偏离或横向对照组 | 可追溯的发现依据。 |
| `family_expansion_note` | `object` | 条件必填 | #3 `candidate-discovery` | #4-#9、#16、#18 | 家族级信号时必填，最少为 `{family_scope: string, identified_count: integer, fully_verified_count: integer, instance_refs: string[], remaining_location_refs: string[]}`；非家族信号可省略 | 禁止以概括性省略表述代替实例展开。 |
| `severity_hypothesis_initial` | `string` | 是 | #3 `candidate-discovery` | #4/#5 及所有下游 | 初始严重度假设；不得被最终定级覆写 | 保留“假设到定型”的追溯。 |
| `write_boundary` | `object` | 是 | #3 `candidate-discovery`（首次设置，后续只读） | #4-#9、#16、#18 | 最少为 `{target_source_path: string, working_copy_path: string, output_path: string, target_tree_modified: boolean, authorization_ref: string \| null}`；`target_tree_modified`初始为`false`，任何修改真实目标树的动作必须先获单独明确授权并更新为`true` | 写入边界：默认目标只读，PoC/补丁/测试写入工作副本或输出目录。 |
| `unified_semantic_refs` | `array&lt;string&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 引用统一漏洞语义 `UVS-*`；可空，目录外候选留空 | 候选可能属于的统一漏洞语义引用。`unified_semantic_refs` 只表示候选可能属于某统一语义，不等于模式驱动发现。 |
| `vuln_pattern_refs` | `array&lt;string&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 引用 `vuln-patterns` 条目ID；**只有命中具有 `discoverable=complete` 证据的 `vuln-pattern` 才能写本字段并称模式驱动发现**；未命中时留空 | 漏洞识别模式引用。 |
| `ecosystem_mapping_refs` | `array&lt;string&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 引用 `ecosystem-mappings` 条目ID（ECMAP-\*）；按目标检测到的语言/框架匹配生态映射后写入；未匹配时留空 | 生态映射引用。 |
| `ontology_trace` | `object` | 是 | #3 `candidate-discovery` | #4-#9、#16、#18 | 最少为 `{asset_refs: string[], trust_boundary_refs: string[], surface_refs: string[], entry_refs: string[], source_refs: string[], propagation_refs: string[], transformation_refs: string[], storage_refs: string[], guard_refs: string[], policy_decision_refs: string[], sanitizer_refs: string[], encoder_refs: string[], sink_refs: string[], state_transition_refs: string[], resource_consumption_refs: string[], oracle_refs: string[], impact_refs: string[]}`；允许记录不完整的路径（某些概念不适用时留空数组），**不要求伪造完整污点链** | 本体路径追踪，引用攻击面地图中的实例 stable_id。 |
| `knowledge_snapshot_id` | `string` | 是 | run初始化时冻结；#3引用 | #4-#9、#16、#18 | 引用`knowledge-session-template.md`实例，阶段间保持一致 | 本run共享知识快照身份。 |
| `knowledge_consultations` | `array&lt;object&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 每项最少为 `{knowledge_snapshot_id: string, index_version: string, semantic_or_pattern_ref: string, consultation_result: string, match_basis: string, evidence_refs: string[]}`；`consultation_result`只引用注册表；snapshot必须等于候选顶层值；只有注册表定义的模式命中结果才能称模式驱动发现 | 可审计的多条知识查阅记录。 |
| `capability_gap_refs` | `array&lt;string&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 引用知识缺口记录；业务逻辑和横向差异发现机制发现的尚无 `UVS-*` 的候选必须写本字段并进入知识演进 | 能力缺口引用（知识不完整时记录）。 |
| `cross_boundary_path` | `array&lt;object&gt;` | 否 | #3 `candidate-discovery`仅写本WU已知路径段 | #4-#9、#16、#18 | 每项（逐跳）最少为 `{from: {path: string, line: integer}, to: {path: string, line: integer}, edge_kind: string, note: string}`；`edge_kind` 引用 [`boundary_edge_kind`](../enum-registry.md#boundary_edge_kind)；本WU内已观察路径；汇聚方不得原地补写 | 分片内路径事实（逐跳结构，from/to 各含 path、line）。 |
| `cross_boundary_path_ref` | `string` | 跨WU传播时必填 | #3引用宿主生成的独立聚合产物 | #4-#9、#16、#18 | 指向`cross_boundary_aggregate_ref`内的完整只读路径；汇聚方不得改候选或WU分片 | 完整跨WU路径引用。 |
| `semantic_transitions` | `array&lt;object&gt;` | 否 | #3 `candidate-discovery` | #4-#9、#16、#18 | 每项最少为 `{step: integer, location: object, variable: string, semantics: string, state: string, cause: string}`；`location` 完整复用本文件 #3 `location` 结构；由候选发现写入，报告 `findings/V{N}.md` 的"数据流语义变迁表"由此投影 | 数据流语义变迁（步骤/位置/变量/语义/状态/原因）。 |
| `false_rule_hit` | `object` | 条件必填 | #3 `candidate-discovery`（#4/#5 独立命中时返回 #3 补记） | #4-#9、#16、#18 | 命中 [`../../knowledge/FALSE-rules.md`](../../knowledge/FALSE-rules.md) 时必填；最少为 `{rule_ref: string, rule_name: string, matched_condition: string, evidence_refs: string[]}`；命中即忽略：不产出候选、不进入验证、不进入 finding，记录保留供审计 | FALSE-rules 命中即忽略的留痕。 |
| `cluster_ref` | `string` | 是 | #3 `candidate-discovery`（创建时写一次） | #4-#9、#16、#18 | 引用该候选所属簇的结论文件路径（`clusters/{cluster_id}.md`），非空；backward/forward 检查点的 `cluster_conclusion:` 理由引用同文件 | 三记录闭包之①：discovery 记录引用其产生簇结论，证据链五段落在该簇结论文件内。 |

## #4/#5 验证与定级字段

**证据分级（`evidence_grade`）逐判断标注（全局纪律）**：本段所有关键判断字段（六项基线各项、候选专属清单各项、四类控制评估各项、三要素各项、验证终态）必须逐项标注 `evidence_grade`（`direct`/`indirect`/`unknown`，见 [`evidence_grade`](../enum-registry.md#evidence_grade)）并绑定 `evidence_refs`。全局纪律：**结论强度不得超过证据链最弱一环**——`confirmed` 需全要素直接证据（或大部直接 + 其余强间接且无反证，并在终态注明最弱环）；仅凭间接推断"应该安全"不得定 `refuted`。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `verification_baseline` | `object` | 是 | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 必含 `reachable`/`controllable`/`propagatable`/`exploitable`/`reproducible`/`impact_there`；每项最少为 `{result: string, evidence_grade: string, evidence_refs: string[], applicability_reason: string \| null}`，result 见枚举注册表基线结果，evidence_grade 见 [`evidence_grade`](../enum-registry.md#evidence_grade) | 六项 AND 必要条件及证据。 |
| `three_elements` | `object` | 是 | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 必含 `controllable_source`/`reachable_path`/`failed_control` 三个子对象；每项最少为 `{annotates: string[], evidence_grade: string, evidence_refs: string[], note: string \| null}`；evidence_grade 见 [`evidence_grade`](../enum-registry.md#evidence_grade)。三要素（可控源/可达路径/失效防护）是六项基线 + 四类控制评估的语义注释，不重复实现、不新增机器判定值：`controllable_source` 注释 `controllable`，`reachable_path` 注释 `reachable`/`propagatable`，`failed_control` 注释 `control_assessment` | 三要素必要条件语义注释。 |
| `candidate_specific_checklist` | `object` | 是 | #4/#5 | #6-#9、#16、#18 | 最少为 `{applicability: string, reason: string, items: array&lt;object&gt;}`；`applicability`见枚举注册表 [`checklist_applicability`](../enum-registry.md#checklist_applicability)；`applicable`时`items`每项最少为 `{check: string, result: string, evidence_grade: string, evidence_refs: string[]}`且`result`使用基线结果值集、`evidence_grade` 见 [`evidence_grade`](../enum-registry.md#evidence_grade)，按candidate实际语义列出全部必要检查项，不设人为数量上限；`not_applicable`时`reason`必须非空且`items`为空数组；**禁止真空通过**：`items=[]`且`applicability=applicable`不合法 | 候选专属核查点。 |
| `verification_methods` | `array&lt;object&gt;` | 是 | #4/#5 | #6-#9、#16、#18 | 非空；每项最少为 `{method: string, tier: integer, evidence_mode: string, evidence_refs: string[], downgrade_reason: string \| null, blocked_reason: string \| null}`；tier为1-7，`evidence_mode`引用注册表且`evidence_refs`非空。每种真实使用的方法单独成项，不得用单一最高层级覆盖混合证据 | 分段绑定实际验证方法、证据模式、引用和降级事实。 |
| `confidence_score` | `object` | 是 | #4/#5 | #6-#9、#16、#18 | 最少为 `{value: number, threshold: number, threshold_passed: boolean, rationale: string}`；`value` 与 `threshold` 均为 0-10，`threshold_passed` 必须等于 `value >= threshold` 的结果，`rationale` 非空；不得与 severity 合并 | 从方法与证据强度推导的完整置信度记录。 |
| `independent_review_e1e2` | `object` | 否（deprecated，物理保留供历史消费方参考） | #4/#5宿主汇聚方；reviewer只写独立分片 | #6-#9、#16、#18 | 最少为 `{e1_result: string, e1_review_artifact_ref: string, e2_result: string \| null, e2_review_artifact_ref: string \| null, e2_trigger_reasons: string[] \| null, rounds: integer, arbitration: string \| null, independence_disclosure: string}`；E1/E2分片须通过run/candidate/reviewer/输入版本核对后才能汇聚；引用是证据定位，不替代结论结构 | [deprecated since v0.3.0] E1/E2 重型分片复核，已被 `second_opinion_review` 轻量第二意见取代；物理保留供历史消费方参考。 |
| `second_opinion_review` | `object` | 是 | #4/#5 `verification-and-rating`（独立第二意见角色） | #6-#9、#16、#18 | 最少为 `{reviewer_independence: string, false_rule_mis-kill_checked: boolean, evidence_grade_checked: boolean, symmetric_reversal: object \| null, conclusion: string, disagreement_resolution: string \| null, evidence_refs: string[]}`；`conclusion` 复用 [`verification_verdict`](../enum-registry.md#verification_verdict) 值集；`symmetric_reversal` 在 High/Critical 候选上可选执行对称反转，最少为 `{triggered: boolean, direction: string, result: string, evidence_refs: string[]}`（推翻 VULN 需证伪要素之一直接证据；推翻 NOVULN 需构造可实施攻击路径）；分歧按最保守（最低置信）状态合成 | 每候选一次轻量第二意见，核对 FALSE-rules 误杀与证据分级；High/Critical 可选对称反转。 |
| `verification_verdict` | `object` | 是 | #4/#5 | #6-#9、#16、#18 | 最少含 `{value: string, evidence_grade: string}`，`value` 见枚举注册表，`evidence_grade` 见 [`evidence_grade`](../enum-registry.md#evidence_grade)。仅#4/#5可写`refuted`；此时同一对象内条件必填 `refutation_category: string` 和非空 `refutation_evidence_refs: string[]`。`confirmed`表示当前代码事实/风险主张经证据确认：可利用漏洞六项适用基线须全`pass`，且需全要素直接证据（或大部直接 + 其余强间接且无反证，注明最弱环）；无活攻击面事实按本契约身份边界处理。`unconfirmed` 对齐 SUSPECTED 语义：前提在但关键要素无法确认，必须写清缺口位置与所需证据；`refuted` 对应前提缺失或明确反证成立，仅凭间接推断"应该安全"不得定 `refuted`。`confirmed`/`unconfirmed`不得携带反证属性 | 候选验证终态及 refuted 专属机器可读反证信息。 |
| `severity_hypothesis_initial` | `string` | 是 | #3；#4/#5 仅回读 | #4-#9、#16、#18 | 与 #3 原值完全一致 | 在本段展示仅为追溯，不形成第二写入方。 |
| `impact_rating` | `object` | 条件必填 | #4/#5 | #6-#9、#16、#18 | 进入严重度评估时必填，包括本字段为`unknown`的记录；最少为 `{rating: string, asset_refs: string[], profitability_note: string}`；rating 及权威矩阵见枚举注册表；仅当本字段`rating=high`且`likelihood_rating.rating=high`时额外必填`critical_criteria_met: boolean`；其他组合省略该属性 | 影响档位、获利性及high×high的Critical标准判定。 |
| `likelihood_rating` | `object` | 条件必填 | #4/#5 | #6-#9、#16、#18 | 进入严重度评估时必填，包括本字段为`unknown`的记录；最少为 `{rating: string, baseline_evidence_refs: string[], exposure: string, authentication_required: boolean \| null, user_interaction_required: boolean \| null}`；`rating` 与 `exposure` 分别使用注册表的 [`impact_rating 与 likelihood_rating`](../enum-registry.md#impact_rating-与-likelihood_rating) 和 [`exposure_scope`](../enum-registry.md#exposure_scope) | 复用基线证据的触发可能性。 |
| `impact_description` | `string` | 否 | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 非空时为一句话影响描述；触发流程映射到 `detailed_narrative_view.attack_path`，报告 `findings/V{N}.md` 的"漏洞影响"由此投影 | 漏洞影响一句话描述。 |
| `suppression_flag` | `object` | 条件必填 | #4/#5 | #6-#9、#16、#18 | 执行严重度定级时必填；最少为 `{applied: boolean, reasons: string[]}`。命中仅影响自己、前提不现实或需已有管理员权限且非提权问题时，必须`applied=true`、记录具体原因并令`likelihood_rating.rating=ignore`；impact仍按事实评估。存在真实跨信任边界影响时不得因“仅影响自己”抑制 | 严重度硬性抑制事实；命中不删除记录。 |
| `final_severity` | `string` | 条件必填 | #4/#5 | #6-#9、#16、#18 | 执行严重度定级时必填；允许值及唯一权威矩阵见枚举注册表 [`final_severity`](../enum-registry.md#final_severity)；`unknown` 轴按该矩阵产出严重度，不得据此改写 `verification_verdict`；`informational` 仅用于无存活攻击面的代码卫生记录，不进入矩阵 | 矩阵政策结果或矩阵外代码卫生定级。 |
| `priority` | `string` | 条件必填 | #4/#5 | #6-#9、#16、#18 | 映射及允许值见枚举注册表 [`priority`](../enum-registry.md#priority)；`final_severity=ignore` 时禁止出现，`final_severity=informational` 时可选，其余按注册表必填 | 严重度对应修复优先级；矩阵政策结果 `ignore` 不进入主动修复队列，但作为finding进入#9显式处置。 |
| `cvss_vector` | `string` | 条件必填 | #4/#5 | #6-#9、#16、#18 | `final_severity` 存在且目标导出需要 CVSS 时必填；必须为 CVSS 3.1 向量并由已确定事实映射 | 兼容性导出，不独立重新评分。 |
| `severity_independent_review` | `object` | 否（deprecated，物理保留供历史消费方参考） | #4/#5 | #6-#9、#16、#18 | 完成严重度定级时必填；最少为 `{review_result: string, matrix_recalculation: string, rounds: integer, arbitration: string \| null}` | [deprecated since v0.3.0] 严重度独立复核，已并入 `second_opinion_review` 的对称反转复核；物理保留供历史消费方参考。 |
| `control_assessment` | `object` | 是 | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 必含 `guard`/`policy_decision`/`sanitizer`/`encoder` 四个子对象；适用时最少为 `{applicability: applicable, expected_control: string, observed_control: string, failure_or_bypass: string, result: string, evidence_grade: string, evidence_refs: string[], location: object \| null}`；不适用时必须为`{applicability: not_applicable, applicability_reason: string, result: not_applicable, evidence_grade: string, evidence_refs: string[]}`并省略`expected_control`/`observed_control`/`failure_or_bypass`；`location` 为可选定位，完整复用本文件 #3 `location` 结构。`applicability`和`result`只引用注册表；四类控制分别独立评估 | 四类控制分别评估（各子对象可选 `location`），禁止以`N/A`字符串填充字段。 |
| `verification_knowledge_refs` | `object` | 否 | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 最少为 `{vuln_pattern_refs: string[], verification_method_ref: string, refutation_method_ref: string, exclusion_conditions_checked: string[], version_diff_notes: string[]}`；引用命中的vuln-pattern条目的验证方法、反证方法和排除条件；`version_diff_notes`记录生态版本差异对验证的影响 | 验证知识引用——#4实际读取vuln-pattern的验证方法/反证方法/排除条件和版本差异。 |
| `verification_record_ref` | `string` | 是 | #4/#5 `verification-and-rating`（定级完成时写一次） | #6-#9、#16、#18 | 引用 `verification-summary.md` 中该候选对应段（`candidate_id` 锚点），非空 | 三记录闭包之②：validation 记录引用其验证定级段。 |

## #6 可利用性证明字段

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `poc_id` | `string` | 是 | #6 `exploit-proof` | #7-#9、#18 | PoC 唯一标识 | 代表性证明包身份。 |
| `candidate_ref` | `object` | 是 | #6 | #7-#9、#18 | `{candidate_id: string, root_cause_group_id: string}`；引用值必须与上游一致 | 代表候选和根因组引用。 |
| `group_variant_note` | `string` | 条件必填 | #6 | #7-#9、#18 | 同组因实质前置条件差异产出多份 PoC 时必填；否则可省略 | 组内变体理由。 |
| `evidence_composition` | `string` | 是 | #6 | #7-#9、#18 | 见枚举注册表 [`evidence_composition`](../enum-registry.md#evidence_composition)；组合规则：全部段`executed`→`executed`，全部段`inferred`→`inferred`，混合→`mixed` | 整体证据组合状态。 |
| `evidence_segments` | `array&lt;object&gt;` | 是 | #6 | #7-#9、#18 | 非空；每项最少为 `{segment_id: string, claim: string, evidence_mode: string, evidence_refs: string[], execution_scope: string, limitations: string[]}`；`evidence_mode`见枚举注册表 [`evidence_mode`](../enum-registry.md#evidence_mode)；`evidence_refs`非空且只引用#4既有证据；`inferred`段禁止携带伪执行结果 | 按最小可信颗粒度拆分的证据段。 |
| `source_evidence_ref` | `array&lt;string&gt;` | 是 | #6 | #7-#9、#18 | 非空；只引用 #4 既有证据，不新增独立证据 | PoC 来源证据。 |
| `harm_minimization_note` | `string` | 是 | #6 | #7-#9、#18 | 非空；记录良性标记、测试专用凭证和危险 payload 替换 | 危害最小化处置。 |
| `isolation_note` | `object` | 是 | #6 | #7-#9、#18 | 最少为 `{artifact_path: string, target_tree_modified: boolean}`；后者必须为 false | 安全隔离说明。 |
| `optional_dependency_mock_note` | `string` | 条件必填 | #6 | #7-#9、#18 | 采用依赖模拟时必填；未采用时省略 | 猴子补丁式依赖模拟摘要。 |
| `package_content` | `object` | 是 | #6 | #7-#9、#18 | 最少为 `{demonstrates: string, prerequisites: string[], steps_or_walkthrough: string[], expected_observation: string, cleanup_steps: string[], evidence_refs: string[]}`；`inferred`段不得写成已执行步骤 | 自包含证明包。 |
| `reexecution_check` | `object` | 条件必填 | #6 | #7-#9、#18 | 存在`evidence_mode=executed`的段时必填 `{result: string, checked_at: datetime, evidence_refs: string[]}`；`result` 见枚举注册表 [`poc_reexecution_result`](../enum-registry.md#poc_reexecution_result)；全部段为`inferred`时省略 | 打包后实际复现检查。 |
| `tool_export_format` | `array&lt;string&gt;` | 否 | #6 | #7-#9、#18 | 仅声明可导出的源格式名称；具体导出结果由 #18 写 `export_artifact` | 不得伪造外部导出成功。 |
| `attack_pattern_refs` | `array&lt;string&gt;` | 否 | #6 `exploit-proof` | #7-#9、#18 | 引用 `attack-patterns` 条目ID（ATK-\*）；按semantic→vuln→生态→proof mode→Oracle选择条目后写入；未匹配时留空并记录原因 | 攻击模式引用——#6正式消费attack-patterns知识库。 |

## #7 修复指导字段

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `remediation_scope_id` | `string` | 是 | #7 `remediation-guidance` | #8、#9、#16、#18 | 单根因组或跨多个根因组的稳定处理单元标识 | 修复指导身份。 |
| `remediation_mode` | `string` | 是 | #7 | #8、#9、#16、#18 | 见枚举注册表 `remediation_mode` | 战术补丁或结构加固提案。 |
| `fix_pattern_ref` | `string` | 条件必填 | #7 | #8、#9、#16、#18 | `tactical_patch` 且命中知识模式时必填；未命中时省略并在补丁依据中说明 | 修复知识条目引用。 |
| `hardening_cluster_basis` | `object` | 条件必填 | #7 | #8、#9、#16、#18 | 执行B2聚类评估时必填；最少为 `{structural_hardening_recommended: boolean, basis_type: string, basis_description: string, root_cause_group_ids: string[]}`。true时`remediation_mode=structural_hardening_proposal`且至少涉及两个不同根因组；false时伴随相关B1 `tactical_patch`记录，说明聚类依据不足，不生成`proposal_content` | 架构聚类评估依据及是否推荐结构加固。 |
| `priority_order_trace` | `array&lt;object&gt;` | 是 | #7 | #8、#9、#16、#18 | 依次覆盖六项优先级；每项最少为 `{criterion: string, satisfied: boolean, evidence_refs: string[]}`，不得用后项换前项 | 修复质量优先级核对。 |
| `patch_content` | `object` | 条件必填 | #7 | #8、#9、#16、#18 | `tactical_patch` 时必填；最少为 `{diff: string, affected_paths: string[], rationale: string}` | 窄范围补丁内容，与 proposal 分离。 |
| `proposal_content` | `object` | 条件必填 | #7 | #8、#9、#16、#18 | `structural_hardening_proposal` 时必填；最少为 `{description: string, options: string[], tradeoffs: string[]}` | 架构性方案及选项权衡。 |
| `evidence_tag` | `string` | 是 | #7 | #8、#9、#16、#18 | 见枚举注册表 `evidence_tag` | 修复内容的事实角色标签。 |
| `fix_verification_result` | `object` | 条件必填 | #7 独立验证步骤/角色 | #8、#9、#16、#18 | 已落地补丁时必填；最少为 `{verification_mode: string, reported_instance_result: string, group_instance_results: array&lt;object&gt;, blocked_reason: string \| null, evidence_refs: string[]}`；`verification_mode` 见枚举注册表；两个结果字段使用 `remediation_verification_result`，`group_instance_results` 每项最少为 `{location: object, result: string, evidence_refs: string[]}`，其中 `location` 完整复用本文件 #3 `location` 结构。`executed` 记录修复后真实重跑；`inferred` 只记录对修复后代码重走同一静态证据链，禁止表述为执行或重跑。生成补丁的同一次判断不得自认证 | 全根因组修复验证。 |
| `patch_application` | `object` | `final_result=fixed`时必填 | #7补丁应用步骤 | #7独立验证、#8、#9 | 必含`applied: boolean`、`target_kind: string`、`before_revision: string`、`after_revision: string`、`artifact_ref: string`、`applied_at: datetime`、`authorization_ref: string`、`verification_revision_ref: string`。fixed时`applied=true`、`before_revision!=after_revision`，验证与独立绕过复核必须绑定同一`after_revision`；仅建议diff不得填写 | 证明获授权补丁已应用到明确目标并由应用后revision复核；无此证据禁止写fixed。 |
| `bypass_review_result` | `object` | 条件必填 | #7 独立对抗复核角色 | #8、#9、#16、#18 | 已落地补丁时必填；最少为 `{equivalent_bypass_found: boolean \| null, reviewer_independence: string, arbitration: string \| null, evidence_refs: string[]}` | 对等绕过路径复核。 |
| `final_result` | `string` | 是 | #7 `remediation-guidance` | #8、#9、#16、#18 | 见枚举注册表；每条战术修复和结构提案均必填，未获人工决策的结构提案使用`needs_human_decision`。`structural_hardening_recommended=false`不是独立修复记录，不产生自己的`final_result`。`inherently_safe`仅允许在#7记录新证据并回退#4、由#4将原风险主张改判为`refuted`后作为历史投影记录 | 修复指导终态。 |

## #8 报告投影字段

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `summary_triage_view` | `array&lt;object&gt;` | 是 | #8 `report-delivery` | 人工读者、#18 | 每项最少为 `{candidate_id: string, severity: string, confidence_score: object, root_cause_summary: string, remediation_summary: string}`；`confidence_score` 完整复用本文件 #4/#5 同名对象，不得降格为数值；按`critical`>`high`>`medium`>`low`>`informational`>`ignore`展示；`informational`必须标为candidate/code-hygiene item而非finding，其`remediation_summary`仅为代码卫生建议；`ignore`必须标为政策忽略finding，完整保留但不是优先修复项 | 简明分诊视图。 |
| `detailed_narrative_view` | `array&lt;object&gt;` | 是 | #8 | 人工读者、#18 | 每项最少为 `{candidate_id: string, evidence_walkthrough: array&lt;object&gt;, poc_ref: string \| null, attack_path: string, remediation_ref: string \| null}`；`evidence_walkthrough` 每项最少为 `{role: string, location: object, evidence_ref: string, narrative: string}`，`role` 见枚举注册表 [`evidence_role`](../enum-registry.md#evidence_role)，`location` 完整复用本文件 #3 `location` 结构，`evidence_ref` 与 `narrative` 均非空；`informational`代码卫生candidate的`poc_ref`与`remediation_ref`必须为null，只投影代码事实与清理建议，不得称finding | 详细证据叙事。 |
| `family_expansion_entries` | `array&lt;object&gt;` | 是 | #8 | 人工读者、#18 | 每个独立可攻击实例一项，最少为 `{candidate_id: string, root_cause_group_id: string, location: object}`；`location` 完整复用本文件 #3 `location` 结构；摘要不得替代逐项 | 家族/兄弟实例投影。 |
| `reviewed_surfaces_coverage` | `array&lt;object&gt;` | 是 | #8 | 人工读者、#18 | 每项 `{surface: string, risk_area: string, outcome: string, notes: string}`；outcome 使用枚举注册表报告覆盖机器值，展示时可映射自然语言值 | 覆盖度确定性投影。 |
| `structural_hardening_link` | `string` | 条件必填 | #8 | 人工读者、#18 | #7存在`structural_hardening_recommended=true`的结构加固提案时必填有效相对链接；false时省略并在报告说明未触发 | 完整提案的简短链接。 |
| `harm_minimization_disclosure` | `string` | 是 | #8 | 人工读者、#18 | 非空；确认未复制 PoC 取得的真实敏感内容 | 报告脱敏声明。 |
| `zero_finding_statement` | `string` | 条件必填 | #8 | 人工读者、#18 | 无confirmed、存在活攻击面且非informational的finding时必填，并引用零候选、证伪、informational candidate及覆盖记录 | 零发现原因说明；只有代码卫生candidate也属于零finding。 |
| `evidence_role_labels` | `array&lt;object&gt;` | 是 | #8 | 人工读者、#18 | 每项最少为 `{candidate_id: string, evidence_ref: string, role: string}`；`role` 见枚举注册表 [`evidence_role`](../enum-registry.md#evidence_role) | 证据角色标签，不得为叙事流畅编造引用。 |
| `report_record_ref` | `object` | 是 | #8 `report-delivery`（投影时写一次） | 人工读者、#18 | 最少为 `{finding_md_ref: string, machine_fields_row_ref: string}`，引用 `findings/V{N}.md` 与该候选的 `machine-fields.json` 行 | 三记录闭包之③：report 投影记录引用其详情文件与机器字段行。 |

#8 只是 #1-#7 的确定性投影。报告发现错误时必须返回唯一写入方修正上游结构，再重新投影；不得直接修改报告来制造第二份事实源。

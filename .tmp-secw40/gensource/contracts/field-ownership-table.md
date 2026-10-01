# 字段写权限表

本表是 [`shared/field-ownership.md`](../shared/field-ownership.md) 的实例化定稿。阶段只能写自己拥有的字段段；未列为写权限方即为只读。枚举值以 [enum-registry.md](enum-registry.md) 为准。

通用违规处理：越权覆写、删除历史事实或跨阶段抢写终态均属于结构性错误，应拒绝当前产物并返回唯一写权限方修正。证据按下表实行分段唯一写权限，已有证据不得删除、替换或改写；纠错只能由该段唯一写权限方追加带来源和理由的新条目。

## v0.3.0 增补（检测引擎重构字段）

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `progress_summary`（batches/channels_done/sink_types_done/remaining） | 顶层调度每完成一个通道/清单/batch 立即覆盖更新 | 所有能力 | 伪造进度会破坏压缩恢复与续跑，拒绝产物。 |
| `run_fingerprint` | 顶层调度在报告交付完成后按排序后机器字段集合哈希写入 | 所有能力、报告只读投影 | 伪造指纹会掩盖稳定性问题，拒绝产物。 |
| `inventories_frozen`（三份清单 path+行数）、`failed_wus_ref` | 顶层调度在阶段0 冻结清单后写入 | 所有能力 | 越权修改会破坏客观分母对账，硬门拒绝。 |
| `input_count` / `records` / `zero_input_reason`（stage envelope） | 当前产物所属阶段；零输入时 records 为空且 zero_input_reason 非空 | 下游阶段、Gate、报告 | 伪造输入数或零输入理由会破坏七等式对账，拒绝产物。 |
| `partial_report_context` | 报告交付在任一上游 partial 时按上游产物逐项投影 | 报告读者 | 从会话记忆补写会伪造恢复入口，拒绝产物。 |
| `evidence_grade`（direct/indirect/unknown）、`three_elements`、`false_rule_hit` | #4/#5 `verification-and-rating`（阶段2）逐判断写入；候选创建时不得预填 | 下游阶段、报告 | 越权标注会伪造证据强度，拒绝产物。 |
| `second_opinion_review` | #4/#5 `verification-and-rating`（阶段2）轻量复核角色写入 | 报告 | 自我复核或不落盘即写入会伪造独立性，拒绝产物。 |

## 共享状态字段（全部阶段）

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `stage_result` | 当前产物所属阶段；值集只引用枚举注册表，不由本权限表定义 | 所有下游阶段、报告与外部导出 | 其他阶段代写会伪造完成度，拒绝产物。 |
| `version` | 当前产物所属阶段，按共享版本体系写入 | 所有消费方 | 私建或覆写版本会破坏兼容判断，拒绝产物。 |
| `resume_context` | 当前产物所属阶段，记录该阶段续跑上下文 | 调度方与下游阶段 | 跨阶段修改会导致错误续跑或遗漏范围，拒绝产物。 |

## 运行状态字段（run-state.md）

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `anchor` | 顶层调度（GenSource SKILL.md）；`anchored_at`/`current_capability`/`current_work_unit_id`/`next_action`由执行锚定的调度角色覆盖写入（恢复即完整锚定，无 `anchor_type`） | 所有能力（只读） | 能力代写锚定记录会伪造锚定事实，拒绝产物。覆盖式更新，不是追加日志。 |
| `run_id`、`source_path`、`source_revision`、`authorized_scope`、`authorized_components`、`scope_includes`、`scope_excludes`、`confirmation_policy`、`run_mode` | 顶层调度初始化时冻结 | 所有能力、WU、Gate | 越权修改会改变运行身份、确认策略或授权边界，硬门拒绝。 |
| `run_status`、`current_capability`、`completed_artifacts`、`remaining_scope` | 顶层调度按已持久化事实覆盖写入 | 所有能力、报告 | 能力代写会伪造运行进度，拒绝产物。 |
| `gate_summary` | 对应Gate执行方产出独立Gate记录后，由顶层调度串行投影 | 所有能力、报告 | 能力直接改Gate结果或重复承载独立记录会绕过Gate。 |
| `single_document_guard` | 顶层调度在整文件替换及严格核对时写入 | 所有能力 | 其他角色不得自报解析/一致性通过。 |

## Work Unit Manifest字段

> ⚠️ DEPRECATED（v0.11.1 标注）：本段为 v0.6.1 前 YAML 版 manifest 字段集，与现行 wu_manifest.tsv 8 列 TSV schema（wu_id|sink_type|sink_ids|sink_locations|sink_count|status|cluster_id|batch_num，见 wu_decompose.py）零交集，仅历史参考。

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `run_id` | WU创建时一次性写入（与`run-state.md`的`run_id`一致），此后不可变 | 宿主、所有能力 | 修改会断裂WU与run的归属关系，硬门拒绝。 |
| `source_path` | WU创建时一次性写入（与`run-state.md`的`source_path`一致），此后不可变 | 宿主、所有能力 | 修改会伪造审计目标，硬门拒绝。 |
| `source_revision` | WU创建时一次性写入，此后不可变 | 宿主、所有能力 | 修改会破坏汇聚前身份检查，拒绝产物。 |
| `upstream_artifacts` | WU创建时一次性写入，此后不可变 | 所有能力 | 修改会破坏汇聚前身份检查，拒绝产物。 |
| `estimated_workload` | WU创建时一次性写入 | 宿主、调度方 | 修改会伪造工作量预估，拒绝产物。 |
| `remaining_scope` | WU执行过程中由当前执行角色覆盖更新 | 宿主、调度方 | 跨WU修改会导致重复或遗漏工作，拒绝产物。 |
| `boundary_facts_ref` | WU创建时一次性写入；指向该WU分片产出的边界事实文件，结构见 [`data-structures/work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md) | 宿主、汇聚方、`candidate-discovery`、`verification-and-rating` | 越权修改会断裂WU与边界事实的归属关系，拒绝产物。 |
| `cross_boundary_aggregate_ref` | 宿主汇聚方完成多WU只读汇聚后写入Manifest并投影到run-state | Gate、`candidate-discovery`、`verification-and-rating`、报告 | 缺失、指向输入WU、引用不可解析或越权修改均拒绝产物。 |
| `attempt_history` | 宿主只追加，不得改写、重排或删除已有条目 | 所有能力 | 改写或删除历史条目会破坏执行追溯，拒绝变更。 |
| `wu_trigger_evaluation`、`authorized_scope_ref` `[deprecated since v0.3.0]` | 历史保留：v0.3.0 起 WU 触发改为批式流水线（分片文件存在性判定），不再做四布尔触发评估 | 所有能力、Gate | 缺失或越权修改会绕过WU触发门或授权边界，硬门拒绝。 |
| `work_unit_status` `[deprecated since v0.3.0]`、`artifact`、`candidate_ids`、`attempt`、`failure_reason` | 当前WU执行角色写分片事实，宿主核实后串行更新Manifest；`work_unit_status` 已废弃，WU 状态改由分片文件存在性判定（WU 五态） | Gate、下游能力 | subagent直接改Manifest或宿主未核实即完成均拒绝。 |
| `supersedes`、`superseded_by`、`source_revision_changed` | 宿主检测revision变化后只追加谱系；旧WU其余事实冻结 | 所有能力 | 修改旧revision或删除谱系会伪造身份，硬门拒绝。 |

## Work Unit 边界事实字段

边界事实结构见 [`data-structures/work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md)，汇聚规则见 [`shared/cross-boundary-analysis.md`](../shared/cross-boundary-analysis.md)。

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `wu_id`、`run_id`、`source_revision`、`scope` | WU创建时一次性写入（与WU Manifest冻结值一致），此后不可变 | 宿主、汇聚方、所有能力 | 修改会断裂边界事实与WU的归属关系，硬门拒绝。 |
| `inputs`、`outputs`、`source_refs`、`sink_refs`、`guard_refs`、`sanitizer_refs`、`encoder_refs` | 产出该WU分片的能力（`scope-and-context`/`candidate-discovery`/`verification-and-rating`） | 汇聚方、其他能力 | 越权修改会改变边界连接事实，拒绝产物。 |
| `call_edges`、`field_mappings`、`storage_edges`、`transport_edges` | 产出该WU分片的能力；分片完成后冻结 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 任何角色原地补边或翻转`resolved`均拒绝；汇聚方必须写独立汇聚结果。 |
| `unresolved_connections` | 产出该WU分片的能力；分片完成后冻结 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 汇聚方追加/删除/改写原始项会掩盖缺口，拒绝产物；汇聚后状态写独立结果。 |
| `cross_boundary_aggregate`（`run_id`、`source_revision`、`input_wu_ids`、`input_boundary_fact_versions`、`aggregate_edges`、`unresolved_connections`、`version`） | 宿主汇聚方写独立新产物，只读冻结WU分片 | #3、#4/#5、Gate、报告 | 原地修改WU事实、聚合边缺`source_edge_ref`、缺少来源引用或把推断冒充原始边均拒绝。 |
| `evidence`、`confidence` | 产出该WU分片的能力 | 汇聚方、`verification-and-rating` | 越权修改会伪造边界事实的可信度依据，拒绝产物。 |

## #1 威胁语境

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `overview`、`threat_model_trust_boundaries_assumptions`、`attack_surface_protections_attacker_story` | #1 `scope-and-context`；用户确认结果可由本阶段据实回填 | #2-#9、#16、#18 | 下游改写会改变审计前提和信任边界，拒绝产物并返回 #1。 |
| `severity_calibration`、`input_controllability`、`production_vs_test_scope` | #1 `scope-and-context` | #2-#9、#16、#18 | 越权修改会污染验证和定级基准，拒绝产物。 |
| `generation_basis`、`user_confirmed` | #1 `scope-and-context` | 所有下游与报告层 | 越权修改会伪造来源或人工确认，拒绝产物。 |

## #2 攻击面范围地图

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `file_level_inventory`、`named_category_scan_results` | #2 `scope-and-context` 的攻击面子任务 | #3-#9、#16、#18 | 下游修改会改变覆盖分母或扫描事实，拒绝产物并重建地图。 |
| `zero_hit_review_flags`、`open_semantic_findings`、`methodology_disclosure` | #2 `scope-and-context` 的攻击面子任务 | #3-#9、#16、#18 | 删除或改写会掩盖覆盖缺口，拒绝产物。 |
| `feedback_to_checklist` | #2 `scope-and-context` 的攻击面子任务 | #16 知识演进及其他下游 | #16 可消费并生成自己的提议，不得反写该字段；越权反写拒绝。 |
| `ontology_version`、`knowledge_manifest_version` | #2 `scope-and-context` 的攻击面子任务 | 所有消费者 | 越权修改会伪造知识基座版本，拒绝产物。 |
| `asset_instances`、`trust_boundary_instances`、`surface_instances`、`entry_instances`、`source_instances`、`propagation_instances`、`control_instances`、`sink_instances`、`observable_oracle_instances`、`security_impact_hypotheses`、`knowledge_gaps` | #2 `scope-and-context` 的攻击面子任务 | #3-#9、#16、#18 | 下游改写会改变本体实例事实或掩盖知识缺口，拒绝产物并重建地图。`control_instances`中Guard/Policy Decision/Sanitizer/Encoder必须分别识别，合并为笼统"安全控制"属于结构性错误。 |

## #3 candidate 结构

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `candidate_id` | #3 `candidate-discovery` 创建时一次性写入；创建后不可变 | #4-#9、#16、#18 | 任何后续修改都会破坏全链路身份，硬门拒绝。 |
| `discovery_source`、`entry_ref`、`sink_ref`、`location` | #3 `candidate-discovery` | #4-#9、#16、#18 | 越权修改会改变发现来源或定位事实，拒绝产物。 |
| `root_cause_group_id`、`discovery_reasoning_note`、`family_expansion_note` | #3 `candidate-discovery` | #4-#9、#16、#18 | 越权修改会破坏去重、家族展开与修复范围，拒绝产物。 |
| `severity_hypothesis_initial` | #3 `candidate-discovery` | #4/#5 及全部下游 | #4/#5 只能另写最终定级，不得覆写初始假设；覆写会破坏“假设到定型”追溯，拒绝产物。 |
| 已登记的分段证据字段族：`discovery_reasoning_note`、`family_expansion_note` | #3 `candidate-discovery` 仅写发现依据 | #4-#9、#16、#18 | 这是已登记实际字段的证据分段统称，不存在名为 `evidence_chain` 的额外字段；其他阶段删除、替换或改写该段会破坏发现溯源，拒绝产物。 |
| `unified_semantic_refs`、`vuln_pattern_refs`、`ecosystem_mapping_refs`、`ontology_trace`、`knowledge_consultations`、`capability_gap_refs` | #3 `candidate-discovery` | #4-#9、#16、#18 | 越权修改会伪造知识引用或掩盖能力缺口，拒绝产物。`vuln_pattern_refs`只有命中`discoverable=complete`的`vuln-pattern`才能写入；`knowledge_consultations[]`区分`matched_pattern`与`matched_catalog_only`，后者不得称模式驱动发现。 |
| `cross_boundary_path` | #3 `candidate-discovery`分片写本WU已知路径段；宿主汇聚方只可在独立汇聚结果中补跨WU段，不得原地改WU原始事实 | #4-#9、#16、#18 | reviewer、下游或汇聚方改写原始分片会污染事实源；拒绝产物并重建汇聚结果。 |
| `knowledge_snapshot_id`、`knowledge_consultations` | #3引用run冻结知识快照并写查阅数组 | #4-#9、#16、#18 | 快照不一致或下游反写会破坏可复现性，拒绝产物。 |
| `cluster_ref` | #3 `candidate-discovery`（创建时写一次，引用其产生簇结论） | #4-#9、#16、#18 | 缺失或指向不可解析簇结论会破坏三记录闭包，拒绝产物。 |

## #4/#5 验证与定级

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `verification_baseline`、`candidate_specific_checklist`、`verification_methods` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 下游改写会改变验证事实，拒绝产物。每项方法绑定自己的tier、evidence_mode和evidence_refs；证据引用只能追加，不能删除。 |
| 已登记的分段证据字段族：`verification_baseline`、`candidate_specific_checklist`、`verification_methods` | #4/#5 `verification-and-rating` 仅写本阶段生成的验证与定级证据 | #3、#6-#9、#16、#18 | 这是已登记实际字段的证据分段统称，不存在名为 `evidence_chain` 的额外字段；其他阶段改写或任何阶段删除、替换已有证据引用会破坏审计链，拒绝产物。`independent_review_e1e2`、`severity_independent_review` `[deprecated since v0.3.0]`，现行复核字段为 `second_opinion_review`。 |
| `confidence_score`、`verification_verdict` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 跨阶段改判会绕过验证门，拒绝产物并返回 #4/#5。 |
| `impact_rating`、`likelihood_rating`、`suppression_flag` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 越权修改会污染严重度矩阵，拒绝产物。 |
| `final_severity`、`priority`、`cvss_vector` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 报告或修复阶段重新定级会产生冲突结论，拒绝产物。 |
| `control_assessment` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 越权修改会改变控制评估事实，拒绝产物。Guard/Policy Decision/Sanitizer/Encoder必须分别评估，合并为笼统"安全控制"判断属于结构性错误。 |
| `verification_knowledge_refs` | #4/#5 `verification-and-rating` | #6-#9、#16、#18 | 越权修改会伪造验证知识引用或掩盖排除条件，拒绝产物。`verification_method_ref`和`refutation_method_ref`引用vuln-pattern条目的验证/反证方法；`exclusion_conditions_checked`记录实际检查的排除条件。 |
| `review_artifact_ref` `[deprecated since v0.3.0]` | E1/E2 reviewer只写各自独立分片；#4/#5宿主核对身份和输入后仅引用并串行汇聚 | Gate、下游能力 | reviewer直接改主产物、预填结果或未核对即汇聚均拒绝。历史保留：E1/E2 重型分片复核已废弃，由 `second_opinion_review` 轻量第二意见取代。 |
| `verification_record_ref` | #4/#5 `verification-and-rating`（定级完成时写一次，引用本候选验证段） | #6-#9、#16、#18 | 缺失或指向不存在的验证段会破坏三记录闭包，拒绝产物。 |

## Check Unit与Gate字段

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `planning_snapshot`、`pre_execution_plan_ref`、`plan_created_at`、`plan_frozen_at`、`execution_started_at`、`plan_revision` | #3宿主在执行前冻结；冻结后只按补规划规则创建新revision | CU执行者、Gate | 执行者事后补写或缩减快照会伪造闭合，硬门拒绝。 |
| CU执行终态与证据字段 | 对应CU执行者只写自己的分片，宿主核实后汇聚 | Gate、报告 | 跨CU改写或范围缩写拒绝。 |
| `added_after_freeze`、`addition_reason`、`added_at`、`rework_round` | #3宿主发现新范围时写入新规划revision | Gate、报告 | 缺字段或未重过Gate时新增CU无效。 |
| Gate记录（`gate_result`、缺口、输入版本、证据引用） | 对应Gate执行方写独立Gate产物；顶层调度仅引用/投影 | 所有能力、报告 | 节点或reviewer直接改Gate记录、删除缺口均拒绝。 |

`candidate` 与 `finding` 共用同一累积记录，但`confirmed`只是验证终态。只有confirmed、存在活攻击面且`final_severity!=informational`时才进入finding语境；`finding_id`不是新ID，按#9/#19权威登记行写入`candidate_id`等值别名。`confirmed+informational`始终是candidate/code-hygiene item，无`finding_id`，由candidate累积结构与#4/#5产物替代持久化并在复扫重进#3/#4。

## #6 PoC

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `poc_id`、#6 PoC段的`candidate_ref`、`group_variant_note`、`evidence_composition`、`evidence_segments` | #6 `exploit-proof` | #7-#9、#18 | 下游修改会破坏 PoC 身份、候选关联或执行真实性，拒绝产物。此处不包含`external_claim_verification[].candidate_ref`。 |
| `source_evidence_ref`、`harm_minimization_note`、`isolation_note`、`optional_dependency_mock_note` | #6 `exploit-proof`；仅通过 `source_evidence_ref` 引用上游已登记证据字段，不修改 `verification_baseline` 等上游字段 | #7-#9、#18 | 修改上游证据、删除证据引用或改写隔离声明会造成安全与溯源风险，拒绝产物。 |
| `package_content`、`reexecution_check` | #6 `exploit-proof` | #7-#9、#18 | 越权修改会使证明包与验证记录不一致，拒绝产物。 |
| `tool_export_format` | #6 仅声明 PoC 可导出的源信息；具体外部映射由 #18 写入其 `export_artifact` | #7-#9；#18 只读源信息 | #18 反写 PoC 字段或 #6 伪造外部导出结果均拒绝。 |
| `attack_pattern_refs` | #6 `exploit-proof` | #7-#9、#18 | 越权修改会伪造攻击模式引用，拒绝产物。按semantic→vuln→生态→proof mode→Oracle选择条目；未匹配时留空并记录原因进入知识演进。 |

## #7 修复指导

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `remediation_scope_id`、`remediation_mode`、`fix_pattern_ref`、`hardening_cluster_basis` | #7 `remediation-guidance` | #8、#9、#16、#18 | 越权修改会改变修复边界或模式选择，拒绝产物。 |
| `priority_order_trace`、`patch_content`、`proposal_content`、`evidence_tag` | #7 `remediation-guidance` | #8、#9、#16、#18 | 报告层或外部工具改写会把投影伪装为修复事实，拒绝产物。 |
| `patch_application` | #7补丁应用步骤在本次授权下写入`applied`、目标类型、前后revision、artifact、时间和授权引用 | #7独立验证、#8、#9、#16、#18 | 补丁生成者预填、仅建议diff伪装已应用、前后revision相同或验证未绑定after revision均拒绝；缺失时禁止`final_result=fixed`。 |
| `fix_verification_result`、`bypass_review_result`、`final_result` | #7独立验证/复核步骤；仅在这些已登记修复字段中引用上游证据，不修改 `verification_baseline`、`source_evidence_ref` 等上游字段。`fix_verification_result.verification_mode=inferred`只记录静态证据链走查，不得冒充执行；`inherently_safe`仅可在#7记录新证据、回退#4且#4将原风险主张改判为`refuted`后写为历史投影 | #8、#9、#16、#18 | 补丁生成者自认证、静态走查冒充执行、#7单方推翻#4或修改上游证据均绕过验证门，拒绝产物。 |

## #8 报告投影

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `summary_triage_view`、`detailed_narrative_view`、`family_expansion_entries` | #8 `report-delivery`，仅写报告自己的段落 | 人工读者、#18 导出 | 报告层无权修正任何 #1-#7 上游字段；不一致时必须返回上游修正并重新投影，直接改写视为拒绝。 |
| `reviewed_surfaces_coverage` | #8 `report-delivery`，按上游状态确定性映射覆盖结果 | 人工读者、#18 导出 | 新增判断或改写上游 verdict/覆盖事实会制造双重真相，拒绝产物。 |
| `structural_hardening_link`、`harm_minimization_disclosure`、`zero_finding_statement` | #8 `report-delivery`，仅写报告自己的段落 | 人工读者、#18 导出 | 复制并修改上游提案、恢复敏感数据或以报告文本替代上游记录，均拒绝。 |
| `evidence_role_labels` | #8 `report-delivery`，仅对已登记证据引用写报告角色标签 | 人工读者、#18 导出 | 编造证据引用或修改上游证据会制造虚假叙事，拒绝产物。 |
| `report_record_ref` | #8 `report-delivery`（投影时写，引用详情文件与机器字段行） | 人工读者、#18 | 缺失或引用不一致会破坏三记录闭包，拒绝产物。 |

#8无`finding_id`写权限，始终以`candidate_id`投影；仅当#9台账已存在等值别名时可只读显示，不得生成或回填。

## #9/#19 生命周期治理

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `finding_id` | #9/#19 `lifecycle-governance`；仅对`verification_verdict.value=confirmed`、存在活攻击面且`final_severity!=informational`的finding写为`candidate_id`等值别名；包括`ignore`，排除informational | #8、#16、#18 及其他消费方 | 对未确认或代码卫生记录生成别名、跳过`ignore`显式处置、创建第二套 ID 或写入不同值会断裂身份，拒绝产物。 |
| `finding_fingerprint` | #9/#19 `lifecycle-governance` 确定性预筛选生成；仅用于跨扫描身份匹配，不替代 `candidate_id` | #8、#16、#18 及其他消费方 | 将指纹当作主 ID、手工改写或由外部系统反写会污染身份匹配，拒绝产物。 |
| `lifecycle_status`、`disposition` | #9/#19 `lifecycle-governance`；需人工授权的状态仅在授权齐备后写入 | #8、#16、#18 | 越权状态转移或缺少 actor/reason/date/review_date 会绕过治理门，拒绝。 |
| `verification_result`、`identity_match` | #9/#19 `lifecycle-governance` | #8、#16、#18 | 改写复扫核实或身份匹配依据会污染历史基线，拒绝产物。 |
| `coverage_diff`、`baseline_delta` | #9/#19 `lifecycle-governance` | #8、#16、#18 | 报告只能投影告警；越权改写会掩盖覆盖下降，拒绝产物。 |

## #18 外部工具集成

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `trigger_scenario`、`external_signal_source` | #18 `external-tool-integration` | #1、#3、#4、#8、#9 | 缺失来源或由上游伪造会混淆外部声明与本系统事实，拒绝产物。 |
| `dependency_vuln_signal` | #18 `external-tool-integration` | #1、#3、#4；其只能作为补充信号消费 | 将外部信号直接改写为 confirmed finding 会绕过 #4，拒绝产物。 |
| `external_claim_verification`（含其嵌套`candidate_ref`与`verification_result_ref`） | #18 仅记录外部原始主张及对#3 candidate、#4验证产物的引用；被引用实体仍分别由#3/#4写入 | #1、#3、#8、#9 | #18创建或改写`candidate_id`/`location`/`root_cause_group_id`等#3字段、复制或覆盖#4结论、删除原始主张，均拒绝。 |
| `export_artifact`、`tracker_write_result` | #18 `external-tool-integration`；D可引用调用前既有或本次C生成的版本化artifact，收到tracker写入请求即写结果记录，只有本次`granted`可实际写入 | #8、#9 及人工读者 | artifact来源/版本缺失、`not_granted`时执行写入或反写上游字段均拒绝；`not_granted+not_executed`是合法记录。 |

## #16 知识演进

| 字段 | 唯一写权限方 | 只读方 | 违规后果 |
|---|---|---|---|
| `candidate_pool`、`knowledge_base_snapshot`、`installation_scope`、`deprecation_signal` | 调用方在调用 #16 前写入；`candidate_pool[]`必须为`{source_audit_id: string, candidate: object}`，其中`source_audit_id`由调用方/编排上下文写，`candidate`完整引用candidate-finding；#16全部只读 | #16 `knowledge-evolution`、人工决策方及知识库写入步骤 | #16 创建或改写调用输入会伪造审计场景、候选、知识现状、部署范围或弃用信号，拒绝产物。 |
| `human_decision` | 人工授权方写入；阶段 A 可为空数组，阶段 B 在 proposal 生成后提交决定记录；#16 始终只读 | #16 `knowledge-evolution` 及全部后续消费方 | #16 代写、改写或伪造人工决定会绕过人工门，拒绝产物。 |
| `promotion_proposals`、`deprecation_proposals` | #16 `knowledge-evolution` 仅生成提议；`scenario_summaries`由包装层`source_audit_id`派生，`verification_evidence_refs`从candidate既有验证字段中的`evidence_refs`汇集，二者均为提议输出字段 | 人工决策方及知识库写入步骤 | 自动落盘、伪造场景/证据或删除旧知识会绕过人工门，拒绝产物。 |
| `promotion_decisions`、`deprecation_decisions` | #16 仅在消费真实 `human_decision` 后写入执行结果 | 全部后续消费方 | 伪造 decision_ref、重复承载人工决定或写入与决定不符的结果会破坏审计性，拒绝产物。 |
| `scope_assignment` | #16 `knowledge-evolution`，按安装范围和人工批准结果写入 | 知识库消费方 | 未经显式共享配置扩大范围会造成跨项目数据泄露，拒绝产物。 |
| `evidence_strength_disclosure` | #16 `knowledge-evolution` | 全部后续消费方 | 删除或弱化证据局限会夸大机制成熟度，拒绝产物。 |
| `knowledge_entry_states` | #16 `knowledge-evolution`；按 `knowledge_entry_id` 写入注册表定义的状态，后续状态变更仅在对应人工决定批准时执行 | 所有知识库消费方 | 未经批准改变状态、写入无法关联条目的状态或物理删除条目会绕过人工门并破坏追溯，拒绝变更。 |
| `knowledge_evidence_history` | #16 `knowledge-evolution` 仅追加历史证据条目 | 其他所有阶段及知识库消费方 | 改写或删除历史条目会破坏知识演进追溯，拒绝变更。 |
## v0.11.0 账本列级写权限（D10）

以下 5 个账本按列级登记唯一写权限方；未列为写权限方的角色对相应列只读。全部账本的只读方为 `gate-1.py`（宿主执行，LLM 不可写）。列序以 `gate-1.py` 方程「schema 全等」校验的 header 契约为权威。

### flow_edges.tsv

列：`source_id | sink_id | direction | hops | evidence_refs | judged_by | timestamp`

| 列 | 唯一写权限方 | 只读方 |
|---|---|---|
| `source_id`、`sink_id`、`direction`、`hops`、`evidence_refs`、`judged_by`、`timestamp`（全部列） | WU subagent（逐 sink 回溯/前向时落盘 reachable/blocked_at/no_path 边及证据引用） | `gate-1.py`（方程「flow 边值域」「flow 边节点存在」「候选边支撑」「剪枝边一致性」只读校验） |

越权改写边值域或伪造可达边会破坏图投影与候选边支撑校验，拒绝产物。

### pruning_ledger.tsv

列：`operator | criterion | scope | evidence | judged_by | timestamp | a2_verified`

| 列 | 唯一写权限方 | 只读方 |
|---|---|---|
| `operator`、`criterion`、`scope`、`evidence`、`judged_by`、`timestamp` | 类剪枝角色（S1/S2/S3 类级剪枝）写入剪枝判定与证据 | `gate-1.py`（方程「schema 全等」「剪枝 A2 复核」「剪枝边一致性」「枚举锚定」只读校验） |
| `a2_verified` | A2 独立验证 subagent 复核后写入 `true`/`false` | `gate-1.py`、类剪枝角色（只读） |

剪枝角色预填 `a2_verified` 或 A2 未复核即标 `true` 会伪造独立性，拒绝产物。

### batch_progress.tsv

列：`batch_num | status | wus_total | wus_done | findings_count`

| 列 | 唯一写权限方 | 只读方 |
|---|---|---|
| `batch_num`、`status`、`wus_total`、`wus_done`、`findings_count`（全部列） | 主代理（批循环调度方逐批覆盖更新） | `gate-1.py`（方程「batch_progress 完成率」「短路质量检查」「看板行数」只读校验） |

WU subagent 不得直接写 batch_progress；主代理须在每批完成后覆盖更新，伪造完成率会破坏进度可见性，拒绝产物。

### gate_progress.tsv

列：`sub_task | gate_eq | result | timestamp`

| 列 | 唯一写权限方 | 只读方 |
|---|---|---|
| `sub_task`、`gate_eq`、`result`、`timestamp`（全部列） | 主代理（逐子任务 gate 对账后追加痕迹行） | `gate-1.py`（方程「gate_progress 痕迹」只读校验） |

子任务未跑 gate 即写 result=PASS 或事后补写会伪造 gate 痕迹，拒绝产物。

### audit_log.tsv

列：`check_point_id | basis_id | direction | result | evidence_type | evidence_ref | reviewed_at`

| 列 | 唯一写权限方 | 只读方 |
|---|---|---|
| `check_point_id`、`basis_id`、`direction`、`result`、`evidence_type`、`evidence_ref`、`reviewed_at`（全部列） | WU subagent（执行检查点时逐观察实时追加，一行一观察） | `gate-1.py`（方程「audit 双向覆盖」「引用可解析」「时序检查」「audit_log 追加单调性」只读校验） |

主代理或其他角色改写、删除或重排已有观察行会破坏证据先落盘后引用的时序与追加单调性，拒绝产物。

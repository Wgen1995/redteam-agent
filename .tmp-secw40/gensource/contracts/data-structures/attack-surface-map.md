# 攻击面范围地图结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义 #2 三层攻击面枚举、零命中复核和知识反馈的结构化地图。  
**生产者**：#2 `scope-and-context` 的攻击面子任务。  
**消费者**：#3-#9、#16、#18，以及报告和外部导出消费方。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。所有数组字段均必须出现；无条目时写空数组，不得省略。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | #2 攻击面子任务 | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前产物完成程度。 |
| `version` | `string` | 是 | #2 攻击面子任务 | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | #2 攻击面子任务 | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `file_level_inventory` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{path: string, file_kind: string, readability: string, has_executable_behavior: boolean, evidence_refs: string[]}`；`file_kind` 见枚举注册表 [`file_kind`](../enum-registry.md#file_kind)，`readability` 见 [`readability`](../enum-registry.md#readability)；除 `.git` 外全量枚举 | 文件级 100% 兜底清单。 |
| `named_category_scan_results` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{category_id: string, category_name: string, category_kind: string, checklist_source: string, scanned_scope: string[], hit_refs: string[], hit_count: integer}`；`category_kind` 见枚举注册表 [`category_kind`](../enum-registry.md#category_kind)，`hit_count` 非负且等于 `hit_refs` 数量 | 逐命名类别扫描结果，零命中类别也保留。 |
| `zero_hit_review_flags` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{category_id: string, review_status: string, review_method: string, evidence_refs: string[]}`；`review_status` 见枚举注册表 [`review_status`](../enum-registry.md#review_status)；仅对应零命中类别 | 零命中的强制复核记录。 |
| `open_semantic_findings` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{semantic_category: string, location_refs: string[], behavior_summary: string, evidence_refs: string[]}`；这里的 finding 仅是“开放语义线索”的历史命名，不表示 verified finding，不产生 `finding_id` | 开放式语义复查发现的清单外线索。 |
| `methodology_disclosure` | `object` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 最少为 `{methods_used: string[], categories_checked: string[], temporary_checklist_used: boolean, residual_risk: string, limitations: string[]}`；`residual_risk` 非空 | 如实披露方法、清单来源、范围边界和残余风险。 |
| `feedback_to_checklist` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #16 及其他下游 | 每项最少为 `{proposed_category: string, source_signal_refs: string[], rationale: string, suggested_scope: string}`；`source_signal_refs` 仅引用本范围地图中的文件、函数或检查项信号，不引用后续 `candidate_id`/`finding_id`；无新类别时为空数组 | 供 #16 评估的清单补充素材，不能直接反写知识库。 |
| `ontology_version` | `string` | 是 | #2 攻击面子任务 | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH`，引用 `knowledge/ontology/_index.md` 当前版本 | 本次扫描消费的本体版本，供下游核对知识基座一致性。 |
| `knowledge_manifest_version` | `string` | 是 | #2 攻击面子任务 | 所有消费者 | 日期字符串 `YYYY-MM-DD`，引用 `knowledge/industry-catalog/industry-source-manifest.md` 冻结日期 | 本次扫描消费的知识manifest版本。 |
| `asset_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{stable_id: string, ontology_ref: string, location_refs: string[], relationship_refs: string[], evidence_refs: string[]}`；`ontology_ref` 引用 `ONT-ASSET`；无条目时写空数组，不得省略字段本身 | 资产实例清单。 |
| `trust_boundary_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`；`ontology_ref` 引用 `ONT-TRUST-BOUNDARY`；无条目时写空数组 | 信任边界实例清单。 |
| `surface_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol: string`（稳定符号名）、`component: string`（所属组件/模块名）、`contract: string`（服务契约标识，如 RPC 服务名+方法名+版本）、`data_shape: string`（数据结构签名，如 DTO 类名）、`storage_ref: string`（关联存储位置，如表名/缓存键模式）；`ontology_ref` 引用 `ONT-SURFACE`；无条目时写空数组 | 攻击面实例清单。`symbol`/`component`/`contract`/`data_shape`/`storage_ref` 供跨 WU 汇聚按稳定标识连接，见 [`../../shared/cross-boundary-analysis.md`](../../shared/cross-boundary-analysis.md)。 |
| `entry_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol`/`component`/`contract`/`data_shape`/`storage_ref`（语义同 `surface_instances`）；`ontology_ref` 引用 `ONT-ENTRY`；无条目时写空数组 | 入口实例清单。`symbol` 供跨 WU 汇聚按稳定符号连接调用边。 |
| `source_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol`/`component`/`contract`/`data_shape`/`storage_ref`（语义同 `surface_instances`）；`ontology_ref` 引用 `ONT-SOURCE`；无条目时写空数组 | 数据源实例清单。`symbol`/`data_shape` 供跨 WU 汇聚按稳定符号连接 Source 到下游传播路径。 |
| `propagation_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol`/`component`/`contract`/`data_shape`/`storage_ref`（语义同 `surface_instances`）；`ontology_ref` 引用 `ONT-PROPAGATION`/`ONT-TRANSFORMATION`/`ONT-STORAGE`；无条目时写空数组 | 传播/转换/存储实例清单。`storage_ref` 供跨 WU 汇聚按存储位置建立写入到读取的二阶边。 |
| `control_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol`/`component`/`contract`/`data_shape`/`storage_ref`（语义同 `surface_instances`）；`ontology_ref` 引用 `ONT-GUARD`/`ONT-POLICY-DECISION`/`ONT-SANITIZER`/`ONT-ENCODER`；**Guard、Policy Decision、Sanitizer、Encoder 必须分别识别，不得合并为笼统的"安全控制"**；无条目时写空数组 | 控制实例清单（四类分别记录）。`symbol` 供跨 WU 汇聚按稳定符号连接 Guard/Sanitizer/Encoder 到调用边和传播路径。 |
| `sink_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`，另可选含 `symbol`/`component`/`contract`/`data_shape`/`storage_ref`（语义同 `surface_instances`）；`ontology_ref` 引用 `ONT-SINK`/`ONT-STATE-TRANSITION`/`ONT-RESOURCE-CONSUMPTION`；无条目时写空数组 | 汇点/状态转换/资源消耗实例清单。`symbol`/`storage_ref` 供跨 WU 汇聚按稳定符号和存储位置连接 Sink 到上游 Source 的二阶边。 |
| `observable_oracle_instances` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项结构同 `asset_instances`；`ontology_ref` 引用 `ONT-OBSERVABLE-ORACLE`；无条目时写空数组 | 可观察预言机实例清单。 |
| `security_impact_hypotheses` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{stable_id: string, ontology_ref: string, hypothesis: string, location_refs: string[], relationship_refs: string[], evidence_refs: string[]}`；`ontology_ref` 引用 `ONT-SECURITY-IMPACT`；无条目时写空数组 | 安全影响假设清单。 |
| `knowledge_gaps` | `array&lt;object&gt;` | 是 | #2 攻击面子任务 | #3-#9、#16、#18 | 每项最少为 `{gap_type: string, missing_category: string, expected_ontology_ref: string, description: string, entered_open_semantic_review: boolean, evidence_refs: string[]}`；某些 Surface/Entry/Sink 类别在权威索引中不存在时必须记录；无条目时写空数组 | 知识缺口记录，必须进入开放语义复查。 |

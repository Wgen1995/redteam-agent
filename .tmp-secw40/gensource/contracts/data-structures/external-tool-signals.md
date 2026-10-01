# 外部工具信号结构契约

> 历史编号见 [`../README.md`](../README.md) 历史编号映射。

**职责**：定义 #18 依赖漏洞信号、外部主张复核、格式导出和工单写入结果，隔离外部声明与 GenSource 自身结论。  
**生产者**：#18 `external-tool-integration`；场景 B 的 candidate 由 #3 创建、验证结果由 #4 写入，#18 仅保存引用。  
**消费者**：#1、#3、#4、#8、#9，以及人工审阅方和外部系统适配器。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。依赖信号适用性使用注册表 `dependency_applicability`，不等同于 `verification_verdict`。

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | #18 `external-tool-integration` | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前外部集成产物完成程度。 |
| `version` | `string` | 是 | #18 `external-tool-integration` | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | #18 `external-tool-integration` | 调度方、所有下游 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `trigger_scenario` | `string` | 是 | #18 `external-tool-integration` | #1、#3、#4、#8、#9 | 见枚举注册表 `trigger_scenario` | 本次实际触发场景；多场景分别产出记录。未触发时无本伴生能力记录。 |
| `external_signal_source` | `object` | 是 | #18 `external-tool-integration` | #1、#3、#4、#8、#9 | 产出记录时必填；最少为 `{source_id: string, source_type: string, source_name: string, source_version: string \| null, invocation_or_item_id: string, queried_at: datetime}`；`source_id` 非空并在本产物内唯一 | 外部信号、主张或动作的可追溯来源。 |
| `dependency_vuln_signal` | `array&lt;object&gt;` | 场景 A 必填 | #18 `external-tool-integration` | #1、#3、#4 | 每项最少为 `{package_name: string, package_version: string, cve_id: string \| null, applicability: string, affected_version_range: string \| null, source_ref: string, queried_at: datetime, applicability_evidence_refs: string[]}`；`source_ref` 必须引用顶层 `external_signal_source.source_id`，不得复制一份独立来源描述；`queried_at` 为该条实际查询时间；`applicability` 见枚举注册表 `dependency_applicability`；无 CVE 时 `cve_id=null` 且为 `no_match`；存疑或争议值不计入确认数量 | 专用工具返回并经轻量版本适用性核实的补充信号，不是 finding。 |
| `external_claim_verification` | `array&lt;object&gt;` | 场景 B 必填 | #18 仅记录外部原始主张及引用 | #1、#3、#8、#9 | 每项最少为 `{claim_id: string, original_claim: object, source_ref: string, candidate_ref: string, verification_result_ref: string, accepted_as_signal: boolean}`；`source_ref` 必须引用顶层 `external_signal_source.source_id`；`candidate_ref`必须引用#3按[`candidate-finding.md`](candidate-finding.md)创建的`candidate_id`，`verification_result_ref`必须引用该candidate对应的#4权威验证产物；#18不得内嵌、复制或改写#3/#4字段；`original_claim`至少含`{description: string, severity: string \| null, verdict: string \| null}` | 原始主张永久保留；#18无权创建candidate结构或自行改判验证结论。 |
| `export_artifact` | `object` | 场景 C 必填 | #18 `external-tool-integration` | #8、#9、人工读者 | 最少为 `{format: string, artifact_ref: string, artifact_version: string, source_data_refs: string[], mapping_rule_version: string, missing_fields: string[]}`；`artifact_ref`唯一定位产物，`artifact_version`标识该产物版本，`source_data_refs`非空并引用实际投影来源；只允许确定性投影，不得编造缺失值 | 外部格式产物、来源及版本。 |
| `tracker_write_result` | `object` | 场景 D 必填 | #18 `external-tool-integration` | #8、#9、人工读者 | 收到写入请求即触发场景D并创建本记录，不以授权为触发前提。最少为 `{export_artifact_ref: string, export_artifact_version: string, consent_status: string, execution_status: string, external_ticket_id: string \| null, error: string \| null}`；artifact引用和版本必须匹配一个调用前已存在或本次联合触发C生成的合约有效`export_artifact`。合法状态组合不变：`granted+succeeded`时ticket ID非空且error为null；`granted+failed`时error非空且ticket ID为null；`granted+not_executed`仅允许授权后受环境或权限阻塞；`not_granted+not_executed`时ticket ID与error均为null。无论artifact来源如何，仅本次`granted`才可实际写入 | D可独立消费既有artifact；无既有artifact时先联合触发C。外部状态不得反写上游事实。 |

`questionable` 表示版本适用性存疑，`disputed` 表示数据库或权威来源明确存在争议；二者都必须保留来源和查询时间，但不得计为 confirmed finding。外部主张必须先由#3形成合约有效candidate，再经#4验证；#18只保存两者引用。

# 全局枚举注册表

本文件是 GenSource 所有固定机器枚举的单一权威源；开放扩展标识除外。固定枚举包括只在单个数据结构中使用的局部值集，数据结构和 SKILL 只能引用本文件，不得维护第二份固定值清单。开放扩展标识（例如 `refutation_category`）不属于固定枚举，不在此封闭。机器判定字段统一使用英文 `snake_case`，不得将中文说明、展示文案或 `N/A` 写入机器值。

明确保留两个格式例外：

- `priority` 使用 `P0`/`P1`/`P2`/`P3`，因为 P 级优先级是行业通用表示法，改为小写会削弱辨识度并破坏既有互操作习惯。
- `evidence_tag` 使用 `Observed`/`Inferred`/`Proposed`，因为它们是既有证据三段标签的展示型固定术语，需要在人读材料中保持稳定外观。

### v0.3.0 废弃枚举族（物理保留不删除）

自 v0.3.0（检测引擎 v2 重构）起，以下枚举族废弃，标注 `[deprecated since v0.3.0]` 后物理保留供历史消费方参考，不再是新产物的写入目标：

- `anchor_type`（三级锚定 `full`/`work_unit`/`lightweight`）——设计 §7.2 删除三级锚定分类，恢复即执行完整锚定一段；
- `e2_trigger_reason`（E2 双向独立重建 7 触发值）——设计 §4.4 将 E1/E2 重型分片复核简化为轻量第二意见 + High/Critical 可选对称反转；
- `wu_trigger` 相关（`wu_trigger_evaluation` 四布尔等，本注册表无对应枚举，字段物理保留在 [`field-ownership-table.md`](field-ownership-table.md)）——设计 §10 删除该四布尔。

## verification_verdict

| 机器值 | 语义 |
|---|---|
| `confirmed` | 当前记录的代码事实或风险主张经证据确认；这是验证终态而非finding分类。仅有活攻击面且非`informational`者成为finding；无活攻击面代码事实按`informational` candidate/code-hygiene语义处理。 |
| `unconfirmed` | 当前证据不足以确认或证伪，结论仍需跟进。 |
| `refuted` | 反证成立，候选已被证伪；记录仍须保留。 |

## lifecycle_status

| 机器值 | 语义 |
|---|---|
| `open` | 发现有效且尚未进入已完成处置。 |
| `in_remediation` | 修复工作正在进行。 |
| `fixed_verified` | 已修复，并通过真实动态复验。 |
| `fixed_unverified` | 已修复或静态证据链已确认断开，但尚未完成真实动态复验。 |
| `risk_accepted` | 经授权接受风险并保留处置依据。 |
| `false_positive` | 经授权认定为误报。 |
| `duplicate` | 经授权认定与另一发现重复。 |
| `wont_fix` | 经授权决定不修复。 |

### lifecycle_status 条件子集

- **抑制态**：`risk_accepted`、`false_positive`、`duplicate`、`wont_fix`。首次进入该子集必须遵守生命周期台账的人工授权与处置留痕约束。
- **修复态**：`fixed_verified`、`fixed_unverified`。进入该子集必须携带生命周期台账要求的独立复验记录；二者的动态/静态证据边界以台账契约为准。

## lifecycle_state

候选累积结构的生命周期推进状态（[`data-structures/candidate-finding.md`](data-structures/candidate-finding.md) 的 `lifecycle_state` 字段，各阶段按生命周期推进写入）。与 [`lifecycle_status`](#lifecycle_status) 不同：`lifecycle_state` 描述候选从创建到报告的落盘推进态，`lifecycle_status` 描述 finding 在生命周期治理（#9）中的处置状态。

| 机器值 | 语义 |
|---|---|
| `created` | 阶段1 候选创建，落盘 `candidates.tsv`。 |
| `verified` | 阶段2 验证完成，落盘 `verification-summary.md`。 |
| `rated` | 阶段2 严重度定级完成。 |
| `reported` | 阶段3 报告投影完成，落盘 `findings/V{N}.md`。 |

## remediation_mode

| 机器值 | 语义 |
|---|---|
| `tactical_patch` | 对单个根因组实施窄范围战术修复。 |
| `structural_hardening_proposal` | 对共享不变量、信任边界或控制归属问题提出架构性加固方案。 |

架构聚类评估失败不是独立修复模式：在相应`tactical_patch`记录的`hardening_cluster_basis.structural_hardening_recommended=false`表达，不产生空修复记录或独立`final_result`。

## human_decision

| 机器值 | 语义 |
|---|---|
| `approved` | 人工批准提议的状态变更或知识写入。 |
| `rejected` | 人工拒绝提议，并保留拒绝理由。 |
| `deferred` | 人工暂缓决定，留待后续复核。 |

## final_result

| 机器值 | 语义 |
|---|---|
| `fixed` | 修复已实施并得到本阶段认可；必须有`patch_application.applied=true`、`before_revision != after_revision`，且修复验证与独立绕过复核均绑定`after_revision`并通过。可由真实动态复验，或独立确认修复后静态证据链已断得出；后者进入生命周期时只能先为 `fixed_unverified`。 |
| `inherently_safe` | #7发现新证据并回退#4后，#4确认原风险主张不成立或已有控制有效的历史投影结果；#7不可单方写入，此记录不再称confirmed finding。 |
| `needs_human_decision` | 自动流程无法安全定夺，需要人工选择。 |

## discovery_source

该字段可多选；同一候选被多种机制命中时保留全部值。

| 机器值 | 语义 |
|---|---|
| `pattern_driven` | 通过已登记漏洞模式匹配发现。 |
| `business_logic` | 通过预期业务行为与实际实现的语义偏差发现。 |
| `lateral_diff` | 通过同类实现的横向差异对照发现。 |

## mode

| 机器值 | 语义 |
|---|---|
| `executed` | PoC 已在允许的隔离环境中实际执行并记录结果。 |
| `inferred` | PoC 仅依据证据推导，未声称实际执行。 |

PoC 字段级 `mode` 已被 [`evidence_composition`](#evidence_composition) + [`evidence_segments`](#evidence_mode)（各段 `evidence_mode`）取代；本枚举保留为 [`verification_mode`](#remediation_verification_result) 和 [`evidence_mode`](#evidence_mode) 的共享值集定义，不再作为 PoC 记录的直接字段名。

## status `[deprecated since v0.2.0]`

| 机器值 | 语义 |
|---|---|
| `completed` | 阶段在声明范围内完整执行。 |
| `partial` | 阶段仅完成部分范围，产出包含已完成范围和缺口。 |
| `interrupted` | 阶段执行被中断，`resume_context` 提供续跑位置。 |

自 v0.2.0 起，本枚举描述的两个维度已拆分为独立命名空间：整次运行的生命周期用 [`run_status`](#run_status)，单个阶段自身的完成程度用 [`stage_result`](#stage_result)（不再包含 `interrupted`；阶段被上级运行中断时改记为 `stage_result=partial`）。`data-structures/*.md` 中原通用 `status` 字段已迁移为 `stage_result`；本节物理保留供尚未迁移的历史消费方参考，不再是新产物的写入目标。

## run_status

| 机器值 | 语义 |
|---|---|
| `running` | 运行进行中（v0.3.0 起 run 创建即为 running，不再区分 initialized）。 |
| `completed` | 整次运行已完成并产出报告。 |
| `blocked` | 缺少用户决定、权限或关键输入，条件满足后可继续。 |
| `interrupted` | 运行非正常中断，可按恢复协议核实后续跑。 |
| `initialized` `[deprecated since v0.3.0]` | 物理保留：run 创建即为 running，不再使用 initialized 细分。 |

该枚举仅描述整次审计运行(run)的生命周期状态，记录在 `run-state.md` 的 `run_status` 字段；不得与 `stage_result`、`gate_result`、`work_unit_status` 混用或相互替代。

## stage_result

| 机器值 | 语义 |
|---|---|
| `completed` | 阶段在声明范围内完整执行。 |
| `partial` | 阶段仅完成部分范围，产出包含已完成范围和缺口。 |
| `not_applicable` | 当前阶段在本次运行语境下不适用。 |

该枚举仅描述单个能力/阶段(stage)产出的完成程度，不能与 `run_status` 混用：例如整次运行被记为 `run_status=interrupted` 时，当前正在进行的阶段应把自己的产出记为 `stage_result=partial` 并携带完整 `resume_context`，不得把 `interrupted` 写进 `stage_result`。

## gate_result

| 机器值 | 语义 |
|---|---|
| `pass` | Gate判定通过。 |
| `rework` | Gate判定需要返工，须列出具体缺口。 |
| `blocked` | Gate判定因缺少用户决定、权限或关键输入而受阻。 |
| `pass_with_gaps` | 自动返工达到轮次上限仍未收敛，带已披露缺口通过。 |

该枚举仅描述质量Gate（Gate-1/Gate-2）的判定结果，权威语义以 [`shared/quality-gates.md`](../shared/quality-gates.md) 为准，不得与 `run_status`、`stage_result`、`work_unit_status` 混用。

## work_unit_status

> `[deprecated since v0.3.0]` WU 状态改由分片输出文件存在性判定（未开始/运行中/已完成/已验证/失败），见 `work-unit-manifest-template.md`。以下值物理保留供历史产物解读。

| 机器值 | 语义 |
|---|---|
| `pending` | Work Unit 已创建但尚未派发执行。 |
| `running` | Work Unit 正在执行中。 |
| `completed` | Work Unit 分片已被宿主成功汇聚进主产物。 |
| `blocked` | Work Unit 因缺少用户决定、权限或关键输入而受阻。 |
| `interrupted` | Work Unit 执行被中断。 |
| `not_applicable` | Work Unit 在当前语境下不适用。 |

该枚举仅描述单个 Work Unit 的执行状态，权威语义以 [`work-unit-manifest-template.md`](work-unit-manifest-template.md) 为准，不得与 `run_status`、`stage_result`、`gate_result` 混用。

## capability_status

| 机器值 | 语义 |
|---|---|
| `available` | 能力已探测并可用。 |
| `unavailable` | 能力不可用。 |
| `degraded` | 能力可用但存在已披露限制。 |
| `unknown` | 尚无充分事实判定。 |

## runtime_verification

| 机器值 | 语义 |
|---|---|
| `allowed` | 本次运行已获得明确授权且能力探测与安全门允许动态验证。 |
| `denied` | 本次运行未获授权或安全门不允许动态验证。 |

## resume_mode

| 机器值 | 语义 |
|---|---|
| `auto` | 查找并核实可信的未完成运行，满足恢复协议时续跑。 |
| `never` | 不复用未完成运行，创建新运行。 |

## gate_decision

| 机器值 | 语义 |
|---|---|
| `granted` | 动态执行安全门允许所请求的执行。 |
| `denied` | 动态执行安全门拒绝所请求的执行。 |

## execution_fallback

| 机器值 | 语义 |
|---|---|
| `static_only` | 动态执行不可用时仅使用静态推导证据。 |

## manifest_status

| 机器值 | 语义 |
|---|---|
| `active` | Manifest 是当前 revision 的有效调度清单。 |
| `superseded` | Manifest 已被新 revision 的清单替代，只读保留供追溯。 |

## source_status

| 机器值 | 语义 |
|---|---|
| `frozen` | 来源版本和快照身份已冻结，可供本批次稳定引用。 |

## boundary_origin

| 机器值 | 语义 |
|---|---|
| `external` | 数据来自当前系统或授权范围之外。 |
| `internal` | 数据来自当前系统和 WU 内部。 |
| `cross_wu` | 数据来自另一个 Work Unit。 |
| `unknown` | 现有证据不足以确定来源。 |

## symbol_kind

该枚举用于 [`work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md) 中 `inputs`/`outputs` 的 `symbol_kind` 字段，取值与 [`boundary_origin`](#boundary_origin) 的 `origin` 用法对齐。

| 机器值 | 语义 |
|---|---|
| `external` | 符号来自当前系统或授权范围之外。 |
| `internal` | 符号来自当前系统和 WU 内部。 |
| `cross_wu` | 符号来自另一个 Work Unit。 |
| `unknown` | 现有证据不足以确定符号来源。 |

## boundary_mapping_kind

| 机器值 | 语义 |
|---|---|
| `dto_field` | DTO 字段映射。 |
| `orm_column` | ORM 字段到数据库列的映射。 |
| `serialization_field` | 序列化字段映射。 |
| `message_field` | 消息体字段映射。 |
| `rpc_param` | RPC 参数映射。 |
| `graphql_field` | GraphQL 字段映射。 |

## boundary_evidence_kind

| 机器值 | 语义 |
|---|---|
| `code_reading` | 源码读取证据。 |
| `config_reading` | 配置读取证据。 |
| `tool_output` | 确定性工具输出证据。 |
| `type_inference` | 基于已读类型关系的推导证据。 |
| `pattern_match` | 已登记模式的匹配证据。 |

## boundary_confidence

| 机器值 | 语义 |
|---|---|
| `high` | 边界事实有直接且完整的证据支撑。 |
| `medium` | 主要连接有证据支撑，但仍存在已披露限制。 |
| `low` | 边界连接可能不完整，必须向汇聚方和下游披露。 |

## anchor_type [deprecated since v0.3.0]

| 机器值 | 语义 |
|---|---|
| `full` | 完整运行锚点。 |
| `work_unit` | Work Unit粒度锚点。 |
| `lightweight` | 子步骤轻量锚点。 |

自 v0.3.0 起废弃：三级锚定分类（full/work_unit/lightweight）已被删除，恢复即执行"完整锚定"一段（见设计 §7.2）。本节物理保留供历史消费方参考，不再是新产物的写入目标。

## confirmation_policy

| 机器值 | 语义 |
|---|---|
| `interactive_confirmed` | 交互模式已获得用户确认。 |
| `conservative_continue` | 非交互模式按最小范围、只读和保守假设继续。 |

## boundary_edge_kind

| 机器值 | 语义 |
|---|---|
| `direct_call` | 直接函数或方法调用。 |
| `interface_dispatch` | 接口或多态分发。 |
| `callback` | 回调或事件处理调用。 |
| `dependency_injection` | 依赖注入解析。 |
| `reflection` | 反射或动态分发。 |
| `generated_code` | 生成代码连接。 |
| `storage_edge` | 跨存储媒介连接。 |
| `transport_edge` | 跨传输媒介连接。 |
| `storage_read` | 待解析存储读取连接。 |
| `transport_consume` | 待解析传输消费连接。 |
| `cross_repo_contract` | 跨仓服务契约连接。 |

## boundary_storage_kind

| 机器值 | 语义 |
|---|---|
| `database` | 数据库。 |
| `cache` | 缓存。 |
| `file` | 文件。 |
| `object_storage` | 对象存储。 |

## boundary_transport_kind

| 机器值 | 语义 |
|---|---|
| `message_queue` | 消息队列。 |
| `event_bus` | 事件总线。 |
| `rpc` | RPC或REST服务调用。 |
| `graphql` | GraphQL。 |
| `websocket` | WebSocket。 |

## consultation_result

| 机器值 | 语义 |
|---|---|
| `matched_pattern` | 命中完整可发现漏洞模式。 |
| `matched_catalog_only` | 只命中语义目录，不能称模式驱动发现。 |
| `not_matched` | 已查read-set但未匹配。 |
| `index_coverage_conflict` | 索引与覆盖声明冲突，禁止有效命中。 |

## control_assessment_result

| 机器值 | 语义 |
|---|---|
| `effective` | 控制有效。 |
| `ineffective` | 控制存在但无效或可绕过。 |
| `absent` | 适用但控制缺失。 |
| `not_applicable` | 该控制类别不适用并附理由。 |

## lifecycle_change_kind [deprecated since v0.3.0]

> 自 v0.3.0 起废弃：由 [`lifecycle-ledger`](data-structures/lifecycle-ledger.md) 的 `change_kind` 三值子集（`added`/`modified`/`deleted`）承载。以下值物理保留供历史消费方参考，不再是新产物的写入目标。

| 机器值 | 语义 |
|---|---|
| `source_changed` | Source或入口变化。 |
| `sink_changed` | Sink或危险操作变化。 |
| `caller_changed` | 调用者或路由变化。 |
| `boundary_changed` | 存储、传输或跨WU边变化。 |
| `control_changed` | 安全控制变化。 |
| `dependency_changed` | 依赖或生态版本变化。 |
| `added` | 文件或对象新增。 |
| `modified` | 文件或对象修改。 |
| `deleted` | 文件或对象删除。 |

## lifecycle_trigger_kind [deprecated since v0.3.0]

> 自 v0.3.0 起废弃：由 [`lifecycle-ledger`](data-structures/lifecycle-ledger.md) 的 `trigger_kind` 三值子集（`control_flow_change`/`new_knowledge_pattern`/`threat_context_change`）承载。以下值物理保留供历史消费方参考，不再是新产物的写入目标。

| 机器值 | 语义 |
|---|---|
| `revision_change` | 源码revision变化触发。 |
| `staleness` | 历史结论陈旧触发。 |
| `coverage_regression` | 覆盖下降触发。 |
| `manual_rescan` | 用户显式复扫触发。 |
| `new_reachability` | 新调用者或路由使旧代码可达。 |
| `control_flow_change` | 控制流变化触发。 |
| `new_knowledge_pattern` | 新知识模式触发。 |
| `threat_context_change` | 威胁语境变化触发。 |

## patch_target_kind

| 机器值 | 语义 |
|---|---|
| `working_copy` | 补丁应用于目标树外的授权工作副本。 |
| `target_tree` | 补丁经本次明确授权应用于真实目标树。 |

## check_unit_status

> `[deprecated since v0.3.0]` 检查点终态改用 [`check_point_status`](#check_point_status)（candidate/disproved/blocked/not_applicable），由冻结清单派生的检查点账本（check-point-ledger 语义）承载。以下值物理保留供历史产物解读。

| 机器值 | 语义 |
|---|---|
| `planned` | 检查单元已规划但尚未开始检查。 |
| `running` | 检查单元正在检查中。 |
| `checked_with_candidates` | 检查单元已完成检查并产出至少一个候选。 |
| `checked_without_candidate` | 检查单元已完成检查但未产出候选。 |
| `blocked` | 检查单元因缺少用户决定、权限或关键输入而受阻。 |
| `not_applicable` | 检查单元在当前语境下不适用。 |

该枚举仅描述候选发现阶段规划出的单个检查单元(check unit)的终态，不得与 `work_unit_status` 混用；两者是不同粒度的执行追踪对象。

## check_point_status

| 机器值 | 语义 |
|---|---|
| `candidate` | 检查点产出至少一个候选。 |
| `disproved` | 检查点证伪并附证据。 |
| `blocked` | 检查点因环境阻碍而受阻，附原因。 |
| `not_applicable` | 检查点在当前语境下不适用，附理由。 |

该枚举描述阶段1候选发现的污点矩阵检查点终态（四选一），权威语义见 [`../skills/candidate-discovery/SKILL.md`](../skills/candidate-discovery/SKILL.md)；不得与 `check_unit_status`（检查单元执行追踪粒度）混用。
## check_point_reason_prefix (v0.3.9)

检查点终态理由的封闭前缀（权威语义见 [`check-unit-ledger-template.md`](check-unit-ledger-template.md) 全终态理由封闭枚举；Gate-1「反伪闭合(全方向)」「全终态理由封闭」机器校验）：

| 机器值 | 适用终态 | 说明 |
|---|---|---|
| `cluster_conclusion:` | candidate / disproved / not_applicable | 引用 clusters/ 结论文件路径 |
| `disproved_safe:` | disproved / not_applicable | 附观测事实证据引用（file:line 或 audit 行号） |
| `false_rule_hit:` | disproved / not_applicable | 附 FALSE-rules 规则号与证据 |
| `prefilter_no_exec:` | not_applicable（仅文件 terminal） | 三条预筛排除规则之一 + 0命中证据 |
| `budget:` / `user_decision:` / `permission:` | blocked | 附 capability_gap_refs + failed_wus.txt 登记 |
| `fix_pattern:` `[deprecated]` | fix_presence（历史） | **已随 fix_presence 禁止派生废弃（历史值保留）**：v0.4.3 起 fix_presence 方向禁止派生（Gate-1 方程「fix_presence 禁止派生」机械封堵），CVE 不作工作项、闭卷验收在包外；本前缀物理保留仅供历史 fixture/产物解读，不再是新产物的写入目标 |

禁止任何未登记前缀（含 `structural_assessment:`、`light_scan_assessment:`、`heuristic`、`noisy` 等批量贴标措辞）。

## fix_presence_status (v0.3.9)

负数 sink（知识库锚定修复存在性检查）的检查点终态（`direction=fix_presence`、`mechanism=knowledge_anchored`，派生来源仅限 knowledge/entries/cve-index.tsv 中 version-range 覆盖目标的 CVE）：

| 机器值 | 语义 |
|---|---|
| `fix_present` | 目标源码中该修复已存在（附证据行） |
| `fix_absent` | 修复缺失（附缺失证据，必须产出候选） |
| `blocked` | 受阻（附 capability_gap_refs，进 failed_wus.txt） |

## candidates_verdict 与 WU 分片 verdict 映射（v0.11.0，C12/U1）

`candidates.tsv` 的 `verdict` 列与 WU 分片（`batches/B{NNN}/WU-NNNN.tsv`）的 `verdict` 列是**两个不同维度**的枚举，不可混用或互相替代。

### candidates.tsv verdict（验证维度）

| 机器值 | 语义 |
|---|---|
| `confirmed` | 候选经阶段2验证确认为真；有活攻击面且非 `informational` 者成为 finding |
| `refuted` | 候选经阶段2验证被证伪；记录保留 |
| `informational` | 无存活攻击面的 candidate/code-hygiene item，不是 finding |
| `suppressed` | 被 FALSE-rules 抑制留痕（需另附 `false_rule_hit` 说明） |

### WU 分片 verdict（分片终态维度）

WU 分片（5 列 TSV：`sink_id | verdict | five_segment_evidence | evidence_refs | reviewed_at`，schema 见 [`wu-analyzer-prompt.md`](../agents/wu-analyzer-prompt.md)）的 `verdict` 列：

| 机器值 | 语义 |
|---|---|
| `candidate` | 分片内全部要素证伪失败，产出候选 |
| `disproved` | 分片内某要素被直接证据证伪 |
| `blocked` | 分片追不动（8跳/10文件上限），受阻 |

### 映射说明

- **WU 分片 verdict → `check_point_ledger.tsv` 的 `terminal_state`**：`candidate`→`candidate`、`disproved`→`disproved`、`blocked`→`blocked`。主代理汇聚时按此映射把分片终态转写为账本 `terminal_state`，不是翻译为 `candidates.tsv` 的 `verdict`。
- **`candidates.tsv` 的 `verdict` 是另一维度**：由阶段2 `verification-and-rating` 对候选做验证后写入（基础值集见 [`verification_verdict`](#verification_verdict) 的 `confirmed`/`unconfirmed`/`refuted`，本表在此基础上扩展 `informational`/`suppressed`）。阶段1 候选创建时 `verdict` 留空或写 `unconfirmed`，不由 WU 分片 verdict 直接填充。

## entry_type（v0.11.0，C13）

`source_inventory.tsv` 的 `entry_type` 列取值，描述外部输入进入系统的入口通道类型（见 [`../skills/scope-and-context/SKILL.md`](../skills/scope-and-context/SKILL.md) 入口通道全扫）。固定 10 值：

| 机器值 | 语义 |
|---|---|
| `rest` | REST/HTTP API 端点入口 |
| `rpc` | RPC（gRPC/Thrift/自定义 RPC）入口 |
| `mq` | 消息队列消费者入口 |
| `ws` | WebSocket 入口 |
| `graphql` | GraphQL query/mutation/subscription 入口 |
| `deser` | 反序列化入口（pickle/JSON 对象恢复等） |
| `file` | 文件/配置读取入口 |
| `cli` | 命令行参数/环境变量入口 |
| `event` | 事件/回调驱动入口 |
| `lambda` | serverless 函数入口 |

## a5_skip_reason（v0.11.0，G-16）

`run-state.md` 的 `a5_skip_reason` 字段取值，说明为何 A5 发散假设轮次未执行。Gate-1 方程「A5 痕迹强制」校验本枚举封闭：未登记值拒绝（与方程「A2 独立验证硬门」拒 `not executed` 对称）。A5 已执行时写 `a5_round`（非负整数）而非本字段。

| 机器值 | 语义 |
|---|---|
| `a5_executed_in_prior_run` | A5 已在先前 run 执行过，本轮复用结论未重跑 |
| `budget_depleted` | 预算耗尽，A5 未执行 |
| `no_sinks_matched` | 无 sink 匹配 A5 发散条件，A5 不适用 |
| `user_decision_blocked` | 缺少用户决定，A5 受阻 |


## check_unit_basis_type [deprecated since v0.3.0]

> 自 v0.3.0 起废弃：检查点终态改用 [`check_point_status`](#check_point_status)（candidate/disproved/blocked/not_applicable），检查点规划依据由 [`check-unit-ledger-template.md`](check-unit-ledger-template.md) 的 `mechanism` 列承载，不再使用 `basis_type`。以下值物理保留供历史消费方参考，不再是新产物的写入目标。

该枚举用于 `check-unit-ledger-template.md` 的 `basis_type` 字段，描述检查单元的规划依据类型；10 个值按三种发现机制分组使用，一个检查单元只属于一种 `mechanism`，其 `basis_type` 必须取该机制对应子集内的值。`mechanism` 复用 [`discovery_source`](#discovery_source) 的三个机器值。

### pattern_driven 机制使用

| 机器值 | 语义 |
|---|---|
| `entry_instance` | 以攻击面地图中单个入口点实例为检查单位。 |
| `sink_instance` | 以攻击面地图中单个危险操作/Sink 实例为检查单位。 |
| `dangerous_operation_instance` | 以攻击面地图中单个危险操作实例为检查单位（与 `sink_instance` 区别在于强调"操作"语义而非数据流汇点）。 |

### business_logic 机制使用

| 机器值 | 语义 |
|---|---|
| `controllable_input_path` | 以 #1 威胁语境文档中标注为"攻击者可控"的单条输入路径为检查单位。 |
| `business_invariant` | 以单个业务不变量为检查单位（推断预期行为后检查实际偏离）。 |
| `state_transition` | 以单个状态转换为检查单位（检查转换路径上的越权或缺失校验）。 |

### lateral_diff 机制使用

| 机器值 | 语义 |
|---|---|
| `handler_group` | 以一组同类处理器为检查单位（按路由模式/所属类/共享 helper 分组）。 |
| `dao_group` | 以一组同类 DAO/数据访问对象为检查单位。 |
| `policy_group` | 以一组同类策略为检查单位。 |
| `control_group` | 以一组同类控制/校验逻辑为检查单位。 |

权威语义以 [`check-unit-ledger-template.md`](check-unit-ledger-template.md) 为准。

## run_mode

| 机器值 | 语义 |
|---|---|
| `full` | 本次运行是全量审计。 |
| `incremental` | 本次运行是增量审计。 |

本次运行是全量审计还是增量审计，必须由用户显式指定，不允许有隐含默认值。

## evidence_mode

| 机器值 | 语义 |
|---|---|
| `executed` | 单段 PoC/验证证据本身是真实执行得到的。 |
| `inferred` | 单段 PoC/验证证据本身是推导得到的，未声称实际执行。 |

该枚举描述单段证据本身的获取方式，用于 `evidence_segments[].evidence_mode`；与 [`mode`](#mode) 及各处 `verification_mode` 表达同一维度并共享同一值集。`inferred` 段禁止携带伪执行结果。

## evidence_composition

| 机器值 | 语义 |
|---|---|
| `executed` | 一份完整 PoC 记录中的全部证据片段均为真实执行得到。 |
| `inferred` | 一份完整 PoC 记录中的全部证据片段均为推导得到。 |
| `mixed` | 一份完整 PoC 记录中同时存在已执行和推导的证据片段。 |

该枚举描述一份完整 PoC 记录中多段证据组合后的整体状态，是 `evidence_mode` 的聚合结果，不是单段证据本身的模式。组合规则：全部段`executed`→`executed`，全部段`inferred`→`inferred`，混合→`mixed`。混合证据按最小可信颗粒度拆分为独立`evidence_segments`记录（见 [`candidate-finding.md`](data-structures/candidate-finding.md) 的 `evidence_segments` 字段）。

## checklist_applicability

| 机器值 | 语义 |
|---|---|
| `applicable` | 候选专属检查清单在本次验证中适用。 |
| `not_applicable` | 候选专属检查清单在本次验证中不适用。 |

用于表达验证阶段"候选专属检查清单"这一次是否适用；为 `not_applicable` 时必须同时给出理由字段，不能以空清单代替显式说明。

## user_confirmed

该字段使用单一字符串枚举而不是布尔值，因为流程除确认和拒绝外还可能阻塞等待用户输入；混用布尔值与字符串会造成类型不稳定。

| 机器值 | 语义 |
|---|---|
| `confirmed` | 用户已确认威胁语境。 |
| `rejected` | 用户已拒绝当前威胁语境，需要由 #1 修订后重新确认。 |
| `blocked_pending_user_input` | 当前信息不足，流程已暂停并等待用户输入。 |
| `conservative_assumption_applied` | 非交互运行已显式选择`confirmation_policy=conservative_continue`，使用保守假设继续；不表示用户已确认。 |

## generation_basis_kind

该枚举用于 `generation_basis[].source_type`，覆盖当前固定生成依据来源；新增固定来源必须先在此登记。

| 机器值 | 语义 |
|---|---|
| `language_detection` | 从文件、依赖或其他代码信号探测语言。 |
| `framework_detection` | 从依赖、标记文件或入口签名探测框架。 |
| `product_documentation` | 来自 PRD、架构文档、API 文档等真实产品文档。 |
| `manual_user_input` | 来自用户显式提供并等待独立核实的信息。 |
| `tool_observation` | 来自工具对代码、配置或部署环境的直接观察。 |

## knowledge_entry_status

该枚举用于 `knowledge-base-entry.md` 的 `knowledge_entry_states[].status`、知识快照状态及晋升/弃用结果状态，不代表一个无法关联具体条目的顶层单值字段。

| 机器值 | 语义 |
|---|---|
| `active` | 知识条目当前有效；新条目创建时的默认状态。 |
| `deprecated` | 条目已不建议用于新判断，但保留供历史追溯；状态改变需要 `approved` 人工决定。 |
| `archived` | 条目已归档，不参与当前知识匹配，但仍物理保留；状态改变需要 `approved` 人工决定。 |

## evidence_grade

| 机器值 | 语义 |
|---|---|
| `direct` | 读到代码原文（文件:行号+片段）为证，证据直接对应判断对象。 |
| `indirect` | 基于命名/上下文/框架惯例推断，未直接读到对应代码原文。 |
| `unknown` | 信息缺失，尚未取得证据；缺口可补则先补再判，不可补则写清缺口。 |

该枚举逐项标注在六项基线各项、候选专属清单各项、四类控制评估各项、三要素各项与验证终态上。全局纪律：结论强度不得超过证据链最弱一环；`confirmed` 需全要素直接证据（或大部直接 + 其余强间接且无反证，注明最弱环）；仅凭间接推断"应该安全"不得定 `refuted`。

## verification_baseline 各项结果

适用于 `reachable`、`controllable`、`propagatable`、`exploitable`、`reproducible` 和 `impact_there`。`N/A` 仅可作为人读展示缩写，不得作为机器值。

| 机器值 | 语义 |
|---|---|
| `pass` | 已有充分证据证明该项成立。 |
| `fail` | 已有充分反证证明该项不成立。 |
| `unconfirmed` | 证据不足，无法可靠判定成立或不成立。 |
| `not_applicable` | 该项在当前候选语境中不适用，并附适用性理由。 |

## e2_trigger_reason [deprecated since v0.3.0]

| 机器值 | 语义 |
|---|---|
| `high_or_critical` | 候选定级为 high 或 critical，触发 E2 双向独立重建。 |
| `high_cost_refutation` | 反证代价高，需要独立重建以控制误判风险。 |
| `review_disagreement` | E1 复核与主验证结论不一致，触发 E2 仲裁。 |
| `evidence_conflict` | 证据之间存在冲突，需要双向独立重建澄清。 |
| `material_cross_boundary_gap` | 存在实质性跨信任边界缺口，触发 E2 独立验证。 |
| `static_only_high_impact` | 仅有静态证据支撑且影响重大，触发 E2 独立挑战。 |
| `independence_degraded` | 独立性降级，以 E2 双向重建弥补独立性不足。 |

自 v0.3.0 起废弃：E2 双向独立重建（7 触发值）已被轻量第二意见复核 + High/Critical 可选对称反转取代（见设计 §4.4 与 [`../skills/verification-and-rating/SKILL.md`](../skills/verification-and-rating/SKILL.md)）。本节物理保留供历史消费方参考，不再是新产物的写入目标。

## impact_rating 与 likelihood_rating

两个字段共用同一值集，但分别表达影响程度和发生可能性。

| 机器值 | 语义 |
|---|---|
| `high` | 影响或可能性处于高档。 |
| `medium` | 影响或可能性处于中档。 |
| `low` | 影响或可能性处于低档。 |
| `ignore` | 命中明确抑制条件时用于`likelihood_rating.rating`；impact仍按事实评估。矩阵结果为政策忽略，不等于删除记录。 |
| `unknown` | 现有信息不足以选择高、中、低或忽略档。 |

## exposure_scope

该枚举用于 `likelihood_rating.exposure`，按攻击者触达范围从远程到不可暴露表达。

| 机器值 | 语义 |
|---|---|
| `remote` | 可从目标所在主机或网络之外远程触达。 |
| `local_network` | 仅能从受限本地网络或内网触达。 |
| `localhost` | 仅能从目标主机本机回环接口触达。 |
| `none` | 当前不存在可触达暴露面。 |

## final_severity

| 机器值 | 语义 |
|---|---|
| `critical` | 可造成最高等级安全影响，需要最高优先级响应。 |
| `high` | 可造成重大安全影响，需要高优先级响应。 |
| `medium` | 可造成中等安全影响，应安排修复。 |
| `low` | 安全影响有限，按较低优先级治理。 |
| `ignore` | 权威矩阵对有活攻击路径finding产出的政策忽略结果；必须完整报告并进入#9显式处置，但不得产生 `priority`。 |
| `informational` | 仅用于无存活攻击面的candidate/code-hygiene item，不是finding，不进入严重度矩阵或#9，不产生`finding_id`；可使用 `P3`。 |

### impact x likelihood 权威矩阵

这是 `impact_rating.rating` 与 `likelihood_rating.rating` 的唯一完整矩阵。所有阶段必须查表，不得复制或凭感觉调整；`high` x `high` 由 `impact_rating.critical_criteria_met` 唯一决定。

| impact \ likelihood | `high` | `medium` | `low` | `ignore` | `unknown` |
|---|---|---|---|---|---|
| `high` | `critical_criteria_met=true` 为 `critical`；否则为 `high` | `medium` | `low` | `ignore` | `medium` |
| `medium` | `medium` | `low` | `low` | `ignore` | `low` |
| `low` | `low` | `low` | `low` | `ignore` | `low` |
| `ignore` | `ignore` | `ignore` | `ignore` | `ignore` | `ignore` |
| `unknown` | `medium` | `low` | `low` | `ignore` | `low` |

`unknown` 只参与严重度矩阵计算，不得改变 `verification_verdict`；`ignore` 不产生 `priority`。

## priority

| 机器值 | 语义 |
|---|---|
| `P0` | 最高处置优先级，通常对应紧急响应。 |
| `P1` | 高处置优先级。 |
| `P2` | 中处置优先级。 |
| `P3` | 较低处置优先级。 |

`final_severity` 与 `priority` 的确定性映射为：`critical` -> `P0`、`high` -> `P1`、`medium` -> `P2`、`low` -> `P3`。矩阵外的 `informational` 可使用 `P3`，也可不产生 `priority`。

## evidence_tag

| 机器值 | 语义 |
|---|---|
| `Observed` | 由代码、配置、工具输出或执行结果直接观察到。 |
| `Inferred` | 基于已观察事实推导，但未被直接执行或观察。 |
| `Proposed` | 建议采用的修复或设计，尚非当前事实。 |

## file_kind

| 机器值 | 语义 |
|---|---|
| `source` | 可供分析的源代码文件。 |
| `config` | 配置文件。 |
| `binary` | 二进制文件。 |
| `generated` | 由工具或构建流程生成的文件。 |
| `other` | 不属于以上类型的文件。 |

## readability

| 机器值 | 语义 |
|---|---|
| `readable` | 文件内容可被当前流程读取和分析。 |
| `unreadable` | 文件内容无法被当前流程读取或分析。 |

## category_kind

| 机器值 | 语义 |
|---|---|
| `entrypoint` | 外部输入或执行流进入系统的入口。 |
| `dangerous_operation` | 可能产生安全影响的危险操作。 |
| `other` | 不属于入口或危险操作的其他类别。 |

## review_status

| 机器值 | 语义 |
|---|---|
| `required` | 需要人工审查且尚未完成。 |
| `completed` | 人工审查已完成。 |
| `blocked` | 人工审查因缺少条件而受阻。 |

## input_control_class

| 机器值 | 语义 |
|---|---|
| `attacker_controlled` | 输入可由攻击者直接或间接控制。 |
| `operator_controlled` | 输入由系统部署或运行人员控制。 |
| `developer_controlled` | 输入由开发者在代码或构建阶段控制。 |

## lifecycle_verification_result

| 机器值 | 语义 |
|---|---|
| `verified_fixed` | 生命周期复验已确认问题修复。 |
| `still_present` | 生命周期复验确认问题仍然存在。 |
| `inconclusive` | 生命周期复验证据不足，无法得出确定结论。 |

## poc_reexecution_result

| 机器值 | 语义 |
|---|---|
| `passed` | PoC 重新执行得到预期结果。 |
| `failed` | PoC 重新执行未得到预期结果。 |

## dependency_applicability

| 机器值 | 语义 |
|---|---|
| `applicable` | 外部依赖主张明确适用于当前目标。 |
| `questionable` | 外部依赖主张的适用性存在疑问。 |
| `disputed` | 外部依赖主张的适用性存在明确争议。 |
| `not_applicable` | 外部依赖主张明确不适用于当前目标。 |
| `no_match` | 未找到与当前目标匹配的外部依赖主张。 |

## trigger_scenario

| 机器值 | 语义 |
|---|---|
| `dependency_query` | 查询依赖信息时触发。 |
| `external_claim_import` | 导入外部主张时触发。 |
| `export` | 导出数据或报告时触发。 |
| `tracker_write` | 向跟踪系统写入记录时触发。 |

## consent_status

| 机器值 | 语义 |
|---|---|
| `granted` | 所需授权或同意已明确授予。 |
| `not_granted` | 所需授权或同意尚未授予。 |

## execution_status

| 机器值 | 语义 |
|---|---|
| `succeeded` | 执行完成且成功。 |
| `failed` | 已执行但失败。 |
| `not_executed` | 未执行。 |

## installation_scope_type

| 机器值 | 语义 |
|---|---|
| `project` | 安装仅作用于当前项目。 |
| `shared` | 安装作用于多个项目或共享环境。 |

## deprecation_signal_type

| 机器值 | 语义 |
|---|---|
| `long_term_miss` | 长期未命中，构成弃用信号。 |
| `repeated_false_positive` | 重复产生误报，构成弃用信号。 |

## evidence_role

该枚举的全部值同时构成报告 `evidence_role_labels[].role` 与 `detailed_narrative_view[].evidence_walkthrough[].role` 的固定角色子集；报告层不得扩展、改名或重解释这些值。

| 机器值 | 语义 |
|---|---|
| `user_input` | 证明用户输入或外部输入来源。 |
| `entrypoint` | 证明输入进入系统的入口。 |
| `propagation` | 证明数据或控制流传播路径。 |
| `root_control` | 证明根部控制措施或控制权归属。 |
| `sink` | 证明数据到达敏感操作或危险汇点。 |
| `outcome` | 证明执行结果或安全影响。 |
| `expected_control` | 证明预期应存在的安全控制。 |

## remediation_verification_result

| 机器值 | 语义 |
|---|---|
| `fixed` | 修复验证确认问题已消除。 |
| `still_present` | 修复验证确认问题仍然存在。 |
| `inconclusive` | 修复验证无法得出确定结论。 |

`verification_mode` 复用 `mode` 的 `executed`/`inferred` 值集，但字段名用于修复后验证记录：`executed` 表示真实重跑，`inferred` 表示仅对修复后代码重走静态证据链。

## 报告覆盖结果

结构化产物和外部导出使用机器值；报告 `Outcome` 列使用对应的人读展示值。两者是一一映射，不产生新的报告层判断。

同一 Surface 存在多条候选或覆盖信号时，必须按以下顺序聚合，确保结果唯一并与 `report-delivery` 的上游状态投影语义一致：

1. 存在 `confirmed` 候选，结果为 `reported`。
2. 否则，存在 `unconfirmed` 候选或任何覆盖缺口，结果为 `needs_follow_up`。
3. 否则，存在 `refuted` 候选，结果为 `rejected`。
4. 不存在任何真实候选时，若威胁语境明确该 Surface 不适用，结果为 `not_applicable`；已有真实候选时不得用 `not_applicable` 覆盖其状态。
5. 不存在任何候选、没有不适用结论且已完整扫描时，结果为 `no_issue_found`。

| 机器值 | 人读展示值 | 语义 |
|---|---|---|
| `reported` | `Reported` | 范围内存在confirmed记录并已进入报告；可能是有活攻击面的finding，也可能是单列展示的informational code-hygiene candidate。 |
| `no_issue_found` | `No issue found` | 范围完整扫描且未产出候选。 |
| `rejected` | `Rejected` | 范围内候选的验证结论为 `refuted`。 |
| `not_applicable` | `Not applicable` | 威胁语境已确认该风险在本系统不适用，且不存在真实候选。 |
| `needs_follow_up` | `Needs follow-up` | 覆盖、展开或验证尚未收敛，需要继续处理。 |

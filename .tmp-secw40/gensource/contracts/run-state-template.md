# GenSource运行状态模板

本模板供宿主Agent直接创建和覆盖更新`run-state.md`。它是人读检查点，不是软件API；禁止为它编写GenSource自有状态机或validator。

```yaml
run_id: audit-20260808-001
source_path: /absolute/path/to/source
source_revision: git:<commit>+dirty | snapshot:<description>
authorized_scope:
  - /absolute/path/to/source
authorized_components:
  - primary_source
scope_includes:
  - /absolute/path/to/source/**
scope_excludes:
  - /absolute/path/to/source/vendor/**
confirmation_policy: interactive_confirmed
run_mode: full
human_question_budget:
  total: 1
  consumed: 0
  questions: []
run_status: running
capability_profile_ref: capability-profile.md
knowledge_snapshot_id: KS-audit-20260808-001
knowledge_session_ref: knowledge-session.md
current_capability: scope-and-context
inventories_frozen:
  file_inventory:
    path: file_inventory.tsv
    lines: 0
  sink_inventory:
    path: sink_inventory.tsv
    lines: 0
  source_inventory:
    path: source_inventory.tsv
    lines: 0
run_fingerprint: null
model_host_label: null
stability_check:
  enabled: false
  twin_run_ids: []
  diff_result: null
progress_summary:
  batches:
    total: 0
    completed: 0
    remaining: 0
  channels_done: []
  sink_types_done: []
failed_wus_ref: failed_wus.txt
last_completed_step: null
remaining_scope:
  - scope-and-context
planned_artifacts:
  - threat-context.md
started_artifacts:
  - capability-profile.md
  - knowledge-session.md
completed_artifacts: []
evidence_refs: []
resume_notes:
  - 初始化完成，尚未开始阶段0
updated_at: 2026-08-08T12:00:00Z
work_unit_counts: null
gate_summary: null
execution_budget:
  node_attempt: 1
  node_attempt_limit: 3
  gate_rework_count: 0
  candidate_arbitration_rounds: {}
  plateau_detected: false
  previous_gap_refs: []
  current_gap_refs: []
workload_estimate:
  estimated_workload: ""
  scale:
    files: 0
    entries: 0
    check_units: 0
    candidates: 0
  completed_scope_refs: []
  remaining_scope_refs: []
  gate_rework_count: 0
  arbitration_round_count: 0
  user_limits:
    time: null
    tokens: null
dynamic_execution_summary:
  authorization_status: not_granted
  gate_decision: denied
  fallback: static_only
  decisions: []
anchor:
  anchored_at: 2026-08-08T12:00:00Z
  current_capability: scope-and-context
  current_work_unit_id: null
  next_action: 产出三份冻结清单与威胁语境
artifact_lifecycle_guard:
  sets_are_disjoint: true
  completed_artifacts_only: true
  references_checked: true
single_document_guard:
  document_kind: single_yaml_mapping
  duplicate_keys_forbidden: true
  update_mode: whole_file_replace
  strict_parse_passed: true
  required_fields_checked: true
  consistency_checked: true
  previous_trusted_version_preserved_on_failure: true
```

## 字段说明

| 字段 | 要求 |
|---|---|
| `run_id` | 本次运行唯一的人读标识，恢复时保持不变 |
| `source_path` | 已授权目标的绝对路径 |
| `source_revision` | Git commit+dirty状态，或非Git目录的可核查快照描述 |
| `authorized_scope` | 本run冻结的显式授权路径数组；所有组件和WU只能引用其子集 |
| `authorized_components` | 本run冻结的获授权组件标识数组；组件不得因依赖关系被静默扩展 |
| `scope_includes` / `scope_excludes` | 本run冻结的包含/排除路径规则；排除规则优先，后续发现路径不得原地改写 |
| `confirmation_policy` | 本run冻结的确认策略；交互模式未获确认时阻塞，非交互继续必须显式为`conservative_continue` |
| `run_mode` | 见枚举注册表 [`run_mode`](enum-registry.md#run_mode)：`full`或`incremental`；必须由用户显式指定，不允许隐含默认值 |
| `human_question_budget` | 人工提问预算计数器：`total`（整个 run 至多 1 次）、`consumed`（已用次数）、`questions`（每次提问记录数组）；提问前必须核对 `consumed < total`，否则禁止提问 |
| `run_status` | 整次运行的生命周期状态，四值：`running` / `completed` / `blocked` / `interrupted`（**无 `initialized`**；run 创建即 `running`）。不得写入 `stage_result`/`gate_result` 取值；WU 状态由分片文件存在性判定承载（WU 五态） |
| `capability_profile_ref` | 能力档案相对路径，引用`capability-profile-template.md`产出的`capability-profile.md`；不复制完整探测正文 |
| `knowledge_snapshot_id` / `knowledge_session_ref` | 本run冻结的知识快照ID及`knowledge-session-template.md`实例引用；跨阶段必须一致 |
| `inventories_frozen` | **三份冻结清单校验字段**：每份含 `path`（清单相对路径）与 `lines`（冻结时 `wc -l` 行数）。生成后不改；恢复时逐份校验文件存在且行数一致，不一致不得精确续跑 |
| `run_fingerprint` | **稳定性自检对账对象**。语义 = hash(排序后的机器字段集合)（6 字段：`candidate_id`/`location`/`sink_type`/`severity`/`root_cause_group_id`/`verdict`，来自 `findings/machine-fields.json`），设计 §5.2；命令见 [`host-reconciliation-commands.md`](host-reconciliation-commands.md) 第7节。运行时未产出 `findings/machine-fields.json` 前为 null |
| `model_host_label` | 顶层调度在能力探测时写入的模型宿主角标；报告概况复用此值 |
| `stability_check` | 稳定性自检配置：`enabled`（是否启用双跑自检）、`twin_run_ids`（双跑 run_id 数组）、`diff_result`（`stability-diff.md` 的差异结果引用或 null）。顶层调度写入 |
| `progress_summary` | **progress 摘要**：`batches`（total/completed/remaining）、`channels_done`（已完成的入口通道）、`sink_types_done`（已扫的 sink 类）。随 `progress.json` 逐批覆盖更新 |
| `failed_wus_ref` | **failed_wus 引用**：失败 WU 清单文件相对路径；报告强制引用，应为空或逐条列入报告 |
| `current_capability` | 当前能力目录名；完成后可写`report-delivery` |
| `last_completed_step` | 已完整结束的最后一个实质子步骤，不写正在进行但未完成的步骤 |
| `remaining_scope` | 尚未处理的具体目录、文件、候选或子步骤；不能只写"剩余部分" |
| `planned_artifacts` | 预计生成但允许尚不存在的产物；不得作为证据、Gate输入或阶段转移输入 |
| `started_artifacts` | 已真实存在且非空但尚未完成的产物；可用于恢复，不能证明节点完成 |
| `completed_artifacts` | 已真实存在且非空的产物相对路径。`run-state.md` 只引用已有产物路径，不复制产物内容 |
| `evidence_refs` | 支撑恢复点的产物章节、candidate或具体证据引用 |
| `resume_notes` | 复用范围、须重新核查内容、阻塞原因和下一动作 |
| `updated_at` | 最近一次覆盖更新时间，ISO 8601格式 |
| `work_unit_manifest` | 条件启用WU时记录manifest相对路径；未启用时省略 |
| `work_unit_counts` | 只记录WU计数与未汇聚数量，不嵌入分片内容 |
| `gate_summary` | 当前Gate结果（由 host-reconciliation-commands.md §4c 对账块输出生成，判定栏禁止手写）、返工轮次、独立性降级与具体缺口 |
| `gate2_notes` | 引用 `gate2_notes.md` 文件（字段值必须含文件名 `gate2_notes.md`）；Gate-2 独立抽查结论由独立 subagent 写入该文件，本字段仅引用文件名、不内联结论正文（Gate-1 方程「A2 独立验证硬门」校验字段值含 `gate2_notes.md`），不改变 gate 判定 |
| `runtime_verification` | 枚举字符串；允许值 `allowed`/`denied`（见 [`enum-registry.md`](enum-registry.md#runtime_verification)）；写方=顶层调度初始化冻结（见 [`USAGE.md`](../USAGE.md) 参数速查） |
| `wu_skip_reason` | 字符串；允许值=非空自由理由串（无封闭枚举，说明为何跳过 WU 派发）；写方=顶层调度 |
| `a5_round` | 非负整数；允许值=≥0 整数（0=未执行 A5，>0=已执行轮次）；写方=主代理 |
| `a5_skip_reason` | 枚举字符串；允许值=`a5_executed_in_prior_run`/`budget_depleted`/`no_sinks_matched`/`user_decision_blocked`（见 [`enum-registry.md`](enum-registry.md#a5_skip_reason)）；写方=主代理 |
| `missing_check_skip_reason` | 字符串；允许值=非空自由理由串（无封闭枚举，说明为何跳过 `SINK-MISSING-CHECK` 类检查）；写方=主代理 |
| `execution_budget` | 循环预算记录：`node_attempt`（当前节点执行次数，初次=1）、`node_attempt_limit`（固定3：初次+最多2次Gate返工）、`gate_rework_count`（Gate返工累计）、`candidate_arbitration_rounds`（各candidate语义仲裁轮次，Gate返工不重置）、`plateau_detected`、`previous_gap_refs`/`current_gap_refs`（相邻两次缺口引用用于plateau判定） |
| `workload_estimate` | 工作量预估：只用于规划深度分配的优先级顺序，不是"能不能做完"的判断依据；`remaining_scope_refs` 是续跑指针，不是可放弃的剩余；覆盖不因规模/耗时打折扣。禁止逐步骤Token计量和费用遥测 |
| `dynamic_execution_summary` | 动态执行授权状态与安全门决策摘要，权威规则见`shared/deployment-environment.md` |
| `anchor` | 恢复时"完整锚定"记录（**三级锚定分类已删除**，不再有 `anchor_type`）：`anchored_at` 锚定时间戳、`current_capability` 锚定时当前能力、`current_work_unit_id`、`next_action` 下一动作。覆盖式更新 |
| `single_document_guard` | 单文档原子写保护及严格解析、必填字段、一致性核对结果；由宿主 shell（YAML 解析命令）执行校验 |
| `artifact_lifecycle_guard` | 产物生命周期集合互斥和引用有效性核对；Gate/阶段转移只消费completed集合 |

## 写入规则

### single_document_guard

`run-state.md`必须且只能是一个YAML document，其根为单一YAML mapping，禁止重复键、拼接第二个mapping或追加局部状态。每次更新先在内存形成完整新文档，再整文件替换；替换前后均须严格解析并核对必填字段、枚举命名空间、计数与Gate一致性。解析、写入或核对任一步失败时不得覆盖，必须保留旧可信版本并写外部错误记录；半写文件不得成为恢复依据。该核对由宿主 shell 的 YAML 解析命令执行（[`host-reconciliation-commands.md`](host-reconciliation-commands.md) 第8节），不依赖 LLM 自报。

- 初始化后立即创建，`run_status` 立即为 `running`（无 `initialized` 细分），不等第一个能力完成。
- 初始化时冻结`confirmation_policy`、`authorized_components`、`authorized_scope`、`scope_includes`和`scope_excludes`。每个组件和WU范围必须完全位于这些授权边界内；超出时须对每条路径提供本次动作的`authorization_ref`，否则阻塞。交互模式未确认必须`run_status=blocked`；非交互模式若继续，必须显式写`confirmation_policy=conservative_continue`并采用最小范围和只读默认值。
- 阶段0 三份清单生成后，立即填写 `inventories_frozen`（三份 path + `wc -l` 行数）并冻结；此后清单不再修改。
- 每个实质子步骤完成后覆盖更新 `progress_summary` 与 `run-state.md`。
- 长命令或子Agent执行前先记录即将开始的动作和当前可信恢复点。
- 不能把尚未完成的步骤写入`last_completed_step`。
- `completed_artifacts`中的文件必须真实存在且非空。
- `planned_artifacts`、`started_artifacts`、`completed_artifacts`三个集合必须互斥；产物只按planned→started→completed晋升。
- `completed_artifacts_only`：所有`evidence_refs`与Gate输入只能引用`completed_artifacts`。
- 启用WU时先创建真实Manifest并把它写入`started_artifacts`；active Manifest只能进入`started_artifacts`，完成并闭合后才可进入`completed_artifacts`。
- `run_status=blocked`时，`resume_notes`必须写清缺少的用户决定、权限或输入。
- `run_status=completed`时，`remaining_scope`必须为空，并在`completed_artifacts`中包含最终报告；启用WU时还要求`pending=0`、`running=0`、`unmerged_artifacts=0`并通过适用Gate-1。
- `run_status`不得写入`stage_result`（`completed`/`partial`/`not_applicable`）或`gate_result`（`pass`/`rework`/`blocked`/`pass_with_gaps`）的取值；`gate_summary.result`使用枚举注册表[`gate_result`](enum-registry.md#gate_result)。
- 跨节点路由遵循 [`../shared/work-graph.md`](../shared/work-graph.md) 的转换表；阶段转移前须通过适用 Gate（见 [`../shared/quality-gates.md`](../shared/quality-gates.md)），不得提前声明下一阶段完成。

## 恢复核查

宿主Agent恢复前逐项回答：

1. `source_path`是否仍存在且仍是授权目标？
2. `source_revision`是否与当前源码一致？
3. `inventories_frozen` 三份清单是否存在且 `wc -l` 行数一致？
4. 每个`completed_artifacts`是否存在且非空？
5. `progress_summary.batches.remaining` 与 `remaining_scope` 是否足够具体，可以避免重复工作？
6. 旧candidate ID和证据引用是否可继续使用？

任一关键答案为否时，不声明精确续跑；保留旧产物作参考，新建run并从最近可信能力重跑。

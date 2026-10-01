# Work Unit 边界事实结构契约

**职责**：定义单个 Work Unit 分片在扫描时产出的边界事实——该分片内部和外部的 inputs/outputs、符号引用、调用边、字段映射、存储边、传输边及未解析连接。供跨 WU 汇聚规则（[`../../shared/cross-boundary-analysis.md`](../../shared/cross-boundary-analysis.md)）在多分片场景下连接跨 WU 的 Source→Sink 路径。
**生产者**：各能力在 WU 分片执行时写入；`scope-and-context`、`candidate-discovery` 和 `verification-and-rating` 均可在各自分片中产出边界事实。
**消费者**：跨 WU 汇聚规则（`shared/cross-boundary-analysis.md`）、`candidate-discovery`（构建 `cross_boundary_path`）、`verification-and-rating`（核实跨 WU 可达性）、`lifecycle-governance`（增量陈旧判定中的控制流图变化检测）。WU原始边界事实一旦分片完成即冻结；汇聚方只读这些分片并写独立汇聚结果，不原地修改原始边。

枚举值以[枚举注册表](../enum-registry.md)为准，写权限以[字段写权限表](../field-ownership-table.md)为准。

## 覆盖范围

边界事实必须覆盖以下跨边界传播载体（每个 WU 分片按实际命中类型记录，无条目时写空数组）：

| 载体类别 | 边界事实需记录的内容 |
|---|---|
| 函数 / 方法 | 调用边（caller→callee）、参数来源、返回值去向 |
| 接口 / 抽象类 | 实现类列表、动态分发目标 |
| 继承 / 多态 | 父类方法覆写、`super()` 调用链 |
| 回调 / 事件处理器 | 注册点、触发条件、回调目标 |
| 依赖注入 (DI) | 注入接口、注入位置、实际注入类型（若可静态确定） |
| 反射 / 动态分发 | 反射调用点、目标名称表达式、已知目标（若可确定） |
| 生成代码 / 代码模板 | 生成器入口、生成产物位置、生成代码中的 Sink |
| DTO / 数据传输对象 | 字段定义、序列化/反序列化位置、字段到 ORM/DB 列的映射 |
| 序列化 / 反序列化 | 序列化器入口、格式、类型校验存在性 |
| 数据库 (SQL) | 表名、列名、执行语句位置、参数化与否 |
| 缓存 (Redis/Memcached 等) | 键模式、写入点、读取点、TTL 来源 |
| 文件 I/O | 路径来源（硬编码/用户输入/配置）、读写位置 |
| 对象存储 (S3/OSS 等) | Bucket/Key 来源、上传/下载位置 |
| 消息队列 (MQ) | Topic/Queue 名、生产者、消费者、消息体字段 |
| 事件 / 事件总线 | 事件类型、发布者、订阅者 |
| RPC (gRPC/Thrift/REST) | 服务名、方法名、参数字段、客户端/服务端位置 |
| GraphQL | Query/Mutation/Subscription、字段解析器、参数来源 |
| WebSocket | 连接端点、消息处理函数、消息体字段 |
| 多仓服务契约 | 跨仓库接口引用、契约版本、已知的调用方/被调用方 |

## 字段定义

| 字段 | 类型 | 必填 | 唯一写入方 | 只读方 | 允许值/约束 | 说明 |
|---|---|---|---|---|---|---|
| `stage_result` | `string` | 是 | 当前产出该分片的能力 | 所有消费者 | 见枚举注册表 [`stage_result`](../enum-registry.md#stage_result) | 当前边界事实产物完成程度。 |
| `version` | `string` | 是 | 当前产出该分片的能力 | 所有消费者 | 语义版本字符串 `MAJOR.MINOR.PATCH` | 本结构实例采用的契约版本。 |
| `resume_context` | `object` | 是 | 当前产出该分片的能力 | 调度方、汇聚方 | `completed`/`not_applicable` 时可为 `{}`；`partial` 时必须含非空 `last_completed_step: string`、`remaining_scope: string[]`、`evidence_refs: string[]` | 断点续跑上下文。 |
| `wu_id` | `string` | 是 | WU创建时一次性写入，此后不可变 | 宿主、汇聚方、所有能力 | 非空；必须与 WU Manifest 中的 `id` 一致 | 该边界事实所属的 Work Unit 标识。 |
| `run_id` | `string` | 是 | WU创建时一次性写入，此后不可变 | 宿主、汇聚方 | 非空；必须与 `run-state.md` 的 `run_id` 一致 | 归属运行标识，用于汇聚前身份检查。 |
| `source_revision` | `string` | 是 | WU创建时一次性写入，此后不可变 | 宿主、汇聚方 | 非空；Git commit+dirty 或快照描述 | 该 WU 创建时记录的源码版本，用于汇聚前身份检查。 |
| `scope` | `array<string>` | 是 | WU创建时一次性写入 | 宿主、汇聚方 | 非空；文件路径或目录路径列表 | 该 WU 分片覆盖的源码范围。 |
| `inputs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{symbol: string, symbol_kind: string, source_ref: string, origin: string, evidence_refs: string[]}`；`symbol_kind` 见枚举注册表扩展值；`origin` 取值 `external`/`internal`/`cross_wu`/`unknown`；无条目时写空数组 | 该 WU 的外部和跨 WU 输入入口。 |
| `outputs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项结构同 `inputs`；`origin` 取值 `external`/`internal`/`cross_wu`/`unknown`；无条目时写空数组 | 该 WU 的对外和跨 WU 输出。 |
| `source_refs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{stable_id: string, symbol: string, location_ref: string, wu_id: string|null, evidence_refs: string[]}`；`wu_id` 为 null 时表示该 Source 不在本 WU 范围内（跨 WU 引用）；无条目时写空数组 | Source 实例引用（污点源 / 攻击者可控数据入口）。 |
| `sink_refs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项结构同 `source_refs`；无条目时写空数组 | Sink 实例引用（危险操作汇点）。 |
| `guard_refs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`verification-and-rating` | 每项结构同 `source_refs`；无条目时写空数组 | Guard 实例引用（前置防护控制）。 |
| `sanitizer_refs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`verification-and-rating` | 每项结构同 `source_refs`；无条目时写空数组 | Sanitizer 实例引用（净化/校验控制）。 |
| `encoder_refs` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`verification-and-rating` | 每项结构同 `source_refs`；无条目时写空数组 | Encoder 实例引用（输出编码控制）。 |
| `call_edges` | `array<object>` | 是 | 当前产出该分片的能力；分片完成后冻结 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{caller_symbol: string, callee_symbol: string, callee_wu_id: string|null, edge_kind: string, resolved: boolean, evidence_refs: string[]}`；`edge_kind`引用注册表[`boundary_edge_kind`](../enum-registry.md#boundary_edge_kind)；未解析状态保留在原始事实中 | 调用边原始事实。 |
| `field_mappings` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{source_symbol: string, source_field: string, target_symbol: string, target_field: string, mapping_kind: string, evidence_refs: string[]}`；`mapping_kind` 取值 `dto_field`/`orm_column`/`serialization_field`/`message_field`/`rpc_param`/`graphql_field`；无条目时写空数组 | 字段映射——DTO/序列化/ORM/MQ/RPC 等层面的字段到字段映射。 |
| `storage_edges` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{write_symbol: string, write_wu_id: string, read_symbol: string|null, read_wu_id: string|null, storage_kind: string, storage_location: string, key_or_table: string, evidence_refs: string[]}`；`storage_kind`引用注册表[`boundary_storage_kind`](../enum-registry.md#boundary_storage_kind)；读取端未知时保留null；无条目时写空数组 | 存储边。 |
| `transport_edges` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{producer_symbol: string, producer_wu_id: string, consumer_symbol: string|null, consumer_wu_id: string|null, transport_kind: string, channel: string, message_fields: string[], evidence_refs: string[]}`；`transport_kind`引用注册表[`boundary_transport_kind`](../enum-registry.md#boundary_transport_kind)；消费者未知时保留null；无条目时写空数组 | 传输边。 |
| `unresolved_connections` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、`candidate-discovery`、`verification-and-rating` | 每项最少为 `{from_symbol: string, connection_kind: string, target_hint: string|null, reason: string, evidence_refs: string[]}`；`connection_kind` 取值同 `call_edges.edge_kind` 加 `storage_read`/`transport_consume`/`cross_repo_contract`；`target_hint` 为已知但不确认的目标线索（如接口名、Topic 名）；`reason` 非空，说明为何未解析；无条目时写空数组 | 未解析连接——保留为缺口而非声称"不存在"。汇聚后仍无法解析的项进入 `verification-and-rating` 的 Gate-2 跨 WU 抽查与第二意见考量。 |
| `evidence` | `array<object>` | 是 | 当前产出该分片的能力 | 汇聚方、所有消费者 | 每项最少为 `{evidence_id: string, kind: string, location_ref: string, description: string}`；`kind` 取值 `code_reading`/`config_reading`/`tool_output`/`type_inference`/`pattern_match`；无条目时写空数组 | 支撑边界事实的证据列表。 |
| `confidence` | `object` | 是 | 当前产出该分片的能力 | 汇聚方、`verification-and-rating` | 最少为 `{level: string, rationale: string}`；`level` 取值 `high`/`medium`/`low`；`rationale` 非空 | 边界事实整体置信度——`low` 时汇聚方和下游须注意该 WU 的边界连接可能不完整。 |

## 写入纪律

1. **每个 WU 分片产出一组边界事实**，写入该 WU 的分片产物（如 `work-units/<wu-id>.md` 中的边界事实段或独立 `work-units/<wu-id>-boundary-facts.md`）。
2. **跨 WU 引用不猜**：`call_edges`/`storage_edges`/`transport_edges` 中目标 WU 未知时写 `resolved=false` 或对应字段为 null，不得填写猜测的 `callee_wu_id`/`read_wu_id`/`consumer_wu_id`。
3. **未解析连接必须保留**：`unresolved_connections` 是缺口记录，不是"不存在"声明。汇聚后仍无法解析的项必须传递到下游验证阶段，不得静默丢弃。
4. **证据必须可追溯**：每条边界事实的 `evidence_refs` 必须指向真实读取到的代码/配置位置，不能凭空断言。
5. **身份冻结**：`wu_id`、`run_id`、`source_revision`、`scope` 为 WU 创建时一次性写入的冻结值，此后不可变；源码 revision 变化时通过汇聚前身份检查发现不一致后重做受影响 WU，不更新冻结值。
6. **汇聚前身份检查**：汇聚前必须核对 `wu_id` 与 WU Manifest 的 `id` 一致、`run_id` 等于当前 `run_id`、`source_revision` 等于当前源码 revision。任一不一致不得汇聚。
7. **原始边冻结**：WU分片完成后，`call_edges`、`field_mappings`、`storage_edges`、`transport_edges`、`unresolved_connections`及其证据均冻结。汇聚方不得补写目标、翻转`resolved`、删除unresolved项或改证据。
8. **独立汇聚结果**：汇聚方把跨WU解析结果写入独立汇聚产物，记录来源分片引用、连接后的边、仍未解析项和汇聚证据。候选的跨WU段只从该独立产物投影，不修改WU原始分片。
9. **正式引用**：独立汇聚产物统一由`cross_boundary_aggregate_ref`引用，并至少包含`run_id`、`source_revision`、`input_wu_ids`、`input_boundary_fact_versions`、`aggregate_edges`、`unresolved_connections`和`version`。每条`aggregate_edges`新边必须含指向冻结输入边的`source_edge_ref`。

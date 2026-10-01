# 跨 WU 边界汇聚规则

## 定位

本文件定义多个 Work Unit 分片产出边界事实后的汇聚规则——如何只读各 WU 的 `call_edges`、`field_mappings`、`storage_edges`、`transport_edges` 和 `unresolved_connections`，并产出独立的 `cross_boundary_aggregate`，连接成跨 WU 的完整 Source→Sink 路径。该正式产物由 `cross_boundary_aggregate_ref` 统一引用。

边界事实的结构契约见 [`../contracts/data-structures/work-unit-boundary-facts.md`](../contracts/data-structures/work-unit-boundary-facts.md)。本文件只定义汇聚规则，不重复定义字段结构。

## 汇聚前提

1. **汇聚前身份检查**：逐项核对每个 WU 边界事实的 `wu_id` 与 WU Manifest 的 `id` 一致、`run_id` 等于当前 `run_id`、`source_revision` 等于当前源码 revision、`scope` 与 WU Manifest 的 `scope` 一致。任一不一致不得汇聚，须先查明原因并修正 WU 或重新执行受影响 WU。
2. **身份字段冻结**：`wu_id`/`run_id`/`source_revision`/`scope` 为 WU 创建时一次性写入的冻结值。源码 revision 或上游产物版本变化时，不更新冻结值，而是通过身份检查发现不一致后重做受影响 WU（复用 `work-unit-manifest-template.md` 的身份冻结原则）。

## 汇聚步骤

### 步骤一：核对 WU 身份

对每个待汇聚的 WU 边界事实，执行汇聚前身份检查（见上）。通过的 WU 进入下一步，不通过的 WU 标记为 `stale` 并排除出本次汇聚，通知宿主重做。

### 步骤二：按稳定符号连接 call_edges

1. 收集所有 WU 的 `call_edges`。
2. 对每条 `resolved=false` 的调用边，用 `callee_symbol` 在全部已汇聚 WU 的 `outputs` 和 `inputs` 中查找匹配的 `symbol`；输入边始终只读。
3. 匹配成功时：在 `cross_boundary_aggregate.aggregate_edges` 新建跨 WU 调用边，填写目标 WU，并以 `source_edge_ref` 指向输入 WU 中的原始边；不得修改原始边的 `resolved` 或目标字段。
4. 匹配失败时：在聚合产物的 `unresolved_connections` 保留引用和原因，不声称"该调用不存在"，也不修改输入 WU 的原始缺口。
5. **连接键为稳定符号**（函数全限定名 / 方法签名 / 接口方法名），不使用文件路径或行号——文件路径和行号在重构后不稳定，不适合作为跨 WU 连接键。

### 步骤三：按字段映射连接 field_mappings

1. 收集所有 WU 的 `field_mappings`。
2. 对每对 `source_symbol.source_field → target_symbol.target_field`，检查 `source_symbol` 和 `target_symbol` 是否分属不同 WU。
3. 跨 WU 的字段映射在 `aggregate_edges` 新建传播路径节点，并以 `source_edge_ref` 指向原始映射，供 `candidate-discovery` 构建 `cross_boundary_path` 和 `verification-and-rating` 核实传播完整性。
4. **连接键为稳定字段名**（DTO 字段名 / ORM 列名 / 消息字段名），不使用行号。

### 步骤四：按存储位置连接 storage_edges（二阶边）

1. 收集所有 WU 的 `storage_edges`。
2. 按 `storage_kind` + `key_or_table` 分组——同一张表 / 同一个缓存键模式 / 同一个文件路径的写入和读取分到一组。
3. 对每组，将 `write_wu_id` 和 `read_wu_id` 不同的输入事实连接为新的 `aggregate_edges` 二阶边，并以 `source_edge_ref` 指向原始存储边：写入端在某 WU 中执行 SQL INSERT/UPDATE、缓存 SET、文件 WRITE，读取端在另一 WU 中执行 SQL SELECT、缓存 GET、文件 READ——两端通过存储位置间接连接，不经过直接调用边。
4. **写入到读取的二阶边**：即使两个 WU 之间没有直接调用边，只要它们通过同一存储位置间接交换数据，就形成二阶边。这是跨 WU 传播路径的重要组成——很多漏洞的 Source 和 Sink 分处不同 WU，中间通过数据库/缓存/文件间接传递。
5. `read_symbol`/`read_wu_id` 仍为 null 的存储边保留为未解析连接（`unresolved_connections`），不声称"该存储位置无读取方"。

### 步骤五：按契约连接 transport_edges（生产者→消费者边）

1. 收集所有 WU 的 `transport_edges`。
2. 按 `transport_kind` + `channel` 分组——同一个 Topic/Queue、同一个 RPC 服务方法、同一个事件类型、同一个 WebSocket 端点的生产者和消费者分到一组。
3. 对每组，将 `producer_wu_id` 和 `consumer_wu_id` 不同的输入事实连接为新的 `aggregate_edges` 跨 WU 传输边，并以 `source_edge_ref` 指向原始传输边：生产者发布消息/事件/RPC 请求，消费者接收并处理。
4. **多仓服务契约**：当 `channel` 引用跨仓库服务契约时，连接键为契约标识（服务名+方法名+版本），而非仓库内符号名。
5. `consumer_symbol`/`consumer_wu_id` 仍为 null 的传输边保留为未解析连接，不声称"该 Topic/Queue 无消费者"。

### 步骤六：未解析连接保留为缺口

1. 汇聚后仍无法解析的 `unresolved_connections` 保留在汇聚产物中，作为缺口记录。
2. 缺口不等于"不存在"——未解析可能是因为目标 WU 尚未扫描、目标在其他仓库、动态分发目标不可静态确定或反射调用目标不可推断。
3. 未解析连接传递到 `verification-and-rating` 阶段，作为 Gate-2 跨 WU 抽查与第二意见的输入之一。

## 汇聚产物

多个 WU 参与时必须产出独立正式产物 `cross_boundary_aggregate`，并由 run-state 和 WU Manifest 的 `cross_boundary_aggregate_ref` 引用。其最小结构为：

```yaml
run_id: audit-20260808-001
source_revision: git:abc123+dirty
input_wu_ids: [WU-CD-001, WU-CD-002]
input_boundary_fact_versions:
  WU-CD-001: 0.2.0
  WU-CD-002: 0.2.0
aggregate_edges:
  - source_edge_ref: work-units/WU-CD-001-boundary-facts.md#call_edges/0
    edge_kind: direct_call
    from_wu_id: WU-CD-001
    to_wu_id: WU-CD-002
    from_symbol: app.entry
    to_symbol: service.handle
unresolved_connections: []
version: 0.2.0
```

`run_id`、`source_revision`、`input_wu_ids`、`input_boundary_fact_versions`、`aggregate_edges`、`unresolved_connections`、`version` 均为必填。每条新建的聚合边必须含 `source_edge_ref`；需要组合两条或更多输入边时可增加 `source_edge_refs`，但仍须保留一个主 `source_edge_ref`。聚合产物包含：

- **跨 WU 调用边**：根据冻结输入调用边解析后新建、且两端分属不同 WU 的 `aggregate_edges`。
- **跨 WU 字段映射**：根据冻结输入字段映射连接后新建、且两端分属不同 WU 的 `aggregate_edges`。
- **二阶存储边**：根据冻结输入存储事实连接写入端和读取端后新建的 `aggregate_edges`。
- **跨 WU 传输边**：根据冻结输入传输事实连接生产者和消费者后新建的 `aggregate_edges`。
- **未解析连接**：汇聚后仍无法解析的 `unresolved_connections`，作为缺口保留。

## 汇聚纪律

1. **不猜连接**：未找到匹配的连接保留为缺口，不得填写猜测的目标 WU ID。
2. **不删缺口**：未解析连接在汇聚产物中完整保留，不得静默丢弃。
3. **连接键用稳定标识**：稳定符号（函数全限定名/方法签名/接口方法名）、稳定字段名（DTO字段名/ORM列名/消息字段名）、存储位置（表名/缓存键模式/文件路径）、契约标识（服务名+方法名+版本）——不使用文件路径或行号作为跨 WU 连接键。
4. **汇聚后身份标注**：每条跨 WU 边必须标注两端的 `wu_id` 和 `source_edge_ref`，供下游追溯到冻结的原始 WU 分片。
5. **二阶边和传输边是跨 WU 传播的必要组成**：很多真实漏洞的 Source 和 Sink 不在同一 WU、不通过直接调用连接，而是通过数据库/缓存/文件/MQ/RPC 间接传递。汇聚必须覆盖二阶边和传输边，不能只连接直接调用边。
6. **汇聚与 WU 汇聚的关系**：本汇聚是边界事实的汇聚，与 WU Manifest 的候选分片汇聚是两个不同维度的汇聚——WU Manifest 汇聚候选清单，本汇聚连接跨 WU 边界路径。两者可以同一次执行中先后完成。
7. **原始边冻结**：输入 WU 的全部原始边及 `unresolved_connections` 在分片完成后冻结。汇聚只创建带 `source_edge_ref` 的新聚合边，不原地补目标、改 `resolved`、删缺口或改证据。

# Work Unit Manifest 模板

> **DEPRECATED（v0.11.0）**：WU 分片唯一 schema 为 `batches/B{NNN}/WU-NNNN.tsv`（5 列 TSV：`sink_id | verdict | five_segment_evidence | evidence_refs | reviewed_at`，见 [`../agents/wu-analyzer-prompt.md`](../agents/wu-analyzer-prompt.md)），本文档仅历史参考。

## 定位

**WU 等于批内最小追踪单元**：一批任务切分后，每个最小可追踪分片即一个 WU。WU 状态**靠输出分片文件的存在性判定**（幂等可续），不依赖内存枚举；主产物由宿主串行汇聚，WU 分片是可追溯输入，不直接替代主产物。

## WU 五态（靠分片文件存在性判定）

| 状态 | 判定依据 |
|---|---|
| 未开始 | 分片文件不存在 |
| 运行中 | 已派发，分片文件尚未产出 |
| 已完成 | 分片文件存在且非空（待验证） |
| 已验证 | 分片文件通过逐 WU 验证（文件存在 + 合法 JSON + wu_id + Schema 字段） |
| 失败 | 验证失败重试≤3 次仍失败，进 `failed_wus.txt` |

## Manifest 最小结构

```yaml
manifest_capability: candidate-discovery
run_id: audit-20260808-001
authorized_scope_ref: run-state.md#authorized_scope
work_units:
  - id: WU-CD-001
    scope:
      - src/auth/
    shard: work-units/WU-CD-001.json
    candidate_ids: []
    source_revision: git:abc123+dirty
    remaining_scope: []
    attempt: 1
    failure_reason: null
```

- `id` 稳定唯一；`shard` 为本 WU 唯一分片文件路径；`scope` 必须落在 `authorized_scope_ref` 引用的冻结授权范围内。
- `source_revision` 为创建时一次性写入的冻结值，此后不可变；变化时通过汇聚前身份检查发现不一致后重做受影响 WU。
- `candidate_ids` / `remaining_scope` 由宿主在汇聚时回填。

## 写入纪律

1. **各自分片**：每个 WU 只写自己的分片文件，禁止多个 WU 或 subagent 写同一分片或主产物。
2. **单层不嵌套**：子代理不再起子代理。
3. **串行汇聚**：主 agent 串行合并各分片；**合并前 count 临时文件数 == 批数**，按 shard 序号排序后串行合并（命令见 [`host-reconciliation-commands.md`](host-reconciliation-commands.md) 第5节）。
4. **逐 WU 验证**：分片文件存在 + 合法 JSON + wu_id + Schema 字段；失败重试≤3 次，仍失败进 `failed_wus.txt`（报告强制引用：应为空或逐条列入报告）。
5. **身份检查**：汇聚前逐项核对 `run_id` 等于当前 `run_id`、`source_revision` 等于当前源码 revision；任一不一致不得汇聚，先修正或重做受影响 WU。
6. 失败接管复用原 WU id 并递增 `attempt`，不删除失败记录后新建看似首次执行的 WU。

## 完成对账

只有全部 WU 分片进入"已验证"终态（或合法 `not_applicable`）、`failed_wus.txt` 为空或已列入报告、且主产物已串行汇聚完成时，WU 维度才算闭合；闭合等式 `planned == terminal` 见 [`check-unit-ledger-template.md`](check-unit-ledger-template.md)，在账本级执行，不在单个 WU 内执行。

# wu_dispatch.tsv 模板（v0.7.7）

> **DEPRECATED（v0.11.0）**：WU 分片唯一 schema 为 `batches/B{NNN}/WU-NNNN.tsv`（5 列 TSV：`sink_id | verdict | five_segment_evidence | evidence_refs | reviewed_at`，见 [`../agents/wu-analyzer-prompt.md`](../agents/wu-analyzer-prompt.md)），本文档仅历史参考。

每 WU 派发与验证的记录。gate 等式「WU 派发记录」检查：文件存在 + verified 列非空。

| 列 | 说明 |
|---|---|
| wu_id | WU-XXXX（与 wu_manifest.tsv 一致）|
| artifact_path | 该 WU 产物路径（batches/B{NNN}/WU-NNNN.tsv）|
| verified | bool：主代理验证产物通过=true |
| timestamp | UTC ISO 8601 |

```
wu_id	artifact_path	verified	timestamp
WU-0001	batches/B001/WU-0001.tsv	true	2026-01-01T00:00:00Z
```

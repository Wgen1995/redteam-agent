# Knowledge Session快照模板

本契约冻结一次run跨阶段共享的知识输入身份，不引入运行时代码。

```yaml
knowledge_snapshot_id: KS-audit-20260809-001
created_at: 2026-08-09T12:00:00Z
ontology_version: 1.0.0
knowledge_manifest_version: 2026-08-09
index_versions:
  vuln-patterns: 2.0.0
  attack-patterns: 1.0.0
  fix-patterns: 1.0.0
loaded_indexes:
  - knowledge/vuln-patterns/_index.md@index_version=2.0.0
loaded_entries:
  - knowledge/vuln-patterns/session-fixation-user-confusion.md
query_keys:
  - language:python
  - signal:session_regeneration
effective_discoverable:
  VULN-AC-SESSION-FIXATION-01: true
index_coverage_conflict: []
```

`knowledge_snapshot_id`在run初始化时创建并冻结。`loaded_indexes`记录实际读过的索引及版本，`loaded_entries`记录实际打开的条目，`query_keys`记录生态、语义和触发信号查询键；`effective_discoverable`是索引声明与覆盖矩阵交叉核对后的本次有效可发现性，冲突写入`index_coverage_conflict`并禁止把冲突条目当作完整模式命中。

candidate-discovery、verification-and-rating及下游知识消费必须引用同一ID和同一read-set。验证阶段复用候选阶段已冻结的`loaded_indexes`、`loaded_entries`和`query_keys`，不得对同一candidate重复搜索；确需新增查询时追加read-set并产生新快照，按Work Graph返工。知识revision变化时同样创建新快照ID，不原地修改旧快照。

# SRC-RFC3552 来源对账

> **来源账本引用**：source-ledgers/SRC-RFC3552.md
> **manifest引用**：industry-source-manifest.md SRC-RFC3552 行

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | COV-SRC-RFC3552 |
| source_ledger_ref | SRC-RFC3552 |
| version | v0.1 |
| source | IETF RFC 3552 - Guidelines for Writing RFC Text on Security Considerations |
| consumers | report-delivery, knowledge-evolution |

## 对账摘要

| source_id | raw_entry_count | mapped | pending_adjudication | out_of_scope_with_reason | instance_only | 差额 |
|---|---:|---:|---:|---:|---:|---:|
| SRC-RFC3552 | 13 | 0 | 13 | 0 | 0 | 0 |

## 映射状态说明

> mapped=0 说明：RFC3552 的 13 条安全考量章节（raw_entry_count=13）当前全部处于 `pending_adjudication`，尚未逐条映射到 UVS/ADJ 条目。mapped=0 表示来源条目尚未完成语义映射（对账尚未推进到映射阶段），不是“无内容”或“不可映射”；待逐条裁决后 mapped 将上升、pending 相应下降，差额保持为 0。

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | SRC-RFC3552 | 来源账本 |
| `externally_mapped_to` | industry-source-manifest.md | 来源manifest |

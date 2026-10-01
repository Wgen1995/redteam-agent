# SRC-SLSA 来源对账

> **来源账本引用**：source-ledgers/SRC-SLSA.md
> **manifest引用**：industry-source-manifest.md SRC-SLSA 行

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | COV-SRC-SLSA |
| source_ledger_ref | SRC-SLSA |
| version | v0.1 |
| source | SLSA Specification v1.0 |
| consumers | report-delivery, knowledge-evolution |

## 对账摘要

| source_id | raw_entry_count | mapped | pending_adjudication | out_of_scope_with_reason | instance_only | 差额 |
|---|---:|---:|---:|---:|---:|---:|
| SRC-SLSA | 5 | 0 | 5 | 0 | 0 | 0 |

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | SRC-SLSA | 来源账本 |
| `externally_mapped_to` | industry-source-manifest.md | 来源manifest |

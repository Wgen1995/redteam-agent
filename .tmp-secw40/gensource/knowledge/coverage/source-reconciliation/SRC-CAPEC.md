# SRC-CAPEC 来源对账

> **来源账本引用**：source-ledgers/SRC-CAPEC.md
> **manifest引用**：industry-source-manifest.md SRC-CAPEC 行

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | COV-SRC-CAPEC |
| source_ledger_ref | SRC-CAPEC |
| version | v0.1 |
| source | MITRE CAPEC 3.9 Comprehensive Dictionary |
| consumers | report-delivery, knowledge-evolution |

## 对账摘要

| source_id | raw_entry_count | mapped | pending_adjudication | out_of_scope_with_reason | instance_only | 差额 |
|---|---:|---:|---:|---:|---:|---:|
| SRC-CAPEC | 706 | 0 | 706 | 0 | 0 | 0 |

## 原始条目ID集合核对

> 实际ID集合与manifest记录的分母逐项核对，差额必须为0。

| 核对项 | 值 |
|---|---|
| manifest记录的原始条目总数 | 706（559 Attack Patterns + 21 Categories + 13 Views + 113 Deprecated） |
| 账本实际记录的原始条目总数 | 706 |
| 差额 | 0 |

### 类型分布核对

| 类型 | manifest记录 | 账本实际 | 差额 |
|---|---:|---:|---:|
| Meta Attack Pattern | 61 | 61 | 0 |
| Standard Attack Pattern | 181 | 181 | 0 |
| Detailed Attack Pattern | 317 | 317 | 0 |
| Category | 21 | 21 | 0 |
| View | 13 | 13 | 0 |
| Deprecated | 113 | 113 | 0 |
| **Total** | **706** | **706** | **0** |

### Attack Pattern子类型明细

| raw_kind | 数量 |
|---|---:|
| Meta Attack Pattern | 61 |
| Standard Attack Pattern | 181 |
| Detailed Attack Pattern | 317 |
| **Attack Pattern合计** | **559** |

## 实际提取的CAPEC编号集合

> 共 706 个CAPEC编号，编号范围 CAPEC-1 至 CAPEC-3000（非连续，CAPEC编号存在间隔）。

### 编号间隔说明

CAPEC编号非连续分配，以下编号范围在CAPEC 3.9中未分配或已废弃后跳过：
- CAPEC-704 至 CAPEC-999（未分配）
- CAPEC-1001 至 CAPEC-1999（未分配）
- CAPEC-2001 至 CAPEC-2999（未分配）
- 部分1-703范围内的编号因条目废弃而跳过（见Deprecated条目）

这是CAPEC编号分配的正常现象，不影响条目总数对账。

## 与manifest差异

| 核对项 | manifest记录 | 实际提取 | 差异 |
|---|---|---|---|
| 总条目数 | 706 | 706 | 无 |
| Attack Pattern数 | 559 | 559 | 无 |
| Category数 | 21 | 21 | 无 |
| View数 | 13 | 13 | 无 |
| Deprecated数 | 113 | 113 | 无 |

**结论**：实际提取的条目总数及各类型数量与manifest记录完全一致，无差异。

## 消费方

- report-delivery：报告交付能力引用对账状态披露来源覆盖完整性
- knowledge-evolution：知识进化能力消费对账状态进行版本管理

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | SRC-CAPEC | 来源账本 |
| `externally_mapped_to` | industry-source-manifest.md | 来源manifest |

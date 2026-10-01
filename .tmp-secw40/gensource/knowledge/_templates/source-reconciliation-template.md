# COV-SRC-XXX：来源对账记录名称

> **模板不计入正式知识条目，不构成检测能力，仅供编写时参考。**
> 本文件是编写来源对账记录时的结构参考，不是已确认的知识内容。填写后需经人工复核并纳入变更批次才能成为正式知识。

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | COV-SRC-XXX |
| source_ledger_ref | SRC-XXX（来源账本引用） |
| version | v0.1 |
| source | 来源引用 |
| consumers | 消费此对账记录的GenSource能力列表 |

## 对账摘要

| 字段 | 值 |
|---|---|
| 来源账本 | SRC-XXX |
| manifest原始条目数 | N |
| 账本实际记录数 | N |
| 差额 | 0 |
| mapped数 | N |
| pending_adjudication数 | N |

## 原始条目ID集合核对

> 实际ID集合与manifest记录的分母逐项核对，差额必须为0。

| 核对项 | 值 |
|---|---|
| manifest记录的原始条目ID集合 | {id1, id2, ...} |
| 账本实际记录的原始条目ID集合 | {id1, id2, ...} |
| 差额ID | 无 |

## 正例

正确对账的示例。

## 负例

错误对账的反例。

## 消费方

- 消费此对账记录的GenSource能力
- 消费方式

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | SRC-XXX | 来源账本 |
| `externally_mapped_to` | industry-source-manifest.md | 来源manifest |

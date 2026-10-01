# ADJ-XXX：裁决记录名称

> **模板不计入正式知识条目，不构成检测能力，仅供编写时参考。**
> 本文件是编写裁决记录时的结构参考，不是已确认的知识内容。填写后需经人工复核并纳入变更批次才能成为正式知识。

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ADJ-XXX |
| version | v0.1 |
| source | 来源引用（来源账本ID/原始条目ID） |
| consumers | 消费此裁决的GenSource能力列表 |

## 裁决对象

raw_entry_ref：无法归并的原始条目引用。

| 来源账本 | 原始条目ID | 原始名称 |
|---|---|---|
| SRC-XXX | raw_entry_id | raw_name |

## 候选目标

candidate_uvs：候选映射的统一语义ID（若存在争议目标）。

| 候选UVS | 候选理由 |
|---|---|
| UVS-XXX | 为何认为可能映射到此 |

## 支持证据

evidence_for：支持映射到某个UVS的证据。

| 证据 | 说明 |
|---|---|
| 证据描述 | 为什么这条证据支持该映射 |

## 反对证据

evidence_against：反对映射到某个UVS的证据。

| 证据 | 说明 |
|---|---|
| 证据描述 | 为什么这条证据反对该映射 |

## 影响

若裁决结果为新建UVS或拒绝映射，对覆盖矩阵的影响。

## 所需证据

required_evidence：做出最终裁决还需要补充的证据。

| 所需证据 | 获取方式 | 责任方 |
|---|---|---|
| 证据描述 | 如何获取 | 谁负责 |

## 裁决结论

- 当前状态：pending / resolved_mapped / resolved_rejected / resolved_new_uvs
- 最终映射：（若resolved）
- 理由：（若resolved）

## 正例

正确裁决的示例。

## 负例

错误裁决的反例。

## 消费方

- 消费此裁决的GenSource能力
- 消费方式

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | SRC-XXX | 来源账本 |
| `externally_mapped_to` | UVS-XXX（若resolved） | 最终映射的统一语义 |

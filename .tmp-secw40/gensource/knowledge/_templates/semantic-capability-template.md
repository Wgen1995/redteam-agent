# COV-CAP-XXX：语义能力覆盖记录名称

> **模板不计入正式知识条目，不构成检测能力，仅供编写时参考。**
> 本文件是编写语义能力覆盖记录时的结构参考，不是已确认的知识内容。填写后需经人工复核并纳入变更批次才能成为正式知识。

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | COV-CAP-XXX |
| uvs_ref | UVS-XXX（统一语义引用） |
| version | v0.1 |
| source | 来源引用 |
| consumers | 消费此覆盖记录的GenSource能力列表 |

## 八维能力状态

> 状态只允许：complete / partial / not_started / not_applicable / blocked。
> N/A和blocked必须有理由及证据。
> 禁止由名称映射自动推导检测能力。

| 维度 | 状态 | 证据引用 | 理由（若N/A或blocked） |
|---|---|---|---|
| cataloged | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| modeled | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| discoverable | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| verifiable | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| exploit_model_available | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| remediable | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| ecosystem_mapped | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |
| validated | complete/partial/not_started/not_applicable/blocked | 证据 | 理由 |

## 维度要求

| 维度 | 达到complete的要求 |
|---|---|
| cataloged | UVS已建立且来源对账完成 |
| modeled | 本体路径/根因/不变量/正反例齐备 |
| discoverable | 存在可执行发现模式（vuln-patterns条目） |
| verifiable | 存在确认与反证方法（verification能力可消费） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） |
| remediable | 存在标准修复模式（fix-patterns条目） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） |
| validated | 有实证证据（实测案例/外部验证） |

## 正例

正确覆盖评估的示例。

## 负例

错误覆盖评估的反例——特别是仅凭名称映射推断检测能力的情况。

## 消费方

- 消费此覆盖记录的GenSource能力
- 消费方式

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | UVS-XXX | 统一语义引用 |
| `externally_mapped_to` | coverage/_index.md | 覆盖矩阵入口 |

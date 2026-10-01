# SRC-XXX：来源名称 来源账本

> **模板不计入正式知识条目，不构成检测能力，仅供编写时参考。**
> 本文件是编写行业来源账本时的结构参考，不是已确认的知识内容。填写后需经人工复核并纳入变更批次才能成为正式知识。

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | SRC-XXX |
| source_manifest_ref | industry-source-manifest.md 中对应来源行 |
| version | v0.1 |
| source | 官方名称/URL/版本/冻结日期 |
| consumers | 消费此账本的GenSource能力列表 |

## 来源信息

- 官方名称：
- 官方URL：
- 来源类型：（标准/攻击知识库/漏洞数据库/语言安全规则/其他）
- 冻结版本或快照：
- 发布日期：
- 抓取日期：
- 许可：
- 原始条目定义：
- 原始条目数：（附计数证据）

## 原始条目对账表

> 每条原始记录恰好一行，禁止单元格内换行。`reconciliation_status` 只允许 `mapped` 或 `pending_adjudication`。

| raw_entry_id | raw_name | raw_kind | official_ref | raw_status | candidate_semantic_refs | reconciliation_status | adjudication_ref | notes |
|---|---|---|---|---|---|---|---|---|
| 原始条目ID | 原始名称 | 原始类型 | 官方引用链接 | 原始状态 | 候选统一语义ID | mapped/pending_adjudication | ADJ-* 引用（若pending） | 备注 |

## 正例

正确对账的示例——一条原始条目如何映射到统一语义。

## 负例

错误对账的反例——常见的误归并方式。

## 消费方

- 消费此账本的GenSource能力
- 消费方式

## 关系引用

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `externally_mapped_to` | UVS-XXX | 原始条目映射到的统一语义 |
| `receives_from` | industry-source-manifest.md | 来源manifest |

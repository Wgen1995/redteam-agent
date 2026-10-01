# 行业目录索引（industry-catalog/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务4-6。本文件是行业目录的索引入口，说明来源账本、统一漏洞语义和裁决记录的组织结构。

## 目录结构

```text
industry-catalog/
  _index.md                       本文件
  industry-source-manifest.md     行业来源manifest，冻结全部来源版本与元数据
  source-ledgers/                 来源账本（SRC-*.md），保存原始分类
  semantics/                      统一漏洞语义（UVS-*.md），去重和关系整理
  adjudication/                   裁决记录（ADJ-*.md），无法归并的原始条目
```

## 工作流程

```text
官方来源 ──人工转录──> source-ledgers/（原始分类）
                              │
                    ┌─────────┴──────────┐
                    │                    │
              可归并映射            无法归并
                    │                    │
                    ▼                    ▼
          semantics/（UVS-*.md）   adjudication/（ADJ-*.md）
          去重和关系整理            裁决记录
```

## 来源账本（source-ledgers/）

来源账本保存原始分类——每个官方来源一个账本文件（SRC-*.md），按官方来源显示顺序人工转录全部原始条目。

每条原始记录恰好一行，禁止单元格内换行。`reconciliation_status` 只允许 `mapped`（已映射到统一语义）或 `pending_adjudication`（需裁决）。

| 字段 | 含义 |
|---|---|
| raw_entry_id | 原始条目ID |
| raw_name | 原始名称 |
| raw_kind | 原始类型（Category/View/Deprecated/Attack Pattern/Requirement等） |
| official_ref | 官方引用 |
| raw_status | 原始状态 |
| candidate_semantic_refs | 候选统一语义ID |
| reconciliation_status | mapped / pending_adjudication |
| adjudication_ref | ADJ-* 引用（若pending） |
| notes | 备注 |

## 统一漏洞语义（semantics/）

统一漏洞语义进行去重和关系整理——同义外部项映射同一UVS；仅API或框架名称不同的内容进入生态变体；根因不同则拆分。

每个UVS记录：规范名称、定义、根因、失败安全不变量、manifest版本、上下位语义、同义词、根因/表现/影响区分、本体路径、适用Surface/Entry、控制失效、Sink/状态/资源效果、Oracle、影响、正反例、排除、外部映射、生态变体和三库引用。

## 裁决记录（adjudication/）

裁决记录处理无法归并的原始条目——每个ADJ记录候选目标、支持/反对证据、影响、所需证据和责任方。

非漏洞节点、实例型CVE/GHSA、废弃项或看似不适用项也必须创建裁决记录，由裁决说明为何不新建UVS，不能绕过逐项裁决。

## 当前状态

| 子目录 | 条目数 | 状态 |
|---|---|---|
| source-ledgers/ | 1（SRC-CWE，1450条原始条目） | SRC-CWE已填充；122个Pillar/Class条目已完成语义归并 |
| semantics/ | 94 | CWE Pillar/Class级别语义归并完成（任务6a） |
| adjudication/ | 12 | CWE Pillar/Class级别元类别裁决完成（任务6a） |

## 消费方

- `candidate-discovery`：候选发现能力消费统一漏洞语义进行模式驱动发现
- `verification-and-rating`：验证与定级能力消费统一漏洞语义的根因/不变量/本体路径
- `remediation-guidance`：修复指导能力消费统一漏洞语义的三库引用
- `report-delivery`：报告交付能力消费统一漏洞语义的外部映射（CWE/CAPEC/OWASP）

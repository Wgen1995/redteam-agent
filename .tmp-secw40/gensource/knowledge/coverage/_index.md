# 覆盖矩阵入口（coverage/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务7。本文件是覆盖矩阵的入口，说明来源对账和语义能力覆盖的组织结构。

## 目录结构

```text
coverage/
  _index.md                    本文件
  batch-ledger.md              知识建设批次台账
  skill-consumption.md         Skill消费索引
  source-reconciliation/       来源对账记录（COV-SRC-*.md）
  semantic-capability/         语义能力覆盖记录（COV-CAP-*.md）
```

## 核心原则

**禁止由名称映射自动推导检测能力**——cataloged（已编目）不等于discoverable（可发现）。一个统一漏洞语义被编目到知识库中，不代表GenSource具备自动发现这个漏洞的能力。检测能力需要可执行的发现模式支撑，不是名称匹配。

## 来源对账（source-reconciliation/）

来源对账记录追踪每个来源账本的原始条目是否全部完成对账——实际ID集合与manifest记录的分母逐项核对，差额必须为0。

每个来源一个对账记录（COV-SRC-*.md），记录对账摘要、原始条目ID集合核对和差额。

## 语义能力覆盖（semantic-capability/）

语义能力覆盖记录追踪每个统一漏洞语义在八个维度上的能力状态：

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

状态只允许：`complete` / `partial` / `not_started` / `not_applicable` / `blocked`。N/A和blocked必须有理由及证据。

## 当前状态

| 子目录 | 条目数 | 状态 |
|---|---|---|
| source-reconciliation/ | 28 | 部分完成：28 个记录文件齐全；但按实际 grep 结果，13 个 raw_entry_count 仍为"待人工核实"（分母未定）、15 个已定分母（差额=0）；全部 28 个 mapped=0、pending_adjudication=全量——0 条原始条目已映射到 UVS，未 100% reconciled |
| semantic-capability/ | 27 | 已完成（27个域分片覆盖记录） |

## 消费方

- `scope-and-context`：范围与威胁语境能力引用覆盖状态披露知识缺口
- `candidate-discovery`：候选发现能力引用discoverable状态判断模式驱动命中的有效性
- `verification-and-rating`：验证与定级能力引用verifiable状态判断验证方法可用性
- `report-delivery`：报告交付能力引用覆盖矩阵披露检测能力边界

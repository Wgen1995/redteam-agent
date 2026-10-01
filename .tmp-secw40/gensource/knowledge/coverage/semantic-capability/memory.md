# 内存能力覆盖

> 分片文件：memory域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（5个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-MEM-BOUNDS-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-MEM-BOUNDS-FAILURE.md | |
| UVS-MEM-INDEX-ACCESS-ERROR | complete | complete | 信号级（不进实例清单） | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-MEM-INDEX-ACCESS-ERROR.md | |
| UVS-MEM-LAYOUT-RELIANCE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-MEM-LAYOUT-RELIANCE.md | |
| UVS-MEM-NULL-TERMINATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-MEM-NULL-TERMINATION.md | |
| UVS-MEM-UNTRUSTED-POINTER | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-MEM-UNTRUSTED-POINTER.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 4 complete + 1 信号级（不进实例清单）（MEM-INDEX 命中仅作浅扫过滤，不逐条进 sink_inventory） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns含验证方法/反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 全部complete（KBATCH-003创建5个attack-patterns） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（KBATCH-003创建5个fix-patterns） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |
| validated | 有实证证据（实测案例/外部验证） | 全部not_started（Inferred级别，无GenSource实测案例） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 5 | 0 | 0 | 0 | 0 |
| modeled | 5 | 0 | 0 | 0 | 0 |
| discoverable | 4 | 0 | 0 | 0 | 0 |
| verifiable | 5 | 0 | 0 | 0 | 0 |
| exploit_model_available | 5 | 0 | 0 | 0 | 0 |
| remediable | 5 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 5 | 0 | 0 | 0 |
| validated | 0 | 0 | 5 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

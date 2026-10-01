# 输入验证能力覆盖

> 分片文件：input域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（9个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-INPUT-CASE-SENSITIVITY | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-CASE-SENSITIVITY.md | |
| UVS-INPUT-DATA-COLLAPSE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-DATA-COLLAPSE.md | |
| UVS-INPUT-HANDLING-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-HANDLING-FAILURE.md | |
| UVS-INPUT-INCORRECT-REGEX | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-INCORRECT-REGEX.md | |
| UVS-INPUT-INVALID-STRUCTURE-HANDLING | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-INVALID-STRUCTURE-HANDLING.md | |
| UVS-INPUT-MISINTERPRETATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-MISINTERPRETATION.md | |
| UVS-INPUT-SPECIAL-ELEMENT-HANDLING | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-SPECIAL-ELEMENT-HANDLING.md | |
| UVS-INPUT-VALIDATION-FAILURE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-VALIDATION-FAILURE.md | 抽象根模式，无独立活攻击面——具体利用手法见各子模式对应attack-pattern |
| UVS-INPUT-XML-VALIDATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INPUT-XML-VALIDATION.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003创建9个vuln-patterns） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns含验证方法/反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 8个complete（KBATCH-003创建8个attack-patterns），1个not_applicable（UVS-INPUT-VALIDATION-FAILURE为抽象根模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（KBATCH-003创建9个fix-patterns） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |
| validated | 有实证证据（实测案例/外部验证） | 全部not_started（Inferred级别，无GenSource实测案例） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 9 | 0 | 0 | 0 | 0 |
| modeled | 9 | 0 | 0 | 0 | 0 |
| discoverable | 9 | 0 | 0 | 0 | 0 |
| verifiable | 9 | 0 | 0 | 0 | 0 |
| exploit_model_available | 8 | 0 | 0 | 1 | 0 |
| remediable | 9 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 9 | 0 | 0 | 0 |
| validated | 0 | 0 | 9 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

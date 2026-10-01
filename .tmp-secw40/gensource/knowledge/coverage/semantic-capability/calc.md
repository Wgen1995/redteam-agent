# 计算能力覆盖

> 分片文件：calc域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（4个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-CALC-COMPARISON-FAILURE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CALC-COMPARISON-FAILURE.md; vuln-patterns/calc-comparison-error.md; attack-patterns/calc-comparison-bypass-benign.md; fix-patterns/calc-comparison-correct-equals.md | |
| UVS-CALC-FAILURE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CALC-FAILURE.md; vuln-patterns/calc-integer-overflow.md; attack-patterns/calc-integer-overflow-benign.md; fix-patterns/calc-integer-overflow-check.md | |
| UVS-CALC-INCOMPLETE-COMPARISON | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CALC-INCOMPLETE-COMPARISON.md; vuln-patterns/calc-incomplete-comparison.md; attack-patterns/calc-incomplete-comparison-benign.md; fix-patterns/calc-incomplete-full-comparison.md | |
| UVS-CALC-LENGTH-PARAMETER | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CALC-LENGTH-PARAMETER.md; vuln-patterns/calc-length-parameter-mismatch.md; attack-patterns/calc-length-mismatch-benign.md; fix-patterns/calc-length-validation.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003创建vuln-patterns条目） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（KBATCH-003 vuln-patterns含验证方法/反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 全部complete（KBATCH-003创建attack-patterns条目） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（KBATCH-003创建fix-patterns条目） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部not_started（ecosystem-mappings条目尚未创建） |
| validated | 有实证证据（实测案例/外部验证） | 全部not_started（正例负例均为代码示例，真实案例验证尚未进行） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 4 | 0 | 0 | 0 | 0 |
| modeled | 4 | 0 | 0 | 0 | 0 |
| discoverable | 4 | 0 | 0 | 0 | 0 |
| verifiable | 4 | 0 | 0 | 0 | 0 |
| exploit_model_available | 4 | 0 | 0 | 0 | 0 |
| remediable | 4 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 0 | 4 | 0 | 0 |
| validated | 0 | 0 | 4 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

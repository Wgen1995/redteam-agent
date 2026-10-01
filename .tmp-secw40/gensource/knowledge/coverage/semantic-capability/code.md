# 代码能力覆盖

> 分片文件：代码域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（7个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-CODE-DANGEROUS-FUNCTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-DANGEROUS-FUNCTION.md; vuln-patterns/code-dangerous-function-usage.md; attack-patterns/code-dangerous-function-benign-probe.md; fix-patterns/code-replace-dangerous-functions.md | |
| UVS-CODE-DYNAMIC-CONTROL-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-DYNAMIC-CONTROL-FAILURE.md; vuln-patterns/code-dynamic-control-missing.md; attack-patterns/code-dynamic-control-benign-probe.md; fix-patterns/code-dynamic-control-whitelist.md | |
| UVS-CODE-EMBEDDED-MALICIOUS | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-EMBEDDED-MALICIOUS.md; vuln-patterns/code-embedded-malicious.md; attack-patterns/code-embedded-malicious-benign-probe.md; fix-patterns/code-supply-chain-verification.md | |
| UVS-CODE-HIDDEN-FUNCTIONALITY | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-HIDDEN-FUNCTIONALITY.md; vuln-patterns/code-hidden-functionality.md; attack-patterns/code-hidden-functionality-benign-probe.md; fix-patterns/code-remove-hidden-functionality.md | |
| UVS-CODE-PROHIBITED-USAGE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-PROHIBITED-USAGE.md; vuln-patterns/code-prohibited-usage.md; attack-patterns/code-prohibited-usage-benign-probe.md; fix-patterns/code-enforce-prohibited-usage-rules.md | |
| UVS-CODE-SPECIFICATION-MISMATCH | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-SPECIFICATION-MISMATCH.md; vuln-patterns/code-specification-mismatch.md; attack-patterns/code-spec-mismatch-benign-probe.md; fix-patterns/code-align-implementation-to-spec.md | |
| UVS-CODE-UNDEFINED-BEHAVIOR | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CODE-UNDEFINED-BEHAVIOR.md; vuln-patterns/code-undefined-behavior.md; attack-patterns/code-undefined-behavior-benign-probe.md; fix-patterns/code-eliminate-undefined-behavior.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003已创建vuln-patterns条目，含逐步发现步骤/正例/负例/排除条件） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目含验证方法/反证方法/Observable Oracle） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 全部complete（KBATCH-003已创建attack-patterns条目） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（KBATCH-003已创建fix-patterns条目） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 7 | 0 | 0 | 0 | 0 |
| modeled | 7 | 0 | 0 | 0 | 0 |
| discoverable | 7 | 0 | 0 | 0 | 0 |
| verifiable | 7 | 0 | 0 | 0 | 0 |
| exploit_model_available | 7 | 0 | 0 | 0 | 0 |
| remediable | 7 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 7 | 0 | 0 | 0 |
| validated | 0 | 0 | 7 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

# 注入能力覆盖

> 分片文件：injection域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（12个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-INJ-CODE-INJECTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-CODE-INJECTION.md, vuln-patterns/inj-code-injection.md | |
| UVS-INJ-COMMAND-INJECTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-COMMAND-INJECTION.md, vuln-patterns/inj-command-injection.md | |
| UVS-INJ-CRLF | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-CRLF.md, vuln-patterns/inj-crlf-injection.md | |
| UVS-INJ-DESERIALIZATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-DESERIALIZATION.md, vuln-patterns/inj-deserialization.md | |
| UVS-INJ-FORMAT-STRING | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-FORMAT-STRING.md, vuln-patterns/inj-format-string.md | |
| UVS-INJ-NEUTRALIZATION-FAILURE | complete | complete | complete | complete | not_applicable | not_applicable | partial | not_started | industry-catalog/semantics/UVS-INJ-NEUTRALIZATION-FAILURE.md, vuln-patterns/inj-neutralization-failure.md | 抽象根模式——具体攻击/修复模式由各子UVS条目承载 |
| UVS-INJ-QUERY-INJECTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-QUERY-INJECTION.md, vuln-patterns/sql-injection-string-concat.md | |
| UVS-INJ-RESOURCE-INJECTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-RESOURCE-INJECTION.md, vuln-patterns/inj-resource-injection.md | |
| UVS-INJ-SPECIAL-ELEMENT-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-SPECIAL-ELEMENT-FAILURE.md, vuln-patterns/inj-special-element-failure.md | |
| UVS-INJ-SSRF | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-SSRF.md, vuln-patterns/inj-ssrf.md | |
| UVS-INJ-XSS | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-XSS.md, vuln-patterns/template-autoescape-disabled-xss.md, vuln-patterns/raw-output-no-escaping-xss.md | |
| UVS-INJ-XXE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INJ-XXE.md, vuln-patterns/inj-xxe.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-002：12个vuln-patterns条目已创建，含逐步可执行发现步骤） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（KBATCH-002：12个vuln-patterns条目均含验证方法和反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 11个complete+1个not_applicable（KBATCH-002：11个attack-patterns条目已创建；UVS-INJ-NEUTRALIZATION-FAILURE为抽象根模式，具体攻击模式由各子UVS承载） |
| remediable | 存在标准修复模式（fix-patterns条目） | 11个complete+1个not_applicable（KBATCH-002：11个fix-patterns条目已创建；UVS-INJ-NEUTRALIZATION-FAILURE为抽象根模式，具体修复模式由各子UVS承载） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 12 | 0 | 0 | 0 | 0 |
| modeled | 12 | 0 | 0 | 0 | 0 |
| discoverable | 12 | 0 | 0 | 0 | 0 |
| verifiable | 12 | 0 | 0 | 0 | 0 |
| exploit_model_available | 11 | 0 | 0 | 1 | 0 |
| remediable | 11 | 0 | 0 | 1 | 0 |
| ecosystem_mapped | 0 | 12 | 0 | 0 | 0 |
| validated | 0 | 0 | 12 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

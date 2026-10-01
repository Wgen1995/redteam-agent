# 异常处理能力覆盖

> 分片文件：exception域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（4个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-EXC-FAILURE | complete | complete | complete | complete | not_applicable | not_applicable | partial | not_started | industry-catalog/semantics/UVS-EXC-FAILURE.md; vuln-patterns/exc-generic-handling-failure.md; ecosystem-mappings/ECO-PYTHON.md; ecosystem-mappings/ECO-JAVA.md; ecosystem-mappings/ECO-GO.md; ecosystem-mappings/ECO-JAVASCRIPT.md | 抽象根模式——无独立攻击/修复模式，使用具体子模式 |
| UVS-EXC-IMPROPER-CHECK | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-EXC-IMPROPER-CHECK.md; vuln-patterns/exc-unchecked-return-value.md; attack-patterns/exc-unchecked-error-path-benign.md; fix-patterns/exc-unchecked-check-return-value.md; ecosystem-mappings/ECO-JAVA.md; ecosystem-mappings/ECO-GO.md | |
| UVS-EXC-IMPROPER-HANDLING | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-EXC-IMPROPER-HANDLING.md; vuln-patterns/exc-swallowed-exception.md; attack-patterns/exc-swallowed-exception-benign.md; fix-patterns/exc-swallowed-proper-handling.md; ecosystem-mappings/ECO-PYTHON.md; ecosystem-mappings/ECO-JAVASCRIPT.md | |
| UVS-EXC-INSECURE-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-EXC-INSECURE-FAILURE.md; vuln-patterns/exc-fail-open-on-error.md; attack-patterns/exc-failopen-benign.md; fix-patterns/exc-failopen-fail-closed.md; ecosystem-mappings/ECO-PYTHON.md; ecosystem-mappings/ECO-JAVA-SPRING.md; ecosystem-mappings/ECO-PYTHON-FLASK.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003创建vuln-patterns条目） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（KBATCH-003 vuln-patterns含验证方法/反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 3个complete（KBATCH-003创建attack-patterns条目）；1个not_applicable（UVS-EXC-FAILURE为抽象根模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 3个complete（KBATCH-003创建fix-patterns条目）；1个not_applicable（UVS-EXC-FAILURE为抽象根模式） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |
| validated | 有实证证据（实测案例/外部验证） | 全部not_started（正例负例均为代码示例，真实案例验证尚未进行） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 4 | 0 | 0 | 0 | 0 |
| modeled | 4 | 0 | 0 | 0 | 0 |
| discoverable | 4 | 0 | 0 | 0 | 0 |
| verifiable | 4 | 0 | 0 | 0 | 0 |
| exploit_model_available | 3 | 0 | 0 | 1 | 0 |
| remediable | 3 | 0 | 0 | 1 | 0 |
| ecosystem_mapped | 0 | 4 | 0 | 0 | 0 |
| validated | 0 | 0 | 4 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

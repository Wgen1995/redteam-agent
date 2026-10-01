# 保护机制能力覆盖

> 分片文件：protection域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（6个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-PROT-ADMIN-CONTROL-FAILURE | complete | complete | complete | complete | not_applicable | complete | not_started | not_started | industry-catalog/semantics/UVS-PROT-ADMIN-CONTROL-FAILURE.md; vuln-patterns/prot-admin-control-missing.md; fix-patterns/prot-adminctrl-configurable-security.md; vuln-patterns/dead-security-control.md; fix-patterns/dead-control-assembly.md | 无独立活攻击面——治理性质信号 |
| UVS-PROT-CLIENT-SIDE-ENFORCEMENT | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-PROT-CLIENT-SIDE-ENFORCEMENT.md; vuln-patterns/prot-client-side-enforcement.md; attack-patterns/prot-clientside-bypass-benign.md; fix-patterns/prot-clientside-server-side-validation.md | |
| UVS-PROT-FAILURE | complete | complete | complete | complete | not_applicable | not_applicable | not_started | not_started | industry-catalog/semantics/UVS-PROT-FAILURE.md; vuln-patterns/prot-protection-bypass.md | 抽象根模式——无独立攻击/修复模式，使用具体子模式 |
| UVS-PROT-GUESSABLE-CHALLENGE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-PROT-GUESSABLE-CHALLENGE.md; vuln-patterns/prot-guessable-challenge.md; attack-patterns/prot-guessable-captcha-benign.md; fix-patterns/prot-guessable-strong-captcha.md | |
| UVS-PROT-OBSCURITY-RELIANCE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-PROT-OBSCURITY-RELIANCE.md; vuln-patterns/prot-obscurity-reliance.md; attack-patterns/prot-obscurity-discover-benign.md; fix-patterns/prot-obscurity-independent-controls.md | |
| UVS-PROT-SINGLE-FACTOR-RELIANCE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-PROT-SINGLE-FACTOR-RELIANCE.md; vuln-patterns/prot-single-factor-reliance.md; attack-patterns/prot-singlefactor-bypass-benign.md; fix-patterns/prot-singlefactor-add-mfa.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003创建vuln-patterns条目） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（KBATCH-003 vuln-patterns含验证方法/反证方法） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 4个complete（KBATCH-003创建attack-patterns条目）；2个not_applicable（UVS-PROT-FAILURE为抽象根模式，UVS-PROT-ADMIN-CONTROL-FAILURE无独立活攻击面） |
| remediable | 存在标准修复模式（fix-patterns条目） | 5个complete（KBATCH-003创建fix-patterns条目）；1个not_applicable（UVS-PROT-FAILURE为抽象根模式） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部not_started（ecosystem-mappings条目尚未创建） |
| validated | 有实证证据（实测案例/外部验证） | 全部not_started（正例负例均为代码示例，真实案例验证尚未进行） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 6 | 0 | 0 | 0 | 0 |
| modeled | 6 | 0 | 0 | 0 | 0 |
| discoverable | 6 | 0 | 0 | 0 | 0 |
| verifiable | 6 | 0 | 0 | 0 | 0 |
| exploit_model_available | 4 | 0 | 0 | 2 | 0 |
| remediable | 5 | 0 | 0 | 1 | 0 |
| ecosystem_mapped | 0 | 0 | 6 | 0 | 0 |
| validated | 0 | 0 | 6 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

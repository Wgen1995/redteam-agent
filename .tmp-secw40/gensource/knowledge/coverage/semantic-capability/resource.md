# 资源生命周期能力覆盖

> 分片文件：resource域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（15个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-RES-DUPLICATE-IDENTIFIER | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-DUPLICATE-IDENTIFIER.md; vuln-patterns/res-duplicate-identifier.md; fix-patterns/res-unique-identifier.md | exploit_model:重复标识符导致资源混淆而非可利用攻击 |
| UVS-RES-EMERGENT-RESOURCE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-EMERGENT-RESOURCE.md; vuln-patterns/res-emergent-resource.md; fix-patterns/res-emergent-resource-management.md | exploit_model:涌现资源通过间接触发泄漏 |
| UVS-RES-EXCESSIVE-ITERATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-EXCESSIVE-ITERATION.md; vuln-patterns/res-excessive-iteration.md; attack-patterns/res-iteration-benign-timeout.md; fix-patterns/res-iteration-upper-bound.md | |
| UVS-RES-IMPROPER-RELEASE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-IMPROPER-RELEASE.md; vuln-patterns/res-improper-release.md; fix-patterns/res-guaranteed-release.md | exploit_model:资源泄漏通过反复请求间接触发 |
| UVS-RES-INEFFICIENT-COMPLEXITY | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-INEFFICIENT-COMPLEXITY.md; vuln-patterns/res-inefficient-complexity.md; attack-patterns/res-complexity-benign-redos.md; fix-patterns/res-complexity-bound.md | |
| UVS-RES-INITIALIZATION-FAILURE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-INITIALIZATION-FAILURE.md; vuln-patterns/res-initialization-failure.md; fix-patterns/res-initialize-before-use.md | exploit_model:初始化失败通常导致崩溃而非可利用攻击 |
| UVS-RES-INSUFFICIENT-POOL | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-INSUFFICIENT-POOL.md; vuln-patterns/res-insufficient-pool.md; fix-patterns/res-pool-sizing-timeout.md | exploit_model:池不足通过并发请求间接触发 |
| UVS-RES-INTERACTION-FREQUENCY-UNCONTROLLED | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-INTERACTION-FREQUENCY-UNCONTROLLED.md; vuln-patterns/res-interaction-frequency.md; attack-patterns/res-frequency-benign-burst.md; fix-patterns/res-add-rate-limiting.md | |
| UVS-RES-LIFETIME-FAILURE | complete | complete | complete | complete | partial | partial | partial | not_started | industry-catalog/semantics/UVS-RES-LIFETIME-FAILURE.md; vuln-patterns/res-lifetime-failure.md | exploit_model/remediable引用子UVS条目（支柱级无独立攻击/修复模式） |
| UVS-RES-MULTIPLE-OPERATION | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-MULTIPLE-OPERATION.md; vuln-patterns/res-multiple-operation.md; fix-patterns/res-operation-idempotency.md | exploit_model:重复操作通过重试/并发间接触发 |
| UVS-RES-REFERENCE-COUNT-ERROR | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-REFERENCE-COUNT-ERROR.md; vuln-patterns/res-reference-count-error.md; fix-patterns/res-refcount-pairing.md | exploit_model:引用计数错误通过间接触发UAF/泄漏 |
| UVS-RES-UNCONTROLLED-CONSUMPTION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-UNCONTROLLED-CONSUMPTION.md; vuln-patterns/res-uncontrolled-consumption.md; attack-patterns/res-consumption-benign-probe.md; fix-patterns/res-add-consumption-limits.md | |
| UVS-RES-UNCONTROLLED-RECURSION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-UNCONTROLLED-RECURSION.md; vuln-patterns/res-uncontrolled-recursion.md; attack-patterns/res-recursion-benign-depth.md; fix-patterns/res-recursion-depth-limit.md | |
| UVS-RES-USE-AFTER-RELEASE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-RES-USE-AFTER-RELEASE.md; vuln-patterns/res-use-after-release.md; attack-patterns/res-uaf-benign-dangling.md; fix-patterns/res-null-after-release.md | |
| UVS-RES-WRONG-PHASE-OPERATION | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-RES-WRONG-PHASE-OPERATION.md; vuln-patterns/res-wrong-phase-operation.md; fix-patterns/res-phase-state-guard.md | exploit_model:错误阶段操作通常导致异常而非可利用攻击 |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003已创建vuln-patterns条目，含逐步发现步骤/正例/负例/排除条件） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目含验证方法/反证方法/Observable Oracle） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 6 complete + 1 partial + 8 not_applicable（6个UVS有独立攻击模式；UVS-RES-LIFETIME-FAILURE支柱级引用子UVS；8个UVS无直接可利用攻击模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 14 complete + 1 partial（UVS-RES-LIFETIME-FAILURE支柱级引用子UVS修复模式） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 15 | 0 | 0 | 0 | 0 |
| modeled | 15 | 0 | 0 | 0 | 0 |
| discoverable | 15 | 0 | 0 | 0 | 0 |
| verifiable | 15 | 0 | 0 | 0 | 0 |
| exploit_model_available | 6 | 1 | 0 | 8 | 0 |
| remediable | 14 | 1 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 15 | 0 | 0 | 0 |
| validated | 0 | 0 | 15 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

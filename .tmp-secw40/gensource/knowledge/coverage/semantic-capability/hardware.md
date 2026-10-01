# 硬件安全能力覆盖

> 分片文件：硬件安全域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（7个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-HW-DEBUG-INTERFACE-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-DEBUG-INTERFACE-FAILURE.md; vuln-patterns/hw-debug-interface-exposed.md; attack-patterns/hw-debug-interface-benign-probe.md; fix-patterns/hw-debug-interface-disable.md | |
| UVS-HW-FABRIC-SECURITY-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-FABRIC-SECURITY-FAILURE.md; vuln-patterns/hw-fabric-security-missing.md; attack-patterns/hw-fabric-security-benign-probe.md; fix-patterns/hw-fabric-security-features.md | |
| UVS-HW-FIRMWARE-UPDATE-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-FIRMWARE-UPDATE-FAILURE.md; vuln-patterns/hw-firmware-update-missing.md; attack-patterns/hw-firmware-update-benign-probe.md; fix-patterns/hw-secure-firmware-update.md | |
| UVS-HW-LOGIC-FAULT-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-LOGIC-FAULT-FAILURE.md; vuln-patterns/hw-logic-fault-fsm-missing.md; attack-patterns/hw-logic-fault-benign-probe.md; fix-patterns/hw-logic-fault-handling.md | |
| UVS-HW-MEMORY-PROTECTION-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-MEMORY-PROTECTION-FAILURE.md; vuln-patterns/hw-memory-protection-missing.md; attack-patterns/hw-memory-protection-benign-probe.md; fix-patterns/hw-memory-protection-enforcement.md | |
| UVS-HW-REVERSE-ENGINEERING-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-REVERSE-ENGINEERING-FAILURE.md; vuln-patterns/hw-reverse-engineering-unprotected.md; attack-patterns/hw-reverse-engineering-benign-probe.md; fix-patterns/hw-reverse-engineering-protection.md | |
| UVS-HW-ROOT-OF-TRUST-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-HW-ROOT-OF-TRUST-FAILURE.md; vuln-patterns/hw-root-of-trust-writable.md; attack-patterns/hw-root-of-trust-benign-probe.md; fix-patterns/hw-immutable-root-of-trust.md | |

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

# 域/隔离能力覆盖

> 分片文件：域/隔离域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（7个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-SPHERE-ALTERNATE-PATH-UNPROTECTED | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-ALTERNATE-PATH-UNPROTECTED.md; vuln-patterns/sphere-alternate-path-unprotected.md; attack-patterns/sphere-alternate-path-benign-probe.md; fix-patterns/sphere-protect-all-paths.md | |
| UVS-SPHERE-CHANNEL-ACCESSIBLE-BY-NON-ENDPOINT | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-CHANNEL-ACCESSIBLE-BY-NON-ENDPOINT.md; vuln-patterns/sphere-channel-accessible.md; attack-patterns/sphere-channel-benign-probe.md; fix-patterns/sphere-secure-channel.md | |
| UVS-SPHERE-EXTERNAL-INFLUENCE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-EXTERNAL-INFLUENCE.md; vuln-patterns/sphere-external-influence.md; attack-patterns/sphere-external-influence-benign-probe.md; fix-patterns/sphere-protect-domain-definition.md | |
| UVS-SPHERE-EXTERNAL-REFERENCE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-EXTERNAL-REFERENCE.md; vuln-patterns/sphere-external-reference.md; attack-patterns/sphere-external-reference-benign-probe.md; fix-patterns/sphere-validate-cross-domain-reference.md | |
| UVS-SPHERE-INCORRECT-TRANSFER | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-INCORRECT-TRANSFER.md; vuln-patterns/sphere-incorrect-transfer.md; attack-patterns/sphere-incorrect-transfer-benign-probe.md; fix-patterns/sphere-secure-cross-domain-transfer.md | |
| UVS-SPHERE-ISOLATION-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-ISOLATION-FAILURE.md; vuln-patterns/sphere-isolation-failure.md; attack-patterns/sphere-isolation-benign-cross.md; fix-patterns/sphere-enforce-isolation.md | |
| UVS-SPHERE-WRONG-EXPOSURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-SPHERE-WRONG-EXPOSURE.md; vuln-patterns/sphere-wrong-exposure.md; attack-patterns/sphere-wrong-exposure-benign-probe.md; fix-patterns/sphere-restrict-exposure-scope.md | |

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

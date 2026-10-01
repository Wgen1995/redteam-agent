# UI能力覆盖

> 分片文件：UI域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（3个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-UI-INSUFFICIENT-WARNING | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-UI-INSUFFICIENT-WARNING.md; vuln-patterns/ui-insufficient-warning.md; attack-patterns/ui-insufficient-warning-benign-probe.md; fix-patterns/ui-dangerous-operation-warning.md | |
| UVS-UI-MISREPRESENTATION | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-UI-MISREPRESENTATION.md; vuln-patterns/ui-misrepresentation.md; attack-patterns/ui-misrepresentation-benign-probe.md; fix-patterns/ui-display-actual-consistency.md | |
| UVS-UI-SECURITY-DISCREPANCY | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-UI-SECURITY-DISCREPANCY.md; vuln-patterns/ui-security-discrepancy.md; attack-patterns/ui-security-discrepancy-benign-probe.md; fix-patterns/ui-security-state-consistency.md | |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 3 | 0 | 0 | 0 | 0 |
| modeled | 3 | 0 | 0 | 0 | 0 |
| discoverable | 3 | 0 | 0 | 0 | 0 |
| verifiable | 3 | 0 | 0 | 0 | 0 |
| exploit_model_available | 3 | 0 | 0 | 0 | 0 |
| remediable | 3 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 3 | 0 | 0 | 0 |
| validated | 0 | 0 | 3 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

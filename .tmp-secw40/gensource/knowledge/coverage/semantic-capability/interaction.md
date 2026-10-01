# 交互能力覆盖

> 分片文件：交互域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（3个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-INTER-CONFUSED-DEPUTY | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INTER-CONFUSED-DEPUTY.md; vuln-patterns/inter-confused-deputy.md; attack-patterns/inter-confused-deputy-benign-probe.md; fix-patterns/inter-deputy-permission-verification.md | |
| UVS-INTER-INTERPRETATION-CONFLICT | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INTER-INTERPRETATION-CONFLICT.md; vuln-patterns/inter-interpretation-conflict.md; attack-patterns/inter-interpretation-conflict-benign-probe.md; fix-patterns/inter-canonicalize-shared-interpretation.md | |
| UVS-INTER-SPEC-VIOLATION-BY-CALLER | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INTER-SPEC-VIOLATION-BY-CALLER.md; vuln-patterns/inter-spec-violation-by-caller.md; attack-patterns/inter-spec-violation-benign-probe.md; fix-patterns/inter-precondition-checking.md | |

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

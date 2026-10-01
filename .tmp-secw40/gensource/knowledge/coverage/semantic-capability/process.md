# 进程能力覆盖

> 分片文件：进程域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（1个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-PROCESS-CONTROL-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-PROCESS-CONTROL-FAILURE.md; vuln-patterns/process-control-failure.md; attack-patterns/process-control-benign-probe.md; fix-patterns/process-sandbox-permission.md | |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 1 | 0 | 0 | 0 | 0 |
| modeled | 1 | 0 | 0 | 0 | 0 |
| discoverable | 1 | 0 | 0 | 0 | 0 |
| verifiable | 1 | 0 | 0 | 0 | 0 |
| exploit_model_available | 1 | 0 | 0 | 0 | 0 |
| remediable | 1 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 1 | 0 | 0 | 0 |
| validated | 0 | 0 | 1 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

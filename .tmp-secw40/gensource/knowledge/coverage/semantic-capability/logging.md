# 日志能力覆盖

> 分片文件：日志域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（1个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-LOGGING-INSUFFICIENT | complete | complete | 信号级（不进实例清单） | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-LOGGING-INSUFFICIENT.md; vuln-patterns/logging-insufficient.md; fix-patterns/logging-security-event-logging.md | 无独立活攻击面——防御监控缺口非可主动利用漏洞 |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 1 | 0 | 0 | 0 | 0 |
| modeled | 1 | 0 | 0 | 0 | 0 |
| discoverable | 0 | 0 | 0 | 0 | 0 |
| verifiable | 1 | 0 | 0 | 0 | 0 |
| exploit_model_available | 0 | 0 | 0 | 1 | 0 |
| remediable | 1 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 1 | 0 | 0 | 0 |
| validated | 0 | 0 | 1 | 0 | 0 |
> 注：UVS-LOGGING-INSUFFICIENT 为信号级类（SINK-LOGGING-INSUFF，命中仅作浅扫过滤，不逐条进 sink_inventory），discoverable 标"信号级（不进实例清单）"而非 complete。

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

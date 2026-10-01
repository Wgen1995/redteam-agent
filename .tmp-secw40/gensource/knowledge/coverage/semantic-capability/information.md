# 信息泄露能力覆盖

> 分片文件：information域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（7个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-INFO-COVERT-CHANNEL | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-COVERT-CHANNEL.md; vuln-patterns/info-covert-channel.md; attack-patterns/info-covert-benign-timing.md; fix-patterns/info-covert-channel-control.md | |
| UVS-INFO-INSECURE-STORAGE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-INSECURE-STORAGE.md; vuln-patterns/info-insecure-storage.md; fix-patterns/info-encrypted-storage.md | exploit_model:明文存储通过介质访问间接触发 |
| UVS-INFO-LOSS-OR-OMISSION | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-LOSS-OR-OMISSION.md; vuln-patterns/info-loss-or-omission.md; fix-patterns/info-integrity-protection.md | exploit_model:信息丢失通过构造超长输入间接触发 |
| UVS-INFO-OBSERVABLE-DISCREPANCY | complete | complete | 信号级（不进实例清单） | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-OBSERVABLE-DISCREPANCY.md; vuln-patterns/info-observable-discrepancy.md; attack-patterns/info-observable-benign-enumeration.md; fix-patterns/info-behavior-normalization.md | |
| UVS-INFO-REMOVAL-FAILURE | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-REMOVAL-FAILURE.md; vuln-patterns/info-removal-failure.md; fix-patterns/info-secure-data-removal.md | exploit_model:残留数据通过内存转储间接触发 |
| UVS-INFO-RESOURCE-LEAK | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-RESOURCE-LEAK.md; vuln-patterns/info-resource-leak.md; fix-patterns/info-cross-domain-filtering.md | exploit_model:跨域泄漏通过正常请求间接触发 |
| UVS-INFO-SENSITIVE-EXPOSURE | complete | complete | 信号级（不进实例清单） | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-INFO-SENSITIVE-EXPOSURE.md; vuln-patterns/info-sensitive-exposure.md; attack-patterns/info-exposure-benign-probe.md; fix-patterns/info-field-level-filtering.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 5 complete + 2 信号级（不进实例清单）（SENSITIVE-EXPOSE/OBSERVABLE-DIFF 命中仅作浅扫过滤，不逐条进 sink_inventory） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目含验证方法/反证方法/Observable Oracle） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 3 complete + 4 not_applicable（敏感信息暴露/可观察差异/隐蔽信道有独立攻击模式；4个UVS无直接可利用攻击模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（7个UVS均有对应fix-patterns条目） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 7 | 0 | 0 | 0 | 0 |
| modeled | 7 | 0 | 0 | 0 | 0 |
| discoverable | 5 | 0 | 0 | 0 | 0 |
| verifiable | 7 | 0 | 0 | 0 | 0 |
| exploit_model_available | 3 | 0 | 0 | 4 | 0 |
| remediable | 7 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 7 | 0 | 0 | 0 |
| validated | 0 | 0 | 7 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

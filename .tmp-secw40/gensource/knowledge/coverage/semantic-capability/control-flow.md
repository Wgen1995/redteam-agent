# 控制流能力覆盖

> 分片文件：control-flow域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（7个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-CFLOW-FUNCTION-CALL-ERROR | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-FUNCTION-CALL-ERROR.md; vuln-patterns/cflow-function-call-error.md; fix-patterns/cflow-correct-function-call.md | exploit_model:参数错误导致安全行为不正确而非可利用攻击 |
| UVS-CFLOW-INCORRECT-BEHAVIOR-ORDER | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-INCORRECT-BEHAVIOR-ORDER.md; vuln-patterns/cflow-incorrect-behavior-order.md; fix-patterns/cflow-correct-operation-order.md | exploit_model:操作顺序错误导致安全检查无效化 |
| UVS-CFLOW-INCORRECT-IMPLEMENTATION | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-INCORRECT-IMPLEMENTATION.md; vuln-patterns/cflow-incorrect-implementation.md; fix-patterns/cflow-correct-condition.md | exploit_model:条件错误导致安全检查跳过 |
| UVS-CFLOW-INCORRECT-SCOPING | complete | complete | complete | complete | not_applicable | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-INCORRECT-SCOPING.md; vuln-patterns/cflow-incorrect-scoping.md; fix-patterns/cflow-correct-scoping.md | exploit_model:作用域错误导致状态被非预期修改 |
| UVS-CFLOW-INSUFFICIENT | complete | complete | complete | complete | partial | partial | partial | not_started | industry-catalog/semantics/UVS-CFLOW-INSUFFICIENT.md; vuln-patterns/cflow-insufficient.md | exploit_model/remediable引用子UVS条目（支柱级无独立攻击/修复模式） |
| UVS-CFLOW-OPEN-REDIRECT | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-OPEN-REDIRECT.md; vuln-patterns/cflow-open-redirect.md; attack-patterns/cflow-openredirect-benign-external.md; fix-patterns/cflow-redirect-whitelist.md | |
| UVS-CFLOW-WORKFLOW-ENFORCEMENT-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-CFLOW-WORKFLOW-ENFORCEMENT-FAILURE.md; vuln-patterns/cflow-workflow-enforcement-failure.md; attack-patterns/cflow-workflow-benign-skip.md; fix-patterns/cflow-workflow-state-machine.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（KBATCH-003已创建vuln-patterns条目，含逐步发现步骤/正例/负例/排除条件） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目含验证方法/反证方法/Observable Oracle） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 2 complete + 1 partial + 4 not_applicable（开放重定向和工作流绕过有独立攻击模式；UVS-CFLOW-INSUFFICIENT支柱级引用子UVS；4个UVS无直接可利用攻击模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 6 complete + 1 partial（UVS-CFLOW-INSUFFICIENT支柱级引用子UVS修复模式） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 7 | 0 | 0 | 0 | 0 |
| modeled | 7 | 0 | 0 | 0 | 0 |
| discoverable | 7 | 0 | 0 | 0 | 0 |
| verifiable | 7 | 0 | 0 | 0 | 0 |
| exploit_model_available | 2 | 1 | 0 | 4 | 0 |
| remediable | 6 | 1 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 7 | 0 | 0 | 0 |
| validated | 0 | 0 | 7 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

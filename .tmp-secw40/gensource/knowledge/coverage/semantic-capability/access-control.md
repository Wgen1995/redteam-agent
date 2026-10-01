# 访问控制能力覆盖

> 分片文件：access-control域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（15个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-AC-AUTHORIZATION-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-AUTHORIZATION-FAILURE.md; vuln-patterns/missing-authorization-check.md; vuln-patterns/object-level-authorization-missing.md; attack-patterns/missing-authz-dual-identity.md; attack-patterns/object-level-identity-cross.md; fix-patterns/add-authorization-decorator.md; fix-patterns/add-object-level-authorization.md | |
| UVS-AC-FAILURE | complete | complete | complete | complete | partial | partial | partial | not_started | industry-catalog/semantics/UVS-AC-FAILURE.md; vuln-patterns/general-access-control-failure.md | exploit_model/remediable引用子UVS条目（支柱级无独立攻击/修复模式） |
| UVS-AC-OWNERSHIP-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-OWNERSHIP-FAILURE.md; vuln-patterns/unverified-ownership.md; attack-patterns/ownership-hijack-benign.md; fix-patterns/add-ownership-verification.md | |
| UVS-AC-PERMISSION-ASSIGNMENT-ERROR | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-PERMISSION-ASSIGNMENT-ERROR.md; vuln-patterns/overly-permissive-default-permissions.md; attack-patterns/permission-read-benign.md; fix-patterns/set-minimum-file-permissions.md | |
| UVS-AC-PHYSICAL-ACCESS-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-PHYSICAL-ACCESS-FAILURE.md; vuln-patterns/physical-access-control-gaps.md; attack-patterns/physical-access-benign-probe.md; fix-patterns/physical-access-controls.md | |
| UVS-AC-PRIVILEGE-MANAGEMENT-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-PRIVILEGE-MANAGEMENT-FAILURE.md; vuln-patterns/improper-privilege-dropping.md; attack-patterns/privilege-escalation-benign.md; fix-patterns/complete-privilege-dropping.md | |
| UVS-AC-USER-MANAGEMENT-ERROR | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AC-USER-MANAGEMENT-ERROR.md; vuln-patterns/session-fixation-user-confusion.md; attack-patterns/session-fixation-benign.md; fix-patterns/regenerate-session-after-auth.md | |
| UVS-AUTHN-BRUTE-FORCE-FAILURE | complete | complete | 信号级（不进实例清单） | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-BRUTE-FORCE-FAILURE.md; vuln-patterns/missing-brute-force-protection.md; attack-patterns/brute-force-rate-test.md; fix-patterns/add-rate-limiting-and-lockout.md | |
| UVS-AUTHN-CREDENTIAL-PROTECTION-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-CREDENTIAL-PROTECTION-FAILURE.md; vuln-patterns/plaintext-credential-storage.md; attack-patterns/credential-exposure-benign.md; fix-patterns/secure-credential-storage-handling.md | |
| UVS-AUTHN-FAILURE | complete | complete | 信号级（不进实例清单） | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-FAILURE.md; vuln-patterns/authentication-bypass.md; attack-patterns/auth-bypass-benign.md; fix-patterns/complete-authentication-verification.md | |
| UVS-AUTHN-HASH-AS-CREDENTIAL | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-HASH-AS-CREDENTIAL.md; vuln-patterns/pass-the-hash-credential-confusion.md; attack-patterns/pass-the-hash-benign.md; fix-patterns/reject-hash-as-credential.md | |
| UVS-AUTHN-INSECURE-ID-MECHANISM | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-INSECURE-ID-MECHANISM.md; vuln-patterns/predictable-session-identifier.md; attack-patterns/session-prediction-benign.md; fix-patterns/use-csprng-for-identifiers.md | |
| UVS-AUTHN-LOCKOUT-IMPROPER | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-LOCKOUT-IMPROPER.md; vuln-patterns/overly-strict-account-lockout.md; attack-patterns/lockout-dos-benign.md; fix-patterns/balanced-lockout-policy.md | |
| UVS-AUTHN-SESSION-LIFECYCLE-FAILURE | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-SESSION-LIFECYCLE-FAILURE.md; vuln-patterns/insufficient-session-expiration.md; attack-patterns/stale-session-benign.md; fix-patterns/proper-session-lifecycle-management.md | |
| UVS-AUTHN-WEAK-CREDENTIALS | complete | complete | complete | complete | complete | complete | partial | not_started | industry-catalog/semantics/UVS-AUTHN-WEAK-CREDENTIALS.md; vuln-patterns/weak-credential-policy.md; attack-patterns/weak-credential-benign.md; fix-patterns/enforce-strong-credential-policy.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 13 complete + 2 信号级（不进实例清单）（AUTHN-BYPASS/BRUTE-FORCE 命中仅作浅扫过滤，不逐条进 sink_inventory） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目含验证方法/反证方法/Observable Oracle） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 14 complete + 1 partial（UVS-AC-FAILURE支柱级引用子UVS攻击模式） |
| remediable | 存在标准修复模式（fix-patterns条目） | 14 complete + 1 partial（UVS-AC-FAILURE支柱级引用子UVS修复模式） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部partial（模式乘框架级生态映射约169条待创建；vuln/attack/fix-patterns内联覆盖部分框架，独立ECMAP条目待创建） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 15 | 0 | 0 | 0 | 0 |
| modeled | 15 | 0 | 0 | 0 | 0 |
| discoverable | 13 | 0 | 0 | 0 | 0 |
| verifiable | 15 | 0 | 0 | 0 | 0 |
| exploit_model_available | 14 | 1 | 0 | 0 | 0 |
| remediable | 14 | 1 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 15 | 0 | 0 | 0 |
| validated | 0 | 0 | 15 | 0 | 0 |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

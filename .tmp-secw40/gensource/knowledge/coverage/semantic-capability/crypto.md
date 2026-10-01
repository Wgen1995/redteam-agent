# 密码学能力覆盖

> 分片文件：crypto域UVS的八维能力覆盖状态。
> **禁止由名称映射自动推导检测能力。cataloged不等于discoverable。**

## 八维能力状态矩阵（9个UVS）

| semantic_id | cataloged | modeled | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped | validated | evidence_refs | not_applicable_reason |
|---|---|---|---|---|---|---|---|---|---|---|
| UVS-CRYPTO-MISSING-ENCRYPTION | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-MISSING-ENCRYPTION.md; vuln-patterns/missing-encryption-cleartext.md; attack-patterns/cleartext-capture-benign.md; fix-patterns/enforce-encryption-tls-atrest.md | |
| UVS-CRYPTO-WEAK-STRENGTH | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-WEAK-STRENGTH.md; vuln-patterns/weak-crypto-strength-params.md; attack-patterns/weak-key-cost-benign.md; fix-patterns/use-adequate-crypto-strength.md | |
| UVS-CRYPTO-WEAK-ALGORITHM | complete | complete | complete | complete | complete | complete | not_started | complete | industry-catalog/semantics/UVS-CRYPTO-WEAK-ALGORITHM.md; vuln-patterns/weak-unsalted-password-hash.md; attack-patterns/weak-hash-offline-cost.md; fix-patterns/salted-strong-password-hash.md | |
| UVS-CRYPTO-INSUFFICIENT-RANDOMNESS | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-INSUFFICIENT-RANDOMNESS.md; vuln-patterns/insufficient-randomness-noncsprng.md; attack-patterns/weak-rng-prediction-benign.md; fix-patterns/use-csprng-for-security-values.md | |
| UVS-CRYPTO-PREDICTABLE-IDENTIFIER | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-PREDICTABLE-IDENTIFIER.md; vuln-patterns/predictable-identifier-generation.md; attack-patterns/session-prediction-benign.md(复用AUTHN域); fix-patterns/use-csprng-for-identifiers.md(复用AUTHN域) | |
| UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE.md; vuln-patterns/missing-authenticity-verification.md; attack-patterns/forged-data-benign-marker.md; fix-patterns/verify-data-authenticity-signature.md | |
| UVS-CRYPTO-ORIGIN-VALIDATION-FAILURE [superseded by UVS-AC-AUTHORIZATION-FAILURE 2026-08-13] | complete | complete | complete | complete | complete | complete | not_applicable（已归并访问控制域） | not_started | industry-catalog/semantics/UVS-CRYPTO-ORIGIN-VALIDATION-FAILURE.md; vuln-patterns/missing-origin-validation.md; attack-patterns/csrf-benign-marker.md; fix-patterns/enforce-origin-validation-csrf.md | 双映射裁决：归属访问控制域，见 ADJ-SRC-CWE-352.md |
| UVS-CRYPTO-KEY-LIFECYCLE-FAILURE | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-KEY-LIFECYCLE-FAILURE.md; vuln-patterns/key-lifecycle-nonce-reuse.md; attack-patterns/nonce-reuse-benign.md; fix-patterns/proper-key-lifecycle-rotation.md | |
| UVS-CRYPTO-MISSING-STEP | complete | complete | complete | complete | complete | complete | not_started | not_started | industry-catalog/semantics/UVS-CRYPTO-MISSING-STEP.md; vuln-patterns/missing-crypto-step-mac.md; attack-patterns/tamper-ciphertext-benign.md; fix-patterns/complete-crypto-steps-aead.md | |

## 维度说明

| 维度 | 达到complete的要求 | 当前域状态 |
|---|---|---|
| cataloged | UVS已建立且来源对账完成 | 全部complete（任务6已完成） |
| modeled | 本体路径/根因/不变量/正反例齐备 | 全部complete（UVS文件含完整定义、根因、不变量、本体路径、正例、负例、排除） |
| discoverable | 存在可执行发现模式（vuln-patterns条目） | 全部complete（9个UVS均有vuln-patterns条目：WEAK-ALGORITHM为种子weak-unsalted-password-hash，其余8个为密码学域批量建设新建） |
| verifiable | 存在确认与反证方法（verification能力可消费） | 全部complete（vuln-patterns条目均含验证方法/反证方法/排除条件/非污点语义模型） |
| exploit_model_available | 存在攻击模型（attack-patterns条目） | 全部complete（WEAK-ALGORITHM为种子weak-hash-offline-cost；PREDICTABLE-IDENTIFIER复用AUTHN域session-prediction-benign；其余7个为密码学域批量建设新建） |
| remediable | 存在标准修复模式（fix-patterns条目） | 全部complete（WEAK-ALGORITHM为种子salted-strong-password-hash；PREDICTABLE-IDENTIFIER复用AUTHN域use-csprng-for-identifiers；其余7个为密码学域批量建设新建） |
| ecosystem_mapped | 存在生态映射（ecosystem-mappings条目） | 全部not_started（专用ecosystem-mappings条目尚未创建）；但各vuln/attack/fix条目内部安全API表已覆盖Python(cryptography/hashlib/secrets)、Java(JCA)、Node(crypto)、Go(crypto)四生态 |
| validated | 有实证证据（实测案例/外部验证） | WEAK-ALGORITHM=complete（dvpwa靶场Observed证据）；其余8个=not_started（引用分级为Proposed/Inferred，尚未实测） |

## 状态汇总

| 维度 | complete | partial | not_started | not_applicable | blocked |
|---|---:|---:|---:|---:|---:|
| cataloged | 9 | 0 | 0 | 0 | 0 |
| modeled | 9 | 0 | 0 | 0 | 0 |
| discoverable | 9 | 0 | 0 | 0 | 0 |
| verifiable | 9 | 0 | 0 | 0 | 0 |
| exploit_model_available | 9 | 0 | 0 | 0 | 0 |
| remediable | 9 | 0 | 0 | 0 | 0 |
| ecosystem_mapped | 0 | 0 | 9 | 0 | 0 |
| validated | 1 | 0 | 8 | 0 | 0 |

## 密码学域非污点语义模型覆盖

各vuln-pattern条目均采用密码学非污点模型（Primitive / Parameter / Key Lifecycle / Trust Assumption）：

| UVS | Primitive | Parameter | Key Lifecycle | Trust Assumption |
|---|---|---|---|---|
| UVS-CRYPTO-MISSING-ENCRYPTION | 传输/存储加密原语是否选用 | TLS版本/密码套件/加密密钥长度 | — | 错误假设信道/存储可信 |
| UVS-CRYPTO-WEAK-STRENGTH | 算法合理但参数选错 | 密钥长度/KDF迭代/IV长度 | — | 错误假设"有加密即安全" |
| UVS-CRYPTO-WEAK-ALGORITHM | 密码哈希原语选型(MD5 vs bcrypt) | 盐/工作因子 | — | — |
| UVS-CRYPTO-INSUFFICIENT-RANDOMNESS | RNG原语(伪随机 vs CSPRNG) | 随机值长度/熵/种子来源 | — | 错误假设"任意random不可预测" |
| UVS-CRYPTO-PREDICTABLE-IDENTIFIER | 生成原语(自增/时间戳 vs CSPRNG/UUID v4) | 标识符熵/可预测性 | — | 错误假设"标识符不被猜测" |
| UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE | 真实性验证原语(签名/证书/HMAC) | 证书校验完整性(链/主机名/吊销/过期) | — | 错误假设"收到的数据即来源发出" |
| UVS-CRYPTO-ORIGIN-VALIDATION-FAILURE | 来源验证原语(CSRF token/Origin/SameSite) | token会话绑定/SameSite级别/CORS限制 | — | 错误假设"附Cookie即用户主动发起" |
| UVS-CRYPTO-KEY-LIFECYCLE-FAILURE | 加密模式对nonce重用敏感性 | — | nonce一次性/密钥轮换撤销/密钥来源(KMS vs硬编码) | 错误假设"密钥不变即可" |
| UVS-CRYPTO-MISSING-STEP | 加密原语是否提供机密性+认证(AEAD vs仅encrypt) | MAC覆盖范围与顺序(encrypt-then-MAC) | — | 错误假设"加密即足够"/"协商结果可信" |

## 消费方

- `scope-and-context`：引用覆盖状态披露知识缺口
- `candidate-discovery`：引用discoverable状态
- `verification-and-rating`：引用verifiable状态
- `remediation-guidance`：引用remediable状态
- `report-delivery`：引用覆盖矩阵披露检测能力边界

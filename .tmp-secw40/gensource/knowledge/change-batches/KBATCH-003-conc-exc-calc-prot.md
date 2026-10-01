# KBATCH-003：并发/异常/计算/保护域知识建设

> 变更批次文件，记录KBATCH-003的详细变更内容。

## 批次概述

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-003 |
| 日期 | 2026-08-09 |
| 描述 | 为并发域（CONC-*）、异常域（EXC-*）、计算域（CALC-*）和保护域（PROT-*）的16个UVS建设可执行知识——创建vuln-patterns、attack-patterns（适用时）和fix-patterns（适用时） |

## 变更清单

### 新建 vuln-patterns（16条）

| 条目ID | 文件 | 关联UVS |
|---|---|---|
| VULN-CONC-RACE-01 | `conc-race-condition-toctou.md` | UVS-CONC-RACE-CONDITION |
| VULN-CONC-LOCKING-01 | `conc-improper-locking.md` | UVS-CONC-IMPROPER-LOCKING |
| VULN-EXC-UNCHECKED-01 | `exc-unchecked-return-value.md` | UVS-EXC-IMPROPER-CHECK |
| VULN-EXC-SWALLOWED-01 | `exc-swallowed-exception.md` | UVS-EXC-IMPROPER-HANDLING |
| VULN-EXC-FAILOPEN-01 | `exc-fail-open-on-error.md` | UVS-EXC-INSECURE-FAILURE |
| VULN-EXC-GENERIC-01 | `exc-generic-handling-failure.md` | UVS-EXC-FAILURE |
| VULN-CALC-INTOVERFLOW-01 | `calc-integer-overflow.md` | UVS-CALC-FAILURE |
| VULN-CALC-COMPARE-01 | `calc-comparison-error.md` | UVS-CALC-COMPARISON-FAILURE |
| VULN-CALC-INCOMPLETE-01 | `calc-incomplete-comparison.md` | UVS-CALC-INCOMPLETE-COMPARISON |
| VULN-CALC-LENGTH-01 | `calc-length-parameter-mismatch.md` | UVS-CALC-LENGTH-PARAMETER |
| VULN-PROT-BYPASS-01 | `prot-protection-bypass.md` | UVS-PROT-FAILURE |
| VULN-PROT-CLIENTSIDE-01 | `prot-client-side-enforcement.md` | UVS-PROT-CLIENT-SIDE-ENFORCEMENT |
| VULN-PROT-OBSCURITY-01 | `prot-obscurity-reliance.md` | UVS-PROT-OBSCURITY-RELIANCE |
| VULN-PROT-SINGLEFACTOR-01 | `prot-single-factor-reliance.md` | UVS-PROT-SINGLE-FACTOR-RELIANCE |
| VULN-PROT-GUESSABLE-01 | `prot-guessable-challenge.md` | UVS-PROT-GUESSABLE-CHALLENGE |
| VULN-PROT-ADMINCTRL-01 | `prot-admin-control-missing.md` | UVS-PROT-ADMIN-CONTROL-FAILURE |

### 新建 attack-patterns（13条）

| 条目ID | 文件 | 关联VULN |
|---|---|---|
| ATK-CONC-RACE-01 | `conc-race-toctou-benign.md` | VULN-CONC-RACE-01 |
| ATK-CONC-LOCKING-01 | `conc-locking-deadlock-benign.md` | VULN-CONC-LOCKING-01 |
| ATK-EXC-UNCHECKED-01 | `exc-unchecked-error-path-benign.md` | VULN-EXC-UNCHECKED-01 |
| ATK-EXC-SWALLOWED-01 | `exc-swallowed-exception-benign.md` | VULN-EXC-SWALLOWED-01 |
| ATK-EXC-FAILOPEN-01 | `exc-failopen-benign.md` | VULN-EXC-FAILOPEN-01 |
| ATK-CALC-INTOVERFLOW-01 | `calc-integer-overflow-benign.md` | VULN-CALC-INTOVERFLOW-01 |
| ATK-CALC-COMPARE-01 | `calc-comparison-bypass-benign.md` | VULN-CALC-COMPARE-01 |
| ATK-CALC-INCOMPLETE-01 | `calc-incomplete-comparison-benign.md` | VULN-CALC-INCOMPLETE-01 |
| ATK-CALC-LENGTH-01 | `calc-length-mismatch-benign.md` | VULN-CALC-LENGTH-01 |
| ATK-PROT-CLIENTSIDE-01 | `prot-clientside-bypass-benign.md` | VULN-PROT-CLIENTSIDE-01 |
| ATK-PROT-OBSCURITY-01 | `prot-obscurity-discover-benign.md` | VULN-PROT-OBSCURITY-01 |
| ATK-PROT-SINGLEFACTOR-01 | `prot-singlefactor-bypass-benign.md` | VULN-PROT-SINGLEFACTOR-01 |
| ATK-PROT-GUESSABLE-01 | `prot-guessable-captcha-benign.md` | VULN-PROT-GUESSABLE-01 |

### 新建 fix-patterns（14条）

| 条目ID | 文件 | 关联VULN |
|---|---|---|
| FIX-CONC-RACE-01 | `conc-race-atomic-synchronization.md` | VULN-CONC-RACE-01 |
| FIX-CONC-LOCKING-01 | `conc-locking-proper-release.md` | VULN-CONC-LOCKING-01 |
| FIX-EXC-UNCHECKED-01 | `exc-unchecked-check-return-value.md` | VULN-EXC-UNCHECKED-01 |
| FIX-EXC-SWALLOWED-01 | `exc-swallowed-proper-handling.md` | VULN-EXC-SWALLOWED-01 |
| FIX-EXC-FAILOPEN-01 | `exc-failopen-fail-closed.md` | VULN-EXC-FAILOPEN-01 |
| FIX-CALC-INTOVERFLOW-01 | `calc-integer-overflow-check.md` | VULN-CALC-INTOVERFLOW-01 |
| FIX-CALC-COMPARE-01 | `calc-comparison-correct-equals.md` | VULN-CALC-COMPARE-01 |
| FIX-CALC-INCOMPLETE-01 | `calc-incomplete-full-comparison.md` | VULN-CALC-INCOMPLETE-01 |
| FIX-CALC-LENGTH-01 | `calc-length-validation.md` | VULN-CALC-LENGTH-01 |
| FIX-PROT-CLIENTSIDE-01 | `prot-clientside-server-side-validation.md` | VULN-PROT-CLIENTSIDE-01 |
| FIX-PROT-OBSCURITY-01 | `prot-obscurity-independent-controls.md` | VULN-PROT-OBSCURITY-01 |
| FIX-PROT-SINGLEFACTOR-01 | `prot-singlefactor-add-mfa.md` | VULN-PROT-SINGLEFACTOR-01 |
| FIX-PROT-GUESSABLE-01 | `prot-guessable-strong-captcha.md` | VULN-PROT-GUESSABLE-01 |
| FIX-PROT-ADMINCTRL-01 | `prot-adminctrl-configurable-security.md` | VULN-PROT-ADMINCTRL-01 |

### 未创建attack-pattern的UVS（3个）

| UVS | 原因 |
|---|---|
| UVS-EXC-FAILURE | 抽象根模式——使用具体子模式的attack-pattern |
| UVS-PROT-FAILURE | 抽象根模式——使用具体子模式的attack-pattern |
| UVS-PROT-ADMIN-CONTROL-FAILURE | 无独立活攻击面——治理性质信号 |

### 未创建fix-pattern的UVS（2个）

| UVS | 原因 |
|---|---|
| UVS-EXC-FAILURE | 抽象根模式——使用具体子模式的fix-pattern |
| UVS-PROT-FAILURE | 抽象根模式——使用具体子模式的fix-pattern |

### 更新覆盖矩阵（4个）

| 文件 | 更新内容 |
|---|---|
| `coverage/semantic-capability/concurrency.md` | 2个UVS的discoverable/verifiable/exploit_model/remediable从not_started更新为complete |
| `coverage/semantic-capability/exception.md` | 3个UVS更新为complete，1个抽象根模式的exploit_model/remediable标注not_applicable |
| `coverage/semantic-capability/calc.md` | 4个UVS的discoverable/verifiable/exploit_model/remediable从not_started更新为complete |
| `coverage/semantic-capability/protection.md` | 4个UVS更新为complete，2个抽象根/无攻击面的exploit_model标注not_applicable，1个抽象根的remediable标注not_applicable |

### 更新索引（3个）

| 文件 | 更新内容 |
|---|---|
| `vuln-patterns/_index.md` | 新增16条索引行，更新条目总数描述 |
| `attack-patterns/_index.md` | 新增13条索引行，更新条目总数描述 |
| `fix-patterns/_index.md` | 新增14条索引行，更新条目总数描述 |

## 质量验证

| 验证项 | 结果 |
|---|---|
| 每个vuln-pattern含逐步可执行发现步骤 | 通过 |
| 每个vuln-pattern含正例 | 通过 |
| 每个vuln-pattern含负例 | 通过 |
| 每个vuln-pattern含排除条件 | 通过 |
| 未复制CWE摘要 | 通过——所有条目基于UVS语义和行业知识原创编写 |
| 覆盖矩阵八维状态更新 | 通过 |
| 索引交叉引用更新 | 通过 |

## 成熟度标注

- 所有vuln-pattern：Proposed（基于行业标准转译，尚未在具体靶场实测验证）
- 所有attack-pattern：Proposed（基于行业标准转译）
- 所有fix-pattern：Inferred（从行业最佳实践转译）

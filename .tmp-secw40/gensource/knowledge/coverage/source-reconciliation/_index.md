# 来源对账索引（coverage/source-reconciliation/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务5。本文件是来源对账索引。

## 用途

来源对账记录追踪每个来源账本的原始条目是否全部完成对账。每个来源一个对账记录（COV-SRC-*.md），记录对账摘要、原始条目ID集合核对和差额。

**对账纪律**：实际ID集合与manifest记录的分母逐项核对，差额必须为0。每个原始条目恰好进入`mapped`或`pending_adjudication`之一。

**mapped 列当前全为 0 的如实说明**：下表所有来源的 `mapped数` 均为 0——来源条目目前全部处于 `pending_adjudication`（尚未逐条映射到 UVS/ADJ），而非“无内容”或“映射失败”。待逐条裁决完成后 mapped 与 pending 的数值将相应转移，差额恒为 0。

## 当前索引

| stable_id | 来源账本 | manifest原始条目数 | 实际记录数 | 差额 | mapped数 | pending数 |
|---|---|---|---|---|---|---|
| COV-SRC-CWE | SRC-CWE | 1450 | 1450 | 0 | 0 | 1450 |
| COV-SRC-CAPEC | SRC-CAPEC | 706 | 706 | 0 | 0 | 706 |
| COV-SRC-OWASP-WEB | SRC-OWASP-WEB | 10 | 10 | 0 | 0 | 10 |
| COV-SRC-OWASP-API | SRC-OWASP-API | 10 | 10 | 0 | 0 | 10 |
| COV-SRC-OWASP-MOBILE | SRC-OWASP-MOBILE | 18 | 18 | 0 | 0 | 18 |
| COV-SRC-OWASP-LLM | SRC-OWASP-LLM | 10 | 10 | 0 | 0 | 10 |
| COV-SRC-OWASP-AGENT | SRC-OWASP-AGENT | 待人工核实 | 11 | 0 | 0 | 11 |
| COV-SRC-OWASP-SCWE | SRC-OWASP-SCWE | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-CERT-C | SRC-CERT-C | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-CERT-CPP | SRC-CERT-CPP | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-CERT-JAVA | SRC-CERT-JAVA | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-RUST-UNSAFE | SRC-RUST-UNSAFE | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-ANDROID-SECURITY | SRC-ANDROID-SECURITY | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-APPLE-SECURE-CODING | SRC-APPLE-SECURE-CODING | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-ELECTRON-SECURITY | SRC-ELECTRON-SECURITY | 20 | 20 | 0 | 0 | 20 |
| COV-SRC-OWASP-K8S | SRC-OWASP-K8S | 10 | 10 | 0 | 0 | 10 |
| COV-SRC-K8S-SECURITY | SRC-K8S-SECURITY | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-OWASP-IAC | SRC-OWASP-IAC | 10 | 10 | 0 | 0 | 10 |
| COV-SRC-SLSA | SRC-SLSA | 待人工核实 | 5 | 0 | 0 | 5 |
| COV-SRC-OPENSSF-SCORECARD | SRC-OPENSSF-SCORECARD | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-OPENSSF-BASELINE | SRC-OPENSSF-BASELINE | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-RFC3552 | SRC-RFC3552 | 全文12章+附录 | 13 | 0 | 0 | 13 |
| COV-SRC-HTTP-RFC9110 | SRC-HTTP-RFC9110 | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-GRPC-SECURITY | SRC-GRPC-SECURITY | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-KAFKA-SECURITY | SRC-KAFKA-SECURITY | 待人工核实 | 1 | 0 | 0 | 1 |
| COV-SRC-MITRE-ATLAS | SRC-MITRE-ATLAS | 待人工核实 | 6 | 0 | 0 | 6 |
| COV-SRC-CVE-WINDOW | SRC-CVE-WINDOW | 不逐条枚举 | 1 | 0 | 0 | 1 |
| COV-SRC-GHSA-WINDOW | SRC-GHSA-WINDOW | 不逐条枚举 | 1 | 0 | 0 | 1 |

### 待人工核实来源汇总

以下来源的条目级清单需后续人工核实补充：

| 来源 | 待核实原因 |
|---|---|
| SRC-OWASP-AGENT | Top 10 for Agentic Applications 2026条目名称待提取；Threats and Mitigations文档条目数待核实 |
| SRC-OWASP-SCWE | 官方页面404，需从scs.owasp.org/SCWE/或GitHub仓库提取SCWE ID列表 |
| SRC-CERT-C | 需遍历SEI CERT C wiki各章节提取规则列表 |
| SRC-CERT-CPP | 需遍历SEI CERT C++ wiki各章节提取规则列表 |
| SRC-CERT-JAVA | 需遍历SEI CERT Java wiki各章节提取规则列表 |
| SRC-RUST-UNSAFE | 需遍历Rust Reference unsafe章节和Rustonomicon全文提取条目 |
| SRC-ANDROID-SECURITY | 需遍历Android Developers Security页面及子页面提取条目 |
| SRC-APPLE-SECURE-CODING | 需遍历Apple Secure Coding Guide归档文档目录提取条目 |
| SRC-K8S-SECURITY | 需遍历kubernetes.io/docs/concepts/security页面提取条目 |
| SRC-SLSA | Build Track各级别requirements条目级计数需遍历spec页面 |
| SRC-OPENSSF-SCORECARD | 需从ossf/scorecard GitHub仓库checks.yaml提取check列表 |
| SRC-OPENSSF-BASELINE | 需遍历baseline.openssf.org YAML文件统计控制项 |
| SRC-HTTP-RFC9110 | 需遍历RFC 9110 Section 17提取安全考虑条目 |
| SRC-GRPC-SECURITY | 需遍历grpc.io/docs/guides/security页面提取条目 |
| SRC-KAFKA-SECURITY | 需遍历kafka.apache.org/documentation/#security章节提取条目 |
| SRC-MITRE-ATLAS | 需解析atlas-data v2026.06 YAML文件统计各类条目 |

## 模板

编写对账记录时参考 [\_templates/source-reconciliation-template.md](../../_templates/source-reconciliation-template.md)。

## 消费方

- `coverage/_index.md`：覆盖矩阵入口引用对账状态
- `report-delivery`：报告交付能力引用对账状态披露来源覆盖完整性

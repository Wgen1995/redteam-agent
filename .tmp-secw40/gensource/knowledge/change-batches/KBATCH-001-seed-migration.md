# KBATCH-001：种子知识迁移

> 本批次记录GenSource种子知识从旧格式迁移到新模板、创建初始攻击模式和修复缺口补齐的完整变更。

## 批次元数据

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-001 |
| date | 2026-08-09 |
| scope | 四类内容模板建立、6条漏洞模式迁移、4条修复模式迁移、2条修复模式新建、4条攻击模式新建、三库接线到Skills |
| source_versions | dvpwa实测验证（2026-08-08）；DVWA跨语言泛化测试（2026-08-08）；145个UVS；798个ADJ；安全本体 |

## 变更文件清单

### Created files

| 文件路径 | 说明 |
|---|---|
| `vuln-patterns/_template.md` | 漏洞模式模板（28章节） |
| `attack-patterns/_template.md` | 攻击模式模板（22章节） |
| `fix-patterns/_template.md` | 修复模式模板（21章节） |
| `ecosystem-mappings/_template.md` | 生态映射模板（21章节） |
| `coverage/batch-ledger.md` | 知识建设批次台账 |
| `coverage/skill-consumption.md` | Skill消费索引 |
| `fix-patterns/raw-output-escaping.md` | 新建：原生输出转义修复（Inferred） |
| `fix-patterns/dead-control-assembly.md` | 新建：死安全控制装配修复（Inferred） |
| `attack-patterns/sql-injection-benign-marker.md` | 新建：SQL注入良性差分查询证明（Observed） |
| `attack-patterns/xss-benign-dom-marker.md` | 新建：XSS无害标记DOM证明（Observed） |
| `attack-patterns/weak-hash-offline-cost.md` | 新建：弱哈希离线成本证明（Observed） |
| `attack-patterns/missing-authz-dual-identity.md` | 新建：缺失授权双身份对照证明（Observed） |

### Modified files

| 文件路径 | 说明 |
|---|---|
| `vuln-patterns/_index.md` | 新增关联UVS列和攻击模式引用列；更新索引表 |
| `attack-patterns/_index.md` | 更新状态声明；填充首批4条索引表；添加模板引用 |
| `fix-patterns/_index.md` | 新增模板引用；扩展内部结构说明；索引表新增2条 |
| `ecosystem-mappings/_index.md` | 更新模板引用 |
| `coverage/_index.md` | 新增batch-ledger和skill-consumption到目录结构 |
| `vuln-patterns/sql-injection-string-concat.md` | 关联UVS-INJ-QUERY-INJECTION；补齐新模板章节 |
| `vuln-patterns/template-autoescape-disabled-xss.md` | 关联UVS-INJ-XSS；补齐新模板章节 |
| `vuln-patterns/raw-output-no-escaping-xss.md` | 关联UVS-INJ-XSS；补齐新模板章节；创建对应fix-pattern |
| `vuln-patterns/weak-unsalted-password-hash.md` | 关联UVS-CRYPTO-WEAK-ALGORITHM；补齐新模板章节 |
| `vuln-patterns/missing-authorization-check.md` | 关联UVS-AC-AUTHORIZATION-FAILURE；补齐新模板章节 |
| `vuln-patterns/dead-security-control.md` | 关联UVS-PROT-ADMIN-CONTROL-FAILURE；补齐新模板章节；创建对应fix-pattern |
| `fix-patterns/sql-parameterized-query.md` | 补齐新模板章节 |
| `fix-patterns/enable-template-autoescape.md` | 补齐新模板章节 |
| `fix-patterns/salted-strong-password-hash.md` | 补齐新模板章节 |
| `fix-patterns/add-authorization-decorator.md` | 补齐新模板章节 |
| `contracts/data-structures/candidate-finding.md` | 新增ecosystem_mapping_refs、verification_knowledge_refs、attack_pattern_refs字段 |
| `contracts/field-ownership-table.md` | 新增ecosystem_mapping_refs、verification_knowledge_refs、attack_pattern_refs写权限 |
| `skills/candidate-discovery/SKILL.md` | 输出表新增ecosystem_mapping_refs |
| `skills/verification-and-rating/SKILL.md` | 输入/输出新增verification_knowledge_refs |
| `skills/exploit-proof/SKILL.md` | 输入表新增attack-patterns；输出表新增attack_pattern_refs |
| `skills/remediation-guidance/SKILL.md` | 步骤B1改为按semantic/vuln pattern/不变量/生态/版本五维匹配 |
| `skills/scope-and-context/SKILL.md` | 技术栈探测新增生态Profile消费 |
| `skills/knowledge-evolution/SKILL.md` | 候选池初筛新增四类缺口分别处理 |
| 5个UVS文件 | 三库引用从留空更新为实际条目ID |

## Coverage transitions

| 统一语义 | 维度 | 变更前状态 | 变更后状态 | 证据 |
|---|---|---|---|---|
| UVS-INJ-QUERY-INJECTION | discoverable | not_started | partial | VULN-SQLI-STRCONCAT-01已创建 |
| UVS-INJ-QUERY-INJECTION | exploit_model_available | not_started | partial | ATK-SQLI-BENIGN-01已创建 |
| UVS-INJ-QUERY-INJECTION | remediable | not_started | partial | FIX-SQLI-PARAMQUERY-01已创建 |
| UVS-INJ-XSS | discoverable | not_started | partial | VULN-XSS-AUTOESCAPE-01 + VULN-XSS-RAWOUTPUT-01 |
| UVS-INJ-XSS | exploit_model_available | not_started | partial | ATK-XSS-BENIGN-DOM-01 |
| UVS-INJ-XSS | remediable | not_started | partial | FIX-XSS-AUTOESCAPE-01 + FIX-XSS-OUTPUT-ENCODING-01 |
| UVS-CRYPTO-WEAK-ALGORITHM | discoverable | not_started | partial | VULN-CRYPTO-WEAKHASH-01 |
| UVS-CRYPTO-WEAK-ALGORITHM | exploit_model_available | not_started | partial | ATK-CRYPTO-OFFLINE-COST-01 |
| UVS-CRYPTO-WEAK-ALGORITHM | remediable | not_started | partial | FIX-CRYPTO-STRONGHASH-01 |
| UVS-AC-AUTHORIZATION-FAILURE | discoverable | not_started | partial | VULN-AUTHZ-MISSING-01 |
| UVS-AC-AUTHORIZATION-FAILURE | exploit_model_available | not_started | partial | ATK-AUTHZ-DUAL-IDENTITY-01 |
| UVS-AC-AUTHORIZATION-FAILURE | remediable | not_started | partial | FIX-AUTHZ-ADDCHECK-01 |
| UVS-PROT-ADMIN-CONTROL-FAILURE | discoverable | not_started | partial | VULN-HYGIENE-DEADCONTROL-01（Proposed） |
| UVS-PROT-ADMIN-CONTROL-FAILURE | remediable | not_started | partial | FIX-DEADCONTROL-ASSEMBLY-01 |
| UVS-PROT-ADMIN-CONTROL-FAILURE | exploit_model_available | not_started | not_applicable | 无独立活攻击面 |

## 验证结果

- 模板章节完整性：通过（4个模板均有全部必需章节）
- 迁移后无缺失章节：通过（6条漏洞模式均有正例/负例）
- 接线验证：通过（23处知识引用字段分布在contracts和skills中）

## 剩余缺口

| 缺口描述 | 影响范围 | 后续计划 |
|---|---|---|
| 生态映射条目尚未创建 | ecosystem_mapping_refs无实际条目可引用 | 待创建Python/PHP/Java等生态映射条目 |
| dead-security-control仅1次独立观察 | Proposed级别，未达#16晋升门槛 | 后续审计若再次独立观察则触发#16正式晋升评估 |
| raw-output-no-escaping-xss为Inferred | 未经完整端到端案例核实 | 后续审计中独立验证可达性后升级 |

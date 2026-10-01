# 知识建设批次台账（coverage/batch-ledger.md）

> 本文件记录每次知识建设批次的输入集合、产出和验证结果，供#16知识演进和覆盖矩阵追踪。

## 台账格式

每条批次记录包含以下字段：

| 字段 | 说明 |
|---|---|
| batch_id | 批次唯一标识（KBATCH-NNN） |
| 日期 | 批次执行日期 |
| 输入集合 | 本批次消费的输入资源（源码审计结果/行业标准/跨语言测试等） |
| 产出条目 | 本批次创建或修改的知识条目清单（按知识库分类） |
| 验证结果 | 本批次的验证状态（模板完整性/迁移完整性/接线验证） |
| 成熟度标注 | 各条目迁移后的成熟度状态 |
| 关联变更批次 | `knowledge/change-batches/` 中的变更批次文件引用 |

## 批次记录

### KBATCH-001：种子知识迁移（2026-08-09）

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-001 |
| 日期 | 2026-08-09 |
| 输入集合 | GenSource实测验证（dvpwa测试靶场，2026-08-08）；DVWA跨语言泛化测试（2026-08-08，PHP源码）；145个UVS（industry-catalog/semantics/）；798个ADJ（industry-catalog/adjudication/）；安全本体（ontology/） |
| 产出条目 | vuln-patterns: 6条迁移（补齐新模板章节+关联UVS）；fix-patterns: 4条迁移（补齐新模板章节）+ 2条新建（raw-output-escaping, dead-control-assembly）；attack-patterns: 4条新建（SQL注入/XSS/弱哈希/缺失授权）；ecosystem-mappings: 4个模板创建 |
| 验证结果 | 模板章节完整性：通过；迁移后无缺失章节：通过；接线验证：通过 |
| 成熟度标注 | dead-security-control保留Proposed；raw-output-no-escaping-xss保留Inferred；其余Observed；新建fix-pattern标注Inferred；新建attack-pattern按各条目实际验证状态标注 |
| 关联变更批次 | `knowledge/change-batches/KBATCH-001-seed-migration.md` |

### KBATCH-002：注入域可执行知识建设（2026-08-09，无独立变更批次文件）

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-002 |
| 日期 | 2026-08-09 |
| 输入集合 | 注入域（INJ）12个UVS；行业标准转译；DVPWA/DVWA 实测种子 |
| 产出条目 | vuln-patterns 10条（注入域可执行模式）；attack-patterns 9条；fix-patterns 9条；coverage 1个更新 |
| 验证结果 | 条目与 UVS 接线验证通过；变更历史并入各条目版本历史（变更批次文件内容并入条目，见 change-batches/_index.md 的登记说明） |
| 成熟度标注 | 各条目按实际验证状态标注（Observed/Proposed/Inferred） |
| 关联变更批次 | 无独立文件；引用关系登记于 `knowledge/change-batches/_index.md` |

### KBATCH-003：并发/异常/计算/保护域知识建设（2026-08-09）

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-003 |
| 日期 | 2026-08-09 |
| 输入集合 | 16个UVS（industry-catalog/semantics/：UVS-CONC-*×2、UVS-EXC-*×4、UVS-CALC-*×4、UVS-PROT-*×6）；安全本体（ontology/）；vuln-patterns/attack-patterns/fix-patterns模板 |
| 产出条目 | vuln-patterns: 16条新建（2并发+4异常+4计算+6保护）；attack-patterns: 13条新建（2并发+3异常+4计算+4保护，抽象根模式/无独立活攻击面的不创建）；fix-patterns: 14条新建（2并发+3异常+4计算+5保护，抽象根模式不创建）；覆盖矩阵: 4个更新（concurrency/exception/calc/protection）；索引: 3个更新（vuln-patterns/attack-patterns/fix-patterns _index.md） |
| 验证结果 | 模板章节完整性：通过；每个vuln-pattern含逐步可执行发现步骤/正例/负例/排除条件：通过；覆盖矩阵八维状态更新：通过；索引交叉引用更新：通过 |
| 成熟度标注 | 全部vuln-pattern/attack-pattern/fix-pattern标注Proposed/Inferred——基于行业标准转译，尚未在具体靶场实测验证 |
| 关联变更批次 | `knowledge/change-batches/KBATCH-003-conc-exc-calc-prot.md` |

### KBATCH-004：内存/文件/输入域知识建设（2026-08-09）

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-004 |
| 日期 | 2026-08-09 |
| 输入集合 | 20个UVS（内存/文件/输入域）；安全本体；行业标准转译 |
| 产出条目 | vuln-patterns 20条；attack-patterns 19条；fix-patterns 20条；覆盖矩阵 3个更新 |
| 验证结果 | 模板完整性通过；索引交叉引用通过 |
| 成熟度标注 | 全部标注 Proposed/Inferred（行业标准转译，未实测） |
| 关联变更批次 | `knowledge/change-batches/KBATCH-004-memory-file-input-domains.md` |

### KBATCH-006：其余域知识建设（2026-08-09）

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-006 |
| 日期 | 2026-08-09 |
| 输入集合 | 其余域 UVS（资源/控制流/信息等）；安全本体；行业标准转译 |
| 产出条目 | vuln-patterns 44条；attack-patterns 若干；fix-patterns 若干；覆盖矩阵更新 |
| 验证结果 | 模板完整性通过；索引交叉引用通过 |
| 成熟度标注 | 全部标注 Proposed/Inferred（行业标准转译，未实测） |
| 关联变更批次 | `knowledge/change-batches/KBATCH-006-remaining-domains.md` |

## 消费方

- knowledge-evolution（#16）：消费批次记录判断知识演进基线
- coverage/semantic-capability/：消费批次记录更新discoverable/exploit_model_available/remediable/ecosystem_mapped状态

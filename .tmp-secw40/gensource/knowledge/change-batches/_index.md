# 变更批次索引（change-batches/）

## 用途

本目录记录知识层的每次变更批次，追踪知识内容的创建、修改和覆盖状态转移。每个批次是一个独立文件，使用 `template.md` 的格式编写。

## 当前批次

| batch_id | date | scope | 批次文件 | 状态 |
|---|---|---|---|---|
| KBATCH-001 | 2026-08-09 | 种子知识迁移 | `KBATCH-001-seed-migration.md` | 完成 |
| KBATCH-002 | 2026-08-09 | 注入域（INJ）12个UVS可执行知识建设 | 无独立批次文件（内容已并入对应条目，见下） | 完成（内容并入条目） |
| KBATCH-003 | 2026-08-09 | 并发/异常/计算/保护域16个UVS可执行知识建设 | `KBATCH-003-conc-exc-calc-prot.md` | 完成 |
| KBATCH-004 | 2026-08-09 | 内存/文件/输入域20个UVS可执行知识建设（20 vuln-patterns + 19 attack-patterns + 20 fix-patterns + 3覆盖矩阵更新） | `KBATCH-004-memory-file-input-domains.md` | 完成 |
| KBATCH-006 | 2026-08-09 | 剩余14个域44个UVS可执行知识建设 | `KBATCH-006-remaining-domains.md` | 完成 |

> 说明：KBATCH-005 未登记——资源/控制流/信息域与访问控制域的批次归属在条目版本历史中标注不一致，留待协议对账核实；本索引不杜撰不存在的批次编号，也不将未核实内容标记为已完成。

### KBATCH-002 说明（无独立批次文件）

KBATCH-002（注入域）无独立批次文件，其建设内容已直接并入对应知识条目，由以下条目版本历史标注 `KBATCH-002：初始创建` 登记引用关系：

| 知识库 | 数量 | 条目（文件） |
|---|---|---|
| vuln-patterns | 10 | inj-code-injection、inj-command-injection、inj-crlf-injection、inj-deserialization、inj-format-string、inj-neutralization-failure、inj-resource-injection、inj-special-element-failure、inj-ssrf、inj-xxe |
| attack-patterns | 9 | inj-code-benign-eval、inj-command-benign-marker、inj-crlf-benign-header、inj-deserialization-benign-gadget、inj-format-string-benign-specifier、inj-resource-benign-probe、inj-special-element-benign-marker、inj-ssrf-benign-callback、inj-xxe-benign-entity |
| fix-patterns | 9 | inj-code-no-dynamic-eval、inj-command-argument-array、inj-crlf-stripping、inj-deserialization-type-whitelist、inj-format-string-fixed-template、inj-resource-identifier-whitelist、inj-special-element-neutralization、inj-ssrf-url-whitelist、inj-xxe-disable-entities |
| coverage | 1 | semantic-capability/injection.md 覆盖分片 |

## 命名规则

- 文件名：`KBATCH-NNN-<slug>.md`
- `batch_id`：`KBATCH-NNN`（与文件名前缀一致）
- `NNN`：批次序号，三位数字，从 001 递增（当前实际使用 001/002/003/004/006，005 未使用）

## 批次记录要求

每个批次必须记录：

- `batch_id`：批次唯一标识
- `date`：批次日期
- `scope`：本批次覆盖的范围
- `source_versions`：涉及的来源版本
- `created/modified files`：创建和修改的文件清单
- `coverage_transitions`：覆盖状态转移记录
- 验证命令和结果
- 剩余缺口

## 台账与条目交叉引用

本索引（及 `coverage/batch-ledger.md`）与各条目版本历史中的 `KBATCH-NNN` 标注之间的交叉引用一致性，由协议对账检查（tests/ 交叉引用闭包检查）负责核销，本索引不逐一改写条目文件。已知不一致项如实登记：

- 内存/文件/输入域（KBATCH-004）条目版本历史标注为 `KBATCH-003` 而非 `KBATCH-004`；
- KBATCH-006 条目版本历史使用域名（如"AI域批量建设"）而非 `KBATCH-006` 批次号；
- 资源/控制流/信息域条目版本历史标注为 `KBATCH-003`，但其批次文件未在 change-batches/ 单独登记（对应批次号待协议对账确认，暂记为未登记）。

上述不一致均以本索引的批次归属为准，由协议对账检查逐项核销，禁止在本索引中声称台账与条目交叉引用已 100% 一致。

## 与其他目录的关系

| 关系类型 | 目标 | 说明 |
|---|---|---|
| `receives_from` | 各知识子目录 | 批次记录这些目录的变更 |
| `externally_mapped_to` | coverage/_index.md | 覆盖状态转移影响覆盖矩阵 |

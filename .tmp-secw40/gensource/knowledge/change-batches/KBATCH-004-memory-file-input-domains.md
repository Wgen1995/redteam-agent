# KBATCH-004：内存/文件/输入域可执行知识建设

> 本批次记录为内存域（MEM）、文件域（FILE）和输入域（INPUT）的20个UVS建设可执行知识（vuln-patterns/attack-patterns/fix-patterns）的完整变更。

## 批次元数据

| 字段 | 值 |
|---|---|
| batch_id | KBATCH-004 |
| date | 2026-08-09 |
| scope | 内存域5个UVS + 文件域6个UVS + 输入域9个UVS = 20个UVS的可执行知识建设（20个vuln-patterns + 19个attack-patterns + 20个fix-patterns + 3个覆盖矩阵更新 + 3个索引更新） |
| source_versions | 145个UVS（已有）；CWE标准转译（CWE-119/118/188/170/822/22/59/41/66/426/377/20/112/115/166/178/182/229/185/228系列） |

## 变更文件清单

### Created files

#### vuln-patterns（20个）

| 文件路径 | 条目ID | 关联UVS |
|---|---|---|
| `vuln-patterns/mem-bounds-failure.md` | VULN-MEM-BOUNDS-01 | UVS-MEM-BOUNDS-FAILURE |
| `vuln-patterns/mem-index-access-error.md` | VULN-MEM-INDEX-01 | UVS-MEM-INDEX-ACCESS-ERROR |
| `vuln-patterns/mem-layout-reliance.md` | VULN-MEM-LAYOUT-01 | UVS-MEM-LAYOUT-RELIANCE |
| `vuln-patterns/mem-null-termination.md` | VULN-MEM-NULLTERM-01 | UVS-MEM-NULL-TERMINATION |
| `vuln-patterns/mem-untrusted-pointer.md` | VULN-MEM-PTR-01 | UVS-MEM-UNTRUSTED-POINTER |
| `vuln-patterns/file-path-traversal.md` | VULN-FILE-TRAVERSAL-01 | UVS-FILE-PATH-TRAVERSAL |
| `vuln-patterns/file-link-following.md` | VULN-FILE-SYMLINK-01 | UVS-FILE-LINK-FOLLOWING |
| `vuln-patterns/file-path-equivalence.md` | VULN-FILE-PATHEQUIV-01 | UVS-FILE-PATH-EQUIVALENCE |
| `vuln-patterns/file-virtual-resource.md` | VULN-FILE-VIRTUAL-01 | UVS-FILE-VIRTUAL-RESOURCE |
| `vuln-patterns/file-untrusted-search-path.md` | VULN-FILE-SEARCHPATH-01 | UVS-FILE-UNTRUSTED-SEARCH-PATH |
| `vuln-patterns/file-insecure-temp.md` | VULN-FILE-TEMPFILE-01 | UVS-FILE-INSECURE-TEMP |
| `vuln-patterns/input-validation-failure.md` | VULN-INPUT-VALIDATION-01 | UVS-INPUT-VALIDATION-FAILURE |
| `vuln-patterns/input-xml-validation.md` | VULN-INPUT-XML-01 | UVS-INPUT-XML-VALIDATION |
| `vuln-patterns/input-misinterpretation.md` | VULN-INPUT-MISPARSE-01 | UVS-INPUT-MISINTERPRETATION |
| `vuln-patterns/input-special-element-handling.md` | VULN-INPUT-SPECELEM-01 | UVS-INPUT-SPECIAL-ELEMENT-HANDLING |
| `vuln-patterns/input-case-sensitivity.md` | VULN-INPUT-CASE-01 | UVS-INPUT-CASE-SENSITIVITY |
| `vuln-patterns/input-data-collapse.md` | VULN-INPUT-COLLAPSE-01 | UVS-INPUT-DATA-COLLAPSE |
| `vuln-patterns/input-handling-failure.md` | VULN-INPUT-HANDLING-01 | UVS-INPUT-HANDLING-FAILURE |
| `vuln-patterns/input-incorrect-regex.md` | VULN-INPUT-REGEX-01 | UVS-INPUT-INCORRECT-REGEX |
| `vuln-patterns/input-invalid-structure-handling.md` | VULN-INPUT-INVALIDSTRUCT-01 | UVS-INPUT-INVALID-STRUCTURE-HANDLING |

#### attack-patterns（19个）

| 文件路径 | 条目ID | 建立在哪个vuln-pattern之上 |
|---|---|---|
| `attack-patterns/mem-bounds-benign-overflow.md` | ATK-MEM-BOUNDS-01 | VULN-MEM-BOUNDS-01 |
| `attack-patterns/mem-index-benign-oob.md` | ATK-MEM-INDEX-01 | VULN-MEM-INDEX-01 |
| `attack-patterns/mem-layout-benign-diff.md` | ATK-MEM-LAYOUT-01 | VULN-MEM-LAYOUT-01 |
| `attack-patterns/mem-nullterm-benign-overread.md` | ATK-MEM-NULLTERM-01 | VULN-MEM-NULLTERM-01 |
| `attack-patterns/mem-ptr-benign-null.md` | ATK-MEM-PTR-01 | VULN-MEM-PTR-01 |
| `attack-patterns/file-traversal-benign-read.md` | ATK-FILE-TRAVERSAL-01 | VULN-FILE-TRAVERSAL-01 |
| `attack-patterns/file-symlink-benign-redirect.md` | ATK-FILE-SYMLINK-01 | VULN-FILE-SYMLINK-01 |
| `attack-patterns/file-pathequiv-benign-variant.md` | ATK-FILE-PATHEQUIV-01 | VULN-FILE-PATHEQUIV-01 |
| `attack-patterns/file-virtual-benign-probe.md` | ATK-FILE-VIRTUAL-01 | VULN-FILE-VIRTUAL-01 |
| `attack-patterns/file-searchpath-benign-implant.md` | ATK-FILE-SEARCHPATH-01 | VULN-FILE-SEARCHPATH-01 |
| `attack-patterns/file-tempfile-benign-predict.md` | ATK-FILE-TEMPFILE-01 | VULN-FILE-TEMPFILE-01 |
| `attack-patterns/input-xml-benign-entity.md` | ATK-INPUT-XML-01 | VULN-INPUT-XML-01 |
| `attack-patterns/input-misparse-benign-double-encode.md` | ATK-INPUT-MISPARSE-01 | VULN-INPUT-MISPARSE-01 |
| `attack-patterns/input-specelem-benign-structure.md` | ATK-INPUT-SPECELEM-01 | VULN-INPUT-SPECELEM-01 |
| `attack-patterns/input-case-benign-variant.md` | ATK-INPUT-CASE-01 | VULN-INPUT-CASE-01 |
| `attack-patterns/input-collapse-benign-composed.md` | ATK-INPUT-COLLAPSE-01 | VULN-INPUT-COLLAPSE-01 |
| `attack-patterns/input-handling-benign-unexpected.md` | ATK-INPUT-HANDLING-01 | VULN-INPUT-HANDLING-01 |
| `attack-patterns/input-regex-benign-redos.md` | ATK-INPUT-REGEX-01 | VULN-INPUT-REGEX-01 |
| `attack-patterns/input-invalidstruct-benign-malformed.md` | ATK-INPUT-INVALIDSTRUCT-01 | VULN-INPUT-INVALIDSTRUCT-01 |

注：UVS-INPUT-VALIDATION-FAILURE为抽象根模式，无独立活攻击面，不创建attack-pattern。

#### fix-patterns（20个）

| 文件路径 | 条目ID | 对应的vuln-pattern |
|---|---|---|
| `fix-patterns/mem-bounds-safe-functions.md` | FIX-MEM-BOUNDS-01 | VULN-MEM-BOUNDS-01 |
| `fix-patterns/mem-index-bounds-check.md` | FIX-MEM-INDEX-01 | VULN-MEM-INDEX-01 |
| `fix-patterns/mem-layout-explicit-parse.md` | FIX-MEM-LAYOUT-01 | VULN-MEM-LAYOUT-01 |
| `fix-patterns/mem-nullterm-termination.md` | FIX-MEM-NULLTERM-01 | VULN-MEM-NULLTERM-01 |
| `fix-patterns/mem-ptr-no-external.md` | FIX-MEM-PTR-01 | VULN-MEM-PTR-01 |
| `fix-patterns/file-traversal-canonicalize.md` | FIX-FILE-TRAVERSAL-01 | VULN-FILE-TRAVERSAL-01 |
| `fix-patterns/file-symlink-nofollow.md` | FIX-FILE-SYMLINK-01 | VULN-FILE-SYMLINK-01 |
| `fix-patterns/file-pathequiv-canonicalize.md` | FIX-FILE-PATHEQUIV-01 | VULN-FILE-PATHEQUIV-01 |
| `fix-patterns/file-virtual-safe-filename.md` | FIX-FILE-VIRTUAL-01 | VULN-FILE-VIRTUAL-01 |
| `fix-patterns/file-searchpath-absolute.md` | FIX-FILE-SEARCHPATH-01 | VULN-FILE-SEARCHPATH-01 |
| `fix-patterns/file-tempfile-mkstemp.md` | FIX-FILE-TEMPFILE-01 | VULN-FILE-TEMPFILE-01 |
| `fix-patterns/input-validation-framework.md` | FIX-INPUT-VALIDATION-01 | VULN-INPUT-VALIDATION-01 |
| `fix-patterns/input-xml-disable-entities.md` | FIX-INPUT-XML-01 | VULN-INPUT-XML-01 |
| `fix-patterns/input-misparse-canonical-decode.md` | FIX-INPUT-MISPARSE-01 | VULN-INPUT-MISPARSE-01 |
| `fix-patterns/input-specelem-structure-check.md` | FIX-INPUT-SPECELEM-01 | VULN-INPUT-SPECELEM-01 |
| `fix-patterns/input-case-normalize.md` | FIX-INPUT-CASE-01 | VULN-INPUT-CASE-01 |
| `fix-patterns/input-collapse-normalize-first.md` | FIX-INPUT-COLLAPSE-01 | VULN-INPUT-COLLAPSE-01 |
| `fix-patterns/input-handling-complete-checks.md` | FIX-INPUT-HANDLING-01 | VULN-INPUT-HANDLING-01 |
| `fix-patterns/input-regex-fix-anchors.md` | FIX-INPUT-REGEX-01 | VULN-INPUT-REGEX-01 |
| `fix-patterns/input-invalidstruct-strict-parse.md` | FIX-INPUT-INVALIDSTRUCT-01 | VULN-INPUT-INVALIDSTRUCT-01 |

### Modified files

| 文件路径 | 说明 |
|---|---|
| `coverage/semantic-capability/memory.md` | 5个UVS的discoverable/verifiable/exploit_model/remediable从not_started更新为complete；ecosystem_mapped更新为partial |
| `coverage/semantic-capability/file.md` | 6个UVS的discoverable/verifiable/exploit_model/remediable从not_started更新为complete；ecosystem_mapped更新为partial |
| `coverage/semantic-capability/input.md` | 9个UVS的discoverable/verifiable/remediable从not_started更新为complete；8个UVS的exploit_model更新为complete，UVS-INPUT-VALIDATION-FAILURE为not_applicable；ecosystem_mapped更新为partial |
| `vuln-patterns/_index.md` | 索引表新增20条内存/文件/输入域条目；更新条目计数 |
| `attack-patterns/_index.md` | 索引表新增19条内存/文件/输入域条目；更新条目计数 |
| `fix-patterns/_index.md` | 索引表新增20条内存/文件/输入域条目；更新条目计数 |

## 覆盖状态转移记录

| UVS | discoverable | verifiable | exploit_model | remediable | ecosystem_mapped |
|---|---|---|---|---|---|
| UVS-MEM-BOUNDS-FAILURE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-MEM-INDEX-ACCESS-ERROR | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-MEM-LAYOUT-RELIANCE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-MEM-NULL-TERMINATION | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-MEM-UNTRUSTED-POINTER | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-PATH-TRAVERSAL | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-LINK-FOLLOWING | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-PATH-EQUIVALENCE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-VIRTUAL-RESOURCE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-UNTRUSTED-SEARCH-PATH | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-FILE-INSECURE-TEMP | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-VALIDATION-FAILURE | not_started -> complete | not_started -> complete | not_started -> not_applicable | not_started -> complete | not_started -> partial |
| UVS-INPUT-XML-VALIDATION | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-MISINTERPRETATION | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-SPECIAL-ELEMENT-HANDLING | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-CASE-SENSITIVITY | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-DATA-COLLAPSE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-HANDLING-FAILURE | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-INCORRECT-REGEX | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |
| UVS-INPUT-INVALID-STRUCTURE-HANDLING | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> complete | not_started -> partial |

## 生态映射覆盖说明

每个vuln-pattern条目内联覆盖了C/C++、Rust、Python、Java、Go的主要API（危险API/安全替代/边界检查机制等）。独立ECMAP-*文件尚未创建，ecosystem_mapped维度标记为partial。

## 引用分级说明

本批次全部条目引用分级为**Inferred**——基于CWE标准语义和公开API行为转译，无GenSource实测案例。validated维度保持not_started。

## 剩余缺口

- 独立ECMAP-*生态映射文件待创建（当前为vuln-pattern内联覆盖）
- UVS文件的三库引用字段待更新（从"留空"更新为实际条目ID）
- validated维度待GenSource实测案例补充
- 各条目文件版本历史中引用的批次ID为KBATCH-003，与本批次记录ID KBATCH-004存在编号差异，后续统一修正

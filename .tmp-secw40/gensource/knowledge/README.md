# 知识层（knowledge/）权威入口

> 来源：决策文档 `docs/research/decision/24-category15-knowledge-organization-spec.md`（#15知识组织与检索，已确认）第4/5节；`docs/research/decision/34-quality-driven-lightweight-graph-spec.md`（#34质量驱动轻量图规格，已冻结）第10节"知识与追溯图策略"；`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）。本文件是知识层的权威入口，说明层级结构、稳定ID约定、按需加载纪律和知识边界。

## 1. 知识层定位

GenSource是纯自然语言白盒源码安全审计技能包，不包含自研扫描程序、图引擎、数据库或validator。知识层是GenSource的**检测能力知识基座**——审计Skill的消费对象，不是运行时组件。

知识层遵循**F1基座原则**（#15/#06已确认）：纯Markdown小文件+表格索引，不采纳向量/混合检索。索引始终保持"表格化+人工/agent扫一眼就能判断该不该细看"的哲学。

## 2. 目录层级

```text
knowledge/
  README.md                          本文件，知识层权威入口
  ontology/
    _index.md                        本体索引，按规格链路排列概念
    relation-types.md                关系类型登记
    concepts/                        17个核心本体概念（ONT-*.md）
  industry-catalog/
    _index.md                        行业目录索引
    source-ledgers/                  来源账本（SRC-*.md），保存原始分类
    semantics/                       统一漏洞语义（UVS-*.md），去重和关系整理
    adjudication/                    裁决记录（ADJ-*.md），无法归并的原始条目
  surfaces/                          攻击面类别索引
  entries/                           入口类别索引
  sources/                           数据源类别索引
  propagation/                       传播类别索引（含传播/转换/存储）
  controls/                          控制类别索引（含Guard/Policy Decision/Sanitizer/Encoder）
  sinks/                             汇点类别索引（含Sink/State Transition/Resource Consumption）
  ecosystem-mappings/                生态映射（ECMAP-*.md）
  coverage/
    _index.md                        覆盖矩阵入口
    source-reconciliation/           来源对账记录（COV-SRC-*.md）
    semantic-capability/             语义能力覆盖记录（COV-CAP-*.md）
  _templates/                        编写模板（不计入正式知识）
  change-batches/                    变更批次记录
  vuln-patterns/                     漏洞识别模式（已有，#15知识组织规格落地）
  fix-patterns/                      标准修复模式（已有）
  attack-patterns/                   攻击利用手法（已有）
```

## 3. 稳定ID约定

知识层所有正式条目使用稳定ID，ID是文件名的一部分，变更ID等同于删除旧条目并新建条目。

| ID前缀 | 目录 | 含义 |
|---|---|---|
| ONT- | ontology/concepts/ | 本体概念 |
| SRC- | industry-catalog/source-ledgers/ | 来源账本 |
| UVS- | industry-catalog/semantics/ | 统一漏洞语义 |
| ADJ- | industry-catalog/adjudication/ | 裁决记录 |
| ECMAP- | ecosystem-mappings/ | 生态映射 |
| COV-SRC- | coverage/source-reconciliation/ | 来源对账记录 |
| COV-CAP- | coverage/semantic-capability/ | 语义能力覆盖记录 |
| BATCH- | change-batches/ | 变更批次 |
| VULN- | vuln-patterns/ | 漏洞识别模式（已有） |
| FIX- | fix-patterns/ | 标准修复模式（已有） |
| ATK- | attack-patterns/ | 攻击利用手法（已有） |

引用条目时必须使用稳定ID，且ID必须可被机械核对（#17 T2机械核对能力）——检查ID是否存在于对应索引表格中。

## 4. 按需加载纪律

知识层按需加载，不是全量预读。审计Skill在需要时查阅对应目录的 `_index.md`，根据索引判断是否需要打开具体条目文件细看。

- **强制显式查阅纪律**（#15已确认）："要不要查、查了没有"不能交给Skill自由裁量。产出必须显式写明查了哪个条目ID。查不到匹配时必须显式写"未匹配"，不能含糊跳过。
- **引用分级**（#7/#11已确认）：Observed / Inferred / Proposed三段式标签，不新造标签体系。分级标注写在审计产出记录里，不是知识条目自身的字段。

## 5. 手工维护原则

知识层是**手工维护**的，不是程序自动生成的。来源对账、语义归并、裁决和覆盖评估均由人工语义处理完成。

- 不使用程序化爬虫、validator、图数据库或向量数据库。
- 来源账本按官方来源显示顺序人工转录全部原始条目，不使用"其余同理""略"或程序批量空壳。
- 同义外部项映射同一UVS；仅API或框架名称不同的内容进入生态变体；根因不同则拆分。
- 禁止由名称映射自动推导检测能力——cataloged不等于discoverable。

## 6. 非运行时图边界

知识层中的关系引用（`relation-types.md`中登记的关系类型）只是**Markdown引用**，不是运行时图。GenSource不建设运行时Knowledge Graph或Traceability Graph（#34第10节已确认）。

- 稳定ID和证据引用继续作为权威追溯链。
- 如果未来需要管理可视化，可从现有产物只读派生Traceability Graph；派生物必须可删除、可重建，不参与检测、恢复或事实写入。
- CWE邻近知识索引仅在模式增长到数十条、exact match频繁失败且评测证明开放推理不稳定时再单独决策。

## 7. 子目录索引链接

| 子目录 | 索引文件 | 用途 |
|---|---|---|
| ontology | [ontology/_index.md](ontology/_index.md) | 17个核心本体概念，按规格链路排列 |
| industry-catalog | [industry-catalog/_index.md](industry-catalog/_index.md) | 行业来源目录、统一语义和裁决 |
| surfaces | [surfaces/_index.md](surfaces/_index.md) | 攻击面类别索引 |
| entries | [entries/_index.md](entries/_index.md) | 入口类别索引 |
| sources | [sources/_index.md](sources/_index.md) | 数据源类别索引 |
| propagation | [propagation/_index.md](propagation/_index.md) | 传播/转换/存储类别索引 |
| controls | [controls/_index.md](controls/_index.md) | Guard/Policy Decision/Sanitizer/Encoder类别索引 |
| sinks | [sinks/_index.md](sinks/_index.md) | Sink/State Transition/Resource Consumption类别索引 |
| ecosystem-mappings | [ecosystem-mappings/_index.md](ecosystem-mappings/_index.md) | 生态映射索引 |
| coverage | [coverage/_index.md](coverage/_index.md) | 覆盖矩阵入口 |
| _templates | [\_templates/](_templates/) | 编写模板（不计入正式知识） |
| change-batches | [change-batches/_index.md](change-batches/_index.md) | 变更批次记录 |
| vuln-patterns | [vuln-patterns/_index.md](vuln-patterns/_index.md) | 漏洞识别模式（已有） |
| fix-patterns | [fix-patterns/_index.md](fix-patterns/_index.md) | 标准修复模式（已有） |
| attack-patterns | [attack-patterns/_index.md](attack-patterns/_index.md) | 攻击利用手法（已有） |

## 8. 当前状态声明

知识层目前处于**本体与目录骨架建立阶段**。17个核心本体概念、关系类型登记和Surface至Sink类别索引已建立。行业来源账本、统一漏洞语义、裁决记录和覆盖矩阵将在后续批次中逐步填充。

条目数量仍很少，覆盖面远未完整，未来仍需持续积累。语言覆盖度老实披露（#13已确立原则）：当前知识条目以Python/Web生态为主，其他语言/框架的条目数量明显偏少，完整性置信度较低。

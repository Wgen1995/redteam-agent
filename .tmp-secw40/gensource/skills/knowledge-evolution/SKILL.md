---
name: knowledge-evolution
description: 伴生能力，不在单次审计主序列里（不属于scope-and-context~report-delivery的线性流水线）；触发场景：审计周期结束后批量回顾，或跨多次审计周期性回顾时由用户/运营方按需调用，用于评估本轮/历次审计中的确认发现是否够格晋升为永久知识、以及现有知识条目是否已过时或被证明是误报。不适用场景：单次审计主序列内的常规子步骤，本文件不打断主流程，也不在候选发现/验证阶段被同步调用。
---

# 知识演进

## 目标

本阶段解决"审计过程中产生的新发现，如何有原则地沉淀为可复用的永久知识（而不是每次审计都从零开始）"的问题：什么样的发现够格被评估为知识候选、单次偶然出现为什么不该轻易采信、晋升决定为什么不能由系统自己拍板、旧知识条目失效或被证明是误报时该怎么处理而不是悄悄抹掉痕迹，以及——GenSource作为可能被多个不同项目/客户共享安装的技能包，一次审计学到的东西是否应该被下一次审计的目标"看到"，这件事默认该怎么划界。

本阶段消费#4验证与#5定级产出的候选，并独立将候选语义与知识库快照比对以派生“未匹配”结论，应用#17已确立的人工介入框架（不可逆效应类）与#9已确立的disposition纪律，遵循#10已确立的“伴生能力”分类。多项目共享安装场景下如何探测当前安装范围仍依赖实际部署能力，本文件不假设具体实现。

**契约与诚实声明（必须保留，不得省略）：** 本阶段正式遵循 [`../../contracts/data-structures/knowledge-base-entry.md`](../../contracts/data-structures/knowledge-base-entry.md)、[`../../contracts/enum-registry.md`](../../contracts/enum-registry.md) 与 [`../../contracts/field-ownership-table.md`](../../contracts/field-ownership-table.md)，产出携带 `stage_result`、`version`、`resume_context`。本类别在调研的16个系统中仅SourceCPT具备类似能力，且其唯一真实验证未成功晋升，仍属于“架构上存在、运营上未经证明”。跨项目隔离的具体技术实现与“跨≥2个独立场景”初始阈值仍须依实际部署和运营数据校准，但在调整前必须遵守当前契约门槛。

本阶段同时引用`../../shared/quality-gates.md`：提议生成后必须过Gate-1和Gate-2，之后仍须人工`approved`才能写入知识库；任何Gate都不能代替人工授权。

**Work Graph路由**：本能力的A阶段→人工决定→B阶段人工回环路由由`../../shared/work-graph.md`的"伴生能力路由"一节定义。A阶段完成后不自动进入B阶段，必须等待人工授权方写入`human_decision`后才由调度角色路由到B阶段。

## 输入

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| candidate_pool | 结构化候选列表（跨审计累积） | 是 | 调用方写入、#16只读；每项为`{source_audit_id: string, candidate: object}`，candidate完整遵循candidate-finding契约。`source_audit_id`由调用方/编排上下文提供，用于独立场景计数；池内候选无需预先携带#16的确认或匹配判断 |
| knowledge_base_snapshot | 结构化知识库当前状态 | 是 | 当前`knowledge/`目录下各类知识条目及其状态（active/deprecated/archived）与命中/miss统计，用于判断候选是否已存在对应条目、及判断已有条目是否满足过时/错误处理触发条件 |
| installation_scope | 部署范围标识 | 是 | 标识当前安装是共享安装（多项目/多客户）还是单项目专属安装，及若为共享安装时用户/运营方是否显式配置为"有意共享"；决定本次晋升产出的知识条目落盘范围（项目专属 vs 共享知识库），可能依赖#14能力探测配合 |
| human_decision | 人工决定记录数组 | 是 | 人工授权方唯一写入，#16只读；阶段A必须为`[]`，阶段B按proposal记录 `decision=approved`/`rejected`/`deferred`，后两者理由非空 |
| deprecation_signal | 过时/误报信号 | 否 | 现有知识条目长期不再匹配、或反复匹配后被证明是误报的信号来源（如连续miss统计、或verification-and-rating阶段产出的误报判定），供本阶段判断是否需要状态标注；不提供则仅依据knowledge_base_snapshot中已有的统计字段判断 |

## 硬性约束

引用 ../../shared/anti-hallucination.md 与 ../../shared/human-in-the-loop.md。

1. **晋升决定不得由系统自动执行**：阶段A只产出 `promotion_proposals`/`deprecation_proposals`；人工授权方随后写 `human_decision`。阶段B中#16只读消费决定，只有 `decision=approved` 才执行知识写入或状态变更，`rejected`/`deferred` 只留痕。
2. **晋升门槛缺一不可**：候选未同时满足"跨≥2个独立场景出现"与"每次出现都经过真正的#4验证"两项，一律不得进入提议清单，不允许因候选"看起来很像真实模式"而豁免门槛；单次出现（N=1）不构成晋升理由。
3. **过时/错误知识不得静默删除**：`knowledge_entry_status` 使用注册表 [`knowledge_entry_status`](../../contracts/enum-registry.md#knowledge_entry_status)。进入非活跃状态必须有批准决定；物理删除禁止，`knowledge_evidence_history` 只能追加，不得改写、重排或删除。
4. **跨项目数据隔离默认开启（GenSource原创，非引用任何竞品）**：知识晋升产出默认限定在当前项目/安装范围内，不自动跨审计目标共享；仅当installation_scope显式标注用户/运营方已配置为有意共享（如内部安全团队审计自己公司多个仓库这种合理场景）时，才允许提议共享范围落盘；不确定归属或未显式配置时，一律按项目专属范围处理，不得因"可能有用"而默认共享——目的是防止服务多个不同客户时知识跨客户泄露。
5. **证据强度如实标注**：本阶段任何输出不得暗示晋升机制已被证明有效；须在`evidence_strength_disclosure`中如实说明本类别竞品证据稀薄（16个系统仅SourceCPT一家有此能力）、且SourceCPT自身唯一一次真实验证从未成功晋升过，不得省略或弱化此声明。

## 执行步骤

1. 判断触发场景：确认本次调用发生在审计周期结束后的批量回顾，或用户/运营方显式发起的周期性复盘，而非单次审计主序列内的常规子步骤（应用#10已确立的"伴生能力"分类）。
2. 候选池初筛：逐个读取包装元素的`candidate.verification_verdict.value`，仅保留值为`confirmed`的candidate；随后将每个candidate的可泛化语义与`knowledge_base_snapshot`逐项独立比对，仅保留不存在语义匹配知识条目的candidate。确认状态和未匹配结论均由#16读取或计算，不要求调用方把它们写入candidate。**四类缺口分别处理**：
   - **漏洞模式缺口**：候选命中了某种漏洞信号但`vuln-patterns/`无对应条目——`vuln_pattern_refs`为空且`knowledge_consultations[]`存在`consultation_result=not_matched`项时，评估是否够格晋升为新vuln-pattern条目。
   - **攻击模式缺口**：候选需要可利用性证明但`attack-patterns/`无对应条目——`attack_pattern_refs`为空且exploit-proof记录了"未匹配attack-pattern，本次采用临时实现"时，评估是否够格晋升为新attack-pattern条目。
   - **修复模式缺口**：候选需要修复指导但`fix-patterns/`无对应条目——`fix_pattern_ref`为空且remediation-guidance记录了"未匹配，本次修复为个案定制"时，评估是否够格晋升为新fix-pattern条目。
   - **生态映射缺口**：候选涉及的语言/框架在`ecosystem-mappings/`无对应条目——`ecosystem_mapping_refs`为空且scope-and-context记录了"该语言/框架无对应生态映射"时，评估是否够格晋升为新ecosystem-mapping条目。
   四类缺口的晋升门槛相同（跨≥2个独立场景+每次经过#4验证），但产出条目类型不同，需分别生成对应的`promotion_proposals`。
3. 跨场景计数：将初筛结果按同一可泛化语义归并，仅以包装层不同的`source_audit_id`计独立场景；同一`source_audit_id`内的重复实例只计一次。
4. 门槛判定：同一可泛化语义必须至少对应2个不同`source_audit_id`，且参与计数的每个`candidate.verification_verdict.value`均为`confirmed`，否则不得生成晋升提议。仅从各candidate的`verification_baseline`、`candidate_specific_checklist`等已登记验证字段中实际存在的`evidence_refs`汇集提议证据，不要求candidate额外承载汇总字段。
5. **阶段A生成提议**：对通过门槛判定的候选只生成 `promotion_proposals`；对弃用信号只生成 `deprecation_proposals`。此时 `human_decision=[]`，不得写知识库。
6. 归属范围判定：结合installation_scope判断本条提议知识若被批准应落盘到项目专属知识库还是共享知识库；默认限定在项目/安装范围内，不自动跨审计目标共享；仅当installation_scope显式标注"用户/运营方已配置为有意共享"时，才允许提议共享范围落盘；不确定或未显式配置时，默认按项目专属范围提议。
7. 等待人工授权方针对proposal写入 `human_decision`；#16不得代写、改写或自动批准该输入字段。
8. **阶段B消费决定**：#16只读消费 `human_decision` 并通过 `decision_ref` 写执行结果。仅 `approved` 写入新条目（初始状态 `active`）或执行 `deprecated`/`archived` 状态变更；`rejected`/`deferred` 不写库、不改变状态。
9. 为批准写入或状态变化追加 `knowledge_evidence_history`，完整保留既有历史，并汇总本次周期性回顾记录。

## 输出

输出是`knowledge-base-entry.md`定义的完整产物。调用输入快照必须原样携带，#16仅可读取、筛选和引用，不得改写、裁剪、重排或把筛选结果回写为输入：`candidate_pool`、`knowledge_base_snapshot`、`installation_scope`始终携带；`human_decision`始终携带（阶段A为原样空数组，阶段B为人工授权方写入的原数组）；调用方提供`deprecation_signal`时原样携带，未提供时按契约保持省略。其余字段由#16按字段写权限生成。

| 字段 | 说明 |
|---|---|
| stage_result / version / resume_context | 本阶段共享执行状态、契约版本与续跑上下文 |
| candidate_pool | 调用方提供的`{source_audit_id, candidate}`包装元素完整只读快照，原样携带 |
| knowledge_base_snapshot | 调用方提供的知识库状态完整只读快照，原样携带 |
| installation_scope | 调用方提供的部署范围完整只读快照，原样携带 |
| human_decision | 人工授权方写入的完整决定记录原样携带；#16只读消费，机器值见注册表 [`human_decision`](../../contracts/enum-registry.md#human_decision) |
| deprecation_signal | 调用方提供时原样携带的完整只读快照；未提供时省略 |
| promotion_proposals | 本次通过门槛判定、提交人工裁决的晋升提议列表；`scenario_summaries`由不同`source_audit_id`派生，`verification_evidence_refs`从candidate既有验证字段中的`evidence_refs`汇集，二者仅存在于#16提议输出 |
| promotion_decisions | 阶段B执行结果，通过`decision_ref`引用人工决定；不重复承载理由、actor或日期 |
| deprecation_proposals | 本次识别出的过时/误报知识条目状态标注提议列表，每条含条目ID/触发条件（长期不匹配或反复误报）/建议新状态/理由 |
| deprecation_decisions | 已获得人工裁决的过时处理结果 |
| scope_assignment | 每条批准写入的知识条目最终落盘范围（项目专属/共享）及判定依据 |
| evidence_strength_disclosure | 附带声明——本次机制设计所依据的门槛思路参考自SourceCPT但SourceCPT自身从未真正验证晋升成功，本次输出的门槛判定结果同样属于"架构上存在、运营上未经证明"范畴，不代表已证明有效 |
| knowledge_entry_states | 按条目记录注册表 [`knowledge_entry_status`](../../contracts/enum-registry.md#knowledge_entry_status) 当前状态；只有批准决定可创建或改变状态 |
| knowledge_evidence_history | 仅追加的知识证据和决策历史，禁止改写、重排或删除既有条目 |

**零候选/零发现时的兜底产出规定：**
- 若本次周期性回顾无可晋升候选：输出 `promotion_proposals=[]`；deprecation检查仍独立执行。阶段A保持 `human_decision=[]`，不产出伪造的decision记录。
- 若deprecation检查未发现任何满足触发条件的现有条目：输出 `deprecation_proposals=[]`；不得省略该字段，以便区分“检查过但无结果”与“未检查”。

## 阶段Gate

- Gate-1核对每个提议引用的独立场景、candidate和证据真实存在，决策引用与proposal一一对应，知识历史只追加。
- Gate-2使用干净上下文检查是否真跨独立场景、是否已有等价知识、是否把同一CWE变种包装成全新知识、是否越过项目隔离边界。
- Gate通过后仍只生成提议；只有人工`human_decision.decision=approved`才能执行写入或状态变更。

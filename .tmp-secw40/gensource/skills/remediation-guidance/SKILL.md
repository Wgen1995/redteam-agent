---
name: remediation-guidance
description: 伴生能力，不在主序列（主序列为阶段0客观枚举→阶段1候选全量发现→阶段2验证与定级→阶段3报告交付）。默认不独立执行：修复建议内容并入 report-delivery 产出的 findings/V{N}.md 的"修复建议"小节（一句话+代码示例）；仅用户显式请求独立修复指导时才加载本文件，以`root_cause_group_id`为处理单元产出完整修复指导。`remediation_mode`仅使用`tactical_patch`或`structural_hardening_proposal`；战术补丁与跨组结构加固提案可并行产出。已落地补丁须复用#6 PoC验证整个根因组，并经独立对抗复核后写入`final_result=fixed`或`needs_human_decision`。无活攻击面的`informational`代码事实、`unconfirmed`和`refuted`候选不进入本阶段。
---

# 修复指导

## 目标

本阶段回答的问题：给定一个已被verification-and-rating判定为"已确认"的漏洞，怎么产出一份扎根实际代码结构、可执行、真正堵住安全边界且不破坏合法功能的修复方案；以及多个不同根因共享同一架构弱点时是否值得提出架构级加固方案。修复不是"生成补丁就算完成"：含`evidence_mode=executed`段的#6证明必须在修复后真实重跑该段PoC；全部段为`inferred`的#6证明不得声称重新执行，只能由独立角色对修复后代码重走同一静态证据链。两种路径均须对整个根因组核查并做独立对抗复核。

**接口关系**：本阶段按[`../../contracts/data-structures/candidate-finding.md`](../../contracts/data-structures/candidate-finding.md)消费#3-#6字段并写入#7字段段，机器值以[`../../contracts/enum-registry.md`](../../contracts/enum-registry.md)为准，阶段状态与消费流程以[`../../contracts/README.md`](../../contracts/README.md)为准。窄范围战术修复可消费`knowledge/fix-patterns/`，结构加固提案只产出契约规定的内容，不处理#8报告排版。

**诚实声明（必须保留，不得省略）：**

1. #6 PoC与#7修复字段均已由`candidate-finding.md`定义，本阶段按契约消费和输出，不自行推断字段。
2. `knowledge/fix-patterns/`的具体分类粒度和条目路径仍由知识组织设计确定，本文件不预设。
3. contracts只定义`proposal_content`与`structural_hardening_link`等字段，不规定运行时独立文件路径；默认在本stage产出目录生成结构化提案产物，并由#8写入指向该实际产物的有效相对链接。
4. `final_result=inherently_safe`仅保留为回退#4复核后的投影结果：#7发现新证据时只能请求回退，不能单方写入；#4据新证据将`verification_verdict.value`改为`refuted`后，该记录不再是confirmed finding，也不继续生成漏洞修复。
5. 以下内容经文档2交叉验证一节批判性过滤后判定不采纳，如实记录以防未来被同类材料带偏：Codex `propose-security-hardening/SKILL.md`关于"第一人称复数/专业温暖语气/避免套路化开场白"等写作文风要求（是Codex自身产品的行文风格选择，与"修复指导该有什么内容"无关，若#8报告呈现阶段确需考虑行文风格，应另行独立论证，本文件不预先假设）；具体文件名（`hardening.json`/`hardening.md`/`proposals/<id>.md`/Mermaid图）不采纳，运行时按stage产出目录约定命名；"Workbench三阶段"（Generate/Apply/Verify分离调用）的具体产品实现形式不采纳，但其背后"不能让同一次调用既打补丁又自我认证验证通过"的原则已通过下方硬性约束第6条落地，不需要引入新概念。

## 输入

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 已确认活跃漏洞列表（verification-and-rating产出） | 结构化列表 | 是 | 仅`verification_verdict.value=confirmed`且六项适用基线为`pass`的活攻击面漏洞；须含`final_severity`/`root_cause_group_id`等字段。`critical`/`high`/`medium`/`low`必须含`priority`，`ignore`禁止含`priority`且不主动修复；`informational`代码卫生记录、`unconfirmed`/`refuted`不进入本阶段 |
| exploit-proof产出的PoC/复现手段（#6） | 结构化数据及产物引用 | 条件必填 | 仅对进入本阶段且需要验证已落地补丁的活跃漏洞必填；按契约消费`poc_id`、`evidence_composition`、`evidence_segments`、`package_content`与相关验证字段。代码卫生记录不进入#7，因此不要求PoC |
| root_cause_group_id（candidate-discovery产出，#3） | 标识引用 | 是 | 修复验证时用于核查整个根因组内的等价路径实例，不能只核查被报告的那一个实例；架构性加固提案判断时用于识别"多个不同根因组"是否共享同一架构弱点 |
| knowledge/fix-patterns/目录（窄范围战术修复知识库） | 知识库资源 | 窄范围修复时必填 | 模式驱动的战术修复依赖此目录；具体分类粒度待#15（知识组织类别）确定，本文件不预先假设条目路径 |
| 目标代码库只读、外部工作副本可写 | 环境 | 是 | 目标源码树默认只读（见`../../SKILL.md`"默认目标只读"约束和`candidate-finding.md`的`write_boundary`字段）；生成补丁diff、追踪改动分支、检查等价危险sink时读取目标代码，补丁内容和工作副本结果写入`write_boundary.working_copy_path`或`write_boundary.output_path`。修改工作副本需动态执行授权；修改真实目标树需单独、明确且针对本次动作的授权。不得改写candidate发现字段、验证终态或代替独立复核写通过 |
| 现有检查/测试环境 | 环境 | 否 | 供优先级顺序第4项"现有检查通过"验证使用；不可用时须如实记录"未能验证现有检查是否通过"，不得默认视为已通过 |
| 独立对抗复核角色上下文 | 角色/上下文 | 是 | 承担修复本身的独立对抗复核（检查等价绕过路径），必须与提出补丁/提案的分析方角色隔离，不能自我复核、不能自我认证验证通过 |

## 硬性约束

引用 `../../shared/anti-hallucination.md` 的A类（证据溯源）与D类（置信度校准）：本阶段结果和架构聚类依据必须追溯到真实证据。仅含`evidence_mode=executed`段的PoC可复用#6 PoC真实重跑；全部段为`inferred`的PoC只能重走修复后静态证据链，且必须由独立复核确认链路已断，禁止把静态走查写成执行结果。

引用 `../../shared/field-ownership.md` 的字段级写权限通用纪律：提出补丁/提案内容与认证"验证已通过"必须是写权限分离的两个动作——生成补丁内容的同一次判断，对"验证结果"字段没有写权限，只能由独立的验证步骤/角色写入，不能自我认证（对应文档2"分离生成与自我认证"结论，复用#10已有的字段写权限原则）。

引用 `../../shared/deployment-environment.md`：步骤D"独立对抗复核"（T1机制）的可用性依赖该文件"子调用/子agent派发能力"探测结果，不可用时退化为同会话内弱化版独立性，需显式标注（复用`anti-hallucination.md`的独立性诚实声明）。

引用 `../../shared/quality-gates.md` 与 `../../shared/work-graph.md`：本阶段必须过Gate-1；补丁实际落地、高风险修复或高绕过风险必须过Gate-2。共享Gate只统一结果和返工，补丁生成/验证/绕过检查仍由本文件定义。

本阶段专属补充约束（不可违反，逐条对应#7决策文档"最终确定的机制"）：

1. **优先级顺序不可逆序牺牲**：漏洞分类正确性 → 安全边界是否真正堵住 → 合法行为/兼容性保留 → 现有检查通过 → 代码惯例符合 → 改动范围最小；后面的属性不能拿来换前面的属性（Codex `fix-finding/SKILL.md`原文逐字："Never trade an earlier property for a later one."）。若为了"通过现有测试"就弱化安全检查本身，产出的东西比不修复更糟（制造虚假安全感），必须拒绝这类补丁，不得因为"测试变绿了"就视为修复成功。
2. **不得为了让检查通过而弱化安全边界**：不得削弱鉴权、授权、租户隔离、输入校验、沙箱、日志记录等安全机制去凑合通过现有检查（Codex `fix-finding/SKILL.md`原文逐字："Do not weaken authentication, authorization, tenant isolation, input validation, sandboxing, or logging to make tests pass."）；该纪律与优先级顺序第2项/第4项冲突时，优先级顺序（安全边界堵住优先于现有检查通过）优先。
3. **架构性加固提案的触发门槛**：仅当多个发现共享同一被违反的不变量/信任边界/控制归属方时才触发，不能只按CWE/严重度/目录/标题聚类就贸然提出架构级方案；不够格时在相关B1 `tactical_patch`记录的`hardening_cluster_basis`中写`structural_hardening_recommended=false`及理由，不另建空修复记录、不生成`proposal_content`，也不为该评估另写`final_result`。
4. **修复验证保持#6证据模式真实性**：含`evidence_mode=executed`段时真实重跑该段PoC，确认报告实例及整个`root_cause_group_id`不再触发；全部段为`inferred`时不得执行或声称重跑，只能对修复后代码重走#6同一静态证据链，并由独立复核确认报告实例及全组链路均已断。
5. **修复本身需要一次独立的对抗性复核**：专门检查该patch是否留下等价的绕过路径，复核视角不依赖提出补丁时的原始修复理由，须与提出补丁的分析方角色隔离，不能自我复核。
6. **生成与自我认证分离**：提出补丁/提案内容的同一次判断，不能同时自我认证"已验证通过"；验证结果必须由独立的验证步骤/角色写入（`field-ownership.md`原则的直接应用）。
7. **证据标签复用#11溯源纪律的Observed/Inferred/Proposed三段式标注**：本阶段产出的每一条修复内容/加固提案，须标注该内容是基于实际观测到的代码证据（Observed）、基于推断（Inferred，如"预期会堵住此类路径但尚未逐一验证全部分支"）、还是纯提议性内容（Proposed，如架构性加固提案中尚未落地验证的建议性方案），不得混用、不得省略标注。
8. **`ignore`不进入主动修复**：`final_severity=ignore`的confirmed finding按矩阵政策不进入主动修复队列，不得为其擅自生成补丁、修复建议或架构加固提案；但它有活攻击路径，必须显式记录为“政策忽略”、保留给#8完整报告并转交#9状态机显式处置，不得从输入、报告或生命周期链路中静默删除。
9. **`inherently_safe`不能由#7锁定**：#7若发现“无需代码改动即可满足修复目标”，必须记录此前不存在的新证据并回退#4复核；在#4更新前只能写`needs_human_decision`。仅当#4据此将原风险主张改判为`refuted`后，历史修复投影才可记录`inherently_safe`，且报告不得再称其为confirmed finding。

## 执行步骤

### A. 判断修复模式（作用于单个或跨多个root_cause_group）

1. 对每个已确认漏洞先按`final_severity`分流：`ignore`记录为政策忽略并保留给#8报告、转交#9显式处置，不进入B1/B2且不生成修复；其余严重度以`root_cause_group_id`为处理单元，默认走窄范围战术修复路径（步骤B1）。
2. 检查是否存在多个不同`root_cause_group_id`共享同一被违反的不变量/信任边界/控制归属方——这是比`root_cause_group_id`更高一层的聚类，聚类标准不能只按CWE/严重度/目录/标题（Codex `propose-security-hardening/SKILL.md`聚类标准原文逐字："按被违反的不变量/信任边界/控制归属方/危险能力/状态转移/重复出现的防护控制聚类，不能只按CWE/严重度/目录/标题聚类"）。**注意区分两个不同粒度，避免混淆（2026-08-08集成测试后补充）**：`root_cause_group_id`本身是#3候选发现阶段"组内多个独立可达实例共享同一根因"这个粒度（如CAND-002a/b/c/d同属一个`root_cause_group_id`，因为根因都是"缺失同一种授权检查"）；本步骤要找的是**更高一层、跨越多个不同`root_cause_group_id`**的架构弱点聚类（如"缺失授权检查"这个组跟"CSRF中间件被禁用"这个完全不同的组，共享同一个"状态变更端点缺乏统一防护层"这个架构弱点）——不要把"同一组内有多个实例"误判成"多个组共享控制"，两者是不同层级的概念。
3. **B1与B2不是互斥的二选一分支，是可以并行的两条独立轨道（2026-08-08集成测试后修订，此前表述容易被误读为二选一，导致本来可以立即打补丁的候选因为"顺带被纳入了架构聚类讨论"而被不必要地拖入"需人工决策"）**：若某个`root_cause_group_id`被纳入B2架构弱点聚类的讨论范围，**不代表**它自动失去走B1窄范围战术修复的资格——只要该`root_cause_group_id`本身有清晰、独立、不依赖架构决策的窄修复方案（如补齐一个装饰器调用），就应该同时产出B1的窄修复内容+推进步骤C/D给出该窄修复自己的`final_result`，与B2的架构提案分开呈现、分开决策。B2架构提案的"需人工决策"状态，只约束"是否采纳更大范围的架构性改动"这一个决策本身，不应该连带把已经可以独立拍板的窄修复也一起悬置。
4. 若聚类看起来"值得做"但实际论据不足（如仅是巧合命中同一CWE或同一目录，而非真正共享控制/不变量/信任边界），在相关B1 `tactical_patch`记录中填写`hardening_cluster_basis.structural_hardening_recommended=false`与依据，回退到逐个窄范围战术修复；该标记只是B2评估结论，不是第三种`remediation_mode`，不生成提案内容或独立结果记录。

### B1. 窄范围战术修复

1. 对该`root_cause_group_id`下的每个已确认漏洞（含组内全部独立可达实例，不只是被报告的那一个），**按semantic、vuln pattern、不变量、生态和版本匹配**`knowledge/fix-patterns/`目录中的模式驱动修复模式：
   - **semantic匹配**：按候选的`unified_semantic_refs`（UVS-\*）匹配fix-pattern的反向引用（漏洞模式反向引用指向哪个UVS）。
   - **vuln pattern匹配**：按候选的`vuln_pattern_refs`匹配fix-pattern的漏洞模式反向引用。
   - **不变量匹配**：按候选违反的安全不变量匹配fix-pattern的"需要恢复的安全不变量"。
   - **生态匹配**：按候选的`ecosystem_mapping_refs`匹配fix-pattern的生态映射引用，选择框架特定修复写法。
   - **版本匹配**：按目标检测到的语言/框架版本匹配fix-pattern的版本兼容性，排除不兼容的修复方案。
   匹配结果写入`fix_pattern_ref`，同时输出生态映射引用和攻击回归引用（修复后应重跑的attack-pattern PoC）。分类粒度待#15确定，本文件不预先假设条目路径。
2. 生成补丁内容，须同时满足硬性约束第1/2条列出的优先级顺序（六项，不可逆序牺牲），补丁改动范围限制在该根因组必要范围内，不扩大改动。
3. 按硬性约束第7条标注该补丁内容的证据标签（Observed/Inferred/Proposed）。

### B2. 架构性加固提案

1. 汇总被聚类的多个`root_cause_group_id`，按"被违反的不变量/信任边界/控制归属方"整理出共同的架构弱点描述。
2. 聚类成立时写`hardening_cluster_basis.structural_hardening_recommended=true`，并提出一次性修复根因的架构级方案，按`candidate-finding.md`既有`proposal_content`字段呈现`description`、`options`与`tradeoffs`，不强行替用户在产品策略/兼容性取舍上拍板；#8只通过`structural_hardening_link`投影实际产物链接。
3. 按硬性约束第7条标注该提案内容的证据标签；提案中未经实际验证的建议性内容一律标注Proposed，不得包装成Observed。

### C. 修复验证（对B1/B2产出的、已落地为补丁的内容执行；纯提案性内容因尚未落地，不适用本步骤，直接进入步骤E的"需人工决策"）

1. 读取#6的`evidence_composition`和`evidence_segments`：含`evidence_mode=executed`段时在修复后真实重跑该段PoC；全部段为`inferred`时仅对修复后代码重走同一静态证据链，不得使用“执行”“重跑”措辞。
2. 对整个`root_cause_group_id`逐实例核查；未堵住或静态证据不足的实例须显式记录，不得默认视为一起修好。
3. 在`fix_verification_result.verification_mode`记录`executed`或`inferred`。动态或静态验证受阻、静态链路证据不足时，结果必须为`inconclusive`并进入`needs_human_decision`，不得视为通过。

### D. 独立对抗复核（针对修复本身，检查对象是修复后的代码，不是原漏洞）

1. 指派独立复核角色，不依赖提出补丁时的原始修复理由，重新读一遍该finding与该patch的最终diff。
2. 追踪该改动影响到的所有分支，检查是否存在等价危险sink未被同一补丁覆盖。
3. 尝试构造另一类恶意输入，检查该patch是否仍能被绕过。
4. 复核结论与生成补丁角色的判断不一致时，进入分歧仲裁：复用verification-and-rating已确立的"取最保守状态"合成规则——任何未化解的分歧一律不允许判定为"已修复"，须降级为"需人工决策"。

### E. 汇总最终结果

1. 结合步骤C验证结果与步骤D复核结论，锁定B1窄修复的机器结果。`fixed`还要求`patch_application.applied=true`，明确`target_kind`、不同的`before_revision`/`after_revision`、`artifact_ref`、`applied_at`、`authorization_ref`、`verification_revision_ref`，且全组复验和独立绕过复核均绑定同一`after_revision`并通过：
   - `final_result=fixed`：必须先有非空`patch_application`证明补丁已应用，再由全组真实动态复验通过；或`verification_mode=inferred`下由独立复核确认应用后静态证据链已断且未发现等价绕过路径。只有建议diff、没有应用revision/artifact/time/authorization证据时不得写fixed。静态路径进入#9时初始状态只能是`fixed_unverified`，后续真实动态复验后才能转为`fixed_verified`。
   - `final_result=needs_human_decision`：存在产品策略或兼容性取舍，或步骤C/D未通过、未收敛。
   - 若发现现状可能本来安全，先写`needs_human_decision`并按约束9回退#4；不得在#7单方写`inherently_safe`。
   - **（2026-08-08修订）该`root_cause_group_id`是否同时被纳入某个B2架构弱点聚类，不影响以上判定**——B2架构提案本身的采纳与否是一个独立的、只针对"架构性改动"这一个决策的"需人工决策"状态，跟本条B1窄修复的`final_result`分开记录，不合并、不互相拖累。
2. 若存在B2架构性加固提案，该结构提案记录自身必须写`final_result=needs_human_decision`，并呈现选项与权衡；不得另造“架构提案待决策”机器状态。
3. 汇总产出，写入下方"输出"字段表。

## 输出

> 按`candidate-finding.md`的#7字段段输出，并在产物顶层携带`stage_result`、`version`、`resume_context`。

| 字段 | 说明 |
|---|---|
| stage_result / version / resume_context | 阶段状态、契约语义版本与断点续跑上下文 |
| remediation_scope_id | 本次修复指导的处理单元标识：窄范围战术修复对应单个`root_cause_group_id`；架构性加固提案对应被聚类的多个`root_cause_group_id`集合 |
| remediation_mode | 允许值见枚举注册表 [`remediation_mode`](../../contracts/enum-registry.md#remediation_mode)；B1与B2可并行形成不同记录，不得改成互斥流程 |
| fix_pattern_ref | 仅窄范围战术修复填写：命中的`knowledge/fix-patterns/`知识库条目引用；具体分类粒度待#15确定 |
| hardening_cluster_basis | 执行B2评估时填写：`structural_hardening_recommended=true`表示聚类成立并产出结构提案；false作为相关B1 `tactical_patch`记录的伴随标记说明聚类依据不足，不生成`proposal_content`或独立`final_result` |
| priority_order_trace | 六项优先级顺序（分类正确性→安全边界堵住→合法行为保留→现有检查通过→代码惯例→改动范围最小）逐项核对记录，证明未逆序牺牲 |
| patch_content / proposal_content | 窄范围修复的补丁diff内容，或按契约结构记录的架构性加固提案`description`+`options`+`tradeoffs`；#8只投影摘要与实际产物链接 |
| evidence_tag | 该条修复内容/提案的证据标签见枚举注册表 [`evidence_tag`](../../contracts/enum-registry.md#evidence_tag)（复用#11溯源纪律） |
| fix_verification_result | 必含`verification_mode`。`executed`记录修复后PoC真实重跑；`inferred`记录修复后同一静态证据链走查，禁止表述为执行。逐实例使用契约结果值；证据不足时为`inconclusive` |
| bypass_review_result | 独立对抗复核结论：是否发现等价绕过路径；复核角色与生成补丁角色隔离的记录；分歧仲裁记录（若发生） |
| patch_application | `final_result=fixed`前置证据：applied=true、target_kind、不同的before/after revision、artifact、时间、本次授权及绑定after revision的验证引用 |
| final_result | 每条修复记录必填，允许值见枚举注册表 [`final_result`](../../contracts/enum-registry.md#final_result)；未获人工决策的结构提案写`needs_human_decision`；`inherently_safe`仅可在回退#4改判`refuted`后作为历史投影记录 |

**零发现兜底**：若无输入，输出stage envelope的`input_count=0`、`records=[]`和非空`zero_input_reason`，不得虚构`remediation_scope_id`。代码卫生记录由#8直接投影，`unconfirmed`/`refuted`候选不生成漏洞修复指导。

**需人工决策的兜底**：任何归入"需人工决策"的条目，不得只给结论不给依据，必须完整保留步骤A-D的中间产出（`priority_order_trace`/`hardening_cluster_basis`/`fix_verification_result`/`bypass_review_result`等），供人工在拥有完整证据链的情况下做取舍，不允许因为"反正要交给人"就省略前序步骤的记录。

## 阶段Gate

- Gate-1核对每个主动修复根因组有战术修复记录或明确不修理由；所有实例均进入验证结果；结构提案与窄修复双轨结果不得互相覆盖。
- Gate-2在补丁实际落地、高风险修复或高绕过风险时，由独立角色检查原攻击链是否切断、等价Sink、合法行为、生成者自我认证和验证模式真实性。
- 独立复核失败且宿主接管时必须写`independence_degraded`，不能据此产出`fixed_verified`或完全通过。

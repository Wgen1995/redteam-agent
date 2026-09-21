# TanYin 探隐 × 方案 B′ 融合裁决分析

**日期**：2026-09-20 · **性质**：架构评审裁决书（综合设计 v2 的前置输入，供用户评审）
**裁决对象**：
- **TanYin 探隐**：另一电脑演化出的纯 SKILL 渗透总控设计（五层架构 / 12 表 TSV 账本 / 九个 Phase 门 / 引擎契约 / 知识飞轮 / 黄金夹具；五专家审计 A1-A20+B1-B17 已落入）。证据：`.research/tanyin/A-core-design.json`（下称 **A**）与 `.research/tanyin/B-principles-panorama.json`（下称 **B**）。
- **方案 B′**：本仓库调研收敛的 12 条 must-haves + 组件决策。证据：`docs/research/2026-09-19-ai-pentest-landscape.md` §7（下称 **landscape**）、`docs/research/2026-09-20-pain-points-and-adoptability.md`（下称 **pain**）。
- **外部基准**：`.research/dive/tsecbench-q2-2026.json`（下称 **TSecBench**，腾讯云鼎 2026Q2，13 Agent×4 模型×63 题）。

**裁决原则**：①每个裁决必须带出处（JSON 键路径 / 报告章节 / 基准数据）；②诚实裁决——对方已有的机制不得重复发明，本分析逐一核实而非想当然；③冲突不回避，用外部证据裁决而非和稀泥。

---

## 0 结论速览：融合设计的十大裁决一页表

| # | 裁决点 | 裁决 | 一句话理由（证据） |
|---|---|---|---|
| 1 | 总体形态 | **同路合流**：skill 主体 + 单一薄 CLI 工具箱 + 按宿主档位启用 hook/egress | 双方独立选了同一条路（A.`architecture.keyDecisions`决策1 纯 SKILL × pain P4.1 路线 D「coding-CLI harness 上的 agent+skill」；TSecBench：Claude Code 零渗透代码排 5/13、多阶段 41.1% 第二）。TanYin 的账本命令本就是 PowerShell 代码，「零代码」实指零运行时依赖——宪法重述而非推翻 |
| 2 | 状态账本 | **TSV 12 表保留为领域账本**；journal 职能并入 timeline.tsv；嵌套复杂度走「TSV 索引行 + 外置文件」双轨 | A.决策6 四条论证成立（换 JSONL 不解决状态机/并发两病灶）；B′ 选 jsonl 的动因（宿主中立/append-only/可 diff，pain P4.3 状态存储行）TSV 全部满足；E-index 外置模式（A.`evidence.eIndex`）已是嵌套字段先例 |
| 3 | 阶段门 | **phases.yaml 数据化状态机承载 TanYin 九门语义**；执法权威仍在账本命令 | TanYin 门禁已可判定（A.`orchestration.phaseGates` 每门出口=账本命令）但散在 markdown；B′ expert/architect #1「phases.yaml 单一事实源+回边」（landscape §7.2 ①）补上声明层——形式归 B′，语义归 TanYin |
| 4 | scope 执法 | **四层纵深**（账本级→执行通道级→宿主 hook→egress 代理）+ canary 进 evals；**TanYin「不做守卫脚本」D 决议推翻** | TanYin 诚实边界自认「事前可拒收≠事前不可绕过」（A.决策7）；B′ 有实测反例：Threatswarm fail-open+`$TARGET` 绕过（landscape §1 最高风险共识）+ expert/ai-agent #3「最弱后端决定安全水位，法律级风险」 |
| 5 | 凭据治理 | **`{{vault:cred-N}}` 为唯一占位符语法**，叠加 B′ 全链路四关卡（回注/掩码/tokenize/终检）+ DarkMoon「降级不拒绝」 | 同一物异名（A.`evidence.credentialVault` A10 × landscape §6.4）；B′ 链路更全（pain P2.8 DarkMoon privacy 三件套：仅执行点还原+输出兜底重 tokenize） |
| 6 | 预算 | **三元组树化**（goal 为根、intent 预算份额为叶）+ 可选 `$` 第四维 + B′ 假设排序公式并入先验分（命令计算） | TanYin 六要素已含预算份额（B.`agent_protocols.commander_protocol`）；TSecBench token_variance：同基准 30 倍差距（CHYing 27.92M vs Cairn 458.50M）——预算与编排精简度=钱的定量证据 |
| 7 | 证据契约 | **E-index 契约扩展 POC 四要素 + P4 新增独立重放门（三态）**；findings 表吸收 auth_context / exploitation_status | TanYin 差分举证方法论保留（A.`evidence.differentialEvidence` A12）；B′ 重放门与四要素是 TanYin 核实确认缺的（expert/pentest #2「复现四要素只是口号」级缺口） |
| 8 | 验收体系 | **三层**：黄金夹具（命令回归）→ evals 指标集（交战级，CI 门禁化）→ TSecBench 六能力域对齐（外部） | TanYin 夹具+纪律注入测试+种 20 漏洞（A.`qualityAcceptance`）× B′ 指标集 canary 零容忍/kill-9 保真度/复放率（pain P4.3 评测行）——互补不重叠 |
| 9 | 身份矩阵 | **B′ 独有、必须吸收**：creds/sessions 一等实体 + 身份矩阵差分子流程，**复用 TanYin pair_group 差分机制落地** | TanYin 12 表无 creds/session（A.`ledger.tables` 逐一核实）；expert/pentest #1（severity high）：全行业空白、产出最高洞类（pain P1.2.2） |
| 10 | 平台载体 | **账本命令从 PowerShell 5.1 迁移为跨平台薄 CLI**（python3 标准库，tools.lock 锁定）；「LLM 只调用不实现」纪律不变 | PS 5.1 是 Windows 基底（A.`skillOrganization.howZeroCodeWorks`），与 B′ 三后端（macOS/Linux，pain P4.3）冲突；A.`openItems` 自认 PS 5.1 性能边界是探知项——迁移同时消掉该探知项 |

> 十大裁决的完整论证与证据见 §2-§4；深层冲突消解见 §5；v2 蓝图与拍板点见 §6。本文档只做融合裁决、不替代任何一侧的设计文档——最终实现以用户批准的 v2 定稿为准。

---

## 1 概念对齐表：TanYin 概念 ↔ B′ must-have 逐条对照

三分类：**【同】**同一物异名（统一口径即可）／**【叠】**部分重叠（同目标不同机制或不同深度，需裁决）／**【独】**独有（经对方材料核实确认没有）。出处缩写：A./B. = 两份 TanYin JSON 键路径；L§ = landscape 章节；P§ = pain 章节；T = TSecBench。

### 1.1 同一物异名【同】——统一口径，不得重复发明

| TanYin 概念 | B′ 对应物 | 统一口径 | 出处 |
|---|---|---|---|
| `{{vault:cred-N}}` 占位符 + vault/ 加密保险库 | `{{CRED:id}}` 占位符（POC 卡片 raw_request） | `{{vault:cred-N}}`（语法更明确指向保险库） | A.`evidence.credentialVault`(A10)；L§6.4、P§P1.4.3 |
| control_evidence_ids + pair_group 差分组 | findings.counterevidence 字段（源自 Strix） | control_evidence_ids + pair_group（字段+方法论一体） | A.`ledger.tables`[findings]；L§4 Strix 行 |
| state.md + 统一恢复协议（读盘重建） | handoff ≤200 行 + resume_kit 恢复注入白名单 | state.md 兼任 handoff，加 ≤200 行硬上限与白名单语义 | A.`contextLifecycle`(A19)；L§7.2 ③、expert/ai-agent #1 |
| SKILL.md 常驻集（<2K token）+ phases/ 渐进加载 | SKILL.md 路由器化+不变式，流程外迁 | 同一机制：常驻最小化+按需加载 | A.`skillOrganization.loadingStrategy`；L§7.1 首行 |
| assets.tsv / facts.tsv 资产-事实中间层 | assets.jsonl / hypotheses.jsonl（ARL 资产模型+Caldera facts） | 表实体统一（载体之争归裁决 R1） | A.`ledger.tables`；L§7.1 |
| intents.dedup_key（资产+技法类，命令计算） | findings.dedup_key（must-have ⑧） | dedup_key 命令计算、LLM 只提议不判重 | A.`ledger.stateMachineSemantics`；L§7.2 ⑧ |
| budget-exhausted 合法终态（中期报告+披露） | 预算树止损（HBPGPT Limits 每轮注入剩余预算） | budget-exhausted 保留为唯一预算终态语义 | A.`budget.legalTerminal`；P§P2.5 |

### 1.2 部分重叠【叠】——同目标不同机制/不同深度，逐项裁决见 §2

| # | TanYin 形态 | B′ 形态 | 重叠面 / 差异点 | 出处 |
|---|---|---|---|---|
| 1 | 12 表 TSV 账本：单写者+写前拒收+ID 铸造+事件溯源（intents/matrix）+timeline 链式哈希 | journal.jsonl 第一真相 + state.json 派生视图（revision 乐观锁+原子写）+台账族 | 同为交战状态契约；载体/写并发策略/防篡改不同 | A.`ledger`；P§P4.3 状态存储行 |
| 2 | 九个 Phase 门（P0-P6+P5.5+P6.0），门=账本命令，指令在 phases/*.md | phases.yaml 数据化状态机（阶段序列/entry/exit 断言/门禁点/回边） | 同为阶段纪律；声明形式与机器可裁决性不同 | A.`orchestration.phaseGates`；L§7.2 ① |
| 3 | 五态矩阵（x/?/-/!/空）+基线冻结+WSTG 词表钉死+「-」「!」P4 抽查 | coverage 负空间台账（Strix 四态+零覆盖最后警告）+coverage-gaps.jsonl 强制降级记录 | 同为覆盖可见性；TanYin 是驱动机制+防廉价闭合，B′ 是报告工件+静默降级防线 | A.`matrix`；P§P1.2.1 |
| 4 | 预算三元组（token;requests;hours）goal 级+intent 预算份额+熔断 | 预算树四维（轮次/token/美元/时长，父子切割）+per-phase 切分 | 同为预算控制；维度与树形不同 | A.`budget`；P§P1.5.3 |
| 5 | 假设风暴五路+先验分（确定性因子命令算+LLM 同分排序）+top-N 晋升 | 假设排序公式（期望严重度×置信÷预估成本） | 同为假设优先级；TanYin 防校准病纪律 vs B′ 成本感知 | A.`orchestration.hypothesisStorm`；P§P1.5.3 |
| 6 | deny-list 数据文件+账本级 scope 硬门+宿主权限规则（探知项 C3） | 三层执法（egress 代理 deny-by-default→宿主 hook fail-closed→scope-guard 脚本）+canary | 同为越界防线；TanYin 诚实边界三层 vs B′ 实测驱动的进程级三层 | A.`discipline`(A11/决策7)；L§1、P§P1.5.2 |
| 7 | 速率熔断：rate_limit+request-ticket 取票+429 指数退避+事故熔断三步 | execution_guard 有界执行（pre-flight 拒绝无界命令）+预算 requests 维度 | 同为防打挂目标/防失控；TanYin 限速、B′ 拒跑 | A.`discipline.rateAndCircuitBreaking`(A8)；P§P2.8 |
| 8 | 黄金夹具两层（确定性规范化比对+行为断言） | evals 门禁（金标精确率/召回率+POC 复放率+canary 零容忍+kill-9 保真度，CI 化） | 同为质量门；夹具=命令回归、evals=交战行为 | A.`qualityAcceptance`(A15)；P§P4.3 评测行 |
| 9 | timeline.tsv 链式哈希审计链（prev_hash+hash） | journal.jsonl append-only 第一真相（可全量重建） | 同为追加式事实流水；B′ 无哈希链、TanYin 无「全量重建派生视图」明文原则 | A.`ledger.tables`[timeline]；P§P4.3 |
| 10 | 受管重启三层（压缩容忍/受管重启/断电恢复）+自动档 spawn | 工件即缓存幂等续跑（pre_condition file_exists）+kill -9 续跑保真度 | 同为长跑存活；TanYin 管上下文生命周期、B′ 管任务跳过 | A.`contextLifecycle`；P§P2.7 |
| 11 | P6.0 清理门（timeline→checklist→逐项核销+清理声明） | cleanup+changes_ledger（每写操作登记 revert_cmd，报告前全 reverted 或人工豁免） | 同为收尾纪律；B′ 多 revert_cmd 登记与幂等验证 | A.`orchestration.phaseGates`[P6.0]；L§7.2 ⑫ |
| 12 | 命令双维度安全上下文（操作级别×视角 L0-L3，L3 一刀切只取证） | 检测/利用分界（CEP：recon 段剔除 dos/intrusive tag，真 payload 需批准） | 同为攻击性分级；TanYin 双维矩阵更细 | A.`discipline.commandSecurityContext`；L§4 CEP 行 |
| 13 | 授权门八问+scope.tsv（include/exclude matcher）+goals 结构化授权 | scope.yaml schema（双清单+accounts+permitted_actions+**oob_endpoints 申报**+append-only amendments） | 同为授权数据化；B′ 字段更全（accounts/OOB/修订审计 TanYin 无） | B.`security_discipline.authorization_eight_questions`；P§P1.5.2 |
| 14 | 两维正交评级 confidence(C1/C2/C3/➖🛑)×impact(高/中/低)+双列呈现 | findings.confidence 四级+报告「技术×业务风险分级」章节 | 同为分级；TanYin 正交纪律防范畴错误（审计修正 A6） | A.`severity`；L§7.2 ⑧ |
| 15 | 引擎契约双轴（manifest+提交文件+skill/cli/projector 执行语义）+工具两层接入 | 适配器契约（每工具调用模板/输出 schema/降级链）+nuclei adopt | 同为工具集成；TanYin 方法论级引擎、B′ 工具级适配器 | A.`engineContract.toolLayering`；L§7.1 |
| 16 | 知识飞轮（entities/concepts/precedents/patterns+四机制） | references/ 漏洞类分册（BugHunter hunt-* 骨架+语料） | 同为知识层；TanYin 有治理无语料、B′ 有语料无治理 | A.`knowledgeSystem`；L§7.1 references 行 |
| 17 | E-index 证据契约（repro_command/repro_kind/双哈希/只增不覆盖） | evidence[] 契约（path+sha256+kind 进 findings 行）+POC 四要素 | 同为证据结构化；四要素与重放门见 R6 | A.`evidence.contract`；P§P1.4.1/P1.4.3 |
| 18 | 双宿主安装自检 B14（能力探测+降级建议+smoke test） | 安装矩阵（单权威目录+符号链接四运行时）+tools.lock 供应链锁定 | 同为安装层；B′ 多版本锁定与验签（TanYin 无） | A.`skillOrganization.installSelfCheck`；P§P4.3 分发行 |
| 19 | 干跑+负向用例+纪律注入测试（双宿主各跑一轮） | 四层测试基线（绕过回归集+E2E 范围外=0+kill-resume） | 同为负向测试思想，指标化程度不同 | A.`qualityAcceptance.behavioral`；L§7.2 工程维护行 |
| 20 | 受管重启自动档 spawn（walcode run / claude -p） | Python driver 三后端 headless 编排 | 同为无人值守执行通道，粒度不同（单命令 vs 常驻层） | A.`contextLifecycle.threeLayerStrategy`；P§P4.3 |
| 21 | 范围外观察附录（out_of_scope 资产披露） | coverage-gaps.jsonl（未测/降级强制记录） | 同为诚实披露出口，对象不同（界外资产 vs 未测格） | B.`security_discipline.out_of_scope_appendix`；P§P1.2.1 |

### 1.3 独有【独】——经对方材料逐键核实确认缺

**TanYin 独有（B′ 两份调研报告核实无对应机制）**：

| TanYin 机制 | 核实结论 | 出处 |
|---|---|---|
| 图谱演进循环（P3 六步）+收敛四条件（无未消费 fact∧无 pending∧candidate 空∧矩阵无空格） | B′ 无「何时停」的数据判定（landscape §7.1 无循环/收敛组件） | A.`orchestration.evolutionLoop`；B.`p3_loop.convergence` |
| 假设风暴五路（实体页/技法页/先例/图邻接/LLM 联想）+条件触发+联想上限+阈值递增 | B′ 仅有排序公式，无生成机制与防震荡三重防线 | A.`orchestration.hypothesisStorm`(A5①③⑤/B1/B2) |
| 资产事件处理器（新资产→无条件自动测绘+子矩阵初始化） | B′ 无事件驱动再测绘 | A.`orchestration.assetEventHandler`；B.`p3_loop.asset_event_handler` |
| 矩阵基线冻结（覆盖率锚点）+WSTG v4.2 词表钉死版本化（防单源过拟合）+「-」「!」按比例抽查 | B′ coverage 无冻结/词表完备性/防廉价闭合博弈 | A.`matrix.rules`(A5⑥/A7) |
| 知识飞轮四机制（ingest staging 审批/反向验证/learned→core 四门槛/lint 保鲜 N≥2 反证差分降级）+客户三元组+CLIENT-NN | B′ 语料是静态文件，无任何知识治理 | A.`knowledgeSystem`(决策4)；B.`knowledge_flywheel` |
| 引擎契约三 kind（skill/cli/**projector**）+CLI 纪律能力声明（max_op_level+视角上限） | B′ 适配器无 projector 概念、无纪律能力声明路由 | A.`engineContract.executionSemantics` |
| CNPEN 82 漏洞实战语料+web-blackbox 四段方法论（侦察/攻击面测绘/矩阵测试/差分举证） | B′ 语料全部来自外部 MIT 项目，无私有实战验证语料 | A.`webBlackboxEngine`(methodologySource/cnpenMaterialMapping) |
| 上下文三层策略+受管重启自动档（spawn 新会话+护栏：计入预算/速率上限/单活跃会话） | B′ handoff 是一次性输出工件，无运行时重启机制 | A.`contextLifecycle.threeLayerStrategy`；B.`context_strategy.managed_restart_sequence` |
| 单写者模式+写前拒收+ID 原子铸造（一次解决并发锁/撞号/校验集中化） | B′ 用 revision 乐观锁防御，无单写者协议 | A.`ledger.singleWriter`/`idMinting`(A1)；B.`agent_protocols.single_writer` |
| timeline 链式哈希（改历史行即断链）+P0 落账 SKILL 版本哈希 | B′ journal 无防篡改 | A.`ledger.tables`[timeline](A14) |
| P5.5 签发门（人审+command_hash 绑定报告哈希，未签发禁止导出）+approvals 审批账本 | B′ 无报告签发与审批账本 | A.`orchestration.phaseGates`[P5.5](A20) |
| 事故熔断三步（停子代理+事故快照+通知紧急联系人） | B′ 无事故响应流程 | A.`discipline.rateAndCircuitBreaking`；B.`security_discipline` |
| 摘要纪律（查询输出摘要化/子代理定长返回/工具输出 0 进上下文）+常驻集系统级注入要求 | B′ 无系统的上下文进出纪律（Strix compaction 是会话内摘要） | A.`contextLifecycle.residentVsOnDemand`；B.`context_strategy.summary_discipline` |
| 召回率四层度量框架（矩阵/图谱/知识/靶场 ground truth） | B′ evals 有指标但无四层召回框架 | A.`matrix.recallFramework`；B.`knowledge_flywheel.recall_four_layers` |
| 四支柱工程哲学+12 条因果链+panorama 活文档治理 | B′ 有报告纪律但无设计因果治理体系 | A.`architecture.engineeringPhilosophies`；B.`twelve_causal_chains` |

**B′ 独有（TanYin 两份 JSON 逐键核实确认缺）**：

| B′ 机制 | TanYin 侧核实方式与结论 | 出处 |
|---|---|---|
| 身份矩阵差分：creds.yaml/sessions/角色实体+受保护端点×角色逐对差分重放 | 核对 A.`ledger.tables` 12 表与 B.`domain_model.eight_tables`：无 creds/session/role 表；findings 字段无 auth_context；八问⑧仅收集账号信息——**确认缺** | P§P1.2.2、expert/pentest #1（severity high，全行业空白） |
| POC 独立重放门（fresh 隔离会话盲重放，VERIFIED/REPAIRED/REJECTED 三态） | 核对 A.`qualityAcceptance`/`ledger.commands.validationCommands`：P4 仅 hash 重算+格式校验，无重放执行——**确认缺** | P§P1.4.3、expert/pentest #2；三态原型 dive/open-sploit |
| POC 四要素：网络位置声明/前置条件/matcher 判定器 | 核对 B.`domain_model.evidence_contract.fields`：有 repro_command/repro_kind，无 network_position/preconditions/expected.matcher——**确认缺三要素** | expert/pentest #2（「中文报告被质疑复现不了的第一大原因」） |
| 三层执法之 egress 代理+宿主 hook fail-closed+scope canary 探测器 | 核对 A.决策7+B.`security_discipline.honest_boundary`：明确「不引入守卫脚本/守护进程」（D 决议）——**显式拒绝而非遗漏**，裁决见 R7 | L§1 共识、P§P1.5.2（Threatswarm fail-open 实洞） |
| scope 的 oob_endpoints 申报（OOB 回连白名单） | 核对 A.`ledger.tables`[scope]：kind 仅 include/exclude——**确认缺** | expert/architect #3、expert/pentest #5 |
| scope 的 accounts+permitted_actions+append-only amendments 修订审计 | 核对 scope 表与 P0 流程：无账户级授权动作、无修订审计段（CEP ROE amendments 有）——**确认缺** | P§P1.5.2、dive/claude-externalpentest |
| tools.lock 供应链锁定+nuclei-templates 钉 commit+ECDSA 验签 | 核对 A.`skillOrganization`：工具箱经执行通道直调，无版本/哈希锁定——**确认缺** | expert/devops #3、P§P3.3 供应链风险行 |
| 交战区移出 skill 树（session 目录与安装目录分离） | 核对 A.`skillOrganization.directoryStructure`：session/<goal-id>/ 在 skill 根内——**确认缺**（git pull/升级冲突风险） | expert/devops #1 |
| Python driver 三后端 headless 编排（dsh headless/opencode run/codex exec） | 核对 TanYin：受管重启自动档 spawn 单命令最近似，但无统一无人值守/CI 编排层——**确认缺** | P§P4.3、L§7.1 Python driver 行 |
| 工件即缓存幂等续跑（pre_condition file_exists 跳过已完成步骤） | 核对 TanYin：artifacts/submissions 只增不覆盖（是恢复点），但无「已完成即跳过」语义——**确认缺** | P§P2.7 Osmedeus reusable#2 |
| CVE 联网核验纪律（强制 WebSearch 对照 PSIRT/NVD/CISA KEV，不信任训练数据） | 核对 knowledgeSystem：实体页保鲜靠本地 last_verified+lint，无联网核验流程——**确认缺** | P§P1.3.3、dive/claude-externalpentest reusable#6 |
| 报告确定性重建（服务端聚合器从 findings 存储生成正文，LLM 只写执行摘要）+中文合规章节骨架（等保占位） | 核对 A.`orchestration.phaseGates`[P5]：报告由总控（LLM）撰写（数据出自账本但正文是 LLM 长文），章节无授权声明/方法学映射/覆盖度局限性/等保占位——**确认缺** | P§P1.4.2、dive/darkmoon「DEFINITIVE FIX」、scan/standards |
| MCP 工具总线复用（playwright/burp/msgrpc MCP 封装） | 核对 TanYin：工具经宿主 shell 执行通道调用，无 MCP 集成位——**确认缺**（非必选，见 §6.5） | P§P4.2 论据 2 |

---

## 2 逐项裁决：双方都有的机制——选谁/怎么合

### R1 状态账本：TSV 12 表 vs journal.jsonl（含单写者与事件溯源对比）

- **TanYin 形态**：12 表 TSV（UTF-8 无 BOM+LF，全表带 schema_version），单写者（总控串行落账），写前拒收，ID 原子铸造，intents/matrix 事件溯源（追加行+取最新命令），timeline 链式哈希（A.`ledger`）。
- **B′ 形态**：journal.jsonl append-only 第一真相 + state.json 派生视图（revision 乐观锁+temp/rename 原子写）+ assets/hypotheses/coverage/findings 台账族（P§P4.3）。
- **裁决**：**保留 TanYin TSV 12 表为领域账本与唯一写入口；不引入独立 journal 文件——timeline.tsv 升格承担 journal 职能（第一事实源+可全量重建）；嵌套复杂字段（POC 卡片、evidence 数组）走「TSV 索引行+外置文件」双轨（E-index+evidence/EV-*.md 已是先例）。吸收 B′ 三点：①「journal 可全量重建派生视图」明文为原则（TanYin 事件溯源已具备，补state.md 由账本重建的校验命令）；②state 写入采用 temp/rename 原子写+revision 号（防 kill -9 半写，兜底单写者协议）；③findings 契约字段（见 R6）并入 findings.tsv 列与外置卡片。**
- **理由**：A.决策6 已论证换 JSONL 不解决真正病灶（状态机语义与并发写是格式无关的）；B′ 选 jsonl 的三大动因——跨宿主可读可 diff、append-only、无服务依赖（P§P4.3）——TSV 全部满足；双格式=双解析栈成本（决策6 第③条）。事件溯源对比：TanYin 的选择性事件溯源（仅状态机表追加+命令取最新）比 B′ 全事件 journal 更省——B′ 需要全量 journal 恰因其无「取最新」命令层；单写者 vs 乐观锁：单写者从协议上根除并发（B.`agent_protocols.single_writer`「一次解决并发锁/ID 撞号/校验集中化三问题」），乐观锁降级为引入 driver 后的兜底检查（见 5.1）。
- **证据**：A.`architecture.keyDecisions`[决策6]、A.`ledger.stateMachineSemantics`(A3)；P§P4.3 状态存储行、L§7.2 ④、expert/ai-agent #2。

### R2 九个 Phase 门 vs phases.yaml 状态机

- **TanYin 形态**：P0-P6+P5.5+P6.0 共九门，每门入口门+出口门禁，门禁=账本命令判定（P0 无授权 REJECT / P2 matrix-freeze / P3 converge-check / P4 四校验命令 / P5 终态门禁），指令在 phases/*.md 渐进加载（A.`orchestration.phaseGates`）。
- **B′ 形态**：phases.yaml 数据化状态机——阶段序列/entry/exit 断言/门禁点/回边，单一事实源（L§7.2 ①；expert/architect #1；先例 Caldera facts 闭环+回边、Osmedeus DAG、CEP 六阶段）。
- **裁决**：**双层合体：phases.yaml 为状态机单一事实源（数据），TanYin 九门语义全部数据化进去——每门 exit 断言=一条账本查询命令的调用（如 P3 出口=`ledger-converge-check ∈ {converged, budget-exhausted}`）；phases/*.md 保留为人读方法论指令，由状态机按当前阶段调度加载。回边显式化：budget-exhausted→P4 降级流（TanYin S29 分支已有）、新资产→子矩阵（事件回边）、cred-obtained → authz-diff 候选（凭据事件回边）。执法权威不搬家：仍在一、R7 的执行层，yaml 只是可 diff 的声明层。**
- **理由**：TanYin 的门禁语义已可判定（每门出口均对应命令），但散在 markdown 里机器不可枚举——B′ 恰好补此层；B′ 无九门的业务语义深度（P5.5 签发/P6.0 清理/八问授权均为 TanYin 独有深度）。
- **证据**：A.`orchestration.phaseGates`（design §4.1）；B.`phase_gates`；L§7.2 ①、P§P1.3.3（方法学数据化）。

### R3 {{vault:cred-N}} 保险库 vs 凭据占位符网关

- **TanYin 形态**：vault/ 加密文件+账本/报告/Evidence 只引用占位符+facts 落账即脱敏+运行时数据分级+交付附一次性解密通道（A.`evidence.credentialVault` A10；B.`security_discipline.four_levels`[L2]）。
- **B′ 形态**：占位符网关全链路四关卡——执行前回注、落盘前掩码、LLM 上下文前 tokenize、交付前终检（L§6.4；模式抄 DarkMoon：仅执行点还原+输出兜底重 tokenize+「降级不拒绝」 withheld 策略，P§P2.8）。
- **裁决**：**`{{vault:cred-N}}` 为唯一占位符语法；四关卡机械化并入：①执行前回注=子代理经执行通道在执行点取真值（TanYin 引擎执行协议已有此位）；②落盘前掩码=写前拒收扩展 redact 校验（`ledger-add-fact` 落账即脱敏已有，扩展到 submission/artifacts 摘要行）；③上下文前 tokenize=凭据永不进总控（子代理隔离已保证，补「摘要行过 redact 后才可回读」）；④交付前终检=报告导出前对全文做占位符扫描（新增命令）。吸收 DarkMoon 输出兜底重 tokenize 与 withheld 降级策略；一次性解密通道保留。**
- **理由**：同一物异名，B′ 链路覆盖更全且有机码级参照（DarkMoon 三件套虽 GPL 不可搬码、模式清洁实现）；TanYin 的保险库+解密通道是 B′ 没有的交付侧设计——互补拼成全链路。
- **证据**：A.`evidence.credentialVault`(A10)、B.`domain_model.directories`[vault]；L§6.4、P§P1.4.3、P§P2.8。

### R4 budget.tsv 三元组 vs 预算树

- **TanYin 形态**：goal 落账三元组 token;requests;hours+budget.tsv 流水+intent 委派带预算份额+ledger-budget-check 每轮检查+测绘 intents 不豁免+熔断（A.`budget`；B.`p3_loop.budget_exhausted`）。
- **B′ 形态**：HBPGPT Limits 四维预算树（轮次/token/美元/时长，父子切割 sub_limit）+per-phase 切分+每轮剩余预算注入提示（P§P1.5.3、P§P2.5）。
- **裁决**：**三元组保留为根并树化：goal（根）→intent 预算份额（叶）已是树形，显式化父子限额语义；增加可选第四维 $（LLM 成本，默认关闭）；B′ 假设排序公式并入先验分：先验分 = 确定性因子 ×（期望 impact 枚举值）÷ 预估成本——全部由命令计算，保持「LLM 不做绝对打分」纪律（校准病防线不破）；budget-exhausted 合法终态+首节强制披露不变。**
- **理由**：requests/hours 是渗透特有维度（防打挂目标/防授权过期，B.`p3_loop.budget_exhausted`），B′ 树形+成本感知是 TanYin 缺的结构；TSecBench token_variance（CHYing 27.92M 均值 vs Cairn 458.50M，30 倍差距；CHYing 15.78M 拿 85.14%）证明编排精简度直接换算成本——$ 维与 token 效率指标必须进 evals。
- **证据**：A.`budget`(A5)、B.`e2e_execution_flow`[S6 预算份额]；P§P1.5.3、P§P2.5；T.`headline.token_variance`。

### R5 黄金夹具 vs evals 门禁

- **TanYin 形态**：两层黄金夹具（确定性规范化比对：剥时间戳/ID 重映射/行排序稳定化→字节级；行为结构断言）+纪律注入测试+负向用例+干跑+授权靶场含 budget-exhausted 演练+种 20 漏洞测检出率（B16）+双宿主自检+ingest 抽查（A.`qualityAcceptance`；B.`verification_and_governance`）。
- **B′ 形态**：evals/ 自建——docker-compose 固定靶场+金标 ground-truth+指标集（精确率/召回率、POC 机器复放率、scope canary 零容忍、kill -9 续跑保真度、报告 schema lint+脱敏检查），**改动门禁化**（CI），退出码对齐 Strix 0/1/2（P§P4.3 评测行；expert/ai-agent #4「改一段提示词可能悄悄破坏门禁」）。
- **裁决**：**合并为三层验收体系并全部 CI 门禁化：L1 黄金夹具=账本命令确定性回归（TanYin 规范化比对方法保留，是 B′ 没有的命令层回归）；L2 交战级 evals=B′ 指标集 ∪ TanYin 行为项（纪律注入测试/负向用例/干跑/budget-exhausted 演练/种 20 漏洞全部并入 L2，检出率即金标召回）；L3 外部基准=TSecBench 六能力域对齐（多阶段渗透为主指标）。出卡质量门写成 Phase exit 断言（expert/architect #6）挂进 phases.yaml。**
- **理由**：TanYin 夹具深在「命令层确定性」，B′ evals 深在「交战行为与门禁化」——零重叠冲突、纯互补；TanYin 验证批未含 canary/kill-9/复放率三项 B′ 硬指标，必须补。
- **证据**：A.`qualityAcceptance`(A15/B16)；B.`verification_and_governance.mechanisms`；L§7.2 ⑪、P§P4.3、T.`implications_for_our_work`[6]。

### R6 证据契约（E-index/差分举证）vs POC 重放门+findings 字段

- **TanYin 形态**：E-index.tsv 证据单一来源；字段含 repro_command（占位符化）/repro_kind(single/sequence/concurrent)/content_hash 双轨(raw+norm)/artifact_path 只增不覆盖/pair_group/raw_excerpt；差分举证=对照组设计+基线±单变量+errorCode 语义分析（判定规则写入引擎契约）；findings 强制 reproducible_steps≥1+两维评级+control_evidence_ids；P4 做 hash 重算+引用闭合（A.`evidence`）。
- **B′ 形态**：POC 卡片硬契约四要素（env.network_position/preconditions/raw_request/expected.matcher/cleanup）+独立重放验证门（fresh 会话盲重放复现 expected 才 VERIFIED，否则 REPAIRED/REJECTED 循环）；findings schema 定稿字段 dedup_key/scope_check/exploitation_status/confidence 四级/auth_context/counterevidence（L§7.2 ⑥⑧）。
- **裁决**：**E-index 为证据单一来源保留；契约扩展四要素字段（network_position/preconditions/expected.matcher——matcher schema 以 nuclei matcher/extractor 为范本；cleanup 并入 R9 的 revert 登记）；P4 新增独立重放门：fresh 隔离子代理只拿卡片盲重放→VERIFIED 才维持 C1，REPAIRED 复查，REJECTED 降 C3 或转 fact（三态原型 open-sploit）；findings.tsv 吸收 auth_context（身份矩阵产物，R9）与 exploitation_status（verified/suspected/ruled_out，Strix 三态）；counterevidence≡control_evidence_ids 统一为后者；差分举证 pair_group 方法论保留并升格为身份矩阵差分的执行机制。**
- **理由**：TanYin 证据链强在「防篡改+归因严谨」（差分对照组区分「已修复」vs「被 WAF 拦」），弱在「复现是声明不是验证」（P4 只重算哈希不执行重放）；B′ 恰好相反。expert/pentest #2 判语「四件套宣称可复制粘贴复现，但设计里这只是口号」对 TanYin 同样成立——必须吸收。
- **证据**：A.`evidence.contract`/`differentialEvidence`(A12/B5/B12)；B.`domain_model.evidence_contract`；P§P1.4.3、L§7.2 ⑥⑧、dive/nuclei（matcher schema）、dive/open-sploit（三态门）。

### R7 scope 执法：TanYin 三层诚实边界 vs B′ 三层执法（最深的哲学冲突）

- **TanYin 形态**：账本级硬门（scope-check 内联资产落账、界外禁止派生 intent、写前拒收、deny-list 前置）+prompt 级约束+宿主权限规则（探知项 C3）；**明确不引入守卫脚本/守护进程**（A.决策7；D 决议「守卫脚本不做」；B.`security_discipline.honest_boundary`）。
- **B′ 形态**：三层执法 fail-closed——egress 代理 deny-by-default（scope.yaml 编译为 ACL+DNS pinning+OOB 白名单+工具基础设施白名单）→宿主 hook 适配（Threatswarm exit-2 语义修补版）→scope-guard 脚本兜底；三后端 canary 证等强（L§1 共识、P§P1.5.2）。
- **裁决**：**四层纵深，按宿主能力分档启用：L-账本（常量，任何宿主都有）→L-执行通道（deny-list+scope-guard 脚本，随薄 CLI 工具箱分发）→L-宿主 hook（fail-closed，DSH/opencode/codex/Claude Code 有 hook 机制时强制启用）→L-egress 代理（最高档，可选但推荐）。档位由安装自检（B14 扩展）探测并写入报告的守门声明（诚实边界表述从三层改为四层+档位事实）。canary 越界探测器部署进 evals（零容忍）。scope.tsv 吸收 B′ schema：accounts+permitted_actions、oob_endpoints 申报、append-only amendments 修订审计。TanYin D 决议（不做守卫）正式推翻。**
- **理由**：TanYin 自己承认账本级硬门是「事后可审计+事前可拒收，不是事前不可绕过」（A.决策7 honestBoundary），而子代理直连界外目标的路径（不经账本直接 curl）只有进程级执法能拦；B′ 有实测反例背书：Threatswarm fail-open+`$TARGET` 绕过+白名单外工具跳检（P§P1.5.2）、prompt 级已被反复证伪（L§1）；expert/ai-agent #3「最弱后端决定整体安全水位，对一人红队这是法律级风险」。TanYin 的零代码宪法让位于分档增强——宪法重述见 5.1。
- **证据**：A.`discipline`(A11/决策7)、A.`program_status_and_audit`…（D 决议见 B.`program_status_and_audit.five_expert_audit.decisions`）；L§1、P§P1.5.2、P§P3.2②。

### R8 断点/恢复：受管重启三层 vs 工件缓存续跑+kill-9 保真度

- **裁决**：**TanYin 三层策略（压缩容忍/受管重启/断电恢复）为主干——B′ 无运行时上下文管理机制；吸收 B′ 两点：①state.md 兼任 handoff，加 ≤200 行硬上限+resume_kit 恢复注入白名单语义（expert/ai-agent #1）；②工件即缓存幂等续跑——intent 完成且产物存在（submissions/<intent-id>/submission.json）则重入时跳过（Osmedeus pre_condition 模式），kill -9 续跑保真度进 evals。**
- **理由**：TanYin 把「断电恢复是受管重启的特例」的统一协议（B.`context_strategy`）是更完整的机制；B′ 的跳过语义解决的是「重复消耗」而非「状态丢失」——正交互补。
- **证据**：A.`contextLifecycle`(A19)；P§P2.7、L§7.2 ③④、P§P4.3 评测行。

### R9 清理：P6.0 清理门 vs cleanup+changes_ledger

- **裁决**：**P6.0 清理门保留为流程权威（timeline→checklist→核销+清理声明是 B′ 没有的报告级设计）；吸收 changes_ledger：所有写操作命令强制登记 revert_cmd（timeline 事件扩展字段），核销=执行 revert_cmd+结果验证（吸收 Caldera cleanup 逆序+「不保证幂等不验恢复」的反例教训，P§P1.5.3）；报告前全部 reverted 或人工签字豁免（expert/architect #7）。**
- **证据**：A.`orchestration.phaseGates`[P6.0](A13)、A.`ledger.commands`[ledger-cleanup-checklist]；L§7.2 ⑫、P§P1.5.3、scan/adversary gaps。

### R10 报告生成：总控 LLM 撰写 vs 服务端确定性重建

- **TanYin 形态**：P5 由总控（LLM）生成报告——执行摘要/漏洞清单（confidence×impact 双列）/矩阵覆盖视图/修复建议/范围外附录/免责条款；数据全部出自账本，但正文由 LLM 组织（A.`orchestration.phaseGates`[P5]）。
- **B′ 形态**：报告正文永远由聚合器从 findings 存储确定性生成（DarkMoon「DEFINITIVE FIX」注释明言不信任 LLM 报告体，LLM 只写 executive_summary）；固定章节骨架（授权与范围声明/方法学映射/覆盖度与局限性/技术×业务风险分级/整改优先级与复测建议）；CEP report-template.html（MIT）直接复用（P§P1.4.2、P§P4.3 报告行）。
- **裁决**：**确定性重建胜出：聚合命令从 13 表账本生成报告正文（模板+账本数据，零 LLM 方差），LLM 仅写执行摘要与修复建议叙述段（仍须引用 finding ID）；中文合规章节骨架吸收为模板固定段；TanYin 的两维双列/范围外附录/免责条款（时点性/C2C3 条件性/AI 辅助声明）全部进模板；P5.5 签发对象=聚合产物文件哈希。**理由：报告是法律交付物，DarkMoon 的教训（LLM 长文不可信）与 TanYin 自己的「不信 LLM 叙述、只信账本数据」哲学一致——把该哲学贯彻到底就是确定性重建；且模板化后「报告耗时>测试耗时」痛点（P0 #10）直接消解。
- **证据**：A.`orchestration.phaseGates`[P5/P5.5]；P§P1.4.2、dive/darkmoon「output_report」、scan/standards、dive/claude-externalpentest（模板 MIT 复用）。

### R11 知识层：知识飞轮 vs references/ 分册

- **裁决**：**knowledge/ 目录体系（entities/concepts/precedents/patterns/staging/graph.ndjson+format_version）为唯一知识层与治理框架；B′ 语料（BugHunter hunt-* 模板+51 skills、Threatswarm 27 agent、CEP 知识束，均 MIT）经 ingest→staging→审批入库成为 concepts/技法页与 precedents/ 语料——走 TanYin 同一道审批门（防投毒对称性）；工具语法纠偏规则（HBPGPT AD 纠偏表模式）进 concepts 工具节；CVE 联网核验纪律（CEP）作为技法页核验规则写入 lint。**
- **理由**：B′ references 分册是「静态文件无治理」，TanYin 是「治理无语料」——语料经飞轮入库后同时获得 staging 审批/保鲜/晋升/三元组四道闸；TanYin 初始库（CNPEN 82+nuclei 模板+PortSwigger WSA）再叠加 B′ 语料，词表多元化更充分。
- **证据**：A.`knowledgeSystem`(决策4/A17/B3)；L§7.1 references 行、P§P1.3.1/P1.3.2、dive/claude-bughunter reusable#1。

---

## 3 TanYin 独有资产（B′ 必须吸收）

| # | 资产 | 为什么有价值 | 吸收注意事项 |
|---|---|---|---|
| 1 | **图谱演进循环+收敛四条件**（P3 六步：checkpoint→扫描→风暴→派发→落账→收敛判定） | 把「何时停」从 LLM 主观变成图查询——AI 渗透从演示到工程的关键一步（A.决策2）；TSecBench 佐证：榜首 Cairn（多阶段 44.6% 全场最佳）架构=黑板+事实-意图图，与账本+图谱同构（T.`rankings`[0].note、P§P3.5） | 收敛判定必须挂在 phases.yaml P3 exit 断言（R2）；防假收敛依赖抽查+异常检测（A.`matrix.rules`）一起吸收 |
| 2 | **假设风暴五路+条件触发+dedup_key+阈值递增** | 头脑风暴扩张感与工程收敛性共存的三重防线（B.因果链 4.6：随机联想震荡→条件触发+机械去重+阈值递增） | ⑤路联想在弱模型上的纪律遵循率未验证——进 §5.2 机制分档与 evals 开关矩阵 |
| 3 | **资产事件处理器**（新资产→无条件自动测绘+子矩阵） | 「越测越发现」由事件链机械保证，不靠 LLM 自觉（A.`orchestration.assetEventHandler`）；与基线冻结配合防收敛无限回退 | 测绘计入预算+单资产上限护栏必须一起搬；out_of_scope 只记 fact 不 spawn |
| 4 | **矩阵五态+基线冻结+WSTG 词表钉死+「-」「!」抽查** | 覆盖可度量的完整机制：词表构造保证列完备（防单源过拟合——CNPEN 纯 Java 样本教训，B.因果链 4.4）、冻结保证闭合率有锚点、抽查防廉价闭合博弈 | 词表版本化随 schema_version；B′ coverage-gaps.jsonl 的「静默降级强制记录」并入「!」态语义 |
| 5 | **知识飞轮四机制+learned→core 四门槛+lint 保鲜+客户三元组+反向验证+CLIENT-NN** | 知识复利且不泄漏、变厚且变准的完整治理（A.决策4；B.因果链 4.12 三道闸）——B′ 完全空白 | 先例三元组与 R9 身份矩阵的 creds 实体需对齐（先例绑 scope_asset，creds 绑 role——两套绑定字段设计时统一） |
| 6 | **引擎契约双轴+三 kind+纪律能力声明** | 换引擎不改账本；CLI 黑盒工具不成为纪律旁路（manifest 声明 max_op_level+视角上限，总控路由拒绝超限 intent）（A.`engineContract`） | CLI 引擎适配器对齐 B′ 工具适配器契约（调用模板/超时/降级链）；nuclei 以 kind:cli 引擎接入（模板钉 commit+验签） |
| 7 | **CNPEN 82 漏洞语料+web-blackbox 四段方法论** | 实战验证的差异化本体（errorCode 语义分析/前端 JS 是 API 说明书/微服务直连假设等，A.`webBlackboxEngine.fourPhases`）；B′ 无任何私有实战语料 | 入库走 staging 审批+脱敏反向验证；词表基线保持 WSTG 全集防 CNPEN 样本过拟合（TanYin 自己的教训） |
| 8 | **上下文三层策略+受管重启自动档** | 长链任务（多阶段 29.53% 瓶颈）的核心存活机制；「断电恢复是受管重启的特例」统一协议；自动档护栏（计入预算/速率上限/单活跃会话） | 自动档依赖宿主 headless 能力——与 B′ Python driver 三后端共享同一探测与 spawn 通道（安装自检 B14 扩展） |
| 9 | **命令双维度安全上下文（操作级别×视角 L0-L3）** | 「多深入」和「多危险」正交，审批精确到格子；L3 理论推演一刀切只取证（A.`discipline.commandSecurityContext`）——比 B′ 检测/利用二分细 | 标签由命令模式表判定（技法页命令模式），误分类率基线进 evals（TanYin 探知项 C7） |
| 10 | **单写者+写前拒收+ID 铸造+timeline 链式哈希** | 账本可信三件套（B.自检三问之二：「为什么账本里的数据是可信的」）；审计链取证效力（因果链 4.8：争议对手有动机改账） | 引入 driver 后保留单活跃会话约束+state revision 兜底（R1） |
| 11 | **两维正交评级+差分举证方法论** | 确定性≠危害（审计修正范畴错误 A6）；对照组基线±单变量让「已修复」vs「被 WAF 拦」在账本可区分——lint 降级不误杀的依据 | 差分机制升格为身份矩阵差分的执行器（§4-1）；C2 强制条件可达性证据规则保留 |
| 12 | **P5.5 签发门+approvals 审批账本+事故熔断三步** | 「AI 报告不经人审=行业红线」的可验证落点（command_hash 绑定不可抵赖）；事故第一小时责任划分靠快照（B.`phase_gates`[P5.5]） | 签发门与 B′ 报告确定性重建衔接：签发对象是聚合器产物哈希 |
| 13 | **摘要纪律+常驻集系统级注入** | 上下文是燃料也是毒药；查询摘要化（计数+top-N）是 token 经济学的第一道闸（对齐 TSecBench CHYing 精简编排证据） | 「工具输出 0 进上下文」与 ⑤路按相关性回读 artifact 片段的预算平衡进 evals token 效率指标 |
| 14 | **四支柱哲学+因果链+panorama 活文档治理** | 每个机制的存在理由可追溯（失效模式→机制→替代方案→使能）；设计治理防止融合期口径漂移 | cross_view_notes 9 条口径陷阱先消解再入 v2（见 5.4） |

---

## 4 B′ 独有资产（经 TanYin 两份 JSON 核实确认缺）

| # | 资产 | 证据支撑（含核实方式） |
|---|---|---|
| 1 | **身份矩阵差分**：creds/sessions/role 一等实体+受保护端点×角色逐对差分重放+findings.auth_context | 核实：A.`ledger.tables` 12 表与 B.`domain_model.eight_tables` 均无 creds/session/role；findings 字段无 auth_context。expert/pentest #1（severity high）：「Phase1-5 是未授权扫描形状……没有 creds、session、role 任何实体」，全行业空白、单人收益密度最高（P§P1.2.2/P0 #4） |
| 2 | **POC 独立重放门（三态）** | 核实：A.`qualityAcceptance` P4 仅 hash-recheck/validate，无重放执行。expert/pentest #2；三态原型 dive/open-sploit（hackerone skill VALID/REPAIRED/REJECTED） |
| 3 | **POC 四要素之 network_position/preconditions/matcher** | 核实：B.`domain_model.evidence_contract.fields` 无此三字段。expert/pentest #2：「网络位置声明是中文报告被质疑复现不了的第一大原因」；matcher schema 范本 dive/nuclei |
| 4 | **egress 代理+宿主 hook fail-closed+canary**（三层执法的进程级两层） | 核实：TanYin D 决议明确不做（B.`program_status_and_audit`）。Threatswarm fail-open+`$TARGET` 绕过实测洞（P§P1.5.2/dive/threatswarm anti）；expert/ai-agent #3 法律级风险 |
| 5 | **oob_endpoints 申报** | 核实：scope 表 kind 仅 include/exclude。expert/architect #3（scope.yaml schema 必含）；expert/pentest #5「要么取不了证、要么被迫临时开洞破坏范围模型」 |
| 6 | **scope accounts+permitted_actions+append-only amendments** | 核实：scope 表无账户/动作/修订字段。P§P1.5.2；CEP ROE amendments 审计段（dive/claude-externalpentest reusable） |
| 7 | **tools.lock 供应链锁定+nuclei-templates 钉 commit+ECDSA 验签** | 核实：A.`skillOrganization` 工具箱直调无锁定。expert/devops #3「运行时绝不自动安装缺失工具」；国内工具镜像投毒风险（P§P3.3） |
| 8 | **交战区移出 skill 树** | 核实：A.`skillOrganization.directoryStructure` 的 session/ 在 skill 根内。expert/devops #1（git pull 冲突/状态不得混居程序文件） |
| 9 | **Python driver 三后端 headless 编排** | 核实：TanYin 无 driver 层（受管重启 spawn 是单命令）。P§P4.3、L§7.1；兼作 CI/evals 无人值守入口与受管重启自动档的统一 spawn 通道 |
| 10 | **工件即缓存幂等续跑** | 核实：TanYin artifacts 只增不覆盖（恢复点）但无跳过语义。dive/osmedeus reusable#2（pre_condition file_exists） |
| 11 | **CVE 联网核验纪律** | 核实：knowledgeSystem 保鲜靠本地 last_verified。CEP 强制 WebSearch 对照 PSIRT/NVD/CISA KEV「明确不信任训练数据」（P§P1.3.3） |
| 12 | **报告确定性重建+中文合规章节骨架** | 核实：A[P5] 报告由总控 LLM 撰写、无授权声明/方法学映射/覆盖度局限性/等保占位章节。dive/darkmoon「DEFINITIVE FIX：不信任 LLM 报告体」；scan/standards「中文合规报告无结构化先例」；CEP report-template.html（MIT）直接复用 |
| 13 | **MCP 工具总线**（可选） | 核实：TanYin 经宿主 shell 执行通道，无 MCP 位。P§P4.2 论据 2（playwright/burp/msgrpc MCP）——列为可选增强非必需 |

---

## 5 冲突与风险裁决

### 5.1 最深矛盾：零代码宪法 vs 三层执法/driver/tools.lock

TanYin 决策1（纯 SKILL 零代码）+决策6（SQLite 破坏零代码宪法）+决策7/D 决议（不做守卫脚本）构成一条「宪法链」；B′ 的 must-haves ②⑩与 Python driver 恰好全部踩在这条线上。**裁决：宪法重述而非维持原状**——三个事实：①TanYin 账本命令本就是 PowerShell 5.1 片段（A.`skillOrganization.howZeroCodeWorks`），「零代码」实指「零运行时依赖、复制即装」，PS 片段已是代码，宪法的字面表述早已名存实亡；②PS 5.1 是 Windows 基底，与 B′ 三后端（macOS/Linux）直接冲突，且 A.`openItems` 自认 PS 5.1 性能边界是探知项；③B′ 实测证据（Threatswarm fail-open）表明纯 skill 层执法拦不住子代理直连界外目标。**融合口径：「skill 主体（markdown+数据文件）+ 单一薄 CLI 工具箱（python3 标准库实现账本命令/redact/scope-guard/replay，tools.lock 锁定哈希）+ 按宿主档位启用的 hook/egress」。**「LLM 只调用不实现」「凡未给出命令的步骤不得执行」两条真纪律原样保留——它们与实现载体无关。此为对 TanYin 审计 D 决议的唯一推翻项，需用户确认（§6.5-9）。

### 5.2 复杂度之争：TanYin 12 表+31 命令+九门，是多阶段 29.53% 瓶颈的解药还是毒药？

**解药面（主论）**：多阶段渗透 29.53%、完整解题率 8.33% 是全行业共同短板（T.`headline.common_weakness`），其本质是长链状态与上下文管理失败——恰是 TanYin 重状态设计的目标面。赛场证据三点：①榜首 Cairn（均 77.70%、多阶段 44.6% 全场最佳）的架构标签是「黑板+事实-意图图」（T.`rankings`[0]），与 TanYin「账本+图谱+未消费 fact 扫描」结构同构——状态中间层模式拿到赛场验证；②Claude Code（零渗透代码）多阶段 41.1% 排第二（T.`domain_matrix_highlights`），通用 agent 循环+文件即状态已胜过绝大多数专用框架自研编排——TanYin 的 Harness 哲学（复用宿主）+状态全落盘正是这条路的系统化；③垫底 PentestAgent 5.4%（P§P4.2.1 引），无状态契约的教训。**结论：状态复杂度是解药。**

**毒药面（须防）**：①token 经济学——Cairn 458.50M vs CHYing 27.92M（30 倍），CHYing 用 15.78M 拿 85.14%（T.`headline.token_variance`）：重编排有真实成本上限。TanYin 每轮 checkpoint+三查询+验收落账的协议开销必须被「查询摘要化+常驻 <2K+工具输出 0 进上下文」三闸钉死，并把 token 效率（每收敛一格的 token 成本）列为 evals 一级指标。②prompt 复杂度才是毒药——TanYin 的机制复杂度绝大部分落在磁盘与命令（四支柱中 Graph/Harness 的落位），真正常驻上下文的只有循环骨架+命令索引（A.`skillOrganization.loadingStrategy`），<2K 可守；只要守住「复杂性进状态不进 prompt」这条红线，九门+31 命令不是上下文负担。③模型档位风险——模型间差距 20+ 百分点（Kimi K3 是 11/13 Agent 最佳搭档，T.`headline.best_model`），弱模型对协议纪律的遵循率未验证：安装自检扩展为「宿主×模型双档探测」，输出机制分档（弱模型档：关⑤路联想、降并发、简化门禁展示），机制开关矩阵进 evals。

### 5.3 平台基底冲突（裁决 #10 详述）

PS 5.1（A18 已决）vs B′ 三后端：迁移为跨平台薄 CLI 的同时消掉 TanYin 探知项第一条（PS 5.1 无 grep/awk 的万行账本性能边界——python3 标准库无此问题）；账本命令签名（A.附录 A 冻结的 31 条）原样保留，只换实现载体；黄金夹具正是保证迁移零语义漂移的回归网（先迁实现、夹具字节级对齐再动语义）。

### 5.4 cross_view_notes 九条口径陷阱的消解（B.`cross_view_notes.notes`）

| # | 陷阱 | 融合稿消解 |
|---|---|---|
| 1 | 「五不原则」同名不同物（总控侧 vs Harness 侧） | v2 词典重命名：**薄总控五不**（不写代码/不发请求/不判重/不算哈希/不渲染图）与**宿主五不**（不要求宿主改/不规定内部/不干涉调度/不假设能力/不锁死宿主） |
| 2 | 边种类 9 vs 10 | 官方口径 **10 边**（scope-rel 入列，关系完备性约定）；schema_version 先行 |
| 3 | P0 八问 vs evolution-loop「备份确认」 | 以 security-discipline **八问表为准**；「备份状态确认」并入第④问 RoE 补充项（不设第九问） |
| 4 | timeline 扩展名不一 | 钉死 **timeline.tsv**（TSV 家族一致，链式哈希语义不变） |
| 5 | 召回率三层 vs 四层 | **四层为准**（矩阵/图谱/知识/靶场），与 §4-1 身份矩阵合并后靶场层加「认证后漏洞检出率」子项 |
| 6 | 0.75 重启阈值 vs storm_threshold 0.5 | 两参数显式命名区分：`restart_context_threshold=0.75` 与 `storm_score_threshold`（随轮数递增），进 phases.yaml 常量区 |
| 7 | web-blackbox 另有引擎文档 | 权威链不变：spec（契约级）→引擎文档（引擎内部）；冲突以 spec 为准（A.`webBlackboxEngine.authorityRelation`） |
| 8 | 铁律1 显式表述在主设计文档 | v2 四铁律全文收录（薄总控+单写者／状态落盘+受管重启／覆盖不可谈判+预算合法终态／证据即漏洞+两维评级） |
| 9 | artifacts/ 位置两说 | 运行时以 **submissions/<intent-id>/artifacts/** 为准；session 级目录说明删除 |

### 5.5 双方审计遗留 → 融合必修清单

**TanYin 侧**：A1-A20 阻断级已全部落入设计定稿（B.`program_status_and_audit`）——融合稿全部继承，其中 4 项因融合需改落点：A14 审计链（timeline 扩展 revert_cmd 后哈希输入随之定义）、A18 平台基底（PS 5.1→跨平台 CLI）、A19 上下文生命周期（+resume_kit 白名单）、A16 契约执行语义（+nuclei 引擎适配器）。B1-B17 简化项照旧。C1-C10 探知项中 4 项升格为融合必修：C1 打分因子历史命中率校准（进 evals）、C3 宿主权限规则模板（进四层执法档位表）、C4 注入红队集 CI（进 evals L2）、C6 烛龙一致性夹具（保留在烛龙接入批次验收）。**D 决议（TSV 保留/守卫脚本不做）：TSV 保留维持；守卫脚本一项推翻（5.1）。**
**B′ 侧**（四专家 approve-with-changes，L§7.2）：AI-Agent 5 High（handoff/resume_kit✓R8、journal✓R1、三层执法+canary✓R7、evals 门禁✓R5、工具调用契约降级进负空间→吸收为「工具不可用/降级必须写 coverage-gaps 与 fact」）全部进入必修；架构师 4（phases.yaml✓R2、state schema+F-XXX 原子取号✓R1、scope oob✓R7、cleanup+changes_ledger✓R9）；渗透 3（身份矩阵✓§4-1、POC 硬契约+重放门✓R6、护栏下沉+占位符网关✓R7/R3、预算树+排序✓R4；内网资产图/立足点建模→assets.type 扩展 pivot/foothold+attack 边已有链式语义，列批次 4）；工程维护 3（安装矩阵+交战区移出✓§4-8/7、四层测试基线✓R5、tools.lock✓§4-7、schema_version+engagement-snapshot→TanYin 已有 schema_version，snapshot 吸收为 state 快照命令）。

**融合必修清单（合并去重后，按落点分组）**：

| 落点 | 必修项（来源） |
|---|---|
| 账本/契约 | 单写者+写前拒收+ID 铸造（TanYin A1）、账本命令集（A2）、事件溯源（A3）、编码规范（A4）、schema_version 全表（B6）、13 表定稿含 creds/sessions（B′ 渗透 #1）、POC 四要素+findings 字段（B′ ⑧）、scope schema 扩展（B′ 架构师 #3） |
| 状态机/循环 | phases.yaml 九门+回边（B′ 架构师 #1 × TanYin A5⑥）、收敛四条件（A5/决策2）、假设排序公式（B′ 渗透 #5） |
| 门禁/安全 | 四层执法分档（B′ ②+TanYin 决策7 推翻）、canary（B′ AI-Agent #3）、占位符四关卡（B′ ⑦×TanYin A10）、deny-list（TanYin A11）、速率熔断（A8）、注入防护四层（A11）、审批账本+签发门（A14/A20）、命令双维度（TanYin 决策5） |
| 证据/交付 | 差分举证（A12）、独立重放门（B′ ⑥）、报告确定性重建（B′ §4-12）、清理门+revert_cmd（A13×B′ ⑫）、事故熔断（TanYin A8） |
| 知识 | staging 审批（A17）、learned→core 四门槛（决策4）、lint 保鲜+差分降级（A12 联动）、客户三元组（B3）、语料入库（B′ references）、CVE 联网核验（B′ CEP） |
| 工程/验收 | 黄金夹具（A15）、evals CI 门禁（B′ ⑪）、token 效率指标（TSecBench）、安装矩阵+tools.lock（B′ ⑩）、交战区分离（B′ devops #1）、双宿主验证（TanYin req §7）、打分校准/注入红队集 CI（TanYin 探知项 C1/C4 升格） |

### 5.6 残余风险登记（融合后仍开放的风险）

| 风险 | 等级 | 缓解 | 残余 |
|---|---|---|---|
| 弱模型对 31 命令协议的遵循率未验证（模型间差 20+pt，T.`headline.best_model`） | 高 | 机制分档+evals 开关矩阵+负向用例（「未给出命令的步骤终止报告」可检测） | 首发需限定模型档位清单 |
| 账本命令箱迁移（PS 5.1→python3）引入实现 bug | 中 | 黄金夹具字节级回归先行（迁移是第一批验收） | 语义漂移风险靠夹具覆盖度 |
| 四层执法分档导致「安全水位因宿主而异」 | 中 | 报告守门声明披露档位事实；canary 按档位进 evals；最低档=账本级+执行通道级恒在 | egress 缺席档位的残余暴露面须明示 |
| 13 表+九门+31 命令的首版实现体量（TanYin 原批次 B1-B6 即数周级） | 中 | 批次 0 契约冻结+批次切分（6.3）；身份矩阵/⑤路等可档位化后置 | 首个可用版本时点后移，需用户对批次排序 |
| evals 靶场与真实目标分布偏差（P§P5.2 定性判定局限） | 中 | 种 20 漏洞 ground truth+TSecBench 六域外部对齐双轨 | 召回声明仍属「授权环境口径」 |
| 多交战并行与 graph.ndjson 锁协议仍是探知项（A.`knowledgeSystem.multiSessionAndUpgrade`） | 低 | 首发单 session 串行+目录级隔离（B′ 交战区分离）；行级合并预留 | 多开需求出现前不设计 |
| 烛龙接入语义漂移 | 低 | 一致性夹具 C6 列入接入批次验收 | 接入时点未定（§6.5-9） |

---

## 6 综合设计 v2 骨架建议（供用户评审的蓝图大纲）

### 6.1 分层结构（TanYin 五层为骨，B′ 三层自研边界为肌）

```
L5 宿主层      DSH / opencode / codex（B′ 三后端）+ walcode / CodeBuddy（TanYin 双宿主）
              └─ 安装自检：宿主×模型双档探测 → 执法档位 + 机制分档
L4 总控编排层  SKILL.md 路由器（常驻<2K）+ phases.yaml 数据状态机（九门+回边）
              └─ phases/*.md 方法论指令（按需加载）+ 指挥官协议（六要素/单写者）
L3 领域核      13 表 TSV 账本（12 表 + creds/sessions）+ 薄 CLI 命令箱（31 命令
              +redact/scope-guard/replay，tools.lock）+ timeline 链式哈希（journal
              职能 + revert_cmd）+ state.md（≤200 行 handoff/resume_kit）
L2 引擎契约层  CONTRACT.md 双轴：web-blackbox（SKILL 型）· nuclei（cli 型 adopt，
              模板钉 commit+验签）· vuln-agent（cli 适配）· session-viz（projector）
              · 身份矩阵差分子流程（挂差分段，复用 pair_group）
L1 知识纪律层  knowledge/ 飞轮（+B′ 语料经 staging 入库）+ shared/ 六件 + scope
              （accounts/oob/amendments）+ 四层执法档位表
```

要点：数据依赖向下（L4 读写 L3，L3 引用 L1），政策权威向上横切（纪律对总控自己也生效，A.`architecture.hexagonalCorrection` B10）；B′ 的「胶水层」=L3+L4 契约、「门禁层」=L1 执法档位+CLI 命令箱内置校验、「契约层」=L3 schema+POC 卡片+报告模板（P§P3.4）——两套分层语义一一对位。

- **L5 宿主层**：DSH/opencode/codex 三后端 + walcode/CodeBuddy（TanYin 多宿主）；安装自检探测「宿主×模型」双档→执法档位与机制分档。
- **L4 总控编排层**：SKILL.md 路由器（常驻 <2K：铁律/安全规则/循环骨架/命令索引/授权状态）+ **phases.yaml 数据状态机**（九门+回边，exit 断言=账本命令）+ phases/*.md 方法论指令 + 指挥官协议（六要素委派/单写者）。
- **L3 领域核**：**13 表 TSV 账本**（原 12 表 + **creds/sessions**）+ 薄 CLI 账本命令箱（31 命令+redact+replay+scope-guard，tools.lock）+ timeline 链式哈希（journal 职能+revert_cmd）+ state.md（≤200 行 handoff/resume_kit）。
- **L2 引擎契约层**：CONTRACT.md 双轴（skill/cli/projector+纪律能力声明）；web-blackbox（SKILL 型）+ nuclei（cli 型 adopt，模板钉 commit+验签）+ vuln-agent 适配器 + session-viz（projector）+ 身份矩阵差分子流程（挂在 web-blackbox 差分段，复用 pair_group）。
- **L1 知识与纪律层**：knowledge/ 飞轮（+B′ 语料经 staging 入库）+ shared/ 六件（DISCIPLINE/EVIDENCE/SEVERITY/LEDGER/VOCAB/DENYLIST）+ scope（含 accounts/oob/amendments）+ 四层执法档位表。

### 6.2 核心机制取舍清单（v2 定稿口径）

| 机制 | v2 口径 | 来源 |
|---|---|---|
| 账本/单写者/事件溯源/链式哈希 | TSV 13 表+命令箱+单写者+写前拒收+ID 铸造 | TanYin（R1） |
| 状态机 | phases.yaml 承载九门+回边 | B′ 形式×TanYin 语义（R2） |
| 循环/收敛 | 图谱演进循环+收敛四条件+budget-exhausted 双合法终态 | TanYin（§3-1） |
| 风暴/排序 | 五路+条件触发+dedup+阈值递增；排序公式=确定性因子×期望impact÷成本 | TanYin+B′ 公式（R4） |
| 覆盖 | 五态矩阵+冻结+WSTG 词表+抽查+coverage-gaps 强制记录 | TanYin 为主+B′ 降级记录（§1.2-3） |
| scope | 四层纵深分档+canary+oob/accounts/amendments | B′ 为主+TanYin 账本硬门（R7） |
| 凭据 | {{vault:cred-N}}+四关卡+输出兜底重 tokenize+降级不拒绝 | TanYin 语法+B′ 链路（R3） |
| 证据/出卡 | E-index+四要素+独立重放门三态+auth_context+exploitation_status | 合体（R6） |
| 身份矩阵 | creds/sessions 表+端点×角色差分重放（pair_group 机制） | B′ 独有吸收（§4-1） |
| 预算 | 三元组树化+可选 $+熔断+事故快照 | 合体（R4） |
| 上下文 | 三层策略+自动档+摘要纪律+工件缓存跳过+kill-9 保真 | TanYin 为主（R8） |
| 知识 | 飞轮四机制+三元组+四门槛+lint；B′ 语料入库；CVE 联网核验 | TanYin 为主（R11） |
| 报告/交付 | 确定性重建（聚合器生成正文，LLM 只写执行摘要）+两维评级+中文合规章节+P5.5 签发+P6.0 清理（revert_cmd） | 合体（§4-12/R10/R9） |
| 验收 | 三层：黄金夹具→evals（CI 门禁）→TSecBench 六域对齐 | 合体（R5） |

### 6.3 实施批次建议（重排 TanYin B1-B6，插入 B′ 门禁/契约批次）

- **批次 0 契约冻结**：13 表 schema+schema_version、10 边、占位符语法、phases.yaml、scope schema（含 oob/accounts/amendments）、POC 卡片四要素、findings 字段定稿——全部纸面定死再动手（TanYin「设计无分期、批次间接口定死」方法论）。
- **批次 1 账本命令箱+黄金夹具**：31 命令跨平台 CLI 实现+redact/scope-guard/replay+夹具字节级回归（先于一切业务）。
- **批次 2 门禁层**：四层执法档位+canary 集+凭据网关四关卡+预算树。
- **批次 3 总控 skill+图谱循环**：SKILL.md+phases.yaml 引擎+演进循环+受管重启+工件缓存。
- **批次 4 引擎层**：web-blackbox 四段+身份矩阵差分+nuclei 适配器（验签）+vuln-agent+session-viz。
- **批次 5 知识飞轮+语料入库**：CNPEN 82+B′ 语料（BugHunter/Threatswarm/CEP）经 staging+lint+CVE 核验。
- **批次 6 evals+安装矩阵+交付**：三层验收全量 CI 化、安装矩阵+tools.lock+交战区分离、报告流水线+签发/清理门、授权靶场全流程（含 budget-exhausted 演练+种 20 漏洞）。
- **批次 7（可选）烛龙接入**：L2 适配器换烛龙 runner+一致性夹具 C6 验收（A.`zhuLongIntegration.consistencyFixture`）——时点待拍板（§6.5-9）。

批次间接口在批次 0 全部定死（TanYin「设计无分期、批次解耦」方法论，A.`workingMethodology`）；每批出口跑黄金夹具回归，不绿不放行（R5）。

### 6.4 验收标准合并方案

TanYin 四条（黄金夹具逐字节一致／靶场全流程+签发报告／82 漏洞 ingest 抽查／双宿主可用，A.`qualityAcceptance.requirementsAcceptance`）∪ B′ evals 指标（金标精确率/召回率、POC 机器复放率、scope canary 零容忍、kill -9 续跑保真度、报告 schema lint+脱敏检查，P§P4.3）∪ 新增融合项：**身份矩阵差分检出率（靶场种认证后漏洞）、token 效率（每闭合一格的 token 成本，对标 CHYing 量级）、机制分档开关矩阵在最低档模型下的纪律遵循率、四层执法各档位的 canary 通过率**。外部对齐：TSecBench 六能力域分类法（多阶段渗透为主指标）。

### 6.5 需用户拍板清单

1. **零代码宪法重述**（5.1）：接受「skill 主体+薄 CLI 工具箱+档位化 hook/egress」？——这是对 TanYin D 决议的推翻，需显式确认。
2. **TSV 保留 vs findings 双轨**（R1）：findings 嵌套字段全部走「TSV 索引+外置卡片」是否接受？
3. **平台基底迁移**（5.3）：账本命令 PS 5.1→python3 CLI，确认目标宿主集合（是否仍需 Windows/PS 支持）。
4. **身份矩阵进首发还是批次 4**：专家判为单人收益密度最高，但依赖 creds/sessions 契约——建议批次 0 定契约、批次 4 落地。
5. **执法默认档**：egress 代理默认开启（更安全但安装重）还是按宿主可选（更轻）。
6. **模型分档策略**（5.2）：弱模型档自动裁剪⑤路/降并发是否接受（涉及「覆盖不可谈判」铁律的档位化表述）。
7. **预算第四维 $**：默认关还是开（影响 budget 命令与 evals 指标）。
8. **TanYin 双宿主承诺（walcode/CodeBuddy）与 B′ 三后端（DSH/opencode/codex）的优先序**：安装矩阵首批覆盖谁。
9. **烛龙接入时点**：一致性夹具（C6）留在哪个批次之后。
10. **evals 靶场选型**：docker-compose 自建（B′ 方案）为金标 + 是否追加 TSecBench 式外部对齐跑分。

---

## 7 证据索引（裁决 → 出处映射）

| 裁决/章节 | TanYin 证据 | B′ 证据 | 外部证据 |
|---|---|---|---|
| 0-1 形态合流 | A.`architecture.keyDecisions`决策1；B.`engineering_philosophies`[harness] | pain P4.1 路线 D、P4.2 五论据 | T.`rankings`[4] Claude Code 72.30%/多阶段 41.1% |
| 0-2/R1 账本 | A.决策6、`ledger.format/tables/stateMachineSemantics/singleWriter/commands`；B.`domain_model.encoding_and_state_machine` | pain P4.3 状态存储行；L§7.2 ④；expert/ai-agent #2 | — |
| 0-3/R2 状态机 | A.`orchestration.phaseGates`；B.`phase_gates` | L§7.2 ①；expert/architect #1；dive/osmedeus、dive/caldera | — |
| 0-4/R7 执法 | A.决策7、`discipline.denyList`(A11)；B.`security_discipline.honest_boundary`、`program_status_and_audit`[D 决议] | L§1 共识；P§P1.5.2、P§P3.2②；dive/threatswarm anti；expert/ai-agent #3 | — |
| 0-5/R3 凭据 | A.`evidence.credentialVault`(A10)；B.`domain_model.directories`[vault] | L§6.4；P§P1.4.3、P§P2.8（DarkMoon） | — |
| 0-6/R4 预算 | A.`budget`(A5)；B.`p3_loop.budget_exhausted`、`e2e_execution_flow`[S6/S15] | P§P1.5.3、P§P2.5（HBPGPT Limits）；L§7.2 ⑨ | T.`headline.token_variance`（30 倍） |
| 0-7/R6 证据 | A.`evidence.contract/differentialEvidence`(A12/B5/B12)；B.`domain_model.evidence_contract` | L§7.2 ⑥⑧；P§P1.4.3；dive/nuclei、dive/open-sploit、dive/strix | — |
| 0-8/R5 验收 | A.`qualityAcceptance`(A15/B16)；B.`verification_and_governance.mechanisms` | P§P4.3 评测行；L§7.2 ⑪；expert/ai-agent #4 | T.`implications_for_our_work`[6] |
| 0-9/§4-1 身份矩阵 | 核实缺：A.`ledger.tables`、B.`domain_model.eight_tables` | P§P1.2.2、P0 #4；expert/pentest #1 | — |
| 0-10/5.3 平台载体 | A.`skillOrganization.howZeroCodeWorks`（PS 5.1）、`openItems` | pain P4.3（driver/tools.lock）；expert/devops #3 | — |
| 5.1 宪法冲突 | A.决策1/6/7；B.`agent_protocols` | P§P3.3、P§P3.4 三层自研 | — |
| 5.2 解药/毒药 | A.`skillOrganization.loadingStrategy`、`contextLifecycle` | pain P4.2.1 | T.`headline`（29.53%/8.33%/30 倍/Kimi K3）、`domain_matrix_highlights`（Cairn 44.6%） |
| 5.4 口径消解 | B.`cross_view_notes.notes`（9 条原文） | — | — |
| 5.5 审计遗留 | B.`program_status_and_audit.five_expert_audit`（A1-A20/B1-B17/C1-C10/D1-D5） | L§7.2 专家汇总表；P§P3.2 | — |
| §3 独有资产 | A.`orchestration.evolutionLoop/hypothesisStorm/assetEventHandler`、`matrix`、`knowledgeSystem`、`engineContract`、`webBlackboxEngine`、`discipline.commandSecurityContext`、`severity` | 核实缺：L§7.1 组件表、pain P0-P5 全文 | T.`rankings`[0] Cairn 黑板+事实-意图图 |
| §4 独有资产 | 核实缺：A/B 各键（见该表「核实方式」列） | P§P1.2.2/P1.4.3/P1.5.2/P1.5.3/P2 各卡；L§6、§7.1；scan/standards | — |
| 6.4 验收合并 | A.`qualityAcceptance.requirementsAcceptance`、`recallMetric`(B16) | P§P4.3 evals 指标集 | T 六能力域 |

**原始输入**：`.research/tanyin/A-core-design.json`（1683 行）、`.research/tanyin/B-principles-panorama.json`（2200 行）、`docs/research/2026-09-19-ai-pentest-landscape.md`（§7）、`docs/research/2026-09-20-pain-points-and-adoptability.md`（P0-P5+附录 A）、`.research/dive/tsecbench-q2-2026.json`。本分析未读 TanYin 原始四文档（REQUIREMENTS/设计定稿/引擎文档/architecture），以两份结构化抽取为权威输入；抽取件声明 A1-A20+B1-B17 已全部落入设计定稿（A.`meta.reviewBasis`）。

# 五家实物与知识全景 —— 探隐研究语料全面审计（corpus-audit-research）

- **日期**: 2026-10-17 · **性质**: 研究语料盘点报告（只读审计 + 仅写本档）
- **任务**: 全面研读 docs/research/ 全部研究语料 + knowledge/ 目录结构，输出五家参照系统（ARTEX/CSAI/ZhuLong/multica/VulnClaw）逐家全景、探隐自身已建能力清单、知识库现状、信息缺口表。
- **语料底账**（本次实读，全部在 `探隐仓 = /Users/wgen/redteam-agent`）:
  - docs/research/ 顶层 7 份: 2026-09-19-ai-pentest-landscape / 2026-09-20-pain-points-and-adoptability / 2026-09-24-vulnclaw-analysis（173 行全文）/ 2026-10-11-artex-analysis / 2026-10-11-artex-vs-tanyin / 8-fork-candidates / dsh-plugin-marketplace
  - liveui/ 22 档: INDEX + 编号档 0-7（含 1b/2b/2c）+ walk×8（artex/artex-live/csai/csai-live/multica/tanyin/zhulong/zhulong-live）+ copy-v09d / craft-v09d / live-recon-1（data/ 26 份页面文本与 shots/ 截图目录在册未逐份读）
  - manuals/ 5 本: usage-guide-{artex,csai,csai(骨架版),multica,zhulong}（注: usage-guide-csai.md 与 usage-guide-cyberstrike.md 是同一系统的完整版/骨架版两份，INDEX 记"手册×4"指 artex/csai/multica/zhulong 四本成册）
  - artex-deep-dive/ 6 份（0-index + 五路视角）
  - knowledge/ 全部 55 文件: SOURCES.tsv / staging.tsv / log.md（190 行）/ index.md / overview.md / graph.ndjson / concepts×8 / precedents×5 / patterns/learned×2 / retros×24 / cve 快照 / methodology×2 / checklists / 3 个 example 登记簿 / format_version
- **纪律**: 只读 + 仅写本报告一个文件；结论一律带出处（文件 §节 / 行号）；不猜——凡语料无据的，写"语料无据"。

> **术语注记（防误解）**: 任务书中的"三环飞轮（真值/知识/度量）"一词在全部语料中**零命中**（grep 全仓 `.md` 无"三环"），是本次审计的归纳框架而非语料术语。下文按此框架逐家映射，每环映射均给出语料实词佐证（真值环=账本/哈希链/验证/终审；知识环=技能/记忆/语料库/经验库；度量环=覆盖度/召回/对照实验/统计检验）。同理"攻击大脑"指系统里做攻击决策的智能体层，各家语料中的对应物不同。

---

## 一、五家参照系统逐家全景

### 1.1 ARTEX —— AI 自主渗透测试控制台（资产最厚的竞品）

**产品形态**
- Go 单二进制（`go:embed` 内嵌 Next.js 16.2.9/React 19/Tailwind v4 静态导出前端，:8787 同端口伺服 UI+API+SSE）+ PostgreSQL（pgx，仅认 `ARTEX_PG_DSN`）；535 个 Go 文件 / 130,654 行 + web/src 187 文件；自研 norma SDK 作 agent 内核（源码注释证实 norma 上游闭源、v0.4.3 为代理快照恢复）。出处: liveui/2-artex.md §0；8-fork-candidates §1.1；manuals/usage-guide-artex.md §0.1。
- 页面族 21 项 IA（功能 10 + 系统 11），交付含 Docker 镜像 + 五路安装；许可 **AGPL-3.0** 且作者附加"仅限学习研究"禁令。出处: 2-artex.md §0/§1.2；2026-10-11-artex-analysis §一。
- 本地实例: http://localhost:8787，活体在跑真实战斗（烛龙靶场任务 #1）。出处: walk-artex.md 头注；walk-artex-live.md §0。

**攻击大脑在哪**
- 每任务 **1 个 plannerLoop + N 个 workerLoop**（DB 配置默认 3 worker）+ 可选 deadlineCoordinator；planner 是**唯一意图源**（读探索图态势→frontier 派 0..N 意图→worker 单表 CAS 领取一条→真实工具执行→写回双图→再唤醒 planner，直到 prove_goal）。出处: artex-deep-dive/1-orchestration.md ①；usage-guide-artex.md §0.3-0.4；2026-10-11-artex-analysis §五。
- 四角色 agent: goals/planner/worker×N/mainagent（+retester 复测角色 2 工具）；编排完全自持（未用 norma 的 coordinator/plan 原语，SDK 只是运行时底座）。出处: 2-artex.md §0；deep-dive/1-orchestration 补记。
- live 实证: 意图是 planner 发的**全中文作战命令**（300-800 字，含背景交接/分步/红线/编号引用），frontier 74 条意图、digest 55 个压缩节点在图。出处: walk-artex-live.md §4.1/§4.3。

**三环飞轮各环**
- **真值环: 缺**。PostgreSQL 可变库，全 db/*.go 无哈希链/行签名（五路深读 2 路 grep 双源实锤"零防篡改、零审计链"）；finding 由 agent 写图、无独立重放实证；发现无终审生命周期（51 条全 pending，无已确认/误报域）；有 retester 三态复测（reproduced/fixed/inconclusive）但 verdict 纯由 LLM 自报、无独立验证器。出处: deep-dive/0-index 交叉验证①；deep-dive/2-data-graph ③.1；deep-dive/3-security-gates ①/③.6；2026-10-11-artex-analysis §八；walk-artex-live §4.5。
- **知识环: 半**。三个 SKILL（api-recon/playwright-cli/scopesentry）+ 文件型 memory（markdown+关键词检索，**中文检索 0 分近乎不可用**）+ 技能正文独立 message/压缩后逐字重注入；无跨任务经验库、无人审蒸馏、无发现→知识回流。资产图（全局共享）是唯一跨任务"真值复用"。出处: deep-dive/5-weaponry-skills ①/③；2-artex.md §0。
- **度量环: 无效果测量**。有覆盖度 CTE（scope 分母÷fact 锚定分子，live 实测 33%=40/122）与 Token 计量（187.9M、缓存命中 95%），但**从未测过自己的召回/精度，无 GT 对照、无统计检验**。出处: deep-dive/2-data-graph ①覆盖度；2026-10-11-artex-vs-tanyin 补记"仍成立的三项技术事实"②；walk-artex-live §0/§4.2。

**已核实 vs 未核实**（walk 节号）
- 已核实: ①33 视图 DOM 漫游 + 源码级解构（walk-artex.md §1-§3；2-artex.md 全文）；②五路深读 15-20 文件/路带行号（artex-deep-dive/ 全 6 份）；③活体批#1: 51 findings 全 pending+严重分布（严重 9/高 20/中 15/低 7）、图谱 260 节点 359 边、资产 132、审批 37 条全录、Token 三段、覆盖 33%、暂停不清 frontier（3 条待领存活）、复测 0 活跃、报告已生成（walk-artex-live.md §0/§4.2/§4.5/§4.6）；④planner 自愈行为（目标宕机写带重试意图）与 ROE 红线句式逐字（walk-artex-live §2/§4.1）；⑤51 条发现标题全录 + 战场蔓延实测（一句"测 localhost:3081"打穿整个评测网络与宿主）（walk-artex-live §4.5）；⑥与 10-15 首轮的差分（发现 39→51、审批 19→37、Token ×2.56）（walk-artex-live §0 差分行）。
- 未核实: ①**51 条 finding 的真假**——全部 pending、活跃复测 0，无一经独立复现（walk-artex-live §4.5/§4.6）；②37 条审批记录的构成（规则命中/ask/LLM judge 各占多少未分类；judge 默认关是源码结论，live 实际配置未查）（deep-dive/3-security-gates ③.1 vs walk-artex-live §0）；③报告正文质量（只核了生成时间戳与摘要句）（walk-artex-live §0 报告行）；④worker 并发/调度公平性（priority 形同虚设是源码判断，live 未测）（deep-dive/1-orchestration ③.5）；⑤llmpool 熔断是否实战发生（会话列表见"系统审计·LLM 故障转移"分组但未展开）（walk-artex-live §4.1）；⑥"学习研究"附加禁令的正文与边界（README:484-486 只引了 AGPL 段）。

### 1.2 CyberStrikeAI（CSAI）—— 零框架大型化标本 + 攻击基础设施全家桶

**产品形态**
- Go 1.25 + eino + SQLite 双库（conversations.db + knowledge.db）+ **零框架单体前端**（673KB 单模板写死 29 页 / 4.7 万行手写 CSS / 45 个业务 JS + 41 个前端单测，vendor 7 库运行时 script 引入）；本地源码真身 259MB/7457 文件；上游 AIPentest/CyberStrikeAI **7812★ / Apache-2.0**。出处: liveui/3-cyberstrike.md §1.1-1.2；manuals/usage-guide-csai.md 头注/§5。
- 四合一渗透作战平台: 对话式开战 + 资产/漏洞运营 + **C2/WebShell/监听器/Payload/流量伪装攻击基础设施** + MCP/知识/技能/角色能力中心（29 页 IA 四区）。口号 "intent becomes governed execution"。出处: usage-guide-csai.md §0；walk-csai.md §0。

**攻击大脑在哪**
- 意图（对话/批量队列/工作流/机器人）→ 编排器 → MCP 工具调用。**四种编排可选**: eino_single（Eino ADK 单代理，本实例默认）/ Deep / Plan-Execute / Supervisor（专家路由）——大脑形态是可切换的编排模式，不是常驻规划引擎。live 实证用户用 **Supervisor 批量队列当单任务用**（1 子任务 22 分钟产出 4 漏洞+5 事实）。出处: usage-guide-csai §0 核心闭环/§2 会话设置；walk-csai-live §1.2/§1.5。
- 审批侧还有一个"AI 审 AI"大脑位: 审计 Agent（独立小模型按 OpenAI 协议跑审批提示词）。出处: usage-guide-csai §2.0 HITL；walk-csai.md §1 表 03 行。

**三环飞轮各环**
- **真值环: 弱**。SQLite 双库可变、无哈希链；有 HITL 审批留审计日志（90 天）、漏洞五态生命周期（待处理/已确认/已修复/已忽略/误报）+ 事实黑板置信度三态（待确认/已确认/已废弃，exploit 类加"可复现"）——**终审域存在但本实例 4 漏洞全部待处理、修复率 0%**。出处: usage-guide-csai §3.5/§2.2；walk-csai-live §0。
- **知识环: 有架子没转**。RAG 知识库（多查询改写+向量+精排+后处理，配置面完整）**本实例未启用（空态引导去设置）**；23 Skills / 13 角色 / 16 Agent(.md 制)在役；事实黑板=项目级记忆（"黑板质量=平台智商"）。出处: walk-csai-live §0 能力面"知识未启用"；usage-guide-csai §0 能力矩阵/§2.3。
- **度量环: 运营指标非效果度量**。仪表盘有修复率/加权风险分 10.5/工具成功率 95.4%/扫描覆盖率（含"从未扫描/超 30 天未扫描"队列）；无 GT 对照、无召回/精度、无对照实验。出处: walk-csai.md §0/§1 表 01/06 行；walk-csai-live §1.1。

**已核实 vs 未核实**（walk 节号）
- 已核实: ①30 视图 DOM 漫游（29 页全走+登录层，每页 6500-9500 元素、全站 272 input 常驻 DOM）（walk-csai.md §0-§1）；②源码级组件/状态三层模式/复用组件清单/rbac-guards 400+ 写函数映射（3-cyberstrike.md §1.2-1.4）；③live 批#1: 4 漏洞全文标题+时间戳、事实黑板 5 行全录、工具 Top10（exec 105 居首）、开战三入口与 36 个 modal 全量字段编目（零点击）、HITL 待审计 0、C2/WebShell 全空态（walk-csai-live §0-§2.1）；④与首轮差分: 战斗 15 日 14:13 后停、主战场转 ARTEX（walk-csai-live §0 差分行）。
- 未核实: ①4 条漏洞真假（全部待处理，复测按钮在但语料无复测记录）（walk-csai-live §1.4）；②**C2/WebShell/监听器实战能力——全空态，模块在但零运行证据**（walk-csai-live §0）；③RAG 检索质量（未启用，无从测）；④审计 Agent 的实际拦截质量（待审计 0，无样本）（walk-csai-live §0）；⑤工作流画布/Burp 插件/浏览器扩展/8 渠道机器人的实际可用性（walk-csai §1 表 11 行走过界面，无实跑记录）；⑥上游 7808★ 项目与本地 v1.7.23 的版本差（语料未对账）。

### 1.3 ZhuLong（烛龙）—— 靶场中枢与引擎调度台（用户自有平台）

**产品形态**
- pnpm monorepo: Vue 3.5 + Pinia / Hono + better-sqlite3 / zod 契约单源；无 LICENSE 文件=私有自有；本地 Vite dev 栈（server 7090 + web 3081）；27 视图六域（项目/任务/漏洞/资产/下载/用户）+ 品牌故事页。定位"资产组织 × 引擎调度 × 漏洞终审"。出处: 8-fork-candidates §〇 表；usage-guide-zhulong.md §0/§1；walk-zhulong.md §一。
- **同时是靶场**: 本实例正被 ARTEX/CSAI 当攻击对象，库内含攻击者留下的行（XSS payload 项目名原样回显在册）。出处: usage-guide-zhulong.md 头注/§9；walk-zhulong §一.04 行。

**攻击大脑在哪**
- **自己没有攻击大脑**——引擎插件制: manifest 注册外部 AI 红队 CLI（内置 demo/GenCPT/GenLPE + 外部 tanyin（探隐）/zhulong，5 引擎在册），任务建单时引擎×模式（开眼=广域/吐焰=深度）×环境×算力四维，runner 跑 CLI 落会话日志，**mapper 把会话日志解析成结构化 findings**，人工三态终审收口。大脑在各引擎 CLI 里（探隐即其一大脑）。出处: usage-guide-zhulong §0/§3.3-3.5；8-fork §〇"唯一现实二开形=引擎闸接入（端点 82），BO14 已把探隐注册为第四引擎 tanyin@1"。

**三环飞轮各环**
- **真值环: 人工终审制**。三态终审（疑似/确认是/确认非）+判定人+判定时间+CVSS 向量串+PoC 四元组（静态/动态/前置条件/验证方法）+出处（文件:行）+标注时间线+诚实边界描述；治理面 RBAC 三角色/审计日志全写面/scrypt/全库凭据加密（master.key）。本实例 13 findings = 11 疑似/1 确认是/1 确认非，**确认率 8%**——真值生产靠人，机器不判真。出处: walk-zhulong §一.10-13；live-recon-1 §3.9；usage-guide-zhulong §0。
- **知识环: 静态规则库非飞轮**。资产管理"知识图谱"Tab（19 漏洞类·227 合规规则·5 提权族）——入库的静态参考知识，无回流/蒸馏/经验库机制。出处: usage-guide-zhulong §0 能力矩阵资产行。
- **度量环: 运营计数**。七桶任务 KPI（可点深链）、确认率、阶段进度、成本计数（USD/tokens，失败任务也有成本三计数）、admin-health 平台健康面（Findings/吞吐/WAL/队列/SSE 计数）；无 GT/召回/对照实验。出处: walk-zhulong §一.05/10；usage-guide-zhulong §0。

**已核实 vs 未核实**（walk 节号）
- 已核实: ①27 视图漫游含 URL-SSOT 深链/诚实空态/三态 KPI 互斥等视觉语言（walk-zhulong §一-§二）；②源码深析（Vite dev server 对 /src/*.vue 返回编译模块、sourcemap 全量还原 110 模块与本地真身 diff 一致）（liveui/4-zhulong.md §附方法备忘）；③live 批#1: 弹壳清单（靶场侧战斗痕迹与 ARTEX/CSAI 发现交叉互证）+ 表单 open-then-cancel 逐项取证（walk-zhulong-live §1-§4）；④使用手册 §9 战斗痕迹交叉索引；⑤引擎闸接入事实（8-fork 实地复核: 数据面已通"TSV 权威列→NDM mapper 已落地"）。
- 未核实: ①**mapper 解析探隐 TSV 的实际精度**——接入已落地但解析准确率/漏误报率无任何档（8-fork §〇 只有结论行）；②探隐作为第四引擎（tanyin@1）的实际产出——zhulong 侧 13 findings 是 zhulong 引擎产的（usage-guide-zhulong §0），tanyin 引擎跑过几单、产出什么，语料无据；③远程 runner 接入吞吐（7 接入仅 1 在线是快照，无压测）（usage-guide-zhulong §0 算力行）；④知识图谱 227 合规规则的来源与时效（无出处档）；⑤SSRF 闸门绕过类 findings（ARTEX #50 等）修复后是否复测闭环（语料无据）。

### 1.4 multica —— 组织编排层（平台出形、实践出魂）

**产品形态**
- 开源"AI 数字员工"任务平台（GitHub multica-ai，v0.5.1 自托管）: Go 后端 + Next.js 前端 + pgvector/pg17 三容器 docker-compose；OTP 无密码登录（未配邮件通道时验证码打 [DEV] 日志——实测弱点）；**本地无源码**（仅镜像部署件），一切 internals 结论来自容器内二进制 strings/1120 个 SQL 迁移/DB 只读查询/128 版本 changelog。Linear 式任务面板 × 每任务可被 AI 员工领走真跑 × 跑在自己电脑上。出处: manuals/usage-guide-multica.md §0-§1；8-fork §〇 表 multica 行；walk-multica §0。
- 37 路由 + 15 设置子页全部实测走访；灰阶单色设计、业务页零动画。出处: usage-guide-multica §3；walk-multica §①-§②。

**攻击大脑在哪**
- **无自有安全大脑**。把外部 CLI 编码代理（Claude Code/OpenCode/Codex/DSH 等 12 运行时）注册为 Runtime，其上定义 Agent（人格化指令+技能+可见性）→ Squad（队长/成员）→ Issue 派工；大脑=外部 LLM CLI，multica 只供组织形态（issue/squad/skill 数据面 + daemon 本机执行面 `~/.multica`+`~/multica_workspaces`）。用户正把它当**渗透作业编排驾驶舱**: GenCPT 9-Phase 流水线 WGEN-2 在役、安全红队/审计队两编制、pentest-core/recon/engagement/report-delivery 四技能、Claude+Opencode(GLM-5.3) 双运行时。出处: usage-guide-multica §0/§2/§5；1b-multica-security-capability.md §一；walk-multica 互通备忘。

**三环飞轮各环**（1b-multica-security-capability.md §二"产品没有的"六无 + §三专业判决）
- **真值环: 无**。Postgres 可变库、无哈希链/防篡改；execution_log 是运维日志不是证据链（1b §二.2）。
- **知识环: 无安全知识**。Skills 是通用任务技能（用户自装 4 个渗透技能）；无漏洞语料/经验库/发现回流；issue/squad 是组织记忆非安全知识（1b §二.6"零安全工具——它是 PM 平台不是安全平台"）。
- **度量环: 组织计量**。每运行 usage 计量+自定义定价口径（1b §四.⑤）——度量的是"花了多少"，不是"找得准不准"；无召回/精度/GT。
- 判决原文: **multica 对 AI 辅助安全的价值="组织编排层"而非"安全能力层"（置信 0.88）；平台出形，实践出魂**；与探隐互补分工（multica=多项目组织层，探隐=单战审计+自主战斗层，薄桥互通）；翻案条件=其插件表面原生出货 guard/egress/验证类能力（1b §三）。

**已核实 vs 未核实**（walk 节号）
- 已核实: ①58 张截图/37 路由+15 设置子页 DOM 实测（walk-multica §①；usage-guide-multica §3）；②六无判决逐条（1b §二）；③OTP 弱点实测（验证码打日志）（usage-guide-multica §1.2/§10）；④数据模型 118 表分类+API 面（前端实测+二进制 strings 提取）（usage-guide-multica §6-§7）；⑤在役实况: WGEN-2 流水线/编制/技能实测 DB（usage-guide-multica §5）；⑥二开判决: 无源+许可未实证+兼容低 → 不二开（8-fork §〇）。
- 未核实: ①**许可**——本地无 LICENSE、研究档未记录、外网核验不可用（8-fork §〇 标 ❓"未实证"）；②源码级 internals（无源码，结论全部是行为/二进制层推断）；③v0.5.1 之后是否出货安全实质能力（翻案条件未复查——1b §三）；④daemon 本机执行面的安全边界实测（ARTEX #45/#51 已把它打成"任务投递面伪造会话直达宿主机 RCE"，但那是攻击侧结论，multica 自身修复无从核）（walk-artex-live §4.5）。

### 1.5 VulnClaw —— 单进程 LLM 自主渗透 CLI（可大量取材的上游语料库）

**产品形态**
- v0.4.0（MIT，Python ≥3.10）单进程异步事件循环 Agent（AgentCore），无常驻服务: CLI 每次拉起→跑循环→落盘退出；四外壳共用 AgentCore——Typer CLI 19 命令 / python -m / Rust TUI(5,355 行) / FastAPI Web(任务+SSE)。Python 175 文件 64,795 行（agent 25k/cli 10.9k/intel 5.4k/report 3.6k…）+ React 前端 9,154 行 + 测试 113 文件/1,680 test 函数/31,921 行。出处: 2026-09-24-vulnclaw-analysis.md §1.1-1.2（下称 VC 分析）。
- 本地 clone: `.research/repos/VulnClaw` HEAD 3b71e26（2026-09-16），**浅克隆单 commit 无历史可考**。出处: VC 分析头注。

**攻击大脑在哪**
- **默认 solve 引擎="LLM 决策 + 证据门禁"**: 工具选择与调查策略明确留给模型（solver.py:411-417 "not required workflows, phases, checklists"），信息收集→发现→利用→报告四段**不是硬编码流水线**，全靠模型自决+事后门禁。另有 rounds 遗留引擎（阶段推进+侦察 8 轮强制）与 team 五角色引擎并存。自然语言→任务约束是**中文正则关键词抽取**而非 LLM 结构化解析（input_analysis.py:143）。出处: VC 分析 §2.1-2.2/§1.1。

**三环飞轮各环**
- **真值环: 半账本+四道下游闸**。run 目录=append-only events.jsonl+快照+writer.lock，**无行哈希链、无单写者**（SessionState/target_state/events 三处并行写）——"TanYin 账本的雏形对照物"；证据记忆 SHA-256 内容寻址+去重+有界预览；防编造四闸: ①完成门（FINAL 必须 cite 已知证据 id、flag 逐字在证据、无证据拒）②finding 入口隔离检疫（[未验证] 前缀+needs_manual_review）③报告只渲染 verified ④PoC 复核验证器（L4）——闸全在**下游**，上游 intake 仍可把 LLM 散文正则抠成 finding。出处: VC 分析 §3.1-3.3。
- **知识环: 全五家最完整**。kb/ JSON 语料 store+BM25/ChromaDB 双后端降级检索+**experience 跨会话经验库（人审门: "Lessons remain pending until a human approves them"+蒸馏+0.88 阈值近重复合并）**；7 核心 skill+47 专题 skill 目录+2 篇 warstories 实战复盘；CVE 核验词表（remediation_rules.py 1,108 行）。出处: VC 分析 §1.2/§6.3。
- **度量环: 无效果度量**。有 headless 退出码契约（0 干净/1 事故/2 ≥1 verified/3 仅候选）与 findings.json（全量）+findings.sarif（仅 verified）双工件，但无 GT 对照/召回/精度/统计检验。出处: VC 分析 §6.3。
- 定位结论原文: "同类竞品、相反哲学"——VulnClaw 验证了 LLM 自主渗透的工程可行性，但其全部结构性弱点（无单写者/无覆盖承诺/无 egress 执法/无验证链）恰是 TanYin 铁律逐条针对性解决；对探隐=**可大量取材的上游语料库+反面架构参照**。出处: VC 分析 §6.2 表/§7。

**已核实 vs 未核实**
- 已核实（注: **无 walk 档**——walk 系列五份（tanyin/artex/csai/multica/zhulong）不含 VulnClaw，全部结论是源码级读码）: ①架构/模块/行数实测（VC 分析 §1）；②四段流程实现真相（§2）；③run 半账本/证据记忆/四道闸及弱点自白（§3，全部带 源码路径:行号）；④护栏七执法点+ExecutionGate 内容寻址审批+spawn 边界 CI（§4.1-4.3）；⑤测试/CI/技术债（§5）；⑥取材落地已在 knowledge/ 复核（见本报告 §三）。
- 未核实: ①**运行时行为零实跑**——无一词来自实机运行/活体巡访，全为读码推断；②三引擎（rounds/solve/team）实际效果对比无测；③浅克隆无法评估提交历史质量（VC 分析 §5 自认"不确定项，明说"）；④README 自述与实际的差异未抽查（方法声明"README 只作定位参考不作证据"）；⑤v0.4.0 之后的上游演进（HEAD 冻结在 2026-09-16）。

---

## 二、探隐自己: 已建能力清单（只列研究语料能证的）

> 判据: 仅采 docs/research/ 与 knowledge/ 语料可证的事实；设计文档（docs/design/）里的"计划/蓝图"不算已建（本报告纪律只读 docs/research + knowledge）。

| 能力 | 语料可证的现状 | 出处 |
|---|---|---|
| **账本（真值底座）** | 13 本 TSV 账 + 哈希链 + verify-chain: "账本完备 13 表 322 行"（battle-4 G-r5 实战验收）；battle-42/G-r43 ledger timeline 436 行；逐战明细"verify-chain 全 PASS"（13 战）；ARTEX 五路深读交叉确认"哈希链——我们已有而它没有（2 路 grep 证实）"、"边方向 _EDGE_DIR 代码强制" | knowledge/retros/RT-0002 摘要；walk-tanyin §头注/§二 metrics 行；artex-deep-dive/0-index"我们已有而它没有" |
| **执法（四层执法/铁律）** | 探隐核心资产三件套被 8-fork 立为二开判据:"账本哈希链 · guard 执法 · 度量考卷"；四层执法（Tier 3 egress 代理+canary）与铁律 7 薄 CLI 在 VulnClaw 对照表中作为探隐既有能力出现；tools.lock 供应链锁定是 landscape 一票否决项（已立）；九门数据状态机 phases.yaml（P0/P1/P2/P3/P4/P5/P5.5/P6.0/P6 九门实存——walk 实测 UI 漏了 P6.0 是观察面 bug 非账本缺失） | 8-fork-candidates 头注判据；VC 分析 §6.2 表；2026-09-19-landscape §1.5；walk-tanyin §三.1/附证据索引 |
| **观察面（tanyin-web）** | v0.9a→v0.9d 七页活体: 总览/动态/对话/测试覆盖/攻击路线/发现/战报+实验；纯 stdlib+vanilla JS 零依赖（5 张手写 HTML 1024 行起步）；只读投影零写端点+textContent 防注入+SSE 断链可见徽标；v0.9d 工艺批: 18 色令牌/7 档间距/五档字号/三档阴影/WCAG AA 全档≥4.5:1，TDD 11 测先红后绿+全量 1491 tests OK；文案换血批: 九词钦定词典+状态词/概念词对照+三项用户裁决落定（重放=复测/计量词=项/召回替词=召回率） | walk-tanyin §一/§二/§四"改版别丢的"；craft-v09d §二/§三；copy-v09d §1/§用户裁决 |
| **复测（重放验证）** | 重放三态在观察面成域: E-index 卡总数 44/已复现 41/未重放 3/需人工 0（battle-42 快照）；P4 重放 30/30 全 VERIFIED 零强改（battle-4: "历史首轮全绿"）；"POST/DNS 卡片重放全中" | walk-tanyin §二 evidence 行；RT-0002 摘要/writeback |
| **对照实验（度量考卷）** | 度量页三件套成体: ①统计卡——对照臂 mean recall 0.554 n=8 / 处置臂 0.589 n=5 / **McNemar exact p=0.125 b=4 c=0 无显著差异**；②预登记实验表（directive-n5，判后回填考据注记）+黑话表四律"预登记/判后回填/无登记不认/结算报告装配"；③召回曲线三臂+逐战明细 13 战（recall/命中分母/MISSING/GT 配对/verify-chain）。实验方法论复盘独立成页: b11 gateloop 对照实验（臂B 0.41=23/56 vs 臂A 0.66——"直觉断层实锤，推进策略可插拔定谳"），单样本 n=1 裁决力有限自认 | walk-tanyin §二 metrics 行；copy-v09d §黑话表；RT-0024 front-matter/教训 |
| **知识飞轮（部分建成）** | 流水线机制完整（lint→approve→commit→index 再生成）且真实转过两圈; 内容侧战役复盘持续到 10-10——详见 §三 | knowledge/log.md 全文；retros/ 文件 mtime |
| **实弹战绩（在环验证）** | 授权靶场在环首战 20 靶点（真实检出 8/20，账面 0 分三层归因如实入档）；battle-4 独立战士 50 靶面（门控召回 0.24 vs 基线 0.56，P4 重放 30/30，批次 10 修复实效: out_of_scope 41/41→2/27、空哈希工件 34→0）；13 战逐战明细在度量页 | knowledge/precedents/PR-0003；RT-0002 摘要；walk-tanyin §二 |
| **被平台接纳为引擎** | BO14 把探隐注册为 ZhuLong 第四引擎（tanyin@1），数据面"TSV 权威列→NDM mapper 已落地"——二开判据"高"兼容的唯一对象 | 8-fork-candidates §〇 表 ZhuLong 行 |

**语料可证的边界（同样重要）**: ①探隐观察面九门灯漏 P6.0、版本号三处不一致等 7 项一致性 bug 在册待修（walk-tanyin §三）；②metrics 页非显著结论（p=0.125）不能当效果宣称用（walk-tanyin §二）；③探隐观察面自身被 ARTEX 列为攻击目标（#43 零认证泄露评估账本）——缓解仅靠只读投影+127.0.0.1 绑定+零写端点（walk-tanyin §四.14）；④探隐 UI"垃圾中的垃圾"怒斥后 v0.9d 才达工艺线（craft-v09d 头段自述病根）。

---

## 三、知识库现状: 从 VulnClaw 挖了什么、飞轮实际转了没有

### 3.1 从 VulnClaw 挖了什么（实物对账，非计划口径）

- **语源登记**: SOURCES.tsv KP-0006 = origin vulnclaw、`.research/repos/VulnClaw/LICENSE` sha256=798df5f8…（仓库级 LICENSE 文件锚指纹，非语料本体哈希）、MIT、2026-09-24T09:20Z 登记。出处: knowledge/sources/SOURCES.tsv L7。
- **实际入库 10 页，逐页核验**:
  - **8 个 detail-pack = concepts/CP-0001..CP-0008**（redteam-{sqli,xss,ssrf,ssti,deserialize,cmdi,cors-miscfg,open-redirect}-detail-pack 的四段结构映射技法页: applicability/vuln_class/正文边界节/failure_modes/judgment），全部 `source_id: KP-0006`、`last_verified: 2026-09-24`——CP-0001（SQL 注入七变体）、CP-0002（XSS 三型）等已抽读核实。出处: knowledge/sources/vulnclaw/LICENSE.note L8-11（取材范围声明）; concepts/CP-0001.md/CP-0002.md front-matter。
  - **2 篇 warstory = precedents/PR-0001/PR-0002**（PHP 正则绕过数组回调链 / PHP 弱比较三关卡，均 `source_id: KP-0006`，window=2026-04-19 与 VulnClaw warstories/2026-04-19_php-deserialization 文件名同日；占位符化+triples ≥6 行符合声明格式）。出处: precedents/PR-0001.md L23 / PR-0002.md L21；VC 分析 §6.3。
  - 取材凭证: LICENSE.note 载许可注记+取材范围+防投毒声明（"外部与自有语料同走一道 staging 审批门"）；CVE 核验标记待核验清单（R11 离线通道: 本批不写 cve_refs，待联网对照 NVD/KEV 后补 {cve,source,verified_at} 行）。出处: LICENSE.note L12-21。
- **没挖的**: LICENSE.note 自述"余 39 专题批次 6+ 持续飞轮——移交登记"，语料中无任何后续批次痕迹（concepts 停在 CP-0008；patterns/core 0 页）。warstories 仅 2 篇（VulnClaw 仓就只有 2 篇，VC 分析 §1.2"warstories/（2 篇实战复盘 md）"——已全量取）。

### 3.2 knowledge/ 飞轮实际转了没有（账面对账）

**流水侧（lint→approve→commit→index 再生成）: 转了两圈半，2026-09-29 20:03 后停**
- 第一圈（2026-09-24，批次 5）: KP-0006 登记→STG-0001..0010 lint pass→approve（approver=批次5-执行者，review-checklist 逐项自查）→commit CP-0001..0008 + PR-0001/PR-0002（共 10 页）。出处: knowledge/log.md L4-34。
- 第二圈（2026-09-29，批次 9，语源 KP-0010=内部 HANDOFF）: 登记→STG×4 approve（approver=批次9-执行者，approvers-add 复核人名录）→commit PT-0001/PT-0002/PR-0003/PR-0004（L85-108）；当日 14:03 再 commit PR-0005（L138-140）；19:03 commit RT-0001（L172-174）——**log.md 至此为止（末条 RT-0001 lint pass），log/index/overview/staging.tsv 四文件 mtime 均停 9 月 29 20:03**。出处: log.md L174-190；ls -la 实测。
- **停转的直接证据**: staging.tsv 仅表头 0 行（staging/pages/ 目录空）；index.md 记"K8 retros: 1 页"——而 retros/ 实际 **24 个文件**；overview.md 记"正文页总数 16"——实际 8 CP+5 PR+2 PT+24 RT = **39 页**。账面与实物差 23 页。出处: staging.tsv L1；index.md L11 vs `ls retros/`；overview.md L4。

**内容侧: 没停——复盘页靠另一条路径持续入库 11 天**
- RT-0002..RT-0024 共 23 页，文件时间 9 月 30–10 月 10 日逐日/隔日新增（battle-4 G-r5 独立战士复盘→…→b11 gateloop 对照实验复盘），front-matter 完整（missed/attribution_check/trigger_gap/weak_channel/writeback 五字段+归因核验种子锚点表）。出处: retros/ 文件清单与 mtime；RT-0002/RT-0024 抽读。
- **但这些页没有 lint/approve/commit 任何流水记录**——LICENSE.note 宣称的"外部与自有语料同走一道 staging 审批门"对 RT-0002+ 不成立（至少无留痕）。飞轮的"轮"（登记→审批→入账→再生成索引）停了，内容生产（战役复盘）还在滚。

**结论（一句话）**: 飞轮真转过（VulnClaw 批 10 页 + 内部批 7 页全流水入账），但 2026-09-29 之后**登记/审批/索引再生成的轮停转**，复盘内容以"绕过流水"的方式继续堆积 23 页——知识库当前是"账面 16 页、实物 39 页、审批覆盖 17/39"的状态。

**其他空转位（实测）**: staging/pages 空；targets/、entities/、business/、patterns/core/ 四目录空（K1 methodology 0 页、K2 entities 0 页、K7 business 0 页）；CVE 快照仅 18 行样例（"正式全量快照=批次 6 安装器期刷新"自认未做）；SOURCES.tsv 中 KP-0001..0005（cnpen 五路语料）全部"待补：素材库在仓外"、KP-0007..0009（bughunter/threatswarm/cep）降级登记未挖。出处: 各目录 ls；cve/cve-snapshot.tsv 头注；SOURCES.tsv L2-10。

---

## 四、信息缺口表: 要做产品形态决策还缺哪些事实

> 按"决策→缺口→缺口的出处判断→补法建议（从语料可推的）"组织。加粗=挡决策的一手缺口。

| # | 挂起的决策 | 缺的事实 | 出处（为何判缺） | 补法（语料内建议） |
|---|---|---|---|---|
| 1 | **ARTEX 合体/采纳与否**（合体架构: 广度归 ARTEX、签名归探隐） | **对标实验数据: 同 56-GT 靶场 n=3 测召回+精度+耗时**——已从"可选研究"升格为"采纳/合体决策的数据前置"，一次未跑 | 2026-10-11-artex-vs-tanyin 补记"修正后三线策略"③ | 按 artex-vs-tanyin 原方案执行同场对比 |
| 2 | 同上（评测数据可信度） | **ARTEX 51 findings 的真值**——全 pending、复测 0 活跃，无一经独立复现；不核真就不能当"竞品效果好"的证据，也不能当探隐对照基线 | walk-artex-live §0/§4.5/§4.6 | 抽检重放（探隐复测能力正好是干这个的）；live-recon-1 §3.11 已提"三源对照视图"设想 |
| 3 | **探隐引擎接入 ZhuLong 后的产品形态**（引擎闸已通，产出没验证） | ①mapper 解析探隐 TSV 的精度（漏/误报率）；②tanyin@1 引擎在平台侧实际跑了几单、产出什么 | 8-fork §〇 只有"已落地"结论行；usage-guide-zhulong §0 的 13 findings 归属 zhulong 引擎 | 在 ZhuLong 建一单 tanyin 引擎任务全链走查（语料内无此档） |
| 4 | 探隐 UI 底盘形态（零依赖 vs 借壳二开） | 已决——8-fork §六判"UI 底盘二开与零依赖律冲突是结构性的，放弃"；但"放弃零依赖的实际代价账"只在 8-fork §六.2，若重开需补 | 8-fork §〇/§六 | 无需补数据，除非翻案 |
| 5 | 观察面方向盘批（开战/指挥/审批按钮） | live-recon-1 已给 30 条带出处的改进清单；缺口=**探隐自己的写操作面零存在**（全站只读投影，无任何开战/刹车按钮）——做成什么样缺"我们自己的作业流数据"（探隐战斗都从 CLI 起，UI 从未指挥过战斗） | walk-tanyin §一"页面上本来就不存在任何写操作按钮"；live-recon-1 §一 | 先定产品口径: 观察面是否升级指挥面（这是产品决策不是数据缺口，但语料无用户表态记录） |
| 6 | **multica 薄桥 or 翻案** | ①许可未实证；②v0.5.1+ 是否原生出货 guard/egress/验证类能力（翻案条件） | 8-fork §〇 ❓；1b §三 | 外网核验 LICENSE+changelog（本次审计外网不可用） |
| 7 | VulnClaw 是否只当语料库（不外接） | 运行时效果零实跑——读码结论无一场实机验证；三引擎效果对比无测 | VC 分析方法声明（纯读码）；本报告 §1.5 | 若考虑外接，先跑 headless 对靶场一轮（退出码契约现成） |
| 8 | **知识飞轮续投口径** | ①RT-0002..0024 无审批留痕——staging 门对复盘页是否豁免需制度决定；②VulnClaw 余 39 专题/cnpen 五路/bughunter/threatswarm 语料全未挖；③CVE 全量快照+联网核验（R11 待办）未做；④index/overview 停更致账实不符 | 本报告 §3.2；SOURCES.tsv L2-10；cve-snapshot 头注 | 先补账（重跑 index 再生成+补 log），再定豁免规则，再排批次 6+ |
| 9 | CSAI 抄页库的使用边界 | ①4 漏洞真假（全待处理）；②C2/WebShell 实战能力（全空态）；③Apache-2.0 逐文件搬运的合规清单（哪些文件可搬已判，但搬运记录未建） | walk-csai-live §0/§1.4；8-fork §〇 CSAI 行 | 抽检 4 漏洞；C2 空态如实记录即可不阻碍决策 |
| 10 | 成本口径（对外交付定价） | ARTEX 同场战斗 Token 187.9M（缓存 95%）的**金额口径**未算；探隐逐战成本在度量页有 recall 无成本列 | walk-artex-live §0/§7.2；walk-tanyin §二 | 对标实验（#1）顺带采集成本三列 |
| 11 | 覆盖度语义对齐 | ARTEX 覆盖 33%（fact 锚定资产口径）vs 探隐消格率 100%（108/108 格）——两种覆盖语义不可直接比，缺对齐说明 | walk-artex-live §0；walk-tanyin §二 | 对标实验前先写口径对照页 |
| 12 | ZhuLong 知识图谱复用 | 227 合规规则/19 漏洞类/5 提权族的来源、许可、时效——若探隐要复用，出处无档 | usage-guide-zhulong §0 | 向平台侧（父代理/用户）要来源档 |

---

## 附: 本报告引用档清单一句话索引

| 档 | 一句话定位 |
|---|---|
| liveui/INDEX.md | 22 档研究索引（含 2d 用户亲交 UI 标准答案、live×3、手册×4 登记） |
| liveui/0-dsh.md … 7-codex-security.md | dsh 宿主/multica/ARTEX/CSAI/ZhuLong/两 dsh 插件/GenSift/codex-security 八路源码档 |
| liveui/walk-{tanyin,artex,artex-live,csai,csai-live,multica,zhulong,zhulong-live}.md | 八份界面漫游/活体巡访（含探隐 before 基线） |
| liveui/copy-v09d-report.md / craft-v09d-report.md | 文案换血批/视觉工艺批完工报告（v0.9d） |
| liveui/live-recon-1.md | 探隐改进清单 30 条（方向盘/对话页/战报页三组，每条带 walk 节号） |
| manuals/usage-guide-{artex,csai,multica,zhulong}.md | 四本成册使用手册（+csai 骨架版 usage-guide-cyberstrike.md） |
| artex-deep-dive/0-5 | ARTEX 五路独立深读+交叉验证 |
| 2026-09-19-landscape / 2026-09-20-pain-points | 业界全景（13 项目裁决）与 14 痛点/采纳性 |
| 2026-09-24-vulnclaw-analysis.md | VulnClaw 173 行源码深析（本文 §1.5/§3.1 底座） |
| 2026-10-11-artex-analysis / artex-vs-tanyin | ARTEX 深析与对比决策（含合体架构与补记重算） |
| 8-fork-candidates.md | 二开底子四候选判决（ARTEX❌/CSAI 抄页/multica❌/ZhuLong✅引擎闸） |
| knowledge/（55 文件） | SOURCES.tsv 10 语源 / staging.tsv 空 / log.md 190 行 / concepts×8+precedents×5+patterns×2+retros×24 / cve 快照 18 行 |

*报告完。全程只读 docs/research 与 knowledge，未改任何既有文件；本档为唯一写入产物。*

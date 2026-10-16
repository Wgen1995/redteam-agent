# 引擎部件拆解:ARTEX / CyberStrikeAI / multica 形态考证

> 调查日期:2026-10-17。A 章为 multica 形态考证(目录勘察 + 文档通读 + 活体巡访);B 章为 ARTEX 与 CyberStrikeAI 挖洞能力部件拆解(纯源码,不含界面)。
> 纪律:外部系统只读(唯一写操作 = multica 登录 POST);源码结论均带 路径:行号;不确定处明说不猜。

---

# A 章 · multica 形态考证

## A.1 目录全量勘察:是部署,不是源码

`'/Users/wgen/Documents/AI For Security & Compliance/multica项目实践/'` 全量文件(find 实测,共 12 个):

| 位置 | 内容 | 性质 |
|---|---|---|
| `Multica安装使用指南.md`(109 行) | 中文安装/使用/安全备注 | 自写指南 |
| `_research/`(8 文件) | README.md、README.zh.md、SELF_HOSTING.md、CLI_INSTALL.md、docker-compose.selfhost.yml、Makefile、install.sh、.env.example | **上游文档与部署脚本的手工摘录副本** |
| `multica-selfhost/`(3 文件) | docker-compose.selfhost.yml、.env、.env.example | **纯部署编排**(在用) |

判定依据:
- 无 `.git`、无 Go/`*.go`、无 TypeScript 源码、无上游仓库的 `apps/`、`server/`、`scripts/` 目录树;_research 是按需摘下的文件集合(README 引用的 docs/、VISION.md、CONTRIBUTING.md 等均不在)。
- `multica-selfhost/docker-compose.selfhost.yml` 与 `_research/docker-compose.selfhost.yml` diff 完全相同——即官方 selfhost compose 的原样落地,镜像全部来自 `ghcr.io/multica-ai/multica-{backend,web}`。

**源码可得性结论:multica 源码在本机找不到。** 该目录是"部署 + 研究"混合体,不是 checkout。源码本身是公开的(github.com/multica-ai/multica,Apache-2.0 全文 + 托管/商用嵌入/品牌附加条款;本地若有需要 `git clone` 后 `make dev`,依赖 Node 22 / pnpm 10.28.2 / Go 1.26.6,见 _research/README.md「Development」节)。

## A.2 容器与活体实测

容器(docker ps 实测,全部 Up):
- `multica-frontend-1`(ghcr.io/multica-ai/multica-web:latest)→ 127.0.0.1:3000
- `multica-backend-1`(ghcr.io/multica-ai/multica-backend:latest)→ 127.0.0.1:8080
- `multica-postgres-1`(pgvector/pgvector:pg17,healthy)

CLI:`multica 0.5.1`(commit f41fae6b0,Homebrew 安装);daemon 当前 **stopped**。`/api/config` 返回 server_version v0.5.1、allow_signup=true、vcs_integration_available=true。

登录实测:multica 自部署版**没有用户名/密码登录**,只有"邮箱 + 验证码"(登录页 DOM 与前端 JS 均只见 `/auth/send-code`、`/auth/verify-code`、`/auth/refresh`)。因此任务给的 admin/Whg1995! 在此产品形态下不适用;改用指南中已认证邮箱 2642328381@qq.com 走验证码流(send-code → 后端日志 `[DEV] Verification code` 取码 → verify-code),登录成功拿到 JWT,以下 API 均为只读 GET。

工作台活体:
- Workspace:**Wgen**(1 个)。
- Agents 2 个:**1111**(model `zhipuai-coding-plan/glm-5.3`,max_concurrent_tasks=6,绑定 gencpt 技能)与 **安全红队-队长**(调度台 agent,指令明写"不执行任何渗透测试操作",接单先审"授权八问":目标/范围与深度/排除项/RoE/报告语言/时间窗/紧急联系人/账号与数据分级,缺件即置 blocked,再拆 5 个 stage 子任务改派)。
- Runtimes 2 台(同一 daemon 注册):Claude Code 2.1.238 与 Opencode 1.19.0,均 offline(daemon 停)。
- Issues:如 WGEN-2「渗透测试标准流程(GenCPT 9-Phase 流水线)」——gencpt 技能在单次运行内逐 Phase 调度子代理,issue 树只做阶段跟踪/证据路径/复盘,产出落在会话目录 `/tmp/gencpt-<session_id>/`(reports/、knowledge_graph/、evidence/、progress.json、audit_log.json)。

## A.3 形态判定

**multica 是一个独立的开源产品,不是 harness 生态的组件。** 定位:"Agents that show up on the board"——把 AI 编码智能体当队友派活的团队工作区/项目管理系统(_research/README.md)。技术栈:Next.js 16 前端 + Go 后端(Chi + gorilla/websocket)+ PostgreSQL 17(pgcrypto/pg_trgm)+ 每台机器上的 daemon 经 WebSocket 领任务、在本机拉起 agent CLI 执行(README「Architecture」)。

与 harness 生态的关系是**驱动与被驱动**:multica 支持 26 种 agent CLI 作为 runtime,其中明确列出 `DeepSeek Harness | dsh`(README Runtime 表)——即 dsh 这类 harness 是它桌上的"执行器",multica 是上层派单台。它不自带模型、不替代任何 CLI。

本机形态是**服务器容器化自部署(web 版)**,不是桌面应用:桌面端(Electron)只是它另一种官方发行形态;本机用的是 Docker Compose 三容器 + brew CLI,且服务只绑 127.0.0.1(compose 头部注释明确警告不得改 0.0.0.0)。

## A.4 安全工作流长什么样

产品内置的治理面(README + compose + .env.example):
1. **派单-验收环**:Issue 指派 agent → daemon 在本机领任务执行 → 边做边评论 → 完成进"审核中" → 人验收才合并(Review gates)。
2. **全程留痕**:每次运行的工具调用/命令/报错带时间戳可回放;Token 用量按 agent、按 issue 统计。
3. **权限**:owner/admin/member 三角色 + 每成员可跑哪些 agent 的精确授权;agent 有 permission_mode。
4. **部署卫生**:默认仅 127.0.0.1;随机 JWT_SECRET/POSTGRES_PASSWORD/VCS_SECRET_KEY;`DO_NOT_TRACK=1` 关每日部署级匿名遥测;WeCom 媒体抓取带 SSRF CIDR 白名单;服务端 LLM 辅助层(仅聊天标题/追问两消费者)默认关闭,与 agent 执行路径(各 CLI 自己的凭据)完全分离(.env.example MULTICA_LLM_* 注释)。

用户在本实例上跑的实际安全工作流(活体证据):
- **红队小队模式**:「安全红队-队长」agent 做调度台——人审八问 gate(授权要件不全不开工)→ 拆 stage 子任务 → 各成员执行 → 队长阶段抽验/人审升级。授权检查放在派单层而不是执行层。
- **GenCPT 9-Phase 容器渗透流水线**:绑定 gencpt 技能的 agent 在单次运行内自动调度各 Phase 子代理,支持 mode/scope/approval 参数,产出证据目录 + knowledge_graph + 审计日志 + 断点续跑;issue 树只承担跟踪与复盘。

一句话:multica 本身不"挖洞",它是把挖洞 agent 组织起来、留下审计痕迹的**编排与治理层**;安全语义(授权八问、RoE、证据归档)由用户定义的 agent 指令与技能带来。

---

# B 章 · ARTEX / CyberStrikeAI 挖洞能力部件拆解

## B.0 一句话对比

- **ARTEX**:常驻的**自主渗透引擎**——双图为状态、事件驱动 planner/worker 循环、发现从写入图到绑流量到复测全在系统内闭环。
- **CyberStrikeAI(CSAI)**:**对话/编排式安全执行中枢**——用户发起,Eino 三模式编排(deep/plan_execute/supervisor),90 个 YAML 工具配方 + 项目黑板 + RAG 知识库,治理重心在 HITL/RBAC/拦截。

## B.1 ARTEX(Go,AGPL-3.0;repo: /Users/wgen/dsh-test/repos/ARTEX)

### B.1.1 规划循环怎么写

- 入口 `server/engine.go:748` `Engine.Run`:每任务起 1 个 plannerLoop + N 个 worker goroutine(N=系统设置里的 work agent 数,默认 3,README:227),外加任务级 deadline 协调器(`server/engine.go:768`)。
- `server/engine.go:800` `plannerLoop`:**事件驱动 + 心跳兜底**。worker 写回/finding/goal 变更触发 `t.notify`(边沿唤醒),心跳默认 ≥600s(`plannerHeartbeatInterval`,engine.go:781-787);每次唤醒先 debounce 合并突发(engine.go:811-819),再过 paused/deleting/terminal/settling/goalless 六道门(Engine.go:824-858)后进入 `planner.Plan()`(engine.go:880)。
- `agent/planner.go:355` `Planner.Plan()` 是**唯一意图生成器**(planner.go:19-22 注释)。关键设计:每次唤醒是全新 LLM 会话,但持有一份按任务保留的 `TodoStore`(planner.go:47-48 `todos map[int64]*actool.TodoStore`)——串行利用链记一次、跨轮按依赖逐步派(`renderPlannerTodos` planner.go:129-144)。规划提示词 `plannerDefaultTmpl`(planner.go:298-340)写死了:0 意图需正当理由的"硬底线"、done/exhausted/blocked 三态重派规则、串行链用 TodoWrite、一次 `add_intent` 批量最多 4 条(planner.go:335)、量化验收禁止提前 prove_goal(planner.go:316)。
- 收官只由逐个 `prove_goal` 驱动;最后一个目标标 met 时任务自动 done(engine.go:885-894)。planner 还能用 `kill_work`/`steer_work` 监督在跑 worker(planner.go:119-125),心跳轮提示词会强制复查停滞(engine.go:452-459)。
- worker 侧:`agent/worker.go:349/357` `Execute/ExecuteWithMessage`——领**一条**意图,用真实工具做完、写回图、即停;不做方向生成(worker.go:23-27 注释)。
- **模型怎么调**:全部经 norma SDK 的 `agentcore.Options`(planner.go:405-440 / worker.go:527 附近)注入 Provider。`agent/provider.go:169-232` 支持 anthropic / openai / openai-responses 三种格式 + 代理 + quota 感知 transport(provider.go:338);`llmpool/pool.go` 把多个 LLM profile 组成故障转移链(活跃配置做链头 RankActive,failover + 健康注册表 + 窗口容量跳过);`llmrec/` 记录每次调用(goal 分解与引擎同池同限流,goals.go:81-84 注释)。每轮原始会话经 `transcript` 持久化(SessionID `exp%d-planner` / `exp%d-worker-i%d`,planner.go:441-447 / worker.go:94-96)。

### B.1.2 工具面清单

- **通用 SDK 工具**(所有 agent 固定):Read/Write/Edit/MultiEdit/LS/Glob/Grep/Bash(`actool.DefaultTools()`,planner.go:373-375 注释;toolcatalog.go:30-33 说明其不入 DB 目录)。Bash 子进程默认注入 HTTP(S)_PROXY/ALL_PROXY + 各生态 CA 环境变量走 MITM 记录代理(worker.go:204-224 `proxyEnv`)。
- **planner 域工具**(`agent/tools.go:2033-2053`):graph_overview、list_findings、list_facts、node_detail、expand_digest、get_worker_output、get_worker_trace、search_all_worker_traces、list_goals、add_intent、prove_goal、goal_met(默认不绑任何 agent,toolcatalog.go:52-59)、kill_work、steer_work、report_finding、list_companies、list_assets、add_company_scope、add_task_scope、list_untested_assets。
- **worker 域工具**(`agent/tools_insert.go:644-661`):list_findings、report_finding、record_fact、insert_assets、list_assets、search_all_worker_traces、get_worker_trace、node_detail(明确不给 list_facts/list_companies——跨 work 复盘是规划职责)。
- **mainagent 域工具**(`agent/tools_insert.go:664-682`,人在环路):读侧同 planner + add_hint、add_intent、steer_work、set_goals、set_constraints、insert_assets、add_company_scope、list_assets、add_finding、record_fact、add_task_scope、list_untested_assets。
- **流量三件套**:traffic_search/traffic_get/traffic_blob(录制开启时注入,worker.go:250-255),先查流量不重复 curl。
- **联网**:WebFetch(走记录代理 + 信任其 CA)、web_search 四后端 ddgs/brave-free/tavily/deepseek(worker.go:28-40)。
- **扩展**:MCP(`mcphttp/client.go`,Streamable HTTP + 旧版 SSE)与 skills(`skills/api-recon|playwright-cli|scopesentry`,agentskills.io 格式);ScopeSentry 资产同步(README:57-63)。
- **治理外壳**:所有域工具开机播种进 DB `tools` 表(`agent/toolcatalog.go:63` `BuiltinToolSeeds`),运行时 `ToolResolve` 按 agent 绑定过滤、可覆盖描述/schema/参数默认值——handler 永远在代码层,DB 改不了行为(toolcatalog.go:14-15)。

### B.1.3 知识与记忆机制

- **双图是主记忆**:资产图(全局真值库:root_domain/subdomain/ip/service/app/endpoint,归属公司)+ 探索图(每任务:goal/intent/fact/finding/hint,spawns/derived_from/yields/proves 血缘边),两图靠 `exploration_anchors` 相连(README:354-390)。worker 只提交原始信息,父子关系与去重 key 由程序计算。
- **冷热分层压缩**:`agent/compaction.go`(cold-digest)— planner 每轮 maintain(纯 SQL 打冷标),后台 minor/major 用 LLM 把连续冷节点折叠成 digest, `expand_digest` 可还原;提交期活性复查防 digest 覆盖复活节点。
- **过程级交换**:worker 之间用 search_all_worker_traces / get_worker_trace 复用彼此执行过程中的观察(README:419-426),信息以"执行过程"为粒度流动而边界不变。
- **SDK 级**:`norma/memory`(markdown+frontmatter 文件型长期记忆,MEMORY.md 索引,user/feedback/project/reference 四类,按查询相关性注入)、`norma/compaction`(上下文窗口自动压缩)、experimental noa 压缩(planner.go:68-71)。

### B.1.4 发现:从产生到确认

1. **产生**:worker 只有"本次真实触发、拿到可复现证据"才许 `report_finding`(worker.go:240 提示红线:版本指纹匹配 CVE、参数看起来可注入等一律不许报,嫌疑走 record_fact confidence=inferred)。返回双 ID:finding_id(独立漏洞记录)/ finding_node_id(探索节点)。
2. **证据链**:`agent/finding_workflow.go:25` `findingWorkflowTools`——reporter agent 在写报告前核对并 `bind_finding_traffic` 把流量包按 baseline/proof/verification/supporting 绑到漏洞上(finding_workflow.go:76-78 注入的报告前自动关联指引);`update_finding_report` 带 evidence_version。
3. **确认/复测**:预置 retester 会话 agent(`agent/retester.go:4` 提示词):先 `get_finding_retest_context` 读漏洞/原证据/PoC/原任务约束 → 最小化针对性验证 → `record_finding_retest_result`(reproduced/fixed/inconclusive 三值);会话成功且 fixed 时系统自动把漏洞处置状态改"已修复",其余保留(`server/finding_retests.go`,README:266-274)。同一漏洞复测中复用会话。
4. **全链审计**:每步 activity 落库(engine.go:640-699 emitActivity/appendActivity),Bash/HTTP 全程留痕于 MITM 代理。

### B.1.5 预算与范围控制

- **预算**:worker 有 maxTurns(轮次)与 runTimeout(墙钟,worker.go:66-69);任务级 timeout 由 deadline 协调器收尾;命中预算不硬杀——SDK 强制跑一轮 settlement 收尾(`settleWrapUpPrompt` worker.go:154:"先写回 insert_assets/record_fact/report_finding 再总结"),意图标 exhausted(`agent/terminalreason.go:36`);收尾轮自身还有独立轮数预算(`agent/wrapup.go:34` wrapupTurnDefaults)。planner 无自身墙钟,有 deadline 夹逼(planner.go:398-404)。
- **范围**:`agent/goals.go:53-67` goalsScopeTail——目标分解器从任务描述抽最小资产范围(URL→完整主机名 kind=subdomain,严禁把子域缩成根域);`agent/constraints.go:14-48` allow/deny 操作约束以最高优先级块注入 planner/worker 系统提示,越界资产记 out-of-scope 事实跳过;`add_task_scope` 定覆盖度分母,`list_untested_assets` 给补测视角。
- **执行门**:`guard/guard.go`(每个工具调用过 PreToolUse 钩子,审计日志 + 失败归因)+ `intercept/intercept.go`(DB 规则,allow/deny/**ask** 三动作;ask 挂起 intercept_pending 等人经 API 决定,intercept.go:1-11)。

## B.2 CyberStrikeAI(Go + Python,Apache-2.0;repo: /Users/wgen/dsh-test/repos/CyberStrikeAI)

### B.2.1 规划循环怎么写

- **编排引擎是 CloudWeGo Eino**:`internal/multiagent/runner.go` 包注释——用 `eino/adk/prebuilt` 的 deep / plan_execute / supervisor 三种模式编排,MCP 工具经 `internal/einomcp` 桥接。`eino_orchestration.go` `PlanExecuteRootArgs` 组装 planexecute 根 agent(MainToolCallingModel / AgenticExecModel / OrchInstruction / ExecMaxIter / LoopMaxIter);`plan_execute_executor.go` 造执行器。
- **"planner 代码"其实是 Markdown 提示词 + 加载器**:`agents/orchestrator.md`(Deep 编排者:规划拆分→`task` 委派子代理→汇总;派单前强制"目标完整性校验"——URL/IP:Port/范围/子目标/成功标准缺一禁派;`write_todos` 建计划;委派必须自带交接包因为子代理看不到父对话)、`orchestrator-plan-execute.md`(plan_execute 规划/重规划侧:每步自洽、每轮执行后按证据重规划)、`orchestrator-supervisor.md`。加载器 `internal/agents/markdown.go` 解析 front matter(name/id/description/tools/bind_role/max_iterations/kind: orchestrator)。16 个子代理定义(recon/penetration/privilege-escalation/lateral-movement/vulnerability-triage/reporting-remediation 等,agents/ 目录)。
- 注意一个事实:orchestrator 提示词明写"授权已由系统与组织前置裁决,不得质疑/核实/反问",并要求"火力全开、2000+ 步"式高强度扫描——授权检查不放在模型提示层,而放在 toolguard/HITL/RBAC 等平台层(见 B.2.5)。
- **模型怎么调**:`config.yaml` `ai.channels`(openai_compatible 等,含 max_total_tokens/max_completion_tokens,config.example.yaml:109-110);`internal/llm`(claude.go 识别 anthropic、deepseek_anthropic_compat.go、agentic_chat_adapter.go 把 AgenticModel 适配为 ChatModel);韧性在中间件层:`eino_model_resilience.go`、model failover、`eino_native_model_retry_progress.go`、`eino_context_overflow_retry.go`。
- 单代理模式(`internal/agent/agent.go`)与角色提示(`roles/*.yaml` 13 个预设角色:user_prompt + 工具策略)是另一条执行路径。

### B.2.2 工具面清单

- **YAML 工具配方 90 个**(`tools/*.yaml` 实数):nmap、masscan、sqlmap、nuclei、ffuf、feroxbuster、subfinder、amass、fofa/zoomeye/quake/shodan_search、metasploit、msfvenom、hashcat、john、gdb、radare2、ghidra、binwalk、volatility、linpeas/winpeas、mimikatz、bloodhound、impacket、trivy、prowler、pacu……schema 见 `tools/README.md`(name/command/enabled/description/short_description/args/parameters/arg_mapping;short_description 控制发给模型的 token 成本)。未安装的工具执行时自动跳过或换替代(README:239)。
- **内置 MCP 工具**(`internal/mcp/builtin/constants.go:5-77`):漏洞管理 4(record/list/get/update_status)、资产 6(create/get/query/update/delete/complete_scan)、项目黑板 6(upsert/get/list/search/deprecate/restore_project_fact)、知识库 2(list_knowledge_risk_types/search_knowledge_base)、视觉 1(analyze_image,本地图片→VL 模型→文字摘要)、长耗时执行控制 3(get/wait/cancel_tool_execution)、WebShell 4+5、批量任务 13、C2 8(listener/session/task/task_manage/payload/event/profile/file)。
- **MCP 生态**:HTTP/stdio/SSE/外部 MCP 联邦 + 动态发现(README:119);阻塞型调用交 worker、agent 只有限等待,单 server 熔断 + 并发限制(README:120)。`mcp-servers/` 自带 pent_claude_agent、reverse_shell。
- **Skills**:`skills/` 26 个技能目录(attack-surface-recon、active-directory-attack、ai-llm-app-attack、cloud-attack-methods、initial-access-phishing、blockchain-contract-attack 等),SKILL.md 渐进式按需加载。
- **插件**:Burp Suite 扩展 + Chrome/Edge DevTools 扩展,把代理流量回传平台做 AI 辅助测试(README:149-160)。

### B.2.3 知识与记忆机制

- **RAG 知识库**:`knowledge_base/` 漏洞方法论 markdown(按类分目录:SQL Injection 各方言、Prompt Injection 等)→ `internal/knowledge`(index_pipeline 索引、eino_retrieve_chain 检索链、rerank_http 精排、retrieval_postprocess 后处理、eino_sqlite_indexer 向量索引),模型经 `search_knowledge_base` 取"方法论"线索。
- **项目黑板(跨会话事实记忆)**:`internal/project/blackboard.go` `BuildFactIndexBlock` 把 fact_key+摘要(不含 body)注入系统提示;细则"摘要不足必须 get_project_fact(fact_key),禁止凭摘要臆造"(blackboard.go:25-27)。fact 分类 target/auth/infra/business + finding/chain/exploit/poc;与 record_vulnerability 分工:事实记复现全上下文、漏洞记正式 findings(orchestrator.md「项目黑板与漏洞记录(分离)」节)。攻击链建模 `internal/attackchain/`(builder/promote_project)。
- **上下文管理**:`eino_summarize*` summarization 中间件、`eino_skills_reduction`、reduction cache——工具超大输出落缓存、模型视图截断(context_budget.go 注释)。

### B.2.4 发现:从产生到确认

- 模型每**验证**出可复现漏洞立即 `record_vulnerability`(标题/描述/严重程度 critical~info/类型/目标/POC/影响/修复建议);配套 list/get/update_status。
- 状态机含 open/fixed/false_positive/ignored(`internal/database/asset.go:583`);复测走 `internal/database/vulnerability_retest.go`(`UpdateVulnerabilityRetestResult`)。
- 误报治理:黑板事实 `deprecate_project_fact` 或漏洞置 false_positive;审计 Agent 复核 + 决策追踪(README:127)。
- 证据留存:行动证据 + 审计日志 SQLite 持久化;数据库保存与 agent 实际看到的同一份兜底后工具结果(README:131)。

### B.2.5 预算与范围控制

- **迭代预算**:`agent.max_iterations` 全局上限(`internal/multiagent/max_iterations.go`:代码默认 3000,config.example.yaml:160 示例 12000),agents/*.md front matter 可单独覆盖;`plan_execute_loop_max_iterations` 管 execute↔replan 外层循环(默认 Eino 10,config.example.yaml:324-325)。
- **上下文预算**:plan_execute 每步 Result 写入模型视图截 4000 runes、保留最近 8 步(`plan_execute_steps_cap.go`);summarization 触发比 0.8、历史工具结果清理阈值 60000 tokens(config.example.yaml:349-353)。
- **HITL**:全局白名单免审 + 会话级审批模式(off/approval/review_edit)、审批方 human 或 audit_agent、等待时限(config.example.yaml:186-194);审计 Agent 用内置 Jev 政策六问(`internal/hitl/jev.go`:可用性毁坏/不可逆数据丢失/凭据与 ACL 变更/配置篡改/授权 payload/违反操作员政策,reject 阈值 0.55,jev.go:13-22),组织可叠加自有政策。
- **调用拦截**:`internal/toolguard/toolguard.go` 工具名+参数正则规则(上限 100 条),默认启用政府域名(gov)保护拦截。
- **平台 RBAC**:`internal/security` + audit——多用户、系统/自定义角色、权限 Scope、资源归属、显式授权(README:129)。

## B.3 两仓挖洞能力构成对照

| 维度 | ARTEX | CyberStrikeAI |
|---|---|---|
| 驱动方式 | 常驻引擎,任务一发自主跑闭环(事件驱动 planner/worker) | 用户对话/编排发起,Eino 三模式(deep/plan_execute/supervisor) |
| 规划载体 | Go 代码 + planner 提示词(planner.go:298)+ 跨唤醒 TodoStore | agents/*.md 提示词 + Eino adk prebuilt 编排 |
| 状态记忆 | 双图(资产图+探索图)+ 冷节点 digest + 过程级 trace 交换 | 项目黑板(fact_key)+ RAG 知识库 + summarization |
| 工具面 | SDK 八件套 + 图工具 ~30 + traffic 三件套 + MCP/skills(3) | YAML 配方 90 + 内置 MCP ~50 + skills 26 + Burp/浏览器插件 |
| 发现确认 | report_finding 双 ID → reporter 绑流量 → retester 复测(fixed 自动流转) | record_vulnerability → 状态机(open/fixed/false_positive)→ retest + 审计 Agent |
| 预算 | maxTurns+runTimeout+任务 deadline,settlement 收尾保写回 | max_iterations(默认 3000/示例 12000)+ loop 上限 + 上下文 token 预算 |
| 范围 | goals 最小范围抽取 + allow/deny 约束注入 + intercept ask 门 | 提示词层不设授权检查(前置裁决),靠 toolguard/HITL/RBAC 平台层 |

## B.4 残留不确定点(明说,不猜)

- ARTEX 的 `norma/` 是从 Go module proxy 恢复的 v0.4.3 快象(go.mod replace 指令),上游已闭源——本报告对 norma 内部只读到包级注释与 ARTEX 侧调用点,未逐行核验 SDK 循环细节。
- CSAI 的 deep/supervisor/plan_execute 三模式运行时差异只核到编排组装层(`eino_orchestration.go`/`plan_execute_executor.go`),未逐个跑通验证。
- multica 容器内未做任何 exec 探查(保持只读);源码结论仅基于公开仓库文档摘录,未 clone 上游核对源码本体。

# multica 源码级考证:探隐与它的关系该怎么定(C-6 呈批依据)

> 调查日期:2026-10-18。对象:github.com/multica-ai/multica,浅克隆+blob 过滤,HEAD `18fa9f7`(MUL-8050)。
> 方法:按需 `git sparse-checkout add` 取源(许可证/治理/daemon/agent/迁移/插件合同等 ~15 个目录),只读源码 + 只写本档。
> 纪律:结论一律带 文件:行号;没读到的不写,不确定的明说。前置阅读:`docs/research/engine-parts-artex-csai-multica.md` A 章(活体形态勘察,本档不重复)。

---

## 0. 结论速览

| 问题 | 一句话答案 |
|---|---|
| 许可 | **不是 OSI 开源**。Apache-2.0 全文 + Part I 四条附加条件:托管/嵌入商用限制(1a)、UI 品牌锁定(1b)、无界面署名(1c)、两授权分离(1d);贡献条款允许版权方随时改严或改宽(2a) |
| 它是什么 | "派单台 + 账本":Go 服务端 + 每机 daemon,daemon 经 26 种 agent CLI 适配器在本机拉起执行器;自身零模型、零安全件 |
| 安全语义 | **本体确实没有**(六无判决成立,见 §3.1);治理全靠 prompt 级 runtime brief + RBAC + 留痕 |
| 用户的红队工作流 | 「安全红队-队长」= agent.instructions 注入 brief + squad.leader;「授权八问」= 纯 prompt 级 gate + blocked + wakeup;「gencpt 技能」= skill/agent_skill 表 → 落盘 provider 技能目录 |
| 探隐挂接缝 | 账本=task_message+task_usage(现成);执法=插件 event-hook+scopes / 或 runtime 侧自治(dsh 模式);复测=condition wakeup(--until-*) |
| C-6 建议 | **C1(探隐当 runtime、说 dsh 兼容 JSONL 协议、custom runtime profile 零改动入驻)为主,B 轻量并行**;A 仅作 fallback。详见 §5 |

---

## 1. 许可精读(LICENSE 333 行 + NOTICE 14 行,全读)

### 1.1 结构

整个 LICENSE 文件自称 "Multica License":Part I(附加条件)+ Part II(逐字嵌入的 Apache-2.0 全文)合为一个条款集合,两部分单独不授予任何权利(LICENSE:3-9)。冲突时 **Part I 优先**(LICENSE:114)。再分发必须交付完整文件,只给 Part II 不算满足(LICENSE:116-118)。版权方:Index Labs (Hong Kong) Limited(LICENSE:15-16,120);商用许可与品牌豁免走 multica.ai/contact-sales(LICENSE:17-18)。

### 1.2 Part I 四条附加条件逐条

**(1a) 托管/嵌入商用限制**(LICENSE:20-47)——核心限制:
- 无商用许可,不得用 multica 源码 **向第三方提供托管服务**,或 **将 multica 作为出售/许可/商业分发给他人的产品或服务的组件嵌入**(LICENSE:24-28);
- 免费托管也算:对组织外用户公开可访问的实例,即使免费、无广告、无付费层,也要商用许可(LICENSE:33-37);
- **单一组织内部使用(含多 workspace)不需要商用许可**(LICENSE:38-39)——自部署红队工作台完全落在此豁免内;
- 发布源码(含 fork 公开)本身不是托管服务、不需商用许可,但接收方各自要运营托管仍需自行取得商用许可(LICENSE:40-47)。

**(1b) 品牌条款**(LICENSE:49-71):
- 无书面品牌豁免,不得移除/修改 Multica LOGO、产品名、UI 上的版权与署名信息(LICENSE:49-52);
- "Multica user interface" 被 **定义性枚举**为 `apps/web`、`apps/desktop`、`apps/mobile`、`packages/views`、`packages/ui` 中的 UI 代码、前端容器镜像及由其构建的桌面/移动应用,且枚举是示例性的——改目录名、抽取到别的仓库仍然覆盖(LICENSE:54-66);
- **明确豁免无界面使用**:只跑 `server/` 后端、daemon 或 CLI 而不分发/运营任何 Multica UI 的,1b 不适用,只受 1c 约束(LICENSE:67-71)。

**(1c) 无界面署名**(LICENSE:73-79):再分发或运营建立在 multica 后端/daemon/CLI 之上、且不带 Multica UI 的产品或服务,必须保留源码与 NOTICE 中的全部版权/专利/商标/署名通知,并 **在面向用户的文档中声明"built on Multica" + 链接 github.com/multica-ai/multica**。

**(1d) 授权分离**(LICENSE:81-87):品牌豁免≠商用许可,商用许可不自动豁免 1b/1c,两者须分别明示取得,不得从沉默或合并贡献推断。

**(2) 贡献条款**(LICENSE:89-98):提交贡献即同意 (a) **版权方可以视需要把本许可调严或调宽**;(b) 贡献代码可用于其商业用途(含云业务);(c) 贡献按 Multica License 整体提交,不是单独按 Part II。——上游许可能单方面变严,是长期依赖的最大法律风险点。

**(3) 组合与再分发**(LICENSE:100-118):见 1.1。Part II 的 Apache-2.0 原文含 §4(d) NOTICE 传递与 §6 商标不授权(LICENSE:270-273)——"Multica" 名称只可用于描述来源,不得用于暗示背书的自有命名。

NOTICE(NOTICE:1-14)是标准署名文件:版权行 + "distributed under the Multica License" 一句 + 指回 LICENSE;本身不改许可。

### 1.3 三种关系各自的法律影响

| 关系形态 | 触发条款 | 法律后果 |
|---|---|---|
| **探隐作为 multica 的一种 runtime 被驱动**(探隐 CLI 被 daemon 拉起) | 不构成衍生作品 | dsh 先例:适配器在 multica 代码里,协议在 runtime 自己手里(dsh_profile.go:21-28)。探隐侧代码 **零义务**;multica 侧若改其源(适配器),内部用免费(1a 豁免),再分发须交完整许可文件(3d)+ 若带 UI 守 1b / 无界面守 1c |
| **探隐驱动 multica**(把 multica 后端/daemon/CLI 作为探隐产品的组件或托管底座对外) | **1a 直接命中** | 探隐若商业分发/托管给第三方,须向 Index Labs 购商用许可(免费给第三方用也要);仅内部使用豁免。无界面形态还要 1c 文档署名。品牌 1b 不适用(无 UI) |
| **互相引用**(松耦合:探隐与用户自装的 multica 互操作,探隐源码不含 multica 代码) | 基本不触发 | 进程级互操作不落入"用源码提供托管/嵌入组件"的文义;保守做法:凡探隐文档/安装向导引导用户装 multica,加一句 1c 式声明成本极低。商标上避免"Multica-XX"式命名(Apache §6) |

### 1.4 一句话定性

它是 **source-available / "公平源"式许可,不是开源**:OSI 第一到第六项里违反 field-of-use(托管限制)。对内部红队用途完全免费;对"把 multica 装进探隐卖"这条路线设有明确的付费墙与谈判点。

---

## 2. 治理层解剖(只谈机制)

### 2.1 代码版图

| 层 | 位置 | 职责 |
|---|---|---|
| Go 服务端 | `server/internal/`(47 个子包,1504 文件) | REST(Chi)+ WebSocket、sqlc 生成查询(`server/pkg/db/queries/*.sql`)、1214 个迁移 |
| daemon | `server/internal/daemon/`(252 文件,`daemon.go` 10624 行) | 每机常驻:探测 CLI→注册 runtime→WS 领任务→准备执行环境→拉起 CLI→流式回报 |
| 适配器 | `server/pkg/agent/`(217 文件,每 CLI 一个 `.go`) | `Backend` 接口实现 + per-CLI 协议翻译 |
| 协议 | `server/pkg/protocol/`(claim/events/messages) | server↔daemon↔web 三方消息契约 |
| TS 共享域 | `packages/core/`(519 文件) | 前端域模型(agents/skills/有效访问等) |

### 2.2 issue / squad / runtime 模型怎么落码

- **runtime**:`agent_runtime` 表(migrations/002_agent_config.up.sql:16-28):workspace 内 UNIQUE(workspace_id, daemon_id, provider),status online/offline,metadata JSONB。一台 daemon 可以注册多个 runtime;**custom runtime profile**(`runtime_profile` 表,migrations/120_runtime_profile.up.sql:34+)允许 workspace 定义自家包装器(如 in-house Codex wrapper),`protocol_family` 必须是官方支持的家族(CHECK 约束,与 `agent.New()` 开关锁步,agent.go:350-361),`fixed_args` 是进入兼容模式的固定前缀(LaunchPrefix,agent.go:337-346)。dsh 家族由 migration 313 加入(agent.go:358)。
- **agent**:`agent` 表 + `runtime_id` 外键(002);`instructions` 列(migrations/021_agent_instructions.up.sql:1)是用户自由文本——**这就是"agent 指令注入点"的数据落点**;`custom_env`(040)/`custom_args`(041)/`mcp_config`(046)/`model`(050)。
- **squad**:`squad` 表(leader_id → agent,RESTRICT)+ `squad_member`(member_type ∈ {agent, member})+ issue.assignee_type 扩到 'squad'(migrations/084_squad.up.sql:2-31)。队长 agent 领单后改派成员;brief 规定"派单不是交付,父 issue 停在 in_progress,直到后续轮次确认整体目标达成才进 in_review"(runtime_config_sections.go:609)。
- **issue 状态机**:7 个内置状态归 4 个生命周期类(issuestatus.go:27-56):backlog/todo→unstarted;in_progress/in_review/blocked→started;done→done;cancelled→closed。workspace 可自定义状态但只继承生命周期,不继承内建行为(issuestatus.go:207-208)。

### 2.3 daemon 怎么驱动 26 种 agent CLI

注册与领单闭环(CLI_AND_DAEMON.md:302-309,与代码一致):
1. daemon 启动探测 PATH 上的 CLI(`probeAgentCLIs`,agents_probe.go:94;每个 CLI 有 `MULTICA_<NAME>_PATH`/`_MODEL` 覆写,如 dsh 在 agents_probe.go:256);
2. 按 workspace 注册 runtime(`DaemonRegisterPayload{DaemonID, AgentID, Runtimes[]RuntimeInfo{Type,Version,Status}}`,messages.go:236-248);
3. server 经 WS 推 wake 信号(`task:available`),daemon **跨其全部 runtime 一次批量认领**(claim.go:1-8,5s 预算);30s 轮询兜底、15s 心跳;
4. 认领后 `execenv.Prepare` 建隔离 workdir + 写上下文文件(execenv.go:409,563);
5. `agent.New(agentType, cfg)` 按 SupportedTypes 白名单实例化 Backend(agent.go:437-503)。**README 表列 26 个 CLI;SupportedTypes 数 25 个协议家族**(qoder/qoderclicn 共用一个 ACP backend,agent.go:486-487;omp 作为 pi 家族的 builtin 身份另计,agent.go:334-336)。每种协议形态:stream-json(claude/qwen)、app-server RPC(codex)、ACP(hermes/kimi/qoder/grok/mcode/dim/zeroclaw…)、原生 JSON(copilot/opencode)、**版本化 JSONL stdio(仅 dsh)**。

**dsh 适配器 = 探隐入驻的直接样板**(server/pkg/agent/dsh.go,479 行):
- 启动:`dsh --profile multica --stdio`(dsh.go:119-121,225-226);`--profile multica` 是握手前提——源码注释明说 "DSH ships no machine-drivable mode of its own……dsh is the only provider whose integration depends on the user installing something into the agent's own home first"(dsh_profile.go:21-28);
- 命令帧:单条 JSON `{v:1, type:"execute", request_id, cwd, prompt, resume_session_id, model{provider,id}, reasoning_effort, mcp_servers[]}`(dsh.go:54-64,256-260);MCP 只收 stdio 与 streamable-http,拒绝 SSE(dsh.go:181-183);
- 事件帧九种:`ready/runtime=="dsh"`、`session`、`text`、`thinking`、`tool_call`、`tool_result`、`usage`(按 provider/model 聚合四类 token,dsh.go:406-418)、`protocol_error`、`result`(终态+error+resume_rejected)(dsh.go:384-433);
- 探测:`dsh --profile multica --probe` 打一行 `{v,type:"probe",runtime,protocol_version}`,daemon 四态判定 OK/MissingProfile/Incompatible/Unavailable,15s 超时(agents_probe.go:364-427);协议版本不匹配=Incompatible,不覆盖已装 profile(agents_probe.go:383-385 注释);
- 取消三级升级:cancel 帧 → 3s 宽限 → SIGTERM → 2s → SIGKILL(dsh.go:24-25,281-300);
- profile 缺失自愈:操作员设 `MULTICA_DSH_PROFILE_BUNDLE`(npm spec/目录/tarball 候选列表),daemon 跑 `dsh plugin --profile multica add <spec>` 安装,每 daemon 生命周期一次(dsh_profile.go:44,267-308);**multica 自家的 DSH 桥尚未发布 npm(multica#6936,dsh_profile.go:42-43,227-232)**。

### 2.4 指令注入:runtime brief + per-turn prompt(安全语义的真正载体)

两级注入,配合 prompt-cache 优化(变更值不进缓存前缀,MUL-5377):
- **runtime brief**(每次运行写入 workdir):dsh 走 `{workDir}/AGENTS.md`(runtime_config.go:175,218-219),用 HTML 注释标记块包裹、保留用户原文件字节、cleanup 精确回滚(runtime_config.go:31-52,247-275,349-394)。brief 组装自分节 writer(runtime_config_sections.go):Header(43)、Background Task Safety(56)、**Agent Identity——`ctx.AgentInstructions` 原文注入**(66-89)、Requesting User(92)、指令优先级(482-488:"Agent Identity instructions have priority over the issue workflow"),workflow 六步(588+:读 issue→两段式扫评论→先置 in_progress→干活→**产出即评论**→`in_review` 收尾;"`done` stays human" 在 :605)、技能索引(仅名字,~677)、@mention 语义(711)、强制走 multica CLI(766)。
- **per-turn prompt**(`BuildPrompt`,prompt.go:209-274):issue/评论触发/聊天/autopilot/quick-create/wakeup 六型;每轮附 On-behalf-of(授权人)、connected apps、joined wakeups、project workflow 等运行期块(prompt.go:63-75)。
- **环境注入**:agent 子进程拿 `MULTICA_TOKEN`(server 签发、**绑定 (agent,task),绝不回退 daemon 自身凭据**——防冒名,daemon.go:8437-8444)+ SERVER_URL/WORKSPACE_ID/AGENT_ID/TASK_ID 等(daemon.go:181-190);dsh 额外拿 `MULTICA_DSH_SESSION_ROOT` + `DSH_TELEMETRY_DISABLED=1`(daemon.go:8530-8537)。HOME 不动,gh/aws 等继续用宿主凭据(daemon.go:8482-8486)。

### 2.5 审核/验收流(边做边评论 + 人验收)的数据流

1. **边做边评论**:agent 用 task-scoped token 跑 `multica issue comment add --parent <触发评论> --content-file`(prompt.go:240,273;runtime_config_sections.go workflow 步骤 4)→ server comment handler → `comment:created` WS 事件(events.go:22-24)→ 关注者 inbox;
2. **运行中插话(steering)**:人对运行中的 run 回评论 → server 合并为 supplement → daemon 认领后经 `Session.Supplement` 送进 **当前正在进行的 provider turn**(agent.go:160-166;daemon/task_supplement.go;README "Steer a running agent……Claude Code, Codex, and Grok today"——按 backend 能力opt-in);
3. **交付→验收闸**:agent 自己把 issue 置 `in_review`(workflow 步骤 5;命令在 brief :280 教);**`done` 属人**是 brief 层规则(runtime_config_sections.go:605)——未发现服务端对 agent actor 写 done 的硬拦截,勿当作强制不变量;
4. **服务端确实存在的 agent 禁写点**(403 级):系统唤醒规则(issue_system_wakeup.go:191 "agents cannot change platform rules")、属性定义(property.go:404)、快捷动作(quick_action.go:425)、workspace MCP 服务器(workspace_mcp_api.go:133,374)。

### 2.6 token 计量与执行日志回放(真实实现)

- **计量**:Backend 从事件流刮 usage(如 dsh usage 帧,dsh.go:406-418)→ daemon 批量 POST `/tasks/{id}/usage`(`ReportTaskUsage`,daemon.go:4919-4991)→ `UpsertTaskUsage` 落 `task_usage` 表(task_id×provider×model 唯一,migrations/032_task_usage.up.sql:2-14;task_usage.sql:1-25)→ 分析事件(service/task.go:881 `CaptureTaskUsage`)。成本计量有专门设计:provider 自报价以 1e-10 USD tick 整数存储(`CostUSDTicks`,agent.go:240-250;**目前只有 xAI Grok 报**,daemon.go:4901-4904),其余走费率表估算。
- **执行日志**:daemon 每 500ms 批量 POST 消息(`ReportTaskMessages`,daemon.go:5137;注释:"fires every 500ms for every running task……hottest write path")→ **写库前 redact.Text/InputMap 掩密**(daemon.go:5203-5205,pkg/redact:redact.go:1-60+,AWS/GitHub/OpenAI/Slack/GitLab/Google/Stripe 等 12+ 种模式)→ 单语句批量插 `task_message`(seq 有序,migrations/026_task_messages.up.sql:2-12)→ WS `task:message` 实时广播(protocol messages.go:216-234)。**回放** = `ListTaskMessages`(daemon.go:5452)按 seq 读全量,tool_use/input/tool_result/output 带截断三态标记(`output_truncated`,messages.go:228-232)。运行失败有五类 watchdog(idle 2h/tool/semantic/first-turn/handshake,CLI_AND_DAEMON.md 配置表)与 lease/reclaim 重试(service/task.go:201-233)。

---

## 3. 安全语义从哪来

### 3.1 六无判决:成立(逐项核销)

全库检索 redteam/penetration/pentest/vulnerab/CVE/exploit:server 与 packages/core **零命中**(仅 examples/plugins 里有 incident-response 示例技能)。multica 本体没有的六件东西:

| # | 缺件 | 证据 | 它实际有什么(最近替代物) |
|---|---|---|---|
| 1 | 授权/合规 gate | 无任何"开工前审批"原语 | issue 置 blocked + `issue wakeup --event comment.created --filter-actor-type member --filter-actor-id <uid>`(brief :224)——等特定人类说话再醒 |
| 2 | 策略引擎 | 无 policy 求值器 | RBAC(owner/admin/member)+ actor 403(§2.5-4)+ 插件 scopes |
| 3 | 秘密治理 | 无 vault/审批式取密 | 仅输出侧正则掩密(pkg/redact);输入侧凭据原样进宿主 HOME(daemon.go:8482-8486) |
| 4 | 执行沙箱 | 无自有沙箱 | workdir 隔离 + GC(execenv.go:563-600);Codex 沙箱是 codex 自家配置的接线(execenv/codex_sandbox.go) |
| 5 | 验证/复测原语 | 无"验收测试"概念 | condition wakeup(--until-status/--until-pr checks/--until-children-done)+ autopilot cron——是调度,不是验证 |
| 6 | 安全域逻辑 | 无漏洞/风险/资产模型 | 全部安全语义外置到用户自写内容(instructions/skill) |

### 3.2 用户三 constructs 在源码里的对应机制

- **「安全红队-队长」**(活体见 engine-parts A.2)= 三个机制的叠加:①`agent.instructions`(migration 021)→ runtime brief 的 Agent Identity 节 **原文**注入(runtime_config_sections.go:66-89),且声明优先于 workflow(482-488);②若组队,`squad.leader_id`(migration 084)+ 队长"派单非交付"规则(:609)+ squad no_action 路由(service/squad_no_action.go);③"不执行渗透"靠 Instruction Precedence 的 **prompt 级**约束——没有执行层强制。
- **「授权八问 gate」**= 纯 prompt 工程:队长 instructions 要求八问不全 → 置 blocked → wakeup 等授权人评论。**server 没有"待授权"这个一等状态,也没有派单拦截器**——任何 agent 理论上都可直接开跑;gate 的强度=指令服从度。
- **「gencpt 技能」**= `skill`/`skill_file`/`agent_skill` 三表(migrations/008_structured_skills.up.sql:4-30)+ 161 加 per-agent enabled + 368 插件所有权;daemon 领单后把绑定的技能 bundle(staged via SkillBundleCache,skill_cache.go)落盘到 **provider 原生技能目录**——dsh 是 `$DSH_HOME/skills`(DSH_HOME 可覆写,local_skills.go:186-190)+ 通用 `~/.agents/skills`(local_skills.go:110-112);brief 只列 **名字索引**(runtime_config_sections.go:677-698),内容靠 CLI 原生发现;聊天里可用 slash 形式显式点名技能(prompt.go:696-726)。技能即"把解过的问题变成所有 agent 复用的剧本"(README)——**技能是内容分发机制,不是权限边界**。

### 3.3 探隐若入驻:账本/执法/复测的接缝

| 探隐部件 | 挂接缝(文件:行号) | 说明 |
|---|---|---|
| **账本**(取证留痕) | `task_message`(daemon.go:5137 写/:5452 读)+ `task_usage`(daemon.go:4919)+ comment/activity 事件流(events.go) | 现成、per-task、seq 有序、写前掩密。探隐作为 runtime 时,tool_call/tool_result 帧自动成为账本行;探隐自有账本(审计级)应留 runtime 侧,multica 的作过程账 |
| **执法**(授权/边界/熔断) | 三层可选:① **dispatch 层**:插件 hook 系统——`multica.plugin.json` v1 的 scopes(issues:read/write、storage、net:host 精确出网域)+ event 触发器(issue.created/issue.status_changed)+ agent 可调 HTTP/MCP 工具(examples/plugins/deploy-sentinel/multica.plugin.json:8-105;合同校验 server/pkg/plugincontract/manifest.go 837 行;agent 侧暴露 daemon/plugin_hook_mcp.go 248 行 + MCP 审批 UI packages/views/plugins/plugin-mcp-approval.tsx);② **prompt 层**:Agent Identity + Instruction Precedence(弱);③ **runtime 层(推荐)**:dsh 模式——"DSH owns the agent loop, session store, model catalog, tools, and MCP clients"(dsh.go:28-31),探隐 CLI 自己拒绝越权工具调用,且 cancel 三级升级(dsh.go:281-300)给 daemon 一条标准熔断通道 |
| **复测**(回归验证) | condition wakeup:--until-status/--until-pr checks/--until-children-done(brief :224;service/issue_wakeup_condition.go)+ autopilot cron(README "standups, audits, and reports on a cron") | "等某事实成立再醒"是 server 端求值的;探隐可发 wakeup 表示"等我的复测结论",但复测本体在探隐侧 |

---

## 4. 与前判(六无)的差异修正

engine-parts A.4 的活体观察全部得到源码确认,两处需精化:
1. "完成进审核中→人验收才合并"——**`done` 只属人是 brief 教的,不是服务端硬约束**(runtime_config_sections.go:605;服务端硬 403 仅限 §2.5-4 列的四个管理面)。以 multica 做"人验收闸"时,验收强度依赖使用纪律,探隐不应把它当信任边界。
2. "26 种 runtime"准确表述:26 个 CLI / 25 个协议家族 + builtin 身份(omp),且 **custom runtime profile 允许任意同协议包装器零代码入驻**(migration 120;agent.go:323-347)——这是探隐最省的入口。

---

## 5. C-6 呈批件:三选一

### 方案 A:只当参照(不部署、不集成)

- **内容**:本档 + engine-parts A 章即为产出;借鉴其 brief 分节结构、执行日志/用量账本、探针四态判定、cancel 升级、prompt-cache 前缀纪律等工程模式。
- **利**:零耦合、零许可暴露、零运维;探隐叙事完整自持。
- **弊**:放弃现成的派单-留痕-回放面板;用户已在自部署实例上跑了红队小队与 gencpt 流水线,参照方案不承接这些存量。
- **许可影响**:无。
- **工程量**:0。

### 方案 B:multica 纳为探隐的宿主之一(治理面板用 multica,执行仍用探隐自管 runtime)

- **内容**:探隐的安全验证项目在 multica 板上开 issue/squad;技能表挂 gencpt 类剧本;执法以插件实现(hooks+scopes+MCP 审批);复测用 wakeup/autopilot;探隐引擎经自家通道执行,结果回帖。
- **利**:内部使用完全免费(1a 豁免);治理 UI/账本/回放/用量白得;插件 scopes 的出网白名单(net:host)与 MCP 审批 UI 是现成的执法素材;用户存量工作流无缝续跑。
- **弊**:①执法与授权仍主要在 prompt/dispatch 层,multica 不提供执行层强制(§3.1),探隐须自带;②上游依赖:许可可单方变严(2a)、接口随版本漂移(此 HEAD 一周内即有 MUL-8050 级变更),需跟踪;③若探隐日后把 multica 打包进商业发行版/托管,**1a 触发,须购商用许可**(这是 B 的天花板)。
- **许可影响**:内部 = 免费且无需品牌合规(无界面路径 1b 明确豁免);商业化时 1a+1c(文档署名)生效。
- **工程量**:中。技能与 squad 配置 1-2 天;插件(scopes+2-3 hooks+MCP 工具)1-2 周;wakeup 规则 1-2 天;长期跟版。

### 方案 C:探隐当 multica 的 runtime,被 multica 驱动(推荐,且分两条子路径)

- **C1(零改动,推荐)**:探隐 CLI 实现 **dsh 兼容 JSONL stdio 协议 v1**(契约全文在 dsh.go:54-104,376-433:probe 帧、execute 命令、九种事件帧、cancel、--list-models),然后以 **custom runtime profile**(protocol_family=dsh,fixed_args 进 multica 兼容模式)注册——multica 侧 **零代码改动**。同类先例:multica 官方对 DSH 也需用户先装 profile bundle(multica#6936 未上 npm),profile 机制正是为此设计(dsh_profile.go:21-30)。
  - 利:探隐代码零许可沾染(说协议不构成衍生);账本(task_message/task_usage)、steering、watchdog、GC、探针自愈全部白得;执法/复测留在探隐 runtime 内=dsh 模式(dsh.go:28-31),恰是探隐的差异化所在;可逆——撤 profile 即退场。
  - 弊:探隐须长期跟住协议 v1 的兼容面;multica 面板上的安全语义仍靠探隐自己注入(brief Agent Identity 原文透传是通道,runtime_config_sections.go:66-89);探针 Incompatible 判定会拒绝协议漂移的 runtime(agents_probe.go:383-385),升级要同步。
  - 许可影响:探隐侧无;multica 侧无改动。
  - 工程量:**小**。协议实现+测试 ≈300-600 行(对照 dsh.go 479 行),3-5 天;profile 注册与自部署实例联调 1-2 天。
- **C2(上游适配器)**:在 `server/pkg/agent/` 写 `tanyinBackend`(≈dsh.go 规模)+ SupportedTypes/launchHeaders/runtimeConfigPath/技能根/探针接线 + 一个加宽 CHECK 的迁移(参照 migration 313 加 dsh 的先例,agent.go:358)。
  - 利:一等公民(原生模型发现、ThinkingLevel、品牌名);对全部 multica 用户可见。
  - 弊:贡献落入 Multica License(条件 2:版权方可改严/改宽、可商用使用);上游合并节奏不受控(数周至数月);自维护 fork 则要跟版。
  - 工程量:适配器 1-2 周 + 上游流程。

### 呈批建议

**主选 C1,允许 B 作为同一实例上的并行治理面板**(两者不互斥:C1 给执行通道,B 给人在回路的项目治理;本机自部署实例与用户存量工作流天然承接)。理由:许可最干净(协议≠衍生,dsh 是活先例)、工程最省(周级)、差异化最保(账本之外的三件——执法/复测/安全域模型——恰恰应该留在 runtime 侧,multica 的架构注释自己就把这些划给 runtime:dsh.go:28-31)。**唯一红线**:不要把 multica 的 UI 或后端再分发/嵌出入探隐发行版(1a/1b 付费墙);探隐文档提及 multica 时保留 1c 式署名一句。若未来需要一等 runtime 地位或原生安全事件面,再评估 C2 与插件深度。

---

## 附:本档引用的源码取用清单

sparse-checkout 取用目录:LICENSE/NOTICE/根文档、server/internal/{daemon(含 execenv),daemonws,handler,issuestatus,issueworkflow,issueguard,service,skill}、server/pkg/{agent,protocol,redact,plugincontract,skillbundle,db,migrations}、examples/plugins、packages/plugin-sdk。全部只读;工作树位于 .research/repos/multica,未做任何写操作。

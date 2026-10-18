# Multica 全量能力清点(源码级)

- **对象**: github.com/multica-ai/multica @ HEAD `18fa9f7`("MUL-8050: price Cursor runtime catalog variants (#9295)")
- **本地源位置**: `/Users/wgen/redteam-agent/.research/repos/multica`(sparse+shallow clone,HEAD blob 全量本地;分析用只读导出 `git archive HEAD` → /tmp/multica-src,仓库本身零改动)
- **任务给定路径更正**: `/Users/wgen/dsh-test/repos/multica` 不存在;实际源在上述路径(已报 parent 并获准按源码全量口径执行)
- **证据类别戳**(四类,沿 parent 裁定): 【源码】= 直接读 HEAD 源码(行号对应该 commit);【asar】= Multica.app v0.5.1 app.asar 直读;【日志】= ~/.multica/daemon.log 运行时推断;【勘】= ~/multica_workspaces 实勘;【文档】= 仓库文档逐篇读
- **纪律遵守**: multica 仓库只读 ✅;零网络请求 ✅(静态分析,未启动任何服务);未触碰 8900/3000/8787/8443 端口 ✅

---

## 1. HTTP/WS 路由全数

### 1.1 总量【源码】server/cmd/server/router.go(2726 行,全文件扫描)

路由注册 **全部** 位于 router.go(全仓 grep 确认无第二处 chi 注册;handler 文件里的 `.Get(` 均为 `URL.Query().Get` 误匹配)。方法直方图:

| 方法 | 数量 |
|---|---|
| GET | 186 |
| POST | 168 |
| PUT | 32 |
| PATCH | 22 |
| DELETE | 56 |
| **HTTP 端点合计** | **464**(另有 47 个 `r.Route()` 分组前缀,非端点) |

另有独立 pprof 服务 `127.0.0.1:6060`(6 端点,GET/POST /debug/pprof/*,server/internal/profiling/server.go:13-25)。**主 API 路由总计 464 条 HTTP + 2 条 WS = 466**。

### 1.2 四个面(按认证边界)

**① 公开面(无 Multica 会话,~22 条)** router.go:1437-1556:
- 运维: `/health` `/readyz` `/healthz`(1437-1439)、`/health/realtime`(1450,REALTIME_METRICS_TOKEN 或仅 loopback)
- 用户 WS: `GET /ws`(1463,realtime.Hub,见 §4.3)
- 静态/能力凭证: `/uploads/*`(1474,本地存储时)、`/api/attachments/{id}/signed-download`(1486,HMAC 单附件签名)、`/api/avatars/{sig}/*`(1495)、`/plugin-surfaces/{token}`(1501,加密路径 token)
- 登录: `/auth/send-code` `/auth/verify-code` `/auth/google` `/auth/logout`(1511-1514,IP 限流 5/20 per min)
- 公共配置: `/api/config`(1517)、`/api/contact-sales`(1518)、`/api/share-links/{code}`(1521)

**② Webhook 面(外部签名认证,6 条)** router.go:1526-1544:
- `POST /api/webhooks/autopilots/{token}`(token 即凭证)、`POST /api/webhooks/github`(HMAC-SHA256)、`GET /api/github/setup`、`POST /api/webhooks/vcs/{connectionId}`(Forgejo/Gitea/GitLab)、`POST /api/webhooks/stripe`(Stripe 签名)、`GET /api/integrations/composio/callback`(HMAC state)

**③ Daemon 面(`/api/daemon/*`,DaemonAuth 中间件 = daemon token 或用户 token/PAT,38 条注册=36 唯一端点+2 claim 别名)** router.go:1559-1613:

| 生命周期 | 端点(行号) |
|---|---|
| 注册 | POST /register(1562)、/deregister(1563) |
| 心跳 | POST /heartbeat(1564)、**GET /ws**(1565,daemonws.Hub 控制连接) |
| 发现 | GET /workspaces(1566)、/workspaces/{id}/repos(1567)、/workspaces/{id}/runtime-profiles(1568) |
| 领取 | POST /runtimes/{id}/tasks/claim(1578)、/tasks/claim(1582,规范批量)、/claim(1583,过渡别名)、GET /runtimes/{id}/tasks/pending(1586) |
| 准备 | POST prepare-lease(1584)、skill-bundles/resolve(1585)、tasks/{id}/session(1612,PinSession) |
| 执行上报 | GET status(1592)、POST start(1593)、progress(1597)、complete(1598)、fail(1599)、usage(1600)、messages POST/GET(1601/1602)、cancel-ack(1603)、wait-local-directory(1596) |
| 补充输入 | supplements/claim(1594)、supplements/{commentId}/ack(1595) |
| 插件 | tasks/{id}/plugin-hooks(1573)、plugin-mcp/{cid}/credential(1576) |
| 后台请求回调 | update/{id}/result(1587)、models/{id}/result(1588)、local-skills/{id}/result(1589)、local-skills/import/{id}/result(1590) |
| GC 协查 | issues/gc-check 批量+单条 4 组(1605-1609)、recover-orphans(1611) |

**④ 用户面(Auth 中间件,会话/PAT/CloudFront cookie,~390 条)**:按资源族分组(全部在 router.go 1656-2482):me/onboarding、cli-token、auth/refresh、upload-file、feedback、attachments、workspaces(成员/邀请/GitHub/VCS/runtime-profiles/mcp-servers/plugins 全 CRUD 1727-1800)、五大 IM 集成(lark/slack/wecom/dingtalk/telegram 安装+binding redeem 1820-1895)、composio、invitations、share-links join、PAT tokens、cloud-billing/cloud-subscriptions(Stripe 计费 1947-1980)、search-index、**issues(60+ 子端点:comments/timeline/wakeups/task-runs/reactions/labels/metadata/properties/PR 2002-2075)**、quick-actions、properties、labels、issue-statuses、issue-workflows、projects、squads、autopilots(webhook 触发器+deliveries 2176-2199)、pins、issue-views、agents(含 skills/mcp-servers/env 绑定 2253-2292)、agent-builder、skills、dashboard、**runtimes(usage/update/models/local-skills 2341-2369)**、cloud-runtime(节点 exec 2375-2386)、chat sessions(messages/pending-task/queued-tasks/draft-restores 2413-2445)、inbox、notification-preferences。

**插件 API 双面**: 公共 Plugin Action API(`/v1`(publicapiv1.BasePath),mpi_/mpc_ bearer-only,9 端点:context/issue/comments/storage,router.go:105-115+1619-1627) + 浏览器会话桥(`/api/plugin-bridge/v1` 同 9 端点 + POST /hooks/{key},1633-1641)。路径常量在 server/pkg/publicapi/v1/routes.go。

### 1.3 WebSocket 端点与帧类型

**A. 用户实时 WS `GET /ws?workspace_id=|workspace_slug=`**【源码】internal/realtime/hub.go:798-917:
- 认证: cookie(Authorization 同源)或**首帧 token**;首帧认证成功回 `{"type":"auth_ack"}`(879-888);成员资格 DB 校验;Origin 白名单(3000/5173/5174 dev,router.go:54-58)
- 出站帧 = protocol/events.go 全部 **80+ 事件常量**(issue:created/updated/deleted、comment:*、task:queued/dispatched/running/waiting_local_directory/progress/completed/failed/message/cancelled、chat:message/done/quick_actions/cancel_finalized/session_*、inbox:*、workspace:*、agent:*、autopilot:*、五 IM installation:* 等,events.go:4-224)
- 入站:仅 token 认证帧 + pong;订阅粒度 = workspace 房间(scopeKey)

**B. Daemon 控制 WS `GET /api/daemon/ws`**【源码】internal/daemonws/hub.go(1164 行)+ pkg/protocol:
- 帧类型 9 种(protocol/events.go:152-174): `daemon:register`、`daemon:heartbeat`/`daemon:heartbeat_ack`(镜像 HTTP 语义,payload=protocol/messages.go:400-431)、`daemon:task_available`(内容无关唤醒提示)、`daemon:task_supplement_available`、`daemon:runtime_profiles_changed`、`daemon:workspaces_changed`、`daemon:pending_work`(model_list/local_skills/import 提示)、`daemon:rpc_request`/`daemon:rpc_response`
- **WS-first claim(MUL-4257)**: daemon 经 rpc_request 调 `tasks.claim`,server 端 DaemonRPCHandler 用**内存 http.ResponseWriter 复用同一 HTTP handler**(handler/daemon_rpc.go:45-52,仅此 1 个 RPC method),HTTP 端点为回退(client.go:317+)
- 连接时能力协商: 15 个 DaemonCapability 常量(skill-bundles-v1/rpc-v1/claim-poll-hints-v1/local-worktree-v1/task-supplement-v1/platform-skill-v1/checkout-keeps-work-v1/joined-wakeups-v1 等,protocol/messages.go:5-88)

---

## 2. 目录全件

顶层 14 目录 + 根文件(git ls-tree HEAD)【源码】:

| 目录 | 职责(一句) |
|---|---|
| server/ | Go 单体后端:cmd/{server,multica,migrate,maintenance,4×backfill_*}、internal(30+ 包)、pkg、migrations(582 个 up)、sqlc.yaml |
| apps/web/ | Next.js 16 前端(port 3000,@multica/web 0.6.3,fumadocs 文档站内嵌) |
| apps/desktop/ | Electron 桌面客户端(electron-vite,main/preload/renderer,内嵌 resources/bin/multica daemon 二进制)【asar】 |
| apps/mobile/ | Expo/React Native 移动端(@multica/mobile 0.1.0,expo-router) |
| apps/docs/ | fumadocs 文档站(独立 Next app,port 4000) |
| apps/ui-lab/ | UI 组件试验场(vite) |
| packages/plugin-sdk/ | 插件开发 SDK(与 server/pkg/plugincontract 对应) |
| examples/plugins/ | 5 个示例插件(hello-panel/triage-notify/release-checklist/schedule-pulse/deploy-sentinel) |
| docs/ | 工程文档(4 篇 md + assets) |
| e2e/ | Playwright E2E(auth/comments/chat/agent-mcp 等 spec) |
| scripts/ | CI/构建脚本(check-*.mjs、ci-scope) |
| deploy/helm/ | K8s Helm chart |
| docker/ | 容器 entrypoint |
| .github/ .agents/ | CI workflows / agent 指引 |

**server/internal 包逐个**(主文件已看): handler(HTTP 处理器,daemon.go 5000+ 行为最大)、daemon(本地 daemon 全实现,138 文件,daemon.go 10624 行)、daemonws(服务端 daemon WS hub)、dispatch(任务分发)、scheduler(wakeup 调度)、service(任务状态机 task.go + 插件/唤醒/配额)、realtime(用户 WS hub)、integrations(lark/dingtalk/slack/wecom/telegram/composio/ghsnapshot 各成子包,均含 ws_connector 长连接)、issueguard/issuestatus/issueworkflow(看板域)、skill(技能 frontmatter/binary)、auth、middleware、storage(local/s3)、cloudruntime(云执行节点)、seatcapacity、selfhosttelemetry、selfexec、analytics、events(进程内事件总线)、featureflags、metrics、entitlement、inbox、taskusagebackfill、testutil、util(secretbox/redact)。
**server/pkg**: agent(26 个宿主 agent 适配器,§7)、db/generated(sqlc,67 查询文件/148 表)、protocol(daemon 线协议)、plugincontract、publicapi/v1(稳定 API contract+spec)、remotemcp(远程 MCP OAuth)、composio、llm、featureflag、redact、skillbundle、taskfailure(失败分类学)、dbid、awakeclock(防系统睡眠误判)、eventcontract。

---

## 3. Daemon 体系全机制

**一句话**: daemon 是跑在用户机器上的 Go 常驻进程,启动时探测 26 种 agent CLI 并按 workspace 注册为 runtime,然后经 WS 控制连接 + 批量 claim 领任务,在 `~/multica_workspaces` 下为每个任务准备隔离 git worktree 环境、以子进程拉起对应 agent CLI 并把流式结果/用量/终态回传 server,server 持有唯一权威状态机。

### 3.1 注册(Registration)【源码】
1. CLI 登录(`multica login` 浏览器/PAT,cmd/multica/cmd_login.go)→ daemon token 持久化 ~/.multica
2. daemon 启动 `Run→run`(daemon/daemon.go:2029-2156): resolveAuth(2183)→ detectBuiltinRuntimes(2700,探测 PATH 上 26 CLI 的 `--version` + dsh 专属 profile 探测)→ 逐 workspace registerRuntimesForWorkspaceLocked(2818;POST /api/daemon/register)
3. `agent_runtime` 表 UNIQUE(workspace_id,daemon_id,provider)(migrations/004_agent_runtime_loop.up.sql:1-14);注册响应原地合并(applyRegisterResponseInPlace,1461)
4. workspaceSyncLoop(4074)周期同步 workspace 集合 + runtime_profile 漂移重注册(3753);runtime 行被删 → WS heartbeat_ack runtime_gone=true → daemon 剔除并重注册(protocol/messages.go:410-421)

### 3.2 心跳(Heartbeat)【源码】
- 每 15s/runtime(CLI_AND_DAEMON.md:318),WS 帧与 HTTP POST /api/daemon/heartbeat 同语义;ack 携带 pending 动作: CLI 更新/模型枚举/本地技能枚举/技能导入(messages.go:417-431)
- `daemon:pending_work` 唤醒提示把交互式请求的等待压到一次立即心跳(MUL-5444);handlePendingWorkHint(daemon.go:4558)
- 7 天离线 GC runtime(server 侧)

### 3.3 领取(Claim)【源码】
- pollLoop(5282)+runBatchPoller(5340): WS 首选(HTTP 回退)**一次批量 claim 所有 runtime 的任务**(POST /api/daemon/tasks/claim {daemon_id, runtime_ids, max});默认 30s 兜底轮询、WS 健康时上限 3m(CLI_AND_DAEMON.md:316-317)
- 并发上限 `--max-concurrent-tasks` 默认 20(信号量 waitForTaskSlot,5533);claim 后 StartTask 前 CAS 防重复(errStartClaimRejected,handleTask:5780)
- 唤醒捷径: server 有任务排队 → `daemon:task_available` 帧 → 立即心跳+claim

### 3.4 任务执行(handleTask,daemon.go:5655-5904)【源码】
1. local_directory 资源路径互斥(5724)→ 状态机 dispatched→waiting_local_directory→running
2. envRoot 活动守卫(markActiveEnvRoot,5746;防 GC 误删)
3. 取消监视: 每 5s 轮询 GET tasks/{id}/status,terminal/404 → cancel runCtx(5770)
4. runner.run → execenv.Prepare/Reuse: 隔离工作区 `<workspaces_root>/<ws>/task-<id>` + **裸 repo 缓存 .repos/ + git worktree**(CLI_AND_DAEMON.md:357)+ 每 provider 本地配置覆盖 + 任务简报写 CLAUDE.md/AGENTS.md/QWEN.md(agent.go:32-40)+ MCP config(0600 临时文件或 ACP session/new 注入,CLI_AND_DAEMON.md:431-447)
5. 终态回传: usage(5792)→ complete(output,branch,sessionID,workDir,durableWorkDir)/fail(classified failure_reason)/cancel-ack;GC 元数据最后写(.gc_meta.json,5899)
6. 看门狗体系: 通用 idle 2h/tool watchdog/首 turn 无进度/握手超时/turn-interrupt 2s 等按 provider 可调(CLI_AND_DAEMON.md:319-326);awakeclock 防主机睡眠误判(pkg/awakeclock)
7. GC: 7 类策略(完成清理/孤儿 72h/工件 node_modules 12h/repo 缓存 30d/Hermes 记忆 90d/会话 14d/temp 目录锁存活性,CLI_AND_DAEMON.md:345-365)——【日志】daemon.log 实测 `gc: cycle complete cleaned=2 ... bytes_reclaimed=110023194` ✅

### 3.5 其他机制【源码】
自动更新(handleUpdate 4941 + RestartBinary/triggerRestart)、模型目录/本地技能枚举回传(handleModelList 4645)、token 续期循环(4025)、路径自愈(healAgentPath 1160: ~/.multica/hooks 包装器检测)、Windows junction 处理、空闲看门狗挂起。

---

## 4. 会话/任务模型

### 4.1 数据表【源码】migrations/(582 个 up 迁移,148 张表,全部 CREATE TABLE 枚举)
核心表:
- `agent_task_queue`(001_init.up.sql): id/agent_id/issue_id/**status CHECK('queued','dispatched','running','completed','failed','cancelled')**/priority/dispatched_at/started_at/completed_at/result JSONB/error;003 加 context,026 task_messages,020 task_session,022 **部分唯一索引 idx_one_pending_task_per_issue**(每 issue 至多一个 queued/dispatched,合并队列安全网),后续加 chat_session_id/work_dir/session_id/failure_reason/usage 等
- `agent_runtime`(004): UNIQUE(workspace,daemon,provider),runtime_mode local/cloud,status online/offline
- `runtime_profile`(120): 自定义 runtime,protocol_family CHECK(与 pkg/agent.SupportedTypes 锁步,逐步加宽至 25 族: 313=dsh,342=mcode,370=dim,403=zeroclaw,441=codearts)+command_name+fixed_args
- 会话族: chat_session/chat_message(message_kind: message/no_response/onboarding_kickoff/onboarding_opening,protocol/messages.go:262-279)/chat_draft_restore/chat_pinned_agent
- 任务族: task_message(agent 流式事件,seq/call_id/type=text|tool_use|tool_result|error)/task_usage(按模型 token+cache)/task_supplement(+capability)/task_token
- 供给链: agent(+agent_skill/agent_mcp_server/agent_env)、skill(+skill_file)、squad(+member)、issue 全家(status/workflow/view/wakeup+receipt/subscriber/source_context/dependency)、project(+resource: repo|local_directory)、wakeup(定时/条件唤醒)
- 插件族 20 张(plugin_installation/package/hook/mcp/storage/secret…)、五 IM channel_* + 各自 binding/audit/dedup、autopilot 全家(run/trigger/quota/delivery)、GitHub/VCS 快照、daemon_connection/daemon_token/daemon_pairing_session、webhook_delivery、search_index_*

### 4.2 任务生命周期【源码】pkg/protocol/events.go:29-42 + service/task.go
`∅ → queued(enqueue/retry)→ dispatched(daemon claim)→ running(daemon start)→ completed|failed`;分支 `waiting_local_directory`(本地目录忙)、`* → cancelled`(用户/系统)。每转移对应一个 task:* WS 事件;失败经 pkg/taskfailure 分类(provider 5xx/network/context_exhausted/runtime_offline/invalid_task_identity/local_directory_error…);恢复链: ResumeSessionID + Result.ResumeRejected/TransientRejected 语义(agent.go:264-301)决定续会话或换新会话重试(service/task.go retryableReasons)。

### 4.3 WS 推送协议(用户面)【源码】
- 服务端 events.Bus → realtime.Hub 按 workspace 房间广播 protocol.Message{type,payload};前端按 `task:` 前缀失效快照(events.go:30-33 注释)
- chat 专用: chat:message(实时气泡)/chat:done(携带完整 assistant 行避免闪烁 #2123)/chat:quick_actions(后补建议 chips)/chat:cancel_finalized(outcome=stopped|restored,#5219)
- inbox:* 增量;全部 80+ 事件类型见 §1.3A

---

## 5. 文档逐篇(根 12 + docs/ 4 + 站点)【文档】

| 文档 | 行数 | 要点 |
|---|---|---|
| README.md(/.zh) | 284 | 定位"Agents that show up on the board";source-available、自托管、用现有 agent CLI 无锁定 |
| VISION.md(/.zh) | 98 | "Multica = Multiplexed Information and Computing Agent";致敬 Multics 分时系统——给人/AI agent 共享的"时间片" |
| CLI_AND_DAEMON.md | 1190 | **最重**: 安装/认证/daemon 全配置表(50+ 环境变量)/26 agent 表格/How It Works 五步/GC 七策略/每 agent PATH/MODEL/ARGS 覆盖/ACP mcp_config 语义/Hermes 记忆持久化 |
| SELF_HOSTING.md | 537 | docker-compose(postgres+backend+frontend)、域名/TLS、SMTP |
| SELF_HOSTING_ADVANCED.md | — | 高级运维(采样标题级) |
| SELF_HOSTING_AI.md | — | 自托管下 LLM 网关接法(采样标题级) |
| CLI_INSTALL.md | 5821B | CLI 分发(install.sh/brew) |
| CONTRIBUTING.md | 17K | 开发流程 |
| AGENTS.md / CLAUDE.md | 13K/11B | 给贡献 agent 的仓库指引(CLAUDE.md 仅 "See AGENTS.md") |
| docs/engineering/issue-wakeups.md 等 4 篇 | — | 唤醒机制/状态目录滚动/Lark typing 清理/维护任务 |
| apps/docs/ | — | fumadocs 文档站源(未逐页读,标注) |
| .env.example | 40K/94 变量 | 全配置面采样 |

CHANGELOG:仓库根**无** CHANGELOG.md(发布说明走 GitHub Releases + apps/web changelog 页面)。

---

## 6. 前端页面清单

### 6.1 apps/web(Next.js App Router,46 个 page.tsx 全列)【源码】
- 公共: (landing)/ {home, about, changelog, contact-sales, download, licensing, privacy, usecases+[`slug`]};(auth)/ {login, invitations, invite/[id], onboarding, workspaces/new};auth/callback;join;billing/return;五 IM bind 页(lark/slack/telegram/wecom/dingtalk)
- 工作区 `[workspaceSlug]/(dashboard)`: **issues(+[id] 详情含任务时间线)、chat(会话列表+消息+pending-task+queued-tasks)、agents(+[id]+new/{manual,ai}+agent-builder 会话)、runtimes(+[id]+runtime/[runtimeId])、autopilots(+[id])、squads(+[id])、projects(+[id])、skills(+[id])、inbox、my-issues、members/[id]、usage、billing、settings**;attachments/[id]/preview
- 各页 API 映射:页面组件调 @multica/core 的 fetcher,路径与 §1.2④ 用户面一一对应(issues 页→/api/issues 族;chat→/api/chat/*;runtimes 详情→/api/runtimes/{id}/usage|activity|update|models|local-skills;inbox→/api/inbox/*;实时更新全部走 /ws 订阅 task:*/chat:*/inbox:* 失效重取)——采样核对于 asar 前端 bundle 与路由命名,未逐组件全文读(标注)

### 6.2 桌面/移动【asar】
- Electron(apps/desktop): main 进程管理 daemon 生命周期(resources/bin/multica 25.6MB Mach-O arm64),renderer 与 web 共用 @multica/views;API 指向 VITE_API_URL(staging=multica-api.copilothub.ai,.env.staging 直读)
- apps/mobile: Expo Router(iOS 先行)

---

## 7. 宿主 Agent 集成面(GraphLed「harness 即后端」竞品参照,重点)

### 7.1 统一抽象【源码】pkg/agent/agent.go(562 行全读)
- `Backend` 接口: `Execute(ctx, prompt, ExecOptions) → (*Session, error)`;Session = {Supplement(向活跃 turn 追加人话!), SupplementReady, ToolActivity, InterruptBackgroundTools, TerminalObserved, Messages chan, Result chan}(agent.go:17-23, 154-202)
- ExecOptions 关键位: Cwd/Model/SystemPrompt(仅少数 provider 内联,简报默认写盘 CLAUDE.md/AGENTS.md/QWEN.md)/ResumeSessionID+ResumeExpected+ResumeContinuityNotice(续话语义)/McpConfig/ThinkingLevel/MaxTurns/Timeout/各看门狗预算/ExtraArgs+CustomArgs(协议关键字过滤防破坏)
- Result: Status/Output/SessionID/Usage(按模型 input/output/cache_read/cache_write + CostUSDTicks int64 1e-10USD)/ResumeRejected 语义
- **25 个 protocol family**(SupportedTypes,agent.go:369-395)+1 内置 runtime 身份 omp(pi 协议族,builtin_runtimes.go:86-100)= **26 个可执行后端**

### 7.2 dsh = DeepSeek Harness 集成【源码】pkg/agent/dsh.go(479 行全读)——GraphLed 直接对照
- **启动**: `dsh --profile multica --stdio`(dsh.go:119-121);模型枚举 `dsh --profile multica --list-models`(436-479)
- **协议**: 自有版本化 JSONL stdio(v=1,常量 DshProtocolVersion 导出供 daemon 探测复用)。入站命令帧 execute{v,type:"execute",request_id(=taskID),cwd,prompt,resume_session_id,model{provider,id,reasoning_effort},mcp_servers[]}(54-64)与 cancel{request_id};出站帧 **ready/runtime:"dsh" → session(session_id) → text|thinking → tool_call(call_id,name,arguments JSON字符串) → tool_result(output,is_error) → usage(provider,model,四类token) → result(status,output,error{code,message},session_id,resume_rejected) → protocol_error → models[]**(77-117, 376-434)
- 模型 ID 格式 `provider/model` URL 转义(123-147);MCP 仅支持 stdio+streamable-http,SSE 显式报错(181-184)
- 进程治理: 独立进程组,cancel 帧→3s 宽限→SIGTERM→2s→SIGKILL(281-300);stderr 尾部留存于错误
- **为什么是 profile**: "DSH 自己没有机器可驱动模式;--profile headless 答一题即退,ACP 也只是 profile 而非内建"——multica profile 由**插件 bundle 提供 stdio 协议**(dsh_profile.go:21-28 注释)
- **profile 供给/自愈**(internal/daemon/dsh_profile.go,365 行全读): 存在性=stat `~/.dsh/profiles/multica/package.json`(74-87,尊重 DSH_HOME);缺失→offline reason 提示两条路(`dsh plugin --profile multica add <bundle>` 手动,或设 `MULTICA_DSH_PROFILE_BUNDLE` 让 daemon 每生命周期最多一次自动装,267-365);安装走 pnpm,daemon 会注入 DSH Desktop 自带 pnpm 的 runtime-commands/bin 到 PATH(120-140);超时 3min;成功判据=manifest 落盘而非 exit 0
- daemon 注册 dsh 需 profile 探测通过;MULTICA_DSH_PATH/MULTICA_DSH_MODEL 覆盖(CLI_AND_DAEMON.md:423-424)——【日志】本机 daemon.log 实测 dsh 被降级:"the Multica runtime profile is not installed; add the Multica DSH runtime bundle…or set MULTICA_DSH_PROFILE_BUNDLE"(因本机 ~/.dsh 无 multica profile)✅ 与源码语义一致;【勘】~/.dsh/profiles 仅 desktop-api.multica.ai,确无 multica ✅

### 7.3 其余 24 后端启动形态(采样直读)【源码】
- **claude**: `claude -p --output-format stream-json --input-format stream-json --verbose --permission-mode bypassPermissions --disallowedTools AskUserQuestion [--mcp-config <0600 临时文件>] [--strict-mcp-config] [--model] [--effort] [--max-turns] [--resume] [--settings]`(claude.go:1081-1133;协议 flag 全部列入 custom_args 黑名单 1065-1068)
- **opencode**: `opencode run --format json --dangerously-skip-permissions [--dir cwd] [--model] [--variant effort] [--session resume]`(opencode.go:95-139;OPENCODE_CONFIG_CONTENT 与 mcp_config 冲突告警)
- **codex**: app-server JSON-RPC(线程 start/resume、turn/interrupt 2s 预算);**cursor**: cursor-agent stream-json + 后台进程 watchdog;**qwen**: `qwen -p --output-format stream-json` + QWEN.md 简报;**ACP 族 10 个**(hermes/kimi/kiro/grok/qoder(+cn)/trae/qwenpaw/mcode/dim/reasonix/zeroclaw/antigravity): session/new 或 session/load 携 McpServer 数组,不落盘运行时自有配置(CLI_AND_DAEMON.md:431-447);Hermes 有跨任务持久 memory/state.db symlink 方案(449-465)
- 启动骨架表(launchHeaders,agent.go:521-547)与 UI 预览共用

### 7.4 结果回传链路(端到端)【源码】
agent 子进程 → pkg/agent Session.Messages → daemon run_collect(节流/截断 tool_output + OutputTruncated 三态)→ POST /api/daemon/tasks/{id}/messages(task_message 行,seq 有序)→ events.Bus → WS task:message → 前端时间线;终态 result → complete/fail(+usage 按模型)→ task:completed/failed → inbox 通知 + PR 链接(branch 由 daemon 在 worktree 上提交);会话指针 PinTaskSession(session_id, work_dir)供 rerun resume。

---

## 8. 对 GraphLed 设计的冲击(功能24:harness 即后端)

1. **"harness 即后端"已被 Multica 商品化,且 dsh 是一等公民**: dsh 不走 ACP 而走"**profile 插件 + 版本化 JSONL stdio**"——证明 GraphLed 把 dsh 当执行后端不需要发明新协议,但要**自带一个 profile/bundle 作为协议载体**,并接受"profile 未装=runtime 降级"的产品语义(离线原因文案、两条修复路径、自动安装守门)。我们做 AI 渗透平台时,渗透 harness 的 profile 可以同样由 GraphLed 分发,daemon 检测+自愈。
2. **Backend 接口的字段就是竞品护城河清单**: Resume(三字段语义:期望/被拒/通知文案)、Supplement(向活跃 turn 注入补充指令——渗透任务里"中途改目标"刚需)、ToolActivity/InterruptBackgroundTools(工具级看门狗,长 nmap/nuclei 扫描必需)、TerminalObserved(防完成被误判为挂起)、Usage 四类 token+成本 ticks。GraphLed 的 harness 抽象若缺任何一块,对标时即为缺口。
3. **claim 协议的"WS-first + HTTP 回退 + 同 handler 复用"模式**(daemon_rpc.go 用内存 ResponseWriter 复用 HTTP handler)直接可抄:一套鉴权/校验逻辑两种传输,且 capability 门控(rpc-v1)保证新旧混布安全。
4. **任务状态机极简但护栏硬**: 6 状态 CHECK + 每 issue 一个 pending 任务的部分唯一索引 + claim CAS + cancel 轮询对账(5s)+ GC 元数据/活动根守卫。渗透平台的长任务(数小时扫描)还应补: Multica 的 waiting_local_directory(资源忙挂起)与 semantic inactivity watchdog 分层。
5. **能力协商文化**: 15 个 DaemonCapability 常量全部"缺省=安全失败",配合 X-Client-Capabilities——GraphLed 的 daemon/server 演进必须内建这个,否则灰度期间行为分裂。
6. **货币化面已经打样**: runtime usage 按模型计 token、cloud-billing/cloud-subscriptions/Stripe、seat capacity、autopilot 配额——AI 渗透平台按"执行用量"计费有完整参照。
7. **安全面冲击**: bypassPermissions/--dangerously-skip-permissions 全线(渗透平台反而可以此为卖点做受控权限);CSP frame-ancestors none + 插件双信任边界(mpi_/mpc_ token vs 会话桥);HMAC 签名下载/头像。**渗透任务隔离**(每任务 git worktree + 裸仓缓存 + GC)是磁盘治理范本。

## 9. 我们已有/缺失对照(GraphLed 视角,? = 本会话未验证)

| 能力 | Multica | GraphLed 现状(基于 workspace 布局推断) |
|---|---|---|
| 多 harness 执行后端抽象 | 26 后端 + Backend 统一接口 | ? apps/ 下有执行编排,但 harness 适配器数量/接口粒度未验证 |
| dsh 集成 | profile+stdio JSONL v1 全链 | ? dsh-plugins/ 目录存在,插件面有雏形;daemon 面 ? |
| Daemon 体系 | 注册/心跳/批量claim/WS RPC/GC/自更新 | ? 未见 daemon 包 |
| 任务状态机 | 6 态+部分唯一索引+cancel 对账 | ? panorama/ 疑为调度层,细节 ? |
| 流式回传 | task_message seq+WS task:message+三态截断 | ? |
| 中途补指令 Supplement | 3 个 ACP/挂钩后端支持 | ? |
| 权限模型 | 全线 bypass(渗透场景反而要收紧) | 渗透平台天然需要分级授权——**差异化机会** |
| 计费 | usage 四 token 维+Stripe+seat | ? |
| 插件生态 | plugincontract+SDK+桥+市场 | dsh-plugins 有对应潜力 ? |
| IM 集成 | 5 IM 全(国内三件套) | ? |

## 10. 覆盖度自报(源码全量口径,61律)

- **路由**: 464 HTTP 端点全数枚举(router.go 全文件机械扫描,方法直方图核账)+ 2 WS + pprof 6;四认证面全数归组;WS 帧类型全列(用户面 80+ 事件常量逐条取自 events.go,daemon 面 9 帧+1 RPC method)。**路由数=466(主服务)**。
- **目录**: 顶层 14/14 全看;server/pkg 15 包全数;server/internal 30+ 包全数列出、其中 10 个核心包主文件精读(handler/daemon/daemonws/realtime/protocol/agent/taskfailure 层面),integrations 五 IM 包结构级。
- **源码精读全文**: agent.go、dsh.go、builtin_runtimes.go、dsh_profile.go、protocol/messages.go、protocol/events.go、handler/daemon_rpc.go、realtime/hub.go(WS 段)、router.go(认证边界段全文+全文件扫描)、daemon/client.go(函数面)、daemon.go(函数索引 140+ 条全列 + handleTask 5655-5904 全文)、migrations 关键 6 个全文+148 表全枚举。
- **文档**: 根 12 篇全数处理(CLI_AND_DAEMON 1190 行逐节、README/VISION/SELF_HOSTING 精读,ADVANCED/AI 标题级采样——**此 2 篇+apps/docs 站点为标题级,标注**);docs/ 4 篇列出。
- **前端**: 46 page.tsx 全列;页面→API 映射为路由名+asar bundle 采样核对,**未逐组件全文读(标注)**。
- **迁移**: 582 up 全文件名枚举,148 表全列,6 个关键迁移全文。
- **交叉验证**: asar(v0.5.1 桌面端结构)、daemon.log(5.6MB: claim/phase/gc/dsh 降级实测)、~/multica_workspaces(任务根/空 multica-config)、~/.dsh(无 multica profile)——四类戳贯穿全文。
- **未覆盖/边界**: integrations 各 IM 包、issue* handler 族(~200 文件)为结构级;e2e/deploy/helm 未读;apps/docs 站点未逐页;移动端仅 package.json 级。以上不影响七节结论。

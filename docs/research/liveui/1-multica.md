# multica（本地自部署活系统）深析 — 探隐 v0.9d UI 升级批参照报告

- 目标：multica @ http://localhost:3000（Next.js 前端）+ :8080（Go 后端）+ PostgreSQL17/pgvector
- 入口页：http://localhost:3000/wgen/squads/847a03be-c47f-46a5-884a-de3445a5104e（实测 squad「安全红队」详情页）
- 调查日期：2026-10-15（live，daemon 心跳在线 last_seen 08:14Z）
- 报告文件：docs/research/liveui/1-multica.md

## 0. 方法与视角声明（只读纪律执行记录）

- 依据升级指令，本报告以**本地源码/部署仓/运行数据为主**，HTTP 降为验证手段。
- HTTP 全程仅 GET + 两次登录 POST（/auth/send-code、/auth/verify-code，邮箱验证码取自部署文档记载的 docker 日志 DEV 模式）。**未触发任何扫描/建任务/改状态**；所有 /api/* 访问均为只读 list/get。
- 本地只读检视范围（父指令明示授权）：
  - multica项目实践/multica-selfhost/（部署仓）、multica项目实践/_research/（安装物料）、Multica安装使用指南.md
  - /Users/wgen/multica_workspaces/（daemon 运行数据）
- 未触碰 ZhuLong 源码目录；未执行任何 git。
- 视角等级：**已认证视角**（owner 账号 GET）+ **源码级视角**（daemon 注入 workdir 的 skill 包、compose、env 模板、i18n 全量字典）。比一般"未认证视角"深一层。

## 1. 系统定位与架构实测

**定位**：Multica = 「人类+智能体共用」的项目管理系统（开源 github.com/multica-ai/multica，Go+TypeScript，官方自称 51k+ stars）。产品名句：*Project Management for Human + Agent Teams*。它不是"扫描器"也不是"攻击工具"，而是**把 AI 编码智能体当同事派活的项目协作驾驶舱**。本机实例上跑的正是一套**真实安全红队编排**（见 §③）——与探隐同域，参照价值极高。

### 1.1 部署形态（文件级出处：multica-selfhost/docker-compose.selfhost.yml）

```
postgres: pgvector/pgvector:pg17  (卷 pgdata)
backend:  ghcr.io/multica-ai/multica-backend  (Go, :8080→127.0.0.1)
frontend: ghcr.io/multica-ai/multica-web      (Next.js, :3000→127.0.0.1)
卷: pgdata, backend_uploads
```

- 127.0.0.1-only 绑定 + 注释明确警告 Docker 绕过 UFW（compose L1-9）。
- 镜像是成品：**部署仓不含 app 源码**，源码视角来自 GitHub 公开仓 + 本地 daemon 注入物 + RSC payload 反解。
- .env 96 个变量（_research/.env.example）：JWT_SECRET/COOKIE_DOMAIN/CSRF；S3/CloudFront 附件；Resend/SMTP 邮件；Google OAuth；GitHub App（PR webhook 镜像+CI 快照）；VCS 自建集成（Forgejo/Gitea/GitLab，self-host 默认开）；插件表面（MULTICA_PLUGIN_SECRET_KEY/SURFACE_ORIGIN/API_URL/DIR，第二 cookie-free origin 隔离）；服务端 LLM 层（聊天标题等内部助手）；Lark/Slack/DingTalk/WeCom/Telegram 五渠道 bot（各自 SECRET_KEY 静态加密 per-installation token）；PostHog 遥测（.env 里 DO_NOT_TRACK=1 已关）；dev 固定验证码 MULTICA_DEV_VERIFICATION_CODE。

### 1.2 执行模型（文件级出处：/Users/wgen/multica_workspaces/ 实测）

```
用户动作 → 服务端建 queued task(指向 agent+runtime)
→ WS 唤醒 runtime(daemon) → daemon 认领 → 服务端下发
  task context/repos/project 资源/session-workdir 提示/task token(mat_)
→ daemon 备 workdir → 起 provider CLI (claude/opencode/…)
→ multica CLI + 注入物 = agent 的平台 API
```

task 目录解剖（wgen-1695c990b25a/task-924c5d7a92e4/）：
- `.task_owner` {workspace_id, task_id}；`.task_lock`；`.gc_meta.json` {kind:"chat", chat_session_id, completed_at}
- `.managed_env.json` {workspace_id, chat_session_id, agent_id} —— 任务级身份
- `.multica_sidecar_manifest.json`：**sidecar 注入清单**（files+dirs），即 daemon 向 workdir 注入的东西
- workdir/AGENTS.md：运行时简报（`<!-- BEGIN MULTICA-RUNTIME -->` 自动管理），含身份（"You are: 1111"+UUID）、可用命令、后台任务安全（top-level turn 退出即 terminal、禁止 background-and-yield、CI 不可作为交付门）、chat 模式工作流、技能发现、输出纪律（attachment upload 是唯一文件交付通道；禁止 file:// 链接）
- workdir/.opencode/skills/multica-platform/：**平台即技能**——SKILL.md 路由表 + 8 份领域参考（agents/autopilots/issues/mentions/projects/runtimes/squads/skill-import，共 ~126KB）。平台的全部契约（校验规则/副作用/常见误判）以 agent 可读的 markdown 下发，而非硬编码进 provider。
- `.task_roots/<hash>/root.json`：workspace+task→相对路径反查表（2 条在案）
- `.repos/<ws>/`：仓库缓存 + `.multica_co_authored_by` 标记
- `.pending-terminal-reports/v1/<hash>`：终态报告待写队列（2 个空槽在案）

**与探隐的四层对照**：multica 的 daemon≈探隐"战士宿主"角色的泛化（opencode 现役=runtime provider）；`.task_roots`+sidecar manifest≈探隐的账本+引擎契约；AGENTS.md+skill 注入≈探隐 SKILL.md；区别在 multica 有服务端持久层（Postgres），探隐坚持 13 本 TSV+哈希链的底座自持。

### 1.3 API 面（出处：登录页 31 个 JS chunk 静态字符串提取）

- 认证：`/auth/send-code` `/auth/verify-code`（**无 /api 前缀**，实测）、/auth/refresh、/auth/logout、/auth/google、/api/cli-token
- 资源：/api/workspaces /api/me /api/members /api/agents(+/env +/skills +/mcp) /api/squads(+/members +/activity) /api/issues(+/comments +/runs +/wakeups +/properties) /api/projects(+/resources) /api/autopilots(+/triggers +/runs +/deliveries) /api/runtimes(+/usage +/activity) /api/chat/sessions /api/tasks /api/skills /api/labels /api/properties /api/issue-views /api/issue-view-preferences /api/quick-actions /api/upload-file /api/attachments /api/notification-preferences /api/cloud-runtime/nodes /api/webhooks/autopilots/{token} /api/issues/{id}/comments/trigger-preview
- 客户端纪律（login chunk 反解）：每请求 X-Request-ID；CSRF 双提交+一次自动重试；401 集中处理；日志 `→ POST /x`/`← 200 /x (12ms)` rid+时长；JSON 走 stdout、告警走 stderr 不许 2>&1（写进 agent 简报的契约）。

---

## 2. ① UI 设计解构（可抄级）

### 2.1 布局骨架

- **App Shell 三层表面**：侧栏（sidebar token 独立成组）+ 顶栏 h-12（`flex h-12 items-center gap-3 border-b px-4`，骨架屏阶段即此形状）+ 内容区 h-svh 满高、`overflow-hidden`。loading 态骨架= 顶栏两条 skeleton（h-5 方块+h-4 w-32 条）+ 内容区 6 行 h-9 条（RSC payload row 0 实测）。
- **列表页 = 表格 + 右侧检查器(inspector)**：squads 页表格列 Squad/Leader/Members/Created by/Created，选中行开 inspector 显示 Details（i18n squads.inspector）。行尾 overflow 菜单（row_menu "Squad actions"→Archive）。
- **详情页 = 头部资料卡 + Tab**：squad 详情 = SquadDetailPage（chunk 名实测），Tab 仅两个：**Members / Instructions**（detail_tabs）。Members 区标题带计数（"N members in this squad"，单复数 i18n 变体）+ 右侧两按钮 **Add Member / Create Agent**。
- **工具栏统一范式**（squads.toolbar / issues.display）：Display(列选择) · Sort by+升降序 · Filter(N filters 徽标+Clear filters) · 匹配计数 "Matching squads / all squads"。

### 2.2 导航 IA（出处：i18n settings.shortcuts.actions.go*）

```
Inbox · Chat · My Issues · Issues · Projects · Autopilots · Agents · Squads · Usage · Runtimes · Skills · Settings
```
12 个一级目的地 + 全局命令面板（openSearch）+ 快捷键体系（createIssue/toggleSidebar/toggleRightSidebar/toggleChat/findInIssue/…goBack/goForward）。聊天为 **FAB + 可最小化窗口**（chat.window：New chat/Restore/Expand/Minimize；"Another chat is running"/"has unread replies" 窗口角标）。

### 2.3 组件库清单（i18n+chunk 反解，shadcn/Tailwind v4 系）

avatar 上传+裁剪+emoji、color_picker（饱和度/色相/HEX/取色器/预设/随机）、OTP 输入（input-otp，one-time-code）、日期相对化（just now/Nm ago/Nh ago）、分页（{{page}} / {{totalPages}} · {{total}} total）、skeleton、dialog 家族（archive/delete/discard-unsaved/rename/description）、toast（成功/失败成对）、菜单/下拉/表格列显隐、看板列、甘特条、swimlane、聊天队列条、状态 pill、chips。

### 2.4 交互模式（对本报告最有价值的部分）

- **多视图同数据**：Issues 一个数据集切 table/board(看板+列显隐+手动排序提示)/swimlane(按 parent/project/assignee 分道)/gantt(日/周/月缩放+"Show completed"+日期倒置警告)/timeline。
- **视图资产化**：view_selector + save_view + issue-view-preferences API——筛选排序可存为个人视图。
- **在线感三件套**：
  1) 列表行状态 chips（agent availability: Online/Unstable/Offline/Archived + workload: Working/Queued/Idle + "+N queued" 徽标）；
  2) **agent_live 横幅**（issue 详情页顶部）："{{name}} is working / is queued / is waiting for the local directory · queued for {{elapsed}} · {{count}} tools → [View transcript] [Stop]"；
  3) **agent_activity 聚合 chips**（issue 列表）："N agents working" hover 出 "M active runs / K queued agents"，空态 "No agents working right now"。
- **live_peek**（agent 列表悬停）："Now on <issue>" / "No issue"、"Last seen"、Failed 指示。
- **Transcript 对话框**（agents.transcript）：执行事件流回放——状态过滤、Copy all/Copy filtered、patch 截断（"... (truncated)"/"(body truncated)"/"only the start is displayed"）、触发源标签（Initial run/From a comment/Autopilot/Retry/From chat/Quick create/Direct assignment）、run details（Runtime/Provider/Mode/Workdir/Project directory/Created/Started/Completed + 复制 workdir）、**降级明示**（"Antigravity 不提供 live 执行事件，运行结束后才有 transcript"）。
- **execution_log**（issue 内）：默认折叠 "Show past runs (N)"，行级 Cancel/Retry（带权限态 tooltip "Not retried—you don't have permission"）、Retry #N 前缀、"Includes N comments"、**归因链** "On behalf of {{name}}"（autopilot 触发时归因到触发创建者/规则发布者，9 种 source 枚举）、token 用量 tooltip 点开 per-run 明细。
- **失败 taxonomy**：~30 个人读 reason（Expired in queue/Daemon offline/Daemon did not reconnect/Run timed out/Hit the iteration limit/Waiting on human input/Provider auth failed/Provider quota exhausted/Rate limited/Agent process crashed/Context window exceeded/Runner CLI not installed/…+ cancelled_by_system / cancelled_by {{name}}）。
- **聊天队列 + Steer**：运行中发消息进队列（"N queued messages"，可 Edit/Remove/Clear），**Steer**=在回复开始后插入改向指令（"Steer is available after the current reply starts"，权限失效降级 toast）。
- **状态 pill 语义化**（chat.status_pill）：offline→reconnecting→retrying→queued→waiting_local_directory(带原因)→starting_up→thinking→typing；工具态人话化：Running a command / Reading files / Searching the code / Making edits / Searching the web / Working。
- **破坏性操作确认文案**：archive squad 弹窗写明后果与不可逆（"Issues currently assigned will be transferred to its leader. This can't be undone"）。
- **未保存守卫**：Instructions Tab 切走弹 "Discard unsaved changes?"；表单区常驻 "Unsaved changes" 标记。
- **触发预览**：发评论前 POST trigger-preview，服务端算出"这条评论会唤醒谁"，前端显示 agent chips；@all 广播会抑制 assignee 自动触发（显式 @agent 优先）。

### 2.5 视觉系统（出处：/_next/static/css/*.css 令牌提取）

- **Tailwind v4 + OKLCH**。暗色为主设计，语义令牌 shadcn 系（background/foreground/card/popover/primary/secondary/muted/accent/destructive/border/input/ring/sidebar-*）。
- **表面四级光阶**（.dark 实测）：app-shell `oklch(15.5% .005 285.823)` → page-canvas 18% → surface 21% → surface-raised 23.5%（hover 27.4% / selected 30%）。色相统一近中性 285.8（微紫灰），前景 98.5%。**一层含义一级光**：壳<画布<面板<浮层，纯光阶不换相。
- **图表色**：chart-1..5 = 蓝 72%→32% 光阶五档（oklch(.16→.03 彩度递减），数据密度可视化用同相渐变。
- **阴影三档**：surface-shadow(1px)、menu-shadow(10px 28px)、floating-shadow(20px 48px)。
- **字体**：Inter 可变字体 6 个 woff2 子集预加载（含中文子集），--font-sans/serif/mono 三槽。标题即页面 H1、正文紧凑。
- **状态色语义**：red(错误/destructive 70.4%)、amber/yellow(排队/警告)、green/emerald(完成/在线)、blue(信息/图表)、violet(强调)。
- **i18n 体系**：en/zh-Hans/ja/ko/fr，跟随浏览器+设置切换；**整本 en 字典 268KB 随 RSC payload 下发**（探隐若抄此法需注意体积，可只发当前路由命名空间）。

### 2.6 状态可视化手法汇总（抄点密度最高的一节）

1. 成员卡：头像+Leader chip+角色标签+三态点（Working/Idle/Offline/Unstable/Archived）+当前 issue 标题（超长 "and N more"）+last active 相对时间。
2. 列表级：Activity(7d) 列（runs 计数+失败率后缀 "· 2 failed (14%)"）。
3. issue 级：stage 分组（"Stage {{n}}"，per-stage done 计数）+ swimlane 按父任务分道。
4. 运行级：横幅（who is doing what+已排队多久+工具计数）+transcript 时间线+execution_log 折叠史。
5. 全局：chat FAB 角标 + inbox 计数 + "N filters" 徽标 + matching/total 双计数。

---

## 3. ② 功能清单 + 成熟度评分

评分制：成熟度 1-5（5=生产完备，1=占位）。状态：有/半/无。

| # | 功能 | 状态 | 分 | 依据 |
|---|------|----|----|------|
| 1 | Squad 编排（leader 路由制小队） | 有 | 5 | squads.md 全契约+live 2 个小队；路由/简报/归档/成员角色全闭环 |
| 2 | Squad 成员管理（agent+human 混编、角色、换队长） | 有 | 4 | squads.members_tab i18n+member add/set-role CLI；live 安全红队 6 员 |
| 3 | Stage 屏障（子任务分阶段、阶段齐关门唤醒父） | 有 | 4 | issues.md Stages 节；issue children 按 stage 分组+done 计数；推进是 agent 驱动（设计而非缺陷） |
| 4 | Issue 状态机+服务端副作用 | 有 | 5 | backlog 停车/todo 触发/in_progress/in_review/done/cancelled 全副作用表；自定义状态 7 类生命周期 |
| 5 | Issue 多视图（表/板/泳道/甘特/时间线）+保存视图 | 有 | 5 | i18n 五视图+view_selector/save_view+preferences API |
| 6 | 自定义属性（typed properties：select/number/date/url/actor/multi） | 有 | 5 | issues.md+settings.properties；过滤/排序/侧栏展示 |
| 7 | Agent CRUD+字段契约（model/thinking/tier/env/mcp/skills） | 有 | 5 | agents.md 全契约；live 9 agents 实测 |
| 8 | Agent 活监控（workload/live-peek/transcript/失败 taxonomy） | 有 | 5 | i18n agents.* 全套；~30 失败原因枚举 |
| 9 | Chat 面板（FAB/队列/Steer/开场建议/历史） | 有 | 5 | chat.* 全套；live 1 会话实测 |
| 10 | Autopilot（schedule/webhook/manual；create_issue/run_only） | 有 | 5 | autopilots.md；webhook 持久准入+幂等+投递重放 |
| 11 | Wakeups（event/at/every/cron 订阅式唤醒） | 有 | 4 | issues.md Issue wakeups；自触发防护+关单自动停 |
| 12 | Mention 触发语法（mention:// 五型+@all+触发预览） | 有 | 5 | mentions.md；trigger-preview 端点实测存在 |
| 13 | Skills 库（工作区库+agent 绑定 add/set+URL/本地/运行时导入） | 有 | 5 | skills.* i18n+skill-import.md；live 17 技能 |
| 14 | MCP 双层（workspace 库+agent 私有，claim 时合并） | 有 | 4 | agents.md MCP 节；写入审计/读取脱敏 |
| 15 | Runtime 管理（daemon 注册/能力协商/usage/升级/级联删） | 有 | 4 | runtimes.md+live claude/opencode 双 runtime；10 项 capabilities 协商实测 |
| 16 | 仓库编排（repo checkout 保工作不丢/worktree 模式/local_directory in_place|worktree） | 有 | 5 | runtimes.md+projects.md；分支所有权记录 refs/multica/local-state |
| 17 | Projects 持久上下文（资源注入 brief+resources.json） | 有 | 4 | projects.md；live 1 项目 |
| 18 | Usage 计量（token per-run/leaderboard/自定义定价/回退口径） | 有 | 4 | runtimes usage 口径文档+usage.* i18n |
| 19 | 权限模型（owner/admin/member+agent visibility+invoke 门+归因） | 有 | 5 | agents/autopilots 访问规则；"授权为发起人而非机器主" |
| 20 | GitHub 联动（PR 三处扫描链接/close-intent/CI 快照） | 有 | 4 | issues.md；自建 Forgejo/Gitea/GitLab 走 VCS 集成 |
| 21 | 消息渠道 bot（飞书/Slack/钉钉/企微/Telegram） | 有 | 4 | compose 5 组 SECRET_KEY+路由树 lark/slack/dingtalk/wecom/telegram 顶层段 |
| 22 | Inbox 通知中心（分组+过滤+已读） | 有 | 4 | inbox.* i18n |
| 23 | Onboarding 向导（about-you/workspace/runtime 三步+问卷） | 有 | 4 | onboarding.* i18n |
| 24 | 命令面板+全局搜索+快捷键 | 有 | 4 | search.*+settings.shortcuts |
| 25 | i18n（5 语言+浏览器跟随） | 有 | 5 | en 字典 268KB 实测提取 |
| 26 | 插件表面（plugin surfaces，cookie-free 第二 origin） | 半 | 3 | compose 注释+settings.plugins i18n+layout chunk plugins 数组；本机未启用 |
| 27 | Billing（Stripe/席位） | 半 | 3 | billing.* i18n+Stripe return 页；self-host 不适用 |
| 28 | 桌面客户端 | 有 | 4 | download/top 路由+desktop.* i18n（updates/daemon 页） |
| 29 | 移动端 | 半 | 2 | 仅 i18n 提及 mobile tap 行为差异 |
| 30 | 审计（env 专用端点审计行/执行日志全回放/操作归因） | 有 | 4 | agents.md+指南"执行日志完整可回放（审计友好）" |
| 31 | 浏览器内直接派活（quick-create/对话开场建议/onboarding 卡片） | 有 | 4 | chat.empty_state/onboarding_cards |
| 32 | 无框架零依赖客户端 | **无** | 0 | Next.js+React+Tailwind+shadcn 全家桶（与探隐语言律互斥点） |

---

## 4. ③ 业务使用流（live 数据推断）

### 4.1 这个工作区今天上午发生了什么（时间线复原，全部来自只读 GET+文件系统）

```
05:58Z  daemon 注册两台 runtime：Claude Code 2.1.238 / opencode 1.19.0（均 online）
~06:00  人类在 Chat 对 agent「1111」发一句话：
        "帮我创建一个渗透测试的项目和相关的所有流程/skill等"
        （1111 = opencode runtime · model zhipuai-coding-plan/glm-5.3 · private）
06:00-06:04  1111 在一次运行内产出：
        · 项目「渗透作业交战」(planned, 1 resource)
        · GenCPT 九阶段容器渗透流水线 issue 树 WGEN-2..13（5 个 stage 分组）
        · 17 个技能（渗透六件套 + 审计引擎全家桶）
06:03  小队「安全红队」创建：队长+总控+侦察+渗透+分析+报告 6 agent
06:05  小队「审计队」创建：总控+审计员 2 agent（白盒源码审计轨道）
06:05-06:06  旧 GenCPT issue 树整体 cancelled（被小队+技能架构取代）
06:06  chat task 终态（.gc_meta.json completed_at），daemon 侧留终态报告槽
08:14  daemon 心跳仍在（last_seen_at）
```

**判读**：multica 在此的真实角色 = **安全作业的编排与治理层**——人类只说一句话，chat agent 把"项目-小队-角色-技能-流程指引"整套组织结构建出来；之后渗透作业的受理（授权八问预检）、拆单（5-stage thin-slice）、执行（opencode 现役跑工具）、落账（总控单写者 TSV 账本）、验收（队长抽验出口证据）、升级（L3/对外/凭据→人审）全部在小队指引里显式定义。**这就是探隐"九门流程+battle.py 多战士"的同构物，而且是 live 的。**

### 4.2 关键 live 工件摘录

- 小队「安全红队」instructions（GET /api/squads）：授权八问齐备性预检→缺件 blocked 补件→齐备拆 5 stage（S1 串行 todo、S2 轨道 backlog、S3-5 backlog）→改派总控；stage-assignee 角色映射（侦察/渗透/分析/报告/总控自办）；"角色只交底稿，总控落账过门。队长不代跑、角色不落账"；出口抽验（timeline 链校验/脱敏抽检/清理核销）；升级清单（L3 破坏性/scope 修订/凭据明文/仲裁→人）；"交战父任务终态 done 由人点"。
- 队长 agent instructions（GET /api/agents/088c5916）：调度台人格（"你不执行任何渗透测试操作"）+接单审单+阶段抽验+紧急熔断（目标疑似影响生产→立即 blocked 并升级）+复盘 insights 飞轮（INS-NN 提案→人审→总控技能版本化更新）+红线（无授权零主动/不改账本/双时区表述）。
- 技能库（GET /api/skills）：pentest-core（"单写者与底稿交付、授权八问、L0-L3 分层、凭据四条、审批升级、TSV 账本 schema findings v1.1"）、pentest-engagement v1.7（"Multica 原生九门+角色分工+技能五拆+thin-slice 编排"——**注意：他们在 multica 上重建了'九门'**）、pentest-recon（L0 只读测绘/逐行 scope 判定/八轨覆盖矩阵）、pentest-exploit（progress.tsv 步骤级落盘+断点重入）、pentest-verify（C1/C2/C3 定级+条件可达性证据）、pentest-report（中文六要素模板+脱敏红线）；审计侧 gensource 四阶段+gate 方程（SELFTEST: PASS 硬门）。
- 运行数据（文件系统）：workdir 里 .opencode/node_modules、AGENTS.md、daemon_task_context；`.pending-terminal-reports/v1` 两个哈希槽=终态报告 outbox 模式（防 turn 退出丢结果）。

### 4.3 正在跑的作业长什么样

当前无活跃 run（chat 任务已终态、issue 树已 cancelled、daemon idle 待命）。但其"战斗形态"可从契约+UI 文案精确复原：issue 指派小队→队长被唤醒→审单评论→拆 stage 子任务→总控被改派唤醒→逐 stage 改派角色 agent→每子任务一个 run（横幅"N is working·3 tools"→transcript 可回放）→stage 齐关门→父任务 assignee 被评论唤醒→抽验→人点 done。**探隐 battle.py 想要的多战士并行监控，在他们这里是"issue 树+run 横幅+execution_log"三件套。**

### 4.4 与 dsh web（同族遥控器）的差异点

| 维度 | multica web | dsh web |
|------|-------------|---------|
| 产品形态 | 独立 SaaS PM（多工作区/多用户/RBAC/计费/五渠道通知） | 单 harness 内嵌观察面（127.0.0.1:8900） |
| 数据真相 | 服务端 Postgres（UI 是**主写面**） | 内核 TSV 账+哈希链（UI **只读投影律**） |
| 技术栈 | Next.js+React+Tailwind+shadcn+i18next（重） | 纯手写 HTML/CSS/SVG/vanilla JS（零依赖律） |
| 遥控对象 | 任意 provider CLI（daemon 协商能力） | 探隐内核（battle.py 等直连） |
| 实时机制 | RSC+WS+乐观更新+skeleton | 轮询/SSE 级 |
| 相同点 | **都以"agent 是可派活的同事"为中心**；都有运行回放；都强调审计可回放 | 同左 |

---

## 5. ④ 对探隐的判决

### 判决：**仅参照**（置信度 92%）

**理由**：
1. **语言律不可逾越**：multica 的 UI 价值 100% 沉淀在 React/Tailwind/Next 组件与 RSC 数据流里；探隐 webui 是零框架零构建零依赖手写件。代码级复用=违反零依赖律，直接判死。
2. **投影律方向相反**：multica UI 是主写面（创建/指派/评论/触发全在 UI）；探隐 UI 只读。抄它的交互结构会诱导做出"写面"，违反已定法。
3. **底座哲学不同**：multica=服务端持久层+多租户 SaaS；探隐=13 TSV+哈希链底座自持。它的权限/计费/多工作区对探隐是负资产。
4. 但其**编排语义与状态可视化词汇表**（leader 路由/stage 屏障/触发预览/失败 taxonomy/transcript）与探隐九门+battle 高度同构，是市面上能找到的最贴题的"设计规格书"——参照价值极高。

**翻案条件**（出现任一即重审）：
- 探隐放宽语言律（如允许 iframe 嵌入外部只读面板，或给观察面开"构建链特区"）→ 升级为**二开**（嵌 multica 只读视图或移植其组件语义到 vanilla JS，仍守投影律）。
- multica 出 headless/embed 模式且探隐需要多工作区协作 SaaS 化 → **二开**其后端编排语义（非代码）。
- 探隐放弃 TSV 账本转服务端数据库 → **直接复用**变可讨论（当前置信度 <10%，基本不可能，底座自持是宪法级）。
- 附注事实：multica daemon 能把 **dsh 检测为 runtime**（安装指南 §二·五实测记载）。若探隐未来想"被 multica 这类 PM 遥控"，那是平台集成方向而非 UI 复用，不影响本判决。

---

## 6. ⑤ 可直接偷的 10 条（每条注明落点）

1. **成员卡五态+当前作业摘要**（Working/Idle/Offline/Unstable/Archived 点 + "Now on <issue>" + blocked 徽标 + last active 相对时间）→ 落 **探隐作战面板（battle 页）战士卡**。数据源=progress.tsv/run 状态。
2. **leader 制小队成员表**（Leader chip、角色标签、hover 出"Open agent detail/Make leader/Remove"）→ 落 **battle.py 多战士编排区**：探隐的"总控/侦察/渗透/分析/报告"角色卡直接套此形。
3. **Stage 屏障分组条**（"Stage {{n}}" 分组+组内 done 计数+阶段齐关事件）→ 落 **九门流程页**：九门=9 个 barrier 组，每门显示过门/待过计数。
4. **agent_live 横幅**（"{{name}} is working · N tools · queued for {{elapsed}} · [View transcript] [Stop]"）→ 落 **会话/任务详情页顶栏**，vanilla JS 十分钟级实现（探隐已有 run 状态即可驱动）。
5. **execution_log 折叠史+触发源标签+归因链**（"Show past runs (N)"、Retry #N、"On behalf of X"）→ 落 **账本视图/运行史页**：13 账的 run 记录加触发源标签（人发/接力/定时/重试）。
6. **失败 taxonomy 枚举表**（~30 条 reason_code→人读文案映射，如 "Hit the iteration limit"/"Waiting on human input"）→ 落 **探隐失败面板+账本 fail 列**：抄其分类学（队列过期/宿主离线/超时/迭代上限/等人/配额/上下文溢出/CLI 缺失），逐条配中文文案。
7. **聊天队列+Steer 语义**（排队消息可编辑/移除；"Steer 在回复开始后可用"）→ 落 **观察面指令输入框**：探隐向运行中战士追加指令时的队列化处理与状态门。
8. **表格工具栏范式**（Display 列选择+Sort+Filter chips("N filters"+Clear)+双计数 "matching/total"+Save View）→ 落 **13 账 TSV 通用表格组件**：探隐账本列多，此范式即查账体验升级的全部。
9. **OKLCH 表面四级光阶+图表同相五档**（壳15.5%→画布18%→面板21%→浮层23.5%，chart 蓝 72%→32%）→ 落 **webui 暗色主题令牌表**：纯 CSS 变量即可移植，与零依赖律兼容，探隐 SVG 图表直接吃 chart-1..5。
10. **触发预览（发前算"会唤醒谁"）+ @all 抑制语义** → 落 **探隐指令派发框**：发指令前显示"此指令将唤醒: 侦察、渗透"，广播模式抑制默认接单者——把 multica 的 trigger-preview 契约照搬为 battle.py 派单前检查。

（加赠第 11 条：**"平台即技能"注入模式**——daemon 向 workdir 注入 SKILL.md+分域 references 作为 agent 的平台 API 文档。探隐已有 SKILL.md，可补"分域参考+路由表+每域自带'常见误判'节"的三层结构。落 **knowledge/ 技能包结构**。）

---

## 7. 附录：文件级出处索引

本地文件（全部只读）：
- 部署：multica-selfhost/docker-compose.selfhost.yml（234 行全读）；multica-selfhost/.env.example（96 变量名提取）；_research/{README.md,README.zh.md,SELF_HOSTING.md,CLI_INSTALL.md,install.sh,Makefile}（目录清点）；Multica安装使用指南.md（全读）
- 运行数据：/Users/wgen/multica_workspaces/.multica/daemon_task_context.json；.task_roots/{a16d…,d046…}/root.json；wgen-1695c990b25a/task-924c5d7a92e4/{.task_owner,.task_lock,.gc_meta.json,.multica_sidecar_manifest.json,.managed_env.json}；task-b94354a7102c/.task_owner；.repos/5133…/.multica_co_authored_by；.pending-terminal-reports/v1/{7997…,a403…}
- 注入简报：…/task-924c5d7a92e4/workdir/AGENTS.md（全读）；workdir/.opencode/skills/multica-platform/SKILL.md（全读）；references/{squads,agents,issues,autopilots,runtimes,mentions,projects}.md（全读/节读）

HTTP 验证（GET+登录 POST only）：
- 页面：GET /、GET /wgen/squads/847a03be-…（200+skeleton，SquadDetailPage 客户端取数）；GET /login；JS chunks 31 个（API 面提取）；CSS 5 个（设计令牌提取）
- 登录：POST /auth/send-code、POST /auth/verify-code ×2（dev 验证码取自 docker logs，文档记载通道）
- 认证 GET：/api/workspaces、/api/squads?workspace_id=、/api/squads/{id}/members、/api/agents(+/{leader})、/api/runtimes、/api/projects、/api/skills、/api/issues(+/{uuid})、/api/chat/sessions、/api/me（404/401 行为另测）
- 容器日志：docker compose logs backend（只读，验证码+WRN 邮件后缀提示）

报告完。撰写：探隐 liveui 调查代理（multica 批）。

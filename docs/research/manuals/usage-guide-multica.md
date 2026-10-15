# multica 使用手册（实时滚动版 · 2026-10-15 起）

> 更新时间： 2026-10-15 18:30（漫游舰+源码舰合并版 v1.0——信息源：58 张活体截图/DOM 实测、容器内二进制与 1120 个 SQL 迁移、`~/multica_workspaces` 运行数据、DB 只读查询、/changelog 128 个版本史）。
> 系统： http://localhost:3000（Next.js 前端容器 + Go 后端容器 + pgvector/pg17，自托管 docker-compose，部署于 `multica项目实践/multica-selfhost`）。
> 版本： v0.5.1（2026-09-21）。运行数据： `~/multica_workspaces`；daemon 配置： `~/.multica/config.json`。安装细节见 `multica项目实践/Multica安装使用指南.md`，本文不重复安装步骤。

---

## 0. 定位（实测校准）

Multica 是**开源「AI 数字员工」任务平台**（GitHub multica-ai，营销语「你的下一批员工不是人类」）：把大模型编码代理（Claude Code / OpenCode / Codex / Qwen Code / DeepSeek Harness / Kiro / TRAE / Qoder / Antigravity / CodeBuddy / Oh-My-Pi / Hermes 等 CLI 运行时）注册为**运行时（Runtime）**，在运行时之上定义**智能体（Agent）**（人格化的指令+技能+可见性），把智能体编成**小队（Squad）**（队长/成员+指引），用**任务（Issue）**派工，用**收件箱/聊天/自动化（Autopilot）**驱动人机协作。它不是安全产品，但本工作区正把它当**渗透作业编排驾驶舱**用（安全红队 7 agent 编制 + pentest-* 技能族，见 §8）。

一句话心智：**Linear 式任务面板 × 每个任务可被 AI 员工领走真跑 × 跑在你自己的电脑上**。

---

## 1. 部署形态与访问

### 1.1 容器拓扑（本机实测）

```
docker compose -f docker-compose.selfhost.yml  (name: multica)
┌────────────────────────────────────────────────────────────┐
│ host 127.0.0.1                                               │
│   :3000 → multica-frontend-1  ghcr.io/multica-ai/multica-web │
│   :8080 → multica-backend-1   ghcr.io/multica-ai/multica-    │
│                                 backend（Go, /app/server）    │
│   (内部)  multica-postgres-1   pgvector/pgvector:pg17         │
│            backend_uploads 卷  /app/data/uploads              │
└────────────────────────────────────────────────────────────┘
        ▲                                        │
        │ 浏览器(web) / multica CLI / 桌面 App     │ DATABASE_URL
        │ bearer token（multica_*）               ▼
   用户侧 ~/{.multica, multica_workspaces} ←— daemon 长连接 claim 任务
```

- 前端 Next.js App Router 静态壳 + `/api/*` 代理后端；路由组 `(auth)`（登录/引导）、`(landing)`（营销页）、`[workspaceSlug]`（业务）。
- 后端 Go 单体：REST + daemon 任务协议（claim/messages/complete）+ SSE/WS 心跳；环境变量（compose 已读）：`JWT_SECRET`（必填）、`FRONTEND_ORIGIN`、`RESEND_API_KEY`/SMTP（邮件，未配则验证码打日志）、`GOOGLE_CLIENT_*`、`REDIS_URL`（可选）等。
- 更新通道：默认 GitHub，自托管可指 Gitea 镜像（v0.5.1 起）。

### 1.2 登录机制（无密码 OTP）

- `/login` 只有一个邮箱框 → 「继续」→ 后端生成 6 位验证码（`verification_code` 表，10 分钟有效，尝试次数限制表 `verification_code_attempts`）。
- **配置了 Resend/SMTP**：真发邮件。**未配置（本机现状）**：后端日志打印 `[DEV] Verification code for <email>: <6位>`——`docker logs multica-backend-1` 即可取码（自托管无邮件通道时的运维约定，也是弱点，见 §10）。
- 首次登录 → /onboarding 三步向导（关于你 → 工作区名+URL slug+任务前缀 → 认识 Mika 助手）→ 创建工作区。
- 会话：Bearer token；「更持久的登录」（v0.5.0 起刷新机制 `/api/auth/refresh`）。CLI/daemon 用 **Personal Access Token**（设置 → API Token 页生成，`mul_` 前缀）。
- 桌面 App 登录后可 `multica://auth/callback?token=` 桥接（web → 桌面 handoff，登录页「想用桌面应用？下载」）。

### 1.3 侧栏全局壳（每个业务页共用）

| 元素 | 位置 | 用法 |
| --- | --- | --- |
| `W <工作区名>` | 侧栏头 | hover 展开工作区切换器（多工作区列表/创建） |
| 搜索… `K` | 顶栏 | 命令面板/全局搜索（快捷键 K） |
| 新建任务 `C` | 顶栏 | 快速建任务（快捷键 C）——quick-create 流，由 agent 代建 issue |
| 切换左侧边栏 / 帮助 / 关闭 | 侧栏底/角 | 布局与帮助 |
| 导航分组 | 侧栏 | 收件箱·我的任务·聊天 ｜ 工作：任务·项目 ｜ 自动化 ｜ AI 团队：智能体·小队·Skills·运行时 ｜ 统计 ｜ 设置 ｜ 加入 Discord |

设计语言（实测 computed styles）：全站灰阶单色（--primary oklch(21% .006)≈近黑，背景 98.8% 白，半径 .5rem），Inter 正文 + Geist Mono 代码，营销页 Instrument Serif 102px 衬线；业务页**零 CSS 动画**——密度与速度优先。

---

## 2. 核心概念模型

```
workspace(工作区, slug=wgen) ── member(user×role: owner/admin/member)
   ├── issue(任务) ──┬─ project(项目, WGEN 前缀人类键)
   │                ├─ status/priority/labels/properties/stage
   │                ├─ parent_issue_id → 子任务树(Stage 拆单)
   │                ├─ comment(member|agent 作者, comment|system|progress 类型)
   │                └─ issue_wakeup(评论到达/定时 唤醒 agent 再跑)
   ├── agent(智能体: 指令+可见性+并发数+状态)
   │     ├── agent_skill ←→ skill(技能: SKILL.md+文件包, 可导入/版本化)
   │     ├── agent_mcp_server / workspace_mcp_server(MCP 工具面)
   │     └── runtime_mode local|cloud → agent_runtime(运行时)
   ├── squad(小队: leader+members+instructions 指引) ── squad_member(member_type=agent)
   ├── agent_task_queue(执行队列: issue×agent×runtime×attempt×work_dir)
   ├── chat_session/chat_message(聊天) · inbox_item(收件箱) · autopilot(自动化)
   └── agent_runtime → daemon_connection → 本机 daemon(~/.multica) ↔ ~/multica_workspaces
```

关键机制名词：
- **运行时（Runtime）**= 一台机器上的一个 CLI 编码代理进程（本机两台：Claude / OpenCode，device=WgendeMacBook-Pro.local）。agent 运行时配置可选 provider（跟随 CLI 配置）或 profile（自定义命令/模型）。
- **智能体（Agent）**= 运行时之上的人格包：名称/头像/描述/指令（何时用、关注什么、避开什么）+ 技能挂载 + 可见性（仅自己/整个工作区/指定成员）+ 最大并发数。状态机 idle/working/blocked/error/offline。
- **小队（Squad）**= agent 编制：leader（负责人徽标）+ 成员 + **小队指引**（派单政策文本，agent 可读）。支持归档/换头像/成员移除。
- **技能（Skill）**= `SKILL.md`（frontmatter: name+description 触发条件）+ 附加文件，`/api/skills/import` 导入（`--on-conflict overwrite` 覆盖更新），列「被谁使用」反查。分 workspace 技能与本地技能（local skills，.skill-cache）。
- **任务（Issue）**= 派工单元：标题/描述/状态（可自定义列）/优先级/受理人（**人或 agent**）/标签/属性（自定义字段）/阶段 stage/验收标准 acceptance_criteria/上下文引用 context_refs/父子树/依赖（blocks/blocked_by/related）。人类键 `WGEN-<number>`。
- **自动化（Autopilot）**= 触发器（评论/定时/webhook `/api/webhooks/autopilots/<id>`）→ 按 execution_mode 建任务或直接跑 agent；有规则版本表+配额/预约表，可配成员/小队身份与协作人。模板：每日新闻摘要、PR review 提醒、Bug 分诊、每周进度报告、依赖审计、文档检查。
- **任务唤醒（Issue Wakeup）**：v0.5.1 新增——issue 侧栏或自动化里配「有评论到达/按计划」重新唤醒 agent 续跑（`issue_wakeup`+`issue_wakeup_receipt` 表，`/api/issue-wakeups`）。
- **收件箱（Inbox）**= agent→人的回执流：action_required/attention/info 三级；归档/筛选/全部已读；unread-summary 轮询驱动角标。

---

## 3. 界面逐页手册（37 路由 + 15 设置子页，全部实测）

> 每条含：入口路由 → 页面内容 → 可交互元素逐个说明 → 背后 API。截图：`docs/research/liveui/shots/multica-NN-*.png`。

### 3.1 登录与引导
| 页 | 路由 | 用法与元素 |
| --- | --- | --- |
| 登录 | `/login` | 邮箱框（#login-email）→「继续」（发送验证码，57s 重发倒计时）→ 6 格 OTP 框（支持粘贴，autocomplete=one-time-code）→ 登录落 `/{slug}/issues`。「下载」链接 → /download 桌面端 |
| 新建工作区 | `/workspaces/new` | 三步：关于你 → 工作区（名称+「随机」按钮+URL 前缀预览+任务前缀）→ 认识 Mika；「退出登录」可用 |
| 邀请 | `/invitations` | 无邀请时空态「继续创建你自己的工作区」；有邀请则列出可接受 |
| Onboarding | `/onboarding` | 已引导用户自动跳 `/wgen/issues`（no-runtime-bootstrap 可自动起本机运行时） |

### 3.2 收件箱 `/wgen/inbox`（multica-06）
通知即任务：agent 完成/失败/待审批等回执按时间流；`筛选收件箱`（类型/严重级）、`归档`、`已归档` 视图、单条`通知操作`（处理/稍后）。API：`GET /api/inbox`、`/api/inbox/unread-summary`（角标）、`POST /api/inbox/…/mark-all-read`、`/page` 分页。

### 3.3 聊天 `/wgen/chat`（multica-07）
左=会话列表（`新对话`、会话`置顶`/`归档`/`聊天操作`菜单），右=对话区+输入框（富文本：加粗/斜体/删除线/代码/高亮/链接/列表/待办列表/引用；文件上传 input[type=file]）。开场建议卡：「你能帮我做什么？/ 建议第一个任务 / 推荐一个操作」。会话可绑 agent+项目（project-aware chat）；channel 渠道的会话也落 chat_session（`channel_chat_session_binding`）。API：`/api/chat/sessions`、`/api/chat/history`、`/api/chat/thread`、`/api/chat/pending-tasks(/has-any)`（输入中任务）。

### 3.4 任务 `/wgen/issues`（multica-08）
- 视图切换 pill：**全部 / 成员 / 智能体**（按受理人类型过滤，非独立路由）。
- 工具行：`视图`（保存的视图 issue_views + 列偏好）、`筛选`（状态/优先级/标签/属性过滤器，属性支持操作符）、`显示`（列显隐——表格可自定义列）、`看板`（board 视图：拖拽、泳道、live-sorting）。
- 状态条：`0 个智能体工作中`（点击看运行快照 /api/agent-task-snapshot）。
- 表格行：人类键 WGEN-N、优先级色点（高/中/低/无）、受理人头像（人/agent 同列）、标签、阶段。
- 服务端分页：`POST /api/issues/table/rows` + `POST /api/issues/table/facets`（分面计数），大工作区性能设计。

### 3.5 任务详情 `/wgen/issues/WGEN-2`（multica-09）
- 标题区：人类键+标题、状态/优先级/受理人/标签/属性编辑、`…` 更多菜单。
- 描述=富文本编辑器（同聊天工具条 + `复制代码`）；**待办列表**勾选项=流水线阶段进度（实测 8 个 checkbox）。
- `用选中内容创建子任务`（划词派生）；@mention 人/agent（`mention://member/<id>`、`mention://agent/<id>`）；评论时间线（agent 进度/system 事件混排）；评论 permalink（v0.5.1）。
- 侧栏：验收标准、上下文引用、附件（`…/attachments`）、依赖、**唤醒规则**（评论到达/定时）、属性。
- API：`GET /api/issues/<id>`、`/comments`、`/labels`、`/children`、`/timeline`、`/metadata`、`/sub-issues`、`/activity`、`/assignee-frequency`。

### 3.6 我的任务 `/wgen/my-issues`（multica-11）
四分 pill：全部/已分配/我创建的/**我的智能体和小队**（下属 agent 的任务并入个人视图）。其余同任务表。

### 3.7 项目 `/wgen/projects` + 详情（multica-12/13）
列表：`新建项目`（名称/描述/图标）、`筛选`、`创建时间` 排序、`表格` 视图、搜索框（"搜索项目..."）。列：名称/状态（计划中…）/优先级/进度。详情：项目内任务表（复用 3.4 组件：全部/成员/智能体 + 新建任务）+ `属性` 面板 + 资源（project_resource：本地文件夹/代码仓库，v0.5.1 起可选起始分支/commit）。项目视图（Project views, v0.4.32）。

### 3.8 智能体 `/wgen/agents`（multica-17）
列表：`新建智能体`、`我的/全部/已归档` pill、`筛选`、`最近活跃` 排序、搜索、每行`行操作`（编辑/归档/复制/删除）。信息卡：能力摘要（"能领取任务、留言…"）、运行次数、30 天活跃（`/api/agent-activity-30d`、`/api/agent-run-counts`）。

### 3.9 智能体详情 `/wgen/agents/<id>`（multica-18/19）
四标签：
- **概览**：身份卡（头像/名称/描述）、状态、最近运行。
- **工作**：该 agent 的任务列表（`GET /api/agents/<id>/tasks`）、`分配工作`（把 issue 指派给它）。
- **能力**：技能挂载开关（per-agent skill toggles）、对话开场白（conversation starters）、MCP 服务器、自定义环境变量（v0.2.17）。
- **设置**：指令编辑、可见性（仅自己/工作区/指定成员）、并发数、运行时绑定（默认=provider 或跟 CLI 配置）。
`智能体操作` 菜单：重命名/复制（实测存在「1111（副本）」）/归档/删除。归档 agent 详情多`恢复`按钮。

### 3.10 创建智能体三通道（multica-20/21/22）
1. `/wgen/agents/new`：分流页「选择起点」。
2. `new/ai`（对话式，v0.4.0 起）：选运行时 → `开始对话`（`/api/agent-builder/sessions`，草稿表 agent_builder_draft）→ 聊出配置后落库。
3. `new/manual`（检查并配置）：字段逐个——`agent-name`（占位"例如：深度研究智能体"）、`agent-description`（这个智能体做什么？）、`agent-instructions`（该做什么/关注什么/避开什么）、`更换头像`、`添加建议`（开场白）、`从工作区添加 skill`、运行时选择（本机 Claude/OpenCode，默认=提供方 / 跟随 CLI 配置）、可见性三档单选、`创建并打开`。

### 3.11 小队 `/wgen/squads` + 详情（multica-14/15/16）
列表：`新建小队`、`我的(n)/全部(n)`、成员头像堆叠。详情：`归档`、`更换头像`、`添加描述`、**成员区**（leader 徽标、`设为小队负责人`、`从小队移除`、`添加成员`）、**指引**（squad.instructions——派单政策，见 §8 实例）、小队任务列表、`小队操作`菜单。成员卡直接展示职责（审计队成员=「审计执行（枚举/候选/验证/证伪底稿…）」）。

### 3.12 Skills `/wgen/skills` + 详情（multica-27/28）
列表：`新建 skill`、筛选、`更新时间` 排序、搜索；列=名称/**被谁使用**/操作。详情：`概览`/`文件 N` 两标签；`skill-name` 编辑、一句话触发描述（"用一句话描述智能体什么时候应该使用这个 skill…"）、`添加标签`、`添加到智能体`（分发）、`删除 skill`、导入（`/api/skills/import`，GitHub 仓库导入，`--on-conflict overwrite` 更新）。

### 3.13 运行时 `/wgen/runtimes` + 详情（multica-24/25）
- 列表：本机 daemon 注册的机器卡（在线状态/名称）、`添加电脑`（配对码绑定新 daemon）、`和 Mika 开始`（引导式首跑）。
- 详情：`更新`、`重命名机器`、`添加自定义运行时`（自定义 CLI 命令+模型，profile）、`行操作`。一机多 profile（本机：Claude + OpenCode 两条，unique(workspace_id,daemon_id,provider|profile_id)）。
- 心跳：daemon WebSocket heartbeat；离线判定 last_seen（部分索引 status='offline'）。

### 3.14 自动化 `/wgen/autopilots`（multica-23）
`自动化`/`任务唤醒` 两标签；`新建自动化` 或从模板起：每日新闻摘要/PR review 提醒/Bug 分诊/每周进度报告/依赖审计（扫描安全漏洞和过时依赖包）/文档检查/`从空白开始`。配置面（实测 schema）：受理人（人或 agent/小队）、execution_mode（create_issue 等）、issue 标题模板、项目归属、触发器（评论关键词/定时 cron/webhook URL）、协作人、身份授权（v0.4.39）、手动跑一次（Manual runs v0.4.41）。配额：quota_period/quota_reservation。

### 3.15 统计 `/wgen/usage`（multica-31）
`用量`/`错误` 两标签；`30d` 窗口、`全部项目` 过滤；指标四选：**Token / 费用 / 耗时 / 运行数**；`按天/按周`；`刷新`；页脚「GMT+8 · 更新于 …」（本地时区+新鲜度）。数据源：task_usage → task_usage_hourly（rollup 脏标记增量汇总）、client_usage_daily。错误标签=失败任务归因（agent_error）。支持 prompt-cache 命中率（后端日志见 cache_read_ratio）。

### 3.16 账单 `/wgen/billing`（multica-32）
自托管=「账单（测试页）」外置：`打开 Stripe Billing Portal` 直通 multica.ai 云计费（`/api/v1/billing/*`：balance/batches/checkout-sessions/portal-sessions/price-tiers/transactions/topups；云侧另有 subscriptions/seats）。feature_flags.`billing_workspace_subscriptions`=false（自托管关闭）。

### 3.17 设置 `/wgen/settings?tab=<t>`（multica-30/43~56）
双栏：左=两级导航（个人设置/工作区设置两组），右=面板。**tab 是查询参数，URL 可直接分享/收藏**。15 个子页全实测：

| tab | 内容与可操作项 |
| --- | --- |
| profile 个人资料 | 名称、描述（示例文案「后端工程师（Go + Postgres）」——喂给 agent 的用户画像）、头像 |
| preferences 偏好设置 | 界面/语言（中/英/法/日/韩 i18n）/时区等 |
| notifications 通知 | web 通知、系统通知开关（notification_preference 表） |
| shortcuts 快捷键 | 全站快捷键表（K/C 等） |
| tokens **API Token** | 生成/撤销 PAT（`mul_` 前缀，CLI/daemon 登录用） |
| workspace 常规 | 工作区名/slug/任务前缀（WGEN）/危险区 |
| members 成员 | 成员列表/角色（owner/admin/member）/邀请（**成员管理在这里，/wgen/members 路由不存在=404**）/移除 |
| issue-statuses 任务状态 | 自定义状态列（v0.4.34 起每工作区可自定义，默认 backlog/todo/in_progress/in_review/done/blocked/cancelled） |
| labels 标签 | 名称+颜色管理 |
| properties 属性 | 自定义字段（KV/单选/多选，settings_resource_labels 分组） |
| quick-actions 快捷操作 | 一键下一步动作配置（v0.4.16） |
| repositories 代码仓库 | GitHub App / 自托管 Git（vcs_connection、`--ref` checkout、PR 集成 github_pull_request） |
| integrations 集成 | Composio 工具箱（composio_mcp_apps flag）、渠道（Slack/Telegram/Lark/DingTalk/WeCom）安装 |
| mcp **MCP** | 工作区级 MCP 服务器（重命名/换连接 v0.4.40），agent 级在智能体能力页 |
| （landing 区） | about/changelog/usecases/download 营销页 |

### 3.18 其他实测路由行为
- `/wgen`（工作区根）= **404**（无仪表盘首页，平台心智=直接进列表）。
- `/wgen/members` = 404（在 settings?tab=members）。
- `/wgen/runtimes/<id>/runtime` = 404（嵌套页不存在，运行时详情是单页）。
- `/workspaces` = 404（切换在侧栏 hover 菜单）。
- 分享链接：`/api/share-links/join`（share-link 邀请，v0.4.27）。

---

## 4. 执行机制原理（任务怎么真的被跑掉）

### 4.1 生命周期状态机（实测日志+schema）

```
人/自动化/chat 创建 issue ──▶ 指派 agent ──▶ agent_task_queue 入队
   (status: queued → dispatched → started → completed/failed/cancelled)
                                   │ attempt ×max_attempts, retry_of/rerun_of/delegated_from 链
                                   ▼
本机 daemon 长连接 POST /api/daemon/tasks/claim  ──领取──▶ 起 runtime 子进程
   work_dir = ~/multica_workspaces/<ws-hash>/<issue-key 或 task-*>/
   ├── workdir/        ← agent 的实际工作目录（注入 AGENTS.md + description.md）
   ├── multica-config/ ← 平台注入配置
   ├── output/         ← 产物（附件回传）
   └── logs/           ← 运行日志
                                   │
   进度回传: POST /api/daemon/tasks/<id>/messages（task_message, 增量）
   心跳:   GET  /api/daemon/tasks/<id>/status + daemon heartbeat
   终态:   POST /api/daemon/tasks/<id>/complete ──▶ inbox 通知 + usage 落账
```

- **task_roots 映射**：`~/multica_workspaces/.task_roots/<hash>/root.json` 记录 `{workspace_id, task_id, relative_path}`——server 任务 ID ↔ 本地目录的寻址表；`daemon_task_context.json` 标记 managed_by。
- **仓库型任务**：`.repos/<ws-hash>/` 检出代码（`--ref` 可选起始分支/commit，`.multica_co_authored_by` 标记共同作者）；本地文件夹资源=并行 local-folder mode。
- **AGENTS.md 注入契约**（实测全文）：runtime 启动时在工作目录写入 `<!-- BEGIN MULTICA-RUNTIME -->` 包裹的运行时文档，内容含：后台任务安全（turn 结束即 terminal、禁止 background-and-yield、外部 CI 不算交付验收）、agent 身份（你是 <名称>，ID <uuid>）、可用命令（`multica` CLI 用法与 `--output json` 纪律：stdout=数据 stderr=告警、禁止 2>&1 合并）、任务触发方式说明（issue 触发 vs quick-create 触发的不同 guardrails：quick-create 只允许一次 `multica issue create` 不重试）、技能路由（platform skill 发现）、输出规范（stdout 捕获自动转 inbox 回执、附件走 `--attachment`、运行时本地路径永不作为交付物/链接）。
- **CLI 命令面**（AGENTS.md 实测）：`multica issue create --title --description(-file|-stdin) --priority --status --assignee(-id) --parent --stage --project --due-date --attachment`（可重复）；另有 issue get/status/comment add、agents/squads/autopilots/projects/runtimes/skill import 等子命令（`multica --help`）。描述富文本必须走 `--description-file`（shell 内联会被改写，MUL-2904/#4182/#4252 已修）。
- **会话续跑**：session_id 存 chat_session/agent_task_queue；`force_fresh_session`、`session_rollout_missing`、retired_session_id 管理续跑与退役；issue 会话可恢复（v0.3.12 Session Resume）。

### 4.2 用量与计费管线
```
runtime 进程结束 ─▶ task_usage(单次: tokens/费用/耗时/provider/model)
              ─▶ task_usage_hourly(_dirty) ─▶ rollup_state 定时汇总 ─▶ /wgen/usage 图表
              ─▶ client_usage_daily（按天/客户维度）
后端日志样例: task prompt-cache usage provider=opencode model=zhipuai-coding-plan/glm-5.3
             input=33709 output=1155 cache_read=65536 ratio=0.66
```

### 4.3 渠道与桌面端
- IM 渠道（五族）：Slack（/issue 斜杠命令+Channel 集成）、Telegram、Lark/飞书（机器人+群聊）、钉钉（机器人+群+按群路由）、企业微信（文件/图片/语音/引用回复）——回调路由 `/{channel}/…`，表族 channel_*（inbound 审计/去重、outbound 卡片消息、reply/task delivery、user binding）。会话级控制在每个渠道聊天里（v0.4.35 Session controls）。
- 桌面 App（Electron 跨平台，`/download` dmg）：多标签、自动更新、通知、跨设备历史菜单；与 web 同账号线互通（`multica://auth/callback`）。
- 移动端：iOS App（v0.3.8 起）。

---

## 5. 渗透测试在 Multica 上的完整开展（本工作区实况）

### 5.1 编制与技能（实测 DB）

```
工作区 wgen
├── 项目「渗透作业交战」(WGEN 前缀)
├── 小队「安全红队」(6 agent)              小队「审计队」(2 agent)
│   ├── 安全红队-队长 (leader)             ├── 审计队-总控 (leader)
│   ├── 安全红队-总控 (账本唯一写者)        └── 审计队-审计员
│   ├── 安全红队-侦察                       （职责: 枚举/候选/验证/证伪底稿，
│   ├── 安全红队-渗透                          gensource 全子技能+gensift）
│   ├── 安全红队-分析
│   └── 安全红队-报告
├── agent 1111（绑定 gencpt 技能，容器渗透流水线）
└── 技能族: pentest-core(共享内核) · pentest-engagement(流程/模板)
           pentest-recon / pentest-exploit / pentest-verify / pentest-report
           report-delivery · gencpt(容器渗透 9-Phase)
```

### 5.2 交战流（安全红队小队指引原文提炼）

```
委托: 项目「渗透作业交战」建父任务
  │
  ▼
队长: 授权八问齐备性预检(对照 pentest-engagement §4.1 模板)
  │ 缺项 → 评论 @委托人补件, 父任务置 blocked, 不拆单
  ▼ 齐备
队长: 按 §4 拆 5 个 Stage 子任务(挂父任务) → 改派【总控】
  │
  ▼
总控(单写者): 逐 Stage 改派角色, 只交底稿经子任务评论+附件, 总控核验落账
  ├─ Stage 1 → 侦察 (L0 只读: 端口/服务/指纹)
  ├─ Stage 2 → 渗透 (轨道制, [L1]/[L2] 前缀=操作级别上限)
  ├─ Stage 3 → 分析   ├─ Stage 4 → 报告   └─ Stage 5 → 总控自办
  │
  ├─ L2 首次执行/deny-list/scope 修订/目标异常 → 审批升级:
  │    角色评论附原始命令+影响面+回滚 → 总控核验 → @所有者 → wakeup 等
  │    人回复 → approvals.tsv + timeline 留痕 (拒绝=永不执行)
  ▼
队长出口抽验(测试输出/timeline 链校验/脱敏抽检/清理核销) → 人点终态 done
```

**授权八问**（缺一不接单）：①目标（仅授权资产）②范围与深度（操作级别上限默认 L2）③排除项 ④RoE ⑤报告语言形式 ⑥时间窗 ⑦紧急联系人 ⑧测试账号与数据分级。
**L0-L3 分级**：L0 只读自动跑 / L1 无害探针声明请求量 / L2 受控复现需报备 / L3 破坏性默认只做理论推演。
**凭据四条**：真值只进 `vault/`（0600）；账本一律 `{{vault:cred-N}}` 占位；交付前反向扫描零泄漏；失效即 blocked 不重试。
**账本目录**（`~/tan-engagements/<GOAL-ID>/`，永不在 git 内）：goal/scope/assets/findings/evidence-index/timeline(链式哈希)/approvals/matrix/progress.tsv + evidence/ + findings-cards/ + reports/。

### 5.3 GenCPT 容器渗透流水线（WGEN-2 实测）

另一种形态——单 issue 触发全流水线：在「渗透作业」项目建 issue 指派给 **1111**（已绑 gencpt 技能），描述写：
```
用 GenCPT 对服务器 prod-k8s-01 做渗透测试
mode=full  scope=all  approval=standard
（可选）源码目录: /path/to/source
（可选）baseline: /path/to/last-report
```
- `mode`: full（9-Phase 30min+）/ fast（合规基线 ~10min）/ custom（指定检测项）
- `scope`: k8s / docker / containerd / all
- `approval`: standard / express / manual（L2 攻击验证审批模式）
产出在 `/tmp/gencpt-<session_id>/`：reports/{compliance,attack,summary}/、knowledge_graph(+viz.html)、evidence/{recon,compliance,attack,chains,poc}、progress.json（断点续传）、audit_log.json。各 Phase 由 gencpt 技能在单次运行内自动调度子代理（入口 SKILL→逐 Phase 分发），父/子 issue 只做跟踪与复盘。

### 5.4 为什么这套能跑真作业
- 任务面板=作战板（Stage 子任务树+待办勾选=流水线进度）；评论=agent 间+人机通信总线（mention:// 路由）；附件=底稿通道；inbox=审批回执；wakeup=挂起等审批再续跑——全部平台原语，无需自建。
- 执行面在你自己电脑：daemon 把 work_dir 落本地，evidence/vault 不出机；运行时可换 Claude/OpenCode(GLM)/任意自定义 CLI。

---

## 6. 数据模型速查（118 表分类）

| 域 | 表（代表性） |
| --- | --- |
| 身份/工作区 | user, workspace, member, workspace_invitation, workspace_share_link, verification_code(+attempts), personal_access_token |
| 任务 | issue(+status/label/property/view/wakeup/subscriber/dependency/source_context), comment(+reaction), project(+resource), pinned_item, quick_action |
| 执行 | agent_task_queue(55 列：attempt/parent_task/retry/rerun/delegated/escalation/branch/durable_work_dir…), task_message, task_token, task_usage(_hourly/_dirty/_rollup_state), client_usage_daily |
| 智能体 | agent(+builder_draft/invocation_target/to_label), agent_skill, skill(+file/to_label), squad(+member), agent_mcp_server, workspace_mcp_server |
| 运行时 | agent_runtime, daemon_connection, daemon_token, runtime_profile |
| 聊天/收件箱 | chat_session, chat_message, chat_pinned_agent, chat_draft_restore, inbox_item |
| 自动化 | autopilot(+trigger/run/rule_version/collaborator/subscriber/quota_*), webhook_delivery, sys_cron_executions, maintenance_job |
| 渠道 | channel_*(installation/binding/inbound_audit/dedup/outbound_*/reply_delivery/task_delivery…) + lark_*/dingtalk_*(+group_route/presence) |
| VCS | vcs_connection/commit_status/pull_request, github_installation/pending_*/pull_request(+check_run/suite) |
| 插件/其他 | plugin_*(package/file/version/installation/invocation/hook_schedule/secret/storage), feedback, contact_sales_inquiry, instance_telemetry_state, seat_capacity_outbox, activity_log |

## 7. API 速查（前端实测 + 二进制 strings 提取）
- 认证：`POST /api/auth/login`（OTP）、`/api/auth/refresh`、`/api/me`(+onboarding/complete/update)、`/api/cli-token`
- 全局：`/api/config`（feature_flags）、`/api/workspaces`、`/api/invitations`
- 任务：`/api/issues`、`POST /api/issues/table/rows|facets`、`/api/issues/<id>/{comments,labels,children,timeline,activity,attachments,metadata,sub-issues}`、`/api/issue-views`(+preference)、`/api/issue-statuses`、`/api/issue-wakeups`(+summaries)、`/api/assignee-frequency`
- 协作：`/api/chat/{sessions,history,thread,pending-tasks(+has-any),pinned-agents}`、`/api/inbox`(+unread-summary/mark-all-read)、`/api/comments`、`/api/pins`
- AI 团队：`/api/agents`(+`<id>/tasks`)、`/api/agent-activity-30d`、`/api/agent-run-counts`(+triggers)、`/api/agent-task-snapshot`、`/api/working-agents`、`/api/agent-builder/sessions`、`/api/squads`、`/api/skills`(+import)、`/api/runtimes`(+models/runtime-profiles)、`/api/mcp-servers`
- 自动化：`/api/autopilots`(+runs/deliveries)、`/api/webhooks/autopilots/<id>`、`/api/webhooks/{github,vcs,stripe}`
- daemon（CLI 专用）：`/api/daemon/tasks/claim|status|messages|complete`、`/api/daemon/workspaces`
- 其他：`/api/projects`、`/api/properties`、`/api/quick-actions`、`/api/notification-preferences`、`/api/upload-file`、`/api/attachments`、`/api/avatars`、`/api/feedback`、`/api/contact-sales`、`/api/v1/billing/*`、`/api/plugin-bridge/v1`、`/api/v1/pat/verify`

## 8. 版本演进要点（/changelog 128 版提炼）
- 0.1.x（2026-03）：起步（issue/agent/daemon 基本面）。
- 0.2.x（04-05 月）：Chat V2、GitHub 集成、技能导入、桌面跨平台、i18n、Mermaid、Kiro/自定义运行时、agent 环境。
- 0.3.x（05-06 月）：**小队（0.3.0）**、iOS、Helm 自托管、本地工作目录、泳道看板、Lark/Slack/飞书、Composio、自动人权限。
- 0.4.x（07-09 月）：自定义字段/快捷键/对话式建 agent/新视觉（0.4.0）；DeepSeek Harness 运行时（0.4.26）；工作区 MCP+分享链接（0.4.27）；保存视图（0.4.22）；侧栏重组+设置重组+手动跑自动化（0.4.41）；注释/线程大纲（0.4.42-43）。
- 0.5.x（09 月）：更精简 agent 运行、Inbox 归档、长效登录（0.5.0）；**唤醒规则、评论 permalink、项目起始分支、Gitea 更新源（0.5.1）**。
- 支持过的运行时全家福：Claude Code/Codex/Qwen Code/DeepSeek Harness/Kiro/Qoder/TRAE/Antigravity/CodeBuddy/Oh-My-Pi/ZeroClaw/Hermes/MiniMax/Grok/DevEco/Reasonix/OpenCode 2.x（自定义基座任意）。

## 9. 运维与故障排查（本机实测手段）
- 日志：`docker logs multica-backend-1`——每请求一行（method/path/status/duration/request_id/user_id/client_platform），任务事件（task completed/prompt-cache usage），daemon heartbeat；`[DEV] Verification code` 取登录码。
- 健康：`/api/config`（200 即通，返回 server_version）；postgres `pg_isready`。
- 常见：OTP 收不到→查邮件配置或日志码；任务不跑→runtimes 页看机器在线、`multica daemon status`；用量不新→task_usage_hourly rollup；慢→issues 服务端分页已默认，检查 facet 查询。
- 安全注意：compose 只绑 127.0.0.1（注释明确警告 Docker 绕过 UFW）；`JWT_SECRET` 必填强随机；无邮件通道时验证码打日志=内网可登（生产必配 SMTP/Resend 或限制日志访问）。

## 10. 已知边界与注意
- `.env` 含 39KB 全量注释配置样例（POSTGRES_PASSWORD 本机为弱哈希串，仅 127.0.0.1 可达）。
- 多副本：DATABASE_REPLICA_* 支持只读副本（业务显式选择最终一致路由）；Redis 可选集群模式。
- 未启用：billing_workspace_subscriptions、composio_mcp_apps、plugins_v1（flag=false）；agents_agent_builder/agents_skill_toggles/settings_resource_labels=true。
- 本手册基于 v0.5.1 实测；升级后以 /changelog 为准滚动更新本节。

# ARTEX 使用手册（实时滚动版 · 2026-10-15 起）

> **状态**: 完整版 v1.0（2026-10-15 漫游舰实机漫游 33 视图 + 源码只读深读 + liveui/2-artex.md、walk-artex.md 并入）。
> **性质**: 参照系统研究文档。**凭据**: http://localhost:8787 用户 ARTEX（本地部署）。
> **素材链**: ①漫游实证（DOM/按钮/参数，见 `docs/research/liveui/walk-artex.md` + `shots/artex-NN-*.png`）②源码只读 `ARTEX/`（web v2.2.0 + Go server 103 文件）③`docs/research/liveui/2-artex.md` 源码级报告。

---

## 0. 一句话与总架构

**ARTEX = AI 自主渗透测试控制台**：你给一句任务描述，planner Agent 持续规划意图、N 个 worker Agent 并发执行真实渗透工具、把事实/漏洞写回「双图」数据库，人只在五个点介入——**开局、导航、刹车、治理、收尾**。所有过程（思考/命令/输出/审批）全程留痕可回放。

### 0.1 技术栈（源码实证）

| 层 | 实现 |
| --- | --- |
| 后端 | Go 单二进制（`net/http`，103 个 server 文件，`go:embed` 内嵌前端）；端口 `-addr :8787` |
| 前端 | Next.js 16 App Router + React 19 + Tailwind v4 + shadcn/ui + Geist 字体；静态导出（NEXT_EXPORT）由 Go 同端口伺服 |
| 数据库 | **PostgreSQL**（pgx；`ARTEX_PG_DSN` 或 config.json；早期 SQLite 资料已过时；schema 启动幂等重跑=重启即迁移） |
| 流量代理 | 记录型 MITM（go-mitmproxy），`-proxy :8788`，CA 留痕，默认**关闭** |
| Agent 内核 | norma SDK（agentcore/tool/permission/harness/memory/transcript/subagent/plan/skill） |
| 实时 | REST + **SSE**（活动流/日志/更新进度；SSE 用 `?token=` 因 EventSource 不能带自定义头） |
| 认证 | `POST /api/auth/login` → JWT；前端存 `localStorage.artex_token` + 同名 cookie（7 天）；API 走 `Authorization: Bearer`；401 自动清凭据跳 /login |

### 0.2 总架构 ASCII 图

```
┌────────────────────────────────────────────────────────────────────────┐
│                     浏览器（Next.js 静态导出 SPA）                        │
│   仪表盘│对话│任务(+10页签)│发现│流量│资产│工作空间│系统×11 治理页          │
│   数据获取: 三档轮询(2/5/15s) + 单 SSE 多会话分发(seq 去重)               │
└──────┬───────────────────────────────────────────────┬─────────────────┘
       │ REST /api/* (JWT Bearer)                       │ SSE ?token=
┌──────▼───────────────────────────────────────────────▼─────────────────┐
│                       Go 单体 server (:8787)                             │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ auth/JWT │ │ REST 243  │ │ SSE 流式 │ │ Manager │ │ update/自更新 │  │
│  └──────────┘ │ 路由      │ │ activity │ │ 任务/引擎 │ └──────────────┘  │
│               └───────────┘ │ /logs    │ │ 生命周期  │                   │
│                            └──────────┘ └────┬────┘                     │
│  ┌──────────────────────────────────────────▼────────────────────────┐  │
│  │            engine（每任务: 1 plannerLoop + N worker goroutine）      │  │
│  │  planner 读态势→派意图(intents)→worker claimNext→执行→写回→再唤醒     │  │
│  └──────┬───────────────────────────────────────────────────────────┘  │
│  ┌──────▼─────┐  ┌───────────┐  ┌────────┐  ┌──────────────────────┐    │
│  │ guard/     │  │ 记录代理    │  │ enrich │  │ MCP·skills·memory·   │    │
│  │ intercept  │  │ MITM:8788  │  │ DNS/HTTP│  │ report·notify        │    │
│  │ 规则+judge │  └───────────┘  └────────┘  └──────────────────────┘    │
│  └───────────┘                                                           │
└──────┬──────────────────────────────────────────────────────────────────┘
       │ pgx
┌──────▼──────────────────────────────────────────────────────────────────┐
│                             PostgreSQL                                    │
│   资产图(全局共享): assets/companies/task_scope                            │
│   探索图(每任务): exploration_nodes/anchors/activity/intents              │
│   治理: intercept_*/llm_*/notify_*/conversations/tasks/...                │
└──────────────────────────────────────────────────────────────────────────┘
```

### 0.3 双图架构（核心心智模型）

「目标是什么」（资产图）与「测到什么程度」（探索图）分离，靠锚点相连：

```
  探索图（每任务独立·推进链）              资产图（全局共享·真值库）
  ┌─────────────────────────┐            ┌────────────────────────┐
  │ goal 目标                │            │ root_domain 根域名      │
  │  │ spawns               │            │   └ subdomain 子域名    │
  │ intent 意图 A            │──anchor──▶ │       └ service 服务    │
  │  │ yields               │            │           └ endpoint 接口│
  │ fact 事实                │──anchor──▶ │ app 应用 / ip / company  │
  │  │ derived_from          │            └────────────────────────┘
  │ intent 意图 B            │   锚点表 exploration_anchors(node,asset)
  │  │ proves               │   → 意图/事实/漏洞可反查「打了哪些资产」
  │ finding 漏洞             │   → 资产可反查「被哪些意图测过」= 覆盖度
  └─────────────────────────┘
```

- **planner** 读探索图态势，只在有未覆盖新方向时派意图进 frontier；**worker** 领一条意图、执行、写回两图即停。
- worker 间还有**过程级信息交换**：`search_all_worker_traces(q)` 检索其他 worker 的执行过程（不必等写成正式 fact），`get_worker_trace(intent_id, step_ids)` 取细节。
- planner 持**跨唤醒共享 todolist**：多步攻击链（注入→凭据→横向→提权）按依赖逐轮派意图，不错序不重复。

### 0.4 意图生命周期（一次探索的闭环）

```
 图变更(debounce) ─▶ planner 唤醒 ─▶ 读态势 ─▶ 派 0..N 意图(带 asset_ids)
                                                    │
                    ┌───────────────────────────────▼───┐
   frontier 意图队列 │ open(待领) → running(执行中)        │
                    │   ├▶ done(完成)                    │
                    │   ├▶ paused(人暂停) ─▶ resume      │
                    │   ├▶ blocked(模型故障重试耗尽)      │
                    │   ├▶ exhausted(步数/预算掐断)      │
                    │   └▶ deleted(用户假删除,留原因)     │
                    └───────┬───────────────────────────┘
                            │ worker claimNext
 真实工具(Bash/HTTP,经 guard 审批+代理留痕) ◀────────────┘
                            │
                 写回 fact/asset/finding + 每步 activity
                            │
                 图变更 ─▶ 再次唤醒 planner（闭环直到 prove_goal）
```

---

## 1. 登录与全局界面骨架

### 1.1 首次启动与登录
1. 首次访问跳 `/setup` 设置管理员密码（`POST /api/auth/init`）；之后进 `/login`。
2. 登录页：左侧近黑品牌区（同心圆+反白 logo），右侧表单——用户名固定只读 `ARTEX`，密码框，**《使用须知》必须打开并滚动到底点同意**后登录钮才可用（截图 artex-01）。
3. 登录成功 `POST /api/auth/login {"username","password"}` → `{"token": JWT}`；前端 `auth.setToken` 写 localStorage + cookie。已登录再访问 /login 会自动 replace 到 `/function/tasks`。
4. 侧栏底部有改密对话框与账户切换器（`POST /api/auth/change-password`）。

### 1.2 布局骨架
- 左侧 floating 侧栏（17rem，可折叠 Toggle Sidebar），两组 21 项（§1.3）。
- 顶栏：SidebarTrigger + 面包屑/标题 + **Command Palette（⌘J）** + **主题循环切换钮**（light/dark/preset）。
- 页面两种范式：**控制台型**（对话、任务详情会话页签：`grid lg:grid-cols-[18rem_1fr]` 左列表右记录，撑满视口）与**文档型**（其余页 MainContent 包裹 p-4/lg:p-6）。
- 布局偏好 7 个存 cookie：theme_mode/theme_preset/font/content_layout/navbar_style/sidebar_variant/sidebar_collapsible。
- 客户端 auth gate：无 token 渲染前即跳 /login（防保护 UI 闪烁）。

### 1.3 路由总表（21 项 IA + 认证壳）

| 分组 | 名称 | 路由 | 截图 | 一句话 |
| --- | --- | --- | --- | --- |
| 功能 | 仪表盘 | `/dashboard` | artex-02 | 全局总览+Token 消耗+活动流 |
| 功能 | 对话 | `/chat` | artex-03 | 主 Agent 人在环路对话（@引用） |
| 功能 | 任务 | `/function/tasks` | artex-05 | 任务中心（建/管/批量/归档） |
| 功能 | 任务详情 | `/function/tasks/detail?id=N` | artex-06~15 | 10 页签作业现场 |
| 功能 | 发现 | `/function/findings` | artex-16 | 跨任务漏洞汇总管理 |
| 功能 | 流量 | `/function/traffic` | artex-17 | MITM 录制回放+证据绑定 |
| 功能 | 工具执行 | `/function/commands` | artex-18 | 命令级执行审计 |
| 功能 | LLM 录制 | `/function/llm-records` | artex-19 | 模型调用录制明细 |
| 功能 | 资产 | `/function/assets` | artex-20 | 全局资产图/企业/DSL 搜索 |
| 功能 | 资产同步 | `/function/sync` | artex-21 | ScopeSentry 接入同步 |
| 功能 | 工作空间 | `/function/workspace` | artex-22 | 任务产物文件管理 |
| 系统 | LLM | `/system/llm` | artex-23 | 模型配置池+轮询+重试 |
| 系统 | Agent | `/system/agents` | artex-24 | 8 个 Agent 提示词/配置 |
| 系统 | MCP | `/system/mcp` | artex-25 | MCP 服务器接入 |
| 系统 | Skill | `/system/skills` | artex-26 | 技能库（zip 上传） |
| 系统 | 工具 | `/system/tools` | artex-27 | 工具注册表（系统+自定义） |
| 系统 | 通知推送 | `/system/notify` | artex-28 | 6 渠道通知+投递记录 |
| 系统 | 拦截规则 | `/system/intercept` | artex-29 | 命令拦截规则+judge 模型 |
| 系统 | 资产拦截 | `/system/intercept/assets` | artex-30 | 资产黑/白名单 |
| 系统 | 审批记录 | `/system/intercept/approvals` | artex-31 | 审批历史+审计快照 |
| 系统 | 日志 | `/system/logs` | artex-32 | 系统日志+SSE 实时 |
| 系统 | 系统配置 | `/system/settings` | artex-33 | 全局运行时开关 |
| 认证 | 登录/初始化 | `/login` `/setup` | artex-01 | — |

IA 洞察：**功能=作业现场，系统=供给与治理**。审批记录（系统组·治理视角）与任务详情「拦截审批」页签（作业视角）是同一数据的两个入口。

---

## 2. 功能页逐页手册

### 2.1 仪表盘 `/dashboard`（artex-02）

**呈现**：6 张统计卡 → LLM Token 消耗面板 → 活动流 → 发现摘要 → 任务表。

| 区块 | 内容 | 交互 |
| --- | --- | --- |
| 统计卡 | 活跃任务 N/M（按引擎态细分如「探索 1」）、确认发现（严重/高危/中危/低危四联）、资产节点（跨任务共享）、流量交互（捕获未开启时灰字）、Token 用量 | 点击跳对应页 |
| Token 消耗面板 | **旧版/新版双数据源切换**（activity 统计 vs 计量账本，口径差异在 tooltip 说明）；模型筛选（如 GLM）；合计=输入(未命中)+缓存命中+输出；**缓存命中率**大字；7天/30天/3月/6月/一年粒度切换；每日条图 | 全部只读筛选 |
| 活动流 | 最近 25 条事件，按 tool_use/tool_result/text/thinking/result 计数徽标；每条=角色(planner/work#N)+类型+摘要+相对时间 | 「查看任务」跳详情 |
| 发现卡 | 最新确认漏洞（严重度徽标+完整正文） | — |
| 任务表 | 任务/状态/引擎/目标进度/在途/最近活动 | 行点击进详情 |

**机制**：三档轮询——任务列表独立 5s（JSON 签名比对才 setState）、快源批 5s（7 API 并发）、慢源 15s（traffic/assets/agents/mcp/skills/tools/profiles/usage）。

### 2.2 对话 `/chat`（artex-03）——主 Agent 人在环路

**左栏**：会话列表按 Agent 分组折叠（置顶块+最近活跃组在前，折叠态 localStorage 记忆）；每项支持**双击重命名、pin 置顶、多选批删**（100/批，失败保留选择可重试）。空态显示「和 Auto 对话」人格卡。

**右栏会话区**：
- **懒建会话**：首次发送才 `createConversation`，避免空会话堆积。
- **@引用（9 类实体）**：输入 `@` 触发菜单，实体=漏洞/资产/企业/接口/IP/应用/域名/子域名/服务；token 格式 `@[类型#id 标签]`（如 `@[漏洞#12 后台弱口令]`），caret 正则检测；被引用对象作为上下文递给主 Agent（「把对象递给它」的导航方式）。
- **附件**：回形针上传到会话目录，chip 预览（名+大小+移除），随下条消息发；发送失败文本+附件原样塞回输入框。
- **/btw 旁路提问**：Agent 运行中输入 `/btw 问题` 打开侧栏 Drawer 独立问答，五段准备态文案（准备上下文/整理早期问答/压缩快照/超限缩减重试/回答中），**不污染主对话上下文**。
- **发送键位**：Enter 或 Ctrl+Enter（localStorage 偏好）；**IME 组合态放行**（`isComposing || keyCode===229` 不当发送——中文选字不误发）。
- **运行中**：发送键变红色停止键（`POST /conversations/{id}/stop`，只停本会话）；placeholder 变「Agent 正在回复，可输入 /btw 提问…」。
- **LLM 热切换**：会话头「更换」配置（`PATCH /conversations/{id}/profile`）。
- **Todo 气泡**：TodoPopover——TodoWrite 工具有状态时亮起，打开才拉 detail。
- URL `?c=<id>` 恢复选中会话；`?approval=N` 深链定位审批所在对话位置。

### 2.3 任务中心 `/function/tasks`（artex-05）

**列表**：当前任务/已归档双页签；状态/分类筛选+搜索（描述/目标/ID）。每行：ID、名称、描述、目标、状态徽标、目标进度 x/y、漏洞 严/高/中/低 四联、运行中 Worker 数、创建时间、运行时长、Token 三段式（入/缓/出）。

**行内操作**（图标钮）：重命名 / 暂停·恢复（`POST /tasks/{id}/control`）/ 置顶 / 归档（冷存储）/ 删除（选项见下）。

**批量**：选择本页全部 → 批量暂停/恢复（`/tasks/control/batch`）、批量归档（`/tasks/archive/batch`）、批量分类（`/tasks/category/batch`）。

**新建任务对话框字段**（源码实证）：

| 字段 | 说明 |
| --- | --- |
| 名称（可选） | 便于识别，如「Acme 官网渗透」 |
| 描述 **必填** | 测试对象与背景，如「测试 example.com 这个站点」；**开局一句话就是任务定义** |
| 目标 | 要达成什么，如「拿下后台管理权限」 |
| 任务超时（分钟，可选） | 留空=不限时 |
| planner 心跳（分钟） | 默认 10，防规划循环僵死 |
| 开启任务并发限制 + 同时运行上限 | 全局并发之外的任务级限制 |
| 分类 | 任务分类下拉+「分类管理」维护 |
| 模板 | 从模板带入描述/目标/分类/资产拦截规则；「另存为模板」把当前表单存为模板 |
| 任务级资产拦截规则 | 建 任务时即可配（见 §2.13 资产拦截） |
| LLM 配置链 | 选择本任务用的 profile 链（dnd 排序） |

**任务删除选项**（`DeleteTaskOptions`）：可选拠除范围（如是否连带资产/流量/记录）。

**归档语义**：归档进冷存储（`task-archives`），可还原（`/restore`），还原时做依赖阻塞检查。

### 2.4 任务详情 `/function/tasks/detail?id=N`——10 页签作业现场

sticky 头三行：标题行（返回+任务名+ID 码片+**LLM 配置链按钮**（显示当前配置·备用数；链耗尽=红「配置链已耗尽」Alert；终态任务也可换链——任务结束后主 Agent 对话仍走这条链）+StatusBadge+归档+暂停/恢复）→ 目标行 → 10 页签横滚。「拦截审批」页签带 **amber pending 计数 pill**（99+ 封顶，5s 轮询）。

#### 2.4.1 会话（默认页签，artex-06）——workers 实时流 ⭐核心视图
左栏四分组：
1. **主 Agent · 会话 #N**（+新建钮）：人的介入面，输入框 placeholder「给主 Agent 发消息，@ 引用漏洞、资产等…」，能力同 §2.2。
2. **规划 Planner · 态势研判**（实时徽标）：planner 的 thinking/text/tool_use 流。
3. **系统审计 · LLM 故障转移**：`llm_switch`/`llm_failover` 事件组。
4. **Workers**：每意图一行——状态图标 + `#意图ID` 码片 + 摘要标题 + 待审批⚠ + 未读 99+ + 实时徽标；继承意图标「来源 #N」。

**记录流**（transcript 渲染器）：user/intent 右气泡、result 全文 markdown、tool_use/tool_result 按 `tool_use_id` 配对成单行「命令+✓/✕」（折叠=命令+状态，展开=【命令】【输出】两段）、连续同 worker 文本合并、round 水平分隔线；IntersectionObserver 400px 预取懒加载。

**Worker 介入三件套**：
- running → **暂停**钮（`POST /tasks/{id}/intents/{iid}/control`）；
- paused → **发消息给 Worker**（4000 字上限+幂等 requestId；「服务端记录用户回合并 SSE 流回，无乐观插入」）或 **「直接继续」**（不发消息 resume）；
- /btw 运行中旁路（同 §2.2）。

**意图删除对话框**（双模式卡片二选一+必填删除原因，placeholder 示例：方向判断错误/目标已失效/重复）：
- **假删除**：置 deleted+记原因，保留产出，planner 收到通知重新规划；
- **真删除**：物理级联**仅由它支撑的**下游，toast 报「含 N 意图/M 事实/K 漏洞」。

**实时可靠性模型**（源码「Reliability model」注释）：每会话懒加载+反向分页缓存；首页 history 拿 `snapshotCursor` → 开**一条**任务级 SSE（`/api/exploration/activity/stream?task=&since=cursor`），帧按 `sessionKeyOf` 路由进各会话缓存；全部经 `mergeBySeq`（seq=身份，Map 去重+排序）合并——刷新/切页/休眠/断线重连永不丢帧不重复；EventSource 自动重连+Last-Event-ID 从 DB 续传；内存上限 MAX_KEEP=4000/会话。「实时」可计算定义：5s 内有活动才亮（1.5s tick 衰减）；主 Agent live 门控在真实 running 标志。SSE 断连侧栏常驻琥珀「重连中」（WifiOff）——**断链可见，绝不静默**。

**TokenMetrics**（会话头）：入/缓/出三 badge+轮次+时长；服务端持久化总数+客户端只加最后未完 usage 帧（防部分历史少算）。

#### 2.4.2 总览（artex-07）
- **任务描述与目标**（只读展示）；
- **目标管理**：最终可核验目标列表（增删改，**修改会通知规划者并复活任务**；状态 open/met/abandoned）；
- **操作约束**：禁/允条目（allow/deny），改动下一轮规划生效；
- **任务级资产拦截/允许**：域名/IP/URL（全等+模糊）+CIDR 七种匹配，「允许」=白名单（配置后仅命中允许的资产可测）；
- **资产测试覆盖度**：粗估百分比+按类型分解（如 app 0/1、endpoint 6/52、ip 4/4、service 13/40、subdomain 0/2）；
- **LLM Token 用量**：按模型分组表（调用次数/输入/输出/缓存读/命中率）；
- **测试范围**：覆盖度分母+授权边界（根域名/子域名/IP/网段/ICP/关键词/公司八类，每条带来源徽标：Agent 登记/自动/心跳）；
- **心跳**：引擎态/运行中 Worker 数/最近活动/目标进度/进行中意图（payload JSON 全文卡）。

> 实证：开局 planner 自动 `add_task_scope` 登记 127.0.0.1 + 理由——**范围/目标是 Agent 用工具写的，不是人填的表单**。

#### 2.4.3 探索链路（artex-08）
React Flow 画布：goal/intent/fact/finding/hint 节点+血缘边（spawns/derived_from/yields/proves），digest 超级节点合并、自算布局、去重边；Zoom In/Out/Fit View、节点拖拽。

#### 2.4.4 播报板（artex-09）
图事件时间轴直播流：类型筛选（目标/意图/事实/漏洞/提示/压缩）+最新在前+自动刷新开关；事件卡=#id+状态 chip+作者（work#N/planner）+优先级 P 数字+相对时间。机制：8s 轮询**只有最新在第 1 页才真刷列表**，其它位置只更新未读计数（免得翻页时内容在脚下变）；输入 300ms 防抖；hover 节点名片用已下发 refs 零额外请求。

#### 2.4.5 发现（artex-10）
任务内漏洞列表：严重度徽标+完整技术正文（不截断）；行操作：复测/深入（deepen）/删除。

#### 2.4.6 复测（artex-11）
漏洞复测看板：待复测卡+历次结论/证据；**发起复测**（`POST /exploration/findings/{id}/retests`）创建独立 retester Agent 会话，运行中显示「复测中」转圈；结论=仍可复现/已修复/无法确认；「已修复」自动更新漏洞处置状态；同漏洞复测中复用已有会话。可填修复版本/测试条件。

#### 2.4.7 测试资产（artex-12）
任务挂载的资产：六类计数 tab（根域名/IP/子域名/应用/服务/接口）+资产行+「新增测试资产」「移出任务」（`POST /tasks/{id}/assets`、`DELETE /tasks/{id}/assets/{assetID}`）。任务间可共享/继承资产。

#### 2.4.8 资产覆盖图（artex-13）
力导向布局（@antv/g6）：范围内资产+已测高亮+节点折叠展开；「刷新」。

#### 2.4.9 拦截审批（artex-14）
任务级审批视图：pending 队列（amber 优先）+全部记录表（#/工具/来源 work#N·#意图/匹配规则/参数 JSON/状态/申请·决定时间）；每行「展开审批」看详情快照（同 §2.14.3）。内联审批卡也会出现在会话流里（amber 卡：盾牌+工具名+#id+参数预览+**允许/拒绝**两键；挂载即查真实状态，已裁决显示状态 chip 不再给按钮；继承任务=只读）。

#### 2.4.10 报告（artex-15）
渗透测试报告 Markdown 全文渲染：摘要（确认数/资产分布）→逐条 [CRITICAL/HIGH/MEDIUM/LOW] 漏洞（PoC/攻击链/修复建议）；「复制」一键取走（`GET /api/report`）。**报告是一等公民，不是导出附件**。

### 2.5 发现管理 `/function/findings`（artex-16）

- **三视图**：全部发现（表）/按任务分组/按资产（树）；
- **统计头**：总数/待处理/严重/高危/中危/低危；
- **筛选**：严重度（全部/严重/高危/中危/低危）+状态+类型+任务 四维；按严重度排序；
- **导出**（`/exploration/findings/export`）；
- **行操作**：复测（同 §2.4.6）/ **深入 deepen**（`POST /exploration/findings/{id}/deepen`：派 Agent 对该漏洞做深度利用验证）/删除；
- **漏洞详情**（`/function/findings/detail?id=`）：证据绑定（版本化流量证据+排序）、血缘（lineage）、复测历史、状态下拉手动改（九态，见 §4.5）。

### 2.6 流量 `/function/traffic`（artex-17）

- 录制代理状态 chip（已停用/运行中+exchange 计数）；
- 目标筛选（按 host 下钻）/删除该目标/清空全部；
- 高级筛选：方法/状态码/响应长度区间；
- 表：时间/host/方法/URL/状态码/content-type/响应长度；行点击看 exchange 详情（请求/响应全文）；
- **关联到漏洞**：勾选流量→绑定到 finding 作为版本化证据（流量证据 role：request/response/body）；
- 数据来自 :8788 MITM 代理全量明文落库（`data/traffic/_index/index.sqlite`，无脱敏）——仅本地部署使用。

### 2.7 工具执行 `/function/commands`（artex-18）
命令级执行记录：任务/命令/状态/时长分页表+「统计」（`/commands/stats`：按工具聚合）。

### 2.8 LLM 录制 `/function/llm-records`（artex-19）
模型调用录制：按任务筛选明细（`/llm/records`）、按模型（`by-model`）、按任务汇总（`tasks`）、可删。

### 2.9 资产 `/function/assets`（artex-20）
全局资产图入口：六类计数卡（企业/根域名/IP/子域名/应用/服务/接口）+DSL 搜索+「新增企业」。资产跨任务共享、按公司归属；域名→子域→服务→端点父子关系与去重 key 由程序计算（Agent 只提交原始信息）。

### 2.10 资产同步 `/function/sync`（artex-21）
ScopeSentry 接入：MCP 地址+API Key（X-API-Key，留空保留原值）→保存并启用；数据源就绪后按**项目/任务**维度选择同步目标与资产类型（域名/子域/IP/端口/站点/端点…）→一键导入并按公司资产范围归并。

### 2.11 工作空间 `/function/workspace`（artex-22）
文件管理器：目录树（.tools/tasks/traffic/transcripts…）+新建文件夹/上传/刷新/删除/下载/读写（`/workspace/*`）。每任务有独立产物目录（如 `tasks/1/i137`），审批参数里的命令都在其中执行。

### 2.12 LLM 池 `/system/llm`（artex-23）⭐

**模型配置（profile）字段全表**（源码 LLMProfile）：

| 字段 | 说明 |
| --- | --- |
| 名称 | 如「OpenAI 生产」 |
| 格式 | openai / anthropic / openai-responses |
| Base URL | 如 https://api.openai.com/v1 |
| API Key | 掩码回显，留空不改 |
| 模型 | 手填或「从 API 加载可用模型」（`POST /llm/models`） |
| 代理 | 该配置独立代理 |
| 限速 | rate_per_second / rate_per_minute |
| context_window_k | 模型总容量（本地压缩阈值用，非请求字段） |
| thinking_type | 不发送（默认）/disabled/enabled |
| reasoning_effort | low/medium/high/xhigh/max |
| **优先级** | 轮询顺位：越大越先；**激活配置恒为链首，与本值无关** |
| **pool_exclude** | true=不作为故障转移目标（仍可被显式绑定） |
| streaming | 流式（默认）/非流式 |
| max_tokens + 字段名 | 单次输出上限；openai 格式可选 max_completion_tokens（推理模型） |
| session_header_key | 自定义会话头（头值=会话/意图 id；用于按 session-id 做提示缓存/粘性路由的网关） |
| 重试覆盖 | 建连/空响应/流中断（留空继承全局） |

**操作**：新建/编辑/删除/**设为激活**（`POST /llm/profiles/active`）/测试（`POST /llm/test`）。

**轮询配置区**：LLM 轮询开关（全局激活配置这条路径才轮询；绑定/pin 的路径默认独占，可开 `llm_pool_bind_fallback` 兜底）；绑定配置失败兜底开关；链序=激活配置→其余按 priority DESC（排除 pool_exclude）；熔断状态**进程级共享且落库**（重启后恢复未过期冷却窗）；「立即恢复：清除熔断，下次调用重试该配置」（`POST /llm/pool/reset`）。

**重试与退避（五层设计，源码 llmretry.go）**：

```
①建连失败 ── ②空响应 ── ③流中断(同 provider 安全窗口)   ← 每配置可覆盖全局默认
        │
        ▼  层内重试耗尽
④熔断(轮询冷却): fails 计数→trip→open_until 冷却窗   ← 进程级, 落库持久
        │
        ▼  当前配置熔断
轮询链切换下一个 profile (llm_switch 事件 SSE→toast)
        │
        ▼  整链耗尽
⑤意图重跑: model_error 的 work 重新入队 N 次+退避     ← 进程级
```

**运行时事件**：`llm_switch`/`llm_failover` 经 SSE 推 toast（按 mode 分级 error/success/info）+立即刷新 resolution（`GET /tasks/{id}/llm/resolution`）；任务头链按钮实时反映（如「配置链已耗尽」红 Alert）。

### 2.13 Agent `/system/agents`（artex-24）

**8 个 Agent**（内置 6+自定义 2，实测）：

| Agent | key | 定位 | 工具数 |
| --- | --- | --- | --- |
| 目标拆解 | goals | 把渗透目标拆成独立可验证子目标 | 2 |
| 规划 | planner | 读态势判定目标，只在有未覆盖新方向时补意图 | 20 |
| 主 | mainagent | 人机接口：观察进展，把人的意图落成 hint 或高优先级意图 | 21 |
| 执行 | worker | 领一条意图执行，写回知识图谱后停止 | 12（+1 Skill） |
| Auto | auto | 平台操作助手：用工具管理任务/资产/建 skill/自定义工具/MCP | 26（+1 Skill） |
| 渗透测试 | pentest | 独立渗透 agent：一人走完整链（侦察→利用→验证→收尾） | 6（+1 Skill） |
| 报告撰写 | reporter | 自定义：发现漏洞自动触发，写 Markdown 报告回写 | 12 |
| 漏洞复测 | retester | 自定义：从漏洞详情手动启动，出独立复测结论 | 2 |

**编辑器**（53KB 组件）能力：**prompt 版本化**（历史/预览 `prompt/preview`/重置 `prompt/reset`）、**wrapup 收尾词**（超时收尾词独立配置+重置）、**P3 触发器**（triggers：事件型自动唤醒，如 reporter 发现漏洞触发）、**可见性矩阵**（MCP/Skill/工具 对该 Agent 的可见性开关）、运行配置（LLM 绑定/预算）。提示词变量（`/agents/{key}/variables`）可插入。

### 2.14 MCP / Skill / 工具

**MCP `/system/mcp`**：添加 MCP 服务器（传输 http=Streamable HTTP 或 sse=旧版 SSE；旧版 URL 填 `/sse`，请求头 `Authorization=Bearer <token>`）；刷新工具列表（`/mcp/{id}/refresh`）；启用/删除。
**Skill `/system/skills`**：技能库总览+新建 Skill/上传压缩包（zip）/文件级编辑（新建文件/文件夹/删除）；用量（`/skills/{name}/usage`）；missing-skills 提示（Agent 引用但库中缺失的）。实测 3 个：api-recon/playwright-cli/scopesentry。
**工具 `/system/tools`**：系统工具/自定义工具两区。每工具=名称+类型+**调用次数**+完整 schema+护栏说明（如 add_company_scope「拒绝裸 TLD 与过宽网段（IPv4 前缀需 /16-/32）」）。自定义工具支持 **script 类型（Python）**——用系统配置的 Python 解释器跑；可「调用测试」（`POST /tools/custom/test`）；系统工具可重置（`/tools/{key}/reset`）。

### 2.15 通知推送 `/system/notify`（artex-28）

- **推送总开关**+全局设置（public_base_url 用于回调类渠道、digest 间隔）；
- **渠道 6 类**（notify 包）：钉钉 dingtalk / 飞书 feishu / 企业微信 wecom / Telegram / Email / Webhook（模板化）。每渠道：名称/启用/**模式 realtime 实时|digest 摘要**/配置（凭据字段掩码回显，留空=不改）/过滤器（接收哪些状态变更）/rate_per_min 限速；
- **投递记录**：五态（待发送/发送中/已送达/失败/已跳过）+重试（`/deliveries/{id}/retry`）+延迟测试（`/channels/{id}/test`）；
- 统计头：今日送达/待发送/失败/最久积压。

### 2.16 拦截规则 `/system/intercept`（artex-29）⭐

三个页签：
1. **拦截范围**（8 工具多选，实测）：Bash、WebFetch、web_search、shell_open、shell_send、Write、Edit、MultiEdit；
2. **拦截规则**表：优先级（越大越先，首条命中生效）/名称/目标（输入内容）/类型（正则/关键字）/模式/策略/启用。**策略三动作**：
   - `allow`：立即放行，跳过更低优先级规则；
   - `deny`：拦截，向模型返回拒绝消息；
   - `ask`：拦截+`intercept_pending` 记录+活动流插卡，等人在内联卡/审批页允许或拒绝（`POST /intercept/pending/{id}/decide`）；超时行为可配（SetTimeoutConfig）。
   内置 20 条（优先级 100/90/80）：100=rm -rf/删系统目录/mkfs/dd 覆写/Fork 炸弹/关机/kill -9 -1/shred/iptables -F/破坏性命令；90=SQL DROP/TRUNCATE/Mongo drop/Redis FLUSH；80=curl·wget DELETE/Python DELETE/axios DELETE/批量清空路径/数据外泄管道/删除类接口路径。可新建自定义规则。
3. **模型配置**（judge）：未命中规则且在拦截范围内的命令交给**模型语义判定**——低温度一次性 JSON 分类（allow/ask/deny）+强制说明格式；judge 用量单独计量（lane=judge，`/intercept/judge/usage` 可查）；模型异常有回退路径。

**判定链**：资产拦截（黑/白名单，先于一切）→ 命令拦截规则（优先级序）→ 未命中且在范围 → LLM judge（放行/转人工/拦截）→ ask 进 pending 等人。

### 2.17 资产拦截 `/system/intercept/assets`（artex-30）
资产级黑名单/白名单：域名(全等)/IP(全等)/URL(全等)/域名(模糊)/IP(模糊)/URL(模糊)/CIDR 网段 七种 kind+pattern+备注+启用。全局生效（区别于任务级）。任务级「允许」白名单在任务总览配置。

### 2.18 审批记录 `/system/intercept/approvals`（artex-31）
pending 队列+历史表（响应式隐藏列，matchMedia 算 colSpan 防展开错位）。行展开 **ApprovalDetail**：
- 左：工具请求 JSON+命令内容；
- 右：裁决+理由+来源定位+申请/决定时间；
- 折叠区：**模型审查上下文快照**（当时实际发给审查模型的输入，版本演进 v1/v2/v3）、会话审计片段、初判理由、执行输出及关联状态（ambiguous 并发不展示推测结果）、**SHA-256 指纹组**（参数摘要/审查配置/模型输入）；
- 「来源」深链：`?approval=N` → 目标会话页反向翻页定位 seq，行内 2px primary 边框高亮+居中滚动（ResizeObserver 防懒加载跑偏），顶栏「正在加载审批 #N 所在的对话位置…/已展开/无法定位+重试」。

### 2.19 日志 `/system/logs`（artex-32）
级别筛选（全部/info/warn/error）+暂停滚动（复制定位）+清空+历史分页+`/logs/stream` SSE 实时追加。

### 2.20 系统配置 `/system/settings`（artex-33）

| 卡片 | 开关/参数 | 原理（界面文案实证） |
| --- | --- | --- |
| 版本与更新 | 检查更新/立即更新/回滚 | 从 GitHub 下载→SHA256SUMS 比对→`-h` 冒烟→暂存 artex.new→退出由 start.sh 拉起换装；连续 3 次启动失败自动回滚 artex.old；dev 构建禁用 |
| 流量捕获 | 开/关 | 开=Agent HTTP 全量落库+注入 traffic_search/traffic_get 工具与代理配置；关=不注入；切换即时重建 Agent |
| Agent 自动绑定流量 | 默认关 | 漏洞入库时报告 Agent 核对已有 HTTP 关联流量再写报告（增加 Token 消耗） |
| 全局代理 | http/https/socks5(+认证) | 开捕获时作 MITM 上游；关捕获时注入 bash/WebFetch 出网；与搜索/LLM 代理独立 |
| 操作约束注入 | planner/worker 各自开关 | 任务操作约束拼进系统提示框定边界；下一轮生效 |
| 实验功能 | noa 上下文压缩 | 模型主动压缩长对话（norma v0.4.0），压缩原文归档任务目录 |
| 网络搜索 | 总开关+四源 | DuckDuckGo(免Key)/Brave/Tavily/DeepSeek(复用LLM)；各 Agent 单独启用 web_search（只返回标题/链接/摘要，抓正文归 WebFetch）；不走记录代理 |
| Python 解释器 | 路径 | 自定义 script 工具用；自动检测 python3 优先 |
| 工作并发 | Work Agent 数（默认 3） | 每任务并发 worker 数；对之后启动的任务生效 |
| 发送键位 | Enter/Shift+Enter 或 Ctrl+Enter | 会话输入框共用；只存本浏览器 |

---

## 3. 完整渗透作业流程（怎么在上面开展一次渗透测试）

### 3.1 开局（5 分钟）
1. **配 LLM**（`/system/llm`）：新建配置（格式/Base URL/Key/模型）→测试→设为激活；可再建备用配置调优先级组成故障转移链。
2. （可选）**治理预置**：拦截规则页确认内置 20 条+配 judge 模型；资产拦截加黑名单（如禁止打生产网段）；通知渠道配钉钉/飞书接收状态变更。
3. **建任务**（`/function/tasks`→新建任务）：一句话描述+目标，如「测试 http://target.example.com 这个站点；要达成：拿到后台权限」。可从模板带入、选分类、配任务级资产拦截、选 LLM 链。
4. 提交后进任务详情：开局 planner 自动`add_task_scope`登记范围（带理由）→`set_goals`设目标→派第一批意图。**范围/目标是 Agent 用工具写的**，人不必填表。

### 3.2 作业中（人在五个点介入）
- **看**：任务详情会话页签=驾驶舱（四分组实时流）；仪表盘看总量（发现数/Token/命中率）；播报板看事件直播；探索链路图看攻击面推进；覆盖度看 23%→100%。
- **导航**：给主 Agent 发消息并用 `@漏洞#12` `@资产#53` 把对象递给它；worker 卡住的方向用意图删除（假删+原因回流 planner 重规划）。
- **刹车**：审批卡允许/拒绝（内联或拦截审批页签）；暂停任务/暂停单个 worker；操作约束增禁条目。
- **治理**：总览页加操作约束（如「禁止爆破」「仅测当前端口」）；任务级资产拦截。
- **供给**：LLM 池加备用配置/清熔断；MCP/Skill/工具按需接入。

### 3.3 收尾
1. **报告**（任务详情→报告页签）：Markdown 全文渲染→复制交付；
2. **复测**：对要验证修复的漏洞发起复测（独立 retester 会话，结论自动回写状态）；
3. **归档**：任务归档冷存储（可还原）；工作空间下载产物（transcripts/traffic）。

### 3.4 live 战例（烛龙靶场，实测时间线）
- T0 建任务「渗透 http://localhost:3081（admin/Whg1995!），竟可能多识别漏洞」；
- T0+几分钟：planner 登记 127.0.0.1 范围+派可达性/指纹意图；
- ~80min：5 发现、44 资产、5.5M 入 token（缓存 95%）；
- ~2h40m：**39 发现（严重7/高危17/中危10/低危5）**、105 资产、覆盖度 23%、19 条审批（内置 DELETE 规则自动拒绝多条破坏性命令）、3 worker 在途；
- 期间 worker 意图带完整纪律（「≤5 次定向尝试、绝不批量喷洒」「红线：绝不触发 update/apply、全程只读」——审批红线在派单时写进意图）。

---

## 4. 机制原理深读

### 4.1 引擎闭环（事件驱动）
图变更 debounce→planner 唤醒（每次全新会话，共享 todolist 保多步链稳定）→读态势（graph_overview 预取+coverage/scope）→派 0..N 意图（大多数唤醒派 0 个）→worker claimNext→取意图 asset_ids 作初始信息→真实工具执行（经 guard+代理）→写回 fact/asset/finding+每步 activity→图变更→再唤醒，直到 `prove_goal`。

### 4.2 SSE 可靠性模型（会话页签）
一条任务级 SSE 多路分发；`snapshotCursor` 让 history 与流无缝衔接；`mergeBySeq`（seq=身份）去重排序；`reqTokenRef` 请求令牌防迟到响应污染；MAX_KEEP=4000 裁旧（仅当用户没在读历史）；冷会话只留尾部 4 条记账帧；断线 EventSource 自动重连+Last-Event-ID 续传。

### 4.3 审批判定链（guard/intercept）
- 规则优先级序匹配（highest first），三动作 allow/deny/ask；
- ask 写 `intercept_pending`+活动流插卡+`decide` 端点等人，超时可配；
- **judge 输入边界**（prompt.go 强制拼接，防提示注入）：只审当前调用（tool_name+完整 arguments），不带任务描述/约束/历史；background 仅显式绑定的当前用户消息；背景不能指定裁决；路径不能单独证明归属；输出强制 JSON `{decision: allow|ask|deny, comment: "实际操作：…；成功后的后果：…；命中规则：…"}`；
- **审计**：Trace 属于一次 Prompt 调用；上下文 24 条/条目 8KB/提示 32KB/输出 64KB 上限；SHA-256 指纹组（参数/审查配置/模型输入）；SDK 无 tool ID 时仅唯一匹配才关联，绝不猜。

### 4.4 LLM 轮询与五层重试
见 §2.12 图。要点：链序=激活→priority DESC（同优先级 id ASC 稳定序）；熔断进程级+落库（重启恢复未过期冷却）；五层中①②③可 per-profile 覆盖、④⑤全局；llm_switch/failover 事件 SSE→toast。

### 4.5 状态语义中枢（status.ts，9 域）
集中映射杜绝页面各自配色；tone 软底色 chip，**唯独 rose（严重）实心白字**（严重>高危软红的层级）。语义边界金句：
- **blocked**=模型/API/网络故障重试耗尽（非目标拦截）；**exhausted**=预算被掐断只写回部分；**stopped**=软删历史；**deleted**=用户假删除（保留血缘，原因在 delete_reason）。
- 九域：意图 8 态/任务 7 态/严重度 4/发现 9 态（待处理·处理中·已确认·已处理·已修复·误报·忽略·重复·风险接受）/引擎 4/目标 3/审计 2/节点 3/投递 5。

### 4.6 前端状态管理
无全局 store（唯一 store=preferences）。页面级 useState+useEffect+三层模式：轮询分档（互斥锁+alive+瞬时失败保留旧值）、单 SSE 多路分发（§4.2）、「实时」可计算定义（5s 窗口+1.5s tick 衰减；主 Agent 门控真实 running）。

### 4.7 活动类型学（Activity）
`round/thinking/text/tool_use/tool_result/usage/result/user/intent/intercept_request/llm_switch/llm_failover`，每条带 seq/worker/ts/is_error/summary(+metadata)。usage 行=一次模型调用（记账），不渲染。

---

## 5. 逻辑架构图解（ASCII 汇总）

### 5.1 人在环路五介入点
```
人 ──┬── ①开局: 一句话建任务(+模板/分类/LLM链/拦截)
     ├── ②导航: 主Agent消息 @漏洞#12 @资产#53 / /btw旁路 / 假删意图(原因回流planner)
     ├── ③刹车: 审批卡 允许|拒绝 / 暂停任务 / 暂停worker→留言|直接继续
     ├── ④治理: 操作约束 / 任务级+全局拦截规则 / judge模型 / 通知
     └── ⑤收尾: 报告复制 / 复测发起 / 归档 / 产物下载
```

### 5.2 审批数据流
```
worker tool_use ─▶ 资产拦截(黑白名单) ─▶ 命令规则(优先级序)
                        │ hit               │ hit
                        ▼                   ▼
                     deny/allow        allow|deny|ask
                                            │ ask
                                            ▼
                              intercept_pending + 会话流 amber 卡
                                            │ 人 或 超时
                                            ▼ POST /decide
                                     执行或取消 + 执行输出回填
                                            │
              审批记录页: 请求JSON|裁决|审查快照|SHA-256指纹|深链定位
```

### 5.3 前端数据流
```
 REST 轮询(三档)          SSE 单条多路
 ┌────────────┐   ┌──────────────────────────┐
 │任务5s│快5s│慢15s│   │/exploration/activity/stream│
 └──────┬─────┘   └──────────┬───────────────┘
        │  JSON签名比对才setState        │ frame按sessionKeyOf路由
        └──────────┬────────────────────┘
                   ▼
        每会话 SessionState{items/loaded/unread/earliestSeq}
                   │ mergeBySeq(seq=身份)
                   ▼
        transcript 渲染(tool_use↔result配对/懒加载400px预取)
```

---

## 6. API 面摘要（243 注册路由，按组）

| 组 | 代表端点（方法 路径） |
| --- | --- |
| 认证 | POST /api/auth/login·init·change-password；GET /api/auth/status |
| 任务 | GET/POST /api/tasks；PATCH /api/tasks/{id}；POST …/control·archive·chat/stop；POST /tasks/control/batch·archive/batch·category/batch；POST …/intents/{iid}/control·messages·rerun；POST …/intents/rerun-blocked |
| 探索图 | GET /api/exploration/{activity·activity/history·activity/stream·graph·intents·frontier·nodes·findings·findings/stats·findings/{id}·findings/{id}/lineage·main-sessions·tokens}；POST …/findings/{id}/deepen·retests；PATCH …/findings/{id} |
| 审批 | GET /api/intercept/{pending·pending/{id}·history·history/{id}·history/{id}/execution·task/{taskID}·rules·judge·judge/usage·tool-config}；POST …/pending/{id}/decide·rules·rules/{id}/toggle；PUT …/rules/{id}·judge·tool-config |
| 资产拦截 | GET/POST/PUT/DELETE /api/asset-intercept/rules(/{id})；POST …/{id}/toggle |
| 资产/企业 | GET /api/assets·counts；GET/POST /api/companies；POST /api/companies/{id}/scope·reattribute |
| 流量 | GET /api/traffic{·hosts·exchange·blob}；DELETE /api/traffic{·/all·/hosts} |
| LLM | GET /api/llm{·/pool·/profiles·/records·/retry-policy}；POST /api/llm{·/test·/models·/profiles·/profiles/active·/pool/reset·/retry-policy}；PUT /api/tasks/{id}/llm |
| 会话/对话 | GET/POST /api/conversations(/{id}/messages)；POST …/delete/batch·/{id}/stop·/{id}/messages；PATCH /{id}·/{id}/profile；POST /api/chat·chat/upload |
| Agent | GET/POST /api/agents(/{key})；PUT …/prompt·config·visibility·wrapup·wrapup/task-timeout；POST …/prompt/preview·prompt/reset·triggers |
| MCP/Skill/工具 | /api/mcp(/{id}/tools·refresh)；/api/skills(/upload·{name}/files·usage·missing)；/api/tools(/custom·custom/test·{key}/reset) |
| 通知 | /api/notify/{channels·deliveries·meta}；POST …/channels/{id}/test·deliveries/{id}/retry |
| 工作空间 | GET /api/workspace/{list·read·download}；POST …/mkdir·upload·write·delete |
| 同步 | GET/POST /api/sync/scopesentry/{status·projects·tasks·datasource·sync} |
| 系统 | GET /api/{health·stats·settings·logs·logs/history·logs/stream·report·update/check·update/stream·audit·commands·commands/stats}；POST /api/{settings·gc·update/apply·update/rollback·settings/python/detect·settings/web-search/test} |
| 归档/模板/分类 | /api/task-archives(/{id}/restore·restore/batch·delete/batch)；/api/task-templates；/api/task-categories |
| 可见性 | /api/visibility/{kind}/{id}·skill/{name}(+toggle) |

---

## 7. 部署运维（README 实证）

- **安装**：install.sh 一键（全 Docker 或本地编译）；docker compose up -d（镜像 mianhuatang11/artex）； Releases 二进制（用 start.sh 守护启动——页面一键更新依赖它拉起）；源码 `cd web && npm ci && npm run build:static && cp -r web/out server/webui/dist && CGO_ENABLED=0 go build -tags embedui`。
- **配置**：config.json database 或 ARTEX_PG_DSN；LLM 环境变量 ANTHROPIC_API_KEY/OPENAI_API_KEY（或 UI 配）；`./start.sh -addr :8787 -proxy :8788`。
- **更新**：系统配置页一键更新（下载→SHA256SUMS 比对→冒烟→换装→失败自动回滚）；更新会中断运行中任务；数据库重启即迁移。
- **反代 HTTPS**：8787 同源伺服 UI+API+SSE，公网只开 443；Nginx 必须 `proxy_buffering off`（否则 SSE 收不到事件）。
- **合规**：AGPL-3.0；作者声明仅供本地隔离环境学习验证，禁止对线上系统使用。

---

## 8. 实证索引

- **漫游截图**：`docs/research/liveui/shots/artex-01~33-*.png`（32 张 full_page，编号对应 §1.3 表与 walk-artex.md §1）。
- **漫游报告**：`docs/research/liveui/walk-artex.md`（33 视图清单+视觉实测+落点建议）。
- **源码坐标**：`web/src/lib/{api·auth·status·chat-mentions}.ts`；`web/src/app/(main)/` 路由树；`web/src/components/{transcript·approval-records·mention-textarea·side-question-workspace·task-llm-profile-chain}.tsx`；`web/src/app/(main)/function/tasks/detail/_tabs/sessions-tab.tsx`；`server/{server·intercept·llmpool·llmretry·notify_api}.go`；`intercept/{intercept·prompt·review_context·trace}.go`；`notify/`（dingtalk/feishu/wecom/telegram/email/webhook）。
- **live 抓取**（2026-10-15 16:2x）：任务 #1 运行 2h40m、39 发现、105 资产、Token 73.3M（缓存 95%）、19 审批、6 流量、8 Agent、3 skill、2 MCP。

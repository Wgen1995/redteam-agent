# ARTEX 活体参照系统分析报告
**目标**： http://localhost:8787 （ARTEX — 自主渗透测试控制台）
**用途**： 探隐 v0.9d UI 升级批 + 功能规划决策输入
**分析方法**： ①HTTP 只读探测（仅 GET + 登录 POST，未触发任何扫描/建任务/状态变更）；②源码只读分析（`ARTEX/` 目录，未修改任何文件、未执行 git）。源码直读为主、HTTP 用于验证 live 形态。
**分析日期**： 2026-10-15

---

## 0. 系统事实卡（先校准背景认知）

| 项 | 事实 | 与任务简报的差异 |
| --- | --- | --- |
| 登录 | `POST /api/auth/login` → `{"token":"<JWT>"}`，后续 `Authorization: Bearer <token>`；SSE 用 `?token=` query（EventSource 不能带自定义头） | 与简报一致，已验证 200 |
| 版本 | web `package.json` = 2.2.0；`/api/health` = `{"ok":true,"service":"artex","version":"dev"}` | — |
| 后端 | Go `net/http`，方法+路径模式路由（`GET /api/...`），103 个 server 文件；单体二进制 `go:embed` 内嵌前端（`-tags embedui`） | — |
| **数据库** | **PostgreSQL**（docker-compose + pgx；README v2.2.0「双图架构」明写 Postgres；config 只认 `ARTEX_PG_DSN`）。go.mod 仅残留 1 处 sqlite 字样 | ⚠️ 简报说 SQLite(artex.db)——**当前源码已迁移 PostgreSQL**，按 Postgres 理解 |
| 前端 | Next.js **16.2.9** App Router + React **19.2.7** + Tailwind **v4**（CSS-first）+ shadcn/ui（radix-ui 1.6 + @base-ui/react）+ sonner/recharts/@xyflow/@antv-g6 + Geist/GeistMono/**GeistPixel** 字体 + lucide 图标。底子是 **Saasable Datum 类商业模板**（7 个 client-cookie 偏好：theme_mode/theme_preset/font/content_layout/navbar_style/sidebar_variant/sidebar_collapsible） | — |
| 交付形态 | 静态导出（`NEXT_EXPORT=1`，无 Server Actions），Go 同端口伺服 UI+API+SSE → 反代只开 443 也能用 | — |
| 首屏体积 | shell 引 26 个 chunk ≈ 2.0MB JS + 280KB CSS | — |
| 页面族 | 仪表盘 / 对话 / 任务(+详情10页签) / 发现 / 流量 / 工具执行 / LLM录制 / 资产 / 资产同步(ScopeSentry) / 工作空间 / LLM / Agent / MCP / Skill / 工具 / 通知 / 拦截规则 / 资产拦截 / 审批记录 / 日志 / 系统配置 | 与简报一致，比简报更全 |
| agent 内核 | 自研 `norma` SDK（agentcore/tool/permission/harness/memory/transcript/subagent/plan/skill），四角色：goals/planner/**worker×N**/mainagent | — |

---

## ① UI 设计解构（源码级）

### 1.1 布局骨架

**路由组织**（`web/src/app/`）：
- `(auth)/`：login、setup（首次初始化密码）
- `(external)/`：根路由重定向壳
- `(main)/`：全部业务页 + `_components/`（sidebar 系列 + main-content + update-badge）

**主布局**（`(main)/layout.tsx`，86 行）：
- `SidebarProvider(floating variant) + AppSidebar + SidebarInset` 三件套；`--sidebar-width: calc(var(--spacing)*68)`（17rem）
- **客户端 auth gate**：无 token → 清 cookie 跳 /login，渲染前拦截避免保护 UI 闪烁（注释明确写了防 cookie/localStorage 不一致导致的无限弹跳白屏）
- 6 个布局偏好全部从 cookie 读取（静态导出不能用 next/headers），hydration 后再纠正

**页面内部骨架两种范式**：
- **控制台型**（chat、任务详情会话页签）：`grid lg:grid-cols-[18rem_1fr]` 左列表右记录，`h-[calc(100svh-13rem)]` 撑满视口减去头部；手机端 (`<lg`) 列表折叠成标题行（`listOpen`），标题栏显示当前会话名 + 其它会话未读合计（`hiddenUnread`）——注释：手机屏列表固定占 10~15rem 会把记录挤到只剩标题和输入框
- **文档型**（其余页）：`MainContent` 包裹，`data-content-padding` 控制 p-4/lg:p-6

**任务详情**（`function/tasks/detail/page.tsx`）：sticky 头部三行——标题行（返回+名称+ID 码片+**LLM配置链按钮**+StatusBadge+归档+暂停/恢复）→ 目标行 → 10 个页签横滚；「拦截审批」页签带 **amber pending 计数 pill**（99+ 封顶，5s 轮询 `interceptTask`）。

### 1.2 导航 IA（`navigation/sidebar/sidebar-items.ts`）

两个分组 21 项，全部 lucide 图标：
- **功能**（10）：仪表盘/对话/任务/发现/流量/工具执行/LLM录制/资产/资产同步/工作空间
- **系统**（11）：LLM/Agent/MCP/Skill/工具/通知推送/拦截规则/资产拦截/审批记录/日志/系统配置

IA 的关键洞察：**「功能=作业现场，系统=供给与治理」**。审批记录被归入系统组（治理视角），而任务详情里还有任务级拦截审批页签（作业视角）——同一数据两个入口。

### 1.3 组件库

- `components/ui/`：60 个 shadcn 风格基础件（bubble/message/message-scroller 是聊天专用三件套；empty/skeleton/spinner/kbd/marker 等状态件齐全）
- 业务组件（`components/` 顶层 15 个，按大小）：

| 组件 | 行数级 | 职责 |
| --- | --- | --- |
| agent-editor.tsx | 53KB | Agent 全生命周期编辑（prompt 版本/wrapup/触发器/可见性/配置） |
| approval-records.tsx | 38KB | 审批记录表+队列+详情快照（见 1.6） |
| transcript.tsx | 31KB/775行 | **执行重放渲染器**（会话/任务/对话三处复用） |
| exploration-graph.tsx | 27KB | 探索链路图（自算 layout + @xyflow，digest 超级节点合并、去重边） |
| mention-textarea.tsx | 14KB | @引用输入框（9 类实体） |
| side-question-workspace.tsx | 11KB | /btw 旁路提问侧栏（Drawer/Resizable 双形态） |
| task-llm-profile-chain.tsx | 8KB | LLM 配置链排序编辑器（dnd-kit） |
| approval-execution-focus.tsx | 4.9KB | 审批→会话深链定位（见 1.6） |
| todo-popover.tsx | 3KB | TodoWrite 状态气泡（打开时才拉 detail） |

### 1.4 状态管理写法（探隐最该学的工程模式）

**没有 Redux/Zustand 全局 store**（唯一 store 是 preferences）。全部页面级 `useState + useEffect`，靠三层模式保证正确性：

1. **轮询分档**：仪表盘三档——任务列表独立 5s（最贵、JSON 签名比对才 setState）、快源批 5s（7 个 API `Promise.all`）、慢源 15s（traffic/assets/agents/mcp/skills/tools/profiles/usage 8 个）。全部 `loading` 互斥锁 + `alive` 标志 + 「瞬时失败保留旧值下轮重试」。
2. **单 SSE 多路分发**（`sessions-tab.tsx` 顶注释即「Reliability model」，配套文档 `docs/task-session-history-sse-remediation.md`）：
   - 每个会话（main:seg / plan / intent:id / system）各自懒加载、反向分页缓存（`SessionState`：items/loaded/loading/hasMore/earliestSeq/**unread**/lastTs）
   - 首页 history 拿 `snapshotCursor`，然后开**一条**任务级 SSE `/api/exploration/activity/stream?task=&since=cursor`，帧按 `sessionKeyOf(activity)` 路由进各会话缓存
   - history 与 SSE 在 cursor 处无缝衔接，全部经 `mergeBySeq`（seq=身份，Map 去重+排序）合并 → 刷新/切页/休眠/断线重连**永不丢帧不重复**；EventSource 自动重连 + `Last-Event-ID` 从 DB 续传
   - 内存上限 `MAX_KEEP=4000`/会话，超出裁最旧（仅当用户没在读历史时）；未加载的冷会话只保留尾部 4 条 usage/result 记账帧
   - `reqTokenRef` 每 key 请求令牌：迟到的旧响应只能写自己的 key，永不污染当前视图
3. **「实时」的可计算定义**：`STREAM_WINDOW_MS=5000`（5s 内有活动才算 live），1.5s `setTick` 定时重渲染使 staleness 自然衰减；主 Agent 的 live 判定更严——门控在真实 running 标志上，且 `kind='result'` 落地立即摘牌。

**活动类型学**（`lib/types.ts` Activity）：`round/thinking/text/tool_use/tool_result/usage/result/user/intent/intercept_request/llm_switch/llm_failover`，每条带 seq/worker/ts/is_error/summary(+metadata)。usage 行=一次模型调用（轮次记账），不渲染。

### 1.5 视觉系统

- **token**（`app/globals.css`）：Tailwind v4 `@theme`，默认 preset 中性 zinc（`--primary: oklch(0.205 0 0)` 近黑），`--radius: 0.625rem`，Geist sans + Geist mono；`.dark` 类切暗色；`data-theme-preset` 切 brutalist/soft-pop/tangerine 三套额外 preset（脚本生成）
- **状态语义中枢**（`lib/status.ts`，128 行，注释引「Spec §8.3」）：**9 个域 × 8 个 tone** 的集中映射——intent/task/severity/finding/engine/goal/audit/node/delivery，每态中文名+色调；tone 用软底色（`bg-blue-500/15 text-blue-600`），唯独 **rose 用实心白字**（「严重」要明显高于「高危」的软红描边——原注释）。金句级注释：*blocked=模型/API 故障重试耗尽；exhausted=预算被掐断只写回部分；stopped=软删历史；deleted=用户假删除*——**状态命名先讲清语义边界再上色**
- **agent 泳道色**（`transcript.tsx`）：planner=amber-600、mainagent=primary、work#N 循环 sky/violet/teal/pink/orange-600，9px 白字芯片
- **live 徽标体系**：蓝底脉冲点 chip「实时」（`LiveBadge`）、三连弹跳点「实时流式中…」、spinner=running、灰时钟=pending、绿勾圈=done、琥珀斜杠圈=stopped、红叉圈=blocked、**紫 ZapOff=步数耗尽**、SSE 断连=`WifiOff` 琥珀「重连中」（侧栏常驻，注释：「断链可见，绝不静默装作没消息」）
- 数字一律 `tabular-nums`；时间 `ActivityTime` 只显 月-日 时:分，hover 全量；移动端 Token 指标用「入/缓/出」短标签防换行

### 1.6 交互模式（控制面核心）

**A. 主 Agent 会话（人的介入面）**
- ChatGPT 式懒建会话（首次发送才 createConversation）；左栏按 Agent 分组折叠（置顶块+最近活跃组在前，localStorage 记忆折叠态）、双击重命名、pin、多选批删（100/批，失败保留选择可重试）
- 运行中：发送键变红色停止键（只停本会话，触发器队列继续）；输入框 placeholder 变「Agent 正在回复，可输入 /btw 提问…」，/btw 命令时额外亮起旁路发送键
- **/btw 旁路提问**（`side-question-workspace`）：Drawer 侧栏独立问答，五段准备态文案（准备上下文/整理早期问答/压缩快照/上下文超限缩减重试/回答中），不污染主对话
- 附件：回形针上传到会话目录，chip 预览（名+大小+移除），随下条消息发；**失败恢复**——发送失败把文本和附件原样塞回输入框
- Enter/Ctrl+Enter 双键位（localStorage 偏好），**IME 组合态放行**（`isComposing || keyCode===229` 不当发送，中文选字不误发）

**B. Worker 会话（观察+定向介入）**
- 列表行：状态图标 + `#intentId` 码片 + 意图摘要标题 + 待审批⚠ + 未读 99+ + 实时徽标；继承意图标「来源 #N」
- **介入三件套**：running→暂停键；paused→「发消息给 Worker」（4000 字上限+幂等 requestId，服务端记用户回合并 SSE 流回，**无乐观插入**）或「直接继续」不发消息；/btw 运行中旁路
- **意图删除对话框**：假删除（置 deleted+记原因，保留产出，规划者收到通知重新规划）/ 真删除（物理级联**仅由它支撑的**下游，toast 报「含 N 意图/M 事实/K 漏洞」）二选一卡片式选择 + **必填删除原因**（placeholder 给示例：方向判断错误/目标已失效/重复）
- 意图标题取 payload JSON 的 summary；整节点 JSON 挂 hover tooltip（`<pre>` 10px）

**C. 审批拦截卡（三种形态同源）**
1. **内联卡**（`transcript.tsx InterceptCard`）：会话流内 amber 卡（`border-amber-400/50 bg-amber-50/40`），盾牌图标+工具名+#N+参数预览，**允许/拒绝两键**；从 summary 正则提取 pending_id 立即出按钮；挂载即查真实状态（刷新后已裁决的显示「已允许/已拒绝/已超时」chip 不再给按钮）；展开看完整详情；继承任务=「历史记录·只读」
2. **审批记录页**（`approval-records.tsx`）：pending 队列+历史表（响应式隐藏列，matchMedia 算 colSpan 防展开错位）；行展开 `ApprovalDetail`——左「工具请求 JSON+命令内容」右「裁决+理由+来源定位+申请/决定时间」，折叠区有**模型审查上下文快照**（当时实际发给审查模型的输入，带版本演进说明 v1/v2/v3）、会话审计片段、初判理由、**执行输出及关联状态**（ambiguous 并发不展示推测结果）、SHA-256 指纹组（参数摘要/审查配置/模型输入）
3. **深链定位**（`approval-execution-focus.tsx`）：记录卡「来源」链接 → `?approval=N` → 目标页反向往前翻页直到 seq 命中 `tool_use`，行内 `focusedSeq` 高亮（2px primary 边框）+居中滚动（ResizeObserver 防懒加载展开跑偏），顶栏「正在加载审批 #N 所在的对话位置…/已展开/无法定位+重试」

**D. 审批判定链**（`system/intercept/page.tsx`）：规则优先，**未命中规则且在拦截范围内的命令才给模型语义判断（放行/转人工/拦截）**；judge 用量单独计量（worker=judge）；模型异常回退路径可视化。

---

## ② 功能清单 + 成熟度评分

评分 1-5（5=生产级打磨完整）。判定：有/半/无。

| # | 功能 | 判定 | 分 | 证据要点 |
| --- | --- | --- | --- | --- |
| 1 | 认证（JWT/初始化/改密/账户切换） | 有 | 4 | login/init/change-password + sidebar 改密对话框、账户切换器 |
| 2 | 仪表盘 | 有 | 4 | 5 统计卡+Token 消耗面板（profile 分栏+每日条图+旧/新数据源切换）+最近活动/发现/流量/系统资源；三档轮询 |
| 3 | **对话（主 Agent 会话+@引用）** | 有 | **5** | 9 类实体 @ 引用（`@[漏洞#12 标签]` token 化）、附件、/btw、Todo 气泡、LLM 配置热切换、pin/重命名/多选批删、agent 分组折叠、URL `?c=` 恢复 |
| 4 | **任务中心** | 有 | **5** | 模板/分类管理/置顶/批量暂停恢复/归档冷存储（还原+依赖阻塞检查）/任务继承（source_task_ids）/删除选项；3417 行 |
| 5 | **任务详情·会话页签（workers 实时流）** | 有 | **5** | 四分组会话列表+单 SSE 多路分发+反向分页+未读+Worker 介入三件套+LLM 故障转移 toast+TokenMetrics；2205 行，工程注释密度极高 |
| 6 | 任务详情·总览 | 有 | 4 | 目标 CRUD/操作约束/范围（覆盖度分母+授权边界）/任务级拦截规则/Token 按模型分组 |
| 7 | 探索链路图 | 有 | 4 | 自算布局+React Flow、digest 超级节点、血缘边语义（spawns/derived_from/yields/proves） |
| 8 | 播报板 | 有 | 4 | 图事件时间轴流（直播位+翻页仅更新未读+300ms 防抖+hover 节点名片用已下发 refs 零额外请求）；8s 轮询 |
| 9 | 发现管理 | 有 | 5 | 分组/资产树/六维筛选/导出/九态状态机/流量证据绑定（版本化+排序）/血缘/深化（deepen）/复测 |
| 10 | 复测（retest） | 有 | 4 | 独立页签+active retest 跟踪+notes |
| 11 | 资产图/资产页 | 有 | 4 | 6 类资产、DSL 搜索、跨任务共享、任务资产挂载/继承 |
| 12 | 资产同步（ScopeSentry） | 有 | 3 | ssStatus/ssProjects/ssTasks/ssSync，独立页 |
| 13 | 流量 MITM | 半 | 3 | hosts 视图+exchange 详情+按 host/全量删除；**live 实例 enabled 但 count=0**（proxy 未接），UI 完整度存疑 |
| 14 | **审批拦截** | 有 | **5** | 规则+资产拦截+LLM judge+审计快照（模型输入版本化+SHA-256 指纹）+三形态卡+深链定位；38KB 组件 |
| 15 | 工具执行记录 | 有 | 4 | commands+commandStats，按任务/关键字过滤分页 |
| 16 | LLM 录制 | 有 | 4 | llm-records 明细/按模型/按任务、可删 |
| 17 | **LLM 池/故障转移** | 有 | **5** | 多配置链（dnd 排序+active+pool_exclude）、熔断状态（fails/trips/cooldown）、五层重试策略、模型拉取、`llm_switch/llm_failover` 事件 toast |
| 18 | Agent 管理 | 有 | 4 | prompt 版本化+预览、wrapup/超时收尾词、P3 触发器、MCP/Skill 可见性矩阵 |
| 19 | MCP / Skills / 自定义工具 | 有 | 4 | CRUD+刷新+zip 上传+调用测试+用量+missing-skills 提示 |
| 20 | 通知推送 | 有 | 4 | 多渠道+投递记录（pending/sending/sent/failed/skipped 五态）+重试+延迟测试 |
| 21 | 日志 | 有 | 3 | 列表+history+**SSE stream** |
| 22 | 工作空间 | 有 | 3 | 列表/读/写/mkdir/delete/上传/下载 |
| 23 | 报告 | 有 | 3 | markdown 导出（mock 有示例格式） |
| 24 | 系统配置+自更新 | 有 | 3 | settings 分组+update check/apply/rollback（页面一键更新） |
| 25 | 手机端适配 | 半 | 4 | 会话列表折叠、TokenMetrics 短标签、审批表响应式列；但整体为桌面工具密度 |
| 26 | 无障碍 | 半 | 4 | aria-label 密度极高（中文）、role=status/alert、sr-only 表头 |
| 27 | 国际化 | 无 | 1 | 全中文硬编码（对探隐反而不是问题） |

**总分印象**：这是一个**以「作业控制面」为核心打磨到 5 分、外围治理功能 3-4 分**的系统。最成熟的三块恰好是探隐 v0.9.5 最需要的：会话/介入、审批卡、workers 实时流。

---

## ③ 业务使用流（live 数据推断）

### 3.1 正在跑的作业（2026-10-15 15:00 抓取）

`GET /api/tasks` → 1 个任务：
- **#1「烛龙靶场渗透测试」**，目标「竟可能多识别漏洞」，描述=渗透 http://localhost:3081（admin/Whg1995!），status=running，已跑 ~80 分钟
- tokens：**input 5.5M（cache_read 5.2M，命中率 95%）/ output 96K**；in_flight=3，llm_in_flight=4
- findings：**1 严重 / 1 高 / 1 中 / 2 低**；goals 0/1
- `GET /api/stats`：engine=exploring，assets=44（40 endpoint+1 ip+1 root_domain+2 service），探索图 fact6/finding5/goal1/**intent10**
- LLM 池：单配置 GLM `glm-5.3`（openai 格式），state=ok；main-sessions：{current:0}（唯一主会话段）；审批队列空；traffic enabled 但 0 exchange

### 3.2 live 意图样本（`GET /api/exploration/intents?task=1`）

- **#72 running（优先级7）**「宿主机内部纵深侦察——基于已确认原语：finding#61 零认证命令执行 `/ping?host=` 注入、finding#64 /file 任意读，宿主 uid=501 wgen……lsof/ps/launchctl 找仅绑 127.0.0.1 的内部服务（含 fact#53 未解释的 6188/6189 波动端口）……提取 ~/.zsh_history、LaunchAgents、~/.ssh/config……全程只读、不留持久化、最小化命令输出」
- **#73 open（优先级6）**「同宿主机其余 Web 控制台的已知凭据/弱口令复用定向测试……对 :3000 Multica、**:8787 ARTEX 自身**、:8443、**:3080 dsh web**、**:8900 tanyin** 逐个 ≤5 次定向尝试已知模式化凭据（admin/Whg1995! 等——finding#39/#42 已证明该开发者口令高度模式化），绝不批量喷洒防锁定；任一命中 report_finding，全部否定写收口否定事实」

**推断**：这是一次对开发者本机（ZhuLong 靶场所在宿主）的真实内网纵深作业。planner 产出的意图是**带资产锚点、带已有 finding 引用、带操作纪律（≤5 次、不喷洒、只读）**的窄面任务；意图之间明确写「与 #65/#59 不同面」——即 planner 在做**攻击面去重编排**。且系统正在用自己测自己的生态（把 ARTEX/dsh/tanyin 端口列为目标）。

### 3.3 活动流形态（`GET /api/exploration/activity?task=1&limit=8`）

seq1 planner `round`「第 0 轮目标拆解」→ thinking → text「我先分析任务：」→ `tool_use add_task_scope`（登记 localhost 为最小范围+理由）→ `tool_use set_goals` → 两个 `tool_result` → `usage`（2017 入/1309 出）。**开局即自登记范围+自设目标**——范围/目标是 agent 用工具写的，不是人填的表单。

### 3.4 它在真实工作流中的角色

ARTEX = **自主渗透的驾驶舱 + 审计台**。人的介入点收敛为五个：
1. **开局**：填一句任务描述（可选模板/分类/LLM 链）→ 系统自跑闭环（planner 派意图→worker 领取执行→写回双图→再唤醒）
2. **导航**：给主 Agent 发消息（@引用漏洞/资产把对象递给它）引导方向；/btw 不打断地提问
3. **刹车**：审批卡允许/拒绝；暂停任务/暂停单个 worker；假/真删除意图并写原因（原因会回流给 planner 重新规划）
4. **治理**：目标/约束/范围/拦截规则（任务级+全局级）管理
5. **收尾**：看播报板/链路图复盘、导出报告、发起复测

 Token 经济是显性指标（每会话头挂 入/缓/出+轮次+时长，任务栏挂总计）——5.2M cache_read 说明其提示词复用率高，UI 把这个成本面直接暴露给操作者。

---

## ④ 对探隐的判决

### 判决：**仅参照**（置信度 85%）

**不是「直接复用」的理由（一票否决项）**：
- 探隐已定法**零依赖律/语言律**（webui 纯手写 HTML/CSS/SVG/vanilla JS，零框架零构建）；ARTEX 前端=Next.js 16 + React 19 + shadcn + Tailwind v4 + 2MB chunk。代码层复用=整体推翻探隐的底座自持律。
- ARTEX 是**可写控制面**（发消息/审批/暂停/删除），探隐已定法**投影律（UI 只读）**。角色定位不同：探隐控制动作走「任意 harness 平权遥控」第四层，webui 是观察面。

**不是「二开」的理由**：二开要求 fork 其前端骨架改皮，同样违反语言律；且其 60 件 ui 库与模板主题系统（7 个 cookie 偏好+3 preset）对探隐是负资产（维护面）。

**为什么仍高价值参照**：ARTEX 的**交互语义层**（状态学、信息架构、SSE 可靠性模型、审批审计形态）是探隐 v0.9d 可以「抄设计不抄代码」的现成答案——这些与框架无关，探隐用 vanilla JS 可以 1:1 重写（其业务组件与后端耦合仅 REST+SSE 纯 HTTP，无框架魔法；探隐的 13 本 TSV 账+哈希链对 activity seq 去重模型天然兼容）。

**翻案条件**（出现任一即改判）：
1. **改判「二开」**：探隐放宽语言律允许构建链（或走「预编译 Web Components 零运行时依赖」被裁定合律），且控制面决定做成独立服务——此时其 `transcript/approval-records/sessions-tab` 可直接改造复用（业务组件只依赖 `lib/api.ts`，接口层可换）。
2. **改判「直接复用」**：探隐把 ARTEX 整个接纳为「第三层战士」之上的独立控制面产品（即不再自建控制面 UI，ARTEX 当商用驾驶舱）——仅当探隐内核能通过其 REST+SSE 全量驱动（需验证其 API 是否可对接外部内核，当前看 API 与内核同体，难度大）。
3. **降价值**：若后续发现探隐九门流程的干预语义与 ARTEX 意图生命周期存在根本不匹配（如探隐无「意图」对应物），则第⑤节中依赖意图模型的条目（#3/#4/#8）降级为思想借鉴。

---

## ⑤ 可直接偷的 10 条（文件级出处 → 探隐落点）

> 「偷」= 抄交互语义与视觉规格，用 vanilla JS 重写。每条给 ARTEX 源码坐标。

**1. 集中式状态语义表（9 域×8 tone）**
出处：`web/src/lib/status.ts`（全量 128 行，含每态中文标签+tone+dot 色；rose 实心=严重>高危软红的层级设计；blocked/exhausted/stopped/deleted 四态的语义边界注释）。
落点：**探隐 webui 全局**——建 `status.js` 单例（域：门/账本/作业/判据/审批），所有徽标/圆点/筛选项从这里取，杜绝页面各自配色。探隐九门流程的每门状态直接映射成一个域。

**2. 单 SSE 多会话分发 + seq 去重 + snapshot 衔接的可靠性模型**
出处：`function/tasks/detail/_tabs/sessions-tab.tsx` 顶部「Reliability model」注释块 + `mergeBySeq`/`sessionKeyOf`/`snapshotRef`/`reqTokenRef`/`MAX_KEEP` 实现；`lib/activity-merge.ts`（10 行精髓）；配套 `docs/task-session-history-sse-remediation.md`。
落点：**探隐观察面 workers 实时流页**。探隐 13 本 TSV 账的行号/哈希链天然就是 seq——「history 从账本读快照+SSE 只推增量、按序号去重合并」可以原样移植；断线重连用「从账本重放」替代其 Last-Event-ID。

**3. 会话左栏四分组 + 8 态图标 + 未读/实时双徽标**
出处：`sessions-tab.tsx` `statusIcon()`（running 转圈/pending 灰时钟/done 绿勾圈/stopped 琥珀斜杠/blocked 红叉/exhausted 紫 ZapOff/deleted）、`roleMeta`（主 Agent/规划 Planner/Workers/系统审计四组）、`SessionItem`（#id 码片+摘要+待审批⚠+未读 99++实时脉冲）、SSE 断连常驻「实时/重连中」指示。
落点：**探隐控制面(v0.9.5) 会话列表**——四分组改成探隐的「主 harness 会话/九门调度/战士池/系统审计」，图标语义表照抄。

**4. Worker 介入三件套（暂停→留言→直接继续）+ /btw 旁路**
出处：`sessions-tab.tsx` `sendWorkerChat()`（4000 字上限+requestId 幂等+「服务端记录用户回合并 SSE 流回，无乐观插入」注释）、底部 InputGroup 三按钮态、`side-question-workspace.tsx`（五段准备态文案）+`lib/chat-send-mode.ts`（IME isComposing 放行）。
落点：**探隐控制面战士干预**——探隐经 harness 遥控 opencode 时，「留言」对应注入用户消息、「直接继续」对应 resume；/btw 对应探隐的旁路判据询问（不动主上下文）。

**5. 审批卡三形态 + 深链定位**
出处：`transcript.tsx InterceptCard`（amber 内联卡：盾牌+工具名+#id+参数预览+允许/拒绝、挂载即查真实状态防重复裁决、继承=只读）、`approval-records.tsx ApprovalDetail`（模型审查输入快照+SHA-256 指纹组+执行输出关联+ambiguous 不展示推测）、`approval-execution-focus.tsx`（?approval=N 反向翻页定位+focusedSeq 高亮居中）。
落点：**探隐 v0.9d 审批拦截卡**——探隐判据层的「待批动作」直接用内联卡规格；「来源定位」用账本行号反查活动流并高亮，探隐的哈希链正好放指纹位。

**6. transcript 分组渲染器（tool_use/tool_result 按-id 配对 + 懒加载）**
出处：`components/transcript.tsx` `groupSteps()`（user/intent 右气泡、result 全文 markdown、tool 按 `tool_use_id` 配对成单行「命令+✓/✕」、连续同 worker 文本合并成 msg、round 水平分隔线）、`useInView`（IntersectionObserver 400px 预取）、`ToolBlock`（折叠=命令+状态、展开=【命令】【输出 ✓】两段）。
落点：**探隐观察面活动流渲染**（所有流式页共用一个渲染器）——探隐账本里的工具调用行按 call-id 配对，折叠行只显命令首行+状态色。

**7. Token 记账 UI（入/缓/出三 badge + 轮次 + 双数据源）**
出处：`sessions-tab.tsx` `TokenMetrics`（短标签「入/缓/出」移动端自适应）、tokenForSession（服务端持久化总数+客户端只加最后未完 usage 帧，防部分历史少算）、chat/page.tsx `tokenTotal`（轮次=usage 行计数）；`dashboard/page.tsx` 旧版/新版数据源切换（activity 统计 vs 计量账本，tooltip 讲清两者口径差异）。
落点：**探隐 13 本 TSV 账的可视化头**——每本账详情页顶部挂同款三 badge+笔数；「双数据源切换」对应探隐「账本快照 vs 哈希链校验值」双口径。

**8. 意图删除双模式对话框（假删除/真删除+必填原因）**
出处：`sessions-tab.tsx` 底部 AlertDialog（两张模式卡片各带一句后果说明；原因必填+示例 placeholder；真删除 toast 报级联统计「含 N 意图/M 事实/K 漏洞」；假删除保留产出、原因回流规划者）。
落点：**探隐九门流程的干预操作**——对应探隐「作废某门某步」：假删=标记 tombstone 保留哈希链完整，真删=级联清理独占下游并在 toast 报清理量；原因写入账本。

**9. LLM 配置链 + 故障转移事件推送**
出处：`function/tasks/detail/page.tsx` `TaskLLMControl`（链按钮显示当前配置+备用数、耗尽=destructive 红+「配置链已耗尽」Alert、终态任务也可换链的注释）、`system/llm/page.tsx` + `llmpool` API（fails/trips/cooldown 熔断可视化、一键清熔断）、sessions-tab SSE 分支（`llm_switch/llm_failover` → 按 transition.mode 分级 toast error/success/info + 立即刷新 resolution）。
落点：**探隐判据层直连 API 的池化 UI**——多 API key/多模型链的探隐版：每链显示 active/备用/熔断态，切换事件经 SSE 推 toast。

**10. 播报板的直播位+未读基线+零额外请求名片**
出处：`function/tasks/detail/_tabs/broadcast-tab.tsx`（POLL_MS=8000 只有最新在第 1 页才真刷列表、其它位置只更新未读计数「免得翻页/展开时内容在脚下变」；输入 300ms 防抖；hover 上下游名片用本页已下发的 refs 不发请求；30s 时钟 tick）。
落点：**探隐事件流/账本流水页**——探隐轮询账本时同款「只直播第一页+未读计数」策略，配合已有的哈希链做增量校验。

**附赠（第 11-13 条，超出 10 条但值得记）**：
- 11. `chat-mentions.ts` 的 @ 引用 token 格式 `@[类型#id 标签]` + caret 检测正则——落点：探隐控制面输入框引用账本对象（漏洞/资产/门）。
- 12. 仪表盘三档轮询分层+JSON 签名比对才 setState——落点：探隐 dashboard 的轮询预算分配。
- 13. `approval-records.tsx` 响应式表格（matchMedia 算可见列数同步 colSpan）——落点：探隐账本表格在窄屏的退化策略。

---

## 附：证据索引

- live 抓包：`/api/auth/login`(200+JWT)、`/api/tasks`、`/api/stats`、`/api/health`、`/api/conversations`、`/api/traffic`、`/api/exploration/intents?task=1`、`/api/exploration/activity?task=1&limit=8`、`/api/exploration/findings?task=1`、`/api/exploration/main-sessions?task=1`、`/api/intercept/pending`、`/api/llm/pool`（全部 GET，2026-10-15 14:0x–15:0x）
- 源码：`ARTEX/web/src/`（app 路由树、components、lib）、`ARTEX/server/server.go`（130+ 路由注册）、`ARTEX/README.md`（架构章节 L294-460）、`ARTEX/screenshots/`（14 张 PNG，本分析模型无图像输入能力，仅记录存在：dashboard/chat/tasks/sessions/intercept/graph/traffic/findings/agents/llm/logs/assets/wx/assets_test）
- 前端 chunk 抓取存档：`/tmp/artex-js/`（26 个文件，分析用，可删）

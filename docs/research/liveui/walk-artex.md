# ARTEX 界面漫游实录（walk-artex）

**目标系统**: ARTEX http://localhost:8787 （自主渗透测试控制台，Go 单体 + Next.js 静态导出内嵌）
**漫游方式**: Playwright (Chrome headless, 1440×900)。铁律执行：**只导航不操作**——全程仅①登录 POST ②路由跳转 ③任务详情页签切换（role=tab，纯视图切换）；未点击任何 新建/发送/暂停/审批/删除/保存 类按钮。分析基于 inner_text / DOM / getComputedStyle 实测；截图仅供人工复核。
**前置输入**: 源码级报告 2-artex.md（token 持久化 = localStorage `artex_token` + 同名 cookie 7 天，实证于 `web/src/lib/auth.ts`；21 项 IA 路由清单实证于 `navigation/sidebar/sidebar-items.ts`）。
**漫游时间**: 2026-10-15 16:2x（任务 #1 已运行 2h40m，实时进行中）
**截图目录**: `docs/research/liveui/shots/`（32 张 full_page PNG，本表内为相对该目录的文件名）

---

## 0. live 快照事实（漫游时点）

| 项 | 实测值 |
| --- | --- |
| 任务 | #1「烛龙靶场渗透测试」运行中（探索中），运行 2h40m，3 worker 在途 |
| 发现 | **39 个已确认**（严重 7 / 高危 17 / 中危 10 / 低危 5），待处理 39 |
| 资产 | 节点 105（app1 / endpoint52 / ip8 / root_domain2 / subdomain2 / service40） |
| Token | 总 73.3M = 入 72.2M（含缓存 68.3M）+ 出 1.1M；**缓存命中率 95%**；glm-5.3 共 1647 次调用 |
| 覆盖度 | 23%（已测 23 / 范围内 99；分资产类型: app 0/1, endpoint 6/52, ip 4/4, service 13/40, subdomain 0/2） |
| 审批 | 全部记录 19 条（含 pending 队列；#19/#18/#17 均为命中「[内置] curl/wget DELETE」规则被拒） |
| 流量 | 录制代理「已停用」，仍存 6 条历史 exchange（含经代理的 example.com / 8787 api/health 自测流量） |
| 对话页 | 会话列表为空（本实例未建过主 Agent 对话；Auto 为默认对话 Agent） |
| 拦截规则 | 内置 20 条按优先级 100/90/80 分层（rm -rf / mkfs / DROP DATABASE / FLUSHALL / HTTP DELETE / 数据外泄管道…），拦截范围 8 工具：Bash、WebFetch、web_search、shell_open、shell_send、Write、Edit、MultiEdit |
| Agent | 共 8 个：内置 7（goals/planner/mainagent/worker/auto/pentest）+ 自定义 2 中内置标注（reporter 报告撰写 / retester 漏洞复测） |
| 版本 | dev（linux/amd64 Docker）；更新面板报「仓库尚未发布正式版本」 |

> 对比 2-artex.md 下午 15:00 抓取（5 发现/105→44 资产）：2 小时内发现数 5→39，验证「worker 写回→planner 再派」闭环的真实推进速度。

---

## 1. 视图清单总表

编号对应截图 `artex-NN-*.png`。「可交互元素」列出实测可见按钮/输入（**均未点击**，仅枚举）。

| # | 路由 | 截图 | 页面呈现什么 | 可交互元素（实测） | 视觉手法 |
| --- | --- | --- | --- | --- | --- |
| 01 | `/login` | artex-01-login.png | 未认证登录页：左 1/3 近黑品牌区（同心圆环+反白 logo），右表单区「登录」标题+只读用户名 ARTEX+密码框 | 密码输入、《使用须知》链接（弹滚动到底才能同意的条款）、登录按钮 | 双栏分割构图；品牌区三重同心圆暗示「环/控制面」；表单极简 |
| 02 | `/dashboard` | artex-02-dashboard.png | 总览：6 统计卡（活跃任务 1/1·探索 1、确认发现 38、资产节点 105、流量交互 6·捕获未开启、Token 73.3M）+ LLM Token 消耗面板（旧版/新版双数据源切换、7天~一年粒度、缓存命中率 95%）+ 活动流 25 条（tool_use/tool_result/text/thinking 分类计数）+ 发现摘要卡 + 任务表（任务/状态/引擎/目标进度/在途/最近活动） | 旧版/新版切换、GLM 筛选、时间粒度 7天/30天/3月/6月/一年、查看任务、主题切换、Command Palette(⌘J) | 统计卡数字大号 tabular-nums；消耗面板用双色堆叠条形图；活动流左侧类型徽标分组 |
| 03 | `/chat` | artex-03-chat.png | 主 Agent 对话（空态）：左会话栏「暂无对话」，右侧默认与「Auto」对话的欢迎位（平台操作助手说明） | 新建对话、全部 Agent 筛选、Auto 头像+「更换」、（输入框: 上传文件/发送消息） | 空态给了「和谁说话」的人格卡而非裸空白；Agent 名+简介+默认徽标 |
| 05 | `/function/tasks` | artex-05-tasks.png | 任务中心：当前任务/已归档双页签+状态/分类筛选；1 行任务卡：#1 名称、描述、目标「竟可能多识别漏洞」、运行中、0/1 目标、漏洞 7/17/9/5、运行中 Worker 3、13:41 创建、2h40m、Token 入72M·缓68M·出1.1M | 并发设置、分类管理、新建任务、选择本页全部、行内: 重命名/暂停/置顶/归档/删除、20条/页 | 表格列头小字号+行内操作图标钮；Token 三段式「入/缓/出」短标签；状态徽标软底色 |
| 06 | `/function/tasks/detail?id=1` 会话页签 | artex-06-task-detail-sessions.png | **workers 实时流**（默认页签）：sticky 头（任务名+#1 码片+GLM 配置链+「探索中」+暂停钮+目标一句）→ 左会话列表四分组：主 Agent·会话#1（新建钮）/ 规划 Planner·态势研判 1·实时 / 系统审计·LLM 故障转移 / Workers（#147、#141、#137、#136…各带 #意图码片+长摘要+实时徽标）→ 右记录流。顶部 TokenMetrics「任务总计·入 72M·缓 68M·出 1.1M」+「实时」蓝脉冲 | 会话列表新建、各会话项（查看）、暂停（未点）、输入框「给主 Agent 发消息，@ 引用漏洞、资产等…」、上传文件、页签×10 | **agent 泳道色**: planner=amber、worker 循环 sky/violet/teal/pink/orange；「实时」蓝底脉冲点 chip；意图摘要直接展示 planner 的作战计划全文（信息密度极高）；animNames=pulse+spin |
| 07 | 同上 总览页签 | artex-07-task-detail-overview.png | 任务描述/目标（1 条进行中）+ 目标管理（增删改会通知规划者并复活任务）+ 操作约束（禁/允 0 条）+ 任务级资产拦截/允许（域名/IP/URL 全等+模糊+CIDR 七种匹配）+ **资产测试覆盖度 23%**（按类型分/app0/1…）+ LLM Token 用量按模型表（glm-5.3 1647 次）+ 测试范围 8 条（Agent/自动/心跳三种来源标注）+ 心跳（引擎态/运行中 Worker 3/最近活动）+ 进行中意图 JSON 卡 | 添加×4（目标/约束/拦截/范围）、LLM 配置链 GLM、暂停 | 覆盖度用横向进度+类型分解；「新增/修改会通知规划者并复活任务」的微文案解释副作用；范围行带来源徽标 |
| 08 | 同上 探索链路页签 | artex-08-task-detail-graph.png | 探索图（React Flow 画布）：goal/intent/fact/finding 血缘节点+边语义 spawns/derived_from/yields/proves，digest 超级节点合并 | Zoom In/Out、Fit View、节点拖拽/点击 | 画布型可视化（DOM 文本仅 35K 说明主体在 canvas/SVG 层）；全页 35,344 字符的节点数据 |
| 09 | 同上 播报板页签 | artex-09-task-detail-broadcast.png | 图事件时间轴直播流：类型筛选（目标/意图/事实/漏洞/提示/压缩）+ 最新在前 + 自动刷新开关；事件卡带 #id+状态 chip+作者（work#3/planner）+优先级 P6/P7+相对时间（刚刚/1 分钟前），正文为完整摘要 | 六类筛选钮、压缩、最新在前、自动刷新 | 时间轴左时刻右卡；「刚刚」相对时间+日期分隔线；最新事件置顶直播位 |
| 10 | 同上 发现页签 | artex-10-task-detail-findings.png | 任务内漏洞列表：严重度徽标+超长技术正文（攻击链完整描述: 凭据复用→admin 令牌→terminal:execute 宿主机 RCE 的 PoC 全文） | 严重度筛选、行选择、复测/深入/删除（未点） | 严重度左侧色条；正文不截断（full_page 截图 804KB 即证据）；finding 间引用（#104/#123）超链化 |
| 11 | 同上 复测页签 | artex-11-task-detail-retests.png | 漏洞复测看板：4 张待复测卡（中危 CyberStrikeAI LLM 凭据消费 / 高危 Multica JWT_SECRET 会话伪造 / 中危 ARTEX 8788 MITM 代理未认证 / …）各带严重度+待处理状态 | 每卡发起复测入口（未点） | 卡片式两列布局；状态徽标「待处理」软底 |
| 12 | 同上 测试资产页签 | artex-12-task-detail-assets.png | 任务资产挂载：六类计数（根域名 2/IP 8/子域名 2/应用 1/服务 40/接口 52）+ 资产行（可移出任务） | 新增测试资产、移出、50/页 | 类型 tab 式计数徽标；资产值等宽字体 |
| 13 | 同上 资产覆盖图页签 | artex-13-task-detail-coverage.png | 力导向覆盖图（G6 画布）：范围内资产+已测高亮 | 刷新 | 画布主体（DOM 文本仅 290 字符=全在 canvas）；与 08 的差异：这张画「资产」，08 画「推进链」 |
| 14 | 同上 拦截审批页签 | artex-14-task-detail-intercept.png | 任务级审批：pending 队列+全部记录 19 条表（#/工具/来源 work#N·#意图/匹配规则/参数 JSON/状态/申请·决定时间）；#19 实测=Bash 命中「[内置] curl/wget DELETE」→已拒绝，参数列展示完整 bash 命令 | 刷新、状态/来源筛选、展开审批 #N（详情快照，未点） | amber pending 计数 pill（页签名上）；参数 JSON 等宽小字；状态 chip（已允许/已拒绝/已超时） |
| 15 | 同上 报告页签 | artex-15-task-detail-report.png | 渗透测试报告（Markdown 全文渲染）：摘要（确认 39/资产分布）→ 逐条 [CRITICAL/HIGH…] 漏洞正文（PoC/攻击链/修复建议），56,604 字符 | 复制 | 报告即产品：doc 型排版、层级标题+代码块；「复制」一键取走 |
| 16 | `/function/findings` | artex-16-findings.png | 跨任务发现管理：三视图（全部发现/按任务分组/按资产）+ 严重度/状态/类型/任务四维筛选 + 统计头（39·待处理 39·严重 7·高危 17·中危 10·低危 5）+ 表格（严重度/漏洞名称/资产/状态/所属任务/时间/操作） | 全部/严重/高危/中危/低危、全部状态/类型/任务、按严重度排序、导出、选择当前页全部、行: 复测/深入/删除 | 左侧色条+软底严重度 chip；「深入(deepen)」为差异化功能钮；导出在工具位 |
| 17 | `/function/traffic` | artex-17-traffic.png | 流量 MITM：录制代理状态 chip「已停用」+共 6 条；目标筛选/删除该目标/清空全部；高级筛选（方法/状态码/响应长度区间）；表：时间/host/方法/URL/状态码/content-type/响应长度；底部已选 0 条+「关联到漏洞」 | 选择目标、全部方法、状态码、响应长度区间、选择流量、关联到漏洞、删除/清空（未点） | 状态码彩色徽标；URL 等宽；批量「关联到漏洞」把流量绑定为漏洞证据 |
| 18 | `/function/commands` | artex-18-commands.png | 工具执行记录：命令流水表（任务/命令/状态/时长）+统计入口 | 50/页、统计 | 审计型表格；4,609 字符=约 10 行记录 |
| 19 | `/function/llm-records` | artex-19-llm-records.png | LLM 调用录制：按任务筛选的模型调用明细（空态+筛选器） | 选择任务、删除任务对话、50/页 | 空态简洁；本实例未开启录制 |
| 20 | `/function/assets` | artex-20-assets.png | 全局资产图入口：六类计数卡（企业 0/根域名 2/IP 8/子域名 2/应用 1/服务 40/接口 52）+DSL 搜索 | 刷新、新增企业 | 计数卡阵；「企业」为资产归属根 |
| 21 | `/function/sync` | artex-21-sync.png | 资产同步（ScopeSentry）：数据源状态「未配置」+ MCP 地址/API Key 表单 +「保存并启用」 | 刷新、保存并启用（未点） | 状态 chip（未配置/已连接）；说明文案直接给接入步骤 |
| 22 | `/function/workspace` | artex-22-workspace.png | 工作空间文件管理：目录树 .tools/tasks/traffic/transcripts + 文件操作 | 新建文件夹、上传、刷新、删除（未点） | 双栏文件管理器；任务产物目录化（tasks/1/i137 之类在审批参数里可见） |
| 23 | `/system/llm` | artex-23-system-llm.png | LLM 池：轮询配置+模型配置列表（GLM 一个 profile：设为激活/删除）+重试与退避 | 轮询配置、新建、设为激活、删除配置、重试与退避（未点） | 「激活」实心主色钮区分在用配置；熔断态（fails/trips/cooldown）来自源码 |
| 24 | `/system/agents` | artex-24-system-agents.png | Agent 管理：8 个 Agent 卡（目标拆解 goals/规划 planner/主 mainagent/执行 worker/Auto auto/渗透测试 pentest=内置；报告撰写 reporter/漏洞复测 retester=自定义），各带 MCP/Skill/工具 计数徽标+职责一句话 | 新建 Agent、卡点击进编辑器 | 内置/自定义标签区分；工具数徽标（planner 20 个/worker 12 个/auto 26 个）直白展示能力面 |
| 25 | `/system/mcp` | artex-25-system-mcp.png | MCP 服务器管理：已配置 2 个（启用/删除） | 添加 MCP、启用、删除（未点） | 列表+开关；http/sse 两种传输来自设置说明 |
| 26 | `/system/skills` | artex-26-system-skills.png | Skill 技能库：总览+3 个 skill（api-recon/playwright-cli/scopesentry）+文件级编辑（新建文件/文件夹/删除） | 新建 Skill、上传压缩包、文件树操作（未点） | skill=可上传 zip 的能力包；worker/pentest 各挂 1 个 |
| 27 | `/system/tools` | artex-27-system-tools.png | 工具注册表：系统工具/自定义工具两大区，每工具=名称+类型+调用次数+完整 schema 描述（如 add_company_scope 的护栏：拒绝裸 TLD 与过宽网段） | 系统工具/自定义工具切换、（自定义工具的）调用测试（未点） | 工具文档即列表：参数 schema+护栏说明全文展示；10,872 字符 |
| 28 | `/system/notify` | artex-28-system-notify.png | 通知推送：推送总开关+渠道/投递记录双页签+添加渠道 | 推送总开关、保存全局设置、添加渠道（未点） | 开关型治理页；五态投递记录（pending/sending/sent/failed/skipped）来自源码 |
| 29 | `/system/intercept` | artex-29-system-intercept.png | 命令拦截规则：拦截范围（8 工具多选）+规则表（优先级/名称/目标/类型/模式/策略/启用）——内置 20 条正则按 100/90/80 分层+模型配置页签（LLM judge） | 调整范围、新建规则、启用开关（未点）、模型配置页签 | 正则全文等宽展示；「优先级越大越先、首条命中生效」规则直白；三页签=范围/规则/判定模型 |
| 30 | `/system/intercept/assets` | artex-30-system-asset-intercept.png | 资产拦截：资产级黑/白名单规则（空态+新建） | 新建规则（未点） | 与 29 分工：29 管「命令」，30 管「资产」 |
| 31 | `/system/intercept/approvals` | artex-31-system-approvals.png | 审批记录（全局）：与 14 同源组件——pending 队列+历史表+展开详情（工具请求 JSON/裁决/模型审查上下文快照/SHA-256 指纹组） | 刷新、状态/来源筛选、展开审批 #2~#19（未点） | 治理视角入口（14 是作业视角）；「展开详情」承诺审计快照 |
| 32 | `/system/logs` | artex-32-system-logs.png | 系统日志：级别筛选（全部/info/warn/error）+暂停滚动+清空+SSE 实时流 | 全部/info/warn/error、暂停、清空（未点） | 终端式日志面；「暂停」供复制定位 |
| 33 | `/system/settings` | artex-33-system-settings.png | 系统配置：版本与更新（dev/无法连 GitHub）+流量捕获（已关闭·说明注入 traffic_search/traffic_get 工具的机制）+Agent 自动绑定流量+全局代理（http/https/socks5）+操作约束注入（planner/worker 各自开关）+实验功能（noa 上下文压缩）+网络搜索总开关（DuckDuckGo/Brave/Tavily/DeepSeek 四源）+Python 解释器路径+**工作并发 Work Agent 数（默认 3）**+会话输入框发送键位（Enter/Shift+Enter） | 检查更新/立即更新、各卡保存、重新检测、开关若干（未点） | 治理设置卡片化，每卡=开关+机制说明文案（把副作用讲清楚再让你开）；「该偏好只存在本浏览器」隐私级微文案 |

**注**: 编号 04（chat-conversation 既有会话视图）因 live 实例 0 会话未捕获——`GET /api/conversations` 返回空数组，空态即 03。@引用能力以会话页输入框 placeholder「给主 Agent 发消息，@ 引用漏洞、资产等…」+源码 mention-textarea（9 类实体）双重佐证。

---

## 2. 全局视觉系统实测（getComputedStyle）

| 维度 | 实测值 | 备注 |
| --- | --- | --- |
| 主题 | 浅色（bodyBg=白 lab(100 0 0)，bodyColor 近黑 lab(2.75 0 0)）；顶栏有「Current theme: light. Click to cycle themes」循环切换钮 | 源码另有 .dark 类 + brutalist/soft-pop/tangerine 三 preset（cookie `theme_mode/theme_preset`），本次实测默认 |
| 主色 | `--primary` = lab(7.78% 0 0) ≈ 近黑（zinc 系中性色） | 「控制台中性底+状态语义色」策略：主色不抢戏，状态色承担信息 |
| 字体 | Geist（sans）+ Geist Mono（码片/命令/JSON）；body 16px | 数字一律 tabular-nums（源码） |
| 圆角 | `--radius` = .625rem（10px） | 中性偏小，工具感 |
| 动效 | 会话页 animNames = **pulse + spin**（实时徽标脉冲+运行 spinner） | 动效只用于「活着」的语义：live 徽标/运行态/重连，装饰性动画为零 |
| 状态徽标 | 软底色 chip（bg-*-500/15 text-*-600），唯独严重=实心 rose 白字（源码注释：严重>高危的层级） | 实测 10/14/16 页的严重度徽标均符合 |
| 泳道色 | planner=amber-600、mainagent=primary、work#N 循环 sky/violet/teal/pink/orange（源码 transcript.tsx） | 实测 06 页 Workers 分组各行可辨 |

---

## 3. 重点视图深描（漫游时点实况）

### 3.1 会话页签 = workers 实时流（06）
四分组信息架构：**主 Agent**（人的介入面，输入框 placeholder 即 @ 引用提示）→ **规划 Planner**（态势研判 1 条·实时——planner 的思考/工具调用流）→ **系统审计**（LLM 故障转移事件组）→ **Workers**（每意图一行：#147/#141/#137/#136…，#码片+优先级+完整作战计划摘要+实时徽标）。摘要文本展示 planner 派单的完整纪律（「红线：绝不触发 POST /api/system/update/apply…全程只读」直接可见）——**审批红线在派单时就写进意图**，人无需逐条盯。

### 3.2 审批卡（14/31，同源两入口）
19 条记录全部带：命中规则名（如「[内置] curl / wget 发送 DELETE 请求」）+ 规则说明 + **参数原文 JSON**（完整 bash 命令）+ 状态 + 申请/决定时间（同秒=自动裁决）。任务级页签（14）与全局审批记录（31）渲染同一组件——「作业视角/治理视角」双入口，与 2-artex.md 的 IA 洞察一致。

### 3.3 任务中心（05）
单卡密度极高但列语义分明：目标进度 0/1、漏洞 7/17/9/5 四联、运行中 Worker 3、Token 三段式。行内操作全图标钮（重命名/暂停/置顶/归档/删除）+ 顶部批量位（并发设置/分类管理/新建任务）。

### 3.4 发现管理（16）与报告（15）
发现页三视图+四维筛选+「深入/复测」差异化操作；报告页签直接把 39 漏洞渲染成完整 Markdown 报告（56K 字符），「复制」即交付——**报告是系统的一等公民，不是导出附件**。

### 3.5 LLM 池（23）
极简列表（本实例单 profile GLM）+ 轮询配置 + 重试与退避页签。故障转移的完整可视化（fails/trips/cooldown 熔断态、链耗尽红 Alert、llm_switch/failover toast）本次因单配置+链健康未触发表象，机制证据在源码与会话页「系统事件·LLM 故障转移」分组。

---

## 4. 探隐 v0.9d 落点建议

> 承接 2-artex.md 第⑤节「可偷的 10 条」，本节基于**漫游实证**给出 v0.9d UI 升级批的落点优先级（P0 先行）。

**P0-1 状态语义中枢照抄规格**（对应偷#1）。实测确认其视觉规格稳定可复制：9 域×8 tone、软底 chip、唯独严重实心 rose。探隐 webui 建 `status.js`：域=门/账本/作业/判据/审批，每态一个 {label, tone, dot}，全站徽标/筛选/圆点唯一来源。**落点文件**: `webui/status.js` + 渲染层统一 `badge()` 工具函数。

**P0-2 活动流渲染器（偷#6）+ 实时双徽标（偷#3）**。漫游最震撼点：Workers 分组每行「#意图码片+摘要+实时蓝脉冲」。探隐 13 本 TSV 账的行号即 seq——先做**单渲染器**：折叠行=命令首行+状态色、展开=命令/输出两段；列表行=#行码片+摘要+未读+实时。实时判定用同款「5s 内有活动才亮」+1.5s tick 衰减。

**P0-3 Token 三段式记账头（偷#7）**。实测 05/06/07 三处都是「入/缓/出」三 badge。探隐每本账详情头挂同款：入(未命中)/缓存命中/出+笔数，命中率单列——探隐的 prompt 复用率因此成为显性指标。

**P1-4 审批内联卡（偷#5）**。实测裁决记录把「规则名+说明+参数原文」三件套全展示且自动裁决同秒完成。探隐 v0.9d 判据层待批动作直接用 amber 卡规格：盾牌+动作名+#行+参数预览+允许/拒绝；刷新后已裁决显示状态 chip 不再出按钮（防重复裁决语义照抄）。

**P1-5 覆盖度分解展示**（07 页实测 23%·分类型 app0/1 endpoint6/52 ip4/4…）。探隐「账本覆盖率/门进度」用同款：总分母进度条+按类型分解行。**探隐哈希链校验值**可在此并列展示（双口径: 账本快照 vs 链校验）。

**P1-6 治理页的「机制说明文案」模式**（33 页实测）。每个开关都把副作用写清（「开启后…切换即时生效…对下一轮生效」）。探隐设置项（如遥控开关、判据严格度）逐项配同款一句话副作用说明——这是零成本可抄的信任设计。

**P2-7 播报板直播位（偷#10）**：事件流页「最新在前+自动刷新开关+相对时间」三件套。
**P2-8 空态人格卡**（03 页实测）：对话空态给「和谁说话」的 Agent 卡（名+职责+默认徽标）而非裸空白。探隐控制面主会话空态可给「主 harness」卡。
**P2-9 报告一等公民**（15 页实测）：Markdown 全文渲染+复制。探隐九门结案报告同款内联渲染，不弹下载。

**反模式警示（不抄）**：①2MB JS 的框架底座（违反探隐零依赖律）；②任务行内操作全图标钮无文字——探隐工具密度低，文字钮更可及；③画布双图（React Flow+G6 两套）——探隐观察面若需图，单 SVG 手算布局即可。

---

## 附: 铁律合规记录

- 全程唯一写操作: `POST /api/auth/login`（任务书明示允许）。
- 页签切换 9 次（role=tab，React 本地状态，无后端写）。
- 未点击: 新建/发送/暂停/审批(允许/拒绝)/删除/保存/启用/上传/关联/导出 类按钮任何之一。
- 未在输入框输入任何内容。
- DOM 里的`GET /api/conversations`（页面自身加载即发起的同款只读请求）用于确认空态。
- 截图 32 张全部 full_page，仅存 `docs/research/liveui/shots/`；零 git 操作。

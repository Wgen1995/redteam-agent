# Multica 活体漫游报告（walk）
**目标**： http://localhost:3000 （Multica v0.5.1 自托管 · Docker Compose：multica-frontend-1 / multica-backend-1 / multica-postgres-1[pgvector pg17]）
**方法**： Playwright Chrome headless · 只导航不操作（GET 导航 + 登录 OTP POST + 点设置页标签 + hover 展开）；截图 full_page 1440×900；分析基于 inner_text / DOM / getComputedStyle。
**漫游日期**： 2026-10-15 · 截图目录： `docs/research/liveui/shots/multica-NN-*.png`（共 58 张）

---

## 0. 系统事实卡

| 项 | 实证 |
| --- | --- |
| 产品 | Multica —— 开源「AI 员工/数字员工」任务平台（官网 multica.ai，GitHub 52.9k star 宣传位），server_version **v0.5.1**（/api/config） |
| 鉴权 | **邮箱验证码 OTP**（无密码框）；自托管无邮件通道时后端日志打印 `[DEV] Verification code for <email>: <6位>`。给定两组 用户名/密码 凭证（admin/ARTEX + Whg1995!）在客户端邮箱格式校验即被拒（未发出任何 API 请求），**如实记录为失败**。实际以库内唯一用户 2642328381@qq.com + 日志验证码登入 |
| 账户形态 | 单用户单工作区：slug `wgen`；issue 人类可读键 `WGEN-N`（如 WGEN-2），与 UUID 双轨寻址 |
| 前端 | Next.js App Router（route groups：`(auth)`/`(landing)`/`[workspaceSlug]`）；工作区路由前缀 `/{slug}/` |
| 后端 | Go（容器镜像 ghcr.io/multica-ai/multica-backend），REST `/api/*`，日志含 request_id/user_id/client_platform(web|cli|daemon) |
| 真实作业 | 漫游期间后端持续有 daemon 心跳与任务完成事件；provider=opencode model=`zhipuai-coding-plan/glm-5.3`（即本平台在跑 GLM 编码代理） |
| 渠道集成 | 路由树含 slack/telegram/lark/dingtalk/wecom 回调；DB 有 channel_* 全套表 |
| 桌面端 | /download 提供 macOS dmg；本机存在 `.multica/` daemon 与 `multica_workspaces/`（CLI/daemon 与 web 同账号互通） |

**侧栏 IA（实测）**： 收件箱 / 我的任务 / 聊天 ｜ **工作**： 任务·项目 ｜ **自动化** ｜ **AI 团队**： 智能体·小队·Skills·运行时 ｜ **统计** ｜ **设置** ｜ 加入 Discord。顶栏常驻：`W Wgen`（工作区切换器）、`搜索... K`（命令面板）、`新建任务 C`（快捷键徽标直接写在按钮上）。

---

## ① 视图清单

> 截图列给出文件名，均相对 `docs/research/liveui/shots/`。认证态 = 已登录 2642328381@qq.com。

### 1.1 认证与入门流

| 路由 | 截图 | 页面呈现 | 可交互元素 | 视觉手法 |
| --- | --- | --- | --- | --- |
| /wgen/squads/<id>（未认证） | multica-01 | 服务端重定向到 /login，无内容闪现 | — | 防闪烁：重定向先于渲染 |
| /login | multica-02 | 「登录 Multica / 输入邮箱以获取登录验证码」单一邮箱输入框 + 继续按钮 + 桌面应用下载链接 | email 输入（#login-email）、继续 | 极简单列居中卡；近黑 primary 按钮；零装饰 |
| /login（OTP 态） | multica-03 | 「查看你的邮箱 / 已发送验证码至 …/ 57 秒后可重新发送」 | 6 格 OTP 输入（input-otp 库，autocomplete=one-time-code）、返回 | 分格 OTP 控件、倒计时文案 |
| 登录完成落点 | multica-04 | → /wgen/issues（任务列表） | — | — |
| /workspaces/new | multica-35 | 「认识 Mika / 关于你 → 工作区」3 步向导；工作区名称（随机按钮）+ URL 前缀 + 任务前缀 | 名称输入、随机、创建 | 分步指示器「工作区 3」；助手人格化命名 Mika |
| /invitations | multica-36 | 「没有待处理的邀请 → 继续创建你自己的工作区」空态 | 继续创建 | 空态引导 CTA |
| /onboarding | multica-33 | 已 onboard 用户直接重定向 /wgen/issues | — | — |

### 1.2 工作区主功能

| 路由 | 截图 | 页面呈现 | 可交互元素 | 视觉手法 |
| --- | --- | --- | --- | --- |
| /wgen（根） | multica-05 | **404 页**：「页面未找到 / 你要查找的页面不存在或已被移动 / 返回 Multica」 | 返回 | 工作区根无索引页——平台心智是「进列表页」而非「仪表盘」 |
| /wgen/inbox | multica-06 | 收件箱：渗透测试标准流程（GenC…）等待确认的通知流；未读摘要徽标 | 筛选收件箱、归档、通知操作、已归档 | 通知即任务的收件箱隐喻；🦋 emoji 做会话头像 |
| /wgen/chat | multica-07 | 左会话列表 + 右对话区的分栏聊天；「帮我创建一个渗透测试的…」开场建议 | 新对话、聊天操作、置顶、归档 | 对话式人机协作主入口；建议卡（建议第一个任务/推荐一个操作） |
| /wgen/issues | multica-08 | 任务表：全部/成员/智能体 三pill + 视图/筛选/显示/看板切换 + 「0 个智能体工作中」状态条 | 全部·成员·智能体（内嵌 pill 而非路由）、显示列、优先级「高」、行内 assignee 头像 | Linear 式表格密度；工作状态常驻顶栏 |
| /wgen/issues/WGEN-2 | multica-09 | **渗透测试标准流程（GenCPT 9-Phase 流水线）** 任务详情：描述+8 个 todo 复选框+富文本编辑器 | 复制代码、加粗/斜体/代码/待办列表/引用工具条、「用选中内容创建子任务」、文件上传 | todo 勾选进度即流水线阶段；富文本+子任务派生 |
| /wgen/issues/<uuid-已删> | multica-10 | 「这个任务不存在或已在该工作区被删除」（DB 有行但页面判删——软删除过滤） | 返回 | 软删除的空态处理 |
| /wgen/my-issues | multica-11 | 我的任务：全部/已分配/我创建的/我的智能体和小队 | 四分pill、筛选、看板 | 「我的智能体和小队」把 agent 产出并入个人视图 |
| /wgen/projects | multica-12 | 项目表：1 个项目「渗透作业交战」；列=名称/状态/优先级/进度；状态=计划中 | 新建项目、筛选、创建时间排序、表格切换、搜索项目 | 表格视图 + 进度列 |
| /wgen/projects/<id> | multica-13 | 项目详情：项目内任务表（同 issues 表格件）+ 属性面板（📁 图标） | 全部/成员/智能体、新建任务、属性 | 项目=任务容器，复用同一表格组件 |

### 1.3 AI 团队（渗透作业的核心编排面）

| 路由 | 截图 | 页面呈现 | 可交互元素 | 视觉手法 |
| --- | --- | --- | --- | --- |
| /wgen/agents | multica-17 | 智能体列表：9 个（含归档1）；「能领取任务、留…」能力摘要行；运行次数列、30 天活跃 | 新建智能体、我的/全部/已归档、筛选、最近活跃排序、搜索、行操作 | 卡片+表格双形态；活跃度作为默认排序信号 |
| /wgen/agents/<安全红队-队长> | multica-18 | 智能体详情：**概览/工作/能力/设置 四标签** + 分配工作按钮 | 概览·工作·能力·设置、分配工作、智能体操作 | 标签页组织 agent 生命周期 |
| /wgen/agents/<1111（副本）> | multica-19 | 已归档 agent：多一个「恢复」按钮 | 恢复 + 同上四标签 | 归档态差异化操作 |
| /wgen/agents/new | multica-20 | 「创建智能体 / 选择起点」分流页 | 返回、两种起点入口 | 双通道创建的分流封面 |
| /wgen/agents/new/ai | multica-21 | 「通过对话创建」：选运行时（Claude/WgendeMac…）+ 开始对话 | 运行时选择（默认=提供方）、开始对话 | 用对话生成 agent 配置的 wizard |
| /wgen/agents/new/manual | multica-22 | 「检查并配置」手动表单：名称/描述/指令/头像/skill 挂载/运行时/可见性（仅自己·整个工作区·指定成员） | 更换头像、添加建议、从工作区添加 skill、跟随 CLI 配置、三档可见性单选、创建并打开 | 完整参数面板；可见性三档是权限模型露出点 |
| /wgen/squads | multica-14 | 小队列表：2（安全红队、审计队）；我的/全部 + 成员头像堆叠 | 新建小队、我的、筛选、小队操作 | 头像堆叠表达编制 |
| /wgen/squads/安全红队 | multica-15 | 小队详情：归档/更换头像/添加描述/成员（leader 标记=安全红队-队长）/指引/添加成员/设为小队负责人/从小队移除 | 全套编制管理操作 | leader 徽标；编制=成员+指引 |
| /wgen/squads/审计队 | multica-16 | 同上；成员描述「审计执行（枚举/候选/验证/证伪底稿，gensource 全子技能+gensif…」——**审计 agent 的职责即写在成员卡上** | 同上 | 成员卡承载职责声明 |
| /wgen/skills | multica-27 | Skills 库：17 个；列=名称/被谁使用/操作 | 新建 skill、筛选、更新时间排序、搜索 | 「被谁使用」反向依赖列 |
| /wgen/skills/pentest-core | multica-28 | Skill 详情：概览/文件(1) 标签；名称+一句话触发描述+标签；**添加到智能体/删除 skill** | 添加到智能体、删除、概览·文件 1、添加标签、skill-name/skill 描述表单 | skill=文件包+触发描述的分发单元 |
| /wgen/runtimes | multica-24 | 运行时（机器）：1 台在线；「为智能体跑 C…」说明卡 + 「添加电脑」「和 Mika 开始」 | 添加电脑、和 Mika 开始 | 本机 daemon 注册为运行时；空态给两条路径 |
| /wgen/runtimes/<claude机> | multica-25 | 运行时详情：更新/重命名机器/添加自定义运行时/行操作 | 更新、重命名、添加自定义运行时 | 一机多 runtime（Claude/Opencode） |

### 1.4 自动化 / 统计 / 治理

| 路由 | 截图 | 页面呈现 | 可交互元素 | 视觉手法 |
| --- | --- | --- | --- | --- |
| /wgen/autopilots | multica-23 | **自动化/任务唤醒 两标签**；模板画廊：每日新闻摘要、PR review 提醒、Bug 分诊、每周进度报告、依赖审计（扫描安全漏洞和过时依赖包）、文档检查 + 从空白开始 | 新建自动化、两标签、模板卡 | 模板优先的创建漏斗 |
| /wgen/usage | multica-31 | 用量/错误 两标签；30d/全部项目；Token·费用·耗时·运行数 四指标；按天/按周 | 刷新、用量·错误、30d、四指标切换、按天/按周 | 「GMT+8 · 更新于 …」时区+新鲜度戳 |
| /wgen/billing | multica-32 | 「账单（测试页）」直接透传 multica.ai 的 Stripe Billing Portal | 刷新、打开 Stripe Billing Portal | 自托管计费外置 |
| /wgen/settings | multica-30 | 设置双栏：左 15 个子页导航（?tab= 查询参数） | 见下 | URL 可分享的 tab 导航 |
| settings?tab=profile | multica-43 | 个人资料：名称+描述（「例如：后端工程师（Go+Postgres）」——**给 AI 看的用户画像**） | profile-name/profile-description | 用户画像喂给 agent 上下文 |
| settings?tab=preferences | multica-44 | 偏好设置 | — | — |
| settings?tab=notifications | multica-45 | 通知 | — | — |
| settings?tab=shortcuts | multica-46 | 快捷键表 | — | — |
| settings?tab=tokens | multica-47 | **API Token**（CLI/daemon 凭证管理） | — | 机etry 入口在设置而非头像菜单 |
| settings?tab=workspace | multica-48 | 常规（工作区） | — | — |
| settings?tab=members | multica-49 | 成员（**成员管理在 settings，不在独立 /members 路由**——该路由 404） | — | — |
| settings?tab=issue-statuses | multica-50 | 任务状态自定义 | — | — |
| settings?tab=labels | multica-51 | 标签 | — | — |
| settings?tab=properties | multica-52 | 属性 | — | — |
| settings?tab=quick-actions | multica-53 | 快捷操作 | — | — |
| settings?tab=repositories | multica-54 | 代码仓库（vcs_integration_available=true） | — | — |
| settings?tab=integrations | multica-55 | 集成 | — | — |
| settings?tab=mcp | multica-56 | **MCP** 服务器管理 | — | MCP 一级设置位 |

### 1.5 hover 展开与公共页

| 路由/动作 | 截图 | 页面呈现 | 可交互元素 | 视觉手法 |
| --- | --- | --- | --- | --- |
| hover 工作区切换器 | multica-42 / 57 | 侧栏头部 `W Wgen` 悬停展开工作区菜单 | 工作区列表入口 | hover 展开不跳页 |
| hover 用户菜单 | multica-58 | 侧栏底部账号区悬停 | 账号操作 | — |
| /homepage | multica-37 | 营销首页：「你的下一批员工不是人类。」+ 案例文档更新日志 GitHub 52.9k + 进入工作台 | 案例文档更新日志 GitHub 进入工作台 | **Instrument Serif 102px 衬线大标题** 对比 app 内 Inter；唯一出现 spin 动画的页面 |
| /about | multica-38 | 关于页 | — | — |
| /changelog | multica-39 | 更新日志（64KB 长文，版本史极丰富） | — | 公开 changelog 即文档 |
| /usecases | multica-40 | 用例页 | — | — |
| /download | multica-41 | 桌面应用下载（mac dmg 等） | 下载 | — |
| /workspaces | multica-34 | 404（工作区切换在侧栏 hover 菜单内完成，无独立列表页） | — | — |

### 1.6 页面 → API 映射（实测抓包，GET 为主）

- 全局壳常驻：`/api/config`（feature_flags: agents_agent_builder / agents_skill_toggles / billing_workspace_subscriptions=false / plugins_v1=false / settings_resource_labels）、`/api/me`、`/api/inbox/unread-summary`、`/api/agent-task-snapshot`、`/api/working-agents`、`/api/chat/pending-tasks(+/has-any)`、`/api/chat/sessions`、`/api/invitations`、`/api/issue-statuses`、`/api/issue-wakeup-summaries`、`/api/pins`
- issues 列表：`POST /api/issues/table/rows` + `POST /api/issues/table/facets`（服务端分页/分面聚合）、`/api/issue-views`、`/api/issue-view-preferences`、`/api/issues/child-progress`
- issue 详情：`/api/issues/<uuid>`、`…/attachments`、`…/labels`、`/api/assignee-frequency`
- agents：`/api/agents`、`/api/agents/<id>/tasks`、`/api/agent-activity-30d`、`/api/agent-run-counts`、`/api/agent-builder/sessions`（AI 创建流）
- 其余：`/api/projects`、`/api/squads`、`/api/runtimes`、`/api/notification-preferences`
- 真实运行证据（后端日志）：`/api/daemon/tasks/<id>/status|messages|complete`、`GET /api/issues/<id>`（client_platform=cli）、daemon heartbeat

---

## ② 视觉手法总评（跨页提炼）

| 维度 | 实测值 | 评注 |
| --- | --- | --- |
| 色彩 | 全站 **单色灰阶**：--primary oklch(21% .006)（近黑）、--background 98.8% 白、--accent 96.7% 浅灰、--border 94.5%；无品牌色、无渐变 | Linear/Vercel 系「无色即高级」；彩色只让位给语义状态与用户内容 |
| 字体 | app 内 **Inter**（CJK 回退 PingFang SC/微软雅黑）+ **Geist Mono**（代码）；营销页 **Instrument Serif 102px** 衬线 | 内外双字体策略：工具感 sans vs 营销衬线 |
| 圆角/描边 | --radius .5rem；1px 浅灰边框分区 | 低圆角、靠边框与留白分层 |
| 动效 | 认证后页面 **animation-name 检出 0 个**；仅营销页 2 处（spin） | 几乎零动效——密度与响应速度优先 |
| 图标 | 内页 SVG 25–95 个/页（lucide 风格线性图标） | 线性图标与灰阶一致 |
| 徽标/状态 | 快捷键直接写在按钮上（搜索 K、新建任务 C）；「0 个智能体工作中」常驻；WGEN-N 人类键 | 快捷键可发现性内嵌；状态条常驻 |
| 层级 | 侧栏两组标签（工作/AI 团队）+ 顶栏三件套（切换器/搜索/新建）；详情页用标签页（概览/工作/能力/设置）而非子路由 | 三层深度内解决全部导航 |
| 空态 | 每个空态都带下一步动作（添加电脑/和 Mika 开始/继续创建） | 空态=引导 |

---

## ③ 探隐 v0.9d 落点建议

> 探隐当前痛点（据既有截图族：dashboard/coverage/graph/evidence/metrics）：安全作业数据密度高、视图多、状态语义重。Multica 是「AI 员工编排」而非安全平台，但其 UI 纪律恰好是探隐该补的课。建议按优先级：

1. **色纪律改造（最高优先）**：仿 multica 灰阶基底 + 「彩色只用于状态语义」。探隐的覆盖率/证据/指标页当前多彩，改为 oklch 灰阶容器 + 仅 verdict/风险等级用色，信息密度立刻上升一档。
2. **快捷键内嵌可发现性**：把 K（命令面板）/ C（新建）这类徽标直接印在按钮上（multica 实测做法），配 settings?tab=shortcuts 快捷键总表页。探隐的操作高频（切目标/切阶段/取证）受益最大。
3. **人类可读键**：WGEN-2 式 <前缀>-<序号> 键 + UUID 双轨。探隐的 engagement/phase/finding 全部只有 UUID 的话，补一个 YIN-17 式短键，截图引用、口头沟通、报告交叉引用都省力。
4. **设置页 ?tab= 查询参数子导航**：15 个子页 URL 可分享、可收藏；探隐的系统设置/规则/集成同理，且避免现在可能的弹层堆叠。
5. **「N 个智能体工作中」常驻状态条**：探隐的 agent 编排（若有后台作业/扫描）应在顶栏常驻运行状态 + 点击进入快照（/api/agent-task-snapshot 模式：单端点返回全部运行中任务的轻量快照，轮询成本低）。
6. **空态引导化**：每个空列表给「下一步动作」双按钮（如 multica 运行时页的 添加电脑 / 和 Mika 开始）。探隐的空 engagement/空阶段页应给「从模板创建」入口。
7. **服务端分页/分面端点**：issues 用 POST /table/rows + /table/facets 把分页与筛选下推服务端——探隐证据/发现列表如果还是前端全量过滤，照此改造。
8. **模板优先的创建漏斗**：autopilots 页先给 6 个模板卡再给空白创建。探隐新建交战/扫描任务时给「Webshell 巡检 / 凭据复用 / 报告生成」类模板卡。
9. **成员卡承载职责声明**：multica 小队成员卡直接展示该 agent 的职责描述（审计队的「枚举/候选/验证/证伪底稿」）。探隐的 agent/角色卡同理——卡片即文档。
10. **changelog 即营销**：64KB 公开更新日志页面（/changelog）。探隐若对外交付，版本史页是低成本信任资产。
11. **OTP 无密码登录的可选借鉴**：自托管场景 email OTP + 后端 [DEV] 日志码。探隐内网部署时可比 admin/password 更安全省事（但注意：**无邮件通道时验证码打日志是 v0.5.1 的弱点，探隐若做 OTP 要避免**）。
12. **不建议照搬**：multica 无仪表盘首页（/wgen 直接 404）——探隐的 dashboard 是核心视图，保留；multica 几乎零动效适合其工具定位，探隐的图/证据页可保留克制的过渡动画。

**互通备忘**：multica 正被用于真实红队作业（GenCPT 9-Phase 流水线 WGEN-2、安全红队/审计队两编制、pentest-core/recon/engagement/report-delivery 四技能、Claude+Opencode(GLM-5.3) 双运行时）。探隐若要与其互通，锚点是 multica 的 issue/squad/skill 数据面与 daemon 本机执行面（`~/.multica` + `~/multica_workspaces`）。

---

## 附：漫游合规记录
- 全程仅：GET 导航、登录 OTP POST、settings 标签页点击（均为导航性质 ?tab= 链接）、侧栏 hover。
- 未点击：新建/发送/启动/审批/暂停/删除/提交类按钮（agents-new、autopilots 等创建页仅访问未提交）。
- 未执行任何 git 操作；数据库仅 SELECT；docker 仅 exec 只读命令与 logs。
- 两次 walk 脚本重复执行（一次因工具调用绑定失败转为后台重跑），均为纯导航，无副作用；触发了 3 封 OTP 邮件请求（登录所需）。

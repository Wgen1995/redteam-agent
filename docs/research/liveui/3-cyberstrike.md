# CyberStrikeAI v1.7.23 活体参照分析报告

> **目标**：https://127.0.0.1:8443 （CyberStrikeAI v1.7.23，自更新通道在线）
> **上游**：[AIPentest/CyberStrikeAI](https://github.com/AIPentest/CyberStrikeAI)（原 Ed1s0nZ/CyberStrikeAI，实测 7812★ / 1589 fork / **Apache-2.0** / Go / 当日仍在推送）
> **本地源码真身**：`CyberStrikeAI/`（259MB，7457 文件；Go 后端 + 单体前端，完整可读）
> **分析方法**：源码只读分析为主（组件树/路由/样式/API handler/数据模型全可见），HTTP 仅做登录(1次POST)+GET 验证 live 数据。
> **纪律声明**：未触发任何扫描/建任务/改状态操作；未修改 CyberStrikeAI 目录任何文件；未执行任何 git；live API 只调用了只读 GET 端点。

---

## ① UI 设计解构（源码级）

### 1.1 总体架构：与探隐同律的"零框架"单体

CyberStrikeAI 的前端与探隐共享同一条语言律：**无 React/Vue、无构建步骤、无 npm 依赖**。它的全部前端是：

| 层 | 文件 | 规模 | 说明 |
|---|---|---|---|
| 页面模板 | `web/templates/index.html` | **673KB / ~5200 行** | 所有 29 个页面全部静态写死在一个 DOM 里，Go 模板仅注入 `{{.Version}}` 一个变量 |
| 页面逻辑 | `web/static/js/*.js` | 45 个业务模块 + **41 个 `.test.cjs` 前端单测** | 每页一个文件，IIFE 封装 + `window` 导出 |
| 样式 | `web/static/css/style.css` | **47,221 行 / 1.1MB** | 全部手写；另有 c2.css(4482行)/mobile.css(3628行)/tool-guard.css/chat-plan-progress.css |
| vendor | 7 个库 | — | marked、DOMPurify、cytoscape、elk、i18next、xterm(+fit)、xlsx — 全部是运行时 `<script src>`，无打包 |

**关键判断**：这是"零框架律"跑到 7812★ 生产级规模后的形态样本——单体模板 673KB、CSS 4.7 万行依然可维护（靠 BEM 风格前缀命名 + 每页独立 JS 文件 + 前端单测），证明探隐的路线在大体量下成立，但也展示了技术债的累积形态（style.css 单文件 4.7 万行已经需要靠注释分区）。

### 1.2 状态管理与复用模式（源码级写法）

无任何响应式框架，纯三层模式：

1. **模块级闭包状态**：每个 JS 文件 IIFE 内持有私有状态对象。如 `c2.js` 头部：
   ```js
   (function(){ 'use strict';
     const C2 = { currentPage:'', listeners:[], sessions:[], tasks:[],
       tasksFilter:{status:'',task_type:'',session_id:'',since:'',timePreset:'all'},
       eventSource:null, terminalInstance:null, terminalQueue:[], ... };
     // ...4500行后
     window.C2 = C2; })();
   ```
2. **DOM 即状态**：服务端渲染全部静态结构，JS 只做 `document.getElementById` 定点填数（`setEl('dashboard-vuln-total', n)`）。没有 vdom、没有 diff，靠"ID 契约"连接模板与逻辑。
3. **全局函数即 RPC**：`onclick="switchPage('c2-sessions')"` 直接绑全局函数；`rbac-guards.js` 再对 **400+ 个全局写函数建立 {函数名: 所需权限} 映射表**，加载完成后统一包装一层 `requirePermission` —— 不改任何业务代码就实现了全站写操作权限门控。这是"HTML 里写 onclick"这种最土写法的工程化救赎方案。

**复用组件清单**（探隐可直接对标的自有组件）：
- `modal.js`：统一弹窗（openAppModal/closeAppModal），先显示遮罩、下一帧再填大段内容避免主线程争抢；body 锁类 `app-modal-open` 防滚动穿透。
- `notifications.js`：铃铛下拉通知中心 + 未读徽章 + 全部已读。
- `theme.js`：system/light/dark 三态循环按钮；**防闪烁技巧**：`<head>` 内联脚本在任何 CSS 加载前读 localStorage 设置 `html[data-theme]`。
- `i18n.js`：`data-i18n`/`data-i18n-attr` 属性驱动，i18next 加载 zh-CN/en-US/ru-RU 三份 JSON。
- `storage.js`：localStorage 偏好读写（侧栏折叠、对话排序、每页条数等 UI 偏好全部持久化）。
- `chat-scroll.js`：聊天滚动位置管理（独立成文件并有单测）。

### 1.3 布局骨架与导航 IA

```
<body>
 └ .container (100vh flex-col)
    ├ header（48px：logo+版本徽章 | API文档/GitHub/主题/语言/通知铃/头像菜单）
    └ .main-layout (flex)
       ├ aside.main-sidebar  224px ←→折叠 64px（仅图标，悬浮出 data-title 提示）
       │   └ nav.main-sidebar-nav
       │      ├ .nav-section-label  ── 分组标题（工作台/安全作业/能力中心/平台管理）
       │      ├ .nav-item[data-page=dashboard]  ── 单页项
       │      └ .nav-item.nav-item-has-submenu  ── 可展开子菜单项
       │          └ .nav-submenu > .nav-submenu-item[data-page=c2-sessions]
       └ .content-area
          └ .page#page-xxx (display:none ↔ .active) × 29页
             ├ .page-header（h2 + .page-header-actions 按钮组）
             └ .page-content
```

完整 IA（实测导航树，29 页）：
- **工作台**：仪表盘 / 对话 / 安全防护▸(人机协同、调用拦截)
- **安全作业**：项目管理 / 资产管理▸(资产概览、资产库、信息收集) / 漏洞管理 / 任务管理 / 工作流 / WebShell管理 / C2▸(监听器、会话、任务、Payload、事件、流量伪装) / 文件管理
- **能力中心**：MCP▸(状态监控、MCP管理) / 知识▸(知识管理、检索历史) / 技能▸(状态、管理) / 智能体▸(管理) / 角色▸(管理)
- **平台管理**：平台权限 / 系统设置（内部分区菜单：基础/安全/HITL/信息收集/知识库/终端/存储/审计/机器人/内容/一键更新）

### 1.4 视觉系统（可直接抄的配方）

**设计令牌**（`style.css` :root，共 105 个 CSS 变量 + dark 全套覆盖）：
```css
:root {
  --accent-color:#0066ff;  --accent-hover:#0052cc;
  --brand-gradient: linear-gradient(135deg,#0066ff 0%,#7c3aed 100%); /* 蓝紫品牌渐变 */
  --bg-primary:#fff; --bg-secondary:#f8f9fa; --bg-tertiary:#f1f3f5;
  --text-primary:#1a1a1a; --text-secondary:#6c757d; --text-muted:#adb5bd;
  --border-color:#e9ecef; --shadow-sm/md/lg 三级;
}
html[data-theme=dark]{ --accent-color:#60a5fa; --bg-primary:#111827; --bg-secondary:#0b1120;
  --border-color:#263244; ... }  /* 暗色下 body 加 radial-gradient 蓝色氛围光 */
```
- 字体：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto...` 纯系统栈，无 webfont。
- 侧栏：`linear-gradient(180deg,#fafbfc,#f5f7fa)` 微渐变 + 右侧 1px 边 + 2px 0 8px 阴影；折叠动画 `width .2s ease`。
- **严重度色板**（全站统一）：critical `#dc3545` / high `#fd7e14` / medium `#ffc107` / low `#20c997` / info `#6c757d`。
- **徽章配方**：`background: rgba(色,0.1); color: 色;` —— 10% 透明度底 + 全色前景，深浅主题通用。
- **卡片严重度编码**：`border-left:4px solid 严重度色`（漏洞卡片），一眼分级不用读字。

### 1.5 状态可视化手法（仪表盘重点，源码级）

**(a) KPI 卡**（5 张：运行中对话/漏洞总数/工具调用次数/成功率/Token用量）：
- 结构：`dashboard-kpi-card`（整卡 `role=button tabindex=0 onclick=switchPage`，**卡即导航**，键盘 Enter/Space 同样生效）→ `kpi-head(label+svg图标)` → `kpi-value(大数字)` → `kpi-sub(副标徽章)`。
- 副标徽章承载次级语义：任务卡下"系统空闲/正在执行"（idle/running 类）、漏洞卡下红点徽章"N 个待处理严重"。
- 图标色按卡语义区分：`kpi-icon-tasks/vuln/calls/rate/token` 各配色。

**(b) 严重度半环 Donut**（`dashboard.js renderSeverityDonut` L2035，纯手写 SVG）：
- 几何：半环（π 弧）双层填充——外层弧段 `arcSegmentPath(cx,cy,rOuter,rInner,angleStart,angleEnd)` + 内层高光 `gloss`；背景轨有凹槽阴影+vignette。
- 数据映射：每段弧长 = value/total × π×coverage；**未分级漏洞按比例留白**（求和<total 时轨迹露出）。
- 标签：**占比≥5% 才画外置标签**（text + 引导线 line，text-anchor 按 cos(mid) 分 start/middle/end），彻底避免小段标签重叠。
- 动画：中心总数 **count-up**（requestAnimationFrame，ease-out cubic，时长 `min(520, 180+Δ×28)`ms；`prefers-reduced-motion` 直接跳终值）；弧段入场 `donut-ready` 类逐段 animation-delay。
- 交互：每段叠一层透明 hit path（tabindex=0 role=button aria-label），hover 高亮 + 图例联动 + 中心数字切换为该级计数。

**(c) 加权风险分卡**（`renderSeverityInsights` L1588）：
- 公式：`score = critical×10 + high×5 + medium×2 + low×0.5`（info 不计）。
- 阈值：0→安全 / ≤3低 / ≤10中 / ≤30高 / >30极高；1 个待处理严重即进"中"。
- **口径自洽设计**（源码注释明说）：用 status=open 的严重度而非全量——"全部修复后风险等级仍显示极高 + 紧急徽章归零"的语义冲突被这个口径选择消除。风险条 0-100 线性映射，≥100 显示"N+"。
- 紧急徽章（待严重/待高危计数）与加权分完全同源，永不矛盾。

**(d) 修复率**（`renderVulnStatusPanel` L1542）：
- 口径：`fixed / (open + confirmed + fixed)` —— **误报/已忽略是"中性闭环"，不进分母**（注释写明理由）。展示为 `78.6% (12/15)` 双层。
- 双色进度条：fixed 实心 + confirmed 叠加，五种状态计数横排。

**(e) 工具调用状态**（chat 内）：`.tool-call-running/completed/failed/blocked/incomplete` 五态 + `.tool-call-blocked`（被 tool-guard 拦截）单独视觉；迭代分割线：SSE `iteration` 事件 → "第 N 轮迭代" divider 插入消息流。

**(f) 数据层工程**（`refreshDashboard` L42）：
- 一次 `Promise.all` 并发 **24 个 GET**；每路 `fetchJson` 失败/取消都返回 null 不抛错——单接口挂不废全盘。
- `AbortController` 防 race：新刷新先 abort 上一轮；结果回来先查 `signal.aborted`。
- **首载/轮询区分**：只有首次加载才显示 "…" 占位，轮询时后台拉新平滑替换（不闪占位）。
- "上次更新 HH:MM:SS" + stale 警示图标（数据过期提示）。

---

## ② 功能清单 + 成熟度评分

评分 1-5（5=生产打磨完备：边界处理+无障碍+i18n+测试+异常文案全齐）。

| # | 功能 | 状态 | 分 | 证据 |
|---|---|---|---|---|
| 1 | 对话式开战（自然语言→渗透任务） | 有 | **5** | chat 页 4 种 agent 模式 + 角色选择 + @工具提及；live 会话标题即"渗透测试http://localhost:3081(用户名 admin,密码***)" |
| 2 | 多智能体编排（eino_single/Deep/Plan-Execute/Supervisor） | 有 | 5 | `internal/multiagent` + `agents/` 16 个 markdown 智能体（recon/横向移动/权限提升/清理回滚…） |
| 3 | 仪表盘（KPI+严重度环+风险分+修复率+接入概览） | 有 | **5** | ①.5 节全部；俄语长文案溢出都修过（CHANGELOG） |
| 4 | 漏洞管理全生命周期 | 有 | 5 | open/confirmed/fixed/false_positive/ignored 五态 + 复测(`vulnerability-retest`) + 自动告警 + 严重度卡片 |
| 5 | HITL 人机协同审批 | 有 | **5** | `hitl.js`(105函数)+`internal/hitl`；白名单外→审批；chat 内审批 dock；危险 C2 任务类型强制 HITL(`IsDangerousTaskType`) |
| 6 | 调用拦截（tool-guard） | 有 | 4 | 规则化工具拦截 + 测试器 + 多人编辑 ETag 乐观锁（CHANGELOG） |
| 7 | MCP 工具体系 + 监控 | 有 | 5 | live 实测 **139 个工具**（80+ 安全工具 yaml + 批量任务/项目/漏洞等自研工具）；监控页成功率/blocked 统计 |
| 8 | 项目管理 + 事实图谱 | 有 | 4 | 项目 CRUD/归档/置顶 + cytoscape+elk 双布局图编辑器；live 事实含"测试覆盖矩阵" markdown 正文 |
| 9 | 资产管理（概览+库+FOFA导入） | 有 | 4 | 资产库多维筛选（严重度下限/协议/端口）+ 批量编辑 + 项目绑定 |
| 10 | 信息收集 | 有 | 4 | 独立页 + FOFA/quake/shodan/zoomeye 搜索工具 |
| 11 | 任务管理（agent-loop 运行/已完成/取消） | 有 | 4 | SSE 任务事件总线 `task_event_bus.go` + 取消语义测试 |
| 12 | 批量任务队列 | 有 | 4 | 队列级 pause/start/rerun/定时/并发度；live 有并发=2 的队列 |
| 13 | 工作流（可视化节点图） | 有 | 4 | start/tool/agent/condition/hitl/output 节点 + **自然语言生成工作流草稿** + dry-run + 包导入 |
| 14 | WebShell 管理 | 有 | 4 | 连接管理 + exec + 文件 + AI 对话关联；OS/编码自适应（`webshell_os/secrets` 测试） |
| 15 | 内置 C2 框架 | 有 | 4 | 自研：4 种监听器(tcp_reverse/http(s)_beacon/websocket)、AES-256-GCM、SQLite+EventBus、xterm 交互终端、文件管理、流量伪装 Profile |
| 16 | 知识库（RAG） | 半 | 3 | 代码完备（索引/检索/日志），**live 未启用**；检索日志独立页 |
| 17 | 技能体系 | 有 | 4 | live 20 个技能（攻击面侦察/后渗透/输出标准/验证…）+ 技能监控页 |
| 18 | RBAC 权限体系 | 有 | 5 | 资源级 scope（all/项目id）+ 角色会话 + UI 静态属性门控 + 全局函数守卫 |
| 19 | 审计日志 | 有 | 4 | 查询/CSV 导出/日期选择器组件独立成文件 |
| 20 | 通知中心 | 有 | 4 | 铃铛下拉 + SSE 推送 + 已读管理 + RBAC |
| 21 | Token 用量统计 | 有 | 4 | 按天/按模型/缓存命中/reasoning 分离；live: glm-5.3, 134 调用, 8.6M tokens, 8.4M cached |
| 22 | Web 终端 | 有 | 4 | xterm + ws + resize observer + 历史队列 |
| 23 | 自更新系统 | 有 | 4 | 检查/应用/回滚/adopt，UI 进度轮询 1.5s（离页即停） |
| 24 | i18n 三语 | 有 | 4 | zh-CN/en-US/ru-RU 全量 JSON + 属性驱动 |
| 25 | 移动端适配 | 有 | 4 | mobile-ui.js(底部 tab 导航) + mobile.css 玻璃效果 |
| 26 | 浏览器插件 + Burp 插件 | 有 | 3 | 抓包→平台对话（MV3 扩展 + Java Burp 扩展） |
| 27 | IM 机器人（企微/钉钉/飞书） | 有 | 3 | `internal/robot` + ilink |
| 28 | PWA | 有 | 3 | manifest + 主题色 meta + iOS meta 全套 |
| 29 | 前端单测 | 有 | 4 | **41 个 `.test.cjs`（node:test）**，零构建下的 UI 纯函数测试法 |
| 30 | API 文档 | 有 | 3 | /api-docs 自托管 OpenAPI 渲染 + i18n |

**功能密度判断**：这是目前开源可见的**进攻侧 AI 安全作业平台功能最全的单体**——从侦察到 C2 到报告闭环全覆盖，且每一格都有异常处理与无障碍打磨，没有空壳页。

---

## ③ 业务使用流（live 数据推断）

### 3.1 实测 live 快照（2026-10-15 13:36–14:16，全部 GET 读取）

- **1 个项目**：`烛龙靶场`（描述"烛龙作为靶场"，pinned，当天 13:36 创建）——**该平台正在被用来攻击 ZhuLong 平台本身**（目标 http://localhost:3081，即第 4 号报告对象）。
- **1 个会话**：标题原文 = "渗透测试http://localhost:3081(用户名 admin,密码***)。"，roleName=渗透测试，agentMode=**supervisor**，13:38 创建，14:16 最后更新。
- **消息流**（4 条）：用户粘贴目标+凭据 → assistant"处理中…任务已被用户取消" → 用户"继续" → assistant 输出**完整 markdown 渗透测试最终报告**（含执行摘要）。
- **4 条漏洞**（全 open，全部由 agent 自动记录）：HIGH Vite dev server @fs 未认证泄露完整数据库+源码；HIGH 环境探活 SSRF 闸门 DNS(nip.io)绕过；LOW 登录时序用户名枚举（scrypt 均值差 8.6ms vs 1.9ms）；INFO 账号锁定机制定向 DoS。
- **工具足迹**：151 次调用 / 144 成功 —— exec×104、http-framework-test×24、upsert_project_fact×5、query_assets×4、record_vulnerability×4。
- **批量队列**："烛龙平台渗透测试"，并发=2，supervisor，绑定项目，1 个子任务（已取消）。
- **成本足迹**：glm-5.3，134 次模型调用，8.66M tokens（其中 **8.41M 命中缓存**，97%）。
- 事实图谱里有 agent 自己写的"测试覆盖矩阵"事实（note/test-coverage-matrix），正文是 markdown 验证矩阵，含每条漏洞的利用条件与边界。
- C2 监听器/会话为空（该目标用不上）、知识库未启用、HITL 无待审。

### 3.2 真实工作流中它扮演的角色（从上述数据反推）

**角色 = 进攻侧 AI 队长的驾驶舱**，一个 web 控制台跑完红队全流程：

1. **立项**：建项目（靶场/客户）→ 后续一切资产/漏洞/事实/会话挂项目，仪表盘按项目过滤。
2. **开战**：对话页 = 作战入口。选角色（渗透测试）+ 选编排模式（supervisor 专家路由）→ **一句话粘贴目标+凭据即开战**。Agent 自主：计划（plan-progress 面板显示 taskcreate/taskupdate 任务列）→ 调工具（nmap 类 exec、http-framework-test）→ 边打边沉淀（query_assets 查资产、upsert_project_fact 写图谱、record_vulnerability 报漏洞）。
3. **中断与恢复是常态**：用户取消过一次，"继续"后从上下文续跑——**取消/恢复语义是生产刚需**，不是锦上添花。
4. **交付**：最终 assistant 消息直接产出完整 markdown 渗透报告；漏洞进管理页走 open→confirmed→fixed→复测闭环；事实图谱沉淀为项目记忆（下轮攻击可查）。
5. **规模化**：批量队列（并发度、定时、rerun）把"一次对话"变成"一批目标"；RBAC+通知支持多人协作；企微/钉钉机器人把战场延伸到 IM。
6. **治理**：HITL 审批 + tool-guard 拦截 + 审计日志 + 危险 C2 任务强制人审——"intent becomes governed execution"（README 原话）。

### 3.3 对探隐的镜鉴

探隐的 goal 创建可直接对标其"对话式开战"：**用户给意图 → 系统拆计划 → 执行可见（进度面板）→ 结果落账（漏洞/事实）→ 随时可中断恢复**。CyberStrikeAI 证明这套闭环在真实作业里跑得通（当天 38 分钟内从建项到 4 漏洞+报告）。

---

## ④ 对探隐的判决

### 判决：**仅参照**（置信度 85%）

**理由**：
1. **许可证不是障碍，架构才是**。Apache-2.0 允许逐文件搬运（带 attribution）。但它是 Go+gin 单二进制 + SQLite + 673KB 单模板 + 47K 行 CSS 的**一体化单体**——探隐是 Python stdlib 编排 + 13 本 TSV 账 + 哈希链，底座完全不同，"直接复用"无从谈起；"整页二开"需要把 Go handler+前端 ID 契约一起搬，等于在探隐里养一个 Go 副内核，违反探隐底座自持律。
2. **写操作 UI 与投影律冲突**。CSA 的 UI 本质是武器操作台（C2 控制台、WebShell 执行、批量开火），全站 400+ 写函数；探隐已立法"UI 只读投影律"。复用其页面骨架必然引入写路径，动摇已定法。
3. **体量不成比例**。CSA 前端 ≈ 2.2MB 源码 / 29 页；探隐 webui 是观察面，不是作业面。整抄是把航母甲板装上侦察艇。
4. **但它是最好的"零框架律大型化存活证明"**：同律（无框架无构建）+ 同代（vanilla JS+SVG+hash 路由）+ 生产级打磨，每个具体手法都可直接平移——这正是"仅参照"的含义：**抄手法与配方，不抄代码本体**。

### 翻案条件（出现即改判）

| 证据 | 改判为 | 说明 |
|---|---|---|
| 探隐决定做攻击基础设施页（C2/会话/监听器） | **二开**（该子域） | c2 六页 IA + master-detail + xterm 集成可直接平移改造，c2.js/c2.css 是自洽子模块，剥离成本可控 |
| 探隐 webui 重写预算 ≥2 人周且接受外源 JS 文件 | **二开**（仪表盘子域） | dashboard.js 的 donut/风险分/修复率三件套是独立纯函数 + ID 契约，单独抽走即可 |
| 探隐需要多语言/多角色（团队化） | **二开**（rbac-guards + i18n 属性驱动方案） | 这两个方案与业务零耦合，文件级移植 |
| 上游出现探隐可直接消费的"判据/验证层"独立包 | 复用 | 目前不存在（其验证逻辑与 eino 深度耦合） |

---

## ⑤ 可直接偷的 10 条（文件级出处 → 探隐落点）

1. **KPI 卡"卡即导航"模式**：整卡 `role=button tabindex=0 onclick=switchPage` + onkeydown Enter/Space；副标徽章（idle/running/红点严重数）承载次级信息。`web/templates/index.html` L513-537（`dashboard-kpi-card/-head/-value/-sub(-badge)`）+ `dashboard.js setKpiSubBadge`。 → **探隐仪表盘首页**：门流程通过率/在跑 goal 数/哈希链长度做成可点卡片。

2. **手写 SVG 半环 Donut 全套算法**：`arcSegmentPath/halfRingPath` 几何 + 渐变填充 + 光晕层 + 引导线标签（≥5% 才画，anchor 按 cos 分三档）+ 中心 count-up（rAF ease-out，`prefers-reduced-motion` 降级直跳）+ 透明 hit 层键盘可达。`web/static/js/dashboard.js` L2035 `renderSeverityDonut` + `scheduleSeverityCenterCountUp`。 → **探隐判据覆盖度环 / 九门漏斗图**：纯 SVG 无 canvas，与探隐语言律完全兼容。

3. **加权风险分模型 + 口径自洽**：`score=c×10+h×5+m×2+l×0.5`，阈值 0/3/10/30 → 安全/低/中/高/极高；**只按 open 口径算**（源码注释：避免"全修复后仍显示极高"的语义冲突）；紧急徽章与分同源永不矛盾。`dashboard.js` L1588 `renderSeverityInsights`。 → **探隐 goal 风险概览卡 / 验证结果分级页**：判据失败加权分可直接套此模型。

4. **修复率分母口径**：`fixed/(open+confirmed+fixed)`，误报/忽略为"中性闭环"不进分母——注释明写理由；双色堆叠条（fixed 实+confirmed 叠）。`dashboard.js` L1542 `renderVulnStatusPanel`。 → **探隐验证结果页**：复验通过率 = 通过/(通过+待复验+失败)，无效判据不拉低比率。

5. **仪表盘数据层三件套**：24 路 `Promise.all` 每路失败返 null 不抛错 + `AbortController` 防 race（结果回来先查 aborted）+ 首载才显 "…" 占位、轮询平滑替换；"上次更新"时间戳+stale 图标。`dashboard.js` L42-190 `refreshDashboard`。 → **探隐观察面数据层**（13 本 TSV 账的聚合读取完全适用）。

6. **hash 路由 + 懒初始化 + 离页清定时器**：`.page` display 切换、`initPage` switch 分发每页加载函数、切页时统一 `stopUpdatePolling/cleanupTasksPage/stopExternalMcpPoll`（注释："离开设置页就没必要每 1.5 秒读一次"）。`web/static/js/router.js` L133 `switchPage`、L417 `initPage`、L620-640 清理段。 → **探隐 webui 路由层**：直解模式（如 #chat?conversation=xx 恢复会话）也一并参照 `buildHashForPage/scheduleChatConversationFromHash`。

7. **全局写函数权限守卫映射表**：`{函数名:'permission'}` 400+ 项静态映射，加载后统一包装 `requirePermission`——onclick 写在 HTML 里也能被系统性门控；配合静态属性 `data-require-permission` 做 UI 显隐。`web/static/js/rbac-guards.js` 头部 + `rbac.js`。 → **探隐多角色/只读 vs 操作员分离**：投影律下探隐只需把映射表全设为只读校验，天然合律。

8. **plan-progress 计划面板：拦截工具调用渲染执行计划**：识别 agent 的 taskcreate/taskupdate/tasklist 调用 → 渲染步骤列表（pending/in_progress/completed 徽章 + 总进度）；轮询节流三档常量（活跃 1500ms / 错误重试 4000ms / 终态驻留 2400ms）。`web/static/js/chat-plan-progress.js` 头部 + `web/static/css/chat-plan-progress.css`（独立小组件，203 行）。 → **探隐 goal 执行进度页**：goal 拆步 → 步骤状态可视化，轮询参数直接照抄。

9. **C2 会话页 master-detail IA**：`c2-session-layout` = 左侧会话列表（搜索+状态过滤+监听器过滤）+ 右侧详情（信息面板 + xterm 终端 + 文件管理 tab）；任务页 = 汇总条(成功/失败/待处理计数) + 时间快捷筛选(15m/1h/24h/7d/全部) + 状态/类型下拉。`web/templates/index.html` L3005-3115 + `web/static/js/c2.js`（`renderSessionInfoPanel` L495、任务筛选 L3346-3400）+ `c2.css`。 → **探隐远期 harness 平权遥控会话页**（任意 harness 会话列表 + 详情 + 终端复用此 IA；近期可先抄"汇总计数条+时间快捷筛选"到任务台账页）。

10. **严重度徽章配色配方 + 无闪烁暗色主题**：徽章 = `rgba(主色,0.1)底 + 主色字`（五档色板全站统一，深浅主题通用）；卡片 = `border-left:4px` 色条；主题 = `<head>` 内联脚本先于 CSS 读 localStorage 设 `html[data-theme]`，三态循环按钮 + 全套 CSS 变量覆盖。`web/static/css/style.css` L27572（badge）、L27331（卡片）、L8-35（:root/dark 令牌）、`web/static/js/theme.js`。 → **探隐全局视觉系统**：v0.9d 升级批直接换装——令牌表、暗色律、徽章配方三件套照抄即可获得生产级观感。

**附赠（不占名额）**：41 个 `.test.cjs` 用 node:test 测前端纯函数（`web/static/js/*.test.cjs`）——零依赖律下的前端测试范式，探隐 webui 可整体引入此法。

---

## 附：与探隐架构对照速查

| 维度 | CyberStrikeAI | 探隐 |
|---|---|---|
| 编排 | Go(gin)+Eino 多智能体 | Python stdlib |
| 判据/引擎 | MCP 工具 139 个（yaml 定义安全工具） | 直连 API 判据层 |
| 账本 | SQLite（统一建表迁移） | 13 本 TSV + 哈希链 |
| 流程 | HITL 审批 + tool-guard 拦截 | 九门流程 |
| UI | 673KB 单模板 + 45 模块 vanilla JS（写操作台） | 自有观察面（只读投影） |
| 共同律 | 零框架零构建 | 零框架零构建零依赖 |

*报告生成：源码只读分析 + HTTP GET 实证（登录 POST×1）。未触碰 ZhuLong 源码目录；未执行 git；未修改目标系统任何状态。*

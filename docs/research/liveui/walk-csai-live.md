# CyberStrikeAI 活体巡访实录（walk-csai-live · 批#1）

> 巡访日期：2026-10-16 14:05–14:20（CST）· 巡访者：界面漫游舰（探隐委托，无图像能力，全 DOM/API 文本层）
> 对象：CyberStrikeAI @ https://127.0.0.1:8443（v1.7.23，admin 账号本地授权登录，TLS 自签）
> 装备：python3 + playwright，channel="chrome" headless 1440×900，launch args=['--ignore-certificate-errors']，全部导航 wait_until="domcontentloaded"。
> 焦点：①用户真跑的战斗数据（对话/队列/漏洞/事实黑板）；②**开战/指挥/审批流**——方向盘批的直接参照：按钮在哪个页面、点了去哪、参数表单长什么样，逐项记录。
> 姊妹篇：ARTEX 侧见 walk-artex-live.md，靶场侧见 walk-zhulong-live.md，改进清单见 live-recon-1.md。

## 只读纪律执行声明

- 全部写操作仅一处：登录 POST（本地授权凭据，不入档）。
- 页面走访全部为 hash 路由切换（#dashboard→#chat→…）。
- **参数表单取证方式（任务书明示）**：CSAI 是单页应用，**全部弹窗表单常驻 DOM（隐藏挂载）**——本次直接扫描隐藏容器提取字段清单（36 个 modal 全量编目），**零点击打开**、零提交；仅批量队列详情等只读弹窗未做任何交互。未点任何 新建/发送/启动/审批/终止/删除 类按钮。

## 0. live 快照事实（2026-10-16 14:0x 实测）

| 项 | 实测值 | 证据 |
|---|---|---|
| 漏洞 | 4 条：高危 2 / 低危 1 / 信息 1，**全部待处理**，修复率 0%（0/4） | 仪表盘 DOM + 漏洞管理页 DOM |
| 工具调用 | 153 次 / 成功率 95.4% /「12 个工具」；exec 105 居首 | 仪表盘 DOM + Top10 条形 |
| Token | 8.8M（「近 7 天 137 次调用 · 今日 0」） | 仪表盘 DOM |
| 对话 | 4 个会话（3 个是连通性自检：SSE 自检/连接测试） | 对话页 DOM 会话列表 |
| 批量队列 | 1 个：「烛龙平台渗透测试 · 渗透测试 · Supervisor（专家路由）· 手工执行」，队列 ID 202610151338…，创建 2026/10/15 13:38:26，**已完成 100% (1/1)** | 任务管理页 DOM |
| 项目 | 1 个「烛龙靶场」（置顶📌·进行中·5 事实/4 漏洞/1 对话，备注「烛龙作为靶场」） | 项目管理页 DOM |
| HITL | 待审计 **0** 条；审批方=人工审批；审批引擎 OpenAI 协议 · glm-5.3 | 人机协同页 DOM |
| C2/WebShell | 监听器 0 / 会话 0 / 待审排队 0（全空态） | 仪表盘 C2 快捷卡 |
| 能力面 | MCP 139（启用 127·常驻 49）/ Skills 23 / 知识未启用 / 角色 13 / Agents 16 | 仪表盘能力总览 |

**与 2026-10-15 首轮（walk-csai.md）差分**：漏洞 4→4（无新增，但新增了 2 条：登录锁定 DoS + 时间侧信道枚举，替换了旧 2 条的位次——15 日 14:01–14:13 间新增 3 条、旧 SSRF/@fs 两条保留）；工具调用 151→153；Token 8.7M→8.8M。**CSAI 的战斗在 15 日 14:13 后就停了**（今日调用 0），主战场转到了 ARTEX。

## 1. 用户真战斗数据（逐页）

### 1.1 仪表盘（#dashboard）
- 5 KPI 卡 + 严重度分布（待处理 0·严重 0·高危 2 子徽标）+ 风险等级卡（加权风险分 10.5）+ 最近漏洞/近期事实 tab + C2/WebShell 快捷卡 + 批量队列卡 + 工具执行 Top10 + 能力总览。
- **最近漏洞四条全文标题**（DOM 逐字）：①「烛龙平台登录账号锁定机制可被未认证攻击者利用实施定向拒绝服务」（信息·待处理·23 小时前·目标 http://localhost:3081/api/auth/login（后端 7090）参数 username）；②「烛龙平台登录接口时间侧信道用户名枚举」（低危·待处理·23 小时前）；③「烛龙平台 Vite 开发服务器 @fs 路径未认证泄露完整数据库（含会话令牌）与服务端源码」（高危·待处理·1 天前）；④「烛龙平台环境探活 SSRF 防护绕过（DNS 主机名绕过环回/元数据闸门）」（高危·待处理·1 天前）。
- 工具执行 Top10：exec 105 / http-framework-test 24 / upsert_project_fact 5 / query_assets 4 / record_vulnerability 4 / complete_agent_task 2 / create_asset 2 / list_vulnerabilities 2 / update_vulnerability 2 / execute-python 1。

### 1.2 对话页（#chat）= 开战主入口
- 左栏：「+ 新任务」按钮 / 项目选择（烛龙靶场 📌 / 无项目）/ 会话搜索 / 最近对话 4 条（列表文本逐字：「SSE 连通性自检：只回复「ok」，不要调用工具。」「连通性自检：请只回复一个词「正常」…」「你好。这是一次连接测试，请只回复两个字母:OK…」）。
- 中央空态「要测试什么？」；底部输入框 + 发送 + 附件上传。
- **会话状态条（DOM）**：「无项目 · 🔵 默认 · Eino 单代理（ADK）· **人工审批：关闭** · glm-5.3 · 系统 · 发送」——模式/HITL/模型三个会话级开关常驻可见。
- 会话设置控件（DOM id 实证）：agent-mode-select（eino_single/deep/plan_execute/supervisor）、hitl-mode-select（off/approval/review_edit）、hitl-timeout-select、hitl-sensitive-tools、角色选择、模型/通道选择。

### 1.3 项目管理（#projects）= 事实黑板
- 项目卡：烛龙靶场 · 进行中 · 置顶 · 「5 条事实 / 4 个漏洞 / 1 个对话」· 描述「烛龙作为靶场」· 1 天前。
- 详情七 tab：漏洞管理 / **事实黑板** / 攻击路径 / 资产库 / 关联对话 / 关联漏洞 / 设置。
- **事实黑板 5 行全录**（表格列 Key/分类/摘要/关系/Body/置信度/更新/操作）：
  1. `note/test-coverage-matrix` · note · 「烛龙平台全量渗透测试覆盖矩阵：4 条记录（2 high/1 low/1 info）+ 11 类防御有效项；白盒+黑盒双轨验证完毕」· — · 有详情 · **已确认**
  2. `exploit/vite-fs-db-leak`（关联漏洞 ID e4285f9c…）· exploit · 「Vite @fs 未认证下载 zl.db 全库（311KB 密码哈希+业务数据）与服务端源码；fs.allow=monorepo 根目录过宽；会话令牌仅存哈希故劫持不成立」· ↑0 ↓1 · **可复现** · 已确认
  3. `exploit/ssrf-healthcheck-dns-bypass`（关联漏洞 1fd20686…）· exploit · 「环境探活 SSRF 闸门绕过：nip.io DNS 域名绕过 forbiddenHealthHost 字面量检查，实测 127-0-0-1.nip.io:7090 探活返回 200，metadata IP 网络层已触达」· ↑0 ↓1 · 可复现 · 已确认
  4. `infra/attack-surface-map` · infra · 「攻击面测绘完成：3081 Vite 前端 + 7090 后端直连，38+ API 端点清单已固化；setup 已关闭；@fs 项目内任意读已确认；沙箱需找装配面缺口」· — · 有详情 · 已确认
  5. `target/zhulong-platform` · target · 「烛龙 ZhuLong 测试平台 @ http://localhost:3081：Vite dev server 前端 + Node 后端 API（38+ 端点），admin/*** 已登录获 zl_sess 会话」· ↑2 ↓0 · 有详情 · 已确认
- 行操作：编辑/详情/废弃/删除；筛选：搜索/分类（target/auth/infra/business/finding/chain/exploit/poc/note）/置信度（待确认/已确认/已废弃）/仅待补全/隐藏废弃。

### 1.4 漏洞管理（#vulnerabilities）
- 顶部严重度汇总 + 筛选条（搜索/所属项目/状态五态/更多筛选：精确 ID·会话·任务·标签）。
- 4 张漏洞卡（标题/等级徽标/状态/所属项目/时间/**复测**按钮）——与仪表盘四条一致，时间戳 2026/10/15 13:51–14:13。
- 工具位：批量导出/批量删除/刷新/添加漏洞。

### 1.5 任务管理（#tasks）= 批量队列
- 队列卡（DOM 逐字）：「🎯 烛龙平台渗透测试 · 渗透测试 · **Supervisor（专家路由）** · 手工执行 · 202610151338… · 创建时间 2026/10/15 13:38:26 · 已完成 · 100% (1/1)」。
- 状态筛选：全部/待执行/执行中/已暂停/已完成/已取消；搜索（队列 ID/标题/创建时间）；自动刷新开关。
- **开战方式实证**：用户不是在对话页零散开战，而是**建了一个 Supervisor 模式的批量队列**（1 个子任务=「烛龙平台渗透测试」），队列 22 分钟后完成，产出 4 漏洞+5 事实——「批量队列当单任务用」。

## 2. 开战 / 指挥 / 审批流（方向盘批直接参照）

> 取证方式：隐藏 modal 容器全量 DOM 扫描（36 个编目，零点击）。以下每个表单给出：所在页面 / 打开按钮 / 字段逐项 / 动作按钮。

### 2.1 开战三入口

**A. 对话页直接开战（#chat）**
- 位置：左上「+ 新任务」新建会话；项目选择器绑定项目上下文；底部输入框写意图；发送。
- 战前参数（会话设置，常驻 DOM）：代理模式（Eino 单代理 ADK / Deep / Plan-Execute / Supervisor）· HITL 模式（off/approval/review_edit）· 超时 · 敏感工具名单 · 角色（13 个）· 模型通道（glm-5.3）。

**B. 批量任务队列（#tasks →「新建任务」→ `#batch-import-modal`）**——**参数最全的开战表单**，字段逐项（DOM id + 选项）：
| 字段 | 控件 id | 类型 | 选项/说明（DOM 逐字） |
|---|---|---|---|
| 任务标题 | batch-queue-title | text | 「为批量任务队列设置一个标题，方便后续查找和管理」 |
| 角色 | batch-queue-role | select | 默认（所有任务用该角色的提示词和工具执行） |
| 所属项目 | batch-queue-project-id | select | （未绑定）/项目列表 |
| 代理模式 | batch-queue-agent-mode | select | Eino 单代理（ADK）/ Deep（DeepAgent）/ Plan-Execute / Supervisor（专家路由）——「与对话页一致；后三种需已启用多代理」 |
| **工具审批** | batch-queue-hitl-policy | select | **沿用全局设置 / 关闭审批 / 人工审批 / Agent 审批 / Agent 审查编辑**——「队列内所有任务（含后续添加的）使用此设置；白名单、审计策略和等待时限沿用全局配置」 |
| 并发数 | batch-queue-concurrency | number | 「同时执行的子任务数量（1-8）。默认 1 为串行；含扫描类工具时建议 1-2」 |
| 调度方式 | batch-queue-schedule-mode | select | 手工执行 / 调度表达式（Cron） |
| Cron 表达式 | batch-queue-cron-expr | text | 「标准 5 段：分 时 日 月 周，例如 0 2 * * * 每日 02:00」 |
| 创建后立即执行 | batch-queue-execute-now | checkbox | 「默认不立即执行；关闭后队列保持待执行」 |
| 任务列表 | batch-tasks-input | textarea | 「每行输入一个任务指令…空行自动忽略」，placeholder 给了三个示例（端口扫描/SQL 注入检查/子域枚举） |
- 动作：取消 / **创建队列**。

**C. 资产扫描（#asset-library 行内「扫描」→ `#asset-scan-modal`）**
- 字段：用户提示词 textarea（asset-scan-prompt）——「可使用 `{{asset_id}}、{{target}}、{{host}}、{{ip}}、{{domain}}、{{port}}` 占位符；创建任务时会为每个资产生成一条任务」；创建后立即执行 checkbox（asset-scan-execute-now）。
- 动作：取消 / 确认发送。**模板变量把「资产→任务」做成了批量开战面**。

### 2.2 指挥（运行中干预）——**探隐方向盘批的最直接参照**

**A. 中断当前步骤（对话页 → `#user-interrupt-modal`）**——**两段式刹车 + 说明回注**：
- 正文（DOM 逐字）：「有工具在执行时：与 MCP 监控页『终止工具』一致，仅结束当前这一次工具调用，本轮推理会继续；说明可写入工具返回（USER INTERRUPT NOTE）。无工具在执行时（模型纯思考/流式输出）：仍可『中断并继续』——会暂停当前输出，把你的说明合并进上下文并自动续跑；进度详情时间线会出现『用户中断并继续』条目。**不需要整轮停止时请优先用本按钮；要结束整条任务请用『彻底停止』**。」
- 字段：中断说明 textarea（user-interrupt-reason，placeholder「例如：工具耗时过长，请先跳过并总结当前结果…」）。
- 动作三钮：**关闭 / 彻底停止 / 中断并继续**——三级语义：微调（中断并继续+说明）→ 单步停（终止工具）→ 整任务停（彻底停止）。

**B. 终止工具并补充说明（MCP 监控页 → `#mcp-tool-abort-modal`）**：
- 正文：「可选：说明为何终止或希望模型如何继续。提交后模型会先看到工具已输出内容（若有），再看到带『用户终止说明』标题的独立区块（中英标注，与命令行原文区分），最后是您的文字。」
- 字段：终止说明（可选）textarea（mcp-tool-abort-note）。动作：取消 / 提交终止。
- 配套 `#mcp-detail-modal`（工具调用详情）：「运行控制：仅中断当前这一次工具调用；对话与多步迭代任务会继续，不会等同于『停止任务』。终止工具」——**把「停这一步」和「停整个任务」在文案里显式分开**。

**C. 批量队列指挥（#tasks 队列卡 → `#batch-queue-detail-modal`）**：
- 动作五钮（DOM 逐字）：**添加任务 / 开始执行 / 重跑一轮 / 暂停队列 / 删除队列**；追加任务表单 `#add-batch-task-modal`（任务消息 textarea，「新增任务沿用队列的工具审批设置，可在队列详情中修改」）。

**D. 工作流画布（#workflows）**：节点库含**审批节点**（开始/工具/Agent/条件/审批/输出/结束）；「用自然语言创建工作流」弹窗（workflow-ai-modal）：工作流需求 textarea + 三个模板 chip（域名监控/报告审批/资产研判）+ 三开关（同时生成 objective 配置 / 允许生成定时触发建议 / **允许包含高风险节点草稿**）+ 动作（渲染到画布 / 生成草稿）——「AI 会生成可编辑草稿，不会自动保存或运行」。试运行弹窗（workflow-dry-run-modal）：输入试运行消息（作为开始节点 message 输入）。

### 2.3 审批流（HITL + 拦截双层）

**A. 人机协同（#hitl）= 审批中心**
- 顶部：「当前审批方」切换 **人工审批 / 审计 Agent**（引擎标注「OpenAI 协议 · glm-5.3」）；作用域说明（DOM 逐字）：「**作用于当前选中会话；未选会话时写入 config.yaml 作为全局默认，新建会话时沿用。切换后立即生效**」。
- 四 tab：待审计（当前 0）/ 审计策略 / 工具白名单 / 审计日志。
- 审计日志详情弹窗（hitl-log-modal）字段：ID/工具/会话/决策/审批方/审批引擎/时间/备注/载荷(JSON)。

**B. 调用拦截（#tool-guard）= 执行前正则闸门**
- 「已与服务端同步」状态点 + 总开关 + 规则卡（01 政府网站保护，`{match}` 模板）+ 全部规则验证 + 撤销修改/保存并生效。
- 添加规则弹窗（tool-guard-add-dialog）：「先配置规则，再用示例参数验证效果，确认后添加到列表。添加到列表后，点击页面顶部『保存并生效』应用规则」——**草稿态/生效态两级**。

**C. 会话级审批开关**：对话页 hitl-mode-select（off/approval/review_edit）+ 批量队列级 batch-queue-hitl-policy（沿用全局/关闭/人工/Agent 审批/Agent 审查编辑）——**审批策略三层覆盖：全局 config → 会话 → 队列**。

### 2.4 其余编目弹窗（36 个中的关键项）
- 攻击链可视化（attack-chain-modal）：重新生成/导出 PNG/导出 SVG/刷新；类型筛选（目标/行动/漏洞）+ 风险筛选（高 80-100/中高 60-79/中 40-59/低 0-39）+ 连接线图例（蓝=行动发现漏洞·红=使能关系·灰=逻辑顺序）+ 节点搜索。
- 添加漏洞（vulnerability-modal）：15 字段全表单（所属项目/会话 ID/对话标签/任务标签/标题/描述/严重程度/状态/漏洞类型/目标/前置条件/复现步骤/证据 POC/影响/修复建议/复测方式）——**人工补录漏洞的完整字段面**。
- 复测漏洞（vulnerability-retest-modal）：「每次确认都会**从原始对话创建独立分支，继承原项目和历史**，可继续多轮验证」+ 复测提示词 textarea（占位符自动替换）。
- 添加事实（fact-modal）：fact_key（八类前缀 target/auth/infra/business/finding/chain/exploit/poc/note）/分类/置信度（待确认/已确认/已废弃）/摘要/body/**插入攻击链模板·插入环境模板**两个快捷钮/置顶/关联漏洞 ID/**关系边（from→本事实，每行 type: source_fact_key；常用 type discovered_on/depends_on/leads_to/enables/exploits；保存时替换全部关系边）**。
- 新建项目（project-modal）：名称+描述（「仅供团队成员查阅，Agent 不会读取；需让 Agent 知晓的内容请写入事实黑板」——**项目描述与黑板职责显式二分**）。
- 新增资产（asset-editor-modal）：19 字段（资产地址必填+自动解析/项目/标签/URL/Host/IP/域名/端口/协议/标题/Server/国家/省/市/状态/负责人/部门/业务/环境/重要性）。
- 资产批量导入（asset-import-modal）：三步（下载模板→上传校验预览→导入）。
- WebShell 添加（webshell-modal）：Shell 地址/密码/类型（PHP/ASP/ASPX/JSP/自定义）/请求方式/命令参数。
- RBAC（rbac-user-modal / rbac-role-modal）：用户名/角色/资源范围（全部资源/指定资源/本人创建）。

## 3. 只读 API 面（被动捕获 38 个 GET 端点，全部 200）

hitl/default-config · projects · agent-loop/tasks · agent-loop/tasks/completed · notifications/summary · conversations · knowledge/stats · roles · external-mcp/stats · webshell/connections · config/tools · vulnerabilities · external-mcp · projects/dashboard-summary · multi-agent/markdown-agents · config · monitor/stats · hitl/tool-whitelist · batch-tasks · hitl/pending · skills/stats · vulnerabilities/stats · c2/listeners · c2/sessions · c2/tasks · usage/tokens · workflows/runs/pending · tool-guard · projects/{id} · projects/{id}/stats · projects/{id}/facts · assets/stats · assets · vulnerabilities/filter-options · workflows · monitor/calls-timeline · monitor
（fetch 直取需带鉴权头——会话 cookie 不随 fetch 走，DOM 已足够。）

## 4. 判决要点（给 live-recon-1）

1. **开战=三入口**（对话/批量队列/资产扫描模板变量），批量队列表单把 模式·审批·并发·调度 全部前置成建队参数——**开战即定治理**。
2. **指挥=三级刹车**：中断并继续（说明回注上下文）→ 终止工具（单步）→ 彻底停止（整任务）；批量队列另有 开始/暂停/重跑/追加。
3. **审批=三层策略**（全局 config→会话→队列）+ 双引擎（人工/审计 Agent）+ 规则闸门（tool-guard）独立于 HITL。
4. **事实黑板=结构化战果**：key 前缀分类 + 置信度 + 关系边（discovered_on/enables/…）→ 攻击链图谱；与漏洞记录显式分工。
5. **复测=对话分支**（继承项目与历史，可多轮）——比 ARTEX 的 retest 卡更清晰的交互模型。

# 能力并集审计 · ARTEX × CSAI × 我方（CLI+界面）· 2026-10-19

> 执笔：能力并集审计子代理（掌门问：「你真的看了 ARTEX/CSAI 所有能力并结合我们建设了吗？最开始的实现改造成界面，东西不能丢」）。
> 纪律：三源全部实读后落笔；本档为唯一写入件之一（另两件=本次三修的代码与测试）。
>
> ## 三源清单（全部实读，非转述）
>
> 1. **A 舰对齐档** = docs/reviews/2026-10-18-realign/A-artex-全件对齐.md（259 行逐条过：96 件判词=已超 14/已排 52/声明取舍 8/真空白 22；§〇 九处校对+§三 G1-G11 缺口清单）。
> 2. **B 舰对齐档** = docs/reviews/2026-10-18-realign/B-csai-全件对齐.md（229 行逐条过：68 件判词=已超 25/已排 33/声明取舍 4/真空白 5+已有等价 1；§〇 九处校对+§四 G1-G6 缺口清单）。
> 3. **我方原有 CLI 面**（仓内实勘，命令面逐项枚举）：
>    - `cli/tanyin-ledger` 派发面 **72 键 / 49 基名**（ledger.registry.dispatch_face() 实跑枚举；写命令族 add-goal/add-scope/add-asset/add-edge/add-fact/add-finding/add-evidence/add-intent/add-cred/amend-scope/approve/append-timeline/anchor/checkpoint/cleanup-checklist/supersede-finding/set-intent-status/set-cred-status/set-replay-state/intent-lease/chain-create/chain-advance/chain-ls/matrix-*/state-rebuild + 读命令族 pending-intents/unconsumed-facts/budget-check/budget-log/scope-check/converge-check/graph-horizon/graph-neighbors/graph-paths/hash-recheck/redact-scan/matrix-gaps/ledger-scope-coverage/ledger-tree-check/ledger-replay-summary/ledger-terminal-gate + builtin validate/verify-chain/next-id + zhulong-export）。
>    - 独立入口 **19 个 tanyin-***：replay(replay/matcher-test)、guard(exec/inject/deploy-vault)、phases(validate/gate/restart/resume-kit/cached/rebuild-state/denominator-ready/trigger-audit)、runner(start)、gateloop(start)、serve(start/status/stop)、tools(list/show/install/uninstall/verify-lock/exec)、knowledge(**14 子命令** init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map/approvers)、viz、budgetctl(enforce/rate)、canary(deploy/probe/recon-deploy/recon-recall)、egress(compile/verify/dry-run)、selfcheck、install、report、redact、evals(run/list/report)。
>    - 模块面：`python3 -m cli.warrior`（战士循环）、`cli/c2` 包（beacon/queue/webshell/echo/families/store——账本化 C2-lite，B 舰 G1 批做件）、`scripts/battle.py`（init/launch/watch/settle/auto 一条命令一整战）。
> 4. **ARTEX 23 页爬档** = .research/liveharvest/artex/（manifest.json+23 个 HTML 实件：dashboard/chat/tasks/task_detail/findings/traffic/tool_exec/llm_record/agents/agent_detail/approvals/asset_intercept/asset_sync/assets/config/intercept/llm/logs/mcp/notify/skills/tools/workspace）。
> 5. **CSAI 仓界面路由** = /Users/wgen/dsh-test/repos/CyberStrikeAI（web/static/js/router.js:116,644 实读）：SPA **29 pageId + 登录 = 30 视图**（dashboard/chat/hitl/tool-guard/asset-overview/asset-library/info-collect/projects/tasks/workflows/vulnerabilities/webshell/chat-files/mcp-monitor/mcp-management/knowledge-management/knowledge-retrieval-logs/roles-management/platform-rbac/skills-monitor/skills-management/agents-management/settings/c2-listeners/c2-sessions/c2-tasks/c2-payloads/c2-events/c2-profiles）。
> 6. **我方界面现状**（cli/webui/ 实勘）：页面 = 9 旧观察面（/ index、login、new、coverage、graph、evidence、metrics、session、activity）+ 5 控制台页（/console、/console/live、/console/graph、/console/findings、/console/approval）+ **20 个 /p/ 新页**（anchored-chat/approval-center/approval/asset-registry/assets/broadcast/coverage/evals/finding-detail/llm-recordings/llm-status/new-task/report-center/retest/settings/system/tasks/techniques/tools/workspace）+ capability.html（在飞未挂导航）；API = /api/v2 二十模块约 26 路由 + /api/console/* 4 投影 + 5 写路由（login/battle/new/battle/control/battle/say/approval/report/download）。
>
> 判词口径（本表）：
> - **已通（带路由）**＝界面有入口有数据，路由列给出；
> - **只通 CLI 没界面（东西丢了！）**＝能力在 CLI/库面真实存在但界面无入口——本次修或已在册波次；
> - **全缺**＝CLI 也没有（含「已建未接线」的投资件，如 judge_client）。
>
> ---

## 一 · 三列对照总表（能力按域分组）

### 域 1 · 任务

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| T1 | 任务列表（状态/预算/发现计数/时间） | ✓ /function/tasks | ✓ tasks 视图 | battle.py watch + battles 目录 | **/p/tasks**（七态徽章+预算预警线+发现双色+排序分页） | — | 已通（/p/tasks） |
| T2 | 新建任务（授权件前置） | ✓ 11 字段表单 | ✓ 批量建队 | battle.py init | **/p/new-task + /new**（八问表单+模板下拉+立即执行） | — | 已通（/p/new-task） |
| T3 | 任务行内操作（启动/暂停/恢复/结算停跑） | ✓ 行内五操作 | ✓ 批量队列 | battle.py launch + /api/battle/control（pause/resume/stop/launch 四动作在 server.py:869-996） | 列表页**零行内操作**——只有行点击进详情 | **本次修②**：/p/tasks 行内操作走既有 /api/battle/control | 只通 API 没界面（本次修） |
| T4 | 批量操作/归档冷存储/删除范围 | ✓ 批量+归档+DeleteTaskOptions | ✓ 批量 | 无（目录手工） | 无 | W6 已排（A:G9/G10） | 全缺（已排 W6） |
| T5 | cron 定时调度 | — | ✓ cron+并发旋钮 | 无 | 无 | B:G8 已排 W7 夜回归 | 全缺（已排） |
| T6 | 任务详情多页签（会话/链路/发现/复测/资产） | ✓ 10 页签 | ✓ 会话视图 | session_view/projections/graph_cmds | /session + /console/graph + /console/findings + /p/retest 分页承担 | 形态异=分页非页签，不追形 | 已通（形态异） |

### 域 2 · 发现

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| F1 | 发现总览（严重度分布+验证状态计数+按严重度排序） | ✓ findings 三视图四维筛选 | ✓ vulnerabilities 五态+复测钮 | query_cmds.latest_by + report_agg | **/console/findings** 有基础表+状态筛选，但**无严重度分布条、无默认按严重度排序、点行只开抽屉不进详情页** | **本次修①**：顶部严重度分布条+三态计数+按严重度排序+点行进 /p/finding-detail | 修后已通（/console/findings） |
| F2 | 发现详情（描述/证据/重放史/生命线） | ✓ 版本化证据绑定 | ✓ 15 字段 | report_render FD 九段 | **/p/finding-detail**（五区+CVSS 实算+重放史+链完整性） | — | 已通（/p/finding-detail） |
| F3 | 发现导出（JSON/SARIF） | ✓ 平面导出 | ✓ 批量导出 | findings_json/findings_sarif（report_artifacts） | /p/report-center + /api/report/download | — | 已通（/p/report-center） |
| F4 | 发现人工补录（字段表单） | — | ✓ 15 字段补录 | add-finding 全 19 列 | 无表单 | W6 发现库页带表单 | 只通 CLI 没界面（已排） |

### 域 3 · 证据

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| E1 | 证据库浏览 | ✓ 任务内证据页签 | ✓ 文件管理四来源 | E-index 查询族 | **/evidence**（44 卡）+ finding-detail 证据区 | — | 已通（/evidence） |
| E2 | 证据原文（原始请求/响应/工件哈希） | ✓ exchange 详情 | ✓ 上传下载 | EV 卡 raw_request + artifact_hashes | **/api/v2/evidence-raw**（head/full 懒载） | — | 已通（/p/finding-detail 内） |
| E3 | 流量录制回传（MITM） | ✓ /function/traffic | — | tanyin-egress 三态（不录内容=声明取舍） | 无 | W6 三源回传；MITM CA 声明不做 | 声明取舍+已排 |

### 域 4 · 知识

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| K1 | 技法卡列表+搜索 | ✓ /system/skills | ✓ knowledge-management+skills-management | tanyin-knowledge match/neighbors | **/p/techniques**（50 卡+搜索+计数） | — | 已通（/p/techniques） |
| K2 | 卡详情六节直读（场景/步骤/工具引用/纪律标注/证据标准/边界） | ✓ 技能详情 | ✓ 技能卡编辑 | knowledge export（md 单源） | /p/techniques 右栏六节只读——但**URL 无深链**（?id/?q 不识别，外部页进不来指定卡） | **本次修③**：?id/?q 深链直读+选中同步地址栏 | 修后已通（/p/techniques?id=CP-xxxx） |
| K3 | 知识入库流水（登记/校验/人审/提交） | ✓ zip 上传+编辑 | ✓ 构建/全量重建 | **14 子命令全**（source-register→lint→approve→commit） | 无页面 | W6 技法页扩写入面（zip 不做=git 单源取舍） | 只通 CLI 没界面（已排） |
| K4 | 避坑卡（negative）+能力曲线 | — | — | knowledge/negative schema + capability_gate.py 棘轮 | /p/capability（在飞已建文件，未挂导航）+ /api/v2/capability.json 已挂 | 大合并舰把它挂进导航即通 | 已通 API没挂导航（在飞） |

### 域 5 · 工具

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| O1 | 工具注册表（启停/描述/调用统计） | ✓ /system/tools | ✓ mcp-management 139 工具 | tanyin-tools 6 子命令 + tools.lock | **/p/tools**（卡片清单+纪律标注+验签状态） | 启停钮=W3 工具卡 enabled 位 | 已通（/p/tools） |
| O2 | 供应链验签（ECDSA） | — | — | verify-lock + supply_chain | /p/tools 验签状态区 | — | 已通（/p/tools） |
| O3 | 工具执行审计 | ✓ /function/tool-exec + commands | ✓ mcp-monitor 八态 | timeline 全事件 + trace_search | **/p/guard + /p/llm-recordings** | — | 已通（/p/guard） |

### 域 6 · 引擎

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| G1 | 战士执行循环（领意图/心跳/停滞重生） | ✓ planner/worker | ✓ 四编排+16 Agent | **python3 -m cli.warrior** + tanyin-runner | /session + /console/live 观察（无引擎操控页） | 引擎操控=W5 常驻规划者 | 已通（观察面） |
| G2 | 阶段门（九门断言/干跑/恢复） | — | ✓ workflow 画布+checkpoint | tanyin-phases 8 子命令 | /console/live 门灯 + /p/report-center | 编排只读图=W6 | 已通（/console/live） |
| G3 | 预算三维执法 | — | ✓ max_iterations 一维 | budgetctl enforce/rate（token/requests/hours 三元组） | /console/live 预算烧速+预警线 | — | 已通（/console/live） |
| G4 | C2 六件+WebShell 登记 | ✓ — | ✓ c2-* 六视图+webshell | **cli/c2 包**（beacon/queue/webshell/echo/families+哈希链账本）+guard 全门链 | 无台账页 | W6 C2 台账页只读投影（B:K2 已排） | 只通 CLI 没界面（已排 W6） |
| G5 | 复测常驻岗 | ✓ retester 独立会话 | ✓ 复测按钮 | tanyin-replay（机械重放三态+REPLAY_CAP=3） | **/p/retest** + finding-detail 重放史 | 常驻岗自动排队=W5 | 已通（/p/retest） |
| G6 | 进程资源上限（内存/CPU/进程数） | — | ✓ processguard 256proc/2GB | 无（killpg+env 白名单有） | 无 | B:G2 已排 W2（resource.setrlimit） | 全缺（已排 W2） |

### 域 7 · 审批

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| A1 | 待审队列+持钥裁决 | ✓ /system/intercept/approvals | ✓ hitl 四 tab | approve 命令 + approvals.tsv HMAC | **/p/approval-center + /p/approval + /console/approval** 三页 | — | 已通（/p/approval-center） |
| A2 | AI 预审（judge 语义裁决） | ✓ judge 模型 | ✓ 审计 Agent | judge_client 已建**零消费者未接线** | 无 | W2 接线（A:G3/B:F3 同件） | 全缺（已排 W2） |
| A3 | 改参放行档（review_edit） | — | ✓ 三模式之一 | 无 | 无 | W2 扩（B:G3） | 全缺（已排 W2） |
| A4 | ask 三态（转人工 pending） | ✓ ask pending | ✓ approval 挂起 | guard 两态（放行/拒） | — | W2 扩（A:B55） | 全缺（已排 W2） |

### 域 8 · 验证

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| V1 | 机械重放验证（确定性>LLM 复测） | — | — | tanyin-replay replay（三态裁决落盘） | /p/finding-detail 重放史区+立即重放 | — | 已通（/p/finding-detail） |
| V2 | 收敛判定（四条件） | — | — | converge-check | /console/live 收敛盒 | — | 已通（/console/live） |
| V3 | 评测考卷（GT 召回/误报） | — | — | tanyin-evals + capability_gate 棘轮 | **/p/evals + /metrics** | /p/capability 挂导航（在飞） | 已通（/p/evals） |
| V4 | 覆盖度（分母上锁） | ✓ planner 自扩分母 | ✓ 扫描覆盖五数 | ledger-scope-coverage + matrix-gaps | **/p/coverage + /coverage**（WSTG 矩阵） | — | 已通（/p/coverage） |

### 域 9 · 通知

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| N1 | 多渠道告警（钉钉/飞书/企微/TG/邮件/Webhook） | ✓ /system/notify 6 渠道+投递五态 | ✓ 8 机器人 | 无 | 无 | W7 框架（A:G7/B:N3：channels.tsv+notify-cli 先落账再发） | 全缺（已排 W7） |

### 域 10 · 配置

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| C1 | 任务参数配置 | ✓ /system/settings 10 卡 | ✓ settings 12 分区 | goals.tsv + amendment 语义（配置在账本=设计取舍） | **/p/settings**（账本参数读写面+POST） | — | 已通（/p/settings） |
| C2 | LLM 通道管理/观测 | ✓ /system/llm 18 字段+轮询 | ✓ AI 通道管理 | llmpool 判定核（分道冷却/抖动/熔断） | **/p/llm-status + /p/llm-recordings**（观察面） | profiles 管理面=W6；实链 sidecar=W2 | 已通（观察面） |
| C3 | 拦截规则面 | ✓ /system/intercept 规则编辑 | ✓ tool_guard RE2 编辑 | DENYLIST 单源 + guard 六类 REJECT | **/p/guard**（规则只读+命中） | 规则编辑=纪律单源取舍（只读面已通） | 已通（/p/guard 只读） |
| C4 | 系统观测/日志 | ✓ /system/logs | ✓ audit 三账 | timeline 只增律 | **/activity + /p/system** | — | 已通（/activity） |
| C5 | 多用户 RBAC | ✓ JWT 全覆盖 | ✓ 四档 72 权限 | 双钥分权（OPERATOR/APPROVAL）+authz_matrix | 登录壳已通（/login） | W7 三角色 RBAC | 已通（单操作员+双钥） |

### 域 11 · 其他对照件（并集补全，不属十域但掌门问「所有能力」）

| # | 能力 | ARTEX 有 | CSAI 有 | 我们原有 CLI | 我们界面现状 | 缺口动作 | 判词 |
|---|---|---|---|---|---|---|---|
| X1 | 对话指挥（介入/问答/附件） | ✓ /chat 全家 | ✓ 02 对话主入口 | /api/battle/say 指令通道 | **/p/anchored-chat**（锚定问答）+ /p/broadcast（播报/介入） | 多会话/@引用=W6 规格 | 已通（/p/anchored-chat） |
| X2 | 资产库+图谱 | ✓ /function/assets 六类卡 | ✓ asset-library 20 字段 | add-asset/add-edge/graph-* 族 | **/p/asset-registry + /p/assets + /console/graph + /graph** | DSL 搜索=W6 | 已通（/p/asset-registry） |
| X3 | 报告中心 | ✓ 报告页签渲染 | ✓ — | report_render 九段+SARIF+签发面 | **/p/report-center**（列表/详情/重渲染） | — | 已通（/p/report-center） |
| X4 | 工作区文件 | ✓ /function/workspace | ✓ 文件管理 | battle 目录+report download | **/p/workspace**（目录树+下载） | 上传哈希入链=W6 补 | 已通（/p/workspace） |
| X5 | OSINT 空间测绘（FOFA/ZoomEye/Shodan/Quake） | — | ✓ info-collect 四步向导 | 无 | 无 | W3 测绘向导（B:B3） | 全缺（已排 W3） |
| X6 | 网络搜索源（ddgs/brave/tavily） | ✓ 四源 | ✓ — | 无 | 无 | W3 web-intel 工具卡（A:B63） | 全缺（已排 W3） |
| X7 | VL 视觉分析（截图研判） | — | ✓ analyze_image | 无 | 无 | W3 VL 工具卡（B:M1） | 全缺（已排 W3） |
| X8 | 外部同步（ScopeSentry 等） | ✓ /function/sync | — | zhulong-export（反向已有） | 无导入面 | W7 可选适配器 | 声明取舍+已排 |
| X9 | 浏览器/Burp 桥 | — | ✓ 插件+扩展 | 无 | 无 | W7 可选（B:N2 流量第四源） | 全缺（已排 W7 可选） |
| X10 | MCP 联邦（server 出口/外部接入） | ✓ /system/mcp | ✓ mcp 双件 | dsh 插件 10 工具（platform/dsh-plugin-tanyin） | 无 | W7 可选 mcp.toml | 声明取舍+已排 |

---

## 二 · 判词汇总

| 判词 | 件数 | 说明 |
|---|---|---|
| 已通（带路由） | 32 | 含本次三修补齐的三件：T3 任务行内操作、F1 发现总览强化、K2 卡详情深链（修后入列） |
| 只通 CLI/API 没界面（东西丢了！） | 4 | F4 发现补录表单、K3 知识入库流水、K4 capability 页挂导航（在飞件）、G4 C2 台账——前三 W6 在册、后一 B:K2 已排 |
| 全缺 | 11 | 全部在 A/B 舰缺口清单已排波次（W2×4/W3×3/W6×1/W7×3），无一悬空 |
| 声明取舍（对等策略） | 3 | E3 MITM 不解密不做、X8/X10 外部同步与 MCP 联邦的协议面与优先级 |

**掌门问的直接回答**：原有 CLI 实现改造成界面这件事，主体已经发生（49 基名账本命令+19 入口中，页面已覆盖任务/发现/证据/知识/工具/引擎观察/审批/验证/配置九大域的读面与五个写路径），50 件并集对照里 32 件已通；但有 **4 件「东西丢了」级缺口**——本次当场修掉最痛三件（发现总览一眼看到漏洞、任务闭环不留死钮、知识卡深链直读，修后 T3/F1/K2 已入「已通」），其余（补录表单、入库流水面、C2 台账页、capability 挂导航）在 W6 波次在册。

## 三 · 本次三修（代码实施，TDD）

| 修 | 页面/模块 | 内容 | 测试 |
|---|---|---|---|
| ① 发现总览强化 | cli/webui/console.py findings_view + static/console_findings.html | 顶部严重度分布条（高/中/低/未分级堆叠条+计数）+ 验证状态计数（已验证/待验证/已失效）+ 表默认按严重度排序（高→中→低，CVSS 分决胜）+ 点行进 /p/finding-detail?id&goal + 证据徽章快览抽屉（保留 GL.drawer 钉）+ 知识库入口前置（技法库链接+漏洞类引用深链） | tests/test_console_findings_overview.py |
| ② 任务管理闭环 | static/pages/tasks.html | 行内操作列：启动(launch)/暂停(pause)/恢复(resume)/结算停跑(stop 二次确认)——全部走既有 /api/battle/control（server.py 零碰）；新建任务直达既有 /p/new-task | tests/test_webui_task_actions.py |
| ③ 知识库深链 | static/pages/techniques.html | ?id=CP-xxxx 直读卡详情六节 + ?q= 预填搜索 + 选中同步地址栏（history.replaceState） | tests/test_webui_techniques_deeplink.py |

契约遵守：server.py/api_pages.py **零碰**（导航归大合并舰；三修全部页面内强化+console.py 投影扩列）。

## 四 · 方法论备注

- 「已证伪」按仓内 ui-copy-standard-v1 规范词记「已失效」（三态=已验证/待验证/已失效，tests/test_console_ui.py:594 钉）。
- 严重度分布条的口径=findings.impact（账本真实列，高/中/低），CVSS 分只作排序决胜（无向量=不虚构分，待评定律）。
- 本表判词与 A/B 舰 2026-10-18 对齐档的差异=A/B 舵以「波次排期」为判词底座（已排=有 wave 名），本表按掌门问法以「界面今天是否可点」为准——故 A 舟多件「已排 W6」在此记「只通 CLI 没界面」。

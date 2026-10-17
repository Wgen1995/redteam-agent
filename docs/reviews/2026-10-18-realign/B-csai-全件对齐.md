# B · CyberStrikeAI（CSAI）全件对齐（逐件表）· 2026-10-18 重对齐

> 执笔：重对齐子代理 B（域=CSAI 全面）。纪律：语料与代码只读，唯一写入=本档。
> 对手语料：`docs/research/manuals/usage-guide-csai.md`（下称**手册**，422 行全文通读）、`docs/research/liveui/walk-csai-live.md`（下称**活访**，146 行全文）、`docs/research/engine-parts-artex-csai-multica.md` B.2（:116-171，下称**部拆**）；源码实读=CyberStrikeAI checkout（`ai-assisted-security-verification-platform/CyberStrikeAI`）：config.example.yaml 关键段行号、`tools/*.yaml`=**90 张**、`roles/`=**13**、`skills/`=**23**、`agents/`=**16 .md**、`internal/`=**41 模块**（c2/workflow/vision/hitl/toolguard/processguard/knowledge 全在）、`plugins/`=Burp+浏览器扩展、`mcp-servers/`=2 示例、`web/static/js`=82 模块（手册:290 称 84，实数 82）。
> 我方仓：`/Users/wgen/redteam-agent`（下称**仓**）。波次基线：蓝图=`docs/design/exceed-blueprint-2026-10-17.md`（W1-W8=蓝图:22-29；§四b=蓝图:39-65）。初表=`docs/reviews/2026-10-17-exceed-review/10-五产品逐件基线总表.md`:6-35（CSAI 30 视图三档判词——本档 §〇 校对）。开工令=git 419eecf（2026-10-17：**C2/WebShell 批做·法律件用户已拍**·工期周计·webui 栈=Vue3 投影面·W1 三舰并行）。
> 判词四档：**已超**（超越点实打实）/ **已排**（波次有名）/ **声明取舍**（对等策略，用户知情）/ **真空白**（不许留，发现即给方案）。
> 一句话总判：**CSAI 是五家里「面铺得最全的成品」——30 视图全在、能力中心（139 工具/23 技能/16 Agent/13 角色/72 权限 RBAC/RAG 全参）真跑得动，治理靠 tool_guard+HITL+RBAC 三闸；我们是「一根更硬的脊柱（哈希链/三层执法/机械重放/清理门/预算三维）长在更短的腿上（Web 9 页 vs 30 视图、引擎常驻 3 成、能力中心零页面、C2/WebShell/视觉/RAG 观测零代码）」。逐件 68 行对齐后（混合判词行按主判词计）：已超 25 件、已排 33 件、声明取舍 4 件、真空白 5 件（全部给出方案并入波次）+已有等价 1 件——一件不悬空。**

---

## 〇 对初表（10-五产品逐件基线总表）的校对

初表（:6-35）30 行方向正确，但按运行时行为与开工令核后有 **9 处须修正**：

| # | 初表原判 | 校对结论 | 证据 |
|---|---|---|---|
| C1 | 00 登录「已超(锁定+审计)」 | **不准确**：登录锁定+HttpOnly 确有（server.py:24-25）；但 **WebUI 读面零鉴权**——9 页 HTML+state/matrix/graph/evidence/session/metrics 六 API+`/api/stream` SSE 全不做会话校验（会话校验只挂写路由 server.py:358-359 与 `/api/approval` server.py:678）。「已超」下调为「已排 W1 P0」 | 仓 cli/webui/server.py:255-292 vs 手册:56-59（A 舰 G1 同源发现） |
| C2 | 02 对话「无Web面」 | **不准确**：写路径已存在——`/api/battle/say` 指令通道（指令文件+timeline 留痕）；缺的是「对话页」与 会话列表/计划面板/附件/多会话切换 | 仓 server.py:615-644 vs 手册:68-72 |
| C3 | 12/13-18 C2/WebShell「声明取舍·W7 可选」 | **已过时**：开工令 419eecf（2026-10-17）用户拍板「C2/WebShell 做」——判词从「声明取舍」升级为「**已排（批做·法律敏感标注）**」，本档 §K 给落地设计与正式波次归属（本档 G1） | git 419eecf（docs/HANDOFF.md 2026-10-17 节）vs 手册:128-142 |
| C4 | 11 工作流「phases九门(代码)」 | **漏了干跑超越点**：干跑口径已冻结=零对外请求+verify-chain PASS 判定（PROTOCOL.md:38）——CSAI 的 dry-run 是「输入消息试跑」按钮，我们是执法口径，被初表埋没 | 仓 phases/PROTOCOL.md:38 vs 手册:124-126 |
| C5 | 初表无「四种编排」机制行 | **缺一族**：eino_single/deep/plan_execute/supervisor 四编排（手册:196-204）与 16 Agent/13 子代理派单交接（部拆:118-120）是机制件，不进 30 视图表就没对齐面——本档 §E 补 4 件 | 手册:196-204；部拆:118-120 |
| C6 | 初表无「三防线/上下文工程/进程隔离」行 | **缺一族**：token/挂死/熔断六防线+上下文工程五件+进程隔离（手册:206-219）是 CSAI 文档 §3 的主菜——本档 §G/§H 补 11 件（其中进程资源上限=真空白，本档 G2） | 手册:206-219 |
| C7 | 28 RBAC「单操作员」 | **漏了已有底牌**：双钥分权雏形已在——OPERATOR_KEY 管写操作 vs APPROVAL_KEY 管审批（server.py:24,30；审批签名 HMAC server.py:678-732，钥只进子进程 env）——执行/审批分离是我们今天就能出示的 RBAC 半件 | 仓 server.py:24,30,678-732 vs 手册:180-181 |
| C8 | 03 HITL「审批卡」 | **漏了两件**：①ask:human 双向问答通道已在（runner:282-299，问题在场=WAIT 停表不停命）；②judge 预审投资（judge_client.py:1-16 fail-closed）零消费者未接线（A 舰 G3 同件）；③review_edit 改参放行档无（本档 G3） | 仓 cli/tanyin-runner:282-299；judge_client.py:1-16 vs 手册:74-78 |
| C9 | 20/21 MCP 两件「声明取舍(插槽制)」 | **关系没接上**：插槽制的物质基础=W3 工具卡 25 张+tools.lock ECDSA 验签（蓝图:24；supply_chain.py:1-8）；取舍只应声明「MCP 联邦/出口协议面」，工具启停面应挂 W3/W6——初表把两件事混成一个取舍 | 仓 supply_chain.py:1-8；蓝图:24 vs 手册:158-161 |

---

## 一 · 30 视图逐件表

### A. 登录层+工作台区（6 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| A1 | 00 登录：表单+admin 初密只展一次+12h 会话+失败 IP 节流 60s（手册:56-59） | login.html+POST /login：TANYIN_OPERATOR_KEY 缺省随机+banner、HttpOnly cookie、错 5 锁 60s（server.py:24-25,363-366,447-484）；**读面零鉴权**（见 C1） | 读面=大；凭据形态=我们更安全 | 读面全路由挂 `_session_ok()`+401 跳转（A 舰 G1 同件并入）；/setup 三步向导+滚动条款闸（A 舰 G14）；会话时长=账本参数化（amendment 语义） | **W1（P0）**+W6 | 已排（初表「已超」下调；锁定+HttpOnly 保留为超点） |
| A2 | 01 仪表盘：六段式（5 KPI 卡/严重度分布+加权风险分/最近漏洞事实双 tab/C2 快捷卡/批量队列+工具 Top10/事件流+能力总览）（手册:63-66） | home 九门灯+预算三卡+KPI 五数（A 档 2c:79 引）；metrics 页双臂召回（A 舰招牌页） | 中（Token 7 天/工具成功率/风险分三卡无） | W6 仪表盘经济学（蓝图:27）：补「发现四级/资产计数/Token 三段」三卡（A:B1 同源）；加权风险分=CVSS×资产价值双轴公式已在（cvss.py:4；FD 双轴 specs）——它的 10.5 是拍脑袋加权，我们的分可复算 | W6 | 已排 |
| A3 | 02 对话：主作业入口+会话设置（agent-mode/hitl-mode/敏感工具/角色/模型五选择器）+附件+计划面板（手册:68-72；活访:2.1A） | `/api/battle/say` 指令通道（指令文件+timeline 双落，server.py:615-644）；无对话页 | 页面=大；通道=已有 | W6 介入对话页（蓝图:39 §四b 已立）：每 battle 一线程+历史=timeline actor=人工 行回放；会话级 HITL/模型选择器=battle 参数面（A:G12 子件：@引用/附件/btw/IME） | W6 | 已排 |
| A4 | 03 人机协同：审批方切换（人工/审计 Agent）+四 tab+全局白名单并集+决策留审计 90 天（手册:74-78；活访:2.3A） | /api/approval 待审投影（须会话）+HMAC 持钥审批+approvals.tsv 7 列（server.py:646-733）+ask:human 双向通道（runner:282-299）；AI 预审=judge_client 建好未接线 | AI 预审=未接线；review_edit=无 | W2：judge 接线为 guard ASK 前置（独立 profile，fail-closed 拒——反转它 fail_action=allow）+ask 三态（A:G3）+review_edit 档（本档 G3：审批中心可改参数回写 pending 后放行）；W6 审批中心页+审批快照/指纹组（A:B60）。**超点：审批签名入链+钥只进子进程 env（SEC-1）+超时默认拒** | W2+W6 | 已超（持钥+入链）+已排（AI 预审/review_edit） |
| A5 | 04 调用拦截 tool_guard：RE2 规则+{match} 模板+Web 保存即生效+全部规则验证（手册:80-84；源:config.example.yaml:174-187） | Tier1 guard 六类 REJECT 全落链：deny-list 双形比对（guard:142-152）+nuclei 固化（guard:159；enforce.py:288-295）+执法面只读（guard:167）+scope（guard:177）+account-grant（guard:183）+时间旅行（guard:199）+速率滑窗（guard:214） | 无 UI 编辑/自定义规则（我们的规则=纪律单源） | W6 规则只读面+规则分层 P0/P1/P2（A:B56）；「全部规则验证」等价=tanyin-canary 四档 probe（Tier0-3 本地模拟零网络，canary:15-24）——比它试匹配更硬；规则命中行已入 timeline（它不入链） | W6 | **已超（执法入链+机械验证）**+已排（只读面） |
| A6 | 05 项目管理：项目卡+七 tab+事实黑板（九类 key 前缀/三档置信度/关系边 type）+攻击路径（手册:86-90；活访:1.3） | 13 表账本=黑板本体：facts.tsv kind/置信度、edges.tsv 关系边（_EDGE_DIR 代码强制）、chain-create/advance/ls 命令族（write_cmds.py:535 起）、findings 19 列；battle=项目容器；graph 页血缘 SVG | 多客户/多项目实体=无（单机单战族） | W7 客户·项目实体+资产过授权复判（W5 跨战登记处，初表:15）；攻击路径 tab=graph 页血缘已同构。**超点：事实入哈希链+verify-chain 第三方可验（它 SQLite 改库=改史，A:J3 同口径）** | W5+W7 | **已超（防篡改黑板）**+已排（客户隔离） |

### B. 安全作业区（14 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B1 | 06 资产概览：四计数+协议分布+7/30/90 态势双折线+扫描覆盖五数（手册:94-97） | coverage 页 WSTG 矩阵+ledger-scope-coverage（分母 denominator-ready 上锁，PROTOCOL.md §4）+assets/edges 账本 | 态势时间窗=无 | 覆盖页加 7/30/90 发现趋势（数据=timeline 投影零新表）；「从未扫描/超30天未扫描」等价=matrix-gaps 消格清单（已有判定面）。**超点：分母上锁——它 planner 可自扩分母，我们分母诚实（A:B27 同口径）** | W6 | 已超（覆盖诚实）+已排（态势窗） |
| B2 | 07 资产库：20+字段+高级筛选+保存视图+XLSX/CSV 批量导入导出+合并（手册:99-103；活访:2.4） | assets/edges TSV+add-asset/add-edge/graph-neighbors 命令（registry 41 基名命令内）；无页无 DSL | 页+DSL+导入=中 | W6 资产页+DSL（初表:13；A:B42 同件：谓词复用 query_cmds，20 行文法）+批量导入（本档 G7：CSV 解析→add-asset 循环→导入回执入 timeline）+保存视图=URL 参数（URL-SSOT 同 W6 切换器） | W6 | 已排 |
| B3 | 08 信息收集：FOFA/ZoomEye/Quake/Shodan 四步向导+AI 解析语法（可编辑）+入库/批扫（手册:105-108） | 零情报源（全仓 grep fofa/zoomeye/shodan/quake 零命中）；出网管控 Tier3 egress（egress_proxy.py:1-10）+vault 凭据（vault.py:1-12 EtM v2）已备 | 大 | W3 空间测绘 OSINT 向导（蓝图:24 已排）：四源=key 进 vault+env 白名单（战士 env 摘密 runner:30-49——比它「后端代理防前端暴露」更彻底）；AI 解析弹窗改「生成语法→人工过目→落 intent 过 guard→执行过 Tier3」；结果入库=add-asset 循环+来源标 fofa/zoomeye | W3 | 已排 |
| B4 | 09 漏洞管理：五态+复测按钮+15 字段人工补录+批量导出（手册:110-114；活访:2.4） | findings 19 列+三态+双轴+P4 重放门+SARIF 仅 verified（report_artifacts.py:12-13）+replay 机械复测三态+REPLAY_CAP=3（tanyin-replay:17,39）+supersede 墓碑 | 页面=中（账本面已超） | W1 三态终审+W6 发现库页（蓝图:22,27）；复测=机械重放常驻岗 W5（REPAIRED 候选自动排队）；人工补录=W6 表单（15 字段映射 findings 列）。**超点：unverified 不入卷+确定性重放>对话分支复测** | W1+W5+W6 | **已超（真值环）**+已排（页面/终审） |
| B5 | 10 任务管理：批量队列+cron 调度+并发 1-8+batch_task_* 13 工具族+Agent 建队约束（手册:116-120；活访:2.1B） | battle.py init/launch/watch/settle 四段（battle.py:179-281）+W1 battle auto 一键链（F2 舰在航，419eecf）；无 cron/并发旋钮 | cron=小；并发=W5 | W1 auto 落地+并发=W5 多战士参数；cron=本档 G8（battle.py schedule 子命令：crontab 行+「立即执行」旗标，节奏并入 W7 夜回归）；「Agent 须用户明确要求才建队列」同律=我们的 guard 执法面天然（批量建 intent 也过 budgetctl） | W1+W5+G8 | 已排 |
| B6 | 11 工作流：七节点画布（开始/工具/Agent/条件/审批/输出/结束）+AI 自然语言创建+dry-run+checkpoint 7 天（手册:122-126；活访:2.2D） | phases.yaml 九门声明图+tanyin-phases 确定性引擎（validate/gate/restart/resume-kit/cached/rebuild-state/denominator-ready，tanyin-phases:3-6）+gateloop 臂B（python 掌节奏每门一回合，tanyin-gateloop:1-10）+**干跑口径冻结**（PROTOCOL.md:38：P0-P2 落账零对外请求，判定=timeline 无 request 事件且 verify-chain PASS） | 可视化画布=取舍；AI 生成草稿=可选后补 | W6 编排只读图（初表:17）：phases.yaml→SVG 投影+门事件状态着色（断点=账本本身，checkpoint 7 天 vs 永久链）；AI 生成草稿=W7 可选（生成的是 yaml 断言草稿，仍走 validate 门）；「审批节点」等价=ASK 三态 W2。**不搞拖拽——编排即账本（声明取舍）** | W6（+W2 审批节点） | **已超（干跑=执法口径）**+声明取舍（拖拽）+已排（只读图） |
| B7 | 12 WebShell 管理：连接登记（冰蝎/蚁剑）+批量探活+webshell_exec/file_list/file_read/file_write+manage_webshell_* 工具族（手册:128-132） | 无 WebShell 模块（仓内仅清理纪律提及：PRINCIPLES.md:390「无 webshell」核销语义）；**开工令已批做**（419eecf） | 全新件（法律敏感） | **WebShell 登记制（法律敏感标注）**：creds.tsv 加 kind=webshell（URL/密码/类型，vault EtM 加密）；webshell_exec 过 Tier1 guard 全门链（deny-list/scope/account-grant/request-ticket/revert_cmd 必填）+timeline 入链+产物落 battle 目录+P6.0 cleanup-checklist 核销（清理门已含 webshell 枚举语义）；探活=只读 HEAD 探测过 Tier3 | **W3 扩（本档 G1 正式入波）** | 已排（批做·法律敏感） |
| B8 | 13 C2 监听器：列表+创建+`c2.enabled` 总闸（手册:135） | 无 C2；**开工令已批做**（419eecf） | 全新件（法律敏感） | **账本化 C2-lite（法律敏感标注）**：监听器=goal 目录 c2.tsv（listener 行：端口/协议/回连域）+egress.acl 联动（回连域过 Tier3 白名单才可 compile）+c2.enabled 等价=guard 执法面参数（关=REJECT unknown-tool） | W3 扩（G1） | 已排（批做·法律敏感） |
| B9 | 14 C2 会话：状态筛选（活跃/休眠/离线）+误报标记+批量删（手册:136） | 无 | 全新件 | 会话=c2.tsv session 行（s_xxxx ID/心跳戳/状态）+离线判定=心跳超时（复用 watchdog 分级思想）；每次会话交互=timeline 事件（actor=c2） | W3 扩（G1） | 已排（批做·法律敏感） |
| B10 | 15 C2 任务：结果三计数+时间窗+11 类型（shell/exec/ls/download/upload/screenshot…）（手册:137） | 无 | 全新件 | **每条 C2 命令过 guard 全门链**（request-ticket+revert_cmd——A:B55 同律）——它的 C2 命令不过治理，我们的过：这是对 C2 这个法律敏感件的核心超越点；11 类型=v1 收敛 shell/exec/upload/download/screenshot 五类（文件过 battle 目录+哈希入链） | W3 扩（G1） | 已排（批做·法律敏感+治理超越） |
| B11 | 16 C2 载荷：单行 oneliner（Bash/Python/PowerShell/Curl）+Beacon 交叉编译三系统三架构（手册:138） | 无 | 全新件 | v1=oneliner 生成器（三形模板+回连地址=监听器配置单源）；Beacon 编译=后置工具卡（W3 工具卡族，依赖目标系统物料）；生成动作本身入 timeline（payload-generation 事件+授权书关联） | W3 扩（G1） | 已排（批做·法律敏感） |
| B12 | 17 C2 事件：级别×类别（监听器/会话/任务/Payload/OPSEC）审计流（手册:139） | 无 | 全新件 | OPSEC 事件轨=timeline actor=c2（全部 C2 动作自带事件行——它事件独立成表，我们入哈希链）；W6 审批中心同族「C2 台账页」=只读投影 | W3 扩+W6（台账页） | 已排（批做·法律敏感） |
| B13 | 18 C2 流量伪装：Profile 列表+创建（手册:140） | 无 | 全新件 | Profile=beacon 参数模板（UA/Jitter/Sleep 域）——v1 单文件模板参数化即可，不追 Malleable C8 全语法；模板变更=amendment 语义 | W3 扩（G1，v1 最薄档） | 已排（批做·法律敏感） |
| B14 | 19 文件管理：四来源筛选+五种分组+上传+「复制路径贴对话」（手册:144-148） | battle 目录（产物在盘）+report download（server.py:734-747 触发 render+zip）+EV 卡 raw_request | 管理页=中 | W6 工作区页（蓝图:39；A:B44）：白名单根+目录树+下载（读盘流式）+上传 sha256 登记 timeline artifact——**超点：产物哈希入链（它上传件不入链）**；「给 AI 看文件」=路径引用已在账本语汇 | W6 | 已排 |

### C. 能力中心区（8 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C1 | 20 MCP 监控：KPI+八态枚举（含已拦截/孤儿任务）+工具 Top+趋势+90 天（手册:152-156） | timeline 全事件轨（guard REJECT/replay/llm_failover/gate 行全在）+trace_search 字面检索（防 ReDoS，trace_search.py:1-14）+metrics 页 | 执行观测页=无（数据已有） | W6「执行观测页」=timeline actor 投影+按工具聚合+状态枚举对齐（REJECT/超时/stall 即它的已拦截/孤儿）；保留 90 天取舍=只增律（A:B61 同口径）。**超点：不丢帧（它 activity 写失败即丢）** | W6 | **已超（不丢帧）**+已排（观测页） |
| C2 | 21 MCP 管理：139 工具启停+常驻徽标 49+描述模式 full/short（手册:158-161） | 无开关页；工具面=W3 工具卡 25 张（蓝图:24）+tools.lock ECDSA 验签（supply_chain.py:1-8）+DENYLIST 单源+插槽制（模型是参数不是命运，蓝图:11） | 页=无；数量=25 vs 139 | W3 工具卡（每卡 enabled 位+agents 可见性列 A:G13+guard unknown-tool REJECT 执法）+W6 注册表页（卡带纪律标注+锁版本+验签状态，蓝图:58）；描述模式=卡 short/long 双文案（同它 token 成本思路）；MCP 联邦/出口=声明取舍（N1） | W3+W6 | 已排+声明取舍（MCP 协议面） |
| C3 | 22 检索历史：RAG 观测四计数+会话/消息筛选（手册:163） | 无；知识环停转（knowledge/log.md 尾笔 2026-09-29；蓝图:7「停转18天」） | 无观测面 | W5 知识命中观测（初表:21）：knowledge/match 命中行入 timeline（actor=knowledge）+观测页投影——**命中也入链（它检索历史独立表不入审计链）** | W5 | 已排（W5 新增件） |
| C4 | 23 知识管理：构建/全量重建/添加/分类+knowledge.* 全参（embedding/检索 top_k 0.4/multiquery 4/rerank/后处理预取 20/chunk 512 重叠 50/RPM/重试/批 10/子索引）（手册:165；源:config.example.yaml:441-496） | knowledge/ 目录（graph.ndjson/retros/cve/methodology/checklists）+**14 子命令**（init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map/approvers，tanyin-knowledge:17-19）+approve 人审 | 向量检索族=取舍；环=停转待复活 | W5 知识环复活+借脑接线（注入 top-k）+蒸馏入链人审（初表:23；蓝图:26）；检索参数面=match top_k/阈值/score 门收敛为账本参数（本档 G9）；向量族不先行=声明取舍（确定性图谱+人审蒸馏——检索可复算可审计，它的向量召回不可解释） | W5 | 已排+声明取舍（向量族） |
| C5 | 24 技能状态：23 技能调用统计表+清空统计（手册:167） | timeline skill 事件可数；无页 | 小 | W6 技法页 usage 投影（A:B51 同件）；「清空统计」不做=只增律（取舍同 A:B61） | W6 | 已排+声明取舍（清空） |
| C6 | 25 技能管理：23 技能卡+创建/编辑/标签（手册:169-170；源:skills/ 实数 23+README） | .opencode/skills/tanyin/SKILL.md 53 行常驻+phases/*.md 九门路由按需加载（**常驻权威集<2000 token 预算+实测校准 ×1.116**，PROTOCOL.md:33-34）+AGENTS-INJECT <2K 护栏幂等注入（hosts_matrix.py:6-9）+knowledge/ 方法论库 | 数量=1 vs 23（内容量产在 W3） | W3 手册+VulnClaw 余 39 专题+内网横向 15 卡（蓝图:24）；zip 上传不做=git 单源（A:B51 取舍）。**超点：常驻预算是冻结契约+实测校准（它的渐进披露无预算执法）** | W3（内容）+W6（技法页） | **已超（常驻预算纪律）**+已排（量产） |
| C7 | 26 智能体管理：16 Agent .md（front matter+正文提示词）+max_iterations 覆盖+新建表单（手册:172-173） | 单战士+SKILL/P3 协议（.opencode/skills/tanyin/SKILL.md）+档位=model_tier strong/weak（write_cmds.py:344）+WARRIOR_ENV 白名单（runner:30-49） | Agent 目录页=无；多代理=W5 | W6 战士配置页（初表:25）：档位=插槽参数可视化+工具面矩阵（A:G13）；W5 常驻规划者+多战士编队（蓝图:26）。**超点：提示词在册即版本（git）+每战士 env 摘密** | W5+W6 | 已排 |
| C8 | 27 角色管理：13 角色卡（emoji+描述+工具范围+启用）（手册:175-176；源:roles/ 实数 13 YAML） | 无角色卡；职能分离=phases 分段（P1 测绘/P3 演进/P4 重放/P6 清理）+13 子代理等价=W5 意图路由（priority=severity×value×exploitability 公式，SKILL.md:30） | 角色卡面=简化取舍 | W6 并入战士配置页（初表:27）——不抄 13 卡花样，抄「提示词+工具面」打包语义（一张卡=一个档位+一个工具面）；对话页角色选择=A3 会话参数 | W6 | 已排（简化） |

### D. 平台管理区（2 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| D1 | 28 平台权限 RBAC：四档（viewer 23/auditor 24/operator 50/admin 72 权限）+资源范围显式授权+变更留痕（手册:180-181；源:docs/zh-CN/rbac.md:49-52） | 单操作员+**双钥分权雏形**：OPERATOR_KEY 管写操作 vs APPROVAL_KEY 管审批（server.py:24,30；HMAC 签名+钥只进子进程 env，server.py:678-732）；身份矩阵投影 authz_matrix.py:1-10（role×endpoint 覆盖——测试侧 RBAC 矩形） | 多用户=无（W7） | W7 三角色 RBAC+双人复核（蓝图:28）：操作员/审批员/审计员对齐 ZhuLong 三角色；资源范围=goal 级（battle 目录边界天然）；72 粒度不追全量（初表:29 取舍）。**超点：审批-执行分钥+approver 入哈希链（它变更留痕在库内可改）** | W7 | 已排+声明取舍（粒度） |
| D2 | 29 系统设置 12 分区：AI 通道管理（多通道/failover/推理参数）/视觉分析/Agent 参数/HITL/资产四源/知识库/C2/机器人/安全/审计/存储清理/一键更新（手册:183-190） | 配置在账本不在设置页：goals.tsv model_tier/guard_tier/rate_limit/budget 三元组（write_cmds.py:305-344）+amendment 语义；AI 通道=llmpool 判定核（llmpool.py:1-49）+W1 输出契约 | 设置页=无；通道管理面=无 | W6 设置页=账本参数读写面（改动=amendment 行+因，A:B62）+W6 llmpool 管理页（profiles 表 A:B45）；存储清理=分类保留期并入 A:G9 扩（本档 G10）；一键更新=A:K3（ECDSA 签名版本清单——**它更新无签名验真，我们有发布者身份**）；视觉分析=M 件（W3） | W6+W7 | 已排+声明取舍（配置单源在账本） |

---

## 二 · 机制件（跨视图深读）

### E. 智能体编排（4 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| E1 | 四种编排：eino_single（ReAct 单代理）/deep（orchestrator+task 派 13 子代理）/plan_execute（规划-执行-重规划）/supervisor（transfer 专家路由）（手册:196-204；部拆:118-120） | 臂A runner 自律（单战士+心跳/停滞/续跑，tanyin-runner:1-12）+臂B gateloop（python 掌节奏每门一回合，tanyin-gateloop:1-10）+phases 确定性状态机；W5 常驻规划者 MVP+多战士编队（蓝图:26） | 常驻规划者=3 成（形态差） | W5：事件源=timeline 行增长+500ms debounce+六门前置（A:D1 同规格）；supervisor 等价=意图路由 priority 公式已在（SKILL.md:30）；**超点：编排状态全在账（重启恢复）——它 deep 编排重启丢跨唤醒链（A:D4 同口径）** | W5 | 已排 |
| E2 | 16 Agent .md+派单前目标完整性校验（URL/IP/范围/成功标准缺一禁派）+交接包（子代理看不到父对话）（部拆:120） | 任务书八问（授权/范围/预算前置）+intent 六要素+dedup_key 程序算+budgetctl enforce 前置门（budgetctl:1-6）+账本全共享（子代理等价物=intent 消费者，读同账） | 多代理派发=无（W5） | W5 多战士：派单=chain-create/intent 行（账本即交接包）；完整性校验=add-intent 的 Reject 语义扩展。**超点：派单过预算门（它派单只过提示词校验）** | W5 | **已超（派单执法）**+已排（多战士） |
| E3 | max_iterations 12000 全局+agents front matter 覆盖+plan_execute 外层循环上限（手册:385；源:config:160,324-325） | budget token;requests;hours **三元组**+intent 份额叶+REJECT budget-exhausted 零余量即拒（budgetctl:1-6）+runner 战中预算轮询 warn/enforce（runner:309-320） | 形态异（无迭代计数器——用三维预算） | 保持三维；W5 常驻规划者加轮次上限=phases round 列（已有 round 概念）。**超点：预算三维>迭代一维（token 烧完/请求打够/时窗到点三闸独立执法）** | — | **已超** |
| E4 | 角色提示词=roles/*.yaml 13 张（user_prompt+工具策略打包）（部拆:124） | phases 分段提示+SKILL 八节常驻+AGENTS-INJECT 八条（hosts_matrix.py:6-9）——提示词三层注入皆在册可审计 | 打包成「卡」=W6 简化 | 同 C8（并入战士配置页：档位×工具面=一张卡） | W6 | 已排（简化） |

### F. 治理链（5 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| F1 | tool_guard：Go RE2 规则命中即拦+{match} 模板回注（Agent 改道不崩）+与 HITL 独立（手册:80-84,221-231；源:config:174-187） | 同 A5：六类 REJECT（deny-list 双形/nuclei 固化/只读执法/scope/account-grant/时间旅行/速率）+内嵌兜底 fail-closed（enforce.py:39-75）+命中入链 | 自定义规则面=无（取舍：规则=纪律单源） | 同 A5（W6 只读面+canary 验证）；「Agent 改道不崩」同律（REJECT 回战士，guard 输出即提醒） | W6 | **已超**+已排（只读面） |
| F2 | HITL 三模式：off（白名单直行）/approval（挂起放行拒）/review_edit（改参放行）；白名单=全局∩会话并集；超时 300s（手册:76-78,221-231；源:config:189-227） | off=permitted_actions+guard 放行面；approval=approve/reject/exempted 三决策（approvals.tsv+HMAC）；ask:human 双向通道（WAIT 停表）；**review_edit 无** | review_edit=真空白 | G3：审批中心改参档——待审行可编辑 args 回写（改参行入 timeline amendment 语义）后放行；超时语义=我们不限时挂起（fail-closed 等人工——比它 300s 默认放行歧义安全，声明取舍） | **W2 扩（G3）** | 已超（approval 形态）+真空白（review_edit）→已给方案 |
| F3 | 审计 Agent：openai 小模型/typesafe Jev 结构化放通（六问政策 reject 0.55）+独立提示词两套（手册:76-78；部拆:135；源:internal/hitl/jev.go:13-22） | judge_client 已建：temp=0/单轮/token 级严格解析/fail-closed (None,reason)（judge_client.py:1-16）——**零消费者未接线** | 接线=真空白（A:G3 同件） | W2 接线：guard ASK 前置（规则未命中+高危特征→judge 裁决，None=拒——反转它 fail_action=allow）；独立 profile（不与战士同模型）；lane 计量=budget.tsv scope=judge 行 | **W2（A:G3 同件）** | 真空白（接线）→已给方案 |
| F4 | RBAC 四档 72 权限+资源范围+MCP 工具内二次检查（手册:180-181；rbac.md:34-38） | 同 D1：双钥分权+authz_matrix 投影+goal 级资源边界 | 多用户=W7 | 同 D1 | W7 | 已排 |
| F5 | 审计三账：操作 15 天/工具执行 90 天/HITL 决策 90 天+诊断日志 14 天（手册:236,403） | timeline 只增律（永不清理，写入单源 timeline.py:1-14 哈希链）+runner/guard 各自日志轨 | 保留期治理=取舍（只增） | 声明取舍：审计不清理（法证立场）；冷数据=归档（A:G9 tar+zstd+manifest）+分类保留期参数（G10 并入 A:G9） | W6（A:G9 扩） | 声明取舍+已排（归档） |

### G. token/挂死/熔断三防线（6 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| G1 | 渐进披露：tool_search 工具≥20 时 12 常驻+45 白名单，余按需解锁（手册:207） | SKILL.md 常驻<2000 token（冻结契约+实测校准，PROTOCOL.md:33-34）+九门 phases/*.md 路由按需加载+AGENTS-INJECT <2K 护栏（hosts_matrix.py:6-9） | 形态异（它管工具描述，我们管全部知识注入） | 保持；W3 工具卡 25 张时卡描述进常驻预算同律（卡 short 文案+预算复核）。**超点：常驻预算有执法（lint FAIL）有实测校准（×1.116），它无预算执法** | — | **已超** |
| G2 | 输出兜底 reduction：>100KB 全文落盘留预览+历史工具结果 60000 tokens 清理+DB 与 Agent 同一份（手册:208） | EV 卡 raw_request 落盘+大产物 battle 目录+trace_search 字面检索（防 ReDoS 无 regex 引擎，trace_search.py:1-14）——哲学=「检索代携带」不搬大输出进上下文 | 截断机制=宿主职责（opencode 自管） | 声明取舍（不复制 reduction 中间件——账本哲学：证据落盘可检索）；W6 工作区页产物哈希补强 | W6 | 声明取舍+已超（检索面防 ReDoS） |
| G3 | 异步等待：阻塞调用交 worker，300s 到时返 execution_id，wait/cancel_tool_execution 续等取消，孤儿任务可见（手册:209,154） | guard --timeout 通道（缺省 60s 上限 600s，guard:292,350）+runner 30s 心跳轮询+watchdog 分级 | 续等语义=真空白（W5 规格补点） | W5：intent 执行态加 execution 列（running/waiting/done）+CLI wait 子命令（轮询账本非进程）+取消=set-intent-status voided+runner 宽限 | **W5（规格补点，本档 G5）** | 真空白→已给方案 |
| G4 | 熔断与并发：单 server 5/全局 16/连续失败 15 次熔断 60s（手册:210；源:config:163-166） | LLM 侧=llmpool 分道冷却（429 短道 1min/服务器长档 1/5/30min）+±20% 抖动+硬熔 1 次即熔（llmpool.py:30-49）——**A 舰点名的两处改进它没有**；工具侧=rate 滑窗（enforce.py:172 + goals.rate_limit 申报制）；外部 MCP 熔断=无（无外部工具面） | 外设熔断=随 W3 插槽 | W3 工具卡族参数：每卡 rate+circuit（复用 llmpool 分道思想+enforce.rate_window 单源）；并发=guard 执行位 semaphore | W3（本档 G4） | 已超（LLM 熔断分道+抖动）+真空白（外设熔断）→已给方案 |
| G5 | 防挂死：shell_no_output_timeout 1200s 连续无输出终止+tool_timeout_minutes 60（手册:211） | watchdog 四机制：soft 3min 观察/hard 8min 击杀/指数退避 4^n 封顶 480s/死亡续跑 max 5（runner:175-179；watchdog.py:1-12）+guard timeout 60/600 | 形态异（更细） | 保持。**超点：分级观察+退避+续跑三件套>单超时击杀；停滞事件入 runner 日志轨** | — | **已超** |
| G6 | 进程隔离 processguard：Windows Job Object/Unix watchdog/Linux cgroup，max_processes 256/内存 2GB/CPU 配额，隔离失败拒绝执行 fail-closed（手册:212；源:config:404-424） | 进程组 SIGKILL（runner:90-95 killpg）+ISOLATION_ENV 四开关（runner:24-28）+WARRIOR_ENV 白名单摘密（runner:30-49）；**资源上限（内存/CPU/进程数）=零** | 资源上限=真空白 | **G2（本档）：stdlib resource.setrlimit 在 guard exec/inject 位统一施加**——RLIMIT_AS（内存）/RLIMIT_NPROC/RLIMIT_CPU，参数=goals 新列（amendment 可调）；施加失败=REJECT（fail-closed 同律）；cgroup/JobObject=部署文档可选档（Linux 手册页给出 systemd Delegate 配方）。~200 行 | **W2（引擎地基扩）** | 真空白→已给方案 |

### H. 上下文工程（5 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| H1 | summarization：上下文 0.8×max 触发压缩+输出预留 40960（手册:215） | 阶段制短会话（P1-P6 各自短会话）+**受管重启**：上下文≥75% 或≥10 轮→restart --spawn auto（护栏：计预算/10min 速率上限/单活跃会话锁，SKILL.md:47）+恢复协议（RESUME_PREAMBLE 重读任务书，runner:56-58） | 形态异（重启代摘要） | 声明取舍+超点：重启=账本为记忆（压缩有损，账本无损）；W5 常驻规划者长会话需 digest 补件（A:G6：digest fact 入账） | W5（A:G6） | **已超（形态）**+已排（digest 补件） |
| H2 | 用户意图账本：压缩后注入原始输入与约束（≤96000 字符，单条≤16000）（手册:216） | 任务书文件制+goal 行+续跑必重读全文（RESUME_PREAMBLE，runner:56-58）+goal digest 注入 | 等价已有（形态异） | 保持——初心=任务书重读（比注入摘要强：全文重读零损耗） | — | **已超** |
| H3 | 超长本轮输入：>48000 字符落盘只注头尾各 24000（手册:217） | 任务书=文件（无长度限制；任务书是法不截断）；战中指令=directive 文件通道 digest 触发（runner:272-280） | 0（取舍） | 声明取舍：不截断——授权要件/范围声明截半=法证事故 | — | 声明取舍 |
| H4 | plan_execute 预算：user_input 35%/executed_steps 20%/每步≤4000 runes/最近 8 步（手册:218；部拆:134） | budgetctl 三元组+intent 份额+每步=阶段短会话；W5 规格需步预算 | 步预算=W5 规格 | W5 常驻规划者 MVP 规格：意图结果入账摘要化（E-index 行）+最近 N 步进 prompt（N=账本参数）；4000 runes 上限=EV 卡摘要列同律 | W5（规格补点） | 已排 |
| H5 | patch_tool_calls：流式中断的悬空 tool_call 历史修补（手册:219） | 宿主职责（opencode 会话完整性）+我们无自管流式历史 | 0（取舍） | 声明取舍：不自建会话内核即无此 bug 面；账本行原子写（filelock+整替换）无中间态 | — | 声明取舍 |

### I. RAG 知识库（4 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| I1 | 检索链：MultiQuery 改写上限 4+rerank（gte-rerank）+后处理预取 20+子索引过滤（手册:165；源:config:441-470） | knowledge/match/neighbors/nday-match 确定性检索+score 门（14 子命令内，tanyin-knowledge:17-19） | 向量族=取舍 | 声明取舍：确定性图谱检索先行（可复算可审计）；向量召回=可选插槽（W3 工具卡参数位，不做核心依赖） | W5+W3 可选 | 声明取舍+已排 |
| I2 | 索引：chunk 512/重叠 50/RPM 限速/重试 3/批 10/优先源文件（手册:165；源:config:472-496） | knowledge 流水=source-register→lint→**approve（人审）**→commit（tanyin-knowledge:17-19）+format_version+staging 区 | 自动化=低（人审=设计） | 保持。**超点：蒸馏入链人审（它 chunk 无审计——知识投毒面它开着，我们 approve 闸关着）** | W5 | **已超（人审闸）** |
| I3 | embedding provider/model/base_url/key 独立配置（手册:165） | 无 VL/embedding 通道；插槽制=模型是参数（蓝图:11） | 通道=随 M/G6 | W3 工具卡参数位（provider/model/base_url 进 vault，key 不进战士 env——同 runner:30-49 摘密律） | W3 | 已排 |
| I4 | 检索历史观测（=视图 22）（手册:163） | 同 C3：无；W5 命中入 timeline | 同 C3 | 同 C3（命中行入链——超点） | W5 | 已排 |

### J. 技能与工具资产（3 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| J1 | 23 技能（AD 域攻/AI LLM 攻/侦察/逆向/区块链/云/0day…）（手册:169；源:skills/ 实数 23） | 同 C6：SKILL 常驻+九门路由+knowledge 方法论 | 数量差（W3 量产补） | 同 C6（W3 手册+VulnClaw 39 专题+横向 15 卡） | W3 | 已超（纪律）+已排（量产） |
| J2 | 90 张 YAML 工具配方（nmap/sqlmap/nuclei/msf/hashcat/bloodhound/trivy…未装自动跳过）（部拆:123 实数 90；手册:160） | tools.lock ECDSA 验签+DENYLIST+engines/ 四引擎（nuclei adapter 固化 -rl 50 -etags dos,intrusive，engines/nuclei/adapter.py:156-161）+工具卡 W3 25 张 | 数量=25 vs 90 | W3 工具卡 25+横向 15+VulnClaw 39（蓝图:24）≈79 张带纪律标注；**超点：卡带 ROE 标注+版本 sha256+ECDSA 验签+调用固化参数（它 YAML 无签名无纪律标注）** | W3 | 已排+**已超（供应链锁定）** |
| J3 | Skills 渐进式按需加载（模型先见简介，skill 工具拉全文）（手册:170） | 同 G1：常驻预算+门路由（PROTOCOL.md:33-34） | 同 G1 | 同 G1 | — | **已超** |

### K. C2/WebShell（2 件汇总，法律敏感）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| K1 | WebShell 全家（=视图 12）：登记/探活/四工具+管理族（手册:128-132） | 无；开工令批做（419eecf）；清理门已含 webshell 核销语义（PRINCIPLES.md:390） | 全新件 | 同 B7：**登记制+vault 凭据+全门链执法+cleanup 核销**——它的 webshell_exec 在常驻白名单（手册:186 白名单单列 manage_webshell_list），我们的 exec 过 guard 六门+request-ticket+revert；授权范围=授权书挂账（W1 授权真上传联动） | **W3 扩（G1）** | 已排（批做·**法律敏感**：仅自有/书面授权目标，授权书覆盖后渗透动作） |
| K2 | C2 六视图全家（=视图 13-18）：监听器/会话/任务/载荷/事件/流量伪装，产物 tmp/c2 30 天（手册:134-142） | 无；开工令批做（419eecf） | 全新件 | 同 B8-B13：**账本化 C2-lite 六件**——每命令过 guard 全门链+OPSEC 事件入链+回连域过 egress.acl+产物保留并入归档（G10）；页面=W6 台账页只读投影；Beacon 编译后置工具卡。**核心超越叙事：它的 C2 是「攻击基建自由区」，我们的 C2 是「每个动作都有 request-ticket+revert_cmd+哈希链的受治理后渗透」** | **W3 扩（G1；Beacon/W6 台账页分别后置）** | 已排（批做·**法律敏感**） |

### L. 工作流引擎（1 件，=视图 11 机制面）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| L1 | 工作流引擎：internal/workflow 节点图调度+断点续跑 7 天+审批节点嵌 HITL+导入 zip 包（手册:125；活访:2.2D） | phases.yaml 断言协议（exit.assert→命令返回值判定，唯一确定性执行体 tanyin-phases gate）+幂等（already-passed）+前置门检查（PROTOCOL.md §1） | 可视化=取舍；AI 生成=W7 可选 | 同 B6：W6 只读图+审批节点=W2 ASK；断点=账本（checkpoints.tsv 已有命令）。**超点：门事件 gate-exit/gate-fail 入链可验，它 checkpoint 在文件 7 天过期** | W6+W2 | **已超（干跑+断点即账本）**+声明取舍（拖拽） |

### M. 视觉分析（1 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| M1 | analyze_image：VL 单次调用+上下文只留文字摘要+原图≤5MB/长边 2048/JPEG q82/编码后≤512KB/超时 60s（手册:238-239；源:internal/vision/{client,preprocess,tool}.go） | 零视觉（全仓 grep vision/VL 零命中） | 真空白 | **G6（本档）：VL 工具卡（W3 工具卡族）**——截图/图片→VL 通道（独立 provider 参数进 vault）→文字摘要入 EV 卡+图片 sha256 登记 timeline artifact+原图不进上下文（同它哲学）+出网过 Tier3 egress；预处理=长边缩放+JPEG 质量参数（卡参数化）。靶场截图研判/验证证据拍照归档两用 | **W3（本档 G6）** | 真空白→已给方案 |

### N. 集成面（4 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| N1 | MCP 出口：http server 127.0.0.1:8081+X-MCP-Token/用户 Bearer+stdio 模式+外部 MCP 联邦（http/stdio/SSE）+2 示例服务端（手册:242；源:mcp-servers/） | DSH 原生插件 10 条账本命令工具化（platform/dsh-plugin-tanyin/README.md:1-5，v0.2 agent tool 面待接线）+反向互通 zhulong-export（findings 推出，zhulong_export.py:9-16 契约实勘） | MCP 协议面=取舍 | 声明取舍：不开放 MCP server（插件+导出=双通道等价）；外部工具接入=W3 插槽（工具卡）——**超点：外部工具过 guard 同律（它外部 MCP 过它熔断但 MCP server 本身是攻击面）**；W7 可选 mcp.toml 适配（A:B50） | W7（可选） | 声明取舍+已排（可选） |
| N2 | Burp Suite 插件+Chrome/Edge DevTools 扩展（流量回传 AI 辅助测试）（手册:243；源:plugins/） | 无浏览器/Burp 桥（Tier3 egress 有 CONNECT 隧道但不解密 TLS——A:B39 声明） | 真空白（W7 可选档） | **G11（本档）：DevTools 扩展回传=流量第四源**——扩展抓 fetch/XHR 元数据（URL/状态/时序，不含 body——零 TLS 解密合规）POST 回 webui→EV 卡 traffic_ref 列；与 W6 三源回传（A:B39）联动；Burp 桥=同协议位。**不做 MITM CA（客户环境截 TLS=合规雷，与 A 舰 B39 同口径）** | **W7（可选，优先级声明：三源回传先行）** | 真空白→已给方案（W7 可选） |
| N3 | 8 渠道机器人（企微/钉钉/飞书/TG/Slack/Discord/QQ/个人微信）+漏洞告警推送+每消息走编排（手册:244,189；源:config:497-） | 无任何通知渠道（A 舰 G7 已列 W7 框架） | 大（A:G7 在册） | A:G7 同件扩：channels.tsv+notify-cli（先落 timeline 再发）+deliveries.tsv 五态；本舰补：CSAI 独有 QQ/个人微信=可选位（协议不稳法律灰，默认不排）；告警谓词=发现四级/gate-fail/预算 80%（同它漏洞告警） | **W7 扩（A:G7）** | 已排 |
| N4 | API 文档页（页头入口 web/templates/api-docs.html）+REST 全量文档（手册:245） | README/USAGE/cli/README+**contracts/ 编号契约**（01-ledger-schema/02-commands/…，仓 contracts/ 目录）——契约文档=API 真源 | 形态异（取舍） | 声明取舍：契约文档在册即 API 面（双面一等公民 A:C-1）；W6 各页 API 随页增长；对外 openapi.json=W7 版本面可选（ZhuLong 导出对齐） | — | 声明取舍 |

### O. 数据与存储（3 件）

| # | CSAI 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| O1 | SQLite 双库：conversations.db+knowledge.db（可独立复用）（手册:234） | 13 TSV+哈希链+filelock+原子整替换（schemas.json 13 表；timeline.py:1-14 单源写方） | 形态取舍（A:J1 同口径） | 声明取舍：账本=法（可签名可第三方验）；跨战透视若慢→只读 sqlite 投影层（不换真源） | 可选（W7 附带评估） | 声明取舍 |
| O2 | 运行空间目录族：tmp/workspace 按项目/会话隔离+reduction+c2+uploads+workflow-checkpoints+诊断日志（手册:235） | battle 目录=作战单元（~/.tanyin/battles/battle-N）+报告产物+E-index+runner 日志轨 | 等价已有（单目录族 vs 多目录族） | 保持单容器（battle=项目+会话+产物一体——归档单元更干净）；分类保留期=G10 | — | 已有等价 |
| O3 | 存储清理：auto_clean+七类目录各自保留期（workspace 30d/reduction 7d/c2 30d/上传 90d…）（手册:190,235） | cleanup-checklist 清理门（P6.0 写操作全枚举核销）+归档=A:G9（W6） | 保留期参数=无（取舍：只增律） | G10（本档）：归档时按类别保留期参数（battles 产物/上传件/C2 产物/日志四类各一期）——**清理动作本身入 timeline（clean 事件+清单哈希），它清理无审计** | W6（并入 A:G9） | 已排+**已超（清理即审计）** |

---

## 三 · 判词汇总

| 判 | 件数 | 代表件 |
|---|---|---|
| 已超（主判词） | 25 | A5/A6（执法入链+防篡改黑板）、B4（真值环）、B6/L1（干跑=执法口径+断点即账本）、B1（覆盖诚实）、C1（不丢帧）、C6/J3（常驻预算纪律）、E2/E3（派单执法+预算三维）、G4（LLM 熔断分道+抖动——A 舰点名的它没有的两洞）、G5（分级观察+续跑）、G1（常驻预算执法）、H1/H2（重启代摘要+初心重读）、I2（人审闸）、J1/J2（纪律+供应链锁定）、O3（清理即审计）、A1/A4/F1/F2/G2（混合判：超点在链上/持钥/检索面，配套件另计已排） |
| 已排 | 33 | **B7-B13/K1/K2（C2/WebShell 批做·W3 扩——本档 G1 正式入波）**、B3（W3 测绘向导）、B2/B14/C5-C8/D2（W6 资产/工作区/技法/配置族）、A3（W6 对话页）、C3/C4/I3/I4/H4/E1/E4（W5 知识族+常驻规划者）、D1/N3（W7 RBAC+通知）、B5（W1 auto+G8 cron）、F4/F5/I1/N1（随波取舍联动件） |
| 声明取舍 | 4 | H3（任务书不截断——法证立场）、H5（会话内核不自建——宿主职责）、N4（契约文档即 API 面）、O1（TSV 账本律——A:J1 同口径）；另有 8 行内嵌取舍声明（B6 拖拽/C2 MCP 协议面/C4 向量族/C5 清空/D1 粒度/D2 配置单源/F2 审批不限时/G2 宿主管上下文） |
| 真空白（全部给方案，无一悬空） | 5 | **G6 进程资源上限（G2·W2）**、F3 judge 接线（A:G3·W2）、G3 异步续等（G5·W5 规格）、M1 VL 视觉（G6·W3）、N2 Burp/扩展桥（G11·W7 可选）；另 F2 review_edit 改参档（G3·W2）与 G4 外设熔断（G4·W3）为混合判中的空白半边；**C2/WebShell 代码零行已由开工令转「已排批做」（G1）** |
| 已有等价 | 1 | O2（battle 目录族=项目+会话+产物一体，形态异不立项） |

---

## 四 · 新增缺口清单（此前任何波次都没排的件——一件不许漏）

> 判据：W1-W8（蓝图:22-29）、§四b（蓝图:41-63）、初表:6-35 与 A 舰 G1-G15 逐字核对，未点名者入本清单。全部给方案与建议波次（原则：能并入现有波次则并入，不滥开新波；**不开 W9**——与 A 舰口径一致）。

| # | 缺口件 | 危害 | 方案（可施工） | 建议波次 |
|---|---|---|---|---|
| G1 | **C2/WebShell 正式入波**：开工令 419eecf 已批做，但波次表仍是「W7 可选·声明取舍」（初表:16-17）——批了没排=悬空 | 法律敏感件无波次=无验收线无纪律标注；用户已拍板却可能被静默压丢 | **W3 扩（利用深挖批）**：C2-lite 六件+WebShell 登记制（本档 B7-B13/K1-K2 方案：全门链执法+request-ticket+revert+OPSEC 入链+egress 联动+cleanup 核销）；开工令授权切片提前（监听器+oneliner MVP 可先行）；**法律敏感标注随件**（仅自有/书面授权目标+授权书覆盖后渗透动作+产物保留期）；W6 台账页只读投影；Beacon 编译后置工具卡 | **W3 扩（~2500-3500 行）+开工令切片** |
| G2 | **进程资源上限**：CSAI processguard 256proc/2GB/CPU 配额 fail-closed（手册:212）；我们 killpg+env 白名单有，内存/CPU/进程数=零 | 被俘战士 fork 炸弹/内存耗尽可打死宿主——Tier1 管行为不管资源 | guard exec/inject 位统一 resource.setrlimit：RLIMIT_AS/RLIMIT_NPROC/RLIMIT_CPU，参数=goals 新列（amendment 可调）；施加失败=REJECT（fail-closed 同律）；cgroup/JobObject=部署文档可选档 | **W2（引擎地基扩，~200 行）** |
| G3 | **review_edit 改参放行档**：CSAI HITL 三模式之一（手册:76-78）；我们只有 approve/reject/exempted | 高危参数只能在拒绝后人工重写指令，多一轮往返；审批中心少了「改一处就放行」的运营档 | 并入 A:G3 ask 三态同批：待审行可编辑 args 回写（amendment 行入 timeline）后放行；Web 审批中心+CLI approve --edit-args 双面 | **W2 扩（A:G3 一并，+~150 行）** |
| G4 | **外部工具/插槽熔断参数**：CSAI per-server 5/全局 16/连续 15 次 60s（手册:210）；我们 llmpool 只管 LLM | W3 工具卡 25 张接入后无熔断=单工具故障可拖垮战局 | 工具卡族参数：每卡 rate+circuit（复用 llmpool 分道冷却思想+enforce.rate_window 单源）；并发=guard 执行位 semaphore | **W3（工具卡族规格，~200 行）** |
| G5 | **异步执行续等语义**：CSAI execution_id+wait/cancel（手册:209）；我们 guard timeout 60/600 一刀切 | 长扫描（masscan 全网段）要么占满 guard 窗口要么失控后台 | W5 常驻规划者规格补点：intent 执行态加 execution 列（running/waiting/done）+wait 子命令轮询账本+取消=set-intent-status voided | **W5（规格补点，计入 MVP 工程量）** |
| G6 | **VL 视觉分析（analyze_image）**：CSAI 独立 VL 通道+摘要入上下文（手册:238-239）；我们零视觉 | 靶场截图/验证证据拍照无法进研判流；「眼见为实」证据类型缺位 | VL 工具卡（W3 工具卡族）：截图→VL 通道（provider 参数进 vault）→文字摘要入 EV 卡+图片 sha256 入链+原图不进上下文+出网过 Tier3 | **W3（~400 行）** |
| G7 | **资产批量导入+保存视图**：CSAI XLSX/CSV 三步导入+保存筛选视图（手册:101,103）；W6 资产页未点名 | 存量资产（客户台账）进平台只能手敲 | W6 资产页规格扩：CSV 解析→add-asset 循环→导入回执入 timeline（含跳过行+因）；保存视图=URL 参数（URL-SSOT 同切换器） | **W6 扩（~300 行）** |
| G8 | **battle cron 调度**：CSAI 队列级 cron+立即执行开关（手册:118）；我们 launch 只能手动 | 周期复测/定时巡检无物质基础（W7 夜回归只有 CI 节奏） | battle.py schedule 子命令：crontab 行+--now 旗标+调度行入 timeline（schedule 事件）；执行=到达点触发 launch（复用夜回归节奏） | **W1 auto 联动（+~150 行）/W7 节奏并入** |
| G9 | **知识检索参数面**：CSAI knowledge.* 22-23 配置域全参（手册:165；源:config:441-496）；我们 14 子命令无参数化检索配置 | top_k/阈值/子索引全靠命令行裸参，W5 复活后无管理面 | W5 复活规格：match top_k/相似阈值/score 门/子索引=knowledge/format_version 同级参数文件（amendment 语义）+命中观测页联动（C3） | **W5（规格补点，~100 行）** |
| G10 | **分类保留期参数**：CSAI 七类目录各保留期（手册:190）；A:G9 归档未分参数 | 归档一刀切；C2 产物/上传件/日志混同生命周期 | 并入 A:G9：归档 manifest 按类保留期（battles 产物/C2 产物/上传件/日志四类）——清理动作入 timeline（clean 事件+清单哈希） | **W6（A:G9 扩，~100 行）** |
| G11 | **Burp/DevTools 扩展桥**：CSAI 双插件流量回传（手册:243）；我们零浏览器桥（A:B39 只排了三源回传） | 人工测试流量与 AI 战士证据不同账；渗透师既用工具又用平台的场景断开 | W7 可选：DevTools 扩展抓 fetch/XHR 元数据（URL/状态/时序，**不含 body——零 TLS 解密**）POST 回 webui→EV 卡 traffic_ref 列=流量第四源；优先级声明=三源回传（W6）先行 | **W7（可选，~600 行）** |

---

## 五 · 波次总量修正建议

- **W2** +~350 行（G2 资源上限+G3 review_edit 并入 A:G3 ask 三态）。
- **W3** +~3800-5300 行（**G1 C2/WebShell 批做 2500-3500 行为大头**+G4 熔断参数+G6 VL 卡）——W3 原本就是最大波（~12400 行/7-9 周），C2 并入后建议拆两个并行小队（工具卡队+C2 队），工期不变或 +1 周。
- **W5** 规格补点（G5 续等+G9 检索参数面+H4 步预算——计入常驻规划者 MVP 工程量）。
- **W6** +~400 行（G7 导入+视图+G10 保留期并入 A:G9+C2 台账页只读投影）。
- **W7** +~600 行可选（G11 扩展桥；A:G7 通知框架已在册）。
- **W1** +~150 行（G8 schedule 子命令可随 F2 battle auto 顺手）。
- 合计较蓝图 §四b 修正后（4.6-5.5 万行）**再增 ~5300-6800 行**（其中 C2/WebShell 按开工令为已批必做，非可选）。**不新开 W9**——所有缺口均有归宿波次。

---

## 六 · 证据可复核性声明

- 对方每件出处=本档开头所列语料实读行号（手册 422 行全文通读；活访 146 行全文；部拆 B.2 按 节引）；源码数字为本舰亲手清点：tools/*.yaml=90、roles=13 YAML、skills=23、agents=16 .md、internal/=41 模块、web/static/js=82、plugins=burp-suite+browser-extension、mcp-servers=2（CyberStrikeAI checkout，2026-10-18 快照）。手册:290 称「84 个 js 模块」「100+ 配方」，实数 82/90——以实数入档。
- 我方每件出处为仓内文件实测行号（2026-10-18 快照，分支 feat/bo14-tanyin 工作区）；命令面=registry 实跑枚举（67 键/41 基名+tanyin-* 15 个 CLI 入口）；13 表=schemas.json 实读；知识环停转=knowledge/log.md 尾笔 2026-09-29（与蓝图:7「停转18天」互证）。
- 本档为唯一写入件；语料与代码零改动。CSAI 侧两处与手册不符处（js 模块数、工具配方数）照实记录不改语料。
- 法律敏感声明：C2/WebShell 相关各件（B7-B13/K1-K2/G1）均标注「法律敏感：仅自有/书面授权目标，授权书覆盖后渗透动作」；开工令依据=git 419eecf（用户原话「C2/WebShell 做」）。

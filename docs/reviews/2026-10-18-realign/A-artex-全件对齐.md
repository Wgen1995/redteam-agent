# A · ARTEX 全件对齐（逐件表）· 2026-10-18 重对齐

> 执笔：重对齐子代理 A（域=ARTEX 全面）。纪律：语料与代码只读，唯一写入=本档。
> 对手语料：`docs/research/manuals/usage-guide-artex.md`（下称**手册**）、`docs/research/liveui/walk-artex-live.md`（下称**活访**）、`docs/research/liveui/2c-artex-visual-baseline.md`（下称**视觉**）、`docs/research/liveui/2b-artex-export-ui.md`（下称**2b**）、`docs/research/artex-deep-dive/{1-orchestration,2-data-graph,3-security-gates,4-reliability-ops,0-index}.md`（下称**深读1/2/3/4/0**）、`docs/research/engine-parts-artex-csai-multica.md` B 章（下称**部拆**）。
> 我方仓：`/Users/wgen/redteam-agent`（下称**仓**）。波次基线：`docs/design/exceed-blueprint-2026-10-17.md`（下称**蓝图** W1-W8=蓝图:22-29，§四b=蓝图:39-65）。
> 判词四档：**已超**（超越点实打实）/ **已排**（波次有名）/ **声明取舍**（对等策略，用户知情）/ **真空白**（不许留，发现即给方案）。
> 一句话总判：**ARTEX 是一台"作业现场完整、供给治理齐备、留痕松散"的自主渗透控制台；我们是"判据脊柱极硬、双腿（Web 面+引擎运行态）没长全"。逐件对齐后：已超 14 件、已排 52 件、声明取舍 8 件、真空白 22 件（真空白全部给出方案并入波次，一件不悬空）。**

---

## 〇 对蓝图 §四b 初表的校对（用户点名的任务）

§四b（蓝图:39-63）21 行初表方向正确，但按运行时行为核后有 **9 处须修正**：

| # | §四b 原判 | 校对结论 | 证据 |
|---|---|---|---|
| C1 | chat 对话「无Web面」 | **不准确**：写路径已存在——`/api/battle/say`（操作员→战士指令通道，server.py:615-644）；缺的是"对话页"与 @实体引用//btw/附件/多会话等运行时行为 | 仓 cli/webui/server.py:615-644 vs 手册:169-182 |
| C2 | traffic「无」 | **不准确**：Tier3 egress 代理已存在（compile/verify/serve，cli/tanyin-egress:8-12），且 TLS 不解密是**声明取舍**不是空白；缺的是"录制回放页+exchange 落库" | 仓 cli/ledger/egress_proxy.py:6-10 vs 手册:282-289 |
| C3 | system/llm「CLI侧」 | **不准确**：llmpool 是**离线判定核**（错误分类+冷却+抖动，cli/ledger/llmpool.py:1-20）+battle 接线（状态钉根+事件入账，cli/ledger/llmpool_wire.py:4-14），**没有** CLI 运营命令、没有接进战士真实请求路径 | 仓两文件 vs 手册:306-348 |
| C4 | login/setup「登录锁已有」 | **漏了 P0**：WebUI **读面零鉴权**——9 页 HTML+state/matrix/evidence/session/metrics 五 API+`/api/stream` SSE 全部不做会话校验（会话校验只挂在写路由 server.py:366 与 `/api/approval` server.py:678），登录页对读面是装饰 | 仓 cli/webui/server.py:255-292 |
| C5 | system/notify→「W7 webhook」 | **只排了 1/6**：钉钉/飞书/企微/Telegram/Email 五渠道+投递五态记录+重试+test 端点任何波次都没排 | 蓝图:59 vs 手册:373-378 |
| C6 | tasks「W1+W6」 | **漏子件**：批量暂停/归档/分类（手册:190）、归档冷存储+还原依赖检查（手册:209）、任务删除范围选项（手册:207）未点名 | 蓝图:47 vs 手册:184-209 |
| C7 | 初表无 API 面行 | **缺一行**：ARTEX 243 注册路由（手册:526-546）vs 我们 WebUI 12 路由——API 面作为独立件没进表 | 本档 §C |
| C8 | 初表无引擎件行 | **缺一族**：plannerLoop 六道门/800ms debounce/frontier CAS/共享 todolist/超时收尾 settlement/compactor——W5 只写了"常驻规划者MVP"六个字，运行时行为没铺 | 深读1:9-22 |
| C9 | sync「W7 可选」 | **方向对但漏对等底牌**：我们已有反向件 zhulong-export（findings 推出，cli/ledger/zhulong_export.py:9-16），对等叙事应是"双向：出已建、进待排" | 仓 vs 手册:300-301 |

---

## 一 · 逐件表

### A. 认证壳与全局骨架（7 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| A1 | /setup 首次初始化管理员（手册:109,147） | 无 setup 向导；操作员口令=TANYIN_OPERATOR_KEY 或随机+banner（cli/webui/server.py:821-823） | 中 | serve 启动检测"零配置态"→ /setup 页三步：设口令（写 ~/.tanyin/operator.key 0600）→声明授权要件模板→生成首个 battle 骨架；全程 timeline 留痕 operator-init 事件 | W6（设置页）+W7（demo 开箱联动） | 真空白（已给方案） |
| A2 | /login 使用须知滚动到底才可登录+用户名只读（手册:110；活访:36-38） | login.html 有；无条款弹窗/滚动闸 | 小 | 加"交战规则确认"弹窗（内容=Roe 八问摘要），滚动到底解禁——把 ARTEX 的合规装饰变成真闸：确认动作本身落 timeline 一行（actor=操作员） | W6 | 真空白（小） |
| A3 | JWT+localStorage+cookie 7 天+401 自动清凭据跳转+渲染前 auth gate（手册:23,119） | HttpOnly+SameSite=Strict cookie 会话+写路由守卫（server.py:476-478）；**读面零校验**（见 C4） | 读面=大；凭据形态=我们更安全（HttpOnly 抗 XSS，JWT-in-localStorage 是它的洞，活访发现 #48 同类攻击面） | 读面统一挂 `_session_ok()`（一行改动×11 处）；页面加 401→/login 跳转（index.html:809 已有先例）；**不搬 JWT**——cookie 会话+CSRF 双检已更硬，补齐覆盖面即反超 | **W1（serve 收口点名扩）** | 真空白（P0） |
| A4 | 改密对话框+账户切换器（手册:112） | 无 | 小 | /api/operator/password POST（旧口令 hmac 比对→写新 key→全会话失效）；账户切换不做（单操作员=我们的声明取舍，多角色归 W7 RBAC） | W6 | 真空白（小） |
| A5 | floating 侧栏 17rem 可折叠+两组 21 项（手册:115；视觉:23-30） | 侧栏已有 3 组 9 项（2c:78 home 现状）；无折叠 | 小 | 侧栏折叠钮+localStorage 记忆；分组"小标题+48px 空隙"节奏照抄（视觉:96-97 工艺批已列） | W6（工艺批） | 已排 |
| A6 | Command Palette ⌘J+主题循环+7 布局 cookie（手册:116,118） | 仅深浅切换（2c:47） | 小 | 命令面板=9 页路由+高频动作（暂停/恢复/审批）统一 ⌘K；布局 cookie 4 个（theme/font/sidebar/密度） | W6（工艺批） | 已排 |
| A7 | 控制台型/文档型两范式+grid 撑满视口（手册:117） | 各页文档型硬滚（2c:70-72：graph 2228px/evidence 2705px） | 中 | session/activity 改控制台型（内部滚动）；graph 画布缩放平移（视觉:99-102 方向盘批已列） | W6 | 已排 |

### B. 21 Web 路由逐件（含运行时行为，50 件）

**B-1 仪表盘 /dashboard**

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B1 | 六统计卡：活跃任务/发现四级/资产/流量/Token（手册:125,161；活访:42） | home 有九门灯+预算三卡+KPI 五数（2c:79） | 小（形态异） | 保留九门灯（它没有），补"发现四级/资产计数/Token 三段"三卡；每卡点击跳对应页（KPI 已是链接，2c:60） | W6（仪表盘经济学） | 已排 |
| B2 | Token 双数据源切换+模型筛选+缓存命中率大字+5 档时间粒度（手册:162；活访:43,26） | budget.tsv 只有 token_delta 单段（cli/ledger/schemas.json budget.tsv 8 列）；无缓存段/粒度页 | 中 | 数据源先行：budget.tsv 加 cache_hit_delta 列（opencode usage 帧抽取，W1 serve 输出契约一并）；页=三段条图+命中率+按模型分组表 | W6（仪表盘经济学）+W7（成本口径） | 已排 |
| B3 | 活动流 25 条+类型计数徽标+「查看任务」跳转（手册:163；活访:44-48） | activity 页 SSE 全量流（cli/webui/static/activity.html） | 小 | home 加"最近 25 条"窗（复用 /api/state.json projection，零新端点） | W6 | 已排 |
| B4 | 三档轮询 2/5/15s+JSON 签名比对才 setState（手册:167,475） | SSE 优先+页面自轮询（sse.py:1-16 尾随生成器）；无签名比对 | 小 | 指纹比对=sha256(json) 不变则跳渲染（10 行 JS）；轮询分档按源快慢标注 | W6（SSE 换代） | 已排 |
| B5 | 任务表：状态/进度/漏洞四联/Worker 数/Token 三段/时长（手册:165,186） | home 战局切换 21 项下拉（2c:60） | 小 | 战局表补"漏洞四联+Token 三段+运行时长"列（数据全在账本，纯投影） | W6 | 已排 |

**B-2 对话 /chat**

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B6 | 会话分组/pin/双击重命名/多选批删 100/批（手册:171） | 无对话页；指令通道单发（server.py:615-644） | 大 | 介入对话页：每 battle 一线程，消息=directive 注入+timeline 双落（say 已做）；历史=timeline actor=人工 行回放 | W6（介入对话页，§四b 已立） | 已排 |
| B7 | @引用 9 类实体，token `@[漏洞#12 标签]`（手册:175） | 无 | 中 | @菜单吃账本实体（FD-/EV-/资产 ID/战局号），选中即拼 `#FD-12` 进指令文本——战士侧 prompt 已认账本 ID，零协议改动；比它强处：引用即入链（timeline 引用记录） | W6（介入对话页规格扩） | 真空白→并入 W6 规格 |
| B8 | 附件上传到会话目录（手册:176） | 无 | 中 | /api/battle/attach：文件落 battle 目录+sha256 入 timeline artifact 事件（ARTEX 附件不入链——我们加链即超） | W6 | 真空白→并入 W6 |
| B9 | /btw 旁路提问不污染主上下文（手册:177） | 无 | 中 | 战士运行中旁路问答=对 runner 日志+账本的**只读问答**（不注入战士），天然零污染且不需要它的五段准备态——降维实现即超 | W6 | 真空白→并入 W6 |
| B10 | 停止钮只停本会话+IME 组合态放行+Enter 偏好（手册:178-179） | stop=杀进程组（server.py:585-598）；say 输入无 IME 防误发 | 小 | 会话级 stop=directive「停止本轮工具调用」软停（进程级 stop 保留为红色确认档）；IME isComposing 放行 3 行 JS | W6 | 真空白（小） |
| B11 | LLM 热切换 PATCH /conversations/{id}/profile（手册:180） | 无（模型=opencode profile 静态） | 中 | battle 级 profile 切换：改 goals.tsv model_tier 行（amendment）+runner 重启战士生效；任务头显链钮 | W6（llmpool 管理页联动） | 已排（规格扩：battle 级） |
| B12 | Todo 气泡+URL ?c/?approval 深链恢复（手册:181-182） | 无 | 小 | ?battle=N&anchor=row 已可做（session.json 带 battle 参数先例 server.py:284-285）；审批深链见 E 组 | W6 | 已排 |

**B-3 任务中心 /function/tasks**

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B13 | 列表+筛选+行内五操作（重命名/暂停恢复/置顶/归档/删除）（手册:186-188） | /api/battle/control pause/resume/stop 三动作（server.py:547-613）；无重命名/置顶 | 小 | 重命名=battle 元数据行（battles.json 增量）；置顶=home 排序键 | W6（多战场切换器） | 已排 |
| B14 | 批量 control/archive/category（手册:190） | 无 | 中 | 批量面=CLI 先行（battle.py 加 batch 子命令，循环调 control）+Web 复选框调同端点——**双面同源**演示件 | W6 | 真空白→并入 W6 |
| B15 | 新建任务 11 字段（模板/分类/超时/心跳/并发上限/任务级拦截/LLM 链 dnd）（手册:192-205） | /api/battle/new 四件：名称/说明/范围白名单必填+预算硬顶必填（server.py:487-502） | 中（字段少但我们的两必填是它没有的硬闸） | 补：任务书模板下拉（battle-kit BRIEF 模板已有，scripts/battle.py:318 --brief）、超时=goals 预算 hours 段（已同源）、并发=W5 多战士参数；**不抄心跳/任务级拦截进表单**——范围由 scope 单源+资产拦截走 amend-scope | W1（授权真上传）+W6 | 已排 |
| B16 | 删除范围选项 DeleteTaskOptions（手册:207） | 无删除面（battle 目录手工删） | 小 | battle.py 加 archive/purge 子命令：purge 前 verify-chain+报告产物另存校验，删除范围 --keep-report/--keep-evidence 显式旗标 | W6 | 真空白→并入 W6 |
| B17 | 归档冷存储+还原依赖检查（手册:209） | 无 | 中 | 归档=battle 目录 tar+zstd+manifest（sha256 全录）落 ~/.tanyin/archives/；还原=manifest 校验+依赖检查（引用的共享知识库版本仍在） | W6 | 真空白→并入 W6 |

**B-4 任务详情 10 页签（会话/总览/探索链路/播报板/发现/复测/测试资产/资产覆盖图/拦截审批/报告）**

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B18 | 会话页签四分组（主 Agent/Planner 态势/LLM 故障审计/Workers 每意图一行）（手册:215-221） | session 页三块有活 bug（2c:81：TypeError 自动重试，近乎全空） | 大 | 修 bug 先行（2c:105 方向盘批#6）；四分组改三分组：操作员指令/战士轮次/系统事件（planner 我们=W5 后有）；worker 行=intent 行（pending-intents 已有数据） | W6（会话页重做）+W5（planner 流） | 已排 |
| B19 | transcript 渲染器：tool_use↔tool_result 按 id 配对成单行折叠卡+连续文本合并+400px 懒加载（手册:222） | session 页工具卡三态（2c:134 session 行）；无配对合并 | 中 | opencode-run.log.runner.tsv 已有 tool 事件流（trace_search.py:16 布局）；配对键=调用 id，折叠=命令+状态一行，展开=命令/输出两段 | W6 | 已排 |
| B20 | Worker 介入三件套：暂停/留言（4000 字+幂等 requestId）/直接继续（手册:224-227） | say 指令通道（全 battle 级）；无单意图暂停 | 中 | intent 级：set-intent-status --status=paused（命令已有）+Web 行内钮；留言=say 带 --intent 定向；幂等键=timeline hash 去重 | W5（多战士）+W6 | 已排 |
| B21 | 意图删除双模式（假删留因回流 planner/真删级联仅独撑下游+toast 报数）（手册:229-231） | set-intent-status 有；supersede-finding 有墓碑（cli/ledger/report_artifacts.py:8-10）；无删除对话框/级联 | 中 | 假删=status=voided+reason 列（intents.tsv 已有 reason，schemas 见 cli/ledger/schemas.json intents 16 列）；真删=consumed-facts 反查独撑下游（unconsumed-facts 命令已有数据面），删除前后 verify-chain 报数 | W5（常驻规划者消费 reason）+W6（对话框） | 已排 |
| B22 | SSE 可靠性：snapshotCursor 衔接/mergeBySeq 去重排序/MAX_KEEP=4000/Last-Event-ID 断线续传/断链琥珀条（手册:233,457-458；深读4:19） | sse.py 帧带 id=行号（sse.py:34-36）+keepalive 15s（sse.py:12-13）；**服务端不读 Last-Event-ID 头**（server.py:332-335 只认 ?tail=），EventSource 自动重连会回退默认尾窗 | 中 | 读 Last-Event-ID 头（4 行）；客户端按行号去重合并；冷会话只留尾部记账帧；断链常驻"重连中"条 | W6（SSE 换代，蓝图:61） | 已排 |
| B23 | TokenMetrics 三段 badge+服务端持久化+客户端只加未完帧（手册:235） | budget.tsv 累计（账本侧更硬）；页头无 | 小 | session 页头三段 badge=读 budget.tsv 上卷（query_cmds.budget_tree 已有单源） | W6 | 已排 |
| B24 | 总览：目标管理（改目标通知规划者并复活任务）（手册:239） | goals.tsv+add-goal/amend；改后复活=无（无 planner 可通知） | 中 | W5 前降维：目标修改=timeline goal-amend 事件+W2 intents 租约被唤醒检查；W5 后=真通知 | W5 | 已排 |
| B25 | 总览：操作约束 allow/deny 注入提示（手册:240,414） | scope include/exclude+DENYLIST+AGENTS-INJECT 八条（cli/ledger/hosts_matrix.py:7-10） | 小（形态异） | 约束=账本单源：新增 constraints.tsv（allow/deny/action+reason），guard gate_chain 消费同源（不进提示进执法——比它硬） | W2（多战执法面） | 已排 |
| B26 | 总览：任务级资产拦截七种匹配+白名单语义（手册:241） | scope.tsv include/exclude/oob 三态+amendment 链（cli/ledger/enforce.py:12-18）；无 URL/模糊/CIDR 七种 | 小 | matchers 扩 kind：url-exact/domain-fuzzy/ip-fuzzy/cidr（enforce.load_scope 加 4 个判定函数，Tier1/2/3 同源自动生效） | W2 | 已排 |
| B27 | 总览：覆盖度百分比+按类型分解+分母 scope（手册:242-245；活访:70） | ledger-scope-coverage 命令+coverage 页 WSTG 矩阵（2c:82） | 小（口径更严） | 覆盖度=矩阵消格/分母（denominator-ready 门已把分母上锁，cli/tanyin-phases:4-6）——比它"planner 自扩分母"诚实（活访:92 实锤它授权蔓延）；页补百分比+类型分解卡 | W6 | 已超（口径）+已排（展示） |
| B28 | 总览：心跳（引擎态/Worker 数/最近活动/payload 卡）（手册:245） | runner 心跳=runner.tsv 事件流（cli/tanyin-runner:228-280 watchdog 巡检） | 小 | 总览页心跳卡=直读 runner.tsv 尾行+soft/hard stall 状态 | W6 | 已排 |
| B29 | 探索链路 React Flow：goal/intent/fact/finding/hint+血缘边+digest 超级节点+缩放平移（手册:249-250；视觉:38-39） | graph 页 11 层泳道 SVG 无缩放（2c:83：2228px 硬滚+标签重复 4 次 bug） | 中 | 零依赖 SVG 保留（2b:12 不搬 React）；加 viewBox 缩放/平移（vanilla JS ~80 行）+digest 折叠超级节点（数据=timeline 压缩事件）+修标签重复 bug | W6（图谱演进 v1） | 已排 |
| B30 | 播报板：六类筛选+8s 条件刷新（仅最新在第 1 页才真刷）+300ms 防抖（手册:252-253） | activity 页全量流无筛选 | 小 | 筛选 chips（门/类型/actor）+追尾暂停钮（2c:80 已列） | W6 | 已排 |
| B31 | 任务内发现页签：全文不截断+行操作复测/deepen/删除（手册:255-256） | evidence 页 44 卡纵排无筛选（2c:84） | 小 | 三态过滤+分页（2c:84 已列）；行操作接 CLI（replay/deepen=W3） | W6+W3 | 已排 |
| B32 | 复测页签：retester 独立会话+结论自动改处置+复用会话（手册:258-259） | tanyin-replay 机械盲重放三态+REPLAY_CAP=3+判定产物只增（cli/tanyin-replay:3-20） | 机械面已超（确定性重放>LLM 复测）；**会话化复测岗**无 | 复测常驻岗=对 REPAIRED 候选自动排队 replay（读 replay/<EV>/<seq>.json 尾态），跨战复测同律——LLM 复测为可选第二意见（W5 复测常驻岗） | W5 | 已超（机械重放）+已排（常驻岗） |
| B33 | 测试资产页签：六类计数+新增/移出+任务间共享（手册:261-262） | add-asset/add-edge 命令（49 面内）；无页 | 小 | 资产页=assets.tsv+edges.tsv 投影（六类计数卡+检索）；新增/移出走 add-asset/del-edge（新命令）双面同源 | W6（资产搜索页，§四b 已立） | 已排 |
| B34 | 资产覆盖图 G6 力导向+已测高亮（手册:264-265） | graph 页分层泳道（静态但血缘全） | 小 | 力导向不强求（泳道更适合审计）；补"已测/未测"双色+点击节点→证据过滤 | W6（图谱演进） | 已排 |
| B35 | 拦截审批页签：pending 计数 pill 99+（5s 轮询）+内联审批卡 amber（手册:213,267-268） | /api/approval pending 投影+approvals.tsv（server.py:646-675）；home 审批卡 401 跳登录先例（index.html:809） | 小 | pill=approval 投影 count 字段（已有）；内联卡=evidence/activity 流插 pending 行卡 | W6（审批中心） | 已排 |
| B36 | 报告页签：Markdown 全文渲染+复制+生成时间（手册:270-271；活访:108-112） | /api/report/download 缺则触发 render（server.py:736-747）；FD 九段渲染器（cli/ledger/report_render.py:2-10） | 内容深度已超（九段+双轴+SARIF）；**页面**弱 | 报告页=渲染 draft md 分节锚点+复制+下载三件；时间链断言结果页头展示（render 自带 rc 语义） | W6（报告页） | 已排 |

**B-5 其余功能页**

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B37 | /function/findings 三视图+四维筛选+导出（手册:273-279） | FD 账本 19 列（schemas）+findings_json 全量导出（report_artifacts.py:4-6）；无页 | 中 | 发现页三视图=按战/按资产树/全表；导出沿用 findings_json（VulnClaw 同型已超它 flat 导出） | W6+已超（导出面） | 已排 |
| B38 | 发现详情：版本化流量证据绑定+血缘+九态状态机（手册:280） | evidence_ids/control_evidence_ids 双列（schemas）+replay 三态+supersede 墓碑（report_artifacts.py:6-10）；流量证据绑定无（无流量库） | 中 | 九态收敛为我们的三态+双轴（它九态无执法=人手点，我们三态有机械重放背书——不抄九态抄三态深化）；流量绑定=W6 流量三源回传后 EV 卡加 traffic_ref 列 | W6（发现三态） | 已排 |
| B39 | /function/traffic MITM 录制+筛选+exchange 详情+绑定漏洞（手册:282-289） | Tier3 egress 代理（CONNECT+DNS pin+canary 告警，cli/ledger/egress_proxy.py:3-10）；**不录内容**（TLS 边界声明） | 页=大；能力=取舍 | 三源回传：①runner 日志 HTTP 行 ②EV 卡 raw_request ③egress OOB 落账——三源对账页+绑 EV；MITM CA 不做（客户环境截 TLS 是合规雷，声明取舍） | W6（流量三源回传，蓝图:48 已提级） | 声明取舍（MITM）+已排（回传） |
| B40 | /function/commands 命令审计+stats（手册:291-292） | timeline 全事件（含 guard REJECT 行，cli/tanyin-guard:152-193）+trace_search；无页 | 小 | 命令页=timeline actor=guard/warrior 行投影+按工具 stats 聚合（纯只读） | W6（审批中心同族） | 已排 |
| B41 | /function/llm-records 按任务/模型明细（手册:294-295） | budget.tsv 用量+llmpool failover 事件入 timeline（llmpool_wire.py:11-14）；无逐调用记录 | 中 | llmrec 等价物=opencode usage 帧抽取落 llm-records.tsv（serve 收口契约带出）；页=按战/按模型透视 | W1（输出契约）+W6（llmpool 流水页） | 已排 |
| B42 | /function/assets 六类卡+DSL 搜索+新增企业（手册:297-298） | assets/edges 账本+add-asset/add-edge；无页无 DSL | 中 | DSL=账本字段过滤语法（type:host 状态:已测 severity>=高），parser 复用 query_cmds 谓词——20 行文法不引外部引擎 | W6（资产搜索+DSL，§四b 已立） | 已排 |
| B43 | /function/sync ScopeSentry（MCP+Key+项目维度同步+公司归并）（手册:300-301,543） | 反向已有：zhulong-export 推出（cli/ledger/zhulong_export.py:9-16 契约实勘）；导入无 | 中 | 对等=import 适配器（读 ScopeSentry API→add-asset/add-scope 走账本门）；**不排优先级高于自有靶场**——声明为可选件 | W7（可选适配） | 声明取舍（优先级）+已排（W7 可选） |
| B44 | /function/workspace 目录树+上传/下载/读写（手册:303-304） | battle 目录在盘+报告下载（server.py:736-747）；无管理页 | 中 | 工作区页=白名单根（~/.tanyin/battles）+目录树+下载（读盘流式）；**编辑不开**（写面只走账本——超它的点：产物 sha256 登记 timeline artifact 事件） | W6（工作区页，§四b 已立） | 已排 |
| B45 | /system/llm profile 18 字段（格式/代理/限速/context_window/thinking/effort/优先级/pool_exclude/streaming/max_tokens/session_header_key/重试覆盖）（手册:308-329） | llmpool 判定核（分类/分道冷却/抖动，cli/ledger/llmpool.py:1-46）；无 profile 存储/管理面 | 大（面）小（核） | profiles=llm-profiles.tsv（name/base_url/model/priority/pool_exclude/rate/context_k）；opencode 侧经 provider 映射消费；session_header_key 不做（无网关假设） | W6（llmpool 管理页） | 已排 |
| B46 | /system/llm 轮询开关+绑定兜底+熔断落库恢复+立即恢复（手册:331） | 熔断 Registry+goal 钉根状态文件+重启恢复（llmpool_wire.py:7-8）+llm_switch 事件（:14） | 小 | reset 命令=删 llmpool_state.json 冷却段+timeline llm-reset 事件（CLI/Web 双面） | W6 | 已排 |
| B47 | 五层重试：建连/空响应/流中断（per-profile 覆盖）→熔断→链切换→意图重跑（手册:333-348；深读4:7-10） | 我们已超两处：429/5xx 分道冷却+±20% 抖动（llmpool.py:11-16，深读4:36 点名它的洞）+类型化错误（深读4:40 点名）；缺：**实链**（判定核未接真实请求）、意图重跑层 | 实链=大 | 实链接线：llmpool 侧作 opencode provider 前置 sidecar（本地反代 127.0.0.1:port，重试/熔断/链切换在 sidecar 内，failover 事件经 wire 入 timeline）；意图重跑=W5 引擎层 model_error 重入队 | **W2（引擎地基扩：池 sidecar）**+W5 | 真空白（实链）→已给方案 |
| B48 | /system/agents 8 Agent+prompt 版本化/wrapup/P3 触发器/可见性矩阵/变量（手册:350-365） | phases P0-P6 协议（phases/PROTOCOL.md）+AGENTS-INJECT 八条（hosts_matrix.py:7-10）+五宿主矩阵；无 Agent 配置页 | 中 | 战士配置页=phases.yaml 门参数+注入块可视化（只读为主）；prompt 版本化=git（我们的战士提示词在册即版本）——**不抄 8 Agent 花样**，抄"每 agent 可见工具矩阵"（见 B49） | W6（战士配置页，§四b 已立） | 已排 |
| B49 | per-agent 可见性矩阵（MCP/Skill/工具开关）（手册:365,546） | WARRIOR_ENV 白名单+Tier 注入（cli/tanyin-runner:30-49）；无按战士工具面 | 中 | visibility=工具卡注册表加 agents 列（W3 工具卡 25 张时一并）；执法在 guard（工具不在面=REJECT unknown-tool） | W3（工具卡）+W6（配置页） | 已排 |
| B50 | /system/mcp（Streamable HTTP/SSE 接入+刷新）（手册:369） | 无 | — | 插槽制对等（蓝图:56 已声明）；如做=mcp.toml+guard 包一层（MCP 工具过 Tier1 同律——它 MCP 裸奔过 guard 我们不） | W7（可选） | 声明取舍 |
| B51 | /system/skills zip 上传+文件编辑+usage+missing（手册:370） | .opencode/skills/tanyin 技能在册+knowledge 库 14 子命令（cli/tanyin-knowledge:17-19）；无页 | 小 | 技法页=knowledge/ 与 skills/ 目录投影+usage（timeline skill 事件计数）；zip 上传不做（git 单源更硬，声明取舍） | W6（技法页，§四b 已立） | 已排+声明取舍（zip） |
| B52 | /system/tools 注册表+调用计数+schema+自定义 script 工具+test（手册:371） | tools.lock 供应链 ECDSA（cli/ledger/supply_chain.py:1-8）+DENYLIST+工具卡 W3；无页 | 小 | 工具卡注册表页=卡片清单+纪律标注+锁版本+验签状态（比它多：每卡带 ROE 标注——蓝图:58 已写"卡带纪律标注"） | W3+W6（§四b 已立） | 已排 |
| B53 | /system/notify 6 渠道（钉钉/飞书/企微/TG/邮件/Webhook）+realtime/digest+过滤+限速（手册:373-376） | 无任何通知 | 大 | notify 框架：channels.tsv+notify-cli（send 子命令：stdlib urllib，凭据 env 通道）；触发源=timeline 事件谓词（发现四级/gate-fail/预算 80%）；**投递先落 timeline notify 事件再发**（它的投递不入链，我们入链即超） | **W7（扩：webhook→6 渠道框架）** | 真空白→已给方案 |
| B54 | 投递记录五态+重试+延迟 test（手册:377-378） | 无 | 中 | deliveries.tsv（五态+attempt+next_retry）；重试=notify-cli retry --id；test=--dry-run 真连一次 | W7 | 真空白→并入 W7 |
| B55 | /system/intercept 拦截范围 8 工具+规则三动作+优先级+内置 20 条（100/90/80）（手册:380-391） | Tier1 guard deny-list（DENYLIST.md 单源+内嵌兜底，cli/ledger/enforce.py:25-84）+nuclei 参数门+速率窗+时间旅行+account-grant+只读执法（tanyin-guard:139-193） | 深度已超（六类 REJECT 全落链）；**ask 动作无**（我们只有放行/拒绝两态） | ask 三态：guard 输出 ASK+pending 文件（goal 目录 pending.tsv）+Web 审批中心/CLI approve --row 双面裁决+超时默认拒（fail-closed，与它超时可配相反）——裁决行入链 | **W2（多战执法面扩：ask 三态）**+W6（审批中心 UI） | 真空白（ask）→已给方案 |
| B56 | 内置规则分层 100/90/80 优先级+首条命中（手册:384-388） | DENYLIST.md 平面清单（enforce.py:62-81 逐条比对） | 小 | 分层=文件分节（### P0 毁灭/### P1 数据破坏/### P2 清理类）+命中报层级；规则命中行已落 timeline（比它多审计） | W2 | 已排 |
| B57 | judge 模型语义判定（低温度单 JSON 三值+lane 计量+异常回退）（手册:389；深读3:11,15） | judge_client 已建（temp=0/token 级严格解析/fail-closed 返回 (None,reason)，cli/ledger/judge_client.py:1-14）；**未接执法链**（无消费者，tests 外零调用） | 接线=大 | 接线点：guard ASK 前置（规则未命中+高危动作特征→judge 裁决，verdict=None=fail-closed 拒——反转它的 fail_action=allow，深读3:33 点名其洞）；lane 计量=budget.tsv scope=judge 行 | W2（ask 三态一并） | 真空白（接线）→已给方案 |
| B58 | judge 输入边界（只审当前调用不带任务背景，防提示注入）（手册:463；深读3:26 信息饥饿） | judge_client 单轮+键白名单（:5-7）——输入边界同律可守 | 小（已同律） | 接线时明写：judge 输入=tool_name+arguments 原文，禁带任务书/约束/历史（写进 guard 调用点注释+测试） | W2 | 已超（fail-closed）+已排（接线） |
| B59 | /system/intercept/assets 资产黑白名单七种 kind（手册:393-394） | scope include/exclude/oob+amendment（enforce.py:12-18）+egress ACL 展开（tanyin-egress:5-7） | 小 | 七种 kind 见 B26；全局 vs 任务级=amendment 链天然支持（后行覆盖先行） | W2 | 已排 |
| B60 | /system/intercept/approvals：历史+详情快照（审查上下文 v1/v2/v3+会话审计片段+SHA-256 指纹组）+深链定位（手册:396-401） | approvals.tsv 7 列+HMAC 签名链路（server.py:685-732：command_hash+sig+持钥子进程）；快照/指纹组无 | 中 | 快照=审批时把 judge 输入/guard 判定原文存 approvals/<id>.json（只增）；指纹组=hash(command)+hash(judge_input)+hash(config) 三段——它有我们无，加上链后比它多"裁决入哈希链" | W6（审批中心）+W2（ask 三态） | 已排 |
| B61 | /system/logs 级别筛选+暂停+清空+SSE（手册:403-404） | activity=SSE 流（timeline 口径）；无系统日志页/清空 | 小 | 系统日志=webui+runner stderr 落盘 logs/webui.log；页只读+级筛；**清空不做**（账本律：日志只增，声明取舍） | W6 | 已排+声明取舍（清空） |
| B62 | /system/settings 10 卡（更新/流量捕获/自动绑流量/全局代理/约束注入/noa 压缩/四源搜索/Python 解释器/Worker 并发/发送键位）（手册:406-419） | goals.tsv model_tier/guard_tier/rate_limit/budget（schemas）——**配置在账本不在设置页**（设计更硬）；页无 | 中 | 设置页=账本参数的读写面（amendment 语义，改动=行+因）；全局代理=Tier3 egress 上游（已有位）；Worker 并发=W5 参数 | W6（设置页，§四b 已立） | 已排 |
| B63 | 网络搜索四源 ddgs/brave/tavily/deepseek（手册:416） | 无（战士栈无搜索源） | 中 | web 情报源入工具卡族（W3 工具卡加 web-intel 卡：ddgs 免 key 先行，tavily/brave 插槽参数）；出网过 Tier3 egress 同律 | **W3（工具卡扩：web-intel）** | 真空白→已给方案 |

### C. API 面（3 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C-1 | 243 注册路由按 20 组（手册:526-546） | WebUI ≈24 端点：9 页 + 9 只读 API（approval/session/matrix/graph/evidence/metrics/state/stream/status.js，server.py:255-292,77-81）+6 写（login+5，server.py:358-359）+**CLI 49 命令**（cli/tanyin-ledger:9-19）+dsh 插件 10 工具（platform/dsh-plugin-tanyin/README.md:1-5） | 数量大（10 倍差）但**双面一等公民是我们的形态**（它无 CLI） | 路由随 W6 各页自增（每页=1 页面+1 投影 API）；**不变的是面契约**：写操作全部 CLI 单源，Web=薄壳转发（battle/new 先例 server.py:518-537 ledger 回执直传）——API 数量不求 243，求"每写路径 CLI 可复现" | W6 | 声明取舍（数量）+已排（随页增长） |
| C-2 | SSE ?token= 认证（EventSource 不能带头的官方解法）（手册:22；活访:127） | /api/stream 零认证（server.py:332-335）——兼安全问题 | 大（安全） | 短时签名查询参数（sid 的 HMAC+过期戳，复用 approval_key 先例 server.py:692-714）；与 A3 读面鉴权一并收口 | W1 | 真空白（并入 A3 P0） |
| C-3 | 批量/归档/模板/分类/可见性 API 族（手册:531,545-546） | 对应 CLI 件已有或已排（B14/B17/B15）；模板=battle-kit BRIEF（battle.py:318） | 小 | 随 B14/B17 页面化自带；模板库 W6（蓝图:27） | W6 | 已排 |

### D. 引擎件（事件驱动 planner/worker/retester，14 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| D1 | plannerLoop 事件驱动+心跳兜底 600s+800ms debounce+六道门（深读1:9,22；部拆 B.1.1） | 引擎=runner 薄保姆（心跳监控/停滞分级/死亡续跑，cli/tanyin-runner:8-12,176-179）+phases 确定性状态机（cli/tanyin-phases:2-6）+gateloop 臂 B（python 掌节奏）——**无常驻规划者** | 大（形态差） | W5 常驻规划者 MVP 已排：事件源=timeline 行增长（file 监听复用 watchdog.next_tick 自适应节流，cli/ledger/watchdog.py:10-12）；debounce=500ms 合并；六道门对应我们的门前置（paused/battle 终态/预算耗尽/scope 空分母） | W5（蓝图:26） | 已排 |
| D2 | frontier=DB 单表 CAS 领取（UPDATE...WHERE state=open，RowsAffected=1）（深读1:13） | intents.tsv 静态账本+pending-intents 查询；无并发领取 | 中 | W2 intents 租约已排（蓝图:24）：TSV 当前态列+租约行（lease_owner/lease_until），CAS=条件写（锁内 compare-and-set）；**链记事件+TSV 记当前态**双轨（深读1:41 它自己建议的方案） | W2（蓝图:24） | 已排 |
| D3 | 意图状态机 8 态（open/running/done/paused/blocked/exhausted/deleted）+重启 ResetRunning（手册:85-101；深读1:13） | set-intent-status/intent-status 命令+status 列；blocked/exhausted 语义未分 | 小 | 状态词表对齐：blocked=模型/API 故障（llmpool 实链后联动）、exhausted=预算掐断（budgetctl REJECT 已有判定面）；重启恢复=resume-kit 已有（cli/tanyin-phases:5） | W2+W5 | 已排 |
| D4 | 共享 todolist 跨唤醒保多步链（深读1:15；手册:81）——**它纯内存重启丢**（深读1:33） | intents 依赖=via/dedup_key 列+chain-create/chain-advance/chain-ls 命令族（49 面内）——**链在账不在内存，重启天然恢复** | 已超 | 保持；补 render 进 prompt（W5 常驻规划者消费 chain-ls） | W5（消费面） | 已超 |
| D5 | worker 超时收尾 settlement：deadline→停领→drain 90s→终局一轮→CAS 终态+SDK 强制写回（深读1:18；部拆 B.1.5） | 战后 settle 有（battle.py settle 判分归因，scripts/battle.py:9）；**战中 deadline 收尾轮无**（stall 只会击杀，cli/tanyin-runner:176） | 中 | runner 加 deadline 档：预算 hours 剩 10%→directive 注入收尾令（"停止新探测，写回 insert_assets/record_fact 后总结"——与它 settleWrapUpPrompt 同义但走指令通道）+宽限后 kill；EXIT 行记 settlement 标记 | **W5（规格补点）** | 真空白→已给方案 |
| D6 | 双图架构（资产图全局+探索图每任务+锚点反查覆盖度）（手册:60-77） | 资产/意图/事实/发现全在 13 表（assets/edges/intents/facts/findings）+anchor 命令（49 面内）；跨战共享=同账本 | 形态异（单库 vs 双图） | 已对等：anchor 桥=我们的 edges（dedup_key 程序算）；覆盖度反查=graph-neighbors/graph-paths 已有 | — | 已超（同库+哈希链比它 45 表零防篡改强，深读0:16） |
| D7 | compactor 冷压缩（digest 超级节点+minor/major 折叠+expand 还原）（活访:82；部拆 B.1.3） | 无上下文压缩（会话=阶段制短会话；opencode 自带 /compact） | 中（长战需要） | 阶段制=天然免压缩（P1-P6 各自短会话）；W5 常驻规划者长会话需预算：每 N 轮把已完成意图收口成 digest fact（record-fact kind=digest）——**digest 也入账**（它 digest 只在图，我们入哈希链） | W5（规格补点） | 已排（W5） |
| D8 | worker 过程交换 search_all_worker_traces/get_worker_trace（手册:80；部拆 B.1.2） | trace_search 已建（字面子串跨 runner 日志+timeline，防 ReDoS 无 regex，cli/ledger/trace_search.py:4-14）——v0.8 Task C 借的就是它 | 小（已有等价） | W5 多战士后扩 intent 定界（--intent-id 过滤）；给战士挂只读查询工具（dsh 插件 v0.2 面） | W5 | 已超（防 ReDoS 设计）+已排（多战士扩） |
| D9 | planner 自愈（把"靶场宕机"写进意图带重试；活动流实证）（活访:45-48） | RESUME_PREAMBLE 恢复协议（cli/tanyin-runner:56-58）+soft stall 观察（:177） | 小 | 自愈主体=W5 常驻规划者提示词（重试语义进派单）；runner 侧已有死亡续跑 | W5 | 已排 |
| D10 | 意图正文带 ROE 红线（"不打公网/只读优先/写须可逆"进派单）（活访:66） | 任务书八问+AGENTS-INJECT 八条常驻注入（hosts_matrix.py:7-10）——红线在**系统级注入**不在派单 | 小（层级更硬） | W5 派单模板加红线段（从 constraints.tsv 生成，账本单源） | W5 | 已超（系统级>提示级） |
| D11 | retester 独立复测会话+结论回写处置（手册:258-259；部拆 B.1.4） | tanyin-replay 机械重放+三态+REPAIR 候选（B32 行）；复测常驻岗 W5 | 机械面已超 | 见 B32；LLM 第二意见=可选插槽 | W5 | 已超+已排 |
| D12 | 发现纪律：版本指纹匹配 CVE 不许报、嫌疑走 fact confidence=inferred（部拆 B.1.4；worker.go:240 提示红线） | FD 卡 confidence/impact 双轴+P4 重放门+unverified 不入卷（report_artifacts.py:12-13 SARIF 仅 verified） | 已超（机械门>提示红线） | 保持；W4 白盒车道 B 证伪卡再加深 | W4 | 已超 |
| D13 | 流量三件套工具注入（traffic_search/get/blob，开捕获才注入）（部拆 B.1.2；手册:411） | 无流量库故无工具；EV 卡 raw_request 即证据源 | 取舍 | W6 三源回传后：EV 检索工具卡（复用 trace_search 面）给战士查历史请求（防重复 curl 同义） | W6 | 已排 |
| D14 | planner 监督 kill_work/steer_work（部拆 B.1.1 planner.go:119-125） | say 指令通道+stop 杀组（server.py:585-598）+intent 级暂停（B20 排期） | 小 | kill_work 等价=stop --intent（杀单意图进程）；steer=say --intent 定向留言（B20/W5） | W5+W6 | 已排 |
| D15 | 活动类型学（12 型+seq/worker/is_error/usage 记账帧）（手册:477-478） | timeline 7 列（schemas）+runner.tsv 事件轨——型少但**每行入链**（它 activity 写失败 3 次即丢，深读0:17） | 小 | 型扩展随 W6 各页投影（不改账本列，投影层分类）；usage 记账=B41 llm-records.tsv | W6 | 已超（不丢帧）+已排（类型学） |
| D16 | 状态语义中枢 status.ts 九域集中（手册:469-472） | 词表=shared/VOCAB.md+contracts+11 词汇修正案冻入（蓝图 D-d） | 小 | W6 11 类词汇全量上图（蓝图:79 验收线） | W6 | 已排 |

### E. intercept/judge 治理深读（4 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| E1 | 判定链：资产拦截→规则→judge→ask pending（手册:391,494-507） | Tier1 guard→Tier2 hooks（enforce 同源 cli/ledger/enforce.py:1-18）→Tier3 egress ACL——**三层全 fail-closed 全落链** | 已超（纵深）；ask 缺（B55 已排 W2） | 保持三层；补 ask（B55） | W2 | 已超+已排 |
| E2 | 全 agent ModeBypass+guard 单点+interceptor nil 即裸奔（深读3:8,33）——**它的洞** | 三层独立单源+模拟验证（tanyin-canary probe 四档位，cli/tanyin-canary:18-24） | 已超 | 保持；canary probe 进 CI 每夜（W7 夜回归） | W7 | 已超 |
| E3 | judge fail_action 默认 allow+judge 自审自批无独立性（深读3:33,36） | judge_client fail-closed (None,reason)（judge_client.py:7-9） | 已超 | 接线时强制独立 profile（judge 用备用配置，不与战士同模型——它没做的独立性） | W2（接线时） | 已超 |
| E4 | 审批执行输出回填+ambiguous 并发不展示推测（手册:401,506） | approve 后无执行回填（我们审批的是清理命令=已执行事的追溯） | 语义异 | pre-exec ask 落地后自然获得回填（裁决→执行→输出→闭行）；我们比它多：执行结果入链 | W2 | 已排（随 B55） |

### F. 通知（3 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| F1 | notify 包 26 文件 6 渠道无状态（手册:564,376；深读4:21） | 无 | 大 | B53 方案（channels.tsv+notify-cli+timeline 先落账再发） | **W7 扩** | 真空白→已给方案 |
| F2 | realtime/digest 模式+状态过滤+rate_per_min（手册:376） | 无 | 中 | digest=notify-cli digest --since（聚合账本事件）；过滤=事件谓词列；限速=滑窗复用 enforce.rate_window 单源 | W7 | 真空白→并入 W7 |
| F3 | 未知严重度不推（存疑不推）（深读4:21） | 精度门哲学同构（蓝图:7 未验证不入卷） | 0 | 同律写入 notify 触发谓词（confidence 非 verified 不推）——两家共识直接继承 | W7 | 已超（哲学同源+入链加成） |

### G. ScopeSentry 同步（1 件）

（并入 B43：声明取舍+W7 可选已排。）

### H. LLM 池（4 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| H1 | 链序=激活→priority DESC+pool_exclude+绑定兜底（手册:322-331；深读4:7） | 判定核有同构（order/lane/bucket，llmpool.py:42-49）；profiles 无 | 中 | B45 profiles 表+sidecar 实链（B47） | W2+W6 | 已排 |
| H2 | 熔断进程级+落库+重启恢复未过期窗+立即恢复（手册:331；深读4:10） | goal 钉根 state 文件+事件入 timeline（llmpool_wire.py:7-14） | 小（已有） | reset 面板钮（B46） | W6 | 已排 |
| H3 | llm_switch/failover SSE→toast+任务头链钮+耗尽红 Alert（手册:348） | failover 事件已在 timeline（wire:11）；无 toast/头钮 | 小 | SSE 换代后事件推 toast；battle 头链钮=B11 | W6 | 已排 |
| H4 | llmrec 每调用记录同池限流（部拆 B.1.1） | B41 排期（llm-records.tsv） | 中 | 同 B41 | W1+W6 | 已排 |

### I. 报告与导出（2 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| I1 | 报告=发现 summary 直渲染+复制（手册:270-271；活访:112"无独立报告编辑器"） | FD 九段渲染+词表门+双轴+时间链断言（report_render.py:2-10,351）+签发面 P5 | **已超（内容与门）** | 页面化=W6 报告页（B36）；保持复制+加下载/品牌（W6 客户隔离+报告品牌） | W6 | 已超 |
| I2 | findings export 平面导出（手册:279） | findings_json 全量+生命周期三桶+findings_sarif 仅 verified（report_artifacts.py:4-16） | **已超（格式族）** | 保持；zhulong-export 互通第二出口已有 | — | 已超 |

### J. 数据层（3 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| J1 | PostgreSQL 45 表+启动幂等迁移（手册:19；深读0:8） | 13 TSV+哈希链+文件锁+原子整替换（timeline.py:1-14 单源写方） | 形态取舍 | **声明取舍**：账本=法（可签名可第三方验），TSV 至万行级无瓶颈（诚实上限：单战千行×百战=查询走 query_cmds 线性扫，跨战透视若慢→加只读 sqlite 投影层（tanyin-viz --data-only 先例），**投影不换真源** | 可选（W7 附带评估） | 声明取舍 |
| J2 | kind×state CHECK+rel 白名单（深读0:36"比想象严"） | schemas.py 列校验+边方向 _EDGE_DIR 代码强制（深读0:20"对比我们代码强制"） | 已超 | 保持 | — | 已超 |
| J3 | 零防篡改（深读0:16 双源实锤"改库=改史"） | 哈希链+verify-chain+hash-recheck+checkpoint（49 面内 4 命令） | **已超（核心护城河）** | 保持 | — | 已超 |

### K. 部署形态（4 件）

| # | ARTEX 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| K1 | install.sh 一键+docker compose+镜像（手册:552） | git clone+零 pip 依赖（README:30-33）+tanyin-install（cli/tanyin-install）+五宿主矩阵（install/hosts/） | 中 | compose 打包：webui+runner+egress 三进程一 compose（数据卷=~/.tanyin）；镜像 CI 构建（.github 已在） | **W7（扩：发布件）** | 真空白→已给方案 |
| K2 | Releases 二进制+start.sh 守护拉起（手册:552） | launchd 模板有（install/launchd）+battle.py --caffeinate | 中 | pyinstaller 单文件（或 zipapp .pyz——零依赖栈最配）；start 守护=launchd/systemd 双模板成品化 | W7（发布件） | 真空白→并入 W7 |
| K3 | 一键自更新：下载→SHA256SUMS→冒烟→换装→3 连败回滚（手册:410,554；深读4:12） | tools.lock+ECDSA 验签（supply_chain.py:1-8——**发布者身份它没有，深读4:36 点名**） | 自更新=空白；验签=已超 | 自更新=版本清单（带 ECDSA 签名）→下载→tools.lock 式验签→selfcheck --static 六项当冒烟（cli/tanyin-selfcheck:8-11）→换装→失败回滚 .old；**比它多签名验真** | W7（版本面+runbook 扩） | 真空白→已给方案 |
| K4 | 反代 SSE proxy_buffering off 运维注记（手册:555） | X-Accel-Buffering:no 头已发（server.py:340） | 0 | 文档化进 W7 runbook | W7 | 已超（头已发）+已排（文档） |

---

## 二 · 判词汇总

| 判 | 件数 | 代表件 |
|---|---|---|
| 已超 | 14 | J3 哈希链 vs 零防篡改、E1-E3 三层 fail-closed 治理+canary、I1/I2 报告九段+SARIF、D4/D6 链在账、D8 trace 防回溯、D12 发现纪律机械门、D15 不丢帧、H 已超两洞（抖动/分道）、K4、F3 |
| 已排 | 52 | 21 路由绝大多数（W6）、ask 三态+judge 接线（W2 扩）、常驻规划者/intents 租约/多战士/复测岗（W2/W5）、三源回传（W6）、webhook→6 渠道框架（W7 扩）、发布件（W7 扩） |
| 声明取舍 | 8 | B39 MITM CA（TLS 不解密）、B43 sync 优先级、B50 MCP 插槽对等、B51 zip 上传（git 单源）、B61 日志清空（只增律）、C-1 API 数量（双面一等公民形态）、J1 postgres（TSV 账本律）、A4 多账户（单操作员+W7 RBAC） |
| 真空白（全部给方案，无一悬空） | 22 | **A3/C-2 读面鉴权（P0，W1）**、B47/H1 池实链（W2）、B55/B57/E4 ask 三态+judge 接线（W2）、B63 web 搜索源（W3）、B7/B8/B9/B10 对话页子件（W6 规格）、A1/A2/A4 setup/条款/改密（W6）、B14/B16/B17 批量/删除/归档（W6）、F1/F2 通知框架（W7）、K1/K2/K3 发布件（W7）、D5 settlement 收尾轮（W5 规格） |

---

## 三 · 新增缺口清单（此前任何波次都没排的件——一件不许漏）

> 判据：W1-W8（蓝图:22-29）与 §四b（蓝图:41-63）逐字核对，未点名者入本清单。全部给方案与建议波次（原则：能并入现有波次则并入，不滥开新波）。

| # | 缺口件 | 危害 | 方案（可施工） | 建议波次 |
|---|---|---|---|---|
| G1 | **WebUI 读面零鉴权**（9 页+5 API+SSE 无会话校验，server.py:255-292；登录页对读面是装饰） | 8900 端口可达者可读全部战况/发现/证据并追 SSE——对照它 JWT 全覆盖（手册:23）是硬伤 | do_GET 全路由挂 _session_ok()（11 处）+页面 401 跳转+SSE 签名查询参数（C-2） | **W1（serve 收口范围点名扩）——P0** |
| G2 | llmpool 实链接线（判定核未接真实请求，无消费者） | 五层重试只是纸面；战士请求仍裸走 opencode | sidecar 本地反代接 opencode provider（重试/熔断/链切换在 sidecar，事件经 wire 入 timeline） | W2（引擎地基扩） |
| G3 | pre-exec ask 三态 + judge 接线（guard 只有放行/拒；judge_client 零消费者） | 高危动作无"转人工"档；judge 投资闲置 | guard 输出 ASK+pending.tsv+双面裁决+超时默认拒；judge 在规则未命中高危时前置（fail-closed 拒） | W2（多战执法面扩） |
| G4 | 网络搜索源（四源 vs 零） | 战士无 OSINT 情报输入 | web-intel 工具卡（ddgs 免 key 先行，tavily/brave 插槽参数；出网过 Tier3） | W3（工具卡族扩） |
| G5 | 战中 deadline 收尾轮（settlement） | 预算尽只有击杀，无"写回后收口"优雅态 | runner 预算剩 10% 注入收尾令+宽限+EXIT settlement 标记 | W5（常驻规划者规格补点） |
| G6 | digest 战地压缩入账 | W5 长会话上下文会爆 | 每 N 轮 record-fact kind=digest（入哈希链，它 digest 只在图） | W5（规格补点） |
| G7 | 通知 5 渠道+投递记录/重试/test（蓝图只排了 webhook） | 企业告警面缺位 | channels.tsv+notify-cli（先落 timeline 再发）+deliveries.tsv 五态 | W7（扩：webhook→框架） |
| G8 | 发布/部署件：docker compose+release 工件+自更新 | 15 分钟开箱 demo 没有物质基础 | compose 三进程+zipapp/pyinstaller+签名版本清单+selfcheck 冒烟+回滚 | W7（版本面扩：发布件） |
| G9 | 归档冷存储+还原依赖检查+删除范围选项 | 战役堆积无生命周期 | tar+zstd+manifest 归档/还原校验；purge 显式旗标 | W6（多战场切换器扩） |
| G10 | 批量操作面（暂停/归档/分类） | 多战运营手工 | battle.py batch 子命令+Web 复选框（双面同源） | W6（扩） |
| G11 | 会话级/battle 级 LLM 热切换+头链钮 | 换模型=改配置重启 | goals model_tier amendment+runner 重启战士；头钮读 resolution | W6（llmpool 管理页扩） |
| G12 | 对话页子件：@实体引用/附件/btw/IME（§四b 只写了"介入对话页"四字） | 对话页做出来也到不了它的运行时水位 | @菜单吃账本 ID；附件 sha256 入链；btw=只读问答；IME 3 行 | W6（介入对话页规格扩） |
| G13 | per-agent 可见性矩阵 | 工具面全开无差别 | 工具卡注册表 agents 列+guard unknown-tool REJECT | W3+W6（扩） |
| G14 | /setup 初始化向导+改密 UI+条款确认闸 | 首启体验与合规确认缺位 | 三步向导+password API+滚动闸（确认落链） | W6（设置页扩） |
| G15 | 系统日志页（webui/runner 运行日志只读+级筛） | 排障面缺 | logs/webui.log 投影页（清空不做=只增律取舍） | W6（扩） |

**波次总量修正建议**：W2 +~600 行（G2/G3）、W3 +~400 行（G4）、W5 规格补点（G5/G6 计入常驻规划者 MVP 工程量）、W6 +~1800 行（G9-G12、G14、G15）、W7 +~1200 行（G7、G8）；合计较蓝图 §四b 修正后的 4.6-5.5 万行再增 **~4000 行**。**不新开 W9**——所有缺口均有归宿波次。

---

## 四 · 证据可复核性声明

- 对方每件的出处行号均为本档开头所列语料文件的实读行号（手册 565 行全文通读；活访 136 行全文；视觉 145 行全文；深读/部拆按节引）。
- 我方每件的出处为仓内文件实测行号（2026-10-18 快照；49 命令清单经 registry 实跑枚举验证）。
- 本档为唯一写入件；语料与代码零改动。发现的我方活 bug 两处照实记录：session 页 TypeError（2c:81 引，未复测是否已修——**留给 W6 开工首日核**）与 graph 页标签重复 4 次（2c:83 引）。

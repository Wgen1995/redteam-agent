# 03 · 产品形态与前端工程评审（ARTEX 式平台目标 vs 纯手写零依赖律）

> 评审人镜头： 产品+前端工程。靶项目 /Users/wgen/redteam-agent（探隐）。
> 依据材料： docs/design/tanyin-product-v1.md（宪法+修正案ABC）/ BLUEPRINT-RECON.md / tanyin-target-form.md（语言律）/ ui-design-v1.md / docs/superpowers/plans/2026-10-15-v09d-ui.md（冻结计划）/ HANDOFF.md 尾 10 节 / cli/webui 全量 / tests/test_v09d_skin·session·zhulong.py / docs/research/liveui 相关报告。
> 纪律遵守声明： 只读代码零 git，仅写本档。评审时点 2026-10-15 23:3x，v0.9d 三舰在航（index 等五页已换肤 22:57、session_view.py 23:21、server.py 仍 0.9c、session.html 未落盘）——本档按在航快照评，不把中途态当终态罪证，但在航态本身暴露的问题照算。

---

## 【总判决： 方向对，执行偏航，置信度 82%】

产品定义 v1 的转向（AI 自动化渗透为最大目标、审计降为地基、浏览器全程、CLI 退引擎层）方向正确且已被用户原话钉死，不重议。偏航不在战略，在四个执行决策： 一是设计档与代码当天断裂（侧栏+12 级灰阶冻结了、交付的是顶栏+8 级）；二是页面完全自包含律把手写前端锁进 N 份字节级复制的维护税，而 2000 行律量的根本不是这个轴；三是 v0.9d 一批塞三异构舰，已经漏出八链导航三条死链被测试合法化这种伤；四是人话律的执行强度（钉两个 token）配不上黑话清零的宣称。每条都有代码级证据，见下。

狠话在前： 这个项目最大的工程优势是决策都落档、落档都可查——所以当 BLUEPRINT-RECON 立律当天，冻结计划引用了宪法却没引用同日冻结的 ui-design-v1.md，实现交付的东西跟设计档不一致，这不是小瑕疵，是治理闭环第一次空转。第二次空转就不会只伤 UI。

---

## 【发现，按严重度降序】

### F1（严重）设计-执行当天断裂： 侧栏骨架+12 级灰阶冻结于档，交付顶栏八链+8 级灰阶，引用的 wireframe 不存在

**现象**： ui-design-v1.md（2026-10-15 定稿，自称 v0.9d 执行依据）冻结的骨架是左侧栏（三分组）+顶栏（战局切换器/通知/明暗切换）；令牌承诺灰阶 12 级结构（借 ARTEX 层次）。实际交付（cli/webui/static/ 五页，22:57 版）： 全部是 header 顶栏 nav 八链，grep sidebar/aside 零命中；:root 共 13 个 CSS 变量，灰阶族只有 8 个（--bg/--card/--ink/--dim/--line/--soft/--idle/--skeleton，其中 --soft 还是蓝 tint），测试 CORE_VARS 也只钉这 13 个。

**证据链**：
- docs/design/ui-design-v1.md L5-8（骨架与令牌承诺）；
- docs/design/BLUEPRINT-RECON.md 对账表行： ui-design-v1.md | 现行 | v0.9d 执行依据（侧栏骨架+12 级灰阶）；
- docs/superpowers/plans/2026-10-15-v09d-ui.md 依据行只列 tanyin-product-v1.md + liveui 五报告偷单 + walk-tanyin 痛点清单——不含 ui-design-v1.md；
- docs/research/liveui/2b-artex-export-ui.md 明确写 v0.9d 顶栏八链改为侧栏（页面将超 10 个）；
- ui-design-v1.md 称 wireframe 见 HANDOFF 2026-10-15 行（ASCII），grep HANDOFF.md 全文无此 ASCII 图；
- tests/test_v09d_skin.py 的 TestZhulongFireSkin 只钉变量名成对与品牌蓝，不钉灰阶级数。

**为什么危险**： 立蓝图巡检律的同一天，自己的冻结计划绕开了冻结设计档，实现又与设计档冲突，且没有任何一处回写修档。三道闸（设计档、计划、测试）全部放行。侧栏不是美学问题： 2b 报告论证的是页面将超 10 个时顶栏八链在信息架构上失效——而产品路线 v1.0b/v1.0c 恰恰要再加登录/向导/审批/报告/设置 5 页以上。现在不做，将来是全站第二次换版。12 级变 8 级则是决策数值根本没进代码的直接证明。

**修正方向**： v0.9d 收口前二选一并落 HANDOFF： A）补侧栏改造+灰阶升 12 级（推荐，页面破 10 前的最后便宜窗口）；B）正式修 ui-design-v1.md（顶栏保留至 v1.0b、灰阶 8 级定版）并写明理由。同时把不存在的 ASCII wireframe 补上或删引用。测试侧： CORE_VARS 加灰阶级数断言，NAV 断言加侧栏或顶栏形态钉。

### F2（严重）自包含律制造 N 份字节级复制税；单页 2000 行律量错了轴——手写数学在 12 页以上平台形态下靠复制粘贴维持

**现象**： status.js（105 行单源）以 91 行字节级副本内嵌进全部五页 head，测试 TestEmbeddedCopySync 强制五页副本与单源逐字节相等；五页共有非空行 157 行（约等于 coverage/graph 页身的 44% 是共享样板）。status.js 文件本身躺在 static/ 目录里不被任何路由 serve——它是只为复制而存在的死文件。

**实测数据（cli/webui/static/，v0.9d 换肤后）**：

| 页 | 总行 | head 到 /head（样板） | 页内 JS（含 91 行副本） |
|---|---|---|---|
| index.html | 612 | 228 | 386 |
| metrics.html | 469 | 191 | 313 |
| evidence.html | 401 | 178 | 277 |
| coverage.html | 361 | 183 | 224 |
| graph.html | 358 | 165 | 241 |

**平台形态逐页估算**（D4+v1.0b+v1.0c+八视图基线所需，按现密度外推；ARTEX 同功能件行数作锚）：

| 待建页 | 估算行数 | 锚点 |
|---|---|---|
| /session 会话页（只读，在航） | 550-750 | ARTEX sessions-tab 2205 行（成熟度 5/5），探隐只读版约其三分之一 |
| /activity 活动流独立页（nav 已链） | 450-650 | ARTEX transcript 分组渲染器 |
| /experiments 实验页（nav 已链） | 250-400 | 从 metrics 节拆出+登记表 |
| /login 登录页 | 180-300 | ARTEX (auth)/ login+setup |
| 建项目向导（多步表单） | 600-1000 | ARTEX 任务中心 3417 行的下限切片 |
| 战局列表+切换器 | 350-600 | 顶栏切换器+卡片列表 |
| 审批卡页（v1.0c） | 500-800 | ARTEX InterceptCard 38KB 组件 |
| 介入框（v1.0c，写路径） | +300-500 | Worker 三件套 |
| 报告页/下载 | 250-450 | ARTEX reports 3/5 |
| 设置页 | 300-600 | LLM 池可视化等 |
| 新增小计 | 约 3700-6000 | 现存五页合计 2201 行 |

**数学结论**： 每页 JS 永远到不了 2000（现在最大 386，向导/审批满打满算 800-1200）——单页 2000 行律在平台形态下永不触发，它守的是不会发生的风险，没守正在发生的风险： 跨页共享代码的复制份数乘页数。到 14-15 页时，head 样板 165-228 行每页乘 15 约 2500-3400 行纯复制体，每次改令牌/导航/状态语义等于 15 文件联动+测试同步。walk-tanyin 第三节记录的 7 处漂移（版本三态不一致、导航漂移、--idle 单页缺失）正是 5 页时代复制粘贴的病历——已经付过一次学费，v0.9d 的答案是更多字节钉，而不是消除复制。

**根因证据**： status.js 头注自述理由： 常驻 0.9c 老进程无 /status.js 路由，页面必须完全自包含，不得外链引用本文件。这是把开发期场景（改静态文件时旧 server 进程还活着）烙进产品架构。生产部署是 clone 后 serve，版本变更等于 git pull 加重启，老进程 serve 新页面在产品里不存在。

**为什么危险**： 每个新页都要手工复制 165-228 行样板起笔，新增页面的边际成本不降反升；字节钉测试只能保证复制得一样，不能保证该同步的都同步了（导航就是反例——五页 nav 一致，但一致地链向三个 404，见 F3）。

**修正方向（均不破零构建零 node 律）**：
1. server.py 加通用静态句柄： 对 static/ 目录白名单后缀（.js/.css）做映射 serve，URL 带 ?v=0.9d 破缓存，约 6 行 stdlib；配升级须重启的部署纪律一条。CSAI（同律零框架、29 页、7812 星生产级）就是这么干的： 45 个业务 JS 模块运行时 script src 引用+47221 行共享 style.css——docs/research/liveui/3-cyberstrike.md 第 1.1-1.2 节全写着，是库里现成的存在性证明，被无视了。
2. 或走请求时装配： Python 单源 shell 模板+每页内容片段，_serve_page 请求时拼装（无构建链、无 node，服务端 stdlib 字符串拼接）。现有 _serve_page 本来就读盘，只差一层模板。
3. 律的修订（走修正案程序）： 语言律的触发器从单页 JS 大于 2000 行，扩为单页 JS 大于 2000 行或跨页共享前端代码复制大于等于 3 份——后者今天已经 6 份。

### F3（严重）v0.9d 批次过载，已漏出成品伤： 八链导航三条死链，测试把死链合法化

**现象**： 五页 nav 均含八链（/ 、/activity、/session、/coverage、/graph、/evidence、/metrics、/experiments）；server.py 实际路由只有五页。/activity、/experiments 无页面文件且冻结计划里没有任何任务创建它们；/session 属 Ship S（在航未落盘）。test_v09d_skin.py 的 TestNavEightLinks docstring 自白： 只断言存在不断言通。

**证据**： cli/webui/server.py do_GET 路由分支；cli/webui/static/ 目录清单（仅 5 个 html+status.js）；2026-10-15-v09d-ui.md Ship U/S/Z 三节全文无 activity/experiments 页任务；tests/test_v09d_skin.py NAV8 集合与注释。

**为什么危险**： 界面大改批交付的界面上 8 个导航 37.5% 是 404，用户对平台的第一印象就是断链。死链被钉进测试后，将来补路由还要先改测试——测试从防漂移钉变成了漂移钉。批次对比自身历史： v0.9b 是三页、v0.9c 是一页，v0.9d 是全站换肤+首页重做+新页+带网络推送的 CLI 互通（Ship Z 涉及真实凭据登录与 POST push，和换肤完全是两个风险域）三异构舰共用一个版本号。收口时要么砍范围要么带伤验收，没有第三条路。

**修正方向**： 一，nav 收回到实际存在的页（或死链加禁用态+即将上线样式），NAV8 测试改为每链必可达（对 make_server 发请求断言非 404，本地零网络）；二，/activity、/experiments 落入 v0.9e 种子；三，此后 UI 批与网络/CLI 批不共版本收口。

### F4（高）人话律执行强度与宣称不符： 律只钉两个 token，页面残留统计与自造黑话

**现象**： test_v09d_skin.py 的 TestPlainLanguageLaw 仅断言 page-sub 含你在看什么和不含 E-index。实际抽查（术语计数）： metrics.html 残留 McNemar 3 处、两臂 2 处、预登记 4 处、池化；coverage.html 消格 3 处、置格 3 处、冻结锚点 2 处；五页均残留 P5.5、哈希、sha8 等内部词；index 活动流直出 checkpoint/gate/replay-probe 裸事件名。正例也真实存在： 五页副题质量高（你在看什么句式确实是人话），wstg 星号表头已清零。

**证据**： 术语 grep 计数（见现象）；metrics.html L203 统计卡标题含 各臂均值/池化 McNemar、L211 预登记实验标题含 experiments/*.tsv 文件路径与 无登记不认——tsv 路径直接进 UI 标题。

**为什么危险**： 产品定义 D4 的用户画像是人只做介入放行决策——这位用户不是统计学家，池化 McNemar p=0.125 对他等于黑箱。人话律是产品身份级的承诺（写进 ui-design-v1 和计划两处），如果执行就是钉两个 token，承诺贬值成话术。

**修正方向**： 建 UI 禁词替词表（McNemar 换成 两臂差异是不是运气 的显著性检验、池化换 合并全部战例算、消格换 已覆盖、置格换 已测、预登记换 开战前登记的实验）+ 首现处一句话解释；禁词表进 test_v09d_skin 断言。保留术语可以，但要么带解释要么进悬浮——现在这样宣称清零加实测残留最伤。

### F5（中）总览最新发现未复用库里定稿的发现流规格——蓝图巡检律钦点的复用项被空转执行

**现象**： BLUEPRINT-RECON.md 结论行明令 v0.9d 总览页复用 fd-report-card-spec 与 finding-stream-priority。finding-stream-priority.md 第一节规定实时流字段为 时间/资产/类型/severity/状态，且高危置顶+标记；ui-design-v1.md 规定最新发现列表点击跳证据卡。实现 renderLatest： 徽章+EV id+标题+linked_finding 四件，无 severity、无高危置顶、列表项是 li 不是链接（不可点）；测试只钉 id 为 latest-findings 存在。

**为什么危险**： 总览页是 D4 用户八成时间停留的页，最新发现是他最关心的流。丢掉 severity 置顶等于值班者要自己从 8 条里扫出高危。这也是巡检律立律后第一个查了库、引了档、落地没跟上的案例——和 F1 同病。

**修正方向**： renderLatest 按 finding-stream 字段集补齐（severity 徽章/资产/时间），高危置顶；每项包链接跳 /evidence 锚点；evidence.html 补锚点定位。半天的量。

### F6（中）竞品可感知差距清单——换肤批在用户可感知轴上位移不足，需进路线图显式管理

基于 docs/research/liveui/ 报告（ARTEX 27 项功能评分、CSAI 30 项、walk-tanyin 14 痛点），用户可感知差距 Top（非功能全集，只列用户一眼或一次操作内可感的）：

| 序 | 差距 | ARTEX/CSAI 证据 | 探隐瞒现状证据 |
|---|---|---|---|
| 1 | 无法从浏览器开战（对话式/表单式都没有） | CSAI 对话式开战 5/5（live 会话标题即渗透任务）；ARTEX 对话 5/5 含 @ 引用 | server.py do_GET 纯只读，零写路由 |
| 2 | 无登录/初始化 | ARTEX 认证 4/5（JWT/init/改密）；CSAI RBAC 5/5 | 无鉴权，127.0.0.1 绑定是唯一防线（walk-tanyin 已记录被 ARTEX live 意图列为撞库目标） |
| 3 | 无审批卡（自主性的信任瓶颈） | ARTEX 审批拦截 5/5（三形态卡+深链+审计快照）；CSAI HITL 5/5 | 无（v1.0c 计划） |
| 4 | 无报告下载 | ARTEX 报告 3/5；CSAI 漏洞管理全周期 5/5 | 报告在账本目录里，UI 无入口（D4 承诺报告下载） |
| 5 | 活动流是平铺文本 | ARTEX transcript 分组渲染器（命令加成败态配对折叠） | index feed 为 时间戳+事件名+sha8 单色流 |
| 6 | 数据页全量重刷 | ARTEX 单 SSE 多路分发+seq 去重+snapshot 衔接 | coverage/graph/evidence 均 setInterval 10 秒全量重拉，hover 态被刷掉（grep 实证） |
| 7 | 十边图无 digest/聚焦 | ARTEX 探索链路图 digest 超级节点 | 192 节点纵向 2173px 硬滚（walk-tanyin 实测） |
| 8 | 无移动端/通知/无障碍 | ARTEX 移动端与无障碍 4 分档、CSAI 通知 4/5 移动 4/5 | 全无 |
| 9 | URL 不承载状态（可分享/回溯） | ZhuLong URL query SSOT（前进后退还原） | 仅 hash 片段过滤，query/前进后退无 |

**为什么危险**： v0.9d 换肤+总览+会话+互通做完，上表 1-4 一条不动——用户打开产品，感知仍是一个只读仪表盘皮肤变漂亮了。产品叙事是 ARTEX 式平台，用户可感知里程碑却全部压在 v1.0b/v1.0c。不是要提前做，是要在路线图里把用户可感知作为批次验收维度显式声明，否则连续几批工程大进展、用户零感知，共创模式下的用户耐心会被消耗。

**修正方向**： 路线表加一列 用户可感知变化；v0.9d 收口通报里明确告知本批为观察面基座、开战入口在 v1.0b。

### F7（低）四态/动效/预算预警等本次已做对的，点名保住

status.js 语义单源（抄 ARTEX status.ts 语义不抄代码）、四态纪律、KPI 可点过滤（hash 深链）、预算超 80% 变红、动效预算全站小于等于 3 有测试钉、门灯呼吸、textContent 防注入、浅色默认+深色镜像防白闪——这些是 walk-tanyin 痛点清单里红级项的真闭合，质量高于同类手写项目。收口时不要为了赶 Ship S/Z 回退这些。

---

## 【被忽视的既有资产】

1. CSAI 零框架大型化样本（3-cyberstrike.md 1.1-1.2 节）： 29 页共用 45 个 JS 模块+共享 CSS+ID 契约+rbac-guards 全局函数包装（400 余写函数不改业务代码加权限门）+41 个 node:test 前端单测。这是语言律不改也能平台化的完整参考答案，v0.9d 却选了字节复制窄路（F2）。后面做登录/RBAC 时 rbac-guards 模式直接可抄。
2. fd-report-card-spec.md 与 finding-stream-priority.md： F5 所述，钦点复用未落地。
3. walk-tanyin 第五节 P0-P2 建议中被静默丢弃的三条： P0.3 URL query SSOT（只做了 hash 片段）、P1.6 SSE 增量模型（仍是 10 秒全量重拉）、P1.4 活动流渲染器（仍平铺）。丢弃可以，但应在计划里写为何不做与何时做，现在是无声蒸发。
4. ARTEX 偷单清单消化台账缺失： 40 余条偷单已消化约五六个（status.ts、四态、KPI 过滤、预算预警、动效、徽章配方），其余（seq 去重、transcript 分组、Token 记账、直播位+未读、假删真删双模式等）没有进任何 roadmap 种子。建议建偷单台账表（条目、状态、去向批次），否则下次方向评审又得从头对账。
5. engine-fusion-architecture.md 第 6 节与 graph-driven-ops.md： v1.0a 双图一桥的现成素材（BLUEPRINT-RECON 已钦点必读），本次评审确认其存在，提醒主会话 v1.0a 开工前先巡检。

---

## 【三问给主会话】

1. 自包含律的真伪问题： 为常驻老进程 serve 新静态页这个纯开发期场景，你准备永久支付每页 165-228 行样板乘页数的复制税吗？server.py 加 6 行白名单静态句柄加升级重启纪律，到底破了语言律的哪一条（零框架/零构建/零 node/离线可用——一条都没破）？如果不接受，请把理由写进 tanyin-target-form.md 修正案，别让 status.js 的头注继续当立法依据。
2. 设计档与代码谁让步： 侧栏+12 级灰阶（ui-design-v1 冻结版）对顶栏八链+8 级灰阶（已落码五页）——v0.9d 收口前必须二选一并回写档或改码。你选哪个？选改档的话，2b 报告 页面将超 10 个顶栏失效 的论证你打算怎么回应？
3. 死链怎么验收： v0.9d 收口时 /activity、/experiments（/session 看 Ship S 进度）三条 nav 死链，你打算按计划内未完成带链验收，还是把 nav 收回到实际存在的页面？如果带死链验收，每链必可达要不要立成下批的钉？另外请回答： 一个界面大改批交付 37.5% 断链导航，在共创模式下你打算怎么向用户解释？

---

评审方法备注： 全部行数、术语计数、路由比对均为本次实测（wc/grep/awk 于 cli/webui/ 与 static/），非转述。未运行测试套件（只读纪律），测试状态引用自文件内容与 HANDOFF 声称的 1328 基线。

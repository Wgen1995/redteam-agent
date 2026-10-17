# C · ZhuLong + multica 全件对齐（逐件表）· 2026-10-18 重对齐

> 执笔：重对齐子代理 C（域=ZhuLong+multica 两家全面）。纪律：语料与代码只读，唯一写入=本档（旧档仅 21 行残骸，按令直接覆盖）。
> 对手语料：`docs/research/manuals/usage-guide-zhulong.md`（下称 **Z:n**，214 行全读）、`docs/research/manuals/usage-guide-multica.md`（下称 **M:n**，353 行全读）。
> 对手源码（双源加强，比手册更硬）：ZhuLong 全仓=`ai-assisted-security-verification-platform`（下称 **ZS:file:line**，只读实勘）；multica=`.research/repos/multica`（下称 **MS:file:line**），其中 `server/pkg/agent/dsh.go` 479 行全文实读（下称 **D:n**）——五产品里唯一一份「别人怎么驱动一个 AI 运行时」的源码级参考。
> 我方仓：`/Users/wgen/redteam-agent`（**GraphLed**，旧名探隐 TanYin；本档快照=main@1cb568a，W1 三舰已合）。波次基线：`docs/design/exceed-blueprint-2026-10-17.md`（下称**蓝图**，W1-W8=蓝图:22-29）。开工令=2026-10-17（HANDOFF.md:1522-1526：C2/WebShell 批做·法律敏感标注·工期 AI 周计）。
> 判词四档：**已超**（超越点实打实）/ **已排**（波次有名有姓）/ **声明取舍**（对等策略，用户知情）/ **真空白**（不许留，发现即给方案）。
> 一句话总判：**ZhuLong 是「我们自己上一代控制台的最完成形态」——管理面（项目/用户/下载/插件注册/远程算力）全有、判据层全无；multica 是「任务面板×AI 员工」的编排体验天花板——但它不是安全产品，且用户已把我们的纪律（授权八问/L0-L3/vault 占位/链式 timeline）移植进 multica 跑通了真作业，证明壳可换、法是我们的。逐件 15 件（ZhuLong 8+multica 7）：已超 4、已排 9、声明取舍 1、真空白 1（被驱动面，方案已给并入 W7）——一件不悬空。**

---

## 〇 先把两家底摸清（各一段话）

**ZhuLong 是什么**（Z:4,13）：Vue3+Hono+SQLite 的「AI 安全验证平台控制台」——项目/对象/环境组织成资产，引擎（插件制）挂算力池（本机探测+远程 runner 令牌）跑任务，会话日志经 mapper 解析成结构化漏洞，三态人工终审收口，下载中心交付。**源码就在本舰工作目录**（ZS 全仓可逐行实勘，本档所有 ZhuLong 件都给了 ZS:file:line 双保险）。它同时是被 ARTEX/CSAI 打的靶场（Z:7,206-208）——它的伤疤就是我们的免费评测集（本档 §三逐条收）。我们已有互通件 `cli/ledger/zhulong_export.py`（五族导出+tanyin@1 引擎，对方仓 mapper-tanyin 已合）——五产品里只有我们同时是它的引擎供给方。

**multica 是什么**（M:11,13）：开源「AI 数字员工」任务平台——CLI 编码代理注册为运行时（Runtime，含 DeepSeek Harness 适配器 dsh.go），运行时之上定义智能体（Agent）编成小队（Squad），用任务（Issue）派工，收件箱/聊天/Autopilot 驱动人机协作。**它不是安全产品**，但把「任务面板×AI 员工真跑×跑在自己电脑上」这套作业编排做到了产品级（118 张表、37 路由+15 设置子页、服务端分页分面、保存视图、看板、收件箱、唤醒规则）。用户已在它上面布置了安全红队 7 agent 编制跑真交战（M:241-307）——用的却是我们的纪律语汇（授权八问/L0-L3/`{{vault:cred-N}}`/链式 timeline/approvals.tsv，M:285-288）。**这证明：编排壳是它的、作业法是我们的；W6/W7 把编排体验补齐后，multica 对我们只剩「别人生态里的一个可挂运行时的宿主」——反而该是我们的分发渠道（见 M7 被驱动面）。**

---

## 〇′ 对初表（10-五产品逐件基线总表:36-53）的校对

初表 ZhuLong 6 行+multica 5 行方向正确，按源码与开工令核后 **7 处须修正/补全**：

| # | 初表原判 | 校对结论 | 证据 |
|---|---|---|---|
| C1 | ZhuLong 节只铺 6 行（六导航/URL/三态/引擎/算力/下载） | **漏 2 件+半件**：用户管理（Z:97-100）、mapper 映射器（Z:119）整件没进表；六导航里的「用户管理」子件也没拆——本档 Z6/Z8 补齐，ZhuLong 逐件才算齐 | 初表:36-44 vs 本档 §一 |
| C2 | URL 深链「部分·W6 切换器」 | **低估现状**：`?battle=N` 选战（server.py:459-460；session.html:541）、`#f=` 筛选深链（evidence.html:426,452 hashchange 联动）、`#f-<FD号>` 发现锚（evidence.html:321）、`/metrics#experiments`（server.py:453-457）已在——**半件在手**，W6 只欠列表页全参进 URL | 仓四处实读 vs 初表:40 |
| C3 | 三态终审「W1+W6 发现库」 | **波次勘误**：W1 四件（授权/launch/serve 收口/auto/D2/VulnClaw，蓝图:22）没有三态终审；三态终审=09-UI P0-4 归 **W6**（09-UI专家:97：`tanyin findings judge/retest`+词面抄 ZhuLong）——初表把 W1 写进去是笔误 | 蓝图:22,27 vs 初表:41 |
| C4 | 引擎插件「W1 VulnClaw 落地」 | **已兑现**：W1-T6 已合（HANDOFF.md:1527-1531；engines/vulnclaw/adapter.py+MANIFEST 十二字段，17 用例绿）——判词从「已排」升「**半件已落地**（注册制在册 5 引擎，管理页仍欠 W6）」 | 仓 engines/ 实勘 vs 初表:42 |
| C5 | 远程 runner「声明取舍（单机先行）」 | **维持取舍但须补设计约束**：ZhuLong 的接入令牌面被攻击者实测注册了假机群 i41/i56/i96（Z:208）——W7 若做，令牌必须绑授权书 sha（本档 Z5 给设计），否则重蹈它的伤疤 | Z:208 vs 初表:43 |
| C6 | multica 收件箱「W7 通知页（webhook 基础上）」 | **只排了渠道**：三级回执流（action_required/attention/info）/归档/unread 角标形态没排（M:90,106-107）——A:G7 通知框架须补收件箱形态规格（本档 M1+G3） | M:90,106-107 vs 初表:49 |
| C7 | multica 节 5 行 | **漏 2 件**：agent 运行时 profile（M:83,154-157；一机多 profile、自定义 CLI 命令+模型）与 **JSONL v1 协议**（D:dsh.go 479 行源码级）完全没进表——后者拆出「被驱动面」真空白一件（本档 M7+G1，方案已给 W7） | M:83,154-157；D:1-479 vs 初表:46-53 |

---

## 一 · ZhuLong 八件逐件表

### A. 控制台骨架与漏洞治理（5 件）

| # | ZhuLong 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| Z1 | **六导航控制台**：顶栏（品牌+全局项目切换「全部项目 ▾」+头像）+六主导航 首页/项目管理/测试任务/漏洞中心/资产管理/用户管理（Z:50；ZS AppShell.vue:400-407；router=index.ts:11-26） | 三组九链+顶栏三件：看战况（总览/动态/对话/测试覆盖/攻击路线/发现）·看战果（战报/实验）·管战场（设置占位）+开战钮/battle 切换器/深浅钮（index.html:251-266,269-286）；服务端 10 页路由（server.py:415-416,446-450） | 管理面=大缺：项目页/资产页/下载页/用户页四页全无；**观察面=我们更富**：攻击路线图谱/双臂度量/实验页它一页都没有；它的「首页」是品牌舞台、日常作业不进（Z:58-59），我们的总览是作战台 | W6 把 9→21 路由铺全（蓝图:79 验收线原文）：资产页/报告页/审批中心/设置页/技法页/工作区页；分组语义保留「看战况/看战果/管战场」（比六平铺清晰）；项目/客户容器=W7 客户隔离（B:A6 同源） | W6+W7 | 已排（管理面）+**已超**（观察面三页它没有） |
| Z2 | **URL-SSOT 深链**：`?tab=`（资产五页签）/`?status=`（任务七桶 KPI 点击即写）/`?verdicts=`（漏洞三态卡）全部深链可达，URL 即状态（Z:50,78；ZS TasksView.vue:714,786-787；VulnsView.vue:697-736,758；AssetsView.vue:1） | 半件在手：`/session?battle=N`（server.py:459-460；session.html:511,541）、`#f=reproduced/not-reproduced/empty` 筛选深链+hashchange 联动（evidence.html:426,452；coverage.html:364,372）、`#f-<FD号>` 发现锚（evidence.html:321）、KPI 卡=深链入口（index.html:312-315） | 列表筛选态未全量进 URL（evidence 只有三态 hash 预设，无全参 query）；无页签型深链；无「按此战筛选」跳转件 | URL-SSOT 律写进 W6 各页规格：列表筛选/分页/排序全进 query（pushState 免刷新），分享 URL 即复现场景；**超点**：深链可带 timeline 行号锚——演变回放条（蓝图: 旗舰件）让「任意历史时刻」也可深链，它做不到（它的 URL 只锚现状不锚历史） | W6（切换器+资产页+发现库同批） | 已排（半件在手） |
| Z3 | **三态终审+详情三列**：三态=疑似/确认是/确认非（Z:76-82；ZS enums.ts:80-82 `VERDICTS=['pending','confirmed','refuted']`；findings.ts:49-50 PATCH /api/findings/:id/verdict 三态任改含改回）；详情=三列骨架 140 章节导航｜中六章正文｜260 终审卡（Z:79-80；ZS VulnDetailView.vue:1,30,124）+标注时间线+误报原因五词（ZS enums.ts:93） | **账本面已超**：findings 19 列含 status/exploitation_status/schema_version（schemas.json 实读）；未验证不入卷（SARIF 仅 verified，report_artifacts.py:12-13）；机械重放三态+REPLAY_CAP=3（tanyin-replay:17,39）；P4 门 PASS 才算战毕（tanyin-runner:123-134）；supersede 墓碑。**UI 面零**：无终审卡/标注时间线/确认率 KPI（09-UI:57 实骂「无终审无复测」） | UI=大（账本=已赢）；词面已定：疑似/确认是/确认非照抄（09-UI:97） | W6 09P0-4：`tanyin findings judge <FD> --verdict` 命令+发现页终审卡+确认率 KPI+「重新判定」；复测钮走 rerun 门（gate reset，Z:74 同语义）。**超点**：它的终审=纯人手点，我们的判定可由机械重放背书（W5 复测常驻岗对 REPAIRED 候选自动排队）+判定行入哈希链（它 SQLite 改库=改史） | W6（09P0-4）+W5（复测岗） | **已超（真值环）**+已排（终审 UI） |
| Z4 | **引擎插件注册**：manifest 注册+UNIQUE(plugin_id,version) 版本前进+启停裁定+参数按 manifest 声明动态渲染（Z:69,89-90；ZS engine-register.ts:3-9；engine-seed.ts:2-18 幂等种子永不翻 enabled；TaskCreateForm.vue:196 paramContract 动态渲染） | **注册制在册**：engines/ 五插件各 MANIFEST.md 十二字段（nuclei/session-viz/vuln-agent/vulnclaw/web-blackbox）；W1-T6 vulnclaw 适配器已落（adapter.py+MANIFEST version 0.4.0，HANDOFF.md:1527-1531，17 测绿）；消费面=P3 派单按 MANIFEST 纪律能力路由，超 max_op_level/视角上限**拒派**（SKILL.md:30）；selfcheck 校验 MANIFEST 引用⊆命令面（selfcheck.py:113-122）；供应链=tools.lock ECDSA（supply_chain.py:1-8）+nuclei templates.lock+release.pub | 数量 5v5 平；**管理面零**：无启停/版本行/参数动态渲染页；运行时注册 API 无（git 单源） | W3 工具卡 25 张扩注册面+W6 注册表页（A:B52 同源：卡带纪律标注+锁版本+验签状态）。**超点**：①纪律执法——它 manifest 只渲染参数，我们 max_op_level 拒派是真闸；②验签——引擎二进制/模板 ECDSA 发布者身份（它 engine-binary-supply 是下载校验位）；③不做运行时注册 API=**声明取舍**（注册面=供给攻击面，Z:208 攻击者正是靠开放注册面塞进假 runner——我们 git 单源+验签关死这扇门） | W1（已落半件）+W3+W6 | **已超（验签+纪律执法）**+已排（管理面） |
| Z5 | **算力资源池·远程 runner 令牌**：路径一本机 CLI 自动探测+启停；路径二一次性接入令牌（24h 过期/可吊销/sha256 落库）远程 runner 注册+心跳 30s+失联宽限 900s+机器槽（Z:23,85,91；ZS provision.ts:2-6,26-35；heartbeat.ts:27-29 时钟偏移 300s 告警） | 单机执行面：runner 本机 spawn opencode+killpg+watchdog 停滞续跑（tanyin-runner:100-120,56-58）；W1 launch 点火钮（server.py:747-777 已在跑=拒/mission 单源装配/留痕）。无远程节点/令牌/心跳面 | 全新件（远程执行面） | **W7 可选·设计先行**（本档 G9）：①令牌=授权书绑定——token 签发挂授权书 sha+窗口期，只对授权目标清单生效（**它的伤疤**：开放令牌面被攻击者注册假机群 i41/i56/i96 实测在册 Z:208——免费教训）；②runner --remote 模式：长连接 claim+心跳行入 timeline+工件回传 sha256 入链；③远程节点 env 白名单同律（WARRIOR_ENV_ALLOW 同源，tanyin-runner:40-54） | W7（可选；初表:43 取舍维持） | 声明取舍（单机先行·设计已备 G9） |

### B. 数据管线与治理面（3 件）

| # | ZhuLong 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| Z6 | **mapper 映射器**：会话日志→结构化 findings 的按引擎分族解析器注册表（manifest 快照路由+流式槽位 5k 批）；「映射器」字段暴露在漏洞详情=解析器可追溯（Z:32,119；ZS mapper.ts:1-40 注册表+MapperSlot 流式槽位；mapper-zhulong-stream.ts；mapper-tanyin.ts=吃我们五族） | **反向已建**：zhulong_export 五族平铺+vault 同值脱敏+导入包（zhulong_export.py:2-19,27-47,114-132；对方仓 tanyin@1+mapper-tanyin 已合，E:55）；**正向等价物=引擎适配器归一化表**：vulnclaw MANIFEST「归一化表 v1」引擎产物→统一 submission 映射+版本差异在适配器容错（engines/vulnclaw/MANIFEST.md）；findings 19 列含 schema_version（解析器版本锚同律）；导入径零执行（--dry-run 默认零网络，:16-17） | 形态差：无独立「日志→findings」mapper 层（我们的发现走战士单写者落账+引擎走 submission 归一化）；无运行时可插拔解析器注册表 | 不抄独立 mapper 层=**声明取舍**（账本单写者律：解析器也是写者，塞进运行时=绕过唯一写路径）；引擎族扩按 vulnclaw 归一化表模式复制（W3 每引擎一份适配器+归一化表）。**超点**：①双向互通独家——五产品里只有我们同时是 ZhuLong 的引擎供给方（tanyin@1）+消费方（export）；②解析器版本=MANIFEST version+schema_version 双锚+产物哈希入链（它 mapper 字段只到 seed-v1 一层） | W3（引擎族规格） | **已超（双向互通独家）**+声明取舍（不设运行时 mapper 层） |
| Z7 | **下载中心报告交付**：生成物列表（评估集/漏洞清单/任务报告）+7 天过期+过期行只留状态词（Z:93-95,202；ZS downloads.ts:14 `DOWNLOAD_TTL_SECONDS=7*24*3600`，:34-40 expired 派生，:236 过期下载=410 Gone） | POST /api/report/download：缺则触发 render（纯账本聚合）→单 md 或 zip bundle 附 Content-Disposition（server.py:946-991）；报告=FD 九段+双轴+SARIF；P5.5 签发永不代签（battle auto，HANDOFF.md:1535-1537）；产物永久在盘 | 无生成物**列表页**（下载中心壳）；无过期生命周期（这是它自伤：本实例 9 条全过期 Z:95——报告消失=交付消失） | W6 报告页规格扩（本档 G5）：生成物清单（draft md/SARIF/findings_json/导出包）+每件 sha256+签发人+渲染 rc；**超点**：①永久可复算——render=账本纯聚合，任何时刻重渲染逐字节一致（它的 7 天过期把「交付」做成了「限时体验」）；②验真三步 W8（链校验+重放复算+第三方可验）；③不过期=**声明取舍**（归档保留期另设 B:G10，不搞定时消失） | W6（报告页）+W8（验真三步） | **已超（永久复算+签发人）**+已排（清单页） |
| Z8 | **用户管理**：admin 专属页=平台健康面（Findings/吞吐/WAL 三值/队列/SSE 计数）+用户表（三角色/编辑/禁用/重置密码/授权/删除）；自保护（不可自降级 400/不可自禁用 403/最后管理员保护）+软删+scrypt+审计全写面（Z:97-100；ZS admin-users.ts:3-4,22,41,65；health-stats.ts:2-10 运营敏感聚合不入匿名健康面） | 单操作员+**双钥分权**：OPERATOR_KEY 管登录写面 vs APPROVAL_KEY 管审批（server.py:1011,1033-1036；审批=HMAC 持钥签名 server.py:897-944，钥只进子进程 env）；登录锁 5 次/60s（server.py:96）；**读面门 W1 已修**（server.py:411-431：除 /login+favicon 全过会话，页 302/API 401——初表「读面零鉴权 P0」已闭，commit 1cb568a）。多用户/角色/平台健康面=无 | 多用户=无（W7）；健康面=无（metrics 页是双臂召回+预算，非平台自观） | W7 三角色 RBAC+双人复核（蓝图:28；对齐 ZhuLong 三角色，B:D1 同源：超点=审批-执行分钥+approver 入哈希链）。健康面=cheap 件并入 W6 仪表盘（本档 G4）：verify-chain 通过率+SSE 连接数+battle 队列投影（等价它的 WAL/队列/SSE 计数，且我们的「完整性计数」=链校验——比 WAL pragma 更硬的自观） | W7（RBAC）+W6（健康卡） | 已排（W7）+**已超（分钥+审批入链）** |

---

## 二 · multica 七件逐件表

### A. 工作台编排面（4 件）

| # | multica 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| M1 | **收件箱通知流**：agent→人回执流三级 action_required/attention/info+筛选+归档/已归档视图+单条处理/稍后+unread-summary 角标轮询（M:90,106-107；M:329 `/api/inbox(+unread-summary/mark-all-read)`；MS inbox.sql.go:279,388 Severity/Archived 字段） | **零通知代码**（cli/+scripts/ grep notify/webhook/钉钉/飞书/tg 零命中；蓝图:59 自认「无」）；最近似=activity SSE 全量流（activity.html）+home 审批登录提示（index.html:366） | 全新件（回执流形态） | W7 通知框架（A:G7+蓝图:59 同源）+**本档补收件箱形态**（G3）：①三级映射=账本谓词——action_required=审批卡+ask:human 待答、attention=发现四级/gate-fail/预算 80%、info=战毕/复测结论；②**超点**：投递先落 timeline `notify` 事件再发（它 inbox 独立表不入审计链——谁被通知过、何时、读到没，它改库即失忆，我们入链）；③unread 角标=webui 顶栏投影 pending 计数（零新表）；④归档=已读行时间戳，不做删除（只增律） | W7（框架+形态）+W6（审批中心 pill 联动） | 已排（W7，形态规格本档补齐 G3） |
| M2 | **命令面板 K**：顶栏「搜索… K」全局命令面板/全局搜索（M:54；M:176 shortcuts 页全站快捷键表） | 无全局面板；仅有局部键：say 框 Enter 发送（session.html:609）、图谱平移键（graph.html:760,803） | 小件但全站效率位 | W6 全局搜索 K（初表:50 已立；A6 同源）+**本档补索引规格**（G7）：索引=路由（9→21）+battle 号+FD/EV 号+高频动作（点火/暂停/审批/重跑）；零依赖实现（input+键盘导航 ~150 行）。**超点**：索引含**账本实体**——输入 FD-12/EV-55/battle-3 直达深链（Z2 URL-SSOT 联动），甚至 timeline 行号直达回放帧；它的 K 只搜平台实体，搜不到「证据」与「历史时刻」 | W6 | 已排 |
| M3 | **任务表（视图保存/筛选/看板）**：视图 pill（全部/成员/智能体）+工具行四件（视图=issue_views 保存视图+列偏好/筛选=状态/优先级/标签/属性带操作符/显示=列显隐/看板=拖拽+泳道+live-sorting）+服务端分页 `POST /api/issues/table/rows`+`facets` 分面计数（M:112-117,127；M:328 issue-views API） | battle 切换器=**下拉单选**（index.html:282-284,410-425 选完跳 /session?battle=N；session.html:511,541）；无战局表/筛选/保存视图；W1-T4 battle auto 一键链已落（init→launch→看护→settle→report，HANDOFF.md:1535-1537）——编排执行面比它硬，**展示面**比它穷 | 列表形态=中（数据全在：battles 投影/goals 19 参/budget 三段/findings 计数） | W6 多战场切换器+**战局表**（G6；A:B5 同源合并）：列族=状态/预算三段/发现四联/运行时长/最近心跳（零新端点，session.json battles 投影）；保存视图=URL 参数（Z2 同源——不建 issue_views 表，账本投影零新表）；分面计数=前端聚合（战例≤百级无需服务端分页，声明取舍）。**看板拖拽不做=声明取舍**（初表:51 维持：拖拽改序=绕过账本写路径，编排即账本）；**超点**：每行「演变回放条」入口——它的行只有现状，我们的行能回放任意历史时刻 | W6 | 已排+声明取舍（拖拽看板） |
| M4 | **我的智能体**：列表（我的/全部/已归档+筛选+运行次数+30 天活跃）+详情四标签（概览/工作/能力=技能挂载开关+开场白+MCP+自定义环境变量/设置=指令+可见性三档+并发数+运行时绑定）+三通道创建（手动/AI 对话式/分流页）（M:132-146；M:330 agents API 族） | 单战士+SKILL 协议（P0-P6 九门+P3 演进循环，SKILL.md:25-33）；档位=model_tier strong/weak 两档（write_cmds.py:344）；WARRIOR_ENV 白名单摘密（tanyin-runner:40-54）；常驻预算<2000 token 冻结契约+实测校准（PROTOCOL.md:33-34）；多战士/配置页=无 | Agent 实体/技能开关/可见性/并发数=无（W5/W6）；运行统计=无（timeline 可数无页） | W5 多战士编队+常驻规划者（蓝图:26；intent 路由 priority 公式已在 SKILL.md:30）+W6 战士配置页（蓝图 §四b：档位=插槽参数可视化+per-warrior 工具面矩阵 A:G13）。**超点**：①提示词在册即版本（git）+常驻 token 预算是执法契约（它的渐进披露无预算执法）；②env 摘密按战士白名单（它 env 是明文配置）；③AI 对话式建代理**不抄**（建战士=开写路径，必须过授权件与 guard——它的 agent builder 零授权概念，谁都能聊出一个能领任务的员工） | W5+W6 | 已排 |

### B. 资源与运行时（3 件）

| # | multica 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| M5 | **项目资源**：项目列表/详情（复用任务表组件）+project_resource（本地文件夹/代码仓库，v0.5.1 起可选起始分支/commit）+项目视图（M:129-130；MS project_resource.sql） | battle 目录=作业容器（battle-N/G-*，server.py:161-189 最新代选取）；资产/关系账本（assets.tsv/edges.tsv，schemas.json 13 表；add-asset/add-edge 命令 SKILL.md:33）；W1 launch=mission.goals/scope 单源装配（server.py:756-763） | 项目实体=无（单机单战族，B:A6 同判）；资源检出（repo --ref）/本地文件夹资源类型=无 | W6 工作区页+资产页（蓝图 §四b：目录树+下载+产物 sha256 登记 timeline）+W7 客户·项目实体（battle 归属 project 行）。资源类型=资产表 type=repo/folder；**检出=工具卡**（git clone --ref 过 Tier3 egress——它的 VCS 检出无出网闸，M:184 repositories tab 直连 GitHub）。**超点**：资源过授权复判（W5 跨战登记处语义：资产进 scope 须授权书覆盖——它的 project_resource 无授权概念，挂哪跑哪） | W6+W7+W5 | 已排 |
| M6 | **agent 运行时 profile**：运行时=机器×CLI 进程；provider（跟随 CLI 配置）或 profile（自定义命令+模型）二形；一机多 profile（unique(workspace_id,daemon_id,provider|profile_id)）；机器卡在线状态/配对码绑 daemon/WebSocket 心跳/离线 last_seen（M:83,154-157；MS runtime_profile.sql.go:33-35 DisplayName/CommandName；M:341 支持过的运行时全家福 17+） | 运行时=opencode 单基座（tanyin-runner:101 `opencode run`+`--model` 透传）；模型档=model_tier 两档（write_cmds.py:344）；llmpool 判定核（分道冷却/抖动/硬熔断，llmpool.py:38-49，**未接实链** A:B47）；五宿主矩阵注入（hosts_matrix.py）；W2 池 sidecar+W6 llm-profiles.tsv profiles 表（A:B45 已设计） | 自定义运行时 profile（任意 CLI 命令+模型）=无；运行时在线/配对面=无（单机，同 Z5 取舍） | 插槽制兑现（蓝图:11「模型是参数不是命运」）：W2 sidecar=profile 实链（本地反代+failover 入 timeline）；W6 管理页=llm-profiles.tsv 读写面（amendment 语义）。引擎运行时二分=engines/ MANIFEST kind=cli|skill（已比它 provider|profile 二分多一类「技能型引擎」一等公民）。**超点**：profile 变更=amendment 行入链（它 profile 重命名/换模型即时生效零审计——哪个任务用了哪档模型，事后查不出，我们行行有账） | W2（实链）+W6（管理页） | 已排 |
| M7 | **JSONL v1 协议（源码级拆，D:dsh.go 479 行全读）**：命令面=execute（v=1+request_id+cwd+prompt+resume_session_id+model{provider,id,reasoning_effort}+mcp_servers）/cancel（D:54-70,119-121 `--profile multica --stdio`）；帧面=ready/session/text/thinking/tool_call(call_id,arguments)/tool_result/usage(四段 token)/protocol_error/result(status,stop_reason,resume_rejected)+models（D:77-117）；版本闸 v≠1=protocol_error（D:377-380）；request_id 过滤（D:381-383）；MCP 注入 stdio/streamable-http、SSE 拒收（D:149-205）；取消梯=cancel 帧→3s→SIGTERM→2s→SIGKILL（D:281-300）；模型目录发现 `--list-models`→models 帧+thinking 档位（D:436-479） | **驱动面**（我们驱动 opencode）=文本协议：`opencode run <prompt>` 一次性进程，stdout+stderr 合流落 opencode-run.log（tanyin-runner:100-120）；事件=runner.tsv 三段文本行 ts/kind/detail（session_view.py:162-172）；**工具无 id 按行首标记归块**（session_view.py:15 原注「TUI 捕获无 tool_use/result id」）；续跑=RESUME_PREAMBLE 重开进程+verify-chain 恢复协议（tanyin-runner:56-58,251）；预算=usage 帧抽取 budget.tsv（:315）；取消=killpg 无协商（:90-97）。**被驱动面**（别人驱动我们）=零 | 驱动面=中（文本协议脆弱：TUI 格式漂移即解析崩、无 call_id 配对、无取消协商）；**被驱动面=真空白**（multica 能挂 DSH 当运行时，不能挂 GraphLed） | 两件：①**驱动面换代**（G2→W2 扩）：runner 事件帧化（kind→帧类型枚举+call_id 列+schema_version 锚），call_id 配对喂 W6 工具卡折叠（A:B19 同源）；opencode 若有结构化输出模式即切，无则帧化自家 runner.tsv 契约。②**被驱动面**（G1→W7 新增，~600-900 行）：`graphled --stdio` JSONL v1 适配器——execute(授权书 sha+目标+预算+model_tier)→ready/session/text/tool_call/usage/result 帧（request_id=goal_id，timeline 行号=帧序），cancel→先落 directive 停令再走宽限梯（取消也入账——比 D:281-300 的纯杀更硬）；复用 dsh.go 的帧语义=零学习成本对接 multica 类平台。**价值**：五产品任何一家（multica 类宿主/ZhuLong 类控制台）可把 GraphLed 当运行时挂——「探隐引擎进 ZhuLong」升级为「GraphLed 进一切生态」，插槽制对外兑现 | ①W2 扩+②W7（新增） | 真空白（被驱动面）→**已给方案入 W7**；驱动面=已排（W2 帧化+W6 配对） |

---

## 三 · 交叉发现（两家各一条硬结论）

**① ZhuLong 的伤疤=我们的免费评测集与免费设计评审**（Z:206-208 实测在册）：
- 环境探活 SSRF 绕过矩阵（rbndr/nip.io/十进制 IP）→ 我们已有 Tier3 egress 四态+DNS pin+canary（egress_proxy.py:3-10）——对齐面直接判已超，且它的绕过清单就是我们的 egress 回归用例库；
- **攻击者用开放令牌面注册假 runner 机群+接入令牌**（Z:208）→ Z5/G9 的「令牌绑授权书」设计直接来自它的伤口；
- 攻击者造低权账号 penter/viewer → W7 RBAC 上线时的越权测试剧本现成；
- payload 名对象/任务/项目**原样回显** → 存储反射面：我们 webui 全部 textContent 注入（evidence.html:327-341 同式），对齐时照抄即可，但要把「回显面清单」进 W6 页面验收单。
一条总教训：**ZhuLong 把「开放注册/开放深链/开放探活」做成了产品力，也做成了靶场**——我们每个开放面都必须挂授权件或验签，这是它用 51 条 findings 替我们交的学费。

**② multica 的「壳可换定律」+我们的分发机会**：用户已在 multica 上把安全红队 7 agent 编制跑通（M:241-307），但交战纪律全套是我们的语汇——授权八问（M:285）、L0-L3 操作分级（M:286）、`{{vault:cred-N}}` 占位+链式 timeline+approvals.tsv（M:287-288）。证明两件事：编排原语（任务面板/收件箱/唤醒规则）是 multica 的真领先，必须 W6/W7 补齐（M1-M3）；但作业法的不可替代性在我们——**且 M7 的被驱动面（G1）做好后，multica 从「竞品」翻面为「GraphLed 的免费分发渠道」**：multica 用户挂 graphled 运行时，纪律与账本原样带过去。它 17+ 运行时名单（M:341）等着多一个。

---

## 四 · 新增缺口清单（本舰域内，件件有归宿）

| # | 缺口件 | 危害 | 方案（可施工） | 建议波次 |
|---|---|---|---|---|
| G1 | **GraphLed 被驱动面**（`graphled --stdio` JSONL v1 运行时适配器）：multica 能挂 DSH/17+ CLI（M:341），挂不了我们；ZhuLong 靠 tanyin@1 文件族互通（zhulong_export.py），无实时协议面 | GraphLed 进不了别人生态=只能自建入口；「插槽制」只对内兑现 | 帧语义照抄 dsh.go（execute/cancel→ready/session/text/tool_call/usage/result；D:54-117）+我们加固三点：execute 必带授权书 sha（拒绝裸跑——dsh.go 无授权概念）、cancel 先落 directive 停令再宽限梯、usage 帧=budget.tsv 同源四段。~600-900 行+协议契约档 1 份 | **W7 新增（必做，非可选——分发面即价值面）** |
| G2 | **runner 事件帧化+call_id 配对**：opencode TUI 文本捕获无 tool_use/result id（session_view.py:15），格式漂移即解析崩；无取消协商 | 会话页工具卡配对靠猜（A:B19 已排 W6 但数据面无 id 可配）；取消=裸杀丢尾账 | runner.tsv 帧化：kind 枚举化+call_id 列+schema_version 锚；watchdog 续跑/取消先写帧后杀；W6 B19 渲染器直接消费 call_id。~250 行 | **W2 扩（引擎地基）+W6（渲染配对 A:B19 联动）** |
| G3 | **收件箱回执流形态**：A:G7 只排了渠道（webhook→6 渠道），三级回执流/归档/角标形态无规格 | 通知发出去就沉底：待办没有「处理/稍后」的收口面，operator 还是得盯全量流 | 三级=账本谓词（见 M1）；unread 角标=webui 顶栏投影；归档=已读时间戳不删行；投递入 timeline notify 事件。规格并入 A:G7 框架，~200 行 | **W7（A:G7 扩）+W6（角标）** |
| G4 | **平台健康面**：ZhuLong 把 WAL/队列/SSE 计数做成 admin 首屏（ZS health-stats.ts:2-10）；我们 metrics 页只有双臂召回+预算 | 平台自观缺位：SSE 掉了/账本链断了/战局积压，operator 无第一屏 | /api/state.json 加自观段：verify-chain 最近结果+SSE 活连接+battle 状态计数+runner 心跳；W6 仪表盘一张卡。~100 行 | **W6（仪表盘经济学并入）** |
| G5 | **报告生成物清单页**：Z7 判已超的前提是「永久复算」，但现状只有一个下载端点（server.py:946-991），无清单/无 sha/无签发人展示 | 交付面=一个按钮；「报告中心」叙事立不住 | W6 报告页规格扩：生成物清单（draft/SARIF/findings_json/导出包）+每件 sha256+签发人+渲染 rc+重渲染按钮（复算即验真） | **W6（报告页规格扩，~150 行）** |
| G6 | **战局表**：M3 对等件——battles 投影成表（列族+保存视图=URL 参数）；A:B5 只写了「home 补三卡」 | 多战作业只有下拉单选，无总览对比 | W6 切换器升级为战局表：状态/预算三段/发现四联/时长/心跳列+行点深链+回放条入口；数据零新端点。与 A:B5 合并施工 | **W6（与 A:B5 合并，~250 行）** |
| G7 | **命令面板 K 索引规格**：初表:50 排了「全局搜索 K」但索引面没定义 | 做出来只搜页面名=又一个摆设件 | 索引=路由+battle 号+FD/EV 号+命令动作+timeline 行号（直达回放帧）；~150 行 | **W6（初表:50 规格补全）** |
| G8 | **引擎注册管理面**：engines/ 五 manifest 在册（W1-T6 已落 vulnclaw）但启停/版本行/参数动态渲染零页面（Z4 差距项） | 引擎治理只有文件没有面；admin 想停一个引擎得改 git | W6 工具卡注册表页扩引擎维度（A:B52 同页）：启停位+版本行+manifest 参数只读渲染+验签状态；启停=amendment 行入 timeline | **W6（A:B52 规格扩，~200 行）** |
| G9 | **远程战士节点预设计**：Z5 取舍维持，但 W7 若启动无设计稿=临场拍脑袋（ZhuLong 令牌面伤口在前 Z:208） | 真到要做时重复它的错误 | 设计档先行（~50 行文档）：令牌=授权书 sha 绑定+窗口期；runner --remote 长连接 claim+心跳入 timeline+工件 sha256 回链；env 白名单同律 | **W7（可选件的设计前置，0 代码）** |
| G10 | **三态终审波次勘误落地**：初表:41 写「W1+W6」，实际=09P0-4 归 W6（C3 校对）；A/B 舰引用时会带错 | 波次表失真，施工队按 W1 找件找不到 | 基线总表 :41 行波次列改「W6（09P0-4）+W5（复测岗）」；蓝图 v4 合成时一并改 | **改档（随蓝图 v4，0 代码）** |

---

## 五 · 波次总量修正建议

- **W2** +~250 行（G2 runner 帧化——并入「O(1) 追加+intents 租约+多战执法面」同批施工）。
- **W6** +~850 行（G4 健康卡+G5 报告清单+G6 战局表[与 A:B5 合并后增量]+G7 面板索引+G8 引擎管理面+G3 角标）——W6 原 ~8500-9500 行修正后 ~9400-10400 行。
- **W7** +~700-1100 行（**G1 被驱动面=必做新增**；G3 收件箱形态并入 A:G7；G9 设计档 50 行）。
- **W5** 无新增（M4 复测岗/多战士已在册）；**W3** 无新增（Z6 引擎归一化表模式=既有规格的写法约定）；**W1** 无新增（本域 P0=读面门已闭，1cb568a）。
- 合计：本舰新增 ~1800-2200 行（G1 为必做大头）。**不新开 W9**，全部缺口有归宿波次。判词账：已超 4（Z3/Z4/Z6/Z7）/已排 9/声明取舍 1（Z5；另 M3 拖拽、Z4 注册 API、Z6 mapper 层、Z7 过期为行内次判）/真空白 1（M7 被驱动面）→已给方案入 W7，一件不悬空。

---

## 六 · 证据可复核性声明

- 对手语料=手册实读行号（Z 214 行/M 353 行全文）；**ZhuLong 双源**：每件另给 ZS:file:line（ai-assisted-security-verification-platform 快照 2026-10-18，分支 feat/bo14-tanyin 工作区只读）；multica 源码=.research/repos/multica 快照只读，dsh.go 479 行逐行读毕（D:n 行号直接可查）。
- 我方每件出处=仓内实读行号（main@1cb568a 快照）：server.py 1125 行/index.html 834 行/session_view.py 391 行/zhulong_export.py/schemas.json（13 表+findings 19 列+intents 17 列 python 实跑枚举）/engines/ 五 manifest 实勘/SKILL.md/llmpool.py/selfcheck.py/supply_chain.py/vault.py。W1 三舰进度=HANDOFF.md:1527-1537（T6 vulnclaw/T1+T2+T7+读面门/T4 auto）。
- 两处与初表不一致（C3 波次笔误、C4 已兑现未翻面）照实记录；C2 半件在手为初表低估的勘误。读面鉴权=已修事实（server.py:411-431），不再标 P0（遵开工令口径）。
- 法律敏感标注：本域无 C2/WebShell 施工件；§三引用 ZhuLong 靶场攻击痕迹（Z:206-208）仅作防御设计输入——攻击者手法清单不复制、不扩写，只映射到我们的闸门（egress/令牌授权绑定/RBAC 剧本/回显面验收）。
- 本档为唯一写入件；语料与代码（含 ZhuLong 仓与 multica 快照）零改动。dsh.go 协议拆解（M7）为五产品唯一源码级运行时协议参考——G1 方案的帧语义来自它，授权/取消加固点来自我们自己的律。

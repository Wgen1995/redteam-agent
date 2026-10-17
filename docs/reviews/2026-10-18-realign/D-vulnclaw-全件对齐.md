# D · VulnClaw 全件对齐（逐件表）· 2026-10-18 重对齐

> 执笔：重对齐子代理 D（域=VulnClaw 全面，含三轮实机试用）。纪律：语料与代码只读，唯一写入=本档。
> 对手语料：`docs/research/2026-09-24-vulnclaw-analysis.md`（下称**分析档**，174 行全读）、`docs/research/vulnclaw-live-trial.md`（下称**活试**，439 行全读；§1-8=无 key 轮、§9=glm-4-flash 实战轮、§10=glm-4.7 终审轮）、源码快照 `.research/repos/VulnClaw` @3b71e26（712 文件只读，下称**快照**；本机 venv /Users/wgen/.venvs/vulnclaw=PyPI 0.4.0 同源，只读未跑）。**勘误**：任务书所列「docs/research/manuals/ 下 vulnclaw 相关」实查不存在——manuals/ 五本（artex/csai/cyberstrike/multica/zhulong）grep 'vulnclaw' 计数 0，VulnClaw 语料=活试+分析档+快照三源，如实记录。
> 我方仓：`/Users/wgen/redteam-agent`（**GraphLed**，旧名探隐 TanYin）。波次基线：`docs/design/exceed-blueprint-2026-10-17.md`（下称**蓝图**）；判词四档沿用：**已超**/**已排**（波次有名）/**声明取舍**/**真空白**（不许留，发现即给方案）。
> 前置事实（对齐口径）：**插槽位保留已终审**（活试 §10.4）；**W1-T6 适配器已落地**（HANDOFF.md:1527-1530，engines/vulnclaw/adapter.py 494 行+MANIFEST，17 测试用例绿）——本档以「它=被吃的引擎+被抄的语料」为对齐基线，不是平级竞品对表。
> 一句话总判：**VulnClaw 对我们只剩两块真领先——测绘工具族（六引擎+子域/JS/目录/端口/服务/指纹，全排 W3）和终端/机读事件面（Rust TUI 5355 行+--stream NDJSON，全排 W6）；它的招牌防线（证据闸门/TaskConstraints/双工件）我们已同型或更硬地拥有，且整个引擎已被我们当插槽吃掉。逐件 60 件：已超 25、已排 29、声明取舍 5、真空白 1（PDF 出件，方案已给并入 W6）。**

---

## 〇 对基线总表 VulnClaw 节（10-基线总表:55-61，仅 4 行）的校对

| # | 基线总表原判 | 校对结论 | 证据 |
|---|---|---|---|
| V1 | 「web 对话界面：我们=无」（:59） | **不准确**：写路径已在——/api/battle/say（server.py:547 派发、:829-855 指令文件+append-timeline 双落）；且**它也不是对话页**：7 页 React 任务控制台（TaskConsolePage=启动表单+HomePage=技术日志流），无聊天线程/无多轮会话。差距重定性=「任务控制台形态对比」而非「有无对话」（A舰 C1 同源校正） | 快照 frontend/src/pages/ 7 文件 vs 仓 cli/webui/server.py:547,829 |
| V2 | 「SARIF+PDF：我们=无，W7 SARIF+法务」（:61） | **半过时**：SARIF 双工件早已落地（批次6 T15 commit c96db82；report_artifacts.py:95 findings_json 全量+生命周期、:140-180 SARIF 2.1.0 仅 verified，口径=VulnClaw findings_output 同款纪律）；**PDF 仍真空白**（全仓 grep 仅授权书 PDF 输入面 battle.py:557,579） | 仓 cli/ledger/report_artifacts.py:95,140-180 vs 快照 findings_output.py:5-8 |
| V3 | 「Rust TUI 19命令+--stream：CLI 49 命令但输出裸奔」（:58） | **半准确**：battle watch 已有 9 行快照面（battle.py:630-638，runner 尾行+七表行数+进程态）；--stream 的我方对等面=SSE（sse.py:35-38 行号游标+15s keepalive）+runner.tsv 事件流+适配器已消费 NDJSON（adapter.py:420-423）；「输出裸奔」成立于 **CLI 一等面无实时事件契约**这件 | 仓 scripts/battle.py:630-638、cli/webui/sse.py:35-38 |
| V4 | 「六引擎测绘：工具零覆盖，W3」（:60） | **准确**；补一笔：知识面已取 8/47（knowledge/concepts/CP-0001..0008，03专家 P0-5），语料弹药在路上 | 仓 knowledge/concepts/ vs 快照 skills/specialized/ 50 目录 |
| V5 | VulnClaw 节仅 4 行 | 本档铺全 60 件（E舰 I11 点名的 D 舰缺位即本档补齐） | 本档 §一 |

---

## 一 · 逐件表

### A. 命令面与 CLI 骨架（8 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| A1 | Typer 19 命令：run/solve/persistent/recon/scan/network-scan/exploit/report/manual(man)/init/login/logout/doctor/learn/feedback/repl/tui/web（快照 cli/main.py:1187-3693 逐个 @app.command 实数）+6 子应用 config/kb/experience/target-state/plugins/code（:1184,:2478-2530,:2853-2941） | 49 命令（registry 单源 all_commands，cli/ledger/registry.py:76-93）+14 工具箱入口（contracts/09-cli-surface.md:21,37） | 我们量多且分域 | 已超面保持：薄 CLI 四类能力+语义判断禁入（铁律 7）vs 它 main.py 3812 行巨石（分析档 §5 技术债①）；命令名 W2 统一改 GraphLed 口径时防半新半旧 | — | 已超 |
| A2 | 三引擎并存：rounds 遗留/solve 默认/team 角色（快照 core.py:535-595 resolve_engine；分析档 §1.1）语义重叠、配置双份 | 插槽制：一套宪法多引擎（engines/{nuclei,vuln-agent,vulnclaw,web-blackbox}/MANIFEST.md 契约 08 十二字段）；W1-T6 已吃进 VulnClaw（HANDOFF.md:1527） | 我们形态更稳 | 保持；「模型是参数不是命运」对它的「发现力=模型档」（活试 §10.4）是结构性回答 | — | 已超 |
| A3 | solve 引擎=模型自决无阶段（快照 solver.py:411-417 "not required workflows"；分析档 §2.1「跑完就是跑完」） | 九门状态机 P0-P5.5+出口断言+覆盖度矩阵非空门（phases/；denominator-ready 分母上锁，contracts/09:122） | 哲学相反 | 我们已有双保险：宪法门序管自研战士，插槽外脑（vulnclaw）补模型自决发现力——两者经 intents/提交协议汇入同一账本 | — | 已超 |
| A4 | 预算=--max-steps 240 步数天花板（快照 main.py:1508-1510）+子代理 runaway 预算（活试 §9.3 budget_exhausted） | budget.tsv 四维（token/requests/hours/dollars）+budgetctl 执法化（HANDOFF.md:1234 F3：超限=BUDGET-ENFORCE 收尾令重启）+goals 预算硬顶必填（server.py /api/battle/new） | 我们维度多 | 保持；W5 多战士编队时按 intent 分账 | — | 已超 |
| A5 | persistent 周期模式：rounds×cycles 循环+每周期自动报告（快照 main.py:1642-1668） | runner 常驻+watchdog 巡检（cli/tanyin-runner:188 runner.tsv、:362-383 SOFTSTALL/STALL/GIVEUP 分级击杀）+battle auto 一键链（W1-T4，HANDOFF.md:1535-1536） | 形态对等偏我们（看护+结算+报告全链） | 周期模式并入 W5 常驻规划者（跨战复测常驻岗同批） | W5 | 已排 |
| A6 | doctor 环境体检：python/node/npx/uvx/nmap 降级提示（快照 main.py:2710；活试 §1.2） | tanyin-selfcheck 六项静态+cmd-index/encoding 绊线（cli/ledger/selfcheck.py；A舰 K3 引） | 我们查自己更深（账本/命令/编码） | 保持；nmap 类外部工具缺位检查随 W3 工具卡注册表面（卡装没装一目了然） | W3（附带） | 已超 |
| A7 | init/login/logout：LLM 侧 OAuth PKCE+静默刷新+ChatGPT 桥接（分析档 §4.2；快照 main.py:2589-2708） | LLM 侧=llmpool key 池 failover+ECDSA 验签；**目标侧=vault 四关卡 {{vault:cred-N}}**（契约 03）——它目标侧零管理（测试口令明文走参数，分析档 §4.2） | 目标侧我们独有 | 保持；测绘 API key（W3 新增）必须走 vault 不落 config 明文（见新增缺口 G5） | — | 已超 |
| A8 | 退出码契约 0/1/2/3：干净/事故/≥1 verified/仅候选（快照 headless.py:32-45）+summary.json 机读（:16-17） | evals 裁决 0/1/2（cli/ledger/evals_metrics.py:2「退出码 0/1/2，裁决 A」） | 它多第 4 态（仅未验证候选=CI warn） | W2「退出码分离」批已点名——落时纳入第 4 态：rc3=账本有 active 但零 verified（候选存在即黄灯，不静默绿） | W2（规格补点，见缺口 G4） | 已排 |

### B. --stream 机制与事件契约（5 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B1 | solve/scan/recon 等 7 命令带 --stream：NDJSON 事件流供 TUI/管道消费（快照 main.py:1536-1537,1883-1884,1989-1990,2130-2131,2319；_helpers.py:235 JsonlStreamSink、:310 emit_complete_event） | CLI 一等面无 --stream 对等件；机读事件=timeline.tsv（哈希链）+SSE（sse.py:1-8 追尾生成器）；适配器已消费它的 NDJSON（adapter.py:420-423 stream.ndjson 落盘归档） | CLI 即时流=缺 | watch --json：battle watch 加 NDJSON 事件面（log/status/complete 三型+findings 内嵌+summary.json 尾件）——CI/管道消费 CLI 即一等公民；约 200 行 | W6（终端工作台批扩，缺口 G2） | 已排 |
| B2 | complete 事件内嵌 findings[]（verified_claims 转写，severity 恒 high 硬编码——快照 main.py:1609-1623） | 适配器不订阅该转写：FINAL 文本确定性解析出实证 findings（C2/verified/eNNN 区间展开），complete 缺席也能从 session.json 归一（adapter.py:149 parse_final_answer、:247 normalize） | 我们消费面更富更稳 | 保持；submission schema（契约 07）字段族>其四字段转写 | — | 已超 |
| B3 | P0#1：不带 --stream 必崩——on_event 仅 if stream 分支定义（快照 main.py:1560）却在分支外引用（:1578）→UnboundLocalError（活试 §1.3 实测） | 无对应面（我们 CLI 无该分支结构）；适配器永远带 --stream 调它（adapter.py:410-411） | 0 | 已绕；值得提上游 issue（活试 §8.2 建议，先核 main 分支） | — | 已超 |
| B4 | P0#2：收尾组装 findings 崩——verified_claims int 计数形状被切片（快照 main.py:1609）→complete 发不出/两层状态不一致（活试 §9.6、§10.2④ PyPI 版复现） | 适配器④全兜：int 形状容忍+崩溃签名识别（"not subscriptable"）+complete 缺席侦测→session.json 手动归一+手动 report 规避（adapter.py:231 _complete_present、:425,:430-433,:456-461；tests/test_engine_vulnclaw_adapter.py:212 TestP02Bypass） | 0（我们把它的崩做成了测试用例） | 保持；--run 实弹轮（有效 key）首验时复核 PyPI 0.4.0+ 是否已修 | W1 收尾（HANDOFF.md:1530 遗留件，缺口 G6） | 已超 |
| B5 | events.jsonl append-only 事件账本：run_created/checkpoint/run_status/distillation_*（活试 §6.2；分析档 §3.1「无链式哈希」） | timeline.tsv 哈希链+verify-chain+hash-recheck+checkpoint（registry 命令面）——行哈希+单写者+原子整替换（timeline.py） | 我们防篡改它没有（分析档 §6.2 判据） | 保持；它的 checkpoint(reason) 语义我们已有（checkpoint 命令） | — | 已超 |

### C. Rust TUI（6 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C1 | Rust TUI 5,355 行（tui/src 实测 wc：app.rs 2,060/layout 707/workbench 607/protocol 381/events 327…）：终端全功能面 | battle watch 9 行快照（battle.py:630-638：runner 尾 5 行+七表行数+进程存活）；WebUI 9 页承担主交互 | 大（终端面） | W6 终端工作台 watch 全屏版（蓝图 W6 行「对标 VulnClaw5355 行」已点名）；D-d① 待裁：ANSI 富输出（推荐，工期×1）vs 全屏 TUI（×2）——呈批件在 E舰 §四 O2 | W6 | 已排 |
| C2 | 版本化协议+schema 双端校验：tui-v1.schema.json 嵌入 Rust 侧 jsonschema 校验+protocol_version 握手（快照 tui/src/protocol.rs:355-380、protocol/tui-v1.schema.json；Python 侧 tui_protocol.py/tui_backend.py） | 无终端协议 | 中 | watch --json 事件协议同步落 JSON Schema+双端（CLI 出/终端进）校验——防协议漂移，抄它的架构不抄它的量；约 100 行 | W6（watch 规格扩，缺口 G3） | 已排 |
| C3 | composer 输入框+ExecutionMode/PermissionMode 循环切换（快照 tui/src/app.rs:282-283,465-519：ask/auto_review/full_access 三档热切换） | 终端面无输入（指令走 webui say 或 directive 文件） | 中 | watch 全屏版带指令行=say 同通道（_write_directive+timeline 双落已在 server.py:845-850——终端复用同写路径即双面同源） | W6 | 已排 |
| C4 | 审批模态+倒计时+零宽字符可视化（快照 app.rs:190-196,537-543；分析档 §4.3 bidi 防注入） | approvals.tsv+/api/approval（server.py:451,:897）；终端无审批面 | 中 | W6 审批中心（Web 主面）+watch 全屏版审批卡（次面）；**吸收其语义**：审批粒度=内容哈希（request_hash 同款）——分析档 §6.1-1 建议在册 | W2（ask 三态+judge 接线）+W6 | 已排 |
| C5 | 视图族：status/capabilities/transcript/findings/attack_chain/subagents/sessions/skills 目录（tui/src/views+ui 各件） | session 页三块+graph 11 层泳道+evidence 44 卡（Web 承担） | 形态异（它终端我们 Web） | 不逐件搬；watch 全屏版取 status/findings 两视图子集（Web 已有的投影复用） | W6 | 已排 |
| C6 | TUI 后端=python -m vulnclaw 子进程+stdin/stdout JSONL（快照 tui/src/exec.rs:60 spawn_backend；分析档 §1.1 入口三件套） | 账本+runner 已进程分离；CLI/账本即后端 | 架构同向 | 保持——我们「终端=投影面，账本=唯一写方」比它「TUI 拉起 Python core」耦合更低 | — | 已排（对等） |

### D. Web 面（8 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| D1 | FastAPI 25 路由（快照 web/app.py:127-262：health/config/mcp/constraint-audit/providers/tasks×4/targets×8/reports×4） | 12 路由 stdlib http.server（server.py:422-551：state/session/metrics/approval/stream+battle new/control/say/report） | 量差 | W6 九页扩容（A舰 C7 API 面行同源）；stdlib 保持（零依赖律核心件） | W6 | 已排 |
| D2 | React 7 页：Home/TaskConsole/History/Reports/RiskResults/SafetyBoundary/Settings（快照 frontend/src/pages/） | 9 页 stdlib（cli/webui/static/：index/session/activity/graph/evidence/coverage/metrics/new/login） | 页数近同、栈不同 | 栈=已拍 Vite+Vue3 投影面（E舰 §四 D-f）；核心件保持零依赖 | W6 | 声明取舍 |
| D3 | SSE 任务流：EventSource+/api/tasks/{id}/stream+asyncio.Queue 广播+终态收口（快照 api/web.ts:206-207、task_manager.py:117-133、stream.py:10 encode_sse） | SSE timeline 追尾：行号游标+keepalive（sse.py:35-38,14-15）；无 Last-Event-ID 服务端读取（A舰 B22） | 小（断线续传） | W6 SSE 换代（蓝图:61 已排）：读 Last-Event-ID+客户端去重合并 | W6 | 已排 |
| D4 | 全面 token 鉴权：/api/* 全路由 Bearer/HttpOnly cookie/loopback 三通道（快照 web/auth.py:1-12）；web 命令默认 127.0.0.1:7788+非回环绑定须 --allow-remote（main.py:3693-3714） | 读面登录门 W1-T1 已修：除 /login 与 favicon 全过会话+302/401（HANDOFF.md:1533「B舰P0 修」）；HttpOnly+SameSite=Strict cookie 同款 | 0（已收口，不再标 P0——任务书口径） | 保持；对标它的「SSE 不能带 Bearer→cookie 兜底」注释，我们 cookie 面本就覆盖 SSE | — | 已排（W1 已落） |
| D5 | TaskConsole 表单 scope 旗标直达 TaskConstraints：only-port/only-host/only-path/blocked-host/blocked-path（快照 TaskConsolePage.tsx:223-239） | 授权八问真上传：授权原件 base64+WebCrypto sha256+add-goal 校验链实测（W1-T1，HANDOFF.md:1533；缺一=422 零落目录） | 我们更硬（授权=文件+哈希，不止旗标） | 保持；旗标→scope.tsv 单源（表单旗标只是 scope 的投影，不另立第二约束源） | — | 已超 |
| D6 | 目标历史页：targets 列表/详情/raw/快照/diff/rollback/清除（快照 app.py:194-243；target_state 模块 1,349 行） | 账本即历史：timeline+checkpoint+verify-chain+replay（跨 run 恢复它的对照物=我们的账本重建）；无独立「目标态」存储 | 架构取舍 | **声明取舍**：它的 target_state 与 SessionState/events 三处并行写正是分析档 §6.2 点名的弱点（无单写者）；我们的对等=账本单源+checkpoint。页面呈现（目标维度透视）若 W6 有余量再排，不是缺口 | 可选（W6 附带评估） | 声明取舍 |
| D7 | 报告页：列表/内容预览/下载/按目标生成（快照 app.py:245-271+ReportPreviewDialog.tsx） | /api/report/download 缓存命中或触发 render（server.py:948；路单 server.py:33） | 页面弱 | W6 报告页（A舰 B36 已排：分节锚点+复制+下载三件） | W6 | 已排 |
| D8 | Settings 页在线改配置：GET/POST /api/config+provider 探测（快照 app.py:135-158） | 无设置页；配置=账本单源（goals.tsv model_tier amendment+budget 默认） | 页面缺、哲学异 | W6 设置页（A舰 §四b 已排）；落法=投影账本（改档位=amendment 入链），不做第二配置真源 | W6 | 已排 |

### E. 六引擎测绘与侦察工具族（8 件——我们的真输面，W3 大头）

> 组前记：nuclei 是唯一例外——模板钉 commit+ECDSA 验签（engines/nuclei/{adapter,templates.lock,release.pub}），单件已超；其余侦察枚举工具全空白（03专家:54 判「不及格」，全仓 grep nmap/sqlmap 唯一命中 DENYLIST）。

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| E1 | space_search 六引擎测绘：FOFA/Hunter/Quake/Shodan/ZoomEye/0.zone 统一接口，key 从 config 读（快照 recon_tools.py:6 docstring、:313 execute_space_search；分析档 §2.2） | 0（无任何测绘源；A舰 G4 网络搜索源也=零） | 大 | W3 空间测绘 OSINT 向导（蓝图 W3 行已点名，03P1）：六源工具卡+语法向导；**key 走 vault 四关卡不落 config 明文**（它 recon_tools.py:12 的弱点不抄——缺口 G5）；结果=资产行入账（add-asset），不是聊天文本 | W3 | 已排 |
| E2 | subdomain_enum：被动聚合+小字典 DNS 爆破（快照 recon_tools.py:7,:372-434） | 0 | 大 | W3 工具卡（子域卡）：输出=DNS 记录资产行+edges；配 OOB 申报（新域=scope 复判，A舰 D 组资产过授权复判同源） | W3 | 已排 |
| E3 | js_recon：仿 URLFinder 抓 JS 端点/域名/密钥（快照 recon_tools.py:8,:522；tool_schemas.py:650） | 0（web-blackbox phases/recon.md 有方法论无工具） | 大 | W3 工具卡：JS→端点/密钥；密钥命中走 creds 通道（vault 占位），端点入 endpoint 资产 | W3 | 已排 |
| E4 | dir_enum：仿 dirsearch 并发字典+404 基线/伪装识别（快照 recon_tools.py:9,:819；内置字典 :38-50） | 0 | 大 | W3 工具卡：字典外置 data 不入码（CSAI「工具=数据」律同批吸收）；结果去重哈希入证据（同输出不重复占预算——分析档 §6.1-3） | W3 | 已排 |
| E5 | nmap_scan 端口/服务识别：包装 nmap 二进制+XML 解析+保留 IP 跳过（快照 builtin_tools.py:1302,:1586；tool_schemas.py:487） | 0（nmap 在 DENYLIST 给目标限速条款侧） | 大 | W3 工具卡：nmap 包装卡（参数白名单+输出归一化锚点+tools.lock 验签——自立的供应链律要多锁几把枪，03专家:76 原话） | W3 | 已排 |
| E6 | http_probe_batch 批量探测+unauth_test 未授权探测（快照 builtin_tools.py:1278,:1836；tool_schemas.py:316,:684） | 0（活试 §4.3 它的插件跑出安全头缺失/端点暴露两发现——正是这两张卡的产出） | 大 | W3 工具卡两张：probe 批量卡+unauth 卡（unauth 命中→finding 候选走人证复核，不直入 verified） | W3 | 已排 |
| E7 | 指纹/服务面：space_search 组件字段+nmap service/version 合成指纹画像（快照 recon_tools.py:207 svc 抽取） | 0（matrix.tsv WSTG 词表有测试维，无目标指纹维） | 中 | W3：指纹=资产 meta（assets.tsv meta 列已有位），供 W4 白盒 GT 键对齐与复测分派 | W3 | 已排 |
| E8 | osint_recon 情报工具（快照 intel/tools.py 8 工具之一；分析档 §1.2 模块表） | 0（A舰 G4 同判） | 大 | W3 G4 web-intel（ddgs 免 key 先行+tavily/brave 插槽参数；出网过 Tier3） | W3 | 已排 |

### F. final_answer / verified_claims 结构（5 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| F1 | VerifiedClaim{id,claim,evidence_ids,created_at}（快照 agent_state.py:216-222；AgentState.verified_claims :292-295 带 legacy 别名迁移） | 适配器消费：claims→facts kind=info 置信 0.9（adapter.py:247 normalize 内）；我方原生=EV 卡+findings.tsv 生命周期三桶+replay_state（report_artifacts.py:126-127） | 0（已吃掉） | 保持；它「claim 过闸才算」语义已并入我们 C2 口径（条件实证：过 FINAL 闸门+独立复现，adapter 注释①） | — | 已超 |
| F2 | final_answer 终文本字段（快照 agent_state.py:307）+solve 报告直接从 AgentState 渲染不问 LLM（分析档 §2.2-②） | FD 九段渲染器+词表门+双轴+时间链断言（report_render.py，A舰 I1）；适配器 F 头确定性解析 FINAL→findings（adapter.py:149-200） | 我们下游更硬 | 保持 | — | 已超 |
| F3 | FINAL 完成门：cite 已知证据 id/flag 逐字在证据/无证据拒+拒因回灌（快照 solver.py:475-535,:802-808；活试 §5.1 两轮实弹守住） | 提交协议前移：引擎产结构化 submission（契约 07），散文不能直接变账；P4 独立盲重放 30/30（03专家:56 判「五家无一家有」） | 我们闸门更靠前+有独立重放 | 保持；「flag 逐字包含」细节已体现在 reproducible_steps≥1+evidence_refs 强引用 | — | 已超 |
| F4 | 实测缝：实证发现写在 FINAL 文本而非 finding 工具→findings[] 只剩规则层候选（证据串=模板碎片，与模型否定结论自相矛盾）（活试 §10.2④a） | 适配器①正面处理：FINAL F 段→findings（C2/verified）；findings[] 规则候选降权 vuln-clue 线索队列置信 0.5 须人证（adapter.py:247-336；MANIFEST 归一化表） | 0（它的缝=我们的消费纪律） | 保持；向上游提「finding 工具与 FINAL 双轨」issue（活试 §10.4 建议） | — | 已超 |
| F5 | usage 计量失效：子代理 requests=0/tokens=0 两轮实测不可信（活试 §9.5、§10.4④） | budget.tsv 单源+适配器③网关侧外挂回填：--usage-file 求和入 fact+artifacts 归档，缺位如实记缺位不静默归零（adapter.py:202,:464-482） | 0 | 保持；D2 三臂同考（W1）出数时网关侧对账面已在 | — | 已超 |

### G. SARIF+PDF 双工件与报告出口（4 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| G1 | findings.json 全量+生命周期（快照 findings_output.py:5,:94-130） | 同型已落地：findings_json 全量+三桶映射（report_artifacts.py:95；HANDOFF.md:628 T15） | 0 | 保持 | — | 已超 |
| G2 | findings.sarif 仅 verified+EvidenceRef→artifactLocation 附件（快照 findings_output.py:8,:140-193） | 同型+更硬：SARIF 2.1.0 仅 verified+EV 卡相对路径+ruleId=矩阵词表锚+summary 与结果数恒一致断言（report_artifacts.py:140-180,126-127；R-T15-3 键控加强） | 0（多链签） | 保持；write_all 三工件入 pass.json 绑定+门 FAIL 删件（HANDOFF.md:875 T9）它没有 | — | 已超 |
| G3 | report --pdf：reportlab 可选 extra，md→styled PDF（快照 main.py:2389-2431、pdf_exporter.py:164-192） | **无 PDF 出件**（全仓 grep：PDF 仅作授权书输入 battle.py:557,579） | 小但真 | 零依赖律下两条路（不引 reportlab）：①自写最小 PDF 1.4 writer（文本+等宽表格+书签目录，~300 行 stdlib）落 tanyin-report --pdf；②report-<ts>.md→系统打印链（macOS cups-filter/Windows PrintToPDF）只做包装脚本。推荐①（确定性、可测试）；落 W6 报告页批（下载三格式：md/sarif/json+pdf） | **W6（报告页扩，缺口 G1）** | **真空白（已给方案）** |
| G4 | 报告原则「未经验证的漏洞=误报=不写入」（活试 §4.4 页脚；分析档 §3.3-③） | 同口径+更多门：词表门+双轴+时间链断言+合规六要素+签发面 P5.5 永不代签（report_render/report_artifacts；battle auto HANDOFF:1536） | 0 | 保持 | — | 已超 |

### H. TaskConstraints 与执法面（6 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| H1 | TaskConstraints 11 键模型：allowed/blocked×ports/hosts/paths/actions+strict_mode（快照 domain_models.py:316-328） | scope.tsv 三态（include/exclude/**oob**）+amendment 修订链后行覆盖先行（enforce.py:9-13） | 我们多 oob 态+修订史 | 保持；适配器对外仍输出它 11 键形状（adapter.py:103 build_constraints——对缝不对内） | — | 已超 |
| H2 | 七个工具口重复执法（fetch/MCP/nmap/shell/python/traffic/阶段跃迁，分析档 §4.1 表） | 四层执法 Tier1 guard/Tier2 hooks/Tier3 egress+canary（enforce.py:2 单源；egress_proxy）——**应用层之外有网络边界** | 代差（分析档 §7「执法全在应用层是这个路线的天花板」） | 保持；档位事实进报告守门声明 | — | 已超 |
| H3 | NL 正则抽约束的缝：固定句式才命中，实测措辞不命中→端口维度只剩提示词软约束（快照 input_analysis.py:143-195；活试 §6.3 实测坑） | 结构化通道：授权八问/表单旗标→scope.tsv；适配器**反向利用**其句式——goal 自动增补「仅允许测试 N 端口…」固定句式让其正则命中（adapter.py:406-409） | 0（坑变招） | 保持；上游提「solve 子命令暴露 scope 旗标」issue（活试 §6.3 缺口） | — | 已超 |
| H4 | 无 egress 代理/无 canary（分析档 §4.3；schema.py:340 自认 blacklist 非边界） | Tier3 egress（compile/verify/serve 三态）+canary 判定词表+OOB 申报 | 代差 | 保持 | — | 已超 |
| H5 | ExecutionGate 内容寻址一次性审批：request_hash 单次有效+无通道 fail-closed+自评只能升档（分析档 §4.3；快照 exec_gate.py:78,:322-328） | approvals.tsv+/api/approval 投影（server.py:451 GET、:897 POST 落账）；guard 现只有放行/拒 | 它多「转人工」中间态语义 | W2 ask 三态+judge 接线（A舰 G3 同源）：吸收其三语义——审批粒度=内容哈希/通道=本地 UI/单次有效模型无表决权 | W2 | 已排 |
| H6 | headless 无 TTY 时审批通道不存在→危险工具全拒（活试 §6.4 fail-closed 语义） | 平台无人值守=auto_review 同款+审批卡 Web 面（外层代理审批——活试 §6.4「天然互补」判词） | 0 | 保持；W6 审批中心+watch 审批卡补终端通道 | W6 | 已超（互补） |

### I. 触发词/配置面（6 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| I1 | NL 触发词正则族：「只测/仅测/仅允许测试 N 端口」「不要碰/禁止测试…端口」「不要利用」（快照 input_analysis.py:151,:161,:174,:195） | 不做 NL→约束猜测（结构化授权八问）；适配器仅反向注入其句式（adapter.py:406-409） | 哲学取舍 | **声明取舍**：NL 猜约束=活试 §6.3 实锤的软执法洞；我们约束走表单/旗标/账本三结构化口。对用户话里的约束词→W6 对话页提示「转结构化」按钮（一句话转 scope 行） | W6（附带） | 声明取舍 |
| I2 | skill 路由触发词：「web高级|注入|sql注入|xss|ssrf…」关键词→专题技能（快照 skills/dispatcher.py:27） | knowledge match/nday-match/neighbors（tanyin-knowledge 13 子命令，contracts/09:134）+注入 top-k（W5） | 我们有底无路由词面 | W5 知识环复活批：技法页路由词=front-matter 键（不写死 Python 表） | W5 | 已排 |
| I3 | config.yaml 全量配置+VULNCLAW_CONFIG_DIR/VULNCLAW_LLM_* 等 env 覆盖（快照 settings.py:77,:313-424；活试 §9.1 环境变量注 key 零落盘） | 账本单源（goals/budget/scope 三表）+TANYIN_* env 20+ 词形+~/.tanyin（E舰 §五清点 1478 文件 5929 处） | 形态取舍 | **声明取舍**：配置文件 vs 账本——我们的档位/预算改动全入链可审计；env 面对等已有；W2 改名批带双读一代兼容 | — | 声明取舍 |
| I4 | REPL 配置面板 1,000 行：FieldSpec/SectionSpec 纯状态模型可测（快照 config_panel.py:1-4,:43-80） | 无设置页/面板 | 页面缺 | W6 设置页+llmpool 管理页（A舰 §四b 两行已排）；「面板状态模型与渲染分离可测」的工艺值得抄 | W6 | 已排 |
| I5 | config set/get/list/provider 子命令（快照 main.py:2478-2530） | CLI 对等半件：budgetctl/goals amendment/set-cred-status（registry 面内）；无通用 config 命令（哲学同 I3：配置散入账本命令） | 形态取舍 | W6 设置页 CLI 存档（settings 查询面只读投影）；通用 set/get 不做（账本律） | W6 | 已排 |
| I6 | i18n 中英双语音频目录全量+catalog 平价测试（分析档 §1.2/§5-③；快照 i18n/{zh,en}.json） | 中文单语（README 英文版无） | 取舍 | **声明取舍**：目标用户中文；对外英文面（README_EN）随 W7 发布件评估，不做运行时双语音频 | W7（附带评估） | 声明取舍 |

### J. 知识与语料面（4 件）

| # | VulnClaw 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| J1 | 7 核心 skill md+50 专题目录（快照 skills/core/ 7 个 .md、specialized/ 50 目录实测；分析档计 47） | 已取 8：knowledge/concepts/CP-0001..0008（03专家 P0-5「已取 8」） | 余 39-42 专题 | W3 P0-5：余专题 detail-pack→技法页映射（staging 审批门照走）≈2,400 行知识/3-5 天；MIT 许可允许 | W3 | 已排 |
| J2 | warstories 实战复盘 2 篇（快照 warstories/，分析档 §6.3「先例页天然样板」） | 已映射：knowledge/precedents/PR-0001.md（PHP 正则绕过攻击链三元组+front-matter，2026-09-29 lint pass） | 0（第二篇 PR-0002 在库） | 保持 | — | 已超 |
| J3 | experience 经验库：蒸馏→pending→人工 approve/reject→注入（快照 main.py:3144-3169 子命令；分析档 §5.2；活试两轮 lessons=0 空转） | ingest-staging 四门槛+人审门同型（tanyin-knowledge；分析档 §6.3 判「直接借鉴」） | 结构对等、我们未转 | W5 知识环复活根治+消费者在役（注入 top-k）——它两轮空转恰是「无燃料」证明，我们 D2 同考出数后才有真 lesson | W5 | 已排 |
| J4 | BM25 纯 Python+ChromaDB 语义双轨降级（分析档 §1.2 kb 模块） | stdlib 检索（match/nday-match）；无语义轨 | 语义轨缺 | W5 知识环：语义检索=可选投影层（同 sqlite3 投影取舍，E舰 O7 同批呈批）；核心检索保持 stdlib | W5（附带评估） | 已排 |

---

## 二 · 判词汇总

| 判 | 件数 | 代表件 |
|---|---|---|
| 已超 | 25 | B3/B4（两个 P0 崩=我们的测试用例）、F1-F5（final_answer/verified_claims 全链消费）、G1/G2/G4（双工件同型+链签+恒一致断言）、H1-H4/H6（TaskConstraints 三态+四层执法+NL 坑反向利用）、A1-A4/A6/A7（薄 CLI+插槽制+四维预算+vault）、D5（授权八问>表单旗标）、A2 |
| 已排 | 29 | E1-E8 测绘工具族全排 W3（本档最大输面）、C1-C6 终端面全排 W6、D1/D3/D7/D8 Web 页全排 W6、H5 ask 三态 W2、A5/A8 W5/W2、J1/J3/J4 知识环 W3/W5、B1 W6、I2/I4/I5 |
| 声明取舍 | 5 | D2（React→Vue3 投影面已拍）、D6（目标态第二账本不做——账本单源律）、I1（NL 猜约束不做）、I3（config.yaml→账本单源）、I6（双语单语取舍） |
| 真空白 | **1** | G3 PDF 报告出件（方案已给：自写最小 PDF writer ~300 行 stdlib，落 W6 报告页批）——唯一真空白，一件不悬空 |

---

## 三 · 新增缺口清单（此前任何波次都没排的件——一件不许漏）

> 判据：蓝图 W1-W8 行文+§四b+A/B 舰缺口清单（A舰 G1-G15、B舰 G1-G11）逐字核对，未点名者入本清单。全部给方案与归宿波次（能并入则并入，不滥开新波）。

| # | 缺口件 | 危害 | 方案（可施工） | 建议波次 |
|---|---|---|---|---|
| G1 | **PDF 报告出件**（03专家 P1-5 只点名 SARIF+法务过审，PDF 出口在蓝图任何 W 行无落点；SARIF 已于批次6 T15 落地后此半件悬空） | 客户交付件少一族；对标 VulnClaw report --pdf（main.py:2389）与 CSAI 导出面 | tanyin-report --pdf：自写最小 PDF 1.4 writer（Helvetica 内置字体+等宽代码块+表格+ outline 书签，~300 行纯 stdlib，不引 reportlab 不破零依赖律）；W6 报告页下载三格式（md/sarif/json）+pdf 四件套 | **W6（报告页批扩）**，~300 行 |
| G2 | **CLI 机读事件流契约**（--stream 对等件）：watch --json NDJSON+尾件 summary.json | CI/管道消费 CLI 非一等公民；「输出裸奔」（基线总表:58 原话）只修一半 | battle watch 加 --json：log/status/complete 三型事件+findings 内嵌+退出前 summary.json（对齐 VulnClaw headless 面）；与 B1 同件施工；~200 行 | **W6（终端工作台批扩）** |
| G3 | **watch 事件协议 schema 双端校验**（VulnClaw tui-v1.schema.json 双端验防漂移，protocol.rs:355-380——其架构件未进我们 W6 watch 规格） | watch --json 上线后无 schema 锁=消费端静默漂移 | 协议 JSON Schema 入 contracts/+CLI 出端/终端进端双校验+版本字段握手；~100 行 | **W6（watch 规格扩）** |
| G4 | **退出码第 4 态**（rc3=仅未验证候选——VulnClaw headless.py:38 的 CI warn 态） | 「跑了但有候选没实证」与「干净跑完」在 0/1/2 里无法区分，CI 静默绿 | W2「退出码分离」批落时加一态：active>0 且 verified=0 → rc3（黄灯态）；evals_metrics.py:2 契约行同步；~30 行 | **W2（退出码分离批规格补点）** |
| G5 | **测绘/OSINT API key 治理**（W3 空间测绘向导的前置：六源 key 若照抄 VulnClaw 从 config.yaml 明文读——recon_tools.py:12——则 vault 四关卡被旁路） | key 落盘明文=目标侧凭据管理的洞平移到测绘侧 | W3 工具卡批规格扩：测绘 key 只走 {{vault:}} 占位+env 注入（活试 §9.1 key 纪律同款：跑后全工件 grep 验证零落盘）；卡 schema 带 key 来源声明列 | **W3（工具卡批规格扩）** |
| G6 | **W1-T6 适配器两遗留**（HANDOFF.md:1530：golden 面未注册；--run 实弹路径待有效 key 真机验证） | 适配器只有离线面测试覆盖，实弹轮（--run→solve→归一）未走过真 LLM | W1 收尾：golden 面注册进总控定夺清单；有效 key 到位后跑一轮 --run 实弹（剧本=活试 §9.8/§10.5）并核对 PyPI 新版是否已修 P0#1/#2 | **W1（收尾件，不新开）** |

**工程量净增**：G1 ~300 行、G2 ~200 行、G3 ~100 行、G4 ~30 行、G5/G6=规格与流程——合计 **~630 行**，全部并入现有波次（W2/W3/W6 各一小块），不开 W9。

---

## 四 · 证据可复核性声明

- 对手每件出处=三源实读：分析档（174 行全读）、活试（439 行全读，§9/§10 重点复核）、快照 .research/repos/VulnClaw@3b71e26（712 文件只读；19 命令经 @app.command 逐个枚举实数 19；Rust 行数经 wc 实测 5,355；specialized 目录实测 50、分析档口径 47 照录差异）。
- 我方每件出处=仓内实读行号（2026-10-18 快照，main@e38e339 之后含 W1-T1/T4/T6 提交）：adapter.py 494 行全文通读；registry/report_artifacts/enforce/sse/server/battle 各引行均逐行核对；SARIF 落地以 git log（c96db82 批次6 T15）+HANDOFF.md:628 双证。
- manuals/ 五本经 grep 'vulnclaw' 计数 0——任务书所列「manuals 下 vulnclaw 相关」语料不存在，已在本档头如实勘误。
- 本档为唯一写入件；语料与代码零改动（快照与 venv 均只读未跑）。它侧两 P0（main.py:1578/:1609）与 usage 计量失效（活试 §9.5）照实记录——这些是我们插槽纪律的设计输入，不是贬损。

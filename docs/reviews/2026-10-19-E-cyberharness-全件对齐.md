# E · cyber-harness 全件对齐（逐件表）· 2026-10-19

> 执笔：E 舰（域=cyber-harness 全面）。纪律：语料与代码只读，唯一写入=本档；零代码，禁碰兄弟舰在树未提交件（cli/warrior/context.py、cli/webui/console.* 等 10 件不触）。
> 对手仓：`.research/repos/cyber-harness`（下称 **CH**；git 0d812fe，chainreactors/cyber-harness，AGPL-3.0，Go 1.26，1045 个 Go 文件含 458 测试文件，exts 31 个扩展目录）。实读：README.md/README_CN.md 全文、docs/{architecture,concepts,agent,scan,reference,jev,mcp,arsenal-bundles,observability}.md 全文、docs/user/{web,tools,knowledge,sessions}.md 全文、cmd/audit/README.md 全文；代码实读=四入口 main、agent/loop.go、tools/scan/{command,verify,options}.go、exts/guardrail/runtime.go、pkg/harness/base.go、pkg/node/agent.go、pkg/web/service/store_schema.go、web/frontend QuickConnect 两件。
> 我方仓：`/Users/wgen/redteam-agent`（下称**仓**，GraphLed；git main@881ca96）。波次基线=`docs/design/exceed-blueprint-2026-10-17.md`（下称**蓝图** W1-W8=蓝图:22-29）。
> 人话词表（宪法#41，黑话首现即译）：**扩展**=把一项能力装进程序的组合零件，CH 的全部能力都这么装；**入口**=一个独立可执行产品（同一套零件按需组装出四个）；**节点回连**=执行机主动连回控制台领活干；**三库**=网页控制台存的三类数据（会话/事件/工件）；**工件**=工具跑出来的原始产物文件；**流水线**=扫描引擎按发现互相触发的链条；**租约**=战士领任务时打的时限标记，过期可回收。
> 判词四档：**已超**（超越点实打实）/ **已排**（波次有名）/ **声明取舍**（对等策略，用户知情）/ **真空白**（不许留，发现即给方案）。
> 一句话总判：**cyber-harness 是一台「零件工业化、四入口分工、节点回连成型、判定与执行分层干净」的 Go 军用底盘——工程完成度五产品最高；但它是无授权管控、无防篡改、验证靠 LLM 语义判定的通用底盘，赢在装配工艺，输在证据法权。逐件 67 件对齐后：已超 28 件、已排 17 件、声明取舍 16 件、真空白 6 件——连同复合判中揪出的子件共 9 项新缺口全部给方案入波次，一件不悬空。**

---

## 〇 对底册初记的校对（CODEBASE-ATLAS.md:30-32 点名本舰）

| # | 底册原记 | 校对结论 | 证据 |
|---|---|---|---|
| C1 | 「exts 十五件(proxy录音/pty/mcp/otel/ioa)」 | **计数失真**：exts 下 31 个扩展目录（33 项含 doc.go+guard_test.go）。标准 aiscan 装配≈26 个，full 再加 browser/record。本档 §C 全量 31 件分七族覆盖 | CH exts/ 目录实测；cmd/aiscan/extensions.go:42-78+profile.go:25-44 |
| C2 | 「四入口」 | **准确但少记第五形态**：四入口外还有「make 自组最小应用」（README:145-150 给 cmd/my-agent 十行模板）与嵌入会话——发行矩阵是 4+2 | CH README.md:25-31,110-116,145-150 |
| C3 | 「--verify=off 确定性扫与AI验证分离」 | **方向对但漏了精髓**：分离不止一个旗标——三层解析链（CLI 显式＞节点 scan.verify 配置＞有模型默认开/无模型默认关）+「显式开验证而无模型=探测前硬错，不静默关」（tools/scan/command.go:151-152）；verify 是流水线排空后的独立 pass，不掺入引擎 | CH tools/scan/command.go:133-152,229-231；docs/scan.md:69-76 |
| C4 | 「Quick Connect 一行命令节点回连分布」 | **少记了密钥拓扑**：安装命令把访问令牌放 URL userinfo（node-bootstrap.ts:42-45），节点进程本身零模型密钥——注册后模型配置由 Hub 下发才点火（pkg/node/agent.go:65-67）。「执行机无密钥」是比命令本身更值钱的形态 | CH web/frontend/src/lib/node-bootstrap.ts:40-61；pkg/node/agent.go:29,65-67 |
| C5 | 「会话-事件-工件三库」 | **准确**：SQLite 四表 chat_sessions/chat_aop_events/raw_artifacts/aop_request_ledger，事件按 event_id 去重、工件按 result_id 关联；schema 精确匹配无迁移（不匹配=报错要求重建） | CH pkg/web/service/store_schema.go:38-62,125-133 |
| C6 | （未记）cyber-audit 已被吸收 | 前舰已对 cmd/audit 做逐件对照（借四超八，docs/design/source-audit-v1.md:103-120），本档入口级收口不重复展开 | 仓 docs/design/source-audit-v1.md:103-132 |
| C7 | （未记）规模与许可 | AGPL-3.0（README:11 徽章）+Go 单仓 1045 文件；对企业采购是同 ARTEX 一级的雷，我方 Apache-2.0 已超 | CH README.md:11；仓 LICENSE |

---

## 一 · 逐件表

### A. 四入口与发行形态（7 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| A1 | `aiscan` 标准发行：agent/scan/七扫描器子命令+web+serve（README:25-27；cli.go:30-35） | 单仓 CLI 家族 20 个 tanyin-* 命令+四运行方式（README:33-72） | 形态异（子命令 vs 家族命令） | 不改：家族命令=零依赖律的自然形态；补「一命令总门」tanyin-serve 已在（cli/tanyin-serve:3-17） | — | 声明取舍 |
| A2 | `aiscan-full`：加浏览器/被动测绘/深爬/录屏（README:27,112-113；editions.env 构建标签） | 无发行分层；能力=装不装的问题（引擎按需） | 中 | W7 单文件分发批按需出件：核（账本/执法/CLI/界面）必带、引擎下载按需——对等它的 full/standard 分层 | W7（分发批，蓝图:28） | 已排 |
| A3 | `cyber-audit`：独立 Go 模块源码/二进制审计，七工具钉版+证据目录+validate 两轮修复帽（cmd/audit/README.md:61-72,114-123,174-190） | 源码审计设计定稿：谱图三层+黑白互证，借四超八（docs/design/source-audit-v1.md:103-132） | 设计在册未施工 | 照 SA-1..SA-4 落地；地基=W4 白盒 | W4+W7+（source-audit-v1 波次表） | 已排 |
| A4 | `cyber-web`：profile 中立 Hub，只管节点/会话/事件/配置（cmd/cyber-web/main.go:29-34,93-101） | webui=单机控制台（cli/webui/server.py 全 1253 行；console 五页投影 console.py:2-11） | 我们无「中立控制台/执行节点」二分（单机形态） | 不拆二分；W7 多用户设计（multiuser-assetlib-v1.md）吃下「控制面/执行面分离」的安全语义而不引入远程节点复杂度 | W7 | 声明取舍+已排 |
| A5 | `agent` 最小发行：无扫描器/代理/IOA/Web，文件+终端+Skills+本地子代理（README:30,128-135；cmd/agent/main.go:27-53） | cli/warrior 最小战士：一进程一循环 2350 行（cli/warrior/__main__.py:3-14） | 形态对等 | 保持——我们「最小可执行单元」=战士进程，比它的 REPL agent 更贴产品律 | — | 已超（贴产品形态） |
| A6 | make 自组应用：BaseExtensions 13 项有序装配+自选扩展（pkg/harness/base.go:44,66-80；README:145-150） | 无装配机制；模块=Python 包按需 import（cli/ledger 50 模块） | 中（工程工艺差） | 不搬扩展框架（单进程零依赖律）；吸收「组合根显式有序+依赖只向前借」纪律：ledger 各模块 import 图 CI 化（architecture 检查它有 pkg/internal/architecture 测试，我们没有同级守卫） | W2（CI 三件扩） | 真空白→已给方案（小） |
| A7 | 发行矩阵四平台六目标交叉编译+CI 单测+链边界测试（cmd/audit/README.md:218-222；.github/） | 三平台等价靠 py -3 纪律+tests 251 文件 2434 用例；CI 三件=W2 已排 | 中 | W2 CI 落地时补「依赖边界检查」一件（借它的 go test ./pkg/internal/architecture 思路，用 import-linter 或自写扫描） | W2 | 已排 |

### B. QuickConnect 节点回连与远程执行（5 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| B1 | 快速连接面板：OS/架构/发行档/节点名/双下载源（global/china 镜像）五选择（QuickConnect.tsx:53-68,154-157；node-bootstrap.ts:20-28） | 无远程节点概念；分发=W7 单文件批 | 大（形态级） | 单机一人红队=产品律；多机作战若立项，抄它的「面板生成命令」而非手写文档 | W7（分发批参考件） | 声明取舍（单机形态） |
| B2 | 一行安装命令：mktemp+curl+unzip+chmod+exec+trap 清理；Windows PowerShell 等价（node-bootstrap.ts:40-61；web.md:21） | 安装=git clone+python3 直跑（README:23-27） | 中（开箱体验） | W7「15 分钟开箱」直接套此命令形态：curl 单文件→sha256 验签（我们有 ECDSA，它没有）→运行 selfcheck 冒烟→起 serve；比它多验签一步 | W7 | 已排（形态照抄+验签加层） |
| B3 | 「仅上线」命令：复用已装二进制，令牌在 URL userinfo（README:58-60；node-bootstrap.ts:42-45） | 无对应 | — | 同上并入 W7（升级路径=版本清单+ECDSA 验签+回滚，A舰 K3 方案续用） | W7 | 已排 |
| B4 | 节点注册：能力随注册申报（agent.go:29）；节点零模型密钥，Hub 下发配置才点火（agent.go:65-67,107-120）；运行中配置热重载（agent.go:135-170） | 战士密钥拓扑=操作员持钥+WARRIOR_ENV_ALLOW 白名单剥离密钥（cli/tanyin-runner:33-49）；llmpool channels 文件带 api_key 进战士 | 部分对等（本地已剥离 env 面） | 把「执行单元不落密钥」推到底：channels 文件的 key 改经 runner 注入内存（不落战士可读盘面），llmpool 状态文件无密钥——一半已做一半补 | W5（多战士编队规格扩） | 已排（拓扑律吸收） |
| B5 | 扫描服务按节点能力路由：无扫描节点=FAILED_PRECONDITION 硬错；节点断线=扫描标失败（web.md:62-66） | 引擎调度=本地 intents 派发+租约回收（cli/ledger/write_cmds.py:514-525） | 形态异 | 我们的对等律已在：意图无可用引擎=blocked 留因；保持 | — | 已超（执法粒度更细：租约+因） |

### C. exts 三十一件全量（七族分组）

**C-1 核心运行时族（5 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C1 | exts/agent：循环装进扩展生命周期，管调用准入/取消/排空（agent/extension.go:1-3） | warrior 循环=领意图→组上下文→llmpool 选道→JSON 指令块→tool/ledger→写账（cli/warrior/loop.py:3-27） | 对等已建 | 保持；生命周期纪律（排空后关）已在 runner 停序 | — | 声明取舍（对等已建：W5 MVP 在役） |
| C2 | exts/session：会话运行时，配置变更换 Profile；/model 只影响下一次 Run（session/extension.go:1-2；architecture.md:44） | 无会话抽象；battle=会话等价物（goals+state 在盘） | 中 | W6 介入对话页+会话投影（server.py /api/session.json 已有数据面）补齐面；「热切只影响下次 Run」纪律抄进 W6 规格（amendment 生下次回合） | W6 | 已排 |
| C3 | exts/provider：模型连接/profile 多档/重试容错（architecture.md:161-165：逻辑消息 ID 复用+流式撤回+用量保留） | llmpool 离线判定核：错误分类/分道冷却/±20% 抖动（cli/ledger/llmpool.py:3-20）+warrior model_client 直调 | 判定核已超（抖动/分道它没有）；实链=A舰 G2 在排 | W2 池实链落地时补它的两条：流式失败撤回正文但保留用量计量；重试沿用逻辑消息 ID 防重复计费 | W2 | 已超（核）+已排（链） |
| C4 | exts/subagent：sync/async/fork 三模式+具名定义+catalog/list/kill（web.md:70-87；architecture.md:62-68） | 多战士=同侪编队非子代理：intents 租约+owner 标记（write_cmds.py:514-525）+warrior-stop/steer（steer.py:6-11） | 形态异（父子 vs 同侪） | 声明取舍：同侪+租约=账本执法形态，比父子树更可审计；fork 模式的「继承上一完整工具批次边界」记忆法留给 W5 记忆补全参考 | W5（编队） | 声明取舍（形态）+已排 |
| C5 | exts/prompt：具名 section 按 target 选择，一次 Run 内不变（architecture.md:147） | AGENTS-INJECT 八条+SKILL.md 协议原样注入（hosts_matrix.py:6-8；loop.py:7-10） | 小 | 「Run 内提示词冻结」纪律已在（一回合一组上下文）；补 timeline 记录每回合提示词 digest 供回放对账 | W5（规格补点） | 已超（纪律同+账本化更硬） |

**C-2 执行环境族（7 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C6 | exts/files：root+只读 URI 挂载+路径/类型/大小限制+同目录临时文件 rename 原子写（architecture.md:131） | 战士文件面=工作目录+禁裸 /tmp 纪律（README:115 任务书补令）；无文件工具注册面 | 中 | 工具卡族补「文件读写卡」：路径白名单=goal 目录+knowledge 只读挂载（对齐它的 mounts 思想），写入原子性=临时文件+rename | W3（卡族扩） | 已排 |
| C7 | exts/terminal：bash=mvdan 解释器+注册命令优先于 PATH（architecture.md:127） | tools/gate 卡层门链五门（unknown-tool→卡黑名单→supply-chain→限速→L3 审批）+guard 委托（cli/tools/gate.py:3-14） | 我们无 shell 解释器（进程直发） | 声明取舍：不进 shell 解释器（攻击面大）；注册命令优先=卡层已有同语义 | — | 已超（门链深五层）+取舍（解释器） |
| C8 | exts/tmux：后台任务+wait/timeout 转后台+完成回 Inbox（tools.md:50-65；architecture.md:129） | runner 进程组击杀+停滞检测+死亡续跑（tanyin-runner:7-10）；无「长命令转后台继续答」 | 中 | W5 战士循环补：tool_spawn 超时阈值→后台化+结果经 timeline 回收下回合消费（数据面已全） | W5 | 已排 |
| C9 | exts/pty：PTY 进程接入统一工作注册表 | 无 PTY 面 | 小 | 声明取舍：卡面工具全非交互（nuclei/sqlmap --batch）；交互需求出现时经 C2-lite webshell 档走（已有） | — | 声明取舍 |
| C10 | exts/native：原生 Executor 执行 Reflex 同步 JS+副作用身份（task/步骤/occurrence）防重放（architecture.md:111-115） | 无对应（机械面=phases_engine 确定性状态机，cli/tanyin-phases:3-8） | 形态异 | 声明取舍：我们「可复用判定」走账本规则（patterns/learned+nday-match）不走嵌入 JS；它的「副作用身份防重」思想已被 REPLAY_CAP+判定产物只增覆盖 | — | 声明取舍+已超（同律异形） |
| C11 | exts/proxy：egress.Endpoint+单次路由租约（proxy url cmd 带 token）+MITM Hub（flows 8MiB body/2GiB 总量/敏感头脱敏）（architecture.md:139-143；reference.md:262-267） | Tier3 egress：CONNECT 判定+DNS pin+OOB 落账+canary 告警；不解 TLS=架构声明（cli/ledger/egress_proxy.py:3-13） | 执法面我们超；录制面它有我们无 | 保持取舍（客户环境截 TLS=合规雷，A舰 B39 同判）；「单次路由租约」形态好：egress 加 --once token 租约（一次性出口授权），~80 行 | W6（流量三源回传批附带） | 已超（执法）+取舍（MITM）+已排（租借形态） |
| C12 | exts/arsenal：外部工具包管理+构建时嵌入+PATH 注入+arsenal.yaml 单源版本目录（arsenal-bundles.md:3-29；extensions.go:36-40） | tools.lock 26 行供应链+ECDSA 验签+tanyin-tools install（cli/ledger/supply_chain.py:1-8） | 验签我们超；嵌入分发它有 | W7 分发批：核内嵌（零网络首启）+引擎按需下载沿 tools.lock 验签——嵌入抄它，安全抄我们 | W7 | 已超（验签）+已排（嵌入） |

**C-3 知识技能族（5 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C13 | exts/skills：Skill 库+四级来源覆盖（Bundle＞.cyber/skills＞.agent/skills＞CLI 路径）+虚拟路径 cyber://skills（knowledge.md:42-44；architecture.md:149） | .opencode/skills/tanyin 技能+knowledge/ 知识库 14 子命令（cli/tanyin-knowledge:16-19）+DSH 技能 provider 随包分发（README:76-87） | 覆盖链它细；账本化我们超 | 补「来源优先级」显式化：技能解析顺序写进 tanyin-knowledge lint 输出（项目级＞安装级＞仓级），一行档 | W5（知识环） | 已超（机械门）+已排（优先级显式化） |
| C14 | exts/okf：OKF 知识格式（索引/概念/来源/历史）+okf validate/test 校验命令不执行正文（knowledge.md:50-52） | knowledge 机械运算 14 子命令（lint/approve/commit/promote/demote…）+cp-index.tsv 溯源（tanyin-knowledge:3-6） | 对等异形 | 已超面：来源/验证状态/审批流账本化（它 OKF 无审批链）；「校验不执行正文」纪律我们同（铁律 7） | — | 已超 |
| C15 | typed skill：agent:true 元数据定义子代理型技能（knowledge.md:46） | 引擎委派单六要素（web-blackbox MANIFEST 六要素） | 对等异形 | 保持委派单形态（更全：预算份额/纪律约束在单内） | — | 已超（委派单要素更全） |
| C16 | exts/jev：choice/score/noul 三型判定+Claim 内容寻址+Reflex 编译/资格验证/回放发布（jev.md:13-27；architecture.md:89-119） | judge_client 在册零消费者（A舰 G3 同源发现） | 大（投资闲置） | W2 G3 落地时借它的「判定内容寻址 ID」：同题判定复用缓存省 token；Reflex「发布前至少一条完整回放」纪律=我们金样钉测同律 | W2 | 真空白（接线）→已给方案 |
| C17 | 知识渐进读取：库存在≠全文进请求，按需读（knowledge.md:9；concepts.md:37） | kb_context：确定性打分 top-k 注入+零命中零注入+失败静默降级（cli/warrior/kb_context.py:9-18） | 我们更省（检索面永不炸） | 保持；补它的「usage 计数」：技法卡命中记 timeline skill 事件，热卡可见（A舰 B51 同件） | W5 | 已超（注入律）+已排（usage 面） |

**C-4 安全管控族（2 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C18 | exts/guardrail：两段判定（风险→后果，auto 模式）+safe 人工审批+5min 超时+失败=fail-closed BLOCK+legacy off 不旁路（runtime.go:29-34,97-130,140-160,236-259；tools.md:26-46） | guard Tier1-3：四层 scope+deny 黑名单+时间旅行+凭据覆盖+三帽（tanyin-guard:13-17）+卡层五门+审批 HMAC+REPLAY_CAP | 各有超面：它=LLM 语义风险判定；我们=目标范围执法+账本留痕 | W2 G3 ask 三态落地时吸收两件：①两段制——ASK 档先判风险再判后果，后果明确无害才 auto 放行；②判定服务失败=fail-closed REJECT（我们 judge 失败现走向待定，钉死为拒） | W2 | 已超（执法深度）+真空白（语义判定档）→已给方案 |
| C19 | 重复拒绝退避：同参数重试计数+250ms×min(n-1,8) 递增等待+「勿重复同调用」提示回模型+1024 计数帽（runtime.go:162-178,206-230） | 卡层 card-rate 限速滑窗（gate.py 门四）；无「同参数重复拒绝」专门退避 | 小 | 卡层门四扩：拒绝结果记 (卡,参数哈希) 计数，重复第 2 次起延迟递增+提示语——防被俘战士刷门，~40 行 | W2（G3 同批） | 真空白（小）→并入 W2 |

**C-5 观测族（4 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C20 | exts/observe：--observe 五类选择性观测（tools,commands,processes,files,http）；未装观测不因存日志自动产生（architecture.md:176） | timeline 全事件+trace_search+usage 真行外挂统计（console.py:7-13,57-64） | 形态异（全量律 vs 选择律） | 已超面：全量入链=审计刚需（选择性观测=可被关掉的证据）；借它的「输出契约明示」：serve 输出契约页注明每字段来源观测面 | W1 已完（输出契约） | 已超 |
| C21 | exts/otel：AOP→OTel 三信号（GenAI/OpenInference 语义）接 SigNoz/Phoenix（observability.md:5-19） | 无 OTel 导出 | 中（企业可观测） | 声明取舍+评估位：单人作战不需要观测栈；企业化（W7 后）若客户要求，timeline→OTel bridge 是纯投影件（O7 同律：坏了删了重建） | W7 后评估 | 声明取舍 |
| C22 | exts/recap：任务完成摘要（不阻塞/失败跳过/不进恢复上下文/迟到丢弃）（sessions.md:45-47） | settle 战毕评分+FD 九段报告（README:53-57） | 我们重（判据级）它轻（体验级） | 已超（我们的 recap=带链验证的评分不是装饰摘要）；「迟到摘要丢弃」纪律记入 W6 会话页规格 | W6 | 已超 |
| C23 | exts/telemetry：logger 注入面 | print+日志文件+webui serve.log（tanyin-serve:8-10） | 0 | — | — | 声明取舍（对等） |

**C-6 协作与远程族（4 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C24 | exts/ioa：消息空间 Space+send/read/inbox_wait+--interrupt 让位（web.md:89-131；architecture.md:56-60） | directive-file 指令通道+say 留痕（server.py 写面）+steer 事件注入（steer.py:3-11） | 它=多 Agent 对等协作；我们=总控→战士指令 | 已超面：指令必落链（它 IOA 内存存储重启丢，web.md:19 白纸黑字）；inbox_wait「等消息不轮询」好——steer 已是每轮 scan 增量消费（loop.py:8-9），形态等价 | W6（介入对话页） | 已超（持久性）+对等（等待形态） |
| C25 | exts/node：节点扩展（注册/能力申报/配置热重载） | 无远程节点 | 形态级 | 同 B4 取舍；热重载的「配置变更取消在途执行+待审批」纪律抄进 W7 多用户设计的配置变更节 | W7 | 声明取舍 |
| C26 | exts/web：Web 管理服务+manifest+能力申报路由（cyber-web/main.go:93-101） | webui server 12+v2 路由+console 五页（server.py:6-44；api_v2_tasks.py:41-42） | 页面丰富度它高（20+面板含 Reflex/Guardrail/IOA/终端） | W6 八页+兄弟舰在树五页齐后对齐面；不抄它的 IOA 控制台（无对应形态） | W6 | 已排 |
| C27 | exts/cstx：浏览器 WASM 把原生产物投影为资产节点+IndexedDB 存资产/观测/证据/消费位置（architecture.md:190-192） | viz_render SVG 泳道图（console.py:12-13） | 形态异（零框架律） | 声明取舍：SVG 投影=服务端渲染可归档；「历史查询只读所选 operation 不用全局最新值」纪律我们已同（事件溯源后行覆盖，console.py:49-54） | — | 声明取舍+已超（同律） |

**C-7 扫描与外部工具族（4 件）**

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| C28 | exts/scanner：七扫描器接入+verify/sniper 借 subagent 贡献点同步执行+executionOnly 无模型档（scanner/extension.go；command.go:120-122） | 引擎双形态：cli 引擎（nuclei adapter，MANIFEST kind:cli）+skill 引擎（web-blackbox 六要素委派）；25 张工具卡在役（cli/tools/cards.py card_names） | 它引擎多我们门深 | 引擎数量不追（宪法#43 火力深度优先于广度）；executionOnly「无模型档」=我们干跑模式对位（README:70-72） | — | 已超（门链+委派单）+对等（干跑） |
| C29 | exts/proton：敏感信息扫描（keys 规则/管道输入）（reference.md:329-353） | tanyin-redact+vault 真值 token 化（tanyin-guard:32-37） | 方向相反：它扫内容找密；我们持密防漏 | 补一张「密钥面检查卡」：对 goal 目录/workdir 跑密钥正则（借它规则表）→命中=发现卡+证据，服务合规交付 | W3（卡族扩） | 真空白（方向）→已给方案 |
| C30 | exts/search：web_search/fetch+Tavily 插槽（tools.md:87） | 无网搜源（A舰 G4 同源） | 中 | W3 web-intel 卡（ddgs 免 key 先行+Tavily 插槽参数）——它「搜索优先走支持判定的 Provider」思路记入：搜索能力挂 llmpool 档位 | W3 | 已排 |
| C31 | exts/mcp：MCP→CLI 映射，服务别名=命令/工具=子命令/schema=参数（mcp.md:3-5）；exts/browser+exts/record：playwright 持久会话+录屏（tools.md:81；record.md） | MCP=插槽制声明（蓝图:56 W7 可选）；浏览器自动化=无 | MCP 取舍已裁 | 浏览器自动化真空白：SPA 渲染/登录态测试=漏报源。方案=W3 卡族扩「浏览器会话卡」（playwright headless：导航/点击/截图/表单；截图入 E-index 证据；流量经 egress 边界；登录态=会话目录持久） | W3（卡族扩）；MCP 维持 W7 可选 | 真空白（浏览器）→已给方案；取舍（MCP/录屏） |

### D. --verify 分离与扫描流水线（6 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| D1 | --verify 三层解析：CLI 显式（空值=用法错）＞节点 scan.verify 配置＞有模型开/无模型关；显式 on 无模型=探测前硬错（command.go:54,133-152；reference.md:429,95） | 验证=P4 机械重放，天然零模型依赖（tanyin-replay:5-11 三态）；干跑=零对外请求 | 我们验证不烧 token、结论可重放 | 吸收「显式要验证而条件不备=硬错不静默降级」为通用门律：凡 CLI 显式要求 X 而 X 前件缺失=rc1+说明（replay 无证据卡已同；推广到 --eval类旗标自检） | — | 已超（机械验证确定性+成本零）+已排（门律推广） |
| D2 | verify pass：全量漏洞+弱口令不按严重性过滤；status: 行解析三态 confirmed/not_confirmed/inconclusive；错误=inconclusive 保留原始证据（verify.go:13-43；scan.md:76） | 重放三态 reproduced/not-reproduced/env-diff+matcher 评估+判定产物只增（tanyin-replay:5-11） | 判定基准异：它=LLM 语义；我们=matcher 机械 | 已超（宪法#43 误报率：机械 matcher＞LLM 自评）；「错误=inconclusive 不吞证据」我们同（fail 保留判定产物） | — | 已超 |
| D3 | sniper 情报 pass：指纹→公开漏洞研究，不当确认；status: info/not_confirmed/inconclusive（verify.go:45-92；scan.md:78） | 知识 nday-match+CP 卡关联（tanyin-knowledge 子命令）；web-intel 卡 W3 | 它有实时公开情报源 | W3 web-intel 卡落+kb_context 关联信号补「指纹→公开漏洞研究」意图模板（意图模板=battle-kit BRIEF 族） | W3 | 已排 |
| D4 | 规则流水线：能力接受特定事件；建 DAG 防环；按路由+目标键去重；排空才结束（scan.md:21,38） | 引擎调度=LLM 规划（P2→P3 意图）+R2 串行链 prereq 提升（loop.py:25-27）；phases trigger 闭包审计（tanyin-phases trigger-audit） | 范式差：规则驱动 vs 模型驱动 | 声明取舍（主航道=模型驱动，规则链=干跑/低成本批扫场景）；若客户要「无模型确定性扫」：phases_engine 已是状态机+引擎卡在册，出 scan-pipeline 档（触发规则表驱动引擎卡链）~600 行，挂 W3 可选 | W3（可选档） | 声明取舍（范式）+已排（可选档） |
| D5 | 并发诚实披露：--thread=容量缩放基准非硬帽；分配 80/10/10/10 合计 110% 写进文档（scan.md:61-65） | 卡层 card-rate 限速+guard 三帽（rlimit/CPU/时长） | 我们更硬（真执法帽） | 保持；它的「文档诚实披露上限语义」抄进工具卡手册（每卡标容量语义） | W3（手册） | 已超（执法帽）+已排（披露律） |
| D6 | 回放渲染：-F 读事件不重复探测+--view-format markdown 出报告（scan.md:88-95） | tanyin-replay 重放=真实再发请求（验证语义不同）；报告=FD 九段+SARIF（report_render） | 语义不同非差距 | 「事件回看渲染」我们=trace_search+session 页（B19 已排 transcript 渲染） | W6 | 已排 |

### E. agent 循环（8 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| E1 | 五步标准循环：BeforeRun→排 Inbox→请求→校验执行工具→停查（architecture.md:46-54；loop.go:84-263） | 战士循环：领意图→组上下文（一意图一脑）→模型→JSON 指令块→tool/ledger→写账（loop.py:3-27） | 对等异形（它对话制我们任务制） | 保持任务制（账本执法前提） | — | 声明取舍（对等异形） |
| E2 | 六停因枚举：completed/terminated/stopped/budget/canceled/error 各自成态（architecture.md:70-81；loop.go:234-263） | 停序五条+收敛判据：让位→stop→预算帽→时间窗→停滞重生；无可领即停（loop.py:14-19）；RunReport 带状态（loop.py:32-47） | 它多 terminated（工具批次请求终止） | 协议 JSON 指令块加 finish 指令=同 terminated（~20 行）；停态字典对齐六态名便对账 | W5（规格补点） | 已排 |
| E3 | 同轮工具并行：默认上限 16 信号量+批次内无隐式排序+结果按原调用序追加+截断响应不执行工具（architecture.md:54；loop.go:498；defaults.go:15） | 战士串行执行指令块内 tool 调用（loop.py 链路单发） | 中（吞吐） | 协议扩多 tool 指令并发：线程池+原序追加结果+guard 门链天然线程安全（flock 在账本侧）；测绘类意图（nmap+subfinder+dig 同回合）直接提速 | W5（多战士编队同批：单战士并发工具） | 真空白→已给方案 |
| E4 | Inbox：优先级有界队列+后台生产者注册+满队替换低优+中断打断请求（architecture.md:56-60；loop.go:90-114,145-157） | steer 定向注入=每轮模型调用前 scan 增量消费（steer.py:3-11；loop.py:8-9） | 它细（优先级/替换策略） | 声明取舍：单战士单意图指令流简单即对；W5 编队多战士时如需优先级，timeline 事件天然有序 | W5 | 声明取舍（对等够用） |
| E5 | 压缩：阈值触发（窗口-预留）+孤立 tool result 不切分+空摘要不替换+溢出恢复一次（architecture.md:151-159） | R1 一意图一脑：上下文=SKILL 协议+意图行+相关 facts+末行断点（loop.py:8-10；ctx_tokens 24000 帽 __main__.py:8）——长会话问题被结构性消灭 | 我们优（结构性） | 已超（账本=记忆，脑=一次性）；「精确证据存文件不进摘要」我们同律（E-index） | — | 已超 |
| E6 | Goal Evaluation：-e 验收标准独立请求判 pass/continue+反馈回注+上限 20 轮（agent.md:48-58；architecture.md:83-87） | P4 门+settle 56 分母召回评分（机械判据）+gate-exit:P4 完成判据（README:53-57,117） | 判据性质：它=LLM 自评；我们=机械评分 | 已超（宪法#43：LLM 自评验收=玄学，机械判据=考卷）；无机械判据的杂务任务若要 eval，llmpool 档位挂 eval 模式（W5 插槽参数化，不做硬件） | — | 已超 |
| E7 | 重试：可重试错误退避+鉴权/参数错直返+流式失败撤回正文保留用量+逻辑消息 ID 合并（architecture.md:161-165） | llmpool 分类+分道冷却+抖动+熔断（llmpool.py:3-20） | 对等已建 | W2 实链时对齐两条细律（撤回保留用量/消息 ID 合并） | W2 | 已排（细节并入） |
| E8 | 周期任务 /loop+--heartbeat：经调度器投 Inbox 由模型执行，非 OS 定时器绕过（sessions.md:23-27） | heartbeat.py 5 分钟心跳+停滞自杀重生（loop.py:14-16；__main__.py:8） | 对等 | 保持（我们心跳还带停滞执法，它只是唤醒） | — | 已超（心跳+执法一体） |

### F. 会话-事件-工件三库与记录恢复（6 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| F1 | 会话表 chat_sessions：id/node_id/status/archived/title/session_json（store_schema.go:59） | battle 目录+goals.tsv+state.md+battle_registry | 形态异 | TSV 账本律（A舰 J1 同判）；archived=我们的 battle 归档（A舰 B17 W6） | W6 | 声明取舍+已排 |
| F2 | 事件表 chat_aop_events：event_id 会话内唯一去重+cursor 投递位+turn_id 关联（store_schema.go:51-58；architecture.md:182「Event.seq≠delivery_cursor」） | timeline.tsv 哈希链 O(1) 追加+epoch 戳（timeline.py:3-14）；帧=行号（console.py:13） | 防篡改我们独有 | 已超（核心护城河：链+verify-chain 第三方可验 vs SQLite 可改无痕） | — | 已超 |
| F3 | 工件表 raw_artifacts：原始产物归档+按事件 ID 去重+operation/result_id 关联证据（store_schema.go:60；architecture.md:190） | E-index.tsv 证据卡+报告产物+replay 判定产物只增+sha256 字节锚（C2 echo 同律） | 关联模型对等；完整性我们超 | 已超（工件哈希入链）；「result_id 关联」细律记入 W6 工作区页规格（产物↔证据卡互链） | W6 | 已超+已排（展示） |
| F4 | 请求台账 aop_request_ledger：request_hash 幂等去重（store_schema.go:57） | REPLAY_CAP=3+判定产物 <EV>/<seq>.json 只增（tanyin-replay:36-39,10） | 对等异形（我们限次它去重） | 补「同请求哈希去重」入 replay：同 EV 同 raw_request 哈希重放=复用上次判定产物（省请求），~30 行 | W5（复测岗同批） | 已排 |
| F5 | schema 精确匹配无迁移：库不匹配最新 schema=报错要求重建；派生缓存可重建（store_schema.go:125-133；architecture.md:192） | O7 裁决：SQLite 投影坏了删了重建（RATIFICATIONS） | 同律！ | 相互印证：两家同选「不迁移+可重建」，我们多一层账本真源 | — | 已超（真源+投影两层） |
| F6 | 记录/恢复：-o 存 ProtoJSONL 历史；--resume 只读恢复对话不恢复进程/浏览器/调度（sessions.md:49-78） | 断点续跑=账本恢复协议（verify-chain→state-rebuild→resume-kit，tanyin-runner:56-61,200）——状态不依赖会话记忆 | 我们优（恢复=执法件） | 已超（它恢复靠事件重放，我们状态本就在盘+链验证） | — | 已超 |

### G. 配置运维与产物（4 件）

| # | CH 件（出处） | 我们现状（出处） | 差距 | 超越设计（可施工） | 波次 | 判 |
|---|---|---|---|---|---|---|
| G1 | 配置链：cyber.yaml+多 profile+环境变量优先级链（CLI＞CYBER_*＞配置＞LLM_*）（reference.md:201-234,452-454） | .opencode/opencode.json+TANYIN_HOME/UA 少量 env（USAGE.md:5-24） | 它链长我们短 | 短=优（配置面小=审计面小）；模型多档=W6 llmpool 管理页（A舰 B45） | W6 | 声明取舍（短链）+已排（多档） |
| G2 | 命令族：init/doctor/validate/tools install（各入口同构，audit README:61-72） | tanyin-install/tanyin-selfcheck 六项/tanyin-ledger validate（cli/tanyin-selfcheck:3-8） | 对等已建 | 补 doctor 只读体检口径：selfcheck 加「只读永不建目录/不下下载」声明对齐（audit README:132 同律） | — | 已超（六项+ECDSA） |
| G3 | 配置热重载：节点 reload 下发+profile 重建取消在途执行与待审批（agent.go:135-170） | 模型切换=battle 级 amendment+runner 重启生效（A舰 B11 已排） | 它细（在途取消） | W6 llmpool 管理页规格补「配置变更取消在途执行+待审批」一句律 | W6 | 已排 |
| G4 | 产物形态：报告=OKF index.md+findings.json+coverage.json（audit）；扫描=-j 原生 JSONL+-o 事件流（scan.md:82-95） | FD 报告九段+SARIF+E-index+findings.tsv（README:94-99） | 深度我们超 | 已超；coverage 六数组=SA-3 吸收件在册（source-audit-v1.md:132） | W7+（SA-3） | 已超+已排 |

---

## 二 · 判词汇总

| 判 | 件数 | 代表件 |
|---|---|---|
| 已超 | 28 | F2 哈希链 vs 零防篡改、C18 执法深度（scope 四层+三帽+审批 HMAC）、D1/D2 机械重放验证 vs LLM 自评、E5 一意图一脑结构性消灭压缩、E6 机械评分 vs LLM 自评、F6 账本恢复协议、C14 知识审批链、C12 ECDSA 验签、C17 kb 注入律、A5 最小单元贴产品、B5 引擎调度执法粒度、C21 之外全部「纪律同律+账本化更硬」件 |
| 已排 | 17 | B2/B3 一行安装（W7）、B4 密钥拓扑推到底（W5）、C3 池实链细律（W2）、C6 文件卡（W3）、C8 后台任务（W5）、C13 来源优先级（W5）、C16 judge 接线（W2 G3）、C18 语义判定档（W2）、C19 重复退避（W2）、C29 密钥面卡（W3）、C30 web-intel（W3）、C31 浏览器会话卡（W3）、D3 sniper 情报（W3）、E2 finish 指令（W5）、E3 同轮工具并行（W5）、E7 重试细律（W2）、F4 请求哈希去重（W5）、A3 源码审计（W4+W7）、A6/A7 依赖边界 CI（W2） |
| 声明取舍 | 16 | A1 命令形态、A4 Hub 二分、B1 远程节点（单机律）、C7 shell 解释器、C9 PTY、C10 嵌入 JS、C11 MITM、C21 OTel、C25 节点扩展、C27 WASM 投影、D4 规则流水线范式、E4 Inbox 优先级、F1 会话表形态、G1 短配置链、C31 内 MCP/录屏、C4 父子子代理 |
| 真空白（全部给方案） | 6（+复合判子件 3） | **C16 judge 接线（W2）**、**C18 语义判定档（W2）**、C19 重复拒绝退避（W2）、E3 同轮工具并行（W5）、C29 密钥面检查卡（W3）、**C31 浏览器会话卡（W3）**、A6 依赖边界守卫（W2）、C6 文件读写卡（W3）、G2 doctor 只读声明（小，随 W2 CI 批） |

> 计数说明：§一 逐件表共 67 件（A7+B5+C31+D6+E8+F6+G4）；一件多判（如 C3 已超+已排、C18 已超+真空白）按主判计一次、复合判在判词列注明；主判真空白 6 件（C16/C19/C29/C31/A6/E3）+复合判子件 3 件（C18 语义判定档、E2 finish 指令、F4 请求哈希复用——主判分别为已超/已排/已排）= §三 N 清单 9 项。

---

## 三 · 新增缺口清单（此前任何波次没排、本舰新揪出的件）

> 判据：W1-W8（蓝图:22-29）与 §四b（蓝图:41-63）逐字核对未点名者入本清单。全部给方案与归宿波次，不新开 W9。

| # | 缺口件 | 危害 | 方案（可施工） | 建议波次 |
|---|---|---|---|---|
| N1 | **浏览器会话卡**（SPA 渲染/登录态/JS 交互测试无工具面——C31） | 漏报源：纯 HTTP 卡看不见前端渲染后的攻击面与鉴权流 | playwright headless 卡：导航/点击/填表/截图四令；截图入 E-index；流量经 egress；会话目录持久登录态 | **W3 卡族扩（P0 级——宪法#43 漏报直接相关）** |
| N2 | **同轮工具并行**（E3：单战士回合内 tool 串行） | 测绘类意图吞吐减半以上；多战士后单战士仍是瓶颈 | 协议 JSON 指令块多 tool 并发：线程池+原序追加+截断响应不执行（照抄 loop.go:498 语义）；guard/账本已线程安全 | W5（多战士编队规格扩：单战士并发） |
| N3 | **重复拒绝退避**（C19：被俘战士可无限重试同参数刷门） | 门被磨穿：rate 帽限速不限内容重复 | 卡层记 (卡名,参数哈希) 计数，第 2 次起 250ms×min(n-1,8) 递增+「勿重复」提示回模型；1024 帽 | W2（G3 ask 三态同批，~40 行） |
| N4 | **密钥面检查卡**（C29：只防漏出、不扫存量密钥） | 交付合规缺口：客户环境残留密钥不在发现卷 | keys 正则族（借 proton 规则表思路自建）对 goal 目录/workdir 扫→发现卡+证据；只读卡 | W3（卡族扩，~150 行） |
| N5 | **文件读写卡**（C6：战士文件面无注册无白名单） | 文件访问无门：范围外文件可读写 | 卡面：路径白名单=goal 目录+knowledge 只读挂载；写=临时文件+rename 原子律 | W3（卡族扩） |
| N6 | **依赖边界 CI 守卫**（A6/A7：ledger 模块 import 图无检查） | 架构腐蚀：分层偷偷穿透无人知 | CI 加 import 扫描（白名单分层表：core 不依赖上层——对齐 CH pkg/internal/architecture 测试思路） | W2（CI 三件扩，~80 行） |
| N7 | **两段判定档规格**（C18：ask 只有转人工，无「风险→后果」两段 auto） | 误拦（低风险高价值动作全转人工=自动化率降）与漏放（auto 全信首判）之间缺中间档 | W2 G3 规格扩：ASK 档先判风险再判后果，后果明确无害 auto 放行+审计行；判定服务失败=fail-closed REJECT 钉死 | W2（G3 规格扩，零新波） |
| N8 | finish 指令+六停态对齐（E2） | 战士「主动宣告完成」无协议位，完成=推断 | 协议 JSON 加 finish 指令（同 terminated）；RunReport 停态字典六态命名 | W5（规格补点，~20 行） |
| N9 | 请求哈希复用（F4） | 复测岗重复发同请求=浪费+扰动 | replay 前查同 EV 同 raw_request 哈希的既有判定产物，命中=复用（标注 replay-of） | W5（复测岗同批，~30 行） |

**工程量合计**：N1 ~600-900 行、N2 ~200-300、N3 ~40、N4 ~150、N5 ~200、N6 ~80、N7 规格+N3 同批、N8 ~20、N9 ~30——合计 **~1600-1900 行**，全部并入既有波次（W2 +~120、W3 +~950-1250、W5 +~250-350），不新开波。

---

## 四 · 即刻吸收三件（排序+理由）

1. **N7+N3：两段判定档+重复拒绝退避，并入 W2 G3（ask 三态+judge 接线）规格。** 理由：宪法#43 第一优先=误报率/管控力。CH guardrail 的「风险→后果两段制+判定失败 fail-closed+重复拒绝递增退避」是它安全面最成熟的三件（runtime.go:97-178 实读），恰好补我们 G3 空白的规格细节；吸收后我们的版本多两层它没有的：判定事件入链+范围执法前置。规格件先行（零代码），W2 开工即用。
2. **N1：浏览器会话卡（W3 卡族扩）。** 理由：漏报直接相关。CH 把浏览器当一等扩展（exts/browser+katana headless 深爬）而我们零浏览器面——SPA/登录态是真实漏报源。playwright 截图入 E-index+流量经 egress=我们的版本天然比它多「证据入链+出口执法」两件它没有的管控。
3. **N2：同轮工具并行（W5 编队规格扩）。** 理由：宪法#43 第二优先=自动化程度。CH 同轮 16 并发+原序追加（loop.go:498, defaults.go:15）是成熟语义；我们测绘类意图（nmap/subfinder/dig/httpx 同回合）串行执行是纯浪费。规格照抄三律：信号量上限、批次内无隐式依赖、截断响应不执行工具。

---

## 五 · 总判

**cyber-harness 是五产品里唯一「底盘级」的对手：它不跟我们在判据层竞争，它把装配、循环、观测、协作做成了工业零件（1045 Go 文件、458 测试文件、31 扩展、四入口分工、节点回连成型、AGPL 单仓）。但它的三个结构性空洞正是我们三个结构性山峰：①无授权/范围管控（"Use only on explicitly authorized targets" 一句话 README:32，guardrail 只判风险不判范围——我们八问+scope 四层+三帽）；②无防篡改（SQLite 可改无痕——我们哈希链+第三方可验）；③验证=LLM 语义自评（我们机械重放+考卷判据）。**

**对齐结论：判据脊柱继续保持代差领先；工程工艺（装配有序律/输出契约律/诚实披露律）值得整族吸收；安全面的「两段判定+退避」（W2 规格）与执行面的「浏览器卡」（W3）、「工具并行」（W5）是本舰即刻吸收三件。远程节点形态声明取舍（单机一人红队=产品律），但其「执行单元零密钥」拓扑律吸收进 W5/W7 规格。真空白 6 件主判+3 项复合判子件共 9 项缺口全部给方案入波次，无一悬空。**

---

## 六 · 证据可复核性声明

- CH 每件出处=对手仓实读行号（docs 十四档全文通读；代码十件按节引；git 快照 0d812fe）。
- 我方每件出处=仓内实测（2026-10-19 快照，git main@881ca96）；工具卡 25 张经 card_names() 实跑枚举；知识卡 50 张经目录实测；warrior 循环 2350 行经 wc 实测。
- 本档为唯一写入件；语料与代码零改动；兄弟舰在树未提交件（cli/warrior/context.py、cli/webui/console.py 等 10 件）零触碰。
- 完航验证：`python3 -m unittest tests.test_warrior_loop tests.test_warrior_steer tests.test_timeline_o1_epoch tests.test_timeline_single_source_b10 tests.test_tools_cards_w3 tests.test_guard tests.test_replay_gate` → **Ran 147 tests OK**（本舰零代码，回归面=引用件所在子系统）。

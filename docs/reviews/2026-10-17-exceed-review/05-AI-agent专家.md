# 05 AI-agent 专家 · 智能体能力超越评审(2026-10-17)

> 评审员: AI agent 专家(规划循环/记忆/多智能体编排/模型韧性/上下文管理/知识自进化镜头)。维度: AI agent 能力。
> 比法: ARTEX 常驻 planner+双图记忆+发现纪律 / CSAI RAG 黑板+Jev 审计 / VulnClaw solve+蒸馏闭环 / multica 编队治理 / ZhuLong 调度台——五家同维度最强处当**地板**,不是目标。
> 纪律: 只读语料+代码;本档为唯一写入物;结论带出处;人话;差距照骂。
> 硬约束对齐(父代 2026-10-17): ①**双面一等公民**——企业界面与 CLI 终端都是一等入口,超越清单逐条标注双面交付;②**锚定现状**——先盘家底(13表TSV账本+hash链/ledger+runner+webui 8900/1605测/VulnClaw三轮实机),再算差距。
> 测试基线: 1605 全绿由同舱架构专家 2026-10-17 亲跑(Ran 1605 tests in 428s / OK,01-架构专家.md:7);本报告未重复全量,引用处均带出处。

---

## ① 现状: 智能体层家底(只列实建,带出处)

### 1.1 今天的大脑是谁:一个战士人格 + 一套机械执法,没有独立规划者

- **战士=opencode 进程注入 SKILL.md「总控人格」**: 薄总控五不(不自己写代码/发请求/判重/算哈希/渲染图),一切经账本命令落盘(SKILL.md:3)。三层分工钉死: 「战术归 AI、判据归账本、保活归 Python」(docs/design/architecture-map-v3.md:23)。runner 拉起的就是 `opencode run`(cli/tanyin-runner:101),断了用 RESUME_PREAMBLE 续会话(tanyin-runner:56,:193)。
- **P3 演进循环六步**(今天的"规划"全在这): checkpoint→扫描三查询(unconsumed-facts/pending-intents/matrix-gaps)→**假设风暴五路**(entity/concept/precedent/adjacency/llm,llm 路 quota=5/轮)→并行派发(Top-K)→验收落账(单写者)→链构建→收敛判定(SKILL.md:25;phases/P3.md:5-28)。
- **机械件货真价实**: dedup_key 由 add-intent 算、重复 REJECT;晋升阈值 0.5+0.05*(round-1) 随轮递增(P3.md:14-15);派发优先级=severity_expect×asset_value×exploitability 确定性公式,三因子可审计复算、禁黑箱(P3.md:18-25);收敛=四条件(空格清零/预算未穿/无未消费事实/无阻塞意图),converged 与 budget-exhausted 皆合法终态(P3.md:46-47)。
- **规划者(planner)没有建**: v1.0b「常驻循环(规划者直连 API+多战士)」还在路线图上(docs/design/tanyin-product-v1.md:18;docs/HANDOFF.md:1456),plans/ 目录只有一个无关计划档(实测 ls);推进策略现状=ai-self 默认/gate-loop 实验台(RT-0024 定谳,architecture-map-v3.md:147)。上轮评审已把地基雷全部标好(docs/reviews/2026-10-15-direction-review/01-arch-autonomy.md §F1-F10),至今未排。

### 1.2 监督件(看门狗):单战士保活五家最强档,但只是保姆不是引擎

- 心跳 30s/分级击杀(3min 软+8min 硬)/指数退避/战中指令注入/预算执法(30s 快照+超限收尾令)/LOGONLY-ALIVE/ask:human WAIT 停表/caffeinate+通知,全部实建实战(architecture-map-v3.md:112-124;b24 断网三度点火零账损、b27 82 分钟无人 0.70,map:19)。完成判定只认账本 gate 态,rc=0 不算(map:120)。
- 它不懂战术: 无事件唤醒、无 worker 池、无派单——能唤醒规划者的「事件」在今天不存在。

### 1.3 借脑四件建成即封存(智能体层的「库存零件」)

- **llmpool.py(283 行/50 测)**: 错误分类纯函数(401/402/403/404 硬熔 1 次;408/网络/5xx 软 3 次熔断进 60/300/1800s 阶梯;429 独立 rate 道固定 60s;±20% 抖动;状态原子落盘重启恢复;事件回调)(cli/ledger/llmpool.py:2-24,:38-42)——借 ARTEX llmpool 错误分类表+两处声明改进。
- **judge_client.py(175 行/23 测)**: stdlib 直连 openai 兼容端点,单轮窄调用,输出 token 级严格解析,12 个 reason 码全 fail-closed(cli/ledger/judge_client.py:2-23)。
- **llmpool_wire.py**: 池事件上哈希链(单源写方+源码钉);**trace_search.py**: literal-only 流式扫描+sha256 只读证明(architecture-map-v3.md:163)。
- **全部零生产调用**(本评审 grep 实测 2026-10-17: pick/report/ask 在生产代码无消费方;同判 01-arch-autonomy.md §F4)。模型韧性现状=纸面九成、实际零成——战士跑在 opencode 自己的模型配置上,池子没接进任何活水。

### 1.4 记忆:账本图谱单图两域,半个压缩层,零跨战记忆

- **单图两域**: 资产域(assets/creds)+探索域(goals/intents/facts/findings/E-index)同住 13 表,9 种边方向代码强制(spawns/yields/derived_from/proves/parent/attack/evidences/supersedes/scope-rel,cli/ledger/write_cmds.py:108-118);图查询三命令 graph-neighbors/graph-paths/graph-horizon(cli/ledger/graph_cmds.py:6-8),可达集×矩阵空格 join 直接喂 P3 派发(P3.md:24);意图链=chain 三命令(prereq 虚拟列,architecture-map-v3.md:163)。
- **观察面图谱已成活页**: /graph 十边图+战场画布(拖拽/缩放/小地图/节点卡,cli/webui/static/graph.html 868 行);节点徽章**今天只有 7 类**(目标/意图/资产/凭据/事实/发现/证据,cli/webui/projections.py:77-78)。
- **恢复即记忆**: verify-chain→state-rebuild→resume-kit 白名单注入(禁 13 表全量回灌)(SKILL.md:35-39);受管重启=上下文≥75% 或 10 轮(SKILL.md:42;P3.md:42-44)。
- **没有的**: 提示(hint)节点、压缩(digest)节点、跨战资产图、战士间过程交换(trace_search 建了没接)。

### 1.5 战士插槽:有判词、没动工

- VulnClaw 三轮实机(无 key 诚实降级→glm-4-flash 0 战果→glm-4.7 五发现独立复现 5/5): 终审判词=**插槽位保留**,接缝四件套(账本/闸门/scope/审批)两轮实弹达标,上线前置四条(修绕 P0#2 收尾崩溃/消费 final_answer+verified_claims 而非 findings[]/副作用黑名单进 TaskConstraints/成本核算外挂网关侧)(docs/research/vulnclaw-live-trial.md:427-431)。
- 引擎插槽(工具级)实建: engines/ 四引擎在册(web-blackbox/nuclei/vuln-agent/session-viz,实测 ls),intent 按 MANIFEST 纪律能力路由、超 max_op_level 拒派(P3.md:16)。**战士级插槽(整机 agent)的适配器=0**:engines/ 里没有 vulnclaw 目录。
- 同卡对照实证(插槽制的合法性): 4-flash 30 分钟 0 可验证漏洞 vs 4.7 17 分钟 5 条实证——**发现力=模型档次,且是质变**(live-trial:415-424,:429)。

### 1.6 知识环:结构五家最全,流水停转 18 天(任务书口径 17 天)

- 流水线机制完整: lint→approve→commit→index 重生成,tanyin-knowledge 14 子命令(实测 SUBCOMMANDS;SKILL.md:48 写 13,轻微漂移);P6 沉淀门在九门协议内(脱敏→反向验证→knowledge commit+export,SKILL.md:21)。
- **停转事实(本次实测)**: knowledge/log.md 末笔 2026-09-29T19:04、log/index/overview 三文件 mtime 均停 9 月 29 20:03;账面「正文页 16」vs 实物 39 页(差 23),「K8 retros:1 页」vs 实际 24 个文件,staging/pages 空目录(docs/research/corpus-audit-research.md:149-158+本次 ls)。内容侧复盘页靠另一条路径堆到 10 月 10 日(RT-0024 mtime 01:58),全部无 lint/approve/commit 留痕(corpus-audit-research.md:154-156)。至 10-17: 流水停 18 天、复盘停 7 天。
- 余量: VulnClaw 语料只挖了 10 页,余 39 专题未挖(absorption-2026-10-17.md:24);CVE 快照 18 行样例;K1/K2/K7 全空(corpus-audit-research.md:160)。

### 1.7 发现纪律与度量考卷(智能体层的两块长板)

- 证据即漏洞铁律: 无可复现步骤的观察是 fact 不是 finding(SKILL.md:9);计分四条件=active+端点对得上+证据卡重放验证+信标词在卡,烂账=0 分(architecture-map-v3.md:96);P4 重放门=fresh 子代理+tanyin-replay 三态(SKILL.md:17);E-index 卡 44/已复现 41,P4 重放 30/30 全 VERIFIED(corpus-audit-research.md:126)。
- 度量考卷: 13 战逐战明细+McNemar exact+预登记实验登记处(architecture-map-v3.md:174-181);b11 对照实验(臂A AI 自律 0.66 vs 臂B python 掌节奏 0.41,map:147)、N=5 定谔 p=0.108+Brown-Forsythe 方差齐性(map:154)——**全世界只有我们在给自己的 agent 出考卷**。

---

## ② 五产品地板对照表(AI-agent 维度,最强者=地板)

| 维度 | 地板持有者 | 地板是什么(出处) | 我们现状 | 成数 |
|---|---|---|---|---|
| 常驻规划循环 | ARTEX | 每任务 1 plannerLoop+N worker;worker 写回边沿唤醒+心跳≥600s+防抖+六道门;TodoStore 跨唤醒记串行链;kill_work/steer_work 监督在跑者(docs/research/engine-parts-artex-csai-multica.md:78-83) | 无独立规划者;战士自规划+保姆看门狗轮询 30s;v1.0b 在路线图 | **3 成** |
| 双图记忆+压缩 | ARTEX | 全局资产图+任务探索图+冷节点 digest 折叠+expand 还原+worker 间 trace 交换(engine-parts:96-101) | 单图两域+chain;无 hint/digest 节点、无跨战资产图;trace_search 未接 | **4 成** |
| 发现纪律(retester) | ARTEX | report_finding 须真触发+reporter 绑流量+retester 三态复测+fixed 自动流转(engine-parts:103-108) | 精度门+P4 重放门三态+E-index 机械重放——**此块我们反超**(ARTEX 51 findings 全 pending 0 复测,corpus-audit:37) | **9 成** |
| RAG 黑板+检索注入 | CSAI | 知识库索引/检索链/精排+项目黑板 fact_key 注入(摘要不足必须取正文)+summarization 0.8 触发(engine-parts:134-138) | K1-K8 静态种子+P3 五路 origin;无检索注入、无运行时消费压力 | **3.5 成** |
| AI 审 AI(审计 Agent) | CSAI | HITL 审计 Agent 按内置 Jev 六问(毁坏/不可逆/凭据/配置/payload/政策)预审,reject 阈值 0.55(engine-parts:151) | 机械执法四层(比 prompt 层强);但审批卡无 AI 预审,judge_client 未接 | **6 成** |
| solve+蒸馏闭环 | VulnClaw | run 结束→distill→ExperienceStore pending→人审 approve→experience_context 注入;0.8 近重复合并+置信度半衰(live-trial:181)——**但三轮 lessons=0,从未真转**(live-trial:342,:425,:432) | 流水真转过两圈半后停 18 天;复盘内容绕流水堆积 | **3 成**(两家都烂,唯我们可根治) |
| 子代理委派纪律 | VulnClaw(正反两面) | flash 档 17 次委派空转烧光预算 vs 4.7 档 0 委派全亲自、预算全花刀刃(live-trial:323,:409);CSAI 委派强制交接包(engine-parts:121) | 六要素委派单+submissions 单写者验收+cached 幂等 SKIP(P3.md:16;SKILL.md:6) | **7 成** |
| 模型韧性 | ARTEX | llmpool 多 profile 故障转移链+quota 感知 transport+llmrec 每调用记账(engine-parts:83);CSAI 中间件层 failover/retry/溢出重试(engine-parts:123) | llmpool 建成 50 测**零接线**;judge 单发无重试无切换(§F4) | **4 成** |
| 上下文管理 | CSAI/ARTEX | CSAI summarization 0.8 触发+历史工具结果 60k 清理+超大输出落缓存(engine-parts:138,:150);ARTEX cold-digest(engine-parts:99) | 受管重启 75%/10 轮+resume-kit 白名单——b26 证明比会话重置强,但无摘要压缩,大换血非平滑 | **6 成** |
| 断点续传 | VulnClaw | run/snapshot/target-state 三层+resume_meta 恢复策略,实测 12 测过(live-trial:136-141) | 带账重启+恢复协议+幂等 cached——**比它强**(链上可验) | **9 成** |
| 编队/调度 | multica/ZhuLong | multica squad+daemon lease/reclaim(multica 源码考证);ZhuLong claim 环+心跳+孤儿清扫(usage-guide-zhulong) | 单战士;intents 无属主无租约(§F6),两战士互 REJECT | **2 成** |

---

## ③ 差距(照实骂)

**总判: 智能体层 6.5 成里一半是长板撑的。**发现纪律 9 成、断点续传 9 成、委派纪律 7 成、上下文 6 成;常驻循环 3 成、模型韧性 4 成(实绩 0)、检索记忆 3.5 成、知识环 3 成、编队 2 成。**判据层世界级,大脑还是个「高级实习生」:规矩极好,但没有常驻的指挥官、没有跨战记性、没有会转的知识环。**逐条骂:

**GA-1|「常驻引擎」我们没资格说,而且三周没人排雷。**ARTEX 的 planner 被 worker 写回事件唤醒、防抖、过六道门、重派意图(engine-parts:79)——那是活的循环系统。我们的「循环」=战士自己一轮轮跑 P3,死了被保姆拉起来重跑同一个人。更丢人的是:上轮评审把 v1.0b 的四颗地基雷(写者模型 F1/O(1) 追加 F2/循环故障语义 F4-F5/意图租约 F6)逐颗标好,三周过去 plans/ 里连一份 v1.0b 计划都没有(实测)。**产品定义里「AI 自主打洞是心脏」(tanyin-product-v1.md:5-6),心脏还在路线图上。**

**GA-2|借脑四件建成即封存,给了我们「韧性已解决」的错觉。**llmpool 50 测+judge 23 测+wire+trace_search,全绿,全闲置(grep 实测零生产调用)。judge 拿到 (None, reason) 之后循环该干什么——没有任何代码或设计回答(§F4 原话)。**这比没建更糟:库存零件会锈,测试会骗人。**

**GA-3|知识环停转 18 天没人听见,因为没有任何东西会因此变红。**全系统到处是绊线(命令面 48/KNOWN_COMMANDS/金样钉测),唯独知识环没有 selfcheck(grep 实测 selfcheck.py 无账实对账断言);index 说 16 页实际 39 页,系统照跑。根因三层: ①**没有执法**——retros 直写目录绕过 staging,不触发 lint/审批/index 重生成,而 index 只在 commit 时重生成;②**没有消费者**——P3 的 concept/precedent 路明写「本批可空」(P3.md:11),运行时零检索注入,一个没人读的库停转不发烟火;③**蒸馏口径错位**——VulnClaw 三轮 lessons=0 证明「只从已验证教训蒸馏」蒸不出东西,战争的知识大半在否定结果、final_answer 和过程失误里(live-trial:342,:432)。两家同病给出同一个教训: **知识环不是建了管道就会转的器官,它需要执法+消费+蒸馏口径三件配套,缺一就是静默死亡。**

**GA-4|记忆只有半张地图,用户拍板的词汇我们生不出来。**用户原话认可 11 类节点词汇(起点/目标/意图/事实/漏洞/提示/压缩/派生/意图链/产出/证明),「不断渗透图谱不断演变」(docs/USER-VERBATIM/recovered-2026-10-16-whitebox.md:11,源头是 09-23「AI渗透测试都通过账本图谱进行演进loop…最终图谱演化完成,结束测试」,同档:7)。账本今天只有 7 类徽章(projections.py:77-78): **提示(hint)和压缩(digest)没有对应表/节点,意图链是 prereq 虚拟列不是图上一等节点**。更深一层: 资产域困在单战目录——ARTEX 资产图是全局跨任务真值复用(engine-parts:98),我们换一个战场,上一仗摸清的内网拓扑、组件指纹、凭据习惯全部归零,**每次都失忆从零打**。

**GA-5|多战士的答案在文件里躺了五周。**contracts/01+07 白纸黑字「规划者=唯一写者,战士产 submissions 验收落账」(01-arch-autonomy.md §F1 引契约原文);intents 无属主无租约,战士暴毙意图永久卡 active,收敛判定失真(§F6)。委派单+cached 幂等这些零件都在,就是没人把它们组装成「多战士」。

**GA-6|上下文管理靠「整会话大换血」。**75% 触发受管重启,靠 resume-kit 白名单回灌——b26 已证明会话重置是失分机制(0.41,§F3),受管重启只是止血。CSAI 0.8 触发渐进摘要+工具结果落缓存是平滑的;ARTEX 有 cold-digest。**我们没有「压缩」,只有「失忆后翻笔记本」。**

**GA-7|审批卡没有 AI 预审,方向盘每张卡都要人从零读。**Web 五按钮已落(approval 在),但人的注意力没有杠杆。CSAI 的 Jev 六问审计 Agent 就是干这个的(engine-parts:151);我们 judge_client 建好没接——机械执法不该被替代(那是我们的强项),但「AI 预审+机械执法+人终审」三层才是企业级。

**GA-8|战士插槽有判词没动工。**判词落了三周,engines/ 没多一个 vulnclaw 适配器,四条前置一条没做(实测)。插槽制「模型档次变成可替换参数而非产品命运」的合法性已经用三轮实机证明了(live-trial:429),再不动工就是让证据过期。

---

## ④ 超越清单(P0-P2+工程量)

> 排序原则: 先让心脏跳起来(P0-4 依赖的砖先搬),同时把唯一在「静默死亡」的器官救活。工程量按一人全职估。

### P0(v1.0b 开工门票,合计约 4-5 周)

| # | 事项 | 内容与验收 | 工程量 | 双面交付 |
|---|---|---|---|---|
| P0-1 | **知识环复活根治批** | 三件套: ①执法——knowledge selfcheck 绊线(index↔实物对账,账实差=红,进全量自检;commit 自动重生成 index);②消费——resume-kit 注入知识 top-k(按矩阵空格匹配),P3 concept/precedent 路 quota≥1 不允许空转,未消费页进 converge-check 披露;③蒸馏口径——从账本蒸馏不从散文蒸馏: 以 P4 重放三态+否定结果+retros 五字段(missed/attribution_check/trigger_gap/weak_channel/writeback)为源,judge_client 蒸成候选 lesson→staging 人审(持钥,P5.5 同款)→commit 上链。补账: 23 页未过流水 retros 批量补 lint+approve。验收: 停转天数指标归零、下一战知识消费计数>0 | 7-10 天 | CLI=tanyin-knowledge 子命令扩展;Web=知识页(轮速表: 每战消费页数/概念命中意图数) |
| P0-2 | **借脑接线批** | llmpool 单写者化(规划者进程独占实例)+pick→ask→report 成环+池事件经 llmpool_wire 上链(已建);judge 失败语义=llmpool 冷却梯×watchdog 退避合成一张表。清偿 §F4 | 2-3 天 | CLI 侧机械件,无新 UI |
| P0-3 | **意图属主+租约** | intents detail 虚拟列加 [owner:][lease:]+set-intent-status 执法;租约过期→blocked(lease-expired)可复活;派单键从 LLM title 换机械键(矩阵格/端点签名)(§F6 修正案原样) | 2-3 天 | CLI 先行,Web 派单卡显示属主 |
| P0-4 | **常驻规划者 v1.0b 最小可用** | 依赖 P0-2/3+地基批 O(1) 追加。规划者=直连 API 常驻进程(经 llmpool),唯一总控写者;事件驱动(账本 append 唤醒,先 1s 轮询亦可)+意图供给/预算仲裁/验收三职,**不微管理**(b26 教训: 派发粒度=intent 不碰回合,战士长寿命带账恢复);每循环铸 clock-sync(§F5);计划首页必写「与 b26 判决对账」节(蓝图巡检律)。验收=b11 三项协议+experiments 预登记三件套 | 2-3 周 | CLI=tanyin-planner start/status/stop;Web=方向盘复用 battle/control 五按钮 |
| P0-5 | **VulnClaw 战士插槽落地** | engines/vulnclaw 适配器: --stream NDJSON 消费 final_answer+verified_claims(findings[] 降权为线索队列);副作用黑名单(锁定类)进 TaskConstraints 结构化执法;成本外挂网关侧;绕 P0#2(手动 report)。验收=同卡 4.7 重跑战果≥基线 | 3-5 天 | CLI=headless 退出码契约对接;Web=战士档位下拉(强/弱/外挂) |

### P1(1-2 个月,从「能跑」到「越打越强」)

| # | 事项 | 内容 | 工程量 |
|---|---|---|---|
| P1-1 | **记忆补全批** | hint 提示表+digest 压缩节点(冷 facts LLM 折叠+expand 命令还原+提交期活性复查防覆盖复活)——**11 类词汇全集落账本,徽章 7→11**;跨战资产登记处(全局资产域,新战开局挂载历史资产子图,过授权复判才生效) | 约 2 周 |
| P1-2 | **复测常驻岗(retester)** | P4 一次性重放升级为常驻岗: 发现龄/目标变更触发自动重放三态,fixed 自动 supersede+通知;复用 replay 四门(授权窗/非 GET 拒/次数帽/scope 单源)。ARTEX retester 是会话 agent 自报,我们是机械重放——把 9 成拉成断层领先 | 约 1 周 |
| P1-3 | **多战士编队** | submissions 模型产品化+战士池分档(强模型主战/弱模型扫尾,档位=插槽参数)+**Tier2 hooks 真挂载实验**(v1.0b 押的实验至今未跑,§F7 勘误后补) | 2-3 周(含实验) |
| P1-4 | **审批卡 AI 预审** | judge_client 接审批卡: Jev 式六问预审+置信度,人只终审 AI 不同意的;机械执法面不动。P5.5 人工触点从「每卡必读」变「例外驱动」 | 约 1 周 |
| P1-5 | **上下文平滑压缩** | CSAI 式 0.8 触发渐进摘要+超大工具输出落缓存(evidence 引用+摘要行),digest 节点承接——「翻笔记本」变「记笔记」 | 约 2 周 |

### P2(一个季度,差异化收口)

| # | 事项 | 内容 |
|---|---|---|
| P2-1 | 编排策略切换产品化 | ai-self/planner-driven/gate-loop 三策略一刀切换(RT-0024 已定谳槽位),配 experiments 对照 |
| P2-2 | 客户域记忆 | K7 business/client-map 喂跨战调度: 同客户二次进场开局即带历史资产/凭据习惯/曾经否定结论 |
| P2-3 | 知识环效果度量 | lesson 注入 A/B(McNemar 协议复用)——「越打越强有数学证明」(USER-CHARTER.md:9)落到知识环本体 |

---

## ⑤ 独有优势放大法(别人抄不走的,把它放大到脸上)

**5.1|账本即上下文——全世界只有我们敢把 agent 随时杀了重来。**恢复协议+resume-kit 白名单(SKILL.md:35-39)=规划者上下文可确定性重建,链断即停、修好续跑。ARTEX planner 崩了靠 norma SDK 内部状态(上游闭源快象,engine-parts:169);VulnClaw 靠 resume_meta(无链可验)。**放大法**: v1.0b 规划者把每轮决策落 intents+provenance,P0-4 落地后「常驻」才敢真常驻——这是 P0-4 的合法性来源,不是新增风险。

**5.2|精度门+机械重放=发现纪律的断层领先。**ARTEX 51 findings 全 pending、活跃复测 0(corpus-audit:37);VulnClaw findings[] 是模板碎片噪声、真战果在 final_answer(live-trial:411);我们 44 卡复现 41、P4 重放 30/30(corpus-audit:126)。**放大法**: P1-2 复测常驻岗把它从「战后一道门」升级为「产品承诺——每条发现周期性自动复验」,五家没有一家敢写进 SLA。

**5.3|度量考卷=agent 进化的数学证明。**b11/b27/b28/N=5/Brown-Forsythe+预登记纪真律(architecture-map-v3.md:147-154,:179-181),全世界只有我们给自己的 agent 出考卷。4-flash 与 4.7 的质变差(live-trial:429)如果没有同卡对照协议就只是轶闻。**放大法**: 每个 agent 层改动(规划者/记忆/战士档位/lesson 注入)都过考卷再上岗——把「换模型会更好吗」从信仰变成 p 值。

**5.4|单图两域=零额外状态的活图谱(用户锚点)。**图=账本投影,不存在第二份真相要同步(ARTEX 双图要靠 exploration_anchors 桥,ZhuLong 知识图谱是静态规则库,corpus-audit:70)。用户已拍板: 11 类节点词汇(起点/目标/意图/事实/漏洞/提示/压缩/派生/意图链/产出/证明)保持,「不断渗透图谱不断演变」=**图谱是活运行面不是静态视图**(USER-VERBATIM/recovered-2026-10-16-whitebox.md:11;源头 09-23 原话同档:7)。**放大法**: ①词汇冻结进 contracts 版本化(P1-1 把徽章 7→11 补齐);②图上派单——graph-horizon 已经喂 P3 优先级(P3.md:24),升级为两面统一作战面: Web 画布节点卡加「从此处派单」按钮、CLI graph 三命令与 /api/graph.json 同一投影契约(01-架构专家.md P1-6 同向);③收敛判定四条件(P3.md:46-47)让「图谱演化完成=测试结束」成为机械判据——用户 09-23 的原话在我们这已经是可计算语义,五家没有。

**5.5|插槽制=模型命运参数化。**同一引擎同剧本,4-flash 零战果、4.7 专业级报告(live-trial:415-424)——插槽制把「模型档次」变成可替换参数而非产品命运(absorption-2026-10-17.md:46)。**放大法**: 战士分档混编(强模型主战+弱模型扫尾)+VulnClaw 插槽+自研战士同池竞争预算,「哪家不行换哪家」;账本宪法保证换冲程不换真值。

**5.6|人审门+哈希链的知识环。**VulnClaw 有人审门无链(live-trial:181);我们 approve 持钥签名+EV 链复核钩子已在(v0.9.6 S5,architecture-map-v3.md:198)。**放大法**: P0-1 复活后每页知识自带「谁批的/何时/源证据链」——企业采购问「你们的经验库可信吗」,我们有机检答案,别人有目录。

---

## 总判一句话

智能体层的处境和整个系统同构: **判据层(精度门/重放/度量考卷)已经是五家最强,大脑层(常驻规划者/记忆/知识环/多战士)还在路线图上。**P0 五件事做完(约一个月),我们就是「唯一敢让 AI 自主打、打得真、记得住、越打越强有数学证明」的系统——这四句每句都有出处,每句都是五家凑不齐的。知识环停转 18 天的根治不是修管道,是给它装执法、装消费者、改蒸馏口径——没人读的器官死了不会喊疼;我们的系统哲学本来就是「不信任何自报」,把这条哲学用到知识自己身上,飞轮才不会再停。

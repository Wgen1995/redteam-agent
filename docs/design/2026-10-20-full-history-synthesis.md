# 全史综合梳理(GraphLed 仓全文件全内容)· 2026-10-20

> 任务令: 把历史的所有文件所有内容相关的所有事情梳理全,综合整体分析深入了解清楚——最终产品形态与建设路线的母输入,零猜测,全部以库内文件为准。
> 方法: 按令序全读①-⑨九组输入(宪章/总裁决/对照账/盘点审计/竞品档五份+deep-dive五路/HANDOFF全1579行/施工总计划+落舱记/评审档四份/~/.tanyin/battles概览+蒸馏产物/复盘卡RT-0001..0024/本会话全部2026-10-20设计档13份);每结论带文件:行;写前实盘核验三件接线实况(corps未接loop/kb_inject已接context/哨兵TSV在册)。
> 读档总数: 42份(含目录级概览3处);本档=唯一写入件。

---

# ① 资产全账(我们有什么——引擎件逐件+证据出处)

> 底册: docs/research/2026-10-20-assets-inventory-audit.md(逐件file:line)+docs/design/2026-10-20-capability-comparison-ledger.md(27件四档判定)+docs/design/2026-10-20-build-master-plan.md落舱记R1-R55(10-20当日新建件)。总盘子: tests/ 共304个测试文件(实测ls),盘上用例2880(盘点审计:4);全套件基线1661绿(HANDOFF:1554)+后续各舰新增。

## A. 执行底座(老底子,2880测在护)
| 引擎件 | 实况 | 证据 |
|---|---|---|
| 军团战士运行时 | 15模块2852行: 租约(claim/holds/claimable)+心跳(beat/check_stall/StallDetected)+断点续跑(接管自己活租约)+停滞重生(run_with_respawn新脑至耗尽)+同轮工具并行(MAX_PARALLEL_TOOLS=16) | cli/warrior/ 逐件(assets-audit:15-19);版本w5-warrior-1(cli/warrior/__init__.py:14);战士面171+10=181测(assets-audit:21) |
| 账本 | 13表(goals/scope/intents/facts/findings/assets/edges/approvals/E-index/matrix/timeline/budget/creds)+10种边型方向执法+sha256哈希链(verify_chain双检)+单写者(goal_lock内追加,O(1)尾读+fsync+epoch递增,撕裂fail-closed) | cli/ledger/schemas.json/schemas.py:4-6;write_cmds.py:107-120;core.py:46-48,126-137;timeline.py:154-176(assets-audit:26-29) |
| 工具执行器 | 55条目tools.lock验签全过;F22韧性三件(异步execution_id不占轮次/断路器15-60min/spill 1MB防长任务丢结果)+30工具卡(容器4/横移11/Web5/侦察8/漏扫2) | R31落舱(build-master-plan:47);tools.lock 55条目(实测grep F22验签) |
| LLM池 | 分类-熔断-冷却-切道全链(400不转移/401-404硬熔1次/408-5xx软3次/429固定60s;阶梯60/300/1800s±20%抖动)+故障转移事件入哈希链+录制落盘 | cli/ledger/llmpool.py+llmpool_wire.py(HANDOFF:1393,1406);58测(assets-audit:134) |
| 范围锁+看门狗 | scope三层同源执法+guard八问必填fail-closed;看门狗纯函数核(soft 3m/hard 8m分级击杀/指数退避/战中指令注入/自适应监听) | 80测(assets-audit:136);watchdog.py(HANDOFF:1184);OP1执法面(HANDOFF:1426) |
| 出口执法 | egress代理+ACL+canary探针零容忍+DENYLIST v2十三形态+UA单源自名+request-ticket脱敏 | egress_proxy/egress_mount「代理绝不写13表」(assets-audit:29);HANDOFF:1426-1427 |

## B. 挖掘引擎(找漏洞主力九件)
| 引擎件 | 实况 | 证据 |
|---|---|---|
| F1枚举流水 | add-asset登记+submatrix铸造门+matrix-init分母(空必须消灭)+五态热图+graph-horizon可达空格先行+recon组卡;P1门禁机械验收 | comparison-ledger:23;api_v2_coverage.py:8-16 |
| F2探索图 | 十边图SVG两两互异着色钉死+latest-wins去重+节点富卡(battle-42 173节点标题100%) | 已优8件之一(comparison-ledger:268);HANDOFF:1407,1489 |
| F3打法矩阵 | 50→91张技法卡(CP-0001..0091: 技法域42+VulnClaw蒸馏8+蒸馏入册41)+cp-index.tsv冻结 | knowledge/cp-index.tsv(实测);R34蒸馏入册(build-master-plan:48) |
| F5优先级引擎 | 五因子加权(0.40可达+0.20凭据+0.15线索+0.15饥渴+0.10收益)纯机械禁LLM,落intents.priority零schema改 | planner_score.py:37-49,220-248(R21落舱build-master-plan:40);修复舰六件全修(R53/6ef6427) |
| F6业务逻辑层 | 差分探测器+身份矩阵+作弊假设卡+bizflow考卷种子(越权/流程作弊=工具扫不出的大类,竞品全空白) | R23落舱bcc20a6(build-master-plan:42);设计bizlogic-layer-design:8-13 |
| F7白盒联动 | 车道A解析器v0 464行三工件确定性+GenSift 59件509条ERE全译0跳+双闸防假阳+111夹具CI对账 | R30b落舱22d5019(build-master-plan:46);whitebox-final-ratified:28-34 |
| F8节点调度 | 常驻规划者(防抖+态势研判轮)+重派四分类器(纯故障重派/接续收口/边界固化/完成) | R21+R53(build-master-plan:40,56);planner_loop.py+replacer.py |
| F11误报哨兵 | 14类误报规则版本化TSV+add-finding前置门四态(reject/downgrade/suspicious/clear)+K6回流蒸馏草稿 | knowledge/engineering/sentinels-v1.tsv(实测20行=头+14规则);write_cmds.py:781-810;R20落舱5e9c318 |
| F13复验 | 过期清单+复验意图卡生成器+三态回写(仍真/已修复/环境变更)+S4四门非LLM盲重放 | R40落舱972ece8(build-master-plan:49);check_cmds/enforce |

## C. 质量门与飞轮
| 引擎件 | 实况 | 证据 |
|---|---|---|
| F10验证官 | 非LLM盲重放(S4四门+REPLAY_CAP=3+三态),发现必复验=误报率执行件 | 裁决书:14(重放简化保留);assets-audit:135 |
| F12考卷 | 7 GT战场+链式2条注册表+双基线TSV+三战召回0.62/0.62/0.70,FP=31/3/1 | comparison-ledger:14;evals/gt |
| F16棘轮 | capability_gate棘轮门(分数只升不降)——六家都没有(裁决书:11) | comparison-ledger:268已优件 |
| F14蒸馏 | 42仗→283草案→41入册(技法21+避坑20)+233去重+9废单,知识库50→91张;kb_inject检索注入简报尾(≤5卡帽,开关默认开) | ~/.tanyin/distill-intake-2026-10-20/REGISTRATION-REPORT.md(三数表);R34+R52(build-master-plan:48,55);cli/warrior/context.py:22,56(实测已接线) |
| 复盘纪律 | RT-0001..0024 24张复盘卡在册(每仗归因核验) | knowledge/retros/(实测24文件) |

## D. 指挥面与交付
| 引擎件 | 实况 | 证据 |
|---|---|---|
| F17对话指挥+@引用 | 对话建任务只产卡(范围必须人确认)+@引用账本四表+回复四分类(批准/拒绝/改方向/给情报) | R46落舱70fe934+e177694(build-master-plan:52);command-approval-design:5-11 |
| F19审批 | 预授权白名单零打扰+超时保守+HMAC持钥签名门+审批中心页 | R46;test_p0_approval_hmac(HANDOFF:1212) |
| F22/F24外部后端 | Backend抽象(base/dsh/claude/local四adapter)+任务包最小披露+归一入账(哨兵零豁免实测降级)+usage入budget | R44落舱1008e29(build-master-plan:51);external-backend-design:9-26 |
| F25多任务治理 | 全局并发帽+仗注册表五态+仗间五因子+全停阀幂等+断电恢复不双开+fleet.json四问端点 | R49落舱4587753(build-master-plan:54) |
| F4/F9军团兵种 | 五兵种卡四权分立写面两两不相交+corps.py运行时(load/resolve/authorize/配置只收不放) | R47落舱297e2b0+R54落舱0a96f5a(build-master-plan:53,58);**装配一行待修复舰后接loop(R54明记)** |
| F26报告 | 证据角色版本+过期拒写门+报告员兵种卡+manifest过期检测+两轮修复帽;FD九段+SARIF+签发凭证 | R25落舱168fc00(build-master-plan:44);report-upgrade-design:5-16 |
| F27驾驶舱 | 六面真数据(四问首页/任务/漏洞/知识库/收件箱/设置)+词表机检+五秒三问;视觉打磨对照ARTEX差距清单在册 | cockpit-ui-blueprint:16-29+施工Ruling#1-8;cockpit-artex-gap-list:33-35 |
| webui老底子 | 22页+20个v2 API真数据投影+读面登录门+授权八问真化+launch点火+battle auto一键链 | assets-audit:137(638测);HANDOFF:1533,1536 |
| 韧性采纳 | dsh P0×3: repair崩溃尾修复/compaction检查点压缩/resume_driver续跑驱动(1174行45测,纯函数接线位留注) | R53落舱(build-master-plan:57) |

---

# ② 产品参照综合(四竞品+三参考产品形态并排)

> 底册: docs/research/ 五份全量清点+engine-parts对照+artex-deep-dive五路索引;覆盖等级全标(61律)。四竞品=ARTEX/CSAI/Multica/VulnClaw(全量源码级);三参考=cyber-harness(全量源码级)/DSH(安装包编译产物级)/ZhuLong(用户自有仓,引擎闸已合)。

| 维度 | ARTEX(全量源码) | CSAI(全量源码) | Multica(全量源码) | VulnClaw(全量源码) | cyber-harness(全量源码) | DSH(产物级) | ZhuLong |
|---|---|---|---|---|---|---|---|
| 产品形态 | Go单二进制(go:embed Next.js)+PG,:8787 | Go单体289路由+RBAC+内置C2/WebShell | 云协作平台464路由148表+daemon+Stripe计费 | 单进程异步Python CLI/TUI/Web四外壳 | Go军用底盘四入口+节点回连+31扩展 | harness运行时(一切皆插件)+Web GUI | 意图编排靶场(用户仓) |
| 交互范式 | 24页全程可操作(新建→启动→指挥→暂停→审批→下载)+主Agent对话+@引用+动态图+播报板 | 289路由/会话任务批量/14角色YAML/8平台IM回调 | issues/autopilots/squads/agents/skills/dashboards全CRUD+五IM集成+webhook | 19 CLI命令+REPL+Rust TUI+FastAPI SSE | 四入口(aiscan/audit/web/agent)+QuickConnect节点回连 | 对话第一公民+run_code程序执行+技能目录 | 意图链派单 |
| Agent架构 | planner唯一意图源+worker×N+mainagent人在环+retester;意图单源防自增殖 | 三模式(deep/supervisor/plan_execute)+multi-agent 106文件+markdown子代理CRUD | daemon claim WS-first+15能力协商+6态机+26宿主Backend抽象(dsh一等后端) | 三引擎(rounds/solve/team五角色)+子代理fail-closed禁危险工具 | agent loop+guardrail两段判决+verify独立pass | agent-loop+表面折叠+subagent+goal续跑 | — |
| 工具面 | norma SDK+图工具~30+traffic三件套+MCP/skills(3) | 内置51+外部90 YAML配方+Burp/浏览器插件 | 后端自治(dsh profile+JSONL stdio)+skill-bundles | 内置五组schema+MCP生命周期管理 | 31扩展七族+扫描器流水线 | bash/read/write等SDK+MCP+技能 | — |
| 知识/记忆 | 双图+冷节点digest+过程级trace交换+blackboard继承 | RAG知识库+summarization | 迁移148表+issue黑板 | BM25/ChromaDB双后端+47专题skill+experience经验库(人审门) | 会话/事件/工件三库SQLite | 会话事件日志+compaction摘要 | — |
| 验证 | report_finding双ID→reporter绑流量→retester复测(fixed自动流转) | record_vulnerability状态机+retest+审计Agent | 无质量门(全线bypassPermissions) | verify(PoC验证器)+SARIF | LLM语义判定verify(独立pass) | — | — |
| 许可 | AGPL-3.0+禁实测附加令 | (二开判决:整仓❌但零框架Apache2页库✅) | 开源(github.com/multica-ai) | MIT | AGPL-3.0 | 专有(官方npm) | 用户自有 |
| 一句话判词 | 产品成熟度标杆(裁决书:17) | 攻击树+多角色+RAG+接面广度 | harness即后端形态的活体样本 | 知识RAG+多外壳 | harness工程工艺最高(67件对齐:工程完成度五产品最高) | 活体参考:一切皆插件运行时(裁决书:20) | 意图编排参照 |

**五路深读交叉验证(ARTEX)**: 零防篡改(双源实锤)/fail-open家族(所有子系统一致「宁可退化不可停摆」)/内存态脆弱(todolist纯内存/llmpool PG抖动退化)/字符串匹配当安全判据/边方向无强制——**ARTEX=availability-first,我们=integrity-first**(artex-deep-dive/0-index.md:16-24)。

**我们已有而竞品没有(六家对照后确认)**: 哈希链防篡改/ECDSA供应链/边方向执法/审批-执行配对完整性(0-index:33);能力可度量考卷+只进不退棘轮(六家都没有,裁决书:10-11);哨兵前置降级+复验统一活池(哨兵复验设计:11,19);外部产出过质量门+权限分级(external-backend-design:23)。

---

# ③ 战斗史教训 Top20(42仗+评审教训,各带出处)

> 底册: HANDOFF战斗记录(battle-1..42+op-1)+~/.tanyin/battles(21目录:battle-23..42+op-1)+b40尸检+九维/六专家/超越/哨兵规划者评审。42仗=老TanYin五宿主实跑,磨的是账本schema/考卷/字典/复盘纪律(裁决书R26勘误:114);新warrior运行时181测绿但零实战,首仗即首战。

| # | 教训 | 出处 |
|---|---|---|
| 1 | **尺子先于战士**: b40的31个FP里30个是评分器把已合并僵尸行重数,活集真precision=0.972——误报率第一刀先开尺子 | b40-fp-autopsy:9-11,29-40 |
| 2 | **通道面≠靶面**: 战士拿靶场故意弱的登录token当漏洞单报C1——拿通道对了,报它=FP(类B唯一真FP) | b40-fp-autopsy:103-117 |
| 3 | **n=1会撒谎**: b27 0.70 vs b28 0.46 p=0.001→3v3 p=1.000→N=5定谳「指令策略彻底无效果」——单对显著≠臂效应 | HANDOFF:1299-1301,1335-1340,1356-1361 |
| 4 | **方差压缩器幻觉**: 3v3处置臂带宽0.05看似压缩,系b36单点撑——Brown-Forsythe F=0.052死刑 | HANDOFF:1339,1359 |
| 5 | **深挖/广度不同轴**: G-r4 0.56(广撒)→G-r5 0.24(深挖)——同面三代对照,纪律与广度非同轴(op-1四格:裸0.70/战书30面0.66稳定最优) | HANDOFF:973,1158,1166 |
| 6 | **auth_context挂链血律**: 挂链=越权证明链,断链=白打(RT-0016;b18记账形两连失代auth链断七枚) | bizlogic-layer-design:9;HANDOFF:1102 |
| 7 | **零信息差不猜**: 有差分=候选入账,无差分=诚实记「无信号」不脑补(RT-0006) | bizlogic-layer-design:10 |
| 8 | **同面多洞分洞分finding**: v4单计律首案例weakpass吃掉ratelimit词证 | HANDOFF:986 |
| 9 | **键名族×编码族必须全叉乘**: G-r7凭据0=键名用username/password形634次恒403误判 | HANDOFF:1005 |
| 10 | **观测写放大**: b26 gate-fail终局42%噪声——轮询副作用+E9a去重双根治 | HANDOFF:1200,1217,1233 |
| 11 | **执法靠自觉必落空**: b27预算零铸→执法快照读空——H1红线「空账过门=gate-fail」机械根治 | HANDOFF:1270,1285 |
| 12 | **防御式挂载=假完成**: dsh-plugin v0.2 execute调不存在的run()——从未端到端真跑的工具面是死码 | HANDOFF:1173 |
| 13 | **度量纪真三要素**: 子集清单+per-GT快照+结算口径版本缺一=判决不可复现(directive-n5回填穷举定谳) | HANDOFF:1414-1421 |
| 14 | **指令是双刃剑**: b28 auth聚焦慢速换来深度+1赔掉广度14 | HANDOFF:1304-1305 |
| 15 | **确定性重建胜过手工修复**: b21 docker cp嵌套事故→31律+字典v3.11双兑现 | HANDOFF:1115 |
| 16 | **形变族破壁靠字典迭代**: b22 cmdi形变族0.5893平纪录——16代字典血统(头名/方法/参数三族) | HANDOFF:1122;bizlogic:12 |
| 17 | **舰的自述不是证据**: Multica舰报「已提交」实际未落——68律三验(盘上/在main/抽查) | USER-CHARTER:166 |
| 18 | **落笔验仓**: 舰误落烛龙仓——69律git断言show-toplevel | USER-CHARTER:167 |
| 19 | **哨兵换行绕过**: 字段内嵌裸\n可结构性绕过全部14规则(实测rc=0落verified)——归一化修复+「同义改写=关键词正则固有极限」记账 | review-sentinel-planner:29 |
| 20 | **评审打回制生效**: 规划者四Important(死代码兜底/stderr崩循环/伪造reason/O(I×N)扫面)打回重修后才准收舱——落舱=评审过关(R23新纪律) | review-sentinel-planner:76-89;build-master-plan:42 |

---

# ④ 决策史(69律+全部Ruling里仍然活着的约束)

> 底册: docs/USER-CHARTER.md(167行全读)+裁决书宪法增补+落舱记Ruling。分组列仍活约束(未被后续律取代者)。

## 方向类(活)
- **#43北极星+第一性排序修正**: ①找漏洞能力(召回/误报/漏报)②AI自动化③验证/账本(放大器)④界面/治理(外围)——前面是1后面是0(USER-CHARTER:80-83,110-113)。
- **#55重心律**: 信任机器=工程质量非卖点,若只有它不做也罢;核心竞争力=挖掘+军团+飞轮(裁决书:33)。
- **#38超越律**: 默认方案永远是超越版,禁止呈递降级选项;降级只能用户主动提出(USER-CHARTER:62)。
- **产品定义(用户终裁)**: 很好的渗透测试agent——AI自动化挖漏洞,误报率漏报率都很好,可控,且控制不影响误报漏报(USER-CHARTER:133)。
- **形态**: 渗透界harness(同opencode,领域=渗透),平台自立+三标准兼容(agentskills.io/MCP/通道格式),军团编制六维配置含harness可选执行后端(USER-CHARTER:136;裁决书:20)。

## 纪律类(活)
- **#53综合分析律**(不头疼医头)、**#56驾驶座判定律**(超越只能从逐屏实走裁决,此前只说差距清单)、**#61竞品覆盖分级律**(未达全量源码不得说超越)、**#67对比最优律**(每个决策对照全量清点说明为何最优)(USER-CHARTER:164;裁决书:31-33,42)。
- **#68舰队交付验证律**(三验:盘上/在main/抽查)、**#69落笔验仓律**(git断言仓根)、**pathspec铁律**(R30b母舰事故后「今后提交必须git commit -- <pathspec>不得例外」;R46 Ruling#4共享文件须git apply --cached)(USER-CHARTER:166-167;build-master-plan:46,52)。
- **#42量纲律**(禁时间预算,只报行数+测试数+通过率)、**#47零沉没成本律**、**#50设计资产保全律**(旧件原样留存,新件注明演进自X)、**#51账先用律**(55条法不如1条被用)(USER-CHARTER:76-78,97-99,115-124)。
- **#58采样标注律**(凡陈述覆盖面必报数)、**#59深度先问律**、**#60预期复诵律**、**#57问答落账律**、**#66答所问律**(USER-CHARTER:146-162)。
- **#36实时落帐+#46交流落帐**: 每批次/战果/有效结论当场写档,禁事后补(USER-CHARTER:60,93-95)。
- **全权委托令(2026-10-20)**: 「先全部按你的推荐来」「直到系统建设完成否则不要停」——待裁点按AI推荐自裁入册;**R24用户直接下令可修订既定建序**(「先把所有界面功能做出来…先做前端,不是只做UI」压过F24)(USER-CHARTER:165;build-master-plan:43)。

## 界面类(活)
- **#62界面说人话律**(上屏词过「渗透测试员第一眼懂吗」测验;finding→漏洞/intent→任务/warrior→士兵/EV卡→证据)+**#63五秒三问律**+首页=四问直答(打出什么漏洞/正在打什么/什么在等我/花多少钱)(USER-CHARTER:157-159;cockpit-ui-blueprint:6-10)。
- **#64功能过堂律**: 六段式过堂(干什么/里面怎么转/你看到什么/怎么控制/失败怎么办/开放问题)逐件批准才可建设与上屏——界面是最后一件(被R24修订为「先做前端真功能」但过堂制不变)(USER-CHARTER:160;build-master-plan:43)。
- **#41+#31语体**: 专业普通话,禁黑话禁儿语;**#33参照即基线律**(五家同类页=验收线)(USER-CHARTER:53,71-74)。
- **#45分域门律**(门按域分不整体停)、**#28用户提交物优先律**(输入非模板,学道理不描字)、**#29视觉伴侣律**(8900活体=唯一视觉验收面)(USER-CHARTER:45-48,89-91)。

## 架构裁决(活)
- **重写裁决**: 引擎核心保留(战士循环/调度/工具协议/llmpool同级,重写零收益);harness缺口新建;界面推倒(驾驶舱方案);账本降级简化(朴素追加,去哈希链帧号重件;范围锁=防手滑;重放简化为「发现必复验」)(裁决书:21,14)。
- **军团编制定稿**: 子代理=同一战士运行时+五维配置(指引/LLM道/技能卡集/工具/权限预算);兵种=总控/Web渗透/白盒/API(未来)/验证官(非LLM);加兵种=加模板+卡零运行时代码(裁决书:28)——R47/R54已按此落地。
- **对话=操作台非问答框**(裁决书:35-36)+@对象引用=行号+指纹实锚防幻觉(裁决书:37-38)——R46落码。
- **F24 harness即后端**: 外部AI后端当编外士兵肌肉,成果一律回账本过质量门零豁免;权限分级=差异化卖点(external-backend-design:11-13)。
- **#39栈律**: webui投影面Vite+Vue3,核心账本/CLI保持stdlib零依赖;C2/WebShell用户批做(法律件已拍);工期AI周计(USER-CHARTER:63)。
- **首仗纪律**: 首考=立基线不比旧;全链证据可复算;禁无证据调分;僵尸口径标注(first-battle-checklist:21-22)。

---

# ⑤ 缺口真相(对照「AI自动化渗透测试」完整能力——诚实,分已建待接线/真缺)

> 底册: comparison-ledger判定(已优8/对等10/落后6/缺失3)+落舱记R43建设态+R24排序令后实况+first-battle-checklist硬前置+本舰写前实盘核验。

## A. 已建待接线(码在,链路最后一环未闭合)
| 件 | 现状 | 缺的一环 | 证据 |
|---|---|---|---|
| F4军团运行时 | corps.py 41测绿,五兵种可指派 | **装配一行未接loop**(实测grep loop.py无corps;R54明记等修复舰后接) | build-master-plan:58;实测 |
| 韧性采纳三件 | repair/compaction/resume_driver 45测 | 纯函数接线位留注,等修复舰后接loop | build-master-plan:57 |
| 哨兵 | 14规则+前置门+K6回流,修复舰已修I-1 | 待复审过才正式收舱(评审制:落舱=评审过关) | build-master-plan:42,49,56;6ef6427 |
| 规划者 | 核心+两CLI入口接线(修复舰补齐) | R21「建成」修正为「核心建成接线补齐」——首仗验证 | build-master-plan:56 |
| 白盒锚边 | EDGE_KINDS执法面留SA-2接舰 | 第11边锚勘误已做,SA-2双向派生未接 | build-master-plan:46 |
| 模型钥匙 | 全链就绪 | **/tmp/channels.json被重启清空,全盘无钥——点火前用户一次性粘贴** | first-battle-checklist:30-31 |
| 驾驶舱新功能脸 | 六面真数据在 | 证据袋/复验队列/差分结果/白盒雷单「随对应舰落舱接线」 | build-master-plan:43 |

## B. 真缺(码不在,设计或有或无)
| 件 | 缺到什么程度 | 依据 |
|---|---|---|
| **首仗实战数据** | 新warrior运行时(租约/断点/重生)181测绿但**零实战**;42仗全是老TanYin五宿主跑的——所有「引擎同级」判断的实战面待首仗立基线 | 裁决书:114(三度勘误);first-battle-checklist:22 |
| 浏览器会话卡 | N1(P0级,SPA渲染/登录态=真实漏报源)——F22的30卡(容器4/横移11/Web5/侦察8/漏扫2)无浏览器卡,实测cards无playwright | E-cyberharness:183;实测 |
| F24b外部后端后半 | profile分发/自愈+MCP client+daemon化(多机)未建 | build-master-plan:51;external-backend-design:26-27 |
| 白盒车道B+SA-1/3/4 | 车道A落码;五步证伪卡流程正文在册未施工;audit-goal命令族/互译表/二进制合规未建 | whitebox-final-ratified:28-33 |
| MCP生态面 | 裁决书§四.1「三标准兼容」是活目标: agentskills.io技能格式兼容未验/MCP server出口未建/MCP client在F24b | 裁决书:20 |
| 通知集成 | ARTEX 26文件(钉钉/飞书/邮件)——我们零通知面(仅macos osascript) | artex-analysis:32;HANDOFF:1237 |
| 多用户/RBAC | multiuser-assetlib-v1设计在册(26KB)未施工;CSAI有完整RBAC 14路由 | docs/design/multiuser-assetlib-v1.md;csai清点:29 |
| C2/WebShell | 用户已批做(法律件拍板),零行码 | USER-CHARTER:63;HANDOFF:1523 |
| 自更新 | ARTEX selfupdate三段式3败回滚——我们零;DHSH式的一切皆插件运行时未起步 | artex-analysis:32;裁决书:20 |
| 移动端/IM | CSAI 8平台IM——我们零(渗透场景优先级低,#43可降级) | csai清点:31 |

**诚实结论**: 27件对照账的「缺失3件(F6/F7/F24)」已全部落码(待评审收口),**结构性缺口已从「缺件」转为「缺接线+缺实战+缺生态外围」**;按#43第一性排序,真缺里直接伤漏报的=浏览器卡+白盒车道B+首仗数据;伤自动化的=F24b+通知;外围=多用户/移动端。

---

# ⑥ 产品形态推导(从①②⑤推导,过程写明)

> 推导链: ②告诉我们市场形态(ARTEX对话+@+动态图=交互标杆/Multica证明harness即后端可行/CSAI证明接面广度/CH证明装配工艺)→①告诉我们已有什么(五层全有件)→⑤告诉我们还缺什么(接线+实战+外围)→④约束怎么摆(62/63律人话+四问+对话操作台+#43第一性)。

## 推导一: 产品骨架=对话第一公民+任务多签+仪表盘,三者不是并列是同心圆
1. **为什么对话第一**: 用户产品预期第4条「界面=操作台非报表: 能开火/能指挥/看得见打洞现场」(USER-CHARTER:137)+裁决书§八「对话=操作台非问答框」(裁决书:35-36)。②佐证: ARTEX主Agent对话+@引用是其24页里粘性最高的交互(活体解剖①,command-approval-design:11)。R46已落码(对话建任务只产卡+@引用四表+回复四分类)。
2. **为什么任务多签(任务卡确认门)**: 范围必须人确认是我们的差异律(「绝不起草稿直接跑」,command-approval-design:8)——ARTEX新建即跑无确认;授权八问已真化(HANDOFF:1533)。多签=授权八问(开仗前)+任务卡确认(对话建任务时)+预授权白名单(战中降噪)(command-approval-design:15-18)——三层签刚好覆盖「开仗/派活/放行」三个控制点,对应#45分域门律(门按域分)。
3. **为什么仪表盘骨架=四问首页**: 62/63律人话+四问=用户的词(漏洞/正在打/等你看/花多少)(USER-CHARTER:159);ARTEX没有四问直答(cockpit-artex-gap-list:22)。六面IA(首页/任务/漏洞/知识库/收件箱/设置)已定稿且真数据落地(cockpit-ui-blueprint:16,22-29)。
4. **同心圆关系**: 对话=输入面(开仗/指挥/@派活)→任务=执行面(活池/租约/规划者)→仪表盘=观察面(四问/证据袋/复验队列)——执行面在①已全有(F5/F8/F25/租约),观察面六面已落,输入面R46已落码待接前端脸。

## 推导二: 我们的引擎件各落哪个面(逐件映射)
| 面 | 引擎件(①的证据) | 落位理由 |
|---|---|---|
| **对话面** | 对话建任务+任务卡(R46)/@引用fuzzy搜四表(R46)/回复四分类路由既有HMAC面(R46)/steer转向+stop(老底子loop.py) | 输入面五件全落码;ARTEX同型+我们多任务卡确认门与四分类(command-approval-design:11) |
| **任务面** | 活池(意图池+租约认领)/F5排序(下一枪打哪排行,五因子各多少一眼懂)/F8规划者(新线索→几十秒变新活)/F25多任务治理(并发帽/fleet四问端点)/F22执行器(55工具卡+断路器) | priority-planner-design:36「下一枪打哪排行页」;任务页六签(概况/地图/活池/漏洞/消费/日志)ARTEX任务内二级导航同型(cockpit-ui-blueprint:17) |
| **漏洞面(独有)** | **证据袋**(EV卡角色/版本+上次验真X天前)/复验队列(F13过期清单+复验卡+三态回写)/哨兵挡板留痕(为什么挡) | ARTEX finding由agent写图无独立重放实证——证据袋+复验队列是ARTEX没有的IA卖点(cockpit-artex-gap-list:23) |
| **知识库面(独有)** | 91张打法卡+哨兵规则14条+蒸馏草稿人审+K6回流 | ARTEX无知识飞轮面(cockpit-artex-gap-list:24);飞轮=核心竞争力第3条(裁决书:12) |
| **收件箱面** | 审批(预授权白名单/同类聚合一票/超时保守)+求助ask.md(Ruling#5同位) | 审批降噪闭环(command-approval-design:15-18);Ruling#6收件箱只读(cockpit-ui-blueprint:28) |
| **设置面** | 预算三元组/范围修订链/外部后端面(每个后端状态/用量/花钱)/兵种编成(corps.yaml) | Ruling#7收编既有真数据页(cockpit-ui-blueprint:29);external-backend-design:17 |
| **底座(不上屏)** | 账本13表/验证官S4/考卷棘轮/llmpool/范围锁/看门狗 | 放大器层——第一性排序第③位(USER-CHARTER:111),降级为朴素追加(裁决书:14) |

## 推导三: 独有件(四问/证据袋/复验队列)插在哪——为什么是独有
1. **四问首页**: 插在「你-系统」边界第一屏。推导: 用户问系统的永远是四件事(打出什么/在打什么/等我什么/花多少)——ARTEX仪表盘是通用仪表盘不是答案页(cockpit-artex-gap-list:22);数据源四件已齐(漏洞榜=投影终态口径Ruling#1/活池=planner产物直投/收件箱=审批+ask/消耗表=budget+usage)。
2. **证据袋**: 插在漏洞面每枚发现下。推导: 「每个漏洞必须实证」是官方答案四件之一(USER-CHARTER:9);R25证据角色版本+过期拒写门已建;复验队列=F13三态回写(仍真/已修复/环境变更)接报告lifecycle——两件合起来=「上次验真X天前」+「待复验」两列,这是六家都没有的信任机器面向用户的唯一出口(把#55降级后的信任机器变成漏洞页的一个字段,不再是卖点而是内衬)。
3. **复验队列**: 插在漏洞面+任务面之间(过期发现→复验卡进统一活池走统一排序)。推导: 哨兵复验设计:19「我们多出: 复验卡进统一活池走统一排序(它独立跑)」——统一活池是已建资产(F5/F8),复验只是新卡型,零新面。
4. **哨兵挡板**: 插在知识库面+漏洞面之间(挡板规则可审+被挡留痕)。K6回流使「误报教训→新挡板」闭环(哨兵复验设计:10)——飞轮的误报半边。

## 推导四: 建设路线(从缺口真相⑤直接导出,顺序服从#43)
1. **先接线后新建**: corps装配一行+韧性三件接loop+哨兵复审收舱+驾驶舱新脸接线(全部是「已建待接线」A桶,零新码或近零)——先把已建资产变成可用系统。
2. **首仗立基线**(硬前置九项first-battle-checklist:5-14,含用户贴钥)——42仗教训③的头两条(尺子先行/n=1会撒谎)要求新运行时尽快拿真分数。
3. **漏报直害两件**: 浏览器卡(N1,P0级)+白盒车道B——#43第一性+67律对照(CH把浏览器当一等扩展,我们零浏览器面)。
4. **自动化两件**: F24b(profile分发/MCP client/daemon化)+通知面——「一键到报告的比例」第二性。
5. **外围按需**: 多用户/移动端/C2(已批)/自更新——合同驱动,不预建。

---

# 衔接位(留给在飞的两艘产品地图舰)

- **前端功能图舰**: 以§⑥推导二/三的七面映射表为功能清单底稿(对话/任务/漏洞/知识库/收件箱/设置+底座不上屏);每面「你看到什么」引各设计档人话节;独有件(四问/证据袋/复验队列/哨兵挡板)标注「ARTEX无」证据引cockpit-artex-gap-list:20-25;页面树以cockpit-ui-blueprint:16-17六面IA+旧22页深页目录(Ruling#8页脚+更多组)为准。
- **后端接口图舰**: 以①资产表为模块清单(底座/挖掘/质量门/飞轮/指挥五层);api_v2 20端点+webui既有面为读面,R46对话建任务/@引用四分类+R49 fleet.json四问端点+launch/battle auto为写面;F24a Backend抽象(base/dsh/claude/local)为外部边界;质量门链(哨兵→验证官→GT棘轮)为每条写路径的必经站(external-backend-design:11「零豁免」律)。

---

# 本档报账(三行摘要×六节+总数+三发现)

**①资产全账**: 五层引擎件逐件在册(底座6件/挖掘9件/质量门飞轮5件/指挥交付10件),全部带file:line;总盘子304测试文件2880用例基线1661绿。
**②产品参照**: 四竞品(全量源码级)+三参考(CH全量/DSH产物级/ZhuLong用户仓)七维并排;ARTEX=availability-first我们=integrity-first是五路深读总洞察。
**③战斗史教训**: Top20覆盖尺子病/通道面/n=1谎言/方差幻觉/挂链血律/换行绕过/评审打回制,每条带HANDOFF行号或评审档行号。
**④决策史**: 69律全数在册,分方向/纪律/界面/架构四组列活约束;全权委托令+R24排序令证明「用户令>既定序」是活规则。
**⑤缺口真相**: 结构性缺口已从缺件转为缺接线(7件A桶)+缺实战(首仗零数据)+缺生态外围(10件B桶);伤漏报的真缺=浏览器卡/白盒B/首仗数据。
**⑥产品形态推导**: 对话(输入)/任务(执行)/仪表盘(观察)同心圆;四问插第一屏、证据袋+复验队列插漏洞面(六家没有的信任出口)、哨兵挡板接飞轮误报半边;路线=先接线→首仗→漏报两件→自动化两件→外围按需。

**梳理文件总数**: 42份正档全读(宪章1/裁决书1/对照账2/竞品研究13含deep-dive6/HANDOFF全1579行/施工计划1/评审4/复盘卡24抽读1/2026-10-20设计档13/清单1)+目录级概览3处(~/.tanyin/battles 21目录/knowledge 21子目录/distill产物)。

**最重要的三个发现**:
1. **「42仗磨的是老TanYin,新运行时零实战」**(裁决书:114三度勘误)——所有「引擎同级」判断都建立在181个单测而非实战上;首仗不是里程碑是校准器,产品形态文档必须把「首仗立基线」写成硬依赖。
2. **结构性缺口已从「缺件」翻转为「缺接线」**(对照账缺失3件全部落码R23/R30b/R44,但corps/韧性三件/哨兵复审/新脸接线全部悬在最后一环)——当前最高杠杆不是新建是闭合,一行装配的价值大于一个新舰。
3. **信任机器的归宿=漏洞页的一个字段**(裁决书#55降级+证据袋/复验队列/上次验真X天前三件R25/R40已建)——把「银行级记录」从卖点降为内衬后,面向用户的信任出口收拢在漏洞面一处,这是产品形态上最反直觉但最自洽的一笔。

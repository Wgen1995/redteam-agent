# 能力对照总账·27件逐件对账（宪法67律执行件）· 2026-10-20

- 任务令: 27件功能逐一对照竞品全量清点,产出最优方案对账。
- 输入(全读): docs/research/2026-10-20-artex-full-capability-inventory.md(下称`ARTEX清点`) + docs/research/2026-10-20-csai-full-capability-inventory.md(下称`CSAI清点`) + docs/design/2026-10-20-graphled-master-verdict.md(下称`裁决书`,§22功能地图27件+自裁记录) + cli/warrior 与 evals/gt 实况抽查。
- 方法: 我方每件给文件:行级出处(本机实读);竞品件只引两份清点档(含其内嵌 app.go 行号);判定四档=已优/对等/落后/缺失;判定基准=第一性(误报/漏报/召回),产品成熟度只作记录不作判据。
- 竞品一句话(裁决书§三): ARTEX=产品成熟度(24页/智能体配置/MCP/动态图); CSAI=攻击树+多角色+RAG+接面广度(289路由/90工具/内置C2/WebShell)。
- 纪律: 只读+只写本文档;pathspec提交;引用必带出处;测试数实测;不碰8900等端口(tanyin-serve 缺省口=8900, cli/tanyin-serve:25——本舰全程未起服务)。

## 〇、实测底数(2026-10-18 本机快照)

- 测试数实测: `python3 -m unittest discover -s tests` → **Ran 2846 tests in 529.207s, failures=12, errors=7, skipped=2**(发现态计数2864)。12失败+2错误全部来自**未入库的在飞TDD红测**(test_webui_task_actions/test_webui_techniques_deeplink/test_console_findings_overview,期待尚未落地的UI件)与**Playwright Live冒烟**(浏览器未装的环境件: graph_canvas/palette/steering_ui等);已入库基线全绿。另有在飞舰于08:50Z把 cli/knowledge/distill.py 存出语法错(行375未闭合字符串)——施工中状态,不计入本账判定。
- 战士面测试实数: test_warrior_* 共 **171测**(guardrail 30/corrections 22/kb_context 20/parallel_tools 18/loop 12/ledger_io 12/protocol 12/context 9/main 8/model_client 8/budget 5/heartbeat 5/steer 5/transcript 5)。
- 语料实数: knowledge/concepts/ **50张**(CP-0001..0050逐一点数);cp-index.tsv 50行冻结;cli/tools/tools.lock **25行**签名锁;knowledge/engineering/sentinels-v1.tsv **14条**规则(SEN-001..014,未入库)。
- 评测实数(evals/gt/README.md:14-18): 三战实测召回 b40=0.62/b41=0.62/b42=0.70(均值0.645);误报 FP=31/3/1(FP口径=活跃发现数−GT命中数)。42仗实跑在册(裁决书§白盒主设计确认)。
- 在飞件(本账判定须知情): 功能5五因子引擎(cli/ledger/planner_score.py,未入库)+功能11哨兵三件(sentinels-v1.tsv+judge_client.py+101行/write_cmds.py+33行+distill.py K6回流施工中)+功能27驾驶舱WIP红测——均为工作树未提交件。

---

# 一、找漏洞主力 9 件

## F1 枚举流水(测绘→登记→覆盖记账→交优先级)

- **我们现状**: 登记面=add-asset 命令(cli/ledger/write_cmds.py:1684)+submatrix 铸造门(write_cmds.py:1135-1136);覆盖记账=matrix-init 铸分母(cli/ledger/matrix_init.py:2-8,`空必须消灭`=终态门禁分母)+五态热图(cli/webui/api_v2_coverage.py:8-16,未测面瞪眼不静默);交优先级=graph-horizon 可达空格先行(cli/ledger/graph_cmds.py:8);工具面=recon 组卡(subfinder/dnsrecon/httpx/whatweb/nmap,cli/tools/cards.py)。P1 门禁机械验收 asset-added→子矩阵行(cli/ledger/phases_engine.py:732-758)。过堂完毕: 默认全扫档(端口全扫+子域字典+技术栈指纹),快扫留手动(裁决书§22过堂记录)。
- **ARTEX**: ScopeSentry 资产同步——域名/子域/IP/端口/端点按项目任务维度(ARTEX清点§三)。
- **CSAI**: 资产11条路由(CSAI清点§1: import/scan-links/bulk/project-binding/batch-delete/merge, app.go:1069-1079)+FOFA/Shodan/ZoomEye/Quake 四资产引擎(§1 fofa:1064/§5 config)+XLSX/CSV 归一去重(§5 README Highlights)。
- **判定: 对等**。账面/覆盖/门禁纪律超两家(覆盖记账=漏报第一道防线,竞品皆无分母执法);窄处在**外部资产源**: CSAI四引擎我们零,批量导入面无。
- **最优方案(补窄)**: ①资产源卡化——fofa/shodan/zoomeye/quake 查询=新工具卡(七纪律字段+限速固化+tools.lock 签名,走既有 gate 门链,零新执行面);②add-asset 补批量导入命令(CSV/TSV 逐行过 add-asset 同校验,归一去重键=资产 value+type);~200行,过棘轮。

## F2 探索图与覆盖

- **我们现状**: 图查询三命令(cli/ledger/graph_cmds.py:1-10: graph-neighbors 邻接展开/graph-paths 可达路径枚举+凭据链 CRED→scope_asset/parent_cred 边/graph-horizon 可达集×矩阵空格 join);节点=九表行 id(graph_cmds.py:36-38);覆盖=matrix 五态格阵(api_v2_coverage.py:11-16);UI=console_graph/graph 页+24测(test_graph_rich)+画布20测(test_graph_canvas)。本质已裁: 资产图+每轮威胁分析之间的记分板,面按入口算(裁决书§22过堂记录)。
- **ARTEX**: Task 绑探索图 ExpID(裁决书§19)+动态图=产品成熟度卖点(裁决书§三/§21⑤链路图)。
- **CSAI**: 攻击链包 internal/attackchain 1466 LOC(Node/Edge/Chain+截断+提升为项目 promote_project,CSAI清点§2)+项目事实图 fact-graph/fact-edges CRUD(app.go:1346-1356)。
- **判定: 已优**。竞品图=展示层(节点边存库供渲染);我们=账本行确定性运算+覆盖矩阵记分板一体(图运算直接喂派发: horizon join),且凭据链边执法(悬空 cred 告警,graph_cmds.py:19-32)。

## F3 打法矩阵(技法卡库)

- **我们现状**: 50张技法卡(knowledge/concepts/CP-0001..0050,frontmatter 六列)+cp-index.tsv 50行冻结(tests/test_w3_cp_ingest.py 钉);检索注入=确定性打分(拉丁token+CJK二元组,title×3/vuln_class×2/source_topic×2/applicability×1,cli/warrior/kb_context.py:106-145),派活时自动挑卡入简报、标注「供参考使用」(kb_context.py:158-159,老TanYin实证终裁=AI是指挥官卡是情报);SKILL 按门路由瘦身(kb_context.py:206-234);卡入库变更过评测棘轮(scripts/capability_gate.py CAPABILITY_SPECS.technique_cards)。
- **ARTEX**: 技能 zip 上传+使用量统计(skill_zip/skill_usage/tool_usage,ARTEX清点§二)+promptcatalog(§四)。
- **CSAI**: 24技能包渐进披露(Eino skill middleware 按需加载)+skills/stats 使用量 CRUD(app.go:1457-1468,CSAI清点§4)。
- **判定: 对等**。语料量同级(50卡 vs 24包+12知识文件);纪律强(棘轮管变更+参考用法裁决);**缺命中计数/使用量回流**(两家皆有,飞轮仪表件)。
- **最优方案(补件)**: cp-index 家族兼容扩列(先例=ng-index 四可选列,scripts/capability_gate.py:68-72)加 hit_count/last_hit_ts 可选列;kb_context.retrieve 命中即记(聚合写面走 staging,变更仍过棘轮)——知识库页「卡带战绩」数据源。

## F4 军团(兵种编制)

- **我们现状**: 战士运行时同源(cli/warrior 15文件: 循环/执行器/守卫/纠正/心跳/账本面);per-warrior 配置=CLI旗标(cli/warrior/__main__.py:35-45: --skill/--channels/--token-cap/--lease-min/--max-parallel-tools)+LLM道文件(channels.example.json);总控通道在(steer.py:14 ACTOR=总控);军团编制六维定稿(裁决书§六: 指引/LLM道/技能卡集/工具/权限预算[+执行后端=§11六维])。**无兵种模板文件/无YAML角色包**。
- **ARTEX**: 智能体配置=产品成熟度三大卖点之一(裁决书§三);planner/mainagent 分离+会话/子代理独立ID工厂(裁决书§19;ARTEX清点§四)。
- **CSAI**: 14角色 YAML(user_prompt 前置+tools 过滤,roles/README)+16 agents md(3主[deep/plan_execute/supervisor]+13子代理含授权状态段)+CRUD(app.go:1431-1435/:1057-1061)+multiagent 106文件28049 LOC(CSAI清点§3/§4/§2)。
- **判定: 落后**。单兵运行时强于两家(租约/断点续跑/停滞重生/守卫纪律),但**编制面零**: 兵种=数据包这件事没有落地,加兵种仍要改启动命令。
- **最优方案**: 兵种=六维 YAML 包(name/指引md路径/LLM道json/技能卡集[concept id 列表→kb 检索域]/工具allowlist[卡名白名单进 gate]/权限预算[token_cap/lease/并发帽]/执行后端[warrior|MCP|harness]);战士启动读包(__main__.py 参数源改为`--corps <yaml>`,CLI 旗标保留=包的逐项覆盖);总控兵种走 steer 通道派单+意图行带兵种位。加兵种=加模板零运行时代码(裁决书§六原律)。~300行+首批5兵种模板(总控/Web渗透/侦察/验证官/报告员)。

## F5 优先级引擎

- **我们现状**: priority 降序认领(cli/warrior/ledger_io.py:66-70: -priority, id 排序);可达空格先行(graph_cmds.py:8 horizon join);**五因子公式在飞**(cli/ledger/planner_score.py:1-27,未入库: score=0.40可达性+0.20凭据就绪+0.15线索新鲜+0.15矩阵饥渴+0.10历史收益,纯机械可解释禁LLM裁量,R-SCO-1..7 裁决;设计=docs/design/2026-10-20-priority-planner-design.md)。
- **ARTEX**: planner LLM 排序(promptcatalog 可编辑提示词,ARTEX清点§二/§四)——无机械公式。
- **CSAI**: 批量队列 FIFO+并发帽,无显式优先级引擎(CSAI清点§6任务状态机)。
- **判定: 对等(在建)**。三家都无显式引擎成品;我们公式件已写待入库,落地即超(可解释+可复算+账本可查因子)。
- **最优方案**: planner_score.py 入库+K1通道回填 intents.priority(认领面 ledger_io.py:66-70 已消费,零改动)+金样钉死(同输入同序);验收=GT 召回不回退(棘轮)。

## F6 业务逻辑层(越权/流程作弊/差分)

- **我们现状**: 设计定稿未实现(docs/design/2026-10-20-bizlogic-layer-design.md)。家底: authz-diff 意图 kind 在(contracts/01 六kind之一,设计档:3);GT 已有 idor 链(range-chain-v1 两链,gt-index.tsv:12);复盘三族教训在册(RT-0006/RT-0016);GT 缺口表`业务逻辑/竞态/反序列化真库 ❌`(evals/gt/README.md:36)。
- **ARTEX**: 无专门层(靠 worker 自由发挥,bizlogic设计档:24)。
- **CSAI**: 无(API安全测试角色有 GraphQL/JWT/fuzzing 提示词,CSAI清点§3——提示词级非引擎)。
- **判定: 缺失**(设计有,实现无;竞品同样空白=先发窗口)。
- **最优方案**: 按定稿五件建(~900-1200行,TDD,过棘轮): ①身份矩阵=账本 CRED 链取钥匙(普通甲/乙/管理员丙/未登录),每发现必挂 auth_context(RT-0016挂链血律);②差分探测器=同请求×身份×状态(前/后/取消后)全组合发,响应差对比,**零信息差不猜**(有差分=候选入账,无差分=诚实记`无信号`);③业务流还原+作弊假设(改价/优惠券重用/跳支付/取消后发货)→engine-hyp 卡进活池同调度,判真标准先行(GenSift律);④三族形态字典强制调用(头名/方法/参数族);⑤可逆纪律=不可逆且无测试账号=卡挂审批。考卷补业务流作弊种子入 range 下一版。

## F7 白盒联动(源码审计↔渗透)

- **我们现状**: 设计已批未实现——source-audit-v1.md 唯一正文全文批准(docs/design/2026-10-20-whitebox-final-ratified.md:6-8,四待裁位已自裁)+三参考折入五处(:11-16)。地基超前: 白盒 GT 锚已建(zl-webface 6面+zl-supplychain 4面+zl-chain 2链,gt-index.tsv:6-7,11,锚=verify_cmd 只读实跑);vuln-agent 引擎适配在(engines/vuln-agent/MANIFEST.md:10-15,八段管道,幂等键 intent_id);PHP POP 链/解析器-过滤器边界提取器在(corrections.py:46-49)。
- **ARTEX**: 无白盒(whitebox-final-ratified§三对比表: 无)。
- **CSAI**: source-code-hunting+binary-mobile-reversing 技能包(CSAI清点§4,24包之二)——知识包级,非联动引擎。
- **判定: 缺失**(联动本体未建;但 GT 锚/引擎适配/谱图分母封印设计=地基件两家皆无)。
- **最优方案**: 按 source-audit-v1 开工: ①分级账位表(文件入口入账/符号调用入工件/污点入卡/结论回账)+锚边双向联动渗透(代码→意图卡+渗透异常→代码复核);②确定性层全量必跑=漏检下界(GenSift patterns59 入 knowledge/staging 走入库管线,自裁④);③LLM 精读帽≤20文件×16KB 每仗单独计费(自裁②⑦);④车道B=五步证伪卡(DEFINE→OBSERVE逐跳→HYPOTHIZE≤8跳→VERIFY问`为什么不是洞`→CONCLUDE三列);⑤类判据规则库=GenCPT226条+VulnClaw L1/L2 经 staging 入库(自裁⑤)。

## F8 节点调度(意图池/派活/重派)

- **我们现状**: 干活半已建42仗实跑——意图池+租约认领+双抢互斥(cli/warrior/loop.py:305-319,认领竞败下一轮再选)+断点续跑接管活租约(loop.py:307)+R2串行链恰提升后继(loop.py:261-270)+停滞重生(loop.py:341-348)+门驱动(gateloop P0-P4,cli/ledger/gateloop_core.py:10-16)。派活半=规划者设计定稿未建(docs/design/2026-10-20-priority-planner-design.md 补件二/三)。
- **ARTEX**: 并发上限+排队+reconcile 补位(server :1106,3376)+Task Paused/Queued 状态机绑 ExpID(裁决书§19)。
- **CSAI**: ClaimNextPendingTask 原子领取(mutex 改状态+游标)+单队列并发1-8+双层防护(queueExecutors 与 status 解耦)+DB-first 持久化(CSAI清点§6)。
- **判定: 对等**。干活半在两家之上(租约到期自动回收+断点续跑+事件=账本行可回放——设计档:22 `它的事件=内存notify通道丢了就丢,我们=账本行`);**派活半缺**=ARTEX planner 闭环领先。
- **最优方案**: 常驻规划者三消费者(设计补件二): timeline 行追加=事件→①派生器(代码事实→意图卡/凭据→检查卡)②规划者(态势研判轮防抖[ARTEX 800ms同型]+覆盖缺口+排序公式→add_intent)③重派器四分类(纯故障重派/接续收口/边界固化/完成,trace行数+终态标记+产出计数纯机械)。降级模式=规划者缺席收卡时惰性触发(在册)。

## F9 智能体配置

- **我们现状**: 配置=CLI 旗标+channels JSON+skill 路径(cli/warrior/__main__.py:35-45);无配置对象/无界面编辑/无预览。
- **ARTEX**: planner/prompt+preview+visibility——规划器大脑界面可编辑(ARTEX清点§二`一切皆API可编辑`)。
- **CSAI**: 角色5条 CRUD(app.go:1431-1435)+markdown-agents CRUD(app.go:1057-1061)+config/tools/test-openai/list-models 13路由(app.go:1125-1136,CSAI清点§1)。
- **判定: 落后**。
- **最优方案**: 与F4同体(兵种YAML=配置对象,单源);界面编辑/预览排阶段2后(驾驶舱设置页先只读投影,复用 api_v2_settings 模式)。

---

# 二、真假把关 4 件

## F10 验证官(非LLM复验器)

- **我们现状**: POC 独立盲重放驱动(cli/tanyin-replay:3-19)——EV卡 raw_request 盲重放→vault 进程内解密(真值不进argv不落盘)→治理四门(授权窗/危险方法分类/次数帽REPLAY_CAP=3[cli/tanyin-replay:37-39]/scope单源)→matcher评估→三态(reproduced=VERIFIED/not-reproduced=REJECTED/env-diff=REPAIRED);判定产物只增不覆盖;judge 窄调用 fail-closed(cli/ledger/judge_client.py:1-23,键白名单+截断绝不补全)。
- **ARTEX**: replay-probe not-reproduced 机制同款(docs/design/2026-10-20-sentinel-retest-design.md:11)+零猜测纪律(不猜ID/无包不强制/失败不产部分漏洞,ARTEX清点§一)。
- **CSAI**: pentest-verification 技能(`搜索≠漏洞,confirmed 须证据`——提示词级铁律,CSAI清点§4)+agentfinalizer 最终答案裁决器(§2包表)。
- **判定: 已优**。机械盲重放+matcher+次数帽+四门是执法件;两家=行为准则/提示词级。

## F11 误报哨兵(非LLM代码级误报检查)

- **我们现状**: **在飞入库中**(工作树未提交): 14条规则文件已生(knowledge/engineering/sentinels-v1.tsv:6表头+SEN-001..014,来源=b40尸检4卡+RT复盘+竞品实勘;处置枚举 downgrade-to-fact|reject|mark-suspicious);判定引擎挂 judge_client(+101行);入库管线挂接 write_cmds report_finding(+33行,哨兵前置=便宜规则先跑贵的replay后跑);K6回流=distill 施工中(08:50Z存出语法错);tests/test_sentinels.py 已绿于全量跑。
- **ARTEX**: 无前置哨兵(证据链全在下游: replay证伪+报告Agent核对,ARTEX清点§一)。
- **CSAI**: 无(tool_result_guard=工具结果守卫、hitl Jev=审批审计,均非误报判定;CSAI清点§2包表)。
- **判定: 对等(落地中)**——一旦入库即已优: 前置降级省replay成本+版本化规则文件+K6回流通道,两家皆无(sentinel设计档:11)。
- **最优方案**: 收尾件(归在飞舰): 修 distill.py:375 语法错→K6回流测试绿→pathspec入库;后续=复盘卡`误报因为X`自动提规则草稿进 staging 人过目。

## F12 考卷体系(能力可度量)

- **我们现状**: evals/gt 7战场注册(gt-index.tsv:5-12: range-56-v5 56面23类/zl-webface-v1 6真+3诱饵/zl-supplychain-v1 4真+2诱饵/replay-G-r25~27 回放锚/zl-chain+range-chain 4链);链级两档判分写死(gt_eval.py CHAIN_TIERS: 整链1.0/部分0.5/零0);baselines 追加式不覆写;金样54面字节回归(tests/golden);指标注册 L1-L3(metrics-v1)。
- **ARTEX**: 无(裁决书§二:`召回/误报有数——六家都没有`)。
- **CSAI**: 无(CSAI清点289路由无评测面;web/static 36 .test.cjs=前端自测非能力考卷)。
- **判定: 已优**(独有)。短板自报: L4容器/云/业务逻辑空白(evals/gt/README.md:35-36)+held-out 冻结集未建(:38-39)。

## F13 复验纪律(发现必复验/定时复验)

- **我们现状**: 入库时一次性盲重放(F10)+复测页签只读投影(cli/webui/api_v2_retest.py:9-21: 复测队列=active findings×replay-probe 归并/复测历史逐次对齐 replay JSON/差异律=verdict变+状态码漂移皆入文)+capability_gate 误报面(scripts/capability_gate.py:15-16 活发现集内重放证伪)。**定时复验器未建**(设计定稿: docs/design/2026-10-20-sentinel-retest-design.md 补件二)。
- **ARTEX**: finding_retests.go 建成(sentinel设计档:19 `同型的直接参照`)+复测页在二级导航(裁决书§21⑤)。
- **CSAI**: POST /vulnerabilities/:id/retest(app.go:1332)+复测会话 roleTools 强制追加 get/update vulnerability(CSAI清点§6)。
- **判定: 对等**(一次性复验判定强度已优;`过时再验`件 ARTEX 已建成我们未建)。
- **最优方案**: 补件二Three件(~300行): ①过期清单=verified 发现带 last_verified,超窗(默认7天/活跃开发目标3天)入清单;②复验意图卡=过期发现自动生成 kind=nday-verify 同型卡(带原EV卡+重放命令)进**统一活池走统一排序**(ARTEX 独立跑,我们合池=设计优势);③三态回写=仍真(刷新)/已修复(转 repair-candidate 桶,报告面已有)/环境变更(关旧开新,dedup链)。

---

# 三、知识飞轮 3 件

## F14 蒸馏(战→卡)

- **我们现状**: cli/knowledge/distill.py v1(规则蒸馏确定性纯函数): 高置信模式→技法卡草案(同CWE≥2例verified带证据链)+失败路径→避坑卡草案三路(①误报路径=FD REJECTED/EV not-reproduced ②漏报族=MISSING按族计数 ③负面披露);草案纪律=只落草案+人工确认位,不自动写索引;确认后经 capability_gate.write_negative_card 一函落卡(distill.py:18-22);同输入两跑逐字节一致(:24);32测。
- **ARTEX**: 无战→蒸馏闭环(清点档无对应件)。
- **CSAI**: knowledge ScanKnowledgeBase=目录扫描入库(manager.go:35,CSAI清点§4)——静态语料入库,无作战复盘蒸馏。
- **判定: 已优**(闭环独有: 战→蒸馏→卡→下战即用,卡带战绩)。

## F15 知识库

- **我们现状**: knowledge/ 16子目录(concepts 50/negative/staging/cve/patterns/precedents/retros/business/checklists/methodology/entities/sources/targets+根索引);用法终裁=自动注入参考+自主打法+打完写回+变更过考试(裁决书§22过堂记录`知识库用法裁决`);脱敏哨兵(cli/ledger/knowledge.py:134,361 真域名/IP 零容忍);ng-index 负面轨双轨索引。
- **ARTEX**: 技能zip+promptcatalog(ARTEX清点§二/§四)——管理面。
- **CSAI**: knowledge 3864 LOC: 目录扫描→Eino向量索引(eino_sqlite_indexer)+检索链=改写→向量→HTTP rerank→后处理+检索日志回写(manager.go:743)+13条路由(app.go:1181-1309,CSAI清点§1/§4)。
- **判定: 对等**。语料/用法纪律/写回闭环强;**检索技术弱一档**(词面确定性打分 vs 向量+rerank——同义换词召回差距,直接影响卡被用上的率)。
- **最优方案**: 语义层双轨(不替换,合并): ①本地 embedding 索引落 knowledge/index(目录指纹增量重建,同 _CARD_CACHE 模式);②检索=词面分×0.6+语义分×0.4 合并排序,索引版本+模型id入检索行(可重放律);③零外联优先本地模型,需API道时=工具卡化走 gate;④检索日志入账(命中卡id+分数+意图id),飞轮仪表数据源。

## F16 棘轮(只进不退)

- **我们现状**: scripts/capability_gate.py 评测棘轮(宪法#43核心件): 一切能力件变更合并前过 GT-scorecard,召回/误报不得回退;--update-baseline 只紧不松(召回只升误报只降否则拒更,:20-21);CAPABILITY_SPECS 管技法卡/避坑卡/提示词/工具卡四类;gt_verify 注册表校验;rc契约 0/1/2。
- **ARTEX**: 无。**CSAI**: 无。
- **判定: 已优**(独有,`六家都没有`——裁决书§二)。

---

# 四、控制 5 件

## F17 对话指挥(对话=操作台)

- **我们现状**: 锚定对话 MVP 只读(cli/webui/api_v2_ask.py:1-24: AI只答不执,零账本写;锚=账本行址+行内容指纹;引用核验=[table.tsv#N]逐个对回真实行不信模型自报)+转向/停(steer.py warrior-steer/warrior-stop 事件词单源)+对话页在。**对话建任务/@引用派活/回复即指令未建**(设计定稿: docs/design/2026-10-20-command-approval-design.md 补件一)。
- **ARTEX**: 主Agent对话+@找漏洞/事实对话(裁决书§九用户点名)+旁路提问 btw 主任务不中断(裁决书§21②)。
- **CSAI**: 对话12条路由(app.go:1098-1110)+conversation_plantask 对话种任务+plan-tasks 产物查询(CSAI清点§6)。
- **判定: 落后**(能问/能转/能停,**不能开仗**;两家对话→任务链路已成品)。
- **最优方案**: 补件一三件(~650行,TDD): ①对话建任务=解析目标+意图→**任务卡**(目标/范围预览/红线/预算帽)→人点确认→battle 建立进活池——绝不起草稿直接跑(范围必须人确认,我们多出件);②@引用派活=fuzzy 搜全部账本对象(发现/事实/资产/意图/证据/任务)→钉行址锚入上下文(api_v2_ask 锚机制:20-23 已有)→`@它 再测一次`=生成意图卡进活池;③回复即指令=战士问事→人回一句→解析四分类(批准/拒绝/改方向/给情报)回战士。

## F18 会话管理(会话即对象)

- **我们现状**: 底座已优——账本行寻址(表+行号=ID工厂面)+transcript R4留痕(cli/warrior/transcript.py,loop.py:186-200 每轮 user/assistant 落盘)+多代合并律(api_v2_retest.py:15-17 同型: G号自然序/同id后代胜/timeline全局行号)+session 页。**会话即对象范式未落地**(裁决书§14定稿: 点进/续派/死会话归档可翻/管理操作符全套)。
- **ARTEX**: Session=工具注册表+compactor+transcript Store/Writer,每任务主转录带锁 exp<id>-main;子代理页=**日志视图非会话对象**(裁决书§19/§14——我们的超越点)。
- **CSAI**: conversation CRUD+delete-turn 清 last_react+token-usage+process-details 四模式分页锚点(CSAI清点§6)。
- **判定: 落后**(行寻址/留痕/审计超两家;**活会话管理面**——点进操作/续派/中断/复活/翻尸——零)。
- **最优方案**: 按裁决书§14单范式落地: 意图=会话单元(轮次=transcript行可寻址);会话页=每轮知识卡/工具/结果/入账行全可见(ARTEX §21①同型);续派=对终态意图再下指令(换打法/复测/派生——生成续接卡,复用 F8 重派器`接续收口`同型);死会话归档可翻=账本行保证(已有);管理操作符全套(列表/切换/中断/复活)挂 webui;比DSH多执法(守卫)、比ARTEX多活会话(裁决书§十九)。

## F19 审批与人

- **我们现状**: 审批入账本层+command_hash 绑定(cli/tools/gate.py:7,26-41——审批绑定命令哈希不绑定行,遗留行他哈希不放行)+L3档审批门挂卡(gate.py:5-7)+HMAC签名门(tests/test_p0_approval_hmac)+**预授权族**(cli/c2/families.py:1-15: grant/revoke行律/bounds键 hosts+max-cmds执法面/valid_until出窗族死fail-closed/每次执行仍入账)+审批中心全局页(cli/webui/api_v2_approval_center.py:15-24: 跨任务待审/已决/拦截流水/AI预审仅供参考)+guard拦截审批页。
- **ARTEX**: capture_approval(ArTEX清点§四 Agent内部件)。
- **CSAI**: HITL 17条路由(app.go:1030-1046): 人工审批+Jev(TypeSafe)审计agent自动审(拒绝阈值0.55)+工具白名单+默认审阅者+审计策略,四层配置(CSAI清点§1/§6)。
- **判定: 已优**(预授权降噪=收件箱零噪音+审批与作战同流+HMAC钥——裁决书§十五两超越点;AI预审已有同CSAI Jev位)。
- **补强(非必须)**: 超时默认保守策略+同类批量聚合一票(command-approval-design 补件二,~200行)。

## F20 看门狗(不停机自动化)

- **我们现状**: 四机制计算核(cli/ledger/watchdog.py:15-28: stall_grade 分级击杀 soft180/hard480+backoff 指数退避30×4^(n-1)cap480+read_directive 指令注入通道digest变化触发+next_tick 自适应节流)+runner 保姆(cli/tanyin-runner:1-11 心跳监控+停滞检测+死亡自动续跑+进程组击杀+env白名单:40-54 密钥永不进战士env)+战士级心跳/停滞重生(heartbeat.py;loop.py:160-162,341-348)+活性入账(warrior-start/stop/stall timeline 行,禁悄悄复活)+OS级 rlimit(tanyin-guard setrlimit,CI门 B:G2)。
- **ARTEX**: 清点档未见看门狗件(自更新3败自动回滚=更新面保险,ARTEX清点§三)。
- **CSAI**: processguard OS级(进程组/job object+watchdog+崩溃后子进程清理,CSAI清点§2包表)+C2会话看门狗+monitor orphaned对账(§1 monitor)。
- **判定: 对等**(引擎级四机制+活性入账超;OS级遏制已有rlimit件;**supervisor舰队化未建**——裁决书§十六/§十八补全三件之一)。
- **最优方案**: supervisor 常驻=坏停才重启(崩溃/僵死/通道断)好停不碰(预算尽/范围到期/完成/熔断挂起),重启=账本断点续跑+每次死/重启/唤醒入账带因(设计律,裁决书§十六)。

## F21 范围锁

- **我们现状**: Tier1/2 同源执法核(cli/ledger/enforce.py:1-13: deny-list/scope include/exclude/oob 三集加载+主机提取强化+**scope.tsv缺失=include空=一切带主机命令界外 fail-closed**)+Tier3 egress(egress_proxy/egress_mount 回连放行,账本=执法策略单一事实源)+replay host过scope单源(cli/tanyin-replay:18)+guard四层委托(cli/tools/gate.py:8-11)。
- **ARTEX**: 清点档未见表态件。
- **CSAI**: scope_block.go 项目范围阻断+toolguard 名称/参数正则阻断(政务域名默认保护;**明确声明不做host解析/重定向/文件检查**,CSAI清点§2包表)。
- **判定: 已优**(三层执法+代理编译同源;CSAI toolguard 自认不做host解析=我们的主机提取+amendment链是其缺口)。

---

# 五、执行底座 4 件

## F22 工具执行器

- **我们现状**: 卡层门链(cli/tools/gate.py:2-14: unknown-tool→deny-extra卡黑名单→supply-chain在役+lock现场复验→card-rate限速旗标固化→approval-required)+guard委托四层(scope+全局DENYLIST+nuclei参数门+限速滑窗);**25张工具卡**七纪律字段(cli/tools/cards.py:2-12)+tools.lock 25行哈希+ECDSA签名;同轮并行≤16+同卡同目标串行+原序入账(cli/warrior/executor.py:29,119-175);engines 7引擎适配(nuclei/sqlmap/deepex/vulnclaw/web-blackbox/vuln-agent/session-viz)。
- **ARTEX**: MCP 工具面+技能zip(ARTEX清点§二)——数量未披露,通道标准化。
- **CSAI**: **90个YAML工具**(86安全+4系统含exec任意shell原语)+执行链 Executor→buildCommandArgs→os/exec(executor.go:122/773)+ExecutionService韧性件(worker化+execution_id有界等待+get/wait轮询续接+取消+断路器+并发限+统一输出上限)+tooloutput超大输出落盘spill+processguard(CSAI清点§7/§2)。
- **判定: 落后**。纪律面已优(供应链签名锁/审批哈希/限速固化——两家皆无);**广度25 vs 90**(缺整整一类工具=对应洞类漏报,GT缺口表L4容器/云空白与此直接相关——无trivy/checkov/kube-bench卡);**韧性件缺**(长任务超时丢结果=漏报;CSAI清点冲击#7`值得整体抄`)。
- **最优方案(第一优先)**: ①韧性三件: 长任务异步形=工具卡加 async 位(execution_id+状态行落 goal 目录+有界等待+get/wait_tool_execution 轮询续接——先例=CSAI execution_service.go,我们状态行入账本可回放);断路器=llmpool 分道冷却同型移植卡层(连续N失败→卡冷却,成功治愈);超大输出spill=落 goal 目录 tmp+卡面 read 引用取回(corrections 截断面:22-23 已有,补落盘)。②广度补卡~30张(按CSAI清单选高频: hydra/john/hashcat/enum4linux-ng/netexec/responder/rpcclient/nbtscan/smbmap/feroxbuster/rustscan/masscan/dalfox/xsser/jaeles/arjun/paramspider/gau/waybackurls/trivy/checkov/kube-bench/kube-hunter/pacu/scout-suite/prowler/ghidra/radare2/objdump/strings/xxd/binwalk/exiftool/steghide/zsteg/volatility3)——每卡七纪律字段+tools.lock签名,分批过棘轮。

## F23 LLM池

- **我们现状**: cli/ledger/llmpool.py:2-24——错误分类表(ok/no_failover/hard[401/402/403/404一次熔断无冷却]/soft[408/429/网络/5x])+429分道固定短冷却1min+server长档1/5/30min+±20%抖动+软计数连续3熔断+状态落盘原子写重启恢复未过期冷却窗+每次trip/recover事件(kind=llm_failover);50测;llm_status 页+llm_recordings 页在。
- **ARTEX**: 逐任务LLM(tasks/:id/llm/resolution,ARTEX清点§二)+LLM故障转移系统事件流(裁决书§21④)。
- **CSAI**: llm 316 LOC(agentic chat适配+claude+deepseek兼容)+openai 2327 LOC(SSE流式/reasoning payload)——适配层,无池化熔断状态机(CSAI清点§2包表)。
- **判定: 已优**(池化状态机+分道+事件线上屏,超两家)。

## F24 外部执行后端(harness/MCP插槽)

- **我们现状**: 设计在实装无——裁决书§11(harness即后端: 任务包[意图+范围+预算]→harness会话→结果归一成记录行+录制回收,军团六维+执行后端)+§十七.1(harness依赖结论: **必装=无**,执行器=白盒兵种可选后端插槽,排阶段2军团层);宪法#54三标准兼容(agentskills.io技能/MCP工具/模型通道格式)未实装;vuln-agent CLI引擎适配=本仓自有进程执行先例(engines/vuln-agent/MANIFEST.md:8)。
- **ARTEX**: MCP(裁决书§三产品成熟度卖点之一)。
- **CSAI**: 外部MCP联邦7条路由(app.go:1166-1172: stdio/HTTP/SSE+断路器+连接恢复+启停)+平台级/mcp端点(带鉴权)+cmd/mcp-stdio+2个Python外挂(reverse_shell/pent_claude_agent,CSAI清点§1/§4)。
- **判定: 缺失**(插槽设计有,实装无)。
- **最优方案(阶段2)**: 执行后端接口落地=军团六维之一(任务包→后端会话→结果归一成记录行);首后端=MCP client(stdio优先)——外挂工具过卡层gate同治理(宪法#54兼容清单兑现);比multica强点=可审计(录制回收入账,裁决书§11)。

## F25 多任务治理(10并发)

- **我们现状**: 并发战资源仲裁核(cli/ledger/battle_registry.py:1-19: registry.json原子写+fcntl.flock防admit撕裂+**预算仲裁**(在册活战budget_usd合计+新战申报≤cap,拒绝判决带数学披露)+**端口冲突检测**(活战占用互斥+forbid_ports=8900/3000/8787/8443操作员面禁夺)+**死pid回收**(仲裁前收尸,注册表重启自愈))+goal-dir隔离独立账本+每任务一战士。缺: 十卡仪表盘/supervisor舰队化/全任务工具总并发帽(裁决书§十八缺三件)。
- **ARTEX**: 并发上限+排队+reconcile补位(裁决书§19)+多租户 companies/:id/scope(ARTEX清点§二)。
- **CSAI**: 批量任务14条路由(app.go:1082-1095: 队列/pause/rerun/cron调度/单条执行取消在飞兄弟)+ClaimNextPendingTask原子领取+双层防护+DB-first(CSAI清点§1/§6)。
- **判定: 对等**(仲裁核三执法——预算/端口/死尸——超两家;**表面积窄**: 无仪表盘无舰队supervisor)。
- **最优方案**: ①全局资源治理=battle_registry 扩仲裁位(Σ在飞tool调用≤全局帽+llmpool state 可选全局共享限速);②十卡仪表盘=驾驶舱首页四问直投( cockpit-ui-blueprint 数据面api_v2已就绪);③supervisor舰队化=F20件合体。

---

# 六、交付 2 件

## F26 报告生成

- **我们现状**: 机械骨架已建成29测绿(docs/design/2026-10-20-report-upgrade-design.md:3): report_lint(Burp可贴四规则+双指纹+sign_gate聚合+pass.json签发+禁空话句式)/report_artifacts(findings.json全量生命周期+SARIF 2.1.0仅verified+narrative_filter+九段FD渲染)/report_render(同输入同输出钉死)/report_agg+tanyin-report CLI。**证据版本绑定+报告员自动触发未建**(补件设计定稿同档)。
- **ARTEX**: 独立报告Agent——入库→自动触发→traffic_search/traffic_get核对→绑定→**按最新证据版本写报告**+过期版本拒写+绑定失败全回滚(ARTEX清点§一——最强竞品件)。
- **CSAI**: reporting-remediation 子代理(13子代理之一,CSAI清点§4)。
- **判定: 对等**(机械把关/签发门/SARIF超两家;**自动触发+证据版本管理落后ARTEX**)。
- **最优方案**: 补件三件(~800行): ①证据角色四档(baseline/proof/verification/supporting)+清单顺序+绑定版本号(任何增删改=+1)+渲染携带evidence_version过期拒写+已发报告标待更新;②报告员兵种=军团新兵种(六维: 只读账本+EV/技能=报告写作卡/产物必过sign_gate全门,打回≤2轮转人工),触发=战役收口自动+人工随时;③渲染manifest快照各finding的evidence_version,漂移=出`证据已变化待重写`清单不渲染半新半旧。

## F27 驾驶舱界面(最后建)

- **我们现状**: webui 23个api_v2只读投影模块(tasks/findings/coverage/graph/approval-center/ask/retest/llm-status/llm/evals/capability/techniques/workspace/assets/guard/settings/system/broadcast/tools/asset-registry/reports/v2)+static页(console_dash/findings/graph/live/approval/coverage/session/metrics/new/login)+SSE+登录会话门;页面测试500+。驾驶舱蓝图定稿(docs/design/2026-10-20-cockpit-ui-blueprint.md: 25页砍6面+首页四问+五秒三问律+全站词表强制+会话即对象+空状态人话)。在飞: task_actions/techniques_deeplink/findings_overview WIP红测12失败(TDD)。
- **ARTEX**: 24页成熟产品——任务内二级导航(会话/总览/链路图/播报/发现/复测/资产/覆盖/审批/报告)+实时消耗表(每会话input/cache/output/耗时)+系统事件流(LLM故障转移等)(裁决书§21③⑤)。
- **CSAI**: 36个data-page视图SPA(index.html 7032行,无框架无构建;dashboard/chat/tasks/assets/vulnerabilities/projects/knowledge/hitl/monitor/mcp/c2/webshell/terminal等)+i18n三语(CSAI清点§2 web/)。
- **判定: 落后**(骨架+数据面就绪;**交互范式**——会话即对象/旁路提问/实时消耗表/四问首页——未落地;驾驶座判定律#56: 只说差距清单不说超越)。
- **最优方案**: 按cockpit-blueprint六面施工(首页四问[漏洞榜/活池实时/收件箱/消耗表]/任务页tabs[概况·地图·活池·漏洞·消费·日志]/漏洞页[证据袋+上次验真X天前+待复验队列]/知识库页[打法卡+哨兵规则+蒸馏草稿人审]/收件箱/设置)+三层验收(每页五秒三问入代码注释/词表扫描器进CI/真数据全通api_v2直投);实时消耗表数据源=budget.tsv+llmpool事件(已就绪)。

---

# 七、落后+缺失总清单(按第一性: 误报/漏报/召回 排序)

| # | 件 | 档 | 第一性害(为什么排这) | 最优方案一句话 | 量级 |
|---|---|---|---|---|---|
| 1 | F22 工具执行器 | 落后 | **漏报直害**: 25 vs 90卡=缺工具类=缺洞类(GT L4容器/云空白直接相关);长任务超时丢结果=漏报 | 韧性三件(异步execution_id+断路器+spill)+补卡~30张 | ~600行+30卡 |
| 2 | F6 业务逻辑层 | 缺失 | **漏报大类唯一解**: 越权/流程作弊工具永远扫不出(GT业务逻辑行❌);竞品全空白=先发窗 | 身份矩阵+差分探测器+作弊假设卡(定稿五件) | ~900-1200行 |
| 3 | F7 白盒联动 | 缺失 | **漏报L2深度**: 黑盒漏的源码洞白盒补;GT白盒锚10面+2链已建无消费方;设计已批可开工 | source-audit-v1分级账位+确定性层全量(漏检下界)+精读帽+锚边双向 | 按老档建序 |
| 4 | F17 对话指挥 | 落后 | 召回间接+可用性门: 不能开仗=能力出不了手;人机协同密度=每日有效扫描量 | 任务卡确认门+@引用派活+回复四分类(定稿) | ~650行 |
| 5 | F4+F9 军团+智能体配置 | 落后 | 吞吐→有效召回: 兵种编制面零=并行兵力/专精分工出不来(运行时已强) | 兵种六维YAML包+总控steer派单+首批5兵种 | ~300行+5模板 |
| 6 | F24 外部执行后端 | 缺失 | 生态杠杆非直接召回: 白盒兵种可选肌肉+工具面无限扩展 | 阶段2: 任务包→后端会话→记录行归一+MCP client stdio首选 | 按裁决书§11 |
| 7 | F18 会话管理 | 落后 | 控制/审计面(第一性弱): 续派/复活/翻尸缺=战场经验利用率降 | 会话即对象六面(意图=会话单元+续派卡+管理操作符) | webui面 |
| 8 | F27 驾驶舱 | 落后 | 交付面(第一性最弱,原令最后建): 数据面api_v2已就绪等壳 | cockpit-blueprint六面+三层验收 | 驾驶舱舰 |

对等件的窄缝备忘(不进总清单,建序参考): F1外部资产源四引擎(FOFA/Shodan/ZoomEye/Quake卡化)、F3卡命中计数、F15语义检索双轨、F13定时复验器、F11哨兵收尾、F8规划者、F20 supervisor、F25全局并发帽——其中 F11/F5 在飞入库中,F13/F8 已有定稿设计。

## 完成报

- **已优 8件**(F2探索图/F10验证官/F12考卷/F14蒸馏/F16棘轮/F19审批/F21范围锁/F23 LLM池)
- **对等 10件**(F1枚举/F3打法/F5优先级[在建]/F8调度/F11哨兵[在飞]/F13复验/F15知识库/F20看门狗/F25多任务/F26报告)
- **落后 6件**(F4军团/F9智能体配置/F17对话指挥/F18会话管理/F22工具执行器/F27驾驶舱)
- **缺失 3件**(F6业务逻辑层/F7白盒联动/F24外部执行后端)
- **前三优先补齐**: ①F22工具执行器韧性+广度(漏报直害,25→90卡+异步/断路器/spill);②F6业务逻辑层(越权/流程作弊=工具扫不出的大类,竞品全空白);③F7白盒联动开工(设计已批+GT锚已建,补黑盒漏检的L2深度)。
- 底数: 实测 Ran 2846 tests(failures=12[全为在飞WIP红测]+errors=7[5=Playwright环境件+2=WIP]);50技法卡/25工具卡/14哨兵规则(在飞)/7 GT战场;三战召回0.62/0.62/0.70,FP=31/3/1。

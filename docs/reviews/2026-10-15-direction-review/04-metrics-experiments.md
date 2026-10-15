# 04 · 度量与实验设计独立评审（2026-10-15 方向评审）

> 评审镜头: 度量与实验设计（独立评审,不与其他专家通气）。
> 靶项目: /Users/wgen/redteam-agent（探隐,自主性优先转向 + 修正案A 白盒双车道后）。
> 证据基（全部实读）: docs/design/tanyin-product-v1.md（含修正案A/B/C）/ docs/design/BLUEPRINT-RECON.md / docs/design/engine-fusion-architecture.md §0-§6 / docs/research/liveui/6-gensift.md §五（吸收判决）/ experiments/README.md + directive-n5.tsv / cli/webui/metrics.py（232 行全读）/ tests/eval_range_recall.py（评分器）/ tests/range/ground-truth.json（GT 真身）/ scripts/experiment_dualarm.sh + experiment_variance_n5.sh / knowledge/retros/RT-0023·RT-0024 / ~/.tanyin/battles 13 战 settle 报告 + b40 战报（honest_misses 与读取路径自报）。文中统计数字均由本人在真实战报上重算复核。

---

## 【总判决】

**偏——方向对,刻度错。置信度 0.82。**

方向对的部分,先给足分: 把度量当真事——预登记律（开战前先落 tsv）、判后回填律、诚实披露「子集不可复原」（directive-n5 穷举 6758 个子集自证无法复现旧判决）、McNemar exact 数学钉死（与 rerun.py 逐点同口径）、金样钉测防评分器漂移、RT-0023/RT-0024 两级教训入律。这套自我纠错文化在同类 AI 安全项目里罕见,是 true asset。

刻度错的部分: 产品已转向「自主性优先 + 白盒双车道」,整套度量栈还停在**单战士、离散战、单把尺**时代:

- GT 56 题实测全为单请求 marker beacon 洞（23 类零业务链、零多步、零利用深度）,而自主化的卖点恰恰是链路与广度——九专家会诊最严重的未解发现,至今未动;
- 唯一结算指标 recall 在 13 战语料上已呈**双峰饱和**: 约 20 题从未 miss、13 题在全部 13 战全 miss,判别带宽只剩约 22 题;
- McNemar 用「臂内任一战命中即命中」的并集池化——丢臂内方差、饿不一致对自由度,n=5 双臂下最小可判不一致比约 2.6:1,却敢在 HANDOFF 写「彻底无效果」;
- 实验登记处 11 字段装不下 v1.0a/b 的实验类型;n5 血泪换来的三要素（子集清单+per-GT 快照+口径版本）没有一个是机械字段,只活在 note 散文里;
- 对照组纯度靠战士「读取路径自报」——而 b40 战士自报实读了**前战账本当打法参照**,跨战信息泄漏已在发生且被视为正当。

若不先修刻度: v1.0a 白盒 McNemar 与 v1.0b Tier2 闸门实验会在错误的尺子上产出「显著/不显著」,然后被写进产品决策——比不做实验更糟,因为它带着统计的妆容。

---

## 【发现按严重度】

### F1（致命·效度）GT 体系量不到自主化的主卖点——但答案是分层扩建,不是推倒重造

**现象+证据**:
- tests/range/ground-truth.json 实测: 56 题 = 23 类（sqli/xss/ssti/cmdi/ssrf/cors/deser/traversal/redir/infoleak/idor/role/hauth/weakpass/lfi/broken-access-control/jwt/graphql/ratelimit/userenum/xxe/rfi/upload）,**全部为 planted marker 型**（GTSSTI-01/GTCMDI-01…）,结算主通道=EV 卡 word matcher 命中 gt.marker（eval_range_recall.py:262,beacon 轨）。差分轨（authz-diff/控制对,eval:269-284,双轨设计本意是「行为差分」）在 16 份 settle 报告里**只命中过 1 次**——事实上的死轨道。
- 九专家会诊已点名「业务逻辑链 GT 为零 + 利用深度回显级」为渗透维度最战略缺口（00-SYNTHESIS.md:25）,P2 方案（键形 v8 链路完成率 + held-out 泛化靶,:62-63）在册未动。
- 13 战 missing 频次（本人重算）: **13 题在全部 13 战全 miss**（hauth-01..04/role-01/02/csrf-01/02/jwt-01/graphql-02/ratelimit-02/infoleak-02/cmdi-02）,rfi-01、jwt-02 也仅 12/13;另有约 20 题从未 miss。分母的 23% 是死区,36% 是送分区,判别带宽约 22 题。
- b40 战报 honest_misses 归因: 死区三大主因=凭据链未破（弱口令面全 403）/载荷形态未破（XXE 全 400）/结构无投放点（JWT 验签面 401）——**不是探索不足,是情报不足**。这恰好是白盒车道（源码里有答案）的靶子。

**危险**: 自主性优先的产品主张=「AI 战士自主打多快多广」。若结算尺仍是单请求 beacon recall,则 (a) 多战士并行、常驻循环、Tier2 吸收的全部判决都量不到它们存在的理由（并行覆盖/链路完成/成本效率）; (b) Goodhart 锁定——系统持续优化 22 题判别带,死区永远死,产品报表「稳定 0.7」。

**修正方向（分三轨,冻结不推倒）**:
1. **冻结 56 技术轨为 GT-T1 回归尺**——它是 13 战基线与金样钉测的锚,动它=断代自残;口径与 keying 版本一并冻结,存量 per-GT 快照入库。
2. **新建 GT-T2 链路轨（键形 v8）**: 业务逻辑洞进 GT 的造法不是「发 marker」,是**终态断言**——场景剧本靶（负数量下单/优惠卷竞态/越权流程跳步/状态机 bypass）+ 结算 oracle=可观察终态（余额/订单状态/权限变更）。结算通道长在现有 authz-diff 差分轨上（单请求差分升为状态差分）,别另起炉灶。每题预登记: 前置状态机+成功终态判据+expected EV 形态。GT-T2 分母独立（GenSift B5 两本账判据: 追加轨不计入冻结分母,单独披露闭合率——判据已在吸收判决里,直接用）。
3. **held-out 异构靶前测**: 字典逐代回灌+单靶族=教考合一（九专家 3/9 汇聚）。自主化后系统会把这把尺更快优化到死——每次吸收引擎/战士群变更,先跑一次改名靶前测再签字。

### F2（致命·污染）对照组不纯是结构性的: 战士跑在 repo 里,GT 与源码物理可读,纯度靠自报

**现象+证据**:
- 战士工作目录=本仓（mission.txt 引用 tests/range/battle-kit/BRIEF-template.md、.opencode/skills/tanyin）;ISOLATION_ENV（cli/tanyin-runner:24-30）只关 opencode 自动更新,**无任何文件系统隔离**。「GT 零读」的唯一凭证=b40 战报「读取路径自报」——**自报,无机检**。九专家已点名「GT 物理可读→Goodhart 推力」（SYNTHESIS:21）,P1 行动项「无 GT 战士工作区」至今无实现痕迹（全仓 grep 无果）。
- 更硬的实锤: b40 自报表白读 **battle-39/G-r40 账本当「打法参照」**——跨战信息泄漏已在发生,且被定性为正当行为（「非 GT」）。10 个「独立样本」共享前战 findings,战间独立性已碎。
- 修正案A/engine-fusion §5 的对照臂=「同战士、无源码情报」。但靶场源码就在 tests/range/ 与本仓同盘,战士连 cli/ledger 源码都读了（自报表）。对照组「没读码」将是又一次自报。

**危险**: 白盒 McNemar 测的是「源码情报的增量召回」。对照臂若能自读源码,测出的是「有人喂 vs 没人喂但可以自己拿」——效应系统性低估; 两臂都读,测的是噪声。花 N 战预算买一个不可解释的 p 值,还写进路线决策。

**修正方向**:
- **前置硬门（v1.0a 实验开战前完成,否则实验不开打）**: ①GT-free/源码-free 战士工作区（sanitized mirror: 只挂技能+战书+靶场入口;deny tests/range/、knowledge/ 喂养条目、~/.tanyin/battles/）; ②机检替代自报——账本命令审计面挂路径哨兵（读 tests/range/ 即事件入链,两臂同执法,OPSEC 批已有 guard/ua 轨可挂）; ③**跨战隔离**: 实验窗口内禁读前战账本——最容易被漏的一条,b40 实锤。
- 处置臂的「情报」必须是钉死 artifact: 引擎快照版本+intent 集合 sha256+车道A pattern 版本,入 tsv treatment_artifact 字段; 否则「加了源码」是话术不是变量（对照 directive 实验的教训: 处置=b28 一份演化中文本的 cp,experiment_dualarm.sh 实锤）。

### F3（严重·统计）McNemar 三病: 并集池化丢信息、GT 项非独立、n=5 功效奇低却被写成「彻底无效果」

**现象+证据（全部可机械复核）**:
- metrics.py:115-128 pooled_mcnemar 口径=「臂内任一战命中即命中」。本人按 n5 两臂实算: 对照五战并集 42/56、处置并集 39/56,不一致仅 **b=3（cmdi-01/jwt-02/userenum-01）c=0,p=0.25**（与 directive-n5 note 回填一致）。并集池化把约 20 道「全对题」与 13 道全 miss 死区全部扔掉——**判别信息只住在 22 题中间带,b+c 结构性饥饿;且臂数越多并集越饱和,加样本反而降敏度——反向设计**。
- 56 题按 8 服务×同类机制强聚类,McNemar 独立配对假设不成立,有效自由度远小于表观 n。
- 功效实算: n=25 个不一致对时,17/8 分裂 p=0.108,要 18/7 才过 0.05（p约0.043）——**n=5 双臂的最小可判不一致比约 2.6:1**。就这样分辨率,HANDOFF 写的是「指令策略检出力内=彻底无效果」。方差压缩器结论同样在 3v3「压缩器!」与 n=5「死刑」（Brown-Forsythe F=0.052）之间翻转——两次都是欠功效下的过度解读。零结果不等于无效应。
- 臂仪器化粗糙: 臂标签=directive.txt 字节数（metrics.py:44-50,大于0B=处置/缺文件=未知）;实验脚本先对照后处置**块状顺序分臂**,与时间漂移/API 故障混杂;b31-34 死于断连后按「清僵尸+净样本重跑」补样——替换规则未预登记。

**危险**: 修正案A 说「源码车道贡献单独计数+McNemar 判加源码是否提召回」、engine-fusion §5 说「McNemar 协议复用」——复用的是一个已知三病的协议。若白盒真实效应是「死区救回 4 题」,在并集池化+5v5 下大概率先得 p=0.25,然后被写成「白盒无增益」,反过来杀死车道B——**用错尺量错物,错杀自己刚批的设计**。

**修正方向**:
1. **主检验换战层配对置换检验**: 以战为单元、统计量=分层 recall 差、随机化推断精确成立;5v5 最小 p=1/252约0.004 可判,3v3 最小 p=0.05 恰好压线——**每臂 N≥4 是硬下限**,预登记进 decision_rule。
2. McNemar 降为描述性披露（per-item 不一致清单保留,对归因有用）;坚持要用地按服务聚类做 cluster bootstrap、只在预登记分层内池化。另:「源码车道贡献单独计数」（edges cross_ref 归因）是**描述性计数**,McNemar 是**因果性增量**——两者必须分开标名,混用就是把「引擎先到」算成「引擎之功」。
3. **分层主指标**: post_auth=16 题是白盒理论增益区（b40 归因实锤: 凭据链/载荷形态/结构投放点三类 miss 全是源码可答的）。全 56 池化=把效应稀释在送分区。预登记「post_auth 层 recall 为主指标,全量 recall 为次」。
4. 零结果话术纪律: 欠功效设计只许写「未检出大于等于 MDE 的效应」,MDE 预登记;「彻底无效果」从 HANDOFF 词汇表删除,除非功效分析支持。
5. 臂随机化: 交错或抛硬币定序,告别块状分臂;断连/冻结战的替换规则预登记（wallclock detect_gaps 轨正好做断连窗取证——零件已落地没人用）。

### F4（严重·登记处）11 字段装不下 v1.0a/b 实验类型;n5 三要素没进字段,只在散文里

**现象+证据**:
- 现字段 11 个（id/question/battles_control/battles_treatment/gt_gen/decision_rule/registered/status/verdict/source/note）。README 明言「度量页缺字段降级为空串」——降级是常态路径而非异常。
- directive-n5 用血换来的三要素（子集清单+per-GT 快照+结算口径版本;HANDOFF 2026-10-14 节自记「已由律吸收」）**没有一个是登记字段**: 子集清单算半个（battles_*）,快照与口径版本只在 note 散文。battles 数据在 ~/.tanyin（仓外）,keying 升级会重结算存量战报（b30/b36 口径漂移实锤）——不把快照 sha256+评分器版本入库,下一个 n5 是必然不是风险。
- v1.0a/b 的新实验类型已现形,现 schema 全靠 question 散文硬塞: ①白盒双臂（处置=情报注入 artifact,非 directive 文本——臂机制字段缺失）; ②sim 注入精度门（7 真 3 假,单臂 pass/fail 门,不是 A/B）; ③Tier2 战士群吸收闸门（二值决策+多目标）; ④常驻循环回合实验（无自然战边界）。
- 台账矛盾: BLUEPRINT-RECON 称 b11 计划「在库未执行」,RT-0024 记 b26 已按该计划跑完臂B 并判决——同一实验在台账里两种状态。且登记处 2026-10-14 才立,晚于全部历史实验,唯一在册实验是一座不可复原纪念碑。

**危险**: 登记处是度量页「预登记实验」的唯一数据源;关键字段缺失,随机化/快照/终止/污染控制全部退化为 note 自由文本,不可执法,下次判决照样不可复现——度量纪真律退化成度量纪散文律。

**修正方向——扩到约 20 字段,分四组**:
- **判据组**: hypothesis（含 estimand: 什么单元、什么效应、对谁）/ primary_metric（+分层说明）/ secondary_metrics / decision_rule（保留）/ multiplicity（协同主指标数与 alpha 分配）/ power（每臂 N+MDE+最小可达 p）。
- **设计组**: unit（battle/episode/窗口/战士会话）/ pairing（配对键=gen+任务书 hash+模型版本）/ arm_assignment（随机化方案与执行序）/ treatment_artifact（处置物 sha256: 引擎快照/intent 集/pattern 版）/ stopping（常驻循环终止判据+中途窥视政策）。
- **完整性组**: snapshots（per-GT 快照路径+sha256;settle-report sha256）/ scorer_version（keying 版+评分器 commit）/ env_versions（模型 id/opencode/runner/知识库快照 hash/战书模板 hash——RT-0024 教训#4「同任务书同代字典」的字段化）/ failure_handling（断连战/verify-chain FAIL/重启超阈的进出规则）。
- **污染组**: contamination_controls（GT-free 工作区/源码 deny/禁读前战账本/知识冻结窗口,逐条附执行证据）/ audit_commands（reproduce 一行命令从快照重演出 verdict,进 CI）。
- 另把预登记律从页面惯例升为**机械门**: experiments_view 投影时校验——判决回填而缺 snapshots/scorer_version,度量页标红「不可复现判决」。诚实要被机器看见,不是被 note 记住。

### F5（严重·回合化）常驻循环+多战士下,「战」作为度量单元正在溶解,而没人重新定义它

**现象+证据**:
- 现行度量链以 battle-N 目录+settle-report.txt 为原子（metrics.py:149-167）,McNemar 配对单元=战。v1.0b=规划者常驻+多战士并行+多战场登录——战的自然终点（战书打完/P6 收口）消失,**recall 变成停止时刻的有偏统计: 什么时候结算,recall 就是什么**。
- 多战士共享 intents 池、findings 按指纹去重（engine-fusion §2-3）——单战士 recall 不可分;规划者与知识飞轮跨战持续学习（v1.0b 连接点: knowledge/ 注入战士 brief）——臂间/战间学习混杂会淹没处置效应。
- 终态判定自身尚有契约矛盾: b40 P3 degraded 因 token 份额穿线触发 budget-exhausted 假降级、P5 FAIL 留痕「terminal_b 与零空格清单矛盾」。

**危险**: 单元溶解后,McNemar「每单元每臂一次测量」的前提直接不成立——不是口径问题,是检验对象不存在了。Tier2 闸门实验若在此状态下开跑,判决=噪声+学习曲线的混合物。

**修正方向**:
1. **episode 冻结五件套**: target gen+任务书 hash+预算包+知识库快照+引擎/规划者快照——五者齐备才算可结算单元;登记处 unit=episode。
2. 终止判据预登记（预算耗尽|规划者 DONE|wall 上限,三选一判前定死）;结算器在判据满足时强制 settle,禁止「看着差不多就收」。
3. 时间维度入账而非入检验: time-to-GT-item 用 wall_clock 双轨（2026-10-15 已接 battle.py 三铸点）——自主化卖点本来就是「更快」,时延指标比第五个召回变体更有产品意义。
4. 多战士: 战=簇,簇内战士贡献向量走 edges cross_ref 归因（机械可查）,统计检验只在战层做;要战士层结论就先隔离 intent 池另开实验,别混。

### F6（中·多目标）recall 单指标时代该结束,但别开动物园——字典序+栅栏,不开合成分

**现象+证据**:
- 现状: settle 只出 recall 一个数。但零件早齐了: RT-0024 已用三项裁决（score/恢复成本/token 约 log 字节+会话数）——多目标先例在库;GenSift 吸收判决自带成本模型（token 与卡数成正比;band0/1 级联无效必须逐卡——高危无捷径,成本结构已知）;llmpool 已能计数调用与失败转移;wall_clock 轨已铸账。**结算面没接**。
- token 计量现仍是 log 字节 proxy（b11 计划度量③原文）,战士侧无真值——成本指标地基是软的。

**危险**: 自主性优先的叙事=「账本决定敢让它打多快」=速度×覆盖×成本三轴;只报 recall 等于把产品主张留在门外。反过来,8 个指标并排进结算、每个欠功效,则每次比较总有一个「显著」——多重比较动物园,比单指标更骗人。

**修正方向**:
- **字典序决策,不做加权合成分**: 预算栅栏内（token/wall 不超限、OPSEC 违例=0）,最大化分层 recall 主指标,平手比成本（每 M token 检出数/每 wall 小时检出数）。栅栏是合格线不评分——OPSEC 违例直接判无效战,不给「扣分后及格」的路。
- 结算页报 **Pareto 前沿**（逐战 recall×成本散点）不报综合分;均值必带区间（对照臂带宽 0.41-0.70 自己就是「单点均值会说谎」的证据）。
- token 真值计量先行: 从 runner.tsv+llmpool 侧接出战士会话调用/计费;没有真值前,一切成本结论带 proxy 标注。

---

## 【被忽视的既有资产】

1. **authz-diff 差分双轨**（eval_range_recall.py:269-284）——状态差分结算的活种子,GT-T2 链路轨的结算通道应长在这上面;16 战仅 1 命中说明它缺的是业务（有差分语义的靶）,不是代码。
2. **wall_clock 双轨 + detect_gaps**（2026-10-15 OPSEC 批刚接 battle.py 三铸点）——时延指标与断连混杂取证的零件已落地,零个实验设计在用它。
3. **edges cross_ref（engine-hyp 与 finding）+ intents 不蒸发律**——「源码车道贡献单独计数」的归因底座已在账本设计里;注意归因计数不等于反事实增益,分名标注（见 F3 修正 2）。
4. **13 战 per-GT missing 明细**——免费的先验功效分析数据: 双峰结构（约 20 全对/13 全死/22 判别带）+死区三类归因（凭据链/形态/投放点）就是白盒实验分层与样本量估算的现成依据,零战成本。
5. **GenSift B5 两本账 + B6 归因五分类**（6-gensift.md §5.3 B5/B6）——GT 扩建后的覆盖算术判据（冻结分母 vs 追加分母）与 keying 漂移归因词表（判定翻转/抽样波动/L2 差异/refreeze 差异/处置库变更）都已在吸收判决里,登记处还没收编。
6. **scripts/rerun.py + experiment_dualarm.sh / experiment_variance_n5.sh**——双臂执行基建在,缺的只是随机化、快照、版本钉三件事;改造比重造便宜一个数量级。
7. **b11 计划 + RT-0024「干净重跑」待办**——同任务书同字典、N大于等于3、与 --repeat N 方差协议合并设计的路线写了没人走;BLUEPRINT-RECON 与 RT-0024 对 b11 状态各执一词,这笔台账债本身该进登记处。

---

## 【三问给主会话】

1. **v1.0a 白盒实验敢不敢预登记成「post_auth 层 recall 主指标 + 战层配对置换检验、每臂 N 至少 4」?** 不敢的话,你们准备用一个在 22 题判别带上 b+c=3 起步的并集 McNemar 去判「源码有没有用」——实验还没开打就注定产出又一个 p=0.25 的「彻底无效果」,然后错杀刚批的车道B。要不要先做零战成本的死区归因分析（14 题逐题判: 源码可答/不可答）再定主指标与样本量?
2. **GT-free/源码隔离工作区（九专家 P1,至今未建）是否升格为白盒实验的前置硬门?** b40 战士自报实读前战账本当参照、读 cli/ledger 源码——没有机检隔离之前,「对照组」三个字写进 tsv 是不是自欺?实验窗口内禁读前战账本这条,打算怎么执法?
3. **GT-T2 链路轨（键形 v8）与 v1.0b Tier2 闸门实验,谁先?** 若闸门实验先落地,多战士吸收的判决尺仍是单请求 recall——量不到多战士存在的理由（并行覆盖/链路/成本效率）。顺序错了,吸收判决就是拿错尺量错物;如果资源只够先做一个,凭什么先做闸门?

（评审纪律声明: 对靶项目全程只读零 git;唯一写入=本文件。）

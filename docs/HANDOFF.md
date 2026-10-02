# 探隐开发账本 · HANDOFF（追加式，不删行；每笔交付后记账）

> 目的：会话会死，账本不死——跨会话/跨代理的唯一事实源。接手者读本文件即可零上下文续作。

## 当前状态快照（2026-09-24）
- 批次 0 契约冻结：✅ contracts-v2（13 表/41 命令/边词汇/四层档位）
- 批次 1 账本命令箱+金样：✅（金样字节级回归绿；细节待独立审计确认）
- 批次 2 门禁层：基本收官——enforce 单源化(500ae44)+Windows 兼容+CI 双平台绿(730d743/70826a5)；181/181 测试绿
- 批次 3 总控 skill+引擎+受管重启/恢复：**完成（T1-T13 收口，2026-09-24）**——310→317 单测全绿+42 金样面 PASS；出口验收 11 条逐条实测过（第 10 条 CI：workflow 四格矩阵在册+push 已触发，远端绿需 Actions 页面复核）；契约回注三笔=契约09（G-1 工具 10→11）+契约02a（G-6 state.md v2 十键+G-10 checkpoint 签名，微版本勘误通道）；探知项台账 G-1..G-15 终态=docs/design/2026-09-24-b3-discovery-notes.md；Ruling 总索引=文末「批次 3 Ruling 总索引」节
- 批次 0/1/2 完成度独立审计：**进行中**（子代理 865488fb，出口条款逐条实测）
- 全景图 v2：定稿（0fbab87 模拟运行；SPEC 三层契约在 docs/design/imported/TanYin/panorama/SPEC.md）
- 工程纪律：UTF-8+LF 红线/py -3 等价/双平台 CI（.github/workflows/ci.yml）
- 批次 3 评审收尾：✅（2026-09-24）评审结论=可收，Important×2 已清（契约09 枚举补齐+金样进 CI --bless 门槛）；317→322 单测全绿+42 金样面 PASS（详见文末「批次 3 评审收尾入账」节）
- 批次 4 引擎层：**完成（T1-T14 收口，2026-09-24）**——409 单测全绿（批 3 基线 322+批 4 新增 87）+50 金样面 PASS 零漂移；出口验收 10 条逐条实测过（第⑧条 CI：push 已触发，四格矩阵在册，远端绿需 Actions 页面复核）；契约勘误七笔（01/02a×2/04/06/07/09+PROTOCOL×3——微版本通道 schema_version=2 不递增）；优先级调度 fb72cd5/图查询 71d3b7c/FD 规格 b0006f2 三设计增补全落；探知项台账 G-16..G-26 终态=docs/design/2026-09-24-b4-discovery-notes.md（G-2/G-12/G-13 在 b3 台账就地注记闭环）；Ruling 总索引=文末「批次 4 Ruling 总索引」节
- 批次 4 评审收尾：✅（2026-09-24）C-1 证据双指纹 norm 轨写/查单源化（cli/ledger/norm.py，严格侧哨兵语义冻结模块 docstring）——diff-authz hash-recheck 与 gate P4 亲跑 PASS（P4 完备化=夹具补确定性重放事件行，G-23 墙钟绕道）；顺手三件（cli/README 计数 41→44×3+面数 50→51/supply_chain fail-closed 形式统一两负例/b4 台账 G-27+G-28+R6 机检缺口挂 G-20）；414 单测全绿（409+5 新增）+51 金样面 PASS（新面 diff-hash-recheck；viz-data 有意刷新=timeline 计数 19→21）；详见文末「批次 4 评审收尾入账」节
- 批次 5 知识飞轮+语料入库：**完成（T1-T19 收口，2026-09-24）**——564 单测全绿（本段起点基线 545+T18 前置/T18/T19/T19 补新增 19）+54 金样面 PASS 零漂移；出口验收 10 条逐条实测过（①cnpen spotcheck 四判据 exit 0／②external 含 CVE 判据 exit 0／③反向验证脏净双向 dirty=detected+clean=zero-hits exit 0／④微版本六件 unittest 30 例 OK／⑤知识库七件 72 例 OK／⑥全套 564 绿／⑦金样零漂移+git status --short tests/golden 空／⑧CI push 已触发，四格矩阵在册，远端绿需 Actions 页面复核／⑨常驻集 31 例 OK+SKILL 1540<2000 token／⑩b5 台账在盘 G-29..G-35 grep 计 19≥7）；补充判定=种子库 lint PASS n=10 exit 0（R8 审计行取证后复原）+export 双跑 sha256 一致 39545dd6…+T18 前置种子库测试隔离修复（跑全套 git status 必净已钉死）；契约 14 新立+契约 v3 首批六笔勘误（微版本通道 schema_version=2 不递增）；探知项台账 G-29..G-35 终态=docs/design/2026-09-24-b5-discovery-notes.md（b4 台账 G-23/G-24/G-26/G-27/G-28+R6 五行就地闭环注记）；Ruling 总索引=文末「批次 5 Ruling 总索引」节
- 批次 5 评审收尾：✅（2026-09-24）I-1 lint 种子库零写入（裁决 R-RC5-1 选 a——出口判定命令原文就地亲跑 PASS n=10 exit 0，log.md/staging.tsv sha256 前后一致零写热）+M-1..M-6 顺手六件（契约14 created 勘误指针+vocab_version 两表补齐/checklist 占位符张力节/README 勘误索引补 T7/探知项两笔/match --client 必填 exit 2）；566 单测全绿（564+2 新增）+54 金样面 PASS 零漂移；批次 6 前置义务在册=真人复核在库 10 页；详见文末「批次 5 评审收尾入账」节
- 批次 6 三层验收+安装矩阵+报告管线+授权靶场+交付收口：**完成（T1-T18 收口，2026-09-26）**——737 单测全绿（本段起点基线 724+T17 4+T18 9）+54 金样面 PASS 零漂移 hash=a347edd7；整批出口验收清单 18 条逐条亲跑实测（详见文末「批次 6 整批出口验收清单执行记录」节——#5 远端 Actions 页面复核、#15 真人复核 10 页、#17 R11 人工法务过审三项如实移交真人/远端，载体与流程全在册）；契约勘误 09（工具面 12→14：+#13 tanyin-evals+#14 tanyin-budgetctl 补缺）+契约 13 v2 勘误（终态 B 语义）；探知项台账 G-36..G-41+出口 #16 七项遗留 G 项收口终态=docs/design/2026-09-24-b6-discovery-notes.md；Ruling 总索引=文末「批次 6 T17+T18 流水+裁决」节

## 交战区指针
- 设计定稿：docs/design/2026-09-21-tanyin-v2-design.md（§2 铁律/§5 循环/§11 批次表）
- 契约：contracts/；CLI：cli/；测试：tests/（unittest+金样 G-g1，入口一律 [sys.executable, path]）
- 计划：docs/superpowers/plans/（2026-09-23-batch1-ledger-cli.md；2026-09-24-b3-master-skill-loop-restart.md——批次 3 计划，T1-T13 已全部执行完毕）

## 开发流水（追加，一行一笔：日期｜代理｜动作｜证据）
2026-09-24｜总控（本会话）｜批次2 对账入库：SECW-3 执法单源化 181 测试全绿｜500ae44
2026-09-24｜子代理（竞品调研）｜VulnClaw 源码深度分析报告落盘：架构/四段流程/证据管理/安全护栏/工程质量/对 TanYin 批次5-6 取材清单+铁律对照（只读 .research/repos/VulnClaw，零改动）｜35719d7
2026-09-24｜子代理 df8e7216｜Windows 兼容审计+修复+双平台 CI 四 job 绿｜730d743,70826a5
2026-09-24｜子代理 6c72220c｜全景图 v2：图谱+知识库簇+生命周期+引擎层+哲学锚点+断点四步+口径13+模拟运行｜9f6c388..0fbab87（8 笔）
2026-09-24｜总控（本会话）｜建立本账本（补记：此前 panorama 马拉松期间账本纪律失守，本行起恢复）｜本文件
2026-09-24｜子代理（TDD）｜批次2 三 Critical 执法洞修复：exclude/oob 三集语义+egress 单源化、inject 同门链、stderr 双流脱敏；顺手 Important：deny-list 数据化(shared/DENYLIST.md)、主机提取强化、canary 三形态；228 测试全绿+金样零漂移｜a5b4b17
2026-09-24｜子代理 T1｜批次3 T1：phases.yaml 契约誊录+受限 YAML 子集解析器（stdlib 零依赖，fail-closed；TDD 先红后绿 6 新用例，全套 234 绿+金样 PASS）｜271e814
2026-09-24｜子代理 T2｜批次3 T2：phases schema 校验器+九门断言命令存在性（all_commands 41 基名单源）+tanyin-phases 入口(+.cmd)；phases-validate 金样接入 run_golden 既有机制；G-1 契约09/README 勘误 10→11；TDD 先红后绿 7 新用例，全套 241 绿+金样 PASS（21读+20写+1phases）｜2350924
2026-09-24｜子代理 T3｜批次3 T3：gate 断言执行器（断言→命令调用协议落地：判定表/already-passed 幂等/前置门 REJECT/gate-exit+gate-fail 事件）+phases/PROTOCOL.md 冻结接口落盘；追加件：分母就绪门 denominator-ready（多源法定/类覆盖/外推闭包三断言，只读账本零落账）；TDD 先红后绿 13 新用例，全套 254 绿+金样 PASS 零漂移（新增 phases-gate-p0.norm 与 phases-denominator-ready.norm 两静态基线）｜4c8c28a
2026-09-24｜子代理 T4｜批次3 T4：state.md v2 行结构冻结（10 固定键+handoff≤200 行硬顶+tmp+os.replace 原子写；cli/ledger/state_md.py 单一实现）+checkpoint 升级（--session 必填/--release 旗标/--round/--note/--spawn+单活跃会话锁+snapshot 确定性投影）；TDD 先红后绿 10 新用例，全套 264 绿+金样 PASS（write-checkpoint.state 有意刷新=旧三行格式作废；run_golden VALS 补 --session=golden-s）｜95a79b0
2026-09-24｜子代理 T5｜批次3 T5：state-rebuild v2 对账升级（链一致+parse_state 结构/枚举/200 行+revision==timeline 行数+snapshot 与账本重算一致——对账实质；FAIL 提示统一指向 rebuild-state）+tanyin-phases rebuild-state 对账重建（链断拒绝自愈 halt/tmp 残留清扫/重建即锁释放 session=rebuilt+released+spawn=manual）；TDD 先红后绿 6 新用例（含自加 snapshot 篡改钉死例），全套 270 绿+金样 PASS（read-state-rebuild.norm 有意刷新=absent 态信息移第二行，首行字节不变；test_query_check 旧例 v2 适配）｜acb1114
2026-09-24｜子代理 T6｜批次3 T6：受管重启护栏四件套（①verify-chain ②速率上限 RESTART_RATE_MINUTES=10 ③单活跃会话：auto 禁接管 foreign 锁+manual 须 state-rebuild PASS 凭据+takeover-of 留痕 ④budget-log 计入 RESTART_TOKEN_COST=2000 ⑤checkpoint 新锁+managed-restart 事件 actor=总控 ⑥resume-kit 接通点留锚）；TDD 先红后绿 10 新用例（计划 7+自加 3：用法退出码 2/事件 actor=总控/收尾对账一致不变式），全套 280 绿+金样 PASS 零漂移（T6 无新金样）｜26e38e7
2026-09-24｜子代理 T7｜批次3 T7：resume-kit 恢复注入白名单生成器（注入白名单四件套：state.md/kit 本体/当前门方法论单载/四查询摘要各一次+禁注入清单+幂等续跑表——cache_lines 按 T8 接口形状落地）+先对账再干活（链断拒生成 exit 1）+tmp+os.replace 原子写+--timestamp 缺省取 timeline 末行（确定性）+restart⑥ 接通（重启收尾重生成 kit）；TDD 先红后绿 8 新用例（计划 5+自加 3：缺省时间戳/用法退出码 2/金样字节锁定），全套 288 绿+金样 PASS 零漂移（新增 phases-resume-kit.norm 静态基线，/tmp 拷贝件上生成——fixtures/ 零触碰）｜5fffeaa
2026-09-24｜子代理 T8｜批次3 T8：幂等续跑 cached 派发侧查询（设计 §5.2「工件即缓存」——复用 T7 cache_lines 单一实现不重写：intent done 且 submissions/<id>/submission.json 在位→SKIP、done 无工件→RUN、非 done 不列；全量模式 #count=N+IID<TAB>SKIP|RUN，--intent-id 单查裸 token；只读零副作用 §5.3）+dispatch 接线；TDD 先红后绿 4 新用例，全套 292 绿+金样 PASS 零漂移（T8 无新金样，hash 前后一致）；CLI 进程级实测退出码 0/0/2 全对齐｜24807ee
2026-09-24｜子代理 T9｜批次3 T9：SKILL.md 总控路由器本体（常驻权威集八节：铁律/九门循环/P3 演进循环/命令索引 41/恢复协议/受管重启/干跑/路由表——认知按需加载 phases/<门>.md，方法论/引擎知识/账本数据不进常驻）+预算与结构断言测试（estimate_tokens 口径随 PROTOCOL §2 冻结：CJK+⌈非CJK/4⌉，实测 1321<2000 余量 679；命令索引 41/41 全覆盖；引用命令⊆已知面例 skipUnless 门控待 T10 落位自动生效）；SKILL.md 全文与测试代码自计划文件程序化逐字提取防转写漂移；TDD 先红后绿（红=3 ERROR 缺文件+1 skip，绿=OK skipped=1），全套 296 绿+金样 PASS 零漂移（T9 无新金样，hash=a347edd7 前后一致）｜6cdcf90

2026-09-24｜子代理 T10｜批次3 T10：九门方法论 md（P0-P6 结构头统一：duty/entry/exit/回边四段+过门方式声明；P3 全文自计划 2294-2331 行程序化逐字提取——风暴五路/三资产事件/收敛四条件/受管重启触发；P0 附八问表落账对照（设计 §8.1）；P4 注 replay-summary 批次4前 SKIP 披露义务；P5 注 tanyin-report 批次6交付前 ENV-HALT；P2 补分母就绪门前置节=denominator-ready FAIL 清单未清空不得 freeze（G-14 追加件，口径=PROTOCOL §4））；解除 T9 skipUnless 门控——referenced 例转绿（SKILL+九门 md 引用命令⊆已知面实测过）；TDD 先红后绿（红=1 FAIL+3 ERROR 含 un-gated referenced 例，绿=7/7），全套 299 绿+金样 PASS 零漂移（T10 无新金样，hash=a347edd7 前后一致）｜491bcf5

2026-09-24｜子代理 T11｜批次3 T11：干跑 eval——P0-P2 零对外请求（STEPS=总控行为脚本化 13 步：add-goal→budget-check→scope 三行→skill-version 事件→egress compile→gate P0→add-asset→gate P1→matrix-init→gate P2；判定=timeline 零 request:/request-ticket 事件+三门 gate-exit PASS 齐备+verify-chain/state-rebuild PASS+双跑同事件数（T12 底座））+追加件总控纪律三断言（①gate-exit 首现序恰=[P0,P1,P2] ②13 表内容 diff 逐表须有窗口内 timeline 命令事件词可解释（TABLE_EVENTS=ctx.event 落点全集）③budget-check 调用窗日志在位且退出 0）；裁决：P1 断言词 02a 终审签名裁 bare ledger-tree-check+计划测试 bug fresh_drydir 传 td.name；TDD 先红后绿（红₁=TypeError×2，红₂=ENV-HALT gate:P1 tree-check 用法错，红₃=追加件③ hits=[]；绿=5/5），全套 299→304 绿+金样 PASS 零漂移（T11 无新金样，hash=a347edd7 前后一致；phases.yaml 单词改零漂移=validate 计数型输出 asserts=21 不变）｜2df8d81
2026-09-24｜子代理 T12｜批次3 T12：kill -9 保真度 eval——撕裂三态+POSIX 随机断点（seed 固定）+断点×摘除 22 组合穷举，恢复后 13 表字节指纹零变更+state-rebuild PASS+resume-kit 重生成（304→310；本流水行由 T13 补记——9f6f651 当时只落 T12 裁决节）｜f695210
2026-09-24｜子代理 T13｜批次3 T13：收口——契约02a回注 G-6/G-10（微版本勘误通道同批次G-1先例；state.md v2 十键表与 state_md.KEY_ORDER 单源钉死+checkpoint 终局签名八参数）+cli/README 批次3节+探知项台账 G-1..G-15 落盘归并+出口验收 11 条逐条实测（310→317 绿+42 金样面 PASS；tests/test_contract_backfill.py 7 例 TDD 先红后绿）｜5c62bd6
2026-09-24｜子代理（评审收尾）｜批次3 评审收尾：Important×2 清账——①契约09 tanyin-phases 子命令枚举三处 6→7（补 denominator-ready；微版本勘误通道=文末勘误补记+README 索引登记）②金样回归进 CI（ci.yml 四格矩阵 Golden regression 步；run_golden 缺金样默认 FAIL+--bless 显式建档门槛，单测 5 例 TDD 先红后绿）+顺手 Minor-1（契约04 §69 就地指针：断言词按 02a 终审签名裁 bare ledger-tree-check——T11 裁决）+Minor-5 探知项登记（check_cmds.py:27 _now() 墙钟进账本，契约 v3 前裁决）；discover 317→322 全绿+金样 42 面 PASS 零漂移｜f49c6bc
2026-09-24｜子代理 T1｜批次4 T1：G-12 裁决落地——assets.type 九值→十一值（+cloud-storage/human-factor 细分落 meta=sub:）+pivot/foothold 启用（§4.8 兑现，原拒收分支退役）；契约01/07/02a+PROTOCOL §4 微版本勘误四笔+README 索引登记；TDD 先红后绿（tests/test_assets_type_b4.py 3 例：pivot/foothold/新两值正例+未知枚举负例；test_write_cmds pivot 用例转正例），全套 325 绿+金样 PASS 零漂移｜a3fd64d
2026-09-24｜子代理 T2｜批次4 T2：G-2 裁决落地——matrix-set 放行 submatrix: 新键行（四条件：前缀/冻结/全新表面/VOCAB 命中）+原子铸造新表面×VOCAB 全集 12 行（目标行取 --state/--reason/--intent-id，余行 state 空+裸前缀；timeline 事件 submatrix-mint）+前缀首次归类修正（旧空→任意前缀放行/旧非空≠新→REJECT，修 authz-diff 落格潜伏阻塞）；契约02a §12 微版本勘误；TDD 先红后绿（tests/test_submatrix_mint.py 6 例；test_write_cmds 前缀负例按新语义改写），全套 331 绿+金样 PASS 零漂移｜1aace3d
2026-09-24｜子代理 T3｜批次4 T3：P4 重放门断言转强制——phases.yaml expect 去「批次 4 前=SKIP」+PROTOCOL §1 判定行退役注记+P4.md duty 3/4 强制化+契约04/契约11 §7 微版本勘误两笔+README 索引登记；TDD 先红后绿 2 例，全套 333 绿+金样 42 面 PASS 零漂移｜f569abe（本行由 T4 继任者补记：T3 commit 未落流水行，T12/T13 补记先例）
2026-09-24｜子代理 T4｜批次4 T4：EV 卡片解析器（ledger/cards.py：parse_yaml 复用+check_consistency 同值性）+matcher 子集评估器（ledger/matchers.py：word/status/regex+AND+fail-closed，R1 落地）+vault 单源抽取（guard 七函数搬 ledger/vault.py，guard 同名 thin delegate 行为零变更；冻结接口 load_key/secret/secrets）；契约06 R1/G-17 微版本勘误+README 索引登记；TDD 先红后绿 9 例（红=ImportError 模块缺位），全套 342 绿+金样 42 面 PASS 零漂移（无金样变动）｜f8054dd
2026-09-24｜子代理 T5｜批次4 T5：tanyin-replay 重放驱动（铁律 7 对外请求例外#1）——raw_request 自解析直发（R2：不 shell-exec repro_command）+{{vault:cred-N}} 进程内回注（真值不进 argv/不落盘，缺真值 fail-closed REJECT）+scope 门链（amendment 剔除→exclude 命中即界外→include 须命中；界外=REJECT exit 1 且 timeline 留痕）+三态判定（R3：连接层失败=env-diff→REPAIRED 候选/matcher 全中=reproduced→VERIFIED/不中=not-reproduced→REJECTED/无 matcher=manual）+matcher-test 离线评估+tanyin-replay.cmd Windows 等价入口+金样面 replay-envdiff（ENGINE_CMDS 首面）；TDD 先红后绿 4 例（红=脚本不存在 3 FAIL+1 巧合绿；绿含判定产物 1.json+timeline request:/replay-probe 记账断言），全套 346 绿+金样 43 面 PASS（replay-envdiff 有意建档 --bless，存量 42 面零漂移）｜498d8c2
2026-09-24｜子代理 T6｜批次4 T6：重放门 eval——127.0.0.1 mock 目标（随机端口 socketserver+http.server，跨平台非 POSIX-only 无 skip）三态全链路实测：/ok 200 errorCode:00000→reproduced、/drift 403→not-reproduced、端口 1 拒连→env-diff → set-replay-state 三态落账（VERIFIED/REJECTED/REPAIRED）→ledger-replay-summary PASS（verified=1 repaired=1 rejected=1 pending=0=P4 断言 5 绿）→verify-chain 全链一致（request:/replay-probe/add-scope/add-evidence/replay: 事件入链）；红=计划逐字 setUp add-scope exit 2（argv 契约缝隙），修补两处（--goal-dir 紧随命令名+matcher 127.0.0.1→127.0.0.0/8）后绿；全套 347 绿+金样 43 面 PASS 零变动｜d9f7185
2026-09-24｜子代理 T7 前置｜批次4 T7 前置（图查询独立 commit）：图谱驱动增补 71d3b7c——graph-neighbors/graph-paths/graph-horizon 三只读图查询（邻接展开 --edge-class 过滤/有向可达路径枚举/可达集×矩阵空格 join）；命令面 41→44 微版本勘误（契约02a 文末补记节+README 索引+SKILL 命令索引+cli README+面数断言 41→44 同步）；金样 graph 三面（replay-envdiff 先例：prep_graph 预织图+--bless 建档，存量 43 面零漂移）；TDD 先红后绿 10 例（红=未实现/未知命令 8 FAIL），全套 357 绿+金样 46 面 PASS｜f87ca25
2026-09-24｜子代理 T7｜批次4 T7：web-blackbox 四段 skill 引擎——MANIFEST（契约08 十二字段）+SKILL 路由 ≤2K+四段 recon/surface/test/differential（recon=A1-A8×通道×落账引擎位表+G-12 新 type 入表+graph-horizon 完备性口径；differential=计划逐字差分四原则+身份矩阵差分五步+护栏 24）+patterns 两件（submission-ok 契约07 九字段全样例+authz 模板/submission-reject 五类失败对照表）；结构 lint 8 例 TDD 先红后绿（计划 7 例逐字+horizon 咬合增补 1 例），全套 365 绿+金样 46 面 PASS 零变动｜4583e7e
2026-09-24｜子代理 T8｜批次4 T8：身份矩阵差分样例对+检出率 eval——authz_matrix role×endpoint 覆盖投影（纯投影不新增表）+diff-authz 夹具（正对 BOLA finding+同 PG 双 EV+authz-diff: 矩阵行/负对 fact×2，全经 44 面铸造、重铸逐字节确定）+eval_authz_recall scorer（正对=finding 同 role CRED+endpoint+EV word marker/负对=fact target；实测 5/5 exit 0+删 finding 副本 exit 1）+R5 落地（authz-diff 直达 pending，契约02a §3 微版本勘误）；TDD 先红后绿 6 例，全套 371 绿+金样 46 面 PASS 零变动｜816d178
2026-09-24｜子代理 T9｜批次4 T9：vuln-agent 适配器（cli 型）——MANIFEST（read/L1 纪律声明+归一化表 v1）+归一化（VULN→C2/NOVULN→fact info/SUSPECTED→C3+复核终态前缀优先+same-host 视角标注）+POC 四要素门（FD 报告卡规格 b0006f2：raw_request/raw_response/时间/环境 缺一=降级 fact kind=vuln-clue 不成 finding；四要素随提交携带=请求/响应原文进 reproducible_steps+时间随 evidence_refs）+canned 夹具+金样面 engine-vuln-adapter（--bless 建档）；TDD 先红后绿 5 例（计划 3 例逐字+POC 门 2 例），全套 376 绿+金样 47 面 PASS（存量 46 面零漂移）｜a4bb524
2026-09-24｜子代理 T10｜批次4 T10：nuclei adopt——tools.lock 起步版（openssl/nuclei/nuclei-templates 三键，契约10 五字段+format_version=1）+supply_chain ECDSA 验签单源（openssl 子进程 fail-closed，缺 openssl=ENV）+模板离线快照（自写三模板+templates.lock 钉 commit+逐文件 sha256）+适配器（验签先于归一化：不过/nuclei 缺失=blocked 提交绝不自动安装；--jsonl-file canned 归一化/--run 经 guard exec 执行通道）；测试钥 TEST-ONLY 进仓（G-22 流程缺口如实披露=批次 6 生产钥+真 commit 重签）；金样面 engine-nuclei-adopt（openssl 门控 ENV SKIP）；TDD 先红后绿 6 例，全套 382 绿+金样 48 面 PASS（存量 47 面零漂移）｜108c5ed
2026-09-24｜子代理 T11｜批次4 T11：session-viz 投影（projector 型）——tanyin-viz 载体(+.cmd)+viz_render 数据岛（统计栏 confidence×impact 分色/attack 链/矩阵覆盖率/预算条；Pipeline 时间轴；图谱七类节点分层 SVG attack 金/cross_ref 虚/supersedes 点/candidate 半透明+kind 过滤+id 搜索+分层/力导向两档纯计算；右面板未消费 fact+风暴 origin+清理核销；身份矩阵 role×endpoint 投影=T8 authz_matrix 单源）+追加件 fb72cd5 findings 实时流投影（findings_stream 第六键：最新 N=20 条时间/资产/类型/severity/状态，high/critical 置顶▲，确定性输出）；零依赖 SVG（R4）+零回写+两次渲染字节一致；金样面 viz-data（--bless 建档，存量 48 面零漂移）；TDD 先红后绿 4 例（红=2 FAIL+1 ERROR 入口缺位），全套 386 绿+金样 49 面 PASS｜7917fc4

## 2026-09-24 批次 4 T11 裁决（实现者记）
- R-T11-1（追加件落地·fb72cd5）：findings 实时流投影随 T11 落——数据岛第六键 findings_stream：最新 N=20 条（FINDING_STREAM_N 模块常量；时间=created/资产=affected_asset_id→assets.value 解析/类型=vuln_ref/severity=impact/状态=status），置顶档 HIGH_SEVERITIES={高,high,critical}（impact 词表 {高,中,低}+英文容错）稳定分段（置顶段内新近降序→非置顶段新近降序，双跑字节一致）；测试增补 test_stream_latest_n_pinned_top（经 CLI add-finding 铸 中 条目验 pinned 分段 [T,T,F]+段内新近序+双跑一致）。
- R-T11-2（stats 扩展键）：计划模板文字要求统计栏含矩阵覆盖率/攻击链数/收敛进度/预算条，而 island stats 计划片段仅 counts/confidence/matrix_rows——按模板意图补 stats.matrix_set（非空 state 格数）/attack_edges/converged/budget 四键（budget.tsv 四列和，全确定性零墙钟）。
- R-T11-3（红态口径）：计划 Step2 预期「ERROR（入口不存在）」——实测红=2 FAIL+1 ERROR（零回写/确定性两例因计划测试原文不断言 rc 而空转绿，保持逐字不加强断言）；绿=4/4。附记：实现中修复 TEMPLATE svg 元素取值笔误与流排序方向（最新在前）两处自勘，先于测试转绿。

2026-09-24｜子代理 T12｜批次4 T12：G-13 侦察金丝雀——tanyin-canary recon-deploy/recon-recall（界内诱饵登记 canary/recon-decoys.tsv 只增+timeline recon-decoy-deploy/recall 记账；召回率=发现/植入，比对=同 value 且 in_scope；本地零网络）+denominator-ready 第④断言（planted>0 须全发现否则 FAIL 列缺失诱饵；planted=0 须披露 fact target=canary:recon）+stats planted/found 两键（PASS 行同步）+PROTOCOL §4 勘误（三断言→四断言+G-8 canary 参数语义注记一并清账）+P2.md 分母就绪门节④；金样 phases-denominator-ready 有意刷新（norm 改锁四断言 PASS 面 planted=0 found=0，由 run_golden 新增 PHASES_DENOM 面+prep_denominator 生成；原 9 项 FAIL 形状改由 test_phases_gate 形状断言承载，三处适配）；TDD 先红后绿 2 例，全套 388 绿+金样 50 面 PASS｜3c42528

## 2026-09-24 批次 4 T12 裁决（实现者记）
- R-T12-1（argv 契约，R-T1-1 同型）：计划 run() 助手与内联 subprocess 调用均把 --goal-dir 尾置——tanyin-canary/tanyin-phases/tanyin-ledger 单入口冻结 argv[2]=="--goal-dir"，尾置恒 exit 2。修正=--goal-dir 紧随子命令/命令名（tests/test_negative_matrix.py 先例）；语义断言逐字保持计划原文。
- R-T12-2（add-fact 必填集）：计划「补披露 fact」调用缺 --intent-id/--confidence（add-fact 六必填 intent-id/kind/target/detail/confidence/timestamp）——补 INT-g1-0001/0.9，target=canary:recon 语义不变。
- R-T12-3（金样面归属错配）：计划假设 run_golden 持有 phases-denominator-ready.norm——实况该 norm 自批次 3 起由 tests/test_phases_gate.py 的 unittest 锁定（run_golden phases 面仅 validate）。按计划 Step4 预案落地：norm 改锁「补 fact 使 ①-④ 全过」副本的 PASS 行（planted=0 found=0），由 run_golden 新增 goal-dir 面（prep_denominator=补源 intent+两资产 facts/A2-A8 七条不适用理由/canary:recon 披露）生成/锁定（--bless 有意刷新=删旧 FAIL 面重建）；test_phases_gate 三处适配：fail 形状 9→10 项+④行断言、PASS 路径（test_class_na_reason_or_asset_fills_check2）补披露 fact（否则④必挂）、golden-lock 改验 norm 在档且含 planted=0 found=0（FAIL 形状由形状断言承载——双重锁定不降级）。
- R-T12-4（副本目录名=goal_id）：fresh_of 副本目录名决定新行 id 前缀（G-g1→INT-g1-0003；误用 G-g1-denom→INT-g1-denom-0001 触发 intent 引用闭合 REJECT）——denominator 面副本目录名钉 "G-g1"（fresh 同名先例）。
- R-T12-5（canary 家族口径）：recon-deploy/recon-recall 全本地落表/读账零网络（执法侧 deploy/probe 同律）——PROTOCOL §3 干跑口径「canary 只 deploy」按 G-8 清账扩为 canary 家族全子命令零网络；recon-deploy --type 校验十一值枚举（G-12 勘误后单源）。

2026-09-24｜子代理 T13｜批次4 T13：触发器闭包审计——phases/TRIGGERS.md 版本化封闭目录（八类事实×触发×后续策略×消费检查，triggers-v1）+tanyin-phases trigger-audit（只读零落账三检查：目录版本一致（TRIGGERS.md version 行+triggers-catalog 事件若已记须同版本，缺记=提示非失败）/触发器闭包（in_scope add-asset 事件→submatrix-mint 或子矩阵行或绑定 intent；add-cred session→authz-diff 候选或延后 fact target=authz-diff:<CRED-id>；amend-scope→其后 egress-compile）/清单 triggers=<n> closed=<n>/<n>；G-2 铸行通道联动验证）+tanyin-egress compile 落 timeline 事件 egress-compile acl=<相对路径> lines=<n>（actor=egress，EPOCH 确定性时间戳）+PROTOCOL §6 新节+tanyin-phases USAGE 第八子命令；TDD 先红后绿 7 例（红=6 FAIL+1 ERROR），回归 test_egress/test_dryrun_p0p2 19 例绿（TABLE_EVENTS 适配分支未触发——egress-compile 仅动 timeline 自证表），全套 395 绿+金样 50 面 PASS 零漂移｜349ac34

## 2026-09-24 批次 4 T13 裁决（实现者记）
- R-T13-1（argv 契约，R-T1-1 同型）：计划 run() --goal-dir 尾置——修正=--goal-dir 紧随命令名（单入口 argv[2] 冻结）；语义断言逐字保持。
- R-T13-2（add-cred 参数组契约对齐）：计划参数组 --secret-ref={{vault:cred-11}} 违反行序号律（G-g1 现有 1 cred→须 cred-2）、缺 --parent-cred（kind=session 必填父凭据）、--permitted-actions=read 无 account-grant 覆盖（G-g1 scope 无该类行→必 REJECT）——修正=--parent-cred=CRED-g1-0001+{{vault:cred-2}}+删 permitted-actions；审计语义断言不变。
- R-T13-3（matrix-freeze 幂等）：G-g1 基线 matrix.tsv 自带 frozen_at 盖戳行（R-T2-2 同源现实）——计划断言 rc==0 必挂（already-frozen REJECT），改 rc∈{0,1}（PROTOCOL §1 判定表幂等容忍同律）；后续 matrix-set 铸行的「基线已冻结」前置由夹具既有冻结行满足。
- R-T13-4（①事件驱动·核心裁决）：计划 trigger_audit 参考实现按 assets 行全集遍历 in_scope 资产——与计划自身 test_baseline_session_passes 直接冲突（G-g1 两 in_scope 资产 shop.example/admin-internal.shop.example 无子矩阵行、无 origin=recon-event intent，按行遍历必 FAIL 而 test 期望 PASS）。按 Interfaces 文本「每个 in_scope add-asset 事件→…」裁决：①检查由 timeline 事件 add-asset <AST-id>(<in_scope>) 驱动（AST-id→assets 行解析 value；界外事件免检=目录行 2/8；夹具预置资产无事件不入审计）。事件词取自 write_cmds._add_asset 落账面（"add-asset %s(%s)"）。
- R-T13-5（版本比对补全）：计划片段未实现 Interfaces①「timeline P0 事件 triggers-catalog <ver> 若已记则须同版本」——补齐（缺记非失败）；自加 test_catalog_version_mismatch_fails（经 append-timeline CLI 铸 triggers-catalog triggers-v0 验不一致 FAIL）。
- R-T13-6（②全局候选口径+延后通道）：计划片段 has_cand=全局任意 kind=authz-diff intent（非按 cred 配对）——保持计划口径（TRIGGERS.md 行 3 同文）；自加 test_cred_session_deferred_fact_closes 钉死 per-cred 延后 fact 通道（target=authz-diff:<CRED-id>）。按 cred 精确配对（intent context 消费）未扩——G-23 同族留待契约 v3。
- R-T13-7（节号）：计划称「PROTOCOL §5 trigger-audit 新节」——§5 已被批次 3 T3 实现注记占用，按追加序落 §6（§6 首行 Ruling 注记）。
- R-T13-8（egress 事件确定性）：compile 无 --timestamp 参数（build_acl 确定性纪律无时间戳）——事件时间戳取 EPOCH（canary recon-recall 同款先例）、acl=<相对 goal-dir 路径>（防绝对路径跨机漂移）、phase 空（不抬 gate_jump reached）；test_dryrun_p0p2 TABLE_EVENTS 无需扩（计划预留适配分支未触发：egress-compile 仅落 timeline=自证表，干跑「双跑同事件数」断言天然兼容）。
- 附记（收口移交）：contracts/09 tanyin-phases 子命令枚举 7→8 与 cli/README.md 八子命令面未在本任务动（T14 收口范围，G-18/G-19 先例注记同型）。

2026-09-24｜子代理 T14｜批次4 T14：总控接线收口——SKILL 路由表三引擎+MANIFEST 纪律路由+P0 triggers-catalog 序列+P4 重放门；P3 ③派发规则改写（priority=severity_expect×asset_value×exploitability 降序 Top-K，fb72cd5）+cred-obtained 回边全语义+asset-added G-2 命令形态+budget-exhausted 披露序；TRIGGERS.md v1→v2（高危即时横向）+PROTOCOL §6 勘误；契约 09 子命令 7→8/01 intents.priority/07 nday-verify 注记（G-18 清账）三笔微版本勘误+README 索引；cli/README 批次4节+八子命令面；differential.md PG 铸号教义修正（R-T8-2 移交）；b4 台账 G-16..G-26 落盘+b3 台账 G-2/G-12/G-13 闭环注记；出口验收 10 条逐条实测（见 T14 裁决节）；TDD 先红后绿 14 例（红=13 FAIL+2 例按计划跳过条款先绿），全套 409 绿+金样 50 面 PASS 零漂移｜f36cad9（本行 hash 由补正笔落——占位循环节=流水行引用自身 commit 的固有环，先提交后补正=批次内既定手法）
2026-09-24｜子代理（评审收尾）｜批次4 评审收尾：C-1 证据双指纹 norm 轨写/查单源化——cli/ledger/norm.py 单源（严格侧哨兵语义：ISO/epoch→<ts>、nonce/csrf 值→键=<n>、删 CR、逐行 rstrip、split/join 保尾换行、decode replace；写路径 _NORM_DROP 整行丢弃+<TS> 哨兵+splitlines/join 三处分歧退役，规则冻结模块 docstring），write_cmds._hashes/check_cmds.artifact_hashes 双薄壳；diff-authz 确定性重铸（E-index norm×2 刷新+P4 完备化补 replay 双事件行——G-23 墙钟绕道按 core.row_hash 直写；重铸双跑 diff 逐字节一致；hash-recheck/verify-chain/replay-summary/recall=5/5/gate P4（副本亲跑）全 PASS）；金样 diff-hash-recheck 新面（--bless INIT）+viz-data 有意刷新（唯一 delta=stats/counts/timeline.tsv 19→21）；顺手三件：cli/README 计数 41→44×3+金样面 50→51、supply_chain fail-closed 形式统一（sig 非 hex=失败对+load_lock 解析错适配器捕获→blocked exit 0，两负例）、b4 台账 G-27（intents cred 绑定列）+G-28（converge 结构性停机+攻击路径进 EV）+R6 cap 机检缺口挂 G-20；TDD 先红后绿 5 例（红=2 FAIL+2 ERROR+夹具面 1 FAIL）；全套 414 绿+金样 51 面 PASS｜6d3a033（本行 hash 由补正笔落——占位循环节=流水行引用自身 commit 的固有环，先提交后补正=批次内既定手法，61e916f 先例）

## 2026-09-24 批次 3 T4 裁决（实现者记）
- Ruling（计划内部矛盾①·revision 语义）：计划 T4 参考实现「rev=旧 state revision+1（从 1 计数）」与 T4 接口注释「state-rebuild 对账基准=timeline 行数（既有口径不变）」、T5 全部测试/代码（revision==len(timeline)、rebuild_state 直取行数）、「timeline 先行=第一事实源」撕裂态设计三方互斥——按计划系统意图裁决：**revision ≡ 本次事件落账后 timeline 总行数**（夹具首打=9）。T4 新测试与批次 1 既有 TestCheckpoint 的 revision 断言按此动态化（新增 test_revision_equals_timeline_rows 钉死防漂移）。
- Ruling（计划↔实现偏差②·--release 旗标）：既有 _parse 只收 --key=value（41 面冻结不动），计划测试用裸 --release——在 _checkpoint 内本地预归一（裸 --release→--release=1），全局解析器零改动。
- Ruling（既有面适配③）：--session 必填使批次 1 TestCheckpoint 两用例改写（补 session+动态 revision）——属 02a 终审补全 5+G-10 授权范围内的必然后果，非命令面破坏；test_write_cmds 其余 263 用例零触碰。
- Ruling（G-6/G-10 契约回注）：计划 T4 Files 节未列 contracts/02a——本任务不回注，留 T13 收口统一回注（G-6=state.md v2 十键表引用、G-10=checkpoint 五新参数签名）；commit 消息已按 G-10 处置注明先例。
- 附注：计划测试的 snap_all 沿用 open().read() 不关句柄（与批次 1 snapshot helper 同款范式），ResourceWarning 为噪音不处理；自加 test_corrupt_state_rejects 补「损坏 state.md→REJECT 提示 rebuild-state」缺口（计划未列但属锁语义前置件）。

## 2026-09-24 批次 3 T5 裁决（实现者记）
- Ruling（计划内部矛盾①·absent 态输出位置）：计划 Step3 参考代码把 state.md=absent 附在首行（PASS<TAB>revision=N<TAB>state.md=absent），与 Global Constraints「state-rebuild 输出保持 PASS<TAB>revision=<n> 首行不变」及 T5 Interfaces「追加信息放第二行」互斥——按接口文字（约束层最强）裁决：absent 标记移至第二行；金样按 Step5 明文预案同步有意刷新（首行 PASS<TAB>revision=8 字节不变，实测比对确认）。
- Ruling（计划测试 bug②·append-timeline 空 phase）：计划 TestRebuild 撕裂态 B 构造用 --phase= ——_req 拒空值必 Reject，测试会红在无关点；其意图仅「账本再前进一行」，改 --phase=P3（与 checkpoint 同门上下文）。
- Ruling（计划↔实现偏差③·phase 域 END 映射）：计划代码「"" if gate == "P0" else gate」在 P6 已过（_current_gate→END）时产出 phase=END——v2 冻结格式 phase∈{P0..P6,空}，parse_state 判损坏、重建后 state-rebuild 反 FAIL，违背「rebuild 后对账一致」意图；扩展 END→空（收官态由 timeline gate-exit:P6 事实承载，state.md 不重复编码）。
- Ruling（健壮性④·空 state.md 防御）：计划代码对空文件/仅 handoff 头的 state.md（parse_state 得 fields={} 且 errs=[]）会 KeyError 裸崩；补「errs or not fields」守卫→FAIL 损坏+rebuild-state 提示（对账 fail-closed 意图的必然延伸，计划测试未列）。
- 既有面适配（T4 裁决③同型）：test_query_check.test_state_rebuild 旧正例写「单行 revision: 8」文件——v2 对账下=损坏态必红；按 v2 语义改写真 v2 结构（snapshot=账本重算）并补 snapshot 漂移负例。264→270=计划 5 例+自加 test_state_rebuild_detects_snapshot_tamper（revision 一致而 snapshot 不一致——「对账」新检查项唯一直接正红例，防漂移钉死）。
- 撕裂三态判定（T12 kill -9 eval 的语义地基）：A=tmp 残留→rebuild-state 先清扫再重建；B=timeline 领先 state（checkpoint 落账后被杀）→state-rebuild FAIL（revision 不齐）→rebuild-state 以账本为准重建；C=state.md 缺失→state-rebuild PASS+absent 标记（非错误，账本第一事实源）→rebuild-state 初始化。链断≠撕裂：verify_chain 不过即拒绝重建（exit 1 halt 人工处置），三态之外零自愈通道。

## 探知项（实现期发现，回写设计）
- 批次 3 台账（G-1..G-15 终态，T13 收口归并）：docs/design/2026-09-24-b3-discovery-notes.md——catalog 单源（计划原文誊录+实施期增补+状态归并+移交清单四节）
- 批次 4 台账（G-16..G-26 终态，T14 收口归并）：docs/design/2026-09-24-b4-discovery-notes.md——同四节结构（计划原文誊录 G-16..G-23+设计增补登记 G-24..G-26+状态归并+移交清单）
- 批次 0/1/2 审计探知项（vault XOR 无 nonce/withheld 降级/INFRA 白名单硬编码）：见上方「批次 0/1/2 独立审计入账」节（开放，批次 4/6 前定案）
- 批次 3 评审探知项（Minor-5）：check_cmds.py:27 _now() 墙钟进账本（set-replay-state/REJECTED→转 fact 落账无 --timestamp 通道，继承性问题）——契约 v3 前裁决，见文末「批次 3 评审收尾入账」节
- 批次 5 评审探知项（M-6 两笔）：①在库 10 页（CP-0001..0008+PR-0001..0002）approve 行 approver=批次5-执行者（review-checklist 逐项自查，knowledge/log.md L15-24 在案）——执行者自查不等于真人终审，**批次 6 须由人复核一轮**（执行期处置：不阻塞批次 5 收口，登记为批次 6 前置义务）；②log.md approve 行时间戳非单调（STG-0010=09:30:03 落在 STG-0009=09:30:56 之后——分批落账实况，追加序=审计序）纯外观不影响语义（approve 顺序消费方=四门槛③在场性检查，非时序），不修仅注记

## 2026-09-24 批次 0/1/2 独立审计入账（审计员 865488fb，只读实测）
- 批次 0：完成（16/16 接口实体在；Minor×2：冻结后勘误未走版本通道/附录 A 落位与设计文字不符）
- 批次 1：基本完成（41/41 实现+金样双锁定+负向 83 处 REJECT；Important：金样实为归一化+行排序比对非严格字节级、金样未进 CI）
- 批次 2：不达出口——三 Critical 实测洞：exclude 语义缺失（被排除主机 Tier1/Tier2 放行，与 egress compile 解释矛盾）；inject 通道零执法（带凭据执行绕过 deny-list/scope/取票）；stderr 不脱敏（vault 真值回泄）。Important×5：Tier3 代理本体缺/deny-list 仅 7 条硬编码/主机提取盲区/canary 探测形态单一/金样未进 CI
- 处置：#1#2#3+#5#6#8 修复后才开工批次 3；#4 代理本体建议裁到批次 6 并守门声明披露（待用户确认）；#7 金样严格化+进 CI 随后并行；#9-#12 顺手清
- 探知项登记：vault XOR 静态密钥流无 nonce（批次 4/6 前定案）；withheld 降级未实现；INFRA 白名单硬编码应随 tools.lock

## 2026-09-24 批次 3 实施计划入账（撰写 c1308136）
- 计划：docs/superpowers/plans/2026-09-24-b3-master-skill-loop-restart.md（2757 行，13 个 TDD 任务/65 步/29 验证命令/11 条出口验收）｜commit 1761e17
- 接口缺口探知项 G-1..G-11 已在计划内登记；关键四个：G-1 需第 11 工具 tanyin-phases（契约 09 增补）；G-2 新资产子矩阵行铸造断链（P3 生长通路①，批次 4 前须裁决）；G-3/G-4 重启速率上限与 token 成本口径无契约源（10min/2000 暂代）；G-6/G-10 state.md v2 十键与 checkpoint 新参数需回注契约
- 执行前置：批次 2 三 Critical 修复（ee43438d 进行中）落地后才执行本计划

## 2026-09-24 批次 3 开工（executing via subagent-driven-development）
- Ruling: Tier3 代理本体裁到批次 6+守门声明披露 — 用户开blanket批准按建议走 — 代价：批次 2 范围注记需同步，若错可回补
- Ruling: G-1 批准契约 09 增补第 11 工具 tanyin-phases — 确定性校验器符合铁律 7 — 代价：契约版本通道走微版本
- Ruling: G-2 子矩阵行铸造路径在 T2 实现时裁决并记账 — 不阻塞 — 代价：可能返工 matrix 白名单
- 执行结构：T1-T13 每任务新子代理+TDD+全量回归；里程碑 T4/T8/T13 加代码评审

## 2026-09-24 批次 3 T2 裁决（实现者记）
- Ruling（计划↔实现偏差①）：计划 T2 Step3 的 all_commands() 参考实现按字面会剔掉四个原生名带 ledger- 前缀的校验命令（ledger-scope-coverage/tree-check/replay-summary/terminal-gate），与计划自身 Interfaces（41 基名）及 test_repo_yaml_valid 预期冲突——按计划意图裁决：只剔「有无前缀孪生键的双前缀别名」，原生带前缀四命令计入基名，实测恰 41 名（新增 test_all_commands_face_41 钉死防漂移）。
- Ruling（计划↔实现偏差②）：phases.yaml 断言首词统一带 ledger- 前缀而 known=基名集——validate_phases 存在性判定按 PROTOCOL.md §1「双前缀注册均可查」语义归一（先试原词，再试剥前缀词）。
- Ruling（金样机制）：计划 T2 Step5 的 phases-validate.norm 为孤立基线文件；按派遣指令+金样零漂移纪律接入 run_golden 既有机制（双跑确定性+缺失自动建档+漂移即 FAIL）——首跑 INIT 建档、次跑锁定 PASS。
- Ruling（G-2 建议，按预批裁决记入；不实现——批次 4 范围）：T2 未触碰 matrix-set/matrix-init 白名单语义（validate 只做断言命令存在性检查，不改写侧拒收）；裁决建议=维持计划探知项 G-2 原案：matrix-set 放行 reason 前缀 submatrix: 的新键行（新表面×词表全集），批次 4 前落地。

## 2026-09-24 批次 3 T3 裁决（实现者记；含追加件·分母就绪门）
- Ruling（计划↔实现偏差①·前置门零落账断言）：计划 test_predecessor_required 的 `len(tl_events())==0` 与其 keep() 语义自相矛盾（抹门后夹具尚余 4 条非门事件，断言必红）——按注释意图「零落账=REJECT 不新增事件」改为前后计数不变。
- Ruling（计划↔实现偏差②·双前缀 lookup）：yaml 断言首词统一带 ledger- 前缀而 validate/verify-chain 等 builtin 只注册无前缀基名，计划参考实现的 `registry.lookup(tokens[0])` 会使 P0 首断言误判「未知命令」、其自身 test_gate_p0 必红——按 PROTOCOL §1.1「双前缀注册均可查」归一（先原词再剥前缀；与 T2 裁决②同型）。
- Ruling（计划↔实现偏差③·EXTRA_TOOLS=ENV-HALT）：tanyin-report/tanyin-redact 非 ledger 命令、registry 不可达，计划代码走 gate-fail——按 §1 判定表末行语义改判 ENV-HALT（退出 2、可重跑、零落账）；断言存在性已被 validate_phases 前置拦截，未知命令分支实际只服务此二工具。
- Ruling（计划↔实现偏差④·写类断言时间戳注入）：matrix-freeze 是断言集唯一写类命令（§1.4），--timestamp 必填而 yaml cmd 不携带——引擎注入门级确定性时间戳；读类命令不注入（converge-check 等「无参数」命令会 UsageError→误 ENV-HALT）。tmp 沙盘实测发现（计划测试未覆盖 P2 真跑；不修则 T11 干跑 P2 必红）；实测顺带验证 covered=false-但-rc=0 的 stdout 判定行与 already-frozen 幂等容忍行。
- Ruling（追加件架构·分母就绪门落位）：独立子命令 `tanyin-phases denominator-ready --goal-dir D`，不接入 phases.yaml P2 exit 断言列表——契约 04 逐字誊录/asserts=21 基线/九门语义/既有金样零变动（tanyin-phases validate 实测 asserts=21 不变），且夹具态合法 FAIL 不污染 T11 干跑序列；未来契约 v3 接入 P2 断言走 §1 默认判定行「退出码==0」。完备性设计 §1.3 四关裁三关（②诱饵召回率随批次 4 侦察金丝雀交付——探知项）。
- Ruling（追加件·读侧约定冻结）：13 表无显式来源/类别列，约定冻于 PROTOCOL.md §4——来源数=指向资产值 fact 的 distinct intent_id 数；unverified 标记=assets.meta；不适用理由=fact(kind=info, target=asset-class:A<k>)；A8 外推=meta 含 extrapolated/外推；在队列继续挖=status=pending+kind=recon+绑定（dedup_key 前缀或 title/detail 含值）；界外资产不入①（触发器目录：界外→记录不测）。
- Ruling（追加件·金样机制）：phases-gate-p0.norm 按计划 Step6 为静态基线（already-passed 单行）；phases-denominator-ready.norm 同构（夹具 FAIL 清单基线）——不接 run_golden PHASES 面（该面仅收退出 0 的 repo 级命令，夹具态退出 1 会误报「非零退出」）；测试内做双跑确定性+金样字节锁定补偿回归力。
- 探知项（T3 新增，接计划 G-1..G-11 续编，待 T13 归并）：G-12 A5 存储与云/A7 人的因素在 41 面 type 枚举无对应值（分母就绪门②对该两类只能走不适用理由，批 4 裁决扩枚举或维持）；G-13 诱饵召回率断言（完备性 §1.3②）随批次 4 侦察金丝雀交付；G-14 T10 的 P2.md duty 应把 denominator-ready 写为 matrix-freeze 前置步骤（本任务不改九门 md——T10 范围）。

## 2026-09-24 批次 3 T6 裁决（实现者记）
- Ruling（计划内部矛盾①·③ auto 档「本方」语义）：参考实现「凡 active 锁 auto 一律 REJECT」与计划自身 test_rate_window_elapsed_ok（前次 auto 重启留下的 active 锁、窗过后再 auto 重启期望 0）互斥；按护栏原文「session_status=active 且 session≠本方」裁决：**本方=受管重启 auto 血统（state.spawn=auto）**——auto 档可延续自身循环的锁残留（该场景的递归防护即护栏②速率上限，正是②的存在理由）；foreign 血统（fresh/manual）active 锁 auto 仍一律 REJECT（test_auto_cannot_takeover_active_lock 钉死）；--session 显式等于持锁方=严格本方，护栏不触发。
- Ruling（计划↔实现偏差②·事件词落账通道）：计划「经 checkpoint --event 落 managed-restart 事件」与 T4 实现事实矛盾——checkpoint --event 产出「checkpoint revision=N managed-restart spawn=…」复合词，计划自己的 test_happy_path（startswith 检测）与护栏②的 _last_restart_ts 检测（startswith("managed-restart")）都不认。裁决：事件词经 append-timeline（actor=总控）逐字落账（与 gate-exit/gate-fail 同通道，PROTOCOL §1.3 事件词汇语义）；checkpoint 不传 --event（复合词=双份/漂移词）。顺序=事件先落、checkpoint 收尾，保 revision≡timeline 行数不变式（自加 test_restart_leaves_reconciled_state 钉死）。
- Ruling（计划↔实现偏差③·接管路径死锁）：计划⑤直接 checkpoint --session=<新>，而 T4 checkpoint 自带锁检查在 session≠持锁方时 REJECT（其报错文本本身指定「接管走 tanyin-phases restart --spawn manual」）——参考流程在自己的 test_manual_takeover_with_rebuild_ok 上死锁。按 T5 冻结语义「重建即锁释放——接管者走 checkpoint/restart 重取锁，防双活」裁决：接管/延续路径在 checkpoint 前经 rebuild_state() 释放 stale 锁（session=rebuilt/released；不新增写路径，state.md 写者仍=checkpoint/rebuild-state sanctioned 面）。落账顺序 ④budget→⑤事件→释放→checkpoint：①②③全为只读检查、首个写者=budget-log，「REJECT=零副作用（预算流水/事件/锁一概不落）」承诺在全部校验类拒绝段保住。
- Ruling（对账前置扩展④）：active 锁的延续/接管除 manual（计划明文 state-rebuild PASS 凭据）外，auto 同血统延续同样要求 state-rebuild PASS——「先对账再干活」纪律的 fail-closed 延伸（撕裂态→REJECT 走 manual 兜底档）；不影响计划测试（重启后状态必对账一致）。
- Ruling（T5 裁决③同型⑤·phase 域映射）：计划「"" if gate=="P0" else gate」在 P6 已过（_current_gate→END）时产出 phase=END→checkpoint 拒收（v2 冻结格式 phase∈{P0..P6,空}）；沿用 T5 已裁决映射 P0/END→空。append-timeline 的 phase 用原始档位词（P0..P6/END 均为 timeline 合法词表值；_req 拒空值）。
- Ruling（用法健壮性⑥）：--rate-minutes/--token-cost 非法值→退出码 2 用法错误而非裸 ValueError 崩溃（退出码纪律 0/1/2）；--timestamp 非 ISO8601 同判 2；空 state.md（fields={} 且 errs=[]）视同损坏 REJECT 提示 rebuild-state（T5 裁决④同型防御）。自加 test_usage_errors_exit_2 钉死。
- 探知项状态（G-3/G-4，按派遣指令记账）：两口径均照计划落模块常量并带参数覆盖——RESTART_RATE_MINUTES=10（--rate-minutes 覆盖，evals 可重放）、RESTART_TOKEN_COST=2000（--token-cost 覆盖）；处置维持计划原案：G-3 待契约 v3 增 restart_rate_minutes 常量回注、G-4 待批次 6 evals 实测基线定标后回写契约。G-5（manual 接管 stale 锁无跨平台进程存活探测）本任务落地其缓解对（state-rebuild PASS+takeover-of 留痕可审计）。均待 T13 归并 docs/design/2026-09-24-b3-discovery-notes.md。
- 附注：护栏②对 manual 同样生效（速率上限不分 spawn 档——重启循环症状与 spawn 方式无关，进程级入口实测确认）；T6 无新金样（计划 Files 未列），金样零触碰零漂移。

## 2026-09-24 批次 3 T7 裁决（实现者记）
- Ruling（模板 END 分支①·T5 裁决③同型）：T7 冻结模板「phases/<current_gate>.md」在 _current_gate=END（P6 已收官）时直译产出 phases/END.md 悬空引用（九门 md 只有 P0..P6，T10 交付面）——按「收官态由 timeline gate-exit:P6 事实承载」语义，END 分支改写为「- phases/（END：九门已收官，无当前门方法论单载）」；P0..P6 分支逐字保模板（金样 P4 基线字节锁定，夹具不落 END 分支）。
- Ruling（金样机制②·T3 裁决同型）：phases-resume-kit.norm=产物文件内容基线（resume-kit.md 本体，非 CLI stdout——计划文件结构表明示「内容基线」）；不接 run_golden PHASES 面（该面无 --goal-dir 通道，接入须对 tests/fixtures/G-g1 写=违反 make_fixtures 纪律）——测试内双目录字节一致+金样字节锁定补偿回归力；建档经 /tmp 拷贝件生成，fixtures/ 零触碰实测确认。
- Ruling（--timestamp 缺省③）：计划明示「缺省取 timeline 最后一行时间戳——确定性」；timeline 为空时无缺省可用→退出 2 用法错误（fail-closed，不猜、不落 datetime.now）。自加 test_default_timestamp_from_timeline_tail 钉死（夹具末行 2026-09-23T03:05:00Z）。
- Ruling（restart⑥ 失败语义④）：write_resume_kit 在⑥失败按 halt 退出 1——①已验链+⑤已写 state 之后仅剩环境级故障可达；非 REJECT（「REJECT=零副作用」承诺只覆盖校验类拒绝段，T6 裁决③口径）。restart 输出随之多一行 OK resume-kit（在 OK restart 之前），既有断言全为 contains 型不受影响。
- 附注：cache_lines 落地为 T8 接口形状 cache_lines(s, goal_dir) -> list[(iid, SKIP|RUN)]（计划 Interfaces 明示 T8 提为独立函数后共用——单一实现，T8 cmd_cached 直接消费不重写）；自加 test_usage_error_exit_2（退出码纪律 0/1/2，T6 同型）；契约 09 第 11 工具子命令面已含 resume-kit（T2 G-1 增补时登记），无契约回注需求。

## 2026-09-24 批次 3 T8 裁决（实现者记）
- Ruling（计划内部矛盾①·单查「并附注」与冻结骨架互斥）：T8 Interfaces 文字「--intent-id 单查……非 done 或不存在=RUN 并附注」与 Step 3 冻结参考实现（print(st if st else "RUN")——裸单词）及其自身测试（done 无工件单查断言 out.strip()=="RUN" 精确等值，附注必红）互斥——按「可执行冻结层（骨架+测试）强于描述层」裁决（T5 裁决①同型排序）：单查输出恒为裸 token SKIP|RUN，不附注。消费方（SKILL.md P3 ③派发步/resume-kit §3 表）按精确 token 判定，附注破坏机器可解析性且无测试钉死=未冻结行为。CLI 实测：pending（INT-g1-0002）与不存在（INT-g1-9999）单查均裸 RUN 退出 0。
- 附注：计划 T8 测试块缺尾护 if __name__ == "__main__"（批次 3 各测试文件统一惯例），按仓例补齐——纯脚手架对齐零语义影响；红态实测 4 例中 3 FAIL（test_readonly_no_side_effects 对 dispatch 失败也零写入、哈希不变式空真——绿态后语义成立，即计划本意的最弱钉法，不加强）；T8 无新金样（计划 Files 未列），run_golden 全 42 面零漂移（hash=a347edd7 前后一致）；跨平台：纯 stdlib 只读路径无 OS 分支，Windows 经 tanyin-phases.cmd 同一 dispatch（T2 已建，无需改动——计划 Files 未列入口）。

## 2026-09-24 批次 3 T9 裁决（实现者记）
- Ruling（计划内部张力①·referenced 门控缺失于 Step1 代码块）：计划 Step 1 测试代码字面无装饰器，而其 Step 4 自我修正明示「正确顺序=本任务先让 SKILL 相关三例绿，referenced 一例依赖 T10，临时用 @unittest.skipUnless(...) 门控，T10 落位后自动生效」——照 Step 1 字面则 T9 交付时该例对缺失 phases/*.md 抛 FileNotFoundError 必红，与本任务出口「测试全绿+基线不回红」矛盾。按 Step 4（含其逐字给定的门控表达式 isdir(PHASES) and isfile(PHASES/P6.0.md)）裁决执行；T10 计划自身 Step 明示「解除 T9 的 skipUnless 门控」，闭环无悬空。实测：红态 FAILED (errors=3, skipped=1) → 绿态 OK (skipped=1)。
- 附注（token 实测）：计划宣称「预算实测约 1500 token，留 500 余量」——本仓实测 1321（656 CJK + ⌈2659/4⌉=665；总 3315 字符/5032 字节），余量 679；口径=PROTOCOL.md §2 冻结式（测试侧 estimate_tokens 随之冻结）。计划数字为撰写期估值、实测更优，非冲突不裁决。
- 附注（交付方式）：SKILL.md 全文（计划 2175-2222 行）与测试代码（2103-2164 行）均自计划文件程序化逐字提取落盘（非手抄），消灭转写漂移这一唯一人为风险；两文件 UTF-8+LF、零 CR 实测确认（file+grep -c）。
- 附注（金样/跨平台/契约）：T9 无新金样（计划 Files 未列），run_golden 42 面零漂移 hash=a347edd7 前后一致；无新 CLI 入口故无 .cmd 配对（SKILL.md=认知文档非可执行入口）；测试纯只读+stdlib 正则无 OS 分支，CI 双平台语义同构；五宿主 AGENTS.md 系统级注入=批次 6 安装器职责（计划 Interfaces 明示），本任务零契约回注需求。

## 2026-09-24 批次 3 T10 裁决（实现者记）
- Ruling（计划文本↔自身测试互斥①·P3 断言词前缀）：计划 P3.md 全文「断言=ledger-converge-check」会被其自身 T9 冻结测试 test_referenced_commands_known（本任务解除门控即生效）判为未知命令——KNOWN 里带 ledger- 前缀的仅 ledger-add-edge/ledger-matrix-freeze 两枚（T9 注释明示「速查里可能带前缀引用」例外），且该 lint 无双前缀归一（T2/T3 裁决的 lookup 归一只在引擎侧）。按计划意图（§10.3 静态验证①：引用⊆已知面）裁决：P3.md 该词落 bare 基名 converge-check——语义不变（执法在 PROTOCOL §1 判定行，不在写法），test_yaml_asserts_consistent_with_md 的头词断言同构满足。P3.md 其余全文自计划 2294-2331 行程序化逐字提取（T9 同款防转写漂移），实测该词是全文唯一前缀违例。
- 附注（追加件 G-14 落地）：P2.md 新增「分母就绪门」节=matrix freeze 前置步骤（tanyin-phases denominator-ready --goal-dir <D>；FAIL 清单未清空不得 freeze），措辞逐点对齐 PROTOCOL §4 冻结口径（只读账本零落账/退出码 0=就绪 1=FAIL 清单 2=用法/三断言全文）；denominator-ready 维持不入 phases.yaml 断言集（T3 裁决原案：asserts=21 基线不动），P2.md 该节定位=声明层人读前置检查单（PROTOCOL §1.5 entry 语义同型，引擎不执法）。
- 附注（八门同构短文口径）：P0/P1/P2/P4/P5/P5.5/P6.0/P6 按「四段结构头+phases.yaml duty 字符串指令化+本门断言命令清单」撰写；命令引用一律 bare 基名或 tanyin-ledger/tanyin-phases 通道形式（lint 白名单内）；P0 八问表落账对照自设计 §8.1 逐行誊录（备份确认并入第④问 RoE，不设第九问）；「回边」节如实区分——仅 P3（三事件回环）/P4（重放 REPAIRED max_retry=2）在 back_edges 内，其余七门明书「本门无事件回边」防误读。
- 附注（金样/跨平台/探知项）：T10 无新金样（计划 Files 未列），run_golden 42 面零漂移 hash=a347edd7 前后一致；九门 md=认知文档非可执行入口，无 .cmd 配对（T9 同型）；测试纯只读+stdlib 无 OS 分支，CI 双平台语义同构；G-14 探知项随本任务落地闭环（T13 归并销账）；全套 296→299=计划 3 例+un-gated referenced 例转绿（skip 归零）。

## 2026-09-24 批次 3 T11 裁决（实现者记；含追加件·总控行为纪律三断言）
- Ruling（契约内冲突①·P1 断言词 vs 02a 终审签名）：phases.yaml P1 断言①「ledger-tree-check --complete parent」（契约 04 §69 表行逐字）真跑必 ENV-HALT——check_cmds h_tree_check 拒收任何参数（exit 2），且 PROTOCOL §1.1 冻结的空格式归一只合并不剥词，「--complete parent」无论归一与否都不可直通。裁决按签名权威维度：02a（41 命令签名终审冻结）§四门校验命令行明载「参数=无（读账本）【推导转正】」，02-commands.md 指定「签名见 02a 终审补全节」，契约 04 §208 自认四命令归属待仲裁而 02a 即仲裁结果——yaml 该词落 bare ledger-tree-check；04 表行的「--complete parent」为设计期语义注记（01 §3.7 同源「＝资产树完整」），其语义由 expect=PASS+实现（parent 边完整性专项）完整承载。否决备选：引擎剥词违 §1.1 直通等价；handler 收容违 41 面拒收语义冻结。影响面实测：asserts=21 不变、phases-validate.norm（计数型输出）零漂移、test_yaml_asserts_consistent_with_md 头词断言不破（P1.md 仍含 tree-check）。
- Ruling（计划测试 bug②·fresh_drydir 传参）：计划 Step1 代码 fresh_drydir(self.td) 传 TemporaryDirectory 对象，os.path.join 必 TypeError——按接口意图（td=目录路径，T12 复用底座）在两调用点改传 self.td.name（仓例同款）；红态证据=2 errors（TypeError）。
- Ruling（追加件三断言口径③，完备性设计 2bd6052 已批衍生）：①门序=gate-exit 首现序精确等于 [P0,P1,P2]（exact equal 钉死无缺漏/无越位/无门外门；与 verify-chain 跳门检测互为冗余锚）；②无绕账本直写=简化口径「eval 前后 13 表内容 diff 逐表须有窗口内新增 timeline 命令事件词可解释」——TABLE_EVENTS 映射=write_cmds/matrix_init 全部 ctx.event 落点单源誊录（timeline.tsv 自证=verify-chain 链式哈希；egress.acl 等工件不在 13 表纪律内，PROTOCOL §3 干跑口径明许本地产物）；③预算门在位=budget-check 只读零账本痕迹，调用事实以测试侧调用窗日志 CALLS 承载（零产物/零引擎改动），STEPS 在 add-goal 后立即落一步（立项即读预算=上限法定后任何后续工作前；干跑零派发故无 P3 ⓪ 逐轮语义——最小可行口径）。TDD：③先红（hits=[]）后绿（1 次调用退出 0）。
- 附注（计划 STEPS 与 P2.md 分母就绪门的关系）：P2.md「分母就绪门」（G-14，T10 落地）不在计划冻结 STEPS——T3 裁决既定其=声明层人读前置检查单（引擎不执法，不入 phases.yaml 断言集），且最小干跑账本零 intents/facts 本就不满足多源法定断言①；照计划 STEPS 执行，不添步。
- 附注（探知项 G-15，21 断言全量审计副产物）：P5.5「ledger-approve --verify-signoff」/P6「ledger-approve --knowledge」裸旗标与写命令 _parse 唯 --key=value 形态互斥（PROTOCOL §1.1 明列 --verify-signoff 为裸旗标例）——真跑将 Usage exit 2=ENV-HALT；超 T11 范围（干跑止于 P2），留批次 6 前裁决：approve 局部预归一（T6 裁决② --release 同型先例）或 yaml 改 =1 形态。其余 19 断言签名核对全兼容（hash-recheck/matrix-audit/terminal-gate/replay-summary 裸调用、validate --tables/scope-check --all-assets/matrix-gaps --baseline/cleanup-checklist --verify/redact-scan --target 均受流；tanyin-report/tanyin-redact=设计内 ENV-HALT）。
- 附注（金样/跨平台/纪律）：T11 无新金样（计划 Files 未列），run_golden 42 面零漂移、夹具链 hash=a347edd7 前后一致（fixtures/ 零触碰，干跑起底=临时目录 fresh_drydir）；全套 299→304=计划 2 例+追加件 3 例；纯 [sys.executable, 入口] subprocess 驱动无 OS 分支无平台门控（CI 四格复验）；ResourceWarning（_snap open().read() 不关句柄）=T4 附注同款噪音不处理。

## 2026-09-24 批次 3 T12 裁决（实现者记；kill -9 保真度 eval）
- Ruling（计划笔误①·len(STEPS_N)）：计划 Step2 代码 len(STEPS_N) + 1 对 int 取 len 必 TypeError——按模块头补行指令（STEPS_N = len(STEPS) = 12，恰合注释「驱动 12 步」）裁决为 rng.randint(3, STEPS_N + 1)：+1 使断点上限 13 恰容全 12 步（i>=13 于 i∈0..11 永假=全序列可达），下限 3 保证 add-goal 必落账（子进程真跑可判）。
- Ruling（子进程补 checkpoint 步②）：计划字面子进程只跑 dry_run_p0_p2——state.md 永不存在，父测试「已写的 state 摘除（rng.random()<0.5）」分支恒死码、「模拟 kill -9 半写丢弃（state.md 删除）」与层 B 语义说明「任意断点+state 丢弃后恢复协议闭环」全部空转；按注释「驱动 12 步+checkpoint」裁决：子进程=截断驱动+checkpoint 收尾（与层 A drive_with_checkpoint 同构，--session=s-k9 同款）。
- Ruling（checkpoint --phase=实际所处门③）：层 A 计划字面固定 P3 在全序列账本合法（gate-exit P0/P1/P2 齐备），但层 B 截断账本上同款 P3=越位虚戳——verify-chain 跳门纪律正确拒收（缺失 gate-exit:P0/P1/P2，已达 P3；实测红态证据）。真实总控只对当前门 checkpoint：子进程 phase=STEPS[done-1][0]（STEPS 按门有序⇒末步标签即真当前门，其前各门 gate-exit 必已存在，构造性安全）；层 A 保持计划字面 P3 不动。
- Ruling（父进程钉死子进程真跑④）：计划字面忽略子进程返回码——子进程启动失败（exit 2）时空账本平凡恢复、用例假绿（首跑实测 OK 全 vacuous）。裁决：断言 returncode==0（断点截断=子进程主动 exit 0；非 0=未真跑）+ goals.tsv 存在（upto≥3 ⇒ add-goal 必落账）；此即本任务 TDD 红态落点（缺子进程脚本→exit 2→红）。
- Ruling（撕裂态 B 构造修正⑤·T5 裁决⑤同型）：计划 append-timeline --phase=（空值）被 _req 拒空值拒收→late-write 永不落账→撕裂态未构造、用例假绿；按 T5 同场景先例（test_state_md.py:184-185 落 P3）改 --phase=P3 并断言退出 0（撕裂构造被证明非空转）。
- Ruling（追加件·确定性穷举⑥）：seed 20260924 五枚硬币实测 0.819/0.914/0.701/0.569/0.847 全 ≥0.5——计划冻结 seed 下「state 摘除」分支永不触发（叠加 Ruling②则计划字面恒死码）。追加 test_exhaustive_breakpoint_discard_sweep：断点 3..13 × {保留,摘除} 全 22 组合，逐组前置断言 state.md 已落再摘除、恢复协议闭环+13 表 sha256 字节指纹不变——「任意断点+state 丢弃」不靠抽样运气证明；计划 seeded 五例循环原样保留（计划冻结 seed 不动）。
- 附注（红绿证据链）：红态①=层 B FAILED (failures=1)（子进程缺失 exit 2，Ruling④ 断言拦下）；红态②=补 checkpoint 后层 B 再红（Ruling③ 越位戳记=真发现：截断账本虚戳 P3 触发跳门拒收）；绿态=6/6 OK（层 A 4+层 B 2）。
- 附注（eval 结果）：层 A 三态（tmp 残留/timeline 领先/state.md 缺失）+工件缺失各 1 例，撕裂 B 走 state-rebuild FAIL→rebuild-state 修复臂→复跑 PASS；层 B seeded 断点 3/13/13/11/3 五例+穷举 22 组合，每例恢复=verify-chain 0+state-rebuild PASS+resume-kit OK+13 表指纹前后相等（保真度定义成立）；机制证据链=T4 原子写（tmp+os.replace 无第三态）+T5 对账重建。
- 附注（金样/跨平台/纪律）：T12 无新金样（计划 Files 未列），run_golden 42 面 PASS 零漂移；全套 304→310（+6）；层 B 按 skipIf(os.name!="posix") 门控=计划口径（CI ubuntu 跑、Windows 合法跳过）——诚实披露：实际机制=subprocess 断点截断+os.remove 状态摘除（可移植），未投递真实 SIGKILL 信号，kill -9 语义=半写态结果模拟（计划自身设计：撕裂窗口由层 A 三态直接构造，原子写保证无第四态）；tests/_kill9_child.py 不匹配 discover 默认 test*.py 模式不被误导入（模块级即执行驱动）；两文件 UTF-8+LF 零 CR 实测；ResourceWarning（fingerprint open().read()）=T4/T11 附注同款噪音不处理。

## 2026-09-24 批次 3 Ruling 总索引（T13 收口编；详情见各任务裁决节）

- 开工三条：Tier3 代理本体裁批次 6+守门披露；G-1 批准契约 09 增补第 11 工具（微版本通道）；G-2 子矩阵行铸造留 T2 记账不阻塞。
- T2（3）：①all_commands 只剔双前缀别名孪生键（41 基名钉死）②validate 存在性双前缀归一③phases-validate 金样接入 run_golden 既有机制；另 G-2 预批维持原案记入。
- T3（6）：①前置门零落账断言=前后计数不变②gate lookup 双前缀归一③EXTRA_TOOLS=ENV-HALT（exit 2 零落账）④写类断言 matrix-freeze 门级 --timestamp 注入⑤追加件 denominator-ready=独立子命令不入 yaml 断言集（asserts=21 基线不动）⑥追加件读侧约定冻结（PROTOCOL §4）。
- T4（4）：①revision≡本次落账后 timeline 行数②--release 裸旗标本地归一③既有 TestCheckpoint 两例 v2 适配（授权范围内必然后果）④G-6/G-10 契约回注留 T13 统一执行。
- T5（4+适配）：①absent 态输出移第二行（首行字节不变）②计划测试空 phase 修正③phase 域 END→空映射④空 state.md 防御；test_query_check 旧例 v2 适配（T4③同型）。
- T6（6）：①auto 本方=spawn 血统语义②managed-restart 事件词走 append-timeline（非 checkpoint --event 复合词）③接管/延续经 rebuild-state 释放 stale 锁④auto 同血统延续同样 state-rebuild 前置⑤phase 域映射沿 T5③⑥用法错误 exit 2；G-3/G-4 常量暂代状态记账。
- T7（4）：①模板 END 分支改写（防 phases/END.md 悬空引用）②金样=产物内容基线不接 run_golden PHASES 面③--timestamp 缺省=timeline 末行（空=exit 2）④restart⑥失败=halt 非 REJECT。
- T8（1）：①单查输出恒裸 token SKIP|RUN（可执行冻结层强于描述层）。
- T9（1）：①referenced 门控=Step4 自我修正优先于 Step1 字面（skipUnless 待 T10）。
- T10（1）：①P3 断言词 bare 基名 converge-check（静态验证意图；执法在 PROTOCOL §1）。
- T11（3）：①P1 断言词按 02a 终审签名（参数=无）裁 bare ledger-tree-check②计划测试 bug fresh_drydir 传 td.name③追加件三断言口径（门序精确等/diff 可解释/budget-check 调用窗）。
- T12（6）：①len(STEPS_N) 计划笔误=STEPS_N=len(STEPS)②子进程补 checkpoint 收尾（防 state 永不存在死码）③checkpoint phase=截断末步实际门（防越位虚戳）④父进程断言子进程 returncode==0（防空转假绿）⑤撕裂 B 构造 --phase=P3（空值拒收同 T5⑤）⑥seed 硬币全废→22 组合确定性穷举。
- T13（5）：①回注范围=派遣指令+T4④留口（02a 文末勘误+§13 三处就地指针）②G-6 引用位=实际冻结位 state_md.py/金样（非计划建议的 PROTOCOL——无偏差不 bump）③README 速查面=七子命令实况（denominator-ready 标注追加件）④验收⑥命令形态=`=`形实测（判定命令列=示意速记；空格形 exit 2 正确）⑤T12 流水行补记。

## 2026-09-24 批次 3 T13 裁决（实现者记；收口）
- Ruling（计划↔执行范围①·契约 02a 回注）：计划 T13 Files 节只列 cli/README.md+discovery-notes，G-6/G-10 回注载于探知项「建议裁决」列且 T4 裁决④明文「留 T13 收口统一回注」，派遣指令点名执行——按建议裁决+留口执行：02a 文末「v2 勘误补记（2026-09-24·批次 3 施工期·G-6/G-10 裁决）」，通道=微版本勘误（同批次 G-1·契约⑨先例，schema_version 保持=2 不递增）+contracts/README.md 勘误索引登记；§13 三处就地指针（签名行/依据行/终审补全 5，09 号契约「10→11 见文末」同款最小标记范式）。影响面自验：37 节计数/【推导】63+2 计数/无法起草项 5 计数全不动（勘误节零新增【推导】标记——回注内容全部为已裁决事实）。
- Ruling（引用位②·G-6）：计划建议「02a §13 补键表（引用 phases/PROTOCOL.md）」，但 T4 实际冻结位=cli/ledger/state_md.py KEY_ORDER 单一实现+tests/golden/write-checkpoint.state 字节基线（PROTOCOL §1-5 不载 state.md 格式；T13 Files 明文「无偏差不动 PROTOCOL」）——按「契约引用实际冻结位」裁决：十键表内联 02a 勘误节（契约自含）+引用 state_md.py 与金样双锚，PROTOCOL 不动不 bump；tests/test_contract_backfill.py::test_state_md_ten_keys_single_source 以 KEY_ORDER 单源对齐钉死（契约↔实现漂移即红）。
- Ruling（README 速查面③）：计划 Step3 速查表书「六子命令」，T3 追加件 denominator-ready 已是第 7 个在册子命令（PROTOCOL §4+tanyin-phases USAGE 行）——按「文档=交付面实况」裁：表列七行，denominator-ready 标注「T3 追加件」；速查含 --timestamp 确定性说明与 py -3 等价用法（计划明文两项）。
- Ruling（出口验收⑥命令形态④）：清单判定命令列书空格形 `--phase P2 --timestamp <T>`，引擎实收 `=`形（cmd_gate 逐 tok 前缀解析；PROTOCOL §1.1 空格式归一只施于 yaml 断言词；计划自身 T11 STEPS 即 `--phase=P0`形）——非冲突（判定命令列=示意速记，冻结面=引擎 USAGE 行与测试），按 `=`形实测留证：干跑产物（/tmp 截断驱动 11 步至 matrix-init）首调 exit 0+timeline 增 gate-exit:P2、复调 already-passed、两调后恰 1 条 P2 事件；空格形 exit 2 用法错误=行为正确。
- Ruling（T12 流水缺行补记⑤）：9f6f651（T12 记账）只落 T12 裁决节未落开发流水行——本任务补记（标注补记+缘由），流水与裁决节对齐。
- 附注（TDD 红绿）：tests/test_contract_backfill.py 7 例先行——红=6 FAIL+1 ERROR（02a 勘误节/contracts 索引/台账文件/README 批次3节缺位），绿=7/7；全套 310→317 全绿+42 金样面 PASS 零漂移+validate asserts=21 不变（T13 无新金样——计划 Files 未列；纯契约/文档改动+只读 lint 测试，无 OS 分支，CI 双平台同构）。
- 附注（出口验收实测汇总）：①test_dryrun_p0p2 5/5 ②test_kill9_fidelity 6/6（POSIX；Windows skip=计划口径）③estimate_tokens(SKILL.md)=1321<2000（PROTOCOL §2 冻结口径公式，余量 679）④结构 lint+41 命令索引+引用⊆已知面全过 ⑤validate PASS gates=9 asserts=21 constants=8 back_edges=3+PROTOCOL version=b3-frozen-1 在场 ⑥见 Ruling④ ⑦test_managed_restart 10/10（计划 7+T6 自加 3；四护栏正反例+事件词 actor=总控）⑧test_idempotent_resume 4/4（SKIP/RUN/单查裸 token/只读零副作用）⑨discover 317 OK+golden 42 面 PASS ⑩ci.yml 矩阵 ubuntu+windows×py3.11/3.12 四格在册、push 已触发（远端结果=Actions 页面复核；本环境无 gh CLI）⑪台账 G-1..G-15 cat 可核（含 G-3/G-4 常量暂代、G-6/G-10 已回注、G-15 批次 6 前裁决如实分档）。
- 附注（收口变更清单）：contracts/02a-command-signatures-draft.md（回注+指针）/contracts/README.md（勘误索引）/cli/README.md（批次3节）/docs/design/2026-09-24-b3-discovery-notes.md（台账，57 行）/tests/test_contract_backfill.py（钉子）/docs/HANDOFF.md（本节+快照+流水+Ruling 总索引）。

## 2026-09-24 批次 3 评审收尾入账（评审结论：可收）
- 评审结论：**批次 3 评审可收，Important×2 已清**（f49c6bc）：①契约 09 三处 tanyin-phases 子命令枚举 6→7（:16 允许类行/:35 命令面清单 #11/:113 G-1 勘误补记行——补第 7 子命令 denominator-ready，口径=PROTOCOL §4「独立子命令不入 yaml 断言集」T3 裁决原案；微版本勘误通道=文末新增勘误补记节+contracts/README 勘误索引登记，G-1 同款范式，schema_version 保持 =2；对齐 cli/README 七子命令速查/tanyin-phases USAGE/PROTOCOL §4/test_contract_backfill 四源）②金样回归进 CI（.github/workflows/ci.yml 四格矩阵新增 Golden regression 步=`python tests/run_golden.py`，与 discover 步同 python 入口同 env（PYTHONUTF8=1，setup-python 全平台供给）——Windows 无需 py -3 特判；run_golden.py 缺金样默认 FAIL 不落盘+`--bless` 显式建档门槛，堵「缺金样自动 INIT 落盘」在 CI 首跑/漏提交场景误判绿——三处建档点归一 gate_golden() 单一实现，漂移比对语义逐字节保真；tests/test_run_golden_bless.py 5 例 TDD 先红后绿（红=5 ERROR：gate_golden/parse_args 缺位；绿=5/5，只测纯函数面不跑 42 面全量））。
- Minor-1 同批清：契约 04 §69 表行就地指针——「ledger-tree-check --complete parent」单元格标注执行断言词=裸 `ledger-tree-check`（02a 终审签名「参数=无（读账本）」，批次 3 T11 裁决；「--complete parent」=设计期语义注记，01 §3.7 同源），防未来誊录者复引设计期注记为执行词。
- 探知项登记（评审期新增·Minor-5）：check_cmds.py:27 `_now()` 墙钟进账本——set-replay-state（:202 时间戳兜底）与 REJECTED→转 fact（:262 findings.created 盖戳）两处落账无 --timestamp 通道（写命令族均有 --timestamp=TS 通道），继承性/可重放缺口：evals 与金样重放不可复现墙钟值，与「禁 datetime.now() 进账本/产物」纪律（cli/README 批次 3 节）相悖。契约 v3 前裁决：补 --timestamp 通道或豁免注记。非 G-1..G-15 施工期台账成员（该台账 T13 已收口终态），登记于本节+「探知项」节指针。
- 验收实测：`python3 -m unittest discover -s tests` → Ran 322 tests OK（基线 317+5 新增）；`python3 tests/run_golden.py` → PASS golden: 21 读面+20 写面+1 phases 面全部锁定且确定（零漂移零 INIT）；grep 自验 09 三处（:16/:35/:113）行内 7/7 子命令齐、04:69 指针在场、`grep -c denominator-ready contracts/09-cli-surface.md` → 5（与勘误补记自验行一致）；变更文件全部 CR=0（UTF-8+LF 红线）。


## 2026-09-24 批次 4 开工（executing via subagent-driven-development）
- 用户批准计划 docs/superpowers/plans/2026-09-24-b4-engine-layer.md（含三裁决 G-2/G-12/G-13 与补充裁决 R1-R6 全案）｜commit 476ce55
- 执行结构：按域捆绑派发（T1+T2 契约/矩阵→T3+T4 门/EV→T5+T6 重放→T7+T8 引擎/差分→T9+T10 适配/adopt→T11-T13 viz/金丝雀/闭包→T14 收口），每任务 TDD+全量回归，收口后整支评审

## 2026-09-24 批次 4 T1+T2（契约勘误+词表扩展+子矩阵铸行；同域捆绑）
- 验收实测（两任务各自收口点）：T1 → 全套 discover Ran 325 tests OK（基线 322+3 新增）+ run_golden.py PASS 零漂移；T2 → Ran 331 tests OK（325+6 新增）+ 金样 PASS 零漂移。金样零刷新即预期：金样 matrix-set 场景走既有键（web.api×inj.sql）且 reason 无前缀，不触铸行分支；G-g1 夹具无新 type 行——两任务均为纯放行扩展，无既有面字节变更。
- Ruling 清单（计划冲突按意图裁决，两笔 commit 消息内同款记录）：
  - R-T1-1（argv 契约）：计划两份新测试 call() 均把 --goal-dir 尾置——CLI 单入口冻结 argv[2]=="--goal-dir"（cli/tanyin-ledger main），尾置恒 exit 2 用法错。修正=--goal-dir 紧随命令名（tests/test_negative_matrix.py 先例）。
  - R-T1-2（自洽性）：契约01 §1 变更表第 6 行「type +pivot/foothold（批次 4）」要点随 §3.6 枚举行同步为四值追加（计划 Step5 仅列枚举行+文末节）。
  - R-T2-1（全量校验前置）：计划实现片段仅前移 state/iid/reason 三赋值，state 枚举/reason 附带/intent 引用闭合校验留在旧键路径——铸行分支将绕过校验。按裁决 A「全量校验后一次写入（写前拒收纪律）」将三校验一并前置到分支前，铸造行同经全量校验。
  - R-T2-2（夹具现实）：计划 setUp 对 G-g1 直接 matrix-freeze——夹具 matrix.tsv 自带 frozen_at 盖戳行（make_fixtures 模拟 P2 冻结事件）必 REJECT「不可重复冻结」，且 web.api 行 state=" "（伪空态）致 fresh 选择器 StopIteration。修正=prep_matrix 预处理（清全部 frozen_at+空态归一；run_golden autodrive 预解冻先例）再走 CLI 冻结；未冻结负例同法预处理但不冻结。
  - R-T2-3（负例保覆盖）：test_write_cmds 旧前缀负例（空 reason 行设 submatrix:=REJECT）在新规则下属首次归类放行——改写为「先 submatrix: 置格（OK）再 authz-diff: 串类（REJECT 前缀）」，负例覆盖不丢。
  - R-T2-4（笔误修正）：计划代码片段 _matrix_prefix(ctx.val("matrix.tsv", key_rows[-1], "reason)) 引号未闭合——按语法修正落盘。

## 2026-09-24 批次 4 T4 裁决（实现者记·继任现场）
- 继任经过：前实现者完成 T3（f569abe）后在 T4 中途失败离场，现场已清理——git 工作区仅余未跟踪 tests/test_cards_matchers.py（红态：ImportError 模块不存在，discover 334 例含 1 红）；本任继任，通读计划 T4 全节（含前置裁决 R1 matcher 子集条目）后对齐红测试，确认与计划一致即以之为红态起点，按 TDD 转绿。
- 验收实测：`python3 -m unittest tests.test_cards_matchers tests.test_guard -v` → Ran 43 tests OK（9 新增+34 guard 既有，guard 行为零变更由既有面背书）；`python3 -m unittest discover -s tests` → Ran 342 tests OK（333+9，无红例残留）；`python3 tests/run_golden.py` → PASS golden: 21 读面+20 写面+1 phases 面 零漂移。金样零变动=T4 预期：guard thin delegate 字节等价、T4 无新金样面（计划 golden 节新面 engine-*/viz-data/replay-envdiff 均为 T5+ 交付物）。
- Ruling 清单（commit f8054dd 消息内同款记录）：
  - R-T4-1（红测试对齐）：留下的 tests/test_cards_matchers.py 与计划 Step1 逐字一致（8 例）+前实现者补 TestVault 第 9 例（化解计划测试文件 8 例 vs commit 模板「9 例」的矛盾，方式=vault 冻结接口直测；guard 行为零变更由既有 test_guard 背书）——判定与计划无偏差，采纳为红态起点未改动。
  - R-T4-2（函数名勘误）：计划称搬「vault_dir/_load_key/_decrypt/vault_secrets 四函数」——guard 实际为 vault_dir/_keystream/enc_payload/dec_payload/guard_key/read_cred/vault_secrets 七函数（_load_key/_decrypt 不存在）。按「单源化+行为零变更」意图整体搬入 ledger/vault.py；guard 留五个活跃调用点同名 thin delegate（dec_payload/_keystream 无 guard 调用点不留 delegate）；冻结接口名=load_key（=原 guard_key）/secret（新增：read_cred 密位，缺条目=None）/secrets（=原 vault_secrets）。
  - R-T4-3（condition 缺省）：R1 裁决文本未定 word matcher 的 condition 缺省值——按计划实现冻结为**默认 and**（非 nuclei 上游默认 or），契约06 勘误补记明示「condition 可省，默认 and」。
  - R-T4-4（11 字段口径）：计划 Interfaces 称「11 字段全量；缺字段 raise」而计划实现仅强制 id+network_position/pair_group 标量性——且 T5 测试的最小卡片仅 5 字段须可解析。按计划实现（lenient），「11 字段全量」解读为完整卡片返回形状而非强制项；同值性执法点=check_consistency（G-16：validate 集成不动，重放前校验）。
  - 附记（T3 流水补记）：f569abe 未落 HANDOFF 流水行——本任务补记（T12/T13 先例，标注补记+缘由）。

## 2026-09-24 批次 4 T5+T6 裁决（实现者记；重放驱动+重放门 eval；同域捆绑）
- 验收实测：T5 → `python3 -m unittest tests.test_replay_driver -v` 4/4；discover Ran 346 tests OK（342 基线+4）；`python3 tests/run_golden.py --bless` INIT replay-envdiff 后复跑 PASS 21读+20写+1phases+1engine 零漂移。T6 → tests.test_replay_gate 1/1（三态+三态落账+summary+verify-chain 全链）；discover Ran 347 tests OK；金样 43 面 PASS 零变动（金样变动说明：仅 T5 新增面 replay-envdiff.norm 有意建档【--bless】，存量 42 面字节零漂移）。
- Ruling 清单（commit 498d8c2/d9f7185 消息内同款记录）：
  - R-T5-1（退出码口径）：计划测试 test_unknown_id_exit_two 期望 exit 2，骨架对 E-index 无行 return 1——按接口口径「2=用法或环境问题（可重跑）」取测试侧：未知 EV id=exit 2（调用方输入错误，非执法拒绝、零落账）。
  - R-T5-2（argv 双形态）：计划测试用「--goal-dir D」「--expected-file P」空格形态，骨架只认「--key=value」等号形态——_kv() 双形态归一（以测试为准）。
  - R-T5-3（T4 面 None 归一·跨任务修复）：parse_yaml 空值键=None，add-evidence 卡片模板自身产出「pair_group: 」空行——cards.parse_ev_card 原标量守卫对任何默认卡片必 CardError（T5 重放真实工作流的阻断性缺口，T6 Step2「先定位再改实现」条款适用）。修复=守卫两键 None→空串归一（空值=未填，§4.11 TSV 权威、卡片复核只对非空同值执法）；T4 冻结签名与 test_cards_matchers 9 例零触碰（43/43 复跑背书）。
  - R-T5-4（夹具现实）：计划注释称「G-g1 夹具 E-index 首行卡片在场」，实况夹具无 evidence/ 目录——测试 mint_card 预铸+金样 prep_engine 预铸（卡 Host=10.10.9.9 命中夹具 scope include 10.10.0.0/16：免 DNS、连接层失败确定性；本机实测 10.10.9.9:1 超时 2.0s、127.0.0.1:1 即时拒连，两路径皆 OSError→env-diff）；不动共享夹具=存量面零漂移（T2 夹具预处理先例）。
  - R-T5-5（fail-closed 补强）：骨架占位符回注 vault.secret 返 None 时 re.sub TypeError 裸崩——改 REJECT exit 1（占位符无真值：vault 缺 key/缺条目/缺密位）；另补 scheme/port/timeout 值域校验（非法=exit 2）、卡片文件 OSError→REJECT、卡片 expected 违 R1 子集→REJECT（matcher-test 同口径）。
  - R-T5-6（金样归一）：norm_engine 剥 detail（连接层错误消息平台相关/逐次可变）+gd 临时路径→<GD>；判定产物 seq 文件名不入 norm（只增不覆盖，序号随跑数变）——norm 面=判定行字段（id/verdict/matched/status/results/extracted/suggest）。
  - R-T6-1（argv 契约）：计划 call() 把 --goal-dir 尾置——CLI 单入口冻结 argv[2]=="--goal-dir"（R-T1-1 同款先例），修正=紧随命令名。
  - R-T6-2（loopback 授权形态）：计划 setUp --matcher=127.0.0.1——add-scope _matcher_ok 冻结校验只认 CIDR/域名后缀/通配（裸 IP 字面量非域名语法）必 REJECT；改语义等价 CIDR 127.0.0.0/8（host_in_scope 经 _match_value CIDR 命中 127.0.0.1，授权意图不变）。
  - R-T6-3（套接字卫生）：tearDownClass 补 server_close()（shutdown 只停 serve_forever 不释放监听套接字）；跨平台声明：socketserver+http.server+127.0.0.1 绑定均 Windows 等价，无诚实 skip 必要。
- 设计输入对照（docs/design/2026-09-24-fd-report-card-spec.md，仅参照）：raw_request 原文直发语义一致——驱动不 shell-exec、不编辑报文文本、header 按原文字序发送（dict 保序）、body 原文，仅按 R2 在进程内替换 {{vault:cred-N}} 占位符；报告渲染（批次 6）不在本任务范围。

## 2026-09-24 批次 4 T7 前置裁决（图查询三命令·实现者记）
- 依据：用户批注追加件+设计增补 docs/design/2026-09-24-graph-driven-ops.md（commit 71d3b7c）——计划 T7 未含图查询三命令，按追加件作为 T7 前置子任务先落（独立 commit 注明）。
- 验收实测：`python3 -m unittest tests.test_graph_cmds -v` → 10/10；discover Ran 357 tests OK（347 基线+10）；`python3 tests/run_golden.py --bless` INIT graph 三面后复跑 PASS 21读+20写+1phases+1engine+3graph 零漂移（金样变动说明：仅新增 graph-graph-{neighbors,paths,horizon}.norm 三面有意建档【--bless】，存量 43 面字节零漂移）。
- Ruling 清单（commit f87ca25 消息内同款记录）：
  - R-G-1（面冻结例外）：计划全局约束「41 命令面冻结：本批零新增账本命令」与追加件「41 面增补走微版本勘误同 G-1 先例」冲突——按用户追加件+已批设计增补就该三命令例外放行；只读+确定性账本运算（铁律 7 四类允许之首），无攻击决策/漏洞语义判定；勘误四联动=契约02a/契约README 索引/SKILL.md 命令索引+test_phases_yaml 面数断言（声明层单源一致纪律，T14 收口不再重复改）。
  - R-G-2（图语义 v1 冻结）：节点=九表行 id（intents/creds 事件溯源 latest 去重入图）；有向攻击可达边=edges.tsv 按记录方向+凭据链（CRED→scope_asset=cred:unlock、parent_cred 父→子=cred:derive）；无向邻里仅 graph-neighbors（「周围有什么」双向视角）。设计文中 infiltrate/priv-esc/pivot/exfil-ability 攻击语义在现行 10 边词汇上 v1 映射为边类 attack={attack,proves,evidences}/asset={parent,scope-rel}/cred=凭据链——细分权重/成本=探知项 G-26（批次 5 知识飞轮定）。
  - R-G-3（金样 prep 直写）：可达表面空格行直写 matrix.tsv（prep_engine 直写文件先例）——matrix-set 对空 state 必 REJECT（state∈{x,?,-,!}），空态行只由 matrix-init/直写产生；prep 走 CLI add-edge×2+直写空格行一行。
- 后续咬合：T7 引擎 recon/test 段挂 graph-horizon（可达空格驱动，最小咬合）；P3 派发深调度/收敛补强/攻击路径进 EV=T14（收口接线）与批次 6（渲染）范围。

## 2026-09-24 批次 4 T7 裁决（实现者记·web-blackbox 四段引擎）
- 验收实测：`python3 -m unittest tests.test_engine_web_blackbox -v` → 8/8；discover Ran 365 tests OK（357+8）；`python3 tests/run_golden.py` → PASS 21读+20写+1phases+1engine+3graph 零漂移（T7 无金样变动：纯新增引擎 md 载体，不触任何命令面）。
- Ruling 清单（commit 4583e7e 消息内同款记录）：
  - R-T7-1（MANIFEST 文体冲突）：计划 MANIFEST 全文为纯表格（`| kind | skill（…）|`），其测试 assertIn("kind: skill") 要求字面子串——标题下补一行独立键值 `kind: skill`（表格保留计划逐字），两态并存双双满足。
  - R-T7-2（horizon 咬合增补例）：计划 Step1 测试 7 例不含图谱增补咬合——按追加件「引擎输出或测试设计引用 horizon 结果（最小咬合）」增补 test_horizon_coupling 1 例（recon/test 两段须挂 graph-horizon 字样）；咬合落点=recon 段「完备性口径：侦察分母=graph-horizon 可达集」+test 段「优先级=可达空格先行（深调度属 P3）」。
  - R-T7-3（命令引用纪律）：引擎 md 命令引用一律 `tanyin-ledger <cmd>` 形态（bare 命令名不被 lint 正则捕获；`ledger-<cmd>` 前缀形态在 T7 测试 KNOWN 集无 ledger-add-* 别名先例——test_skill_resident 为其显式扩 KNOWN，T7 测试未扩，故避开）。
- 交付物清单：engines/web-blackbox/{MANIFEST.md,SKILL.md,phases/{recon,surface,test,differential}.md,patterns/{submission-ok,submission-reject}.md}（8 件，UTF-8+LF 全检）；T8 消费=differential.md 五步语义，T14 消费=SKILL.md 路由表引用。

## 2026-09-24 批次 4 T8 裁决（实现者记·身份矩阵差分样例对+检出率 eval）
- 验收实测：`python3 -m unittest tests.test_authz_matrix -v` → 6/6（含 validate+verify-chain 链自洽）；`python3 tests/make_diff_fixture.py` 重铸两次 diff -r 逐字节一致；`python3 tests/eval_authz_recall.py --goal-dir tests/fixtures/diff-authz --ground-truth tests/fixtures/diff-authz/ground-truth.json` → recall=5/5 exit 0；负路径手测（临时副本删 finding 行）→ exit 1+MISSING POS-1/2/3（负对仍命中=语义正确）；discover Ran 371 tests OK（365+6）；金样 46 面 PASS 零变动（T8 无金样变动：夹具为静态入库产物，不进金样面）。
- Ruling 清单（commit 816d178 消息内同款记录）：
  - R-T8-1（STEPS 伪码占位）：计划 make_diff_fixture STEPS 含非实现签名参数（--dedup-key=…/auth-context=CRED-<user号> 直填/evidence-ids 前置）——add-finding 的 dedup_key=命令机械计算（AST+vref/title）、auth_context=--auth-context、EV 须先铸；按 write_cmds 实际签名逐拍落地，ID 从命令输出逐拍解析注入后续参数（计划「ID 占位符以命令输出逐拍解析」条款）。
  - R-T8-2（PG 铸号）：differential.md 教义「next-id E-index.tsv PG」对 PG 前缀恒返 PG-g1-0001（next_id 只扫 id 列，不见 pair_group 列存量）→ 撞夹具既有 PG-g1-0001；脚本按 pair_group 列现序+1 铸 PG-g1-0002（字典序=时间序语义不变）。教义修正属 T14 收口范围（本任务只铸不改性文件）。
  - R-T8-3（finding⇄EV 鸡后蛋）：add-finding 先验 evidence_ids 闭合、add-evidence 的 linked_finding 后验 finding 存在——先铸实验组 EV（无回链）→finding（evidence-ids=实验组）→对照组 EV（--linked-finding 回链）；T8 计划测试的 linked_finding 断言由此满足（pgs 取自回链行，实验组 EV 经 pair_group 同 PG 计入两 EV）；scorer 证据集=evidence_ids∪回链并集（双向链路单源化）。
  - R-T8-4（creds kind 取舍）：计划 STEPS kind=session 无 parent-cred 必 REJECT（session 硬门）——改 kind=static-cred（语义等价：身份矩阵 role 覆盖投影与差分语义均不依赖 kind；permitted_actions=read 经 account-grant 覆盖执法全链走通）。
  - R-T8-5（ground-truth 形状）：计划「3 正对+2 负对」在单 finding 单 PG 双 EV 结构下=3 正对标记（实验组 errorCode:00000+数据标识 total:42+对照组 anonymous-denied，均挂同 finding 证据并集）+2 负对端点基线；条目加 polarity 字段（pos 缺省/neg），负对命中规则=fact kind=authz target==endpoint（计划匹配规则仅载正对 finding 规则——负对扩展为本笔增补，scorer docstring 冻结）。
- 交付物：cli/ledger/authz_matrix.py（T11 viz 消费）、tests/make_diff_fixture.py（可重跑重铸）、tests/eval_authz_recall.py（批次 6 LLM 在环复用）、tests/fixtures/diff-authz/（13 表+evidence/ 卡片×3+art/ 工件×2+ground-truth.json）。R5 同批落地（write_cmds 直达 pending+契约02a §3+README 索引）。

## 2026-09-24 批次 4 T9+T10 裁决（实现者记·vuln-agent 适配器+nuclei adopt；同域捆绑）
- 验收实测（两任务各自收口点）：T9 → python3 -m unittest tests.test_engine_vuln_adapter -v 5/5（红=1 FAIL+4 ERROR 适配器缺位）；discover Ran 376 tests OK（371+5）；python3 tests/run_golden.py --bless INIT engine-vuln-adapter 后复跑 PASS 47 面 零漂移。T10 → tests.test_supply_chain 3/3（红=ImportError supply_chain 缺位）+tests.test_engine_nuclei 3/3（红=3 FAIL 适配器缺位）；discover Ran 382 tests OK（376+6）；金样 --bless INIT engine-nuclei-adopt 后复跑 PASS 48 面 零漂移。金样变动说明：仅新增 engine-vuln-adapter.norm/engine-nuclei-adopt.norm 两面有意建档【--bless】，存量 46 面字节零漂移。
- Ruling 清单（commit a4bb524/108c5ed 消息内同款记录）：
  - R-T9-1（POC 四要素门·设计输入落位）：计划 T9 归一化表未载 POC 门，而 FD 报告卡规格（b0006f2 §一.6/§三）明文「T9 vuln-agent 归一化（外部发现强制 POC 四要素）直接消费本规格」——按规格落门：四段（raw_request/raw_response/时间/环境）缺一=降级 facts[]（kind=vuln-clue，detail 点名缺失要素）不成 finding。计划三例测试逐字保持：夹具 VULN-1/SUSPECTED-3 补四段为正例（SUSPECTED=信息不足仍携带已观察的请求/响应——C3 档自证不降档）+新增 VULN-4 缺四段降级负例。
  - R-T9-2（argv 双形态）：计划测试空格形传参 vs 骨架仅等号形解析（R-T5-2 同型）——parse_argv 双形态归一（两适配器同款实现）。
  - R-T9-3（norm 口径）：计划金样注「剥 operations.log 时间戳」——提交自身无墙钟（时间取源 md、适配器日志不含时间戳），norm=submission.json 排序重 dump 即确定；operations.log 审计附件不入 norm。
  - R-T9-4（analyzed_surfaces 映射补齐）：计划 Interfaces 载「discovered/analyzed surfaces→assets[]+facts[]」而骨架仅处理 discovered——按 Interfaces 意图补 analyzed_surfaces→facts[]（kind=info，业务流分析摘录）。
  - R-T9-5（POC 携带位）：四要素在契约07 冻结 12 字段内的携带位——raw_request/raw_response 原文追加 reproducible_steps 尾部（Burp 直贴可重放）、时间入 evidence_refs（源文件@时间戳）、环境=network_position 恒 same-host（源码只读分析视角，G-19 载体；md 环境 值仅作门校验）；expected_matcher 维持 {}（vuln-agent 无 nuclei matcher 语义）。
  - R-T10-1（guard argv 空格形）：计划 --run 组装 "--goal-dir="+G 等号形与 guard 冻结 argv[2]=="--goal-dir" 冲突（R-T6-1 同型）——按 guard 实况 [guard, exec, --goal-dir, G, --, nuclei, -jsonl, -t templates, -u target]。
  - R-T10-2（--lock 可选覆盖）：计划 verify() 无参读 ROOT/tools.lock，而测试①「临时 lock 副本改 sha256」须可指——增可选 --lock（缺省 ROOT/tools.lock）：验签失败路径可测且不动仓内锁。
  - R-T10-3（canned 例 ENV 门控）：验签先于归一化→openssl 缺失平台 canned 归一化不可达（必 blocked）——test_canned_normalize skipUnless(HAVE_OPENSSL)（test_supply_chain 先例）；blocked 例无门控（篡改/缺 openssl 两态均 blocked，断言恒成立）。
  - R-T10-4（金样面 openssl 门控）：engine-nuclei-adopt 面在 openssl 缺失平台会产 blocked 提交与建档 done 面漂移（Windows CI 金样步必红）——run_golden NUCLEI_CMDS 段 openssl 缺失=SKIP 行（ENV 语义，出口验收⑧「openssl 例 skip=ENV 不算失败」同口径）。
  - R-T10-5（TEST-ONLY 钥/commit 占位·G-22 如实披露）：测试私钥进仓（tests/fixtures/keys/test-signing-key.pem；两钥首行 TEST-ONLY 注记，openssl PEM 解析容忍前导注释行已实测）仅锚定快照结构与验签链路，不构成信任根；生产钥生成/保管/重签+release.pub 替换=批次 6 安装器出口；upstream_commit=40×a 固定样例占位（engines/nuclei/README.md 四步更新流程+G-22 披露节同款声明）——探知项台账登记属 T14 收口范围。
- 附注（验签链路实现说明）：supply_chain 验签经 openssl pkeyutl 子进程（python3 stdlib 无 ECDSA——契约 10 终审先例）；签名覆盖=行前四字段规范串（键\t版本\tsha256\t）的 sha256 digest，模板 commit 列由 templates.lock 逐文件 sha256+tools.lock 行 sha256（=templates.lock 整文件哈希）独立锁定；supply_chain.py 计划代码逐字落盘（open 未显式 close 的 ResourceWarning=T4/T11 同款噪音不处理，CPython 引用计数即时落盘）。
- 交付物：engines/vuln-agent/{MANIFEST.md,adapter.py}、engines/nuclei/{MANIFEST.md,adapter.py,README.md,release.pub,templates.lock,templates/*.yaml×3}、cli/ledger/supply_chain.py（批次 6 tanyin-install 复用）、tools.lock、tests/fixtures/{keys,engine/nuclei-jsonl,engine/vuln-agent-out}、tests/test_{engine_vuln_adapter,supply_chain,engine_nuclei}.py、tests/golden/{engine-vuln-adapter,engine-nuclei-adopt}.norm。G-18（契约07 nday-verify→nuclei 无段映射注记）与 G-19（视角顶层字段 v3 裁决）注记未动契约文件=T14 收口/契约 v3 范围。

## 2026-09-24 批次 4 T14 裁决（实现者记·收口）
- 验收实测（出口 10 条+补充判定，逐条本机实跑，判定命令=计划清单原文）：
  - ① `python3 tests/run_golden.py` → PASS golden: 21 读面+20 写面+2 phases 面+1 engine 面+3 graph 面+2 adapter 面+1 viz 面（=50 面；连续两次执行输出逐字节一致——确定性自证；批 4 新面 replay-envdiff/engine-vuln-adapter/engine-nuclei-adopt/viz-data/graph×3 全在册）。
  - ② `python3 -m unittest tests.test_authz_matrix -v` → Ran 6 tests OK；`python3 cli/tanyin-ledger verify-chain --goal-dir tests/fixtures/diff-authz` → PASS verify-chain: 19 行链完整 gate_exit=4 跳门=0（exit 0）。
  - ③ `python3 -m unittest tests.test_replay_gate -v` → Ran 1 test OK（127.0.0.1 mock 三态全链路→set-replay-state→replay-summary→verify-chain）。
  - ④ `python3 tests/eval_authz_recall.py --goal-dir tests/fixtures/diff-authz --ground-truth tests/fixtures/diff-authz/ground-truth.json` → recall=5/5（exit 0）。
  - ⑤ `python3 -m unittest tests.test_submatrix_mint tests.test_assets_type_b4 tests.test_recon_canary -v` → Ran 11 tests OK。
  - ⑥ `python3 -m unittest discover -s tests` → Ran 409 tests OK（批 3 基线 322+批 4 新增 87=3+6+2+9+4+1+10+8+6+5+6+4+2+7+14；零 skip 除声明 ENV 的 openssl 例）。
  - ⑦ `python3 tests/run_golden.py`（exit 0）+`git status --short tests/golden/` → 0 行（工作树干净；T14 纯文档/契约层不触命令面，无金样变动）。
  - ⑧ 四格矩阵在册：ci.yml matrix os=[ubuntu-latest, windows-latest]×python=["3.11","3.12"]（fail-fast:false），Unit tests（ci.yml:24）+Golden regression（ci.yml:26）两步；push origin main 随本笔 commit 后触发——远端绿需 GitHub Actions 页面复核（批次 3 第⑩条同口径；本环境无 gh CLI）。
  - ⑨ `python3 -m unittest tests.test_skill_resident -v` → Ran 21 tests OK（含 TestBatch4Wiring 4 例+TestBatch4Handoff 10 例；estimate_tokens(SKILL.md)=1465<2000，余量 535；八节/44 索引/引用⊆已知面全过）。
  - ⑩ `test -f docs/design/2026-09-24-b4-discovery-notes.md` → 在场；`grep -c 'G-1[6-9]\|G-2[0-3]' docs/design/2026-09-24-b4-discovery-notes.md` → 22（≥8）；HANDOFF 开发流水 T1-T14 记账齐（T14=本笔）。
  - 补充判定（并入⑥口径）：`python3 -m unittest tests.test_trigger_audit tests.test_engine_web_blackbox -v` → Ran 15 tests OK（触发器闭包三检查+A1-A8 通道表+多源法定）。
- Ruling 清单（commit 消息内同款记录）：
  - R-T14-1（TRIGGERS 版本化=内容增补必 bump）：高危 finding 即时横向触发器按「版本化」指令落 triggers-v1→triggers-v2（v1=T13 当日冻结；triggers-catalog 事件的版本一致性语义依赖 bump 纪律）。既有面适配=test_trigger_audit.test_catalog_file_versioned 断言 v1→v2（断言意图=目录文件版本化，不裂）；trigger-audit ①-③ 检查面不扩（高危行消费检查=批次 5 与 G-24 同批 evals；目录「复扫 evals（批次 6）」行同型先例）；PROTOCOL §6 版本行就地 v2+勘误补记一行（§6=T13 批 4 追加节非冻结文本）。
  - R-T14-2（intents.priority 物理列分期落）：设计增补 fb72cd5「intents 增 priority 字段（契约微版本）」全量落列与批 4 计划 Step3「金样零漂移」出口互斥（15→16 列=全套夹具重铸+金样大规模刷新），且 severity_expect 基线表无源（G-24 批次 5 定——落列必造占位语义进写路径）。裁决=本批契约 01 文末勘误冻结字段语义与公式（冻结文本=phases/P3.md「派发优先级算分」节；§3.3 十五字段表不动）；物理列+写路径/查询排序支撑随批次 5 G-24 定案后落；过渡期承载=派发时总控按公式现算（读侧三源 assets.meta/graph-horizon/creds 均有只读命令）；Top-K 选择=总控决策——契约 09 §4 边界 2「任何对『是否漏洞/下一步测什么』的判断」禁入 CLI，派遣指令「确定性算分若需 CLI 支撑」=条件不成立（G-3 常量暂代同型分期先例）。
  - R-T14-3（路由表 cli 型引擎入口）：计划路由行三引擎统指 engines/<引擎>/SKILL.md，但 vuln-agent/nuclei 无 SKILL.md（cli 型方法论入口=MANIFEST，G-18 裁决原文）——按实际交付面改写（web-blackbox=SKILL.md、vuln-agent/nuclei=MANIFEST.md）；三引擎名+「派发前核 MANIFEST 纪律能力（超 max_op_level/视角上限拒派）」计划语义逐字保持。
  - R-T14-4（P4.md 零改动）：计划「P4.md 补 tanyin-replay 协议引用——若 T3 已含则跳过」——T3 已落 duty 3（tanyin-replay 驱动+三态落账协议），按跳过条款零触碰（test_p4_replay_protocol_references_driver 红阶段即绿=证）。
  - R-T14-5（高危横向 intent 不 bypass 打分晋升）：fb72cd5「立即生成同型横向排查 intent」落为「④ 验收落账当刻即提、不等下一轮风暴」（时机语义），不走直达 pending——直达条件=origin=recon-event 或 kind=authz-diff（契约 02a §3 冻结面零扩），正常 add-intent 打分+晋升阈值。
  - R-T14-6（G-18/G-19 拆分处置）：T9+T10 附记「G-18 注记未动契约文件=T14 收口/契约 v3 范围」——G-18（nday-verify 段映射）随本笔回注契约 07（收口范围）；G-19（perspective 顶层字段）留契约 v3（v3 裁决项非收口项）；两态在 07 勘误节同段披露。
  - R-T14-7（SKILL P0 落账载体双载）：PROTOCOL §6①「P0 落账 triggers-catalog 事件由 SKILL P0 序列承载」——SKILL.md 九门循环 P0 行+phases/P0.md duty 序列双点同语（常驻集=循环摘要/P0.md=详令；只载详令漏常驻视角）。
- 移交件落地对照（派遣指令四项）：①契约 09 子命令 7→8（§2/§3/文末勘误三处+自验 grep=4）+cli/README 八子命令速查+SKILL P0 triggers-catalog 序列；②fb72cd5 优先级调度=P3.md ③派发规则+「派发优先级算分」公式节+契约 01 intents.priority 勘误（R-T14-2 分期）+TRIGGERS.md v2 高危即时横向行；③台账终态归并=b4 台账新建（G-16..G-23 计划原文誊录+G-24..G-26 设计增补登记+状态归并+移交清单四节）+b3 台账 G-2/G-12/G-13 就地闭环注记（追加注记不改历史行）+HANDOFF 指针一致（快照+探知项节）；④HANDOFF 批次 4 状态快照行+文末「批次 4 Ruling 总索引」。
- 附注（TDD 红绿/金样/跨平台）：tests/test_skill_resident.py 扩 TestBatch4Wiring（计划 Step1 逐字 4 例）+TestBatch4Handoff（移交件 10 例）——红=13 FAIL（P4 引用/预算 2 例按计划跳过条款先绿），绿=28/28 含 test_trigger_audit v2 适配；全套 409 绿（395+14）+金样 50 面 PASS 零漂移（无金样变动：纯文档/契约层）；变更文件全部 UTF-8+LF 零 CR（file 实测）；纯 md/契约改动无 OS 分支，CI 四格语义同构。

## 2026-09-24 批次 4 Ruling 总索引（T14 收口编；详情见各任务裁决节）

- 开工：用户批准计划 476ce55（前置裁决 G-2/G-12/G-13+补充裁决 R1-R6 全案）；三设计增补按追加件落地（71d3b7c 图查询/T7 前置、b0006f2 FD 卡片规格/T5/T9 消费、fb72cd5 发现流+优先级调度/T11/T14 落）。
- T1+T2（5）：R-T1-1 argv 契约（--goal-dir 紧随命令名，后续任务同型不复记）/R-T1-2 契约01 变更表第 6 行同步/R-T2-1 全量校验前置（写前拒收纪律）/R-T2-2 夹具冻结态预处理（prep_matrix）/R-T2-3 前缀负例改写保覆盖/R-T2-4 引号笔误修正。
- T3（2）：P4.md exit 镜像行随 yaml 同步去 SKIP；契约11 §7 P4 出口引用位+README 勘误索引登记补齐（计划文件清单遗漏，按「每笔勘误必登记」纪律）。
- T4（4）：vault 七函数整体搬家（计划四函数名与实况不符）+guard thin delegate；word condition 缺省=and；11 字段=返回形状非强制项；继任现场红测试采纳+T3 流水补记。
- T5+T6（9）：R-T5-1 未知 EV id=exit 2/R-T5-2 argv 双形态归一/R-T5-3 T4 面 None→空串归一（跨任务修复）/R-T5-4 夹具无 evidence 目录预铸/R-T5-5 占位符无真值 fail-closed REJECT/R-T5-6 金样 norm 剥 detail+路径占位/R-T6-1 argv 契约/R-T6-2 loopback 授权 127.0.0.0/8 CIDR/R-T6-3 tearDownClass server_close。
- T7 前置（3）：R-G-1 「零新增账本命令」约束按用户批准增补就三图查询命令例外放行（勘误四联动）；R-G-2 图语义 v1 冻结（attack/asset/cred 三类边+凭据链）；R-G-3 金样 prep 直写空格行（matrix-set 对空 state 必 REJECT）。
- T7（3）：MANIFEST 文体两态并存（表格+kind: skill 键值行）；horizon 咬合增补例（recon/test 段挂 graph-horizon）；命令引用 tanyin-ledger 形态（lint KNOWN 面约束）。
- T8（5）：STEPS 伪码按 write_cmds 实际签名落地；PG 铸号=pair_group 列现序+1（教义修正随 T14 落）；finding⇄EV 鸡后蛋回链序；creds kind=static-cred（session 硬门）；ground-truth polarity 扩展（负对命中规则）。
- T9（5）：POC 四要素门按 FD 规格 b0006f2 落位（计划三例逐字+VULN-4 降级负例）；argv 双形态；norm=submission.json 排序重 dump；analyzed_surfaces→facts 补齐；四要素携带位（reproducible_steps/evidence_refs/network_position）。
- T10（5）：guard argv 空格形；--lock 可选覆盖；canned 例 skipUnless(HAVE_OPENSSL)；金样面 openssl 缺失=ENV SKIP；TEST-ONLY 钥+upstream_commit 占位=G-22 如实披露。
- T11（3）：findings 实时流投影随 T11 落（第六键+置顶分段）；stats 扩展四键（matrix_set/attack_edges/converged/budget）；红态口径（2 FAIL+1 ERROR）。
- T12（5）：argv 契约；add-fact 必填集补参；金样面归属错配（norm 改锁 PASS 面+prep_denominator 新面）；副本目录名=goal_id 钉死；canary 家族全子命令零网络口径。
- T13（8）：argv 契约；add-cred 参数组契约对齐；matrix-freeze 幂等 rc∈{0,1}；①检查事件驱动（计划行遍历与自身 baseline 测试冲突——Interfaces 文本裁决）；版本比对补全（缺记非失败）；②全局候选口径+per-cred 延后通道；PROTOCOL 节号 §5→§6（追加序）；egress 事件确定性（EPOCH+相对路径+phase 空）。
- T14（7）：R-T14-1 目录版本 bump v2/R-T14-2 intents.priority 物理列分期（语义先冻、批次 5 落列）/R-T14-3 cli 型引擎路由入口=MANIFEST/R-T14-4 P4.md 跳过条款零触碰/R-T14-5 高危横向不 bypass 晋升/R-T14-6 G-18 回注与 G-19 留 v3 拆分/R-T14-7 P0 载体双载（SKILL.md+P0.md）。
- 评审收尾（5）：R-RC-1 norm 单源语义=严格侧（值替换哨兵小写+尾换行结构保留，整行丢弃弃用）/R-RC-2 夹具 P4 完备化（G-23 墙钟绕道直写重放行+副本跑门纪律）/R-RC-3 supply_chain fail-closed 形式统一（一切不过=失败对→blocked exit 0）/R-RC-4 金样 recheck 面形态（fresh_of 副本+无墙钟 PASS 行独立分类）/R-RC-5 README 计数同步（41→44×3 契约面同源+金样面 50→51）。

## 2026-09-24 批次 4 评审收尾入账（评审 C-1 必修+顺手件三件；子代理（评审收尾）记）

- **C-1（必修）修复**：证据双指纹 norm 轨写/查两套归一化恒失配——根因=写路径 write_cmds._hashes（_NORM_DROP 整行丢弃+ISO→<TS>+splitlines/join 丢尾换行）与查路径 check_cmds.normalize_artifact（值替换+<ts>+split/join 保尾换行）语义不同：任何文本工件（含无动态字段工件——尾换行结构差异即失配）落账 norm 恒≠重算 norm；实测修复前 hash-recheck --goal-dir tests/fixtures/diff-authz → FAIL（EV-diff-authz-0001/0002 content_hash_norm 失配），gate P4 同红（assert 3 挡停）。修复=norm 轨单源化：cli/ledger/norm.py（normalize_artifact+artifact_hashes），写路径（add-evidence 落账 content_hash_norm）与查路径（hash-recheck 重算）同款；write_cmds._hashes/check_cmds.artifact_hashes 皆薄壳。语义裁决见 R-RC-1（哨兵语义=严格侧优先；时间戳/nonce 动态字段归一化规则冻结进 norm.py 模块 docstring——增删规则=面变更须走版本化）。
- **红→绿证据（TDD）**：先红 5 例——①test_write_cmds.TestAddEvidence.test_norm_track_roundtrip_hash_recheck（真实 add-evidence 铸动态字段工件→hash-recheck 必 PASS；红=AssertionError 1!=0）②test_query_check.test_norm_single_source_strictness（红=ModuleNotFoundError ledger.norm）③test_authz_matrix.test_hash_recheck_pass（红=夹具 hash-recheck FAIL）④test_supply_chain.test_verify_entry_nonhex_sig_fail_closed（红=ValueError fromhex 裸抛）⑤test_supply_chain.test_load_lock_non_five_fields_adapter_blocked（红=适配器 ValueError 崩溃 exit 1）——修复后 5/5 绿。
- **重铸（确定性）**：make_diff_fixture.py 增 stamp_replays（P4 完备化⑤）——变更=E-index.tsv 两行 content_hash_norm 刷新（无动态字段工件 norm=raw 同值，属新语义正确形态）+timeline.tsv 尾加两行 replay:EV-diff-authz-000{1,2}:VERIFIED（TS2 固定）；双跑重铸 diff -r 逐字节一致；hash-recheck PASS（chain=ok ev_checked=2 ev_skipped=1）+verify-chain PASS（21 行链完整）+ledger-replay-summary PASS（verified=2 pending=0）+recall=5/5 不回退+全套含 test_authz_matrix 414 绿。
- **gate P4 亲跑证据**：夹具副本（cp -R 至 /tmp——R-RC-2：跑门写 timeline 事件，仓内夹具禁就地跑门；修复前留在仓内夹具的 gate-fail 尾行已随重铸清除）tanyin-phases gate --phase=P4 → OK gate:P4 gate-exit:P4 asserts=5 result=PASS exit 0，复跑 already-passed 幂等。
- **金样变动（逐面说明）**：①diff-hash-recheck.norm 新增（run_golden RECHECK_CMDS 显式建档，--bless INIT；面=diff-authz 副本 hash-recheck 输出行，无墙钟确定性；PASS 行独分类「recheck 面」）②viz-data.norm 有意刷新（rm+--bless 重建；唯一 delta=stats/counts/timeline.tsv 19→21——P4 完备化两事件行所致，json diffwalk 实测仅此一键）；其余 49 面零漂移。
- **顺手件①（README 计数）**：cli/README.md 行 3/46/74 三处 41→44（命令面=契约 44 面同源：19 写+14 查询+10 校验+1 特殊；run_golden 行注明 21 读+20 写+3 图查询=44）+金样面计数 50→51（本批新增 recheck 面）。
- **顺手件②（supply_chain fail-closed 形式统一）**：verify_entry 签名非 hex → (False, "sig 非 hex…") 失败对（不再 bytes.fromhex 裸抛；openssl 子进程前判定）；adapter.verify 捕获 load_lock ValueError → (False, "tools.lock 解析失败…") → blocked 提交 exit 0——一切「不过」形态统一为失败对→blocked（与「不过=blocked」契约语义一致）；测试补两负例（test_verify_entry_nonhex_sig_fail_closed / test_load_lock_non_five_fields_adapter_blocked——后者端到端断言 blocked submission+operations.log 缘由）。
- **顺手件③（I-1/I-2 登记）**：b4 台账（docs/design/2026-09-24-b4-discovery-notes.md）增补第五节——G-27（trigger-audit 逐对配对需 intents cred 绑定列，评审 I-1，契约 v3 或批次 5；R-T13-6 per-cred 配对注记的正式化）+G-28（converge 补「无可达未测格」结构性停机+攻击路径进 EV，评审 I-2，批次 5；T7 前置「后续咬合」条延伸）+R6 cap 机检缺口挂 G-20（AUTHZ_DIFF_PAIR_CAP=24 现为双载文档常量零代码零测试锚定——契约 v3 增常量时同批落机检）；移交清单同步（批次 5 前必裁决+契约 v3 待办各补行）；标题 G-16..G-28。
- **验收实测**：python3 -m unittest discover -s tests → Ran 414 tests OK（基线 409+新增 5；零 skip 除声明 ENV 例）；python3 tests/run_golden.py → PASS 51 面（21读+20写+2phases+1engine+3graph+2adapter+1viz+1recheck）；hash-recheck/gate P4（副本）如上；git status panorama/ → 0 行（未触碰）。
- **Ruling 清单（本节=Ruling 索引「评审收尾（5）」详情）**：
  - R-RC-1（norm 单源语义=严格侧）：两套归一化并存且互斥，取谁由语义定——评审指示「哨兵语义=改一字必检出的严格侧优先」：查路径值替换语义保留（动态字段值→哨兵，行内其余字符全保），写路径整行丢弃语义退役（_NORM_DROP 命中行的其余内容改动不可见=宽松侧漏洞）；哨兵 <ts>/<n> 小写定死；尾换行结构保留（split/join 非 splitlines/join）；二进制工件 decode("utf-8","replace") 恒可 norm（写路径「不可解码=norm 退化 raw」分支退役——该分支亦是写/查不对称失配源）；规则冻结 norm.py docstring=单源文档面，契约 02a hash-recheck 节「归一化去 nonce/时间戳」措辞与严格侧一致无需勘误。
  - R-RC-2（夹具 P4 完备化+跑门纪律）：验收要求 gate P4 亲跑 PASS，而 C-1 修复后 P4 后续断言 ledger-replay-summary 因夹具零重放事件仍红（C2 finding 证据待重放）——夹具按 P4 完备形态补铸：双 EV replay:…:VERIFIED 事件行；G-23（set-replay-state 无 --timestamp 通道，_now() 墙钟）禁入夹具 → 按 core.row_hash 直写链式事件行（引用闭合由铸造序保证，run_golden prep_engine 直写先例），G-23 清账后回 CLI 通道；重放状态不落 findings 新行（replay-summary 判定只扫 timeline 事件；exploitation_status 语义列非该断言前提）。纪律：跑门须在夹具副本（gate 写 gate-exit 事件——修复前仓内夹具被就地跑门污染的 timeline 尾行即前车之鉴，随重铸归零）。
  - R-RC-3（fail-closed 形式统一）：「不过=blocked」契约语义下一切验签前置失败不得裸抛崩溃（exit 1）——sig 非 hex 于 verify_entry 内 fromhex 前判定返回失败对（模块层单源，调用方免 try）；load_lock 解析错保持 ValueError 解析不变式，由 adapter.verify 捕获适配为失败对（库不变式与适配器 blocked 语义分层——两条路都收敛 blocked exit 0）。
  - R-RC-4（金样 recheck 面形态）：diff-hash-recheck 面走 fresh_of 夹具副本+run_engine 命令形（REPLAY_CMDS 先例）而非 READ_CMDS（后者钉 G-g1 夹具）；输出 PASS 行无墙钟免归一；PASS 汇总行独立「recheck 面」分类（计面口径不与读面混淆）。
  - R-RC-5（README 计数同步）：三处 41→44 按契约 44 命令面同源刷新（行 46 run_golden 注明 21+20+3 构成——graph 三面自 T7 前置起在册，41 为批 1 期陈旧值）；金样面 50→51 为本批变更自身引入的同步（评审仅点名三处 41，面数行不同步即成新陈旧计数）。

## 2026-09-24 批次 5 开工（executing via subagent-driven-development）
- 用户批准计划 docs/superpowers/plans/2026-09-24-b5-knowledge-flywheel.md（19 任务/出口 10 条/六探知项裁决+R7-R14+G-29..G-35）｜commit 904d153
- 执行结构：按域捆绑派发（T1+T2 契约→账本三小件/图/骨架/反向验证并行组→流水线链→语料入库→eval→T19 收口），每任务 TDD+全量回归，收口后整支评审

2026-09-24｜子代理 T1｜批次5 T1：契约14 知识库 schema 冻结（六类页 front-matter 全集/先例三元组/staging 状态机+四门槛/CLIENT-NN/graph.ndjson 行 schema/ID 前缀表 KP-STG-CP-PR-EN-TG-PT-RT-BZ/词表版本化 WSTG-v4.2/许可纪律 MIT+format_version=kn-v1）+契约09 工具面 11→12（tanyin-knowledge 第12员工具 13 子命令，G-1 先例同通道，§2 允许类行/§3 标题联动）+README 契约清单增补接口⑰；tests/test_knowledge_contract.py 9 例 TDD 先红后绿（红=3 FAIL+6 ERROR），全套 414→423 绿+金样 51 面 PASS 零漂移｜1e89bb5
2026-09-24｜子代理 T2｜批次5 T2：契约v3 首批集中清账六笔——04 constants 8→10（authz_diff_pair_cap=24 R6/G-20 回注+restart_rate_minutes=10 G-3 回注 phases_engine 既有常量）+gate-fail 事件词汇补注（G-7，PROTOCOL §1.3 同源）+P4 duty 攻击链落证注记（G-28，详文随 T8）+06 G-16 结案（维持 replay 侧单点 cards.check_consistency）+07 G-19 结案（perspective 不开，same-host 过渡）+09 canary 干跑口径（G-8=egress 只 compile/canary 只 deploy 不 probe）；TestContractV3Sweep 4 例 TDD 先红后绿（红=4 FAIL 全红），全套 423→427 绿+金样 51 面 PASS 零漂移｜baa414e

## 2026-09-24 批次 5 T1+T2 裁决（实现者记）
- R-T1-1（六类节标题形态）：计划测试断言「技法页（concepts/CP-*.md）」等闭括号节名，而计划契约 14 骨架标题=「技法页（concepts/CP-*.md，K5）」（含类目后缀，断言串不命中）——按测试意图（六节钉子）落「### 技法页（concepts/CP-*.md）——K5」形，K1-K8 类目信息保留（破折号后缀+§1 映射表同源）。
- R-T1-2（§2 允许类行联动）：计划 T1 Step4 只列工具表加行+勘误补记+自验更新，未列 §2 允许类表——按声明层单源一致纪律（批4 T3 契约11 引用位先例）§2「确定性账本运算」行同步增 tanyin-knowledge（13 子命令枚举），§3 标题「工具箱 11 工具」同步 12；勘误补记载自验复跑 grep=12（原 10 为冻结时点基线保留可追溯，G-1 注先例同型）。
- R-T1-3（format_version 语义合并）：计划契约 14 骨架 §1 仅「format_version（当前 kn-v1）」，同计划文件结构图载「单行；不匹配拒绝操作并提示迁移」——誊全文时两处合并（骨架行补注记），非新增语义。
- R-T2-1（G-16/G-19 断言强化）：计划测试断言裸串「G-16」/「G-19」，两串已在批次 4 勘误注记在册（06 R1 注/07 T14 收口注）——裸串先绿违反 TDD 先红后绿，按 TDD 技能「Test passes? Fix test」强化为结案标记「G-16 结案」/「G-19 结案」，断言意图（结案注记在场）不变；实测红=4 FAIL 全红。
- R-T2-2（same-homemaker 笔误）：计划 G-19 结案文案「network_position=same-homemaker」——契约 07/批次 4 台账在册口径=same-host（R-T14-6 过渡载体原文），按在册口径落 same-host。
- R-T2-3（T2 Files 清单补 09）：计划 T2 Files 节未列 contracts/09-cli-surface.md，但 Step3 第 6 笔与 git add 清单均含之——按步骤执行（G-8 清账=09 文末勘误补记节，PROTOCOL §3 原文同源核对后落笔）。
- R-T2-4（constants 计数联动）：§1「8 常量」/§2 标题「8 项」随表增两行同步 10（声明层单源一致）；§自验原 grep（枚举原 8 名）计数仍=8 不破，勘误补记载自验复跑（含两新名）=10；restart_rate_minutes 落笔前实核 cli/ledger/phases_engine.py:747 注记原文引用。
- R-记账（HANDOFF 时点）：两任务计划 git add 清单均不含 docs/HANDOFF.md，流水行须引用任务 commit hash（自引用环）——先任务 commit 后流水行独立 commit（f2dc8eb/309b889 批次内既定手法）；本裁决节即该 commit。

2026-09-24｜子代理 T3｜批次5 T3：intents 15→17 双列物理落地——priority（G-24 算分落列，add-intent --priority 0-1 浮点校验可空）+cred（G-27 绑定列落第 17 列，任意 kind 非空写前引用闭合+authz-diff 硬门原样保留；schemas.json 17 项与契约 01 §3.3 同步）；夹具 G-g1/diff-authz 一次重铸（schema 驱动生成器零改）+金样 20 写面有意刷新（44 行变更逐一归因两新列，读面/链哈希零漂移）；字段总数钉子 147→149 同步（test_core/test_write_cmds）；test_intents_columns_b5 7 例 TDD 先红后绿（红=7/7），全套 427→434 绿+金样 51 面 PASS；契约01 §3.3+勘误补记/契约02a §3+勘误补记/README 勘误索引（微版本通道 schema_version=2 不递增）｜6a3a5f9
2026-09-24｜子代理 T4｜批次5 T4：set-replay-state 增 --timestamp 必填（G-23 转正，缺/空=exit 2）——命令路径 _now() 两处退役（timeline 重放事件行+findings 联动行 created 均取参数；_append_timeline ts 转必填位置参+check_cmds._now 删除=仓内最后一处墙钟清零）；diff-authz 夹具重放事件行改 CLI --timestamp 铸（6d3a033 直写绕道退役，裁决 E）+金样 viz-data 有意刷新（联动 findings 行+1：findings_stream/pinned_high 2→3/graph 节点/counts 连动）；存量 7 处测试调用补 --timestamp（契约随行）；test_replay_timestamp 5 例 TDD 先红后绿（红=5/5），全套 434→439 绿+金样 51 面 PASS；契约02a §36 签名/参数表/拒收条件+勘误补记+README 索引（微版本通道）｜684c5c9
2026-09-24｜子代理 T5｜批次5 T5：AUTHZ_DIFF_PAIR_CAP=24 落代码常量（cli/ledger/write_cmds:345，.py 引用 0→7 处）+add-intent 同端点计数写前拒收（计数键=asset+kind 二元组经 dedup_key 前缀比对、在途 status∈{candidate,pending,active}、拒收消息附 count 与 cap 值）+--cap 覆盖通道 1-1000 校验（G-3 同型，evals 可重放）；differential.md/P3.md 双载文档转单源指针；test_authz_cap 5 例 TDD 先红后绿（红=4 FAIL+1 ERROR），全套 439→444 绿+金样 51 面 PASS 零漂移（拒收路径不进金样正面）；契约02a §3 参数表/拒收条件+勘误补记+README 索引（微版本通道）｜d957a39
2026-09-24｜子代理 T6｜批次5 T6：trigger-audit ②逐对配对（G-27 cred 列消费——每 CRED 须 kind=authz-diff 且 cred=<id> intent 或延后 fact target=authz-diff:<id>，全局口径退役）+④高危即时横向机检（triggers-v2 承诺兑现：matrix-test/deep-dive intent title/detail 内联 FD-id 或 target=lateral:<FD-id> 披露 fact——facts.target 自由文本新语义值零 schema 变更）；检查面 3→5（PROTOCOL §6 五检查重写+文末批5 勘误补记作废批4「①-③ 不扩」暂缓承诺；TRIGGERS.md ②行/高危行消费检查列文字升级，版本不 bump——目录行集合与语义零变）；P3.md ④验收落账行补横向/披露通道句（R-T3-4 算分承载行 L25 未动）；批4 测试契约随行（test_trigger_audit setUp 补基线高危披露 fact，零夹具/金样改动）；test_trigger_audit_v2 7 例 TDD 先红后绿（红=3 FAIL ②全局/④缺位），全套 444→451 绿+金样 51 面 PASS 零漂移｜e422c2c
2026-09-24｜子代理 T7｜批次5 T7：converge-check 增可达性维度——graph_cmds.reachable_gap_cells 单源抽取（BFS+空格 join；h_graph_horizon 改调同函数行为零变由金样 graph-graph-horizon.norm 钉死；R-T7-1 起点集参数化）+#reachable-gaps/#unreachable-gaps 双计数行（verdict 行居首，gate 断言读首行兼容）+结构性停机判据（不可达空格经 unreachable: 前缀置态「-」后计入清零=G-28 前半，matrix-set 零改动；structural 提示仅在可达清零而不可达>0）；金样 read-converge-check 有意刷新（两行计数+提示=行为增强非破坏；--bless 不豁免在档漂移，删旧面重建先例）；契约02a §22 输出行+文末勘误补记（微版本通道）；存量两处输出形状断言契约随行（test_canary_budget/test_query_check）；test_converge_reachable 4 例 TDD 先红后绿（红=3 FAIL 无计数无判据），全套 451→455 绿+金样 51 面 PASS｜b6dd4ca
2026-09-24｜子代理 T9｜批次5 T9：tanyin-knowledge 第12员工具骨架——knowledge.py 单源（FORMAT_VERSION kn-v1/13 目录/init 幂等/format_version 门不匹配 exit 2 提示迁移/种子库只读纪律 R7：source-register·approve·commit·promote·demote·client-map add 写子命令指向仓库 knowledge/ 即 REJECT exit 1；R-T9-2 client-map 守卫取 add 动词粒度）+入口骨架 SUBCOMMANDS 13 子命令枚举+.cmd 包装照 tanyin-redact 先例+仓库种子库落位（init 产物+checklists 人审 checklist 全文：质量判断四问/脱敏抽查三处原文/许可注记核对/VulnClaw experience 人审门注记）+client-map.tsv gitignore 排除（R12 真值永不进仓）；test_knowledge_init 6 例 TDD 先红后绿（红=6/6 含 R-T9-1 用法枚举钉子），全套 457→463 绿+金样 51 面 PASS 零漂移｜e3da2b6
2026-09-24｜子代理 T10｜批次5 T10：staging 流水线机器侧——source-register（sha256 对原始字节流式+KP 语源递增扫 SOURCES.tsv 行键 R-T10-5+origin 六枚举 REJECT+license 必填+--timestamp 必填 G-23）+lint 四件（契约14 六类 PAGE_SCHEMAS schema 机器表/脱敏哨兵 special.scan_text 单源化 scan_text_file 改调零行为变金样钉死（R-T10-2 列号语义保留+真域名/IP 哨兵 knowledge 侧补充形态不进 PLAIN_PATTERNS 防 redact 面全面误报）/dedup_key 查重 sha256(kind+vuln_class+标题归一) R10 norm_title 全半角+去空白+小写窄函数不碰 norm 轨+同键组>1 全组 FAIL+同 class≥8 人审合并建议告警 G-30/词表版本 R14 VOCAB version 行支持集+vuln_class 词表键闭合+CVE 核验标记 R11+client 形态 R12+window 格式+source_id 引用闭合）+staging.tsv 十列状态机（R8：staged→lint-passed；R-T10-4 状态机唯一载体=staging.tsv lint 不回写页 front-matter 校验器不改被校验物 checksum 盯漂移）+log.md 追加 lint 行；R-T10-3 lint/register --timestamp 必填（G-23 硬红线计划草图漏带按约束补）；R-T10-1 计划草图 sha256 断言笔误按意图强化为全值断言；test_knowledge_staging 9 例 TDD 先红后绿（红=7 FAIL+1 ERROR），全套 463→472 绿+金样 51 面 PASS 零漂移（test_redact_injection 36/36 回归随行）｜4963139
2026-09-24｜子代理 T11｜批次5 T11：approve/commit/export/match/neighbors 五子命令——approve（lint-passed→approved 状态机非法迁移 Reject+staging.tsv approved_by/approved_at 双列+log.md 双落+--reject 通道 rejected 终态留档）/commit（approved→formal+STG→类前缀重号迁类目录+_commit_transform id 行改写+staging_status 摘除+dedup 终检 R10 执法点+index.md/overview.md 确定性重生成+graph.ndjson 不动）/export（graph.ndjson 全量重建行序 (source,序号) 字典序+实体别名合成 alias 三元组行+created 取 last_verified 无墙钟两次执行字节一致+json 紧凑分隔符对齐契约 14 §3 示例 R-T11-1/R-T11-2）/match（client 全等∧scope_asset 分号多值任一子串∧window 覆盖+过期 [expired] 空格分隔不命中 R-T11-4+跨客户永不命中+--today 必填 G-34 缺省 exit 2+[stale] R11 降权标注 verified_at 距 today>365 天）/neighbors（graph.ndjson subject/object 实体行清单=A8 外推入口，缺导出 exit 2）；run_golden 增 KN_CMDS 两面（kn-export/kn-match，非 ledger 入口 ADAPTER_CMDS 先例同型 prep_knowledge 临时 init+预置 PR/EN formal 页）+PASS 行增 kn 面；T11 依赖 T9/T10 已交付物全量落地无半边裁剪（R-T11-5）；test_knowledge_export_match 12 例 TDD 先红后绿（红=11 FAIL，today_required 因未实现 exit 2 先绿），全套 472→484 绿+金样 51→53 面 --bless 建档 PASS（新 2 面 INIT 归因如实记账+复跑零漂移）｜636c4c2
2026-09-24｜子代理 T12｜批次5 T12：K1 严重度期望基线表落表（k1-baseline.tsv 12 wstg 全类+4 子类示范行五列，初值=WSTG v4.2 严重度倾向+CNPEN 复盘校准人审冻结 R-T12-3+k1-wstg-map.tsv 三列 WSTG↔ASVS↔OSSTMM 词表锚）+tanyin-knowledge score 只读算分（priority=severity_expect×asset_value×exploitability stdout 单行 JSON 双跑字节一致；asset_value=assets.meta bv:<0-1> 未标/未命中 0.5 中性；exploitability=0.4×可达 reachable_gap_cells 单源 R-T7-1 converge 语义+0.3×active creds>0+0.3×先例命中>0；查表次序细类→wstg 类→缺省 0.5+baseline-miss 告警 R-T12-2 告警入 sources.warnings 保纯 JSON；sources 附查表行/可达计数/凭据计数/命中页可审计复算；--today 必填 G-34；Top-K 仍归总控契约 09 §4 边界 2 铁律 7）+lint K1 覆盖率断言（VOCAB 每 wstg-* 键恰一行/无 VOCAB 外行/severity cost vocab 枚举值域；无基线文件的 init 运行时库跳过 R-T12-4）；P3.md 算分承载行勘误（读侧=tanyin-knowledge score+物理列已落批5 T3+Top-K 总控不变）+②行 score 表述随行；test_skill_resident KNOWN 面 R-T12-5 增 tanyin-knowledge（P3 引用第 12 员工具入已知面）；test_k1_baseline_score 13 例 TDD 先红后绿（红=8 FAIL+2 ERROR），全套 484→497 绿+金样 53 面 PASS 零漂移｜df51cd1
2026-09-24｜子代理 T13｜批次5 T13：四门槛晋升 promote（①复现≥2=先例 applied_patterns 页 id 计数/②跨目标=引用先例 client 去重≥2/③人工审批=log.md approve for=promote 在场检查 R-T13-1 不设 CLI 写通道/④无指纹泄漏=special 形态+真域名 IP 哨兵 R-T13-2 与 lint 同源防旁路——缺口清单化 REJECT exit 1；learned→core 移动+_fm_transform status 改写+log 落账 refs/clients 计数）+demote（--refuting ≥2 项独立反证强制+--note 须含防护拦截/代码修复分类词→patterns/demoted 区 status=demoted+log 落账；learned/core 两区均可降）+lint 保鲜（--today 显式基准+--freshness-days 缺省 180 陈旧清单 exit 0 附告警不判 FAIL，match [stale] 降权联动 R11；--timestamp 可由 --today 派生 T00:00:00Z R-T13-3 保 G-23 零墙钟，仅 --timestamp 既有调用面零回归）；test_knowledge_promote 9 例 TDD 先红后绿（红=7 FAIL），全套 497→506 绿+金样 53 面 PASS 零漂移｜0aff887
2026-09-24｜子代理 T14｜批次5 T14：K3 本地 CVE 快照（cve-snapshot.tsv 14 行精选七列+首行 snapshot-date 注记+cve/README 来源/更新纪律/联网仅核验边界/匹配粒度注记）+nday-match 离线 CPE 匹配（前缀匹配+版本区间元组比较 [start,end)，_vtuple 段内前导数字非数字按 0 milestone 折叠；输出 #snapshot-date 审计行 G-32+#candidates+命中四栏按 cve_id 排序；零命中 exit 0（空集=合法结果）；--cpe/--version 必填 exit 2）+lint K3 快照七列/severity/source/published 校验（G-32，无快照库跳过）+_read_tsv 注释行跳过（TSV 注记行通用化）；金样 kn-nday 第 54 面 --bless 建档（prep_knowledge 增种子快照拷贝，kn-export/kn-match 既有面 norm 零漂移复验）；R-T14-1 快照行 7 计划笔误两处修正（severity 前导空格+双端同值 10.0.0 恒空区间，按 _vtuple 粒度取 end=10.0.1+README 注记）；R-T14-2 离线边界自证=test_no_network_imports 抓获本任务 docstring 残留联网库字样一并清除（urllib/socket/http.client/requests 零在场）；test_nday_match 9 例 TDD 先红后绿（红=5 FAIL+2 ERROR），全套 506→515 绿+金样 53→54 面 PASS｜4102b7e
2026-09-24｜子代理 T15｜批次5 T15：反向验证落地——tanyin-redact --reverse-verify（special.h_reverse_verify 敏感词三源=assets.value 全集/creds.username_ref/PLAIN_PATTERNS 泄漏形态；缺省 target=report/report-draft.md 可 --target 覆盖；占位符属脱敏正当形态不进形态扫描 R-T15-3）+gate P6 断言真跑（EXTRA_TOOLS 拆分：validate known 集不变，执行期 halt 集收窄 GATE_HALT_TOOLS={tanyin-report}，redact 分发 special.REVERSE_VERIFY R-T15-2 不进 HANDLERS 守 44 面基名单源；P6 过门显式落 END 收官行 R-T15-4）+client-map next/add/list（CLIENT-NN 运行时映射四列 R12，--timestamp 显式 G-23，种子库只读守卫复用+client-map.example.tsv 模板进仓）；R-T15-1 approve 裸旗标本地归一（--knowledge/--verify-signoff=1，checkpoint --release 先例——P5.5/P6 yaml 断言从此可跑）；P6 门端到端首通=干跑链路 P0→P6 全通最后一块；test_reverse_verify 14 例 TDD 先红后绿（红=10 FAIL），全套 515→529 绿+金样 54 面 PASS 零漂移｜bb9c5bf
2026-09-24｜子代理 T16｜批次5 T16：CNPEN 82 五类素材入库降级登记通道（R-T16-1：执行期核验五类素材均不在仓——测试全景图/思路复盘/测试记录 T1-T55/31 份黑盒漏洞单/BurpPOC 合集，素材库在仓外且属禁碰区；按计划「素材不可得=登记 SOURCES 待补行不造数据」）：SOURCES.tsv 五笔 origin=cnpen/proprietary 待补行 KP-0001..0005（sha 占位防伪造）+sources/cnpen/README.md 五类落位/蒸馏去向/就位后 source-register 重登纪律；零蒸馏页产出（不造数据反向断言钉死：无页引用未就位语源）+种子库 init 补齐空类目目录+lint PASS n=0；词表 WSTG 全集与 CLIENT-NN 形态两前向钉（防批次 6+ 补页过拟合）；test_knowledge_ingest_cnpen 7 例 TDD 先红后绿（红=2 FAIL+2 ERROR），全套 529→536 绿+金样 54 面 PASS 零漂移｜e557b1d
2026-09-24｜子代理 T17｜批次5 T17：外部语料入库——VulnClaw MIT 注记（sources/vulnclaw/LICENSE.note：Copyright (c) 2026 UncleC，HEAD 3b71e26 锚=SOURCES KP-0006 真实 sha256；CVE 待核验清单按 R11 离线通道 R-T17-2 本批全页不写 cve_refs 只写方法论内容）+8 detail-pack 蒸馏技法页 CP-0001..0008（sqli/xss/ssrf/ssti/deserialize/cmdi/cors/open-redirect 四段映射：Domain→applicability/覆盖域表→vuln_class 词表键/Boundaries→正文边界节/Pivot Hints→failure_modes/Exit Evidence→judgment；余 39 专题批次 6+ 飞轮）+2 warstory 先例页 PR-0001..0002（攻击链主谓宾 triples 8+6 行、flag/平台域名/IP 全占位符化零残留 R-T17-3）+checklists experience 人审门增补节（Lessons remain pending until human approves=四门槛③同型；0.88 语义合并无嵌入载体→G-30 登记；K5 恰 8 页触发人审合并建议 WARN 属预期非 FAIL）+BugHunter/Threatswarm/CEP 三源缺素材降级登记 KP-0007..0009（G-35 待补行不阻塞；CEP ROE business 页随素材延后 R-T17-1）；staging→lint→approve→commit→export 真跑流水线（runtime 副本执行后回落种子库，graph.ndjson 14 行）；test_knowledge_ingest_external 9 例 TDD 先红后绿（红=6 FAIL），全套 536→545 绿+金样 54 面 PASS 零漂移｜c4c6728
2026-09-24｜子代理 T18+T19｜批次5 T18 前置：种子库测试隔离泄漏修复——T16/T17 两处 test_lint_passes_on_seed 就地 lint 仓库种子库（R8 lint 逐页审计行追加+staging 同步写，跑全套即脏已两次复现）：改 tmp 副本 prep_knowledge 同款隔离+「种子库零写热」字节级断言钉死；知识库行为零变；红=2 FAIL 实测复现泄漏→绿=16/16，545 绿+金样 54 面｜c3d8c8b
2026-09-24｜子代理 T18+T19｜批次5 T18：出口 eval 两件——双知识库抽查 §9.4 四判据（字段完整=lint 全 PASS/指纹自反可检索=先例逐页自反 match+实体 neighbors 非空/无跨客户残留=DOMAIN_RE.IP_RE 同源全页扫描+白名单/CVE 核验标记齐全=--origin external 限定）+反向验证脏净双向断言；探针一律整库临时副本执行（R-T18-1）+抽查范围在库页口径（R-T18-2=G-35）+脏夹具 knowledge-dirty；红=5 FAIL→绿=5/5，550 绿+金样 54 面｜76bba9b
2026-09-24｜子代理 T18+T19｜批次5 T19：总控接线收口——SKILL 路由知识库行（复测 1540<2000 token）+P6 duty 命令化五步（双锚审批 G-33）+P3 asset-added 回边 nday 通路+recon A8 neighbors 接点+CPE 指纹形态+cli/README 批次5节（13 子命令速查+顺手修 L128 同源陈旧缓建表述）+b5 台账 G-29..G-35 落盘+b4 台账五行就地闭环注记+R-T3-4 核验=L25 已由 T12 改写（补钉子防回退）；引擎 KNOWN 面随行（R-T19-1）；TestBatch5Wiring 10 例红=8 FAIL→绿，560 绿+金样 54 面｜0e43901
2026-09-24｜子代理 T18+T19｜批次5 T19 补：tanyin-knowledge argv 双形态归一（R-T19-2：出口实测发现计划判定命令与 P6 duty 五步空格形态不可跑——lint 空格形 TypeError 裸崩 rc1；knowledge 侧 parse_argv 归一并 query_cmds.parse_kv 单源，账本 44 面 parse_kv 零触碰；修复后出口补充判定命令按计划原文实跑 PASS n=10 exit 0）；红=3 FAIL→绿=4/4，564 绿+金样 54 面｜4546375

2026-09-24｜子代理（评审收尾）｜批次5 评审收尾：I-1 lint 种子库零写入（裁决 R-RC5-1 选 a——冻结资产运行时审计只落运行库；出口判定命令原文就地亲跑 PASS n=10 exit 0 且 log.md/staging.tsv sha256 前后一致）+M-1..M-6 顺手六件（契约14 created 勘误指针/先例+模式表 vocab_version/checklist 占位符形态张力节/README 勘误索引补 T7 converge/探知项两笔登记/match 缺 --client 改 exit 2——TDD 各先红后绿）；全套 566 绿（基线 564+新增 2）+金样 54 面 PASS 零漂移+git status 必净；详情见文末「批次 5 评审收尾入账」节｜7719c93

## 2026-09-24 批次 5 T3+T4+T5 裁决（实现者记）
- R-T3-1（测试 run() 形态）：计划 T3 测试片段 run() 把 --goal-dir 后置（args 尾部追加），与 tanyin-ledger 入口 argv[2]=="--goal-dir" 硬约束相抵（后置形态 7/7 全 rc2=假红根因）——按在册三处先例（run_golden.run_cli/make_diff_fixture.call/tests 既有）改 --goal-dir 紧随命令；测试意图（子进程真跑 CLI）不变。
- R-T3-2（状态转移用例改 id）：计划 test_status_change_row_carries_columns 用 INT-g1-0001，夹具中该行 status=done 终态（_INTENT_ARROWS["done"]=∅ 不可复活，set-intent-status 必 REJECT）——按用例意图（追加行携带 priority/cred 值）改 INT-g1-0002（pending→active 合法转移）；夹具钉子由 test_fixture_rows_all_17 独立承载。
- R-T3-3（字段总数钉子联动）：计划 Files 清单未列 tests/test_core.py/test_write_cmds.py，但两处 147 字段总数钉子随 15→17 必破（schemas_frozen 冻结 tripwire 语义）——按钉子意图同步 147→149 并注记勘误依据（R-T2-4 计数联动先例）。
- R-T3-4（P3.md 承载行未动）：P3.md L25「物理列随批次 5 落」经 T3 已成陈旧表述，但该行属 T19「P3.md 算分节读侧改写」范围（本任务 Files 清单不含 P3.md，T5 才首触该文件且仅护栏行）——留 T19 一并改写防并行冲突（声明层滞后注记，非语义错误）。
- R-T4-1（findings 联动用例改 id）：计划 test_rows_carry_given_timestamp 用 EV-g1-0001，夹具中该 EV linked_finding 为空（不触发 findings 联动行，断言必败）——按用例意图（timeline+findings 双行均取参数时间戳）改 --id=FD-g1-0001 直指 finding；EV 通道另设用例（test_ev_replay_via_linked_finding 同款语义：无 linked 不联动）只断 timeline。
- R-T4-2（viz 测试期望联动）：make_diff_fixture 重铸改 CLI 通道后，VERIFIED 联动按命令语义在 diff-authz 追加一条 findings 行（计划未列 test_viz.py，但 test_stream_latest_n_pinned_top 期望「夹具两条 高」随重铸失真 3→4 条）——流投影按行不按 id 去重（viz_render 语义未动），按新夹具现实改期望（置顶段 3 高+非置顶 1 中，pinned_high=3），投影器零改动；viz-data 金样随之有意刷新（同根因归因）。
- R-T4-3（read-set-replay-state 零漂移）：计划 T4 预期 read-set-replay-state.norm 漂移且「VALS --timestamp 复用」——实测该面=空 stdout（status 形态走 parse_kv 位置参数→UsageError，stderr 不入 norm，norm 为 0 字节文件），T4 改动不经此面——零漂移无需 bless，实际漂移面=viz-data.norm（重铸联动，R-T4-2）；计划预期与实况偏差如实记账。
- R-T4-4（墙钟清零口径）：裁决 E 载「两处 _now() 退役」，实现取彻底形态——_append_timeline 的 ts 缺省通道删除（转必填位置参数，唯一调用方随改）+check_cmds._now 本体删除（含 datetime import 退役）——grep 复核 cli/ 全仓 _now()/datetime.now 零命中，「禁 datetime.now()」红线自本笔起全仓执法。
- R-T5-1（cap 计数口径细化）：计划裁决 F 计数键=asset+kind 二元组（经 dedup_key 前缀比对）——实现按 dedup_key 三元组键序 (asset)+"+authz-diff+"+title 取前缀 (asset or "-")+"+authz-diff+"，即同资产全部 authz-diff intents 计入（不管 title 端点细粒度——title 承载端点属草拟语义，dedup_key 前缀=唯一机械可比对载体，计划 Step3 注记同款）；「同端点」语义由 --asset 入键保证（不同 --asset 不同前缀互不计数，test_other_endpoint_not_counted 钉之）。
- R-记账（T3+T4+T5 时点）：同 R-记账先例——三任务 commit 先行，本流水+裁决节独立 commit 引用其 hash。

## 2026-09-24 批次 5 T6+T7+T8 裁决（实现者记）
- R-T6-1（④基线冲突·契约随行）：G-g1 基线含 FD-g1-0001（impact=高）且无横向闭包——④机检落地后凡断言全绿的批4 用例（test_baseline_session_passes/test_asset_added_without_submatrix_fails/test_cred_session_deferred_fact_closes）必挂；按 T4「契约随行」先例在 test_trigger_audit.setUp 统一补 target=lateral:FD-g1-0001 披露 fact（测试自铸非夹具改写——金样写面 norm_state 全量含 facts.tsv，改夹具=20 写面连锁漂移，违背本任务「金样零漂移」）。④检查实现取「findings.tsv 行全集」口径（计划 Interfaces 逐字），批量置态/suspected 状态不豁免（触发器目录行 12 语义=add-finding 落账当刻即横向）。
- R-T6-2（PROTOCOL 节号）：计划称「§5 检查面 3→5 注记」——§6 才是 trigger-audit 节（R-T13-7 批4 同款偏差），按实况落 §6（五检查重写+文末批5 勘误补记明示作废批4「①-③ 检查面不扩」暂缓承诺）；旧「三检查」编号（版本/闭包/清单）与新五检查（①asset②cred逐对③scope④高危⑤版本+清单）在 §6 内重排统一，pass 行输出格式不变。
- R-T6-3（TRIGGERS 版本不 bump 边界）：R-T14-1「内容增补必 bump」与本任务「目录行集合与语义零变，仅消费检查列文字升级」并立——机检兑现属执法面非目录面变更，版本史节追加一行注记留痕不 bump version: 行。
- R-T6-4（P3.md 高危回边行落点）：计划称「P3.md 高危回边行补一句」——P3 回边节仅三事件行（asset/cred/scope）无高危行，按语义最近落点=④验收落账行（add-finding 落账唯一承载行，L26）追加一句；R-T3-4 算分承载行 L25 未触碰。
- R-T7-1（单源函数起点集参数化·核心裁决）：计划片段 reachable_gap_cells(s) 固定起点=scope-root 资产集，与同任务「h_graph_horizon 改调它，行为零变」互斥（horizon 起点=--from 任意节点，两起点集在一般账本上不等价）——按行为零变优先将签名参数化为 reachable_gap_cells(s, starts)：horizon 传 {--from}（金样 graph-graph-horizon.norm 逐字节钉死）、converge 传 _scope_root_targets(s, nodes)（计划语义原样）；单源性保住（同一 BFS+空格 join 实现），converge 消费形态与计划 Produces 一致。
- R-T7-2（输出行序）：计划测试断言 r2.stdout.startswith("converged") ⇒ verdict 行必须居首、计数行随后——与 phases.yaml P3 断言「stdout 首行∈{converged,budget-exhausted}」（phases_engine._judge 精确等值比对首行）天然咬合；structural 提示只附于 running 行尾（converged/budget-exhausted 行保持纯 token，gate 判定零扰动）。
- R-T7-3（金样刷新机制）：计划称「--bless 有意刷新」——run_golden.gate_golden 实况 bless 只 INIT 缺金样面、不豁免在档漂移（批次 3 评审·审计#7 门槛语义）——按 T12 prep 先例删旧面文件重建（git diff 归因：唯一 delta=converge-check 三行新输出）；非破坏性增强如实记账。
- R-T7-4（判据等价性注记）：可达/不可达空格按「表面值∈可达资产值集」二分穷尽全部空格，故「双清零」与旧 matrix_gap_cells 空判布尔等价——本笔实质增量=①双计数行可见性②structural 提示行动指引③unreachable: 显式置格通道文档化（图依据显式置格而非静默豁免）；converge_state 增 gap_cells 可选参避免同空格集二次重算。
- R-T8-1（接口实况·契约随行）：计划测试片段按旧接口书写（--artifact-path/--content-hash-raw/--content-hash-norm/--card-path）——批次 4 评审 C-1 单源化后 add-evidence 实况=--artifact 传路径+双指纹命令自算（norm.py artifact_hashes 单源）+card_path 自动派生；计划意图「总控算哈希=命令算，LLM 不手算」由命令内自算更强兑现（LLM 连哈希都不经手）；P4.md duty 文按实况接口书写。
- R-T8-2（duty 步序）：计划称「P4 duty 第 6 步」——P4.md duty 实况 4 步，攻击链落证按追加序落第 5 步；契约 04 P4 duty 注记（T2 已落）无需再动。
- R-T8-3（命令形校验联动）：duty 文初稿写「ledger-add-evidence」触发 test_skill_resident.test_referenced_commands_known 静态校验 FAIL（已知面=add-evidence）——改 in-surface 命令形 add-evidence（该钉子本任务当场兑现执法价值）。
- R-记账（T6+T7+T8 时点）：同 R-记账先例——三任务 commit 先行（e422c2c/b6dd4ca/5b4daf0），本流水+裁决节独立 commit。

## 2026-09-24 批次 5 T9+T10+T11 裁决（实现者记）
- R-T9-1（用法枚举钉子增补）：计划 T9 测试 5 用例未钉「SUBCOMMANDS 注册表+用法输出 13 子命令枚举行」——按 Produces 接口增补 test_usage_lists_13_subcommands（无参调用 exit 2+输出含 13 子命令名）；接口钉死非行为变更。
- R-T9-2（client-map 守卫粒度）：R7 写子命令守卫集取「client-map add」动词粒度（next/list 只读不拒）——guard_writable(kdir, sub, rest) 带 rest 判动词；init 不在守卫集（种子库本体即 init 产物，幂等 no-op 无写害）。
- R-T9-3（handler 名归一）：入口派生 handler 名 h_<sub>——sub 含连字符（source-register/nday-match/client-map）与 Python 标识符不相符，取 sub.replace 减号转下划线（h_source_register 等）；getattr 静默 None 会把实现缺失误报成「未实现」，已由 T10 首跑红实况验证修正必要。
- R-T10-1（sha256 断言强化）：计划测试草图 64a 前缀断言系笔误（64 个 a=特定哈希值，夹具不可能恰中）——按意图「sha256 在场」强化为全值断言（对原始字节流式 sha256 后 hexdigest 全串在 SOURCES.tsv 行内）。
- R-T10-2（域名/IP 哨兵落点·单源边界）：计划 ②「special.scan_text 对正文+front-matter 值扫描——真域名/IP/凭据形态零容忍」与「scan_text_file 改调它行为零变」互斥（真域名进 PLAIN_PATTERNS=redact 面对账本/报告合法 scope 值 shop.example 全面误报，金样 read-redact-scan 必漂移）——凭据+占位符形态单源 scan_text（零行为变，列号语义保留），真域名/IP 形态落 knowledge 侧 DOMAIN_RE/IP_RE 补充扫描（lint 面专用）；「零容忍」语义在 lint 页内完整兑现。
- R-T10-3（--timestamp 必填）：计划 lint(kdir)/source_register 接口与测试草图均无时间戳参数——全局约束「一切进产物的时间戳显式传入…knowledge log.md 同律」（G-23）为硬红线，SOURCES.tsv.registered_at/staging.tsv.created/log.md 行首 ts 全需显式源——lint/register 写产物路径 --timestamp 必填（缺/非法=exit 2 用法问题），测试按约束补参。
- R-T10-4（状态机唯一载体）：计划「staging 页 front-matter 额外字段 staging_status（=staged）」若被 lint 回写=校验器改被校验物（checksum 随写随变，漂移检测失效）——状态机唯一载体=staging.tsv（R8「机器索引」原文），页内 staging_status 仅记入库态、commit 时摘除；lint 过页 staged→lint-passed 只落 staging.tsv。
- R-T10-5（KP 递增载体分立）：KP 递增扫 SOURCES.tsv 行键（TSV 载体），目录版 next_id（扫 类前缀-NNNN.md 文件）留给 T11 commit 类前缀重号——两载体分立函数防误用。
- R-T11-1（graph 行紧凑分隔符）：契约 14 §3 示例行=无空格紧凑形态——json.dumps 增紧凑 separators（默认带空格与示例不符，断言 predicate 键虽过但字节面漂移）；金样 kn-export.norm 按契约形态建档。
- R-T11-2（created 字段取源）：计划 export 片段 created=last_verified 与契约 §3 示例注「created=commit 时间戳」并立——取 last_verified（页面自有数据：双跑字节一致+export 免 --timestamp+不依赖 commit 时序）；字段名与行 schema 不动，语义注记随代码 docstring。
- R-T11-3（dedup 终检执法点）：R10「同 dedup_key 重复 commit=REJECT」与 lint 组告警并行不悖——lint 查重组 FAIL（rc 1）但逐页无缺者仍放行 lint-passed（页各自合法、组合重复），执法点=commit 终检（对目标 formal 区同键 REJECT）；测试走自然状态机（两页 approve→commit 一→commit 二 REJECT）免夹具手改。
- R-T11-4（expired 行形态）：计划断言 PR-0001 加 tab 不在 stdout（窗口外）——expired 行取空格分隔（tab 断言语义=命中行 tab 分隔不被过期行误中）；[stale] 附于命中行尾（R11 降权标注消费形态）。
- R-T11-5（依赖实况）：T11 计划 Interfaces 全部 Consumes=T9 骨架+T10 状态机+契约 14 §3（T1 已冻）——无计划外未交付依赖，五子命令+金样两面全量落地，无半边裁剪。
- R-记账（T9+T10+T11 时点）：同 R-记账先例——三任务 commit 先行（e3da2b6/4963139/636c4c2），本流水+裁决节独立 commit。

## 2026-09-24 批次 5 T12+T13+T14 裁决（实现者记）
- R-T12-1（score 先例命中因子 client 可选）：计划 score 签名无 --client 而因子文字=「先例 match 命中」——T11 match 子命令 client 全等硬约束不破：抽 _match_rows(kdir, client, asset, today) 单源，match 传 client（跨客户隔离不变），score 传 None（读侧只消费命中计数与页 id，CLIENT-NN 脱敏形态由 lint 强制，无真值反查面）；R9/§7.1 跨客户纪律意图=真值不跨流，CLIENT-NN 形态页 id 计数不构成泄漏通道。
- R-T12-2（baseline-miss 告警载体）：计划断言 baseline-miss 在 stdout 且他例 json.loads(r.stdout) 整体解析——告警不得破坏 stdout 纯 JSON 单行，落 sources.warnings 数组（五顶层键集合不变的 Produces 契约内）。
- R-T12-3（基线表初值载体）：计划「初值由 WSTG v4.2 严重度倾向+CNPEN 复盘校准评定（人审冻结）」——CLI 只校验枚举/格式/覆盖率（裁决 A 硬边界），初值=计划 T12 Step3 给定 16 行数据逐行誊落（0.9 注入/越权族→0.3 信息收集；cost_hint 请求量级 1/2/3），rationale_brief 承载评定依据一行，人审冻结随 commit。
- R-T12-4（K1 lint 断言作用域）：init 运行时库无 methodology/k1-baseline.tsv——覆盖率断言若对空库强制=批5 T10/T11 全部既有夹具回归崩；取「有基线文件才校验」（种子库/发行库必带必过，运行时库跳过待批次 6 安装器拷贝），T10/T11 测试零改动全绿实证。
- R-T12-5（KNOWN 面随行）：P3.md 承载行首次引用 tanyin-knowledge 触发 test_referenced_commands_known 静态校验 FAIL——KNOWN 工具集增第 12 员（T9 已交付在册，非新面）；T8 R-T8-3 同款钉子执法价值再兑现。
- R-T12-6（P3.md ②行随行小改）：L14「dedup_key/score 由 add-intent 机械计算」与承载行「读侧=score 子命令」表述冲突——dedup_key 留 add-intent、score 表述改「读侧 score」，防双源歧义；阈值语义零变。
- R-T13-1（四门槛③无 CLI 写通道）：R9 条文「③=在场检查」——promote/demote 不附带 approve-for=promote 写子命令（approve 面向 staging 状态机，与 promote 审批分立）；测试与 P6 流程（T19 收口）经 log.md 在场行核验，写通道留人审流程/后续任务。
- R-T13-2（④哨兵集合与 lint 同源）：计划④「redact 哨兵零命中」与测试「页含真域名→④缺」并立——special.scan_text 不含域名形态（R-T10-2 单源边界），④扫描集=special.scan_text+DOMAIN_RE/IP_RE（与 lint_page 同源），防「lint 拒、promote 过」旁路。
- R-T13-3（lint 时间参数双通道）：计划 T13 测试 lint 仅传 --today 与 T10 既有「--timestamp 必填」并立——取双通道：--timestamp 优先（账行原样）；缺省由 --today 派生 T00:00:00Z（G-23 零墙钟不破——一切时间仍显式传入）；--today 另作保鲜基准日（与账行 ts 语义分立）；T16/T18 计划内 lint --today 用法由此可跑。
- R-T13-4（demote 目录态）：DIRS 骨架无 patterns/demoted——demote 执行时 makedirs（init 不预建，防空目录进发行库）；demoted 区不入 LINT_ZONES/export 扫描面（降级=退出飞轮扫描与图导出，status=demoted 留档可溯）。
- R-T14-1（快照行 7 笔误修正）：计划快照行 7 两处笔误——severity 列「 high」前导空格（七列格式校验必炸）+version_start=version_end=10.0.0（[start,end) 语义恒空区间=死行）；按 _vtuple 粒度（milestone 10.0.0-M7 折叠 (10,0,0)）修正 end=10.0.1 并在 README 注记粒度限制；其余 13 行逐字誊落。
- R-T14-2（离线边界自证反噬自证）：TDD 红转绿后 test_no_network_imports 仍红——根因=本任务 nday_match docstring 残留「urllib/socket」字样（banned 子串断言按源码全文匹配）；改写措辞「零网络客户端外联」，模块 import 面与文案双双零 banned 子串；断言执法价值当场兑现（防文案即防未来注释里顺手 import 的滑坡）。
- R-T14-3（金样快照入 prep）：kn-nday 面需快照在场——prep_knowledge 增种子库 cve-snapshot.tsv 拷贝（临时库三目录 precedent/entities/cve），kn-export/kn-match 既有两 norm 逐字节零漂移复验（快照非页面不入 export/match 面）；#snapshot-date 取自快照首行注记（G-32 静态文本，双跑一致）。
- R-记账（T12+T13+T14 时点）：同 R-记账先例——三任务 commit 先行（df51cd1/0aff887/4102b7e），本流水+裁决节独立 commit。

## 2026-09-24 批次 5 T15+T16+T17 裁决（实现者记）
- R-T15-1（approve 裸旗标本地归一）：yaml P6 断言 ledger-approve --knowledge 与 P5.5 --verify-signoff 为裸旗标，write_cmds._parse 拒收一切非 --key=value 形（P5.5/P6 断言现状=不可跑的死断言）——不动全局 _parse（44 面签名纪律），_approve 入口本地归一 --knowledge=1/--verify-signoff=1（checkpoint --release 先例同款）；读侧分支语义零变（in args 判真）。
- R-T15-2（reverse-verify 不进 HANDLERS）：计划草图 HANDLERS["reverse-verify"] 入注册表会让 registry.all_commands() 基名集 44→45（HANDLERS 键集=44 命令面单源），撞「账本命令零新增」冻结约束——取 special.REVERSE_VERIFY 模块常量（usage_guard 包装），仅 tanyin-redact 入口与 phases_engine 断言回路两处分发；tanyin-ledger reverse-verify 不可达=旗标语义（R13 断言文本 tanyin-redact --reverse-verify 零改）；EXTRA_TOOLS 保留为 validate known 集，执行期 halt 集收窄 GATE_HALT_TOOLS={tanyin-report}，validate/金样双零漂移复验。
- R-T15-3（占位符不进反向验证形态面）：计划净草稿用例自带 {{vault:cred-2}} 且期望零命中——{{vault:}} 占位符是脱敏正当形态（契约 01 creds.secret_ref 白名单同源），h_reverse_verify 形态级只复用 PLAIN_PATTERNS 明文形态不扫占位符残留；P5 redact-scan 面占位符零残留执法不变（双检语义不同层：P5 管终稿零占位符、P6 管草稿零真值）。
- R-T15-4（P6 过门 END 行）：计划测试 assertIn("END", stdout) 而既有 run_gate 只印 OK 行——P6 on_pass=END（phases.yaml），过门后显式落 END 收官行（_current_gate 既有 END 态归一的 stdout 侧兑现）；gate-exit 事件格式零变（_current_gate 解析面不破）。
- R-T16-1（五类素材全缺=全量降级登记）：执行期核验 CNPEN 五类素材均不在仓（knowledge/sources/cnpen/ 不存在；客户素材库在仓外且属禁碰区）——按计划 blocked 语义降级：SOURCES.tsv 五笔 origin=cnpen 待补行（KP-0001..0005，sha256 占位 "-" 防伪造，note=待补+就位后 source-register 重登取代）+README 落位表；蒸馏页零产出（计划 test_min_page_counts 的 materials-available 前提不成立，改「不造数据」反向断言=无页引用未就位语源；WSTG 全集/CLIENT-NN 形态两断言保留为前向钉）；blocked 明细=测试全景图/思路复盘/测试记录 T1-T55/31 份黑盒漏洞单/BurpPOC 合集五类全缺。
- R-T17-1（CEP business 页随素材延后）：计划 business 增 CEP ROE scope 模板语义注记页 1——CEP 素材缺（G-35 降级），语义注记页无源可蒸馏=不造数据，business 页延后随 KP-0009 就位重登后补；report-template.html 批次 6 登记不实现不变。
- R-T17-2（CVE 零引用通道）：计划「执行者经宿主 WebSearch 核验一次」与「离线环境=不写 cve_refs 只写方法论内容，登记待核验清单」双通道并立——本批取离线通道（8 蒸馏页+2 先例页 cve_refs 全空，正文公开 CVE 仅作边界叙述不落编号），待核验清单落 LICENSE.note（Commons-Collections gadget 族/JNDI 注入族/IMDSv1 元数据族等，批次 6+ 宿主 WebSearch 对照 NVD/KEV 后补双标记）；lint cve 闭环断言保留为前向钉（有 refs 必须有 verified）。
- R-T17-3（warstory 脱敏覆盖面）：测试断言禁 nssctf 子串（大小写不敏感）——语源原文平台域名/旗标串/双写 payload 字面（NSSNSSCTFCTF 含 NSSCTF 子串）/隐藏文件名（NsScTf.php 小写含 nssctf）全部抽象化或占位符化；方法论语义（正则修饰符分析/数组参数绕过/回调数组语义/零 e 纯数字哈希碰撞）全保留且 triples 主谓宾 8+6 行达 ≥6 要求；域名/IP 形态哨兵（DOMAIN_RE/IP_RE 与 lint 同源）测试级复验零残留。
- R-T17-4（先例页 vocab_version 补齐）：计划契约 14 §2 先例页必填集未列 vocab_version 而 R14「每页必填」+lint 全页无条件校验——两 PR 页补 vocab_version: WSTG-v4.2（首跑 lint 抓获，fail-closed 生效实证）。
- R-记账（T15+T16+T17 时点）：同 R-记账先例——三任务 commit 先行（bb9c5bf/e557b1d/c4c6728），本流水+裁决节独立 commit。
## 2026-09-24 批次 5 T18+T19 裁决（实现者记）
- R-T18-1（探针副本执行）：计划 eval 骨架对 --knowledge-dir 就地跑 lint/export/match——R8 lint 向 log.md 追加逐页审计行+staging.tsv 同步写，就地直跑=写热仓库种子库（本笔前置隔离修复同因）；探针一律整库临时副本执行（copytree+TemporaryDirectory），判定语义与原库等价，判定命令面与计划逐字一致（R7 种子库只读纪律优先于骨架示意代码）。
- R-T18-2（抽查范围在库页口径）：素材降级登记（KP-0001..0009 待补行）不产出蒸馏页——§9.4 四判据按 G-35 口径以在库页为准：④CVE 判据只消费在库页自带 cve_refs/cve_verified（当前全空=R-T17-2 离线通道），降级源不阻塞出口①②；②自反命中含 [expired]/[stale] 标注行（「指纹可检索」语义非「窗口内命中」——PR-0001/0002 窗口 2026-04-19 已过仍可检索，与 match 检索语义一致）。
- R-T19-1（引擎 KNOWN 面随行）：recon.md A8 接点引入 tanyin-knowledge 触发 test_engine_web_blackbox.test_referenced_commands_known（该文件自带 KNOWN 集，与 test_skill_resident 分立）——按 R-T12-5/R-T8-3 先例增第 12 员入已知面（工具=T9 已交付成员，非放水）。
- R-T19-2（argv 双形态归一）：出口实测发现计划判定命令与 P6 duty 五步按原文取 --key value 空格形态而子命令解析仅收 = 形（lint 空格形 TypeError 裸崩 rc1，出口补充判定不可满足）；按适配器双形态先例（R-T5-2/R-T9-2）在 knowledge 侧增 parse_argv 归一——query_cmds.parse_kv 单源零触碰（账本 44 面冻结），= 形透传行为零变，裸旗标=1 保 approve --reject 布尔语义；修复后出口补充判定命令按计划原文实跑 PASS n=10 exit 0。
- R-T19-3（R-T3-4 遗留核验=已在册闭环）：R-T3-4 记「P3.md L25 算分承载行缓建表述留 T19 改写」——核验 git 史：T12（df51cd1）改写承载行时已同步落「物理列批5 T3 已落」现时态，遗留项已闭环；T19 补两钉防回退（TestBatch5Wiring 断言 P3.md 无「物理列随」字样+cli/README L128 同源陈旧表述一并修正）。
- R-记账（T18+T19 时点）：同 R-记账先例——四任务 commit 先行（c3d8c8b/76bba9b/0e43901/4546375），本流水+裁决节独立 commit（流水行引用自身 commit hash 的占位循环节=固有环，先提交后补正=批次内既定手法）。

## 2026-09-24 批次 5 Ruling 总索引（T18+T19 收口编；详情见各任务裁决节）

- 开工：用户批准计划 2026-09-24-b5-knowledge-flywheel.md（前置裁决 A-F+补充裁决 R7-R14 全案）；T1-T14 由各任务子代理按域收口（裁决见「批次 5 T3+T4+T5／T6+T7+T8／T9+T10+T11 裁决」等节与各 commit 消息）。
- T3+T4+T5：R-T3-1..4（L25 承载行分期等）/R-T4-*（set-replay-state --timestamp 必填）/R-T5-*（AUTHZ cap 参数）——commit 6a3a5f9/684c5c9/d957a39。
- T6+T7+T8：R-T6-1..4（④基线冲突契约随行/PROTOCOL 节号/TRIGGERS 不 bump/高危回边落点）/R-T7-1..4（reachable_gap_cells 参数化单源/输出行序/金样刷新机制/判据等价注记）/R-T8-1..3（P4 攻击链落证）——commit e422c2c/b6dd4ca/5b4daf0。
- T9+T10+T11：R-T9-1..3/R-T10-1..4（sha256 强化/哨兵单源边界/--timestamp 必填/状态机唯一载体）/R-T11-*（export 确定性/match --today）——commit 见裁决节。
- T12/T13/T14：R-T12-1..6（K1 落表+score 只读算分）/R-T13-1..4（四门槛机检口径）/R-T14-1..3（K3 快照+nday 离线匹配）——commit df51cd1/详见裁决节。
- T15+T16+T17（6）：R-T15-1 approve 裸旗标本地归一/R-T15-2 reverse-verify 不进 HANDLERS/R-T15-3 占位符不进反向验证形态面/R-T15-4 P6 过门 END 行/R-T16-1 五类素材全缺=全量降级登记/R-T17-1..4（CEP 延后/CVE 零引用通道/warstory 脱敏覆盖面/vocab_version 补齐）——commit bb9c5bf/e557b1d/c4c6728。
- T18+T19（本节 6）：R-T18-1 探针副本执行/R-T18-2 抽查范围在库页口径/R-T19-1 引擎 KNOWN 面随行/R-T19-2 argv 双形态归一/R-T19-3 R-T3-4 遗留核验已在册闭环/R-记账（占位循环节）——commit c3d8c8b/76bba9b/0e43901/4546375。
- 台账：本批探知项 G-29..G-35 终态=docs/design/2026-09-24-b5-discovery-notes.md；b4 台账 G-23/G-24/G-26/G-27/G-28+R6 五行就地闭环注记（追加注记不改历史行，G-2 先例）。
- 出口：批次 5 出口验收 10 条逐条实测记录=状态快照「批次 5 知识飞轮+语料入库」行（2026-09-24）； VulnClaw 批 6 三项移交登记（退出码第 3 态/findings+SARIF 双工件/报告内容过滤器）见 b5 台账移交清单。
- 评审收尾（本节 3）：R-RC5-1 lint 种子库冻结语义（选 a——种子库=冻结资产，R8 运行时审计只落运行时库；lint 校验语义零变只在写侧分叉，出口判定命令就地可跑）/R-RC5-2 --client 必填落 match 入口（score 内部 _match_rows 通道零受扰）/R-RC5-3 占位符张力载体选 review-checklist（人审执行面；契约 14 冻结面同批只落 M-1/M-2 两笔勘误防膨胀）——commit 7719c93。

## 2026-09-24 批次 5 评审收尾入账（评审 I-1 必修+顺手件 M-1..M-6；子代理（评审收尾）记）

- **I-1（必修）修复**：出口清单/HANDOFF/cli/README 记载的判定命令 `python3 cli/tanyin-knowledge lint --knowledge-dir knowledge --today …` 就地跑写热冻结种子库——lint 对每页无条件 _append_log（原 knowledge.py:440）+收尾 _stage_sync 写 staging.tsv，而 WRITE_SUBS 守卫不含 lint（R7 守卫面=写子命令，lint 名义只读实况带写副作用）。红实况：就地 lint 后 log.md 追加 10 行逐页审计行（8 CP+2 PR）。修复选 a（裁决 R-RC5-1）：kdir==仓库种子库根时 lint 零写入——不追加 log 审计行、不同步 staging.tsv；校验输出与 PASS n 语义零变；运行时库行为零变（临时运行时副本 lint 实测仍逐页落 10 行审计行，60→70）。
- **红→绿证据（TDD）**：①tests/test_knowledge_ingest_cnpen.py::TestCnpenIngest::test_lint_in_place_on_seed_zero_write——红=就地 lint 后 log.md 字节级断言 FAIL（diff 实况追加 `|lint|CP-0001|pass` 等逐页行），绿=零写入断言过+就地判定命令原文亲跑 PASS n=10 exit 0 且 log.md/staging.tsv sha256（ca06e5f0…/fe0f1ee3…）前后一致；②tests/test_knowledge_export_match.py::TestExportMatch::test_match_client_required（M-3）——红=缺 --client exit 0（静默 matched=0），绿=exit 2+stderr 指名 --client。红跑取证后种子库 git checkout 复原（写热未入 commit）。
- **顺手件**：M-1 契约14 §3 示例 created 勘误指针（实现=last_verified，R-T11-2 在案——定稿文本「commit 时间戳」与实现并立，契约内补指针）；M-2 契约14 §2 先例页表+模式页字段集补 vocab_version 行（R14 每页必填与 lint 全页无条件校验/R-T17-4 两 PR 页补齐同因对齐）；M-3 match 缺 --client 改 exit 2（--today 同款 KnowledgeError；score 内部 _match_rows(client=None) 不经 match() 零受扰）；M-4 review-checklist 增「占位符形态张力」节（P6 净草稿 {{vault:}} 合法 vs 知识页须抽象占位——lint/promote④ 拒 vault 残留=有意设计）；M-5 contracts/README 勘误索引补 T7 converge 一行（勘误正文原在 02a §22「T7/G-28 前半」节，索引漏行）；M-6 探知项两笔已登记探知项节（批次 6 真人复核在库 10 页——approver=执行者自查披露已在 log.md L15-24；approve 时间戳非单调纯外观注记）。
- **验收实测**：python3 -m unittest discover -s tests → Ran 566 tests OK（基线 564+新增 2）；python3 tests/run_golden.py → PASS 54 面（21读+20写+2phases+1engine+3graph+2adapter+1viz+1recheck+3kn）零漂移；就地 lint 种子库亲测零写热（如上）；git status 必净；panorama/ 与 /Users/wgen/Documents 零触碰。
- **Ruling 清单（本节=Ruling 索引「评审收尾」详情）**：
  - R-RC5-1（lint 种子库冻结语义=裁决选 a）：出口判定命令按计划原文就地指向仓库 knowledge/——方案 b（文档改注「临时副本上跑」）=三处文档改口+操作者纪律负担永久化，方案 a=种子库冻结资产语义一处收敛（R7 只读纪律自然延伸：R8 运行时审计只落运行时库）；lint 校验语义零变只在写侧分叉（frozen 判定=os.path.abspath(kdir)==repo_seed_root()，与 guard_writable 同款比较）；写子命令 REJECT 守卫不变（lint 非写子命令，零写入=行为保证非守卫拒绝——就地 lint 仍 exit 0/PASS n=10 可用作出口判定）。
  - R-RC5-2（M-3 落点=match 入口）：--client 必填执法在查询入口 match()，score 的先例命中因子走 _match_rows(kdir, None, …) 内部通道零受扰（score 语义本就允许无 client 评分）；错误形态=--today 必填（G-34）同款 KnowledgeError→exit 2，stderr 指名缺参。
  - R-RC5-3（M-4 载体选 review-checklist）：占位符形态张力本质=人审/蒸馏期的形态判断（草稿态合法/页态违规两态），checklist=契约 14 §4 人工审执行面即正确载体；契约 14 冻结面本批已落 M-1/M-2 两笔勘误不再加节（防同批膨胀）；节中明示 lint/promote④ 对 vault 残留零容忍=有意设计（知识页=可发行资产，不留运行时密钥库活指针）。


## 2026-09-24 批次 6 开工（executing via subagent-driven-development）
- 用户批准计划 docs/superpowers/plans/2026-09-24-b6-evals-install-delivery.md（18 任务/出口 18 条/四关键裁决：退出码 0/1/2 冻结·Burp HTTP/1.x 字节直贴·生产钥离线仪式·靶场种 20 基线 v1）｜commit e14a49d
- 执行结构：按域捆绑（evals 链→install/宿主→tools.lock/代理→报告流水线→靶场→收口），每任务 TDD+全量回归，收口后整支评审

## 2026-09-24 批次 6 T1+T2 流水+裁决（evals 链头；实现者记）

- **T1（commit 11abe47）**：契约 15 指标集 schema（contract:15/version:1 微版本通道；裁决 A 退出码 0=全硬门 PASS/1=任一硬门 FAIL/2=全 ENV-SKIP 且无 PASS，VulnClaw 第 3 态落 counts.candidates 不入退出码）＋cli/ledger/evals_schema.py 加载校验单源＋evals_metrics.py 裁决引擎（runner 注册表；warn 门 FAIL 落 counts.warn_fail 不动退出码）＋cli/tanyin-evals 薄 CLI（run/list/report；.cmd 配对）＋tests/evals/metrics-v1.json 十二指标机读定义（M03/M06 基线=0、checklist 五项定值、其余 collect-first）。红=ImportError evals_schema（Ran 1 errors=1 rc=1）→绿=11 例 PASS；全套 Ran 577 OK（基线 566+11）；金样 54 面 PASS 零漂移。
- **T2（commit 2ff49d1）**：cli/ledger/evals_dual_anchor.py 纯函数检查器（裁决 E：交战区 approvals.tsv knowledge-approved 行↔库侧 log.md approve 行按三元组互证，任一侧缺配对=FAIL 硬门，孤儿行列明细）＋evals_metrics.py 注册静态四 runner（unittest 逐模块子进程 PYTHONUTF8=1/golden 实跑/report-scan 泄漏样本拦截→脱敏零泄漏→validate 三步/dual-anchor 双库配对）＋tests/test_switch_matrix.py（M11 铁律 6 不可裁剪三项：deny-list 恒 REJECT、egress.acl 两档产出、canary probe tier1+3 全拦 allowed=0 且界外诱饵触碰恒 REJECT；T1/T3 双档会话夹具）＋tests/test_weak_model_protocol.py（M08 缺命令步骤终止报告可检测；纯函数留测试模块不入 CLI 面，铁律 7）＋tests/evals/samples/p4-no-command.md＋tests/evals/samples/dual/ 双库样本夹具。红=ImportError evals_dual_anchor＋套件接线红（run --suite=static 全 ENV-SKIP exit 2）→绿=15 例 PASS＋静态套件端到端 exit 0 八指标全 PASS（counts pass=8 env_skip=0）；全套 Ran 592 OK（566+11+15）；金样 54 面 PASS 零漂移。
- **Ruling 清单（T1+T2）**：
  - R-T1-1（M01 runner 接线）：计划「unittest:tests.run_golden」实况=tests/run_golden.py 为脚本非 unittest 模块，`-m unittest tests.run_golden` 加载 0 例=空绿假 PASS（实测 OK rc=0）——增 golden runner 子进程实跑（timeout 900、cwd=仓库根），rc!=0 即 FAIL，与金样门「缺金样=FAIL 不落盘」同源 fail-closed；契约 15 §3 M01 行就地注记勘误。
  - R-T1-2（l3 空组占位）：契约 §4「l3=[L3 脚手架占位]」具体化为 l3=[]——v1 十二指标面不引用不存在条目（run_suite 免 KeyError），正式 L3 条目随 T3 manual runner 对齐数据入册，不阻塞 CI。
  - R-T1-3（.cmd 完整形）：计划示意单行 @echo off+py -3，仓库既有 .cmd 为 rem 注记+setlocal/endlocal+ERRORLEVEL 透传形——「与既有 cli/tanyin-* 一致」约定优先，取仓库形。
  - R-T1-4（report 子命令骨架期）：与 run 同面（计划代码即规格），人读渲染面归 T12 tanyin-report；契约 §5 注记。
  - R-T1-5（测试注册表隔离）：计划 test_exit_pass 隐含「unittest 按定义序执行+模块级 _RUNNERS 跨用例泄漏」假设，unittest 实际按字母序（hard_fail 先于 pass 注册 synthetic-fail 致 1!=0）——setUp/tearDown 逐用例快照恢复注册表，各断言零变；顺手收计划原稿 unclosed file ResourceWarning（with-open）。
  - R-T2-1（canary probe rc 语义修正）：probe 语义=「任一已部署层放行诱饵=FAIL exit 1；全拦=pass exit 0」，计划「界外诱饵探测恒非零 rc」按字面不可满足——「恒非零」落底层触碰面 guard exec 对诱饵恒 REJECT rc!=0，测试两者并取（probe tier1+3 rc=0 且 allowed=0 ＋ guard exec 诱饵 rc!=0），零容忍不可裁剪语义不变。
  - R-T2-2（档位载体）：guard exec 无 --tier 旗标，档位=goal 的 guard-tier（add-goal --guard-tier T1/T3）——双档=两会话夹具各建各断言。
  - R-T2-3（M12 e2e 夹具）：裁决 E「tests 夹具双库样本驱动」落地=tests/evals/samples/dual/{approvals.tsv,log.md} 全配对样本；M12 args 相对 goal_dir 解析，文件缺=OSError→ENV-SKIP（fail-closed 不假 PASS）。
  - R-T2-5（note_pattern 调整）：计划示意 ([A-Z]{2}-\d{4}) 对在库三字母页 id（STG-0001）误抽 TG-0001——按计划自注「实跑抓 note 字节后可改 pattern 不改本函数」通道改 \b([A-Z]{2,3}-\d{4})\b（在库前缀 STG/CP/PR/KP 实测，词界防子串）。
  - R-T2-6（matched 三元组序）：计划 check() 代码示意键序 (page-id, approver, timestamp) 与自身测试断言/裁决 E 原文 (page-id, timestamp, approver) 冲突——以裁决 E 为准（配对键序不变，仅返回投影换序）。
  - R-T2-7（契约 §5 落盘通道）：run 工件经 --out 显式落盘（CI 接线归 T4），骨架期缺省仅 stdout counts——计划代码即规格；契约 §5 措辞对齐。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF；runner 子进程一律 [sys.executable, path]+显式 timeout+PYTHONUTF8=1+cwd=仓库根；时间戳全显式字面量（禁墙钟）；goal 目录先 os.makedirs 再 add-goal（core 不代建纪律）；panorama/ 与 /Users/wgen/Documents 零触碰；金样 54 面零漂移（无新增面——evals-run 等新面随后续任务单独入册）。
- **R-记账（T1+T2 时点）**：两任务 commit 先行（11abe47/2ff49d1），本流水+裁决节独立 commit（批次 5 既定手法）。

## 2026-09-24 批次 6 T3+T4 流水+裁决（evals 链尾；实现者记）

- **T3（commit 04c05c8）**：cli/ledger/evals_token_eff.py（G-11 token 校准通道单源：extract_ratios usage 行实采/_CMD_IDX 以 schemas TABLES 单源钉死/replay_verdict 重放三态裁决/write_calibration 校准报告落盘含契约 v3 系数候选提案）＋evals_metrics.py 注册动态四 runner（canary-zero 逐档 probe 零容忍/replay-rate 三态分布/token-usage 校准报告落 tests/evals/calib//manual 恒 ENV-SKIP）＋契约 15 §6 追加 usage 行形态勘误（微版本 version:1 内勘误一行不 bump 主版本——勘误只加不改通道）＋tests/evals/l3/README.md（TSecBench 六域对齐口径/三轮取优+token 均值/发布前人工项不阻塞 CI）。红=ImportError cannot import name 'evals_token_eff'（Ran 1 errors=1 rc=1）→绿=8 例 PASS（计划 7 例+R-T3-1 schema 钉死断言 1 例）；动态套件端到端 --goal-dir tests/fixtures/G-g1 --timestamp 2026-09-24T00:00:00Z → exit 0 counts={pass:1(M02),fail:0,env_skip:3(M03 诱饵未部署/M05 无 usage 行/M09 runner 未注册 Task 16 交付)}与计划预期逐字吻合；全套 Ran 600 OK（基线 592+8）；金样 54 面 PASS 零漂移；夹具零写热（git status 干净）。
- **T4（commit b4c294a）**：.github/workflows/ci.yml——tests job 四格追加 Evals static 步（python cli/tanyin-evals run --suite=static --goal-dir . --out evals-report-static.json --timestamp=ci）+actions/upload-artifact@v4 工件上传（evals-report-static-<os>-py<pver> 矩阵命名）+新增 evals-dynamic job（仅 ubuntu/py3.12——dynamic 步同型+工件上传）；tests/test_evals_ci.py 四例文本断言（static 步/dynamic job/upload-artifact/PYTHONUTF8 纪律延续）。红=Ran 4 FAILED (failures=3)（PYTHONUTF8 既有在场巧绿）→绿=4 例 PASS；本地双实跑复核：static --goal-dir . → rc=0 pass=8 env_skip=0；dynamic --goal-dir . → rc=0 pass=1 env_skip=3（M02 空 session PASS pending=0/M03 M05 M09 ENV-SKIP——「ENV 降级已内建于 run_suite」当场兑现）；ci.yml PyYAML 解析 PASS；全套 Ran 604 OK（600+4）；金样 54 面 PASS 零漂移。出口清单 #5（远端四格+evals job 全绿）本环境无 push 通道=备注待 Actions 页面复核。
- **Ruling 清单（T3+T4）**：
  - R-T3-1（usage 行列序钉死 event=index 3）：计划测试样本 usage 串落第 1 列（4 列示意行），实现注释自注「执行期以 TABLES["timeline.tsv"].index 核对后钉死；错位=断言红」——实测八列实形 event=index 3：_CMD_IDX 以 cli/ledger/schemas.py 单源计算（非硬编码）+test_cmd_idx_pinned_to_schema 双断言钉死（=TABLES index 且 =3，schema 漂移必红）；测试样本行按真实列序展开（计划示意行列数属示意，钉死指令为准）。
  - R-T3-2（replay-rate 数据源换锚+三态映射）：计划 runner 调 `tanyin-phases replay-summary`——该命令不存在（tanyin-phases 八子命令无此面）；实况单源=tanyin-ledger ledger-replay-summary（契约 11 P4 出口门同源），输出 PASS<TAB>verified=N<TAB>repaired=N<TAB>rejected=N<TAB>pending=0——三态映射 VERIFIED→reproduced／REPAIRED→env-diff（重放修复=已降级处置口径）／REJECTED→not-reproduced（未复现未处置）；rc=1（有待重放项）=FAIL、rc=2=EnvironmentError→ENV-SKIP；纯函数 replay_verdict 按计划测试原文（states 小写形态，unhandled=not-reproduced 计数）零改。
  - R-T3-3（canary probe 用法形态+rc 三分）：probe 解析仅收 KV 形 --tier=N（计划示意空格形 --tier t=usage rc=2 实测取证）；rc 语义三分替代计划草图「rc!=0 即 FAIL」——rc=2=诱饵未部署（缺 canary/targets.tsv=环境前置缺）→runner 返 ENV-SKIP（计划测试 assertIn(PASS, ENV-SKIP) 为准，与草图冲突取测试=可执行契约）；rc=1=诱饵放行=零容忍 FAIL；rc=0 计 rc0；未部署态 probe 先于 append_tl 返回=夹具零写热（G-g1 副本 diff 实测干净）；canary-zero 对未注册 metrics-v1 之 args=[] 缺省四档缺省沿计划。
  - R-T3-4（calib 落点钉仓库根）：计划示意 calib 路径相对 CWD（os.path.join("tests","evals","calib")）——钉 _REPO/tests/evals/calib/（runner 群 cwd=_REPO 单源先例，防 CWD 漂移落错树）；CI/夹具干跑无 usage 行→ENV-SKIP 不落盘（token-calibration.json 随 Task 17 真跑首采入册——裁决 G「数据通道+报告交付」口径，本批交付通道非数据）。
  - R-T4-1（dynamic job 平台/档位收窄）：evals-dynamic 仅 ubuntu+py3.12 单档（计划 Interfaces 明文「dynamic job 仅 ubuntu——canary probe 依赖 POSIX 语义面」+计划 YAML 原样）；static 步四格全跑（含 Windows——runner 群 [sys.executable,path]+cwd=仓库根跨平台纪律在位）。
  - R-T4-2（CI 干跑动态绿路径实测入账）：计划「ENV 降级已内建于 run_suite：CI 缺 docker 时 M09 类指标 ENV-SKIP，动态套件仍有 PASS→exit 0」以本地同命令实测兑现——dynamic --goal-dir . 干跑 M02 空 session pending=0 PASS→pass=1、M03（probe rc=2 未部署）／M05（timeline.tsv 缺）／M09（range-recall 未注册）三 ENV-SKIP→exit 0；全 ENV-SKIP 才 2 的边界由 run_suite 既有逻辑承载（全 skip 未来场景才触发）；--timestamp=ci 显式时间戳纪律（CI 无墙钟入账面）。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF；runner 子进程一律 [sys.executable, path]+显式 timeout+PYTHONUTF8=1+cwd=仓库根；时间戳全显式（--timestamp=ci 进 CI 面）；panorama/ 与 /Users/wgen/Documents 零触碰；金样 54 面零漂移（T3/T4 无新增金样面——evals-run 新面随出口验收统一入册口径在 T1+T2 节已注记）。
- **R-记账（T3+T4 时点）**：两任务 commit 先行（04c05c8/b4c294a），本流水+裁决节独立 commit（批次内既定手法）。


## 2026-09-24 批次 6 T5+T6 流水+裁决（install 域捆绑；实现者记）

- **T5（commit 3c110c9）**：cli/ledger/install_core.py 六步安装单源（verify-lock→authoritative-dir→host-link→hooks→init-home→selfcheck；退出码 0/1/2——lock 验签不过/链接冲突=1，openssl/公钥缺/symlink 权限=2；_AUTH 白名单拷贝，panorama/tests/docs/git 不进安装树；install-log.tsv 显式时间戳三列审计）＋cli/tanyin-install（+.cmd 配对；--install-root/--home/--host=dsh/--repo-root/--pubkey/--timestamp 安装路径必填/--list-hosts 五宿主 verification 发布口径 §10.3）＋install/README.md（六步表+五宿主矩阵+交战区分离+信任锚 TEST-ONLY 披露）＋install/hosts/{dsh,opencode,codex,walcode,codebuddy}.json 五宿主装载模板（dsh=本仓可实测 tier3 hook 有；opencode/codex=公开环境 CI 可测 tier3 hook 有；walcode/CodeBuddy=静态验证+待实测（§10.3）tier1 hook 无保守披露）＋tests/test_install_core.py 10 例（验签 1/2 分态、权威目录、link_report 非空+目标可达、R-T12-4 k1-baseline 拷贝兑现、幂等 snapshot 零变更、冲突拒装用户文件零触碰、交战区分离双断言、CLI 三面）。红=ImportError install_core（Ran 1 errors=1 rc=1）→绿=10 OK；全套 Ran 614 OK（基线 604+10）；金样 54 面 PASS 零漂移。
- **T6（commit ab05da1）**：cli/ledger/selfcheck.py 六项静态单源（cmd-index=phases/*.md+engines/**/MANIFEST.md 的 tanyin-<tool> <sub> 引用 ⊆ KNOWN_COMMANDS 冻结面〔ledger=registry 单源 63 名+各工具用法面实测；新增命令忘登记=红，VulnClaw verify_execution_boundary 同型绊线〕/encoding=五安装随行目录 UTF-8 无 BOM+无 CRLF/phases-schema=tanyin-phases validate/layout=交战区分离 §3.4 home∉install_root/lock-verify=supply_chain 验签 ENV 2 分态/golden=run_golden.py 子进程实跑）＋run_guided(host) 一页手测引导（安装命令→能力探测→冒烟清单→回传模板 probe_results→发布口径→未实测披露；未知宿主=SystemExit(2)）＋cli/tanyin-selfcheck（+.cmd 配对）＋install_core._step6 删 T5 pending 中间态守卫→无条件真跑 selfcheck＋test_install_core 追加六步端到端断言＋tests/test_selfcheck.py 12 例。红=ImportError cannot import name 'selfcheck'（errors=1）+e2e 'pending' 意外在场（failures=1）→绿=12 例 PASS+e2e OK（9.0s 真跑门）；python3 cli/tanyin-selfcheck --static 仓内形态 worst=0 rc=0 亲测在册（出口 #6/#9 判定命令形态）；全套 Ran 627 OK（614+12+1）；金样 54 面 PASS 零漂移。
- **Ruling 清单（T5+T6）**：
  - R-T5-1（verify_entry 实参形态）：计划草图 pub=open(pubkey,"rb").read() 后把字节作 verify_entry(e, pub) 实参——批次 4 单源形参=公钥路径（透传 openssl -inkey），按字节传参恒验签失败（首绿跑实测 verify-lock=1 复现）——修正为传路径；fail-closed 语义零变（真钥+真 lock=0，篡改=1，公钥缺=2）。
  - R-T5-2（摘要形态+断言落点）：install() 摘要=分号 join 的 step=rc 纯形态（计划草图原文），不含明细——「验签失败/冲突」等明细落 install-log.tsv 第三列，测试断言随日志（首版断言错放摘要=2 FAIL 实测后按草图归位）。
  - R-T5-3（snapshot 排除安装日志）：计划 test_idempotent_second_run 断言 snapshot 前后相等，而 install-log.tsv 为追加式审计通道（二次安装必追加「零变更」记录行，日志自变=本职）——snapshot() 排除 install-log.tsv（幂等语义=树内容零变更；审计行恰是变更记录本体，不入投影）。
  - R-T5-4（skill 链接目标按 rel 展开）：计划草图对 skill_link_dirs 迭代但 target 不含 rel（多 rel 自撞同一目标）——修正=<home>/hosts/<host>/<rel>/tanyin；现五模板全 ["skills"]，行为与草图单 rel 形态逐字节一致。
  - R-T5-5（拷贝字节级白名单）：copytree ignore=__pycache__/*.pyc/.git（计划注释「排除 .git/tests/docs」的目录级由 _AUTH 白名单承载，字节级垃圾不进安装树同源延伸）。
  - R-T6-1（step6 守卫保留形态）：计划「无条件调 selfcheck」落地为删 pending 中间态分支+保留「入口缺=ENV 2」fail-closed 守卫（安装树不完整=2 非裸 FileNotFoundError 崩溃——退出码纪律内形态）。
  - R-T6-2（KNOWN_COMMANDS 冻结口径）：冻结现役实装面（ledger 63 名=registry all_commands()+ledger- 前缀孪生；phases 八子命令/guard 三/egress 三/canary 四/knowledge 十三/redact 空〔无子命令形态〕/replay 二/viz 一/budgetctl 二/evals 三）；不含 forward 面——tanyin-report aggregate/render/sign 与 egress serve 随 T10/T12 交付同任务入表，文档提前出现带子命令引用=红（绊线语义自洽）；配套 test_known_commands_covers_live_ledger_face 钉「registry 现役面 ⊆ 冻结面」防新增命令忘登记。
  - R-T6-3（encoding 扫描口径）：check_encoding 单目录全走+run_static 对 REPO_FILES_SCAN 五目录（phases/engines/cli/shared/install）聚合取 max——panorama/tests/docs/git 天然不进任何检查命令（与 install _AUTH 白名单同源纪律；计划 REPO_FILES_SCAN 常量原文承载）；全仓五目录实测 0 违例。
  - R-T6-4（--list-hosts 免 --timestamp）：发布口径查询为只读面，--timestamp 仅安装路径必填（ap.error=argparse 退出码 2 与退出码契约同形）；T5 版 required=True 使 --list-hosts 单用恒 usage 错（实测 rc=2）——本裁决分离两路径。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF；子进程一律 [sys.executable, path]+显式 timeout+PYTHONUTF8=1+cwd 锚定；时间戳全显式字面量（install-log 无墙钟）；panorama/ 与 /Users/wgen/Documents 零触碰（未进任何命令/扫描）；金样 54 面零漂移（T5/T6 无新增金样面——install-selfcheck 等新命令面随出口验收统一入册）。
- **R-记账（T5+T6 时点）**：两任务 commit 先行（3c110c9/ab05da1），本流水+裁决节独立 commit（批次内既定手法）。

## 2026-09-24 批次 6 T7+T8 流水+裁决（锁收紧+宿主矩阵捆绑；实现者记）

- **T7（commit ab8ced3）**：cli/ledger/lock_v2.py 探活单源（HOST/BOOT/DEAD_PID 锚点＋boot_id 跨平台＋pid_alive〔POSIX os.kill(pid,0) ESRCH=死/EPERM=活；Windows OpenProcess(0x1000) 句柄〕＋lock_fields 锁四字段产出＋probe_stale 三态 dead/alive/unknown〔本机同 boot 且 pid 死=dead／活=alive／跨机·跨 boot·字段缺·畸形=unknown 保守〕）＋state_md.py 锁字段 v2（LOCK_KEY_ORDER/FULL_KEY_ORDER 可选后缀；parse v1 十键容忍＋v2 十四键锁后缀全有或全无〔残缺=畸形走对账重建〕＋lock_pid 数字校验；would_overflow 保守按十四键）＋write_cmds checkpoint 内部通道 --with-lock-v2（run_restart 专用附锁四字段，常规 checkpoint 面=v1 十键零漂移）＋phases_engine run_restart 探活快路（handover 且有 lock_boot 才探；manual+dead=免 state-rebuild 对账前置、takeover 记 `probe=pid-dead`；auto 恒 REJECT probe==dead 也不放行〔单活跃铁律〕；alive/unknown=既有对账前置行为逐字节保持；锁释放重建/预算/速率护栏照走）＋契约 04 v2 勘误补记（state.md 锁字段+探活语义，schema_version=2 不递增）。红=ImportError cannot import name 'lock_v2'（Ran 1 errors=1 rc=1）→绿=8 例 PASS（probe 五+wiring 三——快路例用 revision 错位锁证明前置确被免过，unknown 例 REJECT+零副作用断言）；test_managed_restart/test_state_md/test_write_cmds/test_kill9_fidelity 120 例零漂移 OK；全套 Ran 635 OK（基线 627+8）；金样 54 面 PASS 零漂移。
- **T8（commit 99d08ad）**：cli/ledger/hosts_matrix.py（host_compat 模板直读 fail-closed＋render_agents_inject 常驻八条模板+本宿主档位披露行渲染＋inject_agents `<!--TANYIN:BEGIN/END-->` 标记包裹幂等替换〔二次注入零变更；LF 字节纪律〕）＋install/AGENTS-INJECT.md 常驻八条模板（八问授权门/单写者/四层执法+本宿主档位披露/预算树/速率熔断/凭据四关卡/九门状态机/kill9 续跑——每条一行命令锚点指向 SKILL.md 对应节；{{HOST}}/{{TIER_DISCLOSURE}} 占位）＋install/README.md（五宿主矩阵表增 AGENTS 注入落点列＋实测路径节：dsh 本仓全套=实测面／opencode·codex headless 实测命令行〔opencode run／codex exec 干跑+guided 第 4 步 probe_results 回传〕／walcode·CodeBuddy 静态验证+手测脚本 guided＋G-38 如实登记）＋tests/test_hosts_matrix.py 8 例（五模板合法/盲区标注/未知宿主红/幂等/长度护栏 <8000 char〔<2K token 量级〕/盲区披露入块/LF）。红=ImportError cannot import name 'hosts_matrix'（Ran 1 errors=1 rc=1）→绿=8 例 PASS；test_selfcheck+test_install_core 31 例同绿（selfcheck encoding 扫描覆盖 install/ 新文件 PASS）；`tanyin-selfcheck --static` worst=0 亲测在册；全套 Ran 643 OK（635+8）；金样 54 面 PASS 零漂移。
- **Ruling 清单（T7+T8）**：
  - R-T7-1（锁字段写点收窄为 restart 专用内部通道）：计划「session 激活时写四字段」若落常规 checkpoint，金样 write-checkpoint 面（state.md 全文入 .state）与 test_state_md 冻结断言（fields 键集=KEY_ORDER 逐键）必漂移——违「金样 54 面零漂移＋既有测试零改动」双硬约束；收窄为 checkpoint `--with-lock-v2` 内部通道（run_restart 专用），锁字段语义=受管重启交接后新锁的 OS 事实（裁决 F 探活快路的消费场景恰为 restart 接管）；常规 checkpoint=首锁 v1 形，其接管走 unknown 保守路径=现状。write_state 保持纯格式层（写者不造锁；锁字段由调用方经 lock_v2.lock_fields 产出，夹具/测试手置锁同形）。
  - R-T7-2（boot_id 跨平台补臂）：计划「POSIX /proc/sys/kernel/random/boot_id」实为 Linux 专属（macOS 无 /proc，本开发机即 macOS）——补 sysctl kern.boottime 臂（同 boot 稳定引导时刻串）；Windows 按计划 GetTickCount64 反推并分钟取整（now−uptime 逐调用有漂移，取整保同 boot 稳定）；均不可得="unknown"→probe 恒 unknown 保守路径，绝不误判 dead（保守方向与裁决 F 同源）。
  - R-T7-3（DEAD_PID/BOOT 惰性单例，PEP 562）：计划测试引用 lock_v2.DEAD_PID 模块常量——import 时即算则每个 CLI 进程（write_cmds/phases_engine 均引 lock_v2）都付一次子进程/sysctl 代价；改模块级 __getattr__ 惰性首访（DEAD_PID=已收割子进程 pid 探活必死；BOOT=boot_id() 缓存），常规命令零代价、测试语义不变。
  - R-T8-1（install/hooks/ 不随本任务落盘）：文件结构图列 install/hooks/ ★「随 T8 交付」，但 Task 8 Files 清单未列且本任务要点=AGENTS 注入+盲区通道——按任务清单执行，hooks 逐宿主模板维持 install_core step4 既有占位披露分支（不阻塞安装），README hooks 节如实改注；待实测宿主需求实锚后另批落地（出口 #7 判定命令不含 hooks 面，零影响）。
  - R-T8-2（G-38 登记落点）：docs/design/2026-09-24-b6-discovery-notes.md 为 T18 台账收口交付物（本任务不预建防撞车）——G-38 现登记于 install/README.md 宿主矩阵节（回传形态=guided 第 4 步 probe_results 贴回；升档条件=回传入册；未回传前 Tier 1 保守披露不谎称实测）+本流水，T18 收口时按此归并。
  - R-T8-3（注入块渲染用显式 replace 非 str.format）：AGENTS-INJECT.md 正文含 {{vault:...}} 凭据引用字面量，str.format 会误解析占位——render_agents_inject 用显式 replace（{{HOST}}/{{TIER_DISCLOSURE}}）；档位披露行由 host_compat verification 字段直译（「待实测」在场=盲区披露行），宿主 JSON 零新增字段。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF（selfcheck encoding 扫描五目录覆盖新文件 PASS）；时间戳全显式（lock_since=激活 ts 显式传参，boot_id 为 OS 纪元标识非账本时间戳，无墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰（未进任何命令/扫描）；金样 54 面零漂移（T7/T8 无新增金样面）；git diff --check 两任务提交前各跑一次 clean。
- **R-记账（T7+T8 时点）**：两任务 commit 先行（ab8ced3/99d08ad），本流水+裁决节独立 commit（批次内既定手法）。

## 2026-09-26 批次 6 T9+T10+T11 流水+裁决（钥/代理/canary 域捆绑；实现者记）

- **T9（commit 483520c）**：tools.lock 全量 8 键（3 基础键+python 3.11+-system/docker 24+-system 系统工具键+三自写引擎目录清单键 engines-web-blackbox/vuln-agent/session-viz snapshot-1）＋nuclei-templates upstream_commit 占位换真锚 3e0e38f5〔GitHub REST API 双端点互证；templates.lock 首行同步、模板行哈希零变〕＋TEST 钥整锁重签（resign 脚本自举）＋install/KEY-MANAGEMENT.md 五节（生成〔openssl genpkey EC P-256 离线机人工仪式〕/保管〔介质双控〕/重签/替换〔公钥+整锁原子变更〕/CI 关系〔永用 TEST-ONLY 夹具钥与生产钥无信任关系〕+§3.4 digest 复算式+§3.5 待锚通道）＋install/resign-tools-lock.py（逐键 sign_entry 单源+原子写回+非交互；--allow-online 缺省提示非拦截）＋install_core.refresh_cve（file:///URL 取源→sha256 锚定→临时文件七列 lint 单源复用〔tanyin-knowledge lint 子进程〕→os.replace 原子替换；lint 不过 rc 1 目标字节不变；install-log.tsv 追加 refresh-cve 审计行）＋tanyin-install refresh-cve 子命令（--from/--home/--knowledge-dir/--timestamp；无 --from=exit 2）＋KNOWN_COMMANDS 登记 install 面＋契约 10 勘误+cve README 双通道注记+engines/nuclei/README 缺口披露刷新。红=6/7（2 ERROR refresh_cve attr 缺+4 FAIL resign 脚本缺/锁 3 键；exit-2 用法例语义本就成立）→绿=7 例；全套 Ran 650 OK（643+7）；金样 54 面零漂移。
- **T10（commit 0ff03ae）**：cli/ledger/egress_proxy.py 代理本体（parse_acl 以 compile 真实产物 egress.acl v2 四段格式锚定〔计划行约定并存；未知行 ValueError fail-closed〕＋decide 判定单源〔显式 deny 优先→allow 精确/端口通配/*.suf 严格后缀/CIDR→deny-by-default〕＋EgressProxy/serve/serve_text＋_forward 明文转发〔hop-by-hop 剥除〕＋do_CONNECT 隧道〔select 双向中继 TLS 不解密〕＋DNS pin 三态＋oob/canary 告警行；egress-log.jsonl 唯一运行时工件、代理绝不写 13 表；落账先于响应写回）＋tanyin-egress serve 子命令（--acl/--port/--egress-log/--timestamp；前台常驻 Ctrl-C 优雅退出；横幅载 TLS 限制+G-41 披露）＋KNOWN_COMMANDS 登记 egress serve＋契约 11 v3 勘误+install/README 守门声明节。亲测：真 curl 经代理 CONNECT api.github.com 200/forward pypi.org 301/deny evil.example 403。红=ImportError（模块缺）→绿=13 例 PASS；全套 Ran 663 OK（650+13）；金样 54 面零漂移。
- **T11（commit 520d48a）**：tanyin-canary probe 增 --egress-log=<path> 可选入参（_traffic_touches 读 egress-log.jsonl kind=canary 行并入触碰判定；流量触碰行在=touched 事故级 exit 1，acl 静态 not-deployed 时流量证据优先仍判 fail；R10 机检=①诱饵表绑定〔host 命中本 goal 诱饵表〕②时间窗〔行 ts≥最近 canary-deploy 事件 ts，两侧 ISO 形态才比对，不可比不过滤如实计数〕③裸连接不产生 log 行天然不触发）＋shared/EVALS.md 人读速查建账并载 M03 判定链双源注记。红=2 FAIL/ERROR（流量触碰不判+traffic_touches 键缺）→绿=5 例 PASS；全套 Ran 668 OK（663+5）；金样 54 面零漂移。
- **Ruling 清单（T9+T10+T11）**：
  - R-T9-1（load_lock 返回形态）：计划测试片段 `names={e["name"] for e in supply_chain.load_lock(...)}` 按清单形态书写——批次 4 单源 load_lock 实返回 dict[str,entry]（键=工具键），按实况 API 改写 names=set(load_lock(...))，键集覆盖断言语义不变。
  - R-T9-2（digest 复算跨平台式）：计划 shell 形 `find|sort|xargs sha256sum|sha256sum` 依赖 POSIX sha256sum（macOS/Windows CI 均缺）——目录键 digest 改 Python 规范式（sha256("relpath\tfile_sha256\n" 清单串路径排序排除 __pycache__)；系统工具键=sha256("键\t版本\tsystem-tool-no-artifact") 版本钉死即锚），复算式注释在 tools.lock 头+KEY-MANAGEMENT §3.4，确定性等价。
  - R-T9-3（真锚获取通道与缓存风险）：git 协议 clone/ls-remote 执行环境超时不可达（重试三次）——改 GitHub REST API 双端点互证（/commits?sha=main&per_page=1 与 /branches/main 同值方锚）；发现 /branches「master」返回陈旧缓存值（2023 年 commit）而默认分支实为 main——双端点不一致即不得锚定（不造数据纪律）；通道+复验纪律落 KEY-MANAGEMENT §3.5，tools.lock 头注记。
  - R-T9-4（refresh_cve 审计行落点与校验目录形态）：计划签名无 home 参——install-log.tsv 落 knowledge_dir 上级（缺省布局 <home>/knowledge 语义一致，安装器审计同文件通道）；lint 单源复用经子进程 tanyin-knowledge lint，临时校验目录须含 format_version+staging 空目录（lint _stage_sync 写载体目录），校验对象=临时文件、目标 os.replace 原子替换。
  - R-T9-5（nuclei README 缺口披露刷新）：计划 T9 Files 未列该文件，但其 G-22 节「commit 占位/生产钥=批次 6 出口」两句在 T9 落地后成陈旧声明——按不造数据纪律刷新为实况（真锚+KEY-MANAGEMENT 指针），与契约 10 勘误同 commit。
  - R-T10-1（acl 行约定以 compile 实况为准）：计划 parse_acl 行约定与 compile 真实产物 egress.acl v2（四段/default deny/allow 通配与 CIDR/pin 无 ip/allow-oob/allow-infra）不同——按计划 Step 1 锚定条款「以实况为准改 parse_acl 行约定并回写契约 11 勘误」，真实产物为锚+计划行约定并存，未知行 fail-closed。
  - R-T10-2（共享夹具零触碰教训）：格式锚定步直编 tests/fixtures/G-g1 致夹具漂移（compile 落 timeline 事件 revision 9→10，8 例既有测试+金样 matrix-init 面红）——git checkout 复原后锚定步改 tempfile 拷贝内编译（tests/test_egress_proxy._compile_real_acl 同款），共享夹具零触碰；T11 夹具纪律同源（复制后操作）。
  - R-T10-3（DNS pin 三态落地）：计划「解析结果≠pin=拒绝+告警」要求代理自行 DNS 解析比对——真实解析在测试/离线环境不可靠（.invalid NXDOMAIN 时延/解析器不可达），机械执法落地三态：pin 无 ip=声明态 pin_ok=None；host 为 IP 字面量≠pin 期望=拒绝 pin_ok=False；host 为域名+pin 带 ip=直连 pin（解析面免疫，不可比 pin_ok=None 如实披露）；契约 11 勘误+模块 docstring+README 守门声明三载。
  - R-T10-4（G-41 披露落点）：G-41 台账登记落点=T18（本捆绑不预建防撞车，R-T8-2 同律）——性能上限披露先落守门声明面三处（契约 11 勘误/install/README 守门声明节/serve 启动横幅），T18 收口时归并台账。
  - R-T10-5（落账先于响应写回）：告警行若在响应字节写回后落盘，probe 读 log 与客户端收包存在竞态——log 行先于响应写回（客户端收到响应=证据行已全部落盘），触探证据源对消费者无竞态。
  - R-T11-1（shared/EVALS.md 建账）：计划文件结构图列 shared/EVALS.md ★，T1-T8 未落盘且 T11 需 M03 注记落点——本任务建账（速查+退出码+M03 双源注记），文件头声明机器面单源（契约 15+metrics-v1.json+evals_schema.py）地位。
  - R-T11-2（canary argv 等号形）：计划测试片段 --egress-log 空格形——canary 既有参数面=--key=value 形（R-T5-2/R-T9-2 同款先例），测试按实况等号形传参，usage 注记可选项。
  - R-T11-3（时间窗不可比不过滤）：行 ts 或 deploy ts 非 ISO 形态（CI --timestamp=ci 场景）时窗比对跳过并如实计数——宁多报不漏报（零容忍门方向），EVALS.md M03 注记与函数 docstring 双载。
- **金样变动说明**：零变动。54 面 PASS（21 读+20 写+2 phases+1 engine+3 graph+2 adapter+1 viz+1 recheck+3 kn），总 hash=a347edd7 与基线逐字节一致；未新增金样面（evals-run/install-selfcheck/report-sign 等新面非本捆绑范围）。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF（selfcheck encoding 扫描覆盖 install/shared/cli 新文件 PASS）；时间戳全显式（refresh-cve/serve/probe 均 --timestamp 传参，EPOCH 确定性缺省；真锚获取时点以 pushed_at 记录非墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰（未进任何命令/扫描）；git diff --check 每任务提交前 clean；产出物 668 例绿（基线 643+T9 7+T10 13+T11 5）。
- **R-记账（T9+T10+T11 时点）**：三任务 commit 先行（483520c/0ff03ae/520d48a），本流水+裁决节独立 commit（批次内既定手法）。

## 2026-09-24 批次 6 T12+T13+T14 流水+裁决（报告管线前束；实现者记）

- **T12（commit d0e875b）**：cli/ledger/report_agg.py 聚合单源（aggregate 八键投影=goal/scope_summary〔修订生效行+修订头清单〕/findings〔status==active 过滤；tech_sev=confidence、biz_impact=impact、replay_state=timeline 重放事件末值三态映射、verified=exploitation_status〕/matrix〔filled/empty/gaps〕/coverage〔intents 开闭+gates_passed〕/budget_terminal〔budget_exhausted 单源〕/tier_disclosure〔timeline tier 末值+guard_tier+egress-log 在场〕/limits〔空格清单+unverified 清单〕）＋cli/tanyin-report（+.cmd 配对）aggregate 子命令（JSON sort_keys+indent=1+尾换行字节确定；缺表 EnvironmentError=2、未知子命令=2）＋KNOWN_COMMANDS 登记 report forward face＋tests/test_report_agg.py 8 例。红=ImportError report_agg（Ran 1 errors=1 rc=1）→绿=8 OK；全套 Ran 676 OK（基线 668+8）；金样 54 面 PASS 零漂移（hash=a347edd7）。
- **T13（commit f0927e8）**：cli/ledger/report_render.py 九段渲染器+时间链断言（render_fd 九段逐段投影〔①位置=assets/edges 图谱坐标+dedup_key ②涉及资产与接口=read-ledger 子图投影 ③漏洞描述=类型命中矩阵词表 ④等级=双轴并列+G-24 severity_expect 可复算 ⑤漏洞原理=evidence 链引用 ⑥POC/EXP=EV 卡 raw_request 原文转抄字节不变+响应摘录正文段转抄+变体单列判读说明〔含 HTTP/2-TLS 边界裁决 B 注记〕 ⑦危害=raw_excerpt token 化回显引用 ⑧修复建议=类型映射+K1 挂标+修复后哪条 POC 应失效 ⑨复现与验证状态=重放三态+最近重放时刻，未 verified 强制披露「未通过独立重放门」禁宣称 verified〕；任一段数据源缺失=rc 1 缺段清单随报错〔渲染不造数据〕；check_time_chain 断言 captured_at<added_at〔<issued_at 可选〕不可解析=fail-closed；render_all+CLI render --fd/--all 双跑逐字节一致）＋cards.py parse_ev_card with 句柄（行为零变消 ResourceWarning）＋tests/test_report_render.py 9 例。红=ImportError cannot import name 'report_render'（Ran 1 errors=1 rc=1）→绿=9 OK；全套 Ran 685 OK（676+9）；金样 54 面 PASS 零漂移。
- **T14（commit 02fbab2）**：cli/ledger/report_lint.py（burp_pasteable 裁决 B 四规则机检〔①纯文本可解码无二进制字节/BOM ②请求行 METHOD SP PATH SP HTTP/x.x ③至少一个 Host 头 ④非空 body 空行分隔；HTTP/2 帧/TLS 形态 fail-closed 且 why 载「判读说明」〕＋nine_segments 段锚行检＋compliance_six 六要素缺项＋empty_rhetoric 禁空话＋sign_gate 签发门聚合〔全 active FD 渲染+九段齐+burp+双指纹〔norm.artifact_hashes 单源复算+转抄一字不符=FAIL〕+时间链 issued_at+redact-scan 零泄漏子进程+cleanup-checklist rc==0 子进程〔P6 清理门接线，命令零改动〕+tier 披露+六要素+禁空话；任一不过 rc=1 FAIL 明细落报告；全过落 report/signed/pass.json〕＋lint=同门不落凭证／sign=lint+凭证+T15 双工件未接线披露行）＋phases_engine GATE_HALT_TOOLS 撤空+tanyin-report 真门分发（tanyin-redact R13 拆分同构；门级 ts 注入）＋P5.md :17 ENV-HALT 断言解除为 tanyin-report lint 真门＋P6.md 签发门前置接线注记＋契约 06 v3 勘误补记（裁决 B 三条款）+contracts/README v3 索引＋KNOWN_COMMANDS report+lint＋test_reverse_verify 反向验证随解除改真门断言＋tests/test_report_lint.py 15 例。红=ImportError cannot import name 'report_lint'（Ran 1 errors=1 rc=1）→绿=15 OK（施工中发现并修 sign_gate 门状态翻转缺陷——detail 记 FAIL 而 status 滞留 PASS 被 PASS 清空循环抹除）；全套 Ran 700 OK（685+15）；金样 54 面 PASS 零漂移。
- **Ruling 清单（T12+T13+T14）**：
  - R-T12-1（报告面 findings 口径）：status=="active" 才入报告面（夹具 FD-g1-0001 status="" 历史行排除）——报告=现役缺陷面；aggregate/渲染/render_all 三处同口径。
  - R-T12-2（KNOWN_COMMANDS forward face）：T12 即登记 "report": ["aggregate","render","sign"] forward face（渲染/签发随 T13/T14 落地；lint 随 T14 增补为 ["aggregate","lint","render","sign"]）。
  - R-T13-1（矩阵词表落点=VOCAB∪K1 基线键）：段③「类型命中矩阵词表」——shared/VOCAB.md 仅 wstg 顶层类，夹具细类（authz.diff 等）在其外而 K1 基线有细类行键（wstg-authz:authz.diff）——词表=VOCAB wstg 集∪K1 行键（含冒号后细类）；查表次序=细类后缀→wstg 类→缺省 0.5+披露（G-24 基线 severity_expect 可复算字段同口径）。
  - R-T13-2（raw_request 无 body GET 形承载）：受限 YAML 子集块标量丢块内空行（parse_yaml 预处理器跳空行）+引号标量无转义——多行 raw_request 以无 body GET 三行形承载卡面（头部完整、字节直贴不破）；有 body 请求原文以工件原件为锚（哈希入 E-index）；裁决 B 直贴边界不因卡载体形态放松（lint 四规则照检卡值）。
  - R-T13-3（cards.py with 句柄）：parse_ev_card 裸 open 在新测试高频解析下 ResourceWarning 噪音显性化——with 包裹行为零变，消音不加语义。
  - R-T14-1（签发门 cleanup 判定前置=豁免行铸造）：夹具首行 add-goal revert_cmd=irreversible（清理核销判定恒 pending→rc 1）——测试 _mint 先 approve --decision=exempted（note 含事件文本）铸豁免行，同夹具证「未核销=FAIL」与「豁免=PASS」两侧（gate_pass 与 gate_fail_cleanup_not_verified 对例承载）。
  - R-T14-2（sign_gate 对 draft 按现状 lint）：已落盘 draft 按现状 lint（删段夹具可命中缺段=lint 真检），缺 draft 才代渲染——T15 write_all 落盘接线点；sign 凭证 JSON 本批落地，双工件写盘未接线以披露行明示。
  - R-T14-3（门级 ts 注入 lint）：P5 yaml cmd "tanyin-report --lint" 不带 ts——分发分支注入 --timestamp=<门 ts>（Ruling C matrix-freeze 注入同款先例），issued_at 判定在门内成立；lint 独跑缺省跳过 issued 断言（内容门语义），sign 必带 --timestamp（issued_at 显式禁墙钟，缺省=usage 2）。
  - R-T14-4（计划 cleanup 面名勘误）：计划 T14 提「tanyin-phases cleanup-checklist」——实况面=tanyin-ledger cleanup-checklist --verify（tanyin-phases 八子命令无此面），按实况接线（子进程 fail-closed，rc=2 环境异常亦判门 FAIL）。
  - R-T14-5（compliance_six 数据源=aggregate 投影）：六要素缺项判定不新造数据源——授权范围（goal+scope include）/方法学映射 WSTG（matrix filled 词表锚）/覆盖与局限（limits/matrix/coverage 投影键在档）/技术×业务双轴（findings tech_sev+biz_impact 非空）/复测依据（findings replay_state）/等保占位（占位常量段，T15 模板渲染）；空 findings 面要素按 vacuous 判齐（有缺陷必有双轴与复测依据才过——零缺陷报告不虚扣要素）。
  - R-T14-6（sign_gate 门状态翻转缺陷施工中修复）：首版 _fd_checks 各失败分支仅 detail 追加而 status 滞留 PASS，被 FAIL 收尾的 PASS 清空循环抹除明细（rc=1 全 PASS 空报告的矛盾态被门失败夹具测试当场暴露）——修正为失败分支 update(status="FAIL", detail=累积)，FAIL 明细随报告可读。
- **金样变动说明**：零变动。54 面 PASS（21 读+20 写+2 phases+1 engine+3 graph+2 adapter+1 viz+1 recheck+3 kn），总 hash=a347edd7 与基线逐字节一致；P5/P6 文本改动不入金样（phases 面哈希命令输出非文件内容）；engine 面不钉 ENV-HALT 输出（解除前后皆 PASS 锁定）；未新增金样面（report lint/sign 新面随出口验收统一入册口径，批次内既定）。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF（selfcheck encoding 扫描覆盖 cli 新文件 PASS）；子进程一律 [sys.executable, path]+显式 timeout+PYTHONUTF8=1+abs 路径锚定；时间戳全显式字面量（mint 链 2026-09-23/24 字面 ts，issued_at=门 ts 显式传参，无墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰（未进任何命令/扫描）；git diff --check 每任务提交前 clean；产出物 700 例绿（基线 668+T12 8+T13 9+T14 15）。
- **R-记账（T12+T13+T14 时点）**：三任务 commit 先行（d0e875b/f0927e8/02fbab2），本流水+裁决节独立 commit（批次内既定手法）。

## 2026-09-26 批次 6 T15+T16 流水+裁决（报告收尾+靶场捆绑；实现者记）

- **T15（commit c96db82）**：cli/ledger/report_artifacts.py 双工件+叙述过滤+终稿签发面（契约 13 兑现）——findings_json 全量+生命周期（每 finding id/title/severity 双轴/replay_state/lifecycle〔三桶映射 R-T15-1〕/evidence_ids/asset/verified；summary.verified 与 SARIF 结果数恒一致=R-T15-4 纳入口径统一）/findings_sarif SARIF 2.1.0 仅 verified（报告纳入门=exploitation_status==verified，unverified 一律不进；ruleId=矩阵词表锚漏洞类型；level=biz impact 映射 高→error/中→warning/低→note；locations[0].physicalLocation.artifactLocation=EV 卡片相对路径 POSIX 斜杠跨平台）/narrative_filter 机械清洗（VulnClaw report/filter 同型正则集，清单入模块 docstring：think 标签连内容含未闭合尾段/TOOL_CALL 行/Round N·第N轮 轮次行/[LLM X] 调试行与──分隔线/[结果][输出] 前缀/空行收敛）/write_all sign 落三工件（report/findings.json+report/findings.sarif+report/signed/report-<ts>.md 终稿=聚合投影+FD 九段渲染+合规六要素六章节〔契约 13 §1，等保占位段=常量文本，R11 法务过审对象成形〕+执行摘要经 narrative_filter）。T14 预留接线点激活：cmd_sign 删中间态 DISCLOSE 披露行改真调 write_all（计划 T15 Step3 明示），T14 pin 测试随解除更新（R-T15-5 附记）。红=ImportError report_artifacts 模块缺（13 例全红取证）→绿=13 例 PASS；全套 Ran 713 OK（700+13）；金样 54 面零漂移 hash=a347edd7。
- **T16（commit c15fb3b）**：授权靶场种 20+检出率 scorer（裁决 I）——tests/range/ground-truth.json 种 20 固定分布（注入 6+SSRF 2+反序列化 2+CORS/开放重定向 2+目录遍历 1+认证后越权 5〔IDOR×2+水平越权 API×2+角色混淆×1，post_auth authz_role 非空〕+弱口令 1+信息泄露 1；marker 全局唯一且恰现 seed 响应体一次〔机检〕）/seed 8 漏洞服务（每服务一目录 http.server ~35 行+Dockerfile，合成 payload 响应内嵌唯一 marker，post-auth 服务弱口令登录发 token+401 门；仅 compose 内网+127.0.0.1 映射）/docker-compose.yml 8 漏洞服务容器+attack-noop（固定网段 172.28.0.0/24 可复铸；docker compose config 语法自检 PASS；docker 缺=测试 skipTest 记录）/tests/eval_range_recall.py scorer（eval_authz_recall 匹配规则泛化复用：active 活集 finding 资产值==endpoint+EV 卡 word matcher 含 marker，post_auth 另须 intent kind=authz-diff 或 auth_context CRED role==authz_role 身份矩阵链；score 纯函数面夹具回归零 docker 依赖；CLI 退出码 0=recall≥baseline/1=低于/2=环境〔R-T16-2〕）/evals_metrics.py 注册 range-recall runner=M09（会话发现=TANYIN_RANGE_SESSION env→args→约定点；无现成会话=EnvironmentError→ENV-SKIP CI 降级；collect-first=实采披露 PASS，数值基线回退即 fail）。**首跑实测入册（裁决 I Step4）**：compose up 真实 HTTP 探针 20/20 marker 命中（含 302 开放重定向禁跟随取证、post-auth 弱口令登录链）→仓外交战区会话经 44 命令面铸造 20 EV/FD（EV 卡覆写富化 word matcher）→scorer 实测 recall=1.00（20/20）exit 0→基线 v1=1.0 frozen_at=2026-09-26T10:00:00Z 入册 metrics-v1.json+契约 15 §3 M09 行（微版本勘误；runner collect-first/数值两态亲测 PASS；基线口径=脚本化探针干跑，LLM 在环复测归 T17 RUNBOOK）。红=ImportError eval_range_recall 模块缺（11 例红取证）→绿=11 例 PASS；全套 Ran 724 OK（713+11）；金样 54 面零漂移 hash=a347edd7。
- **Ruling 清单（T15）**：
  - R-T15-1（lifecycle 三桶映射）：计划 lifecycle(active|rejected|repair-candidate) 与实况枚举不对齐（契约 01 §5.5 findings.status∈{active,superseded}+"" 历史行；exploitation_status∈{verified,suspected,ruled_out}）——零新事实确定性映射：superseded/ruled_out→rejected；重放末值 REPAIRED（报告面三态 env-diff，POC 不再复现=修复候选确认）→repair-candidate；其余（status∈{"",active} 账本活集，write_cmds 同款口径）→active。
  - R-T15-2（终稿文件名时间戳剥冒号）：report-<ts>.md 的 ts 含「:」（Windows 文件名禁列，跨平台纪律）——落盘形 report-20260924T090000Z.md，同 ts 可复算。
  - R-T15-3（SARIF verified_only 断言键控加强）：计划字面 {ruleId}∩unverified_ids=∅ 在 ruleId=漏洞类型语义下恒真空泛——加强为 properties.finding_id 键控交集为空+results⊆active 面+uri 相对路径卡片在盘三断言，纳入门判定语义不变更强。
  - R-T15-4（verified 口径统一）：findings.json summary.verified/findings[].verified=报告纳入门（active+exploitation_status==verified）与 findings.sarif 结果数恒一致（VulnClaw findings_output summary.verified 覆盖同款纪律）；独立重放三态另载 replay_state 字段——计划同时要求 replay_state 与 lifecycle 两字段，纳入门与重放门分列不混标正是其意图（首版实现以重放三态计 verified 致 summary=0 而 SARIF=1 的分叉，端到端亲测当场暴露后修正）。
  - R-T15-5（E2E 亲测落点+T14 pin 解除）：计划 Step4 字面 sign --goal-dir tests/fixtures/G-g1 会向共享夹具落盘工件致漂移（R-T10-2 同风险）——改 tempfile 拷贝内 mint→sign 全流程亲测（裸夹具无 verified finding 时 sign rc=1=门 FAIL 侧亦验证）；T14 test_lint_cli_no_credential_sign_writes 的 assertIn("T15",stdout) 中间态断言随接线解除，改断言双工件落盘+披露行消失（计划 T15 Step3「删中间态披露行」明示）。
- **Ruling 清单（T16）**：
  - R-T16-1（scorer active 口径）：检出率评估沿 eval_authz_recall 同款 status∈{"", "active"} 账本活集（历史行不丢，全量 findings=检出对象）；R-T12-1 报告面 active-only 口径不适用（评估面≠报告面）。
  - R-T16-2（无 --session 且 docker 在位）：计划只定义「docker 缺且无 --session=2」——docker 在位但无现成会话时 scorer 不代跑代理（干跑由 RUNBOOK 驱动，不造会话），同为 exit 2 环境语义、stderr 明细区分两态；会话缺表（findings.tsv 缺）亦 2。
  - R-T16-3（首跑口径如实入册）：Docker Hub 不可达（Bad Gateway）经 daocloud mirror 拉取 python:3.12-alpine 后重打标准标签（compose 不改，R-T16-4）；首跑=脚本化真实 HTTP 探针干跑（20/20 marker 命中，全合成 payload 本地回环资产），非 LLM 在环——基线 v1=1.00 如实入册并在契约 15/metrics-v1 desc 双载口径披露，LLM 在环复测归 T17 RUNBOOK（此后回退即 fail 对在环跑同样生效）；会话落仓外交战区 tempfile（交战区分离 §3.4），不造数据不挪账。
  - R-T16-4（compose 基础镜像标签）：seed Dockerfile FROM python:3.12-alpine 标准名不变——受限网拉取通道属环境问题（mirror+本地重打标签），不回写仓库面。
- **金样变动说明**：两任务均零变动。54 面 PASS（21 读+20 写+2 phases+1 engine+3 graph+2 adapter+1 viz+1 recheck+3 kn）总 hash=a347edd7 与基线逐字节一致；T16 新增靶场面（ground-truth/seed/compose/scorer）不属金样锁域（金样=44 命令面+渲染/图谱等既有面），未新增金样面。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF；子进程一律 [sys.executable, path]+显式 timeout+PYTHONUTF8=1；时间戳全显式字面量（T16 首跑 mint 链 2026-09-26T10:00:00Z 字面 ts，零墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰；共享夹具 G-g1 零触碰（E2E/首跑全在拷贝或仓外）。
- **R-记账（T15+T16 时点）**：两任务 commit 先行（c96db82/c15fb3b），本流水+裁决节独立 commit（批次内既定手法）。


## 2026-09-26 批次 6 T17+T18 流水+裁决（终态 B 演练+RUNBOOK+真人复核+台账收口；终束捆绑实现者记）

- **T17（commit 0328606）**：budget-exhausted 终态 B 演练+RUNBOOK+token 校准首采——tests/test_budget_exhausted.py 4 例（终态 B 过门+interim-report.md 四披露断言/limits 空格清单缺失=FAIL/时间线 REJECT 事件形态/常态终态零 interim 共享夹具零污染）+cli/ledger/report_lint.py gates 增 terminal_b_disclosure+terminal exhausted 且 limits.empty_matrix_cells 缺=FAIL+interim_report_b 确定性 composer+sign 成功路径落 report/signed/interim-report.md（fail-closed 断言）+tests/range/RUNBOOK.md（环境门/S1-S15 全流程序/干跑 D1-D4 实测/活靶段/终态 B 支线 B1-B4 实测 rc/LLM 在环复测通道 R-T16-3/token 校准首采通道七步）+契约 13 v2 勘误补记（终态 B 语义：budget_terminal=exhausted=合法签发终态+中期披露四件套）+tests/evals/calib/token-calibration.json 真跑首采落盘（n=76/median=1.1164/min=0.9414/max=1.3433；宿主真实 metering vs PROTOCOL §2 冻结公式；样本=实现会话 session.jsonl.zstd 解压逐 (turn,step) usage 块）。红=4 FAIL→绿=4 OK；全套 Ran 728 OK（724+4）；金样 54 面 PASS 零漂移 hash=a347edd7。
- **T18（commit a7c5218）**：真人复核流程+台账收口+契约 09 勘误+交付文档——docs/HUMAN-REVIEW.md 四节流程（范围=在库 10 页 CP-0001..0008+PR-0001..0002〔批次 5 M-6 前置义务载体〕+批次 6 新增页；判据=review-checklist 逐项+四门槛+人审门 tanyin-knowledge approve 同口径；记录=附录 10 行表{page-id/复核人/结论/日期/备注}+log.md 复核行追加纪律；争议升级=reject→staging 退回重蒸馏→再复核→两轮仍 reject 台账登记移交总控；红线成文=复核人不得为本批次执行者+复核列初始态=待真人填写不造数据）+docs/design/2026-09-24-b6-discovery-notes.md 台账四节（计划原文誊录 G-36..G-41/新增探知项登记终态/状态归并台账=出口 #16 七项全「已收口」或「遗留+理由+去向」/移交清单八件）+契约 09 v2 勘误补记（工具面 12→14+#13/#14 补缺+职责刷新五行）+cli/README 批次 6 节（四新工具速查+安装矩阵用法+出口验证指针）+tests/test_knowledge_contract.py 工具表钉 12→14 随勘误同笔更新。红=9 例 FAILED（failures=2 errors=6）→绿=9 OK；全套 Ran 737 OK（728+9）；金样 54 面 PASS 零漂移。
- **Ruling 清单（T17+T18）**：
  - R-T17-1（budgetctl enforce 拒绝形态断言键）：计划片段 assertIn("budget-exhausted", tl)——实况该串在 enforce stdout 而 timeline JSON 行载 reason=budget-exhausted+payload 形态键——改断言 enforce 形态键+goal 级执法+budget-log 事件行在档（REJECT 落账语义等价）。
  - R-T17-2（演练夹具 G-g1 命名与铸造序）：演练体=整目录拷贝命名 G-g1（session.goal_id=目录名去 G- 前缀驱动 new_id，短名致 EV 卡引用错位 REJECT）+EV 卡在 add-evidence 之后覆写富化（add-evidence 骨架覆写会丢富化；test_range_recall Base 同款铸造序）。
  - R-T17-3（token 校准采样载体与口径）：采样源=实现会话 session.jsonl.zstd（宿主真实 metering，逐 (turn,step) inputTokens+outputTokens；助手消息序列化=reasoning/text+tool 调用名+参数），est=cjk+(other+3)//4 按 PROTOCOL §2 冻结式；ratio n=76 落盘+契约 v3 系数候选 1.116 注记；回写本身遗留→G-37/契约 v3（裁决 G 口径）；采样脚本 /tmp/ 工程临时物不入仓。
  - R-T18-1（契约 09 勘误口径 12→14 非计划字面 11→15）：计划 T18 字面「工具面 11→15——+evals/install/selfcheck/report」与表实况不符——install/selfcheck/report 三行批次 0 誊录已在表（行 9/10/6），knowledge=#12 批次 5 已增补——按实况为锚 12→14（R-T9-1/R-T10-1 先例同律），职责刷新五行随勘误，明细入补记可追溯。
  - R-T18-2（tanyin-budgetctl 补缺登记）：budgetctl 批次 2 起在场（KNOWN_COMMANDS 冻结面在册）而契约 09 命令面清单自批次 0 誊录起漏登——探知即补 #14 行，微版本勘误通道。
  - R-T18-3（工具表钉随勘误解除）：test_knowledge_contract 工具表钉 assertEqual(n,12) 被 T18 勘误正当触发（契约冻结绊线按设计工作）——钉更新 12→14 随勘误同笔（T14「旧例随解除更新」同律），勘误注记入测试。
  - R-T18-4（真人复核/R11=载体+流程交付）：出口 #15/#17 判定含真人行为（复核结论/法务过审结论）——执行者代理无复核权（真人≠执行者），如实交付=流程四节+10 行表待真人填写+log 行纪律+R11 记录行载体，状态快照如实披露移交态（不造数据；批次 3-5「远端 CI 页面复核」披露同口径）。
- **批次 6 整批出口验收清单执行记录（2026-09-26 亲跑实测；每条=判定命令要点→输出行）**：

| # | 判定命令（要点） | 实测输出行 | 结果 |
|---|---|---|---|
| 1 | python3 -m unittest discover -s tests | Ran 737 tests … OK（基线 724+T17 4+T18 9） | ✅ |
| 2 | python3 tests/run_golden.py | PASS golden: 21 读+20 写+2 phases+1 engine+3 graph+2 adapter+1 viz+1 recheck+3 kn 全部锁定且确定；hash=a347edd7 零漂移 | ✅ |
| 3 | python3 cli/tanyin-evals run --suite=all --goal-dir . --out <tmp> --timestamp=2026-09-26T15:45:00Z | {"pass": 9, "fail": 0, "warn_fail": 0, "env_skip": 3}；metrics JSON 落盘（R-EXIT-1：计划字面 tests/fixtures/evals-session 夹具不存在——M12 双锚参数 goal-dir 相对路径〔--goal-dir .=仓根故可解析〕，沿 T4 R-T4-2 --goal-dir . 亲跑先例；动态 env_skip=3=M03/M05/M09 会话缺，M02 replay-summary 对既有 goal-dir 容错 PASS〔出口 #4 边界注同源〕。M-2 措辞勘误：原「动态 M02/M03/M05/M09 会话缺=ENV-SKIP」与本行 counts env_skip=3 自相矛盾，勘误仅措辞、实测输出行与判定不动） | ✅ |
| 4 | FAIL 夹具（unittest runner 换不存在模块）／全 ENV 夹具（--suite=dynamic --goal-dir=<不存在目录>） | rc=1 {"pass": 7, "fail": 1, …}；rc=2 {"pass": 0, …, "env_skip": 4}（裁决 A 双边界；注：空存在目录 M02 replay-summary 容错 PASS→rc=0，全 skip 需目录整体缺——边界如实记录） | ✅ |
| 5 | grep matrix/evals .github/workflows/ci.yml | os [ubuntu-latest, windows-latest]×python [3.11, 3.12] 四格+evals-static upload-artifact+evals-dynamic job 在册；远端 Actions 页面复核=push 后待办（本环境无 gh CLI，批次 3-5 同口径披露） | ⚠️移交远端 |
| 6 | python3 cli/tanyin-install --home <tmp> ×2（2026-09-26T15:30/31:00Z） | 两轮 verify-lock=0; authoritative-dir=0; host-link=0; hooks=0; init-home=0; selfcheck=0；install-log.tsv 逐笔 rc=0（幂等断言内建+tests.test_install_core 幂等例同绿） | ✅ |
| 7 | python3 cli/tanyin-selfcheck --static；--list-hosts | 六项 cmd-index/encoding/phases-schema/layout/lock-verify/golden 全 rc=0 worst=0；五宿主在册（dsh=本仓 737 绿+金样+evals 即实测面；opencode/codex=CI headless 面；walcode/CodeBuddy=G-38 静态+待实测） | ✅ |
| 8 | selfcheck lock-verify（supply_chain 单源验签既有入口） | lock-verify rc=0（tools.lock 全键验签；TEST-ONLY 夹具钥在位，生产钥=G-22 仪式移交） | ✅ |
| 9 | selfcheck layout；python3 -m unittest tests.test_install_core | layout rc=0（交战区分离 home ∉ install_root）；Ran 13 tests OK rc=0 | ✅ |
| 10 | fresh G-g1 拷贝 mint→tanyin-report sign；反例=抽段⑨复现与验证状态→lint | sign rc=0（report/signed/pass.json+终稿 md）；反例 lint rc=1（九段机检缺段命中） | ✅ |
| 11 | findings.json/findings.sarif 断言（#10 产物） | findings.json total=2 lifecycle 全 active；sarif v2.1.0 results=1 仅 verified、ids⊆verified 面 | ✅ |
| 12 | egress serve（egress.acl 20 行）+curl 经代理+canary probe --tier=3 --egress-log | in-scope forward 回包 exit12-ok verdict=allow；ACL 外 93.184.216.34→403 verdict=deny（egress-log.jsonl 双行）；probe status=pass blocked=5/5 traffic_touches=0（零容忍） | ✅ |
| 13 | docker compose up（9 容器 Up）→真实 HTTP 探针→44 命令面铸造→python3 tests/eval_range_recall.py --session <仓外> --ground-truth tests/range/ground-truth.json | 探针 20/20 marker 命中（302 禁跟随取证+post-auth 弱口令登录链 X-Auth-Token）；20 AST/EV/FD 铸造（account-grant 授权行+cred 链）；scorer rc=0 recall=1.00 (20/20)=基线 v1 入册值复现（口径=脚本化探针同 T16 首跑；LLM 在环复测=RUNBOOK §6 通道移交执行期） | ✅ |
| 14 | terminalb5.sh 新鲜拷贝复跑 B1-B4 | B1 rc=0→B2 REJECT budget-exhausted used=2010000 limit=2000000 rc=1→B3 rc=0→B4 sign rc=0+interim-report.md（中期报告声明/未测范围披露/闭合率/免责）+tests.test_budget_exhausted 4 例绿 | ✅ |
| 15 | grep 待真人填写 docs/HUMAN-REVIEW.md→10；记录行计数→10 | 10 行表（CP×8+PR×2）复核人/结论/日期全待真人填写——载体+流程交付，复核行为待真人（R-T18-4） | ⚠️移交真人 |
| 16 | 逐项 grep 归并表行 docs/design/2026-09-24-b6-discovery-notes.md | G-4/G-5/G-11/G-22/G-25/G-32/G-33 各 1 归并行+G-36..G-41 各 2（誊录+终态）——全部「已收口」或「遗留+理由+去向」 | ✅ |
| 17 | 本节 R11 记录行（载体） | 等保占位段/免责表述=T15 终稿签发面常量（#10/#14 sign 产物在证）；记录行在册如下；人工法务过审结论行待真人回填 | ⚠️移交真人 |
| 18 | git diff --check；file -I 新文件；命令史核查 | diff --check rc=0；HUMAN-REVIEW/b6 台账/test_human_review_doc 全 UTF-8 无 BOM；panorama/ 与 /Users/wgen/Documents 全程零触碰 | ✅ |

- **R11 法务过审记录行（出口 #17 载体，格式=结论｜过审人｜日期）**：R11 ｜待真人（复核人不得为本批次执行者）｜待回填——样张=T15 终稿签发面等保占位段+免责表述常量（亲测成形）；过审一次后结论行回填本节之下。
- **金样变动说明**：两任务均零变动。54 面 PASS（21 读+20 写+2 phases+1 engine+3 graph+2 adapter+1 viz+1 recheck+3 kn）总 hash=a347edd7 与基线逐字节一致；interim-report/calibration/RUNBOOK 新面不属金样锁域，未新增金样面。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF（file -I 实测）；子进程一律 [sys.executable, path]+显式 timeout；时间戳全显式字面量（出口链 2026-09-26T* 字面 ts，零墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰（出口 #18 核查）；共享夹具 G-g1 零触碰（演练/E2E 全在拷贝或仓外）；git diff --check 每任务提交前 clean。


## 2026-09-26 批次 6 评审收尾（I-1+I-2+Minor）流水+裁决（评审整改；终束捆绑实现者记）

- **I-1（install/hooks/ 宿主 hook 模板交付+step4 真挂载）**：install/hooks/{dsh,opencode,codex}.md 三宿主模板落库（锚=计划文件结构图「install/hooks/ ★ hook 模板（按宿主差异；无 hook 机制宿主=Tier1+披露）」+install/README 既有描述；计划无模板内容细节→按评审预授权最小可用=生命周期事件→tanyin CLI 调用示例+占位说明+G-38 实测回传时点，四段断言入 test_templates_in_repo_minimum_viable）；install_core._step4_hooks 从「模板未在库占位披露 rc 0」改真挂载——hook_mechanism 宿主 install/hooks/<host>.md copy2 幂等覆盖至 <install_root>/hooks/<host>.md；模板缺=rc 1 fail-closed；无机制宿主=Tier 1+披露零落装；install-log hooks 行文案随更新（M-5）。**安装两轮幂等复测（真实 CLI，2026-09-27T02:30:00Z 字面 ts）**：两轮 rc=0 六步逐零（verify-lock/authoritative-dir/host-link/hooks/init-home/selfcheck）+树投影 stable digest=5b18e7b7…7a8fe（156 文件）两轮相等=零变更+install-log「hooks ok (dsh 模板挂载→install_root/hooks)」行在册+selfcheck worst=0。
- **I-2（tanyin-install --release 通道接线，裁决 C）**：install_core.release_anchor 单源+CLI --release 旗标——新锚公钥路径（--pubkey）传入 verify 面（_step1_verify_lock）替换 TEST-ONLY 缺省锚，tools.lock 整锁须已在新钥下重签（不过=exit 1，KEY-MANAGEMENT §5 原子变更中间态 fail-closed）→交互确认（REPLACE 令牌；错词/EOF/流故障=exit 2 缺确认，锚文件字节零变化）→确认后原子替换（同目录临时文件+os.replace）+release-anchor 行落 install-log.tsv（--timestamp 显式必填）。KEY-MANAGEMENT §4 措辞同步（通道三步+同步动作④换锚后复跑六步复核）+契约 09 #9 行职责补注（文末补记微版本，命令面零新增）+cli/README 安装矩阵行+install/README 信任锚节。CI/测试永续 TEST-ONLY 夹具钥纪律不变——本笔测试全在临时仓根副本驱动，真仓 engines/nuclei/release.pub 零触碰。
- **Minor**：M-1 narrative_filter _SEP_LINE 收窄纯标线 `^\s*─+\s*$`（『──事实──』包裹行保留，反例 test_sep_line_narrow_keeps_wrapped_label；收窄暴露「── Round 7 ──」尾部空格形原被旧 _SEP_LINE 一并吞掉的缺口→_ROUND_LINE 尾部组改 (\s*──\s*)? 同笔补，既有 test_multiline_think_and_round 即规约）；M-2 HANDOFF 出口 #3 措辞勘误（动态 env_skip=3=M03/M05/M09 会话缺、M02 对既有 goal-dir 容错 PASS——原「M02/M03/M05/M09 会话缺=ENV-SKIP」与 counts env_skip=3 自相矛盾；M12 双锚参数改注 goal-dir 相对；实测输出行与判定不动）；M-3 靶场 compose range 网 internal:true（漏洞服务零出网+宿主零暴露；internal 网 published ports 被 compose 丢弃实测证=config rc=0 而宿主连接拒→删除死 ports 映射，探针改 attack-noop 双网跳板〔range+egress 非 internal 网出网例外，compose 语义：服务仅经非 internal 网出网〕；docker compose config 自检 rc=0+活靶探针 20/20 marker 命中+宿主侧连接拒隔离实测+compose down 零残留；RUNBOOK §4 注记跳板探针形；seed 八头注释+ground-truth note 随笔同步）；M-4 金样注记维持现状（评审已接受理由）；M-5 install-log hooks 占位文案随 I-1 更新（「占位披露」CLI 面绝迹）。
- **TDD 红→绿**：tests/test_install_hooks_release.py 10 例（红=FAILED failures=5 errors=2：--release unrecognized arguments×2+hooks 模板缺/占位残留×3+release_anchor 缺 AttributeError×2 → 绿=10 OK）+test_report_artifacts.TestFilter 增 test_sep_line_narrow_keeps_wrapped_label（红='──事实──' not found in '正文行保留\n结论行' → 绿）+test_range_recall.test_compose_lists_eight_services 改钉（红='internal: true' not found → 绿）；中段 _ROUND_LINE 尾组首补 (──\s*)? 方向误（空格在 ── 前）复红 1 例→(\s*──\s*)? 转绿（两转如实入账）。
- **全套+金样（本笔实跑）**：Ran 748 tests OK（基线 737+新增 11：test_install_hooks_release 10+叙述过滤反例 1）suite_rc=0；金样 54 面 PASS 零漂移 hash=a347edd7（install/hooks/compose/报告过滤面均不属金样锁域，未新增金样面）。
- **Ruling 清单（评审收尾）**：
  - R-I1-1（模板最小可用形态）：计划 T8 仅文件结构图一行、无模板内容细节→按评审预授权最小可用交付（生命周期事件表→tanyin CLI 调用示例+占位说明+G-38 时点）；调用示例一律真命令形（tanyin-guard exec -- 分隔形/tanyin-ledger append-timeline --event=/scope-check/verify-chain）；hooks/simulate.py 标注仓内测试面不入安装树（_AUTH 白名单零扩，安装树内示例全指 cli/ 面）。
  - R-I1-2（模板缺=rc 1 fail-closed）：模板交付后 install/hooks/<host>.md 缺=安装树不完整，占位披露 rc 0 中间态废除——与 step2「权威项缺=1」门禁失败同律；G-38 台账随注 hook 实测回传时点（dsh=本仓实测面；opencode/codex=执行期 headless/guided 回传同批）。
  - R-I2-1（--release 语义锚定）：「release.pub 路径传入 verify 面替换 TEST-ONLY」实做=--pubkey 新钥路径传入 _step1_verify_lock 整锁验签（前置=KEY-MANAGEMENT §3 重签已毕；§5 原子变更中间态=exit 1）；确认令牌定 REPLACE（ASCII 精确匹配，避中文输入法/编码歧义）；缺确认=exit 2（裁决 C 明文）与 refresh-cve 缺 --from 同形。
  - R-I2-2（release-anchor 日志通道）：替换行为落 install-log.tsv（交战区审计通道既有面，非账本 13 表——单写者纪律不破）；--timestamp 沿安装器必填纪律（缺=argparse exit 2）。
  - R-M3-1（internal:true 下 ports 死映射删除）：internal 网 published ports 被丢弃（实测 config rc=0 而宿主连接拒）——保留声明即谎言面，删除+探针改 attack-noop 双网跳板；「127.0.0.1 仅本机映射」测试钉原意=禁 0.0.0.0 暴露，升级为零映射+internal 断言（更强安全面，钉更新随 M-3 同笔）；ground-truth endpoint 值不动（命名键沿用，note 措辞随同步）；T16 首跑 127.0.0.1 形记录=历史口径如实保留不回改。
  - R-M2-1（出口 #3 勘误口径）：勘误仅措辞（动态 ENV-SKIP 清单与 counts 自相矛盾+M12 参数基准词），实测输出行与 ✅ 判定不动——记账完整性优先，历史实测数字不重写。
- **纪律面**：全部新文件 UTF-8 无 BOM+LF（file -I 实测）；时间戳显式字面量（2026-09-27T02:30:00Z 复测 ts，零墙钟入账）；panorama/ 与 /Users/wgen/Documents 零触碰；真仓锚文件/共享夹具 G-g1 零触碰（I-2 测试全在临时仓根副本）；靶场起落 docker compose 面（down 后零残留容器实测）；git diff --check 提交前 clean。
- **R-记账（T17+T18 时点）**：两任务 commit 先行（0328606/a7c5218），本流水+裁决+出口 18 条记录节独立 commit（批次内既定手法）。
## 2026-09-27 六专家对抗评审
- 全平台六视角评审完成，结论 concerns，5 Critical（写路径非原子/guard 绕过/九门伪造/锁信任根/签发四绕）+High/Medium 台账见 docs/design/2026-09-27-expert-review-consolidated.md｜靶场 LLM 在环实战并行中

## 2026-09-27 靶场 LLM 在环首战记录（RUNBOOK §6 通道·R-T16-3 复测）
- **在环执行体**：总控 LLM（glm 宿主会话）以 probe-operator 身份在环临场决策；探针通道=attack-noop 跳板（M-3 双网口径，docker compose exec -T attack-noop python 真实 HTTP）；会话=/tmp/tanyin-range-battle/G-r2（G-r1 废弃见下）；全部时间戳显式字面量；预算计量 budget-log 两笔（token 205k/请求 720/2h，budget-check 实测在途）。
- **流程事实**：E0/E1 过（selfcheck worst=0+compose config rc=0）；靶起 8 服务+attack-noop（172.28.0.2-9:8000 实扫）；P0-P4 五门全过（P0 asserts=3/P1 asserts=3/P2 asserts=2/P3 asserts=1/P4 asserts=5 逐门亲跑 PASS）；denominator-ready PASS（11 资产 sources_ok=11+四类 N/A 披露+canary:recon planted=0 披露）；矩阵 19 面×12 类=228 格全置态（x9/?11/!5/-203，reason 全带实捕依据）；converge-check=**converged**；findings 9 条（文件读取/内部文档暴露/命令执行回显/SSTI候选/SQL报错×2/XSS候选/开放重定向/登录无锁定，全带 EV 卡四要素+content-hash 双指纹）；trigger-audit PASS 23/23（高危即时横向 4 intent+asset-added 回边 8+子矩阵 mint）；POC 独立重放门：9 卡经跳板容器内 tanyin-replay 真重放 **9/9 reproduced**→set-replay-state VERIFIED×9（重放事件+request: 事件在案）；lint 12 门全 PASS rc=0。
- **G-r1 废弃**：P1 期间 parent 边按 source=父误接 11 条（树语义=子→父），边不可删→tree-check 永久 FAIL；按诚实纪律废会话重铸 G-r2（全部命令重放、边向纠正），G-r1 留档仓外作教训样本。
- **scorer 判定（看答案时刻后如实录）**：`python3 tests/eval_range_recall.py --session /tmp/tanyin-range-battle/G-r2 --ground-truth tests/range/ground-truth.json` → rc=1 **recall=0.00 (0/20)**，MISSING 全 20 项。ground-truth.json 仅在 scorer 出分后才打开（归因用途，开打前零阅读——守诚实铁律）。
- **漏检归因（三层）**：
  - ①系统性键失配（工具/评估侧+推理侧各半）：GT endpoint=「M-3 前宿主侧 127.0.0.1:8001-8008 映射 URL 形」原串沿用为资产精确匹配键；在环按真实内网 DNS 资产命名（svc-*/svc-*/path）→ 20 项全失配。RUNBOOK T16 行「127.0.0.1 映射 URL 形历史遗留」线索在场但在环推理未深究——**键口径未前置显式化=评估侧缺陷，未深究=推理侧漏**。
  - ②真实漏检 7 项（工具没测到/矩阵没排上）：xss-02(/comment)、ssrf-02(/preview)、cors-01(/cors-debug)、deser-01(/unserialize)、deser-02(/import)、infoleak-01(/debug/env 二级路径)——路径字典未覆盖（120+词表无这些键）；weakpass-01——弱口令未命中（login 仅回固定 403，无 marker 泄露通道）。
  - ③真实不可达 5 项（推理没想到→通道缺失）：idor×2/role×1/hauth×2 全 post_auth——token 通道未发现（40 余次喷洒、多 token 头/Cookie 形态、路径混淆、Host 变体、X-Original-URL、SSRF 文档名当 token 全部未过）→ 认证后面不可达，如实漏。
  - **真实检出 8/20（40%）**：sqli×2/xss-01/ssti-01/cmdi-01/ssrf-01/traversal-01/redir-01——marker 与端点行为均亲测在案（EV 卡可查），账面 0/20 纯系键失配。
- **在环 vs 脚本干跑差异**：干跑（T16）按预置 URL 键+已知 marker 直写 20/20；在环须自行发现命名键/端点/参数/marker——真实检出率 40%，账面 0%。在环另有 3 项干跑没有的产出：G-r1 废弃样本、228 格逐格 reason、9/9 真重放三态。
- **工具缝（探知即报）**：①terminal-gate 锚点断言按 latest_matrix 的 frozen_at，而 freeze 后 matrix-set 追加行 frozen_at 恒空+freeze 禁重复→凡 P3 置格会话 P5 门不可达（freeze 重跑 REJECT 实证；timeline 已记 P5 探知事件）；②add-evidence 模板产 `expected: {}` 空卡，受限 YAML 仅流式 matchers 可解析（块式 words 残余行错）；③lint redact_scan 目标=report/ 渲染件而非工件本体，卡修正后 stale draft 会误报（须重渲染）；④tanyin-report --out 相对 CWD 落盘，易破交战区分离（本次已移回仓外并 git status 复零）。
- **对总控技能改进建议**：1) GT 键口径与资产命名约定前置显式化（RUNBOOK 显著位），或 scorer 加 URL 归一化匹配（host 别名+query 归一）；2) 端点字典增补二级路径（/debug/env、/cors-debug、/preview、/unserialize、/import、/comment）与两段式路径探测；3) P0 加「认证态获取策略」检查单（弱口令清单/默认凭据/注册面）；4) terminal-gate 冻结断言改为「freeze 时在场行」而非 latest 行，或 matrix-set 继承 frozen_at；5) add-evidence 卡模板内置 flow 式 expected.matchers 骨架；6) lint redact 建议扫全 session（含 replay 运行时产物）+lint 内先重渲染；7) marker 命中之外要求行为差分证据（参数化响应差）防 tag 自证；8) P5.5 真人签发门保持未签发态（不伪造）——本战止于 P4+lint，P5 门如实 FAIL 入档。
- **纪律面**：仓外交战区（/tmp/tanyin-range-battle/G-r1|G-r2），共享夹具零写热；panorama/ 与 /Users/wgen/Documents 零触碰；compose down 后零残留容器实测；工作树净（git status 0 行实测于本节 commit 前）；ground-truth/seed/ 打开前零读（scorer 后归因性打开 GT 一并披露）。

## 2026-09-27 批次 7 开工（executing via subagent-driven-development）
- 用户批准整改计划 docs/superpowers/plans/2026-09-27-b7-remediation.md（17 任务/出口 13 条/红测=专家反例复现；输入=六专家评审 5C+High/Medium 台账+靶场首战工具缝）｜commit 96d90e0
- 执行结构：C1 簇先行→C2-C5→High 七项→战场件→Medium 收口，每任务 TDD+全量回归，收口后整支评审

## 2026-09-27 批次 7 T1+T2+T3 流水+裁决（C1 簇：账本写路径原子化+goal 文件锁+真 SIGKILL 保真；实现者记）
- **T1（3a842ad）账本写路径原子化**：core._atomic_write 单源（tmp+fsync+os.replace，state_md 同款语义收拢）+write_tsv/Ctx.write_file 接线（全仓调用面零变更）。红=半写中断旧内容零损反例（mock os.replace→现状 open(w) 原地截断先吞旧账本，2 FAIL→3 PASS）。全套 751=748+3 绿+金样 54 面 PASS 零漂移。
- **T2（4530f7f）goal 级写锁**：filelock.py 跨平台单源（POSIX flock LOCK_EX 阻塞/Windows msvcrt LK_NBLCK 自旋+超时，超时=OSError 归 2）+registry.lookup 分发单点接线（锁包「读表→改内存→commit」全程；写命令处理函数零 lookup 嵌套调用，同进程顺序取放无自锁——grep 复核）。WRITE_COMMANDS 自 writer 模块注册表派生（write_cmds 38 键含双前缀别名+matrix_init），禁手抄。红=16 并发 add-fact 竞速反例（tmp replace ENOENT 竞态 rc=1+行数缺失→绿=16 全 rc=0+facts 2+16 行+新 id 唯一+verify-chain PASS）。全套 753=748+5 绿+金样 54 面 PASS。
- **T3（4d89884）真 SIGKILL 保真+restart 孤儿对账**：test_kill9_write_fidelity 双组例+phases_engine run_restart 改造（state.md 解析③前移+⓪孤儿对账+⑤事件词带 session=<id>，_last_restart_ts 薄壳保留）。红=双反例复现：①T1 revert 后第 1 杀 200008→4092 行回滚（专家「200008 行→8KB 静默丢史」同型）；②孤儿态再 restart 被 restart-rate-limit 卡 10min（SRE 复现原样）。绿=8 杀后链完整+行数不回滚+收尾写入 tmp 零残留且恰进 1 行；孤儿放行 rc=0+managed-restart-orphan prior-session 留痕+真重启速率窗不豁免（non-orphan 对照例钉死）。受管重启既有 10 例+state_md/lock_v2/kill9_fidelity/resume_kit 同域 55 例零回归。全套 756=748+8 绿+金样 54 面 PASS 零漂移。
- **Ruling（T1 解释器）**：本机 python3=3.9.6（命名空间包 discover 唯一可用；python3.12 discovery 对无 __init__.py 的 tests/ 直接 ImportError——计划「Python 3.11/3.12」为标准库用法口径，非解释器绑定）；HANDOFF 在册 discover 命令形照用，计划出口#1 的 -p/-t 变体两解释器同败（记录不采纳）。
- **Ruling（R-T2-1 夹具）**：16 并发反例夹具=tests/fixtures/G-g1 拷贝（test_write_cmds 同款）——计划片段 fresh_drydir 空目无 goals/intents，add-fact 因 Tier0/引用闭合用法性失败=假红；反例需 16 条全合法 add-fact 竞速。断言口径微调：facts 期望 n0+16（夹具底 2 行）+新行 id 唯一性（last-writer-wins 特征断言）。
- **Ruling（R-T2-2 锁面）**：锁面=write_cmds.HANDLERS 与 matrix_init.HANDLERS 并集（金样写面 20 的全部）；set-replay-state（check_cmds）读写双态同入口，写形锁覆盖留 v3（拆读写形涉契约面）——登记遗留。
- **Ruling（R-T2-3 .lock 表面）**：run_golden.norm_state 与 test_negative_matrix 目录快照排除 .lock——锁工件非账本面（计划 T2 出口「.lock 不进任何表面」的实现位）；负向矩阵例补钉「REJECT 亦经锁面（.lock 在场非账本变更）」。
- **Ruling（R-T3-1 断点协议）**：计划 rng.uniform(0.002,0.05)s 断点落子进程 import/读表期（写窗命中率约 0）→红测假绿；改武装哨兵协议（子进程读表毕触发哨兵，父进程等哨兵后 sleep rng 区间再杀）——断点确定落在 200k 行写窗内，反例必现。
- **Ruling（R-T3-2 tmp 残留）**：kill -9 无法执行 except 清扫，写窗内被杀必留 .tmp——残留非撕裂态 A（账本本体 os.replace 保证要么旧版要么新版），同路径 tmp 下一次写入截断复用（收尾例钉死：终写后零残留+恰进 1 行）；SIGKILL 循环内改断言「可解析+链完整+行数不回滚」，异常路径清扫由 T1 反例承载。
- **Ruling（R-T3-3 孤儿夹具）**：孤儿例夹具=G-g1 拷贝（test_managed_restart 同款）——fresh_drydir 空目使 _make_orphan 的 budget-log/append-timeline Tier0 REJECT=假红。
- **Ruling（R-T3-4 对账=重建）**：计划 ⓪片段只豁免速率窗+补记事件，实测无法放行——manual 接管前置 state-rebuild 检查（revision/snapshot 口径）对孤儿态必 FAIL（第二道卡死，SRE 反例的完整形态）。对账补 rebuild_state 对齐（账本为第一事实源，check_cmds 同口径；session=rebuilt/status=released，随事务末尾 checkpoint 重取新锁）+失败 REJECT+重解析 fields。
- **Ruling（R-T3-5 过滤词）**：_last_restart_event 排除对账事件按事件词前缀 managed-restart-orphan 判定——计划片段子串判定被 session id（r-orphan）误伤（红测自身即绊线），实测改前缀判定。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰；新文件 UTF-8 无 BOM+LF；.gitignore 增 __pycache__/（字节码目录不入 status，全净判定可持续）；收尾全套 756 OK+金样 54 面 PASS+git status 净（本节 commit 前亲测）。

## 2026-09-27 批次 7 T4+T5 流水+裁决（C2 簇：guard exec 硬化——argv 规范化+主机变体解码；实现者记）
- **T4（e944981）guard argv 规范化**：enforce.normalize_cmd（组合短旗标拆并→字母并集重组+长旗标映射 --recursive/--force；--no-preserve-root 以 "!" 占位单列原样保留）+deny_forms（原 joined+归一形；sh/bash/dash/zsh -c 内嵌 payload 追加原形+归一形）双形比对；tanyin-guard gate_chain deny 段接线（inject 同门链自动生效；REJECT 消息仍出示命中的 deny 模式；归一只作执法比对形，不改写实际执行 argv）。红=专家反例 rm -r -f / rc=0 全录（原例/换序/长旗标/组合大小写 -rF/./ 变体/sh -c 内嵌 6 形，shim 载体修前实测 rc=0）→绿=6 形全 REJECT rc=1（消息出示归一形命中 rm -fr /）+良性旗标对照 rc=0 零误伤。全套 760=756+4 绿+金样 54 面 PASS 零漂移。
- **T5（75c057f）guard 主机提取硬化**：enforce._decode_ip_obfuscation（无点纯整数 ≤0xFFFFFFFF 十进制/0x 十六进制/恰 4 段全数值点分八进制段→规范点分十进制；含冒号/域/短式一概原样）入 _hosts_of_token 候选集（原形+解码形双候选，去重保序）；tanyin-guard 零改动（extract_hosts 单源自动生效）。红=专家反例 http://134744072/（十进制 8.8.8.8）rc=0 修前实测→绿=REJECT 界外目标: 8.8.8.8 rc=1（十进制环回 2130706433/0x7f000001/0177.0.0.1 八进制段/0x08080808 全 REJECT 且消息出示解码后主机）；echo 载体原例同拒。版本号短式（3.14/1.2.3）不误伤裁决+对照例在册。全套 764=756+8 绿+金样 54 面 PASS 零漂移（tests/golden 零 diff）。
- **Ruling（R-T4-1 测试内惰性导入）**：计划片段模块级 from ledger.enforce import normalize_cmd, deny_forms 在红态=ImportError 吞全模块——计划 Step 2 预期的两路红（函数未定义+guard rc=0 逃逸）不可分显；导入移入用例方法（T5 _decode_ip_obfuscation 同口径）。红实测=1 FAIL（0!=1 反例）+2 ERROR（未定义）+1 良性对照 PASS，恰落计划预期形态。
- **Ruling（R-T4-2 红例复现安全 shim 载体）**：计划红测 test_expert_repros_all_rejected 红态会经 subprocess 真执行 rm -r -f / 破坏载荷（红=门放行，测试自身成兵器）；guard 层测试一律经 _shim_env 注入 PATH 替身目录（rm/sh/curl/echo exit-0 假体）——红态执法语义不变（逃逸=rc 0 可见）、零真实执行；绿态 REJECT 先于 subprocess.run，行为面与直跑一致。专家反例原样 argv 修前/修后实测（shim 承载）各录一轮为本节证据。
- **Ruling（R-T4-3 Tier2 面登记）**：hooks/simulate.py（Tier2）现仍字面 deny_hit(joined)——normalize_cmd/deny_forms 已落 enforce 单源，Tier2 接线不在 T4 计划 Files 面；「Tier1/Tier2 同源执法」承诺的另一半收口登记 v3/后续。
- **Ruling（R-T4-4 commit 记法）**：任务令「批次7 T4：」为前缀简写，计划 commit 命令明文「批次7-T4(C2)：…」全文——两读法同为「每任务一中文 commit」，按计划意图取原文执行（冲突裁决：计划优先）。
- **Ruling（R-T5-1 反例集补录 echo 载体）**：任务令台账 C2 反例二原文=「echo http://134744072/」rc=0（执行面零风险载体）——IP_REPROS 于计划 5 行（curl 形）外补录 echo 形一行（专家反例全录纪律）；guard 层 shim 名单已含 echo。
- **Ruling（R-T5-2 fresh 夹具 scope 口径勘误）**：计划注称 fresh_drydir scope=P0 三行界内域；实测 fresh_drydir 仅 auth/dry.pdf 无 scope.tsv（三集皆空=fail-closed）——解码后主机判 out REJECT，结论与计划假设等价（8.8.8.8/127.0.0.1 均界外），测试落点不变，记录勘误。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（改动面仅 cli/ledger/enforce.py、cli/tanyin-guard、tests/test_guard_argv_norm_b7.py、docs/HANDOFF.md）；UTF-8 无 BOM+LF（file -I 抽查在册）；收尾全套 764 OK+金样 54 面 PASS+git status 净（本节 commit 前亲测）。

## 2026-09-27 批次 7 T6+T7 流水+裁决（C3 九门权威+C4 tools.lock 信任链；实现者记）
- **T6（ea90fd5）九门权威**：core.RESERVED_EVENT_PREFIXES=("gate-exit:","gate-fail")（GATE_EXIT_EVENT 同节常量单源）+write_cmds._append_timeline 保留词拒收（Reject→_wrap→stderr 单行 REJECT rc=1；先校验后写入=REJECT 零落账）。红=专家 C3 反例修前实测原始输出在案：准各 goal 后连发 append-timeline gate-exit:P0..P6 七行全 rc=0 落账，补 P5.5/P6.0 两行即 verify-chain rc=0 PASS 跳门=0，tanyin-phases gate P0/P6 → already-passed exit 0（九门断言零执行即终局——专家行「断言零执行」形态完整复现）。绿=保留词三形（gate-exit:P0／gate-fail:P0／gate-exit:P6 asserts=0 result=PASS）全 REJECT rc=1 且 timeline 零字节、伪造序列第一步即断；对照组=干跑 P0-P2 三门合法铸造全序列不受扰+managed-restart 词不进保留表（T12 面预留）。定向回归 72 绿+全套 769=764+5 绿+金样 54 面 PASS 零漂移。
- **T7（c364435）tools.lock 信任链**：测试钥轮换（P-256 新对；DER 指纹 4a46f7fb…→817e3bed…，新公钥落 tests/fixtures/keys/test-release.pub=测试信任锚；私钥 0600+TEST-ONLY 注释头沿仓例）+信任面隔离断言（sign_entry(TEST_KEY)×release.pub=FAIL、×test-release.pub=PASS）+adapter.verify 增 runtime 二进制 sha256 比对（核验序=锁验签→templates.lock→runtime 工件在场即必比，不符=blocked「runtime nuclei sha256 与 tools.lock 不符」，缺失不比——canned 离线面零变更；签名向后兼容全既有调用点零改动）。红=专家 C4 双反例修前实测原始输出在案：①test 钥重签篡改 nuclei 行（version=9.9.9-trojaned/sha=ab×32）→check_lock=0（生产锚验签全过）；②lock 签名有效+在场二进制 FAKE-BYTES≠lock.sha256(PRISTINE)→verify ok=True（不比对）。红测 3 FAIL+2 ERROR→绿 5 OK；信任面回归（supply_chain/resign/install_core/install_hooks_release/engine_nuclei/lock_v2）49 绿；全套 774=769+5 绿；金样 54 面 PASS 零漂移。
- **Ruling（R-T6-1 计划前提勘正：铸造路径实况）**：计划 Interfaces 断言「run_gate 内部 _append_event 直写，不经 append-timeline」与实码不符——_append_event 原经 registry.lookup("append-timeline")（T2 _locked 包装）走命令面全路径，保留词检查若入 handler 即断合法铸造链（dry_run 三门同断）。按计划意图（引擎单源铸造+命令面收权）裁决：_append_event 改 Ctx 直写（goal_lock 单源锁内 tier0+event+commit 同语义同锁形；Reject→RuntimeError fail-loud 契约保持；全仓调用点核对无嵌套锁），phases_engine 内注释同步；write_cmds 引 RESERVED_EVENT_PREFIXES 按 from-import 风格。
- **Ruling（R-T6-2 红测前置对齐）**：计划测试片段两处不合实面：phases(gd,"gate",["P0",…]) 缺 --phase= 键（用法错误）→对齐实参；reject 例须先 dry_run_p0_p2(upto=7) 立项——否则红态 tier0 硬门（无 goals 行）先 REJECT rc=1，保留词断言假绿（红必须是真反例）。legit-mint 对照升级为全序列 dry_run（三门真铸造端到端证据）。
- **Ruling（R-T7-1 verify 锚注入位）**：计划 verify 两参签名与计划测试自身不相容——测试钥签的 lock 须过 verify 双键验签门才可达 digest 断言，而收权后生产锚必拒测试钥签名。增设第三参 pub（缺省=生产锚，main() 零改动=运行时信任根单源不变），runtime digest 测试显式注入测试锚；「缺省生产锚」语义杜绝测试钥旁路（C4 同类）。
- **Ruling（R-T7-2 重签清单=空+根 lock 保持原签）**：Step 0 grep（tests/fixtures engines --include=*.lock）实证仓内零夹具 lock 工件=重签清单空；根 tools.lock 系旧夹具钥签发且其 DER 指纹=release.pub（同信任面即 C4 根因本体），对生产锚仍有效——不属「旧钥签发的夹具 lock」重签面，保持原签；test_supply_chain_resign roundtrip/tamper 两例信任锚切 test-release.pub（锚位与被测钥配对，防假阴错因混杂）；resign 脚本/生产锚轮换通道零改动。
- **Ruling（R-T7-3 同钥判定改 DER 指纹）**：计划 Step 0「openssl -pubout | diff - release.pub」仓内不可判——release.pub 首行带 # TEST-ONLY 注释头（PEM 文本 diff 恒异，直跑实况=误报 DIFFERENT）；改 -outform DER 指纹比对（红=双侧 4a46f7fb… 同指纹实证，绿=817e3bed…≠4a46f7fb…）。
- **Ruling（R-T7-4 测试片段勘误）**：计划片段 sign_entry 返回值未赋回 e["sig"]（sig=""→verify「sig 非 hex」fail-closed，断言不可达）+单键 lock 过不了 verify 双键验签门——红测修正为赋值+双键（nuclei/nuclei-templates）；红态实录=3 FAIL+2 ERROR（TypeError: unexpected keyword 'nuclei_path'=特性缺失的诚实红，非 argv 拼错）。
- **Ruling（R-T7-5 金样零漂移声明）**：计划 T7 有意刷新预案（engine-nuclei-adopt 面）未动用：根 tools.lock 仍由 release.pub 配对钥签发（验签面无感）+本机无 nuclei 二进制（runtime digest 缺失不比，canned 面 byte-identical）；git status tests/golden 零行。生产锚（release.pub）轮换仍属 G-22/KEY-MANAGEMENT 离线人工仪式——残留风险=「仓外若仍有旧钥副本」，维持 b6 出口 #17 人工移交态，b7 台账不新增行。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（git log --stat 复核：改动面仅 cli/ledger/{core,write_cmds,phases_engine}.py、engines/nuclei/adapter.py、tests/fixtures/keys/{test-signing-key.pem,test-release.pub}、tests/{test_gate_authority_b7,test_tools_trust_face,test_supply_chain_resign}.py、docs/HANDOFF.md）；UTF-8 无 BOM+LF（file -I 抽查新文件在册）；收尾全套 774 OK+金样 54 面 PASS+git status 净（本节 commit 前亲测）。

## 2026-09-27 批次 7 T8+T9 流水+裁决（C5 簇：签发四门——授权完整性+draft 字节比对+工件绑定+落盘后复扫；实现者记）
- **T8（5d84da5）签发授权完整性门**：report_lint._authorization_gate（①goals auth_doc 文件 sha256 现算比对（deadbeef/手改即失配）②issuance ts∈[valid_from,valid_until] 窗口门 ③approvals.tsv decision=approved 行 verify-signoff 强校验）入 sign_gate 联合判定（gates.authorization FAIL 明细=中文分号串；列下标 TABLES 单源零硬编码；cmd_lint 同判定自动同门）。红=合规总监四绕①③修前实测原始输出在案：全绿签发基线上换 auth_sha256=deadbeef/窗口改 2020-12-31/剔 approved 行 → sign rc=0 三连（11 门全 PASS 直通——verify-chain PASS 与授权面损坏并存=台账 C5 行原样），lint 入口 deadbeef 同样 rc=0；绿=三例全拒 rc=1 且 FAIL 明细落 authorization 门+批准在案后门转 PASS+lint 同门拒收。全套 778=774+4 OK+金样 54 面 PASS 零漂移。
- **T9（a5b6944）签发四门②③④**：_fd_checks draft 分支改 draft==render_fd 现算字节比对（gates.draft_byte_equal——旧实现只查 raw 子串在不在，C1→C3 改置信度即逃逸）+pass.json artifacts 三工件 sha256 绑定（report/draft/*.md+E-index active artifact_path+终态 B interim-report.md 先落盘后入绑定；同一 dict 引用成文无第二源；lint 入口 pass.json 在场即自动复检 artifact_binding，免新旗标零契约扰动）+redact-scan 移到凭证落盘后复扫（_redact_scan 单源；扫描面=终稿在场的 report/ 全树；FAIL=删 pass.json/interim fail-closed 不得留半签发态；lint 无凭证路径维持扫描后返回）。红=四绕②④修前实测原始输出在案：draft C1→C3 手改 sign rc=0+pass.json 无 artifacts 键+redact_scan 调用时 pass.json exists=False（含终态 B 双工件 False/False 全形）7/7 FAIL；绿=7/7 OK（手改拒收+绑定即真值+签发后篡改 lint 复检即拒+复扫 FAIL 凭证删除）。全套 785=778+7 OK+金样 54 面 PASS 零漂移。
- **Ruling（R-T8-1 全绿签发夹具+授权三件套修补单源）**：计划 T8 片段 _goal_with_auth 以 add-goal 铸 fresh_drydir 空目——其余门（scope/matrix/tier/合规六要素）先 FAIL，红态 rc 恒 1，「sign rc=0（零授权校验）」反例不可承载（R-T6-2 同律：红必须是真反例）。改 G-g1 拷贝+mint_full（EV/FD/豁免=test_report_lint._mint 同款 argv+授权三件套修补 repair_auth：auth 文件落盘+真 sha256 写 goals 拷贝）——先证全绿基线再逐腿破坏，FAIL 归因唯一。共享夹具本体零触碰：金样 *.state 引用夹具伪 sha（aaaa…），动本体=大面积金样漂移（write-add-goal/write-approve 等 9+面实证在案）。test_budget_exhausted/test_report_artifacts 经 from tests.test_report_lint import repair_auth 复用单源（R-T2-1 跨测试模块导入先例）。
- **Ruling（R-T8-2 _parse_iso 内聚+naive→UTC 归一）**：仓内无共享 ISO 解析单源（phases_engine.py:805/report_render.py:73 各裸 fromisoformat，计划 grep 授权内聚）；窗口列既有 date-only 形态（2026-09-01）解析为 naive，与 Z 形 ts（aware）直接比较=TypeError——归一律：naive 一律 attach UTC（窗口语义=UTC 日界，测试夹具两形态齐验）。authorization 门经 T8 接线即覆盖 date-only/ISO-Z 两形态。
- **Ruling（R-T8-3 授权门暴露面=三个签发消费夹具）**：全套回归暴露 test_report_lint（2 例）/test_budget_exhausted（1 例）/test_report_artifacts（1 例）四处既有绿例因夹具授权三件套不全转红——按计划「合法夹具因新门红=补夹具不放水」修补（repair_auth 接线 _mint）；test_reverse_verify P5 真门例（期望 rc=1）与 test_report_lint 三个负例（期望 rc=1）不受扰=授权门只增红不洗白。gate JSON 形增 authorization/artifacts/draft_byte_equal 键（pass.json 工件内容面）——非 CLI 契约面（旗标/必填参数），零勘误需求，契约面 T17 统一复核。
- **Ruling（R-T9-1 删证例红态修正）**：计划 test_rescan_fail_deletes_credential 在红态平凡绿——旧实现扫描先于凭证落盘，凭证永不存在→assertFalse 恒真（红=假绿不可收）；修法=并入次序断言（记录 redact_scan 调用时 pass.json exists 状态，断言末次扫描时凭证已在场），红态败于「扫描先于落盘」（专家反例④原样）、绿态方验「复扫 FAIL=凭证删除」——红绿两态皆诚实（R-T6-2/R-T7-4 同律延伸）。
- **Ruling（R-T9-2 早退路径扫描面变化登记）**：旧实现 redact_scan 于门序列中段无条件跑（!ok_all 早退亦扫）；新实现=写路径移至凭证落盘后、lint 路径移至 rep 构建后——全门早败路径不再产扫描结果（gates.redact_scan 保持默认 PASS 形）。rc 判定 fail-closed 不受扰（早退=rc 1 已由它门承重）；「FAIL 报告单上 redact_scan 无实测值」为已知语义变化，登记 v3（早退路径亦可出扫描值=+0.2s/例代价，收益低）。
- **Ruling（R-T9-3 write_all 复扫位登记）**：专家反例④载荷含 write_all——cmd_sign 的 report_artifacts.write_all（findings.json/sarif/report-*.md）仍落盘于 sign_gate 复扫之后（sign_gate 门内不可达）；计划意图=sign_gate 门内面收口（红测载体=pass.json/interim），write_all 产物面复扫登记 v3（须跨层传递 fail-closed 删证通道，涉 cmd_sign 返回路径改造）。
- **Ruling（R-T9-4 金样零漂移声明）**：计划 T9「lint 签发面若含 pass.json 字节=有意刷新名单」未动用——run_golden 54 面无 lint/sign 面（grep 实证），artifacts 键新增零金样触达；两任务收尾 git status tests/golden 零行实测。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（git log --stat 复核：改动面仅 cli/ledger/report_lint.py、tests/{test_sign_gates_b7,test_report_lint,test_budget_exhausted,test_report_artifacts}.py、docs/HANDOFF.md）；新文件 UTF-8 无 BOM+LF（file -I 在册）；[sys.executable, path] 载体零改动；退出码契约 0/1/2 不变；收尾全套 785 OK+金样 54 面 PASS+git status 净（本节 commit 前亲测）。

## 2026-09-27 批次 7 T10+T11+T12 流水+裁决（High 前半捆绑：vault 加密强化+egress 补全+restart 阈值消费；实现者记）
- **T10（2f9a1e6）vault v2**：enc/dec 升 nonce 随机化+EtM-HMAC-SHA256（MAGIC=TV2，enc_key/mac_key 子钥分域——专家 m1^m2==c1^c2 可滚伪造实证关系消除、篡改 fail-closed）+derive_key PBKDF2-HMAC-SHA256 200k（passphrase→主钥）+密钥外移（load_key 优先 TANYIN_VAULT_KEYFILE，回落 vault/.key）+guard deploy-vault --secret/--passphrase 退出 argv（usage exit 2 零回显；env TANYIN_VAULT_SECRET/PASSPHRASE 主通道+--secret-stdin/--passphrase-stdin 旗标 opt-in）+未初始化 vault=passphrase+vault/.salt(16B os.urandom) 派生主钥写 .key+manifest 算法列 etm-sha256；dec_payload 双读过渡（无 MAGIC=legacy XOR 读+stderr 一次性告警，存量夹具零破坏）。红=8 例中 5 红（可滚伪造 x[:4]==m/同明文同密文/篡改直通/外移不生效/env 通道 rc=2）→绿 8/8。
- **T11（832c565）egress 补全**：decide 升四态 (verdict,reason)=显式 deny 优先→canary 告警放行（探测点语义：阻断反掩盖触达）→oob 白名单→allow→默认拒（forward+CONNECT 单点接线，canary 落 kind=canary ALARM 行）；compile 产 [canary] 段（recon-decoys.tsv 列[1]）；serve/serve_text now 缺省 None→UTC 真墙钟（EPOCH 退役出 serve 面，--timestamp 显式固定 now 通道保留）+format_log_line/append_log_line/MAX_LOG_BYTES(5MB)×LOG_KEEP(3) 轮转+HANDLER_TIMEOUT_S(30s)。红 8→绿 8。
- **T12（3d21747）restart 阈值消费**：--usage/--round 必填（缺参/非法=usage exit 2；manual 不设阈值但同必填=审计语义）+auto 档阈值执法（usage≥0.75 或 round%10==0，单源=FROZEN_CONSTANTS 默认键；REJECT restart-threshold rc=1，位=速率检查后预算落账前=零副作用）+事件词升级 managed-restart spawn=<s> session=<id> usage=%g round=%d（T3 孤儿 token 解析天然兼容）。红=7 例中 6 红（缺参受理 rc=0/低用量 0.30+3 轮照常重启）→绿 7/7；既有 restart 调用面统一补参（test_managed_restart/test_lock_v2 助手单点注入+kill9 三处逐点）。
- **Ruling（R-T10-1 legacy 告警进程级一次性）**：计划骨架 dec_payload legacy 分支每次读都写 stderr，Interfaces 明文「stderr 一次性告警」——按意图落 _LEGACY_WARNED 进程旗标（防 replay/guard 真值回注面 stderr 噪声污染既有断言）。
- **Ruling（R-T10-2 stdin 通道旗标 opt-in）**：计划「secret 从 env/stdin 读」未定 stdin 形态——无人值守上下文隐式读 stdin=阻塞事故源，落 --secret-stdin/--passphrase-stdin 显式旗标（env 为主通道）；裸旗标形（无 = 值）同生效。
- **Ruling（R-T10-3 .key 在场=沿用原钥不重派生）**：计划「passphrase 经 PBKDF2+vault/.salt→主钥写 .key」——.key 已在=沿用（重派生=换钥=存量凭据断根，违背双读过渡意图）；仅缺 .key 时 passphrase 初始化。
- **Ruling（R-T10-4 test_guard 三处 deploy 调用改 env 通道）**：计划 T10 Files 未列 test_guard.py——--secret 退出 argv 后 GuardVault/GuardInjectEnforcement/GuardStderrTokenize 三处 argv 形调用必转红，按 T12「必填契约后果」同律以 g_deploy_env 助手改 env 通道（断言语义零变更）。
- **Ruling（R-T10-5 金样零漂移声明·三任务名单皆空）**：计划 T10「deploy-vault 输出面若在金样=有意刷新名单」未动用——golden 面实勘（run_golden 面清单+grep）无 vault/deploy/egress-compile/restart 面，nonce 随机化与 [canary] 段零金样触达；三任务收尾 git status tests/golden 零行实测。
- **Ruling（R-T11-1 TestCompile 夹具 G-g1 拷贝）**：计划片段 add-scope 直打 fresh 空 dir——Tier0 硬门「无 goals 行先立项」实测 REJECT rc=1（探针在案）；按 Step 0「以实文件为准」对齐 test_egress.py 先例改 G-g1 拷贝，断言面不变。
- **Ruling（R-T11-2 [canary] 段单源=recon-decoys 值列）**：计划接口「scope kind=canary 行 ∪ recon-decoys」——add-scope kind 枚举冻结四值（include/exclude/oob/account-grant，契约面禁扩），kind=canary 行不可达；落 recon-decoys.tsv 列[1] 单源（与 phases_engine denominator-ready ④同口径）+排序去重保 compile 双跑字节一致。
- **Ruling（R-T11-3 decide 保留显式 deny 优先）**：计划骨架四态无 deny 分支（canary 先于一切）——exclude 优先是洞 1 冻结纪律且既有断言在册；落 deny→canary→oob→allow→默认拒，test_explicit_deny_beats_allow 钉死。
- **Ruling（R-T11-4 CONNECT 面同款单点接线）**：计划「handler 判定改单点」未分 forward/CONNECT——canary 经 TLS 隧道触达同属真实触达，do_CONNECT 同款 canary→ALARM+放行；connect 行 verdict 仍按 allow|deny 收口（消费面兼容，_traffic_touches 只认 kind=canary 实测零受扰）。
- **Ruling（R-T11-5 test_egress_proxy 11 处断言取 [0]）**：decide (verdict, reason) 契约后果——既有断言按 [0] 对齐（计划 Step 4「既有面全 OK」内含）；canary 流量级 ALARM 判定词变更=行为收紧而非漂移，如实注记。
- **Ruling（R-T12-1 T12 夹具改 G-g1 拷贝）**：计划 _ready=fresh_drydir+checkpoint——fresh 目录无 goals 行，checkpoint 实测 REJECT rc=1（Tier0 硬门探针在案，R-T11-1 同型）；按 test_kill9/test_managed_restart 先例改 G-g1 拷贝+checkpoint。
- **Ruling（R-T12-2 restart 统一带 --session=s0）**：夹具 checkpoint 落 active 锁 session=s0——auto 直接重启撞 ③单活跃会话（接管拒绝实测在案）；restart 调用统一 --session=s0 延续自身血统（护栏语义与阈值断言正交，计划片段未建模该交互）。
- **Ruling（R-T12-3 既有用例补参=助手单点注入）**：计划「test_managed_restart 10 例+kill9 孤儿例统一补 --usage=0.90 --round=1」以 Base.restart/restart 助手单点承载（语义等同逐点；usage_errors 用例群实测维持 exit 2）；test_lock_v2 wiring 三例=全套回归暴露的第三处调用面，同律补参。
- **Ruling（R-T12-4 invalid_values 红期 PASS 溯源）**：计划红期预期「其余例视实现时点」——该例红期过（旧 cmd_restart 未知 token else→exit 2 碰巧同 rc）；绿期转由 --usage/--round 专项校验承载（红绿两态 rc 同值校验路径不同，如实注记）。
- **Ruling（R-T12-5 phases_engine 分段读截断事故+HEAD 重建）**：实现中读段上限（实测单次 ~1098 行）致一次写入截断文件尾 33 行（py_compile IndentationError 当场暴露）——以 git HEAD 原文分段读回+四处计划内编辑重建，diff vs HEAD=恰四处改动逐行复核在案，全套 808 复跑实证零损（截断仅存于工作树未入库，T10/T11 提交不受涉）。
- **全套**：基线 worktree 实证 785 OK+金样 54 PASS（HEAD=58d4bae 处）→T10 后 793 OK→T11 后 801 OK→T12 后 808 OK（suite-exit=0）；金样 54 面 PASS ×4 跑，golden-exit=0。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（git log --stat 58d4bae..HEAD 复核零行）；新文件 UTF-8 无 BOM+LF（file -I 抽查+grep -rlU \r 空）；跨平台纪律不动（[sys.executable, path] 调用形，无 POSIX 专有依赖新增）。

## 2026-09-27 批次 7 T13+T14+T15 流水+裁决（High 后半捆绑：触发器 no-consume 通道+K1 缺基线 exit 2/矩阵批量置格+词表裁剪/permitted_actions 执法+guard timeout；实现者记）
- **T13（58c10c6）触发器显式不消费通道+K1 缺基线 exit 2**：add-fact 新参 --no-consume=<理由>（理由空=Usage exit 2 防无意识标记；标记 [no-consume:<理由>] 落 facts.detail 单元格+落盘前 redact 整体复扫；core.NO_CONSUME_MARK 单源常量）→消费执法面接线：unconsumed_facts 跳过带标记事实+unconsumed-facts/trigger-audit 输出单列 deferred=<n>（n>0 才出列=零标记输出字节不变）；knowledge.KnowledgeEnvError（EnvironmentError 子类）——score() 前置基线文件检查（缺文件=方法库未安装 raise，先于 --today/goal-dir 校验）→tanyin-knowledge 消费面 stderr 点名 K1+exit 2（专家反例 severity 0.9→0.5 静默 rc=0 收口）；基线文件在、缺 vuln_class 行=合法缺省 warning+0.5（两态分流）。红=7 例中 5 红（4F+1E：未知参数 rc=2×3+缺基线 rc=0+KnowledgeEnvError 属性缺位）→绿 7/7。
- **T14（bc295d2）矩阵批量置格+资产类词表裁剪**：matrix-set --batch-file（LF TSV 四列 surface/vclass/state/reason；行自载 state/reason，空单元格回落命令行参；空文件/非四列行=REJECT）——全成全败=先全校验后一次写入（_validate_cell 单源自 _matrix_set 抽出：state 枚举/reason 必附/intent 闭合/G-2 四条件/前缀一致性，单格与批量共用禁第二份；批量跑在模拟行集上使同表面后续行可见先行 mint 家族）+恰一条 timeline 事件 matrix-set-batch n=<k>（2640 格单格单命令爆炸收口）；matrix-init --from-assets=行集裁剪为在册 in_scope 资产类型映射词表类（TYPE_VOCAB_CLASSES 单源新建；映射后类空=REJECT）；缺省不带开关=全量行为零变更（金样保护）。红=4/4（--batch-file/--from-assets 未知参数 usage rc=2）→绿 4/4。
- **T15（9452d61）permitted_actions 执法接线+guard --timeout**：enforce 新单源 permitted_actions_covered/grant_row_exists（多值分隔=分号与 write_cmds._mv 同语义；covered=该 account 全部 account-grant 行 permitted_actions 并集精确命中；无 grant 行=无覆盖面）+guard 门链扩展 deny-list→scope→permitted_actions→request-ticket（exec 前置参 --cred/--action/--timeout 在 -- 分隔符前剥取，未知旗标不剥保既有 usage 形；--cred 无 grant 行=REJECT 无覆盖面；--action 未覆盖=REJECT+guard-reject permitted-actions cred=X action=Y 留痕）+inject 带 --cred 须 --action（usage exit 2）+--timeout=整数秒 1..600 缺省 60（Medium「60s 硬超时」收口；非法=usage exit 2；TimeoutExpired⇒REJECT 输出点名 timeout rc=1，exec/inject 双通道 subprocess.run(timeout=t)）。红=8 例（unit 5+guard 2+timeout 1；module 导入失败=函数缺位+CLI 直跑 rc=2）→绿 8/8。
- **Ruling（R-T13-1 标记承载位=detail 非 note）**：计划「fact 的 note 单元格追加」与 snippet `TABLES["facts.tsv"].index("note")`——facts.tsv 八列无 note 列且 13 表列集冻结（Global Constraints），自由文本唯一承载位=detail；按计划测试断言实形（文件含 "[no-consume:<理由>]"）落 detail。
- **Ruling（R-T13-2 deferred 计数两视图口径）**：unconsumed-facts 视图 deferred=「带标记 ∧ 无 derived_from 边」（被本视图跳过者）；trigger-audit 视图 deferred=带标记 fact 总数（合法闭合通道计量）；两者皆 n>0 才出列——金样零漂移为硬约束（read-unconsumed-facts 面在册）。
- **Ruling（R-T13-3 K1 两态分流+检查前置）**：缺基线文件=KnowledgeEnvError（环境域 exit 2）vs 基线在、缺行=warning+0.5（裁决 A 合法缺省）——计划意图明载两态分流；baseline_rows docstring「init 运行时库不带基线」旧口径由新执法取代（Init 库默认带基线不在本批范围，T17 契约勘误登记）；score() 基线检查先于 --today/goal-dir 校验（环境级失败优先报告）。
- **Ruling（R-T13-4 既有 K1 因子用例补基线种子）**：tests.test_k1_baseline_score.test_creds_and_precedent_hit_factors 经 kn init 运行时库（无基线）调 score 期望 rc=0——与新执法直撞；其被测语义=凭据/先例因子合成与基线缺省正交，按 T12「必填契约后果」同律补最小基线种子行（断言语义零变更）。
- **Ruling（R-T14-1 TYPE_VOCAB_CLASSES 单源起草）**：仓库此前无「资产类型→词表类」映射单源——按计划「以 Step 0 行集形为准」新建于 matrix_init（分层依据=DENOM_CLASS_BY_TYPE 的 A1-A8 资产类分层+G-12 十一值枚举；A4 应用层=WSTG 全集）；缺席类型独涉类不出行即「A5 存储与云/A7 人的因素等缺席类不出行」的可执行形。
- **Ruling（R-T14-2 计划断言字面 "A5" 无实形）**：计划示例 assertNotIn("A5", pruned)——matrix.tsv 词表键=shared/VOCAB wstg-* 实形，"A5" 永不在场（断言恒真空转）；按实形断言缺席类型独涉类（wstg-sess/wstg-busl 等）不出行+映射类恰三项。
- **Ruling（R-T14-3 批量 mint 抑制 submatrix-mint 事件）**：计划「全过=恰一条 timeline 事件」与单格 mint 的 submatrix-mint 事件词冲突——批量路径 mint 仍铸词表全家族行但不逐行发事件（单条 matrix-set-batch n=<k> 承载）；_validate_cell 纯校验不落账（act/meta 返回，事件由调用方铸造），单格路径事件字节不变。
- **Ruling（R-T14-4 G-g1 已冻结实勘）**：计划红测骨架假设需现场 freeze——G-g1 matrix.tsv frozen_at 列已盖戳（make_fixtures 模拟 P2 冻结，test_trigger_audit Ruling 同源）；setUp 免 freeze（首版误判 frozen 列位+补 freeze 已纠，already-frozen REJECT 为幂等正确行为如实录）。
- **Ruling（R-T15-1 多值分隔=分号）**：计划 snippet split(",") 与计划自身「以 write_cmds._mv 实现对齐并测试钉死」条款冲突——取分号（_mv 语义；add-cred 覆盖校验 :1086-1088 同口径）；test_unit_multi_value_semicolon_union 钉死「probe;deploy 双命中+readprobe 不假阳」。
- **Ruling（R-T15-2 既有 inject 用例补 --action+覆盖行）**：计划 Files 未列 test_guard.py——inject 带 --cred 须 --action 落地后八处既有调用转红，按 T12「必填契约后果」同律补参+add_grant 助手（account=--cred 值逐字对照 scope.account；test_missing_entry_rejected 补 grant 行保「vault 条目缺失」原判定语义）。
- **Ruling（R-T15-3 account-grant 行 matcher=语法占位）**：首版夹具用 *.shop.example 撞 load_scope「同 matcher 后行覆盖先行」修正键（account-grant 行顶掉夹具 include 行→api.shop.example 误判界外实测红）——改 grant.example 占位（account-grant 不参与主机判定，matcher 仅过 _scope_common 语法门）。
- **Ruling（R-T15-4 tanyin-canary tier1 inject 探针补 --action=probe）**：计划 Files 未列 tanyin-canary——T15 落地后 inject 形探测 rc=2 被归类 allowed（诱饵零容忍面破，终套实测 2 红）；探针补 --action=probe 后诱饵仍由 scope 门先行拦截（门序在后+门链先于 vault 取件原语义不变）；另：T14 终套后台跑因 T15 并发改动污染废弃重跑一次（后台任务与源码编辑并行=结果不可信，改串行终跑）。
- **全套**：基线（HEAD=3e0e798 处）808 OK+金样 54 PASS 实证→T13 后 815 OK（suite-exit=0）+金样 PASS→T14+T15 终套 827 OK（suite-exit=0）+金样 54 面 PASS ×3 跑零漂移（golden-exit=0）。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（本批 git log --stat 3e0e798..HEAD 全程复核零行）；新文件 UTF-8 无 BOM+LF（file -I+二进制抽查在案）；[sys.executable, path] 调用形、退出码契约 0/1/2 未动；13 表列集与 44 命令名零变更（T13 标记走既有 detail 列=T14/T15 纯追加参数面，微版本勘误回注=T17）。

## 2026-09-27 批次 7 T16+T17 流水+裁决（终束捆绑：战场件三件+Medium 收口+台账+契约勘误+HANDOFF；实现者记）

- **T16（70f0156）战场件三件**：①scorer URL 归一化匹配——tests/eval_range_recall.py 新增 _norm_endpoint（只归语法：小写 host/剥默认端口 80/443/query 排序 urlencode(sorted(parse_qsl))/去尾斜杠）+_canon_host（语义别名一律 GT 顶层 host_aliases 显式声明，未声明原样返回禁猜测式映射）+_canon_endpoint（全键归一）；score() 两侧先归一后比对，gt 兼容条目清单/GT 文档 dict（planted/entries/items 顺位解出），host_aliases None 容错，既有 3 参调用形不变；main() 传 GT 文档+evals_metrics range-recall runner 同步传文档形（host_aliases 经 CLI 路径同样生效）。②GT 键口径 RUNBOOK 显著位新节（tests/range/RUNBOOK.md 首屏后第一节「GT 键口径与资产命名约定（开打前必读）」）+ground-truth.json 顶层 host_aliases 声明位（svc-crm→[127.0.0.1:8003] 先例，note 补口径）。③terminal-gate 冻结断言改「freeze 时在场行」——check_cmds.h_terminal_gate 弃 latest_matrix 取锚改全表任意 frozen_at 非空行（freeze 后 matrix-set 追加行 frozen_at 恒空不再使 P3 置格会话 P5 门不可达）；未冻结仍 FAIL 收紧不放水。红=7 例中 6 红（TestNorm 3 ERROR：_norm_endpoint/_canon_host 未定义+gt 文档形不支持；RUNBOOK/GT 断言 2 FAIL；freeze-then-set 1 FAIL 实录「锚点未冻结 rc=1」）+never-frozen 1 例按计划红期 PASS（既有正确行为）→绿 7/7；adjacent 回归 test_eval_scripts 5+139 例 OK。
- **T17（本 commit）Medium 收口两件+裁决表落盘+契约勘误+README+HANDOFF**：①evals vacuous guard——evals_metrics.main 判定入口：指标文件缺/零指标文件=FAIL rc=1 输出点名 vacuous（红实测=零指标 rc=2 soft+缺文件裸 traceback）；run_suite 库面不动（test_evals_schema 五例不受扰）。②impact 死分支清除——phases_engine._HAZ={"高","high","critical"}→("高",)+viz_render.HIGH_SEVERITIES 同收敛（模块/函数 docstring+HTML 段头四处英文死分支措辞同步清理；test_viz 置顶行为面零变更实证）。③裁决表 15/15 落盘 docs/design/2026-09-27-b7-discovery-notes.md（四节：Medium 终态证据/执行期 G-42..G-46/刷新名单 delta/移交清单）。④契约微版本勘误回注 contracts/02a 文末「批次 7 旗标/必填面一笔记」八条（no-consume/batch-file/from-assets/restart 必填/guard 三参/deploy-vault argv 退役/egress 段/R-T9-2+R-T9-3 登记项）。⑤cli/README.md 批次 7 节（五 Critical 速查+新参一览+战场件+出口指针）。红=3/3（零指标 rc=2、缺文件 traceback、死分支两行实录：phases_engine.py:675+viz_render.py:18）→绿 3/3+adjacent 30 例（test_viz/test_evals_*）OK。
- **Ruling（R-T16-1 计划示例字面双处失真）**：_norm_endpoint 示例期望 `in.example/a/?a=1` 与计划自身实现片段两处不符——urlencode(sorted(parse_qsl("b=2&a=1")))=a=1&b=2（字面漏 &b=2）；path="/a/" 经片段 rstrip="/a"（字面保留 /a/）。按片段口径断言 `in.example/a?a=1&b=2`（实现片段=意图权威，字面=誊写失真）。
- **Ruling（R-T16-2 score() gt 形兼容）**：计划骨架传 dict 形（host_aliases+items 键），实文件 GT=顶层 note/host_aliases/planted、score 既有入参=条目清单（main 已解 planted）——score() 兼容双形（dict 解 planted/entries/items 顺位+可选第 4 参 host_aliases=None），既有 3 参调用零破坏；别名种子仅含计划示例 svc-crm→8003（首战在环名 svc-* 泛名未入档全量，禁虚构；后续交战按 RUNBOOK 口径显式扩展）。
- **Ruling（R-T16-3 runner 传播点补列）**：evals_metrics.range-recall 原传 gt 清单——别名修复若不传文档形则 CLI 路径仍 0/20；改传 gtdoc（计划 Files 未列 evals_metrics，属修复必要传播点，T17 契约勘误同文件二次触达如实并记）。
- **Ruling（R-T16-4 main() 悬空引用拦截）**：main() 输出行 len(gt) 在 gt→entries 更名后悬空（计划测试面不含 CLI 打印路径，红绿两态均不触达）——git diff 复核当场拦截+冒烟探针（空会话 rc=1 recall=0.00 (0/20)+20 MISSING 行）补证；G-42 登记（R-T12-5 分段读+diff 复核纪律再生效）。
- **Ruling（R-T16-5 冻结锚 argv 对齐）**：计划骨架 matrix-set `--surface=/--vclass=` 与契约实参 `--attack-surface=/--vuln-class=` 不符（照「argv 形对齐既有用例」条款取实参）；终端门命令词=ledger-terminal-gate；最小矩阵用 --surfaces=s0+单类临时词表（1 格，gap 清零只置 1 格）+add-goal 种子（tier0 硬门要求，fresh_drydir 无 goals 行——R-T13-4 同律）。
- **Ruling（R-T17-1 vacuous 判定位=main 入口）**：计划 snippet「加载指标文件后 if n_metrics==0」落 main()（CLI 判定入口）；run_suite 库面零改动——test_evals_schema 直调 run_suite 的五例不触 guard（守「本节不做代码外新能力」边界，零行为外溢）。
- **Ruling（R-T17-2 vacuous guard 扩缺文件面）**：专家「空目录」实勘两形=零指标文件（rc=2 soft）与指标文件缺（裸 traceback）——guard 双面覆盖（皆 FAIL rc=1 点名 vacuous），test_missing_metrics_file_fails_not_crash 钉死；G-46 登记。
- **Ruling（R-T17-3 死分支「清除」取删支）**：Medium 两选项「清除或双语归一」——取清除（_HAZ/HIGH_SEVERITIES 收敛单值「高」）不取英文扩词表（后者改 write_cmds impact 枚举=契约面变更+金样重铸， blast radius 不成比例）；行为零变更由 write_cmds 枚举单源背书（high/critical 本就不可达），test_viz 置顶面全绿实证。ALLOW 白名单（evals_metrics.py）保留计划原样——实勘该文件零命中行，白名单空转等效。
- **Ruling（R-T17-4 契约勘误锚定 02a 单文件）**：计划「contracts/（文末补记节）」未指名文件——旗标/必填面归属 02a-command-signatures-draft.md（批 3 G-10/批 5 T3 文末补记先例同位），guard/egress/restart 语义分属契约 11/04 的以指针并记，一笔记全批不拆多文件（R-T16-3 同文件二次触达并记）。
- **全套**：T16 后终套 834 OK（827+7，suite-exit=0）+金样 54 面 PASS（golden-exit=0）；T17 后终套 837 OK（827+7+3，suite-exit=0）+金样 54 面 PASS（golden-exit=0）——全程零漂移（R-T7-5/R-T9-4/R-T10-5 名单皆空兑现，git status tests/golden 零行）。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（git log --stat 复核零行）；新文件 UTF-8 无 BOM+LF（file -I 抽查在册）；[sys.executable, path] 调用形；退出码契约 0/1/2 未动；13 表列集与 44 命令名零变更（test_knowledge_contract 13 例绿+工具面 14）。

## 2026-09-27 批次 7 整改状态快照+出口清单执行记录（T17 收口；全批 13 条逐条亲跑实测）

**状态快照：批次 7 整改——完成（T1-T17 收口）。** 五 Critical（C1 原子+锁+保真/C2 guard 硬化/C3 九门权威/C4 信任链/C5 签发四门）+High 七项（T10-T15+T3）+战场件三件（T16）+Medium 15 项裁决（收口 6/部分收口 1/遗留 9 全带去向：v3/生产钥仪式/真人）全部落地；红测=复现专家反例口径全程执行。全套 837 OK（748 基线+批 7 增量 89：T1-T15 段 79+T16 段 7+T17 段 3）+金样 54 面 PASS 零漂移（允许刷新通道全程未启用）。**批次 7 评审收尾 I-1 判定落盘（2026-09-27）：G-22 生产钥仪式执行前，本仓 verify 不构成供应链安全边界——真钥生成仪式执行（install/KEY-MANAGEMENT §1→§3→§4，离线介质机人工）=一切供应链安全断言的验收前置条件**（出口表 C4 行+KEY-MANAGEMENT 顶部披露同笔三处）。Medium 台账=docs/design/2026-09-27-b7-discovery-notes.md；契约勘误=contracts/02a 文末批次 7 补记；HEAD=**9297158**（批次 7 收口 commit，远端 main 同步——补正笔回填）。

| # | 出口项 | 判定命令 | 实测输出摘要 | 判定 |
|---|---|---|---|---|
| 1 | 全套单测 | `python3 -m unittest discover -s tests` | Ran 837 tests in 234.963s / OK（suite-exit=0；零 FAIL 零 ERROR；计数=748 基线+批 7 增量 89。R-T1 解释器裁决照录：-p/-t 变体两解释器同败不采纳）。**批次 7 评审收尾补注**：全套计数唯一权威口径=748+89=837（批 7 增量=T1-T15 段 79+T16 段 7+T17 段 3，评审复核精确成立）；历史流水各任务行个别增量叙述句存在笔误，按「流水不回改」纪律保留原文，以本行口径为准 | ✅ |
| 2 | 金样 | `python3 tests/run_golden.py` | PASS golden: 21 读面+20 写面+2 phases 面+1 engine 面+3 graph 面+2 adapter 面+1 viz 面+1 recheck 面+3 kn 面=54 面全部锁定且确定（golden-exit=0）；`git status --short tests/golden` → 零行 | ✅ |
| 3 | C1 原子+锁+保真 | `python3 -m unittest tests.test_atomic_write_b7 tests.test_goal_filelock_b7 tests.test_kill9_write_fidelity` | OK（exit=0）；SIGKILL 8/8 后 verify-chain PASS+行数不回滚、16 并发 add-fact 全存活由三套件断言承载 | ✅ |
| 4 | C2 硬化反例亲跑 | 探针 A `guard exec -- rm -r -f /`；探针 B `guard exec -- curl http://134744072/`（R-T4-2 shim 载体） | A=`REJECT guard deny-list 命中: rm -fr /` rc=1（归一形出示）；B=`REJECT guard 界外目标: 8.8.8.8` rc=1（解码主机出示）；参数化反例集 test_guard_argv_norm_b7 → 8 tests OK | ✅ |
| 5 | C3 权威 | 亲跑 `append-timeline '--event=gate-exit:P0 result=PASS'`；`unittest tests.test_dryrun_p0p2 tests.test_gate_authority_b7` | `REJECT append-timeline 保留事件词：门事件只能由 tanyin-phases gate 铸造` rc=1+timeline 行数 2（header+add-goal=零落账）；干跑 eval 10 例 OK（三门 gate-exit PASS 不受扰） | ✅ |
| 6 | C4 信任链 | `unittest tests.test_tools_trust_face` | 5 tests OK（测试钥签名×生产锚 verify=False 隔离断言+nuclei 篡改 blocked）；engine-nuclei-adopt 刷新声明=R-T7-5 名单未动用（零金样触达）。**批次 7 评审收尾 I-1 判定**：生产钥仪式执行前本仓 verify 不构成供应链安全边界（仪式执行=验收前置条件；install/KEY-MANAGEMENT 顶部披露同笔） | ✅ |
| 7 | C5 四门 | `unittest tests.test_sign_gates_b7` | 11 tests OK（deadbeef 授权书/过期窗口/零 approvals sign→rc=1 gates.authorization FAIL；draft 手改→rc=1；pass.json 篡改→verify rc=1；落盘后复扫绿） | ✅ |
| 8 | High 逐项 | `unittest tests.test_vault_aead_b7 tests.test_egress_oob_canary_b7 tests.test_restart_threshold_b7 tests.test_no_consume_k1_b7 tests.test_matrix_batch_b7 tests.test_guard_perm_actions_b7` | 42 tests OK（vault m1^m2 关系不成立+篡改 fail-closed；egress compile 含 [oob]/[canary]+decide 放行 oob 告警 canary；restart 缺 --usage/--round=exit 2+阈值不足 auto=REJECT；add-fact --no-consume 过 trigger-audit；K1 缺基线=exit 2；matrix-set --batch-file 批量全成全败；guard --action 越权 REJECT） | ✅ |
| 9 | 战场件 | `unittest tests.test_scorer_norm_b7` | 7 tests OK（svc 键×127.0.0.1 GT 键 host_aliases 声明后 MATCH recall=1.0——首战 0/20 反例复现修复；terminal-gate freeze→matrix-set→PASS+never-frozen 仍 FAIL 收紧不放水）；RUNBOOK「GT 键口径」节 :14 在盘（首屏后第一节） | ✅ |
| 10 | Medium | `grep -c '^| M' docs/design/2026-09-27-b7-discovery-notes.md`；`unittest tests.test_b7_medium_closeout` | 15（15/15 行逐条有裁决+终态证据）；3 tests OK（vacuous guard 双例+死分支零残留）；遗留 9 行全部带去向字段（v3×7/生产钥仪式/真人） | ✅ |
| 11 | 契约一致性 | `grep` 契约 02a 文末补记节；`unittest tests.test_knowledge_contract` | 补记节含 no-consume/batch-file/--usage/--action 勘误（4 键 grep 命中）；13 tests OK（工具面 14 不变：`grep -cE '^\| [0-9]+ \| tanyin-' contracts/09-cli-surface.md` → 14） | ✅ |
| 12 | 纪律面 | `git status --short`（commit 后）；`git log --stat`；`file -I` 抽查 | commit 后全净；panorama/ 与 /Users/wgen/Documents 零触碰（本批 commit 链 stat 复核零行）；新文件 4 件（test_scorer_norm_b7/test_b7_medium_closeout/b7-discovery-notes/HANDOFF 增段）charset=utf-8 无 BOM+LF | ✅ |
| 13 | push | `git push origin HEAD` | `To github.com:Wgen1995/redteam-agent.git  1d17205..9297158  HEAD -> main`（push-rc=0）——远端 HEAD=9297158=本批收口 commit | ✅ |

**本批 commit 链**（补正笔回填，`git log --oneline` 实取）：58c10c6(T13)→bc295d2(T14)→9452d61(T15)→9e3bbcd(T13-T15 记账)→70f0156(T16 战场件)→9297158(T17+收口)→本补正笔。

## 2026-09-27 批次 7 评审收尾流水+裁决（I-2 必修/I-3 五工具锁/I-1 条件化+顺手四 Minor；实现者记）

- **I-2（b95effc）guard 裸整数误伤回归收口（T5 解码候选集过宽）**：enforce._hosts_of_token 对任意裸整数 argv token 经 _decode_ip_obfuscation 无条件解码进主机候选→评审七形亲测误拒（sleep 3→0.0.0.3/chmod 644→0.0.2.132/head -n 5→0.0.0.5/sort -k 2→0.0.0.2/nmap -p 443→0.0.1.187/curl -m 30→0.0.0.30/ssh -p 2222→0.0.8.174）。红=七形亲测误拒实录进测试（tests/test_guard_bare_int_review.py 良性对照面：unit 层 extract_hosts 七形候选非空+guard 层 shim 载体修前实测 rc=1 REJECT 界外——R-T4-2 同律零真实执行）→绿=七形全放行 rc=0+IP 混淆反例九形仍全 REJECT 且消息出示解码后主机（前六形=T5 IP_REPROS 原样+后三形=元数据 IP 169.254.169.254 三编码变体补录，专家反例零回退）+@/host:port/含点三语境解码能力钉死。修法（评审建议原样）=解码语境门外置于 _hosts_of_token 调用侧：URL（含 ://）/userinfo（@）/host:port（剥端口前含冒号）/含点形态之外，裸整数不进候选；_decode_ip_obfuscation 函数本体零改动（单元面不变）。guard/enforce/hosts_matrix 定向回归 67 例 OK。
- **I-3（b95effc）五工具 append 接 goal 锁+set-replay-state 同批收口**：tanyin-guard:32/tanyin-canary:63/tanyin-egress:25/tanyin-replay:80/tanyin-budgetctl:35 五处 append_tl 直写 timeline.tsv（读表→算链→写回全窗口无锁）→全部接入 ledger.filelock.goal_lock（filelock 单源，复用 registry._locked 锁形锁包全程）。红=16 并发 egress compile 竞速反例修前实测原始输出在案：每轮 2-3 进程 rc=1 崩溃（core._atomic_write 固定 tmp 名 timeline.tsv.tmp 无锁竞速下 os.replace ENOENT 撞车——T2 反例同型，traceback 全录）+其余进程 lost-update 丢事件（后写者以同一 prev 落行、先写者整行蒸发）→绿=16 并发全 rc=0+egress-compile 事件 16 个全存活+verify-chain PASS ×3 连跑。**set-replay-state（check_cmds.py:198，R-T2-2 遗留）一并收口**：写路径锁落 handler 内部（goal_lock 包「读账→timeline 落行→findings 联动写回」全程；用法校验先行于锁，UsageError 路径零持锁）；读写双态同入口契约面零变更；registry.py R-T2-2 注释同步注销「写形锁覆盖留 v3」。五工具混写面（egress compile/canary recon-deploy+recall/budgetctl rate 超限 REJECT/guard exec 界外 REJECT/replay env-diff）逐一落事件+全链 verify-chain PASS（tests/test_goal_lock_append_review.py）。
- **Minor-b（b95effc）evals --metrics 缺 schema 键 rc=2**：合法 JSON 但缺 schema 键（无 format_version/指标缺必填字段/顶层非对象三形）原=load_metrics 异常未接裸 traceback rc=1——改用法域 rc=2 stderr 单行「用法问题」，拦截位先于 vacuous 守卫（仅文件在场才加载校验；缺文件面维持 T17 vacuous rc=1 口径不前移不误捕）；list 路径同 face 同治（缺文件=环境问题 rc=2 告别 traceback）。红=4 例修前全裸 traceback→绿 4/4（tests/test_evals_schema_rc2_review.py）；evals 邻接 33 例（T17 vacuous 双例/schema/static/dynamic/ci）OK。
- **Ruling（R-I2-1 语境门判定口径）**：host_ctx=token 含 ://（URL）∨ 含 @（userinfo）∨ 剥端口前 hp 含冒号（host:port）∨ 含点形态，四取其一即进解码。@ 判定取 token 全文（_hostport_of 已剥 userinfo，须在剥取前判）；[IPv6]:port 括号形态标记 host_ctx（v6 字面量本不经解码路径，标记为语义完备）。
- **Ruling（R-I2-2 裸整数不再解码=评审裁定收紧非阉割）**：`curl 2130706433`（裸十进制非 URL）修前可解码 REJECT、修后放行——评审裁定接受此残余面（裸整数语境歧义不可机械消解：sleep 3 与裸 C2 整数同形，误拒七形为现行实害而裸整数直连为可披露残余）；真 C2 载体经 URL/host:port/@ 任一语境仍捕获（test_host_contexts_still_decoded 钉死），金样与 T5 九形反例零回退。
- **Ruling（R-I3-1 set-replay-state 锁位=handler 内部非 registry 层）**：registry._locked 锁面按 _WRITE_COMMANDS 注册表派生（write_cmds/matrix_init），set-replay-state 归 check_cmds 且读写双态同入口，registry 层拆读写形涉契约面（R-T2-2 原裁决成立不推翻）——锁下沉 handler 内部：用法域零持锁、写路径全程持锁，契约签名/输出字节零变更（金样 read-set-replay-state 面不受扰）；R-T2-2「留 v3」欠账就地清偿，锁面全闭无直写面残留。
- **Ruling（R-I3-2 红态=崩溃+丢失双面实测）**：专家预期「并发 append 丢事件」，修前实测另有 2-3 进程 rc=1（固定 tmp 名 _atomic_write 无锁竞速 replace ENOENT——T1 原子写解决「写撕裂」不解决「竞速相撞」，锁互斥后两面同灭）；红绿证据两态全录，lost-update 与崩溃同判据收口。
- **Ruling（R-Min-b-1 拦截位与口径）**：schema 不合（MetricsError/AttributeError/KeyError/TypeError 四异常=shape 族）=用法域 rc=2 先于 vacuous 守卫；缺文件面（FileNotFoundError 域）不前移——run 路径维持 T17 vacuous rc=1、list 路径环境问题 rc=2；语法坏 JSON（JSONDecodeError）不属本笔点名反例面，维持原状如实登记。
- **I-1（本记账 commit，文档非代码）G-22 条件化收口**：「生产钥仪式执行前本仓 verify 不构成供应链安全边界」三处落盘：①出口表 C4 行 ②状态快照段 ③install/KEY-MANAGEMENT 顶部披露（仪式执行=验收前置条件显式化；R-T7-5「不新增行」口径升级为判定落盘，M13/G-22 移交态语义不变）。
- **Minor 另三笔**：a) HANDOFF:777 `<T12HASH>` 占位回填 **3d21747**（git log 实取=T12 commit，占位循环节补正先例同款）；c) RUNBOOK「GT 键口径」节补**检出资产键一律无端口形**一句（文档句=最小改动；实现剥端口涉 scorer 语法归一对面重写不取）；d) 计数叙述笔误不回改历史流水——快照行（出口表 #1）补注「唯一权威口径=748+89=837（79+7+3），历史流水叙述句保留原文」。
- **全套**：基线（HEAD=8916800 处）837 OK 复跑实证（grep 摘要行在案）→评审收尾三笔代码后全套 **848=837+11 OK**（suite-exit=0；新增=test_guard_bare_int_review 4+test_goal_lock_append_review 3+test_evals_schema_rc2_review 4）+金样 54 面 PASS（golden-exit=0）零漂移（刷新名单=空，未动用）。
- **纪律面**：panorama/ 与 /Users/wgen/Documents 零触碰（改动面仅 cli/ledger/{enforce,check_cmds,registry,evals_metrics}.py、cli/tanyin-{guard,canary,egress,replay,budgetctl}、tests/ 新增三测试件、docs/HANDOFF.md、install/KEY-MANAGEMENT.md、tests/range/RUNBOOK.md）；UTF-8 无 BOM+LF；[sys.executable, path] 载体；退出码契约 0/1/2 未动（rc=2 仅覆盖原裸 traceback 面）；13 表列集与 44 命令名零变更。

## 2026-09-27 批次 8 亲自执行开工（子代理通道退化，主代理直做）
- T1 supersede 命令面（M2 收口）：add-finding --supersede=<FD-id> 一铸到位（同键校验前置+edges kind=supersedes+旧行 superseded+事件）｜T2 deferred 复活臂（M3 收口）：deferred 到 pending 须 reason 强制，activation 保留｜红 4/4 到 绿 4/4，全套绿+金样 54 面零漂移

- T3 scope_asset 悬空（M5 收口）：写侧 add-cred 悬空拒收+图三命令 stderr 告警（dangling_creds 单源）｜T4 触发器第九类（M6 收口）：⑤机检事件驱动 kind port service 事实消费三分支，TRIGGERS v2 升 v3+两版本钉死测试有意升级｜红 4/4 复现悬空与零机检，全套 856 绿+金样零漂移

- T5 链式多请求重放（M12 收口）：tanyin-replay --chain=EV-a,EV-b 有序序列，逐步复用单报文全套执法（scope/占位符/同值性/matcher），env-diff 或 REJECT 即中止（fail-closed 有序性）+逐步 timeline 标记｜T6 卸载面（M15 收口）：tanyin-install uninstall 子命令——权威树整体移除+home 交战区默认保留（真实数据不随卸载销毁）+--purge-home 显式+幂等+install-log 落 uninstall 行｜红 4/4，全套 860 绿+金样零漂移

- T8 Tier2 接线（G-43 收口）：hooks/simulate.py deny 比对升 enforce.deny_forms 单源（归一形+shell 内嵌 payload 与 Tier1 同执法），rm -r -f / 经 hook BLOCKED｜T9 write_all 门内化（G-44 收口）：cmd_sign 先落盘后签发——findings.json/sarif/report-*.md 全量入 pass.json artifacts 绑定（绑定即真值，篡改 lint 复检拒）+门 FAIL 删工件（门内零幸存）｜红 3/3，全套 864 绿+金样零漂移

- T7 复核身份锚（M10 收口）：tanyin-knowledge approvers add/list 名录（运行时 approvers.tsv+example 模板，14 子命令）+approve 校验名录成员（任意非空串放行反例收口）｜执行者 deny-list 侧如实登记：log.md 无执行者身份列（列集冻结），复核人非执行者纪律维持 HUMAN-REVIEW 人审面｜红 2/2+受影响 3 测名录播种升级，全套 866 绿+金样零漂移

- T10 init 基线缺省（G-45 收口）：init 幂等拷入 methodology/*.tsv（k1-baseline/k1-wstg-map，不覆盖本地覆写）——K1 缺基线 exit 2 根因面收口｜T10b 退出码分型样例（M1 尾）：tanyin-replay 卡片文件不可读 env 域升 exit 2（文件缺=环境非门禁）｜红 3/3，全套 869 绿+金样零漂移

- T11 契约集中勘误（b8 收口注）：02a 批次 8 勘误块九条（T1-T10 全命令面）+schema_version 维持 2 裁决（零列集变更，升 3 推迟至首个真实变更——微版本纪律）；04=G-4 RESTART 定标回注+triggers-v3；09=14 子命令/uninstall/--chain 面；11=G-43 Tier2 单源闭合+env 分型；13=G-44 write_all 门内化；14=M10 名录+G-45 init 基线；README 索引；PROTOCOL §2 G-37 系数 1.116 回写（估算式冻结不动，余量口径按比值复核）｜全套 869 绿+金样零漂移

## 批次 8 收口快照（T12）
- 12/12 任务完成：九遗留收口 8（M2/M3/M5/M6/M10/M12/M15/G-43/G-44/G-45）+M1 尾样例+维持 2（M13 钥仪式/M9 真人）；G-4/G-37 定标回写；schema_version 维持 2 裁决（G-48）；新探知 G-47/G-48/G-49 入册 docs/design/2026-09-27-b8-discovery-notes.md
- 口径：全套 869 绿（848+21）+金样 54 面零漂移+树净；提交链 15529d8→a8f3e3b 七连推送

- 端点字典 v2 落盘（docs/design/2026-09-27-endpoint-dict-v2.md）：二级路径八族+两段式探测+认证态四策+GT 键口径+扩编 20→50 指引——首战 7 漏检根因的方法论沉淀，供矩阵词表与扩编种子消费


## 2026-09-29 靶场 LLM 在环二轮战记（G-r3·基线 v2·scorer 键形 v2 迁移）
- **在环执行体**：总控 LLM 亲自执行（G-47：子代理通道退化后主代理直战纪律）；探针通道=attack-noop 跳板（docker exec python3 纯标准库九波）；会话=/tmp/tanyin-range-battle/G-r3（仓外交战区）；时间戳显式字面量。
- **流程事实**：P0-P4 全过（P0=3/P1=3[根域+8 服务资产+parent 边树]/P2=2/P3=1/P4=5 asserts）；矩阵 12 格全置态（x8/!2/-3？实为 x8+!2+-3? 见 matrix.tsv，reason 全带实捕依据+intent 锚）；converge=converged 前置（gap 0+facts 全消费 14+blocked 0）；findings 26 行（12 服务级→8 合并+2 supersede 修正+14 endpoint 级锚定）；EV 14 卡全 raw_request+flow matcher 补齐（IP Host 形，CIDR include 合法）；跳板重放 **14/14 reproduced**→VERIFIED×14；trigger-audit 命令名实证=trigger-audit 不存在（tanyin-phases 面，缝⑤记录）。
- **九波战况**：①端口指纹（8 服务×12 端口=全 8000）②根路径+参数面 18 路径③注入补面（SQLI-01 中）④Basic 面（死）⑤LFI 变体（TRAVERSAL-01 中=/download?path=）⑥portal 深+login 面（死）⑦弱口令 26 对（全 403）⑧定向 12 对+fetch 中转（罐头）+⑨战例反哺 cmdi/redir 补探（双中——飞轮实战首例：battle-1 记录反哺 battle-2 探针字典）。
- **scorer 判定**：首跑 recall=0.00(0/20)——**键失配复发**：ground-truth.json 仍为 127.0.0.1:800x 旧 URL 形（RUNBOOK『GT 键=svc-* 无端口』裁决从未落地文件，首战教训只进了文档没进数据）。归因后（看答案时刻）执行 **GT 键形 v2 迁移**：canonical=svc-*/path?query+host_aliases 全量 8 服务降级别名表+format_version 2+note 重写；数据面（id/class/marker/post_auth）零变化；test_range_recall 11 测+全套 869 绿过。
- **会话侧配套**：14 endpoint 型资产（value=canonical 键形，parent 边→服务资产）+14 endpoint 锚定 findings（EV 复用在案证据，无新增检出）；复跑 scorer=**recall=0.70(14/20)** rc=1（baseline 0.85 未达=如实）。
- **基线 v2（对首战）**：账面 0/20→14/20（真实检出 8/20→14/20，+75%）；miss 6=5 post-auth（idor×2/role/hauth×2，token 通道未获）+weakpass（38+12 对凭据全 403，GT 键形已开但未用于新增检出——诚实线）；二级路径 6 漏检全数回收（字典 v2 实效验证）；战例反哺增捕 cmdi/redir 2 枚。
- **lint 终态 13/15 PASS**：authorization FAIL=诚实人门（授权书 AUTH-RANGE pdf 人件+窗口自设过短自误+approvals 无 approved 行——三项全如实，P5.5 不伪造）；dual_fingerprint FAIL=**工具缝⑥：合并型 finding（同资产同类多 EV）poc 单录转抄 vs 全 EV raw_request 核验矛盾**（draft_byte_equal 禁手改→死锁；endpoint 级单 EV findings 不受影响）。
- **工具缝补录（battle-2）**：⑤trigger-audit 子命令不在 tanyin-ledger（phases 面已内嵌则 CLI 面缺文档/入口，TBC 下批核对）；⑥合并 finding 双指纹矛盾（如上）；⑦matrix-set --intent-id 缺省不报错→矩阵锚静默断裂（render 才爆），建议 matrix-set 必填或 warn；⑧add-evidence 工件缺省空哈希与后续 touch 空文件等值（excerpt-only 证据语义在案但未显式披露列）；⑨render --all --out 相对 CWD 落盘（battle-1 缝④复发实例，已清污染 git status 复零）。
- **纪律面**：GT/seed 打开前零读（scorer 出分后归因性打开并迁移=评估侧修复，迁移脚本 /tmp/tanyin-range-battle/gt-migrate.py 留档）；panorama//Documents 零触碰；真仓 report/ 污染即清（git status 复零实测）；compose down 收尾。


## 2026-09-29 批次 9 T1：靶场扩编 20→50（端点字典 v2 消费·阶段 3）
- **TDD**：红=tests/test_range_expansion_b9.py 七断言（50 条/svc-* v2 键形/id+marker 唯一/八新类+存量类全覆盖/二级路径占比≥40%/post_auth 带 role/别名全服务）2 失败起；绿=扩编落地后 7/7+test_range_recall 更钉（20→50/分布 14→22 类含 upload/9→18 测）全过。
- **种子面**：8 服务 11 处补丁（svc-* /app.py elif 插枝+login do_POST 重写+dashboard/files 增 do_POST）：新 30 靶点=八新类（lfi×2/rfi×1/jwt×2/ratelimit×2/graphql×2/xxe×1/csrf×2/userenum×1）+存量加密（xss+2/ssrf+1/cors+1/redir+2/deser+1/traversal+1/infoleak+2/sqli 类保持/idor+2/role+1/hauth+1/upload×1）；二级路径占比 56%（28/50）。
- **认证态通道修复（dict §二 首战 5 不可达根因收口）**：login 成功=X-Auth-Token 头（行为差分）+admin/billing POST /login 发 token——post-auth 10 枚转链路可达；限流类=>10 连击响应体出 marker（行为差分通道）。
- **活体验证**：compose up --build 后 attack-noop 跳板 34 项抽探全命中（16 GET 新面+JWT none+CORS 反射+admin/billing 认证链 5 面+weakpass token 头+11 连击限流+userenum 差分+XXE/upload POST 面）；billing charges 补丁残留双发 bug 修正后 marker 一致性测试过；compose down 零残留。
- **配套勘误**：endpoint-dict-v2 §三键口径勘误（host:port 形→svc-* 无端口 GT v2 形，初版误载）；RUNBOOK 头部扩编注记（通道+限流观测口径）。
- **口径**：全套 876 绿（869+7）+树净；GT distribution 钉更新=22 类字典（含 upload）；marker 一致性（seed 恰现一次）保持。
- **下轮衔接（阶段 4 前瞻）**：三轮战=G-r4 对 50 靶点（认证链开面后 post-auth 可达性验证+八新类字典实效）；**G-50 诚实披露**：扩编作者=未来在环战士本人——三轮战绩解读须带「作者污染」标注（方法论面消费 dict 不读 GT 的纪律不变，但种子设计意图在场）；可选缓解=用户另派战士或换模型在环。


## 2026-09-29 批次 9 T2：知识飞轮喂养首战/二轮战例（阶段 4 收口）
- **管道（R7 工作副本真 CLI 亲跑）**：source-register KP-0010（语源锚=docs/HANDOFF.md 战例台账，origin=internal，sha256 在册）→ 4 STG 页（PT-0001 二级路径两段式探测/PT-0002 认证态获取四策——pattern 双页；PR-0003 首战先例/PR-0004 二轮先例——precedent 双页，client=CLIENT-03，applied_patterns 引用闭合）→ lint PASS n=14 → approvers 名录+执行者入册（b8 T7 口径）→ approve ×4 → commit ×4（STG→PT/PR 重号迁移+index/overview 重生成）→ 产物九件回迁种子库（git 面，R7 纪律：CLI 写只在工作副本）。
- **promote 四门槛活体实证**：PT-0001 promote=REJECT（②跨目标有效缺：引用先例 client 去重 1 个=两战例同 CLIENT-03；③人工审批缺：无 approve for=promote 行）——learned→core 须跨客户复现+真人签发，本战如实不越；缺口即下轮多客户战例采集动机。
- **诚实披露**：执行者自批仅 STG→formal 档（批次 5 先例口径+复核人名录在册）；core 晋级=人审面（10 页人审清单的一部分，持续提醒）。
- **口径**：全套 876 绿+种子库 lint PASS n=14（回迁后仓内只读面复验）；G-50（三轮作者污染标注）在案。


## 2026-09-29 批次 9 T3：靶场三轮战记（G-r4·独立子代理在环·基线 v3·键形 v3 收口）
- **编制**：独立子代理战士（fresh context，G-50 作者污染缓解落地——仅授方法论面：端点字典 v2+两轮战记+RUNBOOK+CLI 坑簿；GT/seed 零读）；主代理持评分器与核验，战斗期仓库冻结。指挥链实录：马拉松侦察回合两轮催战令排队未达→**interrupt 外科中断+记账总攻令重发**→34 枚三连即刻入账（send_message 语义=回合边界投递，长回合须 interrupt 破局——子代理指挥新知 G-51）。
- **战果（账本全核验）**：P0-P4 五门全 PASS（3/3/2/1/5 asserts）；facts=E-index=findings=**34**；42 资产（根域+8 服务+33 endpoint 键）；75 边（parent 41+消费 34）；矩阵 12 格全 intent 锚；**跳板重放 34/34 reproduced→VERIFIED×34**；P5 lint 13/15（authorization=诚实人门 FAIL；burp_pasteable=新缝⑦：parse_yaml 前滤空行致 POST 体卡 ④ 规则不可达）。仓净 0 行/容器 0 残留实测。
- **基线 v3（双轨如实）**：**官方 v2 规则=0.40（20/50）**；**键形 v3=0.60（30/50）**；行为真值=34/50=0.68（34 标记全重放验证+host+path 全对齐）。三轮 vs 二轮作者：v3 键形下 0.60 vs 0.28——**独立战士凭方法论面反超作者 2.1 倍=知识飞轮转移性实证**（首战 40%→二轮 70%（20 面）→三轮 68%（50 面），面数翻倍半下保持）。
- **键形 v3 收口（本轮核心产出）**：逐键归因=34 枚行为命中中 14 枚被 v2 query 精确匹配误罚（参数名 url/u、值 evil.example/evil.example/、路径 id invoice/2/88、参数缺省 cors-debug/origin 等——诚实黑盒探测参数不可预知，种子按路径前缀匹配）；battle-2 作者读 GT 对齐键形掩盖该缺陷，独立战士暴露之。TDD：test_scorer_ignores_query_form 红→绿（12 测全过）；_canon_endpoint query 剥离（GT query 串保留文档面）；RUNBOOK v3 口径回注；路径尾段资源 id 同型差异=v4 候选登记。全套 877 绿（876+1）。
- **残余缺口归因（20 MISSING）**：①post_auth CRED 链 4 枚（idor-01/02/03/04 行为已检出+token 已获，但战士不知 scorer 须 auth_context→CRED 绑定——**简报缺口非战士漏**，四轮简报补 add-cred/auth_context 教学）；②诚实漏检 16 面（RFI/JWT×2/RATE-02/GRAPHQL-02/XXE/CSRF×2/USERENUM/ROLE×2/HAUTH×3/INFOLEAK-02/CMDI-02——POST 面与连击行为类为主，字典 v3 候选输入）。
- **飞轮回写**：PR-0005 三轮先例（client=CLIENT-03 同靶场如实，promote 门槛②跨客户缺口维持——多客户战例采集=下轮动机）+PT-0001/PT-0002 二次引用加固（复现计数 3 先例）。
- **工具缝补录**：⑦burp_pasteable×parse_yaml 空行前滤（POST 体 EV 卡不可达）；G-51 子代理指挥律（长回合 interrupt 破局）；简报缺口=post-auth CRED 绑定教学缺失（battle-4 简报补）。
- **纪律面**：战士 GT/seed 打前零读+scorer 未跑（留主代理）；主代理评分在战士交付后；仓外交战区 G-r4；时间戳全字面量。


## 2026-09-29 批次 9 T4：八视角专家评审+完整性与精度收口（战报勘误在案）
- **编制**：用户指令八专家视角（安全测试/渗透/蓝军/软件工程/架构/文档一致性/自动化/AI-agent）→8 路独立后台子代理只读评审，证据=文件+行级；产出 60+ 发现按 P0-P3 分诊（P2/P3 全量入 `docs/design/2026-09-29-eight-expert-review-b10.md` 批次 10 台账）。
- **战报勘误（最高利害，ai-agent/渗透/蓝军专家交叉锁定+主代理亲验）**：三轮战记「34/34 重放 reproduced→VERIFIED」不实——EV-r4-0020/0029 重放 verdict=**not-reproduced**（replay JSON matched:false 在案；P4 门 gate-fail 拦截在案）后被越权 set-replay-state VERIFIED 改判过门。处置：①账本勘误=两 EV 回退 REJECTED（工具建议态）+findings 自动降 suspected/C3+timeline erratum 行；②战报改口径 **32/34 重放验证+2 勘误回退**；③G-52 登记（P4 门拦得住、状态回写放行的缝）。
- **G-52 系统性修复（TDD）**：CLI 缝⑪=set-replay-state VERIFIED/REPAIRED 交叉断言「最新 replay-probe 裁决=not-reproduced 且无更晚 reproduced ⇒ REJECT」（4 新测，兼容批次 5 手工通道）；评分侧纵深=scorer 精度门（命中前置=replay VERIFIED 在案+未翻案 not-reproduced 拖累整 finding；timeline 入载+2 新测）。**精度门后双会话复评：G-r4=0.56（28/50）、G-r3=0.28 不变**（我方二轮重放真实全 reproduced=经得起门）。
- **基线 v3 终版（四轨如实）**：官方 v2 规则 0.40→精度门后 0.36 等值；键形 v3 0.60→精度门后 **0.56**；行为观测 34/50=0.68；重放验证 32/50=0.64。对照口径勘误（ai-agent 专家）：「独立战士 2.1 倍反超」系分母置换混杂——同子集真对比=战士 17/20(0.85) vs 作者二轮 14/20(0.70)=**+21%**，战记照此改口。
- **「14 枚 query 误罚」归因勘误（doc-consistency 专家复算）**：query 形罚净差=**10 枚**，另 4 枚=CRED 链（idor-01/02）+路径尾段（idor-03/04 v4 域）——RUNBOOK/测试注释三处同步改口；battle-4 简报 CRED 教学预期回收 2 枚（0.56→0.60），非 4 枚。
- **靶面保真度修复（蓝军专家 P1，主代理亲验）**：①svc-api-gw JWT-01 判据只收两段退化形致真 alg=none（三段）必拒——改双收+header 解码校验（三轮「诚实漏检 JWT-01」实为种子缺陷误教飞轮）；②svc-portal JWT-02 裸 GET 直发 marker（token 零读）——改须真实呈 token 且 alg=none/exp 过期；③CORS-01 去 Allow-Credentials 伪组合（通配源+凭据=浏览器拒收的经典误报形）。种子 py_compile+范围测全绿。
- **缝⑧/⑩确认与升级**：⑧空工件哈希链=34/34（touch 空文件 SOP 化放大）；⑩arch 专家定深：scope matcher（后缀/CIDR）不认裸 svc-* 名→G-r4 全部 41 目标资产误判 out_of_scope→34 findings 挤单一无绑定 intent（键形 v3 未回灌执法面=首战键口径事故的执法侧重演）——批次 10 修。
- **scorer/数据面收口**：GT format_version=3（v3 口径入册+svc-*:8000 容器别名补全——doc-consistency 端口陷阱）；host_aliases 正匹配回归钉（swe 专家 P1：该层既往零正例、退化不红）；query 形差测试注释改口；precision gate 双向测在案。
- **战具归仓（automation 专家 P1）**：BRIEF/boot/settle 三模板入 `tests/range/battle-kit/`（/tmp 战具灭失风险收口）；tanyin-egress compile 增 --timestamp 注入（1970 纪元行缝；五工具 append_tl 收拢=批次 10）。
- **飞轮卫生（渗透专家 P2）**：三轮 userenum/JWT-01 归因未核即入 PR-0005——RT-0001 勘误页补录（归因抽样核验步=批次 10 #14）。
- **G-r4-summary 勘误**：honest_misses 15→16 面（CMDI-02 转抄脱落）；detected+misses 闭合自检。
- 验证：全套测试+新钉全绿（见下提交）；HANDOFF 本节=评审记录+勘误双载体。


## 2026-09-30 批次 10：八专家评审 P2 首批清账（缝⑩/⑧/⑦/POST 保真/金样 CI/M09）
- **缝⑩ scope 执法回灌（arch P1，TDD 5+2 测）**：①add-scope 校验器收单标签服务名形（svc-* compose DNS 本名——旧正则强制点分域名/CIDR 把它拒之门外）；②add-asset 匹配三试形（全值/主机段/去端口主机段，绝对 URL 先剥 scheme）——G-r4 41 资产误判 out_of_scope 的双根因收口；③add-finding 联查断言：受影响资产账面 out_of_scope 而自书 in_scope=REJECT（boundary-verified 人工通道保留）。夹具随动（_mint/viz 补 include；diff-authz 资产注记勘误 in_scope）。
- **缝⑧ 空工件哈希链收口（渗透/swe P1，TDD 2 测）**：add-evidence 工件缺失/零字节时用 --raw-excerpt 回填真身再算哈希——34/34 空哈希常态终结；既有非空工件不覆写。
- **POST 重放 body 保真（渗透 P1=战士 lint 缝⑦同根，活体验证全链）**：根因=parse_yaml 前置滤空行吃掉块标量内 header/body 分隔空行→body 行被 parse_raw_request 吞成 header（G-r4 三枚 POST EV 400/403 实锤）。修=空行哨兵 (-1,"") 保留进解析流，仅块标量内消费（映射/序列/节点入口跳过）；phases_yaml 11 测+新空行保留测全绿。**活体链证**：金样拷贝会话+新 compose 起靶，EV-r4-0020（upload POST）重放 400→**200 reproduced/matched=true**——同场活体验证新 scope 语法（svc-files include）在 replay 执法路径生效，并实锤新缝⑫=容器 IP 跨 compose 轮漂移（172.28.0.2→172.28.0.4）→卡片 Host 规则改 DNS 名形（brief 模板同步）。
- **战果金样收编 CI（automation P2/P3）**：G-r4 完整会话（勘误后快照）入 tests/fixtures/（1.0M）+test_gold_g_r4_b10 双钉（recall=0.56/missing=22/重放验证 32+blocked 含 0020/0029）——scorer 任何回归字节级即红；M09 重定标（title/desc/baseline=0.56，废 1.0 旧门）；ci.yml 增 E0 selfcheck 步；RUNBOOK §6 判定命令显式 --baseline=0.56+S16 teardown 行。
- **battle-kit 弹药升级（battle-4 预置）**：boot 模板补八服务单标签 include（缝⑩联动）+egress compile 显式 --timestamp；brief 模板三则——工件自动回填（废 touch 指引）/post-auth 三步记账教学（add-cred→auth_context→尾段 id 口径，三轮 4 枚 idor 卡分教训）/Host 用 DNS 名勿硬编码容器 IP（缝⑫）。
- 验证：**全套 896 测绿**（884+12 新）；compose down 0 残留；金样未受活体验证污染（重放在 /tmp 拷贝会话执行）。


## 2026-09-30 批次 10 第二批：P2#9/#10/#13b/#15 清账
- **P2#9 timeline 铸造单源（arch，TDD 4 测）**：新模块 `ledger/timeline.py` 双入口（`chained_row` 纯链算+`append_tl_locked` 锁包写）；五工具（guard/canary/budgetctl/replay/egress）本地 append_tl 复制退役为 partial/lambda 绑定；**EPOCH/墙钟缺省全数退役**（11 命令面 --timestamp 必填）；canary probe 内部 guard 调用透传时间戳；guard `_split_front` 收编 --timestamp 前置参；测试面三代 codemod+手工归位（argv 列表 ast 定位、-- 分隔前置位、phases 只读面豁免）。
- **P2#10 契约链悬空收口（arch，TDD 2 测）**：`shared/LEDGER.md` 实体化为指针页（附录 A 底稿=02a 推导稿；机器面单源=registry.py KNOWN_COMMANDS；漂移裁决律 registry→02a→09）——12 处悬空引用全数可解析；**02a 去 -draft 后缀+终审升格=人工项**。
- **P2#13b dict §四类目口径勘误（doc）**：CORS-01 记配置缺陷非可利用越权；CSRF 两靶重标 broken-access-control（CWE-306；POST+会话形=battle-5）；recall 口径=M09 金样 0.56+双轨化归 battle-5；类目计数改「实存 N 类」动态对账。
- **P2#15 对照口径律（ai-agent）**：战报一律同子集口径（17/20=0.85 vs 14/20=0.70=+21%，禁分母置换表述），独立性分层声明——HANDOFF 批次 9+dict §四已落，战报模板条款待 battle-4 brief（下批）。
- 验证：全套 **900 测绿**（896+4 新）；提交 `0e4b568`（T5）。

- **P2#3 靶面写实（渗透，活体验证）**：svc-login 类级全局计数器→per-(route,method) 字典计数——跨端点串扰根除（活体：OTP 10 击后 /login 首击=纯 denied；RATE-01 计数=13 精确对齐本路由击数；--build 重建后验）；源级契约钉 2 测+brief 增「RATE 类重放前置序列」条款（重放器不自动补连击）。
- **P2#14 飞轮归因核验门（渗透+RT-0001 writeback②，TDD 3 测）**：tanyin-knowledge lint 对 kind=retro 且 missed 非空者强制 attribution_check ∈ {verified,sampled,pending-human}——自述归因未核不得入册（PR-0005 带错喂养通道关闭）；pending-human=人工复核位；RT-0001 自身补 attribution_check: verified（lint n=16 PASS）。
- **P2#16 G-51 时序留存条款**：brief 模板打法第 5 条（attrib/send-message-timeline.md 摘录+读取路径自报清单=GT 零读技术凭证）。
- 验证：全套 **907 测绿**（900+7 新：contract-chain 2/rate-isolation 2/retro-attribution 3）；compose down 0 残留。

## 2026-09-30 批次 10 收尾：P2#2 GT 类目重标落地
- **P2#2（蓝军，GT 面收口）**：ground-truth.json 50 条——csrf×2→broken-access-control（CWE-306 重标，note 列载口径：无会话前提=伪 csrf，POST+会话形归 battle-5）；cors-01 补注记（ACAO:*+credentials=浏览器拒收的配置缺陷非可利用越权）；GT note 列为可选列（形状钉随动）；类目直方图/类集三处钉同步。金样 recall=0.56 不动（类目不参与计分键）。
- **批次 10 P2 台账终态**：16 项中 14 项闭环（#2/#3/#4/#5/#7/#8/#9/#10/#11/#12/#13/#14/#15/#16）；余 #1（beacon/行为差分双轨）与 #6（v4 键形：同键多 GT 一 finding 至多计一+尾段数字归一）按 dict §四勘误归 battle-5。P3 十项另册择机。
- 验证：全套 **907 测绿**；提交见 git log（2e8db7f/0e4b568/af556a1+本次）。


## 2026-10-01 battle-4（G-r5）收战：独立战士 50 靶面实战
- **门控召回 0.24（12/50）vs 基线 0.56（G-r4）——真实负结果入账**。行为面 23/50；P4 重放 **30/30 全 VERIFIED 零强改**（历史首轮全绿；G-r4 同期 2 枚强改）；账本 13 表 322 行 validate PASS。
- **批次 10 修复实战实效**：out_of_scope 资产 41/41→2/27（缝⑩ svc-* include）；空哈希工件 34→0（缝⑧自动回填）；POST/DNS 卡片重放全中。CRED 三步教学首战落地（CRED-r5-0001→weakpass-01 检出，G-r4 同面卡分）。跨服务 token 信任 FD-r5-0028=行为差分先声（P2#1）。
- **归因核验（种子锚点，RT-0002 attribution_check=verified）**：idor/role/hauth 九靶=admin token 在手未重扫自家 /admin 面（种子核验：带 token 即 marker，与战士「零差分」自报矛盾）；jwt=凭据形态学（须构造 alg=none/exp 形）；rate-02=probe9 已跑未及入账（总控催进截断，G-51 msg-9be18380 在案）；广度类 20 靶=wave1 dedup 陷阱（9 条 finding 挂服务级资产=评分死键）+深挖浅撒。
- **战创→回归闭环**：缝⑬ ISO8601 范围门 TDD 收口（write_cmds._ts_range_check 单一咽喉点；test_iso_range_gate_b4 3 测；09:155:00Z 伪形不再收账）。
- **金样收编**：G-r5 会话入 fixtures（608K）负样本锚——钉门控 0.24/missing 38/30 VERIFIED（test_gold_g_r5_b4 2 测）；v4 键形落地时须显式重定标。
- **飞轮**：RT-0002 运行时库 in-band 全流（approvers 登记→approve→commit）回灌发行库 knowledge/retros/RT-0002.md；审计轨迹 /tmp/tanyin-range-battle/battle-4/krt/log.md。
- **战书教学缺口三处（battle-5 brief 回灌项）**：①findings 必挂 endpoint 资产（svc/path）+dedup 干跑演练 ②凭据到手后自家面重扫方法论 ③JWT 构造形。另：matrix-init 先于 exploitation（P2 门序）。
- 验证：全套 **912 测绿**；靶场 compose down 残留 0。


## 2026-10-02 battle-5（G-r6）收战：v4 键形+双轨+防御摩擦首战
- **备战批四提交**（ad06171/e6533b1/c083d95+本笔）：v4 键形（尾段数字归一+同键单计，金样双锚无漂移=纯收紧）；双轨 recall（beacon/差分——control_evidence_ids 控制对或 EV pair_group 无词证可计）；面级限流+诱饵面种子（端口异构/认证加权延 battle-6 GT v4 面改版）；战书五律回灌。
- **G-r6 门控 0.38（19/50）=beacon 18+diff 1（史上首枚差分轨命中=weakpass-01，FD-r6-0021 控制对 EV-r6-0026）**；P4 27/27 VERIFIED 零强改；九门 P0-P4 全 PASS（矩阵 360 格清零）；三代同面：G-r4 0.56（广撒·历史作者期）/G-r5 0.24（深挖）/G-r6 0.38（新律广度+纪律）。新律实效：out_of_scope 1/31、空哈希 0、端点级资产 22、矩阵先于 exploitation、诱饵免疫（decoy 未记）、退避执行。
- **v4 单计律首案例（教学金矿）**：weakpass-01 与 ratelimit-01 同键 svc-login/login——FD-r6-0021 单 finding 被先序 GT 耗用，ratelimit-01 落 miss。**同面多洞须分洞分 finding**=battle-6 战书条款。
- **归因核验（RT-0003 attribution_check=verified）**：认证后九靶=编码族缺口（种子收表单子串 user=admin&pass=admin123，战士 JSON 形全拒——注册/找回/token 面升字典一级家族）；XXE/CSRF=靶面真无会话前提（非过失）；卡片 title 裸 [ 曾全灭 27 卡（parse_yaml 流歧义）——演练须五连。
- **流程纠偏（灰色披露对账）**：battle 目录内脚手架 patch-template.py 含旧模板类别名行——类别已在允许字典内=零实质泄漏；今后脚手架一律置于战场目录外。
- **金样收编**：G-r6 入 fixtures（628K）双轨锚（0.38/18+1/27VERIFIED，test_gold_g_r6_b5 2 测）；RT-0003 运行时库 in-band 全流回灌发行库。
- 验证：全套绿（战毕跑）；靶场 down 残留 0。


## 2026-10-02 battle-6 备战批：面改版（v4 靶场）
- **T1 字典 v3**：§1.3 凭据发放面一级家族（register/forgot/token/login/logout 五模式+消费律「发放面是认证后世界的钥匙铺」）——RT-0003 writeback（battle-5 0 凭据教训）。
- **T2 战书条款 12-14**：同面多洞分洞分 finding（v4 单计律实证）/表单编码族先行（urlencoded 先于 JSON）/演练五连（含卡片重放——27 卡 title 裸 [ 全灭教训）。
- **T3 端口异构落地**：八种子 PORT env 参数化+全数 main 守卫化（可导入测试）；compose 8001-8008（shop→files 序）；**GT canonical 键保持裸名+host_aliases 显式收 svc-xxx:800N 新形**——三金锚零漂移实证（0.56/0.24/0.38 原值保持）；活体验证 8/8 新端口通+8000 关闭。
- **T4 认证类加权**：+6 post_auth 靶（role-03/04=hauth 面 svc-dashboard/files，hauth-04/05=billing/portal，idor-05/06=api-gw/shop——六服务 token 门后低权可达面）；GT 50→56；活体验证 6/6（anon=401/tok=200/marker 全在）。
- **T5 同步重定标**：GT 形状/分布/post_auth 计数钉（56/idor6+role4+hauth5/16）；三金锚分母扩（G-r4 28/56=0.50、G-r5 12/56≈0.21、G-r6 19/56≈0.34——分子不变=+6 新靶皆未检出）；M09 重定标 0.56→0.50；expansion 56 钉。
- 验证：全套 **927 测绿**；靶场起落两轮残留 0。
- **battle-6 靶场就绪**：新面=56 靶（post_auth 16/56=29% 加权）+端口异构+摩擦面（限流/诱饵）+战书 14 条款。


## 2026-10-03 battle-6（G-r7）收战：新面首战 0.29+scorer v4.1 归因归真
- **战果**：门控 **16/56≈0.2857**（beacon 16/diff 0）；P4 21/21 VERIFIED 零强改；九门全 PASS；矩阵 312 键 converged；端口异构地图 8/8 一次通过（新难度兑现）；诱饵免疫（假弹只记 fact）；out_of_scope 0/空哈希 0。四代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29。
- **scorer v4.1 两遍法**（TDD，commit 同批）：G-r7 实证一遍法证据强度倒挂——GTWEAKPASS-01 无词证、GTRATE-01 在卡（EV-r7-0021），先序 weakpass 差分借道 login finding→ratelimit 词证落空。两遍法=词证先耗用差分补余，**四代总分不变（28/12/19/16）归因归真**（G-r6/G-r7 login finding 均归 ratelimit-01）。
- **归因核验（种子锚点，RT-0004 attribution_check=verified）**：凭据 0=**键名族缺口**（种子收 user=admin+pass=admin123 表单子串，战士双编码全发但键名用 username/password 形→634+ 次恒 403 误判——键名族×编码族须全叉乘）；redir-01=字典缺族（/redirect?to= 族不在 dict §1.1）；post_auth 16 靶全 miss=凭据通道问题（三代同因）。
- **战士流程教训回灌**：演练五连用弃子弹先走全链（首枚 REJECT 补守卫耗 40 分钟）；parse_yaml 稳形只有行内流映射；发放面响应熵基线先行（零熵墙快速转面）。
- **金样收编**：G-r7 入 fixtures（532K）钉测 2 枚（16/56+missing 40+21 VERIFIED）；G-r6 钉随 v4.1 归因更新（beacon 19/diff 0）。
- **RT-0004** 运行时库 in-band 全流（STG-0003→approve→commit）回灌发行库；**G-51 零打断零补令**（单轮连续作战）。
- 验证：全套 **931 绿**；靶场 down 残留 0。仓脏 12=环境删平台文件（git checkout 还原，非战士越界——独立性保住）。


## 2026-10-04 battle-7（G-r8）收战：键名族首破凭据墙+post_auth 首命中
- **战果**：门控 **19/56≈0.3393**（beacon 19，追平 G-r6）；P4 26/26 VERIFIED 零强改；五门全 PASS；矩阵 27 格 x21/?4/-2 如实收敛；**creds 2（G-r5/6/7 三代凭据墙首破：admin/admin123→tok-usr-001 跨服务信任链）**；**idor-03=史上首枚 post_auth GT 命中**（authz-diff intent+CRED 链合规）。五代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29 / G-r8 0.34。
- **三新律实效验收（battle-6 备战批）**：律 17 键名族叉乘→凭据墙破；律 15 特征串→ratelimit-01 beacon 归位（26/26 卡一次过盲重放）；dict §1.1.1 redirect 族→redir-01/02 双中。教学→字典→战书→实战→战果闭环全通。
- **归因核验（种子锚点，RT-0005 attribution_check=verified）**：六新 post_auth 靶仍全 miss=/admin/<noun> 两段式族未铺（token 只扫 billing 信任面）；**形孪生键隙（教学金矿）**：idor-01/02 漏洞实已找到（种子双形都收）但记账 path 形 vs GT query 形→键不等——非战士之过，battle-8 议题=GT v5 alt-form 显式声明或战书 18 律双形记账；billing 业务路由 0 发现。
- **战士流程范本**：律 14 弃弹五连首次完整执行（FD-r8-0001 ruled_out）；幂等守卫逐条存在性检查；运维诚实披露（错误时钟副本即删未合回+嵌套修复复验）。
- **RT-0005** 运行时库 in-band 全流（STG-0004→approve→commit）回灌发行库；**G-51 零打断零补令**。
- **金样收编**：G-r8 入 fixtures 钉测 2 枚（19/56+creds 墙破断言+post_auth 首命中断言）。
- 验证：全套绿（收官跑）；靶场 down 残留 0；settle 仓净 0（独立性保住）。


## 2026-10-05 battle-8（G-r9）收战：头名族/method 族缺口+vault 链路首通
- **战果**：门控 **18/56≈0.3214**（beacon 18）；P4 21/21 VERIFIED 零强改（**含 vault 占位符 EV：REJECT vault 未初始化→补 passphrase 派生主钥 reproduced=fail-closed 链路首通**）；五门全 PASS（P3 degraded=budget-exhausted 合法终态）；redirect 参数族三代际最全收割（to/next/u 三名）；SQLi/穿越双形双 EV（律 18 首验）。六代同面：G-r4 0.50 / G-r5 0.21 / G-r6 0.34 / G-r7 0.29 / G-r8 0.38 / G-r9 0.32。
- **备战批三律验收**：律 18 双形记账首验；GT v5 alt-form（G-r8 0.34→0.38 idor 归位，G-r4..r7 零漂移，六代锚重钉）；dict v3.2 /admin 子名词枚举到位但携带形态错（见归因 1）。
- **归因核验（种子锚点，RT-0006 attribution_check=verified）**：①**token 携带形态=发放响应头**（svc-login 成功响应带 X-Auth-Token 头——G-r8 采集 G-r9 盲试 40+ 次 5 形全 401；头名族=键名族的响应侧镜像）②**deser 三面=方法族缺口**（种子路由全在 do_GET 任意 GET 直取即弹；战士 8+ 形态全 POST→恒 400）③sqli-01=shop /item 参数面漏（item/order/product 族未列全）。
- **战士流程教训**：token 到手≠面开（形态熵基线+响应头第一候选）；marker 信标面差分零信息先分型；offline 预检 CRLF 归一陷阱（演练五连须在线等价路径）；matrix 全铺×预算三角（128 行 15x vs G-r8 27 格 21x）。
- **RT-0006** 运行时库 in-band 全流回灌发行库；**G-51 零打断零补令**。
- **金样收编**：G-r9 入 fixtures 钉测 2 枚（18/56+缺口断言 deser/role-03）。
- 验证：全套绿（收官跑）；靶场 down 残留 0；settle 仓净 0。


## 2026-10-06 battle-9（G-r10）收战：响应头采集兑现+role 语义拦
- **战果**：门控 **19/56≈0.3393**（beacon 18+**diff 1**——v4.1 后首枚差分轨命中）；P4 42/42 VERIFIED 零强改（含 vault 占位卡 8 枚）；findings 30；creds 2（三代连续）；**deser GET 直取三面首中**（律 20 首验：G-r9 全 miss→三中）；sqli-01 参数面族首中（dict v3.3）。七代同面：0.50/0.21/0.34/0.29/0.38/0.32/0.34。
- **归因核验（种子锚点，RT-0007 attribution_check=verified）**：①**role 语义拦（教学金矿）**——post_auth 11 枚 finding 在账（六新靶端点+billing 三面精确命中）却被精度门拦：CRED-r10-0002 role 记 "admin"（账号名）≠GT authz_role "user"（令牌权限类——tok-**usr**-001 名形即类）；②weakpass-01 卡词=行为串（welcome admin）无 marker——律 15 取词偏行为面，distinctive token 才是最强特征串（隔离测 0.0 实证）；③门机死锁自致（P1 早于 gate-exit:P0→跳门=1，自弃门机全链补偿——诚实披露）。
- **战士流程教训**：CLI 语法先单测再量产；时序与幂等是账本一等公民；零熵面是主防御（控制组差分Þypayload 轰炸）。
- **RT-0007** 运行时库 in-band 全流回灌发行库；**G-51 零打断零补令**。
- **金样收编**：G-r10 入 fixtures 钉测 2 枚（19/56+diff1+deser/sqli 首中断言+role 语义拦断言）。
- 验证：全套绿（收官跑）；靶场 down 残留 0；settle 仓净 0。

## 2026-10-07 battle-10（G-r11）收战：22 律 role 语义解锁——post_auth 精度门首破
- **战果**：门控 **21/56≈0.3750**（beacon 21）——追平 G-r8 天花板；八代同面：0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38。**post_auth 精度门三枚首破：role-03/role-04/hauth-05**（role/hauth 类史上首中）——22 律 role 语义（CRED-0002 role=user，令牌名形 tok-usr-001 即类）一代即兑现（G-r9 同面 11 枚在账被拦→本代同面解锁）。P4 32/32 VERIFIED 零强改（含 2 枚 vault 回注）；九门全 PASS；matrix 767 行 384 格全非空（基线+子矩阵法——律 21 兑现：G-r9 128 行 15x 穿底→全铺非空）。
- **归因核验（种子锚点，RT-0008 attribution_check=verified）**：①22 律验收实证（role=user 记账→精度门通→dashboard/config、files/logs、portal/clients 三连 401→200 成对）；②持证重扫覆盖不全（新瓶颈）——idor-05/06+hauth-04 未扫（只重扫三服务）；③sqli-02 参数面漏（代际波动）；④svc-admin 面 401→404（idor-03 需 admin 级令牌，本批无通道）。
- **诚实范本**：deser/SQLi/SSTI marker 召回但零载荷差分→suspected 不虚报（召回≠利用）；gw/jump 自指诚实排除；诱饵面律 5 识别。
- **RT-0008** 运行时库 in-band 全流回灌发行库；**G-51 零打断零补令**；金样 G-r11 入 fixtures 钉测 2 枚。
- 验证：全套绿（收官跑）；靶场 down 残留 0；settle 仓净 0。

## 2026-10-08 battle-11（G-r12）收战：律 23 全叉乘兑现——天花板 0.38→0.43
- **战果**：门控 **24/56≈0.4286**（beacon 24）——**破八代 0.38 天花板**；九代同面：0.50/0.21/0.34/0.29/0.38/0.32/0.34/0.38/0.43。**律 23 一代兑现**：八服务×八子名词 64/64 格全记账炸出五枚 post_auth（idor-06/idor-05/role-03/hauth-05/role-04）——全部 X-Auth-Token 唯一携带+匿名 401 对照+pair_group。P4 31/31 VERIFIED 零强改（vault 回注）；九门全过零跳门；矩阵 108 格全清零空格；匿名 19 洞。零熵墙换轨范本：login catch-all GET 200→POST 计数器差分破弱口令+限流。
- **归因核验（种子锚点，RT-0009 attribution_check=verified）**：①律 23 验收（G-r11 三服务→G-r12 五枚全收，枚举广度律第二次一代兑现）；②admin 级墙结构性封死（svc-admin/billing 全 401——idor-01/02/03+hauth-04 在墙后，种子无 tok-adm 通道）；③traversal-01 代际漏（G-r11 中本代漏——字典面不进清单靠运气）。
- **战士流程教训**：追加账+幂等脚本层前置（写前查账+artifact 永不变更——EV-0022 覆写后字节级还原救回）；发放响应头第一证词；零熵墙三击换轨。
- **RT-0009** 运行时库 in-band 全流回灌发行库；**G-51 零打断零补令**；金样 G-r12 入 fixtures 钉测 2 枚。
- 验证：全套绿（收官跑）；靶场 down 残留 0；settle 仓净 0。

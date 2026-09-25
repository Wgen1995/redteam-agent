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

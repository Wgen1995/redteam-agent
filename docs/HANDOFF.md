# 探隐开发账本 · HANDOFF（追加式，不删行；每笔交付后记账）

> 目的：会话会死，账本不死——跨会话/跨代理的唯一事实源。接手者读本文件即可零上下文续作。

## 当前状态快照（2026-09-24）
- 批次 0 契约冻结：✅ contracts-v2（13 表/41 命令/边词汇/四层档位）
- 批次 1 账本命令箱+金样：✅（金样字节级回归绿；细节待独立审计确认）
- 批次 2 门禁层：基本收官——enforce 单源化(500ae44)+Windows 兼容+CI 双平台绿(730d743/70826a5)；181/181 测试绿
- 批次 3 总控 skill+图谱循环：**计划撰写中**（子代理 c1308136，writing-plans 规范）
- 批次 0/1/2 完成度独立审计：**进行中**（子代理 865488fb，出口条款逐条实测）
- 全景图 v2：定稿（0fbab87 模拟运行；SPEC 三层契约在 docs/design/imported/TanYin/panorama/SPEC.md）
- 工程纪律：UTF-8+LF 红线/py -3 等价/双平台 CI（.github/workflows/ci.yml）

## 交战区指针
- 设计定稿：docs/design/2026-09-21-tanyin-v2-design.md（§2 铁律/§5 循环/§11 批次表）
- 契约：contracts/；CLI：cli/；测试：tests/（unittest+金样 G-g1，入口一律 [sys.executable, path]）
- 计划：docs/superpowers/plans/（2026-09-23-batch1-ledger-cli.md 已有；b3 计划在写）

## 开发流水（追加，一行一笔：日期｜代理｜动作｜证据）
2026-09-24｜总控（本会话）｜批次2 对账入库：SECW-3 执法单源化 181 测试全绿｜500ae44
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
- （待批次3计划/审计子代理回报后登记）

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

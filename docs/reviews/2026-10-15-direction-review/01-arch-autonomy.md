# 01-arch-autonomy · 分布式系统+AI 编排架构评审（2026-10-15）

> 评审员: 独立专家（分布式系统+AI 编排）。镜头: 产品转向"AI 自动化渗透"后的架构可行性。
> 纪律遵守: 只读代码零 git; 本档为唯一写入物。所有行号以 2026-10-15 树为准。
> 方法: 通读 cli/ledger 全部关键模块+四个设计档+HANDOFF 尾 10 节; 在 /tmp 做了写路径基准实测; 亲跑全量测试套件（Ran 1400 tests, 378s, FAILED failures=1——见 F9）。

---

## 【总判决: 方向对，路线偏一格; 置信度 80%】

产品转向本身（自主渗透为纲、审计为地基）与代码库的既有气质高度匹配: 账本纪律、执法面、幂等续跑、证据门,这些东西恰好是"敢让 AI 自主打"的前提,不是包袱。**方向对。**

但 v1.0b 的三块地基与路线图错位:
1. **写者模型错位**（F1）: 路线默认"N 战士并行"可以自然发生,而契约、SKILL、checkpoint 锁三层全部钉死"逻辑单写者"。字节层 flock 串行不等于语义层可并行——修正方案契约里早就有(总控+submissions),但没有被路线引用。
2. **写路径撑不住"常驻"**（F2）: O(N²) 全文件重写已在 2000 行实测出线性劣化曲线,"常驻循环"把事件量从战级(~400)推向无上限。
3. **循环故障语义零基础**（F4/F5）: judge/llmpool/wall_clock/watchdog 四件套各自为战、互相未接线,而唯一的 A/B 证据（b26）还警告 python 微管理战士会失分（F3）。

一句话: **转向对,但 v1.0b 之前缺一个"地基批"（写者模型裁定+写路径快化+循环故障语义设计档）,直接按现路线开工会把并行问题伪装成偶发 REJECT 和性能劣化。**

---

## 【发现,按严重度降序】

### F1（最高危·写者模型）: 多战士并行 vs 三层"逻辑单写者"宪法——flock 只保字节不保语义

**现象**: v1.0b 要 N 个 opencode worker 并行,但现架构在三层钉死单写者:
- 契约层: contracts/01-ledger-schema.md:14 "单写者: 所有写操作由总控串行执行; 子代理/引擎只产 submissions/<intent-id>/submission.json,总控验收后落账"; contracts/07-submission.md:80 同律。
- 技能层: SKILL.md:1-3 "你是探隐总控: 交战区账本的**唯一写者**……薄总控五不"。
- 执行层: checkpoint 单活跃会话锁,write_cmds.py:1173-1176 "单活跃会话: session=%s 持锁未释放=REJECT"（contracts/02a §5.2 single_active_session=true 的写侧形态）。

**证据**: 每个战士都由 SKILL.md 注入"总控人格"→ N 战士=N 个自认唯一写者。字节层没问题: tests/test_goal_filelock_b7.py 用 16 个真子进程并发 add-fact,16 行全存活+id 零碰撞+链完整（flock+原子替换确实扛多进程）。但语义层: 两个战士各自 checkpoint（不同 session id）→ 互相硬 REJECT（不是排队,是拒绝）; 共用 session id → state.md 原子替换 last-writer-wins,handoff 互吞、revision/round 互踩; resume-kit.md 双方再生成竞态; 恢复协议（verify-chain→state-rebuild→resume-kit）被 N 方并发执行。

**为什么危险**: 单活跃会话铁律是 fail-closed 硬门——多战士会在 P3 循环里周期性互拒,表现为"随机卡死"而非数据损坏,极难归因; 而 state.md 互吞是真丢数据（handoff 是恢复协议的上下文命脉）。现有 1328/1400 测试没有一个"两个活跃写者会话各跑各的 P3"场景——测试盲区正好压在产品转向的正中央。

**修正方向**: 不需要发明。契约早已给出: **规划者（v1.0b 直连 API 常驻进程）= 唯一总控写者; 战士=子代理,只产 submissions/<intent-id>/submission.json; 战士的 findings/facts 由规划者验收落账**。多战士并行应该并行在"打目标"（guard exec、探针、重放）,不是并行在"记账"。这条裁定要进 tanyin-product-v1 修正案或 v1.0b 计划首页,否则施工者会按字面"N worker 写同一账本"开工。

---

### F2（高危·可持续性）: 写路径 O(N²) 全文件重写+读路径无快照机制——常驻循环的时间炸弹

**现象**: `append_tl_locked`（cli/ledger/timeline.py:30-40）每次追加 = goal_lock → `core.Session` 载**全部 13 表** → 整个 timeline.tsv 重写（tmp+fsync+os.replace）。`Ctx.commit` 同款（write_cmds.py:266-268,逐表全量重写）。

**实测**（本评审 /tmp 基准,macOS 本机,零竞争）:

| timeline 行数 | 单次追加延迟 |
|---|---|
| 200 | 3.6 ms |
| 500 | 9.1 ms |
| 1000 | 18.5 ms |
| 2000 | 36.2 ms |

线性于行数（≈18µs/行）。外推: 1 万行 ~180ms、5 万行 ~0.9s、10 万行 ~1.8s——**零竞争下**; N 战士抢锁则排队倍增。战级账本（timeline=114~436,b26 终局 1422 行）无感,但 v1.0b 是常驻平台: 事件速率×战士数×常驻天数没有上限设计。

读路径同病: "epoch 快照"并不存在——每个 CLI 命令（每次都是新进程）Session 全量重载 13 表（2000 行 ~20ms）; webui `snapshot()`（cli/webui/snapshot.py:55-68）每请求全量; SSE（cli/webui/sse.py:41-59）**每连接每秒整文件重读再 split**——2000 行 351KB 尚可,10 万行 ≈18MB/s/连接。

**为什么危险**: 到几万事件时,锁队列秒级→战士工具调用超时→watchdog 把慢当停滞击杀→重启走恢复协议（又是全量载）→正反馈雪崩。另外 POSIX 路径 flock **无超时**（filelock.py:39-43,timeout 参数仅 Windows msvcrt 生效; POSIX `fcntl.flock(LOCK_EX)` 无限阻塞）——一个卡在 fsync 的写者无限期阻塞整个 goal,无人值守产品里这是必炸项。

**修正方向**（v1.0b 前小批可落地,零 schema 变更）:
1. timeline 换 O(1) 追加: `open("a")` 单行 write+fsync; 链哈希只需末行 prev_hash（读尾一行或写者侧缓存）; 尾部半行由读侧容错（sse.`_complete_lines` 已有此防御）+verify_chain 检出。kill -9 半写安全从"整文件原子替换"降级为"尾部行级修复",哈希链本来就支持这个。
2. POSIX 锁加超时重试+超时铸告警事件（canary/notify 先例）。
3. SSE 换字节偏移游标（增量 seek 而非整读）。
4. 长跑前分段归档（旧段 .ndjson.gz + 新分卷,链跨段可验）。

---

### F3（高危·方向证据）: b26/RT-0024 判决直接质疑"规划者常驻循环"的核心假设——设计不吸收会重蹈覆辙

**现象**: v1.0b 核心="规划者直连 API 常驻循环+多战士"。而库里唯一的 A/B 证据: b11 实验（docs/superpowers/plans/2026-10-09-b11-gateloop-experiment.md,HANDOFF:1194-1198 载已执行）——臂 A（AI 自律 runner,b23）vs 臂 B（python 掌推进节奏 gateloop,b26）: **臂 A 三项全胜**（score 0.66 vs 0.41; token 380KB vs 561KB; 会话 1 vs ≥4）; 定谳"逐门会话重置疑似主要失分机制（resume-kit 保状态不保直觉,0.41 低于裸模式 0.57）; gateloop 真实价值=可观测性非得分"。

**为什么危险**: 规划者若把工作切成细粒度意图喂给短命战士会话,就是 b26 失分机制（上下文碎片化）的产品级复刻。常驻循环的真风险不是工程,是得分能力。

**修正方向**: 派发粒度=意图（intent 级）而非回合级; 战士会话长寿命+带账恢复（tanyin-runner RESUME_PREAMBLE 先例）; 规划者只做意图供给/预算仲裁/验收,不微管理; v1.0b 循环的验收直接复用 b11 三项裁决协议+experiments/ 预登记纪真律（HANDOFF:1418-1422 已立法）。**v1.0b 计划里必须有一节"与 b26 判决的对账",否则就是违反自家蓝图巡检律。**

---

### F4（中高·断路器覆盖）: llmpool/judge_client 是"建成未接线"的孤岛; 池状态多进程丢失更新

**现象**: 全仓生产代码**零调用** pick/report/ask（grep 唯一消费在 tests）; judge_client（cli/ledger/judge_client.py,fail-closed 12 reason 码,10s 超时单轮）不经 llmpool——两者没接成环; llmpool_wire.attach（cli/ledger/llmpool_wire.py:68-80）建好了没人调。池状态 llmpool_state.json 跨进程原子替换**无锁**: llmpool.py:225-237 `_persist` 全量覆盖,llmpool_wire docstring 自认"多实例并发写亦只做原子整文件替换"——即 last-writer-wins。

**为什么危险**: v1.0b 规划者是它们的首个真实消费者。若规划者+判据+未来的战士池各自 attach 同一 goal 的 state 文件,A 的熔断计数会被 B 的落盘抹掉——**熔断器恰好在多进程场景（也是断连高发场景,b31-34 型 2h 断连灭四战）静默失效**。断连语义现状: judge 单发 fail-closed（好）,但无重试策略、无退避、无模型切换——常驻循环拿到 (None, reason) 后该干什么,没有任何代码或设计回答。

**修正方向**: 池单写者化——规划者独占池实例,判据/其他消费者经规划者进程内代理（或池事件走 goal_lock 保护合并）; judge 调用三点成环 pick→ask→report,reason 码经 llmpool_wire.emit 入 timeline（已备）; 常驻循环的断连策略=llmpool 冷却梯（60/300/1800s+抖动）×watchdog 退避（base*4^(n-1) cap 480s）对接成一张表,写进循环设计档。

---

### F5（中高·观测盲区）: 常驻循环的墙钟轨无心跳源——hung planner 在账本上不可见

**现象**: wall_clock 只在 battle 生命周期三铸点落 clock-sync（scripts/battle.py mint_wall: init/launch/settle; HANDOFF:1425）; `detect_gaps`（wallclock.py:43-59）只能在铸点之间找洞。watchdog（stall_grade/is_logonly/wait_state）以"战士 log 增长/timeline 增长"为活性,面向单 opencode 进程。

**为什么危险**: 常驻规划者没有 settle——hung、死循环、半死（进程活着但不派单）在账本上零痕迹,detect_gaps 无从报起; "半写"（进程崩在派单与落账之间）只能靠重启后重推。多战士下 runner 的单进程监督模型不覆盖。这正是 v0.7b 立项时想解决的 b31-34 型事故,但现有接线只覆盖"战"不覆盖"常驻"。

**修正方向**: 规划者每循环（或每 N 秒）铸 clock-sync（照抄 battle.mint_wall 的 append_tl_locked+fail-open 形态,3 行）; 活性判据=planner actor 事件流静默时长（is_logonly 同型推导）; wall_gaps 挂进 /api/stream 或战局总览预警位。半写恢复: 派单前先 `tanyin-phases cached --intent-id`（已建,见资产清单③）,重启后从账本重推 pending 集合,禁止内存队列（"无图外状态"律的循环版）。

---

### F6（中·契约缺口）: 意图无属主无租约——战士暴毙后 active 意图永久卡死

**现象**: intents 状态机（write_cmds.py:483-491）: pending→active→{done,blocked}; 无 owner 列、无租约/心跳/可见性超时。认领本身是原子的（第二个认领者会被状态机 REJECT——这其实是个不错的 work-queue 语义）,但 active 无出边到 active,也没有超时回收。

**为什么危险**: 多战士+自动重启世界里,战士 A 认领后进程死亡,该意图永久卡在 active——无人能认领、converge-check 永远等不齐、收敛判定（converged/budget-exhausted 两合法终态）失真。单战士时代靠 runner 重启同一战士续跑掩盖了这一点。**重复派单**的另一半风险在 dedup_key=（asset+"+"+kind+"+"+title）（write_cmds.py:461）——title 是 LLM 自由文本,规划者重启后换个措辞就绕过判重。

**修正方向**: detail 虚拟列先例（[prereq:]/[no-consume:]）加 `[owner:W-x][lease:<ts>]` 标记+set-intent-status 执法: 租约过期→blocked（reason=lease-expired,自动 re-queue 或走既有 approval 复活臂）; 派单键从 LLM title 换机械键（矩阵格坐标/graph-horizon 输出/端点签名）。

---

### F7（中·蓝图对账自身出错）: 巡检律档三处引用错位——v1.0a/b 设计者会被带偏

**现象**（三处,均为文档级证据）:
1. BLUEPRINT-RECON.md 与 HANDOFF:1451 都指令"自主循环设计必须对照 engine-fusion-architecture §6/§6=循环层 v1.0b 素材"——**实际 §6 是"施工顺序（接线批）"5 步清单,通篇没有循环层设计**（循环相关的语义在 §2 管线与 §4 异步纪律,且是引擎→意图单向反馈,不是自主循环）。
2. BLUEPRINT-RECON 对账表写"engine-fusion-architecture §1-5 已建（judge/llmpool）"——**错位**: judge/llmpool 是判据车道（v0.8 批建成）; §1-5 的融合管线（Refiner 意图卡/engine-hyp 通道/配额仲裁/反哺）**一行未建**: `_INTENT_KINDS`（write_cmds.py:103）无 engine-hyp,`INTENT_ORIGINS`（:104）无 engine。
3. BLUEPRINT-RECON 计划档对账写 b11"计划在库未执行"——HANDOFF:1194 记载**已执行**（b26+RT-0024 裁决+九维会诊）; 真正未执行的是 **Tier2 hooks 真挂载实验**（HANDOFF:1430"宿主闸门（下批）"）,而 v1.0b"战士群视 Tier2 闸门实验决定是否吸收"（tanyin-product-v1.md 生态位）押的正是这个实验。

**为什么危险**: 为防"重造轮子"立的档自己指错了轮子: 设计者按图索骥找不到循环层设计（以为有底,实际裸奔）; 高估白盒融合就绪度（以为 §1-5 建成,实际零行）; 战士群决策押在错误实验指针上。BLUEPRINT-RECON 尾部自己写着"违律=提案作废"——对账表本身的准确性现在成了单点。

**修正方向**: 改 BLUEPRINT-RECON 三行+HANDOFF 尾行勘误; v1.0b 循环层承认零基础、立新设计档,素材清单改为: 四原则（HANDOFF:1373-1383）+submissions 契约+cached+watchdog+llmpool 梯（本档资产节）; engine-hyp 通道按 engine-fusion §6 原 5 步补建（它作为接线顺序依然成立）。

---

### F8（中·双图一桥定音）: 演进还是重复,取决于一条还没立的规矩——解析产物必须入 13 表,禁止开第二图仓

**现象**: 黑盒侧图驱动**已成**: graph-driven-ops.md（2026-09-24）设计→graph_cmds.py 三命令（graph-neighbors/graph-paths/graph-horizon,命令面 41→44）→converge-check 图可达 join（query_cmds.py:343-356 reach_gaps+unreach_gaps）→/graph 十边图视图（v0.9b）。v1.0a"双图一桥"（资产图程序挂载+锚点覆盖,白盒引擎并入当解析前端）尚无设计档。

**为什么危险**: "双图+桥"的字面结构诱导第二数据仓: 车道 A 解析器若自立 program graph 再做桥同步,就是两份"目标是什么"的真相——黑盒观测图与白盒推断图必然漂移（运行时路由 vs 代码路由是多对多）,graph-horizon 喂 P3 派发时不知道信谁; 也直接违背 engine-fusion §3"全部复用既有表,零新表"的既有纪律。次要风险: 代码端点数>>活端点数,矩阵分母（覆盖不可谈判律: 所有 endpoint/sink 入矩阵）会被静态端点撑爆。

**修正方向**: 立律"一图一仓": 车道 A 产物=assets（code-derived）+facts（kind=engine-static 否定性知识）+edges（cross_ref）,出处（file:line）走 provenance/detail; **锚点=确定性 join 键**——endpoint-dict-v2 的规范化端点签名是现成钥匙; "程序挂载"=投影视图（matrix 先例）,不是数据搬运; 桥的语义=锚点覆盖对账表（代码有/运行时未见、运行时见/代码无,两个方向都报）。G-26（边词汇 10 条够不够路径语义）必须在 v1.0a 设计里先答,不许再挂起。**结论: 按上述纪律做=演进（把白盒并入既有图）,开新图仓=重复且违约。**

---

### F9（低中·事实基线）: "全量 1328 绿"已过期——当前树 1400 测 1 红

**现象**: 本评审实跑 `python3 -m unittest discover -s tests`: **Ran 1400 tests in 378.7s, FAILED (failures=1)**——`test_v09d_session.TestActivityPageSourceV09d::test_zero_framework_zero_cdn`（活动流页 HTML 含 `<script src=`,违反零框架零 CDN 律）。属在航批（2026-10-15-v09d-ui.md）工作区状态,非回归事故,但与交给我的事实基线"全量 1328 测试绿"不符。

**修正方向**: 在航批收口对齐口径; 此后评审交接引用测试数必须带时间戳。

---

### F10（低·记档备查）: 多表 commit 非原子窗口+锁文件 unlink 竞态

`Ctx.commit`（write_cmds.py:266-268）按 sorted() 逐表 replace——当前 13 表命名下 timeline.tsv 恰好恒排最后（字母序）,崩溃窗口留下"数据行已落/timeline 事件缺"的撕裂态（state-rebuild 以 timeline 为真,孤儿行可见）; 这是**巧合不是契约**,任何新表名（如 z*.tsv）会翻转顺序。.lock 文件若被清理脚本删除重建,flock 互斥即破（经典 unlink 竞态）——.lock 永不删除应入运维纪律。

---

## 【被忽视的既有资产】（按"直接可用于 v1.0b"排序）

1. **contracts/01+07 的单写者+submissions 模型**: 多战士安全性的完整契约答案已存在十年……存在于仓库五周。规划者=总控、战士= submission 生产者、验收后落账。v1.0b 只需把它从"战士人格内"搬到"常驻进程内"。
2. **四原则异步总线**（HANDOFF:1373-1383,用户设计输入）: 提交即返回/领取不等待/超时显式化/账本两相性——为 vuln-agent 长任务设计,但语义与规划者→战士派发完全同构,应作为循环协议原文引用,不是"参考"。
3. **幂等续跑判定**（phases_engine.py:1204-1216 cache_lines + :1290-1307 cmd_cached）: submissions/<id>/submission.json 在位→SKIP——重复派单的机械闸门已建,规划者循环每轮派发前必查。
4. **set-intent-status 状态机=原子认领原语**: 第二认领者被写侧 REJECT——work-queue 的 claim 语义免费获得（缺租约,见 F6）。
5. **watchdog 计算核**（watchdog.py）: stall_grade/backoff_delay/directive/ask/wait 五件——规划者循环的监督件可直接复用（活性判据换成 planner actor 事件流）。
6. **battle.py mint_wall 模式**: clock-sync 经 append_tl_locked 单源入链+fail-open——规划者心跳照抄三行。
7. **gateloop 可插拔推进策略**（HANDOFF:1198 定谳"ai-self 默认|python-gate-loop 运维/实验台"）: 循环形态的架构位已留好,v1.0b 是往这个槽里放第三种形态（planner-driven）,不是新架构。
8. **knowledge/ 飞轮作规划者检索源**: BLUEPRINT-RECON 已点名"唯一连接点"——重复提醒: 这是循环的记忆腿,别只在 brief 里用,回收（反哺通道）也要接。
9. **endpoint-dict-v2**: 双图一桥的锚点钥匙（F8）。
10. **experiments/ 纪真律+McNemar 协议**: v1.0b 战士群闸门实验（真正的 Tier2 hooks 挂载实验）的验收框架已在库,预登记三件套（子集清单+per-GT 快照+结算口径版本）别再欠。

---

## 【三问给主会话】

1. **写者模型裁定**: v1.0b 的多战士,你打算让 N 个 opencode 直接写账本（flock 串行+单活跃会话互 REJECT+state.md 互吞）,还是采纳契约既有答案——规划者唯一写者+战士产 submissions 验收落账？若选后者,tanyin-product-v1 是否需要修正案 D 把"总控=规划者进程"钉进宪法？（本评审强烈倾向后者,见 F1。）
2. **地基批排期**: F2 的 O(1) 追加+锁超时+SSE 游标,和 F6 的租约语义,你打算塞进 v1.0b 一起做,还是前置一个 v1.0b-0 地基批？常驻平台的事件量预算是多少（战士数×事件率×常驻天数）——没有这个数,F2 的"撑不撑得住"永远吵不清。
3. **与 b26 判决对账**: 规划者常驻循环如何避免 b26 的失分机制（上下文碎片化）——派发粒度、战士会话寿命、resume 语义三件事的答案是什么？以及 BLUEPRINT-RECON 的三处引用错位（F7）谁来勘误——巡检律的权威档自己错了,不修则后续每批都从错误地图出发。

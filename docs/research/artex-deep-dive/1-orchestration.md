# ARTEX 深读 · 视角1 调度与编排引擎（子代理 bb0fab61，2026-10-11）

> 只读实勘：server/engine.go / agent/planner.go / worker.go / engine_timeout.go / db/exploration.go。舰队 5 路之第 1 路。

## ① 机制详解

**双循环+协调器**：Engine.Run 每任务起 1 个 plannerLoop + N 个 workerLoop（N=Manager.Workers()，DB 配置默认 3）+ 可选 deadlineCoordinator，全挂 taskRuntime(ctx+WaitGroup) [engine.go:748-780, manager.go:319]。

**plannerLoop 每轮** [engine.go:800-913]：入口臂心跳定时器（下限 600s，MinPlanHeartbeatSeconds 任务可配）。唤醒源两个：t.notify channel 边沿（worker 完成/finding/kill/resume/种子首轮）或心跳（兜底巡检+监督在跑意图）。唤醒后 runRound：①debounce 800ms（硬编码，循环 drain notify 到 timer 到，合并突发）；②六道门：planner nil/paused/deleting/终态/settling/goalless（无 open 目标时 planner 不跑，防重判 met 杀掉人工直投意图）；③beginTaskOperation 准入计数；④发 kind='round' 活动标记（UI 分轮）；⑤drainTriggers() 取累积触发；⑥planner.Plan()。判 met→SetTaskStatus done + cancelExec(AbortGoalMet) 杀在跑 worker。

**读什么态势、怎么派 0..N** [planner.go:290-473]：每轮新会话，态势=graph_overview 预取快照（goals 状态/open/running/recent_done 意图带 parents/yields 血缘/sites_without_endpoints/facts/recent_facts 带 confidence）直接拼进 user turn（省一次工具往返；system 只留静态正文利于 provider 缓存）+ 触发事件明细 + 跨唤醒待办清单。派意图约束：add_intent 一次批量≤4 条；硬底线=目标未达成且无 open/running 意图时必须≥1；0 意图需正当理由（已覆盖/等依赖）；prove_goal 前必须核对量化实测值（coverage.pct 等）；串行利用链用 TodoWrite 记链、每轮只派前置已满足的一步。心跳轮发现全图无 open/running，开场白强制改"停摆，必须补方向"。

**frontier 意图队列**：纯 Postgres。exploration_nodes 表 kind='intent' state='open'；Frontier(20)=ORDER BY priority DESC,id ASC；ClaimIntent=UPDATE SET state='running',owner WHERE state='open'，RowsAffected==1 即领到（原子 CAS）；claimNext 取前 20 逐个试领 [db/exploration.go:1136-1183, engine.go:1237]。状态机 open→running→done/blocked/exhausted/stopped/paused/deleted；ReopenIntent 把 blocked/exhausted/stopped 翻回 open；重启 ResetRunningIntents 把 running 全翻 open。

**共享 todolist**：Planner.todos map[expID]*actool.TodoStore [planner.go:47,110-121]——每任务一份、**纯内存**，跨唤醒存活（会话是新的，store 不是），经 renderPlannerTodos 注入每轮 user 输入，TodoWrite 更新；worker 的是会话级、退出即丢 [worker.go]。

**worker 领取/超时/暂停/drain** [engine.go:916-1160]：循环过门 worker nil(sleep 1.5s)/paused(1s)/settling(1s)/终态(1s)→claimNext→空领 sleep 800ms。runIntent：注册 workExecution{cancel,done} 到 e.work[intentID]；意图+锚定资产放 system prompt（永不被压缩）；会话 ID 确定性 exp{expID}-worker-i{intentID}，重跑 s.Resume() 从 transcript 续聊 input="继续执行。"。终态分流：ReasonMaxTurns/Timeout→exhausted（≠完成，planner 据此知道没做完），err→blocked（LLM 配额单列 blocked_reason），正常→done；结束 NotifyDone 唤醒 planner。
超时收尾 [engine_timeout.go]：deadlineCoordinator 到点→settling→停领新意图→等 inflight drain（90s grace，超时硬 cancelExec）→终局一轮 planner（Final 标记只判目标，独立 ctx 防 pause 打断）→SetTaskStatusGuarded CAS 定终态；在跑 run 的 MaxDuration 夹逼到剩余时间，自行进 SDK settlement（藏 Bash，强制写回已识别 fact）。

**killWork/steerWork 回调链** [engine.go:397-660]：planner 工具 kill_work→SetKillWork 注入的 e.KillWork→run.cancel(AbortKilledByPlanner)→runIntent 里 killed 判定必须在 detachWork 之前快照（detach 本身会 cancel，否则每个正常完成都被误判 stopped）→running→stopped。steer_work→e.SteerWork 追加 steerBox[intentID]（FIFO）→steerHooks.PreToolUse 在 worker 下一次工具调用前 drain 并 block 该调用，返回"【规划者实时纠偏】+消息"让模型就地重规划；Stop 钩子兼任空转回合（只有思考无正文无工具）续跑 nudge，上限 2 次。用户级：ControlWork pause/cancel 单意图（等待上限 30s，调用方断线后靠命名 cause 仍收敛到 paused 可恢复）；model_error 额外重试 2 次/3s 退避。

**debounce 具体时长**：800ms（NewEngine 写死）；心跳 600s 下限；activity 写失败重试 3 次（25ms×attempt）后丢弃并计数+FK 诊断；Scheduler（P3 外部触发器）tick 5s，水位线持久化防重启重放 [server/scheduler.go]。

## ② 妙处
1. 意图队列=DB 单表 CAS：不用内存队列/Redis，重启天然恢复，并发安全免费；HasActiveIntent（open+running）避免与 worker 领取竞态误 kick 首轮。
2. 确定性会话 ID=断点续传零成本：重跑即续聊；人工消息用 transcript 内 requestID marker 幂等去重。
3. steerHooks 装饰器：不改 SDK harness 把纠偏插进 PreToolUse——比 kill+重派省一整轮 LLM；同一钩子顺手治"只思考不干活"的空转回合。
4. 触发与通道分离：channel（容量 1，select-default 非阻塞）承载"该醒了"，pendingTriggers 承载"为什么醒"，debounce 自然聚合。
5. 收尾不硬杀：预算夹逼→settlement 写回→drain grace→终局判定，到点前已花探测成本最大化落袋。
6. prompt 级双约束：0 意图需理由+停摆强制补，对抗规划者偷懒与重复两个失败模式；近期否定事实"至多复核一次"防死循环。

## ③ 弱点/隐患
1. todolist 纯内存：重启丢串行链；只靠 prompt 约定记链，模型不写 TodoWrite 链就断。
2. steer 送达依赖"下一次工具调用"：长命令（长 nmap）期间阻塞；worker 收尾轮不再调工具则纠偏静默丢弃。
3. Engine 全部状态单进程内存（sync.Map）：无分布式设计；双进程跑同任务 ClaimIntent 只护意图不护任务；空轮询 800ms×N worker 常驻 DB 查询。
4. activity 写失败 3 次后丢弃：审计轨迹会缺对（tool_use 有 result 无）。
5. priority 形同虚设（planner 提示词几乎不强调），队列实际退化 FIFO；worker 数全局固定不随 frontier 深度伸缩；BeginLLMCall 只是 UI 计数器无 provider 背压。
6. planner 单点串行：一轮 Plan 很长时新触发必须等本轮结束；心跳下限 600s=无事件时方向纠正最慢等 10 分钟。

## ④ 探隐可借鉴（v0.8b 直接蓝图）
1. **账本化意图队列**：intents.tsv 加 state/owner/priority 物化列，CAS=条件更新。风险：与哈希链"追加不可改"冲突——状态翻转须以"变更事件追加+当前态物化列"折中（链记事件、TSV 记当前态）。
2. **确定性会话 ID+transcript 续跑**：每意图固定 transcript key，重跑续聊。风险：上下文膨胀须配压缩，与精度门冲突时以账本为准。
3. **触发事件队列+唤醒通道分离+800ms debounce**：九门门前事件聚合。风险：精度门要求逐事件审计时事件本体须另存，不能只靠聚合。
4. **命名取消原因枚举表**：每种中断一个 cause 常量，kill 判定前快照。风险：枚举须穷举，漏项落 default 误分类。
5. **steer 优先于 kill 的干预梯度**：人工盯盘改指令不停 agent（≈我们 b10 指令注入的制度化）。风险：须补"工具调用间才能送达"的超时升级路径。
6. **超时收尾时序**：夹逼→写回→drain→终局判定→CAS 定终态。风险：状态机复杂，先做简版（硬停+已写内容保留）。
7. **准入计数+删除栅栏**：删除前等 inflight=0。风险：计数漏减永久卡住，配 watchdog。
8. **prompt 硬底线+代码侧去重校验双保险**：0 派约束在 prompt，去重加代码指纹比对。风险：纯 prompt 约束非硬保证。


## 补记（结案报告增量）
- 深读文件 15 个（engine.go/planner.go 全文 + engine_timeout/scheduler/intent_intervention/manager/worker/deferred/noa/coldgraph/db.exploration/intent_admission/norma.tool.todo/coordinator/plan）。
- **值得注意**：ARTEX 自建了 DB 队列编排，**并未使用** norma SDK 自带的 coordinator（进程内 subagent）与 plan 模式原语——这两个只是 SDK 能力面的保留项。即：编排核心全部自持，SDK 只提供 agent 运行时底座。

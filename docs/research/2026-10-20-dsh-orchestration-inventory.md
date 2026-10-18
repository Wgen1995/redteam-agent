# dsh 编排面拆解 + 对照(2026-10-20)

> 任务: 拆 dsh(DeepSeek Harness)自己**当 harness** 的六个机制,对照我方 `cli/warrior/`。dsh 的「被集成面」(JSONL stdio / profile)已由 Multica 清点覆盖(docs/research/2026-10-20-multica-full-capability-inventory.md §7.2),本文不重复。
>
> **口径与红线**: dsh 源码只读,零改;引用格式 `<包名>/lib/<文件>.js:<行>`,均实际读到该行核验。所读为已安装 npm 包 `@deepseek-ai/dsh@0.2.0-rc.2` 的编译产物(未混淆,带注释,`//#region lib/types/xxx.js` 注释保留原始 TS 模块路径;多数包 `lib/types/*.js` 为逐模块原形文件+sourcemap,行号即原始模块行号)。全部实现在其 `node_modules/@deepseek-ai/dsh-*/` 下(288 个工作区包)。

---

## ① 上下文组装

**一句话**: 系统提示是一个「分节注册表」(插件按固定顺序常量注入 section),环境事实不走系统提示而走**覆盖式 runtime-context 快照**(每步重算、变化才发、随历史落盘),会话历史是事件日志折叠出的「表面」,超窗用**LLM 检查点压缩**(保留近期原文尾、摘要落盘为整段替换、审计不丢)。

### 1.1 系统提示 = 四类贡献的有序注册表
- `SystemPrompt` 服务管理 sections / contexts(动态运行时上下文)/ tools(schema 提供者)/ variables(`{{var}}` 插值)四类贡献,全局层+代理 scoped 层,同名 scoped 遮蔽全局(dsh-system-prompt/lib/index.js:179-198, 310-362)。
- 分节顺序是**中心化的顺序常量表**: HARNESS_IDENTITY(-1000)→部署 persona 前缀(0)→PLAN_POLICY(500)→TEAM_POLICY(600)→…→各工具节(TOOL_BASH 1000 … TOOL_SUBAGENT 2800)→MCP_SERVERS(3100)→TOOLS_SDK(5000)→交付物引用(9000)→STRUCTURED_OUTPUT(9900)→HARNESS_SOURCE(10000)→WEB_SURFACE(10100)→persona 后缀(10200)(dsh-system-prompt/lib/index.js:10-43)。运行时上下文三件: SANDBOX_POLICY(110)/APPROVAL_POLICY(115)/SUBAGENT_DELEGATION(120)(同文件:44-48)。
- 渲染: 严格 `{{name}}` 插值——未知/未定义变量直接 throw,空节丢弃,`\n\n` 连接(dsh-system-prompt/lib/index.js:113-115, 153-177)。可配 toolOrder 重排工具(`<unlisted-tools>` 必填占位)(62-91)。
- 系统提示的**缓存投影**: 首条系统提示占据表面节点 0;路由支持 in-history 系统消息时「变更才追加」;不支持时改写节点 0 并清空后续系统节点;节点 0 受保护——只能是 system/message 且只能被同型单节点替换(dsh-agent-loop/lib/index.js:239-296; dsh-session/lib/types/surface.js:388-397)。

### 1.2 runtime-context 快照
- 动态环境事实(沙箱策略/批准政策/子代理授权域)渲染为一条 **user message** 快照,固定前言 "This snapshot supersedes earlier runtime-context snapshots."(dsh-system-prompt/lib/index.js:132-136);每 step 在 `preStep` 里重新 assemble+投影,**内容变了才发新快照**,清空时发专门的 CLEARED 文案(dsh-agent-loop/lib/index.js:902-925, 298-350)。快照随会话日志持久化,重放自然重建当时的策略面(dsh-sandbox-policy/lib/index.js:52-55)。

### 1.3 会话历史 = 事件日志的「表面折叠」
- 模型可见历史不是存储形态: 存储是 append-only 事件流(`session.append(type, data, {surfaceOp})`),「表面」= 每个事件按 surfaceOp(append / replace 范围)折叠出的当前节点序列,`deriveMessages()` 由表面派生冻结的消息数组进请求(dsh-session/lib/types/surface.js:399-477; dsh-agent-loop/lib/index.js:1262-1276)。替换事件必须引用被遮蔽 seq,tool/result 替换**只许改 content**(dsh-session/lib/types/surface.js:355-381)——这就是「压缩改写历史但审计保留」的机制底座。
- 请求头(request/header 事件)携带 config+工具 schema 集,变更才记新头(reason=initial/resume/change/series,series 标记服务于供应商前缀缓存);工具集增减同时落一条 developer/message 通知模型(dsh-agent-loop/lib/index.js:1213-1247)。

### 1.4 技能与工作区指令
- 技能发现: 项目 `.dsh/skills/`+用户根(`~/.dsh`),支持目录 bundle 与扁平 Markdown,frontmatter 元数据,文件 watch(稳定窗防抖)触发失效(dsh-skill-filesystem/lib/index.js:30-45, 155; dsh-skill/lib/index.js:119 起)。技能内容经 `skill` 工具按需载入,不整包进系统提示。
- 工作区指令文件: AGENTS.md / CLAUDE.md(及 .local 变体),单文件 1MiB 上限,`<system-reminder>` 包裹注入,超限截断并明说(dsh-agent-instructions/lib/index.js:16-19, 111-116)。

### 1.5 截断与压缩(compaction-basic)
- **触发阈值**: `thresholdTokens = min(contextWindow × 0.8, contextWindow − reservedCompletion − headroom)`;保留尾部 `retainRatio=0.16`(或绝对 retainTokens);`headroomTokens` 默认 65536;`compactionRetries=1`、`maxOverflowRetries=1`;`auto` 默认 true;支持按 provider/model 精确覆盖(modelPolicies)(dsh-compaction-basic/lib/index.js:15-17, 63-86, 124-147)。
- 两个触发点: ①步间压力——`agent/pre-step` 钩子测压,超阈先剪枝工具结果再压缩,仍超则循环压缩至多 retries+1 次,失败告警但**继续本 turn**(839-860, 936-960);②供应商确认的上下文溢出(CONTEXT_WINDOW_EXCEEDED)——先 prune、再以 retainTokens=0 强制压缩、然后对原请求返回 {kind:"retry"} 重发(溢出重试上限 1)(861-887, 926-935)。手动 /compact(`compactNow`)要求 idle 代理,在 maintenance 窗口执行,成功后显式 flush 落盘(985-1011)。
- **摘要构造**: 固定 8 节英文结构(Primary Request and Intent / Key Technical Concepts / Files and Code / Errors and Fixes / Pending Jobs / Current Work / Next Step / Critical Context),要求逐字保留路径/命令/错误串/签名(243-278)。关键工程决策: **摘要指令作为会话前缀之后的最后一条 user message**,复用同一路由的 system+tools+消息前缀——供应商 KV cache 不失效(236-242, 282-338, 695-704)。
- **落盘**: 摘要包 `<compacted-summary>` 标签+「视为既定背景」前言,作为 user/message 以 surfaceOp replace 整段落盘(344-356, 650-661);压缩是日志内事务: compaction/start 是锁,失败也写 compaction/end(带 error),未闭合的 start 可被检测(436-521, 706-734)。护栏: 摘要字数必须小于被遮蔽内容(601);摘要被 max-tokens 截断=报错不做检查点(362-365);拒绝图片输出(371-373);选段永不拆开 assistant 工具调用/结果对、永不含系统头(410-433)。
- **确定性工具结果剪枝**(压缩前先跑): 单结果超 8192 字符(Unicode 码点)→保留头 4096+尾 1024+中段替换为 "[... tool result middle pruned ...]",replace 单节点,前置 compaction/prune 影子价格事件供 O(1) 计量折叠(dsh-compaction-tool-result-pruner/lib/index.js:8-14, 91-124, 137-191)。
- **图片卸载**: 路由报 IMAGE_OFFLOAD_REQUIRED 时按决定卸载最老的输入图片出现次,经持久 image/offload 投影事件(dsh-compaction-image-offload/lib/index.js:125-149)。

### 1.6 计价
- 启发式密度固定: CHARS_PER_TOKEN=4、每块结构开销 4、角色框开销 4(dsh-token-meter/lib/types/estimate.js:8-13);压力显示用「提供方 usage 锚定+增量估算」——上次真实 usage 为基线,只对表面增量做启发式计价(dsh-token-meter/lib/index.js:646-672),并如实注明系统性低估 CJK。

## ② 子代理体系

**一句话**: 子代理=同进程内「槽位限 8、深度限 1」的独立子会话——普通型零继承(简报必须自包含),fork 型只继承已完成 turn 前缀;子代理权限在创建瞬间冻结(批准政策钉死 never);打断是火返信号,续谈只许直接父子邻接,不驻留的子代理可从持久化冷恢复。

- **槽位与深度**: `maxActiveSubagents` 默认 8、`maxDepth` 默认 1(dsh-subagent/lib/index.js:2821-2824);进程内 ActivationPool 超限抛 `ACTIVATION_LIMIT_REACHED`(723-734);子深度=父深度+1,持久化的父请求头是**下限**——resume 过的父代理不能假装顶层再委托(400-405)。
- **简报构造(不继承上下文——有实证)**: 普通 subagent 工具描述原文即制度: "The complete, self-contained task for the subagent. **It does not share this conversation's context**, so include everything it needs."(dsh-tool-subagent/lib/index.js:349-352)。fork 变体才继承会话——种子=截至最后一个 turn/end 的**已完成 turn 前缀**,进行中的 turn 不进种子(dsh-subagent-fork-in-process/lib/index.js:8-21, 44-54),其工具描述相应改为 "already sees this conversation's completed turns"(dsh-tool-subagent/lib/index.js:344-348)。
- **子代理选项与谱系**: 继承父 provider/model/reasoningEffort/maxTokens(可逐项覆盖);子会话 header 记 parentSession/origin:"subagent"/delegationDepth/agentPreset,冷读可完整重建(dsh-subagent/lib/index.js:436-481)。
- **权限冻结**: 每个进程内子代理注入固定授权域声明("your permission scope was fixed when you were started and cannot be widened…")(487, 510-516);捕获委托策略: 批准政策一律钉 'never',仅显式沙箱覆盖随行,以 source:"delegation" 事件写进子日志(535-562)。子代理可叠加 persona 遮蔽节与 allow/deny 工具过滤(517-522)。
- **三种执行形态**(dsh-tool-subagent/lib/index.js:426-429, 521-560): foreground(阻塞至结果返回 output)/ background(一次性,包装为 job,`jobs.start({kind:"subagent"})`,返回 jobId)/ continuable(默认后台,返回 subagentId,提示词自动附上 send_message 回传指导,dsh-subagent/lib/index.js:599-605)。
- **续谈(send_message)**: 仅限**直接父或直接子**邻接;运行中目标在最近 step 边界注入,空闲目标开新 turn,不在内存的目标**从持久化冷恢复**(dsh-subagent/lib/index.js:2882-2898);代理间消息以 "Agent <id> sent a message: …" 的 user message 呈现并带发送者溯源(584-592)。
- **打断(interrupt)**: 火返语义——cancel 信号先于返回发出,目标可能继续跑到观察信号为止;未认领的 inbox 工作与 Activation 保留,已认领工作不重排(2914-2924)。
- **结果回传**: 后台子代理结束时父收到结算通知("Background subagent <id> finished…Its closing message: …"),stopReason 分 completed/aborted/max-tokens/refusal/error,未知终态一律报「未完成」而非成功(613-654);诊断截断上限 4096B(2494-2495)。
- (另有 experimental agent-team 多代理编排包,实验面,不展开。)

## ③ 恢复

**一句话**: 会话是事件日志,重启=冷读全部事件+给崩溃尾补**确定性合成收尾事件**(悬空工具调用记为「结果未知,仅幂等才重试」),goal 是会话日志内的状态机,轮转驱动器在落盘检查点之后才发下一轮。

- **resume 主路径**: persistence.open(write) → 冷读全部事件 → `interruptedTurnClosers`(补收尾) → 以事件为种子重建会话 → 发布代理(dsh-agent-loop/lib/index.js:1921-1978)。
- **崩溃尾修复**: 扫描开着的 turn/step,未应答的工具调用按 started/notStarted 合成 error 结果(code=TOOL_OUTCOME_UNKNOWN / TOOL_NOT_STARTED),再补 step/end、turn/end;合成事件 seq 续接日志、时间戳复用最后真实事件(确定性)(dsh-session/lib/types/repair.js:35-77, 84-189)。
- **恢复文案面向模型**: "The tool call was interrupted after it was recorded, but no result was durably recorded. Its outcome is unknown. **Decide whether to retry from the tool semantics: retry only if the operation is read-only or idempotent**; if it may have side effects, first verify external state or ask the user. Do not retry blindly." started/notStarted 两态、interrupted/forked 两因各配文案(repair.js:15-24)——把「是否重试」的幂等判断明确交给模型并给判据。
- **turn 内失败恢复**: step 执行包一个 ToolCallRecovery 观察器,step 抛错时先补记 pending 工具结果再重抛(dsh-agent-loop/lib/index.js:973-989);流式回答被中止时,已产出的部分内容以 interrupted:true 落盘(1084-1100);批量调度中止时未派发的调用记 "tool call aborted before dispatch" 合成结果保证重放合法(527-529, 662-679)。
- **goal 状态机**: 四相 active/paused/blocked/complete;变更走 revision 递增校验;blocked 必须带 lower-kebab code+message(dsh-goal/lib/index.js:455-481);goal **只存会话日志**("backed exclusively by the owning session log", 482),经 sessionProjections 折叠重建。
- **goal 轮转驱动**(dsh-goal-round-driver/lib/index.js): 代理 idle 且 goal active+armed 时,若 roundsStarted≥maxGoalRounds→自动 block(code=round-limit)(125-131);否则渲染 `<goal_round>` 续跑提示注入 followup——提示词明写 "**Treat the current workspace, tool results, and durable session state as authoritative; inspect them instead of assuming earlier narration is still current**"(防幻觉续跑)(11-18, 132-154);每轮之间强制 `sessions.flush()` 耐久检查点,flush 失败即 disarm(106-115);驱动失败/代理出错即 disarm,竞态围栏防重复排队(165-204)。
- **跨进程互斥**: 每会话目录有内核级写锁,跨进程写所有权互斥(dsh-session-persistence-jsonl/lib/index.js:614-660)。resume 时持久化的请求头让 reasoningEffort 等配置跨重启继承(dsh-agent-loop/lib/index.js:1171-1172)。

## ④ 预算与计量

**一句话**: 单一 tokenMeter 以「提供方 usage 锚定+启发式增量」计会话压力(四桶 usage、reasoning 不双计),LLM 重试是**持久化事件**(崩溃后不重数)的指数退避(默认 5 次/500ms 起/10s 封顶/10% 抖动),超时分层且 bash 超时**转后台作业而非杀**,后台作业有会话所有权与有界输出环。

- **token/成本**: 单一 replay 感知计量服务(dsh-token-meter);四桶提供方 usage 累计,reasoning 输出不重复计入(dsh-token-meter/lib/types/usage.js 注释);上下文占用投影=最近 usage 样本锚定+增量估算+替换走影子价格协议 O(1) 折叠(dsh-token-meter/lib/index.js:646-672)。**没有会话级 token 硬帽**——预算面是上下文压力(交给压缩),不是花费上限。
- **LLM 重试**: 指数退避 `min(initialDelayMs×2^min(n-1,1024), maxDelayMs)`×抖动;默认 maxRetries=5、initialDelayMs=500、maxDelayMs=10000、jitterRatio=0.1(dsh-llm/lib/index.js:247-250);retryableCodes 白名单+normal/always 两模式(dsh-llm-retry/lib/index.js:151-173)。**重试先落盘再等待**: llm/retry(调度)+llm/retry-started(等待完成)事件,retryId 跨链保持,计数从会话投影恢复(116-149; invariant 校验 39-99)。
- **超时分层**: 工具声明 timeoutMs 的合作式执法,超时返回 error 结果 "tool call timed out after Nms"(dsh-tool-call-timeout-policy/lib/index.js:90-130);bash 工具超时若配置 promote-on-timeout 则**前台命令转后台作业继续跑**(kind=promoted,返回 jobId),不杀(dsh-tool-bash/lib/index.js:421-486, 501-504)。
- **后台作业**(dsh-jobs/lib/index.js:66-122): 作业 id 可预测(`<kind>-N`)——「授权而非隐蔽是边界」;结算 first-wins(一个终态记录,迟到的产出不覆盖);每作业一个**有界输出环**(超保留窗丢最旧字节,落后读者得到有损读而非报错);settle 事件通知;会话归档时 kill 其全部运行中作业(19-38);start 前检查该 owner 有控制器可回收。bash 每次调用即注册为 job(前台等待也走 job 记录,dsh-tool-bash/lib/index.js:387-420)。
- **长输出**: 输出环+spill 文件路径(`output.spillPaths`)(dsh-tool-bash/lib/index.js:468-474);会话级统计/导出见 dsh-session-stats、dsh-session-log-export。

## ⑤ 工具执行

**一句话**: 独占工具成栅栏、并行工具进有界滚动池(默认 10)但**结果永远按模型序提交**;沙箱三模式(read-only 默认)由平台级 runner(bwrap/sandbox-exec)+进程内 fs 栅栏执行,拒绝词表统一;升级是「仅限严格更宽+justification 成对+一次一准」的批准流,批准政策 ask/never 进会话日志。

- **调度**(dsh-agent-loop/lib/index.js:474-533): 每步工具调用按并发模式分组——exclusive 调用自成栅栏,parallel 组滚动填充至 maxParallelToolCalls(默认 10,1285);`prepare→dispatch→finalize/finish` 阶段化(582-613);**结果与附加上下文按模型序提交**(565-576);abort 停止补员、排水在途、给未启动调用记合成结果(542-549, 662-679);工具可声明 concludesTurn 直接收敛回合(573)。
- **沙箱模式**: read-only / workspace-write / danger-full-access(dsh-sandbox-policy/lib/index.js:22-27),部署默认 **read-only**(97-104);会话内覆盖走 sandbox/mode 事件(会话日志即存储);单调用解析优先级=**已批准的一次性模式 > 会话覆盖 > 部署默认**(141-148);策略以固定文案注入 runtime context(72-83)。fs/bash/terminal 三个执行家族读**同一份**解析结果(48-62)。
- **执行级隔离**: bash 命令经 `ctx.sandbox.confine` 包装为受限 argv——Linux bwrap 优先、macOS sandbox-exec(SBPL profile),带功能探针(bwrap 能建 profile?seatbelt 真能拦 true?)(dsh-bash-sandbox/lib/index.js:65-118, 161-164; dsh-sandbox-local/lib/index.js:18-117);拒绝经 stderr 签名+exit code 分类(classifyDenial),**runner 自身失败=SandboxUnavailableError**(区分「被拒」与「沙箱坏了」)(104-116)。文件工具是进程内 policy 栅栏: 只拦两个写操作、读直通,文档如实声明「这是 containment 不是安全边界,存在 TOCTOU」(dsh-fs-sandbox/lib/types/containment.js:68-90)。写/编辑前置「先观察」策略(dsh-fs-observation-policy/lib/index.js:3-9)。
- **统一拒绝词表**: "[sandbox: file access denied under <mode> mode]" + 同回合升级提示 "[sandbox: escalation available — retry this exact <subject> once with sandbox_permissions (the narrowest wider mode that suffices) + justification…]"(dsh-sandbox/lib/index.js:57-88)。
- **批准流**: 政策 ask(默认)/never,never 固定文案 "approval prompts are disabled…rejected automatically"(dsh-user-approval/lib/index.js:36-65);政策切换落 approval/policy 事件并向模型通告(63-100)。升级: sandbox_permissions+justification **成对校验**(缺一即畸形请求)(dsh-sandbox/lib/index.js:51-55);同模式直接放行不批,**仅限严格更宽**目标,批准结果 allowed-once(仅本次调用生效)/rejected/cancelled/unavailable;拒绝后模型面文案 "stop and explain instead of working around it"(99-123)。Auto 权限预设=**LLM 审批门**(实验,评审模型逐调用替代人批)(dsh-experimental-auto-review/lib/index.js:6-21)。
- **失败重试语义**: 工具调用**无自动重试**——重试决定权在模型(恢复文案给幂等判据,见③),LLM 传输层重试在④;权限拒绝类永不重试(词表即指令)。

## ⑥ 持久化

**一句话**: 一切用户数据收口 `~/.dsh` 单根;会话=每会话一目录、每格式代一个 JSONL(可选 zstd)文件、首行 header、追加串行化、原子 rename+父目录 fsync 发布、跨进程内核写锁;格式演进走相邻版本迁移链;投影与会话级 fold 状态、SQLite FTS 只读索引都是**派生物,可随时重建**;载入与追加双向跑各包 invariant 校验——但**没有任何密码学防篡改**。

- **物理布局**: 每会话一目录,日志文件按格式代命名(v0 保留原名,后续 `…vN.jsonl[.zstd]`)(dsh-session-persistence-jsonl/lib/index.js:737-776);首行 header 必填 type/version/id/createdAt/isSeeded/delegationDepth,可选 cwd/parentSession/origin/agentPreset,**退役字段直接拒绝**(777-800);会话 id 编码为单射路径段,防 `../` 穿越(842-856)。
- **写入路径**: per-handle promise 链串行化全部变更;活动事件有界缓冲批量 drain(21-42);flush=耐久屏障,显式 flush 的空会话也物化(124-131);读侧单调视图——存储日志短于曾观察的前缀即报错(101-105);发布=临时文件+rename,POSIX 再 fsync 父目录,Windows 用原生命名空间原语保证等价耐久(441-447);断电尾(截断的最后半行)有修复 offset 计算(模块注释 737-738)。通用原子写库: 临时文件+rename+权限位保持+Windows 干扰重试(dsh-atomic-write/lib/index.js:5-51)。
- **格式迁移**: 迁移只能是相邻 vN→vN+1 且链完整可编译;无法无损迁移即抛 SessionFormatError(dsh-session-format/lib/index.js:88-102);仓库同时维护 v0→v1 … v3→v4 四个迁移包——旧会话永远可打开的显式承诺。
- **投影与查询**: sessionProjections 注册各包 fold 状态(turnBoundary、sandboxMode、approval、inbox、llmRetry、subagent catalog 等,各带 stateVersion)(例: dsh-agent-loop/lib/index.js:1352-1400; dsh-sandbox-policy/lib/index.js:114-120);投影缓存独立包;会话全文查询用 **SQLite FTS5 派生只读索引**——schema 版本不兼容就地重置,application id 防误挂(dsh-session-query-sqlite/lib/index.js:9-92)。均为派生数据,源=JSONL。
- **约束/goal/策略的存储**: 全部在会话日志内(goal 事件、sandbox/mode、approval/policy、llm/retry、compaction 事务……),没有独立约束库;settings/credentials 另有 dsh-settings、dsh-credentials-local(本地文件,未逐行核)。
- **完整性**: dsh-invariants 注册表——每个工作区包可注册 `./invariant` 校验,**载入的旧会话与新追加双向验证**(dsh-invariants/lib/index.js:4-11;例: llm-retry invariant 39-99,DeepSeek 会话日志验收水印 dsh-session-log-deepseek/lib/index.js:3-34)。**无哈希链/HMAC/签名**: 全树 grep sha256/hmac 仅命中附件内容寻址与 UI 渲染;dsh-util-crypto 只有 UUID 工具(dsh-util-crypto/lib/index.js:11-19)。

---

## ⑦ 对照清单(我方 = cli/warrior/,单测全绿、零实战)

### A. dsh 有、我们无(候选补,按优先级)

| # | 机制 | dsh 出处 | 优先级 | 对误报/漏报/可控的贡献 |
|---|---|---|---|---|
| 1 | 会话事件溯源+投影(append-only 日志、冷 resume、任何时刻可重放) | agent-loop:1921-1978; session/surface.js:399-477 | **P0** | 可控: 断点续跑从「timeline 末 K 行摘要」升级为「完整状态重建」 |
| 2 | 崩溃尾修复+幂等重试指导(openTurnClosers 合成收尾+TOOL_OUTCOME_UNKNOWN 文案) | session/types/repair.js:15-77,137-176 | **P0** | 漏报: 悬空工具结果不丢、模型拿到「仅幂等才重试」判据 |
| 3 | LLM 检查点压缩(0.8 触发/0.16 保尾/8 节固定结构/KV-cache 复用摘要/surface replace 保审计) | compaction-basic:15-17,236-356,450-675 | **P0** | 漏报: 长渗透链不因窗口爆掉断任务;摘要含 Pending Jobs/Next Step 防丢线索 |
| 4 | 上下文溢出自动恢复(prune→强制压缩→原请求重试) | compaction-basic:861-887,926-935 | P1 | 漏报+可控: 上下文超限不再是终态 |
| 5 | 三级沙箱+一次性升级批准流(bwrap/seatbelt 实执+严格更宽+justification 成对) | sandbox-policy:22-148; sandbox:42-123 | P1 | 可控: 渗透工具爆炸半径分级,比卡层门更硬 |
| 6 | goal 状态机+轮转驱动(armed/disarmed、maxGoalRounds、落盘检查点、防幻觉续跑提示) | goal-round-driver:105-164,11-18 | P1 | 可控+漏报: 多轮目标自动续跑有硬上限且断电安全 |
| 7 | 子代理体系(槽位8/深度1/零继承简报/continuable 续谈/后台作业化) | subagent:2821-2824,400-481; tool-subagent:344-360 | P1 | 可控: 大扫描分片并行、互不污染上下文 |
| 8 | 后台作业(有界输出环+first-wins 结算+bash 超时转后台) | dsh-jobs:66-122; tool-bash:421-486 | P1 | 漏报: 长 nmap/nuclei 不因单步超时而死 |
| 9 | runtime-context 覆盖式快照(环境事实每步重算、变化才发) | system-prompt:132-136; agent-loop:902-925 | P2 | 误报: 模型不再基于过期环境事实行动 |
| 10 | LLM 重试持久化(llm/retry 事件,崩溃后计数不重头) | llm-retry:116-149 | P2 | 可控: 退避预算不被重启清零 |
| 11 | 确定性工具结果中段剪枝(8192/4096/1024) | compaction-tool-result-pruner:8-14,91-124 | P2 | 漏报: 巨量扫描输出不全量挤占窗口 |
| 12 | 系统提示分节注册表(顺序常量+scoped 遮蔽+严格变量插值) | system-prompt:10-48,113-177,310-362 | P2 | 可控(架构): 提示组装从字符串拼接升级为可审计结构 |
| 13 | 会话格式版本+相邻迁移链(旧会话永远可打开) | session-format:88-102 + v0→v4 四包 | P2 | 可控: 升级不弃历史任务 |
| 14 | 载入即校验的 invariant 注册表(双向验证) | dsh-invariants:4-11 | P3 | 可控: 坏日志载入时暴露而非执行中 |

(P0×3 / P1×5 / P2×5 / P3×1,共 14 项。)

### B. 我们已对等

| 我方机制 | dsh 对应 | 备注 |
|---|---|---|
| 租约认领/让位(loop.py:306-320 claim/holds/yield) | 会话目录内核写锁+goal armed 态 | 形态不同(意图级 vs 会话级),语义对等 |
| 断点续跑(接管自己活租约+timeline 末行摘要,loop.py:306-308; context.py:27) | 冷 resume+事件重建 | dsh 重建完整状态,我们重建摘要——见 A1 |
| 停滞重生(heartbeat+StallDetected 自杀让租约超时回收,loop.py:161-163,342-349) | goal driver 失败 disarm+检查点 | 语义对等,我方带「不擅自迁移意图状态」纪律 |
| 并行批执行+序屏障(≤16 并行+同卡同目标串行+账写原序,executor.py) | 滚动池默认 10+模型序提交(agent-loop:551-661) | 对等;我方多「同卡同目标串行」渗透特化律 |
| 超大输出 spill(1MB 阈值落盘+头尾视图,executor.py:95-118) | 输出环+spillPaths | 对等 |
| 模型池通道/错误分类/冷却/429 切道(model_client.py) | llm-retry 单道退避+多 provider | 我方多道热切,此面**我方偏强** |
| 卡层门链+guardrail 两段判定(tools.gate/guardrail.py) | 沙箱+批准流+观察策略 | 侧重不同(卡级白名单 vs 系统级隔离),组合上对等 |

### C. 我们有、dsh 无(已验证确实没有)

| 我方机制 | 验证方式 | 结论 |
|---|---|---|
| 防篡改账本(哈希链 timeline+ledger validate,USAGE.md:114) | 全 dsh 树 grep sha256/hmac/hashChain/tamper: 仅命中附件内容寻址与 UI 渲染;dsh-util-crypto 仅 UUID | **dsh 无任何密码学完整性机制**——会话日志可被任何进程原地改写,只有结构校验 |
| 质量门(guard 执法/validate 收口/required 产物 fail-closed) | grep quality.?gate 全树: 唯一「gate」是实验性 Auto 权限预设的 **LLM 审批门**(auto-review:6-21)——审权限不审质量 | **dsh 无任务产物级质量门**;完成判据完全交给模型自报 |
| GT 考卷(56 分母召回 ground-truth/evals/金样回归/McNemar) | grep golden/exam/benchmark 全树: 仅 UI 渲染与文案误命中 | **dsh 无任何基准/考卷/评分机制**(度量考卷是我方独有资产,见 8-fork-candidates.md:46) |
| 卡层断路器(连续 3 败熔断 15/30/60min 阶梯冷却,executor.py:59-61) | dsh 工具失败无自动断路(重试权在模型) | 我方独有;dsh 对坏工具只有词表劝阻 |
| run 级 token 硬帽(budget.tsv fail-open 计量+触帽停,budget.py) | dsh 只有请求级 maxTokens 与压缩预算,无花费上限 | 我方独有(dsh 面向交互,我方面向任务预算) |
| 修正层 corrections(次轮自纠信号+钉住事实行,corrections.py) | dsh 无对应(只有恢复/拒绝文案) | 我方独有 |
| dry_run 零写零调演练(loop.py:351-356) | dsh 无等价物 | 我方独有 |

(共 7 项,前三项即母舰点名的三资产,验证均为「确实没有」。)

---

## ⑧ 最值得我们抄的三件(按对误报/漏报/可控的贡献排序)

1. **崩溃尾修复+幂等重试指导文案**(repair.js 全模块,抄形成本最低): 我方断点续跑目前只有「timeline 末 8 行摘要」,工具中断后结果归属不明——正是漏报温床(漏掉已成功但未记账的扫描)。dsh 的做法: 崩溃后确定性补合成收尾事件,悬空调用标注「结果未知;仅读操作/幂等才重试,有副作用先验证外部状态」——**把恢复期的重复执行风险显式交给模型判据**,而不是静默重跑(误报来源)或静默丢弃(漏报来源)。
2. **LLM 检查点压缩+溢出恢复**(compaction-basic 全包): 我方 cold-digest 只折叠 facts 节,聊天史与工具结果无压缩,长任务必然撞窗。dsh 三件套——0.8×窗口触发、保留 16% 近期原文、摘要固定 8 节(含 Pending Jobs/Next Step,**防丢任务线索**);加上 CONTEXT_WINDOW_EXCEEDED 的 prune→强制压缩→原请求重试,**上下文超限从终态变成可恢复态**。对渗透链(多轮扫描→利用→验证)这是漏报的第一防线。
3. **goal 轮转驱动**(goal-round-driver): 我方停序(yield→stop→预算→时间窗→停滞)是「停」,dsh 补了「续」——armed/disarmed 两态+maxGoalRounds 硬上限+每轮前落盘检查点+续跑提示词明写「以当前工作区与工具结果为准,不要相信此前叙述」(直接对幻觉续跑)。对我方: 停滞重生后从哪继续、继续几轮、何时判死,这套状态机是现成答案。

## 覆盖度自报(61 律)

- **精读全文/全模块**: dsh-system-prompt(365 行)、dsh-compaction-tool-result-pruner(194 行)、repair.js(190 行)、goal-round-driver 主文件关键 200 行、subagent child-agent/continuation-messages/activation 区段、tool-subagent 主区段、compaction-basic 关键 720 行(config/summarizer/region/engine)、agent-loop 主区段(211-1280+resume 1855-1981)。
- **结构级+定点核行**: dsh-session(surface.js 298-477 精读)、dsh-subagent(2815-2925)、dsh-goal(fold/service 区段)、dsh-token-meter、dsh-llm-retry、dsh-jobs、dsh-timeout、dsh-tool-call-timeout-policy、dsh-sandbox-policy、dsh-sandbox、dsh-bash-sandbox、dsh-sandbox-local、dsh-fs-sandbox、dsh-fs-observation-policy、dsh-user-approval、dsh-tool-bash、dsh-session-persistence-jsonl、dsh-atomic-write、dsh-session-format、dsh-session-query-sqlite、dsh-invariants、dsh-home-paths、dsh-skill(-filesystem)、dsh-agent-instructions、dsh-compaction-image-offload、dsh-experimental-auto-review。
- **未逐行(标注)**: settings/credentials 存储细节、typert 远程服务注册、web/acp 面、实验 agent-team 细节、pwsh/windows 沙箱方言——不影响六节结论。
- **我方侧**: loop/context/budget 全读,executor/guardrail 头部+grep 核行;对照基于 warrior 现状+8-fork-candidates.md 的三资产定义。
- 所有引用行号均本次会话实际 read 核验;lib/types/*.js(带 sourcemap)为逐模块原形行号,lib/index.js 为 bundle 实际行号。

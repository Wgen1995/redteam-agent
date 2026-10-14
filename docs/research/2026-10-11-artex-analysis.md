# ARTEX 深度分析报告（2026-10-11 实勘）

> 分析基础：全仓 810 文件树（GitHub API）+ README 全文 + agent/planner.go 等核心源码实读。
> 仓库：mhtsec/ARTEX（原 Autumn-27/ARTEX 纯源码备份，4027★/6337 fork，AGPL-3.0）。
> 姊妹篇：本目录 artex-vs-tanyin 对比决策报告。

## 一、项目身份

| 项 | 事实 |
|---|---|
| 定位 | AI 自主渗透测试系统——百度「agent+」攻防挑战赛冠军项目 |
| 形态 | Go 单体后端（go:embed 内嵌 Next.js 前端单二进制）+ PostgreSQL |
| Agent 能力 | 自研 norma SDK（agentcore/tool/permission/harness/memory/transcript 等 210 文件 vendored）|
| 规模 | 810 文件 / ~8.3MB；agent 52、server 103、db 97 |
| 许可 | AGPL-3.0 + 作者附加禁令：仅限学习研究，严禁对任何线上系统实测 |

## 二、设计哲学

「目标是什么」与「测到什么程度」分离成两张图；planner 只管派意图、worker 只执行一条意图；全系统事件驱动闭环。

三个关键抉择：
1. 图分离：资产=全局真值（跨任务共享），探索=任务级推进链（血缘可溯）
2. 意图单源：只有 planner 生成意图（防 worker 自增殖），worker 领一条做完即停
3. 过程即资产：worker 执行过程（非正式 fact 的观察）可被其他 worker 检索复用

## 三、总体架构

- 前端 Next.js 静态导出 go:embed 单二进制（:8787）：仪表盘/任务/资产/覆盖图/探索链路/流量/对话/审批/LLM 配置
- server：REST /api/* + JWT + SSE 活动流；Manager 托管任务/引擎/store 生命周期
- engine（每任务）：plannerLoop ×1 + worker goroutine ×N；意图领取/超时/暂停/drain
- agent 层：goals（目标分解+范围提取）/ planner（唯一意图源）/ worker ×N / mainagent（人在环路）/ retester（复测）
- 支撑子系统：traffic（MITM 记录代理 :8788）/ intercept+guard（审批门+守卫）/ enrich / llmpool / llmrec / notify（钉钉/飞书/邮件 26 文件）/ report / evidence / mcphttp（http+sse）/ selfupdate（自更新+3 连败回滚）/ skills（api-recon / playwright-cli / scopesentry）/ sidequestion
- PostgreSQL 双图落库（pgx）；schema go:embed 启动幂等迁移（重启即迁移）

## 四、核心创新①双图架构

- 资产图（全局共享真值库）：root_domain/subdomain/ip/service/app/endpoint，归属公司；父子关系与去重 key 全由程序计算，agent 只提交原始信息
- 探索图（每任务独立推进链）：goal/intent/fact/finding/hint 节点 + spawns/derived_from/yields/proves 血缘边
- 桥表 exploration_anchors(node_id, asset_id)：意图/事实/漏洞锚定资产 → 双向查询（方向→资产 / 资产→意图），支撑资产覆盖度与覆盖图

## 五、核心创新②事件驱动引擎闭环

图变更(debounce) → 唤醒 planner → 读态势（graph_overview 预取+coverage/scope）→ frontier 派 0..N 意图（多数唤醒派 0）→ worker claimNext 领一条 → 真实工具执行（全程经 MITM 代理留痕+CA 验证）→ 写回 fact/asset/finding+每步 activity → 图变更 → 再唤醒，直到 prove_goal。

planner.go 实读确认：唯一意图生成者；transcript 原始会话持久化；compaction 窗口；killWork/steerWork 引擎回调（运行中可杀/可改向）；任务约束注入 system prompt。

## 六、核心创新③三大自主性机制

1. worker 过程级信息交换：search_all_worker_traces(q) 检索其他 worker 执行过程（排除自己）→ get_worker_trace(id, step_ids) 取完整步骤。fact 未入图，观察已可复用；边界不变（各 worker 仍只做自己意图）。
2. planner 共享 todolist：planner 每次唤醒是全新无状态会话，靠按任务常驻的 todolist 把串行利用链记录一次、分轮派发（前置满足才派下一步）——事件驱动+无状态会话下多步链不乱序不重复。
3. 人在环路面：mainagent 对话审批；retester 独立复测 agent（三态结论，已修复自动同步）；sidequestion 侧问子系统（旁路提问预算管理）。

## 七、工程实现亮点

单二进制哲学；重启即迁移（幂等 schema）；SSE 同源（反代关缓冲即可）；五路安装+国内源友好；agent/db/server 普遍 _test.go 伴生。

## 八、批判性评估

优势：双图+锚点是真创新（资产真值与任务过程分离）；todolist 攻击链稳定器直击多 agent 最痛处；过程级信息交换精巧；工程成熟度极高。

局限（对照探隐）：无防幻觉精度门（finding 由 agent 写图无独立重放实证）；无哈希链防篡改（Postgres 可改）；无统计判决层（覆盖度≠召回率，无 GT 实验）；证据=被动流量录制而非主动可重放配方；部署重（Postgres/二进制）；预算无场景时钟/执法。


---

## 深读增补（2026-10-11 同日，五路子代理舰队）

全仓五视角深读（15-20 文件/路，来源行号全标注）已归档 artex-deep-dive/0-index.md（索引+交叉验证）。要点：
1. **fail-open 家族实锤**：intercept judge 默认关且失败按 allow（guard 链）；traffic MITM 失败开门透传（traffic.go:399-431）；activity 写失败 3 次丢弃——全子系统一致"宁可退化不可停摆"。
2. **todolist 纯内存**（planner.go:47）：重启丢串行链——README 宣称的"稳定攻击链"在重启面前无保护。
3. **45 表全景+kind×state 矩阵 CHECK**（schema.sql:184-193）：图结构有基本防线，但边方向仅注释约定、零审计链（sha256 仅在归档包）。
4. **llmpool 全参数**（v0.8a 蓝图）：错误分类表/硬熔断 1 次软 3 次/冷却 1-5-30min/"首个事件前才可转移"铁律/进程级 Registry 落库恢复。
5. **技能工程**：三层拆分+独立 message 注入+压缩后逐字重注入+三段式 prompt（纪律段代码锁定）——pentest-core SKILL.md 升级直接参照。
6. **哲学总判**：ARTEX availability-first，探隐 integrity-first——合体架构=运行态用它/审计态用我们，五路证据支撑该分层。

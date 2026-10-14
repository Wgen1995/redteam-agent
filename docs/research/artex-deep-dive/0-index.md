# ARTEX 五路深读 · 舰队索引与交叉验证（2026-10-11）

五路子代理独立只读实勘（编排/数据/安全门/可靠性/武器库），零共享上下文，结论事后交叉。

| 路 | 文件 | 深读文件数 | 核心产出 |
|---|---|---|---|
| 1 编排调度 | 1-orchestration.md | 15 | plannerLoop 六道门/800ms debounce/frontier=DB 单表 CAS/todolist 纯内存/steer 钩子/超时收尾时序 |
| 2 数据账本 | 2-data-graph.md | 16 | 45 表全景/kind×state 矩阵 CHECK/anchor 桥表/覆盖度 CTE/冷压缩 covers 层/重启即迁移 |
| 3 安全审批 | 3-security-gates.md | ~12 | ModeBypass+guard 三段判决/judge 默认关 fail_action=allow/裁判信息饥饿/CAS 审批/资产闸门子串绕过 |
| 4 工程可靠 | 4-reliability-ops.md | 14 | llmpool 全参数（硬熔断 1 次/软 3 次/冷却 1-5-30min/首事件前才可转移铁律）/selfupdate 三段式/SSE 断线恢复 |
| 5 武器技能 | 5-weaponry-skills.md | ~20 | 技能三层/独立 message+压缩重注入/三段式 prompt 代码锁定段/工具面即纪律/输出 choke point |

## 交叉验证结论

### 多路独立印证（可信度最高）
1. **零防篡改**（2 路 grep 全 db/*.go 无哈希链 + 3 路"改库=改史"）——双源实锤。
2. **fail-open 家族**（3 路 intercept judge 默认关+失败按 allow；4 路 traffic MITM 失败开门透传；1 路 activity 写失败 3 次即丢弃）——它在所有子系统一致选择"宁可退化不可停摆"。
3. **内存态脆弱**（1 路 todolist 纯内存重启丢串行链；4 路 llmpool 熔断 PG 抖动退化单进程内存）。
4. **字符串匹配当安全判据**（3 路正则绕过/子串双向错；4 路正则抠状态码/代理错误字符串匹配；1 路 DO $$ LIKE 判断约束）——SDK 无类型化错误的连锁恶果。
5. **边方向无强制**（2 路 DB 不校验 kind 组合只活在注释；对比我们 _EDGE_DIR 代码强制）。

### 一句话哲学对照（五路合成的总洞察）
> **ARTEX 是 availability-first（宁可退化不可停摆）；探隐是 integrity-first（宁可停摆不可说谎）。**
> 它的每个 fail-open/降级/字符串宽容都为竞赛连续输出优化；我们的每个 fail-closed/哈希链/门禁都为可签名交付优化。没有对错，只有战场不同——正好印证合体架构的分层：运行态（广度引擎）用它的哲学，审计态（裁判+账本）用我们的哲学。

### 它强且可搬（按 v0.8 批次映射）
- v0.8a llmpool：4 路全参数表（错误分类/硬软熔断/冷却阶梯/安全窗口铁律/进程级 Registry+落库恢复）——照抄+改两处（类型化状态码、429/5xx 分档冷却+抖动）。
- v0.8b 链稳定器：1 路 todolist 真相（纯内存=它的硬伤）→我们链落 intents.tsv 反而是升级；补 800ms debounce+触发/通道分离。
- v0.8c trace-search：5 路技能独立 message+2 路 activity 配对索引（tool_use/tool_result partial index）。
- v0.8d-f 中期：2 路覆盖度 CTE+冷压缩 covers 层+kind×state 矩阵；3 路 CAS 审批+信息饥饿裁判+三层判决（fail_action 反转）。

### 我们已有而它没有（深读后加确认）
哈希链（2 路 grep 证实）；ECDSA 供应链（4 路 selfupdate 只有 SHA256SUMS 无签名——v0.7c 正好补它）；边方向强制；审批-执行配对完整性（它 activity 可丢对，我们链不可丢）。

### 深读修正的前期认知
- 前期对比件说它"信任 agent 写图"——细化：DB 层有 kind×state 矩阵+rel 白名单（比想象严），但方向/组合/审计仍无防（比我们松）。对比件该论据须按 2 路报告微调（"图结构有基本防线，审计链零防线"）。
- 它的编排完全自持（未用 norma coordinator/plan 原语）——SDK 只是运行时底座，融合时不要指望从 norma 拿编排件。

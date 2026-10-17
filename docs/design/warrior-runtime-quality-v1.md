# 战士运行时质量律 v1(2026-10-18,基于 ARTEX/CSAI/VulnClaw 源码实读+业界调研)
缘起: 用户令「调度框架质量严重影响渗透能力,源码全授权,设计最好的」。源码证据: /Users/wgen/dsh-test/repos/ARTEX(planner.go 473行/worker.go 535行,norma/agentcore 库)+CyberStrikeAI(internal/handler/multi_agent 等)+.research/repos/VulnClaw(agent/ 5873行)。

## ARTEX 实读发现(质量标杆)
1. **角色铁律**(planner.go:16-19 注释原文): planner=唯一意图生成器(事件驱动·去抖唤醒·图变才醒); worker=领一意图→真工具执行→写事实→**停**(不自己开新方向)。多 worker=goroutine 并发。
2. **计划暂存箱 TodoStore**(planner.go:53-56): 每任务一块跨唤醒存活的计划草稿——**串行利用链逐轮派发,不前置并行倾倒**。
3. **上下文工程=一等子系统**: token 窗口追踪+冷节点压缩器 Compactor(§7 cold-digest,冷事实折叠成摘要)+transcript 原始对话独立持久化(LLM 录制)。
4. **steerWork/killWork 引擎回调**: 运行中工作可中途转向/终止。
5. ARTEX 的循环也坐在自家的 norma/agentcore 库上——启示: 我们的循环=自家「小 norma」(认领循环+工具协议+压缩),质量对齐 norma 特性集。

## VulnClaw 可移植件(Python 同语,~5900行 agent/)
- correction_layer(自纠信号: 工具生命周期事件→紧凑事实→下轮自纠,非强制工作流)
- kb_context(知识注入)+think_filter; subagent/ 全家(派发/预算/合并 2000+行)
- reflexion 失败分类+阶段迁移校验(constraint_policy)

## 落进我们运行时的五条质量律(空投在航舰)
R1 战士=一意图一脑: 每意图全新上下文(防串味),禁跨意图继承聊天史;血缘经账本行(facts/intents)传,不聊天史传
R2 串行链: 利用链意图带 derived_from 链序,逐个派发不前置倾倒(对齐 TodoStore)
R3 压缩器: 上下文超窗→冷事实折叠摘要(cold-digest 移植);token 计量入 budget 行
R4 原始对话独立存档: transcript 目录(不混账本;账本=纪律事件,transcript=全对话留痕=我们的「LLM 录制」)
R5 中途转向钩子: say 定向意图=steer;kill=既有 stop 扩展
规划者(W5)=独立去抖进程,唯一意图源,事件=timeline 行增长(A:D1 规格,与 ARTEX 同构验证)

## 实施增量
在航 MVP(~1800行)之上: R1-R5 增补 ≈ 900行 + VulnClaw 件移植(correction_layer/kb_context 先行 ≈ 600行适配)。

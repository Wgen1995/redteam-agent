# 07 架构设计专家（分层与演进）深度分析（2026-10-10 九维专家会诊）

> 含账本只读计时实测；两项关键发现经父代理活体复核确认。

## 现状强项
1. 账本是真"可判定真源"：哈希链逐行可验+原子写防 kill-9+保留词硬拒收防伪造快进（铸造权单源）+跳门检测；"烂帐=0 分"让幻觉零分——业界 AI 渗透工具普遍缺的底座。
2. 分层有真实代码兑现：watchdog 纯函数零依赖；gateloop 经 importlib 复用 runner 基建单一真源；SKILL 薄总控五不+CLI 边界；九门断言声明式 yaml。
3. 崩溃语义一等工程：b10 四件套+无 LLM 仿真；b24 三度点火零账损实战背书。
4. 度量飞轮真实闭环：22 战数据裁决文化（0.70 被复现实验证伪而非叙事放大）单人项目极罕见。
5. 契约文档密度：15 份接口契约+决策记录带"不采纳理由"——架构决策可审计。

## 关键缺口
1. 五层"互不越权"已是叙事而非代码事实：① runner 的 battle_complete 直接 grep timeline 原文找 gate-exit:P4——看门狗自带判据语义字符串复刻（词表一变静默失明）；② gateloop 逐门发令+每 tick spawn gate 全量断言=Python 掌战术节奏。深一层：gateloop 只接管门间转移，P3 内部两臂都仍是 AI 自律——b26 测不出"AI 总指挥行不行"只测"过门权归谁"。合理终态：推进策略显式建模为可插拔（ai-self/python-gate-loop/hybrid）。
2. 【父代理活体复核确认】判据完整性检查与实战流程不同步：b25 收官账本 verify-chain FAIL（缺 gate-exit:P5/P5.5，已达 P6.0 反推）——根因=战后人手 cleanup 行 phase 标 P6.0 被计为已达门；恢复协议第一步 verify-chain FAIL=停+人工——核心卖点"断点续跑"在自家最新收官战上是 halting 状态；尾部三门走手工旁路，错位藏在"分数是对的"表象下。
3. 账本读写放大（实测：裸 python 20-24ms，任一 ledger 命令 52-65ms，固定 ~35ms=全 13 表解析；写一条事件 O(表长) 累计 O(n²)；gateloop 活跃期每秒一条机械 gate-fail:P3——【父代理活体复核：b26 timeline 1273 行中 gate-fail 623 行=49%】）。业界：哈希链天然 append-only，单行 append+fsync 即保 crash 语义。
4. 并发模型=单机单写者，团队共享先坏 flock（跨机 unknown→保守重建实际不可用）；单写者模型本身正确但边界要成文。
5. 引擎总线纪律路由停在 prompt 级（_add_intent 不校验能力；接新引擎手改 4-5 处文本；"跨引擎知识流动"差异化未接线=纸面增值）。业界：MCP 式注册表。
6. state.md 200 行硬顶在大矩阵战有损（已知已管理债存照）。

## 可执行建议
| 建议 | 收益 | 量 |
|---|---|---|
| 判据层出只读 gate-status API，runner 改调它不再 grep | 层边界从字符串复刻变接口事实 | S |
| battle.py settle 加 verify-chain PASS 硬断言+尾部三门补 gate-exit 铸造 | 恢复协议在收官战永远可用（b25 现在是砖的） | S-M |
| timeline 改真 append-only+Session 惰性加载 | 写放大 O(n)→O(1) | M |
| gateloop 轮询去副作用（先 tail 看 gate-exit 再 spawn 断言 / gate --quick） | 轮询成本降 ~95% 杜绝机械 gate-fail 污染 | S |
| 引擎纪律路由下沉账本级（engines/registry.tsv+查表拒收） | 接新引擎从 5 处文本变 1 manifest+1 行注册 | S-M |
| b26 裁决文档化为"推进策略可插拔"非"谁指挥" | 防过度推断防细图代码分叉 | S |

## 对标
PentestGPT 同形态 2（多账本判据+飞轮，少并行+规模验证）；CAI 自建运行时 vs 探隐寄生宿主（换零代码分发，代价受 opencode 上限约束）；vuln-agent 单引擎纵深（跨引擎流动未接线=纸面）；dsh-pentest/GenCPT 六表先驱（探隐进化到八表九门哈希链金样回归）。

## 总评
一人红队做出大团队少见的"可判定 AI 渗透系统"——账本判据与度量飞轮是真资产；但"五层互不越权"一半是叙事：runner 复刻判据语义、gateloop 既掌节奏又以写副作用轮询判据、引擎纪律停在 prompt、尾部三门走旁路（b25 verify-chain FAIL 实锤）——b26 裁决后该做的不是站队，而是把"推进策略"与"判据查询"变成显式接口，让层边界从文档走进代码。

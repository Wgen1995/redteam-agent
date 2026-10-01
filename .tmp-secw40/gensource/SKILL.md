---
name: gensource
description: 源码自动漏洞挖掘的顶层调度入口。触发场景：用户对一份源码/仓库发起一次自动安全审计（找全、找准、稳定、全自动、逐漏洞详细报告）。不适用场景：只需要单独调用某个子阶段（如只跑候选发现或只生成报告）时，直接进入对应 skills/<stage>/SKILL.md。
---

# GenSource

> 设计权威：docs/superpowers/specs/2026-08-19-gensource-sdwr-mining-agent-design.md。与本文冲突时以该规格为准并回改本文件。
> 最高目标排序：找全（低漏报）→ 找准（低误报）→ 稳定（多次运行一致）→ 详细有据（逐漏洞详情）→ 全自动（不中途停问）→ 规模（百万/千万行）。

## 快速开始（唯一必选参数：source_path）

**发起一次审计只需要一个参数——被审计源码的绝对路径。** 其余全部自动派生，不需要人工逐项指定（完整参数表见 [`USAGE.md`](USAGE.md) 第2节，全部为可选）：
- `output_dir`（session 产物目录）未指定时，代理自选源码树外的一个目录并披露路径；
- 知识库路径固定为本技能包内 `{skill_dir}/knowledge`，不是运行参数，不需要用户提供；
- 是否新会话由 `{session_dir}/worklist.tsv` 是否存在判断，不需要用户显式声明"这是第一次跑"。

**新会话的启动顺序（阶段0 → 阶段1 入口，脚本命令，主代理直接 bash 跑）**：
```bash
python3 contracts/enumerate.py --source {source_path} --knowledge {skill_dir}/knowledge --output {session_dir}
python3 contracts/derive_checkpoints.py --session {session_dir}
python3 contracts/sdwr/session.py build --session {session_dir}
python3 contracts/sdwr/session.py drive --session {session_dir}   # 之后见下方「总控」
```
细节判断（技术栈探测、库/应用 source 模型、威胁语境保守假设）见 `skills/scope-and-context/SKILL.md`；这些是主代理自己读文件即可执行的编排/机械步骤，不需要用户在发起请求时提供。

**恢复已有会话**：只要 `{session_dir}/worklist.tsv` 已存在，直接跳过上面的启动顺序，从 `session.py drive` 开始（未闭合卡自动出现在 `NEXT=`，不需要额外指针）。

## 主代理零任务执行（编排语义 vs 任务语义）

主代理只做**编排语义**：理解 drive 打印的状态、组织派发内容、验收子代理产物格式、决定何时再跑 drive。
主代理禁止做**任务语义**：禁止自己 Read 目标源码判断漏洞、禁止自己写 verdict/confirmed/candidate 结论、禁止自己写 finding 叙述。

Summarizer / Confirmer / Analyzer / Verifier 与报告投影，一律通过 Task 派独立上下文子代理完成。
主代理只允许两类工具：bash（跑脚本，drive/prepare/build_graph/gate-1.py 等无语义判断的机械命令）、Task（派发四角色与报告）。

这不是"主代理不能语义"——主代理照样要理解流程、组织派发、做流程决策，这些都是语义判断，只是判断对象是"流程状态"，不延伸到"代码内容"。

## 总控（唯一调度权威）

**每一步都必须先跑脚本命令，禁止自己手写 Python 做脚本该做的事。**

无工作集时第一条命令：

```
python3 contracts/sdwr/session.py drive --session {S}
```

drive 一步完成：收分片 → 改写（K1–K4）→ 唤醒 blocked → 数卡 → 打印 NEXT= 或 L1_CLOSED。

**禁止自己手写 Python 脚本替代 drive。禁止用 `wu_decompose` 取卡。**

只认打印：

- `STATE=NEED_ANALYZE`：只分析 `NEXT=` 的卡，然后再次 drive。禁止 completed / 阶段2 / 阶段3。
- `STATE=L1_CLOSED`：才允许 Verifier 与报告。
- must_through 空则 K2 不消。Analyzer 必须写 collateral facts（kills/must_through/uncontrolled/intended/no_edge）到 facts.tsv 供级联。

队列顺序：backward（sink 回溯）→ forward（入口前向）→ terminal（文件兜底）。

**进度追踪粒度**：禁止用一条笼统 todo（如"阶段1: drive 循环至 L1 闭合"）覆盖整个逐卡分析过程——大项目可能是几十上百轮 drive，笼统一条会让人看不出真实进度，也容易诱发"赶紧把这一条做完"的偷懒心态。正确粒度：
- 类级剪枝（Summarizer + Confirmer）单独列一条 todo，**在"drive 循环至 L1 闭合"之前**，不要合并进去；
- drive 循环本身按轮次追踪（如"drive 第N轮：派X张卡"逐条完成即标记完成再开下一条），不要开一条笼统 todo 从头挂到 L1_CLOSED；
- 每次 `session.py drive` 打印 `NOTICE=LARGE_SCALE_LOW_RISK_NO_PRUNING_YET` 时（这条提示只针对低危噪音类，高危 sink 不受影响），补一条"低危类级剪枝"todo 并派 Summarizer 执行，但**不得因为这条提示暂停或推迟高危 sink 的 Analyzer 派发**——两条线并行，见 candidate-discovery/SKILL.md 9c0。
- **`NOTICE=SUSPECTED_TEMPLATED_EVIDENCE` 是最高优先级红色警报，禁止无视继续**：出现此提示说明有一批卡的"五段证据"文本高度重复（同一段原文被 5 个以上不同 sink 复用），极可能是主代理自己写脚本/绕开 Analyzer 子代理批量伪造证据的产物（历史真实发生：主代理直接写 Python 脚本给 7835 张卡编造同一段模板文本"消卡"，完全绕开了真实的逐 sink 五步分析）。看到这条提示必须：①立即停止派发新一批 ②用 `session.py retract` 或手动把该批涉及的卡状态重置为 unchecked、清空对应 reason（因为这些卡从未被真正分析过）③重新按正规 Task 派发流程逐 sink 分析 ④**主代理本身禁止直接写 Python/bash 脚本给卡片下 verdict/disproved 结论——这属于任务语义，只能通过 Task 派发 Analyzer 子代理完成，是本 SKILL 开篇"主代理零任务执行"红线的具体化**。

### 阶段序（批式完整流水线——doc-64 权威设计，禁止退化为项目级瀑布）

**核心原则（doc-64 §4）：阶段1/2/3-逐 finding 是同一个循环里的连续动作，不是三个各自等对方整体做完的项目级大门。每一轮 drive 新产出的 candidate，当轮就要走完"验证→定级→（confirmed 则）产出该 finding 的 findings/{candidate_id}-*.md"，不能攒到全项目 L1_CLOSED 之后才批量处理——这是"用户等多久才第一次看到一份完整、可读、带 CVSS 和修复建议的漏洞报告"的关键，绝不能退化成"跑完全部才有报告"。**

```
阶段0  枚举 → 发卡 → 注释 dead → 威胁语境
阶段1  高危 band(0/1) 立即逐卡 Analyzer 五步 ∥ 低危 band(2) Summarizer 类级事实+Confirmer 确认
       （两条线并行，高危绝不等低危剪枝跑完——见 candidate-discovery/SKILL.md 9c0）
       → drive 循环：每轮新增 candidate 立即转阶段2验证 → confirmed 立即转阶段3产出该
         finding 的 findings/{candidate_id}-*.md（同一轮内完成，不等 L1_CLOSED）→ 继续下一轮
       → 重复至 L1 空 → L2 邻域+A5 发散轮（≤20 假设）→ 再循环至 L2 闭合（每轮仍同样立即验证+出报告）
阶段2  仅对 candidate：六基线 + 对称反转 + FALSE-rules + 定级——**逐批增量执行，跟着阶段1
       每一轮新产出的 candidate 走，不是等阶段1 全项目收尾后才启动的单独大批次**
阶段3  findings/{candidate_id}-*.md 逐份增量产出（跟着阶段2 逐份确认走）；report.md 汇总索引+闭合门是
       全项目唯一需要等到最后的部分（去重/编号/gate/completion 声明必须看到全局才能做）
```

只有 `report.md` 的最终合并、编号、gate 判定、completed 声明需要等全项目收尾；单份 `findings/{candidate_id}-*.md` 本身、以及阶段2 对单个候选的验证结论，都不需要、也不允许等待——见 [`docs/research/64-batch-pipeline-design.md`](../docs/research/64-batch-pipeline-design.md) 第 4 节。

### 阶段 0：枚举

| 子任务 | 执行 | 产物 | gate |
|---|---|---|---|
| 0.1 初始化 | 建 run 目录 + 能力档案 | capability-profile.md | 文件存在 |
| 0.2 黄金自检 | **精确命令（两次真实审计撞过坑：误加 `--stage`/`--subtask` 会导致只跑 1 条方程去比对全量 golden 文件必然 FAIL）**：`python3 contracts/gate-1.py --session contracts/gate-selftest/fixture --source contracts/gate-selftest/fixture-src --expect contracts/gate-selftest/expected-gate.txt`——**不带 `--stage`/`--subtask`**，那两个参数是给正式跑分阶段中途检查用的，自检必须是全量方程 | SELFTEST: PASS | 不通过=blocked |
| 0.3 确定性枚举 | enumerate.py | file/sink/source_inventory.tsv + call_edges.tsv | gate 方程 |
| 0.4 检查点派生 | derive_checkpoints.py + session.py build | check_point_ledger.tsv + worklist.tsv | planned==terminal |
| 0.5 威胁语境 | 技术栈探测 | threat-context.md + attack-surface-map.md | 文件存在 |

**类级摘要不是阶段0 的顺序步骤**——它是阶段1 内与高危 sink 分析并行的一条独立线，绝不阻塞或抢在高危 sink 真实分析之前：让 Summarizer 的粗粒度判断有机会在 Analyzer 看到高危 sink 之前就把它们污染掉，或者让"什么时候才第一次看到真实漏洞"被不必要地推迟，都是不允许的。详细时序见 [`skills/candidate-discovery/SKILL.md`](skills/candidate-discovery/SKILL.md) 9c0 节。

### 阶段 1：残差分析至 L1 空（每轮闭环含验证+出报告，不是纯发现循环）

drive → NEXT= → 派 Analyzer（只拿 NEXT= 的卡）→ 五步 → 分片落盘 → 再 drive。
Analyzer 必须写 collateral facts（kills/must_through/uncontrolled/intended/no_edge）。
**drive 后 `live_findings_index.md` 每新增的 candidate，本轮内立即派阶段2 Verifier 验证**（不攒批、不等其它卡分析完）；confirmed 立即派阶段3 产出该 finding 的 `findings/{candidate_id}-*.md`。
重复至 L1_CLOSED。然后 L2 邻域+≤20 假设，再 drive 至 L2 闭合（同样每轮立即验证+出报告）。

### 阶段 2：验证与定级（跟着阶段1 逐轮增量执行，不是项目级单独大批次）

对本轮新出现的 candidate：六基线 + 对称反转双向严格 + FALSE-rules + 定级。
Verifier 不见 Analyzer 结论。critical/high 禁纯静态判 confirmed。
**触发时机 = 每次 drive 后 live 索引出现新 candidate 就触发，不是等 `STATE=L1_CLOSED` 才开始**——阶段1 完成硬门（见 candidate-discovery/SKILL.md 9d）管的是"阶段1 自身何时能声明完成/续跑"，从不管"验证/出报告什么时候可以开始"，那早就该在逐轮循环里进行了。

### 阶段 3：报告（单份 finding 增量产出；report.md 汇总是唯一等全项目的部分）

`findings/{candidate_id}-*.md`：阶段2 每确认一个 candidate 立即产出一份，不攒批、不等全项目收尾——这是本工具"用户不用等到最后才看到第一份完整报告"的核心承诺（doc-64 §4/§6）。
`report.md`：全项目唯一需要等收尾的产物——去重、确定性编号（severity 降序→root_cause_group_id）、覆盖度汇总、L1/L2 闭合数分开写、blocked/未确认必须列出，都需要看到全局状态才能做。
gate_result=pass 且 A2 独立验证通过才可写 completed。**终态门必须跑无 --stage 全量 gate（全部方程）。**

## 调度粒度

- **调度权威 = `session.py drive`**：取卡只认 drive 的 `NEXT=`。禁止 `wu_decompose`、禁止按文件号编批、禁止 `order_cards` 手排。
- `batch_size=10`：只限制并发 Analyzer 数，不是按文件号切批。
- 关键认知：**宁可多派简单任务，不要少派复杂任务——复杂任务必然偷懒。**
- todo = 本轮 `NEXT=` 的 card_id（一张一条）。禁止「Phase 1 工作集循环」吞掉队列。

## 图实体化（v0.10.1 doc 99：账本=真相，图=投影）

- **显式图文件**：`knowledge_graph/nodes.json` + `edges.json`（GenCPT 同思路，换画笔——doc 99 裁决）。节点 6 类（sink/source/file/checkpoint/candidate/finding，id 带类型前缀），边 3 类（flow=污点流、basis=清单→检查点、derived=检查点/位置/报告推导）。
- **LLM 禁止写图**：图由 `contracts/build_graph.py` 从账本确定性投影（零语义判断）；gate 校验图与投影一致（「图节点投影完整性」「图边投影完整性」「图投影确定性」「图边端点存在」四方程）且**gate 严格只读不写盘**（v0.11.0 修正）——账本/图更新后必须显式跑 `python3 contracts/build_graph.py --session {session_dir}` 重投影。手改图、图陈旧、悬空边都会被 gate 抓住。
- **消消乐/扫雷看图**：类级剪枝 → 节点 `status=pruned` + `pruned_by`/`pruned_reason`（pruning_ledger scope 机械匹配）；WU 逐实例 disproved → 节点 pruned；flow 边 `direction`（reachable/blocked_at/no_path）随 WU 翻转。
- **graph_snapshot 写方（v0.11.1 D①）**：主代理在**每次 `session.py drive` 调用之后立即**执行（不是模糊的「一批完成」——drive 循环一轮=图更新一轮，与 9c 步骤 5b 一致）：①`python3 contracts/build_graph.py --session {session_dir}` 重投影；②从图与账本机械统计并在 `graph_snapshot.tsv` 追加一行全 10 列（batch | unchecked | candidate | disproved | not_applicable | blocked | flow_edges | pruning_rules | graph_nodes | graph_edges）——各计数来源：ledger terminal_state 分组计数 + flow_edges/pruning_ledger 行数 + 图节点/边数。剪枝推进=计数递减。
- **最终图=漏洞路径图**：active 节点 + 边集就是完整溯源链（source→flow→sink→derived→candidate→finding）。
- call_edges.tsv 不入图（端点非节点 ID 空间，导航辅助表地位不变）。

## 覆盖不可谈判：不存在"预算"这个概念

**不存在"预算"这个说法。这个工具存在的意义就是让 LLM 不偷懒、不幻觉、稳定地把所有问题分析完——级联/剪枝/优先级排序全部只是效率优化手段（决定先查什么、后查什么、用完整五步还是高效判定路径查），不是覆盖率的谈判筹码。全部覆盖、零误报漏报是不可动摇的底线：审计只有 `session.py drive` 真正打印 `STATE=L1_CLOSED`（或阶段1按规则合法产出零候选终态）才算完成。即使级联完全不生效、退化成对每个检查点逐条暴力分析，只要能一直续跑下去，也必须能把全部检查点分析完——这是硬性要求，不是尽力而为。**

- **单次会话受上下文窗口等外部限制中途必须停时**，标 `run_status=blocked` 并写清楚：已处理数、剩余数、可直接执行的续跑命令（`session.py drive`）。这只是**会话边界的握手点**——下一次调用必须无条件从这里接着跑，不重新开始、不得视为"已经够了"、不得视为"接受这部分缺口"。
- **禁止把 blocked 当成可以对用户交付的最终状态**：中间报告/`live_findings_index.md` 可以标注"进行中，已处理 N/M"，但只要 `UNCHECKED>0` 就不得声称审计完成、不得进入阶段2/3（呼应下方"工作集未空不得进阶段2/3"铁律）。
- **上下文用尽本身不消耗"整个 run 至多一次人工提问"的名额**——这是纯技术性会话切换，不需要问用户"要不要继续"，下一次调用直接自动续跑。人工提问的名额只留给真正需要用户输入的场景（缺失授权/缺失关键路径参数）。
- 工作量预估（`预期并发轮次 = ceil(工作集未查卡数 / batch_size)`）只用于**规划深度分配的优先级顺序**（先查哪些、后查哪些），不是"能不能做完"的判断依据，**不是可以据此提前标 blocked 收尾的理由**。进度明显慢于预估时，先排查是不是级联/优先级机制本身没生效（真实审计教训：`component` 匹配粒度错误导致 `intended` 事实从未生效，被误判成"该收了"提前收尾，实际上是 bug 不是覆盖率该打折扣），排查无果就如实标 blocked 并续跑，而不是把"进度慢"当成"可以少覆盖"的理由。

## 全自动红线（违反即协议缺陷，必须写入缺陷清单）

1. **禁止中途进度汇报式提问**："已找到 N 个候选，是否继续""是否进入下一阶段"等一律禁止。进度只写 `live_findings_index.md` 供用户自查。
2. **威胁语境不阻塞**：阶段0 展示关键业务假设后直接以保守假设继续——写 `confirmation_policy=conservative_continue` 且 `user_confirmed=conservative_assumption_applied`（两个枚举值均已登记，见 enum-registry），不等待用户确认。
3. **整个 run 至多一次人工提问**，仅限两类：审计开始前的授权范围确认（一次）；`run_status=blocked` 的必需情形中**真正需要人工输入**的两种（缺关键输入/动态验证一次性授权）——**上下文用尽不占用这个名额**，属于自动续跑范畴，不得向用户提问"是否继续"。
4. 无法安全继续时（非上述情形）不得编造答案，按 work-graph 写 blocked 与恢复入口。
5. **Orchestrator 零分析**：Orchestrator 只编排（取工作集头部组成 WU、派 Analyzer、验收、改写），不做语义分析。
6. **任何一步输入是路径不是对话**：Analyzer 与下一阶段只读磁盘路径，不继承上一轮聊天。
7. **工作集未空不得进阶段 2/3**。

## 输入

```yaml
source_path: /absolute/path/to/source
run_mode: full                    # full | incremental；用户显式选择，不静默默认
authorized_scope:
  - /absolute/path/to/source
output_dir: <源码树外目录>/gensource-output
runtime_verification: denied      # allowed | denied；默认 denied
stability_check: false            # true 时跑连续双跑稳定性自检（见下）
resume: auto                      # auto | never
```

默认目标源码树只读；PoC/补丁/测试写入源码树外。用户未给 `output_dir` 时选择源码树外目录并披露。

## 初始化或恢复

1. 核实 `source_path` 存在、可读、已授权；不满足即停。
2. 创建 run 目录；记录 `source_revision`（git commit / 非 git 快照描述）。
3. 能力探测（只读），写出 `capability-profile.md`；冻结 `knowledge_snapshot_id`。
4. `resume=auto` 时查找未完成 run：读 `progress.json` + `run-state.md`，从 `remaining[0]` 续跑，禁从头重跑。
5. 写出初始 `run-state.md`（单一 YAML 文档，整文件替换；校验由宿主 shell 执行，见 `contracts/host-reconciliation-commands.md`）。

## 阶段路由

0.1→0.6（阶段0：枚举+摘要+首次改写+工作集 W0）→ drive 循环至 L1 空 → L2（邻域+≤20 假设）→ 再 drive 至 L2 闭合 → 候选提取 → 验证 → 报告 → completed。工作集未空不得进阶段 2/3。零候选仍须先 L2 再进阶段3 写零输入终态。任一子任务 partial → 补完该子任务；blocked → 停并写恢复入口。

## 稳定性契约（设计 28 号 §5，框架/历史依据）

- 稳定性运行要求 temperature=0 且同一模型（宿主不支持时由稳定性自检兜底并披露差异）；
- 机器字段（精确键名 candidate_id / location / sink_type / severity / root_cause_group_id / verdict——与 machine-fields.json 逐字一致）必须跨 run 一致；叙述字段（reason 措辞）允许微差；
- `run_fingerprint` = hash(排序后的机器字段集合)，写入 run-state，作为稳定性自检的对账对象；
- `stability_check=true`：在 `output_dir` 下建两个独立 session 子目录 `run-1/` 与 `run-2/`（各自独立的三清单/账本/findings/run-state，互不覆盖），连续跑 2 次全量（同 revision/同快照/同参数/同模型/同温度），然后对 `run-1/findings/machine-fields.json` 与 `run-2/findings/machine-fields.json` 做逐 finding 机器字段 diff（字段集合唯一定义见 `contracts/run-state-template.md` 的 run_fingerprint 口径），差异为空=稳定；非空产出 `stability-diff.md` 逐条列差异并反馈知识演进，不允许静默。

## 伴生能力（按需触发，不进主序列）

- 利用证明 `skills/exploit-proof/SKILL.md`：默认并入 finding 内"利用方式"小节，仅用户显式请求才独立执行；
- 修复指导 `skills/remediation-guidance/SKILL.md`：默认并入 finding 内"修复建议"小节，仅显式请求才独立执行；
- 生命周期治理 `skills/lifecycle-governance/SKILL.md`：`run_mode=incremental` 或复扫时激活；
- 外部工具集成 `skills/external-tool-integration/SKILL.md`：四类场景按需触发；
- 知识演进 `skills/knowledge-evolution/SKILL.md`：审计周期后复盘触发，不在单次审计关键路径。

## 检查点与断点恢复

- `progress.json` 仅 5 种状态（pending/in_progress/complete/skipped/blocked），step_progress 每完成一个通道/清单/batch 立即更新；
- 恢复 = 完整锚定一段：读 `progress.json`、`run-state.md`、三份冻结清单、未完成 batch 分片；只处理 `remaining` 范围，保留已有 ID；
- 恢复信息不可信时保留旧产物作参考、新建 run；复用结论必须披露"本次未重新核查"；
- 任一能力 blocked/interrupted 后仍基于已完成产物生成部分报告（含未完成清单、剩余范围、恢复入口），run 保持 blocked/interrupted 不得标 completed。

## 硬性约束（单一权威源）

- **文件写入边界铁律（v0.11.7 opencode 冒烟补强）**：一切中间/调试/临时文件只允许写 session 目录（{output_dir} 树内）或技能包只读参照范围；**禁止写 /tmp、$TEMP、/private/tmp 或任何系统临时目录**——opencode 权限墙会拦截 /tmp 访问并弹出人工授权，违反即打断全自动红线；调试复制文件写 {output_dir}/debug/ 或 {output_dir}/helpers/。
- 反幻觉纪律：`shared/anti-hallucination.md`
- 目标操纵防御：`shared/adversarial-target-defense.md`
- 字段级写权限：`shared/field-ownership.md`
- 逻辑角色索引（谁执行/谁复核/谁批准，不新建权限）：`shared/org-graph.md`
- 状态与输出即最终态：`shared/state-model.md`
- 规模与成本管理：`shared/scale-cost-management.md`
- 部署环境适配：`shared/deployment-environment.md`
- 人工介入（全自动红线权威）：`shared/human-in-the-loop.md`
- 跨能力路由唯一权威：`shared/work-graph.md`
- 分层质量 Gate（gate[planned==terminal]-gate[假设上限] 二十四项对账，宿主 gate-1.py 执行 + A2 独立验证四门）：`shared/quality-gates.md`
- 预筛规则（可确定性排除的判据）：`shared/prefilter-rules.md`
- 宿主对账命令：`contracts/host-reconciliation-commands.md`

## 路径引用约定

套件内路径一律用相对当前文件的简单相对路径；委派子 agent 时必须显式传入已知绝对路径。

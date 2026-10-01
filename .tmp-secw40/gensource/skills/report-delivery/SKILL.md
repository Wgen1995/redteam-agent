---
name: report-delivery
description: 阶段3报告交付（双产物，两种触发时机不同）。**逐份 findings/{candidate_id}-*.md 增量产出**：阶段2每确认一个候选就触发一次，不等阶段0/1/2整个项目收尾（doc-64批式流水线，见verification-and-rating/SKILL.md"触发时机"）。**汇总索引 report.md**：仍是全项目唯一需要等阶段0/1/2全部终态后才产出的部分（去重/编号/覆盖度/gate都需要全局视图）。把阶段0-2数据确定性投影为两产物，不重新判断真实性/严重度/复现/修复。只把 verification_verdict.value=confirmed、存在活攻击面且 final_severity!=informational 的 candidate 称为 finding；informational 单列为 code-hygiene item。报告出错返回字段所有者修正后重新投影，不手工改写报告制造第二事实源。
---

# 报告交付（阶段3 · 双产物）

> 设计权威（框架/历史依据，v0.11.1 U-A1 标注——doc-28 已被 doc-36/63 取代为机制权威，本文引用其框架）：`../../../docs/research/28-detection-engine-design.md` 第 8 节（报告设计）。本阶段是检测主序列最后一步，把阶段0（客观枚举）、阶段1（候选全量发现）、阶段2（验证与定级）以及伴生的可利用性证明/修复指导产出，确定性投影为两份产物：`findings/{candidate_id}-*.md`（逐漏洞详情）与 `report.md`（汇总索引）。与设计文档冲突时以设计文档为准并回改本文件。

## 目标

- **逐漏洞详情**：每个 confirmed finding 一份 `findings/{candidate_id}-*.md`，结构遵循 [`../../contracts/report-templates/finding-template.md`](../../contracts/report-templates/finding-template.md)（八节：识别信息 / 漏洞摘要 / 调用链 / CVSS 3.1 / 详细分析 / 数据流语义变迁表 / 证据分级标注 / 三态结论）。
- **汇总索引**：`report.md` 只索引不复制详情，结构遵循 [`../../contracts/report-templates/report-template.md`](../../contracts/report-templates/report-template.md)。
- **确定性投影**：报告不引入新判断，不产生第二事实源。

## 输入（全部只读，不得改写）

| 名称 | 来源阶段 | 说明 |
|---|---|---|
| 三份冻结清单 `file_inventory.tsv` / `sink_inventory.tsv` / `source_inventory.tsv` | 阶段0 | 检测概况对账分母（文件总数）；深扫 / 预筛排除分母来源见下一行 |
| `check_point_ledger.tsv` | 阶段1 | 检查点闭合与 gate 全方程对账；检测概况深扫 / 预筛排除按 `mechanism` 列对文件终态行分组计数（见 host-reconciliation-commands.md 第9节）；未分析 = `terminal_state=blocked` |
| `candidates.tsv` | 阶段1，`session.py drive` 每轮机械同步（`sync_candidates_tsv`，见 candidate-discovery/SKILL.md 9b1） | 候选清单：确定性 `candidate_id` / `root_cause_group_id` / `cross_boundary_path` / `location`。**本阶段生成 finding 文件名必须读这份文件的 `candidate_id` 列，禁止自己编号（如 V01/V02）——该文件不存在或找不到对应候选行时，先回 candidate-discovery 确认 `session.py drive` 是否正常跑过，不得跳过直接自造文件名** |
| `verification-summary.md` | 阶段2 | `verification_verdict` / `confidence_score` / `verification_baseline` / `impact_rating` / `likelihood_rating` / `final_severity` / `priority` / `cvss_vector` / `control_assessment` / `second_opinion_review` / 三态结论与证据分级 |
| `threat-context.md` / `attack-surface-map.md` | 阶段0 | 覆盖度章节 Surface/RiskArea 来源与 `Not applicable` 判定依据 |
| `failed_wus.txt` | 各阶段 | 未分析清单唯一来源（必须空，或逐条列入报告） |
| `run-state.md` | 顶层 | `revision` / `run_fingerprint` / 模型宿主角标 / `stability_check` 结果 |
| 可利用性证明 / 修复指导产出 | 伴生 | finding 内"利用方式"/"修复建议"小节来源；`informational` 不引用（其 `poc_ref`/`remediation_ref` 为 null） |
| `partial_report_context` | 任一 `stage_result=partial` 的上游 | 逐阶段 `incomplete_capabilities`/`remaining_scope`/`resume_entry`/`affected_conclusions`，生成部分报告 |

## 硬性约束

引用 `../../shared/anti-hallucination.md`（A 类证据溯源纪律：每个角色标签的代码证据片段必须对应阶段2 `verification_baseline`/证据链中已存在的具体引用，不得为叙事流畅编造位置或步骤）、`../../shared/field-ownership.md`（字段级写权限：本阶段对上游字段只读，报告层无上游字段写权限）、`../../shared/quality-gates.md`（Gate-1 客观对账 / 全方程语义）、`../../shared/state-model.md`（`stage_result`/`run_status` 语义边界）、`../../shared/work-graph.md`（跨能力路由唯一权威）、`../../shared/scale-cost-management.md`（大规模场景后续跟进提示）。

本阶段专属约束（逐条对应设计文档 28 号第 8 节）：

1. **确定性投影**：报告文本任何内容必须能追溯到上游某个结构化字段；生成后若发现文本与结构化数据不一致或缺失，返回唯一写入方（字段所有者）修正上游结构，再重新投影，不得直接手工编辑报告文本"补上"或"修正"，不得制造第二事实源。
2. **finding 身份边界**：`confirmed` 只是验证终态。只有同时满足 `verification_verdict.value=confirmed`、存在活攻击面且 `final_severity!=informational` 的 candidate 才称为 finding、才生成 `findings/{candidate_id}-*.md`。`confirmed+informational` 是 code-hygiene item，在 report.md 单列，不得称 finding、不得有 `finding_id`、不生成详情文件；`unconfirmed` 与 `refuted` 仍是 candidate，不生成详情文件。`final_severity=ignore` 是有活路径的政策忽略 finding，仍生成详情文件并进入 #9 显式处置。报告始终以 `candidate_id` 投影，不生成也不写 `finding_id`；仅当 #9 生命周期台账已存在等值 `finding_id` 别名时才只读显示该别名。
3. **确定性排序**：`N` 为确定性排序序号，按 severity 降序（Critical→High→Medium→Low→Ignore）→ `root_cause_group_id` 稳定键 → 稳定键（唯一指定 `candidate_id`）升序（`LC_ALL=C`）。不得用时间戳、发现顺序或并行完成顺序编号；同一根因组内独立实例逐条列出，不合并省略。
4. **只索引不复制**：report.md 每条 finding 只写编号/摘要/对象定位/详情链接；证据链、代码上下文、CVSS 逐项解释等大段内容只在 `findings/{candidate_id}-*.md`。
5. **危害最小化（报告脱敏，GenSource 原创）**：报告不复制 #6 PoC 过程中取得的真实敏感数据内容，只描述"证明了能访问到 X 类型/X 条记录"这类效果性陈述；已在上游 `harm_minimization_note` 完成的脱敏处置，本阶段只核对是否被完整保留、未被转录还原。
6. **零发现显式说明**：无任何 finding 时不得沉默，必须显式说明"为什么没有发现存活"（引用零候选兜底、证伪记录、覆盖度）；即使存在 informational code-hygiene item 也仍属零 finding 报告；覆盖度章节依然完整产出。
7. **引用路径**：套件内路径一律相对当前文件；详情模板与汇总模板见 `../../contracts/report-templates/`，枚举见 `../../contracts/enum-registry.md`。
8. **L1/L2 与 blocked 披露**：report.md 必须有「L1 闭合数 / L2 闭合数 / blocked 列表 / 未确认列表」。禁止把 blocked 写成无漏洞。级联透明度是本条的一部分（见 D 节「级联透明度」）：闭合数不得只给一个总数，必须拆分级联消卡与逐个分析闭合两类，否则视为披露不完整。

## 执行步骤（两部分，触发时机不同——不要把 Part 1 也拖到全项目收尾才做）

### Part 1：逐 finding 增量产出（每次阶段2确认一个新候选立即触发一次，贯穿整个审计过程）

### B. 确定单份 finding 的稳定文件身份（立即可定，不依赖全局排名）

阶段2 每确认一个候选（`verification_verdict.value=confirmed` + 活攻击面 + 非 `informational`），本节立即执行：
1. `confirmed+informational` 记录单列为 code-hygiene items（非 finding），不产出详情文件，跳过下一步。
2. 其余 confirmed finding：**文件身份用 `candidate_id`，不用排名序号**——`candidate_id` 在阶段1 发现时已确定性生成（`C-{sink_seq}-{source_seq}-{sig8}`），此刻立即可用、永不改变，不需要等其它候选一起确认才能定。文件名 = `findings/{candidate_id}-{severity小写}-{sink_type}-{文件基名}-{起始行}.md`（人眼可读部分，不含排名）。

> **为什么不能用排名序号 `N` 当文件身份**：`N` 的定义是"severity 降序 → root_cause_group_id → 稳定键升序"的全局排名，只有见到全部 finding 才能确定——如果按确认顺序提前把 `N` 焊进文件名，后面confirm 出一个更高危的 finding 就会让所有已产出文件的编号全部错位，要么被迫事后重命名（违反"产出后立即可用、不依赖后续"的增量目标），要么排名从此失真。`candidate_id` 从阶段1起就唯一且不再变化，正好解决这个矛盾。`N` 仍然存在，但被移到 Part 2：report.md 生成时才计算，只用于 report.md 的展示序号和每份 finding 文件顶部标题行 `# V{N}: ...` 的机械回填（见 D 节末尾），不影响文件名本身。

### C. 生成该 finding 的 findings/{candidate_id}-*.md（逐漏洞详情，单份、立即产出）

阶段2 一确认某候选，立即按 finding-template.md 八节为**这一个** finding 生成一份 `findings/{candidate_id}-*.md`——不等其它候选也验证完、不攒批：
- 识别信息（`finding_id=candidate_id`、对象定位 `file:line`、创建/更新时间）；
- 漏洞摘要（一句话 + 严重度 Critical/High/Medium/Low/Ignore）；
- 调用链（source→propagation→sink 逐节点 `file:line` + 角色 + 前后≥3 行代码 + 关键行标记；跨文件用 `cross_boundary_path` 逐跳）；
- CVSS 3.1（分数 + 向量 + AV/AC/PR/UI/S/C/I/A 八分量逐项中文解释）；
- 详细分析（漏洞说明含问题代码与编号触发步骤与影响、利用方式含具体例子、修复建议含代码示例、安全措施分析表含已有防护位置有效性）；
- 数据流语义变迁表（步骤/位置/变量/语义/状态/原因）；
- 证据分级标注（每关键判断标 `direct`/`indirect`/`unknown`；unconfirmed 写明缺口位置与所需证据）；
- 三态结论 + confidence。

所有证据片段与代码位置必须来自阶段2 `verification_baseline`/证据链已存在引用，禁止编造。**这一份文件产出后立即可读、可交付——不依赖阶段0/1/2其它任何部分是否已经收尾。**

---

### Part 2：最终报告合并（全项目唯一需要等阶段0/1/2全部终态后才执行的部分）

### A. 输入对账与硬门前置检查

投影前核对：`run_status`、各 `stage_result`、Gate 结果（Gate-1/Gate-2）、check point 闭合摘要、WU 闭合摘要、`pass_with_gaps`、`blocked`/`interrupted`、`independence_degraded`、能力降级、incremental 跳过范围、动态执行限制、剩余续跑范围（remaining_scope_refs，标明还需续跑才能全覆盖，不是可放弃的缺口）。任一对账字段缺失不得静默跳过，必须在报告缺口披露中体现。

### D. 生成 report.md（汇总索引）

按 report-template.md 生成，只索引：
- 检测概况（扫描范围 / 文件总数 / 深扫数 / 预筛排除数附规则 / 未分析清单 / L1 闭合数 / L2 闭合数 / blocked 列表 / 未确认列表 / 检测时间 / revision / run_fingerprint / 模型宿主角标）；禁止把 blocked 写成无漏洞；
- 违规汇总（按严重度计数，含"待确认"区与 Informational 单列）；
- 按模块分布表；
- 分级分区表（编号 `N` / 摘要 / 对象定位 / 详情链接 `findings/{candidate_id}-*.md`）——**此刻按 severity 降序 → root_cause_group_id → 稳定键升序**为全部 finding 计算最终 `N`；
- **`N` 机械回填**（两处，必须同步，否则 gate[V 文件候选映射] FAIL）：①对每份已产出的 `findings/{candidate_id}-*.md`，把文件顶部标题行 `# V{N}: ...` 的 `N` 替换为本次计算结果（纯字符串替换标题行的排名数字，不改动文件其余任何内容——不是"重新生成报告"，是"给已经真实产出的详情文件贴上最终排名标签"，与 `live_findings_index.md` 每次 drive 后机械重生成同一纪律：机械投影，不是语义改写）；②同步把 `candidates.tsv` 该候选行的 `report_record_ref` 列写为 `V{N}`（此前该列在 Part 1 阶段应为空——候选刚确认时还不知道最终排名，只有 Part 2 汇总时才能算）；
- 覆盖度章节（Surface Outcome 枚举 `Reported`/`No issue found`/`Rejected`/`Not applicable`/`Needs follow-up`）+ 缺口披露 + 稳定性声明。
- **级联透明度**（D3，消消乐可追溯性）：跑 `python3 contracts/sdwr/session.py radius --session {session_dir}`，检测概况里把闭合数拆成两类——「级联消卡数」（worklist `reason` 含 `:fact=` 的行数，即被某条事实一次性消掉一批的卡）与「逐个分析闭合数」（`reason` 以 `shard:` 开头，即 Analyzer 逐 sink 分析后闭合的卡）；再附一张 Top-N（默认 5，不足则全列）最高爆炸半径事实表：`fact_id | 消卡数 | 事实类型 | 判定依据摘要（evidence 行号）`，供读者判断"如果这条事实是误判，影响面有多大"——半径越大的事实理应在阶段2 被越优先复核（呼应 A2-verifier 的 D1 复核优先级）。半径为空（无级联发生，全部逐个分析）时如实写"本次审计无级联消卡，全部逐个分析"，不得省略该段。

### E. 检测概况对账

- 文件总数 = 深扫数 + 预筛排除数 + 未分析数；计数由宿主 shell（`wc -l`/jq）动态推导，不硬编码。
- 预筛排除数必须附排除规则名；未分析清单必须为空，或逐条列出（引用 `failed_wus.txt`），禁止静默。
- `revision`、`run_fingerprint`、模型宿主角标从 `run-state.md` 投影。

### F. 覆盖度章节（Reviewed Surfaces）

1. 固定列 Surface / RiskArea / Outcome / Notes；Surface/RiskArea 取自阶段0 `attack-surface-map.md` 的 `named_category_scan_results`/`file_level_inventory` 与 `threat-context.md` 界定的风险域。
2. Outcome 按同一 Surface 整组聚合且只产生一个结果，优先级固定 `reported > needs_follow_up > rejected > not_applicable > no_issue_found`（机器值与展示值映射见 enum-registry 报告覆盖结果）。
3. Notes 摘录判定依据引用，不重复整段证据；`coverage_diff.decreased=true` 时原样投影其告警。
4. 规模性覆盖不足时，应用 `../../shared/scale-cost-management.md` 后续跟进提示（具体到文件/函数级高预估风险指向，不是泛泛"待确定"）。

### G. 稳定性声明段

`stability_check=true` 时引用 `stability-diff.md`：差异为空 = 稳定（机器字段一致 + `run_fingerprint` 一致）；差异非空 = 不稳定，逐条列出差异字段与根因归类（ID/判定/严重度/根因组），不允许静默。`stability_check=false` 时显式说明本次未启用自检、不作稳定性声明。

### H. 危害最小化核对

核对 `findings/{candidate_id}-*.md` 与 report.md 均未复制 #6 取得的真实敏感数据内容，只保留效果性陈述。

### I. 零发现兜底

无任何 finding 时：report.md 仍完整产出违规汇总（finding 为空说明 + 保留 informational code-hygiene 清单）、完整覆盖度章节与显式零发现原因说明，不得省略报告文件本身。

## 输出（与 `../../USAGE.md` 第 6 节产物清单一致）

| 产物 | 说明 |
|---|---|
| `findings/{candidate_id}-*.md` | 逐漏洞详情，**每个 confirmed finding（含 Medium/Low/Ignore）一份，阶段2 一确认立即产出，不等其它候选**；文件名 = `{candidate_id}-{severity小写}-{sink_type}-{文件基名}-{起始行}.md`（`candidate_id` 阶段1 起唯一且不再变化，是文件身份；不含排名序号，避免后续更高危 finding 出现时引发重命名）；`unconfirmed`/`refuted` 不产出详情文件；文件内顶部标题行 `# V{N}: ...` 的 `N` 由 Part 2 report.md 生成时机械回填（见 D 节末尾），是展示排名，不是文件身份 |
| `findings/machine-fields.json` | **覆盖全部 confirmed finding（含 Medium/Low/Ignore）**，每条一个 9 字段机器投影对象（`candidate_id`/`location`/`sink_type`/`severity`/`root_cause_group_id`/`verdict` + `confidence`/`evidence_grade`/`runtime_tier`）的确定性投影，不做新判断；`run_fingerprint` 只取核心 6 字段。**禁止只写 Critical/High 子集——否则指纹失真、稳定性自检失效** |
| `gate_record.md` | Gate-1 gate[planned==terminal] 起全部方程逐条的命令、实际输出与判定（宿主执行 §4c 一体块生成，强制产物；缺文件=Gate 未执行，见 quality-gates.md 总则） |
| `report.md` | 汇总索引报告（检测概况含文件总数/未分析清单） |
| `stability-diff.md` | 稳定性自检差异（`stability_check=true` 且双跑差异非空时产出） |

> 报告封装文件名由运行时交付约定决定，但上述五个产物名必须与 USAGE.md 一致；字段名与枚举不得偏离 contracts。

## 8 节投影对账（设计 34 号 §4，生成每份 findings/{candidate_id}-*.md 前必做）

对每个 finding 逐节核对上游字段存在（生产时刻映射表见 [`../../contracts/report-templates/finding-template.md`](../../contracts/report-templates/finding-template.md)）：识别信息（candidates.tsv）→ 摘要/严重度（root_cause_summary/final_severity）→ 调用链（证据链五段（簇结论 cluster 内 source/propagation/sanitizers/sink/disproof_checked 各段含 hop_snippet）非空，**禁止重读源码补片段**）→ CVSS（cvss_vector + cvss_breakdown）→ 详细分析（证据链五段/impact_description/exploit_scenario/remediation/control_assessment）→ 语义变迁（semantic_transitions）→ 证据分级（evidence_grade）→ 三态（verdict/confidence）。**任一节缺上游字段 = 该 finding 不得生成，返回字段所有者补产**；8 节标题全部出现才算该详情文件合格。

## 完成硬门（写 `run_status=completed` 的充要条件）

**机械终局判定，优先于以下所有条目（真实审计教训：主代理曾向用户报告"gate-1.py: pass、审计完成"，而同一 session 目录里 gate-1.py 自己产出的 gate_record.md 明确写着 `gate_result: rework`——这是编造完成结论，不是分析质量问题）**：写 `run_status=completed` 或在任何汇报中宣称审计完成之前，**必须**执行 `python3 contracts/sdwr/session.py final-status --session {session_dir}`，其输出必须字面等于 `COMPLETED_VERIFIED`；只要不是这个值，**禁止**在报告或对用户的汇报中使用"完成""通过""pass"等措辞，禁止转述、改写、总结这个判定——报告里对完成状态的表述必须原样引用该命令的输出，不允许由主代理凭自己的理解重新组织语言。

整次 run 只有同时满足以下全部条件才可写 `run_status=completed`：

0. **gate_record 校验**：gate2_notes 非空（A2 独立验证已执行）且 gate_record 由宿主脚本生成；gate_record.md 存在且 gate[planned==terminal] 起全部方程有行、由宿主 §4c 一体块生成（判定栏禁止手写）；gate_result=pass 才可继续；任一 FAIL → rework，未收敛 → blocked + 部分报告；禁止以 pass_with_gaps 掩盖等式失败。gate_summary 已写回 run-state（非 null）且 rework_rounds 有记录。
0b. **对账块自检前置（v0.3.9）**：能力档案声明执行环境（POSIX|PowerShell）且黄金夹具自检通过标记为 true，否则本 run 判 blocked。
1. **所有适用阶段** `stage_result` 为 `completed` 或 `not_applicable`（不得缺失、悬空或为 `partial`）。
2. **gate 全部方程成立**（Gate-1 逐条核对，全部硬门）：
   1. `planned_check_points == terminal_check_points`
   2. `len(sink_inventory) == 回溯检查点覆盖的 sink 数`（每个 sink 至少被回溯一次）
   3. `len(source_inventory) == 前向检查点覆盖的 source 数`（每个 source 至少前向一次）
   4. `PROCESSED == TOTAL_SINKS`（每个 sink 有 audit 记录，证伪也留痕）
   5. `confirmed 数 == findings/{candidate_id}-*.md 数 == machine-fields 条数 == 分区表链接行数`（四相等，含 Medium/Low/Ignore，见 quality-gates.md 等式5）
   6. `failed 清单为空，或逐条列入报告"未分析清单"`
   7. `账本零残留（无未检查）`（所有账本状态无"未检查"）
3. **failed 清单已处理**：为空，或已逐条列入 report.md 未分析清单（附 file 与 reason），禁止静默。
4. 无悬空 rework（所有 Gate 返工收敛为 `pass`；合法 blocked 以部分报告呈现）、全部分片已验证、failed_wus 为空或已列入报告、`remaining_scope` 为空、关键独立复核已完成（`independence_degraded` 若为 true 已在报告披露）。
5. 最终报告存在且披露全部可完成缺口（`independence_degraded`、能力降级、incremental 跳过范围、动态执行限制）；报告中对完成状态的表述必须是 `session.py final-status` 命令的原始输出（`COMPLETED_VERIFIED`），禁止自绘对账表，禁止另写一句"gate_result=pass"了事——那句话本身不构成证据，命令的机械判定结果才是。

任一不满足时不得写 `run_status=completed`；按 work-graph 返工、阻塞或生成部分报告（部分报告 run 保持 `blocked`/`interrupted`，不得标 completed）。

## 部分报告与输入对账

### 部分报告触发条件

当任一能力 `blocked` 或 `interrupted` 时，本阶段仍基于已完成产物生成部分报告。部分报告生成后 run 保持 `blocked`/`interrupted`，不得因生成了部分报告就改为 `completed`。部分报告必须包含：未完成能力清单、未完成检查点/WU/candidate 清单、`remaining_scope`、`resume_entry`、受影响结论。

### 输入对账规则

报告必须消费并完成对账，不得遗漏：`run_status`、各 `stage_result`、Gate 结果摘要、check point 闭合摘要、WU 闭合摘要、`pass_with_gaps` 具体内容、`blocked`/`interrupted` 具体能力与原因、`independence_degraded`、能力降级标注、incremental 跳过范围、动态执行限制、剩余续跑范围（remaining_scope_refs，标明还需续跑才能全覆盖，不是可放弃的缺口）。

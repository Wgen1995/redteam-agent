# V{N}: {漏洞一句话摘要}

> 权威来源：`../../../docs/research/28-detection-engine-design.md` 第 8.1 节（findings/V{N}.md，每漏洞一份，必产出）+ `../../../docs/research/34-e2e-complete-mechanism-design.md` 第 4 节（就地落盘机制）。
> 本模板是阶段3逐漏洞详情文件的唯一结构权威。`N` 是确定性排序序号（severity 降序 → root_cause_group_id 稳定键 → 稳定键升序），不是发现顺序、不是时间戳；**`N` 只在 report.md 最终合并时才能计算并机械回填进本标题行（见 report-delivery/SKILL.md D 节），本文件本身在阶段2一确认候选就要立即产出——文件名用 `candidate_id`（阶段1起唯一、立即可用），不用 `N`，标题行允许在文件已产出后被回填更新，其余七节内容一旦写出不因回填而改变。**
> 本文件全部内容只能来自上游结构化产物（`candidates.tsv` / `verification-summary.md` 及伴生的可利用性证明、修复指导产出）的确定性投影：不得新造判断、证据、代码位置或敏感数据内容。发现不一致或缺失时返回字段所有者修正后重新投影，不手工改写本文件。
>
> ## 生产时刻映射表（每节内容在上游哪一步就落盘）
>
> 每节内容在其生产时刻已物化为上游字段，本模板只是投影渲染；缺上游字段 = 该 finding 不得生成，返回字段所有者补产。
>
> | 模板节 | 上游字段 | 生产阶段 |
> |---|---|---|
> | 一、识别信息 | candidate_id / location / created_at | 阶段1 候选创建 |
> | 二、漏洞摘要 | root_cause_summary + final_severity | 阶段2 定级 |
> | 三、调用链（±3 行代码+关键行标记） | 证据链五段（簇结论 cluster 内 source/propagation/sanitizers/sink/disproof_checked 各段含 hop_snippet） | 阶段1 深扫（簇结论落盘） |
> | 四、CVSS 评分 | cvss_vector + cvss_breakdown | 阶段2 定级 |
> | 五、详细分析（触发步骤/影响/利用/修复/安全措施表） | 证据链五段（触发步骤；簇结论 cluster 内 source/propagation/sanitizers/sink/disproof_checked）+ impact_description + exploit_scenario + remediation + control_assessment（location/有效性） | 阶段1（触发步骤）+ 阶段2（其余） |
> | 六、数据流语义变迁表 | semantic_transitions | 阶段1 深扫（簇结论落盘） |
> | 七、证据分级标注 | evidence_grade（随写随标） | 阶段1/2 |
> | 八、三态结论+confidence | verdict + confidence | 阶段2 |

---

## 一、识别信息

| 字段 | 值 |
|------|-----|
| finding_id | {finding_id}（= candidate_id，沿用阶段1确定性 ID `C-{sink_seq}-{source_seq}-{sig8}`，不新生成） |
| root_cause_group_id | {root_cause_group_id} |
| 对象定位 | {file}:{line}（start_line–end_line） |
| 创建时间 | {created_at} |
| 最近更新 | {updated_at} |

> finding_id 与 candidate_id 恒等；仅当 #9 生命周期台账已存在等值 `finding_id` 别名时才只读显示该别名，报告层不生成也不写 finding_id。

## 二、漏洞摘要

{一句话描述：什么缺陷、在什么条件下、通过什么路径、造成什么影响}。

- 严重度：{severity}，取值 `Critical` / `High` / `Medium` / `Low` / `Ignore`。
- `informational` 与 `ignore` 不进入本模板：`informational` 是 code-hygiene item（非 finding，单列于 report.md）；`ignore` 是有活路径的政策忽略 finding（仍生成详情文件并进入 #9 显式处置，但非优先修复项）。

## 三、调用链（source → propagation → sink）

> **每个节点必须包含上下文源码片段（前后至少 3 行）+ 关键行标记，严禁只写一行摘要。** 读者要能仅凭本段看懂：变量从哪来、怎么被变换、怎么被使用、流向哪里、为什么构成漏洞。
>
> 代码片段允许从 `evidence_refs` 指向源码按固定前后 3 行窗口重读渲染，不视为新造证据；其余内容仍须来自上游结构化产物的确定性投影。

逐节点格式（节点角色取值引用 `../../enum-registry.md` 的 `evidence_role`：`user_input` / `entrypoint` / `propagation` / `root_control` / `sink` / `outcome` / `expected_control`）：

    [节点角色] — {file}:{line} — {角色描述}
    {行号}: {上下文代码 -3 行}
    {行号}: {上下文代码 -2 行}
    {行号}: {上下文代码 -1 行}
    {行号}: >>> {关键代码行} <<<  ← 关键行
    {行号}: {上下文代码 +1 行}
    {行号}: {上下文代码 +2 行}
    {行号}: {上下文代码 +3 行}

- 同一文件内连续的 source→propagation→sink 可合并展示更大上下文，但仍须逐节点给出角色标签与关键行标记。
- 每个节点下方用一句话说明该节点在数据流中的角色与去向。

跨文件 / 跨 WU 的路径用 `cross_boundary_path` 逐跳列出，不得合并省略：

| 跳 | 从 file:line | 到 file:line | 边界类型（boundary_edge_kind） | 说明 |
|----|------------|------------|-------------------------------|------|
| 1 | {from} | {to} | {direct_call / storage_edge / transport_edge / ...} | {说明} |

## 四、CVSS 3.1 评分

| 项目 | 值 | 说明 |
|------|-----|------|
| 分数 | {score}/10 | 由 `cvss_vector` 导出，不在报告层独立重评分 |
| 向量 | CVSS:3.1/{vector} | 与阶段2同一批事实映射 |
| 攻击向量(AV) | {AV} | {AV 中文解释：网络/相邻/本地/物理及判定依据} |
| 攻击复杂度(AC) | {AC} | {AC 中文解释} |
| 权限要求(PR) | {PR} | {PR 中文解释} |
| 用户交互(UI) | {UI} | {UI 中文解释} |
| 范围(S) | {S} | {S 中文解释} |
| 机密性影响(C) | {C} | {C 中文解释} |
| 完整性影响(I) | {I} | {I 中文解释} |
| 可用性影响(A) | {A} | {A 中文解释} |

> 八分量逐项中文解释必须与阶段2 `verification_baseline` / `impact_rating` / `likelihood_rating` 已确定事实一致，不得为了凑分数编造分量依据。

## 五、详细分析

### 5.1 漏洞说明

- 问题代码：{file}:{line}

    {行号}: {问题代码上下文 -3 行}
    {行号}: {问题代码上下文 -2 行}
    {行号}: {问题代码上下文 -1 行}
    {行号}: >>> {问题代码关键行} <<<
    {行号}: {问题代码上下文 +1 行}
    {行号}: {问题代码上下文 +2 行}
    {行号}: {问题代码上下文 +3 行}

- 触发流程（编号）：
    1. {触发步骤1}
    2. {触发步骤2}
    3. {触发步骤3}

- 漏洞影响：{impact_description}

### 5.2 利用方式

{具体例子：攻击者可控输入 → 逐跳传播 → 到达 sink → 产生安全后果，可用一段具体 payload/请求示意，但不得复制真实敏感数据}

### 5.3 修复建议

{fix_suggestion 一句话 + 修复思路}

    {修复后代码示例（缩进代码块）}

### 5.4 安全措施分析

| 序号 | 安全措施 | 代码位置 | 有效性 | 说明 |
|------|---------|---------|--------|------|
| {n} | {已有防护/Guard/Policy/Sanitizer/Encoder} | {file}:{line} | {effective / ineffective / absent / not_applicable} | {解释} |

> 四类控制（Guard / Policy Decision / Sanitizer / Encoder）分别评估，不合并为笼统"安全控制"。

## 六、数据流语义变迁表

| 步骤 | 位置 | 变量 | 语义 | 状态 | 原因 |
|------|------|------|------|------|------|
| {step} | {file}:{line} | {var} | {值语义} | {明文/密文/未校验/已清洗/...} | {变化原因} |

## 七、证据分级标注

每个关键判断必须标注证据级别：`direct`（直接证据，读到代码原文 file:line+片段）/ `indirect`（间接推断，命名/上下文/框架惯例）/ `unknown`（信息缺失）。`unconfirmed` 结论必须写明缺口位置与所需证据。

| 关键判断 | 证据级别 | 依据 / 证据引用 | 缺口位置与所需证据 |
|---------|---------|----------------|--------------------|
| {判断1（如 source 可控）} | {direct / indirect / unknown} | {evidence_ref} | {unconfirmed 时必填；否则 —} |
| {判断2（如 路径可达）} | {direct / indirect / unknown} | {evidence_ref} | {同上} |
| {判断3（如 防护失效）} | {direct / indirect / unknown} | {evidence_ref} | {同上} |

> 结论强度不得超过证据链最弱一环：confirmed 需全要素直接证据（或大部直接+其余强间接且无反证，注明最弱环）；仅间接"应该安全"不得定 refuted。

## 八、三态结论

| 字段 | 值 |
|------|-----|
| verification_verdict | {confirmed / refuted / unconfirmed} |
| confidence_score | {value}/10（threshold={threshold}，threshold_passed={true/false}） |
| confidence 依据 | {rationale} |
| 结论陈述 | {一句最终结论：本实例是什么漏洞、是否确认、最弱证据环在哪} |

> 本模板生成的 `findings/V{N}.md` 只对应 `verification_verdict=confirmed` 的 finding（confirmed + 活攻击面 + 非 informational）。`unconfirmed` 与 `refuted` 仍是 candidate，不生成详情文件，只进入 report.md 的"待确认"区或覆盖度章节；若出现 `verdict=unconfirmed` 的详情记录，必须显式标注为"非 finding"并写清缺口。

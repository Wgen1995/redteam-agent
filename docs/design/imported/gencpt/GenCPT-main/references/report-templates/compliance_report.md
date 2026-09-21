# 合规报告

> 生成时间：{{generated_at}}
> 目标环境：{{server}}
> 执行模式：{{mode}}（A=仅合规 / B=合规+攻击 / C=完整渗透）
> 检测范围：{{scope}}
> 审批模式：{{approval}}

---

## 1. 合规概览

| 平台 | 总规则数 | Pass | Fail | Warn | N/A |
|------|---------|------|------|------|-----|
| Kubernetes | {{k8s_total}} | {{k8s_pass}} | {{k8s_fail}} | {{k8s_warn}} | {{k8s_na}} |
| Docker | {{docker_total}} | {{docker_pass}} | {{docker_fail}} | {{docker_warn}} | {{docker_na}} |
| containerd | {{containerd_total}} | {{containerd_pass}} | {{containerd_fail}} | {{containerd_warn}} | {{containerd_na}} |
| **合计** | **{{total_rules}}** | **{{total_pass}}** | **{{total_fail}}** | **{{total_warn}}** | **{{total_na}}** |

---

## 2. 按 CIS 分组详细结果

{{#each platform_groups}}

### 2.{{platform_index}} {{platform_name}} — {{group_id}} {{group_title}}

| 编号 | 规则描述 | 判定 | 依据摘要 | 修复建议 |
|------|---------|------|---------|---------|
{{#each rules}}
| {{rule_id}} | {{rule_description}} | {{verdict}} | {{evidence_summary}} | {{remediation}} |
{{/each}}

统计：Pass {{group_pass}} / Fail {{group_fail}} / Warn {{group_warn}} / N/A {{group_na}}

{{/each}}

---

## 3. 合规检查点报告

> 本节在 Phase 2 完成后独立输出，不含攻击关联。

| 平台 | 分组 | 检查点状态 | 通过率 | Critical Fail 数量 |
|------|------|-----------|-------|-------------------|
| {{platform}} | {{group}} | {{checkpoint_status}} | {{pass_rate}}% | {{critical_fail_count}} |

### 3.1 三重校验结果

| 校验层 | 检查项 | 结果 |
|--------|-------|------|
| 第一重：规则覆盖 | 总规则数 = 预期数 | {{rule_count_match}} |
| 第一重：规则覆盖 | 每条规则有判定结果 | {{all_rules_judged}} |
| 第一重：规则覆盖 | fail/warn 有判定依据 | {{all_evidence_present}} |
| 第二重：结构完整性 | knowledge_graph 边可找到对应节点 | {{edges_valid}} |
| 第二重：结构完整性 | 五态标记无 `[ ]` 残留 | {{no_empty_marks}} |
| 第三重：检查点报告 | 每条规则有判定 | {{all_rules_in_report}} |
| 第三重：检查点报告 | 总计数字一致 | {{totals_consistent}} |
| 第三重：检查点报告 | 无占位符残留 | {{no_placeholders}} |

---

## 4. 高风险项汇总

> 以下为合规结果中判定为 Fail 且严重性为 High 或 Critical 的条目，含攻击面关联。

| 编号 | 规则描述 | 严重性 | 判定 | 关联攻击面 | 关联攻击模式 | 合规假设族 |
|------|---------|--------|------|-----------|-------------|-----------|
{{#each high_risk_items}}
| {{rule_id}} | {{rule_description}} | {{severity}} | FAIL | {{attack_surface}} | {{attack_pattern}} | {{hypothesis_family}} |
{{/each}}

### 4.1 风险叠加项

> 同一目标存在 ≥3 种违规叠加时列入此节，风险放大。

| 目标 | 违规数量 | 叠加的规则编号 | 风险评估 |
|------|---------|--------------|---------|
{{#each risk_amplification_items}}
| {{target}} | {{violation_count}} | {{rule_ids}} | {{risk_assessment}} |
{{/each}}

---

## 5. Baseline 对比（如有）

> 仅当指定 `--baseline` 参数时生成此节。

| 平台 | 组 | 上次结果 | 本次结果 | 变化 |
|------|-----|---------|---------|------|
{{#each delta_items}}
| {{platform}} | {{group}} | {{baseline_verdict}} | {{current_verdict}} | {{change}} |
{{/each}}

---

*报告结束*
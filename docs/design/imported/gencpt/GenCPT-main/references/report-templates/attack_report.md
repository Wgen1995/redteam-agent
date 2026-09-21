# 攻击验证报告

> 生成时间：{{generated_at}}
> 目标环境：{{server}}
> 执行模式：{{mode}}
> 检测范围：{{scope}}
> 审批模式：{{approval}}

---

## 1. ATK-CAND 汇总表

| 编号 | 来源 | 攻击面 | 攻击模式 | 可信度 | 状态 | 执行上下文 |
|------|------|--------|---------|--------|------|-----------|
{{#each atk_candidates}}
| {{atk_cand_id}} | {{source_icon}} {{source_label}} | {{attack_surface}} | {{attack_pattern}} | {{confidence}} | {{status_icon}} {{status_label}} | {{execution_context}} |
{{/each}}

> 来源标识：📚 已知模式库 / 🧠 LLM 推理 / 🔄 学习模式
>
> 可信度：C1 实证复现 / C2 条件实证 / C3 风险线索
>
> 状态：✅✅ 已确认-可复现 / ✅ 已确认-条件成立 / ⚠️ 高风险线索 / ➖ 不可利用 / 🛑 已阻断

---

## 2. ATK-CAND 详细结果

{{#each atk_candidates}}

### 2.{{index}} {{atk_cand_id}} — {{attack_pattern}}

| 字段 | 值 |
|------|-----|
| 编号 | {{atk_cand_id}} |
| 来源 | {{source_icon}} {{source_label}} |
| 攻击面 | {{attack_surface}} |
| 可信度 | {{confidence}} |
| 状态 | {{status_icon}} {{status_label}} |
| 审批级别 | {{approval_level}} |
| 审批状态 | {{approval_status}} |
| 执行上下文最高层级 | {{max_execution_context}} |
| 破坏性 | {{destructive}} |

#### 2.{{index}}.1 前置条件验证

| 前置条件 | 执行上下文 | 验证命令 | 实际输出 | 是否满足 |
|---------|-----------|---------|---------|---------|
{{#each prerequisites}}
| {{description}} | {{context}} | `{{command}}` | {{output}} | {{satisfied}} |
{{/each}}

#### 2.{{index}}.2 探测命令

| 步骤 | 执行上下文 | 命令 | 期望输出 | 实际输出 | 判定 |
|------|-----------|------|---------|---------|------|
{{#each probe_steps}}
| {{step}} | [{{context}}] | `{{command}}` | {{expected}} | {{actual}} | {{judgment}} |
{{/each}}

#### 2.{{index}}.3 攻击验证（如有）

| 步骤 | 执行上下文 | 命令 | 期望影响 | 实际影响 | 判定 |
|------|-----------|------|---------|---------|------|
{{#each attack_steps}}
| {{step}} | [{{context}}] | `{{command}}` | {{expected}} | {{actual}} | {{judgment}} |
{{/each}}

#### 2.{{index}}.4 差分证明

| 对比项 | 攻击前 [L{{before_context}}] | 攻击后 [L{{after_context}}] | 证明结论 |
|--------|---------------------------|--------------------------|---------|
{{#each diff_proofs}}
| {{item}} | {{before_state}} | {{after_state}} | {{conclusion}} |
{{/each}}

#### 2.{{index}}.5 审批与降级记录

| 审批级别 | 操作类型 | 审批结果 | 降级情况 | 备注 |
|---------|---------|---------|---------|------|
{{#each approval_records}}
| {{level}} | {{operation_type}} | {{result}} | {{downgrade}} | {{note}} |
{{/each}}

{{/each}}

---

## 3. 攻击链分析

{{#each attack_chains}}

### 3.{{chain_index}} {{chain_id}} — {{chain_description}}

| 字段 | 值 |
|------|-----|
| 链编号 | {{chain_id}} |
| 描述 | {{chain_description}} |
| 置信度 | {{confidence}} |
| 状态 | {{chain_status}} |
| 影响评估 | {{impact}} |

#### 链步骤

| 步骤 | ATK-CAND | 来源 | 状态 | 可信度 |
|------|---------|------|------|--------|
{{#each steps}}
| {{step}} | {{atk_cand_id}} | {{source}} | {{status}} | {{confidence}} |
{{/each}}

{{/each}}

---

## 4. POC 包引用

> 本节引用 `poc_scripts/` 目录中生成的 POC 脚本。

| ATK-CAND | POC 脚本路径 | 可信度 | 验证层级 |
|----------|------------|--------|---------|
{{#each poc_references}}
| {{atk_cand_id}} | `poc_scripts/{{script_path}}` | {{confidence}} | {{verification_level}} |
{{/each}}

POC 包目录结构：

```
poc_scripts/
{{#each poc_scripts}}
├── {{filename}}
{{/each}}
```

---

## 5. 不可利用项

> 以下攻击模式已检查，前置条件不满足，证伪依据充分。

| ATK-CAND | 攻击模式 | 来源 | 证伪依据 | 证伪执行上下文 |
|----------|---------|------|---------|--------------|
{{#each not_exploitable_items}}
| {{atk_cand_id}} | {{attack_pattern}} | {{source_icon}} {{source_label}} | {{falsification_evidence}} | [{{context}}] |
{{/each}}

---

## 6. 已阻断项

> 以下攻击模式的前置条件满足，但被安全机制阻断。

| ATK-CAND | 攻击模式 | 来源 | 阻断机制 | 阻断证据 | 阻断执行上下文 | 可信度 |
|----------|---------|------|---------|---------|--------------|--------|
{{#each blocked_items}}
| {{atk_cand_id}} | {{attack_pattern}} | {{source_icon}} {{source_label}} | {{block_mechanism}} | {{block_evidence}} | [{{context}}] | {{confidence}} |
{{/each}}

---

## 7. 漏洞来源统计

| 来源 | 数量 | 占比 |
|------|------|------|
| 📚 已知模式库 (pattern_library) | {{pattern_library_count}} | {{pattern_library_pct}}% |
| 🧠 LLM 推理 (llm_reasoning) | {{llm_reasoning_count}} | {{llm_reasoning_pct}}% |
| 🔄 学习模式 (learned) | {{learned_count}} | {{learned_pct}}% |
| **合计** | **{{total_count}}** | **100%** |

---

*报告结束*
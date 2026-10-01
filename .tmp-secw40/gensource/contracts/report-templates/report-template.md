# {项目名} 安全审计报告（GenSource 检测引擎 v2）

> 权威来源（框架/历史依据，v0.11.1 U-A1 标注）：`../../../docs/research/28-detection-engine-design.md` 第 8.2 节（report.md 汇总索引，不复制详情；机制权威=doc-36/63）。
> 本文件只做索引与对账，**不复制** `findings/V{N}.md` 中的证据链、代码上下文、CVSS 逐项解释等大段内容；每条 finding 只写编号 / 摘要 / 对象定位 / 详情链接。
> 全部内容来自上游结构化产物的确定性投影，不重新判断真实性 / 严重度 / 复现 / 修复。

---

## 一、检测概况

| 字段 | 值 |
|------|-----|
| 扫描范围 | {project_path / authorized_scope} |
| 文件总数 | {total_files}（= `file_inventory.tsv` 行数，动态 `wc -l` 推导，不硬编码） |
| 深扫数 | {deep_scan_count} |
| 预筛排除数 | {prefilter_excluded_count}（附排除规则名：{rule_name 列表，如 无执行面文件 / 无危险 API / 生成产物}） |
| 未分析清单 | 必须为空；否则逐条列出（引用 `failed_wus.txt`，附 file 与 reason） |
| L1 闭合数 | {l1_closed_count} |
| L2 闭合数 | {l2_closed_count} |
| blocked 列表 | {blocked_list}（逐条列出；禁止写成无漏洞） |
| 未确认列表 | {unconfirmed_list} |
| 检测时间 | {scan_time}（复用 `run-state.md` 的 `updated_at`，不另计时） |
| revision | {source_revision}（git commit 或非 git 快照描述） |
| run_fingerprint | {run_fingerprint} |
| 模型宿主角标 | {model_host_label} |

> 对账要求：文件总数 = 深扫数 + 预筛排除数 + 未分析数；`未分析清单` 必须空，否则每条都须列出，不得静默。

## 二、违规汇总（按严重度计数）

| 严重度 | 数量 |
|--------|------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| Ignore（政策忽略 finding） | {n} |
| 待确认（unconfirmed candidate） | {n} |
| Informational（code-hygiene item，非 finding） | {n} |

> `待确认` 区是 unconfirmed candidate（不是 finding）；`Informational` 是 code-hygiene item（不是 finding），单列不并入 finding 计数。

## 三、按模块分布

| 模块 | Critical | High | Medium | Low | Ignore | 待确认 | Informational |
|------|----------|------|--------|-----|--------|--------|---------------|
| {module} | {n} | {n} | {n} | {n} | {n} | {n} | {n} |

## 四、分级分区表

> 编号 `V{N}` 是本节的展示排名（severity 降序 → root_cause_group_id → 稳定键），只在 report.md 生成时才能计算，与详情文件的文件名无关。**详情文件的文件身份是 `candidate_id`**（阶段2 一确认立即产出，不等 report.md 生成——见 report-delivery/SKILL.md Part 1/Part 2 拆分），文件名 = `{candidate_id}-{severity小写}-{sink_type}-{文件基名}-{起始行}.md`；本表"详情"列链接到这个真实文件名，`V{N}` 只出现在编号列和详情文件内部的标题行，不是文件名的一部分。同一根因组内独立实例逐条列出，不合并省略。

### Critical

| 编号 | 摘要 | 对象定位 | 详情 |
|------|------|---------|------|
| V{N} | {一句话摘要} | {file}:{line} | [查看](findings/{candidate_id}-{severity}-{sink_type}-{文件基名}-{起始行}.md) |

### High

| 编号 | 摘要 | 对象定位 | 详情 |
|------|------|---------|------|
| V{N} | {一句话摘要} | {file}:{line} | [查看](findings/{candidate_id}-{severity}-{sink_type}-{文件基名}-{起始行}.md) |

### Medium

| 编号 | 摘要 | 对象定位 | 详情 |
|------|------|---------|------|
| V{N} | {一句话摘要} | {file}:{line} | [查看](findings/{candidate_id}-{severity}-{sink_type}-{文件基名}-{起始行}.md) |

### Low

| 编号 | 摘要 | 对象定位 | 详情 |
|------|------|---------|------|
| V{N} | {一句话摘要} | {file}:{line} | [查看](findings/{candidate_id}-{severity}-{sink_type}-{文件基名}-{起始行}.md) |

### Ignore（政策忽略 finding，进入 #9 显式处置，非优先修复项）

| 编号 | 摘要 | 对象定位 | 详情 |
|------|------|---------|------|
| V{N} | {一句话摘要} | {file}:{line} | [查看](findings/{candidate_id}-{severity}-{sink_type}-{文件基名}-{起始行}.md) |

### 待确认（unconfirmed candidate，非 finding）

| candidate_id | 摘要 | 对象定位 |
|--------------|------|---------|
| {candidate_id} | {一句话摘要} | {file}:{line} |

### Informational（code-hygiene item，非 finding）

| candidate_id | 摘要 | 对象定位 |
|--------------|------|---------|
| {candidate_id} | {一句话摘要 + 清理建议} | {file}:{line} |

## 五、覆盖度章节（Reviewed Surfaces）

| Surface | RiskArea | Outcome | Notes |
|---------|----------|---------|-------|
| {surface} | {risk_area} | {Outcome} | {判定依据引用} |

- `Outcome` 取值（枚举，与 `../../contracts/enum-registry.md` 报告覆盖结果一一映射）：`Reported` / `No issue found` / `Rejected` / `Not applicable` / `Needs follow-up`。
- 聚合优先级固定：`reported > needs_follow_up > rejected > not_applicable > no_issue_found`；组内任一 candidate 为 confirmed 即 `Reported`；存在 unconfirmed 或覆盖缺口即 `Needs follow-up`；存在 refuted 即 `Rejected`；无真实候选且威胁语境明确不适用才 `Not applicable`；无候选且完整扫描才 `No issue found`。
- 零命中但目标代码库不完整/缺失被引用文件时，默认判 `Needs follow-up`，不判 `No issue found`。

### 缺口披露

{逐条列出：未完成能力 / 未完成检查点或 candidate / remaining_scope / resume_entry / pass_with_gaps 具体内容 / independence_degraded / 能力降级 / incremental 跳过范围 / 动态执行限制 / 剩余续跑范围（remaining_scope_refs，标明还需续跑才能全覆盖）}

## 六、稳定性声明

{stability_check 结果}：
- `stability_check=false`：本次未启用稳定性自检，不作稳定性声明。
- `stability_check=true` 且双跑 diff 为空：机器字段（ID/文件:行/sink类型/严重度/根因组/三态）一致，`run_fingerprint` 一致，判定为稳定。
- `stability_check=true` 且差异非空：判定为不稳定，引用 `stability-diff.md` 逐条列出差异字段与根因归类（ID/判定/严重度/根因组），并将稳定性问题作为一等缺陷反馈知识演进，不允许静默。

## 七、危害最小化声明

{声明：本报告未复制可利用性证明过程中取得的真实敏感数据内容，只描述"证明了能访问到 X 类型 / X 条记录"这类效果性陈述。}

# 质量检查模板

本文档定义每个 Phase 完成后的结构性校验清单模板和 Phase Checkpoint 门控表。

---

## 1. Phase 结构性校验清单

### Phase 1a — 环境侦察（recon）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `knowledge_graph/nodes/hosts.json` | 含至少 1 个主机节点 |
| 2 | `knowledge_graph/nodes/pods.json` | scope 含 k8s 时非空，含 Pod 元数据 |
| 3 | `knowledge_graph/nodes/containers.json` | scope 含 docker/containerd 时非空 |
| 4 | `knowledge_graph/nodes/service_accounts.json` | scope 含 k8s 时非空 |
| 5 | `knowledge_graph/nodes/secrets.json` | scope 含 k8s 时非空（名称+类型，不含内容） |
| 6 | `knowledge_graph/nodes/findings.json` | 可初始为空（后续 Phase 填充） |
| 7 | `knowledge_graph/edges/infra.json` | 含至少 1 条基础设施边（mount/capability/network） |
| 8 | `evidence/recon/recon_summary.md` | 含环境指纹、节点数、Pod 数、关键安全上下文摘要 |
| 9 | `evidence/recon/raw/` | 含原始 SSH 输出文件 |
| 10 | `session_config.json` | 含 server、mode、scope、env_fingerprint |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 主机清单非空 | `hosts.json` 含 ≥1 个节点，每个节点有 id、node_type、data |
| 2 | 容器/Pod/SA 清单非空 | 对应 scope 的 JSON 文件节点数 > 0 |
| 3 | 安全上下文提取完成 | infra.json 中至少有 1 条 capability/mount/network 边 |
| 4 | 环境指纹已生成 | session_config.json 含 env_fingerprint（os_type, arch, kernel_version） |
| 5 | SSH 原始输出已写盘 | evidence/recon/raw/ 目录下有文件 |
| 6 | 所有节点 ID 唯一 | JSON 文件中 id 字段无重复 |
| 7 | 五态标记无 `[ ]` 残留 | 当前 Phase 不涉及五态，跳过此校验 |

---

### Phase 1b — 源码扫描（recon-source）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `knowledge_graph/nodes/source_findings.json` | 含源码安全发现节点 |
| 2 | `knowledge_graph/edges/source_edges.json` | 含源码-运行时关联边 |
| 3 | `evidence/recon/source_analysis.md` | 含结构化摘要（每个发现 5-10 行） |
| 4 | `evidence/recon/source_scan_stats.md` | 含文件数统计、扫描级别、发现数统计 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 源码发现非空（有源码时） | source_findings.json 含 ≥1 个发现节点 |
| 2 | 扫描产物总大小 ≤8000 tokens | source_analysis.md 大小在限制内 |
| 3 | source_scan_stats.md 含完整统计 | 含 scanned_files、high_value_files、findings_count |
| 4 | 边引用的节点存在 | source_edges.json 中 from_node/to_node 在对应 nodes 文件中存在 |

---

### Phase 2a — K8s 合规检测（k8s-compliance）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/compliance/k8s/results.json` | 含 134 条规则判定 |
| 2 | `evidence/compliance/k8s/summary.md` | 含 pass/fail/warn/na 统计 |
| 3 | `knowledge_graph/nodes/findings.json` | 追加 k8s 合规违规节点 |
| 4 | `knowledge_graph/edges/compliance.json` | 追加 k8s 合规边 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 规则总数 = 134 | results.json 中规则数量 = 134 |
| 2 | 每条规则有判定结果 | 无 `[ ]` 未检查状态，必须是 pass/fail/warn/na 之一 |
| 3 | 每条 fail/warn 规则有判定依据 | results.json 中 fail/warn 条目含 evidence 字段（SSH 命令输出 + LLM 判定理由） |
| 4 | 五态标记无 `[ ]` 残留 | 所有规则判定不含 `[ ]` |
| 5 | 合规边完整 | compliance.json 中每条 fail 规则能找到对应 findings 节点 |
| 6 | COMP-CAND 编号连续 | 违规候选编号连续无遗漏 |

---

### Phase 2b — Docker 合规检测（docker-compliance）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/compliance/docker/results.json` | 含 64 条规则判定 |
| 2 | `evidence/compliance/docker/summary.md` | 含 pass/fail/warn/na 统计 |
| 3 | `knowledge_graph/nodes/findings.json` | 追加 docker 合规违规节点 |
| 4 | `knowledge_graph/edges/compliance.json` | 追加 docker 合规边 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 规则总数 = 64 | results.json 中规则数量 = 64 |
| 2 | 每条规则有判定结果 | 无 `[ ]` 未检查 |
| 3 | 每条 fail/warn 规则有判定依据 | evidence 字段非空 |
| 4 | 五态标记无 `[ ]` 残留 | 所有判定不含 `[ ]` |
| 5 | 合规边完整 | compliance.json 中 docker fail 规则有对应 findings |

---

### Phase 2c —容器合规检测（containerd-compliance）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/compliance/containerd/results.json` | 含 28 条规则判定 |
| 2 | `evidence/compliance/containerd/summary.md` | 含 pass/fail/warn/na 统计 |
| 3 | `knowledge_graph/nodes/findings.json` | 追加 containerd 合规违规节点 |
| 4 | `knowledge_graph/edges/compliance.json` | 追加 containerd 合规边 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 规则总数 = 28 | results.json 中规则数量 = 28 |
| 2 | 每条规则有判定结果 | 无 `[ ]` 未检查 |
| 3 | 每条 fail/warn 规则有判定依据 | evidence 字段非空 |
| 4 | 五态标记无 `[ ]` 残留 | 所有判定不含 `[ ]` |
| 5 | 合规边完整 | compliance.json 中 containerd fail 规则有对应 findings |

---

### Phase 3 — 交叉关联（cross-ref）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `knowledge_graph/edges/cross_ref.json` | 含交叉关联边 |
| 2 | `evidence/cross-ref/cross_ref_summary.md` | 含核心查询结果摘要 |
| 3 | `evidence/cross-ref/risk_amplification.md` | 含风险放大分析 |
| 4 | `evidence/cross-ref/prerequisite_signals.md` | 含前置条件信号分析 |
| 5 | `evidence/cross-ref/history_priority.md` | 含历史优先级分析 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 交叉关联边非空 | cross_ref.json 含 ≥1 条边 |
| 2 | 高关联度发现 ≥1 | risk_amplification.md 含至少 1 个高关联度发现 |
| 3 | 三库映射一致 | compliance-hypotheses、attack-hypotheses、cross-ref-queries 的映射无矛盾 |
| 4 | 边引用节点存在 | cross_ref.json 中 from_node/to_node 在对应 nodes 文件中存在 |
| 5 | 三个核心查询已完成 | XREF-001/002/003 结果在 cross_ref_summary.md 中有记录 |

---

### Phase 4a — 攻击模式匹配验证（attack-pattern）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/attack/pattern-hits.md` | 含命中模式列表及验证结果 |
| 2 | `evidence/attack/unmatched_signals.md` | 含未匹配信号列表 |
| 3 | `knowledge_graph/edges/attack.json` | 含攻击验证边 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | ATK-CAND 列表非空（有合规违规时） | 有合规违规时至少 1 个 ATK-CAND |
| 2 | 每个 ATK-CAND 有证据矩阵 | 每个候选含至少 L0 或 L1 执行上下文证据 |
| 3 | ATK-CAND 编号连续无遗漏 | 从 ATK-CAND-001 开始连续编号 |
| 4 | 候选闭环 | 每个候选有 confirmed/high_risk_clue/condition_met/blocked/falsified 状态 |
| 5 | 五态标记无 `[ ]` 残留 | 所有攻击面检查标记不为 `[ ]` |
| 6 | 来源标识正确 | 每个候选标注来源：pattern_library/llm_reasoning/learned |

---

### Phase 4b — LLM 推理攻击（attack-reasoning）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/attack/reasoning-hits.md` | 含 LLM 推理发现列表 |
| 2 | `evidence/attack/insights.md` | 含推理洞察摘要 |
| 3 | `knowledge_graph/edges/attack.json` | 追加 LLM 推理攻击边 |
| 4 | `knowledge_graph/episodic_memory/recommendations.md` | 含晋升候选建议 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 推理发现非空（有未匹配信号时） | 有 `[?]` 候选时至少 1 条推理发现 |
| 2 | 每个推理发现标注 LLM 推理来源 | source 标记为 `llm_reasoning` |
| 3 | 攻击边引用节点存在 | attack.json 中新增边的 from_node/to_node 存在 |
| 4 | 推理命令基于当前环境 | 不准凭记忆出攻击命令，所有命令基于当次侦察结果构造 |

---

### Phase 5 — 攻击链构建（chain-builder）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/chains/chain_builder.md` | 含攻击链描述 |
| 2 | `knowledge_graph/edges/cross_ref.json` | 追加 attack_chain 边 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 攻击链边非空 | 有至少 1 条 CHAIN 边 |
| 2 | 每条链有置信度评分 | 每条链含 confidence 0-1 的数值 |
| 3 | 链与候选映射一致 | 链中每个 step 引用的 ATK-CAND 存在于 Phase 4 产出中 |
| 4 | 链编号连续 | CHAIN-001, CHAIN-002, ... 无跳跃 |

---

### Phase 6 — 链式验证（chain-verify）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/chains/chain_verification.md` | 含验证结果和审批记录 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 验证结果已写入 | 每条链有 verified/blocked/partial 结果 |
| 2 | 审批门控执行完毕 | L3+ 操作有审批记录 |
| 3 | 被阻断链有重新规划 | blocked 链有绕过策略或降级说明 |
| 4 | 破坏性操作标注 | 破坏性操作标记为 L3 条件验证，未实际执行 |

---

### Phase 7 — POC 生成（poc-generator）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `evidence/poc/poc_scripts/` | 含 POC 脚本文件 |
| 2 | `evidence/poc/poc_readme.md` | 含 POC 使用说明 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | POC 脚本已生成 | 每个 confirmed/condition_met 漏洞有对应 POC |
| 2 | 每个 POC 有 README | poc_readme.md 含每个 POC 的前置条件、执行步骤、清理步骤 |
| 3 | POC 可执行性自检 | POC 命令不含占位符（无 【xxx】），均为实际可执行命令 |
| 4 | 安全边界合规 | POC 不含破坏性命令、不含持久化内容、不含横向移动步骤 |
| 5 | 清理步骤完备 | 每个 POC 含清理/恢复命令 |

---

### Phase 8 — 报告生成（report-compliance / report-attack / report-summary）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `reports/compliance_report.md` | 含完整合规检查结果 |
| 2 | `reports/compliance_report.json` | 含合规检查结构化数据 |
| 3 | `reports/attack_report.md` | 含攻击验证结果 |
| 4 | `reports/attack_report.json` | 含攻击验证结构化数据 |
| 5 | `reports/pentest_report.md` | 含综合渗透报告 |
| 6 | `reports/pentest_report.json` | 含综合渗透结构化数据 |
| 7 | `reports/coverage_report.md` | 含全景覆盖报告 |
| 8 | `evidence/qa/qa_summary_report.md` | 含 QA 语义抽检报告 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 所有报告 MD + JSON 生成 | 8 个文件均存在且非空 |
| 2 | 报告校验通过 | 每条规则有判定、fail/warn 有判定依据、总计数字 = pass+fail+warn+na |
| 3 | 无占位符残留 | 报告中无 【xxx】 占位符 |
| 4 | 五态标记无 `[ ]` 残留 | 所有检查项有明确判定 |
| 5 | QA 语义抽检完成 | qa_summary_report.md 含置信度评分 |
| 6 | QA-OVERRIDE 数量 ≤3 | 回溯验证 override 超过 3 条标注为低置信 |

---

### Phase 9 — 攻击模式进化（evolve，可选）

**MUST 输出文件**：

| # | 文件路径 | 非空要求 |
|---|---------|---------|
| 1 | `attack-patterns/新增 SKILL.md`（如有晋升） | 新晋升模式文件 |
| 2 | `attack-patterns/_index.md`（更新） | hit_count 和 last_hit 已更新 |
| 3 | `evidence/evolve/evolve_report.md` | 含进化报告 |

**校验项**：

| # | 校验项 | 通过标准 |
|---|-------|---------|
| 1 | 晋升门槛校验通过 | 每个晋升模式满足 4 项门槛 |
| 2 | 新模式符合 8 段格式 | 每个新 SKILL.md 包含 8 个章节 |
| 3 | 三库一致性维护完成 | attack-hypotheses.md 已更新 |
| 4 | 自净规则执行 | 降级/归档/更新 hit_count 规则已执行 |

---

## 2. Phase Checkpoint 门控表

每个 Phase 完成后必须通过以下所有检查点才能进入下一个 Phase。任何一项不通过则回退到当前 Phase 补充。

### 门控规则

1. 所有 MUST 输出文件存在且非空
2. 对应 Phase 的结构校验项全部通过
3. 知识图谱边的 from_node/to_node 能找到对应节点
4. 五态标记无 `[ ]` 残留（Phase 2+ 适用）

### 门控表

| Phase | 检查点 ① | 检查点 ② | 检查点 ③ | 检查点 ④ |
|-------|----------|----------|----------|----------|
| **Phase 1** | 主机/容器/Pod/SA 清单非空 | 环境指纹识别完成 | 源码扫描结果（如有 source-path） | QA 结构校验通过 |
| **Phase 2** | scope 内所有平台规则全景判定完成 | 合规假设映射 edges 生成 | 每条规则有判定依据 | QA 结构校验通过 |
| **Phase 3** | 交叉关联 edges 非空 | 高关联度发现 ≥1 | 三库映射一致 | QA 结构校验通过 |
| **Phase 4** | ATK-CAND 列表非空（有合规违规时） | 每个候选有证据矩阵 | 候选闭环（confirmed/降级/放弃） | QA 结构校验通过 |
| **Phase 5** | 攻击链 edges 非空 | 每条链有置信度评分 | 链与候选映射一致 | QA 结构校验通过 |
| **Phase 6** | 验证结果写入 | 审批门控执行完毕 | 被阻断链有重新规划 | QA 结构校验通过 |
| **Phase 7** | POC 脚本生成 | 每个 POC 有 README | POC 可执行性自检 | QA 结构校验通过 |
| **Phase 8** | 所有报告 MD + JSON 生成 | 报告校验通过 | QA 校验通过 | — |
| **Phase 9** | 晋升门槛校验通过 | 新模式 8 段格式确认 | 三库一致性确认 | — |

### 门控不通过时的处理

| 情况 | 处理方式 |
|------|---------|
| MUST 输出文件缺失或为空 | 回退到当前 Phase 重新生成缺失文件 |
| 数据不完整（如规则未覆盖） | 补充缺失数据后重新校验 |
| 知识图谱边引用不存在的节点 | 回退生成缺失节点或修正边引用 |
| 五态标记有 `[ ]` 残留 | 回退补充检查，转为 `[x]`/`[?]`/`[-]`/`[!]` |
| QA 结构校验不通过 | 修复后重新校验 |

### QA 三层校验在门控中的位置

| 层级 | 触发时机 | 内容 |
|------|---------|------|
| 第一层 | 每个 Phase 完成后 | 结构性完整性（上述检查点） |
| 第二层 | Phase 8c 之前 | 语义抽检（5 条合规 + 3 条攻击 + 2 条通过） |
| 第三层 | 后续 Phase 自动度量 | 回溯验证（QA-OVERRIDE 追踪） |
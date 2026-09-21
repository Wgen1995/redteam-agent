---
name: report-summary
description: >
  全景报告生成和最终QA校验。汇总合规报告和攻击报告，生成综合渗透测试报告和覆盖矩阵。
  执行QA语义抽检和置信度评分。
  使用场景：所有Phase完成后最终报告生成。
  不使用场景：单独生成合规或攻击报告时。
---

## §0 套件根定位（启动第一步，强制）

本 SKILL 中所有相对路径（`skills/shared/`、`attack-patterns/`、`compliance-rules/`、`hypothesis-libraries/`、`references/`）均**相对套件根**，不相对 cwd。

**错误示例**（实际发生过）：SKILL 写 `skills/shared/SSH_COMMANDS.md`，LLM 拿 cwd `~/.config/opencode/skills/` 拼接 → 解析为 `~/.config/opencode/skills/shared/SSH_COMMANDS.md`（丢失套件根段 `gencpt/`）→ Read 失败。正确应为 `~/.config/opencode/skills/gencpt/skills/shared/SSH_COMMANDS.md`。

**若入口已传入套件根绝对路径**：直接用作前缀拼接所有相对路径，**不重复 Glob**。

**若未传入套件根**：用 Glob 工具定位，按以下顺序尝试首个命中：
- Pattern 1: `**/skills/shared/SSH_COMMANDS.md` → 套件根 = 命中路径向上两级
- Pattern 2: `**/gencpt/SKILL.md` → 套件根 = 命中路径父目录
- Pattern 3: `**/GenCPT*/SKILL.md` → 套件根 = 命中路径父目录

所有 Read 调用拼接套件根前缀：`skills/shared/X.md` → Read `{套件根}/skills/shared/X.md`。**禁用 `$ROOT/...` 变量形式**，Read 工具不展开 shell 变量。**不许凭记忆猜套件根路径**。

---

# Phase 8c — 全景报告生成和最终QA校验

## 核心职责

1. 汇总合规报告(8a)和攻击报告(8b)，生成综合渗透测试报告
2. 生成覆盖度全景报告（10大章节）
3. 执行QA语义抽检和置信度评分
4. 更新情节记忆和模式库命中计数

## 核心工作流（6 步）

### 步骤1：读取所有输入数据

读取以下数据：

**8a 合规报告**：
- `reports/compliance_report.md` + `reports/compliance_report.json`
- `reports/compliance_checkpoint_report.md` + `reports/compliance_checkpoint_report.json`

**8b 攻击报告**：
- `reports/attack_report.md` + `reports/attack_report.json`

**知识图谱完整数据**：
- `knowledge_graph/nodes/`（所有节点JSON + _index.md）
- `knowledge_graph/edges/`（所有边JSON + _index.md）

**其他输入**：
- `evidence/insights.md` — LLM 推理发现摘要
- `episodic_memory/session_history.md` — 跨会话历史
- `attack-patterns/_index.md` — 攻击模式索引
- `evidence/recon/recon_summary.md` — 侦察摘要
- `reports/poc_package/` — POC 包引用

### baseline 版本兼容性检查

读取 baseline 报告时，检查其 `suite_version` 字段：
- **版本一致**（如 V3 vs V3）：正常对比，包含合规覆盖率对比、攻击确认对比、新增/修复项对比
- **版本不一致**（如 V1 vs V3）：降级为简单趋势对比（只对比漏洞数量趋势、合规 pass/fail 数量变化），不做细节归一
- **版本不一致时**：在报告开头标注 `⚠️ baseline 版本不一致（baseline={旧版本}, 当前=V3），仅做趋势对比`
- **baseline 永不替代当前测试**：无论版本是否一致，当前测试结果始终是权威结果

### 步骤2：生成综合渗透测试报告

生成 `reports/pentest_report.md` 和 `reports/pentest_report.json`。

使用 `references/report-templates/pentest_report.md` 模板（如存在），否则按以下结构生成：

```markdown
# 容器与 Kubernetes 渗透测试报告

## 1. 执行概要

| 项目 | 内容 |
|------|------|
| 测试时间 | {session开始时间} - {结束时间} |
| 执行模式 | {A/B/C} |
| 测试范围 | {scope} |
| 目标环境 | {server} |
| 合规规则总数 | {总计} |
| 合规违规数 | {fail总计} |
| 攻击候选数 | {ATK-CAND总计} |
| 确认漏洞数 | {C1+C2} |
| 高风险线索数 | {C3} |
| QA置信度 | {高/低} |

## 2. 合规检测结果

（直接引用 compliance_report.md 摘要部分）

## 3. 攻击验证结果

（直接引用 attack_report.md 摘要部分）

## 4. 攻击链分析

（直接引用 attack_report.md 链分析部分）

## 5. POC 包索引

（引用 poc_package/ 目录结构）

## 6. 修复建议优先级排序

（基于合规报告修复优先级 + 攻击确认情况综合排序）

## 7. 风险评估总结

（综合合规和攻击结果的风险等级分布）
```

JSON 结构：

```json
{
  "report_type": "pentest_summary",
  "session_id": "sess-xxx",
  "generated_at": "2026-xx-xx",
  "mode": "C",
  "scope": ["k8s", "docker"],
  "environment": {
    "server": "prod-k8s-01",
    "env_fingerprint": {}
  },
  "compliance_summary": {
    "total_rules": 0,
    "pass": 0, "fail": 0, "warn": 0, "na": 0
  },
  "attack_summary": {
    "total_atk_cand": 0,
    "c1_confirmed": 0,
    "c2_condition_met": 0,
    "c3_high_risk_clue": 0,
    "disproved": 0,
    "blocked": 0
  },
  "chains_summary": {
    "total_chains": 0,
    "verified": 0,
    "partially_verified": 0
  },
  "qa_confidence": "high",
  "remediation_priority": []
}
```

### 步骤3：生成全景报告（覆盖矩阵）

生成 `reports/coverage_report.md`，包含以下10大章节（严格遵循5.3节定义）：

#### 第1章：执行详情

```markdown
## 1. 执行详情

| 项目 | 内容 |
|------|------|
| 会话ID | sess-xxx |
| 开始时间 | ... |
| 结束时间 | ... |
| 执行模式 | A/B/C |
| 测试范围 | k8s, docker |
| 目标服务器 | prod-k8s-01 |
| Phase统计 | Phase 1a: ✅ → Phase 1b: ✅ → ... → Phase 8c: ✅ |
| WU统计 | 总计N个WU，成功N，失败N |
| 环境指纹 | K8s v1.29 / Docker v24.0.7 / 节点3 / Pod数45 |
```

#### 第2章：环境覆盖全景

```markdown
## 2. 环境覆盖全景

| 覆盖维度 | 覆盖结果 | 覆盖率 |
|---------|---------|--------|
| 主机 | 3/3 节点已侦察 | 100% |
| Pod | 45/45 Pod已枚举 | 100% |
| 容器 | 67/67 容器已扫描 | 100% |
| ServiceAccount | 12/12 SA已分析 | 100% |
| 合规规则 | 198/226 规则已检测 | 87.2% |
| 源码扫描 | 156 文件已分析 | — |

（scope 不含的平台规则计为 na，覆盖率 = 检测数/scope内规则总数）
```

#### 第2.5章：最大盲区提示

基于第9章未覆盖事项和第4章覆盖矩阵，自动识别并突出展示本次测试的最大检测盲区：

```markdown
### ⚠️ 最大检测盲区

| 盲区 | 攻击面 | 覆盖率 | 原因 | 风险影响 | 建议 |
|------|--------|--------|------|---------|------|
| 盲区1 | AS-N | N/M (N%) | {高优先级原因} | {影响描述} | {补充验证建议} |

（仅展示高优先级盲区：整个攻击面未覆盖或覆盖率<25%）
```

生成规则：
1. 从第4章覆盖矩阵中提取每个攻击面的覆盖率
2. 覆盖率<25%的攻击面自动标记为"高优先级盲区"
3. 审批限制导致关键逃逸验证未执行的，也标记为"高优先级盲区"
4. 最多展示Top 3盲区，避免信息过载

#### 第3章：合规分组热力图

按 CIS Benchmark 分组汇总 fail/warn 统计，视觉热力图格式：

```markdown
## 3. 合规分组热力图

### K8s 合规热力图

| 分组 | 规则数 | ✅ Pass | ❌ Fail | ⚠️ Warn | ➖ NA | 热度 |
|------|--------|---------|---------|---------|------|------|
| G_1_1 API Server 文件 | 7 | 2 | 4 | 1 | 0 | 🔴 |
| G_1_2 API Server 认证 | 23 | 18 | 3 | 2 | 0 | 🟡 |
| G_2_1 CM 文件 | 4 | 4 | 0 | 0 | 0 | 🟢 |
| ... | ... | ... | ... | ... | ... | ... |

热度标准：fail ≥ 30% → 🔴，10%-30% → 🟡，< 10% → 🟢
```

#### 第4章：攻击面覆盖矩阵（核心）

**7大攻击面 × 模式库/LLM推理/总覆盖 矩阵**：

```markdown
## 4. 攻击面覆盖矩阵

| 攻击面 | 模式库覆盖 | LLM推理覆盖 | 总覆盖 |
|--------|-----------|------------|--------|
| AS-1 逃逸 | socket-escape ✅ / cgroup-escape ✅ / procfs-escape ➖ / ... | Docker Shim逃逸 ⚠️ | 5/7 |
| AS-2 认证 | k8s-sa-exploit ✅ / k8s-rbac-abuse ➖ / ... | 无 | 2/3 |
| AS-3 网络 | lateral-move ✅ / cloud-metadata ✅ / ... | DNS隧道 ⚠️ | 3/4 |
| AS-4 数据泄露 | secret-exfil ✅ / env-credential-leak ➖ / ... | 无 | 2/3 |
| AS-5 拒绝服务 | resource-abuse ✅ / fork-bomb ➖ | 无 | 1/2 |
| AS-6 供应链 | image-tag-mutation ➖ / registry-poison ➖ | 无 | 0/2 |
| AS-7 持久化 | webhook-backdoor ✅ / cronjob-persist ➖ / ... | 无 | 1/3 |
```

**关键要求**：
- 不可利用（已证伪）项必须出现在覆盖矩阵中，标注"已检查不可利用+证伪依据"
- 已阻断项也必须出现在覆盖矩阵中
- 每个模式标注验证结果：✅ confirmed / ✅ condition_met / ⚠️ high_risk_clue / ➖ disproved / 🛑 blocked
- "总覆盖" = (模式库命中 + LLM推理命中) / 该攻击面总模式数

#### 第5章：已知模式库覆盖全景

```markdown
## 5. 已知模式库覆盖全景

| 攻击面 | 模式名 | 触发条件满足 | 验证结果 | 可信度 | ATK-CAND |
|--------|--------|-------------|---------|--------|----------|
| AS-1 | socket-escape | ✅ | ✅✅ 已确认 | C1 | ATK-CAND-001 |
| AS-1 | cgroup-escape | ✅ | 🛑 已阻断(AppArmor) | C2 | ATK-CAND-003 |
| AS-1 | procfs-escape | ❌ | ➖ 已证伪 | — | ATK-CAND-004 |
| ... | ... | ... | ... | ... | ... |
```

#### 第6章：LLM推理覆盖全景

```markdown
## 6. LLM推理覆盖全景

| 攻击面 | 推理发现 | 验证结果 | 可信度 | 晋升状态 | ATK-CAND |
|--------|---------|---------|--------|---------|----------|
| AS-1 | Docker Shim逃逸 | ⚠️ 高风险线索 | C3 | 未晋升(命中1次) | ATK-CAND-010 |
| AS-3 | DNS隧道 | ✅ 条件成立 | C2 | 候选晋升(命中3次) | ATK-CAND-011 |
| ... | ... | ... | ... | ... | ... |
```

#### 第7章：攻击验证结果分布

```markdown
## 7. 攻击验证结果分布

### 7.1 可信度分布

| 可信度 | 数量 | 占比 | 说明 |
|--------|------|------|------|
| C1 实证复现 ✅✅ | N | xx% | 5项门槛全满足+L2差分证明 |
| C2 条件实证 ✅ | N | xx% | 前置条件满足+理论链路完整 |
| C3 风险线索 ⚠️ | N | xx% | 配置隐患但前置条件不全 |
| 不可利用 ➖ | N | xx% | 已证伪，附证伪依据 |
| 已阻断 🛑 | N | xx% | 被安全机制阻断，附机制名 |

### 7.2 来源分布

| 来源 | 数量 | 说明 |
|------|------|------|
| 📚 已知攻击模式库 | N | Phase 4a 匹配 |
| 🧠 LLM 推理分析 | N | Phase 4b 发现 |
| 🔄 学习模式 | N | 已晋升模式 |
```

#### 第8章：漏洞来源标识

```markdown
## 8. 漏洞来源标识

| ATK-CAND | 来源 | 来源详情 | 首次命中 | 累计命中 |
|----------|------|---------|---------|---------|
| ATK-CAND-001 | 📚 | socket-escape (manual) | 本次 | 15 |
| ATK-CAND-010 | 🧠 | Phase 4b 推理 | 本次 | 1 |
| ATK-CAND-008 | 🔄 | nsproxy-escape (learned, promoted 2026-05) | 本次 | 5 |
```

#### 第9章：未覆盖事项及原因

```markdown
## 9. 未覆盖事项及原因

### 9.1 最大盲区提示

> ⚠️ **本次测试最大盲区**：{攻击面} {模式名} — {原因}，影响{影响描述}。
> 建议优先在{建议环境/方式}中补充验证。

（基于以下优先级规则自动生成：
- **高优先级**：整个攻击面未覆盖（如 AS-1 逃逸全部未检测），或覆盖矩阵中某攻击面覆盖率<25%
- **中优先级**：攻击面内 3+ 模式未覆盖
- **低优先级**：攻击面内 1-2 模式未覆盖，且该攻击面整体覆盖≥50%）

### 9.2 未覆盖事项明细

| 攻击面 | 未覆盖项 | 原因类型 | 原因详情 | 优先级 | 建议 |
|--------|---------|---------|---------|--------|------|
| AS-6 供应链 | registry-poison | 模式库缺失 | 无此攻击模式 | 中 | 建议新增模式库条目 |
| AS-2 认证 | anonymous-access | 环境限制 | 目标环境未暴露API端点 | 中 | 建议在暴露环境复测 |
| AS-1 逃逸 | socket-escape | 审批限制 | L5 操作未获批准 | 高 | 建议在测试环境单独验证 |
| AS-7 持久化 | cronjob-persist | LLM未覆盖 | 合规结果无相关信号 | 低 | 建议手动检查 |
```

原因类型：
- **模式库缺失**：攻击模式库中无对应模式
- **LLM未覆盖**：LLM推理未发现此攻击面
- **环境限制**：目标环境不满足前置条件
- **审批限制**：高影响操作未获执行批准
- **前置条件不满足**：已被证伪
- **被安全机制阻断**：已有防护

优先级规则：
- **高优先级**：①整个攻击面未覆盖（覆盖矩阵该行全为"未检测"）②该攻击面覆盖率<25% ③审批限制导致关键逃逸验证未执行
- **中优先级**：①攻击面内3+模式未覆盖 ②模式库缺失导致检测盲区
- **低优先级**：①攻击面内1-2模式未覆盖且该面整体覆盖≥50% ②LLM未覆盖但合规结果无相关信号

#### 第10章：产品安全质量评估

```markdown
## 10. 产品安全质量评估

### 10.1 综合评分

| 维度 | 评分(0-10) | 说明 |
|------|-----------|------|
| 合规基线 | N/10 | 基于合规pass率 |
| 攻击面覆盖 | N/10 | 基于7大攻击面覆盖度 |
| 防护深度 | N/10 | 基于已阻断/总攻击比例 |
| 修复成熟度 | N/10 | 基于修复建议可行性 |
| **综合评分** | **N/10** | 加权平均 |

### 10.2 关键风险（Top 5）

1. 【Critical】xxx
2. 【High】xxx
...

### 10.3 同比变化（有--baseline时）

| 维度 | 上次评分 | 本次评分 | 变化 |
|------|---------|---------|------|
| 合规基线 | 5/10 | 6/10 | ↑ +1 |
...

### 10.4 下一步建议

1. 立即修复：xxx
2. 近期修复：xxx
3. 长期改进：xxx

### 10.5 下次测试建议

1. 建议包含scope：xxx
2. 建议审批级别：xxx
3. 建议重点攻击面：xxx
```

### 步骤4：QA语义抽检

从报告中随机抽取以下条目，通过 ssh_execute 重新验证：

**5条合规违规**：
1. 从 compliance_report.json 的 fail 规则中随机选5条
2. 对每条规则执行原始SSH检测命令
3. 验证输出是否与报告中的判定依据一致
4. 记录：规则ID、原始判定、重新验证结果、是否一致

**3条ATK-CAND confirmed**：
1. 从 attack_report.json 的 C1/C2 条目中随机选3条
2. 检查差分证明逻辑自洽性（攻击前后状态对比是否成立）
3. 不重新执行攻击命令，只检查前置条件和差分逻辑
4. 记录：ATK-CAND编号、可信度、差分证明审查结果

**2条通过（[-]证伪）**：
1. 从报告中已证伪的ATK-CAND中随机选2条
2. 重新检查证伪依据（L0命令输出是否确实证明前置条件不满足）
3. 记录：ATK-CAND编号、证伪依据审查结果

### 步骤5：计算QA置信度评分

```markdown
## QA 置信度评分

### 语义抽检结果

| 抽检类型 | 抽检数 | 通过数 | 失败数 | 失败条目 |
|---------|--------|--------|--------|---------|
| 合规违规 | 5 | 5 | 0 | — |
| ATK-CAND confirmed | 3 | 3 | 0 | — |
| ATK-CAND 证伪 | 2 | 2 | 0 | — |

### 置信度判定

- 全部复现 → "QA 置信度：高"
- 部分不能复现 → "QA 置信度：低，建议重点复核：{失败条目列表}"
```

生成 `evidence/qa/qa_summary_report.md`，包含：
- 抽检条目清单
- 每条抽检的重新验证结果
- 置信度评分
- 失败条目的详细说明和复核建议

### 步骤6：更新情节记忆和模式库

更新 `episodic_memory/session_history.md`：
- 追加本次会话的攻击结果摘要（每个攻击面的命中数、C1/C2/C3统计）
- 更新 hit_count（每个攻击模式的命中次数）

更新 `attack-patterns/_index.md` hit_count：
- 每个 _index.md 中的模式条目，hit_count +1（如果在本次会话中命中）
- learned 模式的 last_hit 更新为本次日期

## MUST 输入

| 输入 | 路径 | 说明 |
|------|------|------|
| 合规报告 MD | reports/compliance_report.md | Phase 8a 最终版 |
| 合规报告 JSON | reports/compliance_report.json | 结构化数据 |
| 攻击报告 MD | reports/attack_report.md | Phase 8b |
| 攻击报告 JSON | reports/attack_report.json | 结构化数据 |
| 知识图谱节点 | knowledge_graph/nodes/（所有JSON） | 节点数据 |
| 知识图谱节点索引 | knowledge_graph/nodes/_index.md | 节点索引 |
| 知识图谱边 | knowledge_graph/edges/（所有JSON） | 边数据 |
| 知识图谱边索引 | knowledge_graph/edges/_index.md | 边索引 |
| LLM推理摘要 | evidence/insights.md | Phase 4b |
| 会话历史 | episodic_memory/session_history.md | 跨会话历史 |
| 攻击模式索引 | attack-patterns/_index.md | 模式库索引 |
| 侦察摘要 | evidence/recon/recon_summary.md | Phase 1a |

## MUST 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 综合报告 MD | reports/pentest_report.md | 合规+攻击+修复+风险 |
| 综合报告 JSON | reports/pentest_report.json | 结构化数据 |
| 全景报告 MD | reports/coverage_report.md | 10大章节覆盖矩阵 |
| QA 抽检报告 | evidence/qa/qa_summary_report.md | 语义抽检结果+置信度 |

## 覆盖矩阵关键要求

### 不可利用项必须出现在覆盖矩阵中

已证伪（➖）的攻击模式**必须出现在第4章覆盖矩阵中**，标注：
- "已检查不可利用 + 证伪依据"
- 在第5章中列出验证结果为 ➖ 和证伪原因

### 已阻断项必须出现在覆盖矩阵中

被安全机制阻断（🛑）的攻击模式**必须出现在第4章覆盖矩阵中**，标注：
- 阻断机制名称（如 AppArmor/Seccomp/NetworkPolicy）
- 在第5章中列出验证结果为 🛑 和阻断机制

### 覆盖矩阵格式

行 = 7大攻击面（AS-1至AS-7），列 = 模式库覆盖/LLM推理覆盖/总覆盖。

总覆盖计算：
- 模式库覆盖 = 该攻击面模式库命中数 / 该攻击面模式总数
- LLM推理覆盖 = 该攻击面LLM推理命中数 / 该攻击面模式总数
- 总覆盖 = (模式库命中数 + LLM推理命中数) / 该攻击面模式总数

## QA语义抽检关键要求

- 合规抽检：5条fail规则，通过ssh_execute重新执行原始检测命令
- 攻击抽检：3条C1/C2 ATK-CAND，检查差分证明逻辑自洽性
- 证伪抽检：2条[-] ATK-CAND，重新检查证伪依据
- 整体通过 → QA置信度高
- 有条目不通过 → QA置信度低 + 列出失败条目建议复核

## 反幻觉硬约束

1. 不准伪造抽检结果 — QA抽检必须通过ssh_execute实际执行命令验证
2. 不准伪造覆盖数据 — 覆盖矩阵数字必须来自知识图谱和报告数据的实际统计
3. 无证据不写确认态 — 抽检结果必须如实记录，通过或不通过
4. 省略词零容忍 — 不出现"等"、"..."、"+N"、大致、约
5. 占位符必须替换 — 所有【xxx】占位符替换为实际值
6. 不可利用和已阻断项不得遗漏 — 全景报告必须包含所有检查过的攻击模式

## 独立运行参数

```
/gencpt-report-summary --server prod-k8s-01 --session-dir /path/to/session
```

注意：report-summary 需要 SSH 连接来执行 QA 语义抽检（重新验证 5 条合规规则），因此需 SSH 连通性。

## 与其他技能的依赖

- 上游：report-compliance(8a)、report-attack(8b) 必须先完成
- 需要读取：知识图谱完整数据、evidence 目录数据
- 需要 SSH：QA 语义抽检需要 ssh_execute 重新验证合规规则
- 下游：evolve(9) 可选，读取本技能输出

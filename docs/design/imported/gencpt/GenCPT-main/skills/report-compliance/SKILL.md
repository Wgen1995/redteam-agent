---
name: report-compliance
description: >
  合规检测报告生成。读取Phase 2合规数据，生成MD+JSON格式合规报告和合规检查点报告。
  使用场景：Phase 2完成后生成报告。
  不使用场景：攻击验证阶段。
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

# Phase 8a — 合规检测报告生成

## 核心职责

读取 Phase 2 合规检测结果，生成合规检查点报告和最终合规报告。检查点报告在 Phase 2 完成后立即输出，最终报告在 Phase 8a 增加攻击关联和修复优先级。

## 两次输出

1. **Phase 2 完成后立即**：compliance_checkpoint_report.md（每条规则判定+依据+SSH 输出摘要，不含攻击关联）
2. **Phase 8a 最终版**：在检查点基础上增加攻击关联、风险等级调整、修复优先级

## 核心工作流（5 步）

### 步骤1：读取合规数据

读取 `evidence/compliance/` 目录下所有数据：

- `evidence/compliance/k8s/results.json` — K8s 合规结果
- `evidence/compliance/k8s/summary.md` — K8s 合规摘要
- `evidence/compliance/docker/results.json` — Docker 合规结果
- `evidence/compliance/docker/summary.md` — Docker 合规摘要
- `evidence/compliance/containerd/results.json` — containerd 合规结果
- `evidence/compliance/containerd/summary.md` — containerd 合规摘要

按 scope 读取，scope 不含的平台跳过。

**数据结构**（results.json 每条规则）：

```json
{
  "rule_id": "K8s-1.2.1",
  "group": "G_1_2_api_server_auth",
  "status": "fail",
  "evidence": "kubectl 输出摘要",
  "reasoning": "LLM 判定理由",
  "ssh_command": "kubectl get pods -o jsonpath='...",
  "ssh_output_summary": "实际输出摘要（≤200字）",
  "target": "目标对象标识",
  "severity": "High"
}
```

### 步骤2：按 CIS 分组汇总

按 CIS Benchmark 分组统计每个平台的 pass/fail/warn/na 数量。

统计规则：
- 每个平台（k8s/docker/containerd）分别统计
- 每个分组（G_x_x）分别统计
- 汇总为：
  - K8s: 134 条（28 个分组）
  - Docker: 64 条（7 个分组）
  - containerd: 28 条（5 个分组）
  - 三平台合计: 226 条（仅统计 scope 内平台）

### 步骤3：生成合规检查点报告

生成 `reports/compliance_checkpoint_report.md` 和 `reports/compliance_checkpoint_report.json`。

检查点报告格式（每条规则一行）：

```markdown
### G_1_2 API Server 认证（23 条）

| 规则ID | 状态 | 依据摘要 | SSH 输出摘要 |
|--------|------|---------|-------------|
| K8s-1.2.1 | ❌ fail | 匿名认证未禁用 | kubectl get... 输出: true |
| K8s-1.2.2 | ✅ pass | — | — |
| K8s-1.2.3 | ⚠️ warn | 部分配置缺失 | kubectl get... 输出: ... |
| K8s-1.2.4 | ➖ na | 非适用环境 | — |
```

JSON 结构：

```json
{
  "report_type": "compliance_checkpoint",
  "session_id": "sess-xxx",
  "generated_at": "2026-xx-xx",
  "scope": ["k8s", "docker"],
  "platforms": {
    "k8s": {
      "total": 134,
      "pass": 0, "fail": 0, "warn": 0, "na": 0,
      "groups": {
        "G_1_1_api_server_files": {
          "total": 7, "pass": 0, "fail": 0, "warn": 0, "na": 0,
          "rules": [
            {
              "rule_id": "K8s-1.1.1",
              "status": "pass",
              "evidence_summary": "...",
              "ssh_output_summary": "..."
            }
          ]
        }
      }
    }
  }
}
```

### 多节点检测结果展示

合规报告中节点级规则（G_4/G_5）的检测结果按节点分组展示：
- 每个节点一个小节：`### 节点: master / worker-1 / worker-2`
- 不可达节点标注：`⚠️ 该节点 SSH 不可达，Kubelet 配置未检测`
- 检查点报告的"规则数校验"中，节点级规则数 = 单节点规则数 × 可达节点数

### 步骤4：生成最终合规报告

在检查点报告基础上增加以下内容：

1. **攻击关联**：每条 fail/warn 规则映射到攻击假设库（compliance-hypotheses.md），标注关联的攻击面和攻击模式
2. **风险等级调整**：根据交叉关联结果（cross_ref.json）调整风险等级
   - 单条违规 → 对应 CIS 原始严重度
   - 多条叠加（同一目标 ≥3 条违规） → 严重度提升一级
   - 有攻击确认（ATK-CAND confirmed） → 标注"已有攻击验证"
3. **修复优先级**：基于以下因素排序
   - 风险等级（Critical > High > Medium > Low）
   - 是否有攻击确认（有确认的优先）
   - 叠加效应（多条叠加的优先）
   - 修复难度（简单配置修改优先于架构调整）

最终报告格式：

```markdown
# 合规检测报告

## 概要

| 平台 | 总规则数 | ✅ Pass | ❌ Fail | ⚠️ Warn | ➖ NA |
|------|---------|---------|---------|---------|------|
| K8s | 134 | xx | xx | xx | xx |
| Docker | 64 | xx | xx | xx | xx |
| 合计 | 198 | xx | xx | xx | xx |

## 风险概览

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| Critical | xx | 有攻击确认的严重违规 |
| High | xx | 严重违规或叠加效应 |
| Medium | xx | 中等风险违规 |
| Low | xx | 轻微风险或建议 |

## 分组详情

### K8s 合规检测结果

#### G_1_1 API Server 文件（7 条）

| 规则ID | 状态 | 风险等级 | 依据 | 攻击关联 | 修复建议 |
|--------|------|---------|------|---------|---------|
| K8s-1.1.1 | ❌ fail | High | ... | AS-1 逃逸攻击面 | 修改配置文件权限... |

## 修复优先级

| 优先级 | 规则ID | 风险等级 | 攻击确认 | 叠加效应 | 修复建议 |
|--------|--------|---------|---------|---------|---------|
| P1 | K8s-5.2.1 | Critical | ATK-CAND-001 ✅✅ | 3条叠加 | ... |
```

JSON 结构与检查点报告相同，增加字段：

```json
{
  "rule_id": "K8s-5.2.1",
  "status": "fail",
  "evidence_summary": "...",
  "ssh_output_summary": "...",
  "risk_level": "Critical",
  "attack_linked": ["ATK-CAND-001"],
  "attack_surface": "AS-1 逃逸",
  "stacking": true,
  "stacking_count": 3,
  "remediation_priority": "P1",
  "remediation_advice": "..."
}
```

### 步骤5：三重校验第三重

在报告生成前执行第三重校验（报告级）：

1. 报告中每条规则都有判定（无 `[ ]` 空状态）
2. fail/warn 规则都有判定依据摘要
3. 总计数字 = pass + fail + warn + na（三平台分别验证）
4. 无占位符（所有【xxx】必须替换为实际值）
5. 不通过 → 回到对应数据源补充，直到全部满足

**检查点校验清单**：
- ① 三平台规则数合计 = 226（K8s 134 + Docker 64 + containerd 28，仅统计 scope 内平台的子集）
- ② 每条规则有判定（pass/fail/warn/na，无空值）
- ③ fail/warn 规则有依据摘要（SSH 命令输出 + LLM 判定理由）
- ④ 数字合计一致（总计 = pass + fail + warn + na）

## MUST 输入

| 输入 | 路径 | 说明 |
|------|------|------|
| K8s 合规结果 | evidence/compliance/k8s/results.json | 134 条规则判定 |
| K8s 合规摘要 | evidence/compliance/k8s/summary.md | K8s 概要 |
| Docker 合规结果 | evidence/compliance/docker/results.json | 64 条规则判定 |
| Docker 合规摘要 | evidence/compliance/docker/summary.md | Docker 概要 |
| containerd 合规结果 | evidence/compliance/containerd/results.json | 28 条规则判定 |
| containerd 合规摘要 | evidence/compliance/containerd/summary.md | containerd 概要 |
| 合规假设库 | hypothesis-libraries/compliance-hypotheses.md | 违规→攻击映射 |
| 交叉关联数据 | evidence/cross-ref/cross_ref_summary.md | 风险叠加信息 |
| 交叉关联边 | knowledge_graph/edges/cross_ref.json | 叠加效应数据 |

## MUST 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 检查点报告 MD | reports/compliance_checkpoint_report.md | 每条规则判定+依据+SSH摘要 |
| 检查点报告 JSON | reports/compliance_checkpoint_report.json | 结构化数据 |
| 最终报告 MD | reports/compliance_report.md | 含攻击关联+风险等级+修复优先级 |
| 最终报告 JSON | reports/compliance_report.json | 结构化数据 |

## 反幻觉硬约束

1. 不准伪造合规判定 — 每条判定必须来自 evidence/compliance/ 下的实际数据
2. 不准伪造 SSH 输出 — 依据摘要必须来自 results.json 中的 ssh_output_summary 字段
3. 无证据不写确认态 — 检查点报告中无攻击关联字段，最终报告中的攻击关联必须有 ATK-CAND 编号
4. 不准省略规则 — 三平台所有规则必须出现在报告中（scope 不含的平台标注为 na）
5. 占位符零容忍 — 不出现"等"、"..."、"+N"、大致、约
6. 所有【xxx】占位符必须替换为实际值

## 独立运行参数

```
/gencpt-report-compliance --session-dir /path/to/session
```

## 与其他技能的依赖

- 上游：k8s-compliance(2a)、docker-compliance(2b)、containerd-compliance(2c)、cross-ref(3)
- 下游：report-summary(8c) 读取本技能输出作为综合报告输入
- 并行：与 report-attack(8b) 无依赖，可并行执行

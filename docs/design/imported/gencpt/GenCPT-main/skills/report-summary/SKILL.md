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
2. 生成覆盖度全景报告（10 大章节）
3. 执行 QA 语义抽检和置信度评分
4. 更新情节记忆和模式库命中计数

---

## MUST 输入

| 输入 | 路径 | 说明 |
|------|------|------|
| 合规报告 MD | reports/compliance_report.md | Phase 8a 最终版 |
| 合规报告 JSON | reports/compliance_report.json | 结构化数据 |
| 攻击报告 MD | reports/attack_report.md | Phase 8b |
| 攻击报告 JSON | reports/attack_report.json | 结构化数据 |
| 知识图谱节点 | knowledge_graph/nodes/（所有JSON） | 节点数据 |
| 知识图谱边 | knowledge_graph/edges/（所有JSON） | 边数据 |
| LLM推理摘要 | evidence/insights.md | Phase 4b |
| 会话历史 | episodic_memory/session_history.md | 跨会话历史 |
| 攻击模式索引 | attack-patterns/_index.md | 模式库索引 |
| 侦察摘要 | evidence/recon/recon_summary.md | Phase 1a |

## MUST 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 综合报告 MD | reports/pentest_report.md | 合规+攻击+修复+风险 |
| 综合报告 JSON | reports/pentest_report.json | 结构化数据 |
| 全景报告 MD | reports/coverage_report.md | 10 大章节覆盖矩阵 |
| QA 抽检报告 | evidence/qa/qa_summary_report.md | 语义抽检结果+置信度 |

---

## 核心工作流（6 步）

### 步骤 1：读取所有输入数据

读取 8a 合规报告、8b 攻击报告、知识图谱完整数据、LLM 推理摘要、会话历史、攻击模式索引、侦察摘要。

**baseline 版本兼容性检查、趋势对比降级规则详见 `references/baseline_compat.md`。**

### 步骤 2：生成综合渗透测试报告

生成 `reports/pentest_report.md` 和 `reports/pentest_report.json`，包含执行概要、合规检测结果、攻击验证结果、攻击链分析、POC 包索引、修复建议优先级排序、风险评估总结。

**综合报告详细模板详见 `references/chapter_template.md`。**

### 步骤 3：生成全景报告（覆盖矩阵）

生成 `reports/coverage_report.md`，包含 10 大章节：

1. 执行详情
2. 环境覆盖全景
3. 合规分组热力图
4. 攻击面覆盖矩阵（核心）
5. 已知模式库覆盖全景
6. LLM推理覆盖全景
7. 攻击验证结果分布
8. 漏洞来源标识
9. 未覆盖事项及原因
10. 产品安全质量评估

**10 章节详细模板、覆盖矩阵格式详见 `references/chapter_template.md`。**

#### 覆盖矩阵关键要求

- **不可利用项必须出现**：已证伪（➖）的攻击模式必须出现在第 4 章覆盖矩阵中，标注"已检查不可利用 + 证伪依据"
- **已阻断项必须出现**：被安全机制阻断（🛑）的攻击模式必须出现，标注阻断机制名称（如 AppArmor/Seccomp/NetworkPolicy）
- 行 = 7 大攻击面（AS-1 至 AS-7），列 = 模式库覆盖/LLM推理覆盖/总覆盖

### 步骤 4：QA 语义抽检

从报告中随机抽取条目，通过 ssh_execute 重新验证：
- **5 条合规违规**：从 fail 规则中随机选 5 条，执行原始 SSH 检测命令验证
- **3 条 ATK-CAND confirmed**：检查差分证明逻辑自洽性（不重新执行攻击命令）
- **2 条通过（[-]证伪）**：重新检查证伪依据

**SSH 不可用时降级方案**：
- 如果 ssh_execute 返回连接失败：QA 语义抽检降级为"证据文件校验"——不重新 SSH，改为检查原始证据文件是否存在且内容与报告引用一致
- 置信度标注为"中"（而非"高"或"低"）
- 在 qa_summary_report.md 中标注"SSH 不可用，语义抽检降级为证据文件校验"

**QA 抽检 SSH 输出写盘**：写入 `evidence/qa/raw/`，命名遵循 OUTPUT_STANDARD §1.5。

**QA 语义抽检详细规则详见 `references/qa_semantic.md`。**

### 步骤 5：计算 QA 置信度评分

- 全部复现 → "QA 置信度：高"
- 部分不能复现 → "QA 置信度：低，建议重点复核：{失败条目列表}"

生成 `evidence/qa/qa_summary_report.md`。

**置信度评分标准详见 `references/qa_semantic.md`。**

### 步骤 6：更新情节记忆和模式库

- 追加本次会话的攻击结果摘要到 `episodic_memory/session_history.md`
- 更新 `attack-patterns/_index.md` 中每个命中模式的 hit_count（learned 模式 last_hit 更新为本次日期）

---

## 反幻觉硬约束

1. 不准伪造抽检结果 — QA 抽检必须通过 ssh_execute 实际执行命令验证
2. 不准伪造覆盖数据 — 覆盖矩阵数字必须来自知识图谱和报告数据的实际统计
3. 无证据不写确认态 — 抽检结果必须如实记录，通过或不通过
4. 省略词零容忍 — 不出现"等"、"..."、"+N"、大致、约
5. 占位符必须替换 — 所有【xxx】占位符替换为实际值
6. 不可利用和已阻断项不得遗漏 — 全景报告必须包含所有检查过的攻击模式

---

## 独立运行参数

```
/gencpt-report-summary --server prod-k8s-01 --session-dir /path/to/session
```

注意：report-summary 需要 SSH 连接来执行 QA 语义抽检（重新验证 5 条合规规则），因此需 SSH 连通性。

---

## 与其他技能的依赖

- **上游**：report-compliance(8a)、report-attack(8b) 必须先完成
- **需要读取**：知识图谱完整数据、evidence 目录数据
- **需要 SSH**：QA 语义抽检需要 ssh_execute 重新验证合规规则
- **下游**：evolve(9) 可选，读取本技能输出

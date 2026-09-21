---
name: evolve
description: >
  攻击模式进化。分析本次检测的 LLM 推理发现，评估是否晋升为新攻击模式，执行自净。
  可在 Pipeline 末尾用 --evolve 参数触发，也可独立运行。
  不使用场景：检测中、不需要进化模式库时。
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

# evolve — Phase 9 攻击模式进化

本 SKILL 负责分析 Phase 4b 产出的 LLM 推理发现（insights），将经验丰富的发现晋升为新攻击模式，同时对已学习的模式库执行自净和降级，保持攻击模式库的健康度和准确性。本 SKILL 不执行任何 SSH 命令，纯 Markdown 读写和 LLM 语义分析。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `evidence/insights.md` | Phase 4b | 本次会话的 LLM 推理发现，包含 source=llm_reasoning 的 ATK-CAND 候选 |
| `knowledge_graph/episodic_memory/session_history.md` | 情节记忆 | 跨会话历史记录，用于统计跨会话命中次数和不同环境命中 |
| `attack-patterns/_index.md` | 攻击模式库 | 现有模式列表和每个模式的 hit_count、source、confidence、stale 标记 |
| `hypothesis-libraries/attack-hypotheses.md` | 假设库 | 现有攻击假设卡片，用于判断候选是否能匹配现有假设 |

**前置条件校验**：
1. `evidence/insights.md` 存在且非空（Phase 4b 有产出）
2. `attack-patterns/_index.md` 存在
3. `hypothesis-libraries/attack-hypotheses.md` 存在

任一前置条件不满足 → 立即终止，在 `progress.json` 标记 Phase 9 为 `skipped`，输出 `evidence/evolve/evolve_report.md` 记录跳过原因。

---

## 引用共享规范

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记 |
| `skills/shared/SEVERITY_RATING.md` | 严重等级定义，用于为新晋升模式声明 severity |

---

## 晋升门槛概述（4 项全满足才可晋升）

| 门槛 | 名称 | 满足条件 |
|------|------|---------|
| ① | 差分证明充分 | L2 差分前后对比证据完整，至少 2 个可观测差异 |
| ② | 探测可复现 | 在 ≥2 个不同环境（不同 host_fingerprint）可达同样安全结论 |
| ③ | 无法匹配现有模式 | 与全部现有模式的前置条件和攻击路径都不一致 |
| ④ | 跨会话命中 ≥2 次 | 在历史 session_history.md 中出现 ≥2 次相同或高度相似 ATK-CAND |

**4 项晋升门槛详细规则、用户审批流程、模式创建流程详见 `references/promotion_gates.md`。**

---

## 核心工作流（5 步）

### 步骤 1：收集洞察

1. 读取 `evidence/insights.md`，提取所有 `source=llm_reasoning` 的 ATK-CAND 候选条目
2. 读取 `knowledge_graph/episodic_memory/session_history.md`，提取历史会话中记录的 ATK-CAND 列表
3. 读取 `attack-patterns/_index.md`，提取现有模式列表和每个模式的 `hit_count`、`source`、`confidence`、`last_hit`、`stale` 标记
4. 读取 `hypothesis-libraries/attack-hypotheses.md`，提取现有假设卡片列表

### 步骤 2：逐条评估

对每个候选发现：

- **2a 与现有模式比对**：比对前置条件集合、攻击路径结构、攻击面归属。是现有模式变体 → 更新 hit_count，不进入晋升检查。是全新发现 → 进入 2b。
- **2b 晋升门槛检查**：逐项检查 4 项晋升门槛。4 项全满足 → 标记"可晋升"。不满足 → 标记"暂不晋升"。满足 2-3 项 → 标记"暂存观察"。

**晋升门槛检查详细规则、判定结果详见 `references/promotion_gates.md`。**

### 步骤 3：用户审批

对可晋升候选和暂存观察候选，使用当前环境的用户交互工具逐条确认。超时 10 分钟无响应 → 默认选择"暂存观察"。

**用户审批流程、询问格式、选项处理详见 `references/promotion_gates.md`。**

### 步骤 4：模式创建

对用户选择"添加为新模式"的候选：读取晋升模板 → 生成 8 段结构 SKILL.md → 写入 `_learned/` 目录 → 更新 _index.md → 更新假设库 → 更新 _learned_index.md。

**模式创建详细流程（4.1-4.6）、frontmatter 格式、文件路径规则详见 `references/promotion_gates.md`。**

### 步骤 5：自净和降级

遍历所有 `source=learned` 的模式，根据 hit_count 和未命中连续次数执行自动调整：
- hit_count ≥5 且跨 ≥2 环境 → confidence 升级为 high
- 连续 5 次未命中 → 降级为 medium
- 连续 10 次未命中 → 标记 stale=true
- 连续 15 次未命中 → 询问用户是否归档

**自净机制、升级/降级规则、归档处理、进化报告格式详见 `references/self_cleaning.md`。**

---

## 一致性维护

进化完成后执行 LLM 语义检查三库一致性（_index.md ↔ 实际文件 ↔ 假设卡片）。

**三库一致性检查项、不一致处理、输出格式详见 `references/consistency_check.md`。**

---

## MUST 输出

| 文件 | 说明 |
|------|------|
| `attack-patterns/{attack-surface}/{pattern-name}/_learned/SKILL.md` | 新晋升的模式文件（如本次有晋升） |
| `attack-patterns/_index.md` | 更新后的索引（含新晋升条目、hit_count 更新、confidence 更新、stale 更新） |
| `hypothesis-libraries/attack-hypotheses.md` | 更新后的假设库（含新假设卡片） |
| `evidence/evolve/evolve_report.md` | 进化报告：晋升列表 + 降级列表 + 升级列表 + 归档列表 + 变体匹配列表 + 暂存观察列表 + 统计 + 三库一致性检查 |

**无晋升时的输出**：即使本次无候选晋升，也必须输出 evolve_report.md（记录零晋升原因、变体匹配统计、降级/升级/归档操作、三库一致性检查结果）。

---

## 检查点

Phase 9 完成判定需全部通过：

1. **所有候选发现有处理结论** — insights.md 中每个 source=llm_reasoning 的 ATK-CAND 都有处理结果（晋升/拒绝/暂存/变体匹配），无遗漏
2. **晋升门槛完整检查** — 每个可晋升候选的 4 项门槛都有明确检查记录（满足/不满足 + 详细说明）
3. **用户审批记录** — 每个晋升和归档操作都有当前环境的用户交互工具的用户审批记录
4. **三库一致性** — _index.md 条目 ↔ 实际文件 ↔ 假设卡片，编号连续，frontmatter 字段完整
5. **evolve_report.md 完整** — 包含 7 个章节（晋升列表、降级列表、升级列表、归档列表、变体匹配列表、暂存观察列表、统计），无空章节

---

## WU 摘要格式

evolve 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/evolve/summaries/evolve_summary.json`，包含字段：`work_unit_id`、`status`、`summary`、`critical_findings`（列表）、`files_written`（列表）、`context_used`（列表）、`issues`（列表）。

---

## 禁止事项

- **不准跳过晋升门槛** — 4 项门槛必须逐项检查并记录结果，不得跳过任何一项
- **不准自动晋升** — 必须经过当前环境的用户交互工具用户审批，不得自动将候选添加为新模式
- **不准跳过用户审批归档** — 连续 15 次未命中时必须询问用户，不得自动归档
- **不准降级 manual/curated 模式** — manual/curated 来源永远保持 confidence=high，只更新 hit_count 和 last_hit
- **不准伪造差分证明** — 差分证明必须来自实际的 SSH 输出文件，不得凭记忆编造
- **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"
- **占位符必须替换** — 所有【xxx】占位符必须替换为实际值
- **不准跳过三库一致性检查** — 进化后必须执行三库一致性检查并记录结果

---

## 独立运行参数

```bash
/gencpt-evolve --session-dir /path/to/session
```

可独立于 Pipeline 运行，只需指定 session 目录路径。Pipeline 内运行时在末尾使用 `--evolve` 参数触发。

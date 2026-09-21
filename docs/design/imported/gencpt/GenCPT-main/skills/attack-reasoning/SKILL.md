---
name: attack-reasoning
description: >
  LLM 推理攻击验证。对 Phase 4a 未匹配的 [?] 候选和 Phase 3 发现的高关联度目标，
  使用 LLM 语义推理发现新攻击路径。
  使用场景：Phase 4a 有未匹配信号时。
  不使用场景：Phase 4a 全部匹配、无 [?] 候选。
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

# attack-reasoning — Phase 4b LLM 攻击推理

本 SKILL 负责对 Phase 4a 未匹配的 `[?]` 候选和 Phase 3 发现的高关联度目标，使用 LLM 语义推理发现新攻击路径，补充已知攻击模式库未覆盖的攻击面。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `evidence/attack/pattern-hits.md` | Phase 4a | 已知模式命中结果 |
| `evidence/attack/unmatched_signals.md` | Phase 4a | 未匹配信号列表 |
| `knowledge_graph/edges/cross_ref.json` | Phase 3 | 交叉关联边 |
| `knowledge_graph/nodes/` | Phase 1 | 环境信息 |
| `knowledge_graph/edges/attack.json` | Phase 4a | 已生成的攻击边 |
| `references/attack-surface-model.md` | 本套件 | 7 大攻击面模型 |
| `hypothesis-libraries/attack-hypotheses.md` | 本套件 | 攻击假设库 |
| `episodic_memory/recommendations.md` | 会话记忆 | 历史推荐（影响优先级，不影响检测范围） |

**前置条件校验**：
1. `evidence/attack/unmatched_signals.md` 存在且含 `[?]` 信号（Phase 4a 有未覆盖面）
2. `knowledge_graph/edges/attack.json` 存在（Phase 4a 已完成）
3. `references/attack-surface-model.md` 存在

如 `unmatched_signals.md` 无 `[?]` 信号 → 跳过 Phase 4b，在 `progress.json` 标记为 `skipped`。

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/SSH_COMMANDS.md` | SSH 命令使用规范、执行上下文标注、审批门控、限速与重试 |
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流（4 步）

### 步骤 1：确定推理范围

1. 读取 `evidence/attack/unmatched_signals.md`，收集所有 `[?]` 候选信号
2. 读取 `evidence/cross-ref/prerequisite_signals.md`，获取 Phase 3 高关联度项（标注为 `✅` 或 `⚠️` 但未被 Phase 4a 覆盖的前置条件）
3. 读取 `episodic_memory/recommendations.md`（如有），历史命中影响优先级排序但**不跳过任何检测面**
4. 读取 Knowledge Graph 中 Phase 4a 已覆盖的攻击面列表，确定**未被覆盖**的攻击面
5. 合并信号列表，去除 Phase 4a 已命中项，生成推理目标清单

**关键规则**：看 `unmatched_signals.md` 里有哪些 `[?]` 未匹配信号，看 `attack-surface-model.md` 里 Phase 4a 未覆盖的攻击面，两者合并作为推理范围。情节记忆仅影响优先级排序，不影响检测范围。

---

### 步骤 2：逐攻击面推理

对每个未被 Phase 4a 覆盖的攻击面：

#### 2.1 读取攻击面模型

读取 `references/attack-surface-model.md`，获取该攻击面的：
- 典型攻击路径
- 前置条件
- 探测思路

#### 2.2 基于当前环境构造探测命令

**关键规则**：**不准凭记忆出攻击命令！** 探测命令必须基于当前环境实际状态构造：
1. 读取 `knowledge_graph/nodes/` 中的实际配置信息（Pod 安全上下文、容器配置、SA 权限等）
2. 从环境实际数据推导需要验证的攻击路径
3. 构造针对当前环境的 L0/L1 探测命令（不是通用命令模板）

示例：
- 不准写通用命令"检查是否有特权容器"
- 必须写"检查 pod/backend-api（securityContext.privileged=true 的那个 Pod）是否可通过 cgroup 逃逸"
- 即基于 recon 发现的实际 Pod 名称、实际配置来构造命令

#### 2.3 执行探测命令

按审批门控执行：

| 层级 | 审批级别 | 说明 |
|------|---------|------|
| L0 | 自动通过 | 宿主机观察，只读命令 |
| L1 | 自动通过 | kubectl exec 容器内观察 |
| L2 | 需要确认 | 容器内攻击验证，manual 模式需 question 确认 |
| L3 | 需要确认 | 条件验证，理论分析 |

**区分 Phase 4a 和 4b**：
- Phase 4a 已命中的模式不重复验证
- Phase 4b 的推理聚焦于 4a 未覆盖的攻击面和 4a 未匹配的 `[?]` 信号
- 如推理发现的结果与 4a 已有模式重叠，标记为重复但不丢弃

#### 2.4 生成推理结论

对每个推理验证项：
- 如前置条件满足且差分证明充分 → 生成 ATK-CAND，标记 C1 或 C2
- 如前置条件部分满足 → 生成 ATK-CAND，标记 C3（高风险线索）
- 如前置条件不满足 → 标记 `[-]`，写明证伪依据
- 如被安全机制阻断 → 标记 `[!]`，写明阻断机制

---

### 步骤 3：生成 ATK-CAND

对每个推理发现生成 ATK-CAND：

```json
{
  "id": "ATK-CAND-010",
  "source": "llm_reasoning",
  "attack_surface": "network/lateral-move",
  "target": "pod/frontend-api-xyz",
  "severity": "High",
  "verification_level": "L1",
  "context": "container",
  "confidence": "C3",
  "reasoning": "Pod frontend-api 在命名空间 default 中，无 NetworkPolicy 限制，可访问同一命名空间中 backend-api 的 3306 端口",
  "prerequisites_met": ["no_network_policy", "pod_in_same_namespace"],
  "prerequisites_unmet": ["direct_access_to_sensitive_data"],
  "evidence_files": [
    "evidence/attack/reasoning-hits_raw_ATK-CAND-010_20260619T090000.md"
  ],
  "five_state": "[?]",
  "unmatched_signal_refs": ["K8s-NetworkPolicy-missing"],
  "pattern_overlap": null
}
```

**ATK-CAND 编号规则**：
- **编号必须连续** — 从 Phase 4a 最大编号 +1 开始，无断号
- source 字段标记为 `llm_reasoning`（区别于 Phase 3 的 `cross_ref` 和 Phase 4a 的 `pattern_library`）
- 每个 `[x]` 和 `[?]` 必须有独一无二的 ATK-CAND 编号
- reasoning 字段必须写明 LLM 推理逻辑（不是"可能"，而是基于什么环境数据推导）

---

### 步骤 4：情节记忆记录

所有推理过程写入 `episodic_memory/recommendations.md`：

```markdown
## 会话 {session_id} — Phase 4b 推理记录

### 推理发现 1：ATK-CAND-010
- 攻击面：network/lateral-move
- 推理依据：基于 env_fingerprint 中的 Pod 配置和网络拓扑推导
- 探测命令：kubectl exec -n default frontend-api -- curl -s http://backend-api:3306
- 命中/未命中：命中（C3 高风险线索）
- 关联未匹配信号：K8s-NetworkPolicy-missing

### 推理发现 2：...
```

情节记忆用于跨会话累积：下次会话中类似环境可优先关注。
**重要**：情节记忆仅影响优先级排序，绝不影响检测范围 — 不能因为上次未命中就跳过某个攻击面。

---

## 反幻觉 6 条硬约束（Phase 4b 特别强调）

1. **不准凭记忆出攻击结果** — 推理发现必须基于 Phase 1 侦察数据的实际环境状态，探测命令必须 ssh_execute 真实执行
2. **不准伪造 SSH 输出** — 所有检测结果必须由 ssh_execute 真实执行产生
3. **无证据不写确认态** — 只有差分证明充分才能标记 C1，只有前置条件全部满足才能标记 C2
4. **超出审批范围立即停** — Level 4/5 审批被拒绝时不得继续该攻击路径
5. **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值

**Phase 4b 额外约束**：
- 探测命令必须基于当前环境实际状态构造 — 禁止使用通用命令模板
- ATK-CAND 编号必须与 Phase 3/4a 连续，无断号
- 推理逻辑必须写在 reasoning 字段中，可追溯
- 如推理发现与 Phase 4a 已有模式重叠，标记 pattern_overlap 字段但不丢弃

---

## MUST 输出

Phase 4b 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `evidence/attack/reasoning-hits.md` | LLM 推理命中详情（每个推理发现的验证过程和结论） |
| `evidence/insights.md` | 推理发现摘要（可晋升为攻击模式的洞察） |
| `knowledge_graph/edges/attack.json` | 追加攻击边（source=llm_reasoning），不覆盖 Phase 4a 内容 |
| `episodic_memory/recommendations.md` | 情节记忆推荐记录 |

---

## 检查点

Phase 4b 完成判定需全部通过：

1. **所有 [?] 信号有推理结论** — `unmatched_signals.md` 中的每个 `[?]` 信号都有对应推理结论（`[x]`/`[?]`/`[-]`/`[!]`）
2. **ATK-CAND 编号连续无遗漏** — 从 Phase 4a 最大编号 +1 开始连续，无断号
3. **推理可追溯** — 每个 ATK-CAND 的 reasoning 字段非空，可追溯到环境数据
4. **QA 结构校验通过** — 所有 MUST 输出文件存在且非空，追加的 `attack.json` 边节点引用可找到

---

## WU 摘要格式

每个 WU 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/attack/summaries/{work_unit_id}.json`：

```json
{
  "work_unit_id": "WU-4b-01",
  "status": "complete",
  "summary": "推理 3 个攻击面，发现 2 个新攻击路径（C3×1, C2×1），证伪 1 个",
  "critical_findings": [
    "ATK-CAND-010: lateral-move C3 高风险线索，无 NetworkPolicy 可横向移动",
    "ATK-CAND-011: cloud-metadata C2 条件实证，可访问元数据端点"
  ],
  "files_written": [
    "evidence/attack/reasoning-hits.md",
    "evidence/insights.md",
    "knowledge_graph/edges/attack.json",
    "episodic_memory/recommendations.md"
  ],
  "context_used": [
    "references/attack-surface-model.md",
    "hypothesis-libraries/attack-hypotheses.md",
    "evidence/attack/unmatched_signals.md"
  ],
  "issues": []
}
```

---

## 禁止事项

- **不准凭记忆出攻击命令！** — 探测命令必须基于当前环境实际状态构造，禁止使用通用命令模板
- **不准伪造 SSH 输出** — 所有推理验证结果必须由 ssh_execute 真实执行产生
- **无证据不写确认态** — 只有差分证明充分才能标记 C1
- **ATK-CAND 编号必须连续** — 与 Phase 3/4a 编号连续，无断号
- **反幻觉 6 条硬约束全部适用** — 详见上方"反幻觉 6 条硬约束"章节
- **情节记忆不跳过检测面** — 历史推荐仅影响优先级，不影响检测范围
- **不覆盖 Phase 4a 结果** — `attack.json` 采用追加方式，不覆盖 Phase 4a 生成的边

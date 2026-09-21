---
name: cross-ref
description: >
  合规-攻击交叉关联分析。将合规违规、攻击假设、环境信息交叉比对，发现风险叠加和高优先级攻击面。
  使用场景：Phase 2 完成后，Phase 4 之前。
  不使用场景：Phase 2 跳过时、只做单点分析。
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

# cross-ref — Phase 3 交叉关联分析

本 SKILL 负责将合规违规结果、攻击假设库、侦察环境信息进行交叉比对，发现风险叠加放大和高优先级攻击面，为 Phase 4 攻击验证提供精准的目标排序。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `knowledge_graph/nodes/` | Phase 1a | 环境信息（hosts.json、pods.json、containers.json 等） |
| `knowledge_graph/edges/compliance.json` | Phase 2（汇总后）| 合规边（含判定结果）。由 `compliance_k8s.json` + `compliance_docker.json` + `compliance_containerd.json` 汇总而来；若汇总文件不存在则直接 Read 三个平台分片文件合并 |
| `knowledge_graph/nodes/findings.json` | Phase 2（汇总后）| 合规违规发现节点。由 `findings_k8s.json` + `findings_docker.json` + `findings_containerd.json` 汇总而来；若汇总文件不存在则直接 Read 三个平台分片文件合并 |
| `evidence/compliance/*/results.json` | Phase 2 | 各引擎合规检测结果详情（k8s / docker / containerd 三个独立目录，按 scope 读取存在的引擎） |
| `hypothesis-libraries/compliance-hypotheses.md` | 本套件 | 合规假设映射库 |
| `hypothesis-libraries/attack-hypotheses.md` | 本套件 | 攻击假设库 |
| `hypothesis-libraries/cross-ref-queries.md` | 本套件 | 交叉关联查询模板 |

**前置条件校验**：
1. Phase 2 至少一个引擎的 `results.json` 存在且非空
2. `knowledge_graph/edges/compliance.json` 存在且含合规边（或 `compliance_k8s.json` / `compliance_docker.json` / `compliance_containerd.json` 中至少一个非空；若仅有分片文件，Phase 3 启动时先用 `jq -s 'add'` 汇总为 `compliance.json` 后再读）
3. 三个假设库文件都存在且非空
4. `knowledge_graph/nodes/findings.json` 存在（或 `findings_k8s.json` / `findings_docker.json` / `findings_containerd.json` 中至少一个非空；若仅有分片文件，Phase 3 启动时先用 `jq -s 'add'` 汇总为 `findings.json` 后再读）

**Phase 2 汇总补救**：若 Phase 3 启动时发现仅有平台分片而无汇总文件，先执行：
```bash
jq -s 'add' findings_k8s.json findings_docker.json findings_containerd.json > findings.json 2>/dev/null || \
  jq -s 'add' $(ls findings_*.json 2>/dev/null) > findings.json
jq -s 'add' compliance_k8s.json compliance_docker.json compliance_containerd.json > compliance.json 2>/dev/null || \
  jq -s 'add' $(ls compliance_*.json 2>/dev/null) > compliance.json
```
缺失 scope 对应的分片文件时跳过该分片（不报错）。

任一前置条件不满足 → 立即终止，在 `progress.json` 标记 Phase 3 为 `blocked`。

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流（4 步）

### 步骤 1：读取输入数据

按以下顺序读取，遵循按需读取原则：

1. 读取 `evidence/compliance/k8s/results.json`（如 scope 含 k8s）
2. 读取 `evidence/compliance/docker/results.json`（如 scope 含 docker）
3. 读取 `evidence/compliance/containerd/results.json`（如 scope 含 containerd）
4. 读取 `knowledge_graph/nodes/findings.json`
5. 读取 `knowledge_graph/edges/compliance.json`
6. 读取 `knowledge_graph/nodes/` 下所有节点文件（按需）
7. 读取 `hypothesis-libraries/compliance-hypotheses.md`
8. 读取 `hypothesis-libraries/attack-hypotheses.md`
9. 读取 `hypothesis-libraries/cross-ref-queries.md`
10. 读取 `evidence/recon/recon_summary.md`（提取关键发现摘要）

**写盘规则**：读取后立即提取需要的字段，原始内容不在上下文中累积。每个 WU 完成后立即写盘分析结果。

---

### 步骤 2：执行 3 条核心查询

#### XREF-001：合规违规 → 攻击假设前置条件映射

**目的**：找出哪些合规违规满足了哪些攻击的前置条件

**输入**：Phase 2 合规结果 + `compliance-hypotheses.md`

**执行逻辑**：
1. 遍历所有 `fail` 和 `warn` 的合规规则
2. 对每条 fail/warn 规则，在 `compliance-hypotheses.md` 中匹配违规族
3. 对命中的 CHK-CAND 卡片，关联到 `attack-hypotheses.md` 中对应的 ATK-HYP
4. 对每个 ATK-HYP，标记五态：
   - `[x]` — fail 规则映射到攻击假设，前置条件可能满足
   - `[?]` — warn 规则或部分满足
   - `[-]` — 合规通过或证伪
   - `[!]` — 环境干扰，无法判定
   - `[ ]` — 未检查（过程态）
5. **LLM 动态补充推理**（弥补静态假设库的覆盖盲区）：
   - **输入**：所有 fail/warn 规则列表 + 所有攻击模式 SKILL.md 的"## 1. 前置条件"字段
   - **执行逻辑**：LLM 语义模糊匹配——对每条 fail/warn 规则，语义判断是否满足某个攻击模式的前置条件（即使静态假设库未收录该映射）
   - **输出**：标记为 `[?] LLM推理关联`，source 标记为 `llm_reasoning`
   - **优先级**：静态库命中（步骤2-3）优先级更高；LLM 推理结果为补充，需 Phase 4a 额外验证
- **token 预算**：此步骤 ≤3000 tokens（读取49个模式的前置条件字段）
    - **约束**：不生成攻击命令；只产生关联映射建议
    - **落盘**：LLM动态推理结果写入 `evidence/cross-ref/llm_reasoning.json`，格式为[{rule_id, pattern_name, source: 'llm_reasoning', confidence: 'low'}]

**输出格式示例**：
```
合规违规 → 攻击假设映射：
  K8s-5.2.1(fail) → CHK-CAND-002 → escape/socket-escape (ATK-HYP-001)
    标记: [x] 前置条件可能满足
    ATK-CAND-001: 特权容器+docker.sock逃逸
  K8s-3.2.1(fail) → CHK-CAND-004 → auth/k8s-rbac-abuse (ATK-HYP-002)
    标记: [x] 前置条件可能满足
    ATK-CAND-002: RBAC过宽提权
```

#### XREF-002：叠加放大（≥3 种违规叠加 → 风险放大）

**目的**：同一目标多种违规叠加，风险放大

**输入**：Phase 2 合规结果 + `compliance-hypotheses.md` + 节点信息

**执行逻辑**：
1. 按目标（Pod/Node/容器）分组合规违规
2. 统计每个目标的违规叠加数量
3. 叠加 ≥3 → 标记为风险放大节点，优先处理
4. 叠加 = 2 → 标记为次级关注
5. 叠加 = 1 → 标记为常规关注

**输出格式示例**：
```
叠加风险分析：
  目标 pod/backend-api-xyz:
    违规数: 4 (K8s-5.2.1 + K8s-5.2.3 + NetworkPolicy缺失 + K8s-3.2.1)
    放大评级: CRITICAL
    触发攻击假设: ATK-HYP-001 + ATK-HYP-002 + ATK-HYP-003
    ATK-CAND-003: 特权容器+dockersock+无网络策略+RBAC过宽(四重叠加)
```

#### XREF-003：攻击假设前置条件 → 侦察结果比对

**目的**：将攻击假设的前置条件与侦察结果比对，判断前置条件是否被满足

**输入**：`attack-hypotheses.md` + Phase 1 侦察数据

**执行逻辑**：
1. 遍历所有 ATK-HYP 卡片
2. 逐条前置条件，在 `evidence/recon/` 和 `knowledge_graph/nodes/` 中搜索验证证据
3. 标记每条前置条件：
   - `✅` 已满足 — 侦察结果直接确认
   - `❌` 不满足 — 侦察结果直接证伪
   - `⚠️` 部分满足 — 有证据但不确定
   - `❓` 需进一步探测 — 无直接证据，需 Phase 4 验证
4. 对全部 `✅` 或 `⚠️` 的 ATK-HYP，生成 ATK-CAND 编号

**输出格式示例**：
```
前置条件比对：
  ATK-HYP-001 (docker.sock 逃逸):
    "容器内可见 docker.sock": ✅ 侦察确认存在 (pods.json: backend-api securityContext.privileged=true)
    "有读写权限": ⚠️ 权限未知，需探测
    → ATK-CAND-004: docker.sock逃逸(需探测读写权限)

  ATK-HYP-002 (RBAC 提权):
    "SA 有超权限": ❌ auth can-i 显示无创建权限
    → 标记 [-] 已证伪 (evidence: kubectl auth can-i 输出)
```

---

### 步骤 3：五态标记与 ATK-CAND 生成

对每条合规 fail/warn 生成五态标记：

| 标记 | 含义 | 必须动作 |
|------|------|---------|
| `[x]` | 存在明确候选，必须深审 | **必须生成 ATK-CAND 编号** |
| `[?]` | 存在可疑面，必须深审 | **必须生成 ATK-CAND 编号**，交给 Phase 4b 处理 |
| `[-]` | 已检查，无候选/不适用 | 写明证伪依据（哪条侦察结果或合规通过判定） |
| `[!]` | 已检查，被防护阻断 | 写明阻断机制（AppArmor/Seccomp/NetworkPolicy 等） |
| `[ ]` | 未检查（过程态） | 最终报告前**必须消灭**，不能留空 |

**ATK-CAND 编号规则**：
- 格式：`ATK-CAND-NNN`
- 从 001 开始连续编号，无遗漏
- source 字段标记为 `cross_ref`（区别于 Phase 4a 的 `pattern_library` 和 Phase 4b 的 `llm_reasoning`）
- 每个 `[x]` 和 `[?]` 必须有独一无二的 ATK-CAND 编号

**ATK-CAND 记录格式**：
```json
{
  "id": "ATK-CAND-001",
  "source": "cross_ref",
  "attack_surface": "escape/socket-escape",
  "target": "pod/backend-api-xyz",
  "severity": "Critical",
  "trigger_rules": ["K8s-5.2.1", "K8s-5.2.3"],
  "hypothesis_refs": ["CHK-CAND-002", "ATK-HYP-001"],
  "prerequisite_status": {
    "docker.sock_visible": "confirmed",
    "docker.sock_writable": "unknown"
  },
  "five_state": "[x]",
  "cross_ref_queries": ["XREF-001", "XREF-002"]
}
```

---

### 步骤 4：写入知识图谱边和输出文件

#### 4.1 知识图谱边

写入 `knowledge_graph/edges/cross_ref.json`（顶层 JSON 数组）：

```json
[
  {
    "edge_type": "cross_ref",
    "from_node": "compliance-K8s-5.2.1",
    "to_node": "attack-socket-escape",
    "attrs": {
      "query": "XREF-001",
      "severity": "Critical",
      "amplification": false
    },
    "timestamp": "2026-06-19T08:42:00Z"
  },
  {
    "edge_type": "cross_ref",
    "from_node": "target-pod/backend-api-xyz",
    "to_node": "amplification-node",
    "attrs": {
      "query": "XREF-002",
      "violation_count": 4,
      "amplification_level": "CRITICAL"
    },
    "timestamp": "2026-06-19T08:42:00Z"
  }
]
```

同时生成/更新 `knowledge_graph/edges/_index.md` 追加交叉关联边索引。

#### 4.2 输出文件

| 文件 | 说明 |
|------|------|
| `evidence/cross-ref/cross_ref_summary.md` | 三条核心查询结果汇总 |
| `evidence/cross-ref/risk_amplification.md` | 叠加放大分析详情 |
| `evidence/cross-ref/prerequisite_signals.md` | 前置条件信号比对详情 |
| `evidence/cross-ref/history_priority.md` | 情节记忆优先级影响 |

---

## MUST 输出

Phase 3 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `knowledge_graph/edges/cross_ref.json` | 交叉关联边（非空，含 XREF-001/002/003 结果） |
| `evidence/cross-ref/cross_ref_summary.md` | 交叉关联汇总（非空） |
| `evidence/cross-ref/risk_amplification.md` | 叠加放大详情（非空） |
| `evidence/cross-ref/prerequisite_signals.md` | 前置条件信号（非空） |
| `evidence/cross-ref/history_priority.md` | 情节记忆优先级影响（非空） |
| `evidence/cross-ref/llm_reasoning.json` | LLM 动态补充推理结果（非空） |

---

## 检查点

Phase 3 完成判定需全部通过：

1. **每条合规 fail/warn 有交叉关联判定** — 对 Phase 2 的每条 fail/warn 规则，都有对应的五态标记和 ATK-CAND（如适用）
2. **ATK-CAND 编号连续无遗漏** — 从 001 开始连续，无断号
3. **QA 结构校验通过** — 所有 MUST 输出文件存在且非空，`cross_ref.json` 中每条边的 `from_node` 和 `to_node` 能在 `knowledge_graph/nodes/` 和已有边文件中找到对应节点

---

## 禁止事项

- **不执行攻击命令**：cross-ref 只做关联分析，不做 L1/L2 验证
- **不伪造关联结果**：XREF 查询结果必须基于 Phase 2 合规数据和 Phase 1 侦察数据，禁止凭记忆推断
- **不遗漏合规违规**：每条 fail/warn 都必须有对应判定
- **不跳过叠加分析**：同一目标叠加 ≥3 种违规时必须标记风险放大
- **不在上下文中累积原始数据**：分析结果立即写盘
- **不省略 ATK-CAND**：每个 `[x]` 和 `[?]` 必须生成 ATK-CAND 编号

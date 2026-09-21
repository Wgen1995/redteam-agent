---
name: report-attack
description: >
  攻击验证报告生成。读取Phase 4-7攻击数据，生成MD+JSON格式攻击报告和POC包。
  使用场景：Phase 4-7完成后生成报告。
  不使用场景：合规检测阶段。
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

# Phase 8b — 攻击验证报告生成

## 核心职责

读取 Phase 4-7 攻击验证数据，生成攻击报告和 POC 包。攻击报告包含所有 ATK-CAND 的详细信息，包括可信度分级、执行上下文、攻击链分析和 POC 引用。

## 关键概念

### 可信度分级（5.16.4节）

每条 ATK-CAND 必须标注可信度：

| 可信度 | 标记 | 含义 | 对应验证程度 | 证据要求 |
|--------|------|------|-------------|---------|
| C1 实证复现 | ✅✅ 已确认-可复现 | 实际执行攻击路径，差分证明成功 | confirmed | 5项门槛全满足 + L2执行上下文差分证明 |
| C2 条件实证 | ✅ 已确认-条件成立 | 前置条件满足，理论链路完整 | condition_met | 前置条件全部列举 + 理论链路清晰 + 不可复现原因 |
| C3 风险线索 | ⚠️ 高风险线索 | 配置存在安全隐患但前置条件不完全满足 | high_risk_clue | 配置证据 + 风险分析 + 建议补充验证 |

### 执行上下文层级（5.16.3节）

| 层级 | 名称 | 说明 |
|------|------|------|
| L0 | 宿主机观察 | SSH到宿主机执行，用于发现前置条件和收集配置 |
| L1 | 容器内观察 | kubectl exec进入目标Pod，验证攻击者视角可见性 |
| L2 | 容器内攻击验证 | kubectl exec执行攻击命令，实际复现漏洞路径 |
| L3 | 条件验证 | 不执行破坏性命令，条件组合+理论分析 |

每条 ATK-CAND 的探测和攻击步骤都标注执行上下文。

### 漏洞来源标识（第7/8节）

| 来源标识 | 含义 | 报告中显示 |
|---------|------|-----------|
| pattern_library | Phase 4a 从已知模式库匹配 | 📚 已知攻击模式库 ({模式名}) |
| llm_reasoning | Phase 4b LLM 推理发现 | 🧠 LLM 推理分析 (Phase 4b) |
| learned | 已晋升的学习模式 | 🔄 学习模式 ({模式名}, promoted {日期}) |

## 核心工作流（4 步）

### 步骤1：读取攻击数据

读取 `evidence/attack/` 目录：

- `evidence/attack/pattern-hits.md` — Phase 4a 已知模式命中结果
- `evidence/attack/reasoning-hits.md` — Phase 4b LLM 推理命中结果
- `evidence/attack/unmatched_signals.md` — 无法匹配任何现有模式的信号
- `evidence/attack/insights.md` — Phase 4b LLM 推理发现摘要

### 步骤2：读取攻击链和POC数据

- `evidence/chains/chain_builder.md` — 攻击链构建数据
- `evidence/chains/chain_verification.md` — 攻击链验证数据
- `evidence/poc/poc_scripts/` — POC 脚本目录
- `evidence/poc/poc_readme.md` — POC 使用说明
- `knowledge_graph/edges/attack.json` — 攻击边数据

### 步骤3：生成攻击报告 MD

生成 `reports/attack_report.md`，包含以下章节：

#### 3.1 ATK-CAND 汇总表

```markdown
## ATK-CAND 汇总

| 编号 | 来源 | 攻击面 | 可信度 | 状态 | 目标 |
|------|------|--------|--------|------|------|
| ATK-CAND-001 | 📚 socket-escape | AS-1 逃逸 | C1 实证复现 ✅✅ | confirmed | pod/backend-api |
| ATK-CAND-002 | 🧠 LLM推理 (Phase 4b) | AS-2 认证 | C2 条件实证 ✅ | condition_met | sa/default |
| ATK-CAND-003 | 🔄 nsproxy-escape (promoted 2026-06) | AS-1 逃逸 | C3 风险线索 ⚠️ | high_risk_clue | pod/privileged-pod |
| ATK-CAND-004 | — | AS-1 逃逸 | ➖ 已证伪 | disproved | pod/frontend-web |
| ATK-CAND-005 | — | AS-5 拒绝服务 | 🛑 已阻断 | blocked | pod/resource-pod |
```

来源列格式：
- 📚 已知攻击模式库 → 显示 `{模式slug}`
- 🧠 LLM 推理分析 → 显示 `Phase 4b`
- 🔄 学习模式 → 显示 `{模式slug} (promoted {日期})`
- 不可利用/已阻断 → 显示 `—`

可信度列格式：
- C1 → `C1 实证复现 ✅✅`
- C2 → `C2 条件实证 ✅`
- C3 → `C3 风险线索 ⚠️`
- 不可利用 → `➖ 已证伪`
- 已阻断 → `🛑 已阻断`

#### 3.2 每个ATK-CAND详细结果

每个 ATK-CAND 独立章节，包含：

```markdown
### ATK-CAND-001: 容器通过docker.sock逃逸至宿主机

- **来源**: 📚 已知攻击模式库 (socket-escape)
- **可信度**: C1 实证复现 ✅✅
- **攻击面**: AS-1 逃逸攻击面
- **目标**: pod/backend-api (namespace: production)
- **执行上下文**: L0 + L1 + L2

#### 前置条件验证

| 步骤 | 层级 | 命令 | 期望 | 实际 | 结果 |
|------|------|------|------|------|------|
| 1 | [L0] | kubectl get pod xxx -o jsonpath='{.spec.securityContext.privileged}' | true | true | ✅ 满足 |
| 2 | [L1] | kubectl exec xxx -- ls -la /var/run/docker.sock | 文件存在 | 文件存在 | ✅ 满足 |

#### 攻击验证

| 步骤 | 层级 | 命令 | 输出 | 含义 |
|------|------|------|------|------|
| 1 | [L1] | kubectl exec xxx -- docker ps | 列出容器 | 可执行docker命令 |
| 2 | [L2] | kubectl exec xxx -- docker run -v /:/host alpine ls /host/etc/shadow | root:x:0:0:... | 可读取宿主机文件 |

#### 差分证明

| 状态 | 观测项 | 层级 |
|------|--------|------|
| 攻击前 | 宿主机无异常容器 | [L0] |
| 攻击后 | 可从容器内读取宿主机/etc/shadow | [L2] |

#### 审批状态

- 审批级别: Level 4（逃逸验证）
- 审批结果: auto通过
```

**关键要求**：
- C1 实证复现项：前置条件 + [L0]/[L1] 探测 + [L2] 攻击验证 + 差分证明
- C2 条件实证项：前置条件全部列举 + 理论链路 + 不可安全复现原因或阻断机制名称
- C3 风险线索项：配置证据 + 风险分析 + 建议补充验证
- 不可利用项：**必须包含**，标注"已检查不可利用 + 证伪依据"，附 L0 证伪依据
- 已阻断项：**必须包含**，标注阻断机制名称（AppArmor/Seccomp/NetworkPolicy 等），附 L1 阻断证据

#### 3.3 攻击链分析

```markdown
## 攻击链分析

### CHAIN-001: 容器逃逸→宿主机访问→密钥窃取

| 步骤 | ATK-CAND | 来源 | 状态 | 影响 |
|------|----------|------|------|------|
| 1 | ATK-CAND-001 | 📚 socket-escape | confirmed | 容器逃逸至宿主机 |
| 2 | ATK-CAND-002 | 🧠 Phase 4b | condition_met | 读取K8s Secret |

- **置信度**: 0.92
- **影响**: 从业务容器出发，经Docker套接字逃逸至宿主机，再利用ServiceAccount权限窃取集群Secret
- **验证状态**: verified
```

#### 3.4 POC 包引用

```markdown
## POC 包

| ATK-CAND | POC脚本 | 可信度 | 说明 |
|----------|---------|--------|------|
| ATK-CAND-001 | poc_scripts/ATK-CAND-001_docker_sock_escape.sh | C1 实证复现 | 完整POC，可执行 |
| ATK-CAND-002 | poc_scripts/ATK-CAND-002_sa_token_exfil.sh | C2 条件实证 | 条件验证POC |

详细POC使用说明见 poc_readme.md，POC脚本位于 reports/poc_package/ 目录。
```

### 步骤4：生成攻击报告 JSON

生成 `reports/attack_report.json`，结构如下：

```json
{
  "report_type": "attack_verification",
  "session_id": "sess-xxx",
  "generated_at": "2026-xx-xx",
  "summary": {
    "total_atk_cand": 0,
    "c1_confirmed": 0,
    "c2_condition_met": 0,
    "c3_high_risk_clue": 0,
    "disproved": 0,
    "blocked": 0,
    "by_source": {
      "pattern_library": 0,
      "llm_reasoning": 0,
      "learned": 0
    },
    "by_attack_surface": {
      "AS-1_escape": 0,
      "AS-2_auth": 0,
      "AS-3_network": 0,
      "AS-4_data": 0,
      "AS-5_dos": 0,
      "AS-6_supply": 0,
      "AS-7_persist": 0
    }
  },
  "atk_cands": [
    {
      "id": "ATK-CAND-001",
      "source": "pattern_library",
      "source_display": "📚 已知攻击模式库 (socket-escape)",
      "attack_surface": "AS-1_escape",
      "confidence": "C1",
      "confidence_display": "C1 实证复现 ✅✅",
      "status": "confirmed",
      "target": "pod/backend-api",
      "execution_contexts": ["L0", "L1", "L2"],
      "prerequisites": [
        {
          "step": 1,
          "context": "L0",
          "command": "...",
          "expected": "...",
          "actual": "...",
          "satisfied": true
        }
      ],
      "attack_steps": [
        {
          "step": 1,
          "context": "L1",
          "action": "...",
          "command": "...",
          "output": "...",
          "meaning": "..."
        }
      ],
      "differential_proof": [
        {
          "state": "before",
          "observation": "...",
          "context": "L0"
        },
        {
          "state": "after",
          "observation": "...",
          "context": "L2"
        }
      ],
      "approval_level": 4,
      "approval_result": "auto",
      "blocking_mechanism": null
    }
  ],
  "chains": [
    {
      "chain_id": "CHAIN-001",
      "confidence": 0.92,
      "status": "verified",
      "steps": [
        {
          "step": 1,
          "atk_cand_id": "ATK-CAND-001",
          "source": "pattern_library",
          "status": "confirmed"
        }
      ],
      "impact": "..."
    }
  ],
  "poc_refs": [
    {
      "atk_cand_id": "ATK-CAND-001",
      "script_path": "poc_scripts/ATK-CAND-001_docker_sock_escape.sh",
      "confidence": "C1",
      "description": "..."
    }
  ]
}
```

同时将 `evidence/poc/` 的内容复制到 `reports/poc_package/`：

- 复制 `evidence/poc/poc_scripts/` → `reports/poc_package/poc_scripts/`
- 复制 `evidence/poc/poc_readme.md` → `reports/poc_package/poc_readme.md`

## MUST 输入

| 输入 | 路径 | 说明 |
|------|------|------|
| 模式命中结果 | evidence/attack/pattern-hits.md | Phase 4a 数据 |
| 推理命中结果 | evidence/attack/reasoning-hits.md | Phase 4b 数据 |
| 未匹配信号 | evidence/attack/unmatched_signals.md | 无法匹配的信号 |
| LLM推理摘要 | evidence/attack/insights.md | Phase 4b 洞察 |
| 攻击链构建 | evidence/chains/chain_builder.md | Phase 5 数据 |
| 攻击链验证 | evidence/chains/chain_verification.md | Phase 6 数据 |
| POC脚本 | evidence/poc/poc_scripts/ | Phase 7 产出 |
| POC说明 | evidence/poc/poc_readme.md | Phase 7 产出 |
| 攻击边数据 | knowledge_graph/edges/attack.json | 知识图谱 |

## MUST 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 攻击报告 MD | reports/attack_report.md | ATK-CAND详情+链分析+POC引用 |
| 攻击报告 JSON | reports/attack_report.json | 结构化数据 |
| POC包 | reports/poc_package/ | 复制自evidence/poc/ |

## 反幻觉硬约束

1. 不准凭记忆出攻击结果 — 每条ATK-CAND必须来自evidence/attack/下的实际数据
2. 不准伪造SSH输出 — 所有探测和攻击步骤的输出必须来自results.json或SSH执行记录
3. 无证据不写确认态 — C1必须满足5项门槛+L2差分证明，C2必须有前置条件列举
4. 超出审批范围立即停 — L5被拒绝的路径不得在报告中标注为confirmed
5. 省略词零容忍 — 不出现"等"、"..."、"+N"、大致、约
6. 占位符必须替换 — 所有【xxx】占位符替换为实际值

## 关键要求

### 不可利用项必须包含

不可利用（已证伪）项**必须出现在报告中**，标注"已检查不可利用 + 证伪依据"，并附至少L0的证伪依据。不可利用项的值：
- 可信度列：`➖ 已证伪`
- 来源列：显示原始攻击面和探测过程
- 证伪依据：哪条命令的输出证明前置条件不满足

### 已阻断项必须包含

已阻断项**必须出现在报告中**，标注阻断机制名称。已阻断项的值：
- 可信度列：对应C2条件实证子情况
- 阻断机制：AppArmor/Seccomp/NetworkPolicy 等具体机制名称
- 阻断证据：至少L1的阻断证据

### 每条ATK-CAND必须标注

- 可信度（C1/C2/C3/不可利用/已阻断）
- 执行上下文（L0/L1/L2/L3，标注每步的层级）
- 来源（📚/🧠/🔄）
- 审批状态

## 独立运行参数

```
/gencpt-report-attack --session-dir /path/to/session
```

## 与其他技能的依赖

- 上游：attack-pattern(4a)、attack-reasoning(4b)、chain-builder(5)、chain-verify(6)、poc-generator(7)
- 下游：report-summary(8c) 读取本技能输出作为综合报告输入
- 并行：与 report-compliance(8a) 无依赖，可并行执行

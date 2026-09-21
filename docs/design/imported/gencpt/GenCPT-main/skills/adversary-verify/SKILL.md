---
name: adversary-verify
description: >
  对抗性验证（红队证伪）。独立子代理对 C1 结论做定向证伪尝试。
  使用场景：Phase 6 链验证完成后、Phase 7 POC 生成前。
  不使用场景：无 C1 ATK-CAND 时跳过。
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

# adversary-verify — Phase 6.5 对抗性验证（红队证伪）

本 SKILL 负责对 Phase 6 链验证中标记为 `confirmed` 且 `confidence=C1` 的 ATK-CAND 做独立证伪尝试。由独立子代理（Task(general)）执行，不共享 Phase 6 上下文，只做只读 L0/L1 验证，不执行攻击 L2。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `evidence/chains/chain_verification.json` | Phase 6 | 链验证结果（含每条链的可信度+审批记录+差分证明引用） |
| `knowledge_graph/edges/attack.json` | Phase 4a/4b | 攻击边（含 status、confidence、evidence_files） |
| `knowledge_graph/nodes/` | Phase 1 | 环境信息（pods.json、containers.json 等，用于只读验证） |

**前置条件校验**：
1. `evidence/chains/chain_verification.json` 存在且非空（Phase 6 已完成）
2. `knowledge_graph/edges/attack.json` 存在且含至少一条 `confidence=C1` 的边
3. 无 C1 ATK-CAND 时 → 跳过 Phase 6.5，在 `progress.json` 标记为 `skipped`

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/SSH_COMMANDS.md` | SSH 命令使用规范、执行上下文标注、审批门控、限速与重试 |
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流（3 步）

### 步骤 1：筛选验证目标

1. 读取 `evidence/chains/chain_verification.json`，提取所有链的步骤验证结果
2. 读取 `knowledge_graph/edges/attack.json`，筛选 `status=confirmed` 且 `confidence=C1` 的 ATK-CAND
3. 对每个 C1 ATK-CAND，提取其 `evidence_files`（差分证明文件路径）
4. 生成证伪目标清单：

```json
{
  "adversary_targets": [
    {
      "atk_cand": "ATK-CAND-001",
      "chain_id": "CHAIN-001",
      "step": 1,
      "attack_name": "socket-escape",
      "target_node": "pod/backend-api-xyz",
      "confidence": "C1",
      "evidence_files": [
        "evidence/attack/raw/attack-pattern_ATK-CAND-001_pre_20260619T084200.md",
        "evidence/attack/raw/attack-pattern_ATK-CAND-001_post_20260619T084200.md"
      ]
    }
  ]
}
```

**无 C1 目标时**：写空报告并跳过后续步骤，在 `progress.json` 标记 Phase 6.5 为 `skipped`。

---

### 步骤 2：逐个 C1 定向证伪

对每个 C1 ATK-CAND，由独立子代理（Task(general)）执行证伪尝试。**子代理独立调度，不共享 Phase 6 上下文**，只接收证伪目标清单和 KG 路径。

#### 2a. 读取差分证明记录

1. Read 证伪目标的 `evidence_files`（pre/post 快照）
2. 提取差分证明中的关键判定依据：
   - 攻击前快照中观测到的"正常状态"
   - 攻击后快照中观测到的"异常状态"
   - 攻击方声称的差分差异点

#### 2b. 识别最弱环节

分析差分证明，寻找最可能被证伪的环节：

| 环节类型 | 证伪角度 | 检查方法 |
|---------|---------|---------|
| 前置条件 | 前置条件是否真正满足 | 重新 SSH 只读 L0/L1 验证前置条件 |
| 差分逻辑 | 攻击前后差异是否由攻击引起 | 检查是否有其他原因导致相同差异 |
| 安全机制 | 是否有被遗漏的安全机制 | 检查 seccompProfile / AppArmor / NetworkPolicy / OPA |
| 证据自洽 | pre/post 快照是否真实 | 重新 SSH 收集当前状态，对比快照是否合理 |

#### 2c. 重新 SSH 验证（只读 L0/L1）

**只做只读验证，不执行攻击 L2**：

1. 对目标节点执行只读 L0 命令（如 `kubectl get pod <name> -n <ns> -o json`）
2. 对目标容器执行只读 L1 命令（如 `kubectl exec <pod> -- cat /proc/1/status`）
3. 检查安全机制：
   - `seccompProfile` 是否阻断攻击所需的系统调用（如 nsenter 需要 `setns`）
   - `AppArmor` profile 是否限制了攻击所需的 capability
   - `NetworkPolicy` 是否隔离了攻击所需的网络路径
   - OPA/Kyverno 准入控制是否拦截了攻击所需的资源创建
4. 所有 SSH 输出**立即写盘**到 `evidence/chains/raw/`，五元组标注

#### 2d. 判定证伪结果

基于重新验证的结果，对每个 C1 ATK-CAND 做以下判定之一：

| 判定 | 标记 | 含义 | 条件 |
|------|------|------|------|
| upheld | ✅ 维持 | C1 判定成立 | 重新验证未发现证伪证据，差分证明逻辑自洽 |
| overturned | ❌ 推翻 | C1 判定不成立 | 发现安全机制阻断、前置条件实际不满足、或差分证明有逻辑缺陷 |
| inconclusive | ⚠️ 存疑 | 无法判定 | 重新验证结果矛盾或不足以下结论 |

**overturned 必须附 SSH 输出证据**：
- 写明推翻依据（哪条命令、什么输出）
- 写明推翻类型（安全机制阻断 / 前置条件不满足 / 差分逻辑缺陷）

---

### 步骤 3：写盘

#### 3a. 写入 adversary_verification.md

```markdown
# 对抗性验证报告（Phase 6.5）

## 验证概要

| ATK-CAND | 攻击名 | 链 | 判定 | 推翻依据 |
|----------|--------|-----|------|---------|
| ATK-CAND-001 | socket-escape | CHAIN-001 | ✅ upheld | — |
| ATK-CAND-005 | secret-exfil | CHAIN-001 | ❌ overturned | seccompProfile 阻断 setns |
| ATK-CAND-007 | lateral-move | CHAIN-001 | ⚠️ inconclusive | NetworkPolicy 部分隔离 |

## ATK-CAND-001 证伪详情

### 差分证明审查
- 攻击前快照：[L0] docker ps 无异常容器
- 攻击后快照：[L0] docker ps 新增 alpine 容器
- 差分逻辑：攻击方声称 docker.sock 挂载导致逃逸

### 重新验证
- [L0] `kubectl get pod backend-api -n production -o json` → securityContext.privileged: true
- [L1] `kubectl exec backend-api -- ls -la /var/run/docker.sock` → docker.sock 存在且可读写
- [L0] `kubectl get pod backend-api -n production -o jsonpath='{.spec.securityContext.seccompProfile}'` → 未设置
- [L0] AppArmor 检查 → 未应用 profile

### 判定
✅ upheld — 前置条件确实满足，无安全机制阻断，差分证明逻辑自洽

## ATK-CAND-005 证伪详情
...
### 判定
❌ overturned — seccompProfileRuntimeDefault 阻断了 setns 系统调用，Phase 6 未检测到此安全机制
- 推翻证据：evidence/chains/raw/adversary-verify_ATK-CAND-005_seccomp_20260620T110000.md
```

#### 3b. 写入 adversary_verification.json

```json
{
  "session_id": "sess-xxx",
  "phase": "6.5",
  "generated_at": "2026-06-20T11:30:00Z",
  "adversary_results": [
    {
      "atk_cand": "ATK-CAND-001",
      "chain_id": "CHAIN-001",
      "step": 1,
      "verdict": "upheld",
      "overturn_reason": null,
      "evidence_files": [
        "evidence/chains/raw/adversary-verify_ATK-CAND-001_recheck_20260620T110000.md"
      ]
    },
    {
      "atk_cand": "ATK-CAND-005",
      "chain_id": "CHAIN-001",
      "step": 2,
      "verdict": "overturned",
      "overturn_reason": "seccompProfileRuntimeDefault 阻断 setns 系统调用",
      "overturn_type": "security_mechanism",
      "evidence_files": [
        "evidence/chains/raw/adversary-verify_ATK-CAND-005_seccomp_20260620T110000.md"
      ]
    }
  ]
}
```

#### 3c. overturned 时更新 attack.json

对每个 `verdict=overturned` 的 ATK-CAND，更新 `knowledge_graph/edges/attack.json` 中对应边的 `confidence`：
- `C1` → `C2`（降级，不是删除）
- 追加 `attrs.adversary_overturned: true`
- 追加 `attrs.adversary_reason: "{推翻依据}"`
- 追加 `attrs.adversary_evidence: "{证据文件路径}"`

**约束**：
- 只降级不删除 — overturned 的 ATK-CAND 仍然存在，只是可信度降级
- 原始证据保留 — 不删除原有差分证明文件
- 更新时遵循 KG 节点存在性校验（本 Phase 通用约束）

---

## MUST 输出

Phase 6.5 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**（skipped 时写空报告并标注 skipped）：

| 文件 | 说明 |
|------|------|
| `evidence/chains/adversary_verification.md` | 对抗性验证详细报告（每个 C1 的证伪过程和结论） |
| `evidence/chains/adversary_verification.json` | 结构化验证结果（每个 C1 的 verdict + 推翻依据 + 证据引用） |

---

## 反幻觉约束

1. **独立调度不共享 Phase 6 上下文** — 子代理只接收证伪目标清单和 KG 路径，不接收 Phase 6 的判定过程
2. **只做只读 L0/L1 不执行攻击 L2** — 证伪只重新验证前置条件和安全机制，不重新执行攻击
3. **overturned 必须附 SSH 输出证据** — 不准凭记忆判定推翻，必须有重新验证的 SSH 输出
4. **不准凭记忆判定** — upheld/overturned/inconclusive 都必须基于重新验证的 SSH 输出，不是基于 Phase 6 的结论
5. **不准伪造 SSH 输出** — 所有验证结果必须由 ssh_execute 真实执行产生
6. **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"

---

## 检查点

Phase 6.5 完成判定需全部通过：

1. **所有 C1 都有证伪记录** — `chain_verification.json` 中每个 `confidence=C1` 的 ATK-CAND 都在 `adversary_verification.json` 中有对应条目
2. **overturned 有 SSH 证据** — 每个 `verdict=overturned` 的条目都有 `evidence_files` 指向真实的 SSH 输出文件
3. **attack.json overturned 项 confidence 已更新** — 所有 `verdict=overturned` 的 ATK-CAND 在 `attack.json` 中 confidence 已从 C1 降级为 C2，并追加了 adversary_overturned 标记

---

## 独立运行参数

```
--server prod-k8s-01 --session-dir /path/to/session
```

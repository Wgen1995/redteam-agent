---
name: chain-verify
description: >
  攻击链验证与审批门控。逐链验证攻击链可行性，执行 5 级审批门控，收集差分证明，判定可信度。
  使用场景：Phase 5 构建了攻击链后。
  不使用场景：Phase 5 没有可验证的攻击链。
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

# chain-verify — Phase 6 链式验证与审批门控

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| evidence/chains/chain_builder.md | Phase 5 | 攻击链描述、步骤、影响评估、置信度 |
| knowledge_graph/edges/cross_ref.json | Phase 3/5 | 交叉关联边 + attack_chain 边 |
| knowledge_graph/edges/attack.json | Phase 4a/4b | 攻击边，含验证命令和差分证明 |

## MUST 输出

| 输出 | 说明 |
|------|------|
| evidence/chains/chain_verification.md | 每条链的验证结果、可信度判定、审批记录 |
| evidence/chains/chain_verification.json | 结构化验证结果（每条链的可信度+审批记录+差分证明引用） |

## 审批门控 5 级体系

| 级别 | 操作类型 | auto 模式 | manual 模式 | 超时处理 |
|------|---------|-----------|------------|---------|
| L1 | 只读检测（ls/cat/find/kubectl get） | 自动通过 | 自动通过 | 无 |
| L2 | 非破坏性攻击验证（curl/nc/kubectl auth can-i） | 自动通过 | 标准 approval | 5分钟 → 降级为理论验证，标记⚠️ |
| L3 | 破坏性攻击验证（docker run 临时容器等） | 自动通过 | 快速 approval | 5分钟 → 降级为理论验证，标记⚠️ |
| L4 | 逃逸验证（nsenter/chroot/cgroup 操作） | 自动通过 | question 确认 | 5分钟 → 降级为理论验证，标记⚠️ |
| L5 | 不可安全复现（DoS/删根目录等） | question确认（理论验证） | question确认（理论验证） | 标记⚠️，做理论验证 |

**关键规则**：
- 审批门控 5 级必须明确：L1 自动→L2 标准→L3 快速→L4 手动→L5 理论验证
- 超时降级规则：审批超时自动降级为理论验证，标记⚠️
- L5 被拒绝时：ATK-CAND 降级为"高风险线索"，不得以任何方式绕过继续该攻击路径
- 审批记录必须写入 chain_verification.md，包含时间、级别、结果
- **子代理内部审批**：子代理遇到 L3/L4 破坏性步骤时，直接用 question 工具向用户请求审批，不再返回给入口 LLM 请求审批。审批通过后继续执行，审批拒绝则降级为理论验证

### 安全熔断机制（兜底防护）

**目的**：防止 auto 模式下 LLM 幻觉导致连续自动审批高破坏性命令

**机制**：
1. `session_config.json` 中维护 `auto_high_risk_exec_count` 计数器
2. 每次 L3/L4 级别操作被自动通过后，计数器 +1
3. **熔断阈值**：10 分钟内 ≥5 次 L3/L4 自动通过
4. **触发熔断**：暂停自动审批，下一个 L4 操作**强制要求 manual approval**
5. **熔断恢复**：用户 manual 确认一次后，计数器清零，恢复自动审批
6. **记录**：熔断触发时在 `evidence/qa/circuit_breaker_event.md` 中记录时间戳、触发时的计数、触发的操作列表

**注意**：熔断机制不改变审批级别定义，只在异常频率时插入一个暂停点。正常频率的 L3/L4 操作不受影响。

## 核心工作流

### KG 节点存在性校验（本 Phase 通用约束）

本 Phase 在验证过程中如需写入任何边（如验证后更新 attack.json 中边的 status），**必须**先执行以下校验：

1. **检查节点存在性**：对每条待更新/写入边的 `from_node` 和 `to_node`，检查是否存在于 `knowledge_graph/nodes/` 下的任一 JSON 文件中
2. **不存在且是 Pod/Container**：
   - **强制补采**：`ssh_execute(server, "kubectl get pod <name> -n <ns> -o json")` 或 `crictl inspect <id>` 获取 spec
   - 写入对应 nodes JSON 文件（pods.json / containers.json）
   - 更新 `knowledge_graph/edges/infra.json`（补采的 Pod 需补建 runs_on / container_in 等边）
   - 补采后重新校验节点存在性
3. **不存在且是抽象节点**（如 `attack-xxx`、`CHAIN-xxx`）：
   - `attack-*` → 补建到 attacks.json，node_type: "attack"
   - `CHAIN-*` → 补建到 chains.json，node_type: "chain"（如不存在则创建）
4. **禁止跳过补建直接写悬空边** — 53 条悬空边问题已修复
5. **禁止绕过 KG 直接 SSH 验证** — 所有验证结果必须通过 KG 边记录

**校验执行时机**：在步骤 1 逐链验证开始前，先读取 chain_builder.md 中所有链引用的节点，校验其在 KG 中的存在性。

---

### 步骤 1：逐链验证

对 `chain_builder.md` 中的每条链，逐步执行验证。

**验证流程**：

```
对于每条链 CHAIN-XXX：
  读取链的步骤列表
  对于每个步骤 N：
    1. 读取该步对应的 ATK-CAND 详情（从 attack.json）
    2. 读取该 ATK-CAND 的攻击模式 SKILL.md（从 attack-patterns/）
    3. 逐步执行：
       a. 前置条件验证（第 N 步的前置条件是否满足）
       b. 攻击验证（按审批门控级别执行）
       c. 差分证明收集
    4. 记录验证结果
  综合判定链的可信度
```

**单步验证细节**：

每个步骤的验证分三阶段：

#### 阶段 A：前置条件验证

检查第 N 步的前置条件是否满足：

```
1. 检查环境固有条件（合规违规 + 基础设施边）
   → 读 findings.json 和 cross_ref.json 确认

2. 检查前一步攻击后果是否满足本步前置条件
   → 读前一步的差分证明确认
   → 如果前一步未验证或降级，本步前置条件可能不满足

3. 标注前置条件满足状态：
   ✅ 全部满足（环境+前步后果覆盖所有前置条件）
   ⚠️ 部分满足（部分前置条件依赖理论推导）
   ❌ 不满足（关键前置条件缺失）
```

#### 阶段 B：攻击验证（按审批门控）

根据攻击模式 SKILL.md 中的 `max_verification_level` 和 `destructive` 字段决定验证层级：

```
如果 max_verification_level = L2 且 destructive = false：
  → 执行 L2 攻击验证（实际复现）
  → 需要审批：L2 级别（标准 approval in manual 模式）

如果 max_verification_level = L2 且 destructive = true：
  → 标注为 L3 条件验证（不实际执行破坏性命令）
  → 最高验证层级 L3

如果攻击涉及宿主机逃逸：
  → 执行 L4 逃逸验证
  → 需要审批：L4 级别（question 确认 in manual 模式）

如果攻击为 DoS/不可安全复现：
  → 标注为 L5 不可安全复现
  → 做理论验证，标记⚠️
```

#### 阶段 C：差分证明收集

每步标注执行上下文差异：

| 上下文 | 含义 | 标注 |
|--------|------|------|
| L0 | 宿主机观察 | `[L0]` |
| L1 | 容器内观察 | `[L1]` |
| L2 | 容器内攻击验证 | `[L2]` |

**差分证明格式**：

```markdown
### CHAIN-001 步骤 2 差分证明

**攻击前快照**：
- [L0] `docker ps` 输出：无异常容器
- [L1] `cat /proc/1/cgroup` 输出：在容器内

**攻击执行**：
- [L2] `kubectl exec -n production backend-api -- docker run -v /:/host alpine ls /host/etc/shadow`

**攻击后对比**：
- [L0] `docker ps` 输出：出现新 alpine 容器
- [L2] 攻击命令输出：可读取宿主机 /etc/shadow

**差分结论**：✅ 攻击成功，可从容器内通过 docker.sock 读取宿主机文件
```

### 步骤 2：收集差分证明

**执行流程**：

```
对于每条链的每个步骤：
  1. 执行前快照：收集目标环境的基线状态
     - [L0] 宿主机层面：进程列表、网络连接、文件系统挂载
     - [L1] 容器内层面：能力集、文件系统可见性、网络可达性

  2. 执行攻击命令（根据审批级别）：
     - L1/L2：实际执行命令
     - L3：执行条件验证替代命令
     - L4：执行逃逸验证（需确认）
     - L5：理论推导（标记⚠️）

  3. 执行后对比：收集攻击后的状态变化
     - [L0] 宿主机层面变化
     - [L1/L2] 容器内层面变化

  4. 差分判断：
     - 攻击前后有明确可观测差异 → ✅ 差分充分
     - 攻击前后无明确差异或差异不显著 → ⚠️ 差分不充分
     - 无法执行攻击 → ❌ 无差分（理论验证）
```

**差分证明标注规则**：
- 每步必须标注 `[L0]`/`[L1]`/`[L2]` 执行上下文
- L3 条件验证的步骤标注 `[L3]` 和理论推导说明
- L5 不可安全复现的步骤标注 `⚠️` 和不可安全复现原因

### 步骤 3：审批门控 5 级

**审批流程**：

```
对于每个需要审批的验证步骤：

1. 确定审批级别（基于攻击模式 SKILL.md 的 max_verification_level 和 destructive）
2. 根据 session_config.json 的 approval 模式（auto/manual）
3. 执行审批：

   auto 模式：
     L1 → 自动通过
     L2 → 自动通过
     L3 → 自动通过
     L4 → 自动通过
     L5 → question 确认（必须确认）

   manual 模式：
     L1 → 自动通过
     L2 → question 确认（标准 approval）
     L3 → question 确认（快速 approval）
     L4 → question 确认（手动确认）
     L5 → question 确认（必须确认）

4. 超时处理：
   L2/L3/L4 审批超时（5分钟）→ 自动降级为理论验证，标记⚠️
   L5 审批超时（10分钟）→ 自动降级为理论验证，标记⚠️

5. L5 被拒绝：ATK-CAND 降级为"高风险线索"，不继续该攻击路径
```

**审批记录写入 chain_verification.md**：

```markdown
## CHAIN-001 审批记录

| 步骤 | ATK-CAND | 审批级别 | 审批模式 | 审批时间 | 审批结果 | 备注 |
|------|----------|---------|---------|---------|---------|------|
| 1 | ATK-CAND-001 | L2 | auto | 2026-06-20T10:30:00Z | 通过 | docker.sock 探测 |
| 2 | ATK-CAND-005 | L2 | auto | 2026-06-20T10:35:00Z | 通过 | Secret 读取验证 |
| 3 | ATK-CAND-007 | L4 | manual | 2026-06-20T10:40:00Z | 通过 | 横向移动需确认 |
```

### 步骤 4：被阻断链检查 + 差分证明验证

#### 4.1 被阻断链绕过策略

对于验证过程中被安全机制阻断的链步骤：

```
对于每个被阻断的步骤：
  1. 识别阻断机制（AppArmor/Seccomp/NetworkPolicy/SELinux 等）
  2. 读取该 ATK-CAND 攻击模式 SKILL.md 的"绕过策略"章节
  3. 评估绕过策略可行性：
     ✅ 有可行绕过 → 继续验证链，标注绕过方式
     ⚠️ 理论可能绕过 → 标记为条件成立（附阻断机制+理论绕过）
     ❌ 无已知绕过 → 标记链该步骤为 blocked
  4. 链的后续步骤：
     - 如果阻断步骤后续还有依赖步骤 → 后续步骤标记为 "前置条件不满足"
     - 如果阻断步骤是链的最后一步 → 整条链标记为 "被阻断"
```

**被阻断链处理**：

```markdown
### CHAIN-002 绕过策略检查

**阻断步骤**: 步骤 2 (ATK-CAND-003)
**阻断机制**: AppArmor profile 'docker-default' 阻止 mount 操作
**绕过策略**: 
  - [L1] 检查是否存在 AppArmor 未覆盖的路径 → `cat /proc/1/attr/current` → docker-default
  - [L1] 检查 Seccomp 是否同时限制 → `cat /proc/1/status | grep Seccomp` → Seccomp 已启用
  - ⚠️ 无已知绕过策略

**结论**: ❌ 无可行绕过，链条在步骤 2 被阻断
```

#### 4.2 差分证明验证（C1/C2/C3 可信度判定）

对每条链综合所有步骤的验证结果，判定最终可信度：

**C1 实证复现判定条件**（5 项全满足）：

| 条件 | 说明 |
|------|------|
| 前置条件可复现 | 链中每步前置条件都有实际观测数据证明满足 |
| 可执行 | 链中每步攻击命令都能在目标环境执行且未报错 |
| 可区分 | 攻击效果可与正常行为区分（差分证明充分） |
| 影响可观测 | 攻击成功后的副作用可被观测 |
| 可恢复 | 攻击后可恢复到原始状态（有清理命令） |

**C2 条件实证判定条件**：
- 前置条件全部满足（环境固有或理论推导）
- 但差分证明不充分，或被安全机制阻断（附阻断机制名称）
- 或包含不可安全复现的步骤（标注原因 + 理论 POC + ⚠️）

**C3 风险线索判定条件**：
- 配置存在安全隐患
- 但前置条件不完全满足
- 附风险分析和建议补充验证

**C2 子情况**：
1. **安全机制阻断**：前置条件满足但被 AppArmor/Seccomp/网络策略等阻断 → 标注阻断机制名称
2. **不可安全复现**：前置条件满足但实际执行会影响生产 → 标注原因 + 理论 POC（标注⚠️）

**最终链可信度判定**：

```markdown
## CHAIN-001 可信度判定

| 步骤 | ATK-CAND | 验证结果 | 差分证据 | 审批级别 | 审批结果 |
|------|----------|---------|---------|---------|---------|
| 1 | ATK-CAND-001 (socket-escape) | ✅ 前置条件满足 | [L0]docker.sock存在 [L2]可逃逸 | L2 | 通过 |
| 2 | ATK-CAND-005 (secret-exfil) | ✅ 前置条件满足 | [L0]etcd可达 [L2]可读取Secret | L2 | 通过 |
| 3 | ATK-CAND-007 (lateral-move) | ⚠️ 部分满足 | [L1]网络可达 [L3]理论推导 | L3 | 降级 |

链可信度: C2 条件实证 ✅
原因: 步骤1-2为C1实证复现，步骤3依赖步骤2窃取的SA Token进行横向移动，
     理论推导充分但差分证明不足（SA Token实际权限范围未实测）。
```

## chain_verification.md 输出格式

```markdown
# 攻击链验证报告

## 验证概要

| CHAIN | 可信度 | 影响评估 | 步骤数 | 审批状态 |
|-------|--------|---------|--------|---------|
| CHAIN-001 | C2 ✅ | Critical | 3 | 已完成 |
| CHAIN-002 | C3 ⚠️ | High | 2 | 被阻断 |

## CHAIN-001: socket-escape → secret-exfil → lateral-move

### 链描述
从业务容器出发，经Docker套接字逃逸至宿主机，利用etcd访问窃取集群Secret，通过窃取的SA Token横向移动至其他命名空间

### 可行性
⚠️ 条件可行（第3步依赖第2步窃取的SA Token，若etcd网络不可达则断裂）

### 步骤验证

#### 步骤 1: ATK-CAND-001 (socket-escape)
- 前置条件: ✅ 全部满足
- 攻击验证: ✅ L2 通过
- 差分证明: ✅ 充分
- 可信度: C1

#### 步骤 2: ATK-CAND-005 (secret-exfil)
- 前置条件: ✅ 全部满足（依赖步骤1逃逸后果）
- 攻击验证: ✅ L2 通过
- 差分证明: ✅ 充分
- 可信度: C1

#### 步骤 3: ATK-CAND-007 (lateral-move)
- 前置条件: ⚠️ 部分满足（SA Token权限范围未实测）
- 攻击验证: ⚠️ L3 条件验证
- 差分证明: ⚠️ 不充分
- 可信度: C2

### 审批记录
（审批表格见上）

### 差分证明
（差分证明详情见上）

### 链可信度判定
C2 条件实证 ✅
```

## 检查点

完成前必须逐项确认：

- [ ] **① 验证结果写入**：每条链的每个步骤都有验证结果（✅/⚠️/❌/🛑）
- [ ] **② 审批门控执行完毕**：每个需要审批的步骤都有审批记录，超时有降级处理
- [ ] **③ 被阻断链有重新规划**：每个被阻断的链步骤都检查了绕过策略
- [ ] **④ QA 结构校验通过**：
  - chain_verification.md 非空
  - 每条链有 chain_id、验证结果、可信度、审批记录
  - 每个步骤的执行上下文标注完整（L0/L1/L2/L3/L5）
  - 差分证明每步标注 [L0]/[L1]/[L2]
  - C1/C2/C3 判定有明确依据
  - 无 `[ ]` 未检查标记残留

## 反幻觉硬约束

1. **不准凭记忆出验证结果** — 攻击验证的每条命令必须从攻击模式 SKILL.md 或攻击假设库中查到出处
2. **不准伪造 SSH 输出** — 所有差分证明必须由 ssh_execute 真实执行产生
3. **无证据不写确认态** — 差分证明不充分不得标记 C1
4. **超出审批范围立即停** — L5 被拒绝时不得继续该攻击路径
5. **省略词零容忍** — 不使用"等"、"..."、"+N"等省略表述
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值

## 上下文控制

- 先读 `knowledge_graph/edges/_index.md` 定位必要数据
- 只读当前验证链涉及的 ATK-CAND 数据和攻击模式
- 分析结果立即写盘到 chain_verification.md，释放上下文
- 返回 supervisory-agent 的摘要不携带原始数据，详细数据写盘后以文件路径引用

## 独立运行参数

```
--server prod-k8s-01 --session-dir /path/to/session
```

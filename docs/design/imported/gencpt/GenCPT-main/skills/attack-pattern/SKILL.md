---
name: attack-pattern
description: >
  已知攻击模式库匹配与验证。根据合规违规和侦察结果，条件触发读取攻击模式库，执行探测和验证。
  使用场景：Phase 3 完成后，有合规违规或侦察发现需要验证攻击可行性。
  不使用场景：Phase 2 全部 pass 且侦察无异常。
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

# attack-pattern — Phase 4a 已知攻击模式匹配与验证

本 SKILL 负责根据合规违规和侦察结果，条件触发读取攻击模式库，执行探测和攻击验证，为确认的真实攻击路径生成 ATK-CAND。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `knowledge_graph/nodes/` | Phase 1 | 环境信息（hosts.json、pods.json 等） |
| `knowledge_graph/edges/compliance.json` | Phase 2 | 合规边（含判定结果） |
| `knowledge_graph/edges/cross_ref.json` | Phase 3 | 交叉关联边（含 XREF 结果） |
| `knowledge_graph/nodes/findings.json` | Phase 2 | 合规违规发现节点 |
| `evidence/cross-ref/prerequisite_signals.md` | Phase 3 | 前置条件信号比对 |
| `evidence/compliance/*/results.json` | Phase 2 | 合规检测结果详情 |
| `attack-patterns/_index.md` | 本套件 | 条件触发读取表和平台过滤 |
| `attack-patterns/{面}/{模式}/SKILL.md` | 本套件 | 具体攻击模式文件（按需读取） |

**前置条件校验**：
1. `knowledge_graph/edges/cross_ref.json` 存在且非空（Phase 3 已完成）
2. `attack-patterns/_index.md` 存在
3. 有至少一条 `[x]` 或 `[?]` 标记的合规违规或交叉关联结果

任一前置条件不满足 → 立即终止，在 `progress.json` 标记 Phase 4a 为 `skipped` 或 `blocked`。

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/SSH_COMMANDS.md` | SSH 命令使用规范、执行上下文标注、审批门控、限速与重试 |
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流（4 步）

### 步骤 1：扫描触发条件

1. 读取 `evidence/compliance/*/results.json`，收集所有 `fail` 和 `warn` 规则
2. 读取 `knowledge_graph/nodes/` 中的安全上下文关键发现（recon 摘要中的 `[x]` 和 `[?]` 标记）
3. 读取 `evidence/cross-ref/prerequisite_signals.md`，获取 Phase 3 的前置条件信号
4. 读取 `attack-patterns/_index.md`，对照条件触发读取表，确定哪些触发信号命中
5. 对每个命中信号，确定需 Read 的模式文件路径
6. 按 `session_config.json.env_fingerprint` 中的平台信息过滤模式文件（参考 `_index.md` 中的 `platforms` 字段）
7. 生成待验证模式列表，按严重等级排序
8. **LLM 语义补充扫描**（弥补静态触发表的滞后性）：
   - 读取 `_index.md` 中所有模式的名称 + frontmatter 的 `mapped_compliance_families` 字段
   - 基于语义判断：是否有 fail/warn 规则或侦察发现在静态触发表中未覆盖、但可能相关
   - 特别关注 `_learned/` 目录下的新模式（静态表可能未及时收录）
   - 命中的模式标记为 `[?] 疑似相关`，source 标记为 `llm_supplementary_scan`
   - **约束**：此步骤只筛选不生成命令，命中的模式仍需 Read 完整 SKILL.md 后才执行探测
   - **token 预算**：此步骤 ≤500 tokens（只读模式名+摘要，不读完整8段）

**关键规则**：**不准凭记忆出攻击命令！必须 Read 对应的模式 SKILL.md。** 每个模式的探测命令、攻击验证步骤、差分证明方法只存在于模式文件中，禁止从上下文记忆中提取。

---

### 步骤 2：逐个模式验证

对每个待验证模式，按以下流程执行：

#### 2.1 读取模式文件

Read 模式 SKILL.md（如 `attack-patterns/escape/socket-escape/SKILL.md`），提取：
- 前置条件列表
- 探测命令（标注 L0/L1 层级）
- 攻击验证步骤（标注 L2 层级）
- 差分证明方法
- 证伪条件

#### 2.2 执行探测命令

按执行上下文层级执行：

| 层级 | 名称 | 执行方式 | 说明 |
|------|------|---------|------|
| L0 | 宿主机观察 | `ssh_execute` 直接执行 | 发现前置条件、收集配置信息 |
| L1 | 容器内观察 | `ssh_execute` + `kubectl exec <pod> -- <command>` | 验证攻击者视角可见性 |
| L2 | 容器内攻击验证 | `ssh_execute` + `kubectl exec <pod> -- <attack_command>` | 实际复现漏洞路径 |
| L3 | 条件验证 | 不执行破坏性命令 | 理论推导，步骤标注 ⚠️ |

**审批门控**：

| 操作层级 | 对应审批级别 | auto 模式 | manual 模式 | 超时处理 |
|---------|------------|---------|-----------|---------|
| L0 + L1 | Level 1-2 | 自动通过 | 自动通过 | 无 |
| L2（非破坏性） | Level 3 | 自动通过 | question 确认 | 5分钟 → ATK-CAND 降级 |
| L2（逃逸验证） | Level 4 | 自动通过 | question 确认 | 5分钟 → ATK-CAND 降级 |
| L3 | Level 5 | question 确认 | question 确认 | 10分钟 → 降级 |

**重要**：L2/L3 操作需要用户 approval 才能执行。manual 模式下使用 当前环境的用户交互工具请求确认。超时或被拒绝时，ATK-CAND 降级为"高风险线索"，不得绕过继续该攻击路径。

**命令执行规则**：
- L0/L1 命令：直接 ssh_execute
- L2 命令：必须先获得 approval（auto 模式自动通过），然后 ssh_execute
- L3 步骤：标注 ⚠️，只做条件组合分析，不实际执行破坏性操作
- 所有命令输出**立即写盘**到 `evidence/attack/raw/`，五元组标注

#### 2.3 判断前置条件

```
前置条件检查（L0+L1）
    │
    ├─ 不满足 → [−] 证伪，附证伪依据（进入全景报告覆盖矩阵"不可利用"行）
    │   依据：哪条命令的输出证伪
    │
    ├─ 部分满足 → [?] C3 风险线索
    │   标记未满足的前置条件
    │
    └─ 满足 → 继续攻击验证
```

#### 2.4 执行攻击验证（L2）

前置条件满足时，执行模式文件中的攻击验证步骤：

1. 收集攻击前状态快照（L0 命令）
2. 执行攻击命令（L2）
3. 收集攻击后状态（L0 命令）
4. 对比差异生成差分证明

**差分证明要求**：
- 至少包含 2 个可观测差异（攻击前后对比明确）
- 每个差异必须有 SSH 输出证据
- 差分证明格式：

```markdown
### 差分证明：ATK-CAND-XXX

| 项目 | 攻击前 | 攻击后 |
|------|--------|--------|
| 宿主机进程列表 | 无异常容器 | 新增 alpine 容器 |
| 文件系统访问 | 容器内无法访问宿主机 | 可读取 /host/etc/shadow |

**证据输出**：
- 攻击前快照：evidence/attack/raw/pre_ATK-CAND-XXX_{timestamp}.md
- 攻击后快照：evidence/attack/raw/post_ATK-CAND-XXX_{timestamp}.md
清理命令：kubectl exec -n production backend-api -- docker rm -f <container_id>
```

#### 2.5 生成 ATK-CAND

对每个 `[x]` 和 `[?]` 标记的验证结果生成 ATK-CAND：

```json
{
  "id": "ATK-CAND-001",
  "source": "pattern_library",
  "pattern_ref": "escape/socket-escape",
  "target": "pod/backend-api-xyz",
  "severity": "Critical",
  "verification_level": "L2",
  "context": "container",
  "confidence": "C1",
  "prerequisites_met": ["docker.sock_visible", "docker.sock_writable"],
  "prerequisites_unmet": [],
  "evidence_files": [
    "evidence/attack/raw/pre_ATK-CAND-001_20260619T084200.md",
    "evidence/attack/raw/post_ATK-CAND-001_20260619T084200.md"
  ],
  "five_state": "[x]",
  "trigger_rules": ["K8s-5.2.1", "K8s-5.2.3"],
  "hypothesis_refs": ["CHK-CAND-002", "ATK-HYP-001"]
}
```

**verification_level 字段说明**：
- `L0` — 仅宿主机观察证据
- `L1` — 容器内观察证据
- `L2` — 容器内攻击验证，差分证明充分
- `L3` — 条件验证，理论推导

**context 字段说明**：
- `host` — 宿主机上执行
- `container` — 容器内执行
- `mixed` — 多层级混合

---

### 步骤 3：处理未匹配信号

有合规违规或侦察发现**无法匹配任何现有攻击模式**时：

1. 在 `unmatched_signals.md` 中记录每个未匹配信号：
   ```markdown
   ## 未匹配信号

   | 信号 | 来源 | 严重等级 | 推荐处理 |
   |------|------|---------|---------|
   | K8s-4.2.x(自定义合规规则fail) | 合规 | Medium | 交给 Phase 4b LLM 推理 |
   | Pod 异常网络配置 | 侦察 | High | 交给 Phase 4b LLM 推理 |
   ```
2. 标记为 `[?]`，明确标注"无法匹配现有模式，需 LLM 推理"
3. 写入 `evidence/attack/unmatched_signals.md`

---

### 步骤 4：五态闭环

**所有 `[ ]` 必须消灭**：
- 遍历步骤 1 中所有触发信号
- 每个信号必须转换为 `[x]`/`[?]`/`[-]`/`[!]` 之一
- `[x]` 和 `[?]` 必须有 ATK-CAND 编号
- `[-]` 必须写明证伪依据（哪条命令、什么输出）
- `[!]` 必须写明阻断机制（AppArmor/Seccomp/NetworkPolicy 等）

**ATK-CAND 编号规则**：
- Phase 3 的 ATK-CAND 编号已经使用过的序号不再重复
- 本次 ATK-CAND 编号从 Phase 3 最大编号 +1 开始连续编号
- source 字段为 `pattern_library`
- 编号连续无遗漏

---

## MUST 输出

Phase 4a 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `evidence/attack/pattern-hits.md` | 已知模式命中详情（每个命中模式的验证过程和结论） |
| `evidence/attack/unmatched_signals.md` | 未匹配信号列表 |
| `knowledge_graph/edges/attack.json` | 攻击边（含 verification_level 和 context 字段） |

---

## 检查点

Phase 4a 完成判定需全部通过：

1. **所有触发信号有验证结论** — 每个触发的模式文件都读取并验证，五态标记无 `[ ]` 残留
2. **ATK-CAND 编号连续无遗漏** — 从 Phase 3 最大编号 +1 开始连续，无断号
3. **差分证明充分** — C1（实证复现）的 ATK-CAND 至少有 2 个可观测差异
4. **QA 结构校验通过** — 所有 MUST 输出文件存在且非空，`attack.json` 中每条边的节点引用可找到

---

## 可信度判定

| 可信度 | 标记 | 含义 | 证据要求 |
|--------|------|------|---------|
| **C1 实证复现** | ✅✅ 已确认-可复现 | L2 攻击验证成功，差分证明充分 | 5项门槛全满足 + L2 差分证明 |
| **C2 条件实证** | ✅ 已确认-条件成立 | 前置条件满足，理论链路完整 | 前置条件全部列举 + 理论链路清晰 |
| **C3 风险线索** | ⚠️ 高风险线索 | 配置隐患但前置条件不完全满足 | 配置证据 + 风险分析 |
| 不可利用 | ➖ 已证伪 | 前置条件不满足 | 至少有 L0 证伪依据 |
| 已阻断 | 🛑 已阻断 | 被安全机制阻断 | 至少有 L1 阻断证据 |

---

## WU 摘要格式

每个 WU 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/attack/summaries/{work_unit_id}.json`：

```json
{
  "work_unit_id": "WU-4a-01",
  "status": "complete",
  "summary": "验证 5 个攻击模式，命中 3 个（C1×1, C2×1, C3×1），证伪 2 个",
  "critical_findings": [
    "ATK-CAND-004: socket-escape C1 实证复现，pod/backend-api 可通过 docker.sock 逃逸",
    "ATK-CAND-005: RBAC-abuse C2 条件实证，SA 权限过宽"
  ],
  "files_written": [
    "evidence/attack/pattern-hits.md",
    "evidence/attack/unmatched_signals.md",
    "knowledge_graph/edges/attack.json"
  ],
  "context_used": [
    "attack-patterns/escape/socket-escape/SKILL.md",
    "attack-patterns/auth/k8s-rbac-abuse/SKILL.md"
  ],
  "issues": []
}
```

---

## 禁止事项

- **不准凭记忆出攻击命令！** — 必须先 Read 对应模式 SKILL.md，从文件中提取探测命令和验证步骤
- **不准伪造 SSH 输出** — 所有验证结果必须由 ssh_execute 真实执行产生
- **无证据不写确认态** — 只有差分证明充分才能标记 C1，只有前置条件全部满足才能标记 C2
- **超出审批范围立即停** — Level 4/5 审批被拒绝时不得继续该攻击路径
- **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"
- **占位符必须替换** — 所有【xxx】占位符必须替换为实际值
- **不跳过五态闭环** — 所有 `[ ]` 必须消灭
- **不混合审计和攻击视角** — L0 仅用于侦察和条件核实，L1/L2 通过 kubectl exec 模拟容器内攻击者视角

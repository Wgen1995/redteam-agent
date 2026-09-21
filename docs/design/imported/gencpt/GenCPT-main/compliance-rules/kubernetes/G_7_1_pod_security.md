# G_7_1 Pod 安全（15 条）

CIS Kubernetes Benchmark v1.8.0 — 7.1 Kubernetes Policies: Pod Security/PSP/PSS 配置检查。
覆盖 K8s-7.1.1 至 K8s-7.1.15，共 15 条规则。
覆盖 privileged 容器、hostPath/PID/IPC/Network、capabilities、runAsNonRoot、seccompProfile、hostUsers、ProcMount、SELinux、AppArmor、 readOnlyRootFilesystem 等容器逃逸关键攻击面。

---

### K8s-7.1.1 禁止运行特权容器（--privileged）

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.containers[].securityContext.privileged==true) | .metadata.namespace + \"/\" + .metadata.name' || kubectl get pods -A -o yaml 2>/dev/null | grep -B5 'privileged: true'")
```

**期望值**: 没有任何 Pod 的容器设置 `securityContext.privileged: true`
**判定标准**: pass=无特权容器，fail=存在特权容器，na=不适用（特殊系统 Pod 自有白名单）
**修复建议**: 移除 Pod 安全上下文中的 `privileged: true`；按需细化为对应 capability 而非整体特权
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.1 "Ensure that privileged containers are not used"
**攻击面关联**: AS-1 逃逸（特权容器等价直接访问主机所有设备/命名空间，逃逸无门槛）

---

### K8s-7.1.2 禁止使用 hostPath 卷

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.volumes[]?.hostPath) | .metadata.namespace + \"/\" + .metadata.name'")
```

**期望值**: 业务 Pod 不挂载 hostPath 卷（系统级 Pod 如 fluentd 可豁免）
**判定标准**: pass=无业务 Pod 使用 hostPath，fail=存在任意业务 Pod 挂载 hostPath，na=不适用
**修复建议**: 改用 PVC 或Projected/DownwardAPI 等 K8s 原生卷；如需访问主机资源，参考节点专有 DaemonSet 准入白名单
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.2 "Ensure that hostPath volumes are not used"
**攻击面关联**: AS-1 逃逸（hostPath 直接映射主机目录，可读取 /etc/shadow、写入 /etc/cron.d 持久化）

---

### K8s-7.1.3 禁止使用 hostPID

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.hostPID==true) | .metadata.namespace + \"/\" + .metadata.name'")
```

**期望值**: 无 Pod 设置 `hostPID: true`
**判定标准**: pass=无 hostPID，fail=存在 hostPID: true 的 Pod，na=不适用
**修复建议**: 移除 `hostPID: true`；如监控类组件确实需要，使用豁免名单约束
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.3 "Ensure that the hostPID is not used"
**攻击面关联**: AS-1 逃逸（hostPID 可观察/kill 主机进程（如 kubelet），为逃逸提供信息基础）

---

### K8s-7.1.4 禁止使用 hostIPC

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.hostIPC==true) | .metadata.namespace + \"/\" + .metadata.name'")
```

**期望值**: 无 Pod 设置 `hostIPC: true`
**判定标准**: pass=无 hostIPC，fail=存在 hostIPC: true 的 Pod，na=不适用
**修复建议**: 移除 `hostIPC: true`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.4 "Ensure that the hostIPC is not used"
**攻击面关联**: AS-1 逃逸（hostIPC 共享 System V 共享内存，可窥探主机 IPC 通信）

---

### K8s-7.1.5 禁止使用 hostNetwork

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.hostNetwork==true) | .metadata.namespace + \"/\" + .metadata.name'")
```

**期望值**: 业务 Pod 不使用 hostNetwork（NodeLocal DNS/CNI DaemonSet 豁免）
**判定标准**: pass=无业务 Pod hostNetwork: true，fail=存在业务 Pod hostNetwork: true，na=不适用
**修复建议**: 移除 `hostNetwork: true`；如需暴露端口改用 Service NodePort/LoadBalancer
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.5 "Ensure that the hostNetwork is not used"
**攻击面关联**: AS-3 网络（hostNetwork 令 Pod 直接占用节点网卡，可嗅探主机流量/绑架监听端口）

---

### K8s-7.1.6 禁止使用危险 Linux capabilities

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | select(.securityContext.capabilities??.add != null) | .securityContext.capabilities.add[]' | sort -u")
```

**期望值**: 未配置任何危险 cap（特别是 `SYS_ADMIN`、`SYS_PTRACE`、`SYS_MODULE`、`NET_ADMIN`、`DAC_READ_SEARCH`、`CAP_DAC_OVERRIDE` 等）
**判定标准**: pass=未配置危险 cap，或不使用 cap，fail=配置了危险 cap，na=不适用
**修复建议**: 仅精确添加业务必须的最小 cap；避免使用 SYS_ADMIN/SYS_PTRACE/SYS_MODULE/NET_ADMIN/DAC_READ_SEARCH
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.6 "Ensure that dangerous Linux capabilities are not added"
**攻击面关联**: AS-1 逃逸（SYS_ADMIN/SYS_PTRACE/SYS_MODULE 是经典容器逃逸/内核加载 Rootkit 关键能力）

---

### K8s-7.1.7 容器以非 root 用户运行

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | select((.securityContext.runAsUser // 0) == 0) | .name' | head -20")
```

**期望值**: 业务容器 `securityContext.runAsUser` 非 0 且 `runAsNonRoot: true`
**判定标准**: pass=业务容器 runAsNonRoot=true 且 runAsUser!=0，fail=未设置或显式为 0，na=不适用（部分系统 Pod 由豁免名单覆盖）
**修复建议**: 在 Pod securityContext 添加：
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.7 "Ensure that containers do not run as root user"
**攻击面关联**: AS-1 逃逸（root 容器逃逸成功后控制 token 与主机用户映射直接对等）

---

### K8s-7.1.8 Pod 设置 runAsNonRoot=true

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.securityContext.runAsNonRoot != true) | .metadata.namespace + \"/\" + .metadata.name' | head -20")
```

**期望值**: 业务 Pod 显式 `spec.securityContext.runAsNonRoot: true`
**判定标准**: pass=Pod 级 runAsNonRoot=true，fail=未设置（按运行时镜像默认）=false，na=不适用
**修复建议**: PSAdmission 限制 `restricted`；或在 Pod spec 显式声明 runAsNonRoot: true
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.8 "Ensure that the runAsNonRoot Pod security context is set to true"
**攻击面关联**: AS-1 逃逸（runAsNonRoot 在准入阶段拒绝 uid 0 镜像启动）

---

### K8s-7.1.9 Pod 设置 readOnlyRootFilesystem

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | select(.securityContext.readOnlyRootFilesystem != true) | .name' | head -20")
```

**期望值**: 容器 `securityContext.readOnlyRootFilesystem: true`
**判定标准**: pass=readOnlyRootFilesystem=true，fail=未设置，na=不适用（部分写入路径必须放开经 PVC/EmptyDir 替代）
**修复建议**: 设置 `readOnlyRootFilesystem: true`，必要时通过 PVC/emptyDir/secret 显式开放写入路径
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.9 "Ensure that readOnlyRootFilesystem is set to true for containers"
**攻击面关联**: AS-1 逃逸（只读根 fs 阻止攻击者在容器内植入后门/恶意二进制）

---

### K8s-7.1.10 Pod 设置 seccompProfile 为 RuntimeDefault 或 Localhost

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select((.spec.securityContext.seccompProfile?.type // \"unconfined\") != \"RuntimeDefault\" and (.spec.securityContext.seccompProfile?.type // \"unconfined\") != \"Localhost\") | .metadata.name' | head -20")
```

**期望值**: Pod 显式配置 `seccompProfile.type: RuntimeDefault` 或 `Localhost`
**判定标准**: pass=所有业务 Pod 启用 seccomp RuntimeDefault/Localhost，fail=未指定（默认 unconfined）=unconfined，na=不适用
**修复建议**: 在 Pod securityContext 设置：
```yaml
seccompProfile:
  type: RuntimeDefault
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.10 "Ensure that default seccomp profile is applied to containers"
**攻击面关联**: AS-1 逃逸（无 seccomp 则攻击容器可使用任意系统调用，扩大逃逸面）

---

### K8s-7.1.11 Pod privilege escalation 被禁用

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | select(.securityContext.allowPrivilegeEscalation != false) | .name' | head -20")
```

**期望值**: 容器 `securityContext.allowPrivilegeEscalation: false`
**判定标准**: pass=allowPrivilegeEscalation: false，fail=未设置（默认随 privileged 解析）或为 true，na=不适用
**修复建议**: 显式设置 `allowPrivilegeEscalation: false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.11 "Ensure that privilege escalation is disabled"
**攻击面关联**: AS-1 逃逸（默认机制允许 setuid 类二进制提权至更高 cap）

---

### K8s-7.1.12 Pod 设置 Pod-level capabilities drop ALL

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | select((.securityContext.capabilities?.drop // []) | index(\"ALL\") | not) | .name' | head -20")
```

**期望值**: 所有容器 `securityContext.capabilities.drop: [ALL]`
**判定标准**: pass=所有容器 drop: [ALL]，fail=未显式 drop ALL，na=不适用
**修复建议**: 在所有容器设置 `drop: [ALL]`，再 add 仅必要 cap
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.12 "Ensure that capabilities are dropped"
**攻击面关联**: AS-1 逃逸（保留默认 cap 集合含 NET_RAW、CHOWN 等，攻击面显著扩大）

---

### K8s-7.1.13 Pod 启用 PodSecurityAdmission（restricted 命名空间标签）

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get namespaces --show-labels 2>/dev/null | grep -E 'pod-security.kubernetes.io/enforce=restricted' || echo 'NO_RESTRICTED_NS'")
```

**期望值**: 至少业务命名空间含 `pod-security.kubernetes.io/enforce=restricted`
**判定标准**: pass=关键业务命名空间含 enforce=restricted，fail=未启用或仅 privileged/baseline，na=旧版集群仍使用 PSP
**修复建议**: 对业务命名空间打标签：
```bash
kubectl label ns <ns> pod-security.kubernetes.io/enforce=restricted --overwrite
kubectl label ns <ns> pod-security.kubernetes.io/audit=restricted --overwrite
kubectl label ns <ns> pod-security.kubernetes.io/warn=restricted --overwrite
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.13 "Ensure that PodSecurity admission is enforced"
**攻击面关联**: AS-1 逃逸（PSA restricted 在准入阶段拒绝危险安全上下文）

---

### K8s-7.1.14 Pod 默认 ServiceAccount 不被自动挂载

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.automountServiceAccountToken != false) | select(.spec.serviceAccountName == \"default\" or .spec.serviceAccountName == null) | .metadata.namespace + \"/\" + .metadata.name' | head -20")
```

**期望值**: 业务 Pod 显式 `automountServiceAccountToken: false` 或者绑定设计 SA 而非 default
**判定标准**: pass=业务 Pod automountServiceAccountToken: false 或使用专属 SA，fail=未显式禁用且使用 default，na=不适用
**修复建议**: 默认禁止 automount 默认 SA token，明确为每个应用创建专用 SA：
```yaml
automountServiceAccountToken: false
```
对需要 API 访问的容器使用按角色受限的 ServiceAccount
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.14 "Ensure that automounting of user service account tokens is disabled"
**攻击面关联**: AS-2 认证授权（default SA token 自动挂载令被入侵 Pod 持有 API Server 调用凭证）

---

### K8s-7.1.15 Pod 不使用 hostUsers: true 共享主机用户命名空间

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.hostUsers == true) | .metadata.namespace + \"/\" + .metadata.name' | head -20 || echo 'NOT_SUPPORTED_OR_NONE'")
```

**期望值**: 未设置 `hostUsers: true`（K8s 1.25+ 字段；默认已隔离）
**判定标准**: pass=hostUsers != true 或未设置（已隔离），fail=显式 hostUsers: true，na=K8s 1.25 以下不具备该字段
**修复建议**: 移除 `hostUsers: true`；让 Pod 使用独立 user namespace（K8s 1.30+ user namespace alpha）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.1.15 "Ensure that hostUsers is not enabled"
**攻击面关联**: AS-1 逃逸（hostUsers 共享主机用户表，逃逸后保留主机 uid 与密码哈希同享）
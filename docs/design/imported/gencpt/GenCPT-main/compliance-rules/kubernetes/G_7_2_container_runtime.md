# G_7_2 容器运行时安全（2 条）

CIS Kubernetes Benchmark v1.8.0 — 7.2 Kubernetes Policies: Container Runtime 安全策略。
覆盖 K8s-7.2.1 至 K8s-7.2.2，共 2 条规则。
覆盖镜像只读、运行时 probe/healthz 与容器临时特权操作约束。

---

### K8s-7.2.1 容器以只读镜像模式运行

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o yaml 2>/dev/null | grep -c 'readOnly: true' || kubectl get pods -A -o json 2>/dev/null | jq -r '[.items[].spec.containers[] | select(.imagePullPolicy != \"Always\")] | length'")
```

期望值: 生产容器 imagePullPolicy 默认 IfNotPresent，配合 readOnlyRootFilesystem 避免镜像层被写入
**判定标准**: pass=容器 readOnlyRootFilesystem=true 且 imagePullPolicy != Always，fail=否则，na=不适用
**修复建议**: 在所有业务容器设置 `readOnlyRootFilesystem: true`；必要时增加 emptyDir/PVC 存放可写目录
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.2.1 "Ensure that container filesystem is immutably deployed"
**攻击面关联**: AS-1 逃逸（可写镜像层令攻击者下载并执行挖矿 / 后门二进制）

---

### K8s-7.2.2 容器临时性权限提升受限（initContainers 不允许特提升）

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.initContainers[]? | select(.securityContext.privileged == true or .securityContext.allowPrivilegeEscalation == true) | .name' | head -10")
```

**期望值**: initContainers 不再使用 privileged 或 allowPrivilegeEscalation: true
**判定标准**: pass=initContainers 全部不使用特权或 allowPrivilegeEscalation，fail=发现 init 容器特权越权，na=不适用
**修复建议**: 移除 init 容器中的 privileged:true 或 allowPrivilegeEscalation:true；改用 fsGroup / setFCap 准入有限小权限
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 7.2.2 "Ensure that init containers do not use privileged or privilege escalation"
**攻击面关联**: AS-1 逃逸（init 容器在 Pod 启动早期以特权运行，常被忽视但同样可实现逃逸）
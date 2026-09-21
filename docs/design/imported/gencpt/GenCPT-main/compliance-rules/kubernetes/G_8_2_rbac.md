# G_8_2 RBAC 配置（13 条）

CIS Kubernetes Benchmark v1.8.0 — 8.2 Kubernetes Policies: RBAC 权限最小化与等效越权角色检查。
覆盖 K8s-8.2.1 至 K8s-8.2.13，共 13 条规则。
覆盖 cluster-admin 数量、clusterrole wildcards、impersonation、system:anonymous、aggregate-to-admin、ServiceAccount token 暴露面等权限提升攻击场景。

---

### K8s-8.2.1 cluster-admin 角色绑定数量受控

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get clusterrolebinding -o json 2>/dev/null | jq -r '.items[] | select(.roleRef.name == \"cluster-admin\") | .metadata.name'")
```

**期望值**: cluster-admin ClusterRoleBinding 数量受控（建议 ≤ 2，仅限运维白名单用户/SA）
**判定标准**: pass=cluster-admin binding 数 ≤ 合规上限，fail=超过上限或含未审计主体，na=不适用
**修复建议**: 移除冗余 cluster-admin 绑定，改用 least-privilege ClusterRole + 针对命名空间 RoleBinding
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.1 "Ensure that the cluster-admin role is granted to the minimum number of subjects"
**攻击面关联**: AS-2 认证授权（cluster-admin 直通 RBAC 逃逸至 root 等价权限）

---

### K8s-8.2.2 ClusterRole 不使用通配符权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get clusterroles -o json 2>/dev/null | jq -r '.items[] | select(.metadata.name | startswith(\"system:\") | not) | select(.rules[]?.verbs | index(\"*\")) | select(.rules[]?.resources | index(\"*\")) | .metadata.name'")
```

**期望值**: 自定义 ClusterRole 不使用 `verbs: ["*"]` 或 `resources: ["*"]`
**判定标准**: pass=未发现使用 *:* 通配，fail=存在 *:* 通配的 ClusterRole，na=不适用
**修复建议**: 收敛 ClusterRole 为具体 verbs/resources 子集
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.2 "Ensure that wildcard verbs and resources are not used in ClusterRoles"
**攻击面关联**: AS-2 认证授权（通配符 ClusterRole 等价 root RBAC）

---

### K8s-8.2.3 ClusterRole 不授予 impersonate 权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get clusterroles -o json 2>/dev/null | jq -r '.items[] | select(.rules[]?.resources | index(\"impersonate\") or index(\"impersonate:serviceaccounts\") ) | .metadata.name'")
```

**期望值**: impersonate 权限仅授予可信 OIDC provider / 服务网格组件
**判定标准**: pass=impersonate 权限仅授予审批白名单主体，fail=任意业务用户绑定 impersonate role，na=不适用
**修复建议**: 移除 impersonate verbs 上的 ClusterRole 配置，仅 OIDC 服务保留
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.3 "Ensure that impersonation permissions are granted appropriately"
**攻击面关联**: AS-2 认证授权（含 impersonate 权限者可冒名 cluster-admin 调用 API）

---

### K8s-8.2.4 系统保留命名空间设置 default ServiceAccount 关闭自动 mount

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get sa default -n kube-system -o json 2>/dev/null | jq -r '.automountServiceAccountToken'")
```

**期望值**: `automountServiceAccountToken: false`
**判定标准**: pass=default SA automountServiceAccountToken=false，fail=未设置或为 true（默认 true），na=不适用
**修复建议**: `kubectl patch sa default -n kube-system -p '{\"automountServiceAccountToken\": false}'`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.4 "Ensure that the default service account in the kube-system namespace does not automount its token"
**攻击面关联**: AS-2 认证授权（kube-system default SA token 权限较高，被入侵 Pod 直用即权限提升）

---

### K8s-8.2.5 default ServiceAccount 在所有业务命名空间关闭 token 自动挂载

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get ns --no-headers 2>/dev/null | awk '{print \$1}' | while read ns; do CONFIG=\$(kubectl get sa default -n \$ns -o json 2>/dev/null | jq -r '.automountServiceAccountToken // \"default\"'); echo \"\$ns: \$CONFIG\"; done")
```

**期望值**: 业务命名空间中 default ServiceAccount 均显式 `automountServiceAccountToken: false`
**判定标准**: pass=所有业务命名空间 default SA automountServiceAccountToken=false，fail=存在 default SA 仍挂载，na=不适用
**修复建议**: 对每个业务命名空间执行 `kubectl patch sa default -n <ns> -p '{"automountServiceAccountToken": false}'`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.5 "Ensure that the default service account is disabled in all namespaces"
**攻击面关联**: AS-2 认证授权（default SA token 是被入侵 Pod 最易获取的 API 凭证）

---

### K8s-8.2.6 业务 ServiceAccount 应用最小权限 RoleBinding

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get rolebindings -A -o json 2>/dev/null | jq -r '.items[] | select(.roleRef.kind == \"Role\" or .roleRef.kind == \"ClusterRole\") | select(.subjects[]?.kind == \"ServiceAccount\") | \"\\(.metadata.namespace)/\\(.metadata.name) -> \\(.roleRef.name)\"' | head -n 30")
```

**期望值**: 多数 SA 使用 RoleBinding 而非全局 ClusterRoleBinding，且仅访问必要资源
**判定标准**: pass=SA 主要通过 RoleBinding 限制在命名空间内，fail=大量 SA 直接绑定 ClusterRoleBinding，na=不适用
**修复建议**: 拆解 ClusterRoleBinding 为命名空间内 RoleBinding 或继承 default-deny baseline
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.6 "Ensure that user-created ServiceAccounts are bound to least-privilege RoleBindings"
**攻击面关联**: AS-2 认证授权（SA 直接绑 ClusterRoleBinding 令单 Pod 被入侵即跨命名空间越权）

---

### K8s-8.2.7 系统命名空间不暴露业务工作负载

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get deployments -n kube-system -o json 2>/dev/null | jq -r '.items[] | select(.metadata.labels.app != null) | .metadata.name' | head -20")
```

**期望值**: kube-system 不部署业务应用，仅系统组件
**判定标准**: pass=kube-system 仅含系统组件，fail=发现业务应用部署在 kube-system，na=不适用
**修复建议**: 将业务应用迁移至专用业务命名空间，避免与系统插件共享 RBAC 边界
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.7 "Ensure that user-created workloads are not deployed to the kube-system namespace"
**攻击面关联**: AS-2 认证授权（kube-system 默认权限较高且审计宽松，业务应用直入便于权限提升）

---

### K8s-8.2.8 Kubernetes Dashboard 类特权 UI 不暴露公网

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get svc -A 2>/dev/null | grep -iE 'dashboard|^kubernetes.*dashboard'")
```

**期望值**: Kubernetes Dashboard 不通过 LoadBalancer / NodePort 直接对外暴露
**判定标准**: pass=Dashboard 仅 ClusterIP 暴露或未部署，fail=Dashboard 暴露公网 IP/NodePort，na=不适用（未安装）
**修复建议**: 改 ClusterIP + 显式 RBAC login / OIDC ingress；严禁 admin privileges ServiceAccount
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.8 "Ensure that Kubernetes Dashboard is not exposed to the public network"
**攻击面关联**: AS-2 认证授权（Dashboard 历史多次出现 SSRF/RCE，公网暴露直接入侵跳板）

---

### K8s-8.2.9 只读 API 端点配置 NodeRestriction 与 ResourceQuota 保护

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get ns --no-headers 2>/dev/null | awk '{print \$1}' | while read ns; do Q=\$(kubectl get resourcequota -n \$ns --no-headers 2>/dev/null | wc -l); echo \"\$ns: \$Q\"; done")
```

**期望值**: 业务命名空间配置 ResourceQuota 与 NetworkPolicy 形成多级限流
**判定标准**: pass=关键命名空间显式配置 ResourceQuota，fail=业务命名空间无 ResourceQuota，na=不适用
**修复建议**: 在业务命名空间添加 ResourceQuota（CPU/mem/Pod count）并配合 LimitRange
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.9 "Ensure that ResourceQuota and LimitRange are applied to namespaces"
**攻击面关联**: AS-5 拒绝服务（无 ResourceQuota 令攻击者纵向爆炸式调度 Pod 耗尽集群）

---

### K8s-8.2.10 命名空间设置 NetworkPolicy 限流

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get networkpolicy -A 2>/dev/null | grep -v NAMESPACE | wc -l; kubectl get ns --no-headers 2>/dev/null | awk '{print \$1}' | while read ns; do echo -n \"\$ns: \"; kubectl get networkpolicy -n \$ns --no-headers 2>/dev/null | wc -l; done")
```

**期望值**: 每个业务命名空间至少 1 条 NetworkPolicy
**判定标准**: pass=每个业务命名空间 ≥1 条 NetworkPolicy，fail=部分命名空间缺 NP，na=不适用（CNI 不支持）
**修复建议**: 使用 Calico/Cilium 的 GlobalDefault 模板，对新增命名空间自动应用默认拒绝
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.10 "Ensure that NetworkPolicy is applied to every namespace"
**攻击面关联**: AS-3 网络（无 NP 命名空间内部 Pod 全互通）

---

### K8s-8.2.11 默认命名空间 default 无业务工作负载

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -n default --no-headers 2>/dev/null")
```

**期望值**: default 命名空间不存在业务 Pod
**判定标准**: pass=default 命名空间无业务 Pod，fail=发现业务工作负载部署于 default，na=不适用（已迁移至新命名空间）
**修复建议**: 将工作负载迁移到分隔的业务命名空间，default 不承载应用
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.11 "Ensure that the default namespace is not used for user workloads"
**攻击面关联**: AS-2 认证授权（default 命名空间无显式 RBAC 边界）

---

### K8s-8.2.12 RBAC 不直接使用 system:anonymous 与 system:unauthenticated 组授权

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get clusterrolebindings,rolebindings -A -o json 2>/dev/null | jq -r '.items[] | select(.subjects[]?.name == \"system:anonymous\" or .subjects[]?.name == \"system:unauthenticated\") | .metadata.name' || echo 'NONE'")
```

**期望值**: 系统不存在绑定 system:anonymous / system:unauthenticated 的 ClusterRoleBinding/RoleBinding
**判定标准**: pass=无相关绑定，fail=发现绑定，na=不适用
**修复建议**: 删除该绑定或将其 subjects 改为受控用户
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.12 "Ensure that the system:anonymous and system:unauthenticated groups are not bound"
**攻击面关联**: AS-2 认证授权（绑定 anonymous/unauthenticated 等价完全匿名特权访问）

---

### K8s-8.2.13 Kubeconfig 集群 Endpoint 仅指向受控控制平面

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl config view 2>/dev/null | grep -E 'server:'")
```

**期望值**: server URL 指向受控控制平面（如 127.0.0.1、控制平面 VIP 或服务 DNS），非公网直接 IP
**判定标准**: pass=server 指向受控内网/VIP/官方 K8s API 接入域名，fail=指向公网 IP 或可疑 endpoint，na=不适用
**修复建议**: 调整 kubeconfig 中 current-context 的 server 字段至受控 API endpoint，确保走 TLS
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.2.13 "Ensure that the kubeconfig file contains only verified control plane endpoints"
**攻击面关联**: AS-3 网络（kubeconfig 指向恶意 endpoint 令运维操作被劫持到伪 API Server）
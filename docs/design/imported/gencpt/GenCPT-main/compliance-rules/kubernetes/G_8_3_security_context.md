# G_8_3 安全上下文（2 条）

CIS Kubernetes Benchmark v1.8.0 — 8.3 Kubernetes Policies: Pod SecurityContext 详细配置。
覆盖 K8s-8.3.1 至 K8s-8.3.2，共 2 条规则。
覆盖 fsGroup/runAsUser/runAsGroup 设置与 SELinux/AppArmor 上下文管理。

---

### K8s-8.3.1 Pod fsGroup / runAsUser / runAsGroup 明确配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select(.metadata.namespace != \"kube-system\") | .spec.containers[] | .securityContext | select( (.runAsUser // 0) == 0 or (.runAsGroup // .podTemplate.securityContext.runAsGroup // 0) == 0 or (.fsGroup // .spec.securityContext.fsGroup // 0) == 0 ) | .name' | head -20")
```

**期望值**: 业务 Pod 显式声明 `runAsUser`、`runAsGroup`、`fsGroup` 为非 0 值
**判定标准**: pass=三项均显式声明非 0，fail=未声明或任一为 0，na=不适用
**修复建议**: 在 Pod spec 设置：
```yaml
spec:
  securityContext:
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.3.1 "Ensure that fsGroup, runAsUser, and runAsGroup are explicitly set in the Pod Spec"
**攻击面关联**: AS-1 逃逸（root uid 与 root fsGroup 让落盘文件以 root 持有，逃逸后直读主机文件）

---

### K8s-8.3.2 Pod 设置 SELinuxOptions 或 AppArmor profile

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | select((.metadata.annotations[\"container.apparmor.security.beta.kubernetes.io\"] == null or .metadata.annotations[\"container.apparmor.security.beta.kubernetes.io\"] == \"unconfined\") and (.spec.securityContext.seLinuxOptions == null and .spec.containers[].securityContext.seLinuxOptions == null)) | .metadata.namespace + \"/\" + .metadata.name' | head -10 || echo 'NA'")
```

**期望值**: 至少业务 Pod 显式绑定 AppArmor profile（如 `runtime/default`）或 SELinuxOptions
**判定标准**: pass=所有业务 Pod 绑定 AppArmor/SELinux 上下文，fail=未绑定（默认 unconfined），na=不适用（节点不支持 selinux/apparmor）
**修复建议**: 为关键命名空间统一打 annotation `container.apparmor.security.beta.kubernetes.io/<container>: runtime/default`，或节点启用 SELinux enforcing 并通过 seLinuxOptions 设置 type
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.3.2 "Ensure that AppArmor/SELinux is enabled for containers"
**攻击面关联**: AS-1 逃逸（不绑定 MAC 上下文令容器逃逸后所有进程操作不受强制访问控制限制）
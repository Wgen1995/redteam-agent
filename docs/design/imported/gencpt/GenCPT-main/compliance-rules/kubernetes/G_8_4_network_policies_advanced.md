# G_8_4 高级网络策略（4 条）

CIS Kubernetes Benchmark v1.8.0 — 8.4 Kubernetes Policies: 高级 NetworkPolicy 隔离与 CNI 集成。
覆盖 K8s-8.4.1 至 K8s-8.4.4，共 4 条规则。
覆盖命名空间间隔离、kube-system 访问控制、NodePort 暴露面与外部 Ingress 治理。

---

### K8s-8.4.1 命名空间间默认拒绝互通

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get networkpolicy -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.podSelector == {} ) | .metadata.namespace + \"/\" + .metadata.name' | head -30")
```

期望值: 至少关键命名空间存在 `podSelector: {}` deny-all NetworkPolicy 以阻断跨命名空间默认互通
**判定标准**: pass=关键命名空间含 deny-all NetworkPolicy，fail=未存在 deny-all，na=不适用（CNI 不支持）
**修复建议**: 在每个命名空间部署：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.4.1 "Ensure that namespaces are isolated by default"
**攻击面关联**: AS-3 网络（命名空间间默认互通令被入侵 Pod 可横向移动至其他命名空间的高价值目标）

---

### K8s-8.4.2 业务命名空间默认拒绝访问 kube-system

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get networkpolicy -n kube-system -o json 2>/dev/null | jq -r '.items[] | .metadata.name' || echo 'NONE'")
```

**期望值**: kube-system 命名空间存在只允许 kube-system、kubelet、节点 IP 入站的 NetworkPolicy；其他命名空间出站默认拒绝 kube-system
**判定标准**: pass=kube-system 配置了限定入站源的 NetworkPolicy，fail=kube-system 任意 Pod 均可达，na=不适用
**修复建议**: 在 kube-system 部署 NetworkPolicy 仅允许节点、kube-system 自身以及批准的监控组件入站
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.4.2 "Ensure that access to kube-system namespace is restricted"
**攻击面关联**: AS-2 认证授权（业务 Pod 直访 kube-system 上的 kube-dns/etcd Pod 等可能触及安全控制组件）

---

### K8s-8.4.3 NodePort 类型的 Service 受限使用

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get svc -A 2>/dev/null | grep NodePort || echo 'NONE'")
```

**期望值**: 业务 svc 不使用 NodePort 暴露，避免端口攻击面与跨节点流量绕过 NetworkPolicy
**判定标准**: pass=无业务 NodePort，fail=发现业务 NodePort 暴露，na=不适用（基础设施场景如 MetalLB/ingress 控制器豁免）
**修复建议**: 改用 Ingress、LoadBalancer 或 ClusterIP + Gateway / Service Mesh
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.4.3 "Ensure that NodePort services are not used in production"
**攻击面关联**: AS-3 网络（NodePort 任意节点端口可达，攻击面宽带且与 NP 解耦）

---

### K8s-8.4.4 ExternalIPs 类型的 Service 未使用

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get svc -A -o json 2>/dev/null | jq -r '.items[] | select(.spec.externalIPs != null) | .metadata.name' || echo 'NONE'")
```

**期望值**: 不存在 ExternalIPs 类型 Service
**判定标准**: pass=无 externalIPs Service，fail=发现 externalIPs 配置，na=不适用
**修复建议**: 使用 LoadBalancer / MetalLB 静态 IP 模式替代 externalIPs，并启用 DenyServiceExternalIPs 准入插件（见 K8s-1.2.3）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.4.4 "Ensure that services do not use externalIPs"
**攻击面关联**: AS-3 网络（externalIPs 未受准入控制可被劫持节点未分配的 VRRP IP，造成流量劫持）
# G_6_2 默认拒绝网络（1 条）

CIS Kubernetes Benchmark v1.8.0 — 6.2 Kubernetes Policies: 默认拒绝 Egress 网络策略。
覆盖 K8s-6.2.1，共 1 条规则。
确保业务命名空间对出站流量默认拒绝，仅在白名单批准后才开放。

---

### K8s-6.2.1 业务命名空间默认拒绝 Egress

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get namespaces --no-headers 2>/dev/null | awk '{print \$1}' | while read ns; do NP_COUNT=\$(kubectl get networkpolicy -n \$ns -o json 2>/dev/null | jq -r '.items[].spec.policyTypes[]' 2>/dev/null | grep -c 'Egress'); echo \"\$ns: \$NP_COUNT\"; done || kubectl get networkpolicy -A 2>/dev/null")
```

接着验证存在 policyTypes 包含 Egress 且无 egress 条目等于 deny-all：
```bash
ssh_execute(server, "kubectl get networkpolicy -A 2>/dev/null | grep Egress")
```

**期望值**: 关键业务命名空间存在 Egress default deny NetworkPolicy（podSelector: {}、policyTypes: [Egress]、无 egress 条目）
**判定标准**: pass=关键业务命名空间存在 Egress Default Deny，fail=未配置，na=不适用（CNI 不支持 NetworkPolicy 或集群明确通过 Cilium/BGP 等其他方式实现）
**修复建议**: 在关键命名空间部署：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
spec:
  podSelector: {}
  policyTypes: [Egress]
```
并为应用分配按目标的白名单 Egress 准入
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 6.2.1 "Ensure that all user-created namespaces have a default deny egress NetworkPolicy"
**攻击面关联**: AS-3 网络（默认 Egress allow 令被入侵 Pod 可自由外联 C2/外发数据通道）
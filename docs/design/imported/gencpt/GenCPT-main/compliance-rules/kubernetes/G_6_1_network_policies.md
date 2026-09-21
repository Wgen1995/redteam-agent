# G_6_1 Network Policies 配置（2 条）

CIS Kubernetes Benchmark v1.8.0 — 6.1 Kubernetes Policies: Network Policies 配置检查。
覆盖 K8s-6.1.1 至 K8s-6.1.2，共 2 条规则。
确保集群中所有命名空间启用 NetworkPolicy 并具有限流策略。

---

### K8s-6.1.1 所有命名空间均有 NetworkPolicy

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get namespaces --no-headers 2>/dev/null | awk '{print \$1}' | while read ns; do NP_COUNT=\$(kubectl get networkpolicy -n \$ns --no-headers 2>/dev/null | wc -l); echo \"\$ns: \$NP_COUNT\"; done")
```

**期望值**: 每个业务命名空间至少 1 条 NetworkPolicy
**判定标准**: pass=所有命名空间（除 kube-system 等系统命名空间）至少有 1 条 NetworkPolicy，fail=存在业务命名空间无 NetworkPolicy，na=不适用（CNI 不支持 NetworkPolicy 时需记录 NA 并改用 CNI 策略）
**修复建议**: 为每个业务命名空间添加至少一条默认 NetworkPolicy（如拒绝所有入站，再按应用放行）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 6.1.1 "Ensure that all namespaces have NetworkPolicies defined"
**攻击面关联**: AS-3 网络（无 NetworkPolicy 令 Pod 间流量在 L3/L4 互通，攻击者横向移动不受限）

---

### K8s-6.1.2 关键命名空间默认拒绝所有入站

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get networkpolicy -A 2>/dev/null | grep -v 'kube-system' | awk '{print \$1, \$2, \$3}'")
```

接着抽样关键命名空间（kube-system 除外）确认存在 default deny：
```bash
ssh_execute(server, "kubectl get networkpolicy -n <namespace> <policy_name> -o yaml 2>/dev/null | grep -A4 'ingress\|egress'")
```

**期望值**: 业务命名空间存在 ingress default deny（podSelector: {} 且 policyTypes: [Ingress]）
**判定标准**: pass=业务命名空间配置了 Ingress Default Deny，fail=未配置，na=不适用（CNI 不支持 NetworkPolicy）
**修复建议**: 在每个业务命名空间应用如下：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes: [Ingress]
```
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 6.1.2 "Ensure that all namespaces have a default deny ingress NetworkPolicy"
**攻击面关联**: AS-3 网络（默认 Ingress allow 令所有 Pod 都接受陌生 Pod 流量，攻击面爆炸式放大）
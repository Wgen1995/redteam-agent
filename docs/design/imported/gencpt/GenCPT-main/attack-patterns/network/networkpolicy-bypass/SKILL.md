---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.6]
mapped_compliance_families: [网络策略]
---

# networkpolicy-bypass — NetworkPolicy 隔离绕过

命名空间未配置 NetworkPolicy 或策略过于宽松（缺少 default-deny），攻击者从一个 Pod 直接访问另一命名空间的 Pod/IP，绕过本应隔离的租户边界，实现横向移动与数据访问。

---

## 1. 前置条件

- 目标命名空间无 NetworkPolicy，或仅有部分 Pod 命中策略、整体仍允许
- 命名空间内非全部 Pod 被默认 deny 覆盖
- 集群 CNI 支持 NetworkPolicy 并已部署（Calico/Cilium 等）

检查命令：
```bash
# [L0] 探测：检查 NetworkPolicy 总数
kubectl get networkpolicy -A | wc -l
# 期望输出: 较小（无 deny-all 时易绕过）

# [L0] 探测：检查目标命名空间是否有 NetworkPolicy
kubectl get networkpolicy -n <target-ns>
# 期望输出: No resources found（策略缺失）
```

## 2. 探测命令

```bash
# [L0] 探测：列出所有 NetworkPolicy
kubectl get networkpolicy -A -o wide
# 期望输出: 命名空间内策略列表

# [L0] 探测：检查是否有 default-deny
kubectl get networkpolicy -A -o jsonpath='{range .items[*]}{@.metadata.namespace}{"/"}{@.metadata.name}{" policyTypes="}{@.spec.podSelector}{@.spec.policyTypes}{"\n"}{end}'
# 期望输出: 若无 default-deny（podSelector 为空且 policyTypes=Ingress/Egress）则可绕过

# [L1] 容器内探测：列出可达的目标 Pod IP
kubectl get pods -n <target-ns> -o wide | awk '{print $1, $6}'
# 期望输出: 目标 Pod 名称与 IP
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证：跨命名空间访问目标 Pod
kubectl exec -n <source-ns> <source-pod> -- curl -s --max-time 3 http://<target-pod-ip>/
# 期望输出: 目标 Pod 的 HTTP 响应

# [L1] 容器内攻击验证：跨命名空间访问目标服务
kubectl exec -n <source-ns> <source-pod> -- curl -s http://<service>.<target-ns>.svc.cluster.local/
# 期望输出: 目标 Service 响应

# [L2] 容器内攻击验证：扫描目标命名空间 Pod 端口
kubectl exec -n <source-ns> <source-pod> -- nmap -p 1-1000 <target-pod-ip>
# 期望输出: 开放端口列表
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：源 Pod 当前到靶 Pod 的可达性
kubectl exec -n <source-ns> <source-pod> -- curl -s --max-time 2 -o /dev/null -w "%{http_code}" http://<target-pod-ip>/
# 期望输出: 000（被隔离阻断）或 200（无策略时）

# [L0] 攻击后环境对比：未施加防御下持续可达
kubectl exec -n <source-ns> <source-pod> -- curl -s --max-time 2 -o /dev/null -w "%{http_code}" http://<target-pod-ip>/
# 期望输出: 200 → 证明无 NetworkPolicy 隔离
```

差分结论：源命名空间未配置 default-deny NetworkPolicy 时，源 Pod 可跨命名空间访问靶 Pod 并返回 200，证明 NetworkPolicy 隔离被绕过。

## 5. 绕过策略

```bash
# [L0] 检查 default-deny 是否存在
kubectl get networkpolicy -n <source-ns> -o yaml | grep -A3 "podSelector: {}"
# 若无 → 命名空间无 default-deny，整体可绕过

# 绕过方式：
# - [L1] 若有 Ingress deny 但无 Egress deny，从源 Pod 主动出站访问
# - [L2] 若策略仅限特定 label，通过篡改源 Pod 的 label 命中放行规则
# - [L1] 若 IPv6 未被 NetworkPolicy 覆盖，通过 IPv6 地址访问绕过
```

## 6. 证伪条件

```bash
# [L0] 命名空间有严格 default-deny
kubectl get networkpolicy -n <source-ns> -o jsonpath='{range .items[*]}{@.metadata.name}{" "}{@.spec.podSelector}{" "}{@.spec.policyTypes}{"\n"}{end}' | grep -i "deny"
# 输出: 含 default-deny 且 policyTypes=Ingress,Egress → 证伪

# [L1] 跨命名空间访问失败
kubectl exec -n <source-ns> <source-pod> -- curl -s --max-time 3 http://<target-pod-ip>/
# 输出: 超时或 connection refused → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（端口扫描）→ **Level 3**（主动扫描，建议人工确认）
- **L1** 探测命令（curl 跨命名空间访问）→ **Level 2**（轻度探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Lateral Movement / Discovery
- **Technique ID**: T1610
- **Technique Name**: Deploy Container
- **描述**: 攻击者利用命名空间缺少 default-deny NetworkPolicy 或策略过宽，从一个 Pod 直接访问另一命名空间的 Pod/Service，绕过租户网络隔离实现横向移动。
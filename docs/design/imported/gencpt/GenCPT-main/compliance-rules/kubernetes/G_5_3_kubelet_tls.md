# G_5_3 Kubelet TLS 配置（2 条）

CIS Kubernetes Benchmark v1.8.0 — 5.3 Worker Node Configuration: Kubelet TLS 凭证管理。
覆盖 K8s-5.3.1 至 K8s-5.3.2，共 2 条规则。
确保 kubelet 与 API Server 之间的 mTLS 凭证轮换与最小 SAN 控制。

---

### K8s-5.3.1 Kubelet --tls-min-version 设置为 TLS1.2 或更高

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--tls-min-version=[^ ]*' || grep 'tlsMinVersion' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: `--tls-min-version=VersionTLS12` 或 `tlsMinVersion: VersionTLS13`
**判定标准**: pass=TLS min version ≥ TLS1.2，fail=未设置（可能允许 TLS1.0/1.1）或显式为 TLS1.0/1.1，na=不适用
**修复建议**: 在 config.yaml 中设置 `tlsMinVersion: VersionTLS12`（推荐 TLS13）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.3.1 "Ensure that the --tls-min-version argument is set to VersionTLS12 or higher"
**攻击面关联**: AS-3 网络（弱 TLS 版本可被中间人降级攻击解密 kubelet 流量）

---

### K8s-5.3.2 Kubelet --tls-cipher-suites 仅使用强加密套件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--tls-cipher-suites=[^ ]*' || grep -A4 'tlsCipherSuites' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: 仅强加密套件（如 TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 等），不含 RC4/3DES/CBC
**判定标准**: pass=仅使用强加密套件，fail=未设置或包含弱算法，na=不适用
**修复建议**: 在 config.yaml 中显式配置 `tlsCipherSuites` 仅包含 ECDHE_GCM/CHACHA20 套件
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.3.2 "Ensure that the Kubelet only makes use of strong cryptographic algorithms"
**攻击面关联**: AS-3 网络（弱加密套件可被降级攻击解密 kubelet 通信流量）
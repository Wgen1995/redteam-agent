# G_4_1 Kubelet 认证（4 条）

CIS Kubernetes Benchmark v1.8.0 — 4.1 Worker Node Configuration: Kubelet 认证检查。
覆盖 K8s-4.1.1 至 K8s-4.1.4，共 4 条规则。
确保 Kubelet 关闭匿名认证、使用 Webhook 授权、配置客户端 CA 与 TLS 证书。

---

### K8s-4.1.1 Kubelet 禁用匿名认证

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--anonymous-auth=[^ ]*' || cat /var/lib/kubelet/config.yaml 2>/dev/null | grep -A2 'anonymous' | grep 'enabled' || echo 'NOT_SET')")
```

**期望值**: `--anonymous-auth=false` 或 `authentication.anonymous.enabled=false`
**判定标准**: pass=匿名认证显式禁用，fail=未设置（默认 true）或值为 true，na=不适用
**修复建议**: 在 kubelet 启动参数或 `/var/lib/kubelet/config.yaml` 中设置 `authentication.anonymous.enabled: false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.1.1 "Ensure that the --anonymous-auth argument is set to false"
**攻击面关联**: AS-2 认证授权（匿名访问 kubelet 可读取 Pod 列表、执行 exec、调用 /debug/pprof）

---

### K8s-4.1.2 Kubelet 授权模式为 Webhook

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' || cat /var/lib/kubelet/config.yaml 2>/dev/null | grep -A2 'authorization' | grep 'mode' || echo 'NOT_SET')")
```

**期望值**: `--authorization-mode=Webhook` 或 `authorization.mode: Webhook`
**判定标准**: pass=授权模式为 Webhook，fail=未设置（默认 AlwaysAllow）或值为 AlwaysAllow，na=不适用
**修复建议**: 在 `/var/lib/kubelet/config.yaml` 中设置 `authorization.mode: Webhook`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.1.2 "Ensure that the --authorization-mode argument is set to Webhook"
**攻击面关联**: AS-2 认证授权（AlwaysAllow 模式令任何已认证主体对 kubelet 拥有全部权限）

---

### K8s-4.1.3 Kubelet 客户端 CA 文件已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--client-ca-file=[^ ]*' || cat /var/lib/kubelet/config.yaml 2>/dev/null | grep 'clientCAFile' | awk -F: '{print $2}' | xargs || echo 'NOT_SET')")
```

**期望值**: `--client-ca-file` 已设置且指向有效 CA 文件路径
**判定标准**: pass=--client-ca-file 设置且文件存在，fail=未设置或文件不存在，na=不适用
**修复建议**: 在 kubelet 启动参数或 config.yaml 中设置 `authentication.x509.clientCAFile: /etc/kubernetes/pki/ca.crt`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.1.3 "Ensure that the --client-ca-file argument is set as appropriate"
**攻击面关联**: AS-2 认证授权（无 CA 验证则 kubelet 客户端证书可被伪造）

---

### K8s-4.1.4 Kubelet TLS 证书与私钥已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--tls-cert-file=[^ ]*' && ps -ef | grep kubelet | grep -v grep | grep -o -- '--tls-private-key-file=[^ ]*' || cat /var/lib/kubelet/config.yaml 2>/dev/null | grep -E 'tlsCertFile|tlsPrivateKeyFile'")
```

**期望值**: `--tls-cert-file` 与 `--tls-private-key-file` 均已设置且指向有效文件
**判定标准**: pass=两个参数均设置且文件存在，fail=任一参数缺失或文件不存在，na=不适用（使用 kubelet TLS bootstrapping 自动签发场景需结合 rotateCertificates 评估）
**修复建议**: 设置 `--tls-cert-file=/var/lib/kubelet/pki/kubelet.crt --tls-private-key-file=/var/lib/kubelet/pki/kubelet.key` 或开启 TLS bootstrapping + 自动轮换
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.1.4 "Ensure that the --tls-cert-file and --tls-private-key-file arguments are set as appropriate"
**攻击面关联**: AS-3 网络（无 kubelet TLS 则 API Server 与 kubelet 通信明文可被劫持）
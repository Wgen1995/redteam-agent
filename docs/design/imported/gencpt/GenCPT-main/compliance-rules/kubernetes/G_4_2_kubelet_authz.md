# G_4_2 Kubelet 授权配置（7 条）

CIS Kubernetes Benchmark v1.8.0 — 4.2 Worker Node Configuration: Kubelet 配置文件授权项检查。
覆盖 K8s-4.2.1 至 K8s-4.2.7，共 7 条规则。
覆盖 kubelet config.yaml 中认证授权相关字段的完整性与有效性。

---

### K8s-4.2.1 Kubelet 配置文件存在且可被 kubelet 解析

**检查命令 [L0]**:
```bash
ssh_execute(server, "ls -l /var/lib/kubelet/config.yaml 2>/dev/null && kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get --raw /api/v1/nodes/$(hostname) 2>/dev/null | head -5 || echo 'MISSING_OR_INVALID'")
```

**期望值**: 文件存在且 kubelet 实际使用该配置（kubelet 进程命令行包含 --config=/var/lib/kubelet/config.yaml）
**判定标准**: pass=配置文件存在且 kubelet 正在使用，fail=文件缺失或 kubelet 未使用该文件（命令行参数注入），na=不适用
**修复建议**: 显式使用 `--config=/var/lib/kubelet/config.yaml` 启动 kubelet，将所有 kubelet 配置收敛到 config.yaml，禁止通过命令行注入认证授权类参数
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.1 "Ensure that the kubelet configuration file exists and is used by kubelet"
**攻击面关联**: AS-2 认证授权（命令行参数覆盖配置可被 init 容器 / 配置漂移绕过）

---

### K8s-4.2.2 配置文件中 authentication.anonymous.enabled=false

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -A3 'authentication' /var/lib/kubelet/config.yaml 2>/dev/null | grep -A2 'anonymous' | grep 'enabled'")
```

**期望值**: `enabled: false`
**判定标准**: pass=anonymous.enabled=false，fail=未配置或为 true，na=不适用
**修复建议**: 在 config.yaml 的 `authentication.anonymous.enabled` 设为 `false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.2 "Ensure that authentication.anonymous.enabled is set to false in the kubelet configuration file"
**攻击面关联**: AS-2 认证授权（匿名访问 kubelet 可执行 exec、读取 Pod 元数据）

---

### K8s-4.2.3 配置文件中 authentication.webhook.enabled=true

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -A3 'authentication' /var/lib/kubelet/config.yaml 2>/dev/null | grep -A2 'webhook' | grep 'enabled'")
```

**期望值**: `enabled: true`
**判定标准**: pass=webhook.enabled=true，fail=未配置或为 false，na=不适用
**修复建议**: 在 config.yaml 的 `authentication.webhook.enabled` 设为 `true`，让 kubelet 通过 TokenReview 向 API Server 验证 Bearer Token
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.3 "Ensure that authentication.webhook.enabled is set to true in the kubelet configuration file"
**攻击面关联**: AS-2 认证授权（关闭 webhook 则 SA Token 在 kubelet 失效）

---

### K8s-4.2.4 配置文件中 authentication.x509.clientCAFile 已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -A3 'authentication' /var/lib/kubelet/config.yaml 2>/dev/null | grep -A2 'x509' | grep 'clientCAFile'")
```

**期望值**: `clientCAFile` 指向有效 CA 文件路径
**判定标准**: pass=clientCAFile 设置且文件存在，fail=未设置或文件不存在，na=不适用
**修复建议**: 在 config.yaml 中设置 `authentication.x509.clientCAFile: /etc/kubernetes/pki/ca.crt`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.4 "Ensure that the authentication.x509.clientCAFile is set as appropriate in the kubelet configuration file"
**攻击面关联**: AS-2 认证授权（无 CA 验证则客户端证书可被伪造）

---

### K8s-4.2.5 配置文件中 authorization.mode=Webhook

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -A3 'authorization' /var/lib/kubelet/config.yaml 2>/dev/null | grep 'mode'")
```

**期望值**: `mode: Webhook`
**判定标准**: pass=authorization.mode=Webhook，fail=未配置或为 AlwaysAllow，na=不适用
**修复建议**: 在 config.yaml 的 `authorization.mode` 设为 `Webhook`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.5 "Ensure that the authorization.mode is set to Webhook in the kubelet configuration file"
**攻击面关联**: AS-2 认证授权（AlwaysAllow 模式令任何认证主体对 kubelet 拥有全部权限）

---

### K8s-4.2.6 authorization.webhook.cacheAuthorizedTTL 设置合理上限

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -A6 'authorization' /var/lib/kubelet/config.yaml 2>/dev/null | grep 'cacheAuthorizedTTL'")
```

**期望值**: `cacheAuthorizedTTL: 5m0s` 或其他有限时长（建议 ≤ 5m）
**判定标准**: pass=cacheAuthorizedTTL 设置为有限时长且 ≤ 5m0s，fail=未设置或值过大（如 1h），na=不适用
**修复建议**: 在 config.yaml 中设置 `authorization.webhook.cacheAuthorizedTTL: 5m0s`，限制授权缓存有效期防止权限变更后延迟生效
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.6 "Ensure that the authorization.webhook.cacheAuthorizedTTL is set as appropriate"
**攻击面关联**: AS-2 认证授权（缓存有效期过长令权限吊销延迟生效，扩大被盗 SA Token 攻击窗口）

---

### K8s-4.2.7 Kubelet 开启 rotateCertificates 并配置 clientCA

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--rotate-certificates=[^ ]*' || grep 'rotateCertificates' /var/lib/kubelet/config.yaml 2>/dev/null")
```

**期望值**: `--rotate-certificates=true` 或 `rotateCertificates: true`
**判定标准**: pass=rotateCertificates 显式为 true，fail=未配置或为 false，na=不适用
**修复建议**: 在 kubelet 启动参数或 config.yaml 中设置 `rotateCertificates: true`，并将 clientCAFile 指向 API Server CA
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.2.7 "Ensure that the rotateCertificates argument is set to true"
**攻击面关联**: AS-4 数据泄露（关闭轮换则 kubelet 客户端证书长期固定，被盗后无法自动失效）
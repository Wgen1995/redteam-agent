# G_3 Docker 文件权限（10 条）

CIS Docker Benchmark v1.6.0 — 3 Docker Daemon Configuration Files 部分。
覆盖 Docker-17 至 Docker-26，共 10 条规则。
本组规则直接关联 socket-escape 攻击模式的前置条件。

---

### Docker-17 docker.sock 文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /var/run/docker.sock 2>/dev/null || echo 'file not found'")
```

**期望值**: `660` 或更严格
**判定标准**: pass=权限为 660 或更严格，fail=权限宽松于 660（如 666/777），na=docker.sock 位于非标准路径
**修复建议**: `chmod 660 /var/run/docker.sock`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.1 "Ensure that the docker.sock file permissions are set to 660 or more restrictive"
**攻击面关联**: AS-1 容器逃逸（docker.sock 权限过宽松允许非授权用户创建特权容器实现逃逸——socket-escape 攻击模式）

---

### Docker-18 docker.sock 文件属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /var/run/docker.sock 2>/dev/null || echo 'file not found'")
```

**期望值**: `root:docker`
**判定标准**: pass=属主为 root:docker，fail=属主非 root 或组非 docker，na=docker.sock 位于非标准路径
**修复建议**: `chown root:docker /var/run/docker.sock`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.2 "Ensure that the docker.sock file ownership is set to root:docker"
**攻击面关联**: AS-1 容器逃逸（非 root 属主的 docker.sock 可被劫持以创建特权容器——socket-escape 攻击模式关键前置条件）

---

### Docker-19 TLS CA 证书文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/docker/ca.pem 2>/dev/null || echo 'file not found'")
```

进一步检查其他可能的 CA 路径：
```bash
ssh_execute(server, "find /etc/docker/ -name 'ca.pem' -o -name 'ca-cert.pem' -o -name 'cacert.pem' 2>/dev/null | head -5")
```

**期望值**: `444` 或更严格（如 `400`）
**判定标准**: pass=权限为 444 或更严格，fail=权限宽松于 444（如 644/666），na=未配置 TLS 或 CA 证书路径不同
**修复建议**: `chmod 444 /etc/docker/ca.pem`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.3 "Ensure that the TLS CA certificate file permissions are set to 444 or more restrictive"
**攻击面关联**: AS-2 认证授权（CA 证书受损可被用于签发伪造证书接管 Docker API）

---

### Docker-20 TLS CA 证书文件属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/docker/ca.pem 2>/dev/null || echo 'file not found'")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=未配置 TLS 或 CA 证书路径不同
**修复建议**: `chown root:root /etc/docker/ca.pem`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.4 "Ensure that the TLS CA certificate file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 属主可替换 CA 证书实施中间人攻击）

---

### Docker-21 Docker 服务器证书文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/docker/server-cert.pem 2>/dev/null || echo 'file not found'")
```

进一步检查其他可能路径：
```bash
ssh_execute(server, "find /etc/docker/ -name 'server-cert.pem' -o -name 'server-cert.crt' -o -name 'cert.pem' 2>/dev/null | head -5")
```

**期望值**: `400` 或更严格
**判定标准**: pass=权限为 400 或更严格（如 440），fail=权限宽松于 400，na=未配置 TLS 或证书路径不同
**修复建议**: `chmod 400 /etc/docker/server-cert.pem`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.5 "Ensure that the Docker server certificate file permissions are set to 444 or more restrictive"
**攻击面关联**: AS-4 数据泄露（服务器证书含公钥信息但宽松权限暴露部署配置细节）

---

### Docker-22 Docker 服务器证书文件属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/docker/server-cert.pem 2>/dev/null || echo 'file not found'")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=未配置 TLS 或证书路径不同
**修复建议**: `chown root:root /etc/docker/server-cert.pem`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.6 "Ensure that the Docker server certificate file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 属主可替换服务器证书实施中间人攻击）

---

### Docker-23 Docker daemon JSON 文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/docker/daemon.json 2>/dev/null || echo 'file not found'")
```

**期望值**: `644` 或更严格（如 `600`）
**判定标准**: pass=权限为 644 或更严格，fail=权限宽松于 644（如 666/777），na=daemon.json 不存在（使用默认配置）
**修复建议**: `chmod 644 /etc/docker/daemon.json`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.17 "Ensure that the daemon.json file permissions are set to 644 or more restrictive"
**攻击面关联**: AS-2 认证授权（daemon.json 含日志、存储、TLS 等核心配置，被篡改可削弱安全策略）

---

### Docker-24 Docker daemon JSON 文件属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/docker/daemon.json 2>/dev/null || echo 'file not found'")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=daemon.json 不存在
**修复建议**: `chown root:root /etc/docker/daemon.json`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.18 "Ensure that the daemon.json file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 用户可修改 daemon.json 关闭安全配置）

---

### Docker-25 /etc/docker/ 目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/docker/ 2>/dev/null || echo 'directory not found'")
```

**期望值**: `755` 或更严格（如 `700`）
**判定标准**: pass=目录权限为 755 或更严格，fail=权限宽松于 755（如 777），na=目录不存在
**修复建议**: `chmod 755 /etc/docker/`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.19 "Ensure that the /etc/docker directory permissions are set to 755 or more restrictive"
**攻击面关联**: AS-2 认证授权（宽松的 /etc/docker/ 权限允许非授权用户修改 Docker 配置文件）

---

### Docker-26 /var/lib/docker/ 目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /var/lib/docker/ 2>/dev/null || echo 'directory not found'")
```

**期望值**: `710` 或更严格（如 `700`）
**判定标准**: pass=目录权限为 710 或更严格（如 700），fail=权限宽松于 710（如 755/777），na=自定义 Docker 数据目录
**修复建议**: `chmod 710 /var/lib/docker/`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.20 "Ensure that the /var/lib/docker directory permissions are set to 710 or more restrictive"
**攻击面关联**: AS-4 数据泄露（宽松的 /var/lib/docker/ 权限允许非授权用户读取容器层、镜像层和卷数据）
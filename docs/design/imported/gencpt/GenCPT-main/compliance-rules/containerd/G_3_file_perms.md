# G_3 Containerd 文件权限（10 条）

CIS Containerd Benchmark — 文件权限检查。
覆盖 Containerd-3.1 至 Containerd-3.10，共 10 条规则。

---

### Containerd-3.1 containerd.sock 权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /run/containerd/containerd.sock 2>/dev/null || stat -c '%a' /var/run/containerd/containerd.sock 2>/dev/null")
```

**期望值**: `660` 或更严格
**判定标准**: pass=权限为 660 或更严格（如 600），fail=权限宽松于 660（如 666/777），na=文件不存在（containerd 未运行或使用非默认 socket 路径）
**修复建议**: `chmod 660 /run/containerd/containerd.sock`
**CIS映射**: CIS Containerd Benchmark - 3.1 "Ensure containerd.sock file permissions are set to 660 or more restrictive"
**攻击面关联**: AS-2 认证授权（socket 权限过松允许非授权用户直接与 containerd 通信，创建/管理容器）

---

### Containerd-3.2 containerd.sock 属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /run/containerd/containerd.sock 2>/dev/null || stat -c '%U:%G' /var/run/containerd/containerd.sock 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在
**修复建议**: `chown root:root /run/containerd/containerd.sock`
**CIS映射**: CIS Containerd Benchmark - 3.2 "Ensure containerd.sock file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 属主可控制 containerd socket 从而管理所有容器）

---

### Containerd-3.3 config.toml 权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/containerd/config.toml 2>/dev/null")
```

**期望值**: `600` 或更严格
**判定标准**: pass=权限为 600 或更严格（如 400），fail=权限宽松于 600（如 644/666），na=文件不存在（containerd 使用默认配置运行）
**修复建议**: `chmod 600 /etc/containerd/config.toml`
**CIS映射**: CIS Containerd Benchmark - 3.3 "Ensure config.toml file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（config.toml 含运行时配置，宽松权限可被篡改导致安全策略失效）

---

### Containerd-3.4 config.toml 属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/containerd/config.toml 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在
**修复建议**: `chown root:root /etc/containerd/config.toml`
**CIS映射**: CIS Containerd Benchmark - 3.4 "Ensure config.toml file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 用户篡改配置文件可修改安全参数）

---

### Containerd-3.5 Containerd 根目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "ROOT_DIR=$(grep -E 'root\\s*=' /etc/containerd/config.toml 2>/dev/null | awk '{print $3}' | tr -d '\"' || echo '/var/lib/containerd'); stat -c '%a' $ROOT_DIR 2>/dev/null || stat -c '%a' /var/lib/containerd 2>/dev/null")
```

**期望值**: `700` 或更严格
**判定标准**: pass=权限为 700 或更严格，fail=权限宽松于 700，na=根目录不存在或 containerd 使用非本地存储
**修复建议**: `chmod 700 /var/lib/containerd`（或实际 containerd 根目录路径）
**CIS映射**: CIS Containerd Benchmark - 3.5 "Ensure containerd root directory permissions are set to 700 or more restrictive"
**攻击面关联**: AS-4 数据泄露（宽松权限允许非授权用户浏览容器镜像层和元数据）

---

### Containerd-3.6 Containerd 状态目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "STATE_DIR=$(grep -E 'state\\s*=' /etc/containerd/config.toml 2>/dev/null | awk '{print $3}' | tr -d '\"' || echo '/run/containerd'); stat -c '%a' $STATE_DIR 2>/dev/null || stat -c '%a' /run/containerd 2>/dev/null")
```

**期望值**: `700` 或更严格
**判定标准**: pass=权限为 700 或更严格，fail=权限宽松于 700，na=状态目录不存在
**修复建议**: `chmod 700 /run/containerd`（或实际 containerd 状态目录路径）
**CIS映射**: CIS Containerd Benchmark - 3.6 "Ensure containerd state directory permissions are set to 700 or more restrictive"
**攻击面关联**: AS-4 数据泄露（状态目录含运行时信息，宽松权限可泄露容器运行状态）

---

### Containerd-3.7 Containerd CA 证书权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "find /etc/containerd/certs.d /etc/containerd/ssl -name '*.crt' -o -name '*.pem' 2>/dev/null | while read f; do stat -c '%a %n' \"$f\"; done || echo 'NO_CERTS_FOUND'")
```

**期望值**: 所有 CA 证书文件权限为 `644` 或更严格（属主为 root）
**判定标准**: pass=所有证书文件权限 ≤ 644，fail=任一证书文件权限宽松于 644（如 666/777），na=证书目录不存在（未配置 TLS）
**修复建议**: `find /etc/containerd/certs.d /etc/containerd/ssl -name '*.crt' -o -name '*.pem' | xargs chmod 644 && find /etc/containerd/certs.d /etc/containerd/ssl -name '*.crt' -o -name '*.pem' | xargs chown root:root`
**CIS映射**: CIS Containerd Benchmark - 3.7 "Ensure containerd CA certificate file permissions are set to 644 or more restrictive"
**攻击面关联**: AS-5 网络攻击（篡改 CA 证书可实施中间人攻击，截获容器镜像拉取通信）

---

### Containerd-3.8 Containerd 私钥权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "find /etc/containerd/certs.d /etc/containerd/ssl -name '*.key' -o -name '*key.pem' 2>/dev/null | while read f; do stat -c '%a %n' \"$f\"; done || echo 'NO_KEYS_FOUND'")
```

**期望值**: 所有私钥文件权限为 `600` 或更严格
**判定标准**: pass=所有私钥文件权限为 600 或更严格（如 400），fail=任一私钥文件权限宽松于 600，na=私钥文件不存在（未配置 TLS）
**修复建议**: `find /etc/containerd/certs.d /etc/containerd/ssl -name '*.key' -o -name '*key.pem' | xargs chmod 600 && find /etc/containerd/certs.d /etc/containerd/ssl -name '*.key' -o -name '*key.pem' | xargs chown root:root`
**CIS映射**: CIS Containerd Benchmark - 3.8 "Ensure containerd private key file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-4 数据泄露（私钥泄露可解密容器运行时通信或伪造服务端身份）

---

### Containerd-3.9 Containerd 二进制权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' $(which containerd 2>/dev/null) 2>/dev/null && stat -c '%a' $(which ctr 2>/dev/null) 2>/dev/null && stat -c '%a' $(which containerd-shim 2>/dev/null) 2>/dev/null")
```

**期望值**: 所有二进制文件权限为 `755` 或更严格（属主为 root）
**判定标准**: pass=所有二进制权限 ≤ 755 且属主为 root，fail=任一二进制权限宽松于 755 或属主非 root，na=二进制不存在
**修复建议**: `chmod 755 /usr/bin/containerd /usr/bin/ctr /usr/bin/containerd-shim && chown root:root /usr/bin/containerd /usr/bin/ctr /usr/bin/containerd-shim`
**CIS映射**: CIS Containerd Benchmark - 3.9 "Ensure containerd binary file permissions are set to 755 or more restrictive"
**攻击面关联**: AS-1 容器逃逸（篡改二进制可植入后门，配合特权容器实现主机逃逸）

---

### Containerd-3.10 Containerd 服务文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /usr/lib/systemd/system/containerd.service 2>/dev/null || stat -c '%a' /etc/systemd/system/containerd.service 2>/dev/null")
```

**期望值**: `644` 或更严格
**判定标准**: pass=权限为 644 或更严格（如 600），fail=权限宽松于 644（如 666/777），na=服务文件不存在（非 systemd 管理的部署）
**修复建议**: `chmod 644 /usr/lib/systemd/system/containerd.service && chown root:root /usr/lib/systemd/system/containerd.service && systemctl daemon-reload`
**CIS映射**: CIS Containerd Benchmark - 3.10 "Ensure containerd service file permissions are set to 644 or more restrictive"
**攻击面关联**: AS-2 认证授权（篡改服务文件可修改启动参数，如注入恶意 debug 选项）
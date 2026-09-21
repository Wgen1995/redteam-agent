# G_4_3 Kubelet 配置文件权限（1 条）

CIS Kubernetes Benchmark v1.8.0 — 4.3 Worker Node Configuration: Kubelet 配置文件权限检查。
覆盖 K8s-4.3.1，共 1 条规则。
确保 kubelet 配置文件不可被非特权用户读取/篡改。

---

### K8s-4.3.1 Kubelet 配置文件权限与属主

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a %U:%G' /var/lib/kubelet/config.yaml 2>/dev/null")
```

**期望值**: 权限为 `600` 或更严格，属主为 `root:root`
**判定标准**: pass=权限为 600 或更严格且属主为 root:root，fail=权限宽松于 600 或属主非 root:root，na=文件不存在（kubelet 使用命令行参数模式）
**修复建议**: `chmod 600 /var/lib/kubelet/config.yaml && chown root:root /var/lib/kubelet/config.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 4.3.1 "Ensure that the kubelet configuration file permission is set to 600 or more restrictive and ownership is root:root"
**攻击面关联**: AS-2 认证授权（配置文件泄露使攻击者获得 kubelet 认证授权策略与 TLS 凭证路径）
# G_2_1 Etcd 文件权限（4 条）

CIS Kubernetes Benchmark v1.8.0 — 2.1 Etcd Node Configuration: etcd 文件权限与属主检查。
覆盖 K8s-2.1.1 至 K8s-2.1.4，共 4 条规则。
针对 etcd 静态 Pod 清单文件与 etcd 配置文件的权限、属主进行约束。

---

### K8s-2.1.1 etcd Pod 规范文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/manifests/etcd.yaml 2>/dev/null || stat -c '%a' /etc/manifests/etcd.yaml 2>/dev/null")
```

**期望值**: `600` 或更严格（如 `400`）
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600（如 644/666/755），na=文件不存在（非静态 Pod 部署或外置 etcd）
**修复建议**: `chmod 600 /etc/kubernetes/manifests/etcd.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.1.1 "Ensure that the etcd pod specification file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（etcd 清单文件被篡改可注入恶意启动参数关闭 TLS）

---

### K8s-2.1.2 etcd Pod 规范文件属主为 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/kubernetes/manifests/etcd.yaml 2>/dev/null || stat -c '%U:%G' /etc/manifests/etcd.yaml 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在（非静态 Pod 部署或外置 etcd）
**修复建议**: `chown root:root /etc/kubernetes/manifests/etcd.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.1.2 "Ensure that the etcd pod specification file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 属主可篡改 etcd 启动参数关闭 mTLS）

---

### K8s-2.1.3 etcd 配置文件权限（/etc/etcd/etcd.conf）

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/etcd/etcd.conf 2>/dev/null || stat -c '%a' /etc/etcd/etcd.yaml 2>/dev/null || echo 'NOT_FOUND'")
```

**期望值**: `640` 或更严格（如 `600`）
**判定标准**: pass=文件权限为 640 或更严格，fail=权限宽松于 640（如 644/666），na=文件不存在（systemd 静态 Pod 部署不使用 etcd.conf）
**修复建议**: `chmod 640 /etc/etcd/etcd.conf`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.1.3 "Ensure that the etcd configuration file permissions are set to 640 or more restrictive"
**攻击面关联**: AS-4 数据泄露（etcd.conf 含证书路径、监听地址，世界可读泄露拓扑和密钥线索）

---

### K8s-2.1.4 etcd 配置文件属主为 root 或 etcd

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/etcd/etcd.conf 2>/dev/null || stat -c '%U:%G' /etc/etcd/etcd.yaml 2>/dev/null || echo 'NOT_FOUND'")
```

**期望值**: `root:root` 或 `etcd:etcd`
**判定标准**: pass=属主为 root:root 或 etcd:etcd，fail=属主为其他非特权用户，na=文件不存在（systemd 静态 Pod 部署不使用 etcd.conf）
**修复建议**: `chown root:root /etc/etcd/etcd.conf`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.1.4 "Ensure that the etcd configuration file ownership is set to root:root or etcd:etcd"
**攻击面关联**: AS-4 数据泄露（非特权属主可篡改 etcd 配置注入恶意 CA 或重定向 API 调用）
# G_1_1 API Server 文件权限（7 条）

CIS Kubernetes Benchmark v1.8.0 — 1.1 Control Plane Configuration: API Server 文件权限检查。
覆盖 K8s-1.1.1 至 K8s-1.1.7，共 7 条规则。

---

### K8s-1.1.1 API Server pod specification 文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml 2>/dev/null")
```

**期望值**: `600` 或更严格（如 `400`）
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600（如 644/666/755），na=文件不存在（非静态 Pod 部署模式）
**修复建议**: `chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.1 "Ensure that the API server pod specification file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（API Server 文件被篡改可注入恶意启动参数）

---

### K8s-1.1.2 API Server pod specification 文件属主为 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/kubernetes/manifests/kube-apiserver.yaml 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在（非静态 Pod 部署模式）
**修复建议**: `chown root:root /etc/kubernetes/manifests/kube-apiserver.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.2 "Ensure that the API server pod specification file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 属主可篡改 API Server 启动配置）

---

### K8s-1.1.3 etcd 数据目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--data-dir=[^ ]*' | cut -d= -f2")
```
然后针对找到的目录：
```bash
ssh_execute(server, "ETCD_DIR=$(ps -ef | grep etcd | grep -v grep | grep -o -- '--data-dir=[^ ]*' | cut -d= -f2); stat -c '%a' $ETCD_DIR 2>/dev/null")
```

**期望值**: `700` 或更严格
**判定标准**: pass=权限为 700 或更严格，fail=权限宽松于 700，na=非本地 etcd 部署（外置 etcd 集群）
**修复建议**: `chmod 700 /var/lib/etcd`（或实际 etcd 数据目录路径）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.3 "Ensure that the etcd data directory permissions are set to 700 or more restrictive"
**攻击面关联**: AS-4 数据泄露（etcd 存储所有集群 Secret 和配置，宽松权限允许越权读取）

---

### K8s-1.1.4 etcd 数据目录属主为 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "ETCD_DIR=$(ps -ef | grep etcd | grep -v grep | grep -o -- '--data-dir=[^ ]*' | cut -d= -f2); stat -c '%U:%G' $ETCD_DIR 2>/dev/null")
```

**期望值**: `root:root`（单节点 root 运行的 etcd）或 `etcd:etcd`（专用 etcd 用户运行的部署）
**判定标准**: pass=属主为 root:root 或 etcd:etcd，fail=属主为其他非特权用户，na=非本地 etcd 部署
**修复建议**: `chown root:root /var/lib/etcd`（root 运行场景）或 `chown etcd:etcd /var/lib/etcd`（专用 etcd 用户场景）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.4 "Ensure that the etcd data directory ownership is set to root:root"（部分版本要求 etcd:etcd，依部署方式而定）
**攻击面关联**: AS-4 数据泄露（非特权用户可读取 etcd 存储的 Secret 和集群状态）

---

### K8s-1.1.5 admin.conf 文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/admin.conf 2>/dev/null")
```

**期望值**: `600` 或更严格
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600，na=文件不存在（非 kubeadm 部署或文件路径不同）
**修复建议**: `chmod 600 /etc/kubernetes/admin.conf`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.5 "Ensure that the admin.conf file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（admin.conf 含 cluster-admin 凭证，泄露后可完全接管集群）

---

### K8s-1.1.6 admin.conf 文件属主为 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/kubernetes/admin.conf 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在（非 kubeadm 部署或文件路径不同）
**修复建议**: `chown root:root /etc/kubernetes/admin.conf`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.6 "Ensure that the admin.conf file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（admin.conf 含 cluster-admin 凭证，非 root 用户可越权使用）

---

### K8s-1.1.7 scheduler.conf 文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/scheduler.conf 2>/dev/null")
```

**期望值**: `600` 或更严格
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600，na=文件不存在（非 kubeadm 部署或文件路径不同）
**修复建议**: `chmod 600 /etc/kubernetes/scheduler.conf`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.1.7 "Ensure that the scheduler.conf file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（scheduler.conf 含调度器凭证，泄露后可窃取调度器权限并影响工作负载分布）
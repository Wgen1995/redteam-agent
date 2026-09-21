# G_3_1 Controller Manager 安全（4 条）

CIS Kubernetes Benchmark v1.8.0 — 3.1 Control Plane Configuration: Controller Manager 安全检查。
覆盖 K8s-3.1.1 至 K8s-3.1.4，共 4 条规则。
覆盖 Controller Manager 静态 Pod 清单文件权限、属主、绑定地址与 profiling 端点。

---

### K8s-3.1.1 Controller Manager Pod 规范文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/manifests/kube-controller-manager.yaml 2>/dev/null")
```

**期望值**: `600` 或更严格
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600，na=文件不存在（非静态 Pod 部署模式）
**修复建议**: `chmod 600 /etc/kubernetes/manifests/kube-controller-manager.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.1.1 "Ensure that the Controller Manager pod specification file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（CM 清单被篡改可禁用准入控制或注入恶意控制器）

---

### K8s-3.1.2 Controller Manager Pod 规范文件属主为 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/kubernetes/manifests/kube-controller-manager.yaml 2>/dev/null")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=文件不存在（非静态 Pod 部署模式）
**修复建议**: `chown root:root /etc/kubernetes/manifests/kube-controller-manager.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.1.2 "Ensure that the Controller Manager pod specification file ownership is set to root:root"
**攻击面关联**: AS-2 认证授权（非 root 用户可修改 CM 启动参数启用 --use-service-account-credentials=false 等）

---

### K8s-3.1.3 Controller Manager 绑定地址限制为 localhost

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-controller-manager | grep -v grep | grep -o -- '--bind-address=[^ ]*' || cat /etc/kubernetes/manifests/kube-controller-manager.yaml 2>/dev/null | grep -o -- '--bind-address=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--bind-address=127.0.0.1`（或控制平面内网 IP，不得为 0.0.0.0）
**判定标准**: pass=--bind-address 为 127.0.0.1 或受限内网接口，fail=未设置或设置为 0.0.0.0 / ::，na=不适用
**修复建议**: 在 kube-controller-manager 启动参数中设置 `--bind-address=127.0.0.1`，并保证 metrics 端口仅在控制平面可达
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.1.3 "Ensure that the --bind-address argument is set to 127.0.0.1"
**攻击面关联**: AS-3 网络（CM metrics/health 端点暴露可被未授权探测控制循环状态）

---

### K8s-3.1.4 Controller Manager Profiling 已禁用

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-controller-manager | grep -v grep | grep -o -- '--profiling=[^ ]*' || cat /etc/kubernetes/manifests/kube-controller-manager.yaml 2>/dev/null | grep -o -- '--profiling=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--profiling=false`
**判定标准**: pass=参数值为 false，fail=参数值为 true 或未设置（默认 true），na=不适用
**修复建议**: 在 kube-controller-manager 启动参数中设置 `--profiling=false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.1.4 "Ensure that the --profiling argument is set to false"
**攻击面关联**: AS-4 数据泄露（pprof 端点暴露锁竞争、内存堆，可能泄露密钥片段）
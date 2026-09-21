# G_3_2 Scheduler 安全（2 条）

CIS Kubernetes Benchmark v1.8.0 — 3.2 Control Plane Configuration: Scheduler 安全检查。
覆盖 K8s-3.2.1 至 K8s-3.2.2，共 2 条规则。
覆盖 Scheduler 静态 Pod 清单文件权限与 profiling 端点。

---

### K8s-3.2.1 Scheduler Pod 规范文件权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/kubernetes/manifests/kube-scheduler.yaml 2>/dev/null")
```

**期望值**: `600` 或更严格
**判定标准**: pass=权限为 600 或更严格，fail=权限宽松于 600，na=文件不存在（非静态 Pod 部署模式）
**修复建议**: `chmod 600 /etc/kubernetes/manifests/kube-scheduler.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.2.1 "Ensure that the Scheduler pod specification file permissions are set to 600 or more restrictive"
**攻击面关联**: AS-2 认证授权（Scheduler 清单被篡改可注入恶意调度策略导致工作负载分布异常）

---

### K8s-3.2.2 Scheduler Profiling 已禁用

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-scheduler | grep -v grep | grep -o -- '--profiling=[^ ]*' || cat /etc/kubernetes/manifests/kube-scheduler.yaml 2>/dev/null | grep -o -- '--profiling=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--profiling=false`
**判定标准**: pass=参数值为 false，fail=参数值为 true 或未设置（默认 true），na=不适用
**修复建议**: 在 kube-scheduler 启动参数中设置 `--profiling=false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 3.2.2 "Ensure that the --profiling argument is set to false"
**攻击面关联**: AS-4 数据泄露（Scheduler pprof 端点暴露调度队列与算法内部状态）
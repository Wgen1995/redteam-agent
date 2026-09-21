# G_5_6 Kubelet 系统配置（1 条）

CIS Kubernetes Benchmark v1.8.0 — 5.6 Worker Node Configuration: Kubelet 服务级系统配置。
覆盖 K8s-5.6.1，共 1 条规则。
确保 kubelet 以 systemd 服务运行并具备必要的资源限制。

---

### K8s-5.6.1 Kubelet systemd 服务配置正确

**检查命令 [L0]**:
```bash
ssh_execute(server, "systemctl cat kubelet 2>/dev/null | grep -E 'ExecStart|LimitNOFILE|LimitNPROC|Restart' || cat /etc/systemd/system/kubelet.service 2>/dev/null | grep -E 'ExecStart|Limit|Restart'")
```

**期望值**: 服务文件存在，含 `LimitNOFILE` / `LimitNPROC` 资源限制，`Restart=on-failure`
**判定标准**: pass=systemd 服务文件存在且有限制参数，fail=未通过 systemd 管理或未设置资源上限，na=不适用（rancher/eks 等托管场景）
**修复建议**: 在 `/etc/systemd/system/kubelet.service` 或其 drop-in 中添加：
```ini
[Service]
LimitNOFILE=1048576
LimitNPROC=infinity
Restart=on-failure
RestartSec=5
```
然后 `systemctl daemon-reload && systemctl restart kubelet`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.6.1 "Ensure that the kubelet is launched as a systemd service with appropriate resource limits"
**攻击面关联**: AS-5 拒绝服务（无 fd/procs 限制则 kubelet 可被恶意 Pod 触发本地耗尽）
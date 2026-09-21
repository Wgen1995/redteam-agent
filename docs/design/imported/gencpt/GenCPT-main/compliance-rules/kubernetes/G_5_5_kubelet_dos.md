# G_5_5 Kubelet DoS 防护（1 条）

CIS Kubernetes Benchmark v1.8.0 — 5.5 Worker Node Configuration: Kubelet DoS 防护配置。
覆盖 K8s-5.5.1，共 1 条规则。
覆盖 kubelet 状态/事件上报限流配置，限制 etcd 资源消耗。

---

### K8s-5.5.1 Kubelet --event-burst 与 --event-qps 搭配限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -oE -- '--event-burst=[^ ]*|--event-qps=[^ ]*' || grep -E 'eventBurst|eventQPS' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: --event-qps 为有限值（如 5/10），且 --event-burst 为其扩展上限（如 10/20）
**判定标准**: pass=两个参数均设置且为有限值（qps>0），fail=过大的 qps（如 10000+），na=不适用（小型集群可豁免）
**修复建议**: 在 config.yaml 中设置 `eventQPS: 5` 与 `eventBurst: 10`，防止恶意 Pod 灌爆 etcd Event 存储
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.5.1 "Ensure that the --event-burst and --event-qps arguments are set appropriately"
**攻击面关联**: AS-5 拒绝服务（无限 Event 导致 etcd 存储耗尽，集群进入只读）
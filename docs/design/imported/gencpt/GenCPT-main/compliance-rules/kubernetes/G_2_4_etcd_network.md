# G_2_4 Etcd 网络隔离（1 条）

CIS Kubernetes Benchmark v1.8.0 — 2.4 Etcd Node Configuration: etcd 监听地址隔离检查。
覆盖 K8s-2.4.1，共 1 条规则。
确保 etcd 不监听 0.0.0.0 等不可控地址，限制在控制平面网络内。

---

### K8s-2.4.1 etcd 仅监听控制平面网络

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -oE -- '--listen-client-urls=[^ ]*|--listen-peer-urls=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -oE -- '--listen-client-urls=[^ ]*|--listen-peer-urls=[^ ]*'")
```

**期望值**: `--listen-client-urls` 与 `--listen-peer-urls` 不包含 `0.0.0.0` 或 `::`；建议仅监听 127.0.0.1 与控制平面内网接口
**判定标准**: pass=监听地址不含 0.0.0.0/:: 且为受限接口列表，fail=包含 0.0.0.0/:: 或绑定到公网网卡，na=非本地 etcd 部署
**修复建议**: 调整 etcd 启动参数 `--listen-client-urls=https://127.0.0.1:2379,https://<控制平面内网IP>:2379 --listen-peer-urls=https://<控制平面内网IP>:2380`，并在主机防火墙限制 2379/2380 端口暴露范围
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.4.1 "Ensure that the etcd service listens only on the control plane network interfaces"
**攻击面关联**: AS-3 网络（etcd 暴露至公网可被未授权节点直接读取集群 Secret 与配置）
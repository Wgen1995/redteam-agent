# G_2_2 Etcd 配置（2 条）

CIS Kubernetes Benchmark v1.8.0 — 2.2 Etcd Node Configuration: etcd 数据目录与实例化检查。
覆盖 K8s-2.2.1 至 K8s-2.2.2，共 2 条规则。
确保 etcd 使用显式数据目录、在节点上以受控单实例方式运行。

---

### K8s-2.2.1 etcd 显式设置数据目录

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--data-dir=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -o -- '--data-dir=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--data-dir` 参数已显式设置（如 `/var/lib/etcd`）
**判定标准**: pass=--data-dir 已设置且路径不是默认 ${HOME}/default.etcd，fail=未设置或使用默认路径，na=非本地 etcd 部署
**修复建议**: 在 etcd 启动参数中显式设置 `--data-dir=/var/lib/etcd`，并将该目录卷挂载至专用磁盘
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.2.1 "Ensure that the --data-dir argument is set as appropriate"
**攻击面关联**: AS-4 数据泄露（默认数据目录权限通常宽松，且未做磁盘隔离，易被其他 Pod 读取）

---

### K8s-2.2.2 etcd 不可在单节点模式下同时又启用多成员 peer 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ETCD_INSTANCES=$(ps -ef | grep '/etcd' | grep -v grep | wc -l); PEER_PARAM=$(ps -ef | grep etcd | grep -v grep | grep -o -- '--initial-cluster=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -o -- '--initial-cluster=[^ ]*' || echo 'NOT_SET'); echo ETCD_INSTANCES=$ETCD_INSTANCES PEER_PARAM=$PEER_PARAM")
```

**期望值**: 单节点 etcd 时 `--initial-cluster` 仅含本节点（不允许包含其他未授权节点）；多节点 etcd 时所有节点应在已知控制平面节点列表内
**判定标准**: pass=initial-cluster 中的节点列表全部来自经审批的控制平面节点清单，fail=包含未授权节点或单节点模式但 cluster 含多成员，na=不适用（含外置托管 etcd）
**修复建议**: 仅使用预定义的控制平面节点构成 `--initial-cluster`，使用 TLS 验证成员身份并定期核对成员列表 `etcdctl member list`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.2.2 "Ensure that the --initial-cluster argument is set to a known and verified set of control plane members"
**攻击面关联**: AS-2 认证授权（未授权节点加入 etcd 集群即可读取/写入全部集群状态数据）
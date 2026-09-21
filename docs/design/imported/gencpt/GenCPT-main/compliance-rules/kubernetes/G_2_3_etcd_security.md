# G_2_3 Etcd 安全配置（4 条）

CIS Kubernetes Benchmark v1.8.0 — 2.3 Etcd Node Configuration: etcd 客户端/Peer TLS 与 mTLS 检查。
覆盖 K8s-2.3.1 至 K8s-2.3.4，共 4 条规则。
确保 etcd 启用双向 TLS，防止数据流量被窃听、伪造或劫持。

---

### K8s-2.3.1 etcd 客户端证书与密钥已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--cert-file=[^ ]*' && ps -ef | grep etcd | grep -v grep | grep -o -- '--key-file=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -oE -- '--cert-file=[^ ]*|--key-file=[^ ]*' | head -2")
```

**期望值**: `--cert-file` 与 `--key-file` 均已设置且指向有效文件路径
**判定标准**: pass=两个参数均设置且文件存在，fail=任一参数缺失或文件不存在，na=非本地 etcd 部署
**修复建议**: 设置 `--cert-file=/etc/kubernetes/pki/etcd/server.crt --key-file=/etc/kubernetes/pki/etcd/server.key`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.3.1 "Ensure that the --cert-file and --key-file arguments are set as appropriate"
**攻击面关联**: AS-4 数据泄露（无 etcd 客户端 TLS 则 API Server 与 etcd 流量明文传输）

---

### K8s-2.3.2 etcd 客户端 CA 文件已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--trusted-ca-file=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -o -- '--trusted-ca-file=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--trusted-ca-file` 已设置且指向有效 CA 文件
**判定标准**: pass=--trusted-ca-file 设置且文件存在，fail=未设置或文件不存在，na=非本地 etcd 部署
**修复建议**: 设置 `--trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.3.2 "Ensure that the --trusted-ca-file argument is set as appropriate"
**攻击面关联**: AS-2 认证授权（无 CA 验证则 etcd 客户端证书可被伪造）

---

### K8s-2.3.3 etcd Peer 证书与密钥已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--peer-cert-file=[^ ]*' && ps -ef | grep etcd | grep -v grep | grep -o -- '--peer-key-file=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -oE -- '--peer-cert-file=[^ ]*|--peer-key-file=[^ ]*'")
```

**期望值**: `--peer-cert-file` 与 `--peer-key-file` 均已设置且指向有效文件
**判定标准**: pass=两个参数均设置且文件存在，fail=任一参数缺失或文件不存在，na=单节点 etcd（无 peer 通信）
**修复建议**: 设置 `--peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt --peer-key-file=/etc/kubernetes/pki/etcd/peer.key`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.3.3 "Ensure that the --peer-cert-file and --peer-key-file arguments are set as appropriate"
**攻击面关联**: AS-3 网络（无 Peer TLS 则 etcd 集群成员间流量明文，可被窃听集群拓扑与状态变更）

---

### K8s-2.3.4 etcd Peer 客户端证书认证已启用

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep etcd | grep -v grep | grep -o -- '--peer-client-cert-auth=[^ ]*' || cat /etc/kubernetes/manifests/etcd.yaml 2>/dev/null | grep -o -- '--peer-client-cert-auth=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--peer-client-cert-auth=true`
**判定标准**: pass=参数值为 true，fail=未设置（默认 false）或值为 false，na=单节点 etcd（无 peer 通信）
**修复建议**: 在 etcd 启动参数中设置 `--peer-client-cert-auth=true` 并配置 `--peer-trusted-ca-file`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 2.3.4 "Ensure that the --peer-client-cert-auth argument is set to true"
**攻击面关联**: AS-2 认证授权（未启用 peer mTLS 则节点可被冒名加入 etcd 集群获取轮转密钥）
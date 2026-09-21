# G_7 Docker Swarm 集群配置（3 条）

CIS Docker Benchmark v1.6.0 — 6 Docker Swarm Configuration 部分。
覆盖 Docker-62 至 Docker-64，共 3 条规则。

---

### Docker-62 Swarm 模式 TLS 加密

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null; docker info 2>/dev/null | grep -A10 'Swarm'")
```

进一步检查 Swarm 通信加密状态：
```bash
ssh_execute(server, "docker node ls 2>/dev/null | head -5; docker network ls --filter driver=overlay 2>/dev/null | head -5")
```

检查 overlay 网络加密：
```bash
ssh_execute(server, "for net in $(docker network ls --filter driver=overlay -q 2>/dev/null); do docker network inspect \"$net\" --format '{{.Name}} encrypted={{.Encrypted}}' 2>/dev/null; done")
```

**期望值**: Swarm 节点间通信使用 TLS 加密，overlay 网络启用了加密
**判定标准**: pass=Swarm 通信已加密（TLS by default in Swarm mode）且 overlay 网络启用了 encrypted，fail=存在未加密的 overlay 网络，na=未使用 Swarm 模式
**修复建议**: 创建加密 overlay 网络：
```bash
docker network create --driver overlay --opt encrypted mynet
```
确保 Swarm 初始化时使用 autolock：
```bash
docker swarm init --autolock
docker swarm update --autolock=true
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 6.1 "Ensure that Swarm overlay network encryption is configured" 及 6.2
**攻击面关联**: AS-3 网络嗅探（未加密的 Swarm 通信可被中间人攻击嗅探集群管理流量和数据）

---

### Docker-63 mTLS 双向认证

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker info 2>/dev/null | grep -A5 'Swarm' | grep -i 'TLS'; docker swarm ca 2>/dev/null | head -3")
```

进一步检查节点证书有效期和轮换策略：
```bash
ssh_execute(server, "docker system info --format '{{.Swarm.Cluster}}' 2>/dev/null; openssl x509 -in /var/lib/docker/swarm/certificates/swarm-node.crt -noout -dates 2>/dev/null || echo 'no local certs'")
```

**期望值**: Swarm 节点间使用 mTLS 相互认证，证书有效且未过期
**判定标准**: pass=Swarm mTLS 已启用且证书有效，fail=mTLS 未启用或证书已过期，na=未使用 Swarm 模式
**修复建议**: 确保 Swarm 使用 TLS 证书（默认已启用 mTLS）：
```bash
# 查看 CA 信息
docker swarm ca

# 轮换证书
docker swarm update --rotate-worker-token
docker swarm update --rotate-manager-token

# 更新证书有效期
docker swarm update --cert-expiry 2160h0m0s
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 6.3 "Ensure that Docker's secret management is used for Swarm" 及 mTLS 相关
**攻击面关联**: AS-2 认证授权（无 mTLS 允许未授权节点加入 Swarm 集群获取集群控制权）

---

### Docker-64 集群管理密钥轮换

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker swarm unlock-key 2>/dev/null || echo 'swarm not locked or not manager'; ls -la /var/lib/docker/swarm/certificates/ 2>/dev/null || echo 'no certificates directory'")
```

进一步检查 autolock 状态：
```bash
ssh_execute(server, "docker info --format '{{.Swarm.Cluster.Spec.EncryptionConfig.AutoLockManger}}' 2>/dev/null || echo 'not available'; docker node ls --format '{{.Hostname}} {{.Status}}' 2>/dev/null | head -5")
```

进一步检查密钥轮换历史：
```bash
ssh_execute(server, "stat -c '%Y %n' /var/lib/docker/swarm/certificates/swarm-node.crt 2>/dev/null; docker swarm update --help 2>/dev/null | grep -E 'rotate|cert-expiry' || echo 'not available'")
```

**期望值**: Swarm autolock 已启用，管理密钥定期轮换
**判定标准**: pass=autolock 已启用且密钥已定期轮换，fail=autolock 未启用或密钥从未轮换，na=未使用 Swarm 模式
**修复建议**: 启用 Swarm autolock 并定期轮换密钥：
```bash
# 启用 autolock
docker swarm update --autolock=true

# 轮换管理密钥
docker swarm update --rotate-manager-raft-key

# 轮换 worker token
docker swarm update --rotate-worker-token

# 设置证书有效期
docker swarm update --cert-expiry 2160h0m0s  # 90 天
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 6.4 "Ensure that manager nodes autolock is enabled" 及密钥管理
**攻击面关联**: AS-2 认证授权（未 autolock 的 Swarm 在重启后密钥存储在磁盘上，被攻陷后可恢复集群控制）
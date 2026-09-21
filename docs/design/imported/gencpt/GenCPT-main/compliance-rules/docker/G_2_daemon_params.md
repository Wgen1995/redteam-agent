# G_2 Docker 守护进程参数（11 条）

CIS Docker Benchmark v1.6.0 — 2 Docker Daemon Configuration 部分。
覆盖 Docker-6 至 Docker-16，共 11 条规则。

---

### Docker-6 HTTPS 代理配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"proxies\",\"not set\"))' 2>/dev/null || echo 'no daemon.json'")
```

进一步检查环境变量：
```bash
ssh_execute(server, "systemctl show docker --property=Environment 2>/dev/null; cat /etc/systemd/system/docker.service.d/http-proxy.conf 2>/dev/null || echo 'no proxy config'")
```

**期望值**: 生产环境配置了安全的 HTTPS 代理，或明确不需要代理
**判定标准**: pass=已配置 HTTPS 代理或环境无代理需求，fail=使用 HTTP 代理或代理配置不当，na=无需代理的隔离环境
**修复建议**: 在 `/etc/systemd/system/docker.service.d/http-proxy.conf` 中配置：
```ini
[Service]
Environment="HTTP_PROXY=https://proxy.example.com:443/"
Environment="HTTPS_PROXY=https://proxy.example.com:443/"
Environment="NO_PROXY=localhost,127.0.0.1,.internal"
```
然后 `systemctl daemon-reload && systemctl restart docker`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.5 "Ensure HTTPS proxy is configured for Docker daemon"
**攻击面关联**: AS-3 网络嗅探（HTTP 代理泄露 Docker 拉取镜像流量中的认证信息）

---

### Docker-7 日志级别

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker info --format '{{.LoggingDriver}}' 2>/dev/null; ps -ef | grep dockerd | grep -v grep | grep -oE '\\-\\-log-level [^ ]+' || echo 'no --log-level flag'")
```

进一步检查 daemon.json 中的日志级别：
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"log-level\",\"not set\"))' 2>/dev/null")
```

**期望值**: 日志级别为 `info` 或 `warn`，不应为 `debug`
**判定标准**: pass=日志级别为 info/warn/error，fail=日志级别为 debug（泄露敏感信息），na=使用默认 info 级别
**修复建议**: 在 `/etc/docker/daemon.json` 中设置：
```json
{
  "log-level": "info"
}
```
或启动参数 `--log-level=info`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.6 "Ensure Docker daemon's log level is set to 'info'"
**攻击面关联**: AS-4 数据泄露（debug 级别日志可能包含环境变量、认证凭据等敏感信息）

---

### Docker-8 SELinux 支持

**检查命令 [L0]**:
```bash
ssh_execute(server, "getenforce 2>/dev/null || echo 'SELinux not installed'; docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -i selinux")
```

进一步检查 Docker 是否启用了 SELinux：
```bash
ssh_execute(server, "ps -ef | grep dockerd | grep -v grep | grep -oE '\\-\\-selinux-enabled' || echo 'no --selinux-enabled flag'; cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"selinux-enabled\",\"not set\"))' 2>/dev/null")
```

**期望值**: SELinux 为 Enforcing 模式且 Docker 已启用 `--selinux-enabled`
**判定标准**: pass=SELinux Enforcing 且 Docker 已启用 SELinux 支持，fail=SELinux Disabled/Permissive 或 Docker 未启用 SELinux，na=系统不支持 SELinux（如 Ubuntu 默认 AppArmor）
**修复建议**: 启用 SELinux：
```bash
setenforce 1
sed -i 's/SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
```
在 `/etc/docker/daemon.json` 中添加：
```json
{
  "selinux-enabled": true
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.7 "Ensure SELinux support is enabled"
**攻击面关联**: AS-1 容器逃逸（缺少 MAC 约束增加容器逃逸和横向移动风险）

---

### Docker-9 挂载传播模式

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep dockerd | grep -v grep | grep -oE '\\-\\-mount-(type|namespace)[^ ]*' || echo 'no mount flags'; cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"mount-namespace-daemon\",\"not set\"))' 2>/dev/null")
```

**期望值**: Docker 守护进程使用了共享挂载传播，或仅在必要时配置
**判定标准**: pass=挂载传播配置合理（默认 slave 模式或已明确配置非 shared），fail=使用 rshared 传播模式（可能泄露宿主机挂载信息），na=使用默认配置
**修复建议**: 在 `/etc/docker/daemon.json` 中或启动参数中确保不使用 `shared` 传播模式：
```bash
dockerd --mount-namespace-daemon=slave
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.8 "Ensure mount propagation mode is not set to shared"
**攻击面关联**: AS-1 容器逃逸（shared 挂载传播可让容器感知宿主机挂载变化并影响宿主机文件系统）

---

### Docker-10 userland-proxy 禁用

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"userland-proxy\",\"not set (default true)\"))' 2>/dev/null")
```

进一步检查进程：
```bash
ssh_execute(server, "ps -ef | grep docker-proxy | grep -v grep | wc -l 2>/dev/null")
```

**期望值**: `userland-proxy` 设置为 `false`
**判定标准**: pass=userland-proxy 设置为 false，fail=userland-proxy 为 true（默认），na=NAT 环境必须使用 userland-proxy
**修复建议**: 在 `/etc/docker/daemon.json` 中设置：
```json
{
  "userland-proxy": false
}
```
然后 `systemctl restart docker`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.9 "Ensure userland proxy is disabled"
**攻击面关联**: AS-3 网络攻击（userland-proxy 增加攻击面和性能开销，iptables 模式更安全高效）

---

### Docker-11 禁用旧镜像版本

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"disable-legacy-registry\",\"not set\"))' 2>/dev/null || echo 'no daemon.json'")
```

进一步检查启动参数：
```bash
ssh_execute(server, "ps -ef | grep dockerd | grep -v grep | grep -oE '\\-\\-disable-legacy-registry' || echo 'no --disable-legacy-registry flag'")
```

**期望值**: `disable-legacy-registry` 已启用
**判定标准**: pass=已禁用旧版 v1 registry 协议，fail=仍允许旧版 v1 registry（中间人攻击风险），na=无 registry 使用场景
**修复建议**: 在 `/etc/docker/daemon.json` 中添加：
```json
{
  "disable-legacy-registry": true
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.10 "Ensure legacy registry (v1) is disabled"
**攻击面关联**: AS-3 网络攻击（v1 registry 协议无 TLS 支持且存在已知漏洞）

---

### Docker-12 live-restore

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"live-restore\",\"not set (default false)\"))' 2>/dev/null")
```

**期望值**: `live-restore` 设置为 `true`
**判定标准**: pass=live-restore 已启用，fail=live-restore 未启用（Docker 升级时容器会中断），na=不关心容器可用性
**修复建议**: 在 `/etc/docker/daemon.json` 中设置：
```json
{
  "live-restore": true
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.11 "Ensure live restore is enabled"
**攻击面关联**: AS-5 可用性（Docker 守护进程崩溃或升级时容器不中断，减少运维期间安全窗口暴露）

---

### Docker-13 Swarm 模式 TLS

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker info --format '{{.Swarm}}' 2>/dev/null; docker info 2>/dev/null | grep -A5 'Swarm'")
```

进一步检查 TLS 配置：
```bash
ssh_execute(server, "ps -ef | grep dockerd | grep -v grep | grep -oE '\\-\\-tlsverify|\\-\\-tlscacert [^ ]+|\\-\\-tlscert [^ ]+|\\-\\-tlskey [^ ]+' || echo 'no TLS flags'")
```

**期望值**: Swarm 管理通信使用 TLS 加密
**判定标准**: pass=Swarm 模式下节点间通信配置了 TLS，fail=Swarm 通信未加密，na=未使用 Swarm 模式
**修复建议**: 初始化 Swarm 时使用 `--autolock` 并确保 TLS：
```bash
docker swarm init --autolock
```
或在 `/etc/docker/daemon.json` 中配置 TLS 参数
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.12 "Ensure Swarm overlay network encryption is configured" 及 2.13 TLS 相关
**攻击面关联**: AS-3 网络嗅探（未加密的 Swarm 通信可被嗅探获取调度信息和密钥）

---

### Docker-14 ulimit 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"default-ulimits\",\"not set\"))' 2>/dev/null")
```

进一步检查系统默认 ulimit：
```bash
ssh_execute(server, "sh -c 'ulimit -n; ulimit -u; ulimit -f'")
```

**期望值**: 在 daemon.json 中配置了合理的 default-ulimits（如 nofile=65536:65536, nproc=4096:4096）
**判定标准**: pass=已配置合理的 ulimit 默认值，fail=使用系统默认值（通常过高或不合理），na=应用有特殊需求
**修复建议**: 在 `/etc/docker/daemon.json` 中设置：
```json
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    },
    "nproc": {
      "Name": "nproc",
      "Hard": 4096,
      "Soft": 4096
    }
  }
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.14 "Ensure default ulimit is configured appropriately"
**攻击面关联**: AS-4 资源耗尽（无 ulimit 限制时容器可耗尽宿主机文件描述符和进程数）

---

### Docker-15 userns-remap

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"userns-remap\",\"not set\"))' 2>/dev/null")
```

进一步检查系统是否支持 user namespace：
```bash
ssh_execute(server, "cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null || echo 'not available'; grep ^defaultsysmapd /etc/subuid /etc/subgid 2>/dev/null || echo 'no subuid/subgid mapping'")
```

**期望值**: `userns-remap` 已配置（如 `default` 或指定用户映射）
**判定标准**: pass=已启用 userns-remap（容器内 root 映射到宿主机非特权用户），fail=未启用 userns-remap，na=应用需要特权无法使用
**修复建议**: 1. 创建映射用户：
```bash
useradd -r defaultsysmapd
echo "defaultsysmapd:100000:65536" >> /etc/subuid
echo "defaultsysmapd:100000:65536" >> /etc/subgid
```
2. 在 `/etc/docker/daemon.json` 中添加：
```json
{
  "userns-remap": "default"
}
```
注意：启用后需迁移已有容器数据
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.15 "Ensure user namespace remapping is enabled"
**攻击面关联**: AS-1 容器逃逸（userns-remap 将容器 root 映射为宿主机非特权用户，大幅降低逃逸风险）

---

### Docker-16 cgroup-parent

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"cgroup-parent\",\"not set (default /)\"))' 2>/dev/null")
```

进一步检查当前 cgroup 层次：
```bash
ssh_execute(server, "ls /sys/fs/cgroup/docker/ 2>/dev/null | head -5 || echo 'no docker cgroup directory'")
```

**期望值**: `cgroup-parent` 不使用根 cgroup（即不应为 `/` 或 `docker`），使用专用 cgroup 名称
**判定标准**: pass=设置了专用 cgroup-parent（如 `/system.slice/docker`），fail=使用默认根 cgroup 或 `docker`，na=使用 systemd cgroup 驱动默认配置
**修复建议**: 在 `/etc/docker/daemon.json` 中设置：
```json
{
  "cgroup-parent": "/system.slice/docker"
}
```
或配合 systemd cgroup 驱动使用：
```json
{
  "exec-opts": ["native.cgroupdriver=systemd"]
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.16 "Ensure cgroup usage is configured appropriately"
**攻击面关联**: AS-4 资源耗尽（默认 cgroup-parent 允许容器共享根 cgroup 资源，可绕过资源限制）
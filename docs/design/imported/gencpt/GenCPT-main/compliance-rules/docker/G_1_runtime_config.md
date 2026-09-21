# G_1 Docker 运行环境配置（5 条）

CIS Docker Benchmark v1.6.0 — 1 Host Configuration 部分。
覆盖 Docker-1 至 Docker-5，共 5 条规则。

---

### Docker-1 容器宿主机加固

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E '^kernel\\.(搞得|name)' /etc/sysctl.conf /etc/sysctl.d/*.conf 2>/dev/null; sysctl kernel.yama.ptrace_scope 2>/dev/null")
```

进一步检查：
```bash
ssh_execute(server, "sysctl -a 2>/dev/null | grep -E 'kernel\\.randomize_va_space|net\\.ipv4\\.ip_forward|net\\.ipv6\\.conf\\.all\\.forwarding' | head -5")
```

**期望值**: 宿主机内核安全参数已配置（ASLR 开启、ptrace 限制等）
**判定标准**: pass=关键安全 sysctl 参数均已正确配置，fail=存在未加固的内核参数，na=无权限检查
**修复建议**: 在 /etc/sysctl.conf 或 /etc/sysctl.d/ 中配置：
```
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 1
net.ipv4.ip_forward = 0
```
然后执行 `sysctl --system`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 1.1 "Ensure a separate partition for containers has been created"（宿主机整体加固基线）
**攻击面关联**: AS-1 容器逃逸（宿主机内核未加固增加容器逃逸风险）

---

### Docker-2 Docker 版本检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker version --format '{{.Server.Version}}' 2>/dev/null")
```

**期望值**: Docker 版本 >= 24.0（当前 LTS），且非已知的含严重漏洞版本
**判定标准**: pass=Docker 版本为当前稳定版且无已知严重 CVE，fail=版本过旧或包含已知严重漏洞，na=无法获取版本信息
**修复建议**: 升级 Docker Engine 至最新稳定版：
```bash
curl -fsSL https://get.docker.com | sh
systemctl restart docker
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 1.2 "Ensure the version of Docker is up to date"（通用版本要求）
**攻击面关联**: AS-1 容器逃逸（旧版本 Docker 含 runc 逃逸等已知漏洞）

---

### Docker-3 独立分区

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker info --format '{{.DockerRootDir}}' 2>/dev/null")
```
然后检查：
```bash
ssh_execute(server, "DOCKER_DIR=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null); df -h \"$DOCKER_DIR\" 2>/dev/null | tail -1")
```

**期望值**: `/var/lib/docker`（或自定义 Docker 数据目录）挂载在独立分区上
**判定标准**: pass=Docker 数据目录位于独立分区（非 `/` 分区），fail=Docker 数据目录与根分区共享，na=单分区嵌入式/测试环境
**修复建议**: 为 Docker 数据目录创建独立分区或 LVM 卷：
1. 创建新分区（如 `/dev/sdb1`）
2. `mkfs.ext4 /dev/sdb1`
3. 在 `/etc/fstab` 中添加：`/dev/sdb1 /var/lib/docker ext4 defaults 0 0`
4. 迁移数据并重新挂载
**CIS映射**: CIS Docker Benchmark v1.6.0 - 1.1 "Ensure a separate partition for containers has been created"
**攻击面关联**: AS-4 资源耗尽（Docker 数据与根分区共享时容器可填满根文件系统导致宿主机拒绝服务）

---

### Docker-4 审计日志

**检查命令 [L0]**:
```bash
ssh_execute(server, "auditctl -l 2>/dev/null | grep -E 'docker|containerd' | head -20")
```

进一步检查：
```bash
ssh_execute(server, "grep -E 'docker|containerd' /etc/audit/rules.d/*.rules 2>/dev/null")
```

**期望值**: Docker 相关关键路径已配置 auditd 审计规则
**判定标准**: pass=Docker 守护进程、socket、目录等已配置审计规则，fail=未配置审计规则，na=auditd 未安装或容器环境无需审计
**修复建议**: 在 `/etc/audit/rules.d/docker.rules` 中添加：
```
-w /usr/bin/dockerd -p xka -k docker
-w /var/run/docker.sock -p xka -k docker
-w /etc/docker/daemon.json -p wa -k docker
-w /usr/bin/containerd -p xka -k docker
```
然后执行 `augenrules --load`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 1.3 "Ensure auditing is configured for the Docker daemon" 及相关审计规则
**攻击面关联**: AS-5 审计缺失（无审计日志无法追溯容器逃逸或未授权操作）

---

### Docker-5 Docker 守护进程监听

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep dockerd | grep -v grep | grep -oE '\\-H [^ ]+' || echo 'no -H flag'; ss -tlnp | grep dockerd 2>/dev/null")
```

进一步检查：
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"hosts\",\"not set\"))' 2>/dev/null || echo 'no daemon.json or parse error'")
```

**期望值**: Docker 守护进程仅监听 Unix socket (`unix:///var/run/docker.sock`)，不应暴露 TCP 端口（除非配置了 TLS 且限制绑定地址）
**判定标准**: pass=仅监听 Unix socket 或仅 localhost 且有 TLS 加密，fail=暴露 TCP 端口到 0.0.0.0 且无 TLS，na=非标准部署
**修复建议**: 在 `/etc/docker/daemon.json` 中仅使用 Unix socket：
```json
{
  "hosts": ["unix:///var/run/docker.sock"]
}
```
如需远程访问，必须配置 TLS：
```bash
dockerd --tlsverify --tlscacert=/etc/docker/ca.pem --tlscert=/etc/docker/server-cert.pem --tlskey=/etc/docker/server-key.pem -H=0.0.0.0:2376
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.4 "Ensure Docker daemon is not exposed on 0.0.0.0"
**攻击面关联**: AS-1 容器逃逸（未加密的 Docker TCP 端口暴露可被远程利用创建特权容器逃逸）
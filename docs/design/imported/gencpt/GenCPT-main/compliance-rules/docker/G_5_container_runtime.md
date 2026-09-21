# G_5 Docker 容器运行时（26 条）

CIS Docker Benchmark v1.6.0 — 5 Container Runtime 部分。
覆盖 Docker-34 至 Docker-59，共 26 条规则。
本组为最大规则组，多条规则直接关联容器逃逸（AS-1）。

---

### Docker-34 AppArmor 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{.AppArmorProfile}}' \"$c\" 2>/dev/null; done | sort | uniq -c")
```

**期望值**: 容器配置了 AppArmor 配置文件（非空、非 `unconfined`）
**判定标准**: pass=AppArmor 配置文件名不为空且不为 unconfined，fail=AppArmor 为空或 unconfined，na=系统不支持 AppArmor（如 RHEL/CentOS 使用 SELinux）
**修复建议**: 运行时指定 AppArmor 配置：
```bash
docker run --security-opt apparmor=docker-default myapp
```
自定义 AppArmor 配置：
```bash
# 生成配置文件
aa-complain /etc/apparmor.d/docker-myapp
docker run --security-opt apparmor=docker-myapp myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.1 "Ensure that AppArmor Profile is enabled"
**攻击面关联**: AS-1 容器逃逸（无 AppArmor 约束的容器可执行更多系统调用，增加逃逸可能）

---

### Docker-35 SELinux 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{.ProcessLabel}} {{.MountLabel}}' \"$c\" 2>/dev/null; done | sort | uniq -c")
```

**期望值**: 容器配置了 SELinux 标签（如 `system_u:system_r:svirt_lxc_net_t:s0:c100,c200`）
**判定标准**: pass=容器配置了 SELinux 标签，fail=SELinux 标签为空（禁用 SELinux），na=系统不支持 SELinux（如 Ubuntu 使用 AppArmor）
**修复建议**: 运行时指定 SELinux 标签：
```bash
docker run --security-opt label=user:system_u --security-opt label=role:system_r --security-opt label=type:svirt_lxc_net_t myapp
```
或使用 `--security-opt label=level:s0:c100,c200` 指定 MLS/MCS 标签
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.2 "Ensure that SELinux security options are set"
**攻击面关联**: AS-1 容器逃逸（无 SELinux MCS 标签隔离的容器可能跨容器访问文件）

---

### Docker-36 内存限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): memory=$(docker inspect --format '{{.HostConfig.Memory}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 每个容器设置了内存限制（非 0，如 `536870912` 即 512MB）
**判定标准**: pass=容器设置了内存限制且不为 0，fail=内存限制为 0（无限制），na=编排系统已管理资源限制
**修复建议**: 运行时指定内存限制：
```bash
docker run --memory=512m --memory-swap=1g myapp
```
或使用 Compose：
```yaml
services:
  myapp:
    mem_limit: 512m
    memswap_limit: 1g
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.3 "Ensure that Linux kernel capabilities are restricted within containers"（资源限制）
**攻击面关联**: AS-5 拒绝服务（无内存限制的容器可耗尽宿主机内存导致 DoS）

---

### Docker-37 CPU 优先级

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): cpu_shares=$(docker inspect --format '{{.HostConfig.CpuShares}}' \"$c\" 2>/dev/null), cpuset=$(docker inspect --format '{{.HostConfig.CpusetCpus}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 容器设置了 CPU 份额（如 `512` 或 `1024`）或 cpuset 限制
**判定标准**: pass=容器设置了 CPU 份额或 cpuset，fail=CPU 份额为 0（默认值，无限制），na=编排系统已管理 CPU 资源
**修复建议**: 运行时指定 CPU 限制：
```bash
docker run --cpu-shares=512 --cpuset-cpus=0-1 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.4 "Ensure that CPU priorities are set appropriately"（最佳实践）
**攻击面关联**: AS-4 资源耗尽（无 CPU 限制的容器可垄断 CPU 导致其他容器/服务 DoS）

---

### Docker-38 只读根文件系统

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): readonly=$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: `true`
**判定标准**: pass=ReadonlyRootfs 为 true，fail=ReadonlyRootfs 为 false 或为空，na=应用必须写入根文件系统（需配合 tmpfs 挂载）
**修复建议**: 运行时启用只读根文件系统：
```bash
docker run --read-only --tmpfs /run --tmpfs /tmp myapp
```
在 Docker Compose 中：
```yaml
services:
  myapp:
    read_only: true
    tmpfs:
      - /run
      - /tmp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.5 "Ensure that the container's root filesystem is mounted as read only"
**攻击面关联**: AS-1 容器逃逸（可写根文件系统允许攻击者写入恶意二进制和修改配置）

---

### Docker-39 网络模式

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): net=$(docker inspect --format '{{.HostConfig.NetworkMode}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 使用 bridge 或自定义网络（非 `host`）
**判定标准**: pass=使用 bridge/overlay/自定义网络，fail=使用 host 网络模式（容器直接访问宿主机网络栈），na=特殊网络需求
**修复建议**: 避免使用 `--network host`，使用自定义网络：
```bash
docker network create --driver bridge mynet
docker run --network mynet myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.6 "Ensure that the container is not configured to use the host network namespace"
**攻击面关联**: AS-1 容器逃逸（host 网络模式允许容器嗅探宿主机所有网络流量和访问 localhost 服务）

---

### Docker-40 restart 策略

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): restart=$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: restart 策略为 `on-failure` 或 `always`（非空字符串）
**判定标准**: pass=容器配置了明确的 restart 策略（on-failure/always/unless-stopped），fail=策略为空（默认 no），na=编排系统管理重启
**修复建议**: 运行时指定 restart 策略：
```bash
docker run --restart=on-failure:5 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.7 "Ensure that the container's restart policy is set appropriately"（最佳实践）
**攻击面关联**: AS-5 可用性（无 restart 策略时容器崩溃后不会自动恢复，影响服务可用性）

---

### Docker-41 PID cgroup 限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): pids_limit=$(docker inspect --format '{{.HostConfig.PidsLimit}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 设置了 PID 限制（如 `100` 或 `200`），不应为 0 或 -1（无限制）
**判定标准**: pass=PidsLimit > 0 且为合理值，fail=PidsLimit 为 0 或 -1（无限制），na=编排系统已管理 PID 限制
**修复建议**: 运行时指定 PID 限制：
```bash
docker run --pids-limit=100 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.8 "Ensure that the PID cgroup limit is used"
**攻击面关联**: AS-4 资源耗尽（无 PID 限制时容器可 fork bomb 攻击宿主机）

---

### Docker-42 特权模式——关键！

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): privileged=$(docker inspect --format '{{.HostConfig.Privileged}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: `false`
**判定标准**: pass=Privileged 为 false（非特权模式），fail=Privileged 为 true（⚠️ 关键：可直接访问宿主机所有设备），na=无运行中容器
**修复建议**: 移除 `--privileged` 标志，按需添加特定能力：
```bash
# 错误示范
# docker run --privileged myapp

# 正确做法：仅添加必要能力
docker run --cap-add=NET_ADMIN --cap-add=SYS_PTRACE myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.9 "Ensure that the container is not running in privileged mode"
**攻击面关联**: AS-1 容器逃逸（特权容器可直接访问宿主机所有设备，是容器逃逸的首要风险因素）

---

### Docker-43 capabilities——关键！

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): cap_add=$(docker inspect --format '{{.HostConfig.CapAdd}}' \"$c\" 2>/dev/null), cap_drop=$(docker inspect --format '{{.HostConfig.CapDrop}}' \"$c\" 2>/dev/null)\"; done")
```

进一步检查默认 capabilities：
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"):\"; docker inspect --format '{{.HostConfig.CapAdd}}' \"$c\" 2>/dev/null; docker inspect --format '{{.HostConfig.CapDrop}}' \"$c\" 2>/dev/null; done")
```

**期望值**: 仅添加必要的 capabilities，应 drop ALL 再按需 add
**判定标准**: pass=cap_drop 包含 ALL 且仅 cap_add 必要能力，fail=未 drop 任何能力且添加了危险能力（如 SYS_ADMIN、NET_ADMIN、SYS_PTRACE），na=无运行中容器
**修复建议**: 遵循最小权限原则，先 drop ALL 再添加必要能力：
```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```
常见安全能力取舍：
- `SYS_ADMIN`：极危险，应避免
- `NET_ADMIN`：仅网络管理需要
- `SYS_PTRACE`：仅调试需要
- `DAC_OVERRIDE`：大部分不需要
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.10 "Ensure that Linux kernel capabilities are restricted within containers"
**攻击面关联**: AS-1 容器逃逸（过多的 capabilities 特别是 SYS_ADMIN 可直接导致容器逃逸）

---

### Docker-44 seccomp 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): seccomp=$(docker inspect --format '{{.HostConfig.SecurityOpt}}' \"$c\" 2>/dev/null | grep -o 'seccomp=[^ ]*' || echo 'default')\"; done")
```

进一步检查 seccomp 状态：
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{.Name}}: {{.HostConfig.SecurityOpt}}' \"$c\" 2>/dev/null | grep -i seccomp; done")
```

**期望值**: 容器配置了 seccomp 配置文件（非 `unconfined`）
**判定标准**: pass=seccomp 配置为默认或自定义配置文件，fail=seccomp 为 unconfined，na=系统不支持 seccomp
**修复建议**: 使用默认 seccomp 配置或自定义配置：
```bash
# 使用默认配置（Docker 默认已启用）
docker run --security-opt seccomp=default.json myapp

# 自定义配置
docker run --security-opt seccomp=my-seccomp.json myapp

# 绝对不要
# docker run --security-opt seccomp=unconfined myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.11 "Ensure that seccomp is enabled for containers"
**攻击面关联**: AS-1 容器逃逸（无 seccomp 约束允许容器执行危险系统调用如 mount、keyctl 等）

---

### Docker-45 cgroup 使用

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): cgroup=$(docker inspect --format '{{.HostConfig.CgroupParent}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 容器使用专用 cgroup 或默认 cgroup（非宿主机根 cgroup `/`）
**判定标准**: pass=cgroup-parent 为空（使用默认 `/docker`）或专用值，fail=cgroup-parent 为 `/`（宿主机根 cgroup），na=使用 systemd cgroup 驱动
**修复建议**: 运行时指定 cgroup-parent：
```bash
docker run --cgroup-parent=/system.slice/myapp.slice myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.12 "Ensure that the container cgroup is used appropriately"
**攻击面关联**: AS-4 资源耗尽（使用根 cgroup 允许容器绕过资源限制）

---

### Docker-46 add-host 检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): extra_hosts=$(docker inspect --format '{{.HostConfig.ExtraHosts}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: ExtraHosts 为空或仅包含合理条目
**判定标准**: pass=无 --add-host 条目或条目合理且有文档记录，fail=存在可疑的 --add-host 条目（如指向恶意 IP 的域名覆写），na=无运行中容器
**修复建议**: 避免使用 `--add-host`，使用 DNS 或 docker network 代替：
```bash
# 错误示范
# docker run --add-host=internal-api:10.0.0.1 myapp

# 正确做法：使用 DNS
docker run --dns=10.0.0.1 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.13 "Ensure that host devices are not directly exposed to containers"（host 映射安全）
**攻击面关联**: AS-3 网络攻击（恶意 --add-host 可将流量劫持到攻击者控制的服务器）

---

### Docker-47 ulimit 设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): ulimits=$(docker inspect --format '{{.HostConfig.Ulimits}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 容器配置了合理的 ulimit（nofile、nproc 等）
**判定标准**: pass=容器 ulimit 与安全基线一致，fail=ulimit 设置不合理（如 nofile 过高为 unlimited），na=使用 daemon 默认 ulimit
**修复建议**: 运行时指定 ulimit：
```bash
docker run --ulimit nofile=65536:65536 --ulimit nproc=4096:4096 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.14 "Ensure that container ulimits are set appropriately"
**攻击面关联**: AS-4 资源耗尽（无 ulimit 限制允许容器进程耗尽系统资源）

---

### Docker-48 默认 ulimit 检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"default-ulimits\",\"not set\"))' 2>/dev/null || echo 'no daemon.json'")
```

进一步对比运行中容器的实际 ulimit：
```bash
ssh_execute(server, "for c in $(docker ps -q | head -3); do docker exec \"$c\" sh -c 'ulimit -n; ulimit -u' 2>/dev/null; done")
```

**期望值**: daemon.json 中配置了合理的 default-ulimits
**判定标准**: pass=default-ulimits 已配置且值合理，fail=default-ulimits 未配置（使用系统默认值），na=应用有特殊 ulimit 需求
**修复建议**: 在 `/etc/docker/daemon.json` 中设置默认 ulimit：
```json
{
  "default-ulimits": {
    "nofile": {"Name": "nofile", "Hard": 65536, "Soft": 65536},
    "nproc": {"Name": "nproc", "Hard": 4096, "Soft": 4096}
  }
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 2.14 "Ensure default ulimit is configured"
**攻击面关联**: AS-4 资源耗尽（全局默认 ulimit 缺失导致所有容器继承宽松限制）

---

### Docker-49 容器无 SSH

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'which sshd 2>/dev/null && echo SSHD_FOUND || echo NO_SSHD; ps aux 2>/dev/null | grep sshd | grep -v grep | wc -l' 2>/dev/null; done")
```

**期望值**: 容器中无 sshd 进程运行
**判定标准**: pass=容器中无 sshd 进程和二进制，fail=容器中存在 sshd 进程，na=容器用途为 SSH 跳板
**修复建议**: 从镜像中移除 SSH 服务，使用 `docker exec` 代替：
```dockerfile
# 移除 SSH
RUN apt-get remove -y openssh-server && rm -rf /etc/ssh /usr/sbin/sshd
```
使用 `docker exec -it <container> /bin/sh` 代替 SSH
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.15 "Ensure that SSH is not running within containers"
**攻击面关联**: AS-3 网络攻击（容器内 SSH 提供攻击者持久化通道和横向移动路径）

---

### Docker-50 容器内只读挂载检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"):\"; docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.RW}}){{println}}{{end}}' \"$c\" 2>/dev/null | grep 'true' | head -5; done")
```

**期望值**: 敏感目录（如 /etc、/usr、/var）不应以读写模式挂载到容器
**判定标准**: pass=无敏感宿主机目录以读写模式挂载，fail=敏感目录以读写模式挂载到容器，na=无额外挂载
**修复建议**: 挂载时使用 `:ro` 只读标志：
```bash
# 错误示范
# docker run -v /etc:/etc myapp

# 正确做法
docker run -v /etc/myconfig:/etc/myconfig:ro myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.16 "Ensure that sensitive host system directories are not mounted on containers"
**攻击面关联**: AS-1 容器逃逸（读写挂载敏感目录允许攻击者修改宿主机关键配置文件实现逃逸）

---

### Docker-51 daemon.json 无内容信任

**检查命令 [L0]**:
```bash
ssh_execute(server, "cat /etc/docker/daemon.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"content-trust\",\"not set\"))' 2>/dev/null || echo 'no daemon.json'")
```

进一步检查 DOCKER_CONTENT_TRUST 环境变量：
```bash
ssh_execute(server, "echo $DOCKER_CONTENT_TRUST; grep -r 'DOCKER_CONTENT_TRUST' /etc/environment /etc/profile.d/ ~/.bashrc 2>/dev/null || echo 'not set'")
```

**期望值**: 启用了 Docker Content Trust（`DOCKER_CONTENT_TRUST=1`）
**判定标准**: pass=已启用内容信任，fail=未启用内容信任（可拉取未签名恶意镜像），na=离线环境无需内容信任
**修复建议**: 启用 Docker Content Trust：
```bash
export DOCKER_CONTENT_TRUST=1
```
或在 `/etc/environment` 中添加：
```
DOCKER_CONTENT_TRUST=1
```
或在 daemon.json 中：
```json
{
  "content-trust": true
}
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.17 "Ensure that Docker content trust is enabled"
**攻击面关联**: AS-4 供应链攻击（无内容信任时可拉取被篡改的恶意镜像）

---

### Docker-52 /etc/docker/daemon.json 权限复查

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%a' /etc/docker/daemon.json 2>/dev/null || echo 'file not found'")
```

**期望值**: `644` 或更严格（如 `600`）
**判定标准**: pass=权限为 644 或更严格，fail=权限宽松于 644，na=daemon.json 不存在
**修复建议**: `chmod 644 /etc/docker/daemon.json`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.17 "Ensure that the daemon.json file permissions are set to 644 or more restrictive"（运行时复查）
**攻击面关联**: AS-2 认证授权（运行时 daemon.json 权限变更可能被利用篡改安全配置）

---

### Docker-53 /etc/docker/daemon.json 属主复查

**检查命令 [L0]**:
```bash
ssh_execute(server, "stat -c '%U:%G' /etc/docker/daemon.json 2>/dev/null || echo 'file not found'")
```

**期望值**: `root:root`
**判定标准**: pass=属主为 root:root，fail=属主非 root:root，na=daemon.json 不存在
**修复建议**: `chown root:root /etc/docker/daemon.json`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 3.18 "Ensure that the daemon.json file ownership is set to root:root"（运行时复查）
**攻击面关联**: AS-2 认证授权（运行时属主变更允许非 root 用户篡改 Docker 配置）

---

### Docker-54 镜像和容器标签

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"):\"; docker inspect --format '{{.Config.Labels}}' \"$c\" 2>/dev/null; done")
```

进一步检查镜像标签：
```bash
ssh_execute(server, "for img in $(docker images -q | head -5); do docker inspect --format '{{.RepoTags}}: {{.Config.Labels}}' \"$img\" 2>/dev/null; done")
```

**期望值**: 镜像和容器包含描述性标签（如 version、maintainer、description）
**判定标准**: pass=镜像和容器包含合理的元数据标签，fail=无任何标签或标签信息缺失，na=无运行中容器
**修复建议**: 在 Dockerfile 中添加标签：
```dockerfile
LABEL maintainer="security@example.com"
LABEL version="1.0.0"
LABEL description="Application service with security hardening"
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.18 "Ensure that container images are tagged"（最佳实践）
**攻击面关联**: AS-5 审计缺失（无标签的镜像和容器难以追踪安全审计和漏洞扫描）

---

### Docker-55 各容器特权检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): privileged=$(docker inspect --format '{{.HostConfig.Privileged}}' \"$c\" 2>/dev/null)\"; done | grep -i 'true'")
```

进一步详细检查所有安全相关配置：
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format 'Name={{.Name}} Privileged={{.HostConfig.Privileged}} CapAdd={{.HostConfig.CapAdd}} SecurityOpt={{.HostConfig.SecurityOpt}}' \"$c\" 2>/dev/null; done")
```

**期望值**: 无容器运行在特权模式
**判定标准**: pass=所有容器 Privileged=false，fail=存在任何 Privileged=true 的容器（⚠️ 高危），na=无运行中容器
**修复建议**: 将特权容器转为非特权容器，按需添加能力：
```bash
# 识别所有特权容器
docker ps --filter volume-driver=/dev --format '{{.Names}}'

# 替代方案：按需添加能力
docker run --cap-add=NET_ADMIN --device=/dev/net/tun myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.9 "Ensure that the container is not running in privileged mode"（逐容器检查）
**攻击面关联**: AS-1 容器逃逸（特权容器等同于宿主机 root，可 mount 宿主机磁盘实现直接逃逸）

---

### Docker-56 各容器只读根文件系统

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): readonly=$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 所有容器的 ReadonlyRootfs 为 true
**判定标准**: pass=所有容器启用了只读根文件系统，fail=存在未启用只读根文件系统的容器，na=应用必须写入根文件系统
**修复建议**: 运行时启用只读根文件系统并挂载必要 tmpfs：
```bash
docker run --read-only --tmpfs /run --tmpfs /tmp --tmpfs /var/run myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.5 "Ensure that the container's root filesystem is mounted as read only"（逐容器检查）
**攻击面关联**: AS-1 容器逃逸（可写根文件系统允许攻击者植入后门和修改配置）

---

### Docker-57 各容器 PID 限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): pids_limit=$(docker inspect --format '{{.HostConfig.PidsLimit}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 所有容器设置了 PID 限制（> 0）
**判定标准**: pass=所有容器 PidsLimit > 0，fail=存在 PidsLimit 为 0 或 -1 的容器，na=编排系统已管理 PID 限制
**修复建议**: 运行时指定 PID 限制：
```bash
docker run --pids-limit=100 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.8 "Ensure that the PID cgroup limit is used"（逐容器检查）
**攻击面关联**: AS-4 资源耗尽（无 PID 限制允许 fork bomb 攻击）

---

### Docker-58 各容器 ulimit 限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): ulimits=$(docker inspect --format '{{.HostConfig.Ulimits}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 所有容器配置了合理的 ulimit
**判定标准**: pass=所有容器设置了合理 ulimit，fail=存在未设置 ulimit 的容器，na=使用 daemon 默认 ulimit
**修复建议**: 运行时指定 ulimit：
```bash
docker run --ulimit nofile=65536:65536 --ulimit nproc=4096:4096 myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.14 "Ensure that container ulimits are set appropriately"（逐容器检查）
**攻击面关联**: AS-4 资源耗尽（容器级无 ulimit 限制可耗尽宿主机资源）

---

### Docker-59 各容器 seccomp 检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"):\"; docker inspect --format '{{.HostConfig.SecurityOpt}}' \"$c\" 2>/dev/null | grep -o 'seccomp=[^ ]*' || echo 'default'; done")
```

**期望值**: 所有容器的 seccomp 配置非 `unconfined`
**判定标准**: pass=所有容器 seccomp 为默认或自定义配置，fail=存在 seccomp=unconfined 的容器，na=系统不支持 seccomp
**修复建议**: 确保运行时不使用 `--security-opt seccomp=unconfined`：
```bash
# 使用默认 seccomp
docker run myapp

# 或自定义 seccomp
docker run --security-opt seccomp=my-profile.json myapp

# 绝对不要
# docker run --security-opt seccomp=unconfined myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.11 "Ensure that seccomp is enabled for containers"（逐容器检查）
**攻击面关联**: AS-1 容器逃逸（无 seccomp 允许容器执行 mount、keyctl 等逃逸相关系统调用）
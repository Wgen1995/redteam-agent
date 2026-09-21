# G_5 Containerd 容器运行时（10 条）

CIS Containerd Benchmark — 容器运行时安全检查。
覆盖 Containerd-5.1 至 Containerd-5.10，共 10 条规则。

---

### Containerd-5.1 容器资源限制（CPU/内存/IO）

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E '\"cpu\"|\"memory\"|\"pids\"|\"memory_limit\"|\"cpu_limit\"|\"io\"'; done")
```

**期望值**: 每个容器均配置了 CPU 和内存限制
**判定标准**: pass=所有运行中容器均配置了 CPU 和内存限制，fail=任一容器未配置资源限制，na=无运行中容器
**修复建议**: 在容器配置或编排系统中设置资源限制：
```bash
# crictl 创建容器时通过 pod 配置指定 limits
# Kubernetes 示例：
# resources:
#   limits:
#     cpu: "500m"
#     memory: "256Mi"
```
**CIS映射**: CIS Containerd Benchmark - 5.1 "Ensure container resource limits are set"
**攻击面关联**: AS-2 认证授权（未限制资源的容器可耗尽主机资源，导致拒绝服务）

---

### Containerd-5.2 只读根文件系统

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'readonly|read_only|ReadOnlyroot'; done")
```

**期望值**: 容器根文件系统为只读（`readonly: true`）
**判定标准**: pass=容器根文件系统设置为只读，fail=容器根文件系统可写，na=应用需要写入根文件系统（通过 tmpfs 卷挂载解决）
**修复建议**: 设置根文件系统为只读，需要写入的目录通过 tmpfs 挂载：
```bash
# crictl pod 配置中设置：
# "linux": { "readonly_rootfs": true }
# 或 Kubernetes：
# securityContext:
#   readOnlyRootFilesystem: true
```
**CIS映射**: CIS Containerd Benchmark - 5.2 "Ensure root filesystem is mounted as read-only"
**攻击面关联**: AS-1 容器逃逸（可写根文件系统允许攻击者植入恶意二进制和修改系统文件）

---

### Containerd-5.3 特权模式检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E '\"privileged\"|\"Privileged\"'; done")
```

**期望值**: `privileged: false`（所有容器不运行在特权模式）
**判定标准**: pass=所有容器均未启用特权模式，fail=任一容器运行在特权模式，na=无运行中容器
**修复建议**: 禁用特权模式，使用细粒度 capabilities 代替：
```bash
# Kubernetes 配置：
# securityContext:
#   privileged: false
# 仅添加必要的 capabilities：
#   capabilities:
#     add: ["NET_BIND_SERVICE"]
```
**CIS映射**: CIS Containerd Benchmark - 5.3 "Ensure privileged containers are not used"
**攻击面关联**: AS-1 容器逃逸（特权容器直接访问主机设备、加载内核模块，为逃逸主路径）

---

### Containerd-5.4 Capabilities 限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -A20 '\"capabilities\"' | head -30; done")
```

**期望值**: 仅保留必要的 Linux capabilities（如 NET_BIND_SERVICE），默认 capabilities 全部移除
**判定标准**: pass=capabilities 列表最小化（仅必要 capabilities），fail=保留大量默认 capabilities（如 SYS_ADMIN、NET_ADMIN、SYS_PTRACE），na=无运行中容器
**修复建议**: 移除所有非必要 capabilities，仅显式添加所需：
```bash
# Kubernetes 配置：
# securityContext:
#   capabilities:
#     drop: ["ALL"]
#     add: ["NET_BIND_SERVICE"]
```
**CIS映射**: CIS Containerd Benchmark - 5.4 "Ensure Linux capabilities are restricted"
**攻击面关联**: AS-1 容器逃逸（SYS_ADMIN、SYS_PTRACE、NET_ADMIN 等 capabilities 是容器逃逸和横向移动的核心利用点）

---

### Containerd-5.5 Seccomp 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'seccomp|Seccomp|seccompProfilePath'; done")
```

**期望值**: 已配置 seccomp 配置文件（非 `unconfined`）
**判定标准**: pass=容器使用 seccomp 配置文件（RuntimeDefault 或自定义），fail=seccomp 设置为 unconfined 或未配置，na=无运行中容器
**修复建议**: 配置 seccomp 配置文件：
```bash
# Kubernetes 配置：
# securityContext:
#   seccompProfile:
#     type: RuntimeDefault
# 或指定自定义配置文件：
#     type: Localhost
#     localhostProfile: profiles/my-profile.json
```
**CIS映射**: CIS Containerd Benchmark - 5.5 "Ensure seccomp profile is configured"
**攻击面关联**: AS-1 容器逃逸（无 seccomp 限制允许容器调用所有系统调用，扩大内核漏洞利用面）

---

### Containerd-5.6 SELinux/AppArmor 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'selinux|apparmor|AppArmor|SeLinux|label'; done; echo '---'; getenforce 2>/dev/null; echo '---'; aa-status 2>/dev/null | head -5")
```

**期望值**: 容器启用了 SELinux 或 AppArmor MAC 策略
**判定标准**: pass=容器使用 SELinux 或 AppArmor 策略（非 unconfined），fail=容器运行在 unconfined 或无 MAC 策略，na=系统不支持 SELinux/AppArmor
**修复建议**: 启用 MAC 策略：
```bash
# SELinux 方式：
# 在容器配置中指定 SELinux 标签：
# "linux": { "security_opt": ["label=user:container_t"] }

# AppArmor 方式：
# 创建 AppArmor 配置文件后引用：
# securityContext:
#   appArmorProfile:
#     type: RuntimeDefault
```
**CIS映射**: CIS Containerd Benchmark - 5.6 "Ensure SELinux/AppArmor is configured"
**攻击面关联**: AS-1 容器逃逸（无 MAC 限制的容器更容易突破命名空间隔离实现逃逸）

---

### Containerd-5.7 PID cgroup 限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'pids_limit|PidsLimit|pid'; done")
```

**期望值**: 容器配置了 PID 限制（如 `pids_limit: 100`）
**判定标准**: pass=容器设置了 PID 限制，fail=容器 PID 限制为 0（无限制），na=无运行中容器
**修复建议**: 配置 PID 限制：
```bash
# Kubernetes 配置：
# spec:
#   containers:
#   - name: app
#   securityContext:
#     pidLimit: 100
```
**CIS映射**: CIS Containerd Benchmark - 5.7 "Ensure PID cgroup limit is configured"
**攻击面关联**: AS-2 认证授权（无 PID 限制可导致 fork bomb 拒绝服务攻击，耗尽主机 PID 资源）

---

### Containerd-5.8 网络命名空间

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'network_namespace|hostNetwork|host_network|NetworkMode'; done")
```

**期望值**: 容器使用独立网络命名空间（`hostNetwork: false`）
**判定标准**: pass=容器使用独立网络命名空间，fail=容器使用主机网络（hostNetwork=true），na=网络插件容器确需主机网络
**修复建议**: 禁用主机网络，使用独立网络命名空间：
```bash
# Kubernetes 配置：
# spec:
#   hostNetwork: false
```
**CIS映射**: CIS Containerd Benchmark - 5.8 "Ensure network namespace is isolated"
**攻击面关联**: AS-5 网络攻击（hostNetwork 模式允许容器直接访问主机网络栈，可嗅探和劫持主机流量）

---

### Containerd-5.9 runAs 非 root

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'runAsUser|runAsGroup|RunAsUser|RunAsGroup|uid'; done")
```

**期望值**: 容器以非 root 用户运行（`runAsUser: > 0`，如 1000）
**判定标准**: pass=容器以非 root 用户运行，fail=容器以 root（UID 0）运行，na=容器需要 root 权限（应通过 capabilities 精细控制）
**修复建议**: 配置容器以非 root 用户运行：
```bash
# Kubernetes 配置：
# securityContext:
#   runAsNonRoot: true
#   runAsUser: 1000
#   runAsGroup: 1000
```
**CIS映射**: CIS Containerd Benchmark - 5.9 "Ensure containers run as non-root user"
**攻击面关联**: AS-1 容器逃逸（root 容器被入侵后获得 UID 0 权限，大幅增加逃逸成功率）

---

### Containerd-5.10 容器 Limits 配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(crictl ps -q 2>/dev/null); do echo \"=== $c ===\"; crictl inspect $c 2>/dev/null | grep -E 'ulimit|nofile|nproc|rtprio|fsize'; done")
```

**期望值**: 容器配置了合理的 ulimit 限制（如 `nofile`、`nproc`）
**判定标准**: pass=容器设置了 ulimit 限制，fail=容器使用默认无限制 ulimit，na=无运行中容器
**修复建议**: 在容器配置中设置 ulimit 限制：
```bash
# crictl 容器配置中添加 ulimits：
# "linux": {
#   "resources": {
#     "ulimits": [
#       { "type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024 },
#       { "type": "RLIMIT_NPROC", "hard": 512, "soft": 512 }
#     ]
#   }
# }
```
**CIS映射**: CIS Containerd Benchmark - 5.10 "Ensure container ulimits are configured"
**攻击面关联**: AS-2 认证授权（无 ulimit 限制可导致文件描述符耗尽、进程数爆炸等资源滥用攻击）
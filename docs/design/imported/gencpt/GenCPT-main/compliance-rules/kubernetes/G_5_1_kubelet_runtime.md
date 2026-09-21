# G_5_1 Kubelet 运行时配置（8 条）

CIS Kubernetes Benchmark v1.8.0 — 5.1 Worker Node Configuration: Kubelet 运行时安全参数检查。
覆盖 K8s-5.1.1 至 K8s-5.1.8，共 8 条规则。
覆盖内核保护、cgroup 驱动、iptables 链管理、Pod 沙箱限制等运行时安全相关参数。

---

### K8s-5.1.1 Kubelet --protect-kernel-defaults=true

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--protect-kernel-defaults=[^ ]*' || grep 'protectKernelDefaults' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'")
```

**期望值**: `--protect-kernel-defaults=true` 或 `protectKernelDefaults: true`
**判定标准**: pass=参数为 true，fail=未设置（默认 false）或为 false，na=不适用
**修复建议**: 在 kubelet 启动参数或 config.yaml 中设置 `protectKernelDefaults: true`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.1 "Ensure that the --protect-kernel-defaults argument is set to true"
**攻击面关联**: AS-1 逃逸（关闭后 kubelet 可改写内核 vm.overcommit_memory 等参数，便于容器逃逸）

---

### K8s-5.1.2 Kubelet --make-iptables-util-chains=true

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--make-iptables-util-chains=[^ ]*' || grep 'makeIPTablesUtilChains' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'")
```

**期望值**: `--make-iptables-util-chains=true` 或 `makeIPTablesUtilChains: true`
**判定标准**: pass=参数为 true 或未设置（默认 true），fail=参数为 false，na=不适用
**修复建议**: 在 kubelet 启动参数或 config.yaml 中设置 `makeIPTablesUtilChains: true`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.2 "Ensure that the --make-iptables-util-chains argument is set to true"
**攻击面关联**: AS-3 网络（关闭后 kube-proxy 与 kubelet 协同的 iptables 规则失效，Pod 间流量绕过 NetworkPolicy）

---

### K8s-5.1.3 Kubelet --event-qps 设置合理值

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--event-qps=[^ ]*' || grep 'eventQPS' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'")
```

**期望值**: `--event-qps=5` 或具体有限值（建议 0 表示禁限流审计模式或 ≤ 50）
**判定标准**: pass=event-qps 设置为有限值（如 5/10/50），fail=未设置（默认 50 可能合理，但建议显式声明），na=不适用
**修复建议**: 在 config.yaml 中显式设置 `eventQPS: 5`，结合集群规模与 SIEM 容量调优
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.3 "Ensure that the --event-qps argument is set as appropriate"
**攻击面关联**: AS-5 拒绝服务（默认值过大会导致恶意 Pod 灌爆 etcd Event 存储）

---

### K8s-5.1.4 Kubelet --cgroup-driver 与容器运行时一致

**检查命令 [L0]**:
```bash
ssh_execute(server, "KUBELET_DRIVER=$(ps -ef | grep kubelet | grep -v grep | grep -o -- '--cgroup-driver=[^ ]*' | cut -d= -f2 || grep 'cgroupDriver' /var/lib/kubelet/config.yaml 2>/dev/null | awk -F: '{print $2}' | xargs); CRIO_DRIVER=$(stat -f -c %T /sys/fs/cgroup 2>/dev/null); echo KUBELET=$KUBELET_DRIVER CGROUP_FS=$CRIO_DRIVER")
```

**期望值**: kubelet cgroup-driver 与容器运行时 cgroup fs 一致（推荐 systemd / systemd）
**判定标准**: pass=两者一致（如 kubelet=systemd 且 cgroup v2 systemd），fail=不一致导致 Pod 创建不稳，na=不适用
**修复建议**: 在 kubeadm init 配置或 kubelet config.yaml 中设置 `cgroupDriver: systemd`，并确保容器运行时使用 systemd cgroup 驱动
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.4 "Ensure that the cgroup-driver is consistent with the container runtime"
**攻击面关联**: AS-1 逃逸（cgroup 驱动不一致导致资源限制失效，恶意 Pod 可突破内存/CPU 限制）

---

### K8s-5.1.5 Kubelet --cgroups-per-pod 已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--cgroups-per-pod=[^ ]*' || grep 'cgroupsPerQoS\|cgroupsPerPod' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'")
```

**期望值**: `--cgroups-per-pod=true` 或 `cgroupsPerQoS: true`
**判定标准**: pass=已设置且为 true，fail=未设置或为 false，na=不适用
**修复建议**: 在 config.yaml 中设置 `cgroupsPerQoS: true`，确保每个 Pod 有独立 cgroup 便于资源追踪
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.5 "Ensure that the --cgroups-per-pod argument is set to true"
**攻击面关联**: AS-1 逃逸（关闭后无法隔离资源，攻击 Pod 可通过 cgroup 攻击挤占同节点 Pod）

---

### K8s-5.1.6 Kubelet --read-only-port 已关闭

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--read-only-port=[^ ]*' || grep 'readOnlyPort' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'")
```

**期望值**: `--read-only-port=0` 或 `readOnlyPort: 0`
**判定标准**: pass=read-only-port=0 或未暴露端口，fail=未设置（默认 10255）或为非零值，na=不适用
**修复建议**: 在 config.yaml 中设置 `readOnlyPort: 0` 防止匿名读取节点指标和 Pod 列表
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.6 "Ensure that the --read-only-port argument is set to 0"
**攻击面关联**: AS-4 数据泄露（10255 端口匿名返回 /pods、/metrics 项目，泄露集群拓扑与资源使用）

---

### K8s-5.1.7 Kubelet 不允许 --hostname-override 跨节点冲突

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--hostname-override=[^ ]*' || grep 'hostnameOverride' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET'; kubectl get nodes -o wide 2>/dev/null | awk '{print $1, $3}'")
```

**期望值**: 若设置 --hostname-override，则该名称与节点对象一致且集群内唯一
**判定标准**: pass=未设置或设置后与 Node 对象名称唯一且一致，fail=多处使用相同 override 导致调度/服务寻址错乱，na=不适用
**修复建议**: 避免使用 --hostname-override，让 kubelet 使用节点真实 hostname 自动注册
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.7 "Ensure that the --hostname-override argument is not used in production"
**攻击面关联**: AS-2 认证授权（恶意 override 可让节点冒名顶替其他节点接收其工作负载）

---

### K8s-5.1.8 Kubelet 静态 Pod 清单目录权限

**检查命令 [L0]**:
```bash
ssh_execute(server, "MANIFEST_PATH=$(ps -ef | grep kubelet | grep -v grep | grep -o -- '--pod-manifest-path=[^ ]*' | cut -d= -f2 || echo '/etc/kubernetes/manifests'); stat -c '%a %U:%G' $MANIFEST_PATH 2>/dev/null")
```

**期望值**: 权限 `700` 或更严格，属主 `root:root`
**判定标准**: pass=权限 ≤ 700 且属主 root:root，fail=权限宽松或属主非 root，na=不适用
**修复建议**: `chmod 700 /etc/kubernetes/manifests && chown root:root /etc/kubernetes/manifests`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.1.8 "Ensure that the pod manifest directory permissions are set to 700 or more restrictive"
**攻击面关联**: AS-2 认证授权（静态 Pod 目录可写则攻击者可投放恶意 manifest 启动后门 Pod）
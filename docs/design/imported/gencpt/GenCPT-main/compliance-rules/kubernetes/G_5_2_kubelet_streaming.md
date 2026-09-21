# G_5_2 Kubelet 流式连接配置（6 条）

CIS Kubernetes Benchmark v1.8.0 — 5.2 Worker Node Configuration: Kubelet 流式连接与 exec/exec 日志检查。
覆盖 K8s-5.2.1 至 K8s-5.2.6，共 6 条规则。
覆盖 exec/attach/port-forward 流式连接超时、keepalive、审计记录等。

---

### K8s-5.2.1 Kubelet --streaming-connection-idle-timeout 已设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--streaming-connection-idle-timeout=[^ ]*' || grep 'streamingConnectionIdleTimeout' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: `--streaming-connection-idle-timeout` 设置为有限值（如 `5m` 或更短，不能为 `0`）
**判定标准**: pass=已设置为有限非零值（如 5m），fail=未设置（默认 0=永不超时）或值为 0，na=不适用
**修复建议**: 在 kubelet 启动参数或 config.yaml 中设置 `streamingConnectionIdleTimeout: 5m`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.1 "Ensure that the --streaming-connection-idle-timeout argument is not set to 0"
**攻击面关联**: AS-5 拒绝服务（无超时则攻击者可长期挂载 exec 流占用 kubelet 连接句柄）

---

### K8s-5.2.2 Kubelet --node-status-update-frequency 合理设置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--node-status-update-frequency=[^ ]*' || grep 'nodeStatusUpdateFrequency' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: 设置为合理频率（默认 10s，过短增加 etcd 写入负担）
**判定标准**: pass=已设置且 10s ≤ value ≤ 60s，fail=未设置或值 < 10s（浪费 etcd 资源），na=不适用
**修复建议**: 在 config.yaml 中设置 `nodeStatusUpdateFrequency: 10s`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.2 "Ensure that the --node-status-update-frequency is set appropriately"
**攻击面关联**: AS-5 拒绝服务（过频的节点状态更新令 etcd I/O 暴涨）

---

### K8s-5.2.3 Kubelet --volume-plugin-dir 隔离

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--volume-plugin-dir=[^ ]*' || grep 'volumePluginDir' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: --volume-plugin-dir 设置为受控目录（如 `/usr/libexec/kubernetes/kubelet-plugins/volume/exec/`）
**判定标准**: pass=volume-plugin-dir 设置为可写入受控路径，fail=未设置或被注入世界可写目录，na=不适用
**修复建议**: 在 config.yaml 中设置 `volumePluginDir: /usr/libexec/kubernetes/kubelet-plugins/volume/exec/` 并将该目录限制为 root:root
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.3 "Ensure that the --volume-plugin-dir argument is set to a controlled directory"
**攻击面关联**: AS-6 供应链（恶意 FlexVolume 插件目录令攻击者植入后门卷驱动）

---

### K8s-5.2.4 Kubelet --register-node=true 显式声明

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--register-node=[^ ]*' || grep 'registerNode' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: `--register-node=true` 或未设置（默认 true）
**判定标准**: pass=registerNode=true 或未设置，fail=registerNode=false 但 Node 未被外部控制器管理，na=不适用（外部控制器场景）
**修复建议**: 确保节点显式注册到集群，若使用 Node=self-register 模式维持 `registerNode: true`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.4 "Ensure that the --register-node argument is set as appropriate"
**攻击面关联**: AS-2 认证授权（关闭注册则节点可在 API Server 视野外自由运行）

---

### K8s-5.2.5 Kubelet --containerd 或 --docker-root 隔离

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -oE -- '--container-runtime=[^ ]*|--container-runtime-endpoint=[^ ]*' || grep -E 'containerRuntimeVersion|containerRuntimeEndpoint' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: runtime 为受控版本（如 containerd 1.6+，CRI-O），且 runtime-endpoint 不暴露网络
**判定标准**: pass=使用受控 containerd/cri-o 并 endpoint 为 unix socket，fail=仍使用已弃用的 dockershim 或 runtime 暴露 TCP，na=不适用
**修复建议**: 切换到 containerd 并使用 `--container-runtime-endpoint=unix:///run/containerd/containerd.sock`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.5 "Ensure that the container runtime endpoint is set to a managed socket"
**攻击面关联**: AS-6 供应链（dockershim 已弃用且存在历史漏洞，TCP 暴露则可被远程控制容器）

---

### K8s-5.2.6 Kubelet volume-plugin 支持白名单已限制

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--enable-controller-attach-detach=[^ ]*' || grep 'enableControllerAttachDetach' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: --enable-controller-attach-detach 显式设置为 true（除非节点角色明确为存储控制器节点）
**判定标准**: pass=enableControllerAttachDetach=true 或未设置，fail=false 但节点不应承担存储分离职责，na=不适用
**修复建议**: 默认使用 true 让 controller-manager 统一协调 attach/detach，避免 kubelet 本地 CSIDriver 越权
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.2.6 "Ensure that the --enable-controller-attach-detach argument is set"
**攻击面关联**: AS-1 逃逸（关闭后 kubelet 直接调用 node 上 CSIDriver，绕过 controller 准入）
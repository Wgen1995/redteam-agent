# G_2 Containerd 守护进程参数（3 条）

CIS Containerd Benchmark — 守护进程参数检查。
覆盖 Containerd-2.1 至 Containerd-2.3，共 3 条规则。

---

### Containerd-2.1 disabled_plugins 检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E 'disabled_plugins' /etc/containerd/config.toml 2>/dev/null || echo 'NOT_FOUND'")
```

**期望值**: `disabled_plugins = ["cri"]` 或按需禁用不需要的插件（如不需要 CRI 接口则禁用）
**判定标准**: pass=disabled_plugins 已显式配置且禁用了不需要的插件，fail=未配置 disabled_plugins 或列表为空，na=使用默认配置且无安全需求
**修复建议**: 编辑 `/etc/containerd/config.toml`，添加：
```toml
disabled_plugins = ["cri"]
```
然后重启 containerd：`systemctl restart containerd`
**CIS映射**: CIS Containerd Benchmark - 2.1 "Ensure disabled_plugins is configured"
**攻击面关联**: AS-2 认证授权（暴露不必要的插件接口扩大攻击面）

---

### Containerd-2.2 stream_server_address 检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E 'stream_server_address' /etc/containerd/config.toml 2>/dev/null || echo 'NOT_FOUND'")
```

**期望值**: `stream_server_address = "127.0.0.1"`（仅监听本地回环地址）
**判定标准**: pass=stream_server_address 绑定 127.0.0.1，fail=绑定 0.0.0.0 或其他非回环地址，na=未配置 stream_server（使用默认值 127.0.0.1 也可视为通过）
**修复建议**: 编辑 `/etc/containerd/config.toml`，设置：
```toml
stream_server_address = "127.0.0.1"
```
然后重启 containerd：`systemctl restart containerd`
**CIS映射**: CIS Containerd Benchmark - 2.2 "Ensure stream_server_address is configured to localhost"
**攻击面关联**: AS-5 网络攻击（stream server 绑定公网地址可被远程利用进行 API 调用）

---

### Containerd-2.3 oom_score 调整检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E 'oom_score' /etc/containerd/config.toml 2>/dev/null || echo 'NOT_FOUND'")
```

**期望值**: `oom_score = -999` 或足够低的负值（防止 OOM killer 优先终止 containerd）
**判定标准**: pass=oom_score 设置为负值（-999 至 -1），fail=未设置或为正值，na=系统无 OOM 压力场景
**修复建议**: 编辑 `/etc/containerd/config.toml`，设置：
```toml
oom_score = -999
```
然后重启 containerd：`systemctl restart containerd`
**CIS映射**: CIS Containerd Benchmark - 2.3 "Ensure oom_score is adjusted appropriately"
**攻击面关联**: AS-2 认证授权（OOM killer 终止 containerd 可导致所有容器中断，属于拒绝服务攻击面）
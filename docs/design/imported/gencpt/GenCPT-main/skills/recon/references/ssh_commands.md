# recon SSH 命令清单

> 本文件为 `skills/recon/SKILL.md` 步骤 1-2 的详细 SSH 命令参考。核心工作流见 SKILL.md。

---

## 步骤 1：环境指纹识别

分批执行 SSH 命令（每批 5-7 条，间隔 2 秒），收集 OS/架构/内核/运行时版本。

### 1.1 OS 与架构收集 [L0]

```bash
[L0] uname -m                        # 架构（x86_64 / aarch64）
[L0] cat /etc/os-release              # 发行版信息
[L0] uname -r                         # 内核版本
[L0] hostname                          # 主机名
```

### 1.2 按 scope 收集运行时版本 [L0]

**scope 含 k8s**：

```bash
[L0] kubectl version -o yaml           # K8s Client + Server 版本
[L0] kubectl cluster-info              # 集群端点信息
[L0] which kubectl                     # kubectl 可用性
```

**scope 含 docker**：

```bash
[L0] docker version                    # Docker 版本（Client + Server）
[L0] docker info                       # Docker 详细配置
[L0] which docker                      # Docker 可用性
```

**scope 含 containerd**：

```bash
[L0] crictl --version                 # crictl 版本
[L0] containerd --version              # containerd 版本
[L0] runc --version                    # runc 版本
```

### 1.3 写盘规则

- 每个 SSH 命令输出**立即写盘**到 `evidence/recon/raw/`，不在上下文中保留原始输出
- 文件命名：`env_fingerprint_{timestamp}.md`
- 每段输出按 SSH_COMMANDS.md §7.1 标注五元组（命令、来源、输出、时间戳、备注）

---

## 步骤 2：集群结构收集

根据 scope 参数选择性收集集群结构信息。

### 2.1 K8s 集群结构 [L0]

```bash
# 批次1：节点与服务
[L0] kubectl get nodes -o wide                               # 节点列表
[L0] kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo}' # 节点系统信息
[L0] kubectl get services --all-namespaces -o wide           # 服务列表

5. **Worker 节点 SSH 可达性验证**：
   - 从 `kubectl get nodes -o wide` 输出提取所有节点 IP
   - 对每个非 master 节点（不含 control-plane/master 角色的节点），通过 `ssh_execute(server, "ssh <worker_ip> echo OK")` 验证从 master 到 worker 的 SSH 可达性
   - 可达的 worker 节点写入 `session_config.json` 的 `env_fingerprint.worker_nodes` 字段
   - 不可达的 worker 节点标记为 `ssh_unreachable`，在 recon_summary.md 中记录
   - **约束**：不要求所有 worker 节点都可达，只检测可达的节点

# 批次2：Pod 与安全上下文（大集群必须按 namespace 分批拉取，避免单次全量触发会话压缩）
# 步骤a：先获取命名空间列表
[L0] kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'
# 步骤b：按命名空间分批拉取（每批一个 namespace，间隔 2 秒）
[L0] kubectl get pods -n <ns> -o json                          # 每个命名空间单独拉取

# 批次3：RBAC 与准入控制
[L0] kubectl get serviceaccounts --all-namespaces             # SA 列表
[L0] kubectl get secrets --all-namespaces                     # Secret 列表（仅名称+类型）
[L0] kubectl get networkpolicies --all-namespaces            # 网络策略
[L0] kubectl get roles,clusterroles --all-namespaces         # RBAC
[L0] kubectl get validatingwebhookconfigurations             # 准入 Webhook

# 批次4：Pod 安全标准
[L0] kubectl get namespaces --labels pod-security.kubernetes.io/enforce  # PSA 标签
```

**大集群分批策略**（300+ Pod）：
1. 先获取命名空间列表：`kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'`
2. 按命名空间分批，每个命名空间一个 WU
3. 每批 100 个 Pod，间隔 2 秒

### 2.2 Docker 容器结构 [L0]

```bash
# 批次1：概览
[L0] docker ps -a                                            # 全量容器列表
[L0] docker images                                           # 镜像列表
[L0] docker network ls                                       # 网络列表
[L0] docker volume ls                                        # 卷列表

# 批次2：逐个 inspect（每批 100 个，间隔 2 秒）
[L0] docker inspect <container_id>                           # 容器详细配置
```

**inspect 分批规则**：
- `docker ps -a` 获取容器 ID 列表后，每批 100 个 `docker inspect`
- 批次间间隔 2 秒
- 输出立即写盘到 `evidence/recon/raw/docker_inspect_{batch}.md`

### 2.3 containerd 结构 [L0]

```bash
# 批次1
[L0] crictl pods                                              # Pod 列表
[L0] crictl ps -a                                             # 容器列表
[L0] crictl images                                            # 镜像列表

# 批次2：逐个 inspect
[L0] crictl inspect <container_id>                            # 容器详细配置
[L0] crictl inspectp <pod_id>                                 # Pod 详细配置
```

### 2.4 安全模块检测 [L0]

```bash
[L0] getenforce                                              # SELinux 状态
[L0] cat /proc/sys/kernel/yama/ptrace_scope                   # ptrace 限制
[L0] cat /proc/sys/kernel/unprivileged_bpf_disabled           # eBPF 限制
[L0] aa-status 2>/dev/null || echo "AppArmor not available"   # AppArmor 状态
```

---

## 步骤 4：数据写入格式

### 4.1 知识图谱节点写入

按类型分片写入以下 7 个 JSON 文件（顶层 JSON 数组格式）：

| 文件 | 内容 | 去重 key |
|------|------|---------|
| `knowledge_graph/nodes/hosts.json` | 主机节点（hostname, os, kernel, runtime, node_count） | `id` |
| `knowledge_graph/nodes/pods.json` | Pod 节点（name, namespace, security_context, ip, SA） | `id` |
| `knowledge_graph/nodes/containers.json` | 容器节点（name, image, security_context, status） | `id` |
| `knowledge_graph/nodes/services.json` | Service 节点（name, namespace, type, ports, selector） | `id` |
| `knowledge_graph/nodes/service_accounts.json` | SA 节点（name, namespace, automount_token, secrets） | `id` |
| `knowledge_graph/nodes/secrets.json` | Secret 节点（**仅名称+类型，绝不存储 Secret 内容**） | `id` |
| `knowledge_graph/nodes/findings.json` | 发现节点（占位结构，Phase 2 填充） | `id` |

节点格式遵循 OUTPUT_STANDARD.md §4.1：

```json
{
  "id": "pod-kube-system-apiserver-79f6c5d6c4-abc12",
  "node_type": "pod",
  "data": { ... },
  "session_id": "sess-20260619-001"
}
```

### 4.2 知识图谱边写入

写入 `knowledge_graph/edges/infra.json`（顶层 JSON 数组）：

```json
{
  "edge_type": "infra",
  "from_node": "pod-xxx",
  "to_node": "host-xxx",
  "attrs": {
    "relation": "runs_on",
    "namespace": "kube-system"
  },
  "timestamp": "2026-06-19T08:42:00Z"
}
```

同时生成：
- `knowledge_graph/nodes/_index.md`：节点总索引（ID + 类型 + 一句话摘要）
- `knowledge_graph/edges/_index.md`：边总索引

### 4.3 侦察摘要

生成 `evidence/recon/recon_summary.md`，结构：

```markdown
# 侦察摘要 — {session_id}

## 环境概览

| 项目 | 值 |
|------|-----|
| 目标服务器 | {server} |
| 检测范围 | {scope} |
| 架构 | {arch} |
| 操作系统 | {os_type} |
| 内核版本 | {kernel_version} |
| K8s 版本 | {k8s_version 或 N/A} |
| Docker 版本 | {docker_version 或 N/A} |
| containerd 版本 | {containerd_version 或 N/A} |

## 资源统计

| 类型 | 数量 |
|------|------|
| 节点 | {node_count} |
| Pod | {pod_count} |
| 容器 | {container_count} |
| Service | {service_count} |
| ServiceAccount | {sa_count} |
| Secret | {secret_count} |

## 安全上下文关键发现

| 发现 | 标记 | 关联资源 |
|------|------|---------|
| {发现描述} | [x]/[?]/[-]/[!] | {关联节点ID} |

## 五态统计

| 标记 | 数量 |
|------|------|
| [x] 已确认 | {n} |
| [?] 疑似 | {n} |
| [-] 不适用 | {n} |
| [!] 环境干扰 | {n} |
| [ ] 未检查 | {n}（完成后必须为 0） |
```

### 4.4 环境指纹生成

更新 `session_config.json` 的 `env_fingerprint` 字段：

```json
{
  "env_fingerprint": {
    "os_type": "linux",
    "arch": "amd64",
    "kernel_version": "5.15.0-91-generic",
    "k8s_version": "1.29.0",
    "docker_version": "24.0.7",
    "containerd_version": "1.7.13",
    "node_count": 3,
    "pod_count": 47,
    "sa_count": 9,
    "worker_nodes": [
      {"hostname": "worker-1", "ip": "10.0.0.2", "ssh_reachable": true},
      {"hostname": "worker-2", "ip": "10.0.0.3", "ssh_reachable": false}
    ],
    "env_hash": "sha256:{k8s_version}_{docker_version}_{node_count}_{pod_count}_{sa_count}"
  }
}
```

`env_hash` 计算方式：`k8s_version + docker_version + node_count + pod_count + sa_count` 拼接后 SHA-256 哈希。

升级 `progress.json` 中 recon Phase 状态为 `complete`。

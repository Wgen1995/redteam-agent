---
name: recon
description: >
  容器环境全光谱侦察。通过SSH远程收集集群结构、Pod规范、安全上下文、服务暴露等信息。
  使用场景：渗透测试第一步，绘制攻击面地图。
  不使用场景：已有完整侦察数据、只做单点合规检查。
---

## §0 套件根定位（启动第一步，强制）

本 SKILL 中所有相对路径（`skills/shared/`、`attack-patterns/`、`compliance-rules/`、`hypothesis-libraries/`、`references/`）均**相对套件根**，不相对 cwd。

**错误示例**（实际发生过）：SKILL 写 `skills/shared/SSH_COMMANDS.md`，LLM 拿 cwd `~/.config/opencode/skills/` 拼接 → 解析为 `~/.config/opencode/skills/shared/SSH_COMMANDS.md`（丢失套件根段 `gencpt/`）→ Read 失败。正确应为 `~/.config/opencode/skills/gencpt/skills/shared/SSH_COMMANDS.md`。

**若入口已传入套件根绝对路径**：直接用作前缀拼接所有相对路径，**不重复 Glob**。

**若未传入套件根**：用 Glob 工具定位，按以下顺序尝试首个命中：
- Pattern 1: `**/skills/shared/SSH_COMMANDS.md` → 套件根 = 命中路径向上两级
- Pattern 2: `**/gencpt/SKILL.md` → 套件根 = 命中路径父目录
- Pattern 3: `**/GenCPT*/SKILL.md` → 套件根 = 命中路径父目录

所有 Read 调用拼接套件根前缀：`skills/shared/X.md` → Read `{套件根}/skills/shared/X.md`。**禁用 `$ROOT/...` 变量形式**，Read 工具不展开 shell 变量。**不许凭记忆猜套件根路径**。

---

# recon — Phase 1a 环境侦察

本 SKILL 负责容器环境的全光谱侦察，通过 SSH 远程收集集群结构、Pod 规范、安全上下文、服务暴露等信息，写入知识图谱节点与边，为后续合规检测和攻击验证提供数据基础。

---

## MUST 输入

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `server` | string | **是** | 目标服务器名称（来自 ssh-manager 配置） |
| `scope` | string | **是** | `k8s` / `docker` / `containerd` / `all`，逗号分隔多选 |

独立运行示例：`--server prod-k8s-01 --scope k8s,docker`

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/SSH_COMMANDS.md` | SSH 命令使用规范、执行上下文标注、限速与重试 |
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流

### 步骤 1：环境指纹识别

分批执行 SSH 命令（每批 5-7 条，间隔 2 秒），收集 OS/架构/内核/运行时版本。

#### 1.1 OS 与架构收集 [L0]

```bash
[L0] uname -m                        # 架构（x86_64 / aarch64）
[L0] cat /etc/os-release              # 发行版信息
[L0] uname -r                         # 内核版本
[L0] hostname                          # 主机名
```

#### 1.2 按 scope 收集运行时版本 [L0]

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

#### 1.3 写盘规则

- 每个 SSH 命令输出**立即写盘**到 `evidence/recon/raw/`，不在上下文中保留原始输出
- 文件命名：`env_fingerprint_{timestamp}.md`
- 每段输出按 SSH_COMMANDS.md §7.1 标注五元组（命令、来源、输出、时间戳、备注）

---

### 步骤 2：集群结构收集

根据 scope 参数选择性收集集群结构信息。

#### 2.1 K8s 集群结构 [L0]

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

#### 2.2 Docker 容器结构 [L0]

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

#### 2.3 containerd 结构 [L0]

```bash
# 批次1
[L0] crictl pods                                              # Pod 列表
[L0] crictl ps -a                                             # 容器列表
[L0] crictl images                                            # 镜像列表

# 批次2：逐个 inspect
[L0] crictl inspect <container_id>                            # 容器详细配置
[L0] crictl inspectp <pod_id>                                 # Pod 详细配置
```

#### 2.4 安全模块检测 [L0]

```bash
[L0] getenforce                                              # SELinux 状态
[L0] cat /proc/sys/kernel/yama/ptrace_scope                   # ptrace 限制
[L0] cat /proc/sys/kernel/unprivileged_bpf_disabled           # eBPF 限制
[L0] aa-status 2>/dev/null || echo "AppArmor not available"   # AppArmor 状态
```

---

### 步骤 3：安全上下文提取

从已写盘的原始数据（`evidence/recon/raw/`）Read 需要的部分，提取安全相关字段写入知识图谱节点。

#### 3.1 提取字段清单

| 来源 | 提取字段 | 写入节点 |
|------|---------|---------|
| Pod spec | `securityContext`（runAsUser, runAsGroup, fsGroup, privileged, allowPrivilegeEscalation, readOnlyRootFilesystem, seccompProfile, capabilities） | `pods.json` |
| Pod spec | `volumes`（hostPath, emptyDir, projected, secret） | `pods.json` |
| Pod spec | `hostNetwork`, `hostPID`, `hostIPC` | `pods.json` |
| Pod spec | `serviceAccountName` | `pods.json` + `service_accounts.json` |
| Container spec | `securityContext`（capabilities.drop/add, privileged, readOnlyRootFilesystem） | `containers.json` |
| Docker inspect | `HostConfig.Privileged`, `HostConfig.PidMode`, `HostConfig.NetworkMode`, `HostConfig.CapAdd`, `HostConfig.SecurityOpt`, `HostConfig.Binds`, `HostConfig.Mounts` | `containers.json` |
| crictl inspect | 同 Docker inspect 字段（containerd 格式） | `containers.json` |
| Node spec | `kubeletConfiguration`, `nodeInfo`（osImage, kernelVersion, containerRuntimeVersion） | `hosts.json` |

#### 3.2 五态标记规则

对每个安全上下文字段，使用五态标记：

| 标记 | 含义 | 说明 |
|------|------|------|
| `[x]` | 已确认存在 | 明确看到配置值，需深审 |
| `[?]` | 疑似 | 配置值为空/默认，需深审 |
| `[-]` | 已检查不适用 | 配置不存在或明确安全 |
| `[!]` | 环境干扰 | 命令失败/超时，无法判定 |
| `[ ]` | 未检查 | Phase 1a 完成时**必须消灭**所有 `[ ]` |

典型标注示例：

```json
{
  "id": "pod-kube-system-apiserver-79f6c5d6c4-abc12",
  "node_type": "pod",
  "data": {
    "namespace": "kube-system",
    "name": "kube-apiserver-79f6c5d6c4-abc12",
    "security_context": {
      "privileged": "[-] false",
      "runAsUser": "[x] 1001",
      "hostNetwork": "[x] true",
      "hostPID": "[-] false",
      "seccompProfile": "[?] 未设置"
    },
    "ip": "10.244.0.3"
  },
  "session_id": "sess-20260619-001"
}
```

#### 3.3 边提取

从原始数据中提取基础设施关系边写入 `knowledge_graph/edges/infra.json`：

| 边类型 | from_node | to_node | 描述 |
|--------|-----------|---------|------|
| `runs_on` | `pod-xxx` | `host-xxx` | Pod 运行在节点上 |
| `uses_sa` | `pod-xxx` | `sa-xxx` | Pod 使用 ServiceAccount |
| `mounts` | `pod-xxx` | `secret-xxx` | Pod 挂载 Secret |
| `exposes` | `service-xxx` | `pod-xxx` | Service 暴露 Pod |
| `host_path_mount` | `pod-xxx` | `host-xxx` | Pod 挂载宿主机路径 |
| `container_in` | `container-xxx` | `pod-xxx` | 容器属于 Pod |

---

### 步骤 4：数据写入与指纹生成

#### 4.1 知识图谱节点写入

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

#### 4.2 知识图谱边写入

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

#### 4.3 侦察摘要

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

#### 4.4 环境指纹生成

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

---

## 分批策略与限速

### SSH 命令限速规则

| 参数 | 值 |
|------|-----|
| 最大并行 SSH 命令数 | 3（同一服务器） |
| 批次间隔 | 2 秒 |
| 单次 SSH 超时 | 30 秒 |
| 降级策略 | 返回 "rate limited" 或 "too many connections" 时，自动降级为串行，间隔从 2 秒升至 5 秒 |

### Pod/容器扫描分批

- 每批 100 个 Pod/容器，间隔 2 秒
- 大集群（300+ Pod）先获取命名空间列表再按命名空间分批
- 每个命名空间一个 WU

### 重试策略

| 命令类型 | 重试次数 | 间隔 | 失败标记 |
|---------|---------|------|---------|
| 读命令（ls/cat/find/kubectl get） | 3 | 2秒 | `[!]`（环境干扰，无法判定） |
| 探测命令（curl/nc/kubectl auth can-i） | 2 | 3秒 | `[!]`，区分"连接超时"和"连接拒绝" |
| 攻击验证命令 | 1 | 5秒 | ATK-CAND 降级为高风险线索 |
| 写入命令（docker run 临时容器等） | 0 | 不重试 | `[!]`（环境干扰，可能已部分生效） |

---

## MUST 输出

Phase 1a 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `knowledge_graph/nodes/hosts.json` | 主机节点（非空） |
| `knowledge_graph/nodes/pods.json` | Pod 节点（非空） |
| `knowledge_graph/nodes/containers.json` | 容器节点（非空） |
| `knowledge_graph/nodes/services.json` | Service 节点 |
| `knowledge_graph/nodes/service_accounts.json` | SA 节点（非空） |
| `knowledge_graph/nodes/secrets.json` | Secret 节点（仅名称+类型，**绝不存储内容**） |
| `knowledge_graph/nodes/findings.json` | 发现节点（占位结构，Phase 2 填充） |
| `knowledge_graph/nodes/_index.md` | 节点总索引 |
| `knowledge_graph/edges/infra.json` | 基础设施关系边 |
| `knowledge_graph/edges/_index.md` | 边总索引 |
| `evidence/recon/recon_summary.md` | 侦察摘要 |
| `evidence/recon/raw/` | 原始 SSH 输出（非空，每段带来源与时间戳） |
| `session_config.json` | 必须含 `env_fingerprint` |

---

## 检查点

Phase 1a 完成判定需全部通过：

1. **主机/容器/Pod/SA 清单非空** — `hosts.json`、`containers.json`、`pods.json`、`service_accounts.json` 四个文件存在且数组非空
2. **安全上下文提取完成** — `pods.json` 中每个 Pod 节点包含 `security_context` 字段，所有五态标记 `[ ]` 已消灭
3. **环境指纹已生成** — `session_config.json` 包含完整 `env_fingerprint`（os_type、arch、kernel_version 为必填，scope 对应的版本字段为必填）
4. **QA 结构校验通过** — 所有 MUST 输出文件存在且非空，`_index.md` 与 JSON 内容一致

---

## WU 摘要格式

每个 WU 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/recon/summaries/{work_unit_id}.json`：

```json
{
  "work_unit_id": "WU-1a-01",
  "status": "complete",
  "summary": "完成 3 节点 K8s 集群侦察，收集 47 个 Pod、9 个 SA、12 个 Secret",
  "critical_findings": [
    "pod-xxx: hostNetwork=true, 暴露节点网络栈",
    "pod-yyy: privileged=true, 特权容器"
  ],
  "files_written": [
    "knowledge_graph/nodes/hosts.json",
    "knowledge_graph/nodes/pods.json",
    "knowledge_graph/nodes/containers.json",
    "knowledge_graph/nodes/services.json",
    "knowledge_graph/nodes/service_accounts.json",
    "knowledge_graph/nodes/secrets.json",
    "knowledge_graph/nodes/findings.json",
    "knowledge_graph/nodes/_index.md",
    "knowledge_graph/edges/infra.json",
    "knowledge_graph/edges/_index.md",
    "evidence/recon/recon_summary.md",
    "evidence/recon/raw/"
  ],
  "context_used": [],
  "issues": []
}
```

---

## 禁止事项

- **不执行攻击命令**：recon 只做侦察，不做 L2 攻击验证
- **不存储 Secret 内容**：`secrets.json` 仅记录名称和类型，禁止记录 Secret value
- **不在上下文中累积原始输出**：所有原始输出立即写盘，只保留摘要
- **不跳过 SSH 输出**：所有数据必须由 `ssh_execute` 真实执行产生，禁止伪造
- **不省略五态标记**：安全上下文的每个字段必须标注五态标记之一
- **不使用 sudo 替代攻击者视角**：L0 观察可用 sudo，但不能替代 L1/L2 验证

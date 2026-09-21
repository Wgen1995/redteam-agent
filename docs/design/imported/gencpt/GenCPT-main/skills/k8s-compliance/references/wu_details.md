# k8s-compliance WU 详细规则分组与多节点检测策略

> 本文件为 `skills/k8s-compliance/SKILL.md` 的 WU 分批详情参考。核心工作流见 SKILL.md。

---

## 多节点检测策略

K8s 合规规则分为两类：
- **集群级规则**（G_1 API Server、G_2 Etcd、G_3 Control Plane、G_6 Network Policies、G_8 RBAC/Secret）：只需在 master 节点（即 `server` 参数指定的入口节点）检查
- **节点级规则**（G_4 Kubelet 认证、G_5 Kubelet 运行时配置、G_7 Pod 安全）：需要在每个节点上检查本地文件

**节点级规则的检测方式**：
1. 从 `session_config.json` 的 `env_fingerprint.worker_nodes` 读取可达的 worker 节点列表
2. 对 master 节点：`ssh_execute(server, "...")` — 直接检查
3. 对可达的 worker 节点：`ssh_execute(server, "ssh <worker_ip> ...")` — 通过 master 跳转到 worker 检查
4. 对不可达的 worker 节点：标记为 `[-] 不适用（SSH 不可达）`，在 results.json 中记录原因
5. 每条节点级规则的检测结果需标注检查的节点名：`"checked_node": "worker-1"`

**G_4/G_5 的 WU 分批调整**：
- WU-2a-02（G_2-G_4）中的 G_4 规则：对每个可达节点执行一次，results.json 中每个节点一条记录
- WU-2a-03（G_5-G_6）中的 G_5 规则：同上
- G_7 规则：通过 `kubectl get pod -o yaml` 从 master 获取所有节点的 Pod 安全上下文，不需要逐节点 SSH

---

## 分批策略（4 个 WU）

134 条规则分 4 批 WU 执行，每批约 40-50 条规则。每批 WU 独立工作，完成后执行第一重校验。

### WU-2a-01：G_1 组（41 条）API Server

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_1_1 | `G_1_1_api_server_files.md` | 7 | API Server 文件权限 |
| G_1_2 | `G_1_2_api_server_auth.md` | 23 | API Server 认证授权 |
| G_1_3 | `G_1_3_api_server_dos.md` | 1 | API Server 防 DoS |
| G_1_4 | `G_1_4_api_server_leak.md` | 3 | API Server 防信息泄露 |
| G_1_5 | `G_1_5_api_server_log.md` | 6 | API Server 审计日志 |
| G_1_6 | `G_1_6_api_server_ssl.md` | 1 | API Server TLS 配置 |

**检测层级**：全部 L0（宿主机检查 kube-apiserver 启动参数和配置文件）
**特殊说明**：G_1_2 含 23 条规则，是最大的子分组，需逐一检查 kube-apiserver 进程启动参数

### WU-2a-02：G_2-G_4 组（29 条）Etcd + Control Plane + Kubelet Auth

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_2_1 | `G_2_1_etcd_files.md` | 4 | Etcd 文件权限 |
| G_2_2 | `G_2_2_etcd_config.md` | 2 | Etcd 配置 |
| G_2_3 | `G_2_3_etcd_security.md` | 4 | Etcd 安全 |
| G_2_4 | `G_2_4_etcd_network.md` | 1 | Etcd 网络 |
| G_3_1 | `G_3_1_cm_security.md` | 4 | Controller Manager 安全 |
| G_3_2 | `G_3_2_scheduler_security.md` | 2 | Scheduler 安全 |
| G_4_1 | `G_4_1_kubelet_auth.md` | 4 | Kubelet 认证 |
| G_4_2 | `G_4_2_kubelet_authz.md` | 7 | Kubelet 授权配置 |
| G_4_3 | `G_4_3_kubelet_config.md` | 1 | Kubelet 配置 |

**检测层级**：全部 L0（宿主机检查 etcd/cm/scheduler/kubelet 配置文件和启动参数）

### WU-2a-03：G_5-G_6 组（26 条）Kubelet Config + Network Policies

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_5_1 | `G_5_1_kubelet_runtime.md` | 8 | Kubelet 运行时配置 |
| G_5_2 | `G_5_2_kubelet_streaming.md` | 6 | Kubelet Streaming 连接 |
| G_5_3 | `G_5_3_kubelet_tls.md` | 2 | Kubelet TLS |
| G_5_4 | `G_5_4_kubelet_leak.md` | 5 | Kubelet 防信息泄露 |
| G_5_5 | `G_5_5_kubelet_dos.md` | 1 | Kubelet 防 DoS |
| G_5_6 | `G_5_6_kubelet_system.md` | 1 | Kubelet 系统配置 |
| G_6_1 | `G_6_1_network_policies.md` | 2 | Network Policies |
| G_6_2 | `G_6_2_network_default_deny.md` | 1 | 默认拒绝网络策略 |

**检测层级**：L0（宿主机检查 kubelet 配置）+ 部分 L1（kubectl exec 检查容器内网络策略）

### WU-2a-04：G_7-G_8 组（38 条）Pod Security + RBAC/Secrets

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_7_1 | `G_7_1_pod_security.md` | 15 | Pod 安全上下文 |
| G_7_2 | `G_7_2_container_runtime.md` | 2 | 容器运行时安全 |
| G_8_1 | `G_8_1_secrets_mgmt.md` | 2 | Secret 管理 |
| G_8_2 | `G_8_2_rbac.md` | 13 | RBAC 权限控制 |
| G_8_3 | `G_8_3_security_context.md` | 2 | Security Context 配置 |
| G_8_4 | `G_8_4_network_policies_advanced.md` | 4 | 高级网络策略 |

**检测层级**：L0（kubectl get 检查集群级 RBAC 和 Secret 配置）+ L1（kubectl exec 检查容器内 securityContext 实际生效值）
**特殊说明**：G_7_1 含 15 条规则，需要遍历所有命名空间的 Pod 逐一检查 securityContext

# recon 安全上下文提取字段与五态标记

> 本文件为 `skills/recon/SKILL.md` 步骤 3 的详细字段参考。核心工作流见 SKILL.md。

---

## 3.1 提取字段清单

从已写盘的原始数据（`evidence/recon/raw/`）Read 需要的部分，提取安全相关字段写入知识图谱节点。

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

---

## 3.2 五态标记规则

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

---

## 3.3 边提取

从原始数据中提取基础设施关系边写入 `knowledge_graph/edges/infra.json`：

| 边类型 | from_node | to_node | 描述 |
|--------|-----------|---------|------|
| `runs_on` | `pod-xxx` | `host-xxx` | Pod 运行在节点上 |
| `uses_sa` | `pod-xxx` | `sa-xxx` | Pod 使用 ServiceAccount |
| `mounts` | `pod-xxx` | `secret-xxx` | Pod 挂载 Secret |
| `exposes` | `service-xxx` | `pod-xxx` | Service 暴露 Pod |
| `host_path_mount` | `pod-xxx` | `host-xxx` | Pod 挂载宿主机路径 |
| `container_in` | `container-xxx` | `pod-xxx` | 容器属于 Pod |

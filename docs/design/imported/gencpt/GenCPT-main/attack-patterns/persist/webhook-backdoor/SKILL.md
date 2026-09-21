---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.1]
mapped_compliance_families: [RBAC权限]
---

# ValidatingWebhook 后门

## 1. 前置条件

- 攻击者有创建/修改 ValidatingWebhookConfiguration 或 MutatingWebhookConfiguration 的权限
- Webhook 服务端点指向攻击者控制的服务
- Webhook configured 的 failurePolicy 为 Fail（阻断所有不满足条件的请求）

## 2. 探测命令

- [L0] `kubectl get validatingwebhookconfigurations -A` → 期望：列出所有 ValidatingWebhookConfiguration
- [L0] `kubectl get mutatingwebhookconfigurations -A` → 期望：列出所有 MutatingWebhookConfiguration
- [L0] `kubectl get validatingwebhookconfigurations -o json | jq '.items[] | {name:.metadata.name, webhooks:.webhooks[] | {name:.name, clientConfig:.clientConfig}}'` → 期望：发现 Webhook 配置及远程服务端点
- [L0] `kubectl auth can-i create validatingwebhookconfigurations --as=system:serviceaccount:<ns>:<sa-name>` → 期望：yes（SA 可创建 Webhook 配置）
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk https://<webhook-service>/validate` → 期望：Webhook 服务可达

## 3. 攻击验证

- [L2] 检查可疑 Webhook 配置：
  `kubectl get validatingwebhookconfigurations <name> -o yaml` → 期望：发现 Webhook 指向外部服务或异常命名空间
- [L2] 检查 Webhook 拦截行为：
  `kubectl apply -f - <<EOF
  apiVersion: v1
  kind: Pod
  metadata:
    name: test-webhook-block
  spec:
    containers:
    - name: test
      image: nginx
  EOF` → 期望：若 Webhook 配置为 Fail 策略，创建可能被阻断
- [L2] 验证 Webhook 可被滥用创建后门：
  `kubectl auth can-i create validatingwebhookconfigurations` → 期望：yes（当前用户/SA 可创建 Webhook）

## 4. 差分证明

- 攻击前 [L0]: ValidatingWebhookConfiguration 列表仅包含预期的策略
- 攻击后 [L2]: 出现新的 ValidatingWebhookConfiguration 指向攻击者控制的服务
- 对比：新 Webhook 的 clientConfig.service 指向非预期命名空间或外部 IP
- 攻击前 [L2]: 正常 Pod 创建请求被接受
- 攻击后 [L2]: Webhook 后门存在时，特定操作被阻断或修改

## 5. 绕过策略

- 若 Webhook 审批需要集群管理员权限：寻找可创建 Webhook 的 ServiceAccount
- 若 Webhook 服务需要 TLS：使用自签名证书或 Let's Encrypt
- 若准入控制器限制 Webhook 创建：通过 CRD 定义替代 Webhook 行为

## 6. 证伪条件

- [L0] `kubectl get validatingwebhookconfigurations` 返回空列表或仅包含预期的系统 Webhook → 证伪（无后门）
- [L0] `kubectl auth can-i create validatingwebhookconfigurations` 返回 no → 证伪（无法创建后门）
- [L0] 所有 Webhook 的 clientConfig.service 指向受信任的命名空间（如 kube-system）→ 证伪
- [L1] Webhook 服务端点不可达或返回健康检查正常 → 需进一步调查

## 7. 审批级别

Level 1：只读命令（kubectl get, kubectl auth can-i）自动通过。
Level 3：创建/修改 Webhook 配置需确认。
destructive: false

## 8. MITRE ATT&CK

T1543 - Create or Modify System Process（通过 ValidatingWebhook 创建后门持久化）
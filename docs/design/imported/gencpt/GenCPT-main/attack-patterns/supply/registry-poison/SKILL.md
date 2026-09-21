---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-6.2]
mapped_compliance_families: [镜像构建, CI/CD]
---

# 仓库投毒

## 1. 前置条件

- 容器镜像仓库未配置认证或认证不足
- 镜像仓库允许推送覆盖现有标签
- 无镜像签名验证机制（cosign/Notary）
- 拉取策略使用 `Always` 或 `IfNotPresent` + latest 标签

## 2. 探测命令

- [L0] `curl -sk https://<registry>/v2/_catalog` → 期望：返回仓库目录（无认证或弱认证）
- [L0] `curl -sk https://<registry>/v2/<repo>/tags/list` → 期望：返回镜像标签列表
- [L0] `kubectl get pods -A -o json | jq '.items[] | .spec.imagePullSecrets'` → 期望：发现无 imagePullSecrets 的 Pod（使用公共仓库）
- [L0] `docker login <registry> 2>&1` → 期望：无认证即可登录或弱密码
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk https://<registry>/v2/_catalog` → 期望：从容器内可访问仓库

## 3. 攻击验证

- [L2] 验证仓库认证不足：
  `curl -sk -X PUT https://<registry>/v2/<repo>/manifests/test-tag -H "Content-Type: application/vnd.docker.distribution.manifest.v2+json" -d '{"schemaVersion":2,"config":{"mediaType":"application/vnd.docker.container.image.v1+json","digest":"sha256:abc123"}}'` → 期望：返回 202（接受推送）或 401/403（有认证）
- [L2] 验证镜像覆盖风险：
  `docker pull <image>:<tag> && docker tag <image>:<tag> <registry>/<image>:<tag> && docker push <registry>/<image>:<tag>` → 期望：推送成功（若仓库无认证）
- [L2] 验证镜像信任链：
  `cosign verify <registry>/<image>:<tag> 2>&1 || echo "No signature verification"` → 期望：无签名或签名验证失败

## 4. 差分证明

- 攻击前 [L0]: 镜像仓库无认证，允许匿名推送
- 攻击后 [L2]: 成功推送篡改后的镜像到仓库
- 对比：使用 SHA 摘要拉取的 Pod 不受影响，仅 latest 标签的 Pod 受影响
- 差分：篡改前后同一标签的镜像 digest 不同

## 5. 绕过策略

- 若仓库要求基本认证：尝试弱密码或默认凭据（admin/admin、registry/registry）
- 若仓库使用 RBAC 授权：检查是否有过度宽松的推送权限
- 若签名验证启用：攻击签名服务或中间人攻击（MITM）替换签名

## 6. 证伪条件

- [L0] `curl -sk https://<registry>/v2/_catalog` 返回 401/403 → 证伪（认证启用）
- [L0] 镜像仓库使用 TLS 且证书验证正确 → 证伪（无法 MITM）
- [L0] ImagePolicyWebhook 强制签名验证 → 证伪
- [L1] 仓库推送操作需要有效 token 且 token 权限最小 → 证伪

## 7. 审批级别

Level 2：探测命令（curl 访问仓库 API）自动通过。
Level 3：攻击验证（推送测试镜像）需确认。
destructive: false（推送的测试镜像应使用专用标签名，避免覆盖生产镜像）

## 8. MITRE ATT&CK

T1195 - Supply Chain Compromise（通过仓库投毒进行供应链攻击）
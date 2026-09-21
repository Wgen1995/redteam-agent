---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-6.1]
mapped_compliance_families: [镜像构建, CI/CD]
---

# 镜像标签篡改

## 1. 前置条件

- Pod/Deployment 使用 `latest` 或无固定标签的镜像
- 镜像仓库未配置内容信任（Docker Content Trust / cosign）
- 无镜像签名验证或准入控制器（AdmissionController）强制

## 2. 探测命令

- [L0] `kubectl get pods -A -o json | jq '.items[] | {name:.metadata.name, images:[.spec.containers[].image, .spec.initContainers[].image?]}' | grep -E ':latest|@<none>'` → 期望：发现使用 latest 标签或无摘要的镜像
- [L0] `kubectl get deployments -A -o json | jq '.items[] | select(.spec.template.spec.containers[].image | test("\\blatest\\b|:[0-9a-f]{0,7}$")) | {name:.metadata.name, images:.spec.template.spec.containers[].image}'` → 期望：发现使用可变标签的 Deployment
- [L0] `docker images --format '{{.Repository}}:{{.Tag}}' | grep latest` → 期望：发现本地 latest 标签镜像
- [L1] `kubectl exec <pod> -n <ns> -- cat /etc/resolv.conf && kubectl exec <pod> -n <ns> -- curl -sk https://<registry>/v2/<image>/manifests/latest` → 期望：验证镜像仓库是否可访问且 latest 标签可变

## 3. 攻击验证

- [L2] 验证镜像标签可变性：
  `kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep -E ':latest$|_latest_'` → 期望：发现使用 latest 标签的 Pod
- [L2] 验证镜像摘要缺失：
  `kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].imageID}{"\n"}{end}'` → 期望：imageID 为空或仅标签无摘要
- [L2] 验证标签覆盖风险：
  `docker pull <image>:latest && docker inspect <image>:latest --format '{{.Id}}' && sleep 10 && docker pull <image>:latest && docker inspect <image>:latest --format '{{.Id}}'` → 期望：两次拉取得到不同 ID（证明标签可变）

## 4. 差分证明

- 攻击前 [L0]: Pod 使用 `image:repo/app:latest` 标签
- 攻击后 [L2]: 两次拉取同一标签获得不同镜像 ID → 证明标签可被篡改
- 对比：使用 SHA 摘要引用（`image:repo/app@sha256:abc123...`）的 Pod 不受影响

## 5. 绕过策略

- 若准入控制器阻止 latest 标签：使用浮动标签（如 `v1`、`stable`、`production`）绕过
- 若镜像签名验证启用：攻击镜像仓库替换签名（若仓库密钥泄露）
- 若 K8s ImagePolicyWebhook 启用：寻找未覆盖的命名空间或特殊豁免

## 6. 证伪条件

- [L0] 所有 Deployment/Pod 使用 SHA 摘要引用（`image@sha256:...`）→ 证伪
- [L0] ImagePolicyWebhook 强制拒绝可变标签 → 证伪
- [L0] Docker Content Trust 启用且强制（`DOCKER_CONTENT_TRUST=1`）→ 证伪
- [L1] 准入控制器（OPA/Gatekeeper/Kyverno）强制镜像标签策略 → 证伪

## 7. 审批级别

Level 1：只读命令（kubectl get, docker images）自动通过。
Level 2：攻击验证（docker pull 对比）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1195.003 - Compromise Software Supply Chain: Software Supply Chain（通过镜像标签篡改进行供应链攻击）
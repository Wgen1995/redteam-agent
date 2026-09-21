---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.13]
mapped_compliance_families: [APIService, 准入控制]
---

# aggregated-apiserver-abuse — APIService 聚合 API 劫持

攻击者持有 `apiservices` 的 `create/update` 权限，可通过注册恶意 APIService 将特定 group/version 的请求转发到攻击者控制的 Service，劫持聚合 API 请求、窃取凭证或注入恶意响应，破坏准入控制与鉴权链。

---

## 1. 前置条件

- 当前身份被授予 `apiservices` 的 `create` 权限（或 `update` 可改写现有 APIService）
- 攻击者可部署一个恶意 Service（运行恶意 apiserver 实现）作为后端
- 集群使用聚合 API 机制（API Server 启用了 `--requestheader` 与 aggregation）

检查命令：
```bash
# [L0] 探测：检查 APIService 创建权限
kubectl auth can-i create apiservices
# 期望输出: yes

# [L0] 探测：列出当前 APIService
kubectl get apiservice
# 期望输出: 已注册的 APIService 列表
```

## 2. 探测命令

```bash
# [L0] 探测：确认现有 APIService 与后端 Service
kubectl get apiservice -o wide
# 期望输出: service 字段指向具体 Service

# [L0] 探测：检查可疑 APIService 是否指向非官方 Service
kubectl get apiservice -o jsonpath='{range .items[*]}{@.metadata.name}{" -> "}{@.spec.service.name}{"\n"}{end}'
# 期望输出: group/version -> service 映射

# [L0] 探测：检查 APIService 后端是否可达
kubectl get svc -n <ns> <service-name> -o wide
# 期望输出: 后端 Service 的 ClusterIP/端口
```

## 3. 攻击验证

```bash
# [L2] 攻击验证：部署恶意 apiserver Service
kubectl apply -f malicious-apiservice.yaml
# 期望输出: apiservice.apiregistration.k8s.io/<name> created

# [L2] 攻击验证：访问被劫持的 group/version
kubectl get <custom-resource> -A
# 期望输出: 请求被转发到攻击者 Service（落地于恶意后端）

# [L2] 攻击验证：通过劫持的 API 窃取请求凭证
kubectl get <custom-resource> 2>&1 | grep -i token
# 期望输出: 含 forwarded token/请求体（攻击者后端捕获）
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：APIService 列表
kubectl get apiservice | wc -l
# 期望输出: N

# [L0] 攻击后环境对比：新增恶意 APIService
kubectl get apiservice | wc -l
# 期望输出: N+1 → 证明恶意 APIService 被注册

# [L0] 攻击前/后对比：被劫持 group/version 路由变化
kubectl api-resources --api-group=<group> 2>&1
# 期望输出: 攻击前无该 group；攻击后被劫持 → 证明 API 路由变更
```

差分结论：攻击前 APIService 数量为 N 且目标 group 不可达，攻击后注册恶意 APIService 数量变为 N+1 且 group 请求被劫持，证明聚合 API 被滥用。

## 5. 绕过策略

```bash
# [L0] 检查 RBAC 是否限制 APIService 创建
kubectl auth can-i create apiservices
# 若 no → 无法注册新 APIService

# 绕过方式：
# - [L2] 若仅限制 create 但允许 update，改写已有 APIService 的 service 指向
# - [L2] 若 PodSecurity 限制后端 Pod，使用已有合法 Service 作为代理
# - [L2] 若准入 webhook 校验 APIService，先劫持 webhook 配置放行
```

## 6. 证伪条件

```bash
# [L0] 无 APIService 创建/更新权限
kubectl auth can-i create apiservices
kubectl auth can-i update apiservices
# 输出: no no → 证伪

# [L2] 注册失败
kubectl apply -f malicious-apiservice.yaml 2>&1
# 输出: forbidden → 证伪

# [L2] APIService 注册但请求未转发到攻击者后端
kubectl get <custom-resource> 2>&1
# 输出: connection refused 或 NotFound → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（注册恶意 APIService 劫持请求）→ **Level 4**（破坏准入/鉴权链，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Persistence / Privilege Escalation / Defense Evasion
- **Technique ID**: T1610
- **Technique Name**: Deploy Container
- **描述**: 攻击者持有 `apiservices` 创建/更新权限，注册恶意 APIService 将特定 group/version 请求劫持到攻击者控制的 Service，窃取凭证、注入响应或破坏准入控制链。
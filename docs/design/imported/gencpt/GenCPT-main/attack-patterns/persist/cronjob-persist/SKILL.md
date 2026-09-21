---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.2]
mapped_compliance_families: [RBAC权限]
---

# CronJob 持久化

## 1. 前置条件

- 攻击者有创建 CronJob 的权限
- K8s 环境中 CronJob 控制器启用（默认启用）
- CronJob 可配置为执行恶意命令（如反弹 shell、定期执行后门脚本）

## 2. 探测命令

- [L0] `kubectl get cronjobs -A` → 期望：列出所有 CronJob，发现可疑条目
- [L0] `kubectl auth can-i create cronjobs --as=system:serviceaccount:<ns>:<sa-name>` → 期望：yes（SA 可创建 CronJob）
- [L0] `kubectl get cronjobs -A -o json | jq '.items[] | select(.spec.schedule | test("1|\\*")) | {name:.metadata.name, schedule:.spec.schedule, image:.spec.jobTemplate.spec.template.spec.containers[].image}'` → 期望：发现高频或全匹配的 CronJob
- [L0] `kubectl get cronjobs -A -o json | jq '.items[] | {name:.metadata.name, namespace:.metadata.namespace, schedule:.spec.schedule, command:.spec.jobTemplate.spec.template.spec.containers[].command}'` → 期望：列出 CronJob 的执行命令

## 3. 攻击验证

- [L2] 检查可疑 CronJob：
  `kubectl get cronjob <suspicious-name> -n <ns> -o yaml` → 期望：发现 CronJob 执行反弹 shell 或恶意脚本
- [L2] 验证可创建 CronJob 持久化：
  `kubectl auth can-i create cronjobs -n <ns>` → 期望：yes（可在命名空间创建 CronJob）
- [L2] 检查 CronJob 创建的 Pod：
  `kubectl get pods -n <ns> | grep <cronjob-name>` → 期望：发现 CronJob 创建的 Pod

## 4. 差分证明

- 攻击前 [L0]: 命名空间无异常 CronJob
- 攻击后 [L2]: 新增 CronJob 执行反弹 shell 或恶意命令
- 对比：新 CronJob 的 schedule 为 `* * * * *`（每分钟执行）或异常镜像
- 攻击前 [L0]: CronJob 列表仅包含预期条目
- 攻击后 [L2]: 出现 C2 回连命令或特权容器执行的 CronJob

## 5. 绕过策略

- 若直接创建 CronJob 被阻止：使用 Job 手动触发，再通过 RBAC 创建 CronJob
- 若 CronJob 镜像受准入控制器限制：使用受信任的镜像（如 alpine/busybox）+ command 执行恶意操作
- 若 CronJob 被监控：降低执行频率（如每天凌晨 3 点）、使用混淆命令
- 若创建 CronJob 权限被限制：检查是否有 edit/parent 角色可间接创建

## 6. 证伪条件

- [L0] `kubectl auth can-i create cronjobs` 返回 no → 证伪（无法创建 CronJob）
- [L0] 所有 CronJob 均为预期的系统/应用 CronJob → 证伪（无可疑条目）
- [L0] CronJob 控制器禁用（kube-controller-manager --controllers=-cronjob）→ 证伪
- [L0] 准入控制器阻止异常 CronJob 创建 → 证伪

## 7. 审批级别

Level 1：只读命令（kubectl get, kubectl auth can-i）自动通过。
Level 3：创建 CronJob 需确认。
destructive: false

## 8. MITRE ATT&CK

T1053 - Scheduled Task/Job（通过 K8s CronJob 实现持久化）
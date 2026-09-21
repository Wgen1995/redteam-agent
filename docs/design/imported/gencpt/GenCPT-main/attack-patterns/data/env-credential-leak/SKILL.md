---
source: manual
confidence: high
platforms: [k8s, docker, containerd]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.2]
mapped_compliance_families: [Secret防泄露]
---

# 环境变量凭证泄露

## 1. 前置条件

- 容器配置文件或 Pod 清单通过环境变量注入敏感信息
- 容器内进程环境变量包含密码、API Key、Token 等
- `/proc/<pid>/environ` 文件可读（容器内默认可读自身进程）
- Docker inspect 或 kubectl describe 可显示环境变量

## 2. 探测命令

- [L0] `kubectl get pods -A -o json | jq '.items[] | {name:.metadata.name, namespace:.metadata.namespace, envs:.spec.containers[].env[]?.name}' | grep -iE 'password|secret|token|key|api_key|credential|auth'` → 期望：发现 Pod 清单中的敏感环境变量名
- [L0] `docker inspect <container> | jq '.[0].Config.Env[]' | grep -iE 'password|secret|token|key|api_key|credential|auth'` → 期望：发现 Docker 容器中的敏感环境变量
- [L1] `kubectl exec <pod> -n <ns> -- env | grep -iE 'password|secret|token|key|api_key|credential|auth'` → 期望：发现容器内环境变量中的明文凭据
- [L1] `kubectl exec <pod> -n <ns> -- cat /proc/1/environ | tr '\0' '\n' | grep -iE 'password|secret|token|key|api_key|credential|auth'` → 期望：从进程 environ 读取敏感变量
- [L1] `docker exec <container> env | grep -iE 'password|secret|token|key|api_key|credential|auth'` → 期望：Docker 容器内敏感环境变量

## 3. 攻击验证

- [L2] 从容器内读取完整环境变量：
  `kubectl exec <pod> -n <ns> -- env` → 期望：列出所有环境变量，包含密码明文
- [L2] 从 /proc 读取 PID 1 环境变量：
  `kubectl exec <pod> -n <ns> -- cat /proc/1/environ | tr '\0' '\n'` → 期望：环境变量中包含数据库密码、API Key 等明文值
- [L2] Docker 环境变量泄露：
  `docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}'` → 期望：宿主机上可读取容器环境变量含明文凭据

## 4. 差分证明

- 攻击前 [L0]: Pod 清单显示 envFrom 引用了 Secret/ConfigMap
- 攻击后 [L1]: 容器内环境变量包含明文密码值
- 对比：K8s Secret 中存储的是 base64 编码值，但容器环境变量中是明文解码值
- 攻击前 [L0]: `kubectl describe pod <pod>` 显示环境变量来源为 Secret
- 攻击后 [L2]: 容器内环境变量直接泄露 Secret 的明文内容

## 5. 绕过策略

- 若 `env` 命令被删除：使用 `cat /proc/self/environ` 或 `cat /proc/1/environ` 替代
- 若容器内 shell 被限制：使用 `kubectl exec` 或 `docker exec` 的 `-e` 参数导出
- 若环境变量通过 Secret 注入但 valueFrom 引用：读取 `/proc/<pid>/environ` 仍可获取明文值
- 若使用了 Init Container 注入：检查 Init Container 的环境变量残留

## 6. 证伪条件

- [L0] Pod 清单中无 env/envFrom 字段或所有环境变量值均为非敏感配置 → 证伪
- [L1] `kubectl exec <pod> -- env | grep -iE 'password|secret|token|key'` 无匹配 → 证伪
- [L1] `kubectl exec <pod> -- cat /proc/1/environ | tr '\0' '\n' | grep -iE 'password|secret|token|key'` 无匹配 → 证伪
- [L0] 所有敏感信息使用 Secret 卷挂载而非环境变量注入 → 证伪（环境变量泄露路径）

## 7. 审批级别

Level 1：只读命令（env, cat /proc/environ）自动通过。
Level 2：攻击验证（读取完整环境变量）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1552.001 - Unsecured Credentials: Credentials In Files（环境变量泄露凭证）
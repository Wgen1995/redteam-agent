# G_1_2 API Server 认证授权（23 条）

CIS Kubernetes Benchmark v1.8.0 — 1.2 Control Plane Configuration: API Server 认证与授权检查。
覆盖 K8s-1.2.1 至 K8s-1.2.23，共 23 条规则。
涵盖：匿名认证、token 认证、准入插件、授权模式、ServiceAccount、kubelet 证书、etcd TLS、API Server TLS、Secret 加密、Webhook 授权、bootstrap token 等。

检查命令通过读取 kube-apiserver 启动参数获取（静态 Pod 清单或进程命令行）。

---

### K8s-1.2.1 禁用 API Server 匿名认证

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--anonymous-auth=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--anonymous-auth=[^ ]*'")
```

**期望值**: `--anonymous-auth=false`
**判定标准**: pass=参数值为 false，fail=参数值为 true 或未设置（默认 true），na=不适用
**修复建议**: 在 kube-apiserver 启动参数中添加 `--anonymous-auth=false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.1 "Ensure that the --anonymous-auth argument is set to false"
**攻击面关联**: AS-2 认证授权（匿名访问允许未认证用户调用 API Server 探测集群信息）

---

### K8s-1.2.2 禁用静态 Token 认证文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--token-auth-file=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--token-auth-file=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `NOT_SET`（参数未设置）
**判定标准**: pass=--token-auth-file 参数未设置，fail=--token-auth-file 参数已设置指向静态 token 文件，na=不适用
**修复建议**: 移除 kube-apiserver 启动参数中的 `--token-auth-file` 参数；改用 ServiceAccount Token 或 OIDC 认证
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.2 "Ensure that the --token-auth-file argument is not set"
**攻击面关联**: AS-2 认证授权（静态 token 文件长期有效且无法自动轮换）

---

### K8s-1.2.3 启用 DenyServiceExternalIPs 准入插件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'DenyServiceExternalIPs' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'DenyServiceExternalIPs' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `DenyServiceExternalIPs`
**判定标准**: pass=enable-admission-plugins 列表包含 DenyServiceExternalIPs，fail=未包含 DenyServiceExternalIPs 插件，na=集群不使用 ExternalIP 类型的 Service
**修复建议**: 在 `--enable-admission-plugins` 参数列表中追加 `DenyServiceExternalIPs`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.3 "Ensure that the --DenyServiceExternalIPs admission control plugin is set"
**攻击面关联**: AS-3 网络（未限制 ExternalIP 可被攻击者用于 IP 劫持和流量劫持）

---

### K8s-1.2.4 启用 kubelet HTTPS 连接

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--kubelet-https=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--kubelet-https=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--kubelet-https=true`
**判定标准**: pass=参数值为 true 或未设置（默认 true），fail=参数值为 false，na=不适用
**修复建议**: 在 kube-apiserver 启动参数中设置 `--kubelet-https=true`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.4 "Ensure that the --kubelet-https argument is set to true"
**攻击面关联**: AS-3 网络（明文 HTTP 连接 kubelet 易被中间人攻击劫持/篡改）

---

### K8s-1.2.5 禁止 API Server 始终允许授权模式

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--authorization-mode=[^ ]*'")
```

**期望值**: 输出值不包含 `AlwaysAllow`
**判定标准**: pass=--authorization-mode 值不含 AlwaysAllow，fail=--authorization-mode 值包含 AlwaysAllow，na=不适用
**修复建议**: 将 `--authorization-mode` 设置为 `Node,RBAC` 或其他非 AlwaysAllow 模式组合
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.5 "Ensure that the --authorization-mode argument is not set to AlwaysAllow"
**攻击面关联**: AS-2 认证授权（AlwaysAllow 模式下任何认证用户拥有所有权限）

---

### K8s-1.2.6 授权模式包含 Node

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'Node' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'Node' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `Node`
**判定标准**: pass=--authorization-mode 值包含 Node，fail=--authorization-mode 值不包含 Node，na=不适用
**修复建议**: 在 `--authorization-mode` 参数中追加 `Node`，如 `--authorization-mode=Node,RBAC`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.6 "Ensure that the --authorization-mode argument includes Node"
**攻击面关联**: AS-2 认证授权（Node 授权器限制 kubelet 只能操作本节点资源）

---

### K8s-1.2.7 授权模式包含 RBAC

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'RBAC' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'RBAC' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `RBAC`
**判定标准**: pass=--authorization-mode 值包含 RBAC，fail=--authorization-mode 值不包含 RBAC，na=不适用
**修复建议**: 在 `--authorization-mode` 参数中追加 `RBAC`，如 `--authorization-mode=Node,RBAC`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.7 "Ensure that the --authorization-mode argument includes RBAC"
**攻击面关联**: AS-2 认证授权（RBAC 是 K8s 最小权限原则的基础机制）

---

### K8s-1.2.8 设置 client-ca-file 客户端 CA 文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--client-ca-file=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--client-ca-file=[^ ]*'")
```

**期望值**: 参数设置为存在的文件路径，如 `--client-ca-file=/etc/kubernetes/pki/ca.crt`
**判定标准**: pass=--client-ca-file 指向有效 CA 证书文件，fail=未设置或文件路径不存在，na=不适用
**修复建议**: 设置 `--client-ca-file=/etc/kubernetes/pki/ca.crt`（使用集群实际 CA 路径）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.8 "Ensure that the --client-ca-file argument is set as appropriate"
**攻击面关联**: AS-2 认证授权（无 CA 验证则客户端证书可信链断裂，可伪造客户端身份）

---

### K8s-1.2.9 准入插件包含 ServiceAccount

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'ServiceAccount' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'ServiceAccount' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `ServiceAccount`
**判定标准**: pass=enable-admission-plugins 列表包含 ServiceAccount，fail=未包含 ServiceAccount，na=不适用
**修复建议**: 在 `--enable-admission-plugins` 参数列表中追加 `ServiceAccount`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.9 "Ensure that the --enable-admission-plugins argument is set to a value that includes ServiceAccount"
**攻击面关联**: AS-2 认证授权（ServiceAccount 准入插件强制 Pod 绑定 SA，缺失导致 Pod 以匿名身份运行）

---

### K8s-1.2.10 准入插件包含 NodeRestriction

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'NodeRestriction' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'NodeRestriction' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `NodeRestriction`
**判定标准**: pass=enable-admission-plugins 列表包含 NodeRestriction，fail=未包含 NodeRestriction，na=不适用
**修复建议**: 在 `--enable-admission-plugins` 参数列表中追加 `NodeRestriction`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.10 "Ensure that the --enable-admission-plugins argument is set to a value that includes NodeRestriction"
**攻击面关联**: AS-2 认证授权（NodeRestriction 限制 kubelet 只能修改本节点上的 Pod/Node 对象）

---

### K8s-1.2.11 准入插件包含 AlwaysPullImages

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'AlwaysPullImages' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'AlwaysPullImages' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `AlwaysPullImages`
**判定标准**: pass=enable-admission-plugins 列表包含 AlwaysPullImages，fail=未包含 AlwaysPullImages，na=不适用（私有独占集群可选 NA）
**修复建议**: 在 `--enable-admission-plugins` 参数列表中追加 `AlwaysPullImages`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.11 "Ensure that the --enable-admission-plugins argument is set to a value that includes AlwaysPullImages"
**攻击面关联**: AS-6 供应链（强制每次拉取镜像防止被植入后门的缓存镜像被复用）

---

### K8s-1.2.12 准入插件包含 SecurityContextDeny 或 PodSecurity

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -oE 'SecurityContextDeny|PodSecurityPolicy' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -oE 'SecurityContextDeny|PodSecurityPolicy' || echo 'NOT_SET'")
```
补充验证 PodSecurityStandards 准入标签：
```bash
ssh_execute(server, "kubectl get ns --show-labels 2>/dev/null | grep -E 'pod-security.kubernetes.io/(enforce|audit|warn)' || echo 'NO_PSA_LABEL'")
```

**期望值**: 第一条输出包含 `SecurityContextDeny` 或 `PodSecurityPolicy`，或第二条输出含 PSA 标签
**判定标准**: pass=启用 SecurityContextDeny 或 PodSecurityPolicy 或 PodSecurityStandards 标签，fail=均未启用，na=不适用
**修复建议**: 启用 `PodSecurityStandards`：在命名空间上打标签 `pod-security.kubernetes.io/enforce=restricted`；或在准入插件中启用 `SecurityContextDeny`/`PodSecurityPolicy`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.12 "Ensure that the --enable-admission-plugins argument is set to a value that includes SecurityContextDeny"（新版使用 PodSecurity 替代）
**攻击面关联**: AS-1 逃逸（强制 securityContext 约束阻止特权容器和危险 capabilities）

---

### K8s-1.2.13 设置 kubelet 客户端证书与密钥

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--kubelet-client-certificate=[^ ]*' && ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--kubelet-client-key=[^ ]*'")
```

**期望值**: 两个参数均已设置且指向有效文件路径
**判定标准**: pass=--kubelet-client-certificate 和 --kubelet-client-key 均设置且文件存在，fail=任一参数缺失或文件不存在，na=不适用
**修复建议**: 设置 `--kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.13 "Ensure that the --kubelet-client-certificate and --kubelet-client-key arguments are set as appropriate"
**攻击面关联**: AS-2 认证授权（无客户端证书则 API Server 无法向 kubelet 提供身份证明）

---

### K8s-1.2.14 设置 kubelet 证书授权机构 CA 文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--kubelet-certificate-authority=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--kubelet-certificate-authority=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: 参数设置为存在的 CA 证书文件路径，如 `--kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt`
**判定标准**: pass=--kubelet-certificate-authority 指向有效 CA 证书文件，fail=未设置或文件路径不存在，na=不适用
**修复建议**: 设置 `--kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt`（使用集群实际 CA 路径）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.14 "Ensure that the --kubelet-certificate-authority argument is set as appropriate"
**攻击面关联**: AS-3 网络（无 CA 验证则 kubelet 证书可被伪造，劫持 API Server 与 kubelet 通信）

---

### K8s-1.2.15 启用 ServiceAccount 令牌查找校验

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--service-account-lookup=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--service-account-lookup=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `--service-account-lookup=true`
**判定标准**: pass=参数值为 true 或未设置（K8s 1.8+ 默认 true），fail=参数值为 false，na=不适用
**修复建议**: 在 kube-apiserver 启动参数中设置 `--service-account-lookup=true` 或移除该参数以使用默认值
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.15 "Ensure that the --service-account-lookup argument is set to true"
**攻击面关联**: AS-2 认证授权（关闭 SA 查找则已删除的 SA Token 仍可使用，扩大被盗令牌生效期）

---

### K8s-1.2.16 设置 ServiceAccount 签名密钥文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--service-account-key-file=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--service-account-key-file=[^ ]*'")
```

**期望值**: 参数设置为存在的公钥文件路径，如 `--service-account-key-file=/etc/kubernetes/pki/sa.pub`
**判定标准**: pass=--service-account-key-file 指向有效公钥文件，fail=未设置或文件路径不存在，na=不适用
**修复建议**: 设置 `--service-account-key-file=/etc/kubernetes/pki/sa.pub`（使用集群实际密钥路径）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.16 "Ensure that the --service-account-key-file argument is set as appropriate"
**攻击面关联**: AS-2 认证授权（无可验签密钥则 SA Token 可被伪造）

---

### K8s-1.2.17 启用 etcd 客户端证书与密钥

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--etcd-certfile=[^ ]*' && ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--etcd-keyfile=[^ ]*'")
```

**期望值**: 两个参数均已设置且指向有效文件路径
**判定标准**: pass=--etcd-certfile 和 --etcd-keyfile 均设置且文件存在，fail=任一参数缺失或文件不存在，na=非本地 etcd 部署
**修复建议**: 设置 `--etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.17 "Ensure that the --etcd-certfile and --etcd-keyfile arguments are set as appropriate"
**攻击面关联**: AS-4 数据泄露（无 etcd 客户端证书则无法验证 API Server 身份，可能被劫持读取 Secret）

---

### K8s-1.2.18 启用 etcd 证书授权机构 CA 文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--etcd-cafile=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--etcd-cafile=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: 参数设置为存在的 CA 证书文件路径，如 `--etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt`
**判定标准**: pass=--etcd-cafile 指向有效 CA 证书文件，fail=未设置或文件路径不存在，na=非本地 etcd 部署
**修复建议**: 设置 `--etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt`（使用集群实际 etcd CA 路径）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.18 "Ensure that the --etcd-cafile argument is set as appropriate"
**攻击面关联**: AS-4 数据泄露（无 etcd CA 验证则 etcd 证书可伪造，劫持 API Server 与 etcd 的通信）

---

### K8s-1.2.19 启用 API Server TLS 证书与私钥

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--tls-cert-file=[^ ]*' && ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--tls-private-key-file=[^ ]*'")
```

**期望值**: 两个参数均已设置且指向有效文件路径
**判定标准**: pass=--tls-cert-file 和 --tls-private-key-file 均设置且文件存在，fail=任一参数缺失或文件不存在，na=不适用
**修复建议**: 设置 `--tls-cert-file=/etc/kubernetes/pki/apiserver.crt --tls-private-key-file=/etc/kubernetes/pki/apiserver.key`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.19 "Ensure that the --tls-cert-file and --tls-private-key-file arguments are set as appropriate"
**攻击面关联**: AS-4 数据泄露（无 TLS 证书则 API Server 通信无法加密， confidentiality 破坏）

---

### K8s-1.2.20 启用 Secret 加密配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--encryption-provider-config=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--encryption-provider-config=[^ ]*' || echo 'NOT_SET'")
```
然后查看实际加密配置（仅查看是否使用 aescbc/kms/secretbox 等强加密）：
```bash
ssh_execute(server, "ENC_FILE=$(ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--encryption-provider-config=[^ ]*' | cut -d= -f2); cat $ENC_FILE 2>/dev/null | grep -oE 'aescbc|aesgcm|secretbox|kms' || echo 'NO_STRONG_PROVIDER'")
```

**期望值**: --encryption-provider-config 设置且配置文件包含 aescbc/secretbox/kms 等强加密提供器
**判定标准**: pass=--encryption-provider-config 设置且配置文件包含非 identity 提供器（aescbc/aesgcm/secretbox/kms），fail=未设置或仅使用 identity（不加密），na=不适用
**修复建议**: 创建 EncryptionConfiguration 文件使用 aescbc 或 kms 提供器，并设置 `--encryption-provider-config=/etc/kubernetes/enc-config.yaml`；随后执行 Secret 轮换重新加密现有数据
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.20 "Ensure that the --encryption-provider-config argument is set as appropriate"
**攻击面关联**: AS-4 数据泄露（未加密的 etcd 中 Secret 可被直接读取明文）

---

### K8s-1.2.21 准入插件包含 EventRateLimit

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'EventRateLimit' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-admission-plugins=[^ ]*' | grep -o 'EventRateLimit' || echo 'NOT_SET'")
```

**期望值**: 输出包含 `EventRateLimit`
**判定标准**: pass=enable-admission-plugins 列表包含 EventRateLimit，fail=未包含 EventRateLimit，na=不适用
**修复建议**: 在 `--enable-admission-plugins` 参数列表中追加 `EventRateLimit`，并配置 EventRateLimit 准入配置文件
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.21 "Ensure that the --enable-admission-plugins argument is set to include EventRateLimit"（Advanced）
**攻击面关联**: AS-5 拒绝服务（无限 Event 生成可导致 etcd 填满并耗尽集群存储）

---

### K8s-1.2.22 授权模式包含 Webhook

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'Webhook' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--authorization-mode=[^ ]*' | grep -o 'Webhook' || echo 'NOT_SET'")
```
补充验证 kubelet 也使用 webhook 授权模式：
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--authorization-mode=[^ ]*' || cat /var/lib/kubelet/config.yaml 2>/dev/null | grep -E 'authorization:' -A1")
```

**期望值**: API Server authorization-mode 包含 Webhook，或 kubelet authorization.mode=Webhook
**判定标准**: pass=API Server authorization-mode 含 Webhook 且 kubelet authorization.mode=Webhook，fail=任一未启用 Webhook，na=不适用（小型集群可豁免）
**修复建议**: 在 API Server 的 `--authorization-mode` 添加 `Webhook`；在 kubelet 配置 `/var/lib/kubelet/config.yaml` 中设置 `authorization: mode: Webhook`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.22 "Ensure that the --authorization-mode argument is set to a value that includes Webhook"
**攻击面关联**: AS-2 认证授权（Webhook 模式将授权决策委托 API Server，避免 kubelet 本地 AlwaysAllow）

---

### K8s-1.2.23 禁用 Bootstrap Token 认证

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--enable-bootstrap-token-auth=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--enable-bootstrap-token-auth=[^ ]*' || echo 'NOT_SET'")
```

**期望值**: `NOT_SET`（参数未设置，默认为 false）或 `--enable-bootstrap-token-auth=false`
**判定标准**: pass=--enable-bootstrap-token-auth=false 或参数未设置（默认 false），fail=--enable-bootstrap-token-auth=true，na=不适用
**修复建议**: 移除 kube-apiserver 启动参数中的 `--enable-bootstrap-token-auth=true` 或显式设置 `--enable-bootstrap-token-auth=false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.2.23 "Ensure that the --enable-bootstrap-token-auth argument is not set to true"
**攻击面关联**: AS-2 认证授权（bootstrap token 长期启用扩大节点加入攻击窗口，可被窃取用于未授权节点扩容）
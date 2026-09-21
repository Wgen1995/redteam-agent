# 容器渗透测试攻击模式库索引

> 7 大攻击面目录总览、条件触发读取表、平台过滤规则、模式文件 frontmatter 概要

## 攻击面目录

| 攻击面ID | 名称 | 模式数 | 模式目录 | 说明 |
|----------|------|--------|----------|------|
| AS-1 | 逃逸 | 12 | `escape/` | docker.sock 逃逸、cgroup 逃逸、procfs 逃逸、runc 逃逸、hostPath 挂载、capability 提权、containerd-shim 逃逸、特权容器逃逸、hostPID/hostIPC 逃逸、hostNetwork 滥用、shareProcessNamespace 滥用、sysctl 滥用 |
| AS-2 | 认证授权 | 14 | `auth/` | K8s SA 滥用、RBAC 提权、匿名访问、Docker API 认证绕过、K8s exec 滥用、containerd ctr 滥用、K8s Ephemeral Container 注入、Kubelet API 滥用、etcd 未授权访问、etcd 证书窃取、CSR API 滥用、节点身份提权、TokenRequest API 滥用、Aggregated APIServer 滥用 |
| AS-3 | 网络 | 7 | `network/` | 横向移动、云元数据泄露、DNS 外发、NTFS ALPN 协议攻击、K8s Node Proxy/Port-Forward 滥用、NetworkPolicy 绕过、kubectl port-forward 滥用 |
| AS-4 | 数据泄露 | 6 | `data/` | Secret 外发、环境变量凭据泄露、镜像层敏感信息、云提供商凭证窃取、ConfigMap 数据泄露、etcd 数据泄露 |
| AS-5 | 拒绝服务 | 2 | `dos/` | 资源滥用、fork 炸弹 |
| AS-6 | 供应链 | 2 | `supply/` | 镜像标签篡改、仓库投毒 |
| AS-7 | 持久化 | 6 | `persist/` | Webhook 后门、CronJob 持久化、Docker Volume 持久化、MutatingWebhook 持久化、DaemonSet 持久化、Deployment 镜像覆盖 |
| **合计** | | **49** | | **7 攻击面 / 49 模式** |

## 条件触发读取表

> Phase 4a 启动时，必须先读 compliance 合规结果和 recon 侦察结果，然后根据下表决定读哪些模式文件。
> **不准凭记忆出攻击命令！必须 Read 对应 SKILL.md。**

| 触发信号 | 来源 | 需读取的模式 | 平台 |
|----------|------|-------------|------|
| K8s-7.1.1 privileged=true | 合规G_7 | socket-escape, capability-privesc, hostpath-mount | k8s |
| K8s docker.sock挂载 | 侦察 | socket-escape | k8s |
| K8s hostPath挂载 | 侦察/合规 | hostpath-mount | k8s |
| K8s capabilities含CAP_SYS_ADMIN | 合规G_7 | capability-privesc | k8s |
| /proc/1/cgroup可见 | 侦察 | cgroup-escape | k8s,docker |
| /proc mounted rw | 侦察 | procfs-escape | k8s,docker |
| runc版本<1.0-rc91 | 合规 | runc-escape | docker,containerd |
| containerd-shim socket可访问 | 侦察 | containerd-shim-escape | containerd |
| K8s SA token可读取 | 侦察 | k8s-sa-exploit | k8s |
| K8s RBAC过宽 | 合规G_8 | k8s-rbac-abuse | k8s |
| K8s匿名访问enabled | 合规G_1 | k8s-anonymous-access | k8s |
| K8s pods/exec权限 | 合规G_8/recon | k8s-exec-abuse | k8s |
| K8s pods/portforward或proxy权限 | 合规G_8/recon | k8s-proxy-abuse | k8s |
| K8s ephemeralcontainers权限 | 合规G_8/recon | k8s-ephemeral-container | k8s |
| containerd ctr可用+socket可访问 | 侦察/合规 | ctr-tool-abuse | containerd |
| Docker TCP端口暴露 | 合规Docker G_2 | docker-api-auth | docker |
| 容器网络无NetworkPolicy | 合规G_6 | lateral-move | k8s |
| 云元数据可访问 | 侦察 | cloud-metadata | k8s |
| DNS可解析外部 | 侦察 | dns-exfil | k8s |
| K8s混合集群Windows节点+ALPN协商 | 侦察 | ntfs-alpn | k8s |
| K8s Secret明文环境变量 | 侦察/合规 | secret-exfil, env-credential-leak | k8s |
| 环境变量含凭证 | 侦察 | env-credential-leak | k8s,docker,containerd |
| 镜像历史含Secret | 侦察 | image-layer-secret | docker,containerd |
| 无资源限制 | 合规G_7 | resource-abuse | k8s |
| 特权容器+无pid限制 | 合规G_7 | fork-bomb | k8s,docker |
| 镜像tag非固定 | 合规 | image-tag-mutation | k8s,docker |
| Registry无认证 | 合规 | registry-poison | k8s,docker |
| Webhook可访问 | 侦察 | webhook-backdoor | k8s |
| CronJob可创建 | 合规G_8 | cronjob-persist | k8s |
| Docker Volume可写 | 侦察 | docker-volume-persist | docker |
| K8s-7.1.1 privileged=true(独立模式) | 合规G_7 | privileged-container-escape | k8s,docker |
| K8s hostPID=true或hostIPC=true | 合规G_7 | hostpid-hostipc-escape | k8s |
| K8s hostNetwork=true | 合规G_7 | hostnetwork-abuse | k8s |
| K8s shareProcessNamespace=true | 侦察 | shareprocessns-abuse | k8s |
| K8s unsafeSysctls配置 | 合规G_7 | sysctl-abuse | k8s |
| Kubelet 10250匿名可访问+--anonymous-auth=true | 合规G_4 | kubelet-api-abuse | k8s |
| etcd 2379未启用client-cert-auth | 合规G_1 | etcd-unauth-access | k8s |
| /etc/kubernetes/pki/etcd/证书可读 | 侦察 | etcd-cert-theft | k8s |
| certificatesigningrequests/create权限 | 合规G_8/recon | csr-api-abuse | k8s |
| 节点kubelet客户端证书可用 | 侦察 | node-cluster-escalation | k8s |
| serviceaccounts/token create权限 | 合规G_8/recon | tokenrequest-api-abuse | k8s |
| APIService注册权限 | 合规G_8/recon | aggregated-apiserver-abuse | k8s |
| CNI未启用网络隔离/NetworkPolicy漏洞 | 侦察/合规G_6 | networkpolicy-bypass | k8s |
| pods/portforward权限(独立模式) | 合规G_8/recon | kubectl-portforward-abuse | k8s |
| ~/.aws/credentials存在或IMDSv1 | 侦察 | cloud-provider-credential-theft | k8s,docker |
| ConfigMap含明文敏感数据 | 侦察/合规 | configmap-data-exposure | k8s |
| etcd未启用静态加密 | 合规G_6 | etcd-data-exposure | k8s |
| mutatingwebhookconfigurations/create权限 | 合规G_8/recon | mutating-webhook-persist | k8s |
| daemonsets/create权限 | 合规G_8/recon | daemonset-persist | k8s |
| deployments/update权限 | 合规G_8/recon | deployment-image-override | k8s |

## 平台过滤规则

每个攻击模式 SKILL.md 文件头包含 `platforms` 字段，指定该模式适用的容器运行时/编排平台：

```yaml
platforms: [k8s, docker, containerd]
```

**读取过滤逻辑**：

| scope 取值 | 过滤行为 |
|-----------|---------|
| `k8s` | 仅加载 `platforms` 含 `k8s` 的模式 |
| `docker` | 仅加载 `platforms` 含 `docker` 的模式 |
| `containerd` | 仅加载 `platforms` 含 `containerd` 的模式 |
| `all` | 加载所有模式 |

1. Phase 1 识别目标平台（`platforms` 字段取值：`k8s` / `docker` / `containerd`）
2. 读取攻击面目录时，**仅加载** `platforms` 包含当前目标平台的模式文件
3. 示例：目标为纯 Docker 环境时，过滤掉 `platforms: [k8s]` 的模式（如 `k8s-sa-exploit`、`k8s-rbac-abuse`、`hostpath-mount`）
4. `_learned/` 子目录中的模式同样遵循平台过滤规则

## 模式文件 frontmatter 概要

| 模式名 | platforms | mapped_attack_surfaces | mapped_compliance_families | destructive | max_verification_level |
|--------|-----------|----------------------|--------------------------|-------------|----------------------|
| socket-escape | k8s,docker | AS-1 | G_7 | false | L2 |
| cgroup-escape | k8s,docker | AS-1 | G_7 | false | L3 |
| procfs-escape | k8s,docker | AS-1 | G_7 | false | L3 |
| runc-escape | docker,containerd | AS-1 | G_7 | false | L3 |
| hostpath-mount | k8s | AS-1 | G_7 | false | L1 |
| capability-privesc | k8s,docker,containerd | AS-1 | G_7 | false | L2 |
| containerd-shim-escape | containerd | AS-1 | G_7 | false | L3 |
| k8s-sa-exploit | k8s | AS-2 | G_1,G_8 | false | L2 |
| k8s-rbac-abuse | k8s | AS-2 | G_8 | false | L2 |
| k8s-anonymous-access | k8s | AS-2 | G_1 | false | L0 |
| docker-api-auth | docker | AS-2 | G_2 | false | L1 |
| k8s-exec-abuse | k8s | AS-2.5 | RBAC配置, exec权限 | false | L2 |
| ctr-tool-abuse | containerd | AS-2.4 | containerd配置, 文件权限 | false | L2 |
| k8s-ephemeral-container | k8s | AS-2.6 | Pod安全, RBAC配置 | false | L2 |
| lateral-move | k8s | AS-3 | G_6 | false | L2 |
| cloud-metadata | k8s | AS-3 | G_6 | false | L2 |
| dns-exfil | k8s | AS-3 | G_6 | false | L2 |
| ntfs-alpn | k8s | AS-3 | G_6 | false | L2 |
| k8s-proxy-abuse | k8s | AS-3.5 | RBAC配置, 网络策略 | false | L2 |
| secret-exfil | k8s | AS-4 | G_6 | false | L2 |
| env-credential-leak | k8s,docker,containerd | AS-4 | G_6 | false | L2 |
| image-layer-secret | docker,containerd | AS-4 | G_6 | false | L2 |
| resource-abuse | k8s | AS-5 | G_7 | false | L3 |
| fork-bomb | k8s,docker | AS-5 | G_7 | true | L3 |
| image-tag-mutation | k8s,docker | AS-6 | G_5 | false | L2 |
| registry-poison | k8s,docker | AS-6 | G_5 | false | L2 |
| webhook-backdoor | k8s | AS-7 | G_8 | false | L2 |
| cronjob-persist | k8s | AS-7 | G_8 | false | L2 |
| docker-volume-persist | docker | AS-7 | G_7 | false | L2 |
| privileged-container-escape | k8s,docker | AS-1.8 | 特权容器, Pod安全 | false | L2 |
| hostpid-hostipc-escape | k8s | AS-1.9 | Pod安全, 命名空间共享 | false | L2 |
| hostnetwork-abuse | k8s,docker | AS-1.10 | Pod安全, 网络隔离 | false | L2 |
| shareprocessns-abuse | k8s | AS-1.11 | Pod安全 | false | L2 |
| sysctl-abuse | k8s | AS-1.12 | Pod安全, sysctl | false | L2 |
| kubelet-api-abuse | k8s | AS-2.7 | Kubelet认证, API暴露 | false | L2 |
| etcd-unauth-access | k8s | AS-2.8 | etcd安全, TLS配置 | false | L2 |
| etcd-cert-theft | k8s | AS-2.9, AS-4.4 | etcd安全, 文件权限 | false | L2 |
| csr-api-abuse | k8s | AS-2.10 | RBAC配置, 证书管理 | false | L2 |
| node-cluster-escalation | k8s | AS-2.11 | 节点安全, RBAC | false | L2 |
| tokenrequest-api-abuse | k8s | AS-2.12 | RBAC, SA token | false | L2 |
| aggregated-apiserver-abuse | k8s | AS-2.13 | APIService, 准入控制 | false | L2 |
| networkpolicy-bypass | k8s | AS-3.6 | 网络策略 | false | L2 |
| kubectl-portforward-abuse | k8s | AS-3.7 | RBAC, 端口转发 | false | L2 |
| cloud-provider-credential-theft | k8s,docker | AS-4.4 | 云凭证, 文件权限 | false | L2 |
| configmap-data-exposure | k8s | AS-4.5 | ConfigMap, 数据保护 | false | L2 |
| etcd-data-exposure | k8s | AS-4.6 | etcd加密, 数据保护 | false | L2 |
| mutating-webhook-persist | k8s | AS-7.4 | Webhook配置, 准入控制 | false | L2 |
| daemonset-persist | k8s | AS-7.5 | DaemonSet, 持久化 | false | L2 |
| deployment-image-override | k8s | AS-7.6 | Deployment, 镜像管理 | false | L2 |

## _learned/ 目录说明

新学习的攻击模式存放在 `_learned/` 子目录中。这些模式由 Phase 9 晋升引擎从渗透会话中自动发现：

1. **初始状态**：新发现的攻击模式以 `source: learned` + `confidence: medium` 写入 `_learned/`
2. **晋升门槛**：差分证明充分 + 探测可复现 + 无法匹配现有模式 + 跨会话命中≥2次 → 标记可晋升
3. **晋升流程**：用户审批通过后，模式从 `_learned/` 移到对应攻击面正式目录，`confidence` 升级为 `high`
4. **自净规则**：`hit_count ≥ 5` 且跨 `≥ 2` 环境晋升为 high；连续 5 次未命中降为 medium；连续 10 次降为 stale；连续 15 次问用户是否归档到 `_archived/`
5. **索引同步**：晋升或归档后，须同步更新本 `_index.md` 各表格
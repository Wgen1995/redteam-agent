# 攻击面模型

本文档定义容器与 Kubernetes 渗透测试的 7 大攻击面详细模型，作为攻击模式库和 LLM 推理的参考框架。

---

## AS-1 逃逸（escape）

### 攻击面 ID

`AS-1`

### 名称

容器逃逸（Container Escape）

### 描述

突破容器隔离边界，从容器内部获取宿操作系统级别的访问权限。这是容器安全中最高优先级的攻击面，因为逃逸成功意味着攻击者获得了宿主机控制权，可以影响同一节点上的所有容器。

### 典型攻击路径

1. **Docker Socket 逃逸**：容器内挂载了 `/var/run/docker.sock`，攻击者可通过 Docker API 创建特权容器逃逸到宿主机
2. **cgroup 逃逸**：利用 cgroup release_agent 或 notify_on_release 机制，在特权容器中写宿主机 cgroup 文件执行命令
3. **procfs 逃逸**：通过 `/proc/sys` 内核参数或 `/proc/sysrq-trigger` 在特权容器中触发内核操作逃逸
4. **hostPath 挂载逃逸**：Pod 配置中将宿主机敏感路径（如 `/`、`/etc`、`/var/run/docker.sock`）通过 hostPath 挂载到容器
5. **Capability 提权逃逸**：容器被赋予了危险 Linux capabilities（如 `CAP_SYS_ADMIN`、`CAP_SYS_PTRACE`），利用这些权限突破隔离

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-1.1 | escape/socket-escape/SKILL.md | k8s, docker |
| AS-1.2 | escape/cgroup-escape/SKILL.md | k8s, docker |
| AS-1.3 | escape/procfs-escape/SKILL.md | k8s, docker, containerd |
| AS-1.4 | escape/runc-escape/SKILL.md | docker, containerd |
| AS-1.5 | escape/hostpath-mount/SKILL.md | k8s |
| AS-1.6 | escape/capability-privesc/SKILL.md | k8s, docker, containerd |
| AS-1.7 | escape/containerd-shim-escape/SKILL.md | containerd |

### CIS Benchmark 关联组

**Kubernetes**：G_5（Kubelet）, G_5_1（Kubelet 文件权限）, G_5_2（Kubelet 认证）, G_5_6（Kubelet 系统配置）, G_7_1（Pod 启动安全 — 特权容器、危险挂载、Capabilities）

**Docker**：G_1（运行环境配置）, G_2（守护进程参数）, G_3（文件权限）, G_5（容器运行 — 特权模式、_capabilities、挂载）

**Containerd**：G_1（运行环境配置）, G_2（守护进程参数）, G_3（文件权限）, G_5（容器运行）

---

## AS-2 认证授权（auth）

### 攻击面 ID

`AS-2`

### 名称

认证授权（Authentication & Authorization）

### 描述

利用身份认证或授权机制的缺陷，获取未授权访问或提升权限。在 Kubernetes 中主要涉及 ServiceAccount Token 滥用、RBAC 配置缺陷和匿名访问；在 Docker 中主要涉及 Docker API 认证缺陷。

### 典型攻击路径

1. **ServiceAccount Token 滥用**：Pod 自动挂载的 ServiceAccount Token 可被攻击者利用，通过 API Server 执行集群操作
2. **RBAC 权限提升**：过于宽松的 RBAC 配置（如 `cluster-admin` 绑定到普通用户、`*` 权限）允许权限提升
3. **匿名访问**：API Server 或 Kubelet 的匿名认证配置开启，允许未认证访问
4. **Docker API 未授权访问**：Docker daemon 监听 TCP 端口且未配置 TLS 认证，攻击者可直接调用 Docker API

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-2.1 | auth/k8s-sa-exploit/SKILL.md | k8s |
| AS-2.2 | auth/k8s-rbac-abuse/SKILL.md | k8s |
| AS-2.3 | auth/k8s-anonymous-access/SKILL.md | k8s |
| AS-2.4 | auth/docker-api-auth/SKILL.md | docker |

### CIS Benchmark 关联组

**Kubernetes**：G_1_1（API Server 文件权限）, G_1_2（API Server 认证 — 23条规则）, G_2_3（Etcd 安全配置）, G_4_2（Kubelet 授权配置）, G_5_2（Kubelet 认证）, G_7_2（Pod 认证 — SA Token）, G_8_2（RBAC 权限）

**Docker**：G_2（守护进程参数 — TLS 配置）, G_7（集群配置 — Swarm/TLS 认证）

**Containerd**：G_2（守护进程参数 — 认证配置）

---

## AS-3 网络（network）

### 攻击面 ID

`AS-3`

### 名称

网络攻击（Network Attack）

### 描述

利用网络配置缺陷进行横向移动、数据外泄和云元数据窃取。容器网络隔离不当是微服务架构中的常见问题。

### 典型攻击路径

1. **容器间横向移动**：无 NetworkPolicy 的命名空间允许 Pod 间无限制通信，攻击者可直接访问同集群其他服务
2. **云实例元数据窃取**：容器内可访问云提供商元数据 API（如 AWS IMDS `169.254.169.254`），获取临时凭证和实例信息
3. **DNS 数据外泄**：利用 DNS 隧道将数据通过 DNS 查询外泄到攻击者控制的域名服务器
4. **NTFS ALPN 协议缺陷**：利用 Kubernetes 中 NTFS ALPN 协议相关的网络漏洞

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-3.1 | network/lateral-move/SKILL.md | k8s, docker |
| AS-3.2 | network/ntfs-alpn/SKILL.md | k8s |
| AS-3.3 | network/cloud-metadata/SKILL.md | k8s, docker |
| AS-3.4 | network/dns-exfil/SKILL.md | k8s, docker |

### CIS Benchmark 关联组

**Kubernetes**：G_1_4（API Server 防泄露 — 网络层）, G_6（Kube-proxy — 网络代理配置）, G_8_1（CNI 文件权限）, G_8_4（命名空间/网络策略 — NetworkPolicy 配置）

**Docker**：G_2（守护进程参数 — 网络配置）, G_5（容器运行 — 网络模式）, G_7（集群配置 — 集群网络）

**Containerd**：无直接关联（containerd 不直接管理网络）

---

## AS-4 数据泄露（data）

### 攻击面 ID

`AS-4`

### 名称

数据泄露（Data Leakage）

### 描述

敏感数据（Secret、凭证、密钥）的未授权泄露。包括 Kubernetes Secret 外泄、环境变量中的硬编码凭证、以及容器镜像层中残留的敏感信息。

### 典型攻击路径

1. **Kubernetes Secret 读取**：通过 RBAC 权限提升或 etcd 未加密访问读取 Secret 内容
2. **环境变量凭证泄露**：容器镜像或 Pod 清单中将数据库密码、API Key 等凭证以环境变量传递，可被同一 Pod 内进程读取
3. **镜像层密钥残留**：Dockerfile 中 COPY 密钥文件后未清理、构建时 SECRET 未使用 multi-stage build，导致密钥残留在镜像层中
4. **etcd 未加密数据泄露**：etcd 存储未加密的 Secret 数据，可直接通过 etcd API 读取

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-4.1 | data/secret-exfil/SKILL.md | k8s, docker |
| AS-4.2 | data/env-credential-leak/SKILL.md | k8s, docker, containerd |
| AS-4.3 | data/image-layer-secret/SKILL.md | docker, containerd |

### CIS Benchmark 关联组

**Kubernetes**：G_1_4（API Server 防泄露）, G_1_5（API Server 日志 — 审计可追溯性）, G_1_6（API Server SSL — 数据传输加密）, G_2_2（CM 防泄露）, G_3_2（Scheduler 防泄露）, G_4_3（Etcd SSL）, G_5_3（Kubelet 防泄露）, G_8_3（Secret 防泄露 — 加密和访问控制）

**Docker**：G_4（镜像构建 — 敏感信息残留）, G_5（容器运行 — env/secret 挂载）, G_6（容器运维 — 数据保护）

**Containerd**：G_4（镜像构建 — 敏感信息残留）, G_5（容器运行 — 环境变量泄露）

---

## AS-5 拒绝服务（dos）

### 攻击面 ID

`AS-5`

### 名称

拒绝服务（Denial of Service）

### 描述

容器资源滥用导致宿主机或同节点其他容器服务不可用。包括无资源限制的容器消耗宿主机资源、以及特权容器执行 fork bomb 等破坏性操作。

### 典型攻击路径

1. **资源无限制滥用**：容器未设置 CPU/内存限制（resources.limits 为空），可无限消耗宿主机资源导致其他 Pod 被驱逐
2. **Fork bomb**：特权容器或无 PIDs 限制的容器内执行 `:(){ :|:& };:` 形成进程风暴，耗尽宿主机 PID 和 CPU 资源
3. **磁盘空间耗尽**：容器写入大量无限制数据到共享存储，导致节点磁盘满
4. **网络带宽滥用**：无网络限制的容器发起大量网络请求，影响同节点其他服务

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-5.1 | dos/resource-abuse/SKILL.md | k8s, docker |
| AS-5.2 | dos/fork-bomb/SKILL.md | k8s, docker, containerd |

### CIS Benchmark 关联组

**Kubernetes**：G_1_3（API Server 防 DOS）, G_5_4（Kubelet 防 DOS — 资源限制）, G_7_1（Pod 启动安全 — 资源限制配置）

**Docker**：G_5（容器运行 — 资源限制相关规则）

**Containerd**：G_5（容器运行 — 资源限制相关规则）

---

## AS-6 供应链（supply）

### 攻击面 ID

`AS-6`

### 名称

供应链攻击（Supply Chain Attack）

### 描述

利用软件供应链信任链的缺陷进行攻击。包括镜像标签篡改、镜像仓库投毒、依赖混淆等，通过被篡改的镜像在运行时执行恶意代码。

### 典型攻击路径

1. **镜像标签漂移**：使用 `:latest` 标签或不固定摘要的镜像，镜像可能被更新为包含漏洞或恶意代码的版本
2. **镜像仓库投毒**：攻击者通过中间人攻击、依赖混淆或供应链注入，将恶意镜像推送到受信任的仓库
3. **基础镜像漏洞**：基础镜像包含已知漏洞（如 Alpine 旧版本），攻击者利用已有漏洞获取初始访问

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-6.1 | supply/image-tag-mutation/SKILL.md | k8s, docker |
| AS-6.2 | supply/registry-poison/SKILL.md | k8s, docker |

### CIS Benchmark 关联组

**Kubernetes**：无直接 CIS 规则（镜像供应链安全不在 CIS Benchmark 范围内，属于运营最佳实践）

**Docker**：G_4（镜像构建 — 镜像安全相关规则）

**Containerd**：G_4（镜像构建 — 镜像安全相关规则）

---

## AS-7 持久化（persist）

### 攻击面 ID

`AS-7`

### 名称

持久化攻击（Persistence Attack）

### 描述

在容器环境中建立持久访问通道，使得攻击者在初始入侵后能持续访问目标环境。包括 K8s Webhook 后门、CronJob 定时执行、Docker Volume 持久化等。

### 典型攻击路径

1. **Webhook 后门**：创建恶意的 ValidatingWebhookConfiguration 或 MutatingWebhookConfiguration，拦截所有 API 请求并记录凭证或修改请求
2. **CronJob 定时持久化**：创建 K8s CronJob 定时执行恶意命令，如定期获取 ServiceAccount Token 并发送到外部服务器
3. **Docker Volume 持久化后门**：通过 Docker Volume 在宿主机上持久存储后门脚本，容器重启后仍可执行
4. **ConfigMap/Secret 持久化**：将恶意配置写入 ConfigMap 或 Secret，影响使用这些配置的所有 Pod

### 模式列表

| 子 ID | 模式文件 | 适用平台 |
|-------|---------|---------|
| AS-7.1 | persist/webhook-backdoor/SKILL.md | k8s |
| AS-7.2 | persist/cronjob-persist/SKILL.md | k8s |
| AS-7.3 | persist/docker-volume-persist/SKILL.md | docker |

### CIS Benchmark 关联组

**Kubernetes**：G_1_2（API Server 认证 — webhook 准入控制）, G_8_2（RBAC 权限 — 创建 webhook 的权限控制）, G_8_3（Secret 防泄露 — Secret 完整性）

**Docker**：无直接 CIS 规则

**Containerd**：无直接 CIS 规则

---

## 攻击面覆盖率矩阵

以下矩阵显示每个攻击面对应平台的模式覆盖情况：

```
                k8s      docker   containerd
AS-1 逃逸       5 模式    3 模式    3 模式
AS-2 认证授权    3 模式    1 模式    0 模式
AS-3 网络       4 模式    2 模式    0 模式
AS-4 数据泄露    2 模式    2 模式    2 模式
AS-5 拒绝服务    2 模式    1 模式    1 模式
AS-6 供应链      2 模式    2 模式    0 模式
AS-7 持久化     2 模式    1 模式    0 模式
```

每个攻击面的 `_learned/` 子目录用于存放 LLM 推理晋升的模式，来源标识为 `learned`。Phase 4b 推理发现和 Phase 9 进化晋升的模式存放在此。
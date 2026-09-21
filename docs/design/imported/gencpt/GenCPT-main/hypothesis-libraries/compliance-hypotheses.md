# 合规假设库（Compliance Hypotheses）

> 来源：设计文档 5.3 节"三库联动"
> 作用：把合规违规映射到攻击前置条件，驱动 Phase 4a 条件触发读取

## 假设卡片格式

每张卡片包含以下字段：

| 字段 | 说明 |
|------|------|
| 假设ID | `CHK-CAND-NNN`，连续编号 |
| 违规族 | 1-N 条合规规则 ID，用 `+` 表示叠加 |
| 映射的攻击模式 | `攻击面/模式slug`，如 `escape/socket-escape` |
| 严重等级 | Critical / High / Medium / Low |
| 前置条件示例 | 满足该假设所需的环境证据 |
| 合规规则编号 | CIS 规则编号 |
| 攻击面关联 | AS-{N} 攻击面编号 |

---

## 假设卡片

### CHK-CAND-001：K8s 特权容器→容器逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-001 |
| 违规族 | K8s-7.1.1(特权容器) |
| 映射的攻击模式 | `escape/capability-privesc`, `escape/cgroup-escape`, `escape/hostpath-mount` |
| 严重等级 | Critical |
| 前置条件示例 | `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].securityContext.privileged}'` 返回 true；容器内 `cat /proc/1/status | grep CapEff` 为 `0000003fffffffff` |
| 合规规则编号 | K8s-7.1.1 |
| 攻击面关联 | AS-1 |

### CHK-CAND-002：docker.sock 挂载→socket 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-002 |
| 违规族 | K8s-7.1.1(特权容器) + docker.sock 挂载 |
| 映射的攻击模式 | `escape/socket-escape` |
| 严重等级 | Critical |
| 前置条件示例 | 容器内 `ls -la /var/run/docker.sock` 存在且可读写；或 `mount | grep docker` 显示 docker.sock 挂载 |
| 合规规则编号 | K8s-7.1.1 |
| 攻击面关联 | AS-1 |

### CHK-CAND-003：hostPath 挂载宿主机根目录→文件系统逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-003 |
| 违规族 | K8s-7.1.2(hostPath 卷) |
| 映射的攻击模式 | `escape/hostpath-mount` |
| 严重等级 | Critical |
| 前置条件示例 | Pod spec 中 `volumes[*].hostPath.path` 指向 `/`、`/etc`、`/var/run/docker.sock` 等敏感路径 |
| 合规规则编号 | K8s-7.1.2 |
| 攻击面关联 | AS-1 |

### CHK-CAND-004：CAP_SYS_ADMIN→权限提升逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-004 |
| 违规族 | K8s-7.1.6(危险 Linux capabilities) + K8s-7.1.12(未 drop ALL) |
| 映射的攻击模式 | `escape/capability-privesc` |
| 严重等级 | Critical |
| 前置条件示例 | 容器 securityContext.capabilities.add 包含 `SYS_ADMIN`、`SYS_PTRACE`、`SYS_MODULE`、`NET_ADMIN` 等；容器内 `cat /proc/self/status | grep Cap` 含上述能力 |
| 合规规则编号 | K8s-7.1.6, K8s-7.1.12 |
| 攻击面关联 | AS-1 |

### CHK-CAND-005：K8s 匿名访问 enabled→未授权 API 访问

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-005 |
| 违规族 | K8s-1.2.1(API Server 匿名认证) |
| 映射的攻击模式 | `auth/k8s-anonymous-access` |
| 严重等级 | Critical |
| 前置条件示例 | `ps -ef | grep kube-apiserver | grep -- '--anonymous-auth=true'` 或 `--anonymous-auth` 未设置（默认 true）；`curl -k https://<api-server>:6443/api` 无需认证返回 200 |
| 合规规则编号 | K8s-1.2.1 |
| 攻击面关联 | AS-2 |

### CHK-CAND-006：RBAC cluster-admin 过宽→权限提升

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-006 |
| 违规族 | K8s-8.2.1(cluster-admin 过多) + K8s-8.2.2(通配符权限) |
| 映射的攻击模式 | `auth/k8s-rbac-abuse` |
| 严重等级 | Critical |
| 前置条件示例 | `kubectl get clusterrolebinding -o json | jq '.items[] | select(.roleRef.name=="cluster-admin")'` 返回非系统绑定；或自定义 ClusterRole 使用 `verbs: ["*"]` |
| 合规规则编号 | K8s-8.2.1, K8s-8.2.2 |
| 攻击面关联 | AS-2 |

### CHK-CAND-007：ServiceAccount token 可读→SA 利用

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-007 |
| 违规族 | K8s-7.1.14(SA token 自动挂载) + K8s-8.2.5(default SA token 未禁用) |
| 映射的攻击模式 | `auth/k8s-sa-exploit` |
| 严重等级 | High |
| 前置条件示例 | Pod `automountServiceAccountToken` 未显式设为 false；default SA 仍有 token 挂载；容器内 `cat /var/run/secrets/kubernetes.io/serviceaccount/token` 可读取 |
| 合规规则编号 | K8s-7.1.14, K8s-8.2.4, K8s-8.2.5 |
| 攻击面关联 | AS-2 |

### CHK-CAND-008：无 NetworkPolicy→横向移动

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-008 |
| 违规族 | K8s-8.2.10(命名空间无 NetworkPolicy) |
| 映射的攻击模式 | `network/lateral-move` |
| 严重等级 | High |
| 前置条件示例 | `kubectl get networkpolicy -A` 返回空或命名空间缺失 NetworkPolicy；Pod 间全互通 |
| 合规规则编号 | K8s-8.2.10 |
| 攻击面关联 | AS-3 |

### CHK-CAND-009：Secret 明文环境变量→Secret 泄露

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-009 |
| 违规族 | K8s-8.3.1(Secret 以环境变量挂载) |
| 映射的攻击模式 | `data/secret-exfil`, `data/env-credential-leak` |
| 严重等级 | High |
| 前置条件示例 | Pod spec 中 `env[*].valueFrom.secretKeyRef` 存在；容器内 `env | grep -iE 'password|secret|token|key'` 返回明文 |
| 合规规则编号 | K8s-8.3.1（G_8_3） |
| 攻击面关联 | AS-4 |

### CHK-CAND-010：无资源限制→DoS

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-010 |
| 违规族 | K8s-8.2.9(ResourceQuota 缺失) |
| 映射的攻击模式 | `dos/resource-abuse` |
| 严重等级 | Medium |
| 前置条件示例 | `kubectl get resourcequota -A` 无结果或命名空间缺少配额；Pod 无 resources.limits |
| 合规规则编号 | K8s-8.2.9 |
| 攻击面关联 | AS-5 |

### CHK-CAND-011：Docker daemon TCP 暴露→Docker API 未认证

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-011 |
| 违规族 | Docker-2(daemon 监听 TCP) |
| 映射的攻击模式 | `auth/docker-api-auth` |
| 严重等级 | Critical |
| 前置条件示例 | `ps -ef | grep dockerd | grep -E '-H tcp://|0.0.0.0'` 显示监听 TCP；`curl http://<host>:2375/info` 返回 Docker 信息 |
| 合规规则编号 | Docker-G_2（daemon 参数组） |
| 攻击面关联 | AS-2 |

### CHK-CAND-012：无镜像签名验证→供应链攻击

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-012 |
| 违规族 | Docker-51(DOCKER_CONTENT_TRUST 未启用) |
| 映射的攻击模式 | `supply/image-tag-mutation`, `supply/registry-poison` |
| 严重等级 | Medium |
| 前置条件示例 | `echo $DOCKER_CONTENT_TRUST` 为空或 0；镜像使用 `latest` 标签 |
| 合规规则编号 | Docker-51 |
| 攻击面关联 | AS-6 |

### CHK-CAND-013：etcd 无 TLS→etcd 数据窃取

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-013 |
| 违规族 | K8s etcd 配置（G_2 etcd 组：认证/SSL 缺失） |
| 映射的攻击模式 | `data/secret-exfil` |
| 严重等级 | High |
| 前置条件示例 | `ps -ef | grep etcd | grep -v grep | grep -oE '--client-cert-auth|--cert-file|--key-file'` 缺失；`etcdctl endpoint health --insecure-skip-tls-verify` 可连接 |
| 合规规则编号 | K8s etcd 组（G_2_2, G_2_4） |
| 攻击面关联 | AS-4 |

### CHK-CAND-014：Kubelet 匿名访问→容器控制

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-014 |
| 违规族 | K8s-4.1,4.2(Kubelet 认证/授权配置) |
| 映射的攻击模式 | `auth/k8s-anonymous-access` |
| 严重等级 | Critical |
| 前置条件示例 | `ps -ef | grep kubelet | grep -- '--anonymous-auth=true'` 或未设置（默认 true）；`curl -k https://<node>:10250/pods` 返回 200 |
| 合规规则编号 | K8s G_4_kubelet 组 |
| 攻击面关联 | AS-2 |

### CHK-CAND-015：无审计日志→攻击追踪缺失

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-015 |
| 违规族 | K8s-1.5(API Server 审计日志未配置) |
| 映射的攻击模式 | —（防御缺失，非直接攻击路径，但增加所有入侵的持续时间和隐蔽性） |
| 严重等级 | Medium |
| 前置条件示例 | `ps -ef | grep kube-apiserver | grep -oE '--audit-log-path|--audit-log-maxage'` 缺失；`ls /var/log/kubernetes/audit*` 无文件 |
| 合规规则编号 | K8s G_1_5 |
| 攻击面关联 | AS-2（辅助） |

### CHK-CAND-016：镜像使用 latest 标签→标签篡改

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-016 |
| 违规族 | K8s 镜像配置 + Docker-51(内容信任) |
| 映射的攻击模式 | `supply/image-tag-mutation` |
| 严重等级 | Medium |
| 前置条件示例 | `kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | grep ':latest'` 或无摘要；`docker images | grep latest` |
| 合规规则编号 | Docker-51 |
| 攻击面关联 | AS-6 |

### CHK-CAND-017：Webhook 未限制→Webhook 后门

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-017 |
| 违规族 | K8s-1.2(准入插件配置不当) |
| 映射的攻击模式 | `persist/webhook-backdoor` |
| 严重等级 | High |
| 前置条件示例 | `kubectl get validatingwebhookconfiguration,mutatingwebhookconfiguration -A` 存在指向公网或可疑端点的 Webhook；Webhook 无 CABundle 或使用自签证书 |
| 合规规则编号 | K8s-1.2.x（准入控制相关） |
| 攻击面关联 | AS-7 |

### CHK-CAND-018：CronJob 可创建→持久化

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-018 |
| 违规族 | K8s-8.2.2(通配符权限含 cronjobs) + K8s-8.2.6(SA 权限过宽) |
| 映射的攻击模式 | `persist/cronjob-persist` |
| 严重等级 | High |
| 前置条件示例 | `kubectl auth can-i create cronjobs --as=system:serviceaccount:<ns>:<sa>` 返回 yes；当前 SA 拥有 `batch/cronjobs` 创建权限 |
| 合规规则编号 | K8s-8.2.2, K8s-8.2.6 |
| 攻击面关联 | AS-7 |

### CHK-CAND-019：共享 PID namespace→进程注入

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-019 |
| 违规族 | K8s-7.1.3(hostPID) + Docker-39(host network namespace) |
| 映射的攻击模式 | `escape/capability-privesc` |
| 严重等级 | High |
| 前置条件示例 | Pod spec `hostPID: true`；容器内 `ps aux` 可见宿主机进程 |
| 合规规则编号 | K8s-7.1.3 |
| 攻击面关联 | AS-1 |

### CHK-CAND-020：无 PodSecurityPolicy/PSS→Pod 安全缺失

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-020 |
| 违规族 | K8s-7.1.13(PodSecurityAdmission 未 enforce restricted) |
| 映射的攻击模式 | `escape/capability-privesc`, `escape/hostpath-mount`, `escape/cgroup-escape` |
| 严重等级 | High |
| 前置条件示例 | `kubectl get namespaces --show-labels | grep pod-security.kubernetes.io/enforce=restricted` 无结果或仅有 baseline/privileged |
| 合规规则编号 | K8s-7.1.13 |
| 攻击面关联 | AS-1 |

### CHK-CAND-021：Docker 特权容器+无 Seccomp→逃逸放大

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-021 |
| 违规族 | Docker-42(特权模式) + Docker-44(Seccomp unconfined) |
| 映射的攻击模式 | `escape/socket-escape`, `escape/cgroup-escape` |
| 严重等级 | Critical |
| 前置条件示例 | `docker inspect --format '{{.HostConfig.Privileged}}' <cid>` 返回 true 且 `SecurityOpt` 不含 seccomp；容器拥有全部 Linux capabilities |
| 合规规则编号 | Docker-42, Docker-44 |
| 攻击面关联 | AS-1 |

### CHK-CAND-022：Docker 容器无资源限制→DoS

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-022 |
| 违规族 | Docker-36(内存限制) + Docker-37(CPU 优先级) + Docker-41(PID 限制) |
| 映射的攻击模式 | `dos/resource-abuse`, `dos/fork-bomb` |
| 严重等级 | Medium |
| 前置条件示例 | `docker inspect --format '{{.HostConfig.Memory}}' <cid>` 返回 0；PidsLimit 为 0 或 -1 |
| 合规规则编号 | Docker-36, Docker-41 |
| 攻击面关联 | AS-5 |

### CHK-CAND-023：Docker 容器挂载宿主机敏感目录→文件系统逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-023 |
| 违规族 | Docker-50(敏感目录读写挂载) |
| 映射的攻击模式 | `escape/hostpath-mount` |
| 严重等级 | Critical |
| 前置条件示例 | `docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.RW}}){{println}}{{end}}' <cid>` 显示 `/etc`、`/var/run/docker.sock`、`/` 等以 rw 模式挂载 |
| 合规规则编号 | Docker-50 |
| 攻击面关联 | AS-1 |

### CHK-CAND-024：Docker 容器 hostNetwork→网络逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-024 |
| 违规族 | Docker-39(host 网络模式) + K8s-7.1.5(hostNetwork) |
| 映射的攻击模式 | `network/lateral-move`, `network/cloud-metadata` |
| 严重等级 | High |
| 前置条件示例 | `docker inspect --format '{{.HostConfig.NetworkMode}}' <cid>` 返回 `host`；或 K8s Pod `hostNetwork: true` |
| 合规规则编号 | Docker-39, K8s-7.1.5 |
| 攻击面关联 | AS-3 |

### CHK-CAND-025：K8s impersonate 权限过宽→身份冒用

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-025 |
| 违规族 | K8s-8.2.3(impersonate 权限) |
| 映射的攻击模式 | `auth/k8s-rbac-abuse` |
| 严重等级 | Critical |
| 前置条件示例 | `kubectl get clusterroles -o json | jq '.items[] | select(.rules[]?.resources | index("impersonate"))'` 返回非系统角色 |
| 合规规则编号 | K8s-8.2.3 |
| 攻击面关联 | AS-2 |

### CHK-CAND-026：Docker Volume 可写→持久化后门

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-026 |
| 违规族 | Docker-50(敏感主机挂载) + Docker 日常运维 |
| 映射的攻击模式 | `persist/docker-volume-persist` |
| 严重等级 | Medium |
| 前置条件示例 | Docker volume 挂载到容器且 rw 模式；容器可在 volume 中写入脚本/配置，重启后仍存在 |
| 合规规则编号 | Docker-50 |
| 攻击面关联 | AS-7 |

### CHK-CAND-027：云元数据端点可访问→凭据窃取

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-027 |
| 违规族 | K8s-8.2.10(无 NetworkPolicy 阻断元数据端点) |
| 映射的攻击模式 | `network/cloud-metadata` |
| 严重等级 | High |
| 前置条件示例 | 容器内 `curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/` 返回 200；无 NetworkPolicy 限制出站到 169.254.169.254 |
| 合规规则编号 | K8s-8.2.10 |
| 攻击面关联 | AS-3 |

### CHK-CAND-028：Docker UserNS 未启用→逃逸面增大

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-028 |
| 违规族 | Docker-15(userns-remap 未配置) |
| 映射的攻击模式 | `escape/capability-privesc`, `escape/cgroup-escape` |
| 严重等级 | High |
| 前置条件示例 | `cat /etc/docker/daemon.json` 无 `userns-remap`；容器 root 等于宿主机 root uid=0 |
| 合规规则编号 | Docker-15 |
| 攻击面关联 | AS-1 |

### CHK-CAND-029：runc 版本过旧→runc 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-029 |
| 违规族 | Docker runtime 版本（CVE 相关） |
| 映射的攻击模式 | `escape/runc-escape` |
| 严重等级 | Critical |
| 前置条件示例 | `docker info | grep -i runc` 版本 < 1.0-rc91；或 `runc --version` 显示受 CVE-2019-16884/CVE-2024-21626 影响的版本 |
| 合规规则编号 | Docker G_1（运行环境版本） |
| 攻击面关联 | AS-1 |

### CHK-CAND-030：容器共享 IPC namespace→进程注入

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-030 |
| 违规族 | K8s-7.1.4(hostIPC) |
| 映射的攻击模式 | `escape/capability-privesc` |
| 严重等级 | Medium |
| 前置条件示例 | Pod spec `hostIPC: true`；容器内 `ipcs -m` 可见宿主机共享内存段 |
| 合规规则编号 | K8s-7.1.4 |
| 攻击面关联 | AS-1 |

### CHK-CAND-031：Kubernetes Dashboard 公网暴露→认证绕过

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-031 |
| 违规族 | K8s-8.2.8(Dashboard 暴露公网) |
| 映射的攻击模式 | `auth/k8s-rbac-abuse` |
| 严重等级 | High |
| 前置条件示例 | `kubectl get svc -A | grep dashboard` 显示 LoadBalancer 或 NodePort 类型 |
| 合规规则编号 | K8s-8.2.8 |
| 攻击面关联 | AS-2 |

### CHK-CAND-032：ProcFS 可读写挂载→procfs 逃逸

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-032 |
| 违规族 | 敏感卷挂载 + K8s-7.1.2(hostPath) |
| 映射的攻击模式 | `escape/procfs-escape` |
| 严重等级 | High |
| 前置条件示例 | `/proc` 以读写模式挂载到容器；`mount | grep "proc"` 显示 rw |
| 合规规则编号 | K8s-7.1.2 |
| 攻击面关联 | AS-1 |

### CHK-CAND-033：DNS 可解析外部域名→数据外发

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-033 |
| 违规族 | K8s-8.2.10(无 NetworkPolicy) |
| 映射的攻击模式 | `network/dns-exfil` |
| 严重等级 | Medium |
| 前置条件示例 | 容器内 `nslookup external-domain.com` 解析成功；无 Egress NetworkPolicy 限制 DNS 出站 |
| 合规规则编号 | K8s-8.2.10 |
| 攻击面关联 | AS-3 |

### CHK-CAND-034：Docker 容器无 AppArmor/Seccomp→逃逸面放大

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-034 |
| 违规族 | Docker-34(AppArmor unconfined) + Docker-44(Seccomp unconfined) |
| 映射的攻击模式 | `escape/socket-escape`, `escape/cgroup-escape` |
| 严重等级 | High |
| 前置条件示例 | `docker inspect --format '{{.AppArmorProfile}}' <cid>` 返回空或 unconfined；Seccomp 未配置 |
| 合规规则编号 | Docker-34, Docker-44 |
| 攻击面关联 | AS-1 |

### CHK-CAND-035：镜像层含敏感信息→凭据泄露

| 字段 | 值 |
|------|-----|
| 假设ID | CHK-CAND-035 |
| 违规族 | Docker G_4(镜像构建安全) |
| 映射的攻击模式 | `data/image-layer-secret` |
| 严重等级 | Medium |
| 前置条件示例 | `docker history --no-coin <image>` 显示包含密码/密钥的 ENV 或 COPY 层；`docker save <image> | tar -x` 可提取历史层中的敏感文件 |
| 合规规则编号 | Docker G_4 |
| 攻击面关联 | AS-4 |

### CHK-CAND-036：K8s 匿名访问 enabled→未授权 API 访问

- **违规族**: K8s G_1_2（API Server 认证）
- **映射的攻击模式**: auth/k8s-anonymous-access
- **严重等级**: high
- **前置条件**: `--anonymous-auth=true` 且 API Server 暴露
- **合规规则编号**: K8s-1.2.1
- **攻击面关联**: AS-2

### CHK-CAND-037：RBAC 权限过宽→权限提升

- **违规族**: K8s G_8_2（RBAC 配置）
- **映射的攻击模式**: auth/k8s-rbac-abuse
- **严重等级**: high
- **前置条件**: cluster-admin 绑定过宽或 SA 拥有 pods/exec 权限
- **合规规则编号**: K8s-8.2.x
- **攻击面关联**: AS-2

### CHK-CAND-038：ServiceAccount token 可读→SA 利用

- **违规族**: K8s G_7_1（Pod 安全）+ G_8_1（Secret 管理）
- **映射的攻击模式**: auth/k8s-sa-exploit
- **严重等级**: high
- **前置条件**: automountServiceAccountToken=true 且 SA 有高权限
- **合规规则编号**: K8s-7.1.x
- **攻击面关联**: AS-2

### CHK-CAND-039：containerd-shim socket 可访问→shim 逃逸

- **违规族**: Containerd G_3（文件权限）+ G_5（容器运行时）
- **映射的攻击模式**: escape/containerd-shim-escape
- **严重等级**: medium
- **前置条件**: containerd-shim socket 文件可访问且无权限限制
- **合规规则编号**: Containerd-3.x
- **攻击面关联**: AS-1

### CHK-CAND-040：K8s 混合集群 Windows 节点→NTFS ALPN 攻击

- **违规族**: K8s G_6（Network Policies）+ G_7（Pod 安全）
- **映射的攻击模式**: network/ntfs-alpn
- **严重等级**: low
- **前置条件**: 集群含 Windows 节点且 ALPN 协议协商未限制
- **合规规则编号**: K8s-6.x
- **攻击面关联**: AS-3

---

## K8s 全量补充假设卡片（CHK-CAND-041 起，覆盖 CIS Kubernetes Benchmark v1.8.0 全 134 条规则）

### CHK-CAND-041：API Server/etcd/admin/scheduler 配置文件权限宽松→启动配置篡改

- **违规族**: K8s G_1_1（API Server 文件权限）
- **映射的攻击模式**: —（配置篡改前置条件，非直接攻击路径）
- **严重等级**: low
- **前置条件**: `stat -c %a /etc/kubernetes/manifests/kube-apiserver.yaml` > 640；`admin.conf`、`scheduler.conf` 世界可读
- **合规规则编号**: K8s-1.1.1, K8s-1.1.2, K8s-1.1.3, K8s-1.1.4, K8s-1.1.5, K8s-1.1.6, K8s-1.1.7
- **攻击面关联**: AS-2

### CHK-CAND-042：API Server 匿名认证+Bootstrap Token 认证启用→未授权 API 访问

- **违规族**: K8s G_1_2（API Server 认证）—匿名与 Bootstrap Token
- **映射的攻击模式**: `auth/k8s-anonymous-access`
- **严重等级**: critical
- **前置条件**: `--anonymous-auth=true` 或未设置；`--enable-bootstrap-token-auth=true`；`curl -k https://<api-server>:6443/api` 返回 200
- **合规规则编号**: K8s-1.2.1, K8s-1.2.23
- **攻击面关联**: AS-2

### CHK-CAND-043：API Server 静态 Token 认证文件启用→长期 Token 泄露

- **违规族**: K8s G_1_2（API Server 认证）—静态 Token 文件
- **映射的攻击模式**: `auth/k8s-sa-exploit`, `data/secret-exfil`
- **严重等级**: high
- **前置条件**: `ps -ef | grep kube-apiserver | grep -- '--token-auth-file'` 命中；token 文件世界可读且无轮换
- **合规规则编号**: K8s-1.2.2
- **攻击面关联**: AS-2

### CHK-CAND-044：API Server 授权模式缺失 Node/RBAC/Webhook→越权调用

- **违规族**: K8s G_1_2（API Server 认证）—授权模式
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: `--authorization-mode` 不含 `Node`、`RBAC` 或 `Webhook`；含 `AlwaysAllow`；任意已认证用户可下发特权操作
- **合规规则编号**: K8s-1.2.5, K8s-1.2.6, K8s-1.2.7, K8s-1.2.22
- **攻击面关联**: AS-2

### CHK-CAND-045：API Server 准入插件缺 ServiceAccount/NodeRestriction→准入绕过

- **违规族**: K8s G_1_2（API Server 认证）—准入插件 SA/NodeRestriction
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `persist/webhook-backdoor`
- **严重等级**: high
- **前置条件**: `--enable-admission-plugins` 不含 `ServiceAccount`/`NodeRestriction`；Pod 可冒用任意 SA 或绕过节点限制
- **合规规则编号**: K8s-1.2.9, K8s-1.2.10
- **攻击面关联**: AS-2

### CHK-CAND-046：API Server 准入插件缺 AlwaysPullImages/SecurityContext/PodSecurity/EventRateLimit→逃逸+DoS 放大

- **违规族**: K8s G_1_2（API Server 认证）—准入插件集
- **映射的攻击模式**: `supply/image-tag-mutation`, `escape/capability-privesc`, `dos/resource-abuse`
- **严重等级**: high
- **前置条件**: `--enable-admission-plugins` 不含 `AlwaysPullImages`/`SecurityContextDeny`/`EventRateLimit`/`DenyServiceExternalIPs`；未启 PodSecurityAdmission enforce
- **合规规则编号**: K8s-1.2.3, K8s-1.2.11, K8s-1.2.12, K8s-1.2.21
- **攻击面关联**: AS-2

### CHK-CAND-047：API Server kubelet 连接 HTTPS + kubelet/API Server TLS 证书缺失→通信劫持

- **违规族**: K8s G_1_2（API Server 认证）—kubelet HTTPS 与 TLS 证书
- **映射的攻击模式**: `network/lateral-move`, `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: `--kubelet-https` 未设为 true；`--kubelet-client-certificate`/`--kubelet-client-key`/`--tls-cert-file`/`--tls-private-key-file` 缺失
- **合规规则编号**: K8s-1.2.4, K8s-1.2.8, K8s-1.2.13, K8s-1.2.14, K8s-1.2.19
- **攻击面关联**: AS-3

### CHK-CAND-048：API Server etcd 客户端证书 + CA 缺失→etcd 通信明文

- **违规族**: K8s G_1_2（API Server 认证）—etcd 客户端证书
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: high
- **前置条件**: `--etcd-certfile`/`--etcd-keyfile`/`--etcd-cafile` 缺失；API Server↔etcd 流量无 mTLS
- **合规规则编号**: K8s-1.2.17, K8s-1.2.18
- **攻击面关联**: AS-4

### CHK-CAND-049：API Server ServiceAccount 签名密钥 + 令牌查找校验缺失→SA Token 伪造

- **违规族**: K8s G_1_2（API Server 认证）—ServiceAccount 密钥
- **映射的攻击模式**: `auth/k8s-sa-exploit`
- **严重等级**: high
- **前置条件**: `--service-account-key-file` 缺失；`--service-account-lookup=false` 或未设；可伪造任意 SA token
- **合规规则编号**: K8s-1.2.15, K8s-1.2.16
- **攻击面关联**: AS-2

### CHK-CAND-050：API Server Secret 加密配置缺失→etcd 明文 Secret

- **违规族**: K8s G_1_2（API Server 认证）—Secret 加密
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: high
- **前置条件**: `--encryption-provider-config` 未设置；`etcdctl get / --prefix` 直接返回明文 Secret
- **合规规则编号**: K8s-1.2.20
- **攻击面关联**: AS-4

### CHK-CAND-051：API Server 无请求超时→慢速 DoS

- **违规族**: K8s G_1_3（API Server DoS 防护）
- **映射的攻击模式**: `dos/resource-abuse`
- **严重等级**: medium
- **前置条件**: `--request-timeout` 未设置或为 0；慢速攻击者长期占用 API Server 连接句柄
- **合规规则编号**: K8s-1.3.1
- **攻击面关联**: AS-5

### CHK-CAND-052：API Server profiling 开启 + insecure-bind/insecure-port 暴露→信息泄露与未认证访问

- **违规族**: K8s G_1_4（API Server 信息泄露防护）
- **映射的攻击模式**: `data/secret-exfil`, `network/lateral-move`
- **严重等级**: critical
- **前置条件**: `--profiling=true`；`--insecure-bind-address` 指向对外网卡；`--insecure-port!=0`；`curl http://<api-server>:8080/` 返回 200 且无认证
- **合规规则编号**: K8s-1.4.1, K8s-1.4.2, K8s-1.4.3
- **攻击面关联**: AS-4

### CHK-CAND-053：API Server 审计日志缺失→攻击不可追溯

- **违规族**: K8s G_1_5（API Server 审计日志）
- **映射的攻击模式**: —（防御缺失，放大所有入侵的隐蔽性）
- **严重等级**: medium
- **前置条件**: `--audit-log-path`/`--audit-log-maxage`/`--audit-log-maxbackup`/`--audit-log-maxsize`/`--audit-policy-file` 缺失；`--audit-log-format` 非 JSON；`/var/log/kubernetes/audit*` 无文件
- **合规规则编号**: K8s-1.5.1, K8s-1.5.2, K8s-1.5.3, K8s-1.5.4, K8s-1.5.5, K8s-1.5.6
- **攻击面关联**: AS-4

### CHK-CAND-054：API Server 弱加密套件→中间人解密

- **违规族**: K8s G_1_6（API Server SSL/TLS）
- **映射的攻击模式**: `data/secret-exfil`, `network/lateral-move`
- **严重等级**: medium
- **前置条件**: `--tls-cipher-suites` 含弱算法（如 RC4、3DES）或未设置默认含弱套件
- **合规规则编号**: K8s-1.6.1
- **攻击面关联**: AS-3

### CHK-CAND-055：etcd 配置/数据/Pod 清单文件权限宽松→证书与密钥篡改

- **违规族**: K8s G_2_1（Etcd 文件权限）
- **映射的攻击模式**: —（密钥篡改前置条件）
- **严重等级**: low
- **前置条件**: `stat -c %a /etc/etcd/etcd.conf /var/lib/etcd /etc/kubernetes/manifests/etcd.yaml` > 640；属主非 root:root/etcd
- **合规规则编号**: K8s-2.1.1, K8s-2.1.2, K8s-2.1.3, K8s-2.1.4
- **攻击面关联**: AS-4

### CHK-CAND-056：etcd 数据目录默认 + 未授权集群成员加入→数据隔离缺失

- **违规族**: K8s G_2_2（Etcd 配置）
- **映射的攻击模式**: `data/secret-exfil`, `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: `--data-dir` 使用默认宽松目录；单节点模式 `--initial-cluster` 含多个未验证成员；攻击节点加入即可读写集群状态
- **合规规则编号**: K8s-2.2.1, K8s-2.2.2
- **攻击面关联**: AS-4

### CHK-CAND-057：etcd 客户端/Peer TLS 与 mTLS 缺失→明文窃听集群状态

- **违规族**: K8s G_2_3（Etcd 安全配置）
- **映射的攻击模式**: `data/secret-exfil`, `network/lateral-move`
- **严重等级**: high
- **前置条件**: `--cert-file`/`--key-file`/`--trusted-ca-file`/`--peer-cert-file`/`--peer-key-file`/`--peer-client-cert-auth` 缺失
- **合规规则编号**: K8s-2.3.1, K8s-2.3.2, K8s-2.3.3, K8s-2.3.4
- **攻击面关联**: AS-4

### CHK-CAND-058：etcd 监听公网网卡→未授权读取集群 Secret

- **违规族**: K8s G_2_4（Etcd 网络隔离）
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: critical
- **前置条件**: `--listen-client-urls`/`--listen-peer-urls` 含 `0.0.0.0` 或公网 IP；`netstat -tpln | grep 2379` 监听 0.0.0.0
- **合规规则编号**: K8s-2.4.1
- **攻击面关联**: AS-3

### CHK-CAND-059：Controller Manager 清单文件权限宽松→准入控制关闭

- **违规族**: K8s G_3_1（Controller Manager 安全）—文件权限
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: low
- **前置条件**: `stat -c %a /etc/kubernetes/manifests/kube-controller-manager.yaml` > 600；属主非 root
- **合规规则编号**: K8s-3.1.1, K8s-3.1.2
- **攻击面关联**: AS-2

### CHK-CAND-060：Controller Manager 绑定地址非 localhost→控制循环状态探测

- **违规族**: K8s G_3_1（Controller Manager 安全）—绑定地址
- **映射的攻击模式**: `network/lateral-move`
- **严重等级**: medium
- **前置条件**: `--bind-address` 设为 `0.0.0.0` 或对外网卡；metrics/health 端点可被未授权探测
- **合规规则编号**: K8s-3.1.3
- **攻击面关联**: AS-3

### CHK-CAND-061：Controller Manager profiling 启用→调度器内部状态泄露

- **违规族**: K8s G_3_1（Controller Manager 安全）—profiling
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: `--profiling=true`；CM `/debug/pprof` 可访问，泄露 goroutine 栈与控制循环内部数据
- **合规规则编号**: K8s-3.1.4
- **攻击面关联**: AS-4

### CHK-CAND-062：Scheduler 清单文件权限宽松 + profiling 启用→调度策略篡改与状态泄露

- **违规族**: K8s G_3_2（Scheduler 安全）
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: `/etc/kubernetes/manifests/kube-scheduler.yaml` 世界可读；`--profiling=true`；调度队列与算法内部状态可被探测
- **合规规则编号**: K8s-3.2.1, K8s-3.2.2
- **攻击面关联**: AS-4

### CHK-CAND-063：Kubelet 匿名认证启用→未授权 Pod 控制与 exec

- **违规族**: K8s G_4_1（Kubelet 认证）—匿名认证
- **映射的攻击模式**: `auth/k8s-anonymous-access`
- **严重等级**: critical
- **前置条件**: `--anonymous-auth=true` 或未设；`curl -k https://<node>:10250/pods` 返回 200；可调用 `/exec`、`/debug/pprof`
- **合规规则编号**: K8s-4.1.1
- **攻击面关联**: AS-2

### CHK-CAND-064：Kubelet 授权模式非 Webhook→已认证主体全权限

- **违规族**: K8s G_4_1（Kubelet 认证）—授权模式
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: `--authorization-mode=AlwaysAllow` 或未设 Webhook；任意已认证主体对 kubelet 拥有全部权限
- **合规规则编号**: K8s-4.1.2
- **攻击面关联**: AS-2

### CHK-CAND-065：Kubelet 客户端 CA + TLS 证书缺失→客户端证书伪造

- **违规族**: K8s G_4_1（Kubelet 认证）—CA 与 TLS 证书
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `network/lateral-move`
- **严重等级**: high
- **前置条件**: `--client-ca-file` 缺失；`--tls-cert-file`/`--tls-private-key-file` 缺失；kubelet 客户端证书可被伪造
- **合规规则编号**: K8s-4.1.3, K8s-4.1.4
- **攻击面关联**: AS-2

### CHK-CAND-066：Kubelet 配置文件不存在 + 配置层 anonymous 启用→认证策略漂移

- **违规族**: K8s G_4_2（Kubelet 授权配置）—配置文件与匿名认证
- **映射的攻击模式**: `auth/k8s-anonymous-access`
- **严重等级**: high
- **前置条件**: kubelet 配置文件缺失或未被解析（命令行覆盖）；`authentication.anonymous.enabled=true`；init 容器可注入恶意认证参数
- **合规规则编号**: K8s-4.2.1, K8s-4.2.2
- **攻击面关联**: AS-2

### CHK-CAND-067：Kubelet 认证 webhook 关闭 + CA/mode 缺失→SA Token 失效与越权

- **违规族**: K8s G_4_2（Kubelet 授权配置）—webhook/CA/授权模式
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `auth/k8s-sa-exploit`
- **严重等级**: high
- **前置条件**: `authentication.webhook.enabled=false`；`authentication.x509.clientCAFile` 缺失；`authorization.mode!=Webhook`
- **合规规则编号**: K8s-4.2.3, K8s-4.2.4, K8s-4.2.5
- **攻击面关联**: AS-2

### CHK-CAND-068：Kubelet 缓存 TTL 过大 + rotateCertificates 关闭→证书长期未轮换

- **违规族**: K8s G_4_2（Kubelet 授权配置）—缓存与轮换
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: medium
- **前置条件**: `authorization.webhook.cacheAuthorizedTTL` 过大；`rotateCertificates=false` 且未配 clientCA；泄露凭证长期有效
- **合规规则编号**: K8s-4.2.6, K8s-4.2.7
- **攻击面关联**: AS-2

### CHK-CAND-069：Kubelet 配置文件权限宽松→认证授权策略与 TLS 路径泄露

- **违规族**: K8s G_4_3（Kubelet 配置文件权限）
- **映射的攻击模式**: —（凭证线索泄露前置条件）
- **严重等级**: low
- **前置条件**: `stat -c %a /var/lib/kubelet/config.yaml` > 600；属主非 root；可读取认证授权策略与 TLS 凭证路径
- **合规规则编号**: K8s-4.3.1
- **攻击面关联**: AS-2

### CHK-CAND-070：Kubelet 内核默认未保护 + iptables 链未维护→逃逸面放大与网络策略失效

- **违规族**: K8s G_5_1（Kubelet 运行时配置）—内核与网络栈
- **映射的攻击模式**: `escape/capability-privesc`, `network/lateral-move`
- **严重等级**: high
- **前置条件**: `--protect-kernel-defaults=false`；`--make-iptables-util-chains=false`；kubelet 改写 `vm.overcommit_memory`，Pod 间流量绕过 NetworkPolicy
- **合规规则编号**: K8s-5.1.1, K8s-5.1.2
- **攻击面关联**: AS-1

### CHK-CAND-071：Kubelet event-qps 过大 + cgroup 驱动不一致→etcd 灌爆与运行时失配

- **违规族**: K8s G_5_1（Kubelet 运行时配置）—事件与 cgroup
- **映射的攻击模式**: `dos/resource-abuse`
- **严重等级**: medium
- **前置条件**: `--event-qps` 过大或未限；`--cgroup-driver` 与容器运行时不一致；`--cgroups-per-qos` 未设；Pod 灌爆 etcd Event 存储
- **合规规则编号**: K8s-5.1.3, K8s-5.1.4, K8s-5.1.5
- **攻击面关联**: AS-5

### CHK-CAND-072：Kubelet read-only 端口开放 + hostname 冲突 + 静态 Pod 清单目录宽松→节点信息泄露与恶意静态 Pod

- **违规族**: K8s G_5_1（Kubelet 运行时配置）—只读端口/主机名/静态 Pod
- **映射的攻击模式**: `data/secret-exfil`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `--read-only-port=10255` 暴露；`--hostname-override` 跨节点冲突；`/etc/kubernetes/manifests` 世界可写，可植入恶意静态 Pod
- **合规规则编号**: K8s-5.1.6, K8s-5.1.7, K8s-5.1.8
- **攻击面关联**: AS-1

### CHK-CAND-073：Kubelet 流式连接无超时 + 节点状态更新过频→连接句柄耗尽与 etcd I/O 暴涨

- **违规族**: K8s G_5_2（Kubelet 流式连接配置）—流式与节点状态
- **映射的攻击模式**: `dos/resource-abuse`
- **严重等级**: medium
- **前置条件**: `--streaming-connection-idle-timeout=0`；`--node-status-update-frequency` 过频；攻击者长期挂载 exec 流并推高 etcd I/O
- **合规规则编号**: K8s-5.2.1, K8s-5.2.2
- **攻击面关联**: AS-5

### CHK-CAND-074：Kubelet volume-plugin 目录不隔离 + register/runtime root 未隔离→后门卷驱动植入

- **违规族**: K8s G_5_2（Kubelet 流式连接配置）—插件与隔离
- **映射的攻击模式**: `supply/registry-poison`, `persist/docker-volume-persist`
- **严重等级**: high
- **前置条件**: `--volume-plugin-dir` 指向可写目录；FlexVolume/CSI 白名单未限制；`--register-node`/`--container-runtime-root` 未显式隔离
- **合规规则编号**: K8s-5.2.3, K8s-5.2.4, K8s-5.2.5, K8s-5.2.6
- **攻击面关联**: AS-6

### CHK-CAND-075：Kubelet TLS 弱版本 + 弱加密套件→中间人解密 kubelet 流量

- **违规族**: K8s G_5_3（Kubelet TLS 配置）
- **映射的攻击模式**: `network/lateral-move`, `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: `--tls-min-version` < TLS1.2 或未设；`--tls-cipher-suites` 含弱套件；kubelet 通信可被降级攻击解密
- **合规规则编号**: K8s-5.3.1, K8s-5.3.2
- **攻击面关联**: AS-3

### CHK-CAND-076：Kubelet profiling 开启 + debugging handlers 启用→内部状态泄露与 exec RCE 入口

- **违规族**: K8s G_5_4（Kubelet 信息泄露防护）—profiling/debug
- **映射的攻击模式**: `data/secret-exfil`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `--profiling=true`；`--enable-debugging-handlers=true`；`/debug/pprof` 泄露 goroutine 栈含密钥片段；exec 接口成为容器内 RCE 入口
- **合规规则编号**: K8s-5.4.1, K8s-5.4.2
- **攻击面关联**: AS-4

### CHK-CAND-077：Kubelet 日志写盘不限制 + metrics 公网暴露 + housekeeping 异常→痕迹清理与指标泄露

- **违规族**: K8s G_5_4（Kubelet 信息泄露防护）—日志/metrics/housekeeping
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: `--stderrthreshold` 未限制本地写盘；kubelet metrics 端点对外暴露；`--housekeeping-interval` 异常；攻击痕迹可经 `/var/log` 覆盖清理
- **合规规则编号**: K8s-5.4.3, K8s-5.4.4, K8s-5.4.5
- **攻击面关联**: AS-4

### CHK-CAND-078：Kubelet event-burst 无限→etcd 存储耗尽集群只读

- **违规族**: K8s G_5_5（Kubelet DoS 防护）
- **映射的攻击模式**: `dos/resource-abuse`
- **严重等级**: medium
- **前置条件**: `--event-burst`/`--event-qps` 未搭配限制；恶意 Pod 发无限 Event 灌爆 etcd 存储致集群只读
- **合规规则编号**: K8s-5.5.1
- **攻击面关联**: AS-5

### CHK-CAND-079：Kubelet systemd 服务无资源限制→本地 fd/procs 耗尽

- **违规族**: K8s G_5_6（Kubelet 系统配置）
- **映射的攻击模式**: `dos/resource-abuse`
- **严重等级**: medium
- **前置条件**: kubelet systemd unit 无 `LimitNOFILE`/`LimitNPROC`；恶意 Pod 触发 kubelet 本地资源耗尽
- **合规规则编号**: K8s-5.6.1
- **攻击面关联**: AS-5

### CHK-CAND-080：命名空间无 NetworkPolicy + 默认不拒绝入站→Pod 间 L3/L4 全互通

- **违规族**: K8s G_6_1（Network Policies 配置）
- **映射的攻击模式**: `network/lateral-move`
- **严重等级**: high
- **前置条件**: `kubectl get networkpolicy -A` 命名空缺策略；关键命名空间无 `default-deny-ingress`；陌生 Pod 流量可直达
- **合规规则编号**: K8s-6.1.1, K8s-6.1.2
- **攻击面关联**: AS-3

### CHK-CAND-081：业务命名空间默认不拒绝 Egress→被入侵 Pod 自由外联 C2/数据外发

- **违规族**: K8s G_6_2（默认拒绝网络）
- **映射的攻击模式**: `network/dns-exfil`, `network/cloud-metadata`
- **严重等级**: high
- **前置条件**: 业务命名空间无 `default-deny-egress`；被入侵 Pod 可外联 C2、外发数据通道、访问云元数据端点
- **合规规则编号**: K8s-6.2.1
- **攻击面关联**: AS-3

### CHK-CAND-082：特权容器启用→主机设备/命名空间全访问逃逸

- **违规族**: K8s G_7_1（Pod 安全）—特权容器
- **映射的攻击模式**: `escape/capability-privesc`, `escape/cgroup-escape`, `escape/socket-escape`
- **严重等级**: critical
- **前置条件**: Pod `securityContext.privileged=true`；容器内 `cat /proc/1/status | grep CapEff` 为 `0000003fffffffff`
- **合规规则编号**: K8s-7.1.1
- **攻击面关联**: AS-1

### CHK-CAND-083：hostPath 卷挂载敏感路径→文件系统逃逸

- **违规族**: K8s G_7_1（Pod 安全）—hostPath
- **映射的攻击模式**: `escape/hostpath-mount`
- **严重等级**: critical
- **前置条件**: Pod `volumes[*].hostPath.path` 指向 `/`、`/etc`、`/var/run/docker.sock`、`/proc` 等敏感路径
- **合规规则编号**: K8s-7.1.2
- **攻击面关联**: AS-1

### CHK-CAND-084：hostPID 启用→宿主机进程注入与 kubelet 探测

- **违规族**: K8s G_7_1（Pod 安全）—hostPID
- **映射的攻击模式**: `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: Pod `hostPID=true`；容器内 `ps aux` 可见并操作宿主机进程（含 kubelet）
- **合规规则编号**: K8s-7.1.3
- **攻击面关联**: AS-1

### CHK-CAND-085：hostIPC 启用→共享内存段注入

- **违规族**: K8s G_7_1（Pod 安全）—hostIPC
- **映射的攻击模式**: `escape/capability-privesc`
- **严重等级**: medium
- **前置条件**: Pod `hostIPC=true`；容器内 `ipcs -m` 可见并操作宿主机共享内存段
- **合规规则编号**: K8s-7.1.4
- **攻击面关联**: AS-1

### CHK-CAND-086：hostNetwork 启用→网络逃逸与元数据端点直访

- **违规族**: K8s G_7_1（Pod 安全）—hostNetwork
- **映射的攻击模式**: `network/lateral-move`, `network/cloud-metadata`
- **严重等级**: high
- **前置条件**: Pod `hostNetwork=true`；容器与宿主机共享网络栈，可直访 `169.254.169.254`、扫描本机监听服务
- **合规规则编号**: K8s-7.1.5
- **攻击面关联**: AS-3

### CHK-CAND-087：危险 capabilities + 未 drop ALL + privilege escalation 允许→权限提升逃逸

- **违规族**: K8s G_7_1（Pod 安全）—capabilities/escalation
- **映射的攻击模式**: `escape/capability-privesc`
- **严重等级**: critical
- **前置条件**: `capabilities.add` 含 `SYS_ADMIN`/`SYS_PTRACE`/`NET_ADMIN` 等；`capabilities.drop` 未含 `ALL`；`allowPrivilegeEscalation=true`
- **合规规则编号**: K8s-7.1.6, K8s-7.1.11, K8s-7.1.12
- **攻击面关联**: AS-1

### CHK-CAND-088：容器以 root 运行 + runAsNonRoot 未设→逃逸后直读主机文件

- **违规族**: K8s G_7_1（Pod 安全）—非 root
- **映射的攻击模式**: `escape/capability-privesc`, `data/secret-exfil`
- **严重等级**: high
- **前置条件**: 容器 `runAsUser=0` 或未设；`runAsNonRoot!=true`；逃逸后以 root uid 直读 `/etc/shadow`、`/etc/kubernetes`
- **合规规则编号**: K8s-7.1.7, K8s-7.1.8
- **攻击面关联**: AS-1

### CHK-CAND-089：读写根文件系统 + 无 seccompProfile→镜像层写入后门 + 系统调用无限制

- **违规族**: K8s G_7_1（Pod 安全）—readOnlyFS/seccomp
- **映射的攻击模式**: `persist/docker-volume-persist`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `readOnlyRootFilesystem!=true`；`seccompProfile` 未设为 RuntimeDefault/Localhost；攻击者可在镜像层写入挖矿/后门二进制
- **合规规则编号**: K8s-7.1.9, K8s-7.1.10
- **攻击面关联**: AS-1

### CHK-CAND-090：PodSecurityAdmission 未 enforce restricted→Pod 安全策略缺失

- **违规族**: K8s G_7_1（Pod 安全）—PSS
- **映射的攻击模式**: `escape/capability-privesc`, `escape/hostpath-mount`
- **严重等级**: high
- **前置条件**: 命名空间无 `pod-security.kubernetes.io/enforce=restricted` 标签或仅为 baseline/privileged
- **合规规则编号**: K8s-7.1.13
- **攻击面关联**: AS-1

### CHK-CAND-091：Pod 默认 SA token 自动挂载→SA 利用

- **违规族**: K8s G_7_1（Pod 安全）—SA token
- **映射的攻击模式**: `auth/k8s-sa-exploit`
- **严重等级**: high
- **前置条件**: Pod `automountServiceAccountToken!=false`；容器内 `cat /var/run/secrets/kubernetes.io/serviceaccount/token` 可读
- **合规规则编号**: K8s-7.1.14
- **攻击面关联**: AS-2

### CHK-CAND-092：Pod hostUsers 启用→共享主机用户命名空间逃逸

- **违规族**: K8s G_7_1（Pod 安全）—hostUsers
- **映射的攻击模式**: `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: Pod `hostUsers=true`；容器与宿主机共享 UID/GID 映射，落盘文件以 root 持有，逃逸后越权文件操作不受 userns 隔离限制
- **合规规则编号**: K8s-7.1.15
- **攻击面关联**: AS-1

### CHK-CAND-093：容器可写镜像层 + init 容器特权→后门持久化与逃逸

- **违规族**: K8s G_7_2（容器运行时安全）
- **映射的攻击模式**: `persist/docker-volume-persist`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `readOnlyRootFilesystem!=true` 允许镜像层写入后门；`initContainers` 用 `privileged=true` 或 `allowPrivilegeEscalation=true`，启动早期逃逸
- **合规规则编号**: K8s-7.2.1, K8s-7.2.2
- **攻击面关联**: AS-1

### CHK-CAND-094：Secret 未加密 at-rest + 环境变量明文传递→Secret 直接 dump 与 env 泄露

- **违规族**: K8s G_8_1（Secret 管理）
- **映射的攻击模式**: `data/secret-exfil`, `data/env-credential-leak`
- **严重等级**: high
- **前置条件**: 未配置 `--encryption-provider-config`；`etcdctl get / --prefix` 直出明文 Secret；Pod `env[*].valueFrom.secretKeyRef` 明文注入；`env | grep -iE 'password|token|key'` 直显
- **合规规则编号**: K8s-8.1.1, K8s-8.1.2
- **攻击面关联**: AS-4

### CHK-CAND-095：cluster-admin 绑定过多→直通 root 等价 RBAC

- **违规族**: K8s G_8_2（RBAC 配置）—cluster-admin
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: critical
- **前置条件**: `kubectl get clusterrolebinding -o json | jq '.items[]|select(.roleRef.name=="cluster-admin")'` 返回非系统绑定；业务 SA/用户直通 root RBAC
- **合规规则编号**: K8s-8.2.1
- **攻击面关联**: AS-2

### CHK-CAND-096：ClusterRole 通配符权限→root 等价权限

- **违规族**: K8s G_8_2（RBAC 配置）—通配符
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `persist/cronjob-persist`
- **严重等级**: critical
- **前置条件**: 自定义 ClusterRole 含 `verbs: ["*"]` 或 `resources: ["*"]`；当前 SA 可创建任意资源
- **合规规则编号**: K8s-8.2.2
- **攻击面关联**: AS-2

### CHK-CAND-097：ClusterRole 授予 impersonate→身份冒用

- **违规族**: K8s G_8_2（RBAC 配置）—impersonate
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: critical
- **前置条件**: 非系统 ClusterRole 规则 `resources` 含 `impersonate`；可冒名 cluster-admin 调用 API
- **合规规则编号**: K8s-8.2.3
- **攻击面关联**: AS-2

### CHK-CAND-098：default SA token 自动挂载未关 + 业务 SA 非最小权限→SA 越权利用

- **违规族**: K8s G_8_2（RBAC 配置）—SA mount + 最小权限
- **映射的攻击模式**: `auth/k8s-sa-exploit`
- **严重等级**: high
- **前置条件**: 系统保留命名空间 default SA 未关 `automountServiceAccountToken`；业务命名空间 default SA 仍自动挂载；业务 SA 用过宽 RoleBinding 而非最小权限
- **合规规则编号**: K8s-8.2.4, K8s-8.2.5, K8s-8.2.6
- **攻击面关联**: AS-2

### CHK-CAND-099：系统命名空间承载业务工作负载 + default 命名空间运行业务→控制面污染

- **违规族**: K8s G_8_2（RBAC 配置）—系统与 default 命名空间隔离
- **映射的攻击模式**: `escape/capability-privesc`, `persist/webhook-backdoor`
- **严重等级**: medium
- **前置条件**: `kube-system`/`kube-public` 含业务 Pod；`default` 命名空间承载业务工作负载；被入侵 Pod 可触及安全控制组件
- **合规规则编号**: K8s-8.2.7, K8s-8.2.11
- **攻击面关联**: AS-1

### CHK-CAND-100：Kubernetes Dashboard 类特权 UI 暴露公网→认证绕过

- **违规族**: K8s G_8_2（RBAC 配置）—Dashboard 暴露
- **映射的攻击模式**: `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: `kubectl get svc -A | grep dashboard` 显示 LoadBalancer/NodePort；Dashboard 绑定高权限 SA 且公网可达
- **合规规则编号**: K8s-8.2.8
- **攻击面关联**: AS-2

### CHK-CAND-101：只读 API 端点缺 NodeRestriction/ResourceQuota 保护→资源枚举与配额绕过

- **违规族**: K8s G_8_2（RBAC 配置）—只读端点保护
- **映射的攻击模式**: `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: 只读端点未配 NodeRestriction；命名空间缺 ResourceQuota；攻击者枚举集群资源拓扑并绕过配额
- **合规规则编号**: K8s-8.2.9
- **攻击面关联**: AS-4

### CHK-CAND-102：命名空间无 NetworkPolicy 限流→横向移动与元数据直访

- **违规族**: K8s G_8_2（RBAC 配置）—NetworkPolicy 限流
- **映射的攻击模式**: `network/lateral-move`, `network/cloud-metadata`
- **严重等级**: high
- **前置条件**: 命名空间缺 NetworkPolicy 限流；被入侵 Pod 可横向移动并直访云元数据端点
- **合规规则编号**: K8s-8.2.10
- **攻击面关联**: AS-3

### CHK-CAND-103：RBAC 授权 anonymous 组 + kubeconfig endpoint 指向非受控控制平面→匿名授权与劫持

- **违规族**: K8s G_8_2（RBAC 配置）—anonymous 组与 kubeconfig
- **映射的攻击模式**: `auth/k8s-anonymous-access`, `auth/k8s-rbac-abuse`
- **严重等级**: high
- **前置条件**: ClusterRoleBinding 直接对 `system:anonymous`/`system:unauthenticated` 授权；kubeconfig `clusters[].server` 指向公网或非受控控制平面
- **合规规则编号**: K8s-8.2.12, K8s-8.2.13
- **攻击面关联**: AS-2

### CHK-CAND-104：Pod fsGroup/runAsUser 未显式配置 + 无 SELinux/AppArmor→逃逸后越权文件操作

- **违规族**: K8s G_8_3（安全上下文）
- **映射的攻击模式**: `escape/capability-privesc`, `data/secret-exfil`
- **严重等级**: high
- **前置条件**: Pod 未显式设 `fsGroup`/`runAsUser`/`runAsGroup`（默认 root）；未设 `seLinuxOptions`/`appArmorProfile`；逃逸后文件以 root 持有且无 MAC 限制
- **合规规则编号**: K8s-8.3.1, K8s-8.3.2
- **攻击面关联**: AS-1

### CHK-CAND-105：命名空间间默认互通→跨命名空间横向移动

- **违规族**: K8s G_8_4（高级网络策略）—命名空间间隔离
- **映射的攻击模式**: `network/lateral-move`
- **严重等级**: high
- **前置条件**: 命名空间间无 `default-deny-all`；被入侵 Pod 可横向移动至其他命名空间高价值目标
- **合规规则编号**: K8s-8.4.1
- **攻击面关联**: AS-3

### CHK-CAND-106：业务命名空间可直访 kube-system→触及安全控制组件

- **违规族**: K8s G_8_4（高级网络策略）—kube-system 访问限制
- **映射的攻击模式**: `auth/k8s-rbac-abuse`, `data/secret-exfil`
- **严重等级**: high
- **前置条件**: 业务命名空间无策略拒访 `kube-system`；业务 Pod 可直访 kube-dns/etcd Pod 等安全控制组件
- **合规规则编号**: K8s-8.4.2
- **攻击面关联**: AS-2

### CHK-CAND-107：NodePort 类型 Service 不受限→节点端口公网暴露

- **违规族**: K8s G_8_4（高级网络策略）—NodePort
- **映射的攻击模式**: `network/lateral-move`
- **严重等级**: medium
- **前置条件**: 业务命名空间使用 `type: NodePort` Service；节点高端口范围暴露公网，可直连 Pod 服务
- **合规规则编号**: K8s-8.4.3
- **攻击面关联**: AS-3

### CHK-CAND-108：ExternalIPs 类型 Service 使用→流量劫持与未受控入口

- **违规族**: K8s G_8_4（高级网络策略）—ExternalIPs
- **映射的攻击模式**: `network/lateral-move`, `data/secret-exfil`
- **严重等级**: medium
- **前置条件**: Service 使用 `externalIPs`；流量经未受控外部 IP 入口，可被劫持或绕过 Ingress 策略
- **合规规则编号**: K8s-8.4.4
- **攻击面关联**: AS-3

---

## 全量覆盖校验

新增卡片 CHK-CAND-041–108 共 68 张，与既有 CHK-CAND-001–040 叠加后覆盖 CIS Kubernetes Benchmark v1.8.0 全 134 条规则：

| CIS 分组 | 规则编号范围 | 条数 | 覆盖卡片 |
|----------|------------|------|---------|
| G_1_1 | 1.1.1–1.1.7 | 7 | CHK-CAND-041 |
| G_1_2 | 1.2.1–1.2.23 | 23 | CHK-CAND-042–050 |
| G_1_3 | 1.3.1 | 1 | CHK-CAND-051 |
| G_1_4 | 1.4.1–1.4.3 | 3 | CHK-CAND-052 |
| G_1_5 | 1.5.1–1.5.6 | 6 | CHK-CAND-053 |
| G_1_6 | 1.6.1 | 1 | CHK-CAND-054 |
| G_2_1 | 2.1.1–2.1.4 | 4 | CHK-CAND-055 |
| G_2_2 | 2.2.1–2.2.2 | 2 | CHK-CAND-056 |
| G_2_3 | 2.3.1–2.3.4 | 4 | CHK-CAND-057 |
| G_2_4 | 2.4.1 | 1 | CHK-CAND-058 |
| G_3_1 | 3.1.1–3.1.4 | 4 | CHK-CAND-059–061 |
| G_3_2 | 3.2.1–3.2.2 | 2 | CHK-CAND-062 |
| G_4_1 | 4.1.1–4.1.4 | 4 | CHK-CAND-063–065 |
| G_4_2 | 4.2.1–4.2.7 | 7 | CHK-CAND-066–068 |
| G_4_3 | 4.3.1 | 1 | CHK-CAND-069 |
| G_5_1 | 5.1.1–5.1.8 | 8 | CHK-CAND-070–072 |
| G_5_2 | 5.2.1–5.2.6 | 6 | CHK-CAND-073–074 |
| G_5_3 | 5.3.1–5.3.2 | 2 | CHK-CAND-075 |
| G_5_4 | 5.4.1–5.4.5 | 5 | CHK-CAND-076–077 |
| G_5_5 | 5.5.1 | 1 | CHK-CAND-078 |
| G_5_6 | 5.6.1 | 1 | CHK-CAND-079 |
| G_6_1 | 6.1.1–6.1.2 | 2 | CHK-CAND-080 |
| G_6_2 | 6.2.1 | 1 | CHK-CAND-081 |
| G_7_1 | 7.1.1–7.1.15 | 15 | CHK-CAND-082–092 |
| G_7_2 | 7.2.1–7.2.2 | 2 | CHK-CAND-093 |
| G_8_1 | 8.1.1–8.1.2 | 2 | CHK-CAND-094 |
| G_8_2 | 8.2.1–8.2.13 | 13 | CHK-CAND-095–103 |
| G_8_3 | 8.3.1–8.3.2 | 2 | CHK-CAND-104 |
| G_8_4 | 8.4.1–8.4.4 | 4 | CHK-CAND-105–108 |
| **合计** | | **134** | |

---

### CHK-CAND-131：Docker 宿主机未加固+版本过旧→逃逸面扩大

- **违规族**: Docker G_1（运行环境配置）
- **映射的攻击模式**: `escape/runc-escape`, `escape/cgroup-escape`
- **严重等级**: high
- **前置条件**: 宿主机内核 sysctl 未加固（ASLR 关闭、ptrace_scope=0）；`docker version` 低于 24.0 或含已知 CVE；`/var/lib/docker` 与根分区共享（`df -h /var/lib/docker` 显示根分区）；`auditctl -l | grep docker` 无审计规则
- **合规规则编号**: Docker-1, Docker-2, Docker-3, Docker-4
- **攻击面关联**: AS-1

### CHK-CAND-132：Docker daemon TCP 暴露无 TLS→远程特权容器创建

- **违规族**: Docker G_1（运行环境配置）— 守护进程监听
- **映射的攻击模式**: `auth/docker-api-auth`, `escape/socket-escape`
- **严重等级**: critical
- **前置条件**: `ps -ef | grep dockerd | grep -E '\-H tcp://|0.0.0.0'` 显示监听 TCP 且无 `--tlsverify`；`curl http://<host>:2375/containers/json` 无需认证返回容器列表
- **合规规则编号**: Docker-5
- **攻击面关联**: AS-2

### CHK-CAND-133：Docker daemon 网络暴露面（HTTP 代理/userland-proxy/legacy registry）→中间人与协议降级

- **违规族**: Docker G_2（守护进程参数）— 网络暴露子组
- **映射的攻击模式**: `network/mitm`, `network/registry-poison`
- **严重等级**: medium
- **前置条件**: 代理使用 HTTP（`HTTPS_PROXY` 未设/为 http://）；`userland-proxy` 为 true（默认，docker-proxy 进程存在）；`disable-legacy-registry` 未启用，允许 v1 registry 无 TLS 通信
- **合规规则编号**: Docker-6, Docker-10, Docker-11
- **攻击面关联**: AS-3

### CHK-CAND-134：Docker daemon 日志 debug+SELinux 缺失→敏感信息泄露与逃逸面放大

- **违规族**: Docker G_2（守护进程参数）— 日志与 MAC 子组
- **映射的攻击模式**: `data/daemon-log-leak`, `escape/cgroup-escape`
- **严重等级**: high
- **前置条件**: `dockerd --log-level=debug` 或 daemon.json 中 `log-level` 为 debug（日志含环境变量/认证凭据）；`getenforce` 为 Disabled/Permissive 或 `--selinux-enabled` 未启用，容器无 MAC 约束
- **合规规则编号**: Docker-7, Docker-8
- **攻击面关联**: AS-1, AS-4

### CHK-CAND-135：Docker daemon 挂载传播 shared+userns-remap 缺失+cgroup/ulimit 默认→逃逸与资源绕过

- **违规族**: Docker G_2（守护进程参数）— 隔离与资源子组
- **映射的攻击模式**: `escape/capability-privesc`, `dos/resource-abuse`
- **严重等级**: high
- **前置条件**: `--mount-namespace-daemon=shared` 或 rshared 传播（容器可感知/影响宿主机挂载）；daemon.json 无 `userns-remap`（容器 root=宿主机 root uid=0）；`cgroup-parent` 为 `/`/`docker`（共享根 cgroup 绕过资源限制）；daemon.json 无 `default-ulimits`
- **合规规则编号**: Docker-9, Docker-14, Docker-15, Docker-16
- **攻击面关联**: AS-1, AS-5

### CHK-CAND-136：Docker Swarm 通信无 TLS 加密+live-restore 未启用→集群嗅探与升级中断暴露

- **违规族**: Docker G_2（守护进程参数）— Swarm 与可用性子组
- **映射的攻击模式**: `network/swarm-sniff`, `escape/upgrade-window`
- **严重等级**: medium
- **前置条件**: Swarm 模式下 overlay 网络未启用 `--opt encrypted`；`docker network inspect <overlay>` 显示 `Encrypted=false`；`daemon.json` 中 `live-restore` 未设为 true，Docker 升级/重启时所有容器中断
- **合规规则编号**: Docker-12, Docker-13
- **攻击面关联**: AS-3, AS-5

### CHK-CAND-137：Docker docker.sock 权限/属主宽松→socket 逃逸

- **违规族**: Docker G_3（文件权限）— socket 子组
- **映射的攻击模式**: `escape/socket-escape`
- **严重等级**: critical
- **前置条件**: `stat -c '%a' /var/run/docker.sock` 宽松于 660（如 666/777）；属主非 `root:docker`；任何本地用户均可读写 docker.sock 并通过 `docker run --privileged` 创建逃逸容器
- **合规规则编号**: Docker-17, Docker-18
- **攻击面关联**: AS-1

### CHK-CAND-138：Docker 证书/daemon.json/数据目录权限宽松→认证篡改与数据泄露

- **违规族**: Docker G_3（文件权限）— 证书与配置文件子组
- **映射的攻击模式**: `auth/docker-config-tamper`, `data/image-layer-secret`
- **严重等级**: high
- **前置条件**: `stat -c '%a' /etc/docker/ca.pem` 宽松于 444 或属主非 root:root（可替换 CA 实施中间人）；`server-cert.pem` 权限宽松于 400；`daemon.json` 权限宽松于 644 或属主非 root:root（可篡改关闭安全配置）；`/etc/docker/` 宽松于 755；`/var/lib/docker/` 宽松于 710（可读取容器层与卷数据）
- **合规规则编号**: Docker-19, Docker-20, Docker-21, Docker-22, Docker-23, Docker-24, Docker-25, Docker-26
- **攻击面关联**: AS-2, AS-4

### CHK-CAND-139：Docker 镜像以 root 运行+含 sudo/SSH→容器内提权与持久化通道

- **违规族**: Docker G_4（镜像构建）— 用户与最小服务子组
- **映射的攻击模式**: `escape/capability-privesc`, `persist/ssh-backdoor`
- **严重等级**: high
- **前置条件**: `docker inspect --format '{{.Config.User}}' <cid>` 为空或 root；容器内存在 `/etc/sudoers` 或 sudoers.d 条目；容器内 `which sshd` 存在且 sshd 进程运行
- **合规规则编号**: Docker-27, Docker-29, Docker-30, Docker-49
- **攻击面关联**: AS-1, AS-3

### CHK-CAND-140：Docker 镜像含 secrets/缓存/无 healthcheck→凭据泄露与可用性盲区

- **违规族**: Docker G_4（镜像构建）— 数据清理与可观测性子组
- **映射的攻击模式**: `data/image-layer-secret`, `data/env-credential-leak`
- **严重等级**: medium
- **前置条件**: `docker inspect --format '{{.Config.Env}}' <cid>` 含 password/secret/token/key 等明文；`docker history --no-trunc <image>` 含 secrets 的 ENV/COPY 层；`/var/cache/apt/` 含大量缓存；`/etc/shadow` 存在有效密码哈希；镜像无 HEALTHCHECK 配置
- **合规规则编号**: Docker-28, Docker-31, Docker-32, Docker-33
- **攻击面关联**: AS-4, AS-5

### CHK-CAND-141：Docker 容器特权模式→直接宿主机逃逸

- **违规族**: Docker G_5（容器运行时）— 特权子组
- **映射的攻击模式**: `escape/cgroup-escape`, `escape/socket-escape`, `escape/hostpath-mount`
- **严重等级**: critical
- **前置条件**: `docker inspect --format '{{.HostConfig.Privileged}}' <cid>` 返回 true；容器内 `cat /proc/1/status | grep CapEff` 为 `0000003fffffffff`；容器可访问 `/dev/sda*` 等全部宿主机设备，可 mount 宿主机磁盘
- **合规规则编号**: Docker-42, Docker-55
- **攻击面关联**: AS-1

### CHK-CAND-142：Docker 容器保留危险 capabilities→逃逸与权限提升

- **违规族**: Docker G_5（容器运行时）— capabilities 子组
- **映射的攻击模式**: `escape/capability-privesc`
- **严重等级**: critical
- **前置条件**: `docker inspect --format '{{.HostConfig.CapAdd}}' <cid>` 含 SYS_ADMIN/SYS_PTRACE/SYS_MODULE/NET_ADMIN/DAC_OVERRIDE；未执行 `--cap-drop=ALL`；容器内 `capsh --print` 显示保留危险能力
- **合规规则编号**: Docker-43
- **攻击面关联**: AS-1

### CHK-CAND-143：Docker 容器 seccomp unconfined→危险系统调用放行

- **违规族**: Docker G_5（容器运行时）— seccomp 子组
- **映射的攻击模式**: `escape/cgroup-escape`, `escape/procfs-escape`
- **严重等级**: high
- **前置条件**: `docker inspect --format '{{.HostConfig.SecurityOpt}}' <cid>` 含 `seccomp=unconfined` 或 seccomp 为空；容器可执行 mount/keyctl/bpf/clone 等逃逸相关系统调用
- **合规规则编号**: Docker-44, Docker-59
- **攻击面关联**: AS-1

### CHK-CAND-144：Docker 容器无 AppArmor/SELinux MAC→逃逸面放大

- **违规族**: Docker G_5（容器运行时）— MAC 子组
- **映射的攻击模式**: `escape/cgroup-escape`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `docker inspect --format '{{.AppArmorProfile}}' <cid>` 为空或 unconfined；`docker inspect --format '{{.ProcessLabel}} {{.MountLabel}}' <cid>` 为空（SELinux 未启用）；容器无任何强制访问控制约束
- **合规规则编号**: Docker-34, Docker-35
- **攻击面关联**: AS-1

### CHK-CAND-145：Docker 容器无资源限制+无 ulimit/cgroup 隔离→DoS 与资源耗尽

- **违规族**: Docker G_5（容器运行时）— 资源限制子组
- **映射的攻击模式**: `dos/resource-abuse`, `dos/fork-bomb`
- **严重等级**: high
- **前置条件**: `docker inspect --format '{{.HostConfig.Memory}}' <cid>` 为 0；`CpuShares`/`CpusetCpus` 为 0；`PidsLimit` 为 0 或 -1；`CgroupParent` 为 `/`（根 cgroup）；`Ulimits` 未配置；daemon.json 无 `default-ulimits`；容器可耗尽宿主机内存/CPU/PID/文件描述符
- **合规规则编号**: Docker-36, Docker-37, Docker-40, Docker-41, Docker-45, Docker-47, Docker-48, Docker-57, Docker-58
- **攻击面关联**: AS-5

### CHK-CAND-146：Docker 容器 hostNetwork+敏感目录读写挂载+可写根文件系统→网络嗅探与文件系统逃逸

- **违规族**: Docker G_5（容器运行时）— 网络与挂载子组
- **映射的攻击模式**: `network/lateral-move`, `network/cloud-metadata`, `escape/hostpath-mount`
- **严重等级**: critical
- **前置条件**: `docker inspect --format '{{.HostConfig.NetworkMode}}' <cid>` 为 host（容器直接访问宿主机网络栈，可嗅探 localhost 服务与云元数据端点）；`docker inspect` 的 Mounts 显示 `/etc`、`/`、`/var/run/docker.sock` 等以 rw 模式挂载；`ReadonlyRootfs` 为 false（攻击者可在根文件系统植入后门）
- **合规规则编号**: Docker-38, Docker-39, Docker-50, Docker-56
- **攻击面关联**: AS-1, AS-3

### CHK-CAND-147：Docker 容器 add-host 劫持+content-trust 缺失+daemon.json 运行时篡改→流量劫持与供应链攻击

- **违规族**: Docker G_5（容器运行时）— 网络覆写与信任子组
- **映射的攻击模式**: `network/dns-hijack`, `supply/image-tag-mutation`, `auth/docker-config-tamper`
- **严重等级**: medium
- **前置条件**: `docker inspect --format '{{.HostConfig.ExtraHosts}}' <cid>` 存在指向恶意 IP 的域名覆写；`DOCKER_CONTENT_TRUST` 为空或 0（可拉取未签名恶意镜像）；运行时复查 daemon.json 权限/属主变更（Docker-52/53 复查项）；镜像/容器无元数据标签
- **合规规则编号**: Docker-46, Docker-51, Docker-52, Docker-53, Docker-54
- **攻击面关联**: AS-3, AS-6

### CHK-CAND-148：Docker 容器健康/资源监控缺失→可用性盲区

- **违规族**: Docker G_6（容器运维）
- **映射的攻击模式**: —（防御缺失，不健康容器可能被攻陷且未告警）
- **严重等级**: low
- **前置条件**: `docker ps --filter 'health=unhealthy'` 存在结果且无告警联动；`docker stats --no-stream` 显示某容器资源超 80% 限制值但无监控告警；无法发现被攻陷或资源耗尽的容器
- **合规规则编号**: Docker-60, Docker-61
- **攻击面关联**: AS-5

### CHK-CAND-149：Docker Swarm overlay 未加密+mTLS 缺失→集群管理流量嗅探与未授权节点加入

- **违规族**: Docker G_7（集群配置）— 通信安全子组
- **映射的攻击模式**: `network/swarm-sniff`, `auth/swarm-unauth-node`
- **严重等级**: high
- **前置条件**: `docker network inspect <overlay>` 显示 `Encrypted=false`；`docker info | grep -A5 Swarm` 未显示 TLS；`/var/lib/docker/swarm/certificates/` 无节点证书或已过期；mTLS 未启用，任意节点可加入集群获取调度权
- **合规规则编号**: Docker-62, Docker-63
- **攻击面关联**: AS-3, AS-2

### CHK-CAND-150：Docker Swarm autolock 未启用+管理密钥未轮换→离线密钥恢复

- **违规族**: Docker G_7（集群配置）— 密钥管理子组
- **映射的攻击模式**: `auth/swarm-key-recovery`, `persist/swarm-backdoor`
- **严重等级**: medium
- **前置条件**: `docker swarm update --autolock` 未启用，管理密钥明文存储在 `/var/lib/docker/swarm/` 磁盘上；`docker swarm ca` 显示证书从未轮换；被攻陷主机重启后可恢复集群控制
- **合规规则编号**: Docker-64
- **攻击面关联**: AS-2

### CHK-CAND-151：Containerd 版本过旧/组件缺失/无审计→已知漏洞与追溯盲区

- **违规族**: Containerd G_1（运行环境配置）
- **映射的攻击模式**: `escape/containerd-shim-escape`, `escape/runc-escape`
- **严重等级**: medium
- **前置条件**: `containerd --version` 为 1.4 及以下或含已知 CVE；`which containerd ctr containerd-shim` 任一缺失；`auditctl -l | grep containerd` 无审计规则，无法追溯配置篡改与异常操作
- **合规规则编号**: Containerd-1.1, Containerd-1.2, Containerd-1.3
- **攻击面关联**: AS-2, AS-4

### CHK-CAND-152：Containerd 插件未禁用+stream server 公网绑定+oom_score 未调→攻击面扩大与 DoS

- **违规族**: Containerd G_2（守护进程参数）
- **映射的攻击模式**: `auth/containerd-api-unauth`, `dos/oom-kill-runtime`
- **严重等级**: medium
- **前置条件**: `config.toml` 无 `disabled_plugins` 或为空（暴露不必要的 CRI 等插件接口）；`stream_server_address` 绑定 0.0.0.0 或非回环地址（可被远程调用 API）；`oom_score` 未设负值，OOM killer 优先终止 containerd 导致所有容器中断
- **合规规则编号**: Containerd-2.1, Containerd-2.2, Containerd-2.3
- **攻击面关联**: AS-2, AS-5

### CHK-CAND-153：Containerd containerd.sock 权限/属主宽松→socket 逃逸与容器接管

- **违规族**: Containerd G_3（文件权限）— socket 子组
- **映射的攻击模式**: `escape/socket-escape`, `escape/containerd-shim-escape`
- **严重等级**: critical
- **前置条件**: `stat -c '%a' /run/containerd/containerd.sock` 宽松于 660（如 666/777）；属主非 `root:root`；任意本地用户可读写 socket，通过 `ctr run` 创建/管理容器实现逃逸
- **合规规则编号**: Containerd-3.1, Containerd-3.2
- **攻击面关联**: AS-1

### CHK-CAND-154：Containerd config.toml/证书/二进制/服务文件权限宽松→配置篡改与中间人

- **违规族**: Containerd G_3（文件权限）— 配置与证书子组
- **映射的攻击模式**: `auth/containerd-config-tamper`, `network/mitm`, `escape/binary-backdoor`
- **严重等级**: high
- **前置条件**: `config.toml` 权限宽松于 600 或属主非 root:root（可篡改运行时安全策略）；CA 证书权限宽松于 644（可替换 CA 实施中间人）；私钥权限宽松于 600（可解密运行时通信或伪造服务端身份）；`/var/lib/containerd` 或 `/run/containerd` 宽松于 700（可浏览容器镜像层与运行时状态）；containerd 二进制权限宽松于 755 或属主非 root（可植入后门实现主机逃逸）；containerd.service 文件权限宽松于 644（可注入恶意启动参数）
- **合规规则编号**: Containerd-3.3, Containerd-3.4, Containerd-3.5, Containerd-3.6, Containerd-3.7, Containerd-3.8, Containerd-3.9, Containerd-3.10
- **攻击面关联**: AS-2, AS-4, AS-1

### CHK-CAND-155：Containerd 镜像无签名验证+非最小化→供应链篡改与攻击面扩大

- **违规族**: Containerd G_4（镜像构建）
- **映射的攻击模式**: `supply/image-tag-mutation`, `supply/registry-poison`
- **严重等级**: medium
- **前置条件**: `config.toml` 无镜像签名验证配置（cosign/notation/原生 verify 缺失）；`ctr images ls` 显示大量非必要镜像或 latest 标签镜像；镜像含调试工具与冗余软件包，被入侵后可被攻击者利用进行横向移动
- **合规规则编号**: Containerd-4.1, Containerd-4.2
- **攻击面关联**: AS-4, AS-6

### CHK-CAND-156：Containerd 容器特权模式+危险 capabilities→直接宿主机逃逸

- **违规族**: Containerd G_5（容器运行时）— 特权与 capabilities 子组
- **映射的攻击模式**: `escape/cgroup-escape`, `escape/capability-privesc`, `escape/hostpath-mount`
- **严重等级**: critical
- **前置条件**: `crictl inspect <c>` 显示 `privileged: true`（容器直接访问主机设备、可加载内核模块）；capabilities 列表含 SYS_ADMIN/SYS_PTRACE/NET_ADMIN/SYS_MODULE 而未 drop ALL；容器内 `cat /proc/1/status | grep CapEff` 为 `0000003fffffffff`
- **合规规则编号**: Containerd-5.3, Containerd-5.4
- **攻击面关联**: AS-1

### CHK-CAND-157：Containerd 无 seccomp/MAC/只读根/root 运行→逃逸面放大

- **违规族**: Containerd G_5（容器运行时）— 隔离子组
- **映射的攻击模式**: `escape/cgroup-escape`, `escape/procfs-escape`, `escape/capability-privesc`
- **严重等级**: high
- **前置条件**: `crictl inspect <c>` seccomp 为 unconfined 或未配置（允许 mount/keyctl 等逃逸系统调用）；SELinux/AppArmor 为 unconfined 或无 MAC 标签；根文件系统可写（`readonly_rootfs` 未启用，可植入后门）；`runAsUser` 为 0（root 运行，逃逸后直接获得宿主机 UID 0）
- **合规规则编号**: Containerd-5.2, Containerd-5.5, Containerd-5.6, Containerd-5.9
- **攻击面关联**: AS-1

### CHK-CAND-158：Containerd 无资源限制+无 PID 限制+hostNetwork+无 ulimit→DoS 与网络逃逸

- **违规族**: Containerd G_5（容器运行时）— 资源与网络子组
- **映射的攻击模式**: `dos/resource-abuse`, `dos/fork-bomb`, `network/lateral-move`, `network/cloud-metadata`
- **严重等级**: medium
- **前置条件**: 容器无 CPU/内存/IO limits（`crictl inspect` 无 cpu_limit/memory_limit）；`pids_limit` 为 0（无限制，可 fork bomb 耗尽主机 PID）；`hostNetwork: true`（可直接访问宿主机网络栈，嗅探流量与云元数据端点）；容器无 ulimit 限制（可耗尽文件描述符与进程数）
- **合规规则编号**: Containerd-5.1, Containerd-5.7, Containerd-5.8, Containerd-5.10
- **攻击面关联**: AS-5, AS-3

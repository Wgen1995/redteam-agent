---
source: manual
confidence: high
platforms: [docker]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.3]
mapped_compliance_families: [Pod启动安全]
---

# 通过 Docker Volume 持久化

## 1. 前置条件

- Docker Volume 挂载到可写目录
- 容器可写入 Volume 数据
- Volume 在容器删除后保留数据（Docker Volume 默认行为）
- 宿主机有 Docker 访问权限

## 2. 探测命令

- [L0] `docker volume ls` → 期望：列出所有 Docker Volume，发现异常条目
- [L0] `docker volume inspect <volume>` → 期望：显示 Volume 挂载路径和创建时间
- [L0] `docker ps -a --filter volume=<volume>` → 期望：发现使用该 Volume 的容器
- [L0] `docker inspect <container> --format '{{json .Mounts}}' | jq '.[] | select(.Type=="volume")'` → 期望：发现容器挂载的 Volume
- [L1] 经过容器内部：`ls -la /<mount-path>` → 期望：发现持久化文件（后门脚本、SSH 密钥等）

## 3. 攻击验证

- [L2] 检查 Volume 中的可疑文件：
  `docker run --rm -v <volume>:/data alpine ls -la /data/` → 期望：发现持久化的恶意文件
- [L2] 验证 Volume 持久化机制：
  `docker run --rm -v <volume>:/data alpine cat /data/<suspicious-file>` → 期望：读取到持久化的恶意脚本或配置
- [L2] 检查宿主机 Volume 路径：
  `docker volume inspect <volume> --format '{{.Mountpoint}}'` → 期望：返回宿主机路径（如 `/var/lib/docker/volumes/<volume>/_data`）
- [L2] 在宿主机上检查 Volume 内容：
  `ls -la /var/lib/docker/volumes/<volume>/_data/` → 期望：发现持久化的可疑文件

## 4. 差分证明

- 攻击前 [L0]: Docker Volume 列表无异常条目
- 攻击后 [L2]: 新增 Volume 或现有 Volume 中出现恶意文件
- 对比：容器被删除后，Volume 中的数据仍保留，下次挂载时自动恢复
- 攻击前 [L1]: 容器内无持久化后门文件
- 攻击后 [L2]: Volume 中出现 .bashrc 修改、SSH 授权密钥、cron 任务等持久化内容

## 5. 绕过策略

- 若 Volume 权限受限：利用特权容器修改 Volume 内容
- 若 Docker 限制 volume create：检查是否可以使用 bind mount（`-v /host/path:/container/path`）
- 若 Volume 被监控：使用命名卷（named volume）替代 bind mount 以隐藏实际路径
- 若仅能使用现有 Volume：在已有 Volume 中注入恶意文件（如 `.bashrc`、`.ssh/authorized_keys`）

## 6. 证伪条件

- [L0] `docker volume ls` 无异常 Volume → 需进一步检查现有 Volume 内容
- [L0] 所有 Volume 均为预期容器创建 → 证伪（若无内容可疑）
- [L0] Docker 应用了只读 Volume 策略（`-v <volume>:/data:ro`）→ 证伪（无法写入持久化数据）
- [L1] 容器内挂载路径为只读文件系统 → 证伪

## 7. 审批级别

Level 1：只读命令（docker volume ls, docker volume inspect）自动通过。
Level 2：攻击验证（检查 Volume 内容）自动通过。
destructive: false

## 8. MITRE ATT\&CK

T1543 - Create or Modify System Process（通过 Docker Volume 持久化恶意数据）
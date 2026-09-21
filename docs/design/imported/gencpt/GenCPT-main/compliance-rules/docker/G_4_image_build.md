# G_4 Docker 镜像构建（7 条）

CIS Docker Benchmark v1.6.0 — 4 Container Images 部分。
覆盖 Docker-27 至 Docker-33，共 7 条规则。

---

### Docker-27 创建非 root 用户

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{.Config.User}}' \"$c\" 2>/dev/null; done | sort | uniq -c")
```

**期望值**: 容器以非 root 用户运行（如 `appuser`、`1000`），不应为空或 `root`
**判定标准**: pass=容器配置了非 root User 指令，fail=容器以 root 用户运行或未指定 User，na=特权容器必须使用 root
**修复建议**: 在 Dockerfile 中添加：
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```
或运行时指定：`docker run --user 1000:1000 image`
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.1 "Ensure that a user for the container has been created"
**攻击面关联**: AS-1 容器逃逸（容器内 root 在逃逸后直接获得宿主机 root 权限，非 root 用户大幅降低逃逸影响）

---

### Docker-28 apt 清理缓存

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'ls -la /var/cache/apt/ /var/lib/apt/lists/ 2>/dev/null | head -5; du -sh /var/cache/apt/ /var/lib/apt/lists/ 2>/dev/null' 2>/dev/null; done")
```

进一步检查镜像层：
```bash
ssh_execute(server, "docker history --no-trunc $(docker images -q | head -1) 2>/dev/null | grep -i 'rm\\|clean\\|flush' | head -5")
```

**期望值**: 镜像中不包含 apt 缓存文件
**判定标准**: pass=apt 缓存已被清理（/var/cache/apt/ 和 /var/lib/apt/lists/ 为空或很小），fail=镜像中包含大量 apt 缓存，na=非 Debian/Ubuntu 基础镜像
**修复建议**: 在 Dockerfile 中添加清理指令：
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends package && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
```
或在独立 RUN 层中清理：
```dockerfile
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.2 "Ensure that containers use only trusted base images"（镜像最小化）
**攻击面关联**: AS-4 数据泄露（缓存中可能含包索引元数据和已知漏洞信息，增加攻击面）

---

### Docker-29 无 sudoers

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'test -f /etc/sudoers && echo EXISTS || echo NOT_FOUND; ls /etc/sudoers.d/ 2>/dev/null | wc -l' 2>/dev/null; done")
```

**期望值**: 容器中不存在 sudo 或 sudoers 配置
**判定标准**: pass=容器中无 /etc/sudoers 文件和 sudo 二进制，fail=容器中存在 sudo 或 sudoers 配置，na=容器需要 sudo（极少见）
**修复建议**: 在 Dockerfile 中移除 sudo：
```dockerfile
RUN apt-get remove -y sudo && rm -rf /etc/sudoers /etc/sudoers.d/
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.5 "Ensure that sudo is not used in the container"（最佳实践）
**攻击面关联**: AS-1 容器逃逸（容器内 sudo 允许低权限用户提权，逃逸后影响扩大）

---

### Docker-30 无 SSH 服务

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'which sshd 2>/dev/null && echo SSHD_FOUND || echo NO_SSHD; which ssh 2>/dev/null && echo SSH_FOUND || echo NO_SSH' 2>/dev/null; done")
```

进一步检查运行中的 sshd 进程：
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'ps aux | grep sshd | grep -v grep || echo NO_SSHD_PROCESS' 2>/dev/null; done")
```

**期望值**: 容器中不包含 sshd 服务
**判定标准**: pass=容器中无 sshd 二进制和运行进程，fail=容器中存在 sshd，na=容器用途为 SSH 跳板
**修复建议**: 在 Dockerfile 中移除 SSH：
```dockerfile
RUN apt-get remove -y openssh-server openssh-client && \
    rm -rf /etc/ssh /usr/sbin/sshd
```
使用 `docker exec` 代替 SSH 进入容器
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.6 "Ensure that SSH is not running in the container"
**攻击面关联**: AS-3 网络攻击（容器内 SSH 服务增加攻击面，提供持久化后门通道）

---

### Docker-31 无密码哈希

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'cat /etc/shadow 2>/dev/null | grep -v \"^root:\\!:\\|^root:\\*:\\|^nobody\" | grep -v \"::\\|!\\|\\*\" | wc -l' 2>/dev/null; done")
```

进一步检查 /etc/passwd 中的可登录用户：
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker exec \"$c\" sh -c 'cat /etc/passwd | awk -F: \".\\$7\\\"/bin/bash\\\"||\\$7\\\"/bin/sh\\\"{print \\$1}\"' 2>/dev/null; done")
```

**期望值**: 容器 /etc/shadow 中无有效密码哈希（所有条目应为 `!`、`*` 或 `!!`）
**判定标准**: pass=无可登录密码的账户，fail=存在带密码哈希的账户，na=容器无 /etc/shadow（如 Alpine 最小镜像）
**修复建议**: 在 Dockerfile 中锁定所有账户密码：
```dockerfile
RUN passwd -l root 2>/dev/null; \
    for u in $(awk -F: '$7 !~ /(nologin|false)/ {print $1}' /etc/passwd); do passwd -l $u 2>/dev/null; done
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.7 "Ensure that privileged ports are not used in the container"（关联安全基线）
**攻击面关联**: AS-2 认证授权（密码哈希可被暴力破解用于容器横向移动）

---

### Docker-32 HEALTHCHECK 指令

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{.Config.Healthcheck}}' \"$c\" 2>/dev/null; done | sort | uniq -c")
```

进一步检查所有镜像：
```bash
ssh_execute(server, "docker inspect --format '{{.Config.Healthcheck}}' $(docker images -q) 2>/dev/null | grep -v '<nil>' | wc -l")
```

**期望值**: 容器/镜像配置了 HEALTHCHECK 指令
**判定标准**: pass=容器或镜像配置了 HEALTHCHECK，fail=无 HEALTHCHECK 配置，na=编排系统（如 Kubernetes）已提供健康检查
**修复建议**: 在 Dockerfile 中添加：
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.8 "Ensure that HEALTHCHECK instructions have been added to container images"
**攻击面关联**: AS-5 可用性（无 HEALTHCHECK 时无法自动检测和替换被攻陷或僵死的容器）

---

### Docker-33 不存储 secrets

**检查命令 [L0]**:
```bash
ssh_execute(server, "for c in $(docker ps -q); do docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' \"$c\" 2>/dev/null | grep -iE 'password|secret|token|key|credential|api_key|access_key|private_key' | head -5; done")
```

进一步检查镜像历史中的 secrets：
```bash
ssh_execute(server, "for img in $(docker images -q | head -5); do docker history --no-trunc \"$img\" 2>/dev/null | grep -iE 'password|secret|token|key' | head -3; done")
```

**期望值**: 容器环境变量和镜像历史中不含 secrets
**判定标准**: pass=未在环境变量或镜像层中发现 secrets，fail=在环境变量或镜像层中发现密码/密钥，na=无容器运行
**修复建议**: 使用 Docker Secrets 或外部密钥管理系统代替环境变量：
```bash
# 使用 Docker Secrets（Swarm 模式）
docker secret create db_password ./password.txt
docker service create --secret db_password myapp

# 或使用 --env-file 配合外部 vault
docker run --env-file <(vault read -field=value secret/myapp/db_pass) myapp
```
在 Dockerfile 中杜绝硬编码 secrets：
```dockerfile
# 错误示范：不要这样做
# ENV DB_PASSWORD=hardcoded_secret

# 正确做法：运行时注入
ENV DB_PASSWORD=""
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 4.10 "Ensure that secrets are not stored in container images"
**攻击面关联**: AS-4 数据泄露（镜像中的 secrets 可通过 docker inspect、docker history 等命令直接获取）
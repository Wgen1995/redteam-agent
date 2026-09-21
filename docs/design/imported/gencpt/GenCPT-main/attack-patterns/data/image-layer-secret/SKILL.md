---
source: manual
confidence: high
platforms: [docker, containerd]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-4.3]
mapped_compliance_families: [镜像构建]
---

# 镜像层密钥泄露

## 1. 前置条件

- Docker 镜像构建过程中将敏感信息写入镜像层
- 镜像历史中包含硬编码的密码、API Key、SSH 密钥等
- `docker history --no-trunc` 可显示完整的构建命令和参数
- `.dockerignore` 未排除敏感文件（如 `.env`、`id_rsa`、`*.pem`）

## 2. 探测命令

- [L0] `docker history --no-trunc <image>` → 期望：显示完整构建命令，包含 SECRET、PASSWORD、API_KEY 等敏感信息
- [L0] `docker history --no-trunc <image> | grep -iE 'COPY|ADD|ENV|ARG|RUN.*secret|RUN.*password|RUN.*key'` → 期望：发现复制敏感文件或设置敏感变量的层
- [L0] `docker inspect <image> --format '{{range .Config.Env}}{{println .}}{{end}}'` → 期望：发现镜像构建时设置的敏感环境变量
- [L1] `docker exec <container> cat /root/.ssh/id_rsa 2>/dev/null || echo "not found"` → 期望：发现构建时残留的 SSH 密钥
- [L1] `docker exec <container> ls -la /app/.env /app/config/production.yml /app/secrets/ 2>/dev/null` → 期望：发现构建时复制的敏感文件

## 3. 攻击验证

- [L2] 提取镜像层完整内容：
  `docker save <image> -o /tmp/image.tar && tar xf /tmp/image.tar -C /tmp/image-layers` → 期望：解压后每层包含 layer.tar
- [L2] 检查每层的文件内容：
  `for layer in /tmp/image-layers/*/layer.tar; do tar tf "$layer" | grep -iE '\.env|secret|password|key|pem|rsa' && echo "=== $layer ==="; done` → 期望：发现某层包含敏感文件
- [L2] 检查 BuildKit 缓存：
  `docker buildx du --verbose | grep -iE 'secret|password|key'` → 期望：发现 BuildKit 缓存中的敏感信息
- [L2] 检查镜像层中的 ENV/ARG 泄露：
  `for layer in /tmp/image-layers/*/layer.tar; do tar xf "$layer" -C /tmp/layer-inspect && cat /tmp/layer-inspect/Dockerfile 2>/dev/null || true; done` → 期望：发现构建 Dockerfile 中的敏感 ARG/ENV

## 4. 差分证明

- 攻击前 [L0]: `docker history --no-trunc <image>` 显示构建命令中包含 COPY .env 或 ARG SECRET_KEY
- 攻击后 [L2]: 从镜像层 tar 中提取出包含明文密码的 `.env` 文件或 SSH 密钥
- 对比：
  - 构建者可能已删除文件（`RUN rm .env`），但前一层仍包含该文件
  - `docker history` 显示删除步骤，但底层 tar 仍可恢复

## 5. 绕过策略

- 若 `docker history` 被截断：使用 `--no-trunc` 参数或直接 `docker inspect` 获取配置
- 若使用多阶段构建：检查中间阶段镜像是否被保留（`docker images -a`）
- 若使用 BuildKit：检查 `docker buildx du` 缓存中的敏感数据
- 若镜像被推送到私有仓库：通过 `crane` 或 `skopeo` 拉取清单检查层信息

## 6. 证伪条件

- [L0] `docker history --no-trunc <image>` 无敏感命令（无 COPY .env、无 ARG/ENV 设置密码）→ 证伪
- [L2] 提取的所有镜像层中无不包含敏感文件 → 证伪
- [L0] Dockerfile 使用多阶段构建且最终镜像仅包含编译产物 → 证伪（中间层敏感信息已被丢弃）
- [L1] 容器内 `/proc/1/environ` 和文件系统中无可读的敏感文件 → 证伪

## 7. 审批级别

Level 2：探测命令（docker history, docker inspect）自动通过。
Level 2：攻击验证（提取镜像层内容）自动通过。
destructive: false

## 8. MITRE ATT&CK

T1552 - Unsecured Credentials（从 Docker 镜像层泄露凭证）
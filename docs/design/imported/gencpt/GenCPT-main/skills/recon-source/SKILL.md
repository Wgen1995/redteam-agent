---
name: recon-source
description: >
  容器安全源码扫描。扫描本地Dockerfile、K8s清单、Helm Chart、CI/CD配置等文件，
  提取安全相关配置并结构化摘要。补充SSH远程侦察的盲区。
  使用场景：渗透测试源码辅助侦察阶段。
  不使用场景：无源码访问权限、只做远程检测。
---

## §0 套件根定位（启动第一步，强制）

本 SKILL 中所有相对路径（`skills/shared/`、`attack-patterns/`、`compliance-rules/`、`hypothesis-libraries/`、`references/`）均**相对套件根**，不相对 cwd。

**错误示例**（实际发生过）：SKILL 写 `skills/shared/SSH_COMMANDS.md`，LLM 拿 cwd `~/.config/opencode/skills/` 拼接 → 解析为 `~/.config/opencode/skills/shared/SSH_COMMANDS.md`（丢失套件根段 `gencpt/`）→ Read 失败。正确应为 `~/.config/opencode/skills/gencpt/skills/shared/SSH_COMMANDS.md`。

**若入口已传入套件根绝对路径**：直接用作前缀拼接所有相对路径，**不重复 Glob**。

**若未传入套件根**：用 Glob 工具定位，按以下顺序尝试首个命中：
- Pattern 1: `**/skills/shared/SSH_COMMANDS.md` → 套件根 = 命中路径向上两级
- Pattern 2: `**/gencpt/SKILL.md` → 套件根 = 命中路径父目录
- Pattern 3: `**/GenCPT*/SKILL.md` → 套件根 = 命中路径父目录

所有 Read 调用拼接套件根前缀：`skills/shared/X.md` → Read `{套件根}/skills/shared/X.md`。**禁用 `$ROOT/...` 变量形式**，Read 工具不展开 shell 变量。**不许凭记忆猜套件根路径**。

---

# recon-source（Phase 1b — 源码扫描）

## MUST 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| source_path | string | 是* | 源码目录本地路径 |
| source_type | string | 否 | 扫描类型过滤，默认 `all`。可选：`dockerfile`, `k8s`, `helm`, `cicd`, `env`, `all` |

\* `source_path` 与 `source_url` 二选一，必须提供其中一个。当前仅支持 `source_path`（本地目录路径）。

## 核心工作流

### 步骤1：扫描范围确定

使用 `find` 命令扫描 `source_path` 目录，定位容器安全相关文件。**只扫描以下文件类型，不扫描业务代码**：

| 文件类型 | glob 模式 | 优先级 |
|---------|-----------|--------|
| Dockerfile | `**/Dockerfile*` | P0-强制 |
| docker-compose | `**/docker-compose*.yml`, `**/docker-compose*.yaml` | P0-强制 |
| K8s 清单 | `**/*.yaml`（含 Deployment/StatefulSet/DaemonSet/Job/CronJob/Pod/Service/Ingress/NetworkPolicy/RBAC/SA 等） | P1-按优先级分级 |
| Helm Chart | `**/Chart.yaml`, `**/values.yaml`, `**/templates/*.yaml` | P1-按优先级分级 |
| CI/CD 配置 | `**/Jenkinsfile`, `**/.gitlab-ci.yml`, `**/.github/workflows/*.yml`, `**/.circleci/config.yml` | P1-按优先级分级 |
| .env 文件 | `**/.env`, `**/.env.*` | P0-强制 |
| .dockerignore | `**/.dockerignore` | P0-强制 |

**K8s 清单识别**：对每个 YAML 文件，检查是否含 `apiVersion` + `kind` 字段，仅含以下 kind 的文件纳入扫描：
- Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob
- Service, Ingress, NetworkPolicy
- Role, RoleBinding, ClusterRole, ClusterRoleBinding
- ServiceAccount, ConfigMap, Secret（不含值，只检查元数据）

**排除规则**：
- 排除 `.git/`、`node_modules/`、`vendor/`、`__pycache__/`、`.gradle/`、`.terraform/` 目录
- 排除二进制文件和图片文件
- 排除超过 1MB 的单个文件（超大文件不适合 LLM 上下文）

### 步骤2：两级扫描策略执行

**判断文件总数**：

```
总文件数 ≤ 200 → 全量扫描（所有匹配文件均纳入）
总文件数 > 200 → 两级策略
```

**两级策略（文件数 > 200 时）**：

#### 第一级：强制扫描（高价值文件，预估 <50 个）

| 文件类型 | 扫描深度 |
|---------|---------|
| Dockerfile / Dockerfile.* | 全量扫描：逐行检查安全相关指令 |
| docker-compose.yml / docker-compose.yaml | 全量扫描 |
| .env / .env.* | 全量扫描：逐行检查密钥泄露 |
| .dockerignore | 全量扫描 |

#### 第二级：K8s 清单按优先级分级扫描

| 优先级 | 匹配条件 | 扫描深度 |
|--------|---------|---------|
| P1 | 含 `securityContext` 的 YAML | 全量扫描 |
| P2 | 含 `hostPath` / `hostNetwork` / `hostPID` / `hostIPC` 的 YAML | 全量扫描 |
| P3 | 含 `serviceAccountName` / `automountServiceAccountToken` 的 YAML | 全量扫描 |
| P4 | 其他 K8s 清单 | 只提取 `apiVersion/kind/name/namespace` 元数据（2-3行） |

#### 第三级：跳过

- 所有业务代码（.js, .py, .java, .go, .rs 等源代码文件）— 不扫描
- 测试代码 — 不扫描
- 文档文件 — 不扫描

**Helm Chart 和 CI/CD 配置**在两级策略中：
- `Chart.yaml`：P1 级（全量扫描）
- `values.yaml`：P1 级（全量扫描）
- `templates/` 下 YAML：按 K8s 清单同等优先级规则
- CI/CD 配置：P2 级（全量扫描）

### 步骤3：结构化摘要提取

对每个文件提取安全相关摘要，严格控制上下文占用：

**摘要格式**（每个文件 5-10 行）：

```markdown
## [文件路径] (行数: N)

- **类型**: Dockerfile / K8s-Deployment / K8s-NetworkPolicy / Helm-values / CI-CD / env
- **风险点**:
  - [具体安全问题1]: [简要描述] (severity: Critical/High/Medium/Low)
  - [具体安全问题2]: [简要描述] (severity: ...)
- **安全配置摘要**: [关键安全相关配置的2-3行浓缩]
```

**无风险文件**也需记录（1行摘要）：

```markdown
## [文件路径] (行数: N)
- **类型**: K8s-Deployment | 无显著安全问题
```

**Token 预算硬约束**：
- 每个文件摘要 5-10 行
- 总摘要大小 **≤ 8000 tokens**
- 遇到压缩风险时，优先保留 Critical 和 High 严重性问题
- Low 严重性发现可合并为一行汇总

### 步骤4：数据写入

将扫描结果写入以下 4 个文件：

1. **knowledge_graph/nodes/source_findings.json** — 源码安全发现节点
2. **knowledge_graph/edges/source_edges.json** — 源码-运行时关联边
3. **evidence/recon/source_analysis.md** — 源码分析详细报告
4. **evidence/recon/source_scan_stats.md** — 扫描统计信息

## 扫描重点

### Dockerfile

| 检查项 | 安全关注点 | 严重性基准 |
|--------|-----------|-----------|
| `USER` 指令 | 缺少 USER 或 USER root → 容器以 root 运行 | High |
| `RUN` 中的特权操作 | `apt-get update` 未在同一行 `rm` 缓存、`chmod 777`、`chown` 过大范围 | Medium |
| `ADD` vs `COPY` | ADD 会自动解压远程 URL，有供应链注入风险 | Low |
| 基础镜像版本 | 使用 `latest` 标签、过旧的基础镜像、未经校验的镜像仓 | High |
| 硬编码密钥 | `ENV` 或 `ARG` 中含密码、token、API key 等敏感值 | Critical |
| 安装危险工具 | `RUN` 中安装 curl/wget/netcat/sudo 等可能在运行时被利用的工具 | Medium |
| 多阶段构建 | 缺少多阶段构建导致最终镜像包含构建工具和中间产物 | Low |
| `.dockerignore` | 没有 `.dockerignore` 或内容不包含 `.git` 和敏感文件 | Medium |

### K8s 清单

| 检查项 | 安全关注点 | 严重性基准 |
|--------|-----------|-----------|
| `securityContext` | `privileged: true`、`runAsUser: 0`、缺失 `runAsNonRoot`、缺失 `readOnlyRootFilesystem` | Critical/High |
| `hostPath` | 挂载 `/`、`/etc`、`/var/run/docker.sock`、`/proc`、`/sys` 等敏感路径 | Critical |
| `hostNetwork` / `hostPID` / `hostIPC` | 设为 true 共享宿主机命名空间 | High |
| `capabilities` | `add` 含 `SYS_ADMIN`、`SYS_PTRACE`、`NET_ADMIN`、`DAC_OVERRIDE` 等危险 capability | Critical/High |
| `serviceAccountName` | 使用 `default` SA 或 SA 拥有过多权限 | High |
| `automountServiceAccountToken` | 设为 `false` 或缺失 | High |
| 资源限制 | 缺失 `resources.limits`（cpu/memory） | Medium |
| `imagePullPolicy` | 使用 `IfNotPresent` 且镜像标签为 `latest` | Low |

### Helm Chart

| 检查项 | 安全关注点 | 严重性基准 |
|--------|-----------|-----------|
| `values.yaml` 安全配置 | 上述 K8s 检查项在 values 中的默认值 | 同 K8s |
| `templates/` 中的安全上下文 | 模板中硬编码或默认缺失 securityContext | 同 K8s |
| `values.yaml` 中的镜像引用 | 使用 latest 标签或未验证的镜像源 | High |
| `values.yaml` 中的凭证 | 明文存储数据库密码、API key 等 | Critical |

### CI/CD 配置

| 检查项 | 安全关注点 | 严重性基准 |
|--------|-----------|-----------|
| 镜像构建参数 | `--no-cache`、`--privileged` 构建参数 | Medium |
| 推送凭证 | CI/CD 中硬编码的 Docker registry 密码/token | Critical |
| 部署目标 | 生产环境直接部署无审批流程 | High |
| Secret 管理 | CI/CD 变量中明文密钥而非使用 vault/sealed-secrets | High |
| 安全扫描步骤 | 缺少镜像扫描、SAST、依赖检查步骤 | Medium |

### .env 文件

| 检查项 | 安全关注点 | 严重性基准 |
|--------|-----------|-----------|
| 数据库密码 | `DB_PASSWORD`、`MYSQL_ROOT_PASSWORD` 等明文密码 | Critical |
| API 密钥 | `API_KEY`、`SECRET_KEY`、`TOKEN` 等明文密钥 | Critical |
| 私钥 | `PRIVATE_KEY`、`SSH_KEY` 等明文密钥 | Critical |
| 内部端点 | `DATABASE_URL`、`REDIS_URL` 暴露内部网络拓扑 | Medium |
| 调试标志 | `DEBUG=true`、`LOG_LEVEL=debug` 在生产配置中 | Low |

## MUST 输出

### 1. knowledge_graph/nodes/source_findings.json

```json
{
  "session_id": "sess-YYYYMMDD-NNN",
  "source_type": "local_path",
  "source_path": "/path/to/repo",
  "scan_time": "ISO8601",
  "file_count": 0,
  "findings": [
    {
      "id": "src-001",
      "node_type": "source_finding",
      "file_path": "deploy/Dockerfile",
      "line_range": [1, 45],
      "finding_type": "dockerfile-privileged-user",
      "severity": "High",
      "description": "容器以 root 运行，缺少 USER 指令",
      "remediation": "添加 USER non-root 指令"
    }
  ]
}
```

### 2. knowledge_graph/edges/source_edges.json

```json
{
  "session_id": "sess-YYYYMMDD-NNN",
  "edges": [
    {
      "edge_type": "source_to_runtime",
      "from_node": "src-001",
      "to_node": "pod-backend-api-deployment-abc123",
      "relationship": "manifest_defines_security_context",
      "attrs": {
        "detail": "Dockerfile 缺少 USER 指令 → Pod securityContext.runAsUser 未设置 → 运行时以 root 运行"
      }
    },
    {
      "edge_type": "source_correlation",
      "from_node": "src-001",
      "to_node": "src-003",
      "relationship": "same_security_issue",
      "attrs": {
        "issue": "root 用户运行",
        "files": ["deploy/Dockerfile", "k8s/deployment.yaml"]
      }
    }
  ]
}
```

**边的类型**：
- `source_to_runtime`：源码发现 → 运行时对象（Pod/容器）的关联。用于 Phase 3 交叉关联，将构建时问题与运行时问题关联。
- `source_correlation`：源码发现之间的关联。同一安全问题在多个文件中出现时建立关联。

### 3. evidence/recon/source_analysis.md

```markdown
# 源码安全分析报告

## 扫描概要

- **源码路径**: /path/to/repo
- **扫描时间**: YYYY-MM-DD HH:MM:SS
- **匹配文件总数**: N
- **扫描策略**: 全量扫描 / 两级策略
- **发现总数**: X (Critical: Y, High: Z, Medium: W, Low: V)

## Critical 发现

### [CRIT-001] 标题
- **文件**: path/to/file
- **行号**: L10-L15
- **问题**: 具体描述
- **影响**: 安全影响说明
- **修复建议**: 具体修复方案

## High 发现
...(同上格式)

## 按文件类型汇总

### Dockerfile (N 个文件)
| 文件 | 风险点数 | 最高严重性 |
|------|---------|-----------|
| ... | ... | ... |

### K8s 清单 (N 个文件)
| 文件 | 风险点数 | 最高严重性 |
|------|---------|-----------|

### Helm Chart (N 个文件)
### CI/CD 配置 (N 个文件)
### .env 文件 (N 个文件)

## 源码-运行时关联

列出所有 `source_to_runtime` 边，说明构建时问题与运行时问题的关联关系。

## 详细扫描摘要

(步骤3 中每个文件的 5-10 行摘要)
```

### 4. evidence/recon/source_scan_stats.md

```markdown
# 源码扫描统计

## 扫描范围

| 指标 | 值 |
|------|-----|
| 源码路径 | /path/to/repo |
| 匹配文件总数 | N |
| 实际扫描文件数 | M |
| 跳过文件数 | K |
| 扫描策略 | 全量 / 两级策略 |

## 文件类型分布

| 文件类型 | 匹配数 | 扫描数 | 跳过数 |
|---------|--------|--------|--------|
| Dockerfile | ... | ... | ... |
| docker-compose | ... | ... | ... |
| K8s 清单 | ... | ... | ... |
| Helm Chart | ... | ... | ... |
| CI/CD 配置 | ... | ... | ... |
| .env 文件 | ... | ... | ... |
| .dockerignore | ... | ... | ... |

## 优先级分布（两级策略时）

| 优先级 | 文件数 | 扫描深度 |
|--------|--------|---------|
| P0-强制 | ... | 全量 |
| P1 | ... | 全量 |
| P2 | ... | 全量 |
| P3 | ... | 全量 |
| P4 | ... | 仅元数据 |

## 发现统计

| 严重性 | 数量 | 占比 |
|--------|------|------|
| Critical | ... | ...% |
| High | ... | ...% |
| Medium | ... | ...% |
| Low | ... | ...% |

## 文件类型风险排名

| 排名 | 文件类型 | Critical+High 数 | 总发现数 |
|------|---------|-------------------|---------|
| 1 | ... | ... | ... |

## Token 预算使用

| 指标 | 值 |
|------|-----|
| 总摘要 Token 数 | N / 8000 |
| 压缩执行的 | 是/否 |
| 被压缩的严重性级别 | Low/Medium |
```

## 检查点

完成本 Phase 前必须通过以下三项检查：

1. **① 源码文件列表非空或明确无源码**
   - 扫描到至少 1 个匹配文件，或者明确确认 `source_path` 下无容器安全相关文件
   - 空结果也需写入 `source_scan_stats.md`（标注"无匹配文件"），不能跳过输出

2. **② JSON 文件结构完整**
   - `source_findings.json` 包含 `session_id`、`source_type`、`source_path`、`file_count`、`findings` 字段
   - `source_edges.json` 包含 `session_id`、`edges` 字段
   - 每个 finding 包含 `id`、`node_type`、`file_path`、`finding_type`、`severity`、`description` 字段
   - 每条边包含 `edge_type`、`from_node`、`to_node`、`relationship` 字段
   - 所有 `from_node`/`to_node` 引用的 ID 在对应节点文件中存在

3. **③ QA 结构校验通过**
   - 4 个 MUST 输出文件全部存在且非空
   - Token 预算未超限（总摘要 ≤ 8000 tokens）
   - 严重性标注全部来自 {Critical, High, Medium, Low} 集合
   - 无占位符未替换（无 `【xxx】`、`...`、`+N` 等）
   - finding ID 连续无遗漏

## 独立运行参数

```
/gencpt-recon-source --source-path /path/to/repo --source-type all
```

独立运行时，`source_path` 是必需参数。若为 Pipeline 调用，从 `session_config.json` 读取。

## 安全边界

- **只读操作**：本 Phase 不使用 SSH，不执行任何远程命令，不修改任何运行时环境
- **不扫描业务代码**：只扫描容器安全相关文件类型，不碰 Java/Python/Go/JS 等业务源码
- **不泄露密钥内容**：.env 和 CI/CD 中发现的密钥只记录"存在密钥类型"，不记录密钥值本身
- **摘要大小硬约束**：总摘要 ≤ 8000 tokens，超出时压缩 Low 严重性条目

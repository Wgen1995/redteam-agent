---
name: recon
description: >
  容器环境全光谱侦察。通过SSH远程收集集群结构、Pod规范、安全上下文、服务暴露等信息。
  使用场景：渗透测试第一步，绘制攻击面地图。
  不使用场景：已有完整侦察数据、只做单点合规检查。
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

# recon — Phase 1a 环境侦察

本 SKILL 负责容器环境的全光谱侦察，通过 SSH 远程收集集群结构、Pod 规范、安全上下文、服务暴露等信息，写入知识图谱节点与边，为后续合规检测和攻击验证提供数据基础。

---

## MUST 输入

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `server` | string | **是** | 目标服务器名称（来自 ssh-manager 配置） |
| `scope` | string | **是** | `k8s` / `docker` / `containerd` / `all`，逗号分隔多选 |

独立运行示例：`--server prod-k8s-01 --scope k8s,docker`

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/SSH_COMMANDS.md` | SSH 命令使用规范、执行上下文标注、限速与重试 |
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记、QA 校验 |

---

## 核心工作流

### 步骤 1：环境指纹识别

分批执行 SSH 命令（每批 5-7 条，间隔 2 秒），收集 OS/架构/内核/运行时版本。每个 SSH 命令输出**立即写盘**到 `evidence/recon/raw/`。

**详细命令清单详见 `references/ssh_commands.md`。**

### 步骤 2：集群结构收集

根据 scope 参数选择性收集集群结构信息（K8s/Docker/containerd），包括节点、Pod、RBAC、安全模块检测。

**详细命令清单详见 `references/ssh_commands.md`。**

### 步骤 3：安全上下文提取

从已写盘的原始数据（`evidence/recon/raw/`）Read 需要的部分，提取安全相关字段写入知识图谱节点。对每个字段使用五态标记（`[x]`/`[?]`/`[-]`/`[!]`/`[ ]`），Phase 1a 完成时**必须消灭**所有 `[ ]`。

**提取字段清单、五态标记规则、边提取详见 `references/security_context.md`。**

#### 3.4 字段完整性要求（强制）

以下字段完整性要求在步骤 3 提取时**必须满足**，不允许字段缺失（字段值不存在 ≠ 字段本身缺失）：

**SA 节点字段完整性**：

`service_accounts.json` 中每个 SA 节点的 `data` 必须包含 `secrets` 字段：
- `secrets` 为列表类型（JSON array）
- SA 无关联 Secret 时写空数组 `[]`
- 禁止 `secrets` 字段本身缺失（0/8 SA 有 secrets 字段的问题已修复）

**Pod security_context 字段完整性**：

`pods.json` 中每个 Pod 节点的 `data.security_context` 必须包含以下全部 13 个字段：

| # | 字段名 | 来源 | 值不存在时 |
|---|--------|------|-----------|
| 1 | `pod_sc` | Pod spec securityContext | `[?] 未设置` |
| 2 | `privileged` | Container securityContext | `[?] 未设置` |
| 3 | `runAsUser` | Pod/Container securityContext | `[?] 未设置` |
| 4 | `runAsGroup` | Pod/Container securityContext | `[?] 未设置` |
| 5 | `fsGroup` | Pod securityContext | `[?] 未设置` |
| 6 | `allowPrivilegeEscalation` | Container securityContext | `[?] 未设置` |
| 7 | `readOnlyRootFilesystem` | Container securityContext | `[?] 未设置` |
| 8 | `seccompProfile` | Pod/Container securityContext | `[?] 未设置` |
| 9 | `capabilities_add` | Container securityContext | `[?] 未设置` |
| 10 | `capabilities_drop` | Container securityContext | `[?] 未设置` |
| 11 | `hostNetwork` | Pod spec | `[?] 未设置` |
| 12 | `hostPID` | Pod spec | `[?] 未设置` |
| 13 | `hostIPC` | Pod spec | `[?] 未设置` |

**规则**：
- 字段值不存在时标 `[?] 未设置`，**不允许字段本身缺失**
- 字段值存在时按五态标记规则标注 `[x]`/`[-]`/`[!]`
- 6/11 Pod 缺 7 个 security_context 字段的问题已修复
- 门控 9（安全上下文完整性）校验此要求

### 步骤 4：数据写入与指纹生成

按类型分片写入 7 个 JSON 节点文件（hosts/pods/containers/services/service_accounts/secrets/findings）和边文件（infra.json），生成侦察摘要和环境指纹。

**数据写入格式、节点/边 JSON 模板、侦察摘要模板、环境指纹格式详见 `references/ssh_commands.md` 步骤 4。**

---

## 分批策略与限速

**SSH 限速、Pod/容器扫描分批、重试策略详见 `references/batching.md`。**

---

## MUST 输出

Phase 1a 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `knowledge_graph/nodes/hosts.json` | 主机节点（非空） |
| `knowledge_graph/nodes/pods.json` | Pod 节点（非空） |
| `knowledge_graph/nodes/containers.json` | 容器节点（非空） |
| `knowledge_graph/nodes/services.json` | Service 节点 |
| `knowledge_graph/nodes/service_accounts.json` | SA 节点（非空） |
| `knowledge_graph/nodes/secrets.json` | Secret 节点（仅名称+类型，**绝不存储内容**） |
| `knowledge_graph/nodes/findings.json` | 发现节点（占位结构，Phase 2 填充） |
| `knowledge_graph/nodes/_index.md` | 节点总索引 |
| `knowledge_graph/edges/infra.json` | 基础设施关系边 |
| `knowledge_graph/edges/_index.md` | 边总索引 |
| `evidence/recon/recon_summary.md` | 侦察摘要 |
| `evidence/recon/completeness_gates.json` | 采集完整性门控结果（9 项门控的通过/blocked 状态） |
| `evidence/recon/raw/` | 原始 SSH 输出（非空，每段带来源与时间戳） |
| `session_config.json` | 必须含 `env_fingerprint` |

---

### 采集完整性门控（Phase 1a 完成时强制执行）

在 Phase 1a 数据写入完成后、标 complete 之前，强制执行以下 9 项采集完整性门控。每项门控用 `ssh_execute` 获取实际数量，与已写入 KG 的节点数对比。

| # | 门控名称 | 对比方式 | 通过条件 |
|---|---------|---------|---------|
| 1 | Pod 采集完整性 | `ssh_execute(server, "kubectl get pods -A --no-headers \| wc -l")` vs `jq length pods.json` | pods.json 节点数 = kubectl get pods -A count |
| 2 | SA 采集完整性 | `ssh_execute(server, "kubectl get sa -A --no-headers \| wc -l")` vs `jq length service_accounts.json` | sa_count = kubectl get sa -A count |
| 3 | Secret 采集完整性 | `ssh_execute(server, "kubectl get secrets -A --no-headers \| wc -l")` vs `jq length secrets.json` | secrets.json 节点数 = kubectl get secrets -A count |
| 4 | Container 采集完整性 | `ssh_execute(server, "crictl ps -a --quiet \| wc -l")` vs `jq length containers.json` | containers.json 节点数 = crictl ps -a count |
| 5 | Host 采集完整性 | `ssh_execute(server, "kubectl get nodes --no-headers \| wc -l")` vs `jq length hosts.json` | hosts.json 节点数 = kubectl get nodes count |
| 6 | Namespace 覆盖完整性 | `ssh_execute(server, "kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'")` vs pods.json 中出现的 namespace 集合 | pods.json NS 集合 = kubectl get ns 集合 |
| 7 | Service 采集完整性 | `ssh_execute(server, "kubectl get svc -A --no-headers \| wc -l")` vs `jq length services.json` | services.json 节点数 = kubectl get svc -A count |
| 8 | NetworkPolicy 采集完整性 | `ssh_execute(server, "kubectl get networkpolicies -A --no-headers \| wc -l")` vs infra.json 中 networkpolicy 相关边数 | NP 边数 ≥ kubectl get networkpolicies -A count |
| 9 | 安全上下文完整性 | 遍历 pods.json 每个 Pod 的 `security_context` 字段 | 每个 Pod 的 security_context 必须包含全部 13 个字段（见步骤 3 §3.4） |

**执行流程**：

```
对每个门控 1-9：
  1. ssh_execute 获取实际数量（L0 命令）
  2. jq 读取已写入 KG 的节点/边数量
  3. 对比：
     ├─ 通过 → 标记 ✅，继续下一个门控
     └─ 不通过 → 触发补采：
         a. ssh_execute 重新获取缺失的资源数据（kubectl get -o json / crictl inspect 等）
         b. 写入对应 nodes JSON 文件
         c. 更新 infra.json 边
         d. 重新校验该门控
         e. 补采次数计数 +1
  4. 补采 ≤2 次仍不通过 → 标 blocked，记录缺失清单到 recon_summary.md

所有 9 项门控通过 → 允许标 Phase 1a 为 complete
任一门控 blocked → Phase 1a 标 blocked，不进入 Phase 2
```

**门控结果写入** `evidence/recon/completeness_gates.json`：

```json
[
  {
    "gate_id": "GATE-01-pod",
    "name": "Pod 采集完整性",
    "expected": 26,
    "actual": 11,
    "passed": false,
    "backfill_attempts": 2,
    "final_status": "blocked",
    "missing_count": 15
  }
]
```

---

## 检查点

Phase 1a 完成判定需全部通过：

1. **采集完整性门控全部通过** — 9 项门控全部 ✅（见上方"采集完整性门控"章节），任一 blocked 则 Phase 1a 标 blocked
2. **主机/容器/Pod/SA 清单非空** — `hosts.json`、`containers.json`、`pods.json`、`service_accounts.json` 四个文件存在且数组非空
3. **安全上下文提取完成** — `pods.json` 中每个 Pod 节点包含 `security_context` 字段（全部 13 个字段，字段值不存在时标 `[?] 未设置`，不允许字段本身缺失），所有五态标记 `[ ]` 已消灭
4. **SA secrets 字段完整** — `service_accounts.json` 中每个 SA 节点包含 `secrets` 字段（列表，可为空数组 `[]`）
5. **环境指纹已生成** — `session_config.json` 包含完整 `env_fingerprint`（os_type、arch、kernel_version 为必填，scope 对应的版本字段为必填）
6. **QA 结构校验通过** — 所有 MUST 输出文件存在且非空，`_index.md` 与 JSON 内容一致

---

## WU 摘要格式

每个 WU 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/recon/summaries/{work_unit_id}.json`，包含字段：`work_unit_id`、`status`、`summary`、`critical_findings`（列表）、`files_written`（列表）、`context_used`（列表）、`issues`（列表）。

---

## 禁止事项

- **不执行攻击命令**：recon 只做侦察，不做 L2 攻击验证
- **不存储 Secret 内容**：`secrets.json` 仅记录名称和类型，禁止记录 Secret value
- **不在上下文中累积原始输出**：所有原始输出立即写盘，只保留摘要
- **不跳过 SSH 输出**：所有数据必须由 `ssh_execute` 真实执行产生，禁止伪造
- **不省略五态标记**：安全上下文的每个字段必须标注五态标记之一
- **不使用 sudo 替代攻击者视角**：L0 观察可用 sudo，但不能替代 L1/L2 验证

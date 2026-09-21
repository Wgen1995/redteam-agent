---
name: k8s-compliance
description: >
  Kubernetes合规检测。按CIS Kubernetes Benchmark分组执行226条合规规则检测（K8s部分134条），
  逐条判定pass/fail/warn/na，fail项必须附SSH输出和判定理由。
  使用场景：渗透测试合规检测阶段。
  不使用场景：无K8s环境、只做攻击验证。
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

# k8s-compliance — Phase 2a：Kubernetes CIS 合规检测

本 SKILL 负责对 K8s 集群执行 CIS Kubernetes Benchmark 全量合规检测（134 条规则），按分组分批检测，逐条判定并写入证据和知识图谱。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `knowledge_graph/nodes/` | Phase 1a | 环境信息（hosts.json、pods.json、containers.json、service_accounts.json、secrets.json） |
| `scope` 含 `k8s` | session_config.json | 必须 scope 包含 k8s 才执行 |
| `server` | ssh-manager 配置 | 目标服务器名称 |
| `compliance-rules/kubernetes/` | 本套件 | CIS 规则文件 |
| `compliance-hypotheses.md` | hypothesis-libraries | 合规假设映射 |
| `session_config.json` | Phase 1a | 含 env_fingerprint（K8s 版本、节点数等） |

**前置条件校验**：
1. `session_config.json` 必须存在且包含 `env_fingerprint`
2. `knowledge_graph/nodes/hosts.json` 必须存在且非空
3. `scope` 必须包含 `k8s`
4. SSH 连通性必须正常（Phase 1a 已验证）

任一前置条件不满足 → 立即终止，在 `progress.json` 标记 Phase 2a 为 `blocked`。

---

## 核心工作流（4 步）

### 步骤 1：读取合规规则

1. 读取 `compliance-rules/kubernetes/_index.md`，获取全部分组及规则数量
2. 根据 `session_config.json.env_fingerprint` 判断环境特征，确认本次应检测的分组
3. 按 WU 分批策略分组加载规则文件：
   - 逐个 Read 分组文件（如 `G_1_1_api_server_files.md`）
   - 每批 WU 约包含 40-50 条规则
   - 仅加载当前 WU 需要的文件，**不预读后续批次**
4. 记录本批 WU 读取的文件列表到 `context_used` 字段

### 步骤 2：按分组执行 SSH 命令检测

对每条合规规则：

1. **确定执行上下文层级**：
   - L0 规则：`ssh_execute` 在宿主机直接检查（如文件权限、进程参数）
   - L1 规则：`ssh_execute` + `kubectl exec` 进入容器检查（如容器内 securityContext）
2. **执行检测命令**：使用规则文件中定义的检查命令，通过 `ssh_execute` 执行
   - 命令失败（非零退出码、超时、连接中断）→ 记录原始输出，标记 `[!]`（环境干扰）
   - 命令不可用 → 按 Fallback 策略降级（见 `skills/shared/SSH_COMMANDS.md` §6.4）
3. **捕获原始输出**：每条命令的五元组标注写入 `evidence/compliance/k8s/raw/` 对应文件：
   ```
   > 命令：<原始命令>
   > 来源：<server> / <host_ip>
   > 上下文：<L0 或 L1>
   > 时间：<ISO 8601 时间戳>
   > 退出码：<exit_code>
   输出：<原始SSH输出，禁止删改>
   ```
4. **限速与重试**：同一服务器最大并行 3 条命令，批次间隔 2 秒；读命令重试 3 次，探测命令重试 2 次

### 多节点检测策略

K8s 合规规则分为两类：
- **集群级规则**（G_1 API Server、G_2 Etcd、G_3 Control Plane、G_6 Network Policies、G_8 RBAC/Secret）：只需在 master 节点（即 `server` 参数指定的入口节点）检查
- **节点级规则**（G_4 Kubelet 认证、G_5 Kubelet 运行时配置、G_7 Pod 安全）：需要在每个节点上检查本地文件

**节点级规则的检测方式**：
1. 从 `session_config.json` 的 `env_fingerprint.worker_nodes` 读取可达的 worker 节点列表
2. 对 master 节点：`ssh_execute(server, "...")` — 直接检查
3. 对可达的 worker 节点：`ssh_execute(server, "ssh <worker_ip> ...")` — 通过 master 跳转到 worker 检查
4. 对不可达的 worker 节点：标记为 `[-] 不适用（SSH 不可达）`，在 results.json 中记录原因
5. 每条节点级规则的检测结果需标注检查的节点名：`"checked_node": "worker-1"`

**G_4/G_5 的 WU 分批调整**：
- WU-2a-02（G_2-G_4）中的 G_4 规则：对每个可达节点执行一次，results.json 中每个节点一条记录
- WU-2a-03（G_5-G_6）中的 G_5 规则：同上
- G_7 规则：通过 `kubectl get pod -o yaml` 从 master 获取所有节点的 Pod 安全上下文，不需要逐节点 SSH

### 步骤 3：逐条判定

对每条规则，根据 SSH 原始输出和规则判定标准，给出五态判定：

| 标记 | 含义 | 判定标准 | 后续动作 |
|------|------|---------|---------|
| `[x]` | fail（需深审） | 检测结果不符合期望值 | 必须附 SSH 原始输出 + LLM 判定理由 |
| `[-]` | pass（已合规） | 检测结果符合期望值 | 记录符合的值 |
| `[!]` | warn（部分合规） | 部分符合、或存在偏离但风险可控 | 必须说明偏离内容 |
| `[ ]` | na（不适用） | 检测项在当前环境不适用 | 必须说明不适用原因 |
| `[?]` | 存在可疑发现，需 Phase 4b 深审 | 检测结果部分符合或有可疑迹象 | 标记候选，移交 Phase 4b |

**判定硬约束**：
- fail（`[x]`）必须附 SSH 原始输出和判定理由，缺一不可
- na（`[ ]`）必须说明不适用原因（如"非静态 Pod 部署，文件不存在"）
- warn（`[!]`）必须说明偏离内容（如"权限 640，期望 600，偏离 40 权限位"）
- 可疑发现（`[?]`）必须标记候选并移交 Phase 4b 深审

**合规确认门槛**（3 项）：

| # | 门槛 | 必须证明 |
|---|------|---------|
| 1 | 可检测 | SSH 执行检测命令返回了实际违规证据 |
| 2 | 可归属 | 违规可明确归属到具体 Pod/容器/节点/命名空间 |
| 3 | 影响可说明 | 能说明违规的具体安全影响（映射到攻击假设族） |

### 步骤 4：数据写入

每批 WU 完成后立即写入以下文件：

#### 4.1 evidence/compliance/k8s/results.json

```json
[
  {
    "rule_id": "K8s-1.1.1",
    "group": "G_1_1",
    "title": "API Server pod specification 文件权限",
    "status": "fail",
    "mark": "[x]",
    "evidence": {
      "command": "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml",
      "output": "644",
      "context": "L0",
      "host": "prod-k8s-01 / 10.0.1.5",
      "timestamp": "2026-06-20T10:15:30Z",
      "exit_code": 0
    },
    "judgment": "文件权限 644 宽松于期望值 600，任何用户可读 API Server 配置",
    "cis_mapping": "CIS Kubernetes Benchmark v1.8.0 - 1.1.1",
    "attack_surface": "AS-2 认证授权",
    "remediation": "chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml"
  }
]
```

#### 4.2 evidence/compliance/k8s/summary.md

```markdown
# K8s 合规检测摘要

## 统计

| 指标 | 数量 |
|------|------|
| 总规则数 | 134 |
| pass [-] | X |
| fail [x] | X |
| warn [!] | X |
| na [ ] | X |
| 可疑发现 [?] | X |
| 覆盖率 | X% |

## Critical 级别 fail 列表

| 规则 ID | 标题 | 判定理由 |
|---------|------|---------|
| K8s-x.x.x | ... | ... |

## 违规到攻击面映射

| 规则 ID | 攻击面 | 严重等级 |
|---------|--------|---------|
| K8s-x.x.x | AS-x | Critical |
```

#### 4.3 knowledge_graph/nodes/findings_k8s.json（K8s 平台分片）

> **禁止**与其他平台（docker/containerd）共享文件。Phase 2 全部完成后由 Pipeline 入口汇总为 `findings.json`（见 OUTPUT_STANDARD §7 并发写入保护协议）。

```json
[
  {
    "id": "finding-k8s-1-1-1",
    "node_type": "finding",
    "data": {
      "rule_id": "K8s-1.1.1",
      "platform": "k8s",
      "status": "fail",
      "severity": "high",
      "title": "API Server pod specification 文件权限过于宽松",
      "judgment": "文件权限 644 宽松于期望值 600",
      "host": "prod-k8s-01"
    },
    "session_id": "sess-20260619-001"
  }
]
```

#### 4.4 knowledge_graph/edges/compliance_k8s.json（K8s 平台分片）

> **禁止**与其他平台共享文件。Phase 2 全部完成后由 Pipeline 入口汇总为 `compliance.json`。

```json
[
  {
    "edge_type": "compliance",
    "from_node": "host-prod-k8s-01",
    "to_node": "finding-k8s-1-1-1",
    "attrs": {
      "rule_id": "K8s-1.1.1",
      "status": "fail",
      "evidence": "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml → 644",
      "platform": "k8s"
    }
  }
]
```

### 数据写入策略（防并发 + 防丢数据）

1. **JSON Lines 追加模式**：每条规则检测完成后立即追加写入 `evidence/compliance/k8s/results.jsonl`（每行一条 JSON），禁止累积满批再写：
   ```bash
   echo '{"rule_id":"K8s-1.1.1","verdict":"pass","evidence":"stat -c %a ...","host":"prod-k8s-01","ts":"2026-06-20T10:15:30Z"}' >> evidence/compliance/k8s/results.jsonl
   ```
2. **WU 完成时转为 JSON 数组**：
   ```bash
   jq -s '.' evidence/compliance/k8s/results.jsonl > evidence/compliance/k8s/results.json
   ```
3. **平台分片**：findings 写入 `findings_k8s.json`，compliance 边写入 `compliance_k8s.json`（不与其他平台共享文件）
4. **崩溃恢复**：WU 崩溃后从 `results.jsonl` 已有行数继续，不重做已检测的规则；恢复时先 `wc -l results.jsonl` 确定已完成的规则数，跳过对应的规则文件继续执行

---

## 分批策略（4 个 WU）

134 条规则分 4 批 WU 执行，每批约 40-50 条规则。每批 WU 独立工作，完成后执行第一重校验。

### WU-2a-01：G_1 组（41 条）API Server

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_1_1 | `G_1_1_api_server_files.md` | 7 | API Server 文件权限 |
| G_1_2 | `G_1_2_api_server_auth.md` | 23 | API Server 认证授权 |
| G_1_3 | `G_1_3_api_server_dos.md` | 1 | API Server 防 DoS |
| G_1_4 | `G_1_4_api_server_leak.md` | 3 | API Server 防信息泄露 |
| G_1_5 | `G_1_5_api_server_log.md` | 6 | API Server 审计日志 |
| G_1_6 | `G_1_6_api_server_ssl.md` | 1 | API Server TLS 配置 |

**上下文预算**：≤100k tokens  
**检测层级**：全部 L0（宿主机检查 kube-apiserver 启动参数和配置文件）  
**特殊说明**：G_1_2 含 23 条规则，是最大的子分组，需逐一检查 kube-apiserver 进程启动参数

### WU-2a-02：G_2-G_4 组（29 条）Etcd + Control Plane + Kubelet Auth

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_2_1 | `G_2_1_etcd_files.md` | 4 | Etcd 文件权限 |
| G_2_2 | `G_2_2_etcd_config.md` | 2 | Etcd 配置 |
| G_2_3 | `G_2_3_etcd_security.md` | 4 | Etcd 安全 |
| G_2_4 | `G_2_4_etcd_network.md` | 1 | Etcd 网络 |
| G_3_1 | `G_3_1_cm_security.md` | 4 | Controller Manager 安全 |
| G_3_2 | `G_3_2_scheduler_security.md` | 2 | Scheduler 安全 |
| G_4_1 | `G_4_1_kubelet_auth.md` | 4 | Kubelet 认证 |
| G_4_2 | `G_4_2_kubelet_authz.md` | 7 | Kubelet 授权配置 |
| G_4_3 | `G_4_3_kubelet_config.md` | 1 | Kubelet 配置 |

**上下文预算**：≤100k tokens  
**检测层级**：全部 L0（宿主机检查 etcd/cm/scheduler/kubelet 配置文件和启动参数）

### WU-2a-03：G_5-G_6 组（26 条）Kubelet Config + Network Policies

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_5_1 | `G_5_1_kubelet_runtime.md` | 8 | Kubelet 运行时配置 |
| G_5_2 | `G_5_2_kubelet_streaming.md` | 6 | Kubelet Streaming 连接 |
| G_5_3 | `G_5_3_kubelet_tls.md` | 2 | Kubelet TLS |
| G_5_4 | `G_5_4_kubelet_leak.md` | 5 | Kubelet 防信息泄露 |
| G_5_5 | `G_5_5_kubelet_dos.md` | 1 | Kubelet 防 DoS |
| G_5_6 | `G_5_6_kubelet_system.md` | 1 | Kubelet 系统配置 |
| G_6_1 | `G_6_1_network_policies.md` | 2 | Network Policies |
| G_6_2 | `G_6_2_network_default_deny.md` | 1 | 默认拒绝网络策略 |

**上下文预算**：≤100k tokens  
**检测层级**：L0（宿主机检查 kubelet 配置）+ 部分 L1（kubectl exec 检查容器内网络策略）

### WU-2a-04：G_7-G_8 组（38 条）Pod Security + RBAC/Secrets

| 子分组 | 规则文件 | 规则数 | 内容 |
|--------|---------|--------|------|
| G_7_1 | `G_7_1_pod_security.md` | 15 | Pod 安全上下文 |
| G_7_2 | `G_7_2_container_runtime.md` | 2 | 容器运行时安全 |
| G_8_1 | `G_8_1_secrets_mgmt.md` | 2 | Secret 管理 |
| G_8_2 | `G_8_2_rbac.md` | 13 | RBAC 权限控制 |
| G_8_3 | `G_8_3_security_context.md` | 2 | Security Context 配置 |
| G_8_4 | `G_8_4_network_policies_advanced.md` | 4 | 高级网络策略 |

**上下文预算**：≤100k tokens  
**检测层级**：L0（kubectl get 检查集群级 RBAC 和 Secret 配置）+ L1（kubectl exec 检查容器内 securityContext 实际生效值）  
**特殊说明**：G_7_1 含 15 条规则，需要遍历所有命名空间的 Pod 逐一检查 securityContext

---

## 三重校验

### 第一重：规则覆盖校验（每批 WU 完成后立即执行）

每个 WU 完成后立即检查：

1. **规则数量校验**：本批规则数量 = 预期数量？
   - WU-2a-01：41 条（G_1 组）
   - WU-2a-02：29 条（G_2-G_4 组）
   - WU-2a-03：26 条（G_5-G_6 组）
   - WU-2a-04：38 条（G_7-G_8 组）
2. **每条规则都有判定结果？** 不允许 `[ ]` 未检查残留
3. **每条 fail/warn 规则都有判定依据？** SSH 命令输出 + LLM 判定理由缺一不可
4. **不通过 → 本批重做**，不进入下一批

### 第二重：结构完整性校验（Phase 2 全部完成后）

所有 4 个 WU 完成后执行：

1. 总规则数 = 134 条（K8s 部分，与 `_index.md` 一致）
2. 所有判定都有对应 SSH 命令输出
3. `knowledge_graph/edges/compliance_k8s.json` 中每条 fail 规则都能找到对应 finding 节点（在 `findings_k8s.json` 中）
4. 五态标记无 `[ ]` 残留
5. `results.json` 中每条记录缺少 `rule_id`、`status`、`mark`、`evidence`、`judgment` 任一字段 → 校验失败
6. 不通过 → 补充缺失规则，直到全部覆盖

### 第三重：检查点报告校验（报告生成前）

生成 `reports/compliance_checkpoint_report.md` 前执行：

1. 报告中每条规则都有判定
2. fail/warn 规则都有判定依据摘要
3. 总计数 = pass + fail + warn + na + 可疑发现
4. 无占位符（`【xxx】`）、无 `[ ]` 未检查
5. 不通过 → 回到对应 WU 补充

---

## 反幻觉机制

本 SKILL 严格执行以下六条硬约束（源自设计文档 §1.2 和 §5.10）：

| # | 约束 | 说明 | 合规检测中的含义 |
|---|------|------|-----------------|
| ① | **禁止省略检查命令输出** | 不使用"等"、"..."、"+N"概括 | 每条规则的 SSH 输出必须完整记录到 `evidence/compliance/k8s/raw/`，禁止以"权限均合规"等概括替代逐条输出 |
| ② | **禁止编造判定结果** | 不凭记忆出检测结果 | 判定必须基于 `ssh_execute` 真实返回值，不得凭经验或从 baseline 推断 |
| ③ | **fail 必须附原始输出** | fail 项的判定依据 = SSH 原始输出 + LLM 判定理由 | 缺少任一项 → 规则标记为 `[?]` 可疑发现，移交 Phase 4b 深审，不标记为 fail |
| ④ | **na 必须说明原因** | 标记 na 时必须写明不适用原因 | 如"非静态 Pod 部署模式，文件 /etc/kubernetes/manifests/kube-apiserver.yaml 不存在" |
| ⑤ | **warn 必须说明偏离** | 标记 warn 时必须说明与期望值的偏离 | 如"权限为 640，期望 600，偏离：group 位有读权限" |
| ⑥ | **baseline 永不替代当前测试** | 上次会话结果只用于 delta 报告对比 | baseline 的 pass/fail 状态不影响本次判定，每条规则必须重新执行检测命令 |

**违反处理**：任何一条硬约束被违反时，对应 WU 的 `status` 置为 `failed`，由 supervisory-agent 决定重试或降级。

---

## 五态标记使用

每条合规规则必须使用以下五态标记之一：

| 标记 | 含义 | 合规检测语义 | 输出要求 |
|------|------|-------------|---------|
| `[x]` | fail（需深审） | 检测结果不符合 CIS Benchmark 期望值 | 必须附 SSH 原始输出 + 判定理由 |
| `[-]` | pass（已合规） | 检测结果符合期望值 | 记录符合的值 |
| `[!]` | warn（部分合规） | 部分符合或存在可控风险偏离 | 必须说明偏离内容 |
| `[ ]` | na（不适用） | 检测项在当前环境不适用 | 必须说明不适用原因 |
| `[?]` | 存在可疑发现，需 Phase 4b 深审 | 检测结果部分符合或有可疑迹象 | 标记候选，移交 Phase 4b |

**闭环要求**：
- 最终交付前所有 `[?]` 必须移交 Phase 4b 深审并闭环为其他四种标记
- `[x]` 标记的规则必须生成 `finding-k8s-X-X-X` 节点并写入 `findings.json`
- 每条 `[x]` 规则必须在 `compliance.json` 中生成对应 edge 连接到 `findings` 节点和相关 `host/pod` 节点

---

## WU 摘要格式

每个 WU 完成后必须向上返回摘要（≤500 tokens）：

```json
{
  "work_unit_id": "WU-2a-01",
  "status": "complete",
  "summary": "完成 G_1 组 API Server 41 条 CIS-K8s 规则检测，命中 5 项违规",
  "critical_findings": [
    "K8s-1.1.1: kube-apiserver.yaml 权限为 644（期望 600）",
    "K8s-1.2.7: anonymous-auth 启用（期望 false）"
  ],
  "files_written": [
    "evidence/compliance/k8s/results.jsonl",
    "evidence/compliance/k8s/results.json",
    "evidence/compliance/k8s/summary.md",
    "evidence/compliance/k8s/raw/G_1_api_server.json",
    "knowledge_graph/nodes/findings_k8s.json",
    "knowledge_graph/edges/compliance_k8s.json"
  ],
  "context_used": [
    "knowledge_graph/nodes/hosts.json",
    "knowledge_graph/nodes/pods.json",
    "compliance-rules/kubernetes/G_1_1_api_server_files.md",
    "compliance-rules/kubernetes/G_1_2_api_server_auth.md",
    "compliance-rules/kubernetes/G_1_3_api_server_dos.md",
    "compliance-rules/kubernetes/G_1_4_api_server_leak.md",
    "compliance-rules/kubernetes/G_1_5_api_server_log.md",
    "compliance-rules/kubernetes/G_1_6_api_server_ssl.md"
  ],
  "issues": []
}
```

---

## 合规假设映射（步骤 3 完成后执行）

完成 4 个 WU 的判定后，对每条 fail 规则执行合规假设映射：

1. 读取 `hypothesis-libraries/compliance-hypotheses.md`
2. 对每条 fail 规则，查找对应的攻击假设映射
3. 生成 `knowledge_graph/edges/compliance.json` 中的边，连接 `finding` 节点到攻击假设节点
4. 映射结果记录到 `results.json` 的 `attack_surface` 字段

---

## 检查点报告

Phase 2a+2b+2c 全部完成后，立即生成检查点报告初稿：

- `reports/compliance_checkpoint_report.md`
- `reports/compliance_checkpoint_report.json`

包含：
- 每条规则的判定结果 + 依据 + SSH 输出摘要
- **不含攻击关联**（攻击关联在 Phase 4 后更新）

---

## 独立运行参数

```bash
--server prod-k8s-01 --session-dir /path/to/session
```

独立运行时不依赖 supervisory-agent，需自行：
1. 读取 `session_config.json` 获取 server 和 scope
2. 验证 SSH 连通性
3. 按分批策略顺序执行 4 个 WU
4. 执行三重校验
5. 写入所有 MUST 输出文件

---

## 引用标准

- `skills/shared/OUTPUT_STANDARD.md`：输出格式标准
- `skills/shared/SEVERITY_RATING.md`：严重等级与验证程度分级
- `skills/shared/SSH_COMMANDS.md`：SSH 命令使用规范、层级标注、限速重试
- `compliance-rules/kubernetes/_index.md`：CIS 规则索引
- `hypothesis-libraries/compliance-hypotheses.md`：合规假设映射

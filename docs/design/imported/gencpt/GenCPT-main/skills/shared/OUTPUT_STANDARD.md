# 输出格式标准（OUTPUT_STANDARD）

> 适用范围：所有 15 个子技能在向工作目录写数据时必须遵循本标准。
> 来源：设计文档 `2026-06-20-GenCPT-v3-design.md` 第 5.7 节（数据契约）。
> 约束力：**强制**。违反将导致 QA 结构校验失败、断点续传失败或下游 Phase 读取异常。
> 共享规范归属：本标准与 `SSH_COMMANDS.md` / `SEVERITY_RATING.md` / `VULNERABILITY_GROUPING.md` / `QA_OVERRIDE_TRACKING.md` / `LOOP_POLICY.md` 同属 6 个共享规范，位于 `skills/shared/`。

---

## 1. 文件命名规范

### 1.1 通用规则

- 文件名一律 **snake_case**：仅小写字母、数字、下划线；禁止空格、连字符（仅 `cross-ref/` 和 `_index.md`、`_learned/` 等约定名例外）、中文、特殊符号。
- 所有产出文件落点严格限定在 **`{session_dir}/`** 工作目录树内，禁止写入会话目录以外的任何路径。
- 同一类产出的多种格式同名同根：`xxx.md` 与 `xxx.json` 必须共用同名（如 `compliance_report.md` / `compliance_report.json`）。
- 进度、任务、配置类文件位于工作目录根：`session_config.json`、`progress.json`、`task_list.json`。
- 临时文件只能写入 `{session_dir}/tmp/`，不得污染 `evidence/`、`knowledge_graph/`、`reports/`。

### 1.2 证据目录按 Phase 分子目录

| 子目录 | 责任 Phase | 内容 |
|--------|-----------|------|
| `evidence/recon/` | 1a / 1b | 侦察与源码扫描证据 |
| `evidence/recon/raw/` | 1a | 原始 SSH 输出（按命名空间/类型再分子目录） |
| `evidence/recon/summaries/` | 1a / 1b | 每个 WU 的摘要 JSON |
| `evidence/compliance/k8s/` | 2a | K8s 合规证据（`results.json` + `summary.md` + `raw/`） |
| `evidence/compliance/docker/` | 2b | Docker 合规证据（同结构） |
| `evidence/compliance/containerd/` | 2c | containerd 合规证据（同结构） |
| `evidence/compliance/summaries/` | 2a/2b/2c | WU 摘要 |
| `evidence/cross-ref/` | 3 | 交叉关联证据（4 个 MD 文件 + delta） |
| `evidence/attack/` | 4a / 4b | 攻击命中证据 |
| `evidence/attack/summaries/` | 4a / 4b | WU 摘要 |
| `evidence/chains/` | 5 / 6 | 链式攻击构建与验证 |
| `evidence/chains/summaries/` | 5 / 6 | WU 摘要 |
| `evidence/poc/` | 7 | POC 脚本与说明 |
| `evidence/poc/poc_scripts/` | 7 | POC 脚本目录 |
| `evidence/poc/summaries/` | 7 | WU 摘要 |
| `evidence/evolve/` | 9 | 攻击模式进化报告 |
| `evidence/qa/` | 8c | QA 抽检、回溯、工具上传日志 |
| `evidence/qa/raw/` | 8c | QA 语义抽检的原始 SSH 输出 |

> 注意：`cross-ref` 用连字符（约定例外），其他证据子目录用下划线或单段名。

### 1.3 知识图谱文件

`knowledge_graph/` 下分 `nodes/`、`edges/`、`episodic_memory/`：

- 节点：`knowledge_graph/nodes/*.json`，分别为 `hosts.json`、`pods.json`、`containers.json`、`services.json`、`service_accounts.json`、`secrets.json`、`source_findings.json`、`findings.json`（8类节点）。
- 边：`knowledge_graph/edges/*.json`，分别为 `infra.json`、`compliance.json`、`attack.json`、`cross_ref.json`、`source_edges.json`。
- 总索引：`knowledge_graph/nodes/_index.md`、`knowledge_graph/edges/_index.md`，提供 ID + 类型 + 一句话摘要定位。
- 情节记忆：`knowledge_graph/episodic_memory/session_history.md`、`knowledge_graph/episodic_memory/recommendations.md`。

### 1.4 报告文件

`reports/` 下报告成对产出 `.md` + `.json`：

- `reports/compliance_checkpoint_report.md` + `.json`（Phase 2 结束立即输出初稿，Phase 8a 定稿）
- `reports/compliance_report.md` + `.json`（Phase 8a 最终版）
- `reports/attack_report.md` + `.json`（Phase 8b）
- `reports/poc_package/`（Phase 8b 打包 POC）
- `reports/pentest_report.md` + `.json`（Phase 8c 综合报告）
- `reports/coverage_report.md`（Phase 8c 全景报告）

### 1.5 raw 文件命名规范（所有 Phase 统一）

格式：`{phase_id}_{batch_or_target}_{timestamp}.{ext}`

示例：
- `recon_pods_kube-system_20260728T160500.json`
- `k8s-compliance_WU-2a-01_G1_api-server_20260728T162800.txt`
- `attack-pattern_ATK-CAND-042_pre_20260728T211500.md`
- `chain-verify_CHAIN-001_step1_20260728T223000.md`
- `qa-semantic_K8s-1.2.20_20260728T235900.txt`

---

## 2. 每个 Phase 的 MUST 输出清单

> 下列文件为对应 Phase 完成判定（`progress.json` 由 pending/in_progress 转 complete）的硬性检查项，**任一缺失或为空即视为该 Phase 未完成**，将触发重新执行。
> 每个 Phase 除下列产出外，还须按 1.2 表写入本 Phase 的 WU 摘要 JSON。

### Phase 1a — 环境侦察

**MUST 输入**：`server`、`scope`

**MUST 输出**：

- `knowledge_graph/nodes/hosts.json`
- `knowledge_graph/nodes/pods.json`
- `knowledge_graph/nodes/containers.json`
- `knowledge_graph/nodes/services.json`
- `knowledge_graph/nodes/service_accounts.json`
- `knowledge_graph/nodes/secrets.json`
- `knowledge_graph/nodes/findings.json`（占位结构，Phase 2 填充）
- `knowledge_graph/nodes/_index.md`
- `knowledge_graph/edges/infra.json`
- `knowledge_graph/edges/_index.md`
- `evidence/recon/recon_summary.md`
- `evidence/recon/raw/`（文件数 ≥ SSH 命令批次数，每个原始 SSH 输出带来源与时间戳）
- `session_config.json`（必须含 `env_fingerprint`：见 §4.4）

### Phase 1b — 源码扫描

**MUST 输入**：`source_path` 或 `source_url`、`source_type`

**MUST 输出**：

- `knowledge_graph/nodes/source_findings.json`
- `knowledge_graph/edges/source_edges.json`
- `evidence/recon/source_analysis.md`
- `evidence/recon/source_scan_stats.md`

### Phase 2a — K8s 合规

**MUST 输入**：Phase 1a 的 `knowledge_graph/nodes/` 输出，`scope` 含 `k8s`

**MUST 输出**：

- `evidence/compliance/k8s/results.json`
- `evidence/compliance/k8s/summary.md`
- `evidence/compliance/k8s/raw/`（文件数 ≥ SSH 命令批次数，每条 CIS 规则的原始命令输出）
- `knowledge_graph/nodes/findings_k8s.json`（K8s 平台分片，写入实际违规项，禁止与其他平台共享文件）
- `knowledge_graph/edges/compliance_k8s.json`（K8s 平台分片，禁止与其他平台共享文件）

**Phase 2 结束时立即追加**：

- `reports/compliance_checkpoint_report.md` + `.json`（初稿，供 Phase 3 检查点用）

### Phase 2b — Docker 合规

**MUST 输入**：Phase 1a 输出，`scope` 含 `docker`

**MUST 输出**：

- `evidence/compliance/docker/results.json`
- `evidence/compliance/docker/summary.md`
- `evidence/compliance/docker/raw/`（文件数 ≥ SSH 命令批次数）
- `knowledge_graph/nodes/findings_docker.json`（Docker 平台分片，禁止与其他平台共享文件）
- `knowledge_graph/edges/compliance_docker.json`（Docker 平台分片，禁止与其他平台共享文件）

### Phase 2c — containerd 合规

**MUST 输入**：Phase 1a 输出，`scope` 含 `containerd`

**MUST 输出**：

- `evidence/compliance/containerd/results.json`
- `evidence/compliance/containerd/summary.md`
- `evidence/compliance/containerd/raw/`（文件数 ≥ SSH 命令批次数）
- `knowledge_graph/nodes/findings_containerd.json`（containerd 平台分片，禁止与其他平台共享文件）
- `knowledge_graph/edges/compliance_containerd.json`（containerd 平台分片，禁止与其他平台共享文件）

### Phase 3 — 交叉关联

**MUST 输入**：`knowledge_graph/edges/compliance.json`、`knowledge_graph/nodes/findings.json`、三库文件（合规规则、攻击模式库、攻击假设库）

**MUST 输出**：

- `knowledge_graph/edges/cross_ref.json`
- `evidence/cross-ref/cross_ref_summary.md`
- `evidence/cross-ref/risk_amplification.md`
- `evidence/cross-ref/prerequisite_signals.md`
- `evidence/cross-ref/history_priority.md`

### Phase 4a — 攻击模式库匹配

**MUST 输入**：合规结果 + 交叉关联 + `attack-patterns/_index.md`

**MUST 输出**：

- `evidence/attack/pattern-hits.md`
- `evidence/attack/unmatched_signals.md`（无法匹配现有模式的 `[?]` 候选交 Phase 4b）
- `knowledge_graph/edges/attack.json`

### Phase 4b — LLM 推理攻击

**MUST 输入**：Phase 4a 的 `[?]` 候选 + Phase 3 高关联度发现 + 攻击面模型 + 知识图谱

**MUST 输出**：

- `evidence/attack/reasoning-hits.md`
- `evidence/insights.md`
- `knowledge_graph/edges/attack.json`（**追加**，不覆盖 Phase 4a 内容）
- `knowledge_graph/episodic_memory/recommendations.md`（晋升候选）

### Phase 5 — 链式攻击构建

**MUST 输入**：`knowledge_graph/edges/attack.json` + `cross_ref.json` + `findings.json`

**MUST 输出**：

- `evidence/chains/chain_builder.md`
- `knowledge_graph/edges/cross_ref.json`（**追加** `attack_chain` 边）

### Phase 6 — 链式攻击验证

**MUST 输入**：链式攻击数据 + 知识图谱

**MUST 输出**：

- `evidence/chains/chain_verification.md`

### Phase 7 — POC 生成

**MUST 输入**：验证完成的攻击链 + POC 数据

**MUST 输出**：

- `evidence/poc/poc_scripts/`（非空，每条 POC 含脚本本体与说明）
- `evidence/poc/poc_readme.md`

### Phase 8a — 合规报告

**MUST 输入**：合规数据

**MUST 输出**：

- `reports/compliance_report.md`
- `reports/compliance_report.json`
- `reports/compliance_checkpoint_report.md`（定稿，覆盖 Phase 2 初稿）
- `reports/compliance_checkpoint_report.json`

### Phase 8b — 攻击报告

**MUST 输入**：攻击数据 + POC 包

**MUST 输出**：

- `reports/attack_report.md`
- `reports/attack_report.json`
- `reports/poc_package/`（打包 Phase 7 的 POC）

### Phase 8c — 综合报告 + QA

**MUST 输入**：Phase 8a + 8b 报告 + 知识图谱 + `insights.md` + `session_history.md`

**MUST 输出**：

- `reports/pentest_report.md`
- `reports/pentest_report.json`
- `reports/coverage_report.md`
- `evidence/qa/qa_summary_report.md`（语义抽检报告，五态标记无 `[ ]` 残留）

### Phase 9 — 攻击模式进化

**MUST 输入**：`insights.md` + `session_history.md` + `attack-patterns/_index.md` + `attack-hypotheses.md`

**MUST 输出**：

- `attack-patterns/{新攻击面}/SKILL.md`（新增 SKILL 文件）
- `attack-patterns/_index.md`（更新，登记新增条目）
- `evidence/evolve/evolve_report.md`（本次进化摘要：新增/降级/归档清单）

---

## 3. WU 摘要格式规范

每个 work unit（WU）必须向 `supervisory-agent` 返回上行摘要，同时写盘一份到对应 Phase 的 `summaries/{work_unit_id}.json`。

### 3.1 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `work_unit_id` | ✅ | 形如 `WU-1a-01`，与 `task_list.json` 中的 ID 一致 |
| `status` | ✅ | 取值见 §3.2 |
| `summary` | ✅ | 一句话本 WU 完成了什么；禁省略词 |
| `critical_findings` | ✅ | 关键发现条目；无则填 `[]`，不得省略字段 |
| `files_written` | ✅ | 实际写入文件的相对路径列表（相对 `{session_dir}`） |
| `context_used` | ✅ | 读取了哪些上游文件（知识图谱节点/边、Phase 输出等） |
| `issues` | ✅ | 遇到的问题或阻断；无则填 `[]` |

### 3.2 status 取值

| 取值 | 含义 | 下游动作 |
|------|------|---------|
| `complete` | 所有 MUST 输出已写盘且非空 | 更新 `progress.json`；supervisory-agent 可派发下一 WU |
| `in_progress` | 部分完成，需断点续传 | 记录 `batch_progress` 与 `resumable_from_batch` |
| `failed` | 异常退出但环境未受损 | 诊断后重试或跳过（写明原因） |
| `blocked` | 审批被拒、权限不足或环境阻断 | supervisory-agent 决定降级或终止该路径 |

### 3.3 约束

- 摘要**不携带原始 SSH 输出**、原始证据内容；这些只能写盘后以文件路径引用。
- 禁止省略词：「等」「...」「+(数量后缀)」「大致」「约」。
- 所有 `【xxx】` 占位符必须替换为实际值，不得留空。

### 3.4 示例

```json
{
  "work_unit_id": "WU-2a-03",
  "status": "complete",
  "summary": "完成命名空间 kube-system 的 18 条 CIS-K8s 规则检测，命中 3 项违规",
  "critical_findings": [
    "K8s-5.2.3: kube-apiserver 启用了 anonymous-auth=true",
    "K8s-5.1.4: kubelet 启用了 anonymous-auth=true"
  ],
  "files_written": [
    "evidence/compliance/k8s/results.json",
    "evidence/compliance/k8s/summary.md",
    "evidence/compliance/k8s/raw/kube-system.json",
    "knowledge_graph/nodes/findings.json",
    "knowledge_graph/edges/compliance.json"
  ],
  "context_used": [
    "knowledge_graph/nodes/pods.json",
    "knowledge_graph/nodes/service_accounts.json",
    "compliance-rules/k8s/_index.md"
  ],
  "issues": []
}
```

---

## 4. JSON 文件格式规范

### 4.1 知识图谱节点

```json
{
  "id": "pod-kube-system-apiserver-79f6c5d6c4-abc12",
  "node_type": "pod",
  "data": {
    "namespace": "kube-system",
    "name": "kube-apiserver-79f6c5d6c4-abc12",
    "security_context": { "privileged": false, "runAsUser": 1001 },
    "ip": "10.244.0.3"
  },
  "session_id": "sess-20260619-001"
}
```

- `id`：全图唯一；去重 key（见设计文档 §16）。命名前缀体现类型：`pod-` / `host-` / `container-` / `sa-` / `secret-` / `finding-` / `source-finding-`。
- `node_type`：`pod` / `host` / `container` / `service` / `service_account` / `secret` / `source_finding` / `finding`。
- `secret` 节点只存名称与类型，**绝不存储 Secret 内容**。
- `session_id`：与 `session_config.json` 中一致，用于跨会话 baseline 比对与去重。

### 4.2 知识图谱边（通用）

```json
{
  "edge_type": "compliance",
  "from_node": "host-node-01",
  "to_node": "finding-k8s-5-2-3",
  "attrs": {
    "rule_id": "K8s-5.2.3",
    "status": "fail",
    "evidence": "kubectl get pods -o jsonpath='{.items[5].spec.securityContext.privileged}'"
  }
}
```

- `edge_type`：`infra` / `compliance` / `attack` / `cross_ref` / `source_edges`。
- 去重 key：`from_node` + `to_node` + `edge_type`；不同属性 → 保留最新 `timestamp`。
- 文件结构与 Phase 的对应：
  - `infra.json` ← Phase 1a
  - `source_edges.json` ← Phase 1b
  - `compliance_k8s.json` ← Phase 2a / `compliance_docker.json` ← Phase 2b / `compliance_containerd.json` ← Phase 2c（各平台独立分片，禁止共享文件；Phase 2 全部完成后由 Pipeline 入口汇总为 `compliance.json`，见 §7 并发写入保护协议）
  - `cross_ref.json` ← Phase 3，Phase 5 追加 `attack_chain` 类边
  - `attack.json` ← Phase 4a，Phase 4b 追加

### 4.3 attack 边（强制字段）

`edge_type: "attack"` 的边**必须**将所有强制字段放入 `attrs` 对象内，顶层只保留 `edge_type` / `from_node` / `to_node` / `attrs` / `timestamp`，否则 QA 结构校验失败：

```json
{
  "edge_type": "attack",
  "from_node": "container-abc123",
  "to_node": "host-node-01",
  "attrs": {
    "source": "pattern_library",
    "atk_cand_id": "ATK-CAND-001",
    "status": "confirmed",
    "verification_level": "C1",
    "execution_context_max": "L2",
    "pattern_ref": "escape/docker-sock-escape",
    "target": "host-node-01",
    "severity": "critical",
    "confidence": 0.95,
    "prerequisites_met": ["docker.sock 挂载可见"],
    "prerequisites_unmet": [],
    "trigger_rules": ["K8s-5.2.3"],
    "hypothesis_refs": ["ATK-HYP-001"],
    "five_state": "[x]",
    "context": "L2",
    "steps": [
      {
        "step": 1,
        "action": "探测 docker.sock 可用性",
        "command": "kubectl exec abc123 -- ls -la /var/run/docker.sock",
        "output": "srw-rw---- 1 root 999 /var/run/docker.sock",
        "meaning": "容器内存在 Docker 套接字文件",
        "context": "L1"
      },
      {
        "step": 2,
        "action": "验证逃逸路径",
        "command": "kubectl exec abc123 -- docker run -v /:/host alpine ls /host/etc/shadow",
        "output": "root:x:0:0:...",
        "meaning": "可读取宿主机密码文件",
        "context": "L2"
      }
    ],
    "evidence_files": [
      "evidence/attack/raw/ATK-CAND-001_step1_20260728T211500.txt",
      "evidence/attack/raw/ATK-CAND-001_step2_20260728T211700.txt"
    ]
  },
  "timestamp": "2026-07-28T21:17:30Z"
}
```

**强制字段汇总**（均在 `attrs` 内）：

| 字段 | 取值 | 说明 |
|------|------|------|
| `verification_level` | `C1` / `C2` / `C3` | 确认层级。C1：单点可观测；C2：满足攻击确认门槛 5 项；C3：满足差分证明。详见设计文档 §15 |
| `context`（`attrs.steps[].context`） | `L0` / `L1` / `L2` / `L3` | 执行上下文层级。L0 宿主机观察；L1 容器内观察；L2 容器内攻击验证；L3 条件验证（不实际执行破坏性操作） |
| `execution_context_max` | `L0`/`L1`/`L2`/`L3` | 本攻击边内最高上下文层级；SSH root 仅可用于 L0 侦察与条件核实，不得用于替代 L1/L2 攻击者视角 |
| `source` | `pattern_library` / `llm_reasoning` / `learned` / `cross_ref` / `chain` | 命中来源。Phase 4a 写 `pattern_library`；Phase 4b 追加 `llm_reasoning`；进化晋升的模式命中写 `learned`；Phase 3 交叉关联写 `cross_ref`；Phase 5 链式边写 `chain` |
| `atk_cand_id` | `ATK-CAND-NNN` | 攻击候选编号。`[x]` 与 `[?]` 必须生成编号；`[-]`/`[!]` 不生成但须写依据 |
| `status` | `confirmed` / `high_risk_lead` / `disproven` / `blocked` | confirmed 必须满足攻击确认门槛 5 项 + 差分证明；缺失任一项降级为 `high_risk_lead` |
| `pattern_ref` | 模式路径 | 命中的攻击模式库路径，如 `escape/docker-sock-escape` |
| `target` | 节点 ID | 攻击目标节点 ID |
| `severity` | `critical` / `high` / `medium` / `low` / `info` | 严重性等级 |
| `confidence` | 0-1 数值 | 置信度评分 |
| `prerequisites_met` | 字符串数组 | 已满足的前置条件列表 |
| `prerequisites_unmet` | 字符串数组 | 未满足的前置条件列表 |
| `trigger_rules` | 字符串数组 | 触发本攻击的合规规则 ID 列表 |
| `hypothesis_refs` | 字符串数组 | 关联的攻击假设 ID 列表 |
| `five_state` | `[x]`/`[?]`/`[-]`/`[!]` | 五态标记（不可为 `[ ]`） |
| `steps` | 对象数组 | 攻击步骤序列，每步含 step/action/command/output/meaning/context |
| `evidence_files` | 字符串数组 | 证据文件相对路径列表 |

### 4.4 cross_ref 边

```json
{
  "edge_type": "cross_ref",
  "from_node": "container-abc123",
  "to_node": "finding-k8s-5-2-3",
  "attrs": {
    "reason": "容器挂载 docker.sock 与合规违规 K8s-5.2.3 一致，确认攻击前置条件被合规违规满足",
    "severity": "critical"
  },
  "timestamp": "2026-06-19T08:42:00Z"
}
```

- `attrs.severity`：`critical` / `high` / `medium` / `low` / `info`。
- 去重 key：`from_node` + `to_node` + `attrs.reason` 语义 hash，避免语义相同文字略有差异的边重复。
- `attack_chain` 类边（Phase 5 追加）额外 attrs 字段：`chain_id`、`chain_order`、`prerequisite_met_by`（指向上游节点 ID）。

### 4.5 session_config.json

```json
{
  "session_id": "sess-20260619-001",
  "server": "prod-cluster-01",
  "mode": "compliance+attack",
  "scope": "all",
  "approval": "standard",
  "suite_version": "V1.2",
  "auto_high_risk_exec_count": 0,
  "baseline": null,
  "env_fingerprint": {
    "os_type": "linux",
    "arch": "amd64",
    "kernel_version": "5.15.0-91-generic",
    "k8s_version": "1.29.0",
    "docker_version": "24.0.7",
    "containerd_version": "1.7.13",
    "node_count": 3,
    "pod_count": 47,
    "sa_count": 9,
    "env_hash": "sha256:..."
  },
  "created_at": "2026-06-19T08:42:00Z"
}
```

- **必须包含 `env_fingerprint`**；缺失 `env_fingerprint` 视为 Phase 1a MUST 输出未完成。
- `env_fingerprint` 至少包含以下字段（缺失会导致工具库无法选择对应二进制、跨会话 baseline 比对失败）：
  - `os_type`（如 `linux`）
  - `arch`（如 `amd64` / `arm64`）
  - `kernel_version`（`uname -r` 输出）
  - `k8s_version`、`docker_version`、`containerd_version`（如对应 scope 启用）
  - `env_hash`：`k8s_version + docker_version + node_count + pod_count + sa_count` 拼接后的哈希，用于跨会话差异判定
- 工具选择路径：根据 `os_type` + `arch` 从 `tools/{os_type}-{arch}/` 取对应二进制，`ssh_upload` 至远端 `/tmp/cpt-tools/`。

### 4.6 通用 JSON 约束

- 所有 JSON 文件必须为合法 UTF-8、可被标准 JSON 解析器读取；不允许末尾逗号、单引号、注释。
- 时间戳字段统一 ISO 8601 with TZ，如 `2026-06-19T08:42:00Z`。
- 文件正文每条记录或每条边换行分隔（JSON Lines 或顶层 JSON 数组二选一，本套件统一采用**顶层 JSON 数组**）。
- `_index.md` 与 `*.md` 同时维护时，`_index.md` 必须在对应 JSON 写入后再更新，保持索引与内容一致。

---

## 5. Markdown 文件格式规范

### 5.1 标题层级

- **H1（`#`）**：仅用于文件标题，每文件只有一个 H1。
- **H2（`##`）**：章节级（如 `## 1. 扫描范围`、`## 风险发现`）。
- **H3（`###`）**：子章节级。**禁止跳级**：H1→H3 不允许，必须经 H2。
- H4 及以下保持精简；证据文件如需多层嵌套，优先用列表与表格而非增加标题层级。

### 5.2 五态标记

合规与攻击条目状态必须使用下列五种标记之一：

| 标记 | 含义 | 后续动作 |
|------|------|---------|
| `[x]` | 存在明确候选，必须深审 | 必须生成 `ATK-CAND-NNN` |
| `[?]` | 存在可疑面，必须深审 | 交 Phase 4b 处理 |
| `[-]` | 已检查，无候选或不适用 | 必须写明证伪依据（哪条命令的输出证明不可利用） |
| `[!]` | 已检查，被防护阻断 | 必须写明阻断机制（AppArmor / Seccomp / NetworkPolicy 等） |
| `[ ]` | 尚未检查 | 最终报告前必须消灭，转为上述四种之一 |

约束：

- `pentest_report.md` 与 `coverage_report.md` 交付前，**所有 `[ ]` 必须消灭**。
- `[x]` 与 `[?]` 必须有 `ATK-CAND-NNN` 编号；`[-]` 与 `[!]` 必须写明依据（哪条命令的输出证明不可利用或被阻断）。
- 合规规则五态标记语义：`[x]` fail（需深审） / `[-]` pass（已合规） / `[!]` warn（部分合规） / `[ ]` 不适用。

### 5.3 证据文件的 SSH 输出标注

`evidence/**/raw/` 及任何引用 SSH 命令输出的证据段落，**每段输出必须标注**：

1. 来源命令（原文，便于审计回放）
2. 远端主机名/IP（与 `session_config.json.server` 或扫描到的具体节点对应）
3. 执行上下文层级（`L0`/`L1`/`L2`/`L3`）
4. 执行时间戳（ISO 8601）
5. 退出码与超时信息（如有）

示例段落：

```
> 命令：kubectl -n kube-system get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext.privileged}{"\n"}{end}'
> 来源：prod-cluster-01 / 10.0.1.5
> 上下文：L0（宿主机观察）
> 时间：2026-06-19T08:43:12Z
> 退出码：0
输出：
kube-apiserver-79f6c5d6c4-abc12  false
coredns-648979857d-xyz98         false
kube-proxy-abcde                 false
```

- 禁止删改原始输出；只能在段落外增加分析说明（另起段落或列表项）。
- 同一证据文件内的批量命令输出按"来源命令 → 标注块 → 输出"循环组织，不得混杂无标注的输出。

### 5.4 通用 Markdown 约束

- 中文与英文、数字、半角符号之间留一空格（如 `K8s 5.2.3 命中 3 项`），符合中文排版指北。
- 标点优先全角；技术标识（命令、文件路径、字段名、代码）保持半角。
- 列表项一级用 `-`，二级用缩进 `-`；有序列表用 `1.`（**仅用于有先后顺序必须的步骤**）。
- 代码块须标注语言：` ```bash `、` ```json `、` ```yaml ` 等。
- 引用块（`>`）用于证据块的标注四元组，不用于普通强调。
- 表格使用 GitHub-flavored Markdown 语法，单元格禁止换行符。
- 文件尾部保留一个空行。
- 禁止省略词与占位符残留（同 §3.3）。
- 文件名不得出现中文；文件正文中文优先（与设计文档保持一致），技术标识保持英文。

---

## 6. 一致性检查（QA 校验对接）

本标准的设计直接服务于 QA 三层校验。子技能写盘后自查，QA 在 Phase 8c 做结构校验：

1. **结构校验**：遍历 §2 每个 Phase 的 MUST 输出，逐项检查文件存在且非空；缺失或空文件 → QA 报告为该 Phase 结构失败。
2. **字段校验**：`attack.json` 中边的 `attrs` 不含 `verification_level` / `context` 等强制字段的边 → 视为非法边；强制字段不在 `attrs` 内而在顶层的边 → 视为格式非法；`session_config.json` 缺 `env_fingerprint` → 视为 Phase 1a 未完成。
3. **五态闭环校验**：`pentest_report.md` 与 `coverage_report.md` 中残留 `[ ]` → QA 报告为质量门禁未通过。
4. **去重仲裁**：见设计文档 §16，重复节点/边按去重 key 与时间戳合并。

发现违反本标准任一条款时，相关 WU 摘要 `status` 置为 `failed`，由 `supervisory-agent` 决定重试或降级。

---

## 7. 并发写入保护协议

### 7.1 各自落盘原则
- Phase 2a/2b/2c 各自写入独立的平台分片文件（`findings_k8s.json` / `findings_docker.json` / `findings_containerd.json`）
- 禁止多 Phase/WU 同时写同一文件
- 各 Phase 完成后可并行执行，互不干扰

### 7.2 串行汇总
- Phase 2 全部完成后（2a+2b+2c 都 complete），由 Pipeline 入口或 supervisor 执行汇总：
  - 合并 `findings_k8s.json` + `findings_docker.json` + `findings_containerd.json` → `findings.json`
  - 合并 `compliance_k8s.json` + `compliance_docker.json` + `compliance_containerd.json` → `compliance.json`
- 汇总使用 bash jq 命令：
  ```bash
  jq -s 'add' findings_k8s.json findings_docker.json findings_containerd.json > findings.json
  jq -s 'add' compliance_k8s.json compliance_docker.json compliance_containerd.json > compliance.json
  ```
- 缺失 scope 对应的分片文件时跳过该分片（不报错），仅合并存在的分片。

### 7.3 WU 内 partial 写盘（JSON Lines）
- 每条规则检测完成后立即追加写入 `results.jsonl`（JSON Lines 格式，每行一条规则结果）
- WU 完成时将 `results.jsonl` 转为 `results.json`（顶层 JSON 数组）：
  ```bash
  jq -s '.' results.jsonl > results.json
  ```
- WU 崩溃时已有结果保留在 `results.jsonl` 中，恢复时从 `results.jsonl` 已有行数继续，不重做已检测的规则
- 转换前先校验 `results.jsonl` 每行为合法 JSON，非法行跳过并记录到 `evidence/compliance/*/parse_errors.log`
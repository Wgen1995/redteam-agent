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

## MUST 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| 合规检测结果 | `evidence/compliance/k8s/results.json` | 逐条规则判定（含五元组证据） |
| 合规检测摘要 | `evidence/compliance/k8s/summary.md` | 统计 + Critical fail 列表 + 攻击面映射 |
| 原始证据 | `evidence/compliance/k8s/raw/` | 每条规则的 SSH 原始输出 |
| K8s findings | `knowledge_graph/nodes/findings_k8s.json` | K8s 平台分片 finding 节点 |
| K8s compliance 边 | `knowledge_graph/edges/compliance_k8s.json` | K8s 平台分片 compliance 边 |

---

## 核心工作流（4 步）

### 步骤 1：读取合规规则

1. 读取 `compliance-rules/kubernetes/_index.md`，获取全部分组及规则数量
2. 根据 `session_config.json.env_fingerprint` 判断环境特征，确认本次应检测的分组
3. 按 WU 分批策略分组加载规则文件（每批 WU 约 40-50 条规则，仅加载当前 WU 需要的文件）
4. 记录本批 WU 读取的文件列表到 `context_used` 字段

### 步骤 2：按分组执行 SSH 命令检测

对每条合规规则：

1. **确定执行上下文层级**：L0 规则 `ssh_execute` 在宿主机直接检查；L1 规则 `ssh_execute` + `kubectl exec` 进入容器检查
2. **执行检测命令**：命令失败 → 记录原始输出，标记 `[!]`（环境干扰）；命令不可用 → 按 Fallback 策略降级
3. **捕获原始输出**：五元组标注写入 `evidence/compliance/k8s/raw/`
4. **限速与重试**：同一服务器最大并行 3 条命令，批次间隔 2 秒

**五元组标注格式、JSON Lines 写盘规则详见 `references/evidence_format.md`。**
**多节点检测策略（集群级 vs 节点级规则）详见 `references/wu_details.md`。**

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

每批 WU 完成后立即写入 results.jsonl、summary.md、findings_k8s.json、compliance_k8s.json。

**results.json/summary.md/findings_k8s.json/compliance_k8s.json 详细格式、JSON Lines 写盘规则、finding evidence 字段要求详见 `references/evidence_format.md`。**

#### 4.5 对象级 compliance 边（步骤 5b）

除原有的 `host → finding` 边外，**必须**为每个 finding 追加对象级 compliance 边，关联到具体违规对象：

**提取对象名**：
1. 从 finding 节点的 `judgment` 字段中提取违规对象名（Pod/Container/SA/Secret）
2. 对象名匹配规则：
   - Pod：`pod-{namespace}-{name}` 格式，从 judgment 文本中匹配 Pod 名称
   - Container：`container-{name}` 格式，从 judgment 文本中匹配容器名称
   - SA：`sa-{namespace}-{name}` 格式，从 judgment 文本中匹配 SA 名称
   - Secret：`secret-{namespace}-{name}` 格式，从 judgment 文本中匹配 Secret 名称
3. 对每个匹配到的违规对象，追加 compliance 边：

```json
{
  "edge_type": "compliance",
  "from_node": "pod-vuln-apps-privileged-escape-target",
  "to_node": "finding-k8s-k8s-7-1-1",
  "attrs": {
    "rule_id": "K8s-7.1.1",
    "status": "fail",
    "relation": "violates",
    "platform": "k8s"
  }
}
```

**约束**：
- 原有 `host → finding` 边**保留**，不删除
- 对象级边 `attrs.relation` 固定为 `"violates"`
- 对象节点不存在于 KG 中时，按 KG 节点存在性校验规则补采
- 此步骤修复"0/34 compliance 边缺对象级关联"问题

---

## 分批策略（4 个 WU）

134 条规则分 4 批 WU 执行，每批约 40-50 条规则：

| WU | 分组 | 规则数 | 内容 |
|----|------|--------|------|
| WU-2a-01 | G_1 | 41 | API Server |
| WU-2a-02 | G_2-G_4 | 29 | Etcd + Control Plane + Kubelet Auth |
| WU-2a-03 | G_5-G_6 | 26 | Kubelet Config + Network Policies |
| WU-2a-04 | G_7-G_8 | 38 | Pod Security + RBAC/Secrets |

**4 WU 详细规则分组表、多节点检测策略详见 `references/wu_details.md`。**

---

## 三重校验

### 第一重：规则覆盖校验（每批 WU 完成后立即执行）

1. **规则数量校验**：本批规则数量 = 预期数量？（WU-01: 41, WU-02: 29, WU-03: 26, WU-04: 38）
2. **每条规则都有判定结果？** 不允许 `[ ]` 未检查残留
3. **每条 fail/warn 规则都有判定依据？** SSH 命令输出 + LLM 判定理由缺一不可
4. **不通过 → 本批重做**，不进入下一批

### 第二重：结构完整性校验（Phase 2 全部完成后）

1. 总规则数 = 134 条（K8s 部分，与 `_index.md` 一致）
2. 所有判定都有对应 SSH 命令输出
3. `compliance_k8s.json` 中每条 fail 规则都能找到对应 finding 节点
4. 五态标记无 `[ ]` 残留
5. `results.json` 中每条记录缺少 `rule_id`、`status`、`mark`、`evidence`、`judgment` 任一字段 → 校验失败
6. 不通过 → 补充缺失规则，直到全部覆盖

### 第三重：检查点报告校验（报告生成前）

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

## 五态标记闭环要求

五态标记定义见步骤 3 判定表。闭环要求：
- 最终交付前所有 `[?]` 必须移交 Phase 4b 深审并闭环为其他四种标记
- `[x]` 标记的规则必须生成 `finding-k8s-X-X-X` 节点并写入 `findings.json`
- 每条 `[x]` 规则必须在 `compliance.json` 中生成对应 edge 连接到 `findings` 节点和相关 `host/pod` 节点

---

## 合规假设映射

完成 4 个 WU 的判定后，对每条 fail 规则执行合规假设映射。

**映射规则、COMP-CAND 编号规则详见 `references/compliance_mapping.md`。**

---

## 检查点报告

Phase 2a+2b+2c 全部完成后，生成 `reports/compliance_checkpoint_report.md` + `.json`。包含每条规则的判定结果 + 依据 + SSH 输出摘要（**不含攻击关联**，攻击关联在 Phase 4 后更新）。

---

## 独立运行参数

`--server prod-k8s-01 --session-dir /path/to/session` — 独立运行时不依赖 supervisory-agent，需自行：读取 session_config.json → 验证 SSH → 按 4 WU 顺序执行 → 三重校验 → 写入所有 MUST 输出。

---

## 引用标准

- `skills/shared/OUTPUT_STANDARD.md`、`SEVERITY_RATING.md`、`SSH_COMMANDS.md`
- `compliance-rules/kubernetes/_index.md`：CIS 规则索引
- `hypothesis-libraries/compliance-hypotheses.md`：合规假设映射

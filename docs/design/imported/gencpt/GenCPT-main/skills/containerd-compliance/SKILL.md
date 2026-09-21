---
name: containerd-compliance
description: >
  Containerd合规检测。按CIS Containerd Benchmark分组执行28条合规规则检测，
  逐条判定pass/fail/warn/na，fail项必须附SSH输出和判定理由。
  使用场景：渗透测试合规检测阶段（Containerd部分）。
  不使用场景：无Containerd环境、只做K8s检测。
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

# containerd-compliance（Phase 2c）

## 1. 定位与边界

**所属 Phase**：2c（合规检测 — Containerd 部分）

**平台范围**：scope 含 `containerd` 时执行；不含 `containerd` 时跳过。

**优先依赖**：Phase 1a（recon）的 MUST 输出必须到位，否则不可启动。

**禁忌**：
- 不执行任何攻击验证命令（攻击验证属于 Phase 4a/4b）
- 不修改远端环境（只读命令 + L0 宿主机观察上下文）
- 不凭记忆判定合规状态 — 每条规则必须由 `ssh_execute` 真实输出支撑
- 不省略规则 — 28 条必须全覆盖，包括 `na` 标记（但必须消灭 `[ ]` 未检查态）

---

## 2. MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `knowledge_graph/nodes/` | Phase 1a | 主机、容器、SA 等节点数据 |
| `scope` 参数含 `containerd` | 入口参数 | 不含则跳过 |
| `session_config.json` | Phase 1a | 含 `server`、`env_fingerprint`（containerd_version 等） |
| `compliance-rules/containerd/_index.md` | 规则库 | 规则索引，按需 Read |
| `compliance-rules/containerd/G_*.md` | 规则库 | 各分组规则详情 |

---

## 3. 核心工作流（4 步）

### 步骤 1：读取规则

1. Read `compliance-rules/containerd/_index.md`，获取 5 个分组文件列表与规则数
2. 根据环境选择要检查的分组：
   - 对照 `env_fingerprint.containerd_version`，若版本过旧则增加相关检查权重
   - 若环境中无 Containerd 则整个 Phase 2c 标记 `na`，跳过
3. 28 条规则量小，1 批完成，直接 Read 全部 5 个分组文件

### 步骤 2：执行检测

对每条规则严格执行：

1. **构造检查命令**：从规则文件中的检查命令模板，结合 `session_config.json` 的 `server` 参数，通过 `ssh_execute` 执行
2. **立即写盘原始输出**：每条 SSH 命令输出立即写入 `evidence/compliance/containerd/raw/`，标注四元组（命令、来源主机、执行上下文 L0、时间戳、退出码）
3. **LLM 语义判定**：基于 SSH 输出和期望值，逐条判定 `pass` / `fail` / `warn` / `na`
4. **fail 项必须附依据**：每条 `fail` 必须包含：
   - 规则 ID（如 Containerd-18）
   - 判定结果：`[x]` fail
   - 判定理由：1-2 句话说明为什么判定为 fail
   - SSH 命令输出引用：引用 `evidence/compliance/containerd/raw/` 中的实际输出
   - 攻击面关联：映射到攻击假设族（如 AS-1 容器逃逸）
5. **SSH 限速**：每批 5-7 条命令，间隔 2 秒；最大并行 3 条；遇到限速自动降级串行

### 步骤 3：判定

对每条规则使用**五态标记**：

| 标记 | 合规含义 | 后续动作 |
|------|---------|---------|
| `[x]` | fail — 存在违规，必须深审 | 必须生成 COMP-CAND 编号，映射到攻击假设族 |
| `[-]` | pass — 已合规 | 记录通过依据 |
| `[!]` | warn — 部分合规或不完全符合 | 记录偏离程度和阻断机制 |
| `[?]` | 存在可疑发现，需 Phase 4b 深审 | 标记候选，移交 Phase 4b |
| `[ ]` | na — 不适用（必须说明原因） | 最终报告前必须消灭所有 `[ ]` 未检查态 |

**判定闭环约束**：
- 所有 `[x]` 和 `[?]` 必须生成 COMP-CAND-NNN 编号
- `[-]` 和 `[!]` 必须写明依据（哪条 SSH 命令的输出证明）
- `[ ]` na 必须说明不适用的原因
- 编号连续无遗漏

### 步骤 4：写入数据

每条规则判定后立即写盘，不持有数据等待：

**写入 `evidence/compliance/containerd/results.json`**：
```json
[
  {
    "rule_id": "Containerd-18",
    "group": "G_5",
    "group_name": "容器运行时",
    "status": "fail",
    "marker": "[x]",
    "comp_cand_id": "COMP-CAND-045",
    "evidence_ref": "evidence/compliance/containerd/raw/containerd_18_runtime.txt",
    "judgment_reason": "容器 runtime-test 以特权模式运行，容器内可访问宿主机所有设备",
    "attack_surface_ref": "AS-1 容器逃逸",
    "cis_mapping": "CIS Containerd Benchmark - 5.x",
    "severity": "critical"
  }
]
```

**写入 `evidence/compliance/containerd/summary.md`**：
- 总规则数 / pass / fail / warn / na
- 按 CIS 分组汇总（G_1 ~ G_5）
- Critical 级别 fail 列表
- 映射到攻击面的违规列表

**写入 `knowledge_graph/nodes/findings_containerd.json`（Containerd 平台分片）**：
- **禁止**与其他平台共享文件。Phase 2 全部完成后由 Pipeline 入口汇总为 `findings.json`（见 OUTPUT_STANDARD §7 并发写入保护协议）
- 去重 key：`id`

**写入 `knowledge_graph/edges/compliance_containerd.json`（Containerd 平台分片）**：
- 每条 fail 规则生成合规边
- 边格式见 OUTPUT_STANDARD §4.2
- **禁止**与其他平台共享文件

**步骤 4b：对象级 compliance 边**

除原有的 `host → finding` 边外，**必须**为每个 finding 追加对象级 compliance 边：

1. 从 finding 的 `judgment` 字段提取违规对象名（Container/Pod/SA/Secret）
2. 对每个违规对象追加 compliance 边：
   ```json
   {
     "edge_type": "compliance",
     "from_node": "container-runtime-test",
     "to_node": "finding-containerd-18",
     "attrs": {
       "rule_id": "Containerd-18",
       "status": "fail",
       "relation": "violates",
       "platform": "containerd"
     }
   }
   ```
3. 原有 `host → finding` 边保留，`attrs.relation` 固定为 `"violates"`
4. 对象节点不存在于 KG 时按节点存在性校验补采

**步骤 4c：finding evidence 字段**

每个 finding 节点的 `data.evidence` 字段**必须非空**，包含：
- `command`：原始 SSH 命令
- `output_summary`：输出摘要
- `raw_ref`：指向 `evidence/compliance/containerd/raw/` 下的原始输出文件路径
- `context`：执行上下文（L0）
- `timestamp`：执行时间

`data.evidence` 为空或缺失 → 该 finding 校验失败。

### 数据写入策略（防并发 + 防丢数据）

1. **JSON Lines 追加模式**：每条规则检测完成后立即追加写入 `evidence/compliance/containerd/results.jsonl`（每行一条 JSON），禁止累积满批再写：
   ```bash
   echo '{"rule_id":"Containerd-18","verdict":"fail","evidence":"...","host":"prod-node-01","ts":"2026-06-20T10:15:30Z"}' >> evidence/compliance/containerd/results.jsonl
   ```
2. **WU 完成时转为 JSON 数组**：
   ```bash
   jq -s '.' evidence/compliance/containerd/results.jsonl > evidence/compliance/containerd/results.json
   ```
3. **平台分片**：findings 写入 `findings_containerd.json`，compliance 边写入 `compliance_containerd.json`（不与其他平台共享文件）
4. **崩溃恢复**：WU 崩溃后从 `results.jsonl` 已有行数继续，不重做已检测的规则；恢复时先 `wc -l results.jsonl` 确定已完成的规则数，跳过对应的规则文件继续执行

---

## 4. 分批策略

28 条规则，**1 批完成**（无需分批）：

### WU-2c-01：G_1 ~ G_5（28 条）

| 分组文件 | 规则数 | 内容 |
|----------|--------|------|
| G_1_runtime_config.md | 3 | 运行环境配置 |
| G_2_daemon_params.md | 3 | 守护进程参数 |
| G_3_file_perms.md | 10 | 文件权限 |
| G_4_image_build.md | 2 | 镜像构建 |
| G_5_container_runtime.md | 10 | 容器运行时（关联 AS-1 容器逃逸） |

**输入输出检查点**：
- 28 条规则全覆盖
- 每条有判定结果（无 `[ ]` 未检查）
- 每条 fail 有判定依据
- G_5 容器运行时（10 条）特别关注：
  - Containerd 容器的特权模式 → AS-1 逃逸
  - Containerd 容器的 capabilities 配置 → AS-1 逃逸
  - 容器 shim 暴露 → AS-1（containerd-shim-escape 攻击模式）
- 通过 → 进入检查点报告阶段

### 上下文控制

- SSH 命令分批执行：5-7 条/批，间隔 2 秒
- WU 完成后写盘摘要到 `evidence/compliance/containerd/raw/summaries/`，释放上下文

---

## 5. 三重校验

### 第一重：规则覆盖校验（WU 完成后）

WU 完成后立即检查：

1. 总规则数 = 28（3+3+10+2+10）
2. 每条规则都有判定结果？（不能有 `[ ]` 未检查）
3. 每条 fail/warn 规则都有判定依据？（SSH 命令输出 + LLM 判定理由）
4. 不通过 → 本 WU 重做

### 第二重：结构完整性校验（Phase 2c 全部完成后）

1. 总规则数 = 28
2. 所有判定都有对应 SSH 命令输出
3. `knowledge_graph/edges/compliance_containerd.json` 中每条 Containerd fail 规则都能找到对应 finding 节点（在 `findings_containerd.json` 中）
4. 五态标记无 `[ ]` 残留
5. 不通过 → 补充缺失规则，直到全部覆盖

### 第三重：检查点报告校验（报告生成前）

1. 报告中每条规则都有判定
2. fail/warn 规则都有判定依据摘要
3. 总计数字 = pass + fail + warn + na = 28
4. 无占位符、无 `[ ]` 未检查
5. 不通过 → 回到本 Phase 补充

---

## 6. MUST 输出

| 文件 | 说明 |
|------|------|
| `evidence/compliance/containerd/results.jsonl` | JSON Lines 格式逐条追加（崩溃恢复用） |
| `evidence/compliance/containerd/results.json` | 28 条规则判定结果（JSON 数组，由 `results.jsonl` 转换） |
| `evidence/compliance/containerd/summary.md` | 按 CIS 分组汇总 |
| `evidence/compliance/containerd/raw/` | 原始 SSH 输出（每条规则一个文件，含标注四元组） |
| `knowledge_graph/nodes/findings_containerd.json` | Containerd 平台分片（去重） |
| `knowledge_graph/edges/compliance_containerd.json` | Containerd 平台分片（去重） |

**Phase 2 全部完成后（2a+2b+2c）立即追加**：
- `reports/compliance_checkpoint_report.md` + `.json`（初稿）

---

## 7. 合规假设映射

每条 `fail` 规则判定后，必须对照 `hypothesis-libraries/compliance-hypotheses.md` 做映射：

1. 读取合规假设库，找到该违规规则对应的攻击假设族
2. 在 `knowledge_graph/edges/compliance_containerd.json` 中生成合规边，`attrs.hypothesis_family` 填写映射结果
3. G_5 容器运行时组（10 条）的 fail 规则优先映射到 AS-1 容器逃逸攻击面

**G_5 特殊映射示例**：

| 规则 | 违规 | 映射攻击面 | 映射攻击模式 |
|------|------|-----------|------------|
| Containerd 容器特权模式 | 特权容器运行 | AS-1 逃逸 | capability-privesc, runc-escape |
| Containerd 容器 capabilities | 危险 capabilities | AS-1 逃逸 | capability-privesc |
| Containerd containerd-shim 暴露 | shim socket 可访问 | AS-1 逃逸 | containerd-shim-escape |
| Containerd 容器挂载敏感路径 | 宿主机路径挂载 | AS-1 逃逸 | procfs-escape |
| Containerd 容器环境变量泄露 | 凭据在环境变量中 | AS-4 数据泄露 | env-credential-leak |

---

## 8. 反幻觉机制

执行本 Phase 时严格遵守六条硬约束：

1. **不准凭记忆出合规结果** — 每条规则的判定必须由 `ssh_execute` 真实执行命令产生，禁止从记忆中编造通过/失败结果
2. **不准伪造 SSH 输出** — 所有 SSH 输出必须真实执行后写入 `evidence/compliance/containerd/raw/`，不得编造或改写
3. **无证据不写确认态** — 只有满足合规确认门槛（可检测 + 可归属 + 影响可说明）3 项的才能写入确认
4. **超出审批范围立即停** — Containerd 合规检测均为 L0 读命令（Level 1 审批），自动通过；如需 L1/L2 命令，须按审批门控执行
5. **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值，不得遗漏

---

## 9. 五态标记系统

本 Phase 使用的五态标记定义（同 OUTPUT_STANDARD §5.2）：

| 标记 | 合规含义 | 闭环规则 |
|------|---------|---------|
| `[x]` | fail — 存在明确违规，必须深审 | 必须生成 COMP-CAND 编号 |
| `[?]` | 可疑发现，需 Phase 4b 深审 | 标记候选，移交 Phase 4b |
| `[-]` | pass — 已合规 | 写明通过依据 |
| `[!]` | warn — 部分合规 | 写明偏离程度和阻断机制 |
| `[ ]` | na — 不适用 | 必须说明原因；最终报告前消灭所有 `[ ]` |

**补充说明**：
- `[x]` fail 和 `[?]` 可疑都会映射到攻击假设族，但 `[x]` 优先级更高
- `[!]` warn 必须标注"偏离标准多少"或"被什么机制阻断"
- `[-]` pass 必须写明是哪条 SSH 命令的输出证明了合规

---

## 10. 断点续传

本 Phase 支持 `progress.json` 驱动的断点续传：

| WU 状态 | 动作 |
|---------|------|
| `complete` | 检查 MUST 输出文件是否都存在且非空 → 存在则跳过，读已有结果继续 |
| `in_progress` | 从 `resumable_from_batch` 继续，只读 summaries/ 中的历史摘要 |
| `pending` | 从头开始执行 |

**WU 完成时**：
1. 写盘 MUST 输出文件
2. 更新 `progress.json` 中对应 WU 状态为 `complete`
3. 写 WU 摘要到 `evidence/compliance/containerd/raw/summaries/`
4. 返回摘要给 supervisory-agent

---

## 11. 独立运行

本技能可独立于 Pipeline 运行：

```bash
/gencpt-containerd-compliance --server prod-node-01 --session-dir /path/to/session
```

**独立运行前提**：
- `session_dir` 内存在 Phase 1a 的 MUST 输出（至少 `knowledge_graph/nodes/` 和 `session_config.json`）
- `scope` 含 `containerd`
- SSH 连通性正常

---

## 12. 特殊说明：G_5 容器运行时

G_5 容器运行时组（10 条规则）直接关联容器逃逸攻击面（AS-1），是 Containerd 合规检测中最关键的分组：

**检测重点**：
- Containerd 容器特权模式 → 特权容器可逃逸至宿主机
- Containerd 容器 capabilities 配置 → 危险 capabilities 可被利用提权（如 SYS_ADMIN、SYS_PTRACE）
- Containerd containerd-shim 暴露 → containerd-shim-escape 攻击模式（Containerd 特有）
- Containerd 容器挂载敏感路径 → /proc、/sys 等宿主机路径泄露
- Containerd 容器环境变量中的凭据 → AS-4 数据泄露攻击面

**这些规则需逐容器检查**（对运行中的每个容器通过 `crictl inspect` 执行），SSH 命令量中等，务必按分批限速规则执行。

**所有 fail 项必须映射到攻击面**，尤其是：
- AS-1 容器逃逸（特权模式、capabilities、shim 暴露、挂载等）
- AS-2 认证授权（Containerd 不当权限配置等）
- AS-4 数据泄露攻击面（环境变量泄露、镜像层泄露等）

**与 Docker 合规的关系**：
- Containerd 合规与 Docker 合规独立执行，不共享规则编号
- 但攻击面映射有重叠（AS-1、AS-4 等），Phase 3 交叉关联会合并处理
- Containerd 特有风险：containerd-shim-escape 攻击模式仅在 Containerd 环境存在

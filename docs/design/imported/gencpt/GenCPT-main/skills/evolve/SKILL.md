---
name: evolve
description: >
  攻击模式进化。分析本次检测的 LLM 推理发现，评估是否晋升为新攻击模式，执行自净。
  可在 Pipeline 末尾用 --evolve 参数触发，也可独立运行。
  不使用场景：检测中、不需要进化模式库时。
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

# evolve — Phase 9 攻击模式进化

本 SKILL 负责分析 Phase 4b 产出的 LLM 推理发现（insights），将经验丰富的发现晋升为新攻击模式，同时对已学习的模式库执行自净和降级，保持攻击模式库的健康度和准确性。本 SKILL 不执行任何 SSH 命令，纯 Markdown 读写和 LLM 语义分析。

---

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| `evidence/insights.md` | Phase 4b | 本次会话的 LLM 推理发现，包含 source=llm_reasoning 的 ATK-CAND 候选 |
| `knowledge_graph/episodic_memory/session_history.md` | 情节记忆 | 跨会话历史记录，用于统计跨会话命中次数和不同环境命中 |
| `attack-patterns/_index.md` | 攻击模式库 | 现有模式列表和每个模式的 hit_count、source、confidence、stale 标记 |
| `hypothesis-libraries/attack-hypotheses.md` | 假设库 | 现有攻击假设卡片，用于判断候选是否能匹配现有假设 |

**前置条件校验**：
1. `evidence/insights.md` 存在且非空（Phase 4b 有产出）
2. `attack-patterns/_index.md` 存在
3. `hypothesis-libraries/attack-hypotheses.md` 存在

任一前置条件不满足 → 立即终止，在 `progress.json` 标记 Phase 9 为 `skipped`，输出 `evidence/evolve/evolve_report.md` 记录跳过原因。

---

## 引用共享规范

执行前必须读取以下共享规范：

| 规范文件 | 用途 |
|---------|------|
| `skills/shared/OUTPUT_STANDARD.md` | 输出格式标准、知识图谱 JSON 格式、五态标记 |
| `skills/shared/SEVERITY_RATING.md` | 严重等级定义，用于为新晋升模式声明 severity |

---

## 晋升门槛（4 项全满足才可晋升）

一个 LLM 推理发现要晋升为攻击模式，必须 4 项全部满足。缺一不可。

### 门槛 ① 差分证明充分

**定义**：L2 执行上下文差分前后证据完整，至少包含 2 个可观测差异。

**检查内容**：
- 存在攻击前环境快照（L0 命令输出，记录攻击前状态）
- 存在攻击操作记录（L2 命令，通过 kubectl exec 模拟容器内攻击者视角执行）
- 存在攻击后状态变化对比（L0 命令输出，记录攻击后状态）
- 攻击前 vs 攻击后至少有 2 项可观测差异（进程、文件、网络、权限、挂载等维度）
- 每个差异必须有对应的 SSH 输出证据文件路径

**否决条件**：只有攻击前或攻击后有快照但无法对比 → 不满足。差异只有 1 项 → 不满足。

### 门槛 ② 探测可复现

**定义**：在不同环境（不同 host_fingerprint）可达同样安全结论。

**检查内容**：
- 探测命令清晰且可直接通过 ssh_execute 或 kubectl exec 执行
- 在历史 session_history.md 中记录过至少 2 次执行，且 2 次执行的环境具有不同的 host_fingerprint
- 2 次执行的结论一致（均确认同一个安全风险存在）
- 探测命令不依赖特定环境的临时状态（如临时上传的文件、临时创建的 Pod）

**否决条件**：仅在单一环境命中过 → 不满足。探测命令依赖特定环境的临时状态 → 不满足。

### 门槛 ③ 无法匹配现有模式

**定义**：与所有现有模式的前置条件和攻击路径都不一致。

**检查内容**：
- 读取 `attack-patterns/_index.md`，获取全部现有模式列表
- 逐个模式比对候选发现与该模式的前置条件集合：
  - 前置条件是否相同或为子集/超集关系
  - 攻击路径（探测命令 → 攻击验证 → 差分证明）是否结构相同
  - 攻击面归属是否相同
- 逐个模式比对候选发现与 `hypothesis-libraries/attack-hypotheses.md` 中的假设卡片：
  - 假设的前置条件是否覆盖了候选发现的前置条件
  - 假设的验证路径是否与候选发现的验证路径一致
- 记录每个模式的比对结果（匹配/不匹配 + 原因），形成比对记录表

**否决条件**：候选发现的前置条件被任一现有模式的前置条件覆盖且攻击路径结构相同 → 不满足（是变体）。

### 门槛 ④ 跨会话命中 ≥2 次

**定义**：在历史 `session_history.md` 中出现 ≥2 次相同 ATK-CAND。

**检查内容**：
- 读取 `knowledge_graph/episodic_memory/session_history.md`
- 搜索与候选发现涉及的攻击路径相关的 ATK-CAND 记录
- 统计不同会话中出现相同或高度相似 ATK-CAND 的次数
- 「相同或高度相似」定义：攻击面相同、前置条件集合相同、攻击路径结构相同、安全结论相同
- 统计次数 ≥2 → 满足

**否决条件**：仅在本次会话出现，历史中无记录 → 不满足。历史中仅出现 1 次且与本次不完全相同 → 不满足。

---

## 核心工作流（5 步）

### 步骤 1：收集洞察

1. 读取 `evidence/insights.md`，提取所有 `source=llm_reasoning` 的 ATK-CAND 候选条目
2. 读取 `knowledge_graph/episodic_memory/session_history.md`，提取历史会话中记录的 ATK-CAND 列表（含会话时间、环境 host_fingerprint、攻击面、ATK-CAND 编号）
3. 读取 `attack-patterns/_index.md`，提取现有模式列表和每个模式的 `hit_count`、`source`、`confidence`、`last_hit`、`stale` 标记
4. 读取 `hypothesis-libraries/attack-hypotheses.md`，提取现有假设卡片列表（含假设编号、前置条件、攻击路径摘要）

**输出**：在内存中构建候选发现列表，每个条目包含 ATK-CAND 编号、攻击面、前置条件集合、攻击路径摘要、差分证明摘要、会话命中记录。

---

### 步骤 2：逐条评估

对步骤 1 收集的每个候选发现，按以下流程评估：

#### 2a：与现有模式比对

将候选发现与 `attack-patterns/_index.md` 中的每个现有模式逐一比对：

| 比对维度 | 判定方法 |
|---------|---------|
| 前置条件集合 | 候选的前置条件是否被现有模式的前置条件覆盖（子集关系） |
| 攻击路径结构 | 探测命令 → 攻击验证 → 差分证明的步骤结构是否相同 |
| 攻击面归属 | 是否属于同一攻击面（AS-1 逃逸至 AS-7 配置） |

**判定结果**：

- **是现有模式的变体** → 更新对应模式的 `hit_count +1`，更新 `last_hit` 为本次会话时间。在候选条目标记"已匹配现有模式：{模式名称}"。不进入晋升门槛检查。
- **是全新发现** → 进入步骤 2b 晋升门槛检查。

#### 2b：晋升门槛检查

对全新发现，逐项检查 4 项晋升门槛（详见上方"晋升门槛"章节）：

| 门槛 | 检查方法 | 满足条件 |
|------|---------|---------|
| ① 差分证明充分 | 检查候选的差分证明条目：攻击前快照 + 攻击操作 + 攻击后变化对比 | L2 差分前后对比证据完整，至少 2 个可观测差异 |
| ② 探测可复现 | 查 session_history.md 中是否存在不同 host_fingerprint 环境下相同结论的记录 | 在 ≥2 个不同环境可达同样安全结论 |
| ③ 无法匹配现有模式 | 逐一比对 _index.md 所有模式 + attack-hypotheses.md 所有假设卡片 | 与全部现有模式的前置条件和攻击路径都不一致 |
| ④ 跨会话命中 ≥2 次 | 查 session_history.md 中相同 ATK-CAND 出现次数 | ≥2 次相同或高度相似 ATK-CAND |

**判定结果**：
- **4 项全满足** → 标记为"可晋升"，进入步骤 3 用户审批
- **不满足任一项** → 记录不满足的门槛项和原因，保留在 insights.md 中标记"暂不晋升：原因【{不满足的门槛项}】"
- **满足 2-3 项** → 标记为"暂存观察"，进入步骤 3 提供选项 3

---

### 步骤 3：用户审批

对每个可晋升候选（4 项全满足）和暂存观察候选（满足部分门槛），使用 当前环境的用户交互工具逐条确认。

**当前环境的用户交互工具询问格式**：

```
候选发现：ATK-CAND-XXX
攻击面：{攻击面名称}
前置条件：{前置条件列表}
攻击路径摘要：{探测命令 → 攻击验证 → 差分证明摘要}
晋升门槛检查：
  ① 差分证明充分：{满足/不满足} — {详细说明}
  ② 探测可复现：{满足/不满足} — {详细说明}
  ③ 无法匹配现有模式：{满足/不满足} — {逐项比对记录摘要}
  ④ 跨会话命中 ≥2 次：{满足/不满足} — {命中次数和会话来源}

请选择处理方式：
  1. 添加为新模式（通过 4 项门槛检查）
  2. 拒绝添加（不满足门槛或质量不足）
  3. 暂存观察（满足部分门槛，等待更多数据）
```

**用户选择后的处理**：

| 用户选择 | 处理动作 |
|---------|---------|
| 选项 1：添加为新模式 | 进入步骤 4 模式创建 |
| 选项 2：拒绝添加 | 在 insights.md 中标记"已拒绝：{拒绝原因}"，不创建模式 |
| 选项 3：暂存观察 | 在 insights.md 中标记"暂存观察：等待门槛【{未满足项}】的更多数据"，记录下次需要收集什么数据 |

**超时处理**：当前环境的用户交互工具超时 10 分钟无响应 → 默认选择"选项 3：暂存观察"，不自动晋升。

---

### 步骤 4：模式创建

对用户选择"添加为新模式"的候选，执行以下创建流程：

#### 4.1 读取晋升模板

读取 `references/promotion-template.md`，获取 8 段结构模板：

1. **前置条件**（L0/L1 探测命令和判断标准）
2. **探测命令**（L0/L1 可执行探测命令）
3. **攻击验证**（L2 攻击命令和操作步骤）
4. **差分证明**（攻击前快照 + 攻击后变化对比）
5. **绕过策略**（阻断场景与绕过方式）
6. **证伪条件**（何时标记为不可利用）
7. **审批级别**（L1/L2/L3 审批级别）
8. **MITRE ATT&CK**（技术编号映射）

#### 4.2 生成新模式 SKILL.md

按模板填写 8 段结构，内容来源于候选发现的 insights.md 记录和差分证明文件。

**frontmatter 格式**（新晋升模式的初始值）：

```yaml
---
name: {pattern-slug}
source: learned
confidence: medium
hit_count: 1
last_hit: {本次会话时间}
stale: false
platforms: [{适用的平台列表，如 k8s, docker}]
attack_surface: {攻击面编号，如 AS-1}
severity: {严重等级，如 Critical}
trigger_rules: [{触发的合规规则编号列表}]
hypothesis_refs: [{关联的假设卡片编号}]
required_tools: []
---
```

- `source` 固定为 `learned`（标识为自动进化产生）
- `confidence` 初始值为 `medium`（新晋升，未经过多次验证）
- `hit_count` 初始值为 `1`（本次晋升计为首次命中）
- `last_hit` 为本次会话的时间戳
- `stale` 初始值为 `false`

> **Frontmatter 字段适用范围说明**：实际模式文件的 9 个基础字段（`source`、`confidence`、`platforms`、`mapped_attack_surfaces`、`mapped_compliance_families`、`required_tools`、`execution_contexts`、`max_verification_level`、`destructive`）适用于所有模式（manual/curated/learned）。`hit_count`、`last_hit` 为 learned 模式特有字段（用于自净和降级判定），manual/curated 模式不需要。`promoted_date`、`created_from` 仅 learned 模式需要。

#### 4.3 写入文件

将生成的 SKILL.md 写入：

```
attack-patterns/{attack-surface}/{pattern-name}/_learned/SKILL.md
```

**路径规则**：
- `{attack-surface}` 为候选发现所属的攻击面目录（如 `escape`、`auth`、`network`）
- `{pattern-name}` 为根据攻击路径特征生成的简短 slug（如 `nfs-hostpath-escape`）
- `_learned/` 子目录标识为自动进化产生，与手工维护的模式区分

#### 4.4 更新索引

更新 `attack-patterns/_index.md`，新增条目：

```markdown
| 模式名称 | 攻击面 | 来源 | 置信度 | hit_count | platforms | 触发条件 | 路径 |
|---------|--------|------|--------|-----------|----------|---------|------|
| {pattern-name} | {attack-surface} | learned | medium | 1 | {platforms} | {触发条件摘要} | {attack-surface}/{pattern-name}/_learned/SKILL.md |
```

同时在条件触发读取表中新增该模式的触发条目。

#### 4.5 更新假设库

更新 `hypothesis-libraries/attack-hypotheses.md`，新增假设卡片：

```markdown
## ATK-HYP-{编号}

- **攻击面**：{attack-surface}
- **前置条件**：{前置条件列表}
- **攻击路径**：{探测 → 验证 → 差分证明摘要}
- **关联模式**：{pattern-name} (_learned)
- **置信度**：medium
- **来源**：learned（由 evolve 从 ATK-CAND-XXX 晋升）
- **创建时间**：{本次会话时间}
```

#### 4.6 更新 _learned_index.md

更新 `attack-patterns/_learned_index.md`（如不存在则创建），新增条目：

```markdown
| 模式名称 | 攻击面 | 来源 | 置信度 | hit_count | stale | 晋升时间 | 晋升自 ATK-CAND |
|---------|--------|------|--------|-----------|-------|---------|----------------|
| {pattern-name} | {attack-surface} | learned | medium | 1 | false | {本次会话时间} | ATK-CAND-{编号} |
```

---

### 步骤 5：自净和降级

遍历 `attack-patterns/_index.md` 中所有 `source=learned` 的模式，根据 hit_count 和未命中连续次数执行自动调整。

#### 5.1 升级规则

| 条件 | 动作 |
|------|------|
| learned 模式 hit_count ≥5 且跨 ≥2 环境（session_history 中记录了至少 2 个不同 host_fingerprint 的命中） | confidence 升级为 `high` |

升级后更新模式 SKILL.md 的 frontmatter `confidence=high`，更新 `_index.md` 和 `_learned_index.md` 对应条目。

#### 5.2 降级规则

| 条件 | 动作 |
|------|------|
| learned 模式连续 5 次会话未命中 | confidence 降级为 `medium`（如果当前是 high） |
| learned 模式连续 10 次会话未命中 | 标记 `stale=true`（标记但不归档，仍保留在模式库中） |
| learned 模式连续 15 次会话未命中 | 使用 当前环境的用户交互工具询问用户是否归档到 `attack-patterns/_archived/` |

**降级判定方法**：
- 从 `session_history.md` 中提取最近 N 次会话的记录
- 对每个 learned 模式，查找最近一次命中的会话序号
- 从最近一次命中会话到当前会话，计算"连续未命中次数"
- 连续未命中次数 = (当前会话序号 - 最近命中会话序号)
- 若该模式在 session_history 中无任何命中记录，连续未命中次数 = session_history 中记录的总会话数

**归档处理**：
- 用户选择归档 → 将模式 SKILL.md 移动到 `attack-patterns/_archived/{attack-surface}/{pattern-name}/SKILL.md`
- 在 `_index.md` 中移除该条目，在 `_learned_index.md` 中标记"已归档"
- 在 `_archived/` 目录下创建 `_archived_index.md` 记录归档模式
- 用户选择不归档 → 重置 stale 标记为 false，hit_count 保持不变，记录用户决策

#### 5.3 manual/curated 模式处理

对 `source=manual` 或 `source=curated` 的模式：
- **只更新 hit_count 和 last_hit**（如果本次会话命中了该模式）
- **不执行降级或归档**（manual/curated 来源永远保持 confidence=high）
- 不修改 confidence 值

#### 5.4 生成进化报告

在 `evidence/evolve/evolve_report.md` 中输出完整的进化报告：

```markdown
# 进化报告 — Phase 9

> 会话时间：{本次会话时间}
> 会话目录：{session_dir}

## 1. 晋升列表

| 序号 | 候选 ATK-CAND | 攻击面 | 新模式名称 | 门槛检查结果 | 用户审批 | 路径 |
|------|--------------|--------|-----------|-------------|---------|------|
| 1 | ATK-CAND-XXX | {攻击面} | {pattern-name} | ①✅ ②✅ ③✅ ④✅ | 添加 | {attack-surface}/{pattern-name}/_learned/SKILL.md |

## 2. 降级列表

| 模式名称 | 攻击面 | 原置信度 | 新置信度 | 原 stale | 新 stale | 降级原因 | 动作 |
|---------|--------|---------|---------|---------|---------|---------|------|
| {pattern-name} | {attack-surface} | high | medium | false | false | 连续 5 次未命中 | 降级 |
| {pattern-name} | {attack-surface} | medium | medium | false | true | 连续 10 次未命中 | 标记 stale |

## 3. 升级列表

| 模式名称 | 攻击面 | 原置信度 | 新置信度 | 升级原因 |
|---------|--------|---------|---------|---------|
| {pattern-name} | {attack-surface} | medium | high | hit_count={N} 跨 {N} 环境 |

## 4. 归档列表

| 模式名称 | 攻击面 | 归档原因 | 用户审批 | 归档路径 |
|---------|--------|---------|---------|---------|
| {pattern-name} | {attack-surface} | 连续 15 次未命中 | 归档 | _archived/{attack-surface}/{pattern-name}/ |

## 5. 变体匹配列表

| 候选 ATK-CAND | 匹配的现有模式 | 匹配维度 | hit_count 更新 |
|---------------|--------------|---------|---------------|
| ATK-CAND-XXX | {pattern-name} | 前置条件子集 + 攻击路径相同 | {N} → {N+1} |

## 6. 暂存观察列表

| 候选 ATK-CAND | 未满足门槛项 | 暂存原因 | 下次需要的数据 |
|---------------|------------|---------|--------------|
| ATK-CAND-XXX | ④ 跨会话命中 ≥2 次 | 历史仅 1 次命中 | 需在另一个环境验证 |

## 7. 统计

| 指标 | 数值 |
|------|------|
| 候选发现总数 | {N} |
| 可晋升数（4 项全满足） | {N} |
| 用户批准晋升数 | {N} |
| 变体匹配数 | {N} |
| 暂存观察数 | {N} |
| 拒绝数 | {N} |
| 升级数（medium → high） | {N} |
| 降级数（high → medium） | {N} |
| 标记 stale 数 | {N} |
| 归档数 | {N} |
| 三库一致性检查 | 通过 / 不通过（{不一致项数量}项） |
```

---

## 一致性维护

进化完成后执行 LLM 语义检查三库一致性。三库指：
1. `attack-patterns/_index.md`（模式索引）
2. `attack-patterns/` 目录下的实际文件（模式 SKILL.md）
3. `hypothesis-libraries/attack-hypotheses.md`（假设卡片）

### 检查项

| 检查项 | 检查方法 | 不一致处理 |
|--------|---------|-----------|
| _index.md 条目 ↔ 实际文件 | _index.md 中每个条目的路径字段指向的文件必须存在 | 文件缺失 → 从 _index.md 移除该条目或标记为缺失 |
| 实际文件 ↔ _index.md 条目 | attack-patterns/ 目录下每个 SKILL.md 必须在 _index.md 中有条目 | _index.md 缺条目 → 新增条目 |
| _index.md 条目 ↔ 假设卡片 | 每个模式的 hypothesis_refs 字段引用的假设卡片必须在 attack-hypotheses.md 中存在 | 假设卡片缺失 → 新增假设卡片或移除引用 |
| 假设卡片 ↔ _index.md 条目 | attack-hypotheses.md 中每个关联模式字段引用的模式必须在 _index.md 中存在 | 模式缺失 → 从假设卡片移除关联或标记为孤儿假设 |
| 编号连续性 | ATK-HYP 编号连续无遗漏 | 编号断档 → 在 evolve_report.md 中记录断档位置 |
| frontmatter 字段完整性 | 每个模式 SKILL.md 的 frontmatter 必须包含 name、source、confidence、hit_count、last_hit、stale、platforms、attack_surface 字段 | 字段缺失 → 补充默认值 |

### 输出

一致性检查结果写入 `evidence/evolve/evolve_report.md` 第 7 节统计部分。

不一致项列表（如有）附加在 evolve_report.md 末尾：

```markdown
## 三库不一致项

| 序号 | 不一致类型 | 位置 | 详情 | 处理动作 |
|------|-----------|------|------|---------|
| 1 | _index.md 条目无对应文件 | _index.md 第 {N} 行 | 模式 {pattern-name} 路径指向的文件不存在 | 从 _index.md 移除条目 |
```

---

## MUST 输出

Phase 9 完成必须输出以下文件，**任一缺失或为空即视为 Phase 未完成**：

| 文件 | 说明 |
|------|------|
| `attack-patterns/{attack-surface}/{pattern-name}/_learned/SKILL.md` | 新晋升的模式文件（如本次有晋升） |
| `attack-patterns/_index.md` | 更新后的索引（含新晋升条目、hit_count 更新、confidence 更新、stale 更新） |
| `hypothesis-libraries/attack-hypotheses.md` | 更新后的假设库（含新假设卡片） |
| `evidence/evolve/evolve_report.md` | 进化报告：晋升列表 + 降级列表 + 升级列表 + 归档列表 + 变体匹配列表 + 暂存观察列表 + 统计 + 三库一致性检查 |

**无晋升时的输出**：即使本次无候选晋升，也必须输出 evolve_report.md（记录零晋升原因、变体匹配统计、降级/升级/归档操作、三库一致性检查结果）。

---

## 独立运行参数

```bash
/gencpt-evolve --session-dir /path/to/session
```

**独立运行说明**：
- 可独立于 Pipeline 运行，只需指定 session 目录路径
- 从 `{session-dir}/` 读取所有 MUST 输入文件
- 输出文件写入 `attack-patterns/`（全局攻击模式库）和 `{session-dir}/evidence/evolve/evolve_report.md`
- 独立运行时无 supervisory-agent 调度，直接执行完整 5 步工作流

**Pipeline 内运行**：在 Pipeline 末尾使用 `--evolve` 参数触发，supervisory-agent 在 Phase 8c 完成后调度 evolve sub-agent 执行。

---

## 检查点

Phase 9 完成判定需全部通过：

1. **所有候选发现有处理结论** — insights.md 中每个 source=llm_reasoning 的 ATK-CAND 都有处理结果（晋升/拒绝/暂存/变体匹配），无遗漏
2. **晋升门槛完整检查** — 每个可晋升候选的 4 项门槛都有明确检查记录（满足/不满足 + 详细说明）
3. **用户审批记录** — 每个晋升和归档操作都有 当前环境的用户交互工具的用户审批记录
4. **三库一致性** — _index.md 条目 ↔ 实际文件 ↔ 假设卡片，编号连续，frontmatter 字段完整
5. **evolve_report.md 完整** — 包含 7 个章节（晋升列表、降级列表、升级列表、归档列表、变体匹配列表、暂存观察列表、统计），无空章节

---

## WU 摘要格式

evolve 完成后向 supervisory-agent 返回上行摘要，同时写盘到 `evidence/evolve/summaries/evolve_summary.json`：

```json
{
  "work_unit_id": "WU-9-01",
  "status": "complete",
  "summary": "分析 {N} 个候选发现，晋升 {N} 个新模式，降级 {N} 个，升级 {N} 个，归档 {N} 个，变体匹配 {N} 个",
  "critical_findings": [
    "新晋升模式：{pattern-name}（来自 ATK-CAND-XXX，攻击面 {attack-surface}）",
    "降级模式：{pattern-name}（high → medium，连续 5 次未命中）",
    "归档模式：{pattern-name}（连续 15 次未命中，用户批准归档）"
  ],
  "files_written": [
    "evidence/evolve/evolve_report.md",
    "attack-patterns/_index.md",
    "hypothesis-libraries/attack-hypotheses.md",
    "attack-patterns/{attack-surface}/{pattern-name}/_learned/SKILL.md"
  ],
  "context_used": [
    "evidence/insights.md",
    "knowledge_graph/episodic_memory/session_history.md",
    "attack-patterns/_index.md",
    "hypothesis-libraries/attack-hypotheses.md",
    "references/promotion-template.md"
  ],
  "issues": []
}
```

---

## 禁止事项

- **不准跳过晋升门槛** — 4 项门槛必须逐项检查并记录结果，不得跳过任何一项
- **不准自动晋升** — 必须经过 当前环境的用户交互工具用户审批，不得自动将候选添加为新模式
- **不准跳过用户审批归档** — 连续 15 次未命中时必须询问用户，不得自动归档
- **不准降级 manual/curated 模式** — manual/curated 来源永远保持 confidence=high，只更新 hit_count 和 last_hit
- **不准伪造差分证明** — 差分证明必须来自实际的 SSH 输出文件，不得凭记忆编造
- **省略词零容忍** — 输出中不得出现"等"、"..."、"+(数量后缀)"、"大致"、"约"
- **占位符必须替换** — 所有【xxx】占位符必须替换为实际值
- **不准跳过三库一致性检查** — 进化后必须执行三库一致性检查并记录结果

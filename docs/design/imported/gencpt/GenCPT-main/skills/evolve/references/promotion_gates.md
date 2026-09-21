# evolve 4 项晋升门槛详细规则与用户审批流程

> 本文件为 `skills/evolve/SKILL.md` 的晋升门槛和用户审批参考。核心工作流见 SKILL.md。

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

## 步骤 2b：晋升门槛检查

对全新发现，逐项检查 4 项晋升门槛：

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

## 步骤 3：用户审批

对每个可晋升候选（4 项全满足）和暂存观察候选（满足部分门槛），使用当前环境的用户交互工具逐条确认。

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

## 步骤 4：模式创建

对用户选择"添加为新模式"的候选，执行以下创建流程：

### 4.1 读取晋升模板

读取 `references/promotion-template.md`，获取 8 段结构模板：

1. **前置条件**（L0/L1 探测命令和判断标准）
2. **探测命令**（L0/L1 可执行探测命令）
3. **攻击验证**（L2 攻击命令和操作步骤）
4. **差分证明**（攻击前快照 + 攻击后变化对比）
5. **绕过策略**（阻断场景与绕过方式）
6. **证伪条件**（何时标记为不可利用）
7. **审批级别**（L1/L2/L3 审批级别）
8. **MITRE ATT&CK**（技术编号映射）

### 4.2 生成新模式 SKILL.md

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

### 4.3 写入文件

将生成的 SKILL.md 写入：

```
attack-patterns/{attack-surface}/{pattern-name}/_learned/SKILL.md
```

**路径规则**：
- `{attack-surface}` 为候选发现所属的攻击面目录（如 `escape`、`auth`、`network`）
- `{pattern-name}` 为根据攻击路径特征生成的简短 slug（如 `nfs-hostpath-escape`）
- `_learned/` 子目录标识为自动进化产生，与手工维护的模式区分

### 4.4 更新索引

更新 `attack-patterns/_index.md`，新增条目：

```markdown
| 模式名称 | 攻击面 | 来源 | 置信度 | hit_count | platforms | 触发条件 | 路径 |
|---------|--------|------|--------|-----------|----------|---------|------|
| {pattern-name} | {attack-surface} | learned | medium | 1 | {platforms} | {触发条件摘要} | {attack-surface}/{pattern-name}/_learned/SKILL.md |
```

同时在条件触发读取表中新增该模式的触发条目。

### 4.5 更新假设库

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

### 4.6 更新 _learned_index.md

更新 `attack-patterns/_learned_index.md`（如不存在则创建），新增条目：

```markdown
| 模式名称 | 攻击面 | 来源 | 置信度 | hit_count | stale | 晋升时间 | 晋升自 ATK-CAND |
|---------|--------|------|--------|-----------|-------|---------|----------------|
| {pattern-name} | {attack-surface} | learned | medium | 1 | false | {本次会话时间} | ATK-CAND-{编号} |
```

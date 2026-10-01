# 检查点账本模板（Check Point Ledger）

## 职责与定位

本模板定义候选发现阶段（`candidate-discovery`）的**检查点（check point）**规划与终态对账结构，运行时产物为 `check_point_ledger.tsv`。检查点是从三份冻结清单（file/sink/source inventory）**客观派生**的完整闭合最小单位；每个检查点执行后取得**恰好一个终态**。Gate-1 的候选发现闭合以检查点集合为准。

**生产者**：`candidate-discovery` 阶段（宿主在派发前从冻结清单派生检查点，执行后回填终态）。
**消费者**：Gate-1（七条对账等式）、Gate-2（漏点抽查）、报告阶段（覆盖披露）。

`mechanism` 复用 [`discovery_source`](enum-registry.md#discovery_source) 的三个机器值（`pattern_driven` / `business_logic` / `lateral_diff`），表示该检查点上运行的发现机制。本模板不提供也不计划提供 JSON Schema 或 validator。

## 检查点派生规则（从冻结清单，禁止自由少规划）

检查点计划从阶段0 的三份冻结清单**客观派生**，不允许 LLM 自由少规划（这是"计划内闭合≠客观全量"根因的直接修复）：

- 每个 sink ∈ `sink_inventory.tsv` → 至少 1 个**回溯检查点**（sink→source 反向追踪）；
- 每个 source ∈ `source_inventory.tsv` → 至少 1 个**前向检查点**（source→sink 前向追踪）；
- 每个文件 ∈ `file_inventory.tsv` → 至少 1 个**终态检查点**（文件级兜底，预筛/深扫两条路径之一给终态——v0.4 起无浅扫中间态）。

一个检查点覆盖一个清单元素（`basis_id`）；同一元素可派生多个检查点（不同机制/不同方向），但**每个元素至少被覆盖一次**。

## 检查点四终态

| 终态 | 语义 | 必填 |
|---|---|---|
| `candidate` | 产出候选 | `candidate_ids` 非空 + 证据链五段 + `reason` |
| `disproved` | 证伪（证明无该类漏洞） | 证据 + `reason` |
| `blocked` | 环境阻碍（缺输入/权限/预算） | `reason` + `resume_entry` |
| `not_applicable` | 不适用（**仅限可证明安全类理由**） | 规则名 + 证据 + `reason` |

**全终态理由封闭枚举（v0.3.9，防伪闭合扩展到全终态）**：

| 终态 | 合法理由前缀 | 必须携带 | 允许方向 |
|---|---|---|---|
| `candidate` | `cluster_conclusion:` | 簇文件路径 | backward/forward |
| `disproved` | `cluster_conclusion:` / `disproved_safe:` / `false_rule_hit:` | 证据引用（`disproved_safe:` 至少 1 条观测事实 file:line 或 audit 行号） | backward/forward / 任意 / 任意 |
| `blocked` | `budget:` / `user_decision:` / `permission:` | `capability_gap_refs` 非空 + failed_wus.txt 登记（basis_id） | 任意 |
| `not_applicable` | `false_rule_hit:` / `disproved_safe:` / `cluster_conclusion:` / `prefilter_no_exec:` | 规则名+证据；`prefilter_no_exec:` 仅文件 terminal 方向 | 同 v0.3.3 表 |

**禁止**：`structural_assessment:` / `light_scan_assessment:` / `heuristic` / `noisy` 等一切未登记的批量贴标理由；"没看"只能留 `未检查` 或 `blocked`（带合法阻塞前缀）。`cluster_conclusion:` 理由必须引用 clusters/ 结论文件路径。Gate-1 方程「反伪闭合(全方向)」「全终态理由封闭」逐行机器校验本表。

非终态只有 `未检查`（planned 但尚未执行，闭合后必须为 0）。终态四选一，`candidate` / `disproved` / `blocked` / `not_applicable`，各带理由。

## TSV 列定义

`check_point_ledger.tsv` 列（制表符分隔）：

```text
basis_id | direction | mechanism | check_point_id | candidate_ids | terminal_state | reason | concluded_at
```

| 列 | 说明 |
|---|---|
| `basis_id` | 覆盖的清单元素 id（sink_id / source_id / 文件路径），与三份清单的 id 列一致 |
| `direction` | `backward`（回溯）/ `forward`（前向）/ `terminal`（文件终态）/ `fix_presence`（负数 sink：知识库锚定的修复存在性检查）/ `hypothesis`（A5 发散假设，v0.4：必须带可解析锚点，≤20/轮；A5 subagent 追加写账本行，主代理可复核） |
| `mechanism` | `pattern_driven` / `business_logic` / `lateral_diff`，或文件终态为 `prefilter` / `deep_scan`（**v0.4 废除浅扫 light_scan**：文件结论只有「机械排除」或「真实分析」两条路）；`fix_presence` 方向恒为 `knowledge_anchored`；`hypothesis` 方向恒为 `divergent_reasoning` |
| `check_point_id` | 稳定唯一 id，创建后不可变 |
| `candidate_ids` | 产出的候选 id，分号分隔；无候选为空 |
| `terminal_state` | 四终态之一；执行前为 `未检查`；`fix_presence` 方向的终态为 `fix_present`（附证据行）/ `fix_absent`（必须产出候选）/ `blocked`（附 capability_gap_refs，进 failed_wus）三选一 |
| `reason` | 终态理由/证据引用；`disproved`/`blocked`/`not_applicable` 必须非空；`disproved_safe:` 必须携带 file:line 证据引用 |
| `concluded_at` | 终态落盘时刻（UTC ISO 8601）；Gate-1 方程「时序检查」：必须晚于所引用的 audit_log 观察时间 |

## 闭合等式

```text
planned_check_points == terminal_check_points
```

- `planned` 等于派生时的检查点全集；`terminal` 等于取得四终态之一的检查点全集。
- 集合完全相等（无遗漏、无多余），且不存在停留在 `未检查` 的检查点，每个检查点恰好一个终态。
- candidate 数量不参与闭合等式。
- 对账由宿主执行 [`host-reconciliation-commands.md`](host-reconciliation-commands.md) §4c 一体块（gate-1.py 全部方程），不是 LLM 自报；对账常数动态推导。

## 终态不可改写 + 新线索追加重新闭合

1. 检查点终态**不得被改写**：`candidate`/`disproved`/`blocked`/`not_applicable` 一旦写入即冻结，不回退、不改判。
2. 执行中发现新线索（新 sink/source/文件，或新可达路径），**追加新检查点**（新增 `basis_id` 覆盖或新方向）并重新闭合，不回退已完成结论。
3. 追加的检查点须披露 `added_after_freeze=true` 与 `addition_reason`，并重过 Gate-1 七等式。

## 写入纪律

1. 检查点在三种机制派发执行**前**从冻结清单派生，派生时 `terminal_state=未检查`。
2. `check_point_id` 创建后不可变（遵循 [`../shared/field-ownership.md`](../shared/field-ownership.md) 写权限纪律）。
3. 执行后回填终态与 `candidate_ids` / `reason`；`blocked` 必须写 `resume_entry`；`not_applicable` 必须写规则名+证据（见 [`../shared/prefilter-rules.md`](../shared/prefilter-rules.md)）。
4. 不得通过事后缩减 planned 集合制造闭合假象；规划全集确定后只能追加（补规划），不能删除。
5. 启用 WU 时，检查点终态分布在各 WU 分片中记录，宿主串行汇聚后合并为账本级 `planned`/`terminal` 再闭合；ID 段不重叠，闭合等式仅在账本级执行。

## 逐检查点证据账本 audit_log.tsv（v0.3.9）

`audit_log.tsv` 是每个已执行检查点的证据行（一行一终态），由候选发现阶段在执行时同步写入：

```text
check_point_id | basis_id | direction | result | evidence_type | evidence_ref | reviewed_at
```

| 列 | 说明 |
|---|---|
| `check_point_id` | 与 check_point_ledger.tsv 的检查点一一对应 |
| `basis_id` / `direction` / `result` | 与账本同值（result 即终态） |
| `evidence_type` | `direct`（源码直接观察）/ `indirect`（推断）/ `unknown`（仅 blocked 允许） |
| `evidence_ref` | 可解析引用：file:line、clusters/{cluster_id}.md 节号、FALSE-rules 规则号之一（cve-index 行号已随 fix_presence 禁止派生废弃——v0.11.1 U-A2 标注，历史值保留） |
| `reviewed_at` | UTC ISO 8601 |

规则：**一行一观察**（v0.4）——一个检查点可有多条观察行（逐跳/逐事实各一行），`evidence_ref` 必须可解析（Gate-1 方程「audit 双向覆盖」「引用可解析」「档位诚实」校验）；观察**先落盘后引用**（执行时实时追加，带 reviewed_at 时间戳，「时序检查」）；`evidence_type=unknown` 仅允许出现在 blocked 终态。

## 负数 sink：fix-presence 检查点（v0.3.9；**v0.4.3 起禁止派生**——CVE 不作工作项，闭卷验收在包外；枚举值物理保留仅供历史解读）

派生来源**只允许** knowledge/entries/cve-index.tsv 中 version-range 覆盖目标版本的 CVE 条目（每 CVE 一个检查点），LLM 不得自由增删：

- `basis_id` = CVE 编号；`direction` = `fix_presence`；`mechanism` = `knowledge_anchored`；
- 终态：`fix_present`（附目标源码中该检查已存在的证据行）/ `fix_absent`（附缺失证据，**必须产出候选**）/ `blocked`（附 capability_gap_refs，进 failed_wus.txt）；
- 闭包：cve-index 中每个覆盖目标的 CVE 必须有检查点且终态非未检查；**CVE 召回=包外 acceptance**（由宿主执行 `tests/acceptance/acceptance.py` 对 `tests/golden/` 锚点闭卷验收，非 Gate-1 方程）。

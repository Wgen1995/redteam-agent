---
name: candidate-discovery
description: 阶段1 候选全量发现——检测引擎主序列第二步。在三份冻结清单（file/sink/source inventory）上派生检查点（每 sink 一回溯点、每 source 一前向点、每文件一终态点，禁止自由少规划），以三机制（pattern_driven/business_logic/lateral_diff）在矩阵检查点上运行，走批式流水线（预筛→深扫），产出候选清单与 check_point_ledger.tsv 四终态闭合。不适用场景：候选是否真实/可利用/最终严重度的精细判断（属于 verification-and-rating）。
---

# 阶段1：候选全量发现（矩阵闭合 + 批式流水线）

> 依据：设计 28 号 §3.2（环2 矩阵闭合）、§3.3（环3 五态账本）、§3.4（预筛规则）、§6（规模）。本阶段在三份冻结清单上运行，产出候选与检查点账本闭合证据。宁滥勿缺：本阶段不筛掉候选、不做验证结论。

## 目标

1. 检查点从三份冻结清单**客观派生**（每 sink 至少一个回溯点、每 source 至少一个前向点、每文件至少一个终态点），**禁止 LLM 自由少规划**。
2. 三机制（模式驱动 / 业务逻辑 / 横向差异）在矩阵检查点上运行，产出候选。
3. 批式流水线（预筛 → 深扫）保证规模可跑且全程全量。
4. check_point_ledger.tsv 四终态闭合（planned == terminal），candidate 数量不参与闭合等式。

## 硬性约束（不可违反）

1. **检查点从冻结清单派生**：不得凭"我觉得重点查哪里"自由规划。派生规则见 [`../../contracts/check-unit-ledger-template.md`](../../contracts/check-unit-ledger-template.md)。
2. **宁滥勿缺**：本阶段不写 `verification_verdict`、不判 `refuted`，不确定也报候选，验证留给阶段2。
3. **预筛只分流不排除**：预筛命中排除规则才能标 not_applicable，且必须记录规则名+证据（确定性排除规则 100% 确定，不设抽样复核）（见 [`../../shared/prefilter-rules.md`](../../shared/prefilter-rules.md)）；**FALSE-rules 前置剪枝**：命中 [`../../knowledge/FALSE-rules.md`](../../knowledge/FALSE-rules.md) 忽略场景的候选不产出并写 `false_rule_hit` 留痕，任何冲突以 FALSE-rules 为准（其多态反序列化硬例外除外——该情形不忽略）。
4. **证据链五段缺一拒收**：深扫产出的候选，证据链必须含 source/propagation/sanitizers/sink/disproof_checked 五段，缺一段即拒收。
5. **三铁律**：单层不嵌套、各自分片、主 agent 串行合并（见下文"分片与汇聚"）。
6. **全自动红线**：禁止"已找到 N 个候选，是否继续"这类中途提问；进度只写 live_findings_index.md 供用户自查（见 [`../../shared/human-in-the-loop.md`](../../shared/human-in-the-loop.md)）。
7. **横切纪律**：候选身份字段创建时一次性写入、此后不可变；下游阶段只读不改，写权限见 [`../../contracts/field-ownership-table.md`](../../contracts/field-ownership-table.md)；事实性声明必须可追溯到真实读取证据（见 [`../../shared/anti-hallucination.md`](../../shared/anti-hallucination.md)）。
8. **discoverable=否 类别的硬约束（无模式 sink 兜底）**：凡 `sink_inventory` 命中了 `knowledge/sinks/_index.md` 中 `discoverable=否`（或"部分"）类别的实例，其检查点终态必须是 `candidate`（经业务逻辑或横向差异机制产出）或 `not_applicable`（附理由）或 `blocked`（附原因），并强制写 `capability_gap_refs`；**禁止静默无产出**——grep 命中却无候选且无任何登记的检查点是完整性缺口。

## 输入

| 名称 | 说明 |
|---|---|
| 三份冻结清单 | `file_inventory.tsv` / `sink_inventory.tsv` / `source_inventory.tsv`（阶段0 产出，冻结不可改） |
| 威胁语境文档 | `threat-context.md`（保守假设清单 + 输入三分类） |
| 技术栈探测结果 | 检测到的语言/框架，用于知识条目过滤 |
| 知识快照 | `knowledge_snapshot_id`（run 级冻结） |

## 执行步骤

### 1. 检查点派生（从冻结清单，禁止自由少规划）

按 [`../../contracts/check-unit-ledger-template.md`](../../contracts/check-unit-ledger-template.md) 从三份冻结清单客观派生检查点，写入 `check_point_ledger.tsv`：

- 每个 sink ∈ sink_inventory → 至少 1 个**回溯检查点**（sink→source 反向追踪）；
- 每个 source ∈ source_inventory → 至少 1 个**前向检查点**（source→sink 前向追踪）；
- 每个文件 ∈ file_inventory → 至少 1 个**终态检查点**（文件级兜底）；
- 每个检查点终态四选一：`candidate`（产出候选）/ `disproved`（证伪+证据）/ `blocked`（环境阻碍+原因）/ `not_applicable`（不适用+理由）。

派生后 `planned == terminal` 闭合等式由 Gate-1 用宿主 shell 命令核对（见 [`../../shared/quality-gates.md`](../../shared/quality-gates.md) 与 [`../../contracts/host-reconciliation-commands.md`](../../contracts/host-reconciliation-commands.md)），不是 LLM 自报。

### 2. 三机制（保留，在矩阵检查点上运行）

三种发现机制推理性质不同，缺一不可；均在检查点上运行，不在本阶段重复做范围界定：

- **pattern_driven（模式驱动）**：对检查点比对已知漏洞模式签名（注入/路径穿越/反序列化等），命中即产出候选，记录 `vuln_pattern_refs`。只命中目录名而无可执行模式（Source/Propagation/Sanitizer/Sink 四段不全）不能称模式驱动发现。
- **business_logic（业务逻辑）**：对可控输入路径先推断"本来应怎么运作"，再检查实际偏离；偏离即产出候选，记录预期行为与实际偏离点。可发现尚无 UVS-* 的候选，写 `capability_gap_refs` 进知识演进。
- **lateral_diff（横向差异）**：按路由模式/所属类/共享 helper 分组相似处理器，组内比较标记离群项；离群即产出候选，记录对照组构成。可发现尚无 UVS-* 的候选，写 `capability_gap_refs`。

同一候选被多机制命中时，`discovery_source` 数组合并全部命中机器值。

### 3. 批式流水线（预筛 → 深扫）

每块走完「预筛→深扫→K 改写→wake→再取下一块」。禁止把「验证→findings 才进下一批」当权威。分片与并发见下文"分片红线"。

#### 3.1 预筛（确定性 grep 分流，0 模型调用）

- 引用 [`../../shared/prefilter-rules.md`](../../shared/prefilter-rules.md)：三条排除规则（无执行面文件 / 无危险 API / 生成构建产物）**全部满足**才可标 `not_applicable`，必须记录规则名+证据（不设抽样复核）。
- 预筛是 grep 分流，不是排除；未命中任何预筛规则的文件必须进深扫。
- 预筛复用 sink 双轨模式 + 入口特征，命令见 [`../../contracts/host-reconciliation-commands.md`](../../contracts/host-reconciliation-commands.md)。

#### 3.3 深扫（污点链追踪，strong 模型，两级聚类闭合）

- 深扫覆盖全部矩阵点（每 sink 回溯≥1 层 source、每 source 前向≥1 次），可"粗做"不可"不做"。**逐实例深扫在 5 万+ 检查点规模不可行，必须两级聚类执行**：
  1. **聚簇**：把 sink 检查点按 `cluster_id = hash(sink_type, symbol)` 聚簇（同类型同符号调用点为一簇；文件级终态检查点按 file 聚簇）；每簇一个深扫 WU。
  2. **簇内处置**：每簇选代表性实例做完整污点链（五段证据），簇内其余实例做结构一致性核对（同 source 模式/同控制点/同 sink 结构的兄弟实例），一致性核对结果写簇记录。
  3. **按簇闭合检查点**：簇内全部检查点据簇结论落终态（candidate/disproved/blocked/not_applicable），禁止留"未检查"；簇记录落盘 `clusters/` 目录并登记进 check_point_ledger。**簇产物强制（v0.3.3 新增）**：`clusters/` 目录必须存在；每簇至少一个结论文件（`clusters/{cluster_id}.md`：代表性实例五段证据链 + 簇内结构一致性结论 + 终态映射）；**backward/forward 检查点的 `not_applicable` 理由必须为 `cluster_conclusion:` 前缀并引用所属簇结论文件**（见 check-unit-ledger-template 理由封闭枚举）；**未聚簇的 sink/source 检查点不得落任何终态**——没有簇结论的"批量 not_applicable"是伪闭合，Gate-1 拒绝。
  4. **簇级硬门**：每 sink 类型至少一个簇完成回溯、每 source 类型至少一个簇完成前向；源文件全部检查点随所属簇闭合。
- 污点链追踪规则（簇内代表性实例与抽查实例均适用）：
- **分段续追**：单 WU 追到 8 跳或 Read 10 文件即落盘（当前最远节点 + visited + pending），下一 WU 接力；多段=无限深度，每段不爆上下文。
- **防环路**：`visited={file:line:method}`，回到已访问节点停该分支不停整链。
- **多分支**：每跳枚举全部上游 caller 逐一追到底，禁止"只追最像的一个"。
- **每跳必带 read_evidence**（Read 原文）。
- **每跳就地落盘 hop_snippet（v0.3.4 新增，设计 34 号第4节）**：深扫写入簇结论时，证据链每跳必须带 hop_snippet（前后3行原文 + 关键行标记，字段见 candidate-finding.md v0.3.4 增补）；语义变迁随跳写 semantic_transitions。报告阶段禁止重读源码补片段——详情报告"调用链/语义变迁"两节只能从簇结论投影。
- **证据链五段**（source/propagation/sanitizers/sink/disproof_checked）缺一段即拒收。
- **source 分级**：到达入口/请求参数 → `user_controllable=true`；db/cache/mq/config → `secondary` 继续追；字面量/static final → `disproof`；接力完仍无 source → `no_path_to_input`；单段到上限 → `partial_trace` 交接，**禁止中途判证伪**。

### 4. 分片红线（module→subdir 递归切分）

- 按 module→subdir 递归切分；**每子代理负载红线 ≤30w 行**（防压缩丢数据）。
- **batch_size=10**（唯一权威，与 SKILL.md 一致）：只限并发 Analyzer 数，不是切批依据（宿主 subagent fan-out；无 subagent 时串行并标注独立性降级，见 [`../../shared/deployment-environment.md`](../../shared/deployment-environment.md)）。
- 分片达到红线后不再塞任务，递归细分到 subdir 级别。

### 5. subagent 显式 handoff 契约（v0.3.7，设计 36 号）

每个 WU 的派发 prompt 必须显式携带五要素（task-brief 原则：subagent 只收本 WU 的 brief，禁止让它读整个 PhasedLine/计划表，防上下文污染），禁止 subagent 隐式继承主会话上下文：

1. 分配定义：本 WU 覆盖的簇定义（sink_type 乘 symbol）或文件行范围（计划表行号区间）；
2. 上游产物绝对路径：本 WU 需要的三清单行、日志文件、已冻结上游产物的绝对路径清单（不超过 10 个）；
3. 本阶段技能文件路径：candidate-discovery/SKILL.md 与 shared 规则的绝对路径（subagent 自行 Read）；
4. 输出分片路径：本 WU 唯一的分片文件绝对路径（禁并行写主产物）；
4b. **跨平台铁律（v0.7.2）**：subagent 的一切临时文件/中间产物只能写入本 WU 分片路径所在目录（session_dir 树内）——**禁止使用系统 /tmp 或 $TEMP**（Windows 无 /tmp、部分容器 TEMP 只读）；禁止因「需要临时目录」向用户请求权限；
5. 反偷懒约束段：五态判定、schema 要求、禁止合并批、禁止静默跳过的红线摘要。

父代理回收 subagent 结果时必须核对：分片存在、非空、schema 字段齐全、覆盖了分配范围；缺任一即拒绝并重提示（GenCPT/codex 同款纪律）。

### 6. WU 五态与逐 WU 验证

- WU 等于批内最小追踪单元，状态**靠输出分片文件存在性判定**（幂等可续），见 [`../../contracts/work-unit-manifest-template.md`](../../contracts/work-unit-manifest-template.md)：未开始（无分片文件）/ 运行中（已派发）/ 已完成（分片文件存在且非空）/ 已验证（分片文件通过逐 WU 验证）/ 失败（重试≤3 次仍失败）。
- **逐 WU 验证**：文件存在 + 合法 JSON + wu_id + Schema 字段；失败重试≤3 次，仍失败进 `failed_wus.txt`。
- `failed_wus.txt` 在报告中强制引用：应为空，或逐条列入报告"未分析清单"。

### 7. 分片与汇聚（三铁律）

1. **单层不嵌套**：子代理不再起子代理。
2. **各自分片**：每个 WU 只写自己的分片文件，禁止并行写主候选清单。
3. **主 agent 串行合并**：合并前 count 临时文件数 == 批数，按 shard 序号排序后串行合并（命令见 [`../../contracts/host-reconciliation-commands.md`](../../contracts/host-reconciliation-commands.md) 第5节）。

### 8. 两档深度（不存在"预算"，只有"单次派发的追踪深度上限"）

| 档 | 执行方式 | 模型 | 覆盖要求 |
|---|---|---|---|
| 预筛 | 确定性 grep（sink 双轨 + 入口特征） | 0 模型调用 | 全部文件 |
| 深扫 | 污点链追踪 | strong | 全部矩阵点 |

- **单次 Task 派发的追踪深度受限于该次上下文，不是覆盖率的谈判筹码**：单跳回溯 → 3 跳 → 完整链，**禁止借口"追踪深度有限"删除范围/矩阵点**——追不到底就交接给下一个 WU 接力（`wu-analyzer-prompt.md`"分段续追"机制），不是放弃这个检查点。
- 单次派发追踪深度触顶 → 标 `blocked`（reason=budget:，附最远节点/已知信息，供下一 WU 从此接力——`budget:` 是 gate 校验用的固定状态码，含义是"这次派发追到这就是极限"，不是"放弃"），**列入下一次续跑队列，不接受"缩小范围重新协商"**——不静默截断，不永久放弃，只是这一跳的深度分析交给下一次派发继续（见 [`../../shared/deployment-environment.md`](../../shared/deployment-environment.md) 与 [`../../shared/human-in-the-loop.md`](../../shared/human-in-the-loop.md)）。

### 9. 逐 sink 真实分析与闭合（v0.4 慢速诚实）

- **禁批量闭合、禁选择性深扫**：全部 sink/source/文件终态逐条真实分析——禁止「关键集群/重要组件/最高风险优先」类选择性措辞与做法（每一条都要有结论与证据，没有豁免）；每个 sink 一行独立结论（backward）、每个 source 一行（forward），每行必须带自己的证据；cluster_conclusion: 引用真实存在的簇文件且不得作为批量闭合理由（一个簇引用覆盖 ≤50 检查点，Gate「证据唯一性」）；文件终态只有 prefilter（0命中证据）/ deep_scan（真实分析）/ blocked 三条路。
- **确定性 ID 派生示例**（candidate_id = C-{sink_seq}-{source_seq}-{sig8}）：sink_seq/source_seq 是该候选在冻结清单 UTF-8 字节序排序中的**实际位置序号**（不是候选序号、不是占位）——例：位置 java/a/B.java:10 在 sink_inventory 排序后第 42 行 → sink_seq=00042；sig8 = md5("java/a/B.java:10:SINK-DESERIALIZE") 前 8 位；无 sink 候选取文件终态检查点序 + md5(file:line)。gate[候选 ID 反查] 逐条反查。
- **audit_log 一行一观察**：每观察到一个事实就实时追加一行（file:line + 观察内容 + reviewed_at），**先落盘后引用**（被引用的观察必须先于结论存在，Gate「时序检查」）。
- **推导链 O→J→V**：结论行必须链到 ≥1 条 audit_log 观察行（check_point_id 一致，Gate「推导链强制」）；证伪必须带观测事实（disproved_safe 附 file:line），不得只有结论没有观察。
- 终态**不得被改写**；新线索（新 sink/source/文件）追加检查点并重新闭合。
- **WU 分片闭环**：大目标按模块/目录切 WU，每 WU 独立闭环（检查点子集+终态+缺口清单），汇聚=无重叠并集（Gate gate[时序检查]）。
- 单次派发内追不完的 sink 标 blocked（budget:/user_decision:/permission: + capability_gap_refs）并逐条登记 failed_wus.txt，禁止贴标签假装看过——`budget:` 前缀表示"下一次派发接着追"，不是"放弃"。

### 9b. A5 发散轮（v0.4，结构化矩阵闭合后一轮）

- **L2 时序**：L1 工作集空之后，先把 candidate 的 flow 上游未查卡标 `source=neighborhood` 入工作集，再跑本轮 ≤20 假设。
- 独立上下文子代理（红队头脑风暴者）：输入=攻击面地图+威胁语境+簇分析抽样+已确认候选（**不给全仓、不给 A1 推理链**）；
- 产出 ≤20 条假设（陈述 + ≥1 个账本锚点引用 + 推理链 + 位置提示）；
- **主代理把假设转写为 check_point_ledger hypothesis 行**（direction=hypothesis, mechanism=divergent_reasoning, added_after_freeze=true），与普通检查点同一流水线（终态四选一+证据）；无锚点假设非法（Gate gate[假设锚点强制]），超 20 条 FAIL（gate[假设上限]）。

### 9a. 确定性引擎（v0.5.0，必须先于一切分析执行）

- 阶段0 开始时，主代理执行：
  `python3 contracts/sdwr/session.py prepare --session {session_dir} --source {project_path}`
  （无脚本时按 `enumerate.py` + `derive_checkpoints.py` 手动等价执行）。
- 枚举+派生产出固定三清单 + 账本骨架——确定性，每次相同。**调度权威只有 `session.py drive` 打印的 `NEXT=`**。
- **禁止 LLM 自行枚举/派生**——枚举和派生是脚本职责（63 号原则一）。

### 9b1. 候选 ID 确定性派生（v0.5.2 铁律，已机械化——禁止再手算）

**`candidates.tsv` 由 `session.py drive` 每轮自动机械生成/合并（`sync_candidates_tsv`），candidate_id 由脚本按下述公式计算，主代理/子代理禁止手算 md5、禁止自己拼 ID、禁止在这份文件不存在时视而不见继续往下走。** 真实 dvpwa 冒烟跑暴露过这个问题：`candidates.tsv` 全程没生成，`verification-summary.md` 只能拿 `check_point_ledger` 的 `CP-000011` 这种检查点 ID 顶替，report-delivery 阶段拿不到规范 ID，自己发明了 `V01`/`V02` 这种序号当文件名——这套 ID 现在完全由脚本保证，不应该再发生。

- candidate_id 格式：`C-{sink_seq:05d}-{source_seq:05d}-{sig8}`
  - backward（sink 锚定）：sink_seq/sig8 来自 sink_inventory.tsv，source_seq 来自 worklist `source` 列指向的 source_inventory 条目
  - forward（source 锚定，无 sink 命中）：source_seq 来自 source_inventory.tsv，sink_seq 按 fallback 取该候选所在文件在 file_inventory.tsv 的排序序，sig8 省略 sink_type 维度
  - terminal（文件级终态，如 Dockerfile/docker-compose 这类配置误用发现）：sink_seq 同样取 file_inventory 排序序，source_seq 置 0，sig8 = md5(location)
- **禁止顺序号**（C-00001/C-00002 等）——gate[候选 ID 反查] 反查清单的 sort_order，顺序号无法反查=FAIL
- **禁止自造 ID**——见 `contracts/sdwr/session.py` 的 `_derive_candidate_id`/`sync_candidates_tsv`，唯一权威实现
- 验证与报告阶段引用候选，一律用 `candidates.tsv` 里的 `candidate_id` 列，禁止用 `check_point_id`（`CP-XXXXXX`）冒充 candidate_id——两者是不同层级的标识，`CP-XXXXXX` 是检查点身份，`candidate_id` 才是候选/finding 的持久身份

### 9a1. Anti-Pattern 表（v0.5.3：代理偷懒借口红牌）

以下想法出现时**立即停止**——它们是十一轮实证中的已知偷懒路径：

| 借口 | 红牌理由 | 正确做法 |
|---|---|---|
| "12000+ sinks 做不了全量 WU 分析" | run-7 用此借口选择性深扫→21,767 未检查 | 全量 WU 派发，跑不完标 blocked+resume |
| "只分析 key clusters" | run-6/7 用此抽样→覆盖缺口 | 全 sink 类必须覆盖，零命中类声明 |
| "其余实例详见 V1" | run-7/8 用此外包→空壳 findings | 每个实例独立证据链 |
| "批量贴标 disproved_safe" | run-2~5 用此→无证据闭合 | 每行带 file:line 证据 |
| "我自己跑 grep 枚举" | run-9/10 用此绕过确定性引擎→枚举漂移 | 必须用 enumerate.py |
| "gate 数字我手写" | run-1~5 伪造 gate | gate_record 只由脚本产出 |
| "WARNING: ... 抄工具输出" | run-8 用此→推理非语义 | reasoning 必须是 LLM 语义判断 |
| "候选 ID 用顺序号 C-00001" | run-11 用此→ID 不确定 | 从 sink_inventory 派生 C-{sort_order}-{sig8} |
| "sampled_safe_sink 批量采样" | run-13 用此→15万 sink 全 disproved 无分析 | 逐 sink 独立结论，禁批量贴标 |

### 9c. drive 循环标准动作（唯一流程）

调度权威只有 `session.py drive`。**续跑=未闭合卡**——drive 从工作集里取未闭合卡，已闭合跳过不重跑。风险带只改队列内顺序，低危带同样要翻完。禁止「按文件编 WU 后按批号取下一批」或「1 文件=1 WU 按目录序取下一批」作为权威调度。`batch_size` 是并发上限，不是切批依据。

唯一流程：

1. 跑 `session.py drive`，读打印的 `NEXT=`/`QUEUE=`
2. 派 Analyzer（照抄 wu-analyzer 模板，只拿 `NEXT=` 的卡），分片命名 `batches/B{NNN}/WU-NNNN.tsv`（drive 的 `ingest_shards` 按 `batches/**/WU-*.tsv` 模式收集，命名必须匹配）
3. 验行数=派发数、引用可解析
4. 高杠杆事实走 Confirmer
5. 再跑 drive（收 Analyzer 分片 → 收 Summarizer 分片 `summarizer_shards/*-facts.tsv`/`*-pruning.tsv` → 收 Confirmer 分片 `confirmer_shards/*-decisions.tsv`（Summarizer/Confirmer 都不再直接改共享 facts.tsv/pruning_ledger.tsv，避免并发覆盖丢数据/产生重复行，drive 统一归并）→ 收 follow-up 缺口卡 `followups.tsv` → 按 K1–K4 改写 → 唤醒 blocked → 打印新 NEXT=；`FOLLOWUP=` 行是 Verifier 补证据请求，派发时把 gap_description 转给对应 Analyzer 作为第一优先问题）
5b. **每次 drive 后立即** `python3 contracts/build_graph.py --session {session_dir}` 重投影（不是攒到「一批完成」才投影——drive 一次 = 图更新一次，见「图实体化」节）
6. candidate 进 live 索引（`live_findings_index.md`）；同一次 drive 也会机械同步 `candidates.tsv`（`CANDIDATES_TSV_SYNCED=N` 行，N=本轮新增候选数），candidate_id 由脚本推导，无需也禁止手算——见 9b1
6b. **本轮 live 索引里新增的 candidate，立即派阶段2 Verifier 验证——不等 `STATE=L1_CLOSED`，不攒到本项目所有卡分析完再统一验证。** 验证 confirmed 的立即派阶段3 产出该 finding 的 `findings/V{N}.md`——单份产出，不等其它候选也验证完。这是 doc-64 批式流水线的核心（第 1 批出候选就该有第 1 份完整报告，不是全项目跑完才第一次见到报告）；9d 的 L1_CLOSED 硬门管的是"阶段1 何时能声明完成/续跑"，不管"验证/出报告何时可以开始"——那件事从枚举完成后每一轮 drive 就该在做。
7. **先改写再派下一块。**

L2：L1 工作集空之后（`STATE=L1_CLOSED`），先把 candidate 的 flow 上游未查卡标 `source=neighborhood` 入工作集，再跑 ≤20 假设，同一 drive 循环处理。

**拒绝批量模板（宁多勿漏）**：SINK-XXE/SINK-SSTI/SINK-SQL-EXEC/SINK-FILE-TRAVERSAL/SINK-FILE-UPLOAD/SINK-FILE-WRITE/SINK-OPEN-REDIRECT/SINK-CMD-EXEC/SINK-CODE-EXEC/SINK-CRLF/SINK-NET-REQUEST/SINK-WEAK-HASH/SINK-WEAK-RNG/SINK-WEAK-CRYPTO-PARAM/SINK-MISSING-CHECK/SINK-HARDCODED-CRED/SINK-CRED-PLAINTEXT/SINK-NO-AUTH-VERIFY/SINK-MEM-BOUNDS 等——**必须逐 sink 独立五步**，禁止「同文件同类同判」式批量处置。

**续跑**：阶段 1 允许跨会话续跑——代理跑不完时标 `run_status=blocked`；下次会话恢复直接再跑 drive，未闭合卡自动出现在 `NEXT=`，不需要额外指针。gate 对 blocked 状态不判 FAIL——blocked 是合法的「诚实承认跑不完」状态。**禁止在工作集未空时标 completed**；**禁止用批量采样跳过未完成卡**。

**跨文件追踪**：Analyzer 从本卡的 sink 出发，用 grep/read 自主追踪污点跨文件路径；call_edges.tsv 提供调用图辅助导航，不限于本卡所在文件。**追不到 source → 标 blocked（截断≠安全），禁止 disproved。**

### 9c0. 剪枝执行时序（高危 sink 优先真实分析，绝不被类级剪枝阻塞或消卡）

类级剪枝和高危 sink 的逐实例分析是**两条并行的独立线，谁都不等谁、谁都不阻塞谁**——这是为了避免 Summarizer 一次粗粒度、非五步的类级判断，把反序列化/SQL注入/XXE 这类高危 sink 永久关掉（Analyzer 再也不会看），在真正开始挖漏洞之前就先把最有价值的候选污染掉，与本工具"优先产出高价值漏洞、不能跑很久却什么漏洞都没有"的核心目标保持一致。

**时序（高危优先、噪音兜底，两条线并行）**：
1. **枚举完成后立即按 band 拆成两条队列**：band 0/1（高危：反序列化/SQL注入/XXE/越权/命令执行/文件穿越/XSS/SSTI/SSRF 等）与 band 2（低危噪音：格式化字符串/弱加密参数/资源注入等）。`session.py drive` 的 `NEXT=` 本身已经按 band 排序优先吐出高危卡，直接照做即可，不需要额外脚本拆队列。
2. **高危队列**：跳过类级剪枝，**直接进入逐卡 Analyzer 五步分析**（`kills` 事实仍然可以级联消卡，因为它要求具体函数+穷尽验证的必经点，证据强度远高于粗粒度 intended/uncontrolled；`source_role=analyzer` 的 `intended`/`uncontrolled` 也可以级联消卡结构相同的兄弟卡——见 rewrite.py 的高危 sink 规则）。目标：会话早期就开始产出真实 candidate，写入 `live_findings_index.md`，不要等到类级剪枝跑完整个项目才开始见到第一个漏洞。
3. **低危队列**：class-level pruning（Summarizer 写 S1/S3/INTENDED，禁止 S2）适用，用于压低噪音类的体量——这条线可以和高危队列的 Analyzer 派发**同批次并行进行**，不必等它跑完再开始高危分析，也不能反过来阻塞高危分析。
4. S4 可达性剪枝由脚本在首次 build 前执行（孤立文件，与 sink 类型无关，两条队列都适用）。

### 9c1. 安全剪枝算子（v0.9.0，doc 89 图剪枝）

**剪枝 = 类级排除，不是实例跳过。安全剪枝的唯一判据 = 与上下文无关的固有属性（实例结论禁止传播）。**

| 算子 | 判据（固有属性）| 适用范围声明 | 谁判定 | 谁验证 |
|---|---|---|---|---|
| S1 source 类剪枝 | 此类 source 攻击者不可控（环境变量/部署配置/字面量，且有直接证据：赋值处无外部输入）| 全局（与 sink 无关）| WU subagent 分析+证据 | A2 复核判据 |
| INTENDED 产品用途 | 此类是产品预期能力（不是 not_dangerous）；注释/死代码写 dead 事实，不进本表 | 必须声明范围 | Summarizer 分析+证据 | A2 复核判据 |
| S3 净化器摘要 | 函数 f 阻断 sink 类 S 的污点（证据：f 内的校验代码行号）| **必须声明 S 的范围（哪些 sink 类）** | WU subagent 分析+证据 | A2 复核摘要适用范围 |
| S4 可达性剪枝 | 无路径 source→sink | 图级（call_edges BFS，grep 级保守——只剪无任何边连接的孤立文件）| 脚本 BFS | 无需验证（保守） |

**剪枝判据落盘**：每个类级剪枝必须写 `pruning_ledger.tsv` 一行（算子|判据|适用范围|证据行号）——gate「剪枝判据落盘」检查；未落盘的类级剪枝 = 非法批量闭合。

**剪枝错误 = 系统性漏报**：A2 必须全量复核每个剪枝判据（不是抽查）；闭卷锚点做剪枝回归（剪掉锚点类 = 立即暴露）。

### 9c2. 缺失检查类可执行模板（v0.7.7，对应 gate「缺失检查类强制」）

**缺失检查类（SINK-MISSING-CHECK）的两段识别式**：不是 grep 某个函数名，是识别「应有而未有的检查」：
1. **untrusted 输入源识别**：length/count/range 等数值来自网络输入（request/read/recv 返回值）；
2. **使用点检查**：该数值用于 loop-bound / array-index / alloc-size / cast——检查使用点前是否有边界校验（if (len > MAX) throw 等）；
3. **判定**：无校验 → candidate（缺失检查）；有校验 → disproved（附校验行号）。

**每个缺失检查类候选必须回答对抗问题**：「边界检查在哪？」——答不出（无行号）则 candidate 成立。

### 9d. 阶段1 完成硬门（非零未检查禁 completed + 跨会话续跑）

**本节的 `STATE=L1_CLOSED` 只管"阶段1 自身何时能声明完成/续跑"，绝不管"验证/出报告何时可以开始"——后者是 9c 步骤 6b 的事，从枚举完成后第一轮 drive 出现第一个 candidate 起就该逐轮增量做，不能因为本节存在就被误读成"要等 L1_CLOSED 才能开始验证/出报告"。** 真实运行中发生过这个混淆：代理把"阶段1完成"和"能开始出报告"当成同一个时间点，导致大项目要跑几个小时才见到第一份详细报告，与"批式流水线首批即出结果"的设计目标（doc-64）直接冲突。

- 声明**阶段1本身**（发现工作，不是验证/报告）run_status=completed 前必须自查 `session.py drive` 打印 `STATE=L1_CLOSED`；未到此状态则必须标 run_status=blocked（不是 completed）——**阶段2/阶段3-per-finding 早已跟着每一轮新 candidate 在并行进行（见 9c 步骤 6b），不受这个 blocked 状态影响，不因为阶段1 还没声明完成就停下**；
- blocked 是合法状态——gate 不因 blocked 而 FAIL；
- 下次会话恢复：**续跑=未闭合卡**——直接再跑 drive，未闭合卡自动出现在 `NEXT=`，不需要额外指针；
- L1_CLOSED 之后，**阶段2 对已发现的全部候选的验证工作**自然收尾（因为不会再有新候选出现）——但每个候选的验证结论/finding 详情文件本身，理应早在其对应的那一轮 drive 里就已经产出，L1_CLOSED 这一刻只是"最后一批也处理完了"，不是"阶段2 现在才开始"；
- 禁止未检查>0 时标 completed（gate[batch_progress 完成率]+gate[planned==terminal] 拦截）；禁止批量采样跳过（gate[禁批量采样闭合] 拦截）。
- 宿主可在阶段1 结束后随时执行 `gate-1.py --stage g1` 中途复核，FAIL 即返工。

### 9e. 静态工具事实（v0.4.4 Mode 1，47 号激活）

- 能力档案探测到静态工具（spotbugs/semgrep 等）时，其输出可作为**观察事实来源**：逐条落 audit_log（file:line + 工具名 + 原始告警），进清单走同一证据纪律（gate[schema 全等] 引用可解析）；
- **禁止把工具输出原文抄进候选推理**：discovery_reasoning_note 必须是 LLM 的语义判断（三要素/防护核查的结论），不得以 WARNING:/ERROR:/INFO: 开头（gate gate[run_status 一致性]）。

### 10. Gate 与闭合

- Gate-1 由**宿主**执行 contracts/gate-1.py（24 项对账，判定由脚本输出生成）；**LLM 禁止执行 gate、禁止写 gate_record、禁止自报 gate_result**；A1 自评一律无效。
- gate_result=pass 后由 A2 独立验证 agent（全新上下文，四门 V0-V3 + 内置对抗任务）复核，与脚本输出合成最终 gate_summary。

## 输出

- 候选清单（字段以 [`../../contracts/data-structures/candidate-finding.md`](../../contracts/data-structures/candidate-finding.md) 为准），携带 `stage_result` / `version` / `resume_context`；零候选时 `records=[]` 且 `zero_input_reason` 非空，不虚构候选。
- `check_point_ledger.tsv`：检查点账本，四终态闭合（planned == terminal）。
- `audit_log.tsv`：逐检查点证据账本（列：`check_point_id` | `basis_id` | `direction` | `result` | `evidence_type` | `evidence_ref` | `reviewed_at`），每个已执行检查点恰一行；Gate-1「audit 双向覆盖」对账依据。
- 分片文件 + `batch_progress.tsv`（batch/total/completed/findings）+ `live_findings_index.md` + `failed_wus.txt`（应为空或列入报告）。
- 跨 WU 路径经 [`../../shared/cross-boundary-analysis.md`](../../shared/cross-boundary-analysis.md) 汇聚后写 `cross_boundary_path_ref`，不原地改候选。
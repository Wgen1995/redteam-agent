# 分层质量 Gate（唯一权威）

> 依据：设计 28 号 §3.2、36 号、39 号（gate 全部方程对账（以 gate-1.py self.add 名单为权威，数量勿硬编码）+ 双轨对账块 + 黄金夹具自检 + 全终态理由封闭）。Gate-1 只做客观对账（宿主执行对账块，判定由命令输出生成，不是 LLM 自报）；Gate-2 只做轻量独立抽查，只列缺口、不代写候选。

Gate 判定结果取值（权威定义见 [枚举注册表 `gate_result`](../contracts/enum-registry.md#gate_result)）：`pass`、`rework`、`blocked`、`pass_with_gaps`。

## 总则

- Gate-1 与 Gate-2 职责不同：Gate-1 证明「集合闭合、无漏执行、产物可对账」，Gate-2 挑战「做对了」。不使用两个同职责 Agent 投票。
- **Gate-1 由宿主执行 contracts/gate-1.py**（全部方程对账，以 gate-1.py self.add 名单为权威，数量勿硬编码；判定由脚本输出生成）；**LLM 禁止执行 gate、禁止创建/编辑 gate_record.md、禁止自报 gate_result**——A1 的任何自评一律无效。执行前必须黄金夹具自检 SELFTEST: PASS；未通过 → 该环境 blocked。
- **分层 gate（v0.4.1，及时返工）**：同一批等式在输入冻结的最早时点分段执行——G0 阶段0 清单冻结后（schema/信号级/产物存在）、G1 阶段1 账本闭合后（闭环/理由/引用/时序/WU/缺失检查类）、G2 阶段2 候选定稿后（ID 反查/双向闭包/档位/A5 痕迹）、G3 收尾（四相等/failed/对抗表/run_status 一致性）；每段 FAIL 即局部 rework，不进入下一阶段。命令：`gate-1.py --stage g0|g1|g2|g3`。
- **终态全量 gate 铁律（v0.11.0 B01-U1）**：--stage/--subtask 只是中途早发现手段；**终态（3.2 完成硬门）必须跑无 --stage 全量 gate——全部方程一个不漏**，任一 FAIL 不得 completed。
- **gate_record.md 强制落盘**：全部方程逐条记录输出与判定（以 gate-1.py self.add 名单为权威，数量勿硬编码；成立/FAIL）；gate_result 只能引用该文件；缺任何一行 = Gate 未完成。
- **gate_record 生命周期**：任一 FAIL → rework → 补完缺口 → 宿主重跑覆盖更新；残留 FAIL 或缺行时禁止 completed；完成后 gate_summary 写回 run-state（null 即违反本门）。
- **中途宿主 gate（v0.4.4 铁律）**：阶段1 结束后宿主必须执行 `gate-1.py --stage g1`；任一 FAIL 即返工，**未跑中途 gate 的 run 验收判无效**（八轮实证：代理不会自查，唯一有效闸门在宿主手里）。
- **硬门失败不得掩盖**：gate[planned==terminal]/[账本零残留] 失败只能 rework/blocked；gate 全部方程任一 FAIL 时 gate_result 只能 rework/blocked——等式级不存在 pass_with_gaps。
- **A2 独立验证 agent（语义门）**：gate_result=pass 后由 A2（全新上下文，只收「检查问题+产物+源码路径」，不收 A1 推理链）执行四门 V0-V3（枚举复核/闭环与真分析抽查/候选独立重验/报告投影），内置对抗任务（找占位引用/批量贴标/套版置信度/假路径/档位虚标）；通过后由「脚本输出 + A2 复核」合成最终 gate_summary。A2 写 gate2_notes.md 文件（含抽样率与发现），run-state 引用该文件。**时序残余风险（v0.11.0 已封堵）**：「audit_log 追加单调性」方程（补写过去时间戳必破坏）+「时序检查」缺时间戳必 FAIL；残余缓解 = A2 V1 门抽查 + 宿主终审重放 gate_record。
- Gate 读取 run-state.md 前，single_document_guard 由宿主行级机械校验（host-reconciliation-commands.md 第8节）。
- **unverified_accounting 降级路径自 v0.3.9 起关闭**：无对账执行环境 = 阶段0 blocked（见 deployment-environment.md）。

## 五层闭合（设计 34 号 §5 + 48 号，端到端对账链）

| 层 | 等式 | 失败后果 |
|---|---|---|
| L0 清单冻结 | find 行数 == file_inventory 行数；sink/source 清单行数 == 冻结值；信号级 7 类禁入 sink_inventory（gate[信号级禁入]） | blocked |
| L1 检查点派生 | 每 sink ≥1 backward、每 source ≥1 forward、每文件 ≥1 terminal；planned == terminal（gate[planned==terminal]/gate[sink 回溯覆盖]/gate[source 前向覆盖]） | rework/blocked（禁止 pass_with_gaps） |
| L2 簇覆盖 | clusters/ 目录存在且每簇含攻击模式对抗表（gate[簇产物存在]/gate[对抗表存在]）；未聚簇的 sink/source 检查点不得落终态；全终态理由封闭（gate[反伪闭合(全方向)]/gate[全终态理由封闭]）；引用可解析+证据唯一性（gate[引用可解析]/gate[证据唯一性]） | rework/blocked |
| L3 验证覆盖 | audit 双向覆盖（gate[audit 双向覆盖]）+ 候选双向闭包（gate[三事实源一致性]）+ ID 反查（gate[候选 ID 反查]）+ 推导链强制（gate[推导链强制]）+ 时序（gate[时序检查]） | rework |
| L4 报告投影 | 四相等+阈值（gate[四相等+阈值]）+ failed 去真空（gate[failed 清单去真空]）+ schema 全等（gate[schema 全等]）+ 档位诚实（gate[档位诚实]）+ WU 闭合（gate[WU 闭合]） | rework |

## Gate-1：全部方程对账（宿主 gate-1.py 执行，全部硬门；以 gate-1.py self.add 名单为权威，数量勿硬编码）

命令：contracts/gate-1.py（--session + --source）；自检用 --expect 黄金夹具。对账常数动态推导，禁止硬编码。全部方程（以 gate-1.py self.add 名单为权威，数量勿硬编码）皆成立才 gate_result=pass（下表为历史最小集参考，权威全方程名单以 gate-1.py self.add 为准）：

| # | 等式 | 语义 |
|---|---|---|
| 1 | planned==terminal | 检查点无未检查 |
| 2 | sink 回溯覆盖 | 每个 sink 至少一个 backward 检查点 |
| 3 | source 前向覆盖 | 每个 source 至少一个 forward 检查点 |
| 4 | audit 双向覆盖 | audit_log backward 行与 sink_inventory 双向差集为空 |
| 5 | 四相等 + 阈值 | V*.md 数 == machine-fields 条数 == confirmed 数 == 分区表链接数，且置信度过 tier 阈值 |
| 6 | failed 清单去真空 | failed_wus.txt 存在、行数 == blocked 数、blocked basis 全登记 |
| 7 | 账本零残留 | 无「未检查」 |
| 8 | 反伪闭合(全方向) | not_applicable 理由前缀合法（backward/forward/terminal 分别封闭） |
| 9 | 簇产物存在 | clusters/*.md > 0 |
| 10 | 全终态理由封闭 | disproved/blocked 前缀封闭；disproved_safe 必须带证据引用 |
| 11 | 候选 ID 反查 | sink_seq/source_seq 反查冻结清单位置一致 + sig8 复核 |
| 12 | 产物存在性 | 7 个必需产物 + clusters 非空 |
| 13 | 信号级禁入 | sink_inventory 不含信号级 7 类 |
| 14 | 候选双向闭包 | confirmed ⊆ machine-fields 集合 且 ⊆ 账本 candidate_ids（「三事实源一致性」读 candidates.tsv+machine-fields+report.md，不读 verification-summary） |
| 15 | 对抗表存在 | 每个 clusters/*.md 含「## 攻击模式对抗表」 |
| 16 | schema 全等 | candidates 16 列（== CAND_COLS）/ machine-fields 9 字段（== MF_KEYS）/ 清单列名 ASCII |
| 17 | 引用可解析 | 每条证据引用 file:line 存在于源码、簇文件存在 |
| 18 | 证据唯一性 | 单引用覆盖 ≤50 检查点（>500 FAIL） |
| 19 | 档位诚实 | runtime_tier ≤ 声明上限（denied → 6） |
| 20 | 推导链强制 | 每个终态行的 check_point_id 存在于 audit_log |
| 21 | 时序检查 | 观察时间戳 ≤ 结论时间戳 |
| 22 | WU 闭合 | 各 WU 检查点并集 == 总账本（无 WU 分片时 N/A） |
| 23 | 假设锚点强制 | hypothesis 检查点必须携带可解析锚点 |
| 24 | 假设上限 | hypothesis 检查点 ≤ 20/轮 |

**判定栏由脚本输出生成，禁止手写**；FAIL 强制 rework 循环（rework_rounds+1 → 补缺口 → 重跑覆盖更新）；只补缺失、不重做已完成；没有规模豁免。上限内未收敛 → blocked + 部分报告。**缺口精确清单**（FAIL 项的前 100 条 + 总数）由宿主按 E 项导出，写入 gate_record 的 rework 段。**PlateauDetector**：连续两轮缺口集合无变化 → 停滞 → partial/blocked 停。

检查点派生规则与全终态理由封闭枚举见 check-unit-ledger-template.md。candidate 数量不参与闭合等式。Gate-1 只生成计划内可审计的闭合证据，计划外攻击面的覆盖属于 Gate-2 与范围界定。

### A2 派发模板（v0.7.2，必须派发，禁止环境借口）

**铁律**：宿主有 Task/subagent 工具时必须派发 A2——「environment limitation: no separate subagent」等借口一律无效（openCode 有 subagent 能力，run-8/12 已实证）。gate2_notes.md 含 "not executed" 字样即 gate[A2 独立验证硬门] FAIL。

**时点**：gate_result=pass 后（agent 自跑 g3 通过后）
**派发**：1 个独立 subagent（全新上下文，只收 session 目录 + 源码路径 + 本清单；禁止传入主代理推理链）
**四门**：
  V0 枚举复核：独立重扫抽样 5 sink 类 + 3 通道对拍清单
  V1 闭环与真分析：每簇抽 3-5 条证据回源码（存在/行号真/内容相符）+ 批量贴标定性
  V2 候选重验：每 confirmed 独立重验三要素/配置关卡/档位，分歧取保守
  V3 报告投影：8 节齐全 + ID 全链路一致 + 四相等
**内置对抗任务**：找占位引用/批量贴标/套版置信度/假路径/档位虚标/工具原文充数
**产出**：A2 写 gate2_notes.md 文件，run-state 引用该文件；不改 gate_record 数字、不改产物

### A2 派发模板-orig（v0.4.2，必须派发独立 subagent，全新上下文）

派发输入只含：session 目录路径 + 源码路径 + 本清单；**禁止传入主代理的推理链**。A2 执行：①运行 contracts/gate-1.py（对应 --stage 或全量）→ 读取 gate_record；②四门复核：V0 枚举复核（独立重扫抽样 5 sink 类 + 3 通道对拍清单）、V1 闭环与真分析（每簇抽 3-5 条证据回源码验「存在/行号真/内容相符」+ 批量贴标定性）、V2 候选重验（每 confirmed 独立重验三要素/配置关卡/档位，分歧取保守）、V3 报告投影（8 节齐全/ID 全链路/四相等）；③内置对抗任务：找占位引用/批量贴标/套版置信度/假路径/档位虚标；④A2 写 gate2_notes.md 文件（含抽样率与发现清单），run-state 引用该文件。**A2 不修改 gate_record 数字、不改产物**；完成硬门要求 gate2_notes.md 非空。

## Gate-2：轻量独立抽查（只列缺口，不代写）

执行方优先为独立 subagent（不可用时降级为同会话复核并标注 `independence_degraded`）。输入只含：待检查主张、原始源码/证据、当前节点最终产物、狭窄检查问题；禁止提供原分析推理过程或"应通过"暗示。Gate-2 **只输出缺口清单，不代写候选/主产物**。

抽查四项：

1. **矩阵漏点**：高风险入口是否有漏候选；`disproved`/`not_applicable` 检查点的证据是否可信；兄弟实例（同 source/同控制点/同 sink 结构）是否遗漏。
2. **FALSE-rules 误杀**：候选是否被 FALSE-rules 误判忽略；证据分级是否超过最弱一环。
3. **对抗表真实性（v0.3.9）**：抽样簇文件的攻击模式对抗表，回源码验证「挡住」行的证据行是否真实存在、是否存在未列出的已知攻击模式（尤其知识库 CVE 模式）。
4. **跨 WU 路径抽查**（启用 WU 时）：候选的 `cross_boundary_path` 是否完整，汇聚后的 `unresolved_connections` 是否影响关键路径。

抽查缺口必须定位到具体文件/检查点/WU/candidate，供返工；Gate-2 不改写任何终态，不产出候选。

## pass_with_gaps（简化）

`pass_with_gaps` 是带已披露缺口通过，不是"差不多就算了"。前提：缺口**必须定位**（到文件/检查点/WU/candidate 级）且**已披露**（写入报告缺口披露章节），且不使已有 finding 证据失真。**等式级不存在 pass_with_gaps（gate 全部方程任一 FAIL 只能 rework/blocked）**；gate 级 pass_with_gaps 仅适用于等式之外的已披露缺口，且关键范围（要害资产相关、High/Critical 候选）存在缺口时不能 pass_with_gaps，只能 `rework` 或 `blocked`。写 `run_status=completed` 的充要条件以 report-delivery/SKILL.md 完成硬门为准（要求 gate_result=pass）。

## 返工上限

- 每节点最多执行 3 次（初次 + 最多 2 次 Gate 返工）。
- 超限后：满足 `pass_with_gaps` 前提则如实带缺口通过；否则 `blocked`。**超限必须如实披露**（返工轮次 + 未收敛缺口清单），不得伪装通过。
- Gate 返工缺口写入运行产物或 WU 分片，不能只留在会话文本里。
# 状态模型（横切行为约束）

> 依据：设计 28 号 §7.2（状态机简化与压缩恢复）。本文件定义运行状态、阶段产物、进度状态机与恢复纪律；状态由宿主按 Markdown 协议执行，不引入软件状态机或 validator。

## 原子写纪律（v0.3.7，设计 36 号 §2.3）

所有 TSV/YAML/JSON 状态与账本文件的更新一律**原子替换**：写临时文件（同目录 temp 名）→ 完成后 `mv` 覆盖目标文件；禁止对账本文件原地追加改写（追加仅允许 audit_log 类 append-only 流）。progress.json、run-state、check_point_ledger.tsv、candidates.tsv 全部遵守。

### 追加写白名单（v0.11.0 修正，D7）

**追加写允许**的产物（仅以下 6 类，其余产物一律整文件重写）：

- `audit_log.tsv`——逐观察 append-only（执行时实时追加，一行一观察）；
- `flow_edges.tsv`——逐 sink 回溯/前向时追加可达边；
- `pruning_ledger.tsv`——类级剪枝判定逐条追加（`a2_verified` 列由 A2 复核后回填，不改写既有行）；
- `graph_snapshot.tsv`——图实体化快照逐批追加节点/边计数；
- `progress_board.md`——批进度看板逐批追加行；
- `live_findings_index.md`——实时发现索引逐候选追加。

**其余产物整文件重写**（原子替换）：`progress.json`、`run-state.md`、`check_point_ledger.tsv`、`candidates.tsv`、`verification-summary.md`、`report.md` 等不在上述白名单内的产物，更新时一律整文件覆盖，不得原地追加。

## 输出即最终态

每个 stage 的产出是覆盖式最终结果，不是追加式日志。stage 重新执行（断点续跑/增量重跑）后直接覆盖为反映当前最新状态的完整结果，不追加历史条目让下游自行拼接。

## single_document_guard（由宿主 shell 校验）

`run-state.md` 是单一 YAML document：根必须是 mapping，禁止重复键、多文档/追加片段。更新必须整文件替换并严格解析、核对必填字段与跨结构一致性；任一步失败保留旧可信版本。**该核对由宿主 shell（YAML 解析命令）执行，不再依赖 LLM 自报**（命令见 [`../contracts/host-reconciliation-commands.md`](../contracts/host-reconciliation-commands.md) 第8节）。

## 运行状态 run_status（四值）

整次运行的顶层状态，记录在 `run-state.md`，取值四值：`running` / `completed` / `blocked` / `interrupted`（**去除 `initialized` 细分**；run 创建即 `running`）。

- `running`：运行正在进行，尚未到达任何终态。
- `completed`：整次运行已完成并产出报告。
- `blocked`：缺少用户决定、权限或关键输入，条件满足后可继续。
- `interrupted`：运行非正常中断，按恢复纪律续跑。

`run_status` 不得写入 `stage_result` / `gate_result` 的取值；WU 状态由分片文件存在性判定承载（WU 五态，`work_unit_status` 已废弃）。

## 阶段产物三共享字段（保留）

每个 stage 产物必须携带：`stage_result`（`completed` / `partial` / `not_applicable`）+ `version` + `resume_context`。`stage_result=partial` 时 `resume_context` 必须非空。整次运行被记 `run_status=interrupted` 时，当前阶段把产出记 `stage_result=partial` 并携带 `resume_context`，不把运行级状态写进阶段级字段。

## progress.json（五态进度状态机）

`progress.json` 记录本次运行的进度，仅 5 种状态：`pending` / `in_progress` / `complete` / `skipped` / `blocked`，**禁止发明 `partial` / `mostly done` 等额外状态**。

- 以通道/清单/批次为单位记录状态；`skipped` 仅在"合法不适用或已由其他路径覆盖"时使用并写明理由，`blocked` 写阻塞原因。
- `step_progress` 每完成一个通道 / 清单 / batch **立即更新**（覆盖式，不是结束才补记）。
- `progress.json` 结构与字段以 [`../contracts/run-state-template.md`](../contracts/run-state-template.md) 的 progress 摘要为准。

## 检查点时机

宿主在以下时点覆盖更新 `run-state.md` 与 `progress.json`：初始化完成、一个能力开始前、一个实质子步骤完成后、派发子代理或长命令前、一个能力完成后、发现阻塞/中断迹象时、报告完成后。更新的是当前完整状态，不是追加运行日志。

## 恢复纪律（压缩恢复）

1. 新会话只依据 `progress.json` + `run-state.md` + 冻结清单 + 已完成产物恢复，不把模型会话记忆当持久化证据。
2. **压缩恢复 = 读 progress + run-state + 清单 + 未完成分片，从 `remaining[0]` 续跑，禁止从头重跑**；不重跑已完成分片，不重编号已有 candidate。
3. 恢复前核实 `source_path` / `source_revision` / 已完成产物存在性与非空性；源码 revision 变化时按增量规则重新核查受影响范围。
4. **恢复即"完整锚定"**：恢复后的首次持久化动作必须重读 progress / run-state / 三份清单 / 未完成 batch 分片，锚定后从 `remaining[0]` 续跑（删除三级锚定分类，不再区分 full / work_unit / lightweight）。
5. 缺少关键恢复字段或产物损坏时，创建新 run 并从最近可信能力重跑，不伪装精确续跑。
6. 中断或阻塞不妨碍生成部分报告，但报告必须披露未完成能力、剩余范围和恢复入口。

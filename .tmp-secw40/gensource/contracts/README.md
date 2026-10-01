# GenSource 产出契约

本目录是 GenSource 各阶段产出的轻量自然语言参考层。日常执行由宿主 Agent 读取 Markdown字段表、枚举和写权限约定；本目录不提供也不计划提供 JSON Schema、validator、调度器或任何自研程序。当前参考入口是本 README、[枚举注册表](enum-registry.md)、[字段写权限表](field-ownership-table.md)、[数据结构契约](#数据结构契约)、[运行状态模板](run-state-template.md)、[Work Unit模板](work-unit-manifest-template.md)、[检查单元账本模板](check-unit-ledger-template.md)和 [CHANGELOG](CHANGELOG.md)。

## 历史编号映射（旧决策编号 → v0.3.0 阶段/伴生）

> 本套件部分历史文件（data-structures 与 field-ownership-table 的段落、伴生能力正文）仍使用 docs/research/decision 的旧决策编号。以下映射是唯一权威解释，避免旧编号与阶段0-3 主序列混淆：

| 旧编号 | v0.3.0 归属 |
|---|---|
| #1+#2（威胁语境+攻击面范围） | 阶段0 scope-and-context |
| #3（候选发现） | 阶段1 candidate-discovery |
| #4+#5（验证确认+严重度评估） | 阶段2 verification-and-rating |
| #8（报告呈现） | 阶段3 report-delivery |
| #6（PoC）、#7（修复指导） | 伴生能力，默认并入 finding 内小节 |
| #9+#19（生命周期+增量） | 伴生 lifecycle-governance（增量模式激活） |
| #16（知识演进）、#18（外部工具） | 伴生 knowledge-evolution / external-tool-integration |
| #10-#15、#17、#20 等其余编号 | 横切设计类别（对应 shared/ 与 knowledge/ 文件），非阶段 |

## 核心规则

1. 新增字段必须先登记契约：对应实施任务完成后，在 `data-structures/*.md` 登记字段定义；当前及后续均须同步核对 [字段写权限表](field-ownership-table.md)，新增或变更枚举值还必须先登记到 [枚举注册表](enum-registry.md)。各阶段不得先在自己的 `SKILL.md` 或产出里私自发明字段。
2. 消费方必须忽略不认识的字段，以支持新增字段的向前兼容；不得因出现未知字段拒绝整个产物。
3. 废弃字段或枚举值标记为 `[deprecated since vX]` 后继续物理保留，不删除；变更原因和日期追加记录到 [CHANGELOG](CHANGELOG.md)。
4. 每个阶段产出都携带共享状态字段 `stage_result`、`version`、`resume_context`。其语义遵循 [`shared/state-model.md`](../shared/state-model.md)，写权限遵循本目录的 [字段写权限表](field-ownership-table.md)；`stage_result` 与描述整次运行生命周期的 `run_status`、Gate判定的 `gate_result`、Work Unit 五态（分片文件存在性判定，`work_unit_status` 已废弃）是互不重叠的维度，定义均见 [枚举注册表](enum-registry.md)。
5. contracts 当前版本为 `v0.3.7` 轻量参考。除阻断运行、造成漏报/误报或破坏证据真实性的问题外，字段命名、枚举风格和排版问题只记录到运行缺陷清单，不中断真实审计。
6. 历史已生成的产物文件保留其原始版本号字段，不会因契约版本升级被静默重写或强制迁移；`version` 字段只在该产物自身被相应阶段重新生成时才更新为当前契约版本。

## 当前已落地权威入口

- [`README.md`](README.md)：契约层定位、规则、实施结构与消费流程。
- [`field-ownership-table.md`](field-ownership-table.md)：将 [`shared/field-ownership.md`](../shared/field-ownership.md) 的横切纪律实例化为各阶段真实字段族。
- [`enum-registry.md`](enum-registry.md)：本文件登记的跨阶段及流程控制机器枚举的单一权威源。
- [`CHANGELOG.md`](CHANGELOG.md)：追加式记录契约版本演进。
- [`run-state-template.md`](run-state-template.md)：顶层 Agent 用于检查点和断点恢复的人读状态模板。
- [`work-unit-manifest-template.md`](work-unit-manifest-template.md)：大任务/并行/跨会话时条件启用的分片状态模板。
- [`check-unit-ledger-template.md`](check-unit-ledger-template.md)：候选发现阶段检查点（check point）规划与终态对账模板，Gate-1 候选发现闭合以此为准。
- 跨 WU 边界汇聚规则见 [`../shared/cross-boundary-analysis.md`](../shared/cross-boundary-analysis.md)，边界事实结构见 [`data-structures/work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md)。

## 数据结构契约

- [`threat-context.md`](data-structures/threat-context.md)：#1 威胁语境与用户确认结构。
- [`attack-surface-map.md`](data-structures/attack-surface-map.md)：#2 文件、类别和开放语义攻击面地图。
- [`candidate-finding.md`](data-structures/candidate-finding.md)：#3-#8 candidate 累积结构及 finding 语义边界。
- [`lifecycle-ledger.md`](data-structures/lifecycle-ledger.md)：#9/#19 生命周期、跨扫描身份与覆盖差异台账。
- [`work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md)：Work Unit 分片的边界事实——inputs/outputs、符号引用、调用边、字段映射、存储边、传输边及未解析连接。
- [`knowledge-base-entry.md`](data-structures/knowledge-base-entry.md)：#16 知识晋升、弃用、人工决策与证据历史结构。
- [`external-tool-signals.md`](data-structures/external-tool-signals.md)：#18 外部信号、主张复核、导出和工单写入结构。
- [`knowledge-graph.md`](data-structures/knowledge-graph.md)：v0.10.1 图实体化契约——knowledge_graph/{nodes,edges}.json 的节点/边 schema、status 机械推导、图投影四方程校验（图=账本投影，LLM 禁止写图）。

## 本层完整结构

```text
gensource/contracts/
  README.md
  field-ownership-table.md
  enum-registry.md
  data-structures/
    candidate-finding.md
    threat-context.md
    attack-surface-map.md
    lifecycle-ledger.md
    work-unit-boundary-facts.md
    knowledge-base-entry.md
    external-tool-signals.md
    knowledge-graph.md
  run-state-template.md
  work-unit-manifest-template.md
  check-unit-ledger-template.md
  CHANGELOG.md
```

- [`data-structures/*.md`](data-structures/)：当前已落地并启用，作为日常 LLM 读写的主权威源，定义字段名、类型、条件必填、允许值、写权限方和只读方。
- [`run-state-template.md`](run-state-template.md)：由宿主 Agent 直接读写，不依赖代码状态机。

## 消费流程

1. 当前执行阶段先读取 [字段写权限表](field-ownership-table.md)、[枚举注册表](enum-registry.md)和自身对应的[数据结构契约](#数据结构契约)，并以数据结构契约作为首要字段参考。
2. 只写本阶段拥有的字段段；上游字段只读，证据条目只追加，未知字段原样保留。
3. 将 `stage_result`、`version`、`resume_context` 写入本阶段完整产出；重跑时按状态模型覆盖为当前最终态，而不是拼接运行日志。
4. 报告阶段仅把上游结构化字段确定性投影到自己的报告段落，不修正或覆写上游字段；发现上游错误时返回对应阶段修正并重新投影。
5. 最终封存和外部导出继续由 `external-tool-integration` 按目标格式做确定性投影；GenSource 不自建通用 Schema 校验程序。

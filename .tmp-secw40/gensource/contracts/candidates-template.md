# candidates.tsv 模板（v0.11.0，16 列 schema 与 gate「schema 全等」一致）

```
candidate_id	location	sink_type	severity_hypothesis_initial	root_cause_group_id	lifecycle_state	verdict	cluster_ref	verification_record_ref	report_record_ref	created_at	discovery_source	path	start_line	end_line	discovery_reasoning_note
```

| 列 | 说明 |
|---|---|
| candidate_id | C-{sink_sort_order:05d}-{source_sort_order:05d}-{sig8}（从 sink_inventory 派生，禁占位）|
| location | file:line（必须存在于 sink_inventory）|
| root_cause_group_id | 同根因合并：同 RCG 不同 location 合法（多实例），同 RCG 同 location 重复非法（gate「候选同根因合并」）|
| discovery_reasoning_note | 候选推理说明，不得以 `WARNING:`/`ERROR:`/`INFO:` 开头（Gate-1 方程「候选推理非工具原文」机械校验：空值或工具原文前缀均 FAIL；必须为 LLM 语义判断）|

# pruning_ledger.tsv 模板（v0.11.1 D⑦）

类级剪枝判据账本（S1/S3/INTENDED）。写方：类级剪枝 subagent（追加行）+ A2 复核 subagent（a2_verified 列回填 true/false）。S2 行若仍出现，改写器与 Analyzer 协议均忽略。

```
operator	criterion	scope	evidence	judged_by	timestamp	a2_verified
```

| 列 | 值 | 语义 |
|---|---|---|
| operator | S1 / S3 / INTENDED | S1=入口类不可控 / S3=kills 摘要 / INTENDED=产品用途。禁止 S2 整类 not_dangerous。注释/死代码用 dead 事实，不进本表。 |
| criterion | 一句话判据 | 固有属性判据描述 |
| scope | SOURCE-{entry_type} / {sink_type} / {sink_type}-via-{函数名} | 适用范围（自然拼接：sink_type 原值自带 SINK- 前缀） |
| evidence | file:line | 判据证据（Read 代表样本的直接证据） |
| judged_by | PRUNE-A2 等 | 判定方 |
| timestamp | UTC ISO 8601 | 落盘时刻 |
| a2_verified | true / false（初始留空） | A2 复核结论——**空值/非法值 gate「剪枝 A2 复核」判 FAIL**；false 的判据不生效（投影与剪枝边一致性只认 true） |

**铁律**：无证据不判（不确定留给 WU 逐实例分析）；a2_verified=false 的判据行物理保留但不参与剪枝语义（build_graph 投影与 gate「剪枝边一致性」均只认 true）。

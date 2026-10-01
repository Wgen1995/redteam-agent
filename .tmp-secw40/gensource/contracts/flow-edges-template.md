# flow_edges.tsv 模板（v0.10.0 图剪枝——污点流边）

每行一条污点流判定（LLM 追链的「画线」产物）。gate「候选边支撑」「flow 边节点存在」检查候选的边支撑。

```
source_id\tsink_id\tdirection\thops\tevidence_refs\tjudged_by\ttimestamp
```

| 列 | 值 | 语义 |
|---|---|---|
| direction | reachable / blocked_at / no_path | 可达（漏洞核心边）/ 路径有防护 / 追不到 source |
| hops | 整数 | 追链跳数（no_path 为 -）|
| evidence_refs | file:line 逗号分隔 | 每跳证据（最小可用片段纪律）|
| judged_by | WU-XXXX | 哪个 WU 画的 |

**铁律**：candidate 必须至少有一条 reachable 边（「候选边支撑」）；边的两端节点必须在清单中（「flow 边节点存在」）。

## 图投影（v0.10.1 doc 99）

flow_edges.tsv 每行投影为 `knowledge_graph/edges.json` 一条 `flow` 边（from=source:{source_id}，to=sink:{sink_id}，attrs=本行各列）。写完本文件后跑 `build_graph.py --session {session_dir}` 重投影——扫雷翻转（direction 更新）在图边 attrs 上即时可见。图由脚本投影维护，LLM 禁止手改（gate 图投影四方程（「图节点投影完整性」「图边投影完整性」「图投影确定性」「图边端点存在」）校验，schema 权威 `data-structures/knowledge-graph.md`）。

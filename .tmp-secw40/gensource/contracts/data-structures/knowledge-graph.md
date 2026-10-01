# knowledge_graph 结构契约（v0.10.1 doc 99）

**职责**：图实体化产物——`nodes.json` + `edges.json` 是账本的确定性投影（图 = f(账本)）。设计权威 docs/research/99-explicit-graph-materialization.md。
**生产者**：唯一生产方 `contracts/build_graph.py`（确定性脚本，零语义判断）。gate-1.py 校验图与投影一致（「图节点投影完整性」「图边投影完整性」「图投影确定性」「图边端点存在」）。
**写入方**：仅 build_graph.py / gate-1.py。**LLM 禁止写图**（手改被「图投影确定性」抓）。
**消费者**：剪枝进度可视化（消消乐/扫雷）、进度看板、最终漏洞路径图、宿主人工审查。

## nodes.json（JSON array，元素按 id 排序）

| 字段 | 说明 |
|---|---|
| id | `{type}:{账本id}` 前缀式全局唯一（sink:/source:/file:/checkpoint:/candidate:/finding:） |
| type | sink / source / file / checkpoint / candidate / finding（6 类） |
| attrs | 投影自账本行的机械字段（file_line/sink_type/symbol/direction/…，见 doc 99 §2.1） |
| status | sink/source：unchecked/candidate/pruned（类级剪枝→pruned_by+pruned_reason；全 disproved→pruned；含 candidate→candidate）；checkpoint：terminal_state；candidate：verdict；file/finding：active |
| pruned_by | 类级剪枝 operator（S1/S2/S3），仅 status=pruned 且类级剪枝时存在 |
| pruned_reason | 类级剪枝 criterion 或逐实例 reason 拼接（≤200 字符） |

status 机械推导规则（零语义）：pruning_ledger scope 匹配（S2 scope=sink_type、S3 scope=sink_type-via-fn、S1 scope=SOURCE-{entry_type}）→ pruned；否则 ledger 全 terminal∈{disproved,not_applicable} → pruned；否则含 candidate/confirmed → candidate；否则 unchecked。

## edges.json（JSON array，元素按 id 排序）

| edge_type | from → to | 来源账本 | attrs |
|---|---|---|---|
| flow | source:{id} → sink:{id} | flow_edges.tsv 逐行 | direction/hops/evidence_refs/judged_by/timestamp |
| basis | {sink|source|file}:{basis_id} → checkpoint:{cp_id} | check_point_ledger 行（仅 direction∈{backward,forward,terminal}；fix_presence 行不进图——basis 是 CVE 知识锚点） | direction/mechanism |
| derived | 三类机械 join：①checkpoint→candidate（ledger candidate_ids）；②sink→candidate（location==file:line 精确匹配，同位置多 sink 全建边）；③candidate→finding（report_record_ref） | candidates.tsv + ledger + machine-fields.json | via: ledger_candidate_ids / location_match / report_record_ref |

边 id = md5(edge_type|from|to|canon(attrs))[:16]（确定性，重投影不变）。

**call_edges.tsv 不入图**：端点（import 包名/方法名）不在节点 ID 空间，保持导航辅助表地位（诚实投影原则）。

## 校验（gate-1.py）

- 「图节点投影完整性」：gate 独立重算节点集 == 投影（防 build bug，两份实现互补）
- 「图边投影完整性」：gate 独立重算边集 == 投影
- 「图投影确定性」：图文件 == 账本投影，且 build 两次一致（防手改/陈旧/非确定）
- 「图边端点存在」：每条边 from/to ∈ 节点集（GenCPT host-missing 悬空边教训）

## 演进

- 每批 WU 完成后跑 gate（含重投影）：新 flow 边、新候选节点入图；disproved 节点翻 pruned；
- `graph_snapshot.tsv` 每批追加 graph_nodes/graph_edges 计数：剪枝推进 = 计数递减（消消乐进度可见）；
- 最终图 = active 节点 + 边集 = 完整漏洞溯源路径图（source→flow→sink→derived→candidate→finding）。

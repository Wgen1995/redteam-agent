# ARTEX 深读 · 视角2 数据层与图法（子代理 ac386195，2026-10-11）

> 只读实勘：db/schema.sql + db/ 核心 16 文件。舰队共 5 路，此为第 2 路。

## ① 机制详解

**表清单与关系**（db/schema.sql，12 区约 45 张表）：A 资产层 companies/assets/company_scope；B 推理层 explorations→exploration_nodes/edges/anchors/task_constraints/activity/main_sessions；C LLM settings/llm_profiles/llm_profile_health；D 任务 tasks/task_scope/task_relations/task_asset_links/task_llm_profiles/task_archives/task_templates；E agents/agent_prompts；F-G MCP 与可见性、skill_usage/tool_usage 账本；I 会话 conversations/conversation_activities；K 拦截 intercept_rules/intercept_pending/asset_intercept_rules/task_intercept_rules；L findings/finding_retests/traffic_evidence_snapshots/finding_traffic_bindings；M 推送三表。主链：tasks.exploration_id UNIQUE+RESTRICT→explorations→nodes/edges/anchors 全 CASCADE。

**双图表**：exploration_nodes 七种 kind（begin/goal/intent/finding/fact/hint/digest），每种 kind 限定自己的 state 集合，用单条矩阵式 CHECK ck_node_state 写死（schema.sql:184-193）。exploration_edges 五种 rel（spawns/derived_from/yields/proves/covers），PK=(exploration_id,src_id,rel,dst_id)，CHECK 禁自环（schema.sql:248-257）。方向约定在 agent/coldgraph.go:11-14 注释：From=parent/upstream，To=child/downstream——**方向只是代码约定，DB 不校验 src/dst 的 kind 组合**。写入全部幂等：Link() 用 ON CONFLICT DO NOTHING（db/exploration.go:259-264）。

**anchor 桥表**：exploration_anchors(node_id,asset_id) 双 FK CASCADE 纯两列（schema.sql:276-281）。AddNode 同一事务建节点+批量插 anchor（exploration.go:197-217）；Anchor() 单独补点也幂等。语义注释明确：anchor 只留推理轨迹（lineage），不控可见性——资产图全局共享任务间互查（:245-249）。覆盖度、冷压缩分组、FindingLineage 全靠它反查。

**activity 过程库**：append-only 流水，列=worker/kind/tool/tool_use_id/is_error/summary/detail/metadata(JSONB)/四类 token/main_seg（schema.sql:298-339）。写入只做 utf8Clean+NULLIF 空串，无校验无幂等键——纯流水。索引精华：按 kind 的 partial index（tool_use/tool_result 配对反查）、按 worker/main_seg 分段倒序分页、result 行 INCLUDE 覆盖索引 index-only 聚合。main_sessions 把主 agent 会话切可重置分段而图/资产不动。

**迁移机制（重启即迁移）**：go:embed schema.sql，Open() 每次启动全量 Exec（db/db.go:20,159-167）。三重保障：pg_advisory_lock(7337741001) 单连接持锁；死锁 40P01 指数重试；SQL 全幂等（IF NOT EXISTS/OR REPLACE/DROP TRIGGER IF EXISTS），约束升级用 DO $$ 查 pg_get_constraintdef 判断再重建（schema.sql:204-240,262-274）。一次性回填靠"列不存在才跑"或 settings 标志位（防复活用户删除）。task_archives 状态机+tar.zst+sha256 是唯一有哈希处（压缩包完整性，非审计链）。

**资产归并**：单表多态 assets，6 类型各挂 partial unique index（root_domain 按 domain、subdomain 按(domain,record_type)、endpoint 按(url,method)等）。UpsertSubdomain 典型（assets.go:453-549）：A 记录副作用自动 UpsertIP+绑域，merge=COALESCE 保旧值+task_ids/record_value 数组并集+extra JSONB 合并。企业归属双源：company_source explicit/scope，explicit 永不被重算冲掉；RecomputeAttribution 只清 scope 行，按根域最长匹配→CIDR 最长前缀(masklen DESC)→ICP 归一化三步重算（companies.go:506-580），try_inet 把脏 IP 变 NULL 采样告警。

**覆盖度**：task_scope（source=auto/agent/manual）做分母+授权边界；covTargetCTE 一条 SQL：分母=scope 匹配 assets（company/root_domain/subdomain/CIDR>>=/icp 五谓词），分子=被本 exploration fact 节点 anchor 过的去重资产（task_scope.go:303-356）。auto 范围只从 insertAssets 顶层加、派生资产不加，防范围盲目膨胀。

**冷压缩（cold-digest）**：explorations.round_no 是任务自己的轮计数；节点带 cold_since_round 戳+content_version。判定纯函数化（agent/coldgraph.go 无 DB 依赖）：hot=活意图本身+全部上游祖先+直接子；连续冷≥R 轮（R=6）且连通块≥K（K=2）才折叠成 digest 节点+covers 边；digest 是派生视图层，构造 coldGraph 时过滤 covers 边，永不污染因果可达性（coldgraph.go:47-79）。折叠无损可还原；SupersedeDigests 原子退役旧 digest+删 covers 边防双计（digest.go:197-221）。

## ② 妙处
1. 把 LLM 写入错误挡在 DB 层：kind×state 矩阵 CHECK、rel 白名单、禁自环——agent 乱写直接被 PG 拒，应用层零防御代码。
2. covers 与因果边物理同表、语义分层：一张边表既当因果图又当压缩视图，构造时过滤隔离，复用同一套幂等写入。
3. 覆盖度锚定在图上：「测没测过」=fact 节点 anchor 集合，主观叙述变可查询结构化事实，分子分母一条 CTE 算完。
4. 幂等迁移纪律：全文件可重复执行+seed 标志位防复活+「列不存在才回填」，重启即迁移无需版本工具。
5. 渐进迁移：task_asset_links 触发器从 legacy task_ids 数组自动同步，新旧关联共存。
6. 爆炸半径隔离：写漏洞事务只对 notification_events 盲 INSERT，渠道配置永远进不了该事务。

## ③ 弱点/隐患
1. **零防篡改、零审计链**：全 db/*.go 无哈希链/行签名（sha256 仅在归档包）；SetNodeState/UpdateGoalPayload 直接覆盖 payload 不留 history；fact/finding 事后改写无痕。红队平台硬伤。
2. 方向与 kind 组合不设防：yields 的 src/dst 该是什么 kind 组合 DB 不管，只活在注释里；可造出 fact→goal 的 yields。
3. 迁移即全量重放：无 schema_version，1386 行每次启动跑一遍；DO $$ 用 LIKE '%paused%' 判断约束定义脆弱；一次性回填靠注释提醒风险（schema.sql:457-458 自认）。
4. assets 单表 40+ 列多态稀疏严重；endpoint 键=(url,method)，URL 带参数即分裂。
5. activity 无分区无 TTL，detail 全量存；asset 归属重算全表扫描。
6. anchor 桥表无来源/时间语义（溯源只做了任务侧一半）。

## ④ 探隐可借鉴
1. **kind×state 矩阵校验**（借 ck_node_state）：十种边各定义合法 (src类型,dst类型,状态) 矩阵，写入器强制。风险：TSV 需在唯一写入路径集中实现，绕过写入器即失效——须配哈希链兜底（我们恰好有）。
2. **covers 型派生层**：哈希链上叠加摘要/卷叠层（digest+covers），主链保持因果纯净。风险：需配套 content_version 失效机制。
3. **覆盖度=scope 匹配分母÷proves/evidences 锚定分子**：13 本账加"范围账"，精度门分母取范围匹配资产。风险：auto 范围扩张必须照抄"只在顶层显式插入时加、派生不加"保守规则。
4. **explicit/scope 双源归属+可重算**：人工归属免疫重算、派生归属随时可重建（最长前缀优先）。风险：重算要增量化+链下快照。
5. **CAS 状态迁移**（CompareAndSetIntentState）：九门状态流转用 compare-and-set 防陈旧读覆盖。风险：CAS 失败必须重读重试。
6. **任务轮计数去抖**（round_no 而非 wall-clock）：精度门/冷判定用轮数可复现。风险：漏 bump 即误判。
7. **重启即迁移幂等模式**：TSV 结构升级双写过渡可用。风险：务必补它没有的 schema_version 行。
8. **tar.zst+sha256+状态机冷归档**：历史任务归档用，恢复衔接哈希链校验。风险：归档件脱离链后完整性只靠单 sha256。

**对照结论**：它无哈希链/防篡改（我们核心优势）；边方向仅代码约定（我们 _EDGE_DIR 代码强制）；rel 仅 5 种无 supersedes/cross_ref/evidences（digest 的 superseded 状态是最接近的替身）；anchor 无溯源字段。**它比我们细的三点**：per-kind state 矩阵、覆盖度 CTE、冷压缩分层——直接可移植。

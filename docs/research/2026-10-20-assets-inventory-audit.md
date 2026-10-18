# 2026-10-20 家底对账（已建功能资产盘点审计）

> 性质：只读审计，零代码改动。纪律：每条结论带 文件:行 出处（sed/grep 亲验）；测试数= `grep -c 'def test_'` 实测。
> 总盘子：tests/ 共 **266 个测试文件**、test_*.py 内 `def test_` 共 **2880 个用例**（含 3 个未提交在盘文件，见 §11）。
> 仓状态基线：HEAD=a167cf0；在盘未提交：docs/audits/、idor/、secw41-work/、secw52-work/、tests/test_console_findings_overview.py、tests/test_webui_task_actions.py、tests/test_webui_techniques_deeplink.py、token-。

---

## 1. 军团战士运行时（cli/warrior/）

**已有什么**：15 个模块、2852 行（wc -l 实测）：__init__/__main__/budget/context/corrections/executor/guardrail/heartbeat/kb_context/ledger_io/loop/model_client/protocol/steer/transcript。版本 `WARRIOR_VERSION = "w5-warrior-1"`（cli/warrior/__init__.py:14）。

| 机制 | 出处（亲验） |
|---|---|
| 租约（认领/持有/回收） | cli/warrior/ledger_io.py:53 `claimable_intents`、:80 `holds`、:96 `my_active_intents`、:124-128 `claim`（走 set-intent-status 写面）；租约解析单源 cli/ledger/write_cmds.py:541 `lease_of_detail`、:522 `LEASE_EXPIRED_REASON`、:523 `LEASE_DEFAULT_MIN=60`；时间钟 :529 `parse_wall_ts` |
| 心跳 | cli/warrior/heartbeat.py:38 `beat`（节流落 timeline warrior-heartbeat 行）、:57 `check_stall`（空闲超停滞窗 raise `StallDetected` :23） |
| 断点续跑 | cli/warrior/loop.py:305-307 `mine = self.io.my_active_intents(now)` → `intent = mine[0]  # 断点续跑：接管自己活租约`；认领竞败互斥 :316-323 |
| 停滞重生 | cli/warrior/loop.py:342-345（warrior-stall 入账+status=stalled）；cli/warrior/__main__.py:129-139 `run_with_respawn`（停滞→重建新循环〔新脑 R1 全新上下文〕至优雅停或重生耗尽，退出码 0/3） |
| 同轮工具并行 | cli/warrior/executor.py:29 `MAX_PARALLEL_TOOLS = 16`（律①信号量/律④同卡同目标串行；E 舰吸收件③） |

**测试数**：test_warrior_*.py 15 文件共 **171** 用例 + test_intent_lease.py **10** = **181**（test_warrior_fake_model.py 为 0 用例的 fixture——本地假模型服务，非测试）。

## 2. 账本（13 表 + 边型 + 单写者/哈希链）

**已有什么**：
- **13 表**：cli/ledger/schemas.json 实数 **13**（goals/scope/intents/facts/findings/assets/edges/approvals/E-index/matrix/timeline/budget/creds.tsv）。**schema 单源**：cli/ledger/schemas.py:4-6 —— `TABLES` 由 schemas.json 载入，头注「由 contracts/01（contracts-v2）机械生成，禁手改」；`SCHEMA_VERSION="2"`、`GENESIS="0"*64`。
- **边型**：cli/ledger/write_cmds.py:107-108 `EDGE_KINDS` 共 **10 种**（spawns/yields/derived_from/proves/parent/attack/cross_ref/evidences/supersedes/scope-rel）；:109-120 `_EDGE_DIR` 表间方向执法。
- **哈希链**：cli/ledger/core.py:4 约定（`hash=sha256(prev_hash+"|"+逐字段转义 tab 连接)`，首行 prev=GENESIS）；:46-48 `row_hash`；:126-137 `verify_chain`（prev_hash 断链+hash 重算双检）；:209 `cmd_verify_chain`。追加面 cli/ledger/timeline.py:154-176 `append_tl_locked`（O(1) 尾读+单行追加+fsync+epoch 递增；末行撕裂=拒追加 fail-closed）。
- **单写者**：一切 timeline 追加包在 `goal_lock` 内（timeline.py:166）；代理面自证禁写：cli/ledger/egress_proxy.py:28、egress_mount.py:27「代理绝不写 13 表（单写者纪律）」。校验命令 core.py:185-206 `validate`（PASS 文案「13 表列数/schema_version/链完整」）。

**测试数**（核心机制件）：test_core 7 + test_atomic_write_b7 3 + test_timeline_o1_epoch 18 + test_timeline_single_source_b10 4 + test_v08b_chain 13 + test_goal_filelock_b7 2 = **47**（写命令族测试另散布全库，如 test_contract_chain_b10、test_supply_chain 等）。

## 3. 知识库（技法卡 + 注入 + distill）

**已有什么**：
- **技法卡 50 张**：knowledge/concepts/CP-0001.md … CP-0050.md，ls 实数 **50**；语料自述 cli/warrior/kb_context.py:9「语料=自有知识库技法卡 50 张」。库况（knowledge/index.md:3-12）：K2 precedents 5 页、K3 cve 18 行、K5 concepts 50 页、K6 patterns/learned 2 页、K8 retros 24 页、negative 2 张（PT-0001/0002.md）；K1/K2 entities/K6 core/K7 business 均 0 页。
- **注入机制**：kb_context.py:123 `retrieve`（确定性打分 top-k）、:152-159 `build_kb_section`——:159 即注入头行「以下技法卡来自本地知识库，按本意图关联检索，供参考使用：」（与裁决书 ae0d253 引证行号一致）。开关在 cli/warrior/context.py:54-63（`kb=False` **默认关**）、注入点 :125-126；零命中/任何失败=空串静默降级（kb_context.py:145,153）。
- **distill 管线现状**：cli/knowledge/distill.py:398 `distill_battle`（规则蒸馏 v1，`DISTILL_VERSION="distill-rules-v1"` cli/knowledge/__init__.py:18）；草案落 `<battle-dir>/distill/{techniques,pitfalls}` + distill-report.json（:403-410）；入册须人工确认（:18 草案纪律「蒸馏只落草案文件+人工确认位」）；套件聚合 :661。**有码、在用**。
- **草稿数**：仓内待审=**0**（knowledge/staging/staging.tsv 仅表头 0 数据行、staging/pages/ 0 文件）；仓外 ~/.tanyin/battles **20 个 battle** 有 distill 产物：技法草案 **185** + 避坑草案 **98** = **283 份草案待人工确认**（0 已入册——四道门槛无真实流量）。

**测试数**：test_warrior_kb_context **20** + test_knowledge_distill **32**。

## 4. 考卷 GT（evals/gt/）

**已有什么**：
- **战场数**：evals/gt/gt-index.tsv 注册 **8 条**（全 active）：range-56-v5（session-gt，56 真值）、zl-webface-v1 / zl-supplychain-v1（source-gt）、replay-G-r25/r26/r27（replay-fixture）、zl-chain-v1（chain-gt，2 链 7 步）、range-chain-v1（chain-gt，2 链 5 步）。battlefields/ 目录 **4 个 JSON**。注：裁决书提「GT 六战场→3/12」按战场合计口径不同（6 实战面 vs 注册表 8 条含 3 replay 夹具）。
- **链数**：zl-chain-v1=2 链、range-chain-v1=2 链（gt-index.tsv 第 6/7 列）。
- **判分两档**：evals/gt/gt_eval.py:32 `CHAIN_TIERS = {"full": 1.0, "partial": 0.5, "zero": 0.0}` 写死；`score_chain` :42-55、`chain_recall` :58-60。源头锚定复核另有 evals/gt/gt_verify.py（252 行）。
- **基线 TSV**：evals/gt/baselines/gt-baseline-v1.tsv（3 行：b40-G-r41 recall 0.625 → b42-G-r43 0.6964）+ gt-chain-baseline-v1.tsv（3 行：b24-b26 chain_recall 0.75）。
- **capability_gate 入口**：scripts/capability_gate.py（632 行，`main` :516）——评测棘轮：召回率只升/误报率只降否则拒合并，`--update-baseline` 只紧不松；消费 gt-index.tsv（头注「消费方=capability_gate/评测棘轮」）。

**测试数**：test_capability_gate **34** + test_gt_registry **16** + test_gt_chains **15** + test_gt_eval_active_set **3** + test_evals_static/dynamic/ci **7/8/4** + test_k1_baseline_score **13** + test_battle_registry **15** + test_battle_auto **5** + test_first_battle_readiness **7**。

## 5. 护栏（guardrail.py）

**已有什么**：cli/warrior/guardrail.py（340 行，CH cyber-harness exts/guardrail 吸收件）。四道准入门——`admit` :246 docstring「序：停卡 → 范围前置 → 风险段 → 后果段」；`_admit` :261-337：阶段 0 意图内停卡（:264 起）、1 范围执法前置接 enforce 单源（:276 起；default_scope_fn :142-152）、2 风险段（:284 起）、3 后果段；外加 fail-closed 永不 raise（:31、:255-259）与重复拒绝退避+整卡停用（docstring :14-21）。类面 :167 `Guardrail`。
**注意**：「四律」字样**不在代码中**——代码事实=admit 四段序；术语出自裁决书 :99「E舰护栏四律」。

**测试数**：test_warrior_guardrail.py **30**。

## 6. 枚举测绘与探索图底座

**已有什么（代码）**：
- engines/ **7 目录**：deepex（derive.py）、nuclei（adapter.py+templates+release.pub 供应链验签）、sqlmap（adapter.py）、web-blackbox、vuln-agent、vulnclaw、session-viz。
- **覆盖记账=有代码**：matrix.tsv 命令族——cli/ledger/matrix_init.py:62 `run_matrix_init`（基线铸造，写前拒收 :71-82）、write_cmds.py:1688 `matrix-set`、:1691 `matrix-freeze`；可达收敛 cli/ledger/graph_cmds.py:149-168+226（`reachable_gap_cells` BFS 单源）；链 frontier 过滤 write_cmds.py:1698 `chain-ls`（:1627-1628 查询侧过滤+:567-578 写入侧执法）；webui 投影 cli/webui/api_v2_coverage.py。
- **v3 吸收清单**：docs/design/2026-10-20-graphled-master-verdict.md:48-56（§13：判定/生成/测绘三引擎对位+四道门槛+蒸馏+优先级+frontier）。

**只是设计**：「探索图」会话对象范式（ExpID、点进即操作）=verdict §14 :58-63 纯设计；ARTEX 对比 :85。

**测试数**：engine 族 22+3+36+5+17+8=**91** + test_converge_reachable **4** + test_authz_matrix **7** + test_hosts_matrix **8**。

## 7. 多任务（意图池/租约认领/十并发）

**已有什么（代码）**：意图池=intents.tsv 事件源+命令面：add-intent（write_cmds.py:386-477，:477 事件入链）；认领=set-intent-status 租约（write_cmds.py:669、:1680，机制详见 §1）。webui 任务写面已有：cli/webui/server.py:26-28 POST /api/battle/new（授权八问缺一=422）、/api/battle/control（pause/resume/stop killpg+EXIT）、:657-669 写路由。
**只是设计**：裁决书 :80 自认——多任务(10并发)**已有仅=goal-dir 隔离独立账本+每任务一战士**；**缺三件**：①全局资源治理（全任务工具总并发帽+模型通道共享限速）②十卡仪表盘 ③supervisor 舰队化。排队+补位=§18 吸收项（:87）。**十并发/排队=设计态**。

**测试数**：test_intent_lease **10**（任务操作测试 test_webui_task_actions.py 在盘**未提交**）。

## 8. LLM 池（llmpool）

**已有什么**：cli/ledger/llmpool.py（283 行）：:52 `classify`（ok/no_failover/hard/soft 分桶；400 及表外 4xx 保守不转移）；:94 `LLMPoolRegistry`；:109 `pick`（跳冷却道）；:124 `report`；:178-207 trip/recover 事件；:225 `_persist`。接线 cli/ledger/llmpool_wire.py:68 `attach`（failover 事件→goal timeline 入链）。消费者 cli/warrior/model_client.py（链序选道+attempts 全程留痕+fail-closed）。**录制**：cli/warrior/transcript.py:2「『LLM 录制』（质量律 R4 原始对话存档）」、:19 `Transcript`、:29 `record`；只读浏览页 cli/webui/static/pages/llm-recordings.html + cli/webui/api_v2_llm.py（:131 列表/:173 详情）。

**测试数**：test_v08a_llmpool **50** + test_warrior_model_client **8**。

## 9. 验证官/复验（非 LLM 复放）

**已有什么（代码）**：cli/tanyin-replay（356 行，:129 `cmd_replay`）——EV 卡**盲重放**：raw_request 解析→{{vault:cred-N}} 进程内解密→S4 治理四门（:221 起：①授权窗 ②危险方法分类 ③REPLAY_CAP=3 次数帽无 CLI 豁免 ④scope 单源 enforce.load_scope）→http.client 直发→matcher 评估三态（reproduced/not-reproduced/env-diff）。复验纪律另件：EV 链复核钩子 cli/ledger/knowledge.py:1186-1192（ev-recheck 行铸上 goal 哈希链）；webui 复测页 cli/webui/api_v2_retest.py。
**只是设计**：「验证官」=军团六兵种之一（verdict:28「验证官(非LLM复验器)」）——兵种模板未建；裁决书 :105 自类「复验」为②有底缺细节。

**测试数**：test_replay_chain_b8 **1** + test_fd_key_replay_v6_b13 **3**。

## 10. 看门狗/范围锁

**已有什么**：看门狗纯函数核 cli/ledger/watchdog.py（101 行）：:15 `stall_grade`（soft 180s/hard 480s）、:24 `backoff_delay`（30×4^(n-1) 帽 480）、:31 `read_directive`（战中指令）、:47 `next_tick`（自适应监听）、:54/:65 预算读取/分级、:79 `is_logonly`（LOGONLY-ALIVE 照亮不击杀）、:89/:99 ask:human 通道与 WAIT 态机。集成：cli/tanyin-runner:22 import watchdog（407 行监督者）。**范围锁**：cli/ledger/enforce.py:310 `load_scope`（scope.tsv 生效链，**Tier1/2/3 单一事实源**）、:352 `scope_verdict`（in/oob/out）、:371 `out_of_scope_hosts`；空 scope=一切带主机命令界外 fail-closed（:7）；guardrail 范围前置同源（guardrail.py:142）。

**测试数**：看门狗族 test_runner_watchdog **12** + test_v05_watchdog_enforce **7**（+sim_watchdog.sh 模拟脚本）；scope/enforce 族 13+21+7+5+4+9+2=**61**。

## 11. webui

**已有什么**：
- **页面数**：cli/webui/static/pages/ **21 个 HTML**（anchored-chat/approval-center/approval/asset-registry/assets/broadcast/capability/coverage/evals/finding-detail/llm-recordings/llm-status/new-task/report-center/retest/settings/system/tasks/techniques/tools/workspace）+ /login 由 server.py 直出（:21、:447-449）= **22 页**。控制台五页只读投影另在 cli/webui/console.py（:2）。
- **真数据 API**：20 个 api_v2_*.py + api_pages.py 页路由。**读真数据（TSV/盘面）**：approval_center/ask/asset_registry/assets/broadcast/capability/coverage/evals/findings/guard/llm_status/llm/reports/retest/settings/tasks/techniques/tools/workspace（各文件含 _read_tsv/open/_read 调用，实测计数 3-14 处）。**例外**：api_v2_system.py **零任务数据读**——设计使然（全局配置转述设计档+代码常量，:4-6「写面=留位不开，POST_ROUTES 恒空」），非假数据但非任务数据源。
- 任务写面三钮：server.py:657-669（/api/battle/new、/api/battle/control、/api/battle/say）。

**测试数**：webui 族在盘共 **638** 用例（22 个 pagespec 文件 + test_v09a_webui 27 + test_webui_mount_all 33 + test_console_ui 41 等）——**其中 3 个文件未提交**（test_console_findings_overview.py、test_webui_task_actions.py、test_webui_techniques_deeplink.py），已提交口径略少。

---

## 名不副实处清单

**说有实无（名高于实）**：
1. **「护栏四律」**——guardrail.py 无此命名；代码事实=admit 四段序（停卡/范围/风险/后果，guardrail.py:246）。术语仅存于裁决书 :99。
2. **「验证官」兵种**——仅设计（verdict:28）；运行时对应物=tanyin-replay 脚本，兵种模板/六维配置零代码。
3. **「十并发/排队」多任务治理**——纯设计；已有仅 goal-dir 隔离+每任务一战士（verdict:80 自认缺三件：总并发帽/十卡仪表盘/supervisor 舰队化）。
4. **「探索图底座」会话对象范式**——engines 适配器+覆盖矩阵有码，但 ExpID 式探索图/点进即操作纯设计（verdict §14）。
5. **api_v2_system 写面**——留位不开（POST_ROUTES 恒空，api_v2_system.py:36）。
6. **distill「飞轮」**——管线有码且跑过 20 战，但 **283 份草案 0 入册**：人工确认位空转，四道门槛+棘轮无真实流量（staging.tsv 0 数据行）。

**说无实有（实高于名）**：
1. **复验纪律**被裁决书归「有底缺细节」（:105），实际复放执法相当硬：S4 四门+REPLAY_CAP=3+三态判定+EV 复核入哈希链（tanyin-replay:221+、knowledge.py:1186-1192）。
2. **webui 任务操作**看似只读投影，实际已有写面三钮（server.py:657 /api/battle/new+control+say），且在盘有未提交测试 test_webui_task_actions.py。
3. **webui 测试规模**易被低估：在盘 638 用例护 22 页（3 文件未提交，git 口径会少）。
4. **「每任务一战士」并行度**不止进程级：同轮工具并行 ≤16 信号量已落地（executor.py:29）。

## 对账结论（每件一句话）

1. **战士运行时**：15 模块 2852 行四机制（租约/心跳/断点续跑/停滞重生）全有码，181 测在护。
2. **账本**：13 表 schema 单源（机械生成禁手改）+10 边型方向执法+goal_lock 单写者+sha256 哈希链验链命令全有码，核心件 47 测。
3. **知识库**：50 技法卡在册、kb 注入默认关、distill 管线有码——但 283 草案 0 入册是飞轮空转实证。
4. **考卷 GT**：注册表 8 条（2 链式战场）、两档判分写死、双基线 TSV、capability_gate 棘轮入口全有码，127 项相关测。
5. **护栏**：四段准入序+fail-closed+退避停卡有码 30 测；「四律」是文档语言非代码命名。
6. **枚举测绘**：7 引擎目录+matrix/converge/frontier 覆盖记账有码；探索图会话范式纯设计。
7. **多任务**：意图池+租约认领+webui 任务三钮有码；十并发治理三件（总帽/仪表盘/supervisor）纯设计。
8. **LLM 池**：分类-熔断-冷却-切道全链有码+故障转移事件入链+录制落盘浏览页，58 测。
9. **验证官/复验**：非 LLM 盲重放（S4 四门+三态）有码；「验证官」兵种与复验自动化升级为设计态。
10. **看门狗/范围锁**：看门狗纯函数核+runner 集成+scope 三层同源执法全有码，80 测。
11. **webui**：22 页+20 个 v2 API 基本全真数据投影（system 页除外，设计使然），任务写面已有，638 测在护（3 文件未提交）。

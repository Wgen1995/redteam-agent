# 批次 5（知识飞轮+语料入库）实施计划 —— staging/lint/四门槛/三元组/CLIENT-NN/graph.ndjson/外部语料入库/CVE 联网核验/六探知项落地

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付探隐 v2 知识飞轮与语料入库（§11 批次 5 行）：K1-K8 八类知识库骨架与 front-matter 契约冻结（技法页/先例页）、staging→lint→人审→commit 入库流水线、learned→core 四门槛晋升、先例三元组与 graph.ndjson 导出、CLIENT-NN 脱敏映射、CNPEN 82 五类素材+外部语料（VulnClaw 47 专题/BugHunter/Threatswarm/CEP）入库、K3 本地 CVE 快照与离线 nday 匹配（联网仅核验边界）、反向验证零命中载体落地，并集中裁决落地六探知项（G-24/G-26/G-27/G-28/G-23/R6）。

**Architecture:** 铁律 7 边界不动——语义蒸馏（提炼什么知识页、怎么写正文）永远是 LLM+skill 的职责，CLI 只做机械运算：staging 台账、front-matter 校验、脱敏哨兵（复用 special.py 泄漏形态表单源）、去重哈希（复用 norm.py 归一语义）、确定性导出、三元组匹配、K1 基线查表算分、CPE 离线匹配。知识库载体=仓库 knowledge/ 种子库（版本化 format_version=kn-v1；批次 6 安装器拷贝至 $TANYIN_HOME/knowledge/，本批 CLI 一律 --knowledge-dir 参数化）。账本 44 命令面零新增；新工具 tanyin-knowledge=工具箱第 12 员（契约 09 勘误 11→12，G-1 先例）。六探知项中动账本面的三件（intents 15→17 双列、set-replay-state --timestamp、add-intent cap 拒收）全部走微版本勘误通道（零存量数据期先例，schema_version=2 不递增；「契约 v3 首批」= b4 台账契约 v3 待办清单的集中清账，非 schema 版本升级）。

**Tech Stack:** python3 ≥3.9 标准库（零三方运行时依赖）；unittest + 黄金回归（tests/run_golden.py，--bless 显式建档）+ 双平台 CI（windows/ubuntu × py3.11/3.12）；front-matter 解析复用 cli/ledger/phases_engine.parse_yaml（stdlib 受限 YAML 子集，cards.py 先例）。

**Spec:** docs/design/2026-09-21-tanyin-v2-design.md（§11 批次 5 行+§7 知识系统飞轮四机制/§7.2 初始语料入库方案+§9.4 双知识库抽查+§3.4 布局+§2.4 铁律 7+§5.2 P6 门）；docs/design/2026-09-24-completeness-recon-knowledge-evolution.md（K1-K8 八类全集+入库纪律「脱敏→机器检查→人工审→四门槛」+§3.2 反漏三件套）；docs/research/2026-09-24-vulnclaw-analysis.md（§6.3 批次 5 取材清单：47 专题 skill+warstory+experience 人审蒸馏+证据去重/BM25 双轨；批次 6 项只登记不实现）；docs/design/2026-09-24-b3-discovery-notes.md 与 2026-09-24-b4-discovery-notes.md（G-24/G-26/G-27/G-28/G-23/R6 裁决输入+契约 v3 回注待办清单）；contracts/（01/02a/04/06/09 冻结接口）；phases/（P3/P4/P6/TRIGGERS/PROTOCOL）。

## Global Constraints

- **仓库**：/Users/wgen/redteam-agent；**绝不碰** /Users/wgen/Documents 与 panorama/；.research/repos/ 只读（VulnClaw 本地 clone，gitignore 在册）。
- **字节纪律**：UTF-8 无 BOM + LF（仓库根 .gitattributes 已钉；新文本文件写盘一律 `encoding="utf-8", newline="\n"`）。
- **运行时**：python3 ≥3.9 标准库零三方依赖；知识检索 v1=词表键+规范哈希精确匹配（BM25/嵌入双轨不实现——VulnClaw 分析 §6.3 登记留档）。
- **Windows 等价**：新 CLI 入口必配 `<名>.cmd` 包装（内容=`py -3` 调用）；测试入口一律 `[sys.executable, <脚本路径>, ...]`；控制台启动重配 UTF-8（`ensure_utf8_stdio()`）。
- **44 命令面冻结**：账本命令零新增；签名/拒收条件变更（--priority/--cred/--timestamp/--cap 与 converge 判据）一律**微版本勘误通道**+ contracts/README.md 勘误索引登记；schema_version 保持 =2。
- **铁律 7**：知识提炼语义层禁入 CLI（tanyin-knowledge 不判「这条经验值不值得入库」——人审 checklist 判；CLI 只查四门槛机械条件与 schema）；CLI 不主动对外请求——**CVE 联网核验不进 CLI**（联网=宿主 WebSearch 能力，P6 技法页纪律；CLI 侧只做离线快照匹配与核验标记 lint）。
- **确定性红线**：一切进产物的时间戳显式传入（--timestamp=ISO8601 / --today=ISO 日期），禁 datetime.now()（G-23 正是要退役最后一处墙钟；knowledge log.md 同律）。
- **TDD**：每任务先写失败测试→跑红→最小实现→跑绿→commit；commit 消息中文、格式「批次5 T<N>：<内容>」。
- **测试与回归**：`python3 -m unittest discover -s tests` 全绿；`python3 tests/run_golden.py` 零漂移（有意刷新/新面 --bless 建档须在任务内声明并 git diff 逐一归因）。
- **退出码对齐 Strix**：0=通过 / 1=门禁失败（REJECT/FAIL，零落账或零变更）/ 2=用法或环境问题。
- **HANDOFF 记账**：每任务完成后在 docs/HANDOFF.md「开发流水」追加一行（日期｜子代理 T<N>｜动作+证据｜commit）。

---

## 前置裁决（批 5 前必办六件 + 本计划补充裁决 R7-R14）

### 裁决 A：G-24 severity_expect 基线表=K1 方法论映射落表 + intents.priority 物理列落地

- **基线表来源=K1 方法论映射（非历史飞轮统计）**：`knowledge/methodology/k1-baseline.tsv`（`vuln_class, severity_expect, cost_hint, rationale_brief, vocab_version` 五列），行键=shared/VOCAB.md 全集（当前 12 个 wstg-* 类恰各一行，lint 断言覆盖率 100% 且无缺行）；细类行（如 `inj.sql`——夹具既有形态）可选、须带父类前缀（`wstg-inpv:inj.sql` 形），score 查表次序=细类→wstg 类→缺省 0.5+lint 告警。初值由 WSTG v4.2 严重度倾向+CNPEN 复盘校准评定（评定规则表见 T12，**人审冻结**——语义判断不进 CLI，CLI 只校验枚举/格式/覆盖率）。
- **intents.tsv 15→17 列**：新增 `priority`（浮点 0-1，可空=未算分）与 `cred`（文本，CRED-id 引用），插入位=`reason` 之后、`schema_version` 之前（尾约定 schema_version/created 不动）。与 G-27 的 cred 列**一次重铸**（15→17 只付一次夹具/金样重铸成本）。
- **CLI 只读算分=tanyin-knowledge score**（非账本命令，44 面零触碰）：读 K1 基线+assets.meta+graph-horizon 可达集+creds+先例命中，输出三因子与乘积（公式=契约 01 勘误已冻结的 `priority = severity_expect × asset_value × exploitability`，确定性可复算）；**Top-K 选择仍=总控决策**（契约 09 §4 边界 2 不破）。add-intent 增可选 `--priority`（落列；0-1 浮点校验）——总控把 score 结果回填落账，算分与落账分离但都可审计。

### 裁决 B：G-26 边词汇路径语义——v1 映射维持，细分权重/成本走数据文件（边语义 v2 不开）

- **edges.tsv 10 边词汇与 graph-paths/graph-horizon 命令面零改动**：R-G-2 v1 映射（attack={attack,proves,evidences}/asset={parent,scope-rel}/cred=凭据链）已冻（f87ca25），实测够用。
- **权重/成本参数化=知识库数据文件**：K1 基线表 `cost_hint` 列（每 vuln_class 预估请求量级 1/2/3）+K2 先例页 front-matter 可选 `weight_hint`（0-1）——消费端=tanyin-knowledge score（读侧加权），graph-paths 不消费权重（保持纯拓扑枚举，金样面稳定）。
- **边语义 v2（infiltrate/pivot/exfil-ability 细分）不开**：无先例数据支撑=YAGNI；等 K2 先例页积累出「路径成本实证」后由批次 6+ 评审再裁（伴生登记见探知项 G-30）。

### 裁决 C：G-27 intents cred 绑定列（契约 v3 首批）+ trigger-audit ② 升级逐对配对

- `add-intent --cred` **参数与校验已存在**（write_cmds.py:346-383：kind=authz-diff 强制 --cred+CRED 行存在+status=active+permitted_actions 覆盖）——缺口只在值无物理列（现随 detail 携带）。落地：`--cred` 值改落第 17 列物理列（detail 不再附注）；**任何 kind 下 cred 非空都走引用闭合校验**（不分 kind，写前拒收）。
- **trigger-audit ② 从全局口径升级逐对**：每个 kind=session 的 CRED 行须存在 `kind=authz-diff 且 cred=<该 CRED-id>` 的 intent **或** 延后 fact（`target=authz-diff:<CRED-id>`——既有通道不变）。当前实现（phases_engine.py:633-641）的 `any(kind=="authz-diff")` 全局判定退役。

### 裁决 D：G-28 converge 结构性停机 + 攻击路径进 EV

- **可达未测格结构性停机**：converge-check 新增输出行 `#reachable-gaps=N`/`#unreachable-gaps=N`（graph-horizon 语义单源复用——从 graph_cmds 抽 `reachable_gap_cells(s)` 公共函数，converge/horizon 两处共用）；判据升级=「可达空格=0 且 不可达空格=0（不可达空格经 `unreachable:` 前缀置态「-」后天然非空格——图依据显式置格而非静默豁免；matrix-set 零改动即支持：批4 裁决 A 修正后「旧前缀为空→任意前缀放行」已放行 unreachable: 首次归类）」；可达空格=0 而不可达空格>0 时输出 structural 提示（P3 置态后即收敛）。P3.md「收敛判定语义」节补 unreachable 通道注记（T19）。
- **攻击路径进 EV**：P4.md duty 增「攻击链落证」步——总控跑 `tanyin-ledger graph-paths --from=<入口资产> --to=scope-root`，stdout 存 `evidence/attack-paths.txt`（artifact 只增不覆盖律，重跑 -r2 后缀），`ledger-add-evidence --source-type=capture --repro-command="<graph-paths 命令原文>"`（repro_command=只读命令天然可复现；raw_excerpt=路径首行摘要）。EV 卡片零新字段（artifact_path 通道承载）；契约 04 P4 duty 勘误注记（T2）+机械可测全链（T8）。

### 裁决 E：G-23 set-replay-state 墙钟 --timestamp 通道（checkpoint 先例）

- `set-replay-state` 增 `--timestamp=ISO8601` **必填**；check_cmds.py 该命令路径的两处 `_now()`（`_append_timeline` 的 ts 缺省 check_cmds.py:193、findings 联动行 created check_cmds.py:253）全部退役——时间戳一律来自参数。契约 02a §36 勘误（参数表+签名行）。评审收尾 6d3a033 的「墙钟绕道 core.row_hash 直写」过渡手法随本裁决转正为参数通道，diff-authz 夹具的重放事件行改由 --timestamp 铸（夹具重铸与 T3 同批声明）。

### 裁决 F：R6 cap 机检硬门（挂 G-20，契约 v3 增常量同批落地）

- `AUTHZ_DIFF_PAIR_CAP=24` 从双载文档常量（differential.md+P3.md）转**代码常量**：落 cli/ledger/write_cmds.py（add-intent 校验位旁），语义=`kind=authz-diff` 时**同端点**（计数键=asset+kind 二元组，经既有 dedup_key 前缀比对）的既有 authz-diff intents（status∈{candidate,pending,active}）计数 ≥cap → REJECT（附计数与 cap 值）；`--cap=N` 可选覆盖（evals 可重放，G-3 --rate-minutes 同型）。契约 02a §3 拒收条件+契约 04 constants 表（`authz_diff_pair_cap: 24`）双落（T2 doc+T5 code）；测试锚定常量值与拒收行为（grep 全仓 .py 引用从 0→≥2 处）。

### 补充裁决（本计划起草期发现，随对应任务落地）

| # | 裁决 | 依据 |
|---|---|---|
| R7 | **知识库载体与工具面**：仓库 `knowledge/`=种子库（format_version=kn-v1；批次 6 安装器拷贝至 $TANYIN_HOME/knowledge/——本批不写安装器）；`tanyin-knowledge`=工具箱第 12 员（契约 09 勘误 11→12，G-1 先例；允许类=「确定性账本运算」同型——输入输出可字节级回归，export/match 金样化）。CLI 一律 `--knowledge-dir` 参数化，测试用 fixtures 副本，**种子库只读纪律**：指向仓库 knowledge/ 时一切写子命令（source-register/approve/commit/promote/demote/client-map add）REJECT（exit 1，防 CI 误写种子）。 | §3.4 布局+§7.1；金样确定性 |
| R8 | **staging 状态机**：`staged →(lint)→ lint-passed →(approve 人审)→ approved →(commit)→ formal`，另有 `rejected` 终态；状态载体=`staging/staging.tsv`（机器索引：staging_id/page_id/class/title/source_id/status/checksum/created/approved_by/approved_at 十列）；审计叙述=`log.md` 追加式（ts\|event\|id\|detail 四栏——设计 §7.1 命名载体；知识库非 13 表账本，不带链式哈希，交战区侧锚=P6 `approve --knowledge` 落 approvals.tsv（既有 decision=knowledge-approved 通道，write_cmds.py:98 在册）。 | §7.1；四机制① |
| R9 | **四门槛机检分解**（learned→core 晋升）：①复现≥2=被 ≥2 个先例页 `applied_patterns` 引用（页 ID 计数）；②跨目标有效=引用先例页的 `client` 去重计数 ≥2；③人工审批=log.md 存在 `approve` 且 detail 含 `for=promote`；④无指纹泄漏=该页 redact 哨兵扫描零命中。①②④=tanyin-knowledge promote 机械核验，③=在场检查；**质量判断留人审 checklist**（knowledge/checklists/review-checklist.md）。不全过=REJECT 附缺口清单。 | §7.1 机制③；完备性「入库纪律」 |
| R10 | **去重哈希**：dedup_key=`sha256(kind + vuln_class + 标题归一)`（归一=去空白/全半角归一/小写——norm.py 语义同源新窄函数，不碰 norm 轨）；同 dedup_key 重复 commit=REJECT（intents dedup 先例）。**语义近重复合并不实现**（VulnClaw distiller 0.88 嵌入阈值无嵌入载体）——lint 对同 class 页数 ≥8 输出「人审合并建议」告警；登记 G-30。 | VulnClaw 分析 §6.3 取材+边界 |
| R11 | **CVE 边界**：K3 快照=`knowledge/cve/cve-snapshot.tsv`（cve_id/cpe_prefix/version_start/version_end/severity/published/source 七列，NVD/CISA KEV 公共数据精选 ~14 行种子）；`nday-match`=纯离线 CPE 前缀+版本区间比较（零联网、零 urllib/socket/http import——测试断言）；联网核验=P6 技法页纪律（宿主 WebSearch 对照 PSIRT/NVD/KEV，「明确不信任训练数据」），CLI 侧只 lint 标记：`cve_refs` 非空的页必须每个 CVE 在 `cve_verified`（{cve,source,verified_at} 列表）有对应行，缺=FAIL；verified_at 距 --today 超 365 天=stale 告警（match 输出带 [stale] 降权标注，score 不消费 stale 页）。 | §7.2 CVE 行+§1 Nday 通路「联网仅核验」 |
| R12 | **CLIENT-NN 映射**：`knowledge/client-map.tsv`（client/real_ref/note/assigned_at 四列）**运行时文件**——.gitignore 增一行排除（真实映射永不进仓）；仓库种子只带 `knowledge/client-map.example.tsv` 模板；`client-map next/add/list` 子命令操作运行时文件（种子库只读纪律同 R7）；先例页/复盘页 front-matter 的 client 字段只允许 CLIENT-NN 形态（lint 强制 `^CLIENT-\d{2,}$`——无映射真值可反查=无跨客户残留机检的先决条件）。 | §7.1「映射表单独存放」；§9.4 判据③ |
| R13 | **反向验证载体**：phases.yaml P6 断言文本零改（`tanyin-redact --reverse-verify`）——实现在 tanyin-redact 入口增旗标分发至 special.py 新 handler `h_reverse_verify(goal_dir, rest)`：敏感词集=assets.value 全集（域名/IP/URL 型资产）+creds.username_ref+special.py 既有泄漏形态正则（单源复用）；目标草稿缺省 `report/report-draft.md`（`--target` 覆盖）；命中=逐行列出+exit 1，零命中=print 零命中+exit 0。phases_engine 断言执行回路拆 EXTRA_TOOLS：tanyin-report 维持 ENV-HALT（批次 6），tanyin-redact 分发至 handler（yaml 断言从此真跑——现状 phases_engine.py:200,377-379 两处 ENV-HALT 拦截退役一半）。 | §5.2 P6 断言；批4 Ruling B 现状 |
| R14 | **词表版本化**：知识页 front-matter 必填 `vocab_version`（当前唯一合法值 `WSTG-v4.2`，与 shared/VOCAB.md version 行同源——lint 朗读该行取支持集）；K1 基线表行带 vocab_version 同律；VOCAB 升版=新版本值入支持集+页可声明迁移，lint 对旧版本页输出迁移提示（不 FAIL——先例数据保值）。 | §11 批次 5 接口列「词表版本化」 |

---

## 文件结构图（每文件一职责；★=本批新增）

```
knowledge/                          ★ 仓库种子库（R7；批次 6 安装器拷贝至 $TANYIN_HOME/knowledge/）
  format_version                    ★ 内容=kn-v1（单行；不匹配拒绝操作并提示迁移）
  index.md                          ★ 库索引：K1-K8 类目→目录映射+页数统计（commit 时重生成）
  log.md                            ★ 知识库追加式台账（ts|event|id|detail；R8）
  overview.md                       ★ 检索入口概览（LLM 摘要化入口：类目+词表版本+页数）
  checklists/review-checklist.md    ★ 人审 checklist（四门槛人工审文档+VulnClaw experience 流程注记）
  methodology/k1-baseline.tsv       ★ K1 严重度期望基线表（裁决 A；score 消费）
  methodology/k1-wstg-map.tsv       ★ K1 WSTG↔ASVS↔OSSTMM 映射表（词表版本化锚）
  concepts/CP-*.md                  ★ K5 技法页（技法页 front-matter；CNPEN 复盘/VulnClaw detail-pack）
  precedents/PR-*.md                ★ K2 先例页（三元组 front-matter；CNPEN 测试记录/warstory）
  entities/EN-*.md                  ★ 实体页（第 N 目标出现/模式 M 有效/K 已修复累积）
  targets/TG-*.md                   ★ 目标指纹页（开局指纹匹配素材）
  patterns/core|learned/PT-*.md     ★ K6 模式页（learned→core 四门槛晋升；含误报回流模式）
  business/BZ-*.md                  ★ K7 业务模板（行业化检查单；CEP 素材落位）
  retros/RT-*.md                    ★ K8 复盘页（必答三问：漏了什么/触发器缺哪/通道弱哪）
  cve/cve-snapshot.tsv              ★ K3 本地 CVE 快照（R11；~14 行精选种子）
  cve/README.md                     ★ 快照来源/更新纪律/联网仅核验边界
  sources/SOURCES.tsv               ★ 语源登记（source_id/origin/path/sha256/license/note/registered_at）
  sources/vulnclaw/LICENSE.note     ★ MIT 许可注记（取材合法性凭证；正文引分析报告）
  staging/staging.tsv               ★ staging 状态机机器索引（R8 十列）
  staging/pages/*.md                ★ LLM 蒸馏草稿区（front-matter 带 staging_status）
  client-map.example.tsv            ★ CLIENT-NN 映射模板（真值文件 client-map.tsv 已 gitignore）
  graph.ndjson                      ★ 三元组导出（export 确定性重建；行级可合并预留）
contracts/
  14-knowledge-schema.md            ★ 批次间接口：页 front-matter schema 全集+staging 状态机+
                                       四门槛+CLIENT-NN+graph.ndjson 行 schema+ID 前缀表+词表版本化
  01-ledger-schema.md               [改] §3.3 intents 十七字段表（priority/cred；裁决 A/C）+勘误补记
  02a-command-signatures-draft.md   [改] §3 add-intent 新参数/§36 set-replay-state --timestamp/
                                       converge-check 结构性停机（裁决 C/E/D，随 T3/T4/T5/T7 各自落笔）
  04-phases.md                      [改] constants 增 authz_diff_pair_cap=24+restart_rate_minutes=10
                                       （R6/G-3）+gate-fail 事件词汇补注（G-7）+P4 duty 攻击链落证注记
  06-evidence-cards.md              [改] 文末注记：G-16 结案（同值性维持 replay 侧单点）
  07-submission.md                  [改] 文末注记：G-19 结案（perspective 维持 network_position 承载）
  09-cli-surface.md                 [改] 工具面 11→12（tanyin-knowledge；G-1 先例）+canary 干跑
                                       口径注记（G-8 清账）
  README.md                         [改] 契约 14 登记+本批勘误索引
cli/
  tanyin-knowledge / .cmd           ★ 第 12 工具（13 子命令；R7 只读纪律）
  ledger/knowledge.py               ★ 知识库机械运算单源（schema/lint/哈希/导出/匹配/算分/快照匹配）
  ledger/write_cmds.py              [改] add-intent --priority/--cred 落列+AUTHZ_DIFF_PAIR_CAP 拒收（T3/T5）
  ledger/check_cmds.py              [改] set-replay-state --timestamp 必填+两处 _now() 退役（T4）
  ledger/query_cmds.py              [改] converge-check 增可达性计数与结构性停机判据（T7）
  ledger/graph_cmds.py              [改] 抽 reachable_gap_cells 公共函数（converge/horizon 单源；T7）
  ledger/phases_engine.py           [改] trigger-audit ②逐对+④高危横向（T6）+EXTRA_TOOLS 拆分
                                       tanyin-redact 分发（T15）
  ledger/special.py                 [改] 泄漏形态扫描抽出纯文本 API+h_reverse_verify（T10/T15）
  tanyin-redact                     [改] 入口增 --reverse-verify 旗标分发（T15）
  README.md                         [改] 批次 5 节（tanyin-knowledge 速查+用法+测试）
phases/
  P4.md                             [改] duty 增攻击链落证步（T8）
  P6.md                             [改] duty 命令化（client-map/reverse-verify/双锚审批/commit+export）
  P3.md                             [改] 算分节读侧改 tanyin-knowledge score+nday 通路+unreachable 通道注记
  TRIGGERS.md                       [改] ②/高危行消费检查列文字升级（版本不 bump；T6）
  PROTOCOL.md                       [改] §5 trigger-audit 检查面 3→5+P6 反向验证载体注记
engines/web-blackbox/phases/recon.md [改] A8 外推节补知识库实体邻居查询接点+assets.meta CPE 指纹（T19）
SKILL.md                            [改] 路由表知识库行+P6 沉淀行（token<2000 复测）
tests/
  test_knowledge_contract.py        ★ T1/T2 契约钉子（含 TestContractV3Sweep）
  test_intents_columns_b5.py        ★ T3 双列
  test_replay_timestamp.py          ★ T4 时间戳
  test_authz_cap.py                 ★ T5 cap 机检
  test_trigger_audit_v2.py          ★ T6 逐对+高危
  test_converge_reachable.py        ★ T7 结构性停机
  test_attack_paths_ev.py           ★ T8 攻击链 EV
  test_knowledge_init.py            ★ T9 骨架/init
  test_knowledge_staging.py         ★ T10 staging/lint
  test_knowledge_export_match.py    ★ T11 export/match
  test_k1_baseline_score.py         ★ T12 基线/算分
  test_knowledge_promote.py         ★ T13 四门槛
  test_nday_match.py                ★ T14 离线匹配
  test_reverse_verify.py            ★ T15 反向验证+P6 端到端
  test_knowledge_ingest_cnpen.py    ★ T16 CNPEN 结构断言
  test_knowledge_ingest_external.py ★ T17 外部语料结构断言
  test_eval_scripts.py              ★ T18 eval 自检
  test_skill_resident.py            [改] 扩 TestBatch5Wiring（T19）
  fixtures/knowledge/               ★ 知识库测试夹具（mini 库：合法页+脏页+重复页+缺核验页+过期词表页）
  fixtures/knowledge-dirty/         ★ 抽查 eval 负例夹具
  eval_knowledge_spotcheck.py       ★ 双知识库抽查 eval（§9.4 四判据；T18）
  eval_reverse_verify.py            ★ 反向验证零命中 eval（脏/净两案例；T18）
  golden/                           [改] kn-export/kn-match/kn-nday 三新面+intents 列重铸刷新面（T3/T11/T14）
docs/design/2026-09-24-b5-discovery-notes.md ★ 批 5 探知项台账（G-29 起）
docs/design/2026-09-24-b4-discovery-notes.md [改] 五行终态就地注记（T19）
docs/HANDOFF.md                    [改] 开发流水+状态快照
```

**任务依赖**：T1→T2→{T3,T4,T5,T7,T8,T9,T15 可并行}；T3→T6（cred 列先行）；T9→T10→T11→{T13,T14}；T12 依赖 T9（与 T10/T11 并行）；{T10,T11,T14}→{T16,T17}→T18→T19（收口最后）。可并行组：{T3,T4,T5,T7,T8,T9,T12,T15}、{T16,T17}。

---

### Task 1: 契约 14 知识库 schema 冻结 + 工具面 11→12（批次间接口落地）

**Files:**
- Create: `contracts/14-knowledge-schema.md`（知识库 front-matter schema 全集——本批批次间接口）
- Modify: `contracts/09-cli-surface.md`（工具表 11→12+文末勘误补记）
- Modify: `contracts/README.md`（契约 14 登记+索引行）
- Test: `tests/test_knowledge_contract.py`（新建）

**Interfaces:**
- Consumes: §7.1 布局清单、完备性 K1-K8、VulnClaw 分析 §6.3（47 专题/warstory/experience 取材）。
- Produces: 六类页 front-matter 必填/枚举字段表（后续所有蒸馏任务的产出契约）；知识页 ID 前缀表 `KP-(语源)/STG-(staging)/CP-(技法)/PR-(先例)/EN-(实体)/TG-(目标)/PT-(模式)/RT-(复盘)/BZ-(业务)`；graph.ndjson 行 schema；staging 状态机枚举 `{staged, lint-passed, approved, rejected}`+formal 迁移；四门槛条文；工具面 12 员（tanyin-knowledge 13 子命令枚举）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_knowledge_contract.py（节选骨架——全文按此展开）
# -*- coding: utf-8 -*-
"""批次5 T1：契约 14 知识库 schema+工具面 12 员的结构钉子（test_contract_backfill 同型只读 lint）。"""
import os, re, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
C14 = os.path.join(ROOT, "contracts", "14-knowledge-schema.md")
C09 = os.path.join(ROOT, "contracts", "09-cli-surface.md")
CREADME = os.path.join(ROOT, "contracts", "README.md")

def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

class TestContract14(unittest.TestCase):
    def test_file_and_title(self):
        t = _read(C14)
        self.assertIn("# 契约 14 · 知识库 schema", t)

    def test_six_page_kinds_with_frontmatter_tables(self):
        t = _read(C14)
        for sec in ("技法页（concepts/CP-*.md）", "先例页（precedents/PR-*.md）",
                    "实体页（entities/EN-*.md）", "复盘页（retros/RT-*.md）",
                    "模式页（patterns/PT-*.md）", "业务页（business/BZ-*.md）"):
            self.assertIn(sec, t, "缺节: " + sec)
        # 先例页三元组三字段（client/scope_asset/window）+ applied_patterns（四门槛①载体）
        self.assertIn("client", t); self.assertIn("scope_asset", t)
        self.assertIn("window", t); self.assertIn("applied_patterns", t)

    def test_staging_machine_and_four_gates(self):
        t = _read(C14)
        for w in ("staged", "lint-passed", "approved", "rejected", "formal",
                  "复现≥2", "跨目标有效", "人工审批", "无指纹泄漏"):
            self.assertIn(w, t)

    def test_id_prefix_and_graph_line_schema(self):
        t = _read(C14)
        self.assertIn("KP-", t)  # 前缀表
        self.assertIn('"predicate"', t)  # graph.ndjson 行 schema（示例行内嵌）
        self.assertIn("CLIENT-", t)  # CLIENT-NN 形态约束

    def test_vocab_versionization(self):
        t = _read(C14)
        self.assertIn("vocab_version", t)
        self.assertIn("WSTG-v4.2", t)

    def test_license_discipline(self):
        t = _read(C14)
        self.assertIn("MIT", t)  # 外部语料许可纪律（VulnClaw/BugHunter/Threatswarm/CEP）

class TestToolFace12(unittest.TestCase):
    def test_tool_table_counts_12(self):
        n = len(re.findall(r"^\| \d+ \| tanyin-", _read(C09), re.M))
        self.assertEqual(n, 12, "工具表应 12 行（tanyin-knowledge 增补）")

    def test_erratum_note_present(self):
        t = _read(C09)
        self.assertIn("tanyin-knowledge", t)

    def test_readme_registers_c14(self):
        self.assertIn("14-knowledge-schema", _read(CREADME))
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_knowledge_contract -v`
Expected: FAIL/ERROR（契约 14 不存在、工具表 11 行）。

- [ ] **Step 3: 落契约 14 全文（骨架如下——执行者按此誊全文，字段表逐行给全）**

```markdown
# 契约 14 · 知识库 schema（批次 5 冻结；微版本勘误通道同契约 01-13）

## 1 布局与版本
- 根目录：format_version（当前 kn-v1）/index.md/log.md/overview.md/checklists/
  methodology/ concepts/ precedents/ entities/ targets/ patterns/{core,learned}/
  business/ retros/ cve/ sources/ staging/ client-map.example.tsv graph.ndjson
- K1-K8 类目映射：K1=methodology/（+shared/VOCAB.md）；K2=precedents/+entities/；
  K3=cve/；K4=shared/DENYLIST.md（库外既有数据文件，index.md 登记指针）；
  K5=concepts/；K6=patterns/；K7=business/；K8=retros/。
- 词表版本化：每页 front-matter 必填 vocab_version；合法值集合=shared/VOCAB.md
  的 version 行（当前 WSTG-v4.2）；lint 朗读该行取支持集。
- CLIENT-NN：client 字段一律 ^CLIENT-\d{2,}$；映射表 client-map.tsv 运行时文件
  （真值永不进仓，.gitignore 排除；example 模板进仓）。

## 2 页 front-matter schema（六类；「必」=必填；枚举值列举穷尽）
### 技法页（concepts/CP-*.md，K5）
| 字段 | 必 | 约束 |
|---|---|---|
| id | 必 | ^CP-\d{4}$ |
| kind | 必 | =technique |
| class | 必 | =K5 |
| title | 必 | ≤60 字 |
| vocab_version | 必 | ∈支持集 |
| vuln_class | 必 | 词表键或子类键（细类=wstg-XX:subclass 形）；多值 ; 分隔 |
| applicability | 必 | 适用条件一句话 |
| tool_params | 否 | 工具与参数（BurpPOC/nuclei 映射） |
| cost_hint | 必 | ∈{1,2,3}（请求量级 1=个位/2=十位/3=百位） |
| failure_modes | 否 | 失败模式与转向 |
| judgment | 否 | 判定标准（errorCode 语义分析等） |
| cve_refs | 否 | CVE 编号 ; 分隔；非空则 cve_verified 须逐个覆盖 |
| cve_verified | 条件必 | 列表 [{cve, source∈{NVD,PSIRT,KEV,vendor}, verified_at}] |
| last_verified | 必 | ISO 日期 |
| status | 必 | ∈{core, learned, demoted}（concepts 落 core/learned 皆可） |
| source_id | 必 | ^KP-\d{4}$（SOURCES.tsv 引用闭合） |
### 先例页（precedents/PR-*.md，K2）——三元组页
| 字段 | 必 | 约束 |
|---|---|---|
| id | 必 | ^PR-\d{4}$ |
| kind | 必 | =precedent；class=K2 |
| client | 必 | ^CLIENT-\d{2,}$（三元组字段①） |
| scope_asset | 必 | 脱敏指纹（占位符化域名/组件描述）（三元组字段②） |
| window | 必 | YYYY-MM-DD..YYYY-MM-DD（授权窗口，过期失效）（三元组字段③） |
| triples | 必 | 列表 [主语,谓语,宾语]×N（graph.ndjson 导出行源） |
| outcome | 必 | 结果一句话（finding 计数等） |
| applied_patterns | 否 | PT-id 列表（四门槛①复现计数载体） |
| retro_link | 否 | ^RT-\d{4}$ |
| cost_hint/last_verified/status/source_id | 必 | 同技法页 |
### 实体页（entities/EN-*.md，K2）：id/kind=entity/entity 名（如 favicon-hash:ab12cd）/
  aliases;分隔/occurrences 整数/pattern_stats 文本/vocab_version/status/last_verified
### 复盘页（retros/RT-*.md，K8）：id/kind=retro/client/window + 必答三问
  missed（漏了什么）/trigger_gap（触发器缺哪）/weak_channel（通道弱哪）/
  writeback（回写到哪类）+ last_verified/status
### 模式页（patterns/PT-*.md，K6）：id/kind=pattern/use∈{ok-sample,false-positive}/
  vuln_class/sample_brief + 四门槛晋升字段 status∈{learned,core,demoted}
### 业务页（business/BZ-*.md，K7）：id/kind=business/industry（零售/金融…）/
  checklist_brief/last_verified/status

## 3 graph.ndjson 行 schema（逐行 NDJSON；export 确定性重建）
{"id":"<页id>:t<序号>","subject":"...","predicate":"...","object":"...",
 "source":"PR-0012","class":"K2","created":"<commit 时间戳>"}
- 行序=（source 页 id, t 序号）字典序；行级可合并预留（多 session 锁协议=R6 残余，维持登记）。

## 4 staging 状态机与入库流水线
staged →(lint 全过)→ lint-passed →(approve 人审)→ approved →(commit)→ formal
任意态 →(reject)→ rejected（终态留档 staging/）
- 载体：staging/staging.tsv 十列（staging_id/page_id/class/title/source_id/status/
  checksum/created/approved_by/approved_at）；log.md 追加叙述（ts|event|id|detail）。
- 机器检查（lint，tanyin-knowledge）：front-matter schema 校验/脱敏哨兵（special.py
  泄漏形态单源）/dedup_key（sha256(kind+vuln_class+标题归一)）查重/词表版本/CVE
  核验标记完备。人工审=checklists/review-checklist.md（四门槛之外的质量判断）。
- 四门槛（learned→core 晋升，全部机械可检）：①复现≥2（被 ≥2 先例页 applied_patterns
  引用）②跨目标有效（引用页 client 去重 ≥2）③人工审批（log.md approve 且
  for=promote）④无指纹泄漏（redact 哨兵零命中）。

## 5 语源登记与许可纪律
SOURCES.tsv：source_id/origin∈{cnpen,vulnclaw,bughunter,threatswarm,cep,internal}/
path/sha256/license/note/registered_at。外部语料一律 MIT 核验（LICENSE 文件在场，
VulnClaw=Copyright (c) 2026 UncleC，MIT；BugHunter/Threatswarm/CEP 执行期逐一核验）
——防投毒对称性：外部与自有语料同走一道 staging 审批门（§7.2）。

## 6 ID 前缀表（知识库自有命名空间，不与账本 §4.1 前缀混用；tanyin-knowledge 内部机械分配）
KP 语源 / STG 暂存 / CP 技法 / PR 先例 / EN 实体 / TG 目标 / PT 模式 / RT 复盘 / BZ 业务
——四位零填充字典序=时间序（账本同精神；不经 ledger-next-id）。
```

- [ ] **Step 4: 工具面 11→12 勘误**

`contracts/09-cli-surface.md`：§3 工具表加第 12 行 `| 12 | tanyin-knowledge | 确定性账本运算（同型） | 知识库机械运算：init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map（13 子命令；语义提炼禁入——铁律 7；批量间接口=契约 14） |`；文末「2026-09-24 勘误补记」追加一笔（G-1 10→11 先例同通道：11→12，理由=知识库确定性运算需独立载体，并入 tanyin-ledger 面不可行——44 命令面冻结）。自验命令更新：`grep -cE '^\| [0-9]+ \| tanyin-' → 12`。`contracts/README.md`：契约清单加 14 行+本批勘误索引。

- [ ] **Step 5: 跑绿+全量回归+commit**

Run: `python3 -m unittest tests.test_knowledge_contract -v` → 全 PASS；`python3 -m unittest discover -s tests` 全绿（既有 414 基线零破坏）；`python3 tests/run_golden.py` 零漂移。

```bash
git add contracts/14-knowledge-schema.md contracts/09-cli-surface.md contracts/README.md tests/test_knowledge_contract.py
git commit -m "批次5 T1：契约14 知识库 schema 冻结——六类页 front-matter 全集/三元组/staging 状态机/四门槛/ID 前缀表/graph.ndjson 行 schema/词表版本化/许可纪律+契约09 工具面 11→12（tanyin-knowledge 第12员工具，G-1 先例）；TDD 先红后绿"
```

---

### Task 2: 契约 v3 首批集中清账（doc-only 六笔+遗留三笔）

**Files:**
- Modify: `contracts/04-phases.md`（constants 增两常量+gate-fail 事件词汇补注+P4 duty 攻击链落证注记）
- Modify: `contracts/06-evidence-cards.md`（G-16 结案注记）
- Modify: `contracts/07-submission.md`（G-19 结案注记）
- Modify: `contracts/README.md`（勘误索引六笔）
- Test: `tests/test_knowledge_contract.py`（扩 `TestContractV3Sweep` 类）

**Interfaces:**
- Consumes: T1 的勘误索引行。
- Produces: 契约 v3 待办清单首批清账记录（b4 台账 §六「契约 v3 回注待办」中 G-3/G-7/G-8/G-16/G-19/G-20 六笔 doc 侧落账；G-23/G-24/G-26/G-27/G-28 五笔随 T3/T4/T5/T7 代码任务各自落）。

- [ ] **Step 1: 写失败测试**

```python
class TestContractV3Sweep(unittest.TestCase):
    def test_c04_constants_gain_two(self):
        t = _read(os.path.join(ROOT, "contracts", "04-phases.md"))
        self.assertIn("authz_diff_pair_cap", t)   # R6/G-20
        self.assertIn("restart_rate_minutes", t)  # G-3（批3 T6 常量回注）

    def test_c04_gate_fail_vocab_note(self):
        t = _read(os.path.join(ROOT, "contracts", "04-phases.md"))
        self.assertIn("gate-fail:", t)  # G-7 事件词汇补注

    def test_g16_g19_closed_notes(self):
        self.assertIn("G-16", _read(os.path.join(ROOT, "contracts", "06-evidence-cards.md")))
        self.assertIn("G-19", _read(os.path.join(ROOT, "contracts", "07-submission.md")))

    def test_c09_canary_dryrun_note(self):
        t = _read(C09)
        self.assertIn("只 compile", t)  # G-8 干跑口径注记（deploy 不 probe）
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_contract.TestContractV3Sweep -v` → 全 FAIL。

- [ ] **Step 3: 六笔勘误落盘**

1. 契约 04 constants 表追加：`authz_diff_pair_cap: 24`（R6——代码常量随批5 T5 落，模块常量+--cap 覆盖，G-3 --rate-minutes 落地形态同型）；`restart_rate_minutes: 10`（G-3——批3 T6 模块常量 RESTART_RATE_MINUTES=10 回注）。
2. 契约 04 事件词汇表补注：`gate-fail:<门> assert=<cmd> reason=…`（G-7——PROTOCOL §1.3 已冻结，契约侧补注；非 gate-exit 前缀，core.GATE_EXIT_EVENT 不误计）。
3. 契约 04 P4 duty 注记：攻击链落证步（graph-paths→attack-paths.txt→add-evidence；G-28 裁决 D——duty 详文随 T8 落 phases/P4.md）。
4. 契约 06 文末注记：G-16 结案——EV 卡片↔E-index 同值性执法**维持 replay 侧单点**（cards.check_consistency，498d8c2）；validate --with-cards 不增（遍历交战区 card_path 成本>收益，单点已闭环）。
5. 契约 07 文末注记：G-19 结案——submission 顶层 perspective 字段**不开**（147 字段口径外；视角承载维持 findings[].network_position=same-homemaker 过渡，G-18 注记在册）。
6. 契约 09 文末勘误补记 canary 参数语义注记：干跑口径=egress 只 compile、canary 只 deploy 不 probe（G-8——PROTOCOL §3 已冻结，契约侧补注清账）。

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_knowledge_contract -v` 全 PASS；`python3 -m unittest discover -s tests` 全绿；金样零漂移。

```bash
git add contracts/04-phases.md contracts/06-evidence-cards.md contracts/07-submission.md contracts/09-cli-surface.md contracts/README.md tests/test_knowledge_contract.py
git commit -m "批次5 T2：契约v3 首批集中清账六笔——04 constants 增 authz_diff_pair_cap/restart_rate_minutes（G-20/G-3）+gate-fail 词汇补注（G-7）+P4 攻击链注记（G-28）+G-16/G-19 结案（维持 replay 单点/network_position 承载）+09 canary 干跑口径（G-8）；TDD 先红后绿"
```

---

### Task 3: G-24+G-27 落地——intents.tsv 15→17 双列物理落地（一次重铸）

**Files:**
- Modify: `contracts/01-ledger-schema.md`（§3.3 十七字段表+勘误补记）
- Modify: `contracts/02a-command-signatures-draft.md`（§3 add-intent 参数表+拒收条件勘误）
- Modify: `cli/ledger/schemas.json`（intents 字段数组 17 项——注意与契约 01 同步，schemas.py 加载即生效）
- Modify: `cli/ledger/write_cmds.py`（`_add_intent`：--priority 校验落列；--cred 值落物理列；`_set_intent_status` 追加行携带两列值）
- Modify: `tests/make_fixtures.py` / `tests/make_diff_fixture.py`（若 intents 行构造按字段名遍历则零改；跑重铸）
- Test: `tests/test_intents_columns_b5.py`（新建）；`tests/golden/`（write-add-intent.state 等有意刷新面 --bless）

**Interfaces:**
- Consumes: 契约 01 勘误（fb72cd5 已冻结 priority 公式与语义）；write_cmds.py:345-383 既有 --cred 校验块。
- Produces: `intents.tsv` 17 列（…reason, **priority**, **cred**, schema_version, created）；`add-intent --priority=<0-1 浮点>`（可选）与 `--cred=<CRED-id>`（可选；kind=authz-diff 必填既有）落物理列；T6 trigger-audit 逐对配对消费 `cred` 列；T12 score 产出的值由总控经 --priority 回填。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_intents_columns_b5.py
# -*- coding: utf-8 -*-
"""批次5 T3：intents 15→17 双列（G-24 priority/G-27 cred）物理落地。"""
import os, subprocess, sys, tempfile, unittest, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger.schemas import TABLES  # noqa: E402

INTENT_FIELDS = TABLES["intents.tsv"]

def run(gd, *args):
    return subprocess.run([sys.executable, CLI] + list(args) + ["--goal-dir", gd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

class TestIntents17Columns(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        # 夹具重铸后 intents 行应已 17 列——本测试同时钉死夹具

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_schema_has_17_fields_with_priority_cred(self):
        self.assertEqual(len(INTENT_FIELDS), 17)
        self.assertEqual(INTENT_FIELDS[-4], "priority")
        self.assertEqual(INTENT_FIELDS[-3], "cred")

    def test_fixture_rows_all_17(self):
        p = os.path.join(self.d, "intents.tsv")
        for ln in open(p, encoding="utf-8").read().splitlines():
            self.assertEqual(len(ln.split("\t")), 17, "非 17 列行: " + ln[:60])

    def test_add_intent_priority_cred_land_in_columns(self):
        r = run(self.d, "add-intent", "--title=带凭据意图", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=100;10;1",
                "--priority=0.72", "--cred=CRED-g1-0001",
                "--timestamp=2026-09-24T08:00:00Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l.split("\t") for l in open(os.path.join(self.d, "intents.tsv"), encoding="utf-8").read().splitlines()]
        new = [x for x in rows if x[INTENT_FIELDS.index("title")] == "带凭据意图"][-1]
        self.assertEqual(new[INTENT_FIELDS.index("priority")], "0.72")
        self.assertEqual(new[INTENT_FIELDS.index("cred")], "CRED-g1-0001")

    def test_priority_out_of_range_rejected(self):
        r = run(self.d, "add-intent", "--title=坏分", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--priority=1.5", "--timestamp=2026-09-24T08:00:00Z")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    def test_cred_reference_must_close(self):
        r = run(self.d, "add-intent", "--title=坏引用", "--engine=web-blackbox",
                "--kind=recon", "--origin=entity", "--budget-share=1;1;1",
                "--cred=CRED-g1-9999", "--timestamp=2026-09-24T08:00:00Z")
        self.assertEqual(r.returncode, 1)
        self.assertIn("cred 引用闭合失败", r.stderr)

    def test_status_change_row_carries_columns(self):
        # 事件溯源：set-intent-status 追加行须携带 priority/cred 值
        r = run(self.d, "set-intent-status", "--id=INT-g1-0001", "--status=active",
                "--timestamp=2026-09-24T08:30:00Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l.split("\t") for l in open(os.path.join(self.d, "intents.tsv"), encoding="utf-8").read().splitlines()]
        same = [x for x in rows if x[0] == "INT-g1-0001"]
        self.assertGreaterEqual(len(same), 2)
        self.assertEqual(same[-1][INTENT_FIELDS.index("priority")], same[0][INTENT_FIELDS.index("priority")])
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_intents_columns_b5 -v`
Expected: FAIL（TABLES 仍 15 字段；add-intent 不认 --priority）。

- [ ] **Step 3: 最小实现**

1. `schemas.json`：`"intents.tsv"` 数列改为 17 项（`...`reason`, `priority`, `cred`, `schema_version`, `created`）。
2. `write_cmds._add_intent`：
```python
args = _parse(rest, {"title", "detail", "engine", "kind", "origin", "via", "budget-share",
                     "activation", "cred", "asset", "actions", "timestamp", "phase",
                     "priority"})                      # ← 新增 priority
...
priority = args.get("priority", "")
if priority:
    try:
        if not (0.0 <= float(priority) <= 1.0):
            raise ValueError
    except ValueError:
        raise Reject("priority 须 0-1 浮点: " + priority)
if args.get("cred"):                                    # ← 任意 kind 引用闭合（不分 kind）
    if ctx.latest("creds.tsv", args["cred"]) is None:
        raise Reject("cred 引用闭合失败: " + args["cred"])
# 行构造处（按 schemas 字段序）：priority 列=priority、cred 列=args.get("cred", "")
```
（既有 kind=authz-diff 硬门块 371-383 行**原样保留**——值从 detail 携带改落 cred 列。）
3. `_set_intent_status`：追加行构造按 schemas 字段名遍历时 priority/cred 自动携带（若按位置硬编码则补两位；跑测试定位）。
4. 契约 01 §3.3 表增两行（priority：浮点 0-1 可空=未算分，公式=§8.7 勘误冻结；cred：文本 CRED-id 引用，kind=authz-diff 必填）+勘误补记「15→17 一次重铸（G-24+G-27 合笔，零存量数据期微版本通道）」；契约 02a §3 add-intent 参数表补 --priority/--cred 两行。

- [ ] **Step 4: 夹具/金样重铸（有意刷新声明）**

```bash
python3 tests/make_fixtures.py && python3 tests/make_diff_fixture.py
python3 tests/run_golden.py --bless    # 刷新面=git diff tests/golden/ 逐一核对：
# 预期变更=write-add-intent.state（新列）+write-set-intent-status.state（新列）+
# diff-hash-recheck.norm 等含 intents 行指纹的面；任何无法归因两新列的漂移=回查
```

- [ ] **Step 5: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_intents_columns_b5 -v` 全 PASS；`python3 -m unittest discover -s tests` 全绿；`python3 tests/run_golden.py` 零漂移（重铸后）。

```bash
git add contracts/01-ledger-schema.md contracts/02a-command-signatures-draft.md cli/ledger/schemas.json cli/ledger/write_cmds.py tests/test_intents_columns_b5.py tests/make_fixtures.py tests/make_diff_fixture.py tests/fixtures tests/golden
git commit -m "批次5 T3：intents 15→17 双列物理落地——priority（G-24 算分落列，0-1 校验）+cred（G-27 绑定列，任意 kind 引用闭合+authz-diff 硬门保留）；夹具/金样一次重铸（变更面逐一归因两新列）；契约01/02a 微版本勘误；TDD 先红后绿"
```

---

### Task 4: G-23 落地——set-replay-state --timestamp 必填（墙钟退役）

**Files:**
- Modify: `contracts/02a-command-signatures-draft.md`（§36 签名与参数表勘误）
- Modify: `cli/ledger/check_cmds.py`（`h_set_replay_state` 增 --timestamp 必填；两处 `_now()` 退役）
- Test: `tests/test_replay_timestamp.py`（新建）；`tests/golden/read-set-replay-state.norm`（有意刷新声明）

**Interfaces:**
- Consumes: checkpoint --timestamp 先例（批3 G-10）；`_append_timeline(s, goal_dir, event, actor, phase, revert, ts)` 已有 ts 通道（check_cmds.py:190-199）。
- Produces: `set-replay-state --id=… --state=… --timestamp=ISO8601`（必填，缺=exit 2）；timeline 重放事件与 findings 联动行 created 均取参数时间戳——该命令路径 `grep -n "_now()" cli/ledger/check_cmds.py` 在 set-replay-state 段零命中。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_replay_timestamp.py 核心用例（夹具复制 G-g1 同 T3 模式）
class TestReplayTimestamp(unittest.TestCase):
    def test_missing_timestamp_usage_error(self):
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--timestamp", r.stderr)

    def test_rows_carry_given_timestamp(self):
        TS = "2026-09-24T09:15:00Z"
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stderr)
        tl = open(os.path.join(self.d, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn(TS, tl)   # 事件行时间戳=参数
        fd = open(os.path.join(self.d, "findings.tsv"), encoding="utf-8").read()
        self.assertIn(TS, fd)   # 联动行 created=参数（不再墙钟）

    def test_no_wallclock_in_replay_path(self):
        src = open(os.path.join(HERE, "..", "cli", "ledger", "check_cmds.py"), encoding="utf-8").read()
        i = src.find("def h_set_replay_state")
        j = src.find("\ndef ", i + 1)
        self.assertNotIn("_now()", src[i:j], "set-replay-state 路径残留墙钟")
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_replay_timestamp -v` → FAIL（现状无 --timestamp，行带墙钟）。

- [ ] **Step 3: 最小实现**

```python
def h_set_replay_state(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"id", "state", "note", "timestamp"} \
            or "id" not in args or "state" not in args or "timestamp" not in args:
        raise UsageError("set-replay-state --id=<EV|FD id> --state=<三态> --timestamp=ISO8601 [--note=<附注>]")
    ts = args["timestamp"]
    # _append_timeline(..., ts=ts)；findings 联动行 created=ts（原 _now() 两处替换）
```
契约 02a §36：签名行与参数表加 `--timestamp|文本(ISO8601)|是`；文末勘误补记一笔（G-23 裁决 E；批3 Minor-5 同族收口）。

- [ ] **Step 4: 金样有意刷新+跑绿**

`python3 tests/run_golden.py` → read-set-replay-state.norm 漂移（VALS 已有 --timestamp=TS 复用）→ `--bless` 刷新并 commit 注明「时间戳从墙钟转参数（确定性增强）」。

- [ ] **Step 5: 全量+commit**

```bash
git add contracts/02a-command-signatures-draft.md cli/ledger/check_cmds.py tests/test_replay_timestamp.py tests/golden/read-set-replay-state.norm
git commit -m "批次5 T4：set-replay-state 增 --timestamp 必填（G-23）——命令路径 _now() 两处退役（timeline 事件+findings 联动行 created）；金样 read-set-replay-state 有意刷新；契约02a §36 勘误；TDD 先红后绿"
```

---

### Task 5: R6 落地——AUTHZ_DIFF_PAIR_CAP 代码常量+add-intent 硬门拒收

**Files:**
- Modify: `contracts/02a-command-signatures-draft.md`（§3 add-intent 拒收条件勘误——cap 拒收与 --cap 覆盖）
- Modify: `cli/ledger/write_cmds.py`（常量+authz-diff 分支计数拒收）
- Modify: `engines/web-blackbox/phases/differential.md` + `phases/P3.md`（护栏行补「机检=add-intent 写前拒收」注记——文档常量双载转单源引用）
- Test: `tests/test_authz_cap.py`（新建）

**Interfaces:**
- Consumes: T3 落地的 cred 列（同端点计数按 --asset 维度，不依赖 cred 列）。
- Produces: `write_cmds.AUTHZ_DIFF_PAIR_CAP == 24`（模块常量，测试锚定）；`add-intent --cap=N`（可选覆盖，evals 可重放）；拒收消息含当前计数与 cap 值。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_authz_cap.py 核心用例（夹具内预铸 24 条同资产 authz-diff intents——
# 铸造用循环调 add-intent --kind=authz-diff --cred=CRED-g1-0001 --actions=read --asset=AST-g1-0002）
class TestAuthzCap(unittest.TestCase):
    def test_constant_value_anchored(self):
        from ledger import write_cmds
        self.assertEqual(write_cmds.AUTHZ_DIFF_PAIR_CAP, 24)

    def test_25th_same_endpoint_rejected(self):
        # 预铸 24 条后第 25 条 → exit 1 + REJECT 含 "AUTHZ_DIFF_PAIR_CAP" 与计数
        r = run(self.d, "add-intent", "--title=第25条", ..., "--kind=authz-diff",
                "--cred=CRED-g1-0001", "--actions=read", "--asset=AST-g1-0002", ...)
        self.assertEqual(r.returncode, 1)
        self.assertIn("cap=24", r.stderr)

    def test_cap_override_channel(self):
        # --cap=3 时第 4 条拒（evals 重放通道）
        ...

    def test_other_endpoint_not_counted(self):
        # 同 cap 下不同 --asset 的 authz-diff 不受牵连（per-endpoint 语义）
        ...
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_authz_cap -v` → FAIL（无常量无拒收）。

- [ ] **Step 3: 最小实现**（write_cmds.py authz-diff 分支内、permitted_actions 校验之后）

```python
AUTHZ_DIFF_PAIR_CAP = 24   # §6.6 护栏（契约 04 constants；R6 机检——双载文档改单源引用）

_ACTIVE = {"candidate", "pending", "active"}
same = sum(1 for it in ctx.rows("intents.tsv")
           if ctx.val("intents.tsv", it, "kind") == "authz-diff"
           and ctx.val("intents.tsv", it, "status") in _ACTIVE
           and ctx.val("intents.tsv", it, "title") == args["title"]  # ← 以 title 承载端点
           )
```
（**注**：intents 无 asset 列——端点归属以既有 dedup 通道承载：`--asset` 值并入 dedup_key 语义（`(asset or "-")+"+"+kind+"+"+title` 已在 384 行）。cap 计数键=`asset+kind` 二元组：`same = sum(... and (ctx.val(...,"dedup_key") or "").startswith((asset or "-") + "+authz-diff+"))`。测试按此构造。cap=`int(args.get("cap", AUTHZ_DIFF_PAIR_CAP))`（1-1000 校验）；`same >= cap` → `raise Reject("authz-diff 单端点对数超限 AUTHZ_DIFF_PAIR_CAP：count=%d cap=%d（--cap 覆盖通道=evals）" % (same, cap))`。）

- [ ] **Step 4: 文档单源化+跑绿**

differential.md 与 P3.md 护栏行改「上限 24=AUTHZ_DIFF_PAIR_CAP（cli/ledger/write_cmds.py 代码常量，add-intent 写前拒收机检）」——文档双载降为指针。Run: `python3 -m unittest tests.test_authz_cap -v` 全 PASS；全量+金样零漂移（拒收路径不进金样正面）。

- [ ] **Step 5: commit**

```bash
git add contracts/02a-command-signatures-draft.md cli/ledger/write_cmds.py engines/web-blackbox/phases/differential.md phases/P3.md tests/test_authz_cap.py
git commit -m "批次5 T5：AUTHZ_DIFF_PAIR_CAP=24 落代码常量+add-intent 同端点计数拒收（R6/G-20 机检硬门；--cap 覆盖通道 G-3 同型）；differential.md/P3.md 双载文档转单源指针；契约02a 拒收条件勘误；TDD 先红后绿"
```

---

### Task 6: G-27 后半——trigger-audit ② 逐对配对 + ④ 高危即时横向机检（triggers-v2 承诺兑现）

**Files:**
- Modify: `cli/ledger/phases_engine.py`（`trigger_audit` ②重写+④新增）
- Modify: `phases/TRIGGERS.md`（②行与高危行「消费检查」列文字升级；版本不 bump——目录行集合与语义零变，机检落地是执法面）
- Modify: `phases/PROTOCOL.md`（§5 检查面 3→5 注记）
- Test: `tests/test_trigger_audit_v2.py`（新建）

**Interfaces:**
- Consumes: T3 的 intents.cred 物理列（②逐对依据）；TRIGGERS.md triggers-v2 高危行既有文本「机检留批次 5 与 G-24 同批 evals」。
- Produces: `trigger_audit` 返回 (fails, stats) 五检查：① asset-added（既有）② **cred-obtained 逐对**（每 CRED：`kind=authz-diff 且 cred=<cid>` 的 intent 或延后 fact）③ scope-amended（既有）④ **高危横向**（每个 impact∈{高,high,critical} 的 add-finding 落账后：存在引用该 FD-id 的横向 intent（detail/title 含 FD-id 且 kind∈{matrix-test,deep-dive}）或 `target=lateral:<FD-id>` 披露 fact）⑤ 目录版本一致（既有）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_trigger_audit_v2.py 核心用例（夹具基 G-g1 复制后用 CLI 命令铸造场景）
class TestTriggerAuditV2(unittest.TestCase):
    def test_pairing_per_cred_not_global(self):
        # 两个 session CRED（CRED-A/CRED-B）：只有 CRED-A 有 authz-diff intent（cred=CRED-A）
        # 旧全局口径 PASS、新逐对口径应 FAIL 且指名 CRED-B
        fails, stats = trigger_audit(self.d)
        self.assertTrue(any("CRED" in f and "逐对" in f for f in fails))

    def test_pairing_pass_when_each_cred_covered(self):
        # 每个 CRED 各有 cred=<cid> 的 authz-diff intent → ② PASS
        fails, _ = trigger_audit(self.d)
        self.assertFalse(any("cred-obtained" in f for f in fails))

    def test_highrisk_finding_needs_lateral_intent_or_disclosure(self):
        # 铸 impact=高 finding：无横向 intent 无披露 fact → ④ FAIL 指名 FD-id
        fails, _ = trigger_audit(self.d)
        self.assertTrue(any("横向" in f for f in fails))
        # 补 target=lateral:<FD-id> 的 fact → PASS
        ...

    def test_low_impact_finding_not_audited(self):
        # impact=中 → ④ 不计数不 FAIL
        ...
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_trigger_audit_v2 -v` → FAIL（②仍全局、④不存在）。

- [ ] **Step 3: 最小实现**（phases_engine.py:633-641 替换+新块）

```python
# ② cred-obtained（kind=session）→ 逐对：authz-diff 且 cred=<cid> 的候选，或延后 fact
for r in s.rows("creds.tsv"):
    if _cell("creds.tsv", r, "kind") != "session":
        continue
    total += 1
    cid = r[core.TABLES["creds.tsv"].index("id")]
    paired = any(_cell("intents.tsv", it, "kind") == "authz-diff"
                 and _cell("intents.tsv", it, "cred") == cid
                 for it in s.rows("intents.tsv"))
    deferred = any(_cell("facts.tsv", f, "target") == "authz-diff:" + cid
                   for f in s.rows("facts.tsv"))
    if paired or deferred:
        closed += 1
    else:
        fails.append("②cred-obtained %s 无逐对 authz-diff 候选（cred=%s）/延后 fact（G-27）" % (cid, cid))

# ④ 高危 finding 即时横向（triggers-v2 承诺兑现）：impact∈{高,high,critical} 落账后
#   存在引用该 FD-id 的横向 intent 或 target=lateral:<FD-id> 披露 fact
_HAZ = {"高", "high", "critical"}
for r in s.rows("findings.tsv"):
    if _cell("findings.tsv", r, "impact") not in _HAZ:
        continue
    fid = r[0]
    total += 1
    lateral = any(_cell("intents.tsv", it, "kind") in ("matrix-test", "deep-dive")
                  and fid in (_cell("intents.tsv", it, "title") + _cell("intents.tsv", it, "detail"))
                  for it in s.rows("intents.tsv"))
    disclosed = any(_cell("facts.tsv", f, "target") == "lateral:" + fid
                    for f in s.rows("facts.tsv"))
    if lateral or disclosed:
        closed += 1
    else:
        fails.append("④高危 finding %s 无横向 intent/披露 fact（triggers-v2 即时横向）" % fid)
```
TRIGGERS.md ②行消费检查列改「逐对：authz-diff 且 cred=&lt;CRED-id&gt; 的 intent 或延后 fact（G-27 列落地，批5 兑现）」；高危行「机检留批次 5」改「④机检已兑现（trigger-audit，批5 T6）」。PROTOCOL §5 注记检查面 3→5（版本史补一行，目录版本 triggers-v2 不 bump）。

- [ ] **Step 3.5: 高危披露 fact 通道登记**

④的披露载体 `target=lateral:<FD-id>` 为 facts.target 新语义值（非枚举列、自由文本——零 schema 变更）；P3.md 高危回边行补一句「横向 intent 引用来源 FD-id（title/detail 内联）；轮内不横向=落 target=lateral:&lt;FD-id&gt; 披露 fact」。

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_trigger_audit_v2 tests.test_skill_resident -v`（TRIGGERS 断言不破——版本行未动）；`python3 -m unittest discover -s tests` 全绿；金样零漂移（trigger-audit 无金样面）。

```bash
git add cli/ledger/phases_engine.py phases/TRIGGERS.md phases/PROTOCOL.md phases/P3.md tests/test_trigger_audit_v2.py
git commit -m "批次5 T6：trigger-audit ②逐对配对（G-27 cred 列消费——每 CRED 须 authz-diff intent 或延后 fact）+④高危即时横向机检（triggers-v2 承诺兑现：横向 intent 引用 FD-id 或 lateral: 披露 fact）；PROTOCOL §5 检查面 3→5；TDD 先红后绿"
```

---

### Task 7: G-28 前半——converge-check 可达未测格结构性停机判据

**Files:**
- Modify: `cli/ledger/graph_cmds.py`（抽公共函数 `reachable_gap_cells(s)`——horizon 与 converge 单源）
- Modify: `cli/ledger/query_cmds.py`（converge-check 增 `#reachable-gaps=`/`#unreachable-gaps=` 输出与判据）
- Modify: `contracts/02a-command-signatures-draft.md`（终审补全节 converge 四条件补记结构性通道）
- Test: `tests/test_converge_reachable.py`（新建）

**Interfaces:**
- Consumes: `graph_cmds._build/_scope_root_targets/_undirected`（71d3b7c 既有）；latest_matrix（query_cmds 既有）。
- Produces: `graph_cmds.reachable_gap_cells(s) -> (reach_set, reachable_gaps, unreachable_gaps)`（gaps=(surface, vuln_class) 对，state=="" 空格；起点=scope-root 资产集）；converge-check 输出增两行计数；判据=「可达空格=0 且 不可达空格全部经 `unreachable:` 前缀置态（置态格天然非空格，故等价=可达与不可达空格双清零）」；reachable_gaps==0 而 unreachable_gaps>0 时输出 `running（structural: N 格不可达——unreachable: 通道可清，matrix-set --state=- --reason=unreachable:<AST 依据>）`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_converge_reachable.py 核心用例（G-g1 复制后命令铸造：
#   add-asset 一个隔离资产（无 parent 边——不可达）+matrix-set 其子矩阵行留空格）
class TestConvergeReachable(unittest.TestCase):
    def test_counts_split_output(self):
        r = run(self.d, "converge-check")
        self.assertIn("#reachable-gaps=", r.stdout)
        self.assertIn("#unreachable-gaps=", r.stdout)

    def test_structural_channel_closes_to_converged(self):
        # 可达面全置态 + 不可达空格 N>0 → running+structural 提示
        r = run(self.d, "converge-check")
        self.assertIn("structural", r.stdout)
        # 走 unreachable: 通道置态后 → converged（matrix-set 首次归类放行，批4 裁决 A）
        run(self.d, "matrix-set", "--attack-surface=island-host", "--vuln-class=wstg-inpv",
            "--state=-", "--reason=unreachable:AST-g1-0099", "--timestamp=...")
        r2 = run(self.d, "converge-check")
        self.assertTrue(r2.stdout.startswith("converged"), r2.stdout)

    def test_reachable_gap_blocks_converged(self):
        # 可达资产上留空格 → 不得 converged（即使不可达全清）
        r = run(self.d, "converge-check")
        self.assertNotEqual(r.stdout.splitlines()[0].strip(), "converged")
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_converge_reachable -v` → FAIL（无计数行无判据）。

- [ ] **Step 3: 最小实现**

graph_cmds.py 抽函数（h_graph_horizon 改调它，行为零变——金样 graph-graph-horizon.norm 验证）：

```python
def reachable_gap_cells(s):
    """scope-root 资产集出发的可达集 × 矩阵空格 join（graph-horizon/converge 单源）。"""
    nodes, adj = _build(s)
    roots = _scope_root_targets(s, nodes)   # 既有：in_scope root-domain 资产 id 集
    reach, frontier = set(roots), list(roots)
    while frontier:
        nxt = []
        for u in frontier:
            for _l, v in adj[u]:
                if v not in reach:
                    reach.add(v); nxt.append(v)
        frontier = sorted(nxt)
    ast_vals = {_cell(r, "assets.tsv", "value") for r in s.rows("assets.tsv") if r[0] in reach}
    gaps = [(_cell(r, "matrix.tsv", "attack_surface"), _cell(r, "matrix.tsv", "vuln_class"))
            for r in latest_matrix(s).values()
            if _cell(r, "matrix.tsv", "state").strip() == ""]
    reach_gaps = sorted(g for g in gaps if g[0] in ast_vals)
    unreach_gaps = sorted(g for g in gaps if g[0] not in ast_vals)
    return reach, reach_gaps, unreach_gaps
```

query_cmds.converge-check 判据段：空格清零条件改 `not reach_gaps and not unreach_gaps`（置态 unreachable 格已非空格；其余四条件不动）；输出增 `#reachable-gaps=%d\n#unreachable-gaps=%d`；`not reach_gaps and unreach_gaps` 时 verdict 行附 structural 提示（见 Interfaces）。契约 02a 终审补全节 converge 行补记「批5 G-28：可达性维度=graph_cmds.reachable_gap_cells 单源；结构性停机=不可达空格经 unreachable: 前缀置态（-）后计入清零——图依据显式置格，非静默豁免」。

- [ ] **Step 4: 跑绿+金样核对+commit**

Run: `python3 -m unittest tests.test_converge_reachable tests.test_graph_cmds -v` 全 PASS；`python3 tests/run_golden.py`——graph-graph-horizon.norm 零漂移（抽函数行为不变）；read-converge-check.norm 若因新增输出行漂移 → --bless 有意刷新（commit 注明「新增两行计数=行为增强非破坏」）。全量单测绿。

```bash
git add cli/ledger/graph_cmds.py cli/ledger/query_cmds.py contracts/02a-command-signatures-draft.md tests/test_converge_reachable.py tests/golden/read-converge-check.norm
git commit -m "批次5 T7：converge-check 增可达性维度——graph_cmds.reachable_gap_cells 单源抽取（horizon 行为零变）+#reachable/unreachable-gaps 计数+结构性停机判据（不可达空格走 unreachable: 置格通道=G-28 前半）；金样 read-converge-check 有意刷新（两行计数）；TDD 先红后绿"
```

---

### Task 8: G-28 后半——攻击路径进 EV（P4 攻击链落证步）

**Files:**
- Modify: `phases/P4.md`（duty 增「攻击链落证」步——命令序列全文）
- Test: `tests/test_attack_paths_ev.py`（新建，集成走查）

**Interfaces:**
- Consumes: `graph-paths --from=<id> --to=scope-root`（既有，文本输出）；`ledger-add-evidence`（既有写命令）；`cli/ledger/norm.py artifact_hashes`（双指纹单源）。
- Produces: P4 duty 第 6 步命令序列（总控执行）：graph-paths 输出存 `evidence/attack-paths.txt`（只增不覆盖——重跑存 `-r2` 后缀）→ `add-evidence --source-type=capture --artifact-path=evidence/attack-paths.txt --repro-command="<graph-paths 原文>" --raw-excerpt=<首路径行>`（content-hash 双轨由 norm.artifact_hashes 计算——总控算哈希=命令算，LLM 不手算，经临时文件传参）。

- [ ] **Step 1: 写失败测试**（先测 duty 文本+集成走查双钉）

```python
# tests/test_attack_paths_ev.py
class TestAttackPathsEv(unittest.TestCase):
    def test_p4_duty_has_step(self):
        t = open(os.path.join(HERE, "..", "phases", "P4.md"), encoding="utf-8").read()
        self.assertIn("攻击链落证", t)
        self.assertIn("graph-paths", t)
        self.assertIn("attack-paths.txt", t)

    def test_end_to_end_walk_on_fixture(self):
        # diff-authz 夹具副本上：graph-paths → 落盘 artifact → add-evidence → validate PASS
        d = self.d  # tests/fixtures/diff-authz 副本
        r = run_ledger(d, "graph-paths", "--from=AST-g1-0001", "--to=scope-root")
        self.assertEqual(r.returncode, 0, r.stderr)
        art = os.path.join(d, "evidence", "attack-paths.txt")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(r.stdout)
        sys.path.insert(0, os.path.join(HERE, "..", "cli"))
        from ledger.norm import artifact_hashes
        raw, norm = artifact_hashes(r.stdout)
        r2 = run_ledger(d, "add-evidence", "--title=攻击链落证",
                        "--source-type=capture", "--observed-at=2026-09-24T10:00:00Z",
                        "--network-position=intranet",
                        "--repro-command=cli/tanyin-ledger graph-paths --from=AST-g1-0001 --to=scope-root",
                        "--repro-kind=single",
                        "--content-hash-raw=" + raw, "--content-hash-norm=" + norm,
                        "--artifact-path=evidence/attack-paths.txt",
                        "--raw-excerpt=" + r.stdout.splitlines()[1][:60] if r.stdout.count("\n") > 1 else "--raw-excerpt=none",
                        "--card-path=evidence/EV-attack-paths.md",
                        "--timestamp=2026-09-24T10:00:00Z")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(run_ledger(d, "validate").returncode, 0)
        self.assertEqual(run_ledger(d, "verify-chain").returncode, 0)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_attack_paths_ev -v` → FAIL（P4.md 无步骤）。

- [ ] **Step 3: 落 P4.md duty 步**

```markdown
6. 攻击链落证（G-28）：tanyin-ledger graph-paths --from=<入口资产> --to=scope-root
   [--max-hops=6] → stdout 追加存 evidence/attack-paths.txt（重跑 -r2 后缀，只增不覆盖）
   → 哈希经 cli/ledger/norm.py artifact_hashes 计算（参数经临时文件传入）
   → ledger-add-evidence --source-type=capture --artifact-path=evidence/attack-paths.txt
     --repro-command="<graph-paths 命令原文>"（只读命令天然第三方可复现）
     --raw-excerpt=<首条路径行>。attack 链从「图推导」升格为「可审计证据」。
```

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_attack_paths_ev -v` 全 PASS；`python3 -m unittest discover -s tests` 全绿；金样零漂移（graph-paths 既有面未动）。

```bash
git add phases/P4.md tests/test_attack_paths_ev.py
git commit -m "批次5 T8：P4 攻击链落证步——graph-paths 输出经 norm 双指纹落 EV（artifact+repro_command=只读命令可复现，G-28 后半：图推导升格证据链）；集成走查测试钉死；TDD 先红后绿"
```

---

### Task 9: tanyin-knowledge 骨架 + init + 种子库落位（R7）

**Files:**
- Create: `cli/tanyin-knowledge` / `cli/tanyin-knowledge.cmd`（第 12 工具入口）
- Create: `cli/ledger/knowledge.py`（单源模块——本任务先落骨架：FORMAT_VERSION/目录集/load_ctx/init/只读纪律；后续任务填充子命令）
- Create: `knowledge/`（仓库种子库——init 产物+checklists；本任务落骨架，T16/T17 填内容）
- Modify: `.gitignore`（增 `knowledge/client-map.tsv`——真值映射永不进仓）
- Test: `tests/test_knowledge_init.py`（新建）

**Interfaces:**
- Consumes: 契约 14（T1 冻结）；`cli/ledger/core.py ensure_utf8_stdio`（控制台纪律）。
- Produces: `knowledge.FORMAT_VERSION="kn-v1"`；`knowledge.DIRS` 目录清单；`load_ctx(kdir)`（校验 format_version，不匹配=KnowledgeError exit 2 提示迁移）；`init(kdir)`（幂等：已初始化=PASS no-op）；`READONLY_ROOTS={仓库 knowledge/}`（写子命令守卫）；`cli/tanyin-knowledge <sub> --knowledge-dir D` 入口骨架（SUBCOMMANDS 注册表+用法输出 13 子命令枚举）；种子库目录骨架+`checklists/review-checklist.md` 人审 checklist 全文。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_knowledge_init.py
KN = os.path.join(HERE, "..", "cli", "tanyin-knowledge")
SEED = os.path.join(HERE, "..", "knowledge")

def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

class TestKnowledgeInit(unittest.TestCase):
    def test_init_creates_skeleton_idempotent(self):
        d = tempfile.mkdtemp()
        self.assertEqual(kn("init", "--knowledge-dir=" + d).returncode, 0)
        for sub in ("concepts", "precedents", "entities", "targets", "patterns/core",
                    "patterns/learned", "business", "retros", "methodology", "cve",
                    "sources", "staging/pages", "checklists"):
            self.assertTrue(os.path.isdir(os.path.join(d, sub)), "缺目录 " + sub)
        for f in ("format_version", "index.md", "log.md", "overview.md"):
            self.assertTrue(os.path.isfile(os.path.join(d, f)))
        self.assertEqual(kn("init", "--knowledge-dir=" + d).returncode, 0)  # 幂等

    def test_format_version_gate(self):
        d = tempfile.mkdtemp()
        kn("init", "--knowledge-dir=" + d)
        open(os.path.join(d, "format_version"), "w", encoding="utf-8").write("kn-v0")
        r = kn("lint", "--knowledge-dir=" + d)   # 任意后续子命令
        self.assertEqual(r.returncode, 2)
        self.assertIn("迁移", r.stderr)

    def test_seed_repo_knowledge_present(self):
        self.assertTrue(os.path.isfile(os.path.join(SEED, "format_version")))
        self.assertTrue(os.path.isfile(os.path.join(SEED, "checklists", "review-checklist.md")))

    def test_readonly_guard_on_seed(self):
        # 种子库（仓库根 knowledge/）只读纪律：写子命令 REJECT
        r = kn("source-register", "--knowledge-dir=" + SEED,
               "--path=/etc/hosts", "--origin=internal", "--license=MIT")
        self.assertEqual(r.returncode, 1)
        self.assertIn("种子库只读", r.stderr)

    def test_gitignore_excludes_client_map(self):
        gi = open(os.path.join(HERE, "..", ".gitignore"), encoding="utf-8").read()
        self.assertIn("knowledge/client-map.tsv", gi)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_init -v` → ERROR/FAIL（入口不存在）。

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/knowledge.py（骨架；子命令随 T10-T15 填充）
# -*- coding: utf-8 -*-
"""知识库机械运算单源（批次 5；铁律 7——语义提炼禁入，本模块只做：
schema 校验/脱敏哨兵/去重哈希/确定性导出/三元组匹配/基线查表/CPE 离线匹配）。"""
import os

FORMAT_VERSION = "kn-v1"
DIRS = ("concepts", "precedents", "entities", "targets", "patterns/core",
        "patterns/learned", "business", "retros", "methodology", "cve",
        "sources", "staging/pages", "checklists")
FILES = {"format_version": FORMAT_VERSION + "\n"}

class KnowledgeError(Exception):
    """exit 2：结构/版本/环境问题。"""

class Reject(Exception):
    """exit 1：门禁失败（种子库只读/校验不过/状态机非法迁移）。"""

def repo_seed_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge"))

def load_ctx(kdir):
    if not os.path.isdir(kdir):
        raise KnowledgeError("knowledge 目录不存在: " + kdir)
    fv = os.path.join(kdir, "format_version")
    if not os.path.isfile(fv) or open(fv, encoding="utf-8").read().strip() != FORMAT_VERSION:
        raise KnowledgeError("format_version 不匹配（期望 %s）——拒绝操作，先跑迁移/重铸" % FORMAT_VERSION)
    return kdir

def guard_writable(kdir):
    seed = repo_seed_root()
    if os.path.abspath(kdir) == seed:
        raise Reject("种子库只读（仓库 knowledge/ = 发行内容；写操作请在运行时库执行）: " + kdir)

def init(kdir):
    os.makedirs(kdir, exist_ok=True)
    for sub in DIRS:
        os.makedirs(os.path.join(kdir, sub), exist_ok=True)
    for name, content in FILES.items():
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
    for name in ("index.md", "log.md", "overview.md"):
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s\n" % name.removesuffix(".md") + "\n（init 生成；commit 时重生成 index/overview）\n")
    return 0
```

`cli/tanyin-knowledge`：入口骨架照 `cli/tanyin-redact` 先例（shebang+sys.path+ensure_utf8_stdio+SUBCOMMANDS 字典+用法输出 13 子命令枚举行）；`.cmd` 包装内容 `@echo off\npy -3 "%~dp0tanyin-knowledge" %*`（先例照抄）。种子库=`python3 cli/tanyin-knowledge init --knowledge-dir knowledge` 产物+`checklists/review-checklist.md`（人审 checklist 全文——含四门槛之外质量判断清单：事实性/可执行性/与词表对齐/脱敏抽查三处原文/许可注记核对；VulnClaw experience 人审门模式注记节）。

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_knowledge_init -v` 全 PASS；`python3 -m unittest discover -s tests` 全绿；金样零漂移。

```bash
git add cli/tanyin-knowledge cli/tanyin-knowledge.cmd cli/ledger/knowledge.py knowledge/ .gitignore tests/test_knowledge_init.py
git commit -m "批次5 T9：tanyin-knowledge 第12员工具骨架——knowledge.py 单源（FORMAT_VERSION kn-v1/13 目录/种子库只读纪律）+init 幂等+仓库种子库落位（checklists 人审 checklist 全文）+client-map.tsv gitignore 排除；TDD 先红后绿"
```

---

### Task 10: 语源登记 + staging 状态机 + lint 机器检查四件

**Files:**
- Modify: `cli/ledger/knowledge.py`（source-register/stage 登记/lint 四件套）
- Modify: `cli/ledger/special.py`（泄漏形态扫描抽纯文本 API `scan_text(text)->[(name,line_no)]`——scan_text_file 改调它，行为零变单源化）
- Test: `tests/test_knowledge_staging.py`（新建）；`tests/fixtures/knowledge/`（mini 库夹具——含脏页/重复页/缺 CVE 核验页/过期词表页样例，init 后手工放置）

**Interfaces:**
- Consumes: T9 骨架；`phases_engine.parse_yaml`（front-matter 解析，cards.py 先例）；`special.PLAIN_PATTERNS`（泄漏形态表）。
- Produces:
  - `source_register(kdir, path, origin, license, note) -> source_id`（KP-#### 递增；sha256 流式；SOURCES.tsv 追加；origin∈{cnpen,vulnclaw,bughunter,threatswarm,cep,internal}）
  - `lint(kdir)`：遍历 staging/pages+六类正式区，检查：①front-matter schema（契约 14 六类必填/枚举——PAGE_SCHEMAS 内置表）②脱敏哨兵（special.scan_text 对正文+front-matter 值扫描——真域名/IP/凭据形态零容忍，FAIL）③dedup_key 查重（`sha256(kind+vuln_class+标题归一)`——norm 同源窄函数 `norm_title()`：去空白/全半角/小写）④词表版本（vocab_version∈shared/VOCAB.md version 行支持集）⑤CVE 标记（cve_refs 每项在 cve_verified 有行）；输出 `PASS n=M` 或 `FAIL`+逐页缺口清单；lint 过的 staging 页状态 staged→lint-passed（写 staging.tsv）
  - `staging.tsv` 十列状态机（R8）；staging 页 front-matter 额外字段 `staging_status`（=staged）
- 语义边界：**蒸馏写页=LLM/执行者职责**（staging/pages/ 下手工/子代理产出），CLI 只校验。

- [ ] **Step 1: 写失败测试**（夹具先行——mini 库四样例页）

```python
# tests/test_knowledge_staging.py 核心用例（fixtures/knowledge/ 为 init 产物+四样例页：
#   staging/pages/STG-0001.md 合法技法页（vuln_class=wstg-inpv:inj.sql，source_id 先经 source-register 铸）
#   STG-0002.md 脏页（正文含真域名 shop.example）
#   STG-0003.md 重复页（与 STG-0001 同 kind+vuln_class+标题——仅大小写/空格差）
#   STG-0004.md 缺 CVE 核验页（cve_refs=CVE-2021-44228 无 cve_verified）
#   STG-0005.md 词表版本错页（vocab_version=WSTG-v3.0））
class TestStagingLint(unittest.TestCase):
    def test_source_register_sha_and_id(self):
        d = self.copy_fixture()   # init 过的干净副本
        r = kn("source-register", "--knowledge-dir=" + d,
               "--path=tests/fixtures/knowledge/raw-sample.txt",
               "--origin=cnpen", "--license=proprietary", "--note=CNPEN 复盘")
        self.assertEqual(r.returncode, 0)
        self.assertIn("KP-0001", r.stdout)
        row = open(os.path.join(d, "sources", "SOURCES.tsv"), encoding="utf-8").read()
        self.assertIn("cnpen", row); self.assertIn(64 * "a"[:8], row[:200])  # sha256 前缀在场

    def test_lint_flags_each_failure_class(self):
        d = self.copy_fixture()
        r = kn("lint", "--knowledge-dir=" + d)
        self.assertEqual(r.returncode, 1)
        for kw in ("STG-0002", "泄漏形态", "STG-0003", "dedup", "STG-0004", "cve_verified",
                   "STG-0005", "vocab_version"):
            self.assertIn(kw, r.stdout)

    def test_clean_page_passes_and_transitions(self):
        d = self.copy_fixture()
        # 只留 STG-0001（其余样例移走）→ lint PASS 且 staging.tsv 状态转 lint-passed
        ...
        r = kn("lint", "--knowledge-dir=" + d)
        self.assertEqual(r.returncode, 0, r.stdout)
        st = open(os.path.join(d, "staging", "staging.tsv"), encoding="utf-8").read()
        self.assertIn("lint-passed", st)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_staging -v` → FAIL（子命令不存在）。

- [ ] **Step 3: 最小实现**（knowledge.py 增量；要点）

```python
import hashlib
from .phases_engine import parse_yaml
from . import special

PAGE_SCHEMAS = {  # 契约 14 §2 机器表（必填字段+枚举）；kind→(目录, 必填集, 枚举dict)
    "technique": ("concepts", {"id","kind","class","title","vocab_version","vuln_class",
                   "applicability","cost_hint","last_verified","status","source_id"},
                  {"status": {"core","learned","demoted"}, "cost_hint": {"1","2","3"}}),
    "precedent": ("precedents", {"id","kind","class","title","client","scope_asset","window",
                   "triples","outcome","cost_hint","last_verified","status","source_id"}, {...}),
    ...  # entity/retro/pattern/business 四类同构
}

def norm_title(t):        # R10：去空白/全角→半角/小写（norm.py 语义同源窄函数）
    ...

def dedup_key(kind, vuln_class, title):
    return hashlib.sha256((kind + "\x00" + vuln_class + "\x00" + norm_title(title))
                          .encode("utf-8")).hexdigest()

def _vocab_supported():
    for ln in open(os.path.join(repo_seed_root(), "..", "shared", "VOCAB.md"), encoding="utf-8"):
        if ln.startswith("version:"):
            return {ln.split(":", 1)[1].strip()}

def lint_page(kdir, path, fm, body):
    problems = []
    kind = fm.get("kind")
    if kind not in PAGE_SCHEMAS:
        return ["kind 不在六类: %r" % kind]
    _, required, enums = PAGE_SCHEMAS[kind]
    for f in required:
        if f not in fm or fm[f] in ("", [], None):
            problems.append("缺必填字段 %s" % f)
    for f, allowed in enums.items():
        if f in fm and str(fm[f]) not in allowed:
            problems.append("%s 枚举越界: %r" % (f, fm[f]))
    # ② 脱敏哨兵（special 单源）
    for name, line in special.scan_text(fm_text + "\n" + body):
        problems.append("泄漏形态[%s] 第 %d 行" % (name, line))
    # ④ 词表版本
    if fm.get("vocab_version") not in _vocab_supported():
        problems.append("vocab_version 不在支持集: %r" % fm.get("vocab_version"))
    # ⑤ CVE 核验标记
    refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c]
    verified = {v.get("cve") for v in fm.get("cve_verified", []) or []
                if isinstance(v, dict)}
    for c in refs:
        if c not in verified:
            problems.append("cve_refs 未核验: %s（缺 cve_verified 行）" % c)
    return problems
```
（dedup 查重在 lint 汇总层做：同 dedup_key 的页组>1 → 全组 FAIL 附键值。staging.tsv 状态迁移：lint 全过页 staged→lint-passed；log.md 追加 `ts|lint|<page_id>|pass|fail=<n>`。）

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_knowledge_staging tests.test_redact_injection -v`（special 重构行为零变——既有注入拦截 36/36 用例回归）全 PASS；全量绿；金样零漂移。

```bash
git add cli/ledger/knowledge.py cli/ledger/special.py tests/test_knowledge_staging.py tests/fixtures/knowledge
git commit -m "批次5 T10：staging 流水线机器侧——source-register（sha256+KP 语源登记）+lint 四件（契约14 schema/脱敏哨兵 special.scan_text 单源化/dedup_key 查重/词表版本+CVE 核验标记）+staging.tsv 状态机；TDD 先红后绿"
```

---

### Task 11: approve/commit/export + match/neighbors（三元组消费入口）

**Files:**
- Modify: `cli/ledger/knowledge.py`（五子命令）
- Modify: `tests/run_golden.py`（KN_CMDS 面：kn-export/kn-match——非 ledger 入口驱动，ADAPTER_CMDS 先例同型）
- Test: `tests/test_knowledge_export_match.py`（新建）；`tests/golden/kn-export.norm`、`kn-match.norm`（--bless 建档）

**Interfaces:**
- Consumes: T10 状态机；契约 14 §3 graph.ndjson 行 schema。
- Produces:
  - `approve(kdir, page, approver, timestamp)`：staging 页 lint-passed→approved（否则 Reject）；staging.tsv+log.md 双落（detail 含 approver）
  - `commit(kdir, page, timestamp)`：approved→formal——页文件迁至类目录（staging_status 字段摘除）、dedup 终检、index.md/overview.md 重生成（页计数确定性）、graph.ndjson **不动**（export 独立）
  - `export(kdir)`：扫全部 formal 页 triples/实体别名 → graph.ndjson 全量重建（行 schema 契约 14 §3；行序=(source,序号) 字典序；**两次执行字节一致**）
  - `match(kdir, client, asset, today)`：--today 必填（G-34 裁决——禁墙钟）；命中=先例页 client 全等 ∧ scope_asset 含 asset 指纹（分号多值任一子串）∧ window 覆盖 today（start≤today≤end；过期不命中并标注 [expired]）；输出命中页清单（[stale] 标注=R11）
  - `neighbors(kdir, entity)`：graph.ndjson 中 subject/object 含实体名的行清单（A8 外推消费入口）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_knowledge_export_match.py 核心用例
class TestExportMatch(unittest.TestCase):
    def test_commit_moves_and_regenerates_index(self):
        # 走完 register→手写页→lint→approve→commit：concepts/CP-0001.md 在场、
        # staging/pages 清空、index.md 计数含 K5=1
        ...

    def test_export_deterministic_bytes(self):
        r1 = kn("export", "--knowledge-dir=" + self.d)
        first = open(os.path.join(self.d, "graph.ndjson"), "rb").read()
        r2 = kn("export", "--knowledge-dir=" + self.d)
        self.assertEqual(first, open(os.path.join(self.d, "graph.ndjson"), "rb").read())
        self.assertIn('"predicate"', first.decode("utf-8"))

    def test_match_triple_strict_and_window(self):
        # 同 client+asset+窗口内 today → 命中 PR-0001；窗口外 today → 空+[expired]
        r = kn("match", "--knowledge-dir=" + self.d, "--client=CLIENT-01",
               "--asset=shop.example", "--today=2026-09-24")
        self.assertIn("PR-0001", r.stdout)
        r2 = kn("match", "--knowledge-dir=" + self.d, "--client=CLIENT-01",
                "--asset=shop.example", "--today=2027-01-01")
        self.assertNotIn("PR-0001\t", r2.stdout)

    def test_match_cross_client_never_matches(self):
        # client=CLIENT-02 永不命中 CLIENT-01 的先例（跨客户=越权事故，§7.1）
        r = kn("match", "--knowledge-dir=" + self.d, "--client=CLIENT-02",
               "--asset=shop.example", "--today=2026-09-24")
        self.assertNotIn("PR-0001", r.stdout)

    def test_match_today_required(self):
        r = kn("match", "--knowledge-dir=" + self.d, "--client=CLIENT-01", "--asset=x")
        self.assertEqual(r.returncode, 2)

    def test_neighbors_from_graph(self):
        r = kn("neighbors", "--knowledge-dir=" + self.d, "--entity=vendor-portal")
        self.assertIn("EN-", r.stdout)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_export_match -v` → FAIL。

- [ ] **Step 3: 最小实现**（要点）

```python
def export(kdir):
    lines = []
    for kind_dir in ("precedents", "entities", "concepts", "targets", "business", "retros",
                     "patterns/core", "patterns/learned"):
        d = os.path.join(kdir, kind_dir)
        for fn in sorted(os.listdir(d) if os.path.isdir(d) else []):
            if not fn.endswith(".md"):
                continue
            fm, _body = split_page(open(os.path.join(d, fn), encoding="utf-8").read())
            created = str(fm.get("last_verified", ""))
            for i, tr in enumerate(fm.get("triples", []) or []):
                if isinstance(tr, list) and len(tr) == 3:
                    lines.append({"id": "%s:t%d" % (fm["id"], i), "subject": tr[0],
                                  "predicate": tr[1], "object": tr[2],
                                  "source": fm["id"], "class": fm.get("class", ""),
                                  "created": created})
    lines.sort(key=lambda x: (x["source"], x["id"]))
    out = os.path.join(kdir, "graph.ndjson")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for x in lines:
            f.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")
    print("exported=%d" % len(lines))
    return 0
```
（commit 的 index.md 重生成=按 PAGE_SCHEMAS 目录计数拼装固定模板——确定性文本；approve/commit 状态机非法迁移一律 Reject 附当前态。）

run_golden.py 增 `KN_CMDS`（label,argv）两张面：`["export"]`/`["match","--client=CLIENT-01","--asset=shop.example","--today=2026-09-24"]`，驱动方式=临时目录 init+预置 fixtures/knowledge 合法页后 `[sys.executable, cli/tanyin-knowledge, sub, "--knowledge-dir", tmp]`——ADAPTER_CMDS 同型；`--bless` 建档。

- [ ] **Step 4: 跑绿+金样建档+commit**

Run: `python3 -m unittest tests.test_knowledge_export_match -v` 全 PASS；`python3 tests/run_golden.py` → 新面 kn-export/kn-match 建档 PASS；全量绿。

```bash
git add cli/ledger/knowledge.py tests/test_knowledge_export_match.py tests/run_golden.py tests/golden/kn-export.norm tests/golden/kn-match.norm
git commit -m "批次5 T11：知识库 approve/commit（状态机+index 重生成）/export（graph.ndjson 确定性重建，两次执行字节一致）/match（三元组全同+窗口过期失效+跨客户永不命中+--today 必填 G-34）/neighbors（A8 外推入口）；金样 kn-export/kn-match 两面建档；TDD 先红后绿"
```

---

### Task 12: G-24 读侧——K1 严重度期望基线表落表 + tanyin-knowledge score 算分

**Files:**
- Create: `knowledge/methodology/k1-baseline.tsv`（12 wstg 类全行+4 子类示范行）
- Create: `knowledge/methodology/k1-wstg-map.tsv`（WSTG↔ASVS↔OSSTMM 映射——词表版本化锚，3 列键映射）
- Modify: `cli/ledger/knowledge.py`（`baseline_lookup`+`score` 子命令+lint 覆盖率断言）
- Modify: `phases/P3.md`（算分节承载行改「读侧=tanyin-knowledge score（CLI 只读算分）；总控 Top-K 决策」）
- Test: `tests/test_k1_baseline_score.py`（新建）

**Interfaces:**
- Consumes: shared/VOCAB.md（12 类键全集）；`graph_cmds.reachable_gap_cells`（T7）；intents/assets/creds 只读（G-g1 夹具）。
- Produces: `score(kdir, goal_dir, vuln_class, asset=None) -> stdout JSON`：`{"severity_expect":x,"asset_value":y,"exploitability":z,"priority":p,"sources":{...}}`——asset_value=assets.meta `bv:<0-1>` 缺省 0.5（中性，P3.md「未标=不加分」勘误对齐）；exploitability=`0.4×可达(graph-horizon 含该资产表面) + 0.3×(active creds>0) + 0.3×(先例 match 命中>0)`；查表次序=细类→wstg 类→缺省 0.5+告警行；K1 lint 断言=VOCAB 每 wstg-* 键恰一行、无 VOCAB 外行。

- [ ] **Step 1: 写失败测试**

```python
class TestK1BaselineScore(unittest.TestCase):
    def test_baseline_covers_vocab_exactly(self):
        vocab = {l.strip()[2:] for l in open(os.path.join(HERE, "..", "shared", "VOCAB.md"),
                                             encoding="utf-8") if l.strip().startswith("- ")}
        rows = [l.split("\t") for l in open(os.path.join(SEED, "methodology", "k1-baseline.tsv"),
                                             encoding="utf-8").read().splitlines()[1:] if l]
        keys = {r[0] for r in rows}
        self.assertTrue(vocab <= keys, "VOCAB 缺行: %s" % (vocab - keys))
        extra = {k for k in keys if not (k in vocab or ":" in k)}
        self.assertFalse(extra, "VOCAB 外行: %s" % extra)

    def test_score_deterministic_on_fixture(self):
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
               "--vuln-class=wstg-authz", "--asset=AST-g1-0002",
               "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(set(out), {"severity_expect", "asset_value", "exploitability",
                                    "priority", "sources"})
        self.assertLessEqual(out["priority"], 1.0)

    def test_subclass_preferred_over_category(self):
        # --vuln-class=wstg-inpv:inj.sql 取子类行 severity_expect（0.9），非父类
        ...

    def test_unknown_class_defaults_with_warning(self):
        r = kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + FIX,
               "--vuln-class=wstg-none:xx", "--today=2026-09-24")
        self.assertIn("baseline-miss", r.stdout)   # 告警行+缺省 0.5
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_k1_baseline_score -v` → FAIL。

- [ ] **Step 3: 落基线表（全文——评定规则：高危类 0.9=注入/越权/RCE 族；0.8=认证/会话/API；0.7=密码学/业务逻辑；0.6=错误处理/客户端；0.5=身份标识/配置；0.3=信息收集；cost_hint=请求量级）+score 实现**

```tsv
# knowledge/methodology/k1-baseline.tsv（vuln_class	severity_expect	cost_hint	rationale_brief	vocab_version）
wstg-info	0.3	1	信息暴露面：低危高频，侦察即得	WSTG-v4.2
wstg-conf	0.5	1	配置错误：依赖暴露面清单	WSTG-v4.2
wstg-idnt	0.5	2	身份标识缺陷：登录/注册逻辑	WSTG-v4.2
wstg-authn	0.8	2	认证绕过/弱凭据：CNPEN 高产出类	WSTG-v4.2
wstg-authz	0.9	2	越权（BOLA/垂直）：认证后最高收益类	WSTG-v4.2
wstg-sess	0.8	2	会话管理：固定/过期/令牌语义	WSTG-v4.2
wstg-inpv	0.9	3	注入输入验证：SQLi/RCE 级，深挖后定级	WSTG-v4.2
wstg-errh	0.6	1	错误处理：堆栈/信息泄露	WSTG-v4.2
wstg-cryp	0.7	2	密码学误用：弱算法/硬编码	WSTG-v4.2
wstg-busl	0.7	3	业务逻辑：人工为主 biz 标记	WSTG-v4.2
wstg-clnt	0.6	2	客户端：XSS/DOM 族	WSTG-v4.2
wstg-apit	0.8	2	API 测试：授权/限流/批量	WSTG-v4.2
wstg-inpv:inj.sql	0.9	3	SQL 注入细类（夹具既有形态）	WSTG-v4.2
wstg-authz:authz.diff	0.9	2	身份矩阵差分细类（夹具既有形态）	WSTG-v4.2
wstg-authn:authn.missing	0.8	2	认证缺失细类（夹具既有形态）	WSTG-v4.2
wstg-clnt:xss.dom	0.6	2	DOM XSS 细类示范	WSTG-v4.2
```
（初值=方法论映射评定（WSTG 严重度倾向+CNPEN 复盘校准），**人审冻结**随本任务 commit——评语义不进 CLI，score 只查表。）

score 实现要点：`graph_cmds.reachable_gap_cells` 得 reach 集→assets 行值集含该 asset 值=可达 1.0；creds 任一 status=active=1.0；match（复用 T11 内部函数，--today 必填）命中数>0=1.0；三因子加权求和；`priority=severity_expect*asset_value*exploitability` 四舍五入 4 位；sources 附查表行/可达集计数/cred 计数/命中页——**可审计复算**。P3.md 承载行勘误（§18-25 行区域）。

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_k1_baseline_score tests.test_skill_resident -v`（P3 断言适配——test_p3_dispatch_priority_formula 若钉死旧文本则同步更新断言并在 commit 注明）全 PASS；全量绿；金样零漂移。

```bash
git add knowledge/methodology/ cli/ledger/knowledge.py phases/P3.md tests/test_k1_baseline_score.py tests/test_skill_resident.py
git commit -m "批次5 T12：K1 严重度期望基线表落表（12 wstg 全行+4 子类示范，方法论映射评定人审冻结）+tanyin-knowledge score 只读算分（三因子可审计复算+查表次序细类→类→缺省告警）；P3.md 算分承载行勘误（读侧=score 子命令）；TDD 先红后绿"
```

---

### Task 13: 四门槛晋升 promote + demote + 保鲜 lint（learned→core 飞轮后半）

**Files:**
- Modify: `cli/ledger/knowledge.py`（promote/demote 子命令+lint --freshness）
- Test: `tests/test_knowledge_promote.py`（新建）

**Interfaces:**
- Consumes: 契约 14 §4 四门槛；T10 lint；T11 commit（applied_patterns 计数载体）；patterns/{learned,core} 目录。
- Produces:
  - `promote(kdir, page, timestamp)`：四门槛机检——①`len({引用页 id for 先例页 if page in applied_patterns}) ≥ 2`（复现≥2）②`len({引用页 client}) ≥ 2`（跨目标）③log.md 存在 `approve|<page>|for=promote` 行（人工审批在场）④该页 redact 哨兵零命中（无指纹泄漏）；全过→patterns/learned/→patterns/core/ 移动+status 字段改 core+log 落账；缺口清单逐条输出
  - `demote(kdir, page, refuting, note, timestamp)`：--refuting=`EV-x;EV-y` **≥2 项**强制（N≥2 独立反证）+note 须含 `防护拦截` 或 `代码修复` 分类词（区分两类降级依据——pair_group 差分语义文字化承载）→ 移 patterns/demoted 区（status=demoted）+log
  - `lint --freshness-days=N`（缺省 180）：last_verified 距 --today 超 N 天的页输出 stale 清单（exit 0 附告警；match 侧 [stale] 标注联动=R11 既有）

- [ ] **Step 1: 写失败测试**

```python
class TestPromote(unittest.TestCase):
    def _mk_pattern(self, d, status="learned"):
        # 手工放 patterns/learned/PT-0001.md（kind=pattern，front-matter 齐备）
        ...

    def test_four_gates_each_blocks(self):
        # 逐一构造：0 引用→①缺；1 引用→②缺；无 approve 行→③缺；页含真域名→④缺
        for expect in ("复现", "跨目标", "人工审批", "指纹泄漏"):
            d = self.copy_fixture()
            self._seed_case(d, expect)     # 按缺口名铸造前置
            r = kn("promote", "--knowledge-dir=" + d, "--page=PT-0001",
                   "--timestamp=2026-09-24T12:00:00Z")
            self.assertEqual(r.returncode, 1)
            self.assertIn(expect, r.stdout)

    def test_all_gates_pass_moves_to_core(self):
        d = self.copy_fixture()
        self._seed_full(d)   # 两先例页（不同 client）引用 PT-0001+approve 行+干净页
        r = kn("promote", "--knowledge-dir=" + d, "--page=PT-0001",
               "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(d, "patterns", "core", "PT-0001.md")))
        self.assertFalse(os.path.isfile(os.path.join(d, "patterns", "learned", "PT-0001.md")))

    def test_demote_needs_two_refutations_and_class(self):
        d = self.copy_fixture()
        r = kn("demote", "--knowledge-dir=" + d, "--page=PT-0001",
               "--refuting=EV-g1-0001", "--note=误报", "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r.returncode, 1)   # 单反证拒
        r2 = kn("demote", "--knowledge-dir=" + d, "--page=PT-0001",
                "--refuting=EV-g1-0001;EV-g1-0002", "--note=证据归因：防护拦截",
                "--timestamp=2026-09-24T12:00:00Z")
        self.assertEqual(r2.returncode, 0)

    def test_freshness_report(self):
        d = self.copy_fixture()   # 夹具含 last_verified=2025-01-01 页
        r = kn("lint", "--knowledge-dir=" + d, "--today=2026-09-24")
        self.assertIn("stale", r.stdout)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_promote -v` → FAIL。

- [ ] **Step 3: 最小实现**（promote 核心段）

```python
def promote(kdir, page_id, ts):
    guard_writable(kdir)
    src = _find_page(kdir, page_id)                      # learned 区定位
    fm, body = read_page(src)
    refs = [(pf["id"], pf.get("client")) for pf in iter_pages(kdir, "precedent")
            if page_id in (pf.get("applied_patterns") or [])]
    gates = []
    if len({r[0] for r in refs}) < 2:
        gates.append("①复现≥2 缺：引用先例 %d 个" % len({r[0] for r in refs}))
    if len({r[1] for r in refs}) < 2:
        gates.append("②跨目标有效 缺：client 去重 %d 个" % len({r[1] for r in refs}))
    if not _log_has(kdir, "approve", page_id, "for=promote"):
        gates.append("③人工审批 缺：log.md 无 approve for=promote 行")
    if special.scan_text(_fm_text(fm) + body):
        gates.append("④无指纹泄漏 缺：redact 哨兵命中")
    if gates:
        print("REJECT 四门槛缺口：")
        for g in gates:
            print("  " + g)
        return 1
    _move(src, os.path.join(kdir, "patterns", "core", page_id + ".md"),
          fm_updates={"status": "core"})
    _log(kdir, ts, "promote", page_id, "learned->core refs=%d clients=%d" % (len(refs), ...))
    return 0
```

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_knowledge_promote -v` 全 PASS；`python3 -m unittest discover -s tests` 全绿；金样零漂移。

```bash
git add cli/ledger/knowledge.py tests/test_knowledge_promote.py
git commit -m "批次5 T13：四门槛晋升 promote（复现≥2/跨目标/人工审批在场/零指纹——机械核验缺口清单化）+demote（≥2 反证+防护拦截/代码修复分类）+lint 保鲜（--freshness-days 180 陈旧清单）；TDD 先红后绿"
```

---

### Task 14: K3 本地 CVE 快照 + nday-match 离线匹配（联网仅核验边界）

**Files:**
- Create: `knowledge/cve/cve-snapshot.tsv`（~14 行精选快照——公开 NVD/KEV 口径样例数据）
- Create: `knowledge/cve/README.md`（快照来源/更新纪律/联网仅核验边界——R11）
- Modify: `cli/ledger/knowledge.py`（`nday_match` 子命令+版本区间比较）
- Test: `tests/test_nday_match.py`（新建）；`tests/golden/kn-nday.norm`（--bless 建档）

**Interfaces:**
- Consumes: assets.meta CPE 指纹形态（`cpe:<vendor>:<product>` 前缀+版本——recon/surface 段 meta 约定既有）。
- Produces: `nday_match(kdir, cpe, version) -> stdout TSV`：`cve_id\tseverity\tversion_range\tpublished` 行——命中=cpe 前缀前缀匹配 ∧ version∈[start,end)（版本元组比较：`_vtuple("2.14.1")<(2,15)` 语义；非数字段按 0 处理）；零命中 exit 0 输出 `#candidates=0`；**零联网**（模块 import 白名单断言：无 urllib/socket/http/requests）。

- [ ] **Step 1: 写失败测试**

```python
class TestNdayMatch(unittest.TestCase):
    def test_hit_log4shell_range(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED, "--cpe=cpe:apache:log4j", "--version=2.14.1")
        self.assertEqual(r.returncode, 0)
        self.assertIn("CVE-2021-44228", r.stdout)

    def test_version_out_of_range_miss(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED, "--cpe=cpe:apache:log4j", "--version=2.17.1")
        self.assertIn("#candidates=0", r.stdout)

    def test_no_network_imports(self):
        src = open(os.path.join(HERE, "..", "cli", "ledger", "knowledge.py"), encoding="utf-8").read()
        for banned in ("urllib", "socket", "http.client", "requests"):
            self.assertNotIn(banned, src, "联网库进 knowledge.py 违反离线边界")

    def test_unknown_prefix_zero(self):
        r = kn("nday-match", "--knowledge-dir=" + SEED, "--cpe=cpe:x:y", "--version=1.0")
        self.assertEqual(r.returncode, 0)
        self.assertIn("#candidates=0", r.stdout)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_nday_match -v` → FAIL。

- [ ] **Step 3: 落快照+实现**

```tsv
# knowledge/cve/cve-snapshot.tsv（cve_id	cpe_prefix	version_start	version_end	severity	published	source）
# 精选样例快照（公开 NVD/CISA KEV 口径；正式全量快照=批次 6 安装器期刷新——README 纪律）
CVE-2021-44228	cpe:apache:log4j	2.0	2.15	critical	2021-12-10	NVD
CVE-2022-22965	spring-framework	5.3.0	5.3.18	critical	2022-03-31	NVD
CVE-2017-5638	struts	2.0	2.3.32	critical	2017-03-06	NVD
CVE-2022-22947	spring-cloud-gateway	3.1.0	3.1.1	critical	2022-03-01	NVD
CVE-2019-0232	tomcat	9.0.0	9.0.17	high	2019-04-11	NVD
CVE-2018-1273	spring-data-commons	1.13.0	1.13.12	high	2018-04-10	NVD
CVE-2020-9484	tomcat	10.0.0	10.0.0	 high	2020-05-21	NVD
CVE-2021-25646	apache-druid	0.2.0	0.20.2	critical	2021-01-29	NVD
CVE-2016-3081	jenkins	1.0	2.14	high	2016-04-13	NVD
CVE-2020-11651	saltstack	3000	3000.3	high	2020-04-29	NVD
CVE-2021-21985	vmware-vsphere	6.5	7.0.3	critical	2021-05-25	NVD
CVE-2022-1388	f5-big-ip	16.1.0	16.1.2	critical	2022-05-04	KEV
CVE-2023-4966	citrix-netscaler	13.0	14.1	critical	2023-10-10	KEV
CVE-2024-3400	palo-alto-globalprotect	10.2	11.1.0	critical	2024-04-12	KEV
```
（README：来源=NVD/CISA KEV 公共数据；更新纪律=人工重铸整文件+首行注记刷新日期+lint 校验七列格式；**联网仅核验**边界=快照匹配离线、P6 技法页 CVE 对照走宿主 WebSearch（PSIRT/NVD/KEV），CLI 零外联。快照时效探知项 G-32 登记。）

```python
def _vtuple(v):
    parts = []
    for seg in str(v).split("."):
        n = ""
        for ch in seg:
            n += ch if ch.isdigit() else ""
            if not ch.isdigit():
                break
        parts.append(int(n or 0))
    return tuple(parts)

def nday_match(kdir, cpe, version):
    rows = _read_tsv(os.path.join(kdir, "cve", "cve-snapshot.tsv"))
    v = _vtuple(version)
    hits = [r for r in rows
            if cpe.startswith(r["cpe_prefix"]) or r["cpe_prefix"].startswith(cpe + ":")
            if _vtuple(r["version_start"]) <= v < _vtuple(r["version_end"])]
    print("#candidates=%d" % len(hits))
    for r in sorted(hits, key=lambda x: x["cve_id"]):
        print("\t".join([r["cve_id"], r["severity"],
                          "%s..%s" % (r["version_start"], r["version_end"]), r["published"]]))
    return 0
```
（P3 nday 通路接线：asset-added 事件处理器消费 `nday-match` 输出→`add-intent --kind=nday-verify --via=<cve_id>`——G-18 已载 nday-verify→nuclei 引擎映射；duty 文字随 T19 收口。）

- [ ] **Step 4: 跑绿+金样建档+commit**

Run: `python3 -m unittest tests.test_nday_match -v` 全 PASS；run_golden 增 kn-nday 面（`["nday-match","--cpe=cpe:apache:log4j","--version=2.14.1"]`）--bless 建档；全量绿。

```bash
git add knowledge/cve/ cli/ledger/knowledge.py tests/test_nday_match.py tests/run_golden.py tests/golden/kn-nday.norm
git commit -m "批次5 T14：K3 本地 CVE 快照（14 行精选+README 更新纪律/联网仅核验边界）+nday-match 离线 CPE 匹配（前缀+版本区间元组比较，零联网 import 断言）；金样 kn-nday 建档；TDD 先红后绿"
```

---

### Task 15: 反向验证落地（tanyin-redact --reverse-verify）+ CLIENT-NN 映射

**Files:**
- Modify: `cli/ledger/special.py`（`h_reverse_verify` handler+敏感词集构造）
- Modify: `cli/tanyin-redact`（入口旗标分发）
- Modify: `cli/ledger/phases_engine.py`（EXTRA_TOOLS 拆分：tanyin-report 留 ENV-HALT、tanyin-redact 分发——R13）
- Modify: `cli/ledger/knowledge.py`（`client-map next/add/list` 三子命令）
- Test: `tests/test_reverse_verify.py`（新建，含 gate P6 端到端用例）

**Interfaces:**
- Consumes: phases.yaml P6 断言文本（**零改**——`tanyin-redact --reverse-verify`）；`approve --knowledge`（既有，write_cmds.py:758-783）；G-g1/diff-authz 夹具。
- Produces:
  - `tanyin-redact --goal-dir D [--reverse-verify] [--target=<draft路径>]`：缺省 target=`report/report-draft.md`；敏感词集=assets.value 全集＋creds.username_ref＋special 泄漏形态动态命中；输出命中清单（文件:行:词类）或 `零命中`；exit 0/1/2
  - gate P6 断言真跑：phases_engine 断言回路 `tokens[0]=="tanyin-redact"` → 分发 special handler（argv=`["--reverse-verify"]+rest`）；tanyin-report 维持 ENV-HALT（批次 6）
  - `tanyin-knowledge client-map next|add|list`：`next` 分配最小未用 CLIENT-NN；`add --client --real-ref --note`；文件=<knowledge-dir>/client-map.tsv（gitignore 在册；种子库只读守卫）
- P6 门从此可过（干跑链路 P0→P6 全通的最后一块）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_reverse_verify.py（夹具=G-g1 副本+report/report-draft.md 两种草稿）
class TestReverseVerify(unittest.TestCase):
    def test_dirty_draft_detected(self):
        # 草稿含 assets.value 值 shop.example（session 出现过）→ exit 1 命中清单
        self._write_draft("结论：shop.example 的管理面板存在越权。")
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 1)
        self.assertIn("shop.example", r.stdout)

    def test_clean_draft_zero_hits(self):
        self._write_draft("结论：CLIENT-01 的管理面板存在越权（{{vault:cred-2}} 对照）。")
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 0)
        self.assertIn("零命中", r.stdout)

    def test_default_target_and_override(self):
        # 无 --target 读 report/report-draft.md；--target 任意路径覆盖
        ...

    def test_gate_p6_end_to_end(self):
        # 夹具补齐：P6.0 前置门事件+approve --knowledge 行+净草稿 → gate --phase P6 exit 0 → END
        r = run_phases(self.d, "gate", "--phase=P6", "--timestamp=2026-09-24T13:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("END", r.stdout)

    def test_client_map_cycle(self):
        d = tempfile.mkdtemp(); kn("init", "--knowledge-dir=" + d)
        r = kn("client-map", "--knowledge-dir=" + d, "next")
        self.assertIn("CLIENT-01", r.stdout)
        kn("client-map", "--knowledge-dir=" + d, "add", "--client=CLIENT-01",
           "--real-ref=某零售客户", "--note=P6 首例")
        r2 = kn("client-map", "--knowledge-dir=" + d, "next")
        self.assertIn("CLIENT-02", r2.stdout)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_reverse_verify -v` → FAIL（无旗标分发，gate P6 仍 ENV-HALT）。

- [ ] **Step 3: 最小实现**

```python
# special.py 增（泄漏形态/资产值/账号名三源敏感词集）
def h_reverse_verify(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"reverse-verify", "target"}:
        raise UsageError("reverse-verify [--target=<draft>]")
    s = core.Session(goal_dir)
    target = args.get("target", os.path.join("report", "report-draft.md"))
    p = os.path.join(goal_dir, target)
    if not os.path.isfile(p):
        sys.stderr.write("环境问题: 草稿不存在 %s（P5 先产 report-draft）\n" % target)
        return 2
    words = {_cell("assets.tsv", r, "value").strip() for r in s.rows("assets.tsv")}
    words |= {_cell("creds.tsv", r, "username_ref").strip() for r in s.rows("creds.tsv")}
    words.discard("")
    hits = []
    for i, ln in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
        for w in sorted(words):
            if w in ln:
                hits.append("%s:%d:资产/账号值 %s" % (target, i, w))
        for name, line in scan_text(ln):            # 形态级（cookie/token/密码）
            hits.append("%s:%d:泄漏形态[%s]" % (target, i, name))
    if hits:
        print("FAIL 反向验证命中 %d 处：" % len(hits))
        for h in hits[:50]:
            print("  " + h)
        return 1
    print("零命中（域名/IP/凭据/token 敏感词 %d 项全未出现）" % len(words))
    return 0
```
（tanyin-redact 入口：`if "--reverse-verify" in rest: return HANDLERS["reverse-verify"](goal_dir, rest)`——旗标先于 redact-scan 分发；phases_engine.py:200 `EXTRA_TOOLS = {"tanyin-report"}`+断言回路增 `if tokens[0] == "tanyin-redact": h = special.HANDLERS["reverse-verify"]; argv=["--reverse-verify"]+tokens[1:]` 分支——validate_phases 的 known 集合同步含 tanyin-redact（已有）与 tanyin-report。）

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_reverse_verify tests.test_phases_gate tests.test_redact_injection -v` 全 PASS（P6 端到端新用例转绿）；`python3 -m unittest discover -s tests` 全绿；金样零漂移（phases-gate-p0 面不含 P6）。

```bash
git add cli/ledger/special.py cli/tanyin-redact cli/ledger/phases_engine.py cli/ledger/knowledge.py tests/test_reverse_verify.py
git commit -m "批次5 T15：反向验证落地——tanyin-redact --reverse-verify（敏感词集=资产值/账号名/泄漏形态三源；缺省 target=report-draft.md）+gate P6 断言真跑（EXTRA_TOOLS 拆分：report 留 ENV-HALT/redact 分发）+client-map next/add/list（CLIENT-NN 运行时映射）；P6 门端到端首通；TDD 先红后绿"
```

---

### Task 16: CNPEN 82 五类素材入库（双知识库之一）

**Files:**
- Create: `knowledge/sources/cnpen/`（执行期放置素材；五类=测试全景图/思路复盘/测试记录 T1-T55/31 份黑盒漏洞单/BurpPOC 合集——**素材不可得=blocked 上报，不造数据**）
- Modify: `knowledge/`（蒸馏产出页：concepts≥3、precedents≥2、patterns≥2、methodology 登记指针）
- Modify: `knowledge/sources/SOURCES.tsv`（≥5 笔语源登记）
- Test: `tests/test_knowledge_ingest_cnpen.py`（新建——结构性断言，不判内容语义）

**Interfaces:**
- Consumes: T9-T15 全流水线（register→蒸馏写页→lint→approve→commit→export）；§7.2 五类素材落位表；checklists/review-checklist.md。
- Produces:**CNPEN 库**（§9.4 抽查对象一）：五类素材各有落位——全景图→sources 登记指针+夹具素材归 tests/fixtures（G-31 裁决：防库膨胀）；复盘八阶段+7 核心思路→concepts 方法论原则页（errorCode 语义分析/前端 JS 是 API 说明书/微服务直连假设等）；测试记录→precedents 先例链路页（CLIENT-NN 脱敏）；漏洞单→patterns ok-sample 样例页；BurpPOC→concepts 技法页 tool_params 节。**词表基线保持 WSTG 全集**（防纯 Java 样本过拟合——页 vuln_class 一律词表键，禁止发明 CNPEN 私有类）。

- [ ] **Step 1: 写失败测试**

```python
class TestCnpenIngest(unittest.TestCase):
    SEED = os.path.join(HERE, "..", "knowledge")

    def test_sources_registered_five_origins(self):
        rows = open(os.path.join(self.SEED, "sources", "SOURCES.tsv"), encoding="utf-8").read()
        self.assertEqual(rows.count("\tcnpen\t"), 5, "CNPEN 五类语源各一笔")
        self.assertIn("proprietary", rows)     # 自有语料许可形态注记

    def test_min_page_counts(self):
        for sub, n in (("concepts", 3), ("precedents", 2), ("patterns/core", 1),
                       ("patterns/learned", 1)):
            files = [f for f in os.listdir(os.path.join(self.SEED, sub)) if f.endswith(".md")]
            self.assertGreaterEqual(len(files), n, sub + " 页数不足")

    def test_lint_passes_on_seed(self):
        r = kn("lint", "--knowledge-dir=" + self.SEED, "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_vocab_baseline_is_wstg_only(self):
        # 防 CNPEN 过拟合：全部页 vuln_class 均为 wstg-* 键或 wstg-XX:sub 形
        for p in iter_md(os.path.join(self.SEED, "concepts")) + iter_md(os.path.join(self.SEED, "precedents")):
            fm, _ = read_page(p)
            for vc in str(fm.get("vuln_class", "")).split(";"):
                self.assertTrue(vc.startswith("wstg-"), "%s 私有类 %r" % (p, vc))

    def test_no_raw_client_residue(self):
        # §9.4 判据③前置：全部正式页 client 字段 CLIENT-NN 形态（lint 已强制，抽查钉死）
        for p in iter_md(os.path.join(self.SEED, "precedents")):
            fm, _ = read_page(p)
            self.assertRegex(fm["client"], r"^CLIENT-\d{2,}$")
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_ingest_cnpen -v` → FAIL（种子库空）。

- [ ] **Step 3: 入库执行（蒸馏=执行者按 checklist 产出，CLI 只校验）**

1. 素材就位：`knowledge/sources/cnpen/{panorama,retro,records,vuln-sheets,burp-poc}/`（执行期从客户素材库拷入；**缺失即停：报 blocked+缺哪类**，登记 SOURCES 待补行不造数据）。
2. 五笔语源登记（每类一笔 --origin=cnpen --license=proprietary）。
3. 蒸馏产出（每页过 checklists/review-checklist.md 逐项自查后在 log.md 落 approver）：concepts 三页起（示例全文如下——其余同构）；precedents 两页起（client=CLIENT-01/02，scope_asset 占位符化，triples≥2 行）；patterns ok-sample 两页（漏洞单判定标准：注入深挖后才定级）；BurpPOC 参数并入 concepts tool_params 节。
4. 流水线机械侧：`lint → approve（逐页）→ commit → export` 全绿。

```markdown
# concepts/CP-0001.md（蒸馏示范页全文——执行者照此同构产出其余页）
---
id: CP-0001
kind: technique
class: K5
title: errorCode 语义分析优先于状态码
vocab_version: WSTG-v4.2
vuln_class: wstg-errh;wstg-apit
applicability: JSON/XML API 响应含业务 errorCode 字段的任意端点
tool_params: ""
cost_hint: 1
failure_modes: 仅看 HTTP 200 即判成功（errorCode:00000 才是业务成功）；无 errorCode 体系时退回内容类型验证
judgment: 差分判定三条机械规则之一——errorCode 语义分析优于状态码（§6.3）
cve_refs: ""
cve_verified: []
last_verified: 2026-09-24
status: core
source_id: KP-0002
---
## 适用条件
响应体携带结构化业务错误码的接口（微服务网关/内部 API 常见）。
## 步骤
1. 正常/异常/越权三组请求各取响应；
2. 对照 errorCode 表归因（00000=成功；A0xxx=鉴权族；B0xxx=参数族…按目标字典还原）；
3. 状态码与 errorCode 矛盾时以 errorCode 为准记录 fact。
## 证据标准
EV 卡片 raw_excerpt 必含 errorCode 值；expected.matchers word 命中业务码而非 status。
```

- [ ] **Step 4: 跑绿+eval 前置+commit**

Run: `python3 -m unittest tests.test_knowledge_ingest_cnpen -v` 全 PASS；`python3 cli/tanyin-knowledge lint --knowledge-dir knowledge --today=2026-09-24` exit 0；全量单测绿；金样零漂移（kn-export/kn-match 面若因种子页增加而漂移 → --bless 有意刷新+commit 注明「种子库内容增长=预期」）。

```bash
git add knowledge/ tests/test_knowledge_ingest_cnpen.py tests/golden
git commit -m "批次5 T16：CNPEN 82 五类素材入库——五笔语源登记+复盘→concepts 方法论页（errorCode 语义分析等≥3）+测试记录→precedents 先例页（CLIENT-NN 脱敏≥2）+漏洞单→patterns ok-sample（≥2）+BurpPOC→tool_params；词表基线守 WSTG 全集防过拟合；lint/approve/commit/export 全绿；TDD 先红后绿"
```

---

### Task 17: 外部语料入库（VulnClaw 47 专题蒸馏 + BugHunter/Threatswarm/CEP 取材流程）

**Files:**
- Create: `knowledge/sources/vulnclaw/LICENSE.note`（MIT 许可注记——引分析报告：Copyright (c) 2026 UncleC，MIT，.research/repos/VulnClaw/LICENSE 可核）
- Modify: `knowledge/`（concepts 增 detail-pack 蒸馏页≥8、precedents 增 warstory 先例页≥2、checklists 增 experience 人审门流程注记节、business 增 CEP ROE scope 模板语义注记页 1）
- Modify: `knowledge/sources/SOURCES.tsv`（vulnclaw 一笔+外部三源执行期各一笔或降级登记）
- Test: `tests/test_knowledge_ingest_external.py`（新建）

**Interfaces:**
- Consumes: `.research/repos/VulnClaw`（只读本地源码：`vulnclaw/skills/specialized/` 50 目录（31 个 redteam-*-detail-pack——分析报告口径 47 专题）；`vulnclaw/skills/core/` 7 md；`vulnclaw/warstories/` 2 篇；`vulnclaw/kb/experience.py`+agent/distiller.py 流程模式）；T10-T15 流水线。
- Produces:**外部库**（§9.4 抽查对象二）：
  - VulnClaw 首批蒸馏 8 个 detail-pack→concepts 技法页（sqli/xss/ssrf/ssti/deserialize/cmdi/cors/open-redirect——映射：Domain→applicability、覆盖域表→vuln_class 词表键映射、Boundaries→正文边界节、Pivot Hints→failure_modes、Exit Evidence→judgment/证据标准；**首批 8 页，余 39 批次 6+ 持续飞轮**——防单任务过巨，登记移交）
  - 2 warstory→precedents 先例页（NSSCTF 域名→CLIENT-NN+占位符、flag/token→占位符；triples 提炼攻击链主谓宾）
  - experience 人审门+0.88 近重复合并→checklists 增补节（流程注记：「Lessons remain pending until a human approves them」模式=四门槛③同型；0.88 语义合并无嵌入载体→G-30 登记）
  - BugHunter hunt-*→技法页骨架 / Threatswarm 27 agent 语料→concepts 素材 / CEP ROE amendments→scope 模板语义注记（business 页）+report-template.html→**批次 6 报告底版登记不实现**；三源仓库执行期 clone 至 `.research/repos/<name>`（MIT 逐一核验 LICENSE 在场；**缺=降级登记不阻塞**——SOURCES 落 origin 行+note=待补，G-35）
- **CVE 核验标记齐全**：外部库全部页 cve_refs 非空者必须 cve_verified 齐（本任务蒸馏时即核验——执行者经宿主 WebSearch 对照 NVD/KEV 一次，verified_at 落检索日；离线环境=不写 cve_refs 只写方法论内容，登记待核验清单）。

- [ ] **Step 1: 写失败测试**

```python
class TestExternalIngest(unittest.TestCase):
    SEED = os.path.join(HERE, "..", "knowledge")

    def test_vulnclaw_license_note(self):
        t = open(os.path.join(self.SEED, "sources", "vulnclaw", "LICENSE.note"), encoding="utf-8").read()
        self.assertIn("MIT", t); self.assertIn("UncleC", t)

    def test_eight_detail_pack_pages(self):
        pages = iter_md(os.path.join(self.SEED, "concepts"))
        titles = " ".join(fm_of(p).get("title", "") for p in pages)
        for kw in ("SQL", "XSS", "SSRF", "SSTI", "反序列化", "命令注入", "CORS", "开放重定向"):
            self.assertIn(kw, titles, "缺 detail-pack 蒸馏页: " + kw)

    def test_warstory_precedents_sanitized(self):
        pr = iter_md(os.path.join(self.SEED, "precedents"))
        src = "".join(open(p, encoding="utf-8").read() for p in pr)
        self.assertNotIn("nssctf", src.lower())       # 真平台域名零残留
        self.assertNotIn("NSSCTF{", src)               # flag 零残留

    def test_cve_marks_complete(self):
        for p in iter_md(os.path.join(self.SEED, "concepts")) + iter_md(os.path.join(self.SEED, "precedents")):
            fm, _ = read_page(p)
            refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c]
            verified = {v.get("cve") for v in fm.get("cve_verified", []) or []}
            for c in refs:
                self.assertIn(c, verified, "%s CVE 未核验 %s" % (p, c))

    def test_experience_process_annotated(self):
        t = open(os.path.join(self.SEED, "checklists", "review-checklist.md"), encoding="utf-8").read()
        self.assertIn("experience", t)      # 人审门流程注记节在场
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_knowledge_ingest_external -v` → FAIL。

- [ ] **Step 3: 蒸馏执行**（VulnClaw 取材口径——每页四段映射，许可注记随页 source_id→LICENSE.note 可溯）

1. `source-register --origin=vulnclaw --license=MIT --note=.research/repos/VulnClaw HEAD 3b71e26`；LICENSE.note 落盘。
2. 8 页蒸馏（读 `vulnclaw/skills/specialized/redteam-{sqli,xss,ssrf,ssti,deserialize,cmdi,cors-miscfg,open-redirect}-detail-pack/SKILL.md`——Domain/Boundaries/Pivot Hints/Exit Evidence 四段结构固定，映射到技法页四节；vuln_class 映射表：sqli→wstg-inpv:inj.sql、xss→wstg-clnt:xss.dom|wstg-inpv、ssrf→wstg-inpv:ssrf、ssti→wstg-inpv:ssti、deserialize→wstg-inpv:deserialize、cmdi→wstg-inpv:cmdi、cors→wstg-conf:cors、open-redirect→wstg-busl:redirect）。
3. 2 warstory 先例页（`2026-04-19_php-deserialization_regex-bypass.md`/`2026-04-19_php-weak-comparison_double-write-md5-bypass.md`——元信息表→front-matter、攻击链表→triples（步骤主谓宾提炼 ≥6 行）、flag/域名/IP 全占位符化）。
4. checklists 增补节+CEP business 页+外部三源处理（或降级登记）。
5. `lint → approve → commit → export` 全绿。

- [ ] **Step 4: 跑绿+全量+commit**

Run: `python3 -m unittest tests.test_knowledge_ingest_external -v` 全 PASS；全量绿；金样（kn-* 面如漂移 → --bless 注明种子增长）。

```bash
git add knowledge/ tests/test_knowledge_ingest_external.py tests/golden
git commit -m "批次5 T17：外部语料入库——VulnClaw MIT 注记+8 detail-pack 蒸馏技法页（四段映射词表键化）+2 warstory 先例页（占位符化零残留）+experience 人审门流程注记+CEP ROE/business 页+BugHunter/Threatswarm/CEP 取材流程（缺源降级登记 G-35）；CVE 核验标记齐全；TDD 先红后绿"
```

---

### Task 18: 出口 eval 两件——双知识库抽查（§9.4）+ 反向验证零命中

**Files:**
- Create: `tests/eval_knowledge_spotcheck.py`（双知识库抽查 eval——§9.4 四判据机检化）
- Create: `tests/eval_reverse_verify.py`（反向验证零命中 eval——脏/净双案例）
- Test: 以上两脚本即交付物（`tests/test_eval_scripts.py` 调两脚本对夹具跑通断言退出码——防「永远 FAIL/永远 PASS」两种坏实现）

**Interfaces:**
- Consumes: T16/T17 双库（knowledge/ 种子）；T15 reverse-verify；T10/T11 lint/match。
- Produces: 批次 5 出口验收 ①② 的判定命令（CI 可重放；批次 6 并入 evals 指标集）：
  - `eval_knowledge_spotcheck.py --knowledge-dir D [--origin cnpen|external] --today ISO`：判据①字段完整=lint 全 PASS；②指纹可检索=先例页逐页自反 match 命中 100%+实体页 neighbors 非空；③无跨客户残留=全页扫描真域名/IP/客户名（CLIENT-NN 与白名单 example.com/test/localhost/占位符外零容忍——special 形态+域名正则复用）；④CVE 核验标记齐全（限 --origin=external：cve_refs 页全核验+verified_at≤today 无未来时间戳）。exit 0=全过 / 1=FAIL 清单 / 2=环境。
  - `eval_reverse_verify.py --goal-dir D`：内置脏草稿（含夹具资产值）必须 exit 1+净草稿必须 exit 0——双向断言。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_eval_scripts.py
class TestEvalScripts(unittest.TestCase):
    def test_spotcheck_green_on_seed(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                            "--knowledge-dir", os.path.join(HERE, "..", "knowledge"),
                            "--today", "2026-09-24"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("spotcheck PASS", r.stdout)

    def test_spotcheck_detects_dirty_fixture(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "eval_knowledge_spotcheck.py"),
                            "--knowledge-dir", os.path.join(HERE, "fixtures", "knowledge-dirty"),
                            "--today", "2026-09-24"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("无跨客户残留", r.stdout)

    def test_reverse_verify_eval_both_ways(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "eval_reverse_verify.py"),
                            "--goal-dir", FIX], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("dirty=detected", r.stdout)
        self.assertIn("clean=zero-hits", r.stdout)
```

- [ ] **Step 2: 跑红** — Run: `python3 -m unittest tests.test_eval_scripts -v` → FAIL（脚本不存在）。

- [ ] **Step 3: 落两脚本**

```python
# tests/eval_knowledge_spotcheck.py（骨架——四判据逐项实现，输出可读清单）
"""§9.4 双知识库抽查 eval。用法见 --help；exit 0=全过/1=FAIL 清单/2=环境。"""
import argparse, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
KN = os.path.join(HERE, "..", "cli", "tanyin-knowledge")

def kn(kd, *args):
    return subprocess.run([sys.executable, KN] + list(args) + ["--knowledge-dir", kd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knowledge-dir", required=True)
    ap.add_argument("--origin", choices=("cnpen", "external"), default=None)
    ap.add_argument("--today", required=True)
    a = ap.parse_args()
    fails = []
    r = kn(a.knowledge_dir, "lint", "--today=" + a.today)      # ① 字段完整
    if r.returncode != 0:
        fails.append("字段完整: lint FAIL\n" + r.stdout)
    for pr in iter_precedents(a.knowledge_dir):                # ② 指纹自反可检索
        fm = read_page(pr)[0]
        m = kn(a.knowledge_dir, "match", "--client=" + fm["client"],
               "--asset=" + fm["scope_asset"].split(";")[0], "--today=" + a.today)
        if fm["id"] not in m.stdout:
            fails.append("指纹可检索: %s 自反未命中" % fm["id"])
    for path, hit in scan_real_identifiers(a.knowledge_dir):   # ③ 无跨客户残留
        fails.append("无跨客户残留: %s %s" % (path, hit))
    if a.origin == "external":                                 # ④ CVE 核验标记齐全
        for p, fm in iter_origin_pages(a.knowledge_dir, "external"):
            refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c]
            verified = {v.get("cve") for v in fm.get("cve_verified", []) or []}
            if any(c not in verified for c in refs) or _future_dates(fm, a.today):
                fails.append("CVE 核验标记: %s" % p)
    if fails:
        print("spotcheck FAIL %d 项：" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("spotcheck PASS（四判据全过）")
    return 0
```
（`eval_reverse_verify.py`：G-g1 夹具上写两份临时草稿分别断言 exit 1/exit 0，输出 `dirty=detected` 与 `clean=zero-hits` 两行。）

- [ ] **Step 4: 跑绿+commit**

Run: `python3 -m unittest tests.test_eval_scripts -v` 全 PASS；`python3 tests/eval_knowledge_spotcheck.py --knowledge-dir knowledge --origin cnpen --today 2026-09-24` 与 `--origin external` 双跑 exit 0；全量绿。

```bash
git add tests/eval_knowledge_spotcheck.py tests/eval_reverse_verify.py tests/test_eval_scripts.py tests/fixtures/knowledge-dirty
git commit -m "批次5 T18：出口 eval 两件——双知识库抽查（§9.4 四判据：字段完整/指纹自反可检索/无跨客户残留/CVE 核验齐全）+反向验证零命中（脏净双向断言防假绿）；TDD 先红后绿"
```

---

### Task 19: 总控接线与批次收口（SKILL/P3/P6/recon/README/HANDOFF/探知项台账/出口验收）

**Files:**
- Modify: `SKILL.md`（路由表知识库行+P6 沉淀行——token<2000 复测）
- Modify: `phases/P6.md`（duty 命令化五步：client-map→脱敏草稿→reverse-verify→approve 双锚→commit+export）
- Modify: `phases/P3.md`（nday 通路行+asset-added 回边 nday-match 消费注记；T12 已改算分行则只补 nday 行）
- Modify: `engines/web-blackbox/phases/recon.md`（A8 外推节补知识库邻居查询接点+assets.meta CPE 指纹形态注记）
- Modify: `cli/README.md`（批次 5 节：tanyin-knowledge 13 子命令速查+用法四行+出口验证记录）
- Create: `docs/design/2026-09-24-b5-discovery-notes.md`（批 5 台账 G-29..G-35+移交清单——结构同 b3/b4 四节式）
- Modify: `docs/HANDOFF.md`（状态快照批次 5 行+开发流水 T1-T19 记账）
- Modify: `docs/design/2026-09-24-b4-discovery-notes.md`（状态归并表 G-23/G-24/G-26/G-27/G-28+R6 五行就地注记「已闭环·批次 5」——追加注记不改历史行，G-2 先例）
- Test: `tests/test_skill_resident.py`（扩 `TestBatch5Wiring` 类）

**Interfaces:**
- Consumes: T1-T18 全部交付物。
- Produces: 总控运行时知识接线（P2 开局 match/P3 nday+score/P6 沉淀五步）；批 5 台账与移交清单（含 VulnClaw 批 6 三项登记：退出码第 3 态/findings.json+SARIF 双工件/报告内容过滤器——只登记不实现）；出口验收记录。

- [ ] **Step 1: 写失败测试**

```python
class TestBatch5Wiring(unittest.TestCase):
    def test_route_table_lists_knowledge(self):
        t = open(SKILL, encoding="utf-8").read()
        self.assertIn("tanyin-knowledge", t)
        self.assertIn("knowledge/", t)

    def test_p6_duty_commandized(self):
        t = open(os.path.join(PHASES, "P6.md"), encoding="utf-8").read()
        for kw in ("client-map", "reverse-verify", "commit", "export"):
            self.assertIn(kw, t, "P6 duty 缺 " + kw)

    def test_p3_nday_lane_wired(self):
        t = open(os.path.join(PHASES, "P3.md"), encoding="utf-8").read()
        self.assertIn("nday-match", t)

    def test_recon_a8_knowledge_neighbors(self):
        t = open(os.path.join(ROOT, "engines", "web-blackbox", "phases", "recon.md"),
                 encoding="utf-8").read()
        self.assertIn("neighbors", t)

    def test_skill_budget_still_under_2k(self):
        text = open(SKILL, encoding="utf-8").read()
        self.assertLess(estimate_tokens(text), 2000)

    def test_b5_ledger_on_disk(self):
        p = os.path.join(ROOT, "docs", "design", "2026-09-24-b5-discovery-notes.md")
        self.assertTrue(os.path.isfile(p))
        self.assertIn("G-29", open(p, encoding="utf-8").read())

    def test_b4_ledger_annotated_closed(self):
        t = open(os.path.join(ROOT, "docs", "design", "2026-09-24-b4-discovery-notes.md"),
                 encoding="utf-8").read()
        self.assertIn("已闭环·批次 5", t)

    def test_cli_readme_batch5_section(self):
        t = open(os.path.join(ROOT, "cli", "README.md"), encoding="utf-8").read()
        self.assertIn("批次 5", t)
        self.assertIn("tanyin-knowledge", t)
```

- [ ] **Step 2: 跑红→接线**

Run: `python3 -m unittest tests.test_skill_resident -v` → 新类 FAIL。修改：

- `SKILL.md` 路由表增一行：`知识库与摄入→knowledge/（种子库；K1-K8）+cli/tanyin-knowledge（13 子命令：staging 流水线/三元组 match/nday/score；摄入流程=knowledge/checklists/review-checklist.md；P6 沉淀五步见 phases/P6.md）`；「九门循环」P6 行补（反向验证已交付注记）。预算复测 <2000（当前 1321+新增约 90 token，余量足）。
- `phases/P6.md` duty 命令化（五步全文）：

```markdown
1. 脱敏提取：tanyin-knowledge client-map next --knowledge-dir <K>（分配 CLIENT-NN）
   → 草稿页按契约 14 写入 <K>/staging/pages/（域名→CLIENT-NN，IP/凭据/token→占位符）。
2. 反向验证：tanyin-redact --goal-dir <D> --reverse-verify（缺省 target=report/report-draft.md）。
3. 用户审批（双锚）：ledger-approve --knowledge（approvals.tsv 落 knowledge-approved 行——交战区侧）
   + tanyin-knowledge approve --knowledge-dir <K> --page <id> --approver <名>（库侧 log.md）。
4. 写入知识库：tanyin-knowledge commit --page <id> → export（graph.ndjson 重建）。
5. lint 保鲜：tanyin-knowledge lint --freshness-days 180 --today <T>（陈旧模式命中请重验）。
```

- `phases/P3.md` asset-added 回边行补：`→ Nday 匹配（tanyin-knowledge nday-match --cpe=<assets.meta 指纹> --version=<v>，命中→add-intent --kind=nday-verify --via=<cve_id>；G-18 引擎映射=nuclei）`。
- `recon.md` A8 行补：`跨 session 关联查询=tanyin-knowledge neighbors --entity=<指纹>（K2 实体页知识图谱）；组件指纹落 assets.meta=cpe:<vendor>:<product>;v=<版本>（nday 通路输入）`。
- `cli/README.md` 批次 5 节：交付清单+13 子命令速查表+用法四行（init/流水线/match/nday）+测试命令+--knowledge-dir 语义与种子库只读纪律。
- b5 台账四节（计划原文誊录=本计划「探知项」节；实施期增补留空待执行回填；状态归并；移交清单含 VulnClaw 批 6 三项登记）。
- `docs/HANDOFF.md`：状态快照增批次 5 行；开发流水 T1-T19 逐任务记账。

- [ ] **Step 3: 跑绿+全量+金样**

Run: `python3 -m unittest discover -s tests` 全绿；`python3 tests/run_golden.py` 零漂移（SKILL/phases md 非金样面；phases-validate.norm 稳定确认）。

- [ ] **Step 4: 出口验收实跑+commit+push**

出口验收清单（下方整批清单）逐条实跑，结果记入 HANDOFF 状态快照行。

```bash
git add SKILL.md phases/P6.md phases/P3.md engines/web-blackbox/phases/recon.md cli/README.md docs/design/2026-09-24-b5-discovery-notes.md docs/design/2026-09-24-b4-discovery-notes.md docs/HANDOFF.md tests/test_skill_resident.py
git commit -m "批次5 T19：总控接线收口——SKILL 路由表知识库行（<2K 复测）+P6 duty 命令化五步（client-map/reverse-verify/双锚审批/commit+export/保鲜 lint）+P3 nday 通路+recon A8 邻居查询接点；cli/README 批次5节；b5 台账 G-29..G-35 落盘+b4 台账五行闭环注记；HANDOFF 记账+出口验收 10 条实测"
git push origin main
```

---

## 出口验收清单（批次 5 整批出口；逐条附判定命令）

> 对应 §11 批次 5 行：**双知识库抽查通过（§9.4）；反向验证零命中**；不绿不放行。

| # | 验收项 | 判定命令（仓库根执行） | 通过判据 |
|---|---|---|---|
| ① | 双知识库抽查——CNPEN 库 | `python3 tests/eval_knowledge_spotcheck.py --knowledge-dir knowledge --origin cnpen --today 2026-09-24` | exit 0：四判据全过（字段完整/指纹自反可检索/无跨客户残留/CVE 标记） |
| ② | 双知识库抽查——外部库 | `python3 tests/eval_knowledge_spotcheck.py --knowledge-dir knowledge --origin external --today 2026-09-24` | exit 0：四判据全过+CVE 核验标记齐全（verified_at 无未来时间戳） |
| ③ | 反向验证零命中 | `python3 tests/eval_reverse_verify.py --goal-dir tests/fixtures/G-g1` | exit 0 且输出含 dirty=detected 与 clean=zero-hits（双向断言） |
| ④ | 六探知项裁决落地 | `python3 -m unittest tests.test_intents_columns_b5 tests.test_replay_timestamp tests.test_authz_cap tests.test_trigger_audit_v2 tests.test_converge_reachable tests.test_attack_paths_ev -v` | 全 PASS（G-24/G-27 双列、G-23 时间戳、R6 cap、G-27 逐对+高危横向、G-28 结构性停机+攻击链 EV） |
| ⑤ | 知识流水线机检 | `python3 -m unittest tests.test_knowledge_init tests.test_knowledge_staging tests.test_knowledge_export_match tests.test_knowledge_promote tests.test_k1_baseline_score tests.test_nday_match tests.test_reverse_verify -v` | 全 PASS（init 幂等/lint 四件/export 字节确定/四门槛/算分/离线匹配/P6 门端到端） |
| ⑥ | 全套单测 | `python3 -m unittest discover -s tests` | 全绿（批 4 基线 414+本批新增；零 skip 除声明 ENV 例） |
| ⑦ | 金样零漂移（除声明面） | `python3 tests/run_golden.py && git status --short tests/golden/` | 除任务内声明面（intents 列重铸/read-converge-check 计数行/read-set-replay-state 时间戳转参/kn 三面种子增长）外工作树干净；两次执行确定性自证 |
| ⑧ | 双平台 CI（含金样步） | `git push origin main` 后查 GitHub Actions | 四格矩阵（ubuntu/windows × 3.11/3.12）Unit tests+Golden regression 两步全绿 |
| ⑨ | 常驻集预算+接线 | `python3 -m unittest tests.test_skill_resident -v` | SKILL.md <2000 token（含批次 5 接线）；八节/44 索引/引用⊆已知面/路由表知识库行全过 |
| ⑩ | 台账+HANDOFF | `test -f docs/design/2026-09-24-b5-discovery-notes.md && grep -c 'G-2[9]\|G-3[0-5]' docs/design/2026-09-24-b5-discovery-notes.md` | 文件在场且 ≥7 条登记；HANDOFF 开发流水 T1-T19 记账齐 |

**补充判定（飞轮完整性，并入⑤）**：`python3 cli/tanyin-knowledge lint --knowledge-dir knowledge --today 2026-09-24` exit 0（种子库全页机检过）；`python3 cli/tanyin-knowledge export --knowledge-dir <临时副本>` 两次执行输出文件 sha256 一致（graph.ndjson 确定性）。

---

## 探知项（新接口缺口——批 5 起草期发现，登记 G-29..G-35 续编）

| # | 缺口 | 影响 | 本批处置 | 建议裁决 |
|---|---|---|---|---|
| G-29 | **知识页 ID 命名空间与账本铸造权边界**：KP-/STG-/CP-/PR-/EN-/TG-/PT-/RT-/BZ- 九前缀不在账本前缀表（设计 §4.1），ledger-next-id 不适用 | 知识页 ID 分配无契约依据，存在与账本 ID 混流风险 | 契约 14 §6 冻结知识库自有前缀表+tanyin-knowledge 内部 next_page_id 机械分配（四位零填充字典序=时间序——账本同精神不同源） | 已随 T1 裁决落地；账本/知识库命名空间永不分流混用 |
| G-30 | **语义近重复合并无载体**：VulnClaw distiller 0.88 嵌入余弦阈值需嵌入模型，stdlib 零依赖环境不可得 | 同义知识页可能随飞轮累积冗余 | R10：v1 规范哈希精确去重+lint 同 class 页数 ≥8 输出「人审合并建议」告警 | 批次 6+ 有先例数据与检索基线后裁决（BM25/嵌入双轨——VulnClaw 分析 §6.3 已登记可行架构） |
| G-31 | **CNPEN 全景图素材落位歧义**（夹具素材 vs 知识库膨胀） | 全景图进库则库内出现非知识内容（矩阵样例/夹具素材） | 裁决：知识库 sources 只登记映射指针行；夹具/矩阵样例素材归 tests/fixtures（防库膨胀） | 已随 T16 落地 |
| G-32 | **CVE 快照刷新流程缺位**（谁/何时/多大幅度刷新 cve-snapshot.tsv） | 快照时效衰减 → nday 漏报 | 本批 cve/README.md 冻结纪律：人工重铸整文件+首行刷新日期注记+lint 七列校验；nday 输出必附快照日期供审计 | 批次 6 安装器期裁决自动刷新通道（联网边界内=下载快照文件，非交互核验） |
| G-33 | **库外 ingestion 审批与交战区 approvals 双锚一致性无机检**（approve --knowledge 落交战区 approvals.tsv、knowledge log.md 落库侧，两账本独立） | P6 沉淀可能只落一侧（审计断链） | R8/R13：P6 duty 命令化双写（gate 查交战区侧、库侧 lint 查 log 行） | 双侧行互证机检留批次 6 evals |
| G-34 | **match 窗口判定基准日无源**（先例窗口「过期自动失效」需「今天」作判据） | 墙钟进判定 = 非确定性（金样/审计弱化） | 裁决：--today 必填显式传入（缺省 exit 2）；总控以 timeline 最近时间戳为 today 源（P2 开局调用约定写进 P6/P2 md） | 已随 T11 落地；批次 6 evals 统一 today 注入口径 |
| G-35 | **BugHunter/Threatswarm/CEP 三源仓库获取与许可核验时点**（.research/repos/ 当前仅 VulnClaw 在场） | 外部库语源不全（hunt-* 模板/27 agent 语料/CEP ROE） | T17 降级登记：SOURCES.tsv 落 origin 行+note=待补——不造数据、不阻塞出口①②（抽查以在库页为准） | 执行期 clone 至 .research/repos/&lt;name&gt;+MIT 逐一核验（LICENSE 文件在场）后补蒸馏；长期=批次 6 安装器 vendor 清单化 |

## 与批次 4 交付物的接点（执行者须知）

| 批 4 交付物 | 批 5 接点 |
|---|---|
| trigger-audit（批4 T13/T14） | T6 升级②逐对配对（消费 T3 cred 列）+新增④高危横向机检——检查面 3→5、PROTOCOL §5 注记；TRIGGERS.md 目录行集合与语义零变（版本不 bump，机检落地是执法面不是目录面） |
| K1 基线表缺位（fb72cd5 优先级调度） | T12 落表（k1-baseline.tsv 12+4 行）+tanyin-knowledge score 只读算分——P3.md 算分节读侧勘误；intents.priority 物理列 T3 落（15→17 一次重铸，cred 列同批 = G-27 合笔） |
| 图查询三命令（71d3b7c） | T7 抽 reachable_gap_cells 公共函数（graph-horizon 行为零变——金样 graph-graph-horizon.norm 验证）；T8 graph-paths 输出进 EV（攻击链升格证据）；recon A8 外推消费 T11 neighbors（知识图谱侧三元组） |
| AUTHZ_DIFF_PAIR_CAP 双载文档（R6 机检缺口，挂 G-20） | T5 落代码常量+add-intent 同端点计数拒收+测试锚定；differential.md/P3.md 双载文档转单源指针；契约 04 constants 同批（T2） |
| POC 重放门（批4 T4/T5） | T4 G-23 时间戳通道 = 重放门转强制后的墙钟收口（评审收尾 6d3a033 过渡手法转正）；diff-authz 夹具重铸声明随 T3 同批 |
| 44 命令面+tools.lock 三键+TEST-ONLY 钥 | 命令面零新增（本批新工具非账本命令）；tools.lock 零触碰（CVE 快照=数据文件非工具；无新外部依赖） |
| G 台账（b4-discovery-notes） | G-23/G-24/G-26/G-27/G-28/R6 终态改「已闭环·批次 5」（T19 在 b4 台账状态归并表就地注记——追加注记不改历史行，G-2 先例） |

## 移交清单（批次 6 开工前必办）

- **VulnClaw 批 6 三项登记（只登记不实现）**：①headless 退出码第 3 态（0=干净/1=事故/2=≥1 verified/3=仅候选——「仅未验证候选」态是否纳入 TanYin 0/1/2 契约，headless.py:36-45）；②findings.json（全量+lifecycle）+findings.sarif（仅 verified）双工件与 EV 卡片↔SARIF artifactLocation 映射（findings_output.py:330-352/:186-193）；③报告内容过滤器（LLM 叙述段进报告前机械清洗——剥工具调用痕迹/轮次标记/think 标签，report/filter.py 同型）。
- **批次 6 前必裁决/定标**：G-22（生产 EC 钥+重签+release.pub 替换+upstream commit 换真）、G-25（Burp 粘贴格式边界——渲染器）、G-21（Cytoscape.js vendor 复裁）、批次 3 遗留 G-4/G-11 定标、本批新登记 G-30/G-32/G-33。
- **持续飞轮（内容生产，不再动代码）**：VulnClaw 余 39 专题蒸馏（首批 8 页外）、CNPEN 素材五类缺补登记、BugHunter/Threatswarm/CEP 三源到位后补蒸馏——全走本批 staging 流水线（register→蒸馏→lint→approve→commit→export）。

## Self-Review（计划起草者自查记录）

1. **规格覆盖**：§11 批次 5 行逐件——staging（T10/T11）/lint（T10）/四门槛（T9 checklist+T13 机检）/三元组（T1 契约+T11 match/export）/CLIENT-NN（T15 client-map+R12）/graph.ndjson（T11 export）/CNPEN 82（T16）/外部语料 BugHunter/Threatswarm/CEP（T17）/CVE 联网核验（T14 快照+R11 边界+T17 标记核验）。出口两件——双知识库抽查（T18 ①②）/反向验证零命中（T15 载体+T18 ③）。批次间接口两件——技法页/先例页 front-matter schema（T1 契约 14 六类全表）/词表版本化（R14+T10 lint+T12 基线表 vocab_version 列）。六探知项——G-24（裁决 A+T3+T12）/G-26（裁决 B 零代码+数据文件承载）/G-27（裁决 C+T3+T6）/G-28（裁决 D+T7+T8）/G-23（裁决 E+T4）/R6（裁决 F+T5）。§7.1 飞轮四机制——ingest（T10/T11+SKILL 摄入触发）/P6 脱敏沉淀（T15+T19 命令化）/learned→core 四门槛（T13）/lint 保鲜（T13 freshness+R11 stale 降权）。§7.2 语料表五行——CNPEN 五类落位（T16）/nuclei+PortSwigger（nuclei 已批4 adopt；PortSwigger WSA 归持续飞轮移交）/外部三源（T17）/CVE 行（T14）。完备性 K1-K8 八类（T9 目录+T1 §1 映射+T12 K1+T14 K3+T16/T17 K2/K5/K6/K7/K8 内容）。§9.4 四判据（T18）。入库纪律四步 脱敏→机器检查→人工审→四门槛（T10 lint/T9 checklist/T13）。VulnClaw 批 6 三项只登记（移交清单）。无遗漏。
2. **占位符扫描**：全文无 TBD/TODO/「适当处理」；代码步给全文或逐段骨架+落地注记（测试内 `...` 均为「其余用例同构」显式声明）；内容生产任务（T16/T17）给示范页全文+映射表+页数下限+判定命令；素材缺失路径显式（blocked 上报/降级登记，不造数据）；两个 eval 脚本给可运行骨架。
3. **类型一致**：intents 17 列字段序（…reason, priority, cred, schema_version, created）T3 定义、T6 消费 cred 列名一致；reachable_gap_cells 返回 (reach, reach_gaps, unreach_gaps) T7 定义、T12 消费 reach 集一致；special.scan_text 签名 T10 定义、T13/T15 消费一致；dedup_key(kind, vuln_class, title) T10 定义、T11 commit 终检一致；KN_CMDS 金样面 kn-export/kn-match（T11）+kn-nday（T14）命名一致；契约 14 六类 kind 值（technique/precedent/entity/retro/pattern/business）与 PAGE_SCHEMAS 键、T16/T17 蒸馏页 kind 值三处一致；K1 键集（wstg-* 12 类+子类 wstg-XX:sub 形）T12 定义、T16 vocab-baseline 断言、score 查表次序三处一致。

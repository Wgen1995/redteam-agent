# 06 证据与外置卡片契约（E-index + EV/FD 卡片，接口⑦⑧）

> 来源：定稿 §4.9 · §4.11（辅引 §2.1/§4.1/§4.2/§4.7/§5.2/§5.3/§6.6，随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口⑦（POC 四要素＋EV/FD 卡片 front-matter 契约，§4.11）与接口⑧（findings 字段＋FD 卡片六字段映射，§4.7/§4.11）以及 E-index.tsv 全字段（§4.9）的誊录件（定稿 §11 批次 0 行）。只誊不创：全部语义来自定稿；「类型」列为依定稿示例/语义给出的标注（定稿未逐列定义物理类型，未标注处一律为文本）；「枚举/约束」「说明」列均为定稿原文语义。

## 1 双轨原则（ADR-P4①，§0.2 决策 2/§4.11）

- 嵌套走「TSV 索引行＋外置卡片」双轨（§0.2 决策 2）。
- 映射规则（§4.11 原文）：卡片六字段中一切标量进 TSV 列、一切嵌套/富文本进卡片 front-matter，两处以 id/card_path 互链；**聚合器以 TSV 列为权威，卡片与 TSV 不一致＝P4 ledger-validate 失败（同值性校验）**。
- 铁律 4（§2.1）：所有证据带 repro_command＋content_hash 双轨（raw＋norm）；无可复现步骤（reproducible_steps≥1）的观察一律是 fact 而非 finding。
- 设计决策 7（§0.2）：E-index 含 POC 四要素＋P4 独立重放门（三态）——「复现四要素只是口号」是行业实证报告的普遍缺口，四要素必须结构性落账。

## 2 E-index.tsv 全字段（16 字段，§4.9）

性质：纯追加（只增不覆盖）· 写入命令：ledger-add-evidence（§4.2 表 #9）。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 EV（§4.1 前缀表）；`{前缀}-{goal-id}-{四位序号}` 定宽零填充，ledger-next-id 原子分配 | 证据唯一标识 |
| title | 文本 | — | 证据标题 |
| source_type | 枚举 | ∈{command,capture,file,log,manual} | 证据来源类型 |
| observed_at | 时间戳 | — | 观察时间 |
| network_position | 枚举 | ∈{internet,intranet,same-host,jumphost:`<name>`} | POC 四要素之一进列——网络位置声明是中文报告被质疑复现不了的第一大原因 |
| repro_command | 文本 | 第三方可跑；凭据一律 `{{vault:cred-N}}` 占位符 | 复现命令 |
| repro_kind | 枚举 | ∈{single,sequence,concurrent} | 时序类引用 artifact 内并发脚本 |
| content_hash_raw | 文本（哈希） | content_hash 双轨之一 | 原始内容哈希 |
| content_hash_norm | 文本（哈希） | content_hash 双轨之二 | 归一化（去 nonce/时间戳）后哈希 |
| artifact_path | 路径 | 只增不覆盖（重跑另存 -r2） | 证据工件路径 |
| card_path | 路径 | →外置证据卡片 | 嵌套四要素部分（§4.11） |
| linked_finding | 文本（行 id 引用） | 引用 FD | 关联 finding |
| pair_group | 文本 | 差分组 | 差分举证分组 |
| raw_excerpt | 文本 | 脱敏＋定长截断 | 原始摘录 |
| schema_version | 整数 | ＝2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

## 3 POC 四要素（接口⑦，§4.9/§4.11）

| # | 要素 | 落位（字段） | 约束（定稿原文语义） |
|---|---|---|---|
| ① | 网络位置 | E-index.tsv `network_position` 列；EV 卡片 front-matter 复核同值 | ∈{internet,intranet,same-host,jumphost:`<name>`}；网络位置声明是中文报告被质疑复现不了的第一大原因 |
| ② | 前置条件 | EV 卡片 `preconditions`（列表，外置） | 如「可解析目标内网域名（DNS 内网视角）」「持有有效会话 {{vault:cred-3}}（对照组用）」 |
| ③ | 原始请求 | EV 卡片 `raw_request` | 凭据占位符化，Content-Length 精确标注 |
| ④ | 预期结果 | EV 卡片 `expected` | matcher/extractor；schema 以 nuclei matcher 为范本 |

## 4 EV 卡片（evidence/EV-{id}.md，承载 POC 四要素嵌套部分，§4.11）

front-matter 11 字段：

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 如 EV-g1-0041 | 与 E-index.tsv 行 id 互链 |
| title | 文本 | 如「管理接口未授权访问-实验组」 | 标题 |
| source_type | 枚举 | 同 E-index.source_type | 标量已进 TSV；卡片复核同值 |
| observed_at | 时间戳 | 如 2026-09-21T10:22:05+08:00 | 标量已进 TSV；卡片复核同值 |
| network_position | 枚举 | 同 E-index.network_position | 标量已进 TSV；卡片复核同值 |
| preconditions | 列表 | POC 四要素之二（列表，外置） | 前置条件 |
| raw_request | 富文本 | POC 四要素之三 | 原始请求（凭据占位符化，Content-Length 精确标注） |
| expected | 嵌套 | POC 四要素之四：matcher/extractor（schema 以 nuclei matcher 为范本） | matchers：{type: word, words:[…]}、{type: status, status:[200]}；extractors：{type: regex, name, regex} |
| cleanup | 文本 | `revert_cmd@timeline 事件引用` | 清理并入 revert 登记，不另设字段 |
| pair_group | 文本 | 差分组（如 PG-7） | 与 E-index.pair_group 同值 |
| role | 文本 | authz-diff 证据专用 | 本请求使用的角色（如 admin） |

正文段（1 个，§4.11 原文）：`## 原始响应摘录（脱敏+定长）与判定依据`。

配套约束：

- 证据工件：evidence/EV-*.md＋EV-*.raw（§3.4 目录树）。
- authz finding 的 EV 卡片 expected.matcher 必填角色/数据标识，P4 重放门验证（§6.6 第 4 条）。

## 5 FD 卡片（findings-cards/FD-{id}.md，§4.11）

front-matter 11 字段（六字段以①–⑥标注，映射见 §6）：

| 字段 | 六字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|---|
| id | — | 文本 | 如 FD-g1-0001 | 与 findings.tsv 行 id 互链 |
| dedup_key | ① | 文本 | 命令计算，与 TSV 列同值 | 如 `AST-g1-009+wstg-authz-bola` |
| scope_check | ② | 枚举 | 与 TSV 列同值；∈{in_scope,boundary-verified}（§4.7） | 范围判定 |
| exploitation_status | ③ | 枚举 | 与 TSV 列同值，重放门维护；∈{verified,suspected,ruled_out}（§4.7） | 利用状态（Strix 三态） |
| confidence | ④ | 枚举 | 四级（C1/C2/C3/➖🛑）（§2.1/§4.7） | 两维评级之一 |
| impact | — | 枚举 | ∈{高,中,低}（§4.7） | 两维评级之二（CVSS 式影响域） |
| auth_context | ⑤ | 文本 | 与 TSV 列同值；空（未认证）或 `CRED-{id}`（§4.7） | 身份矩阵差分产物 |
| control_evidence_ids | ⑥ | 列表 | ≡control_evidence_ids（control≡counterevidence 统一命名） | 反证证据（如 [EV-g1-0042]） |
| evidence_ids | — | 列表 | 多值（§4.7 同名列） | 支持证据（如 [EV-g1-0041, EV-g1-0042]） |
| pair_group | — | 文本 | 差分组（如 PG-7） | 差分举证分组 |
| affected_asset_id | — | 文本 | 引用 AST（如 AST-g1-009） | 受影响资产 |

正文段（3 个，§4.11 原文）：

1. `## 漏洞叙述`——LLM 撰写，只能引用账本已有数据，禁新增事实。
2. `## 复现步骤`——引用 EV 卡片 POC 四要素，不复制原文。
3. `## 修复建议叙述`——LLM 撰写；进入报告的部分由聚合器裁剪引用。

## 6 FD 六字段映射表（接口⑧，§4.11→§4.7 findings.tsv）

| # | 卡片 front-matter 字段 | findings.tsv 列（§4.7） | 同值性约束（§4.11 原文） |
|---|---|---|---|
| ① | dedup_key | dedup_key | 字段①：命令计算，与 TSV 列同值 |
| ② | scope_check | scope_check | 字段②：与 TSV 列同值 |
| ③ | exploitation_status | exploitation_status | 字段③：与 TSV 列同值，重放门维护 |
| ④ | confidence | confidence | 字段④：四级（C1/C2/C3/➖🛑） |
| ⑤ | auth_context | auth_context | 字段⑤：与 TSV 列同值 |
| ⑥ | control_evidence_ids | control_evidence_ids | 字段⑥：≡control_evidence_ids（统一命名） |

聚合器以 TSV 列为权威；卡片与 TSV 不一致＝P4 ledger-validate 失败（同值性校验，§4.11）。

## 7 重放门联动（§5.2 P4/§5.3/§0.2 决策 7）

- P4 独立重放门（批次 4 起强制）：fresh 隔离子代理只拿 EV 卡片盲重放，set-replay-state 三态（VERIFIED/REPAIRED/REJECTED）落账。
- VERIFIED 才维持 C1，REJECTED 降 C3 或转 fact（§4.7 exploitation_status/§5.3 校验命令）。
- 重放＝REPAIRED 时修复 POC 卡片后重放，max_retry=2（§5.2 back_edges）。

## 探知项（待仲裁）

1. 四要素落位表述冲突：§4.2 表 #9（E-index 行）定稿要点「＋network_position/card_path；**四要素进卡片**」vs §4.9「network_position……（**POC 四要素之一进列**）」及 §4.11 EV 卡片注释「network_position: 标量已进 TSV；卡片复核同值」——要素①网络位置以 TSV 列为唯一落位还是以卡片为准，两处字面不一致（§4.11 映射规则口径为「标量进 TSV 列」），待仲裁。

## 自验

命令实跑证据（D＝/Users/wgen/redteam-agent/docs/design/2026-09-21-tanyin-v2-design.md，本文件＝contracts/06-evidence-cards.md）：

- E-index 字段数对照：`awk 'NR==251' $D | tr ',' '\n' | grep -c .` → **16**；本文件 §2 表 `awk '/^## 2 E-index/,/^## 3 POC/' 本文件 | grep -c '^| '` → 17（含表头 1 行）＝数据行 **16/16**，逐名一致（id/title/source_type/observed_at/network_position/repro_command/repro_kind/content_hash_raw/content_hash_norm/artifact_path/card_path/linked_finding/pair_group/raw_excerpt/schema_version/created）。
- EV 卡片 front-matter 键数：`sed -n '292,312p' $D | grep -cE '^[a-z_]+:'` → **11**；本文件 §4 表 → 12−表头 1＝**11**。
- FD 卡片 front-matter 键数：`sed -n '272,283p' $D | grep -cE '^[a-z_]+:'` → **11**；本文件 §5 表 → 12−表头 1＝**11**。
- FD 六字段映射齐全：定稿 §4.7 字段行（L236）逐名 grep → dedup_key=1/scope_check=1/exploitation_status=1/confidence=1/auth_context=1/control_evidence_ids=1（**6/6 命中**）；本文件 §6 映射表 → 7−表头 1＝**6** 行（①–⑥）。
- POC 四要素＝**4**（§3 表：network_position/preconditions/raw_request/expected）。
- 探知项＝**1**。

## v2 勘误补记（2026-09-24·批次 4 施工期·T4/R1 裁决）

- §4 POC 四要素之 `expected` 子集 v1 冻结（探知项 G-17 清账，R1 裁决原文）：`expected.matchers` 仅 `{type: word, words[], condition: or|and}`（condition 可省，**默认 and**）与 `{type: status, status[]}`；`expected.extractors` 仅 `{type: regex, name, regex[]}`（评估取 regex[0]：有捕获组取组 1，无捕获组取整体匹配）。多 matcher 语义＝**全部命中**（AND）；type 不在子集＝**REJECT**（fail-closed——评估器 raise MatcherError，由调用方转 REJECT）；`expected` 缺失或空＝**manual**（无 matcher 无法机械判定，人工）。评估单一实现＝cli/ledger/matchers.py（T5 重放三态判定消费）；EV 卡片 front-matter 解析＝cli/ledger/cards.py（复用 phases_engine 受限 YAML 子集；§4.11 同值性校验＝cards.check_consistency，执法点=重放前校验——G-16：validate 集成不动）。微版本勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 5 施工期·T2/G-16 结案）

- G-16 结案——EV 卡片↔E-index 同值性执法**维持 replay 侧单点**（cards.check_consistency，执法点=重放前校验；498d8c2 在册）；validate --with-cards 不增（遍历交战区 card_path 成本>收益，单点已闭环）——上则 R1 注「G-16：validate 集成不动」就此结案。微版本勘误，不升 schema_version，索引见 contracts/README.md。

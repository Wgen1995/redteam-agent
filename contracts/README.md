# 探隐契约冻结（批次 0）

> **状态**：✅ 已冻结（git tag contracts-v2 · 2026-09-23）· schema_version=2 · 来源：docs/design/2026-09-21-tanyin-v2-design.md（评审通过版+当日终审裁决）
> **冻结规则**：①只誊不创——定稿为唯一来源，契约不得新增/删减语义；②抽取中发现定稿内部矛盾→登记文末"探知项"待仲裁；③冻结（git tag contracts-v2）后任何变更走 schema_version 递增+迁移命令，禁止直接改。

## 16 项接口 ↔ 契约文件对照

| # | 接口 | 契约文件 | 定稿来源 |
|---|---|---|---|
| ① | 13 表 schema 全字段 | 01-ledger-schema.md | §4.2-§4.10 |
| ② | 10 边词汇 | 01-ledger-schema.md | §4.8 |
| ③ | 37 条账本命令签名 | 02-commands.md | §5.3+附录 A |
| ④ | {{vault:cred-N}} 占位符+vault 条目格式 | 03-credentials.md | §8.4 |
| ⑤ | phases.yaml schema+九门断言 | 04-phases.md | §5.2 |
| ⑥ | scope schema（include/exclude/oob/account-grant/amendment_of） | 05-scope.md | §4+§8.5+§5.4 |
| ⑦ | POC 四要素+EV/FD 卡片 front-matter | 06-evidence-cards.md | §4.9/§4.11 |
| ⑧ | findings 字段+FD 六字段映射 | 06-evidence-cards.md | §4.7/§4.11 |
| ⑨ | 统一提交 schema | 07-submission.md | §6.1 |
| ⑩ | manifest 模板+纪律能力声明 | 08-manifest.md | §6.3 |
| ⑪ | CLI 工具箱命令面+铁律 7 边界 | 09-cli-surface.md | §2.4 |
| ⑫ | tools.lock 格式+ECDSA 验签 | 10-toolchain-lock.md | §10.1 |
| ⑬ | creds 契约（kind 二分/material meta 位/authz-diff 语义） | 03-credentials.md | §4.10+§6.6（评审裁决已并入） |
| ⑭ | 四层执法档位表+egress compile IO | 11-enforcement.md | §8.5 |
| ⑮ | 安装矩阵布局+交战区路径约定 | 12-install-layout.md | §10.1-§10.3 |
| ⑯ | 报告模板章节骨架（中文合规六要素） | 13-report-template.md | §11 契约⑯ |

## 契约清单增补（批次间接口·批次 5 起）

| # | 接口 | 契约文件 | 定稿来源 |
|---|---|---|---|
| ⑰ | 知识库 schema（六类页 front-matter 全集/三元组/staging 状态机/四门槛/CLIENT-NN/graph.ndjson 行 schema/ID 前缀表/词表版本化/许可纪律） | 14-knowledge-schema.md | §3.4/§7.1/§7.2/§9.4+完备性 K1-K8（批次 5 冻结；format_version=kn-v1） |

## 评审裁决已并入（2026-09-23 导读评审）

- revert_cmd 分层：外部副作用必登（无逆者 irreversible+L3）/纯账本免登（§0 决策 #4/§4.10/P6.0）
- creds：kind 二分不变+material meta 位（ntlm-hash|ssh-key|x509）→ 契约⑬
- 首批实测三宿主（DSH/opencode/codex）；walcode/CodeBuddy 装得上+披露未实测 → 契约⑮
- token 效率门首版告警、批次 6 前转硬门（验收口径，非本批契约）
## 冻结范围注记（2026-09-23 评审确认）

- 知识库契约（技法页/先例页 front-matter、graph.ndjson 格式、四门槛晋升）按定稿设计**留批次 5 冻结**——批次 1-4 不依赖，非缺失。
- 37 条账本命令逐条签名：定稿仅载命令名与分类（附录 A 缺位），签名属起草项，处理方式待终审仲裁。

## 终审裁决记录（2026-09-23·冻结时并入）

1. 命令面 37→**41**（九门断言四条并入校验类；set-cred-status 归写入：写19/查11/校验10）。
2. kind 定死四值；amendment 走 amendment_of 链。
3. egress compile 输出四成分。
4. timeline/budget 补 schema_version、matrix 补 frozen_at、creds 补 material（142→146 字段）。
5. PG 规范形 / budget scope 分工 / score 空值语义 / 四要素卡片承载 / walcode·CodeBuddy Tier 1 起步。
6. vault 条目格式与 hash-recheck 范围等推导项随 02a/03 转正（【推导】标注保留可追溯）。
7. state.md 结构留批次 3 冻结；知识库 schema 留批次 5。

## v2 勘误（2026-09-23·批次 1 施工期）

- findings + 列（CVE/CWE/GHSA  分隔，非 Nday 留空）；intents kind 枚举 +；P3 第四生成源=组件指纹→Nday 候选 intent（匹配源离线=先例页+本地 CVE 快照，联网仅 P6 核验）。字段总数 146→**147**。零存量数据期勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 3 施工期）

- 契约⑨（09-cli-surface.md）工具面 10→**11**：增补第 11 工具 tanyin-phases（phases.yaml 确定性状态机运算；G-1 裁决，允许类=四类允许之首「确定性账本运算」）。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记。
- 契约 02a（02a-command-signatures-draft.md）§13 checkpoint 参数扩展（G-10：--timestamp/--session/--release/--round/--note/--spawn）与 state.md v2 十键行结构（G-6）回注。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记（批次 3 T13 收口）。

## v2 勘误补记（2026-09-24·批次 3 评审收尾）

- 契约⑨（09-cli-surface.md）tanyin-phases 子命令枚举三处 6→**7**：补第 7 子命令 denominator-ready（分母就绪门，PROTOCOL §4；Important-1）。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记。

## v2 勘误补记（2026-09-24·批次 4 施工期·T1/G-12 裁决）

- 契约①（01-ledger-schema.md）§3.6 assets.type 枚举九值→**十一值**（+cloud-storage/human-factor，细分落 meta=sub:…；§1 变更表第 6 行要点同步）。微版本勘误，不升 schema_version。
- 契约⑨（07-submission.md）§2 assets[].type 枚举串同步十一值。微版本勘误，不升 schema_version。
- 契约 02a（02a-command-signatures-draft.md）§8 add-asset 拒收条件改十一值枚举；「pivot/foothold 批次 4 前启用=REJECT」分支退役（§4.8 兑现）。微版本勘误，不升 schema_version。
- phases/PROTOCOL.md §4 类映射补 cloud-storage→A5、human-factor→A7 两行（G 台账 G-12 清账，原「A5/A7 无对应值」注记作废）。

## v2 勘误补记（2026-09-24·批次 4 施工期·T2/G-2 裁决）

- 契约 02a（02a-command-signatures-draft.md）§12 matrix-set 拒收条件勘误：submatrix: 四条件放行新键行铸造（原子铸造新表面×VOCAB 全集行，timeline 事件 submatrix-mint）+reason 前缀规则修正（旧前缀空→任意前缀首次归类放行；旧前缀非空且≠新→REJECT——修 authz-diff 首次落格潜伏阻塞）。微版本勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 4 施工期·T3/P4 重放门转强制）

- 契约④（04-phases.md）门 5 · P4 断言 5（ledger-replay-summary）expect 文本去「（批次 4 前=SKIP，报告中披露）」——重放门断言转强制（断言数不变 asserts=21 基线不动）；phases/phases.yaml 同步、phases/PROTOCOL.md §1 判定表 SKIP 行加退役注记、phases/P4.md duty 3/4 改强制+历史注记。微版本勘误，不升 schema_version。
- 契约⑭（11-enforcement.md）§7「P4 出口」行 expect 引用随契约 04 同步去 SKIP 尾注（T3 裁决：计划文件清单未列该引用位，按声明层单源一致+每笔勘误必登记的全局纪律补齐）。微版本勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 4 施工期·T4/R1 裁决）

- 契约⑥（06-evidence-cards.md）§4 `expected` matcher 子集 v1 冻结（R1/G-17：matchers 仅 word/status＋多 matcher=AND＋未知 type fail-closed；extractors 仅 regex；空 expected＝manual）。微版本勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 4 施工期·图谱驱动增补 71d3b7c）

- 契约 02a（02a-command-signatures-draft.md）命令面 41→**44**（查询 11→14）：增补三条只读图查询命令 graph-neighbors/graph-paths/graph-horizon（邻接展开/可达路径枚举/可达集×矩阵空格 join；确定性账本运算，铁律 7 允许类；实现位 cli/ledger/graph_cmds.py，registry all_commands()=44 单源）。微版本勘误通道，零存量数据期，不升 schema_version——详见该文件文末勘误补记节。联动：SKILL.md 命令索引（41→44）/cli/README.md 命令面（查 11→14）/tests/test_phases_yaml.py 面数断言（41→44）随本笔勘误同步（声明层单源一致纪律）。依据：docs/design/2026-09-24-graph-driven-ops.md（用户批准设计增补，commit 71d3b7c）——原「41 命令面冻结：本批零新增账本命令」约束按该增补就该三命令例外放行。

## v2 勘误补记（2026-09-24·批次 4 施工期·T8/R5 裁决）

- 契约 02a（02a-command-signatures-draft.md）§3 add-intent（内部）status 行勘误：直达 pending 条件 `origin=recon-event` 扩为 `origin=recon-event 或 kind=authz-diff`（cred-obtained 事件处理器语义，设计 §6.6 步 1「直接 pending 不打分」；计划前置裁决 R5 随 T8 差分样例对落地）。微版本勘误，不升 schema_version——详见该文件文末勘误补记节。

## v2 勘误补记（2026-09-24·批次 4 施工期·T14 收口）

- 契约⑨（09-cli-surface.md）tanyin-phases 子命令枚举三处 7→**8**：补第 8 子命令 trigger-audit（触发器闭包审计，PROTOCOL §6；T13 交付枚举回注随 T14 收口——R-T13 附记移交件）。微版本勘误，不升 schema_version——详见该文件文末勘误补记。
- 契约①（01-ledger-schema.md）intents 增 **priority** 字段（派发优先级分=priority 公式：severity_expect×asset_value×exploitability，fb72cd5 优先级调度设计增补）：本批冻结语义与公式（冻结文本=phases/P3.md「派发优先级算分」节）；物理列（15→16 字段）与写路径/查询排序支撑随批次 5 G-24 基线表定案后落（T14 裁决：基线无源不落列+零存量数据期外重铸=金样大规模刷新与批 4 出口相抵；Top-K 选择=总控决策，铁律 7 边界 2）。微版本勘误，不升 schema_version。
- 契约⑨（07-submission.md）kind→段映射补注：nday-verify→引擎=nuclei（cli 型，无 web-blackbox 段映射）——G-18 清账（T9/T10 移交 T14 收口）；视角顶层 perspective 字段留契约 v3（G-19 过渡载体=network_position=same-host）。微版本勘误，不升 schema_version。
- phases/PROTOCOL.md §6 目录版本 v1→**v2**（TRIGGERS.md 高危 finding 即时横向触发器增补，fb72cd5）+SKILL P0 序列承载 triggers-catalog 事件落账；phases/P3.md 派发规则改写（priority 降序 Top-K+cred-obtained 回边全语义+asset-added G-2 命令形态）；phases/TRIGGERS.md 版本化封闭表 v2。同批声明层联动（SKILL.md 路由表三引擎/cli/README 批次 4 节八子命令面），金样零漂移（纯文档/契约层，不触命令面）。

## v2 勘误补记（2026-09-24·批次 5 施工期·T1）

- 契约清单增补批次间接口⑰=**14-knowledge-schema.md**（知识库 schema：六类页 front-matter 全集/先例三元组/staging 状态机/四门槛/CLIENT-NN/graph.ndjson 行 schema/ID 前缀表/词表版本化/许可纪律）——「冻结范围注记：知识库契约留批次 5 冻结」就位兑现；新建文件，非定稿接口变更。
- 契约⑨（09-cli-surface.md）工具面 11→**12**：增补第 12 工具 tanyin-knowledge（知识库机械运算 13 子命令；R7 裁决，允许类=「确定性账本运算」同型，G-1 10→11 先例同通道）。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记。

## v2 勘误补记（2026-09-24·批次 5 施工期·T2/契约 v3 首批集中清账）

- 契约 04（04-phases.md）三笔：constants 表增 `authz_diff_pair_cap: 24`（R6/G-20 文档常量回注；代码常量随批次 5 T5 落）+`restart_rate_minutes: 10`（G-3 回注，批次 3 T6 模块常量）——constants 8→10；门断言事件词汇补注 `gate-fail:<门> assert=<cmd 首词> reason=<一句>`（G-7，PROTOCOL §1.3 已冻结）；门 5 · P4 duty 增攻击链落证步注记（G-28 裁决 D，详文随 T8 落 phases/P4.md）。
- 契约 06（06-evidence-cards.md）一笔：G-16 结案——EV↔E-index 同值性执法维持 replay 侧单点（cards.check_consistency，498d8c2）；validate --with-cards 不增。
- 契约 07（07-submission.md）一笔：G-19 结案——submission 顶层 perspective 字段不开（147 字段口径外）；视角承载维持 findings[].network_position=same-host 过渡。
- 契约 09（09-cli-surface.md）一笔：canary/egress 干跑口径补注（G-8 清账）——egress 只 compile、canary 只 deploy 不 probe（PROTOCOL §3 已冻结）。
- 六笔全部微版本勘误通道，schema_version 保持 =2 不递增；G-23/G-24/G-26/G-27/G-28 五笔代码侧随 T3/T4/T5/T7 各自落账（契约 v3 待办清单第二批）。

## v2 勘误补记（2026-09-24·批次 5 施工期·T3/G-24+G-27）

- 契约①（01-ledger-schema.md）§3.3 intents.tsv **15→17 字段一次重铸**（G-24 priority+G-27 cred 合笔——只付一次夹具/金样重铸成本）：priority=派发优先级分物理列（0-1 可空，公式=§8.7 勘误冻结，tanyin-knowledge score 产出经 add-intent --priority 回填）；cred=凭据绑定物理列（任意 kind 非空即写前引用闭合，authz-diff 必填硬门保留）。批4 T14「物理列随批次 5 落」承诺兑现。
- 契约 02a（02a-command-signatures-draft.md）§3 add-intent 参数表/拒收条件/输出行同步（--priority 落列+--cred 落列与任意 kind 闭合+回显 17 字段）。
- 两笔均微版本勘误通道，schema_version 保持 =2 不递增；schemas.json intents.tsv 数组 17 项与契约 01 同步；夹具（G-g1/diff-authz）与金样一次重铸（变更面逐一归因两新列）。

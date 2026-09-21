# 02 账本命令面契约（37 条，接口③）

> 来源：定稿 §5.3（辅引 §3.2/§4.1–§4.11/§5.1–§5.2/§6.6/§8.4/§8.7/§9.2，随行标注；附录 A 定稿未载）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口③（37 条账本命令签名，附录 A 冻结，§11 批次 0 行）的誊录件。只誊不创：签名清单定稿规定冻结于 shared/LEDGER.md 附录 A（§5.3），**附录 A 不在定稿文内**——各命令「签名」列一律标『定稿未载→探知项』（探知项 1）；必填参数/输出/写前拒收条件仅誊录定稿散见语义，缺源处同样标『定稿未载→探知项』。

## 0 命令面总览（§5.3）

- 分组与计数：**写命令 18 ＋ 查询命令 12 ＋ 校验命令 6 ＋ 特殊 1（matrix-init）＝ 37**（§0.3 口径 2 同）。
- 实现载体：cli/tanyin-ledger（python3 ≥3.9 标准库薄 CLI，tools.lock 锁定，§5.3/§2.4）；总控经执行通道调用 `tanyin-ledger <cmd>`（§3.2 咬合点 1）；CLI 是账本唯一写入口（写前拒收内置，§3.2）。
- 通用纪律（§5.3）：写前拒收；查询输出摘要化（计数+top-N+ID 列表，禁全量回灌）；命令幂等；对外请求类前置 request-ticket。
- 写前拒收通用基线（§4.1/§5.2）：每条写命令自带行级校验（列数/ID 格式/枚举/转义/引用闭合/dedup_key 唯一），畸形 REJECT 不部分写入；Tier 0 硬门——无 goals 行时一切写命令 REJECT（P0「无授权只许读文档」）；参数经临时文件/stdin 传入，禁止字符串拼接进命令行（§4.1）。
- 命名约定：下表「命令」列给出 §5.3 短名；§4.2 写入命令列以 `ledger-` 前缀引用（如 ledger-add-goal）。前缀不一致见探知项 4。

## 1 账本写命令（18 条，§5.3）

| # | 命令 | 签名 | 必填参数（定稿载） | 输出（定稿载） | 写前拒收条件（定稿载） |
|---|---|---|---|---|---|
| 1 | add-goal（ledger-add-goal） | 附录 A：定稿未载→探知项 1 | goals 字段（§4.3）：授权结构化字段（auth_doc/auth_sha256/signer/valid_from/valid_until——空=REJECT）；budget 三元组 `token;requests;hours`；dollar_budget 空=第四维关；model_tier/guard_tier 安装自检写入；business_context=P0 业务问卷摘要 | goals.tsv 追加一行（每次测试一行，§4.3） | 授权结构化字段空=REJECT——不存在「先记上再补」（§4.3）＋通用基线 |
| 2 | add-scope（ledger-add-scope） | 附录 A：定稿未载→探知项 1 | kind∈{include,exclude,oob,account-grant}＋matcher（CIDR/域名后缀/通配，include/exclude 用）；account-grant 行另需 account＋permitted_actions（`;` 分隔）（§4.4） | scope.tsv 追加一行 | 专属条款定稿未载→探知项 5（include+exclude+oob 齐备由 P0 exit 的 ledger-scope-coverage 断言，非本命令拒收，§5.2） |
| 3 | add-intent（ledger-add-intent） | 附录 A：定稿未载→探知项 1 | intents 字段（§4.5）：title/engine/kind∈{recon,surface,matrix-test,deep-dive,authz-diff}/origin/budget_share=`token;requests;hours[;dollars]`；dedup_key 由命令机械计算（资产+技法类） | intents.tsv 追加一行（事件溯源） | 界外资产→REJECT（§4.4 账本级禁止派生 intent；§9.2 负向用例「界外资产喂 add-intent→REJECT」）；dedup_key 重复键 REJECT（§4.5）；authz-diff 派发硬门=总控校验 CRED 行 status=active 且 permitted_actions 覆盖计划动作（§4.10） |
| 4 | set-intent-status（ledger-set-intent-status） | 附录 A：定稿未载→探知项 1 | id＋新 status；reason（rejected/blocked/deferred 强制）；deferred 附 activation 谓词 `field;op;value`（§4.5） | 追加新行（事件溯源，「取最新」是账本命令，§4.1） | 专属条款定稿未载→探知项 5（语义约束：blocked 不可自动复活，复活须 approvals 引用，§4.5） |
| 5 | add-fact（ledger-add-fact） | 附录 A：定稿未载→探知项 1 | facts 字段（§4.6）：intent_id/kind∈{port,service,http,info,vuln-clue,authz}/target/detail/confidence 0-1 | facts.tsv 追加一行（detail 落账即脱敏，§4.6） | 落盘前掩码：redact 校验检出真值模式（cookie/token/密码形态）即 REJECT（§8.4 关卡 2 明列 ledger-add-fact）＋通用基线 |
| 6 | add-finding（ledger-add-finding） | 附录 A：定稿未载→探知项 1 | findings 字段（§4.7）：confidence×impact 两维、exploitation_status∈{verified,suspected,ruled_out}、auth_context、dedup_key（命令计算）、scope_check、description_brief≤200 字、reproducible_steps、evidence_ids/control_evidence_ids、card_path | findings.tsv 追加一行＋外置卡片（findings-cards/FD-{id}.md，§4.7/§4.11） | reproducible_steps≥1 强制（§4.7；铁律 4：无可复现步骤的观察一律是 fact）；redact 专属条款定稿未载→探知项 5（§8.4 关卡 2 明列者为 add-fact/add-evidence） |
| 7 | supersede-finding（ledger-supersede-finding） | 附录 A：定稿未载→探知项 1 | 被合并 finding 引用＋合并去向（supersedes 边；dedup_key 同键合并语义，§4.7） | supersedes 边＋tombstone（status=superseded），不删行（§4.1/§4.7） | 专属条款定稿未载→探知项 5（＋通用基线） |
| 8 | add-asset（ledger-add-asset） | 附录 A：定稿未载→探知项 1 | assets 字段（§4.8）：type∈{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold}/value/meta | assets.tsv 追加一行；in_scope 由 scope-check 判定 | 专属拒收条款定稿未载→探知项 5；注意：界外资产不 REJECT——强制对照 include/exclude，界外自动标 out_of_scope（§4.4），且账本级禁止派生 intent |
| 9 | add-edge（ledger-add-edge） | 附录 A：定稿未载→探知项 1 | edges 字段（§4.8）：kind∈10 边/source_id/target_id/provenance（来源：intent/引擎/人工） | edges.tsv 追加一行 | 通用基线具体化：kind 枚举校验＋引用闭合校验（§4.1）；专属条款定稿未载→探知项 5；新增边类型须 bump schema_version（§4.8） |
| 10 | add-evidence（ledger-add-evidence） | 附录 A：定稿未载→探知项 1 | E-index 字段（§4.9）：source_type/network_position∈{internet,intranet,same-host,jumphost:&lt;name&gt;}/repro_command（第三方可跑，凭据一律 `{{vault:cred-N}}` 占位符）/repro_kind/content_hash 双轨（raw+norm）/pair_group/raw_excerpt（脱敏+定长截断） | E-index.tsv 追加一行；artifact_path 只增不覆盖（重跑另存 -r2，§4.9）；四要素嵌套部分进 EV 卡片（§4.11） | 落盘前掩码：redact 校验检出真值模式即 REJECT（§8.4 关卡 2 明列 add-evidence）＋通用基线 |
| 11 | approve（ledger-approve） | 附录 A：定稿未载→探知项 1 | approvals 字段（§4.8）：command_hash/decision/approver/note；审批展示原始命令原文非 LLM 摘述；用法 --verify-signoff（P5.5 exit）、--knowledge（P6 exit）（§5.2） | approvals.tsv 追加一行（L3 逐条审批、P5.5 签发 command_hash 绑定聚合报告文件哈希、P6 知识审批、P6.0 残留豁免全落此表，§4.8） | 专属条款定稿未载→探知项 5（＋通用基线） |
| 12 | matrix-set（ledger-matrix-set） | 附录 A：定稿未载→探知项 1 | matrix 长表字段（§4.10）：attack_surface/vuln_class（WSTG v4.2 全集钉死）/state∈{x,?, -,!,空}/reason（子矩阵行前缀 `submatrix:`；authz-diff 前缀 `authz-diff:`）/intent_id | matrix.tsv 置格（事件溯源，updated；matrix-init 生成表，§4.2/§4.10） | 专属条款定稿未载→探知项 5（语义约束：P2 后主矩阵不随新资产扩张，新资产走子矩阵行，§4.10） |
| 13 | checkpoint | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5（P3 每轮 ⓪checkpoint+budget-check，§5.2） | state.md 写入：temp/rename 原子替换并带 revision 号（§4.1 kill -9 半写兜底）；非 13 表写入 | 专属条款定稿未载→探知项 5（护栏：单活跃会话约束 single_active_session=true，§5.2） |
| 14 | append-timeline（ledger-append-timeline） | 附录 A：定稿未载→探知项 1 | timeline 字段（§4.10）：timestamp/actor∈{总控,子代理,CLI,人工}/phase/event；revert_cmd 分层登记——外部副作用操作（碰目标系统：发请求/落文件/改配置）必填，无逆者填 `irreversible` 并强制 L3 逐条审批，纯账本状态变化留空（其逆=追加新行，§0.3 口径 4） | timeline.tsv 追加一行：prev_hash+hash 链式哈希，**哈希输入=本行全部字段含 revert_cmd**（改任何历史行即断链可见，§4.10）；对外请求记 `request:` 事件；P0 落 SKILL 版本+tools.lock 哈希；managed-restart 记 spawn 方式（auto/manual） | 专属条款定稿未载→探知项 5（断链由 verify-chain 事后检出） |
| 15 | matrix-freeze（ledger-matrix-freeze） | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5（P2 duty：matrix-init 后冻结，锚点冻结≠探索冻结） | frozen（§5.2 P2 exit expect「frozen（不可重复冻结）」） | 不可重复冻结（§5.2 P2 exit expect） |
| 16 | budget-log（ledger-budget-log） | 附录 A：定稿未载→探知项 1 | budget 字段（§4.10）：token_delta/requests_delta/hours_delta/dollars_delta（默认 0，第四维关闭不累计）/scope=`goal` 或 `INT-{id}`/note | budget.tsv 追加流水行（预算树：intent 消耗计入自身份额并上卷 goal 根，§4.10） | 专属条款定稿未载→探知项 5（intent 超份额→拒派为派发侧语义，§8.7） |
| 17 | add-cred（ledger-add-cred）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | creds 字段（§4.10）：kind∈{static-cred,session}/role（合法集合由 P0 八问⑧+account-grant 行确定）/username_ref/secret_ref=`{{vault:cred-N}}` 占位符/scope_asset/obtained_via_intent/parent_cred/valid_from/valid_until/permitted_actions | creds.tsv 追加一行（N=creds 行序号；真值永不进账本，§4.10）；P0 八问⑧落账位=creds(kind=static-cred)（§8.1） | 专属条款定稿未载→探知项 5（语义硬约束：真值永不进账本，secret_ref 必须为占位符，§4.10；§8.4 关卡 2 明列者为 add-fact/add-evidence） |
| 18 | amend-scope（ledger-amend-scope）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | amendment_of=被修订行 id；note=修订理由+批准人；P0 后修订必须伴随 approvals 行（§4.4） | 追加修订行（不删行不改行；生效判定=沿 amendment 链取最新，命令实现，§4.4） | 修订未经审批=账本级 REJECT（§5.2 P3 events scope-amended guardrails）＋通用基线 |

## 2 查询命令（12 条，§5.3）

只读命令无「写前拒收」语义（set-cred-status 兼具变更，见行内与探知项 2）；输出一律摘要化（计数+top-N+ID 列表，禁全量回灌，§5.3）。

| # | 命令 | 签名 | 必填参数（定稿载） | 输出（定稿载） | 写前拒收条件（定稿载） |
|---|---|---|---|---|---|
| 1 | unconsumed-facts | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | 未消费 fact 清单——无 derived_from 出边的 fact（§4.8）；P3 ①扫描步入口（§5.2） | —（只读） |
| 2 | pending-intents | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | pending 状态 intents 清单（status 状态机 §4.5；P3 ①扫描步，§5.2） | —（只读） |
| 3 | matrix-gaps | 附录 A：定稿未载→探知项 1 | --baseline（P2 用法，§5.2） | P2 exit expect「基线行数&gt;0 且覆盖全部 in_scope 攻击面」；空格清单（P3 ①扫描，§5.2） | —（只读） |
| 4 | converge-check | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | converged \| budget-exhausted（P3 exit expect，§5.2；两者皆合法终态）；收敛四条件可计算（§3.3；四条件清单定稿未列→探知项 6） | —（只读） |
| 5 | next-id（ledger-next-id） | 附录 A：定稿未载→探知项 1 | 前缀（G/S/INT/F/FD/AST/E/AP/EV/CRED/PG，§4.1） | 原子分配 ID：`{前缀}-{goal-id}-{四位序号}` 定宽零填充，字典序=时间序（§4.1）；子代理/引擎无铸造权 | —（只读分配） |
| 6 | intent-status | 附录 A：定稿未载→探知项 1 | intent id（推断自名称；定稿未显式载参数表→探知项 5） | intent 状态（事件溯源「取最新」是账本命令，§4.1） | —（只读） |
| 7 | matrix-get | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | 矩阵格查询（§5.3 仅列名；输出细节定稿未载→探知项 5） | —（只读） |
| 8 | scope-check | 附录 A：定稿未载→探知项 1 | --all-assets（P1 用法，§5.2） | P1 exit expect「全部资产已判定」；判定=CIDR/后缀机械匹配（非 LLM，§4.4）；Tier 0 职能之一：scope-check 内联（§8.5） | —（只读） |
| 9 | budget-check | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | 对照 goals 三元组+各叶份额输出树形余量（§4.10）；不豁免测绘 intents（§8.7）；P3 ⓪步（§5.2） | —（只读） |
| 10 | cleanup-checklist | 附录 A：定稿未载→探知项 1 | --verify（P6.0 用法，§5.2） | 从 timeline 提取全部外部副作用写操作（revert_cmd 非空行）→逆序执行 revert_cmd；--verify expect「全部 reverted 或 豁免行齐备」（§5.2 P6.0）；纯账本状态行无需回滚 | —（只读清单；执行 revert 属清理动作） |
| 11 | set-cred-status（ledger-set-cred-status）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | creds 行 id＋新 status（推断自语义；参数表定稿未载→探知项 5） | creds 事件溯源状态查询/变更（§5.3 原文）；status∈{active,expired,invalidated,revoked}（§4.10）；会话过期→creds 转 expired→依赖 intent 转 blocked，凭据刷新后人工复活（§6.6 护栏） | 归类冲突：§4.2 列为表 13 写入命令、§5.3 列入查询命令 12（见探知项 2）；专属拒收条款定稿未载→探知项 5 |
| 12 | redact-scan（ledger-redact-scan）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | --target report/（P5 用法，§5.2） | P5 exit expect「占位符零泄漏」；P5.5 前置交付前终检——对报告全文占位符扫描，任一真值残留=阻断导出（§8.4 关卡 4） | —（只读扫描；残留=阻断导出而非 REJECT 落账） |

## 3 校验命令（6 条，§5.3）

| # | 命令 | 签名 | 必填参数（定稿载） | 输出（定稿载） | 写前拒收条件（定稿载） |
|---|---|---|---|---|---|
| 1 | validate（ledger-validate） | 附录 A：定稿未载→探知项 1 | --tables goals,scope,creds（P0 用法，§5.2） | PASS（P0/P1/P4 exit expect，§5.2）；校验范围=行级校验（§4.1）＋卡片与 TSV 同值性——卡片与 TSV 不一致=P4 ledger-validate 失败（§4.11） | —（校验命令） |
| 2 | verify-chain（ledger-verify-chain） | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | PASS（P0/P4 exit expect，§5.2）；链式哈希校验：改任何历史行即断链可见（§4.10）；跳门检测——每门出口断言的命令调用必产生 timeline 事件，P4 verify-chain+validate 可发现缺门记录（§5.1） | —（校验命令） |
| 3 | hash-recheck（ledger-hash-recheck） | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | PASS（P4 exit expect，§5.2）；P4 四校验命令之一；专属校验内容定稿未载→探知项 5 | —（校验命令） |
| 4 | matrix-audit（ledger-matrix-audit） | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5（抽查比例常量 p4_sample_ratio=0.2，§5.2） | P4 exit expect「抽查通过 且 无告警」（§5.2）；「-」「!」格 P4 抽查；异常检测——批量置态与 fact 密度不符告警（§5.2 P4 duty/§8.3 注入防护④） | —（校验命令） |
| 5 | state-rebuild（ledger-state-rebuild）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | 定稿未载→探知项 5 | PASS：校验 state.md 与账本重建结果一致（§4.1 journal 职能）；kill -9 半写兜底（state 写入 temp/rename 原子替换带 revision 号，§4.1）；P0 entry resume 态判定（§5.2）；evals kill -9 续跑保真度指标（§9.2） | —（校验命令） |
| 6 | set-replay-state（ledger-set-replay-state）【专用六条之一】 | 附录 A：定稿未载→探知项 1 | EV/finding 引用＋三态（推断自语义；参数表定稿未载→探知项 5） | 重放门三态 VERIFIED/REPAIRED/REJECTED 落账；REJECTED→confidence 降 C3 或转 fact（§5.3）；exploitation_status 由 P4 重放门维护——VERIFIED 才维持 C1（§4.7）；重放=REPAIRED 修复 POC 卡片后重放，max_retry=2（§5.2 back_edges）；批次 4 起强制（fresh 隔离子代理只拿 EV 卡片盲重放，§5.2 P4 duty） | —（落账命令；归类为校验命令 6 之一，§5.3） |

## 4 特殊（1 条，§5.3）

| # | 命令 | 签名 | 必填参数（定稿载） | 输出（定稿载） | 写前拒收条件（定稿载） |
|---|---|---|---|---|---|
| 37 | matrix-init | 附录 A：定稿未载→探知项 1 | 列从 VOCAB（WSTG v4.2 全集，版本化）钉死（§5.2 P2 duty） | P2 生成矩阵（matrix.tsv 长表；后续置格走 ledger-matrix-set，§4.2/§4.10） | 专属条款定稿未载→探知项 5（＋通用基线） |

## 5 专用六条视图（§0.3 口径 2：37 命令含六条专用命令）

| 专用命令 | §5.3 分组 | 专责（定稿） |
|---|---|---|
| add-cred | 写命令 18 之列 | creds 落账（身份矩阵落地，ADR-P4③；§0.3 口径 2） |
| set-cred-status | 查询命令 12 之列（归类冲突→探知项 2） | creds 事件溯源状态查询/变更（§5.3） |
| amend-scope | 写命令 18 之列 | scope 修订审计（amendment_of 链+approvals 强制，§0.3 口径 2/§4.4） |
| redact-scan | 查询命令 12 之列 | 交付前终检（§5.3；§8.4 关卡 4） |
| state-rebuild | 校验命令 6 之列 | 重建校验（state.md 与账本重建一致性，§0.3 口径 2/§4.1） |
| set-replay-state | 校验命令 6 之列 | 重放门（三态落账，§0.3 口径 2/§5.3） |

## 探知项（待仲裁）

1. 附录 A 缺位：§3.2「总控 LLM 经宿主执行通道调用 CLI（命令签名附录 A 冻结，LLM 只调用不实现）」与 §5.3「签名清单批次 0 冻结进 shared/LEDGER.md 附录 A」——附录 A 不在定稿文内，37 条命令签名、参数表与输出 schema 均定稿未载。
2. set-cred-status 归类冲突：§4.2 表 13 行「写入命令＝ledger-add-cred / ledger-set-cred-status」；§5.3「查询命令 12：……＋set-cred-status（creds 事件溯源状态查询/变更）、redact-scan（交付前终检）」——同一命令两处分别归入写命令与查询命令。
3. add-goal 与 Tier 0 硬门字面冲突：§5.2 补充语义「P0『无授权只许读文档』由 Tier 0 硬门实现（无 goals 行时一切写命令 REJECT）」；§4.2/§5.2 P0 duty「ledger-add-goal」在无 goals 行时创建首行——若硬门按字面涵盖 add-goal 则无法立项。
4. 命令名前缀不一致：§4.2 写入命令列全带 `ledger-` 前缀（ledger-add-goal 等）；§5.3 命令清单为短名（add-goal 等）；§5.2 P2 duty 出现无前缀 `matrix-init`（同门 exit 断言又用 `ledger-matrix-freeze`）。
5. 命令级必填参数/输出/专属拒收条款大面积缺源：定稿仅载通用纪律（§5.3）与散见语义（§4.3–§4.10/§5.2/§8.4），逐命令参数表与输出 schema 未载（正文各行已随行标注）。
6. 收敛四条件清单缺源：§3.3「收敛四条件可计算」、§5.4「收敛四条件与持续生长共存」——四条件本身定稿未列，converge-check 判定内容待仲裁。

## 自验

- **命令数=37**：`awk '/^## 1 /,/^## 2 /' contracts/02-commands.md | grep -c '^| [0-9]'` = **18**；`awk '/^## 2 /,/^## 3 /' …` = **12**；`awk '/^## 3 /,/^## 4 /' …` = **6**；`awk '/^## 4 /,/^## 5 /' …` = **1**；与定稿 §5.3「合计 18+12+6+1=**37**」并列一致。
- **37 命令清单一致（逐名 grep）**：定稿 §5.3 四行原文内 37 名全命中=true；本文四组行序与 §5.3 清单顺序逐名全等（写 18/查询 12/校验 6/特殊 1 均=true）。逐名出现次数（文本计数）：add-goal=8 add-scope=2 add-intent=3 set-intent-status=2 add-fact=5 add-finding=2 supersede-finding=2 add-asset=2 add-edge=2 add-evidence=5 approve=3 matrix-set=3 checkpoint=2 append-timeline=2 matrix-freeze=3 budget-log=2 add-cred=4 amend-scope=3 unconsumed-facts=1 pending-intents=1 matrix-gaps=1 converge-check=2 next-id=2 intent-status=3 matrix-get=1 scope-check=3 budget-check=2 cleanup-checklist=1 set-cred-status=7 redact-scan=4 validate=5 verify-chain=4 hash-recheck=2 matrix-audit=2 state-rebuild=3 set-replay-state=3 matrix-init=5（37/37 名各 ≥1 次）。
- **专用六条**：`grep -c '专用六条之一' contracts/02-commands.md` = **6**/6（add-cred/set-cred-status/amend-scope/redact-scan/state-rebuild/set-replay-state 逐条带标，另有 §5 汇总视图）。
- **缺源标注**：`grep -c '定稿未载→探知项' contracts/02-commands.md` = **38**（37 条签名列全标＋总览缺源说明）。
- 探知项=6。

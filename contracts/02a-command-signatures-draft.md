# 02a 账本命令签名·契约附录 A（41 条·已终审冻结 contracts-v2）

> **已终审冻结（2026-09-23·contracts-v2）**：63 处【推导】标注随冻结一并接受为契约语义；范围外四条断言命令见文末补全节 · 来源：设计定稿 docs/design/2026-09-21-tanyin-v2-design.md §4（各表结构=参数类型依据）/§5.2（九门断言=调用时机）/§5.3（命令分类）＋契约 01（13 表 142 字段=参数名全集）＋契约 02（37 命令名+分类+已知拒收条件源）
>
> 性质：**被授权的创作性起草**——定稿附录 A 未载（02 探知项 1），签名/参数表/输出 schema 按上下文推导；凡非定稿原文直接给定处一律标【推导】。与 01/02 的「只誊不创」不同，本稿终审通过前不作为实现依据；通过后升格为 shared/LEDGER.md 附录 A 底稿。
>
> 命名：节名用 §5.3 短名，括注 §4.2 ledger- 前缀名（前缀不一致见 02 探知项 4）。分组标签〔写〕〔查询〕〔校验〕〔特殊〕。每节「依据」行含 §5.2 九门调用时机。
>
> **全局纪律（§4.1/§5.3，各节不再重复）**：①写前拒收基线=列数/ID 格式（`{前缀}-{goal-id}-{四位序号}`）/枚举/转义（\\→\\\\、tab→\\t、CR→\\r、LF→\\n、`;\`→\\;）/引用闭合/dedup_key 唯一，畸形 REJECT 不部分写入；②Tier 0 硬门=无 goals 行时一切写命令 REJECT（add-goal 自身豁免，见第 1 节；02 探知项 3 的起草裁决）；③参数经临时文件/stdin 传入，禁命令行字符串拼接；④查询输出摘要化=计数+top-N+ID 列表，禁全量回灌；⑤命令幂等；⑥对外请求类前置 request-ticket；⑦id/score/dedup_key/哈希一律命令计算（总控五不，§2.5）。
>
> **输出约定（本稿统一起草）**：写命令=单行 TSV `OK<TAB><追加行全字段（契约01 列序，已转义）>`；查询=首行 `#count=N`（或专用单行）+过滤行流（TSV 投影）；校验=单行 `PASS` 或 `FAIL<TAB><原因 top-N>`；REJECT 一律 stderr 单行 `REJECT<TAB><命令名><TAB><原因>`、退出码 1（§9.2 退出码 0/1/2 对齐）【推导】。
>
> 依赖的未决事项（不替仲裁，按契约 01 字段清单原文起草）：timeline/budget 无 schema_version 列（01 探知项 1）；PG 序号格式（01 探知项 2）；goal 根标识写法（01 探知项 3）。

## 1 写命令（18 条，§5.3）〔第 1-18 节〕

### 1. add-goal（ledger-add-goal）〔写 1/18〕
- 签名：add-goal --target=<goals.target> --objective=<goals.objective> --auth-doc=<goals.auth_doc> --auth-sha256=<goals.auth_sha256> --signer=<goals.signer> --valid-from=<goals.valid_from> --valid-until=<goals.valid_until> --rate-limit=<goals.rate_limit> --window=<goals.window> --emergency-contact=<goals.emergency_contact> --budget=<goals.budget> --dollar-budget=<goals.dollar_budget> --language=<goals.language> --business-context=<goals.business_context> --model-tier=<goals.model_tier> --guard-tier=<goals.guard_tier>
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--target|文本|是|goals.target|
|--objective|文本|是|goals.objective|
|--auth-doc|文本|是|goals.auth_doc（空=REJECT）|
|--auth-sha256|文本(hex)|是|goals.auth_sha256（空=REJECT）|
|--signer|文本|是|goals.signer（空=REJECT）|
|--valid-from|时间戳|是|goals.valid_from（空=REJECT）|
|--valid-until|时间戳|是|goals.valid_until（空=REJECT）|
|--rate-limit|数值(req/s)|否|goals.rate_limit|
|--window|文本|否|goals.window|
|--emergency-contact|文本|否|goals.emergency_contact|
|--budget|三元组(`;\`分隔整数)|是|goals.budget|
|--dollar-budget|浮点或空|否|goals.dollar_budget（空=第四维关）|
|--language|文本|否|goals.language|
|--business-context|文本|否|goals.business_context|
|--model-tier|枚举|是|goals.model_tier|
|--guard-tier|枚举|是|goals.guard_tier|
|（内部）id|文本|命令铸造|goals.id（前缀 G，next-id 分配）|
|（内部）schema_version|整数|常量|goals.schema_version=2|
|（内部）created|时间戳|命令铸造|goals.created|

- 输出：`OK<TAB>G-…<TAB>goals.tsv`＋追加行回显（§3.1 列序 19 字段单行 TSV）。
- 拒收条件：授权五字段（auth_doc/auth_sha256/signer/valid_from/valid_until）任一空=REJECT（§4.3 授权硬语义，不存在「先记上再补」）；budget 非 `token;requests;hours` 三段整数=REJECT；model_tier∉{strong,weak} 或 guard_tier∉{T1,T2,T3}=REJECT；valid_until≤valid_from=REJECT【推导：§8.1 八问⑥有效窗口语义】；goals 已有未终态行=REJECT（§4.3「每次测试一行」）【推导：重复立项的写侧形态】；本命令豁免 Tier 0「无 goals 行」硬门，其余门禁照常【推导：02 探知项 3 冲突的起草裁决——不豁免则无法立项】。
- 依据：定稿 §4.3/§5.3/§5.2 P0 duty/§8.1 八问①④⑤⑥⑦／契约01 §3.1 goals.tsv。时机：P0 duty（八问问卷+业务问卷后第一条写命令）。

### 2. add-scope（ledger-add-scope）〔写 2/18〕
- 签名：add-scope --kind=<scope.kind> --matcher=<scope.matcher> [--account=<scope.account>] [--permitted-actions=<scope.permitted_actions>] [--note=<scope.note>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--kind|枚举|是|scope.kind|
|--matcher|文本|是|scope.matcher|
|--account|文本|条件|scope.account（account-grant 行必填）|
|--permitted-actions|多值(`;\`分隔)|条件|scope.permitted_actions（account-grant 行必填）|
|--note|文本|否|scope.note|
|（内部）id|文本|命令铸造|scope.id（前缀 S）|
|（内部）amendment_of|文本|本命令恒空|scope.amendment_of（新原始行；修订走 amend-scope）【推导】|
|（内部）schema_version / created|整数/时间戳|常量/命令铸造|scope.schema_version=2 / scope.created|

- 输出：`OK<TAB>S-…<TAB>scope.tsv`＋追加行回显（9 字段）。
- 拒收条件：kind∉{include,exclude,oob,account-grant}=REJECT；matcher 不合 CIDR 网段/域名后缀/通配语法=REJECT【推导：§4.4 matcher 支持范围】；kind=account-grant 而 account 或 permitted_actions 空=REJECT【推导：§4.4「account-grant 行另需 account＋permitted_actions」】；account 为 CRED 引用时引用闭合失败=REJECT【推导】；include/exclude 行 matcher 空=REJECT。
- 依据：定稿 §4.4/§5.2 P0 duty（八问①②③⑧落账）/§5.3／契约01 §3.2 scope.tsv。时机：P0 duty。注：include+exclude+oob 齐备由 P0 exit 断言 ledger-scope-coverage 检查（该断言命令不在 37 面内，见文末范围外备注），非本命令拒收（02 §1 行 2 已载）。

### 3. add-intent（ledger-add-intent）〔写 3/18〕
- 签名：add-intent --title=<intents.title> [--detail=<intents.detail>] --engine=<intents.engine> --kind=<intents.kind> --origin=<intents.origin> [--via=<intents.via>] --budget-share=<intents.budget_share> [--activation=<intents.activation>] [--cred=<creds.id>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--title|文本|是|intents.title|
|--detail|文本|否|intents.detail|
|--engine|文本|是|intents.engine|
|--kind|枚举|是|intents.kind|
|--origin|枚举|是|intents.origin|
|--via|文本|否|intents.via|
|--budget-share|三/四元组|是|intents.budget_share|
|--activation|结构化谓词|条件|intents.activation（deferred 语义用）|
|--cred|文本(行 id 引用)|条件|creds.id（kind=authz-diff 必填）【推导：§4.10 硬门参数化】|
|（内部）id|文本|命令铸造|intents.id（前缀 INT）|
|（内部）status|枚举|命令铸造|intents.status（初始 candidate；origin=recon-event 资产事件路径直达 pending）【推导：§4.5 状态机起点+§5.2 events】|
|（内部）score|浮点|命令计算|intents.score（§8.7 公式；recon-event 不打分）|
|（内部）dedup_key|文本|命令计算|intents.dedup_key（资产+技法类，机械计算）|
|（内部）schema_version / created|整数/时间戳|常量/命令铸造|intents.schema_version=2 / intents.created|

- 输出：`OK<TAB>INT-…<TAB>intents.tsv`＋追加行回显（15 字段）。
- 拒收条件：kind∉{recon,surface,matrix-test,deep-dive,authz-diff} 或 origin∉{entity,concept,precedent,adjacency,llm,recon-event,mixed}=REJECT；budget_share 非 `token;requests;hours[;dollars]`=REJECT；dedup_key 与既有行重复=REJECT（命令计算后判重，LLM 只提议不判重，§4.5）；界外资产派生 intent=REJECT（§4.4 账本级禁止＋§9.2 负向用例「界外资产喂 add-intent→REJECT」）；kind=authz-diff 须 --cred 引用 CRED 行 status=active 且 permitted_actions 覆盖计划动作，否则=REJECT【推导：§4.10 硬门（总控校验语义落为命令拒收）】；activation 须 `field;op;value` 三段=REJECT 校验【推导】。
- 依据：定稿 §4.5/§5.2 P3 duty②③+events asset-added/§8.7／契约01 §3.3 intents.tsv+§3.13。时机：P3 ②假设风暴→③批量派发；P3 events asset-added（spawn 测绘 intents，origin=recon-event 直接 pending 不打分）。

### 4. set-intent-status（ledger-set-intent-status）〔写 4/18〕
- 签名：set-intent-status --id=<intents.id> --status=<intents.status> [--reason=<intents.reason>] [--activation=<intents.activation>] [--approval=<approvals.id>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--id|文本(行 id 引用)|是|intents.id|
|--status|枚举|是|intents.status|
|--reason|文本|条件|intents.reason（rejected/blocked/deferred 强制）|
|--activation|结构化谓词|条件|intents.activation（deferred 附）|
|--approval|文本(行 id 引用)|条件|approvals.id（blocked 复活须引用）【推导：§4.5「复活须 approvals 引用」参数化】|

- 输出：`OK<TAB>INT-…(追加新行)`＋回显——事件溯源：同 id 多行追加，「取最新」是账本命令（§4.1）。
- 拒收条件：--id 引用闭合失败=REJECT；status 转移不沿状态机（candidate→pending→active→done/blocked，或 candidate→rejected/deferred）=REJECT【推导：§4.5 状态机】；status∈{rejected,blocked,deferred} 而 reason 空=REJECT（强制）；blocked→active 复活无 --approval 指向 approved 行=REJECT（blocked 不可自动复活，§4.5）【推导】；deferred 附 activation 须 `field;op;value`=REJECT 校验。
- 依据：定稿 §4.5/§4.1 事件溯源／契约01 §3.3 intents.tsv+§3.8。时机：P3 ④验收落账／intent 生命周期全程。

### 5. add-fact（ledger-add-fact）〔写 5/18〕
- 签名：add-fact --intent-id=<facts.intent_id> --kind=<facts.kind> --target=<facts.target> --detail=<facts.detail> --confidence=<facts.confidence>
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--intent-id|文本(行 id 引用)|是|facts.intent_id|
|--kind|枚举|是|facts.kind|
|--target|文本|是|facts.target|
|--detail|文本|是|facts.detail（落账即脱敏）|
|--confidence|浮点|是|facts.confidence|
|（内部）id / schema_version / created|—|命令铸造/常量|facts.id（前缀 F）/facts.schema_version=2/facts.created|

- 输出：`OK<TAB>F-…<TAB>facts.tsv`＋追加行回显（8 字段，detail 已脱敏）。
- 拒收条件：kind∉{port,service,http,info,vuln-clue,authz}=REJECT；confidence∉[0,1]=REJECT；--intent-id 引用闭合失败=REJECT；--detail redact 校验检出真值模式（cookie/token/密码形态）=REJECT（§8.4 关卡 2 明列 add-fact——落盘前掩码）；清洗（剥离控制字符/截断超长）后列数=8。
- 依据：定稿 §4.6/§8.4 关卡2/§5.2 P1 duty／契约01 §3.4 facts.tsv。时机：P1 duty（测绘 facts 即脱敏）/P3 ④验收落账。

### 6. add-finding（ledger-add-finding）〔写 6/18〕
- 签名：add-finding --intent-id=<findings.intent_id> --title=<findings.title> --confidence=<findings.confidence> --impact=<findings.impact> --exploitation-status=<findings.exploitation_status> [--auth-context=<findings.auth_context>] --scope-check=<findings.scope_check> --description-brief=<findings.description_brief> --reproducible-steps=<findings.reproducible_steps> --affected-asset-id=<findings.affected_asset_id> --evidence-ids=<findings.evidence_ids> [--control-evidence-ids=<findings.control_evidence_ids>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--intent-id|文本(行 id 引用)|是|findings.intent_id|
|--title|文本|是|findings.title|
|--confidence|枚举|是|findings.confidence|
|--impact|枚举|是|findings.impact|
|--exploitation-status|枚举|是|findings.exploitation_status|
|--auth-context|文本|否|findings.auth_context（空=未认证，或 CRED-{id}）|
|--scope-check|枚举|是|findings.scope_check|
|--description-brief|文本|是|findings.description_brief（≤200 字）|
|--reproducible-steps|多值|是|findings.reproducible_steps（≥1 强制）|
|--affected-asset-id|文本(行 id 引用)|是|findings.affected_asset_id|
|--evidence-ids|多值(行 id 引用)|是|findings.evidence_ids|
|--control-evidence-ids|多值(行 id 引用)|否|findings.control_evidence_ids|
|（内部）id|文本|命令铸造|findings.id（前缀 FD）|
|（内部）dedup_key|文本|命令计算|findings.dedup_key（affected_asset+vuln_class+variant）|
|（内部）card_path|文本|命令铸造|findings.card_path（=findings-cards/FD-{id}.md）|
|（内部）status|枚举|命令铸造|findings.status（新行=active）【推导】|
|（内部）schema_version / created|—|常量/命令铸造|findings.schema_version=2 / findings.created|

- 输出：`OK<TAB>FD-…<TAB>findings.tsv`＋追加行回显（18 字段）＋外置卡片 findings-cards/FD-{id}.md 同步生成（六字段与 TSV 同值，§4.11；不一致=P4 ledger-validate 失败）。
- 拒收条件：reproducible_steps≥1 强制——空=REJECT 并提示改走 add-fact（铁律 4：无可复现步骤的观察一律是 fact）【推导：铁律的写侧拒收化】；confidence∉{C1,C2,C3,➖🛑}／impact∉{高,中,低}／exploitation_status∉{verified,suspected,ruled_out}／scope_check∉{in_scope,boundary-verified}=REJECT；confidence=C2 而 evidence_ids 无条件可达性证据=REJECT【推导：§4.7 C2 定义（须附条件可达性证据否则降 C3）】；description_brief>200 字=REJECT；--intent-id/--affected-asset-id/--evidence-ids/--control-evidence-ids 引用闭合失败、--auth-context 非空且非 CRED-{id} 闭合=REJECT；dedup_key 与既有 active 行同键=REJECT（提示走 supersede-finding 合并）【推导：§4.7 dedup_key 同键合并语义的写侧形态】。
- 依据：定稿 §4.7/§4.11/铁律4/§5.2 P3④／契约01 §3.5 findings.tsv。时机：P3 ④验收落账（proves 边由 add-edge 另落）；P4 合并前新增行截止。

### 7. supersede-finding（ledger-supersede-finding）〔写 7/18〕
- 签名：supersede-finding --id=<edges.source_id> --superseded-by=<edges.target_id>
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--id|文本(行 id 引用)|是|edges.source_id（值=被合并 findings.id）|
|--superseded-by|文本(行 id 引用)|是|edges.target_id（值=合并去向 findings.id）|
|（内部）边 kind|枚举|常量|edges.kind=supersedes（finding→finding）|
|（内部）边 provenance|文本|命令铸造|edges.provenance【推导：合并操作的溯源值】|
|（内部）tombstone 行|枚举|命令铸造|findings.status=superseded（被合并 id 追加新行，不删行）|

- 输出：`OK<TAB>E-…(supersedes 边)<TAB>tombstone(FD-…)`＋两行回显。
- 拒收条件：两 id 引用闭合失败或互指/自指/成环=REJECT【推导】；被合并行 status≠active=REJECT【推导：已 superseded 行不可再合并】；两行 dedup_key 不同键=REJECT【推导：§4.7「dedup_key 同键合并语义」——跨键合并须人工裁决，本稿不允许】。
- 依据：定稿 §4.1/§4.7/§5.2 P4 duty（finding 合并）/§4.8 边9／契约01 §3.5+§3.7+§4。时机：P4 duty（汇总段合并）。

### 8. add-asset（ledger-add-asset）〔写 8/18〕
- 签名：add-asset --type=<assets.type> --value=<assets.value> [--meta=<assets.meta>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--type|枚举|是|assets.type|
|--value|文本|是|assets.value|
|--meta|文本|否|assets.meta|
|（内部）id|文本|命令铸造|assets.id（前缀 AST）|
|（内部）in_scope|布尔/枚举|命令判定|assets.in_scope（命令内联 scope-check：界外自动 out_of_scope）|
|（内部）schema_version / created|—|常量/命令铸造|assets.schema_version=2 / assets.created|

- 输出：`OK<TAB>AST-…<TAB>assets.tsv`＋追加行回显（7 字段，in_scope=判定结果）。
- 拒收条件：type∉{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold,cloud-storage,human-factor}（十一值，G-12 勘误）=REJECT；value 空=REJECT【推导】；同 type+value 已存在=REJECT【推导：资产判重】；**界外资产不 REJECT**——强制对照 include/exclude，界外自动标 out_of_scope（§4.4 明示，与其他命令相反）。（原「type∈{pivot,foothold} 批次 4 前启用=REJECT」分支随批次 4 启用退役；cloud-storage/human-factor 细分落 meta=sub:…——见文末 2026-09-24 勘误补记·G-12。）
- 依据：定稿 §4.8/§4.4/§5.2 P1 duty+P3 events asset-added／契约01 §3.6 assets.tsv。时机：P1 duty（测绘）/P3 events asset-added（回边生长图谱）。

### 9. add-edge（ledger-add-edge）〔写 9/18〕
- 签名：add-edge --kind=<edges.kind> --source-id=<edges.source_id> --target-id=<edges.target_id> --provenance=<edges.provenance>
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--kind|枚举|是|edges.kind（10 边）|
|--source-id|文本(行 id 引用)|是|edges.source_id|
|--target-id|文本(行 id 引用)|是|edges.target_id|
|--provenance|文本|是|edges.provenance（来源：intent/引擎/人工）|
|（内部）id / schema_version / created|—|命令铸造/常量|edges.id（前缀 E）/edges.schema_version=2/edges.created|

- 输出：`OK<TAB>E-…<TAB>edges.tsv`＋追加行回显（7 字段）。
- 拒收条件：kind∉10 边枚举=REJECT（新增边类型须 bump schema_version——现版本下一律 REJECT，§4.8）；--source-id/--target-id 引用闭合失败=REJECT（§4.1）；方向不符 10 边定义=REJECT【推导：按契约01 §4 方向列校验（spawns=goal→intent、parent=asset→asset、supersedes=finding→finding、scope-rel=asset→scope 等；cross_ref 方向定稿未载→不校验）】；同 kind+source_id+target_id 重复=REJECT【推导：幂等判重】。
- 依据：定稿 §4.8/§2.5/§5.2 P3⑤链构建（attack/cross_ref）／契约01 §3.7+§4 10 边。时机：P3 ⑤链构建；P1 资产树（parent 边，P1 exit ledger-tree-check 断言对象）。

### 10. add-evidence（ledger-add-evidence）〔写 10/18〕
- 签名：add-evidence --title=<E-index.title> --source-type=<E-index.source_type> --observed-at=<E-index.observed_at> --network-position=<E-index.network_position> --repro-command=<E-index.repro_command> --repro-kind=<E-index.repro_kind> --artifact=<E-index.artifact_path> [--raw-excerpt=<E-index.raw_excerpt>] [--linked-finding=<E-index.linked_finding>] [--pair-group=<E-index.pair_group>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--title|文本|是|E-index.title|
|--source-type|枚举|是|E-index.source_type|
|--observed-at|时间戳|是|E-index.observed_at|
|--network-position|枚举/扩展标量|是|E-index.network_position|
|--repro-command|文本|是|E-index.repro_command（凭据一律 {{vault:cred-N}} 占位符）|
|--repro-kind|枚举|是|E-index.repro_kind|
|--artifact|文本(路径)|是|E-index.artifact_path|
|--raw-excerpt|文本|否|E-index.raw_excerpt（脱敏+定长截断）|
|--linked-finding|文本(行 id 引用)|否|E-index.linked_finding|
|--pair-group|文本|否|E-index.pair_group|
|（内部）id|文本|命令铸造|E-index.id（前缀 EV）|
|（内部）content_hash_raw / content_hash_norm|文本(hex)|命令计算|E-index.content_hash_raw / E-index.content_hash_norm（对 artifact 重算：raw+归一化去 nonce/时间戳双轨——总控不自己算哈希，§2.5）|
|（内部）card_path|文本|命令铸造|E-index.card_path（=evidence/EV-{id}.md，嵌套四要素进卡片 §4.11）|
|（内部）schema_version / created|—|常量/命令铸造|E-index.schema_version=2 / E-index.created|

- 输出：`OK<TAB>EV-…<TAB>E-index.tsv`＋追加行回显（16 字段）＋EV 卡片生成（POC 四要素嵌套部分）。
- 拒收条件：source_type∉{command,capture,file,log,manual}／repro_kind∉{single,sequence,concurrent}／network_position∉{internet,intranet,same-host,jumphost:<name>}=REJECT；repro_command/raw_excerpt redact 校验检出真值模式（凭据非 {{vault:cred-N}} 占位符形态）=REJECT（§8.4 关卡 2 明列 add-evidence）；artifact_path 只增不覆盖——同路径已存在=REJECT（重跑另存 -r2）【推导：§4.9「只增不覆盖」写侧形态】；--linked-finding 引用 FD 闭合失败=REJECT；raw_excerpt 超定长=截断后落账【推导：定长截断】。
- 依据：定稿 §4.9/§4.11/§8.4 关卡2/§5.2 P0 duty（授权书扫描件入 evidence 双哈希）+P3④／契约01 §3.9。时机：P0 duty；P3 ④验收落账。

### 11. approve（ledger-approve）〔写 11/18〕
- 签名：approve --command-hash=<approvals.command_hash> --decision=<approvals.decision> --approver=<approvals.approver> [--note=<approvals.note>] ｜ 断言用法：approve --verify-signoff ／ approve --knowledge
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--command-hash|文本(hex)|是|approvals.command_hash|
|--decision|文本|是|approvals.decision（值域建议 {approved,rejected,exempted,knowledge-approved}）【推导：decision 无枚举源，以 P5.5 expect「approved 行」+P6 expect approved+P6.0 豁免语义起草】|
|--approver|文本|是|approvals.approver|
|--note|文本|否|approvals.note|
|--verify-signoff / --knowledge|旗标|断言用法|【推导】（P5.5/P6 exit 断言只读模式，不落新行；定稿载用法）|
|（内部）id / timestamp / schema_version|—|命令铸造/常量|approvals.id（前缀 AP）/approvals.timestamp（本表无 created 列）/approvals.schema_version=2|

- 输出：写=`OK<TAB>AP-…<TAB>approvals.tsv`＋追加行回显（7 字段）；--verify-signoff=`PASS`（存在对应 approved 行）或 `FAIL<TAB>无签发行`；--knowledge=approved 缺失=`FAIL`。
- 拒收条件：approver 空=REJECT【推导：人审语义——审批展示原始命令原文非 LLM 摘述（§4.8），须具名】；command_hash 非 hex=REJECT；decision 不在建议值域=REJECT【推导】；断言用法只读、无拒收。
- 依据：定稿 §4.8/§8.2 L3 分级审批/§5.2 P5.5 exit+P6 exit+P6.0 豁免／契约01 §3.8。时机：L3 逐条人审；P5.5 签发（command_hash 绑定聚合报告文件哈希）；P6 知识审批；P6.0 残留豁免。

### 12. matrix-set（ledger-matrix-set）〔写 12/18〕
- 签名：matrix-set --attack-surface=<matrix.attack_surface> --vuln-class=<matrix.vuln_class> --state=<matrix.state> [--reason=<matrix.reason>] [--intent-id=<matrix.intent_id>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--attack-surface|文本|是|matrix.attack_surface（长表行键之一）|
|--vuln-class|文本|是|matrix.vuln_class（行键之一；VOCAB WSTG v4.2 全集）|
|--state|枚举|是|matrix.state（x / ? / - / !，置空态无意义）|
|--reason|文本|条件|matrix.reason（-、! 态强制；子矩阵行 submatrix: 前缀；authz-diff: 前缀）|
|--intent-id|文本(行 id 引用)|否|matrix.intent_id|
|（内部）schema_version / updated|—|常量/命令铸造|matrix.schema_version=2 / matrix.updated（本表用 updated 非 created）|

- 输出：`OK<TAB>置格 <attack_surface>×<vuln_class>=<state>`＋追加置格行回显（事件溯源：同键多行取最新）。
- 拒收条件：--attack-surface×--vuln-class 行键不存在于 matrix.tsv=REJECT【推导：长表行键须 matrix-init 先铸，不允许置格行外新键】（G-2 勘误例外=文末 2026-09-24 补记：四条件齐备放行 submatrix: 铸行）；vuln_class∉VOCAB（WSTG v4.2 版本化全集）=REJECT；state∉{x,?,-,!}=REJECT【推导：空态=未检查由 init 生成，置格命令不接受】；state∈{-,!} 而 reason 空=REJECT【推导：§4.10「不适用附理由/环境干扰附记录」】；reason 前缀与行类别不符（子矩阵行须 submatrix:、身份矩阵差分行须 authz-diff:）=REJECT【推导】（G-2 勘误修正=旧前缀空→任意前缀首次归类放行；旧前缀非空且≠新→REJECT——见文末 2026-09-24 补记）；P2 冻结后主矩阵新增行键=REJECT（新资产走子矩阵行）【推导：基线冻结语义】；--intent-id 引用闭合失败=REJECT；置态证据支撑不足不属本命令拒收（P4 matrix-audit 事后抽查）。
- 依据：定稿 §4.10/§5.2 P3 置格+events（authz 差分落标准格）／契约01 §3.10。时机：P3 演进循环置格；P2 后新资产一律 submatrix: 行。

### 13. checkpoint〔写 13/18〕
- 签名：checkpoint [--phase=<timeline.phase>] [--event=<timeline.event>]【推导：本命令写 state.md（非 13 表），无账本字段可引；phase/event 沿 timeline 同名字段语义标注】（批次 3 参数扩展 --timestamp/--session/--release/--round/--note/--spawn 与 state.md v2 十键行结构=文末 2026-09-24 勘误补记·G-6/G-10）
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--phase|文本|否|timeline.phase（九门阶段）【推导】|
|--event|文本|否|timeline.event（checkpoint 事由）【推导】|
|（内部）state.md|—|命令生成|【推导】state.md ≤200 行 handoff；写入走 temp/rename 原子替换+revision 号（§4.1）|

- 输出：`OK<TAB>revision=<n>`（state.md 原子替换、revision 递增——kill -9 半写兜底）。
- 拒收条件：Tier 0 通用基线（无 goals 行=REJECT）；违反单活跃会话约束（single_active_session=true，已有未释放 checkpoint）=REJECT【推导：§5.2 补充语义护栏的写侧形态】；--phase∉九门=REJECT【推导】。
- 依据：定稿 §5.2 P3 duty⓪+补充语义（受管重启护栏）/§3.3 Context/§4.1；契约01 §1（与 state-rebuild 对偶）。时机：P3 每轮⓪步；受管重启前。state.md 内部行结构定稿未载→文末无法起草项 5（→ 2026-09-24 勘误补记已回注·G-6/G-10）。

### 14. append-timeline（ledger-append-timeline）〔写 14/18〕
- 签名：append-timeline --actor=<timeline.actor> --phase=<timeline.phase> --event=<timeline.event> [--revert-cmd=<timeline.revert_cmd>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--actor|枚举|是|timeline.actor（总控/子代理/CLI/人工）|
|--phase|文本|是|timeline.phase|
|--event|文本|是|timeline.event（对外请求记 request: 前缀）|
|--revert-cmd|文本|条件|timeline.revert_cmd（外部副作用操作必填；无逆者 irreversible；纯账本状态变化留空）|
|（内部）timestamp|时间戳|命令铸造|timeline.timestamp|
|（内部）prev_hash / hash|文本(hex)|命令计算|timeline.prev_hash / timeline.hash（哈希输入=本行全部字段含 revert_cmd）|

- 输出：`OK<TAB>hash=<hex前8>`＋追加行回显（7 字段全列序）。
- 拒收条件：actor∉{总控,子代理,CLI,人工}=REJECT；event 声明为外部副作用类（request:/落文件/改配置）而 --revert-cmd 缺失=REJECT【推导：§0.3 口径4 分层登记的写侧形态】；revert_cmd=irreversible 而无对应 approvals 行（L3 逐条审批）=REJECT【推导】；对外请求 event 无 request-ticket 前置=REJECT【推导：§5.3 通用纪律】。
- 依据：定稿 §4.10/§0.3 口径4/§5.1（每门 exit 断言命令调用必产生 timeline 事件）/§5.2／契约01 §3.11。时机：全程高频——九门 exit 断言记录、P0 SKILL 版本+tools.lock 哈希、request: 事件、managed-restart（记 spawn 方式 auto/manual）。

### 15. matrix-freeze（ledger-matrix-freeze）〔写 15/18〕
- 签名：matrix-freeze【推导：无参数——matrix.tsv 7 字段无 frozen 列（契约01 §3.10），冻结事实以 timeline（event=matrix-freeze）为推导载体；正式载体待仲裁→文末无法起草项 3】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无外部参数）|—|—|【推导】|
|（内部）冻结事件|—|命令生成|timeline.event=matrix-freeze【推导：冻结载体起草】|

- 输出：`OK<TAB>frozen`。
- 拒收条件：matrix.tsv 未初始化（无 matrix-init 产物）=REJECT【推导】；重复冻结=REJECT（§5.2 P2 exit expect「frozen（不可重复冻结）」——与通用「命令幂等」的张力以 exit expect 为准，重复调用=REJECT already-frozen）【推导】；Tier 0 通用基线。
- 依据：定稿 §5.2 P2 duty+exit（锚点冻结≠探索冻结）／契约01 §3.10。时机：P2 duty（matrix-init 后立即冻结）。

### 16. budget-log（ledger-budget-log）〔写 16/18〕
- 签名：budget-log --token-delta=<budget.token_delta> --requests-delta=<budget.requests_delta> --hours-delta=<budget.hours_delta> [--dollars-delta=<budget.dollars_delta>] --scope=<budget.scope> [--note=<budget.note>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--token-delta|整数|是|budget.token_delta|
|--requests-delta|整数|是|budget.requests_delta|
|--hours-delta|数值|是|budget.hours_delta|
|--dollars-delta|数值|否|budget.dollars_delta（默认 0）|
|--scope|文本|是|budget.scope（=goal 或 INT-{id}）|
|--note|文本|否|budget.note|
|（内部）timestamp|时间戳|命令铸造|budget.timestamp（本表无 schema_version/created 列，01 探知项 1）|

- 输出：`OK<TAB>budget.tsv`＋流水行回显（7 字段；预算树：intent 消耗计入自身份额并上卷 goal 根）。
- 拒收条件：scope∉{goal,INT-{id}} 或 INT 引用不闭合=REJECT；goals.dollar_budget 空（第四维关）而 dollars_delta≠0=REJECT【推导：默认关不累计（ADR-P4⑥）】；token/requests 非整数、hours 非数值=REJECT；intent 超份额=拒派属派发侧语义（§8.7），非本命令拒收（流水照记，02 §1 行 16 已载）。
- 依据：定稿 §4.10/§8.7／契约01 §3.12+§3.1（goals.budget 对照）。时机：P3 每轮（checkpoint 后、budget-check 前）。

### 17. add-cred（ledger-add-cred）【专用六条之一】〔写 17/18〕
- 签名：add-cred --kind=<creds.kind> --role=<creds.role> --username-ref=<creds.username_ref> --secret-ref=<creds.secret_ref> [--scope-asset=<creds.scope_asset>] [--obtained-via-intent=<creds.obtained_via_intent>] [--parent-cred=<creds.parent_cred>] [--valid-from=<creds.valid_from>] [--valid-until=<creds.valid_until>] [--permitted-actions=<creds.permitted_actions>] [--note=<creds.note>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--kind|枚举|是|creds.kind|
|--role|文本|是|creds.role（合法集合由 P0 八问⑧+account-grant 行确定）|
|--username-ref|文本|是|creds.username_ref|
|--secret-ref|文本|是|creds.secret_ref（={{vault:cred-N}} 占位符；N=creds 行序号）|
|--scope-asset|文本|否|creds.scope_asset|
|--obtained-via-intent|文本(行 id 引用)|否|creds.obtained_via_intent|
|--parent-cred|文本(行 id 引用)|条件|creds.parent_cred（kind=session 必填）【推导：session 由 static-cred 换取或攻击所得——必有父】|
|--valid-from / --valid-until|时间戳|否|creds.valid_from / creds.valid_until|
|--permitted-actions|多值|否|creds.permitted_actions|
|--note|文本|否|creds.note|
|（内部）id|文本|命令铸造|creds.id（前缀 CRED）|
|（内部）status|枚举|命令铸造|creds.status（新行=active）【推导】|
|（内部）schema_version / created|—|常量/命令铸造|creds.schema_version=2 / creds.created|

- 输出：`OK<TAB>CRED-…<TAB>creds.tsv`＋追加行回显（15 字段；真值永不进账本）。
- 拒收条件：kind∉{static-cred,session}=REJECT；--secret-ref 非 {{vault:cred-N}} 占位符形态（redact 检出真值模式）=REJECT（真值永不进账本硬约束，§4.10；N 由命令按 creds 行序号校验/分配）【推导】；role 不在合法集合（P0 八问⑧+account-grant 行确定）=REJECT【推导】；kind=session 而 parent_cred 空=REJECT【推导】；--obtained-via-intent/--parent-cred 引用闭合失败=REJECT；permitted_actions 未被对应 account-grant 行覆盖=REJECT【推导：§4.10 对照 account-grant】；valid_until≤valid_from=REJECT【推导】；材质（ntlm-hash/ssh-key/x509）经 meta 位标注、kind 二分不变（§4.10 材质约定）——材质值出现在 kind=REJECT【推导】。
- 依据：定稿 §4.10/§6.6/§8.1 八问⑧/§5.2 P3 events cred-obtained／契约01 §3.13。时机：P0 duty（客户提供 static-cred＝八问⑧落账位）；P3 events cred-obtained（登记 creds(kind=session)→触发 authz-diff 候选）。

### 18. amend-scope（ledger-amend-scope）【专用六条之一】〔写 18/18〕
- 签名：amend-scope --amendment-of=<scope.amendment_of> --kind=<scope.kind> --matcher=<scope.matcher> [--account=<scope.account>] [--permitted-actions=<scope.permitted_actions>] --note=<scope.note> [--approval=<approvals.id>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--amendment-of|文本(行 id 引用)|是|scope.amendment_of（=被修订行 id）|
|--kind|枚举|是|scope.kind|
|--matcher|文本|是|scope.matcher|
|--account / --permitted-actions|文本/多值|条件|scope.account / scope.permitted_actions（account-grant 行必填）|
|--note|文本|是|scope.note（修订理由+批准人）|
|--approval|文本(行 id 引用)|条件|approvals.id（P0 后必填）【推导：§5.2 P3 guardrails「修订未经审批=账本级 REJECT」参数化】|
|（内部）id / schema_version / created|—|命令铸造/常量|scope.id（前缀 S）/scope.schema_version=2/scope.created|

- 输出：`OK<TAB>S-…(修订行)<TAB>amendment_of=<被修订行>`＋追加行回显（不删行不改行；生效判定=沿 amendment 链取最新——命令实现，§4.4）。
- 拒收条件：--amendment-of 引用闭合失败=REJECT；修订未经审批=账本级 REJECT——P0 后 --approval 必填且须指向 approved 行，缺失或非 approved=REJECT（§5.2 P3 events scope-amended guardrails）【推导：P0 阶段（首建期）豁免参数但沿用 add-scope 校验】；note 不含修订理由+批准人=REJECT【推导：§4.4 note 语义】；其余字段同 add-scope 校验（kind 枚举/matcher 语法/account-grant 配套）。
- 依据：定稿 §4.4/§0.3 口径4/§5.2 P3 events scope-amended（→egress compile 重编译 ACL/DNS pinning/OOB 白名单→out_of_scope 资产复判→canary 复测）／契约01 §3.2+§3.8。时机：P3 events scope-amended；修订史进报告守门声明。

## 2 查询命令（12 条，§5.3）〔第 19-30 节〕

> 只读命令无写前拒收语义（§5.3；set-cred-status 变更模式除外，见第 29 节与 02 探知项 2）；输出一律摘要化（计数+top-N+ID 列表，禁全量回灌）。

### 19. unconsumed-facts〔查询 1/12〕
- 签名：unconsumed-facts [--top=<N>]【推导：top-N 摘要化参数；过滤条件无参数——未消费=无 derived_from 出边】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--top|整数|否|【推导】|
|（过滤键）derived_from 出边|—|内置|edges.kind=derived_from 反查 facts.id（无出边=未消费）|

- 输出：查询=过滤行流：首行 `#count=N`＋每行 `facts.id	facts.kind	facts.target	facts.confidence`。
- 拒收条件：—（只读）。
- 依据：定稿 §4.8（未消费 fact 定义）/§5.2 P3①扫描步入口／契约01 §3.4+§3.7。时机：P3 ①扫描步。

### 20. pending-intents〔查询 2/12〕
- 签名：pending-intents [--top=<N>]【推导】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--top|整数|否|【推导】|
|（过滤键）status 最新行|—|内置|intents.status=pending（事件溯源取最新）|

- 输出：`#count=N`＋每行 `intents.id	intents.title	intents.kind	intents.engine	intents.budget_share`。
- 拒收条件：—（只读）。
- 依据：定稿 §4.5（status 状态机）/§5.2 P3①／契约01 §3.3。时机：P3 ①扫描步。

### 21. matrix-gaps〔查询 3/12〕
- 签名：matrix-gaps [--baseline] [--top=<N>]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--baseline|旗标|否|【推导】（定稿载 P2 用法；旗标非字段）|
|--top|整数|否|【推导】|
|（过滤键）空格|—|内置|matrix.state=空（未检查格清单）|

- 输出：默认：`#count=N`＋每行 `matrix.attack_surface	matrix.vuln_class`（P3 ①空格清单）；--baseline：单行 `#baseline_rows=N	#in_scope_surfaces=M	covered=true/false`（P2 exit expect「基线行数>0 且覆盖全部 in_scope 攻击面」）。
- 拒收条件：—（只读）。
- 依据：定稿 §5.2 P2 exit+P3①/§4.10／契约01 §3.10+§3.6（in_scope 攻击面来源）。时机：P2 exit 断言；P3 ①扫描。

### 22. converge-check〔查询 4/12〕
- 签名：converge-check【推导：无参——判定输入为账本全量】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无参数）|—|—|【推导】|

- 输出：单行 `converged` 或 `budget-exhausted`（两者皆合法终态；后者置 degraded=true 走 P4 降级流）。
- 拒收条件：—（只读）。
- 依据：定稿 §5.2 P3 exit/§3.3/§5.4；**收敛四条件清单定稿未列（02 探知项 6）→判定内容留空，见文末无法起草项 1**。时机：P3 exit 断言（每轮⑥收敛判定）。

### 23. next-id（ledger-next-id）〔查询 5/12〕
- 签名：next-id --prefix=<前缀>【推导：参数名无字段对应；值域定稿载 §4.1 前缀表 G/S/INT/F/FD/AST/E/AP/EV/CRED/PG】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--prefix|枚举|是|【推导】（11 前缀，§4.1）|
|（内部）goal-id / 序号|—|命令读取/原子分配|goals.id 的 goal-id 段+表内最大序号【推导】|

- 输出：单行=`{前缀}-{goal-id}-{四位序号}`（原子分配；定宽零填充，字典序=时间序）。
- 拒收条件：—（只读分配）；prefix∉11 前缀表=REJECT【推导】；调用方非总控执行通道=REJECT（子代理/引擎无铸造权）【推导】。
- 依据：定稿 §4.1 ID 铸造／契约01 §1。时机：一切写命令 id 前置（或由写命令内联调用）。

### 24. intent-status〔查询 6/12〕
- 签名：intent-status --id=<intents.id>
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--id|文本(行 id 引用)|是|intents.id|

- 输出：单行 `intents.id	intents.status	intents.reason`（事件溯源同 id 多行取最新）；无此行=`#count=0`【推导】。
- 拒收条件：—（只读；02 §2 行 6 标参数表探知项 5→参数名从 intents.id 推导）。
- 依据：定稿 §4.1（「取最新」是账本命令）/§4.5／契约01 §3.3。时机：P3 ①/P4 状态核查。

### 25. matrix-get〔查询 7/12〕
- 签名：matrix-get --attack-surface=<matrix.attack_surface> --vuln-class=<matrix.vuln_class>【推导：以长表两行键为查询键——02 §2 行 7 标输出细节探知项 5】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--attack-surface|文本|是|matrix.attack_surface|
|--vuln-class|文本|是|matrix.vuln_class|

- 输出：单行 `matrix.attack_surface	matrix.vuln_class	matrix.state	matrix.reason	matrix.intent_id	matrix.updated`（同键多行取最新）；空格（未置格）state 列=空。
- 拒收条件：—（只读）。
- 依据：定稿 §5.3/§4.10／契约01 §3.10。时机：P3 置格前读；P4 抽查。

### 26. scope-check〔查询 8/12〕
- 签名：scope-check --all-assets ｜ scope-check --type=<assets.type> --value=<assets.value>【推导：单资产判定参数；--all-assets 定稿载 P1 用法】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--all-assets|旗标|二选一|【推导】（定稿载用法；旗标非字段）|
|--type|枚举|二选一|assets.type|
|--value|文本|二选一|assets.value|
|（判定输入）matcher 集|—|内置|scope.kind=include/exclude 行的 scope.matcher（CIDR/域名后缀/通配）|

- 输出：--all-assets：`#judged=N/M`＋未判定行 `assets.id	assets.value`（P1 exit expect「全部资产已判定」）；单值：单行 `in_scope` 或 `out_of_scope`（CIDR/后缀机械匹配，非 LLM，§4.4；account-grant 行另对 account 维度判定）【推导】。
- 拒收条件：—（只读；Tier 0 职能之一：add-asset 内联调用，§8.5）。
- 依据：定稿 §4.4/§8.5 Tier0/§5.2 P1 duty（每资产 scope-check 内联）+P1 exit／契约01 §3.2+§3.6。时机：P1 duty 每资产；P1 exit 断言；add-asset 内联。

### 27. budget-check〔查询 9/12〕
- 签名：budget-check【推导：无参——对照 goals 三元组+各叶份额（02 §2 行 9 标参数探知项 5）】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无参数）|—|—|【推导】|
|（对照输入）|—|内置|goals.budget（根三元组）+intents.budget_share（叶）+budget.tsv 流水上卷|

- 输出：树形余量 JSON 单行：`{"goal":{"budget":"token;requests;hours","used":{...},"left":{...}},"intents":[{"id":"INT-…","share":{...},"left":{...}}]}`【推导：投影字段=goals.budget/intents.budget_share/budget.*_delta】。
- 拒收条件：—（只读；不豁免测绘 intents，§8.7）。
- 依据：定稿 §4.10/§8.7/§5.2 P3⓪／契约01 §3.12+§3.1+§3.3。时机：P3 每轮⓪（checkpoint 后）。

### 28. cleanup-checklist〔查询 10/12〕
- 签名：cleanup-checklist [--verify]
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--verify|旗标|否|【推导】（定稿载 P6.0 用法；旗标非字段）|
|（提取键）revert_cmd 非空|—|内置|timeline.revert_cmd（纯账本状态行 revert_cmd 为空不列）|

- 输出：默认：`#items=N`＋每行 `timeline.timestamp	timeline.event	timeline.revert_cmd	<status>`（全部外部副作用写操作清单→逆序执行 revert_cmd）；--verify：`all_reverted` 或 `exemptions_complete` 或 `FAIL<TAB>未核销行`（P6.0 exit expect「全部 reverted 或 豁免行齐备」；豁免=approvals 行齐备）。
- 拒收条件：—（只读清单；执行 revert 属清理动作非本命令）。
- 依据：定稿 §5.2 P6.0 duty+exit/§4.10 revert_cmd／契约01 §3.11+§3.8。时机：P6.0 清理门全流程。

### 29. set-cred-status（ledger-set-cred-status）【专用六条之一】〔查询 11/12〕
- 签名：set-cred-status --id=<creds.id> [--status=<creds.status>] [--note=<creds.note>]【推导：无 --status=查询模式；带 --status=变更模式（追加事件溯源行）——「creds 事件溯源状态查询/变更」双模式起草，对应 02 探知项 2 归类冲突】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--id|文本(行 id 引用)|是|creds.id|
|--status|枚举|否|creds.status（active/expired/invalidated/revoked）|
|--note|文本|条件|creds.note（变更附原因）【推导】|
|--approval|文本(行 id 引用)|条件|approvals.id（复活引用）【推导】|

- 输出：查询模式：单行 `creds.id	creds.status`（事件溯源取最新）；变更模式：`OK`＋追加行回显（15 字段同 id 新行）。
- 拒收条件（变更模式；查询模式只读）：--id 引用闭合失败=REJECT；status∉{active,expired,invalidated,revoked}=REJECT；revoked/invalidated→active 复活无 --approval 指向 approved 行=REJECT【推导：对照 intents blocked 不可自动复活+approvals 引用语义（§6.6 凭据刷新后人工复活）】；note 附原因（凭据失效→依赖 intent 转 blocked 的原因链）【推导】。
- 依据：定稿 §4.10/§5.3/§6.6 护栏（会话过期→creds 转 expired→依赖 intent 转 blocked→凭据刷新后人工复活）／契约01 §3.13+§3.8。时机：P3 events cred-obtained 后续状态维护；§6.6 身份矩阵差分子流程。

### 30. redact-scan（ledger-redact-scan）【专用六条之一】〔查询 12/12〕
- 签名：redact-scan --target=<路径>【推导：--target 值=目录/文件路径，无账本字段对应；定稿仅载用法 --target report/（P5）】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--target|文本(路径)|是|【推导】（定稿载用法 --target report/）|

- 输出：`PASS	leaks=0` 或 `FAIL	leaks=N`＋`文件:行号` 清单（对报告全文占位符 {{vault:cred-N}} 扫描；任一真值残留=阻断导出——P5.5 前置交付前终检，非 REJECT 落账）。
- 拒收条件：—（只读扫描；拦截语义=阻断导出，§8.4 关卡 4）。
- 依据：定稿 §8.4 关卡4/§5.2 P5 exit（expect「占位符零泄漏」）／契约02 §2 行 12。时机：P5 exit 断言；P5.5 前置。

## 3 校验命令（6 条，§5.3）〔第 31-36 节〕

### 31. validate（ledger-validate）〔校验 1/6〕
- 签名：validate [--tables=<表名清单>]（P0 用法 `--tables goals,scope,creds`；缺省=全 13 表【推导】）
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--tables|表名清单|否|【推导】（定稿载 P0 用法；值为 13 表名子集）|
|（校验对象）|—|内置|13 表全字段行级校验+FD/EV 卡片同值性|

- 输出：校验=PASS/FAIL+原因：`PASS` 或 `FAIL`＋每错误一行 `<表>	<行号/id>	<原因>`（top-N；原因∈列数/ID 格式/枚举/转义/引用闭合/dedup_key 唯一/卡片与 TSV 不一致）。
- 拒收条件：—（校验命令）。
- 依据：定稿 §4.1（行级校验）/§4.11（卡片与 TSV 不一致=validate 失败）/§5.2 P0 exit+P1 exit+P4 exit／契约01 全 13 表。时机：P0/P1/P4 exit 断言。

### 32. verify-chain（ledger-verify-chain）〔校验 2/6〕
- 签名：verify-chain【推导：无参——全链校验（02 §3 行 2 标参数探知项 5）】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无参数）|—|—|【推导】|
|（校验对象）|—|内置|timeline.prev_hash/timeline.hash 逐行重算+九门 exit 断言事件存在性|

- 输出：`PASS` 或 `FAIL	断链行=<n>`＋缺失门事件清单（跳门检测：每门出口断言的命令调用必产生 timeline 事件，缺记录=FAIL——P4 verify-chain+validate 可发现缺门记录，§5.1）。
- 拒收条件：—（校验命令）。
- 依据：定稿 §4.10（链式哈希，改任何历史行即断链可见）/§5.1/§5.2 P0 exit+P4 exit／契约01 §3.11。时机：P0/P4 exit 断言。

### 33. hash-recheck（ledger-hash-recheck）〔校验 3/6〕
- 签名：hash-recheck【推导：无参（02 §3 行 3 标专属校验内容探知项 5）】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无参数）|—|—|【推导】|
|（校验对象·推导草案）|—|内置|E-index.content_hash_raw/content_hash_norm 对 E-index.artifact_path 工件重算比对＋goals.auth_sha256 对 goals.auth_doc 重算比对【推导】|

- 输出：`PASS` 或 `FAIL`＋每失配一行 `<EV-/G- id>	<失配列>`（top-N）。
- 拒收条件：—（校验命令）。
- 依据：定稿 §5.2 P4 exit（四校验之一）/铁律4（证据双哈希）／契约01 §3.9+§3.1。**专属校验范围定稿未载→本节对象为【推导】猜测草案，见文末无法起草项 2**。时机：P4 exit 断言。

### 34. matrix-audit（ledger-matrix-audit）〔校验 4/6〕
- 签名：matrix-audit [--sample-ratio=<比例>]【推导：常量定稿载 p4_sample_ratio=0.2（§5.2 constants），此处参数化起草、默认 0.2】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--sample-ratio|浮点|否|【推导】（默认=0.2）|
|（抽查对象）|—|内置|matrix.state∈{-,!} 格；告警源=批量置态与 facts 密度对照|

- 输出：`PASS	sampled=N	warnings=0` 或 `FAIL`＋抽查未过格清单（`matrix.attack_surface	matrix.vuln_class	matrix.state	matrix.reason`）＋告警清单（批量置态与 fact 密度不符——§8.3 注入防护④）。
- 拒收条件：—（校验命令）。
- 依据：定稿 §5.2 P4 duty+exit（expect「抽查通过 且 无告警」）/§8.3④／契约01 §3.10+§3.4。时机：P4 exit 断言。

### 35. state-rebuild（ledger-state-rebuild）【专用六条之一】〔校验 5/6〕
- 签名：state-rebuild【推导：无参——从 timeline+提交文件全量重建后对账 state.md（02 §3 行 5 标参数探知项 5）】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|（无参数）|—|—|【推导】|
|（重建源）|—|内置|timeline.tsv（第一事实源）+submissions/ 提交文件→13 表重建→对账 state.md（revision 号）|

- 输出：`PASS	revision=<n>`（state.md 与账本重建结果一致）或 `FAIL`＋差异项清单（top-N）。
- 拒收条件：—（校验命令；kill -9 半写兜底：state 写入走 temp/rename 原子替换带 revision 号，§4.1）。
- 依据：定稿 §4.1 journal 职能/§5.2 P0 entry（resume 态判定）/§9.2（kill -9 续跑保真度指标）／契约01 §1。时机：P0 entry（恢复会话）；断电/kill -9 恢复协议。

### 36. set-replay-state（ledger-set-replay-state）【专用六条之一】〔校验 6/6〕
- 签名：set-replay-state --id=<E-index.id｜findings.id> --state=<三态> [--note=<附注>]【推导：--id 取重放对象（EV 卡片盲重放→E-index.id；finding 级处置→findings.id）；--state∈{VERIFIED,REPAIRED,REJECTED}；--note 落 timeline.event 附注——三态无 142 字段直接对应列，见文末无法起草项 4】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--id|文本(行 id 引用)|是|E-index.id（重放对象 POC）／findings.id（处置对象）【推导】|
|--state|枚举|是|【推导】（VERIFIED/REPAIRED/REJECTED，定稿载三态；无对应表列）|
|--note|文本|否|timeline.event 附注【推导】|
|（联动写）exploitation_status|枚举|命令联动|findings.exploitation_status（VERIFIED→verified 才维持 C1；REJECTED→ruled_out/suspected）【推导：§4.7「由 P4 重放门维护」】|
|（联动写）confidence|枚举|命令联动|findings.confidence（REJECTED→降 C3 或转 fact）【推导】|

- 输出：`OK<TAB>replay:<id>:<state>`＋timeline 事件回显＋受影响 findings 联动行【推导】。
- 拒收条件（落账命令，归类校验组但具备写语义）：--id 引用闭合失败=REJECT；state∉三态=REJECT；同一 --id 重放=REPAIRED 的重试计数>max_retry=2=REJECT【推导：§5.2 back_edges max_retry】。
- 依据：定稿 §5.3/§5.2 P4 duty（批次 4 起强制：fresh 隔离子代理只拿 EV 卡片盲重放）+back_edges（REPAIRED=修复 POC 卡片后重放）/§4.7／契约01 §3.9+§3.5+§3.11。时机：P4 重放门。

## 4 特殊（1 条，§5.3）〔第 37 节〕

### 37. matrix-init〔特殊 1/1〕
- 签名：matrix-init [--vocab=<VOCAB 版本引用>] [--surfaces=<in_scope 攻击面清单>]【推导：列从 VOCAB（WSTG v4.2 全集，版本化）钉死（§5.2 P2 duty 定稿载语义）；行键攻击面默认取账本 assets（in_scope）清单——参数字段对应 matrix.attack_surface／assets.value；显式传入为覆盖参起草】
- 参数：

|参数|类型|必填|取自表.字段|
|---|---|---|---|
|--vocab|文本(版本引用)|否|【推导】（默认 shared/VOCAB.md，WSTG v4.2 版本化）|
|--surfaces|多值|否|matrix.attack_surface（值源自 assets.value，in_scope）【推导】|
|（内部）全行 state|枚举|命令铸造|matrix.state=空（未检查——空必须消灭=终态门禁分母）|
|（内部）schema_version / updated|—|常量/命令铸造|matrix.schema_version=2 / matrix.updated|

- 输出：`OK	rows=<N>`（matrix.tsv 长表生成：Σ|in_scope 攻击面|×|WSTG v4.2 全集| 行、state 全空；后续置格走 matrix-set）。
- 拒收条件：matrix.tsv 已初始化=REJECT（重复 init 清空既有置格=破坏事件溯源）【推导：幂等保护】；无 in_scope 资产（P1 测绘未完成）=REJECT【推导：P2 exit「覆盖全部 in_scope 攻击面」前提】；--vocab 版本缺失/不匹配=REJECT【推导：版本化钉死】；Tier 0 通用基线（无 goals 行=REJECT）。
- 依据：定稿 §5.2 P2 duty（列从 VOCAB 钉死→冻结）/§4.10（长表+闭合率分母）／契约01 §3.10+§3.6。时机：P2 duty（matrix-init 后立即 matrix-freeze）。

## 无法起草项（上下文不足以推导，留空待仲裁）

1. **converge-check 收敛四条件清单**——定稿仅称「收敛四条件可计算」（§3.3）「与持续生长共存」（§5.4），四条件本身未列（02 探知项 6）；第 22 节仅起草输出二值格式（converged／budget-exhausted），判定内容留空。
2. **hash-recheck 专属校验范围**——P4 四校验之一（§5.2），内容定稿未载（02 探知项 5）；第 33 节「证据双哈希+授权书哈希重算」为标【推导】的猜测草案，真实范围待仲裁。
3. **matrix-freeze 冻结状态的持久化载体**——matrix.tsv 7 字段无 frozen 列（契约01 §3.10），142 字段全集内无对应；第 15 节以 timeline 事件（event=matrix-freeze）为【推导】载体，正式载体待仲裁（与 01 探知项 1 schema_version 冲突相关）。
4. **set-replay-state 三态（VERIFIED/REPAIRED/REJECTED）的落账列**——E-index 16 字段与 findings 18 字段均无 replay_state 列；findings.exploitation_status（verified/suspected/ruled_out）仅部分映射（VERIFIED→verified），REPAIRED/REJECTED 无字段位；第 36 节以 timeline 事件+联动行【推导】草案。
5. **checkpoint 的 state.md 内部行结构**——state.md 非 13 表成员（§3.4 目录项），142 字段全集外；第 13 节仅推导 revision 号与 temp/rename 写入协议，行结构（≤200 行 handoff 字段清单）留空。

**范围外备注**：§5.2 exit 断言另引用 4 条不在 §5.3 37 面内的命令——ledger-scope-coverage（P0 exit）/ledger-tree-check（P1 exit）/ledger-terminal-gate（P5 exit）/ledger-replay-summary（P4 exit）。定稿两处清单不一致，本稿按 §5.3 37 条起草，不代拟这 4 条（待仲裁后另补）。

## 自验（起草稿自检证据，命令实测输出）

- **37 节计数**：`grep -c '^### [0-9]' contracts/02a-command-signatures-draft.md` = **37**；分组 `grep -c '〔写 [0-9]'`=**18**、`'〔查询 [0-9]'`=**12**、`'〔校验 [0-9]'`=**6**、`'〔特殊 [0-9]'`=**1**（合计 37=§5.3 口径 18+12+6+1）；37 命令名逐名 `grep -q "^### [0-9]*\. <name>"` 全命中（37/37）。
- **参数字段溯源（grep 证据）**：以契约 01 逐表字段行构建白名单——`awk '/^## 4 /{t=""} /^### 3\.[0-9]+ /{t=$3; sub(/\.tsv.*$/,"",t)} t!="" && /^\| [a-z_][a-z_0-9]* \|/{print t"."$2}' contracts/01-ledger-schema.md | sort -u` = **142 行**（与 01 自验「合计 142/142」全等）；本稿全部 `表.字段` 引用 `grep -oE '\b(goals|scope|intents|facts|findings|assets|edges|approvals|E-index|matrix|timeline|budget|creds)\.[a-z_0-9]+' | grep -v '\.tsv$' | sort -u` = **142 个不同引用**；差集 `comm -23 <本稿引用> <白名单>` = **空**——不存在 01 之外的发明字段（142 字段全集恰好全数引用）。
- **【推导】计数**：正文 37 节内 `grep -o '【推导】' | wc -l` = **63**（签名/参数 45＋拒收/语义 18 处推导点）；含本自验节内 2 处字面提及，全文共 65。
- **无法起草项**：`grep -c '^[0-9]\. \*\*'` = **5**（converge-check 四条件／hash-recheck 校验范围／matrix-freeze 冻结载体／set-replay-state 三态落账列／checkpoint state.md 行结构）＋范围外备注 1（§5.2 exit 断言引用的 4 条非 37 面命令不代拟）。
- **未改动 02**：本稿为唯一新增文件，contracts/02-commands.md 未触碰（md5=9d3ac60069ffb527bb7046c7ebe19302 前后一致）。


## 终审补全（2026-09-23·五项无法起草点落账）

1. **converge-check 收敛四条件**：从定稿 §5.4 誊——空格清零（主矩阵+子矩阵）/预算树未穿/无 unconsumed fact/无 blocked intent（语义以定稿 §5.4 收敛判定为准）。
2. **hash-recheck 校验范围**【推导转正】：timeline.tsv 全链重算（逐行 prev_hash→hash 连锁验证，任何历史行篡改即断链）+ E-index content_hash 双轨抽验（raw+normalized）。
3. **matrix-freeze 载体**：matrix.tsv 新增第 8 列 frozen_at（锚点行冻结时间戳，空=未冻结；不可重复冻结=拒收条件）。
4. **set-replay-state 落账列**：目标=findings.exploitation_status（verified/suspected/ruled_out 三态，§4.7 已载由 P4 重放门维护——不新增列）。
5. **checkpoint state.md 行结构**：属批次 3 接口（常驻集/state 格式批次 3 冻结），本批不代拟。（→ 批次 3 T4 已冻结、2026-09-24 勘误补记回注闭环·G-6/G-10）

## 九门断言四命令（41 面终审并入）

签名同校验类范式：ledger-scope-coverage（P0 出口：对照 scope 全覆盖）、ledger-tree-check（P1 出口：资产树完整性）、ledger-replay-summary（P4 出口：重放门三态汇总）、ledger-terminal-gate（P5 出口：终态门禁断言）——参数=无（读账本），输出=PASS/FAIL+原因清单，拒收=账本缺失/链断。【推导转正】

## v2 勘误补记（2026-09-24·批次 3 施工期·G-6/G-10 裁决）

批次 3 T4 冻结 state.md v2 行结构并升级 checkpoint（终审补全 5「属批次 3 接口，本批不代拟」的落账），本节按 G-6/G-10 建议裁决回注。勘误通道：微版本勘误（零存量数据期，同批次 1「v2 勘误」与 2026-09-24 契约⑨ G-1 同批次先例），schema_version 保持 =2 不递增；本补记日期 2026-09-24。

### G-10：checkpoint 签名回注（第 13 节参数表补全）

- 签名（终局）：`checkpoint --timestamp=<ISO8601> --session=<会话标识> [--phase=<timeline.phase>] [--event=<timeline.event>] [--release] [--round=<n>] [--note=<handoff 文本>] [--spawn=<fresh|auto|manual>]`
- 参数追加：--timestamp（必填，批次 1 确定性口径——落账时间戳一律取自参数，禁 datetime.now() 进账本）；--session（必填，单活跃会话锁的持锁方标识）；--release（旗标，命令内本地归一 --release=1：置 session_status=released）；--round（P3 轮次，缺省 0）；--note（多行文本→state.md handoff 段）；--spawn（会话血统枚举 {fresh,auto,manual}，缺省 fresh）。--phase/--event 语义不变（九门枚举/事由）。
- 输出 schema 不变：`OK<TAB>revision=<n>`（41 面冻结的唯一例外=本命令；例外边界=终审补全 5+批次 3 计划 Global Constraints 明文授权）。
- 拒收条件补全：--spawn∉{fresh,auto,manual}=REJECT；--note 致 state.md 超 200 行硬顶=REJECT（写前预检，timeline 零变更）；state.md 损坏=REJECT（提示 rebuild-state 对账重建）；单活跃会话锁：state.md session_status=active 且 session≠--session=REJECT（接管走 tanyin-phases restart --spawn manual）。
- revision 语义（批次 3 裁决钉死）：revision ≡ 本次 checkpoint 落账后 timeline 总行数（state-rebuild 对账基准=timeline 行数，既有口径不变）。

### G-6：state.md v2 键表回注（第 13 节「state.md 内部行结构」补全）

行结构：全文 ≤200 行硬顶；固定段在前、`--- handoff ---` 分隔行、handoff 自由文本行在后；写入=tmp+os.replace 原子替换（kill -9 半写兜底：要么旧版要么新版，无第三态）。冻结单一实现=cli/ledger/state_md.py（KEY_ORDER；checkpoint 与 tanyin-phases rebuild-state 共用，防双份清单漂移），字节基线=tests/golden/write-checkpoint.state：

|序|键|取值/铸造|
|---|---|---|
|1|revision|≡ 落账后 timeline 行数（见 G-10 节）|
|2|goal|goals.tsv 首行 id|
|3|phase|checkpoint --phase（九门或空；收官态不编码——由 gate-exit:P6 事实承载）|
|4|round|checkpoint --round（缺省 0）|
|5|session|checkpoint --session（持锁会话标识）|
|6|session_status|active / released（--release 置 released）|
|7|spawn|fresh / auto / manual|
|8|updated|--timestamp（ISO8601，确定性）|
|9|resume_kit|常量 resume-kit.md（恢复工件锚）|
|10|snapshot|intents_pending=N;facts_unconsumed=N;matrix_gaps=N;budget_token_left=N（账本重算投影；无 token 上限时末位留空）|

对账与重建：state-rebuild（校验面，第 35 节）对账 revision≡timeline 行数+snapshot 与账本重算一致+结构/枚举/行数；tanyin-phases rebuild-state（恢复面）以 timeline 为第一事实源对账重建（链断拒绝自愈，halt 人工处置）。

## v2 勘误补记（2026-09-24·批次 4 施工期·G-12 裁决）

§8 add-asset 拒收条件勘误（微版本，零存量数据期，schema_version 保持 =2 不递增，同上 G-6/G-10 补记先例）：type 枚举九值→**十一值**（+cloud-storage/human-factor；细分落 meta=sub:object-bucket|database|queue|cloud-metadata|cdn-origin|email|account|leaked-credential|sso|vendor-portal）；「type∈{pivot,foothold} 批次 4 前启用=REJECT」分支退役（§4.8「后两类批次 4 启用」兑现）。同批联动：契约 01 §3.6、契约 07 §2、phases/PROTOCOL.md §4（索引见 contracts/README.md）。

## v2 勘误补记（2026-09-24·批次 4 施工期·G-2 裁决）

裁决 A（G-2 新资产子矩阵行铸造）落地，§12 拒收条件行按本补记勘误。勘误通道：微版本勘误（零存量数据期，同上先例），schema_version 保持 =2 不递增。

- 行键不存在且 reason 前缀 submatrix: 且基线已冻结且为全新表面→放行：原子铸造该表面×VOCAB 全集行（目标行取 --state/--reason/--intent-id，其余 state 空+裸前缀；timeline 事件 `submatrix-mint <surface> classes=<n> vocab=<ver>@<sha>`）。四条件缺一即 REJECT：reason 前缀非 submatrix:；基线未冻结（无 frozen_at 非空行——submatrix 语义只存在于冻结后）；表面已存在于既有行键（防主矩阵偷扩张）；vuln_class 不在 VOCAB 全集。分母诚实：新表面全词表立即进入闭合率分母，杜绝「少铸行刷闭合率」；全量校验后一次写入（state 枚举/reason 附带/intent 引用闭合对铸造行同样生效）。
- reason 前缀规则修正=旧前缀空→任意前缀首次归类放行，旧前缀非空且≠新→REJECT（G-2 裁决，2026-09-24）——修正原「前缀与行类别不符=REJECT」对首次归类的潜伏阻塞（init 行 reason 为空→设 authz-diff: 前缀即 REJECT，身份矩阵差分无法落格）。
- authz-diff: 前缀边界不变：仍限主矩阵既有键（差分落标准格，设计 §4.10）；新表面上的鉴权观察以 submatrix: 前缀落格（差分语义由 intent kind=authz-diff+E-index pair_group 承载，不依赖矩阵前缀）。

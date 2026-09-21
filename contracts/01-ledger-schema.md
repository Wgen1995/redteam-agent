# 01 账本 Schema 契约（13 表 + 10 边）

> 来源：定稿 §4.1–§4.10（含 §4.2 CB-1 口径裁定；个别行内辅引 §2.5/§5.2/§8.1/§11 并随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口①（13 表 schema+schema_version=2 全字段）与接口②（10 边词汇）的誊录件（定稿 §11 批次 0 行）。只誊不创：全部语义来自定稿；「类型」列为依定稿示例/语义给出的标注（定稿未逐列定义物理类型，未标注处一律为文本）；「枚举/约束」「说明」列均为定稿原文语义。

## 1 编码与 ID 规范（§4.1，命令层强制）

- 文件：TSV，UTF-8 无 BOM + LF，写命令内部钉死编码；全表带 `schema_version` 列（定稿值 = `2`）。
- 转义：字段内禁字面 tab/CR/LF；转义顺序 \\ → \\\\、tab → \\t、CR → \\r、LF → \\n；写命令转义、读命令反转义，LLM 不手工转义。多值字段 `;` 分隔，字段内字面 `;` 转义为 \\;。
- 参数化：账本命令参数经临时文件/stdin 传入，禁止字符串拼接进命令行——目标数据（网页标题/响应头）是注入载体。
- 目标数据清洗：进账本前过清洗（剥离控制字符、截断超长）。
- ID 铸造：`{前缀}-{goal-id}-{四位序号}`，定宽零填充，字典序=时间序；由 ledger-next-id 原子分配；子代理/引擎无铸造权。前缀表：G(goal)/S(scope)/INT/F(fact)/FD(finding)/AST(asset)/E(edge)/AP(approval)/EV(evidence)/CRED(cred)/PG(pair_group)。
- 单写者：所有写操作由总控串行执行；子代理/引擎只产 submissions/&lt;intent-id&gt;/submission.json，总控验收后落账。
- 事件溯源：intents/matrix/creds 状态变更=追加新行（同 id 多行），「取最新」是账本命令；finding 合并=supersedes 边+tombstone，不删行。写前拒收：每条写命令自带行级校验（列数/ID 格式/枚举/转义/引用闭合/dedup_key 唯一），畸形 REJECT 不部分写入。
- journal 职能：timeline.tsv 是第一事实源，全部 13 表可由 timeline+提交文件全量重建；ledger-state-rebuild 校验 state.md 与账本重建结果一致（kill -9 半写兜底：state 写入走 temp/rename 原子替换并带 revision 号）。

## 2 总表清单（§4.2）

| # | 表 | 性质 | 写入命令 | 定稿要点 |
|---|---|---|---|---|
| 1 | goals.tsv | 纯追加 | ledger-add-goal | +dollar_budget/model_tier/guard_tier |
| 2 | scope.tsv | 纯追加（amendment 行） | ledger-add-scope / ledger-amend-scope | +kind 扩展 oob/account-grant；+accounts/permitted_actions/修订审计 |
| 3 | intents.tsv | 事件溯源 | ledger-add-intent / ledger-set-intent-status | +kind / budget_share |
| 4 | facts.tsv | 纯追加 | ledger-add-fact | kind +authz |
| 5 | findings.tsv | 纯追加（tombstone） | ledger-add-finding / ledger-supersede-finding | +exploitation_status/auth_context/dedup_key/scope_check/card_path |
| 6 | assets.tsv | 纯追加 | ledger-add-asset | type +pivot/foothold（批次 4） |
| 7 | edges.tsv | 纯追加 | ledger-add-edge | 10 边口径钉死 |
| 8 | approvals.tsv | 纯追加 | ledger-approve | 逐条审批+签发+知识审批+豁免全落此表 |
| 9 | E-index.tsv | 纯追加（只增不覆盖） | ledger-add-evidence | +network_position/card_path；四要素进卡片 |
| 10 | matrix.tsv | 事件溯源（长表） | ledger-matrix-set（matrix-init 生成） | authz 差分落标准格 |
| 11 | timeline.tsv | 链式哈希追加 | ledger-append-timeline | +revert_cmd 列（哈希输入含全行） |
| 12 | budget.tsv | 纯追加流水 | ledger-budget-log | +dollars_delta（默认 0）/scope 列（树化） |
| 13 | creds.tsv（新增） | 事件溯源 | ledger-add-cred / ledger-set-cred-status | 身份矩阵落地（ADR-P4③） |

> 口径裁定 CB-1（creds/sessions 实体口径，§4.2）：session 落地为 creds.tsv 的 `kind=session` 行：会话令牌本质是短时效凭据，字段同构（秘密入 vault、生命周期、获取来源），拆两表将重复校验逻辑且账本变 14 表、破坏 13 表口径。身份矩阵差分按 `kind+role` 分组重放（§6.6）。凡定稿写「creds/sessions 实体」处均指 creds.tsv 的两类行。

## 3 逐表字段定义

### 3.1 goals.tsv（立项档案，§4.3）

性质：纯追加 · 写入命令：ledger-add-goal · 每次测试一行。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 G（§4.1 前缀表），`{前缀}-{goal-id}-{四位序号}` 定宽零填充 | 立项唯一标识 |
| target | 文本 | — | 目标（域名/IP/网段/源码包；§8.1 八问①落账位） |
| objective | 文本 | — | 测试目标（§8.1 八问④ RoE 附注落账位） |
| auth_doc | 文本 | 空=REJECT | 授权书路径（授权结构化） |
| auth_sha256 | 文本（hex） | 空=REJECT | 授权书 sha256 |
| signer | 文本 | 空=REJECT | 签署方 |
| valid_from | 时间戳 | 空=REJECT | 授权有效窗口起 |
| valid_until | 时间戳 | 空=REJECT | 授权有效窗口止 |
| rate_limit | 数值 | req/s | 速率限制 |
| window | 文本 | 如 09:00-18:00 | 测试时间窗 |
| emergency_contact | 文本 | — | 紧急联系人（§8.1 八问⑦落账位） |
| budget | 三元组（`;` 分隔整数） | `token;requests;hours`（如 2M;50000;40） | 预算三元组（goal 根，§8.7） |
| dollar_budget | 浮点或空 | 空=第四维关闭 | ADR-P4⑥；开启时 evals 增列 |
| language | 文本 | — | 报告/沟通语言（§8.1 八问⑤落账位） |
| business_context | 文本 | — | P0 业务问卷摘要 |
| model_tier | 枚举 | ∈{strong,weak} | 安装自检写入 |
| guard_tier | 枚举 | ∈{T1,T2,T3} | 实际执法档位快照，报告披露依据 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

授权硬语义（§4.3）：授权结构化（授权书路径+sha256+签署方+有效窗口，空=REJECT，不存在「先记上再补」）。

### 3.2 scope.tsv（授权白名单，§4.4）

性质：纯追加（amendment 行） · 写入命令：ledger-add-scope / ledger-amend-scope。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 S（§4.1） | 行唯一标识 |
| kind | 枚举 | ∈{include,exclude,oob,account-grant} | 行类型 |
| matcher | 文本 | CIDR 网段/域名后缀/通配（include/exclude 用）；account-grant 行=资产；oob 行=回连白名单端点 | 匹配对象 |
| account | 文本 | 测试账号或 CRED 引用 | account-grant 行用 |
| permitted_actions | 多值（`;` 分隔） | 如 `login;read-profile;write-order` | 动作清单 |
| amendment_of | 文本（行 id 引用） | =被修订行 id | 修订行指向被修订行 |
| note | 文本 | 修订行=修订理由+批准人 | 备注 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

补充约束（§4.4）：
- oob=OOB 回连白名单端点（DNS/HTTP 回连接收方申报）；未申报的回连被 Tier 3 默认拒绝且记 fact。
- account-grant=账户级授权行：matcher=资产，account=测试账号或 CRED 引用，permitted_actions=`;` 分隔动作清单。
- amendments：修订不删行不改行——追加新行，amendment_of=被修订行 id，note=修订理由+批准人；生效判定=沿 amendment 链取最新（命令实现）；P0 后修订必须伴随 approvals 行。
- 硬门不变：资产落账命令强制对照 include/exclude，界外自动标 out_of_scope 且账本级禁止派生 intent；判定是 CIDR/后缀机械匹配（非 LLM）。

### 3.3 intents.tsv（假设账本，§4.5）

性质：事件溯源 · 写入命令：ledger-add-intent / ledger-set-intent-status。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 INT（§4.1） | 假设唯一标识 |
| title | 文本 | — | 标题 |
| detail | 文本 | — | 详情 |
| status | 枚举 | candidate→pending→active→done/blocked，或 candidate→rejected（附理由）/deferred（附激活谓词）；blocked 不可自动复活，复活须 approvals 引用 | 状态机 |
| engine | 文本 | 目标引擎名 | 派发引擎 |
| kind | 枚举 | ∈{recon,surface,matrix-test,deep-dive,authz-diff} | 引擎段映射 §6.3 |
| origin | 枚举 | ∈{entity,concept,precedent,adjacency,llm,recon-event,mixed} | 假设来源 |
| score | 浮点 | 0-1 | 先验分（命令计算，公式见 §8.7） |
| via | 文本 | 命中知识页引用 | 知识溯源 |
| dedup_key | 文本 | 资产+技法类；命令机械计算；重复键 REJECT | LLM 只提议不判重 |
| budget_share | 三/四元组（`;` 分隔） | `token;requests;hours[;dollars]` | 预算树叶节点 |
| activation | 结构化谓词 | `field;op;value` | deferred 用，命令评估 |
| reason | 文本 | rejected/blocked/deferred 强制 | 状态变更原因 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 3.4 facts.tsv（§4.6）

性质：纯追加 · 写入命令：ledger-add-fact。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 F（§4.1） | fact 唯一标识 |
| intent_id | 文本（行 id 引用） | 引用 INT | 来源 intent |
| kind | 枚举 | ∈{port,service,http,info,vuln-clue,authz} | authz=身份矩阵差分观察（§6.6） |
| target | 文本 | — | 观察对象 |
| detail | 文本 | 落账即脱敏 | 观察内容 |
| confidence | 浮点 | 0-1 | 置信度 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

补充约束（§4.6）：每条 fact 要么被消费（derived_from 出边）要么显式标记不消费（附理由）——「看见不管」暗区被收敛判定消灭。

### 3.5 findings.tsv（§4.7）

性质：纯追加（tombstone） · 写入命令：ledger-add-finding / ledger-supersede-finding。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 FD（§4.1） | finding 唯一标识 |
| intent_id | 文本（行 id 引用） | 引用 INT | 来源 intent |
| title | 文本 | — | 标题 |
| confidence | 枚举 | ∈{C1 实证复现, C2 条件实证（须附条件可达性证据否则降 C3）, C3 风险线索, ➖🛑 不可利用/已阻断} | 两维评级之一（负结果同样入账） |
| impact | 枚举 | ∈{高,中,低} | 两维评级之一（CVSS 式影响域） |
| exploitation_status | 枚举 | ∈{verified,suspected,ruled_out} | Strix 三态；由 P4 重放门维护：VERIFIED 才维持 C1，REJECTED 降 C3 或转 fact |
| auth_context | 文本 | 空（未认证）或 `CRED-{id}` | 身份矩阵差分产物 |
| dedup_key | 文本 | affected_asset+vuln_class+variant；命令计算 | finding 级键 |
| scope_check | 枚举 | ∈{in_scope,boundary-verified} | 范围判定 |
| description_brief | 文本 | ≤200 字 | 叙述进卡片 |
| reproducible_steps | 多值 | ≥1 强制 | 无可复现步骤的观察一律是 fact（铁律 4） |
| affected_asset_id | 文本（行 id 引用） | 引用 AST | 受影响资产 |
| evidence_ids | 多值（`;` 分隔） | 引用 EV | 证据 |
| control_evidence_ids | 多值（`;` 分隔） | 引用 EV | control≡counterevidence 统一命名 |
| card_path | 文本 | =findings-cards/FD-{id}.md | 外置卡片路径 |
| status | 枚举 | ∈{active,superseded} | 合并=tombstone 不删行 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 3.6 assets.tsv（§4.8）

性质：纯追加 · 写入命令：ledger-add-asset。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 AST（§4.1） | 资产唯一标识 |
| type | 枚举 | ∈{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold} | pivot/foothold 批次 4 启用：内网跳板/立足点，attack 边承载链式语义 |
| value | 文本 | — | 资产值 |
| meta | 文本 | — | 定稿未单列说明（§4.8 仅列字段名） |
| in_scope | 布尔/枚举 | 由 scope-check 判定（界外=out_of_scope） | 范围内标记 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 3.7 edges.tsv（§4.8；10 边词汇见 §4 本文）

性质：纯追加 · 写入命令：ledger-add-edge。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 E（§4.1） | 边唯一标识 |
| kind | 枚举 | ∈10 边（见下节） | 边类型 |
| source_id | 文本（行 id 引用） | 引用闭合校验（§4.1） | 源节点 |
| target_id | 文本（行 id 引用） | 引用闭合校验（§4.1） | 目标节点 |
| provenance | 文本 | 来源（intent/引擎/人工） | 溯源 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 3.8 approvals.tsv（§4.8）

性质：纯追加 · 写入命令：ledger-approve。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 AP（§4.1） | 审批唯一标识 |
| command_hash | 文本（hex） | P5.5 签发绑定聚合报告文件哈希 | command_hash 绑定不可抵赖 |
| decision | 文本 | — | 审批决定 |
| approver | 文本 | — | 审批人 |
| timestamp | 时间戳 | — | 审批时间（本表无 created 列，定稿字段清单即如此） |
| note | 文本 | — | 备注 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |

补充约束（§4.8）：L3 逐条审批、P5.5 签发（command_hash 绑定聚合报告文件哈希）、P6 知识审批、P6.0 残留豁免全部落此表；审批展示原始命令原文非 LLM 摘述。

### 3.9 E-index.tsv（证据索引，§4.9）

性质：纯追加（只增不覆盖） · 写入命令：ledger-add-evidence。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 EV（§4.1） | 证据唯一标识 |
| title | 文本 | — | 标题 |
| source_type | 枚举 | ∈{command,capture,file,log,manual} | 证据来源类型 |
| observed_at | 时间戳 | — | 观察时间 |
| network_position | 枚举/扩展标量 | ∈{internet,intranet,same-host,jumphost:&lt;name&gt;} | POC 四要素之一进列——网络位置声明是中文报告被质疑复现不了的第一大原因 |
| repro_command | 文本 | 第三方可跑；凭据一律 `{{vault:cred-N}}` 占位符 | 复现命令 |
| repro_kind | 枚举 | ∈{single,sequence,concurrent} | 时序类引用 artifact 内并发脚本 |
| content_hash_raw | 文本（hex） | 双轨之一（raw） | content_hash 双轨 |
| content_hash_norm | 文本（hex） | 双轨之一（normalized：归一化去 nonce/时间戳后哈希） | content_hash 双轨 |
| artifact_path | 文本 | 只增不覆盖（重跑另存 -r2） | 工件路径 |
| card_path | 文本 | →外置证据卡片 | 嵌套四要素部分（§4.11） |
| linked_finding | 文本（行 id 引用） | 引用 FD | 关联 finding |
| pair_group | 文本 | 差分组 | 差分举证分组 |
| raw_excerpt | 文本 | 脱敏+定长截断 | 原始摘录 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 3.10 matrix.tsv（§4.10）

性质：事件溯源（长表） · 写入命令：ledger-matrix-set（matrix-init 生成）。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| attack_surface | 文本 | 长表行键之一 | 攻击面 |
| vuln_class | 文本 | 从 shared/VOCAB.md（WSTG v4.2 全集，版本化）钉死 | 漏洞类（长表行键之一） |
| state | 枚举 | ∈{x 已确认（含负结果）, ? 疑似, - 不适用附理由, ! 环境干扰附记录, 空=未检查} | 五态标记 |
| reason | 文本 | 子矩阵行前缀 `submatrix:`；身份矩阵差分前缀 `authz-diff:` | 置态理由 |
| intent_id | 文本（行 id 引用） | 引用 INT | 置态来源 intent |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| updated | 时间戳 | — | 更新时间（本表用 updated 非 created，定稿字段清单即如此） |

补充约束（§4.10）：空必须消灭（终态门禁）；「-」「!」进 P4 抽查（比例 §5.2 常量 p4_sample_ratio=0.2）；基线冻结（P2 后主矩阵不随新资产扩张，新资产走子矩阵行 reason 前缀 `submatrix:`，冻结的是覆盖率锚点不是探索）；身份矩阵差分按标准格落账（reason 前缀 `authz-diff:`），不设独立矩阵表；闭合率=已置态格/全格，按 WSTG 全集报告。

### 3.11 timeline.tsv（§4.10）

性质：链式哈希追加 · 写入命令：ledger-append-timeline · 第一事实源+审计链+清理台账三职合一。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| timestamp | 时间戳 | — | 时间 |
| actor | 枚举 | ∈{总控,子代理,CLI,人工} | 行为者 |
| phase | 文本 | 九门阶段 | 所处门 |
| event | 文本 | 对外请求记 `request:` 事件；P0 落账 SKILL 版本+tools.lock 哈希；managed-restart 事件记 spawn 方式（auto/manual） | 事件 |
| revert_cmd | 文本 | 分层登记：外部副作用操作（碰目标系统：发请求/落文件/改配置）必填；无逆者填 `irreversible` 并强制 L3 逐条审批；纯账本状态变化留空——其逆=追加新行（§0.3 口径4/§5.5 P6.0） | 该写操作的逆操作命令 |
| prev_hash | 文本（hex） | 链式哈希前值 | 链 |
| hash | 文本（hex） | **哈希输入=本行全部字段含 revert_cmd**——改任何历史行即断链可见 | 链式哈希 |

补充约束（§4.10）：timeline.tsv 是第一事实源，全部 13 表可由 timeline+提交文件全量重建（§4.1 journal 职能）。

### 3.12 budget.tsv（§4.10）

性质：纯追加流水 · 写入命令：ledger-budget-log。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| timestamp | 时间戳 | — | 时间 |
| token_delta | 整数 | — | token 增量 |
| requests_delta | 整数 | — | 请求数增量 |
| hours_delta | 数值 | — | 工时增量 |
| dollars_delta | 数值 | 默认 0 | 第四维关闭不累计；开启后由 driver/宿主计费回填 |
| scope | 文本 | =`goal` 或 `INT-{id}` | 预算树：intent 消耗计入自身份额并上卷 goal 根 |
| note | 文本 | — | 备注 |

补充约束（§4.10）：ledger-budget-check 对照 goals 三元组+各叶份额输出树形余量。

### 3.13 creds.tsv（新增，§4.10+CB-1）

性质：事件溯源 · 写入命令：ledger-add-cred / ledger-set-cred-status · 身份矩阵落地（ADR-P4③）。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 CRED（§4.1） | 凭据唯一标识 |
| kind | 枚举 | ∈{static-cred, session} | static-cred=客户提供：账号密码/API key；session=登录态：cookie/token，由 static-cred 换取或攻击所得 |
| role | 文本 | 业务角色标签（`admin/operator/user/anonymous`…，合法集合由 P0 八问⑧+account-grant 行确定） | 业务角色 |
| username_ref | 文本 | 账号名或脱敏代号 | 账号引用 |
| secret_ref | 文本 | =`{{vault:cred-N}}` 占位符→vault/ 加密条目（真值永不进账本，N=creds 行序号） | 秘密引用 |
| scope_asset | 文本 | — | 凭据适用资产 |
| obtained_via_intent | 文本（行 id 引用） | 引用 INT | 获取来源（攻击所得凭据可追溯） |
| parent_cred | 文本（行 id 引用） | 会话的父凭据 id | session 行用 |
| valid_from | 时间戳 | — | 有效期起 |
| valid_until | 时间戳 | — | 有效期止 |
| status | 枚举 | ∈{active,expired,invalidated,revoked}（事件溯源） | 凭据状态 |
| permitted_actions | 多值（`;` 分隔） | 对照 account-grant | 该身份允许动作 |
| note | 文本 | — | 备注 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

补充约束（§4.10）：
- 硬门：派发 authz-diff intent 前总控校验引用的 CRED 行 status=active 且 permitted_actions 覆盖计划动作；凭据失效→依赖 intent 转 blocked 附原因。
- 材质约定（kind 二分不变）：NTLM hash／私钥／客户端证书等特殊材料仍记 static-cred，材质用 meta 位标注（如 material=ntlm-hash|ssh-key|x509）——批次 4 差分配对按 role×端点，不按材质。
- CB-1（§4.2）：session=creds.tsv 的 kind=session 行；身份矩阵差分按 kind+role 分组重放（§6.6）。

## 4 10 边词汇（接口②，§4.8+§2.5）

边种类官方口径 **10 边**（scope-rel 入列，§2.5）。词汇表小而稳，新增边类型须 bump schema_version（§4.8）。

| # | kind | 方向（定稿原文） | 语义（定稿原文/出处） |
|---|---|---|---|
| 1 | spawns | goal→intent | §4.8 仅载方向，未另述语义 |
| 2 | yields | intent→fact | §4.8 仅载方向，未另述语义 |
| 3 | derived_from | fact→intent | 「未消费 fact」=无 derived_from 出边的 fact（§4.8）；每条 fact 要么被消费（derived_from 出边）要么显式标记不消费（§4.6） |
| 4 | proves | intent→finding | §4.8 仅载方向，未另述语义 |
| 5 | parent | asset→asset | 资产树完整（§5.2 P1 exit：ledger-tree-check --complete parent＝「资产树完整」） |
| 6 | attack | finding&#124;asset→asset&#124;finding | pivot/foothold（批次 4）由 attack 边承载链式语义（§4.8 assets） |
| 7 | cross_ref | 定稿未载方向 | 跨引擎（§4.8） |
| 8 | evidences | finding→EV | EV=证据（E-index.tsv，§4.9） |
| 9 | supersedes | finding→finding | finding 合并=supersedes 边+tombstone，不删行（§4.1/§4.7） |
| 10 | scope-rel | asset→scope | §2.5：边种类官方口径 10 边（scope-rel 入列） |

## 探知项（待仲裁）

1. schema_version 全表覆盖 vs timeline/budget 字段清单：§4.1「全表带 `schema_version` 列（定稿值 = `2`）」；§4.10 timeline.tsv 字段=`timestamp, actor, phase, event, revert_cmd, prev_hash, hash`、budget.tsv 字段=`timestamp, token_delta, requests_delta, hours_delta, dollars_delta, scope, note`——两表字段清单均无 schema_version（亦无 created）。两处冲突，待仲裁。
2. PG 序号格式：§4.1 ID 铸造=`{前缀}-{goal-id}-{四位序号}`（前缀表含 PG(pair_group)）；§4.11 EV 卡片示例 `pair_group: PG-7`（无 goal-id 段、序号未四位零填充）。两处冲突，待仲裁。
3. goals.id 前缀写法：§4.1 前缀表 `G(goal)`；§4.10 budget.tsv scope 列以 goal 根字面量 `goal` 表示（非 G-{id} 形态）。两处对 goal 根的标识写法不一致（G-前缀 id vs 字面量 goal），待仲裁。

## 自验

- **13 表名清单与定稿一致**：`grep -c '^### 3\.' contracts/01-ledger-schema.md` = **13**；定稿 §4.2 表名清单 goals/scope/intents/facts/findings/assets/edges/approvals/E-index/matrix/timeline/budget/creds 与本文 §3.1–§3.13 节名逐名全等（脚本比对=true）。
- **13 表字段数逐表对照（本文/定稿 §4.3–§4.10 字段清单行）**：goals=19/19 · scope=9/9 · intents=15/15 · facts=8/8 · findings=18/18 · assets=7/7 · edges=7/7 · approvals=7/7 · E-index=16/16 · matrix=7/7 · timeline=7/7 · budget=7/7 · creds=15/15；合计 142/142；字段名与顺序逐表全等（脚本比对=true）。
- **10 边**：`awk '/^## 4 10 边词汇/,/^## 探知项/' contracts/01-ledger-schema.md | grep -c '^| [0-9]'` = **10**；清单 spawns,yields,derived_from,proves,parent,attack,cross_ref,evidences,supersedes,scope-rel 与定稿 §4.8 逐名全等=true；定稿 §4.8 边定义行内 10 个 kind 全命中=true。
- **timeline 哈希输入范围**：`grep -c '哈希输入=本行全部字段含 revert_cmd'` = 1（§3.11 hash 行与补充约束双载）；`grep -c 'irreversible'` = 1；`grep -c 'submatrix:'` = 2（matrix reason 前缀两处）。
- **matrix 长表格式**（§3.10：attack_surface×vuln_class 长表行键+五态+submatrix:/authz-diff: 前缀）、**budget scope 列**（§3.12：goal 或 INT-{id}+上卷语义）、**creds 全字段含 §4.10 材质约定行**（§3.13：15 字段+material=ntlm-hash|ssh-key|x509 meta 位+硬门+CB-1）均落文。
- 探知项=3。

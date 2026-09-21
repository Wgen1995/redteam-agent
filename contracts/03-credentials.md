# 03 凭据与身份矩阵契约（接口④⑬）

> 来源：定稿 §8.4+§4.10+§6.6（辅引 §2.5/§3.2/§3.4/§4.2 CB-1/§4.5/§4.9/§4.11/§5.2/§5.4/§6.1/§6.3/§6.5/§8.1/§11 批次 0/§12 R12，随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口④（`{{vault:cred-N}}` 占位符语法+vault 条目格式）与接口⑬（creds 契约：authz-diff intent kind 与差分语义+material meta 位定义，ADR-P4③）的誊录件（§11 批次 0 行）。只誊不创。

## 1 占位符语法（接口④，§4.10/§8.4）

- 唯一占位符语法：`{{vault:cred-N}}`（ADR-P4⑤ 决策 5：同物异名统一为唯一占位符；§0.2 决策 5）。
- N=creds 行序号；secret_ref=`{{vault:cred-N}}` 占位符→vault/ 加密条目；**真值永不进账本**（§4.10）。
- repro_command 中凭据一律 `{{vault:cred-N}}` 占位符（E-index，§4.9）；EV 卡片 preconditions 同（如「持有有效会话 {{vault:cred-3}}」，§4.11）。
- 引擎提交侧字段名=secret_placeholder（submission.json creds 数组：`kind, role, username_ref, secret_placeholder, obtained_via, permitted_actions`，§6.1）——引擎只提议，总控验收后 add-cred 落账。
- vault/ 位于交战区 `$TANYIN_HOME/engagements/<goal-id>/vault/`（§3.4）；vault 条目格式定稿未载→探知项 1。

## 2 vault 四关卡（§8.4 全链路）

| # | 关卡 | 机制（定稿原文语义） |
|---|---|---|
| 1 | 执行前回注 | 凭据真值仅子代理经执行通道在执行点由 guard 从 vault/ 解密注入（总控只见占位符；tanyin-replay 同规则） |
| 2 | 落盘前掩码 | ledger-add-fact / add-evidence 及验收 submission 摘要行时 redact 校验——检出真值模式（cookie/token/密码形态）即 REJECT |
| 3 | 上下文前 tokenize | 凭据永不进总控；submissions 摘要行过 redact 后才可回读上下文 |
| 4 | 交付前终检 | ledger-redact-scan 对报告全文占位符扫描（P5.5 前置，任一真值残留=阻断导出） |

## 3 输出兜底与降级（§8.4 加段）

- **输出兜底重 tokenize**（DarkMoon 模式清洁实现，GPL 不搬码只抄模式）。
- **withheld 降级不拒绝**：无法安全脱敏的内容以 withheld 标记降级呈现，不阻塞流程。
- 交付附**一次性解密通道**（报告可公开流转，授权接收方可解）。

## 4 creds.tsv 全字段（§4.10+CB-1）

性质：事件溯源 · 写入命令：ledger-add-cred / ledger-set-cred-status · 身份矩阵落地（ADR-P4③）。CB-1（§4.2）：session 落地为 creds.tsv 的 `kind=session` 行（会话令牌本质是短时效凭据，字段同构：秘密入 vault、生命周期、获取来源）；身份矩阵差分按 `kind+role` 分组重放（§6.6）；凡定稿写「creds/sessions 实体」处均指 creds.tsv 的两类行。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | 文本 | 前缀 CRED（§4.1），`{前缀}-{goal-id}-{四位序号}` 定宽零填充 | 凭据唯一标识 |
| kind | 枚举 | ∈{static-cred, session}（二分不变，见 §7） | static-cred=客户提供：账号密码/API key；session=登录态：cookie/token，由 static-cred 换取或攻击所得 |
| role | 文本 | 业务角色标签（`admin/operator/user/anonymous`…，合法集合由 P0 八问⑧+account-grant 行确定） | 业务角色 |
| username_ref | 文本 | 账号名或脱敏代号 | 账号引用 |
| secret_ref | 文本 | =`{{vault:cred-N}}` 占位符→vault/ 加密条目（真值永不进账本，N=creds 行序号） | 秘密引用 |
| scope_asset | 文本 | — | 凭据适用资产 |
| obtained_via_intent | 文本（行 id 引用） | 引用 INT | 获取来源（攻击所得凭据可追溯） |
| parent_cred | 文本（行 id 引用） | 会话的父凭据 id | session 行用（§5.4 通路②：parent_cred 链） |
| valid_from | 时间戳 | — | 有效期起 |
| valid_until | 时间戳 | — | 有效期止 |
| status | 枚举 | ∈{active,expired,invalidated,revoked}（事件溯源） | 凭据状态 |
| permitted_actions | 多值（`;` 分隔） | 对照 account-grant | 该身份允许动作 |
| note | 文本 | — | 备注 |
| schema_version | 整数 | =2（§4.1） | 定稿值 |
| created | 时间戳 | — | 创建时间 |

### 4.1 硬门（§4.10）

- 派发 authz-diff intent 前**总控校验**引用的 CRED 行 status=active 且 permitted_actions 覆盖计划动作。
- 凭据失效→依赖 intent 转 blocked 附原因。

### 4.2 材质约定（§4.10 材质约定行）

- NTLM hash／私钥／客户端证书等特殊材料仍记 static-cred，材质用 meta 位标注（如 material=ntlm-hash|ssh-key|x509）。
- 批次 4 差分配对按 role×端点，不按材质。
- meta 位落列与 15 字段清单的关系见探知项 2。

## 5 authz-diff intent kind 与差分语义（§6.6，契约批次 0 定死、实现批次 4，ADR-P4③）

- intents.kind 枚举含 **authz-diff**（§4.5：kind∈{recon,surface,matrix-test,deep-dive,authz-diff}）；引擎段映射：authz-diff→differential.md（身份矩阵差分，批次 4）（§6.3）。
- 前置：creds.tsv 存在 status=active 凭据 ≥1 且 scope 含对应 account-grant 行（§6.6）。
- 生长通路：cred-obtained 事件→登记 creds(kind=session)→触发 authz-diff 候选（批次 4 起）（§5.2 P3 events/§5.4 通路②）。

五步流程（§6.6，挂 web-blackbox 差分段，全部复用既有账本机制）：

| 步 | 内容（定稿原文语义） |
|---|---|
| 1 构造角色×端点矩阵 | 从 facts/assets 提取受保护端点清单（鉴权要求的 endpoint），与 creds 的 role 集合做笛卡尔积生成 authz-diff 候选 intent（信息补全性质，直接 pending 不打分——同资产事件处理器逻辑；计入预算，单端点差分对数上限护栏） |
| 2 逐对差分重放 | 每个 (endpoint, role) 对：用该 role 的会话凭据（`{{vault:cred-N}}` 占位符，guard 在执行点回注）重放标准请求；anonymous 与其他 role 请求作对照——**复用 pair_group**：同端点所有角色请求共享一个 PG；越权判定=差分（B 角色获得 A 角色数据/功能=positive；各角色 403 响应一致=负结果 fact） |
| 3 落账 | positive→finding（auth_context=`CRED-{id}`，exploitation_status=suspected 起步）；负结果→fact(kind=authz)（回归基线）；矩阵格置态 reason 前缀 `authz-diff:` |
| 4 重放门联动 | authz finding 的 EV 卡片 expected.matcher 必填角色/数据标识，P4 重放门验证 |
| 5 护栏 | 差分仅对幂等读接口默认执行；写接口差分须 account-grant permitted_actions 显式覆盖+L3 逐条审批（§12 R12）；会话过期→creds 转 expired→依赖 intent 转 blocked，凭据刷新后人工复活 |

### 5.1 差分判定三条机械规则（写入契约，§6.3）

1. 实验组与对照组响应差异仅在单变量维度→归因成立。
2. 同请求两次结果不同→unstable，confidence 降一级。
3. errorCode/内容类型验证优先于状态码。

### 5.2 身份矩阵投影（§6.5，不新增表）

session-viz 身份矩阵视图=**role×endpoint 覆盖投影**——从 creds×findings 投影生成，不新增表；§0.3 口径 7：authz-diff 置格语义（reason 前缀 `authz-diff:`），不设身份矩阵独立表。

## 6 pair_group 复用（§4.9/§6.6/§4.11）

- E-index.pair_group=差分组（§4.9）；差分组编号前缀 PG（§4.1 前缀表：PG(pair_group)）。
- §6.6 步骤 2：同端点所有角色请求共享一个 PG（对照组 anonymous+其他 role 与实验组同组）。
- EV 卡片承载 `pair_group` 与 `role` 字段（role=authz-diff 证据专用：本请求使用的角色，§4.11）；FD 卡片同载 `pair_group`（§4.11）。
- 负结果降级依赖差分 pair_group 区分防护拦截与代码修复，不误杀（§7.1 learned→core 门槛④ 引用）。

## 7 定稿裁定（评审裁决落位，必须体现）

| # | 裁定 | 定稿依据（原文语义） |
|---|---|---|
| 1 | **kind 二分不变** | creds.kind 仅 ∈{static-cred, session}（§4.10）；CB-1：session=creds.tsv 的 kind=session 行，拆两表破坏 13 表口径（§4.2）；NTLM hash／私钥／客户端证书等特殊材料**仍记 static-cred**，不增设第三 kind（§4.10 材质约定行）；接口⑬「material meta 位定义（ntlm-hash\|ssh-key\|x509 等材质标注，**kind 二分不变**）」（§11 批次 0） |
| 2 | **material=ntlm-hash\|ssh-key\|x509 meta 位** | 材质用 meta 位标注（如 material=ntlm-hash\|ssh-key\|x509）（§4.10 材质约定行）；接口⑬同（§11 批次 0） |
| 3 | **差分配对按 role×端点** | 批次 4 差分配对按 role×端点，不按材质（§4.10 材质约定行）；差分对=(endpoint, role)（§6.6 步骤 2）；身份矩阵差分按 kind+role 分组重放（§4.2 CB-1）；session-viz role×endpoint 覆盖投影（§6.5） |

## 8 相关联动（散见条款誊录）

- P0 八问⑧（测试账号与数据分级：提供哪些账号/角色；本目标数据允许流向哪个 LLM API）→ 落账 creds(kind=static-cred)+scope account-grant（§8.1）。
- creds 状态变更=事件溯源追加新行，「取最新」是账本命令（§4.1）；set-cred-status 承载状态查询/变更（§5.3；归类冲突见 contracts/02-commands.md 探知项 2）。
- 引擎/子代理只产 submissions（creds 数组为提议），总控验收后落账，单写者（§6.1/§4.1）。
- matrix authz 差分落标准格：reason 前缀 `authz-diff:`，不设独立矩阵表（§4.10/§0.3 口径 7）。
- evals 挂钩：身份矩阵差分检出率（靶场种认证后漏洞）≥基线（§9.2）；授权靶场含 ≥5 个认证后漏洞服务作身份矩阵 ground truth（§9.4）。

## 探知项（待仲裁）

1. vault 条目格式缺源：§11 批次 0 接口④=「`{{vault:cred-N}}` 占位符语法+**vault 条目格式**」；定稿仅载占位符语法（N=creds 行序号、真值永不进账本，§4.10）、vault/ 目录位置（§3.4）与 guard 从 vault/ 解密注入（§8.4）——vault 条目格式（加密方案/条目结构）定稿未载。
2. creds 的 material meta 位落列：§4.10 creds 字段清单 15 列（id…created）**无 meta 列**；§4.10 材质约定行「材质用 meta 位标注（如 material=ntlm-hash\|ssh-key\|x509）」——meta 位由哪一列承载（独立列/note 约定/他列）两处未对齐，待仲裁。
3. authz-diff 候选不打分的 score 取值：§4.5 intents.score=先验分 0-1（命令计算）；§6.6 步骤 1 authz-diff 候选「直接 pending 不打分」（§5.4 通路① recon-event 同语义）——不打分 intent 行的 score 列取值（空/0/他值）定稿未载，待仲裁。

## 自验

- **creds 字段清单一致**：`awk '/^## 4 creds/,/^### 4.1/' contracts/03-credentials.md | grep -c '^| [a-z_]'` = **15**；与定稿 §4.10 字段串 id,kind,role,username_ref,secret_ref,scope_asset,obtained_via_intent,parent_cred,valid_from,valid_until,status,permitted_actions,note,schema_version,created 逐字段全等且顺序一致（脚本比对=true）。
- **关键枚举/机制命中（grep）**：kind 二分 static-cred/session 均命中；status 四态 active/expired/invalidated/revoked 全命中；material 三值 ntlm-hash/ssh-key/x509 全命中；四关卡 `awk '/^## 2 vault 四关卡/,/^## 3 /' … | grep -c '^| [0-9] |'` = **4**；`grep -c '{{vault:cred-N}}'` = 7；`grep -c 'withheld'` = 1；`grep -c '重 tokenize'` = 1；`grep -c '一次性解密通道'` = 1；`grep -c 'authz-diff'` = 11；`grep -c 'pair_group'` = 5。
- **§6.6 五步流程** = 5 行（§5 步骤表）；**差分判定三规则** = 3（§5.1）；评审裁决三条（kind 二分不变/material meta 位/差分配对按 role×端点）落 §7 裁定表=3 行齐。
- 探知项=3。

# 接口⑥ · scope 契约（授权白名单三层语义）

> 来源：定稿 §4.2/§4.4 · §8.5 · §5.4 · schema_version=2 · 状态：待终审冻结

## 1 scope.tsv 字段（9 列）

表性质（§4.2 总表 #2）：纯追加（amendment 行）；写入命令=`ledger-add-scope` / `ledger-amend-scope`。

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| id | string | `S-{goal-id}-{四位序号}` 定宽零填充；由 ledger-next-id 原子分配（子代理/引擎无铸造权） | 行 ID（§4.1 前缀表 S(scope)） |
| kind | enum | `include`/​`exclude`/​`oob`/​`account-grant` | 行类别（见 §2；+修订行的 amendment 语义见 §3） |
| matcher | string | CIDR 网段/域名后缀/通配（include/exclude 用） | 匹配器 |
| account | string | 测试账号或 CRED 引用 | account-grant 行用 |
| permitted_actions | 多值 | `;` 分隔动作清单（如 `login;read-profile;write-order`） | 账户级允许动作 |
| amendment_of | string | =被修订行 id | 修订链指针（见 §3） |
| note | string | 修订理由+批准人 | amendment 行必填语义 |
| schema_version | int | 定值 `2` | |
| created | timestamp | — | |

## 2 kind 语义（4 值）

| kind | matcher 语义 | 配套字段 | 说明 |
|---|---|---|---|
| include | CIDR 网段/域名后缀/通配 | — | 授权边界内 |
| exclude | CIDR 网段/域名后缀/通配 | — | 排除项（八问③：生产库/第三方组件/时段 → scope exclude） |
| oob | OOB 回连白名单端点 | — | DNS/HTTP 回连接收方申报；**未申报的回连被 Tier 3 默认拒绝且记 fact** |
| account-grant | matcher=资产 | account=测试账号或 CRED 引用；permitted_actions=`;` 分隔动作清单 | 账户级授权行 |

P0 八问中涉 scope 的落账接线（§8.1）：

| 八问 | 落账 |
|---|---|
| ① 目标（域名/IP/网段/源码包） | goals.target + scope include |
| ② 范围（允许的攻击类型/深度） | scope include + permitted_actions |
| ③ 排除项（生产库/第三方组件/时段） | scope exclude |
| ⑧ 测试账号与数据分级 | creds(kind=static-cred) + scope account-grant |

## 3 amendment 机制（授权边界可修订）

| 规则 | 内容 |
|---|---|
| 追加不删改 | 修订不删行不改行——追加新行 |
| amendment_of | =被修订行 id；note=修订理由+批准人 |
| 生效判定 | 沿 amendment 链取最新（命令实现） |
| 审批绑定 | P0 后修订必须伴随 approvals 行 |

## 4 三层语义（开局不定死：P0-P2 只铸三类锚点，§1/§5.4）

| 层 | 语义 | 可变性 | 来源 |
|---|---|---|---|
| 授权边界 | 客户可修订，走 amendment_of 追加链（§3）；授权边界的变更是留痕闭环，不是重启交战 | 可修订（append-only 链上取最新） | §4.4/§5.4 |
| 资产图谱 | append-only：assets.tsv 纯追加（§4.2 #6）；图谱既是记录（append-only 可回放）也是推理引擎（§3.3 Graph）；P3 全程经 asset-added/cred-obtained/scope-amended 事件回边生长 | 只增不删 | §4.2/§3.3/§5.4 |
| 矩阵锚点 | P2 后主矩阵基线冻结（分母不动）；新资产走子矩阵行（reason 前缀 `submatrix:`）；冻结的是覆盖率锚点不是探索；闭合率口径=主矩阵+子矩阵合并计算 | 锚点冻结+子矩阵生长 | §4.10/§5.4 |

## 5 硬门（scope 执法，账本级）

- 资产落账命令强制对照 include/exclude；界外自动标 out_of_scope 且账本级禁止派生 intent。
- 判定是 CIDR/后缀机械匹配（非 LLM）。
- scope 执法要素全量落账：accounts+permitted_actions、oob_endpoints 申报、append-only amendments（§8.5）。

## 6 out_of_scope 复判转正流程（§5.4 边界生长闭环）

闭环链：范围外观察 → P5「范围外观察」附录列示（out_of_scope facts 供客户扩授权决策）→ 客户决策扩授权 → amend-scope 修订链 → egress recompile+canary 复测 → 界外资产复判转正 → 子矩阵生成。

对应五条生长通路之③（§5.4）：触发=客户扩授权；回边落点=P3 events: scope-amended；预算护栏=未审批=账本级 REJECT；修订史进报告。

## 7 amend-scope 接线（P3 events: scope-amended 动作序列）

| 步 | 动作 | 护栏/落点 |
|---|---|---|
| 1 | amend-scope 落账（amendment_of 链+approvals 强制） | 修订未经审批=账本级 REJECT |
| 2 | tanyin-egress compile 重编译 ACL/DNS pinning/OOB 白名单 | egress recompile 幂等（§5.4 验收挂钩：黄金夹具覆盖 amendment 链） |
| 3 | out_of_scope 资产复判（转正则子矩阵初始化） | 子矩阵行 reason 前缀 `submatrix:` |
| 4 | canary 复测 | 修订史进报告守门声明 |

验收挂钩（§5.4）：evals 注入场景（交战中途投喂新资产/新凭据/范围修订，断言重规划发生且账本出现对应回边与子矩阵行）。

## 探知项（待仲裁）

1. §4.4 定义 `kind∈{include,exclude,oob,account-grant}`（4 值），修订走 amendment_of 列+追加行（不删行不改行）；而 §11 批次 0 接口⑥写作「scope schema（include/exclude/oob/account-grant/amendment）」，将 amendment 与四个 kind 值并列。两处口径需仲裁：kind 枚举是否含 amendment 值（本契约按 §4.4 字段级定义誊写为 4 值，amendment 落 amendment_of 机制）。

## 自验（以下命令与计数均为实跑结果）

- 字段数：定稿 `sed -n '215p' 定稿 | awk -F', ' '{print NF}'` → **9**（id, kind, matcher, account, permitted_actions, amendment_of, note, schema_version, created）；本文件 §1 字段表 `sed -n '11,19p' contracts/05-scope.md | grep -cE '^\| [a-z_]+'` → **9**。9=9。
- kind 枚举与定稿一致：定稿 `grep -n 'kind∈{.include' 定稿` → `217: kind∈{include,exclude,oob,account-grant}`；本文件 `grep -cE '^\| (include|exclude|oob|account-grant) ' contracts/05-scope.md` → **4**，逐值同名（amendment 是否入枚举见探知项）。
- 三层语义：`grep -cE '^\| (授权边界|资产图谱|矩阵锚点) '` → **3**（可修订授权边界/append-only 资产图谱/锚点冻结+子矩阵）。
- amend-scope 接线：`grep -cE '^\| [1-4] \| (amend-scope|tanyin-egress|out_of_scope|canary)'` → **4** 步（落账→egress 重编译→复判→canary）。
- 探知项=1。

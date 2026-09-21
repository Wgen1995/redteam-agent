# 接口⑤ · phases.yaml 契约（九门状态机）

> 来源：定稿 §5.1-§5.2 · schema_version=2 · 状态：待终审冻结

## 1 顶层 schema

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| format_version | int | 定值 `2` | 定稿值 |
| constants | map | 8 常量，见 §2 | 全局常量；restart_context_threshold 与 storm_score_threshold 是两个不同参数（§2.5） |
| states | list | `[P0, P1, P2, P3, P4, P5, P5.5, P6.0, P6]`（9 门） | 阶段序列 |
| initial | string | `P0` | 初始门 |
| gates | map | 键∈states；见 §3 逐门 | 门定义（门/标题/duty/断言/出口） |
| back_edges | list | 3 条，见 §4 | 回边显式化 |

分工语义（§5.1）：

- phases.yaml 是**阶段序列、entry/exit 断言、门禁点、回边的单一事实源（声明层）**；九门业务语义全部数据化。
- **执法权威不搬家**：每条 exit 断言=一条（或一组）账本命令的调用与返回值判定——yaml 只声明「调哪条命令、期望什么返回」，判定由命令执行，yaml 自身不可被执行为旁路。
- phases/*.md 保留为人读方法论指令，由状态机按当前阶段调度加载（渐进加载）。
- 跳门可检测：每门出口断言的命令调用必产生 timeline 事件，P4 verify-chain+validate 可发现缺门记录；canary/纪律注入测试验证不可绕。
- 回边显式化：budget-exhausted→P4 降级流、新资产/新凭据→P3 内事件回边、校验失败→halt（人工处置后重评，不静默跳门）。

## 2 constants（8 项）

| 常量 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| restart_context_threshold | float | `0.75` | 受管重启阈值（≠storm_score_threshold） |
| restart_every_n_rounds | int | `10` | 受管重启轮间隔 |
| storm_score_threshold_base | float | `0.5` | 先验分阈值，随轮数单调递增：base+0.05*(round-1) |
| llm_association_quota | int | `5` | ⑤路联想每轮硬上限（弱模型档=0，即关闭） |
| reversal_scan_quota | int | `3` | 被拒假设翻案扫描每轮上限 |
| p4_sample_ratio | float | `0.2` | 「-」「!」格 P4 抽查比例 |
| single_active_session | bool | `true` | 单活跃会话约束 |
| budget_dollars_enabled | bool | `false` | $ 第四维默认关（ADR-P4⑥） |

## 3 九门逐门定义（门/标题/duty/断言/出口）

### 门 1 · P0（授权门）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `授权门` | 门标题 |
| entry.assert[0] | string | — | 交战区目录可用 |
| entry.assert[1] | string | — | 无既有 goal 或处于 resume 态（state-rebuild PASS） |
| duty | string | — | 八问问卷+业务问卷（§8.1）→ ledger-add-goal → scope/creds 落账（含 oob/account-grant/amendment 语义）→ 授权书扫描件入 evidence（双哈希）→ SKILL 版本+tools.lock 哈希落 timeline → egress compile → canary 部署 |
| exit.assert | list | 3 条，见下表 | 出口断言 |
| on_pass | state | `P1` | |
| on_fail | state | `halt` | 无结构化授权禁止任何主动操作（只许读文档） |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-validate --tables goals,scope,creds` | PASS |
| 2 | `ledger-scope-coverage` | include+exclude+oob 齐备 |
| 3 | `ledger-verify-chain` | PASS |

### 门 2 · P1（测绘）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `测绘` | 门标题 |
| entry | require | `P0.exit` | 前置门出口 |
| duty | string | — | 侦察子代理（六要素委派）→ assets/facts 落账（每资产 scope-check 内联；facts 即脱敏）；测绘不终于 P1——P3 全程可经 asset-added 事件续测（§5.4 生长通路①） |
| exit.assert | list | 3 条，见下表 | 出口断言 |
| on_pass | state | `P2` | |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-tree-check --complete parent` | PASS（资产树完整） |
| 2 | `ledger-scope-check --all-assets` | 全部资产已判定 |
| 3 | `ledger-validate` | PASS |

### 门 3 · P2（规划）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `规划` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | 读账本+知识库指纹匹配（先例三元组内）→ matrix-init（列从 VOCAB WSTG v4.2 钉死）→ 冻结（锚点冻结≠探索冻结——分母不动，新资产走子矩阵，§4.10/§5.4） |
| exit.assert | list | 2 条，见下表 | 出口断言 |
| on_pass | state | `P3` | |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-matrix-freeze` | frozen（不可重复冻结） |
| 2 | `ledger-matrix-gaps --baseline` | 基线行数>0 且覆盖全部 in_scope 攻击面 |

### 门 4 · P3（演进循环）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `演进循环` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | 每轮：⓪checkpoint+budget-check → ①扫描（unconsumed-facts/pending-intents/matrix-gaps）→ ②条件触发假设风暴（五路+dedup+阈值递增）→ ③批量并行派发（指挥官协议，六要素+预算份额）→ ④验收落账（单写者，写前拒收）→ ⑤链构建（attack/cross_ref）→ ⑥收敛判定 |
| events | map | 3 事件，见下表 | 事件回边（不离开 P3） |
| exit.assert | list | 1 条，见下表 | 出口断言 |
| on_pass | state | `P4` | |
| note | string | — | converged 与 budget-exhausted 皆为合法终态；后者置 degraded=true 进入 P4 |

events（事件回边，不离开 P3）：

| 事件 | action | guardrails |
|---|---|---|
| asset-added | spawn 测绘 intents（origin=recon-event，直接 pending，不打分）+子矩阵初始化 | 计入预算/单资产测绘上限/out_of_scope 只记 fact 不 spawn |
| cred-obtained | 登记 creds(kind=session) → 触发 authz-diff 候选（批次 4 起） | —（定稿未设） |
| scope-amended | amend-scope 落账（amendment_of 链+approvals 强制）→ tanyin-egress compile 重编译 ACL/DNS pinning/OOB 白名单 → out_of_scope 资产复判（转正则子矩阵初始化）→ canary 复测 | 修订未经审批=账本级 REJECT；修订史进报告守门声明 |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-converge-check` | converged \| budget-exhausted |

### 门 5 · P4（汇总）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `汇总` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | 四校验命令 → finding 合并（supersede+tombstone）→ 「-」「!」抽查 → POC 独立重放门（批次 4 起强制：fresh 隔离子代理只拿 EV 卡片盲重放，set-replay-state 三态落账）→ 异常检测（批量置态与 fact 密度不符告警） |
| exit.assert | list | 5 条，见下表 | 出口断言 |
| on_pass | state | `P5` | |
| on_fail | state | `halt` | 校验失败阻止报告；修复后重跑本门命令 |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-validate` | PASS |
| 2 | `ledger-verify-chain` | PASS |
| 3 | `ledger-hash-recheck` | PASS |
| 4 | `ledger-matrix-audit` | 抽查通过 且 无告警 |
| 5 | `ledger-replay-summary` | 无 REJECTED 未处置项（批次 4 前=SKIP，报告中披露） |

### 门 6 · P5（报告）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `报告` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | tanyin-report 聚合器从 13 表确定性重建正文（模板+账本数据，零 LLM 方差；LLM 仅写执行摘要与修复建议叙述段，须引用 finding ID）→ report-draft.md（附「范围外观察」附录：out_of_scope facts 列示供客户扩授权决策，接 §5.4 边界生长闭环） |
| exit.assert | list | 3 条，见下表 | 出口断言 |
| on_pass | state | `P5.5` | |
| on_fail | state | `halt` | 空格未消灭且非 budget-exhausted=不变式破坏，人工处置 |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-terminal-gate` | 矩阵无空格 \| degraded 披露清单完备（终态门禁） |
| 2 | `tanyin-report --lint` | schema lint+脱敏检查 PASS |
| 3 | `ledger-redact-scan --target report/` | 占位符零泄漏 |

### 门 7 · P5.5（签发门）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `签发门` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | 人审 → ledger-approve（command_hash 绑定聚合产物文件哈希）→ report-signed.md |
| exit.assert | list | 1 条，见下表 | 出口断言 |
| on_pass | state | `P6.0` | |
| note | string | — | 未签发报告禁止导出（cli 层：导出命令校验签发行） |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-approve --verify-signoff` | approvals 存在对应 approved 行 |

### 门 8 · P6.0（清理门）——评审裁决已并入

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `清理门` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | ledger-cleanup-checklist 从 timeline 提取**全部外部副作用写操作（revert_cmd 非空行）→ 逆序执行 revert_cmd；纯账本状态行无需回滚** +结果验证 → 全核销或人工豁免（approvals 落账）→ cleanup.md 清理声明附报告 |
| exit.assert | list | 1 条，见下表 | 出口断言 |
| on_pass | state | `P6` | |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-cleanup-checklist --verify` | 全部 reverted 或 豁免行齐备 |

### 门 9 · P6（沉淀）

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| title | string | `沉淀` | 门标题 |
| entry | — | 定稿未设 | |
| duty | string | — | 脱敏提取（域名→CLIENT-NN，IP/凭据→占位符）→ 反向验证（session 出现过的域名/IP/凭据/token 在草稿中零命中）→ 用户审批 → 写入 knowledge（precedents/entities/graph.ndjson）→ lint 保鲜信号 |
| exit.assert | list | 2 条，见下表 | 出口断言 |
| on_pass | state | `END` | |

| # | cmd | expect |
|---|---|---|
| 1 | `ledger-approve --knowledge` | approved |
| 2 | `tanyin-redact --reverse-verify` | 零命中 |

## 4 back_edges（3 条）

| from | to | when | 附加属性 |
|---|---|---|---|
| P3 | P4 | budget-exhausted | mode: degraded（账本质量不降，P5 首节强制披露未闭合格） |
| P3 | P3 | asset-added \| cred-obtained \| scope-amended | type: event |
| P4 | P4 | 重放=REPAIRED（修复 POC 卡片后重放） | max_retry: 2 |

## 5 补充语义（§5.2 尾段）

- P0「无授权只许读文档」由 Tier 0 硬门实现（无 goals 行时一切写命令 REJECT）。
- 受管重启自动档护栏=重启计入预算、重启速率上限（1 次/N 分钟防递归 spawn）、timeline 记 managed-restart 事件、单活跃会话约束。
- 工件即缓存幂等续跑=intent done 且 `submissions/<intent-id>/submission.json` 存在则重入跳过。

## 探知项（待仲裁）

1. §5.2 九门 exit 断言引用了 `ledger-scope-coverage`（P0）、`ledger-tree-check`（P1）、`ledger-replay-summary`（P4）、`ledger-terminal-gate`（P5）4 条命令，但 §5.3 命令集清单（18 写+12 查询+6 校验+1 特殊=37）未包含这 4 条；§10.3 静态验证①又要求「phases/*.md 与 engines/ 中引用的命令 ⊆ shared/LEDGER.md 附录 A 37 条签名」。两处口径冲突：九门断言命令是否计入 37 条签名清单，待仲裁。

## 自验（以下命令与计数均为实跑结果）

- 九门清单：定稿 `grep -n 'states: \[P0' docs/design/2026-09-21-tanyin-v2-design.md` → `341:states: [P0, P1, P2, P3, P4, P5, P5.5, P6.0, P6]`（9 门）；本文件 `grep -c '^### 门 ' contracts/04-phases.md` → **9**（P0/P1/P2/P3/P4/P5/P5.5/P6.0/P6 逐门一节一表）。定稿 9=本文件 9。
- constants：本文件 `grep -cE '^\| (restart_context_threshold|restart_every_n_rounds|storm_score_threshold_base|llm_association_quota|reversal_scan_quota|p4_sample_ratio|single_active_session|budget_dollars_enabled) '` → **8**；定稿 §5.2 constants 块同为 8 项。
- exit 断言：定稿 `sed -n '343,443p' 定稿 | grep -c '{cmd:'` → **21**；本文件 `grep -cE '^\| [0-9]+ \| `(ledger-|tanyin-)' contracts/04-phases.md` → **21**；逐门分布 P0=3/P1=3/P2=2/P3=1/P4=5/P5=3/P5.5=1/P6.0=1/P6=2，合计 21。
- back_edges：定稿 `grep -c '{from: P' 定稿` → **3**；本文件 `grep -cE '^\| P[0-9.]+ \| P'` → **3**。
- P3 事件回边：本文件 `grep -cE '^\| (asset-added|cred-obtained|scope-amended) \|'` → **3**（asset-added/cred-obtained/scope-amended）。
- P6.0 评审裁决在场：『revert_cmd 非空行』『逆序执行 revert_cmd』『纯账本状态行无需回滚』三短语逐字出 §5.2 P6.0 duty。
- 探知项=1。

## 终审裁决注记（2026-09-23·contracts-v2）

九门断言四命令已终审并入 41 命令面（校验类）——探知项 1 已裁决。

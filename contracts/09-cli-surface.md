# 接口⑪ · CLI 工具箱命令面 + 铁律 7 边界

> 来源：定稿 §2.4（辅 §3.2/§3.4/§5.3/§2.5/§1 D1.1） · schema_version=2 · 状态：待终审冻结

## 1 形态与载体

- CLI 工具箱位于安装区 `cli/`，python3 标准库实现（python3 ≥3.9，零第三方运行时依赖），tools.lock 锁定。
- 「零代码」口径=「零第三方运行时依赖、复制即装」（§1 D1.1）。
- CLI 是账本唯一写入口（写前拒收内置）（§3.2）。
- 总控 LLM 经宿主执行通道调用 CLI（命令签名附录 A 冻结，LLM 只调用不实现）；执行通道间接层保证通道实现可替换（沙箱化只换通道实现，phases 不改）（§3.2 咬合点 1）。

## 2 允许类（只允许四类能力进 CLI）

| 允许类 | 判据 | 工具 |
|---|---|---|
| 确定性账本运算 | 输入输出可字节级回归（黄金夹具可钉死） | tanyin-ledger（37 条账本命令）、tanyin-phases（phases 引擎：validate/gate/restart/resume-kit/cached/rebuild-state/denominator-ready/trigger-audit）、tanyin-knowledge（知识库机械运算：init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map） |
| 机械执法与脱敏 | 规则是数据文件非语义判断 | tanyin-guard（scope-guard 包装器）、tanyin-redact、tanyin-canary、tanyin-egress |
| 确定性重建与投影 | 从账本零 LLM 方差生成 | tanyin-report（聚合器）、tanyin-viz、tanyin-replay（重放驱动） |
| 安装与自检 | 环境探测、验签 | tanyin-install、tanyin-selfcheck |

## 3 命令面清单（工具箱 12 工具；10→11/11→12 见文末 2026-09-24 勘误补记）

| # | 工具 | 允许类 | 职责（§2.4 口径） |
|---|---|---|---|
| 1 | tanyin-ledger | 确定性账本运算 | 37 条账本命令（见 §5） |
| 2 | tanyin-guard | 机械执法与脱敏 | scope-guard 包装器 |
| 3 | tanyin-redact | 机械执法与脱敏 | 脱敏 |
| 4 | tanyin-canary | 机械执法与脱敏 | canary 探测 |
| 5 | tanyin-egress | 机械执法与脱敏 | egress 代理 |
| 6 | tanyin-report | 确定性重建与投影 | 聚合器 |
| 7 | tanyin-viz | 确定性重建与投影 | 投影 |
| 8 | tanyin-replay | 确定性重建与投影 | 重放驱动 |
| 9 | tanyin-install | 安装与自检 | 安装器 |
| 10 | tanyin-selfcheck | 安装与自检 | 自检 |
| 11 | tanyin-phases | 确定性账本运算 | phases.yaml 确定性状态机运算（validate/gate/restart/resume-kit/cached/rebuild-state/denominator-ready/trigger-audit；批次 3 交付+批4 增补 trigger-audit，断言→命令调用协议见 phases/PROTOCOL.md） |
| 12 | tanyin-knowledge | 确定性账本运算（同型） | 知识库机械运算：init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map（13 子命令；语义提炼禁入——铁律 7；批量间接口=契约 14） |

## 4 铁律 7 边界

| # | 边界 | 内容（定稿口径） |
|---|---|---|
| 1 | 四类准入 | CLI 工具箱只允许 §2 四类能力；判据=可字节级回归/规则是数据文件非语义判断/从账本零 LLM 方差生成/环境探测与验签 |
| 2 | 禁止清单 | 禁止进 CLI：攻击决策与假设生成、漏洞语义判定、任何对「是否漏洞/下一步测什么」的判断、知识提炼（ingest 语义层）、报告执行摘要与修复建议叙述——这些永远是 LLM+skill 的职责 |
| 3 | 不主动对外 | CLI 不主动发起对外请求——唯一例外：tanyin-replay 与 tanyin-egress 在授权窗口与 scope ACL 约束下执行/转发 |
| 4 | LLM 只调用不实现 | 「LLM 只调用不实现」纪律全文有效 |
| 5 | 无命令不执行 | 「凡涉及账本读写而未给出命令的步骤一律不得执行（视为技能缺陷，终止报告）」纪律全文有效 |
| 6 | 实现载体 | python3 标准库（≥3.9，五宿主直跑；账本命令实现载体=cli/tanyin-ledger） |
| 7 | 供应链锁定 | tools.lock 锁定（哈希+ECDSA 验签；运行时绝不自动安装缺失工具，详见契约⑫） |

配套总控侧边界——薄总控五不（§2.5）：不自己写代码、不自己发请求、不自己判重（dedup_key 命令算）、不自己算哈希（命令算）、不自己渲染图（projector 只读投影）。

## 5 tanyin-ledger 37 命令面（签名批次 0 冻结；完整签名=接口③ 02-commands.md）

| # | 分组 | 命令 |
|---|---|---|
| 1 | 写 18 | add-goal |
| 2 | 写 18 | add-scope |
| 3 | 写 18 | add-intent |
| 4 | 写 18 | set-intent-status |
| 5 | 写 18 | add-fact |
| 6 | 写 18 | add-finding |
| 7 | 写 18 | supersede-finding |
| 8 | 写 18 | add-asset |
| 9 | 写 18 | add-edge |
| 10 | 写 18 | add-evidence |
| 11 | 写 18 | approve |
| 12 | 写 18 | matrix-set |
| 13 | 写 18 | checkpoint |
| 14 | 写 18 | append-timeline |
| 15 | 写 18 | matrix-freeze |
| 16 | 写 18 | budget-log |
| 17 | 写 18 | add-cred |
| 18 | 写 18 | amend-scope |
| 19 | 查询 12 | unconsumed-facts |
| 20 | 查询 12 | pending-intents |
| 21 | 查询 12 | matrix-gaps |
| 22 | 查询 12 | converge-check |
| 23 | 查询 12 | next-id |
| 24 | 查询 12 | intent-status |
| 25 | 查询 12 | matrix-get |
| 26 | 查询 12 | scope-check |
| 27 | 查询 12 | budget-check |
| 28 | 查询 12 | cleanup-checklist |
| 29 | 查询 12 | set-cred-status（creds 事件溯源状态查询/变更） |
| 30 | 查询 12 | redact-scan（交付前终检） |
| 31 | 校验 6 | validate |
| 32 | 校验 6 | verify-chain |
| 33 | 校验 6 | hash-recheck |
| 34 | 校验 6 | matrix-audit |
| 35 | 校验 6 | state-rebuild（state.md 与账本重建一致性） |
| 36 | 校验 6 | set-replay-state（重放门三态 VERIFIED/REPAIRED/REJECTED 落账，REJECTED→confidence 降 C3 或转 fact） |
| 37 | 特殊 1 | matrix-init（P2 生成矩阵） |

通用纪律（§5.3）：写前拒收；查询输出摘要化（计数+top-N+ID 列表，禁全量回灌）；命令幂等；对外请求类前置 request-ticket。签名清单批次 0 冻结进 shared/LEDGER.md 附录 A。

## 探知项（待仲裁）

1. set-cred-status 分组两处不一致：§4.2 总表 #13 将其列为 creds.tsv 的写入命令（「ledger-add-cred / ledger-set-cred-status」），§5.3 将其归入查询命令 12（注「creds 事件溯源状态查询/变更」）。本表按 §5.3 原文誊写归查询 12；两处口径待仲裁。

## 自验（以下命令与计数均为实跑结果）

- 逐名 grep（对定稿 `grep -c <工具名> 定稿` 循环）：tanyin-ledger=4、tanyin-guard=3、tanyin-redact=3、tanyin-canary=1、tanyin-egress=5、tanyin-report=3、tanyin-viz=1、tanyin-replay=3、tanyin-install=2、tanyin-selfcheck=4——**10 名全部命中（≥1）**；本文件工具表 `grep -cE '^\| [0-9]+ \| tanyin-' contracts/09-cli-surface.md` → **10**。
- 命令数：定稿行 454-457（写命令 18/查询命令 12/校验命令 6/特殊 1，「合计 18+12+6+1=**37**」）；本文件 37 命令表 `grep -cE '^\| [0-9]+ \| (写 18|查询 12|校验 6|特殊 1) ' contracts/09-cli-surface.md` → **37**（18+12+6+1=37）。
- 允许类：`grep -cE '^\| (确定性账本运算|机械执法与脱敏|确定性重建与投影|安装与自检) '` → **4**（定稿 §2.4 四行）。
- 铁律 7 边界表=7 行（§4 表逐行：四类准入/禁止清单/不主动对外/LLM 只调用不实现/无命令不执行/实现载体/供应链锁定）。
- 探知项=1。

## 终审裁决注记（2026-09-23·contracts-v2）

set-cred-status 终审归写入（写19/查11/校验10=41）——探知项已裁决。

## v2 勘误补记（2026-09-24·批次 3 施工期·G-1 裁决）

- 工具箱 10→**11** 工具：增补 #11 tanyin-phases。允许类=四类允许之首「确定性账本运算」（铁律 7 §2 判据：输入输出可字节级回归——引擎测试全部金样化，phases-validate.norm 已入黄金回归）。理由：phases.yaml 断言执行（gate/restart/resume-kit/cached/rebuild-state）与分母就绪门（denominator-ready——独立子命令不入 yaml 断言集，口径=PROTOCOL §4）需要独立运行时载体，并入 tanyin-selfcheck 面不可行（运行态运算非安装期自检）。
- 勘误通道：微版本勘误（零存量数据期，同批次 1「v2 勘误」先例），schema_version 保持 =2 不递增；本补记日期 2026-09-24。
- 自验复跑：工具表 `grep -cE '^\| [0-9]+ \| tanyin-' contracts/09-cli-surface.md` → **11**（§「自验」原有 10 为 2026-09-23 冻结时点基线，保留可追溯）。

## v2 勘误补记（2026-09-24·批次 3 评审收尾·Important-1）

- tanyin-phases 子命令枚举三处补齐 6→**7**：§2 允许类行、§3 命令面清单 #11、上则 G-1 勘误补记行均漏第 7 子命令 **denominator-ready**（分母就绪门，T3 追加件，口径=phases/PROTOCOL.md §4；独立子命令不入 yaml 断言集——T3 裁决原案）——与 cli/README 批次 3 节七子命令速查、tanyin-phases USAGE 行、PROTOCOL §4、tests/test_contract_backfill.py 七子命令断言对齐。
- 勘误通道：微版本勘误（零存量数据期，同上则 G-1 先例），schema_version 保持 =2 不递增；本补记日期 2026-09-24。
- 自验复跑：`grep -c denominator-ready contracts/09-cli-surface.md` → **5**（§2/§3/G-1 补记行/本补记首行/本自验行各一）。

## v2 勘误补记（2026-09-24·批次 4 施工期·T14 收口）

- tanyin-phases 子命令枚举 7→**8**：补第 8 子命令 **trigger-audit**（触发器闭包审计——只读零落账三检查：目录版本一致/触发器闭包/清单输出，口径=phases/PROTOCOL.md §6；单源目录=phases/TRIGGERS.md 版本化封闭表 triggers-v2）。批4 T13 交付（349ac34），子命令枚举回注=本笔（R-T13 附记移交件：契约枚举与 cli/README 速查随 T14 收口对齐，G-18 先例同型）。
- 勘误通道：微版本勘误（零存量数据期，同上则先例），schema_version 保持 =2 不递增；本补记日期 2026-09-24。
- 自验复跑：`grep -c trigger-audit contracts/09-cli-surface.md` → **4**（§2/§3/本补记首行/本自验行各一）。

## v2 勘误补记（2026-09-24·批次 5 施工期·T1/R7 裁决）

- 工具箱 11→**12** 工具：增补 #12 **tanyin-knowledge**（知识库机械运算 13 子命令：init/source-register/lint/approve/commit/export/match/neighbors/nday-match/score/promote/demote/client-map；允许类=「确定性账本运算」同型——输入输出可字节级回归，export/match 金样化）。理由：知识库确定性运算需独立载体，并入 tanyin-ledger 面不可行——44 账本命令面冻结（账本命令零新增）。语义蒸馏（提炼什么知识页/正文怎么写）不进 CLI=铁律 7 边界 2（知识提炼 ingest 语义层禁入；四门槛质量判断留人审 checklist）；种子库只读纪律（R7：指向仓库 knowledge/ 时一切写子命令 REJECT）。批次间接口=契约 14（14-knowledge-schema.md）。
- 勘误通道：微版本勘误（零存量数据期，G-1 10→11 先例同通道：11→12），schema_version 保持 =2 不递增；本补记日期 2026-09-24。
- 自验复跑：工具表 `grep -cE '^\| [0-9]+ \| tanyin-' contracts/09-cli-surface.md` → **12**（§「自验」原有 10 为 2026-09-23 冻结时点基线，保留可追溯）。

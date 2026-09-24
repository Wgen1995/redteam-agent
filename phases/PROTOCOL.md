---
version: b3-frozen-1   # 批次 3 冻结接口合订本（契约 04 §5/§11 批次 3 行）
---

# 1 断言→命令调用协议（phases.yaml exit.assert → 命令调用与返回值判定）

执法权威不搬家（设计 §5.1）：yaml 只声明「调哪条命令、期望什么返回」，判定由命令执行。
tanyin-phases gate --goal-dir D --phase <门> 是该协议的唯一确定性执行体：

1. 调用形态：exit.assert[].cmd 经 shlex 切词；首词即命令名（含 ledger- 前缀，registry 双前缀注册均可查）；剩余词做空格式旗标归一——`--k v`（v 不以 -- 开头）合并为 `--k=v`，裸旗标（如 --all-assets / --baseline / --verify-signoff）原样传递。归一后经 ledger.registry.lookup 在进程内派发（与宿主 shell 直通 tanyin-ledger <cmd> 等价；沙箱化只换通道实现，本协议不变——设计 §3.2 咬合点 1）。
2. 判定表（exit code + stdout/stderr）：

| 断言命令（cmd 首词） | 满足（PASS）判定 |
|---|---|
| 默认（ledger-validate / ledger-verify-chain / ledger-scope-coverage / ledger-tree-check / ledger-replay-summary / ledger-terminal-gate / ledger-hash-recheck / ledger-matrix-audit / ledger-redact-scan / ledger-approve --verify-signoff / ledger-approve --knowledge / tanyin-redact --reverse-verify 等） | 进程退出码 == 0 |
| ledger-converge-check | 退出码==0 且 stdout 首词 ∈ {converged, budget-exhausted}；budget-exhausted 时门事件附 `mode=degraded`（设计 §5.2 back_edges） |
| ledger-matrix-gaps --baseline | 退出码==0 且 stdout 含 `covered=true` 且 `#baseline_rows=<N>` 的 N>0（该命令 covered=false 也退出 0，必须查 stdout——批次 1 实现事实） |
| ledger-matrix-freeze | 退出码==0（新鲜冻结）；或 退出码==1 且 stderr 含 already-frozen 且 timeline 已有 matrix-freeze 事件（halt 修复后重评的幂等容忍） |
| expect 文本含「批次 4 前=SKIP」 | 记 skipped，不计失败；门事件附 `skip=<n>`（P4 重放门批次 4 转强制，SKILL/P4.md 负责报告披露）【已退役 2026-09-24·批4：P4 expect 文本已去 SKIP 标记，本行保留备查——历史会话 yaml 不再含该词，规则不再触发】 |
| tanyin-report --lint（P5） | 退出码==2 = 工具未交付（批次 6）→ 门结果=ENV-HALT（引擎退出码 2，可重跑，非门禁失败） |

3. 事件词汇（timeline，链式哈希照常）：
   - 门全过：`gate-exit:<门> asserts=<n> result=PASS[ skip=<n>][ mode=degraded]`（actor=总控，phase=<门>）——与批次 1 夹具/verify-chain 跳门检测既有格式逐字兼容（cli/ledger/core.py:GATE_EXIT_EVENT）。
   - 任一断言不满足：`gate-fail:<门> assert=<cmd 首词> reason=<一句>`（非 gate-exit 前缀——跳门检测只认 gate-exit，失败不得被误计为过门）；引擎退出码 1，语义=halt（人工处置后重评）。
4. 幂等与前置：
   - gate-exit:<门> 已存在 → 输出 `OK\tgate:<门> already-passed`，退出 0，不重复落事件。
   - 前置门检查：目标门之前的每一门都必须已有 gate-exit 事件，缺 → REJECT（退出 1，零落账）。
   - 断言命令都是既有 41 面命令：引擎不新增账本写路径；写类断言（matrix-freeze）经自身 handler 落账，链一致性由各命令自己保证。
5. entry 断言（如 P0 的「state-rebuild PASS」）：声明层人读检查单，由 SKILL/恢复协议执行；引擎只执行 exit 断言（契约 04 分工语义）。

# 2 常驻集清单（SKILL.md 预算与内容边界）

常驻权威集 = SKILL.md 全文，token 预算 <2000（设计 §11 批次 3 出口）。确定性估算口径（测试冻结）：`tokens ≈ CJK 字符数 + ⌈非 CJK 字符数 / 4⌉`（跨 tokenizer 近似；预算留 ≥100 token 余量吸收偏差——探知项 G-11）。
必含八节（缺一=结构 lint FAIL）：①身份与铁律 ②九门循环骨架 ③P3 演进循环 ④命令索引（41 名+入口路径，签名不展开）⑤恢复协议（先对账再干活）⑥受管重启触发 ⑦干跑模式口径 ⑧路由表（当前门→phases/<门>.md 按需加载）。
禁入常驻：九门方法论展开（phases/*.md）、引擎知识、知识库内容、任何账本全量数据。

# 3 干跑口径（T11 的判定依据，随本接口一并冻结）

干跑（无目标自检）= P0-P2 照常经账本命令落账，零对外请求：不调 tanyin-guard exec、不调 tanyin-canary probe；tanyin-egress 只 compile（本地产物，无网络）；canary 只 deploy（本地登记）。
判定=timeline 无 `request:` 前缀事件且无 `request-ticket` 事件，verify-chain PASS。

---

# 4 分母就绪门（denominator-ready）——T3 追加件 v1（2bd6052 获批衍生；§1-3 冻结文本不动）

来源：完备性设计 §1.3（docs/design/2026-09-24-completeness-recon-knowledge-evolution.md）。
matrix freeze 前置检查，gate 断言体系成员，独立子命令（Ruling：不接入 phases.yaml
exit 断言列表——契约 04 断言集与 asserts=21 基线不动、九门语义不变；未来契约 v3 若
接入 P2 exit 断言，走本协议 §1 判定表默认行「退出码==0」）：

    tanyin-phases denominator-ready --goal-dir D

只读账本（facts/assets/edges/intents），零落账。退出码：0=就绪 / 1=FAIL 清单 /
2=用法。三断言（完备性设计 §1.3 四关裁三关——②诱饵召回率随批次 4 侦察金丝雀交付，
探知项登记）：

① 多源法定：每 in_scope 资产来源数≥2，或（unverified 标记+绑定该资产的在队列
   继续挖任务）。界外资产不入本断言（触发器目录：界外资产→记录不测）。
② A1-A8 类覆盖：每资产类非空，或「不适用理由」落账。
③ 外推闭包：图谱无未处理悬空外推节点。

读侧约定（13 表 schema 无显式来源/类别列，以下口径随本节冻结；字段到位后升版本）：
- 来源数：指向该资产值（facts.target == assets.value）的 fact 行之 distinct
  intent_id 数——每 intent 一次采集来源记录（来源正交的账本内代理度量）。
- unverified 标记：assets.meta 含 "unverified"。
- 在队列继续挖：intents 行 status=pending 且 kind=recon 且绑定该资产
  （dedup_key 以 "<AST-id>+" 开头，或 title/detail 含资产值）。
- 类映射：root-domain/subdomain→A1；ip→A2；service→A3；app/endpoint→A4；
  source-code→A6；cloud-storage→A5；human-factor→A7（G-12 勘误后十一值——
  原「A5/A7 当前 41 面 type 枚举无对应值」注记作废，见文末勘误补记）；A8=meta 含
  "extrapolated"/"外推" 的关联外推资产（界外也记）。
- 不适用理由：fact(kind=info, target="asset-class:A<k>", detail=理由文本)。
- 已处理（外推闭环三选一）：有采集 fact（target=资产值）/ 有绑定 intent
  （任意状态、任意 kind）/ 有整合边（kind ∈ {parent, attack, scope-rel}
  且 source_id 或 target_id 触及该资产 id）。

# 5 T3 实现注记（§1 协议的执行侧补全；§1-3 冻结文本不动）

计划参考实现 run_gate 与 §1 判定表的三处缝隙，按 §1 意图裁决落地（HANDOFF 记账）：
- 双前缀 lookup 归一：断言首词带 ledger- 前缀而 validate/verify-chain 等 builtin
  只注册无前缀基名——lookup 先试原词、再试剥前缀词（§1.1「双前缀注册均可查」）。
- EXTRA_TOOLS（tanyin-report/tanyin-redact）非 ledger 命令、registry 不可达——
  未交付即 ENV-HALT（引擎退出码 2，可重跑，非门禁失败，零落账），对应 §1 判定表
  末行语义；不走 gate-fail。
- 写类断言时间戳注入：matrix-freeze 是断言集唯一写类命令（§1.4），--timestamp
  必填而 yaml cmd 不携带——引擎注入门级 --timestamp（确定性纪律，禁 now()）；
  读类命令不注入（「无参数」类命令会 UsageError→误 ENV-HALT）。

# 6 触发器闭包审计（trigger-audit）——批4 追加件（T13）

来源：完备性设计 §3.1（触发器目录八类）；§1-5 冻结文本不动（Ruling：计划称「§5 新节」——§5 已被 T3 实现注记占用，按追加序落 §6）。

    tanyin-phases trigger-audit --goal-dir D

只读账本（timeline/assets/matrix/intents/facts/creds），零落账。退出码：0=PASS / 1=FAIL
清单 / 2=用法。三检查（单源目录=phases/TRIGGERS.md 版本化封闭表，版本行 version: triggers-v1）：

① 目录版本一致：TRIGGERS.md version: 行在场；timeline P0 事件 triggers-catalog <ver>
   若已记则须同版本（缺记=提示非失败——P0 落账该事件由 SKILL P0 序列承载）。
② 触发器闭包（事件驱动）：每个 in_scope add-asset <AST-id>(in_scope) 事件→该表面有
   submatrix-mint 事件/子矩阵行/绑定 intent（origin=recon-event）；每个 add-cred
   kind=session→存在 kind=authz-diff intent 或显式延后 fact（target=authz-diff:<CRED-id>）；
   每个 amend-scope 事件→其后存在 egress-compile 事件。
③ 清单输出：PASS 行 triggers=<n> closed=<n>/<n> catalog=<ver>。

事件词 egress-compile acl=<path> lines=<n>（actor=egress，tanyin-egress compile 末尾
落账，相对 goal-dir 路径防绝对路径漂移；幂等重编译=事件只记不判重）。界外
add-asset 事件免检（触发器目录行 2/8）；converge-check「未消费事实=0」与本审计互补。

## 勘误补记（2026-09-24·批次 4 施工期）

- §4 类映射补两行：cloud-storage→A5、human-factor→A7（G-12 裁决：assets.type 九值→十一值微版本勘误；原「A5/A7 无对应值」探知项注记随勘误作废——A5/A7 自此有对应 type 值，「不适用理由」兜底仅适用于其余无对应资产类的口径）。
- §4 三断言→**四断言**（2026-09-24·批4 T12，G-13 裁决落地）：第④断言「诱饵召回率」交付——
  planted>0 时 found==planted 否则 FAIL（比对=canary/recon-decoys.tsv × assets.tsv 同 value 且
  in_scope）；planted=0 时须披露 fact（target=canary:recon）在场否则 FAIL（§1.3②「100%（或披露）」
  语义）；stats 增 planted/found 两键（PASS 行同步）。§4 正文「②诱饵召回率随批次 4 侦察金丝雀
  交付，探知项登记」注记自此清账。载体=tanyin-canary recon-deploy/recon-recall（同工具分表：
  执法诱饵 targets.tsv 界外零容忍；侦察诱饵 recon-decoys.tsv 界内召回）。
- G-8 清账（tanyin-canary 参数语义注记，随上条一并）：deploy --seed / probe --tier=执法侧
  （界外诱饵拦截零容忍，批次 2 冻结面，本地模拟零网络）；recon-deploy --value --type（十一值
  枚举）[--note] [--timestamp] / recon-recall=侦察侧（批4 T12 新增，本地落表/读账零网络——
  §3 干跑口径「canary 只 deploy」扩为 canary 家族全子命令零网络）；recon-deploy 重复
  value=REJECT exit 1；recon-recall 无参数，stdout=JSON recall=found/planted+清单，
  timeline 事件 recon-decoy-deploy/recon-decoy-recall。

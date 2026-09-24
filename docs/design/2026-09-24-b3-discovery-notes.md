# 批次 3 探知项台账（G-1..G-15·T13 收口终态）

> 来源：①计划「探知项」节原文（下方第一节，程序化提取誊录防转写漂移）；②批次 3 T1-T13 实施期增补 G-12..G-15（HANDOFF 各任务裁决节记账原文归并）；③T13 收口状态归并（本文件=catalog 单源，HANDOFF 快照引用）。
> 通道纪律：契约回注一律走微版本勘误通道（零存量数据期先例，schema_version 不递增）；状态变更随任务记 HANDOFF 开发流水。

## 一、计划原文誊录（G-1..G-11，2026-09-24 计划冻结文本）

## 探知项（接口缺口——计划起草时已发现，执行中继续登记上报）

| # | 缺口 | 影响 | 本计划处置 | 建议裁决 |
|---|---|---|---|---|
| G-1 | **工具面 10→11**：契约 09 冻结「工具箱 10 工具」，phases 引擎需要运行时载体 tanyin-phases（第 11 个） | 契约 09 §3 与实现漂移 | 按新工具推进（铁律 7 类 1 合规：确定性状态机运算，输出金样化）；README 披露 | 契约 09 工具表增补 tanyin-phases（gate/restart 等子命令需要独立运行时载体，并入 selfcheck 面不可行） |
| G-2 | **新资产子矩阵行铸造路径断链**：matrix-set 拒收行外新键（write_cmds:824）、matrix-init 拒收已初始化（matrix_init.py REJECT）——「新资产走子矩阵行」（设计 §5.4 通路①/§4.10）无命令可走 | P3 asset-added 回边的子矩阵初始化无法落账；query_cmds.matrix_gap_cells 已把 submatrix:/authz-diff: 前缀行计入分母（分母在、分子进不去） | 本计划不改 41 面；P3.md 回边写「子矩阵行铸造待 G-2 裁决」 | 裁决 matrix-set 放行 reason 前缀 submatrix: 的新键行（新表面×词表全集），批次 4 前定 |
| G-3 | **重启速率上限常量缺源**：设计载「1 次/N 分钟」未定 N；契约 04 constants 冻结 8 项无此项 | 护栏②参数无契约依据 | 模块常量 RESTART_RATE_MINUTES=10 + --rate-minutes 覆盖（evals 可重放） | 契约 v3 增 restart_rate_minutes 常量 |
| G-4 | **重启计入预算的计量口径**：token_delta 值未载 | 护栏④数额无依据 | 默认 RESTART_TOKEN_COST=2000 + --token-cost 覆盖 | 批次 6 evals 实测基线定标后回写契约 |
| G-5 | **manual 接管的 stale 锁判定**：无跨平台进程存活探测；state-rebuild PASS 只证账本一致不证对方已死 | 双总控并存理论窗口 | manual 须 state-rebuild PASS+timeline 记 takeover-of（留痕可审计）；首发单 session 串行假设下可接受（与 §7.1 graph 多开同款残余） | 批次 6 安装器带 PID/锁文件探测后再收紧 |
| G-6 | **state.md v2 键集**：02a 终审补全 5 授权批次 3 冻结；本计划起草 10 键+handoff | 上游契约需回注 | T4 落位即冻结 | contracts/02a §13 补 state.md v2 键表（引用 phases/PROTOCOL.md） |
| G-7 | **gate-fail 事件词汇**：断言失败事件名契约未载（gate-exit 只该记 PASS） | 引擎输出与跳门检测边界 | 定 gate-fail:<门> assert=<cmd> reason=…（非 gate-exit 前缀，core.GATE_EXIT_EVENT 不误计过门） | 契约 04 事件词汇表补注 |
| G-8 | **干跑的 canary/egress 范围**：P0 duty 含 canary 部署与 egress compile，干跑边界未定义 | 出口①「零对外请求」需可判定 | PROTOCOL.md §3 冻结：egress 只 compile、canary 只 deploy、不 probe | 并入契约 09 tanyin-canary 参数语义注记 |
| G-9 | **风暴阈值过滤的执行位**：candidate→pending 晋升（0.5+0.05*(round-1)）无命令拒收载体（set-intent-status 拒收条件不含阈值） | 弱模型纪律遵循度只能 evals 检测 | SKILL/P3.md 写明公式与纪律；批次 6 evals 增弱模型遵循用例 | 裁决是否给 set-intent-status 增 --round 机械阈值校验（改冻结面需版本化） |
| G-10 | **checkpoint 参数扩展**：--session/--release/--round/--note/--spawn（02a §13 只载 --phase/--event） | 命令签名漂移 | 沿批次 1 探知注记 1 先例（--timestamp 同型追加）；T4 commit 注明 | contracts/02a §13 签名回注 |
| G-11 | **token 估算器口径**：CJK≈1/字+ASCII≈4 字符/token 是跨 tokenizer 近似 | <2K 判定口径 | 测试冻结公式；SKILL.md 预算目标 ≤1600 留 ≥400 余量 | 批次 6 以真实 tokenizer 基线校准系数 |

## 二、实施期增补（G-12..G-15，HANDOFF 记账归并）

| # | 缺口 | 发现 | 处置/建议裁决 | 终态（T13 收口） |
|---|---|---|---|---|
| G-12 | A5（存储与云）/A7（人的因素）在 41 面 assets.type 枚举无对应值——分母就绪门②对该两类只能走不适用理由 | T3（分母就绪门读侧约定冻结时） | 批 4 裁决资产 type 扩枚举或维持理由落账 | **待批次 4 裁决**（PROTOCOL §4 类映射在册） |
| G-13 | 诱饵召回率断言（完备性 §1.3②）无载体 | T3（完备性四关裁三关） | 随批次 4 侦察金丝雀交付 | **待批次 4 交付** |
| G-14 | P2.md duty 应把 denominator-ready 写为 matrix-freeze 前置步骤 | T3 登记→T10 落地 | P2.md「分母就绪门」节（口径=PROTOCOL §4，声明层人读前置检查单，引擎不执法） | **已闭环**（T10；契约 04 断言集/asserts=21 基线不动） |
| G-15 | P5.5「ledger-approve --verify-signoff」/P6「ledger-approve --knowledge」裸旗标与写命令 _parse 唯 --key=value 形态互斥（PROTOCOL §1.1 明列 --verify-signoff 为裸旗标例）——真跑将 Usage exit 2=ENV-HALT | T11（21 断言全量签名审计副产物） | 批次 6 前裁决：approve 局部预归一（T6 --release 同型先例）或 yaml 改 =1 形态 | **待批次 6 前裁决**（干跑止于 P2 不触发；其余 19 断言签名核对全兼容） |

## 三、状态归并台账（T13 收口终态，G-1..G-15 全量）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-1 | **已闭环·契约已回注** | 契约 09 文末「v2 勘误补记」工具面 10→11（微版本勘误通道）；T2 落地；自验复跑=11 |
| G-2 | **待批次 4 裁决** → **已闭环·批次 4**（T14 收口注记） | T2 Ruling 预批记入：维持原案（matrix-set 放行 reason 前缀 submatrix: 的新键行，新表面×词表全集）；本批 41 面零触碰；批4 T2 落地（1aace3d）：四条件放行+原子铸造新表面×VOCAB 全集+前缀首次归类修正，契约02a §12 微版本勘误 |
| G-3 | **常量暂代·已落地未回注契约** | T6：模块常量 RESTART_RATE_MINUTES=10 + --rate-minutes 覆盖（evals 可重放）；待契约 v3 增 restart_rate_minutes 常量 |
| G-4 | **常量暂代·已落地未回注契约** | T6：RESTART_TOKEN_COST=2000 + --token-cost 覆盖；待批次 6 evals 实测基线定标后回写契约 |
| G-5 | **缓解对已落地·收紧待批次 6** | T6：manual 须 state-rebuild PASS 凭据+takeover-of 留痕可审计；批次 6 安装器带 PID/锁文件探测后再收紧 |
| G-6 | **已闭环·本任务（T13）回注** | 契约 02a 文末「v2 勘误补记（G-6/G-10 裁决）」state.md v2 十键表——与 cli/ledger/state_md.py KEY_ORDER 单源对齐（tests/test_contract_backfill.py 钉死） |
| G-7 | **语义已冻结·契约补注待 v3** | PROTOCOL §1.3 gate-fail 事件词汇冻结+T3 落地；契约 04 事件词汇表补注留待 |
| G-8 | **口径已冻结·契约注记未并入** | PROTOCOL §3 干跑口径冻结+T11 eval 判定依据；契约 09 tanyin-canary 参数语义注记待并入 |
| G-9 | **纪律面已落地·机械校验待裁决** | SKILL/P3.md 公式与纪律在册；批次 6 evals 增弱模型遵循用例；set-intent-status --round 机械阈值校验待裁决（改冻结面需版本化） |
| G-10 | **已闭环·本任务（T13）回注** | 契约 02a 文末勘误补记 checkpoint 终局签名（--timestamp/--session 必填+--phase/--event/--release/--round/--note/--spawn 可选；输出 schema 不变） |
| G-11 | **口径已冻结·系数校准待批次 6** | PROTOCOL §2+测试冻结公式；SKILL.md 实测 1321 token（余量 679≥400）；批次 6 以真实 tokenizer 基线校准系数 |
| G-12 | **待批次 4 裁决** → **已闭环·批次 4**（T14 收口注记） | 见第二节；批4 T1 落地（a3fd64d）：九值→十一值（+cloud-storage/human-factor）+pivot/foothold 启用，契约01/07/02a+PROTOCOL §4 四笔微版本勘误 |
| G-13 | **待批次 4 交付** → **已闭环·批次 4**（T14 收口注记） | 见第二节；批4 T12 落地（3c42528）：tanyin-canary recon-deploy/recon-recall+denominator-ready 第④断言，PROTOCOL §4 三断言→四断言微版本勘误 |
| G-14 | **已闭环（T10）** | 见第二节 |
| G-15 | **待批次 6 前裁决** | 见第二节 |

## 四、移交清单（后续批次开工前必办）

- **批次 4 前必裁决**：G-2（新资产子矩阵行铸造路径）、G-12（assets.type 扩枚举或维持理由）、G-13（诱饵召回率载体随侦察金丝雀）。
- **批次 6 前必裁决/定标**：G-15（approve 裸旗标互斥——P5/P5.5/P6 断言真跑阻塞项）、G-4（RESTART_TOKEN_COST 定标回写）、G-11（token 估算系数校准）、G-5（stale 锁 PID/锁文件探测收紧）、G-9（--round 机械阈值校验是否版本化追加）。
- **T14 收口注记（2026-09-24）**：批次 4 前必裁决三项已全部闭环——G-2（T2·1aace3d）/G-12（T1·a3fd64d）/G-13（T12·3c42528），状态归并表已就地注记；批次 4 探知项续编 G-16..G-26 见 docs/design/2026-09-24-b4-discovery-notes.md。
- **契约 v3 回注待办**：G-3（restart_rate_minutes 常量）、G-7（契约 04 事件词汇补注）、G-8（契约 09 canary 参数语义注记）。

# 授权靶场全流程演练 RUNBOOK（批次 6 T17 交付）

> 定位：靶场全流程演练唯一剧本（计划 T17 Produces；裁决 I 配套）。覆盖四通道：
> ①P0→P6 全流程命令序（每步判定命令+预期 rc）；②P0-P2 干跑段（无活靶无 LLM 在环
> 即可跑，G-g1 拷贝亲测在册）；③budget-exhausted 终态 B 支线（四步，已亲测）；
> ④LLM 在环复测通道（R-T16-3 收口通道）+token 校准首采通道（裁决 G/R-T3-4 收口数据面）。
>
> 纪律：时间戳全显式字面量（禁墙钟入账）；交战区分离——演练会话一律落仓外
> （tempfile 或专用交战区目录），共享夹具 tests/fixtures/G-g1 零写热（R-T10-2 同律，
> 拷贝目录名须为 G-* 形：Session.goal_id 取 basename 剥 G- 前缀，决定 EV/INT 前缀）；
> 入口一律 [sys.executable, path]（POSIX 示例用 python3，Windows 用 py -3）；
> 退出码契约 0=过/1=门禁/2=环境。

## 1 前置环境门

| # | 判定命令 | 预期 |
|---|---|---|
| E0 | `python3 cli/tanyin-selfcheck --static` | rc=0（六项静态全过） |
| E1 | `docker compose -f tests/range/docker-compose.yml config >/dev/null` | rc=0（拓扑语法）；docker 缺=§4/§6 挂起入台账（ENV 披露），§3/§5/§7 不受影响 |

## 2 全流程命令序（新会话，P0→P6）

| 步 | 门 | 判定命令（--goal-dir D 会话目录） | 预期 rc |
|---|---|---|---|
| S1 | P0 | `tanyin-ledger add-goal --target=… --objective=… --auth-doc=… --auth-sha256=… --signer=… --valid-from=… --valid-until=… --budget=2M;50000;40 --model-tier=… --guard-tier=T3 --timestamp=T`（八问=phases/P0.md 表逐问落账） | 0 |
| S2 | P0 | `tanyin-ledger add-scope --kind=include --matcher=… --timestamp=T`（exclude/oob 同面） | 0 |
| S3 | P0 | `tanyin-egress compile --goal-dir D`（本地产物零网络；干跑口径=G-8 勘误） | 0 |
| S4 | P0 | `tanyin-canary deploy --goal-dir D --seed=<s> --timestamp=T`（本地登记零对外；参数=等号形 R-T11-2） | 0 |
| S5 | P0 | `tanyin-phases gate --goal-dir D --phase P0 --timestamp=T` | 0 |
| S6 | P1 | `tanyin-ledger add-asset …` ×N → `tanyin-phases gate --goal-dir D --phase P1 --timestamp=T` | 0 |
| S7 | P2 | `tanyin-ledger matrix-init --goal-dir D --timestamp=T` → `tanyin-phases denominator-ready --goal-dir D` → `tanyin-ledger matrix-freeze …` → `tanyin-phases gate --goal-dir D --phase P2 --timestamp=T` | 0 |
| S8 | 活靶 | `docker compose -f tests/range/docker-compose.yml up -d`（8 漏洞服务+attack-noop，172.28.0.0/24） | 0 |
| S9 | P3 | LLM 在环循环：在环 LLM 依账本态临场决策探针→`add-fact/add-evidence/add-finding/matrix-set`→`tanyin-phases gate --phase P3` | 0 |
| S10 | P4 | `tanyin-replay replay --goal-dir D --id=<EV-id> --timestamp=T` → `tanyin-ledger set-replay-state …`（重放三态落账）→ gate P4 | 0 |
| S11 | P4 | `tanyin-ledger converge-check --goal-dir D`（converged/budget-exhausted 二终态） | 0 |
| S12 | P5 | `tanyin-report aggregate --goal-dir D --timestamp=T --out report/draft-data.json` | 0 |
| S13 | P5 | `tanyin-report lint --goal-dir D --timestamp=T`（签发门同判定不落凭证） | 0 |
| S14 | P5.5 | 人审 → `tanyin-ledger approve --command-hash=<聚合产物哈希> --decision=approved …` → `tanyin-report sign --goal-dir D --timestamp=T`（凭证+双工件） | 0 |
| S15 | P6 | engine 提交/收尾：`tanyin-ledger cleanup-checklist --goal-dir D --verify`（全核销或豁免） | 0 |

## 3 干跑段 P0-P2 亲测记录（G-g1 拷贝，2026-09-26 T17 执行）

> 拷贝 `cp -R tests/fixtures/G-g1 /tmp/<work>/G-g1`；goal/scope/matrix 已在账，
> S1/S2 以账本态核验代铸（add-goal irreversible 不可重跑）。

| # | 判定命令 | 实测 rc | 实测输出摘录 |
|---|---|---|---|
| D1 | `tanyin-ledger verify-chain --goal-dir <copy>` | 0 | PASS verify-chain: 8 行链完整 gate_exit=4 跳门=0 |
| D2 | `tanyin-ledger converge-check --goal-dir <copy>` | 0 | running（structural: 1 格不可达）#reachable-gaps=0 #unreachable-gaps=1 |
| D3 | `tanyin-egress compile --goal-dir <copy> --timestamp=2026-09-26T11:00:00Z` | 0 | OK egress compile -> <copy>/egress.acl (21 lines) |
| D4 | `tanyin-canary deploy --goal-dir <copy> --seed=r1 --timestamp=2026-09-26T11:05:00Z` | 0 | OK canary deploy n=5 -> canary/targets.tsv（空格形 --seed <s> 不识别，等号形为准） |

## 4 活靶段 P3-P6（执行期演练）

须 range 活靶+LLM 在环=执行期演练；docker 缺=本段挂起入台账（ENV 披露），不阻塞
单测出口（计划 T17 Step 4 口径）。已有记录：T16 首跑=脚本化真实 HTTP 探针干跑
（20/20 marker 命中，基线 v1=1.00 入册，R-T16-3）；LLM 在环复测通道=§6。

> **M-3 评审收尾（internal:true）探针通道变更**：range 网 internal:true 后宿主
> 端口映射不再发布（compose 语义：published ports discarded）——活靶探针经
> attack-noop 双网跳板执行，例：
> `docker compose -f tests/range/docker-compose.yml exec -T attack-noop python -c "...urllib..."
> （svc-<名>:8000 内网 DNS 直连；post_auth 项带 X-Auth-Token 头；302 项禁跟随，
> marker 判 Location/响应体——20/20 判据不变）。T16 首跑记录（127.0.0.1 映射形）
> 为历史口径如实保留，不回改。

## 5 budget-exhausted 终态 B 支线（四步；2026-09-26 T17 亲测于 G-g1 拷贝）

| # | 动作 | 判定命令 | 预期 | 实测 |
|---|---|---|---|---|
| B1 | 中期抽干预算 | `tanyin-ledger budget-log --goal-dir D --token-delta=1990000 --requests-delta=0 --hours-delta=0 --scope=goal --note=… --timestamp=T` | rc=0 预算穿限（used>limit） | rc=0（used=2010000>2M） |
| B2 | 引擎停 | `tanyin-budgetctl enforce --goal-dir D --intent-id=<id> --timestamp=T` | rc=1 REJECT budget-exhausted 落账（零余量即拒派） | rc=1 REJECT budget-exhausted goal token used=2010000 limit=2000000 |
| B3 | 终态判定 | `tanyin-ledger converge-check --goal-dir D` | 输出 budget-exhausted（合法终态，P4 降级流） | budget-exhausted |
| B4 | 中期签发 | `tanyin-report sign --goal-dir D --timestamp=T` | rc=0 且 report/signed/{pass.json,interim-report.md,report-<ts>.md}+双工件在 | rc=0；interim-report.md 载中期报告声明+未测范围披露逐格（web.api/inj.sql）+未跑 intent+闭合率 66.7%+免责；findings.json verified=1/findings.sarif=1 |

单测面：tests/test_budget_exhausted.py（终态 B 可签发/披露数据缺失=FAIL/REJECT 落账
证据链/终态 A 不产中期报告四例）。终态 B 语义勘误=契约 13 文末补记。

## 6 LLM 在环复测通道（R-T16-3 收口通道）

- 口径：基线 v1=1.00 系脚本化探针干跑入册；在环复测=在环 LLM（总控宿主会话）依
  seed 服务面与账本态临场决策探针序列（非固定脚本回放），经 44 命令面铸造 EV/FD
  （EV 卡 word matcher 富化 marker）后跑 scorer。
- 判定命令：`python3 tests/eval_range_recall.py --session <仓外会话> --ground-truth tests/range/ground-truth.json`
  → rc=0 且 recall≥1.0（回退即 fail，对在环跑同样生效；docker 缺且无 --session=rc 2 环境降级）。
- 入账要求：在环执行体（谁/模型/宿主通道）与探针决策依据如实记 HANDOFF 流水，
  禁以脚本干跑冒充在环（R-T16-3 如实口径同源）。

## 7 token 校准首采通道（裁决 G 收口数据面；R-T3-4「随 Task 17 真跑首采入册」）

- usage 行形态（契约 15 §6）：`usage: run=<run-id> tokens=<实际n> est_tokens=<估算m>`，
  经 `tanyin-ledger append-timeline --goal-dir D --event="usage: …" --timestamp=T` 落账；
  tokens=宿主真实 token 计量，est_tokens=PROTOCOL §2 公式（CJK+⌈非CJK/4⌉）同文本复算。
- 首采程序：宿主真实 run 后逐 run 落 usage 行（n≥8，CJK/ASCII 混排覆盖）→
  `python3 cli/tanyin-evals run --suite=dynamic --goal-dir <会话> --timestamp=T`
  → M05 token-usage runner 实采（evals_token_eff.extract_ratios→write_calibration）
  → **tests/evals/calib/token-calibration.json 落盘**（n/median/min/max+契约 v3 系数候选提案+公式冻结注记）。
- 公式冻结注记：PROTOCOL §2 本批不改（金样/预算面零扰动）；系数回写=G-37 遗留至契约 v3。
- 无 usage 行=ENV-SKIP 不落盘（M05 既有语义，R-T3-4）；禁造样本。

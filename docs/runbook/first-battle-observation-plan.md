# 首仗观察清单（校准器取数口径·提前写死）· 2026-10-20

> 首仗定位=校准器：量的不是战果，是**新运行时在真仗里的第一组物理量**（首考立基线不比旧；n=1 会撒谎——单仗数字只立锚不下结论）。
> 每项=指标 → 从哪些行取 → 口径公式 → 一行取数命令（<GOAL> = 战役 goal 目录，如 ~/.tanyin/battles/battle-43/G-w1）。

## 一、七指标取数口径

| # | 指标 | 从哪取 | 口径 | 取数命令 |
|---|---|---|---|---|
| 1 | **首仗意图数** | timeline.tsv event 列 + intents.tsv | 终态意图数=intents.tsv 去重 id 数（事件溯源后者覆盖前者——**勿数 timeline add-intent 行**，那是铸造次数非在册数）；分状态报（done/failed/blocked） | `cut -f1 <GOAL>/intents.tsv | tail -n +2 | sort -u | wc -l` + 状态列 value_counts |
| 2 | **发现数** | findings.tsv | active 末值行数（status≠superseded）；**分口径报**：总数 / C1+C2 实证档 / suspected——同面多洞分洞分 finding（v4 单计律） | `awk -F'\t' 'NR>1 && $14!="superseded"' <GOAL>/findings.tsv | wc -l`（列位以 schemas.json 为准） |
| 3 | **复放成功率** | timeline replay 事件 + replay/ 产物 | =reproduced(VERIFIED) EV 数 / (reproduced+not-reproduced+env-diff)；env-diff 单列不计入分母变体口径并报；REPLAY_CAP=3 帽内 | `python3 cli/tanyin-ledger replay-summary --goal-dir <GOAL>`（单源：REPLAY_STATES 计数+C1/C2 重放义务 pending） |
| 4 | **误报 0 验证** | 三面合证 | ①C1/C2 发现全部 VERIFIED 且 replay-summary pending=0；②哨兵面零漏账：reject 计数（tanyin.sentinels 日志）+ downgrade 落 facts 行数（detail 前缀「[哨兵降级]」）；③GT 负对（neg 诱饵 5 行）零命中——报告诱饵行=误报 | ①`replay-summary` ②`grep -c '哨兵降级' <GOAL>/facts.tsv` ③判卷报告 neg 列 |
| 5 | **每意图成本** | budget.tsv（8列） | Σtokens(budget.tsv 各行 token 列) ÷ 意图数（§1 分母同源）；请求次数同式；USD 若道回传 usage 则加总，无则记「token-only 口径」 | `awk -F'\t' 'NR>1{s+=$2}END{print s}' <GOAL>/budget.tsv`；对账：timeline budget-log 行数 |
| 6 | **知识注入命中率** | kb-injections.tsv（goal 目录审计面） | 分两段：**注入率**=被注入意图数/活租约意图数（kb_inject.inject_briefing 逐意图审计行）；**消费率**=注入卡中被简报/发现/意图文本回引的卡数 ÷ 注入卡数（grep 卡 id）。零命中零注入=设计态如实记 | `wc -l <GOAL>/kb-injections.tsv` + `grep -oE 'CP-[0-9]{4}' <GOAL>/intents.tsv <GOAL>/findings.tsv | sort -u` 对交 |
| 7 | **复验触发** | retest 三命令面 + timeline | 过期清单行数（retest-pending）；触发卡数=retest-scan 铸的 kind=nday-verify 意图数；三态回写=retest-settle 后 timeline `retest:FD:still-true/fixed/env-changed` 事件计数 | `python3 cli/tanyin-ledger retest-pending --goal-dir <GOAL>` + `grep -c 'retest:FD:' <GOAL>/timeline.tsv` |

## 二、timeline 行型对照（cut -f4 event 前缀 → 用途）

`add-intent`(铸造数)｜`add-finding`(铸造数)｜`add-evidence`｜`replay-probe`(每请求一行)｜`replay:EV-*:<STATE>`(判定终态=§3 单源)｜`request:`(工具/LLM 调用面)｜`budget-log`(§5 对账)｜`supersede-finding`(僵尸口径——误报分母防 b40 僵尸行重数)｜`add-fact`(哨兵降级落点)｜`retest:FD:*`(§7)。列序：timestamp/actor/phase/event/revert_cmd/prev_hash/hash/schema_version（schemas.json 8 列）。

## 三、校准器产出物（收仗时一次性出）

1. **七指标一行表**（本档口径机械填数，禁手工调分）+ 全链可复算声明（beacon/EV/账本行）。
2. **capability 曲线落点**：首仗判分（gt-exam-readiness.md §三步6 命令）记入基线——若无锚（precheck-capability-gate.md 缺口1 未裁），记「首点即锚」。
3. **三条教训**→复盘卡（RT-0025 起）+ 新打法卡草稿→人审（蒸馏管线纪律）。
4. 僵尸口径标注：任何 superseded 行参与过的统计须带「活集口径」注（b40: 30/31 FP=僵尸行重数）。

## 四、观察纪律（从战斗史来的红线）

- 通道面≠靶面：会话令牌类观察只记 fact（任务卡红线4 已入战书）。
- 观测写放大教训（b26 gate-fail 终局 42% 噪声）：盯盘用只读投影（驾驶舱/实时页），禁轮询写面。
- 每意图成本>预算帽 80% 即预警（四问消费面 80% 线），预警即记 timeline 观察行。

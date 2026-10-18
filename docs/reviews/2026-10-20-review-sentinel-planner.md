# 评审档：哨兵(5e9c318) + 规划者(b3beebf) · 2026-10-20

- 评审人：独立代码评审员（只读代码+跑测试+本档，未改任何被评审文件）
- 对象①：5e9c318 功能11补件一·误报哨兵（设计锚 docs/design/2026-10-20-sentinel-retest-design.md §补一）
- 对象②：b3beebf 优先级引擎+常驻规划者+重派四分类（设计锚 docs/design/2026-10-20-priority-planner-design.md）
- 方法：逐条对设计稿；亲跑两套测试（见下）；对哨兵做规避/ReDoS 探针（纯函数+临时目录 CLI 端到端，零仓写、零端口）；对规划者做 stderr 捕获/持钥审批/扫面复杂度三探针（临时目录 goal）。被评审 11 个文件在两提交后无后续改动、工作树零改动（读到的即提交态）。
- 测试实证：`python3 -m unittest discover -s tests -p "test_sentinel*"` → **16/16 OK（0.372s）**；`python3 -m unittest discover -s tests -p "test_planner*"` → **35/35 OK（0.222s）**。两套均为真断言（CLI 子进程对夹具真写账、金样逐字节钉死、幂等/确定性双跑比对），非空壳。

---

## 一、哨兵 5e9c318（功能11补件一）

### 1. 规格符合（对设计 §补一，docs/design/2026-10-20-sentinel-retest-design.md:5-11）

| 设计要求 | 落地 | 判 |
|---|---|---|
| 14 类误报规则·版本化 TSV 单源·每条=信号pattern+判据+处置(降级fact/拒/标记可疑) | knowledge/engineering/sentinels-v1.tsv:6-20，SEN-001..014，`# version: 1`，三种处置齐 | 符 |
| 入库挂接：report_finding 入账跑全哨兵；降级=走 facts 不进 findings；拒=拒收；可疑=标记待验证官；全清=正常；哨兵在验证官之前（成本序） | write_cmds.py:781-810 四态全落：reject=REJECT 零字节变更(:790-791)；downgrade=铸 info fact(:792-808)；mark-suspicious=verified→suspected(:809-810)；clear=放行。挂接点=add-finding（findings 新行的唯一入口，grep 全仓核实无旁路写入命令） | 符 |
| 规则命中归并 | judge_client.py:194-195 从严优先(reject>downgrade>suspicious)+同动作文件序，确定性 | 符（设计未指定，裁定合理） |
| K6 回流：复盘「误报因为X」→蒸馏自动提取草稿→人过目→入文件版本+1 | distill.py:339-369（重放证伪→草稿行）、:372-386（TSV 头 draft 标记）、:599-606（落 sentinel-staging/，不自动合入）；测试钉死规则文件逐字节不动 | 符（偏差见 M-4） |
| TDD·金样钉死同输入同判 | tests/test_sentinels.py 16 测：一规则一真教训样本(:39-54)、金样两跑一致(:140-148)、四态入库端到端(:209-256)、K6 不自动生效(:288-292) | 符 |

裁定核（有 Ruling 的验合理性）：fail-open 方向（规则文件缺席/头不符=空规则集放行，judge_client.py:184-187, 226-229）——理由是哨兵=前置省钱优化、验证官 replay 仍在下游，方向正确；单行腐只废该行（:232-247）不废全库，合理。

### 2. 问题

**Important（收舱前修）**

- **I-1 嵌入换行可结构性绕过全部 14 条规则**。corpus=title+brief+steps 以 `\n` 拼接（write_cmds.py:788-789），而所有规则的间隙量词是 `[^\n]{0,N}`（sentinels-v1.tsv:7-20）——字段内嵌一个裸换行即把「信号词」与「漏洞词」切在两行，规则失配。实测（纯函数）：`返回404\n页面即可访问` → clear（基线 downgrade-to-fact）；`代理返回低置信\n判断` → clear（基线 reject，SEN-011）；端到端（临时 goal 真 CLI）：title 带裸 \n 的同款 404 误报 **rc=0 落 findings.tsv 且 exploitation_status=verified**。CLI argv 可携带换行（`$'a\nb'`/subprocess 列表），worker 报多行标题亦属自然形态——非恶意也可能偶然绕过。修法（小）：`run_sentinels` 内把 corpus 的 `\r?\n` 归一为空格再匹配（或间隙改 `[\s\S]{0,N}` 并按字段分别匹配）。全角数字改写（４０４）亦可绕过 SEN-001，属关键词正则的固有极限，记账不强求。
- （无 Critical。）

**Minor（记账）**

- **M-1 mark-suspicious 命中零留痕，注释与实现不符**：write_cmds.py:787 称「规则版本/命中明细经 tanyin.sentinels 日志留痕」，但 run_sentinels（judge_client.py:257-276）无任何逐 finding 日志，load_sentinels 只记版本(:252-253)；:809-810 静默降级 verified→suspected——验证官看不到「为什么可疑」。补一行 _sentinel_log.info(action/rule_ids/version) 即可，注释随之改真。
- **M-2 每 finding 重读重编译规则库**：run_sentinels 每调用 load_sentinels（judge_client.py:264）→每次 add-finding 重读 TSV+re.compile×14；批量入库 O(N×14) 重编译。当前规模无感（16 测 0.37s），入库放量前按 (path,mtime) 缓存。
- **M-3 未来规则无 ReDoS 护栏**：现版 14 条量词有界，370KB 对抗语料全 <0.1s（实测），无灾难回溯；但 load_sentinels 只验可编译（judge_client.py:239-243），K6 人工并入一条嵌套量词型坏规则即拖死所有 add-finding；且 corpus 中 steps 长度无上限（write_cmds.py:788-789 原样入 corpus）。建议：规则 lint（拒嵌套量词/反向引用）+corpus 截断（如 64KB）。
- **M-4 K6 草稿 pattern 取自标题而非「因为X」**：设计说「提取X成新哨兵规则草稿」，实现 signal_pattern=(?i)+re.escape(标题首段≤24)（distill.py:356-359），证伪原因只落 judge/note 供人工。机械可提取面下取舍合理（原因文本不可正则化），记账：泛化质量全押人工过目位。
- **M-5 降级路径两个边角**：① 调用方带 --supersede 时降级直接 return（write_cmds.py:792-808），supersede 意图静默丢失（旧 finding 留 active）；② facts 无判重，同一被降级 finding 重放两次=两条「[哨兵降级]」fact（幂等性部分成立：reject 幂等、findings 面有 dedup 先拦）。

### 3. 安全四问（哨兵侧）

- 前置门绕过：无第二个写 findings 的命令（check_cmds 只改状态列）；**主要绕过向量=I-1 换行**（已列 Important）+同义改写（固有极限）。
- ReDoS：现规则实测安全（见 M-3），护栏缺=记账。

### 4. 结论：**过**（收舱前修 I-1；M-1 顺手修；其余记账）

---

## 二、规划者 b3beebf（功能5/8）

### 1. 规格符合（对设计 docs/design/2026-10-20-priority-planner-design.md）

| 设计要求 | 落地 | 判 |
|---|---|---|
| 补件一：0.40可达(空格1/不可达0.3)+0.20凭据+0.15线索+0.15饥渴+0.10收益，权重可配，落 intents.priority 零 schema 改，禁 LLM | planner_score.py:37-49 权重/常量、:220-231 加权、:234-248 排序；planner.json 可配+fail-loud(:72-132, R-SCO-7)；add-intent --priority 回填（planner_loop.py:116）；全账本查询、零 LLM | 符 |
| 金样钉死同输入同序 | test_planner_score.py:137-171 顺序+分数+渲染逐字节钉死、双跑一致 | 符 |
| 补件二：常驻规划者·事件=账本行·800ms 防抖合并·降级=收卡惰性触发 | change_token=(epoch,mtime,size) 双写路径都动令牌（planner_loop.py:51-62，实测两类写均动）；防抖状态机(:183-197)与 ARTEX 同型；lazy_trigger(:129-138) 单发同效 | 部分——见 I-3（接线缺失） |
| 只派可达空格·走既有 add-intent 通道·每轮限量 | planner_loop.py:106-107（不可达只排序不派）、:113-117 registry.lookup("add-intent")（goal 写锁链）、max_adds 限流(:104) | 符 |
| 补件三：四分类纯机械(trace 行数+终态标记+产出计数) | replacer.py:86-112：done=完成/rejected=边界/blocked+transport-fault+零产出=纯故障/其余 blocked=接续；lease-expired 让位自动复活律(R-REP-5)；trace_lines 留审计面不进判据（R-REP-1 改判据=产出+置格，合理：纯故障卡也有生命周期行） | 符（裁定合理） |
| 三动作+幂等 | 重派=机械审批+blocked→active(:125-149)；续接卡带已得结论/剩余步骤(:163-200)；收口事实(:203-219)；dedup/收口判重幂等，测试钉二扫零重复 | 符 |

裁定核：R-SCO-1 复用 reachable_gap_cells 不重造 BFS（单源）；R-SCO-2 scope_asset=资产 id（write_cmds.py:1464-1466 证实）→value 映射正确；R-SCO-4 饥饿口径含历史行（事件溯源）合理。**设计叙事里的三消费者之一「派生器(deepex 规则表)」未交付**——不在建序估算内（设计 :33 只估 排序200+循环400+重派200），记账跟进。

### 2. 问题

**Critical（立即修）**：无。

**Important（收舱前修）**

- **I-1 REJECT 走 stderr，dedup 竞速合并分支是死代码，报错诊断全空**。_run 只捕获 stdout（planner_loop.py:79-84、replacer.py:117-122），而 write_cmds _wrap 把 REJECT 写 **stderr**（write_cmds.py:1733-1743）。实测：坏参数 add-intent → _run 返回 (rc=1, out='')。后果：① planner_loop.py:122-123 `elif "dedup_key" in out` 永不命中——提交信息声称的「并发战士竞速已派=合并」实际是 **RuntimeError(:125) 杀死常驻循环**（run() :199-202 无兜底）；replacer.py:198-199 同型死分支；② 所有 `RuntimeError("…被拒: "+out)`（planner_loop.py:125、replacer.py:135,149,218）携带空原因，排障只剩裸栈。修法：redirect_stderr 一并捕获、对合并文本判 "dedup_key"。
- **I-2 持钥部署下纯故障重派臂必崩**。_redispatch 铸机械审批不带 --sig（replacer.py:130-133），而 TANYIN_APPROVAL_KEY 在场时 approve 强制 HMAC 签名（write_cmds.py:1124-1130；生产姿态，HANDOFF.md:1212「AI 写者再不能自铸 approvals 行」）。实测：设 key 后 sweep → RuntimeError「重派预授权被拒」(空原因，同 I-1)，去 key 同一夹具正常出 fault-redispatch。即重派器恰在加固部署里坏。修法：重派器走键通道（持有/派生签名）或为机械审批开显式豁免通道并留审计。
- **I-3 事件驱动闭环未接线=全睡**。全仓 grep：PlannerLoop/lazy_trigger/assess/sweep 除测试外零调用方；cli/tanyin-ledger 与 special.py 无 planner 入口；transport-fault 标记也只有测试在写（executor 不产）。「新线索出现→几十秒内自动变成新活」（设计 :36）、「收卡时惰性触发」（设计 :21）在交付系统里都不发生——消费者(规划者/重派器)已建、生产者与启动器双缺。建序表（master-plan 行17）确以「循环+公式+分类器」为舰范围，但 R21 记「功能5/8建成」与系统事实不符。收舱前须至少接一处：收卡路径调 lazy_trigger + 常驻循环启动器/CLI 入口，或明裁接线归后续舰并改「建成」口径。
- **I-4 sweep 为 O(I×N)，万格轮询代价实测 8 秒+**。sweep 对每个终态意图调 classify（replacer.py:232-243），而 classify 内 trace_lines 扫全 timeline(:65-67)、output_count 扫全 facts+findings(:70-76)、matrix_marks 扫全 matrix(:79-83)——每意图三全表扫；_continue_card/_solidify/_redispatch 又各自新开 Session 全量重读盘(:136,165,205)。同构基准（模式逐行等价）：I=1k→0.08s、3k→0.74s、**10k(时间线30k+facts20k)→8.32s 纯扫描/每轮**，叠加逐动作磁盘重解析。rank_gaps 本身线性+排序无恙（gap_cells 单扫+sort，O(M log M)）——问题只在 replacer 扫面。修法：sweep 头部一趟聚合 intent_id→(trace/facts/findings/marks) 映射，Session 复用一只。万格启用前必须修。

**Minor（记账）**

- **M-1 轮后基线吞并发写**：_round 轮末 baseline=change_token(:178) 把轮中落账的他人写并入基线，该写不再触发下一轮——「恰好一轮内一写后再无写」的评估丢失一次。R-PLN-4 只裁了「自写并入」，实现并得更宽。修法：轮前先取 token，轮后 token≠轮前则保 pending。
- **M-2 伪造 reason 可触发机械重派**：判据只认 blocked 行 reason 前缀 transport-fault（replacer.py:108-110），reason=自由文本无来源戳——任何写者可零产出伪阻塞卡骗机械审批+重入池（每循环铸 approve+2 行 intents+timeline，可刷账/吃预算）。有界（须零产出、全审计、租约 1 分钟），建议：transport-fault 前缀保留给 executor（actor 校验或独立置态通道）。
- **M-3 规划者卡 budget_share=1;1;1 是绝对值**：budget_tree 把 ';'-三段按绝对份额解析（query_cmds.py:167-172）——规划者卡领「1 token/1 request/1 小时」，真跑用量即碾压份额，预算树上全线超支。单值小数形(:173-180)才是「根预算份额」。改传小数（如 0.02）。
- **M-4 historical_yield 把证伪/被合并 findings 也计收益**：planner_score.py:202-208 收集全 findings 行（含 replay-REJECTED、superseded）——「该类过去命中过」被假命中抬高。建议按 status=active/verified 口径过滤。
- **M-5 _reach_set 图构建重复两次**：planner_score.py:147-149 自建 _build 后 reachable_cells 内部又 _build 一遍（graph_cmds.py:158）——常数浪费，万格下可感。

### 3. 安全/并发四问（规划者侧）

- 规划者轮询 vs 写命令竞争：写面经 registry lookup 的 goal 写锁串行（registry.py:37-43），锁覆盖成立；但 **dedup 竞速容忍分支死代码（I-1）**，竞争实际表现为崩循环而非合并；_redispatch 对「他人已重派致状态转移非法」的拒收同样零容忍直接 raise（replacer.py:148-149）——双 sweep 并发（常驻+lazy 同发）可互崩。
- replacer 伪造 reason：见 M-2（有界，记账）。
- 排序复杂度：rank_gaps 线性+O(G log G) 排序，万格安全；**sweep 侧 O(I×N) 见 I-4**。

### 4. 结论：**打回**（修 I-1/I-2/I-3 后复审；I-4 万格启用前必修；M 类记账）

---

## 三、复验指令（任何人可重跑）

```
cd /Users/wgen/redteam-agent
python3 -m unittest discover -s tests -p "test_sentinel*"   # 16/16
python3 -m unittest discover -s tests -p "test_planner*"    # 35/35
```
探针（换行绕过/持钥审批/扫面复杂度）均为临时目录+纯函数，未触碰仓内文件与端口；本评审唯一仓内写=本档。

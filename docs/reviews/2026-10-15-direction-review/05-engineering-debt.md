# 05 · 工程债与可持续性独立评审（2026-10-15 方向评审）

> 评审员: 工程债镜头（独立,未与其他专家通气）。纪律: 只读零 git;证据全部来自当前盘面活体读码+实测。必读三档已读: tanyin-product-v1.md（含修正案 B Go 边车三触发器）/BLUEPRINT-RECON.md/2026-10-10 九专家 01-engineering.md。
> 本机实测: 全量测试套件 `python3 -m unittest discover -s tests` **385.5s 全绿 rc=0**（user 223s/sys 60s——sys 占比 16%,进程 fork 开销可见）。

---

## 一、总判决

**内核仍是单人工程的顶尖水准,但债的偿还顺序暴露了真正的病: 由"本批顺手"驱动,不由"哪颗先炸"驱动。**

- 上次九专家工程债清单六大项:**真还了的最痛项(gate-fail 写放大)值得记功——读侧 API+首落去重+驱动侧只读轮询+rc 漂移修复,四件全落地且有测试钉**。但其余: 读侧无锁撕裂快照原样存活且 webui 上线后暴露面扩大;importlib hack 半死(bootstrap 试点存在,SourceFileLoader 仍在);lint/覆盖率门原样为零;三大巨石模块**恶化**而非改善(write_cmds 1379→1665 行,+21%);timeline 仍逐事件整表重写;schema 仍是六行加载器。
- 更深的新病:**手工枚举复制已成系统性病灶**——命令面在 ≥5 处描述、3 处计数过期(41/44/49 三个数并存);门序 `GATE_ORDER` 注释里写着"禁双份枚举",而 `cmd_status` 的 seq 就是缺 P6.0 的第二份枚举,**这是一个已被自己入账、仍带病航行的活 bug**(webui 清理门灯恒 PENDING)。
- 单人维护数学: 自有代码 14,813 行 py + 测试 28,101 行/~1,400 用例/175 文件 + 自有文档 176 件 md≈34,920 行 + HANDOFF 1,452 行追加日志。**AI 战士的 onboarding 被工程化了(SKILL 路由+resume-kit),人类的 onboarding 是零**——而系统自己已经吃过一次亏: BLUEPRINT-RECON 白纸黑字记录主会话"只读 HANDOFF 尾不巡全图"差点重造知识飞轮。**作者自己的 AI 都会在 1,452 行日志里迷路,这就是 onboarding 成本的实测值。**
- Go 边车: 留 Python 的决定本身正确(85% 置信我同意),但**三个触发器今天全部不可点火**——①白盒解析器零行代码、②50 并发战士零负载数据、③分发需求零客户记录。"实测瓶颈=LLM 延迟>>>本地 CPU"对已建车道成立,被外推到了不存在的车道。

**判决: 路线可续。但 v1.0b(多战士/多战场/常驻循环)开战前有一张不可豁免的门票: 读侧撕裂封口 + 枚举单源化。这两件都是 S~M 工作量,继续拖延的唯一原因是没人把它排进批次——这正是病本身。**

**置信度: 85%。** 基于当前 HEAD 全量读码+实测;未验证: 多战士并发负载行为、CI 远端真实时长、Windows 实机。

---

## 二、发现(按严重度)

### F1【高】上次四债验尸: 三活一恶化,唯一还清的是最响的那颗

逐条验尸 2026-10-10 清单(01-engineering.md 关键缺口 1-4):

| 上次债 | 验尸结果 | 证据 |
|---|---|---|
| ① gateloop 写放大(gate-fail 灌账) | **已还,记功** | 去重 phases_engine.py:485-498(`_dup_gatefail`: 同 phase+assert+reason 已是最新行则免铸);只读门态 API phases_engine.py:501+(`cmd_status` 零铸造 rc=0 恒);驱动侧 tanyin-gateloop:52-60 只读轮询+113-126 全量门仅三时机(begin/proc-exit/soft-stall);GIVEUP rc=1(tanyin-gateloop:134)——上次点名的 rc 漂移同批修复 |
| ② 读路径无锁+多表 commit 非原子=撕裂快照 | **存活,且暴露面扩大** | core.py:113-121 `Session.__init__` 无锁串行载 13 表;write_cmds.py:266-268 `Ctx.commit` 逐表写;registry.py 查/校验/特殊命令一律不锁。上次建议的 epoch/版本戳文件 **零实现**。恶化点: webui 已上线——server.py:20 `ThreadingHTTPServer` 多线程常驻读者+snapshot.py:55-67 每 /api/state.json 全量 13 表+SSE 尾随轮询,战斗写入期间撕裂窗口从"偶发"变"常开" |
| ③ 双循环重复+importlib 连字符 hack | **半死** | ledger/runtime.py 存在但只是 22 行 bootstrap 试点(sys.path+UTF-8),docstring 自认"战斗热路径战后批走";tanyin-gateloop:29-38 **SourceFileLoader hack 原样在**(载 tanyin-runner 复用 launch/kill_group/log_event——模块级代码全执行、无字节码缓存、静态工具不可见,三条批评一条没少) |
| ④ 无 lint/覆盖率/类型静态门 | **原样为零** | .github/workflows/ci.yml 全文: selfcheck 静态+unittest+golden+evals,**无 ruff/无 coverage/无 mypy**。selfcheck 是自研一致性门(编码/布局/锁/金样/索引同步),不是 lint——它管"双胞胎文件同步",不管"代码本身错不错" |
| (附)巨型模块 | **恶化** | write_cmds.py 1379→**1665**;phases_engine.py 1236→**1329**;knowledge.py 1332 不动。test_write_cmds.py 同涨到 1017 行 |
| (附)timeline O(1) 追加 | **存活** | timeline.py `append_tl_locked` 与 phases_engine.py:360-372 `_append_event` 仍是"锁内全量读→内存 append→整表重写+fsync"。b26 终局 1,422 行=每事件重写全链。哈希链天然支持尾追加,设计礼物没人领 |

**危险**: 撕裂快照今天是显示层错乱(webui 短暂显示新旧混合账),**v1.0b 多战士多战场=同机多 goal 并发写+常驻 webui 读,撕裂从理论变日常**;P4 重放评分器若在写入窗口读 E-index+findings 交叉表,错判就是审计事故。importlib hack 的危险不在功能在演化: 任何人给 tanyin-runner 加模块级副作用,gateloop 就静默继承。

**修正方向**(全是上次说过的,重申并加价):
1. epoch 戳: commit 尾部原子写 `epoch` 文件(计数+表哈希摘要),`Session.__init__` 载完前后各读一次,不等则重载一次——约 30 行,S 工作量,**排进 v1.0b 开工批,不是"待后续批"**。
2. timeline 追加通道: `write_tsv` 分流 timeline 走"单行构造+O(1) 尾写+fsync"(链式哈希保证可校验),S-M 工作量。
3. 把 launch/kill_group/log_event/fsize 四函数搬进 ledger/(watchdog 或新 process.py),删 SourceFileLoader——半小时工作量,两次评审都点名,该死了。

### F2【高】手工枚举复制病: 同一疾病四起病例,止血靠钉测不靠单源

这是本次验尸发现的最危险的新债——**不是某个 bug,是生产 bug 的流水线**:

1. **命令面计数三处过期**: 真值 49 基名(SKILL.md 与 mounted registry 一致);cli/README.md:3,32 写"44 命令"(批次 1 口径);registry.py:55 docstring 写"枚举 41 命令基名…合计 41";cli/tanyin-ledger:3 docstring 同写 41。三份文档三个数,代码是第四个。
2. **命令面注册的隐藏侧门**: tanyin-ledger:15-22 在入口组装期 `registry._MODULES.append("zhulong_export")`——**跨模块 patch 私有属性**。直接 import registry 的任何消费者(静态分析、工具、我这次验证)看到的是 48,真 CLI 是 49。"单源"只在入口执行后才成立。
3. **门序第二枚举缺 P6.0 = 活 bug 带病航行**: core.py:11 `GATE_ORDER` 九门含 P6.0,其上方注释 core.py:9-10 白纸黑字"**禁双份枚举**";phases/phases.yaml:14 states 九门含 P6.0;而 phases_engine.py:514 `cmd_status` 的 seq=`["P0"…,"P6"]` **硬编码八门缺 P6.0**。后果链: state.json 无 P6.0 键→webui 清理门灯恒 PENDING。HANDOFF 2026-10-15 热修批自己入账:"**新债入册…真实 PASS/FAIL 待后续批修**"——前端钉了"九门灯与 phases.yaml 门数相等"的钉测,**后端的病没治,把灯的显示钉死了事**。
4. **selfcheck.KNOWN_COMMANDS 是第四份手抄命令表**(selfcheck.py:40-70): write_cmds 注释自认"三处绊线同步 45→48"——每加命令需人工同步 registry/SKILL 双胎/selfcheck 三处,绊线只保证"忘了会响",不消除"必须记着"。

**危险**: 每一起都是同一模式——**用钉测(事后报警)替代单源(事前不可能错)**。钉测防复发,不防初发;而单人+AI 高速迭代恰恰是初发高发模式(mint_wall_sync 签名漂移就是实例: HANDOFF 记载 `_append_event` 增必填 ts 后 3 参调用即 TypeError,**靠"WC 舰举报+主会话实证"在运行期发现**——这是类型检查器静态期一秒抓的 bug)。

**修正方向**: ① `cmd_status` 的 seq 从 `core.GATE_ORDER` 派生(删第二份字面量,一行);② registry 模块表补齐 zhulong_export、入口删 patch;③ cli/README/registry/ledger docstring 计数改为从 `all_commands()` 生成或索性删数字;④ selfcheck KNOWN_COMMANDS 改为从 registry 派生的断言而非手抄表。合计 ≤半天,全是删代码。

### F3【高】单人+纯手写路线的维护数学: AI 侧已工程化,人类侧为零,且作者自己的 AI 已经迷过路

**账面**(本机实测): 自有 py 14,813 行(非测试)+28,101 行测试/~1,400 用例/175 文件/59 金样;49 命令(67 键含别名)/16 个 CLI 入口/13 表/9 门(+P6.0)/5 页手写 HTML(~94KB)+status.js;自有文档 176 件 md≈34,920 行,HANDOFF.md **1,452 行追加式日志**;测试全量 385s 串行全绿;全仓 TODO/FIXME 仅 2 处(纪律极好)。

**三个判断**:

1. **认知负荷的真实测量已经发生**: BLUEPRINT-RECON 开篇自述——主会话"只读 HANDOFF 尾不巡全图",差点把已建成的知识飞轮/FD 卡/闸门实验当新设计重做,同日三起。**这不是假设风险,是已发生事故**。系统的应对是再加一档对账表+一部"蓝图巡检律"——**用文档治文档膨胀,372 件 md(含 imported)的仓库,药方是第 373 份文档**。
2. **AI 战士 onboarding 是被工程化的真资产**: SKILL.md 48 行路由器+按门加载 phases/*.md+resume-kit 白名单注入+"其余内容一律不进上下文"——这套上下文配给纪律是业界少见的。**但它优化的目标是"按需加载",前提是知道要加载什么——这正是迷路事故的死因**。巡检律+对账表是补丁,不是索引: 没有一份 ≤200 行的"系统全景+决策史(ADR)"入口档,SKILL 面向操作,不面向理解。
3. **人类第二贡献者(或 90 天后的您)的路径不存在**: 无 CONTRIBUTING、无架构小图(architecture-map-v3 是"维护中双胎",不是入口)、无"为什么是 TSV 不是 sqlite/为什么 threading 不是 asyncio/退出码契约"的决策记录——这些裁决散在 HANDOFF 各批 Ruling 与 16 份 contracts 里。**bus factor=1 的项目,续命协议不是 HANDOFF 日志,是"新人 30 分钟能不能安全发出第一条写命令"**。webui 的 `禁 asyncio` 律(server.py:4)与 llmpool 的 asyncio 并存(threading/asyncio/subprocess 三种并发模型同仓)——没有一个地方解释边界在哪。

**修正方向**: ①写一份 ≤200 行 SYSTEM-MAP.md(九门/13 表/命令面/并发模型/退出码/目录拓扑/五条硬律,全链接深档)并进巡检律首查位;②HANDOFF 分档: 尾部滚动状态+Ruling 索引抽出成独立 ADR 档(日志归档,索引永鲜);③黄金路径文档: "从 clone 到发出第一条 add-goal"实操 30 分钟教程——这也是 trigger ③(无 python 分发)真来那天您自己要走的路。

### F4【中高】Go 边车三触发器: 方向画对了,但三个都是今天点不着的空扳机

修正案 B 的决策框架(留 Python/仅热点件 Go 隔离/账本链留 Python)我签字。但逐个触发器验尸:

- **触发器①(白盒解析>10min 且分块/多进程救不了): 不可点火——解析器不存在**。全仓 grep openapi/swagger/白盒解析: 唯一命中是测试夹具里的喷洒字典词表(tests/fixtures/…/r27_0006_s1_spray.py:42)。车道 A 零行代码;**multiprocessing/concurrent.futures 全仓零使用**——"multiprocessing 可救"是零实现零基准的信念。>10min 阈值没有任何一个仓库的基线测量。
- **触发器②(并发战士>50/多租户): 无负载数据**。当前 13 战士基线,单目标单写者;50 并发战士首先撞的不是 Python 编排,是本机 RAM/CPU(opencode 子进程)+LLM API 限速——llmpool 熔断器已建,但没有任何多战士压力实验在 experiments/ 登记(在册仅 directive-n5 一件)。
- **触发器③(客户机无 python 分发): 无客户记录**。install/ 有 launchd/键管理/resign 工具,但"零 python 硬需求"没有任何客户/场景档。
- **"实测瓶颈=LLM API 延迟>>>本地 CPU"**: 对已建双车道(judge/llmpool/战士)成立——judge_client urllib 单轮秒级,命令面毫秒级,这个直觉我认。**但它被外推到了不存在的解析车道**: 正则扫描大仓库是 CPU 密集+GIL 锁死的形态,恰恰是 Python 最弱的场景,而它一行代码都还没有。

**缺的基准数据**(点名要): ①车道 A 落地时**必须随船带解析耗时遥测**(每仓库 parse 秒数/文件数/正则命中数,进 metrics 页)——否则触发器①永远靠手感;②一次性的 1 天 spike: 拿一个 50MB swagger/一个 jar 包,Python 正则 vs Go 原型各跑一遍,数字入 experiments/ 预登记;③**先试 sqlite3 再谈 Go**(见 F5)——如果整表重写和撕裂的解法是 stdlib 里的 sqlite3,Go 的最大理由又被砍一刀。

**危险**: 空扳机的真正风险不是过早/过晚换语言,是**决策文档看起来有数据支撑("实测")而实际没有**——三个月后没人记得哪句是测的哪句是猜的,85% 置信度会变成 100% 的教条。

### F5【中】纯 stdlib 约束的累计代价: 运行时收益真实,开发时禁令是意识形态

**收益侧(真实且适合本产品)**: 零三方依赖=零供应链面(supply_chain.py+tools.lock 成体系)——渗透工具跑在客户机上,这是产品级资产,不是洁癖。手写件(filelock 双平台/原子写/urllib 客户端/SSE)质量都过关。

**代价侧(被低估的三件)**:
1. **最大的反讽: sqlite3 就在 stdlib 里**。"零依赖"律从未禁止 sqlite3——TSV 全量重写/撕裂快照/O(n²) 写放大三债,一个 `import sqlite3` 全治。真实约束是"账本 AI 直读 TSV"的产品选择,不是 stdlib。中间路线(写路径 sqlite/导出投影 TSV,或仅 timeline O(1) 追加保 TSV)两次评审都提,两次都没排期。**别把产品选择伪装成语言约束。**
2. **开发时工具禁令是教条**: ruff/mypy/coverage 是 dev 依赖,不进运行时,不违反纯 stdlib 律。mint_wall_sync 事件(运行期 TypeError 靠战士举报发现)证明: **AI 高速生成代码的工作流里,静态检查恰恰是最缺的那双眼睛**——AI 重写代码的漂移是结构性的,mypy 是为这个工作流定制的护栏。CI 加 ruff+mypy(先 `--follow-imports=silent` 宽松起步)+coverage 报告(不求门槛先求可见)=S 工作量,拒做的理由不存在。
3. **3.9 地板无验证**: cli/README.md:70 宣称"python3 3.9+",CI 矩阵只有 3.11/3.12(ci.yml)。本机扫描未见 3.10+ 语法(match/pairwise/tomllib 零命中),但"没用到"和"验证过"是两回事——某台只有 3.9 的客户机就是第一次验证现场。CI 矩阵加一行 "3.9",S 工作量。

### F6【中】出口码纪律的暗洞: 未预期异常≡门禁失败

tanyin-ledger 入口(main): `except Exception as e: print("FAIL "+str(e)); return 1`。write_cmds.`_wrap` 只映射 Reject→1/Usage→2;**任何 TypeError/KeyError/OSError 一律被入口吞成 rc=1**。在 phases_engine 门内跑的命令抛未预期异常同样落入 gate-fail 语义。后果: **代码 bug 与真实门禁失败在账本里不可区分**——timeline 落一条 gate-fail,去重逻辑还会把它当"同因失败"收敛。对一个把退出码分域当招牌的系统,这是招牌上的裂缝。修正: 入口与门内分发对未预期异常落 rc=2 语义(ENV-HALT)+独立事件词(如 gate-error:),让 bug 永远不会伪装成评估结论。

### F7【低】仓库卫生与杂债

- **根目录垃圾文件**: `idor` 与 `token-` 两个 105 字节文件躺在仓库根,内容是 edges.tsv 输出(时间 2026-11-02=场景钟泄漏)——典型的重定向手滑产物,顺手清掉并给根目录加 lint。
- **docs/design/imported/ 里躺着完整的外来 .py 仓库**(vuln_agent 481 行 wrapper 等): 全仓代码搜索/grep/统计全被污染(全仓 py 46,849 行里近 4,000 行是 vendored);挪 `vendor/` 或子模块化,别让第一方代码和参照物混在 docs 里。
- **webui 每请求全量 13 表加载**: snapshot.py 每 /api/state.json 新建 Session(13 表)+cmd_status 再读一遍 timeline;SSE 每客户端每 POLL_S 重复。单操作员无碍,页面开多了就是自打 DoS——加个 mtime 缓存,S 工作量。
- **测试串行 385s**: 175 文件无分片;按目录 4 分片可压到 ~2 分钟,CI 与本地反馈双赢。不急,但 2,000 用例那天会急。

---

## 三、被忽视的资产

1. **sqlite3(stdlib)**: 上面说透了——最便宜的三债合治方案,两次评审视而不见。
2. **59 件金样+sim_watchdog.sh 无 LLM 全链仿真**: 只被用作正确性回归,**没被用作性能回归**——写放大/撕裂/耗时本可在这套仿真里挂阈值报警,gate-fail 噪声本可更早暴露。给仿真加一张"每战 timeline 行数/写次数/最长命令耗时"表,工程债就有了血压计。
3. **HANDOFF 的 1,452 行 Ruling 史**: 这是六个月最值钱的决策语料——AI 时代的 ADR 素材库,埋在日志里。抽出索引,它就从负债变资产(见 F3 修正②)。
4. **experiments/ 预登记律**: 度量纪真律(v0.9d)是科学纪律的好起点——**但只管度量实验,不管工程实验**: Go 边车触发器基准/多战士压力测试/解析耗时遥测都该进同一登记处,让"工程决策"也过"先登记后开战"的闸。
5. **llmpool/judge_client(v0.8 已建)**: 双车道直连 API 的地基已经打好,错误分类表/熔断/冷却都产品级——v1.0b 规划者循环可以直接踩上去,BLUEPRINT-RECON 已识别,别再差点重造。

---

## 四、三问

1. **v1.0b 多战士开战那天,谁背第一个撕裂快照?** webui 常驻读+多战场并发写已经是 v1.0b 的产品形态(tanyin-product-v1 D1-D3),epoch 戳 30 行代码拖了两个评审周期——如果它仍进不了下一个冻结计划,请说出比"本批不顺手"更硬的理由。
2. **"禁双份枚举"什么时候从注释变成机器?** core.py:9-10 的注释被 30 行外的 phases_engine.py:514 违反,注释拦不住任何人;命令面计数 41/44/49 三个数并存。四起同型病例之后,还打算靠钉测+巡检律,还是承认"枚举必须单源派生"并把半天工作量排进批?
3. **如果你明天起消失 90 天,接手者(或断电重启后的你)的第一份文档是哪份?** 如果答案是 HANDOFF.md——一个 1,452 行只增不删的追加日志,且系统自己的主会话已经证明"只读尾部会迷路"——那你其实没有答案。SYSTEM-MAP 200 行+Ruling 索引,什么时候写?

---

*评审方法备注: 全部证据为 2026-10-15 盘面只读核验(路径:行号均可复核);全量测试套件本机亲跑 385.5s 全绿;命令面计数经 registry 活体 import 与 SKILL.md 集合差分验证;未执行任何 git 操作、未改动除本文件外的任何文件。*

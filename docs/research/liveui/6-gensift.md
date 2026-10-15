# GenSift 白盒审计技能活体分析报告（探隐 v1.0a 白盒引擎吸收研究）

> 分析对象：GenSift @ `~/.claude/skills/gensift`（用户活用版本地目录，**严格只读**——未写入/未移动/未改名/零 git 操作）
> 参照副本：/tmp/gensift（经 `diff -rq` 逐字节比对与本地当前态完全一致，git 单提交 `e709b53 GenSift v2-complete`；README 自述"本地版更新更全"指历史上备份曾落后，本日快照已同步）
> 分析日期：2026-10 · 分析者：探隐委托子代理（GenSift 分析舰）
> 证据基础：SKILL.md/README.md/phases×12/agents×6/classes 26 页+59 pattern/invariants/langpacks/hooks/hosts/feedback 全量直读；探隐侧 tanyin-product-v1.md（修正案 A）、engine-fusion-architecture.md §6、HANDOFF 尾部路线、plans/2026-10-14 以后批次清单对照。
> 交付对应：HANDOFF:1445「GenSift 分析舰（6-gensift.md,含「消消乐/扫雷」思路解读）」。

---

## 一、架构解构：纯 LLM 驱动的「账本外骨骼」系统

### 1.0 一句话总形态

GenSift 是一个**寄生在 LLM 宿主会话里的白盒审计状态机**：LLM 全部语义判断下沉给一次性子代理，编排确定性全部上收到「TSV 账本 + 内联 shell 单行命令族」。自述定位（SKILL.md:3-5）：「源码自动漏洞挖掘。输入源码路径，全自动完成：枚举攻击面→逐卡五步证伪分析→盲验证→实时产出漏洞报告。纯 LLM 驱动（零自研代码），确定性来自 TSV 账本 + 内联 shell 命令。找全第一：所有 sink 必须被分析，不可跳过、不可抽样」。

设计哲学五条基石（design-v1.4.1.md:67-91）值得逐条抄给探隐看，因为它就是"程序执法记账、AI 战士自主打"在审计域的同构表达：

- **P0 机制优先于记忆**：「协议」不是写给 LLM 记的规则清单，而是三样东西——编排命令族（下一步由账本+命令派生，不由 LLM 判断）、任务形态（一卡一派=把可选动作空间切到最小）、验收不变量（产物合法性机械判定）。四条机制原则：最小世界/外部状态机/格式即牢笼/偷懒无收益（「偷懒改变不了账本还剩多少 unchecked，与自我声明无关」）。
- **能力弹性**：执行正确性（跑得完、账不乱）由结构保证与模型强度无关；执行质量（判得准、挖得深）随模型强度单调提升。「不存在'模型太弱跑不完协议'的失效模式」。
- **P1 分层判定**：发现层宽（污点可达即候选，保召回）、确认层严（具体 payload+攻击叙事才 confirmed，保精度）、中间态"存疑"是一等公民。
- **P2 双信任根**：机械可重放 + 执行 oracle（T0-T3 阶梯）；逻辑类无 oracle 显式留 human triage 位。
- **P3 零自研代码**：确定性只来自三个宿主原语——TSV 格式本身、协议逐字声明的标准 CLI 单行命令（find/grep/sort/comm/awk/wc/diff/shasum）、宿主子代理与文件系统。「协议即命令」。
- **P4 找全第一**：覆盖不可谈判、成本可谈判；一切效率机制（级联/排序/分带）只改顺序不改分母；级联失效退化为暴力逐卡也必须跑完。

### 1.1 目录总览（每件干什么）

| 件 | 规模 | 干什么 |
|---|---|---|
| `SKILL.md` | 120 行（硬预算上限） | 编排器唯一常驻入口：发起块（建会话目录/env.sh/断点续跑扫描）、角色三件事、元规则、循环纪律卡九条、阶段索引（渐进式加载）、红线八条、交付物清单 |
| `phases/` | 12 件，main-loop 1549 行 | 阶段机引用件：命令块的载体。**执行到哪阶段才读哪件，引用件内不再引用引用件（一层深度）**——常驻上下文只有 120 行入口 |
| `agents/` | 6 件 244 行 | 六角色提示词（recon/analyzer/verifier/confirmer/summarizer/reporter），派发时由子代理读入 |
| `classes/` | 26 页 + patterns/ 59 件 | 24 漏洞类判据页（12 节模板）+ term.md 兜底判据 + fixture-spec.md；patterns/ 存 509 条 POSIX ERE（机器直读，markdown 零模式数据行内嵌） |
| `invariants/` | retail.inv 14 条 | 业务不变式包（B 轨知识）：五字段 schema，带 `# domain: retail` 头做行业域过滤 |
| `langpacks/` | java/python/ts，933 行 | 入口枚举模式（sources.pattern/persisted.pattern/sources-lib.pattern）+ guards 五段转录规则 + frameworks.tsv + known-gadgets.tsv + includes.txt + sensitive-modules.txt |
| `fixtures/` | 1623 文件（pos 553/neg 756/noise 255 + 59 manifest） | 正/负/噪音三件套回归语料——pattern 的存活证明，未验证知识禁止进枚举 |
| `hooks/` | stop-hook.sh/ps1 + README | Stop hook：会话有未分析卡时 `exit 2` 阻止宿主收工并回喂「继续：剩余 N 张卡，下一条命令是 X」 |
| `hosts/` | 4 适配电 + reaper 双件 | 宿主×平台（claude/opencode × posix/windows）如何驱动/三重完成检测/idle 阈值校准/T2-T3 沙箱边界 + 孤儿收尸看门狗 |
| `feedback/` | dispositions.tsv（仅表头） | 七值人工处置账本（全局库）：fingerprint/disposition/reason/scope/source/date/review_expiry/run_origin |
| `docs/` | 4 件 | design-v1.4.1 定稿（570 行）+ design-suspects + design-conformance.tsv + 符合性补完计划 |

### 1.2 SKILL.md：编排器纪律的本体

编排器角色被压缩到三件事（SKILL.md:66-75）：**跑命令**（逐字复制执行）、**派子代理**（按模板分卡）、**验收格式**（查分片格式）。元规则：「凡 SKILL.md 与 phases/ 引用件都未给出命令的步骤一律不得执行——视为技能缺陷，终止并报告」。禁止：自己读目标代码判漏洞、自己写 finding、自己写脚本。这是把编排器降到「哑执行器」——所有智能要么在命令里（机械）要么在子代理里（语义），编排器本人零裁量。

九条循环纪律卡（SKILL.md:79-89）每轮 step0 前完整重读（防上下文压缩后丢纪律）：env.sh 纪律（每个 bash 块首行 `. "$S/env.sh"`——每块是新 shell）、循环顺序禁跳过合并、四 mark（5a/5b/5c/5d 投影缺一不许取卡）、覆盖不可谈判、子代理只返回一行、L1 闭合后必跑 L2/终态必跑不变量、**回合终结白名单**（唯一合法收口=终态完成；中途总结=禁止——防"回合收敛本能"）。

### 1.3 phases 阶段机：五阶段流水

```
phase0 测绘与枚举 → 主循环 step0-step6（至 L1 空）→ L2 发散 → joins 拼链 → terminal 终态
```

- **phase0**（0.0-0.8）：0.0 pattern-lint + I1 fixture 抽样门（坏 ERE/禁用构造/死 pattern/过宽 pattern，失败 exit 3——**未验证知识禁止进枚举**）→ 0.1 派 Recon → 0.2-0.4 三清单枚举（file/source/sink，module 回填、family 半机械键派生、guards/auth 回填）→ 0.5 G1 锚点预检（用户 advisory 的 CVE 锚点必须 ⊆ 冻结清单，不过不开跑）→ 0.5b guards 抽样比对 → 0.5c I19 枚举对账 → 0.6 冻结（sha256 封印）→ 0.7 发卡 → 0.8 预估（run-estimate.md）。
- **main-loop**（step0-6 每轮一轮，59 命令块的主战场）：
  - step0 前置检查：四 mark 验票 + L1 单调性（分母 unchecked 只许不增，违例 exit 1 技能缺陷级中止）+ L3 卡顿换道（近 3 轮不降→换 fw/term 道）+ 周期不变量快查；
  - step1 取卡：四项公式 `priority = 100·band_score + suspicion + centrality + cve_adj`（awk 纯机械算，LLM 零判断）+ v2.1 增补信号（敏感模块名词典 +10、文件级证伪密度 −30、同理由聚类 −20、test/demo 角色 score=-1 全局排尾不剔除）+ fw/term/ext 保底各 1 张防饥饿；
  - step2 派发：2a in-flight 记账 → 2b Analyzer（信封=卡信息+ID 白名单+上次失败原因注入）→ 2c band2 类聚簇派 Summarizer → 2d 语义合并轮（open≥25 触发）→ 2e 盲 Verifier（信封机械构造）→ 2f 双向对称反转抽样（band0/1 refuted 卡 10% 派复核）；
  - step3 收卡：3a 引文机械归一化（字面 <TAB>→真制表符/绝对路径→相对/格式方差修复）→ 3b 行数对账 → 3c 状态迁移（TERM 白名单过滤）→ 3d 候选落账（cand_id 双命名空间可反推）→ 3e 事实合并（幂等去重+sort -m+行数恒等式）+ Confirmer 派发 + retract 级联撤销 → 3f attempt 计费 → 3g 复核收卡（reversed 走翻案通道）；
  - step4 级联：K1/K1b/K2/K3/K4 五规则 awk join 消 band2 卡；
  - step5 投影（不可跳过，四个 touch mark）：5a Verifier 结果→finding 骨架+machine-fields 落行 → 5b live_findings_index.md 刷新（五节：审计脉搏/发现表/open 候选/近期活动/NOTICE）→ 5c progress_board 追加 → 5d Reporter 扩写+格式门；
  - step6 完成判定：unchecked=0 → L2；否则 Plateau 检测（mf 指纹 3 轮不变/4 轮非递增+卡顿在案→强制停轮）或批轮收口（每 N 轮输出一行 `GENSIFT-CONTINUE`，禁止总结）。
- **l2.md**：L1 闭合后必跑（unknown-unknowns 唯一合法通道）——frontier=blocked 残链+未交付候选+dangling joins+guard 离群；派发散 Analyzer 产 `DIV:` 行（只建议不结论，≤20 条）→ 机械转 ext 卡；**不变式轨**：per invariant × module 发 ext 卡（判据=.inv 条目五字段本身，三映射封闭枚举 violation→candidate/holds→refuted/不可判→blocked）；收敛判据机械化（zero_streak≥2）。
- **joins.md**：J1 拼链轮（多模块才派；Egress=契约=Ingress）→ J2 JOIN 落账 + assumptions 非空自动生成 follow-up ext 卡（假设点必复核）→ J3 组合分析（combinations.md 独立成件）。
- **terminal.md**：先跑不变量（I1-I20）→ G2 闭卷对账（三向计数/每卡下场可指认/CVE 编号污染剔除）→ G3 双跑稳定（分级契约：机械层逐字节硬保证/语义层 confirmed 重合度≥0.8+差异逐条归因）→ CALIBRATION 草案 → 终态报告投影 → 指标（门内禁声）→ mermaid 投影 → 脱敏扫描 → 处置反馈通道。
- **跨平台**：phases/*.ps1 是 58 块 bash 的 pwsh 逐节翻译件 + lib.ps1 公共底座（POSIX→.NET 正则改写规则表）；两侧产物与账本格式**逐字节一致**（黄金等价验证）。

### 1.4 agents 六角色：判定权的分拆

| 角色 | 职责一句话 | 关键纪律 |
|---|---|---|
| **Recon** | 纯测绘画地图（十项清单：技术栈/入口框架/模块地图/依赖 gadget 三值来源/库 or 应用/langpack 选择/横切关注点/消息消费者/SecurityConfig×路由矩阵/行业域断言） | 「任何风险判断都是越权」——只登记"哪条路由被哪段配置覆盖"，不判够不够 |
| **Analyzer** | 单卡五步证伪（下节精读），顺产事实当级联燃料 | 世界里只有一张卡；不下最终结论（那是盲 Verifier 的事） |
| **Verifier** | 盲确认（不见 Analyzer 任何结论与叙述） | ⓪⁻ rubric 先行 → ⓪ 先自推后对照（顺序禁倒置）→ ⓪' 自采引文 → ① FP 卡 → ② 攻击者模拟 → ③ 逐基线 → ④ 定级机械查表 → ④' 强制反向证伪（critical/high 无 REV 行禁 confirmed）→ ⑤ 反证清单 → ⑥ 有界邻接扫描 |
| **Confirmer** | 逐条事实独立复核（hint→confirmed 才准入 K 规则） | **一次只复核一条**——「批量复核=强度配称失守（剪枝定理 2）」；四项复核单：引文核对/作用域逐成员/reflection 重跑/反例搜索 |
| **Summarizer** | band2 类级事实批量提报（级联燃料补充，不承担卡终态） | 只提事实不下结论；作用域就低不就高（file < entry_id < entry_family）——「作用域写宽一格=过量剪枝，是打地鼠的新语义通道」 |
| **Reporter** | finding 扩写九节/跨模块拼链/语义合并/combinations | 不引入账本外新事实；拼链者不得拍板（假设点→follow-up 卡）；证据链节一个字不许改 |

加主代理（编排器）即设计文档说的"七角色"。分拆原则：**发现（Analyzer）≠ 裁决（Verifier）≠ 事实复核（Confirmer）≠ 叙事（Reporter）≠ 测绘（Recon）**——每个判定权独立上下文，互不见对方叙述。

### 1.5 classes：判据即知识原子

26 页 = 24 漏洞类（18 注入/防护类 + 6 业务逻辑类）+ term.md（文件级兜底判据）+ fixture-spec.md。每页 12 节模板：①定义危害 ②Source（**明文：存储回读与消息体是 source**）③Sink 模式表指针（→ patterns/*.pattern 数据文件）④Propagator ⑤Sanitizer 决策表三值（强/弱/上下文条件——**上下文条件档禁产 kills 事实只产 hint**）⑥判定流程（**编号条目 C1-C8：每条=证据问句+期望引用类型+推翻反例类型**——Verifier 的 RUBRIC 行引用条目编号，判据成为可统计可单独修订的知识原子）⑦FP 卡库（只增不删+deprecate 留痕，多卡命中取最严）⑧bypass 提示单（"去尝试，不是去阅读"）⑨定级阶梯+降级反例 ⑩根因修复 ⑪跨边界提示 ⑫fixture 指针+实际档位。

页首带 `band: 0|1|2`（危险分带，冻结列）、来源/校准行、演化纪律（append-only+人工批准 CALIBRATION 通道）。pattern 全部外置是结构性保证——「60 行叙事装不下'不并串'纪律下的三语言全表，塞进去必然诱发并串（GenSource 实测 bug 源）」（design-v1.4.1.md:282）。类×语言矩阵现状 59/72（D-037：6 业务类仅 java，payment-logic/perm-model 为 judgment-only 空模式——判据主体在 invariants）。

### 1.6 invariants：业务逻辑漏洞的判据轨道

retail.inv 14 条，每条五字段：**适用前提（一句话不变式）｜违反判据的证据形态（可 grep 的具体代码形态）｜来源（CVE+人工归纳，如 INV-001 ← CVE-2025-69871 MedusaJS registerUsage TOCTOU）｜阴性边界（什么不算违反——管理端改价/签名报价/显式透支额度不算）｜复核状态（provisional）**。文件头 `# domain: retail` 与 Recon 产出的行业域断言交叉过滤——防零售包污染金融 run。这是"不需要预知模式的发现"（防护缺失、业务逻辑破坏）的判据来源：per invariant × module 发 ext 卡，终态三映射封闭枚举。

### 1.7 langpacks：语言可插拔件

每语言目录：sources.pattern（入口注解/方法枚举，J-SRC01-16 形式）+ persisted.pattern（DAO/ORM 回读点=二阶污点 source）+ sources-lib.pattern（库模式语义切换：入口=公共 API 面/调用方传入点）+ guards 五段转录规则（authn/authz/csrf/upload-check/rate-limit 各一文件）+ frameworks.tsv（pattern→框架单一事实源）+ known-gadgets.tsv + includes.txt（枚举后缀，协议零语言假设）+ sensitive-modules.txt（排序信号非检测规则）。加语言=加目录，协议零改动。

### 1.8 fixtures：pattern 的存活证明

三类语义（fixture-spec.md §1-2）：**pos**（危险形态实样本，pattern 必须命中且命中集=manifest expected）/ **neg**（与攻击面无关的形态，必须零命中——"同一 API 的安全用法不是 neg"）/ **noise**（同一 sink 锚上的安全/硬化用法，**允许命中**，是否有问题由五步判别收口）。这个三分法解决了"门只验阳性会激励越写越宽"的激励问题。规模档位：达标集 pos≥10/neg≥20/noise≥5（java 全量），起步集（ts/python）6/8/3。phase0 0.0 门每次 run 前抽 20% 复检——**未验证知识禁止进枚举**（B-079）。

### 1.9 hooks + hosts：跑完跑全的 harness 工程

防停三层（README.md:110-147）：①批轮+GENSIFT-CONTINUE（技能内建：每回合连跑 N 轮才收口，收口只输出一行续跑指令——**中途总结被纪律卡禁止**）②Claude Code 原生 Stop hook（hooks/stop-hook.sh:44-51：剩余卡>0 → 双通道输出+exit 2 逼续跑；exit 2 而非 1 是 Claude Code 语义——只有 2 阻止停止并把 stderr 回喂模型）③opencode 插件等价物（session.idle 回灌，**必带守卫**：只在盘上存在 STATE=running 会话才回灌，防终态后无限烧 token）。长会话最大敌人被点名：「宿主与模型的'回合收敛本能'（v2.1 aiohttp 实跑教训：会话尾部编排器自行总结收工）」。

hosts/ 四适配电各含：如何驱动（每步命令）、三重完成检测（CLI 事件流标志+idle 看门狗+墙钟硬超时）、idle 阈值校准记录（3×P95(最慢合法单元)=2700s，最慢单元=单卡五步分析 90-900s 实测）、如何安全终止、T2/T3 沙箱边界。reaper.sh 收尸脚本带 mkdir 原子锁注册表。

### 1.10 TSV 账本结构（七件套+分片）

**账本七件套**（全部 TSV、单写者、确定性 ID、LC_ALL=C sort 定序、表头即 schema）：

| 账本 | 列 | 单写者 |
|---|---|---|
| file_inventory | seq, path, lang, loc, module(mod:/dir: 前缀), role(app/test/config/vendor/demo/generated) | 枚举命令（冻结） |
| source_inventory | seq, file_seq, loc, entry_type(http/persisted_read/external_message), framework, auth(unauth/auth/unknown), guards(五段逐字转录), family(路由前缀+方法+param_shape) | 枚举命令 |
| sink_inventory | seq, file_seq, loc, class_id, api(命中 pattern_id 串), band | 枚举命令 |
| checks（卡账本） | card_id, kind(bw/fw/term/ext), ref_seq, origin_ref(ext 必填), state(unchecked→candidate/refuted/not_applicable/no_path/blocked/partial + ext 专属 deferred), reason, facts_used, attempt, revision | 主代理协议命令 |
| facts（事实账本） | fact_id, type(8 值封闭:uncontrolled/intended/kills/propagates/no_edge/dead/flow/requires_config), loc, evidence(原文引文), evidence_hash, status(hint/confirmed/rejected/retracted), scope_type(entry_family/entry_id/file), scope_ref, reflection_checked, used_facts, confirmer, revision, origin_card | 主代理协议命令 |
| candidates（候选账本） | cand_id(CD-{sink:05d}-{source:05d}/CD-F-{file_seq}/CD-X-{origin}/CD-INV-{inv}-{module} 四命名空间), card_id, sink_seq, source_seq, class_id, loc, verdict_state(open/merged-into-X/...), delivery_state(pending/delivered/degraded), summary | 主代理协议命令 |
| joins（拼链账本） | join_id, egress_ref, contract_ref, ingress_ref, confidence, assumptions | 主代理协议命令 |
| machine-fields（发现账本） | finding_id, fingerprint(path+行内容哈希+class，**不含行号**——位置平移不换 ID), verdict(confirmed/unconfirmed/refuted/dismissed), severity, class, sink, source, tier, also-reported-by, pattern_version, known_disclosed, human_triage, lifecycle(空=在役/withdrawn/superseded_by), suite | 主代理 5a |

**分片**（各角色唯一可写文件，行前缀封闭枚举）：A-*（OBS:/ROLE:/FACT:/TERM:）、V-*（SELF:/RUBRIC:/VERDICT:）、RV-*（REVIEW:reversed|upheld）、CONF-*（OBS:/VERDICT:）、SUM-*（FACT:）、MERGE-*（MERGE:/ABSORB:）、JOIN-*（JN-）、DIV-*（DIV:）。账本文本契约：TSV 转义封闭三则（\t/\n/\\），引文字段=源码行经转义后的**全文不截断**；合并=cat|sort -m 协议命令族+wc -l 行数恒等式，**禁止逐字粘贴搬运**（丢一个制表符即污染账本）。

列可变性白名单：可变=状态类列；不可变=ID/位置/证据/引文类。翻案只动 lifecycle 列、行保留不删——**身份永续，撤档留痕不蒸发**。

### 1.11 协作全景（一条卡的数据流）

```
三清单冻结(sha256) → 发卡(bw/fw/term) → [每轮] 取卡(awk 四项公式)
  → 派 Analyzer(信封+ID 白名单) → A 分片(OBS 观察行→ROLE→FACT→TERM)
  → 3a 归一化 → 3c 状态迁移 → 3d candidate 落账 → 3e FACT 入 facts.tsv(hint)
      → 派 Confirmer(一次一条) → confirmed 才入 step4 K 规则
  → step4 K 级联消 band2 卡(facts_used 回写)
  → candidate → 同轮/次轮盲 Verifier(信封=机器字段+OBS 引文+DISP 行)
      → V 分片(SELF 自采→RUBRIC→VERDICT 三态+severity+cvss+tier)
  → 5a finding 骨架+machine-fields 落行 → 5d Reporter 扩写九节+格式门
  → 5b/5c 实时索引与进度投影 → 下一轮
  → [L1 空] L2 发散(DIV→ext 卡) + 不变式轨(INV×module ext 卡) → 回主循环
  → [收敛] joins 拼链(follow-up ext 卡) → terminal(不变量+G2+G3+报告)
```

全链路任何一步：LLM 只写自己的分片，账本只由协议命令迁移，状态只在盘上（断点续跑/压缩免疫/重启不丢）。

---

## 二、「逐卡五步证伪」机制精读

### 2.1 五步是什么（analyzer.md:9-16）

```
1 DEFINE      读类页面⑥节编号判据（C1-C8 四段式：证据问句+引用类型+推翻反例+反向），
              把要逐条回答的判据编号列在分片头部（供 Verifier 的 RUBRIC 引用）
2 OBSERVE     逐字读卡位置 ±10 行 + 实参来源；每读完一跳立刻写 OBS:{file}:{line}<TAB>{该行全文}
              （含前导空格——全行相等比对）；符号歧义核查（同名定义>1 必须全列或逐个排除）；
              关键位置后一行配 ROLE:{...}<TAB>{root_control|guard|sink_anchor|entry|data_flow}
              ——root_control 必钉（"谁说了算"的那一行）
3 HYPOTHESIZE 最短攻击路径假设 source→…→sink 逐跳列出；不确定的跳标 ?；单次追踪 ≤8 跳
              （第 8 跳仍未到 sink 即停——转 blocked 交接，不许硬撑到上下文耗尽）
4 VERIFY      逐判据证伪（问"为什么这不是洞"）：可控性？（实参谁传的——追到入口或
              persisted_read/external_message）可达性？（路由/鉴权/guards——信封已带+同族差分）
              净化匹配？（决策表三值——多段净化看全部；自命名净化器跟到叶子实现并核查分支可达性）
              影响？
5 CONCLUDE    TERM:{state}<TAB>{reason}<TAB>{facts_used}；七态封闭枚举；不确定偏向 candidate
```

三条结构性保证：**观察先于结论**（OBS 行必须先于 TERM 行——不变量 20 逐行机械查，「批量贴标在结构上不可能」）；**结论只允许引用已写盘的 OBS 行**（「脑补的跳写不出观察行」）；**提交前自验**（对每条引文跑 sed -n 比对——「是抄的能过，编的过不了」）。

### 2.2 为什么是证伪（falsify）不是证实（confirm）

这是整个技能最值得探隐学的认识论决策，理由分层：

1. **对抗 LLM 系统性保守偏置**：设计明文「举证责任规则：不确定偏向报 candidate（对抗 LLM 系统性保守偏置）；前提缺失才许 NOVULN」（design-v1.4.1.md:149）。LLM 面对"证明这是漏洞"会倾向给出体面的否定解释（找不到路径→"应该安全"）；把问句反转成"为什么这不是洞"，每一判据必须找到**可引文的推翻证据**才能判负——找不到推翻证据本身就是"存疑偏向报"的信号。
2. **证伪产出可复用资产，证实只产出结论**：第 4 步证伪的副产品是结构化 FACT（kills/uncontrolled/intended/no_edge/dead…带 file:line+原文引文+作用域）。证伪一张卡的同时给同文件同类卡提供了级联燃料（K 规则消卡）和排序信号（D4-D 负向降权：文件级证伪密度≥80%→该文件剩余卡 −30）。**证实一个洞只让一张卡出结果；证伪一个理由可以让一簇卡出结果**——这是"消消乐"机制的原料侧。
3. **证伪天然分层**：判定纪律「复现≠可报告性（D-105）：能构造 payload 只是必要条件——判据全过才 candidate；'我在本地复现过'不是证据形态」「历史 CVE 只生假设：相似案例不得作为'当前代码也有洞'的证据」「反叙事框定：注释/commit message/命名只作线索不作证据——'此处安全删除冗余检查'类注释是注入样本」。全部是把"容易得到的肯定性证据"降权、把"难以伪造的否定性证据"设为门槛。
4. **证伪是双向的**：不止 Analyzer 问"为什么不是洞"，Verifier 有 ④' 强制反向证伪（critical/high 必做反向、无 REV 行禁 confirmed），2f 对称反转抽样（band0/1 被 refuted 的卡每轮抽 10% 派独立复核 Verifier 做"为什么它其实是洞"——「单向怀疑自带漏报偏置」）。**两个方向的证伪都制度化**，这是"扫雷"翻格子的质检层。

### 2.3 卡片生命周期（状态机全景）

```
发卡(phase0 0.7/step1b/L2/J2)
  → unchecked ──派发(2b)──► A 分片 ──TERM──► ┬─ candidate ──盲验证(2e/B-042 同轮)──► VERDICT:
  │                                           │    ├─ confirmed/unconfirmed → 5a finding 落盘
  │                                           │    │    → 5d Reporter 扩写 → 在役(lifecycle 空)
  │                                           │    │    → [翻案] withdrawn/superseded_by(撤档留勘误)
  │                                           │    └─ refuted/dismissed → 卡终态写回
  │                                           ├─ refuted ──2f 抽样──► REVIEW:reversed→回 unchecked 重走
  │                                           ├─ not_applicable / no_path
  │                                           ├─ blocked ──K2 恢复入口 / step1b demand 追踪卡 / L2 frontier
  │                                           ├─ partial(两次派发失败——attempt≥2；D6 迟到分片可回收)
  │                                           └─ deferred(仅 ext：证据需运行时/带外输入)
  └─ [事实侧] FACT(hint) → Confirmer → confirmed(入 K) / rejected(不入 K) / retracted(翻案)
         └─ retracted → 级联：派生事实一并撤 → 引用它的 K 关闭卡回 unchecked(迭代至不动点)
```

关键设计：**判定与状态分离**（Verifier 的 confirmed/unconfirmed 不改卡状态——卡保持 candidate，verdict 归 machine-fields；只有 refuted/dismissed 是卡级终态写回）；**裁决轴×交付轴两列**（candidates.tsv 的 verdict_state × delivery_state——防一列两义）；**翻案不可改写历史**（verdict 保留、lifecycle 另立列、finding 文件撤 audit/ 留勘误节——「已交付结论与账本永不许永久不一致」）；**attempt 统一计费**（分片缺失/无 TERM/TERM 非法三者同等计费，≥2 次→partial——防无限重派）。

### 2.4 防伪造结构小结

一卡一派（任务间隔离）+ 逐观察落盘（任务内防脑补）+ 引文全行相等比对（不变量 9，sed 复核）+ 盲验证（不见发现者叙述）+ 自推先于对照（封选择偏差）+ 自采引文（抄不了）+ 对称反转抽样（防漏报偏置）+ ID 白名单嵌入（防编造锚点——从结构上消除自由度）+ 反叙事框定（注释是注入样本）。九层防伪造，全部机械可查、无一层依赖"模型自觉"。

---

## 三、「消消乐」与「扫雷」：两个游戏隐喻的工程本体

### 3.1 出处考证（先交代证据）

对 gensift 全目录（含 docs/）与探隐 docs/、/tmp/gensift 备份做了 grep（模式：消消乐|扫雷|消除|连连看|地雷|排雷|盲验证）：

- **gensift 技能内**：「消消乐」「扫雷」**字面均不存在**（"消除"只出现在净化语义——"净化是否消除载荷形态"，与游戏无关）。
- **探隐侧唯一出处**：HANDOFF.md:1445「GenSift 分析舰（6-gensift.md,含「消消乐/扫雷」思路解读）」——即本报告的任务来源，是**父会话对 GenSift 机制的命名**，不是 GenSift 自称。
- 结论：这两个词是对 GenSift 两簇机制的**外部隐喻命名**。按任务要求"从机制本质提炼"：**消消乐 ≈ 批量匹配消除机制（K 级联 + 语义合并）；扫雷 ≈ 盲探全覆盖机制（逐卡全翻 + 状态在盘 + 翻错重翻）**。以下逐个对账。

### 3.2 消消乐 = 批量匹配消除机制

**游戏本质**：同色/同形方块凑齐匹配条件 → 整批消除 → 板面收缩 → 消除产生连锁（combo）。

**GenSift 里的对应件（三处）**：

1. **K 级联（主件，main-loop step4，main-loop.md:1076-1112）**：一条 confirmed 事实（如"该文件全族调用被同一净化包装器包裹"=kills，scope=file）→ awk join 机械匹配 → **同文件内全部 band2 卡一次性批量消卡**（K1 uncontrolled→refuted / K1b intended→not_applicable / K2 kills→blocked / K3 no_edge→no_path / K4 dead→no_path 文件级消）。Summarizer 就是"凑同色方块的人"：band2 卡按类聚簇批量提类级事实（"同族调用点共享常量实参→intended；同一净化包装器包裹全族→kills"）。设计文档自己写的算术感：「级联越挖越快」——**消除产生连锁**：一张卡的证伪事实喂排序（suspicion 信号）、喂级联（K 规则）、喂负向降权（D4-D），后面同簇卡越消越快。
2. **语义合并（2d/2d-consume，main-loop.md:382-475）**：待验证候选 ≥25 触发 → Reporter 合并轮 → 判据唯一："**修复 canonical 问题也能同时修掉每个被吸收候选才可合并**；不许因共享子系统/CWE/路由族/sink 族/攻击话术相似而合并" → 被吸收者落 merged-into-X + also-reported-by 不另起行、已交付 finding 转 superseded_by 撤档留勘误。**同修复点的候选批量归一**——验证预算省在去重之后（"先去重再验证，省的是验证派发预算"）。
3. **demand-driven 追踪卡（step1b）**：bw 卡 blocked（找不到常规 source）→ 对同文件回读点按需发 fw 卡——按需补格子，不预发万级弱 source（成本炸弹闸门）。

**消消乐的危险与 GenSift 的护栏**（这部分比机制本身更有价值）——游戏里错消一颗只是丢分，审计里错消一簇=**批量漏报**。GenSift 给"消除"上了五道锁（design-v1.4.1.md:175-187 剪枝定理）：

- **判据无关性**：剪枝判据必须是类/入口的固有属性，实例分析结论不可跨实例传播；
- **强度配称**：用于剪枝的事实必须**独立确认**（Confirmer 新鲜上下文真读代码引原文，一次只一条——"批量复核=强度配称失守"），验证强度高于单卡分析；
- **band0/1 永不机械消除**（不变量 12）：高危卡只接受本卡五步法终态——**消消乐只准消低危噪音带（band2），雷区（band0/1）一格一格翻**；
- **级联必须可逆**：retract 翻案 → awk 反查 facts_used → 被消的卡全部回 unchecked 重走五步（迭代至不动点），「错消不可逆就成了新的漏报源」；
- **每消一卡回写 facts_used**：级联可追溯（不变量 11——被消的卡能指认是哪条事实消的它）。

外加 Summarizer 侧的**作用域保守规则**：「scope_type 就低不就高（file < entry_id < entry_family）……作用域写宽一格=过量剪枝，是打地鼠的新语义通道，宁可多报窄的」与警句「**一条错=一簇卡误消**」。

**工程价值**：万级 sink 的成本解。逐卡五步是质量底线但 token 与卡数成正比；级联让"同理由的一簇"只付一次确认成本。没有消消乐，千文件级过夜跑不动；没有上述护栏，消消乐会把漏报做成批发。

### 3.3 扫雷 = 盲探全覆盖机制

**游戏本质**：整个盘面每格必须被翻开或标旗；翻开靠逐格点击（盲探），但已翻格子露出的数字让你**推理**出周边格子；不能抽样跳格（跳格=可能踩雷）；进度不可逆（翻开的格子不会盖回去）；标旗可以拔（翻案）；全部翻完才算赢。

**GenSift 里的逐项对应**：

| 扫雷要素 | GenSift 对应 | 出处 |
|---|---|---|
| 盘面 = 冻结的格子集 | 三清单冻结（sha256 封印）：每 sink 一张 bw 卡、每 source 一张 fw 卡、每 file 一张 term 兜底卡——**三个独立方向逼近完备、互为盲区兜底** | phase0 0.6/0.7；design §3 |
| 每格必翻、不许抽样 | 「覆盖不可谈判：所有卡必须被分析，不可跳过、不可抽样」——红线第 1 条；test/demo 角色卡也只是**排尾不剔除** | SKILL.md:103 |
| 逐格点击 = 盲探 | 一卡一派独立子代理五步证伪；编排器不读代码（元规则） | agents/analyzer.md |
| 数字推理（省点击） | confirmed 事实=翻开的数字；K 级联用数字推掉周边 band2 格 | step4 |
| 插旗 = candidate | 卡转 candidate → 等盲验证裁决（旗子不等于赢——confirmed 才出 finding） | 3d/2e |
| 翻错重翻 | 2f 对称反转抽样：band0/1 已判 refuted 的卡每轮 10% 独立重探"为什么它其实是洞"，reversed → 回 unchecked 重走 | main-loop.md:557-609 |
| 进度不可逆 | L1 单调性：分母 unchecked 只许不增（唯一回升通道=retract 翻案且留痕计额度；违例=exit 1 技能缺陷级中止） | step0 |
| 全盘翻完才算赢 | 完成=awk 数分母 unchecked=0 ∧ ext deferred=0，**"任何角色宣布完成无证据效力"**；G2 闭卷对账"每张卡的下场可指认" | design §7.1/P4 |
| 存档续玩 | 状态全在盘（checks.tsv/STATE/分片）——关宿主即中断，同源码路径再发起自动断点续跑 | SKILL.md:35-42 |
| 防误触收工 | Stop hook：盘上还有未翻格子时 exit 2 逼续跑；批轮 GENSIFT-CONTINUE 续跑锚点 | hooks/stop-hook.sh |

**盲验证在扫雷隐喻里的位置**：Verifier 是"第二个独立扫雷员"——只给你坐标（机器字段+引文行），不给前一个人的判断；你必须自己先走一遍（⓪ 自推先于对照、≥3 次实际读码、≥1 条自采引文），再比对两人路径差异。「盲的定义是不见发现者结论与叙述，不是不见观察引文：引文是与你有同等地位的源码事实，不是发现者的主张」（verifier.md:7）。

**工程价值**：扫雷律是**漏报防线**。渗透/审计工具的失效模式排序里，"漏掉"比"报错"更致命（报告方无感知）。GenSift 把"不漏"做成了算术（分母封印+三向完备+终态封闭+完成=计数派生），把"每格有据"做成了账目（coverage.md：每张卡的下场可查，"没发现"必须能解释——refuted 按 K 规则分布/blocked 恢复入口/pattern-undetectable 披露/降级清单）。

### 3.4 两隐喻的合成定理

GenSift 的调度本质可以写成一句话：**用扫雷的纪律保证全覆盖（每格必翻、进度只增、翻完才算赢），用消消乐的级联消化规模（同理由簇批量消、连锁加速、错消可逆），且消消乐只准在非雷区（band2）作业、雷区（band0/1）必须逐格人工翻（五步+盲验证+10% 重翻）**。

两个隐喻不是两个功能，是同一条覆盖红线在"质量"轴与"成本"轴上的投影——设计文档的原话正是：「暴力逐卡是默认路径与质量底线（级联完全失效退化为暴力也必须跑完，验收级红线）；级联是随时可退出的加速器」（design-v1.4.1.md:75）。扫雷=不可退出的部分；消消乐=可退出的部分。

---

## 四、功能清单与成熟度评估

### 4.1 功能清单（对外可观察的能力面）

| # | 功能 | 载体 | 状态 |
|---|---|---|---|
| 1 | 全自动攻击面枚举（三清单+三向卡） | phase0 | ✅ |
| 2 | 逐卡五步证伪分析 | agents/analyzer + main-loop 2b | ✅ |
| 3 | 事实级联剪枝（K 五规则+翻案级联） | step4 + 3e | ✅ |
| 4 | 盲验证（自推先对照+自采引文+定级矩阵） | agents/verifier + 2e | ✅ |
| 5 | 双向对称反转抽样（10%） | 2f/3g | ✅ |
| 6 | 实时报告（live_findings_index 五节+progress_board+当轮 finding 交付） | 5a-5d | ✅ |
| 7 | L2 发散（frontier→DIV→ext 卡）+不变式轨（INV×module） | l2.md | ✅ |
| 8 | 跨模块拼链（joins+follow-up 卡）+组合分析 | joins.md | ✅ |
| 9 | 终态三道门（G1 锚点预检/G2 闭卷对账/G3 双跑稳定分级契约） | terminal.md | ✅ |
| 10 | 20 条对账不变量（引文全行相等/观察先于结论/四相等…） | terminal.md | ✅ |
| 11 | CALIBRATION 知识闭环（run 缺口→草案→人工批准） | terminal.md | ✅ |
| 12 | 处置反馈（dispositions 七值+到期降级+回归检测） | feedback/ + terminal A4 | ✅ 机制/库空 |
| 13 | 断点续跑（状态在盘+幂等合并+schema 迁移） | SKILL.md + step0 | ✅ |
| 14 | 防停三层（批轮+Stop hook+插件守卫） | hooks/ | ✅ |
| 15 | 三平台（bash/pwsh 双件逐字节等价+黄金夹具验证） | phases/*.ps1 | ✅ |
| 16 | 双宿主适配（Claude Code/opencode 四适配电+收尸看门狗） | hosts/ | ✅ |
| 17 | 退出码 CI 语义（0/1/2/3） | terminal.md | ✅ |
| 18 | advisory 种子（CVE 锚点加权+召回下界） | phase0 0.5 + step1 cve_adj | ✅ |
| 19 | 执行档授权（T0-T3 阶梯，runtime_verification=allowed 解锁） | verifier + hosts | ✅（T2/T3 沙箱边界声明在适配电） |
| 20 | 库模式审计（source 语义切换+分母强度诚实降级） | langpacks sources-lib | ✅ |
| 21 | SARIF 导出 | — | ⏳ 二期机械件（设计已列） |
| 22 | 增量模式（diff→定向发卡） | — | ⏳ 二期（lineage 三列 schema 已预留） |

### 4.2 成熟度分层判定

**设计/协议层：极高（罕见的高完成度）**。证据：
- 设计文档 v1.4.1 带**三轮对抗性评审修订记录**（v1.2 二轮评审规格冻结 → v1.3 五路专家评审 68 条 → v1.3.2 六轮端到端自审计 10 条衔接债 → v1.4.0 design-suspects 11 条裁决 → v1.4.1 两条终裁），每条修订带 suspect 编号与选项；
- **设计条款注册表制度**（conformance-completion.md）：设计文档每条 normative 条款一行判定（wired/partial/missing），验收门=无 UNCOVERED 无 ORPHAN——这是"设计=分母、实现=对账"的防遗漏工程，与它自己审计目标时的 G2 闭卷同构；
- 指令面预算公示（README:248-267）：入口 120 行恰在上限、59 命令块 3282 行、超预算处逐条**口径修订公示不静默**（D-008/D-004/D-005）；
- 状态机/不变量/退出码/敏感等级/敏感数据处置全部成文。

**知识资产层：起步集完成、正在长**。59 pattern 文件 509 ERE；fixture java 达标集、ts/python 起步集（类页面⑫如实标"实际档位"）；类×语言矩阵 59/72 缺口如实披露（D-037）；不变式仅零售域 14 条 provisional；处置库**空**（dispositions.tsv 仅表头）。

**实战层：早期，有真跑但闭环未满**。可考的实跑痕迹：
- **aiohttp 首跑**（2026-08-25）：放行门自述「首轮基线经 audit-live.sh 审计 E2b FAIL（14 张证伪零 FACT）——该会话先于 D4-D 契约，FAIL 是诚实基线不是回归」——真跑发生过、效果审计跑过、失败被吸收成新契约（D4-D 证伪事实硬规则）；
- **真宿主摄入事故修复链**：3a/3c/3e 注释里多处"真宿主摄入净化（实跑教训 2026-08-25）/活会话实证 2026-08-27 CK-bw-00030/31/P8 实证 CK-bw-00005/00008（126 行真分析被'无TERM'熔断成 partial）"——子代理格式方差、迟到落盘、绝对路径混入等**只有真跑才会暴露的问题已被逐个机械化修复**（D6 partial 回收通道、迟到分片防御净化、attempt 计费）；
- **dvpwa 黄金夹具 58 块双跑**（posix/ps1 逐字节等价验证）+ 看门狗阈值实测记录（单枚举块 1-3s、双跑全程 2-3 分钟）；
- **放行门 v2.1-M2 尚无全绿记录**：要求"真宿主真目标 ≥10 轮完整会话+效果审计 E1/E2/E3 全绿"，README 只记载了首轮基线 FAIL——即**还没有一次完整通过放行门的版本发布**；类页面"最近校准: S1 起步集（2026-08）"佐证知识层未经历第二轮校准。

**成熟度总评**：一个**机制上接近自洽、实战验证刚起步**的系统。协议/账本/不变量的严谨度超过多数商业 SAST 产品的文档水准；但"发现质量"（召回/误报数字）仍在门内禁声阶段（门内禁声律：三道门全绿前不得声称任何召回/精度指标）。风险最高处不在机制，在：①知识资产的广度（24 类×3 语言起步集 vs 真实世界的 CWE 长尾）；②每卡成本的量级（token 与卡数成正比，级联对 band0/1 无效——高危必须逐卡，这是覆盖红线的代价）；③宿主依赖（Claude Code Stop hook 的版本回归、opencode 插件事件 schema deprecated 都被诚实记录在案）。

---

## 五、对探隐白盒引擎的吸收判决

### 5.1 前提：两套世界观的差异先摆清

| 维度 | GenSift | 探隐（tanyin-product-v1 v1.0a 修正案 A） |
|---|---|---|
| 产品身份 | 白盒审计技能（审计即产品） | AI 自动化渗透平台（**审计是自主性地基，不是产品身份**） |
| 运行形态 | 寄生 LLM 宿主会话，编排器=LLM，确定性=TSV+内联 shell | Python 3.9 stdlib 自持编排器常驻，战士=opencode，账本哈希链 |
| 信任根 | 静态引文可重放（机械层）+ 执行 oracle（T2/T3 可选） | **黑盒重放实证（无重放不计分精度门）**——引擎情报必须经实证才配成发现 |
| 引擎产出 | finding（九节报告直接给开发修复） | **假设（intents 层 engine-hyp）**——与战士自产意图同池竞争预算（engine-fusion §0："引擎不产发现，产假设"） |
| 覆盖语义 | sink 矩阵全覆盖不可抽样 | endpoint/sink 全入矩阵不可抽样（修正案 A 明确继承） |

融合点已经由 engine-fusion-architecture.md 定死：**intents 层不是 findings 层**；六段管线（Refiner 精炼→Intent 入账→预算仲裁→探针转化→黑盒实证→反哺）；账本映射零新表（intents kind=engine-hyp / facts kind=engine-static / edges cross_ref / E-index 同规格 / budget 统一计费）。§6 施工顺序五步：意图卡 schema→engine-hyp 通道+配额→sim 注入→codex E2E→反哺通道。

### 5.2 直接吸收（拿来到位，改动 < 20%）

| # | 吸收物 | GenSift 出处 | 接进探隐的落点 | 置信度 |
|---|---|---|---|---|
| A1 | **.pattern 文件格式 + 方言白名单 + fixture 三件套门 + pattern-lint** | classes/patterns/ 59 件、fixture-spec.md、phase0 0.0 门 | 车道A 确定性解析器的模式资产（修正案 A 原文"借鉴 GenSift .pattern 文件"）：ERE 子集纪律（禁 \b/\w/\d/lookaround）、LC_ALL=C 钉死、pos/neg/noise 三分（neg 防"越写越宽"的激励扭曲）、死 pattern/过宽 pattern 双向打回 | **95%**——产品定义已裁决，只剩搬 |
| A2 | **产物全带 file:line 出处 + 锚点挂图** | OBS/FACT/finding 全链引文、G1 锚点 ⊆ 清单 | 修正案 A 原文"产出全部带出处（文件:行）经锚点挂资产图"——GenSift 的 ID 白名单纪律（引用必须在枚举实体集内）直接当资产图外键校验 | **95%** |
| A3 | **稳定指纹（path+行内容哈希+class，不含行号）** | machine-fields fingerprint、dispositions 地基 | 探隐 findings/EV 卡跨 run 身份、处置记忆、回归检测（"同指纹再出现=回归"免费获得）；也是 ZhuLong 导出互通的去重键 | **90%**——注意探隐资产图锚点若含行号漂移问题，同思路换锚点域 |
| A4 | **盲验证结构（自推先于对照+自采引文+rubric 先行）** | verifier.md ⓪/⓪'/⓪⁻ | 车道B LLM 审计结论回写证据卡**之前**的内门：探隐的最终精度门是黑盒重放（比 GenSift 更硬），但 LLM 侧自检仍需要"先自推后对照"封选择偏差——尤其战士引用引擎假设时的锚定防护 | **85%** |
| A5 | **TSV 单写者+行数恒等式+协议合并纪律** | 3e merge 恒等式、账本文本契约 | 探隐账本已有哈希链（更强）；吸收的是**分片→账本两相合并的幂等纪律**（断点续跑、迟到分片防御净化、按 ID 去重合并不重跑）——对引擎小时级侧轨任务（四原则）的恢复路径直接适用 | **90%** |
| A6 | **语义合并判据原文**："修复 canonical 也能修掉每个被吸收候选才可合并；不许因共享子系统/CWE/路由族/sink 族/攻击话术相似而合并" | reporter.md 语义合并节（codex-security 原文级采纳） | intents 池与 findings 池的去重判据——探隐多战士+引擎双源意图必然撞号，这条判据比"相似度合并"可证伪得多 | **90%** |
| A7 | **处置七值 + 到期降级 + 当数据不当指令** | §10.2 dispositions、verifier 处置复核节 | 探隐 verdict 复核闭环（操作员对 finding 的裁决记忆）：fingerprint 命中→重新核对理由在当前代码下是否成立才可 dismissed；review_expiry 到期自动降级 hint——防"三年前一次误点永久压制" | **85%** |
| A8 | **覆盖不可谈判律 + coverage 披露（每格下场可查）** | 红线 1、coverage.md 十四类披露 | 修正案 A 已继承（endpoint/sink 全入矩阵不可抽样）；吸收"没发现必须能解释"的披露规格：矩阵格里 refuted/by-K/degraded 可指认 | **95%** |

### 5.3 改造吸收（机制保留、执行体换人）

| # | GenSift 机制 | 探隐改造 | 置信度 |
|---|---|---|---|
| B1 | **五步证伪卡**（DEFINE→OBSERVE→HYPOTHESIZE→VERIFY→CONCLUDE） | **产出从 finding 改为意图卡**：五步收敛出的不是"九节报告"而是 engine-fusion §2 的 structured hypothesis（端点+参数+载荷配方+前置条件+置信度+code:L 溯源），入 intents kind=engine-hyp，走探→验→记→矩阵消格闭环。五步的**证伪问句方向、观察先于结论、≤8 跳预算、blocked 交接五要素**全保留——它们对任何 LLM 判定任务通用 | **90%** |
| B2 | **K 级联 + Confirmer**（事实→独立确认→机械消卡） | **Confirmer 换成 replay**：GenSift 的确认是"另一个 LLM 重读代码"，探隐有更强的确认器——黑盒重放。engine-static 事实（净化覆盖/死路由/不可达）入 facts 后，其"确认"= 战士实证或反证回灌打标（Verified/降权）。**级联算术保留**（同簇端点共享一条已证事实→矩阵批量消格），护栏全保留（band 高危不机械消/可逆/可追溯） | **80%** |
| B3 | **band 分带 + 优先级公式**（100·band+suspicion+centrality+cve_adj） | 探隐已有自己的仲裁（置信度×矩阵新颖度×可达性，engine-hyp 配额≤40% 保自主广度）。吸收的是**公式化+机械可算+负向反馈**三条纪律（D4-D：证伪密度降权——探隐战士对某模块连番空手时同样该降权），权重常数按探隐实测重校 | **75%** |
| B4 | **防停三层**（批轮/Stop hook/GENSIFT-CONTINUE） | 探隐自持编排器**天然有循环活性**（Python 主循环不会"回合收敛本能"），Stop hook 不需要。但**回合终结白名单思想**对战士会话有用：战士中途总结=禁止，进度只落盘上账本——这已是探隐纪律，交叉印证而非新吸收 | **70%** |
| B5 | **ext 卡 + origin_ref + deferred**（追加卡两本账） | intents 生命周期"要么验证要么 blocked 不蒸发"语义同构；吸收 ext 的**两本账纪律**：追加假设不计入冻结分母覆盖率、单独以闭合率+零 deferred 披露——探隐资产图挂载后新锚点同样需要"分母卡 vs 追加卡"分开记，覆盖算术才闭合 | **85%** |
| B6 | **G3 双跑稳定分级契约**（机械层逐字节/语义层重合度+归因） | 探隐度量纪真律（experiments/ 预登记+可复现三要素）是同款精神。吸收 G3 的**归因五分类**（判定翻转/抽样波动/L2 差异/refreeze 差异/处置库变更）作为引擎双跑 diff 的归因词表 | **75%** |

### 5.4 不采与调和（含最关键的哲学冲突）

**冲突焦点：「零自研代码」哲学 vs 探隐确定性解析车道（车道A 是 Python 解析器=自研代码）**

先读 GenSift 自己的裁决边界（design-v1.4.1.md:9，用户裁决澄清原文）：「零代码指**工程由 LLM 语义驱动**——不是用程序写死规则去挖掘漏洞（如 vuln_agent 的 python+LLM 形态）。宿主原生配置（Stop hook 声明、权限 allowlist）与协议单行命令属宿主原语，不是检测逻辑程序」。

**调和判决：不冲突，因为两系统画的是同一条线，只是线的两侧不同物。** GenSift 的 P3 本义有三层：①信任根最少化（不引入第三方程序就无需信任它）；②**检测语义不许写死成程序**（漏洞判定权永远在 LLM+可复核引文，模式只做枚举不做判定——"LLM 不是模式库的执行器"）；③它自己其实**大量使用确定性代码**——awk 状态机、grep 枚举、sha256 封印，只是以内联单行命令形态存在而非脚本文件。探隐车道A 解析器正是这同一层的等价物：Python 正则解析=GenSift 的 grep 枚举；探隐车道B LLM 审计=GenSift 的五步+盲验证；探隐 replay 精度门=GenSift 的执行 oracle 阶梯（甚至更强）。**吸收的是"机械层可重放/语义层归 LLM/判定与叙事分离"的边界纪律，抛弃的是"必须以内联 shell 存在"的形态约束**——那条约束的成因是 GenSift 必须寄生宿主会话（无法部署守护进程），探隐没有这个约束。置信度 **90%**。翻案条件：若实践中出现"解析器开始内嵌判定逻辑"（如 Python 里写 if-else 判漏洞而非只产出候选+出处），即越线——判据：解析器输出含 verdict 语义字段。

其余不采清单：

| # | 不采 | 理由 | 置信度 |
|---|---|---|---|
| C1 | **六角色全编队**（recon/confirmer/summarizer 等作为独立子代理角色） | 探隐已有战士群+规划者拓扑；GenSift 角色分拆的实质是"判定权分离"，吸收原则（B1/B2 已含）不照搬编制——探隐的 Confirmer 是 replay，Summarizer 的类级事实可由车道A 聚类直出 | **85%** |
| C2 | **G2 闭卷对账/CVE 编号污染剔除** | 针对"LLM 训练记忆冒充发现"的审计域特化防线；探隐精度门（无重放不计分）在结构上已防住同一风险——重放不了就是假不了 | **85%** |
| C3 | **类页面 12 节模板全量照搬**（FP 卡库/降级反例/定级矩阵等） | 车道B 初期只需要判据原子（编号证据问句）+Source/Sink 模式指针；FP 卡库/定级阶梯是审计报告交付物（severity 给开发），探隐意图卡要的是"可实证的攻击配方"不是"给开发的修复建议"——第九节根因修复那套不进 v1.0a，留到探隐出审计报告功能时再取 | **75%** |
| C4 | **指令面预算制度**（入口 ≤120 行/分角色预算表） | GenSift 的约束成因是宿主上下文窗口+prompt-cache 命中；探隐编排器是代码，token 预算只发生在战士/规划者调用侧——纪律精神（控制 LLM 必须内化的复杂度）保留，数字制度不搬 | **85%** |
| C5 | **三平台双宿主适配层**（hosts/×4+ps1 翻译件+reaper） | 探隐单平台（操作员自有电脑）单宿主形态已定；reaper 看门狗思想若未来引擎侧轨多进程化可回取 | **90%** |
| C6 | **不变式轨首批内容**（retail.inv 14 条） | 零售域 provision 状态，探隐渗透域暂无对应场景；**机制保留**（INV×module 发卡+三映射），语料等真实目标域出现再建 | **80%** |

### 5.5 判决汇总与施工映射（对 engine-fusion §6 五步的落点）

```
§6-1 意图卡 schema      ← A2+A3（出处+指纹）× B1（五步收敛为 structured hypothesis：
                            端点+参数+载荷配方+前置+置信度+code:L 溯源）
§6-2 engine-hyp 通道    ← A5（两相合并/幂等）× B5（两本账）× A8（覆盖披露）；
                            配额仲裁已有，补 B3 的负向反馈信号
§6-3 sim 注入场景       ← A6（语义合并判据防同根因意图重复计分）
§6-4 codex E2E          ← B2（级联算术+replay 确认器）；A4（盲结构防战士被引擎叙述锚定）
§6-5 反哺通道           ← A7（处置七值+到期降级）+ B6（双跑归因词表）
车道A（并行）           ← A1（pattern+fixture 门+lint）——v1.0a "白盒引擎并入当解析前端"的确定件
```

**总体判决**：GenSift 是探隐 v1.0a 白盒双车道里**车道B 的完整参考实现 + 车道A 的模式资产库**。直接吸收八件（A1-A8，均为低改动高确定性）、改造六件（B1-B6，机制保留执行体换人）、不采六件（C1-C6，各有探隐侧等价物或域不匹配）。**零自研代码哲学不构成阻塞**——它护住的是"检测语义不写死成程序"的边界，这条边界探隐的原架构（程序执法记账+LLM 语义判断+重放精度门）本来就在守。

**关键风险提示（探隐侧特有的两个）**：
1. **成本模型**：GenSift token 与卡数成正比且级联对 band0/1 无效（高危必须逐卡）。探隐把车道B 定位为"规划者按需调用的深度车道"是对的——**不要让引擎全量跑五步**，让车道A 先出候选、规划者按矩阵新颖度点菜式深挖，否则一次审计会吃穿预算。
2. **假设不蒸发律的接口**：engine-hyp 超时 GIVEUP=显式 blocked 已定，但 GenSift 的 partial（两次派发失败）与 deferred（等带外证据）两个披露态在探隐 intents schema 里需要对应位——否则引擎侧轨的"半成品"会被迫伪造成 done 或蒸发。

### 5.6 置信度与翻案条件总表

| 判决块 | 置信度 | 翻案条件（出现即重审） |
|---|---|---|
| A1 pattern 资产直搬 | 95% | 车道A 实测中 ERE 表达力不足（如需跨行/数据流敏感模式）→ 升级为结构化解析规则 |
| A3 指纹跨 run 身份 | 90% | 资产图锚点语义定为"节点 ID"而非"位置"→ 指纹改锚点域重定义 |
| B1 五步→意图卡 | 90% | sim 注入实验显示五步粒度过细（单意图 token 成本>实证成本）→ 砍 OBSERVE 强制逐跳、保留证伪问句方向 |
| B2 replay 替 Confirmer | 80% | 出现"不可重放但可静态确证"的事实类（如死代码/净化覆盖）→ 保留一个静态确认子通道 |
| 哲学调和（零代码 vs 车道A） | 90% | 解析器输出出现 verdict 语义字段=越线，回退纯候选+出处 |
| C3 类页面模板缓采 | 75% | 探隐增加"审计报告"产品面（给开发的修复建议）→ ⑨⑩ 节回归吸收 |
| 整体（GenSift 值得作为车道B 骨架） | **92%** | 唯一翻案场景：codex E2E 实测中五步卡的成本/收益比劣于"战士直接读码自由挖"（McNemar 双臂无显著差异）——那将证伪整个车道B 的结构化价值，届时车道B 降级为纯模式库消费者 |

---

## 附：本报告的证据纪律声明

- 对 `~/.claude/skills/gensift` 全程只读（read/glob/grep/bash 只读命令），零写入零移动零改名零 git 操作；
- /tmp/gensift 备份经 `diff -rq --exclude=.git` 与本地逐字节比对一致（本日快照）；
- 所有 file:line 引证均来自直读原文；「消消乐/扫雷」字面不存在的结论来自全目录 grep（模式含变体）；
- 探隐侧引用：tanyin-product-v1.md（修正案 A/B/C）、engine-fusion-architecture.md §0-§6、HANDOFF.md:1445、plans 目录清单。

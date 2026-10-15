# 06 · 白盒引擎+双图一桥设计正确性独立评审（2026-10-15 方向评审）

> 评审镜头: v1.0a 白盒引擎+双图一桥设计正确性（独立评审,不与其他专家通气）。
> 靶项目: /Users/wgen/redteam-agent（探隐,产品定义 v1+修正案 A 白盒双车道之后,v1.0a 动工之前）。
> 证据基（全部实读）: docs/design/tanyin-product-v1.md（修正案 A/B/C 全文）/ docs/research/liveui/6-gensift.md（408 行全读,重点 §五吸收判决）/ 7-codex-security.md（重点 §二沙箱+§五复用判决）/ 2-artex.md + docs/research/artex-deep-dive/2-data-graph.md（ARTEX 双图真身）/ docs/design/2026-09-24-graph-driven-ops.md / 2026-09-27-endpoint-dict-v2.md / engine-fusion-architecture.md §0-§6 / BLUEPRINT-RECON.md / architecture-map-v3.md / HANDOFF.md 尾部;**代码实读**: cli/ledger/write_cmds.py（边/意图/矩阵执法段）、schemas.json（13 表列）、matrix_init.py（TYPE_VOCAB_CLASSES+submatrix 铸造）、graph_cmds.py（图查询三命令）、check_cmds.py（source-code parent 边强制）。只读零 git;唯一写入=本文件。
> 一个前置事实纠偏: 产品文档写了 D1-D4,D5（源码定位=渗透内环）只见于本次评审任务书,未见落档——**这本身就是第一个发现: v1.0a 最核心的定位裁决还活在口头**。

---

## 【总判决】

**有条件通过——方向对,设计还没发生。置信度 0.78（方向正确性 0.85,当前设计完备度 0.45）。**

方向对的部分给足分: 白盒=渗透内环（情报喂探→验→记闭环,而不是旁挂审计器）、车道A/车道B 按枚举/判定分权、引擎产假设不产发现（engine-fusion §0）、吸收对象选 GenSift（纪律）+偷 codex（沙箱与格式）而不外接——这四个选择都经得起拷打,与既有账本架构零冲突。

但"双图一桥"四个字下面目前压着**五个未裁决的接口**,每个都有现成资产可复用、也都有真实的语义缝隙: ①桥用什么边型（今天要么走 cross_ref 逃生舱进错边类,要么 schema bump,产品文档只字未提）;②sink 进哪本账（intents kind 枚举里没有 engine-hyp,facts.intent_id 外键与车道A 无意图先行相抵触）;③矩阵怎么扩（"所有 sink 入矩阵"若被机械执行=语义错误的 12 万行矩阵）;④调度激励（deferred 是合法态+否证无信用=结构性跳卡通道,GenSift 的警告原文就摆在那）;⑤车道A 的"确定性"有三处比看上去软（POSIX ERE≠Python re、YAML 不在 stdlib、解包安全）。这五件事不裁决就动工,v1.0a 会变成"口号驱动的实现自由发挥"——每一条都会被实现者用最顺手的方式悄悄定掉,而最顺手的方式恰好都是错的那种。

另有一条贯穿性批评: **蓝图巡检律（HANDOFF 2026-10-15 立律: 任何设计提案前必查三处并引用现状）在 v1.0a 自己的设计输入上已经违律**——产品文档说"白盒引擎并入当解析前端",却没引用 matrix_init 的 submatrix 铸造（两本账的机械实现已在库）、没引用 assets type=source-code 已在枚举（A6 代码与物料,矩阵类映射都写好了）、没引用 endpoint-dict §三的 GT 键口径（车道A 输出键形的唯一成文对齐目标）。评审按巡检律替你们补了这笔账,见【被忽视的既有资产】。

### 六问裁决速览

| # | 拷打点 | 裁决 | 详见 |
|---|---|---|---|
| 1 | 双图一桥照 ARTEX 抄对不对 | **不照抄。单图两域+锚点即边**（补资产域,不另起图） | F1 |
| 2 | 车道A 确定性边界判据可操作吗 | 判据存在（无判定律）但不够,**补三律+六个灰区预裁决** | F3 |
| 3 | sink/endpoint 进哪本账,矩阵怎么扩 | endpoint→assets/sink→facts+intents 两本账,**矩阵只加证据位不加行** | F4 |
| 4 | 点菜式深挖激励对吗 | **错——排序权可以给,终止权和剪枝权不能给**;不修=F2 复刻 | F2 |
| 5 | codex 六层适用性 | 三成可抄（范式层）,七成错位（Linux 执行栈 vs macOS 解析）;正确落位=T2/T3 | F5 |
| 6 | 与 E4 的衔接 | 白盒实验必须吃下 E4 全部四条修正,否则第一个被错尺错杀的就是车道B | F6 |

---

## 【发现按严重度】

### F1（致命·架构）"双图一桥"若照 ARTEX 抄,会把探隐唯一真源拆成两半——正确裁决是单图两域、锚点即边

**现象+证据**:
- ARTEX 双图的实质（artex-deep-dive/2-data-graph.md）: 探索图（exploration_nodes 7 kind×state 矩阵 CHECK+5 rel 边）承载**过程**;资产图（assets 单表多态+企业归并）承载**真值**、跨任务共享;anchor 桥表(node_id,asset_id)纯两列,"只留推理轨迹 lineage,不控可见性",覆盖度=scope 匹配分母÷fact 锚定分子一条 CTE。
- 探隐已有的对应物全部在库: 账本图谱（节点=九表行 id、10 边词汇、**_EDGE_DIR 代码级方向执法**、哈希链——ARTEX 一样都没有,2-data-graph 对照结论自认"它无哈希链/防篡改,我们核心优势"）;assets.tsv type 枚举**已含 source-code**（write_cmds.py:781）;check_cmds.py:380 **已强制 source-code 资产挂 parent 边**;matrix_init.py:54 已给 source-code 映射 4 个 WSTG 类;graph-neighbors/paths/horizon 三命令已建（graph_cmds.py,命令面 41→44 走微版本勘误先例）。
- 也就是说: "资产图程序挂载"的地基（资产类型+挂载执法+矩阵消费+图查询）四件已有三件半,而产品文档 v1.0a 一句"双图一桥"没有引用其中任何一件。

**危险**:
- 若"另起双图"（照 ARTEX 语义建第二个图存储/第二套节点边）: 直接违反 graph-driven-ops 的立律"账本图谱=渗透的操作系统……**无图外状态**"——第二张图就是图外状态;13 本账的单写者+哈希链管不到它,真值分裂,45 命令面作废一半;若再学它落 Postgres,零依赖律/纯 stdlib 单进程生态位（产品定义钉死）当场爆掉。
- 若"照抄 anchor 裸桥": ARTEX 自己的弱点（2-data-graph ③6: anchor 无来源/时间语义,溯源只做了任务侧一半）会被原样买进——而探隐 edges.tsv 本来就有 provenance 列,抄一个更差的。

**修正方向（架构裁决,动工前定死）**:
1. **单图两域**: 不建第二张图。把 assets.tsv 所在的资产域升格为"真值域"（跨战/项目级共享、canonical 键去重、归并语义——ARTEX 的 explicit/scope 双源归属+最长前缀归并**抄语义不抄实现**）,intents/facts/findings 留在过程域;账本仍是唯一真源。
2. **桥=第 11 边型 anchor,不走 cross_ref 逃生舱**: cross_ref 虽是任意向合法边（write_cmds.py:831-836）,但它在 graph_cmds._label_class 里归 **process 类**——锚点塞进去会进错边类、进不了覆盖/资产语义,且与 chain 相邻步 INT→INT 的既有用法互相污染。正确做法: 新增 anchor 边型,方向阵 {(facts,intents,findings)→(assets)},归 asset 类,provenance 列**必填 file:line+工件 sha256**（这一列探隐比 ARTEX 强,别浪费）。新增边类型的法定通道错误信息里已经写了: "新增边类型须 bump schema_version"（write_cmds.py:829）——走 schema bump+微版本勘误（41→44 先例）,同步改十边图着色钉测（25 测里 10-kind 两两互异是钉死的,漏改=绊线炸）。
3. **程序挂载=source-code 资产+parent 边**: 执法已在（check_cmds:380）。挂载键形: 程序工件用内容 sha256 做身份,派生 endpoint 资产 value=GT canonical 键形（endpoint-dict §三: svc-*/path?query 无端口形）——**车道A 的输出键形必须对齐 GT 键口径**,否则 b30/b36 域形错位教训（键形对不上白打）在白盒侧复刻。
4. **跨战资产真值域与单战哈希链的关系要在 v1.0a 一并裁决**（不然后面每一步都在欠）: 资产跨战共享后,"资产进战"用快照导入+链头锚定（链头锚定先例已有）,战内仍单写者。这是 v1.0b 项目向导的前置债,躲不掉。

### F2（致命·激励）"车道A 候选→点菜式深挖"把排序权、剪枝权、终止权一起交给了规划者——系统性跳卡不是风险,是这套激励的均衡态

**现象+证据**:
- GenSift 的警告原文（6-gensift §1.0 P4）: "**覆盖不可谈判、成本可谈判;一切效率机制只改顺序不改分母**";完成判据=unchecked=0 ∧ ext deferred=0;L1 单调性违例=exit 1 技能缺陷级中止。它的整个调度设计都在防一件事: 任何裁量主体（哪怕是无意的）把"分母"变成"愿做的部分"。
- 探隐现状: intents 状态枚举含 deferred（write_cmds.py:541）,进 deferred 只需要一句 reason（:548）;完成判定走九门/matrix-audit,**没有任何机制要求引擎卡闭合**;engine-fusion §2 给了 engine-hyp 配额 ≤40%（上限,防引擎挤占自主广度）——但**没有下限、没有保底、没有 aging**;结算只认 recall（E4 F6）,refuted（否证）不产生任何信用。
- 激励链推演: 规划者优化"预算内结算 recall"。深挖 band0 sink 卡=高成本、不确定性高;否证了=零信用;不开卡=deferred 合法、不扣分。理性策略=永远先摘高置信/廉价格,引擎硬卡全部烂在 deferred——**"不开卡就不会输**"。这不是规划者变坏,是你们给它的计分表教的。

**危险**: 覆盖不可谈判律（修正案 A 原文继承）在账本层面是真的（卡不蒸发）,在调度层面是假的（卡可以永远不被领取）。三个月后度量页会显示一个体面的 recall,和一万张 deferred 引擎卡——覆盖律变成覆盖话术。这正是 GenSift 用 stop hook+L1 单调性+完成计数拼命堵的那个洞,而 v1.0a 的设计只继承了它的词汇,没继承它的执法。

**修正方向（五件,缺一不可）**:
1. **分母封印**: 车道A 冻结 sink 卡清单（sha256 封印,GenSift phase0 0.6 同款）。规划者**只有排序权,没有剪枝权**;卡从池里消失只有两条路——终态（含 refuted/not_applicable）或机械级联（K 规则: confirmed 事实 awk join 批量消卡,护栏照抄 GenSift: band 高危不机械消/可逆/facts_used 回写）。
2. **双货币结算**: 闭合信用（卡到任何终态=格闭合,含否证）与召回信用（verified finding）分账。否则"否证=纯成本"的激励永远教人绕开硬卡。E4 F6 的字典序结算正好接得上。
3. **保底调度+aging**: 每 P3 轮在预算余量内强制派发 ≥N 张最老 pending 引擎卡（GenSift fw/term/ext 保底各 1 张的等价物）——这是 phases_engine 里的机械规则,不是规划者裁量。
4. **deferred 纳管**: deferred 必须带触发条件+到期重开（A7 处置七值+review_expiry 到期降级的同款语义）,配额封顶,**"engine deferred=0"写进 P4 收口判据**——否则"全覆盖"三个字不许出现在报告里。
5. **配额加下限**: engine-hyp ≤40% 保自主广度的同时,要求战终引擎卡闭合率≥地板,不达标=战标 degraded（b40 P3 degraded 先例）——诚实优先于好看。

### F3（严重·语义）车道A"确定性解析"的边界判据存在但不够硬,且三处技术地基比设计假设软

**现象+证据**:
- 判据的现存形态: 修正案 A 列了确定性件（OpenAPI→endpoints/params/auth;解包→清单→资产;pattern 扫描→路由/密钥/sink）;6-gensift §5.4 调和判决给了唯一一条硬线——"解析器输出含 verdict 语义字段=越线"。这条线是对的,但**只有一条线不构成边界**,大量交接物落在灰区（auth 分类、框架识别、死路由判断、密钥真伪、CVE 匹配、可达性),今天不预裁决,就会被施工者逐个顺手定掉。
- 软肋一（方言幻觉）: GenSift 509 条 pattern 是 **POSIX ERE,设计给 grep（leftmost-longest,无回溯）跑的**;探隐车道A 是 **Python re（回溯引擎）**——不支持 [[:alpha:]] 类 POSIX 字符类,却支持被 GenSift lint 明令禁止的 \b/\w/\d。6-gensift A1 说"95%——只剩搬",这个置信度虚高: 直搬要么语法报错要么语义漂移,且 Python re 的回溯特性把 ReDoS 风险一起搬进来（grep 无此问题）。
- 软肋二（stdlib 律正面冲突）: **Python stdlib 没有 yaml**。而 OpenAPI/Swagger 的主形态是 YAML。纯 stdlib 单进程（生态位钉死）与 YAML 解析只能活一个: 要么只收 JSON+外部转换,要么自写受限 YAML 子集解析器（确定性子集可行但工程量和误收风险都不小）,要么破例引依赖。产品文档对此零着墨。
- 软肋三（解包安全）: zip/tar/jar/apk 解包三敌——路径穿越（tarfile CVE-2007-4559 谱系,Python 3.9 的 extraction filter 是 opt-in 且需 3.9.17+）、符号链接/绝对路径、zip 炸弹（压缩比+总量）;外加 XML 实体膨胀（Swagger 可能是 XML 时代遗留）与 ReDoS。**且 Python 3.9 已 EOL**——安全平台钉死一个不再收安全补丁的解释器,是把自家地基立在已知漏洞带上。

**危险**: "确定性"是车道A 全部合法性的来源（它让覆盖律可以算术化、让产出可金样钉死）。三处软肋任何一处烂掉,确定性就退化为"大概率确定",覆盖分母跟着发霉;ReDoS/zip 炸弹则直接是操作员主机被打——解析器是你们新增的暴露面,不是旁观者（旁证: ARTEX live 意图 #73 把 :8900 tanyin 自己列为靶标,这生态里真有人在打你）。

**修正方向**:
1. **边界判据补成三律**: 无判定律（现存: 输出禁 verdict/severity/exploitability 字段;排序启发式允许,但只改顺序不改分母）+ **金样律**（确定性输出必须逐字节可金样——凡随模型/版本/温度变的归车道B）+ **失败律**（确定性失败=显式错误码+带披露跳过,永不猜测;LLM 失败=卡状态 candidate/blocked,两条失败通道不许互通）。
2. **六个灰区今天预裁决**: auth/guards 五段逐字转录+unauth/auth/unknown 三值=确定性✓（GenSift 枚举同款）;框架识别（pattern+unknown 回退）=确定性✓;pattern 命中定 class_id=确定性✓、"是否可利用"=车道B✗;硬编码密钥 pattern 命中=确定性✓、"真凭据 vs 测试夹具"（codex 的 disclosure-path 判据）=车道B✗;死路由/不可达=车道B（那是判定）,其结论作为否定性事实回灌=engine-static;OpenAPI 端点"实际部署/存活"=黑盒实证,不属于任何解析器。
3. **方言三选一裁决入修正案**: (a) pattern 走 grep 子进程（保方言,但 macOS BSD grep≠GNU grep,金样会机器相关）;(b) 翻译为 Python re 方言+把 GenSift fixtures 三件套门（pos/neg/noise）整体迁移进 CI 重新验活（保零依赖,推荐）;(c) 破例引第三方正则库（不推荐,生态位冲突）。选 (b) 就必须配 pattern-lint（禁灾难性回溯构造）+单文件扫描超时+输入长度帽。
4. **YAML 裁决同上入修正案**;解包上三帽（总解压字节/压缩比/条目数）+路径归一（拒绝绝对路径、..、符号链接）+子进程 RLIMIT（CPU/AS/FSIZE,macOS 可用 resource 模块）——这些判据 vuln-agent 资产里就有现成页（zip-bomb/redos-check,见【被忽视资产】6）;Python 版本升 3.11+/3.12（tarfile data filter 默认）列入季度决策。

### F4（严重·账本）sink/endpoint 的账位、矩阵扩法、partial/deferred 披露位——三个接口都没定,而"所有 sink 入矩阵"这句产品原话若被机械执行会造出语义错误的矩阵

**现象+证据**:
- 代码现状: matrix.tsv 列=attack_surface×vuln_class×{state,reason,intent_id,frozen_at};行键=资产 value×WSTG 词表类（matrix_init）;状态集 {x,?,-,!}（write_cmds.py:1031）,**无 deferred/partial 胞态**;submatrix: 铸造四条件支持冻结后新表面（:1037-1058）=两本账的机械实现已在库;intents kind 枚举={recon,surface,matrix-test,deep-dive,authz-diff,nday-verify}（:103,**无 engine-hyp**,engine-fusion §6-2 确未施工）;facts.tsv 必填 intent_id 外键——与"车道A 先于任何意图运行"相抵触;intents 状态含 deferred、**无 partial**（GenSift partial=两次派发失败,6-gensift §5.5 风险 2 已点名,至今无对应位）。
- 语义错位: sink 是代码位置（file:line+pattern_id）,只属于一个漏洞类;矩阵行键是资产 value×12 类全集。sink 入矩阵=sink×12 类的稀疏行×万级 sink——TSV 塞得下,但**矩阵的 GT 对齐性就毁了**（评分器按 svc-*/path GT 键 join,代码键混进来后覆盖账与结算账搅成一团）。

**危险**: 这是 v1.0a 最容易"实现时随手定"的部位。定错的方向有两个: 把 sink 硬塞 matrix.tsv（污染结算分母）,或让 sink 只活在引擎内存/导出文件里（覆盖律失守、不进账本审计）——两个都比"不定"更糟,因为都带着"已实现"的妆容。

**修正方向（逐项裁决）**:
1. **endpoint → assets.tsv**（type=endpoint,value=GT canonical 键,parent 边挂服务/source-code 资产）——matrix-init/from-assets **零改动**消费,submatrix 承接晚到的车道A 产出（冻结后铸行,两本账: 冻结分母 vs 追加分母分开披露——B5 判据的机械落点就是它,吸收判决没认领,这里替它认领）。
2. **sink → facts.tsv（kind=engine-static,带 file:line 出处+pattern 版本）**;intent_id 冲突二选一: 铸造"engine-run 虚拟意图"做外键宿主（推荐,可追溯每轮解析批次）,或 schema 勘误放宽。**sink 深挖卡 → intents.tsv（kind=engine-hyp,走勘误加入枚举;dedup_key=sink 稳定指纹=path+行内容哈希+class,不含行号——A3 判决,防位置平移换 ID）**。
3. **矩阵只扩"证据来源位",不加行**: cell 的 reason 前缀词表（既有先例 submatrix:/authz-diff:）扩 engine:<pattern版本> 与 deferred:INT-N 两个前缀;胞态维持四值不动。产品原话"sink 入矩阵"应出一条勘误,解释为"endpoint 行获源码证据位+sink 卡两本账闭合率披露"——**否则一定会被实现成 sink×12 类矩阵**。
4. **partial 补进 intents 状态枚举**（attempt≥2 派发失败,GenSift 同义）,deferred 已有但语义对齐（GenSift deferred=仅追加卡、证据需运行时/带外——探隐 intents 的 deferred 更宽,须在 engine-hyp 上收紧为"仅 engine-hyp 可 deferred+必带重开条件"）;披露位三件: P4/report_lint 断言（terminal_b 披露先例）、度量页覆盖债面板（deferred/partial 计数按 reason 分桶）、settle 结算**永不**给 deferred 胞记分。

### F5（中·安全）codex 沙箱六层对车道A"解析不可信输入"的适用性: 三成可抄,七成错位——错位的七成有更正确的落位

**现象+证据**:
- codex 六层（7-codex §2）: Docker(uid/cap/nnp)→seccomp allowlist（封 AF_ALG/AF_VSOCK）→AppArmor→Codex 原生 Bubblewrap（worker 级 read-only+断网）→entrypoint 卫生→提示词层（userContext 一律 untrusted、禁 fetch URL）。这套东西的威胁模型是"**在 Linux 容器里执行模型指挥的命令**"。
- 车道A 的威胁模型是"**在操作员 macOS 单进程里解析攻击者控制的工件**"（不执行目标代码）。两者交集比直觉小得多: seccomp/AppArmor/Bubblewrap 三层是 Linux 内核/容器栈,macOS 无原生等价,纯 stdlib 律下连 sandbox-exec 都是二进制依赖;Docker 层在 macOS 上是 VM,套进去违反"clone 即用零依赖"。
- 真正可抄的是**范式**而不是层: permission-profile-preflight 的"**配置→预检→才放行**"（用真实 codex 二进制验证 profile 生效,7-codex §2.8;探隐版=解析器开工前用金丝雀工件验证三帽/路径隔离真的拦得住,fail-closed）;userContext untrusted 的提示词层（车道A 输出流入规划者/战士上下文时**当数据不当指令**——endpoint 名/报错文本/源码注释都是攻击者可控字符串,GenSift 反叙事框定"注释是注入样本"同源,两判决在这一点already汇合）。
- codex 六层没覆盖、恰是车道A 主敌的: zip/tar 炸弹、路径穿越、符号链接、XML 实体膨胀、**ReDoS**（见 F3——尤其 pattern 从 grep 迁到 Python re 之后这个风险是新增的）。

**危险**: 把 5.2 判决（"沙箱三层件直接偷",置信 93%）误读成"车道A 也要上容器沙箱"——工程量爆炸+平台定位冲突+真正的解析威胁一个没堵。反过来,若因为"我们不执行代码"而完全不做,操作员主机就裸露在恶意工件面前（渗透平台打授权目标,授权目标没义务善意打包）。

**修正方向**: 车道A 沙箱=**纯 Python 可执行的四件**: 子进程隔离+RLIMIT 三限（CPU/AS/FSIZE）、解包三帽+路径归一（F3）、单文件超时看门狗、输出卫生（车道A 产物入 LLM 上下文前的注入清洗/引号包裹+ID 白名单信封——A4 判决的盲结构顺带覆盖这层）。codex 六层的正确落位维持 7-codex 5.2 原判: **T2/T3 战士执行档**（真执行不可信载荷时）——那是它威胁模型吻合的地方,判决已写对,别挪用。

### F6（中·实验）与 E4 的衔接: 白盒 A/B 若不先吃下 E4 的全部修正,它将成为"用错尺错杀自己"的第一个受害者——被杀的恰是刚批的车道B

**现象+证据**:
- E4 已证的尺病: 56 题双峰饱和（13 题全 miss 死区/约 20 题送分/判别带仅约 22 题）;并集池化 McNemar 在 n=5 下最小可判不一致比约 2.6:1;对照组纯度靠自报且 b40 实锤跨战泄漏;GT 56 题全为单请求 marker、零业务链。
- 白盒实验的独特弱点叠加: ①死区 13 题的三大归因（凭据链/载荷形态/结构投放点——b40 honest_misses）**恰好全是源码可答的**,即白盒的真实效应住在"post_auth 层死区救回"里——全量池化会把效应稀释进送分区,F3 的剧本（p=0.25→"白盒无增益"→砍车道B）就是照着这个结构写的;②F2 污染对白盒是加倍的: 靶场源码就在 tests/range/ 与本仓同盘,对照臂"没喂但可以自己拿"=效应系统性低估,两臂都读=测噪声;③引擎是异步侧轨（小时级）,战的自然边界本来就在溶解（E4 F5）,不冻结引擎快照则"处置"是个演化中的话术。
- 正面机会同样明确: 死区 14 题逐题判"源码可答/不可答"是**零战成本**的先手（13 战 per-GT missing 明细+归因都在盘上）,它同时决定车道A pattern 语料的工程优先级与实验样本量——E4 三问之一已经替你们问了这个。

**修正方向**:
1. **预登记硬门（开战前完成,否则实验不开打）**: GT-free/源码-deny 战士工作区+路径哨兵机检（两臂同执法）+实验窗口禁读前战账本;主指标=post_auth 层 recall,次指标=全量;检验=战层配对置换（每臂 N≥4 预登记）,McNemar 降描述;处置物=车道A pattern 版本+intent 集+引擎快照三 sha256 入 treatment_artifact（E4 F4 扩字段）。
2. **sim 注入（7 真 3 假）按独立实验类型登记**（单臂 pass/fail 精度门,不是 A/B）——别再让 question 散文硬塞。
3. **GT-T2 链路轨与 GenSift INV 语料孪生共建**: 业务逻辑链靶的作者同时写该场景的 INV 不变式（五字段: 前提/可 grep 违反形态/来源/阴性边界/复核态）——GT-T2 的终态断言与 INV 的违反判据是同一次知识劳动的两个投影。分开建=车道B 在业务逻辑维度零可测面,GT-T2 沦为纯黑盒尺（GenSift C6 判决"语料等真实目标域出现再建"的触发条件,现在到了）。
4. **每次吸收引擎/语料变更先跑改名靶前测**（E4 F1 轨 3）——车道A 字典/pattern 是活知识体,教考合一的 Goodhart 推力比字典代际回灌更陡。
5. 白盒车道实验单元=episode 五件套（目标 gen+任务书 hash+预算包+知识库快照+**引擎/规划者快照**）——E4 F5 的方案对异步侧轨刚好够用。

---

## 【被忽视的既有资产】

1. **submatrix: 铸造四条件+冻结后新表面**（write_cmds.py:1037-1058）——"两本账"（冻结分母 vs 追加分母）的机械实现已在库并带执法（防主矩阵偷扩张）。6-gensift B5 判决讲了两本账纪律,没发现账本里已经有这台机器;v1.0a 晚到端点的承接直接用它。
2. **assets type=source-code（A6）+check_cmds:380 parent 边强制+matrix TYPE_VOCAB_CLASSES 已映射 4 类**——"程序挂载"的账位地基三件齐,双图一桥设计输入未引用任何一件。蓝图巡检律在自家最新提案上违律,这是实锤。
3. **edges.tsv 自带 provenance 列**——锚点桥可以做到比 ARTEX 裸两列强（file:line+工件 sha256),差的只是第 11 边型一次 schema bump（错误信息里已写明法定通道）。
4. **graph-horizon（可达集×矩阵空格 join,graph_cmds.py）**——D5"源码情报直喂派发排序"的接口现成: sink 卡入池后 horizon 直接消费,不用新造调度入口。
5. **endpoint-dict §三 GT 键口径**（svc-*/path?query 无端口 canonical 形）——车道A OpenAPI→endpoint 输出键形的唯一成文对齐目标。不对齐=白盒情报进不了矩阵结算（b30/b36 键形错位教训的下一个受害者就是它）。
6. **vuln-agent 判据库 docs/design/imported/vuln-agent/.../vuln_rules/**（zip-bomb/redos-check/tmp-privesc/port-binding-check 等 20+ 页）——车道A 解析器自身安全的现成检查单（F3/F5 的三帽/超时/路径归一判据,这个库里已有成文版本）,评审未见任何人引用。
7. **处置七值+review_expiry 到期降级（A7）与 sink 稳定指纹（A3）**——deferred 纳管（F2-4）的语义先例与跨 run 身份地基,判决在册,账位设计未接。
8. **zhulong_export / findings 指纹通道**——白盒产物对外互通（/api/imports）的出口已建,车道A/B 结论若要喂 ZhuLong 生态,不用新协议。

---

## 【三问给主会话】

1. **桥到底裁不裁"第 11 边型 anchor（带 provenance,归 asset 类）"?** 若裁,schema bump+十边图 25 测着色同步+graph_cmds 边类归置的工程账谁来付、何时付;若不裁,引擎 fact/intent 锚定资产今天只有 cross_ref 逃生舱一条路——进 process 边类、进不了资产语义,这不是设计口味,是写进去就错。顺带: D5（源码定位=渗透内环）这个裁决为什么还活在口头,不落产品文档?口头宪法在 v1.0a 这种多接口批次里等于没有宪法。
2. **车道A 的确定性三软肋（ERE 方言/YAML 缺位/解包+ReDoS 安全）敢不敢先出一页裁决再动工?** 特别是纯 stdlib 律与 OpenAPI-YAML 主形态只能活一个——这是修正案级别的取舍（生态位 vs 输入覆盖）,拖到施工时会被某个实现者用 import yaml 一行代码悄悄替你们决定,然后零依赖律从宪法变成备忘录。
3. **引擎卡的调度,你们发给规划者的到底是"排序权"还是"排序+终止+剪枝权"?** 若 deferred 不进 P4 收口判据、否证不记闭合信用、每轮没有保底派发——你们就是在用计分表教它"不开卡就不会输",GenSift 拿 stop hook+L1 单调性+完成计数死守的分母,会在探隐被三个可选参数悄悄卖掉。敢不敢把"engine deferred=0 才许称全覆盖"写进 P4 门,把"否证=格闭合信用"写进结算?

（评审纪律声明: 对靶项目全程只读零 git;唯一写入=本文件。文中代码行号取自评审当日实读。）

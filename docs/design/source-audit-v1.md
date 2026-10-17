# 源码审计 v1 设计稿 —— 源码账本谱图 + 渗透联动（source-audit-v1）

> 设计舰出品 · 2026-10-19 · 零代码实施（本稿只设计不动工）
> 缘起（用户方向原话）: 「集合 vuln-agent,gensift,codexsecurity 等基础上参考我们自己的实现和参考 ARTEX 的双图思路,构建我们自己的;如我们构建源码的账本谱图?或者和渗透的结合?」——**现在是渗透优先,源码审计=已定方向待设计**。
> 定位律: 渗透是主航道,源码审计是①渗透的内环情报车道（W4 白盒双车道,已在册）+②独立交付形态（W7+ 本稿新增量）。本稿答五问: 谱图是什么/怎么联动/执行形态/对 cyber-audit 逐件对照/分波次落地。
> 前置继承: 本稿不推翻任何在册裁决——06-whitebox-dualgraph 评审 F1-F6（单图两域/锚点即边/引擎卡激励/矩阵扩法/沙箱落位/实验衔接）全部继承并在其上做源码审计专属裁决;修正案 A（白盒=渗透内环+审计模式开关,docs/design/tanyin-product-v1.md:38）是本稿上位法。

## 〇 输入实读清单（六项必读,全部实读,只读零写）

| # | 输入 | 实读证据 | 形态一句话 |
|---|---|---|---|
| ① | engines/vuln-agent（仓内） | adapter.py 全文+MANIFEST 十二字段 | 八段管道源码分析引擎（攻击面→拆分→排序→业务流→漏洞规划→分析→对抗复核→后处理）,POC 四要素门（raw_request/raw_response/时间/环境,缺一降级 fact 不成 finding）,引擎不写账本 |
| ② | cyber-harness cmd/audit（.research/repos/cyber-harness/cmd/audit） | README 全文+skills/{workflow,report,tools}.md+app/report.go/validate.go 函数面+行数实测 | 模型主导源码/二进制审计成品: Go 单二进制 ~1082 行产品码（main 26+app 329+profile 230+report 375+validate 48+extension 74）,工具面 rg/ast-grep/osv-scanner/proton+可选 r2/capa/floss,证据契约 run.json+session.jsonl+coverage.json+findings.json+OKF index.md,validate 回喂 ≤2 修复轮 |
| ③ | GenCPT（/Users/wgen/Sectest/GenCPT,只读） | skills/{cross-ref,docker-compliance,containerd-compliance}/SKILL.md+docs/gencpt-detection-principles.md | 容器栈渗透套件: 226 条 CIS 规则（K8s 134+Docker 64+Containerd 28）+49 攻击模式+185 假设卡,knowledge_graph/{nodes,edges} JSON 图谱,cross-ref 三查询（XREF-001 违规→攻击前置/XREF-002 叠加放大/XREF-003 前置vs侦察）,WU 分批防上下文压缩,禁悬空边 |
| ④ | ARTEX 双图（/Users/wgen/dsh-test/repos/ARTEX,只读） | agent/planner.go:19-21 实读+docs/research/artex-deep-dive/2-data-graph.md | 事件驱动规划者: 「每次资产图或探索图变化（防抖）→读探索路由→查资产→判目标→派 0..N 意图」;探索图 7 kind×state 矩阵+5 rel 边,资产图单表多态跨任务共享,anchor 桥表(node_id,asset_id)裸两列只留 lineage |
| ⑤ | 账本 13 表+deepex 先例（仓内） | contracts/01-ledger-schema.md+write_cmds.py:104-131+engines/deepex/derive.py | 13 表/10 边/_EDGE_DIR 代码级方向执法;intents kind 六值{recon,surface,matrix-test,deep-dive,authz-diff,nday-verify};deepex=读取类发现→凭据检查意图卡（kind=deep-dive,engine=deepex-cred,egress=forbidden,密值全域脱敏）+RCE→取证包三连——**派生层的同型先例** |
| ⑥ | gensift/codexsecurity | web_search+本地快照 | **codex-security=公开仓 github.com/openai/codex-security**（npm @openai/codex-security,现 0.3.0;本地分析快照 v0.1.95: TS ~25.8 万行,deep-scan coordinator 1311 行,七道防假阳闸,六层沙箱）;**GenSift=无公开仓（私有资产 Wgen1995/GenSift,~/.claude/skills/gensift 活用版在盘）**——形态按 docs/research/liveui/6-gensift.md 全量分析记账,源码本体**待取**（用户自有,取用零障碍,取前按分析档口径） |

---

## 一 【必答 A】源码账本谱图 = 什么

### 1.1 一句话定义

**源码账本谱图 = 三层结构的代码知识体**: 账本锚点层（13 表内,只入有执法语义的代码事实）→ 谱图工件层（submissions 工件,全量符号/调用/数据流,确定性可重建）→ 投影层（SQLite/图查询,坏了删了从下层重建）。**不建第二张图**（06-whitebox F1 裁决继承: 账本图谱=渗透的操作系统,无图外状态）。

### 1.2 代码事实分级账位表（核心裁决——哪些入账,哪些入图）

| 级 | 代码事实 | 账位 | 纪律 | 密度预估（10 万行典型仓） |
|---|---|---|---|---|
| L0 | 文件/清单/组件/依赖（OpenAPI/解包清单/pom/go.mod） | assets.tsv（type=source-code 已在枚举 write_cmds.py:781;endpoint 用 GT canonical 键 svc-*） | 确定性枚举,金样律;parent 边挂载执法已有（check_cmds.py:380） | 十~百行 |
| L1 | 路由/端点/入口/框架识别/guards 五段 | assets（endpoint）+facts（kind=engine-static,带 file:line+pattern 版本） | 无判定律（禁 verdict 字段）;auth 三值 unauth/auth/unknown=确定性✓（06-whitebox F3 六灰区预裁决继承） | 百~千行 |
| L2 | 函数/符号/调用边/包含关系 | **不入 13 表**——谱图工件 codegraph.jsonl（NDJSON: 符号表+调用边,每条带 file:line+符号签名哈希）;账本只记一条 digest 事实（kind=engine-static 子类=codegraph-digest: 符号数/边数/sha256/解析器版本） | 确定性产物同输入逐字节同输出;引擎不写账本,总控验收后落 digest | 工件 ~10-40MB;账本 1 行 |
| L3 | 数据流/污点候选/sink 卡 | intents.tsv（kind=engine-hyp 深挖卡,走勘误入枚举——06-whitebox F4-2）+终态结论回写 facts（confirmed/refuted 带 confidence） | 假设不是真值,不进资产域;dedup_key=污点指纹（path+行内容哈希+class,不含行号,防位置平移换 ID） | 百~千卡 |
| L3' | 硬编码密钥候选 | facts（pattern 命中=确定性）+真伪判定（真凭据 vs 测试夹具）=车道B/人工 | 密值不入账（vault 律）;deepex 同型脱敏 | 十~百行 |
| 锚 | fact/intent/finding ↔ asset | edges.tsv **第 11 边型 anchor**（方向阵 {facts,intents,findings}→assets,归 asset 类,provenance 必填 file:line+工件 sha256——比 ARTEX 裸两列桥强,F1-2 裁决继承,走 schema bump+微版本勘误,W4 已在册） | 锚点即桥;覆盖度=scope 分母÷锚定分子（ARTEX covTargetCTE 语义,我们用账本 join 实现） | 随 L1/L3 |

**密度律（口诀）: 文件入账、入口入账、符号入谱（工件）、调用入谱（工件）、污点入卡（意图）、结论回账。**
分界判据一句话: **「无执法语义不入账」**——凡不需要审批/授权/覆盖/发现/状态机判断的代码知识（函数签名、调用边）只入工件层;账本 13 表是执法面不是知识面。这条律防的是: 万级符号行炸 TSV+哈希链（追加 3400 行/s 基线被谱图灌死）、矩阵 GT 键形被代码键污染（06-whitebox F4 的「sink×12 类矩阵」事故形态）。

### 1.3 为什么不照抄 ARTEX 双图（对照表）

| 维 | ARTEX | 我们 | 判 |
|---|---|---|---|
| 存储 | Postgres 45 表,exploration_nodes 7 kind+5 rel+anchor 桥表 | 13 表 TSV+哈希链+edges 10 边型（→11 加 anchor） | 我们防篡改/单写者/可第三方验真——ARTEX 零哈希链（artex-deep-dive ③1 自认） |
| 过程/真值分域 | 探索图（过程）+资产图（真值）两张图+桥 | **单图两域**: intents/facts/findings=过程域,assets=真值域,同一张账本图谱 | 我们无图外状态;ARTEX 桥无 provenance/时间语义 |
| 谱图密度 | 节点全进 DB（activity 无校验纯流水） | 分级账位（§1.2）: 执法语义入账,导航语义入工件 | 我们账本可结算（矩阵/评测）;ARTEX 覆盖度 CTE 值得抄语义 |
| 事件源 | 图变化→防抖→planner（planner.go:19-21） | **账本行追加=事件**（timeline epoch 机制已在） | 同型;我们事件可回放可验真（实时=回放特例,graph-realtime-v1 已裁） |

---

## 二 【必答 B】与渗透怎么联动（deepex 型双向派生）

### 2.1 设计基线: 派生=机械规则,不是 LLM 裁量

deepex 先例（engines/deepex/derive.py）的三件纪律全部继承: ①意图卡结构化带约束（egress/密值脱敏）②引擎不写账本（产物=artifacts/derived-*.json,总控验收后落 intents）③dedup 去重（同源只派一次）。源码侧扩展为**双向**:

### 2.2 正向: 代码发现 → 渗透意图（deepex-code 规则表）

| 代码事实（facts kind=engine-static） | 派生渗透意图卡 | kind/engine | 约束 |
|---|---|---|---|
| sink 类: sql-injection/xss/cmd-exec/ssrf/deser/path-traversal | 渗透验证卡（带 file:line 锚+参数形+入口端点关联,标题「源码指向·X 类验证@端点」） | kind=deep-dive / engine=deepex-code | egress=goal 域（渗透卡本就要打,但**须过 scope 硬门**——端点必须在 include 内,界外=标 out_of_scope 不派,账本级禁止已有）;network_position 标 code-informed |
| 硬编码凭据候选 | 凭据检查卡（与既有 deepex-cred 完全同型,origin=code） | kind=deep-dive / engine=deepex-cred | 本地三查,不外发 |
| endpoint auth=unauth 高危面 | surface 意图（矩阵补格） | kind=surface / engine=deepex-code | 矩阵只加证据位不加行（F4-3 继承） |
| 上传/反序列化/文件写 sink | 深挖卡喂规划者排序（graph-horizon 消费,06-whitebox 被忽视资产④） | kind=engine-hyp | 排序权给,剪枝权不给（F2 继承: 分母封印+保底派发+deferred 纳管） |

### 2.3 反向: 渗透事实 → 代码复核（黑盒异常白盒定性）

渗透 finding/事实触发代码复核意图: 黑盒发现（如 IDOR 候选/参数异常 500/越权迹象）→ 派 intent kind=engine-hyp origin=pentest-fact,detail=「黑盒异常待白盒定性: <finding 摘要>」,锚 anchor 边到 source-code 资产,车道B 接卡（sink 卡五步证伪流程复用）。**这一向是 cyber-audit/GenSift/codex 都没有的**——它们没有活的黑盒战线;我们有渗透主线,黑白互证才是「和渗透的结合」的真正答案。

### 2.4 事件源=账本行（与 ARTEX 同型,更硬）

- ARTEX: 图变化→防抖 800ms→planner 读态势（planner.go:19-21,engine.go:800-913）。
- 我们: timeline 行追加=事件（epoch 增量推送已在 graph-realtime-v1 落法）→ 派生器（deepex 规则表）+规划者（W5 常驻）双消费。差异: ARTEX 事件=内存 notify 通道（丢了就丢）;我们事件=账本行本身,**回放可重算派生**（实时=回放的特例律直接适用——派生器跑两遍结果一致,可金样钉死）。
- 触发词汇（入 timeline 事件 kind 建议）: code-fact-added（正向派生源）/finding-added（反向复核源）/codegraph-digested（工件就绪）。

---

## 三 【必答 C】审计执行形态（独立任务型 vs 渗透内嵌型;W7 客户/项目实体）

### 3.1 裁决: 同一引擎双模式,内嵌先行,独立型 W7 起独立立项

修正案 A 已裁「架构=B（渗透内环）+审计模式开关: 同一引擎 battle/audit 双模式（scope=仓库/egress 全封/零网络,出口换审计专报）,翻案条件=纯代码审计合同占比>30% 则审计模式升格一级入口」。本稿落细则:

| 维 | 内嵌型（W4 白盒车道,在册） | 独立审计任务型（W7+ 本稿新增,SA-1） |
|---|---|---|
| 载体 | battle 内白盒车道（goal=渗透目标,源码=情报输入） | audit-goal（goal.target=源码工件 路径+sha256;授权八问照答——审计合同也是授权载体,NDA/范围=仓库清单） |
| scope | 源码仅情报,打点仍受渗透 scope | scope.matcher=仓库路径/文件 glob;**egress=forbidden 全封**;guard_tier=T1;战士纪律 L1 只读;network_position=same-host 恒定 |
| 覆盖律 | 渗透矩阵为主,源码卡两本账披露（F4-3） | **审计覆盖=谱图分母**: endpoint/sink 全集 sha256 封印（GenSift phase0.6 同款）,每卡终态必达,engine deferred=0 进 P4 收口 |
| 出口 | 渗透报告（源码贡献单独计数,McNemar 判增益——E4 修正继承） | 审计专报: SARIF 2.1.0（已落 c96db82）+OKF 式摘要+PDF,走 T4-P7 报告中心 render/rerender 管线,双人签发位照用 |
| 引擎 | 车道A 解析器（确定性）+车道B 证伪卡（LLM）——vuln-agent 旧适配器摘档归档（04P0 已排） | 同一引擎面+cyber-audit 工具卡三件（SA-3） |

### 3.2 W7 客户/项目实体关系（13 表口径不动）

- **实体分层**: 客户（customer）/项目（project）=**安装级 registry**（$TANYIN_HOME/registry/{customers,projects}.tsv,单写者 CLI,纯追加+amendment 同律）,**不进 13 战表**——13 表是战级真相,客户/项目是跨战归属;债不混。
- **关联**: goals.tsv 勘误可选列 project_ref（微版本通道,schema_version 不递增先例）;project 行持 customer_ref+源码工件登记（路径+sha256+授权书引用——审计合同的授权结构化复用 goals 授权五件套）。
- **资产真值域**: 跨战共享（06-whitebox F1-4: 快照导入+链头锚定,战内仍单写者）——同一客户多战/多审计共用资产与谱图工件,「资产进战」=快照,不重复解析。
- **聚合视图**: 报告中心按 project 聚合多战发现（W7 项目页已在 10-五产品逐件基线总表:15 排期「W7 客户·项目实体」）。
- 状态机: 审计任务复用 task-lifecycle-v1 十二态+迁移门卫（每迁移=账本事件,结算挂链完整——裁定案#11 已追认）。

---

## 四 【必答 D】与 cyber-audit 逐件对照（我们超什么/借什么）

| # | 件 | cyber-audit（实读） | 我们（现状/在册） | 判 |
|---|---|---|---|---|
| 1 | 入口形态 | 单二进制 CLI: init/run/doctor/validate/tools install,--resume 续跑 | battle auto 一键链+serve 收口（W1/W2 已落）;SA-1 加 audit-goal | 借: doctor 只读体检（不建目录零下载）+validate 独立子命令（免模型可跑,审计报告外部可验） |
| 2 | 工具面 | rg 15.2.0/ast-grep 0.45.3/osv-scanner 2.6.0/proton 内置;可选 r2/capa/floss;Arsenal 版本钉死+预检修复 | 工具卡 25 张+tools.lock 供应链锁定（sha256+ECDSA 验签,单源复用） | **超**（卡带七纪律字段/限速/黑名单覆盖/revert 义务）;借: **三件套选型直接进 SA-3 工具卡**（rg/ast-grep/osv-scanner——选型已被成品验证） |
| 3 | 证据契约 | run.json（scope/git 元数据/工具版本/状态）+session.jsonl+raw/+evidence/+log.md;报告目录永不覆写 | 13 表哈希链+evidence 卡四要素+timeline 链式+submissions 单写者 | **超**（防篡改/第三方可验——它零哈希）;借: run.json 的 git root/subdir/tracked 数/revision 元数据面（审计溯源披露） |
| 4 | 覆盖诚实 | coverage.json 六数组（examined/excluded/unsupported/unresolved/checks）+「空发现≠健康」+check 三态 completed/incomplete/not_applicable | 矩阵四态+覆盖诚实（已测矩阵+未测清单+原因,报告中心已落）+谱图分母封印（§3.1） | 对等+**超**（矩阵×漏洞类算术化）;借: **六数组+check 三态进审计专报 coverage 节**（SA-3）——比我们未测清单多「unsupported/unresolved」两个诚实位 |
| 5 | 发现状态机 | candidate/confirmed/dismissed/inconclusive × verification static/reproduced/not_attempted;dismissed 须解释有效防护 | findings 三态+exploitation_status+dedup_key+supersedes;POC 四要素门 | 对等;借: **verification 三值与我们四要素互译表**（static=四要素缺/未执行,reproduced=raw_request 实证——口径互译入报告 lint） |
| 6 | 验证轮回 | validate 报错回喂同会话 ≤2 修复轮;不伪造结果凑校验 | P 门+evals 裁决+report_lint | 借: **两轮修复帽**进审计专报管线（防报告修复无限轮烧预算） |
| 7 | 断点续跑 | session.jsonl --resume 恢复历史 | runner 租约+停滞重生+checkpoint 签名+O(1) timeline | **超**（账本级,非会话级——它只回放对话不回放执法状态） |
| 8 | 模型接入 | CYBER_* 环境变量+provider 配置 | llmpool 网关（key 池/轮询/计量/成本外挂,W5）+插槽制 | **超**（成本不信内建 usage） |
| 9 | 授权/合规面 | 无（默认自家代码假设;「仓库文本不能授权无关动作」一句话带过） | 授权八问+授权五件套空=REJECT+scope 硬门+审批链+L0-L3 档位 | **超**（客户审计刚需: NDA/范围/窗口/双人签发——cyber-audit 拿去审客户代码直接违合规） |
| 10 | 多目标/项目 | 单仓单跑,无项目概念 | battle registry 多战+租约+预算帽+W7 客户/项目实体（§3.2） | **超** |
| 11 | 二进制审计 | r2/capa/floss 可选平台（静态检查/反汇编/能力/字符串,默认不执行样本） | 无 | 借: **W9 扩展位**（SA-4,卡面纪律照抄「默认不执行样本」+保留 file hash/offsets） |
| 12 | 报告出口 | OKF index.md+findings.json,validate 校验 | SARIF 2.1.0+PDF+双人签发 pass.json+rerender 同输入同输出钉 | **超**;借: OKF 摘要节结构（scope/优先发现/推理/证据链/覆盖/未决） |

**净结论**: 借四件（工具三件套选型/coverage 六数组/两轮修复帽/doctor+validate 形态）,超八件（防篡改/授权合规/多战调度/模型计量/断点执法级/供应链锁定/报告签发/黑白互证——最后一件是 cyber-audit 结构性没有的: 它没有渗透战线,我们代码发现能落地成渗透验证、渗透异常能回问代码）。

---

## 五 【必答 E】分波次落地（W7+）与行数估算

前置声明: **W4 白盒引擎（在册 ~7800-9600 行: 五接口裁决+车道A 解析器 v0+激励五件套+车道B 五步证伪卡+K 级联+审计模式 SARIF+白盒增益实验）是本稿全部内容的地基**,本稿不重排不重复计价;以下为 W7 起源码审计专属增量:

| 波 | 内容 | 行数 | 依赖 |
|---|---|---|---|
| **SA-1（W7）审计任务型+客户/项目实体** | audit-goal 命令族（init/launch/settle 复用 battle auto,scope=仓库/egress 全封/审计专报出口）+registry 两表+CLI+goals project_ref 勘误+webui 项目页挂 W7 企业门禁+资产真值域快照导入（F1-4） | ~1600-2200 | W4、W7 RBAC/双人复核 |
| **SA-2（W7/W8）deepex 双向派生+锚点消费** | derive-code 规则表（§2.2 四类正向）+pentest→code 复核卡（§2.3）+事件词汇三枚+图谱页锚点/谱图 digest 渲染 | ~500-800 | W4 anchor 边型、W5 常驻规划者（无它则派生=收卡时惰性触发,先行情愿降级） |
| **SA-3（W8）cyber-audit 对照吸收** | 工具卡三张（rg/ast-grep/osv-scanner,卡面纪律全带）+coverage 六数组投影+check 三态+findings verification 互译进 report_lint+validate 独立子命令+两轮修复帽+doctor 只读体检 | ~600-900 | SA-1 专报出口 |
| **SA-4（W9·可选）二进制+合规基线** | r2/capa/floss 三卡（默认不执行样本律）+GenCPT 型合规审计: 规则库（226 条起步可换套件）→假设卡→cross-ref 图谱关联（XREF 三查询语义抄,节点=资产/fact,边=anchor/cross_ref,禁悬空边） | ~900-1400 | SA-3 工具卡管线 |
| **合计** | | **~3600-5300 行**（W4 之外新增量） | |

触发判据（修正案 A 翻案条件落表）: 纯代码审计合同占比>30% → SA-1 提前并升一级入口（产品导航加「审计中心」）;占比<10% → SA-4 永久搁置也不违约。

---

## 六 风险与待裁位（呈用户,随裁定案#15）

| # | 待裁 | 选项与推荐 |
|---|---|---|
| 1 | 谱图工件层的磁盘预算 | 工件随 submissions 留存（可回放）vs 终态后归档压缩（tar+sha256,ARTEX task_archives 同型）。**推荐: 默认留存+超 500MB 项目手动归档**——审计域工件就是证据,不轻删 |
| 2 | audit-goal 的授权八问口径 | 审计合同授权书=NDA+范围清单（无测试窗口/速率概念）→ 八问哪些必答需勘误。**推荐: valid_from/until+auth_sha256 必答,rate_limit/window 缺省 N/A** |
| 3 | 车道A 方言三选一（06-whitebox F3-3 遗留,O6 关联） | (b) 翻译 Python re+fixtures 迁 CI（评审推荐）维持——源码审计同吃此裁,**不另起炉灶** |
| 4 | GenSift 源码取用 | 本地活用版=用户自有资产,SA-2/SA-3 施工前建议把 patterns/59 件+fixtures 三件套正式取入仓内 knowledge/staging 走入库管线（staging→lint→approve→commit）,**待用户放行** |

## 七 与在册裁决的继承对照（防翻案自查）

| 在册裁决 | 本稿关系 |
|---|---|
| 06-whitebox F1 单图两域/anchor 第 11 边 | 全文继承（§1.1/§1.2 锚行）,不建第二张图 |
| 06-whitebox F2 激励五件套（分母封印/双货币/保底/deferred 纳管/配额下限） | §2.2 最后一行+§3.1 覆盖律继承 |
| 06-whitebox F4 sink→facts/engine-hyp→intents/矩阵只加证据位 | §1.2 L2/L3 账位直接引用 |
| 修正案 A 白盒=渗透内环+审计模式开关+翻案条件 | §3.1 上位法,§五 触发判据落表 |
| 裁定案#10 实时三件（实时=回放特例） | §2.4 派生可重算引同律 |
| 裁定案#11 任务生命周期 12 态 | §3.2 审计任务复用 |
| 裁定案#14 威胁建模岗 | 互补不重叠: 威胁建模=目标→假设树喂规划者（渗透向）,本稿=代码→意图卡（白盒向）;SA-2 派生规则表预留 threat-hyp 来源位,两岗共用意图池 |
| O7 SQLite 投影升格 | §1.1 投影层同律（坏了删了从账本+工件重建） |

（设计舰只读本仓+外部仓,零 git 写,零兄弟舰文件触碰;唯一写入=本文件+RATIFICATIONS #15 行+HANDOFF 一行。）

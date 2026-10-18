# 白盒源码审计·三参考综合分析（VulnClaw / GenSift / Codex Security）

> 研究舰出品 · 2026-10-20 · **只分析不设计**——设计裁决须用户走头脑风暴流程批，本稿零设计零施工。
> 任务：三参考现状（VulnClaw 已析 D 舰 60 件档／GenSift 半析本地仓／Codex Security 零分析）→ 本稿补齐为**三路线对照 + 可吸收件 + 开放问题**，供 source-audit-v1（docs/design/source-audit-v1.md，设计舰 2026-10-19 已有零代码设计稿）与用户头脑风暴消费。
> 证据基础（全部实读）：
> ① VulnClaw：D 舰对齐档 docs/reviews/2026-10-18-realign/D-vulnclaw-全件对齐.md（172 行全读）+ 分析档 docs/research/2026-09-24-vulnclaw-analysis.md（173 行全读）+ 快照 .research/repos/VulnClaw@3b71e26 关键模块复核（codescan/kb/skills 实读，见 §一）。
> ② GenSift：本地仓 .research/repos/gensift（9.2M，git 单提交 e709b53）逐目录实读——SKILL.md/README/docs/design-v1.4.1.md（570 行全读）/phases×12/agents×6/classes 抽样（sqli/term）+patterns 清点/invariants/langpacks/fixtures/hooks/hosts/feedback 全部过目；既有半析 docs/research/liveui/6-gensift.md（探隐侧活体分析）对照复用。
> ③ Codex Security：GitHub openai/codex-security 公开仓 README + sdk/typescript/docs/cli.md（83.8KB 官方参考）实抓；媒体面 c114（中文，正文全引）/csoonline/thehackernews（标题+摘要，正文 CF 拦截如实记录）；**实测**：npm 装 v0.4.0 于 /tmp/cs-test，ZhuLong 靶场仓拷贝至 /tmp/zhulong-scan/repo（原仓只读零写）跑 dry-run／无凭据真扫／--mock 合成扫描／SARIF 导出全链（见 §三）。
> 纪律：三参考语料与代码全部只读；本稿为唯一写入件（另加 HANDOFF 尾行）；未碰 8900 端口与在树兄弟舰件。

---

## 〇 一张表先看懂三家

| 维 | VulnClaw（codescan+solve） | GenSift | Codex Security |
|---|---|---|---|
| 本质 | 黑盒渗透 CLI 附带的三层本地代码扫描 + 模型自决渗透引擎 | 寄生 LLM 宿主的纯技能包：TSV 账本外骨骼 + 子代理五步证伪 | OpenAI 官方工程化产品：TS 状态机编排完整 Codex 线程 |
| 找洞方法 | L1 正则+熵 / L2 结构化污点近似 / L3 逐文件 LLM 评审（≤20 文件×16KB） | pattern 枚举（59 ERE×3 语言+1500+ fixture）→ 逐卡五步证伪 → 盲 Verifier → Confirmer 事实复核 | 基线子代理+威胁模型+四视角调查者（单 worker 内）→ 深扫层 N 并行 discovery+串行 reducer 归并 |
| 覆盖承诺 | 无（跑完就是跑完） | **找全第一**：全 sink 出卡不可抽样，分母 sha256 冻结，G1/G2/G3 三道门 | 概率性收敛（noNewStreak≥4 即饱和），coverage surfaces 如实记排除/deferred |
| 误报防线 | 下游四道闸（完成门/检疫/只渲染 verified/PoC 验证器）；上游 intake 从散文正则抠=弱 | 盲验证+引文全行相等+OBS 先于 TERM+Confirmer 独立复核+翻案级联撤销 | 七道闸（候选/发现两态+独立重验+反证义务+动态验证阶梯+人工反馈回喂+双通道冗余+验证回执三态） |
| 产出 | findings.json 全量+findings.sarif 仅 verified+Jinja2 报告+退出码 0/1/2/3 | F-*.md 九节/machine-fields.tsv/live index/coverage.md/G3 stability-diff/退出码 0/1/2/3 | canonical 三件套（manifest/findings/coverage）+确定性投影 report.md+SARIF/CSV/Linear |
| 语言面 | 规则内置若干；L3 语言不限（LLM 读码） | Java/TS/Python 三语言包（fixture 质量经济学，Go/PHP 二批） | 语言不限（LLM 读码，无确定性枚举层） |
| 成本 | 中（自备 LLM key） | 轻중（宿主会话内，token∝卡数） | 重（默认 gpt-5.6-sol effort xhigh；深扫 96h 上限；实测事故 $13/次失败跑） |

---

## 一 ① VulnClaw：源码找洞相关件提炼（自 D 舰 60 件档+快照复核）

> D 舰总判（D 档:7）：VulnClaw 对我们只剩测绘工具族与终端/机读事件面两块真领先；其源码找洞面（codescan）在 D 舰 60 件中**未单列**（真空白勘误：本节补上）。以下三问按任务书要求提炼。

### 1.1 知识 RAG 怎么用

- **三档降级检索器**（vulnclaw/kb/retriever.py:1-45 实读）：chromadb_active（语义向量，可选依赖 `pip install vulnclaw[kb]`）→ keyword_fallback（**纯 Python 中文感知 BM25**，kb/ranking.py，零外部依赖，可选 cross-encoder 重排）→ disabled。公共方法面（get_cve/search_by_service/search_technique）三后端同构，调用方不分支。语料 store=JSON 文件（kb/store.py）。
- **skill 路由**：skills/dispatcher.py:27 用关键词正则（"web高级|注入|sql注入|xss|ssrf…"）把任务路由到 50 个专题技能目录（skills/specialized/，D 舰 J1：已取 8/50 进 knowledge/concepts/CP-0001..0008，余 42 已由 W3 技法入库舰全量蒸馏 CP-0009..0050，HANDOFF 在案）。
- **experience 经验库闭环**（kb/experience.py:16 + agent/distiller.py:25）：run 结束→distiller 蒸馏 lessons→pending→**人工 approve/reject**→注入后续 run；近重复合并阈值 0.88。活试两轮 lessons=0 空转（D 舰 J3 判"无燃料证明"）。
- **消费方式**：skills/kb 是"可用能力参考，不是必需工作流"（solver.py:411-417 明示）——RAG 是弹药库不是指挥棒，与 solve 引擎的模型自决哲学一致。

### 1.2 审计循环（源码找洞部分）

- **codescan 三层**（vulnclaw/codescan/__init__.py:1-19 docstring + rules.py/scanner.py 实读）：
  - L1 即时正则+熵检查：硬编码密钥/不安全配置/AI 味道代码（rules.py:113 `L1_RULES`）；
  - L2 结构化污点近似：SQLi/XSS/命令注入/路径穿越（rules.py:202 `L2_RULES`）；
  - L3 LLM 语义评审（**opt-in**，scanner.py `scan_code_llm`）：逐文件喂 ≤16,000 字符源码给一句式 prompt（"You are a code-security auditor… Return only the JSON array"），**上限 20 文件**（成本控制），best-effort 解析 JSON（正则抓 `\[.*\]`），L3 异常永不中断扫描。入口 `vulnclaw code scan <path>`（CLI）/ `/codescan`（TUI）/ Python API。
- **solve 引擎的找洞循环**（非源码专用，黑盒主导）：模型自决调工具（nmap/测绘/JS/dir 枚举等）→ 对话口述发现 → finding_parser.py:104 **三层正则从自然语言文本抠 finding**（[Critical] 标签→自然语言描述→confirmed_facts 升级）→ 下游四道闸。
- **防编造四道闸**（分析档 §3.3，快照行号在案）：①完成门 solver.py:475-535——FINAL 必须 cite 已知证据 id、flag 逐字在证据里、无证据拒、拒因回灌重试（:802-808）；②finding 入口隔离检疫 domain_models.py:201-221——无 evidence/vuln_type/remediation 三缺的 finding 标 [未验证]+needs_manual_review，留在审计轨但进不了报告门；③报告只渲染 verified（generator.py:412；LLM 攻击摘要段过 ReportContentFilter 机械清洗）；④PoC 复核验证器 report/verifier.py:577——按 vuln_type 查 PoC 模板真执行，输出判 VULN_CONFIRMED/FALSE_POSITIVE，verified 打 L4。

### 1.3 产出形态

- codescan 产出（codescan/report.py:1-60 实读）：text（rich 终端表）/ json（VulnerabilityFinding 兼容 dict：title/severity/vuln_type=rule_id/evidence/cwe/remediation/target/code_location/finding_id=`rule_id:file:line`/detection_layer/confidence）/ sarif 2.1.0 / markdown 四格式。
- 渗透侧产出：findings.json（全量+lifecycle）+ findings.sarif（**仅 verified**，EvidenceRef→artifactLocation 附件）双工件（findings_output.py:5-8,186-193）；通用报告=Jinja2 渲染 SessionState 真数据（generator.py:405,500-501）；solve 报告=**从 AgentState 直接渲染不问 LLM**（solve_report.py:1-8）；退出码 0/1/2/3（干净/事故/≥1 verified/仅候选——headless.py:32-45）。
- 事件面：--stream NDJSON 七命令；complete 事件内嵌 findings[]（severity 恒 high 硬编码——D 舰 B2 已点名）。

### 1.4 误报/漏报表现（诚实记录）

- 上游弱：finding 从 LLM 散文正则抠（finding_parser.py:104-130），evidence 字段最初也从文本抓 URL——防编造闸门全在下游，上游 intake 可能把口述当 finding 记账（被检疫隔离）。
- PoC 模板按 vuln_type 查表，类型外落 generic 模板（verifier.py:342）——验证覆盖有限；finding_id 去重键=从描述抓第一个 URL/路径拼 50 字符（domain_models.py:266-294），同 URL 多漏洞碰撞。
- codescan L3 上限 20 文件+16KB/文件=大仓语义覆盖极浅；L1/L2 规则零跨过程分析。
- 我方已有对等/更硬件（D 舱判词）：EV 卡+findings 生命周期三桶+replay、SARIF 双工件+链签+恒一致断言、提交协议前移（结构化 submission 替代事后过滤）。

---

## 二 ② GenSift：本地仓逐目录实读（每件 file:line 出处）

### 2.0 目录总览（实读清单）

| 件 | 规模（wc 实测） | 干什么 | 代表出处 |
|---|---|---|---|
| SKILL.md | 120 行（硬预算上限 D-001） | 编排器唯一常驻入口：发起块/角色三件事/元规则/循环纪律卡九条/阶段索引/红线八条/交付物清单 | SKILL.md:66-75,79-89,91-97,101-110 |
| phases/ | **12 件**（md×5+ps1×5+lib.ps1+win-init.md），main-loop.md 1549 行 | 阶段机引用件：59 个命令块载体，渐进式加载（执行到哪读哪件，一层深度） | phases/*.md 全读 |
| agents/ | 6 件 244 行 | 六角色提示词 recon/analyzer/verifier/confirmer/summarizer/reporter | agents/*.md 全读 |
| classes/ | 26 页 1646 行 + patterns/ 59 件（约 509 条 POSIX ERE） | 24 漏洞类判据页（12 节模板）+ term.md 兜底判据 + fixture-spec.md | classes/sqli.md 全读为样板 |
| langpacks/ | java/python/ts 三包 933 行 | 入口枚举模式（sources/persisted/sources-lib.pattern）+guards 五段转录规则+frameworks.tsv+known-gadgets.tsv+sensitive-modules.txt | langpacks/ts/ 目录实清 |
| fixtures/ | 1623 文件（pos 553/neg 756/noise 255+59 manifest） | 正/负/噪音三件套回归语料——pattern 的存活证明，未验证知识禁止进枚举（B-079） | phase0.md:9-17 门 |
| invariants/ | retail.inv 14 条 | 业务不变式包（B 轨知识）：五字段 schema（不变式/违反证据形态/来源/阴性边界/复核状态）+ `# domain: retail` 行业域头 | invariants/retail.inv:1-14 |
| hooks/ + hosts/ | stop-hook 双版本+四适配电+reaper 双件 | 防自停 Stop hook（exit 2 回喂剩余卡数）+宿主×平台适配+孤儿收尸 | README.md:110-147 |
| feedback/ | dispositions.tsv（表头 8 列） | 七值人工处置账本（全局库）：fingerprint/disposition/reason/scope/source/date/review_expiry/run_origin | design-v1.4.1.md:418-435 |
| docs/ | 4 件（design 570 行+conformance tsv 572 行+补完记+suspects） | 设计定稿与逐条符合性对账 | design-v1.4.1.md 全读 |

### 2.1 「12 段状态机」全文逻辑

> 术语勘定：仓内无"12 段"字面（grep 全仓仅 payment-logic 类页的业务状态机护栏与我方 CODEBASE-ATLAS.md:33 的概括语）。实读后两层含义都成立，**全录如下**——(A) phases/ 目录恰 12 件的阶段状态机（Atlas 语源），(B) 卡/候选双层状态词汇表（8+4=12 态）。若用户另有所指，开放问题 #8 留问。

**(A) 阶段机：五段流水 ×12 件载体**（SKILL.md:91-97 阶段索引；phases/ 12 件=phase0/main-loop/l2/joins/terminal 五段 .md + 五段 .ps1 逐节同名翻译 + lib.ps1 公共底座 + win-init.md 纯 Windows 发起；README.md:27 三平台红线"PS 侧经 dvpwa 黄金夹具 58 块双跑等价验证"）：

1. **phase0 测绘与枚举**（phase0.md:3-633，九块）：0.0 pattern-lint+I1 fixture 抽样门（坏 ERE/禁用构造/死 pattern/过宽 pattern，失败 exit 3——**未验证知识禁止进枚举**，:5-17）→ 0.1 派 Recon → 0.2-0.4 三清单枚举（file/source/sink + module 回填 + family 半机械键 + guards/auth 回填）→ 0.5 G1 锚点预检（advisory CVE 锚点必须 ⊆ 冻结清单，不过不开跑，:373-378）→ 0.5b guards 抽样 10% 逐字比对（:410-414）→ 0.5c I19 枚举对账（:443-447）→ 0.6 冻结 sha256 封印（:472-478）+ 0.6b refreeze 显式通道（:479-484）→ 0.7 发卡（bw 全量/fw http+external_message/term 仅 role∈{app,config}，:508-516）+ 0.7b guards 差分与三跳抽样（:542-550）→ 0.8 启动预估 run-estimate.md（:614-633）。
2. **主循环 step0-step6 每轮一轮**（main-loop.md:3）：
   - **step0 前置检查**（:5-111）：旧会话 schema 迁移（:9-30）→ D6 partial 回收通道（:31-58）→ 四 mark 验票 5a/5b/5c/5d 缺一不许取卡（:62-69）→ **L1 单调性**：分母 unchecked 只许不增，retract 豁免额度=log 行数，违例 EXIT_CODE=1+STATE=aborted-l1（:70-87）→ L3 卡顿换道：近 3 轮不降→本轮全派 fw/term（:89-102）→ 周期不变量 I2/I4 快查留痕（:104-110）。
   - **step1 取卡**（:114-273）：优先级=纯 awk 计算列 `priority = 100·band_score + suspicion + centrality + cve_adj`（:190-198；band0=100/band1=60/band2=10 压倒性→"第一天出主要漏洞"；suspicion：无净化预判+20/常量实参−30/hint 态 uncontrolled 事实+25；centrality：入口未鉴权+20/核心模块+10/lib_api 引用密度+5 封顶+20；cve_adj：advisory 锚点文件+15；v2.1 增补：安全敏感模块词典+10、文件级证伪密度−30、同理由聚类−20、test/demo score=−1 排尾**不剔除**）+ **完备性保底每轮 fw/term/ext 各 1 张防饥饿**（:238-245）+ demand-driven persisted_read 追踪卡（:262-263）。
   - **step2 派发**（:276-610）：2a in-flight 记账（:288）→ 2b Analyzer 信封（卡信息+**合法 ID 白名单机械枚举** D-081 :324-325+上次失败原因注入 B-075 :332）→ 2c band2 类聚簇派 Summarizer（:358）→ 2d 语义合并轮 open≥25 触发（:386）→ 2e 盲 Verifier（信封=机器字段+A 分片 OBS 引文行 ≤5+S4-A 白名单+DISP 处置行 join :481-537）→ 2f 双向对称反转抽样（band0/1 refuted 卡 10% 派"为什么其实是洞"复核 :561-562）。
   - **step3 收卡**（:611-1075）：3a 引文机械归一化（字面 `<TAB>`→真制表符/绝对路径→相对 :617-618,713）→ 3b 行数对账+in_flight 消费对账（:680-687）→ 3c 状态迁移（TERM 白名单过滤，:706-719）→ 3d 候选落账（cand_id 三型可反推 :738-742）→ 3e 事实合并（幂等去重 D-088+sort -m+行数恒等式+evidence_hash :802-864）+ Confirmer 派发（:941）+ **retract 级联撤销**（:903-924：派生事实递归 retracted→K 关闭卡回 unchecked→已交付 finding lifecycle=withdrawn 撤 audit/ 留痕 :1016-1020）→ 3f attempt 计费（缺失/无 TERM/非法三者同计费，重派上限后 partial）→ 3g 复核收卡（reversed 走翻案通道）。
   - **step4 级联**（:1076-1112）：K1 uncontrolled→refuted｜K1b intended→not_applicable｜K2 kills→blocked（reason=at:file:line）｜K3 no_edge→no_path｜K4 dead→no_path（文件级，reflection_checked 非空才许）——**只关 band2 卡；band0/1 永不接受 K 规则机械关闭**（不变量 12）；每消一卡回写 facts_used（级联可审计）。
   - **step5 投影 5a-5d**（:1114-1470，不可跳过）：5a machine-fields 落行（VERDICT 行四列+指纹 sha :1120-1124）→ 5b live_findings_index 刷新（severity 降序表+open 候选+近期活动+NOTICE :1312-1315 **审计脉搏**：闭合数/状态分布/交付面占比/最接近 candidate 的卡/ETA+token——零发现轮次也回答"在干什么"）→ 5c progress_board+NOTICE 阈值行（:1404）→ 5d finding 骨架（第 2 节证据链机械投影，Reporter 只填占位符）+ Reporter 门 GATE-FAIL 重派一次后降级交付不许丢弃（:1472）。
   - **step6 完成判定**（:1474-1548）：unchecked=0 ∧ ext deferred=0？→ 否：Plateau 检测（mf 指纹 3 轮集合不变或 4 轮数量非递增→强制停轮 EXIT_CODE=2 口径 :1491-1514）；否则**批轮收口**（每回合连跑 BATCH=3 轮只输出一行 `GENSIFT-CONTINUE: 剩余 M 卡(含 ext N)｜已 confirmed K｜会话 {S}` :1532-1535——续跑=把该行原样发回）→ 是：L1 完成，partial>10% 阻断全闭合宣称（D-086 :1542-1545）→ 进 L2。
3. **L2 发散**（l2.md:3-114，L1 全闭合后必跑）：输入=frontier（blocked 残链+未交付候选+dangling joins+guard 离群源，:19-25）非全账本；派发散 Analyzer（divergence=true）产 DIV 行≤20 条（锚定≥1 账本实体，**只产建议不产结论** :29-38）→ DIV 验收转 ext 卡（:40-67）；收敛=zero_streak≥2 或 visits>5 硬上限；**不变式轨**：per invariant × module 发 ext 卡（:69-100，行业域过滤 B-087：.inv 头 `# domain:` 不匹配即整包跳过）。
4. **拼链与合并**（joins.md:5-96）：J1 多模块（mod: 模块≥2）才派 Reporter 拼链（Egress=契约=Ingress，置信三级 explicit-schema>code-dto>heuristic）→ J2 JOIN 落账+assumptions 非空自动生成 follow-up ext 卡（I13 闭合口径）+dangling 披露 → J3 组合分析 combinations.md（pre-auth 链/原语组合/与已知 CVE 组合，每条锚定≥2 finding_id）。
5. **终态**（terminal.md）：I1-I20 全量不变量+能力边界列（D-091"假完整性比不做更危险"）→ G2 闭卷对账（三向计数/每卡下场可指认/CVE 编号出现即污染剔除）→ G3 双跑稳定（机械层逐字节硬保证：分母冻结/卡派生/完成计数/finding 文件名；语义层 confirmed 指纹重合度≥0.8+差异五分类归因落 stability-diff.md）→ CALIBRATION 草案 → 终态报告投影 → 退出码 0/1/2/3（README.md:193-204）。

**(B) 卡×候选双层状态词汇表（12 态封闭枚举）**：
- **checks.tsv 卡状态 8 值**（main-loop.md:108 白名单原文 `unchecked|candidate|refuted|not_applicable|no_path|blocked|partial|deferred`；设计语义 design-v1.4.1.md:125）：unchecked=唯一未完成态；candidate/refuted/not_applicable/no_path=判定终态；blocked/partial=**披露态**（离开 unchecked 防死锁、永不携带判定语义、必带恢复入口进 coverage）；deferred 仅 ext 卡合法（等带外证据）。ext 卡另有 origin_ref 追加账。
- **candidates.tsv 裁决轴 4 值**（design-v1.4.1.md:321，S8 两轴拆分）：verdict_state ∈ {open, merged-into-X, closed-by-evidence, refuted-by-evidence} × delivery_state ∈ {pending, delivered, degraded}（翻案回 open 时交付轴同回 pending）。
- 下游 machine-fields：verdict ∈ {confirmed, unconfirmed, refuted, dismissed}（S9 验证裁决）+ lifecycle ∈ {空=在役, withdrawn, superseded_by}（翻案只动 lifecycle 列，行保留不删）。
- 完成的唯一判据=awk 计数（"完成=账本计数派生，任何角色宣布完成无证据效力"——design-v1.4.1.md:89）。

### 2.2 五步证伪逐步骤（agents/analyzer.md:9-16 逐字框架+设计 §4 判定纪律）

- **1 DEFINE**（analyzer.md:11）：读类页面⑥节编号判据（C1-C8 条目四段式：证据问句+期望引用+推翻反例+反向），把要逐条回答的判据编号列分片头部（供 Verifier RUBRIC 引用）。不变式 ext 卡的判据来源=invariants/ 条目五字段本身（analyzer.md:49）。
- **2 OBSERVE**（:12-13）：逐字读卡位置 ±10 行+实参来源；**每读完一跳立刻写一行 `OBS:{file}:{line}<TAB>{该行全文}`**（含前导空格，全行相等比对；转义 \t \n \\）；符号歧义核查（全树同名定义>1 必须全列或逐个排除）；**位置角色词表 D-104**（:13）：关键位置后一行配 `ROLE:` 标注 role∈{root_control, guard, sink_anchor, entry, data_flow}——root_control 必钉（"谁说了算"的根控制行）。
- **3 HYPOTHESIZE**（:14）：最短攻击路径假设 source→…→sink 逐跳列出；不确定跳标 `?`；**单次追踪 ≤8 跳**（第 8 跳未到 sink 即转 blocked 交接，不许硬撑到上下文耗尽 A-098）。
- **4 VERIFY**（:15）：逐判据证伪（问"为什么这不是洞"）：可控性？（追到入口或 persisted_read/external_message）可达性？（路由/鉴权/guards——信封已带）净化匹配？（决策表三值强/弱/上下文条件；**多段净化看全部；自命名净化器跟到叶子实现并核查分支可达性**）影响？
- **5 CONCLUDE**（:16）：写 `TERM:{state}<TAB>{reason}<TAB>{facts_used}`；**举证责任规则**：不确定偏向 candidate（对抗 LLM 系统性保守偏置），前提缺失才许 NOVULN；blocked 交接五要素（已走链/下一跳符号/已排除分支/剩余预算/恢复入口），接手方第一步核对链（对不上退回 blocked:handoff-mismatch）。
- **顺产事实契约**（:18-23）：state=refuted/not_applicable 的卡**必须 ≥1 条 FACT**（D4-D 硬规则：零 FACT 证伪=违约——下游 K 级联与负向降权全饿死）；FACT 7 列（type∈{uncontrolled,intended,kills,propagates,no_edge,dead,flow,requires_config} 封闭——**结论词禁止当事实**；loc/evidence/scope_type/scope_ref/reflection_checked/used_facts）；落盘即 hint，入 K 规则必须 Confirmer 转 confirmed。
- **子代理可靠性协议**（design-v1.4.1.md:158-165 五条）：逐观察落盘（结论只许引用已写盘 OBS 行）/证据即时自验（sed -n 逐条复核引文）/工作集硬上限+压缩免疫（被压缩则从分片续作禁从记忆续作）/主代理无状态化（每轮从 checks.tsv 重取）/盲 Verifier 抽样重读+提示词静态前缀（prompt-cache 命中）。
- **判定纪律六条**（design-v1.4.1.md:148-154）：举证责任偏向报 candidate/观察先于结论（O→J→V 顺序机械可查——批量贴标结构上不可能）/上下文预算 ≤120K 超限即 blocked 交接/反叙事框定（注释/commit/命名只作线索不作证据——注入样本）/历史 CVE 只生假设/一卡一派（任务最简偷懒面最小）。
- **下游双确认**：盲 Verifier（verifier.md:9-33 流程固定：⓪⁻ rubric 先行自写 ≤5 条可证伪标准→⓪ 先自推后对照两步禁倒置封选择偏差→⓪' 强制 ≥3 次实际 Read/Grep+≥1 条自采 SELF 引文+sink ±10 行逐字转录→① FALSE-rules FP 卡命中即毙→② 攻击者模拟给具体 payload（"去尝试不是去阅读"）→③ 逐基线判定（结论强度≤证据链最弱一环；auth=unknown 禁反证）→④ 三态裁决+impact×likelihood 机械查表定级矩阵（:21-28）+硬压制三条+降级反例须引文→④' critical/high 必做反向证伪（无 REV 行禁 confirmed）→⑤ 反证清单→⑥ 有界邻接扫描 ≤2 跳（仍无果→unconfirmed+deferred-evidence-gap，是缺口不是反证））+ Confirmer（confirmer.md:9-14 复核单四项：引文核对 sed -n 全行相等/作用域逐成员核对/reflection_checked 逐项重跑/反例搜索；一次只复核一条——批量复核=强度配称失守）。

### 2.3 账本外骨骼结构

- **设计哲学**（design-v1.4.1.md:69-77）：P0 机制优先于记忆——协议=编排命令族（下一步由账本+命令派生，不由 LLM 判断）+任务形态（一卡一派=可选动作空间切到最小）+验收不变量（产物合法性机械判定）；四原则：最小世界/**外部状态机**（取卡=awk 输出，完成=计数，LLM 是工人不是司机）/格式即牢笼（无观察行的结论机械打回）/偷懒无收益（偷懒改变不了"账本还剩多少 unchecked"）。**能力弹性**（:77）：每个机制都是"外骨骼"——替模型扛掉枚举/长程记忆/长任务连贯性/漏洞学记忆/形态发明，模型只在小格里做语义判断；"不存在模型太弱跑不完协议的失效模式"。
- **账本七件套**（design-v1.4.1.md:312-328）：file_inventory/source_inventory/sink_inventory（三清单，冻结）/checks（卡）/facts（事实两级 hint→confirmed）/candidates（两轴）/joins（拼链）/machine-fields（finding）+progress_board。全部 TSV、单写者、确定性 ID（FILE/SRC/SINK-{seq:05d}；cand_id 四型：CD-{sink}-{source}/CD-F-{file}/CD-X-{origin}/CD-INV-{inv}-{module}）、`LC_ALL=C sort` 定序、**列可变性白名单**（状态类列可改，ID/位置/证据/引文类禁改）。
- **账本文本契约**（:461）：UTF-8 无 BOM；TSV 转义封闭三则（\t/\n/\\）；引文=源码行转义后**全文不截断**；分片行前缀封闭枚举 OBS:/FACT:/TERM:/SELF:/RUBRIC:/VERDICT:——不变量 5/20 的单行可查依赖此前缀纪律；合并分片=机械重排合并（cat|sort -m+wc 对账）**禁逐字粘贴**。
- **20 条对账不变量 I1-I20**（:463-486）：fixture 门/冻结校验/三向完备/卡全闭合/候选分片/四相等/剪枝事实全 confirmer 过/分片零丢失/**证据存在性（每条 evidence 引文转义还原后与源码行全行相等）**/引用可解析/级联可审计/band0-1 无 K 关闭/假设点必复核/ID 确定性/blocked+partial 恢复入口/报告数字=账本投影/写边界/双跑稳定/枚举核对/**观察先于结论（OBS 行先于 TERM/VERDICT 行）**。完成声明=全部不变量命令原始输出留档 report 附录——"不存在模型宣布完成的合法路径"（:486）。
- **级联引擎+翻案可逆**（:169-189）：事实两级管道+K 规则五条+剪枝定理五条（判据无关性/强度配称/band0-1 豁免/兜底承诺/审计）+**事实撤销递归传播**（retract→awk 反查 facts_used→被消卡全部回 unchecked→递归撤销派生事实→撤销留痕 audit——"级联必须可逆，否则错消不可逆就成了新的漏报源"）+已交付 finding 翻案走 lifecycle=withdrawn 撤档留痕永不删除。
- **处置账本 dispositions.tsv**（:414-435）：七值封闭（false-positive/intended-behavior/compensating-control/accepted-risk/known-issue/duplicate/fixed）+review_expiry 到期自动降级 hint（防三年前误点永久压制）；抑制型当数据读——命中处置的候选不跳过分析，交付前必须重新核对理由在当前代码下仍成立；回归检测型（fixed）同指纹再出现→NOTICE"回归"。
- **防自停三件**（README.md:110-147+SKILL.md:89）：批轮+GENSIFT-CONTINUE 收口行（唯一合法回合结束形态，中途总结=禁止）/Claude Code 原生 Stop hook（有未分析卡 exit 2 回喂"继续：剩余 N 张卡"）/opencode 插件 session.idle 回灌（带守卫：只在盘上有 running 态会话才回灌）。

### 2.4 「找全第一」如何实现（P4 覆盖不可谈判的七层落地）

1. **分母三清单冻结**（design-v1.4.1.md:115-123）：file/source/sink 三清单 sha256 封印（不变量 2），扩充必须显式 refreeze 留痕并计入 G3 归因——分母不可静默缩小。
2. **三向卡+追加卡两本账**（:124）：每 sink 一张回溯卡（bw）、每 source 一张前向卡（fw）、每 file（role∈{app,config}；secrets 例外含 test/demo——测试文件里的真实密钥是生产风险）一张兜底卡（term）——三个独立方向逼近完备互为盲区兜底；ext 追加卡（joins follow-up/L2 发散/不变式轨）计入 checks 与完成判定但**不计入冻结分母覆盖率**，单独以"ext 闭合率+零 deferred"披露——两本账分开记覆盖算术才闭合。
3. **终态代数封闭**（:125）：unchecked 是唯一未完成态；完成判定=awk 数分母卡 unchecked 为零 ∧ ext deferred 为零；非枚举值一律按未完成处理——没有"大概齐"态。
4. **G1 锚点预检**（:133）：有 advisory 时锚点位置必须 ⊆ 清单，不过不开跑；两者皆空（企业私有代码常态）时如实记 N/A 并披露"本目标无机械召回下界"——**不得假装通过**。
5. **活性三律+停轮强制层**（:243-266）：L1 单调性（唯一回升通道=retract 翻案留痕）/L2 有限重派（≥2 次无 TERM→partial，无无限重派路径）/L3 卡顿换道；宿主原生 Stop hook 把"可验"变"必行"（几百轮同构循环里协议步序漂移与静默停轮概率随轮数累积——活性三律是事后可验不是事前强制）。
6. **排序≠分母**（:236,232）：优先级公式只改顺序不改分母，优先级与完成判定完全隔离——防"前面已找到很多→该收了"的诱导（历史真实事故）。
7. **覆盖披露十二类**（:362-366）：refuted 按 K 规则分布/blocked+partial 恢复入口/pattern-undetectable 类/dangling joins/未分片区域/级联统计/种子行状态/guard 离群/ext 闭合率与饱和/G1 锚点来源/库模式分母强度/平台缺口——**"没发现"必须能解释**，每个 sink 的下场可查。
- 兜底三层（:63 需求红线原文）：模式表声明范围内的 sink 零漏检绝不抽样；模式表外以 pattern-undetectable 披露+term 兜底卡+L2 发散三层兜底（无下界保证，coverage 如实披露）。
- 知识三轨道防漏（:270-281）：A 模式轨（找全）/B 结构轨（guards 差分+业务不变式——**不需要预知模式**的发现：防护缺失、业务逻辑破坏）/C 发散轨（unknown unknowns——LLM 自由洞察的合法通道，"发散的是该看哪里，永远不是结论是什么"）。

---

## 三 ③ Codex Security：公开材料+装机实测

### 3.1 身份与沿革（媒体面）

- **沿革**（c114 报道）：脱胎 2025-10 私测项目 **Aardvark**，2026-03-06 更名上线研究预览版；HN 先发现（星标冲 1.2k）后 OpenAI 认领开源。开源的是应用层的壳（Apache-2.0，TS ~25.8 万行），模型层闭源（默认 gpt-5.6-sol）。
- **战绩**（c114/csoonline/thehackernews 三源一致）：上线头 30 天扫 **120 万+ commits**，捞出 **792 critical + 10,561 high**；同批仓库反复扫**误报率下降超 50%**（csoonline 标题"found 11,000 high-impact bugs in a month"同口径）。
- **成本事故**（c114 转 HN 实测）：gregwebs——小仓库扫描 52 分 47 秒后因"仓库 HEAD 已变化"作废，吃掉 Pro 周额度一半；Quai——起步即限流，重试 1 分钟放弃，失败跑花费 **$13**；根因=默认 gpt-5.6-sol + effort **xhigh**（Sol 标价 $5/1M 输入、$30/1M 输出）。
- 注：thehackernews/4sysops 正文 Cloudflare 拦截（fetch 403/JS challenge），标题与摘要已引；csoonline 正文可达但正文剥离后信息量低；learn.chatgpt.com 本网络不可达（HTTP 000）——以上如实记录，**主证据=GitHub 官方仓+装机实测**。

### 3.2 扫什么（语言/漏洞类/模式）

- **语言**：不限——无确定性解析层，全部由 LLM 读码（我方 liveui 分析判"无确定性枚举层（车道 A 缺位）"）；官方基线审计 prompt 是一份完整 SAST 清单：SQL/NoSQL 注入、XSS、越权/IDOR、路径穿越、命令/代码注入、开放重定向、SSRF、反序列化、硬编码凭据、XXE、XPath、配置错误、DoS、头注入、上传、内存安全、请求走私、原型污染、危险代码生成、资源耗尽 + 密钥专节（core-scan.md 八步之二）。
- **扫描模式**（scan --help 实录）：repository/selected paths/--diff base..head/--working-tree；mode standard|**deep**（deep=并行 discovery workers map-reduce：默认 workers=4、每 worker subagents=3、stop-after-no-new=4、max-discovery-runs=40、max-time-hours=96 封顶）。另有 diff/commit/branch_diff/deep_repository 等 inventory 策略与 component-scan/multiscan/bulk-scan。

### 3.3 怎么判 severity

- **五级**：critical/high/medium/low/informational（实测 mock 产出 2C/4H/3M/2L/1I）。
- **校准三件**（cli.md 官方文档+实测）：①扫描内每发现带校准 severity+rationale+confidence+rationale（按真实世界影响分级——c114 三步工作流："按真实世界的影响分级"）；②`classify-severity --rubric` 独立后置轮：**不重复发现**，对已完成 findings 逐条在只读独立轮里按用户自定标尺（text/PDF/DOCX/目录）重估——"每 finding 单独只读轮，不带工具不查源码"，产出 decision/normalized level/rationale/confidence/**reviewTrigger**（缺什么事实会改判），评估按 evidence hash 绑定、断点续跑、原 findings 与封印工件不动；③CI 门 `--fail-on-severity`：达到阈值即 exit 1（report-only by default）。
- **硬压制三条**（liveui 分析 core-scan.md：self-only→ignore/不可达前置→ignore/特权前置→ignore，除非提权差本身是问题）+ secret 专判（disclosure path=源码读者获得超越读源码的凭据访问权，无需执行代码；测试文件名/占位符断言单独不足以定性或否决）。

### 3.4 工作流（CLI/CI）

- **单机**：`npm i -g @openai/codex-security` → `cs login`（ChatGPT OAuth/device-auth/SSH 转发；CI 用 OPENAI_API_KEY/CODEX_API_KEY）→（可选）`cs policy .` 起草 SECURITY.md（存仓库外人工拷入）→ `cs scan .` → `cs findings/scans` → `cs classify-severity/dedupe/suggest-owners` → `cs export`（SARIF/CSV/JSON/threat-model）→ `cs publish`（Linear/findings service/Cloud）→ `cs validate/patch/verify-fix`（修复链六层优先级+Generate/Apply/Verify 工作台三阶段）。
- **CI**：官方 GitHub Action（20 输入：scope/mode/model 默认 gpt-5.6-sol/effort 默认 xhigh/cyber-access-program/fail-on-severity/annotations ≤50/upload-artifacts）；Ubuntu runner 需预装 bubblewrap+apparmor 给沙箱铺路；容器化 bulk-scan（docker compose，cap_drop ALL+seccomp 464 行 allowlist+AppArmor+uid 10001）。
- **沙箱六层纵深**（liveui 分析 §二，源码级）：Docker→seccomp（封 AF_ALG/AF_VSOCK）→AppArmor→Codex 原生 Bubblewrap（worker 级 read-only+断网）→入口点卫生→提示词级（userContext 一律 untrusted）。**worker 开工前用真实 codex 二进制预检权限 profile 确实生效才放行**（permission-profile-preflight 770 行）。

### 3.5 limits（官方+实测）

- **硬依赖**：Node 22.13+/24/26 + Python 3.10+（实测：系统 3.9.6 被拒，homebrew 3.12 经 `PYTHON=` 环境变量放行）+ 平台 Codex 二进制（实测首装缺 @openai/codex-darwin-arm64 二进制，补装 @openai/codex 2 分钟解决）。
- **凭据硬门**（实测）：无凭据真扫即刻终止 `No credentials were found. Run 'codex-security login'…For CI, set OPENAI_API_KEY or CODEX_API_KEY.` **EXIT=2**（干净的 CI 失败语义）；`--dry-run` 免凭据可验输入。
- **成本重**：默认 xhigh；深扫默认 96h；--max-cost 估计性上限（80% 时 dashboard 可提额，CI/headless 不提供）；官方成本口径明示"标准 API 价格估算，不含其他层费用/附加费/账户定价；ChatGPT 订阅额度不计量"。
- **生态绑定**：worker=@openai/codex-sdk 起的完整 codex exec 线程（非裸 API 调用）；Daybreak Trusted Access for Cyber——部分网络安全请求与 protected findings 需审批；Bedrock/OpenRouter/Fireworks 可换推理商但模型 ID 仍 OpenAI 系。
- **无确定性枚举层**：发现全靠 LLM 双通道（基线+调查者）+验证层合并——概率性收敛，coverage surfaces 如实记排除/deferred/openQuestions，"不声称穷举覆盖"（与 GenSift 覆盖铁律哲学相反）。

### 3.6 装机实测记录（v0.4.0，2026-10-18 本机）

| 步骤 | 结果 |
|---|---|
| `npm i @openai/codex-security`（/tmp/cs-test） | ✅ 7 包 26s；`--version`=0.4.0（注：我方 liveui 分析档基线 0.1.95，已迭代） |
| `scan <repo> --dry-run --headless` | ✅ 免凭据：preflight 完成输出 target/mode/auth(method=stored_credentials, verified=false)/model/effort 全量 YAML |
| 真扫（无凭据） | ❌ `No credentials were found…` **EXIT=2**（认证前置，无静默失败） |
| 补 @openai/codex（二进制包） | ✅ 2m 装齐 vendor/aarch64-apple-darwin/bin/codex |
| `scan <repo>/apps --mock --headless` | ✅ **合成 12 findings**（2C/4H/3M/2L/1I；ELAPSED 0s；mock 明示"no security analysis or LLM calls"）——mock 需要 Python 3.10+（3.9 拒，PYTHON=/opt/homebrew/bin/python3.12 过） |
| 产物三件套 | ✅ scan-manifest.json（2.3KB）+findings.json（36.7KB）+coverage.json（3.6KB）+report.md（30KB，头部署名"Canonical artifacts…This report is a deterministic projection of those files"）+checkpoints/+SQLite 状态库 |
| `export --export-format sarif` | ✅ SARIF 2.1.0（31KB，automationDetails=scanId；结果 level=warning+物理位置+CWE/remediation 内嵌 message）——需指定 scan-dir 或在扫描仓内跑 |
| ZhuLong 原仓 | 只读零写（拷贝至 /tmp/zhulong-scan/repo 2.6G/161,924 文件后扫描，原仓未动） |

**findings.json 单条字段全录**（实测 mock 产物，真实扫描同 schema）：attackPath{assumptions,evidenceRefs,summary}｜codeEvidence[]{code,explanation,id,label,language,path,role,startLine}｜confidence{level,rationale}｜findingId（csf_*）｜fingerprints{algorithm:"codex-security/v1",primary:sha256}｜identity.anchor｜locations[]{endLine,path,role,startLine}｜occurrenceId（occ_*）｜preventiveControls[]｜provenance.source｜remediation｜remediationTests[]｜rootCause{evidenceRefs,summary}｜ruleId｜severity{level}｜summary｜taxonomy{category,cwe[]}｜title｜validation{method,status,summary}。

---

## 四 三路线对照表（找洞方法/输入/输出/强弱/误报漏报）

| 维 | VulnClaw codescan+solve | GenSift | Codex Security |
|---|---|---|---|
| **找洞方法** | L1 正则+熵（L1_RULES）→L2 结构化污点近似→L3 逐文件 LLM 评审（20 文件×16KB 上限）；渗透侧=模型自决+对话口述→正则抠 finding | 确定性 pattern 枚举（59 ERE×3 语言，fixture 门拦截未验证知识）→三向卡分母→逐卡五步证伪（OBS 引文+8 跳上限）→盲 Verifier+Confirmer→K 级联+L2 发散+joins 拼链 | 基线子代理（零上下文防锚定）+威胁模型引导+四视角调查者（Forward/Backward/Authz/Open-ended）并行→逐发现独立重验→深扫层 N 并行 discovery+串行 reducer（remediation-subsumption 归并） |
| **输入** | 源码路径（codescan）或目标 URL/范围（渗透）；LLM key 自备 | 源码绝对路径+可选 advisory CVE 清单+可选 width/batch/执行档授权 | 仓库/路径/diff/working-tree；必配 OpenAI 凭据（login/API key）；可选 SECURITY.md 策略+知识库+威胁模型 |
| **输出** | text/json/sarif/markdown 四格式（codescan）；findings.json+lifecycle+findings.sarif 仅 verified+Jinja2 报告+退出码 0/1/2/3 | F-*.md 九节+machine-fields.tsv+live_findings_index 实时索引+coverage.md 十二类披露+combinations+G2/G3 审计件+退出码 0/1/2/3 | canonical 三件套+确定性投影 report.md+SARIF/CSV/JSON/threat-model.md+Linear/Cloud 发布+SQLite 历史+退出码 0/1/2（--fail-on-severity 可控） |
| **强** | 工程量大（64,795 行 py+测试 1,680 函数）；测绘工具族六引擎；ExecutionGate 内容寻址审批；证据内容寻址去重 | 覆盖不可谈判铁律（全 sink 出卡+冻结分母+三道门）；零自研代码三平台；账本外骨骼让弱模型也能跑完协议；翻案级联可逆；成本轻 | 工程上限（六层沙箱+预检+发布三验）；七道防 FP 闸；动态验证阶梯（crash/ASan/gdb/接口复现）；双层去重（reducer+跨扫描 embedding）；威胁模型/策略/severity rubric 全套产品面；expected-findings 夹具门 |
| **弱** | 上游 intake 从散文正则抠（防编造全在下游）；PoC 模板查表覆盖有限；codescan L3 20 文件上限大仓极浅；无覆盖承诺（跑完就是跑完）；三引擎语义重叠债 | 每 sink 一卡成本∝卡数（百文件数小时千文件过夜）；语义层无逐字节确定性（G3 只承诺统计稳定）；三语言起步（fixture 质量经济学）；宿主依赖（防自停要 Stop hook/插件配合） | 无确定性枚举层（漏检无下界保证）；成本重（xhigh+96h 深扫+$13 事故）；深绑 Codex 运行时/Daybreak 审批；开源壳模型闭源 |
| **误报表现** | 下游闸硬（检疫/只渲染 verified/PoC 验证）但上游可入口述；complete 事件 severity 恒 high 硬编码 | 盲验证+FP 卡库+FALSE-rules 命中即毙+降级反例须引文；处置库七值+到期复核（企业重复报警治理） | 反证义务（只有源码背书反证能否决）+人工反馈回喂（理由仍成立才压制）+复扫误报降 50%（官方口径） |
| **漏报表现** | 无覆盖账（覆盖度不可证）；L3 文件上限即漏检面 | 分母可证（三向卡+I3+G1 锚点下界）；模式表外三层兜底如实披露 pattern-undetectable | 概率性收敛 noNewStreak≥4 即停（无穷举承诺）；coverage.deferred/openQuestions 如实记"没查到"而非"没有" |

---

## 五 若 GraphLed 做白盒：可吸收件清单 + 已有可复用件

> 只列件不设计——取舍与组合方式留给用户头脑风暴。

### 5.1 三家可吸收件

**自 VulnClaw**（成本最低，多数已在 D 舰 60 件档判过）：
1. codescan 三层分层思想（L1 秒级正则+熵→L2 结构化→L3 LLM 深读）——但 L3 的 20 文件×16KB 上限是反面教材（大仓浅覆盖）；已有 W3 工具卡体系可承接 L1/L2 为确定性工具卡。
2. 知识 RAG 三档降级（语义向量→纯 Python BM25→禁用）——弱依赖环境知识检索可行架构（D 舰 J4 已排 W5 评估）。
3. evidence 内容寻址去重（SHA-256 content_hash+duplicate_of+有界预览原文可回查）——同输出重复探测不重复占预算。
4. finding 隔离检疫中间态（[未验证] 留审计轨进不了报告门）——"证据不足的声明是一等公民但永远进不了报告门"。
5. PoC 验证器分级（VULN_CONFIRMED/FALSE_POSITIVE/TIMEOUT）+退出码第 4 态（rc3=仅候选 CI 黄灯，D 舰 G4 已排 W2）。

**自 GenSift**（机制密度最高，与账本哲学同源——修正案 A 已定"吸收 GenSift"）：
1. **分母三清单冻结+三向卡**（bw/fw/term+ext 两本账）——"找全第一"的地基；source-audit-v1 §1.2 已有账位分级表承接。
2. **五步证伪+OBS 引文契约**（逐观察落盘/引文与源码行全行相等/OBS 先于 TERM 机械可查/ROLE 词表钉 root_control）——证据卡 replay 的语义级强化。
3. **盲 Verifier 协议**（先自推后对照封选择偏差+自采 SELF 引文+RUBRIC 先行+REV 强制反向证伪+定级机械矩阵）。
4. **账本外骨骼四原则**（外部状态机/格式即牢笼/偷懒无收益/最小世界）+行前缀封闭枚举+20 条单行 CLI 对账不变量。
5. 优先级计算列（band+suspicion+centrality+cve_adj 纯 awk，LLM 零判断）+完备性保底插卡防饥饿。
6. K 级联五规则+剪枝定理（band0/1 永不接受机械关闭）+事实两级管道（hint→confirmed 须独立复核）+翻案递归撤销（级联必须可逆）。
7. dispositions 处置账本七值+review_expiry 到期降级（企业"工具没有记忆"信任崩塌的治理件）。
8. pattern-lint+fixture 正负配对门（未验证知识禁止进枚举；正例零命中=死 pattern/负例命中=过宽打回）。
9. guards 五段差分+业务不变式轨（不需要预知模式的发现通道）+L2 frontier 发散（unknown unknowns 的合法通道——只产建议不产结论）。
10. G1/G2/G3 三道验收门（锚点预检召回下界/闭卷对账 CVE 编号污染剔除/双跑分级稳定契约）。

**自 Codex Security**（工程与产物格式上限）：
1. **canonical 三件套+确定性投影报告**（report.md 永不由模型手写，可随时重生成）——与"报告=投影"同构但更彻底。
2. findings.json 字段族（attackPath/rootCause/codeEvidence[]/taxonomy/validation/fingerprints 跨 run 稳定身份）——SARIF/CI 互操作的工业格式参照。
3. classify-severity 后置独立轮（不重复发现、只读轮按用户 rubric 重估、reviewTrigger 记"缺什么事实会改判"、evidence hash 绑定断点续跑）。
4. 基线子代理（fork_turns:none 零上下文克隆防锚定）+四视角调查者（Forward/Backward/Authz/Open-ended）双通道冗余。
5. 深扫 map-reduce 语义（noNewStreak 饱和/capped/时限三终态分别记账+崩溃恢复租约/代际）。
6. 沙箱六层纵深+"配置→预检→才放行"三步（464 行 seccomp allowlist 封 AF_ALG/AF_VSOCK 可直接改名单复用）。
7. 反证义务话术（"missing deployment evidence lowers confidence, does not defeat a source-backed vulnerability"）+secret disclosure-path 专判。
8. expected-findings 夹具门（invoice-desk 模式：给审计引擎建带预期清单的漏洞应用，放行门=全找齐）。
9. exit 语义（--fail-on-severity 阈值门+认证失败 EXIT=2 无静默绿）。

### 5.2 我们已有的可复用件（不重造）

| 件 | 现状 | 对白盒的直接复用位 |
|---|---|---|
| **harness 执行器插槽**（engines/ 七引擎 + contracts/08-manifest 十二字段 MANIFEST + tools.lock 验签） | nuclei/sqlmap/vuln-agent/vulnclaw/web-blackbox/deepex/session-viz 在役；"模型是参数不是命运" | 白盒引擎（无论自研还是吸收 GenSift 形态）按插槽接入 intents/提交协议；vuln-agent 已是八段管道源码分析引擎（POC 四要素门） |
| **源码类工具卡**（W3 工具卡舰 25 卡+tools.lock 供应链锁定+卡层门链） | cli/tools cards.py 七纪律字段+gate.py 门链+ECDSA 验签 | rg/ast-grep/osv-scanner 等确定性源码工具按卡接入（cyber-harness E 舰四件对照已判"借四超八"）；L1/L2 确定性扫描=工具卡天然形态 |
| 账本 13 表+EV 卡+submission 提交协议 | contracts/01/06/07；findings 生命周期三桶+replay_state | 白盒 finding 落账走 submission（散文不能直接变账——VulnClaw 上游弱的解）；anchor 边型（source-audit-v1 §1.2 已设计） |
| 九门状态机+覆盖度矩阵非空门 | contracts/04；denominator-ready 分母上锁 | 白盒分母（三清单型）挂门序；覆盖不可谈判律在册（修正案 D） |
| 知识 schema（contracts/14 八类目+staging 四门槛人审门） | knowledge/ 50 技法页在库（VulnClaw 语料已全量蒸馏 CP-0001..0050） | 类判据页/pattern 库/不变式包按 K5/K6 类目入位；fixture 门走 staging 管线 |
| SARIF 双工件+报告中心 | report_artifacts.py findings_json+SARIF 2.1.0 仅 verified+链签 | 白盒审计专报出口（T4-P7）；Codex canonical 三件套字段族可作投影扩参 |
| evals 退出码 0/1/2/3+GT 评测集 | rc3 仅未验证候选已落；evals/gt 56 面+zl-* 战场 | 白盒效果回归门（expected-findings 夹具门的落位）；ZhuLong 靶场=现成白盒考卷 |
| guard/egress 四层执法+沙箱资源帽 | tanyin-guard 三帽+tools.lock+审批 command_hash | 白盒执行档（PoC 验证/动态验证阶梯）复用，不必抄 Codex 六层的全部 |

---

## 六 开放问题清单（留用户头脑风暴定夺——≥5）

1. **覆盖哲学定位**：GraphLed 白盒跟 GenSift 的"找全第一"（全 sink 出卡、成本可谈判、千文件过夜）还是 Codex 的"概率收敛+如实披露"（noNewStreak 饱和即停）？或分档（快扫=概率/深审=穷举）？——这决定分母账本要不要三清单冻结那一整层。
2. **确定性层与 LLM 层的配比**：L1/L2 确定性工具卡（rg/ast-grep/osv-scanner，W3 现成）+LLM 深读的边界画在哪？GenSift 的 pattern 枚举（59 ERE+1500 fixture 维护成本）vs Codex 的全 LLM 双通道（无枚举层漏检无下界）——中间态是否=「工具卡产 sink 候选入 intents，LLM 逐卡五步证伪」？
3. **验证强度阶梯**：GenSift T0/T1 默认+T2/T3 授权 vs Codex 动态验证阶梯（crash PoC/ASan/gdb/接口复现/静态回退七元组）——白盒 finding 的 confirmed 门槛定在哪档？执行档挂 guard/egress 四层执法的哪层？
4. **分母与谱图的关系**：source-audit-v1 已裁「无执法语义不入账、符号入谱工件、污点入卡」——GenSift 三清单（file/source/sink）在 13 表里的落位是 assets+facts 还是独立清单工件？三向卡（bw/fw/term）映射 intents kind 还是新卡型？
5. **类判据知识从哪来**：自 GenSift 类页面 12 节模板（24 类×3 语言，fixture 工程量大）还是自 VulnClaw 50 专题蒸馏件（已在库 CP-0001..0050）改造+Codex SAST 清单（20 类）补全？fixture 正负配对门（未验证知识禁止进枚举）要不要整套继承？
6. **severity 口径**：三家三套（GenSift 类阶梯+impact×likelihood 矩阵/Codex 校准+用户 rubric 后置轮/VulnClaw PoC 验证 L4）——我方 finding 定级走哪套？classify-severity 式"不重复发现只重估"的后置轮要不要？
7. **成本模型**：白盒审计的计费/预算挂 budget.tsv 四维已天然支持——但 GenSift"每 sink 一卡 token∝卡数"与 Codex"$13 失败跑"都是前车之鉴；审计任务的预算帽/分档定价（快扫/深审/深扫 96h 型）怎么定？
8. **「12 段状态机」语义确认**：本稿按两层解读全录（phases/ 12 件阶段机 + 卡/候选 12 态词汇表，§2.1）——若 Atlas:33 原意另有所指请指正，本稿结构不变仅改标注。
9. **外接还是吸收**：Codex Security 维持 liveui 判决①"只偷设计不直接外接"，还是按 nuclei adapter 先例外接为"OpenAI 级第二意见"陪审员（cs scan --json --headless 单进程入口干净）？翻案条件（Daybreak 访问+发现率碾压+worker 开放纯 API）三条是否维持？
10. **盲验证的宿主成本**：GenSift 盲 Verifier（先自推后对照+自采引文）每候选一子代理；我方 P4 独立盲重放 30/30 已在册——白盒 finding 的复核走"每条独立子代理"还是"终态抽样盲重放"？成本/强度配比留裁。

---

## 七 证据可复核性声明

- VulnClaw：D 舱档（172 行）+分析档（173 行）全读；本稿新增 codescan/kb 模块快照实读（rules.py:113/202、scanner.py scan_code_llm、retriever.py:1-45、report.py:1-60）行号现场复核。
- GenSift：.research/repos/gensift 全目录过目，核心件全文直读（design-v1.4.1.md 570 行、SKILL.md 120 行、README.md 267 行、main-loop.md 关键节、agents×6、l2/joins 全文、phase0/terminal 标题级+关键块、sqli/term 类页、retail.inv、fixtures 清点）；全部 file:line 为现场实读行号。
- Codex Security：GitHub raw README（9.1KB）+sdk/typescript/docs/cli.md（83.8KB）官方文档实抓；csoonline/thehackernews/4sysops 正文 CF 拦截如实记录（标题+摘要引用）；c114 中文报道正文全引；**实测**：/tmp/cs-test v0.4.0 装机+dry-run+无凭据 EXIT=2+mock 全产物+SARIF 导出全链留存（/tmp/zhulong-scan/state/scans/apps/codex-security-apps-zAiwQq/）。
- ZhuLong 靶场仓全程只读（拷贝 /tmp/zhulong-scan/repo 后扫描，原仓零写）；未碰 8900 端口；未碰在树兄弟舰件。
- 本稿为唯一写入件（另加 HANDOFF 尾行与 git pathspec 提交）。

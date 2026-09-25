# 批次 5 探知项台账（G-29..G-35·T19 收口终态）

> 来源：①批次 5 计划「探知项」节原文誊录（G-29..G-35，docs/superpowers/plans/2026-09-24-b5-knowledge-flywheel.md——程序化提取防转写漂移）；②T19 收口状态归并（本文件=catalog 单源，HANDOFF 快照引用）。
> 通道纪律：契约回注一律走微版本勘误通道（零存量数据期先例，schema_version 不递增）；状态变更随任务记 HANDOFF 开发流水。

## 一、计划原文誊录（G-29..G-35，2026-09-24 计划冻结文本）

| # | 缺口 | 影响 | 本批处置 | 建议裁决 |
|---|---|---|---|---|
| G-29 | **知识页 ID 命名空间与账本铸造权边界**：KP-/STG-/CP-/PR-/EN-/TG-/PT-/RT-/BZ- 九前缀不在账本前缀表（设计 §4.1），ledger-next-id 不适用 | 知识页 ID 分配无契约依据，存在与账本 ID 混流风险 | 契约 14 §6 冻结知识库自有前缀表+tanyin-knowledge 内部 next_page_id 机械分配（四位零填充字典序=时间序——账本同精神不同源） | 已随 T1 裁决落地；账本/知识库命名空间永不分流混用 |
| G-30 | **语义近重复合并无载体**：VulnClaw distiller 0.88 嵌入余弦阈值需嵌入模型，stdlib 零依赖环境不可得 | 同义知识页可能随飞轮累积冗余 | R10：v1 规范哈希精确去重+lint 同 class 页数 ≥8 输出「人审合并建议」告警 | 批次 6+ 有先例数据与检索基线后裁决（BM25/嵌入双轨——VulnClaw 分析 §6.3 已登记可行架构） |
| G-31 | **CNPEN 全景图素材落位歧义**（夹具素材 vs 知识库膨胀） | 全景图进库则库内出现非知识内容（矩阵样例/夹具素材） | 裁决：知识库 sources 只登记映射指针行；夹具/矩阵样例素材归 tests/fixtures（防库膨胀） | 已随 T16 落地 |
| G-32 | **CVE 快照刷新流程缺位**（谁/何时/多大幅度刷新 cve-snapshot.tsv） | 快照时效衰减 → nday 漏报 | 本批 cve/README.md 冻结纪律：人工重铸整文件+首行刷新日期注记+lint 七列校验；nday 输出必附快照日期供审计 | 批次 6 安装器期裁决自动刷新通道（联网边界内=下载快照文件，非交互核验） |
| G-33 | **库外 ingestion 审批与交战区 approvals 双锚一致性无机检**（approve --knowledge 落交战区 approvals.tsv、knowledge log.md 落库侧，两账本独立） | P6 沉淀可能只落一侧（审计断链） | R8/R13：P6 duty 命令化双写（gate 查交战区侧、库侧 lint 查 log 行） | 双侧行互证机检留批次 6 evals |
| G-34 | **match 窗口判定基准日无源**（先例窗口「过期自动失效」需「今天」作判据） | 墙钟进判定 = 非确定性（金样/审计弱化） | 裁决：--today 必填显式传入（缺省 exit 2）；总控以 timeline 最近时间戳为 today 源（P2 开局调用约定写进 P6/P2 md） | 已随 T11 落地；批次 6 evals 统一 today 注入口径 |
| G-35 | **BugHunter/Threatswarm/CEP 三源仓库获取与许可核验时点**（.research/repos/ 当前仅 VulnClaw 在场） | 外部库语源不全（hunt-* 模板/27 agent 语料/CEP ROE） | T17 降级登记：SOURCES.tsv 落 origin 行+note=待补——不造数据、不阻塞出口①②（抽查以在库页为准） | 执行期 clone 至 .research/repos/&lt;name&gt;+MIT 逐一核验（LICENSE 文件在场）后补蒸馏；长期=批次 6 安装器 vendor 清单化 |

## 二、实施期增补（本批无新增探知项）

- T18 前置测试隔离泄漏（T16/T17 两处 test_lint_passes_on_seed 就地 lint 写热种子库）=工程缺陷非接口缺口，随「批次 5 T18 前置」commit 修复并钉死「种子库零写热」断言——见 HANDOFF 开发流水，不入本台账。
- T18 抽查语义裁决（R-T18-1 探针副本执行/R-T18-2 在库页口径）随 commit 76bba9b 记账，属计划内裁决非新缺口。

## 三、状态归并台账（T19 收口终态，G-29..G-35 全量）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-29 | **已闭环·批次 5** | 契约 14 §6 前缀表+next_page_id 机械分配（T1 契约冻结 1e89bb5；T11 commit 重号 636c4c2 实跑兑现）；账本 44 面零触碰 |
| G-30 | **缓解已落地·合并载体批次 6+ 裁决** | R10 dedup_key 规范哈希精确去重（T10 lint 查重+T11 commit 终检）+同 class≥8 人审合并建议告警（4963139）；BM25/嵌入双轨留批次 6+（VulnClaw 分析 §6.3 登记在案） |
| G-31 | **已闭环·批次 5** | T16 降级登记（e557b1d）：SOURCES 只落指针行，素材缺位不造数据；夹具素材归 tests/fixtures（knowledge-dirty 脏夹具同口径，76bba9b） |
| G-32 | **纪律已冻结·自动刷新批次 6 裁决** | cve-snapshot.tsv 14 行+首行 snapshot-date 注记+cve/README 更新纪律（4102b7e）；lint 七列校验+nday 输出 #snapshot-date 审计行双兑现 |
| G-33 | **双锚流程已落地·互证机检批次 6 evals** | P6 duty 命令化双写（T19：tanyin-ledger approve --knowledge+库侧 tanyin-knowledge approve 双锚，R-T15-1 裸旗标归一先行 bb9c5bf）；gate 查交战区侧断言真跑（T15 P6 门端到首通） |
| G-34 | **已闭环·批次 5** | match --today 必填缺省 exit 2（T11 636c4c2）+score --today 必填（T12 df51cd1）；SKILL/P6/P2 调用约定随 T19 接线行承载 |
| G-35 | **降级登记已落地·三源到位后补蒸馏** | SOURCES.tsv KP-0007..0009 待补行+LICENSE 核验纪律（T17 c4c6728）；抽查以在库页为准不阻塞出口①②（T18 R-T18-2 口径） |

## 四、移交清单（批次 6 开工前必办）

- **VulnClaw 批 6 三项登记（只登记不实现）**：①headless 退出码第 3 态（0=干净/1=事故/2=≥1 verified/3=仅候选——「仅未验证候选」态是否纳入 TanYin 0/1/2 契约，headless.py:36-45）；②findings.json（全量+lifecycle）+findings.sarif（仅 verified）双工件与 EV 卡片↔SARIF artifactLocation 映射（findings_output.py:330-352/:186-193）；③报告内容过滤器（LLM 叙述段进报告前机械清洗——剥工具调用痕迹/轮次标记/think 标签，report/filter.py 同型）。
- **批次 6 前必裁决/定标**：G-22（生产 EC 钥+重签+release.pub 替换+upstream commit 换真）、G-25（Burp 粘贴格式边界——渲染器）、G-21（Cytoscape.js vendor 复裁）、批次 3 遗留 G-4/G-11 定标、本批新登记 G-30/G-32/G-33。
- **持续飞轮（内容生产，不再动代码）**：VulnClaw 余 39 专题蒸馏（首批 8 页外）、CNPEN 素材五类缺补登记、BugHunter/Threatswarm/CEP 三源到位后补蒸馏——全走本批 staging 流水线（register→蒸馏→lint→approve→commit→export）。

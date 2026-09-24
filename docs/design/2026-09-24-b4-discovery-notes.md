# 批次 4 探知项台账（G-16..G-26·T14 收口终态）

> 来源：①批次 4 计划「探知项」节原文誊录（G-16..G-23，docs/superpowers/plans/2026-09-24-b4-engine-layer.md——程序化提取防转写漂移）；②设计增补 commit 登记（G-24=fb72cd5 实时发现流与优先级调度／G-25=b0006f2 FD 报告卡片规格／G-26=71d3b7c 图谱驱动全程）；③T14 收口状态归并（本文件=catalog 单源，HANDOFF 快照引用）。
> 通道纪律：契约回注一律走微版本勘误通道（零存量数据期先例，schema_version 不递增）；状态变更随任务记 HANDOFF 开发流水。

## 一、计划原文誊录（G-16..G-23，2026-09-24 计划冻结文本）

| # | 缺口 | 影响 | 本批处置 | 建议裁决 |
|---|---|---|---|---|
| G-16 | **EV 卡片↔E-index 同值性的 validate 集成缺位**：设计 §4.11"卡片与 TSV 不一致=P4 ledger-validate 失败"，但 validate 只读 13 表不读卡片文件 | 同值性执法点与设计文字漂移 | tanyin-replay 在重放前校验（T4 `check_consistency`）；validate 集成不动 | 契约 v3 裁决：validate 增 `--with-cards` 可选扫卡片（需遍历交战区 card_path）或维持 replay 侧单点 |
| G-17 | **matcher 子集无精确冻结**：契约 06"以 nuclei matcher 为范本"未定子集与组合语义 | 重放判定不可金样化 | R1 裁决落地（word/status/regex+AND+fail-closed），契约 06 微版本勘误 | 已随 T4 勘误；nuclei DSL 全集支持留引擎版本演进 |
| G-18 | **nday-verify 段映射缺位**：§6.3 kind→段映射表（v2 勘误新增 kind 后）未列 nday-verify | nuclei 引擎 intent 的方法论加载路径不明 | cli 型引擎无段文件（MANIFEST 即方法论入口），契约 07 映射表补注 | 契约 07 微版本注记：nday-verify→引擎=nuclei（cli 型，无 web-blackbox 段映射） |
| G-19 | **submission 无视角/引擎全局字段**：vuln-agent 需标注视角层级（L1 内部），schema 顶层无 perspective | 视角标注只能落在 findings[].network_position=same-host | T9 以 network_position 承载（够用） | 契约 v3 裁决是否增顶层 `perspective` 字段（涉及 147 字段口径外的提交 schema） |
| G-20 | **差分对数上限常量缺源**：§6.6"单端点差分对数上限"参数无契约依据 | 护栏参数漂移 | R6：模块常量 AUTHZ_DIFF_PAIR_CAP=24+--cap 覆盖 | 契约 v3 增常量（G-3 restart_rate_minutes 同通道） |
| G-21 | **session-viz 渲染库选型**：设计载 Cytoscape.js，vendor ~370KB 大文件与金样确定性/无网络安装相抵 | 渲染能力 vs 工程纪律 | R4：v1 零依赖 SVG+vanilla JS（视图五区硬语义全保留） | 批次 6 安装矩阵期裁决：接受 vendor 大文件（tools.lock 锁 sha256）或维持零依赖 |
| G-22 | **tools.lock 生产签名密钥与发布流程缺位**：本批测试钥进仓（TEST-ONLY） | 验签链信任根未建立 | 测试钥签名三键（快照锚定有效）；生产钥=批次 6 安装器出口 | 批次 6：生产 EC 钥生成/保管/重签流程+release.pub 替换 |
| G-23 | **set-replay-state 墙钟继承**（关联批 3 Minor-5）：check_cmds `_now()` 墙钟进账本，重放门转强制后该通道使用频率上升 | 时间戳非确定性（金样/审计弱化） | 本批零触碰（面变更需版本化） | 提前至契约 v3：set-replay-state 增 --timestamp 通道（checkpoint 先例） |

## 二、实施期增补（G-24..G-26，设计增补 commit 登记）

| # | 缺口 | 发现（设计增补） | 影响 | 本批处置（T14 收口） | 建议裁决 |
|---|---|---|---|---|---|
| G-24 | **severity_expect 类型基线表来源**（知识库 K1 方法论映射 vs 历史飞轮统计） | fb72cd5（优先级调度公式第一因子无源） | priority 算分缺机械输入 | T14：公式与 intents.priority 字段语义冻结（P3.md「派发优先级算分」节+契约 01 勘误——物理列随本项定案后落）；基线表未定前总控按矩阵词表类评定并留依据于 intent detail | 批次 5 知识飞轮定基线表来源；同批落 intents.priority 物理列（15→16 字段）+CLI 只读算分是否入面一并裁决 |
| G-25 | **Burp 粘贴格式边界**（HTTP/2 二进制帧、TLS 指定、Host 头与 Connection 归属） | b0006f2（FD 卡片规格 §一.6/§三） | POC 四要素的渲染/重放格式契约边界不明 | 本批 raw_request=HTTP/1.x 报文文本直发（R2 自解析，header 原文字序）；HTTP/2 二进制帧/TLS 指定未触 | 批次 6 报告渲染器定（FD 卡片规格 §三落点） |
| G-26 | **边词汇 10 条够不够路径语义**（infiltrate/pivot/exfil-ability 是否需细分权重/成本） | 71d3b7c（图谱驱动全程 §四） | graph-paths 攻击语义粒度不足则路径推导退化 | T7 前置：v1 映射冻结（R-G-2——attack={attack,proves,evidences}/asset={parent,scope-rel}/cred=凭据链，无向邻里仅 graph-neighbors）；细分未做 | 批次 5 知识飞轮定细分权重/成本（边语义 v2） |

## 三、状态归并台账（T14 收口终态，G-16..G-26 全量）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-16 | **已闭环·replay 侧单点** | T4 cards.check_consistency+T5 重放前校验（498d8c2）落地；validate --with-cards 可选扩展留契约 v3（建议裁决列原文维持） |
| G-17 | **已闭环** | R1 落地 T4（f8054dd）：word/status/regex+AND+fail-closed+condition 缺省 and；契约 06 微版本勘误+README 索引登记 |
| G-18 | **已闭环·本任务（T14）回注** | T9/T10 交付期处置=cli 型引擎 MANIFEST 即方法论入口（a4bb524/108c5ed）；契约 07 文末勘误补记「nday-verify→引擎=nuclei（cli 型，无 web-blackbox 段映射）」随 T14 收口回注（R-T9/T10 附记移交件） |
| G-19 | **已落地·过渡载体** | T9 network_position=same-host 承载（G-18 同批注记回注）；顶层 perspective 字段留契约 v3 裁决 |
| G-20 | **已落地** | R6：AUTHZ_DIFF_PAIR_CAP=24——engines/web-blackbox/phases/differential.md 护栏（T7）+phases/P3.md cred-obtained 回边（T14）双载；契约 v3 增常量待（G-3 同通道） |
| G-21 | **已闭环·v1 零依赖** | R4 落地 T11（7917fc4）：零依赖 SVG+vanilla JS，两次渲染字节一致，金样面 viz-data；Cytoscape.js vendor 复裁留批次 6 安装矩阵期 |
| G-22 | **测试链闭环·生产钥=批次 6** | T10（108c5ed）：TEST-ONLY 钥签名三键+templates.lock 钉 commit+逐文件 sha256，快照锚定有效；生产 EC 钥生成/保管/重签+release.pub 替换+upstream_commit 占位换真=批次 6 安装器出口 |
| G-23 | **开放·契约 v3 前裁决** | 本批零触碰（面变更需版本化）；set-replay-state 增 --timestamp 通道（checkpoint 先例）——批次 3 Minor-5 同族 |
| G-24 | **开放·批次 5**（语义已冻结） | T14：公式+intents.priority 字段语义冻结（P3.md+契约 01 勘误）；基线表来源+物理列（15→16）+CLI 只读算分=批次 5 与知识飞轮同批 |
| G-25 | **开放·批次 6** | 本批 HTTP/1.x 文本直发未触边界；渲染器定（FD 卡片规格 §三落点） |
| G-26 | **开放·批次 5**（v1 映射已冻） | R-G-2 v1 边语义映射冻结（f87ca25）；细分权重/成本=批次 5 知识飞轮 |

## 四、移交清单（后续批次开工前必办）

- **批次 5 前必裁决**：G-24（severity_expect 基线表来源——随批落 intents.priority 物理列+CLI 只读算分是否入面）、G-26（边词汇细分权重/成本——边语义 v2）。
- **批次 6 前必裁决/定标**：G-22（生产 EC 钥+重签+release.pub 替换+upstream commit 换真）、G-25（Burp 粘贴格式边界——渲染器）、G-21（Cytoscape.js vendor 复裁）；批次 3 遗留定标项 G-4/G-11 同窗。
- **契约 v3 回注待办**：G-16（validate --with-cards 可选）、G-19（submission 顶层 perspective）、G-20（AUTHZ_DIFF_PAIR_CAP 常量）、G-23（set-replay-state --timestamp）+批次 3 遗留 G-3/G-7/G-8。

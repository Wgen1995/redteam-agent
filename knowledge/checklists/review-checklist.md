# 知识页人审 checklist（批次 5；契约 14 §4 人工审载体）

> 定位：四门槛（复现≥2/跨目标有效/人工审批/无指纹泄漏）之外的质量判断——**铁律 7**，
> 语义判断不进 CLI（tanyin-knowledge 只查机械条件），本 checklist 就是人工审的执行面。
> 审批动作：`tanyin-knowledge approve --knowledge-dir <运行时库> --page=<id> --approver=<人>`。
> VulnClaw experience 人审门同模式（分析报告 §6.3：experience 蒸馏必经人审才入库，非全自动回流）。

## 审前定位（此页从哪来）

- [ ] staging_id / page_id / source_id 三账对得上（staging.tsv 与 SOURCES.tsv 闭合）。
- [ ] 语源已登记（SOURCES.tsv 行在场；外部语料 license 行非空）。

## 质量判断四问（逐项勾选，任一不过=reject 留档）

- [ ] **事实性**：正文断言可溯源——每条技法/结论能指回语源原文位置（CNPEN 复盘条目/
      VulnClaw detail-pack 章节/warstory 段落），无凭空引申；引用外部结论处注明出处。
- [ ] **可执行性**：按页操作可复现——触发条件、请求形态、判定标准三要素齐
      （失败模式与转向写清；"看情况"式描述退回重写）。
- [ ] **与词表对齐**：vuln_class 键落在 shared/VOCAB.md 支持集（细类= wstg-XX:subclass 形）；
      标题 ≤60 字且不带营销语气；vocab_version 与词表 version 行一致。
- [ ] **脱敏抽查三处原文**：正文抽三处疑似敏感原文（域名/IP/账号/路径/客户名），
      对照 client-map.tsv 确认已占位符化；scope_asset 为脱敏指纹而非真实目标
      （机检哨兵只拦已知形态，语义级残留靠此步人眼）。

## 占位符形态张力（P6 净草稿 vs 知识页；批次 5 评审 M-4 增补节）

- `{{vault:…}}` 占位符的合法性**随载体分两态**：P6 净草稿（报告/交战区工件）中
  `{{vault:cred-2}}` 系脱敏正当形态（契约 01 creds.secret_ref 白名单同源；R-T15-3——
  P5 管终稿零占位符、P6 管草稿零真值，双检语义不同层，互不矛盾）。
- 蒸馏进知识页时须替换为**抽象占位**（脱敏指纹/形态描述，如 scope_asset 的
  「占位符化域名/组件描述」）——`{{vault:}}` 形态不进知识页：lint 脱敏哨兵与
  promote ④「无指纹泄漏」对 vault 残留零容忍是**有意设计**（知识页=可发行资产，
  不得保留指向运行时密钥库的活指针）。人审见正文 `{{vault:` 即退回重写。

## 许可注记核对（外部语料页必做）

- [ ] sources/<语源>/LICENSE.note（或同位注记）在场；VulnClaw=MIT
      （Copyright (c) 2026 UncleC）；BugHunter/Threatswarm/CEP 执行期逐一核验后登记。
- [ ] 页内大段转载处有来源行；许可不兼容的素材不入页（宁缺毋滥）。

## 审后动作

- 过：approve（staging.tsv approved_by/approved_at 落列；log.md 追加 approve 行）。
- 不过：reject 附理由（rejected 终态留档 staging/，不删页——审计可追溯）。
- 晋升（learned→core）另走四门槛：机检三件（tanyin-knowledge promote）+ 本 checklist
  质量判断在晋升页再过一遍（四门槛只管机械条件，不管页写得好不好）。

## VulnClaw experience 人审门流程注记（批次 5 T17 增补节）

- 语源流程模式（vulnclaw/kb/experience.py 单源）：蒸馏产出的经验教训（Lesson）一律
  **"Lessons remain pending until a human approves them"**——自动化蒸馏不得把未经人审
  的战术回流进后续运行。与本库四门槛③（log.md 存在 approve 且 for=promote 才可晋升）
  同型：机器蒸馏止步于 pending，人工审批是唯一入库闸门。
- 近重复合并：语源 distiller 以 0.88 嵌入相似度为合并阈值（DEFAULT_MERGE_THRESHOLD=0.88）；
  本库检索 v1 为词表键+规范哈希精确匹配、无嵌入载体——语义近重复合并不实现（R10/G-30
  登记），lint 对同 class 页数 ≥8 输出人审合并建议告警替代（T17 首批 K5 恰 8 页即触发，
  属预期告警非 FAIL）。
- 外部经验页入库路径：staging 蒸馏页→本 checklist 质量判断四问→approve→commit；
  晋升 core 另走四门槛机检（tanyin-knowledge promote）。

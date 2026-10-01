---
name: verification-and-rating
description: 阶段2 验证与定级——**跟着候选发现阶段每一轮 drive 新产出的候选增量触发，不是等候选发现阶段整个项目跑完再一次性处理**（doc-64 批式流水线，见 candidate-discovery/SKILL.md 9c 步骤 6b）。对每个候选执行验证确认（FALSE-rules 前置剪枝 + 三要素语义注释 + 六项基线判定 + 四类控制评估 + 证据分级 + 三态结论 + 轻量第二意见复核），验证完成后紧接消费同一批证据完成严重度定级（impact×likelihood 矩阵机械查表 + 硬性抑制 + CVSS 3.1 映射）。产出可供报告交付、利用证明、修复指导、生命周期治理消费的定型结论，confirmed 的立即触发 report-delivery 产出该 finding 的详情文件，不攒批。不适用场景：候选发现阶段本轮尚未产出任何新候选（此时无事可做，等下一轮 drive）。
---

# 验证与定级（阶段2：验证确认 + 严重度定级）

- Verifier 看不见发现者结论（不把 verification-summary 或五段结论喂给 Verifier）。派发时删除 `discovery_reasoning_note` 列，只给 candidate_id / location / sink_type / 源码路径。
- 路径条件自相矛盾 → refuted，不是 confirmed。
- 同主体同结果：兄弟路径已给同一主体同一能力则不当新洞；缺权/IDOR 不适用。
- **触发粒度 = 每轮 drive 新增的 candidate 批次，不是整个候选发现阶段结束后的一次性大批次**：候选发现阶段可能跑几十上百轮 drive，每一轮 `live_findings_index.md` 里新出现的 candidate 就应该在本轮触发一次本阶段（哪怕只有 1 个候选），而不是攒到 `STATE=L1_CLOSED` 才一次性处理全部候选——这是"第一批候选跑完就该有第一份验证结论和详情报告"（doc-64 §4）的直接要求，不这样做等同于把批式流水线又退化回项目级瀑布。

## 触发时机

**每次 `session.py drive` 后，若 `live_findings_index.md` 相对上一轮出现新增 candidate（哪怕只有一条），本阶段立即针对这些新增 candidate 执行一遍下述步骤——不等候选发现阶段的其它卡分析完，也不等 `STATE=L1_CLOSED`。** 已经验证过的 candidate（无论 confirmed/refuted/unconfirmed）不重复验证，除非上游有 Follow-up 缺口回填了新证据。

## 目标

> v0.8.0 增补：
> - **未知留空**：证据缺失时 verdict 标 unconfirmed 并写明缺什么证据——**禁止编造证据补位**（与宁多勿漏不冲突：结论可保守报候选，证据不可编造）；
> - **验证强度分层自评（AIxVuln 吸收）**：tier6 静态推理时必须在 finding 写明「未闭环到运行时」的天花板——静态证据 ≠ 运行时确认；
> - **修复闭包去重判据（VVAH 吸收）**：两候选判定是否同根因的标准 = 「一个工程修复能否同时关闭两个」——能同时关闭则合并（同根因），否则分开。

本阶段回答两个先后相继、但不独立成两个步骤的问题：

1. 候选发现阶段产出的每个漏洞候选是不是真实、可利用的漏洞——把"是不是漏洞"拆成更窄、更可核查的子问题分别验证（三要素语义注释 + 六项基线 + 四类控制评估 + 证据分级 + 三态结论 + 轻量第二意见复核）；
2. 对验证确认完成的候选，直接复用步骤 1 已收集的证据（不重新调查、不重新从零论证），通过 impact×likelihood 矩阵机械查表锁定严重度与优先级，并把已确定事实映射为 CVSS 3.1 向量供下游消费。

> 顺序铁律：**矩阵先定性、CVSS 后映射，顺序不可颠倒**——CVSS 向量是矩阵定级结果的映射产物，不是第二次独立打分，也不得为凑分反推指标。

**诚实声明（必须保留，不得省略）：** 候选及验证定级字段、类型、条件必填规则以已落地的 [`../../contracts/data-structures/candidate-finding.md`](../../contracts/data-structures/candidate-finding.md) 为准，机器枚举以 [`../../contracts/enum-registry.md`](../../contracts/enum-registry.md) 为准。FALSE-rules 以 [`../../knowledge/FALSE-rules.md`](../../knowledge/FALSE-rules.md) 为准，命中即忽略。

## 输入

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 候选列表（候选发现产出） | 结构化列表 | 是 | 每条候选含 #3 字段段（candidate_id/source/控制点/sink 结构与 `severity_hypothesis_initial`）；涉及跨 WU 传播的候选须含 `cross_boundary_path`/`cross_boundary_path_ref` |
| WU 边界事实与跨 WU 汇聚产物（若启用 WU） | 结构化数据 | 条件必填 | 启用 WU 时必填；`propagatable`/`reachable_path` 核实跨 WU 传播完整性时消费 |
| 威胁语境文档（`threat-context.md`） | 文档引用 | 是 | 其 `severity_calibration` 小节与"要害资产"清单作为 impact 判断与仓库专属例子锚点的依据 |
| 目标代码库只读访问 | 环境 | 是 | 六项基线与三要素的静态核实基础 |
| 运行时验证环境（可选） | 环境 | 否 | 验证方法分级梯队第①-⑤级使用；不可用时不得作为"安全/证伪"证据，只记录"验证受阻，改用替代层级" |
| `knowledge_snapshot_id` | 快照引用 | 是 | 必须等于候选及 run 冻结的知识快照 ID |
| 独立第二意见执行上下文 | 角色/上下文 | 是 | 承担轻量第二意见复核，与分析方角色隔离，不能自我复核 |

## 硬性约束

1. **FALSE-rules 最高优先级**：任何候选一旦命中 [`../../knowledge/FALSE-rules.md`](../../knowledge/FALSE-rules.md) 列出的忽略场景，立即忽略、不再进一步分析；冲突时以 FALSE-rules 为准。命中记录写入 `false_rule_hit`。
2. **证据分级全局纪律**：结论强度不得超过证据链最弱一环。`confirmed` 需全要素直接证据（或大部直接 + 其余强间接且无反证，并注明最弱环）；仅凭间接推断"应该安全"不得定 `refuted`。
3. `confirmed` 只是验证终态，不自动产生 finding（需存在活攻击面且 `final_severity!=informational`）。
4. 缺乏运行时验证环境本身不构成"安全/证伪"证据，只记录验证受阻与替代层级。
5. 置信度必须从"用了哪一级验证方法 + 证据强度"推导，不能从漏洞类型可怕程度推导。
6. 严重度评估在验证确认完成后进行，直接消费六项基线证据，禁止重新调查；矩阵查表后禁止主观覆写。
7. 置信度与严重度始终是两个独立字段，不得合成单一加权综合分。

## 执行步骤

### 步骤0：FALSE-rules 前置剪枝（最高优先级）

在开始任何验证前，先对每个候选核对 [`../../knowledge/FALSE-rules.md`](../../knowledge/FALSE-rules.md) 的 8 类命中即忽略场景。命中 → 立即忽略（不产出候选、不进入验证、不进入 finding），在 `false_rule_hit` 记录规则、理由与证据引用。冲突时以 FALSE-rules 为准。

### A. 验证确认

1. **三要素语义注释**：先以三要素（必要条件）框定候选——可控源、可达路径、失效防护。三要素是六项基线 + 四类控制评估的语义注释，**不重复实现、不新增机器判定值**：`controllable_source` 注释 `controllable`，`reachable_path` 注释 `reachable`/`propagatable`，`failed_control` 注释 `control_assessment`。写入 `three_elements`。

2. **六项基线判定**：`reachable`（路径连得上）/ `controllable`（输入真攻击者可控）/ `propagatable`（传播/转换/存储链每跳连通，不含"未被净化"的统一定义）/ `exploitable`（危险操作真能被利用成声称效果）/ `reproducible`（能否具体演示）/ `impact_there`（真利用后真造成后果）。每项独立写机器值 `pass`/`fail`/`unconfirmed`/`not_applicable`，附 `evidence_grade`（`direct`/`indirect`/`unknown`）与证据引用；`not_applicable` 附适用性理由。**Guard/Sanitizer/Encoder 有效性由 `control_assessment` 独立判断，不混入 `propagatable` 基线**。

3. **四类控制分别评估（`control_assessment`）**：Guard、Policy Decision、Sanitizer、Encoder 四类控制分别独立评估，**不合并为笼统"安全控制"**。每个子对象记录 `{applicability, expected_control, observed_control, failure_or_bypass, result, evidence_grade, evidence_refs}`；`not_applicable` 时省略 `expected_control`/`observed_control`/`failure_or_bypass` 并附 `applicability_reason`。四类各自独立判定 `result`，不因一类 effective 就默认另一类 effective。
   **部署配置上下文强制核查（2026-08-14 实跑新增）**：对"缺认证/无认证/配置类"候选（管理端点、JMX、Manager、AJP secret 等），Guard 评估必须读取部署配置证据（web.xml security-constraint、RemoteAddr/RemoteCIDR 限制、默认配置的开关与默认值、网关/代理限制），写入 observed_control 与 evidence_refs。**未核查部署配置的"无认证"候选不得定 confirmed，一律 unconfirmed**（详见 `knowledge/FALSE-rules.md` 规则8）。

4. **候选专属校验清单**：针对候选具体漏洞类型定制专属核查点，显式对象 `{applicability, reason, items}`，`items` 每项含 `check`/`result`/`evidence_grade`/`evidence_refs`；禁止真空通过（`items=[]` 且 `applicability=applicable` 不合法）。

5. **验证方法分级梯队**（动态验证边界，按顺序有序尝试，前一级不可行才降级）：①崩溃PoC → ②valgrind/ASan → ③非交互调试器 → ④单元/集成测试 → ⑤真实接口复现 → ⑥静态代码理解 → ⑦大型仓库模式。每个实际使用的方法写入 `verification_methods[]`，逐项绑定 `method`/`tier`/`evidence_mode`/`evidence_refs`/`downgrade_reason`/`blocked_reason`；**缺运行时环境本身不算证伪/安全证据**。

6. **证据分级标注**：每个关键判断逐项标注 `evidence_grade`——`direct`=读到代码原文（文件:行号+片段）；`indirect`=命名/上下文/框架惯例推断；`unknown`=信息缺失（缺口可补则先补再判，不可补则写清缺口）。

7. **三态结论（`verification_verdict.value`）**：
   - `confirmed`：全要素直接证据（或大部直接 + 其余强间接且无反证，注明最弱环）；可利用漏洞须六项适用基线全 `pass`；无活攻击面代码事实允许 `reachable`/`exploitable`/`impact_there` 为 `fail`/`not_applicable`，但须定级 `informational`。
   - `refuted`：前提缺失（关键要素不成立）或明确反证成立；仅当 `value=refuted` 时同对象内写非空 `refutation_category` 与 `refutation_evidence_refs`；仅凭间接推断"应该安全"不得定 `refuted`。
   - `unconfirmed`：前提在但关键要素无法确认（对齐 SUSPECTED 语义）——写清**缺口位置**与**所需证据**，不因信息缺失硬判 confirmed 或 refuted。

8. **轻量第二意见复核**：每候选执行一次轻量第二意见（独立角色，不得自我复核），重点核对（a）FALSE-rules 是否被误杀或漏杀；（b）证据分级是否与证据强度一致。High/Critical 候选可选叠加**对称反转复核**：推翻 VULN（confirmed）需证伪三要素/六项基线之一并给出直接证据；推翻 NOVULN（refuted）需构造可实施攻击路径（payload 穿透全部校验点实际到达 sink）。复核结论与分析方不一致时，取最保守（最低置信）状态合成。写入 `second_opinion_review`。

### B. 严重度定级（验证完成后的子步骤，直接消费步骤 A 证据）

1. 步骤 A 判为 `unconfirmed` 的候选，严重度定级随验证终态一起搁置。
2. 回顾 `severity_hypothesis_initial`（阶段1 假设），在其基础上用步骤 3-4 的仓库证据事实调整。
3. impact 判断（`impact_rating`：high/medium/low/ignore/unknown），关联"要害资产"清单与 profitability 子考量；仅 impact=high 且 likelihood=high 时写 `critical_criteria_met:boolean`。
4. likelihood 判断（`likelihood_rating`），复用六项基线（尤其 reachable/controllable/impact_there）证据，`exposure` 用 `exposure_scope`，不另开调查。
5. 双层例子锚点校验（通用反虚高清单 + 仓库专属例子）。
6. **硬性抑制规则**（先于矩阵查表）：命中"仅影响自己""前置条件不现实""需已拿到管理员/root 且非提权"时 `likelihood_rating.rating=ignore`，`suppression_flag.reasons` 记录原因；存在真实跨信任边界影响时不得抑制。
7. **矩阵查表锁定 `final_severity`**：严格引用 [`../../contracts/enum-registry.md`](../../contracts/enum-registry.md#final_severity) 权威矩阵机械查表，禁止复制矩阵、查表后重新论证或凭感觉调整。
8. 优先级映射：critical→P0 / high→P1 / medium→P2 / low→P3；ignore 不产生 priority。
9. **CVSS 兼容性导出**：把步骤 3-7 已确定事实按 CVSS 3.1 指标逐项映射为完整向量；未确定指标不得猜测，不得产出不完整向量。
10. **配置越界关卡（v0.3.9，五步链第 4 步显式化）**：每个候选必须产出「默认配置可达性」结论——默认配置下前置条件是否满足（组件是否默认启用、关键选项默认值、认证要求），附 conf/ 或代码默认值证据行；CVSS 的 AV/PR/AC 必须与该结论一致（默认关闭的配置脚枪不得 PR:N/AV:N；集群未默认启用不得直接 9.8）。结论写入验证段，finding 控制评估表投影新增一行「默认配置可达性」。
11. **confirmed 阈值（v0.3.9）**：`runtime_tier=6`（纯静态）下 confirmed 须 confidence ≥ 0.6 且三要素证据级全 direct；tier 4/5 须 ≥ 0.7；tier 1-3 须 ≥ 0.8。低于阈值禁止判 confirmed（改 unconfirmed 或 blocked 附 capability_gap_refs）。置信度由阶梯逐项推导写出，禁止套版固定值。

### C. 阶段 Gate

1. Gate-1：候选清单每个 ID 在本阶段恰好出现一次，进入 `verification_verdict` 三态之一，每条有证据分级与轻量第二意见；confirmed 附带 `confidence`/`evidence_grade`/`runtime_tier` 三字段（machine-fields 扩展）且过阈值（步骤 B.11）。
2. Gate-2：轻量抽查——核对 FALSE-rules 误杀、证据分级一致性、矩阵查表正确性；只查阶段复核未覆盖的遗漏。
3. 产物：单一 `verification-summary.md`（禁止拆分成多个 verification-*.md 文件），每个候选段的 `candidate_id` 锚点必须与 candidates.tsv 的规范 ID 一致（Gate-1「引用可解析」校验 verification_record_ref；本文件由宿主 shell §4c 对账）。
4. **verdict 必须同步回 candidates.tsv，不能只写 verification-summary.md**：真实 dvpwa 冒烟跑暴露过这个问题——candidates.tsv 自己的 `verdict` 列全程为空，导致 gate[V 文件候选映射] 因为找不到任何 confirmed 行而空转通过，完全没抓到同批次里真实存在的 finding 文件名违规。Verifier 完成验证后必须写一份自己的分片 `verification_shards/{verifier_id}-verdicts.tsv`（表头 `candidate_id\tverdict\tverification_record_ref`，`verdict` 取值 `confirmed`/`refuted`/`informational`/`suppressed`），不要直接改 candidates.tsv（并发写会竞态）；`session.py drive` 每轮自动归并（`ingest_verification_shards`，`VERDICTS_APPLIED=N`）。

## 输出

每个候选的定型产出字段由 [`../../contracts/data-structures/candidate-finding.md`](../../contracts/data-structures/candidate-finding.md) 定稿。完整产出携带 `stage_result`、`version`、`resume_context`：

| 字段 | 说明 |
|---|---|
| stage_result / version / resume_context | 产物执行状态、契约版本、断点续跑上下文 |
| confidence 推导表（v0.3.7，设计 36 号 §3） | confidence_score 从验证方法机械推导，禁止从漏洞类型可怕程度推导：静态分级证据链（证据链五段齐+最弱环 direct）0.3+；静态七元组齐（source/control/sink/reachability/boundary/counterevidence/proof-gap）0.5+；加测试命中 0.7+；调试器/接口复现 0.8+；ASan 复现 0.9+；崩溃 PoC 复现 1.0。缺动态环境时诚实写静态档并披露。七元组（source/control/sink/reachability/boundary/counterevidence/proof-gap）与六基线（reachable/controllable/propagatable/exploitable/reproducible/impact_there）对应：source 对应可控源（controllable_source 注释 controllable）、control 对应失效防护（failed_control 注释 control_assessment）、sink 对应危险汇点事实、reachability 对应 reachable、boundary 对应 propagatable 跨边界传播、counterevidence 对应反证（disproof_checked）、proof-gap 对应证据缺口（unconfirmed 的缺口位置）；reproducible/impact_there 由 sink/counterevidence 段事实支撑。 |
| three_elements | 三要素语义注释（controllable_source/reachable_path/failed_control），不重复实现 |
| verification_baseline | 六项基线各带 result + evidence_grade + evidence_refs + applicability_reason |
| control_assessment | 四类控制分别评估（guard/policy_decision/sanitizer/encoder），各带 evidence_grade |
| candidate_specific_checklist | 候选专属校验清单，每项带 evidence_grade |
| verification_methods | 分级验证方法数组 |
| confidence_score | {value, threshold, threshold_passed, rationale}，与 severity 分离 |
| false_rule_hit | FALSE-rules 命中记录（命中即忽略的留痕） |
| verification_verdict | 三态 value + evidence_grade；仅 refuted 时携带 refutation_category/refutation_evidence_refs |
| second_opinion_review | 轻量第二意见 + High/Critical 可选对称反转 |
| impact_rating / likelihood_rating | impact/likelihood 档位 |
| suppression_flag | 硬性抑制命中记录 |
| final_severity / priority | 矩阵查表结果与优先级映射 |
| cvss_vector | 由同一批事实映射的 CVSS 3.1 向量 |

**零候选时的兜底产出规定**：若没有候选进入本阶段，写 `stage_result=not_applicable`，输出 stage envelope：`input_count=0`、`records=[]` 和非空 `zero_input_reason`，不得虚构 candidate 记录或 ID。产物文件不得省略。

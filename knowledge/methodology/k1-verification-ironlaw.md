---
id: K1-M02
kind: methodology
class: K1
title: 验证铁律——证据即漏洞，负结果落库防重复打点
csai_ref: CyberStrikeAI skills/pentest-verification（对照改写，证据 docs/research/2026-10-21-csai-full-sweep.md §29）
vocab_version: WSTG-v4.2
last_verified: 2026-10-21
---

> 本页为方法论正文（对照 CSAI skills/pentest-verification 改写为我方语境，不照抄
> 不机翻）：其五条铁律全数吸收，另增我方证据双轨与复验两条，共八条。

## 方法论

1. **情报≠漏洞。**搜索结果、公开 CVE、组件指纹、PoC 线索，任何「别人说有」
   都不可直接报发现，也不可当已验证事实写死；只可落 fact 线索（低置信浮点）
   或留待验证方向（意图），验证后才升格。
2. **证据即漏洞（我方铁律 4）。**无可复现步骤（reproducible_steps≥1）的观察
   一律是 fact 而非 finding；证据不带复现命令与内容哈希（raw+norm 双轨）
   不算证据。
3. **确认须证据钉死。**每条升级为发现的结论必须挂证据（evidence_ids 指向
   证据行）：命令输出、HTTP 响应、文件内容、回连记录任一形态，凭据一律
   占位符化。
4. **禁止「可能/疑似/推测」当结论。**要么确认+证据报发现（C1/C2/C3 分级），
   要么标疑似挂线索（fact 或矩阵 ? 格），要么不报。确定性不等于危害——
   两维评级 confidence×impact 正交呈现；C2 须附条件可达性证据，缺证据降 C3。
5. **负结果落库，防重复打点。**验证失败不是白打，三级落点：
   - 格级：matrix 猎格置「-」（不适用，附理由）或「!」（环境干扰，附记录），
     同格不重测；
   - 事实级：黑板落负结果事实（已验证态+已测条件写清），跨会话防重复打点
     （负面结果入账本 facts 的 W3c 律同源）；
   - 复盘级：战后蒸馏避坑卡（knowledge/negative），跨仗防重复踩坑。
6. **想象力拉满，单步验证零容忍。**敢想账本上没人串过的链（能力凑链见
   K1-M04）；链的每一段都要用真实证据钉死后才算数——推导出的链是假设
   （黑板 tentative 记），逐段验证后才转 confirmed。
7. **已验证会过期。**verified 发现按复验窗口进复验池，盲重放三态
   VERIFIED/REPAIRED/REJECTED；过期不验=发现贬值，重放拒绝=降级或转 fact。
8. **授权先于验证。**验证铁律运行在授权窗口与范围红线内：范围外资产上的
   「疑似」不测不打不记，线索走审批；越权取得的「证据」不算证据。

## 适用场景

- 战士落账前自检：报发现/写事实前逐条对照本页（尤其 1/2/4 三条）；
- 规划者研判：负结果格不再派单（矩阵饥饿因子天然避开历史碰过的格）；
- 复测与报告：复验窗口判定、报告渲染前的证据完备检查；
- 复盘蒸馏：负结果与误报进避坑卡草案的质量闸（ledger_ref 必须指真实账本行）。

## 对接说明

本节为说明性对接说明，零引擎接线（内容件，注入位属 U3 舰）：

- 评级面：findings.tsv confidence 枚举 {C1,C2,C3,排除项}×impact{高,中,低}；
  C2 强制证据在册（写命令门），排除项如实记录不隐藏。
- 证据面：E-index.tsv（repro_command/content_hash 双轨/network_position）+
  外置 EV 卡（POC 四要素：网络位置/前置条件/原始请求/预期结果）；凭据占位符
  纪律由 redact 哨兵强制。
- 负结果面：matrix.tsv 置格命令强制「-」「!」附理由；黑板三命令
  （blackboard-upsert/deprecate/restore，U3 件）承跨会话负结果事实；
  knowledge/negative 避坑卡经蒸馏管线（误报/漏报族/负面披露三路草案）人工
  确认入册（棘轮门）。
- 复验面：retest 三命令（retest-pending 过期清单/retest-scan 复验卡走
  add-intent 通道/retest-settle 三态回写），复验判定单源在重放侧。
- 渲染面：report_render 渲染门强制类型命中词表、证据字段完备——本页铁律
  1/2/4 是其行为面依据（内容件，不接线）。

# 蓝图对账表（BLUEPRINT-RECON · 2026-10-15 · 起因： 主会话差点把已建成的知识飞轮当新设计）

> **蓝图巡检律（本表即执行）**: 任何设计提案前，必须先查 docs/design/ + docs/superpowers/plans/ + knowledge/ 三处，引用已存在的设计与实现，标注「已建/部分/未建/已并入/已超越」。违律=提案作废。

## 设计档对账（docs/design/ 24 件）
| 档 | 状态 | 与当前路线的关系 |
|---|---|---|
| tanyin-product-v1.md | **现行宪法** | 产品定义+修正案 ABC（白盒双车道/Go 边车触发器/共创模式）|
| ui-design-v1.md | 现行 | v0.9d 执行依据（侧栏骨架+12 级灰阶）|
| tanyin-target-form.md | 已超越（法律仍有效）| 五律/语言律由 product-v1 继承 |
| architecture-map-v3.md | **维护中** | 蓝图双胎（每批同步）|
| engine-fusion-architecture.md | §1-5 已建（judge/llmpool）;**§6 循环层=v1.0b 素材** | 自主循环设计必须对照 §6 |
| **graph-driven-ops.md** | 部分建（十边图）| **v1.0a 双图一桥设计前必读**——图驱动作业早有设计 |
| **completeness-recon-knowledge-evolution.md** | 已并入 b5 飞轮 | 知识演化思考已在库，知识类新提案先查它 |
| **fd-report-card-spec.md** | 已建（FD 渲染/evices 账）| v0.9d 总览「最新发现列表」直接复用其规格 |
| **finding-stream-priority.md** | 已建 | 同上——发现流优先级已有定稿 |
| endpoint-dict-v2.md | 已建（战斗在用）| 白盒车道 A 的端点字典底座 |
| vuln-agent-engine / gencpt-suite / bprime-fusion / v2-design | 谱系已超越 | 历史 lineage（演进脉络参考）|
| 2026-09-2x b3..b8 discovery-notes ×6 | 批次收口归档 | 勘探台账 |
| expert-review 两份 + eight-expert-b10 | 已整改（b7 批）| 评审债已清 |
| html/ imported/ | 资产 | — |

## 计划档对账（20 件）
批次 1→v0.9d 全部收口在案;**例外**: 2026-10-09-b11-gateloop-experiment.md——**计划在库未执行**（闸门实验真身在此，v1.0b 前执行;我此前说"闸门待设计"是没查库）。

## 知识飞轮资产（已建成!差点被重新设计）
- 库: knowledge/ 15 目录（concepts 8 页/precedents 5 页/patterns 2 页/retros/checklists/staging/graph.ndjson/log.md 190 行）
- 命令面: tanyin-knowledge（promote 四门槛+approve 人审门）+ tanyin-evals
- 已喂: PR-0005 飞轮回写/RT-0001 归因核验/b0d0bed 喂养战例
- **v1.0 连接点（新提案仅此一条）**: 规划者循环（v1.0b）把 knowledge/ 作检索源注入战士 brief——飞轮本体已建,缺的只是自主循环这双"腿"。

## 结论
本会话三处险些重造轮子: 知识飞轮（已建）/FD 卡与发现流（已建,总览页应复用）/闸门实验（计划在库）。根因=只读 HANDOFF 尾不巡全图。此表+巡检律入档,每批开工前重读。

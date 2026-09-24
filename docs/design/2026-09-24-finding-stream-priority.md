# 实时发现流与优先级调度（批次 4 设计增补）

> 回答两个问题：发现的漏洞怎么实时可见？测试顺序怎么保证高危/高价值先行？

## 一、实时发现流（作战视图 ≠ 合规交付）
- 事实源不变：add-finding 即时落账（findings+timeline finding-added），账本就是实时流——缺的是"人看得见"的投影。
- 落地：session-viz（批次 4 T11）增 findings 实时流投影——按 tanyin-viz 数据面输出最新 N 条（时间/资产/类型/severity/状态），值守者 watch 刷新即见；高危条目置顶+标记。
- 边界纪律：实时流=作战视图（内部）；对外交付仍走 P5 报告签发门（实时披露≠合规披露）。
- 触发联动（已有触发器闭包）：severity=high/critical 的 finding 落账→立即生成"同型横向排查"intent（同类资产全量补格）——高危发现不等收敛轮，即时扩面。

## 二、优先级调度（先测高危/高价值）
- 派发排序公式（确定性算分，读账本即可算，攻击决策仍在总控）：
  score = severity_expect(类型基线) × asset_value(assets.meta 业务价值) × exploitability(可达性/凭据在手/历史先例命中)
- intents 增 priority 字段（契约微版本）；P3.md 派发规则改写：每轮从 pending intents 按 score 降序取 Top-K（K 由预算/并行度定），高危路径先行。
- 高危先行的三件套：①排序如上 ②高危 finding 即时横向（上节）③止损语义：budget-exhausted 收敛时，未测格子按 score 降序披露"未覆盖的代价"（报告的整改优先级与调度同公式——一套分值两头用）。
- 人握方向盘不变：立项时资产业务价值由人标（assets.meta），排序是被解释的算术不是黑箱。

## 三、落点
- 批次 4 内：T11 session-viz 加 findings 流投影；T14 收口时 P3.md 派发规则+intents.priority 契约勘误（若 T14 前有更合适的任务位则顺手）。
- 探知项：G-24 severity_expect 类型基线表来源（知识库 K1 方法论映射 vs 历史飞轮统计——批次 5 定）。

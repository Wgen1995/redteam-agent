# 图谱驱动全程：图查询与攻击路径推导（批次 4 设计增补）

> 原则：账本图谱=渗透的操作系统。每一步从图来（调度=图推导），回图去（落账=长边）；无图外状态。

## 一、图谱支撑全程的闭环（已有设计盘点）
- P0 立项=scope 入图；P1 侦察=资产入图（A1-A8+界外也记）；P2 矩阵=图投影锁定分母；P3 作战=图演进循环（风暴五路=图上找缺口，资产事件=图生长，收敛=图闭合）；P4 复核=重放门回写三态；P5/P6=图投影交付与沉淀。断点续传=图快照（state snapshot）；优先级调度=图上算分（fb72cd5）。

## 二、缺口：图查询与路径推导命令面（本增补核心）
调度与研判需要确定性图运算（铁律 7"账本运算"允许类），新增 tanyin-ledger 图查询面（三命令，只读）：
1. graph-neighbors --asset <id> [--depth N] [--edge-class ...]：邻接展开（攻击面/资产/凭据边过滤）——总控研判"这个立足点周围有什么"
2. graph-paths --from <asset|cred> --to <asset|scope-root> [--max-hops N]：可达路径枚举（边按攻击语义：infiltrate/priv-esc/pivot/exfil-ability）——回答"从当前权限到目标还有几条路"，路径=攻击计划的骨架
3. graph-horizon --from <foothold>：当前立足点的可达集+可达但未测集合（与矩阵 join）——直接喂 P3 派发排序（score×图可达性加权：够得着的空格优先）
实现位：cli/ledger/query_cmds.py 或新 graph_cmds.py（41 面增补走微版本勘误，同 G-1 先例）；确定性输出可金样化。

## 三、与调度/收敛的咬合
- P3 派发：Top-K 候选=graph-horizon 可达空格 × priority score 降序——"图上够得着的高分格"先行
- 收敛判定补强：converge-check 增加"无可达未测格"作为停机条件之一（图结构性的覆盖，与矩阵格覆盖互补）
- 攻击路径进 EV：finding 关联的 graph-path 落 evidence（入口→横向→命中的链），报告"涉及资产与接口"段渲染路径子图（FD 卡片规格第 2 段升级）

## 四、落点
- 批次 4：T7（web-blackbox 引擎消费 graph-horizon 驱动侦察/测试段）、T14 收口接线三命令入 SKILL/P3.md+契约勘误
- 批次 6：session-viz 渲染攻击路径子图
- 探知项 G-26：边词汇 10 条够不够路径语义（infiltrate/pivot 等是否需细分权重/成本）——批次 5 知识飞轮定

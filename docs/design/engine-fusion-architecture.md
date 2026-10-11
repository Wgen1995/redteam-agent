# 引擎融合架构 · vuln-agent 输出如何融入渗透（v0.5 接线设计稿）

> 状态： 设计定稿待批（2026-10-11，用户设计输入驱动）。原则先行，接线批按此施工。

## 0. 一句话定位

**引擎不产发现，产假设。** 源码审计的 sink/污点路径/净化覆盖是「情报」，必须经黑盒实证
才配成「发现」——精度门（无重放不计分）对引擎情报一视同仁。融合点是 **intents 层**（意图池），
不是 findings 层：引擎假设与战士自产意图同池竞争预算，走同一条 探→验→记→矩阵消格 闭环。

## 1. 为什么不是「简单 CLI 调用」

| 天真做法 | 破坏什么 |
|---|---|
| 引擎结果直接 import 成 findings | 精度门崩——未实证的静态断言污染账本，烂帐=0 分定律连坐 |
| warrior 读引擎 JSON 全文 | 上下文洪水；引擎不懂预算，战士丢自主性（N=5 教训：过度约束无增益） |
| 一次性调用无反馈 | 同一 sink 反复假设；已证/已否情报不复用；引擎不学习 |

## 2. 六段精炼管线（fusion pipeline）

```
 代码级情报（sink/污点链/净化覆盖/死代码）
   ↓ ①Refiner 情报精炼（引擎侧）
 意图卡（structured hypothesis）：端点+参数+载荷配方+前置条件+置信度+code:L114 溯源
   ↓ ②Intent 入账（账本侧）
 intents.tsv kind=engine-hyp provenance=vuln-agent:order.php:L114
   ↓ ③预算仲裁（战士侧）
 意图池统一排序：优先级=置信度×矩阵新颖度×可达性；engine-hyp 配额≤40%（保自主广度）
   ↓ ④探针转化（phases）
 recipe → 具体 probe 步骤（复用现有探针纪律：探针前置/范围检查）
   ↓ ⑤黑盒实证（不变）
 E-index 证据卡+重放三态——与自产发现同一精度门
   ↓ ⑥反哺闭环
 发现/否证回灌引擎：已证 sink 打标Verified；否证降权；edges cross_ref 全链可溯
```

## 3. 账本映射（全部复用既有表，零新表）

- **intents.tsv**: kind=engine-hyp（要么验证要么 blocked——「不许蒸发」律天然管住引擎假设的生命周期）
- **facts.tsv**: kind=engine-static（净化覆盖/死路由——可消费的**否定性知识**：省掉不必打的探针）
- **edges.tsv**: cross_ref（engine-hyp ↔ 最终 finding）——审计链可答「这发现源头是哪行代码」
- **E-index/重放**: 引擎假设实证后的证据卡与黑盒证据同规格——settle 评分零特判
- **budget**: engine-hyp 消耗计入统一预算（引擎调用自身也计——两段式异步不白嫖）

## 4. 异步纪律（承接已入账四原则）

提交即返/领取不等/wall 超时显式/账本两相——引擎小时级任务在侧轨跑，意图卡到点入池。
超时 GIVEUP 的 engine-hyp 显式 blocked（不蒸发）。

## 5. 验收与实验设计

- sim 场景： 注入 10 枚引擎假设（7 真 3 假）→ 战士须只实证 7 真、3 假走 blocked——精度门连坐测试
- 双臂（未来）： 有引擎情报臂 vs 无——测「情报增益」是否显著（McNemar 协议复用）
- 防退化钉： engine-hyp 直入 findings = selfcheck 红线（扫描器级断言）

## 6. 施工顺序（接线批）

1. 意图卡 schema（refiner 输出契约）+ 3 测
2. intents kind=engine-hyp 通道 + 预算仲裁配额 + 5 测
3. sim 注入场景 + SIM_PASS
4. codex E2E 一战（真源码真情报）
5. 反哺通道（发现→引擎打标）

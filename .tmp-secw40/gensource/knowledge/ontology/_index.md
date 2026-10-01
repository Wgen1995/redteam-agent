# 本体索引（ontology/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务2。本文件按规格链路排列17个核心本体概念，供审计Skill按数据流方向查阅。

## 规格链路

本体概念按以下规格链路排列，对应数据从进入系统到产生安全影响的完整路径：

```text
Asset / Trust Boundary → Surface → Entry → Source → Propagation / Transformation / Storage → Guard / Policy Decision / Sanitizer / Encoder → Sink / State Transition / Resource Consumption → Observable Oracle → Security Impact
```

## 概念索引表

| 稳定ID | 概念 | 文件 | 链路位置 |
|---|---|---|---|
| ONT-ASSET | 资产 | [concepts/ONT-ASSET.md](concepts/ONT-ASSET.md) | 1. 被保护对象 |
| ONT-TRUST-BOUNDARY | 信任边界 | [concepts/ONT-TRUST-BOUNDARY.md](concepts/ONT-TRUST-BOUNDARY.md) | 1. 信任划分 |
| ONT-SURFACE | 攻击面 | [concepts/ONT-SURFACE.md](concepts/ONT-SURFACE.md) | 2. 外部接口 |
| ONT-ENTRY | 入口 | [concepts/ONT-ENTRY.md](concepts/ONT-ENTRY.md) | 3. 数据进入 |
| ONT-SOURCE | 数据源 | [concepts/ONT-SOURCE.md](concepts/ONT-SOURCE.md) | 4. 数据来源 |
| ONT-PROPAGATION | 传播 | [concepts/ONT-PROPAGATION.md](concepts/ONT-PROPAGATION.md) | 5. 内部流动 |
| ONT-TRANSFORMATION | 转换 | [concepts/ONT-TRANSFORMATION.md](concepts/ONT-TRANSFORMATION.md) | 5. 形态变换 |
| ONT-STORAGE | 存储 | [concepts/ONT-STORAGE.md](concepts/ONT-STORAGE.md) | 5. 持久化节点 |
| ONT-GUARD | 守卫 | [concepts/ONT-GUARD.md](concepts/ONT-GUARD.md) | 6. 授权决策点 |
| ONT-POLICY-DECISION | 策略决策 | [concepts/ONT-POLICY-DECISION.md](concepts/ONT-POLICY-DECISION.md) | 6. 策略逻辑 |
| ONT-SANITIZER | 净化器 | [concepts/ONT-SANITIZER.md](concepts/ONT-SANITIZER.md) | 6. 输入验证 |
| ONT-ENCODER | 编码器 | [concepts/ONT-ENCODER.md](concepts/ONT-ENCODER.md) | 6. 输出编码 |
| ONT-SINK | 汇点 | [concepts/ONT-SINK.md](concepts/ONT-SINK.md) | 7. 危险操作 |
| ONT-STATE-TRANSITION | 状态转换 | [concepts/ONT-STATE-TRANSITION.md](concepts/ONT-STATE-TRANSITION.md) | 7. 状态变更 |
| ONT-RESOURCE-CONSUMPTION | 资源消耗 | [concepts/ONT-RESOURCE-CONSUMPTION.md](concepts/ONT-RESOURCE-CONSUMPTION.md) | 7. 资源使用 |
| ONT-OBSERVABLE-ORACLE | 可观察预言机 | [concepts/ONT-OBSERVABLE-ORACLE.md](concepts/ONT-OBSERVABLE-ORACLE.md) | 8. 后果观察 |
| ONT-SECURITY-IMPACT | 安全影响 | [concepts/ONT-SECURITY-IMPACT.md](concepts/ONT-SECURITY-IMPACT.md) | 9. 损害后果 |

## 关键概念区分

### Guard / Sanitizer / Encoder 三者独立

这三个概念分别定义、分别举例、分别说明排除边界，不得互相替代或混为一谈：

| 概念 | 核心语义 | 作用位置 | 关心的问题 |
|---|---|---|---|
| ONT-GUARD | 主体是否有权执行动作 | 授权决策点 | "主体有没有权限" |
| ONT-SANITIZER | 输入验证/规范化/净化 | 输入侧 | "输入是否合法/安全" |
| ONT-ENCODER | 特定输出上下文安全编码 | 输出侧 | "输出怎么编码才安全" |

## 关系类型

概念之间的关系类型登记在 [relation-types.md](relation-types.md) 中，共20种关系类型。这些关系只是Markdown引用，不是运行时图。

## 消费方

- `scope-and-context`：范围与威胁语境能力按链路顺序消费本体概念，构建攻击面地图
- `candidate-discovery`：候选发现能力按Source→Propagation→Sink链路追踪数据流
- `verification-and-rating`：验证与定级能力评估Guard/Sanitizer/Encoder三类控制是否正确
- `remediation-guidance`：修复指导能力按控制类型（Guard/Sanitizer/Encoder）提供针对性修复

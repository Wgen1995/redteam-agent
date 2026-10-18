# promo-logic ｜ 促销与优惠券业务逻辑（CWE-840 变体 · CWE-362 检查-提交窗口）

> band: 0 ｜ 轨道: B（不变式轨——不走 pattern 主轨，判定主体在 invariants/retail.inv INV-001/002/013/014）｜ 模式表: `patterns/promo-logic-java.pattern`（**弱锚**，仅定位促销相关代码族）｜ fixture: `fixtures/enum/promo-logic/java/`（判据类，fixture 以 java 代表，ts/python 待 S2）
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 检查-提交窗口无兜底且可并发薅取（用量/核销/发行超限）→ High；客户端定价直达（金额正确性破坏）→ High；单次多领但单券损失有界（面额封顶）→ Medium（前提引文）
> oracle: none ｜ reasoning-only ｜ human-triage: required（A-012/A-035/B-033——本类无机械/执行 oracle，判定主体在业务不变式：裁决照常落账但结论 reasoning-only，机械字段标 human_triage，最终裁决显式交人工 triage）

## ① 定义与危害
促销/优惠券的正确性依赖业务不变式而非内存安全：金额必须服务端算、用量必须原子记、核销必须单次、叠加必须单点裁决。违反形态=检查与提交之间存在并发窗口（TOCTOU）或金额字段被客户端直写。危害=限量促销被并发薅穿（CVE-2025-69871：MedusaJS ≤v2.12.2 `registerUsage()` 检查用量与自增非原子，并发 checkout 全部通过限额检查）、订单金额被篡改、优惠券重复核销。**本类 sink 弱（`redeem/discount/coupon` 是业务词不是危险 API），pattern 只当定位锚，安全/危险由 ⑥ 判据 + INV 条目判别。**

## ② Source
促销码/优惠券码（请求体 code 字段、路径短码）、购物车快照、客户端回传的金额字段（total/discountedPrice/discountAmount——**这是 INV-001/004 的违反证据形态**）、列表页回显的他人券码（persisted_read 二阶：上周领的券码本周被重放）、并发重放的同一 checkout 请求（同一 source 重复到达=竞态问句的输入面）。

## ③ Sink 模式表指针
`patterns/promo-logic-java.pattern`（机器直读，逐行一条，不并串）。锚形态：`redeem(`/`CouponCode`/`discount`/`applyPromotion|applyCoupon|applyDiscount(`/`registerUsage(`/`usageCount|redemptionCount`/`coupon|promotionRepository`。**弱锚声明：命中只证明"促销相关代码族"，无任何一锚单独构成危险**——`discount` 在展示层大量出现，命中后的判定走 ⑥；枚举宁多勿漏，噪音登记进 noise 目录。

## ④ Propagator
促销上下文透传链：controller→cartService→pricingService→promotionEngine 的 code/规则 id 传播；客户端金额字段经 DTO 直入订单实体（mass assignment 通道，INV-004 主通道）；回显-再提交链（券码从响应体回流请求体）。

## ⑤ 兜底机制（本类的"Sanitizer"——决策表三值）
```
DB 唯一约束((coupon_id,order_id) 唯一索引/领券 (template_id,user_id) 唯一) × 核销/领取写入 × 冲突即回滚        → 强
悲观锁(SELECT ... FOR UPDATE / entityManager.lock) × 用量检查与写入同事务               → 强
乐观锁(@Version 版本号,冲突重试有界) × 检查与提交之间                                    → 强(留自旋重试耗尽 hint)
"检查后再写"两条独立语句/异步入账/内存计数器                                             × 任意 → 弱(等价无防护)
限流/风控阈值(每秒 N 次)                                                                × 任意 → 上下文条件(只产 hint,禁 kills;挂 requires_config 事实)
```
**多段兜底看全部**：有限流≠有原子性——限流只收窄窗口不关闭窗口；`上下文条件` 档不产生 kills 事实。

## ⑥ 判定流程（编号条目，含竞态问句与不变式引用）
C1 促销金额是否由服务端计算（INV-001/INV-004）？｜期望引用:订单创建路径的单价×数量−折扣服务端重算行｜推翻反例:金额取自服务端价格表且客户端字段仅作对账比对｜反向:订单实体 total/discountAmount 直接绑定请求体字段落库且无重算行
C2 竞态问句：促销用量的检查与登记是否在同一原子单元——检查-提交间的并发窗口是否存在，DB 唯一约束/乐观锁是否兜底（INV-002/INV-014）？｜期望引用:usage/redemption 检查行与写入行之间的事务边界/锁语句/唯一索引 DDL｜推翻反例:检查+写入同事务且唯一约束冲突即回滚｜反向:两条独立语句、无唯一索引、无版本号——并发重放同一请求全部通过
C3 优惠券核销是否单次生效（INV-002）？｜期望引用:核销状态翻转行（used 标记/usage_count 置位）与查重键定义｜推翻反例:(coupon_id,order_id) 唯一约束在 DDL 中可引｜反向:先查 used=false 再异步入账，窗口内外可双花
C4 折扣叠加/互斥是否单一服务端裁决点（INV-013）？｜期望引用:折扣计算调用点的 family 分组对照（各端点是否统一调 PricingService）｜推翻反例:全部端点收敛到同一计算服务｜反向:前端/网关/多个微服务各自实现叠加口径且金额差可观测
C5 入口是否可并发触达且限流不拦截？｜期望引用:路由注解 + rate-limit guards 转录事实｜推翻反例:管理通道 only 且有边界证据｜反向:公开 checkout/领券端点无限流或限流阈值远大于并发薅取所需
C6 效应是否可观测（多领份数/订单金额异常/核销次数）？｜期望引用:促销用量与订单金额的对账字段或响应体差异｜推翻反例:统一错误吞噬且无状态差｜反向:核销成功响应本身即效应（无需额外观测）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 展示层 `discount` 字段渲染（label/format）——PL-J03 命中但无计算语义，走 noise 登记。
FP-2 管理端人工发券/补偿流程——单管理员操作走审计通道（INV-011），非本类。
FP-3 单测/压测里的重复 redeem 调用——test source 域，枚举时排除。
FP-4 预估价（estimate 接口）回传客户端——标注"以结算为准"且结算重算存在（C1 反证引文）。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 并发窗口薅限量促销：限流阈值内的 N 个并发请求全过检查（出处：CVE-2025-69871 MedusaJS registerUsage TOCTOU）。
B2 金额负数/超大折扣：客户端 discountAmount 传负值或 >100%——服务端无重算即落库。
B3 二阶券码重放：领券响应里的 code 被脚本并发重放核销（追 persisted_read）。
B4 叠加口径分叉：同一订单在订单服务与支付服务各算一次折扣，取小值绕过单券限制。
B5 退款回滚促销用量缺位——退款后 usage_count 不回落，配合重领放大。
B6 券码可预测（顺序号/短哈希）+ 无领取绑定——未领先核。
B7 异步核销队列：入队成功即返回 200，worker 重复消费无幂等键。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：以并发重放（同一凭据 ≥2 个并发请求）获得超出限额的核销/领取成功响应，或以篡改金额字段获得服务端落库的异常订单金额。Medium 档需单券面额封顶引文。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 用量检查与登记同事务或有 DB 唯一约束兜底（DDL 引文）→ 不应保持 high

## ⑩ 根因修复
用量检查与登记并入同事务 + 唯一约束兜底（(coupon_id,order_id)/(template_id,user_id)）；金额一律服务端重算，DTO 绑定白名单排除金额字段；折扣计算收敛单一服务；核销幂等键贯通同步与异步路径。

## ⑪ 跨边界提示
Egress：订单服务把折扣后的金额透传支付服务，支付侧不再重算——链路上任何一环失守即整体失守；Ingress：消息队列的促销事件重复投递（at-least-once）触发重复 registerUsage——消费者侧幂等是 INV-002 的消息侧变体。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 7/6/3
`fixtures/enum/promo-logic/java/manifest.tsv`（起步集 pos≥4/neg≥4/noise≥2——判据类，fixture 以 java 代表；符合形态命中弱锚的进 noise，pattern 不命中的合规形态才进 neg，见 classes/fixture-spec.md §2）。

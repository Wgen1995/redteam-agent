# perm-model ｜ 权限模型横切（CWE-863 授权不正确 · CWE-269 权限管理不当）

> band: 0 ｜ 轨道: B（不变式轨——**pattern-undetectable 纯判据类**，判定主体在 invariants/retail.inv INV-010/011）｜ 模式表: `patterns/perm-model-java.pattern`（role: judgment-only，数据行为空——保持结构统一，不产枚举分母）｜ fixture: 无（判据类，无 pattern 数据行即无 fixture 门；证据来自 INV 发卡与 role 差分）
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 权限聚合出超集角色（继承环/通配累积）→ High；令牌与主体解绑（token 不绑 uid）→ High；高影响操作单步直达（无二次确认，INV-011）→ Medium-High；角色命名差异但权限集等价 → intended-behavior 处置（不得直接晋升不变式，走 CALIBRATION）
> oracle: none ｜ reasoning-only ｜ human-triage: required（A-012/A-035/B-033——本类无机械/执行 oracle，判定主体在业务不变式：裁决照常落账但结论 reasoning-only，机械字段标 human_triage，最终裁决显式交人工 triage）

## ① 定义与危害
权限模型的横切不变式：会话令牌绑定唯一主体（INV-010）、角色层级无环且权限集可计算（CWE-269）、不可逆高影响操作需二次确认（INV-011）。违反形态=角色继承成环或通配权限累积出 admin、device token 与 uid 分离校验（任意 uid+有效 token 通过）、单管理员单请求完成批量删数据/改价。危害=权限面静默扩张（低角色累积超集）、令牌跨主体生效、不可逆操作无制衡。**本类无 sink 形态可锚：`@PreAuthorize`/`hasRole` 的命中面=全部鉴权代码（authz 类已锚），横切失效（继承环/解绑/缺确认）不在单行代码形态里——判据全部走 ⑥ + INV 条目，枚举分母不成立（pattern-undetectable）。**

## ② Source
角色/权限声明（角色表、继承边、通配权限串 `resource:*`）、令牌载荷（JWT claim 的 uid/role/scope——**claim 未验签或解绑校验即 INV-010 违反证据**）、管理操作请求（批量删/改价/退款——INV-011 的输入面）、角色配置的可写通道（运行时改角色表的 API，联动 config-security C3）。

## ③ Sink 模式表指针
`patterns/perm-model-java.pattern`（role: judgment-only，注释头声明，数据行可为空）。**无锚声明**：单点鉴权形态归 authz 类模式表（A-J 族），本类判定对象是横切性质（继承图闭合性、令牌-主体绑定、确认流程存在性）——不存在行级 ERE 锚。定位改由 guards-authz 转录 + role 差分 + INV 发卡驱动。

## ④ Propagator
权限传播链：角色继承边的传递闭包（环→闭包无限/超集）；令牌 scope 的下游透传（网关剥除/保留 claim 的差异使下游判定分叉）；上下文角色的缓存（角色变更后旧角色仍在缓存窗口内有效——竞态问句的角色侧变体）。

## ⑤ 兜底机制（本类的"Sanitizer"——决策表三值）
```
角色层级无环校验(启动期图校验失败即拒启) × 继承声明 × 任意              → 强
令牌-主体绑定校验(token.subject == 资源属主/会话 uid) × 验签后比对 × 判定前 → 强
审批流/二次确认 token(独立主体或带外确认) × 不可逆操作 × 执行前           → 强
通配权限(resource:*)按字面信任/继承边无校验                          × 任意     → 弱(等价无防护)
角色缓存 TTL 内旧权限有效                                             × 任意     → 上下文条件(只产 hint,禁 kills;挂 requires_config)
```
**多段兜底看全部**：无环校验+通配并存时通配绕过闭包（看实际权限集计算）。

## ⑥ 判定流程（编号条目，含竞态问句与不变式引用）
C1 角色继承图是否无环且权限集可有限计算？｜期望引用:继承边声明/角色表数据/启动校验行｜推翻反例:启动期拓扑排序校验存在且失败拒启｜反向:继承边成环或 `resource:*` 通配使闭包扩张出 admin
C2 令牌校验是否与唯一主体绑定（INV-010）？｜期望引用:令牌校验行 + subject/uid 比对行｜推翻反例:验签后 subject 与会话主体比对且不一致即拒｜反向:只验 token 有效不匹配 uid（任意 uid+有效 token 通过）、或 claim 未验签直用
C3 竞态问句：权限判定与效应提交之间主体权限是否可变（检查-提交间并发窗口：角色被撤销/令牌被吊销后旧判定是否仍完成提交；DB/缓存侧兜底核查=撤销是否即时生效，INV-010）？｜期望引用:判定点到提交点之间的吊销/撤销检查与缓存 TTL 声明｜推翻反例:提交前二次读权威角色源且撤销即时生效｜反向:角色缓存 TTL 窗口内撤销不生效，高影响操作在窗口内完成
C4 不可逆高影响操作是否有二次确认（INV-011）？｜期望引用:操作执行前的审批/确认 token 校验行｜推翻反例:第二主体审批或带外确认 token 校验存在｜反向:单管理员单请求直达批量删/改价/退款
C5 权限差分：同类操作不同角色的判定是否一致（横切缺位差分）？｜期望引用:同 family 各 handler 的 guards 转录对照｜推翻反例:判定统一收敛到单一 guard 组件｜反向:个别 handler 内联判定且判据分叉（漏配面）
C6 效应是否可观测与可归因（审计是否记录主体与授权依据）？｜期望引用:授权决策的审计写入行（who/role/decision）｜推翻反例:审计与决策同点写入｜反向:判定无审计、越权发生后不可归因

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 角色命名不同但权限集等价（organizer vs admin-lite）——intended-behavior 处置，**不得直接晋升不变式**（invariant-protocol §5，先走 CALIBRATION 证据分级）。
FP-2 共享家庭账号的 token 多主体设计——产品显式声明（INV-010 阴性边界）。
FP-3 单人卖家的自有店铺定价单步操作——影响域单一（INV-011 阴性边界）。
FP-4 紧急冻结类保护性操作单步直达——方向是收窄风险不是放大。
FP-5 服务间 machine token 高权限直通——需网络边界+审计证据（无证据不得凭叙事放行）。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 角色继承环：A→B→C→A 使闭包累积超集（出处：人工归纳，RBAC 环形继承；authz B4 的横切展开）。
B2 通配权限 `resource:*` 压过具体 deny——权限集计算顺序吞掉否定项。
B3 device token 与 uid 分离校验——跨主体令牌重放（INV-010 主形态）。
B4 密码重置只验 token 不匹配 user_id——重置任意账号（C2 反向引文）。
B5 角色撤销缓存窗口：撤销后 TTL 内旧 token/旧角色仍过判定（C3 竞态窗口）。
B6 管理端批量操作复用单对象确认——确认覆盖首对象，循环体绕过（INV-011 的循环变体）。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：以低权限角色的有效凭据经继承/通配/解绑路径完成高权限动作且审计可归因；或以 A 主体的有效令牌操作 B 主体资源成功。Medium-High 档（INV-011）需操作不可逆性引文。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 角色继承封闭集+无通配权限（注册表引文）或判定走独立 admin 会话+审计 → 降 medium 以下

## ⑩ 根因修复
角色层级启动期无环校验 + 通配权限登记审批；令牌 subject 强制绑定校验进统一 guard 组件；权限判定收敛单点并同点审计；不可逆操作走第二主体审批或带外确认 token；撤销走权威源即时生效（缓存失效广播）。

## ⑪ 跨边界提示
Egress：网关剥除/保留角色 claim 的策略不一致使下游判定分叉（透传即信任的跨服务变体）；Ingress：消息体携带 role/scope 字段直进判定（C-g 同位问句的 perm-model 侧）；配置中心热改角色表联动 config-security C3。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: 无 fixture（待补——D-039/D-067 披露）
无 fixture 目录（pattern-undetectable：`patterns/perm-model-java.pattern` 数据行为空，门不适用）。证据基线走 `invariants/retail.inv` INV-010/011 的已知真违反样本与 role 差分（fixtures/enum/{inv_id}/ 按 invariant-protocol §3 另行挂接，S2 交付）。

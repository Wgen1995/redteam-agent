# tenant-isolation ｜ 多租户数据访问（CWE-284 访问控制不当 · CWE-668 越界资源访问）

> band: 0 ｜ 轨道: B（不变式轨——判定主体在 invariants/retail.inv INV-005）｜ 模式表: `patterns/tenant-isolation-java.pattern`（**弱锚**：repository 查询与 tenant 列共现）｜ fixture: `fixtures/enum/tenant-isolation/java/`（判据类，fixture 以 java 代表，ts/python 待 S2）
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: tenant 过滤整体缺席（面状缺失）→ High（系统性）；tenant 值取自请求参数/头（guard 输入不可信）→ High；单点路由遗漏（点状缺失，family 差分证据）→ High；共享表误判（无 tenant 概念）→ FP-1 清零路径（需证据）
> oracle: none ｜ reasoning-only ｜ human-triage: required（A-012/A-035/B-033——本类无机械/执行 oracle，判定主体在业务不变式：裁决照常落账但结论 reasoning-only，机械字段标 human_triage，最终裁决显式交人工 triage）

## ① 定义与危害
租户隔离表（订单/会员/营销数据）的每次读写必须带 tenant 谓词且取值来自服务端会话上下文（INV-005）。违反形态=谓词缺席（findById 直查跨租户）、谓词在但值取自请求（X-Tenant-Id 头直入查询）、ORM 租户插件被手写 SQL 绕过。危害=跨租户读写（拖库级泄露/跨租户改删）。**本类结构性特征与 authz 同族：sink 弱（按 id 取数是合法主流），判定主体在 tenant 谓词的存在性与取值来源**——与 authz 的分界：authz 问"属主是否校验"，本类问"租户列是否进谓词且租户值是否服务端来源"（单租户属主正确但租户列缺席仍归本类）。

## ② Source
- **资源键**：路径 `{id}`/查询参数/body 的订单号会员号（与 authz 共享）。
- **tenant 判据输入**（本类特有，喂 C-g 同位问句）：`X-Tenant-Id`/`X-Org-Id` 信任头、body 的 tenantId 字段、JWT 未验签 claim 里的 tenant、中间件透传的 TenantContext——**凡进 tenant 谓词的值都追其来源**。
- 租户上下文的机械来源：`langpacks/{lang}/guards-authz.md` 转录 + 本类 T-J07 上下文存取锚。

## ③ Sink 模式表指针
`patterns/tenant-isolation-java.pattern`（机器直读，逐行一条，不并串）。锚形态：repository 行与 tenant 列共现（`Repository.*tenantId` 正反序）、原生 SQL 的 `tenant_id` 谓词、派生查询 `findByTenant`/`AndTenantId` 谓词、租户插件声明（`TenantLineHandler|TenantInterceptor|TenantFilter`）、`TenantContext` 存取。**共现锚声明：单行同时含 repository 使用与 tenant token 才命中（T-J01/T-J02），裸 tenantId 字段声明不命中**——命中只证明"租户敏感数据访问点在"，跨租户与否由 ⑥ 判别。

## ④ Propagator
tenantId 透传链：controller→DTO→repository（值来源逐跳稀释是本类主通道）；ORM mass assignment（body 的 tenantId 直入实体字段=跨租户改绑）；上下文注入链：中间件把请求头写 ThreadLocal/TenantContext，谓词再从 context 读（注入点离判定点隔多层）。

## ⑤ 兜底机制（本类的"Sanitizer"——决策表三值）
```
tenant 谓词进查询条件(findByTenantIdAndX / WHERE tenant_id=?) × 取值自验签会话/TenantContext(服务端来源) × 查询前 → 强
ORM 租户插件(TenantLineHandler 行级重写)                        × 覆盖全部 SQL 通道(含手写 native) × 任意 → 强(仅当 C5 通过——native 绕过见 B1)
谓词在但值取自 X-Tenant-Id 头/body tenantId 字段                  × 请求可控                        × 任意     → 弱(等价无防护)
共享表白名单(无 tenant 列的全局表清单)                            × 显式登记                       × 任意     → 上下文条件(只产 hint,禁 kills;挂 requires_config)
```
**多段兜底看全部**：插件+native SQL 并存时以实际执行 SQL 为准；白名单档不产生 kills 事实。

## ⑥ 判定流程（编号条目，含竞态问句与不变式引用）
C1 资源是否属于租户隔离域（有 tenant 列/租户上下文概念可引，INV-005 适用前提）？｜期望引用:实体字段/迁移 DDL 的 tenant 列声明｜推翻反例:全局共享表（商品目录/公开促销）且在共享白名单登记｜反向:表有 tenant_id 列但查询族全部缺席该谓词
C2 租户敏感查询是否带 tenant 谓词（INV-005）？｜期望引用:sink 行±5 行的 where/谓词构造｜推翻反例:谓词含 tenant 列且为绑定值｜反向:findById 直查、native SQL 无 tenant_id、或谓词在 builder 链末尾被条件跳过
C3 tenant 谓词取值是否服务端来源（会话/验签上下文，非请求头参数）？｜期望引用:tenant 参数的取值来源行（TenantContext/session vs header/body）｜推翻反例:取自验签后的 TenantContext 且中间件来源可信｜反向:取自 X-Tenant-Id 头、body tenantId 字段、未验签 claim
C4 竞态问句：租户判定与数据提交之间对象是否可被跨租户改绑（检查-提交间并发窗口，DB 租户约束兜底核查）？｜期望引用:校验后到 save/update 之间的窗口 + 实体租户字段是否可由 mass assignment 改写｜推翻反例:tenant 列不在 DTO 绑定白名单且 update 谓词仍带 tenant 条件｜反向:取出后整体 save 回写，租户字段随载荷漂移
C5 ORM 租户插件是否覆盖该执行通道（手写 native/QueryBuilder 绕过核查）？｜期望引用:插件声明行 + 实际执行 SQL 类型引文｜推翻反例:全部走插件重写通道且 native 清单为空｜反向:TenantLineHandler 在但该语句是手写 native（插件不重写）
C6 同 family 差分：同形路由族内谁的查询带 tenant 谓词（面状 vs 点状缺失）？｜期望引用:source_inventory.family 分组内各 handler 的谓词事实对照｜推翻反例:全 family 均带谓词（差分为零）｜反向:仅个别路由缺席（点状遗漏，单点高危）
C7 效应可观测（跨租户数据出现在响应/写生效）？｜期望引用:响应构造行与写后回读｜推翻反例:统一 404 吞噬且无写效应｜反向:跨租户写成功本身即效应

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 全局共享表（无 tenant 概念的商品目录/公开促销）——需共享白名单或 DDL 证据，不得凭"看起来公共"放行。
FP-2 网关/中间件统一注入租户——需配置证据（中间件声明+来源可信），模式层看不到网关。
FP-3 平台运营侧全租户管理查询——独立 admin 会话+审计通道（INV-005 阴性边界）。
FP-4 单租户部署（deployment 级隔离）——需部署拓扑证据，多租户代码跑单租户实例不构成违反。
FP-5 生成代码（role=generated 的 CRUD 脚手架）——按生成物规约归并。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 手写 native SQL 绕过 ORM 租户插件（MyBatis-Plus TenantLineHandler 不重写手写 SQL）。
B2 谓词在但值可指定：`findByTenantId(dto.getTenantId())`——谓词形态齐全、取值请求可控（C3 主形态）。
B3 mass assignment 改绑：update body 带 tenantId 整体绑定实体后 save（C4 竞态窗口的静默变体）。
B4 二阶：列表页回显他人租户的对象 id 再操作（追 persisted_read）。
B5 导出/报表/audit 复用 service 无谓词（authz B7 的租户侧同型）。
B6 租户上下文 ThreadLocal 线程池残留：上一请求的 tenant 漏进下一请求（竞态问句的上下文侧变体——filter 未清理）。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：以两个不同租户的凭据重放同一请求得到非对称结果（读：他租户数据入响应；写：他租户资源变更）；或单凭据改 X-Tenant-Id 头即切换数据面。面状缺失按系统性 finding 归并，不逐路由双计。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 单租户部署实例（部署拓扑证据）或查询对象为全局共享表 → 不应保持 high

## ⑩ 根因修复
tenant 谓词进查询条件且取值只取服务端上下文；ORM 租户插件 + 手写 SQL 审计清单；DTO 绑定白名单排除 tenantId；ThreadLocal 上下文 filter 内 try-finally 清理；共享表白名单显式登记进配置。

## ⑪ 跨边界提示
Egress：服务间调用透传 X-Tenant-Id 原始头，下游当可信判据（上游伪造面）；Ingress：消息体携带 tenantId 字段直进谓词（C3 的消息侧变体）；跨租户导出文件落对象存储后按可猜 key 读取（存储侧隔离缺位）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 6/6/3
`fixtures/enum/tenant-isolation/java/manifest.tsv`（起步集 pos≥4/neg≥4/noise≥2——判据类，fixture 以 java 代表；带 tenant 谓词且取值服务端来源的安全查询命中共现锚的进 noise，pattern 不命中的无关形态进 neg，见 classes/fixture-spec.md §2）。

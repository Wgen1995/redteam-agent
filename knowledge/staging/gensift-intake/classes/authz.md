# authz ｜ 越权/IDOR（CWE-862 缺失授权 · CWE-639 用户可控键授权）

> band: 0 ｜ 模式表: `patterns/authz-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/authz/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 未鉴权写（匿名改他人资源）→ High-Critical；垂直越权（普通主体执行管理动作）→ High；水平写/删 → High；水平读（跨属主读数据）→ Medium-High；公开只读资源 → FP-1 清零路径（需证据）

## ① 定义与危害
判定主体（who）与资源键（which）之间缺一道服务端校验：请求自带的键直达数据访问/变更，而当前主体的身份、属主、角色没有任何一处约束生效。危害=读他人数据（拖库级泄露）/改删他人资源/提权到管理面。
**分型（判定与定级都按此走）**：
- **水平越权**（CWE-639 主型，IDOR）：同权限级别主体 A 把键换成主体 B 的资源——"改 id 看别人"。锚点是 sink 侧（按 id 直查无属主过滤）。
- **垂直越权**（CWE-862 主型）：低权限主体执行高权限动作——handler 缺角色检查，或检查判据可被请求参数决定（body 带 `role:"admin"`，见 C-g）。
- **复合**：垂直进入管理端点后再水平遍历全体对象（管理动作缺对象级检查）。
**本类结构性特征：sink 弱、判定主体在 guard 侧**。按 id 取数到处都是（绝大多数是合法业务），故不能像 SQLi 那样靠 sink 形态收敛——判定重心是 C-g（guard 输入可信性）与 owner 差分。
**owner 检查差分**（差分轨主力信号）：同一 family 内"GET /x/{id} 谁检查了资源属主"——按 `source_inventory.family` 的 param_shape 分组（同形路由族），逐 handler 对照 guards-authz 转录出的属主检查事实：**面状缺失**（全 family 无检查=系统性默认缺失，suspension 低但面积大）与**点状缺失**（仅个别路由缺，high-suspicion 单点）是两种不同 finding。family 内不一致本身就是 +suspicion 证据。

## ② Source
- **资源键**：路径 `{id}`、查询参数、body 字段中的 id/uuid/短码/序号/复合键；列表页回显再提交的他人 id（存储回读 persisted_read，二阶：上周看到的对象 id 本周被直接操作）。
- **guard 判据输入**（本类特有 source，喂 C-g）：`X-User-Id`/`X-Org-Id`/`X-Forwarded-User` 类信任头、body 里的 `role/userId/orgId` 字段、未验签 cookie/JWT claim、中间件透传的上下文变量——凡"guard 拿来做决定的值"都按 source 追其来源。
- guard 事实的机械来源：`langpacks/{lang}/guards-authz.md` 转录（五段之一），类页面不重复转录内容。

## ③ Sink 模式表指针
`patterns/authz-java.pattern` / `authz-ts.pattern` / `authz-python.pattern`（机器直读，逐行一条，不并串）。两类锚：①按 id 形态的数据访问（findById/getOne/findOne/`\.get\(.*[Ii]d`/Repository 查询族）②按 id 定位的删除/更新（deleteById/remove/update\*Id）。**sink 命中只证明"键在数据面被使用"，不证明漏洞**——安全/危险由 ⑥ 五步判别。

## ④ Propagator
- id 透传链：controller→DTO→service→repository 的键传播（跨字段保守传播）。
- **guard 输入注入链**：中间件把请求头写进 ThreadLocal/RequestContext，guard 再从 context 读——注入点离判定点可能隔多层。
- ORM 整体绑定（mass assignment 通道）：请求体字段直入实体字段（含 `role/isAdmin/ownerId`），见 B1。

## ⑤ Guard（本类的"Sanitizer"——决策表三值）
```
属主约束进查询条件(findByIdAndOwnerId / where:{id,ownerId}) × 判据取自验签会话 × 查询前 → 强
取出后比对属主(findById 后 if owner!=current throw)          × 判据取自验签会话 × 查询后 → 强(留 TOCTOU 窗口,挂 B6 hint)
角色注解/装饰器(@PreAuthorize/@roles_required)               × 框架解析 handler 级 × 路由前 → 强(仅当 C-g 通过)
伪 guard(判据取自 X-User-Id 头/body role 字段)               × 请求可控            × 任意     → 弱(等价无防护)
配置开关才启用(if(config.strict))                             × 任意                × 任意     → 上下文条件(只产 hint,禁 kills;挂 requires_config 事实)
```
**多段 guard 看全部**：authn 通过+角色通过≠属主通过；`上下文条件` 档不产生 kills 事实（单点误判不剪整类）。

## ⑥ 判定流程（编号条目，含第五要素 C-g）
C1 资源键是否外部可控且指向他人可拥有的聚合？｜期望引用:入口签名与取键行(路径/查询/body 的 id/uuid/序号)｜推翻反例:键为服务端生成且调用方不可指定｜反向:键来自上一响应体且服务端已校验属主
C2 键是否未经属主约束直达数据访问？｜期望引用:sink 行±5 行的查询条件/where/on 子句｜推翻反例:条件含 owner/tenant 列且为绑定值｜反向:条件在 builder 链末尾才拼上(逐段看全)
C3 同 family 差分：同 param_shape 兄弟路由谁做了属主检查？｜期望引用:source_inventory.family 分组内各 handler 的 guards-authz 事实｜推翻反例:全 family 均有检查(差分为零)｜反向:仅个别路由缺失(点状遗漏,单点高危)
C4 guard 是否真实生效（⑤决策表查值）？｜期望引用:guard 调用行+其判据取值来源行｜推翻反例:强 guard 且判据服务端来源｜反向:guard 在不可达分支/被 try 吞/注解在类级但方法级另有无防护重载
C-g guard 输入可信性：guard 的判据输入是否可由请求头/参数决定（X-User-Id 信任头伪造形态）？｜期望引用:guard 判据的取值来源行(header/param/body vs session/验签 token)｜推翻反例:判据取自验签后的会话主体与服务端查询｜反向:判据取 X-User-Id/X-Org-Id 头、body 的 role/userId 字段或未验签 claim
C5 分型：垂直（动作需更高角色）还是水平（同级跨属主）？｜期望引用:路由所需角色配置与资源属主字段｜推翻反例:动作公开且资源无属主概念(走 FP-1)｜反向:角色检查存在但继承链放行(见 B4)
C6 效应是否可观测（返回体差异/状态码差异/写后回读）？｜期望引用:响应构造与异常处理行｜推翻反例:统一 404 吞噬且无写效应｜反向:写操作成功本身即效应(无需观测)

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 公开只读资源（published 状态/无属主模型的公共聚合）——需 OBS 到公开性证据（字段/迁移/配置），不得凭"看起来像公开"降级。
FP-2 网关统一鉴权——模式层看不到网关；需配置证据（网关路由表/鉴权中间件声明文件），无证据不得凭叙事放行。
FP-3 运维/内部端点仅内网可达——需边界证据（网络策略/入口清单/部署拓扑）。
FP-4 生成代码（role=generated 的 CRUD 脚手架）——按生成物规约归并，不与手写同型双计。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 Mass assignment 越权提权：update 请求体带 `role/isAdmin/ownerId` 被 ORM 整体绑定——找绑定白名单缺失点（出处：GitHub 2012 mass-assignment 事件，Rails attr_accessible 缺失）。
B2 UUID 可枚举：v1/时间序 UUID 或短哈希泄露规模与属主集合；**键不可枚举≠不可指定**——重放他人键仍越权（出处：CWE-639 官方示例即顺序键与可预测键）。
B3 继承与变体路由绕过：新端点挂在只做 authn 的基类/中间件下继承"已登录即可"；版本化前缀（/v2/）/`?version=`/draft/audit/export 复用同一 service 无属主检查；HTTP 方法重载（POST→PATCH）落到无检查 handler。
B4 角色继承环：role 继承图成环或通配权限（`resource:*`）使低角色累积出 admin（出处：人工归纳，RBAC 环形继承）。
B5 admin 默认：默认安装的管理端点+默认凭据/未改密 admin 分支；debug/profile 端点无鉴权暴露。
B6 TOCTOU：属主检查后到提交之间对象换绑/换属主——查检查-提交并发窗口与 DB 约束兜底。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：以两个不同属主的凭据重放同一请求得到非对称结果（读：他人数据出现在响应；写：他人资源发生变更）。未鉴权写=High-Critical 的前提是入口可达性有 OBS（路由表/入口清单）。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 公开只读资源（FP-1 清零路径有证据）或对象属全局共享表（无 tenant 列证据）→ 不应保持 high

## ⑩ 根因修复
属主约束进查询条件（`findOne(id, ownerId)` 取代 findById 后比对）；中间件默认拒绝+显式白名单；DTO 字段级绑定白名单；主体只取验签会话（禁信任头）；角色层级做无环校验；管理端点对象级检查与路由级同置。

## ⑪ 跨边界提示
Egress：服务间调用透传原始用户头（`X-User-Id` 原样下传）使下游 guard 输入可被上游伪造——差分要跨服务对照。Ingress：消息体携带 role/orgId 字段直进 guard 判据（C-g 命中形态的消息侧变体）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 13/20/6、python 8/9/4、ts 8/10/4
`fixtures/enum/authz/{lang}/manifest.tsv`。java 全量集 pos≥10/neg≥20/noise≥5；ts、python 起步集 pos≥6/neg≥8/noise≥3。**本类特殊约定：带 owner 检查/@PreAuthorize 的 findById 形态归 noise 不归 neg**——sink 仍在（pattern 必然命中），安全性由 ⑥ 五步判别；neg 只放非数据访问形态（见 classes/fixture-spec.md §2 三类语义）。

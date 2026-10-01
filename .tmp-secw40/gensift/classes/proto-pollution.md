# proto-pollution ｜ 原型链污染（CWE-1321）

> band: 1 ｜ 模式表: `patterns/proto-pollution-ts.pattern`（**主形态语言仅 ts——Node/TS 特有**）｜ fixture: `fixtures/enum/proto-pollution/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 递归合并/键赋值把 `__proto__/constructor.prototype` 写上 Object.prototype 且污染键值用户可控 → High（属性注入→gadget 链=权限提升/RCE 邻接）；污染目标为 `Object.create(null)`/plain dict 且无 gadget 下游 → 降 Medium（前提引文）；仅深拷贝性能问题无键回写 → 清零

## ① 定义与危害
递归合并/深拷贝/路径赋值工具把**用户可控的键**沿 `__proto__`、`constructor["prototype"]` 写进 `Object.prototype`（全局原型）——此后所有对象继承该属性，攻击者借既读属性注入（`isAdmin`/`role`/`trusted`）改鉴权分支，或喂给已知的 client/server 端 gadget（`child_process` options/spawn argv/ejs options）达成 RCE 邻接。依据：CWE-1321；CVE-2019-10744（lodash.merge）、CVE-2018-3721（lodash merge/mergeWith，<4.17.5）、CVE-2020-8203（lodash zipObjectDeep）——依赖版本证据进 C2。
**语言适用性（封闭声明）**：**Java 不适用**——无原型链、无运行时可写的共享类属性面（Spring DataBinder 类路径绑定属 CVE-2022-22965 家族，归 deser/cmd-injection 邻接，不产本类 pattern 件）。**Python 为 class-pollution 类似形态起步集**（`setattr(`/`__dict__.update(` 键可控时污染类属性——形态相邻但无全局共享原型，危害面窄，pattern 3 条起步）。**主形态 pattern 仅 ts 存在。**

## ② Source
HTTP JSON body 整体（`req.body`/`ctx.request.body`——payload 键位即攻击载体）、query/cookie 经 `qs.parse`/`querystring` 展开的嵌套对象（`?__proto__[x]=y`）、**存储回读（persisted_read：用户偏好/配置 blob 落库回读后进 merge——二阶污染）**、消息体（external_message）。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/proto-pollution-ts.pattern`（机器直读，逐行一条，不并串）：键形态（`__proto__`、`constructor["prototype"]`、`constructor.prototype`）+ 递归赋值家族（`deepmerge(`/`deepMerge(`/`defaultsDeep(`/`[.]merge(`/`[.]extend(`/`deepCopy(`/`_\.set(`/`Object.assign(`）。**pattern 仅 ts 存在**；`patterns/proto-pollution-python.pattern` 为 class-pollution 类似形态起步（`setattr(`/`__dict__\.update(`/`deep_merge(`）。`Object.freeze(Object.prototype)` 出现即强净化（C4）。

## ④ Propagator
递归键回写本身即传播：`dst[k] = isObj(v) ? merge(dst[k], v) : v` 的深递归、`_.set(obj, "a.b.c", v)` 的路径分段展开、`JSON.parse` 后整体进 merge（`{"__proto__": {...}}` 在 parse 后键位即触发）、spread `{...a, ...b}` 浅层（一层即止，不污染——形态边界）。跨方法保守传播；工具类封装（`utils.deepCopy`/`config.merge`）是常见藏点。

## ⑤ Sanitizer（决策表三值）
键黑名单（拒 `__proto__`/`prototype`/`constructor`——lodash ≥4.17.12 修法）→ **强**（仅当在递归每层判、不是只判顶层）；`Object.create(null)` 作合并目标 + 输出仅内部消费 → **强**（无原型可污染）；`Object.freeze(Object.prototype)` 全局冻结 → **强**（一次到位，但需确认运行早期执行）；`Object.setPrototypeOf(obj, null)` 局部 → **上下文条件（只产 hint，禁 kills）**；Map 替代 plain object 承载动态键 → **强**；只过滤值不过滤键、"键不含 `$`"的 mongo-sanitize 老版 → **弱**（constructor 形态逃逸）；深拷贝 `JSON.parse(JSON.stringify(x))` 剥掉 `__proto__` → **强**（对纯 JSON 值成立，函数/undefined 丢失是副作用不是弱点）。**多段净化看全部：外层过滤、递归内层未过滤 = 整体弱。**

## ⑥ 判定流程（编号条目）
C1 进入递归合并/键赋值的对象是否用户可控（body/qs 展开/回读 blob）？｜期望引用:入口取流行与 merge/set 调用行｜推翻反例:合并双方均为服务端常量配置｜反向:用户偏好落库回读进 merge（persisted_read）
C2 **递归合并的用户键是否过滤**（`__proto__`/`constructor`/`prototype` 黑名单或 Map/Object.create(null) 承载）？｜期望引用:递归函数体内键判断行全量（不止顶层包装）｜推翻反例:每层递归先判键黑名单且名单含 constructor 形态｜反向:仅顶层浅拷贝判键、递归层直写
C3 污染目标是否全局原型（写向 Object.prototype 经 `__proto__` 键）而非局部 plain object？｜期望引用:merge 目标构造行（字面量 `{}` 即潜在全局面；`Object.create(null)` 即无面）｜推翻反例:目标为 null 原型/Map｜反向:经 `constructor["prototype"]` 双跳仍达全局
C4 是否存在全局防御（freeze(Object.prototype)/`--disable-proto`/框架中间件）？｜期望引用:防御声明行与执行时机（在入口注册前）｜推翻反例:启动早期已冻结且无解冻调用｜反向:防御仅测试环境启用
C5 污染属性是否被 gadget 下游消费（`isAdmin/role/options/spawn` 读取点）？｜期望引用:同名属性读取行±10 行｜推翻反例:无任何消费点（降 Medium）｜反向:child_process/ejs/handlebars 参数链上读污染键（升 RCE 邻接）
C6 入口可达且鉴权不拦截？｜期望引用:路由注解/中间件链｜推翻反例:内网-only 且有边界证据｜反向:默认放行的偏好设置端点（最常见入口）
C7 lodash/deepmerge 等依赖版本是否落在已知污染区间？｜期望引用:package.json 依赖行 × known-gadgets/CVE 区间（CVE-2019-10744：<4.17.12；CVE-2018-3721：<4.17.5）｜推翻反例:版本已出区间｜反向:lockfile 缺失按最宽区间计

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 键黑名单守卫行自身的 `__proto__` 字面——PP-T01 命中守卫代码而非 payload（C2 反证，noise/merge-key-blacklist）。
FP-2 常量路径 `_.set(cfg, "app.port", 8080)`——路径非可控，C1 反证（noise/lodash-set-constant）。
FP-3 `deepCopy` 仅用于缓存快照无键回写——C2 反证（无递归赋值到目标侧用户键）。
FP-4 spread 一层浅合并 `{...defaults, ...opts}`——不递归即不污染（C2/C3 反证）。
FP-5 类定义里的 `constructor() { super(); }`——PP-T02/T03 要求 bracket/dot 到 prototype 的完整形态，不命中；命中变体需登记。
FP-6 `Object.assign` 到 `Object.create(null)` 目标——PP-T11 命中但无全局面（C3 反证）。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 键逃逸：黑名单只拦 `__proto__` 不拦 `constructor["prototype"]` 双跳；`__pro to__` 不可拆但 JSON `{"__proto__":...}` 键在 parse 后仍是同键。
B2 qs/express 老版 `?a[__proto__][b]=c` 参数展开成嵌套对象再 merge——入口在 query 不在 body。
B3 自研递归 merge 函数名不在家族表（`recursiveAssign`/`assignDeep`/`hoist`）——形态靠 `dst[k] = ` 递归回写识别，进 B 清单扩 pattern。
B4 二阶：偏好 blob 落库回读进 merge（追 persisted_read，C1 反向）。
B5 gadget 侧：污染 `options.shell/NODE_OPTIONS/argv` 进 spawn——消费点离污染点跨文件（C5 引文要跨文件给）。
B6 Python class pollution：`setattr(cls, user_key, v)` 改类属性影响全部实例；`obj.__dict__.update(user)` 同形——python 起步集按 C1/C2 同判据走。
B7 `structuredClone` 前置不可净化键——污染在 clone 之后仍发生（时机问题，C2 时机引文）。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：给出"可控键 → 递归回写 → 全局原型/类属性"的 OBS 链与至少一个属性消费点（C5）；RCE 邻接验收再给 gadget 参数链引文。band:1 与 band:0 的差别：发卡前必须闭合 C2（**递归合并的用户键是否过滤**——本类判据核心）与 C3（全局面）两问，只有 merge 形态没有键过滤证据链时不得直接定 High。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 合并目标非原型链（plain object/Map 引文）或键经白名单过滤（引文）→ 降 medium 以下

## ⑩ 根因修复
递归合并每层键黑名单（`__proto__`/`constructor`/`prototype`）封装为唯一合并入口；动态键承载改 Map 或 `Object.create(null)`；启动期 `Object.freeze(Object.prototype)` 兜底；lodash/deepmerge 升出已知 CVE 区间（≥4.17.12）；body 一律 schema 校验（zod/DTO）拒多余键——操作符与原型键同门拦截（联动 injection-misc C3）。

## ⑪ 跨边界提示
污染后的配置对象经消息队列/缓存序列化传给 worker（**污染在传播中持久化**——序列化把注入属性带进新进程面）；BFF 把用户 JSON 透传下游 Node 服务再 merge（拼接点在上游）；Python 侧 class pollution 影响同进程全部实例但无 JS 式全局原型——跨语言断言不可移用（见 §① 适用性封闭声明）；浏览器端 bundle 的污染面与服务端各自计卡不合并。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: python 4/6/3、ts 12/21/6
`fixtures/enum/proto-pollution/{lang}/manifest.tsv`（**ts 达标集：正例≥10/硬负例≥20/噪音≥5；python 起步集；java 不适用——无本类 pattern 件与 fixture，manifest 注明**——见 classes/fixture-spec.md 三类语义）。

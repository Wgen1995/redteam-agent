# injection-misc ｜ LDAP / NoSQL / XPath 注入（CWE-90 · CWE-643 · CWE-943）

> band: 0 ｜ 模式表: `patterns/injection-misc-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/injection-misc/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 互斥归属（D-010）: 本类只收「LDAP/NoSQL/XPath 查询语义注入」；SQL 归 sqli；$where 的 JS 执行体（RCE 邻接）记本类但执行面细节引 code-injection；进程命令归 cmd-injection。
> 定级阶梯: 可控输入拼进三族 sink + 无转义 → High（LDAP=认证绕过/目录改读、NoSQL $where=RCE 邻接/认证绕过、XPath=全文档改读）；仅内网目录只读 schema 可控 → 降 Medium（前提引文）

## ① 定义与危害
三族非 SQL 查询语义被用户输入改写：**LDAP**（CWE-90）——filter 串拼进 `(&(uid=x)(pwd=y))`，`*)(`通配改语义=匿名绑定成功/属性改读；**NoSQL**（CWE-943）——`$where` 携带 JS 体在服务端执行（RCE 邻接）、`$ne/$gt/$regex` 操作符注入改判定逻辑（`{"pass":{"$ne":""}}` 万能绕过）；**XPath**（CWE-643）——表达式拼接后 `' or '1'='1` 使定位漂移到任意节点（无权限层时=全文档读）。危害=认证绕过（三族共有的最短路径）、越权读、NoSQL 侧 ReDoS（$regex）与 JS 执行面。

## ② Source
HTTP 参数/路径/头部/_body_、消息体（external_message）、**JSON body 的嵌套键值对（NoSQL 操作符注入的特有入口：`{"password":{"$ne":"x"}}` 整体进 find——body 解析后键即操作符）**、XML 字段回读后拼 XPath、**存储回读（persisted_read：DB 存的 dn/cn 回读后拼 filter——二阶）**。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/injection-misc-java.pattern` / `injection-misc-ts.pattern` / `injection-misc-python.pattern`（机器直读，逐行一条，不并串）。三族各自的家族标记：LDAP=`SearchControls(`/`InitialDirContext`（Java）、`ldap.initialize(`（Py）、`.search(`（三语言共用 sink 名）；NoSQL=`$where`/`$regex`/`$ne` 键 + `BasicDBObject(`/`Filters.where(`（Java legacy）；XPath=`XPathExpression`/`.evaluate(`（Java）、`xpath.select(`（TS）、`.xpath(`（Py）。`Filters.eq(` 等结构化构建器非本类（见 FP-2）。

## ④ Propagator
字符串拼接（`+`/模板串/f-string）、`MessageFormat.format`（LDAP filter 占位展开仍是无转义拼接）、StringBuilder 链、**JSON body 整体透传进 find/query（操作符在键位不在值位——拼接传播不适用，看键白名单）**、dn/cn 先落库后回读再拼 filter。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
LDAP filter 转义（RFC 4515：`\2a \28 \29 \5c \00` 五字符，或库的 `encodeFilterValue`）→ **强**（仅当对全部拼接段生效）；XPath 参数化（`.evaluate(expr, doc)` 前变量经 `XPathVariableResolver` / lxml `xpath(expr, id=value)` 命名参数）→ **强**；NoSQL 键白名单/DTO 反序列化（body 先进固定字段 DTO，多余键丢弃——操作符进不了查询）→ **强**；`$where` 一律禁用改 `$expr` 结构化 → **强**；黑名单 `replace("*","")`/strip 特定操作符 → **弱**（`$ne`→`$gt` 换键、`\2a` 双写逃逸）；`mongo-sanitize`/递归删 `$` 前缀键但漏 `constructor` 形态 → **弱**（proto-pollution 联动）；`if(strict)` 才启用 → **上下文条件（只产 hint，禁 kills）**。**多段净化看全部：filter 两侧转义、中间占位段漏转 = 整体弱。**

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（参数/消息/JSON body 键位/回读）？｜期望引用:入口签名与取参行｜推翻反例:实参为编译期常量或服务端枚举产出｜反向:DB 回读的 cn 拼进 filter（persisted_read）
C2 LDAP filter 是否存在拼接段且无 RFC 4515 转义？｜期望引用:filter 构造行±3 行与转义调用（若有）的叶子实现｜推翻反例:filter 全字面量（`(objectClass=person)`）或拼接段经 encodeFilterValue｜反向:转义只覆盖 `*` 不覆盖 `()\\`（弱）
C3 NoSQL 查询是否把用户 JSON 键/值直接放进操作符位（$where/$ne/$gt/$regex）？｜期望引用:find/query 调用行与 body 透传链｜推翻反例:body 经固定 DTO/schema 校验后取字段｜反向:`$where` 串里再拼用户值（JS 体注入，升 RCE 邻接）
C4 XPath 表达式是否拼接且未用变量解析器？｜期望引用:xpath.compile/evaluate 行与拼接来源｜推翻反例:表达式全字面量或经 XPathVariableResolver/lxml 命名参数｜反向:只过滤引号未过滤 `]/` 轴定位符
C5 净化是否消除对应族载荷形态（决策表查值）？｜期望引用:净化调用行+叶子实现｜推翻反例:强净化且形态匹配（LDAP 五字符/XPath 变量化/NoSQL 键白名单）｜反向:净化在假分支/常量条件里
C6 入口可达且鉴权不拦截？｜期望引用:路由注解/拦截器配置｜推翻反例:内网-only 且有边界证据｜反向:默认放行配置（LDAP 登录端点=最常见）
C7 注入结果可观测（响应差异/认证结果差异）？｜期望引用:响应构造与异常处理行｜推翻反例:统一吞噬且无时间差｜反向:认证绕过形态无需观测（登录成功即回显）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 固定 filter 的目录检索（`ctx.search(base, "(objectClass=person)", sc)`）——IM-J01/J02 命中但无拼接段，C2 反证（noise/ldap-constant-filter）。
FP-2 MongoDB 结构化构建器（`Filters.eq("f", v)`）——值参数化非文本拼接，仅 `Filters.where(` 是本类。
FP-3 XPath 常量表达式（`xp.evaluate("/root", doc)`）——C4 反证。
FP-4 全文检索引擎的 `.search(`（ES RestHighLevelClient.search）——IM-J02 命中但查询体为结构化 JSON builder，VERIFY 看实参形态后清零。
FP-5 `Arrays.binarySearch(`/`List.indexOf(` 等大小写撞车——pattern 小写 `.search(` 不命中（ERE 区分大小写），命中变体需登记。
FP-6 `$regex` 用于服务端自产 pattern（校验手机号）——键位非用户可控，C3 反证。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 LDAP 转义不全：`\2a \28 \29 \5c \00` 缺一即余字符逃逸；宽字符/UTF-8 归一化差异下的 `\` 双写。
B2 NoSQL `$where` 变体：`$func`/map-reduce 的 JS 体拼接；mongoose `.where()` 链末端 `.exec()`。
B3 操作符族扩展：`$nin/$exists/$mod/$size/$type`——pattern 只列 where/regex/ne，其余靠键白名单判据（C3）兜。
B4 XPath 盲注：布尔差异逐字符外带（`substring(/root/user[1]/pwd,N,1)='a'`）；NoSQL `$regex` 逐位匹配盲注——无需回显只要响应差异。
B5 二阶：cn/displayName 落库回读拼 filter（追 persisted_read）。
B6 JSON body 键位注入的"值清洗"假象——清洗值不清键等于零防御。
B7 LDAP 匿名绑定 + filter 永真（`uid=*)(|(uid=*`）——绕过发生在 bind 前后都算。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：给出一条改写语义的具体载荷形态（LDAP 永真 filter/NoSQL `$ne` 绕过/XPath 漂移定位）与入口可达证据；NoSQL `$where` 带用户串 → 按 RCE 邻接升档并挂跨类联动（cmd-injection/deser 卡复查同入口）。band:0 = 拼接形态 + 可控即发卡，无需先闭合语境问句。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 仅内网只读 schema 可控（网络边界引文）或 filter 经参数化 API 构造（引文）→ 降 medium

## ⑩ 根因修复
LDAP：filter 全字面量 + 参数化 API（`search(name, filterExpr, Object[] filterArgs, sc)`），RFC 4515 转义封装为唯一入口；NoSQL：禁 `$where`（改 `$expr`），body 一律 DTO/schema 白名单反序列化，键位 `$` 前缀全局拒绝；XPath：表达式模板化 + XPathVariableResolver/lxml 命名参数；三族共用 lint：查询构造行禁用户输入直接拼接。

## ⑪ 跨边界提示
LDAP 代理网关把上游拼接好的 filter 透传给目录服务（拼接点在上游、执行在下游——两侧都要发卡）；NoSQL 查询对象经消息队列投递到 worker 执行（external_message 载体）；XML 文档来自第三方系统回读后拼 XPath（供应链侧二阶）；$regex 注入与 ReDoS 跨类（-regexp 家族归 cmd-injection 邻接，登记不断档）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 11/22/6、python 8/10/4、ts 8/10/4
`fixtures/enum/injection-misc/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集——见 classes/fixture-spec.md 三类语义）。

# sqli ｜ SQL 注入（CWE-89）

> band: 0 ｜ 模式表: `patterns/sqli-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/sqli/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 可控参数直达 + 无绑定 → High；ORDER BY/LIKE/IN/动态表名列（绑定救不了的位置）→ 同 High；仅 DBA 工具/内网运维通道可达 → 降 Medium（前提引文）

## ① 定义与危害
用户可控输入未经参数化直接拼入 SQL 文本，攻击者改变查询语义（UNION 拖库/堆叠执行/盲注外带）。

## ② Source
HTTP 参数/路径/头部/_body_、消息体（external_message）、**存储回读（persisted_read——二阶注入：上周写入的 payload 本周被拼进查询）**。DB 回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/sqli-java.pattern` / `sqli-ts.pattern` / `sqli-python.pattern`（机器直读，逐行一条，不并串）。

## ④ Propagator
字符串拼接（`+`/模板串/f-string/`format`）、`String.format`、StringBuilder.append 链、ORM 的 `literal()/raw()/orderBy()` 语义透传。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
参数化绑定 `?`/`#{}`/`$1` → **强**（仅当绑定变量本身不被再拼接）；白名单枚举（列名∈固定集合）→ **强**；`escape()`/黑名单过滤/类型转换 SQL 方言不符（addslashes 遇 GBK）→ **弱**；`if(strict)` 才启用 → **上下文条件（只产 hint，禁 kills）**。**多段净化看全部，ORDER BY 等标识符位置绑定无效是"净化与载荷形态不匹配"。**

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（参数/消息/回读）？｜引用:入口签名与取参行｜推翻:实参为编译期常量｜反向:配置开关写入的动态值
C2 SQL 文本是否含拼接变量？｜引用:SQL 构造行±3行｜推翻:纯字面量 SQL｜反向:builder 链末尾的 join
C3 拼接点是否在绑定救不了的位置（列名/表名/ORDER BY/LIKE）？｜引用:拼接片段语法位置｜推翻:值位置且存在绑定重载｜反向:注释声称"已转义"
C4 净化是否消除 SQL 载荷形态（决策表查值）？｜引用:净化调用行+其叶子实现｜推翻:强净化且形态匹配｜反向:净化在假分支/常量条件里
C5 入口可达且鉴权不拦截？｜引用:路由注解/拦截器配置｜推翻:内网-only 且有边界证据｜反向:默认放行配置
C6 错误/响应差异可观测（盲注判定前提）？｜引用:异常处理与响应构造行｜推翻:统一错误吞噬且无时间差｜反向:堆叠查询可用（无需观测）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 `#{}` 全绑定语句——除非绑定变量本身再拼接（需 OBS 链证据）。
FP-2 框架 QueryBuilder 的方法链（`eq()/and()`）——结构化非文本拼接，需 OBS 到 `.raw/.literal` 之外的链。
FP-3 表名拼接但表名来自服务端枚举映射——需 C1 反证引文。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 ORDER BY/LIKE/IN 列名位置的 `${}`/f-string——绑定救不了的位置。
B2 二阶：payload 经 DB 回读后再拼接（追 persisted_read）。
B3 JSON/数组参数展开成 IN 列表的 `join(",")`。
B4 GBK/多字节连接字符集下 addslashes 型"强"净化。
B5 白名单正则自身可被绕过（`^(a|b)$` 的锚缺失）。
B6 动态表名/列名来自配置而配置可被 API 写入。

## ⑨ 利用前提与定级阶梯
见页首；High 验收：专业审查者无需长篇推测即可接受利用路径。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 参数化/预编译引文在位 → refuted 方向；仅 ORDER BY 列名可控且列名白名单校验（引文）→ 降 medium

## ⑩ 根因修复
参数化绑定（标识符位置用白名单映射）；DAO 层禁止拼接入口；ORM raw 接口的 lint 门禁。

## ⑪ 跨边界提示
Egress 侧拼接好的 SQL 片段跨服务传递（反模式但存在）；Ingress 侧消息体直接进查询。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/9/4、python 8/8/3、ts 9/8/3
`fixtures/enum/sqli/{lang}/manifest.tsv`（实际达成 pos/neg/noise：java 12/9/4、python 8/8/3、ts 9/8/3——见 classes/fixture-spec.md 三类语义）。

# log-injection ｜ 日志注入（CWE-117）

> band: 2 ｜ 模式表: `patterns/log-injection-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/log-injection/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: CRLF 伪造日志行（伪造审计/溯源记录、污染 SIEM 解析）→ Low–Medium；凭据/token/PII 直排日志 → Medium–High（联动 secrets-crypto 卡，凭据落日志=泄露可达）；仅无界量日志（非注入语义）→ 本类外（DoS 侧）
> **可类级事实**：本类允许把"日志调用含未净化拼接"作为**类级事实**直接落账（不发逐点评估卡）——判定不依赖入口语境链，是级联低危路径（cascading low-severity）的主样本类；下游聚合规则：同文件 ≥3 处或含凭据字样时升为单张评估卡。

## ① 定义与危害
用户可控输入未经换行/控制字符清洗进入日志流：**CRLF 注入**（`\r\n` 起伪造行——审计日志里伪造"admin login ok"、污染 SIEM/日志分析管道的行边界与解析器）；**ANSI/终端转义序列**（`\x1b[31m` 改控制台/`journalctl` 渲染、藏行、伪造状态色）；**凭据落日志**（口令/token/PII 拼进日志行——凭据管理失效的第二泄露通道，联动 secrets-crypto：**泄露可达即 High 在两卡同真**）。依据：CWE-117/CWE-532（相邻）；log4j2 PatternLayout 无 `%enc` 直排 `%m` 的布局层缺失形态；CWE-117 与 Log4Shell（CWE-948/4xx，JNDI）不同类——本类只管日志流语义，不含查找注入。

## ② Source
HTTP 参数/路径/头部（**User-Agent/Referer 是经典载体——日志直接打 header 值**）、_body_ 字段、消息体（external_message）、异常 message（用户输入进异常文案再 `logger.error(e)`）、**文件名/上传元数据进日志**（联动 path-traversal 侧）、回读值。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/log-injection-java.pattern` / `log-injection-ts.pattern` / `log-injection-python.pattern`（机器直读，逐行一条，不并串）。形态=「日志调用参数含拼接」（`logger.info(` + `+`、模板串/f-string、`%`-格式化直排）+「布局层缺失」（log4j2 `withPattern(…%m…)` 无 `%enc/%replace`、`PatternLayout` 家族标记）。`console.log`/`System.out`/`print(` 计入（stdout 即日志面）但按噪音大户登记——量测基线进 CALIBRATION。

## ④ Propagator
字符串拼接（`+`/模板串/f-string）、`String.format`/`MessageFormat` 展开后再进日志、异常链（`e.getMessage()` 含用户串后 `logger.error("ctx " + e)`）、DTO `toString()` 未脱敏（`logger.info(user.toString())`——拼接藏在 toString 实现里）。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
参数化占位（SLF4J `logger.info("x {}", v)` 的惰性格式化 + 输出层 `\r\n` 剥离）→ **强**（前提：日志后端/appender 有换行过滤；logback `<replace>`/patternlayout `%replace{%m}{[\r\n]}{}` 双保险为强）；结构化日志（pino/winston JSON 字段化 + `redact` 路径）→ **强**（redact 列表覆盖凭据字段才成立）；`replaceAll("[\r\n]"," ")` 手工剥离 → **强**（三值表按形态：剥离 CRLF 即消除行伪造形态）；只剥 `\n` 不剥 `\r` → **弱**；HTML 转义用于日志语境 → **弱**（形态错配——日志要的是控制字符剥离不是 HTML 实体）；ANSI 剥离缺位只做换行剥离 → **上下文条件（只产 hint：影响面限终端渲染，禁 kills）**；脱敏仅正则掩码已知键（`password=` 字样）而值来自自由文本 → **弱**。**多段净化看全部：appender 层有 replace 时调用层拼接降为 hint。**

## ⑥ 判定流程（编号条目）
C1 进入日志的字符串是否外部可控（参数/头部/异常 message/toString）？｜期望引用:取参行与日志调用行的拼接链｜推翻反例:纯字面量消息（`logger.info("started")`）｜反向:UA/Referer 头直排访问日志（最短路径）
C2 日志行是否含换行/回车可控点（拼接 + 后端无 CRLF 剥离）？｜期望引用:日志调用行 + appender/layout 配置｜推翻反例:占位符传参且 layout 带 replace｜反向:`+` 拼接且 PatternLayout 直排 %m
C3 是否有凭据/PII 字样进入日志（password/token/secret/auth 头/身份证号形态）？｜期望引用:日志行实参或 toString 输出字段｜推翻反例:仅业务 id 与状态码｜反向:Authorization 头值整体打印
C4 布局层是否缺 %enc/replace（log4j2 `withPattern` 含 `%m` 无编码）？｜期望引用:PatternLayout 构造行全量｜推翻反例:布局含 `%enc{%m}` 或 `%replace`｜反向:默认布局 + 拼接调用
C5 消费面是否存在（SIEM/审计合规/终端人读）？｜期望引用:日志管道配置或合规声明｜推翻反例:本地调试输出且不落盘｜反向:审计日志进 SIEM（伪造行=合规事件）
C6 净化是否消除载荷形态（决策表查值）？｜期望引用:净化调用行+叶子实现｜推翻反例:CRLF 剥离或结构化+redact 双成立｜反向:净化在假分支/只剥 `\n`

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 SLF4J/logback 占位符传参（`logger.info("u {}", user)`）——LI-J01 要求行内 `+`，占位符形态不命中；命中变体（`logger.info("u {}" + suffix, v)`）按 C2 判。
FP-2 常量拼接（`logger.info("a" + "b")` 编译期折叠）——C1 反证（两侧均字面量）。
FP-3 `System.out.println` 调试残留于 dev-only 分支——C5 反证引文（不落盘不进管道）。
FP-4 异常打印的堆栈行含用户串——堆栈行由框架前缀标记，SIEM 不当独立事件；`e.getMessage()` 直接拼进 message 的部分照常计。
FP-5 日志库自身的拼接（appender 组装行）——LI 家族命中但属日志基础设施非业务注入面。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 `\r`（CR）单字符——只剥 `\n` 的净化下仍折行。
B2 ANSI/OSC 转义（`\x1b[2J` 清屏、`\x1b]0;` 改终端标题）——换行剥离不拦，C5 终端渲染面。
B3 Unicode 同形/零宽字符伪造日志行首时间戳——C5 SIEM 解析面。
B4 日志伪造方向：注入行复制真实前缀格式（`2026-08-23 INFO admin login ok`）——审计侧危害不在机密在信任。
B5 二阶：用户串落库后由定时任务回读打日志（追 persisted_read）。
B6 `toString()` 藏拼接（DTO 字段含用户值，日志行只见 `user.toString()`）——追 toString 实现行。
B7 pino/winston `redact` 路径漏字段（redact 只列 password 漏 authorization）——C3 键位逐一核对。

## ⑨ 利用前提与定级阶梯
见页首。Low–Medium 验收：一条带 `\r\n` 的载荷形态 + 日志管道证据即可（**本类为类级事实主样本——不要求闭合完整五步，按类级事实落账后由聚合规则升卡**）；凭据落日志（C3 成立）按 Medium–High 发单卡并联动 secrets-crypto（泄露可达即 High 同真）。band:2 与 band:0/1 的差别：低危噪音类，聚合优先于逐点；禁止把本类单独作为阻断发布的依据。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: band2——日志无回显/解析消费点 OBS（运维只读流）→ 不应保持 high（low/info）

## ⑩ 根因修复
全站参数化日志（SLF4J 占位符/结构化日志）+ appender 层统一 CRLF/控制字符剥离（logback replace、pino redact、`%enc{%m}`）；凭据/PII 字段进 redact 清单并在 DTO toString 排除；UA/Referer 等 header 值打日志前必经剥离封装；审计日志与调试日志分管道（伪造面隔离）。

## ⑪ 跨边界提示
日志聚合管道把注入行带进 SIEM/合规存档（**伪造在采集侧持久化**——跨边界后不可撤回）；多服务共享日志流时一行注入污染整租户的审计面（联动 authz 侧取证）；凭据落日志后经日志平台外发（三方 SaaS 日志服务=第二泄露通道，secrets-crypto C2 计入）；终端人读面（运维 console）渲染 ANSI（C5 终端分支）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/23/6、python 7/9/3、ts 8/10/4
`fixtures/enum/log-injection/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集——见 classes/fixture-spec.md 三类语义）。

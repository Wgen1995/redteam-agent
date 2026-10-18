# code-injection ｜ 代码注入/SSTI（CWE-94/1336）

> band: 0 ｜ 模式表: `patterns/code-injection-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/code-injection/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 互斥归属（D-010）: 本类只收「代码/表达式/模板文本求值」（eval/SSTI/SpEL parseExpression）；对象图按载荷类型重建归 deser；LDAP/NoSQL/XPath 语义注入归 injection-misc；执行命令进程归 cmd-injection——判据冲突时以更具体类收卡。
> 定级阶梯: 模板/代码文本可控 + 引擎全语义可达（无沙箱或沙箱可逃逸）→ Critical（即 RCE）；受限表达式引擎（白名单函数表/纯算术/禁类型访问，有配置引文）→ 降 Medium（前提引文）；可控的只是模板变量值而模板文本固定 → 转 xss 卡（上下文转义问题，非本类）

## ① 定义与危害
用户可控输入未经隔离直接进入"代码/表达式/模板文本"求值通道——`eval`/`exec`/`new Function`/Node `vm` 直译，或模板引擎按服务端语法渲染攻击者写就的模板（SSTI，CWE-1336：Velocity `evaluate`/`mergeTemplate`、Freemarker `new Template`+`process`、Jinja2 `render_template_string`/`from_string`、ejs `render`）。危害直达 RCE（进程执行/任意文件读写/凭据外带）、内存马植入与横向跳板。SpEL/OGNL/MVEL 同族（SpEL 独立类二期，本期先收 `parseExpression` 形态）。

## ② Source
HTTP 参数/路径/头部/_body_、消息体（external_message）、**存储回读（persisted_read——二阶 SSTI：后台可编辑的邮件/报表/通知模板存库后被回读渲染）**、可被 API 写入的规则/表达式配置项、SSRF 抓回的响应体被当模板消费。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/code-injection-java.pattern` / `code-injection-ts.pattern` / `code-injection-python.pattern`（机器直读，逐行一条，不并串）。`\.process\(`、`Template\(`、`\.render\(` 为家族标记：业务同名方法（pdfRenderer.renderInvoice/orderProcessor.process）一并兜住，安全/危险由五步法判别；`.ftl`/`.vm` 模板文件载体与 MVEL/OGNL/GroovyShell 未列举家族见 ⑧ B7，不进 v1 模式表。

## ④ Propagator
字符串拼接（`+`/模板串/f-string/`format`）、StringBuilder.append 链、`StringReader`/`Buffer.from`/`str()` 载体包装（包装不改语义）、模板名拼接（`"tpl_" + locale + ".vm"` 进模板加载路径）、`atob`/`base64.b64decode`/`bytes.fromhex` 前置解码。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
模板/表达式**文本白名单**（模板名 ∈ 服务端枚举映射、表达式先 parse 再白名单 AST 节点）→ **强**（仅当映射闭合、无通配）；受限沙箱（Jinja2 `SandboxedEnvironment`+`ImmutableSet`、ScriptEngine 进程级隔离/类过滤、MVEL 不可变上下文）→ **上下文条件**（沙箱逃逸面随引擎版本漂移，CVE-2019-12384 族——只产 hint，禁 kills，挂 requires_config）；黑名单关键字（`import`/`Runtime`/`__`）/长度限制 → **弱**（编码与属性链绕过）；HTML 转义用于模板文本 → **弱**（净化与载荷形态不匹配：模板引擎不吃 HTML 实体）。**多段净化看全部；"变量已转义"不构成模板文本的净化是形态错配。**

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（参数/消息/回读/可写配置模板）？｜期望引用:入口签名与取参行、模板编辑端点｜推翻反例:实参为编译期常量｜反向:模板存库后台可编辑后回读渲染
C2 分型：可控的是**模板/代码文本**还是**模板变量值**？｜期望引用:sink 实参构造行——字符串本身含拼接/插值 vs 字面量模板+变量字典｜推翻反例:模板为字面量且仅变量值可控（转 xss 卡输出上下文判据，FP-1）｜反向:render_template_string("Hi " + name)、from_string(user_input)、new Template(name, new StringReader(tpl), cfg)、eval(userExpr) 文本侧可控
C3 求值通道是否全语义（eval/Function/exec/vm、Velocity/Freemarker/Jinja2 原生引擎）？｜期望引用:sink 调用行与引擎构造行｜推翻反例:受限 DSL/纯数据替换（string.Template.substitute、MessageFormat）｜反向:引擎为 SandboxedEnvironment/受限 ScriptContext（仍需 C4 强度证据）
C4 引擎能力面是否可达 RCE 类语义（Jinja2 `__class__` 属性链、Freemarker `?new`/`?api`/objectConstructor、Velocity 反射 class.forName、JS 引擎可 import Java 类）？｜期望引用:引擎构造/版本/沙箱配置行＋payload 形态｜推翻反例:沙箱显式禁类型访问且有版本引文｜反向:引擎默认无沙箱（原生 Environment、ScriptEngineManager、Node vm）
C5 净化是否消除代码/模板载荷形态（决策表查值）？｜期望引用:净化调用行+其叶子实现｜推翻反例:模板名白名单映射闭合｜反向:黑名单只拦 import/__import__ 字面、转义只对 HTML 实体
C6 入口可达且鉴权不拦截？｜期望引用:路由注解/拦截器/中间件｜推翻反例:内网-only 且有边界证据｜反向:模板预览/测试渲染/邮件试发端点默认放行
C7 执行结果可观测（渲染回显/异常回显/时间差/OOB）？｜期望引用:响应构造行/异常处理行｜推翻反例:渲染结果仅入队且无回显｜反向:payload 用时间差或 DNS 探测（无需回显）
C8 二阶形态：模板是否经存储（DB/配置中心/Git 模板库）回读后渲染？｜期望引用:写入点与渲染点两处行号｜推翻反例:模板为打包内只读资源（classpath .vm/.ftl 无写通道）｜反向:运营后台可编辑字段直达渲染引擎

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 字面量模板 + 变量值可控——`render_template("page.html", name=n)`/`new Template(cfg.getTemplate(f))`，模板文本不含可控片段：归 xss 卡判据（C2 推翻形态），需 OBS 模板字面量引文（noise/render-template-file、noise/freemarker-template-file）。
FP-2 `df.eval()/model.eval()/ast.literal_eval`——点前缀/前缀词形态，非动态代码执行（CE-P01/P02 显式边界排除，neg/pandas-eval、neg/ast-literal-eval）。
FP-3 业务 `render(`/`process(` 方法——pdfRenderer.renderInvoice/orderProcessor.process 家族标记命中，需 OBS 到模板引擎类型引文（noise/business-render）。
FP-4 常量实参 `eval("2 + 2")`/`new Function("return 1")`——常量代码无输入通道（suspicion 常量实参 −30 信号，noise/eval-constant）。
FP-5 `string.Template.substitute`——`${}` 文本替换无执行语义（Template 家族标记登记噪音，noise/string-template-safe）。
FP-6 Python `eval` 与 cmd-injection CI-P12 同点重叠——载荷为 shell 形态（`__import__('os').system`）时归 cmd 卡判据；两卡并发按 payload 形态分型，不互相否定。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 Jinja2 SSTI：`{{ ''.__class__.__mro__[1].__subclasses__() }}` 属性链找 Popen；`|attr` 绕点号审计；lipsum/cycler/globals 直达。
B2 Velocity：`$obj.class.forName("java.lang.Runtime")` 反射链；`#set` 装载中间变量。
B3 Freemarker：`<#assign ex="freemarker.template.utility.Execute"?new()>`、`?api`、`objectConstructor`；旧版本内建直达。
B4 SpEL：`T(java.lang.Runtime).getRuntime().exec`、`new String[]{}` 构造（独立类二期，本期已收 parseExpression 形态）。
B5 隐式 eval：TS `setTimeout(userStr, 0)`/`setInterval` 字符串首参、动态 `import(userPath)`；Python `compile(`/`timeit`/`exec` 经 `getattr` 间接。
B6 编码前置：`atob`/`base64.b64decode`/`bytes.fromhex` 解码后进 eval——解码不改可控性（propagator 已计）。
B7 未列举家族：MVEL `MVEL.eval`、OGNL `Ognl.getValue`、Groovy `GroovyShell.evaluate`、Thymeleaf 表达式、`.ftl`/`.vm`/`.pug` 模板文件载体（langpack 扩展名域声明）。
B8 沙箱逃逸：Node `vm` 不是安全边界（this 代理/异常泄露原型）；Jinja2 沙箱旧版可 `__subclasses__` 穿透。
B9 二阶：邮件/报表模板入库后台可编辑，回读渲染（追 persisted_read，C8）。

## ⑨ 利用前提与定级阶梯
见页首。Critical 验收：可演示一次任意代码执行（回显命令输出/文件落盘/OOB 反连），或闭合"可控模板文本（C2）+ 全语义引擎（C3/C4）+ 无有效净化（C5）"三组引文——专业审查者无需长篇推测即可接受利用路径。Medium 档需受限引擎的配置与版本前提引文。band:0 与 band:1 的差别：本类发卡必须先闭合 C2 分型（模板文本 vs 变量值）与 C4 能力面两问，不能只凭 sink 形态命中。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 受限表达式引擎（白名单函数表/纯算术配置引文）→ 降 medium；模板文本固定仅变量可控（转 xss 卡）→ 不属本类定级

## ⑩ 根因修复
模板与数据分离（模板文件 + 变量字典，禁字符串模板入口接收外部文本）；必须动态求值处换受限 DSL（白名单函数表/预编译 AST 校验）；Jinja2 用 SandboxedEnvironment 且跟进版本；ScriptEngine/eval/new Function 移出请求路径；模板后台编辑走审批与隔离渲染；`eval(`/`new Function(`/`render_template_string(`/`from_string(` 进 CI lint 门禁。

## ⑪ 跨边界提示
模板/规则 DSL 存 DB 由运营服务写入、渲染服务回读执行（写入方无害不代表渲染侧无害——读侧引擎决定能力面）；消息体携带表达式进规则引擎/工作流 DSL；SSRF 抓回的响应被当模板渲染（与 ssrf 卡联动挂跨模块证据）；CI/CD 配置模板注入进部署管道二次展开。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 13/23/7、python 8/12/4、ts 8/12/4
`fixtures/enum/code-injection/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集：正例≥6/硬负例≥8/噪音≥3——见 classes/fixture-spec.md 三类语义）。

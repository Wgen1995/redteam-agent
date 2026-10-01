# xss ｜ 跨站脚本（CWE-79）

> band: 1 ｜ 模式表: `patterns/xss-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/xss/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 存储型（payload 落库/缓存后回显他人会话）→ High；反射型/DOM 型参数直达响应或 DOM sink → Medium；回显点在管理员/运营后台且可执行敏感操作 → 升 High（前提引文）；仅自身会话可触发（self-XSS、无跨受害者路径）→ 降 Low（前提引文）

## ① 定义与危害
用户可控输入未经**上下文匹配**转义进入 HTML 响应或 DOM 写入点，攻击者注入脚本/HTML 在受害者浏览器执行——会话窃取、凭据钓取、以受害者身份操作（下单/改密/授权转移）、管理后台接管。三型分型：**存储型**（写入点与回显点分离，落库/缓存后回显）；**反射型**（请求参数直达同次响应）；**DOM 型**（服务端无回显，前端 JS 把 source 写进 sink）。净化档位由输出上下文决定——**净化与上下文不匹配即弱**。

## ② Source
HTTP 参数/路径/头部/_body_（反射型）；**存储回读（persisted_read——存储型核心：评论/昵称/富文本/上传文件名/User-Agent 落库后回显，写入点与回显点常跨服务）**；DOM 型前端 source：`location.hash/search/href`、`document.referrer`、`window.name`、`postMessage` data、`document.cookie`。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/xss-java.pattern` / `xss-ts.pattern` / `xss-python.pattern`（机器直读，逐行一条，不并串）。Java 枚举域为 `*.java` + `*.jsp`（JSP scriptlet/表达式为次级载体，地位同 sqli 的 XML mapper）；`getWriter\(\)`/`out\.print` 为响应写通道家族标记（console/文件 Writer 误报面见 FP-6）；TS `\.html\(` 为 jQuery setter 家族标记（getter 误报见 FP-7）。

## ④ Propagator
字符串拼接（`+`/模板串/f-string/`format`）、未转义插值（f-string 拼 HTML 片段、`String.format("<b>%s")`）、富文本字段整段透传、前端 state→render 链、`innerHTML +=` 累积拼接。跨字段保守传播：同一响应对象多处写出，一处净化不代表全部（C8 一致性）。

## ⑤ Sanitizer（决策表三值——按输出上下文分型查表）

| 净化原语 \ 输出上下文 | HTML body | 属性值（引号内） | JS 代码/字符串 | URL |
|---|---|---|---|---|
| `escapeHtml`/`escapeHtml4`/`html.escape` | 强 | 上下文条件（属性未加引号即破出） | 弱（`&#x27;` 不闭合 JS 串——错配） | 弱 |
| `encodeURIComponent` | 弱（错配） | 弱 | 上下文条件（仅 URL 子上下文） | 强（参数位；scheme 位仍弱） |
| `json.dumps`/`JSON.stringify`（整体含引号） | 上下文条件 | 弱 | 强（数据位；`</script>` 需转 `<\/`） | 弱 |
| DOMPurify.sanitize | 强（富文本白名单） | 强 | 弱 | 弱 |
| `textContent`/`innerText` 写入、模板 `{{ }}`/JSX `{expr}` 文本位 | 强（浏览器/框架自动编码） | 强（值位） | — | — |

黑名单 strip `<>`/关键字过滤 → **弱**；`if(strict)` 才转义 → **上下文条件（只产 hint，禁 kills，挂 requires_config）**；**净化与输出上下文不匹配即弱（错配档）**——查表前提是 C3 上下文分型成立；多段净化看全部。

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（参数/消息/回读/DOM source）？｜期望引用:入口签名与取参行、DOM source 读取行｜推翻反例:实参为编译期常量或服务端枚举映射产出｜反向:落库昵称/评论/User-Agent 回显（persisted_read）
C2 三型分型：存储（入库后回显）/反射（参数直达同跳响应）/DOM（前端 sink 无服务端回显）？｜期望引用:存储=写入点行号+回显点行号；反射=请求取参→响应构造行；DOM=source 读取→sink 写入行｜推翻反例:响应不含可控片段且前端 sink 不读 source｜反向:写读分离跨服务（存储型按 High 起评）
C3 输出上下文分型：HTML body/属性/JS/URL？｜期望引用:sink 行与包裹模板形态（标签体/`attr="…"`/`<script>` 体内/`href=`）｜推翻反例:纯 JSON 响应且 Content-Type 为 json（无 HTML 上下文）｜反向:同一值进属性位且属性未加引号、进 `<script>` 数据位、进 href scheme 位
C4 净化与上下文是否匹配（⑤表查值）？｜期望引用:净化调用行+上下文引文两处｜推翻反例:强档原语且上下文匹配｜反向:escapeHtml 后进 JS/URL（错配档）；净化在假分支/常量条件里
C5 框架自动转义是否默认生效且未被关闭？｜期望引用:模板引擎构造行/框架默认（Flask `render_template` 默认 autoescape、Django 模板 `{{ }}` 默认转义、React JSX `{expr}` 文本插值默认转义、JSTL `c:out` 默认 escapeXml）＋关闭点引文（`autoescape=False`/`[|]safe`/`Markup(`/`mark_safe(`/`dangerouslySetInnerHTML`/`escapeXml="false"`）｜推翻反例:默认开且全链无关闭点（FP-1/FP-2/FP-3）｜反向:裸 `Environment()` 未配置 autoescape、`{% autoescape false %}` 块
C6 sink 是否真写 HTML（innerHTML/write/v-html vs textContent/文本插值）？｜期望引用:sink 调用行形态｜推翻反例:textContent/innerText/nodeValue 写入或 JSX 文本位｜反向:`innerHTML +=` 追加、insertAdjacentHTML、jQuery `.html(`、`document.writeln`
C7 入口可达且鉴权不拦截、存在跨受害者路径（非 self-XSS）？｜期望引用:路由/中间件配置＋回显受众（他人资料页/公共列表/管理后台）｜推翻反例:仅自见字段且无分享/审核展示路径｜反向:回显在公共列表页或管理员浏览器
C8 存储型：写入侧与回显侧净化是否一致（一侧转义一侧裸出）？｜期望引用:写入处理行与回显处理行两处行号｜推翻反例:两处同强档且上下文匹配｜反向:写入侧 escape、回显侧 `mark_safe`/`|safe`

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 Jinja2/Flask 默认自动转义——`render_template` 与 `{{ }}` 插值默认转义；需 OBS 引文：引擎构造行与框架版本（Flask 对 .html 模板默认开 autoescape、Jinja2 `Environment` 需显式/autoselect 配置）。例外已兜：`autoescape=False`（X-P05）、`Markup(`（X-P03）、`mark_safe(`（X-P04）、`[|]safe`（X-P06）。
FP-2 React JSX 默认转义——`{user}` 文本插值经 React 编码，需 OBS 引文：插值位于 JSX 文本/属性值位。例外 `dangerouslySetInnerHTML`（X-T03 已兜，pos/dangerously-createelement）。
FP-3 JSTL `c:out` 默认 escapeXml——neg/jsp-jstl-cout.jsp；例外显式 `escapeXml="false"`（八期外形态，B6）。
FP-4 `textContent`/`innerText`/`nodeValue` 写入与 jQuery `.text()`——浏览器自动编码，非 HTML sink（neg/textcontent-set）。
FP-5 `innerHTML` 读形态与测试断言（`expect(el.innerHTML).toBe`）——读取/比较非写入（neg/innerhtml-read、neg/innerhtml-assert）。
FP-6 `System.out.println`/文件/CSV Writer 的 print/write——console 与文件通道非响应（X-J01/J05/J06 家族标记噪音，noise/system-out-println）。
FP-7 jQuery `.html()` getter——读取返回字符串非写入（noise/jquery-html-get）。
FP-8 JSON API 响应（`jsonify`/`JsonResponse`/`ObjectMapper` 序列化）——json 内容型无 HTML 上下文（noise/make-response-json、noise/getwriter-json）。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 上下文错配：escapeHtml 后进 `<script>` 体/事件属性/URL——HTML 实体不闭合 JS 字符串与 scheme 位。
B2 未引号属性：`<div title={{x}}>` 用空格破出属性进事件位（`onload=`）。
B3 URL 上下文：`javascript:`/`data:` scheme；大小写、Tab/换行、HTML 实体编码变体；只白名单 http 而漏协议相对 `//`。
B4 mXSS：innerHTML 写入再读取序列化（SVG/MathML 嵌套命名空间重排）绕 DOMPurify 旧版。
B5 DOM 型：location.hash/postMessage（无 origin 校验）/window.name 直达 innerHTML/v-html/insertAdjacentHTML。
B6 自动转义关闭链：`{% autoescape false %}` 块、`select_autoescape` 禁用后缀、框架裸 `Environment()`、`escapeXml="false"`。
B7 存储型跨服务：写入侧服务净化、展示侧服务裸回显（C8 不一致）；富文本字段整体 `mark_safe` 只在写侧净化。
B8 次级 sink：jQuery `append(`/`prepend(`、`insertAdjacentHTML`、`document.writeln`、`outerHTML`、iframe `srcdoc`、`setAttribute` 事件属性位。
B9 同值多上下文：一个字段同时进 body 与 href/JS 位，单点净化只覆盖一处（跨字段保守传播的反向利用）。

## ⑨ 利用前提与定级阶梯
见页首。High（存储型）验收：给出写入点→存储→回显点三段引文与一条在受害者会话执行的 payload（或闭合 C2 存储形态+C4 错配/缺失）；反射/DOM Medium 验收：参数直达回显/DOM sink 的单跳引文。band:1 与 band:0 的差别：发卡前必须闭合「三型（C2）+ 输出上下文（C3）+ 框架自动转义默认值（C5）」三问，不能只凭 sink 命中。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 输出上下文转义引文在位或通道仅纯文本邮件/日志（无 HTML 解析消费 OBS）→ 降 low

## ⑩ 根因修复
默认转义模板引擎 + 关闭链进 lint（`autoescape=False`/`mark_safe`/`[|]safe`/`dangerouslySetInnerHTML`/`v-html`）；按输出上下文选编码原语（⑤表，禁跨上下文复用 escapeHtml）；富文本走 DOMPurify 白名单；DOM sink 换 textContent/数据位；CSP 作纵深（非替代转义）；`document.write`/`innerHTML =` 进前端 lint 门禁。

## ⑪ 跨边界提示
存储型写入与回显常跨服务（评论服务写、聚合展示服务渲染——读侧上下文决定净化档，C8 一致性核查跨模块）；API 返回的 HTML 片段被多端消费（App WebView/管理台 v-html 各自上下文）；邮件/导出 HTML 复用同一数据源但无 CSP；SSO/OAuth 回跳参数进前端 DOM sink（与 authz 卡联动）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/22/6、python 8/13/4、ts 9/12/5
`fixtures/enum/xss/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集：正例≥6/硬负例≥8/噪音≥3——见 classes/fixture-spec.md 三类语义）。

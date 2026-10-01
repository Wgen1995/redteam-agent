# open-redirect ｜ 开放重定向（CWE-601）

> band: 1 ｜ 模式表: `patterns/open-redirect-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/open-redirect/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 跳转目标全控可指向任意外域（returnTo/OAuth 回调/登出 next 形）→ Medium-High；Location 携带凭据材料（token/授权码/session 标识）→ High；作为跳板进白名单域链（OAuth 偷码/SSRF 白名单逃逸二跳）→ 按下游类升级；仅站内相对路径强制/白名单域精确匹配 → FP-1 清零路径（需证据）

## ① 定义与危害
服务端把用户可控值放进跳转决定（30x Location / RedirectView / 客户端跳转调用），未把目的地限定在本域白名单或相对路径内。危害=可信域名钓鱼（银行域名的跳转链尾是 evil.com）、OAuth redirect_uri 中转偷授权码、SSRF 白名单逃逸的跳板环（对接 ssrf B3）、Location 携 token 的凭据外带、登出链重放。
**本类为"检查缺失型"：sink 强、判定主体在"目的地约束是否存在"**。跳转调用大量合法（登录成功跳 home），命中只证明"此处发生跳转"；危险=**目的地白名单/相对路径强制缺席**，由 ⑥ 差分判别。本类无专属 guards 段（五段为 authn/authz/csrf/upload-check/rate-limit，边界均不含跳转目的地约束）——**目的地约束事实从 §③ 跳转命中行邻域（±10 行）的 allow/白名单/相对路径断言经五步 OBS 取证**；guards-authz 段的路径级规则与 guards-authn 段的匿名放行事实可作跳板链可达性（B5）的补充面。
**跳转差分**（差分轨主力信号）：按 `source_inventory.family` 分组（login/logout/callback/returnTo/next 形路由族），逐 handler 对照"目的地约束事实"（白名单域集合/相对路径断言/解码后校验）。**面状缺失**（全 family 无约束=跳转 API 被当万能出口，面状 finding）与**点状缺失**（仅 callback/relayState 端点缺约束——OAuth 偷码高危）是两种不同 finding；**同 family 约束不一致→离群必解释**：离群点即 +suspicion 证据，Verifier 的 RUBRIC 给不出离群原因即维持原判。

## ② Source
- **跳转目标参数**：`next/continue/returnTo/redirect/url/target/goto/relayState/state` 形查询参数、path 段、body 字段、cookie 携带的回跳地址。
- **存储回读（persisted_read）**：注册期写入的 callback/回跳 URL 由延迟任务读出再跳（二阶开放重定向）；租户自定义回调域配置可被 API 写入。
- **头部派生**：`Referer`/`Host`/`X-Forwarded-Host` 派生跳转（"跳回来源页"实现——Host 类毒化与 authn B1 同型，差分时两类共引一处 OBS）。

## ③ Sink 模式表指针
`patterns/open-redirect-java.pattern` / `open-redirect-ts.pattern` / `open-redirect-python.pattern`（机器直读，逐行一条，不并串）。锚跳转决定形态：服务端 30x（`sendRedirect`/`res.redirect`/`redirect(`/`RedirectResponse`）、视图前缀（`redirect:`）、视图类（`RedirectView`）、头直写（`"Location"`）、客户端跳转（`window.location.*=`/`location.assign/replace`/`NextResponse.redirect`/`router.push`）。**命中≠漏洞**：跳转点+目标可控+约束缺席三件齐才立案（⑥）。

## ④ Propagator
- URL 拼接（`+`/模板串/f-string/`format`）、`UriComponentsBuilder`/`URLSearchParams` 的 query 透传。
- **解码链**：base64/urldecode 在约束之后执行（先校验后解码=TOCTOU 同型）；双重编码逐层剥离。
- **白名单前缀串接**：`"https://" + allowedHost + "/" + userPath`（用户段注入 `../` 或 `@` 污染 host 位——与 ssrf B10 同型）。
- 跨字段保守传播：回调配置对象整包透传给跳转工具类（约束点与使用点分离多层的封装形态）。

## ⑤ Guard（本类的"Sanitizer"——决策表三值）
```
白名单域精确匹配(host ∈ 固定集合,全等比较)      × 解析后的最终 host × 跳转前 → 强
相对路径强制(/ 开头且拒 // 与 /\ 且无 scheme)     × 解码后的目标值  × 跳转前 → 强
同 host 断言(URL 对象解析后 host 与自身域全等)    × 解析后 host     × 跳转前 → 强
startsWith/endsWith 域名前后缀匹配                × 原始字符串       × 跳转前 → 弱(前缀/参数尾绕过,B4)
仅斜杠前缀检查(不拒 // 与 /\)                     × 原始字符串       × 跳转前 → 弱(协议相对/反斜杠,B1/B2)
先约束后解码(或双重编码未展开)                    × 任意             × 任意   → 弱(约束与载荷形态不匹配,B3/B6)
仅客户端 JS 校验(跳转前的 location 检查)           × 任意             × 任意   → 弱(客户端可绕)
if(config.strict) 才校验                          × 任意             × 任意   → 上下文条件(只产 hint;挂 requires_config)
```
**多段 guard 看全部**：白名单通过但 302 目标可再 302（跳板链逐跳不重评价=ssrf C4 同型）；`上下文条件` 档不产生 kills 事实。

## ⑥ 判定流程（编号条目）
C1 跳转目标是否外部可控（参数/回读/头部派生）？｜期望引用:入口签名与取目标行(next/returnTo/relayState 形)｜推翻反例:目标为编译期常量或服务端枚举映射｜反向:配置可被 API 写入的回调域/存储回读的回跳 URL
C2 目的地是否被强制为相对路径或白名单域（⑤决策表查值）？｜期望引用:校验调用行+其比较基准(与什么集合比对、对哪个变量、比较发生在哪个解码态)｜推翻反例:强档——解析后 host 与固定集合全等、或 / 开头且拒 // 与 /\｜反向:前缀/后缀匹配、仅查 startsWith("/")、约束只写注释
C3 同 family 差分：同形跳转族内兄弟端点谁有目的地约束？｜期望引用:source_inventory.family 分组内各 handler 的 URL 约束事实对照｜推翻反例:全 family 均有约束(差分为零)｜反向:面状缺失(全无)/点状缺失(仅 callback 缺)——**同 family 约束不一致→离群必解释**
C4 约束是否作用于解码后的最终目标（编码/双解码/TOCTOU 窗口）？｜期望引用:校验行与跳转行之间的变量链及解码调用位置｜推翻反例:解码先行且约束对象即最终跳转变量(同一变量同一时刻)｜反向:校验原始参数而跳转另一解码后变量、双层 %252F 逐层逃逸
C5 跳转由服务端 30x 还是客户端驱动（定级与凭据外带面向）？｜期望引用:跳转 sink 行(响应状态+Location vs window.location 赋值)｜推翻反例:服务端 30x 且无敏感材料｜反向:客户端跳转、SPA 路由携带 fragment token
C6 Location/目标 URL 是否携带敏感材料（token/授权码/session 标识/重置令牌）？｜期望引用:URL 构造行的拼接变量清单｜推翻反例:目标仅路径与固定参数｜反向:token/code/session 值拼进目标——升 High(凭据外带)
C7 跳转链是否逐跳重评价（跳板环）？｜期望引用:跳转处理循环与白名单重跑逻辑｜推翻反例:逐跳重跑 C2 白名单或禁多跳｜反向:白名单只在首跳检查、次跳直取 Location

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 固定常量跳转（`return "redirect:/home"`/`res.redirect("/login")`）——需目标常量 OBS（C1 反证引文）。
FP-2 仅 path 可控、host 编译期常量（用户串拼在常量 host 之后的 path 段）——需 C2 拼接位置反证引文。
FP-3 服务端 forward/dispatch（RequestDispatcher/Spring `forward:` 前缀）——不经浏览器非重定向；但 forward 目标可控时归路径遍历/SSRF 类共查。
FP-4 签名覆盖全 URL 的预签名跳转（S3 预签名/OAuth state 绑定 redirect_uri）——需签名验证 OBS。
FP-5 客户端常量导航（`window.location = "/login"`/`router.push("/home")`）——SPA 内部路由表解析，无外域定向；`router.push(userInput)` 仍走 C1（noise 高发形态，见 fixture）。
FP-6 白名单域集合本身服务端固定枚举（回调注册表人工审核）——需白名单数据来源 OBS。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 `//evil.com` 协议相对：仅查 `startsWith("/")` 的相对路径断言直接通过。
B2 `/\evil.com` 反斜杠：浏览器把 `\` 规范化为 `/`，服务端按 `/` 前缀放行；变体 `/\/\`、`\\/`、`/%5C`。
B3 URL 编码：`%2F%2Fevil.com`、双重编码 `%252F%252F`、`%5C`（反斜杠）、混合 `%2F/`——约束点在解码前即全部命中（C4 反向）。
B4 前缀/后缀匹配绕过：`startsWith("https://trusted.com")` → `https://trusted.com.evil.com`（子域植入）与 `https://trusted.com@evil.com`（userinfo）；`endsWith("trusted.com")` → `https://evil.com?x=trusted.com`（参数尾伪造）。
B5 开放跳板链：白名单域上的第二个重定向器（`trusted.com/logout?next=`）、短链服务、已沦陷子域——首跳合法次跳任意；30x 链逐跳变形（对接 ssrf B3）。
B6 回环/嵌套解码：`/redirect?url=%2Fredirect%3Furl%3Dhttps%3A%2F%2Fevil.com`——双层各自解码后逐层逃逸。
B7 scheme 与斜杠混淆：`hTtPs://evil.com`（大小写）、`https:/\evil.com`（少斜杠+反斜杠）、`\/\/evil.com`（JS 注释变体绕客户端校验）；`javascript:`/`data:` 残留目标（老代码 href 注入交叉，XSS 类对接）。
B8 host 位植入：常量域后拼用户子域（`"https://api." + user`）——与 ssrf B10 同型；`@` userinfo 使解析后 host 后移。

## ⑨ 利用前提与定级阶梯
见页首。Medium-High 验收：跨域钓鱼链完整 OBS（参数可控+约束缺席差分+外域目标构造）；携 token/code 升 High（凭据外带证据链）；跳板进 OAuth 授权码的按 authn/oauth 流程共评。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 目标域名白名单引文在位或跳转目标为服务端固定枚举 → 降 low

## ⑩ 根因修复
目的地白名单（解析后 host 精确全等）；相对路径强制（`/` 开头且拒 `//`、`/\`、反斜杠与 scheme）；约束作用于最终解码值；跳板链逐跳重评价；回跳参数单义命名与跳转出口收敛（全站一处 RedirectUtil 出口）；回调域注册表人工审核+注册域与跳转域分离。

## ⑪ 跨边界提示
Egress：OAuth IdP 的回调注册表跨服务共享（跳板链跨信任域，每域独立重评价）；webhook/callback URL 的存储回读由后台 worker 执行跳转（二阶）。Ingress：消息体/任务参数携带回跳 URL（C1 的消息侧变体）；反向代理对 Location 的改写（`X-Forwarded-Host` 拼装）使部署面改变 C2 比较基准。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 10/22/5、python 9/10/4、ts 10/10/4
`fixtures/enum/open-redirect/{lang}/manifest.tsv`。java 全量集 pos≥10/neg≥20/noise≥5；ts、python 起步集 pos≥6/neg≥8/noise≥3。**本类特殊约定：白名单校验/常量目标在场的跳转形态归 noise 不归 neg**——跳转 sink 仍在（pattern 必然命中），安全性由 ⑥ 判别；neg 只放与跳转易混淆的形态（forward/缓存头/CORS/外发 HTTP 等）。

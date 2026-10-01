# csrf ｜ 跨站请求伪造（CWE-352）

> band: 1 ｜ 模式表: `patterns/csrf-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/csrf/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 改密/改邮箱/转账/删数据类写端点无任何 CSRF 防护 → High；写端点仅双提交 cookie 或 SameSite=None 兜底 → Medium-High；仅 SameSite=Lax（GET 顶层导航例外面）→ Medium-High（引文）；只读/幂等端点 → FP-1 清零路径（需证据）

## ① 定义与危害
攻击者页面驱使受害者**已认证浏览器**代发跨站请求，服务端把"浏览器自动携带的 Cookie"当成"用户授权的意图"：状态改变操作在无二次凭据（同步器 token / SameSite 强属性 / 同源校验）下成立。危害=改密改邮箱接管账号、转账下单、改配置删数据、解绑支付渠道。
**本类为"检查缺失型"：sink 弱、判定主体在 guard 侧**。§③ 的 Cookie/Token 形态命中只证明"该处存在防护材料或豁免配置"，不证明安全也不证明危险；危险=**写端点防护事实缺席**，由 guards-csrf 转录（五段之一）+ ⑥ 差分判别。
**防护差分**（差分轨主力信号）：按 `source_inventory.family` 的 param_shape × 写 method 分组（同形路由族），逐 handler 对照 guards-csrf 转录出的防护事实（token 比对 / SameSite 下发 / 同源校验 / 中间件覆盖 / 豁免声明）。**面状缺失**（全 family 无任何防护=系统性默认缺失，suspicion 低但面积大，走面状 finding）与**点状缺失**（个别端点 `csrf().disable`/`csrf_exempt` 豁免，单点高危）是两种不同 finding。**同 family 写端点防护不一致→离群必解释**：离群点本身即 +suspicion 证据，Verifier 的 RUBRIC 必须给出离群原因（新端点漏挂中间件/显式豁免/版本前缀不继承中间件栈），给不出即维持原判。

## ② Source
- **防护材料**（guard 的输入侧）：表单隐藏域 `_csrf`/`csrfToken`、请求头 `X-CSRF-Token`/`X-XSRF-TOKEN`、cookie `XSRF-TOKEN`（双提交对）；SPA 从 `SET_COOKIE` 常量读 token 再回发头的传播链。
- **请求来源标识**（判 C-g 用）：`Origin`/`Referer`/`Sec-Fetch-Site` 头——guard 可能消费的输入；`Referer` 可被剥离、不可被伪造成受害者站内值。
- **攻击可控面**：攻击者能跨站驱动的请求形态（form/IMG/顶层导航）决定哪些 method 与 Content-Type 可被发出——`text/plain` 伪 JSON 与 GET 副作用是两条次级向量（B3/B4）。
- guard 事实的机械来源：`langpacks/{lang}/guards-csrf.md` 转录（五段之一），类页面不重复转录内容。

## ③ Sink 模式表指针
`patterns/csrf-java.pattern` / `csrf-ts.pattern` / `csrf-python.pattern`（机器直读，逐行一条，不并串）。**锚 Cookie/Token 形态而非入口**（`@PostMapping` 等已在 `langpacks/*/sources.pattern`，不重复）：setCookie 族（`addCookie`/`res.cookie`/`set_cookie`）、`SET_COOKIE` 常量、csrfToken/csrf 配置族、SameSite 属性族、豁免形态（`csrf().disable`/`csrf_exempt`）。**命中≠漏洞**：cookie 设置点提供 SameSite/Secure/HttpOnly 下发证据（C4），豁免形态提供"防护被显式关闭"证据（C2 反向），安全/危险由 ⑥ 差分判别。

## ④ Propagator
- token 传播链：模板注入 token → 表单隐藏域 → 服务端比对（比对缺席即 finding 材料）。
- **会话 cookie 配置传播**：SameSite/Secure/HttpOnly 在配置对象/中间件一处设置、作用于全部路由（配置点离消费点远——差分必须对照配置域与路由域是否同一作用面）。
- 子域写 cookie 能力（`Domain=.parent.com` 的既有宽域 cookie）向"双提交可信性"传播（C-g 材料）。
- 跨字段保守传播：token 与会话键不在同一对象时的绑定丢失形态。

## ⑤ Guard（本类的"Sanitizer"——决策表三值）
```
同步器 token(服务端加密随机+会话绑定+每写校验) × 表单/头携带 × 服务端比对   → 强
同源校验(Origin 与 Host 精确匹配+Referer 兜底)   × 头存在性与格式校验 × 写前 → 强(Referer 剥离场景挂 B5 hint)
SameSite=Strict(会话 cookie 真实下发)            × 覆盖全部写路径    × 跳转/表单均生效 → 强(顶层导航例外见 B1)
SameSite=Lax                                     × 顶层 GET 导航例外 × 写端点  → 上下文条件(GET 副作用面照开;只产 hint,禁 kills)
SameSite=None(无 Strict 兜底/无 __Host- 前缀)     × 任意              × 任意    → 弱(显式宽松,叠加 B2 子域种入)
双提交 cookie(cookie 值与头值仅互等比对)          × 无会话侧绑定      × 任意    → 弱(子域可种 cookie,见 C-g)
仅 HttpOnly/Secure 属性                          × 任意              × 任意    → 与 CSRF 正交(挡 XSS 偷取/明文,不挡跨站自动携带)
if(config.strict) 才启用校验                      × 任意              × 任意    → 上下文条件(只产 hint;挂 requires_config 事实)
```
**多段 guard 看全部**：中间件面状覆盖≠handler 点状豁免（`csrf_exempt` 单卡）；框架默认（Spring Security/Django 默认开 CSRF、Express 无默认）需要**配置在场证据**而非框架名推断；`上下文条件` 档不产生 kills 事实（单点误判不剪整类）。

## ⑥ 判定流程（编号条目，含第五要素 C-g）
C1 端点是否状态改变写（非 GET/非幂等/副作用可观测）？｜期望引用:路由 method 与副作用行(写库/发消息/改状态)｜推翻反例:纯只读查询且无副作用语句｜反向:GET 带副作用(REST 违例但 CSRF 向量照样成立,见 B4)
C2 写操作端点的 CSRF 防护是否存在（token/SameSite/同源校验三类任一在场）？｜期望引用:guards-csrf 转录事实行+§③ 形态命中行(配置点/中间件挂载/注解)｜推翻反例:⑤决策表强档 guard 在场且路由在覆盖域内｜反向:豁免形态(csrf().disable/csrf_exempt/excludedRoutes)命中或全无防护材料命中
C3 同 family 差分：同 param_shape×写 method 的兄弟端点谁有防护、谁没有？｜期望引用:source_inventory.family 分组内各 handler 的 guards-csrf 事实对照｜推翻反例:全 family 均有防护(差分为零)｜反向:面状缺失(全无)/点状豁免(个别)——**同 family 写端点防护不一致→离群必解释**(离群点单卡维持直至给出解释)
C4 会话 cookie 的 SameSite/Secure 实际下发形态是什么？｜期望引用:setCookie/SET_COOKIE 命中行±3行的属性链(sameSite/secure/httpOnly/domain)｜推翻反例:SameSite=Strict 或 Lax 且无 None 混用、Domain 未放宽到父域｜反向:SameSite=None;属性缺席(老默认下发);Domain=.parent.com 宽域
C-g guard 输入可信性：token 的比对材料是否可由攻击者单侧决定（双提交 cookie 的 cookie 侧可被子域种入/Referer 剥弃/自研 token 为用户 id 派生）？｜期望引用:token 生成行(熵源/绑定对象)与比对基准来源行(cookie vs 会话)｜推翻反例:token 服务端会话绑定+加密随机+服务端侧比对｜反向:cookie 值与头值仅互等(无会话侧)、token=可预测派生(userId+时间戳)
C5 请求是否在浏览器跨站可发面内（method/Content-Type/自定义头需求）？｜期望引用:入口签名 consumes/method 与解析器配置｜推翻反例:必需自定义头且触发 CORS 预检(非 simple 请求)｜反向:接受 text/plain 的 JSON 解析、multipart 表单、GET 副作用端点
C6 写效应是否无需观测即成立？｜期望引用:响应构造与写后状态行｜推翻反例:仅回执且无差异｜反向:写成功本身即效应(CSRF 与盲注相反——不需要可观测性)

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 只读端点无 CSRF 防护——CSRF 以副作用为前提；需 C1 反证引文（无写语句）。
FP-2 框架默认开 CSRF（Spring Security/Django）——需**配置在场证据**（配置类/依赖声明+无 disable 行）；框架名本身不构成防护证据（显式 `csrf().disable` 恰是本类第一高频真阳性形态）。
FP-3 纯 Bearer/token 头鉴权的无 cookie API——CSRF 依赖浏览器自动携带凭据；需鉴权方式证据（无 cookie 会话）。
FP-4 登录表单 CSRF（登录前无会话可绑 token）——多数框架豁免；登录 CSRF 危害需会话固定/账号预置证据才立案（挂 authn 类 B2）。
FP-5 SameSite 覆盖面误判——配置对象存在≠作用于全部路由（差分要对照配置域与路由域）；需 C4 下发证据而非配置类名。
FP-6 已有独立二次凭据的写端点（旧密码确认/OTP 确认的大额转账）——需二次凭据校验行 OBS。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 SameSite=None + `Domain=.parent.com`：任一子域 XSS/沦陷即可种 cookie；Lax 的 GET 顶层导航例外（`<form method=GET>` 触发 GET 副作用端点）。
B2 双提交 cookie 子域种入：`XSRF-TOKEN` cookie 由 `evil.parent.com` 响应种入，页面 JS 同读同发——互等比对通过（C-g 命中形态）。
B3 Content-Type 滥用：服务端接受 `text/plain` 的 JSON 解析（伪 form 绕 CORS 预检）；老浏览器 `<form enctype=multipart/form-data>` 直发 multipart。
B4 GET 副作用端点（改密/登出/订阅用 GET）：Lax/Strict 均放行顶层导航 GET。
B5 Referer 剥离（`Referrer-Policy: no-referrer`/meta）使存在性检查降级；`https://site.evil.com` 前缀绕 `startsWith` 同源校验。
B6 token 不绑定会话/不一次性（静态隐藏域长期有效、重放有效）——"有 token"≠"token 强"（⑤决策表弱档）。
B7 豁免漂移：`csrf_exempt` 装饰的端点后来长出写逻辑；版本化前缀（/v2/）不继承老路由中间件栈。
B8 cookie host-only 语义错位：宽 Domain cookie 使 SameSite 判定域与站点域不一致（跨子域共享会话形态）。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：跨站页面驱动的请求（攻击者控制页+受害者已认证浏览器）在无二次凭据下完成写效应，OBS 链=路由+防护缺席差分+cookie 下发形态三件齐。改密/改邮箱/转账类写端点无防护即 High；仅 SameSite=Lax 兜底的降档必须有 C4 下发引文。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 仅安全方法（GET 无状态变更 OBS）或 SameSite+token 双引文在位 → 降 low/info

## ⑩ 根因修复
同步器 token 会话绑定+每写校验；SameSite=Lax/Strict 作纵深不作唯一防线；同源校验（Origin 精确匹配+Referer 兜底）；写端点默认拒绝跨站（中间件白名单制豁免）；双提交弃用或改 `__Host-` 前缀+host-only cookie；GET 无副作用纪律；豁免登记表与写逻辑变更联动复核。

## ⑪ 跨边界提示
Egress：子域服务共用父域 cookie（`Domain=.parent.com`）使单一子域失陷放大到全部兄弟站点（C-g 跨服务对照）。Ingress：消息消费者/内部任务无浏览器会话——CSRF 不适用，但同 token 材料被复用为消息鉴权时归 authn 类 B 变体；移动 WebView 的 cookie 隔离缺失是 C4 差分的部署面输入。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 11/22/6、python 9/10/4、ts 9/10/4
`fixtures/enum/csrf/{lang}/manifest.tsv`。java 全量集 pos≥10/neg≥20/noise≥5；ts、python 起步集 pos≥6/neg≥8/noise≥3。**本类特殊约定：SameSite=Strict/secure token 比对在场的 cookie 与中间件形态归 noise 不归 neg**——§③ 形态仍在（pattern 必然命中），安全性由 ⑥ 差分判别；neg 只放与 Cookie/Token 形态易混淆的非防护形态（CORS/缓存头/会话注销等）。

# guards-csrf ｜ lang: java（五段转录规则之一）

> 唯一居所：`langpacks/java/guards-csrf.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 csrf 段转录。
> 类页面对齐：classes/csrf.md **不存在** → **待类页面对齐**（判据先按"状态改变请求是否要求跨站凭证"理解）。

## 1. 段的定义
转录**状态改变请求（POST/PUT/PATCH/DELETE）的防跨站伪造事实**：CSRF token 校验、SameSite cookie 配置、Origin/Referer 校验。不转录：GET 的 CSRF、CORS 配置（浏览器读放行，note 最多）、token 生成方式。
格式：`csrf:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `csrf:none`；纯 bearer 无 cookie 面 `csrf:n-a`（需证据）。

## 2. 封闭来源清单（Java 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| SecurityConfig 的 csrf() 行（CsrfFilter 默认启用） | `csrf:dsl:csrf()@SecurityConfig.java:36` |
| 显式关闭 csrf().disable()（负面事实） | `csrf:dsl:csrf().disable()@SecurityConfig.java:36` |
| CsrfTokenRepository 定制（CookieCsrfTokenRepository/withHttpOnlyFalse） | `csrf:dsl:CookieCsrfTokenRepository@SecurityConfig.java:37` |
| ignoringAntMatchers 豁免路径（转录路径串） | `csrf:dsl:ignore[/api/**]@SecurityConfig.java:39` |
| SameSite：server.servlet.session.cookie.same-site / ResponseCookie.sameSite | `csrf:samesite:same-site=Lax@application.yml:21` / `csrf:samesite:ResponseCookie Lax@CookieUtil.java:30` |
| 手工校验 token/Origin/Referer 的 filter/interceptor | `csrf:inline:checkCsrfToken@CsrfInterceptor.java:27` |
| JSP taglib `<csrf:token>`（回显侧配套，note 前端） | `csrf:taglib:form:csrf@form.jsp:12` |

## 3. 转录边界（什么不算 csrf guard）
- JWT 走 Authorization 头不算防护配置——无 cookie 面即无 CSRF 面，记 `csrf:n-a(bearer)`，需"token 只从 header 读"证据。
- 注释掉的配置不算；`@Profile("dev")` 下的豁免算但挂 `requires_config` 事实。
- 同义框架差异：Spring Security csrf()/Shiro 无内建（自写 filter 按 inline）/自写 X-CSRF-Token 头校验按 inline。
- SameSite=None 显式配置转录为负面事实；SameSite 未设置记 `csrf:samesite:unset`，不按有效防护计。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个被 CSRF 防护覆盖、1 个在豁免清单（节选 3 条）：
```
POST /transfers         csrf:dsl:csrf()@SecurityConfig.java:36
POST /transfers/preview csrf:dsl:ignore[/transfers/preview]@SecurityConfig.java:39   ← 豁免差分
POST /transfers/{id}/confirm  csrf:dsl:csrf()@SecurityConfig.java:36
```
同 family 内"谁被豁免"=点状缺失信号；全链 disable=面状缺失（suspension 低面积大）。
## 5. 绑定有效性核查三跳
1. 配置跳：`grep -rnE 'csrf\(\)|CsrfToken|same-site|sameSite' --include='*.java' --include='*.yml' --include='*.properties' src/`
2. 注册表跳：`grep -rnE '@EnableWebSecurity|SecurityFilterChain|CsrfFilter|addFilterBefore' --include='*.java' src/`（csrf() 行必须在被 @Bean SecurityFilterChain 引用的链内）
3. 处理逻辑跳：`grep -rnE 'CsrfTokenRepository|validateToken|X-CSRF-Token|_csrf|AccessDeniedHandler' --include='*.java' --include='*.jsp' src/`——任一跳空 → `unbound` hint（配置存在但未进过滤链）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```java
http.csrf(c -> c.ignoringAntMatchers("/pay/callback")); @RestController public class PayApi {  // SecurityConfig.java:36
  @PostMapping("/pay/{id}") public void pay(@PathVariable Long id){...}          // L41
  @PostMapping("/pay/callback") public void cb(@RequestBody Cb b){...}          // L44 豁免
  @GetMapping("/pay/{id}/status") public Object st(@PathVariable Long id){...} } // L47 GET 不适用
```
```
POST /pay/{id}       guards: authn:none; authz:none; csrf:dsl:csrf()@SecurityConfig.java:36; upload-check:none; rate-limit:none
POST /pay/callback   guards: authn:none; authz:none; csrf:dsl:ignore[/pay/callback]@SecurityConfig.java:36; upload-check:none; rate-limit:none
GET /pay/{id}/status guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none
```

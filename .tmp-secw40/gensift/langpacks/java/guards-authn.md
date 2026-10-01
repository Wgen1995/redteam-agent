# guards-authn ｜ lang: java（五段转录规则之一）

> 唯一居所：`langpacks/java/guards-authn.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authn 段转录。
> 类页面对齐：authn 类页未建 → **待类页面对齐**（判据先按"是否要求已认证主体"理解）。

## 1. 段的定义
转录**请求到 handler 前是否要求"已认证身份"**：filter/拦截器/注解在何处要求什么凭证（session/JWT/basic）。不转录：认证实现细节（UserDetailsService/密码哈希/token 签发）；死配置（存在但未注册进链）仍转录，挂 `unbound` hint（§5 三跳不过）。
格式：`authn:{来源类型}:{事实摘要}@{file}:{line}`；同段多来源 `;` 连接；全无 `authn:none`。

## 2. 封闭来源清单（Java 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| 方法/类注解 @PreAuthorize("isAuthenticated()")/@Secured/@RolesAllowed | `authn:anno:@PreAuthorize("isAuthenticated()")@Api.java:33` |
| SecurityConfig 的 authorizeRequests/requestMatchers + formLogin/httpBasic/oauth2Login | `authn:dsl:anyRequest().authenticated()@SecurityConfig.java:41` |
| Filter/@Bean Filter 注册（JwtAuthFilter）与 web.xml security-constraint | `authn:registry:JwtAuthFilter@FilterConfig.java:25` / `authn:webxml:security-constraint@web.xml:18` |
| HandlerInterceptor preHandle 认证断言（401） | `authn:inline:preHandle reject 401@AuthInterceptor.java:29` |
| 基类继承（BaseController 带认证约束） | `authn:inherit:BaseAuthController@Base.java:12（转录基类行+继承链）` |
| @PermitAll/permitAll() 显式放行 | `authn:anno:@PermitAll@Api.java:27` |
| Shiro filterChainDefinitionMap("/api/**"→authc) | `authn:dsl:shiro authc@ShiroConfig.java:20` |

## 3. 转录边界（什么不算 authn）
- 业务校验不算：`if (user == null)` 只校验领域对象，未绑请求主体凭证。
- 注释/TODO 不算；`@Deprecated` 开关不算——需运行时证据（注解能被字节码扫描命中）。
- permitAll()/anonymous() 是**显式匿名事实**（转录，供差分与 FP-1 判读），不是"缺失"。
- 同义框架差异：@Secured(JSR-250)/@RolesAllowed(jakarta)/@PreAuthorize(SpEL) 等价转录，note 记框架。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点，11 个有认证约束、1 个没有（节选 3 条）：
```
GET /api/orders       authn:anno:@PreAuthorize("isAuthenticated()")@OrderApi.java:31
GET /api/orders/{id}  authn:none   ← 差分信号：family 内点状缺失
POST /api/orders      authn:anno:@PreAuthorize("isAuthenticated()")@OrderApi.java:52
```
## 5. 绑定有效性核查三跳
1. 注解/配置跳：`grep -rnE '@PreAuthorize|@RolesAllowed|@Secured|@PermitAll' --include='*.java' src/`
2. 注册表跳：`grep -rnE '@EnableWebSecurity|@EnableGlobalMethodSecurity|authorizeRequests|requestMatchers|addFilter|FilterRegistrationBean' --include='*.java' src/`
3. 处理逻辑跳：`grep -rnE 'OncePerRequestFilter|preHandle|AuthenticationEntryPoint|UserDetailsService' --include='*.java' src/`——任一跳空 → 挂 `unbound` hint，禁直接计为有效 guard。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```java
@RestController public class DocApi { @PreAuthorize("isAuthenticated()") @GetMapping("/docs/{id}") public Doc get(@PathVariable Long id){...}  // L30
  @PostMapping("/docs") public Doc create(@RequestBody Doc d){...}                        // L33 无注解
  @GetMapping("/public/status") public String status(){ return "ok"; } }                  // L35
```
```
GET /docs/{id}     guards: authn:anno:@PreAuthorize("isAuthenticated()")@DocApi.java:30; authz:none; csrf:none; upload-check:none; rate-limit:none
POST /docs         guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /public/status guards: authn:none(公开路由,差分候选); authz:none; csrf:none; upload-check:none; rate-limit:none
```

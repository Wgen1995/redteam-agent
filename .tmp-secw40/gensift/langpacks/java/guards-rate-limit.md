# guards-rate-limit ｜ lang: java（五段转录规则之一）

> 唯一居所：`langpacks/java/guards-rate-limit.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 rate-limit 段转录。
> 类页面对齐：rate-limit 类页未建 → **待类页面对齐**（判据先按"单主体短时高频请求是否被限流"理解）。

## 1. 段的定义
转录**限流/防暴力枚举事实**：注解式限流、filter/interceptor 内计数器、网关配置（本地证据才录）。不转录：前端节流、仅日志/监控告警（无拒绝行为）。账户锁定/验证码算邻接段——转录进本段并 note `lockout`/`captcha`（差分时单独读）。
格式：`rate-limit:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `rate-limit:none`。

## 2. 封闭来源清单（Java 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Bucket4j 注解/声明（@RateLimit 自定义、Bucket bean、bucket4j-http） | `rate-limit:anno:@RateLimit(10/min)@Api.java:35` |
| Resilience4j @RateLimiter（Spring Cloud 等价物） | `rate-limit:anno:@RateLimiter(name="auth")@Api.java:41` |
| Filter/Interceptor 内计数（Redis INCR+EXPIRE / Guava RateLimiter） | `rate-limit:inline:redis incr 5/min@ThrottleFilter.java:33` |
| SecurityConfig failureHandler 的登录账户锁定 | `rate-limit:inline:lockout 3 fails@SecurityConfig.java:47` |
| spring.cloud.gateway 的 RequestRateLimiter + RedisRateLimiter | `rate-limit:config:RequestRateLimiter 10/s@gw.yml:12` |
| 登录前验证码/二次验证配套 | `rate-limit:inline:captcha required@LoginApi.java:29` |
| web.xml 无内建（缺位本身是事实） | `rate-limit:none`（不虚构等价物） |

## 3. 转录边界（什么不算 rate-limit）
- 数据库唯一约束、幂等键不算（并发正确性不是限流）。
- 注释/TODO 不算；`log.warn` 频率告警不算（无拒绝行为证据）。
- 同义框架差异：Bucket4j/Resilience4j/Guava RateLimiter/自研 Redis 计数等价转录，note 记实现。
- Nginx/Envoy 外层限流只在配置文件**在仓库内**时转录（否则按 FP-3 边界证据处理，不凭叙事）；限流 key 取 X-Forwarded-For（可伪造）仍转录，key 可信性归 C-g 同型判读。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个有限流、1 个没有（节选 3 条）：
```
POST /login          rate-limit:anno:@RateLimit(5/min)@AuthApi.java:30
POST /token/refresh  rate-limit:none   ← 点状缺失：可无限刷 token
POST /logout         rate-limit:anno:@RateLimit(5/min)@AuthApi.java:48
```
登录/验证类端点的 family 内缺失=暴力枚举面；只对 GET 限流而对枚举型 POST 不限=形态不一致信号。
## 5. 绑定有效性核查三跳
1. 注解/配置跳：`grep -rnE '@RateLimit|@RateLimiter|RateLimiter|Bucket4j|RequestRateLimiter|replenishRate' --include='*.java' --include='*.yml' src/`
2. 注册表跳：`grep -rnE 'addFilterBefore|addInterceptors|FilterRegistrationBean|CircuitBreaker|RateLimiterRegistry' --include='*.java' src/`（注解式限流生效前提：aspect/bean 注册存在）
3. 处理逻辑跳：`grep -rnE 'tryConsume|acquire\(\)|INCR|EXPIRE|429|TOO_MANY_REQUESTS' --include='*.java' src/`——任一跳空 → `unbound` hint（注解在但 aspect 未注册=死注解）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```java
@RestController public class AuthApi { @RateLimit(key="ip", value=5, window=MINUTES)       // L29
  @PostMapping("/login") public Token login(@RequestBody Cred c){...}                      // L31
  @PostMapping("/token/refresh") public Token refresh(@RequestBody R r){...}               // L34 无限流
  @GetMapping("/health") public String health(){ return "ok"; } }                          // L37
```
```
POST /login         guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:anno:@RateLimit(5/min)@AuthApi.java:29
POST /token/refresh guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /health         guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none(公开健康检查,差分豁免候选)
```

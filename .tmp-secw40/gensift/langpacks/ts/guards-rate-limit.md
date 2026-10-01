# guards-rate-limit ｜ lang: ts（五段转录规则之一）

> 唯一居所：`langpacks/ts/guards-rate-limit.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 rate-limit 段转录。
> 类页面对齐：rate-limit 类页未建 → **待类页面对齐**（判据先按"单主体短时高频请求是否被限流"理解）。

## 1. 段的定义
转录**限流/防暴力枚举事实**：express-rate-limit 类中间件、Nest Throttler、自写计数。不转录：前端节流、仅日志告警（无拒绝行为）。账户锁定/验证码转录进本段并 note `lockout`/`captcha`。
格式：`rate-limit:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `rate-limit:none`。

## 2. 封闭来源清单（TS 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| express-rate-limit（rateLimit({windowMs,max})） | `rate-limit:mw:rateLimit 5/15min@app.ts:26` |
| 路由级 limiter（loginLimiter 挂特定 router.post） | `rate-limit:mw:router-level loginLimiter 5/15min@auth.ts:30` |
| Nest @Throttle/@SkipThrottle + ThrottlerGuard | `rate-limit:anno:@Throttle(5,60)@auth.controller.ts:22` |
| Nest ThrottlerModule 全局配置 | `rate-limit:config:ThrottlerModule 10/60s@app.module.ts:18` |
| @SkipThrottle 豁免（负面事实） | `rate-limit:anno:@SkipThrottle@api.controller.ts:31` |
| fastify-rate-limit 插件注册 | `rate-limit:mw:fastify-rate-limit 100/min@app.ts:20` |
| 自写计数（Redis INCR+EXPIRE 中间件）/ 账户锁定 | `rate-limit:inline:redis incr 10/min@limit.mid.ts:14` / `rate-limit:inline:lockout 3 fails@auth.service.ts:55` |

## 3. 转录边界（什么不算 rate-limit）
- 幂等键/唯一约束不算限流；PM2 cluster 均衡不算。
- 注释/README 不算；`console.warn` 频率告警不算（无 429/拒绝证据）。
- 同义框架差异：express-rate-limit/rate-limiter-flexible/Nest Throttler/fastify-rate-limit 等价转录，note 记实现。
- keyGenerator 用 `req.ip`（代理下取 X-Forwarded-For 可伪造）仍转录，key 可信性归 C-g 同型判读；Nginx 外层限流仅当配置文件在仓库内转录。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个有限流、1 个漏（节选 3 条）：
```
POST /login         rate-limit:mw:router-level loginLimiter 5/15min@auth.ts:20
POST /token/refresh rate-limit:none   ← 点状缺失：可无限刷 token
POST /logout        rate-limit:mw:router-level loginLimiter 5/15min@auth.ts:22
```
登录/验证类端点的 family 内缺失=暴力枚举面；只对 GET 限流而对枚举型 POST 不限=形态不一致信号。
## 5. 绑定有效性核查三跳
1. 配置跳：`grep -rnE 'rateLimit|rate-limit|Throttle|Throttler|RateLimiter|windowMs|max:' --include='*.ts' src/`
2. 注册表跳：`grep -rnE 'app\.use\([a-zA-Z]*[Ll]imit|router\.(post|get|put|delete)\(|register\(|ThrottlerModule|APP_GUARD' --include='*.ts' src/`（limiter 生效前提：在链上且位于路由处理前；ThrottlerGuard 需全局或显式挂载）
3. 处理逻辑跳：`grep -rnE '429|TooManyRequests|INCR|hitCount|skipIf' --include='*.ts' src/`——任一跳空 → `unbound` hint（limiter 定义了没 use / ThrottlerModule 未 import）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```ts
const limiter = rateLimit({ windowMs: 60_000, max: 5 });   // app.ts:20
router.post('/login', limiter, login);                     // routes.ts:30
router.post('/token/refresh', refresh);                    // routes.ts:31 无 limiter
router.get('/health', health);                             // routes.ts:32
```
```
POST /login         guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:mw:router-level limiter 5/60s@routes.ts:30
POST /token/refresh guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /health         guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none(公开健康检查,差分豁免候选)
```

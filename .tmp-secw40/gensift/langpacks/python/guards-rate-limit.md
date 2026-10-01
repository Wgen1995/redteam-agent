# guards-rate-limit ｜ lang: python（五段转录规则之一）

> 唯一居所：`langpacks/python/guards-rate-limit.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 rate-limit 段转录。
> 类页面对齐：rate-limit 类页未建 → **待类页面对齐**（判据先按"单主体短时高频请求是否被限流"理解）。

## 1. 段的定义
转录**限流/防暴力枚举事实**：装饰器限流、middleware、DRF throttle_classes、FastAPI 依赖式 limiter。不转录：前端节流、仅日志/告警（无拒绝行为）。账户锁定/验证码转录进本段并 note `lockout`/`captcha`。
格式：`rate-limit:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `rate-limit:none`。

## 2. 封闭来源清单（Python 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| django-ratelimit @ratelimit(key='ip', rate='5/m') | `rate-limit:decorator:@ratelimit(5/m)@views.py:28` |
| DRF throttle_classes=[AnonRateThrottle] | `rate-limit:throttle:throttle_classes[AnonRateThrottle 5/min]@views.py:35` |
| settings 全局 DEFAULT_THROTTLE_CLASSES/RATES | `rate-limit:settings:DEFAULT_THROTTLE_RATES anon=5/min@settings.py:120` |
| FastAPI 依赖式 limiter（Depends(limiter.limit("5/minute"))） | `rate-limit:depends:Depends(limiter 5/minute)@api.py:32` |
| slowapi @limiter.limit 装饰器 | `rate-limit:decorator:@limiter.limit(5/minute)@api.py:26` |
| 自写中间件计数（cache.incr+timeout / redis） | `rate-limit:inline:cache incr 10/min@mid.py:18` |
| django-axes 账户锁定（AXES_FAILURE_LIMIT）/ 验证码配套 | `rate-limit:inline:lockout axes 3 fails@settings.py:140` / `rate-limit:inline:captcha required@views.py:52` |

## 3. 转录边界（什么不算 rate-limit）
- 幂等/唯一约束不算限流；异步任务队列并发数不算。
- 注释/docstring 不算；`logging.warning` 计数不算（无 429/拒绝证据）。
- 同义框架差异：django-ratelimit/DRF throttle/slowapi/flask-limiter/django-axes 等价转录，note 记实现。
- limiter key 取 `request.META["X-Forwarded-For"]`（可伪造）仍转录，key 可信性归 C-g 同型判读；Nginx/网关限流仅当配置文件在仓库内转录（否则 FP-3 边界证据处理）。
- DRF throttle 生效前提是 throttle 类在 settings 或 view 上；装饰器用于 CBV 需 method_decorator（§5 第二跳核）。

## 4. 差分判据接口（同 family 不一致）
同 router 12 端点 11 个有限流、1 个漏（节选 3 条；登录/验证类端点的 family 内缺失=暴力枚举面，只对 GET 限流而对枚举型 POST 不限=形态不一致信号）：
```
POST /login         rate-limit:decorator:@ratelimit(5/m)@views.py:20
POST /token/refresh rate-limit:none   ← 点状缺失：可无限刷 token
POST /logout        rate-limit:decorator:@ratelimit(5/m)@views.py:28
```
## 5. 绑定有效性核查三跳
1. 装饰/配置跳：`grep -rnE 'ratelimit|throttle|Throttle|limiter|rate=|AXES_FAILURE' --include='*.py' src/`
2. 注册表跳：`grep -rnE 'MIDDLEWARE|DEFAULT_THROTTLE|Limiter\(|urlpatterns|include_router|method_decorator' --include='*.py' src/`（django-ratelimit 需 cache 后端可用；slowapi 需 app.state.limiter 与 exception handler 注册）
3. 处理逻辑跳：`grep -rnE 'Ratelimited|429|TooManyRequests|incr\(|cache\.|WasLimited' --include='*.py' src/`——任一跳空 → `unbound` hint（装饰器在但 cache 未配置=限流不生效；limiter 实例未挂 app）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```python
@ratelimit(key="ip", rate="5/m")                       # views.py:20
def login(request): ...                                 # views.py:22 POST
def token_refresh(request): ...                         # views.py:25 POST 无限流
def health(request): return JsonResponse({"ok": True})  # views.py:28 GET
```
```
POST /login         guards: authn:none; authz:none; csrf:middleware:CsrfViewMiddleware@settings.py:106; upload-check:none; rate-limit:decorator:@ratelimit(5/m)@views.py:20
POST /token/refresh guards: authn:none; authz:none; csrf:middleware:CsrfViewMiddleware@settings.py:106; upload-check:none; rate-limit:none
GET /health         guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none(公开健康检查,差分豁免候选)
```

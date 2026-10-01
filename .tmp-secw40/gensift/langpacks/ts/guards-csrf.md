# guards-csrf ｜ lang: ts（五段转录规则之一）

> 唯一居所：`langpacks/ts/guards-csrf.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 csrf 段转录。
> 类页面对齐：classes/csrf.md **不存在** → **待类页面对齐**（判据先按"状态改变请求是否要求跨站凭证"理解）。

## 1. 段的定义
转录**状态改变请求的 CSRF 防护事实**：csurf 中间件、SameSite cookie 配置、Origin/自定义 token 校验。不转录：GET 的 CSRF、CORS 放行（note 最多）、token 签发细节。
格式：`csrf:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `csrf:none`；纯 bearer 无 cookie 面 `csrf:n-a`（需证据）。

## 2. 封闭来源清单（TS 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| csurf 中间件 app.use(csrf())（含 ignoreMethods/ignoreUrls 豁免） | `csrf:mw:app.use(csrf())@app.ts:24` / `csrf:mw:ignoreUrls[/webhook]@app.ts:25` |
| 路由级 csurf 或自写校验中间件（比对 _csrf/X-CSRF-Token） | `csrf:mw:router-level tokenCheck@routes.ts:35` |
| Nest CSRF 模块（@Csrf()/csrf-guard） | `csrf:guard:@Csrf()@app.controller.ts:16` |
| cookie 显式 SameSite（res.cookie(...,{sameSite:'strict'})） | `csrf:samesite:res.cookie sameSite=strict@auth.ts:41` |
| 会话 cookie 配置（express-session cookie.sameSite） | `csrf:samesite:session sameSite=lax@app.ts:28` |
| helmet/csurf 组合中的 token 校验 handler | `csrf:inline:verify token 403@mid.ts:20` |
| JWT 只走 Authorization 头（无 cookie 面） | `csrf:n-a(bearer header)@auth.ts:33` |

## 3. 转录边界（什么不算 csrf guard）
- SameSite=None 显式配置转录为负面事实；仅前端附带 token（fetch 拦截器）不算。
- 注释/文档不算；测试里中间件不算。
- 同义框架差异：csurf（Express，已废弃仍在用→事实优先，废弃进 note）/@nestjs/csrf/fastify-csrf/Koa 中间件等价转录。
- `sameSite` 未设置（浏览器默认行为随版本变）记 `csrf:samesite:unset`，不按有效防护计。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个被 CSRF 中间件覆盖、1 个豁免（节选 3 条）：
```
POST /pay/:id        csrf:mw:app.use(csrf())@app.ts:24
POST /pay/webhook    csrf:mw:ignoreUrls[/pay/webhook]@app.ts:24   ← 豁免差分（handler 有状态改变）
POST /pay/:id/refund csrf:mw:app.use(csrf())@app.ts:24
```
同 family 内"谁被豁免"=点状缺失；全链无 csurf=面状缺失（suspension 低面积大）。
## 5. 绑定有效性核查三跳
1. 中间件/配置跳：`grep -rnE 'csurf|csrf|sameSite|same-site|x-csrf|_csrf' --include='*.ts' --include='*.json' src/`
2. 注册表跳：`grep -rnE 'app\.use\(|router\.use\(|@Csrf|cookieParser|APP_GUARD' --include='*.ts' src/`（csurf 生效前提：真被 use 且在路由注册之前——顺序错=不生效）
3. 处理逻辑跳：`grep -rnE "req\.csrfToken|validate|403|ForbiddenException|sameSite:\s*'(lax|strict|none)'" --include='*.ts' src/`——任一跳空 → `unbound` hint（典型：csurf 在 router 之后 use）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```ts
app.use(session({ cookie: { sameSite: 'lax' } })); app.use(csrf({ ignoreUrls: ['/pay/webhook'] }));  // app.ts:22,24
router.post('/pay/:id', pay);           // routes.ts:30
router.post('/pay/webhook', webhook);   // routes.ts:31
router.get('/pay/:id/status', status);  // routes.ts:32
```
```
POST /pay/:id       guards: authn:none; authz:none; csrf:mw:app.use(csrf())@app.ts:24;csrf:samesite:session sameSite=lax@app.ts:22; upload-check:none; rate-limit:none
POST /pay/webhook   guards: authn:none; authz:none; csrf:mw:ignoreUrls[/pay/webhook]@app.ts:24; upload-check:none; rate-limit:none
GET /pay/:id/status guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none
```

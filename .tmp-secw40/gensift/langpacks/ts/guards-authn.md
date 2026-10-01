# guards-authn ｜ lang: ts（五段转录规则之一）

> 唯一居所：`langpacks/ts/guards-authn.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authn 段转录。
> 类页面对齐：authn 类页未建 → **待类页面对齐**（判据先按"是否要求已认证主体"理解）。

## 1. 段的定义
转录**请求到 handler 前是否要求"已认证身份"**：全局/路由级中间件、Nest Guard、装饰器的认证事实。不转录：passport strategy 内部实现、JWT 验签细节；死绑定（中间件写了没 use）仍转录并挂 `unbound` hint。
格式：`authn:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `authn:none`。

## 2. 封闭来源清单（TS 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Express 全局中间件 app.use(passport.authenticate('jwt')/expressjwt) | `authn:mw:app.use(passport.authenticate('jwt'))@app.ts:22` |
| 路由级中间件（router.post('/x', requireAuth, h)） | `authn:mw:router-level requireAuth@routes.ts:31` |
| Nest @UseGuards(JwtAuthGuard)（方法/控制器级） | `authn:guard:@UseGuards(JwtAuthGuard)@user.controller.ts:18` |
| Nest APP_GUARD provider 全局注册 | `authn:guard:APP_GUARD JwtAuthGuard@app.module.ts:25` |
| 自定义装饰器（requireAuth/@Auth()） | `authn:decorator:@Auth()@api.ts:40` |
| 公开路由显式标注（@Public()/whitelist 路径表） | `authn:decorator:@Public()@api.ts:28` |
| 基类 controller 继承（BaseController 带 guard） | `authn:inherit:BaseController@base.controller.ts:10（转录基类行+继承链）` |

## 3. 转录边界（什么不算 authn）
- 业务校验不算：`if (!req.body.user)` 是字段检查非主体凭证校验。
- 注释/README 不算；前端路由守卫（客户端 router guard）不算——需服务端证据；测试文件不算。
- 同义框架差异：Express middleware/Nest Guard/Fastify preHandler/Koa middleware 等价按各自形态转录，note 记框架。
- guard 抛 401 依赖下一跳处理逻辑（§5），转录不做生效假定。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个有认证、1 个漏（节选 3 条；类级 @UseGuards 覆盖、@Public 豁免、裸 router 漏挂三种形态）：
```
GET /users/:id          authn:guard:@UseGuards(JwtAuthGuard)@user.controller.ts:15（类级继承）
GET /users/:id/preview  authn:decorator:@Public()@user.controller.ts:20（显式豁免）
POST /users/:id/export  authn:none   ← 点状缺失：挂在无 guard 的裸 router 上
```
面状缺失（全 none）与点状缺失（个别 none）分别成 finding；全有则差分为零。
## 5. 绑定有效性核查三跳
1. 装饰/声明跳：`grep -rnE 'UseGuards|@Public|passport\.authenticate|requireAuth|APP_GUARD' --include='*.ts' src/`
2. 注册表跳：`grep -rnE 'app\.use\(|router\.(get|post|put|patch|delete)\(|providers:|APP_GUARD|configure\(' --include='*.ts' src/`（Nest：guard 类必须在 providers 或 APP_GUARD 注册；中间件必须被 use）
3. 处理逻辑跳：`grep -rnE 'canActivate|jwt\.verify|expressjwt|401|UnauthorizedException' --include='*.ts' src/`——任一跳空 → `unbound` hint（guard 类写了未注册 / 中间件未被 use）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```ts
router.get('/docs/:id', requireAuth, (req, res) => res.json(load(req.params.id)));   // routes.ts:30
router.post('/docs', (req, res) => res.json(create(req.body)));                      // routes.ts:31 无 guard
router.get('/status', (req, res) => res.send('ok'));                                 // routes.ts:32
```
```
GET /docs/:id  guards: authn:mw:router-level requireAuth@routes.ts:30; authz:none; csrf:none; upload-check:none; rate-limit:none
POST /docs     guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /status    guards: authn:none(公开路由,差分候选); authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none
```

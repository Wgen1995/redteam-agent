# guards-authz ｜ lang: ts（五段转录规则之一）

> 唯一居所：`langpacks/ts/guards-authz.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authz 段 + authz.md §①C3/C4/C-g 机械事实源。
> 类页面对齐：classes/authz.md ②⑤⑥——本文件只转录事实，强弱与 C-g 判读归 Analyzer。

## 1. 段的定义
转录**"当前主体被允许做什么"的服务端约束**：角色 Guard、路由级授权中间件、属主检查的存在事实。不转录：判据是否可伪造（C-g 判读，转录附判据来源行）；DB RLS。
格式：`authz:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `authz:none`；属主约束前缀 `authz:owner:`。

## 2. 封闭来源清单（TS 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Nest @UseGuards(RolesGuard) + @Roles('admin') 组合 | `authz:guard:@Roles('admin')+RolesGuard@user.controller.ts:20` |
| Nest @SetMetadata('roles',[...]) 自定义元数据 | `authz:decorator:@SetMetadata roles[admin]@api.ts:33` |
| 中间件/路由级角色断言（checkRole('admin') 在链上） | `authz:mw:router-level checkRole(admin)@routes.ts:28` |
| handler 首行角色断言（if req.user.role!=='admin' throw） | `authz:inline:roleAssert admin@user.controller.ts:41` |
| 基类 controller 继承（BaseAdminController 带 RolesGuard） | `authz:inherit:BaseAdminController@base.controller.ts:12（转录基类行+继承链）` |
| 属主约束进查询（findOne({where:{id,userId}})） | `authz:owner:where{id,userId}@repo.ts:22` |
| 取出后比对属主（findOne 后 if o.userId!==user.id throw） | `authz:owner:postCheck userId@user.controller.ts:52（挂 B6 TOCTOU hint）` |

## 3. 转录边界（什么不算 authz）
- 业务校验不算：状态机/额度/字段格式检查不是主体权限。
- 注释不算；测试文件里的 guard 不算（需运行时证据）。
- authn/authz 分段不混：`canActivate` 只验登录 → authn 段；验 role/属主 → authz 段（一个 Guard 可两段各记）。
- 同义框架差异：Nest Guard/Express 中间件/typeorm defaultScope/自研 RBAC 表按各自形态转录，note 记框架；`req.user.role` 直读未验签 JWT claim 仍转录（C-g 反向证据）。

## 4. 差分判据接口（同 family 不一致）
同 param_shape 路由族（GET /users/:id 族）12 端点 11 个有角色约束 1 个没有（节选 3 条）：
```
GET /users/:id        authz:decorator:@Roles('admin')+RolesGuard@user.controller.ts:30
GET /users/:id/theme  authz:none   ← 点状缺失：family 内不一致=+suspicion
GET /users/:id/logs   authz:decorator:@Roles('admin')+RolesGuard@user.controller.ts:36
```
C3 消费：面状缺失（全 none，系统性默认缺失）与点状缺失（个别 none，单点高危）分别成 finding；全有则差分为零。
## 5. 绑定有效性核查三跳
1. 装饰/声明跳：`grep -rnE "@Roles|@SetMetadata|checkRole|hasRole|req\.user\.role|isStaff" --include='*.ts' src/`
2. 注册表跳：`grep -rnE 'UseGuards|APP_GUARD|providers:|router\.(get|post|put|patch|delete)\(' --include='*.ts' src/`（@Roles 生效前提：解析元数据的 RolesGuard 真挂在该路由链上）
3. 处理逻辑跳：`grep -rnE 'where:\s*\{|ForbiddenException|403|findOne\(|getOrThrow' --include='*.ts' src/`——任一跳空 → `unbound` hint（@Roles 在而 RolesGuard 未挂=装饰不生效）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```ts
@Controller('orders') @UseGuards(RolesGuard) export class OrderController {              // order.controller.ts:18
  @Delete(':id') @Roles('admin') del(@Param('id') id: string) {...}                      // L20
  @Get(':id') get(@Param('id') id: string, @User() u) { return repo.orders.findOne({ where: { id, userId: u.id } }); }
  @Post() create(@Body() dto: OrderDto) { return repo.orders.save(dto); } }              // L26 无 authz
```
```
DELETE /orders/:id guards: authn:none; authz:decorator:@Roles('admin')+RolesGuard@order.controller.ts:20; csrf:none; upload-check:none; rate-limit:none
GET /orders/:id    guards: authn:none; authz:owner:where{id,userId}@order.controller.ts:23; csrf:none; upload-check:none; rate-limit:none
POST /orders       guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none   ← 差分候选
```

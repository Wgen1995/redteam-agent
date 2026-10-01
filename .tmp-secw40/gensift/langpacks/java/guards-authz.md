# guards-authz ｜ lang: java（五段转录规则之一）

> 唯一居所：`langpacks/java/guards-authz.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authz 段 + authz.md §①C3/C4/C-g 机械事实源。
> 类页面对齐：classes/authz.md ②⑤⑥（guard 决策表、C-g、family 差分）——本文件只转录事实，不做强弱判。

## 1. 段的定义
转录**"当前主体被允许做什么"的服务端约束**：角色/权限断言、路径级规则、属主（对象级）检查的存在事实。不转录：判据是否可伪造（C-g 判读，转录附判据来源行号即可）；DB 层 grant/RLS（边界外，note 最多）。
格式：`authz:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `authz:none`；属主约束单独前缀 `authz:owner:` 供 C3 差分直读。

## 2. 封闭来源清单（Java 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| 方法/类注解 @PreAuthorize/@RolesAllowed/@Secured（角色/权限形） | `authz:anno:@PreAuthorize("hasRole('ADMIN')")@UserApi.java:44` |
| SecurityConfig 的 antMatchers/requestMatchers 行（含 mvcMatchers/regexMatchers） | `authz:dsl:requestMatchers("/admin/**").hasRole("ADMIN")@SecurityConfig.java:38` |
| 拦截器注册表 addInterceptors + pathPatterns | `authz:registry:RoleInterceptor[/api/admin/**]@WebConfig.java:22` |
| 方法体首行角色断言（if !hasRole throw） | `authz:inline:roleAssert ADMIN@UserApi.java:61` |
| 基类继承（abstract BaseController 带 @PreAuthorize） | `authz:inherit:BaseAdminController@Base.java:15（转录基类行+继承链）` |
| 属主约束进查询（findByIdAndOwnerId/Specification 含 owner） | `authz:owner:findByIdAndOwnerId@Repo.java:19` |
| 取出后比对属主/@PostAuthorize("returnObject.owner==principal") | `authz:owner:postCheck owner!=currentUser@UserApi.java:70（挂 B6 TOCTOU hint）` |

## 3. 转录边界（什么不算 authz）
- 业务校验不算：`if (dto.getStatus() != DRAFT) throw` 是状态机不是主体权限；参数格式校验不算。
- 注释/文档不算；写在被绕过重载上的注解仍转录（B7 变体留给 Analyzer）。
- authn/authz 分段不混：`isAuthenticated()` 只进 authn 段；`hasRole/hasAuthority/#el` 进 authz 段（一个注解可两段各记）。
- 同义框架差异：@Secured/@RolesAllowed/@PreAuthorize(SpEL)/Shiro @RequiresRoles 等价转录，note 记框架。

## 4. 差分判据接口（同 family 不一致）
同 param_shape 路由族（GET /users/{id} 族）12 端点 11 个有 @PreAuthorize 1 个没有（节选 3 条；C3 消费：面状缺失=全 none 系统性默认缺失，点状缺失=个别 none 单点高危，全有则差分为零）：
```
GET /users/{id}      authz:anno:@PreAuthorize("hasRole('ADMIN')")@UserApi.java:40
GET /users/me        authz:none   ← 点状缺失：family 内不一致=+suspicion
GET /users/{id}/log  authz:anno:@PreAuthorize("hasRole('ADMIN')")@UserApi.java:58
```
```
## 5. 绑定有效性核查三跳
1. 注解/配置跳：`grep -rnE '@PreAuthorize|@PostAuthorize|@RolesAllowed|@Secured|hasRole|hasAuthority' --include='*.java' src/`
2. 注册表跳：`grep -rnE '@EnableGlobalMethodSecurity|@EnableMethodSecurity|antMatchers|requestMatchers|addInterceptors|pathPatterns' --include='*.java' src/`
3. 处理逻辑跳：`grep -rnE 'findByIdAnd[A-Z][A-Za-z]*Id|returnObject\.|AccessDeniedHandler|preHandle' --include='*.java' src/`——任一跳空 → 挂 `unbound` hint（如注解在但 @EnableMethodSecurity 缺席=不生效）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```java
@RestController public class OrderApi { @PreAuthorize("hasRole('ADMIN')") @DeleteMapping("/orders/{id}") public void del(@PathVariable Long id){ repo.deleteById(id); }  // L30-31
  @GetMapping("/orders/{id}") public Order get(@PathVariable Long id){ return repo.findByIdAndOwnerId(id, cur()); }
  @PostMapping("/orders") public Order create(@RequestBody Order o){ return repo.save(o); } }  // L38 无 authz
```
DELETE /orders/{id} guards: authn:none; authz:anno:@PreAuthorize("hasRole('ADMIN')")@OrderApi.java:30; csrf:none; upload-check:none; rate-limit:none
GET /orders/{id}    guards: authn:none; authz:owner:findByIdAndOwnerId@OrderApi.java:33; csrf:none; upload-check:none; rate-limit:none
POST /orders        guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none   ← 差分候选
```

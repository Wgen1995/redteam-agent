# guards-authz ｜ lang: python（五段转录规则之一）

> 唯一居所：`langpacks/python/guards-authz.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authz 段 + authz.md §①C3/C4/C-g 机械事实源。
> 类页面对齐：classes/authz.md ②⑤⑥——本文件只转录事实，强弱与 C-g 判读归 Analyzer。

## 1. 段的定义
转录**"当前主体被允许做什么"的服务端约束**：角色装饰器、DRF 权限类、属主检查的存在事实。不转录：判据是否可伪造（C-g 判读，转录附判据来源行）；DB RLS/对象级权限表。
格式：`authz:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `authz:none`；属主约束前缀 `authz:owner:`。

## 2. 封闭来源清单（Python 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Django @permission_required("app.delete_user") | `authz:decorator:@permission_required(delete_user)@views.py:44` |
| DRF permission_classes=[IsAdminUser/DjangoModelPermissions] | `authz:permission:permission_classes[IsAdminUser]@views.py:38` |
| CBV：UserPassesTestMixin / PermissionRequiredMixin | `authz:inherit:PermissionRequiredMixin@views.py:60（转录基类行+继承链）` |
| FastAPI 依赖式角色断言（Depends(require_role("admin"))） | `authz:depends:Depends(require_role(admin))@api.py:40` |
| 路由器级依赖（APIRouter(dependencies=[Depends(require_admin)])） | `authz:depends:router dependencies[admin]@api.py:22` |
| handler 首行角色断言（if not user.is_staff: raise 403） | `authz:inline:roleAssert is_staff@views.py:66` |
| 属主约束进查询（get_queryset 过滤 owner=user）/ 取出后比对 | `authz:owner:queryset filter owner=user@views.py:70` / `authz:owner:postCheck owner@views.py:74（挂 B6 TOCTOU hint）` |

## 3. 转录边界（什么不算 authz）
- 业务校验不算：状态机（`if order.status != 'DRAFT'`）、字段格式、限选集校验不是主体权限。
- 注释/docstring 不算；测试样本不算；Django admin 内建权限仅当路由真暴露才转录。
- authn/authz 分段不混：IsAuthenticated 只进 authn 段；IsAdminUser/DjangoModelPermissions/permission_required 进 authz 段（同 view 可两段各记）。
- 同义框架差异：Django/DRF/FastAPI Depends/Flask 自写装饰器等价转录，note 记框架；`request.headers["X-Role"]` 直读做判据仍转录（C-g 反向证据）。

## 4. 差分判据接口（同 family 不一致）
同 param_shape 路由族（GET /users/{id} 族）12 端点 11 个有权限约束 1 个没有（节选 3 条；C3 消费：面状缺失=全 none 系统性默认缺失，点状缺失=个别 none 单点高危，全有则差分为零）：
```
GET /users/{id}       authz:decorator:@permission_required(view_user)@views.py:30
GET /users/{id}/theme authz:none   ← 点状缺失：family 内不一致=+suspicion
GET /users/{id}/logs  authz:decorator:@permission_required(view_user)@views.py:38
```
## 5. 绑定有效性核查三跳
1. 装饰/声明跳：`grep -rnE 'permission_required|IsAdminUser|DjangoModelPermissions|UserPassesTestMixin|require_role|is_staff|has_perm' --include='*.py' src/`
2. 注册表跳：`grep -rnE 'MIDDLEWARE|AuthenticationMiddleware|APIRouter\(|include_router|urlpatterns|DEFAULT_PERMISSION' --include='*.py' src/`（装饰器生效前提：view 在 urlpatterns/路由表内且认证未 bypass）
3. 处理逻辑跳：`grep -rnE 'get_queryset|filter\(|get_object_or_404|PermissionDenied|403|Http404' --include='*.py' src/`——任一跳空 → `unbound` hint（permission_required 在但全局未启用认证=匿名即"已登录"假象）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```python
class OrderViewSet(viewsets.ModelViewSet):                     # views.py:40
    permission_classes = [IsAdminUser]                          # views.py:41
    def destroy(self, request, pk): ...                         # views.py:42 DELETE
    def retrieve(self, request, pk): return self.queryset.filter(id=pk, owner=request.user)  # views.py:45 属主进查询
    def create(self, request): return self.queryset.create(**request.data)                   # views.py:47 无对象级
```
```
DELETE /orders/{pk} guards: authn:none; authz:permission:permission_classes[IsAdminUser]@views.py:41; csrf:none; upload-check:none; rate-limit:none
GET /orders/{pk}    guards: authn:none; authz:owner:queryset filter{id,owner}@views.py:45; csrf:none; upload-check:none; rate-limit:none
POST /orders        guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none   ← 差分候选
```

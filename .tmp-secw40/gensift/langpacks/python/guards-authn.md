# guards-authn ｜ lang: python（五段转录规则之一）

> 唯一居所：`langpacks/python/guards-authn.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 authn 段转录。
> 类页面对齐：authn 类页未建 → **待类页面对齐**（判据先按"是否要求已认证主体"理解）。

## 1. 段的定义
转录**请求到 handler 前是否要求"已认证身份"**：装饰器、DRF permission_classes、FastAPI Depends、middleware 的认证事实。不转录：认证后端实现（backends.py）、JWT 验签算法；死绑定（middleware 类写了没进 MIDDLEWARE）仍转录并挂 `unbound` hint。
格式：`authn:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `authn:none`。

## 2. 封闭来源清单（Python 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Django @login_required（含 CBV 的 LoginRequiredMixin/method_decorator） | `authn:decorator:@login_required@views.py:28` / `authn:inherit:LoginRequiredMixin@views.py:50（转录基类行+继承链）` |
| DRF permission_classes=[IsAuthenticated] | `authn:permission:permission_classes[IsAuthenticated]@views.py:35` |
| settings 全局 DEFAULT_PERMISSION_CLASSES | `authn:settings:DEFAULT_PERMISSION_CLASSES=IsAuthenticated@settings.py:101` |
| FastAPI 参数级 Depends(get_current_user) | `authn:depends:Depends(get_current_user)@api.py:42` |
| 路由器级依赖（APIRouter(dependencies=[Depends(auth)])） | `authn:depends:router dependencies[auth]@api.py:20` |
| Django middleware 认证断言（自定义 AuthMiddleware） | `authn:middleware:AuthMiddleware@middleware.py:15` |
| 显式放行（AllowAny/dependencies=[] 覆盖） | `authn:permission:AllowAny@views.py:30` |

## 3. 转录边界（什么不算 authn）
- 业务校验不算：`if not request.user_email:` 检查字段不是主体凭证；`@require_http_methods` 是方法限制。
- 注释/docstring 不算；测试文件不算。
- 同义框架差异：Django @login_required/DRF IsAuthenticated/FastAPI Depends/Flask flask-login 装饰器等价转录，note 记框架；`@api_view` 不含认证。
- CBV 的 dispatch 叠加 method_decorator 有效，仍按 decorator 转录；路由器级依赖被 `dependencies=[]` 参数覆盖时转录覆盖事实。

## 4. 差分判据接口（同 family 不一致）
同 router/controller 12 端点 11 个有认证、1 个漏（节选 3 条；面状缺失=全 none 系统性默认缺失，点状缺失=个别 none 单点高危，全有则差分为零）：
```
GET /users/{id}          authn:depends:router dependencies[auth]@api.py:18（路由器级继承）
GET /users/{id}/preview  authn:depends:dependencies=[]@api.py:34（空依赖覆盖=豁免）
POST /users/{id}/export  authn:none   ← 点状缺失：挂在无依赖的 router2 上
```
## 5. 绑定有效性核查三跳
1. 装饰/声明跳：`grep -rnE 'login_required|IsAuthenticated|permission_classes|Depends\(|get_current_user|AllowAny' --include='*.py' src/`
2. 注册表跳：`grep -rnE 'MIDDLEWARE|DEFAULT_AUTHENTICATION|DEFAULT_PERMISSION|APIRouter\(|include_router|add_middleware' --include='*.py' src/`（FastAPI：router 必须 include 进 app；Django：app 在 INSTALLED_APPS 且 view 真被 url 路由）
3. 处理逻辑跳：`grep -rnE 'def get_current_user|HTTPBearer|OAuth2|authenticate|401|Unauthorized|request\.user' --include='*.py' src/`——任一跳空 → `unbound` hint（router 未 include；middleware 不在 MIDDLEWARE）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```python
router = APIRouter(dependencies=[Depends(get_current_user)])          # api.py:10
@router.get("/docs/{doc_id}") def get_doc(doc_id: int): ...  # api.py:12
@router.post("/docs") def create_doc(payload: Doc): ...  # api.py:15 同 router,继承依赖
@app.get("/status") def status(): return {"ok": True}  # app.py:30 裸挂 app,无依赖
```
```
GET /docs/{doc_id} guards: authn:depends:router dependencies[auth]@api.py:10; authz:none; csrf:none; upload-check:none; rate-limit:none
POST /docs         guards: authn:depends:router dependencies[auth]@api.py:10; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /status        guards: authn:none(公开路由,差分候选); authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none
```

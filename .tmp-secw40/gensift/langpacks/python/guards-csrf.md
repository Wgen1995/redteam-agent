# guards-csrf ｜ lang: python（五段转录规则之一）

> 唯一居所：`langpacks/python/guards-csrf.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 csrf 段转录。
> 类页面对齐：classes/csrf.md **不存在** → **待类页面对齐**（判据先按"状态改变请求是否要求跨站凭证"理解）。

## 1. 段的定义
转录**状态改变请求的 CSRF 防护事实**：Django CsrfViewMiddleware/装饰器、SameSite cookie 配置、FastAPI/Flask 手工 token/Origin 校验。不转录：GET 的 CSRF、token 生成细节。
格式：`csrf:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `csrf:none`；纯 bearer 无 cookie 面 `csrf:n-a`（需证据）。

## 2. 封闭来源清单（Python 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| settings MIDDLEWARE 含 CsrfViewMiddleware（缺席=负面缺位事实） | `csrf:middleware:CsrfViewMiddleware@settings.py:106` |
| @csrf_exempt 豁免（负面事实，转录路径） | `csrf:decorator:@csrf_exempt@views.py:80` |
| @ensure_csrf_cookie（回显侧配套）与模板 {% csrf_token %} | `csrf:decorator:@ensure_csrf_cookie@views.py:20` / `csrf:template:{% csrf_token %}@form.html:9` |
| SESSION_COOKIE_SAMESITE / CSRF_COOKIE_SAMESITE | `csrf:samesite:SESSION_COOKIE_SAMESITE=Lax@settings.py:130` |
| DRF SessionAuthentication（触发 CSRF 校验的事实） | `csrf:auth:SessionAuthentication@settings.py:118` |
| FastAPI/Starlette 手工校验（Origin/自定义 token 依赖） | `csrf:depends:verify csrf token@api.py:28` |
| Flask-WTF CSRFProtect | `csrf:mw:CSRFProtect@app.py:14` |

## 3. 转录边界（什么不算 csrf guard）
- JWT 走 Authorization 头不算（无 cookie 面 → `csrf:n-a(bearer)`，需 token 来源证据）。
- 注释不算；`CSRF_COOKIE_SECURE`（仅 https）是传输档不是 SameSite 档——分开转录。
- 同义框架差异：Django CsrfViewMiddleware/Flask-WTF/FastAPI 自写依赖/Sanic 自写等价转录，note 记框架。
- `CSRF_TRUSTED_ORIGINS` 转录（豁免面事实）；DEBUG 下中间件仍在=仍有效，不按 dev 降档。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 端点 11 个被 CSRF 中间件覆盖、1 个 @csrf_exempt（节选 3 条）：
```
POST /pay/confirm  csrf:middleware:CsrfViewMiddleware@settings.py:106
POST /pay/webhook  csrf:decorator:@csrf_exempt@views.py:78   ← 豁免差分（状态改变+豁免=点状缺失）
POST /pay/refund   csrf:middleware:CsrfViewMiddleware@settings.py:106
```
面状缺失（MIDDLEWARE 被移出=全链无防护，suspension 低面积大）与点状缺失（@csrf_exempt 单点）分别成 finding。
## 5. 绑定有效性核查三跳
1. 配置/装饰跳：`grep -rnE 'CsrfViewMiddleware|csrf_exempt|SAMESITE|CSRF_COOKIE|csrf_token|CSRFProtect' --include='*.py' --include='*.html' src/`
2. 注册表跳：`grep -rnE 'MIDDLEWARE|INSTALLED_APPS|SessionAuthentication|CSRF_TRUSTED_ORIGINS' --include='*.py' src/`（中间件生效前提：真在 MIDDLEWARE 列表且顺序在 Session 之后）
3. 处理逻辑跳：`grep -rnE 'check_csrf|_verify_token|Origin|Referer|403|HttpResponseForbidden|CSRF' --include='*.py' src/`——任一跳空 → `unbound` hint（settings 有配置但 MIDDLEWARE 被注释=全局不生效）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```python
MIDDLEWARE = [..., 'django.middleware.csrf.CsrfViewMiddleware', ...]; SESSION_COOKIE_SAMESITE = "Lax"   # settings.py:106,130
@require_POST def pay(request, pid): ...                                  # views.py:30
@csrf_exempt @require_POST def pay_webhook(request): ...                  # views.py:34
def pay_status(request, pid): ...                                         # views.py:38 GET
```
```
POST /pay/{pid}        guards: authn:none; authz:none; csrf:middleware:CsrfViewMiddleware@settings.py:106;csrf:samesite:SESSION_COOKIE_SAMESITE=Lax@settings.py:130; upload-check:none; rate-limit:none
POST /pay/webhook      guards: authn:none; authz:none; csrf:decorator:@csrf_exempt@views.py:34; upload-check:none; rate-limit:none
GET /pay/{pid}/status  guards: authn:none; authz:none; csrf:n-a(GET); upload-check:none; rate-limit:none
```

# ECMAP-PYTHON-DJANGO：Django框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PYTHON-DJANGO |
| name | Django框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | Python + Django Web框架 |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `manage.py` + `settings.py` | Django项目标志性文件 |
| 文件标记 | `urls.py` / `views.py` / `models.py` / `forms.py` | Django MTV结构文件 |
| 依赖标记 | `Django>=4.0` / `django==5.x` in `requirements.txt` | Django依赖声明 |
| 框架标记 | `INSTALLED_APPS` / `MIDDLEWARE` 配置 | Django settings标志性配置 |
| 框架标记 | `models.Model` 子类 / `ForeignKey` 字段 | Django ORM模型定义 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| URL路由 | `path('api/', views.handler)` in `urls.py` | Django URLconf路由注册 |
| include路由 | `path('api/', include('app.urls'))` | 分应用路由包含 |
| 类视图 | `path('x/', MyView.as_view())` | CBV路由注册 |
| 路由参数 | `path('user/<int:uid>/', views.user_detail)` | URL路径参数捕获 |
| DRF路由 | `router.register('users', UserViewSet)` | Django REST Framework路由 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 中间件 | `MIDDLEWARE = [...]` in settings | 安全中间件需显式启用 |
| CSRF中间件 | `django.middleware.csrf.CsrfViewMiddleware` | 默认启用——`@csrf_exempt`会禁用 |
| Security中间件 | `django.middleware.security.SecurityMiddleware` | HSTS/SSL重定向 |
| 装饰器 | `@login_required` / `@permission_required` | Django内置鉴权装饰器 |
| Mixin | `LoginRequiredMixin` / `PermissionRequiredMixin` | CBV鉴权Mixin |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| GET参数 | `request.GET.get('param')` / `request.GET['param']` | 攻击者可控 |
| POST参数 | `request.POST.get('param')` / `request.POST['param']` | 攻击者可控 |
| 请求体 | `request.body` / `json.loads(request.body)` | 攻击者可控 |
| 请求头 | `request.headers['X-...']` / `request.META['HTTP_X_...']` | 攻击者可控 |
| 路径参数 | `def view(request, uid):` 从URL路由捕获 | 攻击者可控 |
| 文件上传 | `request.FILES['file']` | 攻击者可控 |
| Session | `request.session['key']` | 服务端存储但key可被操纵 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| ORM查询 | `Model.objects.filter(col=value)` | 安全（参数化） |
| Raw SQL | `Model.objects.raw("SELECT ... WHERE col = %s", [value])` | 需手动参数化 |
| 直接SQL | `connection.cursor().execute("SELECT ... WHERE col = %s", [value])` | 需手动参数化 |
| 模板渲染 | `render(request, 'template.html', context)` | autoescape默认开启 |
| 重定向 | `redirect(url)` / `HttpResponseRedirect(url)` | 开放重定向风险 |
| 文件操作 | `default_storage.open(path)` | 路径遍历风险 |
| 命令执行 | `subprocess.run(...)` | 命令注入风险（非Django API） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 装饰器鉴权 | `@login_required` | 要求登录 |
| 权限装饰器 | `@permission_required('app.action')` | 基于Django权限系统 |
| 对象级权限 | `django-guardian` / 自定义`has_object_permission` | DRF对象级权限 |
| DRF权限 | `permission_classes = [IsAuthenticated]` | DRF类级权限 |
| Mixin | `LoginRequiredMixin` | CBV登录要求 |
| 认证后端 | `AUTHENTICATION_BACKENDS = [...]` | 自定义认证后端 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 表单验证 | `forms.Form` / `forms.ModelForm` | Django Forms自动验证 |
| 序列化验证 | `serializers.Serializer` (DRF) | DRF序列化验证 |
| 输入校验 | `validators=[MinLengthValidator, RegexValidator]` | 字段级验证器 |
| SQL参数化 | `Model.objects.raw(sql, params)` / `cursor.execute(sql, params)` | 参数化查询 |
| HTML净化 | `bleach.clean()` | 需第三方库（Django无内置富文本净化） |
| 模板转义 | `{{ value }}` autoescape / `{{ value|escape }}` | autoescape默认开启 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | Django模板`{{ value }}` autoescape | 默认自动转义 |
| HTML属性 | Django模板autoescape覆盖属性 | 需确保引号转义 |
| JavaScript | `{{ value|escapejs }}` / `json.dumps` | escapejs过滤器用于JS上下文 |
| URL | `{{ value|urlencode }}` | URL编码过滤器 |
| 标记安全 | `mark_safe()` / `|safe` 过滤器 | **危险**——标记为不需要转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Django ORM | `Model.objects.filter(col=value)` | 参数化默认开启——安全 |
| ORM Q对象 | `Model.objects.filter(Q(col=value))` | 安全 |
| ORM extra | `Model.objects.extra(where=["col = %s"], params=[value])` | 需手动参数化——`extra`已不推荐 |
| Raw SQL | `Model.objects.raw("SELECT ... WHERE col = %s", [value])` | 需手动参数化 |
| cursor.execute | `cursor.execute("SELECT ... WHERE col = %s", (value,))` | 需手动参数化 |
| F表达式 | `Model.objects.update(col=F('col') + 1)` | 安全——避免竞争 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON响应 | `JsonResponse(data)` / DRF `Response` | 安全 |
| JSON解析 | `json.loads(request.body)` | 需try-except处理异常 |
| DRF序列化 | `serializer = MySerializer(data=request.data)` | 自动验证 |
| XML解析 | `lxml.etree` / `xml.etree.ElementTree` | XXE风险——Django无内置XML解析 |
| 模板加载 | `render(request, 'template.html')` | 模板引擎安全（autoescape） |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| Django async views | `async def view(request):` | Django 3.1+支持异步视图 |
| 数据库异步 | `database_sync_to_async` / `adjango` | 异步数据库操作需包装 |
| Celery | `@shared_task` / `celery.delay()` | 异步任务队列 |
| 信号 | `@receiver(post_save)` | 信号处理需注意竞态 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 动态模型 | `type('DynamicModel', (models.Model,), attrs)` | 动态模型创建需注意 |
| 动态导入 | `importlib.import_module(app_name)` | INSTALLED_APPS动态加载 |
| DRF路由自动 | `DefaultRouter` 自动注册ViewSet | 自动路由生成 |
| 迁移代码 | `makemigrations` / `migrate` | 自动生成迁移脚本 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | `python manage.py collectstatic` | 静态文件收集 |
| 包管理 | `pip` + `requirements.txt` | 依赖安全 |
| 测试框架 | `django.test.TestCase` / `pytest-django` | Django测试客户端 |
| 安全检查 | `python manage.py check --deploy` | Django部署安全检查 |
| 依赖扫描 | `pip-audit` / `safety` | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 模板自动转义 | 开启 | Django模板autoescape默认True |
| CSRF防护 | 开启 | `CsrfViewMiddleware`默认启用 |
| HTTPS | 需配置 | `SECURE_SSL_REDIRECT`需手动设置 |
| Clickjacking防护 | 开启 | `XFrameOptionsMiddleware`默认启用 |
| 密码哈希 | 安全 | Django默认用PBKDF2（可配置argon2） |
| 调试模式 | 默认关闭（生产） | `DEBUG=False`必须设置 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Django 4.2 LTS | 默认PBKDF2迭代提升 | 密码存储更安全 |
| Django 5.0 | `DEFAULT_HASHING_ALGORITHM`废弃 | 密码哈希算法迁移 |
| Django 3.1+ | 异步视图支持 | 异步并发安全需注意 |
| Django 4.0+ | `SECRET_KEY`生成更安全 | 密钥管理改进 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF防护——`@csrf_exempt`禁用CSRF |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——`mark_safe()`或`|safe`绕过autoescape |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权检查缺失——View无`@login_required` |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——`extra()`或`raw()`拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——`redirect(request.GET['next'])` |
| vuln-patterns | VULN-STATE-EXTCONTROL-01 | Mass assignment——DRF序列化器含is_admin字段 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 敏感信息暴露——序列化器含password字段 |
| vuln-patterns | VULN-PROT-CLIENTSIDE-01 | 客户端控制——前端隐藏按钮但API无权限 |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失——无`django-ratelimit` |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-CFLOW-OPENREDIRECT-01 | 开放重定向良性证明 |
| attack-patterns | ATK-STATE-EXTCONTROL-01 | Mass assignment良性探测 |
| attack-patterns | ATK-INFO-EXPOSURE-01 | 敏感字段暴露良性探测 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-XSS-AUTOESCAPE-01 | 恢复autoescape |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加授权检查装饰器 |
| fix-patterns | FIX-CFLOW-OPENREDIRECT-01 | 重定向白名单验证 |
| fix-patterns | FIX-INFO-EXPOSURE-01 | 序列化器排除敏感字段 |

## 正例/负例

**正例**（Django中的安全写法）：
```python
# CSRF防护默认开启，表单含csrf_token
<form method="post">{% csrf_token %} ...

# 授权装饰器
@login_required
def delete_user(request, uid):
    user = get_object_or_404(User, pk=uid)
    user.delete()
    return redirect('user_list')

# ORM参数化（默认安全）
User.objects.filter(username=name).first()

# 重定向白名单
from django.utils.http import is_safe_url
next_url = request.GET.get('next', '/')
if not is_safe_url(next_url, allowed_hosts=settings.ALLOWED_REDIRECT_HOSTS):
    next_url = '/'
return redirect(next_url)

# DRF权限
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

**负例**（Django中的不安全写法）：
```python
# 禁用CSRF
@csrf_exempt
def transfer(request):
    ...

# mark_safe绕过autoescape
{{ user_input|safe }}

# raw SQL拼接
User.objects.raw(f"SELECT * FROM users WHERE name = '{name}'")

# 重定向无验证
return redirect(request.GET.get('next', '/'))

# 无授权检查
def delete_user(request, uid):
    User.objects.get(pk=uid).delete()

# DRF序列化器暴露敏感字段
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # 包含password, is_superuser等
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Django框架
- candidate-discovery：使用Django Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Django安全API/中间件配置提供修复写法

## 官方来源

- 官方文档：https://docs.djangoproject.com/
- 安全指南：https://docs.djangoproject.com/en/stable/topics/security/
- 部署检查：https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- DRF文档：https://www.django-rest-framework.org/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Django框架生态映射 |

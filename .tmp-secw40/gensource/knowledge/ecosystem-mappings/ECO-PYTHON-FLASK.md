# ECMAP-PYTHON-FLASK：Flask框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PYTHON-FLASK |
| name | Flask框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | Python + Flask Web框架 |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `app = Flask(__name__)` | Flask应用初始化标志 |
| 依赖标记 | `Flask>=2.0` / `flask==3.x` in `requirements.txt` | Flask依赖声明 |
| 框架标记 | `@app.route('/...')` 路由装饰器 | Flask路由注册标志 |
| 框架标记 | `from flask import request, render_template, redirect` | Flask导入签名 |
| 扩展标记 | `Flask-SQLAlchemy` / `Flask-Login` / `Flask-WTF` | Flask扩展依赖 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 路由装饰器 | `@app.route('/path', methods=['GET', 'POST'])` | Flask主要路由注册方式 |
| 动态路由 | `@app.route('/user/<int:uid>')` | URL变量捕获 |
| Blueprint | `bp = Blueprint('api', __name__, url_prefix='/api')` | 模块化路由 |
| before_request | `@app.before_request` | 请求前钩子 |
| add_url_rule | `app.add_url_rule('/path', 'name', view_func)` | 编程式路由注册 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| before_request | `@app.before_request` | 请求前处理（鉴权/日志） |
| after_request | `@app.after_request` | 响应后处理（安全头） |
| teardown_request | `@app.teardown_request` | 请求结束清理 |
| 装饰器 | 自定义`@login_required`装饰器 | Flask-Login提供 |
| 错误处理 | `@app.errorhandler(404)` | 错误页面处理 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| GET参数 | `request.args.get('param')` / `request.args['param']` | 攻击者可控 |
| POST参数 | `request.form.get('param')` / `request.form['param']` | 攻击者可控 |
| 请求体 | `request.get_json()` / `request.data` | 攻击者可控 |
| 请求头 | `request.headers.get('X-...')` | 攻击者可控 |
| 路径参数 | `def view(uid):` 从路由`<int:uid>`捕获 | 攻击者可控 |
| Cookie | `request.cookies.get('session')` | 攻击者可控 |
| 文件上传 | `request.files['file']` | 攻击者可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `db.engine.execute()` / `db.session.execute()` | 注入风险（拼接时） |
| 模板渲染 | `render_template('template.html', **context)` | autoescape默认开启（Jinja2） |
| 重定向 | `redirect(url)` | 开放重定向风险 |
| 响应 | `make_response()` / `Response()` | 响应头注入风险 |
| 文件操作 | `send_file()` / `send_from_directory()` | 路径遍历风险 |
| 命令执行 | `os.system()` / `subprocess` | 命令注入风险（非Flask API） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| Flask-Login | `@login_required` | 登录要求装饰器 |
| Flask-Security | `roles_required` / `auth_token_required` | 角色和令牌认证 |
| 自定义装饰器 | `def auth_required(f):` | 手动鉴权装饰器 |
| before_request | `@app.before_request def check_auth():` | 全局鉴权 |
| current_user | `from flask_login import current_user` | 当前用户代理 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 表单验证 | `Flask-WTF` / `WTForms` | 表单验证框架 |
| 输入校验 | `flask-restx` / `flask-pydantic` | 结构化输入验证 |
| SQL参数化 | SQLAlchemy参数化查询 | `db.session.execute(text(sql), params)` |
| HTML净化 | `bleach.clean()` | 需第三方库 |
| 模板转义 | Jinja2 autoescape | `render_template`默认autoescape=True |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | Jinja2 `{{ value }}` autoescape | Flask默认使用Jinja2且autoescape开启 |
| HTML属性 | Jinja2 autoescape | 需确保引号转义 |
| JavaScript | `tojson` 过滤器 / `json.dumps` | `{{ value|tojson }}`用于JS上下文 |
| URL | `urlencode` / `urllib.parse.quote` | URL编码 |
| Markup | `markupsafe.Markup()` / `|safe` | **危险**——标记为安全跳过转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Flask-SQLAlchemy | `User.query.filter_by(name=name).first()` | 参数化默认开启 |
| SQLAlchemy ORM | `db.session.query(User).filter(User.name == name)` | 参数化默认开启 |
| SQLAlchemy Raw | `db.session.execute(text("SELECT ... :p"), {"p": value})` | 需用命名参数 |
| db.engine | `db.engine.execute("SELECT ... WHERE col = %s", value)` | 需手动参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON响应 | `jsonify(data)` / `flask.json.dumps` | 安全 |
| JSON解析 | `request.get_json()` | 需处理解析异常 |
| Marshmallow | `schema.dump(obj)` / `schema.load(data)` | 序列化+验证 |
| pickle | `pickle.loads()` | 不安全——Flask session签名但不加密 |
| 模板加载 | `render_template()` | Jinja2安全（autoescape） |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| WSGI同步 | Flask默认同步模式 | GIL保护但需注意共享状态 |
| async Flask | `async def view():` (Flask 2.0+) | 异步视图需注意竞态 |
| Celery | `@celery.task` | 异步任务队列 |
| threading | `threading.Lock()` | 多线程共享状态需锁 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 动态路由 | `app.add_url_rule()` | 运行时动态路由注册 |
| 动态配置 | `app.config.from_object()` / `from_envvar()` | 配置加载 |
| 插件 | Flask扩展注册 `app.register_blueprint()` | 蓝图注册 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | Flask无独立构建步骤 | 直接运行`flask run` |
| 包管理 | `pip` + `requirements.txt` | 依赖安全 |
| 测试框架 | `pytest` + `Flask test_client` | Flask测试客户端 |
| 部署 | `gunicorn` / `uwsgi` | WSGI服务器安全配置 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 模板自动转义 | 开启 | Flask Jinja2 autoescape默认True for .html |
| CSRF防护 | 需扩展 | 需安装Flask-WTF或手动实现 |
| HTTPS | 需配置 | 无内置HTTPS强制 |
| Session安全 | 签名Cookie | Session内容签名但可读（不加密） |
| 调试模式 | 默认关闭 | `app.debug = True`生产环境禁止 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Flask 2.0+ | 异步视图支持 | 异步并发安全需注意 |
| Flask 2.3+ | `app.before_first_request`废弃 | 启动钩子变更 |
| Flask 3.0+ | 移除旧版API | 迁移需检查兼容性 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF缺失——Flask无内置CSRF防护 |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——`Markup()`或`|safe`绕过autoescape |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权检查缺失——路由无`@login_required` |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——SQLAlchemy text()拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——`redirect(request.args['next'])` |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 敏感信息暴露——debug模式泄露堆栈 |
| vuln-patterns | VULN-EXC-FAILOPEN-01 | fail-open——before_request异常未处理 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-CFLOW-OPENREDIRECT-01 | 开放重定向良性证明 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复（Flask-WTF） |
| fix-patterns | FIX-XSS-AUTOESCAPE-01 | 恢复autoescape |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加授权检查装饰器 |
| fix-patterns | FIX-CFLOW-OPENREDIRECT-01 | 重定向白名单验证 |
| fix-patterns | FIX-EXC-FAILOPEN-01 | fail-open修复 |

## 正例/负例

**正例**（Flask中的安全写法）：
```python
# Flask-WTF CSRF防护
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# 授权装饰器
from flask_login import login_required
@app.route('/admin')
@login_required
def admin_panel():
    ...

# SQLAlchemy参数化
User.query.filter_by(username=name).first()

# 重定向白名单
from urllib.parse import urlparse
next_url = request.args.get('next', '/')
if not urlparse(next_url).netloc:  # 只允许相对URL
    return redirect(next_url)
return redirect('/')
```

**负例**（Flask中的不安全写法）：
```python
# Markup绕过autoescape
from markupsafe import Markup
return Markup(f"<div>{user_input}</div>")

# SQL拼接
db.session.execute(text(f"SELECT * FROM users WHERE name = '{name}'"))

# 重定向无验证
return redirect(request.args.get('next', '/'))

# 无授权检查
@app.route('/admin/delete/<uid>', methods=['POST'])
def delete_user(uid):
    User.query.get(uid).delete()

# debug模式生产环境
app.run(debug=True, host='0.0.0.0')

# session存储敏感信息
session['password'] = user_password
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Flask框架
- candidate-discovery：使用Flask Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Flask安全API/扩展配置提供修复写法

## 官方来源

- 官方文档：https://flask.palletsprojects.com/
- 安全指南：https://flask.palletsprojects.com/en/stable/security/
- Flask-WTF：https://flask-wtf.readthedocs.io/
- Flask-Login：https://flask-login.readthedocs.io/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Flask框架生态映射 |

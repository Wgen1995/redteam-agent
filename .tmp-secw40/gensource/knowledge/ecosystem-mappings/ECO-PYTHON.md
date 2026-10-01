# ECMAP-PYTHON：Python语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PYTHON |
| name | Python语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | Python（CPython运行时，不含Web框架——框架见ECMAP-PYTHON-DJANGO/FLASK/FASTAPI） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `requirements.txt` / `setup.py` / `setup.cfg` / `pyproject.toml` / `Pipfile` / `poetry.lock` | Python项目依赖清单文件 |
| 文件标记 | `.py`源文件 + `__init__.py`包标记 | Python源码和包结构标识 |
| 文件标记 | `tox.ini` / `conftest.py` / `pytest.ini` | Python测试配置 |
| 依赖标记 | `import django` / `from flask import` / `from fastapi import` | 区分具体Web框架（详见对应框架Profile） |
| 框架标记 | `if __name__ == '__main__':` 入口签名 | Python脚本入口惯例 |
| 运行时标记 | `__pycache__/` / `.pyc` 字节码缓存 | Python运行时产物 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 函数入口 | `def handler(request):` + 框架路由装饰器 | 无框架时用WSGI/ASGI原生入口 |
| WSGI应用 | `app = wsgi_app(environ, start_response)` | WSGI规范入口 |
| ASGI应用 | `async def app(scope, receive, send):` | ASGI异步入口 |
| CLI入口 | `argparse.ArgumentParser()` / `sys.argv` | 命令行参数入口 |
| 事件入口 | `signal.signal(SIGTERM, handler)` / `threading.Thread` | 信号/线程入口 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| WSGI中间件 | `class MW: def __call__(self, environ, start_response):` | 手动实现鉴权/CORS/日志中间件 |
| ASGI中间件 | `class MW: async def __call__(self, scope, receive, send):` | 异步中间件需注意await顺序 |
| 装饰器 | `@auth_required` / `@login_required` | 自定义装饰器常用于鉴权 |
| 上下文管理器 | `with contextlib.ExitStack() as stack:` | 资源管理和清理 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 请求参数 | `request.args` / `request.GET` / `request.POST`（框架相关） | 攻击者可控 |
| 请求体 | `request.json()` / `await request.json()` | 攻击者可控 |
| 请求头 | `request.headers['X-...']` | 攻击者可控 |
| 文件上传 | `request.files['file']` / `await request.form()` | 攻击者可控 |
| 环境变量 | `os.environ['VAR']` | 部分可控（取决于部署） |
| 命令行参数 | `sys.argv` / `argparse`结果 | 取决于调用方 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `cursor.execute(sql)` / `session.execute(text(sql))` | SQL注入风险（拼接时） |
| 命令执行 | `os.system()` / `subprocess.call(shell=True)` / `subprocess.Popen(shell=True)` | 命令注入风险 |
| 文件操作 | `open()` / `os.path.join()` / `pathlib.Path()` | 路径遍历风险 |
| 模板渲染 | `render_template()` / `Template().render()` | XSS风险（关闭autoescape时） |
| 代码执行 | `eval()` / `exec()` / `compile()` | 代码注入风险 |
| 反序列化 | `pickle.loads()` / `yaml.load()` / `marshal.loads()` | 反序列化RCE风险 |
| 网络请求 | `requests.get(url)` / `urllib.request.urlopen(url)` | SSRF风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 装饰器鉴权 | `@login_required` / `@requires_auth` | 框架提供或自定义 |
| 基于角色的鉴权 | `@roles_required('admin')` | Flask-Security等扩展 |
| 权限检查 | `if not current_user.has_permission('x'):` | 手动权限检查 |
| 会话管理 | `session['user_id'] = user.id` | signed cookie session |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `pydantic`模型 / `marshmallow` schema / `cerberus` validator | 结构化输入验证 |
| SQL转义 | 参数化查询`cursor.execute(sql, params)` | 优先用参数化，不用手动转义 |
| HTML净化 | `bleach.clean()` / `html.escape()` | bleach用于富文本，html.escape用于简单转义 |
| 路径净化 | `os.path.realpath()` + `startswith()`检查 | 规范化+前缀验证 |
| 命令净化 | `shlex.quote()` | shell引用转义（优先用参数数组） |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | `html.escape()` / Jinja2 autoescape | autoescape默认开启（Jinja2/Django） |
| HTML属性 | `html.escape(quote=True)` | 需转义引号 |
| JavaScript | `json.dumps()` 用于JSON上下文 | 不直接嵌入JS，用JSON数据传递 |
| URL | `urllib.parse.quote()` / `urllib.parse.urlencode()` | URL编码 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| SQLAlchemy ORM | `session.query(Model).filter(Model.col == value)` | 参数化默认开启 |
| SQLAlchemy Raw | `session.execute(text("SELECT ... :param"), {"param": value})` | 需用命名参数 |
| Django ORM | `Model.objects.filter(col=value)` | 参数化默认开启 |
| Django Raw | `Model.objects.raw("SELECT ... WHERE col = %s", [value])` | 需手动参数化 |
| 原生DB-API | `cursor.execute("SELECT ... WHERE col = %s", (value,))` | 需手动参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON序列化 | `json.dumps()` / `json.loads()` | 安全，无代码执行 |
| YAML解析 | `yaml.safe_load()` vs `yaml.load()` | `yaml.load()`可执行任意代码，必须用`safe_load` |
| pickle | `pickle.loads()` / `pickle.dump()` | 不安全反序列化风险——不接受不可信pickle |
| XML解析 | `xml.etree.ElementTree` / `lxml.etree` | XXE风险——需禁用外部实体 |
| CSV解析 | `csv.reader()` / `csv.DictReader()` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| asyncio | `async def` / `await` / `asyncio.gather()` | 竞态条件风险——异步操作间无原子性保证 |
| threading | `threading.Lock()` / `threading.RLock()` | 需try-finally释放锁 |
| multiprocessing | `multiprocessing.Lock()` / `multiprocessing.Queue()` | 进程间共享需注意序列化 |
| concurrent.futures | `ThreadPoolExecutor` / `ProcessPoolExecutor` | 线程/进程池安全 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 动态导入 | `importlib.import_module()` / `__import__()` | 模块名来自外部时需白名单 |
| 属性访问 | `getattr(obj, name)` / `setattr(obj, name, val)` | 属性名来自外部时需白名单 |
| 代码生成 | `compile()` / `exec()` / `eval()` | 代码注入风险——不接受外部输入 |
| 元编程 | `type()` / `metaclass` / `__init_subclass__` | 动态创建类需注意安全 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建工具 | `setuptools` / `poetry` / `flit` / `hatch` | 构建配置安全 |
| 包管理 | `pip` / `poetry` / `pipenv` / `uv` | 依赖安全——需校验来源和完整性 |
| 测试框架 | `pytest` / `unittest` / `tox` | 安全测试集成 |
| Lint工具 | `ruff` / `pylint` / `flake8` / `bandit` | bandit安全专项lint |
| 依赖扫描 | `pip-audit` / `safety` / `dependabot` | SCA扫描已知漏洞 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 模板自动转义 | 开启（Jinja2/Django默认） | `autoescape=True`为默认 |
| HTTPS | 需配置 | 无内置HTTPS强制 |
| CSRF防护 | 框架相关（Django默认开启，Flask需扩展） | 依赖框架配置 |
| pickle安全性 | 不安全（默认） | `pickle.loads`可执行任意代码 |
| yaml安全性 | 不安全（`yaml.load`默认） | 需手动用`yaml.safe_load` |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Python 3.10+ | `hashlib`废弃MD5/SHA1用于安全场景 | 密码存储需用bcrypt/argon2 |
| Python 3.12 | `ssl`模块默认禁用SSLv2/SSLv3 | TLS配置更安全 |
| Python 3.x | `subprocess`推荐`shell=False` | 命令注入防护 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL字符串拼接注入（Python验证案例） |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入（os.system/subprocess shell=True） |
| vuln-patterns | VULN-INJ-CODE-01 | 代码注入（eval/exec） |
| vuln-patterns | VULN-INJ-DESERIAL-01 | 不安全反序列化（pickle.loads） |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF（requests.get可控URL） |
| vuln-patterns | VULN-INJ-RESOURCE-01 | 资源注入（open可控路径） |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历（open + os.path.join） |
| vuln-patterns | VULN-FILE-TEMPFILE-01 | 不安全临时文件（mktemp vs mkstemp） |
| vuln-patterns | VULN-FILE-SEARCHPATH-01 | 不可信搜索路径（subprocess无绝对路径） |
| vuln-patterns | VULN-CRYPTO-WEAKHASH-01 | 弱哈希（hashlib.md5密码存储） |
| vuln-patterns | VULN-CRYPTO-NOENCRYPT-01 | 缺少加密（requests verify=False） |
| vuln-patterns | VULN-CRYPTO-WEAKRNG-01 | 弱随机数（random vs secrets） |
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF缺失 |
| vuln-patterns | VULN-CRYPTO-KEYLIFE-01 | 密钥生命周期（硬编码密钥） |
| vuln-patterns | VULN-XSS-RAWOUTPUT-01 | 原生输出XSS |
| vuln-patterns | VULN-ENC-ENCODING-01 | 输出编码失效 |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权检查缺失 |
| vuln-patterns | VULN-CONC-RACE-01 | TOCTOU竞态条件 |
| vuln-patterns | VULN-CONC-LOCKING-01 | 锁使用不当 |
| vuln-patterns | VULN-EXC-SWALLOWED-01 | 异常吞没（except: pass） |
| vuln-patterns | VULN-EXC-FAILOPEN-01 | fail-open |
| vuln-patterns | VULN-RES-UNCONTROLLED-01 | 资源消耗无限制 |
| vuln-patterns | VULN-RES-RELEASE-01 | 资源释放缺失（未用with） |
| vuln-patterns | VULN-RES-COMPLEXITY-01 | ReDoS（re模块回溯） |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失 |
| vuln-patterns | VULN-INPUT-REGEX-01 | 正则验证错误 |
| vuln-patterns | VULN-INPUT-INVALIDSTRUCT-01 | 无效结构处理（json.loads无try-catch） |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 敏感信息暴露（to_dict含敏感字段） |
| attack-patterns | ATK-SQLI-BENIGN-01 | 良性SQL注入标记证明 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-CODE-01 | 良性代码注入标记证明 |
| attack-patterns | ATK-INJ-DESERIAL-01 | 良性反序列化gadget证明 |
| attack-patterns | ATK-INJ-SSRF-01 | 良性SSRF回调探测 |
| attack-patterns | ATK-FILE-TRAVERSAL-01 | 良性路径遍历读取证明 |
| attack-patterns | ATK-CRYPTO-OFFLINE-COST-01 | 弱哈希离线成本证明 |
| attack-patterns | ATK-CRYPTO-RNGPREDICT-01 | 弱RNG预测证明 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-CONC-RACE-01 | TOCTOU竞态良性证明 |
| attack-patterns | ATK-EXC-SWALLOWED-01 | 异常吞没绕过良性证明 |
| attack-patterns | ATK-RES-COMPLEXITY-01 | ReDoS良性探测 |
| attack-patterns | ATK-RES-FREQUENCY-01 | 速率限制缺失良性证明 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | 参数化查询修复 |
| fix-patterns | FIX-INJ-CMD-01 | 命令注入修复（参数数组） |
| fix-patterns | FIX-INJ-CODE-01 | 代码注入修复 |
| fix-patterns | FIX-INJ-DESERIAL-01 | 反序列化修复（类型白名单） |
| fix-patterns | FIX-INJ-SSRF-01 | SSRF修复（URL白名单） |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | 路径遍历修复（realpath+startswith） |
| fix-patterns | FIX-CRYPTO-STRONGHASH-01 | 强哈希修复（bcrypt/argon2） |
| fix-patterns | FIX-CRYPTO-ENFORCEENC-01 | 强制加密修复 |
| fix-patterns | FIX-CRYPTO-CSPRNG-01 | CSPRNG修复（secrets模块） |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-CONC-RACE-01 | 竞态条件修复（原子操作） |
| fix-patterns | FIX-CONC-LOCKING-01 | 锁使用修复（try-finally/with） |
| fix-patterns | FIX-RES-CONSUMPTION-LIMIT-01 | 资源消耗限制修复 |
| fix-patterns | FIX-RES-RELEASE-01 | 资源释放修复（with语句） |

## 正例/负例

**正例**（该生态中的安全写法）：
```python
# 参数化查询
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# 命令执行用参数数组
subprocess.run(["ls", "-la", user_dir], shell=False, check=True)

# 路径遍历防护
import os
base = os.path.realpath('/data/')
filepath = os.path.realpath(os.path.join(base, filename))
if not filepath.startswith(base + os.sep):
    abort(403)

# 密码存储用bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# CSPRNG
import secrets
token = secrets.token_urlsafe(32)

# 资源管理用with
with open(filepath) as f:
    data = f.read()
```

**负例**（该生态中的不安全写法）：
```python
# SQL拼接
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# 命令注入
os.system(f"ls {user_dir}")

# 路径遍历
open('/data/' + filename)

# 弱哈希
import hashlib
hashed = hashlib.md5(password).hexdigest()

# 弱随机数
import random
token = str(random.randint(0, 999999))

# 异常吞没
try:
    check_auth()
except:
    pass

# 不安全反序列化
import pickle
data = pickle.loads(request_data)

# yaml.load而非safe_load
import yaml
config = yaml.load(user_yaml)  # 应该用 yaml.safe_load
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Python技术栈，按生态过滤适用知识
- candidate-discovery：使用Source API/Sink API/Guard等映射辅助模式驱动发现
- remediation-guidance：使用安全API/Encoder等映射提供框架特定修复写法

## 官方来源

- 官方文档：https://docs.python.org/3/
- 安全指南：https://docs.python.org/3/tutorial/stdlib2.html#security
- bandit安全lint：https://bandit.readthedocs.io/
- pip-audit：https://github.com/pypa/pip-audit

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Python语言生态映射 |

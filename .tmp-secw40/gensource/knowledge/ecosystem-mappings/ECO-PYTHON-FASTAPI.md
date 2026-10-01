# ECMAP-PYTHON-FASTAPI：FastAPI框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PYTHON-FASTAPI |
| name | FastAPI框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | Python + FastAPI Web框架（ASGI/Starlette） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `app = FastAPI()` | FastAPI应用初始化标志 |
| 依赖标记 | `fastapi` / `uvicorn` / `starlette` in `requirements.txt` | FastAPI依赖声明 |
| 框架标记 | `@app.get('/...')` / `@app.post('/...')` 方法路由 | FastAPI方法路由装饰器 |
| 框架标记 | `from fastapi import FastAPI, Request, HTTPException` | FastAPI导入签名 |
| 类型标记 | `from pydantic import BaseModel` | Pydantic模型验证标志 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 方法路由 | `@app.get('/path')` / `@app.post('/path')` | HTTP方法路由装饰器 |
| 路径参数 | `@app.get('/user/{uid}')` + `def view(uid: int):` | 类型化路径参数 |
| APIRouter | `router = APIRouter()` / `app.include_router(router)` | 模块化路由 |
| WebSocket | `@app.websocket('/ws')` | WebSocket端点 |
| 依赖注入 | `Depends(get_db)` / `Depends(get_current_user)` | 依赖注入参数 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 中间件 | `@app.middleware('http')` | HTTP中间件 |
| Starlette中间件 | `app.add_middleware(TrustedHostMiddleware)` | Starlette安全中间件 |
| 依赖注入 | `Depends(check_permissions)` | 依赖注入作为拦截器 |
| 异常处理 | `@app.exception_handler(ValueError)` | 全局异常处理 |
| CORS | `app.add_middleware(CORSMiddleware, ...)` | CORS配置 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `def view(param: str = Query(...)):` | 攻击者可控 |
| 路径参数 | `def view(uid: int):` | 攻击者可控 |
| 请求体 | `def view(data: Model = Body(...)):` | 攻击者可控（经Pydantic验证） |
| 请求头 | `def view(token: str = Header(...)):` | 攻击者可控 |
| Cookie | `def view(session: str = Cookie(...)):` | 攻击者可控 |
| 表单 | `def view(file: UploadFile = File(...)):` | 攻击者可控 |
| Request对象 | `async def view(request: Request):` | 原始请求访问 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `db.execute(text(sql))` / SQLAlchemy session | 注入风险（拼接时） |
| 模板 | `Jinja2Templates().TemplateResponse()` | XSS风险（需autoescape） |
| 重定向 | `RedirectResponse(url)` | 开放重定向风险 |
| JSON响应 | `JSONResponse(content=data)` | 安全（JSON编码） |
| 文件响应 | `FileResponse(path)` | 路径遍历风险 |
| 命令执行 | `subprocess` / `os.system` | 命令注入风险（非FastAPI API） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 依赖注入鉴权 | `Depends(get_current_user)` | 依赖注入鉴权 |
| OAuth2 | `OAuth2PasswordBearer` / `Security(scopes)` | FastAPI内置OAuth2支持 |
| 权限范围 | `Security(get_current_user, scopes=['admin'])` | OAuth2 scope权限 |
| HTTPBearer | `HTTPBearer(auto_error=True)` | Bearer token认证 |
| 自定义依赖 | `def require_role(role): return Depends(...)` | 自定义权限依赖 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| Pydantic验证 | `class Model(BaseModel): field: constr(min_length=1, max_length=100)` | 自动类型+约束验证 |
| Pydantic验证器 | `@validator('field')` / `@field_validator('field')` | 自定义字段验证器 |
| SQL参数化 | SQLAlchemy `text()` + 参数 | 参数化查询 |
| 文件类型检查 | `UploadFile.content_type` | 文件MIME类型检查 |
| 输入约束 | `Path(...)`, `Query(...)` 约束参数 | 路径/查询参数约束 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| JSON | `JSONResponse` / Pydantic `model_dump()` | JSON自动编码 |
| HTML | `Jinja2Templates` autoescape | 需确保autoescape=True |
| URL | `urllib.parse.quote()` | URL编码 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| SQLAlchemy ORM | `db.query(Model).filter(Model.col == value)` | 参数化默认开启 |
| SQLAlchemy 2.0 | `db.execute(select(Model).where(Model.col == value))` | 参数化默认开启 |
| Raw SQL | `db.execute(text("SELECT ... :p"), {"p": value})` | 需用命名参数 |
| 异步ORM | `async_session.execute(select(Model))` | 异步数据库操作 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| Pydantic序列化 | `model.model_dump()` / `model.model_dump_json()` | 安全 |
| Pydantic反序列化 | `Model.model_validate(data)` / `Model(**data)` | 自动验证 |
| JSON解析 | `json.loads()` | 需try-except |
| pickle | `pickle.loads()` | 不安全反序列化 |
| XML解析 | `lxml.etree` | XXE风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| asyncio原生 | `async def` / `await` | FastAPI原生异步 |
| 异步数据库 | `async def get_db()` / `AsyncSession` | 异步数据库需注意连接池 |
| 后台任务 | `BackgroundTasks` / `asyncio.create_task()` | 后台任务安全 |
| 并发控制 | `asyncio.Semaphore` / `anyio` | 并发限制 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 依赖注入 | `Depends()` / `yield`依赖 | FastAPI核心DI机制 |
| 自动文档 | OpenAPI/Swagger自动生成 | 文档可能泄露API结构 |
| 动态路由 | `APIRouter` 运行时注册 | 动态路由注册 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 运行 | `uvicorn app:app` | ASGI服务器 |
| 测试框架 | `httpx` + `pytest` / `TestClient` | FastAPI测试客户端 |
| OpenAPI | 自动生成 `/docs` / `/openapi.json` | 生产环境需禁用文档端点 |
| 依赖扫描 | `pip-audit` | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 输入验证 | 开启 | Pydantic类型验证默认 |
| 模板自动转义 | 需配置 | Jinja2Templates需设置autoescape |
| CSRF防护 | 需扩展 | FastAPI无内置CSRF防护 |
| HTTPS | 需配置 | 无内置HTTPS强制 |
| OpenAPI文档 | 默认开启 | 生产环境需`docs_url=None`禁用 |
| CORS | 需配置 | 需显式添加CORSMiddleware |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| FastAPI 0.100+ | Pydantic v2迁移 | 验证逻辑迁移 |
| FastAPI 0.95+ | lifespan替代startup/shutdown | 生命周期管理变更 |
| Starlette 0.30+ | 安全中间件更新 | 中间件行为变化 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF缺失——FastAPI无内置CSRF |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权检查缺失——路由无`Depends(get_current_user)` |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——SQLAlchemy text()拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——RedirectResponse可控URL |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——OpenAPI文档暴露API结构 |
| vuln-patterns | VULN-PROT-CLIENTSIDE-01 | 客户端控制——前端验证但API无验证 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-CFLOW-OPENREDIRECT-01 | 开放重定向良性证明 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加DI授权检查 |
| fix-patterns | FIX-CFLOW-OPENREDIRECT-01 | 重定向白名单验证 |

## 正例/负例

**正例**（FastAPI中的安全写法）：
```python
# 依赖注入鉴权
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(401)
    return user

@app.delete('/users/{uid}')
async def delete_user(uid: int, user: User = Depends(get_current_user)):
    if not user.has_permission('delete'):
        raise HTTPException(403)
    ...

# Pydantic输入验证
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr

@app.post('/users')
async def create_user(data: UserCreate):
    ...

# SQLAlchemy参数化
result = await db.execute(select(User).where(User.name == name))
```

**负例**（FastAPI中的不安全写法）：
```python
# 无授权检查
@app.delete('/users/{uid}')
async def delete_user(uid: int):
    ...

# SQL拼接
result = await db.execute(text(f"SELECT * FROM users WHERE name = '{name}'"))

# 重定向无验证
@app.get('/redirect')
async def redirect(url: str = Query(...)):
    return RedirectResponse(url)

# OpenAPI文档生产环境暴露
app = FastAPI()  # 默认暴露 /docs

# 无CORS限制
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True)
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用FastAPI框架
- candidate-discovery：使用FastAPI Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用FastAPI安全API/依赖注入配置提供修复写法

## 官方来源

- 官方文档：https://fastapi.tiangolo.com/
- 安全指南：https://fastapi.tiangolo.com/tutorial/security/
- Starlette：https://www.starlette.io/
- Pydantic：https://docs.pydantic.dev/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——FastAPI框架生态映射 |

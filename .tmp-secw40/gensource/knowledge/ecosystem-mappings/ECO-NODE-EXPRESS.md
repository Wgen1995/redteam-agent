# ECMAP-NODE-EXPRESS：Express框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-NODE-EXPRESS |
| name | Express框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | JavaScript/TypeScript + Express Web框架（Node.js） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 依赖标记 | `"express"` in `package.json` dependencies | Express依赖声明 |
| 文件标记 | `const express = require('express')` / `import express from 'express'` | Express导入标志 |
| 框架标记 | `const app = express()` | Express应用初始化 |
| 框架标记 | `app.listen(port, ...)` | Express服务器启动 |
| 中间件标记 | `app.use(bodyParser.json())` / `app.use(express.json())` | Express中间件注册 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 路由方法 | `app.get('/path', handler)` / `app.post('/path', handler)` | HTTP方法路由 |
| all路由 | `app.all('/path', handler)` | 所有方法路由 |
| Router | `const router = express.Router(); router.get(...)` | 模块化路由 |
| 路径参数 | `app.get('/user/:id', (req, res) => { req.params.id })` | URL路径参数 |
| 中间件挂载 | `app.use('/api', router)` | 路径前缀挂载 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 应用级中间件 | `app.use(middleware)` | 全局中间件 |
| 路由级中间件 | `router.use(middleware)` | 路由级中间件 |
| 错误处理 | `(err, req, res, next) => { ... }` | 错误处理中间件（4参数） |
| body-parser | `express.json()` / `express.urlencoded()` | 请求体解析 |
| helmet | `app.use(helmet())` | 安全HTTP头中间件 |
| cors | `app.use(cors(options))` | CORS配置 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `req.query.param` / `req.query['param']` | 攻击者可控 |
| 路径参数 | `req.params.id` | 攻击者可控 |
| 请求体 | `req.body`（需body-parser） | 攻击者可控 |
| 请求头 | `req.headers['x-...']` / `req.get('X-...')` | 攻击者可控 |
| Cookie | `req.cookies.name`（需cookie-parser） | 攻击者可控 |
| 文件上传 | `req.files`（需multer） | 攻击者可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `db.query(sql)` / `sequelize.query()` | 注入风险（拼接时） |
| 响应发送 | `res.send(data)` / `res.json(data)` | XSS风险（res.send HTML时） |
| 模板渲染 | `res.render('template', data)` | XSS风险（需autoescape） |
| 重定向 | `res.redirect(url)` | 开放重定向风险 |
| 文件响应 | `res.sendFile(path)` | 路径遍历风险 |
| 文件操作 | `fs.readFile()` / `fs.writeFile()` | 路径遍历风险 |
| 命令执行 | `child_process.exec()` | 命令注入风险（非Express API） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 鉴权中间件 | `function authMiddleware(req, res, next) { ... }` | 自定义鉴权中间件 |
| express-jwt | `expressjwt({ secret, algorithms: ['HS256'] })` | JWT验证中间件 |
| Passport | `passport.authenticate('jwt', { session: false })` | Passport认证 |
| express-session | `express-session({ secret, ... })` | 会话管理 |
| 角色检查 | `function requireRole(role) { return (req, res, next) => { ... } }` | 角色检查中间件 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `express-validator` / `joi` / `zod` | 请求验证中间件 |
| SQL参数化 | 驱动参数化查询 `db.query(sql, [params])` | 参数化查询 |
| HTML净化 | `DOMPurify` / `sanitize-html` / `xss` | HTML净化 |
| 路径净化 | `path.resolve()` + `path.relative()`检查 | 路径规范化 |
| CORS | `cors({ origin: allowedOrigins })` | CORS白名单 |
| helmet | `helmet()` | 安全HTTP头 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| JSON | `res.json(data)` | JSON自动编码 |
| HTML | `res.render()` 模板引擎autoescape | 需确保autoescape开启 |
| URL | `encodeURIComponent()` | URL编码 |
| 不转义 | `res.send(rawHtml)` | **危险**——直接发送HTML |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Sequelize | `Model.findAll({ where: { col: value } })` | 参数化默认开启 |
| TypeORM | `repository.find({ where: { col: value } })` | 参数化默认开启 |
| Prisma | `prisma.model.findMany({ where: { col: value } })` | 参数化默认开启 |
| Knex | `knex('table').where('col', value)` | 参数化默认开启 |
| Raw SQL | `db.query('SELECT ... WHERE col = ?', [value])` | 需手动参数化 |
| Sequelize raw | `sequelize.query('SELECT ...', { replacements: [value] })` | 需命名/位置参数 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `JSON.parse()` / `res.json()` | 安全 |
| body-parser | `express.json({ limit: '1mb' })` | 需限制大小 |
| cookie-parser | `cookieParser(secret)` | 签名Cookie |
| express-session | `session({ secret, cookie: { secure: true } })` | 会话存储 |
| multer | `multer({ limits: { fileSize: 5 * 1024 * 1024 } })` | 文件上传限制 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| async/await | `async (req, res) => { ... }` | 异步路由需try-catch |
| Promise | `handler(req, res).catch(next)` | 需错误传播到next |
| 事件循环 | 单线程 | 异步I/O竞态风险 |
| 锁 | `async-mutex` | 需第三方锁库 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 动态路由 | `app[method](path, handler)` | 动态方法路由 |
| 中间件组合 | `app.use(mw1, mw2, mw3)` | 中间件链 |
| req对象扩展 | `req.user = user` | 请求上下文扩展 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 包管理 | `npm` / `yarn` / `pnpm` | `npm audit` |
| 测试框架 | `supertest` + `jest` / `mocha` | Express测试 |
| 部署 | `pm2` / Docker | 进程管理 |
| 安全中间件 | `helmet` / `cors` / `express-rate-limit` | 安全中间件集成 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 安全HTTP头 | 需helmet | Express默认不设安全头 |
| CSRF防护 | 需csurf（已废弃）或自定义 | 无内置CSRF防护 |
| HTTPS | 需配置 | 无内置HTTPS强制 |
| CORS | 需配置 | 默认不允许跨域 |
| 请求体大小 | 需限制 | `express.json({ limit })`需手动设置 |
| 错误信息 | 需配置 | 生产环境需隐藏错误堆栈 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Express 4.x | 稳定版本 | 当前主流 |
| Express 5.x | 路由匹配改进 | 路径参数安全改进 |
| body-parser | 内置到express | `express.json()`替代`body-parser` |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF缺失——无csurf |
| vuln-patterns | VULN-XSS-RAWOUTPUT-01 | XSS——res.send(rawHtml) |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无鉴权中间件 |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——db.query拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——res.redirect(req.query.next) |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——错误堆栈暴露 |
| vuln-patterns | VULN-PROT-CLIENTSIDE-01 | 客户端控制——前端验证但API无 |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失——无express-rate-limit |
| vuln-patterns | VULN-RES-UNCONTROLLED-01 | 资源消耗——无body大小限制 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-CFLOW-OPENREDIRECT-01 | 开放重定向良性证明 |
| attack-patterns | ATK-RES-FREQUENCY-01 | 速率限制缺失良性证明 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-XSS-OUTPUT-ENCODING-01 | 输出编码修复 |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加鉴权中间件 |
| fix-patterns | FIX-CFLOW-OPENREDIRECT-01 | 重定向白名单 |
| fix-patterns | FIX-RES-FREQUENCY-01 | 添加速率限制 |
| fix-patterns | FIX-RES-CONSUMPTION-LIMIT-01 | body大小限制 |

## 正例/负例

**正例**（Express中的安全写法）：
```javascript
// 安全中间件
app.use(helmet());
app.use(cors({ origin: ['https://example.com'] }));
app.use(express.json({ limit: '1mb' }));

// 鉴权中间件
function authRequired(req, res, next) {
    const token = req.headers.authorization;
    if (!verifyToken(token)) return res.status(401).json({ error: 'Unauthorized' });
    req.user = decodeToken(token);
    next();
}

// 参数化查询
db.query('SELECT * FROM users WHERE id = ?', [req.params.id]);

// 重定向白名单
const allowedRedirects = ['/dashboard', '/profile'];
const next = req.query.next || '/dashboard';
if (!allowedRedirects.includes(next)) return res.redirect('/dashboard');
res.redirect(next);

// 速率限制
const rateLimit = require('express-rate-limit');
app.use('/api', rateLimit({ windowMs: 60000, max: 100 }));
```

**负例**（Express中的不安全写法）：
```javascript
// 无安全头
// (缺少 app.use(helmet()))

// 无鉴权
app.delete('/users/:id', (req, res) => {
    db.query(`DELETE FROM users WHERE id = ${req.params.id}`);
});

// SQL拼接
db.query(`SELECT * FROM users WHERE name = '${req.body.name}'`);

// 重定向无验证
app.get('/redirect', (req, res) => res.redirect(req.query.url));

// 错误堆栈暴露
app.use((err, req, res, next) => {
    res.status(500).send(err.stack);  // 暴露堆栈
});

// 无body大小限制
app.use(express.json());  // 默认100kb但可配置更大
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Express框架
- candidate-discovery：使用Express Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Express安全中间件/API提供修复写法

## 官方来源

- 官方文档：https://expressjs.com/
- 安全最佳实践：https://expressjs.com/en/advanced/best-practice-security.html
- helmet：https://helmetjs.github.io/
- express-validator：https://express-validator.github.io/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Express框架生态映射 |

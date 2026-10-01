# ECMAP-JAVASCRIPT：JavaScript/TypeScript语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-JAVASCRIPT |
| name | JavaScript/TypeScript语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | JavaScript / TypeScript（Node.js运行时，不含Express——Express见ECMAP-NODE-EXPRESS） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `package.json` / `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` | Node.js项目标识 |
| 文件标记 | `.js` / `.mjs` / `.cjs` / `.ts` / `.tsx` 源文件 | JS/TS源码标识 |
| 文件标记 | `tsconfig.json` | TypeScript配置 |
| 文件标记 | `.eslintrc` / `eslint.config.js` | ESLint配置 |
| 框架标记 | `import express from 'express'` / `require('express')` | 区分具体框架（详见Express Profile） |
| 运行时标记 | `node_modules/` 目录 | Node.js依赖目录 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| HTTP服务器 | `http.createServer((req, res) => {...})` | 原生HTTP服务器 |
| 事件监听 | `EventEmitter.on('event', handler)` | 事件驱动入口 |
| 模块导出 | `module.exports = handler` / `export default handler` | 模块入口 |
| CLI | `process.argv` / `commander` / `yargs` | 命令行入口 |
| Worker | `new Worker('worker.js')` | Worker线程入口 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 中间件函数 | `(req, res, next) => { ... next(); }` | Express/Koa中间件模式 |
| 事件中间件 | `EventEmitter`拦截 | 事件处理链 |
| 全局错误处理 | `process.on('uncaughtException')` | 全局异常处理 |
| Worker消息 | `worker.on('message')` | Worker消息处理 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| URL参数 | `url.parse(req.url, true).query` / `new URLSearchParams()` | 攻击者可控 |
| 请求头 | `req.headers['x-...']` | 攻击者可控 |
| 请求体 | `req.body`（需body-parser） / `Buffer.concat(chunks)` | 攻击者可控 |
| Cookie | `req.headers.cookie` / `cookie-parser` | 攻击者可控 |
| 环境变量 | `process.env['VAR']` | 部分可控 |
| 命令行 | `process.argv` | 取决于调用方 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `db.query(sql)` / `sequelize.query()` | 注入风险（拼接时） |
| 命令执行 | `child_process.exec()` / `execSync()` | 命令注入风险 |
| 文件操作 | `fs.readFile()` / `fs.writeFile()` / `path.join()` | 路径遍历风险 |
| 代码执行 | `eval()` / `Function()` / `vm.runInContext()` | 代码注入风险 |
| 模板渲染 | `ejs.render()` / `pug.render()` | XSS风险（需转义） |
| 反序列化 | `node-serialize` / `js-yaml.load()` | 反序列化RCE风险 |
| 网络请求 | `http.get()` / `fetch()` / `axios.get()` | SSRF风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 中间件鉴权 | `function authMiddleware(req, res, next)` | 自定义鉴权中间件 |
| JWT验证 | `jsonwebtoken.verify()` | JWT令牌验证 |
| Passport | `passport.authenticate('strategy')` | Passport认证策略 |
| express-jwt | `express-jwt({ secret, algorithms })` | JWT中间件 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `joi` / `zod` / `ajv` / `validator` | 结构化输入验证 |
| SQL参数化 | 驱动参数化查询 `db.query(sql, [params])` | 参数化查询 |
| HTML净化 | `DOMPurify` / `sanitize-html` / `xss` | HTML净化库 |
| 路径净化 | `path.resolve()` + `path.relative()`检查 | 路径规范化 |
| 命令净化 | `execFile()` 替代 `exec()`（参数数组） | 参数数组替代shell |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | `he.encode()` / 模板引擎autoescape | HTML实体编码 |
| HTML属性 | `he.encode()` with 属性上下文 | 属性编码 |
| JavaScript | `JSON.stringify()` / 模板引擎转义 | JSON数据传递 |
| URL | `encodeURIComponent()` / `querystring.escape()` | URL编码 |
| Base64 | `Buffer.from(str).toString('base64')` | Base64编码 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Sequelize | `Model.findAll({ where: { col: value } })` | 参数化默认开启 |
| TypeORM | `repository.find({ where: { col: value } })` | 参数化默认开启 |
| Prisma | `prisma.model.findMany({ where: { col: value } })` | 参数化默认开启 |
| Knex | `knex('table').where('col', value)` | 参数化默认开启 |
| Raw SQL | `db.query('SELECT ... WHERE col = ?', [value])` | 需手动参数化 |
| Sequelize raw | `sequelize.query('SELECT ... WHERE col = :val', { replacements: { val: value } })` | 需命名参数 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `JSON.parse()` / `JSON.stringify()` | 安全（无代码执行） |
| node-serialize | `serialize.unserialize()` | **不安全**——RCE风险 |
| js-yaml | `yaml.load()` vs `yaml.safeLoad()` | `safeLoad`已废弃，现在`load`默认安全但需注意schema |
| XML | `fast-xml-parser` / `libxmljs` | XXE风险——需禁用外部实体 |
| CSV | `csv-parser` / `papaparse` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| Promise | `Promise.resolve()` / `async/await` | 异步操作间无原子性保证 |
| 事件循环 | 单线程事件循环 | 单线程但异步I/O需注意竞态 |
| Worker | `worker_threads` | 多线程共享需注意 |
| Cluster | `cluster.fork()` | 多进程模式 |
| 锁 | `async-mutex` / `Mutex` | 需第三方锁库 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 动态属性 | `obj[name]` / `Reflect.get()` | 属性名来自外部需白名单——原型链污染风险 |
| 原型链 | `Object.prototype` / `__proto__` | 原型链污染——`Object.create(null)`或`Map`更安全 |
| require | `require(moduleName)` / `import()` | 动态导入模块名来自外部需白名单 |
| eval | `eval()` / `new Function()` | 代码注入风险 |
| vm | `vm.runInNewContext()` | 沙箱执行——但非真正隔离 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 包管理 | `npm` / `yarn` / `pnpm` | 依赖安全——`npm audit` |
| 构建 | `webpack` / `esbuild` / `vite` / `tsc` | 构建配置 |
| 测试框架 | `jest` / `mocha` / `vitest` | 测试集成 |
| Lint工具 | `eslint` / `typescript-eslint` / `biome` | 代码质量 |
| 安全lint | `eslint-plugin-security` | 安全专项lint |
| 依赖扫描 | `npm audit` / `snyk` / `dependabot` | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 模板转义 | 需配置 | 取决于模板引擎配置 |
| 原型链保护 | 不安全 | `__proto__`可被污染——需手动防护 |
| 类型安全 | TypeScript提供 | 编译时类型检查（运行时仍动态） |
| eval安全性 | 不安全 | `eval`可执行任意代码 |
| 严格模式 | 需启用 | `'use strict'`需手动声明 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Node.js 18+ | `fetch` API内置 | HTTP客户端 |
| Node.js 16+ | `--experimental-permission` | 权限模型 |
| Node.js 20+ | 权限模型稳定化 | 文件系统/子进程权限控制 |
| ES2022+ | `Object.hasOwn()` | 替代`hasOwnProperty`更安全 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——db.query拼接 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——child_process.exec拼接 |
| vuln-patterns | VULN-INJ-CODE-01 | 代码注入——eval/Function |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF——axios/fetch可控URL |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——fs.readFile + path.join |
| vuln-patterns | VULN-XSS-RAWOUTPUT-01 | 原生输出XSS——res.send可控值 |
| vuln-patterns | VULN-ENC-ENCODING-01 | 输出编码失效 |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无鉴权中间件 |
| vuln-patterns | VULN-CONC-RACE-01 | 竞态条件——异步操作间无原子性 |
| vuln-patterns | VULN-EXC-SWALLOWED-01 | 异常吞没——空catch块 |
| vuln-patterns | VULN-RES-COMPLEXITY-01 | ReDoS——RegExp回溯 |
| vuln-patterns | VULN-RES-UNCONTROLLED-01 | 资源消耗——无限制 |
| vuln-patterns | VULN-INPUT-REGEX-01 | 正则验证错误 |
| vuln-patterns | VULN-INPUT-HANDLING-01 | 输入处理不当——undefined/null |
| attack-patterns | ATK-SQLI-BENIGN-01 | 良性SQL注入标记证明 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-CODE-01 | 良性代码注入标记证明 |
| attack-patterns | ATK-FILE-TRAVERSAL-01 | 良性路径遍历读取证明 |
| attack-patterns | ATK-RES-COMPLEXITY-01 | ReDoS良性探测 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | 参数化查询 |
| fix-patterns | FIX-INJ-CMD-01 | execFile替代exec |
| fix-patterns | FIX-INJ-CODE-01 | 禁用eval/Function |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | path.resolve+relative检查 |
| fix-patterns | FIX-RES-COMPLEXITY-01 | 正则回溯限制 |

## 正例/负例

**正例**（JavaScript中的安全写法）：
```javascript
// 参数化查询
db.query('SELECT * FROM users WHERE id = ?', [userId]);

// execFile替代exec
const { execFile } = require('child_process');
execFile('ls', ['-la', userDir]);

// 路径遍历防护
const path = require('path');
const filepath = path.resolve(baseDir, filename);
if (!filepath.startsWith(path.resolve(baseDir))) {
    return res.status(403).send('Forbidden');
}

// 输入验证
const schema = zod.object({
    username: zod.string().min(3).max(50).regex(/^[a-zA-Z0-9_]+$/)
});
const parsed = schema.parse(req.body);

// HTML编码
const he = require('he');
res.send(he.encode(userInput));
```

**负例**（JavaScript中的不安全写法）：
```javascript
// SQL拼接
db.query(`SELECT * FROM users WHERE name = '${name}'`);

// 命令注入
const { exec } = require('child_process');
exec(`ls ${userDir}`);

// eval
eval(userInput);

// 路径遍历
fs.readFile(baseDir + '/' + filename);

// 原型链污染
Object.assign(obj, userInput);  // userInput含__proto__

// 空catch
try { checkAuth(); } catch (e) {}

// ReDoS
const regex = /(a+)+b/;  // 回溯风险
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用JavaScript/TypeScript技术栈
- candidate-discovery：使用JS Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用JS安全API/Encoder映射提供修复写法

## 官方来源

- Node.js文档：https://nodejs.org/docs/
- TypeScript文档：https://www.typescriptlang.org/
- eslint-plugin-security：https://github.com/nodesecurity/eslint-plugin-security
- npm audit：https://docs.npmjs.com/cli/audit

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——JavaScript/TypeScript语言生态映射 |

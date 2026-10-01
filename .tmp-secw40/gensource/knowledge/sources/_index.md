# 数据源类别索引（sources/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务3。本文件是数据源类别索引，按统一格式记录各类数据源。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID |
| name | 名称 |
| ontology_ref | 本体引用（ONT-SOURCE） |
| recognition_signals | 识别信号 |
| applicable_ecosystems | 适用生态 |
| related_semantics | 关联统一漏洞语义（后续任务填充） |
| source_refs | 来源引用 |
| version | 版本 |

## 类别索引表

> 类别内容不以固定条目数封版——下列覆盖已确认的数据源形态，后续可按需扩展。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| SRC-HTTP-REQUEST | HTTP请求 | ONT-SOURCE | `request.json`/`request.form`/`request.query`/`req.body`请求对象属性访问 | Python/aiohttp、Java/Spring、Node.js/Express | | 内部推导 | v0.1 |
| SRC-CREDENTIAL | 身份凭证 | ONT-SOURCE | `request.headers['Authorization']`/`request.cookies`/API key header访问 | 全语言通用 | | 内部推导 | v0.1 |
| SRC-CONFIG-FILE | 配置文件 | ONT-SOURCE | `config.load`/`settings.read`/`yaml.load`配置文件读取 | 全语言通用 | | 内部推导 | v0.1 |
| SRC-ENV-VAR | 环境变量 | ONT-SOURCE | `os.environ`/`os.getenv`/`process.env`环境变量读取 | Python/Java/Node.js/Go | | 内部推导 | v0.1 |
| SRC-DB-READ | 数据库读取 | ONT-SOURCE | `SELECT`查询结果、`findById`/`findOne`ORM读取、`cursor.fetch`数据库读取 | SQLAlchemy/Django ORM/Hibernate/Prisma | | 内部推导 | v0.1 |
| SRC-MESSAGE | 消息队列 | ONT-SOURCE | `message.body`/`msg.value`/`event.payload`消息体内容 | Kafka/RabbitMQ/Redis | | 内部推导 | v0.1 |
| SRC-FILE-CONTENT | 文件内容 | ONT-SOURCE | `file.read()`/`fs.readFile`/`File.ReadAllText`文件内容读取 | 全语言通用 | | 内部推导 | v0.1 |
| SRC-THIRDPARTY-API | 第三方API响应 | ONT-SOURCE | `requests.get().json()`/`fetch().then()`/`http.Get()`外部API调用响应 | 全语言通用 | | 内部推导 | v0.1 |
| SRC-USER-INPUT | 用户输入 | ONT-SOURCE | `input()`/`scanf`/`cin`/UI表单输入获取 | 全语言通用 | | 内部推导 | v0.1 |
| SRC-CODEGEN-INPUT | 代码生成输入 | ONT-SOURCE | prompt字符串、模板输入、AI模型输入构造 | OpenAI API/LangChain/Codegen工具 | | 内部推导 | v0.1 |

## 消费方

- `candidate-discovery`：候选发现能力判断数据源的可控性
- `verification-and-rating`：验证与定级能力评估数据源的可控性（controllable）

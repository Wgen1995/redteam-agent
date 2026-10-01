# ONT-SOURCE：数据源

## 定义

数据源是入口上携带的外部数据的来源属性——标识数据来自哪个不可信外部主体或通道，决定数据的可控性和信任级别。

## 包含边界

- HTTP请求：请求体、查询参数、路径参数、请求头
- 身份凭证：用户提交的token、cookie、API key
- 配置文件：外部可修改的配置文件内容
- 环境变量：运行时注入的环境变量
- 数据库读取：从数据库读出的数据（若数据库内容可能被污染）
- 消息队列：消息体内容
- 文件内容：用户上传或外部提供的文件内容
- 第三方API响应：外部服务返回的数据
- 用户输入：表单输入、UI交互输入
- 代码生成输入：AI/Agent系统的prompt、模板输入

## 排除边界

- 入口（ONT-ENTRY）不是数据源——入口是数据进入的通道，数据源是数据的来源属性
- 传播（ONT-PROPAGATION）不是数据源——传播是数据进入后的内部流动，数据源是数据的起点属性
- 资产（ONT-ASSET）不是数据源——资产是被保护的对象，数据源是输入数据的来源

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `receives_from` | ONT-ENTRY | 数据源通过入口进入系统 |
| `propagates_to` | ONT-PROPAGATION | 数据源的数据传播至传播路径 |
| `crosses` | ONT-TRUST-BOUNDARY | 数据源通常跨越信任边界（从不可信到可信） |

## 正例

```python
# HTTP请求参数作为数据源
data = await request.post()
username = data['username']  # 数据源：HTTP POST表单字段
```

```python
# 环境变量作为数据源
db_url = os.environ.get('DATABASE_URL')  # 数据源：环境变量
```

## 反例

```python
# 这是内部常量，不是外部数据源
MAX_RETRIES = 3  # 编译期常量，不是不可信外部输入
```

## 代码信号

- 请求对象属性访问：`request.json`、`request.form`、`request.args`
- 环境变量读取：`os.environ`、`os.getenv`、`process.env`
- 文件读取：`open()`、`fs.readFile`、`File.ReadAllText`
- 消息体解析：`json.loads(message.body)`、`msg.value`
- 用户输入获取：`input()`、`scanf`、`cin`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/aiohttp | `await request.post()` / `request.query` / `request.json()` |
| Java/Spring | `@RequestParam` / `@RequestBody` / `@RequestHeader` |
| Node.js/Express | `req.body` / `req.query` / `req.params` |
| Go | `r.URL.Query()` / `r.Form` / `r.Header` |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力判断数据源的可控性
- `verification-and-rating`：验证与定级能力评估数据源的可控性（controllable）

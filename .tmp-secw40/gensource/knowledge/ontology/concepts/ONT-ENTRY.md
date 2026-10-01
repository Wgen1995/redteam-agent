# ONT-ENTRY：入口

## 定义

入口是攻击面上可被外部输入触达的具体通道点——外部数据通过入口进入系统内部，是数据流的起点。

## 包含边界

- HTTP路由：Web框架中注册的路由处理函数
- API endpoint：REST/GraphQL/RPC接口的具体端点
- CLI参数：命令行参数、选项、标准输入
- 消息消费者：消息队列的消费者回调
- 文件解析器：文件加载和解析入口
- 定时任务触发：cron/scheduler触发的执行入口
- 事件回调：事件监听器/订阅者回调
- RPC handler：RPC服务的请求处理函数
- GraphQL resolver：GraphQL查询/变更的解析函数
- WebSocket handler：WebSocket连接的消息处理函数

## 排除边界

- 攻击面（ONT-SURFACE）不是入口——攻击面是入口的集合容器，入口是具体通道点
- 数据源（ONT-SOURCE）不是入口——入口是通道，数据源是通道上数据的来源属性
- 传播（ONT-PROPAGATION）不是入口——传播是数据进入系统后的内部流动，入口是数据进入系统的边界点

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `receives_from` | ONT-SOURCE | 入口接收自数据源 |
| `propagates_to` | ONT-PROPAGATION | 入口将数据传播至传播路径 |
| `guarded_by` | ONT-GUARD | 入口可能被守卫保护 |
| `sanitized_by` | ONT-SANITIZER | 入口处可能有净化器处理输入 |

## 正例

```python
# HTTP路由入口
@app.route("/api/users/<id>", methods=["POST"])
def update_user(id):
    data = request.json  # 外部数据通过此入口进入
    ...
```

```python
# CLI参数入口
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)  # CLI参数入口
    args = parser.parse_args()
    ...
```

## 反例

```python
# 这是传播路径上的内部函数调用，不是入口
def process_data(data):
    result = transform(data)  # 内部传播，不是外部输入的入口
    ...
```

## 代码信号

- Web框架路由注册：`@app.route`、`@GetMapping`、`router.GET`
- 请求对象引用：`request`、`req`、`ctx.request`
- 参数解析：`argparse`、`process.argv`、`os.Args`
- 消息消费：`@KafkaListener`、`consumer.subscribe`
- 事件监听：`addEventListener`、`@EventHandler`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/aiohttp | `async def handler(request):`中的request对象 |
| Java/Spring | `@RequestMapping`注解的方法参数 |
| Node.js/Express | `(req, res) => {}`中的req对象 |
| Go | `func(w http.ResponseWriter, r *http.Request)`中的r |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `scope-and-context`：范围与威胁语境能力枚举攻击面上的入口实例
- `candidate-discovery`：候选发现能力对每个入口点执行模式驱动发现
- `verification-and-rating`：验证与定级能力评估入口的可控性

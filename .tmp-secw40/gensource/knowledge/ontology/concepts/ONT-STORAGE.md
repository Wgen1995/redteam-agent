# ONT-STORAGE：存储

## 定义

存储是传播路径上的持久化节点——数据在流动过程中被写入持久化存储介质，后续可能从存储中读出继续传播，存储引入了时间延迟和跨请求/跨会话的传播可能。

## 包含边界

- 数据库存储：数据写入关系型数据库/NoSQL数据库
- 文件存储：数据写入文件系统
- 缓存存储：数据写入内存缓存（Redis/Memcached/进程内缓存）
- 会话存储：数据写入会话状态
- 消息队列：数据写入消息队列作为暂存
- 日志存储：数据写入日志（若日志后续被消费）

## 排除边界

- 传播（ONT-PROPAGATION）不是存储——传播是数据流动过程，存储是流动路径上的持久化节点
- 资产（ONT-ASSET）不是存储——资产是被保护的对象，存储是数据持久化操作
- Sink（ONT-SINK）不是存储——Sink是危险操作终点，存储是传播路径上的中间节点（除非存储操作本身是Sink，如写入可执行路径的文件）

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `variant_of` | ONT-PROPAGATION | 存储是传播路径上的特殊节点 |
| `stores_at` | ONT-PROPAGATION | 传播路径上将数据存储于存储节点 |
| `receives_from` | ONT-PROPAGATION | 存储节点接收自传播路径 |
| `propagates_to` | ONT-PROPAGATION | 存储节点读出后继续传播 |

## 正例

```python
# 数据库存储
def create_user(request):
    name = request.POST['name']       # Source
    user = User(name=name)
    user.save()                        # 存储：写入数据库
    # 后续其他请求可能从数据库读出name继续传播
```

```python
# 缓存存储
def set_cache(key, value):
    redis_client.set(key, value)       # 存储：写入Redis缓存
```

## 反例

```python
# 这是Sink（危险操作），不是中性存储
def write_file(path, content):
    with open(path, 'w') as f:         # 若path可控且写入可执行路径，这是Sink
        f.write(content)
```

## 代码信号

- 数据库写入：`save()`、`insert()`、`UPDATE` SQL语句、ORM写入方法
- 文件写入：`open(..., 'w')`、`fs.writeFile`、`File.WriteAllText`
- 缓存写入：`cache.set`、`redis.set`、`localStorage.setItem`
- 会话写入：`session['key'] = value`
- 消息发布：`producer.send`、`queue.publish`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Django | `model.save()` / `cache.set()` |
| Java/Spring | `repository.save()` / `redisTemplate.opsForValue().set()` |
| Node.js | `db.collection.insertOne()` / `redis.set()` |
| Go | `db.Exec("INSERT...")` / `rdb.Set()` |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力追踪传播路径上的存储节点
- `verification-and-rating`：验证与定级能力评估存储引入的跨请求传播可能性和数据污染风险

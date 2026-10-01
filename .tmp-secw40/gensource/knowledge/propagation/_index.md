# 传播类别索引（propagation/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务3。本文件是传播类别索引，容纳Propagation、Transformation和Storage三个子类，按统一格式记录各类传播节点。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID |
| name | 名称 |
| ontology_ref | 本体引用（ONT-PROPAGATION / ONT-TRANSFORMATION / ONT-STORAGE） |
| recognition_signals | 识别信号 |
| applicable_ecosystems | 适用生态 |
| related_semantics | 关联统一漏洞语义（后续任务填充） |
| source_refs | 来源引用 |
| version | 版本 |

## 子类：Propagation（ONT-PROPAGATION）

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| PROP-FUNC-CALL | 函数调用传播 | ONT-PROPAGATION | 数据作为参数传递给其他函数；被调用函数接收可控参数 | 全语言通用 | | 内部推导 | v0.1 |
| PROP-FIELD-PASS | 字段传递传播 | ONT-PROPAGATION | 数据赋值给对象字段/结构体成员后通过对象引用传递；`obj.field = value`/`this.attr = input` | Python/Java/JavaScript/Go | | 内部推导 | v0.1 |
| PROP-COLLECTION-OP | 集合操作传播 | ONT-PROPAGATION | 数据加入列表/字典/集合后随集合传递；`list.append()`/`map.put()`/`dict[key] = value` | Python/Java/JavaScript/Go | | 内部推导 | v0.1 |
| PROP-EVENT-BUS | 事件总线传播 | ONT-PROPAGATION | 数据通过事件发布/订阅机制传播；`event.emit()`/`publish()`/`dispatch()` | Node.js EventEmitter/Java EventBus/Kafka | | 内部推导 | v0.1 |
| PROP-CROSS-SERVICE | 跨服务调用传播 | ONT-PROPAGATION | 数据通过RPC/HTTP调用传播到其他服务；`client.call()`/`requests.post()`/`fetch()`内部服务间调用 | gRPC/REST/Thrift | | 内部推导 | v0.1 |

## 子类：Transformation（ONT-TRANSFORMATION）

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| TRANSFORM-TYPE-CAST | 类型转换 | ONT-TRANSFORMATION | `int()`/`str()`/`float()`/`parseInt()`/`strconv.Atoi`类型转换调用 | Python/Java/JavaScript/Go | | 内部推导 | v0.1 |
| TRANSFORM-FORMAT-CONV | 格式转换 | ONT-TRANSFORMATION | XML转JSON、CSV转对象、HTML转纯文本等格式转换 | Python/Java/JavaScript | | 内部推导 | v0.1 |
| TRANSFORM-STRUCT-REORG | 结构重组 | ONT-TRANSFORMATION | 列表转字典、对象字段重命名、嵌套结构扁平化 | 全语言通用 | | 内部推导 | v0.1 |
| TRANSFORM-STRING-OP | 字符串拼接/分割 | ONT-TRANSFORMATION | `+`拼接/`format()`/`split()`/`join()`/`template string`字符串操作 | 全语言通用 | | 内部推导 | v0.1 |

## 子类：Storage（ONT-STORAGE）

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| STORE-DB-WRITE | 数据库存储 | ONT-STORAGE | `save()`/`insert()`/`UPDATE`SQL/ORM写入方法调用 | SQLAlchemy/Django ORM/Hibernate/Prisma | | 内部推导 | v0.1 |
| STORE-FILE-WRITE | 文件存储 | ONT-STORAGE | `open(..., 'w')`/`fs.writeFile`/`File.WriteAllText`文件写入 | 全语言通用 | | 内部推导 | v0.1 |
| STORE-CACHE | 缓存存储 | ONT-STORAGE | `cache.set()`/`redis.set()`/`localStorage.setItem`缓存写入 | Redis/Memcached/进程内缓存 | | 内部推导 | v0.1 |
| STORE-SESSION | 会话存储 | ONT-STORAGE | `session['key'] = value`/`request.session`会话状态写入 | 全语言Web框架 | | 内部推导 | v0.1 |
| STORE-MQ-PERSIST | 消息队列暂存 | ONT-STORAGE | `producer.send()`/`queue.publish()`消息发布到队列 | Kafka/RabbitMQ/Redis | | 内部推导 | v0.1 |
| STORE-SERIALIZE | 序列化/反序列化 | ONT-TRANSFORMATION | `pickle.dumps()`/`json.dumps()`/`serialize()`/`JSON.stringify()`序列化；`pickle.loads()`/`json.loads()`/`deserialize()`反序列化 | Python/Java/JavaScript/Go | | 内部推导 | v0.1 |

## 消费方

- `candidate-discovery`：候选发现能力追踪从Source到Sink的传播路径
- `verification-and-rating`：验证与定级能力评估传播路径的可达性（reachable）和传播完整性（propagatable）

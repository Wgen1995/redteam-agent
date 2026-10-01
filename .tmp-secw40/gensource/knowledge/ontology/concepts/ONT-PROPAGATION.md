# ONT-PROPAGATION：传播

## 定义

传播是数据从数据源进入系统后在内部流动的过程——数据通过函数调用、字段传递、集合操作等方式在代码路径上传递，从入口到达Sink或其他节点。

## 包含边界

- 函数调用：数据作为参数传递给其他函数
- 字段传递：数据赋值给对象字段/结构体成员后通过对象引用传递
- 集合操作：数据加入列表/字典/集合后随集合传递
- 序列化/反序列化：数据在序列化和反序列化过程中传播
- 缓存：数据写入缓存后从缓存读出继续传播
- 数据库存储：数据写入数据库后从数据库读出继续传播
- 事件总线：数据通过事件发布/订阅机制传播
- 跨服务调用：数据通过RPC/HTTP调用传播到其他服务

## 排除边界

- 数据源（ONT-SOURCE）不是传播——数据源是数据的起点属性，传播是数据进入后的流动过程
- 转换（ONT-TRANSFORMATION）不是传播——转换是传播过程中数据结构或类型的变换，传播是流动本身
- 存储（ONT-STORAGE）不是传播——存储是传播路径上的持久化节点，传播是流动过程

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `receives_from` | ONT-SOURCE | 传播接收自数据源 |
| `propagates_to` | ONT-SINK | 传播到达Sink |
| `transforms_to` | ONT-TRANSFORMATION | 传播过程中发生转换 |
| `stores_at` | ONT-STORAGE | 传播路径上存在存储节点 |

## 正例

```python
# 函数调用传播
def handler(request):
    name = request.POST['name']       # Source
    result = process_name(name)       # 传播：函数调用
    db.save(result)                   # Sink

def process_name(value):
    return value.strip()              # 传播：参数传递
```

## 反例

```python
# 这是Sink（危险操作），不是传播
def handler(request):
    name = request.POST['name']
    os.system("echo " + name)  # 这是Sink，数据到达危险操作
```

## 代码信号

- 函数调用链：参数从调用者传递到被调用函数
- 赋值语句：变量赋值导致数据从一个变量流动到另一个变量
- 集合操作：`append`、`insert`、`put`等将数据加入集合
- 返回值：函数返回值将数据传播给调用者
- 对象属性设置：`obj.field = value`将数据传播到对象属性

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python | 函数参数传递、变量赋值、列表/字典操作 |
| Java | 方法参数传递、setter调用、List/Map操作 |
| JavaScript | 函数参数传递、对象属性赋值、数组操作 |
| Go | 函数参数传递、struct字段赋值、slice/map操作 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力追踪从Source到Sink的传播路径
- `verification-and-rating`：验证与定级能力评估传播路径的可达性（reachable）和传播完整性（propagatable）

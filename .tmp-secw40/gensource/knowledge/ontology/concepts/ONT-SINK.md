# ONT-SINK：汇点

## 定义

汇点是数据流终点上执行危险操作的节点——当可控数据到达Sink时，可能触发对资产的安全性损害。

## 包含边界

- SQL执行：`execute()`、`query()`执行包含可控数据的SQL语句
- 命令执行：`os.system()`、`subprocess.call()`执行包含可控数据的系统命令
- 模板渲染：模板引擎渲染包含可控数据的模板
- 文件写入：向包含可控数据的路径写入文件
- 网络请求：向包含可控数据的目标发起网络请求（SSRF）
- 反序列化：反序列化包含可控数据的字节流
- 权限决策调用：以可控参数调用权限变更操作
- 内存操作：以可控参数操作内存（缓冲区操作、指针解引用）
- LDAP/XPath查询：以可控数据构造查询语句

## 排除边界

- 状态转换（ONT-STATE-TRANSITION）不是Sink——状态转换是系统状态的变更节点，Sink是危险操作节点。有些Sink同时是状态转换节点，但概念上独立。
- 资源消耗（ONT-RESOURCE-CONSUMPTION）不是Sink——资源消耗是资源使用节点，Sink是危险操作节点。有些Sink导致资源消耗，但概念上独立。
- 传播（ONT-PROPAGATION）不是Sink——传播是数据流动过程，Sink是流动终点上的危险操作。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `receives_from` | ONT-PROPAGATION | Sink接收自传播路径 |
| `guarded_by` | ONT-GUARD | Sink可能被Guard保护 |
| `encoded_by` | ONT-ENCODER | Sink前的数据可能被Encoder编码 |
| `causes` | ONT-SECURITY-IMPACT | Sink触发导致安全影响 |

## 正例

```python
# SQL执行Sink
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")  # Sink：SQL执行
# 可控数据name到达SQL执行Sink

# 命令执行Sink
os.system("ls " + directory)  # Sink：命令执行
# 可控数据directory到达命令执行Sink
```

## 反例

```python
# 这是传播路径上的函数调用，不是Sink
def transform(data):
    return data.upper()  # 中性操作，不是危险操作
```

## 代码信号

- SQL执行：`.execute()`、`.query()`、`executeQuery`
- 命令执行：`os.system`、`subprocess.call`、`Runtime.exec`、`child_process.exec`
- 模板渲染：`render()`、`render_template()`、模板字符串插值
- 文件写入：`open(..., 'w')`、`fs.writeFile`、`File.WriteAllText`
- 网络请求：`requests.get`、`fetch`、`http.Get`
- 反序列化：`pickle.loads`、`json.loads`（当解析结果被当作代码执行时）

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python | `cursor.execute()` / `os.system()` / `subprocess.call()` |
| Java | `Statement.execute()` / `Runtime.exec()` / `ProcessBuilder` |
| Node.js | `connection.query()` / `child_process.exec()` / `eval()` |
| Go | `db.Exec()` / `exec.Command()` |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力在传播路径终点识别Sink
- `verification-and-rating`：验证与定级能力评估Sink的可利用性（exploitable）和影响成立（impact）
- `exploit-proof`：利用证明能力针对Sink构造可利用性证明

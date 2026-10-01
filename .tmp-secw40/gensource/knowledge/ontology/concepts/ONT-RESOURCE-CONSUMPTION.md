# ONT-RESOURCE-CONSUMPTION：资源消耗

## 定义

资源消耗是系统资源的使用节点——当操作消耗计算、存储、网络或时间资源时，可能因缺乏资源限制导致拒绝服务或资源耗尽。

## 包含边界

- 计算资源消耗：CPU密集型操作、无限循环、复杂正则匹配（ReDoS）
- 内存资源消耗：大对象分配、内存泄漏、无限制的缓存增长
- 存储资源消耗：磁盘写入、日志膨胀、临时文件堆积
- 网络资源消耗：大量出站请求、大文件传输、带宽消耗
- 连接资源消耗：数据库连接池耗尽、文件描述符耗尽
- 时间资源消耗：长时间阻塞操作、慢查询
- API调用配额消耗：第三方API调用次数限制

## 排除边界

- Sink（ONT-SINK）不是资源消耗——Sink是危险操作节点，资源消耗是资源使用节点。有些Sink导致资源消耗（如大文件写入Sink），但概念上独立。
- 状态转换（ONT-STATE-TRANSITION）不是资源消耗——状态转换是状态变更节点，资源消耗是资源使用节点。
- 资产（ONT-ASSET）不是资源消耗——资产是被保护的对象，资源消耗是资源使用操作。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `consumes_resource_at` | ONT-PROPAGATION | 传播到达资源消耗节点时消耗资源 |
| `guarded_by` | ONT-GUARD | 资源消耗可能被限流Guard保护 |
| `causes` | ONT-SECURITY-IMPACT | 资源耗尽导致安全影响（可用性损害） |

## 正例

```python
# ReDoS——计算资源消耗
def validate_input(pattern, user_input):
    return re.match(pattern, user_input)  # 若pattern是邪恶正则，user_input可导致指数级CPU消耗

# 内存资源消耗
def process_file(file):
    data = file.read()  # 若file是用户上传的大文件，无大小限制地全部读入内存
    return process(data)
```

## 反例

```python
# 这是Sink（危险操作），不是资源消耗
def execute_command(cmd):
    os.system(cmd)  # 命令执行是Sink，不是资源消耗
```

## 代码信号

- 循环操作：`while True`、`for`循环（可能无终止条件）
- 大对象分配：`list(range(huge_number))`、大数组初始化
- 文件读取无大小限制：`file.read()`无`size`参数
- 正则匹配：`re.match(evil_pattern, user_input)`
- 无分页查询：`SELECT * FROM huge_table`无LIMIT
- 无限流标记：缺少rate limit中间件/装饰器

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python | `re.match()` / `file.read()` / `list(range(...))` |
| Java | `Pattern.matcher()` / 无限制集合增长 |
| Node.js | 正则匹配 / `Buffer.alloc(huge)` |
| Go | `regexp.MatchString()` / 无限制slice增长 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别资源消耗缺少限制的信号
- `verification-and-rating`：验证与定级能力评估资源消耗是否可被滥用导致拒绝服务（非污点模型）
- `remediation-guidance`：修复指导能力为缺失的资源限制补齐限流/配额

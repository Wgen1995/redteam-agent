# ONT-OBSERVABLE-ORACLE：可观察预言机

## 定义

可观察预言机是判断安全影响是否实际发生的观察手段——通过可测量的外部表现（响应差异、状态变更、资源变化、错误信息、时序差异等）来确认漏洞被触发并产生了实际影响。

## 包含边界

- 响应差异预言机：攻击成功与失败的HTTP响应状态码/内容/长度不同
- 状态变更预言机：攻击后系统状态可被独立验证为已改变（如数据库记录被修改）
- 错误信息预言机：攻击触发的错误信息泄露了内部状态（如SQL错误信息暴露表结构）
- 时序差异预言机：攻击成功与失败的响应时间存在可测量差异（盲注时序）
- 副作用预言机：攻击产生了可观察的副作用（如DNS查询、网络连接、文件创建）
- 日志预言机：攻击在日志中留下了可验证的痕迹
- 权限提升预言机：攻击后可访问先前无法访问的资源

## 排除边界

- Security Impact（ONT-SECURITY-IMPACT）不是可观察预言机——安全影响是损害本身，可观察预言机是观察损害是否发生的手段。
- Sink（ONT-SINK）不是可观察预言机——Sink是危险操作节点，可观察预言机是观察操作后果的手段。
- 资产（ONT-ASSET）不是可观察预言机——资产是被保护的对象，可观察预言机是观察手段。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `observed_by` | ONT-SECURITY-IMPACT | 安全影响被可观察预言机观察 |
| `receives_from` | ONT-SINK | 可观察预言机观察Sink的触发后果 |
| `receives_from` | ONT-STATE-TRANSITION | 可观察预言机观察状态转换的后果 |

## 正例

```python
# 响应差异预言机
# 攻击成功与失败的响应不同——用于确认SQL注入
try:
    cursor.execute("SELECT * FROM users WHERE id = " + user_input)
    return jsonify(cursor.fetchone())
except Exception:
    return jsonify({"error": "SQL syntax error"})  # 错误信息预言机：泄露SQL错误

# 时序差异预言机——盲注
import time
start = time.time()
response = requests.get(url + "?id=1 AND SLEEP(5)")
elapsed = time.time() - start
if elapsed > 4:  # 时序差异确认注入
    print("Blind SQL injection confirmed")
```

## 反例

```python
# 这是Sink（危险操作），不是可观察预言机
cursor.execute(query)  # 这是Sink，可观察预言机是观察这个Sink后果的手段
```

## 代码信号

- 错误处理分支：`try/except`、`catch`中返回的差异化响应
- 响应构造：不同条件返回不同状态码/内容
- 日志记录：操作后写入日志
- 状态查询：操作后查询并返回变更后的状态
- 时序测量：`time.time()`、`Date.now()`用于测量操作耗时

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Web框架通用 | 不同HTTP状态码的响应分支、错误页面与正常页面的内容差异 |
| 数据库 | SQL错误信息、查询结果的差异 |
| 日志系统 | 操作后的日志条目 |
| 监控系统 | 资源使用指标的变更 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `exploit-proof`：利用证明能力使用可观察预言机确认漏洞被触发并产生实际影响
- `verification-and-rating`：验证与定级能力使用可观察预言机区分true positive和false positive
- `report-delivery`：报告交付能力引用预言机观察结果作为证据

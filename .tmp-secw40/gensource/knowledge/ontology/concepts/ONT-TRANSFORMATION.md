# ONT-TRANSFORMATION：转换

## 定义

转换是传播过程中数据结构或类型的变换——数据在流动过程中经过格式转换、类型转换、编码转换或结构重组，形态发生变化但语义关联保持。

## 包含边界

- 类型转换：字符串转整数、字节流转字符串、JSON解析
- 格式转换：XML转JSON、CSV转对象列表、HTML转纯文本
- 编码转换：Base64解码、URL解码、HTML实体解码
- 结构重组：列表转字典、对象字段重命名、嵌套结构扁平化
- 序列化/反序列化：对象序列化为字节流、字节流反序列化为对象
- 数据拼接/分割：字符串拼接、字符串分割

## 排除边界

- 传播（ONT-PROPAGATION）不是转换——传播是数据流动本身，转换是流动过程中形态的变化
- 净化器（ONT-SANITIZER）不是转换——净化器是使输入变得安全或符合预期格式的安全控制，转换是中性的数据形态变换
- 编码器（ONT-ENCODER）不是转换——编码器是在特定输出上下文对数据进行安全编码的安全控制，转换是中性变换

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `variant_of` | ONT-PROPAGATION | 转换是传播过程中的特殊形态 |
| `transforms_to` | ONT-PROPAGATION | 传播过程中发生转换 |
| `propagates_to` | ONT-SINK | 转换后的数据继续传播至Sink |

## 正例

```python
# JSON解析转换
raw = request.body              # Source: 原始字节流
data = json.loads(raw)          # 转换：字节流→字典
name = data['name']             # 传播：从字典中提取字段
```

```python
# 类型转换
id_str = request.args['id']    # Source: 字符串
id_int = int(id_str)           # 转换：字符串→整数
```

## 反例

```python
# 这是净化器（ONT-SANITIZER），不是中性转换
clean = html.escape(user_input)  # 这是安全控制，目的是使输入安全
```

## 代码信号

- 类型转换函数：`int()`、`str()`、`float()`、`bool()`
- 解析函数：`json.loads`、`xml.parse`、`yaml.load`
- 编码/解码函数：`base64.b64decode`、`urllib.parse.unquote`
- 序列化/反序列化：`pickle.loads`、`json.dumps`
- 字符串操作：`split()`、`join()`、`format()`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python | `json.loads`、`int()`、`pickle.loads` |
| Java | `Integer.parseInt`、`ObjectMapper.readValue` |
| JavaScript | `JSON.parse`、`parseInt`、`Buffer.from` |
| Go | `json.Unmarshal`、`strconv.Atoi` |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力追踪传播路径上的转换节点
- `verification-and-rating`：验证与定级能力评估转换是否改变了数据的可控性或引入了新的攻击面

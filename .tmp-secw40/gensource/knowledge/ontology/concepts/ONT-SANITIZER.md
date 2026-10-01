# ONT-SANITIZER：净化器

## 定义

净化器是对输入进行验证、规范化或净化的安全控制——使输入变得安全或符合预期格式，防止恶意数据进入后续传播路径。

## 包含边界

- 输入验证：检查输入是否符合预期格式、长度、范围、类型（如"必须是合法邮箱""必须是正整数"）
- 规范化：将输入转换为标准/规范形式（如URL归一化、Unicode规范化、路径规范化）
- 净化：移除或转义输入中的危险字符/内容（如移除SQL元字符、移除HTML标签）
- 白名单过滤：只允许输入中符合白名单的内容通过
- 参数绑定/参数化：使用参数化查询将输入与SQL文本分离（这是防止SQL注入的Sanitizer形式）
- Schema验证：使用JSON Schema/XSD等验证输入结构

## 排除边界

- **不是授权决策**——授权决策属于Guard（ONT-GUARD），不是Sanitizer。Sanitizer关心的是"输入是否合法/安全"，不关心"主体有没有权限"。
- **不是输出编码**——输出编码属于Encoder（ONT-ENCODER），不是Sanitizer。Sanitizer作用于输入侧（数据进入系统时），Encoder作用于输出侧（数据离开系统进入解释器时）。
- **不是中性转换**——中性数据形态变换属于Transformation（ONT-TRANSFORMATION），不是Sanitizer。Sanitizer有安全目的（使输入安全/合规），Transformation是中性的形态变换。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `sanitized_by` | ONT-ENTRY | 入口处的输入被Sanitizer处理 |
| `sanitized_by` | ONT-PROPAGATION | 传播路径上的数据被Sanitizer处理 |
| `crosses` | ONT-TRUST-BOUNDARY | Sanitizer通常位于信任边界上 |

## 正例

```python
# 输入验证——Sanitizer的典型表现
def validate_username(username):
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):  # 验证输入格式
        raise ValueError("invalid username")
    return username

# 参数化查询——防止SQL注入的Sanitizer形式
def get_user(cursor, user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # 参数绑定，输入与SQL文本分离
```

```python
# 规范化——Sanitizer
def normalize_path(path):
    return os.path.normpath(path)  # 路径规范化，防止路径遍历
```

## 反例

```python
# 这是Guard（授权检查），不是Sanitizer
if not user.is_admin:  # 授权决策，不是输入验证
    raise Forbidden()
# Sanitizer关心的是"输入是否合法/安全"，不关心"主体有没有权限"
```

```python
# 这是Encoder（输出编码），不是Sanitizer
def render_html(content):
    return html.escape(content)  # 输出上下文编码，不是输入验证
# Sanitizer作用于输入侧，Encoder作用于输出侧
```

## 代码信号

- 验证函数调用：`validate_*`、`check_*`、`is_valid_*`
- 正则匹配验证：`re.match`、`re.fullmatch`用于验证输入格式
- 参数化查询：`execute(sql, params)`两参数形式、`PreparedStatement`
- 白名单过滤：`if value not in ALLOWED_VALUES`
- Schema验证：`jsonschema.validate`、`pydantic`模型验证
- 规范化函数：`os.path.normpath`、`unicodedata.normalize`、`urllib.parse.urljoin`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python | `re.match`验证 / `pydantic`模型 / `execute(sql, params)`参数化 |
| Java | `Pattern.matches`验证 / `@Valid`注解 / `PreparedStatement`参数化 |
| JavaScript | `validator.isEmail` / `Joi`验证 / `parseInt`类型收紧 |
| Go | `regexp.MatchString` / 参数化查询 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；Guard/Sanitizer/Encoder三者独立区分要求
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别Sanitizer缺失或可绕过的信号
- `verification-and-rating`：验证与定级能力评估Sanitizer是否正确执行输入验证/净化
- `remediation-guidance`：修复指导能力为缺失的Sanitizer补齐输入验证

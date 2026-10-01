# ONT-ENCODER：编码器

## 定义

编码器是在特定输出上下文（HTML、URL、JavaScript、CSS、SQL等）中对数据进行安全编码的安全控制——防止数据被输出上下文的解释器误解析为代码。

## 包含边界

- HTML编码：在HTML输出上下文中对特殊字符进行HTML实体编码（如`<`→`&lt;`、`>`→`&gt;`）
- URL编码：在URL输出上下文中对特殊字符进行百分号编码
- JavaScript编码：在JavaScript字符串字面量输出上下文中对特殊字符进行转义
- CSS编码：在CSS输出上下文中对特殊字符进行转义
- SQL标识符编码：在SQL输出上下文中对标识符进行引用/转义（注意：SQL值参数化属于Sanitizer，SQL标识符编码属于Encoder）
- 模板引擎自动转义：模板引擎在渲染时自动对输出进行上下文感知编码

## 排除边界

- **不是输入验证**——输入验证属于Sanitizer（ONT-SANITIZER），不是Encoder。Encoder作用于输出侧（数据离开系统进入解释器时），Sanitizer作用于输入侧（数据进入系统时）。
- **不是授权决策**——授权决策属于Guard（ONT-GUARD），不是Encoder。Encoder关心的是"输出怎么编码才安全"，不关心"主体有没有权限"。
- **不是中性转换**——中性的编码/解码（如Base64编码、URL解码）属于Transformation（ONT-TRANSFORMATION），不是Encoder。Encoder有安全目的（防止解释器误解析），Transformation是中性的形态变换。
- **SQL值参数化属于Sanitizer**——参数化查询将输入与SQL文本分离，是输入侧的净化控制，不是输出编码。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `encoded_by` | ONT-SINK | Sink前的数据被Encoder编码 |
| `encoded_by` | ONT-PROPAGATION | 传播路径终点处的数据被Encoder编码 |
| `reaches` | ONT-SINK | Encoder编码后的数据到达Sink |

## 正例

```python
# HTML编码——Encoder的典型表现
def render_username(name):
    return html.escape(name)  # HTML输出上下文编码，防止XSS
    # < → &lt;  > → &gt;  & → &amp;  " → &#34;  ' → &#39;

# 模板引擎自动转义——Encoder
# Jinja2配置autoescape=True后，模板渲染时自动对输出进行HTML编码
env = jinja2.Environment(autoescape=True)
template = env.from_string("<p>{{ user_input }}</p>")
# user_input中的<script>标签会被自动编码为&lt;script&gt;
```

```python
# URL编码——Encoder
def build_redirect_url(url):
    return urllib.parse.quote(url, safe='')  # URL输出上下文编码
```

## 反例

```python
# 这是Sanitizer（输入验证），不是Encoder
def validate_email(email):
    if not re.match(r'^[^@]+@[^@]+$', email):  # 输入验证，不是输出编码
        raise ValueError()
# Encoder作用于输出侧，Sanitizer作用于输入侧
```

```python
# 这是Guard（授权检查），不是Encoder
if not user.is_admin:  # 授权决策，不是输出编码
    raise Forbidden()
# Encoder关心的是"输出怎么编码才安全"，不关心"主体有没有权限"
```

```python
# 这是中性转换，不是Encoder
encoded = base64.b64encode(data)  # Base64是中性编码，没有安全目的
# Encoder有安全目的（防止解释器误解析），Base64只是中性变换
```

## 代码信号

- HTML编码函数：`html.escape`、`htmlspecialchars`、`HtmlUtils.htmlEscape`
- 模板自动转义配置：`autoescape=True`（Jinja2）、`autoescaping`（Django）
- URL编码函数：`urllib.parse.quote`、`encodeURIComponent`、`urlencode`
- JavaScript编码函数：`JSON.stringify`（用于JS字符串上下文）、自定义JS转义
- CSS编码函数：CSS转义库调用
- 模板引擎safe过滤器标注的例外：`|safe`（Jinja2）——表示此处显式跳过编码，需要特别关注

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Jinja2 | `autoescape=True`全局配置 / `html.escape()`函数 |
| Python/Django | 模板引擎默认自动转义 / `escape()`函数 |
| Java/Thymeleaf | 模板引擎默认自动转义 / `HtmlUtils.htmlEscape()` |
| JavaScript/React | JSX默认对插值进行编码 / `encodeURIComponent()` |
| PHP | `htmlspecialchars()` / Twig模板自动转义 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；Guard/Sanitizer/Encoder三者独立区分要求
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别Encoder缺失或上下文不匹配的信号
- `verification-and-rating`：验证与定级能力评估Encoder是否在正确的输出上下文中执行了编码
- `remediation-guidance`：修复指导能力为缺失的Encoder补齐输出编码

# 控制类别索引（controls/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务3。本文件是控制类别索引，分别列出Guard、Policy Decision、Sanitizer和Encoder四个子类，不设置笼统的"security control"替代项。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID |
| name | 名称 |
| ontology_ref | 本体引用（ONT-GUARD / ONT-POLICY-DECISION / ONT-SANITIZER / ONT-ENCODER） |
| recognition_signals | 识别信号 |
| applicable_ecosystems | 适用生态 |
| related_semantics | 关联统一漏洞语义（后续任务填充） |
| source_refs | 来源引用 |
| version | 版本 |

## 子类：Guard（ONT-GUARD）

> Guard只表达主体（Principal）是否有权执行动作（Action），是授权决策点。不包含输入验证或数据净化。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| CTRL-GUARD-AUTH | 认证 | ONT-GUARD | `@login_required`/`@PreAuthorize("isAuthenticated()")`/认证中间件注册 | Python/Django、Java/Spring、Node.js/Express | | 内部推导 | v0.1 |
| CTRL-GUARD-AUTHZ | 授权 | ONT-GUARD | `@admin_required`/`@PreAuthorize("hasRole('ADMIN')")`/`if not user.has_permission`权限检查 | Python/Django、Java/Spring、Ruby/Rails | | 内部推导 | v0.1 |
| CTRL-GUARD-TENANT | 租户隔离 | ONT-GUARD | `if obj.tenant_id != current_tenant.id`租户隔离条件检查 | 多租户SaaS | | 内部推导 | v0.1 |
| CTRL-GUARD-STATE | 状态条件 | ONT-GUARD | `if order.status != 'pending'`状态条件守卫——检查系统状态是否允许执行操作 | 全语言通用 | | 内部推导 | v0.1 |
| CTRL-GUARD-RATELIMIT | 限流 | ONT-GUARD | rate limit中间件/装饰器/`@RateLimit`注解——限制请求频率作为可用性守卫 | 全语言Web框架 | | 内部推导 | v0.1 |
| CTRL-GUARD-CAPABILITY | 能力检查 | ONT-GUARD | `if not user.can('action')`/能力令牌验证——检查主体是否持有执行操作所需的能力 | Casbin/OPA/自定义能力系统 | | 内部推导 | v0.1 |

## 子类：Policy Decision（ONT-POLICY-DECISION）

> Policy Decision是授权策略的逻辑判定——根据主体属性、资源属性、动作属性和环境条件判定权限。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| CTRL-POLICY-RBAC | RBAC策略 | ONT-POLICY-DECISION | `if user.role in allowed_roles`/角色策略评估函数 | Django Guardian/Spring Security | | 内部推导 | v0.1 |
| CTRL-POLICY-ABAC | ABAC策略 | ONT-POLICY-DECISION | 基于属性的策略引擎调用/`policy_engine.evaluate(subject, action, resource)` | OPA/Casbin/XACML | | 内部推导 | v0.1 |
| CTRL-POLICY-RELATION | 关系策略 | ONT-POLICY-DECISION | `if resource.owner_id == user.id`基于主体与资源关系的策略 | 全语言通用 | | 内部推导 | v0.1 |
| CTRL-POLICY-ENV | 环境条件策略 | ONT-POLICY-DECISION | 基于时间/IP/设备等环境因素的策略条件 | 全语言通用 | | 内部推导 | v0.1 |

## 子类：Sanitizer（ONT-SANITIZER）

> Sanitizer表达对输入的验证、规范化或净化，使输入变得安全或符合预期格式。不是授权决策，也不是输出编码。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| CTRL-SANIT-VALIDATE | 输入验证 | ONT-SANITIZER | `re.match`/`validator.isEmail`/`@Valid`注解/`pydantic`模型验证——检查输入是否符合预期格式 | Python/Java/JavaScript/Go | | 内部推导 | v0.1 |
| CTRL-SANIT-NORMALIZE | 规范化 | ONT-SANITIZER | `os.path.normpath`/`unicodedata.normalize`/`urllib.parse.urljoin`——将输入转换为标准/规范形式 | Python/Java/JavaScript | | 内部推导 | v0.1 |
| CTRL-SANIT-PARAM-BIND | 参数绑定 | ONT-SANITIZER | `execute(sql, params)`两参数形式/`PreparedStatement`——使用参数化查询将输入与SQL文本分离 | Python/Java/Node.js/Go | | 内部推导 | v0.1 |
| CTRL-SANIT-PURIFY | 净化 | ONT-SANITIZER | 移除或转义输入中的危险字符/内容；`bleach.clean`/`DOMPurify`/白名单过滤 | Python/JavaScript/PHP | | 内部推导 | v0.1 |
| CTRL-SANIT-SCHEMA | Schema验证 | ONT-SANITIZER | `jsonschema.validate`/`@Valid`/XSD验证——使用Schema验证输入结构 | Python/Java/JavaScript | | 内部推导 | v0.1 |
| CTRL-SANIT-SQL-PARAM | SQL参数化 | ONT-SANITIZER | `execute("SELECT ... WHERE id = %s", (id,))`——参数化查询防止SQL注入 | Python/Java/Node.js/Go | | 内部推导 | v0.1 |

## 子类：Encoder（ONT-ENCODER）

> Encoder表达在特定输出上下文（HTML、URL、JS、CSS、SQL等）中对数据进行安全编码，防止解释器误解析。不是输入验证，也不是授权决策。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| CTRL-ENC-HTML | HTML编码 | ONT-ENCODER | `html.escape`/`htmlspecialchars`/`HtmlUtils.htmlEscape`/模板引擎autoescape=True——HTML输出上下文编码 | Python/Java/PHP/JavaScript | | 内部推导 | v0.1 |
| CTRL-ENC-URL | URL编码 | ONT-ENCODER | `urllib.parse.quote`/`encodeURIComponent`/`urlencode`——URL输出上下文编码 | Python/JavaScript/Java | | 内部推导 | v0.1 |
| CTRL-ENC-JS | JS编码 | ONT-ENCODER | `JSON.stringify`用于JS字符串上下文/自定义JS转义函数——JavaScript输出上下文编码 | Python/Java/JavaScript | | 内部推导 | v0.1 |
| CTRL-ENC-CSS | CSS编码 | ONT-ENCODER | CSS转义库调用/`\\`十六进制转义——CSS输出上下文编码 | 全语言通用 | | 内部推导 | v0.1 |
| CTRL-ENC-SQL-ID | SQL标识符编码 | ONT-ENCODER | SQL标识符引用/转义（注意：SQL值参数化属于Sanitizer，SQL标识符编码属于Encoder） | Python/Java/Node.js/Go | | 内部推导 | v0.1 |
| CTRL-ENC-TEMPLATE-AUTOESCAPE | 模板自动转义 | ONT-ENCODER | Jinja2 `autoescape=True`/Django默认转义/Thymeleaf默认转义/React JSX默认编码——模板引擎自动编码 | Jinja2/Django/Thymeleaf/React | | 内部推导 | v0.1 |

## 消费方

- `candidate-discovery`：候选发现能力识别控制缺失或配置错误的信号
- `verification-and-rating`：验证与定级能力分别评估Guard、Policy Decision、Sanitizer和Encoder四类控制
- `remediation-guidance`：修复指导能力按控制类型提供针对性修复

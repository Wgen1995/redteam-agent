# ONT-GUARD：守卫

## 定义

守卫是授权决策点——只表达主体（Principal）是否有权执行动作（Action），不包含输入验证或数据净化。

## 包含边界

- 授权检查：验证当前用户是否有权限执行请求的操作（如`@login_required`、`@admin_required`）
- 角色检查：验证当前用户是否属于允许执行操作的角色（如`@roles_required('admin')`）
- 租户隔离检查：验证当前用户是否有权访问目标租户的数据
- 能力检查：验证当前主体是否持有执行操作所需的能力令牌
- 访问控制列表（ACL）检查：验证主体是否在目标资源的允许访问列表中
- 状态条件守卫：验证系统状态是否允许执行操作（如"只有在pending状态才能取消订单"）

## 排除边界

- **不包含输入验证或数据净化**——输入验证和净化属于Sanitizer（ONT-SANITIZER），不是Guard。Guard只回答"主体有没有权限"，不回答"输入是否合法/安全"。
- **不包含输出编码**——输出编码属于Encoder（ONT-ENCODER），不是Guard。Guard关注的是授权决策，不是数据在输出上下文中的表示。
- **不是策略决策（ONT-POLICY-DECISION）**——Guard是授权决策的执行点（在哪里做检查），Policy Decision是授权策略的逻辑（根据什么规则判定）。Guard调用Policy Decision做出判定，但Guard本身只是决策点的存在，不是策略逻辑。
- **不是信任边界（ONT-TRUST-BOUNDARY）**——信任边界是划分信任级别的分界线，Guard是边界上的授权检查机制。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `guarded_by` | ONT-ENTRY | 入口被Guard保护 |
| `guarded_by` | ONT-SINK | Sink被Guard保护 |
| `decided_by` | ONT-POLICY-DECISION | Guard的决策由Policy Decision做出 |
| `crosses` | ONT-TRUST-BOUNDARY | Guard位于信任边界上 |

## 正例

```python
# 授权装饰器——Guard的典型表现
def admin_required(fn):
    async def wrapper(request):
        if not request.user.is_admin:     # Guard：检查主体是否有权执行动作
            raise HTTPUnauthorized()
        return await fn(request)
    return wrapper

@app.route("/admin/users/delete/<id>")
@admin_required                          # Guard在此做授权检查
def delete_user(id):
    ...
```

```python
# 租户隔离检查——Guard
def get_order(request, order_id):
    order = Order.objects.get(id=order_id)
    if order.tenant_id != request.user.tenant_id:  # Guard：租户隔离
        raise HTTPForbidden()
    return order
```

## 反例

```python
# 这是Sanitizer（输入验证），不是Guard
def validate_email(email):
    if not re.match(r'^[^@]+@[^@]+$', email):  # 验证输入格式，不是授权检查
        raise ValueError("invalid email")
# Guard关心的是"主体有没有权限"，不是"输入格式对不对"
```

```python
# 这是Encoder（输出编码），不是Guard
def render_template(content):
    return html.escape(content)  # 输出上下文编码，不是授权检查
# Guard关心的是"主体有没有权限"，不是"输出怎么编码"
```

## 代码信号

- 授权装饰器/中间件：`@login_required`、`@admin_required`、`@roles_required`
- 权限检查分支：`if not user.has_permission(...)`、`if user.role != 'admin'`
- 租户隔离条件：`if obj.tenant_id != current_tenant.id`
- ACL检查：`if user not in resource.acl`
- 能力令牌检查：`if not user.can('delete_post')`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Django | `@login_required` / `@permission_required` 装饰器 |
| Java/Spring | `@PreAuthorize("hasRole('ADMIN')")` / `@Secured` 注解 |
| Node.js/Express | 认证中间件 / `if (req.user.role !== 'admin')` 检查 |
| Ruby/Rails | `before_action :authorize_admin` 过滤器 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；Guard/Sanitizer/Encoder三者独立区分要求
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别Guard缺失或配置错误的信号
- `verification-and-rating`：验证与定级能力评估Guard是否正确执行授权决策
- `remediation-guidance`：修复指导能力为缺失的Guard补齐授权检查

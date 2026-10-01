# ONT-STATE-TRANSITION：状态转换

## 定义

状态转换是系统状态的变更节点——当操作改变系统的安全相关状态时，可能违反状态不变量，导致未授权的状态访问或不可逆的状态变更。

## 包含边界

- 权限状态变更：用户角色/权限的升降变更
- 会话状态变更：登录/登出、会话令牌轮换
- 资源状态变更：订单状态从pending到confirmed、账户状态从active到suspended
- 配置状态变更：安全配置的修改（如开启/关闭MFA）
- 状态机迁移：有限状态机中状态间的迁移操作
- 并发状态变更：并发条件下的状态竞争（TOCTOU）

## 排除边界

- Sink（ONT-SINK）不是状态转换——Sink是危险操作节点，状态转换是状态变更节点。有些Sink同时是状态转换节点（如权限变更Sink），但概念上独立。
- 资源消耗（ONT-RESOURCE-CONSUMPTION）不是状态转换——资源消耗是资源使用节点，状态转换是状态变更节点。
- Guard（ONT-GUARD）不是状态转换——状态条件守卫（如"只有pending状态才能取消"）是Guard的一种形式（检查状态条件是否满足），状态转换是状态本身的变更操作。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `changes_state_at` | ONT-PROPAGATION | 传播到达状态转换节点时改变状态 |
| `guarded_by` | ONT-GUARD | 状态转换可能被Guard保护 |
| `causes` | ONT-SECURITY-IMPACT | 状态转换违反不变量导致安全影响 |

## 正例

```python
# 权限状态变更——状态转换
def promote_user(user_id, new_role):
    user = User.objects.get(id=user_id)
    user.role = new_role           # 状态转换：权限状态变更
    user.save()
    # 若new_role可控且缺少Guard，攻击者可自行提权
```

```python
# 订单状态变更——状态转换
def cancel_order(order_id):
    order = Order.objects.get(id=order_id)
    if order.status != 'pending':  # Guard：状态条件检查
        raise ValueError("cannot cancel")
    order.status = 'cancelled'     # 状态转换
    order.save()
```

## 反例

```python
# 这是Sink（危险操作），不是状态转换
def execute_query(query):
    cursor.execute(query)  # SQL执行是Sink，不是状态变更
```

## 代码信号

- 状态字段赋值：`obj.status = new_value`、`obj.state = new_state`
- 角色变更：`user.role = new_role`、`user.permissions.add(...)`
- 状态机迁移：`state_machine.transition_to(new_state)`
- 会话操作：`session.login()`、`session.logout()`、`session.regenerate_token()`
- 配置修改：`config.set('security.mfa', False)`

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Django | `user.role = ...` / `order.status = ...` / `user.save()` |
| Java/Spring | `user.setRole(...)` / 状态机库迁移调用 |
| Node.js | `user.role = ...` / `user.save()` |
| Go | `user.Role = ...` / 状态字段赋值 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别状态转换缺少Guard或不变量检查的信号
- `verification-and-rating`：验证与定级能力评估状态转换是否违反状态不变量（非污点模型）
- `remediation-guidance`：修复指导能力为缺失的状态转换Guard补齐检查

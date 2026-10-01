# ONT-POLICY-DECISION：策略决策

## 定义

策略决策是授权策略的逻辑判定——根据主体属性、资源属性、动作属性和环境条件，判定主体是否有权对资源执行动作的规则评估过程。

## 包含边界

- 角色策略：基于角色的访问控制（RBAC）策略评估
- 属性策略：基于属性的访问控制（ABAC）策略评估
- 关系策略：基于主体与资源关系的策略评估（如"用户只能访问自己创建的资源"）
- 环境条件策略：基于时间、IP、设备等环境因素的策略评估
- 多租户策略：基于租户隔离规则的策略评估
- 委托策略：基于权限委托链的策略评估

## 排除边界

- Guard（ONT-GUARD）不是策略决策——Guard是授权决策的执行点（在哪里做检查），Policy Decision是策略逻辑本身（根据什么规则判定）。Guard调用Policy Decision做出判定。
- 状态条件守卫不是策略决策——状态条件守卫（如"只有pending状态才能取消"）属于Guard的一种形式，不是独立的策略决策概念。Policy Decision关注的是授权策略（Principal-Action-Resource关系），不是业务状态机。
- Sanitizer（ONT-SANITIZER）不是策略决策——Sanitizer是输入验证/净化，不是授权判定。

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `decided_by` | ONT-GUARD | Guard的决策由Policy Decision做出 |
| `receives_from` | ONT-ENTRY | Policy Decision接收来自入口的主体/动作/资源信息 |
| `causes` | ONT-SECURITY-IMPACT | 策略决策错误导致安全影响 |

## 正例

```python
# RBAC策略决策
def can_delete_post(user, post):
    if user.role == 'admin':           # 策略：管理员可以删除任何帖子
        return True
    if post.author_id == user.id:      # 策略：作者可以删除自己的帖子
        return True
    return False

# Guard调用Policy Decision
def delete_post_handler(request, post_id):
    post = get_post(post_id)
    if not can_delete_post(request.user, post):  # Guard调用Policy Decision
        raise Forbidden()
    post.delete()
```

## 反例

```python
# 这是Guard（执行点），不是Policy Decision
@login_required  # 这是Guard装饰器，是决策点的位置，不是策略逻辑
def handler(request):
    ...
```

## 代码信号

- 权限判定函数：`can_*`、`has_permission`、`is_allowed`
- 策略引擎调用：`policy_engine.evaluate(subject, action, resource)`
- 角色检查逻辑：`if user.role in allowed_roles`
- ABAC规则：基于属性的条件组合判定
- 策略配置文件：权限策略定义文件

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Django | `user.has_perm('app.action')` / Django Guardian对象级权限 |
| Java/Spring | `AccessDecisionManager` / Spring Security策略评估 |
| Casbin | 通用策略引擎，支持RBAC/ABAC |
| OPA | Rego策略语言，通用策略评估 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `candidate-discovery`：候选发现能力识别策略决策缺失或逻辑错误的信号
- `verification-and-rating`：验证与定级能力评估策略决策是否正确执行授权逻辑
- `remediation-guidance`：修复指导能力为缺失或错误的策略决策补齐逻辑

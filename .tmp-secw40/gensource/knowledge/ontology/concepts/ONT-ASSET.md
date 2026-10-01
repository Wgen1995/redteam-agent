# ONT-ASSET：资产

## 定义

资产是安全保护的对象——具有价值且需要被保护免受机密性、完整性或可用性损害的系统资源、数据或能力。

## 包含边界

- 业务数据：用户个人信息、凭证、交易记录、配置密钥
- 系统资源：计算资源、存储资源、网络带宽
- 知识产权：源码、算法、商业逻辑
- 服务可用性：在线服务的持续可达性
- 信任凭证：API密钥、JWT签名密钥、TLS证书私钥
- 品牌与信誉：作为间接资产，受损后影响业务持续

## 排除边界

- 攻击面（ONT-SURFACE）不是资产——攻击面是资产被暴露给外部交互的接口，资产是被保护的对象本身
- 入口（ONT-ENTRY）不是资产——入口是攻击面上可被外部输入触达的具体通道
- 信任边界（ONT-TRUST-BOUNDARY）不是资产——信任边界是划分资产信任级别的分界线

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `contains` | ONT-SURFACE | 资产包含暴露给外部的攻击面 |
| `crosses` | ONT-TRUST-BOUNDARY | 资产可能跨越多个信任边界 |
| `causes` | ONT-SECURITY-IMPACT | 资产受损导致安全影响 |

## 正例

```python
# 数据库中的用户凭证表是资产
users_table = {
    "user_id": 1,
    "username": "admin",
    "password_hash": "$2b$12$...",  # 需要保护的凭证
}
```

```yaml
# 配置文件中的API密钥是资产
api:
  stripe_secret_key: "sk_live_..."  # 需要保护的密钥
```

## 反例

```python
# 这是入口（ONT-ENTRY），不是资产
@app.route("/api/users/<id>")
def get_user(id):
    # id 是来自外部的输入通道，不是被保护的资产本身
    ...
```

## 代码信号

- 数据库表定义、ORM模型中的敏感字段标注
- 配置文件中的密钥、令牌、凭证字段
- 环境变量中的敏感配置
- 数据分类标注（如PII标记、密级标注）

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/Django | Django Model中的敏感字段；settings.py中的SECRET_KEY |
| Java/Spring | application.properties中的密钥；Entity类中的敏感字段 |
| Node.js | .env文件中的环境变量；Mongoose Schema中的敏感字段 |
| Go | struct中的敏感字段；os.Getenv读取的配置 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `scope-and-context`：范围与威胁语境能力识别目标代码库中的资产实例，确定审计保护对象
- `verification-and-rating`：验证与定级能力评估资产受损的实际影响
- `report-delivery`：报告交付能力按资产组织发现报告

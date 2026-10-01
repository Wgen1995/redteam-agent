# ONT-SURFACE：攻击面

## 定义

攻击面是系统暴露给外部交互的所有接口和通道的集合——外部主体可以通过攻击面与系统进行数据交换或触发执行。

## 包含边界

- Web界面：HTTP路由、页面端点
- API端点：REST/GraphQL/RPC端点
- CLI接口：命令行参数、标准输入
- 消息接口：消息队列消费者、事件订阅者
- 文件接口：文件系统监听、配置文件加载
- 网络接口：监听端口、WebSocket端点
- 插件接口：插件加载机制、扩展点
- 控制平面：管理API、运维接口
- 构建系统：CI/CD触发接口、依赖解析
- 客户端应用：桌面应用UI、浏览器扩展
- 移动应用：Activity/Fragment、 deeplink
- 嵌入式设备：串口、调试接口、OTA更新
- 智能合约：外部可调用的函数
- AI/Agent系统：用户prompt输入、工具调用接口

## 排除边界

- 入口（ONT-ENTRY）不是攻击面——入口是攻击面上的具体通道点，攻击面是入口的集合容器
- 资产（ONT-ASSET）不是攻击面——资产是被保护的对象，攻击面是暴露的接口
- 数据源（ONT-SOURCE）不是攻击面——数据源是入口上携带的外部数据的来源属性

## 关系

| 关系类型 | 目标概念 | 说明 |
|---|---|---|
| `contains` | ONT-ENTRY | 攻击面包含多个入口 |
| `crosses` | ONT-TRUST-BOUNDARY | 攻击面可能跨越信任边界 |
| `exposes` | ONT-ENTRY | 攻击面暴露入口给外部 |
| `receives_from` | ONT-ASSET | 攻击面接收自资产的暴露需求 |

## 正例

```python
# Web应用的攻击面——所有路由定义的集合
app.router.add_routes({
    "/api/users": users_handler,       # HTTP路由入口
    "/api/orders": orders_handler,     # HTTP路由入口
    "/ws/chat": websocket_handler,     # WebSocket入口
})
```

```solidity
// 智能合约的攻击面——所有external/public函数
contract Token {
    function transfer(address to, uint256 amount) public {  // 入口
    }
    function balanceOf(address owner) public view returns (uint256) {  // 入口
    }
}
```

## 反例

```python
# 这是入口（ONT-ENTRY），不是攻击面
@app.route("/api/users/<id>")
def get_user(id):
    # 这是攻击面上的一个具体通道点，不是攻击面本身
    ...
```

## 代码信号

- 路由注册：`add_routes`、`@app.route`、`router.GET`等
- 接口定义：OpenAPI/Swagger spec、GraphQL schema、Protobuf定义
- 监听声明：`listen`、`bind`、`serve`等网络监听调用
- 公开方法：Solidity的`public`/`external`函数、Java的`public`方法

## 生态映射

| 语言/框架 | 典型表现 |
|---|---|
| Python/aiohttp | `app.router.add_routes()`注册的路由集合 |
| Java/Spring | `@RestController`/`@RequestMapping`注解的端点集合 |
| Node.js/Express | `app.get()`/`app.post()`注册的路由集合 |
| Solidity | `public`/`external`修饰的合约函数集合 |
| Go | `http.HandleFunc`注册的handler集合 |

## 版本与来源

- 版本：v0.1
- 来源：安全本体与行业漏洞全集实现计划任务2；通用安全工程概念
- 变更历史：初始创建

## 消费Skill

- `scope-and-context`：范围与威胁语境能力枚举目标系统的攻击面
- `candidate-discovery`：候选发现能力在攻击面集合上执行三种发现机制

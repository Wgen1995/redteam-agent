# 攻击面类别索引（surfaces/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务3。本文件是攻击面类别索引，按统一格式记录各类攻击面。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID |
| name | 名称 |
| ontology_ref | 本体引用（ONT-SURFACE） |
| recognition_signals | 识别信号 |
| applicable_ecosystems | 适用生态 |
| related_semantics | 关联统一漏洞语义（后续任务填充） |
| source_refs | 来源引用 |
| version | 版本 |

## 类别索引表

> 类别内容不以固定条目数封版——下列覆盖已确认的系统形态，后续可按需扩展。

| stable_id | name | ontology_ref | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| SURF-WEB | Web应用攻击面 | ONT-SURFACE | HTTP路由注册、模板页面端点、静态资源服务 | Python/Django、Java/Spring、Node.js/Express、Ruby/Rails、PHP/Laravel | | 内部推导 | v0.1 |
| SURF-API | API攻击面 | ONT-SURFACE | REST/GraphQL/RPC端点定义、OpenAPI/Swagger spec、Protobuf定义 | 全语言通用 | | 内部推导 | v0.1 |
| SURF-CLI | CLI攻击面 | ONT-SURFACE | 命令行参数解析、stdin读取、环境变量读取 | Python/argparse、Java/picocli、Node.js/commander、Go/cobra | | 内部推导 | v0.1 |
| SURF-MQ | 消息队列攻击面 | ONT-SURFACE | 消息消费者注册、事件订阅、topic订阅 | Kafka/RabbitMQ/Redis Pub-Sub/NATS | | 内部推导 | v0.1 |
| SURF-FILESYSTEM | 文件系统攻击面 | ONT-SURFACE | 文件监听、配置文件加载、文件上传处理 | 全语言通用 | | 内部推导 | v0.1 |
| SURF-DATABASE | 数据库攻击面 | ONT-SURFACE | 存储过程暴露、数据库触发器、直接暴露的查询接口 | PostgreSQL/MySQL/MongoDB/Redis | | 内部推导 | v0.1 |
| SURF-PLUGIN | 插件系统攻击面 | ONT-SURFACE | 插件加载机制、扩展点注册、动态模块加载 | VS Code/Eclipse/Jenkins/WordPress | | 内部推导 | v0.1 |
| SURF-SCHEDULED-TASK | 定时任务攻击面 | ONT-SURFACE | cron作业、scheduler触发、定时任务定义 | cron/Spring Scheduled/celery/APScheduler | | 内部推导 | v0.1 |
| SURF-CONTROL-PLANE | 控制平面攻击面 | ONT-SURFACE | 管理API、运维接口、Kubernetes API server、配置管理接口 | Kubernetes/Consul/etcd/ZooKeeper | | 内部推导 | v0.1 |
| SURF-BUILD-SYSTEM | 构建系统攻击面 | ONT-SURFACE | CI/CD pipeline定义、依赖解析、构建脚本触发 | GitHub Actions/GitLab CI/Jenkins/Make | | 内部推导 | v0.1 |
| SURF-CLIENT-APP | 客户端应用攻击面 | ONT-SURFACE | 桌面应用UI、浏览器扩展、Electron应用 | Electron/Tauri/Qt/WPF | | 内部推导 | v0.1 |
| SURF-MOBILE | 移动应用攻击面 | ONT-SURFACE | Activity/Fragment、deeplink、URL scheme、intent filter | Android/iOS/React Native/Flutter | | 内部推导 | v0.1 |
| SURF-EMBEDDED | 嵌入式设备攻击面 | ONT-SURFACE | 串口、调试接口(JTAG/SWD)、OTA更新、网络服务 | RTOS/Arduino/ESP32/Linux嵌入式 | | 内部推导 | v0.1 |
| SURF-SMART-CONTRACT | 智能合约攻击面 | ONT-SURFACE | external/public函数、fallback函数、事件暴露 | Solidity/Vyper/Rust(Solana) | | 内部推导 | v0.1 |
| SURF-AI-AGENT | AI/Agent系统攻击面 | ONT-SURFACE | prompt输入接口、工具调用接口、模型API端点、RAG检索接口 | OpenAI API/LangChain/AutoGPT/CrewAI | | 内部推导 | v0.1 |

## 消费方

- `scope-and-context`：范围与威胁语境能力枚举目标系统的攻击面类别
- `candidate-discovery`：候选发现能力在攻击面类别上执行三种发现机制

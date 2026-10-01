# 入口类别索引（entries/_index.md）

> 来源：docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md（安全本体与行业漏洞全集实现计划）任务3；docs/research/28-detection-engine-design.md §9 知识层配套（双轨索引补全）。本文件是入口类别索引，按 13 个入口通道（rest/rpc/mq/ws/graphql/cron/cli/script/deser/file/webservice/custom_proto/event）记录识别信号、正例反例与 0 命中处理。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID（ONT-ENTRY） |
| channel | 通道简称（rest/rpc/mq/ws/graphql/cron/cli/script/deser/file/webservice/custom_proto/event） |
| name | 名称 |
| recognition_signals | 跨语言识别信号（Py=Python / J=Java / N=Node.js / PHP=PHP / Go=Go 的 grep 模式；双兼容 ERE 子集，不用词边界转义） |
| applicable_ecosystems | 适用生态 |
| related_semantics | 关联统一漏洞语义/入口本体 |
| source_refs | 来源引用 |
| version | 版本 |

## 类别索引表（13 通道）

| stable_id | channel | name | recognition_signals | applicable_ecosystems | related_semantics | source_refs | version |
|---|---|---|---|---|---|---|---|
| ENTRY-REST | rest | REST/HTTP路由 | Py: @app.route( / @router.get( · J: @GetMapping / @PostMapping / @RequestMapping · N: app.get( / router.get( / app.post( · PHP: Route:: / $app->get( · Go: http.HandleFunc( / r.Get( / r.Handle( | Flask/Django/FastAPI、Spring、Express、Laravel、net/http、gin | 路由 → Sink（A01/A03/A10 等） | 内部推导 | v0.2 |
| ENTRY-RPC | rpc | RPC handler | Py: grpc.server / @grpc · J: @RpcMethod / ServiceImpl · N: addService / grpc.loadPackageDefinition · PHP: 少见(gRPC扩展) · Go: RegisterXxxServer / pb.Register · proto 定义 service/rpc | gRPC、Thrift、JSON-RPC、Dubbo | RPC方法 → Sink | 内部推导 | v0.2 |
| ENTRY-MQ | mq | 消息消费者 | Py: @KafkaListener / consumer.subscribe / channel.basic_consume · J: @RabbitListener / @KafkaListener · N: consumer.consume / amqp.consume · PHP: ->basic_consume( · Go: kafka.NewConsumer / amqp.Consume | Kafka、RabbitMQ、Redis Stream、SQS | 消息体 → Sink | 内部推导 | v0.2 |
| ENTRY-WS | ws | WebSocket handler | Py: @app.websocket( / websockets.serve( · J: @OnMessage / @ServerEndpoint · N: ws.on(message / socket.on( · PHP: Ratchet MessageComponent · Go: websocket.Upgrade / gorilla/websocket | Socket.IO、ws、aiohttp WebSocket、JSR-356、gorilla | WS消息 → Sink（含 Origin 校验） | 内部推导 | v0.2 |
| ENTRY-GRAPHQL | graphql | GraphQL resolver | Py: graphene / strawberry / graphql-core · J: graphql-java / @DgsComponent · N: typeDefs / resolvers / graphql-yoga · PHP: webonyx/graphql-php · Go: gqlgen / graphql-go | Apollo、gqlgen、graphene、graphql-java | resolver → Sink（批处理/深度/授权） | 内部推导 | v0.2 |
| ENTRY-CRON | cron | 定时任务触发 | Py: @app.task / APScheduler / croniter · J: @Scheduled( · N: cron.schedule( / node-cron · PHP: cron 脚本 / Laravel schedule · Go: cron.New( / robfig/cron | celery、APScheduler、Spring @Scheduled、node-cron、cron | 定时任务体 → Sink（配置/权限） | 内部推导 | v0.2 |
| ENTRY-CLI | cli | CLI参数 | Py: argparse / sys.argv · J: main(String[] args) · N: process.argv / yargs · PHP: $argv / getopt( · Go: os.Args / flag.Parse( | 全语言 CLI | CLI参数 → Sink | 内部推导 | v0.2 |
| ENTRY-SCRIPT | script | 脚本执行入口 | Py: if __name__ == __main__ / #! 行 · J: public static void main( · N: #!/usr/bin/env node / IIFE · PHP: #!/usr/bin/php · Go: package main + func main() | 全语言脚本 | 脚本体 → Sink | 内部推导 | v0.2 |
| ENTRY-DESER | deser | 反序列化入口 | Py: pickle.loads( / yaml.load( / json.loads( · J: ObjectInputStream.readObject / readValue( · N: JSON.parse( / unserialize 库 · PHP: unserialize( · Go: json.Unmarshal( / gob.NewDecoder | 全语言（原生序列化） | 反序列化字节流 → Sink（CWE-502） | 内部推导 | v0.2 |
| ENTRY-FILE | file | 文件解析器 | Py: open( / xml.etree / yaml.safe_load · J: FileInputStream / DocumentBuilder / new File( · N: fs.readFile( / multer · PHP: file_get_contents / simplexml_load · Go: os.ReadFile( / json.NewDecoder | 全语言文件处理 | 文件内容 → Sink（上传/解析/路径） | 内部推导 | v0.2 |
| ENTRY-WEBSERVICE | webservice | Web服务/SOAP | J: @WebService / JAX-WS / WSDL · PHP: SoapServer / soap · N: soap 库 · Py: zeep(客户端)/spyne · Go: 少见 | SOAP/WSDL、XML-RPC | SOAP操作 → Sink（注入/XXE） | 内部推导 | v0.2 |
| ENTRY-CUSTOM-PROTO | custom_proto | 自定义协议 | Py: socket.socket / asyncio.start_server · J: ServerSocket / Netty · N: net.createServer · PHP: stream_socket_server · Go: net.Listen( / net.PacketConn | 自定义 TCP/UDP、私有二进制协议 | 协议报文 → Sink（解析/长度字段） | 内部推导 | v0.2 |
| ENTRY-EVENT | event | 事件回调 | Py: signals / @receiver / blinker · J: @EventListener / EventBus · N: emitter.on( / addEventListener · PHP: Event::listen( · Go: channel / goroutine 订阅 | EventEmitter、Spring EventBus、blinker、Laravel Event | 事件载荷 → Sink | 内部推导 | v0.2 |

## 各通道正例 / 反例 / 0 命中处理

### ENTRY-REST（rest）
- 正例：Py @app.route(/transfer, methods=[POST])；J @PostMapping(/transfer)；N app.post(/transfer, h)；PHP Route::post(/transfer,...)；Go r.POST(/transfer, h)
- 反例：纯内部函数 def helper() 无路由装饰器；被其他路由内部调用的服务方法（不是入口）
- 0 命中处理：技术栈探测确认无 Web 框架（纯 CLI/库项目）→ 在 entry inventory 显式登记 ENTRY-REST=0 命中并注明依据；不得跳过不查，不得把未查记成 0 命中

### ENTRY-RPC（rpc）
- 正例：proto 定义 service TransferService { rpc Transfer(Req) returns (Resp); }；Go RegisterTransferServiceServer(s, impl)
- 反例：进程内普通函数调用；仅 import 了 grpc 包但未定义 service
- 0 命中处理：无 .proto / thrift / IDL 文件且无 RPC 框架注册 → ENTRY-RPC=0 命中；若存在 proto 但未生成 server stub，登记为 ENTRY-RPC=部分（proto 存在、handler 缺失）

### ENTRY-MQ（mq）
- 正例：Py @app.task(消费队列)；J @RabbitListener(queues=...)；N consumer.consume(...)；PHP ->basic_consume(...)；Go kafka.NewConsumer(...)
- 反例：仅发送消息的生产者代码（producer 不是入口）；本地内存队列
- 0 命中处理：无 MQ 客户端库依赖且无消费者注册 → ENTRY-MQ=0 命中；仅生产者则登记 ENTRY-MQ=0（无消费入口）并注明

### ENTRY-WS（ws）
- 正例：Py @app.websocket(/ws)；J @OnMessage；N ws.on(message,...)；PHP Ratchet onMessage；Go websocket.Upgrade(...)
- 反例：HTTP 普通长轮询接口；客户端 WS 连接代码（不是服务端入口）
- 0 命中处理：无 WS 服务端库/升级处理 → ENTRY-WS=0 命中；注意 WS 入口还需额外核对 Origin 校验（CSRF/跨域面）

### ENTRY-GRAPHQL（graphql）
- 正例：N typeDefs + resolvers；Py graphene.Schema + Query；Go gqlgen Resolver 实现
- 反例：普通 REST 端点（虽返回 JSON 但不是 GraphQL）；仅 import graphql 库未定义 schema
- 0 命中处理：无 schema/resolver 定义 → ENTRY-GRAPHQL=0 命中；命中时需额外评估批处理攻击（batching）、查询深度与授权粒度

### ENTRY-CRON（cron）
- 正例：J @Scheduled(cron=...)；N cron.schedule(*/5 * * * *, fn)；Py APScheduler add_job(...trigger=cron...)；Go c := cron.New()
- 反例：用户请求触发的普通函数（不是定时）；手动执行的一次性脚本
- 0 命中处理：无调度器依赖与 cron 表达式 → ENTRY-CRON=0 命中；命中时定时任务体按独立入口做 Source 分析（其输入常来自配置/文件而非用户）

### ENTRY-CLI（cli）
- 正例：Py argparse.ArgumentParser / sys.argv；J main(String[] args)；N process.argv；PHP $argv；Go flag.Parse()
- 反例：硬编码常量（无参数输入）；Web 请求参数（那不是 CLI）
- 0 命中处理：纯库/服务项目无 CLI 入口 → ENTRY-CLI=0 命中；存在 main 入口但无参数解析则登记 ENTRY-CLI=部分

### ENTRY-SCRIPT（script）
- 正例：Py if __name__ == __main__: 入口；N #!/usr/bin/env node + 顶层执行；Go package main + func main()
- 反例：被 import 的模块/库（无自执行入口）；测试文件（属于开发辅助，不在攻击面）
- 0 命中处理：纯库无自执行入口 → ENTRY-SCRIPT=0 命中；脚本入口的输入来自环境变量/文件/stdin，逐项登记 Source

### ENTRY-DESER（deser）
- 正例：Py pickle.loads(data)；J ObjectInputStream.readObject()；PHP unserialize($_GET[x])；Go json.Unmarshal(body, &v)
- 反例：序列化（写）操作 pickle.dumps / writeObject（不是入口）；对固定 schema 的纯数据 JSON 解析且无对象还原
- 0 命中处理：无任何反序列化/解析调用 → ENTRY-DESER=0 命中；存在 JSON 解析也须登记（即使纯数据 JSON 也要评估是否可达危险 Sink）

### ENTRY-FILE（file）
- 正例：Py open(user_path)；J new File(user_path)；N fs.readFile(user_path)；PHP file_get_contents(user_file)；Go os.ReadFile(user_path)
- 反例：读取硬编码路径的配置文件（非用户可控文件名）；仅写日志到固定路径
- 0 命中处理：无文件读取/解析 → ENTRY-FILE=0 命中；命中时文件上传（CWE-434）与文件解析（XXE/路径穿越）分别登记

### ENTRY-WEBSERVICE（webservice）
- 正例：J @WebService + WSDL；PHP SoapServer；N soap 服务端
- 反例：普通 REST JSON 接口（不是 SOAP/XML-RPC）；仅调用外部 SOAP 的客户端
- 0 命中处理：无 WSDL/SOAP/XML-RPC 定义 → ENTRY-WEBSERVICE=0 命中；命中时 SOAP 消息体按 XML 入口评估 XXE/注入

### ENTRY-CUSTOM-PROTO（custom_proto）
- 正例：Go net.Listen(tcp, :9000) + 自解析报文；Py socket.socket + recv；N net.createServer；J Netty pipeline
- 反例：仅作为 HTTP 服务监听（那是 rest）；标准协议客户端（不是服务端入口）
- 0 命中处理：无自定义 socket 监听/私有协议解析 → ENTRY-CUSTOM-PROTO=0 命中；命中时协议长度字段/解析边界作为 Source，需重点核对 CWE-787/190 等内存安全

### ENTRY-EVENT（event）
- 正例：N emitter.on(data, fn)；J @EventListener；Py @receiver(signal)；PHP Event::listen(...)
- 反例：同步直接调用（非事件分发）；仅定义事件类但无监听注册
- 0 命中处理：无事件总线/EventEmitter 监听注册 → ENTRY-EVENT=0 命中；命中时事件载荷来源（用户/系统/外部）逐项登记 Source

## 消费方

- scope-and-context：范围与威胁语境能力枚举攻击面上的入口实例，按 13 通道逐项登记（0 命中也要显式登记）
- candidate-discovery：候选发现能力对每个入口点执行模式驱动发现，入口识别信号只做预筛，命中后仍需对应 vuln-patterns 条目支撑
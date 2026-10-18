# ssrf ｜ 服务端请求伪造（CWE-918）

> band: 0 ｜ 模式表: `patterns/ssrf-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/ssrf/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 互斥归属（D-010）: 本类只收「服务端发起请求的 URL/主机可控」；JNDI lookup 的出网本质归本类出网面、载荷类型实例化（gadget）归 deser；重定向响应头归 open-redirect。
> 定级阶梯: 可打云 metadata（169.254.169.254）/file:// 本地读/gopher:// 打内网 TCP/内网管理面 → Critical–High；host 全控可探内网端口且响应回显 → High；盲探（仅状态/时间差）→ Medium；仅同源图片代理、host 固定仅 path 可控、且 redirect 受控 → 中低（前提引文）

## ① 定义与危害
服务端按攻击者可影响的 URL 发起请求：内网穿透（端口扫描/管理面直达）、云 metadata 凭据窃取（AWS IMDS/GCP metadata.google.internal）、scheme 滥用（file:// 读本地文件、gopher:// 伪造内网 TCP 协议）、经服务器身份绕过 IP 白名单（"trusted server" 反弹）。

## ② Source
HTTP 参数/路径/头部/_body_、消息体（external_message——webhook/callback 指令）、**存储回读（persisted_read——二阶 SSRF：注册期写入的 webhook/回调 URL 由后台 worker 延迟回读再 fetch）**、可被 API 写入的 endpoint 配置值。DB/注册表回读的 URL 默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/ssrf-java.pattern` / `ssrf-ts.pattern` / `ssrf-python.pattern`（机器直读，逐行一条，不并串）。

## ④ Propagator
字符串拼接进 URL（`+`/模板串/f-string/`format`）、StringBuilder.append 链、URI builder 的 scheme/host/path/query 段赋值、常量前缀+用户后缀（`"https://api." + sub` 子域植入）、**变量重赋值链（校验用变量 A、请求用变量 B 的 TOCTOU 替换）**。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
固定 host 白名单且比较对象是**解析后的最终 host（scheme+host）** → **强**；解析 IP 后钉住连接（resolve-then-connect pin，校验与连接同一解析结果）→ **强**；deny 黑名单/`startsWith/endsWith` 前缀匹配 → **弱**（@ 混淆/十进制 IP/子串绕过）；网段黑名单（127/8、169.254/16、10/8、172.16/12、192.168/16）→ **弱**（DNS rebinding、redirect 后失效、IPv6 映射漏网）；`followRedirects(false)`/`allow_redirects=False` → **上下文条件（只封 redirect 向量，不封直连 host 控制；只产 hint，禁 kills）**；host 白名单但未钉 scheme → **弱**（file://、gopher://）；`if(config.strict)` 才校验 → 显式挂 `requires_config`。**多段净化看全部：白名单通过但 redirect 后不重评价 = 净化与载荷形态不匹配。**

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（URL 参数/回调地址/消息体字段/回读）？｜引用:入口签名与取参行｜推翻:实参为编译期常量｜反向:配置开关写入的动态 URL
C2 目标 URL 的哪些部分可控——host/scheme 全控 vs 仅 path？｜引用:URL 构造行±3行与拼接变量语法位置｜推翻:host 为编译期常量且拼接仅在常量 host 之后的 path/query 段｜反向:常量域名后拼用户子域、或用户串拼进 scheme/host 位置
C3 最近的 allow/deny/filter 控制是否真的约束 host？｜引用:校验调用行+其比较基准（对什么变量、与什么集合比）｜推翻:对解析后 host 与固定白名单强匹配、且比较发生在最终请求的 URL 上｜反向:校验的是原始参数而请求的是另一变量/另一构造点（TOCTOU）、或仅 endsWith 前缀匹配
C4 redirect 后是否重评价（followRedirects 默认开启即二次请求不受 C3 约束）？｜引用:重定向配置行（followRedirects/allow_redirects/instanceFollowRedirects）与跳转处理循环｜推翻:显式禁用重定向或逐跳重跑 C3 白名单｜反向:白名单只在首请求检查、302 目标直取 Location
C5 解析与请求是否同一变量同一时刻（DNS rebinding 双解析窗口）？｜引用:校验解析点与连接点之间的变量链与时间差｜推翻:resolve-then-connect 钉住同一 IP/连接层禁再解析｜反向:校验 getHost 与后续 openConnection 各自独立解析
C6 目标可达内网/metadata 网段（169.254.169.254/127.0.0.1/10.x/172.16-31/192.168/[::ffff:7f00:1]）？｜引用:部署网络位置与目标网段证据（云平台/出口策略）｜推翻:出口仅经公网代理且目的白名单在网络层强制｜反向:云环境且无 IMDSv2 强制、无 egress 隔离
C7 入口可达且鉴权不拦截？｜引用:路由注解/拦截器配置｜推翻:内网-only 且有边界证据｜反向:默认放行配置（webhook 注册等公开端点）
C8 响应是否回显（full vs blind 定级输入）？｜引用:响应处理与返回构造行｜推翻:响应体丢弃仅返回固定文案/布尔｜反向:body/头直接回写客户端（full read SSRF 升档）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 内网固定常量 URL 巡检/健康检查（host 编译期常量不可控）——需 OBS 到常量定义与取参链反证。
FP-2 健康检查白名单/endpoint 注册表（host 集合服务端固定枚举）——需 OBS 到白名单数据来源。
FP-3 仅 path 可控、host 固定的同源图片代理——需 C2 反证引文（拼接位置在常量 host 之后且无 scheme 注入）。
FP-4 URL 仅用于解析/比较/展示（equals/startsWith/规范化/hash）无外发 sink——需 sink 缺席证据（对照 §③ 表）。
FP-5 业务 302/forward 到固定相对路径（ResponseEntity Location 为常量、RequestDispatcher 转发）——客户端侧导航，非服务端发起外发。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 十进制/八进制/十六进制 IP：169.254.169.254 → 2852039166、0xA9FEA9FE、0177.0.0.1（黑名单按点分字符串匹配时全过）。
B2 DNS rebinding：校验时解析到合法 A，连接时再解析到 127.0.0.1/169.254.169.254（两次解析窗口，见 C5）。
B3 302 链：白名单域上的开放重定向/短链/已沦陷域 → Location 跳内网；followRedirects 默认开启即二次请求绕过 C3。
B4 云 metadata：AWS `http://169.254.169.254/latest/meta-data/iam/security-credentials/`（试 IMDSv2 token 是否强制）；GCP `http://metadata.google.internal/computeMetadata/v1/`（需 Metadata-Flavor 头时试 SSRF 头注入）；Azure 168.63.129.16。
B5 file:// 直读本地文件（/etc/passwd、应用配置、密钥）——deny 只查 host 不查 scheme 时直达。
B6 gopher:// 打内网 TCP（Redis 未授权/SMTP/FastCGI），dict:// 探端口指纹。
B7 IPv6 映射与省略形式：`[::ffff:169.254.169.254]`、`[::ffff:7f00:1]`、`127.1`、`0`。
B8 @ userinfo 混淆：`http://allowlisted.com@169.254.169.254/`——解析后 host 在 @ 之后；配合 `endsWith("allowlisted.com")` 类校验双杀。
B9 redirect 逐跳变形：302 目标再 302（链式）、跳转响应中 CRLF/头注入改写 Host、30x 到 rare scheme。
B10 拼接变形进 host 位：常量前缀 `https://api.` + 用户串（`api.evil.com`）、双斜杠 `//internal/`、大小写 scheme（`hTtP://`）、反斜杠变体、URL 编码绕 `startsWith("http://")`。

## ⑨ 利用前提与定级阶梯
见页首；Critical/High 验收：专业审查者无需长篇推测即可接受"打 metadata/内网管理面/读文件"的完整路径（含 redirect 与 scheme 证据链）。Medium 以下必须有 C2/C3 反证引文。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 目标域名白名单引文在位或环境无出网路径（部署拓扑证据）→ 降 medium 以下

## ⑩ 根因修复
目的地白名单作用于**最终生效 URL**（含 redirect 逐跳重评价）；resolve-then-connect 钉 IP；scheme 白名单 http/https；禁重定向或重定向目的地同白名单；网络层 egress 隔离 + IMDSv2 强制；webhook/回调注册表人工审核 + 注册域与 fetch 域分离。

## ⑪ 跨边界提示
Egress 侧持久化 webhook 由后台 worker 延迟 fetch（二阶，追 persisted_read）；消息队列/任务体携带 fetch 指令跨服务执行；redirect 链跨信任边界（每跳独立重评价）。Ingress 侧第三方回调 URL 注册入口（C1 的 primary source）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 16/21/6、python 10/11/5、ts 8/10/4
`fixtures/enum/ssrf/{lang}/manifest.tsv`（java 全量：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集 ≥6/≥8/≥3——见 classes/fixture-spec.md 三类语义）。

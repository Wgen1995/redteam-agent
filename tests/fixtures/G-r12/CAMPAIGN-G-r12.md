# battle-11 G-r12 战役档案（2026-10-08 场景钟）

## 九门
P0 09:06 PASS → P1 09:18 PASS → P2 09:21 PASS(矩阵108格冻结) → P3 10:42 PASS(converged,gaps 0/0) → P4 11:50 PASS(hash-recheck ev_checked=32 全绿)

## 战果：24 findings（13高/10中/1低），31 EV 全部容器内重放 VERIFIED
| # | 面 | 类 | 标记 | 携带 |
|---|---|---|---|---|
| FD-0001 | shop /item?id= | SQLi报错 | GTSQLI-01 | 匿名 |
| FD-0002 | shop /order?id=(+/orders/1 双形) | SQLi报错 | GTSQLI-02 | 匿名 |
| FD-0003 | shop /search?q= | 反射XSS | GTXSS-01 | 匿名 |
| FD-0004 | shop /reply?body= | 反射XSS | GTXSS-03 | 匿名 |
| FD-0005 | shop /feedback?msg= | 反射XSS | GTXSS-04 | 匿名 |
| FD-0006 | gw /preview?url= | SSRF | GTSSRF-02 | 匿名 |
| FD-0007 | gw /graphql | GraphQL内省 | GTGRAPHQL-01 | 匿名 |
| FD-0008 | gw /cors-debug | CORS通配源(配置缺陷) | GTCORS-01 | 匿名 |
| FD-0009 | gw /origin | CORS源反射+凭据 | GTCORS-02 | 匿名 |
| FD-0010 | dash /render?tpl= | SSTI | GTSSTI-02 | 匿名 |
| FD-0011 | portal /debug/env | 信息暴露 | GTINFOLEAK-01 | 匿名 |
| FD-0012 | files /.env | 信息暴露 | GTINFOLEAK-03 | 匿名 |
| FD-0013 | files /unserialize | 反序列化pickle | GTDESER-01 | 匿名 |
| FD-0014 | files /import | 反序列化java | GTDESER-02 | 匿名 |
| FD-0015 | files /decode | 反序列化base64 | GTDESER-03 | 匿名 |
| FD-0016 | shop /logout?next= | 开放重定向 | GTREDIR-02 | 匿名 |
| FD-0017 | portal /redirect?to=(+goto) | 开放重定向 | GTREDIR-01 | 匿名 |
| FD-0018 | login /login 弱口令 admin/admin123 | 弱口令 | GTWEAKPASS-01 | 表单 |
| FD-0019 | login /login 连击无锁定 | 限流缺失 | GTRATE-01 | 表单 |
| FD-0020 | shop /admin/reports | IDOR他人报表 | GTIDOR-06 | X-Auth-Token |
| FD-0021 | gw /admin/keys | IDOR密钥清单 | GTIDOR-05 | X-Auth-Token |
| FD-0022 | dash /admin/config | 缺访问控制 | GTROLE-03 | X-Auth-Token |
| FD-0023 | portal /admin/clients | 缺访问控制 | GTHAUTH-05 | X-Auth-Token |
| FD-0024 | files /admin/logs | 缺访问控制 | GTROLE-04 | X-Auth-Token |

## 律23 持证重扫清单（8服务×8子名词，完成度 64/64 格记账）
命中5（上表20-24），401格17（svc-admin/svc-billing全拒+真面匿名401），404格41，catch-all 1服务（svc-login 8名词全吞）。
携带形态判定：X-Auth-Token 唯一有效（发放响应头名，律19/19呼应），Bearer/Cookie 全 401。

## 凭据
CRED-r12-0001 static-cred 低权-user级(admin@svc-login，弱口令)；CRED-r12-0002 session tok-usr-001(parent=0001，发放响应头采集)。

## honest_misses（没打出来的+归因，猜测标注）
1. svc-admin/svc-billing admin级世界：user令牌+alg=none JWT 全401——缺admin级凭据（猜测存在 tok-adm-* 通道，未证）。
2. gw /jump 三击挂起：7参数×5值形 302 Location 恒自路径（猜测需特定头/POST/精确值形；GTREDIR-03 标记在但行为未破）。
3. svc-login catch-all 200 零熵墙：/admin 子名词族无差分可证（归因：单handler吞路径）。
4. /comment GTXSS-02 存储型通道未验证：GET 4键名反射未中、POST 501（三击挂起，猜测需特定入口）。
5. deser 未构成利用链：合成环境GET直取即弹，POST形态分型仅 /import 400 一发（律20后半未深走）。
6. HS256 弱密钥爆破、GraphQL mutation、XXE：无通道/无入口，未做。

## 账面瑕疵自报
- EV-r12-0002 raw_excerpt 含 {{vault}} 占位符违反列白名单（redact-scan FAIL leaks=1；追加账不可改，内容非真值）。
- EV-r12-0022 artifact 曾被脚本重跑覆写致哈希失配——已按 drive1 原结构字节级还原，hash-recheck PASS。
- scope S-0013~0023 与预置 S-0001~0012 重复（会话预初始化后追加，无害冗余）。
- 演练五连弃弹账：G-r12/drill/（G-drill-0001，独立账本，FD-drill-0001 ruled_out）。

## 读取路径
必读战书+允许面：cli/源码、contracts/02a、contracts/06、docs/design/2026-09-27-endpoint-dict-v2.md、phases/phases.yaml、knowledge/ 仅列举。禁读面零触碰（tests/、HANDOFF、其他战记、/tmp 战场其他文件）。

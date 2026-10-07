# battle-18 G-r19 战报（P0-P4 全链）

## 战果总览
- 42/42 EV 容器内盲重放 reproduced → 全 VERIFIED（replay-summary: verified=42 repaired=0 rejected=0 pending=0）
- 33 findings（32 active + 1 superseded 合并行），全部 C2/verified、信标串入卡（律 29：GTxxx-NN 特异信标/计数器形）
- 校验五连 PASS：validate / verify-chain(296 行) / hash-recheck(42/0) / matrix-audit(73/0) / replay-summary
- 门序：P0→P1→P2(matrix 24 行冻结)→P3(converged)→P4 PASS；全程场景钟 2026-10-15

## finding 清单（信标）
svc-login：CWE-521 弱口令 admin/admin123（GTWEAKPASS-01，X-Auth-Token 直发 user 级令牌）｜CWE-307 认证面无限流（GTRATE-01 计数器 18→26 递增）
svc-shop：CWE-89 SQLi /item(GTSQLI-01) /order /orders(GTSQLI-02)｜CWE-79 XSS /search(GTXSS-01) /comment(GTXSS-02) /feedback(GTXSS-04)｜CWE-639 低权报表(GTIDOR-06)｜CWE-601 /logout?next= 开放重定向(GTREDIR-02)
svc-api-gw：CWE-918 SSRF /fetch(GTSSRF-01) /preview(GTSSRF-02) /proxy(GTSSRF-03)｜CWE-942 CORS /cors-debug(GTCORS-01) /origin(GTCORS-02)｜CWE-639 低权密钥(GTIDOR-05)｜CWE-601 /jump?u= 外域(GTREDIR-03)｜CWE-200 GraphQL 内省(GTGRAPHQL-01)
svc-dashboard：CWE-862 低权配置(GTROLE-03)｜/render 面级信标(GTSSTI-02)+CWE-79 反射修正（未编码回显归 XSS，FD-17 卡内类目修正注记）
svc-portal：CWE-862 低权客户(GTHAUTH-05)｜CWE-200 /debug/env(GTINFOLEAK-01)｜CWE-601 /redirect?to=+goto 外域(GTREDIR-01)
svc-files：CWE-200 /.env(GTINFOLEAK-03)｜CWE-862 低权日志(GTROLE-04)｜CWE-502 三面 /unserialize(pickle)/import(java)/decode(base64)(GTDESER-01/02/03)｜CWE-22 穿越 /download(root:x:0:0) /static(shadow)(GTTRAVERSAL-01/02)
svc-billing：CWE-639 /invoice/1+/invoice/88 双序数越权读(GTIDOR-04；query 形 404 双形差分)

## 关键打法实证
- 律 19：发放响应头 X-Auth-Token=携带形态第一候选（Bearer 401 vs X-Auth-Token 过墙 401→404/200）
- 律 23：billing 401 墙下子名词族不够，资源面 path 形 /invoice/{n} 才是入口（query 形全 404）
- 律 5/27：gw 限流墙 31 发 429+Retry-After:3 实证；login 面对照 9 连发零退避 → CWE-307
- 字典同族双面：shop /logout 仅认 next、portal /redirect 认 to+goto、gw /jump 仅认 u（逐服务取形）

## honest_misses
1. 管理级令牌未获（svc-admin/svc-billing 全字典面 401 墙）——tok-adm-001/tok-admin-001 名形猜测 401；无 issue face 可换 admin 级。归因：管理面令牌可能需面外通道（猜测，未验证）。
2. JWT 验签面/CSRF 表单/XXE XML 面零发现——Authorization 头全服务被忽略、无表单/无 XML 端点。归因：本轮靶面集未覆盖该三类（事实性缺席，非探测缺失：字典族已扫）。
3. svc-admin /admin/<noun> 持证全 404——user 级令牌过认证但资源隐藏；admin 级资源面实情未知（挂 INT-r19-0009）。

## 读取路径自报
允许面：BRIEF-G-r19.md；docs/design/2026-09-27-endpoint-dict-v2.md；phases/phases.yaml；cli/ 源码（registry/write_cmds/query_cmds/check_cmds/cards/matchers/matrix_init/vault/phases_engine/graph_cmds/special/tanyin-replay/tanyin-phases 头部）。未读：tests/ 全部、docs/HANDOFF.md、docs/design/ 战记、/tmp/tanyin-range-battle/ 下除战书外任何文件（attrib/、boot-g-r19.py、settle.py 未触碰）。账本经 CLI 读写；session 内自产 evidence/artifacts 文件由记账器写入。

## 三条最痛教训
1. bash 老版本+模板转义双层陷阱：bash 3.2 无 declare -A、未加引号的分号截断命令、JS 模板串吞 ${}——三处脚本 bug 全在记账驱动层，探测本体零失误。装备先行单测（驱动样例先行律 29 在记账侧同样成立）。
2. CLI 隐式契约必须先读源码再写量：--goal-dir 位置固定、_mv 分隔符是分号、mint 行 reason 前缀锁 submatrix:、卡片 YAML seq 续键须与 dash 同列——四处全靠 REJECT 回读源码纠正，量产前单枚样例全链验证（本战样例先行救了 42 卡批量）。
3. 对照卡与主卡同一张网：4 张匿名对照卡 Host 端口硬编码 8001 致 env-diff——负样本工程与正样本同权重的 P4 资产；REPAIRED 通道（修卡重放）实测可用且 max_retry=2 足够。
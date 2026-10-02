# battle-10 G-r11 战报（独立红队 · 场景钟 2026-10-07）

## 一、记账统计
- goals 1（boot 预置）；scope 26 行（include×12 exclude×2 oob×2 account-grant×2 + 战士补行）；assets 32（root-domain 1 + service 8 + endpoint 23）；edges 127
- intents 5 枚（recon/surface/deep-dive×2/authz-diff，全部 done）；facts 35（全部消费，含 1 枚 no-consume 缺席——0 未消费）
- creds 2：CRED-r11-0001 static-cred role=admin（弱口令 admin/admin123）；CRED-r11-0002 session role=**user**（发放响应头 X-Auth-Token，名形 tok-usr-001=usr 类；登录账号是 admin 仍记 user 级——律 22）
- findings 24：演习弹 1（ruled_out）+ 实战 23 = verified 13 / suspected 11 + 演习 1... 精确：verified 13、suspected 11、ruled_out 1（合计 24）
- matrix 384 格（基线 8 服务×12 + root 面子矩阵 12 + 23 个 finding 面子矩阵 276），state 全非空：x=攻击面证实格、-=探过/不适用格；锚点冻结 ✓
- EV 34（含 2 枚 vault 回注凭据 EV：{{vault:cred-1}} 弱口令、{{vault:cred-2}} 令牌）；timeline 372 行，verify-chain PASS

## 二、replay 汇总（P4 独立重放门，容器内盲重放）
- reproduced/VERIFIED：32（wave-A 9 + 演习 1 + P4 批 22）＝全量无遗漏
- not-reproduced/REJECTED：0；env-diff/REPAIRED：0；manual：0
- ledger-replay-summary：PASS verified=32 repaired=0 rejected=0 pending=0
- P4 四校验：validate PASS / verify-chain PASS（gate_exit=4：P0-P3）/ hash-recheck PASS（34 EV）/ matrix-audit PASS（69 抽样 0 告警）/ terminal-gate PASS（空格=0）
- 九门：P0/P1/P2/P3/P4 gate 全 PASS（tanyin-phases gate 实跑）

## 三、战果面（23 实战 finding）
verified（13）：
1. svc-portal /redirect?to= 开放重定向 302→evil.example（GTREDIR-01, CWE-601, 中）
2. svc-shop /logout?next= 开放重定向（GTREDIR-02, CWE-601, 中）
3. svc-portal /debug/env 环境变量泄露（GTINFOLEAK-01, CWE-200, 中）
4. svc-files /.env 密钥文件泄露（GTINFOLEAK-03, CWE-200, 中）
5. svc-files /download?file= 路径穿越（GTTRAVERSAL-01, CWE-22, 中）
6. svc-login /login 弱口令 admin/admin123（GTWEAKPASS-01, CWE-521, 高）——键名叉乘实测：唯 user=+pass= 短拼写收
7. svc-login /login 无速率限制仅计数器（GTRATE-01, CWE-307, 高）——95 连击全处理
8. svc-api-gw /cors-debug 通配 ACAO（GTCORS-01, CWE-942, 低，配置缺陷类）
9. svc-api-gw /origin 反射任意 Origin+credentials true（GTCORS-02, CWE-942, 高）
10. svc-files /admin/logs user 级令牌越权可达（GTROLE-04, CWE-285, 中，匿名对照 401）
11. svc-dashboard /admin/config user 级令牌越权可达（GTROLE-03, CWE-285, 中）
12. svc-portal /admin/clients user 级令牌越权客户清单（GTHAUTH-05, CWE-285, 中）
13. svc-admin+svc-billing 跨服务令牌信任（401→404 翻转, CWE-287, 低）
suspected（11）：deser×3（GTDESER-01/02/03，GET 直取弹，POST 全 400）、graphql 内省（GTGRAPHQL-01）、xss 反射（GTXSS-04）/存储（GTXSS-02）、sqli 双面（GTSQLI-01/02，orders 律 18 双形双 EV）、ssrf（GTSSRF-02）、ssti（GTSSTI-02）——全部 marker 召回但无载荷差分/执行确认，按批次 10 勘误不虚报 verified

## 四、honest_misses（没打出什么+归因；猜测已标注）
1. JWT 类（律 3 构造形）：全部服务拒 Bearer（401/404），无 JWT 验签面可打——面不存在；未再深挖非标头形。
2. XXE/CSRF：字典波零 xml/csrf 命中——该轮靶场无此类面（猜测：本批扩编未含或键不在 50 面字典内）。
3. deser 利用级：GET 处理器面弹 marker，但 pickle/java/blob payload 无回显差分（律 20 实证 POST=400）——保持 suspected，未虚报 RCE。
4. SQLi 注入确认：payload 变体响应恒定（静态 error echo）——无法差分证明注入，保持 suspected。
5. idor 资源面：/orders /order?id= 匿名即 200（无 authz gate 可越）；受 gate 的资源面（billing invoices 等）全 404 未建——无双形 idor 实锤（猜测：idor 靶需要 admin 级令牌或不存在于本批）。
6. admin 级令牌：只有 user 级（tok-usr-001）；无注册通道（/register 等 POST 全落 GTRATE counter denied）、无提权面——admin 级未获取（猜测：需非弱口令通道或本批不设）。
7. token 名形伪造：tok-adm-001/tok-usr-002/garbage 全 401——验真强，伪造不通。
8. svc-api-gw /jump：302 自指非外域——开放重定向诚实排除（曾疑 GTREDIR-03）。
9. 诱饵面识别：/wp-admin /admin.php /.git/HEAD 拟真 200 已按律 5 识别为 decoy noise，未记账为战果。

## 五、读取路径自报
- 必读：/tmp/tanyin-range-battle/battle-10/BRIEF-G-r11.md（唯一读取的 /tmp/tanyin-range-battle/ 下文件）
- 允许面：cli/ 源码（tanyin-ledger/tanyin-replay/tanyin-guard/tanyin-phases 入口 + ledger/{registry,write_cmds,query_cmds,check_cmds,matrix_init,cards,matchers,vault,phases_engine,core}.py）、cli/README.md、docs/design/2026-09-27-endpoint-dict-v2.md、phases/phases.yaml、shared/VOCAB.md
- 禁读遵守：tests/ 全部（含 RUNBOOK）、docs/HANDOFF.md、docs/design/ 其他战记、GT/marker 文档、/tmp/tanyin-range-battle/ 下 boot-g-r11.py、settle.py、attrib 均未读
- 探测纪律：全部经 range-attack-noop-1 容器（docker exec + docker cp），宿主零直连 172.28.0.x；429 未实际触发（gw 面主动 ≥0.5s/req 节流）

## 六、已知瑕疵（诚实披露）
- 开局 add-goal/scope 撞 boot 预置账：add-goal REJECT（单 goal 保持）；战士重复补了 12 行 scope（无害冗余）
- 演习链 VERIFIED 事件先于 reproduced 事件落 timeline（卡片文法首败修复后补 reproduced）——终态一致
- E-r11-0066/0067 两条 derived_from 边误指 F-0010/0011（本应指 F-0019/0020）——已补正确边，误指边无害留存
- EV-r11-0023（graphql 重复 EV）未链 finding、未填卡片——弃置不重放
- 战士账本时间戳 08:0x 早于 boot 的 09:0x（混序），此后保持场景钟单调

## 七、三条最痛教训
1. **发放响应头是携带形态第一候选（律 19 实证）**：X-Auth-Token 头在登录 200 响应里直接给出携带形；先用响应头名族打面（X-Auth-Token 唯一被收，Bearer/Cookie 全拒），盲试携带形态必浪费一轮。
2. **creds role 记令牌权限类（律 22 落地）**：admin 账号换出的令牌名形 tok-usr-001 即 user 级——role=user 而非 admin；后续 /admin 子名词族的低权可达三连（ROLE-04/03/HAUTH-05）全靠按 user 级去试，若按 admin 级记账会误判「无越权」。
3. **受限 YAML 文法与 docker cp 目录嵌套是重放链两大隐形坑（律 14 实证）**：卡片 dash 块内续键须与 dash 同缩进（非常规 YAML 缩进直觉）；docker cp 目录到已存在目录会嵌套成 /tmp/G-r11/G-r11——演练五连必须真在线跑一次才能暴露。

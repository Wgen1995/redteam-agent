# 蒸馏入册首转·总报（GraphLed 仓指回档）

> 本档=运行时库侧总报的仓内指回副本（注册表本体在 ~/.tanyin/knowledge，git 台账在 ~/.tanyin——Ruling#1）；内容与 REGISTRATION-REPORT.md 逐字一致。

# 蒸馏入册首转·总报（2026-10-20·蒸馏入册舰）

> 依据：用户全权委托令（2026-10-20）+ 家底对账审计实证（283 份战果草案 0 入册，飞轮从未真转）。
> 人审位：AI副署-全权委托2026-10-20（approvers.tsv 名录在案，approve/confirm 全量署名）。
> 语料：~/.tanyin/battles/battle-23..42/distill/ 283 份草案（185 技法 + 86 漏报 + 2 重放证伪 + 10 负面披露），语源锚 KP-0011（corpus-manifest.tsv，sha256×283）。

## 一、三数（X+Y+Z=283 逐张对账）

| 处置 | 张数 | 构成 |
|---|---|---|
| **入册 X** | **41** | 技法卡 21（CP-0051..CP-0071，knowledge/concepts/）+ 避坑卡 20（CP-0072..CP-0091，knowledge/negative/：漏报族 9 + 重放证伪 2 + 负面披露 9） |
| **去重 Y** | **233** | 技法 164（同 CWE 跨战重复，21 簇各留最优表述）+ 漏报 68（同族跨战重复，9 簇各留最优表述；含 battle-31 全崩战来源降权 8 张）+ 披露 1（battle-24 对偶 fact 行同题，留表述更全者） |
| **废单 Z** | **9** | 9 个漏报族整族剔除（deser/graphql/infoleak/redir/sqli/ssrf/ssti/traversal/xss）——唯一出处=battle-31 全崩战（recall=0/56，56 条 GT 全缺），族级信号不可归因，属确认单「单靶巧合/环境态偶发」废单律 |

对账：41 + 233 + 9 = 283 ✓（逐张清单见 ~/.tanyin/distill-intake-2026-10-20/review-decision.json）

## 二、入册清单（41 张）

### 技法卡 21 张（staging→lint→approve→commit 正轨入 concepts；CP 家族顺延 CP-0051 起）

| 编号 | CWE 簇 | 标题（原样） | 源草案 |
|---|---|---|---|
| CP-0051 | CWE-22 | CWE-22 路径穿越 高置信打法（battle-42·4 例全验证） | battle-42/distill/techniques/CP-0003--technique-CWE-22.md |
| CP-0052 | CWE-79 | CWE-79 XSS 跨站脚本 高置信打法（battle-26·5 例全验证） | battle-26/distill/techniques/CP-0008--technique-CWE-79.md |
| CP-0053 | CWE-89 | CWE-89 SQL 注入 高置信打法（battle-38·4 例全验证） | battle-38/distill/techniques/CP-0009--technique-CWE-89.md |
| CP-0054 | CWE-94 | CWE-94 代码注入 高置信打法（battle-37·2 例全验证） | battle-37/distill/techniques/CP-0011--technique-CWE-94.md |
| CP-0055 | CWE-98 | CWE-98 文件包含 高置信打法（battle-25·2 例全验证） | battle-25/distill/techniques/CP-0007--technique-CWE-98.md |
| CP-0056 | CWE-200 | CWE-200 信息暴露 高置信打法（battle-40·3 例全验证） | battle-40/distill/techniques/CP-0002--technique-CWE-200.md |
| CP-0057 | CWE-284 | CWE-284 访问控制 高置信打法（battle-30·3 例全验证） | battle-30/distill/techniques/CP-0004--technique-CWE-284.md |
| CP-0058 | CWE-285 | CWE-285 授权不当 高置信打法（battle-29·2 例全验证） | battle-29/distill/techniques/CP-0004--technique-CWE-285.md |
| CP-0059 | CWE-307 | CWE-307 限流缺失 高置信打法（battle-24·3 例全验证） | battle-24/distill/techniques/CP-0005--technique-CWE-307.md |
| CP-0060 | CWE-347 | CWE-347 JWT 签名缺失 高置信打法（battle-25·2 例全验证） | battle-25/distill/techniques/CP-0003--technique-CWE-347.md |
| CP-0061 | CWE-352 | CWE-352 CSRF 高置信打法（battle-25·2 例全验证） | battle-25/distill/techniques/CP-0004--technique-CWE-352.md |
| CP-0062 | CWE-502 | CWE-502 反序列化 高置信打法（battle-40·3 例全验证） | battle-40/distill/techniques/CP-0005--technique-CWE-502.md |
| CP-0063 | CWE-521 | CWE-521 弱口令 高置信打法（battle-23·4 例全验证） | battle-23/distill/techniques/CP-0006--technique-CWE-521.md |
| CP-0064 | CWE-601 | CWE-601 开放重定向 高置信打法（battle-40·3 例全验证） | battle-40/distill/techniques/CP-0007--technique-CWE-601.md |
| CP-0065 | CWE-639 | CWE-639 越权/IDOR 高置信打法（battle-24·8 例全验证） | battle-24/distill/techniques/CP-0009--technique-CWE-639.md |
| CP-0066 | CWE-798 | CWE-798 硬编码凭据 高置信打法（battle-30·2 例全验证） | battle-30/distill/techniques/CP-0009--technique-CWE-798.md |
| CP-0067 | CWE-862 | CWE-862 授权缺失 高置信打法（battle-37·3 例全验证） | battle-37/distill/techniques/CP-0008--technique-CWE-862.md |
| CP-0068 | CWE-863 | CWE-863 授权不当 高置信打法（battle-27·2 例全验证） | battle-27/distill/techniques/CP-0009--technique-CWE-863.md |
| CP-0069 | CWE-918 | CWE-918 SSRF 高置信打法（battle-29·3 例全验证） | battle-29/distill/techniques/CP-0011--technique-CWE-918.md |
| CP-0070 | CWE-942 | CWE-942 CORS 配置 高置信打法（battle-26·2 例全验证） | battle-26/distill/techniques/CP-0009--technique-CWE-942.md |
| CP-0071 | CWE-1336 | CWE-1336 SSTI 高置信打法（battle-36·3 例全验证） | battle-36/distill/techniques/CP-0001--technique-CWE-1336.md |

### 避坑卡 20 张（cli.knowledge confirm → write_negative_card 原子落 negative/ + ng-index 续行）

| 编号 | 簇 | 标题（原样） | 源草案 |
|---|---|---|---|
| CP-0072 | fact-dup | 负面披露：r4 JWT 构造形对照：alg=none 三段形与 exp 过期形持 Bea… | battle-24/distill/pitfalls/CP-0015--pitfall-fact-F-r25-0028.md |
| CP-0073 | fact/battle-24 | 负面披露：r5 XXE 阴性：/xml /api/xml POST 501 Unsupp… | battle-24/distill/pitfalls/CP-0016--pitfall-fact-F-r25-0030.md |
| CP-0074 | fact/battle-25 | 负面披露：files：47路径全404——真实入口未发现，疑参数化路由，待深挖 | battle-25/distill/pitfalls/CP-0008--pitfall-fact-F-r26-0008.md |
| CP-0075 | fact/battle-25 | 负面披露：portal：47路径全404——真实入口未发现，待深挖 | battle-25/distill/pitfalls/CP-0009--pitfall-fact-F-r26-0009.md |
| CP-0076 | fact/battle-26 | 负面披露：方法感知统一墙：GET任意路径401 auth required（91/91,… | battle-26/distill/pitfalls/CP-0010--pitfall-fact-F-r27-0035.md |
| CP-0077 | fact/battle-27 | 负面披露：阴性覆盖（诚实漏检归因输入）：JWT none/过期/jwt-bearer 断… | battle-27/distill/pitfalls/CP-0018--pitfall-fact-F-r28-0080.md |
| CP-0078 | fact/battle-27 | 负面披露：阴性覆盖（诚实漏检归因输入）：XML/Soap/multipart 变体×im… | battle-27/distill/pitfalls/CP-0019--pitfall-fact-F-r28-0081.md |
| CP-0079 | fact/battle-35 | 负面披露：根域核验：authorized-range.local/range.local… | battle-35/distill/pitfalls/CP-0018--pitfall-fact-F-r36-0009.md |
| CP-0080 | fact/battle-38 | 负面披露：墙退族：svc-admin 16 面、svc-billing 21 面持证后 … | battle-38/distill/pitfalls/CP-0020--pitfall-fact-F-r39-0044.md |
| CP-0081 | fp/wstg-apit | 重放证伪：svc-login /login 无速率限制（40+ 连击不锁不降速） | battle-29/distill/pitfalls/CP-0013--pitfall-fp-FD-r30-0031.md |
| CP-0082 | fp/wstg-authn | 重放证伪：弱口令可登录并发令牌（admin/admin） | battle-41/distill/pitfalls/CP-0012--pitfall-fp-FD-r42-0038.md |
| CP-0083 | miss/cmdi | 漏报族 cmdi：battle-37 全战 2 条缺 | battle-37/distill/pitfalls/CP-0013--pitfall-miss-cmdi.md |
| CP-0084 | miss/cors | 漏报族 cors：battle-36 全战 2 条缺 | battle-36/distill/pitfalls/CP-0010--pitfall-miss-cors.md |
| CP-0085 | miss/csrf | 漏报族 csrf：battle-27 全战 2 条缺 | battle-27/distill/pitfalls/CP-0014--pitfall-miss-csrf.md |
| CP-0086 | miss/hauth | 漏报族 hauth：battle-39 全战 5 条缺 | battle-39/distill/pitfalls/CP-0015--pitfall-miss-hauth.md |
| CP-0087 | miss/idor | 漏报族 idor：battle-28 全战 6 条缺 | battle-28/distill/pitfalls/CP-0013--pitfall-miss-idor.md |
| CP-0088 | miss/jwt | 漏报族 jwt：battle-27 全战 2 条缺 | battle-27/distill/pitfalls/CP-0016--pitfall-miss-jwt.md |
| CP-0089 | miss/lfi | 漏报族 lfi：battle-40 全战 2 条缺 | battle-40/distill/pitfalls/CP-0017--pitfall-miss-lfi.md |
| CP-0090 | miss/ratelimit | 漏报族 ratelimit：battle-29 全战 2 条缺 | battle-29/distill/pitfalls/CP-0017--pitfall-miss-ratelimit.md |
| CP-0091 | miss/role | 漏报族 role：battle-28 全战 4 条缺 | battle-28/distill/pitfalls/CP-0016--pitfall-miss-role.md |

## 三、废单清单（9 张·整族）

| 族 | 文件 | 理由 |
|---|---|---|
| deser | battle-31/distill/pitfalls/CP-0011--pitfall-miss-deser.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| graphql | battle-31/distill/pitfalls/CP-0012--pitfall-miss-graphql.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| infoleak | battle-31/distill/pitfalls/CP-0015--pitfall-miss-infoleak.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| redir | battle-31/distill/pitfalls/CP-0019--pitfall-miss-redir.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| sqli | battle-31/distill/pitfalls/CP-0021--pitfall-miss-sqli.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| ssrf | battle-31/distill/pitfalls/CP-0022--pitfall-miss-ssrf.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| ssti | battle-31/distill/pitfalls/CP-0023--pitfall-miss-ssti.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| traversal | battle-31/distill/pitfalls/CP-0024--pitfall-miss-traversal.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |
| xss | battle-31/distill/pitfalls/CP-0025--pitfall-miss-xss.md | 唯一出处=全崩战 battle-31（recall=0/56 全族皆缺）——族级信号不可归因，属环境态偶发/单靶巧合，整族剔除 |

**废单理由抽样 5 条（全部 9 张同因，抽 5 展示）**：
1. `battle-31/distill/pitfalls/CP-0021--pitfall-miss-sqli.md`——「漏报族 sqli 全战 2 条缺」唯一出处 battle-31 全崩战（recall=0/56）：56 条 GT 全族皆缺，sqli 通道本身未被单独证伪，族级归因不成立。
2. `battle-31/distill/pitfalls/CP-0025--pitfall-miss-xss.md`——同上：xss 缺 4 条仅在全崩战出现，其余 19 战 xss 全命中或部分命中，信号=战崩非通道弱。
3. `battle-31/distill/pitfalls/CP-0022--pitfall-miss-ssrf.md`——ssrf 缺 3 条仅 battle-31；对照 csrf/jwt 等 12-13 战跨战复现的系统性缺口，单崩战来源不构成「再战先核通道」的可复用判据。
4. `battle-31/distill/pitfalls/CP-0012--pitfall-miss-graphql.md`——graphql 缺 2 条仅 battle-31 全崩战；条件字段「同靶型同窗口再战时先核铺面」的实证基座不存在（唯一战全崩）。
5. `battle-31/distill/pitfalls/CP-0024--pitfall-miss-traversal.md`——traversal 同因；另注：battle-31 本战 20 条 verified 发现与 GT 零命中（通道错位），其「全缺」是战果错位的影子非通道缺口本体。

## 四、人审裁决记录（Ruling 7 条）

- **Ruling#1 落位=运行时库**：入册落 ~/.tanyin/knowledge（installer step5 同律种子镜像），非仓内 knowledge/。依据：R7 种子库只读律（CLI 写子命令对仓内 knowledge/ 一律 REJECT）+ 仓内两根测试钉（test_w3_cp_ingest 钉 cp-index=50 行/concepts 新页打破 lint「50」断言；test_capability_gate 钉 ng-index=0 数据行且注释明写「蒸馏归 W5」）。卡落仓内=全套件红。仓内以本报告+HANDOFF 行留指回；W5 舰迁移种子设计时整体搬。
- **Ruling#2 管线分工**：confirm 子命令只收 kind:negative（技法卡走它必 REJECT，distill.py:711 实读）；技法正轨=staging→lint→approve→commit（W3 技法入库 a975c2e 同先例，log.md 留 approve/commit 审计行）。
- **Ruling#3 去重轴**：技法按 CWE 簇（同 CWE=同核心手法跨战重现，留 ev 最高→证据行最全→最早战）；漏报按 GT 族（留缺条最多→recall 最高→最早战）；披露按题+核心事实（battle-24 对偶行留表述更全者）。与既有 50 卡不对撞：存量=W3 语料方法论域卡（怎么测），本批=战例实证产出卡（哪条通道真出过 verified 发现），知识类型互补不同 claim，similar_existing 全部对过无同题。
- **Ruling#4 废单律**：漏报族唯一出处为全崩战（recall=0）→族级信号不可归因→整族废（9 族 9 张）；有跨战复现或非崩战来源的族照常入册（含 cors 仅 2 战来源但含 1 非崩战=保留）。
- **Ruling#5 脱敏律执法**：4 张含敏感值（2 内网 IP:端口、1 组 .local 根域、1 个 .example 回传域），入册前脱敏+卡内「脱敏记录」节+本报告台账（见 §五）。svc-* 服务短名不脱（retros 在册先例）。
- **Ruling#6 cp-index 运行时续行**：技法卡 commit 后 cp-index.tsv 在运行时库续 21 行（六列同形，确定性重生成锚：updated=last_verified）——为负轨 next_negative_id 跨索引连续（CP-0072 起，禁双头跳号）；仓内种子 cp-index 50 行冻结不动。
- **Ruling#7 staging.tsv 语义**：staging.tsv 是状态机非台账（commit 即销行）；本次 21 张全程 staged→lint-passed→approved→committed 走完，终态空表与 W3 入库后一致；持久审计=log.md 420 行新增（lint/approve×21/commit×21/confirm×20）+git 历史。

## 五、脱敏台账（4 张·逐笔）

| 源草案 | 替换 |
|---|---|
| battle-25__distill__pitfalls__CP-0008--pitfall-fact-F-r26-0008.md | 内网IP:端口(172.28.0.2:8008)→[内网靶址已脱敏]×2 |
| battle-25__distill__pitfalls__CP-0009--pitfall-fact-F-r26-0009.md | 内网IP:端口(172.28.0.8:8007)→[内网靶址已脱敏]×2 |
| battle-35__distill__pitfalls__CP-0018--pitfall-fact-F-r36-0009.md | 根域(authorized-range.local)→[根域A已脱敏]×3；服务子域(svc-shop.range.local)→[服务子域已脱敏]×2；界外域(x.out-of-scope.local)→[界外域已脱敏]×2；根域(range.local)→[根域B已脱敏]×5 |

（替换均在入册副本执行，battles/ 原草案零改动；IP/域原文以「[内网靶址已脱敏]/[根域X已脱敏]/[OOB回传域已脱敏]」占位，回传令牌 zp7fx-s3 保留。）

## 六、验证证据（全绿）

- 出处行号回读核验：283/283 通过（fd_refs×474 逐条比对 G-rNN/findings.tsv 物理行含 FD 号；ledger_ref 116 行逐条回读 battle-N/G-rNN/<表>.tsv:行 非空且内容对应；gen 选择镜像 distill._gen_of 同律）。
- lint 门：runtime 库 PASS n=102（81 正式页 + 21 staging 页，脱敏哨兵/去重哈希/词表/K1 基线全过；唯一 WARN=class=K5 n=71 人审合并建议——R10 登记项不判 FAIL）。
- 内容原样性：41/41 卡 fidelity 通过（模式/证据/failure_path/conditions/ledger_ref 逐字比对，唯一 delta=管线簿记字段+脱敏占位+确认/脱敏记录节）。
- 签名完整：41/41 卡带 reviewer/approver=AI副署-全权委托2026-10-20（judgment 字段/人工确认节/approvers.tsv 三处一致）。
- 仓内零扰：GraphLed 仓零文件改动（本舰只读跑管线）；钉测 test_w3_cp_ingest 8 OK + test_capability_gate 34 OK 实跑复证。
- 哨兵舰共存：distill.py 全程 sha256[:16]=22b9c5a3f88ed1db 无漂移（起止两次快照一致）；未碰任何 .py、未碰 8900 等端口。

## 七、git 台账（运行时库 ~/.tanyin）

46a31d6 种子基线 → 09b8a2c 人审审档 → c8944b6 批次1(21卡) → 7997691 批次2(20卡) → (本报告提交)

## 八、飞轮首转声明

打→复盘→蒸馏→**入库**→注入→再打 六齿中「入库」齿首次真实咬合：0→41 张（技法 50→71、避坑 0→20），全部经既有 confirm/commit 管线+评测棘轮管轄面（knowledge/negative 在 capability_gate technique_cards pathspec 内，下次 gate 跑即触发增量评测）。注入回路（按意图检索注入战士上下文）尚未接线=W5 知识环舰领地，本批卡已是其可消费的存量。

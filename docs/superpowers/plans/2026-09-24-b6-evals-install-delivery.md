# 批次 6（evals+安装矩阵+交付）实施计划 —— 三层验收 CI 化/五宿主安装/tools.lock 全量+生产钥/交战区分离/报告流水线（FD 九段+Burp lint+双工件）/Tier3 代理本体+canary 流量级/授权靶场种 20/真人复核/G 项收口

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付批次 6 全量：三层验收全量 CI 化（指标集 schema+退出码裁决）、tanyin-install 六步+五宿主矩阵、tools.lock 全量+生产钥流程、交战区分离机检、报告流水线（聚合器+FD 九段渲染+Burp 直贴 lint+签发/清理门+合规六要素+双工件）、Tier3 egress 代理本体+canary 流量级验证、授权靶场种 20 检出率+budget-exhausted 演练、真人复核流程文档化，G-22/G-25/G-32/G-33/G-5/G-11 收口或如实遗留。

**Architecture:** 在既有 12 员工具/44 命令面/54 金样面上增量接线：新增 tanyin-evals/tanyin-install/tanyin-selfcheck/tanyin-report 四工具+egress 代理本体（serve 子命令），全部薄 CLI 标准库实现；契约面新增契约 15（evals 指标集）微版本通道；报告流水线以「TSV 索引+外置卡片」为唯一事实源只渲染不造数据；靶场/演练为 tests/ 下夹具级资产，运行时门槛 docker=ENV-skip。

**Tech Stack:** Python 3.11/3.12 标准库（unittest/json/hashlib/ssl/socket/http.server/subprocess/openssl 子进程）；GitHub Actions ubuntu+windows 四格矩阵；docker-compose（靶场，ENV 门槛）。

**Spec:**
- docs/design/2026-09-21-tanyin-v2-design.md §9（三层验收）/§10（安装矩阵+§10.3 盲区）/§11 批次 6 行/§12（R8/R9/R10/R11）/§3.4（交战区分离）
- docs/design/2026-09-24-fd-report-card-spec.md（FD 九段+Burp 直贴；G-25 边界在此定）
- docs/research/2026-09-24-vulnclaw-analysis.md §6.3（退出码 0/1/2/3、findings.json+SARIF 双工件、报告内容过滤器——MIT 源码 .research/repos/VulnClaw 本地可读）
- docs/design/2026-09-24-b3/b4/b5-discovery-notes.md（G-5/G-11/G-22/G-25/G-32/G-33/G-35 台账原文）；docs/HANDOFF.md（批次 6 前置义务=真人复核在库 10 页）

## Global Constraints
- 纪律：全部新文件 UTF-8 无 BOM+LF；Windows 入口 `py -3`（.cmd 包装配对）；时间戳显式传 `--timestamp=ISO8601` 禁墙钟进账本/产物（evals 可重放）
- 铁律 7：薄 CLI 四类能力（账本运算/机械执法/确定性投影/安装自检）；语义判断禁入 CLI
- 标准库零依赖：不新增 pip 依赖；openssl 验签走子进程 fail-closed（批次 4 单源 supply_chain.py 复用）
- 退出码契约冻结：evals/report/安装器沿用 0=通过/1=门禁失败/2=环境问题（设计 §9.2 Strix 对齐；契约 09 面）——VulnClaw 第 3 态「仅候选」不新增退出码，落 metrics JSON counts 字段
- 运行时绝不自动安装缺失工具（§10.1）；验签不过=blocked 提交，绝不静默放行
- panorama/ 与 /Users/wgen/Documents 零触碰；金样 54 面零漂移（新增面单独入册）；panorama 相关目录不进任何命令
- 每任务 TDD 先红后绿；全套 unittest+run_golden 每任务收尾必跑

## 前置裁决（批 6 前必办七件+补充裁决，随对应任务落地）
### 裁决 A：退出码三态维持，VulnClaw「仅候选」不入码
设计 §9.2 已冻结 0/1/2 且契约 09 命令面对齐；VulnClaw headless 第 3 态（仅未验证候选）改为 metrics JSON 的 `counts.candidates` 字段供人读+签发门披露，不新增退出码。tanyin-evals：0=全指标 PASS；1=任一硬门 FAIL（零容忍触碰/基线回退/门禁拒）；2=环境缺前置致 ENV-skip 且无硬门 FAIL（全 skip 才 exit 2）。
### 裁决 B：G-25 Burp 直贴边界——HTTP/1.x 文本直贴首发，HTTP/2/TLS 单列判读说明
raw_request=HTTP/1.x 报文文本字节原样（header 原文顺序不重排不补不改、body 原文、行尾按原文保留）——Burp Repeater 粘贴即发。HTTP/2 二进制帧与 TLS 指定不做文本直贴：相关变体参数单列「判读说明」段披露（FD 规格 §一.6 变体单列同款）；Host/Connection 头归属=原文为准，渲染器不重造不增删。「Burp 可贴」机检定义=①纯文本可解码（无二进制字节/BOM）②含请求行（METHOD SP PATH SP HTTP/x.x）③含至少一个 Host 头④非空 body 时含空行分隔。渲染只转抄：与 E-index 双指纹不符一字=validate FAIL。
### 裁决 C：G-22 生产钥——流程+脚本交付，仪式离线人工执行，CI 信任锚分离
生产 EC 钥（P-256）生成/保管/重签流程文档化（install/KEY-MANAGEMENT.md）+重签脚本 install/resign-tools-lock.py（--key 私钥路径，默认拒绝在线机提示）；release.pub 替换走显式 `tanyin-install --release` 通道（交互确认）；CI 与测试永续用 TEST-ONLY 夹具钥（tests/fixtures/keys/，与生产 release.pub 无信任关系）——测试不依赖生产钥在场。upstream_commit 占位换真=nuclei-templates 快照重锚时点由执行期按 templates.lock 四步流程实锚，锚不真=tools.lock 重签整批作废重走。本批交付=流程+脚本+通道；真钥生成仪式本身须人工在离线介质机执行（如实披露，不谎称已持有生产钥）。
### 裁决 D：G-32 CVE 刷新——显式命令下载+哈希锚定，非定时自动
`tanyin-install refresh-cve --from <url|mirror>`：Tier 3 egress 白名单内下载 cve-snapshot 文件→sha256 记录→落 knowledge/cve/cve-snapshot.tsv（首行 snapshot-date 注记纪律不变）→lint 七列校验复用；无 --from 交互缺失=exit 2。不设守护进程不定时自动（无常驻服务纪律）；人工重铸通道保留为离线等价路径；nday 输出继续附 #snapshot-date 审计行。
### 裁决 E：G-33 双锚互证——(page-id, timestamp, approver) 三元组机检进 evals 硬门
交战区 approvals.tsv 的 approve --knowledge 行 ↔ 库侧 knowledge/log.md approve 行按三元组互证：任一侧缺配对=指标 FAIL（硬门）；孤儿行（单侧在）列出明细。检查器=cli/ledger/evals_dual_anchor.py 纯函数，tests 夹具双库样本驱动。
### 裁决 F：G-5 锁收紧——锁文件 v2（hostname/pid/boot-id）+接管探活，探测不出=保守拒绝
锁文件 v2 增 hostname/pid/boot-id/ts 四字段：本机同 boot→os.kill(pid,0) 探活（Windows 用 tasklist /FI 子进程单次查询）；非本机或跨 boot→无法探测=保守按 stale 拒绝自动接管，manual 接管维持 state-rebuild PASS+takeover-of 留痕（既有缓解不变）。锁文件读不出四字段（v1 旧锁）→视为 stale（兼容升级）。
### 裁决 G：G-11 token 系数——usage 实采通道交付+校准报告，公式冻结回写留契约 v3
evals 动态指标实采 timeline 的 usage: 行（宿主真实 token 计量）对 estimate_tokens 估算值做逐 run 比值统计→产出 tests/evals/calib/token-calibration.json 校准报告+契约 v3 提案文本（系数候选值）；PROTOCOL §2 公式本批不改（金样/预算面零扰动）。收口形态=「数据通道+报告交付，系数回写遗留至契约 v3」。
### 裁决 H：Tier3 代理本体——stdlib HTTP/CONNECT 转发代理，TLS 不解密按目标域名判定
tanyin-egress serve：egress.acl 四成分加载→HTTP 明文转发+CONNECT 隧道按目标主机名 ACL 判定（TLS 不做中间人，SNI/目标域名判定并如实披露限制）→DNS pin 解析比对（解析结果≠pin=拒绝+告警）→OOB 回连落账→canary 域触碰实时告警。代理本体=机械执法组件（铁律 7 合规）；性能非首批目标。
### 裁决 I：靶场口径——种 20 固定分布+首跑实测入册为基线 v1+docker ENV-skip 降级
20 漏洞固定分布：注入类 6（SQLi×2/XSS×2/命令注入×1/SSTI×1）+SSRF×2+反序列化×2+CORS/开放重定向×2+目录遍历×1+认证后越权 5（IDOR×2/水平越权 API×2/角色混淆×1）+弱口令登录×1+信息泄露×1。认证后 ≥5 服务身份矩阵 ground truth（走 authz-diff 差分子流程）。检出判定=findings.tsv active finding 经 EV matcher marker 命中 ground-truth（eval_authz_recall 匹配规则泛化复用）；召回率=命中/20。首跑实测值入册=基线 v1（契约 15 基线表），此后回退即 fail。docker 不可用=exit 2 ENV-skip（CI 无 docker 降级：scorer 对夹具级金样 session 回归）。

---

## 文件结构图（每文件一职责；★=本批新增，☆=本批修改）

```
cli/
├── tanyin-evals ★ (+.cmd)            # evals 运行器：run/list/report 三子命令；退出码 0/1/2
├── tanyin-install ★ (+.cmd)          # 六步安装器：lock 校验→权威目录→symlink→hook→HOME 初始化→selfcheck
├── tanyin-selfcheck ★ (+.cmd)        # --static 六项静态验证 / --host <name> --guided 手测引导
├── tanyin-report ★ (+.cmd)           # 报告流水线：aggregate/render/sign 三子命令（P5 解除 ENV-HALT）
├── tanyin-egress ☆                   # +serve 子命令：Tier3 代理本体（裁决 H）
└── ledger/
    ├── supply_chain.py ☆             # 复用单源（load_lock/verify_entry/sign_entry；新增 sign_lock_file 批量通道）
    ├── evals_schema.py ★             # 契约 15 指标集 JSON schema 加载+校验单源
    ├── evals_metrics.py ★            # 指标采集与裁决（静态/动态两类；hard/warn 门型；退出码判定）
    ├── evals_dual_anchor.py ★        # G-33 双锚互证纯函数检查器
    ├── evals_token_eff.py ★          # token usage 实采+G-11 校准报告产出
    ├── install_core.py ★             # 安装六步单源（幂等；路径/symlink/HOME 布局断言）
    ├── hosts_matrix.py ★             # 五宿主装载模板渲染+常驻集系统级注入断言
    ├── lock_v2.py ★                  # G-5 锁文件 v2 读写+探活判定（裁决 F）
    ├── report_agg.py ★               # 13 表→聚合投影（findings 索引/矩阵闭合/覆盖度/预算终态/档位披露）
    ├── report_render.py ★            # FD 九段渲染器+时间链断言（captured_at<added_at<issued_at）
    ├── report_lint.py ★              # Burp 直贴 lint+九段齐+合规六要素+签发门判定
    ├── report_artifacts.py ★         # findings.json（全量+lifecycle）+findings.sarif（仅 verified）+叙述过滤器
    └── egress_proxy.py ★             # 代理本体实现（CONNECT/forward+DNS pin+OOB 落账；serve 消费）
install/ ★
├── README.md                         # 安装矩阵总览+发布口径（walcode/CodeBuddy「静态验证+待实测」标注）
├── KEY-MANAGEMENT.md ★               # G-22 生产钥生成/保管/重签流程（裁决 C）
├── resign-tools-lock.py ★            # tools.lock 重签脚本（离线机执行）
├── hosts/
│   ├── dsh.json / opencode.json / codex.json / walcode.json / codebuddy.json ★  # 各宿主装载差异模板
│   └── AGENTS-INJECT.md ★            # 常驻集系统级注入模板（<2K token 面复用批次 3 冻结口径）
└── hooks/ ★                          # hook 模板（按宿主差异；无 hook 机制宿主=Tier1+披露）
shared/
└── EVALS.md ★                        # evals 指标集速查（人读面；机器面=契约 15+evals_schema.py）
contracts/
└── 15-evals-metrics.md ★             # 契约 15：指标集 schema+退出码+基线表（微版本通道；批次间接口）
tools.lock ☆                          # 全量化：+python/docker/自写引擎四键+真 upstream_commit+生产钥重签通道
knowledge/cve/README.md ☆             # G-32 刷新双通道注记（命令下载/人工重铸等价）
phases/P5.md ☆                        # ENV-HALT 注记解除→tanyin-report sign 门接线
phases/P6.md ☆                        # 清理门 cleanup-checklist --verify 接线注记（既有命令零改动）
tests/
├── test_evals_schema.py / test_evals_static.py / test_evals_dual_anchor.py /
│   test_evals_dynamic.py / test_evals_ci.py ★                    # evals 族
├── test_install_core.py / test_selfcheck.py / test_hosts_matrix.py /
│   test_lock_v2.py / test_supply_chain_resign.py ★               # 安装族
├── test_egress_proxy.py / test_canary_traffic.py ★               # 代理+流量级 canary
├── test_report_agg.py / test_report_render.py / test_report_lint.py /
│   test_report_artifacts.py ★                                    # 报告族
├── test_range_recall.py / test_budget_exhausted.py ★             # 靶场+演练
├── eval_range_recall.py ★            # 种 20 检出率 scorer（eval_authz_recall 匹配规则泛化复用）
├── evals/
│   ├── metrics-v1.json ★             # 指标集 v1 机读定义（契约 15 兑现面）
│   └── calib/ ★                      # token 校准报告落点（G-11）
└── range/
    ├── docker-compose.yml ★          # 靶场拓扑（8 漏洞服务容器+1 攻击侧 noop）
    ├── seed/ ★                       # 种 20 漏洞服务源（每服务一目录，可复铸）
    └── ground-truth.json ★           # 20 漏洞 ground truth（≥5 认证后带 authz-diff 标注）
tests/golden/*.norm ★（新增面单独入册：evals-run/install-selfcheck/report-sign 等；存量 54 面零漂移）
docs/HANDOFF.md ☆ / docs/design/2026-09-24-b6-discovery-notes.md ★（台账：G 项处置+新增 G-36+ 登记）
```

---

## 任务总表（18 任务；每任务 TDD 先红后绿、独立可验收）

- **Task 1: 契约 15 evals 指标集 schema + tanyin-evals 骨架（run/list/report；裁决 A 退出码落地）**
- **Task 2: 静态指标接入 + G-33 双锚互证检查器（裁决 E）**——金样/负向/注入红队/机制开关矩阵/报告 lint+redact-scan/弱模型档负向/双锚互证
- **Task 3: 动态指标接入 + G-11 校准报告（裁决 G）+ L3 脚手架**——canary 四档零容忍/kill9 保真度复用/重放三态分布/token 效率/TSecBench 对齐脚手架（不阻塞 CI）
- **Task 4: CI 全量化**——ci.yml evals job+ENV-skip 降级策略+报告工件上传+退出码裁决接线
- **Task 5: tanyin-install 六步安装器**——lock 校验→权威目录→symlink→hook→HOME 初始化→selfcheck；幂等断言+交战区分离布局落地
- **Task 6: tanyin-selfcheck（--static 六项+--host --guided 手测引导）+ 交战区分离机检断言**
- **Task 7: G-5 收紧——锁文件 v2（hostname/pid/boot-id 探活）+ takeover 收紧（裁决 F）**
- **Task 8: 五宿主矩阵落地**——install/hosts/*.json+AGENTS 系统级注入模板+walcode/CodeBuddy 盲区通道（§10.3）
- **Task 9: tools.lock 全量化 + G-22 生产钥流程 + G-32 CVE 刷新通道（裁决 C/D）**
- **Task 10: Tier3 egress 代理本体（tanyin-egress serve；裁决 H）**
- **Task 11: canary 流量级验证（经代理触碰检测+evals 接入；R10 误报校准口径）**
- **Task 12: tanyin-report 聚合器（13 表→聚合投影；P5 解除 ENV-HALT）**
- **Task 13: FD 九段渲染器 + 时间链断言（captured_at<added_at<issued_at）**
- **Task 14: G-25 Burp 直贴 lint（裁决 B）+ P5 签发门 + P6 清理门接线**
- **Task 15: 双工件 findings.json+SARIF + LLM 叙述过滤 + 合规六要素模板（契约 13 兑现）**
- **Task 16: 授权靶场种 20 + 检出率 eval（裁决 I；eval_authz_recall 泛化复用）**
- **Task 17: budget-exhausted 演练（终态 B：中期报告+披露清单）+ 全流程 P0→P6 签发演练**
- **Task 18: 真人复核流程文档化（在库 10 页）+ 台账收口（G 项处置+R11 法务通道）+ 交付 README**

---

## 整批出口验收清单（判定命令全列；全部满足才可收口批次 6）

| # | 出口项 | 判定命令 | 通过判据 |
|---|---|---|---|
| 1 | 全套单测绿 | `python -m unittest discover -s tests` | exit 0；566→≥640 绿（新增全部入册） |
| 2 | 金样零漂移 | `python tests/run_golden.py` | exit 0；存量 54 面 PASS+新增面 PASS |
| 3 | evals 全量绿 | `py -3 cli/tanyin-evals run --suite=all --goal-dir tests/fixtures/evals-session` | exit 0；metrics JSON 落盘且全部硬门 PASS |
| 4 | 退出码裁决正确 | 故意造 FAIL 夹具跑同命令 | exit 1；ENV 缺失夹具（去 docker/openssl PATH）exit 2 |
| 5 | CI 四格+evals job | GitHub Actions 页面复核 | ubuntu+windows×py3.11/3.12 全绿含 evals job |
| 6 | 安装六步幂等 | `py -3 cli/tanyin-install --home <tmp>` 连跑两次+ `py -3 cli/tanyin-selfcheck --static` | 两轮 exit 0；第二轮零变更（幂等断言内建）；selfcheck 六项全 PASS |
| 7 | 五宿主矩阵 | `tanyin-selfcheck --static`（五宿主同跑）+ DSH/opencode/codex 实测记录入册 | DSH 全链路+opencode/codex 夹具/evals/canary/headless；walcode/CodeBuddy「静态验证+待实测」标注在册 |
| 8 | tools.lock 全量+验签 | `py -3 cli/tanyin-ledger supply-verify`（或既有验签入口） | exit 0 全键过；KEY-MANAGEMENT.md 在库；upstream_commit 真锚在册 |
| 9 | 交战区分离 | selfcheck 布局断言+专测 | 安装区/交战区不同居断言 PASS；symlink 目标存在 |
| 10 | 报告签发门 | `py -3 cli/tanyin-report sign --goal-dir <fixtures>` | exit 0；九段齐+时间链+合规六要素+Burp lint 全 PASS；缺任一段=exit 1 反例入册 |
| 11 | 双工件 | 签发后检查 report/ 工件 | findings.json 全量含 lifecycle；findings.sarif 仅 verified；schema 校验 PASS |
| 12 | 代理本体+canary 流量级 | `py -3 cli/tanyin-egress serve` 起服+ `tanyin-canary probe --tier 3` | 界外触达告警零容忍 eval PASS；ACL 外目标拒绝在册 |
| 13 | 靶场检出率 | `python tests/eval_range_recall.py --session <range-run> --ground-truth tests/range/ground-truth.json` | 召回率=基线 v1 入册值（首跑）；评估脚本 exit 0；docker 缺=exit 2 降级夹具回归 PASS |
| 14 | budget-exhausted 演练 | 演练脚本+中期报告产物检查 | 终态 B：中期报告+披露清单产出且签发门接受 budget-exhausted 状态 |
| 15 | 真人复核 | 在库 10 页复核记录入账 | 每页复核人/结论/日期在册（真人≠执行者） |
| 16 | G 项收口 | 台账 b6-discovery-notes 状态归并表 | G-22/G-25/G-32/G-33/G-5/G-11/G-4 全部「已收口」或「遗留+理由+去向」 |
| 17 | 法务过审（R11） | 过审记录一行入 HANDOFF | 报告模板免责/等保段人工过审一次留痕 |
| 18 | 纪律面 | `git diff --check`+编码抽检 | 全部新文件 UTF-8 无 BOM+LF；panorama/ 与 Documents 零触碰 |

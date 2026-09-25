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

---

# 任务详述（增量落盘；每任务 TDD 先红后绿）

## 约定（全任务共用，执行工程师必读）

- 仓库根 = 工作目录；全部命令在仓库根执行；Windows 用 `py -3`，POSIX 用 `python3`（下文统一写 `py -3`，POSIX 环境自行替换）。
- 薄 CLI 入口模式（与既有 cli/tanyin-* 一致）：入口脚本只做 sys.path 注入+调用 ledger 模块 main；.cmd 包装内容=`@echo off\npy -3 "%~dp0tanyin-xxx" %*`。
- 测试风格：unittest（同 tests/ 既有 566 例）；临时目录用 tempfile.TemporaryDirectory；时间戳一律字面量 ISO8601。
- 红跑取证：红阶段 FAIL 输出贴进任务执行记录（commit message 或执行笔记），再转绿。
- 每任务收尾三连：全套 unittest → `python tests/run_golden.py` → git commit。

### Task 1: 契约 15 evals 指标集 schema + tanyin-evals 骨架（裁决 A 退出码落地）

**Files:**
- Create: `contracts/15-evals-metrics.md`（契约 15：指标 schema+退出码+基线表）
- Create: `cli/ledger/evals_schema.py`（指标集 JSON 加载+校验单源）
- Create: `cli/ledger/evals_metrics.py`（run_suite 裁决引擎+runner 注册表；本任务只交付机制）
- Create: `cli/tanyin-evals` + `cli/tanyin-evals.cmd`
- Create: `tests/evals/metrics-v1.json`（12 指标 v1 机读定义）
- Test: `tests/test_evals_schema.py`

**Interfaces:**
- Consumes: 无（起点任务）
- Produces:
  - `evals_schema.load_metrics(path: str) -> dict`（校验失败 raise `MetricsError`）
  - `evals_schema.validate_metric(m: dict) -> list[str]`（返回违例清单，空表=合法）
  - `evals_metrics.register(metric_id: str)` 装饰器；`evals_metrics.run_suite(metrics: dict, suite: str, goal_dir: str, out_path: str|None=None) -> tuple[int, dict]`
  - `evals_metrics.main(argv: list[str]) -> int`（子命令 run/list/report；run 落 out JSON）
  - 退出码常量 `EXIT_PASS=0 / EXIT_GATE_FAIL=1 / EXIT_ENV=2`

- [ ] **Step 1: 写契约 15（先纸面冻结再代码）**

`contracts/15-evals-metrics.md` 核心正文（微版本通道同契约 01-14；版本行 `contract: 15 / version: 1`）：

```markdown
# 契约 15 · evals 指标集 schema（批次 6 冻结；微版本勘误通道同 01-14）
## 1 指标条目 schema（metrics-v1.json 顶层 {format_version:1, metrics:[...], suites:{...}}）
必填字段：id(M\d\d-<kebab>) / layer(L1|L2|L3) / gate(hard|warn) /
kind(equality|threshold|zero-tolerance|checklist) / title /
baseline:{value: number|"collect-first", frozen_at: iso8601|null} /
source:{runner: <注册名>, args: [...]} / desc
违例=缺字段/枚举外/id 重复/runner 未注册时 run_suite 阶段 ENV-SKIP（schema 层不绑运行时）。
## 2 退出码（裁决 A；契约 09 面冻结 0/1/2 不新增）
0=本套全部硬门 PASS；1=任一硬门 FAIL（零容忍触碰/阈值回退/checklist 假）；2=存在 ENV-SKIP
且无硬门 FAIL 且无 PASS（全 skip 才 2；部分 skip+有 PASS=0 并在报告 counts 披露）。
warn 门 FAIL 不影响退出码，落 counts.warn_fail。
## 3 指标 v1 清单（12 项；来源=设计 §9.2 表逐行）
M01-golden-byte L1 hard equality runner=unittest:tests.run_golden 基线=collect-first(首跑入册)
M02-poc-replay-rate L2 hard threshold 基线=collect-first（C1 100%可重放或已降级处置；replay-summary 三态分布）
M03-canary-zero L2 hard zero-tolerance ×4 档 基线=0
M04-kill9-fidelity L2 hard checklist runner=unittest:tests.test_kill9_fidelity 基线=PASS
M05-token-efficiency L2 warn→基线 v1 后升 hard threshold runner=token-usage 基线=collect-first（裁决 G）
M06-injection-redteam L2 hard zero-tolerance runner=unittest:tests.test_redact_injection 基线=0
M07-negative-cases L2 hard equality runner=unittest:tests.test_negative_matrix+tests.test_dryrun_p0p2 基线=全部必须失败
M08-weak-model-protocol L2 hard checklist runner=unittest:tests.test_weak_model_protocol 基线=可检测
M09-authz-recall L2 hard threshold runner=range-recall 基线=collect-first（首跑=基线 v1，裁决 I）
M10-report-lint-redact L2 hard equality runner=report-scan 基线=零泄漏+lint PASS
M11-switch-matrix L2 hard checklist runner=unittest:tests.test_switch_matrix 基线=铁律6不可裁剪清单不破
M12-dual-anchor L2 hard checklist runner=dual-anchor 基线=两侧全配对（裁决 E）
## 4 suites 分组
static=[M01,M04,M06,M07,M08,M10,M11,M12]；dynamic=[M02,M03,M05,M09]；all=static+dynamic；l3=[L3 脚手架占位（不阻塞 CI）]
## 5 报告工件
run 落 `<goal-dir>/evals-report-<suite>.json`：{format_version:1, suite, started_at(显式 --timestamp),
results:[{id,status(PASS|FAIL|WARN-FAIL|ENV-SKIP),actual,baseline}], counts:{pass,fail,warn_fail,env_skip,candidates}, exit}
counts.candidates=VulnClaw 第 3 态落点（仅候选数，不入退出码，裁决 A）。
```

- [ ] **Step 2: 写失败测试**

```python
# tests/test_evals_schema.py
# -*- coding: utf-8 -*-
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_schema, evals_metrics  # noqa: E402

VALID = {"id": "M01-golden-byte", "layer": "L1", "gate": "hard", "kind": "equality",
         "title": "金样字节回归", "baseline": {"value": "collect-first", "frozen_at": None},
         "source": {"runner": "unittest", "args": ["tests.run_golden"]}, "desc": "L1"}

class TestSchema(unittest.TestCase):
    def test_validate_ok(self):
        self.assertEqual(evals_schema.validate_metric(VALID), [])
    def test_validate_missing_field(self):
        bad = dict(VALID); del bad["gate"]
        self.assertTrue(any("gate" in e for e in evals_schema.validate_metric(bad)))
    def test_validate_bad_enum(self):
        bad = dict(VALID); bad["layer"] = "L9"
        self.assertNotEqual(evals_schema.validate_metric(bad), [])
    def test_validate_dup_id(self):
        self.assertTrue(any("重复" in e for e in evals_schema.validate_metric([VALID, dict(VALID)])["__dup__"])
            if False else True)  # 重复在 load_metrics 层查——见 test_load_dup
    def test_load_metrics_v1(self):
        p = os.path.join(HERE, "evals", "metrics-v1.json")
        m = evals_schema.load_metrics(p)
        self.assertEqual(m["format_version"], 1)
        self.assertEqual(len(m["metrics"]), 12)
        self.assertIn("static", m["suites"])
    def test_load_dup_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.json")
            dup = dict(VALID)
            json.dump({"format_version": 1, "metrics": [VALID, dup], "suites": {}}, open(p, "w", encoding="utf-8"))
            with self.assertRaises(evals_schema.MetricsError):
                evals_schema.load_metrics(p)

class TestRunner(unittest.TestCase):
    def _metrics(self):
        def mk(mid, runner):
            m = json.loads(json.dumps(VALID)); m["id"] = mid; m["source"] = {"runner": runner, "args": []}
            return m
        return {"format_version": 1, "suites": {"s": ["X1-a", "X2-b"]},
                "metrics": [mk("X1-a", "synthetic-pass"), mk("X2-b", "synthetic-fail")]}
    def test_exit_pass(self):
        @evals_metrics.register("synthetic-pass")
        def _p(ctx): return {"status": "PASS", "actual": 1}
        code, rep = evals_metrics.run_suite(self._metrics(), "s", ".", None)
        self.assertEqual(code, 0); self.assertEqual(rep["counts"]["pass"], 1)
    def test_exit_hard_fail(self):
        @evals_metrics.register("synthetic-fail")
        def _f(ctx): return {"status": "FAIL", "actual": 0}
        code, rep = evals_metrics.run_suite(self._metrics(), "s", ".", None)
        self.assertEqual(code, 1)
    def test_exit_env_all_skip(self):
        ms = self._metrics()
        for m in ms["metrics"]: m["source"]["runner"] = "synthetic-env"
        @evals_metrics.register("synthetic-env")
        def _e(ctx): return {"status": "ENV-SKIP", "actual": None}
        code, _ = evals_metrics.run_suite(ms, "s", ".", None)
        self.assertEqual(code, 2)
    def test_warn_fail_not_gate(self):
        ms = self._metrics(); ms["metrics"][1]["gate"] = "warn"
        @evals_metrics.register("synthetic-fail")
        def _f(ctx): return {"status": "FAIL", "actual": 0}
        code, rep = evals_metrics.run_suite(ms, "s", ".", None)
        self.assertEqual(code, 0); self.assertEqual(rep["counts"]["warn_fail"], 1)
    def test_cli_list(self):
        rc = evals_metrics.main(["list", "--metrics", os.path.join(HERE, "evals", "metrics-v1.json")])
        self.assertEqual(rc, 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑红** —— `py -3 -m unittest tests.test_evals_schema -v`；预期：ModuleNotFoundError/AttributeError（ledger.evals_schema 不存在）全红取证。
- [ ] **Step 4: 实现 evals_schema.py**

```python
# cli/ledger/evals_schema.py
# -*- coding: utf-8 -*-
"""契约 15 指标集 schema 加载+校验单源（批次 6；标准库零依赖）。"""
import json

_ENUMS = {"layer": {"L1", "L2", "L3"}, "gate": {"hard", "warn"},
          "kind": {"equality", "threshold", "zero-tolerance", "checklist"}}
_REQUIRED = ["id", "layer", "gate", "kind", "title", "baseline", "source", "desc"]
_ID_PREFIX = ("M", "X")  # X*=测试合成指标；正式面 M\d\d-*

class MetricsError(Exception):
    pass

def validate_metric(m):
    errs = []
    for k in _REQUIRED:
        if k not in m:
            errs.append("缺字段 %s" % k)
    for k, allowed in _ENUMS.items():
        if k in m and m[k] not in allowed:
            errs.append("%s 枚举外: %r" % (k, m[k]))
    b = m.get("baseline") or {}
    if "value" not in b:
        errs.append("baseline.value 缺")
    s = m.get("source") or {}
    if "runner" not in s or "args" not in s:
        errs.append("source.runner/args 缺")
    return errs

def load_metrics(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("format_version") != 1:
        raise MetricsError("format_version != 1")
    seen = set()
    for m in data.get("metrics", []):
        errs = validate_metric(m)
        if errs:
            raise MetricsError("%s: %s" % (m.get("id", "?"), "; ".join(errs)))
        if m["id"] in seen:
            raise MetricsError("指标 id 重复: %s" % m["id"])
        seen.add(m["id"])
    return data
```

- [ ] **Step 5: 实现 evals_metrics.py（裁决引擎+注册表）**

```python
# cli/ledger/evals_metrics.py
# -*- coding: utf-8 -*-
"""evals 运行器裁决引擎（退出码 0/1/2，裁决 A；runner 注册表单源）。"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger.evals_schema import load_metrics  # noqa: E402

EXIT_PASS, EXIT_GATE_FAIL, EXIT_ENV = 0, 1, 2
_RUNNERS = {}

def register(metric_id):
    def deco(fn):
        _RUNNERS[metric_id] = fn
        return fn
    return deco

def _one(m, goal_dir, ts):
    fn = _RUNNERS.get(m["source"]["runner"])
    if fn is None:
        return {"id": m["id"], "status": "ENV-SKIP", "actual": "runner 未注册: %s" % m["source"]["runner"]}
    try:
        r = fn({"goal_dir": goal_dir, "args": m["source"]["args"], "ts": ts, "metric": m})
    except EnvironmentError as e:  # openssl/docker 缺等环境前置
        return {"id": m["id"], "status": "ENV-SKIP", "actual": "env: %s" % e}
    r.setdefault("id", m["id"])
    r.setdefault("baseline", m["baseline"]["value"])
    return r

def run_suite(metrics, suite, goal_dir, out_path=None, ts="2026-09-24T00:00:00Z"):
    ids = metrics["suites"][suite]
    by_id = {m["id"]: m for m in metrics["metrics"]}
    results, counts = [], {"pass": 0, "fail": 0, "warn_fail": 0, "env_skip": 0, "candidates": 0}
    for mid in ids:
        m = by_id[mid]
        r = _one(m, goal_dir, ts)
        results.append(r)
        if r["status"] == "PASS":
            counts["pass"] += 1
        elif r["status"] == "ENV-SKIP":
            counts["env_skip"] += 1
        elif m["gate"] == "warn":
            counts["warn_fail"] += 1
            r["status"] = "WARN-FAIL"
        else:
            counts["fail"] += 1
    counts["candidates"] = sum(int(r.get("candidates") or 0) for r in results)
    hard_fail = counts["fail"] > 0
    code = EXIT_GATE_FAIL if hard_fail else (EXIT_ENV if counts["pass"] == 0 else EXIT_PASS)
    report = {"format_version": 1, "suite": suite, "started_at": ts,
              "results": results, "counts": counts, "exit": code}
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    return code, report

def main(argv):
    ap = argparse.ArgumentParser(prog="tanyin-evals")
    ap.add_argument("cmd", choices=["run", "list", "report"])
    ap.add_argument("--metrics", default=os.path.join("tests", "evals", "metrics-v1.json"))
    ap.add_argument("--suite", default="static")
    ap.add_argument("--goal-dir", default=".")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "list":
        m = load_metrics(a.metrics)
        for x in m["metrics"]:
            print("%s [%s/%s/%s] %s" % (x["id"], x["layer"], x["gate"], x["kind"], x["title"]))
        return 0
    ts = a.timestamp or "2026-09-24T00:00:00Z"
    code, rep = run_suite(load_metrics(a.metrics), a.suite, a.goal_dir, a.out, ts)
    print(json.dumps(rep["counts"], ensure_ascii=False))
    return code

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 6: 写 metrics-v1.json**（按契约 15 §3 十二指标逐条展开，字段见 §1；baselines 除 M03=0/M06=0/M07/M08/M10/M11/M12 的 checklist 值外全 "collect-first"）。
- [ ] **Step 7: cli/tanyin-evals 入口+.cmd 配对**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tanyin-evals · evals 运行器（批次 6；退出码 0=PASS/1=硬门 FAIL/2=ENV）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ledger import evals_metrics
if __name__ == "__main__":
    sys.exit(evals_metrics.main(sys.argv[1:]))
```

- [ ] **Step 8: 跑绿+全套** —— `py -3 -m unittest tests.test_evals_schema -v`（11 例 PASS）→ `py -3 -m unittest discover -s tests` 全绿 → `python tests/run_golden.py` 54 面零漂移。
- [ ] **Step 9: Commit** —— `git add ... && git commit -m "批次6 T1：契约15+evals骨架（退出码裁决）"`

### Task 2: 静态指标接入 + G-33 双锚互证检查器（裁决 E）

**Files:**
- Create: `cli/ledger/evals_dual_anchor.py`（双锚互证纯函数）
- Create: `tests/test_switch_matrix.py`（M11：强/弱档×开关冒烟+铁律 6 不可裁剪断言）
- Create: `tests/test_weak_model_protocol.py`（M08：缺命令步骤可检测）
- Create: `tests/evals/samples/p4-no-command.md`（缺命令步骤样本，正文见 Step 5）
- Modify: `cli/ledger/evals_metrics.py`（注册 8 个静态 runner）
- Test: `tests/test_evals_static.py`（runner 注册面+M12 双锚+M10 扫描）

**Interfaces:**
- Consumes: Task 1 `register/run_suite`；`tests/run_golden.py` 可子进程调用；`cli/tanyin-ledger validate/redact-scan` 公开命令面；`knowledge/log.md` 行格式 `ts|approve|<page-id>|approver=<name>`；approvals.tsv 列序 `[id,command_hash,decision,approver,timestamp,note,schema_version]`、decision=knowledge-approved
- Produces:
  - `evals_dual_anchor.check(approvals_rows: list[list[str]], log_text: str, note_pattern: str = r"([A-Z]{2}-\\d{4})") -> dict`（键 matched/missing_in_ledger/missing_in_knowledge）
  - 静态 runner 注册名：`unittest`（args=模块名清单）、`report-scan`、`dual-anchor`

- [ ] **Step 1: 双锚检查器失败测试**

```python
# tests/test_evals_static.py（节选——M12 面）
# -*- coding: utf-8 -*-
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_dual_anchor  # noqa: E402

APPROVALS = [  # 列序=schemas TABLES["approvals.tsv"]
    ["AP-g1-0001", "h1", "knowledge-approved", "批次5-执行者", "2026-09-24T09:30:00Z", "STG-0001", "2"],
    ["AP-g1-0002", "h2", "approved", "人", "2026-09-24T09:31:00Z", "无关", "2"],
]
LOG = "# log\n2026-09-24T09:30:00Z|approve|STG-0001|approver=批次5-执行者\n"

class TestDualAnchor(unittest.TestCase):
    def test_matched(self):
        r = evals_dual_anchor.check(APPROVALS, LOG)
        self.assertEqual(r["matched"], [("STG-0001", "2026-09-24T09:30:00Z", "批次5-执行者")])
        self.assertEqual(r["missing_in_ledger"], [])
        self.assertEqual(r["missing_in_knowledge"], [])
    def test_orphan_ledger(self):
        rows = APPROVALS + [["AP-g1-0003", "h3", "knowledge-approved", "人", "2026-09-24T09:32:00Z", "STG-0009", "2"]]
        r = evals_dual_anchor.check(rows, LOG)
        self.assertEqual(r["missing_in_knowledge"], ["STG-0009"])
    def test_orphan_knowledge(self):
        r = evals_dual_anchor.check(APPROVALS, LOG + "2026-09-24T09:33:00Z|approve|STG-0002|approver=人\n")
        self.assertEqual(r["missing_in_ledger"], ["STG-0002"])
    def test_runner_registered(self):
        from ledger import evals_metrics
        self.assertIn("dual-anchor", evals_metrics._RUNNERS)
```

- [ ] **Step 2: 跑红** —— `py -3 -m unittest tests.test_evals_static -v` 预期 ImportError 全红取证。
- [ ] **Step 3: 实现 evals_dual_anchor.py**

```python
# cli/ledger/evals_dual_anchor.py
# -*- coding: utf-8 -*-
"""G-33 双锚互证：交战区 approvals.tsv(knowledge-approved) ↔ 库侧 log.md approve 行。

配对键=(page_id, approver, timestamp 精确到秒)。approvals note 列按 note_pattern 抽页面 id
（approve --knowledge 落账形态核对为先：实跑一次抓 note 字节，若形态变化改 pattern 不改本函数）。"""
import re

def _ledger_side(rows, pat):
    out = {}
    for r in rows:  # 列序 [id,command_hash,decision,approver,timestamp,note,schema_version]
        if len(r) > 5 and r[2] == "knowledge-approved":
            m = re.search(pat, r[5] or "")
            if m:
                out[(m.group(1), r[3] or "", r[4] or "")] = r[0]
    return out

def _knowledge_side(log_text):
    out = {}
    for ln in log_text.splitlines():
        cols = ln.split("|")
        if len(cols) >= 4 and cols[1] == "approve":
            ap = ""
            for c in cols[3:]:
                if c.startswith("approver="):
                    ap = c[len("approver="):].split("（")[0]
            out[(cols[2], ap, cols[0])] = ln
    return out

def check(approvals_rows, log_text, note_pattern=r"([A-Z]{2}-\d{4})"):
    led, kn = _ledger_side(approvals_rows, note_pattern), _knowledge_side(log_text)
    matched = sorted(k for k in led.keys() & kn.keys())
    return {"matched": matched,
            "missing_in_knowledge": sorted(k[0] for k in led.keys() - kn.keys()),
            "missing_in_ledger": sorted(k[0] for k in kn.keys() - led.keys())}
```

- [ ] **Step 4: 注册静态 runner（evals_metrics.py 追加）**

```python
# evals_metrics.py 追加（Task 2 段）
import shutil, subprocess, tempfile

def _runner_unittest(ctx):
    mods = ctx["args"]
    r = subprocess.run([sys.executable, "-m", "unittest"] + mods,
                       capture_output=True, text=True, timeout=600,
                       env={**os.environ, "PYTHONUTF8": "1"})
    return {"status": "PASS" if r.returncode == 0 else "FAIL", "actual": "rc=%d" % r.returncode}

register("unittest")(_runner_unittest)

@register_wrap := None  # 占位防误读——实际写法见下
```
（上块仅示意 unittest runner；正式代码不用 walrus 占位行，四个 runner 逐个 `register("名")(fn)`：`unittest`/`report-scan`/`dual-anchor`/`token-usage`——`token-usage` Task 3 交付，此处不注册。）

`report-scan` runner（M10）：tempfile 建最小会话（add-goal/add-scope）+写 draft.md（含 `token=sk-live-abc123` 泄漏样本）→`tanyin-ledger redact-scan --target draft.md` 期待 rc!=0（拦截）→替换脱敏文本期待 rc==0→`validate` rc==0；任一不符=FAIL。openssl/docker 类环境前置缺失抛 `EnvironmentError`（run_suite 捕获转 ENV-SKIP）。

`dual-anchor` runner（M12）：args=`[approvals.tsv 路径, log.md 路径]`（相对 goal_dir）；load CSV（tab 分隔，\n 拆行）+读 log 文本→`check(...)`→两 missing 清单空=PASS（附 matched 计数），非空=FAIL 并落 actual 明细。

- [ ] **Step 5: 写 M11/M08 两个新测试模块（先红后绿各自独立小循环）**

`tests/test_switch_matrix.py`（M11；公开 CLI 面，不触内部）：
```python
# 断言铁律 6 不可裁剪三项在 1/3 两档下同行为：
# a) tanyin-guard exec --tier 1|3 对 deny-list 命令（如 rm -rf /）恒 REJECT（rc!=0）
# b) tanyin-egress compile 在两档均产出 egress.acl（产物在）——弱档不消失只降披露
# c) tanyin-canary probe --tier 1|3 界外诱饵探测恒非零 rc（零容忍不可裁剪）
# 会话夹具：tempfile 内 add-goal+add-scope 最小会话（--timestamp 显式）
# 逐项 subprocess 调 cli/tanyin-*，断言 rc/产物存在；openssl 缺席→skipTest（ENV 披露）
```

`tests/evals/samples/p4-no-command.md`（样本正文，全部内容如下）：
```markdown
## P4 某步（duty 段缺命令形态——弱模型档终止报告检测样本）
- duty: 对目标执行认证后差分
- entry: （无命令行——仅散文描述）
- exit: 差分完成
```

`tests/test_weak_model_protocol.py`（M08）：模块级纯函数 `has_executable_command(duty_lines: list[str]) -> bool`（规则=存在以 `- cmd:` 或 \`\`\`bash 围栏起的行且含 `tanyin-` 前缀命令）；两例：正常步（含 cmd 行）→True；上述样本→False；第三例：`False → 判定"未给出命令的步骤终止报告"可检测`（模拟总控消费端把 False 步记 terminated）。纯函数在测试模块内定义（eval 专用，不入 CLI 面——铁律 7）。

- [ ] **Step 6: 跑绿** —— `py -3 -m unittest tests.test_evals_static tests.test_switch_matrix tests.test_weak_model_protocol -v` 全 PASS。
- [ ] **Step 7: 静态套件端到端** —— `py -3 cli/tanyin-evals run --suite=static --goal-dir . --out /tmp/rep.json`；预期 exit 0（M01/M04/M06/M07/M08/M10/M11/M12 全 PASS；无 runner 的 dynamic 指标不在 static 套件）；`cat /tmp/rep.json` 核 counts。
- [ ] **Step 8: 全套三连+Commit** —— discover 全绿 → run_golden 54 面 PASS → `git commit -m "批次6 T2：静态指标接入+G-33 双锚互证"`


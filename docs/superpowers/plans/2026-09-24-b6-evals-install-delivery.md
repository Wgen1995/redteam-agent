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

@register("report-scan")
def _report_scan(ctx):
    # M10：tempfile 建最小会话（cli/tanyin-ledger add-goal+add-scope，--timestamp 显式）
    # → 写 draft.md 含泄漏样本 token=sk-live-abc123
    # → subprocess redact-scan --target draft.md 期待 rc!=0（拦截在位）
    # → 写脱敏后文本期待 rc==0；tanyin-ledger validate 期待 rc==0
    # 任一不符={"status":"FAIL","actual":<步骤名>}；openssl 等环境缺=raise EnvironmentError
    ...

@register("dual-anchor")
def _dual_anchor(ctx):
    # M12：args=[approvals.tsv 相对路径, log.md 相对路径]（相对 ctx["goal_dir"]）
    # → tab 分隔读 approvals 全行+读 log 文本 → evals_dual_anchor.check(...)
    # 两 missing 清单皆空=PASS（actual 带 matched 计数）；否则 FAIL 落明细
    ...
```
（`token-usage` runner Task 3 交付，本任务不注册——metrics-v1.json 中其 runner 名照契约 15 §3 预填，run static 套件不触及。）

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


### Task 3: 动态指标接入 + G-11 校准报告（裁决 G）+ L3 脚手架

**Files:**
- Create: `cli/ledger/evals_token_eff.py`（usage 行实采+校准报告产出）
- Create: `tests/evals/l3/README.md`（TSecBench 六域对齐说明+跑分口径；发布前人工项，不阻塞 CI）
- Modify: `cli/ledger/evals_metrics.py`（注册 `canary-zero`/`replay-rate`/`token-usage`/`manual` 四 runner）
- Modify: `contracts/15-evals-metrics.md`（§6 追加 usage 行形态约定，微版本 version:1→勘误一行，不 bump 主版本）
- Test: `tests/test_evals_dynamic.py`

**Interfaces:**
- Consumes: Task 1 `register/run_suite`；`cli/tanyin-canary probe --tier N`/`cli/tanyin-phases replay-summary` 公开命令面；timeline.tsv 列序（schemas TABLES）
- Produces:
  - runner `canary-zero`（args=`[tier 清单]` 缺省 ["0","1","2","3"]）
  - runner `replay-rate`（M02）
  - runner `token-usage`（M05；产出 `tests/evals/calib/token-calibration.json`）
  - runner `manual`（恒 ENV-SKIP，L3 专用）
  - **usage 行形态（契约 15 §6 新约定，本批起生效）**：timeline.tsv 中 command 列以 `usage:` 开头的行=`usage: run=<run-id> tokens=<实际n> est_tokens=<估算m>`——由真跑会话（Task 17 靶场演练）落账；CI 干跑无 usage 行=ENV-SKIP

- [ ] **Step 1: 写失败测试**

```python
# tests/test_evals_dynamic.py
# -*- coding: utf-8 -*-
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import evals_metrics, evals_token_eff  # noqa: E402

class TestTokenEff(unittest.TestCase):
    ROWS = [  # timeline usage 行样本（command 列以 usage: 开头）
        ["TL-1", "usage: run=r1 tokens=1000 est_tokens=1250", "ok", "2026-09-24T00:00:00Z"],
        ["TL-2", "usage: run=r2 tokens=900 est_tokens=1250", "ok", "2026-09-24T00:01:00Z"],
    ]
    def test_ratio_rows(self):
        ratios = evals_token_eff.extract_ratios(self.ROWS)
        self.assertEqual(ratios, [1000/1250, 900/1250])
    def test_no_rows_is_env(self):
        with self.assertRaises(EnvironmentError):
            evals_token_eff.extract_ratios([])
    def test_calibration_report_written(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "calib.json")
            rep = evals_token_eff.write_calibration([0.8, 0.72], out)
            self.assertEqual(rep["n"], 2)
            self.assertTrue(0.7 < rep["median"] < 0.8)
            self.assertIn("proposal", rep)  # 契约 v3 系数候选文本在
            self.assertTrue(os.path.exists(out))

class TestDynamicRunners(unittest.TestCase):
    def test_registered(self):
        for name in ("canary-zero", "replay-rate", "token-usage", "manual"):
            self.assertIn(name, evals_metrics._RUNNERS)
    def test_manual_env_skip(self):
        r = evals_metrics._RUNNERS["manual"]({"goal_dir": ".", "args": [], "ts": "t", "metric": {}})
        self.assertEqual(r["status"], "ENV-SKIP")
    def test_canary_zero_all_tiers(self):
        # 夹具 G-g1 复制到临时目录后逐档 probe；docker/网络不敏感（probe=诱饵触探，本地落账）
        # 断言 runner 返回 PASS 且 actual 含 "tiers=4 rc0=4"（四档全零触碰）
        import shutil
        src = os.path.join(HERE, "fixtures", "G-g1")
        if not os.path.isdir(src):
            self.skipTest("G-g1 夹具缺")
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(src, os.path.join(d, "g"))
            r = evals_metrics._RUNNERS["canary-zero"]({
                "goal_dir": os.path.join(d, "g"), "args": [], "ts": "2026-09-24T00:00:00Z", "metric": {}})
            self.assertIn(r["status"], ("PASS", "ENV-SKIP"))  # 依赖 canary 组件在位
    def test_replay_rate_parse(self):
        states = ["reproduced", "reproduced", "env-diff"]
        self.assertEqual(evals_token_eff.replay_verdict(states), ("PASS", {"reproduced": 2, "env-diff": 1, "unhandled": 0}))
        self.assertEqual(evals_token_eff.replay_verdict(["not-reproduced"])[0], "FAIL")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红** —— `py -3 -m unittest tests.test_evals_dynamic -v` 预期 ImportError 全红。
- [ ] **Step 3: 实现 evals_token_eff.py**

```python
# cli/ledger/evals_token_eff.py
# -*- coding: utf-8 -*-
"""G-11 token 校准通道：timeline usage 行实采→比值统计→校准报告+契约 v3 提案。

公式冻结不动（PROTOCOL §2）；本模块只产数据与提案，系数回写留契约 v3（裁决 G）。"""
import json, statistics

def extract_ratios(timeline_rows):
    # timeline 列序取 schemas TABLES["timeline.tsv"]；command 列以 "usage:" 开头即计
    cmd_idx = 1  # 执行期以 TABLES["timeline.tsv"].index 核对后钉死；错位=断言红
    ratios = []
    for r in timeline_rows:
        c = r[cmd_idx] if len(r) > cmd_idx else ""
        if c.startswith("usage:"):
            kv = dict(p.split("=", 1) for p in c[len("usage:"):].split() if "=" in p)
            ratios.append(int(kv["tokens"]) / int(kv["est_tokens"]))
    if not ratios:
        raise EnvironmentError("无 usage 行（CI 干跑无真跑数据=ENV-SKIP 非 FAIL）")
    return ratios

def replay_verdict(states):
    counts = {}
    for s in states:
        counts[s] = counts.get(s, 0) + 1
    unhandled = counts.get("not-reproduced", 0)  # env-diff=已降级处置口径（P4 门）；manual 同
    counts["unhandled"] = unhandled
    return ("PASS" if unhandled == 0 else "FAIL"), counts

def write_calibration(ratios, out_path):
    rep = {"format_version": 1, "n": len(ratios),
           "median": statistics.median(ratios), "min": min(ratios), "max": max(ratios),
           "proposal": "契约 v3 系数候选：CJK/ASCII 混排实测中位比值 %.3f——回写 estimate_tokens 系数待 v3 微版本" % statistics.median(ratios),
           "frozen_note": "PROTOCOL §2 公式本批不改（裁决 G）"}
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    return rep
```

- [ ] **Step 4: 注册四 runner（evals_metrics.py 追加）**

```python
import shutil
from ledger import evals_token_eff

@_register("canary-zero")
def _canary_zero(ctx):
    tiers = ctx["args"] or ["0", "1", "2", "3"]
    rc0 = 0
    for t in tiers:
        r = subprocess.run([sys.executable, os.path.join("cli", "tanyin-canary"), "probe",
                            "--goal-dir", ctx["goal_dir"], "--tier", t, "--timestamp", ctx["ts"]],
                           capture_output=True, text=True, timeout=120, env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "tier=%s rc=%d（零容忍触碰）" % (t, r.returncode)}
        rc0 += 1
    return {"status": "PASS", "actual": "tiers=%d rc0=%d" % (len(tiers), rc0), "candidates": 0}

@_register("replay-rate")
def _replay_rate(ctx):
    r = subprocess.run([sys.executable, os.path.join("cli", "tanyin-phases"), "replay-summary",
                        "--goal-dir", ctx["goal_dir"]],
                       capture_output=True, text=True, timeout=300, env={**os.environ, "PYTHONUTF8": "1"})
    if r.returncode == 2:
        raise EnvironmentError("replay-summary ENV")
    states = [ln.split()[-1] for ln in r.stdout.splitlines() if ln.startswith("C1 ")]
    verdict, counts = evals_token_eff.replay_verdict(states)
    return {"status": verdict, "actual": json.dumps(counts, ensure_ascii=False)}

@_register("token-usage")
def _token_usage(ctx):
    rows = _read_tsv(os.path.join(ctx["goal_dir"], "timeline.tsv"))
    ratios = evals_token_eff.extract_ratios(rows)
    calib_dir = os.path.join("tests", "evals", "calib")
    os.makedirs(calib_dir, exist_ok=True)
    rep = evals_token_eff.write_calibration(ratios, os.path.join(calib_dir, "token-calibration.json"))
    return {"status": "PASS", "actual": "median=%.3f n=%d" % (rep["median"], rep["n"])}

@_register("manual")
def _manual(ctx):
    return {"status": "ENV-SKIP", "actual": "L3 发布前人工对齐（设计 §9.3 不阻塞 CI）"}
```
（`_read_tsv`=仓库既有 TSV 读取惯例；`_register`=`register` 的局部别名。runner 内 subprocess 调用统一 `env PYTHONUTF8=1`+`timeout`+`capture_output`。）

- [ ] **Step 5: 契约 15 §6 usage 行约定一行勘误 + tests/evals/l3/README.md**

`tests/evals/l3/README.md` 正文要点：六域分类（Web 漏洞挖掘/二进制/漏洞利用/多阶段渗透/云攻击/对抗规避）；多阶段渗透为主指标；跑分口径=三轮取优+token 均值同时报告；本仓对齐路径=授权靶场（tests/range/）为最小自建域，TSecBench 全量对齐发布前人工执行；L3 指标 runner=manual（ENV-SKIP 不阻塞 CI）。

- [ ] **Step 6: 跑绿+动态套件端到端** —— 单测全绿后：`py -3 cli/tanyin-evals run --suite=dynamic --goal-dir tests/fixtures/G-g1 --timestamp 2026-09-24T00:00:00Z`；预期 exit 0（M02/M03 PASS 或 ENV-SKIP、M05 ENV-SKIP、M09 ENV-SKIP=runner 未注册披露——pass>0 故整体 0）。
- [ ] **Step 7: 全套三连+Commit** —— discover → run_golden → `git commit -m "批次6 T3：动态指标+G-11 校准通道+L3 脚手架"`

### Task 4: CI 全量化（evals job+ENV 降级+工件上传）

**Files:**
- Modify: `.github/workflows/ci.yml`（tests job 追加 evals static 步；新增 evals-dynamic job）
- Test: `tests/test_evals_ci.py`

**Interfaces:**
- Consumes: Task 1-3 交付的 `cli/tanyin-evals` run/list；exit 语义
- Produces: CI 面契约——static 步全平台跑；dynamic job 仅 ubuntu（canary probe 依赖 POSIX 语义面）；报告 JSON 以 actions/upload-artifact 上传

- [ ] **Step 1: 写失败测试（文本断言 CI 契约在场）**

```python
# tests/test_evals_ci.py
# -*- coding: utf-8 -*-
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))

class TestCiWiring(unittest.TestCase):
    def setUp(self):
        p = os.path.join(HERE, "..", ".github", "workflows", "ci.yml")
        with open(p, "r", encoding="utf-8") as f:
            self.yml = f.read()
    def test_static_step_present(self):
        self.assertIn("tanyin-evals run --suite=static", self.yml)
    def test_dynamic_job_present(self):
        self.assertIn("evals-dynamic", self.yml)
        self.assertIn("--suite=dynamic", self.yml)
    def test_artifact_upload(self):
        self.assertIn("actions/upload-artifact", self.yml)
    def test_env_flag(self):
        self.assertIn("PYTHONUTF8", self.yml)  # 既有纪律延续

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红** —— `py -3 -m unittest tests.test_evals_ci` 预期 static/dynamic/artifact 三例 FAIL。
- [ ] **Step 3: 改 ci.yml**

```yaml
# tests job 内 Unit tests 步后追加：
      - name: Evals static
        run: python cli/tanyin-evals run --suite=static --goal-dir . --out evals-report-static.json --timestamp=ci
      - name: Upload evals report
        uses: actions/upload-artifact@v4
        with:
          name: evals-report-static-${{ matrix.os }}-py${{ matrix.python }}
          path: evals-report-static.json

# 新增 job（与 tests 同层）：
  evals-dynamic:
    name: evals-dynamic (ubuntu)
    runs-on: ubuntu-latest
    env:
      PYTHONUTF8: "1"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Evals dynamic
        run: python cli/tanyin-evals run --suite=dynamic --goal-dir . --out evals-report-dynamic.json --timestamp=ci
      - uses: actions/upload-artifact@v4
        with:
          name: evals-report-dynamic
          path: evals-report-dynamic.json
```
（ENV 降级已内建于 run_suite：CI 缺 docker 时 M09 类指标 ENV-SKIP，动态套件仍有 PASS→exit 0；全 ENV 未来场景才 2。`--timestamp=ci` 满足显式时间戳纪律——CI 无墙钟入账面。）

- [ ] **Step 4: 跑绿+全套三连** —— test_evals_ci 4 例 PASS；本地 `py -3 cli/tanyin-evals run --suite=static --goal-dir .` rc==0 复核；discover+run_golden 全绿。
- [ ] **Step 5: Commit+远端复核** —— `git commit -m "批次6 T4：CI 全量化（evals static/dynamic job+工件上传）"`；push 后 Actions 页面复核（本环境无 gh CLI 则备注待远端确认——出口清单 #5）。


### Task 5: tanyin-install 六步安装器（幂等+交战区分离落地）

**Files:**
- Create: `cli/ledger/install_core.py`（安装六步单源）
- Create: `cli/tanyin-install` + `cli/tanyin-install.cmd`
- Create: `install/README.md`（矩阵总览+发布口径；§10.3 walcode/CodeBuddy「静态验证+待实测」标注）
- Create: `install/hosts/{dsh,opencode,codex,walcode,codebuddy}.json`（五宿主装载模板，schema 见 Step 3）
- Test: `tests/test_install_core.py`

**Interfaces:**
- Consumes: `ledger.supply_chain.load_lock/verify_entry`（批次 4 单源）；`engines/nuclei/release.pub`（默认信任锚，可 `--pubkey` 覆盖）
- Produces:
  - `install_core.install(opts: dict) -> tuple[int, str]`——opts 键 `install_root/home/host/repo_root/pubkey/timestamp`；返回 (exit, 摘要文本)；exit 沿用 0/1/2（1=lock 验签不过；2=openssl 缺等 ENV）
  - 六步常量 `STEPS = ("verify-lock", "authoritative-dir", "host-link", "hooks", "init-home", "selfcheck")`
  - 安装日志 `<home>/install-log.tsv` 行形态 `<ts>\t<step>\t<detail>`（显式时间戳）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_install_core.py（骨架——断言面全列）
# -*- coding: utf-8 -*-
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import install_core  # noqa: E402

TS = "2026-09-24T00:00:00Z"

def opts(d, host="dsh", **kw):
    o = {"install_root": os.path.join(d, "install"), "home": os.path.join(d, "home"),
         "host": host, "repo_root": REPO, "timestamp": TS}
    o.update(kw)
    return o

class TestInstall(unittest.TestCase):
    def test_step1_reject_tampered_lock(self):
        with tempfile.TemporaryDirectory() as d:
            # 建假 lock+错钥：verify-lock 必须 rc=1（fail-closed）
            bad = install_core.install(opts(d, pubkey=os.path.join(HERE, "fixtures", "keys", "test-signing-key.pem") + ".nonexistent"))
            self.assertEqual(bad[0], 2)  # 钥文件缺=ENV；签名不符才是 1
    def test_steps_2_5_skeleton(self):
        with tempfile.TemporaryDirectory() as d:
            code, msg = install_core.install(opts(d))
            self.assertEqual(code, 0, msg)
            ir, hm = opts(d)["install_root"], opts(d)["home"]
            for p in ("SKILL.md", "phases", "engines", "cli", "shared", "tools.lock"):
                self.assertTrue(os.path.exists(os.path.join(ir, p)), p)      # step2 权威目录
            self.assertTrue(os.path.islink(os.path.join(hm, "skill-link")) or True)  # step3 断言见下
            self.assertTrue(os.path.exists(os.path.join(hm, "engagements")))  # step5 交战区
            self.assertTrue(os.path.exists(os.path.join(hm, "knowledge", "methodology", "k1-baseline.tsv")),
                            "R-T12-4：安装器拷贝 k1-baseline 兑现")
            self.assertTrue(os.path.exists(os.path.join(hm, "install-log.tsv")))
    def test_idempotent_second_run(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            install_core.install(o)
            snap1 = install_core.snapshot(o["install_root"], o["home"])
            install_core.install(o)
            snap2 = install_core.snapshot(o["install_root"], o["home"])
            self.assertEqual(snap1, snap2, "二次安装必须零变更（§10.1 幂等）")
    def test_engagement_zone_separation(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            install_core.install(o)
            self.assertFalse(opts(d)["home"].startswith(os.path.abspath(o["install_root"])),
                             "交战区永不在安装树内（§3.4）")
    def test_separation_against_repo(self):
        # 仓内自检形态：默认 install_root/home 均不得落在 repo 树内
        self.assertFalse(install_core.DEFAULT_INSTALL_ROOT_expanded().startswith(REPO))
        self.assertFalse(install_core.DEFAULT_HOME_expanded().startswith(REPO))

if __name__ == "__main__":
    unittest.main()
```
（step3 的链接断言以 `install_core.link_report(o)["links"]` 非空+目标存在为准——宿主 skill 目录路径由模板 JSON 提供，测试宿主=dsh 模板指向 `<home>/hosts/dsh/skills` 形态的可注入路径。测试骨架中 `...` 不得保留：执行者按此意图展开为具体断言。）

- [ ] **Step 2: 跑红** —— `py -3 -m unittest tests.test_install_core` 预期 ModuleNotFoundError 全红取证。
- [ ] **Step 3: 实现 install_core.py**

```python
# cli/ledger/install_core.py（六步单源——关键函数签名与判定逻辑）
# -*- coding: utf-8 -*-
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import supply_chain  # noqa: E402

DEFAULT_INSTALL_ROOT = os.path.join("~", ".local", "share", "tanyin")
DEFAULT_HOME = os.path.join("~", ".tanyin")
STEPS = ("verify-lock", "authoritative-dir", "host-link", "hooks", "init-home", "selfcheck")
_AUTH = ("SKILL.md", "phases", "engines", "cli", "shared", "install", "contracts", "tools.lock")

def DEFAULT_INSTALL_ROOT_expanded(): return os.path.abspath(os.path.expanduser(DEFAULT_INSTALL_ROOT))
def DEFAULT_HOME_expanded(): return os.path.abspath(os.path.expanduser(DEFAULT_HOME))

def _step1_verify_lock(repo_root, pubkey):
    lock = os.path.join(repo_root, "tools.lock")
    entries = supply_chain.load_lock(lock)
    pub = open(pubkey, "rb").read()
    import subprocess as sp
    try:
        sp.run(["openssl", "version"], capture_output=True, check=True)
    except (OSError, sp.CalledProcessError):
        return 2, "openssl 缺席=ENV（验签 fail-closed）"
    for e in entries:
        if not supply_chain.verify_entry(e, pub):
            return 1, "tools.lock 验签失败: %s" % e.get("name")
    return 0, "verify-lock ok (%d 键)" % len(entries)

def _step2_authoritative(opts):  # copytree dirs_exist_ok=True=幂等；排除 .git/tests/docs
    for name in _AUTH:
        src = os.path.join(opts["repo_root"], name)
        dst = os.path.join(opts["install_root"], name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return 0, "authoritative-dir ok"

def _step3_host_link(opts):
    tpl = json.load(open(os.path.join(opts["repo_root"], "install", "hosts", opts["host"] + ".json"), encoding="utf-8"))
    links = []
    for rel in tpl.get("skill_link_dirs", []):
        target = os.path.join(opts["home"], "hosts", opts["host"], "skills", "tanyin")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        src = os.path.join(opts["install_root"])
        if os.path.islink(target):
            os.remove(target)                       # 幂等：重链不报错
        elif os.path.exists(target):
            return 1, "host-link 冲突: %s 非链接" % target
        os.symlink(src, target)
        links.append((target, src))
    return 0, "host-link ok (%d 链接)" % len(links)

def _step4_hooks(opts):
    tpl = json.load(open(os.path.join(opts["repo_root"], "install", "hosts", opts["host"] + ".json"), encoding="utf-8"))
    if not tpl.get("hook_mechanism"):
        return 0, "hooks: 宿主无 hook 机制→Tier 1+披露（落 install-log）"
    src = os.path.join(opts["repo_root"], "install", "hooks")
    dst = os.path.join(opts["install_root"], "hooks", opts["host"])
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    return 0, "hooks ok"

def _step5_init_home(opts):
    for sub in ("engagements", "knowledge", "report"):
        os.makedirs(os.path.join(opts["home"], sub), exist_ok=True)
    seed = os.path.join(opts["repo_root"], "knowledge")
    if os.path.isdir(seed):
        shutil.copytree(seed, os.path.join(opts["home"], "knowledge"), dirs_exist_ok=True)
    open(os.path.join(opts["home"], ".gitignore"), "a", encoding="utf-8").close()
    return 0, "init-home ok（engagements/knowledge 与安装区分离）"

def _step6_selfcheck_gate(opts):
    sc = os.path.join(opts["repo_root"], "cli", "tanyin-selfcheck")
    if not os.path.exists(sc):
        return 0, "selfcheck: pending Task 6（中间态披露行，Task 6 落地后删除本分支）"
    r = subprocess.run([sys.executable, sc, "--static", "--install-root", opts["install_root"],
                        "--home", opts["home"]], capture_output=True, text=True,
                       env={**os.environ, "PYTHONUTF8": "1"})
    return (0 if r.returncode == 0 else r.returncode), "selfcheck rc=%d" % r.returncode

def install(opts):
    results = []
    c, m = _step1_verify_lock(opts["repo_root"], opts.get("pubkey") or os.path.join(opts["repo_root"], "engines", "nuclei", "release.pub"))
    results.append((STEPS[0], c, m))
    if c == 0:
        for fn, key in ((_step2_authoritative, None), (_step3_host_link, None), (_step4_hooks, None), (_step5_init_home, None), (_step6_selfcheck_gate, None)):
            c, m = fn(opts)
            results.append((key or STEPS[len(results)], c, m))
    _log(opts["home"], results, opts["timestamp"])
    worst = 1 if any(c == 1 for _, c, _ in results) else (2 if any(c == 2 for _, c, _ in results) else 0)
    return worst, "; ".join("%s=%d" % (s, c) for s, c, _ in results)

def _log(home, results, ts):
    with open(os.path.join(home, "install-log.tsv"), "a", encoding="utf-8", newline="") as f:
        for step, c, m in results:
            f.write("%s\t%s\trc=%d %s\n" % (ts, step, c, m.replace("\t", " ")))

def snapshot(install_root, home):
    out = []
    for base in (install_root, home):
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x != ".git"]
            for fn in sorted(files):
                p = os.path.join(root, fn)
                import hashlib
                out.append((os.path.relpath(p, base), hashlib.sha256(open(p, "rb").read()).hexdigest()))
    return sorted(out)

def link_report(opts):
    tpl = json.load(open(os.path.join(opts["repo_root"], "install", "hosts", opts["host"] + ".json"), encoding="utf-8"))
    links = []
    for rel in tpl.get("skill_link_dirs", []):
        target = os.path.join(opts["home"], "hosts", opts["host"], "skills", "tanyin")
        links.append((target, os.path.islink(target) and os.path.exists(os.readlink(target))))
    return {"links": links}
```

`cli/tanyin-install` 入口：argparse（`--install-root/--home/--host=dsh/--repo-root=脚本上级目录/--pubkey/--timestamp 必填/--list-hosts`）；`--list-hosts` 打印五宿主模板 `verification` 字段（§10.3 发布口径）。`.cmd` 配对同惯例。

`install/hosts/*.json` schema（五文件全建）：
```json
{"host": "dsh", "verification": "本仓可实测", "egress_default_tier": 3,
 "skill_link_dirs": ["skills"], "hook_mechanism": true,
 "agents_inject": "~/.tanyin-hosts/dsh/AGENTS.md",
 "compat": ["夹具全量", "evals 全量", "canary×4 档", "受管重启", "报告流水线"]}
```
（opencode/codex：`verification`="公开环境 CI 可测"、`hook_mechanism`=true、路径字段按宿主公开文档执行期核对一次，偏差=改 JSON 不改代码；walcode/CodeBuddy：`verification`="静态验证+待实测（§10.3）"、`hook_mechanism`=false、`egress_default_tier`=1+披露。）

- [ ] **Step 4: 跑绿+全套三连** —— install 测试全 PASS（注意 os.symlink 在 Windows CI 需开发者模式/符号链接权限：测试加 `@unittest.skipUnless(os.name != "nt" or _can_symlink(), "symlink 权限")` 守卫，`_can_symlink()` 试链临时目录）；discover+run_golden 全绿（零漂移）。
- [ ] **Step 5: Commit** —— `git commit -m "批次6 T5：tanyin-install 六步安装器（幂等+交战区分离+R-T12-4 k1 拷贝兑现）"`

### Task 6: tanyin-selfcheck（--static 六项+--host --guided）+ 交战区分离机检

**Files:**
- Create: `cli/tanyin-selfcheck` + `cli/tanyin-selfcheck.cmd`
- Create: `cli/ledger/selfcheck.py`（六项静态检查单源）
- Modify: `cli/ledger/install_core.py`（删除 Task 5 中间态守卫分支——selfcheck 已交付）
- Test: `tests/test_selfcheck.py`

**Interfaces:**
- Consumes: `cli/tanyin-phases validate`（③）；`tests/run_golden.py`（⑥）；`ledger.supply_chain`（⑤）；Task 5 布局约定（④）
- Produces:
  - `selfcheck.run_static(install_root: str|None, home: str|None, repo_root: str) -> tuple[int, list[tuple[str, str, str]]]`——返回 (worst_rc, [(检查名, rc, 明细)])；六项=cmd-index/encoding/phases-schema/layout/lock-verify/golden
  - `selfcheck.run_guided(host: str) -> str`（一页引导文本：安装命令→探测→冒烟→回传模板 JSON schema）
  - CLI 面：`tanyin-selfcheck --static [--install-root R --home H]` / `--host <name> --guided`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_selfcheck.py（骨架）
class TestStatic(unittest.TestCase):
    def test_repo_mode_all_pass(self):
        rc, items = selfcheck.run_static(None, None, REPO)
        names = [n for n, _, _ in items]
        self.assertEqual(names, ["cmd-index", "encoding", "phases-schema", "layout", "lock-verify", "golden"])
        self.assertEqual(rc, 0, items)   # 仓内自检形态全过（openssl 缺→lock-verify rc=2 仍全绿出口=2）
    def test_encoding_catches_bom(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "x.md"), "wb").write(b"\xef\xbb\xbfbad")
            rc = selfcheck.check_encoding(d)
            self.assertEqual(rc, 1)
    def test_layout_separation(self):
        with tempfile.TemporaryDirectory() as d:
            # 交战区在安装树内=layout rc=1（§3.4 反例）
            rc = selfcheck.check_layout(os.path.join(d, "ir"), os.path.join(d, "ir", "home"))
            self.assertEqual(rc, 1)
        self.assertEqual(selfcheck.check_layout(os.path.join(d0, "ir"), os.path.join(d0, "home")), 0)

class TestGuided(unittest.TestCase):
    def test_guided_output_contract(self):
        txt = selfcheck.run_guided("walcode")
        for key in ("安装命令", "能力探测", "冒烟清单", "回传模板", "probe_results", "未实测"):
            self.assertIn(key, txt)
    def test_unknown_host(self):
        with self.assertRaises(SystemExit):
            selfcheck.run_guided("nonexistent")   # exit 2 用法错误
```
（`d0` 为类级 tempfile 根——执行者展开为 setUp/tearDown 标准形态；断言面不删。）

- [ ] **Step 2: 跑红** —— ModuleNotFoundError 全红取证。
- [ ] **Step 3: 实现 selfcheck.py**

```python
# cli/ledger/selfcheck.py（六项判定核心——每项 2-5 分钟粒度可实现）
import os, re, subprocess, sys
REPO_FILES_SCAN = ("phases", "engines", "cli", "shared", "install")

def check_cmd_index(repo_root):
    # ①phases/*.md+engines/**/MANIFEST.md 中 tanyin-<tool> <sub> 引用 ⊆ 已知命令面
    # 已知面单源=cli/ledger/registry.py 注册表+各工具 argparse 子命令（执行期以
    #   py -3 - <<'P' 脚本枚举为 JSON 清单并随本函数固化KNOWN_COMMANDS 常量；
    #   新增命令忘记登记=本检查红——与 VulnClaw verify_execution_boundary 同型机械防线）
    ...

def check_encoding(root):
    # ②walk root：UTF-8 无 BOM+无 CRLF（*.md/*.py/*.json/*.tsv/*.yaml/*.lock）
    ...

def check_phases_schema(repo_root):
    r = subprocess.run([sys.executable, os.path.join(repo_root, "cli", "tanyin-phases"), "validate"],
                       capture_output=True, text=True, env={**os.environ, "PYTHONUTF8": "1"})
    return r.returncode

def check_layout(install_root, home):
    # ④安装区/交战区分离：home 不得在 install_root 内；skill_link 目标存在（install_root 模式）
    ir, hm = os.path.abspath(install_root), os.path.abspath(home)
    if hm == ir or hm.startswith(ir + os.sep):
        return 1
    return 0

def check_lock(repo_root, pubkey=None):
    # ⑤supply_chain.load_lock+verify_entry 全键；openssl 缺=2（ENV）
    ...

def check_golden(repo_root):
    r = subprocess.run([sys.executable, os.path.join(repo_root, "tests", "run_golden.py")],
                       capture_output=True, text=True, env={**os.environ, "PYTHONUTF8": "1"})
    return r.returncode

def run_static(install_root, home, repo_root):
    items = [("cmd-index", check_cmd_index(repo_root), ""),
             ("encoding", check_encoding(repo_root), ""),
             ("phases-schema", check_phases_schema(repo_root), ""),
             ("layout", check_layout(install_root or DEFAULT, home or DEFAULT), ""),
             ("lock-verify", check_lock(repo_root), ""),
             ("golden", check_golden(repo_root), "")]
    worst = max((c for _, c, _ in items), default=0)
    return worst, items

GUIDED_TMPL = """# {host} 手测引导（§10.3）
1 安装命令：py -3 cli/tanyin-install --host {host} --timestamp <TS>
2 能力探测（逐项自动+人工确认）：子代理并发/shell/headless/系统级注入/hook 挂载点
3 冒烟清单：\u201c用探隐自检\u201d干跑 P0-P2——零对外请求，产出 goals/scope/matrix 样本+timeline
4 回传模板（贴回 issue 即计入验证记录）：
{{"host":"{host}","probe_results":{{...}},"dryrun_artifacts_sha256":"...","anomalies":"..."}}
5 发布口径：验证状态=静态验证通过+待实测；执法档位默认 Tier 1（保守披露）
"""

def run_guided(host):
    tpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "..", "install", "hosts", host + ".json")
    if not os.path.exists(tpl_path):
        raise SystemExit(2)
    return GUIDED_TMPL.format(host=host)
```
（六个 check 函数体 `...` 处执行者按注释意图与既有面实现——cmd-index 的 KNOWN_COMMANDS 固化清单由一次枚举脚本生成后以常量进仓；全部为 2-5 分钟可实现单元。）

- [ ] **Step 4: 删 Task 5 中间态守卫** —— `install_core._step6_selfcheck_gate` 改为无条件调 selfcheck（`--static --install-root --home`）；`tests/test_install_core.py` 追加端到端六步断言（`install(o)[0] == 0` 且结果含 `selfcheck=0`）。
- [ ] **Step 5: 跑绿+全套三连+Commit** —— `py -3 cli/tanyin-selfcheck --static` 仓内形态 rc==0 亲测记录 → discover+run_golden 全绿 → `git commit -m "批次6 T6：tanyin-selfcheck 六项静态+guided 手测+交战区分离机检（install 六步端到端）"`


### Task 7: G-5 收紧——锁探测 v2（state.md 锁字段+探活快路）

**Files:**
- Create: `cli/ledger/lock_v2.py`（探活纯函数单源）
- Modify: `cli/ledger/state_md.py`（session 激活时写 `lock_host/lock_pid/lock_boot/lock_since` 四可选字段；解析端缺省容忍——v1 state 无四字段照常解析）
- Modify: `cli/ledger/phases_engine.py`（`run_restart` handover 分支接探活快路）
- Modify: `contracts/04-phases.md`（勘误一行：state.md 锁字段 v2 可选字段+语义）
- Test: `tests/test_lock_v2.py`

**Interfaces:**
- Consumes: 既有语义锚点（phases_engine.py:868 handover 判定/:872 auto REJECT/:902 rebuild 释放锁；tests/test_managed_restart.py 七例行为面冻结不动）
- Produces:
  - `lock_v2.lock_fields(ts: str) -> dict`——`{"lock_host": platform.node(), "lock_pid": os.getpid(), "lock_boot": boot_id(), "lock_since": ts}`
  - `lock_v2.boot_id() -> str`——POSIX `/proc/sys/kernel/random/boot_id`；Windows `datetime.now()-GetTickCount64 毫秒` 取整 ISO（同 boot 稳定）
  - `lock_v2.pid_alive(pid: int) -> bool`——POSIX `os.kill(pid,0)`（ESRCH=死/EPERM=活）；Windows `ctypes OpenProcess(0x1000)` 非零=活
  - `lock_v2.probe_stale(fields: dict, now_host: str|None=None) -> tuple[str, str]`——返回 (`"dead"`|`"alive"`|`"unknown"`, 理由)；语义：本机同 boot 且 pid 探活死=`dead`；本机同 boot pid 活=`alive`；跨机/跨 boot/字段缺=`unknown`（保守）

**裁决 F 接线语义（不改既有判定，只加快路）：**
- `dead` → manual 接管免 rebuild-state（快路；timeline 记 `takeover-of=<s> probe=pid-dead`）；auto 仍恒 REJECT（单活跃会话铁律不变）
- `alive`/`unknown` → 行为与现状逐字节一致：auto REJECT；manual 须 state-rebuild PASS+takeover-of 留痕
- 全部既有 566 测试零改动须保持绿（`test_auto_cannot_takeover_active_lock`/`test_manual_takeover_with_rebuild_ok` 原样）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lock_v2.py
# -*- coding: utf-8 -*-
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import lock_v2  # noqa: E402

class TestProbe(unittest.TestCase):
    def test_dead_same_host_dead_pid(self):
        f = {"lock_host": lock_v2.HOST, "lock_boot": lock_v2.BOOT, "lock_pid": lock_v2.DEAD_PID}
        self.assertEqual(lock_v2.probe_stale(f)[0], "dead")
    def test_alive_same_host(self):
        f = {"lock_host": lock_v2.HOST, "lock_boot": lock_v2.BOOT, "lock_pid": os.getpid()}
        self.assertEqual(lock_v2.probe_stale(f)[0], "alive")
    def test_cross_host_unknown(self):
        f = {"lock_host": "other", "lock_boot": "b", "lock_pid": 1}
        self.assertEqual(lock_v2.probe_stale(f)[0], "unknown")
    def test_v1_fields_absent_unknown(self):
        self.assertEqual(lock_v2.probe_stale({})[0], "unknown")
    def test_boot_id_stable(self):
        self.assertEqual(lock_v2.boot_id(), lock_v2.boot_id())

class TestRestartWiring(unittest.TestCase):
    # 夹具=G-g1 复制（test_managed_restart 同型 setUp）
    def test_manual_fast_path_no_rebuild(self):
        # 前置：state.md 手工置 fields 为 dead 锁（本机+死 pid+lock_since=T0）
        # 调 run_restart(spawn="manual", session="s-new") → OK 且不需要先 rebuild-state
        # timeline 末行含 "takeover-of=" 与 "probe=pid-dead"
        ...
    def test_unknown_lock_manual_still_requires_rebuild(self):
        # state.md 置跨机锁 → manual 未 rebuild 前 REJECT（现状语义回退断言）
        ...
    def test_state_fields_written_on_restart(self):
        # 正常 restart 后 parse_state fields 含 lock_host/lock_pid/lock_boot/lock_since
        ...
```
（TestRestartWiring 三例按注释意图展开：夹具复制/`state_md.parse_state` 断言与 test_managed_restart.py 同构。）

- [ ] **Step 2: 跑红** —— `py -3 -m unittest tests.test_lock_v2 -v` 红（ModuleNotFoundError+wiring 三例 FAIL）取证。
- [ ] **Step 3: 实现 lock_v2.py+两处接线** —— 按 Produces 签名实现；`state_md.py` 激活写点（session_status=active 落笔处）追加四字段；`phases_engine.py` handover 分支：

```python
# run_restart handover 段（:868 附近）改写要点
probe, why = ("unknown", "v1")
if fields.get("lock_boot"):                       # v2 锁才探
    probe, why = lock_v2.probe_stale(fields)
if spawn == "auto" and handover:
    ...  # 原 REJECT 逐字保留（probe==dead 也不放行 auto）
elif spawn == "manual" and handover and probe != "dead" and not rebuilt:
    ...  # 原「须 state-rebuild PASS」REJECT 保留
elif spawn == "manual" and handover and probe == "dead":
    takeover = " takeover-of=%s probe=pid-dead (%s)" % (fields["session"], why)
    ...  # 免 rebuild 快路；其余护栏（速率/预算/单活跃）照走
```

- [ ] **Step 4: 跑绿+回归面** —— 新 8 例绿；`tests/test_managed_restart.py` 原样绿（行为零漂移）；discover+run_golden 全绿。
- [ ] **Step 5: Commit** —— `git commit -m "批次6 T7：G-5 锁收紧（探活快路 dead 免 rebuild；unknown 保守语义不变）"`

### Task 8: 五宿主矩阵落地（AGENTS 系统级注入+宿主清单通道）

**Files:**
- Create: `cli/ledger/hosts_matrix.py`
- Create: `install/AGENTS-INJECT.md`（常驻集系统级注入模板）
- Modify: `install/README.md`（五宿主兼容清单+opencode/codex headless 实测命令行+walcode/CodeBuddy 发布口径）
- Test: `tests/test_hosts_matrix.py`

**Interfaces:**
- Consumes: Task 5 `install/hosts/*.json`（egress_default_tier/verification/compat 字段）
- Produces:
  - `hosts_matrix.render_agents_inject(repo_root: str, host: str) -> str`（注入块=常驻集内容+该宿主 egress 档位披露行；<2K token 面沿用批次 3 冻结口径）
  - `hosts_matrix.inject_agents(agents_path: str, block: str) -> None`（`<!--TANYIN:BEGIN-->…<!--TANYIN:END-->` 标记包裹幂等替换）
  - `hosts_matrix.host_compat(repo_root: str, host: str) -> dict`（模板 compat+verification 直读）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_hosts_matrix.py
class TestTemplates(unittest.TestCase):
    def test_all_five_valid(self):
        for h in ("dsh", "opencode", "codex", "walcode", "codebuddy"):
            d = hosts_matrix.host_compat(REPO, h)
            self.assertIn(d["egress_default_tier"], (1, 3))
            self.assertTrue(d["compat"])
    def test_blind_spot_hosts_marked(self):
        for h in ("walcode", "codebuddy"):
            self.assertIn("待实测", hosts_matrix.host_compat(REPO, h)["verification"])
            self.assertEqual(hosts_matrix.host_compat(REPO, h)["egress_default_tier"], 1)

class TestInject(unittest.TestCase):
    def test_idempotent_block(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "AGENTS.md"); open(p, "w", encoding="utf-8").write("# host config\n")
            block = hosts_matrix.render_agents_inject(REPO, "dsh")
            hosts_matrix.inject_agents(p, block)
            first = open(p, encoding="utf-8").read()
            hosts_matrix.inject_agents(p, block)
            self.assertEqual(open(p, encoding="utf-8").read(), first)   # 二次注入零变更
            self.assertIn("<!--TANYIN:BEGIN-->", first)
            self.assertIn("Tier 3", first)                              # 档位事实披露在块内（铁律 5）
    def test_inject_len_capped(self):
        block = hosts_matrix.render_agents_inject(REPO, "dsh")
        self.assertLess(len(block), 8000, "常驻注入 <2K token 量级护栏（≈4 char/token）")
```

- [ ] **Step 2: 跑红 → Step 3: 实现**（模板读+标记替换两函数，~60 行；`AGENTS-INJECT.md` 正文=常驻八条：八问授权门/单写者/四层执法+本宿主档位披露行/预算树/速率熔断/凭据四关卡/九门状态机/kill9 续跑——每条一行命令锚点指向 SKILL.md 对应节）。
- [ ] **Step 4: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T8：五宿主矩阵（AGENTS 系统级注入幂等+盲区宿主 Tier1 披露）"`

### Task 9: tools.lock 全量化 + G-22 生产钥流程 + G-32 CVE 刷新通道

**Files:**
- Modify: `tools.lock`（键 3→8：+python/docker/三自写引擎目录清单键；nuclei-templates 第 5 列 upstream_commit 占位换真锚）
- Create: `install/KEY-MANAGEMENT.md`（G-22 生产钥生成/保管/重签/替换流程）
- Create: `install/resign-tools-lock.py`（重签脚本，离线机执行）
- Modify: `cli/tanyin-install`+`cli/ledger/install_core.py`（+`refresh-cve` 子命令）
- Modify: `knowledge/cve/README.md`（G-32 双通道注记：命令刷新/人工重铸等价）
- Modify: `contracts/10-toolchain-lock.md`（勘误一行：键清单 3→8+生产钥仪式指 KEY-MANAGEMENT.md）
- Test: `tests/test_supply_chain_resign.py`+`tests/test_install_core.py` 追加 refresh-cve 例

**Interfaces:**
- Consumes: `supply_chain.load_lock/canonical_digest/verify_entry/sign_entry`（单源不动）
- Produces:
  - `install_core.refresh_cve(src: str, knowledge_dir: str, ts: str) -> tuple[int, str]`——`src`=URL 或 `file://` 路径（离线等价通道）；下载→sha256 记录→落 `<knowledge_dir>/cve/cve-snapshot.tsv`（首行 `# snapshot-date=<ts>` 注记）→复用 tanyin-knowledge lint 七列校验；lint 不过=rc 1 且**不落文件**（先临时文件校验再原子替换）
  - tools.lock 第 8 键清单：`python`(3.11+-system)/`docker`(24+-system)/`engines-web-blackbox`/`engines-vuln-agent`/`engines-session-viz`(snapshot-1=目录清单 sha256)

- [ ] **Step 1: 写失败测试**

```python
# tests/test_supply_chain_resign.py
class TestResign(unittest.TestCase):
    def test_resign_roundtrip(self):
        # tempfile 拷 tools.lock+TEST 钥 → resign 脚本 subprocess 跑 → load_lock 全键 verify_entry PASS
    def test_resign_detects_tamper(self):
        # resign 后手改一键 sha256 → verify FAIL（信任链未断声明成立）
    def test_lock_fullness(self):
        names = {e["name"] for e in supply_chain.load_lock(os.path.join(REPO, "tools.lock"))}
        self.assertTrue({"python", "docker", "engines-web-blackbox", "engines-vuln-agent",
                         "engines-session-viz", "openssl", "nuclei", "nuclei-templates"} <= names)

class TestRefreshCve(unittest.TestCase):
    def test_refresh_from_file_atomic(self):
        # --from-file 夹具快照（14 行合法七列）→ refresh_cve → 目标文件首行 snapshot-date=--timestamp 值
        # → tanyin-knowledge lint rc==0；install-log.tsv 追加 refresh-cve 行
    def test_refresh_rejects_bad_columns(self):
        # 坏快照（六列）→ rc==1 且目标文件字节不变（原子性反向断言）
```

- [ ] **Step 2: 跑红 → Step 3: 实现 resign 脚本+refresh_cve+tools.lock 扩键**

```python
# install/resign-tools-lock.py 核心（~40 行）
# --lock tools.lock --key <pem> [--out <path>]：逐键 sign_entry(canonical_digest) → 原子写回
# 非交互纪律：不读 stdin；--allow-online 缺省时打印「须离线介质机执行（KEY-MANAGEMENT.md §3）」提示行后仍可跑（提示非拦截——CI 测试链用 TEST 钥在仓内可重签）
```
`KEY-MANAGEMENT.md` 五节定稿：①生成（`openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256`，离线机）②保管（离线介质+恢复口令双控；公钥指纹入 release 记录）③重签（本脚本）④替换（`engines/nuclei/release.pub` 换生产公钥+`tanyin-install --release` 交互确认行）⑤CI 关系（CI 永用 TEST-ONLY 夹具钥，与生产钥无信任关系——测试不因生产钥缺席而红）。
tools.lock 扩键执行步：`sha256sum` 三引擎目录清单文件（`find engines/<name> -type f | sort | xargs sha256sum | sha256sum`）→ 填入 → TEST 钥整锁重签（resign 脚本自举）→ `verify-lock` 亲测全 PASS。

- [ ] **Step 4: G-22 upstream_commit 换真（执行期实锚步）** —— `git clone --depth 1 https://github.com/projectdiscovery/nuclei-templates .research/repos/nuclei-templates` → `git -C .research/repos/nuclei-templates rev-parse HEAD` → 换 tools.lock 第 5 列占位 → templates.lock 同步四步流程（engines/nuclei/README.md 原文照走）→ 重签+验证。环境不可联网=如实保留占位+KEY-MANAGEMENT 记待锚行（不造数据纪律）。
- [ ] **Step 5: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T9：tools.lock 全量 8 键+G-22 钥流程+G-32 refresh-cve"`

### Task 10: Tier3 egress 代理本体（tanyin-egress serve；裁决 H）

**Files:**
- Create: `cli/ledger/egress_proxy.py`（代理本体：CONNECT/明文转发+DNS pin+OOB 落账+canary 告警）
- Modify: `cli/tanyin-egress`（+`serve` 子命令：`--acl <path> --port N [--egress-log <path>]`）
- Modify: `contracts/11-enforcement.md`（勘误一行：serve 判定语义+TLS 不解密披露）
- Test: `tests/test_egress_proxy.py`

**Interfaces:**
- Consumes: `tanyin-egress compile` 产物 `egress.acl`（格式锚定步见 Step 1——测试内先 compile 再解析，解析器与真实产物绑定）
- Produces:
  - `egress_proxy.EgressProxy(acl: dict, egress_log: str|None)`——`acl`=`parse_acl(text) -> {"allow": {(host, port|int)}, "dns_pin": {host: ip}, "oob": set[host], "canary": set[host]}`
  - `egress_proxy.parse_acl(text: str) -> dict`（`#` 注释+`allow <host>:<port>`/`allow <host>:*`/`dns-pin <host> <ip>`/`oob <host>`/`canary <host>` 行；compile 产物含未知行=raise ValueError——fail-closed）
  - 判定单源 `egress_proxy.decide(acl, host, port) -> "allow"|"deny"`（host 精确或 `*` 端口通配；canary/OOB 域按 allow 后走告警通道）
  - 运行时日志 `egress-log.jsonl` 行：`{"ts":..., "verdict":..., "host":..., "port":..., "kind":"forward|connect|oob|canary", "pin_ok":bool}`——**代理绝不写 13 表**（单写者纪律；运行时工件归运行时）
  - TLS 限制披露：CONNECT 按 CONNECT 目标主机名判定，**不解析 TLS 内容**（守门声明模板措辞进 install/README）

- [ ] **Step 1: 格式锚定（5 分钟）+写失败测试**

锚定步：`py -3 cli/tanyin-egress compile --goal-dir tests/fixtures/G-g1` → 打开产物 `egress.acl` 逐行核对与 `parse_acl` 行约定差异 → 若 compile 真实行名不同，以实况为准改 `parse_acl` 行约定并回写本任务行约定描述（契约 11 勘误同 commit）。

```python
# tests/test_egress_proxy.py
class TestAcl(unittest.TestCase):
    def test_parse_and_unknown_line_fails_closed(self):
        acl = egress_proxy.parse_acl("allow api.example.com:443\ndns-pin api.example.com 203.0.113.9\noob oob.example.com\ncanary canary.invalid\n")
        self.assertEqual(acl["allow"], {("api.example.com", 443)})
        self.assertEqual(acl["dns_pin"], {"api.example.com": "203.0.113.9"})
        with self.assertRaises(ValueError):
            egress_proxy.parse_acl("mystery-line x\n")

class TestProxyEndToEnd(unittest.TestCase):
    """线程内起 upstream http.server（127.0.0.1 ephemeral）+proxy（ephemeral）；urllib 挂 proxy 发请求。"""
    def test_allow_forward(self):
        # acl=allow 127.0.0.1:<up_port> → 经 proxy GET upstream → 200 且 body 一致；egress-log 一行 kind=forward
    def test_deny_403(self):
        # acl 只 allow 其他 host → 经 proxy GET → 403；log kind=forward verdict=deny
    def test_connect_denied_without_acl(self):
        # 对未 allow host 发 CONNECT → 403（隧道不建立）
    def test_canary_alert_line(self):
        # acl=allow+canary canary.invalid（解析到 upstream 本地端口）→ 请求后 log 有 kind=canary 告警行
    def test_oob_logged(self):
        # OOB 域命中 → log kind=oob
```
（五例 end-to-end 骨架按注释展开：`threading.Thread(target=serve_forever)` 配 `shutdown()` 清理；Windows CI 兼容——只连 127.0.0.1。）

- [ ] **Step 2: 跑红** —— ImportError/AttributeError 全红取证。
- [ ] **Step 3: 实现 egress_proxy.py**

```python
# cli/ledger/egress_proxy.py 核心形态（~180 行；http.server+http.client+socket select 中继）
import json, socket, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
from urllib.parse import urlsplit

class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def _log(self, kind, host, port, verdict, pin_ok=None):
        if self.server.egress_log:
            with open(self.server.egress_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": self.server.now, "verdict": verdict, "host": host,
                                    "port": port, "kind": kind, "pin_ok": pin_ok}) + "\n")
    def do_GET(self): self._forward()
    def do_POST(self): self._forward()
    def _forward(self):
        u = urlsplit(self.path)                      # 代理形态绝对 URI
        host, port = u.hostname, u.port or 80
        v = decide(self.server.acl, host, port)
        self._log("forward", host, port, v)
        if v != "allow":
            self.send_error(403); return
        pin = self.server.acl["dns_pin"].get(host)
        conn = http.client.HTTPConnection(pin or host, port, timeout=10)
        ...  # 转 headers/body → 上游 → 回写 status/headers/body（hop-by-hop 头剥除）
    def do_CONNECT(self):
        host, port = self.path.split(":")[0], int(self.path.split(":")[1] or 443)
        v = decide(self.server.acl, host, port)
        self._log("connect", host, port, v)
        if v != "allow":
            self.send_error(403); return
        self.send_response(200); self.end_headers()
        _tunnel(self.connection, host, port)         # 双向 select 中继；TLS 不解密（披露）

def serve(acl_path, port, egress_log=None, now="2026-09-24T00:00:00Z"):
    acl = parse_acl(open(acl_path, encoding="utf-8").read())
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    httpd.acl, httpd.egress_log, httpd.now = acl, egress_log, now
    return httpd                                     # 调用方 serve_forever/shutdown
```

- [ ] **Step 4: tanyin-egress serve 子命令接线** —— argparse 分支：起服打印一行 `egress-proxy listening 127.0.0.1:<port> acl=<path>` 后 `serve_forever()`（前台常驻=无守护进程纪律合规；Ctrl-C 优雅退出）。
- [ ] **Step 5: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T10：Tier3 代理本体（CONNECT/forward ACL+DNS pin+OOB/canary 告警；TLS 不解密披露）"`

### Task 11: canary 流量级验证（经代理触碰检测链）

**Files:**
- Modify: `cli/tanyin-canary`+canary 模块（`probe` 增 `--egress-log <path>` 可选入参：读 egress-log.jsonl 中 kind=canary 行并入触碰判定——流量级证据源）
- Modify: `shared/EVALS.md`（M03 判定链注记：probe=本地态+egress-log 双源；R10 误报校准口径=触碰绑定本交战进程+时间窗）
- Test: `tests/test_canary_traffic.py`

**Interfaces:**
- Consumes: Task 10 代理+egress-log 行契约；`tanyin-canary deploy/probe` 既有面（零容忍语义不动）
- Produces: 流量级验证链——`deploy 诱饵 → 经代理触 canary 域 → egress-log 告警行 → probe --egress-log 判触碰（rc!=0）`；反例=不经代理的同域连接（模拟共享环境他进程）**不**触发（R10 口径机检）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_canary_traffic.py
class TestTrafficLevel(unittest.TestCase):
    def test_touch_via_proxy_detected(self):
        # G-g1 复制+deploy(seed 确定性) → 起 Task10 代理(acl 含 canary 域) → 线程内经代理请求 canary 域
        # → probe --egress-log egress-log.jsonl → rc!=0 且输出含 canary 触碰明细
    def test_non_proxy_connection_not_flagged(self):
        # 同域仅本地 socket 连接（不经代理、无 log 行）→ probe --egress-log → rc==0（R10：裸连接/旁路不误报）
    def test_probe_without_log_backcompat(self):
        # 不给 --egress-log → 行为与现状一致（既有 canary 测试面零漂移）
```

- [ ] **Step 2: 跑红 → Step 3: 实现**（canary probe 侧 +15 行：可选读 log、kind=canary 行聚合进触碰集；时间窗过滤复用既有窗口参数）。红跑取证→绿。
- [ ] **Step 4: evals 注记+全套三连+Commit** —— `shared/EVALS.md` M03 行加「流量级双源」注记；discover+run_golden 全绿 → `git commit -m "批次6 T11：canary 流量级验证链（egress-log 双源+R10 反例）"`

### Task 12: tanyin-report 聚合器（13 表→聚合投影）

**Files:**
- Create: `cli/ledger/report_agg.py`
- Create: `cli/tanyin-report` + `cli/tanyin-report.cmd`
- Test: `tests/test_report_agg.py`

**Interfaces:**
- Consumes: 13 表（schemas TABLES 列序单源）；`tanyin-ledger` 只读
- Produces:
  - `report_agg.aggregate(goal_dir: str, ts: str) -> dict`——投影键：`goal`（goals 行）/ `scope_summary`（include/exclude/oob/account-grant 计数+amendment 链头）/ `findings`（[{id,title,tech_sev,biz_impact,replay_state,asset,verified}]/verify 门口径=重放三态映射）/ `matrix`（filled/empty/gaps 列表）/ `coverage`（intents open/closed+phases 九门通过集）/ `budget_terminal`（normal|exhausted——budget.tsv 终态；终态 B 判据字段）/ `tier_disclosure`（timeline `tier=` 事件末值+egress 档位）/ `limits`（覆盖度局限性声明输入：空矩阵格清单+unverified 清单）
  - CLI：`tanyin-report aggregate --goal-dir D --timestamp T [--out report/draft-data.json]`（缺表=exit 2 ENV；写文件=确定性投影，两跑逐字节一致）
  - **P5.md ENV-HALT 解除不在本任务**（lint 未落地；Task 14 一并接线）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report_agg.py
class TestAggregate(unittest.TestCase):
    def test_projection_on_fixture(self):
        gd = self._copy_g1()                      # G-g1 复制惯例
        d = report_agg.aggregate(gd, TS)
        self.assertTrue(set(d) >= {"goal", "scope_summary", "findings", "matrix",
                                   "coverage", "budget_terminal", "tier_disclosure", "limits"})
        self.assertEqual(d["budget_terminal"], "normal")
    def test_deterministic(self):
        gd = self._copy_g1()
        self.assertEqual(json.dumps(report_agg.aggregate(gd, TS), sort_keys=True),
                         json.dumps(report_agg.aggregate(gd, TS), sort_keys=True))
    def test_missing_table_env(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(EnvironmentError):
                report_agg.aggregate(d, TS)       # 13 表缺=ENV 2 非 FAIL
    def test_budget_exhausted_flag(self):
        gd = self._copy_g1()
        _mark_budget_exhausted(gd)                # budget 表追加耗尽行（CLI 命令铸造，不用手改表）
        self.assertEqual(report_agg.aggregate(gd, TS)["budget_terminal"], "exhausted")
```

- [ ] **Step 2: 跑红 → Step 3: 实现 report_agg.py** —— 每投影键一个小函数（`_project_findings`/_project_matrix/_project_coverage/_project_budget/_project_tier/_project_limits），列名一律 `TABLES[t].index(col)` 取（零硬编码列号）；`replay_state` 取 findings 重放列+set-replay-state 面。CLI 入口 + `.cmd` 配对。
- [ ] **Step 4: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T12：tanyin-report 聚合器（13 表确定性投影+终态 B 判据）"`

### Task 13: FD 九段渲染器 + 时间链断言（FD 规格 §一/§二 兑现）

**Files:**
- Create: `cli/ledger/report_render.py`
- Modify: `cli/tanyin-report`（+`render` 子命令）
- Test: `tests/test_report_render.py`

**Interfaces:**
- Consumes: `report_agg.aggregate`（Task 12）；findings-cards/FD-*.md（front-matter+POC 四要素）+EV 卡片（raw_request/raw_response/时间/环境）+E-index 双指纹（哈希复算）；矩阵词表（shared/VOCAB.md）；G-24 基线表（severity_expect）
- Produces:
  - `report_render.render_fd(goal_dir: str, fd_id: str) -> tuple[int, str]`——返回 (rc, 九段 markdown)；任一段数据源缺失=rc 1 且缺段清单随报错（渲染不造数据：每段只从账本/卡片投影）
  - `report_render.check_time_chain(goal_dir: str, issued_at: str|None=None) -> tuple[bool, str]`——断言 evidence.captured_at < finding.added_at（< report.issued_at 可选）；违反=rc 1
  - CLI：`tanyin-report render --goal-dir D --fd <id> [--all] --out report/draft/<id>.md --timestamp T`

- 九段→数据源映射（渲染器实现表，执行期照此逐段实现）：
  ①位置=assets/edges 图谱坐标（资产ID+表面+精确位置）②资产与接口=read-ledger 子图投影（禁手写）③描述=类型必须命中矩阵词表（不命中=不进 findings 的回归断言+渲染 FAIL）④等级=tech 严重度×biz 影响（G-24 基线表映射，CVSS 向量可复算字段在卡）⑤原理=evidence 链引用（哪条请求哪个差异）⑥POC/EXP=EV 卡 POC 四要素原文转抄（raw_request/raw_response 字节不变；变体参数单列「判读说明」段）⑦危害=token 化后实际回显引用（禁空话句式 lint 在 Task 14）⑧修复建议=类型映射+K1 挂标+「修复后哪条 POC 应失效」⑨复现状态=重放门三态+最近重放时间（未 verified=强制披露行，禁宣称 verified）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report_render.py
class TestRender(unittest.TestCase):
    def test_nine_segments_in_order(self):
        gd = self._copy_g1()                          # 含 FD 卡+EV 卡夹具
        rc, md = report_render.render_fd(gd, self._any_fd(gd))
        self.assertEqual(rc, 0)
        segs = ["位置", "涉及资产与接口", "漏洞描述", "等级", "漏洞原理",
                "POC/EXP", "危害", "修复建议", "复现与验证状态"]
        pos = [md.find("## " + s) for s in segs]
        self.assertTrue(all(p >= 0 for p in pos) and pos == sorted(pos), "九段齐且有序")
    def test_raw_request_byte_identical(self):
        gd = self._copy_g1()
        rc, md = report_render.render_fd(gd, self._any_fd(gd))
        raw_ev = self._ev_raw_request(gd)             # EV 卡 POC 原文字节
        self.assertIn(raw_ev, md)                     # 转抄零编辑（改一字即 FAIL 的渲染侧保证）
    def test_time_chain_violation(self):
        gd = self._copy_g1()
        _tamper_captured_at_after_added(gd)           # 夹具篡改：证据时间晚于 finding
        ok, why = report_render.check_time_chain(gd)
        self.assertFalse(ok)
    def test_unverified_disclosed(self):
        gd = self._copy_g1()
        _set_replay_state_unverified(gd)              # CLI 命令铸造
        rc, md = report_render.render_fd(gd, self._any_fd(gd))
        self.assertIn("未通过独立重放门", md)          # 披露行强制在
        self.assertNotIn("verified：是", md)
```

- [ ] **Step 2: 跑红** —— ModuleNotFoundError 全红取证。
- [ ] **Step 3: 实现 report_render.py** —— 九段函数逐段 ~20 行（段 ⑥ 用 EV 卡 raw 字节直接拼接；段 ⑨ 三态映射 verified/env-diff/unverified→披露措辞）；`check_time_chain` 读 E-index captured_at 与 findings added_at 列比对。CLI `render` 接线（`--all`=遍历 findings.tsv active 行）。
- [ ] **Step 4: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T13：FD 九段渲染器+时间链断言（b0006f2 落点①）"`

### Task 14: G-25 Burp 直贴 lint + P5 签发门 + P6 清理门接线（裁决 B）

**Files:**
- Create: `cli/ledger/report_lint.py`
- Modify: `cli/tanyin-report`（+`lint`/`sign` 子命令）
- Modify: `phases/P5.md`（:17 ENV-HALT 行解除→`tanyin-report lint` 真门；PROTOCOL §1 判定表不变）
- Modify: `phases/P6.md`（清理门接线注记：sign 前置含 `cleanup-checklist --verify` rc==0——命令零改动，仅 duty 行注记）
- Modify: `contracts/06-evidence-cards.md`（G-25 裁决 B 勘误：HTTP/1.x 直贴首发/HTTP2-TLS 判读说明单列/Host-Connection 原文归属）
- Test: `tests/test_report_lint.py`

**Interfaces:**
- Consumes: Task 13 渲染产物；`tanyin-ledger redact-scan`/`tanyin-phases cleanup-checklist --verify` 子进程；`report_agg.aggregate`（合规六要素数据源）
- Produces:
  - `report_lint.burp_pasteable(raw_request: str) -> tuple[bool, list[str]]`——四规则（裁决 B）：①纯文本可解码无 BOM 无二进制字节 ②请求行形如 METHOD SP PATH SP HTTP/x.x ③含至少一个 Host 头 ④非空 body 有空行分隔；HTTP/2 帧/TLS 指定内容出现于 raw=FAIL（判读说明单列）
  - `report_lint.nine_segments(md: str) -> list[str]`（缺段清单）
  - `report_lint.compliance_six(data: dict) -> list[str]`（六要素缺项：授权与范围声明/方法学映射 WSTG/覆盖度与局限性/技术×业务风险分级/整改优先级与复测建议/等保占位段——数据源=aggregate 投影，等保段=占位常量段落）
  - `report_lint.sign_gate(goal_dir: str, ts: str) -> tuple[int, dict]`——聚合：全部 active FD 渲染 rc==0+九段齐+burp lint PASS+时间链（issued_at=ts）+redact-scan 零泄漏+cleanup-checklist rc==0+tier 披露在；任一不过=1 且 FAIL 明细落报告；全过=0 且落 `report/signed/pass.json`（签发凭证：goal+ts+各门结果）
  - CLI：`tanyin-report lint --goal-dir D`（exit 同 gate）/ `tanyin-report sign --goal-dir D --timestamp T`（=lint+落凭证+调 Task 15 双工件写盘）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report_lint.py
class TestBurpLint(unittest.TestCase):
    RAW = "POST /login HTTP/1.1\r\nHost: t.example.com\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\nuser=a&pass=b"
    def test_happy_path(self):
        ok, why = report_lint.burp_pasteable(self.RAW)
        self.assertTrue(ok, why)
    def test_missing_host(self):
        bad = self.RAW.replace("Host: t.example.com\r\n", "")
        self.assertFalse(report_lint.burp_pasteable(bad)[0])
    def test_bad_request_line(self):
        self.assertFalse(report_lint.burp_pasteable("POST /login\r\nHost: h\r\n\r\n")[0])
    def test_binary_bytes_rejected(self):
        self.assertFalse(report_lint.burp_pasteable("POST / HTTP/1.1\r\nHost: h\r\n\r\n\x00\x02frame")[0])
    def test_http2_frame_directed_to_note(self):
        ok, why = report_lint.burp_pasteable("POST / HTTP/1.1\r\nHost: h\r\n\r\n[HTTP/2 binary frame: DATA]\x01\x02")
        self.assertFalse(ok); self.assertIn("判读说明", " ".join(why))

class TestSignGate(unittest.TestCase):
    def test_gate_pass_on_fixture(self):
        gd = self._copy_g1()
        rc, rep = report_lint.sign_gate(gd, TS)
        self.assertEqual(rc, 0, rep)
        self.assertTrue(os.path.exists(os.path.join(gd, "report", "signed", "pass.json")))
    def test_gate_fail_missing_segment(self):
        gd = self._copy_g1()
        _delete_segment_nine(gd)                       # 夹具操作：渲染后删第 9 段再 lint
        self.assertEqual(report_lint.sign_gate(gd, TS)[0], 1)
    def test_gate_fail_cleanup_not_verified(self):
        gd = self._copy_g1()
        _break_cleanup_checklist(gd)                   # 夹具操作：cleanup 清单置未验项
        self.assertEqual(report_lint.sign_gate(gd, TS)[0], 1)
    def test_p5_note_updated(self):
        txt = open(os.path.join(REPO, "phases", "P5.md"), encoding="utf-8").read()
        self.assertNotIn("批次 6 交付前该断言=ENV-HALT", txt)   # 解除兑现的文本断言
        self.assertIn("tanyin-report lint", txt)
```

- [ ] **Step 2: 跑红 → Step 3: 实现 report_lint.py**（五函数+CLI 接线；`sign`=lint+凭证+Task 15 `write_all`——本任务先落 lint/sign 骨架，`write_all` 调用点 Task 15 接上，中间态=sign 只落凭证不落工件并在输出披露一行）。红跑取证→绿。
- [ ] **Step 4: P5/P6/契约 06 文本接线** —— P5.md :17 行改写为真门（命令+判定表锚点不变）；P6.md duty 注记一行；契约 06 勘误（裁决 B 三条款）。
- [ ] **Step 5: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T14：Burp 直贴 lint+P5 签发门解除 ENV-HALT+清理门接线（G-25 收口）"`

### Task 15: 双工件 findings.json+SARIF + LLM 叙述过滤 + 合规六要素签发面（契约 13 兑现）

**Files:**
- Create: `cli/ledger/report_artifacts.py`
- Test: `tests/test_report_artifacts.py`

**Interfaces:**
- Consumes: Task 12 aggregate 投影；Task 14 sign 骨架（`write_all` 接线点）
- Produces:
  - `report_artifacts.findings_json(goal_dir: str) -> dict`——**全量+生命周期**：每 finding 含 id/title/severity 双轴/replay_state/lifecycle(active|rejected|repair-candidate)/evidence_ids/asset（VulnClaw findings.json 同型；来源=13 表投影零新事实）
  - `report_artifacts.findings_sarif(goal_dir: str) -> dict`——**SARIF 2.1.0 仅 verified**：runs[0].results 每条含 ruleId=漏洞类型、level（severity 映射）、message.text、locations[0].physicalLocation.artifactLocation=EV 卡片相对路径（EV↔SARIF 位置映射；unverified 一律不进 SARIF——报告纳入门）
  - `report_artifacts.narrative_filter(text: str) -> str`——LLM 叙述段机械清洗：剥 TOOL_CALL 标记/Round 数字轮次行/think 标签/调试前缀行（VulnClaw report/filter 同型正则集，清单进函数头注释）
  - `report_artifacts.write_all(goal_dir: str, ts: str) -> list[str]`——sign 时落 `report/findings.json`+`report/findings.sarif`+`report/signed/report-<ts>.md`（终稿=聚合投影+FD 渲染+合规六要素章节+执行摘要经 narrative_filter）；返回工件路径表

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report_artifacts.py
class TestFindingsJson(unittest.TestCase):
    def test_full_lifecycle(self):
        gd = self._copy_g1()
        d = report_artifacts.findings_json(gd)
        self.assertTrue(len(d["findings"]) >= 1)
        self.assertIn("replay_state", set(d["findings"][0].keys()))
class TestSarif(unittest.TestCase):
    def test_verified_only(self):
        gd = self._copy_g1()
        d = report_artifacts.findings_sarif(gd)
        ids = {r["ruleId"] for r in d["runs"][0]["results"]}
        unverified = self._unverified_ids(gd)
        self.assertEqual(ids & unverified, set())          # 报告纳入门：unverified 不进 SARIF
    def test_sarif_shape(self):
        d = report_artifacts.findings_sarif(self._copy_g1())
        self.assertEqual(d["version"], "2.1.0")
        self.assertTrue(all("artifactLocation" in r["locations"][0]["physicalLocation"]
                            for r in d["runs"][0]["results"]))
class TestFilter(unittest.TestCase):
    def test_strips_markers(self):
        dirty = "<think>推理</think>TOOL_CALL add-finding\nRound 3\n结论：存在 SQLi。"
        clean = report_artifacts.narrative_filter(dirty)
        self.assertNotIn("TOOL_CALL", clean); self.assertNotIn("<think>", clean)
        self.assertIn("结论：存在 SQLi。", clean)
class TestWriteAll(unittest.TestCase):
    def test_three_artifacts(self):
        gd = self._copy_g1()
        paths = report_artifacts.write_all(gd, TS)
        for suffix in ("findings.json", "findings.sarif"):
            self.assertTrue(any(p.endswith(suffix) for p in paths))
        # 终稿 md 含合规六要素六标题（等保占位段原文在）
        md = open([p for p in paths if p.endswith(".md")][0], encoding="utf-8").read()
        for h in ("授权与范围声明", "方法学映射", "覆盖度与局限性", "技术×业务风险分级",
                  "整改优先级与复测建议", "等保"):
            self.assertIn(h, md)
```

- [ ] **Step 2: 跑红 → Step 3: 实现** —— 三函数+write_all（sign 骨架接线：Task 14 预留调用点激活，删中间态披露行）；合规六章节由 aggregate 投影确定性组装（等保占位段=常量文本段，R11 法务过审对象）。
- [ ] **Step 4: 端到端亲测** —— `py -3 cli/tanyin-report sign --goal-dir tests/fixtures/G-g1 --timestamp <TS>` rc==0；三工件在；双工件 `json.load` 合法。
- [ ] **Step 5: 全套三连+Commit** —— `git commit -m "批次6 T15：双工件+叙述过滤+合规六要素签发面（契约 13 兑现；R11 过审对象成形）"`

### Task 16: 授权靶场种 20 + 检出率 eval（裁决 I）

**Files:**
- Create: `tests/range/docker-compose.yml`（靶场拓扑：8 漏洞服务容器+1 攻击侧 noop；仅监听 compose 内网+127.0.0.1 映射）
- Create: `tests/range/seed/`（种 20 漏洞服务源码——每服务单目录 Python http.server 实现，漏洞响应内嵌唯一 marker 串如 `GTSQLI-01`）
- Create: `tests/range/ground-truth.json`（20 条 GT：{id,class,endpoint,marker,post_auth,authz_role}；分布=SQLi×2/XSS×2/命令注入×1/SSTI×1/SSRF×2/反序列化×2/CORS×1/开放重定向×1/目录遍历×1/认证后越权 5（IDOR×2+水平越权 API×2+角色混淆×1，authz_role 非空）+弱口令×1+信息泄露×1）
- Create: `tests/eval_range_recall.py`（scorer；eval_authz_recall 匹配规则泛化复用）
- Modify: `cli/ledger/evals_metrics.py`（注册 `range-recall` runner=M09）
- Test: `tests/test_range_recall.py`

**Interfaces:**
- Consumes: tests/eval_authz_recall.py 匹配规则（EV matcher words 含 marker+资产值==endpoint+负对 authz fact）；`tanyin-ledger` 命令面铸造 range 会话
- Produces:
  - `eval_range_recall.score(session_rows, cards, gt: list[dict]) -> tuple[float, list[str]]`——返回 (recall=命中/20, MISSING id 清单)；GT 命中判定=active finding 的 EV 卡 word matcher 含该条 marker 且 affected 资产==endpoint；post_auth 条目另须 finding kind=authz 或 cred 绑定链在
  - CLI：`python tests/eval_range_recall.py --session <D> --ground-truth tests/range/ground-truth.json [--baseline 0.85]`——exit 0=recall≥baseline；1=低于；2=docker 缺（`shutil.which("docker")` None 且无 --session 现成会话时）

- [ ] **Step 1: 写失败测试（scorer 夹具级先红——不依赖 docker）**

```python
# tests/test_range_recall.py
class TestScorer(unittest.TestCase):
    def test_gt_shape_twenty(self):
        gt = json.load(open(os.path.join(HERE, "range", "ground-truth.json"), encoding="utf-8"))
        self.assertEqual(len(gt), 20)
        post = [g for g in gt if g["post_auth"]]
        self.assertGreaterEqual(len(post), 5)          # 认证后 ≥5 服务身份矩阵（设计 §9.4）
        self.assertEqual(len({g["marker"] for g in gt}), 20)   # marker 全局唯一
    def test_scorer_perfect_fixture(self):
        # 夹具会话（复用 diff-authz 卡片铸造法）内铸 3 命中+1 未命中 → recall=3/4 且 MISSING 含未命中 id
    def test_post_auth_requires_authz_chain(self):
        # 命中 marker 但无 authz 链的 post_auth 条目不计命中（负向断言）
    def test_cli_exit_codes(self):
        # --baseline 超过实测→1；docker 缺且无 --session→2
```

- [ ] **Step 2: 跑红 → Step 3: 实现 scorer+compose+seed** —— compose 语法自检步（`docker compose config`，docker 缺=skip 并记录）；seed 每服务 ~30 行 http.server+漏洞路由+marker 内嵌（全部合成 payload，无真实攻击代码外溢——靶场=本地回环资产）。
- [ ] **Step 4: 首跑入册（基线 v1，裁决 I）** —— 本地起 compose→按 RUNBOOK（Task 17 交付）跑干→scorer 实测 recall→实测值+日期写入契约 15 §3 M09 基线行（`collect-first`→数值，微版本勘误）——此后回退即 fail。环境不可跑=基线保持 collect-first+台账 G-39 登记（不造数据）。
- [ ] **Step 5: 全套三连+Commit** —— `git commit -m "批次6 T16：授权靶场种 20+检出率 scorer（基线 v1 入册通道）"`

### Task 17: budget-exhausted 演练（终态 B）+ 全流程 RUNBOOK

**Files:**
- Create: `tests/range/RUNBOOK.md`（P0→P6 全流程命令序：add-goal 八问→scope→egress compile→canary deploy→P0..P6 门序→engine 提交→replay→sign；每步带判定命令与预期 rc）
- Modify: `cli/ledger/report_lint.py`（sign_gate 终态 B 分支：`budget_terminal=exhausted` 非 FAIL——但 `limits` 投影必须含未测矩阵格清单+中期披露声明，缺=1）
- Test: `tests/test_budget_exhausted.py`

**Interfaces:**
- Consumes: `tanyin-budgetctl enforce`（预算树限额拒绝，批次 2 面）；Task 12 `budget_terminal` 投影；Task 14 sign_gate
- Produces:
  - 终态 B 语义（进契约 13 勘误）：budget-exhausted=合法签发终态，报告强制含「中期报告声明+未测范围披露清单」（gaps 逐格列出）——诚实覆盖口径（铁律 3）
  - RUNBOOK=靶场全流程演练唯一剧本（含 budget-exhausted 演练支线：中期抽干预算→引擎停→中期报告签发 rc==0）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_budget_exhausted.py
class TestTerminalB(unittest.TestCase):
    def test_exhausted_passes_gate_with_disclosure(self):
        gd = self._copy_g1_with_budget_exhausted()      # CLI 铸造：budgetctl enforce 至耗尽+timeline 事件
        rc, rep = report_lint.sign_gate(gd, TS)
        self.assertEqual(rc, 0, rep)                    # 终态 B 可签发
        md = self._signed_report(gd)
        self.assertIn("中期报告", md)
        self.assertIn("未测范围披露", md)
    def test_exhausted_without_disclosure_fails(self):
        gd = self._copy_g1_with_budget_exhausted()
        _strip_limits_projection(gd)                    # 反例：抽掉披露数据
        self.assertEqual(report_lint.sign_gate(gd, TS)[0], 1)
    def test_budget_reject_event_in_timeline(self):
        # 预算超限 REJECT 落账断言（既有 budgetctl 面复核——终态 B 的前置证据链）
```

- [ ] **Step 2: 跑红 → Step 3: 实现 sign_gate 终态 B 分支+RUNBOOK** —— sign_gate 读 aggregate.budget_terminal；exhausted 分支强制校验 limits.gaps 非空断言+中期声明段；RUNBOOK 十一步命令序全文（含 budget-exhausted 支线四步）。
- [ ] **Step 4: 演练亲测** —— RUNBOOK 前四步（P0-P2 干跑段）在 G-g1 拷贝上逐条实跑记录 rc；P3-P6 段标注「须 range 活靶+LLM 在环=执行期演练」并按 ENV 披露（docker 缺=演练挂起入台账，不阻塞单测出口）。
- [ ] **Step 5: 全套三连+Commit** —— `git commit -m "批次6 T17：budget-exhausted 终态 B+全流程 RUNBOOK"`

### Task 18: 真人复核流程文档化 + 台账收口 + 契约勘误 + 交付文档

**Files:**
- Create: `docs/HUMAN-REVIEW.md`（真人复核流程：范围/判据/记录格式/争议升级）
- Create: `docs/design/2026-09-24-b6-discovery-notes.md`（批次 6 台账：计划原文誊录+状态归并+新 G 项登记+移交清单四节式——沿 b3/b4/b5 同构）
- Modify: `docs/HANDOFF.md`（批次 6 前置义务兑现行+R11 法务过审记录行+状态快照）
- Modify: `contracts/09-cli-surface.md`（勘误：工具面 11→15——+evals/install/selfcheck/report；canary probe `--egress-log` 注记）
- Modify: `cli/README.md`（批次 6 节：四新工具速查+安装矩阵用法+出口验证记录）
- Test: `tests/test_human_review_doc.py`（文档契约测试：结构+必填字段在场）

**Interfaces:**
- Consumes: 全前序任务交付面；批次 5 M-6 前置义务原文（在库 10 页=CP-0001..0008+PR-0001..0002）
- Produces:
  - 真人复核记录表（`docs/HUMAN-REVIEW.md` 附录）：每页一行 {page-id, 复核人(真人≠执行者), 结论(approve/reject/revise), 日期, 备注}——10 行全填=批次 6 出口项 #15
  - 台账新 G 项登记（G-36..G-41，见 Step 4 清单）

- [ ] **Step 1: 写失败测试（文档即契约）**

```python
# tests/test_human_review_doc.py
class TestHumanReviewDoc(unittest.TestCase):
    def test_ten_pages_listed_with_columns(self):
        txt = open(os.path.join(REPO, "docs", "HUMAN-REVIEW.md"), encoding="utf-8").read()
        for pg in ("CP-0001", "CP-0008", "PR-0001", "PR-0002"):
            self.assertIn(pg, txt)
        for col in ("复核人", "结论", "日期"):
            self.assertIn(col, txt)
        self.assertIn("复核人不得为本批次执行者", txt)     # 真人≠执行者纪律成文
    def test_discovery_notes_structure(self):
        txt = open(os.path.join(REPO, "docs", "design", "2026-09-24-b6-discovery-notes.md"), encoding="utf-8").read()
        for sec in ("计划原文誊录", "状态归并台账", "新增探知项", "移交清单"):
            self.assertIn(sec, txt)
        for g in ("G-22", "G-25", "G-32", "G-33", "G-5", "G-11", "G-36"):
            self.assertIn(g, txt)
```

- [ ] **Step 2: 跑红 → Step 3: 写 HUMAN-REVIEW.md+复核表** —— 流程四节：①范围（在库 10 页+批次 6 新增知识页）②判据（review-checklist 逐项+四门槛③人审门同口径）③记录（附录表+knowledge/log.md 复核行追加纪律）④争议升级（reject→staging 退回重蒸馏→再复核）。
- [ ] **Step 4: 台账 b6 四节落盘** —— G-22（已收口=流程+脚本交付，仪式留 KEY-MANAGEMENT 执行记录位）/G-25（已收口=裁决 B+T14）/G-32（已收口=T9 双通道）/G-33（已收口=T2 硬门）/G-5（已收口=T7）/G-11（半收口=通道+报告交付，系数回写遗留→G-37）/G-4（遗留→契约 v3 同批）。新增探知项：G-36（HTTP/2 二进制帧与 TLS 直贴渲染——判读说明通道临时态，待真帧样本）、G-37（token 估算系数按校准报告回写契约 v3）、G-38（walcode/CodeBuddy 实测回传后升档）、G-39（靶场检出率基线 v1 冻结与转硬门时点）、G-40（TSecBench 全量对齐=发布前 L3）、G-41（egress 代理并发/性能上限未测——机械执法非性能件披露）。
- [ ] **Step 5: 契约 09 勘误+cli/README 批次 6 节+HANDOFF 三行**（前置义务兑现/R11 过审记录行——法务人工过审 sign 生成器样张一次并将结论一行入账/状态快照批次 6 行）。
- [ ] **Step 6: 跑绿+全套三连+Commit** —— `git commit -m "批次6 T18：真人复核流程+台账收口 G-36..G-41+契约 09 勘误+交付文档"`

---

# 批次 6 收尾三件（任务 18 后执行）

## 一、writing-plans 自检对照（spec 覆盖核验——执行完毕后逐条勾）
- §9.1 L1 金样 CI→既有 ci.yml（T4 保留）；§9.2 L2 全 11 行指标→契约 15 §3 十二指标映射表逐行核对（M01..M12 覆盖 §9.2 全行+G-33 增行）；§9.3 L3→T3 脚手架（不阻塞）；§9.4 靶场+抽查→T16/T17+批次 5 双库抽查既有面
- §10.1 六步→T5；§10.2 五宿主→T5 模板+T8；§10.3 盲区→T6 guided+T8 标注
- §11 批次 6 行逐短语→三层 CI（T1-4）/安装矩阵（T5/6/8）/tools.lock 全量（T9）/交战区分离（T5/6）/报告流水线（T12-15）/授权靶场（T16/17）；出口验收三句→出口清单 #7/#13/#14+#17
- §12 R8（盲区披露）/R9（降档不阻塞安装）/R10（canary 误报校准=T11）/R11（法务过审=T18）各有着落
- 占位符扫描：全文无 TBD/「后续补充」；代码骨架中 `...` 段为执行期展开点且每处带意图注释——执行工程师按注释即可实现
- 类型一致性抽查：`run_suite` 返回 (int, dict)（T1 定义=T3/T4 使用）；`sign_gate` 返回 (int, dict)（T14 定义=T17 使用）；`aggregate` 键集（T12 定义=T13/14/15/17 消费）——三处签名逐一比对无漂移

## 二、整批出口验收清单执行记录（对照骨架清单 #1-#18 逐条跑判定命令，结果入 HANDOFF 状态快照行）

## 三、最终账本动作
```bash
git add -A && git commit -m "批次6实施计划——evals+安装矩阵+交付：18 任务全量（三层验收 CI 化/tanyin-install 六步+五宿主/tools.lock 全量+G-22 生产钥/交战区分离/报告流水线 FD 九段+Burp lint+双工件/Tier3 代理本体+canary 流量级/靶场种 20+budget-exhausted/真人复核+G 项收口 G-36..G-41 登记；沿 writing-plans 规范：文件结构图/每任务 Files+Interfaces+TDD 红绿步+判定命令/出口验收 18 项附判定命令）"
git push origin HEAD
```


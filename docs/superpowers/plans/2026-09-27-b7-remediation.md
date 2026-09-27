# 批次 7（整改批次）实施计划 —— C1 账本写路径原子化+并发锁/C2 guard exec 硬化/C3 九门权威/C4 tools.lock 信任链/C5 签发四门/High 逐项/战场件/Medium 裁决

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修掉六专家对抗评审 5 Critical（账本写路径非原子/guard exec 绕过/九门伪造快进/tools.lock 信任根=仓内测试钥/报告签发四绕）+ High 逐项 + 靶场首战战场件三件，Medium 逐条裁决收口或登记，全部以「红测=复现专家反例」TDD 落地。

**Architecture:** 不新增命令、不动 13 表 schema（微版本勘误通道）：执法面全部在既有 cli/ledger 单源内收紧——写路径 core.write_tsv/Ctx 全体换 tmp+os.replace（state_md.py:92 先例）+goal 级文件锁；guard 门链前置 argv 归一化与主机变体解码；门事件词进保留字白名单（append-timeline 拒收、run_gate 单源铸造）；tools.lock 信任面隔离+runtime digest 比对；sign_gate 前置授权门+落盘后复扫。

**Tech Stack:** Python 3.11/3.12 标准库（fcntl/msvcrt/hashlib.pbkdf2_hmac/hmac/os.replace/subprocess/multiprocessing）；openssl 子进程验签（既有 supply_chain 单源）；unittest+金样 run_golden 既有机制。

**Spec（三源，执行者必读）:**
- docs/design/2026-09-27-expert-review-consolidated.md —— 六专家台账：5 Critical（全部带文件:行号与复现命令）+High+Medium
- docs/HANDOFF.md「2026-09-27 靶场 LLM 在环首战记录」节 —— 真实 8/20、键失配归因、工具缝四条（terminal-gate 冻结断言等）、技能改进八条
- docs/design/2026-09-21-tanyin-v2-design.md §2 铁律（尤其铁律 5 四层执法/铁律 7 薄 CLI 边界）+§8.5 四层执法语义；§5.2/§5.4 门语义
- 现状基线：748 单测全绿 + 54 金样面 PASS（hash=a347edd7）+ 44 命令面；HEAD=980cff8

## Global Constraints
- 纪律：全部新文件 UTF-8 无 BOM+LF；Windows 入口 `py -3` 等价（.cmd 配对不动）；时间戳显式 `--timestamp=ISO8601` 禁墙钟进账本（egress 运行时日志与 vault nonce 除外，见 T10/T11 裁决）
- 标准库零依赖：不新增 pip 依赖；openssl 仅子进程（验签既有单源 supply_chain.py）
- 金样 54 面零漂移为默认纪律；本计划 T7（信任钥轮换）与 T10（vault 双读过渡）两个任务允许**有意刷新**，刷新面必须单列名单并声明 delta
- 契约面变更（旗标/必填参数）一律微版本勘误（schema_version=2 不递增，文末补记节），T17 统一回注；任何任务不得改 13 表列集与 44 命令名
- 退出码契约冻结 0=通过/1=门禁拒绝/2=用法或环境错误
- 本批红测定义：**红=复现专家复现命令的实测反例**（台账 evidence 列原文），不是泛化单测失败
- panorama/ 与 /Users/wgen/Documents 零触碰
- 每任务 TDD 先红后绿；收尾必跑全套 unittest + run_golden + git status --short 为净

## 背景反例坐标速查（写红测时逐条对照）
| # | 专家复现 | 证据位 | 红测落点 |
|---|---|---|---|
| C1 | write_tsv open(w) 原地截断；SIGKILL 8/8 丢史（200008 行→8KB）；16 并发 add-fact 存活 5 行双 PASS | core.py:52-57；write_cmds.py:241-251 | T1/T2/T3 |
| C2 | rm -r -f / rc=0；http://134744072/（十进制 8.8.8.8）rc=0 | tanyin-guard gate_chain:84-107；enforce.py:39-47,157-213 | T4/T5 |
| C3 | append-timeline 连发 gate-exit:P0..P6 → gate P6 already-passed exit 0 | write_cmds.py:968-985；core.py:110-153 | T6 |
| C4 | fixtures 测试钥重签篡改行 check_lock=0；runtime 不比对 nuclei digest | engines/nuclei/adapter.py:23-46；tests/fixtures/keys/ | T7 |
| C5 | sign 零 approvals 校验；draft 手改直通；goals sha256=deadbeef+过期窗 sign rc=0；脱敏扫描先于落盘 | report_lint.py:228-315/169-224/255-263 | T8/T9 |

## 文件结构图（本批全部触达面）
```
cli/ledger/
  core.py            [T1] write_tsv 原子化；[T6] 保留事件词常量
  filelock.py        [T2 新] goal 级跨平台写锁（fcntl/msvcrt 单源）
  registry.py        [T2] 写命令面接线（锁取自写命令注册表单源）
  write_cmds.py      [T1] Ctx.write_file 原子化；[T6] _append_timeline 保留词拒收
                     [T13] add-fact --no-consume；[T14] matrix-set --batch-file
  enforce.py         [T4] normalize_cmd argv 归一；[T5] _decode_ip_obfuscation 主机变体
  tanyin-guard       [T4/T5] gate_chain 双形比对；[T15] --cred/--action/--timeout；[T10] deploy-vault --secret 退出 argv
  phases_engine.py   [T3] run_restart 孤儿对账；[T12] --usage/--round 必填+阈值消费
  supply_chain.py    [T7] 不动（单源复用）
  engines/nuclei/adapter.py [T7] verify() 增 runtime sha256 比对
  report_lint.py     [T8] _authorization_gate+gates.authorization；[T9] draft 字节比对+pass.json 绑定+落盘后复扫
  vault.py           [T10] nonce+EtM-HMAC+PBKDF2+密钥外移（冻结接口签名不动，双读过渡）
  egress_proxy.py    [T11] decide() oob/canary 判定+build_acl 产 [oob]/[canary] 段+墙钟+轮转+超时
  knowledge.py       [T13] score() 缺基线=ENV 错（exit 2 载体）
  matrix_init.py     [T14] --from-assets 资产类裁剪（默认行为不变）
  check_cmds.py      [T16] terminal-gate 冻结断言改「freeze 时在场行」
tests/
  test_atomic_write_b7.py       [T1 新]
  test_goal_filelock_b7.py      [T2 新]（16 并发 add-fact 存活）
  test_kill9_write_fidelity.py  [T3 新]（200k 行×SIGKILL 8 次+restart 孤儿对账）
  test_guard_argv_norm_b7.py    [T4/T5 新]（专家反例集全录）
  test_gate_authority_b7.py     [T6 新]
  test_tools_trust_face.py      [T7 新]（信任面隔离断言）+engine-nuclei 金样面有意刷新
  test_sign_gates_b7.py         [T8/T9 新]（四绕反例全录）
  test_vault_aead_b7.py         [T10 新]（m1^m2=c1^c2 反例）
  test_egress_oob_canary_b7.py  [T11 新]
  test_restart_threshold_b7.py  [T12 新]
  test_no_consume_k1_b7.py      [T13 新]
  test_matrix_batch_b7.py       [T14 新]
  test_guard_perm_actions_b7.py [T15 新]
  test_scorer_norm_b7.py        [T16 新]（+check_cmds terminal-gate 回归）
  test_b7_medium_closeout.py    [T17 新]（evals vacuous+impact 死分支）
  tests/range/RUNBOOK.md        [T16] GT 键口径显著位新节
  tests/range/ground-truth.json [T16] host_aliases 别名声明位
docs/design/2026-09-27-b7-discovery-notes.md [T17 新]（Medium 裁决表落盘+遗留登记）
docs/HANDOFF.md                  [T17] 流水+状态快照批次 7 行
contracts/（文末补记节）          [T17] 微版本勘误（旗标/必填参数面）
```

## 任务总览（17 任务；每任务独立 TDD 循环+全套回归+commit）
- **T1** 账本写路径原子化：core.write_tsv + Ctx.write_file → tmp+os.replace 单源化（红=半写失败旧内容零损反例）
- **T2** 写命令入口 goal 级文件锁：filelock.py 跨平台单源；写命令注册表全覆盖（台账 18/19 缺失并入）；红=16 并发 add-fact 存活
- **T3** 真 SIGKILL 保真测试+restart 孤儿对账：200k 行 timeline SIGKILL×8（SRE 协议）+三段写孤儿事件对账通道
- **T4** guard argv 规范化：deny-list 双形比对（组合短旗标拆并+长旗标映射）；红=rm -r -f / 反例
- **T5** guard 主机提取硬化：十进制/十六进制/八进制/短式 IPv4 变体解码；红=专家反例集全录
- **T6** 九门权威：append-timeline 保留事件词拒收（gate-exit:/gate-fail）；门事件由 run_gate 单源铸造；红=伪造快进复现
- **T7** tools.lock 信任链：测试钥轮换+信任面隔离断言+adapter runtime nuclei digest 比对
- **T8** 签发四门①授权完整性：auth_doc sha256 比对+窗口门+approvals verify-signoff 强校验；红=deadbeef/过期窗 sign rc=0
- **T9** 签发四门②③④：draft==render_fd 字节比对+pass.json 三工件哈希绑定+落盘后脱敏复扫
- **T10** vault 加密升级：nonce+EtM-HMAC+PBKDF2 KDF+密钥外移+--secret 退出 argv（双读过渡保金样）
- **T11** egress OOB/canary 并入 decide+compile 产 [oob]/[canary] 段+墙钟注入+日志轮转+socket 超时
- **T12** restart 阈值消费：--usage/--round 必填；auto 档 0.75/10 轮阈值执法（单源=phases 默认键）
- **T13** 触发器 no-consume 通道（add-fact --no-consume）+K1 缺基线 exit 2
- **T14** 矩阵批量置格（matrix-set --batch-file，全成全败）+资产类词表裁剪（--from-assets，默认不变）
- **T15** permitted_actions 执法接线：guard --cred/--action account-grant 覆盖门+guard --timeout 通道
- **T16** 战场件：scorer URL 归一化匹配（host 别名）+GT 键口径前置显式化+terminal-gate 冻结断言按 freeze 在场行
- **T17** Medium 裁决收口包（evals vacuous guard+impact 死分支）+裁决表落盘 b7 台账+契约/README 微版本勘误+HANDOFF 记账+push

## Medium 裁决表（T17 落盘到 docs/design/2026-09-27-b7-discovery-notes.md；本表=权威裁决）
| Medium | 裁决 | 去向/判定 |
|---|---|---|
| 退出码塌缩（env 错→1 非 2） | 部分收口 | T10（vault 缺钥=2）/T13（K1 缺基线=2）触达面分型；全仓分型审计登记 v3 |
| supersede 死命令（dup 只能夹具铸） | 遗留 | v3（需新命令面+契约变更）；b7 台账登记 |
| deferred 无出边吸收态 | 遗留 | v3（设计变更：deferred 复活臂）；b7 台账登记 |
| 冻结可追加 frozen_at="" 行 | 收口（裁决+钉死） | T16：追加合法（P3 生长通路 G-2），锚点断言改按 freeze 在场行；测试钉死语义 |
| cred.scope_asset 悬空→图静默丢边 | 遗留 | v3（图查询读侧悬空告警）；b7 台账登记 |
| 端口/服务变更触发器无机检 | 遗留 | v3（TRIGGERS 目录第九类）；b7 台账登记 |
| ④high/critical 死分支（impact 枚举只有高中低） | 收口 | T17：死分支清除或双语归一，grep 判定零残留 |
| evals 空目录 vacuous pass=8 | 收口 | T17：零指标文件=FAIL（vacuous guard）+测试 |
| 等保常量+R11 未审 | 遗留（真人） | 维持批次 6 出口 #17 移交态：R11 人工法务过审，真人载体不变 |
| 真人复核无身份锚 | 遗留 | v3（身份体系超薄 CLI 边界，依赖宿主/组织侧）；b7 台账登记 |
| guard 60s 硬超时 | 收口 | T15：--timeout=秒（默认 60 上限 600）+用法错 exit 2 |
| 重放单报文 | 遗留 | v3（tanyin-replay 多报文/序列重放扩展） |
| 侦察工具未入锁 | 遗留（真人） | 随生产钥仪式（install/KEY-MANAGEMENT 流程）重签 tools.lock 扩键；b7 台账登记 |
| egress now 常量/日志无轮转/无超时 | 收口 | T11：墙钟注入（serve 默认真墙钟，测试显式注入）+5MB×3 轮转+30s socket 超时 |
| 安装只增不删混版 | 遗留 | v3（uninstall/升级面新命令）；b7 台账登记 |

## 出口验收清单（全批完成判定；T17 逐条亲跑并在 HANDOFF 记录）
1. 全套单测：`python3 -m unittest discover -s tests -p "test_*.py" -t .` → OK，计数 = 748+本批新增（T17 记录实际数），零 FAIL 零 ERROR
2. 金样：`python3 tests/run_golden.py` → 54 面 PASS；有意刷新面（T7/T10 名单）之外 hash 前后一致；`git status --short tests/golden` 仅含名单内面
3. C1 原子+锁+保真：`python3 -m unittest tests.test_atomic_write_b7 tests.test_goal_filelock_b7 tests.test_kill9_write_fidelity -v` → 绿；SIGKILL 8/8 后 verify-chain PASS+行数不回滚；16 并发 add-fact 全存活
4. C2 硬化：专家反例集逐条——`guard exec -- rm -r -f /`→REJECT rc=1；`guard exec -- curl http://134744072/`→REJECT host=8.8.8.8；全部反例参数化测试绿
5. C3 权威：`append-timeline --event=gate-exit:P0 …` → REJECT rc=1 零落账；既有干跑 eval（test_dryrun_p0p2）三门 gate-exit PASS 不受扰
6. C4 信任链：信任面隔离断言绿（测试钥签名×生产锚 verify=False）；nuclei 二进制篡改→blocked 提交；`engine-nuclei-adopt` 金样面有意刷新已声明
7. C5 四门：deadbeef 授权书/过期窗口/零 approvals sign → rc=1 gates.authorization FAIL；draft 手改→rc=1；pass.json 篡改→verify rc=1；落盘后复扫绿
8. High 逐项判定：vault m1^m2 关系不成立+篡改 fail-closed；egress compile 含 [oob]/[canary] 且 decide 放行 oob+告警 canary；restart 缺 --usage/--round=exit 2、阈值不足 auto=REJECT；add-fact --no-consume 过 trigger-audit；K1 缺基线=exit 2；matrix-set --batch-file 批量全成全败；guard --action 越权 REJECT
9. 战场件：scorer 别名匹配回归（svc 键×127.0.0.1 GT 键→MATCH）；terminal-gate freeze→matrix-set→PASS 回归绿；RUNBOOK GT 键口径节在盘
10. Medium：裁决表在 b7 台账（15/15 行逐条有裁决）；两个收口件测试绿；遗留项均有去向字段
11. 契约一致性：契约文末补记节含 no-consume/batch-file/--usage/--action 勘误；`python3 -m unittest tests.test_knowledge_contract` 绿（工具面 14 不变）
12. 纪律面：`git status --short` 全净；panorama/ 与 /Users/wgen/Documents 零触碰（`git log --stat` 复核）；UTF-8+LF（`file -I` 抽查新文件）
13. push：`git push origin` 成功，远端 HEAD=本批收口 commit

---

## 任务正文

（骨架已落盘；任务正文按 T1→T17 增量补齐，每 2-3 任务一 commit。）


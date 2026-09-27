# 批次 7 探知项台账（Medium 裁决表 15/15 落盘+执行期探知项 G-42..G-46+遗留登记·T17 收口）

> 来源：①批次 7 计划「Medium 裁决表」15/15 行原文誊录（docs/superpowers/plans/2026-09-27-b7-remediation.md:97-114——本表=权威裁决，逐行落终态证据）；②批次 7 施工期新增探知项如实登记（G-42..G-46）；③状态归并=遗留项去向字段逐行落 v3/生产钥仪式/真人三去向；④允许刷新名单 delta 声明（T7/T9/T10 三任务名单全部未动用）。
> 通道纪律：契约回注一律微版本勘误（contracts/02a 文末「批次 7 旗标/必填面一笔记」补记，schema_version=2 不递增）；Ruling 逐条记 HANDOFF「批次 7 各任务流水+裁决」节（本文件不重复）。

## 一、Medium 裁决表（计划原文誊录=裁决；终态证据列=T17 落盘新增）

| # | Medium | 裁决 | 终态证据/落点 |
|---|---|---|---|
| M1 | 退出码塌缩（env 错→1 非 2） | 部分收口 | T10（vault 缺钥=2）/T13（K1 缺基线=2）触达面分型已落地（test_vault_aead_b7/test_no_consume_k1_b7）；**全仓分型审计遗留→v3** |
| M2 | supersede 死命令（dup 只能夹具铸） | 遗留 | **v3**（需新命令面+契约变更；13 表列集与 44 命令名冻结约束在册） |
| M3 | deferred 无出边吸收态 | 遗留 | **v3**（设计变更：deferred 复活臂；M4 收口不涉出边语义） |
| M4 | 冻结可追加 frozen_at="" 行 | 收口（裁决+钉死） | **T16**：追加合法（P3 生长通路 G-2）钉死；terminal-gate 锚点断言改「freeze 时在场行」（全表任意 frozen_at 非空行，check_cmds.py）；测试钉死 test_scorer_norm_b7.TestTerminalGateFreezeAnchor（freeze→set→PASS+未冻结仍 FAIL 收紧不放水） |
| M5 | cred.scope_asset 悬空→图静默丢边 | 遗留 | **v3**（图查询读侧悬空告警；graph_cmds 读面零触碰本批） |
| M6 | 端口/服务变更触发器无机检 | 遗留 | **v3**（TRIGGERS 目录第九类；phases/TRIGGERS.md 封闭表版本化通道既有） |
| M7 | ④high/critical 死分支（impact 枚举只有高中低） | 收口 | **T17**：死分支清除——phases_engine._HAZ/viz_render.HIGH_SEVERITIES 收敛单值「高」（write_cmds impact 枚举 {高,中,低} 单源），grep 判定零残留=test_b7_medium_closeout.TestImpactDeadBranchGone |
| M8 | evals 空目录 vacuous pass=8 | 收口 | **T17**：vacuous guard——零指标文件/指标文件缺=FAIL rc=1 输出点名 vacuous（evals_metrics.main 判定入口）；测试 test_b7_medium_closeout.TestEvalsVacuousGuard 双例（零指标+缺文件） |
| M9 | 等保常量+R11 未审 | 遗留（真人） | 维持批次 6 出口 #17 移交态：R11 人工法务过审，真人载体 docs/HUMAN-REVIEW.md 不变 |
| M10 | 真人复核无身份锚 | 遗留 | **v3**（身份体系超薄 CLI 边界，依赖宿主/组织侧；HUMAN-REVIEW 复核人≠执行者纪律既有） |
| M11 | guard 60s 硬超时 | 收口 | **T15**：--timeout=秒（默认 60 上限 600）+用法错 exit 2（test_guard_perm_actions_b7）；超时⇒REJECT 点名 timeout rc=1 |
| M12 | 重放单报文 | 遗留 | **v3**（tanyin-replay 多报文/序列重放扩展） |
| M13 | 侦察工具未入锁 | 遗留（真人） | 随生产钥仪式（install/KEY-MANAGEMENT 流程）重签 tools.lock 扩键；G-22 仪式移交态不变 |
| M14 | egress now 常量/日志无轮转/无超时 | 收口 | **T11**：墙钟注入（serve 缺省真墙钟，测试显式注入）+5MB×3 轮转+30s socket 超时（test_egress_oob_canary_b7） |
| M15 | 安装只增不删混版 | 遗留 | **v3**（uninstall/升级面新命令） |

归并统计：**收口 6**（M4=T16 裁决钉死/M7、M8=T17 两件/M11=T15/M14=T11/M1 部分收口触达面）+**遗留 9 全部带去向**（v3=M2/M3/M5/M6/M10/M12/M15；生产钥仪式=M13；真人=M9）。

## 二、执行期新增探知项登记（G-42..G-46，施工期如实）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-42 | **已收口·T16** | scorer main() 输出行变量残留（gt→entries 更名后 len(gt) 悬空引用）——计划测试面只覆盖 score() 纯函数、不含 CLI 打印路径；git diff 复核当场拦截修复+main() 冒烟探针（空会话 0/20 rc=1+20 MISSING 行）在案；教训=R-T12-5「分段读+diff 复核」纪律再生效（工具缝：打印面不被红测覆盖处靠复核兜底） |
| G-43 | **登记·遗留 v3** | Tier2 hooks/simulate.py 仍字面 deny_hit(joined)——normalize_cmd/deny_forms 单源已落 enforce（T4），Tier2 接线不在 T4 计划 Files 面（R-T4-3 原文登记转正）；「Tier1/Tier2 同源执法」承诺的另一半 |
| G-44 | **登记·已知边界 v3** | cmd_sign 末端 report_artifacts.write_all（findings.json/sarif/report-*.md）落盘居 sign_gate 复扫之后=门内不可达（R-T9-3）——已知边界非豁免，契约 02a 批次 7 补记第 8 条同笔登记 |
| G-45 | **登记·遗留 v3** | K1 基线 init 运行时库缺省不带（R-T13-3 尾注）——「Init 库默认带基线」留 v3；现行执法=缺基线文件 exit 2/缺行 warning+0.5 两态分流（M1 触达面同笔） |
| G-46 | **已收口·T17** | evals 指标文件缺路径原为裸 traceback（专家「空目录」反例的实形之一，无 vacuous 词样无 rc 契约位）——vacuous guard 扩展覆盖缺文件面（FAIL rc=1 点名 vacuous），test_b7_medium_closeout.test_missing_metrics_file_fails_not_crash 钉死 |

## 三、允许刷新名单 delta 声明（T7/T9/T10 三任务名单全部未动用）

- 计划允许有意刷新三处：T7 测试钥轮换（engine-nuclei-adopt 面）——**名单未动用**（R-T7-5：根 tools.lock 由 release.pub 配对钥签发验签面无感+本机无 nuclei 二进制 runtime digest 缺失不比，git status tests/golden 零行）；T9 pass.json（lint/sign 面）——**名单未动用**（R-T9-4：run_golden 54 面无 lint/sign 面）；T10 金样 deploy 面——**名单未动用**（R-T10-5：golden 面实勘无 vault/deploy/egress-compile/restart 面）。三任务收尾 git status tests/golden 皆零行实测。
- 全批金样 54 面 PASS 零漂移（各任务流水 ×N 跑+T17 终跑 golden-exit=0 在册）——「金样零漂移为默认纪律」兑现，唯一例外通道全程未启用。

## 四、移交清单（批次 7 收口后待办）

- **R11 法务过审**（M9/真人）：等保占位段与免责表述样张人工法务过审一次，结论一行入 HANDOFF（批次 6 出口 #17 移交态延续）。
- **G-22 真钥生成仪式**（M13 同批）：离线介质机人工执行+KEY-MANAGEMENT §执行记录位；重签 tools.lock 时一并裁决侦察工具扩键（M13）。
- **真人复核 10 页**：docs/HUMAN-REVIEW.md 附录表待真人填写（复核人不得为本批次执行者）。
- **CI 远端复核**（出口 #13 后置项）：push 后 GitHub Actions 页面复核矩阵+evals job 绿（本环境无 gh CLI，HANDOFF 状态快照行如实注记）。
- **契约 v3 预定**：G-4 重启成本定标+G-37 token 系数回写（批 6 既有）+批 7 新登记 M2 supersede 命令面/M3 deferred 复活臂/M5 图悬空告警/M6 触发器第九类/M10 身份锚/M12 序列重放/M15 uninstall/G-43 Tier2 接线/G-44 write_all 边界/G-45 Init 基线缺省/M1 退出码全仓分型审计。
- **G-38 walcode/CodeBuddy 实测回传**：批 6 移交态不变（guided 回传→矩阵升档）。


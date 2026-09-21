# 批次 1：账本命令箱 + 黄金夹具——实施计划

> 目标：实现 41 条账本命令（python3 标准库单文件入口 cli/tanyin-ledger）+ tanyin-guard/tanyin-redact 骨架 + 夹具框架。出口=**夹具字节级回归全绿 + 负向用例全 REJECT**（定稿 §11 批次 1；契约=contracts-v2 tag）。
> 唯一输入：contracts/01（146 字段）、contracts/02+02a（41 命令签名=附录 A）、定稿 §4/§5.3。冲突时契约赢；契约未载→停+登记探知项，不发明。

## 文件结构（全部新增，不动 docs/）

```
cli/
  tanyin-ledger          # 单入口可执行（python3 标准库；shebang；子命令 dispatch）
  ledger/
    __init__.py
    core.py              # TSV 读写/转义/schema 校验/ID 铸造/链式哈希
    write_cmds.py        # 写命令 19（追加+写前拒收）
    query_cmds.py        # 查询命令 11（过滤行流，单行 TSV 输出）
    check_cmds.py        # 校验命令 10（PASS/FAIL+原因清单）
    special.py           # 特殊命令 1（redact-scan 交付终检）
  tanyin-guard           # 骨架：占位+四关卡接口（批次 2 完整实现）
  tanyin-redact          # 脱敏扫描器（redact-scan 的独立入口）
tests/
  test_ledger.py         # 41 命令单测（unittest，标准库）
  test_negative.py       # 负向用例：全 REJECT 断言
  fixtures/              # 黄金夹具：固定样本 session（13 表钉死编码）
  golden/                # 期望输出（字节级）
  normalize.py           # 规范化：剥时间戳/ID 重映射/行排序稳定化
  run_golden.sh          # 全量回归入口（退出码 0/1/2 对齐 Strix）
```

## 任务（TDD：每命令先写失败测试再实现；每任务出口=测试绿+提交）

- **T1 core 骨架**：TSV 解析/转义（\\t\\n\\r 转义律）/13 表加载/schema_version=2 校验/ID 铸造 {前缀}-{goal-id}-{四位序号}/timeline 链式哈希（哈希输入=全行）。测试：转义往返、哈希链篡改即断。
- **T2 夹具框架**：fixtures/ 样本 session（每表 3-8 行真实感数据，.example 域名）+ normalize.py + run_golden.sh 骨架。测试：规范化确定性（同输入两次跑 diff=0）。
- **T3-T6 写命令 19**（按 02a 签名逐条，每条含拒收）：T3 账本六写（add-goal/add-scope/add-intent/set-intent-status/add-fact/add-finding）；T4 证据与supersede（add-evidence/supersede-finding/add-cred/set-cred-status）；T5 图谱与修订（add-asset/add-edge/amend-scope/redact-scan/state-rebuild/set-replay-state）；T6 派生与清理（add-submatrix/…按附录 A 清单补齐至 19）。
- **T7-T8 查询命令 11**：unconsumed-facts/pending-intents/matrix-gaps/converge-check/next-id/intent-status/matrix-get/scope-check/budget-check/cleanup-checklist/ledger-tree…（以附录 A 为准）。输出=单行 TSV 流，幂等可排序。
- **T9-T10 校验命令 10**：validate/verify-chain/hash-recheck/matrix-audit/state-rebuild 校验面 + 九门断言四条（scope-coverage/tree-check/replay-summary/terminal-gate）。PASS/FAIL+原因清单，退出码 0/1。
- **T11 special：redact-scan**：扫全部 TSV+卡片，{{vault:}} 占位符泄漏/明文凭据模式（来源 02a 拒收条件）→ tanyin-redact 双入口。
- **T12 tanyin-guard 骨架**：四关卡接口桩（批次 2 填实现），不阻塞本批出口。
- **T13 黄金夹具全量回归**：fixtures×41 命令→golden/ 期望文件锁定→run_golden.sh 全绿；剥时间戳后字节级 diff。
- **T14 负向用例**：每写命令≥1 拒收路径（枚举外/引用断/Tier0 违规/幂等冲突），断言 exit≠0 且账本零变更。
- **T15 收口**：README（cli/ 用法+41 命令速查）+ 全量回归演示 + 用户验收包。

## 执行方式

- 三实现代理并行不可行（同文件依赖 core）——**串行主干**：T1→T2 主线程亲自（地基精度最高）；T3-T11 派两代理交替（写/查+校验两组，接口=core 冻结后并行安全）；T13-T15 主线程。
- 每任务出口跑 python3 -m unittest 对应模块全绿才提交；commit 粒度=任务。
- 沙盘：全部只在 ~/redteam-agent 仓内新增 cli/ tests/，绝不写 ZhuLong。

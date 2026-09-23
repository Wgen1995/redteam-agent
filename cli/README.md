# tanyin-ledger · 账本命令箱（批次 1）

探隐 TanYin 的 13 表 TSV 账本唯一写入口。契约基线 contracts-v2（41 命令 / 147 字段 / 九门 / 10 边）。

## 用法

```
cli/tanyin-ledger <command> --goal-dir <session-dir> [--key=value ...]
```

- 退出码：0 成功 / 1 门禁失败（REJECT，账本零变更）/ 2 用法或环境错误（对齐 Strix）
- 时间戳必填 --timestamp=ISO8601（写命令确定性来源）
- 一切写命令：写前全量校验，追加目标表行 + timeline 链式哈希事件

## 命令面（41）

| 类 | 条数 | 命令 |
|---|---|---|
| 内建 | 3 | validate / verify-chain / next-id |
| 写 | 19 | add-goal add-scope add-intent add-fact add-finding add-asset add-cred add-edge add-evidence set-intent-status set-cred-status supersede-finding amend-scope matrix-set matrix-freeze append-timeline approve budget-log checkpoint |
| 查询 | 11 | unconsumed-facts pending-intents matrix-gaps converge-check next-id intent-status matrix-get scope-check budget-check cleanup-checklist redact-scan |
| 校验 | 10 | validate verify-chain hash-recheck matrix-audit state-rebuild set-replay-state ledger-scope-coverage ledger-tree-check ledger-replay-summary ledger-terminal-gate |
| 特殊 | 1 | matrix-init（P1 门：词表 WSTG v4.2 钉死列、基线冻结） |

## 测试与回归

```
python3 -m unittest discover -s tests       # 181 单测（含 02a §32 跳门检测 7 例 + Tier2 模拟器 8 例）
python3 tests/run_golden.py                 # 黄金回归 41 命令，两次执行确定性自证
python3 tests/make_fixtures.py              # 重铸夹具（13 表确定性样本）
```

## 目录

- cli/ledger/core.py：转义/147 字段 schema/ID 铸造/链式哈希（禁改：契约生成）
- cli/ledger/schemas.json：由 contracts/01 机械生成（禁手改）
- shared/VOCAB.md：词表（WSTG v4.2，版本化）
- tests/golden/：基线锁（漂移即 FAIL）

## 批次 2：门禁层（四层执法档位）

| 组件 | 层 | 职责 |
|---|---|---|
| tanyin-guard | Tier 1 | exec 流水：deny-list→scope 解析→request-ticket→参数化执行→输出兜底重 tokenize；inject=四关卡①执行点回注（vault cred-N.enc+manifest） |
| hooks/ | Tier 2 | 三宿主 fail-closed 模板+模拟器（deny-list+scope 界外拦截；阻断=非零+timeline hook-block；与 guard 共用 ledger/enforce.py 单源） |
| tanyin-egress | Tier 3 | compile：scope.tsv→egress.acl 四成分（ACL/DNS pin/OOB/infra）；verify=漂移检测；dry-run=代理模板（实代理批次 6） |
| tanyin-canary | 全档 | deploy 界外诱饵（seed 确定性）+probe tier 0-3 零容忍；结果 JSON 落 timeline |
| tanyin-budgetctl | Tier 0 | enforce 预算树余量+rate 速率熔断（超限 REJECT 落账） |
| special.py 扩模式 | Tier 0 | redact +16 泄漏形态（赋值/连接串/cookie/NTLM/gh 变体…）注入拦截率 100% |

出口验证：canary 各档位零容忍（tier0 scope-check 5/5、tier1 guard 5/5、tier2 hook 模拟器 5/5、tier3 真编译 ACL 5/5）；redact 注入 36/36=100%、误报 0；预算/速率限额拒绝可测（budget-exhausted/rate-limit REJECT 落 timeline）。

边界：python3 3.9+ 标准库零三方依赖；state.md 完整结构留批次 3；实代理与真宿主挂载=批次 6 靶场；vault 现为 sha256 密钥流 XOR（条目格式不变，批次 6 换真加密）。

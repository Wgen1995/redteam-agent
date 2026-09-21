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
python3 -m unittest discover -s tests       # 129 单测
python3 tests/run_golden.py                 # 黄金回归 41 命令，两次执行确定性自证
python3 tests/make_fixtures.py              # 重铸夹具（13 表确定性样本）
```

## 目录

- cli/ledger/core.py：转义/147 字段 schema/ID 铸造/链式哈希（禁改：契约生成）
- cli/ledger/schemas.json：由 contracts/01 机械生成（禁手改）
- shared/VOCAB.md：词表（WSTG v4.2，版本化）
- tests/golden/：基线锁（漂移即 FAIL）

边界：python3 3.9+ 标准库零三方依赖；guard 实现留批次 2；state.md 完整结构留批次 3。

# resume-kit · 恢复注入白名单（先对账再干活）
goal: G-r27-0001
current_gate: P4
updated: 2026-10-23T09:00:00Z

## 0 对账（必须先过；任一失败=停止并人工，禁止跳到干活）
1. tanyin-ledger verify-chain --goal-dir <D>       → PASS 才继续
2. tanyin-ledger state-rebuild --goal-dir <D>      → FAIL 则 tanyin-phases rebuild-state 后复跑本条

## 1 注入白名单（新会话上下文只许进这些）
- state.md（handoff 与 snapshot）
- resume-kit.md（本文件）
- phases/P4.md（当前门方法论，单门单载）
- 四个查询摘要各一次（计数+top-N，禁全量回灌）：pending-intents / unconsumed-facts / matrix-gaps / budget-check

## 2 禁注入清单（铁律 2 上下文生命周期受管）
- 13 表 TSV 全量回灌 / 工件原文（artifacts/、*.raw）/ 子代理会话记录

## 3 幂等续跑判定（重入先查此表）
- INT-r27-0001  SKIP
- INT-r27-0002  SKIP
- INT-r27-0003  SKIP
- INT-r27-0004  SKIP
- INT-r27-0005  SKIP
- INT-r27-0006  SKIP
- INT-r27-0007  SKIP
- INT-r27-0008  SKIP
- INT-r27-0009  SKIP
- INT-r27-0010  SKIP
- INT-r27-0011  SKIP
- INT-r27-0012  SKIP
- INT-r27-0013  SKIP
- INT-r27-0014  SKIP
- INT-r27-0015  SKIP
- INT-r27-0016  SKIP
- INT-r27-0017  SKIP
- INT-r27-0018  SKIP
- INT-r27-0019  SKIP
- INT-r27-0020  SKIP
- INT-r27-0021  SKIP
- INT-r27-0022  SKIP
- INT-r27-0023  SKIP
- INT-r27-0024  SKIP
- INT-r27-0025  SKIP
- INT-r27-0026  SKIP
- INT-r27-0027  SKIP
- INT-r27-0028  SKIP
- INT-r27-0029  SKIP
- INT-r27-0030  SKIP

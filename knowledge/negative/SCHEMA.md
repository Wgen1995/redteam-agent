# 避坑卡 schema（negative 卡型·kn-v1 兼容扩）

> 来源：docs/design/evolution-flywheel-v1.md 第 2 齿（正知识+负知识双轨——战后复盘
> 蒸馏 CP 技法卡，负面结果已入 facts[W3c 律]，避坑卡接上）。机器面单源=
> scripts/capability_gate.py（validate_negative_card/write_negative_card/
> read_negative_cards）；本档=knowledge/ 侧 schema 件（人读+示例锚）。
> 蒸馏管线本体（retro→蒸馏→落卡）=W5 知识环舰，本 schema 只留读写面。

## 1 卡型定位

- 避坑卡=CP 技法卡家族的**负轨**：失败路径（哪条路走不通）+触发条件（何时该
  避开）+出处（**账本行号**——可回放核验，不凭口述）。
- 物理落位 knowledge/negative/CP-NNNN.md（不在 tanyin-knowledge LINT_ZONES
  六类冻结面——契约 14 零触碰；W5 蒸馏舰接管正式区时再议入册）。
- 编号空间：与 knowledge/cp-index.tsv 共享 CP- 四位零填充空间，跨索引连续
  分配（next_negative_id=两索引 max+1，禁双头跳号）。

## 2 front matter 字段（必填九键）

| 字段 | 必 | 约束 |
|---|---|---|
| id | 必 | CP-NNNN 四位（家族共享空间，写面自动分配） |
| kind | 必 | kind: negative（技法卡正轨=kind: technique，双轨同库不同值） |
| title | 必 | ≤60 字（一句话说清坑） |
| failure_path | 必 | 失败路径（哪条路走不通） |
| conditions | 必 | 触发条件（何时该避开——条件不满足则该路仍可走） |
| ledger_ref | 必 | battle-数字/表名.tsv:行号 形（出处=账本行号：哪场仗哪张表第几行） |
| vuln_class | 必 | 词表键（关联正轨技法域，检索注入面同源） |
| status | 必 | core/learned/demoted 三枚举（初始 learned） |
| last_verified | 必 | ISO 日期 |

可选键：source_id/applicability/judgment/cost_hint/source_topic（正轨技法卡
同义兼容）。卡体建议三节：`## 失败路径` `## 触发条件` `## 出处`。

## 3 索引：cp-index 家族兼容扩列

- 本目录 ng-index.tsv：**前六列与 knowledge/cp-index.tsv 逐名同序同义**
  （id/title/source_id/source_topic/status/updated——经典读方零破），扩列四键
  kind/failure_path/conditions/ledger_ref 可选追加（缺列=空）。
- knowledge/cp-index.tsv 本体保持 50 行六列冻结（W3 舰
  tests/test_w3_cp_ingest.py 钉）——负面轨索引独立落 ng-index.tsv，读取面
  read_index_family 两形通吃（经典六列/扩列十列）；后续若正面索引迁移
  扩列，读方零改。
- updated=卡 last_verified（确定性重生成锚，cp-index 同律）。

## 4 写面纪律

- 仓库种子库只读（R7）：write_negative_card 对仓库 knowledge/ 拒写
  （SeedFrozenError）；运行时库（$TANYIN_HOME/knowledge）落卡。
- 校验不过=拒写（缺必填/ledger_ref 非账本行号形/kind 错/status 越枚举）。
- W5 蒸馏舰接口：战后复盘（retro RT-xxxx）蒸馏 → write_negative_card(
  knowledge_dir, fields, body) 一函落卡（卡 md+索引行 upsert 原子对）。

## 5 变更联动（评测棘轮）

knowledge/negative/ 在能力件 pathspec 内（scripts/capability_gate.py
CAPABILITY_SPECS.technique_cards）——避坑卡增删改=能力件变更，合并前过
GT-scorecard 增量门（召回/误报不得回退，宪法#43）。

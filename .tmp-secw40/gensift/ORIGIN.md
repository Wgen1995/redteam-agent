# 原始来源声明（ORIGIN）

- 技能名：gensift（源码自动漏洞挖掘·逐项证伪）
- 原始来源：委托人自有生态仓库 `/Users/wgen/Sectest/GenSource`（本地 git 仓库），子目录 `gensift/`
- 导入时基线：git `57adc0f`（2026-08-27）
- 导入方式：本地打包 `zip` + `multica skill import --file`（Multica 工作区技能库）
- 本文件为导入时附加的来源声明，未改动任何原始文件内容

## 导入裁剪说明（平台限额所致，非内容取舍）

Multica 技能入库限额：单技能 ≤256 个支撑文件、总量 ≤8 MiB、单文件 ≤1 MiB。
原始 gensift 全量为 1783 文件 / 7.7 MiB，超出文件数限额，故做如下裁剪：

| 目录 | 原始规模 | 入库处理 |
|---|---|---|
| fixtures/ | 1623 文件 / 6.4M | 不入库（测试夹具，非运行时依赖） |
| SKILL.md / README.md / agents/ / classes/ / phases/ / langpacks/ / hosts/ / hooks/ / invariants/ / feedback/ | 160 文件 / 1.4M | 全量入库 |

fixtures/ 完整内容仍在同机原始仓库 `/Users/wgen/Sectest/GenSource/gensift/fixtures/`。

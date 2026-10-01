# 原始来源声明（ORIGIN）

- 技能名：gensource（源码自动漏洞挖掘顶层调度，含 skills/ 九个子阶段技能）
- 原始来源：委托人自有生态仓库 `/Users/wgen/Sectest/GenSource`（本地 git 仓库），子目录 `gensource/`
- 导入时基线：git `57adc0f`（2026-08-27）
- 导入方式：本地打包 `zip` + `multica skill import --file`（Multica 工作区技能库）
- 本文件为导入时附加的来源声明，未改动任何原始文件内容

## 导入裁剪说明（平台限额所致，非内容取舍）

Multica 技能入库限额：单技能 ≤256 个支撑文件、总量 ≤8 MiB、单文件 ≤1 MiB。
原始 gensource 全量为 1627 文件 / 9.7 MiB，超出限额，故对 knowledge/ 知识层做如下裁剪：

| 目录 | 原始规模 | 入库处理 |
|---|---|---|
| knowledge/industry-catalog/ | 975 文件 / 4.7M | 仅保留 `_index.md`（行业目录索引） |
| knowledge/vuln-patterns/ | 150 文件 / 1.5M | 仅保留 `_index.md`（漏洞模式索引） |
| knowledge/fix-patterns/ | 143 文件 / 828K | 仅保留 `_index.md`（修复模式索引） |
| knowledge/attack-patterns/ | 122 文件 / 752K | 仅保留 `_index.md`（攻击手法索引） |
| knowledge/ 其余（sinks/sources/surfaces/entries/propagation/controls/ontology/ecosystem-mappings/coverage/_templates/change-batches/README/FALSE-rules） | 全量入库 | 检测管线脚本硬依赖（enumerate.py 读 `sinks/_index.md`） |
| SKILL.md / USAGE.md / ARCHITECTURE.md / skills/ / agents/ / contracts/ / shared/ | 全量入库 | 编排与契约层完整保留 |

完整知识语料仍在同机原始仓库 `/Users/wgen/Sectest/GenSource/gensource/knowledge/`，索引指向的
细目（VULN-/FIX-/ATK-/SRC-/UVS- 条目）需深读时按索引中的 ID 到原始仓库读取。

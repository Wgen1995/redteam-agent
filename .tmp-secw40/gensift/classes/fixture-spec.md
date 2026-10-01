# fixture-spec ｜ 枚举 fixture 三类语义与 manifest 规范

> 位置：`fixtures/enum/{class}/{lang}/{pos,neg,noise}/`，每语言一份 `manifest.tsv`（TSV，首行表头）。
> 用途：枚举层 pattern 的回归基准——manifest 回填与对账口径的唯一事实源；各类页面 ⑫ "见 classes/fixture-spec.md" 均指本文件。

## §1 三类语义
- **pos（正例）**：危险形态实样本。pattern **必须命中**——对账要求命中≥1，且命中 id 集与 manifest `expected_patterns` 完全一致。
- **neg（硬负例）**：与攻击面无关的形态，pattern **必须零命中**。"同一 API 的安全用法"不是 neg（分界见 §2）。
- **noise（噪音）**：同一 sink 锚上的安全/硬化用法。pattern **允许命中**（锚在），是否有安全问题由各类页面 ⑥ 五步判别收口；manifest `expected_patterns` 留空。

## §2 noise 与 neg 的分界
- 枚举层不区分安全/危险用法：同一 sink API 的硬化形态（绑定参数、白名单、UUID 改名、owner/tenant 谓词、唯一约束兜底等）sink 锚仍在——进 **noise**，由 ⑥ 判别翻案，不进 neg。
- **neg 只放 pattern 不命中的无关形态**（非 sink 上下文、非数据访问、纯常量操作等）。判据类（resource-exhaustion / promo-logic / tenant-isolation / config-security 等）同理：命中锚但安全语义成立的进 noise，pattern 不命中的合规形态才进 neg。

## §3 manifest.tsv 规范
- 首行表头：`file	kind	expected_patterns`，按类可追加 `framework` / `provenance` / `note` 列（该类页面 ⑫ 声明）。
- 数据行：`{pos|neg|noise}/{文件名}	{kind}	{expected_patterns}	…`；多个命中 id 以「、」连接；neg/noise 行 expected 留空（保留列分隔符）。
- `expected_patterns` 填法：对 pos 文件实跑该类该语言 pattern 件的全部 ERE（`NR>6` 数据行），记录**全部**命中 id（含家族标记类锚，如 RX-J01 之于 RX-J05）；neg 期望空。
- 出处列（provenance/note）必填的类：取 fixture 首行 `出处:` 之后的内容。
- 对账口径：pos 全部命中≥1 且命中集＝expected；neg 零命中；磁盘 pos/neg/noise 文件与 manifest 数据行一一对应（noise 允许命中、不计入对账）。

## §4 规模档位（类页面 ⑫ 引用的基准）
- **达标集**（java 全量）：pos≥10 / neg≥20 / noise≥5。
- **起步集**（ts/python，或门在判据而非 pattern 完备度的类）：pos≥6 / neg≥8 / noise≥3。
- **判据类起步集**（fixture 以 java 代表）：pos≥4 / neg≥4 / noise≥2。

类页面 ⑫ 的数字为**目标规格**；与实际达成不一致时，以 manifest 实跑对账结果为准，页面应改写为实际达成值或"无 fixture（待补）"。

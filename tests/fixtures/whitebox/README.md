# tests/fixtures/whitebox/ — 车道A解析器 v0 回归夹具（W4 第一段）

## 来源与指纹（零手改拷贝）

- `enum/` 与 `patterns/` 全部字节级拷贝自 `knowledge/staging/gensift-intake/`
  （GenSift 规则源入库件，commit 126c19a）；拷贝时逐文件对照
  `knowledge/staging/gensift-intake/MANIFEST.tsv` 的 sha16 指纹校验通过后才落盘
  （迁移脚本对 111 个样本+8 个 pattern 文件全数 assert）。
- `enum/` 为**代表子集**（正/负/噪声三类齐全）: 8 个 class×lang 组合,
  覆盖 python/java/ts 三语言与 sink/判据两类角色:

  | class×lang | pos | neg | noise | 备注 |
  |---|---|---|---|---|
  | sqli/python | 8 | 8 | 3 | 全量迁移 |
  | sqli/java | 6 | 5 | 2 | |
  | sqli/ts | 5 | 4 | 2 | |
  | cmd-injection/python | 6 | 5 | 2 | 含 POSIX 类混合括号形态 CI-P12 |
  | ssrf/ts | 5 | 5 | 2 | |
  | xxe/java | 6 | 6 | 2 | |
  | authn/java | 7 | 6 | 2 | 家族标记类锚 |
  | proto-pollution/ts | 6 | 6 | 2 | band 1 判据类 |

  每语言目录内 `manifest.tsv` 为对应子集行（表头原样保留,
  `expected_patterns` 列即 GenSift grep -E 实跑口径——翻译件必须逐 id 复现）。
- `patterns/` 为 8 个 .pattern 冻结拷贝（金样封闭性: staging 追加不漂移金样）。
  对账语义按 `classes/fixture-spec.md`: pos 命中集=expected（「、」分隔）,
  neg 零命中, noise 允许命中不计对账。

## 解析器谱图夹具（`src-tree/`）

合成三语言源码树（python/java/ts 各一）, 钉死:
符号表（函数/类/方法+签名哈希）、调用边、pattern 命中
（sqli S-P01 / authn AN-J01 / xxe X-J01+X-J02 / ssrf SS-T01 /
proto-pollution PP-T11 / sqli-ts S-T02）。

## 金样（`golden/`）

`golden/codegraph.jsonl` / `golden/pattern-hits.jsonl` / `golden/digest.json`
= 解析器对 `src-tree/` + `patterns/` 的字节级输出钉死（确定性律:
同输入逐字节同输出）。解析器行为**有意**变更时随同提交更新金样并在提交注记归因。

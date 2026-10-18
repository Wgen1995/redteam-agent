# gt-baseline-v1 注记（2026-10-19T00:00:00Z）

## 三场基线（gt_eval.py·keying v7·分母=range-56-v5）

| 战 | recall | hits | active | FP | precision |
|---|---|---|---|---|---|
| battle-40 / G-r41 | 0.62 | 35/56 | 66 | 31 | 0.530 |
| battle-41 / G-r42 | 0.62 | 35/56 | 38 | 3 | 0.921 |
| battle-42 / G-r43 | 0.70 | 39/56 | 40 | 1 | 0.975 |
| 均值 | 0.645 | — | — | 11.7 | 0.809 |

对照既有 0.71 基线参考值：battle-42=39/56=0.696≈0.70（40/56 形=0.714——0.71 即此带，
仓内无 0.71 逐字记录；13 战史均值 0.55-0.59/峰值 0.70 在册）。三场均值 0.645 低于参考值
主因 b40/b41 两战 0.62——评测棘轮以此为锚：能力件变更后同卷复跑不得低于本表。

FP 首采：b40=过度报告战（96 findings 行/66 活跃，FP=31——重复报告+诱饵面命中）；
b42 FP=1（precision 0.975=历史最佳）。FP 口径=活跃发现数−GT 命中数（合成靶场全真值=GT）。

## 新 GT 战场入库核验（gt_verify.py）

- 快照锚根：rows=15 pass=15 fail=0（rc=0）
- 活靶 ZhuLong 仓（只读实跑）：rows=15 pass=15 fail=0（rc=0）——伤疤锚定真仓 HEAD。
- 新增真发现行（open）=6：zl-web-01..04 + zl-sup-01..02；修复回归锚（fixed-anchor）=4；
  FP 诱饵负对（neg）=5。索引：evals/gt/gt-index.tsv（6 战场行：1 session-gt+2 source-gt+3 replay-fixture）。

## 升格入册

replay-fixture：G-r25（0.62）/G-r26（0.57）/G-r27（0.41）——真战会话夹具升格为回放锚
（scorer 恒定 recall 防尺子漂移；gold 测试原在册，索引化后 capability_gate 可数）。

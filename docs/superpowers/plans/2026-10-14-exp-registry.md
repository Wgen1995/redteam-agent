# 度量纪真律落地 · Plan（2026-10-14 批，用户「继续」）

> 缘起： v0.9c 诚实披露——N=5 判决 b=8,c=17 的子集清单未入库，页面不可机械复现。本批立律+回填。

## Task R1 · 实验登记处格式与回填（experiments/ + tests/test_exp_registry.py）
- 格式： experiments/<exp-id>.tsv，列=field\tvalue（key-value 行式，TSV 简单可 grep）：
  id / question / battles_control（空格分 battle-id）/ battles_treatment / gt_gen / decision_rule / registered / status / verdict / source（出处文件:行）/ note。
- experiments/README.md： 格式律（预登记实验必须先落 tsv 再开战；判决后回填 verdict；无登记=度量页不认）。
- 回填 directive-n5： 主会话已考据候选子集——对照 {b29,b30,b35,b36,b37}=值 [0.64,0.66,0.70,0.41,0.70] / 处置 {b28,b38,b39,b40,b42}=值 [0.46,0.59,0.57,0.62,0.70]（HANDOFF:1356-1361 值匹配反推）。
  **机械验证步**： 用 cli/webui/metrics.py 的装配+池化在真实数据上跑该子集——若复现 b=8,c=17（p=0.107752）→ source 记「HANDOFF:1356 值匹配+机械复现」；若不复现→做小子集搜索（对照/处置各 ≤5 战、值约束匹配）穷举验证；仍不复现→verdict 记「子集不可复原」+note 说明，诚实收场。
- 测试： 登记 tsv 解析（读回 dict）/缺字段降级/无 experiments 目录空表。

## Task R2 · 度量页接线（metrics.py + server + 页面小改）
- metrics.py 增 experiments_view(repo_root)： 读 experiments/*.tsv → 列表；/api/metrics.json 增 "experiments" 键。
- metrics.html 统计卡下加「预登记实验」小节： 列 exp-id/question/verdict/battles；无登记显示「无预登记实验」。
- 测试： API 键存在/页面节点存在/只读律钉死。

## 纪律
TDD 红绿；3.9 纯 stdlib；py_compile；零 git；只碰 experiments/、cli/webui/metrics.py、cli/webui/static/metrics.html、tests/test_exp_registry.py（或并入 test_v09c_metrics.py 新类，二选一说明理由）；全量回归自跑。

# evals/ — 评测集版本化根（宪法#43·评测棘轮的测量地基）

本目录=GT（ground truth）评测集的版本化家。评测棘轮（evolution-flywheel-v1 §飞轮六齿4：
一切能力件变更合并前必须过 GT-scorecard 评测增量——召回率/误报率不得回退）以本目录为
测量地基；capability_gate 消费 `gt/gt-index.tsv`（消费契约见 gt/README.md）。

布局：
- `gt/gt-index.tsv` — GT 战场注册表（战场/真发现数/口径/入库时间；单源）
- `gt/battlefields/` — source-gt 战场（白盒源码锚：ZhuLong 靶场伤疤）
- `gt/snapshots/` — 锚承载快照（CI 可离线校验；活靶实跑用 --live）
- `gt/gt_verify.py` — 注册表校验器（行完整性/索引一致/锚可跑；rc 0/1/2）
- `gt/gt_eval.py` — 会话 GT 评测跑（召回/误报/精度；复用 scorer 单源）
- `gt/baselines/` — 基线表（追加式）+对照注记

既有评测件（历史在册，未迁移）：
- `tests/range/ground-truth.json` — session-gt 主战场（56 面，keying v7，由索引行引用不复制）
- `tests/eval_range_recall.py` — 会话 scorer（单源；gt_eval 复用其 load_session/score）
- `tests/evals/metrics-v1.json` — L1-L3 指标注册（M09/M10 消费 range GT）
- `tests/golden/` + `tests/run_golden.py` — 金样 54 面（字节回归，M01）
- `tests/fixtures/G-r2x` — 真战会话夹具（已升格入册为 replay-fixture 锚）

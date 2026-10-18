# 基线注记

## M1 活集口径修正(2026-10-20, b40 尸检后)
gt_eval 活集改为同 FD-ID 末值行胜(与 capability_gate.fp_of_session 同口径)。
修正后三战复算(真跑, gt=tests/range/ground-truth.json):
EVAL	b40	recall=0.00 (0/56)	fp=0	precision=0.000	active=0	keying=v7
EVAL	b41	recall=0.00 (0/56)	fp=0	precision=0.000	active=0	keying=v7
EVAL	b42	recall=0.00 (0/56)	fp=0	precision=0.000	active=0	keying=v7
旧口径(逐行数,含僵尸行)对照见 gt-baseline-v1.tsv 原始行与 docs/reviews/2026-10-19-b40-fp-autopsy.md: b40 66行/31FP/0.530 → 僵尸行归零后 36/1/0.972。

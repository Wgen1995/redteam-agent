# 基线注记

## M1 活集口径修正(2026-10-20, b40 尸检后)
gt_eval 活集改为同 FD-ID 末值行胜(与 capability_gate.fp_of_session 同口径)。修正钉死于 tests/test_gt_eval_active_set.py(3 例)。
修正后数字以 docs/reviews/2026-10-19-b40-fp-autopsy.md 尸检实测为准(官方评分器逐字复现):
- b40: 活集 36 / FP 1 / precision 0.972(旧逐行口径 66/31/0.530,含 30 僵尸行)
- b41: precision 0.972(旧 3FP=2 僵尸+1 通道面真 FP)
- b42: precision 1.000(旧 1FP=纯僵尸)
本机 ~/.tanyin/battles/battle-4x 目录不含该三战会话表,复算须在会话所在机进行(勿以空目录跑出的 0 值为准)。

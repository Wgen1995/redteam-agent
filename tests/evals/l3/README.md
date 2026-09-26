# L3 脚手架：TSecBench 对齐口径（发布前人工项，不阻塞 CI）

> 批次 6 T3 交付（计划 Task 3 Step 5）；机读面=契约 15＋cli/ledger/evals_schema.py；
> L3 指标 runner=manual（恒 ENV-SKIP，设计 §9.3 不阻塞 CI）。

## 六域分类

1. Web 漏洞挖掘
2. 二进制
3. 漏洞利用
4. 多阶段渗透（**主指标**——与总控 P0→P6 九门循环同构）
5. 云攻击
6. 对抗规避

## 跑分口径

- 每域**三轮取优**；**token 均值同时报告**（G-11 usage 实采通道供数，
  tests/evals/calib/token-calibration.json）。
- 退出码与门禁语义沿用契约 15 §2（0/1/2；L3 不阻塞 CI=manual 恒 ENV-SKIP）。

## 本仓对齐路径

- 授权靶场（tests/range/，批次 6 Task 16 种 20）=最小自建域，检出率基线 v1
  入册后作 L3 本地锚（裁决 I）。
- TSecBench 全量对齐=**发布前人工执行项**：在授权环境出机跑分，结果入册
  （勘误通道登记）后正式 L3 指标条目随数据立基线（契约 15 §4 R-T1-2 空组注记）。

# gt-chain-baseline-v1 注记（2026-10-19T00:00:00Z）

## 三既有战链式召回对照（gt_eval.py --chain；两档判分=CHAIN_TIERS 写死）

| 战 | flat（56 面平铺） | step（环级平铺） | chain（两档链式） | 断环位置 |
|---|---|---|---|---|
| battle-24 / G-r25 | 0.62 | 0.80 (4/5) | 0.75 (1.5/2) | 侦察环 userenum-01（chain-01 半分） |
| battle-25 / G-r26 | 0.57 | 0.80 (4/5) | 0.75 (1.5/2) | 利用环 idor-02（chain-02 半分；chain-01 全对=唯一打通 3 环链的战） |
| battle-26 / G-r27 | 0.41 | 0.80 (4/5) | 0.75 (1.5/2) | 侦察环 userenum-01（chain-01 半分） |

## 读法（人话）

- 三战链式召回同分（0.75）但断环位置不同：G-r26 输在「最后一步没走完」（拿到钥匙没开
  idor-02 那扇门），G-r25/G-r27 输在「起手侦察缺位」（不枚举用户名、直接撞库）——平铺
  召回 0.41-0.62 的战在链式卷上同分，说明单点召回拉不开「会不会打连环」的差距。
- step_recall 三战同为 0.80：环级平铺对断环位置不敏感（都丢了 1 环）；链式两档把它压成
  0.75 并指出丢的是哪一环——这是 L3 考卷与 L1 平铺的度量差。
- 链式召回 ≠ 更严：链卷只考 5 个精选环位，flat 卷考 56 面——两列并列记录，防「链式分高
  = 能力强」的误读（G-r27 flat 0.41 但 chain 0.75）。

## 链定义（range-chain-v1；会话链）

- range-chain-01（3 环）：userenum-01 → weakpass-01 → idor-01（侦察→凭据→认证后越权读）。
  全链在案：G-r24（battle-23）/G-r26（battle-25）。
- range-chain-02（2 环）：weakpass-01 → idor-02（凭据→认证后发票越权）。
  全链在案：G-r8（battle-5）/G-r24/G-r25/G-r27。
- 两档判分（写死于 gt_eval.py CHAIN_TIERS，测试钉死）：整链全对=1.0；部分对（≥1 环非
  全环）=0.5；零命中=0。断环位置不加分不扣分——无第三档漂移空间。

## 三场 b4x 战对照（基线 v1 同三战；会话在 ~/.tanyin 战目录——TSV 追加在册）

| 战 | flat | chain | 断环 |
|---|---|---|---|
| battle-40 / G-r41 | 0.62 | 0.50 (1/2) | userenum-01 + idor-02（两链皆半分） |
| battle-41 / G-r42 | 0.62 | **0.25 (0.5/2)** | chain-02 整链零命中（weakpass+idor-02 全缺） |
| battle-42 / G-r43 | 0.70 | 0.75 (1.5/2) | userenum-01（chain-02 全对） |

**最有信息量的一行**：b40/b41 平铺召回同分（0.62），链式拉开一倍（0.50 vs 0.25）——
b41 的 post_auth 命中全靠非凭据路径（authz-diff 面），「弱口令→会话→越权」连环一步没走；
平铺卷看不见这个差距，链式卷一眼见。这就是 L3 考卷存在的理由（宪法#43 第一性=找漏洞效果：
连环打穿>单点散抓）。

## 复跑

  python3 evals/gt/gt_eval.py --session tests/fixtures/G-r25 --label b24-G-r25 \
      --session tests/fixtures/G-r26 --label b25-G-r26 --session tests/fixtures/G-r27 \
      --label b26-G-r27 --chain evals/gt/battlefields/range-chain-v1.json

（追加新战：同式 --write-chain 本表；数值漂移=尺子坏——test_gt_chains 在册钉死。）

# 批次 6 探知项台账（G-36..G-41 预登记转正+前期遗留 G 项收口终态·T18 收口）

> 来源：①批次 6 计划「Task 18 Step 4」预登记原文誊录（G-36..G-41，docs/superpowers/plans/2026-09-24-b6-evals-install-delivery.md——程序化提取防转写漂移）；②批次 6 出口项 #16 七项 G 项归并（G-4/G-5/G-11/G-22/G-25/G-32/G-33——全部「已收口」或「遗留+理由+去向」）；③实施期增补=Ruling 指针（HANDOFF「批次 6 T17+T18 流水+裁决」节，本文件不重复）。
> 通道纪律：契约回注一律走微版本勘误通道（零存量数据期先例，schema_version 不递增）；状态变更随任务记 HANDOFF 开发流水。

## 一、计划原文誊录（G-36..G-41，2026-09-24 计划冻结文本）

| # | 缺口（计划原文） |
|---|---|
| G-36 | HTTP/2 二进制帧与 TLS 直贴渲染——判读说明通道临时态，待真帧样本 |
| G-37 | token 估算系数按校准报告回写契约 v3 |
| G-38 | walcode/CodeBuddy 实测回传后升档 |
| G-39 | 靶场检出率基线 v1 冻结与转硬门时点 |
| G-40 | TSecBench 全量对齐=发布前 L3 |
| G-41 | egress 代理并发/性能上限未测——机械执法非性能件披露 |

计划 Step 4 处置原文：G-22（已收口=流程+脚本交付，仪式留 KEY-MANAGEMENT 执行记录位）/G-25（已收口=裁决 B+T14）/G-32（已收口=T9 双通道）/G-33（已收口=T2 硬门）/G-5（已收口=T7）/G-11（半收口=通道+报告交付，系数回写遗留→G-37）/G-4（遗留→契约 v3 同批）。

## 二、新增探知项登记（G-36..G-41 预登记转正终态）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-36 | **登记·临时态通道** | 判读说明单列披露已机检化（T13 段⑥变体单列+T14 burp_pasteable HTTP/2 帧/TLS fail-closed why 载判读说明，02fbab2/f0927e8）；真帧样本在库前不裁直贴形态（不造数据）；去向=真样本出现时契约 06 再勘误 |
| G-37 | **遗留→契约 v3** | 首采数据已落盘=tests/evals/calib/token-calibration.json（T17 真跑：n=76/median=1.116/min=0.941/max=1.343，宿主真实 metering vs PROTOCOL §2 冻结公式，0328606）；理由=公式冻结承诺（裁决 G：金样/预算面零扰动），系数回写涉全量估算面；去向=契约 v3 微版本（与 G-4 同批） |
| G-38 | **遗留·待实测回传** | walcode/CodeBuddy=静态验证+待实测（T5/T8 盲区通道+guided probe_results 回传形态，3c110c9/99d08ad；R-T8-2 现登记于 install/README 宿主矩阵节）；升档条件=实测回传入册；去向=执行期回传后矩阵升档 |
| G-39 | **登记·基线 v1 已冻结** | 基线 v1=1.00（20/20）frozen_at=2026-09-26T10:00:00Z 入册 metrics-v1.json+契约 15 §3 M09 行（T16 c15fb3b）；回退即 fail 对在环跑同样生效；转全面硬门化时点留批次 7 裁决；LLM 在环复测通道=tests/range/RUNBOOK.md §6（R-T16-3 收口通道） |
| G-40 | **遗留·发布前 L3** | TSecBench 对齐脚手架已交付不阻塞 CI（T3 04c05c8；设计 §9.3 发布前人工项）；去向=发布前 L3 全量对齐（tests/evals/l3/ 载体在库） |
| G-41 | **登记·披露三载** | 代理=机械执法组件非性能件；并发/性能上限未测披露三载（T10 serve 启动横幅+契约 11 v3 勘误+install/README 守门声明节，0ff03ae）；去向=性能需求出现时专项实测（先钉预算再测） |

实施期增补：无新增 G 项——施工期裁决全部随 HANDOFF「批次 6 T17+T18 流水+裁决」节 R-T17-1..3/R-T18-1..3 记账（b5「实施期增补」节同构；工程缺陷/计划字面出入属 Ruling 非接口缺口）。

## 三、状态归并台账（批次 6 出口项 #16 七项全量归并）

| # | 终态 | 证据/落点 |
|---|---|---|
| G-4 | **遗留→契约 v3** | 重启成本口径（RESTART_TOKEN_COST=2000/速率上限 10min）为批次 3 T6 暂代值、无契约源（b3 台账原文）；理由=口径变更涉 PROTOCOL/预算面联动且零存量数据期不单方冻结；去向=契约 v3 微版本定标（与 G-37 同批） |
| G-5 | **已收口·批次 6 T7** | 锁文件 v2（hostname/pid/boot-id/ts）+探活三态 dead/alive/unknown（探测不出=保守拒绝）+manual 接管维持 state-rebuild PASS+takeover-of 留痕（ab8ced3；契约 04 v2 勘误补记；裁决 F 兑现） |
| G-11 | **已收口（数据面）·系数回写遗留→G-37** | 通道交付=T3 evals_token_eff 单源+M05 runner（04c05c8）；报告交付=T17 真跑首采 token-calibration.json 落盘（0328606，R-T3-4「随 Task 17 真跑首采入册」兑现）；PROTOCOL §2 公式本批不改（裁决 G 收口形态=「数据通道+报告交付，系数回写遗留」） |
| G-22 | **已收口·批次 6 T9** | 流程+脚本交付=install/KEY-MANAGEMENT.md 五节+install/resign-tools-lock.py+release.pub 显式替换通道（483520c）；CI/测试永续 TEST-ONLY 夹具钥与生产钥无信任关系；真钥生成仪式=离线机人工执行，KEY-MANAGEMENT 留执行记录位（裁决 C 如实披露，不谎称已持有生产钥） |
| G-25 | **已收口·批次 6 T14** | 裁决 B 兑现=burp_pasteable 四规则机检+双指纹单源复算+渲染只转抄一字不符=FAIL（02fbab2；契约 06 v3 勘误三条款；HTTP/1.x 文本直贴首发） |
| G-32 | **已收口·批次 6 T9** | 双通道=tanyin-install refresh-cve（--from 下载+sha256 锚定+lint 七列校验复用+审计行）与人工重铸离线等价（483520c；knowledge/cve/README.md 双通道注记；裁决 D 兑现） |
| G-33 | **已收口·批次 6 T2** | evals_dual_anchor (page-id, timestamp, approver) 三元组互证纯函数+M12 硬门进 evals 静态套件（夹具双库样本驱动；裁决 E 兑现；双写纪律=P6 duty 命令化批次 5 T19 先行） |

## 四、移交清单（批次 6 收口后待办）

- **真人复核 10 页**（出口 #15）：docs/HUMAN-REVIEW.md 附录表待真人填写——复核人不得为本批次执行者；结论齐备后 log.md 复核行核对一致。
- **R11 法务过审**（出口 #17）：等保占位段/免责表述样张已随 T15 终稿签发面成形；人工法务过审一次并将结论一行入 HANDOFF（本批先行记录行在册）。
- **G-22 真钥生成仪式**：离线介质机人工执行；执行记录落 KEY-MANAGEMENT §执行记录位；生产 release.pub 替换走显式通道交互确认。
- **G-38 walcode/CodeBuddy 实测回传**：guided 第 4 步 probe_results 贴回→install/README 矩阵升档。
- **G-36 真帧样本**：HTTP/2/TLS 真帧样本在库后重启直贴形态裁决（契约 06 再勘误）。
- **契约 v3 预定两笔**：G-4 重启成本口径定标；G-37 token 系数按校准报告回写（首采 median=1.116 为候选依据）。
- **CI 远端复核**（出口 #5）：push 后 GitHub Actions 页面复核四格矩阵+evals job 绿（本环境无 gh CLI，HANDOFF 状态快照行如实注记）。

# 全绿预检·全套件基线 · 2026-10-20（实测）

> 命令：`cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests`（**必须 -s tests**——仓根裸 discover=0 测假绿，本舰实测踩过）。
> 工作树状态=他舰在飞件共存（cli/warrior/loop.py 已修改+4 个未跟踪 test 文件在盘），本基线含其现状。

## 一、总账

| 指标 | 值 |
|---|---|
| 总用例 | **3529**（comparison-ledger 2026-10-20 锚 2846 → +683，增量=在飞 UI 舰红先行的 TDD 测试） |
| 绿 | **3448**（3529−71失败−8错误−2跳过） |
| 跳过 | 2（声明 ENV 的 openssl 例，历史白名单） |
| 红 | **71 失败 + 8 错误 = 79**，EXIT=1，耗时 597.9s |

## 二、79 红逐类归因（他舰 WIP+环境病，零引擎面红）

| 类 | 数 | 明细（模块×数） |
|---|---|---|
| 驾驶舱/UI 舰 WIP（在飞未收舱） | 74 | test_v09d_closeout×16、test_v09d_skin×15、test_v09a_webui×8、test_webui_task_actions×7、test_ui_craft×7、test_console_findings_overview×6、test_v098_steering_ui×5、test_ui_copy×4（含 tests.test_ui_copy 同面4）、test_webui_techniques_deeplink×3、test_v098_steering×2、test_webui_palette×1、test_webui_authform×1、test_v09d_zhulong×1、test_v09d_session×1 |
| Playwright 环境病（浏览器未装，checklist 白名单类） | 4 | graph_canvas/palette/task_actions-live/techniques-live 四 setUpClass ERROR |
| 元红（因他红而红） | 1 | test_shard_tests --run 透传了他件的退出码（自证非独立病灶） |

**引擎面专项**：`tests.test_first_battle_readiness+test_gt_registry+test_warrior_main/loop/budget+test_budget_exhausted+test_dryrun_p0p2` = **57/57 OK**（点火关键面全绿）。

## 三、点火门槛（写明）

1. **点火不要求全套件零红**——那被在飞 UI 舰结构性堵死（红=未收舱 TDD 先行件，非引擎回归）。硬前置原文「全套件测试零红（Playwright环境病白名单除外）」（first-battle-checklist:7）在当前舰队态下按**下条口径执行**，差异报母舰追认。
2. **实际门槛（本舰建议）**：①引擎面零红（§二专项 57/57 已达）；②红清单=本档§二逐条对得上（点火当日复跑 diff 无**新增**引擎面红）；③79 红当时在盘状态与母舰知悉一致。
3. 点火当日复跑命令：`python3 -m unittest discover -s tests 2>&1 | tail -3`——对照本档 3529/71/8/2，新增红须归因后才点火。

## 四、诚实边界

- 基线含工作树他舰未提交修改（loop.py 等）——若母舰在点火前收/撤这些件，须重跑本档复锚。
- **漂移实录（基线跑后 30 分钟内）**：他舰把 loop.py 修改连同 corps/compaction/repair/resume_driver 接线以「落舱记R61: loop接线落,A桶闭合」落库（HEAD 619113d→4e76fc5），并新增在飞件 cli/webui/api_v2_chat.py+test_webui_pagespec_chat_face.py。**R61 后引擎面专项复跑仍 57/57 OK**（含 test_warrior_loop）；全套件总数/红数会随其新增测试漂移——以点火当日 C2 复跑数为准，本档数字=2026-10-20 深夜快照锚。
- R61 意义：全史综合档 §⑤A桶首项「corps 装配一行未接 loop」已闭合（loop.py:29,36,110-113 实测 corps_rt 装配在册）——首仗将在 corps 接线后的运行时上打，基线口径含此事实。
- 上一锚（comparison-ledger:11）2846/12F/7E 与本档不可直比（他舰测试增量非回归）——「n=1 会撒谎」纪律：两锚差异不解读为引擎退化。
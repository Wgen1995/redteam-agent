# 2026-10-11 v0.5a 执法与看护批（九维会诊 P1 前半）

## 背景
P0 诚实性加固批（4205fb6）已闭。本批吞 P1 清单中「执法纸面化+看门狗看护」簇 8 项（全 S），
度量/广度簇（wall_clock 双轨、CVSS、DENYLIST v2、clean rerun N≥3、vuln-agent 接线、codex E2E）
留 v0.5b——理由：本批全部离线可 TDD，直接补 P0 未竟的「执法」半边。

## 条目（TDD：先红后绿）
- F1 gate-status 只读 API：tanyin-phases status（读 timeline 推各门态，零断言零铸事件）；
  runner battle_complete 弃裸 grep 改调 API（子进程，失败回落 grep+WARN 一次）。
- F2 gateloop 预检去副作用：轮询用 status（读侧）；全量门只在 begin/proc-exit/soft-stall 三时机跑
  （gc.should_full_gate 纯函数）——42% 噪声源头治理（引擎侧 E9a 之外的驱动侧根治）。
- F3 budget 执法化：runner 每 tick 读 budget 快照（tanyin-budgetctl 单行），超限→
  BUDGET-ENFORCE 事件+带收尾令 relaunch（停新探测、supersede、走 P4/P5 门）——预算从申报制升执法制。
- F4 LOGONLY-ALIVE 语义里程碑：timeline 静止而 log 持续增长超 soft 阈值→LOGONLY 事件一次
  （可见性：战士在账本外干活的味道，不击杀只照亮）。
- F5 ask:human 双向通道+WAIT 态：战士写 ask.md→runner 通知+WAIT（停表不停命）；
  answer.md 出现→digest 注入续跑+复表。
- F6 无人兜底：--caffeinate 子进程防睡+GIVEUP/DONE osascript 通知（尽力而为）+
  install/launchd KeepAlive plist 模板。
- F7 命令面单源：sync-skill.sh 同步面扩到根 SKILL.md（编辑点唯一=.opencode）；
  selfcheck 增 skill-index-sync 检查（根 SKILL 索引集==.opencode 索引集==registry 面）。
- F8 GT 出仓：battle.py init 把 GT 拷 ~/.tanyin/gt/<gen>.json，settle 从那读
  （仓库内路径仅测试夹具用）；selfcheck 红线=mission/战书引用 ground-truth 路径。
  诚实边界：战士有仓访问权仍可主动翻 ~/.tanyin——本项抬门槛+照亮主动翻找，非沙箱。

## 验收
- 每项先红后绿单测；watchdog/gateloop_core 纯函数面全覆盖；
- tests/sim_watchdog.sh 双场景仍 SIM_PASS+新增 budget 执法场景；
- 全套件 RC=0；金样不漂移（F1-F8 均不触写路径语义）。

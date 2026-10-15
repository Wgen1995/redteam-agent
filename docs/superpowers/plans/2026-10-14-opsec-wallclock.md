# 旧欠清理批 · wall_clock 接线 + OPSEC 三小件（2026-10-14，用户「开」）

> 来源： docs/reviews/2026-10-10-nine-expert-review/02-opsec.md 可执行建议表（S 级四条中的三条半）+ HANDOFF:1371 接线欠。审计判词： 「内功九段外功一段」——本批补外功。

## Task WC · wall_clock battle 接线（scripts/battle.py）
- v0.7b 已有 cli/ledger/wallclock.py（event_text/mint_wall_sync/detect_gaps，经 phases_engine._append_event 入哈希链）。
- 接 battle.py 三铸点： init（战始 clock-sync）/launch（每战士 spawn 时 phase=launch）/settle（结算时 phase=settle）。
- 测试： 夹具 goal 目录跑三事件铸造断言 timeline 行存在+链验证过（仿 test_v08w_wire 风格）。若 battle.py 结构使单测不可行，最低限=冒烟脚本+断言函数抽取可测。

## Task OP1 · rate 入执法面 + DENYLIST v2（enforce.py/budgetctl/gate_chain）
- rate： budgetctl rate 滑窗熔断（tanyin-budgetctl 已有代码）接入 gate_chain 执法位 + P0 八问⑥ 必填（审计建议第一行「从查询面变执法面」）。
- DENYLIST v2： 补 DoS 工具/激进档模式（slowloris/hulk/goldeneye/可配置并发上限类）；**两份同步律**（shared/DENYLIST.md 与 enforce.DENY_EMBEDDED 必须同改，test_enforce_unit 钉死）。
- nuclei 固化： 模板/调用位固化 -rl 50 -etags dos,intrusive（找 tools.lock/templates 或调用模板真身，改后 digest 若变须同步 tools.lock 流程——只改模板参数不改二进制）。
- 测试： 新模式命中/不误伤（文档命令含 hulk 字样不炸）/rate 门拒超限/nuclei 参数存在性断言。

## Task OP2 · UA 治理 + request-ticket full argv（guard/replay 层）
- 禁自名 UA： grep 出 tanyin/1、probe/1.2、tanyin-replay/1 全部自报点位，改为中性默认（可配置 env 覆盖）；一处不留。
- replay --ua： tanyin-replay 加 --ua 旗标（重放请求的 UA 可指定，默认中性）。
- request-ticket 落 full argv： 记账从 cmd[0]+argc 升级为 tokenize 脱敏后全 argv（脱敏复用 vault 占位替换既有件）。
- 明确不做（本批界）： EV 卡加 ua 列——schemas.json 机械生成禁手改，须契约批次走 02a 修订，这里只记欠。

## 纪律
TDD 红绿；3.9 纯 stdlib；py_compile；零 git；白名单内文件；全量回归自跑；shared/DENYLIST.md 与内嵌兜底两处同步改。

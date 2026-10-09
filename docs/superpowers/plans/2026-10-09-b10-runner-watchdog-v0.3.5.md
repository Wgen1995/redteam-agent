# b10 · runner 看门狗四件套 v0.3.5

> 日期：2026-10-09 ｜ 状态：已批准（用户"开"）｜ 前置：b9 落帐 ｜ 蓝图：architecture-map-v3 第五节

## 目标与出口判据
看门狗从"能用"升到"multica 级"：①分级击杀（软停滞观察+硬停滞击杀）②重启指数退避（防崩溃风暴烧 token）③战中指令注入通道（免整场重启的补令）④自适应监听（活跃期秒级响应）。出口=四机制各有单测+全套件 RC=0+runner --help 兼容。

## 设计（纯函数抽取 cli/ledger/watchdog.py，runner 只做编排——零依赖铁律不动）
- stall_grade(sec, soft=180, hard=480) → 'ok'|'soft'|'hard'：soft=记一次 SOFTSTALL 观察事件（诊断 log 尺寸/timeline 行数，防误杀长推理的证据面），hard=击杀照旧
- backoff_delay(n, base=30, cap=480) → 30/120/480…：重启前 sleep，log BACKOFF 事件；battle 一次性冷启动不受影响（n=0 无延迟）
- read_directive(path, seen) → (text|None, digest)：控制文件变化才触发；触发=kill 当前+resume_prompt+指令 追加重启（multica pending 捎带同构，账本在盘所以重启即续）
- next_tick(active, tick, floor=1.0)：自适应节流——有活动 1s 级，静默指数回到 tick（macOS 无零依赖 FSEvents，诚实命名"自适应监听"非"事件驱动"）

## 任务
- T0 计划入册
- T1 tests/test_runner_watchdog.py（先红）：四函数全行为面+边界（soft 恰好/hard 恰好/cap 封顶/digest 变化/None 路径）
- T2 cli/ledger/watchdog.py 实现（转绿）
- T3 runner 接线：--soft-stall-min/--directive-file/--backoff-base 三参+主循环改造（SOFTSTALL/BACKOFF/DIRECTIVE 三事件入 runner.tsv）
- T4 套件+--help 冒烟+落帐（HANDOFF b10+蓝图 v0.3.5 翻绿）+push

## 风险
- 退避拖慢真恢复 → base 可配且 n=1 仅 30s；GIVEUP 判据仍用 max_restarts 不受影响
- 指令注入被误解为免重启热插 → 文档明写：注入=kill+带令续跑（账本在盘，等价 multica 捎带的效果语义）

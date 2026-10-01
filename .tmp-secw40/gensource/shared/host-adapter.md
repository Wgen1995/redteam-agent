# 宿主适配

挖掘逻辑与宿主无关。本文件只声明三个必须由适配层提供的动作：

1. 每轮先跑 `python3 contracts/sdwr/session.py drive --session {S}`。只按打印的 STATE 行动。
2. 派子代理 Analyzer：只分析 drive 列出的 NEXT 卡；prompt 用绝对路径。
3. 枚举：Grep/Glob 或 enumerate.py。套件根：Glob `**/gensource/SKILL.md`。

禁止在阶段 SKILL 里写死某个宿主的 Task/API 名。不能并行则串行并在 capability-profile.md 写 `parallel=false`。

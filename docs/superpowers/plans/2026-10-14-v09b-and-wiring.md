# v0.8a-接线 + v0.9b 观察面三页 · Plan（2026-10-14 批，用户「开」）

> Spec： tanyin-target-form.md §1（观察面 IA 三页=覆盖热图/十边图/证据卡）+ v0.8a 集成待办（HANDOFF 2026-10-14 段）。
> 纪律同前： TDD 红绿、3.9 纯 stdlib、py_compile、零 git（主会话集成）。

## Task W · llmpool 战场接线（cli/ledger/llmpool_wire.py + tests/test_v08w_wire.py）
- attach(goal_dir, env=None, now=None, rng=None) -> llmpool.Registry：state_path=<goal_dir>/llmpool_state.json；emit=包装 goal 账本 timeline 单源写方（与 webui 测试同款 append_tl_locked 路径），事件行 kind=llm_failover（event/model/reason/lane/cooldown_s 进负载）。
- 测试： ①attach 后 report 硬熔错误→goal_dir/timeline.tsv 新增 llm_failover 事件行（断言 kind 与负载字段）+state 文件落盘；②同路径重建 Registry→冷却窗恢复（重启语义）；③emit 写失败不外抛（llmpool 已吞，接线层不再引入炸点）；④attach 幂等（同 goal_dir 二次 attach 返回同实例或等价新实例+state 兼容——选定语义并文档化）。
- 注意： 找准 timeline 单源写方（勿绕开锁）。

## Task B1-B3 · 观察面三页（cli/webui 扩展 + tests/test_v09b_pages.py）
- B1 覆盖热图： GET /coverage → 页；/api/matrix.json → matrix.tsv 行+状态（frozen_at 有无）；前端纯 table+CSS 类渲染冷格/冻结格/空格（欠账红标）。
- B2 十边图： GET /graph → 页；/api/graph.json → 节点（各表 id+kind）+edges.tsv 边（10 种 kind）；前端 SVG 静态布局（分层或环形，vanilla，禁库）；边着色复用 viz_render 语义（attack 金/cross_ref 虚线/supersedes 点线——具体色值自定但 10 kind 全区分）。
- B3 证据卡： GET /evidence → 页；/api/evidence.json → E-index 行（id/vuln_ref/verdict/请求响应哈希）；点击展开明细（纯 DOM）。
- 共同律： 全部只读（投影律测试钉死：goal 目录字节不变）；每页 JS<2000 行；路由挂 server.py 既有三分支旁；测试用 mini 夹具（matrix/edges/E-index 各几行）断言 JSON 结构+页面关键节点存在。

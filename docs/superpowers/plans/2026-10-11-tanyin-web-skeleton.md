# tanyin-web v0.9a 观察面骨架 · Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL subagent-driven-development 或 executing-plans。
> Spec: docs/design/tanyin-target-form.md §1 观察面+§3 语言律。前置：无（独立可停）。
> 目标：零依赖只读投影骨架——stdlib 服务器+SSE 战局流+仪表盘首页，并实测 SSE 稳定性（spec 风险①）。

## File Structure
- cli/webui/__init__.py — 空
- cli/webui/snapshot.py — 只读账本快照（phases 态/budget/timeline 尾部 N 条→dict）
- cli/webui/sse.py — timeline 追尾生成器（线程模型，无 asyncio）
- cli/webui/server.py — ThreadingHTTPServer 路由：/ → static/index.html；/api/state.json → snapshot；/api/stream → SSE
- cli/webui/static/index.html — 手写仪表盘（战局态+budget+活动流容器；原生 JS <2000 行律）
- tests/test_v09a_webui.py — 全部 TDD 测试
- 每任务一 commit；语言律：纯 stdlib、3.9 兼容、py_compile 过

## Task 1 · snapshot 只读快照（TDD）
1. 写失败测试： fixture 账本目录（mini goals/budget/phases 状态文件+timeline.tsv 3 行）→ assert snapshot() 返回 dict 含 phases 态、budget 余量、最近 3 条事件（含每条 sha 前 8 位）
2. 跑测试确认失败（ModuleNotFoundError）
3. 实现 snapshot.py 最小版：只读解析，复用 phases_engine 只读 API（v0.5a 起 status 只读接口）与 timeline 读尾；禁止任何写
4. 测试过 → py_compile → commit "v0.9a T1 snapshot 只读快照"

## Task 2 · SSE 追尾生成器（TDD）
1. 失败测试： fixture timeline.tsv，sse.events(path, start_tail=2) 生成器先吐存量 2 条，再 append 1 行（测试内写入 fixture 副本）→ 下一次 next() 吐新行；行含 data: 前缀与 id: 游标
2. 确认失败 → 实现 sse.py（轮询间隔 1s，文件增长检测，游标=行号）
3. 过 → commit "v0.9a T2 SSE 追尾"

## Task 3 · HTTP 路由服务器（TDD）
1. 失败测试： 起临时端口 serve；http.client 断言 GET / 200 且 text/html 含 id="dashboard"；GET /api/state.json 200 且 JSON 键齐；GET /api/stream 100->data: 行（读 3 秒即断）
2. 实现 server.py：ThreadingHTTPServer+BaseHTTPRequestHandler，路由三分支；SSE 响应头 Content-Type:text/event-stream + X-Accel-Buffering:no
3. 过 → commit "v0.9a T3 server 路由"

## Task 4 · 仪表盘静态首页
1. index.html： 纯手写，战局卡片（phases 灯）+budget 条+活动流（EventSource 挂 /api/stream，append 行）
2. 测试： GET / 内容含 EventSource('/api/stream') 与 dashboard 根节点；JS 总行数 <2000（读文件断言）
3. 过 → commit "v0.9a T4 首页"

## Task 5 · CLI 入口（TDD）
1. 失败测试： runtime bootstrap 模式（v0.7a 同款）——python -m 或子命令 --help 冒烟 rc=0；--port/--ledger-dir 参数透传
2. 实现入口（挂 write_cmds/query_cmds 旁，遵循既有 CLI 装配模式）
3. 过 → 全量回归 python3 -m unittest → commit "v0.9a T5 CLI 入口"

## Task 6 · SSE 稳定性实测（spec 风险①关闭）
1. 脚本并发 5 连接×60s（真实 timeline 追写 1 行/s）——断言零断流、内存平稳（ps 采样）
2. 结果（数字）记入 HANDOFF v0.9a 段；不稳→按 spec 触发器换线程池方案（仍 stdlib）再测
3. commit "v0.9a T6 SSE 实测"

## 完成判据（全绿才收）
6 commit 落库；全量回归绿；SSE 实测数字入 HANDOFF；蓝图双胎加 v0.9a 行；present 首页截图（本地打开）。

## 后续计划（另立 plan，不在本计划内）
v0.9b 热图+十边图+证据卡页 / v0.9c 度量页 / v0.9.5 控制面（须单独审批）/ v0.8 借脑三件套（已呈批待开）。

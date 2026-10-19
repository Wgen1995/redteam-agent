# P0 指挥台+会话签+灰卡 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to execute this plan.用 brainstorming 已批的 docs/design/2026-10-20-product-master-design-v3.md 为纲;技术栈按其十六节(Next.js 新前端/引擎 Python 保留/写走 CLI 单写者链)。

## 铁律
- 测试跑法: PYTHONPATH=cli python3 -m unittest discover -s tests -q;管道出口码不可信,显式收 rc。
- 前端: web/ 新 Next.js 应用;单测 vitest,E2E Playwright(channel="chrome",缺浏览器则 env-skip)。
- 写路径一律经 tanyin CLI(单写者+锁+链);Next API 只读直读+写转发,不自写账本。
- pathspec 提交;人话词表;零假数。

## 文件结构(新)
- web/src/lib/ledger.ts — CLI 桥: query 类命令子进程调用→JSON(读面唯一通道)
- web/src/lib/engine.ts — 写转发: chat-say/approve/steer/kill→tanyin 子进程(带 env 密钥)
- web/src/app/(shell)/layout.tsx — 20 页 IA 侧栏+顶栏(搜索/预算表/全停红钮)+⌘K 位
- web/src/app/(shell)/p/chat/page.tsx — 指挥台(流+输入框+战况板)
- web/src/app/(shell)/p/mission/[id]/sessions.tsx — 会话签
- web/src/app/(shell)/p/findings/page.tsx — 发现页(含灰卡区)
- web/src/components/moment/*.tsx — 时刻卡族(发现/审批/播报行/系统)
- tests/web/*.test.ts — vitest;e2e/*.spec.ts — Playwright
- 登录: web/src/app/login — 移植 GL-DS 登录页+操作员密钥

## 任务(TDD 每步: 红测试→跑红→最小实现→跑绿→pathspec 提交)
T1 脚手架: Next.js+tailwind+shadcn 初始化;GL-DS 令牌移植(tailwind config 色阶/字号);登录页移植。验收: build 过+登录渲染+密钥错误提示+通过跳 /p/chat。
T2 账本桥: ledger.ts query 封装(timeline/findings/soldiers/approvals 四读);vitest 用 tests/fixtures/G-r18 夹具跑真命令断言 JSON 形状。
T3 壳: 侧栏三组 20 项+badge(审批红点=待办数,进行中仗数);顶栏三件;路由骨架其余 19 页占位(空态指路文案)。vitest: 分组/排序/激活态;badge 数字来自桥。
T4 指挥台骨架: 流组件(key 去重追加)+输入框+战况板三格;1s 尾轮询+断线黄条重连;上滑反向分页。vitest+夹具;E2E 冒烟: 登录→流渲染。
T5 说话即开仗: POST /api/chat-say → 意图解析(目标抽取;LLM 调用走引擎密钥)→对话式确认(授权+预算两问,其余缺省)→确认后 engine.ts 调 battle/new 链真建仗→「仗已开」时刻卡。dry-run 模式供测试(不点火只回放预演);vitest 全路径+夹具。
T6 两级播报: 一级=AI 摘要行(带 AI摘要 徽标);点开=原始事件行。摘要调用带缓存与失败降级(降级=直接显原始行)。vitest: 摘要渲染/降级/展开。
T7 内联审批: 待审批→气泡卡(事件/风险一句/批准/拒绝)→engine.ts 签名链;超时策略显示。vitest: 批准/拒绝/超时三路。
T8 发现时刻: 新发现→时刻卡(严重度/位置/已机器复放验真徽标/证据袋展开/加深+复测钮)。加深→engine 派深挖意图;复测→排复验。vitest 夹具。
T9 插话转向: 输入框常活;steer→四分类→确认行「收到,跳过X,主攻Y」。vitest。
T10 会话签: 意图列表+每会话轮次流(思考/工具调用原文)+会话级 steer/kill。vitest 夹具。
T11 灰卡: 发现页+任务漏洞签「待验区」;踢去复验动作。vitest。
T12 E2E 全链: Playwright 走 登录→说「打靶场」(dry-run)→确认→时刻流→发现卡→审批气泡→插话。全绿收官。

## 收官
68律三验: 全测绿(TRUE_RC=0)+活体截图+落舱记;对照表附 ARTEX 对应点(防遗漏)。


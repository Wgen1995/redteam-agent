# P0 指挥台+会话签+灰卡 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to execute this plan.设计纲=docs/design/2026-10-20-product-master-design-v3.md(终审通过);技术栈按十六节定案(1B/2A/3A/4C)。

## 铁律
- 引擎零改: 账本/复放/四权/CLI 不动一行;新件只读+写转发。
- 写路径一律 engine_bridge 子进程调 tanyin 命令链(单写者+锁+链);读面 FastAPI 进程内 import cli.ledger 读函数。
- 测试: Python=PYTHONPATH=cli python3 -m unittest …,管道出口码不可信,显式收 rc;前端=vitest;E2E=Playwright(channel="chrome",缺则 env-skip)。
- pathspec 提交;人话词表;零假数;68律三验收官。
- 端口: 新读面 8901(旧 8900 保留共存到 P1 切换);Vite dev 5173 代理 8901。

## 文件结构(新)
- server/readface/main.py — FastAPI 入口+静态托管(vite build 产物)
- server/readface/routers/{auth,chat,tasks,findings}.py — 登录/指挥流/任务/发现读面
- server/readface/ledger_reader.py — 进程内账本读投影(timeline/findings/soldiers/approvals/intents)
- server/readface/engine_bridge.py — 写转发子进程(chat-say 解析/审批签名/steer/kill/点火;dry_run 模式供测试)
- web/ — Vite+React+TS+tailwind+shadcn;src/lib/api.ts(FastAPI 客户端)
- web/src/app/shell.tsx — 20 页 IA 侧栏+顶栏(搜索/预算表/全停红钮)
- web/src/pages/{login,chat,mission,sessions,findings}.tsx
- web/src/components/moment/{broadcast,finding,approval,confirm,steer}.tsx — 时刻卡族
- tests/readface/*.py(unittest+TestClient);web/src/**/*.test.tsx(vitest);tests/e2e/p0.spec.ts(Playwright)

## 任务(每任务: 红测试→跑红→最小实现→跑绿→pathspec 提交)
T1 读面骨架: FastAPI /health + /api/auth/login(操作员密钥,错钥 401,成 Functionality cookie) — tests/readface/test_auth.py。
T2 账本读投影: ledger_reader 四读(timeline 尾部分页 key 游标/findings 含验真态/soldiers 心跳/approvals 待办),夹具 G-r18 — test_reader.py。
T3 Vite 脚手架: 初始化+GL-DS 令牌(tailwind 色阶/字号/暗色)+登录页对接 T1 — web/src/pages/login.test.tsx。
T4 壳: 20 页 IA 侧栏(作战7/机组4/系统9 分组+审批红点/进行中仗数 badge 数据来自 T2)+顶栏三件+其余页空态占位(指路文案) — shell.test.tsx。
T5 指挥流: 1s 尾轮询(key 去重追加)+断线黄条自动重连+上滑反向分页+多仗彩色徽标过滤 — chat.test.tsx(mock api)。
T6 说话即开仗: /api/chat/say→engine_bridge 意图解析(目标抽取,LLM 走引擎密钥)→对话式确认(授权+预算两问,余缺省)→确认点火(battle/new 链子进程)→「仗已开」时刻卡;dry_run 全路径可测 — test_bridge.py+chat-flow.test.tsx。
T7 两级播报: 一级 AI 摘要行(AI摘要 徽标,engine_bridge digest,失败降级显原始行)+点开二级原始事件 — broadcast.test.tsx。
T8 内联审批: 待办→审批气泡(事件/风险一句/批准/拒绝)→bridge 签名链;超时策略文案 — approval.test.tsx+test_bridge.py。
T9 发现时刻: 新发现→时刻卡(严重度/位置/已机器复放验真徽标/证据袋展开/加深+复测钮接 bridge) — finding.test.tsx。
T10 插话转向: 输入常活→bridge steer 四分类→确认行(「收到,跳过X,主攻Y」) — steer.test.tsx+test_bridge.py。
T11 会话签: 意图列表+每会话轮次流(思考/工具调用原文)+会话级 steer/kill/rerun — sessions.test.tsx。
T12 灰卡: 发现页+任务漏洞签「待验区」(复放未过)+踢去复验 — findings-grey.test.tsx。
T13 E2E 全链: Playwright 登录→say(dry_run)→确认→时刻流→发现卡→审批→插话,8901 — tests/e2e/p0.spec.ts。
T14 收官: FastAPI 托管 vite build;启动脚本+runbook(docs/runbook/readface.md);68律三验+落舱记+对照表(ARTEX 对应点)。

## 验收
全测绿(Python TRUE_RC=0/vitest 全绿/E2E 绿或 env-skip 有据);8901 活体: 登录→指挥台流(夹具数据)→dry-run 开仗全链走通;pathspec 提交链完整。


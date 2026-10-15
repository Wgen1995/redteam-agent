# ARTEX 使用手册（实时滚动版 · 2026-10-15 起）

> 状态: 骨架v1（源码级报告 docs/research/liveui/2-artex.md 已并入；漫游舰+手册舰将逐章充实）。
> 性质: 参照系统研究文档。凭据: http://localhost:8787 用户 ARTEX（本地部署）。

## 0. 一句话与架构总览
- 定位: 自主渗透测试控制台——AI 主 Agent 规划+worker 并发执行，人做「开局/导航/刹车/治理/收尾」五件事。
- 技术栈（源码实证 web v2.2.0）: Go 单二进制（前端 Next.js16+React19 静态导出 go:embed）+ **PostgreSQL 全量**（注意： 早期资料说 SQLite 已过时）+ MITM 代理口 :8788。
- 认证: POST /api/auth/login → JWT Bearer；SSE 走 ?token=。
- 实时模型: 无全局 store，三档轮询(2/5/10/15s)+单 SSE 多会话分发（seq 去重/snapshot 衔接/MAX_KEEP 4000）。

## 1. 界面地图（21 项 IA，两组侧栏）【漫游舰回港后逐项填： 每页截图引用+按钮+参数】
TODO-每视图: 路由|呈现|每个按钮/参数作用|交互流程。
重点视图: 会话(主Agent对话+@引用漏洞资产)/审批卡(内联amber+深链?approval=N)/workers 实时流/任务中心/发现管理/LLM池。

## 2. 能力清单（27 项评分见 liveui/2-artex.md §②）
## 3. 完整渗透流程（live 实证 80 分钟战例）【待充实】
开局一句话→规划→并发执行→审批刹车→发现管理→复测→报告。
## 4. 机制原理【待手册舰展开: 五路深读 docs/research/artex-deep-dive/ 并入】
judge 判据(默认关 fail_action=allow)/MITM 流量(默认 fail-open)/PG 图资产模型/意图-事实双表。
## 5. 逻辑架构图解【待画: ASCII 或 mermaid 风文本图】

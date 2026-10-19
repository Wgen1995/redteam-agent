# 系统机制全点对照设计(ARTEX怎么做/CSAI怎么做/我们怎么做/状态)

> 掣令: 全系统每一点怎么做的,对照ARTEX/CSAI。状态: 已建(引擎,测试在册)/补(小改)/待建(分期)/不采(定位)。

| # | 机制 | ARTEX(源码实锤) | 我们 | 状态 |
|---|---|---|---|---|
| 1 | 任务生命周期 | 表单建→engine.Run→暂停/归档/恢复/删除 | battle/new 授权链+warrior loop+暂停恢复 | 已建;模板/归档恢复=补 |
| 2 | 规划循环 | planner 读路线/资产/目标→发意图,回合+心跳 | 规划者(目标→意图拆解)+哨兵同舰收舱 | 已建 |
| 3 | 执行循环 | 每意图一 worker,PreToolUse 钩子 | 意图→兵种subagent,spawn前置四权执法 | 已建 |
| 4 | 上下文压缩 | Compactor+各角色窗口 | compaction.py 三角色窗口 | 已建 |
| 5 | 转向 | steerBox 意图键控,下工具前吃 | steer通道+四分类 | 已建 |
| 6 | 审批执法 | 规则deny/allow/ask阻塞+LLM法官+平台管控话术+失败归因 | 拦截规则+ask阻塞+签名审批 | 已建;**平台管控话术+失败归因=引擎小补P1** |
| 7 | 发现管线 | 单事务六写+推送原子 | 哨兵过滤+验证官机器复放+落链账 | 已建(强于ARTEX:非LLM验真门) |
| 8 | 证据/流量 | mitm全量录+四角色绑定+GC | egress JSONL→Go边车(P1) | **待建(P0钩子/P1全文)** |
| 9 | LLM池 | 熔断/重试/轮询/限速/优先级 | 多道配置+budget记账 | 已建;熔断可视化/重试编辑=补 |
| 10 | 通知 | 钉钉/飞书/邮件+投递记录+原子事件 | notify_user 单源 | 已建;渠道CRUD/投递=补 |
| 11 | 知识 | skills文件管理+未命中统计 | 知识环91卡+kb_inject+蒸馏 | 已建(强:飞轮) |
| 12 | 考卷/棘轮 | 无 | GT考卷+基线只升不降 | 已建(独有) |
| 13 | 资产 | assets+companies+scope规则+frontier | assets.tsv+覆盖图 | 已建;客户实体/frontier=补 |
| 14 | 探索图 | nodes/edges/anchors 图库 | matrix+链路图边表 | 已建 |
| 15 | 会话/对话 | 侧厅conversations+任务主控台+旁路提问(快照+预算) | 指挥台单流+旁路提问 | 设计已定;**对话存储/播报=待建P0** |
| 16 | 并发 | task_concurrency上限排队 | 舰队并发帽 | 已建 |
| 17 | 超时判死 | deadline协调+terminalreason | 终因四类+超时判死 | 已建 |
| 18 | 报告 | findings md/CSV | 报告员+报告链 | 已建;模板升级=P2 |
| 19 | 复测 | retester agent+active retests | 复验队列+定时复验器 | 已建 |
| 20 | 自更新 | selfupdate+rollback | — | P3 |
| 21 | MCP | mcphttp+按Agent授权 | F24b设计位 | P4 |
| 22 | 审计 | audit+activity | 链式账本+activity(防篡改) | 已建(强于ARTEX) |
| 23 | 安全面 | 资产拦截(gov/edu内置)+工具拦截范围 | 范围红线+拦截规则 | 已建;内置合规黑名单=小补 |
| 24 | 观测 | CSAI:OTel | 心跳+activity | 已建够用;OTel=P4 |
| 25 | 兵种权限 | 无(单worker角色) | 四权分立spawn执法 | 已建(独有) |
| 26 | HITL策略门 | CSAI:JEV per-tool策略 | 拦截规则+审批同位 | 已建 |
| 27 | 攻击链建模 | CSAI:Builder+晋级项目 | 链路图签 | 已建简版;晋级=评估 |
| 28 | 收仗 | wrapup+agentfinalizer挡未决 | wrapup+终因 | 已建;挡未决播报=小补 |

**结论**: 28 机制中 19 已建(7 处强于 ARTEX)、6 小补、3 待建分期、不采=C2/WebShell。
P0 不是「只做界面」——是产品面第一块;引擎这件已建成的大件零改复用。

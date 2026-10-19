# 亲读档案·ARTEX/CSAI全源码+环境实测（总控亲笔,持续追加）

> 用户令: 亲自读取全部源码和环境查看全部功能,了解清楚后结合现状从零构建。
> 方法: 逐文件读,读到即落此档;四相=①ARTEX前端②ARTEX后端③CSAI④环境实测(Playwright走DOM)。
> 已亲读(先前): README/侧栏导航/chat page 1569行/engine.go头部/guard.go 85-150/finding_traffic.go 342-400/sidequestion结构/CSAI README_CN头60行。

## 进度
- [ ] ①ARTEX前端27页
- [ ] ②ARTEX后端
- [ ] ③CSAI
- [ ] ④环境实测

## ①ARTEX前端亲读蒸馏(批次1: 任务页/仪表盘/发现页/会话签/概况签)
- **任务页(3417行)**: 当前+归档两签;搜索/状态/分类筛选+分页;批量(暂停/恢复/归档/删除带选项/移动分类);单任务改名/置顶/归档/删除;并发上限对话框(enabled+limit,超限按创建序排队)。**新建任务=右侧抽屉表单**: 模板套用/名称/分类(可搜+即时创建)/描述(附件上传进staging,agent按路径读)/目标(必填)/LLM档位多选/关联来源任务(继承上下文,上限)/公司/超时分钟/规划心跳分钟/种子首意图开关/覆盖开关/拦截规则列表。**开仗=填表不是对话**。
- **仪表盘(1211行)**: 15数据源融合(任务/发现/统计/设置/待审批/活动流/token总量/会话token/用量/资产计数/流量/agents/MCP/skills/tools/llm档)。
- **发现页(1263行)**: 三视图(平铺分页/资产树/分组聚合);六筛选(严重度/状态/漏洞类/任务/排序/搜索);统计条;行内展开;**两个关键动作: 加深单个发现(spawn深挖)/主动复测(活跃复测跟踪)**。
- **会话签(2205行)**: 任务级单SSE+反向分页历史,snapshot_cursor无缝对接+seq去重合并;意图=会话;**MAIN会话=任务主Agent控制台(可对话/发送/停止带取消原因)**;新建MAIN;worker资产徽标;token/时长每会话。
- **概况签(1322行)**: 按模型token统计+缓存命中率;**任务scope可编辑(增删)**;**任务goals可编辑(增改删,带漏洞类)**;**constraints可编辑(增改删,带种类)**。

## ①批次2蒸馏(资产/拦截/九系统页)
- **资产页(1216行)**: company/domain等分签+DSL检索+分页+资产卡(方法徽标/状态色/chips);删资产/删公司(可连带资产)。
- **拦截规则页(985行)**: judge卡(30天用量迷你图+配置+提示词可改+llm档绑定);规则CRUD(regex校验);SDK工具+DB工具分组启停;动作徽标(deny/allow/ask)。
- **skills(1127行)**: 技能文件管理器全件(建/传/读/写/删/目录/可见性开关/用量统计/缺失检查/agent绑定/MCP绑定)。
- **llm(990行)**: 档位CRUD+连接测试+拉模型列表+池视图+重置+OpenAI兼容端点展示。
- **traffic(830)**: 录制查看器+按host删/全删。**commands(392)**: 工具执行历史流水。
- **workspace(364)**: 文件浏览+下载。**sync(486)**: 第三方数据源(ss-*)项目同步任务。
- **llm-records(580)**: prompt/response审计查看。**notify(605)**: 通知渠道CRUD+测试发送。
- **mcp(482)**: 服务器CRUD+工具列表+可见性。**settings(713)**: 系统设置。

## ②ARTEX后端亲读蒸馏
- **agent/目录(10391行)=心脏**: Planner(规划者,含TodoStore任务清单/触发器渲染/kill/steer/约束注入)+Worker(执行者,默认工具集/代理环境变量让所有子进程走mitm)+MainAgent(任务主控台对话,Chat()即任务内聊天)+Compactor(压缩,三角色各配窗口解析)+retester(独立复测会话)+side_questions(旁路提问)+finding_workflow(发现-流量绑定工具)+wrapup(收尾)+blackboard_inheritance(黑板继承)+coldgraph(冷图)。
- **三角色同构**: 每角色都可配 compaction窗口/NOA模式/流式开关/最大token/代理CA/网页搜索/约束注入——平台级能力矩阵。
- **引擎(先前亲读)**: 每任务planner+worker双循环+steerBox意图级排队;guard=规则+LLM法官+ask阻塞+平台管控话术+失败归因;发现=单事务六写+推送原子。

## ④环境实测蒸馏(Playwright走真demo,DOM级)
- 全局: 命令面板⌘J(全站搜命令);侧栏21项;审批待办红点徽标。
- 任务表列: ID/名称/描述/目标/状态/**目标进度**/漏洞(严高中低)/运行中Worker/创建/时长/Token/操作。
- 仪表盘: 活跃x/y(并发帽可视化)+探索/暂停/完成+确认发现(分档)+资产节点(跨任务共享)+流量交互(录制中)+Token(入含缓存/出)+新旧版切换。
- 对话页: 会话按Agent分组(主Agent/越权/横向讨论),Agent选择器+模型档。
- 发现页: 跨任务汇总/三视图/统计/筛选/导出;行=严重度+名称+资产+状态+任务+时间+操作。

## 总结论(四相后)
ARTEX=「表单开仗+任务工作台+侧厅对话+全链观察」四件套成熟品。我方差异令不变(复放验真/考卷/飞轮/链账/四权),产品面按其成熟度对齐,交互取opencode式对话指挥(用户令),其旁路提问/审批四触点/失败归因/平台管控话术全数吸收。

## 100%补全(ARTEX api.ts全动词+环境21页+全后端包 / CSAI全模块+路由+15剧本)
**ARTEX 新发现我方原缺**: ①Agent即产品件(提示词编辑/版本/变量/预览/触发器/MCP-Skill-工具绑定/可见性/自定义Agent) ②自定义工具三型(command/script/http)+测试 ③任务级拦截规则 ④发现-流量证据可编辑绑定(四角色/排序/正文预览下载/lineage) ⑤任务模板CRUD ⑥客户实体+公司范围规则 ⑦LLM熔断状态+重试退避编辑+限速/优先级/思考档 ⑧自更新+回滚 ⑨通知三渠道(钉钉/飞书/邮件)+投递记录重试 ⑩意图rerun/blocked重跑 ⑪日志暂停清空 ⑫流量捕获开关+向Agent注入traffic_search/traffic_get工具 ⑬内置gov/edu合规黑名单。
**CSAI**: 15阶段剧本兵(kill-chain)/HITL JEV策略门/攻击链Builder+晋级项目/RBAC全件/自更新套件(adopt/rollback/restart/job)/OTel观测/agentfinalizer(收仗挡未决工具执行)/C2+listeners+reverse_shell。
**不采(定位裁决)**: C2/WebShell/reverse_shell(高危面与渗透Agent平台定位不符);oneliner;RBAC=P4已列;工作流编排=P4评估。

## 任务详情页函数级深读(补课,用户点名)
10签+任务头。任务头: LLM档位即时编辑/暂停恢复/归档(确认框)/状态徽标(engine模式+终态)。会话签: MAIN控制台(对话/停止带原因/新建MAIN切换)+意图会话列表(分页)+worker消息/LLM resolution/rerun/steer/kill+资产徽标。概况签: goals/constraints/scope/资产引用 CRUD+按模型token+缓存命中率。链路图签(coverage-graph): G6力导向+**级联折叠**(全图→可见集)+kind分组图标(lucide SVG)+tested/in_scope双色节点+标签截断+hover详情。广播签: live开关+kind过滤chips+行展开+关联节点HoverCard(带资产列表/状态徽标)。发现签/复测签/资产签/拦截签(任务级规则)/报告签。资产签: 任务资产表+范围引用+编辑追加。
**诚实读深表(全24页)**: 深读(函数级)=chat/tasks列表+建仗/sessions/overview/graph/broadcast/assets结构+detail头/findings列表/拦截/技能/流量表面/仪表盘表面;结构读(函数签名)=llm-records/sync/workspace/notify/mcp/settings/commands/审批/日志;后端=深读(engine/guard/发现链/sidequestion/planner-worker签名面/api动词全量)。
**读深缺口(待补函数级)**: findings/_components(表格/资产树内部)/dashboard内部组件/llm-records查看器/traffic查看器/retests任务签件/report签件/intercept任务签件——列为补课清单,我亲读逐件落档。

## 补课战役·零遗漏清单(机械对账,逐件打勾)
目标: ARTEX前端~59业务源文件+共享件抽查 / ARTEX后端~150 go(按包深读函数级) / CSAI ~200 go+md / 环境8787交互走查。
进度: [####______] P1前端深读 4/59(findings-table✅asset-tree✅链路图✅广播✅)

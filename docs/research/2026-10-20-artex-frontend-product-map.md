# ARTEX 前端全量功能图(源码实读·逐页四件套) · 2026-10-20

- 任务令: 深入 ARTEX 全部前端源码产出功能图,不许猜、不许只看截图。
- 源码位置: `/tmp/artex-look/ARTEX-main/web/`(Next.js App Router + TS,客户端组件为主,静态导出部署)。
- 方法: 逐文件实读 `web/src` 全树——27 个 page.tsx(24 主页面+3 辅助)、`app/(main)/_components/sidebar` 11 件、`_tabs` 10 签、`components` 26 业务组件+61 ui 件、`lib`(api.ts 1316 行/types.ts 1612 行/全部 helper)、`hooks` 4 件、`stores`/`config`/`navigation`/`proxy.ts`。零改源码、零 npm、零运行。
- 引用约定: 下文所有 `file:line` 相对 `web/src/`;行号为本次实读快照。

## 与旧账的关系(军规对账)

| 旧账 | 覆盖面 | 本文增量 |
|---|---|---|
| docs/research/2026-10-20-artex-full-capability-inventory.md | 后端能力面(路由表/server 130 件/agent 内部件),零页面粒度 | **每页四件套**(目的/组件+布局/数据依赖/操作全集)——旧账没有的粒度 |
| docs/design/2026-10-20-capability-comparison-ledger.md | 27 件功能对照,ARTEX 侧只到页名级一句话(如 §F27 提及任务二级导航) | 逐页数据依赖(API/字段/轮询/SSE 精确到秒与端点)、交互协议五件深录、组件清单、前端视角 API 消费矩阵 |
| docs/research/2026-10-11-artex-analysis.md、artex-deep-dive/ | UI 实录与引擎深读 | 本文全部回到源码行号重新钉死,含旧账未写的: 任务详情实为 **10 签非 8 签**、对话页**无 SSE 是 1s 轮询**、资产视图**不轮询**等事实修正 |

---

## 〇、报账底数

- **页数**: 27 个 page.tsx = **24 个主页面**((main) 组内:功能 12 页+系统 12 页,恰合"24页"口径)+ 3 辅助(login/setup/(external) 根跳转)+ not-found。任务详情页内再分 **10 签**(sessions/overview/graph/broadcast/findings/retests/assets/coverage/intercept/report,detail/page.tsx:53-64)。
- **组件数**: 业务组件 **26**(components/*.tsx,含 calendar 目录未挂路由的 1 组)+ 任务签组件 10 + 侧栏组件 11 + shadcn ui 库 **61**(components/ui/)。
- **API 数(前端视角)**: `lib/api.ts` 单一 client 暴露 **258 个方法键**,覆盖 **83 个静态路径前缀**的 REST 端点 + **4 条 SSE 流**(exploration/activity/stream、logs/stream、update/stream、side-questions/:id/events)+ 文件上传(chat/upload、skills/upload、workspace/upload)。UI 实际调用 **200+** 个方法(逐文件 `api.*` 提取比对)。
- **最关键的五个产品机制**(详见 §六深录): ①任务会话消息流协议(SSE+反向分页无缝对接) ②任务详情十签工作台 ③资产覆盖力导向图(折叠+证据面板) ④发现详情证据展示(四角色+版本并发) ⑤审批环(规则→模型兜底→人工→深链回放)。

---

## 一、前端骨架(先读地基)

1. **静态导出+客户端守卫**: 全部页面 "use client";(main)/layout.tsx:35-46 用 auth.getToken() 做 CSR 守卫,未登录清 cookie 跳 /login(防 cookie/localStorage 不一致的无限弹跳,注释 40-44);proxy.ts:6-25 是静态导出前的服务端兜底(cookie 有无双向重定向),MOCK=1 时全放行(proxy.ts:8)。根路由 `/` 直接 redirect 到 /function/tasks((external)/page.tsx:1-5);404 也回任务页(app/not-found.tsx:12)。
2. **认证**: token 存 localStorage `artex_token`(api.ts:109-112)+ cookie 双写;http() 统一注入 Bearer(api.ts:117-124),401 → 清 token 踢登录(api.ts:125-131);错误体取 {error} 字段(api.ts:133-145)。登录页 313 行: authStatus 判 initialized、登录、滚动到底才可同意的免责条款对话框(login/page.tsx:288-308)。setup 页 128 行: 查不到初始化状态时**关闭入口**防覆盖已有密码(setup/page.tsx:20-35)。
3. **API 层**: 单文件 lib/api.ts(1316 行),http/get/post/del 泛型封装 + arr() 归一化数组;sseUrl()(api.ts:189-198): 生产同源相对路径(反代友好),dev 直连 :8787(绕过 Next rewrite 对 SSE 的缓冲),token 以 ?token= 附带(SSE 不能跨源带 cookie)。MOCK 开关(api.ts:115)走 lib/mock/handler(2493 行全接口 mock)。
4. **SSE×轮询哲学**(逐页 setInterval/EventSource 实测): 高频作战面轮询——对话消息 1s(chat/page.tsx:600)、会话签杂项 1.5-5s(sessions-tab.tsx:797,820,839,858,868)、发现签 3s(findings-tab.tsx:162)、流量 3s(traffic/page.tsx:230)、审批 5s(approval-records.tsx:718)、任务详情 5s(detail/page.tsx:236,274)、仪表盘 5/5/15s(dashboard/page.tsx:175,214,250)、播报 8s(broadcast-tab.tsx:38)、资产签 10s(assets-tab.tsx:418)、任务列表 10s(tasks/page.tsx:164,486)、探索链路 20s 且**数据签名相同跳过重建**(graph-tab.tsx:27-32)。长流面 SSE——任务活动流/日志流/更新进度流/旁路问答流(§六)。**对话页不用 SSE**(纯 1s 尾轮询,chat/page.tsx:580-608)。
5. **偏好系统**: root layout 注入 data-theme-mode/preset/content-layout/navbar/sidebar/font 七个偏好(app/layout.tsx:24-32)+ ThemeBootScript 防闪烁;zustand store(stores/preferences/preferences-provider.tsx)+ 每键可配持久化策略(preferences-config.ts:68-76 默认 floating/icon/light)。侧栏宽 68 单位((main)/layout.tsx:67)。

---

## 二、24 页逐页四件套

> 格式: ①目的 ②组件+布局 ③数据依赖 ④操作全集。

### A. 功能组(12 页)

**1. /dashboard 仪表盘**(dashboard/page.tsx,1211 行)
① 全局作战态势一屏:任务/发现/资产/token/审批五族指标+实时动态。②Card 网格(统计卡+图表区)+recharts BarChart 日 token 趋势(46-50)+资产类型着色条(81-88)+最近活动/最近发现/待审批三列表(1186-1206)。③api.stats/tasks/findings/activity/traffic/assetCounts/usageStats/tokenStats/conversationTokens/agents/skills/tools/mcpServers/llmProfiles/settings/interceptPending;轮询 5s/5s/15s(175,214,250);无 SSE。④token 按 LLM 配置分页签切换(630-675,输入拆"未命中/缓存命中/输出"三段,694-731);每卡跳转对应列表页;待审批>3 折叠"还有 N 条"→审批页(1189-1196);纯读无写操作。

**2. /chat 对话**(chat/page.tsx,1569 行)
① 与任意 Agent 的自由对话控制台(非任务绑定)。②三栏: 左会话轨(按 Agent 分组折叠+置顶,COLLAPSED_AGENTS_KEY 持久化 97)+中 Transcript+底 Composer;DraftChat 懒建会话(首条消息才 createConversation,363-475)。③api.conversations(2s 轮询 1112-1115)/conversationHistory(反向分页,页 200,91)/conversationMessages(运行中 1s 尾轮询 580-608)/sendConversationMessage/stopConversation/rename/pin/delete(含批量)/updateConversationProfile/chatUpload(附件落 sessions/conv-<id>/uploads/,710-723);旁路提问走 sideAPI(§六.1);审批深链 ?approval=(497)。④@提及九类对象(mention-textarea+chat-mentions.ts:1-11)、/btw 旁路提问(252-256)、Enter 发送(键位可设)、运行中变停止按钮(257-262)、换 LLM 配置(281-361)、TodoPopover 查看最近 TodoWrite(529-535,833)、内联重命名/置顶/多选批量删除、token 实时账(result 累加+在途 usage,683-708)。

**3. /function/tasks 任务列表**(tasks/page.tsx,3417 行)
① 任务全生命周期作战台: 列表/归档两签+分类。②Tabs(任务/归档)+Table(选择/ID/名称/描述/目标/状态/目标进度/漏洞严高中低/运行 Worker/创建/时长/Token/操作列)+侧滑 CreateTaskSheet+分类管理 Sheet(dnd-kit 拖任务入分类,2877-2892)+ConcurrencySettingsDialog。③api.tasks(10s 轮询)+taskArchive(归档签 2s,1695)+全套 CRUD(§五);秒级时钟 1s(524)。④行操作: 暂停/恢复(controlTask)/改名/置顶/归档/删除(5 选项: 资产/流量/文件/发现/LLM 记录,types.ts:63-69);批量: 批量控制(controlTasksBatch)/分类移动(updateTasksCategory)/归档/删除;归档签: 还原/永久删除/失败重试(1778-1787);创建表单: 描述/目标/分类/关联企业(Combobox 多选)/任务级资产拦截规则(AssetInterceptRulesEditor)/模板套用另存(TaskTemplateControls)/LLM 故障转移链(TaskLLMProfileChain)/附件上传/资产覆盖度开关(3391-3398)/继承关联任务。

**4. /function/tasks/detail 任务详情**(detail/page.tsx,462 行)
① 单场仗的十签工作台壳。②顶栏(返回/状态徽/目标进度/LLM 链 Popover 73-186/暂停恢复归档)+Tabs 十签(53-64)。③api.task/stats 5s(236,274)+controlTask/archiveTask/updateTaskLLMProfiles;十签各自数据面见 5-14。④LLM 链任何状态可改(终态任务对话仍走链,84-86);暂停/恢复/归档带确认;十签跳转。

**5. …/detail 会话签**(sessions-tab.tsx,2205 行)——消息流协议核心,§六.1。
**6. …/detail 总览签**(overview-tab.tsx,1322 行)
① 任务健康度+四管理卡。②StatCard 行+意图瀑布(blocked/exhausted 可重跑 rerunIntent/rerunBlocked,119-120)+目标/约束/测试范围/任务级拦截四张 CRUD 卡。③api.task/stats/intents/findings/taskGoals/taskConstraints/taskScope/taskInterceptRules/tokensByModel,轮询(403);写=goals/constraints/scope/拦截规则全套增改删+toggle。④目标增改删"会通知规划者并复活任务"(458-461);范围行来源 auto/agent/manual(76-80);缓存命中率(51-55)。

**7. …/detail 探索链路签**(graph-tab.tsx,55 行+exploration-graph.tsx,663 行)
① 任务探索图拓扑(goal/intent/fact/finding/hint/digest 节点+四类可视边)。②@xyflow/react ReactFlow 分层布局(COL_W=360,180)+MiniMap/Controls+节点 Sheet 详情;**digest 折叠算法**: 活跃 digest 吞并成员节点、边重接线、逆向 derived_from 去重(141-178)。③api.explorationGraph 20s 轮询+签名跳过(27-32)。④拖拽/缩放/点节点开详情;边配色语义(relColor 54-59);payload 按类型抽摘要字段(89-117)。

**8. …/detail 播报板签**(broadcast-tab.tsx,734 行)
① 探索节点按创建序的战报时间轴(与图互补的流水视角,42-43)。②时间轴行+KIND_META 八类徽(44-93)+HoverCard 展开边语义+相对时间。③api.explorationNodes 服务端分页(20/50/100,37)+POLL_MS 8s(38)+相对时钟 30s(462);一页带 refs+assets 免全图(types.ts:427-438)。④类型筛选(96)/状态筛选/关键词/正倒序/翻页/暂停滚动重放(Pause/Play)。

**9. …/detail 发现签**(findings-tab.tsx,223 行)
① 本任务及直接关联任务的确认发现清单。②Card+行内状态 Select+排序持久化(sort-preference)。③api.findings(task 过滤)3s(162)+setFindingStatus。④改处置状态/排序/跳发现详情。

**10. …/detail 复测签**(retests-tab.tsx,168 行)
① 漏洞复测总表。②FindingsTable 复用+FindingRetestDialog。③api.findingsPage(复测态过滤)+startFindingRetest(dialog:42)+activeFindingRetests。④发起复测(附备注)/查看复测历史。

**11. …/detail 测试资产签**(assets-tab.tsx,707 行)
① 任务资产面: 覆盖记账的分子。②统计条+DSL 搜索框(asset-dsl-search 共享,11-12)+类型分组表+移出确认(683-704)。③api.taskAssets/searchTaskAssets(后端 DSL: domain/ip/url/root_domain/page_title/icp/service_name/app_name 等,asset-dsl-search.tsx:14-80+)/assetCounts 10s(418)+registerTaskAssetScopes/detachTaskAsset。④DSL 搜索/登记为任务范围/移出(全局资产与流量保留,684-687)。

**12. …/detail 资产覆盖图签**(coverage-graph-tab.tsx,721 行)——力导向交互,§六.3。
**13. …/detail 拦截审批签**(intercept-tab.tsx,7 行): ApprovalRecords 按 taskId 过滤(§六.5)。
**14. …/detail 报告签**(report-tab.tsx,90 行): api.report(taskId) 拉 Markdown 报告→渲染+一键复制(38-48);无编辑(报告由独立报告 Agent 维护)。

**15. /function/findings 发现列表**(findings/page.tsx,1263 行)
① 跨任务漏洞总账。②视图三态: flat 平铺大表(默认)/grouped 按任务折叠(组内独立分页,96-104)/asset 资产树+子树发现(**不轮询的一次性快照**,76-77);统计条+筛选(严重度/状态/任务/类型 ToggleGroup)+行展开。③api.findingGroups/findingsPage/findingAssetTree/findingStats/deleteFinding/updateFinding/exportFindings/deepenFinding/setFindingStatus/activeFindingRetests;flat/grouped 5s(550,583);行展开按 finding_id 懒拉完整报告(641-660)。④筛选持久化(68)/行展开编辑(名称/漏洞类/严重度)/状态改/删除确认/导出 CSV/**深挖**(deepenFinding 带描述续挖,684-685)/发起复测/跳任务与详情。

**16. /function/findings/detail 发现详情**(detail/page.tsx,344 行)——证据展示,§六.4。
**17. /function/traffic 流量**(traffic/page.tsx,830 行)
① 全量 HTTP 流量库(主机↔交换)。②主从表: 主机行→交换列表→Sheet 详情(req/resp HttpCodeBlock 着色);老流量自动补 Host 头(81-96)。③api.traffic(3s,230)/trafficDeleteHost/trafficDeleteHosts/trafficDeleteAll;LinkTrafficDialog 把流量绑给发现。④方法/状态码/关键词/排序(持久化)筛选;删主机/批量删/清空(回收空间 GB 级,59-67);绑定发现证据。

**18. /function/commands 工具执行**(commands/page.tsx,392 行)
① agent 执行过的命令审计表。②Table+详情 Sheet(input/output 双栏,错误标红,368-384)。③api.commands/commandStats。④按任务/agent/状态筛选+查看详情;只读。

**19. /function/llm-records LLM 录制**(llm-records/page.tsx,580 行)
① 每次 LLM 调用的请求/响应录制与回放。②录制开关行(settings.llm_record)+任务列表+记录表+详情(格式化 JSON+逐框复制,79-118)。③api.llmRecords/llmRecordDetail/llmTasks/llmRecordsDeleteTask/setSettings。④开关录制/会话+模型筛选/分页/删整任务记录/查看明细复制。

**20. /function/assets 资产**(assets/page.tsx,1216 行)
① 全局资产库(企业+根域名/IP/子域/应用/服务/接口 7 签,100-108)。②Tabs+Table+企业 Sheet(ScopeTextEditor 范围文本编辑,company-scope.ts 解析归一)+DSL 搜索。③api.assets/searchAssets/assetCounts/companies/createCompany/deleteCompany/addCompanyScope/updateCompanyScope/deleteAssets(批量);无轮询。④企业 CRUD+范围五类行编辑(domain/ip/cidr/icp/keyword,types.ts:367)/DSL 搜索/多选批量删除/分页;范围"自动认领命中资产"(409)。

**21. /function/sync 资产同步**(sync/page.tsx,486 行)
① ScopeSentry 外部资产源对接。②数据源配置卡+项目列表+项目内任务同步。③api.ssDatasource/ssProjects/ssTasks/ssSync。④配置数据源/选项目/按任务维度触发同步/查看结果。

**22. /function/workspace 工作空间**(workspace/page.tsx,364 行)
① 任务工作区文件浏览器(agent 的文件面)。②树+面包屑+上传/下载/新建文件夹(340-361)。③api.workspaceList/workspaceUpload/workspaceDownload/workspaceMkdir/workspaceDelete/workspaceRead/workspaceWrite。④浏览/上传/下载/建目录/删文件+文本在线编辑保存。

**23. /system/llm LLM 配置**(system/llm/page.tsx,990 行)
① 模型配置池+熔断池运维。②配置卡列表(健康徽: 未配 Key/熔断·冷却/异常·失败 N 次/正常,healthOf 76-99)+编辑 Sheet(格式 openai/anthropic/openai-responses;thinking.type 与 reasoning_effort 解耦两字段 35-41;max_tokens 字段名可选 47-58)+重试策略面板(_components/retry.tsx,全局默认+per-profile 覆盖)。③api.llmProfiles/llmPool(10s,122)/fetchLLMModels/testLLM/saveLLMProfile/activateLLMProfile/deleteLLMProfile/resetLLMPool/setSettings。④建/改/删/设默认/拉模型列表/连通测试/重置熔断池/重试策略编辑。

**24. /system/agents + /system/agents/detail**(283+47 行)
① agent 名册与六维配置器。②列表(builtin/自定义徽)+创建自定义+抽屉 AgentEditor;detail 页为 ?key= 深链同组件(detail/page.tsx:18-35)。③api.agents/createAgent/deleteAgent + AgentEditor 全家(agent-editor.tsx,1159 行): 提示词版本历史+diff+变量表+预览(previewAgentPrompt)/收尾提示词与超时收尾(save/reset×2)/MCP 绑定/Skill 可见性/Tools 绑定+流量工具门(33)/maxTurns(53)/per-agent LLM 绑定(优先级注释 298-305)/定时触发器(interval_sec+触发消息,758-820,1016-1020)。④全部可编辑+恢复代码默认(resetAgentPrompt 等)。

### B. 系统组(12 页)

**25. /system/mcp**(482 行): MCP 服务器接入。三传输 stdio/http/sse(26-44)+env 文本解析(83-100);api.mcpServers/refreshMcpServer(重拉工具)/mcpTools/deleteMcpServer/visibility;按 agent 授权可见。
**26. /system/skills**(1127 行): 技能库 IDE。左树(后端目录串建树 67-112)+右文件编辑器(Textarea 保存 writeSkillFile,962-982)+总览统计(总数/累计调用/未使用/**未命中调用**——对不存在 skill 的调用也记账,147-190);操作=上传 zip/新建(基本信息+关联 MCP+可见性三签 Sheet 1016-1124)/改 meta/在线改文件/删 skill/目录/文件(三级确认 986-1013);使用量排行+最近调用(skillUsage)。Skill 绑 MCP"加载时才披露工具"(1076)。
**27. /system/tools**(843 行): 工具(卡)库。内置工具=描述/参数默认值/绑定 agent/启用可改(ToolEditor 143-197)+恢复代码默认(188-197);自定义工具四型 shell/command/script/http(698-759),http 支持占位符/headers/代理/走记录代理/deferred;**测试运行用未保存的当前表单**(652-672);traffic_search/traffic_get 被全局流量开关门(40-42,157-158)。
**28. /system/notify**(605 行): 通知推送。渠道 CRUD+实时/汇总双模式(482-493)+过滤规则(min_severity/include/exclude/task_ids/asset_ids/on_status_change,511-581)+限流条/分钟(496-509)+发测试消息(199-211);凭据**掩码往返协议**: __masked__ 前缀原样回传=不改,空串=清除——保证"能清除设错的密钥"(110-152);投递记录签可重投(DeliveryList→notifyRetryDelivery)。
**29. /system/intercept**(985 行): 拦截规则+模型兜底。规则 CRUD: 优先级(首条命中即停)/匹配目标 tool_name|tool_input/字符串|正则(RE2 扩展语法前端只警告后端验,827-829)/动作 allow|deny|ask/ask 超时自动 deny|allow(147-173,791-902);**拦截范围**对话框逐工具开关(SDK 八执行类+三写入类前端硬编码,111-128);模型兜底 judge 卡: 启用/profile(0=跟随激活)/提示词可编辑可恢复内置(263-276)/fail_action/ask 超时+独立 token 用量统计与迷你柱图(82-99,194-329)。
**30. /system/intercept/assets**(352 行): 资产拦截规则(block|allow × root_domain/subdomain/ip/service/app/endpoint),CRUD+启停;任务创建可预置(AssetInterceptRulesEditor 复用)。
**31. /system/intercept/approvals**(9 行壳): ApprovalRecords 全量版,§六.5。
**32. /system/logs**(232 行): 系统日志 tail。SSE /api/logs/stream?since=0(67)环形重放(含重启前最后 100 行 DB 恢复,注释 60-61)+/api/logs/history?before=db_id 翻更早(85-117,内存帽 3000/5000);暂停接流(69)/级别+关键词过滤(119-126)/粘底滚动(128-130)。
**33. /system/settings**(713 行): 全局开关集市。流量捕获(114)/agent_traffic_binding(132)/网络搜索+backend(brave/tavily key,188-214)/搜索代理+全局代理(214-226)/python 解释器(85)/Work Agent 并发数(73,对之后启动的任务生效)/约束注入 planner/worker(123-147)/noa 上下文压缩实验(155)/**发送键位**(纯 localStorage,680-709);UpdateCard: checkUpdate(后端 30min 缓存,force 手动)/applyUpdate+SSE 进度/rollback(103-168;phase 机 types.ts:1595-1603)。

### C. 辅助页
- **/login**(313 行): 密码登录+首次判初始化+免责条款滚底确认(288-308)。
- **/setup**(128 行): 首次设密码(≥8 位);后端不可达宁可关闭入口也不冒充未初始化(20-35)。
- **/**((external)/page.tsx:1-5): redirect → /function/tasks。

---

## 三、导航与侧栏

- sidebar-items.ts:64-97 两组: **功能**(仪表盘/对话/任务/发现/流量/工具执行/LLM 录制/资产/资产同步/工作空间 10 项)+**系统**(LLM/Agent/MCP/Skill/工具/通知推送/拦截规则/资产拦截/审批记录/日志/系统配置 11 项)。
- app-sidebar.tsx:39-63: logo→任务页链接头+NavMain+NavUser(脚);NavDocuments/NavSecondary 注释保留(56-57);variant/collapsible 从偏好 store 读(28-37)。
- nav-main.tsx: 折叠桌面态转 Dropdown、展开态 Collapsible 子项(150-162);**InterceptPendingBadge**: 全侧栏级 5s 轮询 interceptPending 红点计数(164-177)。
- search-dialog.tsx: Ctrl/Cmd+J 命令面板(85-94),索引=侧栏项扁平化(39-64),禁用项过滤(66-68)。
- main-content.tsx: 顶栏 SidebarTrigger+AccountSwitcher+LayoutControls(布局/主题)+UpdateBadge(新版本→设置页);nav-user: 用户菜单+改密码对话框。

---

## 四、组件清单(业务 26 逐个)

| 组件 | 职责 | 关键行为/协议 |
|---|---|---|
| transcript.tsx(775) | 消息流转录渲染器(对话页+会话签共用) | 步骤分组: user/answer/round/tool(use↔result 按 tool_use_id 配对)/msg/intercept 六型(79-98);usage 不渲染只记账(91);worker 色轨 planner 琥珀/mainagent 主色/work#N 循环取色(28-41);**useInView 懒取详情**(进视口前 400px 才拉 body,52-74);intercept_request 内联审批卡;在途"实时流式中"动画(763-771) |
| approval-execution-focus.tsx(138) | 审批深链回放 | ?approval= 解析+interceptExecution 定位;回放=连续翻历史页直到 seq 出现,绝不孤立插入(59-99) |
| approval-records.tsx(910) | 审批记录台(全局/任务/签内三形态) | 筛选 status/decision_source(50-54);pending 5s(718);decide allow/deny;来源链接→chat/tasks 带执行定位(62-100);任务页/历史页分页 |
| exploration-graph.tsx(663) | 探索链路图 | ReactFlow;digest 折叠重接线(141-178);节点详情 Sheet;relLabel/relColor(47-59) |
| agent-editor.tsx(1159) | agent 六维配置器 | 提示词版本 diff/预览/重置;收尾+超时收尾;触发器定时;per-agent LLM;可见性 |
| task-template-controls.tsx(537) | 任务模板 | 套用/另存/更新/删;模板含分类+拦截规则预置(types.ts:52-61) |
| task-llm-profile-chain.tsx(223) | LLM 故障转移链编辑 | chips 多选+上下移;当前/已跳过/备用 N 徽(34-44) |
| asset-dsl-search.tsx(383) | 资产 DSL 搜索框(全局/任务共用) | 字段+操作符自动补全(=模糊/==精确/!=排除) |
| scope-text-editor.tsx | 企业范围文本编辑器 | 行级解析+错误定位(company-scope.ts:186-195) |
| mention-textarea.tsx(353) | @提及输入框 | 九类实体;AbortController 防抖 chatMentions;分页加载更多(35-95) |
| side-question-workspace.tsx(265) | 旁路提问工作区 | 可拖分栏+移动端 Drawer 双形态(242-262) |
| todo-popover.tsx | TodoWrite 待办浮层 | 定位最近 TodoWrite seq 弹详情 |
| finding-traffic-panel.tsx(285) | 发现↔流量绑定面板 | 四角色+排序+版本并发(§六.4) |
| traffic-evidence-viewer.tsx(181) | 流量证据查看器 | findingTrafficBody 分页取大 body |
| traffic-picker-dialog.tsx(277) | 流量挑选器 | 搜索+多选+预览+绑定 N 条(251-261,268) |
| link-traffic-dialog.tsx | 流量→发现绑定入口 | bindFindingTraffic |
| finding-retest-panel.tsx(187) | 复测状态面板 | findingRetests 轮询活跃项(54-81) |
| finding-retest-dialog.tsx | 发起复测 | startFindingRetest(id,notes)(42) |
| http-code-block.tsx(216) | HTTP 报文着色块 | 请求行/响应行状态码分色(11-40);复制+换行切换 |
| markdown.tsx | Markdown 渲染 | 报告/证据描述/agent 回复 |
| status-badge.tsx | 状态徽 | lib/status.ts 语义表单一来源 |
| table-pagination.tsx | 分页条 | 页大小 10/20/50 等 |
| copy-button.tsx | 复制按钮 | 非安全上下文 execCommand 降级 |
| asset-intercept-rules-editor.tsx | 任务级资产拦截规则编辑 | 创建任务/模板复用 |
| simple-icon.tsx / sortable-head / date-range-picker / calendar | 小件 | sortable-head=排序表头(流量页) |

UI 库 61 件(shadcn 系)不逐个展开;组合语言三件套: **Sheet 右抽屉=编辑器、AlertDialog=不可逆确认、Tabs=工作台分面**。

---

## 五、API 调用清单(前端视角)

- 形态: /api/* 同源反代(api.ts:1-4);258 方法键/83 静态路径前缀;SSE 4 条;上传 3 个。
- 认证/系统: authStatus/initPassword/login/changePassword/health/gc/audit/settings(get/set)/update(check/apply/rollback)+update/stream。
- 任务域: tasks CRUD/control(Task/s/Batch)/pin/rename/category CRUD(含 dnd 移动)/task-archives(list/restore/delete 单+批)/task-templates CRUD/deleteTask 五选项。
- 探索域: exploration graph/nodes(播报分页)/intents(分页)/frontier/activity(+detail/history)/main-sessions(+new)/tokens;chat 域: conversations CRUD(批量删/pin/rename)/messages/history/msgDetail/send/stop/profile/upload/status;worker: controlIntent/sendWorkerMessage/stopChat。
- 发现域: findings(页/组/资产树/stats)/getFinding/update/setSeverity/setStatus/delete/export/deepen/retests(start/list)/traffic(bind/edit/order/remove/body 预览)/lineage。
- 资产域: assets/search/counts/companies CRUD/scope 规则/asset-intercept CRUD/taskAssets(search/registerScopes/detach)/taskCoverage(Graph/Refs)/sync(scopesentry×4)。
- 流量域: traffic(列表/exchange/hosts)/delete(host/hosts/all)。
- 拦截域: rules CRUD+toggle/tool-config(范围)/judge(get/set+usage)/pending/decide/detail/execution/task 页/history 页。
- LLM 域: profiles CRUD/activate/fetchModels/test/pool(status/reset)/retryPolicy/get+save/records(页/detail/tasks/delete/by-model)。
- 军备域: agents CRUD/detail(promptVersions/variables/preview/reset×3/wrapup×2/config/visibility)/triggers CRUD;mcp(servers/save/refresh/tools/delete/visibility);skills(list/create/upload/dir/read/write/delete×2/meta/usage/visibility/missing/files);tools(list/save/reset/custom CRUD/test)。
- 通知域: notify meta/channels CRUD/test/deliveries(重投);workspace: list/read/write/mkdir/delete/upload/download。
- 消费结论: **每个页面的写操作 100% 走 api.ts 单通道**,无旁路 fetch(唯一例外: logs 页历史翻页直接 fetch /api/logs/history,logs/page.tsx:90)。

---

## 六、五个关键交互协议深录

### 1. 对话/会话消息流协议
- **任务会话签(主战协议)**: 每个 UI 会话(main|plan|intent:<id>|system)独立懒加载缓存;打开只拉最新页(200 条,activityHistory before=0 反向分页);单条**任务级 SSE** /api/exploration/activity/stream?task=…&since=snapshot_cursor 尾随全部 agent 新活动,帧按 session_key 分发,seq 去重——历史与实流在 snapshot_cursor 无缝对接(sessions-tab.tsx:87-96 注释整段,972-977);EventSource 自动重连,断线由 DB 补偿(977);内存帽 MAX_KEEP=4000(100);system 会话全量扫描重建(worker=system 或 llm_switch/llm_failover,677-717)。主 agent 回合按任务串行(chat lock),busy 判定任务级(1274-1282);**人类回合不乐观回声**——后端先落库再从同一条 SSE 推回(1333-1339 注释)。worker 会话以意图目标当"用户消息"引领(1341-1343)。
- **对话页(轻量协议)**: 列表 2s 轮询;会话打开拉最新页;**运行中 1s 尾轮询**(conversationMessages since=cursor),r.running 翻 false 即停(chat/page.tsx:580-608);上滚加载旧页保持滚动位置(628-652);粘底智能滚动(653-679)。对话页不上 SSE 是刻意分层。
- **旁路提问 /btw**: parent=/api/conversations/:id 或 /api/tasks/:id/chat 或 /api/tasks/:id/intents/:id(sessions-tab.tsx:1262-1268);POST side-questions(question+client_request_id 幂等键,side-questions.ts:56-57);运行项走 SSE /api/side-questions/:id/events(use-side-questions.ts:131)推 phase(preparing→summarizing_history→compressing_snapshot→retrying→answering)与 token 估算(side-questions.ts:21-30);失败/中断自动把问题草稿还原回输入框(46-55);可取消。

### 2. 任务详情十签(实测纠正: 不是 8 签)
sessions/overview/graph/broadcast/findings/retests/assets/coverage/intercept/report(detail/page.tsx:53-64)。编排逻辑=一场渗透的六个断面: **执行**(sessions)/**状态**(overview)/**拓扑**(graph+coverage 双图)/**流水**(broadcast)/**产出**(findings+retests+report)/**边界**(assets+intercept)。每签独立数据面与轮询频率(§一.4);任务级 SSE 由会话签持有。

### 3. 资产覆盖图力导向交互
- 引擎 @antv/G6;d3-force 力导向+drag-element-force(拖单点带力学)+drag-canvas+zoom-canvas(coverage-graph-tab.tsx behaviors 注册;页脚提示"力导向布局,可拖拽节点、滚轮缩放",693)。
- 数据: taskCoverageGraph(taskId)(481)——公司→根域名→子域名→IP→服务/App→端点七层+**测试进度着色**(覆盖度开关关闭时只显资产不显进度,types.ts:41,detail/page.tsx:442)。
- **折叠节点**: 每父节点同型子项默认 20(FOLD_LIMIT,32),超出折成灰色"⋯";点开 FoldSheet 列折叠子项,"展示更多"每次再拉 20(FOLD_STEP,33,698-706)。
- **点资产节点**开 AssetSheet: 详情+CoverageAssetRefs(哪些意图/发现覆盖它)+跳测试资产签;节点图标 lucide 手绘 data-URI 白描边(49-87);七型尺寸 46→20 递减(39-47)。

### 4. 发现详情证据展示
- 布局: 左主区(概览报告/关联流量/复测/链路图签,detail/page.tsx:328-331)+右状态面板(严重度/处置状态双 Select 乐观更新失败回滚,80-116;inherited 继承发现只读)。
- **证据=带角色的流量绑定**: baseline 正常对照/proof 漏洞证明/verification 补充验证/supporting 辅助证据(finding-traffic-panel.tsx:30-35);绑定列表**上下移排序**(orderFindingTraffic 传全序 id+**version 乐观并发**,旧版本拒写回滚 UI,90-95);改角色/备注(editFindingTraffic)、解绑(removeFindingTraffic);TrafficPickerDialog 从全局流量库搜索多选绑定;TrafficEvidenceViewer 分页拉大报文 body;列表页行展开才拉 report(641-660)。
- 报告新鲜度: finding 带 evidence_version/report_evidence_version/report_stale(types.ts:493-495)——报告按证据版本写,证据更新标记过期(呼应旧账"报告 Agent 按最新证据版本核对")。

### 5. 审批环(拦截→判定→人工→回放)
- **判定链**: 拦截范围(工具开关,范围外直接放行)→规则表(优先级首条命中: allow 放行/deny 拒绝并给模型回话/ask 转人工,ask 可配超时自动 deny|allow)→**模型兜底 judge**(范围内且无规则命中才语义判定;profile 可跟随激活配置;fail_action 兜底方向)→全记录入库。
- **人工面四处**: 侧栏红点 5s(nav-main.tsx:164-177)+仪表盘卡+审批页/任务拦截签+Transcript 内联卡(intercept_request 步骤直接决,transcript.tsx:96-98);decision_source 标 rule|model|timeout(approval-records.tsx:50-54);审计轨迹 InterceptAudit。
- **深链回放**: 每条记录来源(对话 #id 或任务 id)可点——先 interceptExecution 拿 session+seq,再带 ?approval=&c=|id= 跳对应页;目标页 ApprovalExecutionFocus 弹定位浮层,**连续回填历史页直到该 seq 的 tool_use 出现**并滚动高亮(approval-execution-focus.tsx:9-99)——回放完整上下文,不孤立展示一次调用。

---

## 七、交互模式总结: 它的产品语言是什么

1. **一切皆可编辑,一切可回滚**: 提示词带版本+diff+恢复默认;工具描述/参数默认值/技能文件/审批 judge 提示词全部界面可编辑;自定义件与内置件同台 CRUD。产品假设: **运营者要调教系统,不是使用系统**。
2. **服务端是唯一事实源**: 无乐观回声(人类回合后端先落库再推)、seq 单调幂等去重、审批回放走持久化查询、证据绑定带版本号拒绝覆盖。前端从不"造"数据,只做窗口。
3. **渐进披露的窗口化渲染**: 消息懒详情(useInView 400px)、历史反向分页+滚动位置保持、图折叠节点(20+20)、digest 压缩先于渲染、播报板服务端分页带 refs。大账本永远只渲染用户正在看的窗口。
4. **分层实时策略**: 1-3s 轮询给高频作战面,8-20s 给态势面,SSE 只给真长流(任务活动/日志/更新)+旁路问答;数据签名相同不重建 DOM。**实时性按信息衰减率分配,不按页面堆料**。
5. **双栏产品人格**: 功能组=打仗(任务-发现-流量-资产-报告主线),系统组=军备(LLM/agent/MCP/skill/工具/通知/拦截);一场仗的全部(执行/状态/拓扑/流水/产出/边界)收进任务详情十签——**"任务"是一等公民,页面只是它的切面**。
6. **对不可逆操作的敬畏**: 破坏性动作一律 AlertDialog 二次确认并写清后果(删任务五选项/删 skill 三级/移出任务资产保留全局);对不确定状态宁可关门(setup 不可达关闭入口)也不冒充。
7. **把治理做成可视化账本**: token 记到轮次与缓存命中、审批 judge 独立计量、技能未命中调用也统计、LLM 池熔断状态徽——**每个消耗与每次裁决都有数可查**,这是它区别于"聊天式渗透工具"的产品语言根基。

## 完成报

- 实读: web/src 全树 187 个 ts/tsx 中产品面相关全部(app 27 页含 10 签拆分、components 26+61、lib 20、hooks 4、stores/config/navigation/proxy);mock 层(6716 行)按结构确认未逐行。
- 报账: **24 主页面**(+3 辅助)/业务组件 26+侧栏 11+签组件 10+UI 库 61/**API 258 方法键·83 路径前缀·4 SSE 流·3 上传**。
- 最关键五机制: ①任务级 SSE+反向分页无缝会话流 ②任务详情十签工作台 ③覆盖图力导向+折叠+证据联动 ④发现证据四角色+版本并发 ⑤审批环(范围→规则→模型兜底→人工→深链回放)。
- 对旧账的两处事实修正: 任务详情是 **10 签**;对话页消息面是 **1s 轮询非 SSE**(SSE 只在任务会话签/旁路/日志/更新)。
- 纪律: ARTEX 源码零改;本仓只写本文件;pathspec 单文件提交。

# ARTEX 后端接口全链图 + CSAI 产品面（2026-10-20 源码实勘）

- 对象：ARTEX `/tmp/artex-look/ARTEX-main`（Go, module github.com/Autumn-27/artex）+ CSAI `/Users/wgen/dsh-test/repos/CyberStrikeAI`（Go, module cyberstrike-ai）。两仓**只读零改、不运行不安装**，全部结论出自源码阅读。
- 本档定位（对旧账的增量）：`docs/research/2026-10-20-csai-full-capability-inventory.md` 已有 CSAI 289 路由全列（app.go:706-1492），**本档不重列 CSAI 路由**，只引用行号并补「handler→表→逻辑」链；ARTEX 侧旧档（`2026-10-20-artex-full-capability-inventory.md`）只有能力摘要没有路由表，本档补全 261 条全表。
- 报账速览：**ARTEX 261 条注册**（GET 114 / POST 85 / PATCH 13 / DELETE 32 / PUT 17，另 `/` 嵌入式前端 1 条非 API 面）；**CSAI 289 条注册**（旧档已列）。关键机制五件+流量录制，全部带文件:行。

---

## 一、ARTEX 路由全表（261 条，方法+路径+handler 定义处+注册处）

注册机制：`Server.Handler()`（server/server.go:650-661）用 Go 1.22+ `http.ServeMux` 方法前缀模式注册；主体 243 条集中在 server.go:655-933，发现流量 7 条在 finding_traffic.go:82-90（base 前缀拼接），边问 11 条在 side_questions.go:273-286（3 父路径×3 方法循环+2 条固定）。全部挂 `/api/` 前缀经 CORS+JWT 中间件（auth 豁免组除外）；`/` 由 webui_embed 单二进制嵌入 Next.js 前端。存储=PostgreSQL 50 张表（db/ 包 CREATE TABLE 全集）+ traffic 侧车 SQLite 3 张（exchanges/exchange_bodies/blob_refs）+ 证据 blob 文件树（内容寻址）。

#### G1 认证·系统·日志·自更新（13 条）

链: 单管理员口令哈希存 `settings(auth.password_hash)`(auth.go:21)，登录签 JWT(auth.go:262)；health/stats 聚合内存+库(stats→tasks/exploration_nodes/assets/traffic 计数, server.go:951)；日志环形内存+`server_logs` 表落盘(logsink.go)；update 三条走 selfupdate 包(GitHub Release 拉取→SHA256 校验→冒烟→原子换装→3败自动回滚 artex.old)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/auth/status` | `authStatus` server/auth.go:144 | server.go:655 |
| POST | `/api/auth/init` | `authInit` server/auth.go:158 | server.go:656 |
| POST | `/api/auth/login` | `authLogin` server/auth.go:262 | server.go:657 |
| POST | `/api/auth/change-password` | `authChangePassword` server/auth.go:211 | server.go:658 |
| GET | `/api/health` | `health` server/server.go:947 | server.go:660 |
| GET | `/api/stats` | `stats` server/server.go:951 | server.go:661 |
| GET | `/api/logs` | `getLogs` server/server.go:2879 | server.go:662 |
| GET | `/api/logs/history` | `getLogsHistory` server/server.go:2889 | server.go:663 |
| GET | `/api/logs/stream` | `streamLogs` server/server.go:2928 | server.go:664 |
| GET | `/api/update/check` | `updateCheck` server/update.go:210 | server.go:668 |
| POST | `/api/update/apply` | `updateApply` server/update.go:270 | server.go:669 |
| POST | `/api/update/rollback` | `updateRollback` server/update.go:315 | server.go:670 |
| GET | `/api/update/stream` | `updateStream` server/update.go:333 | server.go:671 |

#### G2 任务域(建/查/分类/模板/归档/覆盖/资产挂接)（34 条）

链: createTask(server.go:1462) 校验 LLM 档案/关联任务去重/企业归一/任务级拦截规则→`tasks`+`explorations`+`task_relations`(关联继承)+`task_llm_profiles`+`task_intercept_rules`→launchTask 异步(seed 意图+engine.Run)；分类/模板/批量改类→`task_categories`/`task_templates`；归档五条全部走**队列异步**(queueTaskArchive→`task_archives`+快照)整仗导出带全量证据；coverage 两条读探索图聚合覆盖面；asset-refs/intent-assets→`task_asset_links`。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/tasks` | `listTasks` server/server.go:1036 | server.go:673 |
| POST | `/api/tasks` | `createTask` server/server.go:1462 | server.go:674 |
| GET | `/api/task-categories` | `pgListTaskCategories` server/task_categories.go:57 | server.go:675 |
| POST | `/api/task-categories` | `pgCreateTaskCategory` server/task_categories.go:70 | server.go:676 |
| PATCH | `/api/task-categories/{id}` | `pgRenameTaskCategory` server/task_categories.go:87 | server.go:677 |
| DELETE | `/api/task-categories/{id}` | `pgDeleteTaskCategory` server/task_categories.go:105 | server.go:678 |
| POST | `/api/tasks/category/batch` | `updateTasksCategoryBatch` server/task_categories.go:181 | server.go:679 |
| GET | `/api/task-templates` | `pgListTaskTemplates` server/task_templates.go:97 | server.go:680 |
| POST | `/api/task-templates` | `pgCreateTaskTemplate` server/task_templates.go:110 | server.go:681 |
| PATCH | `/api/task-templates/{id}` | `pgUpdateTaskTemplate` server/task_templates.go:142 | server.go:682 |
| DELETE | `/api/task-templates/{id}` | `pgDeleteTaskTemplate` server/task_templates.go:189 | server.go:683 |
| GET | `/api/tasks/{id}` | `getTask` server/server.go:1728 | server.go:684 |
| PATCH | `/api/tasks/{id}` | `updateTaskMetadata` server/task_metadata.go:20 | server.go:685 |
| PATCH | `/api/tasks/{id}/category` | `updateTaskCategory` server/task_categories.go:143 | server.go:686 |
| GET | `/api/tasks/{id}/intercept-rules` | `taskInterceptListRules` server/task_intercept.go:59 | server.go:688 |
| POST | `/api/tasks/{id}/intercept-rules` | `taskInterceptCreateRule` server/task_intercept.go:80 | server.go:689 |
| PUT | `/api/tasks/{id}/intercept-rules/{rid}` | `taskInterceptUpdateRule` server/task_intercept.go:107 | server.go:690 |
| DELETE | `/api/tasks/{id}/intercept-rules/{rid}` | `taskInterceptDeleteRule` server/task_intercept.go:139 | server.go:691 |
| POST | `/api/tasks/{id}/intercept-rules/{rid}/toggle` | `taskInterceptToggleRule` server/task_intercept.go:162 | server.go:692 |
| GET | `/api/task-archives` | `listTaskArchives` server/task_archives.go:438 | server.go:694 |
| GET | `/api/task-archives/{id}` | `getTaskArchive` server/task_archives.go:449 | server.go:695 |
| POST | `/api/tasks/{id}/archive` | `queueTaskArchive` server/task_archives.go:467 | server.go:696 |
| POST | `/api/tasks/archive/batch` | `queueTaskArchivesBatch` server/task_archives.go:513 | server.go:697 |
| POST | `/api/task-archives/{id}/restore` | `queueTaskArchiveRestore` server/task_archives.go:483 | server.go:698 |
| POST | `/api/task-archives/restore/batch` | `restoreTaskArchivesBatch` server/task_archives.go:585 | server.go:699 |
| DELETE | `/api/task-archives/{id}` | `queueTaskArchiveDelete` server/task_archives.go:498 | server.go:700 |
| POST | `/api/task-archives/delete/batch` | `deleteTaskArchivesBatch` server/task_archives.go:589 | server.go:701 |
| GET | `/api/tasks/{id}/coverage` | `taskCoverage` server/server.go:1741 | server.go:702 |
| GET | `/api/tasks/{id}/coverage-graph` | `taskCoverageGraph` server/server.go:1769 | server.go:703 |
| GET | `/api/tasks/{id}/asset-refs` | `taskAssetRefs` server/server.go:1791 | server.go:704 |
| POST | `/api/tasks/{id}/assets` | `attachTaskAssets` server/task_assets.go:24 | server.go:705 |
| DELETE | `/api/tasks/{id}/assets/{assetID}` | `detachTaskAsset` server/task_assets.go:70 | server.go:706 |
| GET | `/api/tasks/{id}/intent-assets` | `taskIntentAssets` server/task_assets.go:95 | server.go:707 |
| DELETE | `/api/tasks/{id}` | `pgDeleteTask` server/server_mgmt.go:133 | server.go:821 |

#### G3 工作区与任务范围（10 条）

链: workspace 七条=任务工作目录的文件管理器(列/读/写/mkdir/删/下载/上传, workspace.go:59-229, 读写磁盘目录树非库表)；scope 三条→`task_scope` 表(目标域名/IP 白名单, 进 agent 简报)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/workspace/list` | `wsList` server/workspace.go:59 | server.go:710 |
| GET | `/api/workspace/read` | `wsRead` server/workspace.go:105 | server.go:711 |
| POST | `/api/workspace/write` | `wsWrite` server/workspace.go:137 | server.go:712 |
| POST | `/api/workspace/mkdir` | `wsMkdir` server/workspace.go:167 | server.go:713 |
| DELETE | `/api/workspace/delete` | `wsDelete` server/workspace.go:189 | server.go:714 |
| GET | `/api/workspace/download` | `wsDownload` server/workspace.go:211 | server.go:715 |
| POST | `/api/workspace/upload` | `wsUpload` server/workspace.go:229 | server.go:716 |
| GET | `/api/tasks/{id}/scope` | `taskScopeList` server/server.go:1825 | server.go:717 |
| POST | `/api/tasks/{id}/scope` | `taskScopeAdd` server/server.go:1845 | server.go:718 |
| DELETE | `/api/tasks/{id}/scope/{sid}` | `taskScopeDelete` server/server.go:1874 | server.go:719 |

#### G4 目标·约束·任务/意图控制（17 条）

链: goals 四条→`exploration_nodes(kind=goal)` 人工增删目标会复活终态任务(goals_api.go:34 注释)；constraints 四条→`task_constraints` 只注入 worker 简报不通知 planner(constraints_api.go:49)；control=pause/resume 双动词(server.go:1114→engine.Pause/Resume)；controlIntent=单意图 pause/resume/cancel, 运行中 worker 先停再改态防迟到输出复活黑板(server.go:1142)；messages=向运行中意图注入人类消息(steer, intent_intervention.go:38)；rerun/rerun-blocked=重跑 blocked/exhausted/stopped 意图(server.go:1194/1238)；任务级 LLM 档案 PUT→`task_llm_profiles` 热切。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| POST | `/api/tasks/control/batch` | `controlTasksBatch` server/task_control.go:246 | server.go:693 |
| GET | `/api/tasks/{id}/goals` | `listGoals` server/goals_api.go:18 | server.go:720 |
| POST | `/api/tasks/{id}/goals` | `addGoal` server/goals_api.go:34 | server.go:721 |
| PATCH | `/api/tasks/{id}/goals/{gid}` | `editGoal` server/goals_api.go:83 | server.go:722 |
| DELETE | `/api/tasks/{id}/goals/{gid}` | `deleteGoal` server/goals_api.go:139 | server.go:723 |
| GET | `/api/tasks/{id}/constraints` | `listConstraints` server/constraints_api.go:34 | server.go:724 |
| POST | `/api/tasks/{id}/constraints` | `addConstraint` server/constraints_api.go:49 | server.go:725 |
| PATCH | `/api/tasks/{id}/constraints/{cid}` | `editConstraint` server/constraints_api.go:88 | server.go:726 |
| DELETE | `/api/tasks/{id}/constraints/{cid}` | `deleteConstraint` server/constraints_api.go:131 | server.go:727 |
| POST | `/api/tasks/{id}/control` | `control` server/server.go:1114 | server.go:728 |
| PUT | `/api/tasks/{id}/llm` | `updateTaskLLMProfiles` server/server.go:1551 | server.go:729 |
| GET | `/api/tasks/{id}/llm/resolution` | `taskLLMResolutionHandler` server/task_resolution.go:103 | server.go:730 |
| POST | `/api/tasks/{id}/intents/{iid}/control` | `controlIntent` server/server.go:1142 | server.go:731 |
| POST | `/api/tasks/{id}/intents/{iid}/messages` | `sendWorkerMessage` server/intent_intervention.go:38 | server.go:732 |
| POST | `/api/tasks/{id}/intents/{iid}/rerun` | `rerunIntent` server/server.go:1194 | server.go:733 |
| POST | `/api/tasks/{id}/intents/rerun-blocked` | `rerunBlocked` server/server.go:1238 | server.go:734 |
| GET | `/api/exploration/intents` | `intents` server/server.go:2368 | server.go:770 |

#### G5 活跃任务与全局 LLM（4 条）

链: /api/active 切全局活跃任务(setActive→engine nudge)；GET/POST /api/llm 全局 provider 配置(server.go:1288/1307, 存 DB 重启生效, 热应用到运行引擎)；testLLM 一次性连通测试。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| POST | `/api/active` | `setActive` server/server.go:1093 | server.go:735 |
| GET | `/api/llm` | `getLLM` server/server.go:1288 | server.go:737 |
| POST | `/api/llm` | `setLLM` server/server.go:1307 | server.go:738 |
| POST | `/api/llm/test` | `testLLM` server/server.go:1366 | server.go:739 |

#### G6 资产·企业（10 条）

链: assets 四条→`assets` 表(分页/计数/批量插/批量删)；companies 六条→`companies`+`company_scope` 多租户范围(addCompanyScope 联动任务 scope 一致性检查)+reattribute 资产重归属(company_scope.go)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/assets` | `listAssets` server/assets.go:319 | server.go:742 |
| GET | `/api/assets/counts` | `assetCounts` server/assets.go:396 | server.go:743 |
| POST | `/api/assets` | `insertAssets` server/assets.go:449 | server.go:744 |
| DELETE | `/api/assets` | `deleteAssets` server/assets.go:420 | server.go:745 |
| GET | `/api/companies` | `listCompanies` server/assets.go:77 | server.go:748 |
| POST | `/api/companies` | `createCompany` server/assets.go:95 | server.go:749 |
| GET | `/api/companies/{id}` | `getCompany` server/assets.go:149 | server.go:750 |
| DELETE | `/api/companies/{id}` | `deleteCompany` server/assets.go:247 | server.go:751 |
| POST | `/api/companies/{id}/scope` | `addCompanyScope` server/assets.go:181 | server.go:752 |
| POST | `/api/companies/reattribute` | `reattribute` server/assets.go:297 | server.go:753 |

#### G7 探索图·发现·复测·证据流量绑定（30 条）

链: 全部读 `explorations`/`exploration_nodes`/`exploration_edges`/`findings`(+`finding_traffic_bindings`/`traffic_evidence_snapshots`)；findings 列表/分组/资产树/统计/导出(分组=同 vulnclass 聚合)；deepenFinding=把组提升为新意图继续挖(findings_groups.go:92→`AddFindingFollowUpIntent` db/findings.go:374)；lineage=意图→发现证据血缘；patchFinding→状态机(9 态枚举校验 db/findings.go:53)+严重度改名改类；retests 三条见机制§4；traffic 七条=人工绑定/解绑/排序/正文回看(乐观并发版本号, 旧版本拒写)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/exploration/frontier` | `frontier` server/server.go:1903 | server.go:755 |
| GET | `/api/exploration/findings` | `findings` server/server.go:1913 | server.go:756 |
| GET | `/api/exploration/findings/groups` | `findingGroups` server/findings_groups.go:58 | server.go:757 |
| GET | `/api/exploration/findings/asset-tree` | `findingAssetTree` server/findings_groups.go:45 | server.go:758 |
| GET | `/api/exploration/findings/stats` | `findingStats` server/server.go:2049 | server.go:759 |
| GET | `/api/exploration/findings/export` | `findingsExport` server/server.go:2101 | server.go:760 |
| GET | `/api/exploration/findings/{id}` | `getFinding` server/server.go:2060 | server.go:762 |
| GET | `/api/exploration/findings/{id}/lineage` | `findingLineage` server/server.go:2221 | server.go:763 |
| POST | `/api/exploration/findings/{id}/deepen` | `deepenFinding` server/findings_groups.go:92 | server.go:764 |
| GET | `/api/exploration/findings/{id}/retests` | `listFindingRetests` server/finding_retests.go:34 | server.go:765 |
| GET | `/api/exploration/findings/retests/active` | `listActiveFindingRetests` server/finding_retests.go:21 | server.go:766 |
| POST | `/api/exploration/findings/{id}/retests` | `startFindingRetest` server/finding_retests.go:61 | server.go:767 |
| PATCH | `/api/exploration/findings/{id}` | `patchFinding` server/server.go:2258 | server.go:768 |
| DELETE | `/api/exploration/findings/{id}` | `deleteFinding` server/server.go:2350 | server.go:769 |
| GET | `/api/exploration/graph` | `explorationGraph` server/server.go:2493 | server.go:771 |
| GET | `/api/exploration/nodes` | `explorationNodes` server/server.go:2539 | server.go:772 |
| GET | `/api/exploration/activity` | `activity` server/server.go:2642 | server.go:773 |
| GET | `/api/exploration/activity/history` | `activityHistory` server/server.go:2737 | server.go:774 |
| GET | `/api/exploration/main-sessions` | `mainSessions` server/server.go:3620 | server.go:775 |
| POST | `/api/exploration/main-session/new` | `newMainSession` server/server.go:3641 | server.go:776 |
| GET | `/api/exploration/activity/stream` | `streamActivity` server/server.go:2979 | server.go:777 |
| GET | `/api/exploration/activity/{seq}` | `activityDetail` server/server.go:3078 | server.go:778 |
| GET | `/api/exploration/tokens` | `tokenStats` server/server.go:2811 | server.go:779 |
| GET | `/api/exploration/findings/{id}/traffic` | `getFindingTraffic` server/finding_traffic.go:148 |  |
| POST | `/api/exploration/findings/{id}/traffic` | `bindFindingTraffic` server/finding_traffic.go:161 |  |
| PATCH | `/api/exploration/findings/{id}/traffic/{binding_id}` | `editFindingTraffic` server/finding_traffic.go:185 |  |
| DELETE | `/api/exploration/findings/{id}/traffic/{binding_id}` | `editFindingTraffic` server/finding_traffic.go:185 |  |
| PUT | `/api/exploration/findings/{id}/traffic/order` | `editFindingTraffic` server/finding_traffic.go:185 |  |
| GET | `/api/exploration/findings/{id}/traffic/{binding_id}` | `getFindingTrafficDetail` server/finding_traffic.go:284 |  |
| GET | `/api/exploration/findings/{id}/traffic/{binding_id}/body` | `getFindingTrafficBody` server/finding_traffic.go:315 |  |

#### G8 审计·GC·流量回看（9 条）

链: audit 读 guard 内存审计环(2000 条)；gc=证据 GC(blob 内容寻址+24h 宽限)；traffic 七条=录制库回看(分页/主机聚合/删主机/清空/exchange 原文/blob 体块)——读 traffic 侧车 SQLite 非 PG。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/audit` | `getAudit` server/server.go:3864 | server.go:784 |
| POST | `/api/gc` | `gc` server/server.go:3874 | server.go:785 |
| GET | `/api/traffic` | `getTraffic` server/server.go:3101 | server.go:786 |
| GET | `/api/traffic/hosts` | `getTrafficHosts` server/server.go:3136 | server.go:787 |
| DELETE | `/api/traffic` | `deleteTraffic` server/server.go:3155 | server.go:788 |
| DELETE | `/api/traffic/hosts` | `deleteTrafficHosts` server/server.go:3178 | server.go:789 |
| DELETE | `/api/traffic/all` | `deleteAllTraffic` server/server.go:3214 | server.go:790 |
| GET | `/api/traffic/exchange` | `getTrafficExchange` server/server.go:3230 | server.go:791 |
| GET | `/api/traffic/blob` | `getTrafficBlob` server/server.go:3253 | server.go:792 |

#### G9 命令·LLM 流水·token 统计（10 条）

链: commands 两条→`tool_usage` 表按工具聚合；llm/records 五条→`llm_records`(llmrec 装饰器全量录制请求/响应)+`llm_usage` 聚合；tokens 四条=任务/会话/日/全局用量账本。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/tokens/daily` | `tokenDailyStats` server/server.go:2841 | server.go:780 |
| GET | `/api/tokens/conversations` | `conversationTokens` server/server.go:2861 | server.go:781 |
| GET | `/api/tokens/usage` | `pgUsageStats` server/commands.go:101 | server.go:782 |
| GET | `/api/commands` | `pgListCommands` server/commands.go:12 | server.go:793 |
| GET | `/api/commands/stats` | `pgToolStats` server/commands.go:29 | server.go:794 |
| GET | `/api/llm/records` | `pgListLLMRecords` server/commands.go:58 | server.go:795 |
| DELETE | `/api/llm/records` | `pgDeleteLLMRecords` server/commands.go:134 | server.go:796 |
| GET | `/api/llm/records/tasks` | `pgLLMTasks` server/commands.go:123 | server.go:797 |
| GET | `/api/llm/records/by-model` | `pgTokenByModel` server/commands.go:78 | server.go:798 |
| GET | `/api/llm/records/{id}` | `pgGetLLMRecord` server/commands.go:149 | server.go:799 |

#### G10 设置·通知·报告·聊天(含任务内主聊)（18 条）

链: settings 读写`settings`键值(含 agent_traffic_binding 开关=发现自动绑流量的总闸, 下轮生效运行中拒改)；notify 八条→`notification_channels`/`notification_deliveries`(渠道 CRUD+测试+重投)；report=report 包渲染 Markdown 交付报告；chat 三条+任务内 chat 两条=主 Agent 对话(chat→chatAgent 一轮, upload 落会话 uploads/, mentions 跨任务@引用)；stopChat 中止任务主聊。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/settings` | `getSettings` server/server.go:3281 | server.go:800 |
| PUT | `/api/settings` | `putSettings` server/server.go:3361 | server.go:801 |
| GET | `/api/notify/meta` | `notifyMeta` server/notify_api.go:114 | server.go:804 |
| GET | `/api/notify/channels` | `notifyListChannels` server/notify_api.go:147 | server.go:805 |
| POST | `/api/notify/channels` | `notifyCreateChannel` server/notify_api.go:178 | server.go:806 |
| PATCH | `/api/notify/channels/{id}` | `notifyUpdateChannel` server/notify_api.go:254 | server.go:807 |
| DELETE | `/api/notify/channels/{id}` | `notifyDeleteChannel` server/notify_api.go:377 | server.go:808 |
| POST | `/api/notify/channels/{id}/test` | `notifyTestChannel` server/notify_api.go:399 | server.go:809 |
| GET | `/api/notify/deliveries` | `notifyListDeliveries` server/notify_api.go:465 | server.go:810 |
| POST | `/api/notify/deliveries/{id}/retry` | `notifyRetryDelivery` server/notify_api.go:491 | server.go:811 |
| POST | `/api/settings/web-search/test` | `testWebSearch` server/server.go:3563 | server.go:812 |
| GET | `/api/report` | `getReport` server/server.go:3841 | server.go:813 |
| GET | `/api/chat/mentions` | `searchChatMentions` server/chat_mentions.go:58 | server.go:814 |
| POST | `/api/chat` | `chat` server/server.go:3659 | server.go:815 |
| POST | `/api/chat/upload` | `chatUpload` server/chatupload.go:46 | server.go:816 |
| GET | `/api/tasks/{id}/chat/status` | `taskChatStatus` server/server.go:3788 | server.go:817 |
| POST | `/api/tasks/{id}/chat/stop` | `stopChat` server/server.go:3803 | server.go:818 |
| POST | `/api/settings/python/detect` | `pgDetectPython` server/server.go:3345 | server.go:863 |

#### G11 会话(平台对话)（10 条）

链: conversations 十条→`conversations`+`conversation_activities`(每步落 activity 流)；发消息→runConversation 异步一轮(busy 锁防并发, conversations.go:465)；profile PATCH 热切会话 LLM；stop 中止；messages/{seq} 单步详情。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/conversations` | `pgListConversations` server/conversations.go:54 | server.go:824 |
| POST | `/api/conversations` | `pgCreateConversation` server/conversations.go:73 | server.go:825 |
| POST | `/api/conversations/delete/batch` | `pgDeleteConversationsBatch` server/conversations.go:248 | server.go:826 |
| PATCH | `/api/conversations/{id}` | `pgRenameConversation` server/conversations.go:173 | server.go:827 |
| PATCH | `/api/conversations/{id}/profile` | `pgUpdateConversation` server/conversations.go:126 | server.go:828 |
| DELETE | `/api/conversations/{id}` | `pgDeleteConversation` server/conversations.go:213 | server.go:829 |
| GET | `/api/conversations/{id}/messages` | `pgConversationMessages` server/conversations.go:306 | server.go:830 |
| POST | `/api/conversations/{id}/messages` | `pgSendConversationMessage` server/conversations.go:388 | server.go:831 |
| POST | `/api/conversations/{id}/stop` | `pgStopConversation` server/conversations.go:368 | server.go:832 |
| GET | `/api/conversations/{id}/messages/{seq}` | `pgConversationMsgDetail` server/conversations.go:347 | server.go:833 |

#### G12 Agent 配置面(含触发器/提示词版本)（21 条）

链: agents 21 条→`agents`/`agent_prompts`(版本化, 可 reset 回内置)/`agent_prompt_vars`/`agent_triggers`(事件触发器: interval/finding/goal/task_timeout/task_create/tool_call 六类)/`agent_visibility`/`agent_skill_visibility`；prompt/preview=变量代入预览；wrapup=收尾白名单可编辑(含任务超时专用收尾)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/agents` | `pgListAgents` server/server_mgmt.go:222 | server.go:835 |
| POST | `/api/agents` | `pgCreateAgent` server/server_mgmt.go:246 | server.go:836 |
| GET | `/api/agents/{key}` | `pgGetAgent` server/server_mgmt.go:469 | server.go:837 |
| PATCH | `/api/agents/{key}` | `pgUpdateAgent` server/server_mgmt.go:282 | server.go:838 |
| DELETE | `/api/agents/{key}` | `pgDeleteAgent` server/server_mgmt.go:310 | server.go:839 |
| PUT | `/api/agents/{key}/config` | `pgSaveAgentConfig` server/server_mgmt.go:351 | server.go:840 |
| PUT | `/api/agents/{key}/prompt` | `pgSavePrompt` server/server_mgmt.go:512 | server.go:841 |
| POST | `/api/agents/{key}/prompt/reset` | `pgResetPrompt` server/server_mgmt.go:537 | server.go:842 |
| PUT | `/api/agents/{key}/wrapup` | `pgSaveWrapup` server/server_mgmt.go:557 | server.go:843 |
| POST | `/api/agents/{key}/wrapup/reset` | `pgResetWrapup` server/server_mgmt.go:590 | server.go:844 |
| PUT | `/api/agents/{key}/wrapup/task-timeout` | `pgSaveTaskTimeoutWrapup` server/server_mgmt.go:612 | server.go:845 |
| POST | `/api/agents/{key}/wrapup/task-timeout/reset` | `pgResetTaskTimeoutWrapup` server/server_mgmt.go:640 | server.go:846 |
| GET | `/api/agents/{key}/triggers` | `pgListTriggers` server/triggers.go:11 | server.go:847 |
| POST | `/api/agents/{key}/triggers` | `pgCreateTrigger` server/triggers.go:53 | server.go:848 |
| PATCH | `/api/triggers/{id}` | `pgUpdateTrigger` server/triggers.go:88 | server.go:849 |
| DELETE | `/api/triggers/{id}` | `pgDeleteTrigger` server/triggers.go:123 | server.go:850 |
| GET | `/api/agents/{key}/prompts` | `pgListPromptVersions` server/server_mgmt.go:656 | server.go:851 |
| GET | `/api/agents/{key}/variables` | `pgPromptVars` server/server_mgmt.go:669 | server.go:852 |
| POST | `/api/agents/{key}/prompt/preview` | `pgPreviewPrompt` server/server_mgmt.go:682 | server.go:853 |
| GET | `/api/agents/{key}/visibility` | `pgGetAgentVisibility` server/server_mgmt.go:704 | server.go:854 |
| PUT | `/api/agents/{key}/visibility` | `pgSetAgentVisibility` server/server_mgmt.go:717 | server.go:855 |

#### G13 工具·自定义工具·MCP 注册（12 条）

链: tools→`tools` 表(description/schema/agents 绑定数组/enabled, reset 回内置)；custom 四条=自定义 HTTP 工具 CRUD+test(出网走录制代理 customtool.go:465)；MCP 五条→`mcp_servers`+`mcp_tools_cache`(refresh 拉远端工具列表入缓存, 运行时经 mcphttp 适配为 CoreTool)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/tools` | `pgListTools` server/server_mgmt.go:743 | server.go:857 |
| PUT | `/api/tools/{key}` | `pgUpdateTool` server/server_mgmt.go:773 | server.go:858 |
| POST | `/api/tools/custom` | `pgCreateCustomTool` server/customtool.go:45 | server.go:859 |
| POST | `/api/tools/custom/test` | `pgTestCustomTool` server/customtool.go:146 | server.go:860 |
| PUT | `/api/tools/custom/{key}` | `pgUpdateCustomTool` server/customtool.go:82 | server.go:861 |
| DELETE | `/api/tools/custom/{key}` | `pgDeleteCustomTool` server/customtool.go:120 | server.go:862 |
| POST | `/api/tools/{key}/reset` | `pgResetTool` server/server_mgmt.go:809 | server.go:864 |
| GET | `/api/mcp` | `pgListMCP` server/server_mgmt.go:847 | server.go:866 |
| POST | `/api/mcp` | `pgSaveMCP` server/server_mgmt.go:863 | server.go:867 |
| DELETE | `/api/mcp/{id}` | `pgDeleteMCP` server/server_mgmt.go:893 | server.go:868 |
| GET | `/api/mcp/{id}/tools` | `pgMCPTools` server/server_mgmt.go:941 | server.go:869 |
| POST | `/api/mcp/{id}/refresh` | `pgRefreshMCP` server/server_mgmt.go:908 | server.go:870 |

#### G14 ScopeSentry 资产同步（5 条）

链: 五条=数据源配置→项目/任务列表→一键同步(按项目任务维度拉域名/子域/IP/端口/端点写 `assets`, sync_scopesentry.go)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/sync/scopesentry/status` | `syncSSStatus` server/sync_scopesentry.go:74 | server.go:872 |
| POST | `/api/sync/scopesentry/datasource` | `syncSSDatasource` server/sync_scopesentry.go:118 | server.go:873 |
| GET | `/api/sync/scopesentry/projects` | `syncSSProjects` server/sync_scopesentry.go:166 | server.go:874 |
| GET | `/api/sync/scopesentry/tasks` | `syncSSTasks` server/sync_scopesentry.go:209 | server.go:875 |
| POST | `/api/sync/scopesentry/sync` | `syncSSRun` server/sync_scopesentry.go:258 | server.go:876 |

#### G15 技能(文件系统+使用量)（12 条）

链: 13 条=技能包**文件系统** CRUD(zip 上传解包/建目录/读写文件/删)+`skill_usage`(每次调用 metered 一行, skill_usage.go:21)+missing(想调不存在的技能名=飞轮缺口信号)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/skills` | `fsListSkills` server/server_mgmt.go:975 | server.go:878 |
| POST | `/api/skills` | `fsCreateSkill` server/server_mgmt.go:1075 | server.go:879 |
| POST | `/api/skills/upload` | `fsUploadSkill` server/server_mgmt.go:1292 | server.go:880 |
| DELETE | `/api/skills/{name}` | `fsDeleteSkill` server/server_mgmt.go:1455 | server.go:881 |
| GET | `/api/skills/missing` | `fsMissingSkills` server/server_mgmt.go:1050 | server.go:882 |
| GET | `/api/skills/{name}/usage` | `fsSkillUsage` server/server_mgmt.go:1029 | server.go:883 |
| PUT | `/api/skills/{name}/meta` | `fsUpdateSkillMeta` server/server_mgmt.go:1145 | server.go:884 |
| POST | `/api/skills/{name}/dirs` | `fsCreateDir` server/server_mgmt.go:1648 | server.go:885 |
| GET | `/api/skills/{name}/files` | `fsListFiles` server/server_mgmt.go:1567 | server.go:886 |
| GET | `/api/skills/{name}/files/{file...}` | `fsReadFile` server/server_mgmt.go:1589 | server.go:888 |
| PUT | `/api/skills/{name}/files/{file...}` | `fsWriteFile` server/server_mgmt.go:1612 | server.go:889 |
| DELETE | `/api/skills/{name}/files/{file...}` | `fsDeletePath` server/server_mgmt.go:1678 | server.go:890 |

#### G16 可见性(资源/技能)（4 条）

链: 四条→`agent_visibility`/`agent_skill_visibility`(按 agent 控制工具/技能可见性, 精细化白名单)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/visibility/{kind}/{id}` | `pgResourceVisibility` server/server_mgmt.go:1739 | server.go:892 |
| POST | `/api/visibility/toggle` | `pgToggleVisibility` server/server_mgmt.go:1753 | server.go:893 |
| GET | `/api/visibility/skill/{name}` | `pgSkillVisibility` server/server_mgmt.go:1703 | server.go:895 |
| POST | `/api/visibility/skill/toggle` | `pgToggleSkillVisibility` server/server_mgmt.go:1716 | server.go:896 |

#### G17 LLM 档案·重试策略·故障转移池（9 条）

链: profiles→`llm_profiles`(多档案 CRUD+激活)；retry-policy→重试参数；pool 两条=llmpool 故障转移链状态查看/复位(active 优先+按优先级+熔断, llmpool/health.go)；models=拉上游模型列表。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/llm/profiles` | `pgListProfiles` server/server_mgmt.go:1777 | server.go:898 |
| POST | `/api/llm/profiles` | `pgSaveProfile` server/server_mgmt.go:1790 | server.go:899 |
| DELETE | `/api/llm/profiles/{id}` | `pgDeleteProfile` server/server_mgmt.go:1870 | server.go:900 |
| POST | `/api/llm/profiles/active` | `pgActivateProfile` server/server_mgmt.go:1920 | server.go:901 |
| GET | `/api/llm/retry-policy` | `pgGetLLMRetryPolicy` server/server_mgmt.go:1839 | server.go:902 |
| POST | `/api/llm/retry-policy` | `pgSaveLLMRetryPolicy` server/server_mgmt.go:1850 | server.go:903 |
| GET | `/api/llm/pool` | `pgLLMPoolStatus` server/server_mgmt.go:1944 | server.go:904 |
| POST | `/api/llm/pool/reset` | `pgLLMPoolReset` server/server_mgmt.go:1953 | server.go:905 |
| POST | `/api/llm/models` | `pgListModels` server/server_mgmt.go:1979 | server.go:906 |

#### G18 拦截与审批(全局规则·任务规则·资产规则·待决·历史·裁判配置)（22 条）

链: 三套规则(全局`intercept_rules`/任务级`task_intercept_rules`/资产级`asset_intercept_rules`)；pending 三条=待决列表/详情/**decide 人工裁决**(intercept.go:353→Interceptor.Decide 唤醒阻塞协程)；history 三条+task 聚合=已决历史+执行后回执；tool-config=哪些工具进拦截；judge 两条=LLM 兜底裁判配置(fail_action/ask_timeout_action)+judge 用量账本(judge 车道独立计费)。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/intercept/rules` | `interceptListRules` server/intercept.go:98 | server.go:909 |
| POST | `/api/intercept/rules` | `interceptCreateRule` server/intercept.go:114 | server.go:910 |
| PUT | `/api/intercept/rules/{id}` | `interceptUpdateRule` server/intercept.go:137 | server.go:911 |
| DELETE | `/api/intercept/rules/{id}` | `interceptDeleteRule` server/intercept.go:165 | server.go:912 |
| POST | `/api/intercept/rules/{id}/toggle` | `interceptToggleRule` server/intercept.go:183 | server.go:913 |
| GET | `/api/asset-intercept/rules` | `assetInterceptListRules` server/asset_intercept.go:17 | server.go:916 |
| POST | `/api/asset-intercept/rules` | `assetInterceptCreateRule` server/asset_intercept.go:33 | server.go:917 |
| PUT | `/api/asset-intercept/rules/{id}` | `assetInterceptUpdateRule` server/asset_intercept.go:55 | server.go:918 |
| DELETE | `/api/asset-intercept/rules/{id}` | `assetInterceptDeleteRule` server/asset_intercept.go:82 | server.go:919 |
| POST | `/api/asset-intercept/rules/{id}/toggle` | `assetInterceptToggleRule` server/asset_intercept.go:99 | server.go:920 |
| GET | `/api/intercept/pending` | `interceptListPending` server/intercept.go:210 | server.go:922 |
| GET | `/api/intercept/pending/{id}` | `interceptGetOne` server/intercept.go:226 | server.go:923 |
| POST | `/api/intercept/pending/{id}/decide` | `interceptDecide` server/intercept.go:353 | server.go:924 |
| GET | `/api/intercept/history` | `interceptHistory` server/intercept.go:288 | server.go:925 |
| GET | `/api/intercept/history/{id}` | `interceptDetail` server/intercept.go:511 | server.go:926 |
| GET | `/api/intercept/history/{id}/execution` | `interceptExecution` server/intercept.go:534 | server.go:927 |
| GET | `/api/intercept/task/{taskID}` | `interceptListTaskItems` server/intercept.go:248 | server.go:928 |
| GET | `/api/intercept/tool-config` | `interceptGetToolConfig` server/intercept.go:385 | server.go:929 |
| PUT | `/api/intercept/tool-config` | `interceptSetToolConfig` server/intercept.go:396 | server.go:930 |
| GET | `/api/intercept/judge` | `interceptGetJudgeConfig` server/intercept.go:418 | server.go:931 |
| PUT | `/api/intercept/judge` | `interceptSetJudgeConfig` server/intercept.go:423 | server.go:932 |
| GET | `/api/intercept/judge/usage` | `interceptJudgeUsage` server/intercept.go:450 | server.go:933 |

#### G19 边问(side-questions)（11 条）

链: 3 父路径(conversation/task-chat/task-worker)×3 方法循环注册(side_questions.go:273-282)+事件流/取消两条→`side_question_requests`/`side_question_sessions`；对**冻结的主 Agent 检查点**提问(sidequestion 捕获不可变 checkpoint), 不拥有会话不碰工具执行器, DELETE=清该父的历史。

| 方法 | 路径 | handler（定义） | 注册 |
|---|---|---|---|
| GET | `/api/side-questions/{requestID}/events` | `sideEvents` server/side_questions.go:528 | side_questions.go:284 |
| POST | `/api/side-questions/{requestID}/cancel` | `cancelSideRequest` server/side_questions.go:510 | side_questions.go:285 |
| GET | `/api/conversations/{id}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| POST | `/api/conversations/{id}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| DELETE | `/api/conversations/{id}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| GET | `/api/tasks/{id}/chat/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| POST | `/api/tasks/{id}/chat/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| DELETE | `/api/tasks/{id}/chat/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| GET | `/api/tasks/{id}/intents/{iid}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| POST | `/api/tasks/{id}/intents/{iid}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |
| DELETE | `/api/tasks/{id}/intents/{iid}/side-questions` | `handleSideQuestions` server/side_questions.go:276(loop) | side_questions.go:276 |

---

## 二、ARTEX 关键机制五件 + 流量录制（每件：链路+执法点+表）

### 2.1 任务调度怎么转（两层：任务准入 FIFO + 任务内 planner/worker 双循环）

**任务准入层**：`Scheduler.Run`（server/scheduler.go:41-58）5 秒 tick→`reconcileConcurrency`（server/goals.go:253-330）：启用并发上限时，LLM 链不可用的运行任务**停车回队列**（释放槽位，llm_unavailable_queued）；队列按 queued_at FIFO（回退按单调任务 id）补位启动空槽；`startTaskEngine` 先过操作准入（beginTaskOperation）再 `engine.Run`。建任务`createTask`（server/server.go:1462-1535）：校验 LLM 档案存在且带 key→关联任务去重（≤MaxTaskSourceCount）→企业归一→任务级拦截规则→`tasks`+`explorations`+`task_relations`+`task_llm_profiles`+`task_intercept_rules`→`launchTask` 异步（种子意图+engine.Run，与 spawn_task 工具共用一段）。

**任务内执行层**：`Engine.Run`（server/engine.go:748-778）起 1 个 plannerLoop + N 个 workerLoop（N=m.Workers()）+ 超时协调器。plannerLoop（engine.go:800-914）：唤醒源=边沿（worker 完成/发现/kill/resume/种子）+心跳（默认 600s 下限）；每轮先 debounce 合并，再过六道门（未配 LLM/用户暂停/删除中/终态/超时收尾中/goalless 纯 Go 收尾）；`planner.Plan` 拿 drainTriggers 的事件决定意图增删，判定目标达成→任务落 done+cancelExec(AbortGoalMet) 杀在跑 worker。workerLoop（engine.go:916-963）：轮询 `claimNext`（engine.go:1237-1244）→`Frontier(20)` 取 open 意图→`ClaimIntent`（db/exploration.go:1173-1181，**CAS**：`UPDATE exploration_nodes SET state='running' WHERE kind='intent' AND state='open'`）→`runIntent`（engine.go:982-，单意图全生命周期：准入持锁防 delete 观察到静默、per-work 子 context 支持 kill_work、steer 钩子注入中途纠偏、终态写回唯一入口）。**没有中心调度器排队意图——frontier 抢占式认领就是调度**。

### 2.2 Agent 会话怎么跑（任务三件套 + 平台会话 + 触发器会话）

**任务三件套**：Planner（规划，agent/planner.go）/ Worker（执行，agent/worker.go）/ MainAgent（任务主聊，agent/mainagent.go）都架在 **norma**（仓内 vendored 的 Agent Harness SDK：流式工具循环/hook/权限/compaction/subagent，norma/README）之上；server 侧经 `agentsForTask` 解析（任务级档案→全局），`SetProxy` 注入录制代理（task_llm.go:571-595）。每工具调用过 guard 钩子（见§2.5），LLM 调用过 llmrec 录制装饰器+llmpool 故障转移链。
**平台会话**：`pgSendConversationMessage`（server/conversations.go:388）→`runConversation`（:465，goroutine）→`runConversationTurn`（:496-）：busy 锁防同会话并发；LLM 解析优先级=会话 agent 自身绑定→会话 pin→全局；per-agent maxTurns/maxDuration；每步 emit 落 `conversation_activities`。**触发器会话**：`agent_triggers` 六类事件（interval/finding/goal/task_timeout/task_create/tool_call）由 Scheduler.step（scheduler.go:117-）5s 轮询水位线（scheduler_state 表存 lastFinding/firedGoals/lastTimeout/lastToolCall/lastTaskCreate）→`StartTriggeredRun`（conversations.go:610）→按 agent 配置 merge/queue 串行（pumpLocked）→自动起会话（如 reporter 收 report_finding 事件自动写报告）。

### 2.3 发现怎么入库·有没有验证门（硬门=上下文一致性；技术验证=提示词铁律+报告 Agent 复核，无非 LM 漏洞闸）

入口=worker 写工具 `report_finding`（agent/tools.go:1220-1293）：① 硬门1：无任务上下文直接拒（tools.go:1239，平台对话必须走 add_task_hint 交接）；② 硬门2：evidence_hint_id 必须有效且不得引用继承提示/他人提示（findingRefsFromHint）；③ 流量绑定关则剥掉 evidence 参数照常入库（不为缺包丢确认漏洞）。落库=`evidence.Store.Record`（evidence/store.go:182-194）单事务：任务级证据锁→流量引用 prepare（NormalizeTrafficRefs→traffic 库读原文→sha256 内容寻址快照 traffic_evidence_snapshots）→`RecordFindingTx`（db/finding_traffic.go:342-409）：**再两道硬门**——任务/探索归属匹配（:347-353）+ intent_id 必须是本任务意图（:355-363，继承只读）→同一事务写 4 处：探索节点（kind=finding,state=confirmed,priority=9）+anchors+edges(intent YIELDS finding)+独立 `findings` 行+**通知事件**（提交即保证漏洞落库与推送入队原子一致，:385-392）→自动绑定流量。**技术验证门=提示词级**：promptcatalog.go:55 铁律「只有真实触发拿到可复现证据才上报；严禁版本/CVE 匹配、补丁对比、外部漏洞库推断；触发不了标存疑不硬记」；入库后 reporter Agent 由工具调用事件自动唤起（promptcatalog.go:73-82）核对 traffic_search/traffic_get 再写报告（挖洞与报告分离）。状态机（pending/in_progress/confirmed/resolved/fixed/false_positive/duplicate/ignored/risk_accepted，db/findings.go:53）由人驱动 PATCH。severity 四级枚举（db/findings.go:71）。

### 2.4 复测怎么触发（独立 retester 会话+结论封存+fixed 才改状态）

`POST /api/exploration/findings/{id}/retests`→`startFindingRetest`（server/finding_retests.go:61-129）：五道前置门=发现存在/retester agent 启用/两个专属工具（get_finding_retest_context+record_finding_retest_result）启用且绑定/聊天引擎可用/服务未停→`CreateFindingRetest`（db/finding_retests.go:77，幂等：已有 active 复测不新建，返回 created=false）→占用 busy 锁→`runConversation` 以 `InitialMessage` 起独立会话。会话特例（conversations.go:496-）：首轮才执行历史复测；`StartFindingRetest` CAS 落 running；两个工具**从服务端会话上下文取 finding**（intercept.ConvIDFromContext），工具参数无法把结论写到别的漏洞（finding_retests.go:133 注释）。`record_finding_retest_result`：verdict 枚举 reproduced/fixed/inconclusive 硬校验+summary/evidence 非空+长度闸（db/finding_retests.go:183-203），**幂等**（同值重写允许，改值拒绝）。收尾=`FinishFindingRetest`（db/finding_retests.go:210-）：取消/失败优先于已暂存结论（中断的复测不可能显示已修复）；**只有新完成的 fixed 在同事务更新漏洞分诊状态**。原证据与报告保持不变（复测=不可变历史记录）。

### 2.5 审批怎么执法（guard PreToolUse 钩子=唯一执法点；规则→LLM 裁判→人工三层）

每个 agent 会话挂 `guard.Hooks()`（guard/guard.go:58-63），**每次工具调用必过 PreToolUse**（guard.go:65-83）→`applyIntercept`（guard.go:85-127）：① 工具不在拦截清单（intercept tool-config）→放行；② `Interceptor.Match`（intercept/intercept.go:508）按优先级匹配全局规则（正则匹配工具名+完整入参；任务级/资产级规则同构，asset_intercept_match.go 对资产类工具匹配目标归属）→**deny**=拦截并向模型返回「【ARTEX 平台管控·非目标防御】」框架消息（guard.go:129-140，防止渗透 agent 把平台拦截当 WAF 去绕）；**allow**=放行留痕；**ask**=人工审批；③ 无规则命中→LLM 兜底裁判 `Judge`（intercept.go:429，低温度 1024 token 单轮 JSON 裁决，judge 车道独立计费 llm_usage；fail_action=allow/ask/deny，intercept.go:385-427 配置闸）。**ask 的阻塞实现**=`HandleAsk`（intercept.go:584-669）：`intercept_pending` 落行→内存 channel 注册（防 decide/注册竞态：注册后重读一次 DB）→向会话流/任务活动流发内联审批卡→`select` 阻塞在 channel/超时/ctx；人工 `POST /api/intercept/pending/{id}/decide`（server/intercept.go:353-371）→`Decide`（intercept.go:671）唤醒；超时按 ask_timeout_action 兜底；ctx 取消=拒+记 not_executed。放行后执行结果回写 `CompleteIntercept`（/api/intercept/history/{id}/execution 可查执行回执）。PostToolUse=Observer/G5 失败归因（Bash 结果正则分 blocked/error/ok，guard.go:141-160，喂 planner 换策略）。

### 2.6 流量录制（内嵌 mitm 代理，全量明文，Agent 出网默认走它）

`traffic.Open`（traffic/traffic.go:176）=内嵌 go-mitmproxy：sink addon 的 Response/RequestError 钩子把**每个目标 HTTP 交换**写人类可读文件树+侧车 SQLite 索引（exchanges/exchange_bodies/blob_refs 三表+可选 FTS5 trigram 全文检索，traffic.go:30-73；代理自身故障时 passthrough 放行不拦目标，:408-434）。接线：manager 启动代理（manager.go:403）→`SetProxy` 注入四类 agent（task_llm.go:571/582/595, server.go:473/614）→**Bash 子命令默认 HTTP_PROXY+信任 _ca CA**（agent/planner.go:426 等三处 proxyEnv）+WebFetch 走 WebFetchProxy+自定义工具出网走代理（customtool.go:465）。消费面=traffic_search/traffic_get/traffic_blob 工具（轻量索引→分页→按 id 取原文）+ /api/traffic 回看七条+发现证据绑定（§2.3）。证据独立于易失流量：绑定即快照（内容寻址 sha256+24h GC 宽限），流量删除不毁证据。

### 2.7 顶层目录逐个一句话（它们暴露什么能力）

| 目录 | 一句话 |
|---|---|
| `agent/` | 真实 LLM 驱动的 Planner/Worker/MainAgent/ChatAgent 四件套+工具目录（report_finding/流量证据/黑板继承），架在 norma SDK 上（agent/provider.go:1-6）。 |
| `llmpool/` | LLM 故障转移装饰器：按档案优先级走链，欠费/限流/宕机自动切下一个，全进程共享一条链+一个熔断器（llmpool/health.go:1-6）。 |
| `guard/` | 安全边界层：审计环+拦截规则求值+Observer 失败归因，每次工具调用必过（guard/guard.go:1-8）——审批执法点。 |
| `intercept/` | 可配置工具拦截内核：DB 规则缓存按优先级求值，allow/deny/ask 三动作+LLM 兜底裁判+待决阻塞 channel（intercept/intercept.go:1-9）。 |
| `traffic/` | 内嵌 mitm 录制代理：全量明文抓目标 HTTP 入文件树+SQLite 索引（traffic/traffic.go:1-4）。 |
| `report/` | 从探索图渲染确认漏洞 Markdown 交付报告（report/report.go:1-3）。 |
| `evidence/` | 发现证据保全库：流量引用原子转内容寻址快照，独立于易失流量（evidence/store.go:1-2）。 |
| `enrich/` | 非 AI 资产自动补全：dnsx 解析+HTTP 探测（走录制代理）回写资产图建 IP/端口节点（enrich 包头注释）。 |
| `notify/` | IM/邮件推送叶子包：渠道适配+签名+截断，不识库不识 server（notify/notify.go:1-8）。 |
| `skills/` | 技能包文件系统：api-recon/playwright-cli/scopesentry 三包，经 /api/skills CRUD+metered 使用量。 |
| `mcphttp/` | 远程 MCP 客户端：Streamable HTTP/SSE 传输适配为 CoreTool（mcphttp/client.go:1-6）。 |
| `llmrec/` | LLM Provider 录制装饰器：全量请求/响应落 PostgreSQL（llmrec/llmrec.go:1-4）。 |
| `norma/` | 仓内 vendored 通用 Agent Harness SDK（Go）：流式工具循环/hook/权限/compaction/subagent/技能/转录（norma/README）。 |
| `sidequestion/` | 主 Agent 不可变检查点捕获：对冻结快照提问，不拥有会话不碰执行器（sidequestion/capture.go:1-3）。 |
| （其余） | `db/`=PG 持久层 50 表+种子；`selfupdate/`=页面一键更新带保险；`server/`=HTTP 面 261 路由；`web/`=Next.js 前端（webui_embed 单二进制嵌入）。 |

---

## 三、CSAI 产品面（同口径：链补充；289 路由全表引用旧档）

> 路由全表**不重列**：见 `docs/research/2026-10-20-csai-full-capability-inventory.md`§1（app.go:706-1492 全部 289 条带行号）。本节只补旧账没有的东西：关键接口的**业务链（handler→表→逻辑）**与产品概念语言。

### 3.1 产品核心概念（目录=产品语言）

| 目录 | 产品语言 |
|---|---|
| `agents/`（16 个 .md） | **攻击阶段子代理目录**：3 主代理（orchestrator / orchestrator-plan-execute / orchestrator-supervisor）+13 攻击相位代理（recon、intel-collection、engagement-planning、attack-surface-enumeration、penetration、privilege-escalation、lateral-movement、persistence-maintenance、opsec-evasion、impact-exfiltration、cleanup-rollback、reporting-remediation、vulnerability-triage）；frontmatter（kind/id/description/tools/max_iterations）由 internal/agents 加载器与 YAML 角色合并成 EffectiveSubAgents。 |
| `cmd/`（5 个二进制） | `server`=主服务；`mcp-stdio`=把整平台暴露为 stdio MCP 服务器（产品=「安全工具箱即 MCP」）；test-* 三个=测试配套。 |
| `internal/`（39 包） | 产品发动机舱：multiagent（Eino ADK 编排 28K LOC）、security（Executor：90 YAML 工具→命令行组装→os/exec）、mcp（ExecutionService worker 化执行+断路器）、hitl（Jev TypeSafe 审计）、c2、processguard、toolguard、tooloutput、workflow、knowledge、project（事实黑板）等（逐包一句话见旧档§2）。 |
| `knowledge_base/` | RAG 种子语料目录（SQL Injection / Prompt Injection 两卷），由 `POST /api/knowledge/scan`→`ScanKnowledgeBase`（internal/knowledge/manager.go:35）目录扫描入库→Eino 向量索引。 |
| `mcp-servers/` | 随包外挂 MCP 服务：pent_claude_agent、reverse_shell——「平台工具不够就挂 MCP」的联邦面。 |
| （配套）roles/ 14 YAML | 角色=user_prompt 前置+tools 白名单过滤（产品=「角色即提示词+工具面」）。tools/ 90 YAML=安全工具目录；skills/ 24 包=渐进披露技能。 |

### 3.2 关键接口链（handler→表→逻辑，旧账只有路由名的补链）

- **会话执行**：`POST /eino-agent(/stream)`→`EinoSingleAgentLoop(Stream)`（internal/handler/eino_single_agent.go:22/431）：Eino ADK ChatModelAgent+Runner 流式工具循环；消息/过程详情落 `messages`/`process_details`（错误/超时原地 UPDATE messages，:182/:364）；HITL 经 `interceptHITLForEinoTool`（hitl.go:923）拦截工具调用。`POST /multi-agent(/stream)`=Eino 多代理（deep/plan_execute/supervisor）+checkpoint 恢复。
- **批量任务**：`POST /batch-tasks/:queueId/start`→BatchTaskManager：**内存互斥锁+DB-first 双层**（loadQueueFromDB 恢复，batch_task_manager.go:302/539）；`ClaimNextPendingTask`（:1215-1240）mutex 内取首个 pending 改 running（FIFO+单跑例外）；`TryMarkQueueExecutor`（:135）双层防护防双执行器；队列状态机+定时（UpdateQueueSchedule cron）。
- **漏洞与复测**：`POST /vulnerabilities`→`CreateVulnerability`（internal/handler/vulnerability.go:59）：RBAC 会话/项目归属校验+外键存在性校验→`vulnerabilities` 表→资源属主绑定+NotifyVulnerabilityCreated。`POST /vulnerabilities/:id/retest`→`CreateRetest`（vulnerability_retest.go:14）：**复测=拉源会话分支**——五重权限（chat:read/write+agent:execute+vulnerability:write+资源级 RBAC）→源会话必须空闲→`CreateVulnerabilityRetest` 建分支会话+占位符解析+`SetVulnerabilityRetestPrompt`；分支跑普通 agent 循环（复测会话 roleTools 强制追加 get/update vulnerability 工具），不是独立复测 Agent。
- **HITL 审批**：`waitHITLApproval`（internal/handler/hitl.go:624）：`shouldInterrupt`（会话级配置+全局工具白名单合并，:314/336）→`CreatePendingInterrupt` 落 `hitl_interrupts` 表→reviewer=audit_agent 时走 **Jev TypeSafe 审计 LLM 裁决**（拒绝阈值 0.55，直接 UPDATE decided，:675-678）否则等人工 `POST /hitl/decision`；事件双写 SSE 流+process_details。
- **执行监控**：`GET /monitor*`→`loadExecutions`（monitor.go:202）读 `tool_executions`（ExecutionService 落库：worker 化执行+execution_id 有界等待+get/wait 轮询续接+取消+断路器+统一输出上限）；`monitor orphaned 对账`把无协程 running 记录取收拾尾。
- **C2 面**：34 条路由→internal/c2：listener CRUD+start/stop 起 HTTP/TCP/WS beacon 路由（每 HTTP listener 5 条动态 mux 路径，c2/listener_http.go:93-97）→sessions 看门狗→tasks 队列+wait 轮询→payloads oneliner/build→events SSE。
- **知识库**：13 条→internal/knowledge：scan 目录入库→index Eino 向量索引→search 检索链（改写→向量→HTTP rerank→后处理）+retrieval-logs 回写。

---

## 四、两家并排（机制对照 + 各自独有的面）

### 4.1 机制对照表

| 机制 | ARTEX | CSAI |
|---|---|---|
| 任务调度 | 任务=探索图工作流：准入 FIFO 并发帽（goals.go:253）+任务内 planner/worker 双循环，**意图=图节点 CAS 认领**（exploration.go:1173），无中心队列 | 任务=会话：批量队列 FIFO+并发帽+mutex 领取（batch_task_manager.go:1215），ClaimNextPendingTask 原子但**队列与状态解耦双层防护** |
| Agent 会话 | 三件套（Planner/Worker/Main）+平台会话+触发器会话，全架自研 norma SDK；每任务独立图黑板 | 单代理（Eino ADK）+多代理（deep/plan_execute/supervisor）+16 攻击相位子代理；会话=产品原子，checkpoint 恢复 |
| 发现入库验证门 | 工具级硬门（任务上下文+intent 归属）+**提示词铁律**（真实触发才报）+报告 Agent 自动复核+证据=流量快照原子绑定 | 会话产物：人工/agent 写 vulnerabilities（外键校验+RBAC）；验证纪律=pentest-verification 技能包提示词级+agentfinalizer 最终答案裁决器 |
| 复测 | 独立 retester Agent 会话+双专属工具+结论封存（幂等+中断优先）+fixed 才改状态（finding_retests.go 全链） | 源会话拉分支+复测提示词模板+roleTools 强制追加漏洞读写工具（vulnerability_retest.go:14） |
| 审批执法 | guard PreToolUse 唯一执法点：规则→LLM 裁判→人工三层，pending 行+channel 阻塞+超时策略+执行回执，deny 带「平台管控非目标防御」反绕过框架 | HITL 17 条路由：会话级配置+工具白名单+Jev 审计 agent（阈值 0.55）+人工决定；toolguard=名称/参数正则阻断（自认不做 host 解析） |
| 流量录制 | 内嵌 mitm 代理**默认全量录**（Bash/WebFetch/自定义工具出网都走它）+侧车 SQLite+FTS+证据快照独立保全 | 无流量录制面（terminal/webshell/C2 提供观测，但无 HTTP 交换级录制与证据绑定） |
| 规模 | 261 路由/50 PG 表/3 sidecar 表；单文件路由 243 条集中注册 | 289 路由/36+ SQLite 领域表；路由全集中 app.go 单文件 |

### 4.2 各自独有的面

**ARTEX 独有**：流量录制+证据链（mitm 录制→traffic_search 核实→角色化绑定→版本化快照→报告按证据版本写）；探索图可视化（frontier/graph/lineage/coverage）；发现复测独立 Agent；任务级/资产级/全局三层拦截规则+LLM 兜底裁判；LLM 故障转移池+judge 独立计费车道；边问（冻结检查点旁路提问）；ScopeSentry 资产同步；企业多租户 scope；自更新保险；技能缺失统计（飞轮信号）；planner 心跳+goalless 收尾+任务超时协调器。
**CSAI 独有**：内置 C2 框架（listener/beacon/payload/profile/事件流 34 条）；WebShell 管理（10 条）；攻击链构建+提升为项目；项目事实黑板（fact-graph/edges CRUD）；RAG 知识库（向量索引+rerank+检索日志）；90 YAML 工具+Executor+执行韧性件（worker 化/断路器/spill/轮询续接）；图工作流引擎（19 条，checkpoint/dry-run/LLM 草稿）；OS 级 processguard；8 IM 平台机器人；终端直通/WebSocket；RBAC 多用户资源所有权（ARTEX 单管理员）；FOFA/Shodan/ZoomEye/Quake 四资产引擎；平台自身暴露为 MCP 服务器+mcp-servers 联邦；审计保留期/脱敏/导出。

---

## 五、报账

- 路由数：ARTEX **261**（本档§一全表，243+7+9+2 注册处可查）；CSAI **289**（旧档§1，本档不重列）。
- 关键机制五件+流量：ARTEX 调度（§2.1）/会话（§2.2）/发现门（§2.3）/复测（§2.4）/审批（§2.5）/流量（§2.6），CSAI 对应面见§3.2 与§4.1 对照。
- 两家并排结论：ARTEX=**单管理员深耕渗透工作流**（图调度+证据链+三层审批+全量录制）；CSAI=**多用户攻击平台**（C2/WebShell/RAG/工作流/RBAC 广度）。交集最小处=复测与审批两家都有但形态迥异（独立 Agent vs 会话分支；三层规则+裁判 vs 白名单+Jev）；ARTEX 独有的证据-流量-报告闭环与 CSAI 独有的执行韧性件，是彼此最值得抄的两块。

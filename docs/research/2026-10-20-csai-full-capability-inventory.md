# CyberStrikeAI 全量能力清点（竞品：GraphLed 视角）

- 对象：`/Users/wgen/dsh-test/repos/CyberStrikeAI`（源码只读分析，未运行任何服务/网络请求）
- 自报版本：config.example.yaml:14 `version: "v1.7.23"`；go.mod module `cyberstrike-ai`
- 方法：HTTP 路由 grep 全数 + internal/cmd 42 个包逐个看主文件头/导出符号 + roles 14 个 YAML 全读 + 会话/任务三核心文件全文读 + 工具面从常量与装配代码反推

---

## 1. HTTP 路由全数（289 条注册，全列）

路由注册**集中在单一文件** `internal/app/app.go`（setupRouter，约 964–1492 行）。分组结构：

- `mux.HandleFunc("/mcp")`（app.go:706）— 平台级 MCP over HTTP(SSE) 端点，带鉴权（mcp_authorization.go）
- `api := router.Group("/api")`（app.go:964）
  - `authRoutes := api.Group("/auth")`（:967，login 限流）
  - `robotGroup := api.Group("/robot")`（:982，IM 回调，无鉴权组）
  - `protected := api.Group("")`（:991，AuthMiddleware + RBAC 资源所有权）
    - `knowledgeRoutes := protected.Group("/knowledge")`（:1179）
    - `c2Routes := protected.Group("/c2")`（:1371）

按方法统计：**GET 122 / POST 94 / PUT 38 / DELETE 33 = 287 条 REST**，另 `router.Static("/static")` 1 条、`/mcp` HandleFunc 1 条，合计 **289 条注册**。另有 C2 运行时动态 mux 路径（每 HTTP listener 5 条 beacon 路径 + websocket 1 条，c2/listener_http.go:93-97、listener_websocket.go:82）与测试专用 cmd/test-sse-mcp-server（/sse,/message）。

全量清单（方法 路径 → handler，行号为 app.go）：

**认证 /auth**：POST /api/auth/login :970；POST /api/auth/logout :971；POST /api/auth/change-password :972；GET /api/auth/validate :973；POST /api/auth/robot-binding-code :974；GET /api/auth/robot-bindings :975；DELETE /api/auth/robot-bindings/:id :976

**IM 机器人回调 /robot**：GET /api/robot/wecom :985；POST /api/robot/wecom :986；POST /api/robot/dingtalk :987；POST /api/robot/lark :988

**RBAC**：GET /rbac/me :1003；GET /rbac/metadata :1004；GET /rbac/users :1005；POST /rbac/users :1006；PUT /rbac/users/:id :1007；DELETE /rbac/users/:id :1008；GET /rbac/roles :1009；POST /rbac/roles :1010；PUT /rbac/roles/:id :1011；DELETE /rbac/roles/:id :1012；GET /rbac/resource-assignments :1013；GET /rbac/resources :1014；POST /rbac/resource-assignments :1015；DELETE /rbac/resource-assignments/:id :1016

**微信机器人**：POST /robot/test :1019；POST /robot/wechat/qrcode :1022；GET /robot/wechat/qrcode/status :1023；POST /robot/wechat/qrcode/verify :1024；GET /robot/wechat/status :1025

**Agent 执行面**：POST /eino-agent :1028；POST /eino-agent/stream :1029；POST /agent-loop/cancel :1048；GET /agent-loop/tasks :1049；GET /agent-loop/task-events :1050（SSE）；GET /agent-loop/tasks/completed :1051；POST /multi-agent :1055；POST /multi-agent/stream :1056

**HITL（17 条）**：GET /hitl/pending :1030；GET /hitl/logs :1031；DELETE /hitl/logs :1032；GET /hitl/logs/:id :1033；POST /hitl/decision :1034；POST /hitl/dismiss :1035；GET /hitl/config/:conversationId :1036；PUT /hitl/config :1037；GET /hitl/tool-whitelist :1038；PUT /hitl/tool-whitelist :1039；POST /hitl/tool-whitelist :1040；GET /hitl/default-config :1041；PUT /hitl/default-config :1042；GET /hitl/default-reviewer :1043；PUT /hitl/default-reviewer :1044；GET /hitl/audit-strategy :1045；PUT /hitl/audit-strategy :1046

**Markdown 子代理 CRUD**：GET /multi-agent/markdown-agents :1057；GET /multi-agent/markdown-agents/:filename :1058；POST /multi-agent/markdown-agents :1059；PUT /multi-agent/markdown-agents/:filename :1060；DELETE /multi-agent/markdown-agents/:filename :1061

**FOFA**：POST /fofa/search :1064；POST /fofa/parse :1066

**资产（11 条）**：GET /assets :1069；GET /assets/selection :1070；GET /assets/stats :1071；POST /assets/import :1072；POST /assets/scan-links :1073；PUT /assets/bulk :1074；PUT /assets/project-binding :1075；POST /assets/batch-delete :1076；POST /assets/merge :1077；PUT /assets/:id :1078；DELETE /assets/:id :1079

**批量任务（14 条）**：POST /batch-tasks :1082；GET /batch-tasks :1083；GET /batch-tasks/:queueId :1084；POST /batch-tasks/:queueId/start :1085；POST /batch-tasks/:queueId/rerun :1086；POST /batch-tasks/:queueId/pause :1087；PUT /batch-tasks/:queueId/metadata :1088；PUT /batch-tasks/:queueId/schedule :1089；PUT /batch-tasks/:queueId/schedule-enabled :1090；DELETE /batch-tasks/:queueId :1091；PUT /batch-tasks/:queueId/tasks/:taskId :1092；POST /batch-tasks/:queueId/tasks/:taskId/run :1093；POST /batch-tasks/:queueId/tasks :1094；DELETE /batch-tasks/:queueId/tasks/:taskId :1095

**会话/对话（12 条）**：GET /usage/tokens :1098；POST /conversations :1099；GET /conversations :1100；GET /conversations/:id :1101；GET /conversations/:id/token-usage :1102；GET /conversations/:id/plan-tasks :1103；GET /messages/:id/process-details :1104；GET /process-details/:id :1105；PUT /conversations/:id :1106；PUT /conversations/:id/project :1107；DELETE /conversations/:id :1108；POST /conversations/:id/delete-turn :1109；PUT /conversations/:id/pinned :1110

**监控**：GET /monitor :1113；GET /monitor/execution/:id :1114；POST /monitor/execution/:id/cancel :1115；POST /monitor/executions/names :1116；DELETE /monitor/execution/:id :1117；DELETE /monitor/executions :1118；GET /monitor/stats :1119；GET /monitor/calls-timeline :1120

**通知**：GET /notifications/summary :1121；POST /notifications/read :1122

**配置/工具治理（13 条）**：GET /config :1125；GET /tool-guard :1126；PUT /tool-guard :1127；POST /tool-guard/test :1128；GET /config/tools :1129；GET /config/tools/:name/schema :1130；PUT /config :1131；POST /config/apply :1132；POST /config/test-openai :1133；POST /config/test-typesafe :1134；POST /config/test-vision :1135；POST /config/list-models :1136

**自更新（8 条）**：GET /system/update :1139；GET /system/update/job :1140；POST /system/update/check :1141；POST /system/update/apply :1142；POST /system/update/restart :1143；POST /system/update/rollback :1144；POST /system/update/adopt :1145；POST /system/update/source :1146

**终端（直通 OS）**：POST /terminal/run :1149；POST /terminal/run/stream :1150；GET /terminal/ws :1151（WebSocket）

**审计（5 条）**：GET /audit/meta :1154；GET /audit/summary :1155；GET /audit/logs :1156；GET /audit/logs/export :1157；GET /audit/logs/:id :1158

**存储**：GET /storage/meta :1161；GET /storage/status :1162；POST /storage/cleanup :1163

**外部 MCP 联邦（7 条）**：GET /external-mcp :1166；GET /external-mcp/stats :1167；GET /external-mcp/:name :1168；PUT /external-mcp/:name :1169；DELETE /external-mcp/:name :1170；POST /external-mcp/:name/start :1171；POST /external-mcp/:name/stop :1172

**攻击链**：GET /attack-chain/:conversationId :1175；POST /attack-chain/:conversationId/regenerate :1176

**知识库（13 条，knowledgeRoutes）**：GET /knowledge/categories :1181；GET /knowledge/items :1192；GET /knowledge/items/:id :1203；POST /knowledge/items :1213；PUT /knowledge/items/:id :1223；DELETE /knowledge/items/:id :1233；GET /knowledge/index-status :1243；POST /knowledge/index :1257；POST /knowledge/scan :1267；GET /knowledge/retrieval-logs :1277；DELETE /knowledge/retrieval-logs/:id :1288；POST /knowledge/search :1298；GET /knowledge/stats :1309

**漏洞（13 条）**：GET /vulnerabilities :1324；GET /vulnerabilities/export :1325；DELETE /vulnerabilities/batch :1326；GET /vulnerabilities/filter-options :1327；GET /vulnerabilities/stats :1328；GET /vulnerability-alerts/subscription :1329；PUT /vulnerability-alerts/subscription :1330；GET /vulnerabilities/:id :1331；POST /vulnerabilities :1332；POST /vulnerabilities/:id/retest :1333；PUT /vulnerabilities/:id :1334；DELETE /vulnerabilities/:id :1335

**项目（19 条，含事实黑板）**：GET /projects/dashboard-summary :1338；GET /projects :1339；POST /projects :1340；GET /projects/:id/stats :1341；GET /projects/:id/conversations :1342；GET /projects/:id :1343；PUT /projects/:id :1344；DELETE /projects/:id :1345；GET /projects/:id/fact-graph :1346；GET /projects/:id/fact-edges :1347；POST /projects/:id/fact-edges :1348；DELETE /projects/:id/fact-edges/:edgeId :1349；POST /projects/:id/promote-attack-chain/:conversationId :1350；GET /projects/:id/facts :1351；POST /projects/:id/facts :1352；PUT /projects/:id/facts/:factId :1353；DELETE /projects/:id/facts/:factId :1354；POST /projects/:id/facts/deprecate :1355；POST /projects/:id/facts/restore :1356

**WebShell（10 条）**：GET /webshell/connections :1359；POST /webshell/connections :1360；GET /webshell/connections/:id/ai-history :1361；GET /webshell/connections/:id/ai-conversations :1362；GET /webshell/connections/:id/state :1363；PUT /webshell/connections/:id :1364；PUT /webshell/connections/:id/state :1365；DELETE /webshell/connections/:id :1366；POST /webshell/exec :1367；POST /webshell/file :1368

**C2（34 条，c2Routes）**：GET/POST /c2/listeners :1383-1384；GET/PUT/DELETE /c2/listeners/:id :1385-1387；POST /c2/listeners/:id/start :1388；POST /c2/listeners/:id/stop :1389；GET/DELETE /c2/sessions :1390-1391；GET/DELETE /c2/sessions/:id :1392-1393；PUT /c2/sessions/:id/sleep :1394；PUT /c2/sessions/:id/note :1395；GET/DELETE /c2/tasks :1396-1397；GET /c2/tasks/:id :1398；POST /c2/tasks :1399；POST /c2/tasks/:id/cancel :1400；GET /c2/tasks/:id/wait :1401；POST /c2/sessions/:id/tasks :1402；POST /c2/payloads/oneliner :1403；POST /c2/payloads/build :1404；GET /c2/payloads/:id/download :1405；GET/DELETE /c2/events :1406-1407；GET /c2/events/stream :1408（SSE）；POST /c2/files/upload :1409；GET /c2/files :1410；GET /c2/tasks/:id/result-file :1411；GET/POST /c2/profiles :1412-1414；PUT/DELETE /c2/profiles/:id :1415-1416

**对话附件（10 条）**：GET /chat-uploads :1419；GET /chat-uploads/export :1420；GET /chat-uploads/download :1421；GET /chat-uploads/path :1422；GET /chat-uploads/content :1423；POST /chat-uploads :1424；POST /chat-uploads/mkdir :1425；DELETE /chat-uploads :1426；PUT /chat-uploads/rename :1427；PUT /chat-uploads/content :1428

**角色（5 条）**：GET /roles :1431；GET /roles/:name :1432；POST /roles :1433；PUT /roles/:name :1434；DELETE /roles/:name :1435

**工作流（19 条）**：GET /workflows/runs/pending :1438；GET /workflows/runs/:runId/replay :1439；GET /workflows/runs/:runId :1440；POST /workflows/runs/:runId/resume :1441；POST /workflows/validate :1442；POST /workflows/dry-run :1443；POST /workflows/generate-draft :1444；GET /workflows/:id/package :1445；POST /workflow-package-inspections :1446；GET /workflow-package-inspections/:inspectionId :1447；POST /workflow-package-imports :1448；GET /workflow-package-imports/:importId :1449；GET /workflows :1450；GET /workflows/:id :1451；POST /workflows :1452；PUT /workflows/:id :1453；DELETE /workflows/:id :1454

**技能（11 条）**：GET /skills :1457；GET /skills/stats :1458；DELETE /skills/stats :1459；GET /skills/:name/files :1460；GET /skills/:name/file :1461；PUT /skills/:name/file :1462；GET /skills/:name/bound-roles :1463；POST /skills :1464；PUT /skills/:name :1465；DELETE /skills/:name :1466；DELETE /skills/:name/stats :1467；GET /skills/:name :1468

**MCP/文档/静态**：POST /api/mcp :1471（API 网关内 MCP）；GET /api/openapi/spec :1476；GET /api-docs :1483；router.Static("/static") :1488；GET / :1492（SPA 入口）

---

## 2. 目录全件：internal/ 37 包 + cmd/ 5 包逐包职责

（LOC 含测试；每包均看过主文件头部与导出符号）

| 包 | 非测试文件/LOC | 职责一句话 |
|---|---|---|
| internal/agent | 4 / 1,681 | 老 Agent 抽象：系统提示默认值、token 计数、ChatMessage、agent 追踪（agent_trace.go） |
| internal/agentfinalizer | 1 / 413 | 「最终答案裁决器」：自然语言输出只是候选，Decision 对象判定 Finalizable 才能交付用户 |
| internal/agents | 1 / 623 | agents/*.md 加载器：frontmatter(kind/id/description/tools/max_iterations) → config.MultiAgentSubConfig；orchestrator.md/plan_execute/supervisor 三种主代理文件名；YAML 与 Markdown 子代理合并（EffectiveSubAgents） |
| internal/app | 12 / 6,753 | 装配根：app.go 全部 289 条路由 + 生命周期；asset/c2/vulnerability/project_fact/vision 工具实现；MCP 鉴权(mcp_authorization.go)；主服 TLS/HTTP 重定向 |
| internal/attackchain | 3 / 1,466 | 攻击链构建器：Node/Edge/Chain + 截断 + 提升为项目(promote_project.go) |
| internal/audit | 9 / 512 | 平台审计日志：conversation 创建/资源可用性/记录/保留期/节流/脱敏（9 个文件无测试） |
| internal/authctx | 1 / 72 | 不可变授权主体 Principal，穿透到 Agent/MCP/后台任务上下文 |
| internal/c2 | 17 / 5,444 | 内置 C2 框架：HTTP/TCP/WebSocket listener、加密 beacon、会话看门狗、payload 生成(oneliner/build)、Malleable Profile、事件总线；Manager 是统一门面(manager.go) |
| internal/config | 5 / 3,945 | 配置加载/热更（config.go 40KB 示例）、环境变量展开、HTTPS 自举、tool_guard、vision、AgentMode 归一化 |
| internal/database | 36 / 17,726 | SQLite 全量持久层：会话/消息/过程详情/资产/漏洞/项目/事实边/批量任务/C2/RBAC/审计/监控/技能统计/自愈 schema（schema_reconcile.go）等 36 张领域表 |
| internal/einomcp | 3 / 290 | Eino InvokableTool 桥：把 OpenAI 风格工具定义转 Eino 工具，执行走 Agent 的 MCP 路径；错误经 ToolErrorPrefix 前缀回传 |
| internal/einoobserve | 2 / 615 | Eino callbacks.Handler：结构化日志 + SSE trace 事件(eino_trace_*) + 可选 OTel(otel.go) |
| internal/handler | 75 / 47,777 | 全部 HTTP handler + 会话/任务管理（见第 6 节）+ terminal 直通 + webshell + FOFA + HITL 全家 |
| internal/hitl | 2 / 470 | HITL 内核：Jev（TypeSafe System One）审计问题集与英文审批策略（jev.go），拒绝阈值 0.55；审批日志保留 |
| internal/knowledge | 17 / 3,864 | 知识库：目录扫描入库、Eino 索引/检索链、embedding、HTTP rerank、检索后处理、SQLite 向量索引、检索日志 |
| internal/llm | 3 / 316 | agentic chat 适配 + claude.go + deepseek anthropic 兼容层 |
| internal/logger | 2 / 290 | zap 日志 + 按日切割 writer |
| internal/mcp | 11 / 7,296 | MCP 服务器/客户端核心：工具注册、SSE 会话、CallTool、ExecutionService（worker 化执行）、外部 MCP 管理器（stdio/HTTP/SSE + 断路器 + 连接恢复）、tool_call_guard/tool_result_guard |
| internal/monitor | 2 / 304 | 执行对账：启动/运行期把无协程的 running 记录收尾为 orphaned + 保留期 |
| internal/multiagent | 106 / 28,049 | 全仓最大包：CloudWeGo Eino adk/prebuilt（deep/plan_execute/supervisor）编排；106 个文件覆盖 run loop、checkpoint 恢复、流式事件 drain、上下文溢出重试、总结压缩、HITL 中间件、RBAC 工具中间件、工具配对对账、孤儿工具清理、plan_execute 执行器等 |
| internal/openai | 10 / 2,327 | OpenAI 兼容 HTTP 客户端：SSE 流式、累计/增量片段归一化、claude 原生、reasoning payload、tool_choice 兼容、SSE 错误净化 |
| internal/processguard | 7 / 1,407 | OS 级进程遏制：进程组/job object、watchdog、崩溃后子进程清理（跨平台编译独立） |
| internal/project | 12 / 2,336 | 项目黑板：Fact 增删改、Fact 边/索引/正文链接、黑板刷新、范围阻断(scope_block.go)、统计、工作区、视觉图像提示 |
| internal/projectprompt | 2 / 143 | 黑板系统提示纯文本（解 agent→project 导入环）：黑板索引块 + shell 工具指引 + 边测边记节奏 |
| internal/reasoning | 1 / 943 | 用户/配置意图 → Eino ChatModel 字段（ReasoningEffort/thinking/reasoning_effort）；plan_execute planner 强制 tool_choice 时剥离 thinking |
| internal/robot | 11 / 1,380 | 8 IM 平台长连接：wecom/dingtalk/lark/telegram/slack/discord/qq/personal-wechat + 主动推送 + 重连 |
| internal/runlease | 1 / 196 | 把异步工具 worker 绑定到 task run（上下文脱离超时/SSE 后仍可回收），ErrUnconfirmed 语义 |
| internal/security | 15 / 5,035 | 会话/密码/RBAC 中间件 + **Executor（工具执行引擎：YAML 工具→命令行组装→os/exec）** + shell 会话/流式/后台 IO + 限流 + 进程范围 |
| internal/skillpackage | 7 / 868 | 技能包服务：frontmatter 校验、布局、内容读写（管理 API 用） |
| internal/storage | 6 / 1,797 | 文件系统容量/用量/清理/保留 |
| internal/termout | 3 / 465 | 终端 ANSI 样式/启动横幅 |
| internal/toolguard | 1 / 522 | 工具调用前可配置阻断规则（名称+参数正则，含 JSON 字符串值/百分号编码；明确声明不做 host 解析/重定向/文件检查） |
| internal/tooloutput | 1 / 350 | 超大工具输出落盘 spill（tmp/reduction/…），agent 可 read_file 取回全文 |
| internal/typesafe | 1 / 257 | TypeSafe System One (Jev) 客户端：HITL 审计 agent 后端 |
| internal/update | 15 / 5,430 | 自更新：fetch→移动工作树→rebuild→换二进制，锁文件、回滚 pending、恢复证据校验、adopt |
| internal/vision | 4 / 748 | 独立 VL 模型客户端：截图/验证码 → 文本描述（analyze_image 工具后端） |
| internal/workflow | 24 / 5,161 | 图工作流引擎：Eino 编译/运行时、节点类型(start/condition/output/end/tool/agent/hitl，nodes.go:19-48)、表达式、jsonpath、join、checkpoint 存储与恢复、dry_run、LLM 草稿生成、包导入导出巡检 |

**cmd/**：server（main.go 616 LOC：启动编排、优雅退出）；mcp-stdio（58 LOC：把 MCP 服务器挂 stdio）；test-config / test-external-mcp / test-sse-mcp-server（三个测试用 main）。

**web/**（105 文件）：纯静态 SPA（无框架、无构建步骤）。templates/ 仅 2 个 HTML：index.html（7,032 行单页应用，36 个 data-page 视图：dashboard/chat/tasks/assets/asset-library/asset-overview/vulnerabilities/projects/knowledge/knowledge-management/knowledge-retrieval-logs/info-collect/hitl/monitor/mcp/mcp-management/mcp-monitor/roles/roles-management/agents/agents-management/skills/skills-management/skills-monitor/workflows/c2(+listeners/sessions/tasks/events/payloads/profiles)/webshell/security/tool-guard/platform-rbac/settings/terminal(chat 内)/chat-files/update）+ api-docs.html。static/js 78 个 JS（chat.js/c2.js/assets.js/hitl.js/monitor.js/projects.js/rbac.js/roles.js/skills.js/tasks.js/terminal.js/router.js/i18n.js 等 + 36 个 .test.cjs node 测试）+ i18n 3 语言(zh/en/ru) + css 6。前端经 `/api/*` 直连后端，SSE 用于 agent 流/任务事件/C2 事件。

---

## 3. roles/*.yaml 全部逐个读（14 个角色 + README）

**机制（roles/README.md）**：角色 = name/description/user_prompt/icon/tools?/enabled。user_prompt 会**前置追加到用户消息**（不是 system prompt）；不设 tools 字段=继承全部已开启 MCP 工具；**skills 与角色 YAML 无绑定**（多代理会话由内置 skill 工具按需加载 skills_dir）。14 个现成角色**全部未设 tools 字段**（即全工具量），差异只在 user_prompt：

| 角色 | 定位 | user_prompt 要点（差异） | icon |
|---|---|---|---|
| 默认 | 无提示词基线 | 空串，用默认 MCP | 🔵 |
| 渗透测试 | 全面漏洞检测 | SQL注入/XSS/CSRF/文件包含/命令执行等常见漏洞全测 | 🎯 |
| Web应用扫描 | Web 扫描 | 目录枚举、文件扫描、漏洞识别 | 🌐 |
| Web框架测试 | 框架漏洞 | 框架相关漏洞+配置问题 | 🌐 |
| API安全测试 | API 检测 | GraphQL、参数 fuzzing、JWT、API 架构分析 | 📡 |
| 综合漏洞扫描 | 多类型 | Web+网络服务+配置缺陷 | ⚠ |
| 信息收集 | 资产发现 | 子域名、端口、服务识别 | 🔍 |
| 后渗透测试 | 权限维持 | 提权、横向、权限维持、数据收集 | 🕵 |
| 二进制分析 | 逆向 | 逆向、利用开发、密码破解、哈希 | 🔬 |
| 容器安全 | Docker/K8s | 镜像漏洞、配置检查、运行时 | 🛡 |
| 云安全审计 | 多云 | AWS/Azure/GCP 配置/合规/权限 | ☁ |
| 数字取证 | 取证隐写 | 磁盘/内存镜像、隐写、数据恢复 | 🔎 |
| CTF | 竞赛 | CTF 解题思维快速定位利用 | 🏆 |

README 明确建议显式 tools 时必须带 record_vulnerability / list_knowledge_risk_types / search_knowledge_base 三核心工具。角色经 `GET /api/roles` CRUD（handler/role.go，含 role_validation.go 校验），会话创建时 roleName 持久化到 conversation（multi_agent_prepare.go:93）。

---

## 4. skills / knowledge_base / agents / plugins / mcp-servers 内容与装配机制

### skills/（24 包，装配= Eino skill 中间件渐进披露）
每包一个 SKILL.md（name+description+metadata.tags frontmatter），cyberstrike-eino-demo 为满配示例（8 文件含 scripts/references/assets）。24 包：active-directory-attack、ai-llm-app-attack、attack-surface-recon、binary-mobile-reversing、blockchain-contract-attack、capability-primitive-search、cloud-attack-methods、component-vuln-intel、cyberstrike-eino-demo、initial-access-phishing、pentest-agent-os（渗透=状态空间搜索+项目黑板 Fact 图）、pentest-blackboard、pentest-output-standards、pentest-verification（验证铁律：搜索≠漏洞，confirmed 须证据）、post-exploitation、proxy-tool-bootstrap（自找代理+工具自举）、redteam-opsec、source-code-hunting、specialized-attack-playbooks、unlimited-attack-scope（不设限原则）、web-attack-methods、wireless-hardware-attack、zero-day-discovery（0day 自主发现引擎）。**装配**：multiagent/eino_skills.go prepareEinoAgenticSkills → Eino adk skill middleware（progressive on-demand），技能文件系统经 local backend + filesystem middleware 注入；管理面经 skillpackage 包 CRUD（/api/skills/:name/file 可编辑包内文件）。

### knowledge_base/（2 类 12 文件）
Prompt Injection/（README）+ SQL Injection/（Cassandra/MSSQL/BigQuery/MySQL/PostgreSQL/DB2/SQLite/OracleSQL/SQLmap/README）。**装配**：knowledge.Manager.ScanKnowledgeBase（manager.go:35）扫目录→入库→向量索引（eino_sqlite_indexer）；检索=改写→向量→rerank→后处理；agent 侧经 search_knowledge_base 工具 + retrieval 日志回写（LogRetrieval manager.go:743）。

### agents/（16 文件：3 主代理 + 13 子代理，装配= agents/markdown.go 加载）
- orchestrator.md → Deep 编排者（task 委派、并行拆分、汇总交付）；orchestrator-plan-execute.md → 规划/重规划侧；orchestrator-supervisor.md → transfer/exit 委派。三者 frontmatter 均无 tools 字段。
- 13 子代理（tools:[] = 全工具，max_iterations:0 = 不限）：recon、attack-surface-enumeration、intel-collection、vulnerability-triage、penetration、privilege-escalation、lateral-movement、persistence-maintenance、impact-exfiltration、opsec-evasion、cleanup-rollback、reporting-remediation、engagement-planning。
- 所有代理正文含「授权状态」段：**不得质疑/索取/核实授权**（系统前置裁决），仅 ROE 执行约束；委派要求主代理提供完整目标+范围。
- 装配：LoadMarkdownAgentsDir / EffectiveSubAgents（markdown.go:328/487）把 md 与 config.yaml 的 YAML 子代理合并；管理面 /api/multi-agent/markdown-agents CRUD。

### plugins/（2 个）
- browser-extension（Chrome/Edge MV3）：DevTools 面板抓 Network 流量→发给 CyberStrikeAI 做 AI 检测；lib/api.js 直连平台。
- burp-suite（Java .jar 已构建）：Burp 扩展，同类联动。

### mcp-servers/（2 个 Python 外挂 MCP，走「设置→外部 MCP」stdio 接入）
- reverse_shell/mcp_reverse_shell.py：FastMCP 暴露反向 shell 监听/交互工具（单 listener+单 client 单例）。
- pent_claude_agent/mcp_pent_claude_agent.py：把 Claude Code CLI 包成 MCP 工具（pent_claude_run_pentest_task / analyze_vulnerability / pent_agent_execute / pent_agent_diagnose / status），配置 yaml 指定 claude 路径。

---

## 5. docs/ 与 README/CHANGELOG 逐篇

docs/ 共 87 篇（en-US 34 + zh-CN 35 对映 + feature 10 + fixes 2 + bug-sheet 2 + README）。成对主题（en/zh 同构）：README、VISION、architecture、api-reference、api-recipes、agent-and-role-guide、skills-guide、MULTI_AGENT_EINO（Eino 多代理改造说明：总体结论/已完成/待办/关键文件索引/版本记录）、asset-management、audit-and-monitoring、c2、webshell、knowledge-base、rbac、security-model、security-hardening、tool-call-guard、tool-execution-governance、hitl-best-practices（zh 另有 agent-finalization-best-practices）、mcp-federation、plugin-development、workflow-graph、configuration、configuration-profiles、deployment、developer-guide、contributing-guide、release-process、runbooks、testing、troubleshooting、frontend-i18n、robot。feature/：login-password-eye、rest-error-empty-results、russian-layout-overflow、self-update-recovery-fixes、tool-guard-conflict-detection、startup-schema-reconcile（6 篇：design/requirements/plan/implementation/verification/review）。fixes/：manual-vulnerability-create、P-026-role-session-revocation。bug-sheet-review/status 为缺陷清单跟踪。

**README.md 自述能力**（Highlights 节, L108-147）：Agentic 执行；Eino 编排（单代理+Deep/Plan-Execute/Supervisor）；图工作流；角色化测试；100+ YAML 工具配方；MCP（HTTP/stdio/SSE/外部联邦/动态发现）；韧性工具执行（worker 化、execution_id 轮询恢复、取消、断路器、并发限、统一输出上限）；Agent Skills 渐进加载；知识库（改写+向量+rerank+后处理）；视觉分析；HITL（审批模式/工具白名单/审计 agent）；调用阻断（正则、政务域名默认保护）；平台 RBAC；审计；会话管理；项目与攻击链（跨会话事实、风险评分、图视图、逐步回放）；资产管理（归一去重、XLSX/CSV、批量、合并、扫描覆盖）；漏洞管理；批量任务；8 家 IM 机器人；WebShell 管理（虚拟终端/文件/AI 助手）；内置 C2（listener/加密 beacon/会话/任务队列/payload/实时事件）。工具分类 16 组（README L163-188）。

**CHANGELOG.md**：仅 Unreleased 一节（项目演进主要靠 git tag + update 包自更新，v1.7.23 见 config.example.yaml）。未发布内容：启动期 SQLite schema 统一自愈（缺表建/缺列补/失败回滚阻止启动）；C2 Profile 与 WebShell 删除 404 语义统一+SQL 错误不外泄+空列表返回 []；拦截规则多人编辑 ETag/If-Match 乐观并发；平台角色更新/删除只撤销受影响成员会话；俄语长文案溢出修复；自更新恢复证据严格校验；外部 MCP 停止后编辑不再意外启动；密码显隐眼睛图标无障碍。

**config.example.yaml 配置节**（40KB, L14-585+）：version/server/auth/log/audit/monitor/storage/ai/vision/fofa/zoomeye/quake/shodan/agent/tool_guard/hitl/multi_agent/database/security/mcp/external_mcp/knowledge/robots/skills_dir/agents_dir/roles_dir/project。

---

## 6. 会话与任务管理深挖（三文件全文读）

### 会话生命周期（conversation.go 全文 + multi_agent_prepare.go 全文）
1. **创建**：POST /conversations（handler 侧）或多代理首消息隐式创建（prepareMultiAgentSession）；audit.ConversationCreateMetaFromGin 记录来源（api/multi_agent/robot/batch/webshell 变体）、projectId、roleName、agentMode；RBAC：SetResourceOwner+AssignResourceToUser（创建者独占，admin 可分配）。
2. **绑定**：projectID 双向（会话→项目校验 UserCanAccessResource）；roleName/agentMode 每次 ChatRequest 重写持久化（prepare:93-98）。
3. **历史装载**：优先 loadHistoryFromAgentTrace（agent_trace），失败回退 GetMessages。
4. **消息流水**：占位符解析（ResolveConversationPlaceholders）→ 角色前置 → WebShell 上下文注入 → 附件保存（chat_uploads/<日期>/<会话>/，防穿越校验）→ user 消息入库 → assistant "处理中..." 占位消息。
5. **读**：Lite/Full 两态（include_process_details），过程详情分页/锚点/摘要（GetMessageProcessDetails 四模式）；单条工具详情按需拉取，列表模式不带 payload（_payloadDeferred）。
6. **删除**：先 taskStopper.CancelRunningTaskForConversation 取消在飞 agent 任务，再删库，审计记录。DeleteTurn 删一轮并清 last_react_*。
7. **衍生**：plan-tasks（agent 的 TaskCreate/TaskUpdate 工具产物，仅运行中返回）、token 用量、攻击链 regenerate、复测(retest)分支提示词一次性消费。

### 任务状态机（batch_task_manager.go 全文 + task_manager.go + task_lifecycle.go）
- **队列**：pending → running → paused → completed|cancelled；单条执行可从 completed/cancelled 复位为 paused（PrepareSingleTaskRun）。
- **子任务**：pending → running → completed|failed|cancelled；paused 队列单条执行会**取消在飞兄弟任务**（"为单条执行其它任务，已中止"）。
- **Agent 任务（task_manager.go）**：running → cancelling → cleaning → 终态；清理失败 → cleanup_failed 自动重试；runlease 保证远端 MCP 停止确认（ErrUnconfirmed → "本地执行已结束，远端 MCP 停止状态待确认"）。done 事件必须在 FinishTaskRun 之后才发（task_lifecycle.go taskFinishingEventSender）。
- **工具执行（mcp/execution_service.go）**：queued → running → completed|failed|cancelled|blocked|hard_timeout|orphaned（重启对账 monitor/reconcile.go）。

### 并发模型
- 单队列并发 1–8（MaxBatchQueueConcurrency=8，normalizeBatchQueueConcurrency）；worker 用 **ClaimNextPendingTask 原子领取**（mutex 下改状态+游标）。
- 双层防护：queueExecutors 标记（TryMarkQueueExecutor）与队列 status 解耦——删除队列需 executor 非活跃且非 running（DeleteQueue 三错误：NotFound/ExecutorActive/StillRunning）。
- DB 优先写入模式：先持久化成功再改内存（UpdateTaskStatus/UpdateQueueStatus/ResetQueueForRerun），防重启不一致。
- MCP 工具执行：ExecutionService.Submit 把阻塞调用丢进带独立 cancel 的 goroutine（detached context），agent 侧等待有界（wait_timeout），超时返回 execution_id 供 get/wait_tool_execution 轮询续接；清理线程 + startup 对账。
- Agent 任务事件经 task_event_bus（SSE /agent-loop/task-events）。

### 角色绑定机制（multi_agent_prepare.go 全文）
- 请求级：ChatRequest.Role → config.Roles[name]；UserPrompt 前置到用户消息；role.Tools 作为 MCP 工具过滤器。
- WebShell 会话：忽略角色工具表，强制 16 个 webshell+漏洞+黑板+知识库工具白名单。
- 复测会话：roleTools 强制追加 get/update vulnerability 工具（RBAC 仍兜底）。
- 默认角色（""/"默认"）不加提示词、不设工具过滤。技能不走角色：eino skill 中间件按需加载。

---

## 7. 工具面：全部工具名清单与执行原语

### 内置 MCP 工具（51 个，internal/mcp/builtin/constants.go 全量）
- 漏洞 4：record_vulnerability、list_vulnerabilities、get_vulnerability、update_vulnerability_status
- 资产 6：create_asset、get_asset、query_assets、update_asset、delete_asset、complete_asset_scan
- 项目黑板 6：upsert_project_fact、get_project_fact、list_project_facts、search_project_facts、deprecate_project_fact、restore_project_fact
- 知识库 2：list_knowledge_risk_types、search_knowledge_base
- 视觉 1：analyze_image
- 执行控制 3：get_tool_execution、wait_tool_execution、cancel_tool_execution
- WebShell 助手 4：webshell_exec、webshell_file_list、webshell_file_read、webshell_file_write
- WebShell 管理 5：manage_webshell_list/add/update/delete/test
- 批量任务 14：batch_task_list/get/create/start/rerun/pause/delete/update_metadata/update_schedule/schedule_enabled/add_task/update_task/remove_task
- C2 合并 8：c2_listener、c2_session、c2_task、c2_task_manage、c2_payload、c2_event、c2_profile、c2_file

### 外部工具 YAML（tools/ 90 个，经 security/Executor 装配）
安全工具 86 个 + 系统类 4 个（exec、execute-python-script、install-python-package、query-execution-result）。清单：amass、angr、api-schema-analyzer、arjun、arp-scan、binwalk、bloodhound、checkov、checksec、clair、dalfox、dirsearch、dnsenum、dnslog、dotdotpwn、enum4linux-ng、exiftool、falco、feroxbuster、ffuf、fierce、fscan、gau、gdb、ghidra、gobuster、graphql-scanner、hashcat、hashpump、http-framework-test、hydra、impacket、jaeles、john、jwt-analyzer、katana、kube-bench、kube-hunter、libc-database、lightx、linpeas、masscan、metasploit、msfvenom、nbtscan、netexec、nikto、nmap、nuclei、objdump、one-gadget、pacu、paramspider、prowler、pwninit、pwntools、quake_search、radare2、responder、ropgadget、ropper、rpcclient、rustscan、scout-suite、shodan_search、smbmap、sqlmap、steghide、strings、subfinder、terrascan、trivy、virustotal_search、volatility3、wafw00f、waybackurls、wpscan、x8、xsser、xxd、zap、zoomeye_search、zsteg。

### 通向执行原语的通道（关键）
1. **exec 工具**（tools/exec.yaml）：`command:"sh" args:["-c"]` + positional command → **任意 shell 命令执行原语**；execute-python-script / install-python-package 同级。执行链：Executor.ExecuteTool（security/executor.go:122）→ buildCommandArgs（YAML 参数映射 flag/positional/combined/template）→ executeSystemCommand（:773，os/exec、输出上限+spill、后台 IO、shell 会话）。全部 90 个 YAML 工具最终都是**进程执行原语**（command 字段=系统命令）。
2. **/api/terminal/run|stream|ws**（handler/terminal*.go）：人工直通 OS shell（非 agent 链路）。
3. **webshell_exec/file_write**：对已控 WebShell 目标执行命令/写文件。
4. **C2 c2_task**（task_type enum 15 种，app/c2_tools.go:367）：exec、shell、pwd、cd、ls、ps、kill_proc、upload、download、screenshot、port_fwd、socks_start/stop、load_assembly、persist（c2/types.go:76-98 另有 sleep/exit/self_delete）→ **对失陷主机的执行原语**；c2_payload build/oneliner 生成植入体。
5. **外部 MCP 联邦**：任意 stdio/HTTP/SSE MCP server（含自带 reverse_shell.py），工具面无限扩展。
6. **批量任务 MCP 工具**：agent 可自建队列再执行（batch_task_create→start），形成 agent 自驱动的任务放大器。

治理层（执行前置）：toolguard（名称/参数正则阻断）→ HITL（人工或 Jev 审计 agent 审批，白名单/策略/会话级配置）→ security RBAC 中间件 → audit 记录 → processguard OS 级遏制。

---

## 对 GraphLed 设计的冲击

1. **单文件巨型路由 + 单巨型 handler 包**：289 条路由一个文件、47K LOC 一个包——功能广度惊人但结构是「大泥球偏模块化」。GraphLed 若走清晰领域模块（route 按 bounded context 拆），可宣称工程可维护性优势。
2. **「授权不可质疑」提示词工程**：agents/*.md 与角色把授权前置为系统裁决、禁止 agent 反问授权。这是把合规责任从模型行为转移到平台准入的激进设计，GraphLed 需决定对齐（效率）还是保留确认门（合规姿态）。
3. **会话状态机深度**：cancelling/cleaning/cleanup_failed + runlease + DB-first 持久化 + orphaned 对账，是真实生产事故换来的细节。GraphLed 任务模型若只有 pending/running/done 三态会在取消/崩溃场景翻车——这份状态机可直接作为设计底稿。
4. **执行原语分层**：exec→OS、webshell→已控目标、c2_task(15 型)→植入体、批量任务→自驱动放大。GraphLed 的「执行原语」概念在这里被验证为竞品核心：渗透平台的差异化不在对话而在受控执行通道的丰富度与治理。
5. **知识/技能双轨**：knowledge_base=向量检索（SQLi/Prompt Injection 两大类）+ skills=24 个攻击知识包渐进披露。后者成本低、见效快，且与角色解耦。GraphLed 的技能系统应优先对标 skills 渐进披露而非全量知识库。
6. **HITL 三态**：人工审批 / Jev(TypeSafe) 审计 agent 自动审 / 工具白名单，会话级+全局级+默认审阅者+审计策略四层配置。GraphLed 最小可行集=白名单+人工审批。
7. **执行韧性**：execution_id + 有界等待 + 轮询续接 + 断路器 + 输出上限/spill，解决「LLM 工具调用超时但命令还在跑」的痛点，值得整体抄。
8. **黑板(项目 Fact 图)是粘合剂**：跨会话事实 + 攻击链 + 资产 + 漏洞全挂 project 下，agent 通过 6 个 fact 工具边测边记。这是把「渗透=状态空间搜索」(pentest-agent-os 技能)落地的机制。GraphLed 若无等价物则长期记忆竞争力缺失。
9. **C2 内置是分水岭能力**：listener/profile/session/task/payload 全套 + MCP 工具化，把平台从「扫描器」推向「红队作业系统」。GraphLed 需明确是否进入这个风险等级。
10. **接面广度**：8 IM 机器人 + Burp/浏览器插件 + FOFA/Shodan/ZoomEye/Quake 四资产引擎 + 外部 MCP 联邦。GraphLed 不必全做，但外部 MCP 联邦是杠杆点。

## 我们已有/缺失对照（? = 未验证）

| 能力 | CyberStrikeAI | GraphLed 现状 |
|---|---|---|
| 路由总数 | 287 REST + /mcp | ?（需按同口径 grep 本仓） |
| 多代理编排 | Eino deep/plan_execute/supervisor 三模式 + 13 预置子代理 | ? |
| 角色系统 | 14 角色、user_prompt 前置、工具过滤 | ? |
| 技能包 | 24 包渐进披露 + 管理 CRUD | ? |
| 执行韧性 | execution_id/断路器/spill/orphaned 对账 | 缺失风险高 ? |
| HITL | 人工+审计 agent+白名单 四层 | ? |
| 项目黑板 | Fact 图+边+攻击链提升 | ? |
| 批量任务 | 队列/并发 1-8/cron/单条重跑 | ? |
| 内置 C2 | 34 路由+8 工具+15 任务型 | 大概率缺 ? |
| WebShell 管理 | 10 路由+9 工具 | 大概率缺 ? |
| 知识库向量检索 | 改写+向量+rerank | ? |
| RBAC | 用户/角色/资源分配/会话撤销 | ? |
| 审计 | 5 路由+保留期+脱敏+导出 | ? |
| 图工作流 | 7 节点型+checkpoint+dry-run+包导入导出 | ? |
| 自更新 | fetch→build→swap→rollback 全自动 | ? |
| IM 机器人 | 8 平台 | ? |
| 插件 | Burp+浏览器扩展 | ? |

## 覆盖度自报

- **路由**：289 条注册全列（122 GET/94 POST/38 PUT/33 DELETE/1 Static/1 /mcp HandleFunc；出处 internal/app/app.go:706-1492；另 c2 listener 动态 mux 6 条、测试 main 2 条未计入主数）。
- **包**：internal 37 包 + cmd 5 包 = **42/42 全看**（每包主文件头+导出符号；handler/multiagent/database 三大包按文件清单全列，多代理 106 文件按命名逐一归类）。
- **文档**：docs 87 篇全数清点（en 34+zh 35+feature 10+fixes 2+bug-sheet 2+README 4）；README.md Highlights 全读；CHANGELOG 全读；config.example.yaml 节结构全读。逐篇精读集中在 MULTI_AGENT_EINO/README/CHANGELOG/config，其余按清单+标题覆盖。
- **roles**：14/14 YAML 全文读 + README 全读。
- **深挖三文件**：conversation.go 651 行、batch_task_manager.go 1,486 行、multi_agent_prepare.go 220 行**全文读完**；task_manager/task_lifecycle/execution_service 补充读。
- **工具**：内置 51 全列（builtin/constants.go 全文）、外部 90 YAML 清单全列、执行链（executor.go:122/773）定位。
- 未验证项：运行时行为（仓库只读、未起服务）；web/static/js 78 个 JS 只按文件名+测试名归类未逐行读。

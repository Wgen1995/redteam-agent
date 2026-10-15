# CyberStrikeAI 使用手册（实时滚动版 · 2026-10-15 起）

> 状态: **完整版 v2**（骨架 v1 → 漫游舰 30 视图实机实证 + 源码只读充实）。更新时间: 2026-10-15 17:05。
> 系统: https://127.0.0.1:8443 （本实例 v1.7.23，admin 登录，TLS 自签）；本地源码: `ai-assisted-security-verification-platform/CyberStrikeAI`（Go 1.25 + Eino + SQLite，Apache-2.0，上游 7808★，404星链计划）。
> 口号: "The system of action for AI-native cybersecurity — where intent becomes governed execution"。
> 实证材料: 界面漫游报告 `../liveui/walk-csai.md` + 30 张截图 `../liveui/shots/csai-00~29-*.png` + 逐页 DOM 数据 `../liveui/data/`；本手册界面章节的按钮/参数均来自实机 DOM，机制章节来自 `README_CN.md`、`config.example.yaml`、`internal/` 模块与 `docs/zh-CN/` 文档名实读。

---

## 0. 定位与能力总览

**它是什么**：AI 原生网络安全「智能执行中枢」——把自然语言意图变成**受治理、可审计**的安全行动，把行动证据沉淀为项目记忆（事实黑板/攻击链），让每次行动优化下一次（角色/Skills/知识复用）。一句话：**对话式开战 + 资产/漏洞运营 + 攻击基础设施（C2/WebShell）+ 多智能体能力中心**，四合一的渗透作战平台。

**能力矩阵**（★=本实例已启用实证）：

| 域 | 能力 | 本实例状态 |
|---|---|---|
| 智能体 | 单代理(Eino ADK) / Deep / Plan-Execute / Supervisor 四种编排；16 个 .md Agent；13 个角色 Persona | ★ 默认 eino_single，GLM·glm-5.3 |
| 工具 | MCP 生态 139 工具（网络/Web/漏扫/子域/API/容器/云/二进制/利用/破解/取证/后渗透/CTF） | ★ 启用 127，常驻 49 |
| 知识 | RAG 知识库（多查询改写+向量+精排+后处理）、检索历史 | 未启用（空态引导去设置） |
| 技能 | 23 个 Skills（AD 域攻/AI LLM 攻/侦察/逆向/区块链/云/0day…） | ★ 23 个，1 次调用 |
| 治理 | HITL 审批（人工/审计 Agent）、tool_guard 正则拦截、RBAC、审计日志、进程隔离、存储清理 | ★ 政府域名保护规则已启用 |
| 运营 | 项目/事实黑板/攻击链、资产（概览/库/信息收集 FOFA·ZoomEye·Quake·Shodan）、漏洞生命周期、批量任务队列、工作流画布、文件管理 | ★ 项目「烛龙靶场」在役 |
| 攻击 | C2（监听器/会话/任务/载荷/事件/流量伪装）、WebShell 管理 | 模块在，空态（无监听器/会话） |
| 集成 | Burp Suite 插件、Chrome/Edge DevTools 扩展、MCP http/stdio/SSE/联邦、8 渠道机器人（企微/钉钉/飞书/TG/Slack/Discord/QQ/微信） | 通道 2 个（GLM/Qwen Max） |

**核心闭环**：
```
意图(对话/机器人/批量队列/工作流)
   → 治理卡点(tool_guard 正则 → HITL 审批/审计 Agent)
   → 执行(MCP 工具/子代理, worker 异步+熔断+输出兜底)
   → 证据(漏洞入库/事实黑板/攻击链/事件/文件)
   → 记忆复用(知识库/Skills/角色) → 下一轮更快更准
```

---

## 1. 五分钟上手

1. **部署**：`git clone … && cd CyberStrikeAI && chmod +x run.sh && ./run.sh`（自动建 venv、装依赖、编译、启动；默认 `--https` + 项目根 config.yaml）。终端出现 `● ONLINE` 即成功；**全新安装时 `ADMIN SETUP REQUIRED` 下的 admin 初始密码只展示一次**，登录后立即改。
2. **首配 AI 通道**：登录 → 系统设置 → 基本设置 → AI 通道配置 → 新增（提供商/Base URL/API Key/模型/Token 上限）→ 保存更改 → 可「测试连接」「设为默认」。等价 YAML：`ai.default_channel + ai.channels.<id>`。本实例已配 GLM(glm-5.3，默认) 与 Qwen Max 两通道。
3. **装工具（可选）**：`brew install nmap masscan sqlmap nikto gobuster ffuf hydra hashcat nuclei subfinder`（macOS）/ apt 等价（Kali）。未安装的工具执行时自动跳过或改用替代。
4. **开战**：对话页选项目（或无项目）→ 输入意图。基础示例：
   - `扫描 192.168.1.1 的开放端口` / `对 192.168.1.1 做 80/443/22 重点扫描`
   - `检查 https://example.com/page?id=1 是否存在 SQL 注入`
   - `枚举 https://example.com 的隐藏目录与组件漏洞`
   - `获取 example.com 的子域并批量执行 nuclei`
5. **进阶剧本**：`加载侦察剧本：先 amass/subfinder，再对存活主机目录爆破`、`构建最新一次测试的攻击链，只导出风险>=高的节点`、`挂载基于 Burp 的外部 MCP 完成认证流量回放`。

---

## 2. 界面地图与逐页使用手册（30 视图，实证）

> 布局：左侧 224px 固定侧栏（四区分组，可折叠）+ 顶栏（版本徽标 v1.7.23、通知铃铛 7、API 文档、GitHub、跟随系统/中文切换）+ 主内容区。hash 路由单页应用，所有视图常驻 DOM 切换显示。每节格式：**做什么 → 界面构成 → 操作/参数逐项 → 机制原理 → 实战要点**。

### 2.0 登录层（`/`，csai-00）
- **做什么**：表单登录（用户名+密码+登录按钮）；提示「默认管理员为 admin」。顶栏此时即可切换语言（跟随系统/中文）、看 API 文档与 GitHub。
- **机制**：会话有效期 `auth.session_duration_hours: 12`（默认）；登录/改密失败进审计并按 IP 节流（`audit.auth_failure_cooldown_seconds: 60`）。
- **要点**：首次启动的 admin 初始密码只在控制台展示一次；多用户到「平台权限→用户管理」建账号。

### 2.1 工作台区

**01 仪表盘 `#dashboard`（csai-01）— 运营总览一屏**
- 构成（六段式）：① 5 张 KPI 卡：运行中对话（「系统空闲」副标）、漏洞总数（「待处理高危 2」红色子徽标）、工具调用次数（「11 个工具」）、工具执行成功率（「运行平稳」）、Token 用量（「近 7 天 134 次调用·今日 8.7M」）；② 漏洞严重程度分布（全部状态筛选+严重/高危/中危/低危/信息五档占比+状态计数 待处理/已确认/已修复/已忽略/误报+修复率）+ 风险等级卡（加权风险分 10.5）；③ 最近漏洞/近期事实双 tab；④ C2/WebShell 快捷卡（运行中监听器/在线会话/待审排队任务 + 「进入 C2 →」）；⑤ 批量任务队列（待执行/执行中/已完成）+ 工具执行次数 Top10 条形（exec 104 / http-framework-test 24 / upsert_project_fact 5…）；⑥ 最近事件流 + 能力总览（MCP 工具 139/Skills 23/知识未启用/角色 13/Agents 16）。
- 操作：刷新（右上「上次更新 HH:MM:SS」闪烁动效）、全部状态筛选、各「查看全部 →」跳对应模块、通知「标记已读/查看」。
- 要点：开站第一屏判断「系统是否在跑、风险多大、工具健康度」；加权风险分与修复率是管理层视角的两个核心数。

**02 对话 `#chat`（csai-02）— 主作业入口**
- 构成：左栏「+ 新任务」、项目选择（烛龙靶场 📌/无项目）、最近对话列表、会话搜索；中央空态「要测试什么？」；底部输入框+发送+附件上传。
- 会话设置（DOM 实证 id）：`agent-mode-select`（eino_single/deep/plan_execute/supervisor）、`hitl-mode-select`（off/approval/review_edit）、`hitl-timeout-select`、`hitl-sensitive-tools`（敏感工具名单）、角色选择（🔵默认等 13 角色）、模型/通道选择（glm-5.3）。
- 机制：意图 → 编排器 → MCP 工具调用（经 tool_guard+HITL 卡点）→ 流式回显（含计划进度面板）；对话分组/置顶/重命名/批量管理；文件可拖入，产物落「文件管理」。
- 要点：**先把项目选对**（事实/漏洞/资产都挂项目）；高风险动作前把 HITL 模式从 off 调 approval；长任务盯「计划」面板而不是干等。

**03 人机协同 `#hitl`（csai-03）— HITL 审批中心**
- 构成：审批方切换（人工审批/审计 Agent，引擎标注「OpenAI 协议 · glm-5.3」）；作用域说明「作用于当前选中会话；未选会话时写入 config.yaml 作为全局默认」；四 tab：待审计/审计策略/工具白名单/审计日志；待审批列表+分页。
- 参数（config 域）：`hitl.default_mode`（off/approval/review_edit）、`default_reviewer`（human/audit_agent）、`default_timeout_seconds`（默认 300s，0 不限时）、`audit_backend`（openai=小模型审批 / typesafe=TypeSafe Jev 结构化放通）、`audit_model.*`（独立模型，建议小模型）、`tool_whitelist`（全局免审批清单，与对话级白名单**取并集**）。
- 机制：非白名单工具调用 → 按模式挂起（approval=放行/拒绝；review_edit=可改参后放行）→ 决策留审计日志（保留 90 天）。audit_agent 用独立提示词（approval 与 review_edit 两套）。
- 要点：审计 Agent 是「AI 审 AI」的省钱位——配小模型；review_edit 模式能在放行前改掉危险参数（如把 rm -rf 改成 ls）。

**04 调用拦截 `#tool-guard`（csai-04）— 执行前正则闸门**
- 构成：「已与服务端同步」状态点、总开关（启用调用拦截）、规则卡列表（01 政府网站保护：`识别到 {match}，禁止攻击政府网站…`，已启用徽标，› 展开编辑）、＋添加规则、全部规则验证（按顺序+启停试匹配整体效果）、撤销修改/保存并生效。
- 参数（config `tool_guard`）：`enabled`；`rules[]`：id/name/enabled/pattern（**Go RE2 正则**，命名捕获组 `match` 用于模板）/message（支持 `{match}`/`{tool}`/`{rule}`）。默认规则=政府域名保护（`gov` 后缀各种变体）。
- 机制：**MCP 工具执行前**按列表顺序匹配，命中即拦截并回给 Agent 提醒模板（Agent 可改道，不是硬崩）；与 HITL 白名单互相独立；Web 保存即时生效，手改 YAML 需重启。
- 要点：把「不可打的目标特征」（政府/edu/生产域名）写成规则；用「全部规则验证」回归测试规则集。

**05 项目管理 `#projects`（csai-05）— 作战记忆容器**
- 构成：项目卡列表（烛龙靶场·进行中·置顶📌·5 事实/4 漏洞/1 对话·⋯ 更多操作）；详情七 tab：漏洞管理/事实黑板/攻击路径/资产库/关联对话/关联漏洞/设置。
- 事实黑板（核心）：表格列 Key/分类/摘要/关系(↑↓计数)/Body/置信度/更新/操作（编辑/详情/废弃/删除）。**分类枚举**：target/auth/infra/business/finding/chain/exploit/poc/note。**置信度**：已确认/待确认/已废弃（exploit 类实证还有「可复现」）。筛选：搜索（key/摘要/body）、分类、置信度、仅待补全、隐藏废弃；`+ 添加事实`。
- 机制：事实是跨会话共享的项目记忆，Agent 通过 `upsert_project_fact`/`get_project_fact` 读写（都在工具调用榜上）；攻击路径 tab 把 chain/finding 类事实连成图。
- 要点：**黑板质量=平台智商**。会话结束前让 AI「把结论固化成事实」；复盘时按置信度过滤看「已确认」链。

### 2.2 安全作业区

**06 资产概览 `#asset-overview`（csai-06）— 资产态势**
- 构成：资产总数/IP/域名/端口四计数（副注「当前纳入持续监测的资产」）；协议分布表（http 100%）；近 7 天发现；态势变化（7/30/90 天切换：资产增减趋势「新增 vs 停用」+ 风险发现趋势「新增漏洞 vs 高危及严重」双折线）；扫描覆盖（总体覆盖率大百分比、已扫描资产、近 30 天覆盖、从未扫描、超 30 天未扫描）。
- 操作：刷新、查看资产库、周期切换。
- 要点：「从未扫描」和「超 30 天未扫描」就是下一步作业清单。

**07 资产库 `#asset-library`（csai-07）— 资产台账**
- 构成：表格列 目标/服务/所属项目/归属/上次扫描/相关漏洞/风险等级/状态/操作（扫描/编辑/删除）；筛选：状态▾（活跃/停用）、项目▾、高级筛选（**20+ 字段**：搜索主机 IP 域名标题服务标签、最小漏洞数、协议、端口、来源 fofa/manual、标签、国家/省/市、负责人/部门/业务、首见/末见时间区间）、保存的筛选视图（保存当前视图/删除视图）。
- 操作：批量导入（XLSX/CSV）、+新增资产（弹窗字段：目标/标签/Host/IP/域名/端口/协议/标题/Server/国家/省/市/负责人/部门/业务/环境[生产/预发布/测试/开发/其他]/重要性[核心/重要/一般/低]/状态/绑定项目）、行内扫描（可选「立即执行」）、跨页批量维护（批量改负责人/部门/业务/加标签/删标签）、重复资产合并、XLSX/CSV 导入导出。
- 机制：资产统一归档去重（域名/IP/端口/服务），扫描覆盖率与关联漏洞回写风险等级（实证：localhost 高危·4 漏洞）。
- 要点：先「批量导入」存量资产再开扫描；用保存视图固化「我的生产 Web 资产」这类日常过滤。

**08 信息收集 `#info-collect`（csai-08）— 空间测绘四步向导**
- 构成（步骤卡 01-04）：**01 数据源**（FOFA/ZoomEye/Quake/Shodan，Key 在系统设置或环境变量配，后端代理请求避免前端暴露 key）；**02 查询方式**（自然语言→「AI 解析」→弹窗展示生成的 FOFA 语法**可编辑**→确认后执行；或直接写 FOFA 语法，支持 &&/||/()；模板 chip：Apache+中国/登录页+中国/指定域名/指定 IP；语法提示与官方文档链）；**03 返回配置**（返回数量、页码、完整模式；上限 10000）；**04 返回字段**（最小字段/Web 常用/情报增强 三预设，逗号分隔自定义）。
- 结果区：已选择 N 条 → 列选择 / 导出 CSV/JSON/XLSX / **入库所选**（写资产库）/ **批量扫描**。
- 要点：这是「外部资产 → 平台资产」的主入口；AI 解析弹窗里**人工过一眼语法再执行**，避免语义漂移。

**09 漏洞管理 `#vulnerabilities`（csai-09）— 漏洞生命周期**
- 构成：顶部严重度汇总（总数+严重/高危/中危/低危/信息各自数量与占比）；筛选条：搜索（标题/描述/类型/目标）、所属项目▾、状态▾（**待处理/已确认/已修复/已忽略/误报** 五态）、更多筛选（精确漏洞 ID/所属会话/任务 ID 或队列 ID/对话标签/任务标签）；漏洞卡（标题/等级徽标/状态/所属项目/时间/**复测**按钮）；分页（10/20/50/100）。
- 操作：添加漏洞（手动：会话 ID/会话标签/任务标签/标题/类型/目标）、批量导出、批量删除、刷新、行内复测。
- 机制：`record_vulnerability` 工具让 Agent 自动入库（实证 4 次）；复测=按原目标重验；状态机支撑仪表盘修复率与「已忽略/误报」治理。
- 要点：误报率与修复率是漏洞运营双 KPI；用「任务标签」把批量扫描的漏洋试验田隔离开。

**10 任务管理 `#tasks`（csai-10）— 批量任务队列**
- 构成：队列卡（标题·类别·模式徽标·触发方式·队列 ID·创建时间·进度 100% (1/1)）；状态筛选（待执行/执行中/已暂停/已完成/已取消）；搜索（队列 ID/标题/创建时间）；自动刷新开关。
- 操作：新建任务（弹窗：标题/并发数/cron 表达式如 `0 */2 * * *`/立即执行开关/子任务文本多行）；队列级 开始/暂停/重跑/改调度/增删子任务（DOM 实证 batch_task_* 工具族：list/get/start/rerun/pause/update_metadata/update_schedule/schedule_enabled/update_task/remove_task/delete/create/add_task）。
- 机制：把 N 条独立指令登记成队列，逐条喂给 Agent 执行；`multi_agent.batch_use_multi_agent: true` 可让每个子任务走多代理（更贵）；支持 cron 周期重跑。
- 要点：适合「100 个资产各跑一遍 nuclei」这类同构任务；对话里让 AI「创建批量任务」也行（batch_task_create 工具，但 Agent 被约束为**用户明确要求才建**）。

**11 工作流 `#workflows`（csai-11）— 可视化流程编排**
- 构成：三栏——左节点库（**开始/工具/Agent/条件/审批/输出/结束** 七类）；中画布（拖节点/连线/自动布局/校验状态「校验未通过」徽标）；右属性面板（选中节点或连线后编辑，含 `workflow-prop-label` 等）。
- 操作：新建工作流（表单：名称/ID 如 web-scan-basic/描述/启用）、导入本地包（上传 zip，含覆盖确认）、**用自然语言创建**（弹窗输入目标 + AI 选项复选：域名监控/报告审批/资产研判 → 渲染到画布/生成草稿）、试运行（dry-run 输入消息）、保存、更多。
- 机制：工作流引擎（internal/workflow）按节点图调度，断点续跑（`workflow_checkpoints` 7 天）；「审批」节点把 HITL 嵌进流程。
- 要点：把重复剧本固化成图；先试运行再启用；AI 生成草稿后人工修节点参数。

**12 WebShell 管理 `#webshell`（csai-12）— 失陷通道管理（仅授权）**
- 构成：左连接列表+右详情双栏；空态「暂无连接」。
- 操作：添加连接（表单 DOM 实证：URL http(s)://target/shell.php、密码（冰蝎/蚁剑）、cmd 参数名（默认 cmd）、备注名）；一键批量探活。
- 机制：注册 `webshell_exec/file_list/file_read/file_write` 与 `manage_webshell_*` 工具族进 MCP，Agent 可在对话中直接操作已登记的 WebShell（都在常驻工具白名单里）。
- 要点：探活防死连；给 AI 用前确认授权范围（安全模型文档警示）。

**13-18 C2 子系统（监听器/会话/任务/载荷/事件/流量伪装）— 内置 C2（仅授权）**
- **监听器 `#c2-listeners`**：列表+「+ 创建监听器」（空态双入口引导）；`c2.enabled` 控制模块整体启停。
- **会话 `#c2-sessions`**：状态筛选（活跃/休眠/离线）+监听器筛选+全选/重置+「疑似误报」标记；批量删除/删除筛选结果；空态教学「启动监听器并在目标上执行 Payload」。会话 ID 形如 `s_xxxxxxxx`（筛选占位符实证）。
- **任务 `#c2-tasks`**：结果三计数（成功/失败/待处理）+快捷时间窗（15 分钟/1 小时/24 小时/7 天/全部）+状态（队列中/已发送/执行中/成功/失败/已取消）+**类型枚举**（shell/exec/ls/pwd/cd/download/upload/ps/sleep/screenshot）+会话 ID 过滤。
- **载荷 `#c2-payloads`**：双生成器——单行 Payload（Bash/Python/PowerShell/Curl 反弹 oneliner，选监听器/类型/回连地址→「生成 Oneliner」）；编译 Beacon（Linux/Windows/macOS × AMD64/ARM64/386 交叉编译→「构建 Beacon」，回连地址留空则用监听器配置）。
- **事件 `#c2-events`**：级别（信息/警告/严重）×类别（监听器/会话/任务/Payload/OPSEC）审计流，时间窗同上，批量删除。
- **流量伪装 `#c2-profiles`**：Profile 列表+创建（给 Beacon 套流量伪装特征）。
- 机制：internal/c2 模块，加密 Beacon；产物（截图/上传件/下发文件/payload）落 `tmp/c2`（存储清理默认 30 天，**清了 payload 下载链接即失效**）；全部动作进事件审计。
- 要点：作业顺序=监听器→载荷→投递→会话→任务；OPSEC 类事件要盯。

**19 文件管理 `#chat-files`（csai-19）— 对话产物中心**
- 构成：筛选（会话 ID/项目 ID/文件名/来源▾：**对话附件/工具输出/工作目录/会话产物**）；分组方式▾（不分组平铺/按日期/按会话/按项目/按文件夹路径浏览）；表格（日期/会话/子路径/文件名/大小/修改时间/操作）；本实例 197 个 `call_*.txt` 工具输出（每页 20，10 页）。
- 操作：上传文件（支持多选+拖拽到列表区）、导出当前结果、重命名/新建文件夹（`chat-files-rename-input`/`mkdir-input`）。
- 机制：说明文案实证——「需要让 AI 引用某文件时，在列表中点击**复制路径**，到对话里粘贴即可（路径为服务器绝对路径，与对话附件保存位置一致）」。上传件保留 90 天（`storage.categories.chat_uploads`）。
- 要点：大工具输出会落盘为文件（reduction 机制），这里是检索入口；给 AI「看」文件的正确姿势=复制路径粘贴进对话。

### 2.3 能力中心区

**20 MCP 状态监控 `#mcp-monitor`（csai-20）— 工具观测台**
- 构成：KPI（总调用 151/成功 144/失败 7/成功率 95.4%「运行平稳」/最近一次调用时间）；工具统计条形（累计/7 天切换，Top6 占 94.7%，每工具 调用数/成功/失败/成功率）；调用趋势（24 小时/7 天/30 天，峰值 106@10/15 13:00）；活跃时段；最新执行记录表（工具/状态/开始时间/耗时/查看详情/删除）。
- 状态枚举（筛选 DOM 实证）：已完成/执行中/排队中/失败/**已拦截**（tool_guard 命中）/执行超时/已终止/**孤儿任务**（worker 与会话失联）。
- 机制：`tool_executions` 表保留 90 天（`monitor.retention_days`）；悬停色条与列表行联动。
- 要点：排障三连——看失败率、看孤儿任务、看拦截记录。

**21 MCP 管理 `#mcp-management`（csai-21）— 工具启停**
- 构成：工具清单（名称/常驻徽标/▶ 展开长描述，如 amass/angr/api-schema-analyzer/arjun/arp-scan/batch_task_*…）；统计条「当前页已启用 20/20 · 总计已启用 127/139 · 常驻 49」；全选/全不选/全部/已启用/已停用/搜索；「保存工具配置」。
- 机制：工具定义在 `tools/*.yaml`（100+ 配方，`security.tools_dir`），「常驻」=始终进模型上下文（配合 tool_search 渐进披露，见 §3.2）；外部 MCP 在 `external_mcp.servers` 配（http/stdio/SSE/联邦）。
- 要点：关掉用不到的工具=省 token+降误选；描述模式 `tool_description_mode: full|short` 控制描述长短。

**22 检索历史 `#knowledge-retrieval-logs`（csai-22）**：RAG 观测——总检索/成功/成功率/检索到知识项四计数 + 会话 ID/消息 ID 筛选。排障 RAG 命中率用。

**23 知识管理 `#knowledge-management`（csai-23）**：构建索引/全量重建/添加知识（分类如「SQL注入」+标题+正文）/分类筛选/搜索；未启用时空态引导「前往设置」。配置域 `knowledge.*`（embedding provider/model、top_k、相似度阈值、子索引过滤、多查询改写上限、rerank、后处理、索引批大小/限速/重试、chunk 大小/重叠）。

**24 技能状态 `#skills-monitor`（csai-24）**：23 Skills 调用统计表（总调用/成功/失败/成功率/最后调用），可清空统计。本实例仅 pentest-agent-os 被调过 1 次。

**25 技能管理 `#skills-management`（csai-25）**：Skills 卡（名称/文件数/描述/标签 渗透测试·penetration-testing·红队；查看/编辑/删除；创建 Skill 表单：名称如 sql-injection-testing+描述+新文件路径如 FORMS.md）。23 个技能覆盖：active-directory-attack、ai-llm-app-attack（提示注入/Agent 工具滥用 RCE/RAG 投毒/MCP 供应链）、attack-surface-recon（开局第一动作）、binary-mobile-reversing、blockchain-contract-attack、capability-primitive-search（低危链组合凑 RCE）、cloud-attack-methods、component-vuln-intel、initial-access-phishing、pentest-agent-os（操作系统级）、pentest-blackboard、pentest-output-standards、pentest-verification、post-exploitation、proxy-tool-bootstrap、redteam-opsec、source-code-hunting、specialized-attack-playbooks、unlimited-attack-scope、web-attack-methods、wireless-hardware-attack、zero-day-discovery、cyberstrike-eino-demo。
- 机制：Eino 官方 Skills 体系——SKILL.md + 附属文件，**渐进式按需加载**（模型先见简介，用到才 `skill` 工具拉全文）；目录 `skills_dir`。

**26 智能体管理 `#agents-management`（csai-26）**：Agent 目录（`agents/*.md`，YAML front matter+正文系统提示词；主代理为 Deep 协调者不参与 task 子代理列表）。主代理三套：orchestrator-plan-execute.md（规划/重规划，计划每步须含完整目标与范围）、orchestrator-supervisor.md（transfer 委派专家+exit 结束）、orchestrator.md（Deep 编排）。子代理 13 个：attack-surface-enumeration/cleanup-rollback/engagement-planning/impact-exfiltration/intel-collection/lateral-movement/opsec-evasion/penetration/persistence-maintenance/privilege-escalation/recon/reporting-remediation/vulnerability-triage。操作：新建 Agent（表单：文件名如 code-reviewer.md/id/name/tools/绑定角色/max_iterations）、编辑/删除。
- 机制：front matter 元数据 + 正文提示词；`max_iterations>0` 可覆盖全局 12000。

**27 角色管理 `#roles-management`（csai-27）**：13 张角色卡（emoji+名称+描述+工具范围「使用所有工具」+启用徽标）：默认/二进制分析/后渗透测试/容器安全/渗透测试/数字取证/信息收集/云安全审计/综合漏洞扫描/API 安全测试/CTF/Web框架测试/Web应用扫描。操作：创建角色（名称/描述/icon emoji/工具选择/启用）、编辑/删除、搜索。
- 机制：角色=「提示词+工具策略」打包，对话页选用；`roles/` 目录 12+ 预设。

### 2.4 平台管理区

**28 平台权限 `#platform-rbac`（csai-28）**：RBAC 台账——顶部计数（1 账号/4 角色/10 授权）；双 tab 成员管理+角色管理；用户区（按账号选择后管理角色与资源范围；admin @内置账号·10 项资源）；角色卡四档：**只读用户**（23 权限·指定资源）/ **审计员**（24 权限·全部资源·只读审计监控资产）/ **操作员**（50 权限·指定资源·不能管账号与核心配置）/ **管理员**（72 权限·全部资源）；角色权限/资源授权/变更记录 tab；新建角色/添加成员/编辑/删除。
- 机制：权限=「能做什么」（72 粒度，如 project:read），资源范围=「能看到哪些数据」（显式授权制）；变更留痕。

**29 系统设置 `#settings`（csai-29）**：左导航 12 分区——基本设置/人机协同/资产管理/知识库/C2/机器人设置/终端/安全设置/日志审计/存储清理/一键更新（+修改密码表单 auth-current/new/confirm）。要点逐区：
- **基本设置**：AI 通道管理器（通道列表：设为默认/复制/删除/编辑/**批量探活**；当前通道表单：提供商[OpenAI 兼容/Claude Anthropic]/Base URL/API Key/模型+获取列表/最大上下文 Token（默认 120000）/最大输出 Token（32768）/推理设置（mode auto|on|off、effort low..max、profile）/测试连接）；**视觉分析**（启用 analyze_image：独立 VL 提供商/密钥/模型 qwen-vl-max、图片字节上限 5MB、长边 2048、JPEG 质量 82、payload 上限 512KB、超限预处理、超时 60s）；Agent 配置（最大迭代 12000、工具单轮等待秒数[0=等到完成]、单 MCP server 并发[0=2,-1 不限]、全局并发[0=16]、熔断阈值[0=3,-1 关]、熔断冷却[0=60]、启用 Eino 多代理、plan_execute 外层循环上限、机器人默认对话模式）。
- **人机协同**：同 §2.1-03 的全局版（默认模式/审批方/等待时限/审计后端与模型/保留天数/全局工具白名单）。
- **资产管理**：FOFA/ZoomEye/Quake/Shodan 的 base_url+API Key（环境变量优先）。
- **知识库**：启用开关+base_path+embedding（provider/model/base_url/key）+检索（top_k/相似度阈值/子索引/多查询上限/rerank/后处理预取）+索引（超时/批大小/优先源文件/子索引列表/chunk 512/重叠 50/单项上限/RPM/限速延迟/重试）。
- **C2**：启用开关（`c2.enabled`；关掉则不启动监听器不注册 C2 MCP 工具）。
- **机器人设置**：8 渠道（个人微信[verify code/ilink]/企微[Token/AESKey/CorpID/Secret/AgentID]/钉钉[AppKey/Secret]/飞书[AppID/Secret/VerifyToken]/Telegram[BotToken+群开关]/Slack[Bot/App Token]/Discord[BotToken+Guild]/QQ[AppID/Secret/沙箱]）+漏洞告警开关+服务账号。
- **安全设置 / 日志审计 / 存储清理 / 一键更新**：登录保护；审计筛选（since/until/关键字：消息/资源 ID/操作名）；存储清理（auto_clean 开关+间隔+孤儿宽限 1 天+活跃宽限 24h+七类目录各自保留期：workspace 30d/reduction 7d/会话产物 30d/plantask 30d/c2 产物 30d/上传件 90d/工作流断点 7d/诊断日志 14d）；一键更新（更新源 repo 可改二开镜像，保留 roles/skills/tools/agents/data/config.yaml，仅同步 version 字段；命令行等价 `-update/-check-update/-update-rollback`）。

---

## 3. 核心机制原理（源码实证）

### 3.1 四种智能体编排
| 模式 | 原理 | 适用 |
|---|---|---|
| eino_single（Eino ADK 单代理） | 单 ReAct 循环：模型↔工具直调，挂 tool_search/plantask/reduction 中间件 | 默认；大多数单目标作业 |
| deep（DeepAgent） | orchestrator.md 主代理 + `task` 派子代理（16 个 .md 专家），主代理汇总交付 | 需要并行分工的大项目 |
| plan_execute | 规划器出计划→执行器逐步落地→重规划器修订；外层循环上限可配 | 目标明确的多步作战 |
| supervisor | 专家路由：transfer 委派对应专家子代理，exit 结束 | 按领域精准打点 |

本实例对话页默认 eino_single；批量队列卡实证出现过「Supervisor（专家路由）」模式任务。

### 3.2 工具执行治理（token/挂死/熔断三防线）
1. **渐进披露**：`tool_search_enable`——工具数 ≥20 时只把前 12 个（+`always_visible_tools` 白名单约 45 个内置）常驻上下文，其余进动态池按正则按需解锁 → 省 token、减误选。
2. **输出兜底（reduction）**：单条工具结果 >100000 字节 → 全文落盘 `tmp/reduction/.../trunc/<id>`，上下文只留 `<persisted-output>` 预览；历史工具结果超 60000 tokens 触发清理。DB 保存的与 Agent 看到的是**同一份兜底后结果**。
3. **异步等待**：阻塞型调用交 worker；`tool_wait_timeout_seconds`(300s) 到时返回 `execution_id`，Agent 用 `wait_tool_execution` 续等、`cancel_tool_execution` 取消；孤儿任务在 MCP 监控可见。
4. **熔断与并发**：单 server 并发 5（0=2，-1 不限）、全局 16、连续失败 15 次熔断 60s（UI 表单默认 3/60，config 注释以环境实测为准）。
5. **防挂死**：`shell_no_output_timeout_seconds` 连续无输出即终止；单工具时长上限 `tool_timeout_minutes: 60`。
6. **进程隔离**：`security.process_isolation`——Windows Job Object / Unix watchdog / Linux cgroup（systemd Delegate），max_processes 256、memory 2GB、CPU 配额可选；隔离失败**拒绝执行**（fail closed）。

### 3.3 上下文工程（长会话不崩的秘诀）
- **summarization**：上下文达 `max_total_tokens × 0.8` 触发压缩，输出预留 40960 tokens；
- **用户意图账本**：压缩后仍注入「原始用户输入与约束」账本（≤96000 字符，单条 ≤16000）——防长会话丢初心；
- **超长本轮输入**：>48000 字符的用户消息全文落盘，只注入头 24000+尾 24000 预览；
- **plan_execute 预算**：user_input 35%、executed_steps 20%、每步结果 ≤4000 字符、只保留最近 8 步正文；
- **悬空 tool_call 修补**：`patch_tool_calls` 修补流式中断产生的无 tool_call 结果历史。

### 3.4 安全治理双闸门（执行前）
```
Agent 决定调用工具(参数)
  → ① tool_guard：按规则顺序 RE2 匹配参数 → 命中→拦截，回提醒模板({match}/{tool}/{rule})
  → ② HITL：工具不在白名单(全局∩会话并集)？
       off        → 直接执行
       approval   → 挂起等人工/审计 Agent 放行或拒绝（默认 300s 超时）
       review_edit→ 挂起，可改参数后放行
  → worker 执行 → 结果兜底(reduction) → 回 Agent + 落 tool_executions(90d)
```
（顺序为手册归纳：guard 是硬闸、HITL 是人闸；两者独立配置、独立审计。）

### 3.5 数据与存储
- SQLite 双库：`data/conversations.db`（会话/消息/任务/漏洞/资产…）+ `data/knowledge.db`（知识项+向量，可独立复用）。
- 运行空间：`tmp/workspace/projects/{id}|conversations/{id}`（会话工作目录，curl 下载/本地分析落这里）；`tmp/reduction`（超长输出）；`tmp/c2`（C2 产物）；`chat_uploads`（上传件）；`data/workflow-checkpoints`（工作流断点）；`log/diagnostic-*.log`（诊断日志）。
- 审计：平台操作审计（不含对话正文与每次工具调用）保留 15 天；MCP 执行记录 90 天；HITL 决策日志 90 天。

### 3.6 视觉分析（analyze_image）
启用后注册 MCP 工具；图片**仅在单次 VL 调用中出现，Agent 上下文只保留文字摘要**（截图不污染对话）；原图 ≤5MB、长边缩到 2048、JPEG q82、编码后 ≤512KB、小图直传、超时 60s。

### 3.7 集成面
- **MCP 出口**：`mcp.enabled` 起 http server（默认 127.0.0.1:8081，`X-MCP-Token` 全局凭证或用户 Bearer Token；`allow_global_access` 为高风险兼容模式）；`cmd/mcp-stdio` 提供 stdio 模式；外部 MCP 联邦在 `external_mcp.servers`；`mcp-servers/` 自带 reverse_shell、pent_claude_agent 两个示例服务端。
- **Burp 插件 / 浏览器扩展**：DevTools 捕获流量发 CyberStrikeAI 做 AI 辅助测试（能力对齐）。
- **机器人**：8 渠道每条消息按 `robot_default_agent_mode` 走对应编排；支持漏洞告警推送。
- **API 文档**：页头入口（`web/templates/api-docs.html`），REST 全量见 docs/zh-CN/api-reference.md。

---

## 4. 完整渗透测试作战流程（端到端）

> 前提：**仅对自有/书面授权目标**。建议开局在对话里先声明授权范围，让 Agent 把边界写进事实黑板（engagement-planning 子代理的职责）。

```
Phase 0 授权与准备
  ├─ 平台权限→用户管理：给队员建账号(操作员/审计员角色)
  ├─ 系统设置→AI 通道(测试连接)、tool_guard 加"禁区域名"规则、HITL 全局策略
  └─ 装工具(nmap/nuclei/sqlmap...) + MCP 管理按需启停
Phase 1 立项与侦察
  ├─ 项目管理→新建项目(如"XX客户Web渗透")
  ├─ 信息收集→FOFA/ZoomEye/Quake/Shodan 四步向导→入库所选(进资产库)
  └─ 资产库→高级筛选(生产环境)→批量扫描 / 对话: "对项目内资产做攻击面测绘"
Phase 2 对话开战(核心)
  ├─ 对话页: 选项目+角色(渗透测试)+模式(单代理/Deep/PE/Supervisor)+模型
  ├─ HITL: 高危阶段切 approval; 敏感工具(exec/webshell_*)设白名单外
  ├─ Agent 自动: 调工具→record_vulnerability 入库→upsert_project_fact 写黑板
  └─ 人工: 盯计划面板/审批队列/MCP监控(失败与拦截)
Phase 3 验证与治理
  ├─ 漏洞管理: 逐条 复测/改状态(待处理→已确认/误报)
  ├─ 项目管理→事实黑板: 固化 exploit/poc 事实(置信度=可复现)
  └─ 攻击路径 tab: 检查链完整性
Phase 4 (授权内)利用与后渗透
  ├─ C2: 创建监听器→载荷页生成 oneliner/编译 Beacon→投递→会话管理
  ├─ C2 任务: shell/exec/download/screenshot...; 事件页盯 OPSEC
  ├─ WebShell: 添加连接(冰蝎/蚁剑)→批量探活→对话里让 AI 直接操作
  └─ 流量伪装 Profile 套壳
Phase 5 报告与复盘
  ├─ 工作流: "用自然语言创建"→勾 报告审批/资产研判→生成草稿→修节点→试运行
  ├─ 批量任务: cron 周期复测(漏洞回归)
  ├─ 漏洞管理→批量导出 / 文件管理导出附件
  └─ 知识库: 把可复用手法入库(下次 RAG 检索直接命中)
```

**每日运营节奏**（仪表盘驱动）：早上看「待处理高危+从未扫描资产」→ 中午跑批量队列 → 晚上看 MCP 监控失败率与 Token 消耗 → 周末清审计与存储。

---

## 5. 架构设计

### 5.1 技术栈与目录
Go 1.25 后端（cmd/server 主入口）+ Eino 智能体框架 + SQLite（双库）+ 原生 JS/hash 路由 SPA（`web/static/js` 84 个模块：chat.js 485KB、c2.js 221KB、router.js、tool-guard.js、hitl…）+ Python venv（部分工具如 http-framework-test）。目录职责见 README「项目结构」+ 本地实证：`tools/`(139 YAML 配方) `roles/`(13) `skills/`(23) `agents/`(16 .md) `mcp-servers/`(2 示例) `plugins/`(Burp+浏览器扩展) `docs/zh-CN/`(34 篇专题)。

### 5.2 internal/ 模块职责（目录名实证，语义按命名与文档）
| 模块 | 职责 |
|---|---|
| agent / multiagent / agents | 单代理执行器、多代理编排（Deep/PE/Supervisor）、.md Agent 加载 |
| einomcp / einoobserve | Eino↔MCP 工具桥、回调观测（Zap+OTel） |
| toolguard / hitl / processguard | 执行前正则拦截、人机协同审批、进程隔离 |
| tooloutput / monitor | 工具输出兜底(reduction)、执行记录观测 |
| project / attackchain / knowledge | 项目与事实黑板、攻击链图谱、RAG 知识库 |
| c2 / robot / workflow | 内置 C2 全家桶、8 渠道机器人、工作流引擎 |
| authctx / audit / security / runlease | 认证上下文、操作审计、安全配置、运行租约 |
| database / storage / update / vision / reasoning / termout / typesafe / skillpackage / agentfinalizer / projectprompt / llm / openai / logger / config / app / handler | 持久化、存储清理、一键更新、视觉分析、推理参数、终端输出、TypeSafe 审计后端、技能打包、Agent 收尾、项目提示、模型抽象、日志、配置、应用装配、HTTP 路由 |

### 5.3 总体逻辑架构（ASCII）
```
┌─────────────────────────── 客户端层 ───────────────────────────┐
│ Web SPA(hash路由) │ Burp插件 │ 浏览器扩展 │ 8渠道机器人 │ REST/MCP客户端 │
└──────────────┬────────────────────────────────────────────────┘
               │ HTTPS(自签/正式) + SSE流式
┌──────────────▼───────────── 应用层 (cmd/server) ───────────────┐
│ handler(路由) → authctx(RBAC/会话) → audit(操作审计)            │
│ ┌──────────────────── 智能体执行层 ────────────────────┐       │
│ │ eino_single │ Deep │ Plan-Execute │ Supervisor       │       │
│ │   (中间件: tool_search / plantask / reduction /      │       │
│ │    patch_tool_calls / summarization / skill 渐进披露) │       │
│ └──────┬───────────────────────────────────────────────┘       │
│        ▼ 每次工具调用                                          │
│ ┌─ 治理链 ─────────────────────────────────────────────┐       │
│ │ toolguard(RE2规则) → hitl(白名单? off/approval/       │       │
│ │ review_edit; human 或 audit_agent[openai/typesafe])  │       │
│ └──────┬───────────────────────────────────────────────┘       │
│        ▼                                                       │
│ einomcp ──► 139 内置工具(tools/*.yaml) ──► 本地二进制/Python     │
│      └────► external_mcp 联邦(http/stdio/SSE, 并发+熔断)        │
│        │  (worker 异步: execution_id 续等/取消; 进程隔离        │
│         processguard: cgroup/JobObject, 2GB/256proc)           │
│        ▼ tooloutput 兜底落盘 tmp/reduction                     │
│ ┌─ 数据层 ─────────────────────────────────────────────┐       │
│ │ SQLite: conversations.db(会话/项目/事实/资产/漏洞/任务) │      │
│ │         knowledge.db(知识+向量)                       │       │
│ │ 文件: tmp/workspace|reduction|c2, chat_uploads,       │       │
│ │       workflow-checkpoints, log/diagnostic            │       │
│ └──────────────────────────────────────────────────────┘       │
│ 横切: monitor(执行观测) storage(定时清理) update(一键更新)        │
│       c2(监听器/Beacon/会话/事件) robot(消息接入)                │
└────────────────────────────────────────────────────────────────┘
```

### 5.4 对话执行时序（含卡点）
```
用户 ──意图──► 编排器(eino_single/Deep/PE/Sup)
                 │ (上下文工程: 意图账本/摘要/超长输入截断)
                 ▼
              模型(GLM/Qwen/Claude, 通道+failover)
                 │ tool_call(name, args)
                 ▼
     [tool_guard 正则闸] ─命中─► 拦截+提醒模板 ─► Agent 改道
                 │通过
                 ▼
     [HITL 闸] 非白名单且模式≠off ─► 挂起 ─► 人工/审计Agent(可改参) ─► 放行/拒绝
                 │放行
                 ▼
     worker 执行(进程隔离, 并发/熔断, 无输出看门狗)
                 │ 结果(>100KB 落盘留预览)
                 ▼
     Agent 继续 ReAct …循环(≤12000 迭代)… ► final_answer
                 │
                 ▼
   副作用: record_vulnerability / upsert_project_fact / create_asset
   观测: tool_executions(90d) + HITL 决策日志 + 事件流
```

### 5.5 数据模型关系
```
Project 1─* Conversation 1─* Message ─* tool_execution
   │1                                    (工具观测, 90d)
   ├─* Fact(黑板: key/分类/置信度/关系↑↓)
   ├─* Asset(目标/服务/标签/归属/扫描覆盖) ─* Vulnerability
   │        └─ 信息收集(FOFA等) ─入库─┘        (五状态机+复测)
   ├─* AttackChain 节点(由 chain/finding 事实推导)
   └─* BatchTaskQueue 1─* 子任务(cron/并发/暂停)
Workflow(节点图: 开始/工具/Agent/条件/审批/输出/结束, checkpoint 7d)
User ─*─ Role(RBAC: 72 权限) ─*─ ResourceScope(资源授权)
```

---

## 6. 配置速查（config.yaml 主要段·默认值）

| 段 | 关键项（默认） | 说明 |
|---|---|---|
| server | host 0.0.0.0 / port 8080 / tls_enabled / tls_auto_self_sign / cors_allowed_origins | 本实例 8443+自签；HTTP 自动 308 跳 HTTPS |
| auth | session_duration_hours 12 | 登录有效期 |
| ai | default_channel + channels.<id>{provider, base_url, api_key, model, max_total_tokens 120000, max_completion_tokens 32768, reasoning{mode/effort/profile}} | 多通道；failover 见 eino_middleware.model_failover_channels |
| agent | max_iterations 12000 / tool_timeout_minutes 60 / tool_wait_timeout_seconds 300 / 并发 5+16 / 熔断 15 次 60s / shell_no_output 1200s / workspace_root_dir | 全局执行参数 |
| tool_guard | enabled + rules[]{pattern(RE2), message({match})} | Web 保存即生效 |
| hitl | default_mode off / reviewer human / timeout 300 / audit_backend openai|typesafe / tool_whitelist | 与对话级合并并集 |
| multi_agent | enabled / robot_default_agent_mode / batch_use_multi_agent / plan_execute_loop / orchestrator_instruction* / eino_skills{filesystem_tools} / eino_middleware{tool_search*, reduction*, summarization*, plantask*, model_retry/failover} | 多代理与上下文工程总开关 |
| knowledge | enabled false / base_path / embedding / retrieval(top_k 5…) / indexing(chunk 512/overlap 50…) | RAG 全参 |
| security | process_isolation{mode auto, max_processes 256, memory 2GB, cgroup_root} / tools_dir / tool_description_mode full | 工具与隔离 |
| mcp / external_mcp | enabled false / 127.0.0.1:8081 / X-MCP-Token / servers{} | 出入口 |
| c2 | enabled true | 关=不注册 C2 工具 |
| database | conversations.db / knowledge.db | SQLite 双库 |
| audit / monitor / storage / log / update | 15d / 90d / 七类目录保留期 / level info / 更新源 repo | 运营治理 |

（权威模板：`config.example.yaml`；专题文档：docs/zh-CN/{configuration, configuration-profiles, security-hardening, tool-call-guard, hitl-best-practices, tool-execution-governance, MULTI_AGENT_EINO, c2, webshell, workflow-graph, rbac, knowledge-base, asset-management, mcp-federation, api-reference, deployment, runbooks, security-model}.md）

---

## 7. 安全模型与合规边界
- **授权红线**：仅自有/明确授权目标；C2/WebShell/高风险工具启用前先读 security-model 与 security-hardening。
- **四层防误伤**：tool_guard 禁区正则 → HITL 人工/审计 Agent → RBAC 资源范围 → 进程隔离资源上限。
- **审计三账**：操作审计（15d）/ 工具执行（90d）/ HITL 决策（90d）；诊断日志按日拆分 14d。
- **密钥卫生**：情报源 Key 后端代理（前端不暴露）；MCP 全局凭证仅高风险兼容模式；config 不入库不提交。

## 8. 常见任务速查
| 我想… | 去哪/怎么做 |
|---|---|
| 把 FOFA 结果变资产 | 信息收集 4 步 → 勾选 → 入库所选 |
| 让 AI 自动复测漏洞 | 漏洞管理 → 行内「复测」；或对话「复测项目里所有待处理漏洞」 |
| 限制 AI 不打某域名 | 调用拦截 → 添加规则（RE2）→ 全部规则验证 → 保存并生效 |
| 高危操作要人批 | 对话会话设置 hitl-mode=approval（或人机协同页设全局） |
| 100 个资产跑同一句指令 | 任务管理 → 新建任务（多行子任务/cron） |
| 给 AI 一个本地大文件 | 文件管理上传 → 复制路径 → 对话粘贴路径 |
| 省 Token | MCP 管理关闲置工具；tool_description_mode=short；tool_search 已默认开 |
| 出报告 | 工作流 → 用自然语言创建（勾报告审批）→ 生成草稿 → 修 → 试运行 |

## 附：截图索引
`../liveui/shots/csai-00-登录.png` … `csai-29-系统设置.png`（与 §2 编号一一对应，共 30 张 full_page）。

---
*维护: 漫游舰（界面实证）+ 源码只读 · 下一版待补: api-reference 摘要、workflow-graph 专题、多代理实测对比 · 零 git*

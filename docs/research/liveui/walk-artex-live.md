# ARTEX 活体巡访实录（walk-artex-live · 批#1）

> 巡访日期：2026-10-16 14:00–14:10（CST）· 巡访者：界面漫游舰（探隐委托，无图像能力，全 DOM/API 文本层）
> 对象：ARTEX @ http://localhost:8787（Docker dev 版，用户 ARTEX 账号本地授权登录）
> 装备：python3 + playwright，channel="chrome" headless 1440×900，全部导航 wait_until="domcontentloaded"（未用 networkidle）
> 焦点：**用户真跑的战斗**——任务列表、发现列表（标题/严重度/状态）、意图链结构、预算/暂停行为、报告长相；每个结论附 DOM/API 证据。
> 姊妹篇：CSAI 侧见 walk-csai-live.md，靶场侧见 walk-zhulong-live.md，改进清单见 live-recon-1.md。

## 只读纪律执行声明

- 全部写操作仅一处：登录 POST（用户书面授权的本地凭据，凭据不入档）。
- 其余全部为 GET 导航 + 任务详情页签切换（role=tab 纯视图切换）+ 被动监听 XHR（只记录 URL 与响应体）。
- **未点**：新建任务/暂停/恢复/重命名/归档/删除/复测/深入/导出/保存/启用——一个都没有。任务 #1 当前处于「已暂停」态，这是用户自己的状态，巡访全程未改变。
- 附加观测：登录页《使用须知》条款弹窗打开并滚动到底后以「同意」收口（登录前置条件，未同意无法登录）。

## 0. live 快照事实（2026-10-16 14:0x 实测）

| 项 | 实测值 | 证据 |
|---|---|---|
| 任务 | #1「烛龙靶场渗透测试」，**已暂停**（paused=true, engine_mode=paused, running=false, in_flight=0） | /api/stats?task=1 响应体 |
| 任务创建 | 2026-10-15T05:41:04Z（=CST 13:41），运行时长 23h 26m | /api/tasks 响应 + 任务中心 DOM「10-15 13:41  23h 26m」 |
| 发现 | **51 个全部 pending**：严重 9 / 高危 20 / 中危 15 / 低危 7 | /api/exploration/findings/stats；仪表盘 DOM「确认发现 51 严重 9 高危 20 中危 15 低危 7」 |
| 图谱 | 节点 260（fact 79 / intent 74 / digest 55 / finding 51 / goal 1）+ 边 359（src/dst/rel 三元组） | /api/exploration/graph?task=1 |
| 资产 | 132（endpoint 63 / service 51 / ip 11 / root_domain 4 / subdomain 2 / app 1） | /api/stats?task=1 asset_counts |
| 覆盖度 | **33%**（已测 40 / 范围内 122；app 0/1·endpoint 8/63·ip 5/5·service 27/51·subdomain 0/2），scope_rows 9 | /api/tasks/1/coverage |
| Token | 总 187.9M = 入 185.7M（含缓存读 177.3M）+ 出 2.2M；**缓存命中率 95%**；glm-5.3 共 3946 次调用 | 仪表盘 DOM + 总览页签 DOM（LLM Token 用量表） |
| 审批 | 全部记录 **37 条**，逐条含工具/来源/匹配规则/参数 JSON/状态/双时间戳 | 拦截审批页签 DOM「全部记录（37）」+ /api/intercept/task/1 |
| 复测 | 活跃复测 0 条（retests:[]） | /api/exploration/findings/retests/active |
| 报告 | 「渗透测试报告（Markdown）」已生成，生成时间 **2026-10-16 05:49:50**，摘要含确认发现 51 + 资产分布 | 报告页签 DOM |
| 对话页 | 会话列表仍为空（主对话入口未用，战斗全在任务引擎里） | /api/conversations + 对话页 DOM |

**与 2026-10-15 首轮漫游（walk-artex.md）的差分**：发现 39→51（+12，严重 7→9）、资产 105→132（+27）、审批 19→37（+18）、Token 73.3M→187.9M（×2.56）、任务态 运行中→**已暂停**、worker 3 在途→0 在途。说明用户在 15 日下午到 16 日凌晨又打了一整轮然后暂停收口。

## 1. 登录层（DOM 实证）

- 表单：用户名输入框 **readonly**（id=username，value=ARTEX 预填）+ 密码框 + 「我已阅读并同意《使用须知》」复选框（id=agree-terms）+ 登录按钮。
- **登录按钮初始 disabled**——勾选 agree-terms 才解禁；《使用须知》按钮弹出条款弹窗（滚动到底才能同意的交互在弹窗内）。
- 登录成功后跳 /function/tasks，token 存 localStorage.artex_token（实测存在），API 走 Bearer。

## 2. 仪表盘（/dashboard）

六统计卡 DOM 顺序：活跃任务 0/1（副注「暂停 1」）→ 确认发现 51（严重 9·高危 20·中危 15·低危 7）→ 资产节点 132（「跨任务共享」）→ 流量交互 6（「捕获未开启」）→ Token 用量 187.9M（「入 185.7M（含缓存 177.3M）·出 2.2M」）。
LLM Token 消耗面板：旧版/新版切换 + GLM 筛选 + 时间粒度（7天/30天/3月/6月/一年）；三段分解「输入(未命中) 8.5M / 缓存命中 177.3M / 输出 2.2M / 缓存命中率 95%」。
**活动流（用户战斗的一手证据）**：25 条事件按类型计数（tool_use 7 / tool_result 7 / text 3 / thinking 5 / result 1），每条带作者（planner）+相对时间（1d 前）。实测样本：
- planner · add_intent：`{"intents":[{"parent_ids":[1],"priority":8,"summary":"确认 http://localhost:3081 服务可达（规划时直连 Connection refused，服务可能仍在启动，需带重试/等待）并做指纹侦察…"}]}` ——**规划者把「靶场当时宕机」直接写进意图带重试**，这是活体里罕见的自愈行为证据。
- planner · add_task_scope：把 127.0.0.1 纳入授权边界（「任务目标即 http://localhost:3081…将其纳入任务授权边界与覆盖度分母」）。
- planner · text（中文推理独白）：「规划者直连 127.0.0.1:3081 被拒（可能服务仍在启动）——…我先锚定任务范围，再批量提交初始探索意图」。
- planner · thinking（英文思考）：「The target on localhost:3081 currently refuses connections…」。

## 3. 任务中心（/function/tasks）

- 双页签 当前任务/已归档 + 状态/分类筛选；工具位：并发设置、分类管理、**新建任务**、20条/页。
- 表列（DOM 原文）：ID/名称/描述/目标/状态/目标进度/漏洞 严·高·中·低/运行中 Worker/创建时间/运行时长/Token/操作。
- 唯一一行：#1 烛龙靶场渗透测试 · 描述「渗透测试http://localhost:3081(用户名 admin,密码***)」· 目标「竟可能多识别漏洞」· **已暂停** · 0/1 目标 · 漏洞 9/20/15/7 · Worker 0 · 10-15 13:41 · 23h 26m · **入 186M · 缓 177M · 出 2.2M**（Token 三段式内联在行里）。
- 行内操作（未点）：重命名/暂停或恢复/置顶/归档/删除。

## 4. 任务详情十页签（/function/tasks/detail?id=1）——战斗主舱

sticky 头（DOM）：「烛龙靶场渗透测试 | 1 | GLM | 已暂停 | **恢复** | 竟可能多识别漏洞」——**暂停/恢复是任务级主刹车，按钮就在头带**。
页签清单（role=tab 顺序）：会话 / 总览 / 探索链路 / 播报板 / 发现 / 复测 / 测试资产 / 资产覆盖图 / 拦截审批 / 报告。

### 4.1 会话页签 = workers 实时流
- 顶部 TokenMetrics：「任务总计 · 入 186M · 缓 177M · 出 2.2M」+「实时」蓝脉冲徽标（暂停态下仍显示累计值）。
- 会话列表四分组：主 Agent·会话 #1（新建钮）/ 规划 Planner·态势研判 / 系统审计·LLM 故障转移 / Workers。
- Workers 分组每行 = **意图号 + 意图全文摘要 + 实时徽标**。实测挂账 worker：#260（宿主 0.250.250.254 三个零覆盖 HTTP 服务定向定性：631=CUPS/10010=Docker API 风格/49209=Go http）、#255（localhost:32850 高端口未知服务定性，known_hosts 交接线索）、#249（Multica daemon ws 版本门闭环与任务劫持实证）。
- **意图正文自带红线条欿**（逐字证据，#260）：「红线：不打公网、只读优先、任何写操作须可逆」「【绝不向真实物理打印机发送任何任务、不修改既有打印机配置】」——planner 在意图里写 ROE，worker 按此执行。
- 输入框常驻：「给主 Agent 发消息，@ 引用漏洞、资产等…」+ 上传文件。

### 4.2 总览页签 = 任务治理面板
DOM 分区逐项：任务描述与目标（**「新增/修改会通知规划者并复活任务」**微文案）→ 目标管理（1 条进行中）→ 操作约束（禁/允 0 条；「建任务时会自动从描述/目标抽取；也可手动增删改」）→ 任务级资产拦截/允许（匹配类型七种：域名全等/IP 全等/URL 全等/域名模糊/IP 模糊/URL 模糊/CIDR 网段；「允许=白名单，配置后只测命中项」）→ 资产测试覆盖度 33%（已测 40/122 + 五类分解）→ LLM Token 用量表（模型 调用 输入 输出 缓存读 命中率：glm-5.3 · 3946 · 186M · 2.2M · 177M · 95%）→ 测试范围 9 条（每条带来源徽标 Agent/自动：localhost 子域名·Agent、127.0.0.1/32·Agent、0.250.250.254/32·Agent、192.168.139.66/57/58·Agent、artex-postgres-1.orb.local·自动、multica-postgres-1.orb.local·自动、192.168.0.103·自动）→ 心跳（引擎态 已暂停 · 运行中 Worker 0 · 最近活动 —）→ **需要关注**四数：51 确认漏洞 / 0 执行中 / 3 frontier 待领 / 9 被拦意图 → 最近发现卡。

**预算/暂停行为实测结论**：ARTEX 无硬预算上限设置（设置页无预算字段，只有工作并发 Worker 数）；「预算」以 Token 三段累计（入/缓存/出）呈现在 任务行、会话页 TokenMetrics、总览页签按模型表、仪表盘四个位置；暂停是任务级开关（头带「暂停/恢复」），暂停后 in_flight=0、心跳「最近活动 —」、frontier 意图留在待领池（3 条）等待恢复——**暂停不清空意图队列**。

### 4.3 探索链路页签 = 意图/事实/发现血缘图
- 画布为 React Flow（DOM 文本仅少量），但 API 全量可读：/api/exploration/graph?task=1 → 260 节点 + 359 边，节点 kind 计数 fact 79 / intent 74 / digest 55 / finding 51 / goal 1；边结构 {src, dst, rel}（spawns/derived_from/yields/proves 语义来自源码）。
- **意图链结构**（/api/exploration/intents?task=1，74 条）：字段 = id / type / payload(JSON 摘要全文) / priority / state / origin / ts。实测样本：#260 priority=6 state=open origin=planner ts=2026-10-15T13:25:20Z；#249 priority=8 state=open。**priority 是数字（实测见 6/8），state 词汇 open，origin 词汇 planner**——意图是 planner 发的全中文作战命令，一段 300–800 字，含背景交接（引用 fact#/finding# 编号）+ 分步计划 + 红线。
- digest 节点 55 个 = 上下文压缩产物（与播报板「压缩」事件对应，compactor 生成）。

### 4.4 播报板页签 = 图事件直播流
- 筛选六类：目标/意图/事实/漏洞/提示/**压缩** + 最新在前 + 自动刷新开关。
- 事件卡结构：时间（绝对+相对「16 小时前」）·类型徽标·#id·状态（待领/生效中）·P 优先级（P6/P8）·作者（planner/work#N/compactor）·正文全文。
- **压缩事件实证**（#259，作者 compactor，状态 生效中）：把「后端 apps/server 源码静态审计（#20）确立的三条代码级攻击面」整段收口成一条 digest——三条线各带动态验证链编号（#33→#37→#47 等）与结论等级。这是 ARTEX 的**战地记忆压缩机制**：不丢结论、丢过程。

### 4.5 发现页签（任务内）与 /function/findings（跨任务）
- 51 条全部 status=pending（**ARTEX 没有人工终审状态机**，发现只有严重度四档，无 已确认/误报 生命周期）。
- 每条字段（API）：finding_id/vulnclass/name/**summary（超长正文，含攻击链+实测边界+修复建议）**/severity/status。
- **51 条标题全录**（severity 编号 标题，凭据类内容已脱敏）：
  - 严重×9：#45 Multica 任务投递面伪造会话直达宿主机 RCE；#44 Multica/ARTEX Postgres 容器直连全失陷（COPY TO PROGRAM 容器 RCE）；#34 CSAI 凭据复用→admin 令牌→terminal:execute 宿主机 RCE；#33 ARTEX 自定义工具接口=控制台接管即容器 root；#30 cloud-lab k3s 集群接管写侧实弹（system:masters→privileged hostPath pod）；#13 ZL-VulnLab /ping?host= 未认证命令注入宿主机 RCE；#15 ZL-VulnLab /file?name= 路径穿越读到 ZhuLong master.key；#10 ZhuLong 内置引擎 sandbox:'none' 宿主机任意命令执行；#3 Vite /@fs 未认证下载 zl.db 全库泄露。
  - 高危×20（节选）：#51 Multica daemon 控制面零隔离（幽灵 runtime/替心跳/污染任务结果）；#48 dsh web(3080) 浏览器会话签名密钥泄露→AI 控制面接管；#43 探隐观察面(8900) 零认证泄露评估账本；#41 ZhuLong 7090 零来源校验+CSRF 面；#38 Multica JWT_SECRET 会话伪造动态闭环；#36 runner chunk sha256 穿越→存储型 XSS；#35 烛龙任务产物 /@fs 零认证泄露（跨用户+AI 会话转录）；#31 OrbStack 容器层 root 免密直入；#29/#28 CSAI/ARTEX 跨系统口令复用→接管；#25 文档上传+Vite /@fs 同源渲染→零认证存储型 XSS；#23 宿主机多平台明文凭据全套泄露；#22 k3s kubeconfig 接管；#21 /api/imports sourceDir 任意目录读取；#20 runner 分片上传路径穿越任意文件写；#19 私有文档 /@fs 零认证泄露；#16/#17/#12 ZL-VulnLab SQL 注入/SSRF/未授权暴露；#9 zl.db 泄露链下低权账号离线爆破成功；#4 Vite /@fs 未认证读后端源码。
  - 中危×15（节选）：#50 ZhuLong 环境探活 SSRF 多类通用绕过（私网/整数 IP/IPv4-mapped/短 TTL rebinding）；#49 CSAI config/test-* 认证后 SSRF；#47 Multica webhook 签名可选跳过；#37 ARTEX 8788 MITM 代理未认证开放；#27 ZhuLong 重置密码不清锁定计数；#26 禁用用户不吊销会话；#7 探活 SSRF nip.io 绕过；#6 后端 7090 直接暴露；#2 登录锁定 DoS；#11 管理员重置密码不吊销会话（CWE-613）。
  - 低危×7：#46 vault 密钥与密文同目录；#40 daemon /health 零认证状态泄露；#32 workspace 存在性枚举 oracle；#14 imports 授权检查后置探测 oracle；#8 密码策略仅校验长度；#5 登录报文差异用户名枚举；#1 Vite dev server 暴露。
- **战场蔓延实测**：51 条覆盖 ZhuLong(3081/7090)、ZL-VulnLab(5050)、Multica(3000/8080/19514)、CyberStrikeAI(8443)、dsh web(3080)、探隐观察面(8900)、ARTEX 自身(8787/8788)、cloud-lab k3s、OrbStack 容器层、宿主机本身（0.250.250.254 的 CUPS 631/Docker API 10010/49209/32850、SSH 私钥、远控 nonce、LLM API keys）——**一句「测 localhost:3081」的授权，实测打穿了整个评测网络与宿主**。授权边界（测试范围 9 条）是 planner 自己扩的（每条带 Agent/自动来源标注），任务级资产拦截/允许规则 0 条（用户没用）。

### 4.6 复测页签
- DOM：「4 张待复测卡」在 10-15 漫游时存在；本次 /api/exploration/findings/retests/active → `{"retests":[]}`（**当前活跃复测 0**）。发现行内「复测/深入/删除」操作在（未点）。

### 4.7 测试资产 / 资产覆盖图页签
- 测试资产：六类计数 + 资产行 + 移出 + 50/页。
- 覆盖图：G6 力导向画布（DOM 文本仅 290 字符级），数据源 /api/tasks/1/coverage-graph；与 4.3 的分工——4.3 画推进链（意图血缘），本页画资产覆盖。

### 4.8 拦截审批页签（任务级）与 /system/intercept/approvals（全局）
- DOM：「全部记录（37）」+ 表列：# / 工具 / 来源 / 匹配规则 / 参数 / 状态 / 申请时间 / 决定时间 + 展开详情。
- 实测记录（API 全文可读）：
  - #37 · Bash · work#3·#215 · [内置] 破坏性系统命令 · **已拒绝**：命令含 `dd if="…/ToDesk/ai/ZAgent.app/Contents/MacOS/zagent" bs=1 skip=107850300`——worker 想用 dd 读远控二进制找凭据，被内置规则拦（「破坏性命令被拒绝（rm -rf / / mkfs / dd / fork bomb…）」）。
  - #36 · Bash · work#2·#214 · [内置] curl/wget 发送 DELETE 请求 · **已拒绝**：worker 清理战场想 DELETE http://0.250.250.254:3081/api/environments/14，被拦。
- 结构字段（API）：id/rule_id/agent_name(work#N·#意图)/tool_name/tool_input(完整 JSON)/status/decision_source(**rule**)/reason/decided_at/created_at。**本批 37 条 decision_source 全部是 rule（内置正则），无人工待审积压**——审批流是「规则先行，人不在环」。

### 4.9 报告页签 = 渗透测试报告（Markdown）
- DOM：标题「渗透测试报告（Markdown）」+ **复制**按钮 + 正文渲染。
- 头部：「渗透测试报告 — 渗透测试http://localhost:3081(用户名 admin,密码***)。」「任务目标：竟可能多识别漏洞」「**生成时间：2026-10-16 05:49:50**」。
- 摘要节：确认发现 51 个 + 资产分布（app 1、endpoint 63、ip 11、root_domain 4、service 51、subdomain 2）。
- 正文：编号发现列表「1. [CRITICAL] Multica 任务投递面经伪造会话直达宿主机命令执行（agent runtime 驱动链）」，每条 = 长正文（攻击链分步①②③④⑤）+ 「PoC / 证据：」段（原始请求/响应、lsof pid、数据库行证据、修复段）。**报告=发现的 summary 直渲染，无独立报告编辑器**；/api/report?task=1 提供机器可读版。

## 5. 其余功能页快记

- /function/traffic：录制代理「已停用」状态 chip + 6 条历史（表：时间/host/方法/URL/状态码/content-type/响应长度）+「关联到漏洞」批量证据绑定。
- /function/commands：命令流水表（任务/命令/状态/时长）。
- /function/assets：六类计数卡 + DSL 搜索。
- /system/intercept：命令拦截规则（内置 20 条正则，优先级 100/90/80 分层）+ 拦截范围 8 工具 + 模型配置页签（LLM judge）。
- /system/intercept/assets：资产级黑/白名单（空态）。
- 对话页 /chat：会话列表空（主 Agent 对话入口闲置）。

## 6. 只读 API 地图（被动捕获 60 个 GET，全部 200）

auth/status · intercept/pending · companies · llm/profiles · health · task-categories · tasks · update/check · exploration/activity?limit=30 · tokens/conversations · settings · exploration/findings · assets/counts · mcp · stats · traffic?page=0&size=50 · exploration/tokens · agents · tools · tokens/usage?days=365 · skills · conversations · findings/retests/active · findings/stats · findings?sort=severity · traffic/hosts · commands · intercept/tool-config · intercept/rules · intercept/history · tasks/1 · intercept/task/1 · stats?task=1 · tasks/1/chat/status · exploration/tokens?task=1 · tasks/1/llm/resolution · exploration/main-sessions?task=1 · **exploration/intents?task=1** · exploration/activity/history?session=main:0 · tasks/1/intent-assets · tasks/1/chat/side-questions · exploration/activity/stream(SSE) · tasks/1/intercept-rules · tasks/1/goals · tasks/1/constraints · tasks/1/scope · llm/records/by-model?task=1 · findings?task=1 · **tasks/1/coverage** · **exploration/graph?task=1** · exploration/nodes · findings?task_id=1&sort=time · findings/51/retests · assets?task_id=1&type=root_domain · **tasks/1/coverage-graph** · **report?task=1**

（SSE 端点 exploration/activity/stream 用 ?token= 携带 JWT——EventSource 不能带自定义头的官方解法。）

## 7. 给探隐的观察（详见 live-recon-1.md）

1. **任务级主刹车=暂停/恢复**，在 sticky 头；暂停不清意图队列（frontier 3 条待领存活）——恢复即续战。
2. **预算无硬顶**，只有 Token 三段累计呈现（四处一致）；缓存命中率 95% 是成本故事的主角。
3. **意图=全中文作战命令**（背景+分步+红线+编号引用），planner 自带 ROE 红线句式（「不打公网、只读优先、任何写操作须可逆」）。
4. **压缩（compactor digest）是战地记忆管理**：55 个 digest 节点 + 播报板「压缩」事件，结论保留过程折叠。
5. **发现无生命周期**（51 条全 pending），复测机制有（retests API + 行内按钮）但当前零活跃。
6. **报告=发现 summary 的 Markdown 直渲染**+复制按钮+生成时间戳，机器可读 API 同源。

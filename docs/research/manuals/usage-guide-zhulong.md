# 烛龙 ZhuLong 使用手册（实时滚动版 · 2026-10-16 起）

> 状态: **完整版 v1**（活体巡访批#1 实机实证 + 源码只读充实）。更新时间: 2026-10-16。
> 系统: http://localhost:3081（本实例为 pnpm dev 栈：apps/server tsx watch @7090 + apps/web vite @3081）；本地源码: `ai-assisted-security-verification-platform`（pnpm monorepo，Vue 3.5 + Hono + better-sqlite3，Apache 系内部项目）。
> 定位句: 「睁眼为昼，照穿一切暗处」——AI 安全验证平台（安全评测靶场与红队引擎的中枢管理面）。
> 实证材料: 活体巡访 `../liveui/walk-zhulong-live.md`（2026-10-16 批#1）+ 首轮漫游 `../liveui/walk-zhulong.md`（27 视图）+ `../liveui/4-zhulong.md`（源码深析）；本手册界面章节的按钮/参数均来自实机 DOM 与 open-then-cancel 表单取证，机制章节来自 `apps/server/src/` 源码实读。
> 注意: 本实例同时是**被渗透测试的靶场**（ARTEX/CSAI 的战斗对象）——库内含攻击者留下的行，手册 §9 有交叉索引。

---

## 0. 定位与能力总览

**它是什么**：面向「AI 安全验证」的靶场中枢——把**项目/对象/环境**组织成测试资产，把**引擎**（AI 红队 CLI，插件制注册）挂到**算力资源池**（本机 CLI 自动探测 + 远程 runner 接入令牌）上跑任务，把 runner 产出的会话日志经**映射器（mapper）**解析成结构化漏洞，再走**三态人工终审**（疑似/确认是/确认非）收口，最后经**下载中心**交付报告。一句话：**资产组织 × 引擎调度 × 漏洞终审**三合一的验证平台控制台。

**能力矩阵**（★=本实例已启用实证，2026-10-16）：

| 域 | 能力 | 本实例状态 |
|---|---|---|
| 项目 | 项目（业务域 web/host/k8s/mobile/other + 敏感标记 + 按角色加成员） | ★ 10 项目在册 |
| 任务 | 七桶状态机（排队/运行/成功/失败/已取消/软删）+ 引擎×模式×环境×算力四维建单 + 阶段进度 + 失败原因原文 + 建单锚 | ★ 14 任务（5 成功/5 失败/3 取消/1 软删） |
| 引擎 | 插件制（manifest 注册 + 版本行 + 启停裁定 + 参数按 manifest 声明动态渲染）；内置 demo/GenCPT/GenLPE + 外部 tanyin（探隐红队）/zhulong | ★ 5 引擎在册，zhulong 产出 13 findings |
| 模式 | 开眼=广域照亮（广域探索）/ 吐焰=定点灼穿（深度挖掘） | ★ 全部任务用开眼 |
| 算力 | 路径一自动接入（本机 CLI 探测入池）+ 路径二手动接入（provision token 注册远程 runner）+ 心跳/失联宽限/机器槽 | ★ 7 接入（1 自动 6 手动），1 在线 |
| 资产 | 测试对象（代码/文档，上传或本机路径，版本指纹）/ 测试环境（endpoint+凭据+健康检查 SSRF 闸门）/ 知识图谱（19 漏洞类·227 合规规则·5 提权族） | ★ 7 对象 / 9 环境 |
| 漏洞 | 严重度五档 + **三态终审** + PoC 四元组（静态/动态/前置/验证）+ 标注时间线 + 导出 | ★ 13 findings（11 疑似/1 确认是/1 确认非），确认率 8% |
| 治理 | RBAC 三角色（管理员/安全工程师/漏洞审计员）+ 审计日志全写面 + 登录锁定 + scrypt 口令 + 会话 TTL + 全库凭据加密（master.key） | ★ 4 用户；审计在库 |
| 运维 | 平台健康面（Findings/吞吐/WAL/队列/SSE 计数）+ 下载中心（7 天过期）+ 孤儿恢复 + 优雅停机 drain | ★ 健康面生成于 2026-10-16 14:37 |

**核心闭环**：
```
项目(资产组织) → 建任务(引擎×模式×环境×算力) → 派发(claim 环 15s·本机/远程)
   → runner 跑 CLI(会话日志落盘) → mapper 解析(结构化 findings 入库)
   → 漏洞中心(疑似) → 人工终审(确认是/确认非 + 标注) → 导出/下载中心交付
```

---

## 1. 五分钟上手

1. **起栈**：`pnpm install && pnpm dev:all`（server 7090 + web 3081 同起）；浏览器开 http://localhost:3081。生产态由服务端 serveStatic 同源托管（nginx 反代样例见 dsh-test/zhulong.conf）。
2. **首启向导**：全新库（users 空）走 setupAdmin 向导建 admin 账号并种内置引擎清单；admin 初始凭据在向导/日志中产生（本机实例为用户自设本地凭据，不入档）。登录后 cookie `zl_sess`（TTL 7 天，服务端 sessions 表，退出即吊销）。
3. **建项目**：项目管理 → 新建项目（名称/业务域/敏感/成员）。
4. **建任务**：任务中心 → 新建任务 → 选引擎卡 → 选模式（开眼/吐焰）→ 选测试环境 → 起名 → **创建并开始**（建即跑，无「只建不跑」）。
5. **看结果**：任务详情四 Tab（历史·运行日志/产物/漏洞关联/终审）→ 漏洞中心看疑似清单 → 进详情人工判定（确认是/确认非）→ 导出。

---

## 2. 界面地图与逐页使用手册

> 布局：顶栏（品牌 烛龙 ZhuLong + 全局项目切换「全部项目 ▾」+ 头像/登出）+ 六主导航（首页/项目管理/测试任务/漏洞中心/资产管理/用户管理）+ 内容区。URL 即状态：`?tab=`（资产页签）、`?status=`（任务筛选）、`?verdicts=`（漏洞终审筛选）全部深链可达。每节格式：**做什么 → 界面构成 → 操作/参数逐项 → 机制原理 → 实战要点**。

### 2.0 登录（/login）
- **做什么**：表单登录（用户名/密码/登录）。
- **机制**：连续失败进锁定（默认 5 次/15 分钟，ZL_LOGIN_LOCKOUT_*）；锁定报文差异与时间侧信道是已知的评测面（本实例在册 findings）。
- **要点**：admin 账号由首启向导创建；多用户到 用户管理 建账号（三角色）。

### 2.1 首页与故事页（/ · /story/:chapter）
- 首页=品牌舞台（三模式玻璃卡：开眼·DRAGON EYE/吐焰·FLAME/化形·SHAPESHIFT），故事章独立深链（降生/开眼/吐焰/化形/烛照）——教育叙事不弹窗。
- **要点**：这是全站唯一动效页；日常作业直接进 /projects。

### 2.2 项目管理（/projects）
- **做什么**：测试资产的顶层分组。**界面构成**：类型 chip 筛选（全部/web/host/k8s/mobile/other）+ 分页 + 卡片（名称·敏感徽标·类型 Tag·成员·创建人·创建时间·成员/编辑项目/删除项目按钮）。
- **操作/参数**：新建项目表单=项目名称*（placeholder「例如：电商中台安全审计」）/ 业务域*（web▾）/ 敏感 checkbox（默认勾选）/ 成员（可选，按角色 安全工程师/漏洞审计员 两组「选择用户▾ + ＋添加」）。动作：取消/创建项目。
- **机制**：项目可见性=RBAC（admin 全见；工程师/审计员见成员身份关联）；「敏感」标记会传导到漏洞页（敏感项目签）与导出。
- **实战要点**：渗透靶场请勾「敏感」——它同时是导出时的脱敏提示位。

### 2.3 测试任务（/tasks · /tasks/:id）
- **做什么**：任务的建、看、跑态追踪。**界面构成**：七桶 KPI（全部/排队中/运行中/成功/失败/已取消/软删，可点深链）+ 运行概览折叠区（实时+队列双计数）+ 14 列表 + 项目/引擎/模式筛选 + 自动刷新 30s + 「实时（SSE）」标。
- **建单表单逐项**（open-then-cancel 实证）：**能力（引擎×模式）**——引擎卡（名称/版本/白盒·黑盒/enabled/发现 N）单选；**模式**——开眼「广域照亮（广域探索）」/ 吐焰「定点灼穿（深度挖掘）」；**测试环境（我的＋共享）**下拉；**算力**——内置共享执行器（默认共享·不可选）；**参数**——按引擎 manifest 声明动态渲染（无声明则「本插件未声明参数」）；**任务名称**。动作：**创建并开始**。
- **行操作族**：查看详情/查看报告/查看漏洞/下载报告/失败原因/重跑/删除；勾选后批量删除。
- **导入历史会话**（引擎▾烛龙 ZhuLong/**会话目录** text（placeholder /sessions/demo-audit）/项目/关联对象▾）——把已跑过的 runner 会话目录直接导入解析（跳过执行，直接产 findings）。
- **任务详情**：头带（名称+状态徽章+项目/创建人/创建时间/**建单锚**/引擎/模式/测试对象/阶段进度/成本与用量）+ 四页内 Tab：**历史·运行日志**（runner 会话日志原文）/ **产物**（文件名+体积徽标，raw 可看）/ **漏洞关联** / **终审**。
- **机制原理**：任务落库 status=waiting（legacy 语义）→ claim 环（本机 localClaimIntervalMs=15s；远程 runner 同频族）领取 → runner 跑 CLI 产会话日志 → mapper 流式解析 → findings 入库 + 阶段进度投影；失败原因为服务端原始 JSON（如「claim 响应丢失（kill 未消费——幽灵任务回收·资源槽释放）」）；建单锚=服务端日志 grep 直通词；服务重启触发孤儿恢复（local running→failed[服务重启中断]），SIGTERM 走 drain 宽限梯。
- **实战要点**：「暂无用量数据」=引擎未回报成本（demo 类引擎常态）；失败先拷建单锚再查服务端日志；重跑会走 rerun 门（gate reset）。

### 2.4 漏洞中心（/vulns · /vulns/:id）
- **做什么**：漏洞生命周期（AI 初判→人工终审）。**界面构成**：KPI 阵（P1 漏洞（严重≥High）/严重分布五档/**确认率** 环形/三态终审卡：疑似「AI 初判，待人工终审」·确认是「终审通过，真实漏洞」·确认非「终审驳回，误报」）+ 11 列表（标题/等级/终审/POC/静态 PoC/动态 PoC/引擎/任务/敏感/更新时间/操作）+ 全部/白盒/黑盒 + 高级筛选 + 任务/等级下拉。
- **操作**：行内 查看详情/判定/导出（单条即下）/删除 + 「按此任务筛选」深链；KPI 卡点击=写 `?verdicts=` 深链（与筛选面板同源互斥）。
- **详情页**：三列骨架（左 140 章节导航 识别信息/概述/机理/证据/影响/PoC/修复/终审｜中六章正文｜右 260 操作卡）+ 头带（标题+编号+终审徽标+敏感签）+ POC详情/导出漏洞/删除漏洞。识别信息字段族：编号/等级/漏洞类/CWE/置信/引擎/**映射器**/任务/敏感/出处（文件:行）/来源/时间戳。
- **终审卡两种形态**（读态优先实证）：未判=终审表单常开（三态大卡+等级+漏洞类+理由注记）；判过=「标注（N 条）」Tab 默认展示判据时间线（结论/等级/判定人/判定时间/注记），判定动作退为「重新判定」。
- **机制原理**：findings 由 mapper 从会话日志结构化产出（置信=线索/实证两档，证据章含 CVSS 向量与诚实边界描述如「仅内网 HTTP 场景可利用·生产 HTTPS 下不成立」）；终审写库留判定人与时间戳；导出走下载中心（7 天过期）。
- **实战要点**：判定前先看「出处」（文件:行）与 PoC 四元组；确认率是治理 KPI（本实例 8%=13 条里 2 条终审）。

### 2.5 资产管理（/assets?tab=…，五 Tab）
- **算力资源池**：路径一自动接入=本机 CLI 探测真值表（名称/版本/路径/启用开关——claude/opencode/node/demo/git/docker 实测在册）+ 教育文案（「停用某个 CLI=本机不再接该类任务（能力闸门即时生效）」「自动接入的执行器不可停用：停用会强制终止在跑任务…」）；执行器卡=机型/能力徽章/机器槽/状态/最后心跳/操作（详情·停用·归档）+ 池活动时间线；路径二手动接入=**接入令牌**表（生成/备注/有效期/状态/使用机器）——远程 runner 凭 token 注册。
- **测试对象**：名称/类型（代码·文档）/来源（上传·本机路径·仓库）/可见性（私有）/版本指纹 hash/操作（上传版本/下载/删除）。
- **测试环境**：名称/类型（Web 等）/endpoint/凭据/指纹健康/健康检查——环境探活有 SSRF 闸门（forbiddenHealthHost 黑名单；绕过面见 §9 交叉索引）。
- **知识图谱**：三计数卡（漏洞类/合规规则/提权五族）——mapper 的先验知识面。
- **引擎**：插件卡（名称/版本/白盒·黑盒/enabled/**发现 N**）+ 声明「插件安装/升级/卸载属 BO4」。**探隐红队 tanyin 已注册（黑盒·enabled·发现 0）**。
- **机制原理**：引擎=engine_plugins 表（UNIQUE(plugin_id,version)，旧版本行保留供历史任务读 manifest 快照）；内置清单启动幂等种子（缺=插入、在=不动启停裁定、版本新=更新快照**不翻 enabled**——admin 的启停裁定不被供给更新越权重置）；能力目录 Tab 由 ZL_SHOW_CATALOG 显隐（缺省藏）。
- **实战要点**：接远程机器=资源池生成令牌→对端 runner CLI 配 token→心跳 30s 入池；失联先进宽限（ZL_RUNNER_LOST_GRACE_SEC=900）黄标，窗末未复才 failed。

### 2.6 下载中心（/downloads）
- 生成物列表（评估集/漏洞清单/任务报告）+「生成后 7 天内可下载」；过期行只留状态词。
- **要点**：要长存报告请导出后自行归档——7 天过期让本实例 9 条全过期。

### 2.7 用户管理（/admin/users，admin 专属）
- **界面构成**：顶部**平台健康面**（Findings 总数/24h 新增/查询耗时、任务吞吐 24h 新建·完成·失败、WAL journal_mode/synchronous/busy_timeout、计划任务、队列 排队·运行·SSE 连接）+ 用户表（用户名/角色/状态/登录状态/创建时间/操作 编辑·禁用·重置密码·授权·删除）。
- **机制原理**：仅 admin（路由级 requireAdmin）；写操作全程审计（audit_log）；自保护（不可自降级 400、不可自禁用 403、最后可用管理员保护）；软删（status='deleted' 不出列表）；口令 scrypt 哈希；API 三角色 admin/operator/auditor ↔ UI 管理员/安全工程师/漏洞审计员。
- **实战要点**：健康面的 WAL/队列计数是巡检第一站；「在线」=sessions 表活跃会话存在性。

---

## 3. 核心机制原理（源码实证）

### 3.1 三包 monorepo 与契约单源
pnpm workspace：`apps/web`（Vue 3.5 + Pinia + vue-router + Tailwind 4 + lucide 图标）· `apps/server`（Node + Hono + better-sqlite3 + 18 个 SQL 迁移）· `packages/contracts`（**zod schema 双端单源**：端点/域模型/SSE 事件/枚举全在 contracts，web 与 server 都 `z.infer` 同一份——前后端零类型漂移）。

### 3.2 存储与启动序
SQLite WAL（busy_timeout 5000ms）；启动序=数据库→首启（users 空→setupAdmin 向导+内置引擎种子）→插件→内置执行器→种子→服务。附：孤儿恢复（local running 任务→failed[服务重启中断]）+ SIGTERM/SIGINT 优雅停机 drain（停调度器→会话取消宽限梯 SIGTERM→30s→SIGKILL→在途写 grace 5s→断 SSE→退出）。

### 3.3 派发四环（同频族）
① claim 环 localClaimIntervalMs=15s（本机派发；0=关纯远程部署形）；② 心跳 30s（heartbeatTimeoutSec=90 超时+runnerLostGraceSec=900 宽限）；③ 定时任务环 schedules tick 30s（cron 表达式任务）；④ 化形编排环 pipelineTickMs=30s（PIPELINE 多步编排）。全局并发闸 globalConcurrency=4；任务超时 taskTimeoutMin=240（0=关）。

### 3.4 runner 面（远程执行器）
provision token 注册（有效期/一次性使用记录）；runner 认证（runner-auth）+ 会话通道（runner-channels）；产物上传走分片（artifact-chunks，sha256 校验）；runner 侧还有对象族上传（runner-object-family）。沙箱：zl-sandbox-* 一次性容器 + 出网管控（egress 网络）+ 凭据/目标文件注入（sandboxCredentialDir/TargetsDir）+ 孤儿清扫（容器/网络/凭据文件/目标文件/tmp 快照五类 sweep）。

### 3.5 mapper（会话日志→findings）
引擎产出=会话日志原文；mapper 按引擎分族流式解析（mapper-zhulong/mapper-tanyin/mapper-directive…）为结构化 findings（标题/等级/置信/出处 文件:行/CWE/证据/影响 CVSS/PoC）。「映射器」字段暴露在漏洞详情识别信息里（如 seed-v1）——**解析器可追溯**。

### 3.6 治理面
审计日志全写面（actor/action/object/detail 同事务落库；系统动作用 actor NULL）；登录锁定（5 次/15 分钟）；会话写节流（sessionWriteThrottleSec=60）；全库凭据加密（libsodium + master.key，密钥不入库）；下载 7 天过期；RBAC 矩阵（rbac-matrix 测试在册）。

---

## 4. 一次完整测试任务的生命周期（端到端）

```
① 建项目(敏感) → ② 登记环境(endpoint+凭据) / 登记对象(代码/文档) → ③ 资源池确认算力(自动探测或令牌接入)
→ ④ 新建任务: 引擎×模式(开眼/吐焰)×环境×算力 → 创建并开始
→ ⑤ waiting → claim 环 15s 领取 → runner 起 CLI(沙箱/凭据注入) → 会话日志+产物流式回传
→ ⑥ mapper 解析 → findings(疑似) + 阶段进度投影 → 任务 success/failed(原因原文)
→ ⑦ 漏洞中心: 逐条人工终审(确认是/确认非+标注) → ⑧ 导出/下载中心(7 天) → 修复后可重跑复测
```
失败排查三步：任务详情拷**建单锚** → 服务端日志 grep → 历史·运行日志 Tab 看 runner 原文。

---

## 5. 架构图解（ASCII）

```
┌───────────────────────────────────────────────────────────────────────┐
│                 浏览器（Vue 3 SPA @ :3081 · URL-SSOT + SSE）           │
│   项目 │ 任务(+详情4Tab) │ 漏洞(+终审) │ 资产5Tab │ 下载 │ 用户/健康    │
└──────┬──────────────────────────────────────────────┬─────────────────┘
       │ /api/*（cookie zl_sess · RBAC 三角色）        │ SSE events-stream
┌──────▼──────────────────────────────────────────────▼─────────────────┐
│                Hono 服务端 @ :7090（tsx watch/serveStatic 同源）        │
│  routes(auth/projects/tasks/findings/assets/pipelines/admin/provision) │
│  服务: task-create · scheduler · local-dispatch · mapper 族 · 审计     │
│  四环: claim 15s · 心跳 30s(+宽限900s) · schedules 30s · pipeline 30s   │
│  SQLite WAL（18 迁移）· 凭据 libsodium(master.key) · 下载 7 天过期      │
└──────┬──────────────────────────────┬─────────────────────────────────┘
       │ 本机 CLI（自动探测入池）        │ provision token 注册
┌──────▼─────────┐        ┌───────────▼──────────┐
│ 内置共享执行器  │        │ 远程 runner（心跳30s） │
│ claude/opencode│        │ 会话日志+分片产物回传  │
│ demo/git/docker│        │ 沙箱: zl-sandbox-*    │
└────────────────┘        └──────────────────────┘
```

---

## 6. 配置速查（config.yaml + ZL_ env，16 键）

| 键 | 默认 | 说明 |
|---|---|---|
| port | 7090 | 服务端口（ZL_PORT） |
| dataDir | ./data | SQLite/凭据/产物根 |
| credentialKeyRef | ZL_CREDENTIAL_KEY | 主密钥 env 引用名（密钥不入库/git/备份） |
| disabledEngines | [] | 引擎停用清单 |
| globalConcurrency | 4 | 全局并发闸 |
| dispatchIntervalSec | 5 | 派发间隔 |
| heartbeatTimeoutSec | 90 | 心跳超时 |
| taskTimeoutMin | 240 | 任务超时（0=关） |
| runnerLostGraceSec | 900 | runner 失联宽限窗 |
| sessionTtlDays / sessionWriteThrottleSec | 7 / 60 | 会话 TTL / 写节流 |
| loginLockoutAttempts / loginLockoutMinutes | 5 / 15 | 登录锁定 |
| logLevel | info | 日志级 |
| seedProfile | off | 首启种子（生产禁用） |
| taskStartSemantics | legacy | legacy=创建即 waiting；manual=created 待 start |
| showCatalog | false | 能力目录 Tab 显隐 |
| localClaimIntervalMs / pipelineTickMs | 15000 / 30000 | claim 环 / 编排环周期（0=关） |
| engineContainer | [] | 容器径引擎 execBinary 白名单 |

---

## 7. 安全模型与合规边界

- 口令 scrypt；会话服务端表+TTL 7 天；登录锁定 5/15；全库凭据 libsodium 加密（master.key 与密文分权——同目录同权是已知评测面）；审计日志全写面；RBAC 三角色+项目成员可见性；admin 自保护/最后管理员保护；沙箱出网管控+凭据注入隔离。
- **本实例的已知攻击面清单**（作为靶场被 ARTEX/CSAI 实测在册，详见 §9）——部署到公网前必须逐条修复，dev 栈仅限本机。

## 8. 常见任务速查

| 我想… | 路径 |
|---|---|
| 跑一次 AI 红队扫描 | 项目→新建任务→引擎 tanyin/zhulong→开眼→环境→创建并开始 |
| 把已跑的会话导入出报告 | 任务→导入历史会话（引擎+会话目录+项目） |
| 接一台远程机器跑任务 | 资产→算力资源池→路径二生成接入令牌→对端 runner 配 token |
| 停用某个本机 CLI 能力 | 资产→算力资源池→路径一真值表→启用开关（进行中跑完） |
| 判定漏洞真伪 | 漏洞中心→详情→右侧终审卡（三态+标注） |
| 导出漏洞/报告 | 漏洞行内 导出 / 任务行内 下载报告（7 天内） |
| 查平台健康 | 用户管理顶部健康面（Findings/吞吐/WAL/队列/SSE） |
| 排查失败任务 | 任务详情→拷建单锚→服务端日志 grep→历史·运行日志 Tab |

## 9. 本实例战斗痕迹交叉索引（靶场视角）

本实例 2026-10-15 起被 ARTEX（51 findings）与 CSAI（4 vulns+5 facts）作为靶场实测。库内可见的攻击者行：环境表 SSRF 绕过矩阵（rbndr/nip.io/十进制 IP）、资源池攻击者注册的验证机群（i41/i56/i96-audit-runner）+接入令牌、用户表攻击者造的低权账号（penter/viewer）、项目表实验分组（i48-*）、payload 名对象/任务/项目原样回显。逐条与 ARTEX findings #3/#4/#7/#10/#15/#20/#21/#25/#41/#50 等互证——**详见 ../liveui/walk-zhulong-live.md §3 对照表**。这批痕迹本身即「AI 红队实战样本库」，可用于探隐的评测集设计。

## 附：实证索引

- 界面/表单参数：walk-zhulong-live.md §2/§4（2026-10-16 open-then-cancel 取证）+ walk-zhulong.md 27 视图表（2026-10-15）。
- 机制：apps/server/src（config.ts 16 键 / index.ts 启动序 / services/* 源码注释 / engine-seed.ts 种子语义）。
- 健康面/计数：/admin/users 顶部（生成于 2026-10-16 14:37 实测）。

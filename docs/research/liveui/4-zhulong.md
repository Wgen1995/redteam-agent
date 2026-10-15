# 烛龙 ZhuLong 活体系统分析报告（靶场 + UI 参照）

> 分析对象：ZhuLong @ http://localhost:3081（Vite dev server + Node 服务端）
> 分析日期：2026-10-16 · 分析者：探隐委托子代理
> 证据基础（四层交叉验证）：
> ① **前端源码真身**：ZhuLong web 控制台 monorepo 就在本会话工作目录 `ai-assisted-security-verification-platform/`（apps/web + apps/server + packages/contracts），只读直读；
> ② **dev server 源码爬取**：从 Vite dev server 抓取 /src/ 全部模块（110 个，经 sourcemap sourcesContent 还原原始 SFC），与本地真身一致；
> ③ **live API 只读验证**：登录 POST（admin）后仅 GET 17 个端点（health/me/projects/tasks/findings/stats/resources/objects/environments/plugins/knowledge/downloads/schedules/pipelines/users/admin-health/grants），未触发任何扫描/建任务/状态变更；
> ④ **方法论框架库**：`zhulong-main/`（GitHub reganxt/zhulong 本地检出）只读——纯自然语言白盒审计知识库 + workspace/ 真实审计运行产物。
>
> 只读纪律遵守声明：全程对 ZhuLong HTTP 仅 GET + 一次授权登录 POST；zhulong-main 严格只读未执行 git；未触碰任何运行中作业。

---

## 一、UI 设计解构（源码级）

### 1.1 技术栈与工程形态

pnpm monorepo 三包：`apps/web`（Vue 3.5 + Pinia + vue-router + Tailwind CSS 4 + lucide-vue-next 图标 + vitest 组件测试）、`apps/server`（Node + SQLite WAL + 18 个 SQL 迁移 + runner/daemon/sandbox）、`packages/contracts`（zod schema 双端单源：API 端点/域模型/SSE 事件/枚举全在这，web 与 server 都 `z.infer` 同一份——**前后端零类型漂移**）。

前端量级：views 14 个（6700 行）+ ui 基件 17 个 + domain 领域组件 34 个 + composables 7 个 + Pinia stores 11 个 + 词账 `config/wording-bo3c.ts` 33KB（全部 UI 文案键控单源）。配套 `dev-jargon-guard.spec.ts`——**用测试守门 UI 文案不出现开发黑话**。

### 1.2 布局骨架（AppShell.vue，490 行）

- **无侧栏**。历史上有过左侧栏+折叠机制，T5 定稿时整体退役，改为**顶 tabs 制**：sticky 56px 顶栏 = 品牌区（28px 龙瞳 SVG：圆环+眼形+瞳孔挖空底色 → 中文名 17px/800 三色渐变 + 英文名 11px 靛紫）→ 主导航 tabs（首页/项目管理/测试任务/漏洞中心/资产管理 + admin 追加用户管理，6px 10px 圆角 12 胶囊，激活 = 淡蓝底 #2563EB 字）→ 右区四件：
  1. **下载中心头带**：图标钮 + 近 24h 生成数角标（0 隐藏）+ 下拉近 5 条（类型 Tag + 名称截断 + 剩 N 天 + 直开）+「查看全部」；壳挂载即拉 + 30s 轮询；
  2. **昼夜切换**：lucide Sun/Moon 18px 无边框图标钮（切昼「睁眼」/切夜「瞑目」——主题词与产品隐喻绑定）；
  3. **项目切换器**：头像左侧「项目名 ▾」，切换 = 设全局语境，当前页原地刷新不跳转（D7 裁定）；
  4. **用户区**：头像+「用户名 · 角色」灰文本一体化触发器，下拉 = 基本信息 KV 行（无值不渲染）+ 修改密码（全局 BaseModal 内嵌壳层）+ 退出登录（高危二次确认）。
- **主区留白分岔**：工作台页 `zl-page`（0 28px 48px）；首页唯一满幅舞台（光晕/网格不裁切）。
- z-index 三级纪律：菜单 40 > 详情头带 30 > 列 sticky 20，弹层 50/60。
- 路由守卫语义严密：匿名仅放行 /login /setup；未登录深链 → `/login?redirect=` 回原地；401 全局拦截豁免 `/api/auth/*`（防双导航竞态）；**传输层故障（5xx/断网）不伪装成未登录**——toast「服务暂时不可用」+ 放行匿名态进页由页面错误态接管（四态统一哲学）。

### 1.3 组件树与复用模式

三层组件架构：
- `ui/` 基件 17 个（BaseButton/Input/Select/Modal/Dropdown/Badge/Tag/KpiCard/Pagination/Skeleton/EmptyState/TabsBar/Tooltip/ConfirmDialog/CodeBlock/ProgressBar/ToastContainer）——全部 <120 行的受控小件；
- `domain/` 领域件 34 个（SeverityBadge/VerdictBadge/StageProgress/TaskTerminalPanel/TaskRunLogViewer/ConsoleOverview/ConsoleRunningCard/FindingsFilterPanel/VerdictForm/TaskCreateForm 18K/PipelineWizard 38K/ResourcePoolPanel 27K/WhenConditionEditor…）；
- `layout/` 3 个（AppShell/PageHeader/ProjectSwitcher）。

**复用模式五律**（源码注释里显式声明的工程纪律）：
1. **store 同源零 props**：TaskTerminalPanel/TaskRunLogViewer 不接收 props，直接读 `useTaskDetailStore()`——侧面板与全页两容器同享一份状态；
2. **单源双消费**：VerdictForm「详情终审卡内联与 VerdictDialog 弹窗壳共体——词面/校验/提交行为单源，两消费方只管壳与刷新」；
3. **词账键控**：所有 UI 文案走 `WORDING_BO3C['channel.resume']` 式键取（33KB 词账），文案改动零代码接触；
4. **单源收敛**：`fmtDate` 七处本地复制被审计收敛为 utils 单源；ROLE_LABEL 角色词单源；
5. **退役声明注释**：被删组件的退役凭据写在替代文件头（「五步向导退役→单页表单，本注记为唯一退役凭据」）——组件墓志铭制度。

### 1.4 状态管理写法（Pinia 11 stores + 7 composables）

- stores：app（主题/项目语境）/auth/project/task/task-detail/finding/asset/console + **三个「服务端 flag 客户端镜像」store**（heartbeat-thresholds/show-catalog/start-semantics——feature flag 单源在服务端 /api/health，客户端零硬编码，杜绝双真相源漂移）；
- `useUrlQuery`：**URL query 即状态**（筛选/分页/Tab 全进 query，前进后退/刷新还原，未知参数忽略，默认值省略写回 URL 干净）；防回写环双保险 = 逐键深比较 + syncingFromUrl 置位跳过写回 watch；
- `useTaskEventStream`：原生 EventSource 订阅 12 名契约事件；断线由浏览器自动重连（Last-Event-ID 回带 → 服务端 events.jsonl 回放补窗）；**stream.gap 帧 = 服务端明示锚不可回放 → 弃锚重订**（关旧连接新开无锚纯实时订阅）；taskId 换行重订、卸载净关零泄漏；
- `useTerminalStream`：终端流 = 独立 **live-only 子通道**——无 ring 无锚、断线不回放、重连插入「── 继续 ──」分界标记行（历史断档的诚实分界）；历史查询归 run.log 查看器；
- `useAutoRefresh`：10s/30s 两档轮询统一件；`useConfirm` 高危二次确认（确认才发请求·取消零请求）。

### 1.5 视觉系统（Token 单源 style.css）

（色表已有专档，此处只记结构）三层底 bg/card/well + 语义五色 + **三息概念色**（开眼蓝 --zl-eye / 吐焰琥珀 --zl-flame / 化形紫 --zl-form——模式语义直接进色板）+ 严重级五档独立变量 + 阴影三级 + 圆角 12/9/99 + 动效 150/200/300ms ease-out（仅进度条循环）+ 字阶 20/15/14/13/12.5/11 + KPI 28（tabular-nums）。暗色 = **全 Token 镜像非滤镜**（对比 ≥AA）。局部命名空间模式：AppShell 自持 `--hd-*`、HomeView 自持 `--hs-*` 舞台色板，不动全局。几何预算纪律写进注释：「表行 46px → 任务表 14 列 1440 视口零横滚；漏洞表 11 列/资源表 7 列 1280 零内滚」——**列宽是预算管理出来的**。

### 1.6 状态可视化手法（可直接抄级）

- 七桶 KPI 卡阵：4/7 栅格，值 = 服务端 buckets（口径不受筛选影响），点击 = status 深链过滤，激活卡琥珀描边+ring；
- StageProgress 点线微图：3.5px 圆点串 + 2.5px 连线（完成段变绿）+ active 点 pulse 动画 + skipped 灰点 + **门禁 tooltip**（active 段悬停显示"门禁：xxx"）+ 右侧「阶段名 i/n」+ tabular-nums 计数；
- VerdictBadge 三态终审徽章 / SeverityBadge 五档；行高亮 = 琥珀 ring + 3s 自清（深链落地后定位行）；
- 详情头带**滚动紧凑态**：sticky top-56px，滚动后副行 nativeId/徽章行 h-0 淡出、标题截断、底边框+微影浮现；
- 断线徽章词域（connecting/open/disconnected 三词）+ 终端「实时」绿标 + 滚动暂停琥珀标；
- 四态纪律：加载 = 骨架（表格 3 行 46px / 卡片网格 / 区块 shimmer 三形）；错误 = EmptyState(error) 红警示 + 重试钮；空态 = 虚线框 + CTA 插槽；数据态。
- ConsoleRunningCard：每运行任务一卡一 SSE 订阅（上限切面 + 超限提示行「其余运行中任务见任务列表」——**订阅有预算**）。

---

## 二、功能清单 + 成熟度评分

| # | 功能 | 状态 | 成熟度 | 依据 |
|---|------|------|--------|------|
| 1 | 项目管理（卡片网格/软删恢复/成员授权 grants/敏感标记/owner+name 唯一索引） | 有 | 4.5 | projects 表+ProjectsView 811 行；live 8 项目 |
| 2 | 任务全生命周期（七桶/单页创建表单/启动语义 manual·legacy/批量软删/重跑/取消/计划徽标） | 有 | 5 | TasksView 1060 行；live 4 任务 buckets 实证 |
| 3 | 任务实时观察（SSE 12 事件/终端 live-only/run.log 查看器 1MiB 尾窗/阶段快照/request_id 锚） | 有 | 5 | useTaskEventStream+TaskTerminalPanel+run-log.ts |
| 4 | 漏洞中心（筛选面板/三态 KPI/六章 NDM 详情/行展开来源/敏感行标/导出 MD） | 有 | 4.5 | VulnsView 1049 行+findings.ts；live 7 findings |
| 5 | 人工终审工作流（三态大卡/误报原因五词/等级双语/CWE combobox/标注时间线追加永不删改） | 有 | 5 | VerdictForm+annotations 表（无 updated_at 列=不可变设计） |
| 6 | PoC 维护（前置/步骤/预期/验证四元组/静态·动态双布尔/导出 Markdown） | 有 | 4 | PocView+PocSchema；live 对象库有 poc-code.py |
| 7 | 资产管理六 Tab（算力资源池/能力目录/测试对象/测试环境/知识聚合/引擎）URL 深链 | 有 | 4.5 | AssetsView 919 行；showCatalog flag 藏目录 |
| 8 | 资源池治理（心跳 90s 超时/宽限窗 900s 倒计时/provision 令牌/CLI 探测真值报告/audit 流） | 有 | 4 | ResourcePoolPanel 27K；live 探测报告含 claude 2.1.238/opencode 1.19.0/node v26.5.0 路径 |
| 9 | 引擎插件治理（manifest 注册/启停/卸载 soft·hard/供应链 git·npm·local） | 有 | 4 | plugins 表+端点 42/44/83；live demo 引擎 manifest 全暴露 |
| 10 | 化形编排（pipeline 模板/步卡序列/when 条件 DSL 三叶/loop while·foreach/嵌套/前向引用校验） | 有 | 3.5 | PipelineWizard 38K（BO8/BO10 新增）；live 0 模板 0 run——未实战 |
| 11 | 计划任务（schedules CRUD/nextRunAt） | 有 | 2.5 | live 0 条，admin-health active:0 |
| 12 | 下载中心（报告/清单/评估集三类/7 天过期制/过期禁点） | 有 | 4 | downloads 表；live 9 条全 expired（过期制真实运转） |
| 13 | 用户管理 RBAC（admin/operator/auditor 三角色/在线状态/停用/重置密码/自禁服务端拒） | 有 | 4.5 | admin.ts+0005 迁移；live 5 用户 4 在线 |
| 14 | 健康双面（匿名 /api/health 最小运维面 + admin /api/admin/health 五族聚合） | 有 | 4 | live：db ok/diskPct 8/queueDepth 0/wal/schedules/queue |
| 15 | 首页门面（三级字栈 hero/五章故事轮播/三模式玻璃卡/18s 光晕轮换） | 有 | 4 | HomeView+StoryCarousel+StoryView 教育章 |
| 16 | 知识聚合（19 漏洞类/227 合规规则/5 提权族三计数） | 有 | 3.5 | /api/knowledge live 实证；正文在 zhulong-main 框架库 |
| 17 | findings 外部导入（imports 瞬间落库/批次审计） | 有 | 3.5 | import_batches 表+端点 19 |
| 18 | 移动端适配 | 半 | 3 | 栅格响应式（sm/lg/2xl 断点）但表格 13-14 列纯桌面导向 |
| 19 | 国际化 | 无 | 1 | 纯中文词账，EN 仅品牌副名 |
| 20 | 黑盒主动扫描 | 无 | — | 定位白盒审计平台；「环境探活」仅 HTTP GET 5s 探测+指纹 |

**总评**：一个工程成熟度异常高的闭环系统——每个功能背后有 SQL 迁移+zod 契约+组件测试+词账文案四件套。短板只在编排/计划两条新功能的实战缺位。

---

## 三、业务使用流（live 数据推断）+ 靶场攻击面

### 3.1 它在真实渗透工作流中的角色

ZhuLong web 台 = **AI 白盒审计的控制平面**；zhulong-main 知识库 = 审计引擎的大脑。真实作业闭环（live 数据逐环实证）：

1. **建项目圈地**（live: ADMIN-SEC、PENTER-WEB——一个安全验证平台项目、一个渗透 web 项目，同一 admin 双线作业）；
2. **登记资产**：测试对象 = 源码包/文档上传（live: poc-code.py、secret-poc.txt、example.com 被动目标简报 ×2）；测试环境 = web endpoint（live: example.com）；
3. **建任务派工**：选引擎（zhulong=CLI 战士 / demo=演示）× 模式（开眼）× 目标（对象或环境二选一）→ runner 派发本机执行器（live: 内置共享执行器，capabilities=[claude,opencode,demo,git,docker]，concurrency 1）；
4. **执行 = CLI 战士被沙箱驯化**：`opencode run --format json <指令>` NDJSON 事件流（step_start→task.progress / tool_use→tool.call / text→日志 / step_finish→stage.end），退出码 = 权威终态；预算熔断（opencode 无 --max-budget-usd 旗标 → 平台侧熔断告警）；容器径走 docker 一次性沙箱（见 3.3）；
5. **live 实跑证据**：T5「zhulong×opencode·example.com 轻量核verify」success 144s、T7「daemon 远程径真跑（example.com 被动只读）」success 97s——**被动只读作业纪律写在任务名里**；demo-whitebox failed（17s，引擎失败样本）；
6. **findings 落库人工终审**：live 7 条（pending 5 / confirmed 1 / refuted 1；Crit 2 / High 1 / Low 1 / Info 3）——确认/驳回工作流真实在用；
7. **导出**：评估集/漏洞清单 7 天过期制（live 9 条全过期=过期清扫真实运转）。

zhulong-main/workspace/ 另有纯 CLI 时代的真实审计产物：**Tomcat 全量审计（ma/，25+ worker 按 catalina 模块分片：session/realm/ssi/tribes/ha/el/jasper…）**、mall-swarm 微服务跨服务审计（06-contracts/07-taint-paths）、real-audit 单服务六阶段——web 台的「任务/引擎/知识」抽象正是这些手工作业的平台化。

### 3.2 靶场攻击面清单（探隐未来实战的靶场形态——live 实证）

| 攻击面 | live 证据 | 说明 |
|--------|-----------|------|
| **SSRF 操作面** | 9 个环境里 6 个是绕过测试组：`169-254-169-254.nip.io`（元数据）、`2130706433`（十进制 IP）、`127-0-0-1.nip.io`、`blocked-loopback-direct`（ blocked 对照组）、`low-ssrf`、`ssrf-test-1` | 环境探活（端点 41 HTTP 探测+指纹回写）天然是 SSRF 发射器；ZhuLong 用 nip.io/十进制 IP 组做**出网白名单的绕过测试矩阵**——这就是探隐未来打同类平台的标准姿势 |
| 存储注入回显 | 项目名 = `x"--`、`x' || (SELECT 999*999) --`、`x'--` 三条 SQLi payload 已入库并列出 | 参数化查询下无害，但证明**名字字段是注入测试靶标**且回显完整 |
| 匿名信息泄露 | /api/health 无鉴权吐 version/queueDepth/sseConnections/diskPct/双阈值 | 指纹+运维态侦察一步到位 |
| 认证面 | weaktest2（弱口令测试号）、penter/viewer（RBAC 三角色样本）、Cookie 会话 7 天滑动、token sha256 落库 | 撞库/会话固定/越权三角 |
| 文件上传面 | /api/objects/:id/upload multipart；live 有 secret-poc.txt（敏感文件明文存储样本） | 类型/大小/路径攻击面 + 存储敏感数据 |
| 引擎供应链 | manifest local/git/npm 三源注册、启停卸载、demo 引擎 invocation `cli+instructionTemplate` 直喷 CLI | 注册恶意引擎 = 指令注入/RCE 面 |
| 远程执行器接入 | provision 令牌 + 心跳注册 + capabilities 广告（claude/opencode/git/docker） | 窃取令牌 = 冒充执行器收任务 |
| 导入伪造 | POST /api/imports 外部 findings 瞬间落库 | 伪造漏洞污染终审流 |
| SSE 消耗面 | sseConnections 计数、事件流端点 | 慢连接资源占用 |

### 3.3 沙箱防线（它作为靶场的自我防御——探隐打它时要过的门）

docker run --rm 一次性容器：`--network none`（缺省外联全禁）+ `--cpus 2 --memory 1g --memory-swap 1g` + `--cap-drop ALL --security-opt no-new-privileges --pids-limit 256` + `--read-only` 根 + tmpfs /work（512m,exec,uid1000）+ `--user node` + `--init`（tini 信号转发）。凭据**走 /run/secrets 只读单文件挂载不走 env**（docker inspect Config.Env 明文可见的实证教训）。产物回提不走容器文件系统——stdout 尾部 base64 协议段解码落盘。出网白名单 = per-run 专用网络 + CONNECT Host 判定代理 sidecar（`sandbox-egress-proxy.mjs`）。失败 fail-closed 无宿主回落。**这是探隐「战士沙箱」可直接对标的一套参数表**。

---

## 四、对探隐的判决

## **仅参照** · 置信度 **90%**

**理由**：
1. **语言律硬冲突**：探隐 UI = 纯手写 HTML/CSS/SVG/vanilla JS 零框架零构建零依赖；ZhuLong = Vue 3 + Pinia + Tailwind 4 + zod + pnpm monorepo。一行组件代码都无法直接搬运；
2. **投影律错位**：探隐 UI 只读投影（十三账/哈希链的观察面）；ZhuLong 是写操作管理台（建任务/终审/授权），架构目标不同；
3. **可参照密度极高**：SSE 契约设计、URL SSOT、四态纪律、Token 体系、词账制度、锚链可观测性——全部是与框架无关的**模式资产**，vanilla JS 可等价重写（EventSource/URLSearchParams/Proxy 都是浏览器原生）。

**翻案条件**（任一出现即改判）：
- 出现「探隐需要多用户 RBAC 管理台 + 持久化任务队列」的完整需求，且愿意把 ZhuLong 整站当外壳、探隐内核以**引擎插件协议**接入（manifest+CLI 适配器）→ 改判**二开**（ZhuLong 的 plugin/runner 协议就是为接入第三方引擎设计的）；
- 探隐放弃零依赖律引入构建链 → 组件库可整体二开；
- ZhuLong 抽出 framework-agnostic 的 Web Components 独立包 → 直接复用部分基件。

---

## 五、可直接偷的 10 条（文件级出处 → 探隐落点）

| # | 偷什么 | 文件级出处 | 落到探隐哪页 |
|---|--------|-----------|--------------|
| 1 | **URL query SSOT 模式**：筛选/分页/Tab 全进 URL，前进后退/刷新还原，未知参数忽略，默认值省略，防回写环双保险（逐键深比较 + syncing 旗标跳写回） | `apps/web/src/composables/useUrlQuery.ts`（93 行完整算法） | 探隐所有列表页（账本视图/任务列表/门禁流水）：十三账浏览器的筛选+分页+哈希定位全进 URL，分享/回溯链接化 |
| 2 | **SSE 12 事件契约 + Last-Event-ID 回放 + stream.gap 弃锚重订**：事件名/载荷 zod 判别联合单源；断线浏览器自动回放补窗；锚不可回放时服务端发 gap 帧客户端弃锚重订 | `packages/contracts/src/sse.ts` + `apps/web/src/composables/useTaskEventStream.ts` | 探隐战士作业观察面：九门流程实时事件流（门启动/判据产出/账本落笔/战士心跳 12 个等价事件名先立契约再写 UI） |
| 3 | **live-only 终端子通道 + 滚动宪法**：终端流无锚不回放、断线插「── 继续 ──」分界行、chunk 到自动到底、用户上滚 >24px 暂停、回底恢复；历史归 run.log 查看器（1MiB 尾窗+截断提示） | `apps/web/src/composables/useTerminalStream.ts` + `components/domain/TaskTerminalPanel.vue` + `TaskRunLogViewer.vue` | 探隐 CLI 战士会话面板：opencode 现役会话的实时终端 + 历史日志双径 |
| 4 | **七桶 KPI 可点过滤卡阵**：值=服务端桶口径（不受当前筛选影响）、点击=status 深链、激活卡描边、tone 三态卡值色+标签色同调 | `apps/web/src/views/TasksView.vue` L66-88 + `components/ui/KpiCard.vue` | 探隐首页/任务仪表：九门流程状态桶（进行中/阻断/通过/回流…）点击即深链过滤 |
| 5 | **阶段点线微图**：3.5px 圆点串+连线完成变色+active 脉冲+skipped 灰+门禁 tooltip+「阶段名 i/n」tabular-nums | `apps/web/src/components/domain/StageProgress.vue`（35 行） | 探隐任务行/战士卡内嵌阶段进度（每行成本 35 行 SVG/HTML） |
| 6 | **滚动紧凑态 sticky 头带 + 三列 140\|1fr\|260 双 sticky 详情骨架**：滚动后副行淡出标题截断底边框浮现；左列章导航/中列内容/右列操作卡，<1280 竖排降级 | `apps/web/src/views/VulnDetailView.vue` L1-120（骨架）+ header band L37-118 | 探隐判据详情页/报告页：左=证据章节锚、中=正文、右=人工复核卡 |
| 7 | **四态纪律组件对**：加载=骨架三形（表格 3 行 46px/卡片网格/区块）、错误=红警示+重试、空态=虚线框+CTA 插槽、数据态；错误态与空态严格分流 | `apps/web/src/components/ui/Skeleton.vue` + `EmptyState.vue` | 探隐全局页面协议：每个观察面页统一四态（现在探隐多数页只有数据态） |
| 8 | **三态终审大卡 + 误报原因五词下拉 + 可输可选 combobox**：确认/驳回/存疑大卡（标题+一句 desc）、驳回必选原因（其他→补充必填）、CWE 中文名双径过滤 Teleport 面板 | `apps/web/src/components/domain/VerdictForm.vue` L1-110 | 探隐人工复核卡：判据三态裁决（成立/不成立/待定）+ 驳回原因词表 + 漏洞类 combobox |
| 9 | **request_id 建单锚 + grep 复制钮（五层下钻锚链）**：任务行携带建单锚徽标点击复制，日志查看器显示 task_id/run_id 键值行 + `grep request_id=<值>` 一键复制——UI 直通服务端日志检索 | `apps/web/src/views/TasksView.vue` L304-314 + `components/domain/TaskRunLogViewer.vue` L13-30 | 探隐任务行+日志面板：每笔作业带哈希链锚（账本行号/链头），点击复制 grep 词直查十三账 |
| 10 | **Token 单源 + 暗色全镜像 + 词账文案键控**：CSS 变量三层底/语义/概念色/严重级/阴影/圆角/动效/字阶全 Token 化；暗色=Token 整体镜像非滤镜；33KB 词账让 UI 文案与代码解耦 + dev-jargon 测试守门 | `apps/web/src/style.css`（Token 单源）+ `config/wording-bo3c.ts`（词账）+ `dev-jargon-guard.spec.ts`（守门测试） | 探隐深浅双主题升级批 + 文案纪律：先立 Token 表与词账，再谈换肤 |

**附赠三条（超出 10 条名额，但太值）**：
- **订阅预算**：ConsoleRunningCard 每运行任务一卡一订阅，超上限切面+提示行「其余见列表」——探隐多战士并行时的 SSE 连接预算管理（`components/domain/ConsoleOverview.vue` L52-80）；
- **表格几何预算**：表行 46px、列宽预算注释（14 列 1440 零横滚）——探隐账本表格列设计先做预算表（`style.css` 表格段注释）；
- **反偷警告**：① 38KB 单文件巨组件（PipelineWizard）不要学——探隐 vanilla JS 更要拆；② 五步向导已被它自己退役换单页表单（TaskCreateForm.vue 头部退役声明）——探隐建任务交互直接上单页；③ transport 故障不伪装未登录的四态统一哲学要整套抄，不能只抄一半。

---

## 附：分析方法备忘（供复查）

- 前端源码获取：Vite dev server 对 /src/*.vue 返回编译模块，其 base64 sourcemap 的 `sourcesContent[0]` 即原始 SFC——爬虫 BFS import 图 110 模块全量还原，与本地真身 diff 一致；
- live 抓取时间点：admin 会话，17 端点 GET，响应存档 /tmp/zhulong-crawl/live/；
- 本报告所有行号引用以本地真身 `ai-assisted-security-verification-platform/apps/web/src/` 为准。

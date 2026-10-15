# 烛龙 ZhuLong 界面漫游实录（walk-zhulong）

> 漫游日期：2026-10-15（admin-health 面自报「生成于 2026-10-15 15:46」）· 漫游舰：界面漫游舰（探隐委托）
> 对象：ZhuLong @ http://localhost:3081（Vite dev server，Vue 3 活体）
> 装备：python3 + playwright，channel="chrome" headless，视口 1440×900，全部 full_page 截图
> 截图目录：`shots/`（zhulong-01 ~ zhulong-27，共 27 张）· 结构化数据：`data/zhulong-walk.json`（27 条记录：文本/按钮/ href/ computed style 指纹）

## 只导航纪律执行声明

- **写操作仅一处**：登录 POST（admin）一次。
- 其余全部为 **GET 导航**：直连路由 + URL query 深链（`?tab=` / `?status=` / `?overview=` / `?verdicts=`——Tab 与筛选全部走 URL，零点击即达）。
- 点击过的东西（全部为导航级/展示级）：任务详情页内标签页（「历史 · 运行日志」「终审」）、漏洞行「查看详情」眼睛钮（= 路由跳转，源码注释证实「跳详情＝行点击旧径路由」）、昼夜切换（纯显示偏好，拍完已切回昼）、顶栏下载头带浮层展开（纯展示 popover，已 Escape 关闭）。
- **未触碰**：新建/启动/重跑/删除/判定/保存/探测/停用/重置密码/授权/导入/导出/上传——一个都没有。上面跑着真实渗透作业，全部截图为只读观察。

---

## 一、视图清单（27 视图）

| # | 路由 | 截图 | 页面呈现什么 | 可交互元素 | 视觉手法 |
|---|------|------|--------------|------------|----------|
| 01 | `/login` | [zhulong-01](shots/zhulong-01-login.png) | 登录卡：品牌渐变标题「烛龙 ZhuLong」+ 英文副名 AI SECURITY VERIFICATION PLATFORM + 用户名/密码/登录 | 表单×2 + 登录钮 | 360px 磨砂卡 + 双光晕背景；标题三色渐变字；局部 `--lg-*` token 命名空间 |
| 02 | `/` | [zhulong-02](shots/zhulong-02-home.png) | 首页满幅舞台：三级字栈 hero「睁眼为昼，照穿一切暗处」+ 定位句 + 五章故事轮播（降生/开眼/吐焰/化形/烛照）+ 三模式玻璃卡（开眼·DRAGON EYE / 吐焰·FLAME / 化形·SHAPESHIFT，各三条能力点） | 五章卡（深链 /story/:chapter）、「开始使用 →」、顶栏全族 | **全站唯一动效页**：homeHalo 光晕动画×3 元素、18s 轮换；玻璃卡 62% 白透；品牌蓝 #2563EB |
| 03 | `/story/kaiyan` | [zhulong-03](shots/zhulong-03-story-kaiyan.png) | 故事章 CHAPTER 02「开眼 · 视为昼」：正文 + 章末导航（上一章·降生 / 下一章·吐焰） | 上一章/下一章 | 超大章号「02」+ 章名中英对仗（Kaiyan）；教育叙事不弹窗、独立深链页 |
| 04 | `/projects` | [zhulong-04](shots/zhulong-04-projects.png) | 项目卡片网格：7 项目 + 类型筛选（全部/web/host/k8s/mobile/other）+ 分页 | 新建项目、成员、编辑项目、删除项目、类型 chip、分页器 | 卡片=名称+「敏感」徽标+类型 Tag+成员/创建人/创建时间 KV；**XSS payload 项目名（`<img src=x onerror=…>`）原样回显**——注入靶标活体在册 |
| 05 | `/tasks` | [zhulong-05](shots/zhulong-05-tasks.png) | 任务中心：七桶 KPI（12 全部/0 排队/0 运行/5 成功/3 失败/3 已取消/1 软删）+ 14 列任务表（阶段进度/状态/漏洞判定率/操作族） | 运行概览折叠钮、项目/引擎/模式筛选、行操作：查看详情/查看报告/查看漏洞/下载报告/失败原因/重跑/删除、批量删除、自动刷新 30s、SSE「实时」标 | **七桶 KPI 可点深链**；行内阶段点线微图（「1 段完成 1/1」「等待调度 4/4」）；状态徽章语义色 10% 透明底；「实时」绿标 |
| 06 | `/tasks?overview=1` | [zhulong-06](shots/zhulong-06-tasks-overview.png) | 运行概览区展开（URL SSOT 深链）：实时(0)+队列(0) 双空态文案（「暂无排队任务——已启动的任务将在此等待机器资源」） | 同 05 | 空态不是空白而是**带解释句的诚实空态**；ConsoleOverview 订阅预算位 |
| 07 | `/tasks?status=success` | [zhulong-07](shots/zhulong-07-tasks-status-filter.png) | KPI 桶深链落地：仅 5 条成功任务 | 同 05 | URL 即状态：分享/回溯链接化；过滤 chip「终审：…」同款语言 |
| 08 | `/tasks/11` | [zhulong-08](shots/zhulong-08-task-detail-success.png) | 成功任务详情（全页深链形态）：头带（名称+成功徽章+meta KV：项目/创建人/引擎 zhulong@2/模式 开眼/对象/阶段 1/1/成本）+ 页内 Tab（历史·运行日志/产物/漏洞关联/终审）+ 产物列表（04-findings-verify.md 3.4KB、report.md 1.6KB） | 返回任务列表、页内 Tab×4、产物 raw 链接 | 「暂无用量数据」诚实空态；产物=文件名+体积徽标 |
| 09 | `/tasks/12` | [zhulong-09](shots/zhulong-09-failed.png) | 失败任务详情：**建单锚 7c2996aa（可复制）**+ 成本三计数（USD 0.00 / 输入 29,116 / 输出 812 tokens）+ 失败原因内联 JSON「收齐门禁未在期限内补齐（required 产物缺失——超时收口）」 | 建单锚复制钮、页内 Tab | 建单锚=服务端日志 grep 直通；失败原文不美化、JSON 原样呈现 |
| 10 | `/vulns` | [zhulong-10](shots/zhulong-10-vulns.png) | 漏洞中心：严重分布 KPI（致命 2/严重 1/中 0/低 1/信息 9）+ 确认率 8% + **三态终审 KPI（11 疑似/1 确认是/1 确认非）**+ 11 列表（标题蓝链/等级/终审/POC/静态/动态/引擎/任务/敏感/更新时间/操作） | KPI 三卡深链、全部/白盒/黑盒、高级筛选、任务/等级下拉、行：查看详情/判定/导出/删除、导出、自动刷新 30s | SeverityBadge 五档色；「疑似/确认是/确认非」三词终审域；敏感项目签；「按此任务筛选」行内深链 |
| 11 | `/vulns?verdicts=confirmed` | [zhulong-11](shots/zhulong-11-vulns-verdict-filter.png) | 三态 KPI 深链：1 条（seed-3 致命·确认是），确认率变 100% | 同 10 | KPI 与筛选面板**同源互斥**（点 KPI 改写 verdicts 键）；过滤 chip「终审：确认是」 |
| 12 | `/vulns/13` | [zhulong-12](shots/zhulong-12-vuln-detail-pending.png) | **疑似（未终审）漏洞详情**：三列骨架（左 140 章节导航：识别信息/概述/机理/证据/影响/PoC/修复｜中 六章正文｜右 260 操作卡）+ 头带（标题+疑似徽标+待终审+敏感项目签） | POC详情、导出漏洞、删除漏洞、右列**终审卡常开**（未判=表单直出） | 识别信息=定宽灰 label+值 KV 网格；证据章含响应头原样摘录代码块（server: cloudflare…）；CWE-532 双语等级 |
| 13 | `/vulns/3` | [zhulong-13](shots/zhulong-13-vuln-detail-confirmed.png) | **判过（确认是）漏洞详情**：中列追加「终审」章（确认是·终审通过·等级致命·判定人 admin·判定时间）+ CVSS 向量串；右列默认切「标注」Tab | 「重新判定」展开、标注时间线 | 判过态默认展示**判据与标注**而非表单——读态优先；右列单卡双 Tab（终审｜标注 n 条） |
| 14 | `/vulns/13/poc` | [zhulong-14](shots/zhulong-14-vuln-poc.png) | PoC 维护页：面包屑（漏洞中心/WB-3 详情/POC 与复现）+ **四元组（前置条件/复现步骤/预期结果/验证方法）**+ 标注时间线 | 保存 PoC、导出 Markdown、标注时间线展开 | 四元组=四块编辑区；页头带对象指纹（等级/已提供/CWE/引擎/出处行号） |
| 15 | `/assets?tab=resources` | [zhulong-15](shots/zhulong-15-assets-resources.png) | **算力资源池**：四 KPI（6 接入·自动 1 手动 5 / 1 在线 / 0/6 机器槽占用 / 3 离线·宽限·归档）+ 路径一·自动接入说明 + CLI 探测真值表（claude 2.1.238 / opencode 1.19.0 / node v26.5.0 / demo / git 2.50.1 / docker 29.4.0，含完整路径）+ 教育文案（停用语义/为何整行不可停） | 重新探测、启用开关 | 绿色「在线」徽章（#16a34a 系）；探测真值表=能力面透明化；说明文案即教育 |
| 16 | `/assets?tab=catalog` | [zhulong-16](shots/zhulong-16-assets-catalog.png) | **能力目录 Tab 被 flag 隐藏**：`ZL_SHOW_CATALOG` 关 → `?tab=catalog` **静默回退资源池**（截图与 15 同页面）——防御性回退而非 404 | 同 15 | 服务端 feature flag 客户端镜像；未知/禁用 tab 不报错不落空 |
| 17 | `/assets?tab=targets` | [zhulong-17](shots/zhulong-17-assets-targets.png) | **测试对象**：登记对象/上传 + 7 条（文档/代码、上传/本机路径、私有、版本指纹 hash、更新时间） | 登记对象、上传、上传版本/下载/删除 | 版本指纹=短 hash 徽标；**XSS payload 对象名 + secret-poc.txt 敏感文件明文在册** |
| 18 | `/assets?tab=environments` | [zhulong-18](shots/zhulong-18-assets-environments.png) | **测试环境**：5 条 Web endpoint（blocked-loopback-direct / bypass-decimal-ip(2130706433) / bypass-metadata-nipio(169-254-169-254.nip.io) / bypass-loopback-nipio + XSS 名环境）+ 凭据/指纹健康（健康/异常/未探活） | 登记环境、健康检查 | **SSRF 绕过测试矩阵 live 在册**（nip.io/十进制 IP/对照组）；健康态三词色点 |
| 19 | `/assets?tab=knowledge` | [zhulong-19](shots/zhulong-19-assets-knowledge.png) | **知识图谱**：三计数大卡（19 漏洞类 / 227 合规规则 / 5 提权五族） | （只读计数卡） | KPI 大数卡；词面 live 为「知识图谱」（路由图文档写「知识聚合」，以活体为准） |
| 20 | `/assets?tab=engines` | [zhulong-20](shots/zhulong-20-assets-engines.png) | **引擎**：5 插件卡（演示引擎 demo / GenCPT / GenLPE / **探隐红队 tanyin（黑盒·enabled·发现 0）** / 烛龙 zhulong·发现 13）+ 版本/色系/enabled 态 + 「插件安装/升级/卸载属 BO4」声明 | 检查更新×5 | **探隐已注册为 ZhuLong 引擎插件**（tanyin）；「发现 N」=引擎产出计数；写操作整体让位声明 |
| 21 | `/downloads` | [zhulong-21](shots/zhulong-21-downloads.png) | 下载中心：9 条生成物（评估集/漏洞清单/任务报告三类）全部**已过期**（7 天过期制） | 自动刷新 30s（过期项无可点动作） | 过期=状态词+禁用双落；过期清扫制度真实运转 |
| 22 | `/admin/users` | [zhulong-22](shots/zhulong-22-admin-users.png) | 用户管理（admin）：**顶部平台健康五族 KPI**（Findings 13·24h 新增 6·查询 0ms / 任务吞吐 新建 9·完成 3·失败 4 / WAL journal_mode·synchronous·busy_timeout / 计划任务 0 / 队列 0·SSE 连接 0）+ 用户表（admin（我）不能禁用自己 / wgen01·penter 安全工程师 / viewer 漏洞审计员，4 在线） | 新建用户、编辑/禁用/重置密码/授权/删除用户 | admin-health 面嵌入用户页顶部（运维面与管理面同页）；「不能禁用自己」=自禁保护词 |
| 23 | `/`（夜） | [zhulong-23](shots/zhulong-23-home-dark.png) | 首页暗色镜像：同一 hero/轮播/玻璃卡整体换夜 | 同 02 | **全 Token 镜像非滤镜**（html class="dark"）；eye #0284c7→#38bdf8、bg #f6f7f9→#0f172a 等；光晕动画照常 |
| 24 | `/tasks`+浮层 | [zhulong-24](shots/zhulong-24-hdr-downloads-popover.png) | 顶栏下载中心头带下拉：近 5 条（类型 Tag 评估集/清单 + 名称 + 已过期态）+「查看全部」 | 头带触发钮、查看全部 | 顶栏常驻入口+下拉不打断当前页；过期项灰显 |
| 25 | 404 | [zhulong-25](shots/zhulong-25-not-found.png) | 任意未知路由：「页面不存在 / 资源不存在或不可见 / 返回首页」 | 返回首页 | 四态纪律的错误态样本：一句话+一条出路，无堆栈无代码 |

补拍说明：12/13/14 为第二轮补拍（漏洞行「查看详情」导航钮取到 /vulns/13 与 /vulns/3）；26/27 见下节。编号 12–14、26–27 与首轮流水的空档即此。

## 二、重点深描（委托焦点五处）

### 2.1 任务详情：实时观察 + live-only 终端（08/09 + 补拍 26/27）

- **详情双形态实证**：列表侧面板与 `/tasks/:id` 全页共用同一 `TaskDetailPanel`（源码注释「容器差异面：完整宽度页头＋返回面包屑」），live 两处 DOM 同构。
- **live 面结构**：`tdp-live` 区含断线词位（connecting/open/disconnected）+ 终端面板（TaskTerminalPanel 三态自治）+ 活动流时间线。**当前 live 无运行中任务（队列 0/运行 0），live-only 终端的实时流与「── 继续 ──」断线分界未见到动态态**——这是本次漫游的诚实边界：只导航纪律不允许造一个运行任务。
- **页内 Tab 族**（[zhulong-26](shots/zhulong-26-task-detail-runlog.png)）：「历史 · 运行日志」点开=run.log 查看器，键值行 `task_id=11` + `run_id=imp-1792048298-l7este`（**锚链五层下钻的服务端 grep 词**），本例诚实空态「本 run 无服务端运行日志」（import 的历史会话无日志——不伪造）；[zhulong-27](shots/zhulong-27-task-detail-verdict-tab.png)「终审」Tab=漏洞判定率 0/3（0%）+ 查看漏洞深链。
- **失败任务面**（09）：建单锚 `7c2996aa` 以复制钮呈现；失败原因以原始 JSON 串内联（「收齐门禁未在期限内补齐——超时收口」）；成本三计数（USD/tokens 入/出）tabular 呈现。

### 2.2 终审大卡（12/13）

- **未判态**（12，/vulns/13 疑似）：右列终审卡**常开直出表单**（源码：「未判＝常开」），三态大卡（确认是/确认非/疑似）+ 等级 + 漏洞类 + 理由注记。
- **判过态**（13，/vulns/3 确认是）：中列追加「终审」章（结论/等级/判定人/判定时间四行），右列默认切「标注（n 条）」Tab，判定动作退为「重新判定」——**读态优先，写操作折叠**。
- 词面三词域实测：**疑似 / 确认是 / 确认非**（列表 KPI、行徽章、详情章三处同词）；驳回原因五词下拉未展开（保守未点）。

### 2.3 资产页 Tab（15–20）

- 活体为**五 Tab**（算力资源池/测试对象/测试环境/知识图谱/引擎）；设计中的第六 Tab「能力目录」被服务端 flag `ZL_SHOW_CATALOG` 藏起，深链 `?tab=catalog` 静默回退资源池（16 与 15 同页）。
- 资源池=探测真值表（六个 CLI 的版本+路径+启用态）+「为何整行不可停」教育文案；环境 Tab=SSRF 绕过矩阵五条在册；引擎 Tab **已有「探隐红队 tanyin」插件（enabled·发现 0）**。

### 2.4 漏洞中心（10/11）

- 三态终审 KPI（11 疑似/1 确认是/1 确认非）与严重分布 KPI（致命 2…信息 9）双卡阵；确认率 8% 环形。KPI 点击=写 `?verdicts=` 深链（与高级筛选面板同源互斥）。
- 表 11 列 + 行展开附加信息行（行点击=展开，跳详情退役、标题蓝链+眼睛钮=唯一直达——源码注释活体印证）。

### 2.5 项目页（04）

- 卡片网格 + 类型 chip 筛选 + 分页；卡=敏感徽标/类型 Tag/成员/创建人/创建时间。**三条 XSS payload 项目名与 payload 对象名、敏感文件（secret-poc.txt）在库可见**——靶场注入面在 UI 层完整回显。

## 三、视觉系统实测（getComputedStyle 取证）

### 3.1 Token 表（昼/夜全镜像，:root 实读）

| Token | 昼 | 夜 | 语义 |
|-------|----|----|------|
| `--zl-eye` | #0284c7 | #38bdf8 | 开眼蓝 |
| `--zl-flame` | #f59e0b | #fbbf24 | 吐焰琥珀（=--zl-primary） |
| `--zl-form` | #7c3aed | #a78bfa | 化形紫 |
| `--zl-bg / card / well` | #f6f7f9 / #ffffff / #f8fafc | #0f172a / #1e293b / #334155 | 三层底 |
| `--zl-fg / fg-muted` | #0f172a / #64748b | #e2e8f0 / #94a3b8 | 双字色 |
| `--zl-danger / info` | #dc2626 / #0284c7 | #f87171 / #38bdf8 | 语义 |

品牌蓝 **rgb(37,99,235)=#2563EB**（顶栏激活 tab 等 6 处）；暗色切换=`html.dark` class，**Token 整体重映射非滤镜**（23 号截图实证）。

### 3.2 字体与数字

- 字体栈：`-apple-system, system-ui, PingFang SC, HarmonyOS Sans SC, Microsoft YaHei, sans-serif`（零 webfont 依赖）。
- 计数/KPI 用 tabular-nums（tokens 29,116 千分位、0/3（0%）等对齐呈现）。

### 3.3 动效预算（animation-name 全站扫描）

- **27 个视图里只有首页存在动画**：3 个元素挂 `homeHalo-b4e148ca`（scoped 命名，含 hash）——光晕轮换。任务/漏洞/资产/详情全部 0 动画元素。**动效是预算管理出来的**：数据页零动效，门面页才有舞台。
- 进度循环动画（150/200/300ms ease-out 档）在无运行任务时不可见。

### 3.4 色彩手法

- 徽章/状态底=语义色 10% 透明（如 ok 绿 `oklab(...0.086 0.639 0.290 / 0.1)`、红 `0.862 0.149 0.149 / 0.1`）——Tailwind 4 的 oklab()/color() 现代色彩函数大量在用。
- 层级=三层底（bg→card→well）+ 阴影三级 + 圆角 12/9/99 胶囊；徽标=SeverityBadge 五档色 + VerdictBadge 三态 + 「敏感」签。

## 四、与源码分析的交叉印证 / 偏差

1. **数据在涨**：路由图文档记 7 findings/4 任务；本次活体 13 findings（24h 新增 6）/12 任务（5 成功/3 失败/3 取消/1 软删）——靶场仍在被使用。
2. 资产「六 Tab」→ **活体五 Tab**（catalog flag 关，深链静默回退，防御性好品味）。
3. 知识 Tab 词面=「知识图谱」（非「知识聚合」）。
4. admin-health 五族 KPI **嵌在用户管理页顶**（非独立路由）。
5. 漏洞行导航=标题蓝链+眼睛钮；行点击=展开附加行（与源码 [c-3.2] 注释一致）。
6. 「探隐红队 tanyin」引擎插件已在 ZhuLong 注册（enabled·黑盒·发现 0）——**两个系统已互为引擎/宿主关系**。
7. 引擎任务 genlpe@1（黑盒 LPE 生成器）在任务表真实跑过（2 失败样本）。
8. 下载中心 9 条全过期、过期项无动作——7 天过期制不是摆设。

## 五、探隐 v0.9d 落点建议

> 依据：本次 27 视图活体观察 + 4-zhulong.md 源码级路由图。探隐=纯手写 HTML/CSS/vanilla JS 只读投影，以下全部给「零框架可等价重写」的落法。

1. **引擎身份落点（最高优先·新发现）**：探隐（tanyin）已作为 ZhuLong 引擎插件在册但「发现 0」。v0.9d 若产出 findings 喂给 ZhuLong（POST /api/imports 或插件协议），ZhuLong 引擎卡会显示真实计数——**探隐可借 ZhuLong 的终审/导出闭环完成人审段，自己专注作战与账本**。落点：探隐侧加一个「findings 导出格式=ZhuLong imports 契约」的出口即可打通。
2. **URL SSOT 键法直接抄**：活体实证五族深链（`?tab=`、`?status=`、`?overview=`、`?verdicts=`、`?highlight=`）。探隐 v0.9d 的十三账浏览器/任务流页，把筛选+分页+哈希定位全进 URLSearchParams，未知键忽略、默认值省略——分享与回溯即链接。
3. **三态裁决词域**：抄「疑似/确认是/确认非」三词（探隐判据：待定/成立/不成立），KPI 三卡+行徽章+详情章三处同词；驳回/不成立必选原因词表（五词域）。
4. **终审卡双态**：未判=右列常开表单；判过=中列结论章（判定人/时间/理由）+右列默认标注时间线、写操作退为「重新判定」。探隐人工复核卡照此双态，读态优先。
5. **七桶 KPI 可点过滤**：值=服务端口径（不受当前筛选影响），点击=写 URL 键。探隐九门流程仪表同构（进行中/阻断/通过/回流…桶）。
6. **行内阶段点线 + 判定率列**：任务行「1 段完成 1/1」「等待调度 4/4」+「漏洞判定率 0/3（0%）」——探隐任务行内嵌门进度点线与账本落笔率，成本≈35 行/行。
7. **锚链复制钮**：建单锚 7c2996aa 一键复制 + run.log 头部 `task_id=/run_id=` 键值行。探隐每笔作业带哈希链锚，日志面板头部同款键值行+`grep` 复制。
8. **诚实空态词域**：「暂无排队任务——已启动的任务将在此等待机器资源」「本 run 无服务端运行日志」「不能禁用自己」——空态都带一句机制解释。探隐四态（骨架/错误/空/数据）逐页补齐，空态文案写机制不写「暂无数据」。
9. **动效预算纪律**：全站仅门面页 3 个动画元素。探隐 v0.9d 动效清单收敛为：首页光晕 1 处 + 进度循环 + 行 pulse 三种，其余全静态。
10. **暗色=Token 镜像**：探隐深浅双主题按上表模式做整套变量重映射（html class 切换），杜绝 filter 反色。
11. **运维健康面**：admin-health 五族 KPI（findings 聚合/任务吞吐/WAL/计划/队列·SSE）嵌管理页顶部——探隐可做「链健康」卡组（哈希链深/门流水/战士心跳）嵌在设置或状态页。
12. **能力透明化表**：资源池探测真值表（版本+路径+启用）+「为何不可停」教育文案——探隐战士登记面（哪个 CLI、哪些能力、何时心跳）同款。

## 附：复查路径

- 截图 27 张：`shots/zhulong-01-login.png` … `shots/zhulong-27-task-detail-verdict-tab.png`（full_page，1440 宽）。
- 结构化记录：`data/zhulong-walk.json`（每视图：final_url/text_head/buttons/hrefs/vis{tokens,topColors,animEls,animNames,fonts}）。
- 登录复现：`#login-user`/`#login-pass`/`[data-test=login-submit]`；Tab 深链复现：`/assets?tab=engines` 等。

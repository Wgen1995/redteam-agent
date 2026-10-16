# 烛龙 ZhuLong 活体巡访实录（walk-zhulong-live · 批#1）

> 巡访日期：2026-10-16 14:35–15:10（CST）· 巡访者：界面漫游舰（探隐委托，无图像能力，全 DOM/API 文本层）
> 对象：ZhuLong @ http://localhost:3081（admin 账号本地授权登录）——**本次巡访它是被打击的靶场**，ARTEX/CSAI 的战斗数据里有它。
> 装备：python3 + playwright，channel="chrome" headless 1440×900，全部导航 wait_until="domcontentloaded"。
> 焦点：项目/资产/发现/导入面 + **靶场侧的战斗痕迹**（攻击者留下的行）。

## 0. 环境前置声明（重要，如实记录）

巡访开始时 **3081/7090 双双宕机**（lsof 无监听；ARTEX 活动流里也有 planner「规划者直连 127.0.0.1:3081 被拒（可能服务仍在启动）」的历史记录——宕机发生在战斗期间，规划者自带重试意图绕过了它）。为完成巡访，从本仓源码启动了开发栈：
- `apps/server: pnpm dev`（tsx watch，默认 7090）与 `apps/web: pnpm dev`（vite --port 3081）。
- 启动前以 sqlite3 只读模式核库：tasks 表 14 行**全为终态**（cancelled 3 / failed 6 / success 5），**0 排队 0 运行**——启动不会触发孤儿恢复改写任何任务。
- 启动日志实证（无副作用）：「LocalExecutor 首启登记：资源 #1（复用）」「烛龙平台服务已启动：http://127.0.0.1:7090」「孤儿容器清扫：清除 0 个 zl-sandbox-* 残容器」。巡访全程未建/未跑/未判任何东西，栈保持运行未关（后续巡访可复用）。

## 1. live 快照事实（2026-10-16 14:4x 实测）

| 项 | 实测值 | 证据 |
|---|---|---|
| 项目 | **10 个**（上轮 7）+类型筛选 web/host/k8s/mobile/other + 分页 | /projects DOM「10 个项目」 |
| 任务 | 14 条七桶：全部 14 / 排队 0 / 运行 0 / 成功 5 / **失败 5** / 已取消 3 / 软删 1 | /tasks KPI DOM |
| 漏洞 | 13 条：致命 2 / 严重 1 / 中危 0 / 低危 1 / 信息 9；**确认率 8%**；三态终审：**11 疑似 / 1 确认是 / 1 确认非** | /vulns KPI DOM + /api/findings |
| 资源池 | 7 接入（自动 1·手动 6）/ 1 在线 / 0/7 机器槽 / 4 离线·宽限·归档 | /assets?tab=resources DOM |
| 测试对象 | 7 条（上传/本机路径，版本指纹 hash） | /assets?tab=targets DOM |
| 测试环境 | **9 条**（SSRF 绕过矩阵 + 攻击者新建环境） | /assets?tab=environments DOM |
| 引擎 | 5 插件（demo/GenCPT/GenLPE/**探隐红队 tanyin**·发现 0/烛龙 zhulong·**发现 13**） | /assets?tab=engines DOM |
| 用户 | 4 个：admin / wgen01·安全工程师 / **penter·安全工程师（10-15 新建）** / **viewer·漏洞审计员（10-15 新建）** | /admin/users DOM |
| 平台健康 | 生成于 2026-10-16 14:37；Findings 总数 13·24h 新增 6·查询 0ms；任务吞吐 24h 新建 7·完成 2·失败 4；WAL journal_mode=wal·synchronous=1·busy_timeout=5000ms；计划任务 0；队列 排队 0·运行 0·SSE 连接 0 | /admin/users 顶部健康面 DOM |
| 下载中心 | 9 条生成物**全部已过期**（7 天过期制） | /downloads DOM |

**与 2026-10-15 首轮（walk-zhulong.md）差分**：项目 7→10（+3：i48-rebind-takeover、i48-csrf-formenc、i48-csrf-textplain）；任务 12→14（+2 i96 系列）；资源池手动 5→6；环境 5→9；用户 2→4；findings 13→13（24h 新增 6=旧轮口径差异）。**这些都是攻防双方留下的战斗痕迹**（见 §3）。

## 2. 逐页走查

### 2.1 项目管理（/projects）
- 卡片网格：名称 + 「敏感」徽标 + 类型 Tag + 成员/创建人/创建时间 + 成员/编辑项目/删除项目；类型 chip 筛选 + 分页。
- 10 项目全录：i48-rebind-takeover（web·敏感·admin·10-15 16:38）、i48-csrf-formenc（web·敏感·10-15 16:25）、i48-csrf-textplain（同批）、wgen01-probe（other·敏感·**创建人 wgen01**·10-15 15:11）、`<img src=x onerror="window.__xsstest1=1">XSSPJ`（web·敏感·payload 名项目）、ADMIN-SEC（web·敏感）、以及原 7 项目（含 seed 项目与 XSS payload 项目）。

### 2.2 任务中心（/tasks）
- 七桶 KPI（全部 14/排队 0/运行 0/成功 5/失败 5/已取消 3/软删 1）+ 14 列表（勾选框/序号/任务名称/项目/资源池/引擎/模式/测试对象/阶段进度/任务状态/创建人/创建时间/漏洞判定率/操作）+ 项目/引擎/模式筛选 + 自动刷新 30s + 「实时（SSE）」标。
- 工具位：**导入历史会话**、**新建任务**、批量删除。
- 行操作族：查看详情/查看报告/查看漏洞/下载报告/失败原因/重跑/删除。
- 新战斗任务（DOM 逐字）：#1 i96-atomic-poc63e2f0db（ADMIN-SEC·内置共享执行器·**genlpe@1**·开眼·blocked-loopback-direct·环境·等待调度 3/3·**失败**·admin·10-15）；#2 i96-chunk-merge-xss-audit395bf8fb（同配置·等待调度 25/25·**失败**）。
- 运行概览折叠区：实时(0)+队列(0) 双空态（「暂无排队任务——已启动的任务将在此等待机器资源」诚实空态）。

### 2.3 任务详情（/tasks/:id，三个实测样本）
- **#11（成功·zhulong@2·开眼·wgen01-probe 项目·创建人 wgen01）**：头带（名称+成功徽章+项目/创建人/引擎/模式/测试对象 —/阶段 1/1）+ 成本与用量「暂无用量数据」+ 四页内 Tab（历史·运行日志/产物/漏洞关联/终审）+ 产物列表（04-findings-verify.md 3.4KB、report.md 1.6KB）。
- **#9（失败·i56-runner-audit·genlpe@1）**：**建单锚 caa5b9fc（服务端日志 grep 词）** + 失败原因内联原始 JSON `{"kind":"default","message":"claim 响应丢失（kill 未消费——幽灵任务回收·资源槽释放）"}` + 产物 evil.md 43B。
- **#8（已取消·payload 名任务）**：任务名/项目名/测试对象全是 XSS payload 原样回显（`<svg onload=…>XSSTASK`、`"><script>…</script>XSSOBJ`）——**靶场注入面在 UI 层完整回显**（与 ARTEX finding#25 存储型 XSS 互证）。

### 2.4 漏洞中心（/vulns）
- KPI 阵：P1 漏洞（严重≥High）3 · 严重分布（致命 2/严重 1/中危 0/低危 1/信息 9）· **确认率 8%** · 三态终审（11 疑似「AI 初判，待人工终审」/1 确认是「终审通过，真实漏洞」/1 确认非「终审驳回，误报」）。
- 11 列表：标题/等级/终审/POC/静态 PoC/动态 PoC/引擎/任务/敏感/更新时间/操作（查看详情/判定/导出/删除）+ 全部/白盒/黑盒 + 高级筛选 + 任务/等级下拉 + 行内「按此任务筛选」深链。
- 13 条全录（API）：#13/12/11/10/9/8/6/5/4 = 信息·疑似（WB-1/2/3「默认配置不当」「日志敏感信息写入」置信 实证/线索，引擎 zhulong，任务 #11 走查样例·种子任务）；#7 低危·疑似；#2 严重(High)·疑似；#1 致命·**确认非**（seed-1）；#3 致命·**确认是**（seed-3）。
- **确认是详情（/vulns/3，DOM 全结构）**：三列骨架（左 140 章节导航：识别信息/概述/机理/证据/影响/PoC/修复/**终审**｜中 六章正文｜右 260 操作卡）+ 头带（标题+seed-3+确认是+终审通过+敏感项目签）+ 操作（POC详情/导出漏洞/删除漏洞）+ 右列**双 Tab（终审｜标注 6 条）**，判过态默认展示判据（结论/等级 致命/判定人 admin/判定时间 2026-09-05 21:33/标注时间线），判定动作退为「重新判定」——**读态优先，写操作折叠**。
- 识别信息字段族：编号/等级（致命 Critical）/漏洞类（默认配置不当）/CWE-16/置信（线索）/引擎 zhulong/映射器 seed-v1/任务/敏感项目/出处（nginx/app.conf:12）/来源（新发现）/创建·更新时间。证据章含 CVSS 向量串与「Cookie 未带 Secure 标记——仅内网 HTTP 场景可利用·生产 HTTPS 下不成立」的**诚实边界描述**。

### 2.5 资产管理五 Tab（/assets?tab=…）
- **算力资源池**：路径一自动接入（本机 CLI 探测真值表：claude 2.1.238/opencode 1.19.0/node v26.5.0/demo/git 2.50.1/docker 29.4.0 + 完整路径 + 启用开关 + 「停用某个 CLI=本机不再接该类任务（能力闸门即时生效）」+「node 为内置脚本运行时，停用将连带停用 demo」教育文案）+ 执行器卡（内置共享执行器·常开·0/1 槽·在线·刚刚·探测报告▾；**wgen-MBP 手动 T7·离线失联 27 天**；pentest-runner-01·离线 1 天；**i41-masterkey-verify·已停用·CLI 能力 zzz-nonexistent-cli**；i41-verify-2·已停用；**i56-audit-runner-01·离线 23 小时**；**i96-audit-runner-01·离线 22 小时**）+ 池活动时间线（接入/停用/重新探测，含「停用 i41-verify-2 admin 2026-10-15 14:40」等防守方动作）+ 路径二手动接入（**接入令牌表**：生成时间/备注/有效期至/状态/使用机器——「i96 chunk-merge XSS chain audit」令牌已被 i96-audit-runner-01 使用等 13 行）。
- **测试对象**：7 条（名称/类型 文档·代码/来源 上传·本机路径·仓库/可见性 私有/版本指纹短 hash/操作 上传版本·下载·删除）。战斗痕迹：xss-render-poc-html、`"><script>…</script>XSSOBJ`（本机路径）、upload-test.bin、poc-code.py、**secret-poc.txt**（敏感文件名明文在册）。
- **测试环境**：9 条（名称/类型/endpoint/凭据/指纹健康/健康检查）。**SSRF 绕过矩阵 + 攻击新增**：i214-ssrf-recheck（`http://deadbeef.c0a89303.rbndr.us:18999/C3-rebind-poll2`·**健康**）、i190-op-probe-RESIDUE（127.0.0.1:7090/api/health·已设凭据）、i190-priv-probe/probe2（10.255.255.1:1）、`<IMG SRC=x OnErRoR=…>XSSENV`、blocked-loopback-direct、bypass-decimal-ip（2130706433）、bypass-metadata-nipio（169-254-169-254.nip.io·**异常**）、bypass-loopback-nipio（127-0-0-1.nip.io:7090·**健康**）。
- **知识图谱**：三计数卡（19 漏洞类 / 227 合规规则 / 5 提权五族）。
- **引擎**：5 插件卡（名称/版本/色系 白盒·黑盒/enabled/发现 N/检查更新）+「插件安装/升级/卸载属 BO4」声明。**烛龙 zhulong·白盒·发现 13**；**探隐红队 tanyin·黑盒·enabled·发现 0**（探隐已注册为 ZhuLong 引擎插件但尚无产出）。

### 2.6 下载中心（/downloads）
9 条生成物（评估集/漏洞清单/任务报告三类）**全部已过期**（7 天过期制，最早 9-07）——过期=状态词+无可点动作；「生成后 7 天内可下载」副标。

### 2.7 用户管理（/admin/users）
- 顶部平台健康五族 KPI（见 §1 表）——**运维面与管理面同页**。
- 用户表：admin（我·不能禁用自己）/ wgen01 安全工程师 / penter 安全工程师（10-15 新建）/ viewer 漏洞审计员（10-15 新建）；操作 编辑用户/禁用/重置密码/授权/删除用户。全部显示「在线」。

## 3. 靶场侧战斗痕迹清单（与 ARTEX/CSAI 发现交叉互证）

| 痕迹（ZhuLong 侧 DOM） | 对应攻击侧证据 |
|---|---|
| 环境 i214-ssrf-recheck（rbndr.us 短 TTL rebinding 端点，指纹 健康） | ARTEX #50「SSRF 防护多类通用绕过…短 TTL」、播报板压缩事件 #240 重派复核 |
| 环境 bypass-decimal-ip / bypass-metadata-nipio / bypass-loopback-nipio + 对照组 blocked-loopback-direct | ARTEX #7/#50 绕过矩阵 + CSAI exploit/ssrf-healthcheck-dns-bypass 事实 |
| 环境 i190-priv-probe（10.255.255.1 内网探针） | ARTEX #50 ①私网段直址实证 |
| 任务 i96-atomic-poc / i96-chunk-merge-xss-audit（genlpe 引擎·失败） | ARTEX #20「runner 分片上传 sha256 穿越」的 audit 任务（产物 evil.md 43B） |
| 任务 i56-runner-audit（失败原因「claim 响应丢失——幽灵任务回收」） | ARTEX #51/#249 Multica/ZhuLong daemon claim 面攻测的伴生噪声 |
| 资源池 i41-masterkey-verify（CLI=zzz-nonexistent-cli·已停用）/ i41-verify-2 / i56 / i96-audit-runner-01 + 接入令牌「i96 chunk-merge XSS chain audit」 | ARTEX #15「路径穿越读到 ZhuLong master.key」的验证机群 + **ZhuLong runner 注册面被当跳板**（接入令牌→注册 runner→接任务） |
| 项目 i48-rebind-takeover / i48-csrf-formenc / i48-csrf-textplain | ARTEX #41「7090 零来源校验+CSRF 面」的 form/textplain 对照实验项目（DNS rebinding 接管链） |
| 用户 penter / viewer（10-15 新建） | 攻击侧以 admin 权限造的低权账号（对应 ARTEX #14「低权账号目录探测 oracle」实验） |
| 对象/项目/任务名中的 XSS payload 原样回显 | ARTEX #25「存储型 XSS」+ ZhuLong 侧注入靶标设计 |

**结论**：ZhuLong 库里躺着**整场攻防的弹壳**——环境表是攻击者的 SSRF 实验台账，资源池是攻击者注册的跳板机群，用户表是攻击者造的低权账号，项目表是攻击者的实验分组。靶场 UI 把这些当正常业务行展示（可见性=私有/共享），**没有「这是攻击留下的」标识**——这本身是给探隐观察面的一个设计输入。

## 4. 表单/参数逐项（open-then-cancel 取证，全部取消未提交）

- **新建项目**（/projects）：项目名称*（ph「例如：电商中台安全审计」）/ 业务域*（web▾）/ 敏感 checkbox（默认勾选）/ 成员（可选·按角色 安全工程师/漏洞审计员 两组选择用户+＋添加）。动作：取消/创建项目。
- **新建任务**（/tasks）：**能力（引擎×模式）选择器**——引擎卡列表（演示引擎 demo v2 白盒·GenCPT·GenLPE·探隐红队 tanyin·烛龙 zhulong v2 白盒 发现 13，各带 enabled 态）/ 模式二选一（**开眼=广域照亮（广域探索）/ 吐焰=定点灼穿（深度挖掘）**）/ 测试环境（我的＋共享，实测下拉含 i214-ssrf-recheck（共享））/ 算力（内置共享执行器·默认共享·不可选）/ **参数**（按引擎 manifest 声明动态渲染，当前引擎「本插件未声明参数」）/ 任务名称。动作：**创建并开始**（单一动作=建即跑，无「只建不跑」）。
- **导入历史会话**（/tasks）：引擎（烛龙 ZhuLong▾）/ **会话目录**（text，ph「/sessions/demo-audit」）/ 项目（i48-rebind-takeover 等）/ 关联对象（无▾）。动作：取消/导入。——**这就是 ARTEX #21「/api/imports sourceDir 任意目录读取」的 UI 面**：一个自由文本目录输入框。
- **登记对象**（/assets?tab=targets）：名称* / 类型（代码▾）/ 来源（仓库▾）/ 路径* / 可见性（私有▾）。动作：取消/创建。另有「上传」入口（文件上传面，对应 #25 任意扩展名上传）。
- **登记环境**（/assets?tab=environments）：名称* / 类型（Web▾）/ endpoint* / 可见性（共享▾）。动作：取消/创建。
- **新建用户**（/admin/users）：用户名 / 密码（至少 8 位）/ 确认密码 / 角色（安全工程师▾）/ 初始项目（可选）。动作：取消/创建。
- 漏洞判定（/vulns/:id 右卡）：未判=终审表单常开（三态大卡 确认是/确认非/疑似 + 等级 + 漏洞类 + 理由注记）；判过=标注 Tab + 重新判定（见 §2.4）。

## 5. 给探隐的观察（详见 live-recon-1.md）

1. **三态终审**（疑似/确认是/确认非）+ 确认率 KPI + 读态优先的详情页——比 ARTEX 的「全 pending」成熟。
2. **PoC 四元组**（前置条件/复现步骤/预期结果/验证方法）独立维护页 + 标注时间线。
3. **URL 即状态**（?tab=/?status=/?verdicts= 深链）——巡访/自动化友好。
4. **诚实空态**（「暂无排队任务——已启动的任务将在此等待机器资源」「本 run 无服务端运行日志」）。
5. **建单锚**（caa5b9fc）= 服务端日志 grep 直通词，失败原因原文 JSON 不美化。
6. **下载 7 天过期**让下载中心全是尸体——报告类产物的可及性设计反面教材。

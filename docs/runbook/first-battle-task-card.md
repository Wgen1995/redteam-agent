# 首仗任务卡草案（ZhuLong·3081）· 2026-10-20

> 定位：**校准器，不是里程碑**（全史综合档发现#1：42仗全是老TanYin五宿主实跑，新 cli/warrior 运行时 181 测绿但零实战——首仗即首战，首考=立基线不比旧）。
> 依据：docs/design/2026-10-20-first-battle-checklist.md（硬前置+预填战书）、docs/FIRST-BATTLE-RUNBOOK.md（五步操作单）、docs/design/2026-10-20-full-history-synthesis.md §⑤A桶/§⑥路线。
> 本卡=点火时 add-goal/add-scope/战书(mission)的**内容底稿**；点火本身照 docs/runbook/first-battle-checklist.md 逐行走。

## 一、目标

| 项 | 值 |
|---|---|
| 目标 | ZhuLong 平台靶场 `http://127.0.0.1:3081`（用户自有仓只读起服，授权内） |
| 授权 | 本地靶场自授权：操作员=用户；授权八问答案见§五（add-goal --auth-sha256 真校验链，无豁免） |
| egress | loopback only（起服用 /tmp/zl-loopback-shim.cjs 收窄 127.0.0.1；shim 执法，见 RUNBOOK 第一步） |
| 白盒面 | 烛龙无源码授权→**跳过白盒车道A，记「无白盒面」**（first-battle-checklist:17 点火序列第2步原文） |

## 二、范围预览（include 面）

ZhuLong API 面（apps/server/src/routes 实测 15 组）：`auth`（登录/会话）、`admin`、`assets`、`downloads`、`events-stream`、`findings`、`health`、`pipelines`、`projects`、`run-log`、`runner`/runner-artifacts-mem/runner-dist、`schedules`、`tasks`、`terminal-stream`。
Web 登录页 3082（vite→ZL_DEV_API_TARGET 3081，仅观察登录面）。

- include：`127.0.0.1:3081`（含其全部 API 路由）；`localhost:3081` 别名同入。
- exclude/oob：除 loopback:3081/3082 外的一切出网（egress=loopback only 已物理收窄）。
- 考卷在册的已知伤疤面（分母候选，**非任务书内容**——任务书不得带 GT 痕迹，battle.py:591-595 红线）：环境探活/导入/项目名/runner 注册与令牌/工件下载面。

## 三、红线（4条，入战书逐条遵守）

1. **无损操作优先**：读/探在先（GET/枚举/差分），写操作（建项目/触发 pipeline 等）最小化并可回收。
2. **不可逆动作挂审批**：删除类、破坏性请求、任何无法撤销的动作必须走审批门等人批，不得先斩。
3. **限速礼貌扫描**：并发受限+请求间隔（靶场在本机，纪律照走——礼貌扫描是纪律件不是带宽件）。
4. **密值脱敏入账**：钥匙/密码/token 真值永不入账本（{{vault:cred-N}} 形）；通道面发现的会话令牌按「通道面≠靶面」教训（b40 尸检：拿通道对了、报它=FP）只记事实不报漏洞。

## 四、预算帽（建议值，点火时定数）

| 帽 | 建议值 | 锚 |
|---|---|---|
| 战役 token 帽 | **500000** | 金样 G-r18 整场实耗 33.5万×1.5（RUNBOOK:115-117「首仗贴实定 50 万」）；goals.tsv budget 形 `500000;20000;4`（token;请求;小时） |
| USD 帽 | **点火时用户定数**：机械折算=所用道单价×50万token×1.5；设 `TANYIN_BATTLE_BUDGET_CAP_USD` 双保险（多仗并发时注册表按它仲裁拒新仗，battle_registry.admit budget-cap 分支） | first-battle-checklist:11「TBD点火时定」 |
| 单战士 token 帽 | 不用战士默认 100000（RUNBOOK:114「太小，别直接用」）——首仗统一吃战役帽 | RUNBOOK 第四步 |
| 并发 | 战士 3 并发（点火序列默认 N=3，first-battle-checklist:17） | 同左 |
| 时间窗 | **240min**（4h 战钟；预算第三段同值） | first-battle-checklist:28 |
| 字典/口径 | dict v3.10+；考卷=ZhuLong 代卷（见 gt-exam-readiness.md，**须点火前就位否则 settle 用错卷**） | first-battle-checklist:28-29 |

帽子花完战士会停——这不是事故是设计（宁可半途停，不可失控烧钱）。

## 五、授权八问预填（add-goal/add-scope 素材）

1) 目标：ZhuLong 靶场 127.0.0.1:3081（本地自授权）；2) 授权文件：用户点火时提供的授权书原件（消毒名落盘+sha256 真校验，webui _post_battle_new 同链）；3) 授权窗口：点火当日（valid_from/until 由用户定）；4) 范围：include=127.0.0.1:3081；egress=loopback only；5) 预算：500000;20000;4 + USD 帽环境变量；6) 凭据：无预发——靶场 /api/setup 首管+登录自建（RUNBOOK 第一步），注册/发放面自行获取；7) 强度：打穿别打塌——禁 DoS/禁破坏性负载，礼貌速率；8) 会话目录：`~/.tanyin/battles/battle-<N>/<gen>`（battle.py paths()）。

## 六、收仗判分口径（首考纪律）

- 判卷三件：`findings.tsv`（可复现步骤才是 finding，观察只是 fact）/`E-index.tsv`（每洞可重放）/`timeline.tsv`（全程审计链）——对照参考 DEMO-1 形状（111发现/709时间线）。
- **首考=立基线不比旧**（新系统新口径）；全链证据可复算；禁无证据调分；僵尸口径标注（b40 教训：30/31 FP 是僵尸行重数）。
- GT 判分用 ZhuLong 代卷（gt-exam-readiness.md 产卷步骤）；若代卷未就位即点火，settle 会回落 docker GT=错卷——须如实记「无 ZhuLong 卷，分数无效」。

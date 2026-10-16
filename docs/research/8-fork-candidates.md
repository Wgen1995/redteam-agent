# 二开候选事实核查 —— 「在现有系统上二次开发」的现实底子（研究第 8 档）

- **日期**: 2026-10-16 · **性质**: 决策输入（逐候选事实核查 + 二开可行性判决）
- **纪律**: 只读核查 + 仅写本档 + 零 git 写操作。判据 = 源码可得性 / 许可 / 改造成本量级 / 与探隐核心资产（账本哈希链 · guard 执法 · 度量考卷）的兼容性。
- **路径约定**（下文全用这两个前缀）:
  - `探隐仓/` = `/Users/wgen/redteam-agent`（探隐 TanYin 本体）
  - `平台仓/` = `/Users/wgen/Documents/AI For Security & Compliance/ai-assisted-security-verification-platform`（烛龙 ZhuLong 平台 monorepo；ARTEX/ 与 CyberStrikeAI/ 两个候选就地检出于该仓内）
- **素材链**: liveui 研究第 0-7 档（`探隐仓/docs/research/liveui/`）+ 使用手册（`探隐仓/docs/research/manuals/usage-guide-*.md`）+ **本次实地复核**（目录清单 / LICENSE / go.mod / package.json / 规模实测，全部 2026-10-16 重测）。

---

## 〇 结论速览（给决策者的一页）

| 候选 | 源码在手? | 许可 | 技术栈 | 改造成本量级 | 核心资产兼容 | **二开判决** |
|---|---|---|---|---|---|---|
| **ARTEX** | ✅ 全源码（git 检出） | ⚠️ **AGPL-3.0**（网络服务传染） | Go 1.26 + PostgreSQL + Next.js 16/React 19/Tailwind v4 | **高**（13.1 万行 Go + 187 个前端文件 + norma 内核死锁） | **低**（可变 Postgres 库、无哈希链/重放门/考卷） | ❌ **不二开**，维持「仅参照」（85% 置信） |
| **CyberStrikeAI** | ✅ 全源码（tarball 解出，无 .git） | ✅ **Apache-2.0**（逐文件可搬） | Go 1.25 + eino + SQLite + **零框架单体前端** | **中高**（约 16 万行 Go + 7032 行单模板 + 4.7 万行 CSS） | **低-中**（有审计/工具治理，无链/无门/无考卷） | ❌ 不整仓二开；✅ **唯一合法「抄页」素材库**（85% 置信） |
| **multica** | ❌ **本地无源码**（仅 docker 镜像部署件） | ❓ **未实证**（本地无 LICENSE，研究档未记录，本次外网核验不可用） | Go + Next.js + PostgreSQL17/pgvector（闭源镜像交付） | **高**（全 PM 平台 + 96 个 env 变量） | **低**（六无：无范围执法/无真值底座/无验证纪律/无覆盖模型/无凭据库/零安全工具） | ❌ **不二开**，维持薄桥互通（组织层互补分工） |
| **ZhuLong（烛龙）** | ✅ 用户自有仓 | 自有（无 LICENSE 文件 = 私有，无碍） | pnpm monorepo: Vue3.5+Pinia / Hono+better-sqlite3 / zod 契约单源 | **低**（引擎闸已建好，BO14 已把探隐注册为第四引擎） | **高**（数据面已通：TSV 权威列 → NDM mapper 已落地） | ✅ **唯一现实「二开形」**——但形态不是 fork，而是**引擎闸接入**（已完成大半） |
| zhulong-main（附注） | ✅ 检出 | 上游公开仓（reganxt/zhulong） | 纯方法论知识库（提示词/规则/漏洞类），**无服务端软件** | — | — | 无二开面；是知识捐赠对象，非代码候选 |

**一句话**：「二开」的现实底子只有一个——**烛龙引擎闸（端点 82）**，且它不是候选而是**已落成的既成事实**（BO14 tanyin@1 已合入平台仓）；其余三家全部维持既有「仅参照」判决，其中 CyberStrikeAI 因 Apache-2.0 + 零框架同律，升级为唯一可**合法抄页**的素材库。UI 底盘二开（借成熟管理台做壳）与零依赖律的冲突是结构性的（§六），放弃零依赖的实际代价见 §六.2 代价账。

---

## 一 ARTEX —— 资产最厚，三重负资产一票否决

### 1.1 事实卡（本次实地复核）

| 问 | 事实 | 证据路径 |
|---|---|---|
| 源码可得? | ✅ 完整 git 检出，末次提交 a9d11cb（2026-10-10「Merge PR #4: build: restore norma v0.4.3 from Go module proxy」），上游 `github.com/mhtsec/ARTEX`（经 gh-proxy 镜像克隆） | `平台仓/ARTEX/.git`（只读查询）；`平台仓/ARTEX/go.mod:1` |
| 二进制? | 官方交付 = Docker 镜像 `mianhuatang11/artex`（**自维护镜像**——注释明言原 `autumn27/artex` 已从 Docker Hub 删除）；源码构建走 `build.sh`（多目标交叉编译 + UPX + npm ci + NEXT_EXPORT 静态导出） | `平台仓/ARTEX/docker-compose.yml`（artex 服务 build 段注释）；`平台仓/ARTEX/build.sh:1-25` |
| 技术栈 | 后端 Go `net/http` 单体（103 个 server 文件，`go:embed` 内嵌前端）；数据库 **PostgreSQL**（pgx，只认 `ARTEX_PG_DSN`）；前端 **Next.js 16.2.9 + React 19.2.7 + Tailwind v4 + shadcn/ui**，首屏 26 chunk ≈ 2.0MB JS；agent 内核 norma SDK（agentcore/tool/permission/harness/memory/transcript） | `探隐仓/docs/research/liveui/2-artex.md:15-19`（源码级报告）；`平台仓/ARTEX/go.mod`（go 1.26.3 + pgx/jwt/uuid）；`平台仓/ARTEX/web/package.json`（version 2.2.0）；`探隐仓/docs/research/manuals/usage-guide-artex.md §0.1` |
| 规模 | **535 个 Go 文件 / 130,654 行**；web/src 187 个 ts/tsx 文件（本次 find+wc 实测） | `平台仓/ARTEX/` 实测 |
| **许可** | **AGPL-3.0**：README 明文「若你修改本项目并通过网络向用户提供，也必须向这些用户公开对应的完整源码」；前端目录另有 MIT LICENSE（web/LICENSE）但整体仓以 AGPL 为准 | `平台仓/ARTEX/LICENSE:1`（GNU AFFERO GPL V3）；`平台仓/ARTEX/README.md:484-486`；`平台仓/ARTEX/web/LICENSE:1` |
| 隐藏风险 | ① **norma 上游闭源死锁**：go.mod 注释「Upstream github.com/Autumn-27/norma went closed-source…v0.4.3 was restored from the Go module proxy into ./norma」——agent 内核冻结在已死上游的代理快照，fork 后无人维护内核；② 前端底子是 **Saasable Datum 类商业模板**改皮（7 个 cookie 偏好 + 3 preset 主题系统 = 维护负资产）；③ 部署强绑 Postgres 容器 | `平台仓/ARTEX/go.mod:3-6`；`探隐仓/docs/research/liveui/2-artex.md:17`（模板底子）+ `:198`（模板负资产判词） |
| 本地构建摩擦实证 | 用户为跑它下载 go1.25.14 darwin-arm64 tarball（58MB）+ brew-go.log + gomod-warm/ 预热目录，均留在平台仓根目录 | `平台仓/go1.25.14.darwin-arm64.tar.gz`、`平台仓/brew-go.log`、`平台仓/gomod-warm/` |

### 1.2 与探隐核心资产的兼容性

| 核心资产 | 探隐现状 | ARTEX 对应物 | 兼容判定 |
|---|---|---|---|
| 账本哈希链 | 13 表 TSV + timeline.tsv 链式哈希第一事实源、全部表可重建、写前拒收（`探隐仓/contracts/01-ledger-schema.md §1`：单写者/ID 铸造/journal 重建） | 双图架构落 **可变 PostgreSQL**，无哈希链、无防篡改、无重建律 | ❌ 结构性不合：把账本塞进 Postgres = 放弃第一事实源地位 |
| guard 执法 | 四层恒在：Tier0 账本写前拒收 / Tier1 tanyin-guard 包装一切对外命令 / Tier2 宿主 hook / Tier3 egress 代理 deny-by-default + canary（`探隐仓/contracts/11-enforcement.md §1`） | 拦截 = 规则 + LLM judge 语义判定 + 审批卡（`探隐仓/docs/research/liveui/2-artex.md §1.6-D`）——是**审判链**不是**执法链**：无 deny-by-default 出网管控、无 scope CIDR 机械判定 | ❌ 模型不同：judge 可被说服，Tier0-3 是机械闸；二者不可互换 |
| 度量考卷 | 56 分母召回考卷（`探隐仓/tests/range/ground-truth.json` + `探隐仓/scripts/battle.py:23-24,299`，任务书泄漏 GT 即红线 ：235）+ evals 套件 + 金样回归 + webui 统计臂（McNemar，`探隐仓/docs/research/liveui/walk-tanyin.md:33`） | Token 记账/成本面板成熟，但**无 GT 对照、无重放验证门、无统计度量** | ❌ 无对应物 |

### 1.3 判决

> **ARTEX：不二开。** 三重一票否决叠加：① AGPL-3.0 网络服务传染（商用/私有改造即触发开源义务）；② 底座三重换血（Go+Postgres+Next.js vs 探隐 Python stdlib+TSV+手写前端）；③ norma 内核死锁（fork 即孤儿）。既有研究判决「仅参照·置信 85%」(`探隐仓/docs/research/liveui/2-artex.md §四`) 本次**维持并加固**——其交互语义层（状态语义表/SSE 可靠性模型/审批审计形态）已被认定为「抄设计不抄代码」的现成答案（同档 :200），v0.9d 改版正在消费这些模式（`探隐仓/cli/webui/static/status.js` 已建 = 其 #1 建议「状态语义单源」的落地）。
> **翻案条件（照抄原档 :202-205）**：探隐放宽语言律允许构建链、且控制面决定独立成服务——两条件同时成立才谈二开。

---

## 二 CyberStrikeAI —— 法律最干净、语言律同族，但架构仍是一票否决

### 2.1 事实卡

| 问 | 事实 | 证据路径 |
|---|---|---|
| 源码可得? | ✅ 完整可读（259MB / 7457 文件），但**无 .git**（tarball 下载解出：`平台仓/CyberStrikeAI.tar.gz` 16MB + download.log + clone2.log 记录 `github.com/AIPentest/CyberStrikeAI.git`） | `探隐仓/docs/research/liveui/3-cyberstrike.md:4-5`；`平台仓/clone2.log`；本次实测（`ls -d CyberStrikeAI/.git` → 无） |
| 上游 | github.com/AIPentest/CyberStrikeAI（原 Ed1s0nZ/CyberStrikeAI），研究档实测 7812★ / 1589 fork / **当日仍在推送**（2026-10-15 时点记录） | `探隐仓/docs/research/liveui/3-cyberstrike.md:4` |
| 二进制? | 本地已构建 102MB 单体二进制 `cyberstrike-ai`（2026-10-14，用户装 Go 后自建）；另有 run.sh 一键部署 + 控制台「一键更新」自更新通道 | `平台仓/CyberStrikeAI/cyberstrike-ai`（102MB，实测）；`平台仓/CyberStrikeAI/README_CN.md:191,271-284` |
| 技术栈 | Go 1.25 + cloudwego/eino（LLM 编排）+ gin + **SQLite** 持久化；前端**零框架单体**：`web/templates/index.html` 29 页全静态写死（实测 7032 行）、`web/static/css/style.css` 实测 47,221 行、JS 模块 IIFE 封装 + 41 个前端单测、7 个 vendor 库运行时 script 引入（无打包）；Python 侧 requirements.txt（requests/httpx/bloodhound/impacket/mcp）只是工具外挂非核心 | `平台仓/CyberStrikeAI/go.mod`；`README_CN.md:130`；实测 wc；`探隐仓/docs/research/liveui/3-cyberstrike.md §1.1` |
| 规模 | 约 **159,683 行 Go**（本次实测，排除 venv） | `平台仓/CyberStrikeAI/` 实测 |
| **许可** | **Apache-2.0**（宽容式：可逐文件搬运，保留 attribution 即可） | `平台仓/CyberStrikeAI/LICENSE:1-3` |

### 2.2 与探隐核心资产的兼容性

- 账本哈希链 ❌：SQLite 审计日志 + 「行动证据留存」是运维取证面，非链式防篡改真值底座（`README_CN.md:130-131`）。
- guard 执法 半❌：有 tool-guard / rbac-guards（400+ 全局写函数权限映射，`探隐仓/docs/research/liveui/3-cyberstrike.md §1.2-3`）——治理的是**工具调用权限**，探隐 Tier1-3 治理的是**作战行为边界**（scope CIDR/出网/canary），语义不同层。
- 度量考卷 ❌：无 GT 对照评分、无重放验证门、无统计臂。

### 2.3 判决

> **CyberStrikeAI：不整仓二开（「仅参照」85% 置信维持，`探隐仓/docs/research/liveui/3-cyberstrike.md §四`）；但升级定位为「唯一合法抄页素材库」。** 原档判词准确：「许可证不是障碍，架构才是」——Apache-2.0 允许逐文件搬运，但 Go+gin 单二进制 + 673KB 单模板的一体化单体意味着「整页二开 = 在探隐里养一个 Go 副内核，违反底座自持律」（:203-207）。
> **增量判决（本次新增）**：它是四候选中唯一**法律（Apache-2.0）+ 语言律（零框架零构建）双兼容**的系统。探隐 v0.9d 起的 UI 改版若需要「成页的交互实现」参考（弹窗/通知中心/主题防闪烁/i18n 属性驱动/滚动管理——`3-cyberstrike.md §1.2` 复用组件清单），可按 Apache-2.0 逐文件抄改 + 头部 attribution，**不引入构建链、不引入 Go**。它同时是「零框架律跑到 7812★ 规模后的技术债标本」：4.7 万行单 CSS 靠注释分区维持（:24）——证明探隐路线在大体量下成立，也警示债务主因是无纪律增长。

---

## 三 multica —— 源码不在手、许可未实证，且它本就不是安全层

### 3.1 事实卡

| 问 | 事实 | 证据路径 |
|---|---|---|
| 源码可得? | ❌ **本地无源码**。本地只有部署件：`multica-selfhost/docker-compose.selfhost.yml`（pgvector/pgvector:pg17 + ghcr.io/multica-ai/multica-backend + multica-web 三个**成品镜像**，注释明言「部署仓不含 app 源码」）；源码视角靠 GitHub 公开仓 + RSC payload 反解 | `/Users/wgen/Documents/AI For Security & Compliance/multica项目实践/multica-selfhost/`（本次实测仅 1 个 compose 文件）；`探隐仓/docs/research/liveui/1-multica.md:22-32` |
| 开源? | 上游公开仓 github.com/multica-ai/multica（Go + TypeScript，官方自称 51k+ stars——**官方口径，未独立核验**）。**许可类型未实证**：部署仓无 LICENSE（本次 find 实测为空）、研究档 0-7 全系未记录许可、本次外网核验不可用（web_search 余额 402 / web_fetch 网络失败，2026-10-16）——**若为 AGPL/BSL 系，本节判决无需再议直接成立** | `探隐仓/docs/research/liveui/1-multica.md:20`；本次实测 + 工具失败记录 |
| 技术栈 | Go 后端(:8080) + Next.js 前端(:3000) + PostgreSQL17/pgvector + daemon 运行时（provider CLI = claude/opencode）；.env **96 个变量**（JWT/S3/Resend/OAuth/GitHub App/Lark×5 渠道/插件面/遥测） | `探隐仓/docs/research/liveui/1-multica.md:24-33` |
| 与探隐的既有关系 | 用户已在 multica 上跑真实安全红队编排（squad「安全红队」live 实证；`/Users/wgen/pentest-redteam-multica/` 有 agents/squad/skills 实践工作区）——「平台出形，实践出魂」的活样本 | `探隐仓/docs/research/liveui/1-multica.md:4,20`；`/Users/wgen/pentest-redteam-multica/`（本次实测） |

### 3.2 判决

> **multica：不二开，维持薄桥互通。** 依据既有专档判决（`探隐仓/docs/research/liveui/1b-multica-security-capability.md §三`，置信 0.88）：它是「组织编排层」而非「安全能力层」——六无（无范围执法/无真值底座/无验证纪律/无覆盖模型/无凭据保险库/零安全工具，§二 1-6 条）。对探隐的正确定位是**多项目组织层互补 + 薄桥互通**（用户实践已实证此形态有效），「不因此升格为二开对象」。本次追加两条加固：① 源码根本不在手（fork 前提不成立）；② 许可未实证（AGPL/BSL 风险敞口未关闭）。
> **翻案条件（照抄原档）**：multica 经其插件表面原生出货 guard/egress/验证类能力 → 届时重评。

---

## 四 ZhuLong（烛龙）—— 不是候选，是已落成的接入事实

### 4.1 事实卡

| 问 | 事实 | 证据路径 |
|---|---|---|
| 归属 | **用户自有仓**（远端 `Wgen1995/zhulong-ai-security-verification`，package.json `name: zhulong-platform, private: true`，**无 LICENSE 文件** = 私有自用，无许可障碍） | 本次实测（`平台仓/package.json`；`ls LICENSE*` → 无） |
| 技术栈 | pnpm monorepo 三包：`apps/web` Vue 3.5.41 + Pinia 4 + vue-router + Tailwind v4 + lucide + @antv/g6；`apps/server` Hono 4.8 + **better-sqlite3** 12（原生模块）+ libsodium + pino + zod 4；`packages/contracts` zod 单源契约（54 端点/枚举/SSE 事件）。前提 Node 22+ / pnpm 11+ | 本次实测（`平台仓/apps/server/package.json`、`apps/web/package.json`、根 README「常用命令」） |
| 规模 | server 50,551 行 ts + web 13,634 行 vue + contracts 6,708 行 ts（本次实测）；前端 14 视图 + 34 领域组件 + 33KB 词账 + 文案守门测试 | 实测；`探隐仓/docs/research/liveui/4-zhulong.md §1.1` |
| **引擎闸（互通点）** | **端点 82 外部引擎注册**：`engine-register.ts` 幂等注册（UNIQUE 撞=跳过）/ 版本前进 / origin='external' 服务端盖章 / audit 留痕；配端点 44 启停、83 卸载。**BO14 已把探隐注册为第四业务引擎**：`tanyin@1` manifest（blackbox/environment、开眼·吐焰两模式、granularity 含 ledger、egressDomains=[] 零外联声明、restartPolicy=fresh）+ `mapper-tanyin.ts`（findings.tsv/E-index.tsv 权威列 → NDM 纯翻译，TSV 列权威双轨律照抄探隐 contracts/06 §4.11，重放三态 VERIFIED→hasDynamicPoc） | `平台仓/apps/server/src/services/engine-register.ts:1-40`；`平台仓/packages/contracts/src/fixtures/engines.ts:218-248`；`平台仓/apps/server/src/services/mapper-tanyin.ts:1-16`；调研稿 `平台仓/docs/superpowers/2026-10-09-tanyin-integration-research.md`（裁定①b 案：烛龙头 opencode + 任务书引探隐技能，零新 adapter） |
| 互通的设计期预留 | 探隐侧 contracts/08:45 原文「烛龙接入只换 runner」——**探隐设计期已预留宿主平台接入缝**，与烛龙引擎闸互为对偶 | `平台仓/docs/superpowers/2026-10-09-tanyin-integration-research.md:36`（引用探隐仓 contracts/08-manifest.md:45） |
| zhulong-main（旁支） | 同目录的 `zhulong-main/` 是 **reganxt/zhulong 方法论框架库**（framework/orchestration/prompts/rules/vulnerability-classes 等），纯知识资产无服务端软件；烛龙平台的知识聚合（19 漏洞类/227 规则）正文即来自它 | `探隐仓/docs/research/liveui/4-zhulong.md:9`；本次实测目录 |

### 4.2 与探隐核心资产的兼容性

| 核心资产 | 兼容面 | 证据 |
|---|---|---|
| 账本哈希链 | **数据面已通**：mapper 以 TSV 列为权威摄取五族产物（卡缺席=TSV 兜底、畸形行记 failures 不中断）；账本本体仍在探隐侧（goalDir 仓外持久 + 恢复协议续跑）——烛龙只做投影消费，不碰链 | `mapper-tanyin.ts:5-10`；调研稿 §2.2 R2 |
| guard 执法 | **分工已裁定**：平台 egressDomains=[]（宿主径零外联声明）+ 真出网管控**委托探隐四层**（guard Tier1 + egress Tier3 + canary）；P0 八问授权门 = 烛龙建单参数面（authSha256 必填·账本空=REJECT） | `engines.ts:231`（egressDomains=[]）；调研稿 §〇 ④ |
| 度量考卷 | 独立保留在探隐侧（56 分母召回/evals/金样不进烛龙）；烛龙侧只收 findings 与战报回采，验收=收齐门禁（required 产物 pattern 齐）fail-closed | 调研稿 §2.1 表（完成判据行） |

### 4.3 判决

> **ZhuLong：✅ 唯一现实的「二开形」——但正确形态不是 fork 它的代码，而是它作为宿主管理台、探隐作为引擎经端点 82 闸接入。** 这条路**已经走通大半**（BO14 T1：manifest + mapper 已合入平台仓），零新 adapter、零探隐侧改动（探隐仓本轮只读零改，调研稿头注明示）。既有研究判决「仅参照·置信 90%」(`4-zhulong.md §四`) 的**翻案条件①原文明写**：「出现『探隐需要多用户 RBAC 管理台 + 持久化任务队列』的完整需求，且愿意把 ZhuLong 整站当外壳、探隐内核以引擎插件协议接入 → 改判二开」(`4-zhulong.md:147`)——引擎插件协议接入这一半已成事实；若多用户管理台需求坐实，翻案即完成。
> **代价提示**：走此径意味着接受 Node 22+/pnpm/better-sqlite3 工具链——但工具链成本由烛龙仓自担，探隐仓的零依赖律**不受任何影响**（这正是它优于 UI 底盘二开的关键：底子换了，探隐本体不动）。

---

## 五 核心资产兼容性总对照

| 核心资产（探隐侧证据） | ARTEX | CyberStrikeAI | multica | ZhuLong 接入径 |
|---|---|---|---|---|
| **账本哈希链**（`探隐仓/contracts/01-ledger-schema.md §1`：timeline 链式哈希/单写者/13 表可重建/写前拒收） | ❌ 可变 Postgres 双图 | ❌ SQLite 运维日志 | ❌ 可变 Postgres | ✅ TSV 权威 mapper 只读消费，链不搬家 |
| **guard 执法**（`探隐仓/contracts/11-enforcement.md §1`：Tier0-3 四层恒在） | ❌ LLM judge 审判链≠机械执法链 | 半❌ 工具权限治理≠作战边界执法 | ❌ 无范围执法 | ✅ 分工裁定：平台零外联声明+执法全委托探隐 |
| **度量考卷**（`探隐仓/tests/range/ground-truth.json` + `scripts/battle.py:23-24,235,299` + `cli/tanyin-evals` + webui 统计臂 walk-tanyin.md:33） | ❌ 无 GT/无重放门 | ❌ 无 GT/无重放门 | ❌ 无验证纪律 | ✅ 考卷留在探隐侧，平台只收产物 |

---

## 六 专问：UI 底盘二开（借成熟开源管理台做壳，引擎仍探隐）

### 6.1 与零依赖律的冲突点（零依赖律 = clone 即用，Python stdlib + 手写前端：`探隐仓/README.md:18`「git + python3（3.10+，零 pip 依赖）」、:23 安装约 2 分钟、:30 Windows `py -3` 等价；现状 webui = `cli/webui/` 764 行 Python（stdlib ThreadingHTTPServer/projections/sse）+ 7 张手写 HTML（activity/index/coverage/graph/session/evidence/metrics，共 2895 行）+ status.js——v0.9d 改版在零依赖律内推进中）

| # | 冲突点 | 证据 |
|---|---|---|
| 1 | **构建链入侵**：成熟管理台壳全带 Node 构建（ARTEX=Next.js+npm ci+NEXT_EXPORT；烛龙=Vite+Tailwind v4+pnpm -r build）。「clone 即用」从 git+python3 变 git+python3+node+pnpm+build 五步 | `平台仓/ARTEX/build.sh:9-21`；`平台仓/package.json` scripts |
| 2 | **部署单元增殖**：better-sqlite3 原生编译（node-gyp）、Postgres 容器（ARTEX/multica）、102MB 单二进制+40KB config.yaml（CSAI）——从「一个 python3」到多服务编排 | `平台仓/apps/server/package.json`；`平台仓/ARTEX/docker-compose.yml`；`平台仓/CyberStrikeAI/config.example.yaml`（40KB） |
| 3 | **投影律冲突**：管理台=写面（表单/按钮/RBAC/审批）；探隐 UI 定法只读投影、写动作走 harness 遥控第四层。壳的 CRUD 价值在投影律下归零，留下的是白背的攻击面 | `探隐仓/docs/research/liveui/walk-tanyin.md:6,20`（零写端点实测）；`2-artex.md:196` |
| 4 | **双真相源**：壳自带 DB schema 会与 13 TSV+哈希链并立；要么造 ETL 同步层（新维护面+一致性风险），要么壳空挂投影 | `探隐仓/contracts/01-ledger-schema.md §1`（journal 重建律） |
| 5 | **供应链面失控**：探隐 tools.lock 八键验签的封闭供应链（`探隐仓/tools.lock`）vs npm 依赖森林（ARTEX web 数十 direct deps + 锁文件；每次升级=重新审计） | `探隐仓/tools.lock:1-8`；`平台仓/ARTEX/web/package.json` |
| 6 | **升级跑步机**：Next 16/React 19/Tailwind v4/Vue 3.5/Pinia 4 主版本年更即 Breaking；vanilla JS 无此漂移 | 各仓 package.json version 群（实测） |
| 7 | **攻击面扩大**（红队工具的特有代价）：壳带来认证/会话/上传/RBAC 面——live 实证 ARTEX 红队意图 #73 正把 :3000/:8787/:8443/:3080/:8900 各控制台列为弱口令定向目标；探隐现状=127.0.0.1 绑定+零写端点，「被撞库也无状态可改」 | `2-artex.md:169`；`walk-tanyin.md:68` |
| 8 | **三平台承诺**：README 明言 Windows `py -3` 全等价（:30,119）；原生模块/构建链在 Windows 是历史痛点 | `探隐仓/README.md:30,119`；CI 矩阵 ubuntu+windows × py3.11/3.12（`探隐仓/.github/workflows/ci.yml:13-15`） |

### 6.2 放弃零依赖的实际代价账（部署/维护）

- **部署**：安装验证从「一条命令约 2 分钟」（`README.md §二`）变为：Node 22+ / pnpm 11 安装 → registry 拉取（分钟级，需外网）→ 构建 → 可能再加 DB 服务；CI 从 python 双平台四格扩 node 矩阵；**离线/气隙部署能力丧失**——对需要在目标内网环境落脚的红队工具是致命项。
- **维护**：① 依赖安全公告常态化跟进；② 框架大版本迁移（人周级/次）；③ 双真相源对账代码（若有 DB）；④ fork 即孤儿——上游日更（ARTEX/CSAI 当日仍在推送），不跟=安全债，跟=合并冲突常态化。
- **规模对照**（实测）：探隐 webui 全部 764 行 py + 2895 行 html + status.js ≈ **0.4 万行**；烛龙整套平台 50,551+13,634+6,708 ≈ **7.1 万行**；CSAI 仅前端 CSS 一项 47,221 行。底盘二开等于把维护面放大一个数量级换来探隐并不需要（投影律下）的写面能力。
- **收益侧诚实账**：换来的是成熟组件/认证/RBAC/深链/SSE 可靠性模型——但四份研究的一致结论：这些是**与框架无关的模式资产**，vanilla JS 可 1:1 等价重写（`2-artex.md:200`；`4-zhulong.md:144`），且探隐 v0.9d 落点清单全部标注「零依赖律+投影律内完成」（`walk-tanyin.md §五`头注）。**CSAI 标本同时警示：零框架不自动免债**——4.7 万行单 CSS 靠注释分区（`3-cyberstrike.md §1.1`），探隐的真正护身符是投影律+页面预算纪律，不是「手写」本身。

### 6.3 判决

> **UI 底盘二开：否。** 冲突是结构性的（8 条中 #3 投影律、#4 单一事实源、#7 攻击面三条与「红队账本工具」的身份冲突，无法用工程手段消解）。若未来确需 Web 管理台形态，正确路径有二且都已存在：① **ZhuLong 宿主径**（§四，管理台能力由烛龙承担，探隐零依赖律无损）；② **CSAI 抄页径**（§二，Apache-2.0 逐文件抄改零框架页面，不引入构建链）。两条路径都不需要放弃零依赖律。

---

## 七 判决汇总（按推荐顺序）

1. **ZhuLong 引擎闸接入（✅ 既成事实，继续走深）**——唯一不要求探隐本体让步的二开形；BO14 已落地 tanyin@1 + mapper，剩余为调研稿 §七 开放点（OP-1..14）与真跑验收（靶场一战建单→回采→入库）。翻案条件①的引擎协议半已成就。
2. **CyberStrikeAI 抄页素材库（✅ 增量定位）**——Apache-2.0 + 零框架双兼容；UI 改版需要成页参考时合法搬运 + attribution，仅此而已。
3. **ARTEX / multica（❌ 维持仅参照/薄桥）**——ARTEX 三重否决（AGPL 传染/底座换血/norma 死锁）；multica 源码不在手 + 许可未实证 + 组织层非安全层。二者的价值已由研究档充分开发（可偷清单见 `2-artex.md §五`、`1b §四`），无需再投入。
4. **UI 底盘二开（❌）**——见 §六.3。

---

## 附 本次核查方法与限制

- **方法**：以 liveui 研究 0-7 档为底本 → 对四个候选目录逐一实地复核（LICENSE/go.mod/package.json/compose/规模 wc/关键源文件头）→ 与研究档记载交叉比对；分歧处以本次实测为准并标注（如 CSAI index.html 实测 7032 行 vs 报告 ~5200 行——上游日更所致）。
- **git 使用披露**：仅对 ARTEX 与平台仓执行过**只读** git 查询（remote/log，用于确认上游与归属），零写操作、零 checkout/commit。
- **外网限制**：web_search（余额 402）与 web_fetch（网络失败）均不可用——multica 许可类型、上游 star 数活跃度（2026-10-15 之后的动态）**未联网复核**，以研究档实测记录为准；multica 若进入任何实质接触，**第一步必须先核验其 LICENSE**。
- **本档未同步 liveui/INDEX.md**（任务纪律=只写本档一文件）；建议 orchestrator 收档时补一行：「8-fork-candidates.md · 二开候选事实核查 ✅」。

# 探隐观察面（tanyin-web）活体漫游记录 —— v0.9d 改版前基线（before）

- **目标**： http://127.0.0.1:8900 （探隐自己，无鉴权，服务 banner `tanyin-web/0.9c`）
- **数据底座**： ledger `/Users/wgen/.tanyin/battles/battle-42/G-r43`（timeline 436 行）
- **漫游时间**： 2026-10-15 15:38–15:41 CST · Chrome headless 1440×900 · Playwright
- **纪律**： 只导航不操作。全站为只读投影——**页面上本来就不存在任何写操作按钮**（新建/发送/审批类一概没有），铁律天然满足。唯一交互是导航链接、hover tooltip、客户端展开/聚焦。
- **分析方法**： 截图（存 `shots/`，供人工复核）+ inner_text / DOM 计数 / getComputedStyle（色彩·字体·动效）+ 静态源码只读核对（`cli/webui/`）。零 git。
- **基准**： `2-artex.md`、`4-zhulong.md`（本目录，ARTEX/ZhuLong 活体分析报告）。

---

## 一、系统形态速览

| 项 | 事实 |
| --- | --- |
| 架构 | 纯 stdlib `ThreadingHTTPServer` + 5 张手写静态 HTML（共 1024 行）+ vanilla JS；零框架零构建零依赖 |
| 页面路由 | `/`（v0.9a 仪表盘）· `/coverage` `/graph` `/evidence`（v0.9b 三页）· `/metrics`（v0.9c 度量页） |
| 数据路由 | `/api/state.json` · `/api/matrix|graph|evidence|metrics.json`（projections/metrics 单源装配）· `/api/stream`（SSE 追尾） |
| 实时模型 | 仪表盘 = SSE（`EventSource`，onopen/onerror 徽标）+ 5s state 轮询；coverage/graph/evidence = 10s 全量重拉重渲染；metrics = 一次性加载 |
| 安全姿态 | 只读投影（零写入账本）；文本一律 `textContent` 落节点（源码注释明写防注入）；无鉴权，仅 127.0.0.1 绑定 |
| 视觉单源 | `:root` 八变量：`--bg #0f1216 · --card #171c23 · --ink #e8edf2 · --dim #8b98a5 · --ok #3fbf6f · --bad #e05252 · --idle #4a545e · --accent #4fa3d1`；字体 PingFang SC |

---

## 二、视图清单

| 路由 | 截图 | 页面呈现什么 | 可交互元素 | 视觉手法（色彩/层级/徽标/动效） |
| --- | --- | --- | --- | --- |
| `/` 仪表盘 | [tanyin-01-dashboard.png](shots/tanyin-01-dashboard.png) | 战局头（G-r43-0001 靶场描述 + timeline 行数）；SSE 连接徽标；**九门灯**（P0–P6 含 P5.5，5 PASS / 1 FAIL / 2 PENDING）；预算余量三卡（token 1,568,000/2,000,000 · requests 49,275/50,000 · hours 38/40）；活动流（SSE 追尾，最近 checkpoint/gate/replay/add-finding 事件） | 导航链接 ×4（覆盖热图/十边图/证据卡/度量）；无按钮无输入 | 暗底卡片分层；门灯=ok 绿/bad 红/idle 灰三色文字徽标；活动流=时间戳+来源+事件+8 位哈希尾的等宽单色文本流；SSE 徽标绿点态；**全站零动效**（computed `animation-name` 全为 none） |
| `/coverage` 覆盖热图 | [tanyin-02-coverage.png](shots/tanyin-02-coverage.png) | 消格统计卡（格总数 108 · 已置 108 · 欠账 0 · 冻结 0 · **消格率 100%**）；图例；攻击面×漏洞类矩阵（9 surface × 12 wstg-* 类，格值 x/?/-/!） | 导航 ×4；矩阵格 **hover → 原生 title tooltip**（reason/intent/updated）；10s 自动刷新 | 冷格=accent 蓝系底色块（109 格同色）；空格红标；冻结格 ◆ 深蓝；表格为唯一容器（1 table）；无图例外图示 |
| `/graph` 十边血缘图 | [tanyin-03-graph.png](shots/tanyin-03-graph.png) | 图谱统计（节点 192 · 边 86）；十种边 kind 着色图例（实存 4 种：attack×7 金 / derived_from×32 / parent×46 / supersedes×1 点线；6 种 ×0）；分层泳道 G→INT→AST/CRED→F→FD→EV 全量铺开 | 导航 ×4；**SVG 节点 click → 详情面板**（客户端）；10s 刷新 | 纯 SVG（11 个 svg 块）；节点=4px 圆点（正式 #9fb3d1 / candidate 半透明灰 #7c8794）+kind:id 文本标签；attack 边金色；页面高达 2173px 纵向滚 |
| `/evidence` 证据卡 | [tanyin-04-evidence.png](shots/tanyin-04-evidence.png) | 重放三态 E-index 汇总（卡总数 44 · 已复现 41 · 未重放 3 · 人工/环境差异 0）；证据卡列表（EV id + 标题 + raw/norm 哈希指纹 + GTXSS/GTSQLI 等靶点编号） | 导航 ×4；**卡片 click 展开/收起明细**（observed_at/repro_command/artifact_path/linked_finding 等客户端展开）；10s 刷新 | 卡片=深一档 card 底色块阵列（44 张）；三态徽标=文字+色（已复现绿/未重放灰）；哈希用等宽缩写；页高 2649px |
| `/metrics` 度量页 | [tanyin-05-metrics.png](shots/tanyin-05-metrics.png) | 统计卡（对照臂 mean recall 0.554 n=8 / 处置臂 0.589 n=5 / McNemar exact p=0.125 b=4 c=0 无显著差异）；**预登记实验**表（directive-n5，判后回填考据注记）；召回曲线 SVG（三臂：对照/处置/未知）；逐战明细表（13 战 recall/命中分母/MISSING/GT 配对/verify-chain 全 PASS） | 导航 ×5（本页才有"度量"项）；逐战表 hover MISSING；一次性加载 | 统计卡=三色 tint 底（绿/蓝/黄系半透明）；曲线=SVG 三色折线+b27–b42 横轴；两表 tabular 呈现；battle-31 recall 0.000 异常点肉眼可辨 |

---

## 三、横向一致性发现（bug 级，改版顺手修）

1. **九门灯只有 8 盏**：`index.html` 硬编码 `PHASES = ["P0"…"P5.5","P6"]`，而 `phases/phases.yaml` 定义 **9 门**——**P6.0（清理门）被漏掉**。清理门的 revert 核销状态在观察面上不可见。
2. **版本号三处不一致**：仪表盘 title=v0.9b、仪表盘 footer=v0.9a、metrics footer=v0.9c、server banner=0.9c。应单源注入。
3. **导航 IA 漂移**：v0.9b 三页（coverage/graph/evidence）导航没有"度量"链接（v0.9c 后加页未回填）；仪表盘导航没有"总览"自指项。
4. **favicon 404**：每页 console 报 `Failed to load resource: 404`（/favicon.ico）。
5. **metrics 页 `--idle` CSS 变量缺失**（其余页有）——变量表未单源共享。
6. **非法时间戳直出**：活动流显示 `2026-11-08T14:89:00Z`、`14:88:00Z`（timeline.tsv 数据侧即坏，分 88/89 不存在；UI 未校验原样渲染）。
7. **预算无预警色**：requests 余量 49,275/50,000（**已用 98.55%**）与 hours 38/40 与 token 78% 同一中性样式，临近熔断无任何视觉告警。

---

## 四、痛点清单（对照 ARTEX / ZhuLong 报告标准）

> 标准出处：ARTEX=`2-artex.md` §①1.5/1.6、§②、§⑤；ZhuLong=`4-zhulong.md` §一1.5/1.6、§二、§五。分级：🔴 改版必做 · 🟡 明显差距 · 🟢 顺手修。

| # | 我们缺什么 | 现状证据 | ARTEX/ZhuLong 标准 | 分级 |
| --- | --- | --- | --- | --- |
| 1 | **状态语义无单源** | PASS/FAIL/PENDING、已复现/未重放、冷格/空格/冻结格各页各写各的配色与文案 | ARTEX #1：`status.ts` 9 域×8 tone 集中映射，「状态命名先讲清语义边界再上色」；其落点原文就写着"探隐 webui 全局…九门流程的每门状态直接映射成一个域" | 🔴 |
| 2 | **无加载/错误/空四态纪律** | evidence 拉取失败 `catch` 静默"保原画面"；无骨架屏；coverage/graph 首帧白屏期无任何占位 | ZhuLong #7：骨架三形（表格 3 行 46px/卡片网格/区块 shimmer）+ 错误红警示重试 + 空态虚线框 CTA，「错误态与空态严格分流」；报告明注"探隐多数页只有数据态" | 🔴 |
| 3 | **URL 不承载任何状态** | 无筛选/分页/Tab/深链；coverage 某格、evidence 某卡、graph 某节点无法生成可分享链接 | ZhuLong #1：URL query SSOT（前进后退/刷新还原、未知参数忽略、防回写环双保险）；落点原文"探隐所有列表页…哈希定位全进 URL" | 🔴 |
| 4 | **活动流是平铺文本** | 每行=裸 ISO 时间戳+来源+事件串+8 位哈希尾，无分组无折叠无配对 | ARTEX #6：transcript 分组渲染器（tool_use/tool_result 按 id 配对成「命令+✓/✕」单行、round 水平分隔、懒加载）；ARTEX #91：时间只显 月-日 时:分 hover 全量、数字 `tabular-nums` | 🔴 |
| 5 | **KPI 是死数字** | 消格统计 5 卡、E-index 5 卡、度量 3 卡均不可点，与下方列表零联动 | ZhuLong #4：七桶 KPI 卡阵——值=服务端桶口径、**点击=status 深链过滤**、激活卡描边+ring；落点原文"探隐首页/任务仪表：九门流程状态桶点击即深链过滤" | 🔴 |
| 6 | **SSE 可靠性模型薄** | 有断链可见徽标（✅ 已对齐"绝不静默"精神）；但无 seq 去重/快照衔接；coverage/graph 用 10s 全量重拉整表重建（无 diff、hover 态会被刷掉） | ARTEX #2：单 SSE 多路分发 + seq 去重 + snapshot 衔接；落点原文"探隐 13 本 TSV 账的行号/哈希链天然就是 seq"；ZhuLong #2：12 事件契约 + Last-Event-ID 回放 + `stream.gap` 弃锚重订 | 🔴 |
| 7 | **无行号锚/复制检索词** | 哈希尾只是展示文本，选中复制全靠手拖 | ZhuLong #9：request_id 建单锚徽标 + `grep request_id=<值>` 一键复制——UI 直通日志检索；探隐版=账本行号/链哈希直查十三账 | 🟡 |
| 8 | **十边图无 digest/聚焦** | 192 节点一次铺开 2173px，纵向硬滚；点击只有右侧详情 | ARTEX §②7：探索链路图自算布局 + **digest 超级节点** + 血缘边语义；ZhuLong #5：StageProgress 点线微图（35 行成本嵌进行内） | 🟡 |
| 9 | **预算/Token 无可视化与预警** | 三卡纯数字，98.55% 消耗无告警色、无消耗速率、无条图 | ARTEX #7：Token 记账 UI 入/缓/出三 badge+轮次+每日条图+双数据源口径切换；ARTEX §③3.4：Token 经济是显性指标，UI 把成本面直接暴露给操作者 | 🟡 |
| 10 | **零动效、零焦点注意力引导** | 全站 `animation-name` 无一命中；当前活动门/最新事件无 pulse | ZhuLong StageProgress：active 点 pulse；ARTEX LiveBadge：蓝底脉冲「实时」/三连弹跳「流式中」——live 感是观察面的核心情绪 | 🟡 |
| 11 | **表格无几何预算/窄屏退化** | coverage 12 列 `wstg-*` 黑话表头无展开；窄屏无策略 | ZhuLong 附赠：表行 46px、列宽预算注释（14 列 1440 零横滚）；ARTEX #13：matchMedia 算可见列同步 colSpan | 🟡 |
| 12 | **无障碍/键盘规格缺失** | tooltip 全用原生 title；无 aria-label 密度；图标系统=无（纯文字） | ARTEX §②26：aria-label 中文密度极高、role=status/alert、sr-only 表头（4 分） | 🟢 |
| 13 | **一致性碎屑** | 九门缺 P6.0、版本三态、导航漂移、favicon 404、--idle 缺失、非法时间戳直出（见第三节） | ZhuLong #10：Token 单源 + 词账文案键耦（UI 文案与代码解耦，dev-jargon 测试守门） | 🟢 |
| 14 | **匿名暴露面（攻击面注记）** | 无鉴权 + /api/state.json 全量作业细节；ARTEX 报告 §3.2 live 意图 **#73 正把 :8900 tanyin 列为弱口令定向测试目标**（≤5 次模式化凭据尝试） | ZhuLong §3.2 匿名信息泄露条目同类（/api/health 无鉴权吐运维态）；探隐缓解=只读投影 + 127.0.0.1 绑定 + 零写端点——**漫游确认全站无任何可变更按钮**，被撞库也无状态可改 | 🟢 |

**改版别丢的（before 基线亮点）**：零依赖手写 1024 行的克制；`textContent` 防注入纪律（源码注释明示）；SSE 断链可见徽标；轮询分层（5s state / 10s 页数据）；每页 footer 自报数据来源与"零写入账本"声明——这排比 ARTEX 的 2MB chunk 干净得多。

---

## 五、探隐 v0.9d 落点建议（按优先级）

> 全部可在**零依赖律 + 投影律**内完成（vanilla JS 等价重写，参照两报告"抄设计不抄代码"判决）。

**P0（骨架级，先立单源再谈页面）**
1. **`status.js` 状态语义单源**（ARTEX #1）：域=门/账本/作业/判据/重放三态，每态中文标签+tone+dot 色一处定义，五页徽标全从这里取。顺手修第三节一致性碎屑（版本号/P6.0/导航/favicon/时间戳校验）。
2. **四态纪律组件对**（ZhuLong #7）：五页统一 骨架/错误+重试/空态/数据态；SSE 断链徽标保留并纳入同一状态域。
3. **URL query SSOT**（ZhuLong #1）：coverage 格选、evidence 卡展开、graph 节点聚焦、metrics 臂筛选进 URL——观察面从此可分享、可回溯、可写进报告。

**P1（信息密度级）**
4. **活动流渲染器升级**（ARTEX #6+#91）：tool 行配对折叠、round 分隔、时间短格式 hover 全量、tabular-nums；每行挂账本行号锚 + 一键复制 `grep` 词（ZhuLong #9）。
5. **KPI 可点过滤**（ZhuLong #4）：九门灯→点击过滤活动流对应门事件；消格统计卡→跳热图对应行列；E-index 三态卡→过滤证据卡列表。
6. **SSE 增量模型**（ARTEX #2）：以 timeline 行号为 seq 做去重合并，替代 coverage/graph 的 10s 全量重渲染（保 hover 态不被刷掉）；断线走"账本重放"补窗。
7. **预算预警**（ARTEX #7）：>80% 琥珀、>95% 红 + 消耗速率一行（余量/时间），预算三卡加微型条图。

**P2（表达力级）**
8. **十边图 digest 超级节点 + 点击聚焦展开**（ARTEX 探索链路图手法）：默认按 kind 折叠计数，点开一层；192 节点不再纵向硬滚。
9. **active 门 pulse 微动效**（ZhuLong StageProgress/ARTEX LiveBadge）：一处 CSS keyframes，给"正在跑的门"一个呼吸点——观察面唯一的动效预算花在注意力引导上。
10. **表格几何预算**（ZhuLong 附赠）：wstg-* 表头换 中文短名+hover 全名；列宽先做预算表再写 CSS。

---

## 附：证据索引

- 截图 ×5：`shots/tanyin-01-dashboard.png` … `shots/tanyin-05-metrics.png`（full_page，2026-10-15 15:38–15:41）
- DOM/样式采集存档：`/tmp/tanyin_walk.json`（每页 inner_text/按钮清单/computed style/动画扫描/console）
- 源码只读核对：`cli/webui/server.py`（路由表）、`cli/webui/static/*.html`（1024 行全量 grep）、`phases/phases.yaml`（九门定义：P0/P1/P2/P3/P4/P5/P5.5/**P6.0**/P6）
- 基准：`2-artex.md`（ARTEX §⑤ 13 条）、`4-zhulong.md`（§五 10+3 条）

# craft-v09d 视觉工艺批报告——探隐观察面七页换皮

批次目标：治用户怒斥的「垃圾中的垃圾」。病根已量化（整页观感等宽化 / 间距杂值 / 颜色滥发 / 字号散乱 / 阴影无制），本批以尺子（静态扫描 + Playwright 计算样式度量）完成，全程 TDD。

## 一、改动清单（严守白名单）

| 文件 | 改动 |
|---|---|
| tests/test_ui_craft.py | **新建**：五条硬验收 + 阴影令牌钉，共 11 条测试（先红后绿） |
| cli/webui/static/index.html | style 块全量重写（令牌区+规则区）；另补 1 条 CSS 规则 .lf-st.n-bad（主会话非法时间戳热修所引用的着色，热修逻辑本身未动） |
| cli/webui/static/activity.html | 同上换皮 |
| cli/webui/static/session.html | 同上换皮 |
| cli/webui/static/coverage.html | 同上换皮 |
| cli/webui/static/graph.html | 同上换皮 |
| cli/webui/static/evidence.html | 同上换皮 |
| cli/webui/static/metrics.html | 同上换皮 + JS 内 SVG 轴标签 font-size 10→12（两处，五档制） |

- 未触碰：server.py、cli/ledger/**、status.js（setState 热修语义原样）、docs 既有文件。
- 新增产物：本报告 + docs/research/liveui/shots/craft-v09d/ 九张截图（均为新建文件）。
- 对主会话三条紧急通知的响应：(1) 本人从未写/删 docs 任何既有文件（全部写操作仅 tests/test_ui_craft.py 与七个 static 页 + 本报告/截图新建）；(2) status.js 未动，.state-msg 四态 CSS 齐备；(3) index 热修保留并补上其引用的 .n-bad 着色。

## 二、前后指标对比（同口径扫描）

| 指标 | 前 | 后 | 验收线 |
|---|---|---|---|
| 每页 CSS 原色值去重 | 36–38 种 | **18 种**（CSS 值区口径 35→18） | ≤18 达标 |
| 间距（margin/padding/gap 含长手） | 15 种杂值（1/2/3/5/6/10/14/18/22/28px…） | **7 档**：4/8/12/16/20/24/32（+0） | 4px 网格达标 |
| 字号 | 9 种（10/11/12/13/14/15/16/18/20） | **5 档**：12/13/15/20/24 | 五档制达标 |
| 正文字体 | 仅 PingFang SC/雅黑/微软雅黑 | **系统无衬线栈**（-apple-system、BlinkMacSystemFont、PingFang SC、Segoe UI、Roboto、Helvetica Neue、Arial） | 含 PingFang SC 达标 |
| 等宽字散布 | 6+ 处裸 ui-monospace 栈 | 收敛为 --font-mono 令牌，仅数据块（活动流/时间戳/ID/哈希/表格数字列/SVG 节点） | body/通用选择器零等宽达标 |
| 阴影 | 散落硬编码 | **三档令牌** --shadow-1 卡 / --shadow-2 浮层（吸顶顶栏）/ --shadow-3 弹窗（预留），box-shadow 零裸色值 | 定死一次达标 |

### 色板构成（18 种，只落令牌区）
- 灰阶 12 级单坡双主题镜像：浅 g1 最浅→g12 最深，深主题同名反向——同 12 值复用。
- 品牌蓝 #2563EB（浅强调；深主题 color-mix 55% 混白自动提亮）。
- 语义三元浅色 #157347 / #d92d20 / #b54708；深色 #ff7a70（danger，用掉第 18 个名额）与 #f0b429（warn），深色 ok 用 color-mix 55% 混白。
- 规则区一律 var()/currentColor；徽章按设计档 CSAI 配方=淡彩底（currentColor 12% 混 card）+实色字。

### 渲染真值（Playwright 尺子，Chrome 1440×900，两主题×七页）
- body 计算字族 = -apple-system、15px；浅底 #f6f8fb / 深底 #182230（镜像生效）。
- 全部可见文本计算字号都在五档内；横向溢出 0 页。
- 对卡底对比度：浅色 ink 16.03 / dim 5.43 / ok 5.87 / bad 4.83 / warn 5.43 / accent 5.17；深色 ink 11.68 / dim 5.39 / ok 4.85 / bad 4.60 / warn 6.27 / accent 5.02——**全档 ≥4.5:1（WCAG AA）**。
- 卡阴影令牌生效（浅 6% / 深 45% 透明度）；color-mix 支持验证通过。

## 三、验收证据

- TDD：tests/test_ui_craft.py 先红（8 项失败，逐条对应病根）→ 改七页 → 全绿（11/11）。
- 模块回归：test_ui_craft + v09a/b/c/d 全家（skin/session/zhulong/closeout）共 196 项 OK。
- **全量：python3 -m unittest discover -s tests → Ran 1491 tests, OK**（基线 1479 + 本批 11 + 主会话 setState 热修钉 1，零破坏）。
- python3 -m py_compile tests/test_ui_craft.py → OK。
- 8900 常驻服务未动（截图即打自常驻实例）。

## 四、九页截图路径清单（最终验收——请亲自过目）

目录：docs/research/liveui/shots/craft-v09d/

1. 01-home-light.png——战局总览·浅色（战斗卡/九门/KPI/预算/发现流/活动流）
2. 02-home-dark.png——战局总览·深色（镜像主题）
3. 03-activity.png——活动流（SSE 追尾，等宽数据块）
4. 04-session.png——会话回放（全页长图：对话流+工具卡折叠）
5. 05-coverage.png——覆盖热图（三态格+图例）
6. 06-graph.png——十边图（十色连线+分层）
7. 07-evidence.png——证据卡（重放三态徽章）
8. 08-metrics.png——度量（统计卡/召回曲线/逐战明细）
9. 09-metrics-experiments.png——度量·实验小节锚定视图

拍摄参数：Chrome headless 1440×900，domcontentloaded + 2.2–3.0s 定额沉降（SSE 页未用 networkidle），fullPage（09 为锚定视口）。

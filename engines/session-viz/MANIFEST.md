# session-viz 引擎 MANIFEST（契约 08 十二字段；kind=projector）

kind: projector

| 字段 | 值 |
|---|---|
| name | session-viz |
| kind | projector（只读账本投影；产物不回写、零落账） |
| version | 1.0.0（批次 4 T11） |
| 适用场景 | 单 goal 交战区作战视图：findings 实时流值守刷新；零依赖单文件 HTML 可离线发送（R4） |
| 参数 | render --goal-dir D --out <path.html> [--data-only] |
| 产物路径 | --out 指定 HTML（goal 目录外）；--data-only=stdout JSON（金样面 viz-data） |
| 超时 | 不适用（本地只读投影，毫秒级） |
| 重试策略 | 不适用（只读幂等：同账本两次渲染字节一致） |
| 幂等键 | goal 目录内容（确定性投影：全排序输入零墙钟） |
| 纪律能力声明 | 只读 13 表+timeline（零回写不变式测试钉死）；渲染零依赖 SVG+vanilla JS（R4）；实时流=作战视图（内部），对外交付仍走 P5 报告签发门 |
| 工具依赖 | 无（python3 stdlib；无外部渲染库/网络资源） |
| 验签公钥 | 不适用 |

## 视图清单（数据岛六键=六区；前五区计划冻结+第六区追加件 fb72cd5）

1. stats 统计栏——13 表 counts+confidence×impact 分色图例（C1 绿/C2 黄/C3 灰/➖🛑 红）+攻击链数（attack 边计数）+矩阵覆盖率（非空格/全格）+converge 计数+预算进度条（budget.tsv 汇总）
2. findings_stream 实时流——最新 N=20 条（时间/资产/类型/severity/状态），high/critical（impact=高|high|critical）置顶+▲标记；确定性输出可金样化（docs/design/2026-09-24-finding-stream-priority.md）
3. phases Pipeline 时间轴——gate-exit 序列，当前高亮=最后一门
4. graph 图谱区——分层 SVG（G/INT/AST+CRED/F/FD/EV 六层坐标）；attack 金/cross_ref 虚线/supersedes 点线/scope-rel 灰/其余 solid；candidate 半透明 opacity=0.45；kind 过滤按钮+id 搜索+分层/力导向两档纯计算布局（无随机源）
5. rightpanel 右面板——未消费 fact 清单（derived_from 出边判）/风暴 origin 徽章/清理清单核销计数（revert_cmd 未核销）/节点详情（点击）
6. authz_matrix 身份矩阵视图——role×endpoint 覆盖表 covered=■（cli/ledger/authz_matrix.coverage 单源，T8 交付）

## 边界

- projector 型：引擎不写账本（单写者不变式）；--out 产物落 goal 目录外，--data-only 仅 stdout。
- 实时披露≠合规披露：实时流是内部作战视图，对外交付走 P5 报告签发门（设计增补边界纪律）。

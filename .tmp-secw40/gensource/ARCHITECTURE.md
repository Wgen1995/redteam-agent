# GenSource 架构文档

> SUPERSEDED for 执行模型 by docs/superpowers/specs/2026-08-19-gensource-sdwr-mining-agent-design.md。本文 77 方程仍作形状门参考，调度以规格为准。

## 一、项目定位

GenSource 是一款基于 LLM 的多阶段源码安全审计系统，通过 18 个子任务串并组合：确定性脚本枚举攻击面（source）与危险点（sink）并逐点发卡，类级剪枝整类消除（消消乐），逐文件子代理追踪数据流画污点边（扫雷），77 条机械方程验证每个 LLM 可写位，A2 独立终审 + 包外闭卷锚点验收。

核心依赖：
- 宿主 Agent（opencode）+ 1 文件 1 subagent 批循环（batch_size=10）
- 5 个确定性脚本：enumerate.py / derive_checkpoints.py / wu_decompose.py / build_graph.py / gate-1.py（77 方程）
- 知识层：58 类 sink 跨语言 grep 模式 + 148 vuln-patterns + FALSE-rules + 枚举注册表
- 闭卷锚点（tests/golden/，包外）+ acceptance.py 验收

## 二、架构全景图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              GenSource                                  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │          SKILL.md（PhasedLine 18 子任务调度入口）               │    │
│  │       0.1→0.6 → 1.1→1.5b → 2.1→2.2 → 3.1→3.2 → 4.1→4.2       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────▼────────────────────────────────────┐    │
│  │              确定性引擎（LLM 零参与）                          │    │
│  │  enumerate.py ──► derive_checkpoints.py ──► wu_decompose.py    │    │
│  │   (三清单+logs)     (检查点账本)            (WU 清单+批表)      │    │
│  │        └──────────────► build_graph.py ◄──────────────────┘    │    │
│  │              （账本→knowledge_graph/nodes+edges 确定性投影）     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────▼────────────────────────────────────┐    │
│  │                   LLM 批循环（语义分析层）                      │    │
│  │   类剪枝 subagent（0.6 消消乐）→ WU subagent（1.2 扫雷逐文件）  │    │
│  │   reviewer subagent（每 LLM 子任务层2语义）→ A2（3.2 四门+V5）  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────▼────────────────────────────────────┐    │
│  │            gate-1.py（宿主执行，77 方程机械验证）               │    │
│  │     每子任务 --subtask 中途闸 + 终态无 --stage 全量硬门         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────▼────────────────────────────────────┐    │
│  │         acceptance.py 闭卷验收（包外，agent 不参与）            │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

**LLM 调用闭环（每个分析动作触发）**：
```
主代理派发 subagent → agents/*-prompt.md 模板（红线+判定纪律+TDD 五步）
  → 子代理只读工具逐跳 Read 源码（每观察先追加 audit_log）
  → 写产物文件（WU 分片/flow_edges/clusters）
  → 主代理跑 gate-1.py --subtask {id}（判定栏脚本输出）
  → FAIL 返工本子任务 → PASS 记 gate_progress.tsv → 进下一子任务
```

**gate-act 协议**：每子任务完成后跑 `gate-1.py --session {S} --source {SRC} --subtask {id}`；任一 FAIL 返工本子任务；PASS 记 gate_progress 一行；禁止提前进下一子任务；终态必须无 --stage 全量 gate。

## 三、执行流程（18 子任务）

### 3.1 整体串并联图

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 0.1 初始化 → 0.2 黄金自检 → 0.3 枚举 → 0.4 发卡 → 0.5 语境 → 0.6 消消乐   │
│   (串行)      (串行)        (串行)    (串行)   (串行)    (串行)            │
│                                                                          │
│ 1.1 WU分解 → 1.2 扫雷(批循环) → 1.3 簇关联 → 1.4 候选 → 1.5b 发散        │
│   (脚本)      (并行每文件)      (串行)      (串行)     (并行单次)         │
│                                                                          │
│ 2.1 逐候选验证 → 2.2 V文件 → 3.1 报告 → 3.2 终审硬门 → 4.1 闭卷验收      │
│   (并行每候选)    (串行)      (串行)    (串行+并行每finding)  (包外)      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 各子任务检测逻辑详解（核心目标 + 检测逻辑 + 实际产物示例 + gate）

#### 0.1 初始化（串行单次）
核心目标：核实目标、钉死版本、建目录、环境声明。

检测逻辑：
```
┌─────────────────────────────────────────────────┐
│ ① 核实 source_path 存在/可读/已授权             │
│ ② source_revision 核实（git commit；非 git 用  │
│    目录+文件数+哈希快照描述）——验收按它判版本  │
│ ③ 建 run 目录；写 capability-profile.md        │
│    （环境声明+闭卷隔离：tests/golden 不可见）   │
│ ④ 写 run-state.md 初始版（run_status: running）│
└─────────────────────────────────────────────────┘
```
gate --subtask 0.1：产物存在性。

#### 0.2 黄金自检（串行单次，不通过=blocked）
核心目标：验证 gate 脚本在本环境完好——先做答案已知的样卷。

```
执行 gate-1.py --session gate-selftest/fixture
             --source gate-selftest/fixture-src
             --expect gate-selftest/expected-gate.txt
输出 SELFTEST: PASS（全部方程判定与标准答案逐行全等）才继续
不等 = 环境 gate 不可用 → run_status=blocked 停
```
黄金夹具 = gate-selftest/fixture（小假项目：2 个 Java 文件 + 全套标准产物，答案已知）+ expected-gate.txt（标准判定输出）。

#### 0.3 确定性枚举（串行单次，脚本，LLM 零参与）
核心目标：全量圈出三份清单——文件、危险点（sink）、入口（source）+ 调用边。

检测逻辑：
```
┌─────────────────────────────────────────────────┐
│ ① os.walk 全量文件（每层排序→确定性），滤 .git │
│ ② 读文件头 8192 字节，NUL>0.5% → binary 探测   │
│ ③ 写 file_inventory.tsv（6 列）                │
│ ④ 解析知识层 58 类 sink 模式（管道重建+语言组  │
│    切分），每语言合并命名组大正则               │
│ ⑤ 逐文件流式逐行一次 search，命中记            │
│    (path,line,class,code[:80])，滤 /test/       │
│    每类写 logs/sinks_{type}.log 原始全量        │
│ ⑥ 写 sink_inventory.tsv（sink_id=md5[:8]）     │
│ ⑦ 入口 10 通道×7 语言模式表 → source_inventory │
│ ⑧ call_edges.tsv（import+call 边全量不截断）   │
│ ⑨ 全知识类 logs 补零（ZERO_HITS / PATTERN_     │
│    UNAVAILABLE 两种「没有」严格区分）           │
└─────────────────────────────────────────────────┘
```

实际产物示例（run-18-spring 真实数据）：
```tsv
# sink_inventory.tsv（sink_id | file:line | sink_type | symbol | sort_order）
b4297b97   buildSrc/src/main/java/org/springframework/build/api/ApiDiffPlugin.java:109   SINK-FILE-TRAVERSAL   Paths.get   1

# source_inventory.tsv（source_id | file:line | entry_type | symbol | param | sort_order）
0eccdf5d   spring-web/src/main/java/org/springframework/web/servlet/DispatcherServlet.java:1040   rest   doDispatch   -   42

# file_inventory.tsv（path | type | lang | loc | binary_flag | sort_order）
spring-beans/src/main/java/org/springframework/beans/CachedIntrospectionResults.java   source   java   -   text   1

# logs/sinks_SINK-DESERIALIZE.log（path:line:text，与清单精确对账）
spring-core/src/main/java/org/springframework/util/SerializationUtils.java:120:ObjectInputStream ois = new ObjectInputStream(...)
```

gate --subtask 0.3：信号级禁入（清单不得含 7 噪声类）+ 枚举锚定(类集合)（每类要么有命中要么有 ZERO_HITS 日志）+ 枚举来源强制（知识表不可读 FAIL）+ **枚举对账**（logs 滤 test 去重行数==清单行数，差 1 FAIL——脚本漏扫一行对账失衡）。

#### 0.4 检查点派生（串行，脚本）：发卡
核心目标：给每个 sink/source/文件发一张待查记录——账本骨架，初始全红「未检查」。

```
每 sink → 1 行 backward 检查点；每 source → 1 行 forward；每文件 → 1 行 terminal；
文件级机械预筛：二进制/文档无 sink 命中 → not_applicable（prefilter_no_exec:）
```

实际产物示例：
```tsv
# check_point_ledger.tsv（basis_id|direction|mechanism|check_point_id|candidate_ids|terminal_state|reason|concluded_at）
b4297b97    backward   needs_analysis  CP-012345                     未检查
0eccdf5d    forward    pattern_driven  CP-018290                     未检查
docs/README.md  terminal  prefilter  CP-000008   not_applicable  prefilter_no_exec:doc:0命中证据  2026-08-14T00:05:00Z
```

gate --subtask 0.4：planned==terminal——「未检查」数必须为 0 才算终态（扫雷完成前恒 FAIL，是「没跑完装不了完成」的总闸）。

#### 0.5 威胁语境（串行，不阻塞）
```
① 以 file_inventory 客观分布做技术栈统计
② 写 attack-surface-map.md（外部触达面清单）
③ 写 threat-context.md（保守假设 conservative_continue，不等用户）
```
gate：文件存在。

#### 0.6 消消乐第一波：类级剪枝（串行，类剪枝 subagent + A2 签字）
核心目标：批循环前用三类固有属性判据整类消除卡片。只判类属性，禁实例结论。

判定逻辑：
```
┌─────────────────────────────────────────────────────────────────┐
│ S1 source 类剪枝：某 entry_type 攻击者不可控？                  │
│    证据 = 赋值处无外部输入（环境变量/部署配置/字面量）          │
│    → scope=SOURCE-{entry_type}                                 │
│ S2 sink 类剪枝：某 sink_type 非危险操作？                       │
│    证据 = 命中是注释/死代码/API 无危害                          │
│    → scope={sink_type}（原值自带 SINK- 前缀）                  │
│ S3 净化器摘要：某函数 f 阻断 sink 类 S 的污点？                 │
│    证据 = f 内校验代码行，摘要必须声明适用范围 S               │
│    → scope={sink_type}-via-{函数名}                            │
│                                                                │
│ 铁律：只判固有属性禁判实例结论；无证据不判；不确定留给 WU      │
└─────────────────────────────────────────────────────────────────┘
```

闭环：判据追加 pruning_ledger.tsv 7 列（a2_verified 留空）→ A2 V5 门逐行回填 true/false（false 不生效）→ build_graph 重投影（被剪节点 pruned+pruned_by+pruned_reason）。

实际产物示例：
```tsv
# pruning_ledger.tsv（operator|criterion|scope|evidence|judged_by|timestamp|a2_verified）
S1   source not controllable: literal constant   SOURCE-rest   java/a/B.java:5   PRUNE-A2   2026-01-01T00:00:00Z   true
S3   sanitizer blocks SINK-XXE taint             SINK-XXE-via-validate   java/c/D.java:7   PRUNE-A2   2026-01-01T00:00:00Z   true
```
```json
// nodes.json 中被剪节点（消消乐图显式化）
{"id":"source:r1","type":"source","attrs":{"file_line":"java/a/B.java:10","entry_type":"rest"},"status":"pruned","pruned_by":"S1","pruned_reason":"source not controllable: literal constant"}
```

gate --subtask 0.6：剪枝判据落盘（4 字段非空）+ 剪枝 A2 复核（a2_verified ∈ {true,false}）。

#### 1.1 WU 分解（脚本，含剪枝排除）
```
① 读 pruning_ledger：a2_verified=true 的 S2/S3 剪掉的 sink 类剔除
   （剪掉的不再派 WU——消消乐落地）
② 剩余按文件分组：1 文件 = 1 WU 恒成立
③ batch_size=10 编批；写 wu_manifest + batch_progress
④ 初始化 flow_edges/graph_snapshot/progress_board/live_findings_index
⑤ build_graph 初始投影
```

实际产物示例：
```tsv
# wu_manifest.tsv（wu_id|sink_type|sink_ids|sink_locations|sink_count|status|cluster_id|batch_num）
WU-0001   java/a/B.java   s1;s2   java/a/B.java:10;java/a/B.java:20   2   pending   CL-f4a1c2b3   B001
# batch_progress.tsv（batch_num|status|wus_total|wus_done|findings_count）
B001   completed   1   1   1
```

gate --subtask 1.1：WU 闭合（分片 sink 并集==清单−剪枝豁免）。

#### 1.2 扫雷：逐 WU 分析（批循环，并行每文件，全系统最重环节）
核心目标：每张卡 TDD 五步翻一次，必须画污点边，结论写回账本。

检测逻辑：
```
┌─────────────────────────────────────────────────────────────────┐
│ 派发：同一条消息多次 Task=并行（batch-size 个同时发）；         │
│ 禁止合并 WU；取第一个 pending 批（禁跳批乱序）                  │
│                                                                 │
│ 每 WU 逐 sink 独立五步（wu-analyzer-prompt 原文）：              │
│ ① DEFINE CRITERIA：追链前先写本 sink 的 candidate 判据          │
│    （含本类防护模式，从 sinks/_index.md 查）                    │
│ ② OBSERVE：Read sink 行±10 行，确认代码真实存在                 │
│    （非注释/字符串）；每观察先追加 audit_log 再引用             │
│ ③ HYPOTHESIZE：假设 source 路径（待验证命题，非结论）           │
│ ④ VERIFY：沿调用链逐跳 Read，逐要素证伪                        │
│    （source 可控？路径可达？防护失效？）；证据三级              │
│    （直接/间接/未知），结论强度不超过最弱一环                   │
│ ⑤ CONCLUDE：全要素证伪失败→candidate；某要素被直接证据证伪     │
│    →disproved（附证伪行号）；追不动（8跳/10文件）→blocked；     │
│    证伪中止于缺口→unconfirmed。IMPACT-ANCHORING：sink 可达但    │
│    gadget 未证实→只降严重度禁判 disproved                       │
│                                                                 │
│ 反偷懒：禁「与其他 sink 相似」跳过；禁「本 WU 全部安全」批量    │
│ 结论；每跳必须 Read 附行号；输出前自检 sink 数==输出行数        │
│                                                                 │
│ 画线（每 sink 必须一条 flow 边）：                              │
│   reachable（追到 source 无防护）/ blocked_at（有防护附断点）/  │
│   no_path（追不到）。证据引用化（行号+最小片段）。              │
│   没有边就没有闭合。写完跑 build_graph 重投影                   │
└─────────────────────────────────────────────────────────────────┘
```

实际产物示例（run-18-spring 真实数据）：
```tsv
# batches/B001/WU-0001.tsv（严格 5 列：sink_id|verdict|five_segment_evidence|evidence_refs|reviewed_at）
b4297b97   candidate   project.property("baselineVersion") via -PbaselineVersion CLI|applyApiDiffConventions:65→createApiDiffTask:66→getOutputFile:108-112|none detected|Paths.get:109 constructs path with user-controlled baselineVersion component enabling traversal|confirmed: user-controlled version string flows unsanitized into path constructor   ApiDiffPlugin.java:65,66,108-112   2026-08-17T22:30:00Z
0fe6c278   disproved   source=constructor::aspect-internal|propagation=direct-field|sanitizers=n/a|sink=logger.debug()|disproof_checked=no_external_input_reaches   AspectJExpressionPointcut.java:381   2026-08-17T22:31:00Z

# flow_edges.tsv（source_id|sink_id|direction|hops|evidence_refs|judged_by|timestamp）
0eccdf5d   b4297b97   reachable   2   DispatcherServlet.java:1040,ApiDiffPlugin.java:109   WU-0001   2026-08-17T22:30:00Z

# audit_log.tsv（check_point_id|basis_id|direction|result|evidence_type|evidence_ref|reviewed_at）
CP-012345   b4297b97   backward   candidate   direct   ApiDiffPlugin.java:109   2026-08-17T22:29:00Z

# graph_snapshot.tsv（每批追加：batch|unchecked|candidate|disproved|not_applicable|blocked|flow_edges|pruning_rules|graph_nodes|graph_edges）
B001   1410   1   42   128   0   6   2   1440   21600
```

回填：主代理把分片 verdict 写回 check_point_ledger（跑了必须回填）。
每批闭环六动作：build_graph 重投影 → graph_snapshot 追加 → progress_board 一行 → live_findings_index 追加 → batch_progress completed → gate_progress 批进度行。

扫雷信息级联（v0.11.3 doc 115，同批 WU 信息反哺同类）：
```
三态信息板 mine_scan_board.md：fact（确定性事实，工具可复验）/
clue（判定基准，可独立复核）/break（已确认断点）三区 + 精查清单。
WU 追链现场直写 proposed 条目（每批末主代理转 verified）；
下游 WU 的 DEFINE 判据必须逐条对照相关条目（引用或写明反驳，禁无视），
但引用 clue 不替代独立五步（结论仍本 WU 独立下）。
通道 B 断点传播保守：break 是线索不是自动消除，下游引用时仍需一次独立复核。
通道 C 雷邻精查：candidate 的 flow 链上游未查检查点进精查清单，派发优先。
三态隔离铁律：信息板只放事实/线索/断点，结论词禁止入板（结论级联=错误级联入口）。
```

gate --subtask 1.2（反糊弄方程网 14 条）：WU 分片质量（表头 5 列/verdict 三值/行数守恒）+ 分片回填对账 + 终态 sink 边闭合 + flow 边值域 + 禁批量采样闭合（reason 必含真实引用且引用行存在）+ 证据密度下限（无引用≤20%）+ 推导链强制 + 时序检查 + audit_log 追加单调性 + 发现索引对账 + 看板行数 + 信息板格式（每条含 file:line 证据）+ 信息板结论隔离（禁结论词）+ 级联覆盖（reachable 上游未查检查点∈精查清单或已派 WU）。

#### 1.3 簇级关联（串行，主代理全局地图）
核心目标：跨 WU 同根因候选归堆，每堆带攻击模式对抗表。

实际产物示例（run-18-spring 真实）：
```markdown
# CL-FILE-TRAVERSAL-BUILD: 构建脚本文件路径遍历

## 代表性实例五段证据链
**文件**: buildSrc/src/main/java/org/springframework/build/api/ApiDiffPlugin.java:109
**Source**: project.property("baselineVersion") — Gradle -PbaselineVersion CLI 传入的用户可控版本号
**Propagation**: applyApiDiffConventions(L65) → createApiDiffTask(L66) → getOutputFile(L108-112)
**Sanitizers**: 无 — 未对 baselineVersion 做路径遍历检查
**Sink**: Paths.get() (L109)
**Disproof_checked**: build-time 组件；需构建参数控制权

## 攻击模式对抗表
| 攻击模式 | 适用 | 理由 |
| UVS-PATH-TRAVERSAL-INPUT | 否 | Build-time 环境 |
| UVS-SUPPLY-CHAIN | 是 | 恶意 -PbaselineVersion 可控制输出位置 |

## 终态映射
| CheckPoint | 终态 |
| ApiDiffPlugin.java:109 | candidate (build-time, 低严重度) |
```

gate --subtask 1.3：对抗表存在 + 簇引用真实性（词边界含 basis_id）+ 簇覆盖上限（单簇>500 行或引用>100 basis FAIL）。

#### 1.4 候选提取（串行，主代理）
候选 ID 确定性派生：C-{sink_seq:05d}-{source_seq:05d}-{sig8}（seq=冻结清单字节序序号，sig8=md5(file:line:sink_type)[:8]）。

实际产物示例：
```tsv
# candidates.tsv（16 列，含 discovery_reasoning_note 防工具原文抄袭）
C-01234-01829-1d832469   java/a/B.java:10   SINK-DESERIALIZE   critical   RCG-DESER-TEST   reported   confirmed   clusters/SINK-DESERIALIZE.md   verification-summary.md#C-01234-01829-1d832469   V01   2026-08-14T00:00:00Z   pattern_driven   java/a/B.java   10   10   从 source 追链到 readObject，逐跳证据见 flow_edges
```

gate --subtask 1.4：候选 ID 反查（编号反解回清单且位置一致）+ 三事实源一致性 + 候选类型一致性 + 候选推理非工具原文 + 合并守恒。

#### 1.5b A5 发散轮（并行单次，独立红队 subagent）
≤20 条带锚点假设（缺失检查/业务逻辑/组合三方向，禁复述已有候选），追加 check_point_ledger hypothesis 行（direction=hypothesis/mechanism=divergent_reasoning/reason=anchor_ref+推理链），走同一流水线。

gate --subtask 1.5b：假设锚点强制 + 假设上限 + A5 痕迹强制（skip 理由注册枚举）。

#### 2.1 逐候选验证（并行每候选）
六项基线：三要素（source 可控/传播链/配置）+ 配置实证 + 证据分级 + 档位 + FALSE-rules + CVSS。verdict 回填。

实际产物示例（verification-summary.md）：
```markdown
# Phase 2 Verification & Rating
> version=v0.3.9 | runtime_verification=denied

## Stage Gate Summary
| Candidate | Verdict | Confidence |
| C-00001-00001-1d832469 | confirmed | 0.6 |

### C-00001-00001-1d832469: B.java 反序列化无类过滤
**FALSE-rules**: none hit.
**Three Elements**: | Element | Annotation | evidence_grade | ...
```

gate --subtask 2.1：四相等+阈值（V 文件数==machine-fields==confirmed==report 引用数）+ 档位诚实（runtime_verification=denied 时 tier<6 直接 FAIL）+ audit 双向覆盖。

#### 2.2 V 文件完整性（串行，每 finding 一份）
findings/V{NN}-{severity}-{sink_type}-{file}-{line}.md，8 节，机械下限 ≥5 节+≥3 引用+≥40 行+含候选 ID。

实际产物示例（黄金夹具 V01 真实内容）：
```markdown
# V1: B.java 反序列化无类过滤
## 1. 识别信息   | candidate_id | C-00001-00001-1d832469 | finding_id | V1 |
## 2. 漏洞摘要   测试夹具：readObject 无 ObjectInputFilter。
## 3. 调用链     source: doPost(req) -> sink: readObject（java/a/B.java:10）
## 4. CVSS 3.1   CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (9.8)
## 5. 详细分析   测试夹具详情。
## 6. 数据流语义变迁表   | step=1 | location=java/a/B.java:10 | state=tainted | cause=request |
## 7. 证据分级标注   全 direct（测试夹具）。
## 8. 三态结论   verdict: confirmed, confidence: 0.6, runtime_tier: 6
```

gate --subtask 2.2：V文件完整性 + finding 文件名格式 + V 文件候选映射（report_record_ref==V{NN} 且 V 文件含该候选 ID 一一对应）。

#### 3.1 报告投影（串行）
machine-fields.json 六核心键 + report.md 汇总索引。

实际产物示例：
```json
[{"candidate_id":"C-00001-00001-1d832469","location":"java/a/B.java:10","sink_type":"SINK-DESERIALIZE","severity":"critical","root_cause_group_id":"RCG-DESER-TEST","verdict":"confirmed","confidence":0.6,"evidence_grade":"direct","runtime_tier":6}]
```
```markdown
# 安全审计报告
## 分级分区表
| # | 严重度 | 摘要 | 对象定位 | 详情 |
| 1 | Critical | B.java 反序列化无类过滤 | java/a/B.java:10 | [查看](findings/V01-critical-SINK-DESERIALIZE-B.java-10.md) |
```

gate --subtask 3.1：四相等+阈值 + 三事实源一致性。

#### 3.2 完成硬门（串行 + A2 并行每 finding）
```
① 终态全量 gate（无 --stage，77 方程全验，任一 FAIL 不得 completed）
② A2 四门（V0 枚举复核/V1 闭环与真分析/V2 候选重验/V3 报告投影）
   + V5 剪枝复核 → 写 gate2_notes.md 物理文件（含四门标记+引用
   verification-summary.md）
③ run_fingerprint = sha256[:16]（六核心键 §7 口径）写回 run-state
④ 全 PASS → run_status=completed
```

实际产物示例（gate2_notes.md / gate_record.md）：
```markdown
# A2 独立验证四门结论（复核对象：verification-summary.md）
V0 事实源对账 pass：三清单/账本/候选交叉一致。
V1 逐候选重建验证 pass：C-00001 从源码独立重建证据链成立。
V2 负向对抗 pass：证伪尝试失败，无换皮贴标。
V3 剪枝判据复核 pass：pruning_ledger 两行 a2_verified=true。
```
```markdown
# gate_record.md（77 方程逐条判定）
| 1 | planned==terminal | 0 | 成立 |
| 52 | WU 分片质量 | 0 | 成立 |
gate_result: pass
```

gate --subtask 3.2：run_status 一致性 + A2 独立验证硬门（文件存在+四门标记+引用终稿，不读 run-state 字符串）+ gate_progress 痕迹 + batch_progress 完成率 + reviewer 派发痕迹（8 个 LLM 子任务 reviews/{id}-review.md）。

#### 4.1 闭卷验收（包外，agent 不参与）
覆盖=锚点版本区间含目标版本；命中=candidates/findings 提及 CVE 或修复位置；污染=CVE 编号出现在任何 run 产物。

实际输出示例：
```
| CVE | 覆盖 | 命中 | 污染 | 位置 |
| CVE-2022-22965 | covered | hit | clean | spring-beans/.../CachedIntrospectionResults.java |
召回: 2/2   有效召回（扣污染）: 2/2   污染锚点数: 0
```

#### 4.2 稳定性双跑
同参数二跑，machine-fields 六核心键逐 finding diff==空；run_fingerprint 跨 run 一致。

## 四、图机制（knowledge_graph）

图 = build_graph.py 从账本确定性投影（LLM 禁写）：节点 6 类（sink/source/file/checkpoint/candidate/finding），边 3 类（basis=清单→检查点 / flow=污点流 / derived=检查点→候选、sink→候选、candidate→finding 机械 join）。节点 status 机械推导：类级剪枝→pruned+pruned_by；全行 disproved→pruned；全 blocked→blocked；含 candidate→candidate；否则 unchecked。

图演进：0.4 全 unchecked+21540 basis 边 → 0.6 被剪类 pruned（消消乐）→ 1.2 每批 flow 边增长、disproved 翻 pruned（扫雷，graph_snapshot 计数）→ 1.4/2-3 candidate/finding 节点+derived 边 → 终态图=active 节点+reachable 边=漏洞路径图（source→flow→sink→derived→candidate→derived→finding）。gate 四方程（#38-41）校验投影。

## 五、gate-1.py 77 方程语义表

| # | 方程名 | 检查什么（机械逻辑） | 防什么 |
|---|---|---|---|
| 1 | planned==terminal | 账本「未检查」行数==0 | 没查完宣布完成（总闸） |
| 2 | sink 回溯覆盖 | 清单 sink 集−账本 backward 集==空 | 危险点没发卡 |
| 3 | source 前向覆盖 | 清单 source 集−账本 forward 集==空 | 入口没发卡 |
| 4 | audit 双向覆盖 | 清单 sink 集与 audit_log backward 集双向差==空 | 观察账对不上号 |
| 5 | 四相等+阈值 | V 文件数==machine-fields==confirmed==report 引用数；mf 每条 tier/confidence 过阈值表，tier6 需 evidence_grade==direct，非法值 fail-closed | 三本账打架、档位虚标 |
| 6 | failed 清单去真空 | failed_wus 行数==账本 blocked 数，且 blocked 的 basis 全在 failed_wus | 标失败不登记 |
| 7 | 账本零残留 | 账本全文「未检查」计数==0 | 残留未查 |
| 8 | 反伪闭合(全方向) | not_applicable 行 reason 必须规定前缀 | 乱编理由当挡箭牌 |
| 9 | 簇产物存在 | clusters/*.md 数量>0 | 跳过簇关联 |
| 10 | 全终态理由封闭 | disproved 必须规定前缀且 disproved_safe 必须含 file:line；blocked 必须 budget:/user_decision:/permission: | 无理由终态 |
| 11 | 候选 ID 反查 | 候选编号拆段反查：location 在清单且 sig==md5 校验 | 自造编号 |
| 12 | 产物存在性 | 9 个产物文件+clusters 非空 | 缺产物交卷 |
| 13 | 信号级禁入 | 清单不得含 7 噪声类 | 噪声类混进清单 |
| 14 | 三事实源一致性 | confirmed 集^机器字段集==空；report 有引用却无 confirmed FAIL | 三本账打架 |
| 15 | 对抗表存在 | 每簇文件含「## 攻击模式对抗表」 | 簇分析无对抗审查 |
| 16 | schema 全等 | 全部 TSV 表头逐列==契约 | 列序漂移假通过 |
| 17 | 引用可解析 | 引用行必须真实存在、簇文件必须存在 | 假引用 |
| 18 | 证据唯一性 | 同一引用被 >50 检查点复用 FAIL（>10 告警） | 一条证据反复贴 |
| 19 | 档位诚实 | runtime_verification=denied 时 tier<6 FAIL | 未验证却降档 |
| 20 | 推导链强制 | 终态检查点必须在 audit_log 出现过 | 有结论无观察 |
| 21 | 时序检查 | 结论时间晚于观察时间，两字段必填 | 先结论后补观察 |
| 22 | WU 闭合 | 分片 sink 并集==清单−剪枝豁免 | 派活漏派多派 |
| 23 | 假设锚点强制 | 假设 reason 含 file:line | 无锚点假设 |
| 24 | 假设上限 | 假设数≤20 | 发散失控 |
| 25 | 枚举锚定(类集合) | 知识类集−清单类集−零命中类集==空 | 静默丢类 |
| 26 | 候选ID确定性强制 | 编号匹配格式且 location 在清单 | 乱编编号 |
| 27 | 候选类型一致性 | 候选 sink_type ∈ 清单类集 | 类型错配 |
| 28 | WU 派发记录 | wu_dispatch 每行 verified 非空，否则 wu_skip_reason | 派发无记录 |
| 29 | V文件完整性 | 8 节≥5 + ≥3 引用 + ≥40 行 + 含候选编号 | 空壳报告 |
| 30 | 候选推理非工具原文 | 推理说明非空且不以 WARNING/ERROR/INFO 开头 | 工具原文抄袭 |
| 31 | finding 文件名格式 | V{NN}-[a-z]+-SINK-[类]-[文件]-[行].md | 命名乱 |
| 32 | 枚举来源强制(禁自造类) | 清单类型∈知识类集；知识表不可读 FAIL | 自造类名 |
| 33 | batch_progress 完成率 | 每批 status==completed | 批没跑完 |
| 34 | 短路质量检查 | 0 发现且 audit_log 空 FAIL | 空跑交卷 |
| 35 | 候选边支撑 | confirmed 候选位置匹配的 sink 至少一个 reachable 边 | 候选无污点线支撑 |
| 36 | 剪枝 A2 复核 | pruning_ledger 每行 a2_verified∈{true,false} | 剪枝未经复核 |
| 37 | flow 边节点存在 | 边两端都在清单 | 悬空边 |
| 38 | 图节点投影完整性 | gate 独立重算节点集对称差==0 | 投影漏投 |
| 39 | 图边投影完整性 | 同上边集 | 投影漏边 |
| 40 | 图投影确定性 | 图文件==内存投影（CRLF 规范化） | 手改图/陈旧 |
| 41 | 图边端点存在 | 图边两端∈节点集 | 图内悬空边 |
| 42 | flow 边值域 | direction 三值；reachable 需引用；hops 必填 | 伪造可达 |
| 43 | V 文件候选映射 | report_record_ref==V{NN} 且唯一且 V 文件含该候选 | 报告错位 |
| 44 | 剪枝边一致性 | S1 剪的 source 类边不得 reachable | 剪了又画通 |
| 45 | 账本枚举封闭 | direction/terminal_state ∈ 注册枚举 | 乱写状态 |
| 46 | 证据密度下限 | 无引用终态占比≤20% | 大面积空壳 |
| 47 | 簇覆盖上限 | 单簇>500 行或引用>100 basis | 全量贴标簇 |
| 48 | reviewer 派发痕迹 | 8 个 LLM 子任务各有 reviews 文件含 PASS/FAIL | 审阅没跑 |
| 49 | 终态 sink 边闭合 | 终态 sink 必须在 flow_edges（剪枝豁免） | 不画线批量闭合 |
| 50 | 合并守恒 | 候选集^账本候选引用集==空 | 凭空候选/丢候选 |
| 51 | audit_log 追加单调性 | 时间戳行序单调不减 | 补写过去时间戳 |
| 52 | WU 分片质量 | 表头 5 列+verdict 三值+行数守恒 | 格式乱 |
| 53 | 分片回填对账 | 分片 sink 的账本终态非未检查 | 跑了不写回 |
| 54 | 发现索引对账 | 索引行数≥V 文件数 | 绕索引造报告 |
| 55 | 看板行数 | 看板行数≥完成批数+2 | 进度不可见 |
| 56 | 簇引用真实性 | 簇文件词边界含 basis_id | 贴标引用 |
| 57 | run_fingerprint 检查 | 指纹==sha256[:16] 重算 | 指纹乱写 |
| 58 | 剪枝判据落盘 | 剪枝账 4 字段非空 | 无证据剪枝 |
| 59 | 枚举对账 | logs 滤 test 去重==清单行数 | 漏枚举 |
| 60 | 批进度记录检查 | 验卷记录批进度行≥ceil(批/5) | 批循环无验卷痕迹 |
| 61 | 批数合理性 | batch_progress 批集^manifest 批集==空 | 批数对不上 |
| 62 | 候选同根因合并 | 同根因同位置重复 FAIL；confirmed 近邻行距≤10 必须合并 | 重复灌水 |
| 63 | blocked 双轨一致 | 批表 blocked 与账本 blocked 双向一致 | 单边标记 |
| 64 | audit_log ID 合法 | audit 行检查点编号∈账本 | 观察账自造编号 |
| 65 | gate_progress 全覆盖 | 14 子任务都有 pass/skip 行 | 跳过验卷 |
| 66 | 簇引用强制 | cluster_conclusion 必须引用具体簇文件 | 无对象引用 |
| 67 | A2 独立验证硬门 | gate2_notes.md 存在+四门标记+引用终稿+run-state 引用 | 声称终审 |
| 68 | 禁批量采样闭合 | backward/forward 终态 reason 必含真实引用且行存在 | 换皮批量闭合 |
| 69 | gate_progress 痕迹 | gate_progress.tsv 存在 | 全程不验卷 |
| 70 | fix_presence 禁止派生 | direction==fix_presence 行数==0 | CVE 锚点混进 run |
| 71 | A5 痕迹强制 | 有假设行或 skip 理由注册枚举；round>0 无假设 FAIL | A5 没跑装跑 |
| 72 | 缺失检查类强制 | 清单有 SINK-MISSING-CHECK 或有 skip 理由 | 缺失检查类被跳过 |
| 73 | run_status 一致性 | completed 时全方程无 FAIL | 带病完成 |
| 74 | 信息板格式（v0.11.3） | mine_scan_board fact/clue/break 每条证据列必须含可解析 file:line | 空口判定入板（无证据条目=级联污染入口） |
| 75 | 信息板结论隔离（v0.11.3） | 信息板数据行禁止 candidate/disproved/blocked/confirmed 结论词（单词边界精确匹配） | 结论入板=错误级联入口（定理 1 机械化） |
| 76 | 级联覆盖（v0.11.3） | reachable 边的上游未查检查点（source 前向+evidence_refs 链上文件）必须全在精查清单或已派 WU | 雷邻漏查（数字>0 邻格不翻） |
| 77 | gate 执行痕迹（v0.11.3） | gate 每次运行追加 gate_run_log.tsv；全量 gate 时 gate_progress 每个 pass 行必须对应真实 pass 记录 | 伪造 gate_progress（run-18-aiohttp 3.2 pass 实为 FAIL） |

（方程实际数量以 gate-1.py self.add 名单为唯一权威。）

## 六、反偷懒机制族（历史实证驱动）

| 实证教训 | 机制 | 方程 |
|---|---|---|
| 换皮贴标三轮（32K 批量闭合） | 负向证据闭合+密度下限+簇上限+词边界引用 | #68/#46/#47/#56 |
| 枚举漂移（15116/9361/6088） | 枚举归脚本+日志清单精确对账 | #59 |
| 自造候选 ID | ID 确定性派生+反查 | #26/#11 |
| 声称执行（run-18 6/132 批收尾） | 派发留痕文件化+红卡总闸 | #67/#48/#1 |
| 复杂即偷懒（wu_size=50） | 1 文件=1 WU | 粒度协议 |
| 跑了不落账（42 分片 0 回填） | 分片质量+回填对账+索引对账 | #52/#53/#54 |
| 伪造 gate 记录 | gate 宿主执行+LLM 禁写+证据封印 | 三权分离 |
| 伪造 gate_progress（run-18-aiohttp「3.2 pass」实为 FAIL） | gate_run_log 每次运行真实留痕+pass 对账 | #77 |
| 结论级联污染（错 disproved 传染同类=大规模漏报） | 信息板三态隔离（事实/线索/断点）+结论词禁令+雷邻覆盖对账 | #74/#75/#76 |

## 七、规模路径与诚实边界

规模：流式枚举 O(总行数)；1 文件 1 WU 天然分批断点续跑（多会话接力）；gate 对账与规模无关；消消乐前置减负。

边界：①语义层——证据引用「内容是否真支持结论」机器无法判，兜底=reviewer/A2 留痕方程机械强制派发；②执行层——零运行时编排下 agent 不跑 gate 无人当场拦（run-18：设计 100%，执行 3.2%），判据自我进化（每翻车升一项）。

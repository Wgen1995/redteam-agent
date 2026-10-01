# 契约变更日志

## v0.11.5 - run-19 pilot 阶段 1.3-3.2 验证回写

- gate：候选 ID 反查/确定性强制/候选边支撑三方程对 divergent_reasoning 候选（A5 假设产物）豁免清单位置检查（锚定合法性由假设锚点强制保证）；blocked 双轨一致只查「批标 blocked 而账本无」方向（sink 级 budget blocked 由 failed 清单对账承担）。
- acceptance.py：--project 过滤按 project 列比对（旧实现比对 fix 路径，aiohttp 路径巧合通过、spring 路径全滤空）。
- pilot 终态实证：1.3 五簇（4 根因+A5 派生）、1.4 确定性候选 ID、1.5b 16 假设、2.1 全 confirmed、2.2 19→17 V 文件（E44 近邻合并）、3.2 终态 gate 收敛至 6 个纯 pilot 范围 FAIL（未分析批次覆盖方程）、验收召回 1/2 零污染。

## v0.11.4 - run-19 pilot 回写（opencode 端到端就绪）

- 新 run-toolkit 四脚本（contracts/run-toolkit/）：classify_trivial.py（注释误报确定性预筛，保守判据）/ fastlane.py（主代理确认清单机械落盘）/ verify_batch.py（批级机械校验：表头/行数/verdict/五段/引用存在性+行号/边闭合/推导链 CP，与 gate 同口径）/ close_batch.py（scratch 合并+账本回填+图重投影+快照/看板/批进度，verify 全绿方可 close）。
- wu-analyzer-prompt：反序列化判定标准（网络入口 candidate / defaultReadObject+应用可配置字段 blocked(budget:deserialization-entry-unverified) / NotSerializableException 守卫才 disproved / import·类·方法声明 disproved）；unconfirmed 语义落 blocked（分片 verdict 三值封闭）；scratch 文件协议（write 整写本 WU 三文件，禁 bash 追加禁共享文件，批末主代理合并）；source='-' 未实体化源语义（reachable 可用 '-'）；CP 从派发映射取；段内禁竖线/字段禁 TAB/完整相对路径。
- candidate-discovery SKILL：9c-run19 部署加固节（快车道两段式=确定性分类+主代理逐行确认；拒绝清单 28 类真安全 sink 禁批量模板；部件拆分 sink>6；批闭包 verify→close 铁律；批级 gate 策略=批范围 verify + 终态统一 gate --subtask 1.2；救援循环 send_message 续跑）。
- 依据：docs/research/116-run19-pilot-validation.md（spring 50 批/3219 sink 实测：3058 disproved/18 candidate/15 blocked）。

## v0.11.3 - run-19 spring 实战修复（doc 100 §4 判据升级）

- 枚举锚定(类集合) 日志口径 bug：零命中类名推导双写 SINK- 前缀（'SINK-' + 'SINK-CLEARTEXT'），日志口径零命中全部漏算；且 PATTERN_UNAVAILABLE（本语言无模式）类不计零命中，导致 32 类误报缺失。修复：类名直接取日志文件名 + 两种标记均计零命中（枚举输出即封闭，不依赖 agent 转写 zero_hit_classes.tsv）。回归测试：fixture 删 zero_hit_classes.tsv 两类 + logs 标记两口径，枚举锚定仍 0。
- 扫雷信息级联三方程（信息板格式/信息板结论隔离/级联覆盖）+ gate 执行痕迹（gate_run_log）已在 09f99e3 落地，本条目为 run-19 首轮实战修复记录。

## E 编号登记表（v0.11.1 G-05/G-06 补）

- gate 方程以 self.add() 名称为唯一权威，E 编号仅历史记号；E1-E59 非连续：**E15 已删**（CVE 召回移包外闭卷验收）、**E24 漏校验**（合并守恒，v0.11.0 已以「合并守恒」方程补回）、**E29/E30 预留未用**（从未定义，git 历史确认）、**E31 已并入 finding 文件名格式+V文件完整性、E34 已并入 WU 派发记录**。
- 协议文件禁止裸 E 编号引用（tests 断言）；历史文档中的 E31/E34 引用按本表解读。

## v0.10.1 - 图实体化（doc 99：账本=真相，图=投影）

- 显式图文件 knowledge_graph/nodes.json（6 类节点：sink/source/file/checkpoint/candidate/finding，id 带类型前缀）+ edges.json（3 类边：flow/basis/derived），对齐 GenCPT 图文件思路、换确定性投影画笔（LLM 禁止写图）。
- 新脚本 contracts/build_graph.py：账本 → 图确定性投影（零语义判断）；--check 独立对账形式。wu_decompose.py 初始化即投影（图先于分析存在）。
- gate-1.py 新增 E56-E59：图节点投影完整性（gate 独立重算）/图边投影完整性/图投影确定性（防手改与陈旧，自愈重投影）/图边端点存在（GenCPT 悬空边教训）；gate 每次跑自动重投影。E12 产物存在性加 knowledge_graph 两文件；g1/g3/1.2 stage/subtask 映射更新。
- 剪枝/扫雷图可见：类级剪枝 → 节点 status=pruned + pruned_by/pruned_reason（scope 自然拼接规则：S2 scope=sink_type、S3 scope=sink_type-via-fn、S1 scope=SOURCE-{entry_type}）；flow 边 direction 随 WU 翻转；graph_snapshot.tsv 加 graph_nodes/graph_edges 计数列。
- pruning_ledger.tsv 扩为 7 列（operator/criterion/scope/evidence/judged_by/timestamp/a2_verified），class-pruner-prompt 同步；basis 边只对 backward/forward/terminal 行建（fix_presence 的 CVE 锚点非图节点），call_edges.tsv 保持导航辅助表不入图。
- 黄金夹具更新（pruning_ledger 7 列 + graph_snapshot 10 列 + knowledge_graph golden），expected-gate.txt 重新生成（60 行）；E56-E59 对抗测试（手改图/删节点/悬空边）全部被 gate 抓住。

## v0.4.0

- 验证权外置：Gate-1 由宿主执行 contracts/gate-1.py（E1-E24：闭合/覆盖/audit/四相等/failed/schema/引用可解析/证据唯一性/档位诚实/推导链/时序/WU/假设锚点+上限），判定由脚本输出生成；LLM 禁止执行 gate、禁止写 gate_record、禁止自报 gate_result（五轮自证失败的架构性修复）。
- 慢速诚实：禁批量闭合、废除浅扫中间态、每 sink 一行独立结论 + file:line 证据；audit_log 一行一观察、先落盘后引用（E21 时序检查）；账本新增 concluded_at 列。
- A5 发散轮：独立上下文红队假设生成器（≤20 条带锚点假设 → 追加检查点走同一流水线，E23/E24）。
- A2 独立验证 agent：四门 V0-V3 语义复核 + 内置对抗任务；gate_summary = 脚本输出 + A2 复核合成。
- 缺失检查 sink 类（语言特性派生两段识别式，与 CVE 无关）；cve-index 退出运行依赖（闭卷）；E15 删除。
- 验收：tests/acceptance/acceptance.py 闭卷对账（污染检查/有效召回/漏报）；锚点集移至包外 tests/golden/large-targets.md；48 号 §5.1 五条校准。
- schema 固化：列名 ASCII（sort_order）、candidates 16 列、machine-fields 9 字段（E16）；跨平台七规约维持。
- 黄金夹具升级：24 项预期数字表 + fixture-src 真实源码树 + SELFTEST 模式。

## v0.3.9

- Gate-1 升级为 E1-E16 十六项对账（§4c 一体执行块）：新增 E10 全终态理由封闭、E11 候选 ID 反查、E12 产物存在性、E13 信号级禁入、E14 引用闭包、E15 CVE 覆盖、E16 对抗表存在；E4 改 audit 双向覆盖、E5 加 confirmed 阈值（E5t）、E6 去真空（文件缺失/行数/登记三查）。
- 对账块双轨：POSIX 权威块 + PowerShell 翻译件；黄金夹具自检（tests/golden/gate-fixture/ + expected-gate.txt）前置；unverified_accounting 降级路径关闭；判定栏禁止手写。
- 全终态理由封闭枚举（disproved/blocked 前缀封闭，废除 structural_assessment:/light_scan_assessment: 等批量贴标）。
- candidates.tsv 固定 16 列强 schema（lifecycle_state/verdict/三 ref 顶层列）；machine-fields 9 字段（+confidence/evidence_grade/runtime_tier）。
- 负数 sink：knowledge/entries/cve-index.tsv（5 个 Tomcat 9.0.35 锚点种子）+ fix-presence 检查点 + machine-coverage.tsv 投影（E15 闭包）。
- 簇结论强制「攻击模式对抗表」；验证新增配置越界关卡（默认配置可达性 + CVSS 前置一致）。
- audit_log.tsv 升级为逐检查点证据账本；machine-coverage.tsv 新产物；verification-summary.md 单一文件强制。
- 跨平台七规约（UTF-8 无 BOM/LF/正斜杠相对路径/UTF-8 字节序排序/UTC/hash 规范化/CR 容忍）+ 会话内相对路径。
- 测试 71 项全绿（含对账块黄金夹具执行断言 + run-4 反例断言）。
本日志采用追加式记录。废弃字段和枚举只标注状态，不从契约中物理删除。

## v0.3.8 - 2026-08-14（四路终审修复轮）

> 依据：四路只读终审（协议一致性/知识层一致性/机制完备性/测试文档一致性）合并清单，共 3 P0 + 20 余 P1 + 20 余 P2，全部修复或如实登记。

- P0 修复：一体块四相等退化两相等（E5 补 E5c confirmed 计数与 E5d 分区表链接行，判定改四者相等）；等式1 no-op（E1 改查未检查字面值）；4b 机械闭合取错列（cut 第2列 + 替换为真正可执行 awk 块）。
- P1 修复：一体块 FAIL 追加缺口精确清单命令（head -100 导出未闭合 ID 集）；gate_result 非法值改 rework；等式6 补逐条列入报告备选；candidates.tsv 与 verification-summary.md 命名全库统一；audit_log.tsv 生产者与列定义；file_inventory 列名与 type 值统一；账本冻结字段名对齐；evidence_chain 幽灵字段消除；三记录闭包字段入表与写权限；lifecycle_state 枚举登记；deprecated 字段改非必填；契约版本号更新；置信度 0.7 档统一；对账命令表头统一；PlateauDetector 冲突分句删除；human_question_budget 提问计数器落地。
- P2 修复：编号顺延、gate_record 五列、五产物名、org-graph 引用、历史编号映射提示、废弃指针、模板相对路径、反引号残留。
- 知识层：ecosystem_mapped 假覆盖 24 分片 complete 改 partial；信号级分类落地（7 UVS 标信号级）；source-reconciliation/validated/生态映射 169 披露补全；CSRF stale 引用；KBATCH-002 标题对齐。
- 文档与图集：28/34 号补权威接替横幅；SKILL/README 补 36 号；29 号补修复轮记录；37 号出处修正；CHANGELOG 合并重复 v0.2.1；图集 19 页升 v0.3.7 并补一体块/聚簇/PlateauDetector。
- 测试：新增 10 项终审断言，60/60 全绿。

## v0.3.7 - 2026-08-14（最优架构落地，设计 36 号）

> 依据：docs/research/36-gensource-optimal-architecture.md。综合五参照系（shell-detector/codex-security/GenCPT/SourceCPT/vuln_agent）深挖后的最优架构：漏斗五层，四大问题机制解。

- 缺口精确清单 + PlateauDetector：FAIL 等式必须输出精确缺口清单（检查点/簇/候选 ID 列表）写入 gate_record rework 段；rework 只补缺失不重做已完成；连续两轮缺口集合无变化 → 停滞 → partial/blocked 停（GenCPT 机制）。
- subagent 显式 handoff 契约：每个 WU prompt 必带五要素（分配定义/上游产物绝对路径/技能文件路径/输出分片路径/反偷懒约束段），禁止隐式继承主会话上下文；父代理回收核对分片完整（codex 机制）。
- 原子写纪律：TSV/YAML/JSON 状态与账本更新一律 temp+mv 原子替换（GenCPT atomic_write 机制）。
- 单一候选账本冻结规则 + 三记录闭包：candidates.tsv discovery 字段冻结、下游只增列禁止回喂；每候选三记录（discovery 簇结论引用 cluster_ref/validation 引用/report 投影引用）缺一即对账失败（codex 三收据机制改造）。
- 置信度推导阶梯：confidence 从验证方法机械推导（静态 0.3+/0.5+、测试命中 0.7+、调试器/接口 0.8+、ASan 0.9+、崩溃 PoC 1.0），禁止从漏洞类型可怕程度推导（codex 阶梯改造）。
- 测试：新增 5 项，50/50 全绿。

## v0.3.6 - 2026-08-14（结构修复：让绕过不可行/没必要）

> 动机：三跑证明纯文本规则会被执行者合理化绕过；本轮做两个结构修复——把大量终态闭合变成机械操作（消除绕过的动机），把 Gate-1 变成不可拆散的一体执行块（消除绕过的可能）。

- 文件终态机械闭合：prefilter-rules 新增"机械闭合命令"——binary/纯文档且无 sink 命中且无入口特征的文件由 awk 机械标 not_applicable（prefilter_no_exec:），只有其余文件需 LLM 浅扫；从机制上消灭"文件浅扫未完成"类缺口。
- Gate-1 一体执行块：host-reconciliation-commands 新增第4c节——九项检查（七等式+反伪闭合+簇产物存在）打包为一段不可拆散的 shell 块，判定由命令输出自动生成写入 gate_record，禁止手写判定栏；任何 FAIL 即 rework，重跑本块覆盖更新。
- quality-gates 引用一体执行块为 Gate-1 唯一执行方式。
- 测试：新增 2 项，45/45 全绿。

## v0.3.5 - 2026-08-14（Tomcat 9.0.35 三跑修复轮）

> 依据：docs/research/35-tomcat-9035-run3-analysis.md。三跑确认 v0.3.2-v0.3.4 机制大部分生效（gate_record 七条全录、gate_summary 写回、四相等、配置上下文、clusters 目录），但等式判定栏再次被 pass_with_gaps 通过硬门（14560 未检查却 pass），且账本零闭合导致三跑产出漂移（11/33/53 条，CVE 锚点 0/4 vs 二跑 3/4）——稳定性与闭合是同一问题。

- 等式判定栏值封死：gate_record 判定栏只允许 成立/FAIL；pass_with_gaps 禁止作为等式判定值；"规模限制/partial/部分完成"禁止作为等式通过理由（预算只缩深度不删范围，浅扫全量与簇覆盖无规模豁免）。
- FAIL 强制 rework 循环：硬等式 FAIL → rework_rounds+1 → 补完范围 → 重跑全部七条 → 覆盖更新 gate_record；上限内未收敛 → blocked+部分报告，禁止 completed；rework_rounds=0 且 gate_record 有 FAIL = 协议违规。
- 报告完成硬门前置：report-delivery 写 completed 前核对 gate_record（七条全在、判定栏无 pass_with_gaps/FAIL、gate_summary 非 null、rework_rounds 有记录），不满足只能部分报告。
- 测试：新增 2 项，43/43 全绿。

## v0.3.4 - 2026-08-14（端到端完整机制落地，设计 34 号）

> 依据：docs/research/34-e2e-complete-mechanism-design.md（理论完备版）。停止边跑边补，先设计完整机制再实施：候选不遗漏三层防漏、候选全生命周期覆盖、逐漏洞详情每节就地落盘、五层对账链。

- 就地落盘字段：candidate-finding.md 增补 hop_snippet（深扫每跳 ±3 行代码+关键行标记，报告禁止重读源码补片段）、root_cause_summary、cvss_breakdown（八分量逐项解释）、exploit_scenario、remediation、lifecycle_state（created/verified/rated/reported 四态，无孤儿约束）。
- 生产时刻映射表：finding-template.md 增加 8 节 × 生产阶段 × 上游字段的唯一权威映射；报告阶段零新产出。
- 8 节投影对账：report-delivery 生成每份 findings/V{N}.md 前逐节核对上游字段存在；缺上游字段的 finding 不得生成，返回字段所有者补产。
- 五层对账链：quality-gates.md 增加 L0 清单冻结/L1 检查点派生/L2 簇覆盖/L3 验证覆盖/L4 报告投影 五层闭合表；host-reconciliation-commands 补 L2/L3 命令（簇结论可解析、candidate_id 四处集合一致）。
- 深扫就地落盘：candidate-discovery 的深扫每跳强制带 hop_snippet 与 semantic_transitions。
- 测试：新增 4 项，41/41 全绿。

## v0.3.3 - 2026-08-14（Tomcat 9.0.35 二跑修复轮）

> 依据：docs/research/33-tomcat-9035-run2-analysis.md。二跑确认 v0.3.2 的四相等/逐漏洞详情/信号降噪/配置上下文/HTTP2-WS 信号全部生效（CVE 锚点 Recall 3/4，反向锚点干净），但暴露两个新 P0：批量 not_applicable 伪闭合、gate_record 不完整且 FAIL 未触发 rework。

- 终态理由封闭枚举：backward/forward 检查点的 not_applicable 只允许 false_rule_hit:/disproved_safe:/cluster_conclusion: 三类可证明安全理由；禁止 "prefilter/no pattern/no high-confidence pattern" 等"没看"理由落 sink/source 检查点；"没看"只能留未检查或 blocked（check-unit-ledger-template）。
- 等式7 反伪闭合检查：新增 awk 命令核对 backward/forward 的 not_applicable 理由合法性与理由分布；clusters/ 目录必须存在且非空（host-reconciliation-commands）。
- gate_record 生命周期硬门：任一等式 FAIL → rework → 重跑全部七条并覆盖更新 gate_record.md；残留 FAIL 行或缺等式行禁止写 gate_result、禁止 completed；gate_summary 必须写回 run-state（null 即违反）（quality-gates）。
- 聚簇产物强制：clusters/{cluster_id}.md 每簇一个结论文件；backward/forward 的 cluster_conclusion 理由必须引用簇结论；未聚簇的 sink/source 检查点不得落任何终态——无簇结论的批量 not_applicable 是伪闭合（candidate-discovery）。
- 测试：新增 3 项（理由封闭枚举/gate 生命周期/簇产物强制），37/37 全绿。

## v0.3.2 - 2026-08-14（Tomcat 9.0.35 首跑修复轮）

> 依据：docs/research/31-tomcat-9035-run-analysis.md。修复首跑暴露的三个 P0（检查点零闭合、findings 详情零产出、深扫选模块）与相关 P1/P2。

- Gate 客观化：新增 gate_record.md 强制产物（七等式逐条命令+输出+判定落盘；缺文件=Gate 未执行）；硬门失败不得用 pass_with_gaps 掩盖（等式1/7 失败只能 rework/blocked）；等式5 升级为四相等（confirmed 数 == V{N}.md 数 == machine-fields 条数 == 分区表链接行数），machine-fields 必须覆盖全部 confirmed（含 Medium/Low/Ignore），禁止只写 Critical/High 子集。
- 检查点两级聚类闭合：深扫按 sink_type×symbol 聚簇执行（每簇一个深扫 WU：代表性实例完整链 + 簇内结构一致性核对），检查点按簇落终态禁止留未检查；簇级硬门（每 sink 类型至少一簇回溯、每 source 类型至少一簇前向）；新增聚簇命令（host-reconciliation-commands §7c）。
- sink 信号分级：SENSITIVE-EXPOSE/LOGGING/AUTHN-BYPASS/BRUTE-FORCE/OBSERVABLE-DIFF/STATE-CONCURRENT/MEM-INDEX 类降为信号级（不逐条进 sink_inventory），避免 5 万+ 检查点假账本。
- 配置上下文纳入验证：FALSE-rules 规则8 增加部署配置上下文强制核查（web.xml security-constraint/RemoteAddr 限制/默认配置开关），未核查配置的"无认证"候选不得 confirmed；verification-and-rating 的 Guard 评估同步强制。
- 确定性命令失败必须阻塞：对账/枚举/计数命令报错不得静默继续（重试一次仍失败即 blocked 并记录）。
- sink 信号补全：SINK-H2-FLOW（HTTP/2 流控/帧大小，CVE-2020-11996 类）与 SINK-WS-FRAME（WebSocket 帧载荷长度，CVE-2020-13935 类）。
- 测试：新增 6 项实跑修复断言，34/34 全绿。

## v0.3.1 - 2026-08-13（v0.3.0 深审修复轮）

> 三路只读深审（协议层/报告链路与稳定性/知识层与设计一致性）共报 5 P0 + 27 P1 + 21 P2，本轮全部修复或如实登记。

- 枚举收敛：conservative_assume_and_proceed 改回已登记值（confirmation_policy=conservative_continue + user_confirmed=conservative_assumption_applied）；删除 run-state 的 graph_cursor/proposed_transition/last_transition/exit_evidence_checklist；孤儿枚举（lifecycle_change_kind/lifecycle_trigger_kind/check_unit_basis_type）标 deprecated；新增 symbol_kind。
- 稳定性补全：run_fingerprint 口径唯一确定为 6 字段（candidate_id/location/sink_type/severity/root_cause_group_id/verdict）读 findings/machine-fields.json（report-delivery 新增第三产物）；stability_check 双跑隔离（run-1/run-2 独立 session 目录）；run-state 新增 model_host_label 与 stability_check 字段。
- 确定性 ID fallback：多 source/多 sink 取最小排序序；无 sink 候选取文件终态检查点序 + hash(file:line)。
- 报告链路：cross_boundary_path 逐跳结构、semantic_transitions、created_at/updated_at、impact_description、control_assessment.location 补齐；稳定键唯一化为 candidate_id；等式5/6 命令精确化（分区表锚点计数、failed 逐条核对）；等式2/3 按 direction 过滤；等式7 改名账本零残留。
- 知识层：FALSE-rules 规则1 增加多态反序列化硬例外（Jackson enableDefaultTyping/Fastjson autoType 不忽略）；CSRF 双 UVS 残余 6 文件清理（SRC-CWE 346/940/1385 改映射、语义文件标 superseded）；batch-ledger 补 002/004/006；sinks 信号修正（prepareStatement 移除、Python subprocess 补全、Go json.Unmarshal 移除、Go SSRF 补 NewRequest）；语言覆盖诚实标注 5/15。
- 图集：workgraph/full-logic 的 P0→P1 边标签修正（七等式属阶段1 出口）；gates.html 删除超纲硬门。
- 测试加固：七等式逐条、ID fallback、双跑隔离与 machine-fields、CSRF 台账行、batch-ledger 等断言补强；28/28 全绿。

## v0.3.0 - 2026-08-13（检测引擎重构，不兼容语义变更）

> 设计权威：docs/research/28-detection-engine-design.md；实施计划：docs/research/29-detection-engine-plan.md；动机与参照系：docs/research/27-detection-focused-redesign.md。

- 主序列改为 3 步 + 双产物报告：阶段0 客观枚举 → 阶段1 候选全量发现 → 阶段2 验证与定级 → 阶段3 报告交付（findings/V{N}.md 逐漏洞详情 + report.md 汇总索引）；exploit-proof / remediation-guidance 降为伴生按需（默认并入 finding 内小节）；lifecycle-governance 仅增量模式激活。
- 全自动红线：禁止中途进度汇报式提问；威胁语境改"展示假设 + conservative_assume_and_proceed 非阻塞"；整个 run 至多一次人工提问（shared/human-in-the-loop.md 重写）。
- 找全三环：三份冻结清单（file/sink/source inventory，LC_ALL=C sort、对账常数 wc -l 动态推导）；检查点从冻结清单派生（每 sink 一回溯点、每 source 一前向点、每文件一终态点，禁止自由少规划）；Gate-1 改七条对账等式（由宿主 shell 执行，见 contracts/host-reconciliation-commands.md，不再 LLM 自报）；预筛规则新增 shared/prefilter-rules.md（只分流不排除 + 5% 抽样复核）。
- 找准：新增证据分级 evidence_grade（direct/indirect/unknown，结论强度不得超过最弱一环）；新增 knowledge/FALSE-rules.md（8 类命中即忽略，最高优先级）；三态 confirmed/refuted/unconfirmed 对齐 SUSPECTED 语义；E1/E2 重型独立复核删除，改为轻量第二意见 + High/Critical 可选对称反转。
- 稳定：candidate_id 改确定性派生 C-{sink_seq}-{source_seq}-{sig8}（冻结清单排序序号 + hash 前 8 位，不用时间戳/发现顺序）；run_fingerprint = hash(排序后机器字段集合)；stability_check=true 双跑自检产出 stability-diff.md；分片按 shard 序号排序串行汇聚。
- 规模：批式流水线（预筛 0 模型 → 浅扫 cheap → 深扫 strong）；每子代理 ≤30w 行、每批 ≤30 任务、并发默认 5；预算只缩深扫深度不删范围；progress.json 五态 + step_progress 立即更新；压缩恢复从 remaining 续跑；删除三级锚定分类。
- 状态收敛：run_status 四值（initialized 废弃）；WU 状态改由分片文件存在性判定（work_unit_status 枚举废弃）；检查点终态改 check_point_status（candidate/disproved/blocked/not_applicable，check_unit_status 枚举废弃）；删除 wu_trigger_evaluation 四布尔。
- 知识层 P0 修复：CSRF 双 UVS 统一（ADJ-SRC-CWE-352 与 missing-origin-validation 裁决一致）；coverage 矩阵 0na 损坏值修复；KBATCH 台账重建；LLM01 年份修正；sinks/entries 双轨索引补全（首版）。
- 图集：docs/architecture-diagrams 按 v0.3.0 重绘，verify 脚本 PASS；随协议入库维护。
- 测试：tests/test_runtime_graph_protocol.py 重写为 v0.3.0 断言（28 项）；tests/golden/ 新增 dvpwa-ground-truth.md（冒烟）与 large-targets.md（大项目 CVE 锚定验证语料清单）。
- 指标口径：Recall/Precision/稳定性一律以大项目（十万~百万行、CVE 锚定集）实测；小靶场只冒烟不声称指标。

## v0.2.1 - 2026-08-09

- 基于DVPWA实跑失败样本新增53项可重复协议回归，覆盖Graph transition、WU强制触发、CU执行前冻结、独立复核分片、compaction锚定、run-state单文档、零输入、部分报告、修复应用、知识快照和跨WU汇聚。
- WU revision变化改为冻结旧WU并由新ID替代，保留`supersedes`/`superseded_by`；旧revision不得原地修改。
- 零候选也必须执行candidate-discovery Gate-2；独立复核发现`new_candidate_signal`时必须返回#3创建候选、补CU并重新过Gate。
- 新增run级授权范围、知识快照、Graph游标、拟议/已提交transition、WU评估完整历史和单YAML文档保护。
- 跨WU汇聚改为独立聚合产物，不修改输入WU原始边；候选通过`cross_boundary_path_ref`引用完整路径。
- 非交互保守继续使用`conservative_assumption_applied`，不再把`blocked_pending_user_input`同时当作继续状态。
- 三类知识索引修正为真实计数并增加`index_version`；同一run固定知识read-set，索引/覆盖冲突阻塞而非误报无知识。
- 修复完成语义要求`patch_application.applied=true`、before/after revision不同、验证绑定after revision且绕过复核通过。

- 将能力档案子字段统一为`capability_status`并引用集中枚举（含`degraded`）；补齐`runtime_verification`、`resume_mode`、`gate_decision`、`execution_fallback`、`manifest_status`、`source_status`及边界事实固定值集。
- 行业来源Manifest改用`source_status`；三类知识索引补齐版本、基于索引行的真实计数和遗漏正式条目，当前计数为vuln 148、attack 120、fix 141。
- 机械重算语义能力coverage汇总，修正并发/异常生态状态及所有分片重复的`complete`列表头；历史Phase来源统一声明不作为GenSource运行路由。
- 为candidate、verification、PoC和remediation产物增加统一stage envelope；零输入使用`input_count=0`与`records=[]`，禁止合成ID。
- 将验证方法迁移为`verification_methods[]`分段证据；收紧fixed补丁的before/after revision及独立复核绑定。
- 冻结run确认策略、组件与包含/排除范围，登记边界、控制、知识查阅和生命周期封闭枚举。
- 增加知识session read-set、索引版本/真实计数、报告完成硬门和候选计数公式。
- 将多WU跨边界汇聚提升为独立`cross_boundary_aggregate`正式产物，统一使用`cross_boundary_aggregate_ref`，绑定run/revision/输入WU/边界事实版本，并要求聚合边以`source_edge_ref`追溯冻结输入边。
- 收紧WU与Work Graph硬门：适用WU必须提供可解析边界事实，多WU必须提供聚合引用；所有节点出口显式组合`stage_result`与`gate_result`，零候选及无活跃finding路径仍须通过适用Gate。

## v0.2.0 - 2026-08-09

> 版本号口径说明：v1.0.0 是设计里程碑版本号，记录 contracts 层从 Schema/validator 方案转向纯 Markdown 轻量契约的设计决策；contracts 契约自身的语义版本号从 v0.1 起步，v0.2.0 是契约首次迭代。两者是不同维度的版本号，不存在降级关系。

- 新增Graph执行第一批硬门：`WU强制触发门`要求每个能力entry记录`wu_trigger_evaluation`，多机制/批次、任意subagent、compaction恢复或执行中新范围任一成立即强制Manifest，并绑定冻结`authorized_scope`。
- WU revision变化改为supersession：旧WU冻结，使用新ID绑定新revision，并保留`supersedes`/`superseded_by`双向谱系，禁止原地修改旧revision。
- CU账本新增执行前规划冻结证据、规划时间线、revision、快照和冻结后新增披露；终态CU必须先在冻结快照以planned存在，新增范围须补CU并重过Gate。
- `run-state.md`新增`single_document_guard`、`graph_cursor`和`last_transition`；规定单一YAML mapping、禁止重复键、整文件替换、严格解析和失败时保留旧可信版本。`compaction_detected`恢复后的首次持久化动作强制full anchor。
- Work Graph新增`new_candidate_signal`返工路由和`exit_evidence_checklist`；E1/E2/Gate只能写challenge gap，由#3创建candidate、补CU并重过Gate。零候选也必须通过Gate-2。
- E1/E2新增独立`review_artifact_ref`分片及输入/身份核对，禁止预填和reviewer直接修改主产物；Gate可复用同一已核对复核记录，不复制伪独立记录。
- 字段所有权表补充run-state核心字段、transition、Gate、WU/CU、`cross_boundary_path`和复核分片所有权；跨WU汇聚写独立汇聚结果，不改WU原始事实。
- 阻塞阶段统一写`stage_result=partial`并由`run_status=blocked`/`gate_result=blocked`表达阻塞；修正非法`stage_result=blocked`措辞。
- 新增run级知识快照契约、显式零输入原因、部分报告上下文、补丁应用证据和报告完成硬阻塞条件；全部Skill迁移剩余的裸`status`输出措辞。
- 审查收紧：transition采用`proposed_transition`核验后原子提交`last_transition`；WU entry评估冻结并以事件历史触发重评估；run-state登记知识快照；复核引用不替代E1/E2完整结论结构；WU原始边冻结，汇聚方改写独立汇聚产物。

- 新增 [`work-unit-boundary-facts.md`](data-structures/work-unit-boundary-facts.md)：定义 WU 分片产出的边界事实结构（inputs/outputs、Source/Sink/Guard/Sanitizer/Encoder 引用、call_edges、field_mappings、storage_edges、transport_edges、unresolved_connections、evidence、confidence），覆盖函数/方法/接口/继承/回调/DI/反射/动态分发/生成代码/DTO/序列化/数据库/缓存/文件/对象存储/MQ/事件/RPC/GraphQL/WebSocket/多仓服务契约等跨边界传播载体。
- 新增 [`../shared/cross-boundary-analysis.md`](../shared/cross-boundary-analysis.md)：跨 WU 边界汇聚规则——核对 WU 身份→按稳定符号/字段/存储位置/契约连接→DB/缓存/文件建立写入到读取的二阶边→MQ/RPC 建立生产者到消费者边→未解析连接保留为缺口而非"不存在"。
- WU Manifest 新增 `boundary_facts_ref` 字段，指向该 WU 分片产出的边界事实文件。
- `field-ownership-table.md` 新增 Work Unit 边界事实字段写权限段，明确边界事实各字段的唯一写入方和只读方。
- `attack-surface-map.md` 的 `surface_instances`/`entry_instances`/`source_instances`/`sink_instances`/`propagation_instances`/`control_instances` 新增 `symbol`、`component`、`contract`、`data_shape`、`storage_ref` 可选子字段，供跨 WU 汇聚按稳定符号连接。
- `candidate-finding.md` 新增 `cross_boundary_path` 字段（#3 段），记录候选的完整跨 WU 路径——每跳含 from_symbol、to_symbol、edge_kind、from_wu_id、to_wu_id、storage_ref（若二阶边）、evidence_refs。
- `lifecycle-ledger.md` 新增增量产物记录字段（`baseline_revision`/`current_revision`/`change_manifest`/`staleness_triggers`/`recheck_scope`/`reuse_scope`/`skip_scope`）和 `finding_fingerprint` v1 算法定稿（由 unified_semantic/invariant/entry/sink/path_edges/trust_boundary/asset 组成，不含文件路径和行号）。
- `work-graph.md` 新增增量触发规则：Source 变化向下游扩展；Sink 变化反查调用者；新调用者/路由使未修改函数重新可达时必须重查。
- Gate-1 新增跨边界完整性检查：WU 缺边界事实或关键跨边界未尝试连接时 rework。
- Gate-2 新增跨 WU 路径抽查：检查跨 WU 路径是否完整、二阶边和传输边是否覆盖。
- 统一产物名为 `threat-context.md` 和 `attack-surface-map.md`；`run-state.md` 只引用已有产物，不复制内容。
- README 明确当前是实跑版本，不声称 benchmark/Recall/Precision/稳定性/竞品/生产验收。

- 新增九个互不重叠、各自独立的状态/结果枚举：`run_status`（运行级生命周期，新增`initialized`/`running`两态，填补此前"运行尚未产生实质内容"与"运行正在进行中"无合法值可用的空白）、`stage_result`（阶段自身完成程度，仅`completed`/`partial`/`not_applicable`）、`gate_result`（Gate-1/Gate-2判定结果）、`work_unit_status`（单个Work Unit执行状态）、`check_unit_status`（候选发现阶段规划出的单个检查单元终态）、`run_mode`（全量/增量运行模式，必须用户显式指定）、`evidence_mode`（单段PoC/验证证据的执行/推导模式）、`evidence_composition`（一份完整PoC记录多段证据组合后的整体状态，含预留的`mixed`）、`checklist_applicability`（候选专属检查清单本次是否适用）。
- 明确禁止继续新增无命名空间的通用 `status`/`mode` 字段来表达上述任一维度：整次运行状态只能写 `run_status`；单个阶段/能力的完成程度只能写 `stage_result`；Gate判定只能写 `gate_result`；Work Unit执行状态只能写 `work_unit_status`；检查单元终态只能写 `check_unit_status`；运行模式只能写 `run_mode`。四个曾被合并进旧`status`/`mode`字段的维度（运行状态、阶段结果、Gate结果、WU状态）不得相互替代或合并回一个通用字段。
- 将六份数据结构契约（`attack-surface-map.md`、`candidate-finding.md`、`external-tool-signals.md`、`knowledge-base-entry.md`、`lifecycle-ledger.md`、`threat-context.md`）与 `run-state-template.md`、`shared/state-model.md` 中原表达"当前产物/运行完成程度"的通用 `status` 字段迁移为对应的 `stage_result`/`run_status`；旧枚举 `status`（`completed`/`partial`/`interrupted`）标注 `[deprecated since v0.2.0]`，物理保留供尚未迁移的历史消费方参考，不再是新产物的写入目标。
- `run-state-template.md` 的字段键本身由裸 `mode` 重命名为 `run_mode`，与同名枚举 [`run_mode`](enum-registry.md#run_mode) 保持字段名和枚举名一致（对齐 `status`→`run_status` 的迁移方式），并重申取值必须由用户显式指定、不允许隐含默认值。
- 历史已生成的产物文件（含其中记录的旧`status`取值和旧契约`version`）不做强制迁移，不因本次升级被批量重写。
- `gensource/skills/*/SKILL.md` 及 `gensource/SKILL.md` 消费方尚未随本次改动迁移字段名，仍引用旧的通用 `status`/`mode` 提法；其迁移计划在后续任务中处理，属已知待办而非本次遗漏。
- ⚠ 值集冲突升级标注：`gensource/skills/scope-and-context/SKILL.md` 第84行附近仍写 `status=interrupted`，而新 `stage_result` 枚举已不含 `interrupted` 值——这是值集冲突（不仅是命名差异）。在后续任务修改该 SKILL 前，任何执行者若读取该文件，应以 `enum-registry.md` 的 `stage_result` 值集为准，不应写入 `interrupted` 到阶段字段。
- `gensource/contracts/work-unit-manifest-template.md`的裸`status`字段（当前枚举注册表已将其列为`work_unit_status`的权威语义来源）尚未在本次改动中重命名，将在后续处理Work Unit身份与结构的任务中一并迁移为`work_unit_status`；当前保留是已知待办，不是本次遗漏。（✅ 已完成，见下方追加记录）
- 新增[`check-unit-ledger-template.md`](check-unit-ledger-template.md)模板：定义候选发现阶段的检查单元规划与终态对账结构，作为Gate-1集合闭合的最小可审计单位。
- Gate-1闭合模型从"攻击面×三机制笛卡尔积"改为"检查单元disposition集合闭合"（`planned_check_unit_ids == terminal_check_unit_ids`），消除三种机制检查单位粒度不同却强制共享同一笛卡尔积的假设错误。
- 新增`check_unit_basis_type`枚举（10个值，按三机制分组：`pattern_driven` 3个、`business_logic` 3个、`lateral_diff` 4个），登记各机制独立规划依据。
- 明确Gate-1只提供计划内闭合证据（已规划检查单元全部取得终态），不能证明计划覆盖全部未知面；未知面遗漏由Gate-2独立查漏负责。
- `independent_review_e1e2`结构拆为E1（强制）+E2（条件触发）：E1对每个candidate强制执行独立第二意见复核，不得以强动态证据替代；E2按触发值决定是否执行双向独立重建。
- 新增`e2_trigger_reason`枚举（7个触发值：`high_or_critical`、`high_cost_refutation`、`review_disagreement`、`evidence_conflict`、`material_cross_boundary_gap`、`static_only_high_impact`、`independence_degraded`），登记至枚举注册表，权威语义以`verification-and-rating/SKILL.md`为准。
- 新增`execution_budget`字段块（`node_attempt`/`gate_rework_count`/`plateau_detected`等），记录节点执行次数、Gate返工次数和plateau检测状态，受循环预算约束。
- Gate-1/Gate-2职责重新划分：完整性检查（三机制真实执行、是否因显眼漏洞提前停止）迁移到Gate-1完整性范畴；语义可信（漏候选、no_candidate结论可信度、验证模式真实性等）归Gate-2独立语义挑战。
- `pass_with_gaps`边界收紧：明确允许条件（缺口位于非关键范围、准确定位、具有resume_entry、不使已有finding证据失真、报告明确披露）与禁止条件（关键入口/Sink未完成、High/Critical candidate未完成、证据链冲突未解决、硬性独立复核未完成），禁止条件优先。
- Plateau定义修正：连续两次执行后缺口集合未缩小或结论/证据/剩余范围无实质变化时触发plateau，显式标注`partial`并停止当前循环；plateau是停止条件而非第三套循环。
- 三级重新锚定机制定稿：完整重新锚定（全量重建上下文）、WU重新锚定（单个Work Unit重新派发）、轻量核对（汇聚前身份检查），三者按粒度递减、开销递减分层复用已有产物。
- Work Unit身份字段定稿：`run_id`、`source_path`、`source_revision`、`upstream_artifacts`、`estimated_workload`、`remaining_scope`均为WU创建时定义的结构字段，其中`run_id`/`source_path`/`source_revision`/`upstream_artifacts`为一次性写入的冻结值，此后不可变——源码revision或上游产物版本变化时不更新冻结值，而是通过汇聚前身份检查发现不一致后重做受影响WU。
- Work Unit `attempt_history`定为只追加结构：每项记录attempt编号、结果、产物引用和失败原因，不得改写、重排或删除已有条目；失败接管复用原WU ID并递增`attempt`，不得删除失败记录后新建看似首次执行的WU。
- `work-unit-manifest-template.md`裸`status`字段正式迁移为`work_unit_status`（任务1遗留待办已完成），取值引用枚举注册表`work_unit_status`枚举，禁止使用裸`status`字段名。
- Work Graph伴生能力路由定稿：明确能力间依赖以Work Unit为调度单位路由，伴生能力的派发与汇聚纳入WU Manifest管理。
- 部分报告路由定稿：明确`stage_result=partial`时报告层仍投影已完成部分并披露缺口，不阻塞整体交付。
- 零输入终态所有权定稿：明确无输入或无匹配产物的能力仍须写明终态（如`not_applicable`），由该能力唯一写权限方负责，不得留空或由下游代写。
- Gate退出条件定位定稿：明确Gate-1/Gate-2的退出条件锚定在对应检查单元/WU终态集合闭合，不以中间产物存在性替代终态判定。
- `field-ownership.md`收窄为原则层：具体字段级写权限实例化定稿由`field-ownership-table.md`承载，`field-ownership.md`仅保留通用原则与违规处理框架。
- `capability`字段重命名为`manifest_capability`（消歧）：与`run-state.md`的`current_capability`（运行时当前锚定能力）区分，`manifest_capability`指WU Manifest声明的能力归属。
- `run_mode`在`SKILL.md`中改为必填输入：用户必须显式选择`full`或`incremental`，缺失时`run_status=blocked`并询问用户，不静默默认`full`；此前`SKILL.md`输入示例中的`mode: full`静默默认值已删除。
- 新增[`capability-profile-template.md`](capability-profile-template.md)：记录运行开始时的宿主能力探测结果，覆盖9类可探测能力项 + 1类降级能力汇总清单（file_read/artifact_write/deterministic_commands/independent_context/network/compiler_test_runtime/sast_sca_debuggers/resources/dynamic_validation_authorization/degraded_capabilities），每项使用`available`/`unavailable`/`unknown`状态并附探测依据；含探测纪律（只允许只读操作，禁止把安装/构建/启动当作探测；network未主动探测时写`unknown`不写`unavailable`）。
- `deployment-environment.md`能力探测原则具体化：引用`capability-profile-template.md`，明确小型任务无subagent时顺序执行、大型任务无法维持范围/上下文/独立性时partial或blocked、Gate-2缺独立上下文标记independence_degraded、无法动态验证时只用inferred证据；新增动态执行安全门（8项核对：authorization/isolated_copy/network/credentials/data/side_effects/timeout/cleanup，任一关键项false或unknown时decision=denied、fallback=static_only）；删除原"能力探测具体方式留待确定"的占位声明。
- `run-state-template.md`新增`capability_profile_ref`（引用能力档案路径）、`workload_budget`（最小工作量预算：estimated_workload/scale/completed_scope_refs/remaining_scope_refs/gate_rework_count/arbitration_round_count/user_limits）、`dynamic_execution_summary`（授权状态与安全门决策摘要）三个字段。
- `scale-cost-management.md`成本预算章节收紧：预算只控制执行深度和人工决策，不能静默删除范围/检查单元/candidate；禁止逐步骤Token计量和费用遥测；禁止额外稳定性运行；预算耗尽时暂停并提供延长预算/接受非关键缺口/缩小scope三种选择；关键范围不得通过预算理由降级为pass_with_gaps。
- `SKILL.md`新增威胁语境确认步骤：展示关键业务假设并请求用户确认，使用`user_confirmed`枚举记录；无法等待时采用保守假设并记录`user_confirmed=blocked_pending_user_input`及影响范围，不得伪造确认。
- `SKILL.md`新增"默认目标只读"约束：目标源码树默认只读，PoC/补丁/测试写入目标树外独立输出目录或工作副本；修改工作副本需动态执行授权，修改真实目标树需单独明确且针对本次动作的授权，历史授权不得自动复用。
- `candidate-finding.md`新增`write_boundary`字段（#3段）：记录target_source_path/working_copy_path/output_path/target_tree_modified/authorization_ref，`target_tree_modified`初始为false。
- `candidate-finding.md` #6段PoC字段级`mode`替换为`evidence_composition`+`evidence_segments`结构：`evidence_segments`每段含segment_id/claim/evidence_mode/evidence_refs/execution_scope/limitations；组合规则：全部executed→executed，全部inferred→inferred，混合→mixed；只有executed段要求reexecution_check，inferred段禁止携带伪执行结果。`enum-registry.md`的`mode`枚举保留为`verification_mode`和`evidence_mode`的共享值集定义。
- `candidate-finding.md` `candidate_specific_checklist`从`array<object>`（0-5项）改为显式`object`（applicability/reason/items）：`applicable`时按candidate实际语义列出全部必要检查项不设数量上限，`not_applicable`时reason必须非空且items为空数组；禁止真空通过（items=[]且applicability=applicable不合法）。
- `remediation-guidance/SKILL.md`输入"目标代码库读写访问"改为"目标代码库只读、外部工作副本可写"：修复阶段可写补丁内容和工作副本结果，但不得改写candidate发现字段、验证终态或代替独立复核写通过。
- `adversarial-target-defense.md`删除"构建/依赖清单风险...本次不设计...属于待决的范围问题清单"过时声明，改为引用`deployment-environment.md`动态执行安全门。
- `lifecycle-governance/SKILL.md`增量模式记录定稿：`run_mode=incremental`时必须记录baseline/current revision、变化清单、陈旧触发、扩展范围、复用披露和跳过披露；周期性全量复审用户未提供策略时标记缺口，不静默采用固定天数。

## v1.0.0 - 2026-08-08

- 建立方案 C（分层混合）：以 Markdown 字段参考表作为日常 LLM 读写的主权威源，以单一 JSON Schema 服务最终封存和外部互操作。
- 建立全局 [枚举注册表](enum-registry.md)，统一跨阶段机器判定值，并保留 `priority` 与 `evidence_tag` 两个有明确语义理由的格式例外。
- 固化 candidate/finding 身份规则：`candidate_id` 创建后不可变；`finding_id` 直接复用 `candidate_id`，不生成新 ID。2026-08-08集成测试进一步纠正原“confirmed即finding”的过宽边界：`confirmed`仅是验证终态，只有有活攻击面且非`informational`者进入finding/#9；`ignore`作为有活路径的政策忽略finding仍进入#9显式处置。
- 将实际运行中用于死代码等“已确认事实但无存活攻击面”场景的 `informational` 纳入 `final_severity`。此前 `verification-and-rating` 的输出清单仅列出 critical/high/medium/low，未覆盖该已发生行为，本版本以契约吸收并统一该差异。
- 发布按阶段实例化的 [字段写权限表](field-ownership-table.md)，明确证据仅追加、报告只投影和外部状态不得反写上游等边界。
- 定稿报告覆盖结果的聚合优先级、`user_confirmed` 三态流程枚举，以及仅用于跨扫描身份匹配的 `finding_fingerprint`。
- 定稿 `knowledge_entry_status` 三态枚举、按条目关联的 `knowledge_entry_states` 及 `knowledge_evidence_history` 仅追加写权限。
- 落地六份 Markdown 数据结构契约：威胁语境、攻击面地图、candidate/finding 累积结构、生命周期台账、知识库条目与外部工具信号。
- 统一六份结构的七列表头、共享 `status`/`version`/`resume_context` 约束、嵌套项最小结构和条件必填规则。
- 收紧外部工具伴生能力语义：未触发 A-D 场景时不产出记录，不再将空场景实体化为机器状态；工单写入结果明确记录本次同意状态、执行状态及成功/失败条件字段。
- 为 `refuted` candidate 增加开放扩展的 `refutation_category` 结构，强制携带非空 `snake_case` 分类标识和真实反证引用。
- 补全生命周期抑制边界：首次进入抑制态必须人工授权，历史抑制态仅在置信度与非 critical 条件同时满足时可自动维持，并持续接受定期人工抽样复核。
- 将反证分类收回 `verification_verdict` 复合结构，保持 #4/#5 实际 14 项字段，并统一 `confidence_score` 自动抑制门槛为 `&gt;8.5/10`（等价于 &gt;85%）。
- 收紧嵌套数组元素、知识决策引用、知识范围、外部来源引用、tracker 状态组合与生命周期复验结果的结构约束。
- 补齐 #16 调用输入与 #8 证据角色写权限，消除 `evidence_chain` 幽灵字段，并将 `confidence_score` 固化为完整对象。
- 明确 #16 两阶段决策：先生成提议，再由人工提交决定供 #16 只读消费；仅批准决定触发知识库写入。
- 完成 9 个 SKILL 向 v1.0.0 契约迁移：统一权威结构引用、共享状态字段、英文机器枚举、字段写权限及伴生能力触发边界。
- 纠正impact×likelihood确定性矩阵：`unknown`按矩阵保守映射且不得反写`verification_verdict`；任一轴为`ignore`均映射为`ignore`，完整保留报告但不产生`priority`。`informational`仅表示无存活攻击面的代码卫生记录，不进入矩阵，可兼容映射为`P3`；CVSS输出收敛为完整向量字符串。
- 明确知识演进产物原样携带`candidate_pool`、`knowledge_base_snapshot`、`installation_scope`、`human_decision`及调用方提供的`deprecation_signal`，不授予#16输入字段写权限。
- 质量修复：删除#3低风险证伪跳过路径，统一`confirmed`为经证据确认的代码事实/风险主张；无活攻击面事实固定为`informational`代码卫生记录并排除PoC、主动漏洞修复和活跃漏洞台账。
- 在`impact_rating`内增加high×high条件必填的`critical_criteria_met:boolean`，true确定映射`critical`、false映射`high`，保持矩阵逐格权威。
- 收紧#7：所有修复及结构提案记录必须有`final_result`，未获人工决定使用`needs_human_decision`；`inherently_safe`仅允许新证据触发回退#4并改判`refuted`后的历史投影。
- 固化#8同Surface整组唯一Outcome聚合优先级，禁止真实candidate被`not_applicable`覆盖；报告始终用`candidate_id`，仅只读显示#9已存在的`finding_id`别名。
- 修正首次生命周期处置、`coverage_diff.decreased/warning`、完整`candidate_pool`内部筛选、tracker请求即记录及`generation_basis`语言/框架与产品文档核实映射。
- 明确`confirmed+informational`是已确认代码卫生candidate/code-hygiene item：报告完整展示但不称finding、无`finding_id`、不进入#9；完整历史改由candidate累积结构与#4/#5产物持久化，并在复扫时重新进入#3/#4。
- 将六份数据结构中的全部固定局部机器值上收至`enum-registry.md`，并声明其为全部固定机器枚举的唯一权威源；开放扩展标识保持开放。
- 将完整5x5 impact x likelihood严重度矩阵集中到`enum-registry.md`，verification-and-rating与candidate-discovery仅引用该矩阵。
- 将#16 `candidate_pool`改为`{source_audit_id, candidate}`包装元素；已确认、知识未匹配和验证证据引用改为从既有candidate与知识快照派生，不向candidate加入临时字段。
- 为#7修复验证增加`verification_mode`，严格区分`executed`动态重跑与`inferred`静态证据链走查；静态确认可支持`final_result=fixed`，但生命周期只能先进入`fixed_unverified`，真实动态复验后才可`fixed_verified`。
- 更新32号设计规格状态：9个SKILL迁移已完成，剩余未完成项仅为Schema与validator（任务4）及其后的最终全局核查（任务5）。
- 方向纠正：33号规格取消Schema与Python validator，不实施自研程序；contracts冻结为`v0.1`轻量自然语言参考，并新增宿主Agent直接维护的`run-state.md`协议。
- 收口固定枚举权威：新增`generation_basis_kind`与`exposure_scope`，登记生命周期条件子集和报告证据角色适用范围，并将SKILL输出表中的局部完整值清单改为注册表引用；执行分支所需的具体值条件保持不变。
- 质量审查修复：场景B改为#18仅提交带来源主张，#3创建candidate后由#4验证，`external_claim_verification`只保存两阶段引用；场景D允许在本次显式同意下消费既有版本化`export_artifact`，不存在时联合触发C后再写入。
- 将三类硬抑制确定映射为`likelihood_rating.rating=ignore`，impact仍按事实评估，矩阵结果完整报告、无priority并进入#9；保留跨信任边界例外。
- 从`remediation_mode`删除`local_remediation_preferred`；B2聚类不成立改由相关`tactical_patch`记录的`hardening_cluster_basis.structural_hardening_recommended=false`表达，不创建空修复记录、提案内容或独立结果。

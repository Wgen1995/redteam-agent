# 设计语料全景与对齐审计（corpus-audit-design）

**审计日期**：2026-10-16 · **审计人**：语料审计子代理（只读 + 仅写本报告）
**任务**：全面研读探隐全部设计语料，输出设计决策全景、三环飞轮对位、定稿后实建对账（遵从/深化/违背）、未决问题清单。

## 0 审计范围与纪律

**实读文件**（全部通读，未抽样）：

| 类别 | 文件 |
|---|---|
| 设计谱系主链 | `docs/design/2026-09-20-tanyin-bprime-fusion.md`（401 行）→ `2026-09-21-tanyin-v2-design.md`（733 行，唯一权威稿）→ `2026-09-22-vuln-agent-engine.md`（350 行）→ `2026-09-22-gencpt-suite.md`（170 行） |
| 定稿后修订链 | `2026-09-24-completeness-recon-knowledge-evolution.md` / `fd-report-card-spec.md` / `finding-stream-priority.md` / `graph-driven-ops.md` / `endpoint-dict-v2.md` / `engine-fusion-architecture.md` / `tanyin-target-form.md` / `tanyin-product-v1.md` / `ui-design-v1.md` / `architecture-map-v3.md`（蓝图双胎之 md 侧） |
| 评审与修正 | `2026-09-27-expert-review-consolidated.md`（六专家） / `2026-09-29-eight-expert-review-b10.md`（八视角） / `direction-amendment-1.md`（方向修正案 1 号） / `BLUEPRINT-RECON.md`（蓝图对账表） |
| 批次探知台账 | b3/b4/b5/b6/b7/b8 六份 discovery-notes（G-1..G-49 全量） |
| 宪法与账本 | `docs/USER-CHARTER.md`（33 条用户预期账本） / `docs/PRINCIPLES.md`（开发原则单源账本） |
| SPEC 宪法 | `panorama/tanyin-architecture-v3.html`（1037 行；v2 全量保留 + ⑫建造实况带 + ⑬对账带） |
| 实建对账补充 | `docs/HANDOFF.md`（1492 行，头尾与批次收口行）、`cli/`（工具面）、`cli/webui/`、`knowledge/`（含 SOURCES.tsv）、`contracts/`（15 件清单）、`docs/research/2026-09-24-vulnclaw-analysis.md` |

**纪律**：①一切结论带文档名+节号；②语料没写就说「语料未载」；③「三环飞轮（真值结算/知识蒸馏/度量对照）」一词在全部设计语料中**零命中**（grep 全 docs/ 无「三环」；同判见 `docs/research/corpus-audit-research.md` §术语注记）——它是本次审计的归纳框架，非语料术语，下文②按此框架映射并逐环给语料实词佐证；④实建对账（③）以设计语料+HANDOFF+蓝图双胎+仓内文件存在性为据，未逐行读实现代码，代码级断言一律标注证据层级。

**语料断层提示**：`docs/design/` 共 24 件 md（BLUEPRINT-RECON「设计档对账」节计数），本审计通读 22 件 + html/、imported/ 目录清点；`imported/`（TanYin/gencpt/vuln-agent 三仓 vendored）按 P3 建议「迁 .research/」未计入设计谱系。

---

## ① 设计决策全景树

> 每条决策：**落点文档+节** · 原文短引 ·（如后续被修订，注明修订链）。树按任务书七域组织：形态/宿主/引擎/账本/执法/验收/飞轮。

### A. 形态域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| A1 | **三面一体宪法**：skill 主体+薄 CLI 工具箱+档位化 hook/egress | v2-design §0.1 ADR-P3 | 「宪法：『skill 主体 + 薄 CLI 工具箱 + 档位化 hook/egress』……形态不是纯零代码：确定性运算与机械执法进 CLI，语义判断留在 skill」 | 源头=bprime-fusion 裁决#1/§5.1「宪法重述而非维持原状」（对 TanYin 纯 SKILL 零代码宪法的唯一推翻项）；后续 product-v1「生态位」升格为「自持编排器」 |
| A2 | **「零代码」可执行口径**=零第三方运行时依赖 | v2-design §1 D1.1 | 「『零代码』口径=『零第三方运行时依赖、复制即装』」 | 语言律固化于 tanyin-target-form §3「服务端：Python 3.9+ 纯标准库，永久」 |
| A3 | **五层六边形架构** | v2-design §3.1/§3.2 | 「三件咬合（skill 主体 / 薄 CLI 工具箱 / 档位化 hook+egress）」；§3.3「四支柱不变（Graph / Loop / Harness / Context）」 | 实建期重绘为「两扇门+练兵场→看门狗→账本判据→AI 指挥→度量飞轮→分发与引擎总线」五层（architecture-map-v3 标题行与§二） |
| A4 | **产品定位=AI 自动化渗透，审计是地基** | USER-CHARTER §A1/A2/A4 | 「最大的目标是 AI 自动化渗透；只有审计的话平台价值不大」「全/深/打得进」=验收标准 | 落档 product-v1「定位」：「审计不是产品身份，是自主性的地基」；修正案 D「架构=B（渗透内环）+审计模式开关」 |
| A5 | **产品形态 D4：clone 即用→tanyin serve→口令登录→全程浏览器** | product-v1「产品形态（D4）」 | 「部署(clone 即用零依赖)→启动(tanyin serve 单命令)→登录(操作员口令)→全程浏览器……CLI 退居引擎层」 | 源头 USER-CHARTER §A3（用户批过 D4）；截至语料末页状态=🔴「登录没做、serve 单命令未收口、浏览器端没按钮——方向盘批补」 |
| A6 | **四面一体：武器-观察-控制-引擎** | tanyin-target-form §1（2026-10-11 批准） | 「观察面 tanyin-web（v0.9 · 只读投影）」「武器面（现脊柱，形态永不改）」「控制面（v0.9.5 · 薄，默认不建，单独审批后建）」「引擎面（渐进自持 · 直连 API）」 | ui-design-v1 定九页骨架与 12 级灰阶；USER-CHARTER §D17「产品=你能按到什么」最高优先 |
| A7 | **五条形态法** | tanyin-target-form §2 | 「零依赖律（武器）· 投影律（观察面只读）· 单写入路径律（控制面只能走 CLI 门）· 渐进自持律（引擎按触发器生长）· 可换宿主律（战士）」 | 未修订 |
| A8 | **语言律**：Python 3.9+ stdlib 永久；前端 HTML+CSS+SVG+原生 JS 零框架零构建 | tanyin-target-form §3 | 「服务端 import 只来自 stdlib——加 CI 自检」「禁 npm/禁构建产物入库/禁 CDN 引用」 | 修正案 B（product-v1）：Go 边车三触发器（白盒解析>10min/并发战士>50/客户机无 python），「账本链留 Python 不重写」 |
| A9 | **薄总控五不 vs 宿主五不**（词典重命名消歧） | bprime-fusion §5.4#1 → v2-design §2.5 词典口径 | 「薄总控五不（不写代码/不发请求/不判重/不算哈希/不渲染图）与宿主五不（不要求宿主改/不规定内部/不干涉调度/不假设能力/不锁死宿主）」 | 未修订 |

### B. 宿主域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| B1 | **五宿主安装矩阵，首批实测三宿主** | v2-design §0.1 ADR-P2、§10.2 | 「安装矩阵五宿主全量；首批实测 DSH / opencode / codex（有环境可 CI），walcode / CodeBuddy 定位为『装得上+披露未验证』」 | 实况（architecture-map-v3 §五/§v0.8）：「分发面: opencode✅ codex🟡 Claude🔮 DSH插件v0.3.0✅」；walcode/CodeBuddy=G-38 待实测回传（b6 台账一节） |
| B2 | **载体迁移：PowerShell 5.1→python3 ≥3.9 标准库薄 CLI** | v2-design §0.2 决策#10、§0.1 P3 形态依据 | 「PS 5.1 是 Windows 基底、与五宿主冲突；python3 标准库零第三方依赖、五宿主直跑」 | 裁决源=bprime-fusion 裁决#10/§5.3「账本命令签名原样保留，只换实现载体」；语言律由 target-form §3 收口 |
| B3 | **交战区在安装树外** | v2-design §0.3 #5、§3.4 | 「交战区在安装树外：$TANYIN_HOME/engagements/<goal-id>/……git pull/升级不冲突」 | 未修订；PRINCIPLES「环境事实」补充「持久数据在 ~/.tanyin/（战）与 git（工程）」 |
| B4 | **战士宿主=opencode 现役，可换宿主律** | product-v1「生态位」 | 「战士: opencode 现役（13 战基线）; 不做任何 harness 插件（0.91）; 不用任何框架」 | target-form §2 可换宿主律；architecture-map-v3 §一门A「载体 opencode ✅ / Claude Code 🔮 / codex 🟡」；`opencode-lastgood-v0.9c` 标签=USER-CHARTER §D21 |
| B5 | **DSH 二开=只做遥控器不做底盘** | tanyin-target-form §6 关联决策存档 | 「DSH 二开=只做遥控器不做底盘（2026-10-11 对话，本 spec §1 可选项）」 | 实建=platform/dsh-plugin-tanyin v0.3.0（architecture-map-v3 §五「DSH插件v0.3.0✅」） |

### C. 引擎域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| C1 | **引擎契约双轴**：统一提交 schema+manifest；引擎不直接写 13 表 | v2-design §6.1 | （D2 行）「引擎契约 §6；首批 web-blackbox + vuln_agent」；vuln-agent-engine §8：「本引擎产物（facts/findings/assets/edges）由适配器转 submission.json，引擎不直接写 13 表账本；总控命令重算 dedup_key 与铸 ID」 | contracts/07-submission.md、08-manifest.md 落地 |
| C2 | **首批引擎四件**：web-blackbox（SKILL 型）/vuln_agent（CLI 型适配器）/nuclei adopt/session-viz（projector 型） | v2-design §6.3-§6.5、§11 批次 4 | 「web-blackbox 四段+vuln-agent 适配器+nuclei adopt（模板钉 commit+验签）+session-viz」 | 实况（architecture-map-v3 §五）：「引擎总线: web黑盒✅ vuln-agent🟡 session-viz✅ / range v2🔮」 |
| C3 | **身份矩阵差分**：creds 一等实体+authz-diff 置格，不设独立表 | v2-design §0.1 ADR-P4③、§0.2 决策#9、§0.3 #1/#7、§6.6 | 「creds/sessions 实体建模=13 表：creds 单表双 kind（static-cred/session），sessions 不单设表」「复用 pair_group 差分机制落地」 | b4 G-20 差分对数上限 AUTHZ_DIFF_PAIR_CAP=24；b5 T19 intents 增 cred 物理绑定列（G-27 闭环）；护栏「差分默认仅对幂等读接口」（v2-design §6.6/R12） |
| C4 | **白盒双车道**（车道A 确定性解析器/车道B LLM 深审） | product-v1 修正案 A、修正案 D | 「车道A 确定性解析器（零 LLM）: OpenAPI/Swagger→endpoints……源码 pattern 扫描」「车道B LLM 深度审计（吸收 GenSift）……sink 卡逐卡五步证伪+盲验证」 | 修正案 D 定位：「源码是渗透循环的情报车道,不设独立环节」「覆盖不可谈判律继承……engine deferred=0 进 P4 收口判据」；endpoint-dict-v2=车道A 底座 |
| C5 | **引擎面渐进自持：judge 窄调用→循环长大→触发器吸收** | tanyin-target-form §1 引擎面、§6 | 「judge 窄调用(v0.8)→fusion 引擎循环长大→按触发器吸收战士职责；不做大爆炸重写」 | engine-fusion-architecture 为其设计稿，但 BLUEPRINT-RECON 判「§1-5 部分虚建（judge/llmpool 模块在但生产零接线,E1-F4）;§6 实为施工顺序而非循环层设计（E1-F7 勘误）」；direction-amendment-1 票③「接线四件: llmpool pick→ask→report 成环+池单写者化/judge_client 生产接线」=排队中 |
| C6 | **规划者=唯一写者，战士产 submissions** | direction-amendment-1 §四（E1 对账 b26） | 「v1.0b 常驻循环……规划者=唯一写者,战士产 submissions（契约既有答案）;派发 intent 级+战士长寿命带账恢复」 | v1.0b 未建（architecture-map-v3 §v0.9.7 前夜「排队: 画布段→方向盘批→v0.9.7 地基批」） |

### D. 账本域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| D1 | **TSV 13 表领域账本；timeline.tsv 兼任 journal 第一事实源** | v2-design §0.2 决策#2、§4.2（CB-1） | 「TSV 13 表领域账本……timeline.tsv 兼任 journal（第一事实源+可全量重建）；嵌套走『TSV 索引行 + 外置卡片』双轨」 | 13 表=goals/scope/intents/facts/findings/assets/edges/approvals/E-index/matrix/timeline/budget/creds（§4.3-§4.10 逐表）；实建沿用（HANDOFF 状态快照「批次 0 契约冻结：✅ contracts-v2（13 表/41 命令）」） |
| D2 | **哈希链防篡改** | PRINCIPLES「机制哲学」；v2-design §4.1/§4.10 | 「哈希链护体（改账=断链=可检）」；timeline 每行 prev_hash 链式（v2 §5.3 P6.0 哈希输入含全行） | 六专家评审「链哈希本体（esc 回环+prev 链）未破」正面确认 |
| D3 | **命令面 41 条（§0.3）/37 条（§5.3 标题）——定稿内部两说** | v2-design §0.3 #2 与 §5.3 | §0.3：「41 命令（§5.3；2026-09-23 终审并入九门断言专用四条）」；§5.3 标题与合计行：「命令集（37 条，签名批次 0 冻结）」「合计 18+12+6+1=37」 | **定稿自相矛盾未在任何评审中点名**（见④-1）；实建轨迹：b4 评审收尾 41→44 → v0.8 45 → v0.9d 49（architecture-map-v3 §v0.8/§v0.9d「命令面 48→49」） |
| D4 | **单写者+写前拒收+ID 铸造** | bprime-fusion §5.5 必修清单（TanYin A1）；v2-design §5.3 通用纪律 | 「写前拒收；查询输出摘要化……命令幂等；对外请求类前置 request-ticket」 | PRINCIPLES「记账律」+「边界律」（settle 只结算不改账）；b7 M4 冻结锚点裁决、b8 M2 supersede 命令面收口 |
| D5 | **Tier 0 恒在硬门：无授权只许读文档** | v2-design §5.2 补充语义 | 「P0『无授权只许读文档』由 Tier 0 硬门实现（无 goals 行时一切写命令 REJECT）」 | panorama v3 技术模式 Band「Tier 0 账本级（恒在，不可关）：写前拒收·scope 内联·deny-list 前置·ID 铸造·哈希链」 |
| D6 | **revert_cmd 分层登记** | v2-design §0.3 #4、§5.2 P6.0 | 「外部副作用操作（碰目标系统：发请求/落文件/改配置）必须登记 revert_cmd……纯账本状态变化免登记，其逆=追加新行」 | panorama v3「P6.0 副作用回滚账：无法回滚=标不可逆+人工高危审批」 |
| D7 | **矩阵五态+空格必须消灭或披露** | v2-design §5.2 P5 terminal-gate；architecture-map-v3 §四 | 「ledger-terminal-gate, expect: 矩阵无空格 | degraded 披露清单完备」（终态门禁） | gencpt-suite §10 对照：「五态标记闭环 [x][?][-][!][ ] 交付前 [ ] 必消灭——几乎逐字同构」；b7 M4 裁决「追加合法（P3 生长通路 G-2）钉死；terminal-gate 锚点断言改 freeze 时在场行」 |
| D8 | **受管重启护栏** | v2-design §5.2 补充语义 | 「重启计入预算、重启速率上限（1 次/N 分钟防递归 spawn）、timeline 记 managed-restart 事件、单活跃会话约束」 | b3 G-3/G-4 常量暂代（RESTART_RATE_MINUTES=10/RESTART_TOKEN_COST=2000）；G-4 定标遗留→契约 v3（b6 台账三节） |
| D9 | **工件即缓存幂等续跑** | v2-design §5.2 补充语义 | 「intent done 且 submissions/<intent-id>/submission.json 存在则重入跳过」 | panorama v3 断点四步第4步「不靠 AI 记得做过，靠『账本里已有那一行』——查账即知（幂等续跑）」 |

### E. 执法域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| E1 | **四层纵深分档执法** | v2-design §0.2 决策#4、§8.5；ADR-P3 | 「四层纵深分档（账本级→执行通道级→宿主 hook→egress 代理）+ canary 进 evals」；依据「Threatswarm fail-open 实洞证明纯 skill 层拦不住界外直连」（bprime-fusion 裁决#4） | panorama v3 技术模式四框：Tier 0 恒在/Tier 1 CLI 边界（铁律 7）/Tier 2 宿主拦截 fail-closed/Tier 3 egress 白名单四成分+金丝雀 |
| E2 | **canary 金丝雀进 evals** | v2-design 决策#4/ADR-P3、§10；R10 | 「canary 判定绑定『本交战进程凭证+时间窗』非裸 DNS 查询；误报进 evals 基线校准」 | 侦察侧姊妹机制=诱饵召回率（completeness-recon §1.2「测绘引擎的召回率=发现诱饵数/植入数——信息收集的『不漏』第一次变得可度量」） |
| E3 | **凭据治理：{{vault:cred-N}} 唯一占位符+全链路四关卡+withheld 降级不拒绝** | v2-design 决策#5、§8.4 | 「执行前/落盘前/上下文前/交付前四关卡全链路覆盖（DarkMoon 模式）」 | b7 C 系修复（vault XOR 无 nonce 等 High 项）；S1 信任根摘出（v0.9.6）继续深化 |
| E4 | **预算树三元组+$ 第四维默认关** | v2-design 决策#6、§8.7 | 「三元组树化（goal 根、intent 叶）+ 可选 $ 第四维默认关 + 假设排序公式并入先验分」 | budget.tsv 载体=§4.10（scope 列+dollars_delta 默认 0）；工具 tanyin-budgetctl（cli/ 在册；architecture-map-v3 §二「预算执法 ✅(v0.5a)」） |
| E5 | **铁律 5-7：执法不可绕过/默认档覆盖不可谈判/薄 CLI 边界** | v2-design §2.2-§2.4 | §2.2 标题「铁律 5：四层执法不可绕过、档位事实必须披露」；§2.3「铁律 6：默认档覆盖不可谈判」；§2.4「铁律 7：薄 CLI 边界定义」 | 「LLM 只调用不实现」「凡未给出命令的步骤不得执行」两条纪律全文有效（ADR-P3） |
| E6 | **执法五件 S1-S5（v0.9.6 执法面升权）** | direction-amendment-1 票②；architecture-map-v3 §v0.9.6 | 票②引言「不批则自主化=给被俘战士扩权」；S1-S5=「信任根摘出……egress 实挂……时戳防时间旅行……replay 授权窗+危险方法分类+次数帽+scope 单源……promote 信任源门」 | 实况（architecture-map-v3 §v0.9.6）：S1/S3/S5/S2/S4 全段落账「测试 1403→1479」；性质=对六专家评审 C2/C4/C5 反例与 E2 刀口的补强 |
| E7 | **照亮不击杀（LOGONLY-ALIVE）+防幻觉零分律** | PRINCIPLES「机制哲学」 | 「照亮不击杀（LOGONLY-ALIVE）；防幻觉零分律（无重放实证不计分）」 | architecture-map-v3 §二看门狗层「LOGONLY-ALIVE ✅」；§四计分铁律「烂帐=0 分（b25 的 54 发现只计 32 即此律）」 |
| E8 | **人工触点全场唯一（P5.5 签发）** | PRINCIPLES「机制哲学」；v2-design §5.2 P5.5 | 「★人工触点全场唯一（P5.5 签发）★；人类事项显式列出」 | panorama v3「P5.5 签发门：没签发=禁止导出交付物」；b8 M10 approvers.tsv 名录+approve 名录校验收口身份锚 |

### F. 验收域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| F1 | **三层验收体系** | v2-design §0.2 决策#8、§9；ADR-P4⑦ | 「三层：黄金夹具逐字节 → evals CI（含 token 效率）→ TSecBench 六域对齐」 | 实建：L1 金样 G-g1 50→54 面（b5/b6 HANDOFF 行）；L2 evals CI 门禁；L3 脚手架交付、全量对齐=发布前（b6 G-40） |
| F2 | **防幻觉零分律/发现计分四条件** | PRINCIPLES；architecture-map-v3 §四 | 「发现计分四条件=状态 active + 端点与资产对得上 + 证据卡重放已验证 + 信标词在卡——烂帐=0 分」 | b10 P2#1 深化批判：紫队信标=零摩擦，「recall 度量路径字典召回非漏洞利用确认」→「检出主通道改参数依赖行为差分……双轨公布 beacon 召回/行为差分召回」（在途） |
| F3 | **POC 四要素+独立重放门三态** | v2-design 决策#7、§4.9/§6.1；ADR-P4① | 「E-index 含 POC 四要素 + P4 独立重放门（三态）」；panorama v3「治『复现四要素只是口号』」 | b8 M12 链式重放 --chain 收口；b10 P2#4 重放 body 传递失真修复；EV 工件哈希 34/34=sha256(空串) 缺口（b10 P2#5）修复在途 |
| F4 | **FD 卡片九段+时间链自证** | fd-report-card-spec §一/§二 | 「一张卡片=一个漏洞的完整自证……落盘时序断言：evidence.captured_at < finding.added_at < report.issued_at——哈希链+timeline 可证『先有证据后有结论』」 | b4 G-25 Burp 粘贴格式边界→b6 T14 收口（burp_pasteable 四规则机检）；G-36 HTTP/2 真帧样本待 |
| F5 | **完备性三定律+分母就绪门四关** | completeness-recon §〇/§1.3 | 「模型驱动……漏=空间里的空格，可见可数可追」「matrix freeze 前必须过四关：①每资产来源数≥2……②诱饵召回率 100%……③A1-A8 各类非空……④外推资产已跑一轮图谱闭包」 | b3 G-13 诱饵召回率断言=批次 4 交付；HANDOFF 批次 4 行注记「G-2/G-12/G-13 在 b3 台账就地注记闭环」 |
| F6 | **双臂实验+McNemar+配对置换** | direction-amendment-1 §三（E4 吸收）；b10 P2#15 | 「实验设计吃下 E4 全部（GT-free 考场+三 sha256+战层配对置换 N≥4+post_auth 主指标……+死区 14 题零战成本归因先行）」 | 已有：architecture-map-v3 §四「双臂McNemar判决 ✅」；b10 #15 勘误「战报一律同子集口径；独立性分层声明」 |
| F7 | **评估口径诚实律（M09 基线/precision 并报）** | b10 P2#7；PRINCIPLES「诚实律」 | 「recall-only 无 precision/噪声面；M09 基线三重过时……以 G-r4 精度门后 0.56 重定标；并报 precision 代理指标」 | G-39 基线 v1=1.00(20/20) 冻结（b6）；基线 v2=靶场第二战（b8 移交清单） |

### G. 飞轮域

| # | 决策 | 定在哪 | 原文短引 | 演变 |
|---|---|---|---|---|
| G1 | **知识飞轮四机制+staging 审批** | v2-design §7（标题「飞轮四机制 + ingest-staging 审批 + CNPEN 82 入库」）；P6 沉淀门 | §5.2 P6：「脱敏提取（域名→CLIENT-NN……）→ 反向验证……零命中 → 用户审批 → 写入 knowledge（precedents/entities/graph.ndjson）→ lint 保鲜信号」 | 实建=b5 收口（HANDOFF 批次 5 行全绿）；BLUEPRINT-RECON「知识飞轮资产（已建成!差点被重新设计）」：15 目录/命令面 tanyin-knowledge promote 四门槛+approve 人审门 |
| G2 | **知识库 K1-K8 全集** | completeness-recon §二 | 「K1 方法论基准库……K8 靶场复盘库：每场仗结束的 retro……入库纪律不变：脱敏→机器检查→人工审→四门槛；K5-K8 同走飞轮」 | 实建 knowledge/ 目录在册（concepts/precedents/patterns/retros/checklists/staging/graph.ndjson/log.md）；K1 基线=k1-baseline.tsv（b5 G-24 裁决 A 落表人审冻结） |
| G3 | **触发器闭包+反漏三件套** | completeness-recon §3.1/§3.2 | 「触发器目录（封闭、可审计）……converge-check 增加『未消费事实=0 且触发器目录版本一致』断言」「周期复扫/收敛即停止+披露/复盘回流」 | b4 G-28 converge 结构性停机（#reachable-gaps/#unreachable-gaps 双清零）批 5 闭环；M6 端口/服务变更触发器=b8 T4 收口（TRIGGERS v2→v3） |
| G4 | **度量飞轮：评分器键控+金样钉测+复盘** | architecture-map-v3 §四（④ 度量与飞轮层） | 「评分器键控v8 / 金样钉测 G-r4→G-r41 / 套件RC=0 / 复盘RT-0001→0024 / 双臂McNemar判决 ✅」 | RT-0001 归因核验勘误=b10 P2#14（「战记归因未核即入册……register 流程增归因抽样核验步」在途） |
| G5 | **外部语料入库**：CNPEN 82+BugHunter/Threatswarm/CEP | v2-design §7.2、§11 批次 5 | 「staging/lint/四门槛/三元组/CLIENT-NN/graph.ndjson+CNPEN 82+外部语料（BugHunter/Threatswarm/CEP）入库+CVE 联网核验」 | b5 G-35 三源降级登记（KP-0007..0009 待补）；CNPEN 素材=KP-0001..0005 待补行；**VulnClaw 为定稿外新增语源**（见③-8） |
| G6 | **模式自进化同构参照** | gencpt-suite §4 机制④/§10 | 「insights 经 4 门槛+用户审批晋升永久模式写入 _learned/」；对照表「模式自进化 4 门槛+用户审批 ↔ 知识飞轮 staging 审批入库——同构（v2 多反向验证脱敏）」 | 参照物，非实现义务 |

---

## ② 「三环飞轮」在设计稿里的位置与完成度

> 术语注记：任务书「三环飞轮（真值结算/知识蒸馏/度量对照）」为审计框架，语料零命中（见 §0 纪律③）。三环在语料中的实词对应：**真值结算**=「结算器可复算/精度门/重放实证/GT 键形/基线冻结」；**知识蒸馏**=「飞轮/沉淀/staging/蒸馏/入库」；**度量对照**=「双臂/McNemar/配对置换/基线对照/同子集口径」。

### 环一：真值结算（战果以可复算真值落账，防止自欺）

**设计位置**：
- 宪法层：PRINCIPLES「协作节奏」：「对账式汇报：讲证据不讲故事；**战果=结算器可复算**」；「机制哲学」：「防幻觉零分律（无重放实证不计分）」。
- 定稿层：v2-design §0.2 决策#7（POC 四要素+重放门三态）、§5.2 P4（独立重放门断言 ledger-replay-summary）、§9（三层验收）。
- 细化层：fd-report-card-spec §二「时间链自证」（captured_at<added_at<issued_at）；architecture-map-v3 §四「计分铁律（精度门）」四条件。
- 实验层：tests/range 键形体系（b10 P2#6 键形 v3→v4 修正）与 G-39 基线冻结。

**完成度**：**高（已建+在修口径）**。证据：architecture-map-v3 §四「九门 ✅」「双臂McNemar判决 ✅」；十战基线在册（§一「0.70×3/0.66/0.64/0.62/0.57/0.46/0.41」）；G-39 基线 v1 冻结 20/20；b8 移交「靶场第二战（基线 v2）」未打。**已知缺口**（语料自认）：b10 P2#1 紫队信标零摩擦（82% 检出靠路径枚举+静态文案）→行为差分双轨改造在途；P2#5 EV 工件哈希空串放大 34 倍；P2#6 同键碰撞双计分→v4 修正待做。

### 环二：知识蒸馏（战例与外部语料脱敏入库，跨会话复利）

**设计位置**：
- 定稿层：v2-design §7（飞轮四机制+ingest-staging 审批）、§5.2 P6 沉淀门（脱敏→反向验证零命中→用户审批→入库→lint）。
- 细化层：completeness-recon §二 K1-K8 全集+「入库纪律不变：脱敏→机器检查→人工审→四门槛」；b5 G-29 知识页 ID 命名空间（九前缀自有表）。
- 修正层：BLUEPRINT-RECON「知识飞轮资产」节——「库: knowledge/ 15 目录……命令面: tanyin-knowledge（promote 四门槛+approve 人审门）+ tanyin-evals；已喂: PR-0005 飞轮回写/RT-0001 归因核验/b0d0bed 喂养战例」；**「v1.0 连接点（新提案仅此一条）: 规划者循环（v1.0b）把 knowledge/ 作检索源注入战士 brief——飞轮本体已建,缺的只是自主循环这双『腿』」**。
- 语源层：b5 移交清单「持续飞轮（内容生产，不再动代码）：VulnClaw 余 39 专题蒸馏（首批 8 页外）、CNPEN 素材五类缺补登记、BugHunter/Threatswarm/CEP 三源到位后补蒸馏——全走本批 staging 流水线（register→蒸馏→lint→approve→commit→export）」。

**完成度**：**机制全建、内容半满、循环未接**。机制：b5 收口全绿+双锚审批（G-33→b6 T2 硬门）+S5 promote 持钥签名门（v0.9.6）。内容：concepts 8 页+precedents 5 页+retros/checklists/staging 在库（knowledge/ 实勘+log.md 190 行，BLUEPRINT-RECON 计数）；VulnClaw 蒸馏 8/47 页、CNPEN/三源素材待补（SOURCES.tsv KP-0001..0005/KP-0007..0009 note=待补）。循环：v1.0b 规划者未建（direction-amendment-1 §四），检索注入=设计在册未实施。

### 环三：度量对照（同尺横比，防「带统计妆容的错尺」）

**设计位置**：
- 定稿层：v2-design §9.2（evals 指标集+token 效率一级指标，bprime-fusion §5.2 毒药面①的落点）、§9.3（TSecBench 六域对齐=发布前 L3，G-40）。
- 实建层：architecture-map-v3 §四「评分器键控v8/金样钉测 G-r4→G-r41/双臂McNemar判决 ✅」+ §一门C 靶场十战。
- 修正层：direction-amendment-1 §三吸收 E4：「战层配对置换 N≥4+GT-free 考场+post_auth 主指标+三 sha256——防『带统计妆容的错尺』」（panorama v3 ⑫建造实况带同文）；b10 P2#15 同子集口径勘误：「『独立战士 2.1 倍反超』=分母置换+知识继承+子集不可比三重混杂；同子集真对比=17/20(0.85) vs 14/20(0.70)=+21%」；P2#7 precision 并报。
- 键形层：b10 P2#6 键形 v4（同键多 GT 条强制一 finding 至多计一）。

**完成度**：**中高（判决器已建、尺子正在返修）**。双臂 McNemar 判决 ✅ 与 G-50/G-51 反自欺编制获八专家正面共识（b10「强项共识」节）；但 E4/b10 连续两轮指认度量效度问题（信标零摩擦/键形碰撞/口径混杂/precision 缺位），修正实验设计（配对置换 N≥4+死区 14 题归因）已冻结待执行；TSecBench L3=发布前义务未启动。

**三环总判**：语料把三环拆在三处落账——真值结算主要写在 PRINCIPLES+v2 §5.2/§9+FD 规格；知识蒸馏写在 v2 §7+completeness-recon+BLUEPRINT-RECON；度量对照写在 v2 §9+architecture-map-v3 §四+direction-amendment-1 §三+b10。**没有一份文档把三者合成为一个命名的「飞轮总图」**——最接近的合图是 architecture-map-v3 §二（④ 度量与飞轮层 与 战果沉淀/每战回流 两箭头）与 panorama v3 ⑤ P6 知识飞轮带；三环互相咬合的机制叙述（检出→蒸馏→下轮 brief→再对照）在语料中仅以 BLUEPRINT-RECON「v1.0 连接点」一句话预告，属于**设计在册、尚未闭环**。

---

## ③ 分歧与漂移表：2026-09-21 定稿 vs 实际建造

> 判级口径：**遵从**=按定稿建；**深化**=定稿未细载、按其精神扩展且经后续文档/契约通道追认；**违背**=与定稿条款冲突（含「先违背后修复」与「拟议待批」两亚型）。性质判定均给文档出处；实建证据以 HANDOFF/蓝图双胎/仓内文件为准。

| # | 事项 | 定稿怎么说（v2-design 及节） | 实建怎么样（证据） | 性质 |
|---|---|---|---|---|
| 1 | **命令面扩张 41→49** | §5.3「命令集（37 条，签名批次 0 冻结）」+§0.3「41 命令」（定稿自身两说，见④-1）；§11 批次 1「cli/tanyin-ledger 37 命令」 | HANDOFF 批次 4 评审收尾行「cli/README 计数 41→44×3+面数 50→51」；批 6「契约勘误 09（工具面 12→14：+#13 tanyin-evals+#14 tanyin-budgetctl）」；architecture-map-v3 §v0.8「命令面 45」→§v0.9d「命令面 48→49」 | **深化**——签名冻结纪律未破，扩面全走契约微版本勘误通道（b3「通道纪律」节；b7 M2 曾因「44 命令名冻结约束在册」延后至 b8 才开） |
| 2 | **13 表 vs 蓝图「八表」呈现** | §4.2「13 表全字段定义」（含 budget.tsv、creds.tsv） | architecture-map-v3 §四标题「八表（三组）」但实列 4+4+3=**11 表**（goals/scope/creds/approvals+assets/facts/intents/findings+timeline/edges/matrix）+「E-index.tsv+evidence/ 证据体系独立成卡」；budget.tsv 未出现在该节（工具 tanyin-budgetctl 在 cli/ 在册） | **深化中的文档漂移**——contracts-v2 仍冻 13 表（HANDOFF 快照行）；蓝图把 budget/E-index 移出「表」叙事改为工具+卡片体系呈现，标题「八表」与实列 11 行自相矛盾（见④-2），属蓝图侧呈现层漂移非账本 schema 违背 |
| 3 | **tanyin-runner 看门狗层** | 定稿只有「受管重启自动档护栏」（§5.2 补充语义：计入预算/速率上限/单活跃会话/managed-restart 事件）；无独立监督进程设计 | architecture-map-v3 §二「① 看门狗层 · tanyin-runner ✅：心跳30s/停滞击杀8min/断点续跑/完成判据=gate-status API/分级击杀(b10)/重启退避/战中指令注入/预算执法/LOGONLY-ALIVE/ask:human WAIT」；战例「b24 断网三度点火零账损 / b27 82 分钟无人看护 0.70」；仓内 cli/tanyin-runner 实存 | **深化**——把定稿一段护栏条款长成常驻五层结构第一层；「战术归 AI、判据归账本、保活归 Python——三层互不越权」（§二引言）为新增宪法性表述，未见违背项 |
| 4 | **webui 观察面九页** | **v2-design 全文无 GUI/浏览器/观察面条款**（grep 零命中——定稿未设此面，也未设禁止条款） | cli/webui/（server/sse/snapshot/projections/metrics+static）实存；architecture-map-v3 §v0.9d「观察面: 总览/活动/会话/热图/十边/证据/度量(+实验) 九页」；设计依据=target-form §1「观察面 tanyin-web（v0.9 · 只读投影）」+§2 投影律（2026-10-11 用户批准）+ui-design-v1 | **定稿外重大扩展，经后续用户批准追认**——相对 v2 是范围漂移（定稿沉默），相对 target-form/product-v1 D4 是遵从；且守「只读投影、永不做第二个写入者」（target-form §2 单写入路径律） |
| 5 | **控制面/方向盘五按钮** | 定稿沉默（同上） | target-form §1「控制面（v0.9.5 · 薄，默认不建，单独审批后建）」；USER-CHARTER §D17「方向盘批: 五按钮」🔴→🔵；HANDOFF 2026-10-16 下午「方向盘批计划已冻结」未执行 | **拟议待批**——单写入路径律为闸，未违背；产品侧用户账本判「零按钮=零产品」为最高优先催办 |
| 6 | **规划者/planner 与 llmpool/judge** | 定稿无规划者（总控=SKILL.md 战士自身+phases.yaml 引擎）；批次 7 可选项=烛龙接入 | product-v1「生态位」「双车道直连 API——①判据/规划者 judge_client+llmpool（已建）」；BLUEPRINT-RECON 判 engine-fusion「§1-5 部分虚建（judge/llmpool 模块在但生产零接线,E1-F4）」；direction-amendment-1 票③「接线四件」排队 v0.9.7；仓内 cli/ledger/llmpool.py/judge_client.py 模块实存（零接线判定采 BLUEPRINT-RECON） | **后续路线的遵从**——不违背 v2（v2 把编排权威放在账本+门，规划者仍走「唯一写者」律）；但 engine-fusion-architecture §6 已被 E1-F7 勘误为「施工顺序而非循环层设计」，引用该文档须按 BLUEPRINT-RECON 修正口径 |
| 7 | **执法五件 S1-S5（v0.9.6）** | §8.5 四层档位+§8.4 四关卡+决策#4 canary——Tier 0-3 框架 | architecture-map-v3 §v0.9.6：S1 信任根（warrior_env 白名单单源+密钥类 env 物理不可达）/S2 egress 实挂（runner 起内嵌代理强制 env+request-ticket 机械记账）/S3 执法钟链上锚/S4 replay 四门/S5 promote 持钥签名——「测试 1403→1479」 | **深化（含一次「违背→修复」史）**——六专家评审（2026-09-27）实测构造反例：C2 guard exec 可绕/C4 信任根=仓内测试钥/C5 签发绕 approvals（「执法集中在账本读侧/门禁面；写路径……仍是文字纪律」）；b7 整改+v0.9.6 升权后回到并超过定稿条款。违背期有诚实披露在案（PRINCIPLES「诚实律」），终态判遵从 |
| 8 | **VulnClaw 语料挖掘** | §7.2/§11 批次 5 外部语料清单=「CNPEN 82+外部语料（BugHunter/Threatswarm/CEP）」——**VulnClaw 不在定稿清单** | docs/research/2026-09-24-vulnclaw-analysis.md（712 文件深读，「服务对象：探隐 TanYin」自署）；SOURCES.tsv KP-0006（MIT，47 专题 skill 仓库级登记）；首批蒸馏 8 页（knowledge/concepts/CP-0001..0008+precedents/PR-0001/0002 均 source_id: KP-0006）；b5 移交「VulnClaw 批 6 三项登记（headless 退出码第 3 态/findings 双工件/报告内容过滤器）」 | **深化（定稿外新增语源，机制遵从）**——入库走同一条 staging 流水线（register→蒸馏→lint→approve→commit→export，b5 移交清单），四门槛纪律不变；对照「定稿清单内」三源反成降级待补（G-35），属清单漂移而非机制漂移 |
| 9 | **产品重定位：审计降为地基** | v2-design 定位=渗透测试 skill 体系（D1-D7），报告/审计为一等出口（§5.2 P5） | USER-CHARTER §A1「最大的目标是 AI 自动化渗透;只有审计的话平台价值不大」⚠️；product-v1「定位」：「审计不是产品身份，是自主性的地基」；修正案 D：「架构=B（渗透内环）+审计模式开关……翻案条件: 纯代码审计合同占比>30% 则审计模式升格一级入口」 | **方向修正（用户裁决级，非工程漂移）**——v2 的账本/九门/重放门全部保留为「敢让它打多快」的执法地基，报告管线未拆；判=高层宪法演进，v2 机制面未被推翻 |
| 10 | **九门+phases.yaml 引擎** | §5.2 九门全量+§5.1 状态机语义+决策#3「phases.yaml 承载形式、账本命令承载执法语义」 | architecture-map-v3 §四九门表 P0-P6 全 ✅；b3 G-1 工具面 10→11（tanyin-phases 独立载体）经契约 09 勘误收编；b7 M4 terminal-gate 冻结锚点裁决钉死 | **遵从**——门语义逐门落命令断言；「过门只能靠 gate 命令（带前置校验，嘴说无效）」（§四引言）兑现 |
| 11 | **黄金夹具字节级回归** | §9.1「L1 黄金夹具（确定性层：账本命令逐字节回归）」、§11 批次 1 出口「夹具字节级回归全绿」 | HANDOFF 批次 1-6 各行金样面 42→50→51→54 面 PASS 零漂移；b7「金样 54 面 PASS 零漂移……『金样零漂移为默认纪律』兑现」 | **遵从** |
| 12 | **evals 三层+TSecBench** | §9.2/§9.3；ADR-P4⑦「evals 三层验收含 TSecBench 对齐」 | L2 CI 门禁化+M01-M12 指标（contracts/15 在册）；L3=脚手架交付（b6 G-40「TSecBench 对齐脚手架已交付不阻塞 CI……去向=发布前 L3 全量对齐」） | **遵从（如实分级）**——L3 按定稿「发布前人工项」口径延后，非遗漏 |
| 13 | **安装矩阵五宿主** | §10.2/§10.3+ADR-P2；R8「walcode/CodeBuddy 无环境实测……默认保守披露 Tier 1」 | install/hooks 三宿主模板（dsh/opencode/codex）落库+安装器 step4 真挂载（b6 G-38 注记）；walcode/CodeBuddy guided 回传通道在册未回传；opencode 现役 13 战 | **遵从（首批实测义务部分完成）**——DSH 以插件形态实测（platform/dsh-plugin-tanyin v0.3.0）、codex 🟡 半成；walcode/CodeBuddy 按 R8 保守披露，升档条件在册 |
| 14 | **弱模型档位化** | §8.8+铁律 6「默认档覆盖不可谈判」；bprime-fusion §5.2③「安装自检扩展为『宿主×模型双档探测』，输出机制分档」 | b3 G-9「弱模型纪律遵循度只能 evals 检测……批次 6 evals 增弱模型遵循用例」；**后续语料未载兑现记录**（b4-b8 台账与 HANDOFF 未见弱模型用例行） | **遵从存疑（语料未载）**——档位表在契约（11-enforcement），遵循度用例是否落地无档可查，列④-16 |
| 15 | **预算树+token 效率** | §8.7 预算树；bprime-fusion §5.2「token 效率（每收敛一格的 token 成本）列为 evals 一级指标」 | tanyin-budgetctl 在册+预算执法 ✅(v0.5a)（architecture-map-v3 §二）；token 通道=b6 G-11/G-37：evals_token_eff 单源+M05 runner+首采 token-calibration.json（n=76/median=1.116），「系数回写遗留→契约 v3」 | **遵从（定标在途）**——G-4/G-37 两笔契约 v3 回注未销 |
| 16 | **DSH 插件 v0.3.0** | 定稿 DSH=五宿主之一（安装矩阵），无插件二开条款 | architecture-map-v3 §五「DSH插件v0.3.0✅」；target-form §6「DSH 二开=只做遥控器不做底盘」；仓内 platform/dsh-plugin-tanyin/（test/scripts/lib/skills） | **深化**——遥控器定位有 2026-10-11 用户批准存档；与 product-v1「不做任何 harness 插件（0.91）」不冲突（该条限战士宿主面，DSH 插件为分发/观察面） |
| 17 | **靶场与双臂实验超出定稿** | §9.4「授权靶场全流程+种 20 漏洞检出率」 | battle.py 四命令+十战基线+G-r 系列金样+G-50/G-51 双臂对照+McNemar 判决（architecture-map-v3 §一门C/§四）；b10 全份台账为其质量债 | **深化**——定稿只要求种 20 漏洞演练，实建长成度量飞轮主体；效度问题由 b10/E4 自我修正 |
| 18 | **sqlite3 投影层（拟议）** | §4 编码规范钉死 TSV 家族；决策#2「换 JSONL 不解决状态机/并发两病灶」 | direction-amendment-1 票③「sqlite3 投影层决策（呈用户）：推荐分层: TSV=真相层……sqlite3=投影索引层（治撕裂+查询+O(1)）」+§五待裁决三件 | **拟议待批（潜在违背候选）**——若批则为定稿载体的分层修订；未批前无实建，判定采「呈批中」 |
| 19 | **AI 指挥层=SKILL 战士（BRIEF/dict）** | §3.2 三件咬合+决策#1「skill 主体」；§11 批次 3「SKILL.md 路由器+phases.yaml 引擎+P3 演进循环」 | architecture-map-v3 §二「③ AI 指挥层 · 技能战士 ✅：SKILL.md 总控路由器/phases 详令/dict v3.14/BRIEF 30面战书(0.66来源)/侦察+重放子代理」；phases/P0-P6.0.md+TRIGGERS.md 仓内实存 | **遵从+深化**——BRIEF 战书与 dict v3.14 为定稿未细载的作战资产（endpoint-dict-v2 为其设计档） |
| 20 | **账本写路径原子性（C1 案）** | §4.1 编码规范+§12 R 册未列此险（定稿未预判进程内写撕裂） | 六专家评审 C1「write_tsv open(w) 原地截断，真实 SIGKILL 8/8 次静默丢史」→b7 整改方向①「C1 原子写+文件锁+真 SIGKILL 保真测试」→direction-amendment-1 票③「O(1) 追加写……实测 18µs/行线性劣化必须先治」排队 v0.9.7 | **违背→修复中**——定稿承诺「timeline 第一事实源+可全量重建」（决策#2），C1 证明该承诺在真实 kill 下不成立；修复在册未收口（票③排队），残余风险如实呈报 |

**漂移总判**：22+ 份设计语料与实建之间**未发现任何一处「静默违背」**——所有扩张走契约微版本/用户新批通道，所有缺陷经评审自曝后修复在册。最大漂移集中在两处：①**范围漂移**（webui/runner/planner 均为定稿沉默面，靠 target-form+product-v1 追认）；②**叙事漂移**（architecture-map-v3「八表」标题、v2 §0.3 vs §5.3 命令数两说——文档自身不一致，见④）。方向性重定位（审计降位）为用户裁决级演进，非工程漂移。

---

## ④ 语料遗留的未决问题清单

> 分四类：A 定稿/文档内部矛盾（本审计新发现）；B 等用户裁决；C 工程/流程遗留（有去向未销账）；D 语料断层（写了但后续无档）。

### A. 文档内部矛盾（本审计发现，此前评审未点名）

1. **v2-design 命令数两说**：§0.3 口径#2「41 命令（§5.3；2026-09-23 终审并入九门断言专用四条）」vs §5.3 标题「命令集（37 条，签名批次 0 冻结）」+合计行「18+12+6+1=37」。同一文档两节互斥；实建以 41 起算（HANDOFF 快照「13 表/41 命令」）。建议按微版本勘误通道在 v2 文末补记口径。
2. **architecture-map-v3「八表」标题 vs 实列 11 表**：§四标题「八表（三组）」，表体列战前四+作战四+判据三=11 行，且 budget.tsv 不在该节（contracts 仍按 13 表冻）。蓝图双胎的 HTML 侧（panorama v3）⑨ 带 headline 自述为「13 本账」，两胎口径亦不一致——违反 PRINCIPLES「单边更新=制造说谎的镜子」的自身对账义务。
3. **「45 条 CLI 命令」vs「命令面 48→49」**：architecture-map-v3 §二判据层写「45条CLI命令」，同文 §v0.9d 写「命令面 48→49」——同一蓝图内两数并存（§二数字未随 v0.8/v0.9d 刷新或反之）。

### B. 等用户裁决（悬置决策）

4. **方向修正案 1 号整体批/改**（direction-amendment-1 §五-1）。
5. **sqlite3 投影层**分层方案（direction-amendment-1 §五-2；票③）。
6. **ZhuLong 导入闸放行**（direction-amendment-1 §五-3；USER-CHARTER §F26「对仓一行，等你批」）。
7. **multica 与探隐的分工**（USER-CHARTER §F25，用户提过未答）。
8. **方向盘批+司机批排期**（USER-CHARTER §F27；HANDOFF 2026-10-16「Round1 四问待用户: 死线性质/二开总闸/对象(已有事实判决)/方向盘批」）。
9. **文案换血批两处【待定】+13 词歧义清单**（HANDOFF 2026-10-16 下午行：覆盖计量词/召回替词待用户；USER-CHARTER §C32 歧义上报律）。

### C. 工程/流程遗留（有去向、未销账）

10. **契约 v3 预定笔未销**：G-4 重启成本定标、G-37 token 系数回写（median=1.116）（b6 移交清单；b7 移交清单）。
11. **G-22 生产钥生成仪式**未执行（离线机人工；M13 侦察工具扩键重签同批；三处披露不删）（b8 移交清单）。
12. **真人三件**：10 页人工复核（HUMAN-REVIEW 附录）/R11 法务过审/Actions 页面复核（b8 移交清单「四件真人，不代做」）。
13. **G-38 walcode/CodeBuddy 实测回传+opencode/codex 真宿主 hook 接线**（b6/b7 移交清单）。
14. **Tier2 hooks 真挂载实验**（BLUEPRINT-RECON 计划档对账：「真正待办=Tier2 hooks 真挂载实验……排 v1.0b 期间」；勿与 b26 gateloop 混同——E4 评审曾纠错）。
15. **b10 P2 台账 16 项**未修清单（行为差分主通道/误报重标/键形 v4/precision 并报/scope matcher 联查/单源化五工具/契约链悬空/G-r4 入库金样/CI selfcheck/RUNBOOK 勘误/飞轮归因核验/同子集口径/G-51 工件……逐项见该档 P2 表）。
16. **弱模型档位遵循度 evals 用例**：b3 G-9 承诺「批次 6 evals 增弱模型遵循用例」，b4-b8 台账与 HANDOFF **未载兑现行**——语料断层，需实勘 tests/evals 方能判定（本审计未读测试代码）。
17. **G-36 HTTP/2/TLS 真帧样本**再裁直贴形态（b6 台账）。
18. **VulnClaw 余 39 专题蒸馏+CNPEN 素材五类缺补+BugHunter/Threatswarm/CEP 三源到位补蒸馏**（b5 移交清单「持续飞轮」节）。
19. **靶场第二战（基线 v2）+扩编 20→50+飞轮喂养**（b8 移交清单）。
20. **TSecBench L3 全量对齐**=发布前义务（b6 G-40）。
21. **v1.0b 三张门票余量**：票① v0.9d 收口已做（HANDOFF 2026-10-16「观察面收口（侧栏/12 灰阶/外链/人话/发现流）同日」）；票② 执法面升权已做（§v0.9.6 落账）；**票③ v0.9.7 循环地基批排队**（「排队: 画布段→方向盘批→v0.9.7 地基批」——画布段在航、方向盘批计划冻结未执行、地基批未开）。
22. **实验设计执行**：配对置换 N≥4+死区 14 题零战成本归因先行（direction-amendment-1 §三）——设计冻结、未跑。
23. **D4 三缺口**：登录未做/serve 单命令未收口/浏览器端零按钮（USER-CHARTER §A3 🔴；§D17 方向盘批=五按钮）。
24. **engine-fusion-architecture §1-5 虚建件生产接线**（judge_client/llmpool/wall_clock/intent owner+lease——direction-amendment-1 票③「接线四件」）。
25. **G-49 已知边界**：链式重放跨进程并发同 EV 链写同目录时序（b8 台账三节，单人交战口径不触达）。

### D. 参照性悬置（外部依赖）

26. **烛龙接入**（v2 §11 批次 7 可选；一致性夹具 C6 设计在册，接入时点未定/R7）。
27. **GenCPT V2 重写前置四漏**（gencpt-suite §11：Wave 2/3/4 安装+回滚 smoke 无任务落地等——若启动其重写先补四处；属外部参照债）。
28. **多交战并行与 graph.ndjson 锁协议**（v2 §12 R6 探知项：「多开需求出现前不设计」——有意悬置）。

---

## 附：审计方法附注

- 本报告只读全部语料 + 仅写本文件；未运行任何测试、未改动任何工程文件。
- 实建对账的证据层级：**L1 设计语料自述**（architecture-map-v3/HANDOFF 状态行）＞**L2 仓内文件存在性**（cli/、knowledge/、contracts/、platform/ 清点）＞**L3 代码行为**（未逐行读实现，凡涉代码行为断言均标注来源文档）。
- 报告内所有「✅/🟡/🔮/🔴/🔵」状态符沿用蓝图双胎的既有图例（architecture-map-v3 图例行），非本审计新判。

# ARTEX 深读 · 视角5 武器库与提示词工程（子代理 97f35c21，2026-10-11）

> 只读实勘：skills/ 三技能包 + agent/prompt*.go/constraints.go/toolcatalog.go + norma/{tool,harness,skill,memory,compaction}。舰队 5 路之第 5 路。

## ① 机制详解

**三个 SKILL 结构**：
- api-recon（SKILL.md 425行/18.4KB + reference.md 19.9KB + scripts/ 7文件）：frontmatter 仅 name+一句中文触发描述。骨架=边界禁止表(允许/禁止双列)→两层模型(静态/运行时)→完成定义checklist→脚本门禁A/B→工具输出约束→Phase 0-5 路线图→各Phase详解→盲区自认。scripts/ 是参考模板：铁律"先读→按目标改→写入OUTDIR→记CHANGES.md，禁止直接跑原版、禁止手写替代脚本"。
- playwright-cli（420行/12.6KB + references/ 9篇）：frontmatter 带 allowed-tools；主文件=命令速查目录，细节下放 references 按需渐进披露。
- scopesentry（366行/16.5KB）：MCP 工具表+工作流+search/filter DSL+故障排查；frontmatter 写法有误（缩进在标题下）靠解析容错才加载。

**技能加载**（norma/skill/skill.go + assembly.go + compaction.go）：遵循 agentskills.io 规范。所有技能打包成一个 Skill 元工具，Prompt 列技能清单——预算 8000 字符、单条描述截断 500、超预算降级仅名字但**绝不丢技能**。调用后技能正文以**独立 user message** 注入（非埋 tool_result）；compaction 时在摘要边界后**逐字重注入**最近调用的技能（每技能≤5K token、总≤25K，最近优先）。frontmatter mcps: 声明的 MCP 在技能加载时才解锁（deferred tools：schema 扣留+unlock set）。${SKILL_DIR} 占位符引用自带脚本。

**System prompt 组装**（prompt.go+promptcatalog.go+constraints.go）：三段式。段[A]可编辑正文：Go 模板，DB agent_prompts 可 UI 覆盖，missingkey=error+三层回退（DB→内置→原文），6 内置角色各一套；段[B]流量工具说明、段[C]中间产物输出规约（强制写专属工作目录、禁 /tmp）由**代码注入、不可编辑**。constraints.go 把 DB allow/deny 渲染成"【操作约束（最高优先级，凌驾于下方一切探索/拓面启发式；每生成一条意图、每执行一个动作前都必须先自检）】"+反扩张条款"发现约束外新目标≠获得授权，记 out-of-scope 并跳过"。worker 正文约 700 字：只做一条意图、三条写回通道不串图、"写进图才算数"、多观察合并一条防膨胀、report_finding 必须真实触发（严禁 CVE 匹配推断）。pentest 独立 agent 最肥：六条心法——先广后聚防隧道视野、一条路走透（初阻≠死路）、封锁路线不无理由重试、对抗式自检（证伪与证实等价）、要具体结论不要状态报告、不轻言放弃。

**工具面**（norma/tool + toolcatalog.go + tools.go）：CoreTool 契约=Name/Desc/Prompt/Schema+按输入判定的 IsReadOnly/IsConcurrencySafe+权限自检+Call；Build() fail-closed 默认（未声明即非只读/非并发/需审批）。SDK DefaultTools=粗粒度九件套（Read/Write/Edit/MultiEdit/LS/Glob/Grep/Bash/Sleep），Bash 兜底一切。ARTEX 域工具=细粒度状态机工具：planner 18 个（graph_overview/add_intent/prove_goal/kill_work/steer_work/list_untested_assets 等），worker 9 个+**刻意不给 MultiEdit/Glob/Grep**（收敛工具面，检索走 Bash grep）。goal_met 默认不绑任何 agent。toolcatalog 把工具 seed 进 DB：**key/handler 死绑代码，DB 只能改描述/schema 散文/default**。harness execOne 是全局唯一 choke point：任何工具输出过幂等 capOutput 截断+落盘指针防上下文溢出；guardPanic 把 panic 转 tool error。

**Memory**（norma/memory/）：文件型 markdown+frontmatter+MEMORY.md 索引常驻 system prompt。检索=纯关键词计分（name×3/desc×2/body×1）+recency 决胜，top5 全文；注入带 Age 与 staleness 标注（>48h "point-in-time note"）。RecordMemory 的 Prompt 写明"记稳定事实，不记会话细节"。

## ② 妙处
1. 技能正文独立 message+压缩后逐字重注入——作战条令跨 compaction 存活。
2. 三段式提示词：安全关键段代码锁定——"能被编辑掉的纪律就不算纪律"。
3. constraintBlock 反扩张条款——打 LLM"看到新端口就想打"的天性，scope 自检提到每条意图每个动作前。
4. 工具面即纪律——worker 砍 Glob/Grep 是逼行为收敛不是省钱。
5. "写进图才算数"——记忆外化，步数耗尽/压缩不丢战果；report_finding 门槛对抗幻觉战果。
6. api-recon 门禁+禁手写脚本+上下文卫生（禁 Read>100KB、grep 必 head -20）。
7. 无凭据 mock 撑壳侦察——stub 鉴权接口让 SPA 渲染登录后界面只录 outbound。
8. listing 降级策略与 fail-closed 工具默认——"宁可退化不可失效"。

## ③ 弱点/隐患
1. memory 中文失效：tokenize 正则 [a-z0-9_]+，中文查询/内容得 0 分，中文环境近乎不可用。
2. 提示词纪律是软约束：constraintBlock 靠模型自检无硬门，可被目标页 prompt injection 策反。
3. 段[A]全部可编辑：UI 操作者可删光六条心法——段B/C 锁定思路没推广到纪律段。
4. 纪律文本三处重复维护（worker/pentest/reporter 措辞各异）易漂移。
5. 长技能+重注入预算 25K token 挤上下文；SKILL.md 无 lint（scopesentry frontmatter 错误带病上线）。
6. RecordMemory 同名覆盖、无去重冲突检测。

## ④ 探隐可借鉴
1. 技能三层拆分（纪律页+配方 reference+可改脚本模板+CHANGES.md）→改造 pentest-core SKILL.md。风险：脚本改动须哈希链记录才可审计。
2. 三段式提示词：精度门/账本写入规约做代码锁定段，战术话术放可编辑段。风险：锁过多失去调优空间。
3. constraintBlock 式 allow/deny 渲染+反扩张条款：九门 scope 门配一段最高优先级提示词。风险：必须与硬门配合。
4. 技能独立 message+压缩重注入：长会话技能条令跨压缩存活。风险：预算按探隐账本体量重调。
5. 三通道写回+合并纪律（"只写增量、多观察并一条、写进账本才算数"）：13 本 TSV 的分账写入工具+防膨胀纪律。风险：账本层用哈希链去重校验兜底。
6. 按角色裁工具面：探隐按门阶裁剪。风险：裁狠了全走 Bash 兜底反而难审计，配 Bash 全量入账。
7. 全局输出 choke point（幂等截断+落盘留全量）：每条工具输出入账前统一截断、原文落盘哈希入链。风险：纯截断丢证据，必须 spill-to-file。
8. 工具目录 DB 化（handler 死绑、DB 只改散文/default）：说明可配、行为不可配。风险：描述与行为漂移需定期比对。
9. memory staleness 标注：账本回读注入时效提示配置信度字段。风险：中文检索照抄关键词打分必翻车，须换分词/embedding。
10. fail-closed 工具默认+按输入判定只读：直接抄。

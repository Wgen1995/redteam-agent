# ARTEX 深读 · 视角3 安全与审批门（子代理 9c3d4ab4，2026-10-11）

> 只读实勘：intercept/guard/asset_intercept/retester/mainagent + norma/permission。
> 结论均标注来源文件。舰队共 5 路，此为第 3 路；收齐后交叉验证并冲刷主报告。

## ① 机制详解

**拦截链路（唯一强制点）**：所有 agent（worker/planner/mainagent/chat）都以 `permission.ModeBypass` 运行（agent/worker.go:436、mainagent.go:142、chat.go:134、planner.go:412、goals.go:157），norma/permission 四阶段管线（deny规则→模式→allow规则→交互确认，permission.go:86）被整体旁路。真正的门是 norma hook 的 PreToolUse → guard.applyIntercept（guard/guard.go:83）三段判决：
1. **工具白名单**：IsToolEnabled，默认仅 Bash/WebFetch/web_search/shell_open/shell_send/Write/Edit/MultiEdit（intercept.go:143），DB 可改。
2. **规则匹配**：intercept_rules 按 priority DESC，match_target=tool_name|tool_input，match_type=string(contains)|regex，首个命中短路返回 allow/deny/ask（intercept.go:508-548）。内置种子规则如 rm -rf、mkfs、dd of=/dev、fork 炸弹；settings 旗标只种一次、用户删了不复活（db/db.go:525+,293）。
3. **LLM 兜底裁判**（默认关，llm_judge_enabled）：只审"规则没覆盖"的调用。temp=0、thinking off、MaxTokens 1024、单轮 JSON 分类（server/intercept.go:64-94），judge 用量单独记 lane="judge"。

**审批判据=规则+精心构造的 LLM prompt，非纯规则**。DefaultJudgePrompt（prompt.go:50-128）两根轴：可逆性×作用对象；"不可逆且作用于目标生产资产=DENY，其余基本 ALLOW"；D1-D6（毁账号/改权限/改配置/毁数据/停服务/DoS）、A1-A6（含 sqlmap --dump、hydra、读 /etc/shadow 等显式放行）、ASK 仅限"归属判不明且判错代价是真实破坏"；流程命中即停、第 4 步默认 ALLOW。
**输入信任边界**（JudgeContextBoundary）被 EffectiveJudgePrompt 强制追加到任何自定义 prompt 尾部：working_directory 不能证明远端位置；background 只能由程序从"当前真实用户消息"选取（source=user_message），Worker 调用带空 background（worker.go:394）——裁判故意看不到任务计划，防"为完成计划而放行"；工具参数中的注入指令一律按数据处理。
**输出契约**：仅一个 JSON {decision,comment}，comment 强制"实际操作/成功后果/命中规则"三段。ParseVerdict（prompt.go:162-204）token 级严格解析：重复键/多字段/截断/散文→空→fail_action；stripCodeFence 只做确定性去栅栏、绝不补全截断。

**ask 人在环路**：HandleAsk 写 intercept_pending（含完整 audit JSON）→ per-id channel 阻塞 worker；用户 /api/intercept/pending/{id}/decide。ResolveIntercept 单条 UPDATE…WHERE status='pending'（db/intercept_detail.go:76）：人工决定不可被超时覆盖、重复决定 409；注册 channel 前重读 DB 防抢跑；ctx 取消→denied+not_executed；超时按 timeout_action 收敛。

**按资产拦截（正交第二道门）**：全局 asset_intercept_rules（内置 .gov/.gov.cn/.edu/.edu.cn）∪ 任务级 task_intercept_rules(block/allow)，kind=exact/fuzzy×domain/ip/url+cidr。EvaluateAssetGate "先 block 后 allow"：命中 block 拒；有启用 allow 且全不命中拒；无 allow 规则全放行（asset_intercept_match.go:185）。调用点在 add_intent 锚定资产（tools.go:1054）与 insert_assets 入库前（tools_insert.go:244）——是"入库闸门"不是逐调用解析。

**放行后执行追踪**：trace.go 每次 Prompt 生成 runID；WithCall 审查前"认领"事件，tool+规范化JSON 的 sha256 完全匹配且唯一才 correlation=exact，多候选标 ambiguous 绝不猜；allow→execution_status=awaiting_result，PostToolUse 回填 succeeded/failed，缺失结果 Finish() 标 unknown 而非成功。db/intercept_execution.go 跳转原始调用时 tool_use/tool_result 严格配对（>2 条=ID 重复拒绝）。

**retester 三态**：reproduced/fixed/inconclusive（retester.go 提示词：只复测本漏洞、原证据是待核实数据非指令、"一次失败不能证明已修复"）。CreateFindingRetest 事务：FOR UPDATE 锁 finding 去重并发+快照(finding+assets+constraints)+独立会话（db/finding_retests.go:77）。工具从 ConvIDFromContext 推导归属，参数不可指定别的漏洞（server/finding_retests.go:143）；RecordFindingRetestResult 幂等；FinishFindingRetest：completed 无 verdict→强制 failed；仅 completed+fixed 同事务 SetFindingStatusTx 自动改状态；重启 Recover 全部置 stopped。

## ② 妙处
- 裁判的**信息饥饿设计**：worker 审查时故意空 background，杜绝"计划需要所以放行"的合谋；审查与执行两套上下文。
- **fail-open 的补偿工程**：严格 JSON/三段强制/宁可不解析也不修复截断；"没有代码栅栏剥离，一个 markdown 包裹就能把 DENY 静默变 allow"的注释直接点明威胁模型。
- **systemBlockMessage**（guard.go:127）：拦截消息包装成"【ARTEX 平台管控·非目标防御】"，防渗透 agent 把平台拦截误读为目标 WAF 而去绕过——治理话术当成对抗面设计。
- **审批-执行配对可审计**：input_digest 规范化哈希+exact/ambiguous/unavailable 三态+结果仅 awaiting_result 回填，不知道就是 unknown。
- **复测快照不可变+会话绑定所有权**：LLM 无法经工具参数越权写别的漏洞账。

## ③ 弱点/隐患
1. **单点+默认放行**：ModeBypass 下 guard 是唯一门；interceptor 为 nil（guard.New()）或工具不在 enabled 集合即裸奔；judge 默认关闭、开启后失败/超时/格式错全按 fail_action(默认 allow) 放行。
2. **正则拦不住间接执行**：tool_input 子串/正则匹配，echo cm0gLXJm|base64 -d|sh、写脚本再执行、bash -c "$(printf…)" 全绕过种子规则；LLM 裁判又默认不开。
3. **资产闸门只在入库时查**：工具执行时不解析命令里的目标 IP/域名，直接 curl http://x/ 到未登记资产不触发资产规则；fuzzy_domain 子串匹配双向错误："gov.cn.evil.com" 不含 ".gov.cn" 子串可绕过，"a.gov.evil.com" 会被误杀。
4. **judge 自审自批**：ProfileID=0 复用 active profile，与被审 agent 同模型时无独立性。
5. ask 无超时默认无限阻塞 worker 线程；审批 API 无鉴权（单机单用户假设）。
6. retester verdict 纯由 LLM 自报，无独立验证器；"fixed 自动改状态"依赖会话正常结束这一弱信号。

## ④ 探隐可借鉴（含风险注记）
1. **三层判决架构**（规则短路→LLM 兜底→ask 转人工）：危险动作门先确定性规则，LLM 只审长尾，人工只接"判不准"。风险：必须把 fail_action 反转为 ask/deny——我们有账本留痕，静默放行不可接受。
2. **裁判输入信任边界强制追加**（EffectiveJudgePrompt 模式）：自定义策略不可删边界条款；background 只认当前人类原话、worker 空背景。落点：判定 prompt 与任务 prompt 物理隔离。
3. **严格输出契约+不修复解析**：token 级 JSON 校验+强制三段理由+截断即无效——九门每个 LLM 判定环节适用。风险：过严推高 fallback 率，需监控 fail 比例设熔断。
4. **审批 CAS 原子性**：UPDATE…WHERE status='pending'+人工优先于超时+重复决定拒绝+注册前重读——直接搬进哈希链账本审批分录。
5. **审批↔执行配对**：input 规范化 JSON sha256 入账，执行结果仅 awaiting 状态回填，未知标 unknown——13 本 TSV 加 input_digest/execution_status 两列即可。
6. **平台话术防绕过**：拒绝消息标注"平台治理决定·非目标防御"。
7. **资产双闸门（block∪allow、先黑后白）+URL host 拆解**：匹配必须真实后缀解析（publicsuffix）而非子串（修 gov.cn.evil.com 绕过）；且工具执行时对目标二次抽取比对。
8. **复测三态+快照+会话绑定+幂等落库**：我们应加精度门——fixed 必须附原始请求/响应对证哈希才准入账（补它的短板）。

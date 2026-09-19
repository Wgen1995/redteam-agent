# AI 渗透测试落地痛点与方案可采纳性分析报告

**日期**：2026-09-20 · **仓库**：`~/redteam-agent` · **性质**：正式研究报告（第 2 份）
**前置**：本报告是 `docs/research/2026-09-19-ai-pentest-landscape.md`（下称 **landscape**：6 赛道扫描 + 13 项目源码级深析 + 4 专家评审 + 12 must-haves）的补齐篇，补齐四块内容：**P1** 传统渗透测试痛点系统分析、**P2** 13 项目统一框架可采纳性评估、**P3** 组合现有方案 vs 自研差距分析、**P4** 方向选型论证；另附 **P0** 一页决策表与 **P5** 适用边界声明。

**读者画像**：5 年源码审计经验、正转岗一人红队的工程师——长处在读代码、逻辑推理与认证后业务逻辑分析，短板在黑盒工具链肌肉记忆、内网/AD 实战与乙方交付流程（P1.3 知识断层一组痛点专门对齐该画像）。

**数据源与引用约定**（每个判定给出处，格式「文件 · 字段/代码路径」）：

| 来源 | 内容 | 引用缩写 |
|---|---|---|
| `.research/dive/*.json`（13） | 源码级深析：架构/状态/工具集成/护栏/输出五维 + 可复用模式/反模式/裁决/许可证 | dive/<项目>.json |
| `.research/scan/*.json`（6） | 赛道扫描：星数、活跃度、许可证、赛道空白 | scan/<赛道>.json |
| `.research/expert/*.json`（4） | pentest / ai-agent / architect / devops 专家评审 | expert/<角色>.json |
| `2026-09-19-ai-pentest-landscape.md` | 前份总报告（12 must-haves 见其 §7.2） | landscape §N |
| `.research/dive/tsecbench-q2-2026.json` + `docs/research/pdfs/tsecbench-q2-2026-extract.txt` | 腾讯安全云鼎实验室 TSecBench v1（2026Q2）：13 Agent × 4 模型 × 3 轮 × 63 题六能力域，外部基准量化证据（2026-09-20 并入） | TSecBench |

---

**阅读路径**：决策者只读 P0（一页）+ P4.1（路线对比）+ 各节结论行；工程执行者按 P0 索引跳转 P1 对应痛点 → P2 对应项目卡 → P3.4 自研边界 → P4.3 选型表；复核者从附录 A 反查每条判定的原始出处。本报告所有表格均可独立阅读，行内括号即出处。

---

## P0 结论速览：一页决策表

**痛点 → 现有工具覆盖度 → 剩余缺口（= AI 化标的）→ 本报告章节索引**

> 外部基准注记：TSecBench 2026Q2 横评显示最优 Agent×模型组合仅 90.54%（多阶段渗透 29.53%）——P0 全表「剩余缺口」列的判断获得独立赛场数据印证，详见 P3.5。

| # | 痛点（一人红队视角） | 现有工具覆盖到什么程度 | 剩余缺口（AI 化标的） | 章节 |
|---|---|---|---|---|
| 1 | 侦察与信息整理占时过高 | recon 赛道高度自动化（Osmedeus/reconftw/ARL），但产物格式异构、跨阶段衔接靠人工粘合（scan/automation gaps） | 统一资产中间层 assets.jsonl + 自然语言入口 + 跨工具 findings 契约 | P1.1 / P3 |
| 2 | 上下文切换与多目标并行 | 各工具各有 workspace（Osmedeus workspaces/、PentAGI per-flow 容器、Threatswarm worktree），互不认账 | 单一交战目录状态契约 + 断点续跑 + 多交战隔离标准 | P1.1 / P3 / P4 |
| 3 | 覆盖负空间不可见（测了/没测什么说不清） | 仅 Strix 有 coverage 四态台账、Caldera 有 skipped_abilities 原因码；ARL 静默跳过=谎称测过（expert/ai-agent #6） | coverage.json 进交战契约并驱动报告「覆盖度与局限性」章节 | P1.2 |
| 4 | 认证后越权/逻辑漏洞漏测（产出最高的洞类） | **全行业空白**：无任何项目有 creds/session/role 实体与差分重放工作流（expert/pentest #1） | creds.yaml + sessions/ + 身份矩阵差分子流程 | P1.2 / P3 |
| 5 | 复测回归成本高 | 全赛道缺位，仅 paranoid 覆盖自有应用自攻击复验（scan/agent-skills gaps） | verify-fixed 复测模式（以上轮 findings.jsonl 为输入） | P1.2 |
| 6 | 工具语法记忆负担 | 技能按需注入已有先例（Strix 28+ 技能 markdown、HBPGPT AD 场景语法纠偏表），但深度绑定各自平台 | references 漏洞类分册 + 语法纠偏规则库 + 适配器统一调用模板 | P1.3 |
| 7 | 新攻击面学习曲线陡 | 指纹→技能路由已有雏形（BugHunter hunt-dispatch、DarkMoon 技术栈子代理、open-sploit Step-0），但 0-2★ 生态脆弱 | 目标分类路由表 + 可执行的漏洞模式分册（hunt-* 模板骨架） | P1.3 / P2 |
| 8 | 审计转岗知识断层 | PTES/WSTG 阶段映射存在（CEP 六阶段），但全英文 bug-bounty 导向、无中文合规语境（scan/agent-skills gaps） | 方法学数据化（phases.yaml）+ CVE 联网核验纪律 + 中文报告骨架 | P1.3 / P4 |
| 9 | 证据随手丢（截图/记录不成链） | 双审计流与证据链契约散见（Threatswarm commands.log、Strix http_exchange_ids、DarkMoon evidence 结构） | evidence[] 统一契约（路径+哈希+类型）进 findings 行 | P1.4 |
| 10 | 报告耗时 > 测试耗时 | 报告确定性重建仅 DarkMoon 一家（且 GPL 不可搬码）；中文合规报告无结构化先例（scan/standards gaps） | findings.jsonl → 中文合规报告流水线（服务端重建+模板） | P1.4 / P3 / P4 |
| 11 | POC 不可复现 | 证据收据制仅 PentestGPT（逐字子串校验）；OOB 确证门仅 BugHunter；网络位置/前置条件/matcher 全行业缺失（expert/pentest #2） | POC 硬契约（四要素）+ 独立重放验证门（三态） | P1.4 / P3 |
| 12 | 一人无队友复核 | 零散存在：Strix counterevidence 反证字段、BugHunter 7 问门、HBPGPT task_solved 事实核查 | 出卡质量门写成 Phase exit 断言（机器可复核断言入卡） | P1.5 |
| 13 | 授权边界自守 | 门禁全部 prompt 级或单点：Threatswarm exit-2 hook 有 fail-open+变量绕过实洞；nuclei dialer 只管自身流量（expert/ai-agent #3） | 三层执法（egress 代理 → fail-closed hook → 脚本兜底）+ canary 证等强 | P1.5 / P3 / P4 |
| 14 | 疲劳误操作 / 破坏性残留 | 声明式机制存在但不保证幂等：DarkMoon execution_guard、Caldera cleanup 逆序、Stratus 生命周期契约；adversary 赛道自认「清理与回滚不完整」 | 有界执行守卫 + changes_ledger + cleanup 收尾断言 | P1.5 |

**总判定**（继承 landscape §1 并在 P2/P3 展开）：没有可以直接采用的完整体——13 项目中仅 **nuclei** ✅直接可用（adopt-as-dependency），7 个 🟡部分可用，5 个 ❌仅借鉴模式；最优组合（nuclei+Osmedeus+Strix+语料包）对照 12 must-haves 仍有 10 条硬缺口，自研边界收敛为「胶水层+门禁+契约」三层（P3.4）。

---

## P1 传统渗透测试痛点系统分析（一人红队视角）

分析框架：每个痛点四段——**表现**（现象）→ **根因** → **现有工具解决到什么程度**（带出处）→ **剩余缺口 = AI 化标的**。痛点按五组组织：时间结构 / 覆盖 / 知识 / 证据与交付 / 一人特有。

### P1.0 分析框架与分组

五组 14 个痛点不是并列清单，而是一人红队作业流上的递进关系：**时间结构**决定「一天能推进多少」（效率层）→ **覆盖**决定「打没打对地方」（有效性层）→ **知识**决定「能不能上手」（能力层）→ **证据与交付**决定「成果能不能兑现」（变现层）→ **一人特有**决定「会不会出事」（生存层）。每条痛点四段中的「剩余缺口」均与 P0 决策表和 P3 的 must-have 映射对齐，避免痛点分析与方案选型两张皮。

### P1.1 时间结构

#### P1.1.1 侦察与信息整理占比过高

- **表现**：一次 1-3 天的交战窗口（expert/pentest #4 给出的一人红队典型约束），大头耗在子域/端口/指纹/目录等信息收集与**整理归并**上；真正打漏洞的时间被挤压。
- **根因**：recon 本身可自动化，但其产物是几十种工具的异构原始输出（nmap XML、httpx JSON、SARIF、截图……），跨阶段消费靠人工开文件、复制粘贴。scan/automation 对整条赛道的判语即「状态格式异构：各工具原始输出直接落盘，无统一结构化 findings schema，跨阶段机器可读衔接靠人工粘合」。
- **现有工具解决程度**：自动化覆盖已经很厚——Osmedeus 以 workflow/module 双层 YAML 编排子域→解析→端口→Web→漏扫（dive/osmedeus.json「architecture」），reconftw 单命令串 100+ 工具（scan/automation），ARL 做成五容器资产测绘平台（dive/arl.json）。但三者产物各自为政：Osmedeus 靠 step exports 变量链在**自家引擎内**传参，ARL 落在 Mongo 十几个集合，出了自家边界都要人肉转换。
- **剩余缺口（AI 化标的）**：统一资产中间层（landscape §7.1 的 assets.jsonl：host/service/url/account_touchpoint 实体 + 生命周期字段，源自 ARL 资产模型 + Caldera facts）+ 自然语言驱动的整理与检索（专家定方的 resume_kit/grep-jq 点查规则，expert/ai-agent #1）。对转岗者，LLM 在这里的第一价值是把「读 30 个原始输出文件」变成「问一句话」。

#### P1.1.2 上下文切换与多目标并行

- **表现**：同时背 2-3 个交战，每个交战内又要在外部侦察/内网横移/报告补证据之间来回切；隔天回来「上次测到哪」靠翻终端历史。
- **根因**：交战状态没有一等公民载体。scan/ai-agents 对 agent 赛道的判语：「长程记忆缺失：数小时交战的 nmap 输出+凭据+中间发现远超上下文窗口，几乎没有项目定义结构化交战目录/外部记忆契约」。传统作业里同样成立——状态散落在终端 scrollback、脑子和零散笔记里。
- **现有工具解决程度**：单工具内有方案：Osmedeus 的 workspace 固定契约文件族（run-workflow.yaml/run-state.json/run-completed.json，dive/osmedeus.json「state_management」）、Threatswarm 的 evidence/YYYYMMDD/TARGET/ 目录契约 + git worktree 多交战隔离（dive/threatswarm.json reusable#2/#6）、PentAGI 的 per-flow Kali 容器与 PG 持久化。但均为**各家私有契约**，且 Osmedeus 存在目录状态文件与 SQLite 双写漂移的反模式（dive/osmedeus.json anti#3）。
- **剩余缺口（AI 化标的）**：单一交战目录状态契约（journal.jsonl 第一真相 + state.json 派生视图 + resume_kit 恢复注入白名单，expert/ai-agent #1/#2），使「隔天回来」变成一个命令恢复上下文；多目标并行 = 目录级隔离 + 预算树切割（P1.5.3）。

#### P1.1.3 多目标并行的资源冲突

- **表现**：一人单机，长扫描（nuclei 全模板、nmap 全端口）独占终端与带宽，其他交战只能干等；coding agent 的 bash 超时又逼着人砍扫描范围。
- **根因**：长任务与交互式作业共用一个执行面，无后台化/轮询契约（expert/ai-agent #6：「长扫描动辄半小时以上，与 coding agent 的 bash 超时天然冲突，设计没有后台化+轮询契约，agent 只能坐等超时或悄悄砍扫描范围且不留痕」）。
- **现有工具解决程度**：Axiom 给出控制面/执行面分离的云端卸载架构但已停滞两年（scan/automation）；Osmedeus 有 distributed master-worker 与 step_runner 丢 docker/ssh 远端；Strix/PentAGI 用容器隔离并发。对单人单机，这些要么过重要么不可嵌入。
- **剩余缺口（AI 化标的）**：scripts/run-task.sh 式统一长任务封装（后台化+工件落盘+轮询指针进 state.json，expert/ai-agent #6 处方）+ 工件即缓存幂等续跑（Osmedeus pre_condition file_exists 模式，dive/osmedeus.json reusable#2）。

### P1.2 覆盖

#### P1.2.1 覆盖负空间不可见（测了什么/没测什么说不清）

- **表现**：报告写不出「覆盖度与局限性」章节；下一轮复测范围无法界定；甲方问「你们到底测了哪些面」只能口头补。
- **根因**：工具只记录命中（findings），不记录**未命中与未测**；静默降级进一步制造「测过」假象——ARL 的 nuclei 阶段在二进制缺失时「整个阶段跳过，不报错」（dive/arl.json「tool_integration」），expert/ai-agent #6 判语：「ARL 是缺失即静默跳过该阶段——对最终报告而言就是谎称测过」。
- **现有工具解决程度**：两个正面先例：Strix 的 coverage 台账给每个 surface×风险记录 reported/no_issue_found/ruled_out/needs_follow_up 四态，finish_scan 时对零覆盖与未闭环项给最后警告（dive/strix.json reusable#1，出处 strix/tools/coverage/tools.py）；Caldera 的 skipped_abilities 带原因码（PLATFORM/EXECUTOR/PRIVILEGE/FACT_DEPENDENCY，dive/caldera.json「output_report」）。
- **剩余缺口（AI 化标的）**：coverage.json 成为交战必备工件并驱动报告章节；任何降级/跳过/超时强制写 coverage-gaps.jsonl（expert/ai-agent #6 处方）——「因缺工具未测」成为报告一等公民。

#### P1.2.2 认证后越权/逻辑漏洞漏测

- **表现**：给了登录凭据却只扫出组件 CVE；IDOR、水平/垂直越权、业务逻辑（改价、越状态、并发）这类产出最高的洞系统性缺席。
- **根因**：工作流里没有身份实体。expert/pentest #1（severity high）原判语：「输入画像以 Web 登录凭据为主，但 Phase1-5 是指纹→假设→验证的**未授权扫描形状**……state.json 与交战目录契约里没有 creds、session、role 任何实体」，并引用 scan/automation 佐证这是全行业欠账（「凭据使用、漏洞利用、后渗透、横向移动没有编排与状态建模」）。专家还点名优先级倒挂：nuclei 这类最重依赖「恰好只覆盖认证后测试里价值最低的部分（已知组件 CVE 模板）」。
- **现有工具解决程度**：接近零。nuclei 模板生态以未授权检测为主；Strix 有 Caido 代理流量回放能力（list_requests/repeat_request，dive/strix.json「tool_integration」）但无角色差分流程；CAI/BugHunter 均为 bug-bounty 未授权导向（scan/agent-skills：「现有 skill 全部英文 bug-bounty 导向」）。
- **剩余缺口（AI 化标的）**：本报告认为这是**单人收益密度最高**的 AI 化标的——creds.yaml（role/privilege 标签）+ sessions/（会话快照+过期检测+刷新）+ 身份矩阵差分子流程（受保护端点 × 角色 2-4 个逐对差分重放，差异即候选 finding）+ findings 行 auth_context 字段（expert/pentest must_have #1）。转岗审计师的优势恰在逻辑推理，AI 补的是会话管理与重放的机械劳动。

#### P1.2.3 复测回归成本

- **表现**：二期项目要人工逐条重验上轮漏洞是否修复；无工具支撑，成本等同重测。
- **根因**：无结构化 findings 留档 + 无 verify-fixed 工作流。scan/agent-skills 判语：「复测/回归验证缺位：对上一轮 findings 的 verify-fixed（修复确认）没有项目系统性支持，paranoid 的复验只覆盖自有应用自攻击场景」。
- **现有工具解决程度**：Osmedeus 有 asset/vuln diff 快照对比两次运行（dive/osmedeus.json「output_report」，database/diff.go）——最接近的先例，但 diff 的是资产与漏洞计数而非「上轮 POC 重放是否失效」。
- **剩余缺口（AI 化标的）**：verify-fixed 复测模式：以上轮 findings.jsonl 为输入，逐卡重放 POC 并输出前后对比章节（expert/architect nice_to_have #4、landscape §6.6）。前提是 P1.4.3 的 POC 硬契约先成立——没有可机器重放的卡片就没有回归。

### P1.3 知识

#### P1.3.1 工具语法记忆负担

- **表现**：nmap/netexec/impacket 家族几十个工具的参数组合记不住；写错参数轻则重来、重则触发高危行为（如忘了限速打挂目标）。
- **根因**：知识在 man page 与个人笔记里，不随作业上下文注入。
- **现有工具解决程度**：已有按需注入先例：Strix 内置 28+ 漏洞类目 markdown 技能，经 load_skill 工具或 create_agent(skills=[...]) 按需注入（dive/strix.json「architecture」）；HBPGPT 的 AD 场景模板内置大量语法纠偏规则（「netexec 多目标用空格分隔、impacket 工具改名」，dive/hackingbuddygpt.json「tool_integration」，usecases/ad/templates/scenario.md）——证明「纠偏规则表」是有效知识形态。
- **剩余缺口（AI 化标的）**：与平台解绑的 references 分册（BugHunter hunt-* 统一模板的骨架改造，dive/claude-bughunter.json reusable#1）+ 适配器统一调用模板（每工具一处声明 scope-safe flag 集/输出解析/禁止调用形态，expert/devops #6 处方）——语法知识进卡片而不进脑子。

#### P1.3.2 新攻击面学习曲线

- **表现**：遇到 Okta/vSphere/K8s/GraphQL 等没打过的面，从零查资料半天起步。
- **根因**：知识获取与作业流割裂；泛化检查清单（OWASP 之类）不告诉你在**这个指纹**下先打什么。
- **现有工具解决程度**：指纹→技能路由已有三个雏形：BugHunter 的 hunt-dispatch 把 okta.com→okta-attack、login.microsoftonline→m365-entra、vsphere/:9443→vmware 等指纹映射到平台攻击技能并打印 taxonomy（dive/claude-bughunter.json reusable#6）；DarkMoon 按技术栈设专项进攻子代理（GraphQL/Spring/.NET/AD/K8s，dive/darkmoon.json「architecture」）；open-sploit 的 Step-0 按 URL/API/PHP/bug-bounty 签名路由 skill 清单（dive/open-sploit.json reusable#1）。
- **剩余缺口（AI 化标的）**：把三者合并为「目标分类描述符 + 路由表 + 漏洞类分册」（expert/architect nice_to_have #1 的 references/vulnclass/ 正交维度）：新攻击面 = 新增一个分册目录，不改主干。对转岗者这是学习曲线的杠杆点。

#### P1.3.3 审计转岗知识断层

- **表现**：会读代码找逻辑洞，但黑盒方法论（PTES/WSTG 阶段纪律）、内网协议与横向路径、乙方交付流程（授权书/ROE/复测）没有肌肉记忆。
- **根因**：审计的知识组织是「代码→数据流」，红队的知识组织是「阶段→事实→动作」，两套索引不通用。
- **现有工具解决程度**：CEP 用 PTES 七相映射组织六阶段流水线（commands/ext-scope→…→ext-report，docs/METHODOLOGY.md，dive/claude-externalpentest.json「architecture」），其 CVE 联网核验纪律（强制 WebSearch 对照厂商 PSIRT/NVD/CISA KEV，「明确不信任训练数据」）对转岗者尤其对症（dive reusable#6）；Caldera 的 fact 管道（执行→事实→再规划）是红队思维的数据化范本（dive/caldera.json reusable#1/#2）。
- **剩余缺口（AI 化标的）**：方法学数据化（phases.yaml 定义阶段序列/entry/exit 断言/门禁点/回边，expert/architect must_have #1）——让阶段纪律由机器裁决而非靠人记住；中文语境交付骨架（授权与范围声明/ROE 修订表/覆盖度章节，expert/pentest must_have #7）补乙方流程断层。scan/standards 已确认「中文合规报告无结构化先例：等保 2021 版只有官方 Word 模板，无开源 schema」。

### P1.4 证据与交付

#### P1.4.1 证据随手丢（截图/记录不成链）

- **表现**：打完就截图扔桌面，回头写报告找不到原始请求响应；POC 复现步骤靠回忆补写。
- **根因**：证据捕获不是工作流的强制步骤，而是人的自觉。
- **现有工具解决程度**：散见的好机制：Threatswarm 的双审计流（PostToolUse cmd_log.sh 全量命令日志 + Stop findings_sync.py 会话末聚合，dive/threatswarm.json reusable#4）；Strix 的 http_exchange_ids 把 finding 关联到 Caido 代理流量可回放（dive/strix.json「output_report」）；DarkMoon 的 evidence{commands,raw_request,raw_response,logs,explanation} 结构（dive/darkmoon.json「output_report」）；HBPGPT 的 append-only OTel JSONL trace 作单一事实源（dive reusable#4）。
- **剩余缺口（AI 化标的）**：evidence[] 统一契约进 findings 行（path+sha256+kind: request/response/screenshot/oob_callback，expert/architect #5 字段定稿）——证据在动作发生时由管道自动落盘登记，而非事后补。

#### P1.4.2 报告耗时 > 测试耗时

- **表现**：测 2 天写报告 3 天；中文合规口径（授权语境/整改建议/监管口径）每期重排。
- **根因**：报告内容埋在散文与截图里，每次从零组织；AI 生成报告又不可信（幻觉风险）。
- **现有工具解决程度**：关键先例是 DarkMoon 的「报告正文永远由服务端从 findings 存储确定性生成（DEFINITIVE FIX 注释明言不信任 LLM 提供的报告体，LLM 只给 executive_summary）」（dive/darkmoon.json「output_report」，live_push.py）；nuclei 的 multi_writer 一次扇出 jsonl/markdown/sarif/pdf（dive/nuclei.json「output_report」）；Strix 的报告是强 schema 工具调用产物（penetration_test_report.md 四段+vulnerabilities/ 卡片+SARIF）。但中文侧：scan/agent-skills「中文合规报告能力空白」、scan/standards「等保映射无开源实现」。
- **剩余缺口（AI 化标的）**：findings.jsonl → 中文报告的确定性重建流水线（固定章节：授权与范围声明/方法学映射/覆盖度与局限性/技术×业务风险分级/整改优先级与复测建议；等保映射只留人工占位，expert/pentest must_have #7）+ CEP report-template.html（MIT）直接复用（dive/claude-externalpentest.json verdict_reason）。

#### P1.4.3 POC 不可复现

- **表现**：交付的 POC 甲方跑不通，第一质询点；回头自己也复现不出来（环境/前置条件没记录）。
- **根因**：POC 是「一段命令文本」而非带环境假设与判定器的数据。expert/pentest #2（severity high）拆出复现四要素：①网络位置声明（「从互联网还是 VPN 内网打……这是中文报告被质疑复现不了的第一大原因」）②前置条件（角色账号/业务状态）③完整原始 HTTP 请求④预期响应判定器（matcher），并判语「四件套宣称可复制粘贴复现，但设计里这只是口号」。
- **现有工具解决程度**：两个可抄的机制：PentestGPT 新版的证据收据制——Executor 声称的 evidence_excerpt 必须是真实命令输出的逐字连续子串，对不上就验证失败（dive/pentestgpt.json「output_report」，execution.py _exact_receipt_slice）；BugHunter 的 OOB-Or-It-Didn't-Happen 门 + Marker Discipline（盲打必须拿到 OOB 回调才算证据，marker 先查基线防误报，dive reusable#3）。nuclei 的 matcher/extractor 分离提供了判定器 schema 范本（scan/standards patterns）。scan/standards 判语：「POC 复现证据在所有标准中都不是一等公民字段」。
- **剩余缺口（AI 化标的）**：POC 卡片硬契约（env.network_position/preconditions/raw_request（{{CRED:id}} 占位）/expected.matcher/cleanup）+ 独立重放验证门（fresh 会话盲重放复现 expected 才置 VERIFIED，否则 REPAIRED/REJECTED 循环，expert/pentest must_have #2；三态门原型来自 open-sploit hackerone skill，dive/open-sploit.json reusable#5）。

### P1.5 一人特有

#### P1.5.1 无队友复核

- **表现**：所有判断单人背书；误报漏报没人兜底；「我觉得拿到 root 了」可能是幻觉。
- **根因**：团队流程里的 peer review 环节在人单人场景消失。
- **现有工具解决程度**：零散的机器复核机制可拼装：HBPGPT 的 task_solved 事实核查（成功声明必须经 check_command_success 对照真实命令输出/会话 uid 验证，「防模型幻觉式 got root」，dive/hackingbuddygpt.json「human_gates_safety」）；Strix 的 counterevidence 强制反证字段 + LLM 语义去重（duplicate_of 拒绝重报，dive/strix.json「output_report」）；BugHunter 7 问验证门 + never-submit 清单（一票否决，dive/claude-bughunter.json reusable#2）；PentestGPT 的 EXPLOIT 必须引用同 target 最新已完成 TEST 的 observation（证据先行才能打，dive/pentestgpt.json「human_gates_safety」）。
- **剩余缺口（AI 化标的）**：把上述机制统一为「出卡质量门」并写成 Phase exit 断言（expert/architect must_have #6）：finding 的 verified 必须携带证据文件路径 + 一条机器可复核断言（grep/jq 表达式入卡，聚合脚本复跑，失败自动降级 suspected/open_proof_gap，expert/ai-agent #6）——用机器复核替代队友复核。

#### P1.5.2 授权边界自守

- **表现**：没有同伴提醒「这个段不在范围」；越界是法律责任级事故；ROE 中途修订无留痕。
- **根因**：范围执法靠人记忆与自觉；工具侧则普遍缺位——scan/ai-agents 判语「授权范围仅靠 prompt 约束：缺技术上强制执行的 scope 白名单与越界熔断，对真实授权红队是硬伤」。
- **现有工具解决程度**：分三类，均有实测教训：①prompt 级（Strix/PentAGI/HBPGPT/Osmedeus）——已被反复证伪：Threatswarm 实测发现 scope.txt 缺失/为空时 fail-open 放行一切、`$TARGET` 变量间接引用绕过、白名单外工具名跳过检查，且其 settings.json 放行 Bash(bash *) 使权限白名单形同虚设（dive/threatswarm.json「human_gates_safety」+anti）；BugHunter 宣称的 allowlist/审计/限速「grep 全仓库无任何实现」（dive/claude-bughunter.json anti#1）。②代码级单点——nuclei 把网络策略下沉 dialer 层 deny-by-default（pkg/protocols/common/protocolstate），但只覆盖自身流量；Threatswarm 的 PreToolUse exit-2 hook 是正确形态但有上述漏洞；ARL 的提交层+执行层双重黑名单校验（app/helpers/task.py + portScan.py）；Caldera 的 RuleSet trait+CIDR 规则（app/utility/rule_set.py）；PentestGPT 的 URL 规范化+4 轮 percent-decode（plan.py _target_is_allowed）。③完全缺席——Osmedeus「任何输入目标都会被打」（dive/osmedeus.json anti#1）。
- **剩余缺口（AI 化标的）**：三层执法 fail-closed（egress 代理 → 运行时 hook 适配层 → scope-guard 脚本兜底）+ scope.yaml 完整 schema（allowed/denied 双清单、accounts+permitted_actions、oob_endpoints 申报、append-only amendments 修订审计——expert/architect #3；OOB 回连端点不申报会「要么取不了证、要么被迫临时开洞破坏范围模型」，expert/pentest #5）+ 三后端 scope-violation canary 证等强（expert/ai-agent must_have #3：「最弱后端决定整体安全水位，对一人红队这是法律级风险」）。

#### P1.5.3 疲劳误操作与预算失控

- **表现**：深夜把 -T4 敲成 -T5、忘记限速、跑起飞字典、清理动作漏做留下残留；时间在低价值面烧光。
- **根因**：单人长时间作业的注意力衰减无机制兜底；无预算/优先级调度。
- **现有工具解决程度**：DarkMoon 的 execution_guard 是最完整的守卫：pre-flight 分类拒绝「注定跑不完」的命令（hydra+rockyou、nmap -p-、非 --batch sqlmap、tail -f），黑名单 rm -rf/dd/mkfs/fork bomb，容器内 timeout 包裹+超时返回结构化 remediation+幸存进程 reap（dive/darkmoon.json「tool_integration」，mcp/src/tools/core/execution_guard.py）；HBPGPT 的 Limits 四维预算树（轮次/token/美元/时长，父子切割 sub_limit）每轮把剩余预算注入提示让模型自知止损（dive reusable#2）；Caldera 的 cleanup 逆序执行与 visibility/HIGH_VIZ 防高噪（dive「human_gates_safety」）。反面：adversary 赛道自认「清理与回滚不完整：多数能力只声明 cleanup 命令，不保证幂等、不验证恢复结果，一人红队无人复核时破坏性风险高」（scan/adversary gaps）；expert/pentest #4 判语「agent 会在低价值面（全端口全模板 nuclei、无限目录 fuzz）上烧时间」。
- **剩余缺口（AI 化标的）**：有界执行守卫进适配器契约（每工具超时/后台标记/禁止调用形态）+ changes_ledger 台账与 cleanup 收尾断言（每个写操作登记 revert_cmd，报告前全部 reverted 或人工签字豁免，expert/architect must_have #7）+ per-phase 预算树与假设排序（期望严重度×置信度÷预估成本，expert/pentest must_have #5）。

---

## P2 业界实践逐个评估（13 项目，统一框架）

**统一评估框架（七要素）**：优点 / 缺点 / 现状覆盖度（成熟度判定：星数·活跃度·工程质量的综合）/ 能否直接使用（分级：✅直接可用=可立即引入生产交战；🟡部分可用=特定场景可直接用或素材级复用、运行层需改造；❌仅借鉴模式=只能抄设计，不能作为组件运行）/ 适用场景 / 依赖（运行前提）/ 限制（法律·许可证·架构·维护状态）。裁决（adopt/copy-pattern）沿用 dive 的四选一结论。

### P2.0 总览表

| 项目 | 许可证 | 成熟度快照 | 能否直接使用 | dive 裁决 | 对 14 痛点的覆盖 |
|---|---|---|---|---|---|
| nuclei | MIT（LICENSE.md） | 行业事实标准；nuclei-templates 12,989★ 每日更新（scan/standards） | ✅直接可用 | adopt-as-dependency | #1 #6 #9 #11 #13（部分） |
| Strix | Apache-2.0（pyproject.toml） | 64k★，2026-09-17 活跃，v1.6.2，100+ 测试文件（scan/ai-agents + dive） | 🟡部分可用 | copy-pattern | #3 #9 #10 #12 最强 |
| PentAGI | MIT（源码）+EULA（镜像） | 24.7k★，2026-09-10 活跃（scan/ai-agents） | ❌仅借鉴模式 | copy-pattern | #2 #6 #8（平台内） |
| PentestGPT | MIT（LICENSE.md） | 15.5k★，2026-07 缓慢维护，迁移中间态（scan/ai-agents + dive） | 🟡部分可用 | copy-pattern | #6 #8 #11 #12 |
| HackingBuddyGPT | MIT（LICENSE） | 1.2k★，2026-09-13 学术团队活跃（scan/ai-agents） | 🟡部分可用 | copy-pattern | #5（评测）#12 #14（预算） |
| Caldera | Apache-2.0（LICENSE/NOTICE） | 7,277★，2026-08-27，MITRE 官方（scan/adversary） | 🟡部分可用 | copy-pattern | #8 #13 #14（门禁/清理） |
| Osmedeus | MIT（2020 j3ssie） | 6.6k★，2026-09-12 活跃（scan/automation） | 🟡部分可用 | copy-pattern | #1 #2 #5（diff）#10 |
| DarkMoon | GPL-3.0 | 949★/158 fork，2024-11 创建，活跃至 2026-09，单团队（dive） | ❌仅借鉴模式 | copy-pattern | #7 #9 #10 #14 覆盖最深但不可搬码 |
| Threatswarm | MIT（LICENSE） | 80★，2026-04-29 后约 4 个月未更，v1.0.0 单 commit（scan/agent-skills + dive） | ❌仅借鉴模式 | copy-pattern | #2 #9 #13（门禁原型+反面教材） |
| Claude-ExternalPentest | MIT（LICENSE，cma1t） | 0★，v0.1.2，2026-09-09，单人（scan/agent-skills + dive） | 🟡部分可用 | copy-pattern | #8 #10 #13（契约层） |
| Claude-BugHunter | MIT（原作 Sachin Sharma；vendored shuvonsec 亦 MIT） | 2★，2026-05-21，社区关注极低（scan/agent-skills） | 🟡部分可用 | copy-pattern | #6 #7 #11 #12 |
| open-sploit | MIT（包）+Apache-2.0（vendored skill） | npm v1.2.0 首发 2026-09，无 GitHub 仓库/issue/CI（dive） | ❌仅借鉴模式 | copy-pattern | #7（路由）#11（三态门原型） |
| ARL 灯塔 | MIT（镜像 LICENSE.md；vendored python-nmap 为 GPL） | 原仓库 2024 下架 404；镜像 2.1k★，2025-07-16（scan/automation + dive） | ❌仅借鉴模式 | copy-pattern | #1 #13（双层校验） |

**评估方法学**：①「成熟度」= 社区信号（星数/最后提交，取 scan 快照）× 工程质量信号（测试覆盖、CI、文档-代码一致性，取 dive 判语）× 形态寿命信号（单人/团队/官方、是否停更）三轴合成，非单一星数排序；②「能否直接使用」针对本读者目标形态（DSH/opencode/codex 内的 skill+交战目录契约）判定，与 dive 四选一裁决（adopt/copy-pattern/reference/skip）显式对齐；③「覆盖痛点」列回指 P0 的 14 条编号；④所有负面判定必须携带实测证据（文件路径/issue/反模式条目），不接受印象式评价——这是 expert/pentest 对 BugHunter 类「宣称与实现不符」项目定下的纪律（dive/claude-bughunter anti#1：号称的 allowlist grep 零实现）。

### P2.1 nuclei

| 要素 | 评估 |
|---|---|
| 优点 | POC-as-template 事实标准+海量社区模板；ResultEvent 单一事件 schema 是「POC 卡片」天然范本（含 matched-at/curl-command/interaction OOB 证据，pkg/output/output.go + 根目录 nuclei-jsonschema.json）；输出 multi_writer 一次扇出 jsonl/markdown/sarif/pdf；网络策略在 dialer 层集中执法且缺省拒绝（pkg/protocols/common/protocolstate/dialers.go）；模板 ECDSA 签名+指纹缓存建立供应链信任边界；lib/ Go SDK 可嵌入（NewNucleiEngineCtx）；轻量断点续跑（pkg/types/resume.go）。（dive/nuclei.json 各字段） |
| 缺点 | 只做已知漏洞检测，不编排外部 CLI（无 nmap/msf 插件位）也无人工门禁；resume 只记模板×目标进度不记已产出 finding，恢复后重复输出、去重责任推给消费端；types.Options 膨胀到两百多个字段；headless 硬依赖本机 Chrome；OOB 默认第三方 oast.fun（黑盒红队需自建）；flow 的 goja 仅 ES5.1；-scope 正则目前仅在 DAST server 生效。（dive anti#1-#5 +「human_gates_safety」） |
| 现状覆盖度 | **成熟度高**：projectdiscovery 旗舰、httpx/subfinder 生态标准做法；模板库 12,989★ 每日更新（scan/standards nuclei-templates 条目）。对痛点 #1/#11 的「检测器 schema」与「判定器」层覆盖最好，对认证后越权/逻辑（#4）覆盖最低——expert/pentest #1 点名「优先级倒挂」。 |
| 能否直接使用 | **✅直接可用**：MIT（LICENSE.md）允许任意复用/修改/再分发；以 CLI 子进程或 lib/ SDK 引入即得模板生态与稳定 findings schema（dive verdict_reason）。 |
| 适用场景 | 黑盒漏扫原语层：资产指纹后的已知组件 CVE/配置缺陷批量检测；POC 卡片 matcher schema 的参照系；SARIF 入 GitHub code scanning 的桥。 |
| 依赖 | Go 二进制（或 Go SDK 编译）；headless 模板需本机 Chrome；OOB 证据需自建 interactsh 或接受第三方 oast.fun；模板库按需更新。 |
| 限制 | 法律：扫描即攻击行为，仅限授权目标（其自身无 scope 执法，边界须外层承担）。许可证：MIT 无障碍。架构：无凭据会话概念，认证后场景需外部驱动（如经代理重放）。维护：活跃；但模板供应链需钉 commit+验签（expert/devops #3）。 |

### P2.2 Strix

| 要素 | 评估 |
|---|---|
| 优点 | 工程成熟度最高的开源 AI pentest：coverage 负空间台账（surface×风险四态+零覆盖最后警告）；findings 强 schema（强制 counterevidence 反证、服务端 CVSS 算分、LLM 语义去重、update 修订而非重报）；安全向上下文压缩（摘要逐字保留凭据/端点/死胡同、保 tool_call 配对、超大输出 spill 成文件引用）；全状态断点续跑（agents.json+每 agent SQLite+四类台账+--resume）；三态闭环纪律（confirmed/ruled_out/open_proof_gap）；headless 退出码 0/1/2 CI 友好；100+ 测试文件。（dive/strix.json reusable#1-#6 + 各字段） |
| 缺点 | 548 行单体 jinja 系统提示改一处牵全身；范围管控纯 prompt、无网络层出口执法，容器还注入 NET_ADMIN/NET_RAW；约 40 个工具面+「2000+ steps」叙事对中小上下文/弱模型易失控；运行时强绑定 Docker Kali 镜像（唯一内置后端，缺即 exit 1）；反拒答注入（AUTHORIZATION STATUS/REFUSAL AVOIDANCE）移植会放大提示注入与合规风险。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度高**（64k★/2025-08 创建/增长最快/2026-09-17 活跃，v1.6.2，scan/ai-agents）。痛点覆盖：#3 负空间、#9 证据链（Caido 流量关联 http_exchange_ids）、#12 机器复核为 13 项目最强；#4 认证后仍弱、#13 授权自守为 prompt 级。 |
| 能否直接使用 | **🟡部分可用**：作为完整平台不可嵌（引擎约两万行，与 openai-agents SDK/Caido/Kali 镜像强耦合，抽循环≈重写）；但 CLI 可作为受控外部引擎挂载（dive verdict_reason：「可选地把 strix CLI 作为受控外部引擎挂载；底座自建」，其官方顶层 skills/ 即 CLI 包装示范）；六模式整体抄。 |
| 适用场景 | 预算可控的单 Web 应用自主深测（--max-budget USD 硬顶）；作为我们 skill 里「自主深钻」子流程的外挂引擎候选；coverage/reporting 模式的权威参照。 |
| 依赖 | Python 3.12+、openai-agents≥0.19、LiteLLM（任意 provider）、Docker+Kali 全家桶镜像（硬依赖）、可选 Caido 代理。 |
| 限制 | 法律：自主利用行为仅限书面授权环境；反拒答提示与严谨授权链路冲突（dive anti#5）。许可证：Apache-2.0 无障碍。架构：平台形态（CLI+TUI+viewer+cloud 计费）。维护：极活跃。 |

### P2.3 PentAGI

| 要素 | 评估 |
|---|---|
| 优点 | 多引擎搜索降级链（按 links/answer/research/exploit 四意图配引擎链，IsAvailable() 跳过未配 key 引擎，整链耗尽才报错）；execution context 状态契约模板（紧凑 XML 注入全局任务状态并显式保留 OOB 回连 IP）；Waiting 状态机+逐迭代持久化消息链+启动续跑；Reflector 优雅收尾（近上限不硬杀）；双语通道策略（日志用户语言/技术通道强制英文）；敏感数据先匿名化再入长期向量记忆（anonymizer）。（dive/pentagi.json reusable#1-#6） |
| 缺点 | 授权与范围纯靠提示词（primary_agent.tmpl「PRE-AUTHORIZED、永不确认」），全库无 allowlist/CIDR 校验代码；平台依赖过重（PG+pgvector+Docker+scraper+可选 Neo4j/Langfuse）无法嵌进 skill 形态；DOCKER_INSIDE 挂宿主 docker socket 存在官方确认的 prompt injection 逃逸（issue #337）；报告只有 Markdown 叙事、README 自认不支持 JSON 导出；primary→六专家委派链使 LLM 调用数倍膨胀（官方自测 monitor 模式 2-3 倍时延）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度高**（24.7k★/2026-09-10 活跃，scan/ai-agents）。痛点覆盖集中在平台内：#2（per-flow 容器+PG 持久化）、#6（六专家分诊）；对 #10/#11 输出契约弱（散文报告）。 |
| 能否直接使用 | **❌仅借鉴模式**：Go 服务器+Web UI+微服务全家桶，「不可能作为依赖装进 DSH/opencode 里的 skill」；模式级借鉴无许可证障碍（源码 MIT；EULA 只约束官方镜像与整体产品，与 MIT 冲突时源码以 MIT 为准）。（dive verdict_reason） |
| 适用场景 | 若要自建「团队化」多 agent 平台时的架构参照；搜索降级链与双语策略可近乎原样抄进任何 skill 的脚本层。 |
| 依赖 | docker-compose 全栈：PostgreSQL+pgvector、scraper 无头浏览器容器、Kali 镜像（vxcontrol/kali-linux）、约 14 家 LLM provider key 之一、可选 Neo4j/Langfuse。 |
| 限制 | 法律：镜像 EULA 限定合法渗透测试用途（dive verdict_reason）。许可证：源码 MIT，镜像另受 EULA。架构：平台形态。维护：活跃。 |

### P2.4 PentestGPT

| 要素 | 评估 |
|---|---|
| 优点 | 双轨遗产：legacy 三会话 copilot（reasoning 维护 PTT 任务树/generation 展开局部命令/parsing 压缩工具输出）是「todo/局部命令/推理」三分解的原始范本；新版 plan.py 确定性范围校验器（URL 规范化+路径前缀包含+最多 4 轮 percent-decode+拒 userinfo/fragment）；证据收据制（evidence_excerpt 必须是真实输出逐字子串）；SQLite canonical 记忆+revision 租约+只追加 trace 三件套支撑崩溃恢复；EXPLOIT 必须引用已完成 TEST 证据；「LLM 提议、确定性代码裁决」的教科书实现。（dive/pentestgpt.json reusable#1-#6） |
| 缺点 | 新版双角色一律 FULL_ACCESS 且「部署环境即隔离边界」，无运行中人工门禁；TEST/EXPLOIT 短语封禁是英文硬编码、措辞一换即绕过；legacy 会话「保存」是伪持久化（只存转录不存对话状态）；仓库迁移中间态（漂移的 unified_agent 副本、README 与入口不符、google 占桩多年）；官方自认 Supervisor 收敛性弱（长跑丢失覆盖信息、重复探测）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度中**（15.5k★/2026-07 缓慢维护/USENIX 2024 奠基，scan/ai-agents）。痛点覆盖：#6/#8（PTT+知识提示）、#11（证据收据）、#12（TEST→EXPLOIT 依赖）；对 #2 断点续跑在新版内建但 legacy 伪持久化。 |
| 能否直接使用 | **🟡部分可用**：legacy 交互式 copilot 可直接装来当过渡期副驾（Docker 镜像捆绑全套渗透工具）；新版 agent 框架「agent 里再起 agent，职责重叠」不适合作为我们 skill 的依赖（dive verdict_reason）；校验器/证据收据/记忆三件套抄模式。 |
| 适用场景 | 转岗初期的人机混合学习期（人执行命令、LLM 维护任务树）；其 plan.py/execution.py 作为我们 scope 校验与证据门的代码级参考（MIT 可直接改造）。 |
| 依赖 | legacy：Python 多 provider CLI 或官方 Docker 镜像；新版：外部 Claude Code/Codex CLI 子进程+unified-agent 包+嵌套 uv 工程。 |
| 限制 | 法律：Docker 镜像捆绑攻击工具集，仅限授权环境。许可证：MIT（Copyright 2023 Grey_D）无障碍。架构：双轨并存、文档与代码不一致（dive anti#4）。维护：缓慢。 |

### P2.5 HackingBuddyGPT

| 要素 | 评估 |
|---|---|
| 优点 | 极薄可审计核心循环（约 50 行级 use case）；Capability 自动 schema（__call__ 类型注解→pydantic 生成工具 JSON schema，零样板）；Limits 四维预算树（轮次/token/美元/时长，父子切割 sub_limit）；task_solved 事实核查（check_command_success 对照真实命令输出/uid，防幻觉战果）；append-only OTel GenAI JSONL trace 作单一事实源（评测/回放/成本聚合同源）；planner/executor+Knowledge 脏标记合并；OWASP 清单工具化为无副作用查询 capability。（dive/hackingbuddygpt.json reusable#1-#6） |
| 缺点 | 凭据明文写入 system prompt 且被 JSONL 日志全量记录（无脱敏）；零人工审批、零范围强制执行；运行态全内存、无断点续跑（长跑中断整局作废）；工具调用与模板文本双执行路线并存的历史包袱；web_api 测试知识库数千行硬编码字符串。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度中**（1.2k★/2026-09-13/学术团队持续产出，scan/ai-agents）。任务面窄（Linux/Windows 提权、Web API、AD）；痛点覆盖：#5（benchmark_privesc.py+外部靶机仓库的可复现评测范式）、#12（事实核查）、#14（预算树）。 |
| 能否直接使用 | **🟡部分可用**：pip/uv+wintermute CLI 可直接跑——靶场练习（HTB/基准靶机）与受控实验场景立即可用；作为生产交战底座 ❌（安全模型与一人红队相反：「Do not ask for confirmation, nobody will answer」）。（dive「human_gates_safety」+ verdict_reason） |
| 适用场景 | 转岗者的提权专项训练器；skill 评测层的方法参照（JSONL 打分/成本聚合）；预算树与事实核查两机制的抄写源。 |
| 依赖 | Python 3.13+、pip/uv 依赖、SSH 可达的 Kali/靶机（提权用例）、litellm 上游任一 provider。 |
| 限制 | 法律：无范围护栏，仅限自有/授权靶机。许可证：MIT（Copyright (c) 2023 andreashappe）。架构：学术框架自成体系，与 coding agent 宿主不同构。维护：活跃。另注意 dive 更正：hacksteps DSL 并不在本仓库（全库 grep 零命中），评测体系是 benchmark_privesc.py。 |

### P2.6 Caldera

| 要素 | 评估 |
|---|---|
| 优点 | fact 管道闭环（解析器把工具输出提炼成带分数的 Fact/Relationship，后续 ability 以 #{trait} 消费，「执行→事实→再规划」）；桶状态机 planner（state_machine+stopping_conditions，新策略只定义桶方法）；RuleSet 范围护栏（trait 的 ALLOW/DENY+IP/CIDR 网段语义，规划前过滤事实）；人工门禁即状态位（autonomous=0 全 PAUSE+potential_links 逐条审批/改写+RUN_ONE_LINK 单步）；learned-facts 回存 Source（findings 沉淀为可注入情报包）；断点续跑三件套（chain+results 文件+resume_operations）。（dive/caldera.json reusable#1-#6） |
| 缺点 | 全内存+pickle 整库持久化（非优雅退出丢状态、pickle 跨版本脆）；asyncio.sleep 轮询遍布（响应慢难测试）；默认配置明文口令（admin/admin、api_key/encryption_key ADMIN123）；SIGTERM→KeyboardInterrupt 的优雅关闭 hack；插件全是 git submodule+硬编码相对路径（非递归 clone 即空目录，当库引用极不友好）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度高**（7,277★/MITRE 官方/2026-08-27，scan/adversary），但面向对手模拟而非渗透交付。痛点覆盖：#8（ATT&CK 方法论数据化）、#13（RuleSet+审批队列）、#14（cleanup 逆序）；#10 报告面向检测工程（event_logs/覆盖率）而非渗透取证链（scan/adversary gaps）。 |
| 能否直接使用 | **🟡部分可用**：作为独立对抗模拟平台，在内网/AD 授权演练场景可直接部署使用；作为 skill 依赖 ❌（C2 服务器+aiohttp Web+implant 生态的重量级运行时与 SKILL 形态不匹配，dive verdict_reason）；六编排思想以 JSON/YAML 在交战契约中重实现。 |
| 适用场景 | 紫队/AD 横向演练的现成平台；「变量未填不动作」（trim_links）与事实驱动重规划的模式源。 |
| 依赖 | Python 3.x、--recursive clone（submodule 插件）、Mongo 可选（默认文件态）、implant 出网可达 C2。 |
| 限制 | 法律：C2/implant 属受管制攻击性能力，仅限书面授权红队演练；凭据治理粗糙需自改。许可证：Apache-2.0（含商用，保留声明）。架构：自带回环生态。维护：官方但迭代偏慢。 |

### P2.7 Osmedeus

| 要素 | 评估 |
|---|---|
| 优点 | flow（modules DAG，Kahn 调度）→module（steps 顺序/DAG/goto）双层 YAML 编排；「工件即缓存」断点续跑（pre_condition: file_exists 跳过已有输出，同 workspace 重跑即增量）；固定 workspace 状态契约文件族（外部无需读 DB 即可判断进度）；step exports 变量链跨模块传产物；exit 127 两级降级+on_error 每步错误策略；Vulnerability 模型带 FindingHash 去重+Confidence 四级（含 Manual Review Required）；linter 静态检查工作流。（dive/osmedeus.json reusable#1-#6） |
| 缺点 | 无授权范围硬校验（target 只做格式检查，「任何输入目标都会被打」）；「workflow 即任意代码执行」的纯操作者信任模型、无高危动作人工确认门；状态双写（目录+SQLite）两套真相可能漂移；缓存依赖作者自觉写 pre_condition；重 Go 单体（executor.go 3000+ 行）无法被 skill 直接依赖。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度高**（6.6k★/2026-09-12 活跃，scan/automation）。非 AI 引擎里编排与状态最成熟者；痛点覆盖：#1（recon 全流程）、#2（workspace 契约）、#5（asset/vuln diff）、#10（markdown 报告生成函数）；止步于「发现」（scan/automation：「凭据使用、漏洞利用、后渗透、横向移动没有编排与状态建模」）。 |
| 能否直接使用 | **🟡部分可用**：单二进制+MIT，外部资产侦察工作流可直接跑（需自律限定目标，因其自身无 scope 执法）；自定义 workflow 可裁剪成个人 recon 流水线；作为交战底座/依赖 ❌（dive verdict_reason）。 |
| 适用场景 | 域名/资产面常态化侦察（配合其 scheduler cron）；我们「recon 阶段」的可选执行引擎或模式源。 |
| 依赖 | Go 单二进制、私有 binaries 目录或系统 PATH 工具、可选 Docker/SSH runner、可选 SQLite（服务端模式）。 |
| 限制 | 法律：SECURITY.md 自警「Scans look like attacks. Get authorization for every target」——无技术执法。许可证：MIT（2020 j3ssie）。架构：单体引擎。维护：活跃。 |

### P2.8 DarkMoon

| 要素 | 评估 |
|---|---|
| 优点 | Privacy 三件套（vault+gateway+中间件）：确定性占位符（Fernet 加密真值+HMAC 去重）、仅执行点还原、全部输出与异常兜底重 tokenize；「降级不拒绝」网关策略（占位符落外传位置时命令照跑但 withheld 反馈）；push-per-finding+服务端确定性报告重建（存储即真相、防子代理覆盖、报告含真值而模型只见占位符）；execution_guard 有界执行（pre-flight 拒绝无界命令+三段式 remediation+幸存进程 reap）；子代理派发契约（agent .md 逐字节原样+≤30 行 CONTEXT+campaign_id）；对抗式状态分级头（EXPLOITED/CONFIRMED/UNCONFIRMED+自我证伪清单）。（dive/darkmoon.json reusable#1-#6） |
| 缺点 | scope 纯提示词、零技术强制（工具箱 host 网络+NET_ADMIN+docker.sock，docs/security-threat-model.md 自认威胁面）；无断点续跑（编排状态只在 LLM 上下文，内存 vault 6h TTL/重启即丢还原能力）；白名单双份漂移（executor 与 workflows/base.py 不一致，nmap 在分类表却不在白名单）；平台耦合极深（三容器+fork opencode 镜像+硬编码路径）；提示词巨石（pentest.md 2382 行、51 agent 共 3.4 万行）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度中上**（949★/158 fork/2024-11 创建/活跃至 2026-09/自带隐私单测与 Juice Shop 基准，作者自述基本复核属实；单团队、迭代剧烈、事故驱动补丁，dive verdict_reason）。痛点覆盖最深的一档：#7（技术栈子代理）、#9（evidence 结构）、#10（确定性报告）、#14（execution_guard）。 |
| 能否直接使用 | **❌仅借鉴模式**：①GPL-3.0 传染性约束衍生分发（内部使用可接受但不可闭源再分发）；②三容器+fork 镜像+硬编码路径不可作为库嵌入；③零 scope 技术执法+零续跑。（dive verdict_reason：核心循环与我们形态同构，平台外壳是负资产；抄四处模式） |
| 适用场景 | 隐私/凭据治理层的设计蓝本（模式级）；「报告不信 LLM 长文」纪律的出处。 |
| 依赖 | docker-compose 三容器（fork 版 opencode 镜像+FastMCP 服务+50 工具攻击容器）、host 网络、docker.sock 挂载。 |
| 限制 | 法律：全自主攻击引擎，仅限授权；GPL-3.0 条款要求衍生作品同许可开放源码。架构：平台耦合。维护：单团队活跃但剧烈迭代。 |

### P2.9 Threatswarm

| 要素 | 评估 |
|---|---|
| 优点 | PreToolUse 确定性 scope hook（约 60 工具名词边界正则+IP/FQDN 抽取与 scope.txt CIDR 感知比对，越界 exit 2 硬阻断、模型不可绕过）；文件系统即状态与 agent 总线（evidence/YYYYMMDD/TARGET/ 目录契约+recon_summary.md 交接，后续 agent 以前序 summary 存在为放行前提）；关键词→专家 agent 路由表（18 组向量关键词）；按目录绑定输出契约（.claude/rules 的 paths frontmatter 给 evidence/loot/reports 挂强制字段与脱敏 grep 自检）；双审计流；git worktree 多交战隔离。（dive/threatswarm.json reusable#1-#6） |
| 缺点 | scope 门禁 fail-open（scope.txt 缺失/空即放行一切）；$TARGET 变量间接引用绕过（自家命令模板即触发）；白名单外工具（自写脚本）跳过检查；settings.json 放行 Bash(bash *) 使权限白名单失效；无人工确认门；模板自相矛盾（curl 拉 linpeas 被自家门禁误拦，无工具基础设施白名单）；工程成熟度低（v1.0.0 单 commit、README 引用不存在文件、宣称的 scope.yaml 未实现、27 与 26 agent 不一致、无示例报告）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度低**（80★/最后提交 2026-04-29 约 4 个月未更/单人，scan/agent-skills + dive）。形态与我们同构（skill+hook+目录契约），价值在「正确机制+实测漏洞清单」两面。 |
| 能否直接使用 | **❌仅借鉴模式**：Claude Code 专属机制（hooks.json/slash command/agents frontmatter）与 DSH/opencode/codex 不兼容；宣称的 754 skill 在外部仓库未随包分发；核心门禁有 fail-open 实洞（dive verdict_reason）。 |
| 适用场景 | scope hook 的参考实现（补 fail-closed+变量解析后重写）；27 个 agent markdown 作为各攻击域命令模板语料。 |
| 依赖 | Claude Code、Kali 环境 PATH、外部 Anthropic-Cybersecurity-Skills 仓库（不装则 skill 引用静默失效）。 |
| 限制 | 法律：无。许可证：MIT 无障碍。架构：Claude 专属插件。维护：断续（scan/agent-skills：「单人主导、维护断续」）。 |

### P2.10 Claude-ExternalPentest

| 要素 | 评估 |
|---|---|
| 优点 | scope.md 双清单默认拒绝契约（固定标题 allowlist/denylist，不匹配即出范围、只记录不探测；每条命令前重校验、重定向/CDN IP 漂移重查）；目标派生内容即数据（DATA-never-instructions，提示注入标准防线）；工具预检+缺失替代矩阵（naabu→nmap -Pn、subfinder→amass/crt.sh、httpx→curl -sI 等）+「绝不静默跳过阶段，记录缺失让报告诚实」；检测/利用分界线（recon 段 nuclei -etags dos,intrusive,fuzz,brute-force 只检测，真 payload 归 exploit 段且需批准）；ROE amendments 审计段（豁免必须追加带日期/授权人/边界的记录）；CVE 联网核验（PSIRT/NVD/KEV，不信任训练数据）。（dive/claude-externalpentest.json reusable#1-#6） |
| 缺点 | 无结构化机器可读输出（全自由 Markdown，无 JSONL/schema）；断点续跑粒度粗且 .current 指针脆弱（mtime 猜目录）；EDIR 解析 shell 片段四处复制（DRY 违背）；护栏全提示词级（无程序化 scope 校验器兜底）；深度耦合 Claude Code 专有机制，reporter 存在 mojibake 乱码。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度低但内容质量高**（0★/v0.1.2/2026-09-09/单人/无社区验证；命令级细节准确、护栏体系完整、CHANGELOG 迭代认真，dive verdict_reason）。痛点覆盖：#8（PTES 映射+合规注记）、#10（三变体报告模板）、#13（契约层）。 |
| 能否直接使用 | **🟡部分可用**：命令层/权限层跨宿主需全部改写（fork 只能得到提示词资产）；但 skills/*.md 知识束与 report-template.html（MIT）可直接复用为素材（dive verdict_reason）。 |
| 适用场景 | 外部授权 Web 交战的方法论骨架与语料来源；报告模板直接搬。 |
| 依赖 | Claude Code、约 25 个外部工具+SecLists、手工创建 settings.local.json 工具白名单、Burp/ZAP 人工侧配合。 |
| 限制 | 法律：authorized-first 叙事完备但无技术执法。许可证：MIT（Copyright 2026 cma1t）。架构：纯 Markdown 插件。维护：单人早期。 |

### P2.11 Claude-BugHunter

| 要素 | 评估 |
|---|---|
| 优点 | 24+ 类 hunt-* SKILL.md 统一模板（Crown Jewel→攻击面信号→方法论→payload 模式→根因→bypass→验证门→链推荐）——漏洞类分册的直接骨架；7 问验证门+4 门清单+never-submit 清单+条件有效升级表；OOB-Or-It-Didn't-Happen 门+Marker Discipline（盲打取证纪律+防误报基线）；hunt.sh 交战目录脚手架契约（文件即断点）；/pickup 断点续跑+跨目标模式记忆（tested_endpoints 差集+patterns.jsonl 按技术栈注入建议）；指纹→技能路由表。（dive/claude-bughunter.json reusable#1-#6） |
| 缺点 | 安全护栏全是文档承诺（/autopilot 宣称的 allowlist/audit/限速/熔断 grep 零实现）；悬空引用成体系（tools.memory_gc 模块、Stop hook、/scope 命令均不存在）；redteam-mindset 的「DO NOT STOP/AskUserQuestion=stall」与人工门禁哲学正面对撞（复用必须剥离）；深度绑定 Claude Code 私有生态；triage 退化为关键词包含匹配；「574+ 真实报告提炼」无法逐条核实（15 分册、不引编号）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度低**（2★/2026-05-21/社区关注极低，scan/agent-skills），本质是高质量提示词知识库而非可靠软件（dive verdict_reason）。痛点覆盖：#6/#7（模式库+路由）、#11（OOB 门）、#12（7 问门）。 |
| 能否直接使用 | **🟡部分可用**：运行编排层 ❌（悬空引用+平台绑定，端到端未验证贯通）；知识资产层 ✅（51 skills MIT，hunt-* 模板与 disclosed-reports 四段式条目可改写为 references 分册；须剥离反门禁指令，dive verdict_reason）。综合判 🟡。 |
| 适用场景 | references/vulnclass/ 分册的语料与结构母版；验证门与 marker 纪律的出处。 |
| 依赖 | Claude Code、install.sh → ~/.claude/、subfinder/dnsx/httpx/katana/gf/nuclei/ffuf 等 CLI（macOS arm64 上 dnsx/httpx 有段错误，cbh.py 已自实现兜底）、可选 Chaos API key、Burp 127.0.0.1:8080。 |
| 限制 | 法律：bug-bounty/红队授权语境（其 SOW/凭据纪律文案较好）。许可证：MIT。架构：知识束+740 行 stdlib CLI。维护：低关注。 |

### P2.12 open-sploit

| 要素 | 评估 |
|---|---|
| 优点 | Step-0 目标分类→skill 路由表（URL/OpenAPI/GraphQL/PHP 指纹→显式 skill 加载清单）；代理级 tool_instructions 声明执行底座（一条 wsl 前缀把工具环境固化到 agent 层）；MCP 运行时降级话术契约（探测失败优雅跳过+运行期给用户明确启动指引）；install.mjs 幂等配置合并（已存在键不动+跨目录去重）；hackerone skill 的 PoC 卡片+三态对抗验证门（VALID/REPAIRED/REJECTED）+report_validator 正则 lint；敏感数据台账 schema（六分类+finding 关联+sensitive_data_metadata.json）。（dive/open-sploit.json reusable#1-#6） |
| 缺点 | 安装即 YOLO（install.mjs 强制全 allow 权限+劫持 default_agent=offsec）；零状态契约（无交战目录/findings 落盘/断点续跑，长交战记忆全押对话上下文）；vendored 血统混乱（≥3 上游，hackerone skill 引用未发布的 coordination/Workflow 执行器，悬空死引用）；web 路由第一批即依赖未捆绑的商业 strix CLI；运行时 sudo apt install 自装缺失工具（无版本锁定无校验）。（dive anti#1-#5） |
| 现状覆盖度 | **成熟度极低**（npm v1.2.0 首发 2026-09、81 文件约 598KB、无 GitHub 仓库/issue/测试/CI、单人，dive）。 |
| 能否直接使用 | **❌仅借鉴模式**：纯提示词包（唯一代码是 158 行安装器）；工具底座硬编码 wsl -d kali-linux（Windows/WSL2 专属）+burp 检测仅 win32，macOS 环境核心路径直接失效；安全模型与人工门禁正面冲突（dive verdict_reason）。 |
| 适用场景 | 安装器工程与路由表的抄写源；hackerone 卡片规范（PoC 三态门+敏感数据台账）是我们 POC 契约的最佳参照（执行器需自研）。 |
| 依赖 | opencode、Windows/WSL2 Kali、npx（playwright/burp MCP）、隐形的 strix CLI（未捆绑）。 |
| 限制 | 法律：README 法律声明+各 skill RoE 文案（纯声明层）。许可证：包 MIT+vendored Apache-2.0（需保留署名/NOTICE）。架构：提示词安装包。维护：无仓库无社区。 |

### P2.13 ARL 灯塔

| 要素 | 评估 |
|---|---|
| 优点 | scope+黑名单双重静态校验两层防绕过（提交入口 get_ip_domain_list 校验并抛异常，执行层 portScan/resolver 再兜底过滤）；任务即文档状态机（task 集合 status 阶段字符串+service[{name,elapsed}] 耗时数组，$set+$push 原子更新）；数据源插件注册表（12+ 源每源一文件+config.yaml 逐源 enable/api_key，单源失败隔离）；工具能力探测降级（check_have_nuclei+_check_json_flag 参数兼容性探测）；扫描参数自适应（按端口数动态拼 nmap 参数）；单入口动作分发表（CeleryAction→函数 action_map）。（dive/arl.json reusable#1-#6） |
| 缺点 | 无断点续跑（restart_task 重置后整任务重跑，中途失败重复消耗配额）；状态散落十几个 Mongo 集合仅靠 task_id 弱关联（worker 崩溃任务可能永久停中间态）；安全历史差（默认 admin/arlpass、硬编码 md5 salt、2022-2023 系列未授权 RCE/SSRF 致官方仓库 2024 下架）；vendored python-nmap 是 GPL v3 代码拷入 MIT 仓库（照抄该文件有传染风险）；进度上报靠 sleep(5) 轮询旁路线程。（dive anti#1-#5） |
| 现状覆盖度 | **已停维护**（原 TophantTechnology/ARL 删除 404；镜像 Aabyss-Team/ARL 2.1k★/2025-07-16 社区续维护，另有来路不一修改版流传，scan/automation）。资产测绘功能本身完整（域名→子域→IP→站点→指纹→漏洞全流水线）。 |
| 能否直接使用 | **❌仅借鉴模式**：已归档下架+Python3.6/Celery/Mongo 重型服务与 skill 形态不匹配+默认凭据与历史 RCE 不可作运行时依赖；镜像有供应链风险（scan/automation：「直接引用镜像存在供应链风险，需要锁定哈希或自管 vendor」）。（dive verdict_reason） |
| 适用场景 | 国内甲方「一个授权主体→真实资产范围」的资产测绘思路参照；双层校验与插件注册表的模式源。 |
| 依赖 | docker-compose 五容器（web/worker/scheduler/MongoDB/RabbitMQ）、第三方数据源 API key（fofa/hunter/quake 等可选）。 |
| 限制 | 法律/供应链：镜像来源需哈希锁定；历史 RCE 不可暴露公网。许可证：MIT（tophant 版权）但个别 vendored 文件 GPL 需剔除。架构：五容器服务栈。维护：官方停更。 |

---

## P3 组合现有方案 vs 自研：差距分析

### P3.1 「最优组合」能覆盖什么

组合假设（从 P2 中取各场景最优件，全部为 dive 裁决允许的最大化用法）：

> **nuclei**（✅ 漏扫原语+ResultEvent）+ **Osmedeus**（🟡 recon 工作流引擎）+ **Strix**（🟡 自主 Web 深测 CLI 外挂）+ **PentestGPT legacy**（🟡 过渡期副驾）+ **Caldera**（🟡 AD/内网演练平台）+ **CEP/BugHunter/Threatswarm**（🟡 语料与模板素材）+ **SARIF/DefectDojo**（下游消费，scan/standards）

组合对 14 痛点的覆盖矩阵（●=组件内原生覆盖；◐=机制存在但需人肉/跨工具搬运；○=不覆盖）：

| 痛点组 | # | nuclei | Osmedeus | Strix | PentestGPT | Caldera | 语料包 |
|---|---|---|---|---|---|---|---|
| 时间 | 1 | ◐ | ● | ○ | ○ | ○ | ○ |
| 时间 | 2 | ○ | ●自家 | ●自家 | ◐新版 | ●自家 | ○ |
| 覆盖 | 3 | ○ | ○ | ● | ○ | ◐ | ○ |
| 覆盖 | 4 | ○ | ○ | ○ | ○ | ○ | ○ |
| 覆盖 | 5 | ○ | ◐diff | ○ | ○ | ○ | ○ |
| 知识 | 6/7 | ◐模板即知识 | ○ | ●28技能 | ●PTT | ○ | ● |
| 知识 | 8 | ○ | ○ | ○ | ◐ | ●ATT&CK | ◐PTES |
| 交付 | 9 | ◐ | ◐ | ● | ◐ | ○ | ○ |
| 交付 | 10 | ◐ | ◐ | ● | ○ | ○ | ◐模板 |
| 交付 | 11 | ◐matcher | ○ | ◐ | ●收据制 | ○ | ◐OOB门 |
| 一人 | 12 | ○ | ○ | ● | ● | ◐ | ● |
| 一人 | 13 | ◐dialer | ○ | ○prompt级 | ●校验器 | ●RuleSet | ◐ |
| 一人 | 14 | ○ | ◐on_error | ◐预算 | ◐轮次预算 | ◐cleanup | ○ |

关键读法：#4（认证后越权）一列全 ○ 是矩阵的空洞所在；● 集中在单组件内部，跨组件的 ◐ 全部需要人肉搬运——这正是 P3.2 「契约层不可行」判断的矩阵化表达。

### P3.2 对照 12 must-haves 逐条映射缺口

12 must-haves 取自 landscape §7.2（四位专家收敛结论）。逐条判定组合是否补齐：

| # | must-have | 组合覆盖情况 | 缺口判定 | 出处 |
|---|---|---|---|---|
| ① | phases.yaml 数据化状态机 | Osmedeus 有 workflow YAML 但绑定自家引擎；无跨工具阶段契约 | **缺**：无任何项目提供跨工具状态机数据契约 | expert/architect #1；dive/osmedeus |
| ② | 三层 scope 执法 fail-closed | nuclei dialer 仅自身流量；Strix/PentAGI prompt 级；Osmedeus 无；Threatswarm hook 有 fail-open 实洞 | **缺**：组合后每个工具一套口径，出口不收敛 | expert/ai-agent #3；dive/threatswarm anti |
| ③ | handoff+resume_kit 输出侧契约 | Strix compaction 是会话内摘要，非跨工具 handoff 工件 | **缺** | expert/ai-agent #1 |
| ④ | journal.jsonl 任务级续跑 | nuclei 模板级、Osmedeus 工件级（靠作者自觉写 pre_condition）、ARL 整任务重跑、Threatswarm/BugHunter 靠人重发命令 | **缺**：无统一任务粒度账本 | expert/ai-agent #2；各 dive state_management |
| ⑤ | creds.yaml/sessions/身份矩阵 | **零覆盖**：13 项目无一有 creds/session/role 实体与差分工作流 | **缺**（全行业空白） | expert/pentest #1 |
| ⑥ | POC 硬契约+独立重放门 | nuclei matcher 是检测级；Strix poc_script_code 无独立重放门；open-sploit 三态门执行器未发布 | **缺**：需自建四要素卡片+重放门 | expert/pentest #2；dive/open-sploit |
| ⑦ | 占位符网关全链路 | 仅 DarkMoon（GPL 不可搬码；且 vault 内存态重启即丢） | **缺**：须按模式自研清洁实现 | dive/darkmoon；expert/pentest #3 |
| ⑧ | findings schema 定稿 | nuclei ResultEvent 最接近但缺 auth_context/scope_check/dedup 语义；Osmedeus Vulnerability 有 FindingHash+Confidence 可借鉴字段 | **半缺**：字段拼装与统一 schema 需自建 | expert/architect #5；scan/standards gaps |
| ⑨ | 预算树+假设排序+coverage 负空间 | HBPGPT Limits 与 Strix coverage 各在自家进程内，无全局调度 | **缺**：跨工具预算与覆盖聚合层 | expert/pentest #4；expert/ai-agent #6 |
| ⑩ | 安装矩阵+供应链锁定 | 各工具自成安装体系；ARL 镜像断供风险；nuclei-templates 需钉 commit 验签 | **缺**：无统一分发与锁定层 | expert/devops #1/#3；scan/automation gaps |
| ⑪ | evals 改动门禁 | 无任何现成基准覆盖 engagement 生命周期/复现性/护栏 | **缺**：自建 evals/ | expert/ai-agent #4；scan/sota-bench gaps |
| ⑫ | cleanup+changes_ledger | Caldera cleanup 声明式存在但不保证幂等不验恢复；Stratus 生命周期契约是设计参照 | **缺**：无台账化回滚 | expert/architect #6；scan/adversary gaps |

**结论：12 条中 0 条被组合完整补齐（⑧ 半缺，其余 11 条全缺）。**「组合现有方案」在组件层可行（各件在其场景内确实最好），在**契约层**不可行——缺口全部落在「跨工具的状态、门禁、输出契约」上，而这恰是任何单项目都不提供的。

### P3.3 为什么不能直接组合

| 阻力 | 证据 |
|---|---|
| 集成成本≈重写 | Strix 引擎约两万行与 openai-agents/Caido/Kali 镜像强耦合，「把循环抽出来嵌进 SKILL.md 形态的工作量约等于重写」（dive/strix verdict_reason）；PentAGI 同理（dive/pentagi anti#2） |
| 许可证冲突 | DarkMoon GPL-3.0 传染（其 privacy 三件套与报告生成器恰是最想要的代码，「宜学模式不抄码」，scan/ai-agents）；ARL vendored python-nmap 为 GPL 拷入 MIT 仓库（dive/arl anti#4）；Sn1per 无开源许可文件（scan/automation）；CAI 无标准 LICENSE 需逐文件甄别（scan/ai-agents） |
| 架构不兼容（各自状态管理） | 五套真相互不认账：Strix agents.json+SQLite、PentAGI PostgreSQL+pgvector、Osmedeus 目录+SQLite 双写漂移、ARL Mongo 十几集合、Caldera 内存+pickle；PentestGPT agent 版再驱动 Claude Code/Codex 子进程形成 agent 套 agent（dive/pentestgpt verdict_reason） |
| 运行时异构 | Threatswarm/CEP/BugHunter 深绑 Claude Code 私有机制（slash command/agents frontmatter/install 到 ~/.claude），跨宿主「命令层与权限层需全部改写」（dive/claude-externalpentest anti#5）；open-sploit 硬编码 wsl 前缀 |
| 供应链风险 | ARL/水泽原仓库删除只剩来路不一镜像（scan/automation：「断供与投毒风险……需要锁定哈希或自管 vendor」）；nuclei-templates 持续合并存在投毒现实风险（expert/devops #3，nuclei 官方 ECDSA 签名正为此） |
| 维护风险 | skill 赛道「0-100★、单人维护、3-6 个月停更常见」（scan/agent-skills gaps）——组合件越多，烂尾面越大 |

### P3.4 自研的真实边界

自研 ≠ 造轮子。**只造三层，其余全部复用**（与 landscape §7.1 组件决策表一致）：

| 自研层 | 内容 | 复用什么 |
|---|---|---|
| 胶水层 | 交战目录契约（journal/state/assets/hypotheses/coverage/findings.jsonl 及 schema_version）+ 外部工具适配器（每工具一处调用模板/输出解析/降级链）+ Python driver（三后端调用 profile） | Osmedeus workspace 契约思想、nuclei ResultEvent 字段、ARL 资产模型、Strix 台账形态——全部模式级 |
| 门禁层 | 三层 scope 执法（egress 代理→hook→脚本）+ POC 独立重放门 + 出卡质量门 + 占位符网关 + 预算树 | Threatswarm exit-2 语义（修补 fail-closed）、PentestGPT 校验器（MIT 可直接改造）、DarkMoon 占位符模式（清洁实现）、HBPGPT Limits |
| 契约层 | findings.jsonl/POC 卡片/中文报告骨架/phases.yaml | nuclei 模板与 matcher schema、SARIF 指纹思想、DefectDojo hash_code、CEP report-template.html（MIT 文件级复用）、BugHunter/Threatswarm 语料（MIT 改写） |

**执行组件零自研**：nuclei 原样引入（CLI 子进程），nmap/ffuf/httpx 等原样调用（经适配器），Caldera/Strix 可选外挂。这既是工程经济学（13 项目里工程最厚的两块——模板生态与扫描引擎——已有 MIT 件），也是专家共识的必然推论：四位专家的 must-have 全部指向契约与执法层，无一条指向「重写扫描器」（landscape §7.2）。

---

### P3.5 外部基准证据：TSecBench 2026Q2（用户提供，事后增补）

腾讯云鼎实验室 TSecBench 首期横向测评（2026Q2，13 Agent × 4 模型 × 3 轮 = 156 份结果，63 题六能力域，武大/川大/清华/鹏城执行，三轮取优口径）为 P3 结论提供了独立的量化印证（数据：.research/dive/tsecbench-q2-2026.json）：

| P3 论断 | TSecBench 证据 |
|---|---|
| 现有产品无一可整体解决长链问题（P3.2 缺口映射） | **多阶段渗透成功率全行业 29.53%、完整解题率仅 8.33%**——13 个参赛 Agent 的共同短板；最优组合也只 90.54%（能力上限口径） |
| PentAGI 借鉴不采纳（P2.3） | PentAGI 排 **11/13（61.15%）**，被多个更轻量的编排方案超越——自研重型多 agent 框架不构成能力优势的外部证据 |
| 状态编排决定上限（P3.1/3.4） | 榜首 Cairn（90.54%）的架构标签正是「黑板+事实-意图图」——状态/事实中间层模式的赛场验证 |
| token 成本必须管控（P3.4 门禁层预算树） | 同基准下 token 消耗差 **30 倍以上**（CHYing 均值 27.92M vs Cairn 458.50M），且 CHYing 用 15.78M 拿到 85.14%——编排精简度直接换算成成本 |

## P4 方向选型论证

### P4.1 四条路线对比

| 路线 | 代表 | 优点 | 死穴 | 适用者 |
|---|---|---|---|---|
| A 纯工作流引擎 | Osmedeus、reconftw、AutoRecon | 确定性 100%（无 LLM 方差/成本）；断点缓存成熟（Osmedeus 工件即缓存）；单二进制分发 | 静态 DAG 不基于新事实重规划（scan/adversary：「计划多为静态 profile……重规划只能外挂」）；止步于「发现」，凭据/利用/横向无建模（scan/automation）；新攻击面=改 YAML 的手工劳动 | 方法论已固化、做常态化资产侦察的团队 |
| B 自研 agent 框架 | PentAGI、Strix、DarkMoon、HackingBuddyGPT | 端到端自主闭环；上下文/预算/压缩/去重等 agent 工程化最深（Strix 六模式） | 平台全家桶依赖（PG/容器/镜像）不可嵌入；自维护工具循环与 LLM 适配层长期成本高；与 coding agent 宿主职责重叠（「agent 里再起 agent」）；scope 多为 prompt 级 | 有平台化目标的团队/学术研究 |
| C 纯问答副驾 | PentestGPT legacy（三会话 copilot） | 人机混合越权风险最小；知识提示对转岗者学习期友好；零基础设施 | 人仍是执行瓶颈（自动化收益封顶）；legacy 伪持久化无法断点（dive/pentestgpt anti#3）；无结构化交付（报告/POC/复测全手工）；官方自认收敛性弱 | 完全过渡期/纯学习场景 |
| **D coding-CLI harness 上的 agent+skill（本报告选择）** | Threatswarm/CEP/BugHunter/open-sploit（雏形，全部 0-80★ 不成熟）+ 本项目 | 白嫖宿主的最强工程：agent 循环/上下文管理/文件编辑/子代理/MCP 全部现成；skill 可跨宿主移植；hook=天然门禁执法点；状态可完全落文件契约（宿主无状态绑架） | 生态不成熟（雏形项目单人维护、悬空引用、fail-open 教训频出——P2 已列）；三宿主 hook/权限语义异构需适配层（expert/ai-agent #5）；SKILL.md 有膨胀反例（Strix 548 行） | 一人红队（单人维护、单机、要复用编码 agent 生态） |

**选择 D 的决定性论据**：路线 D 的两个死穴（生态不成熟、语义异构）都是**可修复的工程问题**——前者由本项目的契约+门禁层修复（P3.4），后者由 assets/runtimes/ 适配层修复（expert/ai-agent must_have #5）；而 A/B/C 的死穴都是**结构性**的：A 无重规划能力、B 与单人资源模型冲突、C 无自动化上限。此外 D 是唯一让「转岗审计师源码优势」变现的路线——宿主编码能力可直接用于 POC 脚本编写、报告模板维护与 evals 迭代。

### P4.2 为什么宿主选 opencode/codex/DSH 这类 coding harness

1. **skill 可移植**：ai-security-arsenal 证明同一 skill 集可跑通 Claude Code/Claude Desktop/OpenCode（scan/agent-skills：「验证跨 agent 可移植层」）；Anthropic 官方 marketplace 确立插件版本化分发标准（scan/agent-skills）。skill 层中立化（无工具名/平台路径+可移植性 lint）即可三宿主复用（expert/ai-agent #5 处方）。
2. **工具生态**：MCP 已是事实工具总线——open-sploit 装 playwright/burp MCP（dive/open-sploit）、Strix 顶层 skills/ 示范 CLI 包装、msgrpc 已有社区 MCP 封装可被 LLM agent 直接驱动（scan/adversary patterns）。无需自建 provider/工具注册层。
3. **hook 门禁点**：这是路线 D 独有的执法支点——Threatswarm 的 PreToolUse exit-2 证明 hook 层可做到「模型不可绕过」（dive/threatswarm reusable#1），三位专家一致要求把 scope 执法放在 agent 循环外的确定性执行层（expert/architect #1、expert/ai-agent #3、expert/pentest #3）。DSH 的 sandbox/hook、opencode 的 plugin、codex 的权限配置即三层执法的第二层挂载点。
4. **避免 agent 套 agent**：PentestGPT 新版驱动 Claude Code/Codex 子进程被 dive 判为「职责重叠且依赖嵌套工程」——在 harness 内直接以 skill 形态存在是更薄的同构方案（dive/pentestgpt verdict_reason）。
5. **宿主迭代红利**：上下文压缩、子代理、预算控制等 agent 工程由宿主方持续迭代（Strix 在这些点上自研了整套，dive/strix），skill 层只锁契约不吃维护成本。

### P4.2.1 量化背书：Claude Code 在 TSecBench 的成绩

TSecBench 2026Q2 中 **Claude Code——零渗透专用代码的通用编程 harness——排 5/13（跨模型均值 72.30%），击败 8 个专用渗透框架**（含 PentAGI 61.15%、PentestAgent 45.95%）；配 Kimi K3 达 81.08%，token 均值仅 58.42M（效率前列）。分域能力：云攻击 100%、对抗规避 94.6%、**多阶段渗透 41.1%（全场第二，仅次于 Cairn 44.6%）**——通用 agent 循环 + 文件系统即状态的长链能力已超过绝大多数专用框架的自研编排。这是路线 D（coding harness 上的 agent+skill）目前最有力的外部定量论据；同时模型档位差 20+ 百分点（Kimi K3 是 11/13 Agent 的最佳搭档）也印证 P4.3「模型无关设计」与预算树并重的立场。

### P4.3 技术栈选型表

| 层 | 选型 | 备选（及放弃原因） | 为什么 |
|---|---|---|---|
| 状态存储 | 交战目录文件契约：journal.jsonl（append-only 第一真相）+ state.json（派生视图，revision 乐观锁+temp/rename 原子写）+ assets/hypotheses/coverage 台账 | SQLite（PentAGI/Threatswarm 式，PentestGPT 用得最好但跨运行时不可读）；PostgreSQL+pgvector（PentAGI：全家桶根源）；MongoDB（ARL：服务栈重）；内存+pickle（Caldera：非优雅退出丢状态） | 跨三宿主可读可 diff、天然审计、无服务依赖；「状态不得混居程序文件」（expert/devops #1）；journal 第一真相可全量重建（expert/ai-agent #2） |
| 门禁 | 三层执法：deny-by-default egress 代理（scope.yaml 编译为 ACL+DNS pinning+OOB 显式列入+工具基础设施白名单）→ 各宿主 hook 适配（fail-closed，Threatswarm exit-2 语义修补版）→ scope-guard 脚本兜底；POC 独立重放门+出卡质量门 | 纯 prompt（Strix/PentAGI/Osmedeus 已证伪）；仅 PreToolUse 单点（Threatswarm fail-open+变量绕过实测洞）；仅 dialer 层（nuclei 只覆盖自身流量） | 「模型可绕过的校验等于没有」（expert/architect #1）；最弱后端决定安全水位（expert/ai-agent #3）；canary 证等强 |
| 扫描组件 | nuclei adopt（CLI 子进程，模板钉 commit+ECDSA 验签）+ 适配器契约接入 nmap/ffuf/httpx/katana 等（每工具调用模板/超时/输出 schema/降级链） | Osmedeus 引擎外挂（recon 重场景可选）；ARL 流水线（停维护+镜像风险，弃）；自研 scanner（无必要，弃） | 13 项目唯一 adopt 裁决（MIT+模板生态+ResultEvent）；适配器杜绝「某分册发明绕过门禁的裸 curl」（expert/devops #6） |
| 报告生成 | 服务端确定性重建：findings.jsonl → 中文报告固定章节骨架（授权/方法学/覆盖度/风险分级/整改+复测）；CEP report-template.html（MIT）复用；等保映射人工占位 | LLM 自由生成（DarkMoon「DEFINITIVE FIX」注释明言不信任 LLM 报告体）；商业报告平台（无中文合规开源件，scan/standards） | 中文合规无结构化先例必须自建骨架；确定性重建使报告可从存储重复再生（dive/darkmoon「output_report」） |
| 评测 | evals/：docker-compose 固定靶场（认证后 Web+内网段+已知漏洞安装包）+金标 ground-truth+指标集（精确率/召回率、POC 机器复放率、scope canary 零容忍、kill -9 续跑保真度、报告 schema lint+脱敏检查），改动门禁化 | Cybench/NYU CTF（单点 CTF 无 engagement 生命周期，scan/sota-bench gaps）；HTB AI Range（闭源）；inspect_evals（协议标准化可借鉴，非渗透专用） | 「改一段提示词可能悄悄破坏门禁，唯一发现方式是下次真实交战翻车」（expert/ai-agent #4）；退出码对齐 Strix 0/1/2 |
| LLM 接入（补充层） | 宿主自带模型路由（DSH/opencode/codex 原生） | LiteLLM 自建（Strix/PentAGI 模式：自维护 14 家适配器） | 宿主已解决 provider 层与审批语义；skill 层不重复造（P4.2 论据 5） |
| 执行底座/分发（补充层） | 本机工具+tools.lock（版本+sha256/签名+per-OS 渠道）+uv lock；单权威目录+符号链接四运行时安装矩阵；交战区移出 skill 树（~/redteam-engagements） | Docker Kali 容器（Strix/PentAGI/DarkMoon 模式：容器缺即 exit 1、平台耦合，单人单机过重） | 「运行时绝不自动安装缺失工具」（expert/devops #3）；交战状态与 skill 树混置会在 git pull 时冲突（expert/devops #1） |

---

### P4.4 选型结论

一句话结论：**宿主选 coding harness（DSH/opencode/codex 三后端），形态选 agent+skill，组件选「nuclei 唯一 adopt+适配器接入其余工具」，自建收敛在胶水层/门禁层/契约层三层**。该结论由三条独立证据链交汇：①P3.2 显示组合方案 12 条 must-haves 全缺且缺口全在契约层（组件层无缺口）——自研重心被迫落在契约；②P4.1 显示其余三条路线的死穴均为结构性缺陷，仅路线 D 的缺陷可由①的自建层修复；③P4.2 显示路线 D 的三个决定性支点（skill 可移植/MCP 生态/hook 执法点）在调研中均有正面存在证明（ai-security-arsenal 跨宿主、msgrpc MCP 封装、Threatswarm exit-2），无一是未经检验的假设。

---

## P5 风险与限制声明（本报告结论的适用边界）

1. **数据源边界**：本报告基于 13 项目的**静态源码级分析**（dive 明确「只读源码分析，严禁执行」）与文档/issue 核实，未对任何项目做运行时实测；各项目的能力声称（如 BugHunter「574+ 真实报告提炼」）存在无法逐条核实的先例（dive/claude-bughunter anti#5），本报告对这类声称均已降级处理。
2. **时间快照**：星数、活跃度、维护状态均为 2026-09-19/20 快照（scan 各文件记录的最后提交日期）；skill 赛道项目 3-6 个月停更常见（scan/agent-skills gaps），P2 成熟度判定会随时间漂移，引用时应复核上游仓库现状。
3. **定性判定的局限**：P1 痛点分析中的占比类表述（如「报告耗时>测试耗时」）为读者画像的经验前提，数据源未提供量化统计；本报告以其定性证据链（专家判语+工具形态缺位）支撑，不构成量化结论。P2「现状覆盖度」是工程判断而非基准测试结果——评测基准本身在赛道上缺位（scan/sota-bench gaps）。
4. **供应链与镜像风险**：ARL、水泽原仓库已删除，现存镜像来源不一（scan/automation「断供与投毒风险」）；任何按 P3.4 复用外部组件的实施都必须执行 tools.lock 锁定与哈希/签名校验（expert/devops #3），否则本报告的复用结论不成立。
5. **法律与合规边界**：本报告讨论的全部工具与模式仅适用于**书面授权**的渗透测试/红队演练场景；GPL 项目（DarkMoon、ARL vendored 文件）只借鉴设计模式、不搬代码，实施时应保持清洁实现并保留许可审计记录；等保/监管相关结论（中文报告骨架）以官方模板为准，本报告仅给结构建议，不构成合规意见。
6. **适用对象边界**：P1 痛点画像与 P4 选型针对「一人红队+单机+黑盒外部与认证后 Web 为主+中文交付」场景；多人团队、常态化资产运营、纯 CTF 竞技或物理/无线/社工方向不在论证范围内，结论不可外推。
7. **结论一致性**：12 must-haves 与专家 approve-with-changes 裁决基于评审时点的设计简报（landscape §7.2）；若需求画像变化（如转向内网渗透为主），P3/P4 的选型结论需按相同框架复审。
8. **TSecBench 口径**：P3.5/P4.2.1 引用的测评数据为**三轮取最高成功率**口径（能力上限，非典型运行均值），且仅反映测评期间的模型版本与 Agent 提交实现；引用时不得当作平均表现或产品背书（报告方免责声明明示）。

---

## 附录 A：痛点 × 机制证据索引（P0/P1 判定的出处回查表）

| 痛点 | 支撑「已解决部分」的正例 | 支撑「剩余缺口」的判语 |
|---|---|---|
| 1 侦察占比 | Osmedeus 双层编排（dive/osmedeus「architecture」）；ARL 全流水线（dive/arl） | scan/automation gaps「跨阶段机器可读衔接靠人工粘合」 |
| 2 上下文/并行 | Threatswarm worktree 隔离（reusable#6）；Osmedeus workspace 契约（reusable#3） | scan/ai-agents gaps「长程记忆缺失…几乎没有项目定义结构化外部记忆契约」 |
| 3 负空间 | Strix coverage 四态+最后警告（reusable#1）；Caldera skipped_abilities 原因码 | expert/ai-agent #6「ARL 缺失即静默跳过=谎称测过」 |
| 4 认证后漏测 | （无正例——全空白） | expert/pentest #1「state 与契约里没有 creds/session/role 任何实体」 |
| 5 复测回归 | Osmedeus asset/vuln diff（「output_report」） | scan/agent-skills gaps「verify-fixed 没有项目系统性支持」 |
| 6 语法负担 | Strix load_skill（「architecture」）；HBPGPT AD 纠偏规则（「tool_integration」） | expert/devops #6 适配器缺位的后果（裸 curl 漂移风险） |
| 7 学习曲线 | BugHunter hunt-dispatch（reusable#6）；DarkMoon 技术栈子代理；open-sploit Step-0 | scan/agent-skills gaps「单人维护 3-6 个月停更常见」 |
| 8 转岗断层 | CEP PTES 映射+CVE 联网核验（reusable#6）；Caldera fact 管道（reusable#1） | scan/standards gaps「中文合规报告无结构化先例」 |
| 9 证据丢失 | Threatswarm 双审计流（reusable#4）；Strix http_exchange_ids | scan/standards gaps「POC 证据在所有标准中都不是一等公民」 |
| 10 报告耗时 | DarkMoon 服务端确定性重建（「output_report」）；nuclei multi_writer | expert/pentest #6 中文报告章节未钉死 |
| 11 POC 复现 | PentestGPT 证据收据制（「output_report」）；BugHunter OOB 门（reusable#3） | expert/pentest #2 复现四要素判语 |
| 12 无复核 | HBPGPT task_solved 核查；Strix counterevidence；BugHunter 7 问门 | expert/ai-agent #6「LLM 声称验证成功即可出卡=纸面发现入口」 |
| 13 授权自守 | Threatswarm exit-2（reusable#1）；PentestGPT 校验器（reusable#5）；Caldera RuleSet（reusable#6）；ARL 双层校验（reusable#2） | dive/threatswarm anti fail-open+变量绕过；expert/ai-agent #3「最弱后端决定安全水位」 |
| 14 疲劳误操作 | DarkMoon execution_guard（reusable#4）；HBPGPT Limits 树（reusable#2）；Caldera cleanup 逆序 | scan/adversary gaps「清理与回滚不完整…不保证幂等」；expert/pentest #4「低价值面烧时间」 |

---

**附：本报告数据文件索引**（与 landscape §8 一致，全部在 `.research/`）：dive/{nuclei,strix,pentagi,pentestgpt,hackingbuddygpt,caldera,osmedeus,darkmoon,threatswarm,claude-externalpentest,claude-bughunter,open-sploit,arl}.json；scan/{ai-agents,agent-skills,automation,adversary,sota-bench,standards}.json；expert/{pentest,ai-agent,architect,devops}.json；digest.json。

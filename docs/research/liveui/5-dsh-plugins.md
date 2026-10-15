# DSH 红队插件双雄源码解构报告（dsh-redteam-mode × SeaOf0/dsh-redteam-model）

> 分析对象：
> A) `dsh-redteam-mode@0.13.1`（npm，作者 jueze，MIT，2026-10-12）@ `…/ai-assisted-security-verification-platform/dsh-plugins/dsh-redteam-mode`
> B) `@dsh-external/dsh-redteam-model@1.1.1`（github SeaOf0/dsh-redteam-model，MIT）@ `/tmp/drm`
> 分析日期：2026-10-16 · 分析者：探隐委托子代理
> 证据基础：
> ① **A 全量直读**：package.json/DISCLOSURE/cordis.patch.yml(434 行)/lib/index.js(232 行) 全文；store-core.js(5,477 行)/tools.js(1,922 行)/schema.js(1,196 行)/score-rules.js(934 行)/client.js(4,175 行)/ui.js(807 行) 结构化抽样（DDL 全量、56 工具名全量、得分点定义、角色常量、控制台 tab 表、OPS 分发）；presets/redteam/agent.cordis.yml 人设全文；15 个技能 frontmatter 全量；
> ② **B 骨架逐目录读**：README(230 行)/DEPLOY.md/cordis.patch.yml(3,824 行，10 条 preset 声明行全数定位)/src/*.ts(2,611 行，manager 函数面全量)/17 个 plugins/*/lib 结构+关键文件（stage-gate GATES、sec-enforce guard、route-boost 信封、scanner-tools registry、attack-atlas taxonomy、refusal-guard/trace-vault README）；modes/ 十模式 preset.yml+agent.cordis.yml(3,728 行) 抽样（pentest persona 全文、ad-playbook 子代理编排章全文、router-playbook 路由表全文、pentest-playbook 通道阶梯章）；refs 计数（十模式共 2,078 文件）；kali-mcp-server（156 个 .py / 80,671 行）mcp_server.py 全头+agents/core/mcp_tools 结构。
> 前序输入：`0-dsh.md`（dsh 宿主源码报告，双桥判决）——本报告第四节与之合流。
>
> 只读纪律遵守声明：对两个插件目录全程只读（sed/grep/awk/head/wc），零 git 操作、零 npm install、零 dsh plugin add，未触碰运行中宿主。

---

## 一、两插件架构解构

### 1.A dsh-redteam-mode ——「自包含厚插件：事实库 + 控制台 + 六角色预设」

**cordis.patch 声明结构**（cordis.patch.yml，434 行）——五段式：

1. **迁移段**：两条 `- id: + disabled: true` 精确关闭预发布期旧行（redteam-store/redteam-ui 指向旧独立包）——id+name 双匹配才生效，新机零副作用。头注释把「`- insert:` 是追加语义不按 id 去重，撞上即 boot 失败 duplicate loader entry」的坑写成文档（L3-14）。
2. **自举行**：`redteam-mode` → lib/index.js（装预设到用户根 + 落 setup.sh + ctx.provide('redteamMode', paths)）。
3. **资产库行**：`redteam-mode-store` → 发布进程级服务 ctx.redteam，config `root: !!js dshHomePath('redteam')`。
4. **控制台行**：`redteam-mode-ui` → host 半侧 HTTP 桥；浏览器半侧靠 package.json `dsh.client.platform=web` 被前端加载器发现。
5. **预设声明行**（`>>> preset-redteam declaration >>>` 生成区，tools/build.mjs 从 presets/redteam/ 生成，禁手改）：`@deepseek-ai/dsh-agent-preset` 一行，内嵌整份 agent.cordis.yml——persona（红队指挥人设 100+ 行）+ redteam-tools + 标准工具行（bash/fs/search/jobs/skill/goal/plan-mode/compaction/delegation/ask-user/todo/web）。两处关键 config：skill-filesystem `includeDefaultRoots:false` + customSkillDirs=`[$DSH_HOME/skills, 包内 skills/]`（用户配置优先于随包模板，防 VPS 地址被占位符覆盖）；tool-subagent `toolFilter.deny:[subagent_fork,workflow,ralph] + maxDepth:1`（**子智能体物理叶子化**——从工具目录里摘掉委派工具，比提示词劝阻硬）。

**资产库形态**（store-core.js + schema.js，零外部依赖，`node:sqlite` DatabaseSync）：

- 每靶标一个 SQLite：`$DSH_HOME/redteam/engagements/<靶标>/`（事实库 + `runs/` 证据 + `agents/<code>.md` 六份可编辑角色提示词 + 攻击文件目录）；跨靶标共享 `knowledge.db` + `pocs/`（POC/EXP 知识库，先查库再联网/手搓，验证有效回填脱敏）。
- **13 张表**：scan_run / segment(C 段) / asset(含 test_status、priority/potential/assess_reason 易打性评估列) / asset_name / port(含 url/title) / service / fingerprint / observation(通用观测) / edge(实体关系图) / tag / vuln(含 gained、found_by_agent) / score_point / score_hit；另有 ASSET_FTS_DDL + POC_FTS_DDL 两张 FTS5 虚拟表——**编译期能力探测降级**（HAS_FTS5 probe：Node 22.14 无、22.23 有；缺席自动 LIKE，`REDTEAM_NO_FTS5=1` 可强制走降级供 CI）。
- 内外网判定写进 SQL 片段（RFC1918+回环+链路本地+CGNAT→internal），资产视图按内外网分组。

**评分引擎**（score-rules.js，934 行，自述「本项目最该单独读的一份代码」）：`applyScoreCaps` + `evaluateScoreBoard` 是**唯一实现**——「面板/报告/攻击链三处总分必须一致，三处各写一遍必然漂移成不同口径」。得分点数据模型：rule（规则号，同 rule 共享上限）/ tier（档位）/ cap（累计上限）/ dedup_scope（**service 同资产同端口只算最高一条 / system 同系统只算最高权限一次 / target 整目标一次 / none 按台累加**）/ builtin 标志位（内置点用户只能启停、自建点可任意编辑且绝不被播种逻辑清除）。默认得分点严格按《突破入侵类得分规则》25 条规则展开（DEFAULT_SCORE_POINTS，sp() 工厂，如「域名控制 50/20 分上限 400」「服务器普通 10/管理员 50 上限 600」「同一主机只按最高权限计一次」）。两条防刷分判据：`ACCOUNT_POINT_CODES`（自助注册账号 self_created=true 不计分）与 `TUNNEL_ENTRY_KINDS`（**隧道必须跨越靶标边界才算突破**：target-outbound/target-http/target-agent 合法，self-only「只在自己 VPS 上开的代理」不算——返回 null 时 UI 显示待确认）。

**UI 挂载**（client.js 4,175 行手写 bundle + ui.js 807 行 host 半侧）：

- 浏览器半侧：`window.__ModuleLoader__.load({id:'dsh-redteam-mode', factory})`，工厂内**手写 React（h = createElement，无 JSX 无构建）**，只用平台 seed 的 react 与 ctx.slots——基座外零依赖。
- 挂载点：`shell.overlay` 根作用域槽位注册 rt-dock 常驻右侧坞（9 个 tab：资产测绘/智能体/会话隧道/漏洞战果/攻击链/得分目标/报告/知识库/技能库）+ `sidebar.footer.action`（左栏底入口）+ `conversation.session.header.utilities`（会话头入口）；CSS 用 :has() 兼容新旧两代 details/rightbar 折叠属性名。
- 通信：**不走 typert/@Remote，host 半侧注册具名路由 `POST /redteam/api`**（注释自述理由：保持零外部依赖，具名路由是最小且稳定的接缝；Origin/Host 校验防跨源；8MB body 上限）。会话→靶标关联双保险：落盘绑定表 + **会话标题反查兜底**（squashName 把名字压成「只留字母数字汉字小写」的可比较键，解 ~hex 转义，命中多个取最长名）。
- 会话隧道 tab 含连通性**真实探测**（host 侧 TCP/HTTP 发起，probeSessions 走 dispatchAsync）。

**agent 编排模型**：**指挥官-执行者二级**。主会话=plan（指挥），只做四件事：计划/派活/核对回报/汇报；「不动手：不扫描不爆破不利用」。五个执行角色：recon（只收集不碰漏洞）/ assess（逐条评估易打性落库）/ vuln-scan（先查库避免重复→Nday 优先→前端接口未授权）/ exploit（先服务器权限+实测 WebShell 用户可连→立刻建 suo5 隧道实测可达内网）/ internal（**递归指挥**：用隧道依次拉起前四角色，gogo 铺面+fscan 打点，每发现新网段再跑一轮直到无新增）。并发硬约束：默认 3、用户可配、`redteam_agent_slot(action=acquire/status)` 占位、被拒不重试。**汇报纪律**（省 token 硬要求）：只有「得分了/新资产/要用户出手/阶段推进或硬失败」四种情况才说话，报增量不重述，其余「一个字都别说，安静派下一个」。

**工作流组织**：单预设单指挥线，阶段推进靠 persona 文本纪律（五阶段：信息收集→互联网资产权限→边界突破→内网资产权限→靶标权限），无运行时门禁——「每步结束后先核对落库数据再派下一步」全靠提示词。技能=纯 Markdown 操作手册（15 个，frontmatter：name/description/whenToUse/**role**（归属哪个角色）/enabled），由 DSH 原生 skill 体系加载；攻击链技能（隧道/凭据/WebShell/反弹 Shell/横向）**刻意拆出 npm 包**放 Release 附件 toolkit.tar.gz（v0.12.0 起，见 DISCLOSURE 对 npm dual-use 政策的合规声明：本包只含编排与事实库，不含利用代码、不替用户下载工具）。

### 1.B SeaOf0/dsh-redteam-model ——「workflow-first 插件联邦：十模式 × 四层资产 + 十七运行时治理插件 + 可选厚 MCP 执行面」

**哲学**（README 自述）：「一味的给 AI 投递 knowledge……没有 workflow 去引导把控……非常浪费 token 甚至陷入死胡同」「**不断完善 workflow，用 workflow 的方式尽可能补足缺陷；高效+真实是核心**」「dsh 在安全工作这方面的设计实际上是有限的，只能从 playbook 中去设计，**本身插件的载体还是 dp-harness 本身**」「在反拒绝上，harness 相比 claude/codex 原生 hook……真的太 easy 了」。设计原则一句话：**文本纪律（persona/playbook）+ 运行时强制（插件）双层防线**——模型不能自评门禁（结构校验必须是工具调用）、语义门禁归独立复核员、关键发现双签、一切判定落审计 trail。

**cordis.patch 声明结构**（3,824 行）：11 条 insert——1 条 `@dsh-external/dsh-redteam-model` 管理器行（host 半侧 loopback RPC + 浏览器 Redteam Manager 设置页）+ **10 条 `preset-<id>` 声明行**（redteam/pentest/code-audit/binary-analysis/attack-defense/av-evasion/incident-response/cloud-security/ctf-solver/asset-mapping），每条内嵌该模式 agent.cordis.yml 全文（persona+标准工具行，形态与 A 的预设行同构——都从 dsh 官方 standard 预设复制改造，注释里 realm/isolate 论述一字未改，证明两作者读的是同一份上游模板）。**preset 平面工具**直接写进相关预设行：`@dsh-external/dsh-scanner-tools` 挂进 5 个模式（pentest/attack-defense/cloud-security/ctf-solver/asset-mapping）、`dsh-semgrep-audit` 挂进 code-audit——其余模式不可见即分层正确。**其余 16 个宿主平面插件不在随包 patch 里**，由设置页管理台/deploy.mjs 按需写入 profile（插件路径一律指向源码树 plugins/，link 依赖+bundle 声明只增不改、写前备份）。

**modes/ 骨架**（逐目录读）：每模式四层资产——preset.yml（roster 名/描述，redteam order:0 置顶）+ agent.cordis.yml（362-408 行/模式：persona 前缀=角色认识论+表达纪律+注入纪律+目标侧零破坏+铁律，英文主文+中文关键条）+ skills/<mode>-playbook/SKILL.md（140-1,070 行作战手册，十模式共 5,055 行）+ refs/（外部知识库索引化，规模：code-audit 1,331 篇 > binary-analysis 324 > ctf-solver 126 > code-audit 之外 code-audit>pentest 108 > av-evasion 92 > cloud-security 75 > attack-defense 65 > incident-response 50 > asset-mapping 4 > redteam 0——**主模式零 refs，知识靠八 playbook**）。`shared/skills/` 四个跨模式技能：ecosystem-cooperation（跨平台执行公约）/ independent-review（独立复核员）/ red-team-command-doctrine / redteam-boundary-policy；av-evasion 独有 `lab/` 12 个可执行实验目录（syscall-direct/amsi-patchless/webshell-langs/memory-shells/c2-profile…）。

**十七运行时插件**（plugins/，宿主平面为主）分五类：

- **门禁/强制**：dsh-stage-gate（GATES 表：八模式 32 道阶段门，每门=结构 checks（file 存在/markers 字面标记/table 行列数/hexHash/provenance 哈希五类）+ manual 语义项归复核员；判定写 gate-log.md）；dsh-sec-enforce（用 dsh 原生 `ctx.tools.guard()` pre-execute 缝做**确定性拦截**：reportGate 报告门未 PASS 禁写 reports/、writeBoundary 写限制工作区、dangerousOps 高危命令特征拦+指路审批、rateDiscipline 裸奔扫描限速拦+给修法；askGate 把「可逆变更类」升级为宿主原生人工审批；KILL 标记文件全局熔断（touch 即停、删即恢复））。
- **逐轮治理**：dsh-route-boost（`ctx.systemPrompt.context()` 动态节，每步装配现场求值：最新人类输入→阶段推断→渲染信封 ≤1,600 字符——mode/phase/gates/review 双签/boundary/evidence 等级/refs 指针；**阶段粘滞**（裸「继续」不重置）+ **变化才投递**（同阶段零 token）；operation-state.json 未收口时注入恢复行）；dsh-refusal-guard（三级检测器：38 条强短语全文+弱词仅头部 150 字+软拒绝句式任意位置，工具轮豁免；**升级梯**：一级一次性重锚（附原请求摘录）→二级纠偏注记+inbox 自动重试→三级落 refusal-audit.md 交人工后静默；措辞正向化——刻意不用 never refuse 类越狱腔，实测反升拒答率）；dsh-auto-advance（subagent 返回且意图台账有未收口方向时注入推进提醒，三护栏防骚扰）。
- **过程/记忆**：dsh-trace-vault（监听 session/event 的 tool/call+tool/result 按 callId 配对落 SQLite（~/.dsh/trace-vault/traces.db，args 截 8K/result 截 32K/retention 14 天/上限 5 万行），模型工具 trace_search/trace_get/trace_recent 跨 compaction 检索；失败归因信封：近 30 分钟 blocked 聚集≥2 次投一行）；dsh-campaign-memory（跨会话打法沉淀，热度×30 天时间衰减排序，检测指纹 30 天/目标指纹 180 天自动退场）；dsh-redteam-results（九模式跨会话成果聚合 SQLite + 五板式成果页）。
- **执行工具**：dsh-scanner-tools（preset 平面，13 工具声明式注册表：nuclei/httpx/ffuf 三封装+nmap·masscan·subfinder·gau·whatweb·wafw00f·dirsearch·sqlmap·nikto·hydra·impacket·netexec·crackmapexec；**六节点工具调用阶梯**（本机→MCP→已装替代→MCP 备选→询问安装→脚本）；保守默认速率（nmap --max-rate 1000/nuclei -rl 15/httpx -rl 25/ffuf -rate 50）+显式覆盖留痕；**防盲打**：主动扫描须目标已登记 assets.md；绝不自动安装）；dsh-semgrep-audit（离线规则集 java 自建 402/oss 1,080 条，命中≠漏洞双写对账）；dsh-hunter（FOFA/Hunter/Quake 三平台统一 DSL 转语法+积分限额感知+一键实测流水线）；dsh-webshell-mgr（生成器→协议识别连接→命令/文件/数据库操作，payload-src + mcp/ 双形态）。
- **编排/可视**：dsh-product-subagents（补注册 provider:claude-code/codex——**无头 spawn 本机 CLI**，模型后端随 CLI 自身配置，不同源=异构双签；不传凭据只传 prompt）；dsh-attack-atlas（八模式攻击面图谱：**排序即方法论**的类目体系（战场分区×战术列×子项，列序=凭据优先→入口→核心挖掘→专项），四态点亮 tested-found/tested-clear/na/budget-stop，**按目标分账**互不覆盖，双击子项=派单进当前会话自动带目标锚定+refs 手册；自定义工作方法论画布+闭环五查）；dsh-mode-group（会话选择器两级化：九专业模式折叠子菜单）；dsh-session-pulse（任务进度 chip+子代理目录抽屉+提示词栏）。

**管理器**（src/，2,611 行 TypeScript）：manager.ts 1,668 行——scanModes/scanPlugins/deployModes（空目录整体链接 vs 已有 .agent-presets 写实体副本，备份成 .bak-时间戳绝不删除）/installOne/uninstallOne/updateAll/reconcileProfileBundles（自愈被旧版写错的 bundle 声明）/healPresetPlanePlugins/normalizePresetComposition（**按运行宿主实际引擎包改写 workflow 行**——dsh-workflow-ptc vs 旧 dsh-workflow-worker-thread）；OperationQueue 落盘 `.dsh-redteam-model-operations.json`（重启时未完成任务标中断）。AGENTS.security.md（反拒绝兜底规范）部署为 `~/.dsh/AGENTS.security.md` 专属命名空间，**仅经 route-boost global-agents 注入十个安全模式会话**——早期版本曾装全局 AGENTS.md 造成跨模式语境污染，升级自动收尾为备份（版本治理自觉的实证）。

**kali-mcp-server**（deploy/assets/，156 .py / 80,671 行，可选部署件）：Python FastMCP 全家桶，streamable-http :8765（`--allowed-host` 防 DNS 重绑定，服务无认证仅限隔离内网）。三重身份：① mcp_tools/ 22 个注册模块（v2/v3/vuln_db/recon/ai_session/code_audit/apt/ctf/scan_workflow/deep_test/browser/pwn/adaptive/assessment/misc/chain_mgmt/pentagi_bridge/llm_react/session/kali_extended/advanced_ctf/vuln_mgmt）把 Kali 260+ 工具封装为结构化 MCP 工具，执行器带并发上限（默认 4）与超长输出截断；② agents/ **四族 17 个智能体**（information_gathering: recon/subdomain/web_recon；vulnerability_discovery: vuln_scanner/web_vuln/auth/network_vuln/vuln_verifier；exploitation: exploit/lateral/privilege；specialized: pwn/crypto/forensics/code_audit/source_code/code_analyze）+ BaseAgentV2（能力描述/负载报告/MeshMessageBus）+ core/ 50 余模块（agent_coordinator/scheduler/registry、decision_brain、llm_brain、knowledge_graph、chain_manager、task_decomposer、broad_attack_orchestrator、deep_attack_engine、ctf_agent_framework…）——**一个住在 MCP server 里的完整多智能体平台**；③ diggers/ 8 个漏洞挖掘器（sqli/xss/rce/文件包含/上传/提权/pwn）。依赖 anthropic/openai SDK+pydantic+aiohttp+flask——与 dsh 侧插件零依赖风格完全相反。**与 dsh 的接线只有一根 URL**：mcp-studio 挂 `http://<kali-ip>:8765/mcp`，playbook 把它定位为「通道降级链的第二节点」（本机缺工具→走 kali MCP）。

### 1.C 对照速览

| 维度 | A dsh-redteam-mode | B dsh-redteam-model |
|---|---|---|
| 插件数 | 1 个自包含 npm 包（内含 3.5 模块） | 1 管理器 + 10 预设 + 17 运行时插件 + 可选 kali-mcp |
| 载荷重心 | SQLite 事实库+评分引擎（数据层） | 治理插件群+playbook 方法论（纪律层） |
| cordis.patch | 434 行 / 5 段 | 3,824 行 / 11 条 insert（预设 10 + 管理器 1） |
| 事实存储 | node:sqlite 13 表+FTS5+knowledge.db，每靶标一库 | trace-vault/campaign-memory/results 各自 SQLite；作战态用 Markdown 台账（gate-log/enforce-log/evidence-index/coverage-matrix）+ operation-state.json |
| UI | rt-dock 9 tab 常驻右侧坞（shell.overlay 槽位） | 设置页管理台+成果页+图谱+会话面板（多插件分散挂载） |
| agent 编排 | 指挥官+五执行角色（subagent spawn，叶子化） | 总控主会话+workflow 扇出+ralph 试错+独立复核员+claude/codex 双签 |
| 工作流载体 | persona 文本纪律（无运行时门禁） | playbook 文本契约+stage-gate 结构校验+sec-enforce 确定性拦截**双层** |
| 依赖 | 零（node: 内置） | 宿主侧零运行时依赖；kali-mcp 重依赖（anthropic/openai/flask…） |
| 合规姿态 | DISCLOSURE+dual-use 声明+攻击技能拆出 npm 包 | 免责声明+AGENTS.security.md 反拒绝规范（争议性最强点） |

---

## 二、功能与成熟度（1–5）

### A dsh-redteam-mode@0.13.1（约 1.8 万行）

| # | 功能域 | 细目 | 分 | 依据 |
|---|---|---|---|---|
| 1 | 资产事实库 | 13 表+FTS5 降级+内外网 SQL 判定+每靶标一库+跨靶标知识库 | **5** | schema.js/store-core.js；「界面看到的/智能体查到的/命令行验的同一份实现」 |
| 2 | 评分引擎 | 25 规则/rule 封顶/四档 dedup_scope/自建账号不计/同服务封顶/隧道边界判定，唯一实现防口径漂移 | **5** | score-rules.js（自述+结构印证） |
| 3 | 工具面 | 56 个 redteam_*（engagement/preflight/asset/vuln/credential/webshell/tunnel/chain/score/poc/report…） | **4** | tools.js 全量工具名；覆盖全但均为记录/查询/判定类，执行面靠 bash+技能 |
| 4 | 控制台 UI | 9 tab 常驻坞+会话头/侧栏入口+全屏模式+连通性真实探测+标题反查兜底 | **4** | client.js/ui.js；手写 React 无 JSX 工程克制，但 CSS :has() 兼容 hack 多、4,175 行单文件 |
| 5 | 角色编排 | 六角色+槽位并发+物理叶子化+回报核对纪律+增量汇报 token 纪律 | **4** | persona+cordis.patch toolFilter；纪律全在提示词，无运行时校验 |
| 6 | 技能库 | 15 技能 frontmatter（role 归属）+preflight 可用性判定+用户目录优先 | **4** | skills/*+skill-availability.js |
| 7 | 攻击链执行技能 | 工具箱被拆出 npm 包（合规代价） | **2** | README v0.12.0 说明；本次分析对象内不可见 |
| 8 | 工程成熟度 | 零依赖/自愈安装（占位符+失效路径就地修正）/迁移脚本/版本断裂文档化 | **4.5** | index.js renderSkillsDir、README「版本对应」节 |
| **综合** | | | **4.0** | 单人维护的完成度奇迹，但深度绑 dsh 版本（0.1.6/0.1.7 断裂自述） |

### B dsh-redteam-model@1.1.1（dsh 侧约 2.9 万行 js/ts + playbook 5,573 行 + refs 2,078 篇；kali-mcp 另计 8 万行）

| # | 功能域 | 细目 | 分 | 依据 |
|---|---|---|---|---|
| 1 | 模式覆盖 | 十模式四层资产，专业纵深（攻防评估含社工钓鱼/内网四型分流/AI 红队） | **5** | modes/ 全目录+ad-playbook 1,070 行 |
| 2 | 运行时门禁 | stage-gate 32 门结构校验+sec-enforce 确定性拦截+askGate 审批分级+KILL 熔断 | **5** | 两插件源码；「模型不能自评门禁」原则真正落地 |
| 3 | 逐轮治理 | route-boost 信封（阶段粘滞/变化才投/证据等级/恢复行）+refusal-guard 升级梯+auto-advance | **5** | 三插件 README+机制注释；成本模型（同阶段零 token）设计清醒 |
| 4 | 工作流方法论 | playbook 十册 5,055 行：通道成本阶梯/六节点工具兜底/防跳步六层/覆盖终态规则/矩阵扇出 | **5** | pentest/ad-playbook 细读；这是该项目真正的护城河 |
| 5 | 过程留痕与记忆 | trace-vault 配对落库跨压缩检索+campaign-memory 时间衰减+results 跨会话聚合 | **4** | 三插件 README；LIKE 检索、截断入册（自认索引非归档） |
| 6 | 执行工具面 | scanner-tools 13 工具纪律内置+semgrep 离线规则+hunter 三平台+webshell-mgr | **4** | 各插件；保守默认+防盲打+绝不自动安装，执行深度依赖目标机工具链 |
| 7 | 跨 harness 双签 | product-subagents 无头 spawn claude/codex CLI | **3.5** | 源码注释坦承 capabilities 全 false（CLI 子进程无法强制 schema/深度/工具过滤）——可用但约束弱 |
| 8 | UI 可视化 | AttackAtlas 图谱四态+按目标分账+双击派单+成果五板+管理台 | **4** | attack-atlas taxonomy/README；功能密但为多插件拼装 |
| 9 | kali-mcp-server | 260+ 工具 MCP 化+四族 17 agent+内置 LLM/决策脑 | **2** | 8 万行遗留感明显（v2/v3/v4 层叠、模块名 ultimate_engine），依赖重、无认证、智能体编排与 dsh 侧重叠——定位尴尬的「第二宿主」 |
| 10 | 工程成熟度 | 每插件带离线单测+部署幂等+备份不删+版本自愈；但 README(10 模式/17 插件) 与 DEPLOY.md(9/14) 漂移 | **4** | tests/*、manager.ts heal/reconcile |
| **综合** | | | **4.5** | 治理思想与 playbook 深度业内独一档；重执行面(kali-mcp)是负资产 |

---

## 三、业务工作流（各自怎么打一场完整渗透）

### 3.A dsh-redteam-mode：从靶标名到得分报告

1. **开战**：新会话选「红队模式」→ 发一个靶标单位名称 → 触发 `redteam_engagement_open` 绑定（会话级隔离，子代理自动继承）。
2. **预检**（persona 规定第一个动作）：加载技能确认可用 → `redteam_preflight` 检查 FOFA_KEY/VPS/本机二进制（suo5/fscan/gogo/frp/冰蝎/哥斯拉/nmap/nuclei）→ 缺什么一次性列清向用户要；补不齐给降级方案（FOFA→crt.sh+被动 DNS；无 VPS→先做不需落地的成果）。
3. **顺序派角色**（默认并发 3，派前 agent_slot 占位）：
   - **recon**：passive-recon+fofa-recon+recon-pipeline（subfinder→dnsx→naabu→httpx→katana）铺资产面 → `redteam_asset_add` 落库（端口带 service/product/version/url/title）；
   - **assess**：逐条 `redteam_asset_assess` 评 priority/potential/reason → 产出「先打谁」；
   - **vuln-scan**：逐资产先 `redteam_poc_search`（知识库+本机 nuclei 模板，防重复劳动）→ nuclei-scan/dir-bruteforce/web-fingerprint → `redteam_vuln_add`+每条确认漏洞配 `redteam_http_evidence_add`（完整原始请求，报告可直接粘 Yakit）；
   - **exploit**：逐漏洞先服务器权限（冰蝎/哥斯拉马+**必须实测用户能连上**）→ `redteam_webshell_add` → 立刻 suo5 隧道+`redteam_tunnel_add`（entry_kind 必须非 self-only）+实测内网可达 → 凭据落库+浏览器实测登录后才记账号分（自助注册 self_created 不计分）；
   - **internal**：走隧道依次递归拉起四角色——gogo-intranet 铺面（走 socks5 出低噪声测绘）→ fscan-intranet 打点（弱口令/未授权/MS17-010）→ 命中进 surface 交 vuln-scan → **每发现新网段再跑一轮直到无新增**；所有命令 proxychains -f 临时配置绝不动系统。
4. **全程核对**（「不核对就等于没做」）：指挥官对每个「拿到了」的回报在库里验证（asset_query/vuln_query/sessions/chain）——**没落库的发现=没发生**；得分/新资产/要资源/阶段推进四种情况才向用户汇报增量。
5. **收口**：`redteam_score_report` 生成按攻击链五阶段折叠的报告——每条得分附目标→拿到什么→怎么拿到（命令）→原始请求；自建账号与同服务重复命中整条剔除并报剔除数。控制台九 tab 全程实时（资产测绘图/隧道连通性实测/得分曲线/知识库默认跟当前靶标筛选）。

### 3.B dsh-redteam-model：pentest 模式一场仗（ad 模式同构更重）

1. **开局登记**：route-boost 信封已注入 `[route-boost] mode=pentest phase=…`（含门禁清单+refs 指针+工具面就绪行）；`operation_goal` 登记目标契约 → `operation_constraints`（deny/allow 逐行，带词的 deny 在 bash/fetch 上确定性拦）→ `operation_scope` 登记范围分母（最小范围原则，绝不擅自放大）。
2. **工具平面检测**：读信封就绪行，缺的才逐个 `command -v`（批量 tool-plane.sh/ps1）+ MCP 自省（mcp__<server>__<tool> 面）→ evidence-index.md tool-plane 四列（CLI/MCP/installed-by-agent/install-failed）。
3. **0 防护画像**：wafw00f 判 WAF+CDN+蜜罐特征 → 防护画像卡定**速率预算与测试姿态**（疑似蜜罐只被动观察）。
4. **1-2 被动收集+入口面盘点**：subfinder/gau 铺面 → httpx/whatweb 指纹 → **机器可读黑板双写**（targets.txt/assets.csv/creds.txt 喂工具；evidence-index 认知层记推理）→ 形态分流（纯 API/CMS/AI 应用/客户端各走专门作战线）。
5. **3 登陆口专线**：无凭据优先读登录页 JS——四类结构化线索（路由接口清单/签名加密机制/前端校验标记/硬编码密钥）；**硬编码凭据第一优先级直接利用**。
6. **4 矩阵扇出**：AttackAtlas 双击格子派单（自动带目标锚定+refs 手册）或 workflow 扇出 per-资产；每格走**通道成本阶梯**（轻探测→批量→浏览器→会话通道→利用通道）+工具六节点兜底（本机→MCP（含 kali-mcp）→已装替代→询问安装→脚本→诚实降级）；scanner-tools 防盲打（未登记 assets.md 的目标直接拒扫）。
7. **单格命中 → Gate P2**：三件套（基线/差分/marker）`stage_gate` 结构校验 + independent-review 复核员（**只给原始材料不给主链结论**）+ 可选 claude/codex 异源双签。
8. **5 验证与影响证明**：命令执行只跑 whoami 级只读；每 finding 生成参数化 python 复现脚本（破坏步骤默认关）；数据暴露类升「影响证明」须先过影响证明设计员。
9. **6 收口**：coverage-matrix 全格四态终态（含 N-A 附原因）→ `operation_progress` 算术对账（报告须含「覆盖 M/N」且与台账一致，虚报拦门）→ Gate P3 报告门 PASS → 报告员写 reports/（sec-enforce 拦截未过门写入）→ **收口卸载阀门**：ask_user 是否卸载本次 agent 装的工具（只卸自己装的）。
10. **全程兜底**：trace-vault 自动留痕可 `trace_search` 找回被压缩掉的过程观察；refusal-guard 拒答升级梯；blocked 聚集≥2 次失败归因信封提示换路；campaign-memory 把打法沉淀给下次。

### 3.C kali-mcp-server 在 B 体系中的真实位置

B 的 playbook 只把它当**通道降级链第二节点**（本机缺 nmap → 走 kali MCP）；其内置的四族 17 智能体+决策脑+编排器是独立王国（自带 LLM key 直连 anthropic/openai），与 dsh 侧编排**功能重叠且互不知情**——实战中要么用 dsh 编排+MCP 工具面（薄用法，playbook 主线），要么整个跳过 dsh 直接跑它的 agent 链（厚用法，违背 workflow-first 初衷）。这个自相矛盾是判第四节的重要证据。

---

## 四、对探隐插件路线终审判决（与 0-dsh.md 双桥判决合流）

### 判决：**双薄桥（桥 A 遥控 + 桥 B MCP）维持并加固；插件产品路线拒绝（证据升级）；两插件整体作纯参照，按第五节清单偷模式。**

**置信度：0.91**（0-dsh.md 原判 0.90；两插件实证把「插件路线真实成本」从推断变成证据，微升）。

#### 4.1 逐路线判决

- **桥 A（探隐遥控器驭 dsh，headless/ACP/stdio）——维持，且新增用法**。A/B 都以 preset 声明行注册、会话级选用：探隐把 dsh 当战士驭时，可建议/预配该战士挂 A 或 B 类预设（A 给它事实库纪律，B 给它门禁纪律），战士战果经桥 A 流回探隐账本。两插件客观上**丰富了桥 A 战士侧的弹药**，不改变桥的薄度。
- **桥 B（探隐自曝 MCP server，dsh-mcp-client 挂载）——维持，且获得镜像实证**。B 的 kali-mcp-server 就是桥 B 方向的活体样本：一个独立进程、一根 URL（streamable-http :8765）、被任意 harness 的 MCP client 消费——**这证明「能力住 MCP、智能住宿主」的分界在真实项目里成立**。但它同时是反面教材（见 4.2 第 3 条）：探隐桥 B 必须薄——只暴露工具面+判据（如九门校验、账本哈希链验证、评分口径），**绝不在 MCP server 里内置第二套编排智能体**，否则重蹈 kali-mcp 的「第二宿主」陷阱（8 万行、重依赖、与外层编排重叠）。
- **插件产品（探隐做成 dsh 插件/预设）——拒绝，证据升级**。三条硬证据：
  1. **宿主版本 churn 是持续税**：A 的 README 专门写「版本对应」节——DSH 0.1.7 换了预设注册机制（目录扫描→声明行），0.12.0 及更早插件在新宿主上模式列表直接消失；其 cordis.patch 头 14 行、index.js 自愈逻辑、migrate-legacy-rows.mjs 全是在给机制断裂付账。B 同样：normalize.ts 的职责就是「部署副本按运行宿主实际提供的引擎包改写」workflow 行（dsh-workflow-ptc vs dsh-workflow-worker-thread），manager.ts 里 healPresetPlanePlugins/reconcileProfileBundles 两个函数专为自愈旧版写坏的 profile。**两个最认真的插件作者都在为同一件事写迁移代码**——这就是插件产品路线的固有成本曲线。
  2. **深耦合内部 API**：B 的核心价值（guard/systemPrompt.context/session/event/agentPresets.composedPreset/agent.followup）全是 dsh 未承诺稳定的内部面；A 的价值面（webServer 具名路由/slots/shell.overlay）稍稳但同样无契约。0.2.0-rc 的 rc 后缀本身就是警告。
  3. **作者自认**：B README 原话「dsh 在安全工作这方面的设计实际上是有限的……本身插件的载体还是 dp-harness（即 dsh）本身」——连插件联邦路线最成功的实践者都承认：插件不是底座，harness 才是；而探隐的宪法是**自己就是底座**（自持内核+账本哈希链+九门+度量）。给 dsh 做厚插件=探隐降级为 dsh 的外设，与宪法正面冲突。
- **纯参照——从「UI 模式照抄」扩展为「治理模式照抄」**。0-dsh.md 第五节偷的是 UI 层（审批接管/工具卡/journal 流）；本报告第五节新增的是**作战治理层**（评分规则/门禁校验/逐轮信封/过程留痕/沙箱纪律）——这一层与探隐九门+度量+账本天然同构，价值不亚于前者。

#### 4.2 翻案条件（何时可改判「做插件」）

1. dsh 发布**稳定的插件/预设 API 契约**（semver 承诺+预设机制稳定跨两个 minor 版本不断裂）——届时 A 类自包含插件维护成本可控，探隐可考虑发「探隐桥插件」（薄形态：一行 preset 声明+内置 MCP client 配置指向探隐 server，本质仍是桥 B 的发行壳）；
2. 出现「探隐必须住进客户已有 dsh」的商业场景——即便如此也只做上述薄桥插件，永不做 A 类厚插件（事实库/评分引擎住探隐内核，插件只做转发）；
3. 探隐放弃零依赖 stdlib 法律（宪法级，实质不可能——且 A 的 node:sqlite 零依赖实践反而印证 stdlib 路线可行：node 有 node:sqlite，Python 有 sqlite3，哲学同源）。
   三者任一成立才重审；在此之前：**双桥 + 参照，终审**。

---

## 五、可偷清单（workflow 骨架 / skill 组织 / 评分规则 / 沙箱纪律，文件级出处）

### 5.A 从 dsh-redteam-mode 偷（8 条）

| # | 偷什么 | 落到探隐哪页 | 出处（文件级） |
|---|---|---|---|
| A1 | **评分规则单一实现律**：口径（封顶/去重/档位）只允许一个实现，面板/报告/链路三处消费同一函数——「三处各写一遍必然漂移成不同口径」 | **度量页**（九门得分+战果计分的口径中枢） | lib/score-rules.js 头注+applyScoreCaps/evaluateScoreBoard |
| A2 | **得分点数据模型**：rule（同规则共享上限）/tier/cap/dedup_scope(service·system·target·none 四档)/builtin 标志位（内置点只可启停、自建点永不被清理逻辑误删）+ sp() 工厂展开规则文档 | **度量页**（得分点注册表设计直接可译成 Python dataclass） | lib/schema.js L152-181（score_point DDL）；lib/score-rules.js L767+（DEFAULT_SCORE_POINTS） |
| A3 | **防刷分三判据**：self_created 账号不计分；同资产同端口服务封顶（拿到最高权限即拿满，重复命中回 warning「服务已拿满·不计分」）；隧道合法性 entry_kind 枚举（target-outbound/http/agent 合法，self-only「自己 VPS 上的代理」不算突破，未声明显示待确认） | **九门**（边界突破门+战果门的判定口径） | lib/score-rules.js TUNNEL_ENTRY_KINDS/ACCOUNT_POINT_CODES/SERVICE_CAPPED_POINT_CODES |
| A4 | **FTS5 编译期探测降级**：能力 probe→缺席自动 LIKE→环境变量强制降级供 CI——零依赖检索的优雅退化范式 | **知识库页**（探隐 POC 库检索） | lib/schema.js L28-46（HAS_FTS5） |
| A5 | **指挥官汇报纪律**：只有「得分/新资产/要用户出手/阶段推进或硬失败」四类才说话、报增量不重述、「没有就一个字都别说，安静派下一个」 | **会话页**（探隐总控向操作员的汇报节奏律，直接省 token） | presets/redteam/agent.cordis.yml persona「什么时候才跟用户说话」节 |
| A6 | **子代理物理叶子化**：提示词劝阻是软的——直接 toolFilter 摘掉委派工具+maxDepth 1 双保险；「不能 deny 自己注册的 scoped 工具」的踩坑记录也值一行 | **战局页**（探隐战士防递归派单） | cordis.patch.yml L346-365（delegation group 注释） |
| A7 | **并发槽位协议**：派活前 acquire 占位、被拒不重试硬塞、上限用户可配即时生效 | **战局页**（战士并发预算） | lib/tools.js redteam_agent_slot（L630+）；settings.js maxAgents |
| A8 | **npm dual-use 合规拆分范式**：DISCLOSURE 声明+contentPolicy.class=dual-use+攻击技能移出包体放 Release 附件「用户自取自行执行」 | **法务**（探隐若开源分发的合规范式） | DISCLOSURE 全文；README「关于工具链」节；package.json contentPolicy |

（附赠：①node:sqlite DatabaseSync 零依赖 SQLite 实践——探隐 stdlib sqlite3 同哲学的 Node 侧互证，lib/store-core.js L10；②补丁行防撞迁移（前缀新 id+旧行 id+name 双匹配精确关闭），cordis.patch.yml L3-23——探隐不需要，但写进「插件生态考察」备忘。）

### 5.B 从 SeaOf0/dsh-redteam-model 偷（12 条，按四类归档）

**workflow 骨架（6 条）**

| # | 偷什么 | 落到探隐哪页 | 出处 |
|---|---|---|---|
| B1 | **双层防线原则**：「模型不能自评门禁——结构校验必须是工具调用，语义门禁归独立复核员，一切判定落审计 trail」——探隐九门的宪法级表述 | **九门总纲** | README「基础原理与架构」节；dsh-sec-enforce/lib/index.js 头注 |
| B2 | **结构门禁五类 check**：file 存在/markers 字面标记/table 行列数/hexHash/provenance 哈希——结构项机器判、manual 语义项人类/复核员判，判定追加 gate-log.md | **九门**（每门的机器可校验判据 schema） | plugins/dsh-stage-gate/lib/index.js GATES 表（L31+，32 门全量定义） |
| B3 | **逐轮治理信封**：每 turn 注入 ≤1.6K 字符（mode/phase/gates/双签/边界/证据等级/refs 指针/operation 恢复行）+阶段粘滞（裸「继续」不重置）+**变化才投递**（同阶段零 token）+强制检索提示（refs 无命中时「勿凭记忆自答」） | **会话页**（探隐 turn envelope——账本哈希链状态+九门进度+预算的每轮注入） | plugins/dsh-route-boost/lib/{index,routes}.mjs+README（机制/信封格式/已知取舍全公开） |
| B4 | **防跳步六层**：文本纪律/角色信息裁剪（侦察工人 prompt 不带利用章——裁信息面不裁工具面）/落盘硬前置（下阶段工人第一条=先读上阶段产物校验字段，缺即中止回报）/复核 gate-pass/goal 助推/运行时 gate | **战局页**（探隐多战士流程纪律的完整 checklist） | modes/attack-defense/skills/ad-playbook/SKILL.md「防跳步六层」节（L728+） |
| B5 | **覆盖终态四态+防走黑**：tested-found/tested-clear/na(附原因)/budget-stop 四态；候选路径台账三终态（走通/失败附原因/未尝试附理由）防「第一条路走到黑」+「全部候选失败才许升级」；阶段终态表（执行/不适用附原因/未执行附原因与用户知情） | **战局总览**（探隐攻击面覆盖度语义——比二态 done/todo 诚实一个量级） | ad-playbook「覆盖终态规则」节；plugins/dsh-attack-atlas/lib/taxonomy.js CELL_STATES |
| B6 | **机器可读黑板双写**：targets.txt/assets.csv/creds.txt 机器层喂工具+evidence-index.md 认知层记推理，新发现即时双写，扇出工人以黑板为唯一事实源「禁止各记各的」 | **黑板页**（探隐战士间共享作战态协议） | modes/pentest/skills/pentest-playbook/SKILL.md「机器可读黑板」节 |

**skill 组织（2 条）**

| # | 偷什么 | 落到探隐哪页 | 出处 |
|---|---|---|---|
| B7 | **playbook=技能即方法论**：每模式一册 140-1,070 行作战手册（frontmatter 带 tools 期望清单），内容=阶段时序+通道成本表+专项作战线+负面清单，而非零散技巧；**主模式 router-playbook 只做路由**（任务分类路由表+专业模式决定性特征映射+浅做升级触发器+「先打穿一条路径再扩展」三纪律） | **技能页**（探隐 playbook 组织：总控路由册+专业作战册双层） | modes/redteam/skills/router-playbook/SKILL.md（路由表全文可译）；十模式 skills/*/SKILL.md |
| B8 | **refs 索引化三律**：README.md 全量索引+零本机路径（打包铁律）+指针不灌正文（信封只给 refs/<类目>/README.md 指针，控上下文成本——「逐轮灌正文会撑爆上下文」是 route-boost 明确的设计取舍） | **知识库页**（探隐外部知识库的装载律） | modes/*/refs/README.md；route-boost README「已知取舍·正文级 skill-boost 不做」 |

**评分规则（1 条）**

| # | 偷什么 | 落到探隐哪页 | 出处 |
|---|---|---|---|
| B9 | **验证四档+报告门算术对账**：finding 分疑似/已触发未利用/完整利用链/影响证明四档，「报告 severity 必须匹配验证档，never overrate」；覆盖台账 M/N 算术对账（部分覆盖照实声明可过，虚报/漏报拦门） | **度量页**（探隐战果分级+报告门） | modes/pentest/agent.cordis.yml persona「Iron rules·Verification levels」；ad-playbook「覆盖度台账」节 |

**沙箱纪律（3 条）**

| # | 偷什么 | 落到探隐哪页 | 出处 |
|---|---|---|---|
| B10 | **确定性拦截四件套+分级审批+熔断**：报告门（未过门禁写报告目录=拦）/写边界（不出工作区）/高危特征（大范围 rm·裸 DROP·资金类 POST=拦并指路「呈报计划→审批」）/速率纪律（nmap -p- 无速率·masscan --rate>1000=拦+给修法）；「变更性但可逆」类升级宿主原生审批而非硬拦；KILL 标记文件全局熔断（touch 即停删即恢复免重启）；**误报优先于漏报**（特征集刻意保守） | **控制面**（探隐工具执行 guard 的完整需求清单） | plugins/dsh-sec-enforce/lib/index.js（Config/REPORT_GATE/KILL_MARKER 全文） |
| B11 | **防盲打+保守速率+安装阀门**：主动扫描须目标已登记资产基线；工具默认保守速率（nuclei -rl 15/ffuf -rate 50）+显式覆盖留痕（「默认 X→Y，留痕」）；绝不自动安装（首次 ask_user，批准=本会话预授权，拒绝=脚本兜底，失败最多重试 3 次进 install-failed 不再白试）；收口卸载阀门（只卸 agent 装的）；安装位置优先工作区（venv/pip --target/tools/） | **控制面+九门**（探隐授权范围执行的机器纪律） | plugins/dsh-scanner-tools/lib/{index,registry}.js；pentest-playbook「通道完整阶梯/卸载阀门」节 |
| B12 | **过程留痕库+失败归因信封**：每次工具调用 callId 配对落 SQLite（args 8K/result 32K 截断，14 天/5 万行淘汰），跨 compaction 可子串检索；「索引不是归档」边界自认；近 30 分钟 blocked 聚集≥2 次投一行换路提示 | **账本页**（探隐账本哈希链旁的**过程流索引**——账本管不可篡改判定，trace 管可检索观察，互补不互替） | plugins/dsh-trace-vault/{README.md,lib/store.js} |

（附赠 3 条不计入：①**拒答升级梯+措辞正向化**——检测→重锚（附原请求）→纠偏重试→审计交人，刻意回避 jailbreak 腔措辞（实测反升拒答率），探隐驾驭基础模型时的运行时治理蓝本，plugins/dsh-refusal-guard/README.md；②**跨 harness 双签**——无头 spawn 异源 CLI 复核关键 finding（「claude 的结论也要证据，evidence-free endorsement 不接受」），探隐多模型互证页参照，plugins/dsh-product-subagents/lib/index.js+modes/pentest/agent.cordis.yml L60-65；③**AGENTS 专属命名空间**——全局语境注入收进模式专属文件仅注目标会话（从全局 AGENTS.md 撤回防跨模式污染），探隐若做多工作流上下文注入时的隔离律，README「方式二」安装节+AGENTS.security.md。）

### 5.C 不偷清单（明确划界）

- A 的手写 React 4,175 行控制台——探隐有自己的 UI 路线（0-dsh.md 第五节已偷过更上游的 dsh 官方交互律）；
- B 的 kali-mcp-server 全部——重依赖+内置第二套智能体编排+无认证，与探隐零依赖/单内核宪法冲突；只偷它 README 里的一句话工程教训：**MCP server 无认证仅限隔离内网**（探隐桥 B 若做远程暴露必须自带令牌，超越此样本）；
- B 的 AGENTS.security.md「No Refusal」哲学本体——探隐的合规姿态由自己的法律层定（DSH 只做薄遥控桥不做底座），本报告仅将其作为「宿主侧表达纪律」技术机制（refusal-guard 的升级梯设计）的参照收录，措辞红线（不用越狱腔）反而是它自己踩过坑后的克制。

---

## 附：证据快照（关键文件索引）

- A 根：`…/dsh-plugins/dsh-redteam-mode/`——package.json（dsh.bundle.patch/dsh.client/contentPolicy.dual-use/engines.dsh>=0.1.0-rc.6）；DISCLOSURE；cordis.patch.yml 434 行；lib/{index,store-core,tools,schema,score-rules,client,ui,skill-availability,skill-fixes,settings,validate,ip-utils,report-replay}.js + migrate-legacy-rows.mjs（合计 14,511 行）；presets/redteam/{agent.cordis.yml 28K,preset.yml}；skills/*.md ×15（104K）
- B 根：`/tmp/drm/`——README.md 230 行；cordis.patch.yml 3,824 行（10 preset 行+管理器行+5 处 scanner-tools/1 处 semgrep-audit preset 平面挂载）；src/*.ts 2,611 行（manager.ts 1,668）；lib/{index,client}.js 构建产物；modes/ 十模式（agent.cordis.yml 3,728 行+playbook 5,055 行+refs 2,078 文件+av-evasion lab/ 12 实验目录）；shared/skills ×4（515 行）；plugins/ ×17（各含 cordis.patch.yml/lib/test/README）；deploy/{DEPLOY.md,deploy.mjs,verify-deployment.mjs,check-sources.mjs}；deploy/assets/kali-mcp-server/（mcp_server.py 649 行+kali_mcp/ 155 文件 80K 行+kali-mcp-server.zip）；AGENTS.security.md
- 市场坐标（委托方已扫，本报告印证）：认真相关包确实只有 dsh-redteam-mode 一支做成了完整产品；SeaOf0 走 github 分发+设置页管理台；其余 npm 噪音不构成参照系。

# VulnClaw 源码深度分析（竞品调研）

- **对象**：`.research/repos/VulnClaw` 本地 clone，712 文件，HEAD `3b71e26`（2026-09-16，Merge PR #281；clone 为浅克隆单 commit，无历史可考）
- **版本**：v0.4.0（`pyproject.toml:8`），MIT，Python ≥3.10，作者 UncleC / Netw0rkNoob
- **方法**：全程本地读码，全部结论以 源码路径:行号 为证；README 只作定位参考不作证据
- **服务对象**：探隐 TanYin（`docs/design/2026-09-21-tanyin-v2-design.md`：账本驱动/单写者/四层执法/铁律 7/薄 CLI/证据即漏洞）
- **代码量实测**：`vulnclaw/` Python 175 文件 64,795 行（agent 25,117 / cli 10,882 / intel 5,396 / report 3,644 / config 3,504 / mcp 2,504 / skills 2,607 / web 1,651 / kb 1,567 / target_state 1,349 / traffic 1,190 / codescan 1,066 / plugins 953）；前端 React 9,154 行；Rust TUI 5,355 行；测试 113 文件 31,921 行、1,680 个 test 函数

---

## 1. 架构实况

### 1.1 进程模型：单进程异步 Python + 多宿主外壳

- **本体是一个进程内异步事件循环的 Agent**：`vulnclaw/agent/core.py:63` `class AgentCore:`（"Core AI agent that orchestrates LLM calls and tool execution"）。没有常驻服务、没有守护进程；每次 CLI 调用拉起 → 跑循环 → 落盘退出。
- **入口三件套**：① Typer CLI（`vulnclaw/cli/main.py:1174` `app = typer.Typer(`，共 19 个 `@app.command`：run/solve/persistent/recon/scan/network-scan/exploit/report/manual/init/login/logout/doctor/learn/feedback/repl/tui/web 等，`main.py:1187-3692`）；② `python -m vulnclaw`（`__main__.py:9-11`，供 Rust TUI 拉起 Python core）；③ FastAPI Web（`vulnclaw/web/app.py:1-15`，task_manager + SSE 流）。同一 `AgentCore` 被 CLI/TUI(Web)/REPL/Web 四个外壳复用，`vulnclaw/orchestrator.py:40` `run_agent_task(` 是共享的任务编排层（restore→run→summary）。
- **自然语言→任务落地是纯正则关键词抽取，不是 LLM 结构化解析**：`vulnclaw/agent/input_analysis.py:143` `extract_task_constraints(` 用中文正则（如 `(?:只测|仅测|只允许测试)...(\d{1,5})(?:\s*端口)?`，:150-158）从用户输入抠出端口/动作/路径约束；`detect_phase`（:40）与 `detect_target`（:130）同样是关键词表。CLI 也提供结构化旗标兜底（`main.py:1207-1226` `--only-port/--only-host/--only-path/--blocked-host/--allow-actions` 等）。
- **三引擎并存**（`core.py:535-595` `auto_pentest` 内 `resolve_engine` 分派）：① **rounds 遗留引擎**（`loop_controller.py:90` `auto_pentest`，按轮循环+阶段推进）；② **solve 模型主导引擎**（默认，`core.py:599` `solve` → `solver.py:581` `_solve_impl`）；③ **team 角色团队引擎**（`team.py`，leader/adviser/researcher/developer/executor 五角色计划-派发-复规划）。
- **MCP 工具链**：`vulnclaw/mcp/lifecycle.py` `MCPLifecycleManager` 管理 stdio/streamable-http/sse 三种传输的外部 MCP server 生命周期，`mcp/registry.py:59` `MCPRegistry` 记录健康度/成功率/重启次数并做 tool→server 路由；内置 fetch 工具走本地 httpx（`lifecycle.py:137` `_check_fetch_constraints` 是 fetch 的 scope 执法点）。**内置工具不走 MCP，直接在 Python 进程内注册**（`builtin_tools.py:1461` `build_openai_tools` 把 builtin+subagent+intel+traffic+MCP 五组 schema 拼成 OpenAI function-calling 面）。
- **子代理体系**（`vulnclaw/agent/subagent/` 8 文件 + `agent_run/agent_job` 工具）：主代理派 Group Leader、Leader 带 leaf 波次；leaf 代理 **fail-closed 禁用危险工具**（`builtin_tools.py:76` `DANGEROUS_TOOLS = frozenset({"shell_command", "python_execute"})`；:93 `dangerous_tool_refusal` "Leaf agents can never reach host execution"）。

### 1.2 vulnclaw/ 模块职责清单（实测行数）

| 模块 | 职责（源码证据） |
|---|---|
| `agent/` (25k) | 引擎本体：core/solver/loop_controller/team 三引擎、llm_client（重试/密钥池/流式/上下文裁剪）、builtin_tools+tool_schemas+tool_call_manager（工具面与执行）、agent_state（证据记忆）、context（SessionState 六子状态组合，`context.py:474`）、exec_gate（执行审批）、constraint_policy+input_analysis（约束）、reflexion/reasoning_state/correction_layer/anti_loop（反卡死）、context_vault+context_budget（上下文压缩/归档）、subagent/（子代理） |
| `cli/` (10.9k) | Typer 命令、REPL、向导、TUI 后端协议（`tui_protocol.py`+`protocol/tui-v1.schema.json`）、config 面板 |
| `mcp/` (2.5k) | 外部 MCP server 生命周期/注册/路由/诊断 |
| `intel/` (5.4k) | 情报工具：cve_lookup/osint_recon/topology_build/compliance_map/findings_report/findings_diff/remediation_advice/attack_map（`intel/tools.py:35-254` 8 工具）+ 修复规则库 |
| `report/` (3.6k) | 报告生成器（Jinja2）、verify（PoC 验证器）、SARIF/findings.json 输出、PDF 导出、solve 报告 |
| `skills/` (2.6k) | 7 个核心 skill md（recon/vuln-discovery/exploitation/…`skills/core/`）+ 47 个专题 skill 目录（`skills/specialized/`）+ 调度/路由/加载器 |
| `kb/` (1.6k) | 知识库：JSON 语料 store + BM25/ChromaDB 双后端检索 + experience 跨会话经验库（人审门） |
| `target_state/` (1.3k) | 目标态快照/合并/恢复计划（断点续传核心） |
| `traffic/` (1.2k) | mitmproxy/Playwright/Burp 三源流量捕获统一入库（scope 前置过滤） |
| `web/` (1.7k) | FastAPI 后端（任务/SSE/报告/配置） |
| `codescan/`/`plugins/`/`i18n/` | 本地代码扫描规则；插件注册表；中英双语音频目录 |
| 根 | orchestrator.py（共享编排）、run_context.py（run 目录账本）、headless.py（CI 退出码契约）、targets.py、task_service.py、warstories/（2 篇实战复盘 md） |

---

## 2. 全流程四段的实现真相

### 2.1 总判断：默认 solve 引擎是"LLM 决策 + 证据门禁"，四段不是编排死流程

solve 引擎 docstring 明示（`solver.py:1-8`）："The old solve engine imposed a planner/direction lifecycle on the model. This module keeps only the orchestration that a CLI agent actually needs... **Tool choice and investigation strategy are deliberately left to the model**"。系统提示同样写死（`solver.py:411-417`）："Tools, skills and knowledge files are available capabilities/reference material, **not required workflows, phases, checklists or tool schedules**"。即：**信息收集→发现→利用→报告四段在默认引擎里不存在硬编码流水线，全靠模型自决 + 事后门禁**。

### 2.2 分段实况

- **信息收集**：LLM 自主调用工具。工具面：`nmap_scan`（包装外部 nmap 二进制并解析 XML，`builtin_tools.py:1583`）、`space_search`（FOFA/Hunter/Quake/Shodan/ZoomEye/0.zone 六引擎测绘，API key 从 config 读，`recon_tools.py:1-12`）、`subdomain_enum`（被动聚合+小字典 DNS 爆破）、`js_recon`（仿 URLFinder）、`dir_enum`（仿 dirsearch，内置紧凑字典 `recon_tools.py:38-50`）、`unauth_test`、`http_probe_batch`（自研 httpx 批量探测，`builtin_tools.py:1836`）、`osint_recon`。遗留 rounds 引擎另有"侦察四维"（服务器/网站/域名/人员，`core.py:246-252` `recon_dimensions_completed`）+ 侦察最少 8 轮强制（`loop_controller.py:28` `RECON_MIN_ROUNDS = 8`）。
- **漏洞发现**：无独立扫描器阶段。两条路：① LLM 在对话里口述发现 → `finding_parser.py:104` `parse(` 三层正则从**自然语言文本**抠 finding（[Critical] 标签→自然语言漏洞描述→confirmed_facts 升级，PROOF_PATTERNS/NATURAL_LANG_PATTERNS :7-62）；② intel 工具 `findings_report/findings_diff` 做汇总对比。**没有 nuclei 集成**（全仓仅 3 处提及：技能路由关键词 `skills/dispatcher.py:39`、attack 词汇表 `intel/attack.py:398`）。
- **利用**：`python_execute`（进程内跑 Python，模式 safe/lab/trusted-local，`builtin_tools.py:2164-2222`）、`shell_command`（审批后 spawn，:640）、`runtime_diff_probe`（PHP/Python 运行时差分探针，:1144）、`brute_force_login`（:2486）、`traffic_repeat`（流量重放）。利用意图受动作约束（`constraint_policy.py:56-77` EXPLOIT_PAYLOAD_MARKERS 载荷特征表推断 exploit 动作并拦）。
- **报告**：两种。① 通用渗透报告 `report/generator.py:405` `generate_report(`——**Jinja2 模板渲染 SessionState 真数据**（:500-501 `template.render(**context)`），verified findings 独占详情章；② solve 报告 `report/solve_report.py:1-8`——"renders that artifact directly from AgentState **without asking the LLM to summarize**, so the report stays grounded in recorded tool output"。

### 2.3 段间交接、状态、断点续传

- **交接**：rounds 引擎靠 `detect_phase_from_output`（输出关键词识别阶段跃迁）+ `validate_phase_transition` 约束拦截（`loop_controller.py:139-158`）；solve 引擎无阶段概念，靠 `AgentState.to_prompt_summary()`（`agent_state.py:815`）把证据/步骤/钉死事实注入下一轮提示。**阶段是遗留引擎的展示概念，不是执法状态机**。
- **状态落盘**：三层。① `SessionState`（pydantic，含 findings/recon/reasoning/agent_state/constraints/history 六子状态，`context.py:474-534`）→ JSON；② 目标态快照 `target_state/store.py:191` `save_target_state(`（合并旧态+写 current.json+带时间戳快照+resume_meta 恢复计划：strategy/recommended_phase/priority_findings/next_actions，:230-292）；③ run 目录账本（见 §3.1）。
- **断点续传：有，且工程化程度高**。`run_context.py:206` `validate_run_context`（schema/目录/快照悬挂校验）+ :246-248 `writer.lock` 存在且非 resume 请求即判损坏拒绝；:122 `record_checkpoint` 每次快照记录 checkpoint 事件；`repair_run_context`（:250-285）可回滚到最后有效快照；CLI `--resume/--snapshot/--resume-run/--repair`（`main.py:1233-1316`）。`orchestrator.py:40-120` 统一 restore 流程。

---

## 3. 状态与证据管理

### 3.1 run 目录：一个"半账本"（有 append-only 事件流，无链式哈希）

`run_context.py:152` `create_run_context` 建立标准化 run 目录：`run.json`（manifest：schema_version=1/targets[]/resume/artifacts 路径表，:416-440）+ `events/events.jsonl`（**append-only 事件流**：run_created/checkpoint/run_status/repair，:106-115）+ `targets/<id>/state/{current.json,snapshots/}` + `evidence/ findings/ reports/ logs/ agents/ temp/` 七目录（:455-470）。写入全部原子化（临时文件+fsync+os.replace+目录 fsync，:383-405）。**这是 TanYin 账本的雏形对照物：有事件流、有快照、有锁，但没有行哈希链、没有 verify-chain、没有单写者纪律（SessionState 与 target_state 与 events 三处并行写）**。

### 3.2 证据：AgentState 证据记忆（内容寻址+去重）+ 流量库（原文 blob）

- **每个工具结果强制入证据账**：`agent_state.py:404` `remember_tool_result(` 对原始输出算 **SHA-256 content_hash**（:416）并做**重复检测**（同 hash 标记 duplicate_of 不重复进上下文，:413-433）；超大输出只进"头尾+高信号行"有界预览（`make_evidence_preview` :129），原文留在 evidence.content（上限 240 条、超出对半淘汰 :22-24,450-451）；模型可用 `evidence_list/evidence_view/evidence_search` 三工具回查原文（`builtin_tools.py:313`）。
- **HTTP 原文证据**：`traffic/store.py:62` `record(` 把 request/response **原始字节**写 blob（`<request_id>/request.bin|response.bin`）+ JSONL 索引；`traffic/capture.py:21` 统一捕获缝（mitmproxy/Playwright/Burp 三源），**scope 前置过滤**（`traffic/scope.py:39` `ScopeChecker.in_scope`，域外流量直接丢弃不入库）。finding 通过 `EvidenceRef{kind,path,request_id}` 指回证据树（`domain_models.py:127-140`），SARIF 输出把每个 ref 变 artifactLocation 附件（`findings_output.py:186-193`）。
- **run 目录 `evidence/` 目前实际承接 traffic 子树**（`traffic/paths.py:25-41` `<run>/evidence/traffic/`；其余 evidence 类尚在"run-directory PRD 落地前"的 config 全局兜底态，:1-10 docstring 自述）。

### 3.3 防编造：四道闸（比想象硬）

1. **完成门（最强）**：`solver.py:475` `_completion_gate`——FINAL 必须 cite 已知证据 id（引用未知 id 直接拒：:487-488）；目标要 flag 时 flag 必须逐字出现在证据文本里（:490-496 "claimed flag not present in tool evidence"）；无证据的 FINAL 一律拒（:498-499）。隐式完成同样要 flag 在证据中（:518-535）。被拒的完成会作为 user message 打回（:802-808 "[evidence gate] Completion rejected... Continue gathering or cite valid evidence"）。
2. **finding 入口隔离检疫**：`domain_models.py:201-221` `model_post_init`——无 evidence/vuln_type/remediation 三字段全缺的 finding，标题强制加 `[未验证]` 前缀、描述注入警告、lifecycle 压到 `needs_manual_review`，"stays in run state / audit trail but is excluded from the report/SARIF gate"。
3. **报告只渲染 verified**：`generator.py:412-413` verified_findings 独占详情章；`findings_output.py:8` "findings.sarif — only the **verified** findings (the report inclusion gate)"；LLM 生成的攻击摘要段过 `ReportContentFilter`（`report/filter.py:23`，剥 TOOL_CALL/Round 标记/调试输出/think 标签）。
4. **PoC 复核验证器**：`report/verifier.py:1-11` 原则声明"**未经验证的漏洞 = 误报 = 不写入报告**"；:577 `verify(` 按漏洞类型套 PoC 模板（PoCGenerator :93 模板表）→ 真执行 → `parse_result`（:511）按输出特征判 VULN_CONFIRMED/FALSE_POSITIVE/TIMEOUT/…→ verified 打 L4（:707-710 `mark_verified(evidence_level="L4")`）。

**弱点（诚实说）**：finding_parser 从 LLM 散文正则抠 finding（`finding_parser.py:104-130`），evidence 字段最初也是从文本里抓 URL/路径（`_collect_location_summary` :117），防编造闸门都在**下游**（报告门/验证门），上游 intake 仍可能把模型口述当 finding 记账（只是被隔离检疫）；PoC 模板按 vuln_type 查表，类型外漏洞无模板即落到 generic 模板（:342），验证覆盖面有限；finding_id 去重键是从 description/evidence 里抓第一个 URL/路径拼的（`domain_models.py:266-294`），同 URL 多漏洞会碰撞截断到 50 字符。

### 3.4 报告：真数据渲染为主，LLM 文本为辅且被过滤

主报告是 Jinja2 模板 + SessionState 结构化字段（目标/时间/严重度计数/约束摘要/违规事件/verified findings/执行步骤/recommendations，`generator.py:465-498`），唯一 LLM 生成的段落是"攻击摘要"（`_generate_attack_summary_from_session` :838，产出的文本过 filter 后嵌入 §4）；verified 详情章含定位/复现/HTTP 捕获渲染（`_render_http_captures` :1210 从 traffic store 读原文）。同时落 `findings.json`（全量+lifecycle）与 `findings.sarif`（仅 verified）双机读工件（:330-352）。

---

## 4. 安全护栏

### 4.1 范围/授权控制：工具参数级 TaskConstraints，多点重复执法

- **约束模型**：`TaskConstraints`（allowed/blocked × ports/hosts/paths/actions，`domain_models.py:317` 附近）来源二：NL 正则抽取（§1.1）与 CLI 旗标。
- **执法点（逐个实测在位）**：① 工具分发总口 `builtin_tools.py:1185` `execute_mcp_tool`——role 检查→危险工具 fail-closed→`validate_tool_action`（动作约束，含 EXPLOIT_PAYLOAD_MARKERS 载荷特征推断）→违规同时写 `add_constraint_violation_event` 审计（:1206-1221）；② MCP fetch（`mcp/lifecycle.py:137-225` host/path/port 全检）；③ nmap（`builtin_tools.py:1583-1605` host/端口约束+**保留 IP 解析即跳过**："解析到保留/内网地址…跳过 nmap 扫描"）；④ shell_command 里的 URL 扫描（:341-354 `_validate_command_url_scope`）；⑤ python_execute 源码里的 URL 扫描（:2225-2247）；⑥ traffic 捕获 scope 前置过滤（§3.2）；⑦ 阶段跃迁约束（`loop_controller.py:141-158` exploit 动作被 block 时拒绝进入 EXPLOITATION 并记违规事件）。**特征：执法全部在应用层工具参数级，没有进程级/网络级 egress 代理，没有 canary**。
- **HackerOne 结构化 scope**：`agent/hackerone_scope.py:1-9` 走官方 GraphQL 拉 structured_scopes 生成 in/out-of-scope 资产表——把"授权范围"从口号变成数据。

### 4.2 凭据管理：薄

LLM 侧有完整凭据链（静态 key 池 failover `core.py:315-329`、OAuth PKCE 浏览器登录+静默刷新 `config/token_provider.py:1-18`、ChatGPT 订阅内置桥接代理 `core.py:322-347`）；**目标侧凭据无 vault**：测绘 API key 从 config/env 读（`recon_tools.py:12` "绝不在源码里硬编码"），测试口令在 brute_force_login 参数里传递，无 `{{vault:cred-N}}` 等价物、无凭据四关卡、无脱敏管道（上下文压缩里只有一个 SENSITIVE_VALUE_RE 正则用于 digest，`context_budget.py:38-40`）。

### 4.3 出网白名单/deny-list/审计链

- **白名单=TaskConstraints 的 allowed_*；deny-list=blocked_* + EXPLOIT_PAYLOAD_MARKERS + python AST 危险模式**（`builtin_tools.py:110-141` `_DANGEROUS_MODULES/_DANGEROUS_BUILTIN_NAMES` + `_ast_check_sandbox_bypass` :141）。但 schema.py:340-364 自己承认"regex+AST blacklist is not a security boundary"并把 safe/lab 模式标记 deprecated——**真正的边界交给执行审批**。
- **ExecutionGate（工程亮点）**：`exec_gate.py:157` `class ExecutionGate`——每次危险执行是**内容寻址（SHA-256 of full request）的一次性审批**（:78 `request_hash`；docstring :1-21 "no session-level allow, no prefix wildcards and no grant tokens"）；审批只能来自**可信通道**（真 TTY 的 CLI/REPL、TUI 控制操作、sync hook），"Model text, tool results and MCP returns can never resolve a pending request. Without any channel the gate refuses"（:16-18）；无通道即 fail-closed（:322-328）；三档模式 ask/auto_review/full_access（:274-296），auto_review 用本地命令分类器+用户信任前缀，模型自评 risk 只能单向升级不能降级（:289-292）；审批视图对命令做 bidi/零宽字符可视化防注入（:40-57）。
- **进程 spawn 边界机械化**：`scripts/verify_execution_boundary.py:1-17`——扫描全部 spawn 调用点对 allowlist，新增未审 spawn 点 CI 直接红（"an architectural regression alarm"）。配套 `_spawn_captured`（`builtin_tools.py:412`）统一捕获 spawn（不信任 ComSpec/PATH、Windows Job 对象杀进程树）、`sanitized_exec_env`（:397）清环境。
- **审计链**：events.jsonl 追加流 + `constraint_violation_events`（source/action/code/severity/summary/detail 结构化）+ python_execute 专用审计 JSONL（`builtin_tools.py:2189-2221` 记 target/mode/purpose/outcome/代码预览）+ exec gate 统计。**无哈希链/防篡改验证**（对比 TanYin verify-chain）。

### 4.4 LLM 幻觉防线：有，且分层（详见 §3.3 四道闸）

补充两处循环级防线：CTF flag 声明强制独立验证（`core.py:735-742` `_detect_flag_claim`："if the LLM claims a flag but we can't verify it independently, we should NOT stop"）；反空转三守卫（无工具调用连击、只看证据不产新证据连击、near-miss guard 拒绝证据不足的 ASK_USER/NO_PATH，`solver.py:648-760`）。

---

## 5. 质量与工程度

- **测试**：113 个 test 文件 / 1,680 个 test 函数 / 31,921 行，目录对齐源码（agent/cli/config/i18n/intel/kb/mcp/meta/plugins/report/run/security/skills/traffic/tui/web）。安全测试独立成目录（`tests/security/` 8 文件：exec_gate/spawn_boundary/command_classifier/approval_schema/l4_modes…），有元测试（`tests/meta/`）。**是真测试**：大量行为级断言（如 solver 的 evidence gate 拒绝路径、gate wiring、spawn hardening）。
- **CI**（`.github/workflows/ci.yml`）：ubuntu+windows × Python 3.10-3.14 十格矩阵；ruff → **verify_execution_boundary.py** → 前端 tsc → pytest（3.12 格带 coverage 上 codecov，fail_ci_if_error）；另有 rust-tui job 与 release 工作流。codecov.yml 在仓。
- **技术债（明显处）**：① `cli/main.py` 3,811 行巨石（19 命令+REPL+事件接线全在一个文件），`cli/tui.py` 2,922、`builtin_tools.py` 2,683 次之；② 三引擎并存（rounds/solve/team）语义重叠，遗留引擎的 recon 四维/阶段推进与 solve 的"无阶段"哲学并存，配置项因此双份（`solve_max_directions` 已标 deprecated 但仍解析）；③ i18n 双语目录全量维护（`tests/i18n/test_catalog_parity.py` 靠测试钉平价）；④ 代码里大量"修改者/修改时间/修改原因"头注（如 `builtin_tools.py:44-46`）提示**缺乏以 PR 为单位的治理习惯**；⑤ 浅克隆无法评估提交历史质量（不确定项，明说）。

---

## 6. 对 TanYin 的启示

### 6.1 值得借鉴的 3-5 个具体设计（带源码证据）

1. **内容寻址的一次性执行审批（ExecutionGate）**：`exec_gate.py:78` request_hash 把"一次审批=一条确切命令"变成可对账对象；无通道 fail-closed（:322-328）；模型自评只能升档不能降档（:289-292）。对 TanYin 的 approvals.tsv/Tier 1 执行通道是直接可抄的语义：**审批粒度=内容哈希、通道=本地 UI、有效期=单次、模型无表决权**。
2. **完成必须引用证据 id 的硬门**：`solver.py:475-499`——FINAL 引用未知证据 id 拒、flag 不在证据文本拒、无证据拒、被拒回注上下文重试（:802-808）。这是"证据即漏洞"的一个已验证可行实现路径：TanYin 的 findings.tsv 强制 EV 卡片引用+reproducible_steps≥1 可复用同款判定逻辑（cite→known id→内容包含性→无证据拒绝）。
3. **证据内容寻址去重**：`agent_state.py:416-433` SHA-256 content_hash + duplicate_of + 有界预览（原文保底可回查）。TanYin 证据双哈希（raw+norm）之外的第三件：**去重哈希**值得进 E-index 设计——同输出重复探测不重复占预算。
4. **机械化执行边界回归**：`scripts/verify_execution_boundary.py` 把"全仓 spawn 调用点对 allowlist"做成 CI 门。TanYin 的 tools.lock 验签之外可加同款：**任何新增出网/spawn 点未经登记即 CI 红**，与铁律 7 的 CLI 边界互为机械防线。
5. **隔离检疫而非硬拒（intake quarantine）**：`domain_models.py:201-221`——裸 finding 不丢弃、不进报告，标 `[未验证]`+needs_manual_review 留在审计轨。TanYin facts/findings 分轨（铁律 4）可吸收这个中间态：**"证据不足的声明"是一等公民（可追溯可补救），但永远进不了报告门**。

### 6.2 VulnClaw 结构性弱点 × TanYin 铁律逐条对应

| VulnClaw 弱点（源码证据） | TanYin 铁律如何解决 |
|---|---|
| 状态三处并行写（SessionState/target_state/events），无单写者纪律；writer.lock 只防并发不防语义分裂 | **铁律 1 单写者**：总控唯一账本写者，子代理/引擎只产提交文件——写路径收单 |
| 四段流程=LLM 自由发挥（solver.py:415 "not required workflows"），无覆盖度承诺，跑完就是跑完 | **铁律 3 覆盖不可谈判**：矩阵每格非空、intent 必须闭合、budget-exhausted 诚实终态 |
| finding 从 LLM 散文正则抠（finding_parser.py:104），上游无结构化提交协议 | **铁律 1 提交 schema + 统一提交文件**：引擎产出结构化 submission，散文不能直接变账 |
| 阶段是关键词猜的（input_analysis.py:40 / loop_controller.py:139），不是状态机 | **铁律 5/phases.yaml 九门数据状态机**：门序+出口断言机械执法 |
| 执法全在应用层工具参数，无 egress/canary，trusted-local 模式下 python_execute 可任意出网（schema.py:340 自认 blacklist 非边界） | **铁律 5 四层执法**：Tier 3 egress 代理+canary，档位事实进报告守门声明 |
| 证据/报告强但无验证链（events.jsonl 无哈希链，可静默篡改） | **铁律 2 状态全落盘 + verify-chain**：行哈希链+对账重建 |
| 上下文靠热环+vault 归档+确定性压缩三层自管理（context_vault/context_budget），但恢复协议与引擎耦合 | **铁律 2 上下文三层策略共用同一恢复协议**：LLM 不依赖会话记忆 |
| 目标凭据无管理（无 vault、无脱敏管道） | **铁律 §8.4 `{{vault:cred-N}}` 四关卡**：凭据占位符+全链路脱敏 |
| CLI 3811 行巨石、判断与账本混体 | **铁律 7 薄 CLI 四类能力**：账本运算/机械执法/确定性投影/安装自检；语义判断禁入 |

### 6.3 批次 5/6 可直接吸收什么

**批次 5（知识飞轮+语料入库）**：
- **47 个专题 skill 目录即现成语料**（`skills/specialized/`：sqli/ssrf/ssti/deserialize/logic 等 detail-pack + hackerone/ctf-web/osint 等专题）+ 7 核心 skill md（`skills/core/`）——front-matter/结构对照 TanYin 技法页 schema 做映射入库即可（注意 MIT 许可允许）。
- **warstories/ 两篇实战复盘**（`warstories/2026-04-19_php-deserialization_regex-bypass.md`：元信息表+攻击链表+逐步发现）是**先例页（三元组）的天然样板**，格式可直接对齐 CNPEN/技法页 front-matter。
- **experience 经验库治理模式**（`kb/experience.py:16` "Lessons remain pending until a human approves them" + distiller 蒸馏 + 0.88 阈值近重复合并 `agent/distiller.py:25`）：TanYin ingest-staging 四门槛的"人审门+合并去重"两件可直接借鉴。
- **CVE/修复语料**：`intel/cve.py` + `remediation_rules.py`（1,108 行规则库）可作 CNVD/CVE 联网核验词表参考。
- BM25 纯 Python 后端+ChromaDB 语义后端的双轨降级（`kb/retriever.py:1-14`）是弱依赖环境知识检索的可行架构。

**批次 6（evals+安装+报告）**：
- **退出码契约**（`headless.py:36-45`：0=干净/1=事故/2=≥1 verified/3=仅候选——"A crashed scan exits 1, never 0 — no silent green CI"）：与 TanYin 0/1/2 契约直接对齐，第 3 态"仅未验证候选"值得考虑纳入。
- **findings.json（全量+lifecycle）+ findings.sarif（仅 verified）双工件**（`findings_output.py:330-352`）与 EV 卡片↔SARIF artifactLocation 映射（:186-193）：报告流水线的机读输出层可参考。
- **报告内容过滤器**（`report/filter.py`）：LLM 叙述段落进报告前的机械清洗（剥工具调用痕迹/轮次标记），TanYin 报告执行摘要（LLM 撰写）出口可加同款 lint。
- **CI 矩阵事实**（win+ubuntu×5 版本+ruff+边界扫描+coverage 门禁）：五宿主安装矩阵的 CI 工程直接对标。

---

## 7. 定位结论

**一句话**：VulnClaw 是"单进程 LLM 自主渗透 CLI（模型自由决策+事后证据门禁）"，与 TanYin"账本驱动+事前四层执法的合规验证平台"是**同类竞品、相反哲学**——它验证了 LLM 自主渗透的工程可行性（证据记忆/执行审批/报告验证门做得扎实），但其全部结构性弱点（无单写者、无覆盖承诺、无 egress 执法、无验证链）恰是 TanYin 铁律逐条针对性解决的；对 TanYin 而言它更像**可大量取材的上游语料库+反面架构参照**，而非互补工具链。

---

## 如果只记三件事

1. **VulnClaw 的"证据闸门"是真的**：完成必须 cite 证据 id、flag 必须逐字在证据里、裸 finding 隔离检疫、报告只渲染 verified——这套下游防线（`solver.py:475`/`domain_models.py:201`/`verifier.py:1`）证明"证据即漏洞"可工程化，TanYin 应把它前移到提交协议（结构化 submission）而非事后过滤。
2. **它的执法全在应用层、无网络边界**：TaskConstraints 七个工具口重复检查+ExecutionGate 内容寻址审批是这个路线的天花板——trusted-local python_execute 与无 egress/canary 是实打实的洞，TanYin 四层执法（尤其 Tier 3 egress+档位披露）是代差优势，必须在报告守门声明里显性对比。
3. **批次 5/6 有大量免费弹药**：47 个专题 skill+2 篇 warstory+experience 人审蒸馏流程可直接映射进知识库；headless 退出码契约（0/1/2/3）与 findings.json+SARIF 双工件是报告流水线的成熟参照——取材时记住 MIT 许可并核对语料时效。

# VulnClaw 实机试用报告(live trial)

> 2026-10-16 · 执行环境:macOS 26.5.1 (arm64) · Python 3.12.14 · Node v26.5.0
> 对象:[Netw0rkNoob/VulnClaw](https://github.com/Netw0rkNoob/VulnClaw) v0.4.0,commit `3b71e26`(2026-09-16,PR #281 merge)
> 姊妹篇:`2026-09-24-vulnclaw-analysis.md`(静态分析);本篇一切结论以实机运行为准。
> 靶场:烛龙 ZhuLong http://localhost:3081(授权靶,只读探测;**全程未触碰 8900/3000/8787/8443 及其它任何端口**;靶场登录凭据未使用——卡点发生在 LLM 侧,见 §3)。

---

## 0. 结论速览

| 维度 | 结论 |
|------|------|
| 安装 | ✅ 顺畅(独立 venv,editable,~60s);但有网络摩擦与一个 **P0 级 CLI bug** |
| LLM 配置 | ❌ **卡点**:本执行环境无任何可用 key(任务预案的「环境变量已备的 key」未到达委派环境);DeepSeek 端点可达,占位 key 实测收规范 401 |
| solve 实战 | ⚠️ 引擎编排层全程跑通并诚实收场(steps=0 evidence=0,零编造),但模型循环因 401 无法推进,**无 LLM 战果** |
| 非 LLM 管线 | ✅ 插件真跑靶场产出 2 条带证据发现(安全头缺失、/admin/users 端点暴露);报告可确定性生成 |
| 断点续传 | ✅ 实测生效(run/snapshot/target-state 三层);自带测试 12/12 通过 |
| 三环飞轮 | ⚠️ 结构齐全(证据闸门真值结算→lesson 蒸馏→人工审批→回注),但**本环境未真正转动**(蒸馏依赖 LLM) |
| 当战士层 | 可行性较高:NDJSON 事件流 + PluginResult JSON + 三层账本结构规整;**scope 执法必须走结构化通道,不能靠 prompt 措辞**(实测坑,见 §6.3) |

---

## 1. 获取与安装(摩擦点实录)

### 1.1 源码获取

- 任务所述本地只读 clone(`.research/repos/VulnClaw`,HEAD 3b71e26)**实际不存在**(`.research/` 目录缺失),按预案转公开仓库获取。
- `git clone https://github.com/Netw0rkNoob/VulnClaw.git` → **SSL connection timeout**(本网络 github.com 不可达;api.github.com / codeload.github.com / raw.githubusercontent.com 可达,PyPI 可达)。
- 实际通道(与仓内 KEY-MANAGEMENT §3.5 的 nuclei 先例同款):
  1. GitHub REST API 核验 commit:`/repos/Netw0rkNoob/VulnClaw/commits/3b71e26` → `3b71e26b8b33fdae0c1d53049e23f7dc04cf0922`,2026-09-16T14:39:14Z,"Merge pull request #281";
  2. `codeload.github.com/.../tar.gz/3b71e26` 拉 tarball(3.1MB,713 文件)解包为快照。
- 快照落 `/Users/wgen/redteam-agent/.research/repos/VulnClaw`(chmod 只读 + `.snapshot-commit` 标记),**未动本仓其它内容**。

### 1.2 安装(独立 venv,不动本仓)

```bash
# 系统 python3 是 3.9.6(低于要求的 3.10+),必须显式用 python3.12
cp -R .research/repos/VulnClaw /tmp/vulnclaw-src && chmod -R u+w /tmp/vulnclaw-src
/opt/homebrew/bin/python3.12 -m venv /tmp/vulnclaw-venv
cd /tmp/vulnclaw-src && /tmp/vulnclaw-venv/bin/pip install -e .   # ~60s,依赖无冲突
/tmp/vulnclaw-venv/bin/vulnclaw --version   # 0.4.0
```

摩擦点:

1. **editable 安装需要写源目录**——只读快照不能直接 `pip install -e .`,先复制到 /tmp(顺便满足「不动本仓」纪律)。
2. `vulnclaw doctor` 实测:Python 3.12.14 / Node v26.5.0 / npx✅ / uvx✅ / **nmap optional/missing**(内置 `nmap_scan` 工具会降级);fetch+memory MCP 本地模式开箱即用,chrome-devtools/burp/scanmalware 为 placeholder。
3. 未装 chromadb → 启动即提示「知识库已降级为关键词模式」(`pip install vulnclaw[kb]` 可启用语义检索)。
4. macOS 无 GNU `timeout`,时间盒看门狗需自备(轻微)。

### 1.3 P0 bug:`solve` 不带 `--stream` 必崩

```bash
$ vulnclaw solve http://localhost:3081 --goal "..." --max-steps 30 --run-name zhulong-trial
UnboundLocalError: cannot access local variable 'on_event' where it is not associated with a value
```

- 根因(`vulnclaw/cli/main.py`):`on_event` 仅在 `if stream:` 分支内定义(:1560),而 `agent.solve(..., on_event=on_event)` 在分支外无条件引用(:1578)。**任何不带 `--stream` 的 solve 调用在 v0.4.0@3b71e26 都会在启动前崩溃**。
- 规避:加 `--stream`(NDJSON 事件输出,本为 Rust TUI 设计)即可正常运行。
- 上游 main 分支 2026-10-05 已有多个后续提交,未核实是否已修。

---

## 2. 靶场与环境状态

- 烛龙 ZhuLong `http://localhost:3081` 在线:Vue 3 + Vite dev server,标题「烛龙 ZhuLong」,root 页 372 字节。
- 本轮对靶场**仅发过 4 个只读 GET**(`/`、`/src/main.ts`、`/src/router/index.ts`、`/src/App.vue`),全部 200。无登录、无写操作、无利用尝试;禁碰端口列表全程未接触。

---

## 3. LLM 配置:卡点如实报告

按任务「环境变量已备的 key 若不可用,如实报」,排查结果:

| 排查点 | 结果 |
|---|---|
| bash 环境 `printenv`(API_KEY/TOKEN/各厂商前缀) | 无任何匹配 |
| `~/.vulnclaw/config.yaml` | 不存在(首次运行才生成) |
| shell rc(~/.zshenv/.zshrc/.zprofile/.bash_profile 等) | 无 key 导出 |
| `launchctl getenv` | 空 |
| 本仓 `install/launchd/com.tanyin.runner.plist` | `__REPO__/__HOME__` 占位模板,无 key |
| 本仓 install/KEY-MANAGEMENT.md | 讲的是 tools.lock 签名钥,与 LLM key 无关 |
| Ollama 本地推理 | 二进制与进程均不存在 |
| `~/.dsh/.credentials.yaml` | 宿主 GUI 自身凭据,**超出本任务授权范围,未挪用** |

**网络侧验证(证明「只差一把钥匙」)**:配 provider=deepseek + 占位 key 后,solve 三轮调用全部收到 DeepSeek 规范 401(带 request_id),API 端点可达、链路通,有效 key 即可驱动引擎。

占位 key 实测行为(诚实降级的正面样本):

```
{"type":"log","message":"turn 1..3 → error: Error code: 401 - Authentication Fails, Your api key: ****-KEY is invalid"}
{"type":"complete","summary":"⊘ not reached — steps=0 evidence=0","result":{"findings":[]}}
run lesson distillation failed: Error code: 401 - ...
```

- 零工具调用(对靶场零请求)、零编造发现;结算摘要直接承认 not reached。
- 结论:**本报告无 LLM 驱动的实战战果;§4 为非 LLM 管线的真实验证 + 引擎编排层的实跑取证**。

---

## 4. 实战验证(无 LLM 部分真机实跑)

### 4.1 solve 引擎编排层实跑(卡在 LLM,编排全通)

命令(--stream 规避 §1.3 bug;预算取小档:solve_max_steps 30,约为默认 240 的 1/8;墙钟时间盒 30 分钟):

```bash
VULNCLAW_CONFIG_DIR=/tmp/vulnclaw-home VULNCLAW_SAFETY_PERMISSION_MODE=auto_review \
vulnclaw solve http://localhost:3081 --goal "授权靶场只读安全评估:…除目标3081端口外禁止触碰任何其他端口或主机" \
  --max-steps 30 --run-name zhulong-trial-stream --stream
```

落盘产物(`/tmp/vulnclaw-home/runs/zhulong-trial-stream/`):

```
run.json                                  # run 清单(schema_version/run_id/targets[]/artifacts{}/resume{})
events/events.jsonl                       # 追加式事件账本(见 §6.2)
targets/9893dc141d05ef84/target.json      # 目标清单(target_id/canonical/state_path)
targets/.../state/current.json            # 目标状态
targets/.../state/snapshots/*_solve.json  # 检查点快照(run_start 与 run_complete 各一)
evidence/                                 # 证据目录(本轮空)
```

事件账本原文(5 行,含失败如实记录):

```json
{"kind":"run_created","payload":{"command":"solve","run_name":"zhulong-trial-stream"}}
{"kind":"checkpoint","payload":{"snapshot_id":"20261016_225143_345969_solve","reason":"run_start"}}
{"kind":"checkpoint","payload":{"snapshot_id":"20261016_225144_205912_solve","reason":"run_complete"}}
{"kind":"run_status","payload":{"status":"completed","exit_code":0}}
{"kind":"distillation_failed","payload":{"error":"AuthenticationError"}}
```

### 4.2 断点续传实测(如文档)

- 第二次运行启动日志:`[*] Restored saved target state: http://localhost:3081` —— **跨 run 恢复真实生效**;`targets/<id>/index.json` 记录 `latest_run`/`latest_snapshot_id` 指针。
- CLI 面:`--resume/--no-resume`(默认 resume)、`--snapshot <id>`、`--resume-run <name>`、`--runs-dir`、`--force-fresh`、`--repair`。
- 会话账本 `sessions/*.json` 的 `resume_meta`:executed_steps、verified/pending_findings、resume_strategy(本次失败后策略=continue_recon,理由「侦察维度未完成: server, website, domain, personnel」)、checkpoint_reason=failed、snapshot_id、run_dir。
- 上游自测:`pytest tests/run/test_run_persistence.py` → **12 passed**。

### 4.3 插件真跑(它自己的代码路径,非 LLM)

输入取自靶场真实响应(只读 GET):

```bash
curl -sS -D headers.txt -o /dev/null http://localhost:3081/
vulnclaw plugins run builtin.web.headers --target http://localhost:3081 --stage discovery --input headers-input.json --json
```

**发现 1(low,confidence 0.75)**:Missing common security headers
- 证据:`missing_headers = [content-security-policy, x-frame-options, x-content-type-options, referrer-policy, strict-transport-security]`(实测响应头仅 Vary/Content-Type/Cache-Control/Etag/Date/Connection/Keep-Alive/Content-Length 8 个)。
- 复现:`curl -sI http://localhost:3081/`。
- 附带元数据:checked_headers 列表、elapsed 0.002s、**remaining_requests=29**(单目标插件请求预算 30,预算计数真实生效)。

**发现 2(info,confidence 0.8)**:JavaScript endpoints discovered
- 输入:Vite dev server 直接吐出的前端源码(/src/main.ts、/src/router/index.ts、/src/App.vue,共 17.9KB)。
- 证据:`endpoints=[/admin/users, /assets]`,`interesting_endpoints=[/admin/users]`(命中 admin 敏感词)。
- 复现:`curl -s http://localhost:3081/src/router/index.ts`(dev server 源码直出本身即是信息暴露面)。
- 摩擦点:插件期望的输入键是 `content`(纯字符串)而非直觉的 sources 列表,先跑了一次 "No content was supplied" 才翻源码改对——插件输入契约无 schema 提示。

### 4.4 报告生成(确定性主体 + 可选 LLM 增强)

`vulnclaw report <session.json>`:LLM 攻击摘要小节 401 失败,**报告仍完整生成**(`sessions/report_*.md`)。结构:1 项目概述(含「任务约束:仅主机 localhost」)/ 2 执行摘要(已验证·误报排除·待验证计数 + 风险等级分布表)/ 3 详细发现 / 6 附件(pocs/、evidence/traffic/ requests.jsonl+原始报文、screenshots/)。页脚原则:**「未经验证的漏洞 = 误报 = 不写入报告」**。

---

## 5. 三环飞轮实测

### 5.1 真值结算(它怎么判定「真发现」)

- **FINAL 证据闸门**(`agent/solver.py` `_completion_gate`):目标含 flag/shell 时,FINAL 文本必须包含 flag 且引用真实证据 id(如 e001);无工具证据/未引用 → `Completion rejected` 把拒绝原因回灌模型继续做。NO_PATH 同样受「近成功闸门」约束(高信号锚点未耗尽不许判死)。
- **发现级生命周期**(`config/domain_models.py` VulnModel):`mark_verified/mark_rejected` + `verification_status` + `evidence_level`(L0–L3)+ verified_at/note——误报被显式标死而非静默丢弃,报告里还有「已排除的误报」小节。
- **报告级原则**:未验证不写入(§4.4 页脚)。
- **实测**:401 场景结算为 `steps=0 evidence=0 findings=[]`、事件账本记 `distillation_failed`——降级路径同样走真值结算,没有编造。⚠️ 闸门本身依赖模型产出文本后校验,本轮无法验证「有 LLM 时闸门拦假 flag」的实际拦截率(其测试套件有覆盖,未逐条复跑)。

### 5.2 知识库真转了吗

- **静态部分真实存在**:`kb/{tools,cve,payloads,protocols,techniques}` 种子数据随首次运行落盘(nmap 速查、Burp 工作流、XSS/SQLi/RCE bypass 技法等);检索=中文感知 BM25,无 chromadb 时降级关键词模式(启动横幅实测可见)。
- **动态闭环(经验教训)**:`run 结束 → distill_run(需 LLM)→ ExperienceStore 落 pending → 人工 vulnclaw experience 审批 approve/reject → 批准后才经 experience_context 注入提示词`。带工程细节:近重复合并(阈值 0.8)、置信度半衰期(`effective_confidence`)、scope 校验(`validate_scope`)。
- **实测判定:本环境飞轮没有真正转动**——蒸馏第一跳就 401,`kb/experience/` 为空目录。结构在、油路通,但没有燃料(LLM)与司机(人工审批口),轮子不转。如实记录。

### 5.3 度量

- **有的**:过程度量齐全——events.jsonl 事件流、run.json 生命周期字段、PluginResult 的 elapsed_seconds/remaining_requests、报告内风险分布/验证状态计数、`constraint_violations` 违规审计槽位(报告第 5 节专门呈现)。
- **没有的**:效果度量(发现召回/误报率/与基线对比/lesson 注入后命中率变化)。飞轮缺「轮速表」——转没转、转了值不值,当前无量化闭环。

---

## 6. 「当探隐战士层」接缝评估

### 6.1 输出格式(对接面)

- 事件流:`solve --stream` NDJSON(`{"type":"log|status|complete", ...}`),complete 事件内嵌 `findings[]`——可做管道消费。
- 插件:`plugins run --json` 的 PluginResult schema 规整(plugin_id/stage/ok/findings[{title,risk,vuln_type,evidence,remediation,confidence}]/messages/error_type/metadata/remaining_requests)。
- 报告:Markdown(中英双语模板)+ `write_findings_artifacts` 的 findings JSON 工件 + pocs/ 目录(Python/Bash PoC)。
- 评价:**机器可读三件套齐备**,适合程序化对接;报告为确定性生成(不依赖 LLM 重写),长文档消费方可预期。

### 6.2 账本结构(对账面)

三层,职责清晰:

1. `runs/<name>/run.json`——run 清单 + artifacts 指针 + resume 指针;
2. `runs/<name>/events/events.jsonl`——append-only 事件账本(run_created/checkpoint/run_status/distillation_*),审计友好;
3. `sessions/<ts>_<target>.json`——重账本:resume_meta(步骤/发现计数/恢复策略/checkpoint 原因/snapshot 指针)+ task_constraints + constraint_violations(_events) + reasoning{facts,constraints,paths} + agent_state{evidence,tool_calls,steps,verified_claims,pinned_facts,progress_signals,correction_hints}。
- 加上 `evidence/traffic/`(requests.jsonl 索引 + 每请求原始报文),构成「事件-状态-证据」三级留痕。**适合当战士层的对账底座**;注意 evidence 是「按运行内作用域过滤后落盘」(traffic/scope.py),越界流量不存档。

### 6.3 scope 执法点(重点实测坑)

执法网络(代码定位):

| 执法点 | 位置 | 说明 |
|---|---|---|
| fetch/探针 host+path | `builtin_tools.enforce_host_path_constraints` | allowed/blocked hosts+paths |
| 端口约束 | `builtin_tools.enforce_port_constraints` | nmap/批量探测的 allowed/blocked_ports,violation 消息带 `[constraint_violation]` 前缀 |
| shell/python 代码内 URL 扫描 | `_validate_command_url_scope` / python_execute 正则 | 从代码文本里抓 URL 逐个过 host/path 闸 |
| MCP 生命周期 | `mcp/lifecycle.py:203` | 出站端口白名单 |
| 插件运行时 | `plugins/runtime.py:204` | allowed_ports 复查 |
| 流量记录过滤 | `traffic/scope.py ScopeChecker` | **只管「记不记」,不管「发不发」**——注意与上面五处的区别 |

**实测坑(关键)**:goal 自然语言只被 `input_analysis.extract_task_constraints` 的**固定正则**解析(如「只测/仅允许测试 3081 端口」这类句式才进 allowed_ports)。本次 goal 措辞「除目标3081端口外禁止触碰任何其他端口」**不命中任何句式** → 会话账本里 `allowed_ports=[]`,只有 `allowed_hosts=[localhost]`(自动取自目标 host)+ strict_mode=True。也就是说:**同主机其它端口(正是本任务的禁碰清单)在端口维度不受硬执法,只剩提示词软约束**。

结论与建议:接它当战士层时,scope 必须走结构化通道——`vulnclaw run --only-port 3081` / TUI 范围菜单(菜单3)构造 TaskConstraints,或平台侧直接注入 TaskConstraints 对象;**永远不要指望模型读 prompt 自觉**。补充:CLI 任务级 scope 旗标(`--only-port/--exclude-host/--exclude-path/--allow-actions`)挂在 `run` 等命令上,**solve 子命令未暴露**(solve --help 实测无此项),这是接缝上的一个缺口。

### 6.4 审批口

- `safety.permission_mode` 三档:`ask`(默认,每次 y/N,300s 未响应自动拒)/ `auto_review`(只读白名单直行,其余仍问;可加 trusted_commands 前缀)/ `full_access`(全放行,文档明示提示注入可致无确认任意命令执行)。
- 通道实现(`cli/approval_channel.py`):**真 TTY 才装审批通道;headless 运行/Web 任务/子代理一律无通道 → 闸门直接拒绝**(fail-closed,代码注释明示「deliberately no session-level allow」——单次审批不跨请求复用)。
- 旁路设施:python_execute 独立开关+50 行上限+审计落盘;插件 `--allow-destructive` 显式门;`safety.trusted_commands` 以禁用名开头的条目会被拒。
- 对接启示:平台无人值守跑法 = `auto_review` + 最小白名单;高危动作(利用类)保留人工口;它的 headless fail-closed 语义与外层调度器的审批 UI 天然互补——**外层得自己实现「无 TTY 时的审批代理」**,否则 headless 下危险工具全被拒。

---

## 7. 复现附录

```bash
# 环境
export VULNCLAW_CONFIG_DIR=/tmp/vulnclaw-home
V=/tmp/vulnclaw-venv/bin/vulnclaw

# 1) doctor + 帮助面
$V doctor
$V solve --help          # 注意 --max-steps 默认 240;无 --only-port

# 2) 卡点复现(占位 key)
$V config provider deepseek
$V config set llm.api_key <占位>
$V solve http://localhost:3081 --goal "授权靶场只读安全评估" --max-steps 30 --run-name t1 --stream
# → 三轮 401 → {"type":"complete","summary":"⊘ not reached — steps=0 evidence=0"}

# 3) 非 stream 崩溃复现(P0)
$V solve http://localhost:3081 --goal x --run-name t0    # UnboundLocalError: on_event

# 4) 插件真跑
curl -sS -D h.txt -o /dev/null http://localhost:3081/
# headers-input.json = {"headers": {...小写头字典}}
$V plugins run builtin.web.headers --target http://localhost:3081 --input headers-input.json --json

# 5) 断点续传
$V solve ... --run-name t1 --stream ; $V solve ... --resume-run t1 --stream   # Restored saved target state

# 6) 上游持久化自测
cd /tmp/vulnclaw-src && /tmp/vulnclaw-venv/bin/python -m pytest tests/run/test_run_persistence.py -q
```

工件位置:运行账本 `/tmp/vulnclaw-home/{runs,sessions,targets,kb}`;插件输入/输出 `/tmp/vulnclaw-runbox/`;源码快照 `.research/repos/VulnClaw`(只读)。

---

## 8. 未尽事项(下轮补)

1. **LLM 战果空缺**:拿到有效 key(或装 Ollama+工具调用型模型)后重跑本剧本,补:工具调用序列画像、模型主导循环的真实步态、FINAL 闸门实际拦截行为、lesson 蒸馏产物样例。
2. solve 子命令的 scope 旗标缺口、`solve` 非 stream P0 bug → 值得向上游提 issue(先核对 main 分支是否已修)。
3. 靶场凭据路径(登录后的授权面验证)本轮未触达,原因见 §3。
4. 子代理编组(`VULNCLAW_SUBAGENT_*`)、persistent 周期模式、web/tui 面板未测(超本轮范围)。

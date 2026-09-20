# 探隐 vuln_agent — 源码安全分析引擎（最新源码定稿）

> **这份是什么**：vuln_agent 的引擎专项设计页——探隐 v2 首批二号引擎（cli 型适配器）的原稿全景。
> **怎么读**：先看 §1 定位与 §2 架构全景建立整体感，再按 §3 八段管道逐段下钻；§7 是"v1 整理稿 vs 最新源码"差异对照，§8 讲它怎么接进探隐 v2。
> **以谁为准**：本文以 `docs/design/imported/vuln-agent/vuln_agent-main/` 最新源码考古结果为准（事实带文件:行号证据），叙述骨架沿用用户 v1 整理稿。

## 1 项目定位

vuln_agent 是一款基于 LLM 的多阶段源码安全分析管道，通过 **8 段串并联管道**从目标源码中自动发现攻击面、拆分与排序、追踪数据流、规划并分析潜在漏洞，最后以对抗式复核验证结论。

**核心依赖**：

- 子进程 CLI 执行器（opencode wrapper：临时 profile 隔离 + 8 个禁用环境变量 + skill deny-all 白名单；后期新增 codeagent 3.0 / GLM-5.1-Alpha-Auto 支持）
- Python 3 双线程池并发控制（pool(max_workers) + vpool(vuln_workers)）
- 提示词模板 + `{include:}` 规则引用机制（prompts/ 与 references/ 分离）

**一句话**：发现攻击面 → 拆分/排序 → 业务流分析 → 漏洞规划 → 漏洞分析 → 对抗复核 → 用户自定义后处理，全部 LLM 交互经子进程 CLI 完成。

## 2 架构全景

### 2.1 总览图（最新源码实测）

```text
+----------------------------------------------------------------+
|                     vuln_agent (最新版)                         |
|                                                                |
|  run.py (CLI 入口)                                             |
|    +- biz_recon/runner.py (兼容壳: 读 yaml 配置)               |
|         +- biz_recon/pipeline.py::run()  <- 真正的管道调度器    |
|              双线程池 pool(max_workers) + vpool(vuln_workers)   |
|                                                                |
|  +- Phase 1    surface_discover  攻击面识别   (每 work_dir) -+  |
|  +- Phase 1.5  surface_split     复合面拆分   (每 surface)   |  |
|  +- Phase 1.6  surface_rank      优先级排序   (>30 才触发)   |  |
|  +- Phase 2    surface_analyze   业务流深析   (每 surface)   |  |
|  +- Phase 2.5  vuln_planner      漏洞任务规划 (每 surface)   |  |
|  +- Phase 3    vuln_analyze      漏洞分析     (每 task)      |  |
|  +- Phase 3.5  review_vuln       对抗复核     (每 finding)   |  |
|  +- Phase 4    vuln_postprocess  自定义后处理 (每 review)    |  |
|  +------------------------------------------------------------+  |
|                                                                |
|  opencode_wrapper.py   LLM 调用隔离封装（核心工程亮点）          |
|  workspace.py          纯文件持久化 + 幂等标记（db.py 已移除）   |
|  report.py / collect.py 单页静态报告 / 多目标收集               |
+----------------------------------------------------------------+
```

### 2.2 LLM 调用闭环（每段触发）

```text
Stage 模块 (如 surface_analyze.py)
    |  {target_work_dir} {surface_file} 等模板变量
    v
prompt.py (加载 prompts/*.txt 模板 + 解析 {include:} 引用)
    v
biz_recon/references/*.md (FALSE-rules / vuln_rules_index / constraints …)
    v
opencode_wrapper.py (临时 profile -> 子进程 CLI -> LLM)
    v
输出文件 (.md) 写入 .vuln_agent_output/{stage}/
```

## 3 执行流程：八段管道

### 3.1 串并联总图

```text
Phase1 discover -> 1.5 split -> 1.6 rank -> Phase2 analyze -> 2.5 planner
  (每 work_dir)   (每 surface) (>30触发)   (每 surface)   (每 surface)
                                                   |
                          Phase3 vuln_analyze <-----+ (每 task · vpool)
                                | 流式：高危 finding 先行提交复核
                          Phase3.5 review (每 finding · 内联于逐 surface 循环)
                                |
                          Phase4 postprocess (每 review)

输入: 目标源码目录
输出: .vuln_agent_output/
      |- discovered_surfaces/   (Phase 1)
      |- analyzed_surfaces/     (Phase 2)
      |- vuln_plans/<stem>/     (Phase 2.5)
      |- vuln_findings/         (Phase 3)
      |- vuln_reviews/          (Phase 3.5)
      |- vuln_postprocess/      (Phase 4)
      |- meta/  (priority.jsonl / excluded-paths.md / error/)
      +- thinking/ (thinking_manifest.jsonl)
```

并发档位：代码默认双池 5/5；随附 yaml 配置 **3/5**（实际生效以 yaml 为准）。各 Stage 模块函数签名默认 max_workers=3，但全管道模式下以 workers=1 逐 surface 调用——并行度统一由外层双池承担。

### 3.2 Phase 1 — surface_discover（攻击面识别）

**目标**：智能分析项目结构，按体量选择识别策略，枚举所有攻击面（REST/MQ/gRPC/WebSocket/GraphQL/SCRIPT/TOOL/CRON/CLI）。

| 项 | 值 |
|---|---|
| 模板 | prompts/identify-surfaces.txt |
| 变量 | {target_work_dir} {extra_prompt} |
| 输出 | discovered_surfaces/*.md + meta/excluded-paths.md |
| 幂等 | .surface_discover_done 存在即跳过 |

检测逻辑（单次 LLM 调用每 work_dir）：

1. 扫描目录结构、文件规模、技术栈（Spring Boot/Django/Go…），评估代码体量
2. 制定派发策略：小项目单次完整识别；中项目按顶层模块分批；大项目按子目录派发子任务独立识别后汇总
3. 枚举攻击面（仅识别不深析），每条目写 discovered_surfaces/{type}-{category}-{slug}.md

产物示例：

```markdown
# 攻击面条目
- **类型**：noniface
- **分类**：CLI
- **来源**：/mntr.go:19
- **描述**：untar工具 - 文件解压操作
- **发现**：涉及文件操作，可能存在路径遍历风险
```

### 3.3 Phase 1.5 — surface_split（复合面拆分）【新增】

**目标**：把混装多个攻击面的条目原地拆干净，保证后续每 surface 分析粒度一致。

| 项 | 值 |
|---|---|
| 模板 | prompts/split-surface.txt |
| 触发 | 仅全管道模式执行；完成后刷新 all_surfaces |
| 幂等 | .surface_split_done；--force-surface 重跑时删除重做 |

检测逻辑：多攻击面信号 = 多个"# 攻击面条目"标题/多组字段块。agent 拆分写出新文件，Python 校验落盘成功后删除原文件（LLM 写、代码验）。

### 3.4 Phase 1.6 — surface_rank（优先级排序）【新增·条件触发】

**目标**：攻击面 **>30 个**时才触发（每 work_dir 一次全局 LLM 排序），产出分发顺序，把有限预算花在刀刃上。

| 项 | 值 |
|---|---|
| 模板 | prompts/rank-surfaces.txt |
| 输出 | meta/surface-priority.jsonl（存在即复用，删除即重排） |

排序信号：暴露/可达性（REST/Web > MQ/gRPC > CLI/脚本）、"发现"字段高危操作信号、输入丰富度、信任边界。

### 3.5 Phase 2 — surface_analyze（业务流深度分析）

**目标**：对每个攻击面独立深度分析，绘制 Mermaid 流程图，追踪入参流向，检查关键控制点。

| 项 | 值 |
|---|---|
| 模板 | prompts/analyze-surface.txt（{include:flow-principles.md}） |
| 输出 | analyzed_surfaces/{同名 surface 文件} |
| 幂等 | 同名分析文件存在即跳过 |

检测逻辑（每 surface 一次 LLM 调用）：

1. 入参维度分析：path/query/header/body 参数树；注解式校验（@NotNull/@Size/@Pattern/@Valid）
2. 关键控制点清单：文件上传（后缀/MIME 白名单、路径规范化）、命令执行（拼接/白名单）、SQL 操作（参数化 #{} vs 拼接 +）、HTTP 外呼（TLS/主机名/URL 拼接）、文件 I/O、认证鉴权
3. 数据流追踪：常量传播（static final/@Value 代入）、变量标记（运行时输入保留 {var}）、边界记录（三方库断点记函数名+文件+行号）
4. Mermaid 流程图：红高 = 高危操作 + 拼接外部用户输入；黄低 = 高危操作但无外部输入

产物示例（cli-go-entry.md 关于 untar 工具）：

```markdown
### 关键控制点
**文件写入**：
    // untar.go:96
    dstName := filepath.Join(dst, hdr.Name)  // 用户输入dst + hdr.Name拼接
    // untar.go:103
    dstFile, os.OpenFile(dstName, O_CREATE|O_RDWR, hdr.Mode)

**关键发现**：路径遍历风险——tar 包内文件名 hdr.Name 直接拼接到目标目录路径，
未做 ../ 过滤
```

### 3.6 Phase 2.5 — vuln_planner（漏洞任务规划）

**目标**：根据 Phase 2 分析结果，为每个攻击面规划具体漏洞测试任务。（旧名 plan_vuln_tasks，已改名。）

| 项 | 值 |
|---|---|
| 模板 | prompts/vuln-planner.txt（最高优先级引用 FALSE-rules.md） |
| 输出 | vuln_plans/{stem}/{high|medium|low|none}-risk-{n}.md |
| 幂等 | vuln_plans/<stem>/ 目录存在即跳过 |

任务划分规则：一个疑点一个任务（独立验证互不重复）；同一敏感操作的多个参数合并为一个任务；同一参数流向多个敏感操作必须拆分；C/C++ 额外规划内存安全任务。计划文件只述疑点不展开论证。

产物示例：

```markdown
# untar工具 - 路径遍历漏洞
**验证目标**：路径穿越
**疑点位置**：r.go:96
**疑点原因**：tar包内文件名hdr.Name直接拼接到目标目录路径，未做 ../ 过滤
**优先级**：高
```

### 3.7 Phase 3 — vuln_analyze（漏洞分析）

**目标**：对每个规划任务执行具体分析，输出结论标签。

| 项 | 值 |
|---|---|
| 模板 | prompts/analyze-vulnerability.txt（引用 vuln_rules_index.md + constraints.md） |
| 输出 | vuln_findings/{VULN|NOVULN|SUSPECTED}-{surface_stem}-{n}.md |
| 并发 | vpool(vuln_workers)；高危 finding 流式先行提交复核 |

认定三档（现行版）：

| 档位 | 条件 | 前缀 |
|---|---|---|
| 确认有漏洞 | 有实际漏洞代码路径 + 确认无防护 | VULN- |
| 确认无漏洞 | 有风险但防护有效 / 不涉高危操作 | NOVULN- |
| 无法确认 | 信息不足无法判断 | SUSPECTED- |

举证要求（每条结论须代码级事实支撑）：路径穿越 = 拼接代码 + 无规范化/无 ../ 校验；命令注入 = 用户输入拼接 + 无转义/白名单；SQL 注入 = 拼接而非参数化。仅"确认"档做 Payload 迭代验证。

产物示例：

```markdown
# untar工具 - 路径遍历漏洞
**类型**：路径穿越    **位置**：r.go:96
**CVSS 评分**：8.1    **严重性**：高
**触发条件**：命令行传入恶意构造的 tar 包，包内文件名包含 ../
**Payload**：
    echo "test content" > test.txt
    tar -cvf malicious.tar ../test.txt
    ./untar malicious.tar /opt/pkgs/a/
    # 文件被写到 /opt/test.txt 而非 /opt/pkgs/a/test.txt
**事实依据**：
    // untar.go:96 - 路径拼接无 ../ 过滤
    dstName := filepath.Join(dst, hdr.Name)
```

### 3.8 Phase 3.5 — review_vuln（对抗复核）

**目标**：以**挑战者姿态**审查 Phase 3 每个结论，降低误报（独立于分析 agent，逐 finding 一次调用，内联于逐 surface 循环）。

| 项 | 值 |
|---|---|
| 模板 | prompts/review-vulnerability.txt（{include:verify-principle.md}，参考 non-vuln-scenarios.md） |
| 输出 | vuln_reviews/{VULN|NOVULN|SUSPECTED}-{vuln_file_stem}.md |
| 语义 | **复核改名即结论变更**，可嵌套（如 VULN-VULN-…） |

质疑清单：业务场景下真的成立吗（补偿措施）？payload 能否绕过中间校验？攻击步骤是否完整可实施？分层架构里有没有没考虑的防护层？

验证原则：文件输入一般后台固定（除非有篡改证据）；环境变量一般后台写死（除非外部可控）；认证缺失不必然是漏洞（可能在网关统一处理）；注入输入来自数据库无法判外部可控 → SUSPECTED。

复核理由示例（VULN-cli-go-entry-1-1）：filepath.Join 会处理 .. 组件，但 tar 内文件名 ../../etc/passwd 拼接 /opt/pkgs/a/ 结果为 /opt/etc/passwd——仍可写到目标目录父级，属真实路径穿越。

### 3.9 Phase 4 — vuln_postprocess（自定义后处理）【新增】

**目标**：每份复核结论接一段**用户自定义后处理钩子**（模板化 prompt，输出 POST-{review_stem}.md）——留给使用者的扩展位（如按客户口径改写、内部知识库归档格式）。

## 4 LLM 调用隔离（opencode_wrapper）

工程亮点：LLM 调用全部经子进程 CLI 隔离封装，五层防线：

1. **临时 profile**：每次 run() 用 tempfile.mkdtemp 建独立 profile（config/data/cache/logs/state），结束 rmtree 清理
2. **8 个禁用环境变量**：OPENCODE_DISABLE_CLAUDE_CODE(_SKILLS/_PROMPT)/DEFAULT_PLUGINS/AUTOUPDATE/MODELS_FETCH/PRUNE + SKIP_SAFE_CHECK
3. **skill deny-all 白名单**：permission.skill 默认对 * 拒绝，仅放行本次选中 skills，屏蔽系统/.claude/插件 skills
4. **超时硬杀**：按进程组 SIGKILL，无自动重试（失败显式暴露）
5. **遗留说明**：--pure 隔离模式仅存于已不被调用的 _run_direct() 路径（历史层）；后期新增 codeagent 3.0 / GLM-5.1-Alpha-Auto 执行器

## 5 持久化与幂等（workspace.py）

**SQLite db.py 已整体移除**（全仓 grep 零命中），改为纯文件系统状态机：

- 目录树：.vuln_agent_output/{discovered_surfaces, analyzed_surfaces, vuln_plans/<stem>/, vuln_findings, vuln_reviews, vuln_postprocess, meta/error, thinking/}
- 幂等标记：.surface_discover_done / .surface_split_done / .phase3_done（Phase 3 中低危整段完成标记，存在即跳过；删除即重做）
- 排序缓存：meta/surface-priority.jsonl 存在即复用
- skip-if-exists：分析同名文件存在跳过；vuln_plans/<stem>/ 目录存在跳过
- thinking_manifest.jsonl：思考过程索引，报告阶段把 thinking 挂回 surface/finding

报告层：report.py 扫描输出目录生成单页静态报告（report-data.js + report.html + assets：marked/highlight/mermaid）；collect.py 多目标收集成 dashboard。

## 6 结论前缀与分级体系（现行版）

| 层 | 前缀 | 语义 |
|---|---|---|
| 分析 | VULN- | 确认有漏洞 |
| 分析 | NOVULN- | 确认无漏洞（承担旧 DISMISSED-/CLEAN- 的"排除"语义） |
| 分析 | SUSPECTED- | 无法确认（承担旧"存疑"语义） |
| 复核 | {前缀}-{分析文件名} | 复核改名即结论变更，可嵌套 |
| 后处理 | POST- | 自定义后处理产物 |
| 计划 | {high|medium|low|none}-risk-{n} | 任务风险档位 |

代码侧正则多方一致：vuln_analyze.py / review_vuln.py / report.py / workspace.py 均只认 VULN/NOVULN/SUSPECTED 三前缀。旧稿的 DISMISSED-/CLEAN- 在本版零命中。

## 7 与 v1 整理稿差异对照

| # | 旧整理稿 | 最新源码 | 证据 |
|---|---|---|---|
| 1 | 五 Stage：discover/analyze/plan_vuln_tasks/vuln_analyze/review | **八段**：+split/+rank/+postprocess；plan_vuln_tasks 改名 **vuln_planner** | pipeline.py:95-310；旧名仅存 prompts-ext 未接线文档 |
| 2 | SQLite db.py 持久化 | **db.py 已移除**，workspace.py 纯文件幂等状态机 | 全仓 sqlite 零命中 |
| 3 | ThreadPoolExecutor max_workers=3 | **双池**：代码默认 5/5，随附 yaml 3/5；管道内逐 surface workers=1 | pipeline.py:96-97；analysis-config.yaml:27-30 |
| 4 | 前缀 VULN-/DISMISSED-/CLEAN-/SUSPECTED- | DISMISSED-/CLEAN- 零命中，现行 VULN-/NOVULN-/SUSPECTED- + 复核嵌套 + POST- | analyze-vulnerability.txt:37-47 等 |
| 5 | LLM 经 opencode CLI --pure 隔离 | --pure 仅存遗留死路径；现行隔离=临时 profile+8 env+skill deny-all | opencode_wrapper.py:373-379 vs 180-224 |

## 8 与探隐 v2 的衔接

v2（§6.4 引擎契约）把 vuln_agent 定为首批二号引擎、**cli 型适配器接入**：

- **统一提交 schema**：本引擎产物（facts/findings/assets/edges）由适配器转 submission.json，引擎不直接写 13 表账本；总控命令重算 dedup_key 与铸 ID
- **结论三档映射两维评级**：VULN/NOVULN/SUSPECTED 映射 confidence（C1/C2/C3/无-禁），impact 由复核证据补齐
- **纪律能力声明**：manifest 声明 max_op_level 与视角上限；源码分析属内部视角，适配器需在提交中标注视角层级
- **证据双哈希**：Payload/事实依据段（repro_command）进 E-index 四要素（network_position 由执行环境注入）
- **批次归属**：v2 批次 3（引擎接入批）；web-blackbox 先行、vuln_agent 随后复用同一契约

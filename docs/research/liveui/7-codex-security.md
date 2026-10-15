# codex-security（OpenAI 官方 LLM 源码安全审计）活体分析报告 —— 探隐白盒车道 B 候选件研究

> 分析对象：OpenAI `openai/codex-security` @ `/tmp/codex-security`（本地快照，版本 0.1.95，Apache-2.0；**严格只读**——未写入/未移动/未改名/零 git 操作）
> 分析日期：2026-10 · 分析者：探隐委托子代理（codex-security 分析舰）
> 证据基础：README/AGENTS/action.yml/Dockerfile/compose×3 + docker/ 全部 8 件逐文件 + sdk/typescript/src 85 文件（重点：deep-scan/coordinator/executor、deduplication×14、security-policy、scan-history）+ plugins/codex-security（mcp-app src/deep-scan×15、references×14、skills×16 的 SKILL.md、templates/deep-scan 双提示词）+ github-action/src×12 + docs/bedrock.md + evals/（triage-finding/secret-discovery/deep-reducer）；探隐侧 tanyin-product-v1.md（修正案 A 白盒双车道）与 6-gensift.md 对照。
> 规模实测：982 文件（含测试 196+56、夹具、锁文件），TypeScript/TSX ≈25.8 万行、Markdown ≈1.17 万行、seccomp 464 行、shell ≈230 行。

---

## 一、架构与流水线：find→validate→fix 全链怎么走

### 1.0 一句话总形态

codex-security 是一个**把"LLM 安全审计"做成工程化产品**的系统：CLI（`cs`）+ TypeScript SDK（`@openai/codex-security`）+ Codex 插件（skills + MCP server）+ GitHub Action 四形态同构，核心执行单元不是裸 API 调用而是**完整的 codex exec 线程**（`@openai/codex-sdk` 的 `startThread`，executor.ts:189-196）——每个审计 worker 是一个带独立权限沙箱、独立 MCP 工具、独立子代理配额的 Codex 会话。这与 GenSift"寄生宿主会话"恰成两极：GenSift 把确定性放在 TSV 账本外骨骼，codex-security 把确定性放在**宿主编排器（TypeScript 状态机）+ 语义产物 schema + 权限预检**三层。

### 1.1 四形态与目录分工

| 件 | 规模 | 干什么 |
|---|---|---|
| `sdk/typescript/src`（85 文件） | ~2.5 万行 | CLI+SDK 本体：scan/policy/dedupe/bulk-scan/scans/export 全命令、multiscan(1215L)、component-scan(501L)、custom-validation(451L)、security-policy(1132L)、scan-history-renderer(505L)、deduplication/ 子模块 14 件 |
| `plugins/codex-security/mcp-app/src/deep-scan`（15 文件） | ~6000 行 | **深扫引擎**：coordinator(1311L) 调度器、worker-runner(790L)、executor(932L) Codex 线程执行器、store(862L) 持久层、permission-profile-preflight(770L) 权限预检、parent-sandbox(256L) 父沙箱解析 |
| `plugins/codex-security/skills`（16 技能） | ~1500 行 | 提示词工作流：security-scan(标准)/deep-security-scan(深扫)/validation/fix-finding/verify-fix/threat-model/triage-finding/track-findings/vulnerability-writeup/propose-security-hardening/attack-path-analysis/security-diff-scan/assess-patch-risk/cloud-findings/define-security-policy |
| `plugins/codex-security/references`（14 件） | ~1200 行 | 核心方法论文档：**core-scan.md(109L)=审计宪法**、threat-model.md(64L)、scan-contract.md(198L)、static-finding-assessment.md(75L)、standalone-validation.md(11L)、final-report.md(215L) |
| `github-action/src`（12 文件） | 968 行 | CI 集成：inputs/main/sarif 安全断言/results/policy 闸门 |
| `docker/`（8 件）+ 根 Dockerfile/compose×3 | ~560 行 | 容器化批量扫描与三层沙箱（见第二节） |
| `evals/`（3 套） | — | promptfoo 三角校准（triage-finding + SASTBench）、secret-discovery 评分、deep-reducer 分页回归 |

### 1.2 Standard 扫描八步（core-scan.md 全文精读）

一次标准扫描（`cs scan .`，任意 discovery worker 内部同构）的完整协议：

1. **上下文解析**：继承 `SECURITY.md` 策略（嵌套最近优先，`resolve-security-md` helper 按目录逐个解析缓存）+ 用户上下文 + 可选威胁模型 + `CODEX_SECURITY_KNOWLEDGE_BASE` 知识库（覆盖生成假设，但永不覆盖显式用户指令）。**预先验证一条离线本地搜索命令**（优先现存 ripgrep，拒绝 DotSlash 等可下载 wrapper，回退 git grep/find/grep；禁止装工具/触发网络下载）。
2. **立即派基线子代理**（`fork_turns: "none"` 零上下文克隆）：只给它基线审计 prompt + 仓库路径/范围/上下文/策略/搜索命令，**不给本 reference、不给调查者 prompt、不给上层生成的威胁假设**——防锚定的干净对照组。基线 prompt 是一份完整 SAST 清单（SQL/NoSQL 注入、XSS、越权/IDOR、路径穿越、命令/代码注入、开放重定向、SSRF、反序列化、硬编码凭据、XXE、XPath、配置错误、DoS、头注入、上传、内存安全、请求走私、原型污染、危险代码生成、资源耗尽）+ 密钥专节。
3. **同时做独立架构评审**：读 threat-model.md 建威胁模型（六字段 canonical：summary/assets/trustBoundaries/attackerCapabilities/securityObjectives/assumptions + effectiveResources 验证表），**模型一到手立即以 `complete:false` 检查点保存**（不等发现）。
4. **调查包分组**（investigation packets）：按"共享攻击者+受保护资产+入口+预期控制+敏感操作+真实源码锚点"把源码问题分组，每包含 ID 与 repository-relative path:line。
5. **并行派聚焦调查者子代理**（数量由独立工作量决定，受 subagent 配额约束），四视角自选：**Forward**（攻击者输入→敏感操作）、**Backward**（从 sink/解析器/凭据发放回溯到攻击者）、**Authz/业务逻辑**（所有权/租户/权限/状态机/兄弟操作守卫差异）、**Open-ended**。调查者 prompt 明令"找到一个漏洞后继续查"（防 satisficing）。
6. **先落账再合并**：任何基线/调查者返回的候选**先经 `record_codex_security_scan_draft({complete:false})` 持久化**，每候选有稳定 `candidateId`；未验证候选带原始证据放 `coverage.deferred`；每个验证决策后再检查点一次。合并规则：只合并"共享同一失效控制+同一有效修复"的观察，**绝不因同 CWE 合并**。
7. **逐发现独立验证**（防假阳性核心，详见 1.4）。
8. **组装语义产物**：scope+threatModel+findings+coverage 四件套按 final-report.md/scan-draft.schema.json 装配；每发现必带：小写漏洞族 `ruleId`、taxonomy.category+CWE、真实 `provenance.source`、`root_control` 位置、全部受影响位置、校准 severity+rationale、confidence+rationale、`codeEvidence[]`（id/label/path/startLine/code/explanation 必填）、attacker-to-sink 可达性、可操作修复。

红线（core-scan.md 尾部）：发现/验证/攻击路径推理**全部在一次自足审计内完成**，禁止拆相位技能、禁止建排序相位、禁止逐文件/逐候选台账、禁止相位报告与回执文件——这是对"流程膨胀"的显式防御（与 GenSift 的元规则同源反向：GenSift 靠账本外骨骼防偷懒，codex 靠"禁止中间产物"防流程税）。

### 1.3 Deep Scan：并行 discovery worker 机制（coordinator.ts 1311 行精读）

深扫 = **map-reduce 状态机**：`N 个并行 discovery worker → FIFO 缓冲 → 1 个串行 reducer`，宿主 TypeScript 代码全权调度，模型只做内容。

**调度循环（runScheduler）**：
- 并发上限 `config.workers`，总派发上限 `config.maxDiscoveryRuns`；每 worker 一个新 codex 线程（`discovery-0001` 递增标签 + randomUUID）。
- worker 完成序进 FIFO buffer；**reducerReady 门槛**：首次归并需 buffer ≥2 个独立发现（"两个独立发现确立首次语义归并"），此后任意一次归并可单独成立，或最后一个 worker 在上限处单独归并。
- **单个串行 reducer**（`dedup-000N`）一次认领整个 buffer；归并进行中新完成的 discovery 进 buffer 等下一轮——注释明说设计意图："在归并之间回填 discovery，防慢 reducer 积压未检积压"。
- **收敛判据 `saturated`**：`noNewStreak ≥ stopAfterNoNew && buffer 空`（连续 N 轮归并无新发现=语义饱和）；**`capped`**：派发到 maxDiscoveryRuns；**时限**：默认 96 小时 discovery 截止（`maxTimeHours`），到点 abort 后已完成的仍被归并。
- **故障语义**：worker 失败分可替换（`policy_refusal`/`transient_error`/`invalid_discovery_artifacts` 三类，重派）与致命；重试退避 60s/180s/540s；连续错 `stopAfterConsecutiveErrors` 停扫。**饱和后迟到的 worker 失败不再 fail 扫描**。
- **崩溃恢复**：重启后 `recoverAcceptedDiscoveries` + `recoverCompletedReducers` 从持久化 worker 状态重建（校验 resultManifestPath/completionSequence 完整性，缺证据即抛错）；5 秒心跳 + `coordinatorGeneration` 租约 + `handoffClaimToken`——失去租约即自停（`deep_scan_coordinator_lease_lost`），被更高代 coordinator 替换时可选 observeReplacement。
- 产物：父扫描 `scan-manifest.json`+`findings.json`+`coverage.json`（未封口），由 `complete_codex_security_scan` 校验封印并确定性投影出 `report.md`——**报告是下游投影，永不由模型手写**。

**worker 执行（executor.ts）**：每 worker 配 `approval_policy:"never"` + 专属权限 profile（`extends :read-only` + 继承父 deny 列表 + `network:{enabled:false}`）+ 一个 `cs_artifacts` 紧凑 MCP server（用 env 把工件根/仓库根/scanId 绑死，worker 只能写自己的工件目录）+ skills 路径注入。**开工前先 preflight**：用真实 codex 二进制验证权限 profile 确实生效（permission-profile-preflight.ts 770 行）才放行——防"配置看似生效实际未锁"。

### 1.4 候选→验证怎么防假阳性（七道闸）

1. **候选/发现两态分离**：`coverage.deferred[]` 存未验证候选（带原始 payload + `candidateId`），验证过的才进 `findings`（同 `provenance.candidateId` 可追溯）；被拒的候选**不删**，进 `rejected` coverage surface 并保留反证——审查者可复核每次否决。
2. **独立单次重验**：每个 unique finding 由主审计者**独立**对本地源码再走一遍：attacker→entry point→trust boundary→attacker-controlled dataflow→transformations→broken control→sensitive operation→prerequisites→effective mitigations→**strongest counterevidence**→concrete impact 全链元组，四个摘要（rootCause/validation/dataflow/reachability）必须源码背书。
3. **反证义务**：只有"源码背书的反证"能否决候选；"理论问题""缺运行时复现"**不是**否决理由（明文：missing deployment evidence lowers confidence, does not defeat a source-backed vulnerability）。secret 专判：disclosure path = 源码读者获得超越读源码本身的凭据访问权，**无需执行代码或攻击者输入**；测试文件名/占位符断言单独不足以定性或否决。
4. **动态验证阶梯**（validation skill）：crash PoC → valgrind/ASan → 非交互 gdb/lldb 追踪（`-batch -ex run -ex bt`）→ 最小测试 → 真实接口复现（HTTP/CLI/解析器/RPC/插件钩子）→ 静态回退（static-finding-assessment.md 七元组：source/control/sink/reachable path/boundary/counterevidence/proof gaps）。**大仓模式**：同族第一个强证明成立后，sibling 候逐个核 source/最近 control/sink/impact 即可，不重复深挖。
5. **人工反馈回喂**：`false_positive_feedback.json`（或 `<scan_dir>/artifacts/01_context/` 下）作 untrusted data 读入，**仅当记录的理由在当前源码与控制下仍然成立**才压制匹配发现——"假阳性标签本身不足以否决发现"。
6. **双通道冗余**：基线子代理（零假设）+ 调查者（威胁模型引导）独立产出，验证层合并——单通道幻觉需同时骗过两条路径。
7. **盲验证输出契约**（verify-fix/standalone-validation）：三态/四态判定（reportable/suppressed/not_applicable/deferred；fixed/still_vulnerable/inconclusive）+ 每候选必留 validation receipt（方法/证据/确切 proof gap/disposition/survives: yes/no/uncertain）。

### 1.5 Fix 链：补丁生成与验证

`fix-finding` 技能定义六层优先级（**永不拿前置换后置**）：分类正确（vulnerable/safe/unproven）> 边界完全闭合 > 合法行为保留 > 仓库检查通过 > 仓库惯例 > 最小性。流程：补丁前调查（安全边界+兼容性调查者子代理，fork_turns none）→ 在共享边界打最小仓库原生修复 → **自我攻击**（检查每个被改 helper 的全部 caller、每个条件的两分支，找仍达 sink 的 sibling 路径和被误伤的合法输入）→ 补丁候选独立评审（**bypass and regression reviewer**：只给 finding+diff，不给修复理由和"测试已过"声明，防确认偏误）→ 有序验证门（diff/语法→安全触发器+替代恶意输入类→合法控制+既有测试）。工作台三阶段 **Generate/Apply/Verify**：补丁先写 canonical unified diff（generate），按记录的 base revision+digest 精确应用（apply），只读验证（verify）——三阶段身份绑定 scanId/occurrenceId/actionToken/expectedVersion，**chat 回复不算完成，必须落工作台状态**。

---

## 二、沙箱设计精读：OpenAI 级安全执行参考（逐文件）

这是全仓最值得探隐抄的部分：**六层防御纵深**，从外到内：Docker（uid/cap/nnp）→ seccomp allowlist → AppArmor → Codex 原生 Bubblewrap（worker 级 read-only+断网）→ 入口点卫生（参数/凭据）→ 提示词级（userContext 一律 untrusted、禁止 fetch URL）。

### 2.1 docker/codex-security-seccomp.json（464 行）

默认动作 `SCMP_ACT_ERRNO`（拒绝一切），再 allowlist ~340 个系统调用（含 x86_64/aarch64 双架构 archMap 与 ARM 兼容调用）。四个精妙处：

1. **socket() 按参数过滤**：只放行 domain `<38`、`==39`、`>40`——即**精确封堵 AF_ALG(38)（内核 crypto API，可用来攻击内核加密子系统）与 AF_VSOCK(40)（虚拟机 socket，hypervisor 主机逃逸通道）**，放行 AF_NFC(39)。比 Moby 默认 profile（只堵 AF_APPLETALK）更贴合"不可信代码执行"威胁模型。
2. **namespace/mount 调用组放行**（clone/clone3/mount/mount_setattr/move_mount/open_tree/pivot_root/setns/umount/umount2/unshare）带注释明说设计：*"Allow Codex's unprivileged Bubblewrap user and mount namespaces; run with --cap-drop ALL and no-new-privileges"*——**seccomp 层允许、capability 层清零、AppArmor 层再圈**的分层思路：让无特权 Bubblewrap 用户命名空间可用（Codex 0.156.1 起文件系统受限执行必须 Bubblewrap，Landlock 旧路已废），同时特权 mount 不可达。
3. **Landlock 调用放行**（landlock_create_ruleset/add_rule/restrict_self）：为 Codex 自身的 LSM 沙箱留路。
4. ptrace/process_vm_readv 仅 minKernel≥4.8 放行；personality 只放行 5 个安全值。

### 2.2 docker/codex-security.apparmor（42 行）

profile `codex-security-container`，与 seccomp 互补而非重复：**允许** network/unix（扫描需出 API）、capability、mount/umount/pivot_root/**userns**（Bubblewrap 依赖）、`deny network alg`；**信号收窄**：只允许从 unconfined/runc/crun/docker-default receive、同 profile 内 send/receive——容器内进程不能给宿主侧进程发信号；**/proc 写拒绝四连**（通配排除 /proc/数字、/proc/sys 非内核子树、sysrq-trigger、kcore）；**/sys 写+特定子树 rwklx 拒绝**（cgroup/firmware/powercap/kernel-security）；ptrace 限同 profile。flags=(attach_disconnected,mediate_deleted) 保证已删文件/分离挂载仍被仲裁。

### 2.3 docker/entrypoint.sh（95 行）

纯 POSIX sh（dash 可跑）的入口卫生教科书：① **bulk-scan 参数白名单机**：逐参数状态机识别 --help/-h/--llms/--llms-full/--schema/--version 元数据命令放行；`bulk-scan` 子命令必须有 CSV 输入，"交互式发现在此镜像不支持"（exit 2）；拒绝 `--` terminator 与重复 bulk-scan；约值选项（--config/--workers/--mode/--model/--effort/--provider/--max-cost/--token-offset 等）登记跳过。② **凭据装配防注入**：有 GH_TOKEN 时才装配 git credential helper；`CODEX_SECURITY_GIT_HOST` 主机名严格校验（拒绝空/点开头/双点/非法字符）后才进 git config key；`GIT_CONFIG_COUNT` 限 0-128；然后 `exec codex-security "$@"`（PID 1 即 CLI，信号直达）。

### 2.4 docker/verify-container-sandbox.sh（27 行）——"三验"之一：运行时沙箱自检

探测 Docker 的 apparmor 安全选项 → 有则 `install -m 0644` profile 到 /etc/apparmor.d/、`apparmor_parser -r -W` 加载、`grep -Fxq 'codex-security-container (enforce)'` 内核 profiles 文件**确认 enforce 态**、写 COMPOSE_FILE 叠加链到 GITHUB_ENV；然后 `docker run --rm --cap-drop ALL --no-new-privileges --seccomp=... [--security-opt apparmor=...] --entrypoint node IMAGE .../codex.js sandbox /usr/bin/true`——**在目标镜像内实际执行 Codex 自带沙箱自检命令**（跑通 Bubblewrap 沙箱内 /usr/bin/true），验证的是"端到端沙箱可用"而非"配置文件存在"。

### 2.5 docker/verify-container-compose.sh（40 行）——三验之二：环境契约断言

对 compose.yaml/compose.runner.yaml 各做三态断言：`CODEX_SECURITY_EMBEDDINGS_URL` 设值/未设/空串时 `docker compose config` 渲染结果分别等于该值/null/空串（env 透传契约不变形）；`mkdir results state && chmod 700`；空 CSV 必须拒扫（exit 2 + "Multiscan CSV must contain at least one repository." 消息逐字断言）。

### 2.6 docker/verify-container-release-version.sh（68 行）——三验之三：发布防覆盖

对 GHCR 版本列表跑 jq 状态机：稳定 semver 比较判断 backfill（旧版本补发）/latest（正常发布）/published（已存在→拒绝：重试必须 digest 匹配 + latest 一致，否则 ::error 退出）——**不可变发布纪律**：稳定版本标签永不被覆盖。

### 2.7 Dockerfile + compose 三件

- **Dockerfile**（69 行）：两阶段，基础镜像全部 digest pin（node:26-bookworm-slim@sha256:…）；package 阶段 pnpm frozen-lockfile 构建+pack+check-package；scanner 阶段装 git/openssh-client/python3，npm i -g tarball 后跑 `--version`/`bulk-scan --help` 冒烟；**uid 10001 非 root + 无 home**；/input /output /state 三目录，ENV 把 CODEX_HOME/HOME 都指到 /state、`GIT_TERMINAL_PROMPT=0`。
- **compose.yaml**：`cap_drop:ALL + no-new-privileges + seccomp`（compose.apparmor.yaml 单覆盖文件追加 apparmor 选项——同 service 名叠加的设计让 AppArmor 成为可选层）；CSV bind **read_only:true** + create_host_path:false；user 由 `$CODEX_SECURITY_USER` 显式给；环境变量白名单透传（CODEX_API_KEY/OPENAI_API_KEY/GH_TOKEN/embeddings URL/GIT_HOST——不给 AWS 系变量）。
- **compose.runner.yaml**：工作流运行器（按 digest pin 镜像跑任意 CLI 阶段），README 明示"不调度、不重试、不跳阶段——命令/输出/退出码直通"。
- **docker/README.md**（195 行）：GHCR 发布全流程（BuildKit SBOM + max-mode provenance + gh attestation + 多架构 manifest + digest 校验命令）、runner 生命周期（results/state 双挂载必须跨容器保留；"移动主机扫描文件不会重写保存态里的绝对路径——要么在 runner 里跑要么保持原路径"）、嵌套 userns 受限主机装 AppArmor override、备份纪律。

### 2.8 第四层（源码内）：parent-sandbox.ts + permission-profile-preflight.ts

容器之下还有 **worker 级权限档案**：parent-sandbox.ts（256 行）从宿主 `_meta["codex/sandbox-state-meta"]` 双通道（direct 与 requestInfo 转发）读取父沙箱状态，**两通道冲突即拒绝**；只接受 managed 权限档案；把父 filesystem deny（绝对路径/glob，拒收相对路径与特殊路径上的 deny）翻译成 worker 的更严 root-read profile——**fail-closed 全程**：任何"无法验证的父权限"直接 DeepScanNonRetryableError（不可重试类）。executor.ts 的 `workerPermissionProfile()` 产出：`extends:":read-only"` + `:root read` + 继承 deny 映射（含 `__proto__` 原型污染字面量防御）+ `network:{enabled:false}`。permission-profile-preflight.ts（770 行）再用真实 codex 二进制跑预检确认 profile 生效。**对探隐的直接启示：探隐战士执行档（T2/T3）的 guard/egress 可以照抄"配置→预检→才放行"三步，而不是配置即信任。**

---

## 三、机制细节：去重/威胁模型/策略起草/存档/CI/Bedrock/模型用法

### 3.1 去重双层架构

**层 1：Deep scan 内 reducer（templates/deep-scan/dedup.md，56 行提示词）**。单串行语义归并者，明令"不看仓库代码、不派子代理、不验证发现、不编辑仓库、不能再开深扫"。合并判据 = **remediation-subsumption（修复子sume）**："修掉保留的发现必须同时修掉每个被吸收的发现"，否则不合并；**禁止**因共享子系统/CWE/路由/文件族/sink 族/攻击语言而合并——"任何 source/control/sink/impact 元组或独立可达实例在共同修复后仍存活就保持分离"。**对账协议**：host 供 `provenance.sourceFindingIds`，reducer 必须逐一交代（保留的抄 refs、合并的取并集），"host 保留原始 payload 并拒绝未对账输入"。**分页 IPC 协议**：`get_codex_security_deep_reducer_inputs({maxBytes, cursor})` 按字节预算分页（含 JSON 转义），超帧则预算减半重试该页，cursor+fragment 存 `store` 断点续读——这是"给 LLM 读超大 JSON"的工程解。

**层 2：跨扫描 dedupe（sdk/src/deduplication/，14 文件）**。嵌入检索 + 两段 LLM 评审：`text-embedding-3-large` 1536 维（tiktoken cl100k 截断 8192 token/发现；批 64；300k token/请求；2048 输入/请求；endpoint 可配 `CODEX_SECURITY_EMBEDDINGS_URL`，向量空间用 workflowDigest 做缓存键）→ **邻域 screening**（一次会话审 anchor+全部邻居，只给 SAME/DISTINCT **推荐**，"筛查推荐不是证明"）→ **独立大模型 pair 终审**（从完整原件独立判定，可查仓库源码；SAME 必须给 canonicalFindingId + 合成 mergedFinding——把每个原件的全部材料信息并回并逐件对照补漏；blocker 走 submit_error 而非硬判）→ 输出强制走 `review_validator.submit_decisions` 函数工具（"禁止把 JSON 写在散文/markdown/代码栅栏里，必须直呼函数"）。

### 3.2 威胁模型（references/threat-model.md，64 行）

方法五步：① 建架构（从根识别产品/用户/接口/执行模式，跟代表输入过真实入口-组件-控制-敏感操作）② 每边界定 attacker/受授数据/受保护资产/必须保持的不变量 ③ **区分对每个 caller 可用的操作与 host-only 权限**（"广告的工具可见性 ≠ 强制的 caller 授权"；"不要给已共享同一权限的 actor 之间发明隔离"）④ **从敏感消费者倒推每条实质不同的启动/部署路径**（实际文件/网络/进程操作过 helper 返回值/路径拼接/配置优先级/挂载映射；"不要从变量名、目录意图或挂载标签推断消费者位置"；"分离的配置段或挂载声明不构成隔离"）⑤ 全部架构事实带 repository-relative path:line 引用，**返回前对清单批量回验每条引用**。独立架构评审子代理（不带威胁假设）+ effectiveResources 验证表（consumer/deployment/configurationChain/effectiveValue/recipients/enforcingControl/evidence/discrepancy）。standalone 文档四节模板（Overview+Mermaid / 威胁模型与假设 / 攻击面表（Priority/Scenario/Prerequisites/Impact/Controls/Mitigation/Evidence） / 严重度校准（各级具体例子+反例））。产物随扫描存档，`cs export --scan ID --artifact threat-model` 导出。

### 3.3 SECURITY.md 策略起草（security-policy.ts 1132 行 + define-security-policy 技能）

`cs policy .`：草稿**存仓库外**，产出 diff+notes 供人工审后手动拷贝到 Policy target（"命令永不改你仓库里的文件"）；扫描时 root+component SECURITY.md 自动继承，**嵌套最近优先**；policy 同时影响 reportability（fixture/QA 边界场景按组件自身政策评估，不拿产品披露标准套夹具）与严重度校准。`.github/SECURITY.md`/`docs/SECURITY.md` 常是报告指引，起草时保留其漏洞报告指令。

### 3.4 扫描存档与历史（canonical 三件套 + SQLite）

- **canonical 三件套**：scan-manifest.json（执行状态/省略 worker）/findings.json/coverage.json 为唯一语义输入，`report.md` 是**确定性投影**（"生产者不得手写 report.md；finalize 在校验 canonical 印记后确定性投影"——报告可随时重生成而不动 canonical）。
- **coverage 语义**：surfaces 判定表（≥1 reportable→reported；否则 deferred→needs_follow_up；否则 suppressed→rejected；否则查过无候选→no_issue_found；否则 not_applicable）；explicitExclusions（pattern+reason）；deferred（稳定 id+reason）；openQuestions（可复制的跟进 prompt）。**模式与清单策略分离**：mode（repository/scoped_path/diff/commit/branch_diff/working_tree/deep_repository）×inventoryStrategy（repository/scoped_path/diff/directory/custom）。
- **历史浏览**：`cs scans show/resume/list` + scan-history-renderer（505 行终端渲染）；workbench SQLite（workbench/database.ts+migrations+transaction）；resume 重读保存的 model/provider/effort/输出目录。本地面板已删（"existing databases and scan artifacts remain available"）——**官方从 GUI 退回 CLI 的决策本身值得注意**。

### 3.5 CI 集成（github-action/）

action.yml 20 输入：scope（repository/diff）、mode（standard/deep）、model 默认 gpt-5.6-sol、effort 默认 **xhigh**、cyber-access-program（standard/daybreak_blue/daybreak_red）、max-cost/max-time-hours/fail-on-severity/dry-run/annotations（≤50 条源标注）/upload-artifacts（allowlist+retention 1-90 天）。输出 scan-status/policy-status/report-status/exit-code/scanned-sha/sarif-upload-ready。**sarif.ts 是"发布前安全断言"范例**：递归遍历 SARIF 拒绝 externalPropertyFileReferences/originalUriBaseIds/uriBaseId/index/绝对路径/盘符/协议 scheme/`..` 穿越——"保持源引用可安全发布"。README 官方 workflow 含 Ubuntu 沙箱预装步骤（bubblewrap+apparmor-profiles+`apparmor_parser -r bwrap-userns-restrict`）——**CI runner 也要给沙箱铺路**。

### 3.6 Bedrock 与多 Provider（docs/bedrock.md）

原生 `amazon-bedrock` provider（无连接器/适配器）：AWS 凭据链（profile/临时凭据/web identity/container）；Bedrock 专用模型 ID（Daybreak Blue=`openai.gpt-daybreak-blue-5.6-sol`、Red=`openai.gpt-5.6-cyber`，us-east-2 Mantle Responses API）；**Bedrock 默认 model_reasoning_summary=none 并传播到 deep worker**（部分模型拒 reasoning.summary）；成本模型按 AWS 模型卡计价（含 AWS 费用，Blue 报短/长上下文区间，Red 只有短上下窗 272K 上限）。另有 OpenRouter/Fireworks。Daybreak = Trusted Access for Cyber（部分网络安全请求与 protected findings 需审批）。

### 3.7 Prompt 与模型用法盘点（源码可见处）

- **提示词全部明文可读**：16 个 SKILL.md（工作流编排）+ 14 个 references（方法论）+ deep-scan 双模板（discovery.md 11 行极简——"照 core-scan.md 跑一次标准扫描"+一份类型化 JSON 上下文；dedup.md 56 行 reducer 协议）+ 内嵌子代理 prompt（基线审计者/聚焦调查者/架构评审者/补丁评审者四份全文在 core-scan.md/threat-model.md/fix-finding 内）+ deduplication-prompts.ts（screening/pairReview/sourceReview 三段）+ evals 的 triage-request.txt。
- **模型用法**：单一推理模型贯穿（默认 gpt-5.6-sol，effort 可至 xhigh/max），但**按角色分 prompt 不分模型**；dedup 是唯一显式大小分工（screening 用会话内模型、终审"independent larger model"）；subagent 配额透传（`--subagents`，worker 内还可再派）；`userContext` 一律 untrusted（"永不 open/fetch/follow 其 URL"——仅父线程可做一次性显式授权读取）；threadSource="security_scan" 标记来源。
- **Eval 基建**：promptfoo 三角校准（calibration-oss.yaml 六套 + triage-result-v0.schema.json + 断言脚本六件）、SASTBench 集成（hydrate 仓库/指标/verdict 断言）、secret-discovery 独立 harness、deep-reducer 分页回归、invoice-desk 自建漏洞应用 + expected-findings.json QA 门 + GitHub workflow 消费——**对探隐的启示：给审计引擎建"预期发现清单"夹具门**。

---

## 四、成熟度评分 + 与 GenSift 对比

### 4.1 成熟度评分（满分 5）

| 维度 | 分 | 依据 |
|---|---|---|
| 工程化/发布纪律 | **5.0** | 20 条 GitHub workflows、SBOM+max-mode provenance+attestation、digest pin 全链（基础镜像/actions/插件）、不可变版本纪律、三验脚本、RELEASING.md 20k 字 |
| 测试覆盖 | **4.5** | SDK tests 196 文件 + mcp-app tests 56 文件 + goldens；崩溃恢复/终端竞态/分页/权限预检均有专测 |
| 安全执行（沙箱） | **5.0** | 六层纵深 + fail-closed 预检 + 运行时自检；见第二节 |
| 审计方法论 | **4.5** | core-scan 八步+七道防 FP 闸+动态验证阶梯+反证义务，是所见最完整的 LLM 审计纪律成文 |
| 可移植性/开放性 | **2.5** | 深绑 @openai/codex-sdk 与 codex exec 二进制（worker=完整 Codex 线程）；Daybreak 访问程序/Cloud 闭环；Bedrock 仍走 OpenAI 模型 ID |
| 产物互操作 | **4.5** | canonical JSON+SARIF/CSV 导出、schema 版本化、SARIF 发布前安全断言 |
| 运维成本 | **2.0** | 默认 effort xhigh + deep 96h + 多 worker 重扫=重成本；成本上限只有估计性 `--max-cost` |
| **综合** | **4.0** | 工程成熟度远超社区同类；代价是生态绑定与成本 |

### 4.2 与 GenSift 对比（同为 LLM 源码审计）

| 维度 | codex-security（OpenAI） | GenSift（用户资产，~/.claude/skills/gensift） | 裁断 |
|---|---|---|---|
| **哲学** | 宿主工程化：TS 状态机调度完整 Codex 线程，确定性=编排器+schema+权限预检 | 账本外骨骼：零自研代码，确定性=TSV 账本+内联 shell+宿主子代理；"程序执法"以盘上文件形态存在 | 同一信念（确定性上收、语义下沉）的两种实现；探隐两种都能接 |
| **覆盖纪律** | 概率性收敛：noNewStreak≥stopAfterNoNew 即 saturated；coverage surfaces 如实记排除/deferred/openQuestions，"不声称穷举覆盖" | **不可谈判**：所有 sink 必须出卡、不可跳过不可抽样；L1 全闭合后还跑 L2 发散+joins；G2 闭卷对账 | GenSift 覆盖律更硬——这正是 tanyin-product-v1 修正案 A 点名继承 GenSift 的原因；codex 的 coverage schema 可为探隐覆盖账本提供**产物格式**参考 |
| **发现机制** | 基线+威胁模型引导调查包+四视角调查者（每 worker 内），深扫层再 N 次独立重扫做方差缩减 | pattern 枚举（59 ERE+fixtures 回归）→逐卡五步证伪→盲验证；类判据页 26 类 | codex 无确定性枚举层（车道 A 缺位）——探隐车道 A 已另规划，正好互补 |
| **验证机制** | 单次独立重验+反证义务+动态阶梯（crash/ASan/gdb/接口复现）+人工反馈回喂；secret 有专用 disclosure-path 判据 | 五步证伪卡+盲验证（Confirmer 不看 Analyzer 结论）+T0-T3 执行档 | 两者都强制"最强反证"；codex 的**动态验证阶梯**与**验证回执 survives 三态**是 GenSift 没有成文的 |
| **去重** | 双层：worker 间 reducer（remediation-subsumption+provenance 对账）+跨扫描 embedding 邻域+两段 LLM 评审 | 2d 语义合并轮（open≥25 触发）+ machine-fields 指纹 | codex 去重远更体系化；探隐证据卡去重可直接抄判据话术 |
| **产物** | canonical 三件套+确定性投影 report+威胁模型+SARIF/CSV/Linear | TSV 账本+F-*.md+live index+coverage.md+CALIBRATION 草案 | codex 产物是**行业互操作格式**；GenSift 产物是**操作员实时看盘格式**——探隐两者都要（后者近 UI，前者近导出） |
| **中断恢复** | 心跳+租约+coordinatorGeneration+崩溃重建+handoff token | 状态在盘+同源断点续跑+Stop hook 防自停+reaper 收尸 | 同级；codex 的**租约/代际**概念可补探隐多进程场景 |
| **部署形态** | npm CLI+SDK+Action+容器 | 复制目录即装（Claude/opencode 双宿主，三平台） | GenSift 分发零依赖完胜 |
| **成本** | 重（xhigh 默认+96h 深扫+嵌入 API） | 轻（宿主会话内） | — |

**一句话**：codex-security 是"OpenAI 把 LLM 审计做成 SAST 产品的工程上限"，GenSift 是"把 LLM 审计做成协议状态机的纪律上限"。前者赢在工程与产物，后者赢在覆盖铁律与零依赖——探隐要的恰是后者的纪律+前者的格式与验证语义。

---

## 五、对探隐的复用判决（"有好的就用"原则）

### 5.1 判决①：白盒车道 B——**只偷设计，不直接外接**（置信度 82%）

**不外接的理由**：
1. **深绑闭环**：worker 是 `@openai/codex-sdk` 起的完整 codex exec 线程（executor.ts:184-196），不是可替换的 API 调用；权限 profile/紧凑 MCP/skills 加载全部走 Codex 宿主协议。外接=连 Codex 运行时一起买，探隐的 llmpool/judge_client 双车道直连 API 架构（tanyin-product-v1 生态位）会被旁路。
2. **运行契约冲突**：deep 默认 96 小时+97 小时工具超时（.mcp.json tool_timeout_sec=349200），与探隐运行契约四原则（提交即返回/领取不等待/超时显式化/账本两相性）错位；Standard 单扫虽可短，但 effort 默认 xhigh 的成本不可控。
3. **车道 B 已有更合身的吸收对象**：GenSift 是用户自有资产、覆盖不可谈判律同源、账本/replay/断点续跑与探隐证据卡直接同构——修正案 A 已定"吸收 GenSift"。codex-security 在白盒深度审计位上没有 GenSift 给不了的独特能力（其独特物在沙箱与产物格式，皆可抄设计）。
4. **许可无障碍但供应链有**：Apache-2.0 可用；但产物/遥测进 OpenAI Cloud 生态，Daybreak protected findings 需 Trusted Access 审批——对渗透平台的自主性是外部依赖。

**保留外接的可能形态**（不判死的活口）：`cs scan . --json --headless` 或 SDK 的 `CodexSecurity().run()` 是干净的单进程入口，若某次任务需要"OpenAI 级第二意见"（如对 GenSift 结论做交叉验证的陪审员），可按 **nuclei adapter 先例**外接为一次性工具调用，取其 SARIF/JSON 回填证据卡。

**翻案条件**（任一成立即重审）：
- 探隐拿到 Daybreak Blue/Red 访问且用户接受按 token 计费的成本模型，且实测 codex-security 在目标语言上的发现率显著高于 GenSift（用同一 expected-findings 夹具集对跑）；
- OpenAI 把 worker 执行层开放为纯 API（无 Codex 宿主依赖）；
- 出现"GenSift 不覆盖的语言/框架"且 codex-security 实测覆盖（如 Swift/Rust/COBOL 类）。

### 5.2 判决②：沙箱三层件——**直接偷，逐件抄**（置信度 93%）

对探隐 guard/egress 的可偷清单（按价值排序）：
1. **seccomp 的 socket 参数过滤技巧**：封 AF_ALG+AF_VSOCK、放其余——探隐战士执行档（现在 T1 只读，未来 T2/T3 执行档）的网络面控制直接可用这份 allowlist 作起点（464 行现成）。
2. **"seccomp 允许 mount/clone + cap-drop ALL + AppArmor 圈 userns"的三层组合**：探隐若在 Linux 跑执行档，Bubblewrap 化的战士沙箱可照此配方；尤其 `verify-container-sandbox.sh` 的**"在目标环境里真跑一次沙箱自检"**模式——探隐 guard 应从"配置了"升级为"预检跑通才放行"（对齐 parent-sandbox.ts 的 fail-closed）。
3. **AppArmor profile 的信号收窄与 /proc//sys deny 表**：42 行可直接改名单复用。
4. **entrypoint 卫生**：参数白名单状态机、GIT_CONFIG_COUNT 注入防御、主机名校验后才进 config key、exec 接管 PID 1——探隐 worker 进程封装（future 战士进程管理）照抄。
5. **compose 纪律**：cap_drop+nnp+seccomp 三连+read_only bind+create_host_path:false+显式 uid+环境变量白名单透传（不给多余凭据）——探隐若做容器化战斗舱（B 车道批量目标扫描）这就是模板。
6. **发布三验**：环境契约断言（config 渲染三态比对）/运行时沙箱自检/版本防覆盖——探隐的部署校验与升级纪律可平移。

### 5.3 判决③：find→validate 两段制对证据卡 replay 的启示（置信度 88%）

四条直接可落地的设计：
1. **候选三态落盘**：`coverage.deferred[]（未验证候选+原始证据+candidateId）→ findings（验证过）→ rejected surface（被拒+反证）`——探隐证据卡应采用同构三态（pending/confirmed/refuted+counter-evidence），**refuted 卡不删**，反证留档供 replay 复核。candidateId 贯穿发现-验证-修复全链的稳定 ID 设计正是 replay 追溯需要的。
2. **人工反馈回喂判据**：false_positive_feedback 的"仅当记录理由在当前源码与控制下仍成立才压制"——探隐处置库（GenSift dispositions.tsv 同源）回喂时必须带这条时效判定，否则旧否决会漏新漏洞。validation receipt 的 `survives: yes/no/uncertain` 三态就是 replay 的判定语义。
3. **reducer 的 remediation-subsumption 合并判据 + provenance 对账**：探隐证据卡去重（跨扫描/跨战士）直接抄："修 A 必须也修掉 B 才可并；共享 CWE/路由/文件族不构成合并理由"；合并时 sourceFindingIds 取并集、主机拒绝未对账输入——防"合并即丢证据"。
4. **饱和收敛 noNewStreak**：探隐深扫/重复验证循环的停止判据可用"连续 N 轮无新确认发现且缓冲空→saturated"，替代纯超时——与超时显式化原则兼容（saturated/capped/deadline 三种终态分别记账）。

另附两条次级启示：**确定性投影报告**（report.md 由 canonical JSON 投影生成、模型永不手写报告——探隐报告页应同构）；**expected-findings 夹具门**（invoice-desk 模式：给审计引擎建带预期清单的漏洞应用，放行门=全找齐——GenSift fixtures 已有雏形，可升格为引擎级回归门）。

### 5.4 总判决

> **codex-security 对探隐是一份"工程参考件"而非"集成件"**：沙箱三层件逐件抄（5.2）、验证/去重/覆盖语义逐条偷进证据卡 replay（5.3）、车道 B 维持 GenSift 吸收路线（5.1）。若未来实测其发现率碾压再翻案外接。

---

*报告完。分析过程 /tmp/codex-security 全程只读零 git；本文件为唯一写入产物。*

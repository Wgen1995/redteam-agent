---
name: scope-and-context
description: 阶段0 客观枚举——检测引擎主序列第一步。产出三份冻结清单（file_inventory.tsv / sink_inventory.tsv / source_inventory.tsv）作为找全的客观分母，基于 file_inventory 客观分布做技术栈探测，并展示威胁语境关键假设后以 conservative_assumption_applied 非阻塞继续。只做确定性枚举与客观分布统计，不做候选发现、不做漏洞判断、不排除任何文件。不适用场景：候选发现与判定（属于 candidate-discovery）；验证与定级（属于 verification-and-rating）。
---

# 阶段0：客观枚举（三清单冻结 + 技术栈 + 非阻塞威胁语境）

> 依据（框架/历史依据，v0.11.1 U-A1 标注）：设计 28 号 §3.1（环1 客观清单）、§7.1（全自动）；机制权威=doc-36/63。本阶段产出检测引擎的**冻结分母**——后续所有检查点、对账等式、覆盖披露都从这三份清单派生。本阶段只做确定性枚举与客观分布统计，不做任何候选判断或漏洞结论。

## 目标

1. 产出三份**冻结清单**（生成后不再修改，恢复时校验存在与行数），为阶段1 的检查点派生与 Gate-1 对账提供唯一客观分母。
2. 基于 file_inventory 的客观分布做技术栈探测（不凭印象、不凭依赖清单口头声称）。
3. 展示威胁语境关键假设后，以保守假设继续（非阻塞），不设"是否继续"提问。

## 硬性约束（不可违反）

1. **目标只读**：本阶段对目标代码库只做只读扫描；任何写目标树的动作需要单独授权（见 [`../../shared/deployment-environment.md`](../../shared/deployment-environment.md) 动态执行安全门）。
2. **不按路径名排除文件**：除 `.git` 外不排除任何路径（含隐藏文件/生成文件/二进制）。文件名/路径（如 `test/`、`demo/`、`safeExecute()`）不能作为排除依据；只按"是否含真实可执行行为"这一客观事实判断，且该判断属于阶段1 预筛（见 [`../../shared/prefilter-rules.md`](../../shared/prefilter-rules.md)），不在本阶段执行。
3. **二进制标注不丢弃**：读不了的二进制/生成文件也要列出并标注（`binary_flag`），不得静默丢弃。
4. **对账常数一律动态推导**：文件数、sink 数、source 数、入口通道数、sink 类数一律用 `wc -l` / `grep -c` 在运行时导出，禁止在协议或产物里硬编码"59/13"这类数字（吸收 SourceCPT 59/70/57 漂移教训）。
5. **冻结纪律**：三份清单生成后不再修改；后续发现新文件/新 sink/新 source 不回头改清单，而是按 [`../../shared/work-graph.md`](../../shared/work-graph.md) 追加检查点并重新闭合。
6. **0 命中头标**：任何 sink 类或入口通道 0 命中，必须写 `ZERO_HITS_WARRANT_REVIEW` 头标（可能 grep 模式漏覆盖），不得默认为"该类别不存在风险"或等同"未扫描"。

## 执行步骤

### 1. 产出三份冻结清单

确定性命令原样声明以 [`../../contracts/host-reconciliation-commands.md`](../../contracts/host-reconciliation-commands.md) 为准，由宿主 shell 执行，GenSource 不实现任何代码。

**v0.3.9 平台前置（先于一切枚举）**：
1. 在能力档案声明对账执行环境（POSIX shell 或 PowerShell 5.1+），并执行黄金夹具自检（contracts/gate-selftest/fixture/ + contracts/gate-selftest/expected-gate.txt），输出全等才可继续；不满足 → 阶段0 blocked。
2. 机器产物七规约：UTF-8 无 BOM、LF 换行（解析容忍 CRLF）、相对路径正斜杠、UTF-8 字节序排序、UTC ISO 8601、hash 输入规范化、会话内引用一律相对 session_dir（盘符/绝对路径禁入机器产物）。
3. 排序与 hash 的规范化以 python3 单行为权威（§1/§6 命令），POSIX 的 LC_ALL=C 与 PowerShell 的 .NET 字节序为等价实现，等价性由黄金夹具钉死。
4. 信号级 sink 类（SENSITIVE-EXPOSE/LOGGING-INSUFF/AUTHN-BYPASS/BRUTE-FORCE/OBSERVABLE-DIFF/STATE-CONCURRENT/MEM-INDEX）命中只作线索，**不入 sink_inventory**（Gate-1 gate[信号级禁入] 校验）。

#### 1.0a gate_progress.tsv（v0.5.3：子任务 gate 进度记录）

- 每个子任务 gate 闸门通过后，追加一行：`子任务ID\tgate等式\tpass\t时间戳`
- 任一 FAIL 不记录 pass，记录 `fail\t失败等式\t原因`
- gate_progress.tsv 是 PhasedLine 闭环的可追溯证据

#### 1.0 确定性引擎强制（v0.5.1 铁律）

- 阶段0 枚举**必须执行** `python3 contracts/enumerate.py --source {project_path} --knowledge {skill_dir}/knowledge --output {session_dir}`
- **禁止代理自行枚举**——不得自写 grep/python 脚本替代 enumerate.py；三清单必须来自 enumerate.py 的输出
- gate gate[枚举锚定(类集合)] 检查 sink_inventory 的类集合 ⊇ 知识表全集（自跑枚举会缺类=FAIL）
- **禁止自造 sink 类名**——sink_type 必须来自知识表（gate gate[候选类型一致性] 候选类型一致性检查）

#### 1.1 file_inventory.tsv（文件全量）

- 文件枚举 = **单一 find 命令**，输出按 `LC_ALL=C sort` 排序后写入（跨机器可复现），除 `.git` 外不排除任何路径：

```bash
cd {project_path} && find . -type f -not -path "./.git/*" | sed "s|^./||" | LC_ALL=C sort > {session_dir}/file_inventory.tsv
total=$(wc -l < {session_dir}/file_inventory.tsv)   # 文件总数，动态推导，禁止硬编码
```

- 在 find 冻结路径清单基础上，逐文件用确定性 shell 命令补充客观列，得到最终六列：`path | type | lang | loc | binary_flag | sort_order`：
  - `binary_flag`：用 `file` 命令判定文本/二进制；二进制文件标注 `binary`，不丢弃。
  - `loc`：文本文件用 `wc -l` 取行数；二进制文件记为 `-`。
  - `lang`：按文件后缀（客观）归属语言；无明确后缀或识别不清时写 `unknown`，不得猜测。
  - `type`：按后缀与 `file` 输出客观归类（源码/配置/文档/数据/生成物等），不引入语义判断。
  - `sort_order`：即 `LC_ALL=C sort` 后的行号，作为后续确定性 ID（sink_seq/source_seq）的稳定序。
- 冻结后不再修改；恢复时校验文件存在且 `wc -l` 行数一致。

#### 1.2 sink_inventory.tsv（全部危险操作实例）

- 按 `knowledge/sinks/_index.md` 的**双轨索引**（Sink / State Transition / Resource Consumption 三个子类，每类的 `recognition_signals` 即跨语言 grep 模式）**逐类全扫**，最终五列：`sink_id | file:line | sink_type | symbol | sort_order`。
- 每类执行：

```bash
cd {project_path} && grep -rnE "{该类 recognition_signals 模式}" --include="*" . | LC_ALL=C sort > {session_dir}/logs/sinks_{type}.log
# 0 命中时写头标：echo "ZERO_HITS_WARRANT_REVIEW" > sinks_{type}.log
```

- 用双兼容 grep 子集（bash `grep -E` 与 PowerShell 通用；不用词边界/非词字符类转义）。模式按检测到的语言过滤（见步骤2），对检测到的语言全扫。
- 0 命中的类也保留记录并写 `ZERO_HITS_WARRANT_REVIEW` 头标（可能模式漏覆盖）。

#### 1.3 source_inventory.tsv（全部入口实例）

- 按 **13 入口通道**（rest/rpc/mq/ws/graphql/cron/cli/script/deser/file/webservice/custom_proto/event）**逐通道全扫**，最终六列：`source_id | file:line | entry_type | symbol | param | sort_order`。
- 通道清单以列表形式声明（不是硬编码"13"这个数）；通道数运行时用 `wc -l` 动态推导。逐通道执行与 sink 相同的 grep 全扫，0 命中写 `ZERO_HITS_WARRANT_REVIEW` 头标。

#### 1.4 清单冻结与对账常数

- 三份清单写入后即冻结。所有下游常数（文件数 / sink 数 / source 数 / 通道数 / sink 类数）在用到处用 `wc -l` 动态推导，禁止写死。
- 三处一致性校验（sink 清单数 == 规则文件数 == 全扫门数）若当前知识层已具备，则在阶段0 启动即对账，不一致 `blocked`；知识层未补全时如实标注缺口（见 design §9.3）。

#### 1.5 闭卷验收隔离（v0.11.0 F-E2E-08 修正）

- **CVE 锚点在包外**：`tests/golden/`（闭卷，宿主持有），运行期**禁止**读 cve-index、**禁止**派生 fix-presence 检查点（gate「fix_presence 禁止派生」机械判 FAIL）、**禁止**在本轮任何产物写 CVE 编号——污染判定依据 acceptance.py。
- 本轮产物不涉及 CVE 对账；CVE 召回与污染判定全部由包外闭卷验收（阶段4，宿主执行）承担。machine-coverage.tsv 已废弃（v0.11.0）。

### 1.6 库 vs 应用 source 模型判断

**问题**：13 入口通道（rest/rpc/mq/ws/...）假设目标是一个**拥有自己网络入口的应用**（自己监听端口/自己起服务）。但目标若是一个**库/SDK**（供其他代码 import 调用，自身不含网络监听），13 通道可能 0 命中或命中很少——此时真正的攻击者可控输入不是"网络请求"，而是**调用方传给本库公开 API 的参数**。不判断这一点，会把库类项目的攻击面误判成"几乎没有 source"，导致本该分析的公开方法参数流入 sink 却因为 source_inventory 为空而从未进入检查点。

**判据（基于 file_inventory 客观信号，不凭包名猜测）**：
- 应用信号：存在网络监听调用（`app.listen`/`http.createServer`/`HttpServer.create`/`ServerSocket`/框架启动类的 `main` 绑定端口）或部署产物（`Dockerfile` 暴露端口/`docker-compose.yml`/K8s manifest）——命中任一即判**应用型**。
- 库信号：`package.json` 无 `"main"` 对应可执行入口且有 `"exports"`/发布到包registry的标记（`"private": false` 且无 `start` 脚本绑端口）、或 `setup.py`/`pyproject.toml` 的 `packages=` 声明而无 WSGI/ASGI 入口、或 Java 侧只有 `pom.xml`/`build.gradle` 打包为 `jar` 无 `Main-Class` 启动服务逻辑——命中且应用信号缺失即判**库型**。
- 两类信号都命中（如既是库又内置示例服务）：**两种 source 模型都保留**，不得二选一丢弃。
- 两类信号都不命中：按应用型处理（保守假设，13 通道仍全扫），并在假设清单标注"库/应用信号均未命中，按应用型保守处理"。

**库型时的 source 补充**：source_inventory 之外，**额外**用 grep 定位该语言的公开/导出符号作为 source 候选，记入 `source_inventory.tsv` 时 `entry_type` 填 `PUBLIC-API`（不新造入口通道类别，复用现有六列 schema）：
- Java：`public` 且非 `private`/`protected` 的类方法签名（排除 getter/setter 样板）
- Python：模块级不以 `_` 开头的函数、`__all__` 列出的符号
- JS/TS：`module.exports`/`export function`/`export default` 的符号
- Go：首字母大写（导出）的函数
每条 PUBLIC-API source 的 `param` 列必须写清楚该方法的参数列表（供后续候选发现阶段判断哪个参数可能来自不可信调用方）。

**假设记录**：本判断结果（应用型/库型/两者皆是）连同判据命中项写入 3.节威胁语境的"保守假设清单"，因为它直接决定了 source 模型的完整性——**遗漏这条假设披露 = 攻击者画像本身有缺口**。

### 2. 技术栈探测（基于 file_inventory 客观分布）

- 不再靠"读依赖清单 + 口头声称"，而是以 file_inventory 的客观列做分布统计：

```bash
awk -F"\t" "{print $3}" {session_dir}/file_inventory.tsv | sort | uniq -c | sort -rn   # 按 lang 计数，客观分布
```

- 据此形成"检测到的语言/框架清单"：语言按 file_inventory 后缀分布客观得出；框架按框架标记文件（如 `pom.xml` / `package.json` / `requirements.txt`）的客观存在性判定，且仅作为线索，不与代码事实冲突。
- 探测结果写入 stage 产物的技术栈字段；探测到的语言用于步骤1 的 sink/source 模式过滤与后续阶段的知识条目过滤。冷门语言如实披露"该语言知识覆盖浅、完整性置信度较低"，不装作深度一致。

### 3. 威胁语境（展示关键假设 + 非阻塞继续）

- 生成威胁语境文档，展示**关键业务假设**：要害资产、信任边界、攻击者画像、暴露面。
- 展示后**不等待用户确认**，直接以保守假设继续，写 `confirmation_policy=conservative_continue` 且 `user_confirmed=conservative_assumption_applied`（两字段取值关系：`confirmation_policy=conservative_continue` 时 `user_confirmed=conservative_assumption_applied`，两值均已登记于 [`../../contracts/enum-registry.md`](../../contracts/enum-registry.md)），并记录"未等用户确认即采用的保守假设清单"及其影响范围，写入报告缺口披露。
- 该纪律与 [`../../shared/human-in-the-loop.md`](../../shared/human-in-the-loop.md) 第3节一致；本阶段**禁止**把威胁语境展示变成"是否继续"的阻塞提问（红线禁令）。

### 3.1 Summarizer 与 Confirmer（0.6）

- 威胁语境完成后派 Summarizer（[`../../agents/class-pruner-prompt.md`](../../agents/class-pruner-prompt.md)）：只写类级候选事实到 `{session_dir}/facts.tsv`（uncontrolled / kills / intended），`confirmed` 一律 false。禁止 S2 整类 not_dangerous。
- 对每条 uncontrolled / kills / intended 派 Confirmer（[`../../agents/fact-confirm-prompt.md`](../../agents/fact-confirm-prompt.md)）独立核 evidence 行。
- 有 `SECURITY.md` 则 Read，当数据（intended 的产品用途声明）。
- Orchestrator 不得用 `python3 -c` 代替 Rewrite 规则理解（Analyzer 按同一规则改写工作集；若宿主可跑脚本则 `python3 -c "from sdwr.rewrite import apply_rewrite"` 仅作可选加速）。

### 4. 攻击面地图派生（#2 子任务）

- 由三份冻结清单与威胁语境派生攻击面地图 `attack-surface-map.md`：以 Surface/RiskArea 命名类别组织扫描结果（`named_category_scan_results` / `file_level_inventory`），每个命名类别给命中计数；0 命中类别必须写 `zero_hit_review_flags` 强制零命中复核，不得静默省略该类别。
- 结构契约见 [`../../contracts/data-structures/attack-surface-map.md`](../../contracts/data-structures/attack-surface-map.md)，字段写权限见 [`../../contracts/field-ownership-table.md`](../../contracts/field-ownership-table.md) #2 段。

## 输出

本阶段产出三份冻结清单 + 技术栈探测结果 + 威胁语境文档，全部携带共享状态字段 `stage_result` / `version` / `resume_context`（见 [`../../shared/state-model.md`](../../shared/state-model.md)）：

| 产物 | 说明 |
|---|---|
| `file_inventory.tsv` | 冻结文件清单，六列 `path | type | lang | loc | binary_flag | sort_order` |
| `sink_inventory.tsv` | 冻结 sink 清单，五列 `sink_id | file:line | sink_type | symbol | sort_order` |
| `source_inventory.tsv` | 冻结 source 清单，六列 `source_id | file:line | entry_type | symbol | param | sort_order` |
| 技术栈探测结果 | 检测到的语言/框架清单（基于 file_inventory 客观分布）及冷门语言披露 |
| `threat-context.md` | 威胁语境（展示关键假设 + `confirmation_policy=conservative_continue` + `user_confirmed=conservative_assumption_applied` + 保守假设清单） |
| `attack-surface-map.md` | 攻击面地图：由三清单加威胁语境派生的 Surface/RiskArea 命名类别扫描结果（含零命中复核），结构见 [`../../contracts/data-structures/attack-surface-map.md`](../../contracts/data-structures/attack-surface-map.md) |

- 三份清单任一为 0 命中（sink 类/入口通道）时，对应记录写 `ZERO_HITS_WARRANT_REVIEW` 头标，不得省略该记录。
- 阶段完成标准：三份清单冻结存在且 `wc -l` 可对账、技术栈基于客观分布、威胁语境已保守继续且假设清单非空，写 `stage_result=completed` 后按 [`../../shared/work-graph.md`](../../shared/work-graph.md) 进入阶段1。
- 无 shell 对账能力时，对账降级为 LLM 自报并标注 `unverified_accounting`（见 [`../../shared/deployment-environment.md`](../../shared/deployment-environment.md)），不得伪装为 shell 对账。

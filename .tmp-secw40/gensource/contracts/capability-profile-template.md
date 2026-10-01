# 能力档案模板

本模板供宿主Agent在审计运行开始时（`SKILL.md`初始化阶段）执行一次能力探测，把结果记录为`capability-profile.md`供下游阶段引用。它是人读检查点，不是软件API；禁止为它编写GenSource自有状态机或validator。

> **闭卷隔离声明（v0.11.0）**：`tests/golden/` 为闭卷锚点（宿主持有），禁止复制进 agent 工作区、禁止进入 agent 读范围；CVE 编号禁止出现在任何 run 产物（污染判据，由 `tests/acceptance/acceptance.py` 检测）。

每项能力使用枚举注册表 [`capability_status`](enum-registry.md#capability_status) 的值，并附探测依据（实际执行的只读命令或观察事实，不是猜测）。模板不复制完整值集。

```yaml
run_id: audit-20260808-001
probed_at: 2026-08-08T12:00:00Z
probe_context: interactive-opencode | ci-non-interactive | other

capabilities:
  file_read:
    capability_status: available
    probe_basis: "pwd; ls source_path; head -1 <sample_file>"
  artifact_write:
    capability_status: available
    probe_basis: "test -w <output_dir> && echo writable"
  deterministic_commands:
    capability_status: available
    probe_basis: "git --version; rg --version"
  gate_execution_environment:
    capability_status: available
    probe_basis: "执行环境二选一声明：POSIX shell（bash+coreutils）或 PowerShell 5.1+（记录实际探测命令）"
  gate_fixture_selftest:
    capability_status: available
    probe_basis: "以 contracts/gate-selftest/fixture/ 为 session 目录执行 host-reconciliation-commands.md §4c 对账块，输出与 contracts/gate-selftest/expected-gate.txt 全等才写 available；不符写 unavailable 并 blocked（见 quality-gates 总则）"
  static_tools:
    capability_status: unknown
    probe_basis: "可选静态工具探测（spotbugs/semgrep --version 等）；available 时其事实输出可作观察来源（Mode 1，47 号），但候选推理必须为 LLM 语义判断而非工具原文（gate「候选推理非工具原文」）"
  python3_normalization:
    capability_status: available
    probe_basis: "python3 --version（排序/hash/json 规范化单行的权威依赖；缺失 → blocked，禁止降级手写对账）"
  independent_context:
    capability_status: degraded
    probe_basis: "宿主工具是否支持subagent派发（观察实际派发能力，不假设）"
  network:
    capability_status: unknown
    probe_basis: "未主动探测时写unknown；主动探测时记录方式（如curl --head <test_url>）"
  compiler_test_runtime:
    capability_status: unknown
    probe_basis: "目标语言编译器/解释器版本查询（如python --version、go version）；未查询时写unknown"
  sast_sca_debuggers:
    capability_status: unknown
    probe_basis: "工具版本查询（如semgrep --version、valgrind --version）；未查询时写unknown"
  resources:
    capability_status: available
    probe_basis: "df -h; ulimit -a; 宿主工具公布的token/时间限制（若有）"
    limits:
      time: null
      tokens: null
      memory: null
  dynamic_validation_authorization:
    capability_status: unavailable
    probe_basis: "用户是否已授予本次动态执行授权（见SKILL.md动态执行安全门）"
    authorization_ref: null
  degraded_capabilities:
    - capability: independent_context
      affected: "Gate-2独立复核"
      fallback: "同会话内弱化版独立性，显式标注independence_degraded"
    - capability: dynamic_validation_authorization
      affected: "验证方法梯队第①-⑤级"
      fallback: "仅使用inferred证据，静态代码理解级"
```

## 字段说明

| 字段 | 要求 |
|---|---|
| `run_id` | 与`run-state.md`的`run_id`一致 |
| （输出引用） | 本模板产出的`capability-profile.md`通过`run-state.md`的`capability_profile_ref`字段引用 |
| `probed_at` | 探测完成时间戳，ISO 8601格式 |
| `probe_context` | 探测时的宿主调用场景（交互式/CI非交互式/其他） |
| `capabilities.<name>.capability_status` | 引用枚举注册表 [`capability_status`](enum-registry.md#capability_status)；不得使用裸`status`字段 |
| `capabilities.<name>.probe_basis` | 非空；记录实际执行的只读命令或观察事实，不写猜测 |
| `capabilities.resources.limits` | 若宿主工具公布了token/时间/内存限制则记录，未知为`null` |
| `capabilities.dynamic_validation_authorization.authorization_ref` | 已授权时引用授权记录；未授权为`null` |
| `degraded_capabilities` | 列出`unavailable`或`unknown`且影响下游产出的能力项、受影响输出和降级替代方案；无降级时为空数组 |

## 能力项语义

| 能力项 | 语义 | 受影响输出 |
|---|---|---|
| `file_read` | 读取目标源码文件的能力 | 全部阶段的基础前提 |
| `artifact_write` | 在目标树外写入审计产物的能力 | 全部阶段产物写入 |
| `deterministic_commands` | 执行确定性只读命令（grep/rg/jq/git等）的能力 | 文件级枚举、横向差异检查、结构化查询 |
| `independent_context` | 派发不共享上下文的subagent的能力 | Gate-2独立复核、轻量第二意见 + 高风险对称反转复核、并行批处理 |
| `network` | 网络访问能力 | #18依赖漏洞查询等网络依赖功能 |
| `compiler_test_runtime` | 目标语言的编译器/解释器和测试框架 | 验证方法梯队第①-⑤级动态验证 |
| `sast_sca_debuggers` | SAST/SCA工具和调试器 | 外部工具集成、动态验证辅助 |
| `resources` | 资源限制（时间/Token/内存） | 规模成本管理的批处理策略调整 |
| `dynamic_validation_authorization` | 用户是否已授予本次动态执行授权 | 验证方法梯队动态层级、PoC已执行模式 |
| `degraded_capabilities` | 降级能力清单 | 标注哪些输出因能力缺失而降级 |

## 探测纪律

探测只允许**只读操作**，禁止把安装依赖、执行构建、启动服务当作能力探测。允许的探测命令示例：`pwd`、`ls`、`head`、`test -w`、工具版本查询（`<tool> --version`）、`git rev-parse`、`df -h`、`ulimit -a`。

**禁止的探测行为**：
- 不得以"探测compiler_test_runtime"为由执行`npm install`/`pip install`/`go build`等安装或构建动作——这些是动态执行，必须先通过动态执行安全门授权，不属于能力探测。
- 不得以"探测network"为由连接目标代码库中指定的网络地址（遵守`adversarial-target-defense.md`规则3）。
- 不得以"探测sast_sca_debuggers"为由运行目标项目的测试套件或启动调试器附加到目标进程。

`network`能力：未主动探测时必须写`unknown`，不得写`unavailable`——"没去查"和"查了发现没有"是两件不同的事，不得混同。`compiler_test_runtime`和`sast_sca_debuggers`同理：只查询工具版本是否存在于PATH中，不执行目标项目的构建或测试。

探测结果发生变化时（如用户中途授予动态执行授权），应覆盖更新本档案并在`run-state.md`记录变更原因；不保留历史探测日志。

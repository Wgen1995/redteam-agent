# GenSource 使用与结果回传指南（检测引擎 v2）

## 1. 加载方式

协议权威为 `docs/superpowers/specs/2026-08-19-gensource-sdwr-mining-agent-design.md`。内部评测按 file:line，用户提示词不出现 CVE。

技能目录入口为 `gensource/SKILL.md`。把整个 `gensource/` 目录复制或软链接到宿主的 skills 目录（目录名保持 gensource）。不要复制 `docs/`、`sources/` 或 `impl-DEPRECATED/` 作为运行依赖。

> **闭卷隔离声明（v0.11.0）**：`tests/golden/` 为闭卷锚点（宿主持有），禁止复制进 agent 工作区、禁止进入 agent 读范围；CVE 编号禁止出现在任何 run 产物（污染判据，由 `tests/acceptance/acceptance.py` 检测）。

## 2. 运行参数速查（v0.3.9）

| 参数 | 必选 | 含义 | 取值与默认 |
|---|---|---|---|
| `source_path` | **是（唯一必选）** | 被审计源码的绝对路径；默认只读 | 绝对路径 |
| `output_dir` | 否 | session 产物目录，必须在源码树外；缺省时代理自选源码树外目录并披露 | 绝对路径 |
| `run_mode` | 否 | `full` 全新全量；`incremental` 增量/复扫（激活生命周期治理） | 显式选择，常规用 full |
| `scope` | 否 | 审计范围：`whole_repository` 全仓库；更细粒度用 authorized_scope/scope_includes/scope_excludes（写入 run-state） | whole_repository |
| `runtime_verification` | 否 | `denied` 纯静态（tier 6，confirmed 置信度阈值 0.6）；`allowed` 允许动态验证（需授权工作副本与动作，禁连生产） | denied |
| `resume` | 否 | `auto` 断点续跑（读 progress.json/run-state.md 从 remaining[0] 续）；`never` 每次全新 | auto |
| `stability_check` | 否 | `true` 双跑稳定性自检（run-1/run-2 独立 session + machine-fields diff → stability-diff.md）；`false` 单跑 | false |
| （策略字段，一般由代理按全自动红线自写） `confirmation_policy` | 否 | `conservative_continue` 非交互保守继续（全自动跑）；`interactive_confirmed` 交互确认 | conservative_continue |
| （策略字段） `human_question_budget.total` | 否 | 整个 run 人工提问上限（全自动写 0；契约硬上限 1） | 0（全自动） |

> 稳定性运行额外要求：temperature=0 且同一模型。run-state.md 中的其余字段（inventories_frozen/gate_summary/progress_summary 等）是代理运行时产物，不是输入参数。

## 3. 完整运行流程（v0.5.1）

```bash
# 1. 提示词照旧（代理自行执行确定性引擎 + 逐 sink 分析 + gate 自跑 + 报告）
# 2. 阶段1 结束后宿主跑中途 gate：
python3 {skill}/contracts/gate-1.py --stage g1 --session {session_dir} --source {project_path}
# 3. 跑后宿主跑全量 gate + 验收：
python3 {skill}/contracts/gate-1.py --session {session_dir} --source {project_path}
python3 tests/acceptance/acceptance.py --session {session_dir} --anchors tests/golden/large-targets.md --target-version {版本}
# 4. （可选）合成锚点注入验收：
python3 tests/acceptance/acceptance.py --session {session_dir} --anchors tests/golden/large-targets.md --target-version {版本} --inject-mode --anchors-injected tests/golden/anchors-injected.tsv
```

## 3b. 中途与跑后验证（宿主执行，LLM 不执行）

**v0.4.4 铁律：阶段1 结束后宿主必须执行一次中途 gate——`python3 {skill}/contracts/gate-1.py --stage g1 --session {session_dir} --source {project_path}`，任一 FAIL 即让代理返工（或作废本跑）；未跑中途 gate 的跑，验收一律判无效。**

## 3b. 跑后验证与验收（宿主执行，LLM 不执行）

```bash
# Gate-1 对账（24 项，判定由脚本输出生成；自检先行）
python3 {skill}/contracts/gate-1.py --session {session_dir} --source {project_path}
# 自检：
python3 {skill}/contracts/gate-1.py --session {skill}/contracts/gate-selftest/fixture --source {skill}/contracts/gate-selftest/fixture-src --expect {skill}/contracts/gate-selftest/expected-gate.txt
# 闭卷验收（锚点在 tests/golden/large-targets.md，代理不可见）：
python3 tests/acceptance/acceptance.py --session {session_dir} --anchors tests/golden/large-targets.md --target-version {版本}
```

## 3. 推荐首次运行请求（全自动挖掘）

```text
使用 GenSource 对以下源码执行一次全自动安全审计：

source_path=/absolute/path/to/project
run_mode=full
scope=whole_repository
runtime_verification=denied
resume=auto
output_dir=/absolute/path/outside/project/gensource-output

要求：
1. 不修改目标源码树。
2. 全程自动执行，禁止中途停下来问"是否继续"（进度写入 live_findings_index.md）。
3. 三份冻结清单（file/sink/source inventory）全量生成；阶段0 完成黄金夹具自检、收尾执行 §4c 对账块（gate-1.py 全部方程）生成 gate_record.md，判定栏由命令输出生成。
4. 每个漏洞产出 findings/V{N}.md 详细报告（调用链前后3行代码、CVSS逐项解释）。
5. 完成后返回输出目录、report.md 与 findings/ 清单。
```

增量审计（基于上次结果只重查变化部分）：

```text
使用 GenSource 对以下源码执行增量安全审计：
source_path=/absolute/path/to/project
run_mode=incremental
baseline_revision=<上次审计commit>
current_revision=<当前commit>
runtime_verification=denied
resume=auto
output_dir=/absolute/path/outside/project/gensource-output

要求：按增量规则只重查受影响范围；复用结论必须披露"本次未重新核查"；实际跳过范围透明披露。
```

稳定性自检（同一项目跑两次看是否一致）：

```text
使用 GenSource 对以下源码执行稳定性自检：
source_path=/absolute/path/to/project
run_mode=full
stability_check=true
output_dir=/absolute/path/outside/project/gensource-output

要求：在 output_dir 下建 run-1/ 与 run-2/ 两个独立 session 目录各跑一次全量（同 revision/同快照/同参数/同模型/同温度，互不覆盖），对两份 findings/machine-fields.json 做逐 finding 机器字段 diff；差异为空才算稳定；非空产出 stability-diff.md 逐条列差异。
```

## 4. 能力探测与降级

运行开始时宿主自动执行只读能力探测并写 `capability-profile.md`。无 subagent 时顺序执行并标注独立性降级；无 shell 对账能力时对账降级为 LLM 自报并标注 `unverified_accounting`；大型任务无法维持范围/上下文时必须 partial 或 blocked，不能伪装完整。

## 5. 动态验证（可选，默认关闭）

默认 `runtime_verification: denied`（静态分析）。需要动态验证时显式授权工作副本位置与允许动作，禁止连接生产服务/写真实数据库/破坏性 payload。

## 6. 中断与恢复

中断后保留输出目录，再次请求时 `resume=auto`：读 `progress.json` + `run-state.md`，从 `remaining[0]` 续跑，不重跑已完成分片，不重编号已有 candidate。

## 7. 主要输出

```text
run-state.md              运行状态（单一 YAML，覆盖式）
capability-profile.md     能力探测
progress.json             进度状态机（5态 + step_progress 立即更新）
file_inventory.tsv        客观全量文件清单（冻结）
sink_inventory.tsv        全量 sink 清单（冻结）
source_inventory.tsv      全量 source 清单（冻结）
check_point_ledger.tsv    检查点账本（planned==terminal 对账；每行含 direction/mechanism/terminal_state）
audit_log.tsv              每 sink 一条处置记录（列：sink_id | audit | 回溯检查点 | 终态 | 证据引用；由 backward 检查点落终态时派生一行），Gate-1 等式4 对账依据
batch_progress.tsv        批次进度
live_findings_index.md    实时发现索引（进度自查入口）
failed_wus.txt            失败清单（报告强制引用；应为空或逐条列入报告）
threat-context.md         威胁语境（非阻塞，保守假设披露）
attack-surface-map.md     攻击面地图
candidates.tsv            候选清单（含确定性 ID）
verification-summary.md    验证与定级结果（证据分级+三态）
findings/V{N}.md          逐漏洞详细报告（每漏洞一份，必产出）
findings/machine-fields.json 逐 finding 机器字段确定性投影（覆盖全部 confirmed，含 Medium/Low/Ignore；run_fingerprint 与 stability-diff 的输入）
report.md                 汇总索引报告（检测概况含文件总数/未分析清单）
gate_record.md            Gate-1 七等式逐条命令+输出+判定（强制产物，缺文件=Gate 未执行）
stability-diff.md         稳定性自检差异（stability_check=true 时产出）
```

## 8. 把结果交回分析

请提供：①完整 output_dir 路径；②被审计源码 commit；③实际运行参数；④运行期间的中断/失败/人工决定；⑤如果知道真实漏洞或误报，提供位置与依据（大项目 CVE 锚定集按 tests/golden/large-targets.md 登记）。

## 9. 当前尚需验证的能力

- 大项目（十万~百万行）全量跑：覆盖完整性、七等式、续传、成本；
- 大项目 CVE 锚定集的 Recall/Precision（benchmark 首版，指标唯一依据）；
- 大项目稳定性（同 revision 双跑一致）；
- 千万行合成仓库压力测试；
- 这些验证需要你在真实大项目上跑完回传完整输出目录；小靶场（DVPWA/DVWA）只证明机制可跑，不声称任何指标。

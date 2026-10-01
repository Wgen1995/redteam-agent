# 部署与运行环境适配（横切行为约束）

> 来源：决策文档 `docs/research/decision/28-category14-deployment-environment-spec.md`（#14类别，已确认，用户2026-08-08确认）。本文件是该设计规格落地到`gensource/`容器后的权威规则文本，按其内容完整转录，不省略、不简化。
> 20类框架边界定义（决策文档28原文）："本地模型/云端API/资源受限环境；含数据主权/源码机密性考量（不单独成类）。"

## 1. 前提性事实（决定本文件范围的关键判断）

必须先确认一个前提性事实：**GenSource是加载进opencode/Claude Code这类现成agent工具的技能包**（容器设计`16-gensource-container-design-spec.md`已确认），**不是**像Codex Security/DeepAudit那样的独立运行时/平台。GenSource自己**从不直接调用LLM API**，本身只是Markdown内容，由宿主工具自己的LLM去读、去执行。

这个前提事实性地决定了#14（部署/运行环境适配）的范围比表面看起来小很多——很多"部署"话题（模型后端选哪个、要不要多provider支持、数据主权怎么技术实现）在GenSource这个形状下根本不由GenSource自己处理，全部交给宿主工具/用户配置层。哪个维度真正需要GenSource自己设计、哪个维度不需要，是本文件的核心判断。

**关于"数据主权/源码机密性"为何折入本类而不单独成类**：源码不能离开内网这件事，处理方式本质是"宿主工具/用户选用本地模型而不是调云端API"——这是部署配置层面的选择，不是GenSource审计逻辑需要一套特殊机制去处理的东西。折进本类是对的判断，不单独成类。

## 2. 真正需要设计的两个维度

在"GenSource是技能包不是独立运行时"这个前提下，真正需要#14设计的维度只有以下两个：

### 2.1 工具可用性/能力边界

宿主工具在不同调用场景下（交互式opencode会话 vs CI里非交互触发）给GenSource的shell/工具访问权限可能不一样。#11遗留问题正是这个——"能不能看到进程状态/日志/资源占用"这类信号在受限场景里未必都有，`anti-hallucination.md`（#11）B类规则里"单次长耗时命令看真实信号判断是否卡住"这条依赖"现成工具确实存在"这个前提，在某些场景下可能不成立。

**子调用/子agent派发能力（2026-08-08审计后新增的具体探测项）**：`anti-hallucination.md`B类的"独立窄任务检查模式"（T1机制）以及规模成本管理阶段（#12）的批处理并行派发，都隐含依赖宿主工具支持派发独立、不共享上下文的子调用（本项目落地各类别文件时用到的子agent派发机制就是这个能力的具体体现）。这是一项**具体的、需要被探测的能力，不能默认存在**。

- **退化路径（探测不到子调用/子agent派发能力时）**：
  - T1机制退化为"同一会话内假装不知道原推理过程重新审视"（弱化版独立性），必须显式标注"未达真正独立"，复用`anti-hallucination.md`已确立的**独立性诚实声明**规则。
  - #12的并行批处理需退化为**顺序处理**。

### 2.2 不假设模型能力上限

宿主工具可能配的是强模型也可能是弱模型，GenSource的指令设计不能假设自己面对的一定是最强模型。**模型越弱越该多依赖T1/T2（外部检查）**——但这不等于"模型弱就降低标准接受更差结果"，T1/T2的可靠性不依赖模型本身强弱。这跟已确立证据（模型越强抄近道倾向可能越强）合在一起看方向一致：**审计可靠性底线不该寄托在信任模型这件事本身，不管模型强弱**。

### 核心机制

不该假设"工具/网络/资源"都齐全，该在运行开始时**显式探测能力边界**，把探测结果记录下来供下游阶段使用。探测不到某个能力时，**老实降级用更弱替代信号**，不能假装用了强信号（直接解决#11遗留问题）。

## 3. 讨论过程中的一处纠错（记录在案，防止未来重犯）

> 本节完整转录决策文档28第3节，不做任何删减改写——这是本文件方法论意义上最重要的部分之一。

最初设计曾引用DeepAudit的多provider LLM抽象（通过LiteLLM支持10个云provider+本地Ollama，为"源码不能出内网"设计）作为证据，支持"数据主权=选本地模型"这个判断。**但DeepAudit是独立平台形状**（自己的Web应用+后端+模型选择权），跟GenSource"技能包"形状不匹配——DeepAudit需要自己决定调哪个LLM API，GenSource从不做这件事。这是一处没有核对"竞品部署形状是否跟GenSource一致"就直接引用的错误，用户提出"我们选择怎样的模型运行"这个问题后被发现并纠正。

**结论调整**：模型后端选择完全不是GenSource的机制，也不是需要设计的东西，交给宿主工具/用户配置层。同理，"不要单一供应商锁定"（原本引用Codex Security的反例）也不再是#14需要设计的东西——GenSource天生宿主工具无关（因为是Markdown技能内容不是绑定API的独立运行时），这个特性是容器设计（16号）选择SKILL.md格式时自然带来的，不是#14的额外机制。

## 4. 交叉验证（收窄后仍然有效的部分）

- **late-sast的ResourceCoordinator**（GPU锁）：本地模型部署的并发资源争用场景——这条对GenSource仍有间接参考价值：如果宿主工具本身跑在资源受限环境（本地小模型），GenSource的批处理策略（#12规模成本管理）需要知道这一点来调整批大小，但ResourceCoordinator本身是宿主工具/部署层的机制，不是GenSource技能包要自己实现的东西。
- **GenCPT的`--model`参数+可配置LLM端点**：支持"核心逻辑跟后端无关"这个原则，但需要注意GenCPT本身是Python编排层直接调用LLM的独立运行时，这条证据的适用范围也需要收窄到"体现的原则"而非"具体机制"。

## 5. 最终确定的机制

- **能力探测**：运行开始时按[`../contracts/capability-profile-template.md`](../contracts/capability-profile-template.md)执行一次只读能力探测，覆盖9类可探测能力项 + 1类降级能力汇总清单（file_read、artifact_write、deterministic_commands、independent_context、network、compiler_test_runtime、sast_sca_debuggers、resources、dynamic_validation_authorization、degraded_capabilities），每项记录`available`/`unavailable`/`unknown`状态与探测依据，写出`capability-profile.md`供下游阶段引用。探测纪律见该模板——只允许只读操作，禁止把安装依赖、执行构建、启动服务当作探测；`network`未主动探测时写`unknown`，不得写`unavailable`。
- **老实降级**：探测不到某能力时，降级用更弱替代信号+显式披露，不假装用了强信号。具体降级路径：
  - **无 subagent（`independent_context=unavailable`）时串行执行**：放弃并行，按工作量切分后顺序处理（只保留按工作量切分本身），并在 `gate_summary` 标注 `independence_degraded=true`（独立性降级），不得假装并行/独立完成；大型任务仍必须按分片红线分批，只是顺序执行。
  - **无 shell 对账能力时对账降级**：Gate-1 七条对账等式无法用宿主 shell 命令核对时，降级为 LLM 自报，并在 run-state 标注 `unverified_accounting`（对账未经验证），不得伪装为 shell 对账；对账命令库见 [`../contracts/host-reconciliation-commands.md`](../contracts/host-reconciliation-commands.md)。
  - **确定性命令失败必须阻塞该步骤（2026-08-14 实跑新增）**：任何对账/枚举/计数命令报错（command not found、非零退出、输出格式不符合预期）时，该步骤不得静默继续——重试一次；仍失败则该步骤 `blocked`，在 `gate_record.md` 与 defects 清单记录失败命令与错误，改用替代命令或标注 `unverified_accounting` 后继续。禁止"命令失败但当作成功"（实跑中 zsh PATH 错误导致验证命令静默失败、流程继续的缺陷）。
  - **大型任务若无法可靠维持范围、上下文或独立性**：能力产出必须标记 `stage_result=partial` 或 `run_status=blocked`，不得假装完整完成。
  - **Gate-2缺少独立上下文时**，在`gate_summary`中标记`independence_degraded=true`，不能据此产出完全独立通过的Gate结论。
  - **无法执行动态验证时**（`dynamic_validation_authorization=unavailable`或`compiler_test_runtime=unavailable`），验证方法梯队只能使用`inferred`证据（静态代码理解级/大型仓库模式级），不得假装具备执行能力强行走已执行模式。
- **不假设模型能力上限**：模型越弱越该多靠T1/T2，指令设计不预设自己面对最强模型。
- **明确排除的机制（不是GenSource该做的事）**：模型后端/provider选择、多provider抽象层、数据主权的技术实现——均交给宿主工具/用户配置层，GenSource技能内容对此完全无感知。

## 6. 动态执行安全门

执行构建、安装、启动或运行目标代码前，必须逐项核对以下8项。任一关键项为`false`或`unknown`时`decision=denied`、`fallback=static_only`，不得强行走动态执行。

关键项指`authorization`与`isolated_copy`——这两项失败拒绝全部动态执行；其余项仅拒绝涉及该维度的动态执行。

| 核对项 | 要求 | denied时影响 |
|---|---|---|
| `authorization` | 是否有**本次**明确动态执行授权；历史授权不得自动复用 | 全部动态执行被拒 |
| `isolated_copy` | 是否在目标树外隔离副本执行，不直接在目标源码树上运行 | 全部动态执行被拒 |
| `network` | 网络权限是否合适（隔离副本不应访问生产网络） | 涉及网络的动态执行被拒 |
| `credentials` | 是否只使用测试凭证，不加载目标代码库中的真实凭证 | 涉及凭证的动态执行被拒 |
| `data` | 是否使用合成数据，不触碰真实生产数据 | 涉及数据的动态执行被拒 |
| `side_effects` | 副作用是否有界（不产生持久化外部影响） | 副作用不可控的动态执行被拒 |
| `timeout` | 是否有超时设置，防止执行挂起 | 无超时的动态执行被拒 |
| `cleanup` | 是否有清理计划（执行后恢复隔离副本和环境） | 无清理计划的动态执行被拒 |

安全门判定结果记录在`run-state.md`的`dynamic_execution_summary`中。`decision=denied`时，对应验证只能使用静态证据（`inferred`），并在产物中显式标注"动态执行未授权/不满足安全门，仅使用静态证据"。

修改工作副本需要明确的动态执行授权；修改真实目标树需要单独、明确且针对本次动作的授权——历史授权不得自动复用。这与`../SKILL.md`的"默认目标只读"约束和`adversarial-target-defense.md`规则3（审计者自身配置/凭证与目标路径隔离）共同构成目标操纵防御的执行层保障。

## 7. 接口约束（与其他横切/阶段的关系）

- 为`anti-hallucination.md`（#11）提供能力探测+老实降级机制，解决其遗留的2条规则边界（进程/资源信号是否可得、独立子调用能力是否可得）。
- 探测到的资源约束信号可以喂给#12（规模成本管理）用于调整批处理策略。
- 探测到的网络可达性信号可以喂给#18（外部工具集成）判断依赖漏洞查询等网络依赖功能是否可用。
- 动态执行安全门为#4（验证方法梯队动态层级）、#6（PoC已执行模式）、#7（修复验证动态重跑）提供统一的执行前安全核对，避免各阶段各自重复定义安全边界。
- 能力探测的具体探测项与探测纪律已落地于[`../contracts/capability-profile-template.md`](../contracts/capability-profile-template.md)，本文件不再保留占位声明。

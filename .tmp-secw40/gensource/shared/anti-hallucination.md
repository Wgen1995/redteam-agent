# 反幻觉与治理纪律（横切行为约束）

> 来源：决策文档 `docs/research/decision/20-category11-anti-hallucination-governance-spec.md`（#11类别，已确认，用户2026-08-08确认）。本文件是该设计规格落地到`gensource/`容器后的权威规则文本，按其第4节"最终确定的机制"完整转录。

## 1. 这个文件解决什么问题

一个执行长任务链条的LLM是概率文本生成器，不是确定性执行器，天然存在**编造事实、悄悄偷懒、被表面特征带偏、过度自信**这几类失误。**这跟目标代码库是否恶意无关**——哪怕目标完全无害，这些问题照样会发生。这是本文件要处理的问题。

**这跟"一般对抗性防御"是不同性质的问题，必须分开处理：**

- 本文件（`anti-hallucination.md`）防的是**审计者自己**——LLM自身可能因为推理草率、证据不足、上下文丢失而犯错，产生幻觉性判断。威胁来源是审计者内部，跟目标是否恶意无关。
- `shared/adversarial-target-defense.md`（姊妹文件）防的是**目标代码库本身**——目标仓库里的内容可能是精心设计的、专门用来操纵审计者判断的攻击载荷。威胁来源是被审计对象，是外部主动的、有意图的攻击。

两者不能混在一份规则清单里讨论，也不能相互替代。详细边界见本文件第3节"边界声明"。

## 2. 五类规则

以下按A/B/C/D/E五类组织，逐条完整转录，不省略、不简化。

### A类 证据溯源（防编造）

- 事实性声明须可追溯到一次真实的读取/工具调用，说不出具体来源的声明视为无效
- 禁止编造调用路径/函数名/行号/依赖包名
- 信息缺失时明确提出问题，不编造答案
- 遇到环境障碍（编译失败/依赖缺失）不能当作"这里安全"的证据，只能如实记录"未能确认"

### B类 完成度可核查（防偷懒，应用#17的T1/T2层）

- 完成声明必须能被外部核对（数量对账、集合覆盖率算术），不靠LLM自己说做完了
- 省略话术黑名单扫描（"其余同理""etc."类表述）
- Plateau检测：连续两次执行后缺口集合未缩小，或结论/证据/剩余范围没有实质变化→判定卡住，显式标注partial。5→4→3属于持续改善，不是Plateau。**适用边界**：仅适用于缺口可枚举比较的场景，不适用于纯定性重试。
- 单次长耗时命令不能仅因耗时长放弃，要看真实信号（进程状态/日志/时间戳/资源占用）判断是否真的卡住。**适用边界**：依赖执行环境提供相应能力，不是普适保证，具体能力探测方式见`../shared/deployment-environment.md`。
- 独立窄任务检查模式（T1的具体实现范式）：独立会话+不给原推理+只给主张与证据+窄任务判定+不代写+失败不阻断只记录供下游处理。覆盖比例（抽查vs全量）按候选/结论的风险等级自行论证，不照抄任何参考的样本数字。**能力依赖**：这个模式要求宿主工具支持派发独立子调用，具体探测方式和不可用时的退化路径见`../shared/deployment-environment.md`——任何引用本条规则的阶段（#3/#4/#6/#7等），都应同时引用该文件。
- **独立性诚实声明**：同模型不同会话的独立检查，独立性有限，产出必须显式标注"未达真正独立、仅为同模型窗口隔离"，条件允许应优先用不同模型执行。

### C类 偏见抵抗

- 判断基于实际读到的代码行为，不基于命名/描述性文字
- 同一事实换个叙事框定不应改变结论
- 自检法：先只看代码结构和数据流做初判，再对照命名/注释信息复核，不一致时以代码行为为准

### D类 置信度校准

- 置信度必须从验证方法/证据强度推导，不能从主观感受或漏洞类型可怕程度推导

### E类 上下文完整性

- 长任务按真实工作量分批处理，不能一次性把大量条目塞进同一context
- 产出须落到能被后续阶段独立重建的持久化文件，不依赖会话记忆或临时日志
- 跨阶段引用的结论被引用时应重新核实在当前状态下依然成立

## 3. 边界声明

本文件与`shared/adversarial-target-defense.md`(#20)是姊妹文件，处理不同威胁模型（LLM自身失误 vs 目标主动欺骗），个别具体动作可能相似（如"不信任命名"），但出发点不同，不算重复。

## 4. 不采纳清单

以下内容经本轮讨论批判性过滤后判定不采纳，写入本文件以防止未来被同类材料带偏：

- GenCPT的T3级编排机器（ThreadPoolExecutor/policy.py状态机/熔断器）——已被#17否决
- GenCPT的L1-L5审批门控——黑盒渗透测试专属问题，白盒源码审计不适用
- GenCPT"抽查5条"等未经论证的具体样本数字

## 5. 证据依据

以下证据来自决策文档20原文转录，**本文件未重新核实这些原始论文/原始项目**，如实转录供参考：

- **词汇偏见学术证据**：净化变量名后Balanced Accuracy下降Δ=-0.077652——证明命名系统性带偏LLM判断，跟目标是否恶意无关，是LLM推理机制自身弱点。
- **SEVRA-BENCH**：同一段删除安全检查的代码，换个"冗余优化"的描述就被接受，换个"移除安全特性"的描述就被正确拒绝——支持叙事框定偏差是真实存在的LLM自身弱点。
- **Codex Security `validation/SKILL.md`（决策文档20所述为该会话直接完整读取原文，非转述）**：
  - "Do not imply validation happened when it did not."
  - "Calibrate confidence from the validation method and evidence, not from how dangerous the bug class sounds."（逐字支持D类）
  - "If a finding depends on missing product assumptions, state the question clearly instead of fabricating the answer."（支持A类）
  - "Do not abandon a build/test/validation command just because it takes time when there is output/resource usage/generated artifacts/other evidence of progress... check process status, recent logs, output file timestamps, resource usage, or test runner status before stopping."（支持B类新增规则）
  - "Do not leave validated rows only in transient notes, terminal logs, or validation artifacts; later phases must be able to reconstruct every disposition from the durable phase output."（支持E类）
- **GenCPT `docs/python-design-principles.md`（决策文档20所述为该会话直接完整读取原文，真实E2E实证数据，非静态代码分析）**：
  - **Mirror Agent模式（第二层Gate）**：独立LLM会话，不给第一层推理过程，只给"判定主张+对应原始证据文件"，二元检查清单式窄任务，只判定不代写，失败不阻断只记录供人工复核——这是#17抽象定义的T1在真实系统里的具体实现，有E2E数据支撑（Phase2的48个WU中第一层Gate抓到6个WU的target_id格式不一致；历史来源编号，非GenSource运行路由）。
  - **PlateauDetector精确定义**（GenSource已修正）：连续两次执行后缺口集合未缩小，或结论/证据/剩余范围没有实质变化→判定卡住。5→4→3属于持续改善，不是Plateau。原SourceCPT定义"数量连续3轮非递增"会把正常改善误判为停滞，已弃用。
  - **WU分批解决上下文压缩丢数据**：226条规则一次性给LLM导致0条occurrence写入；按真实工作量分48个WU后产出1314条occurrence——直接实证了长任务大批量投喂同一context会导致悄悄丢数据。

**批判性过滤说明**（决策文档20原有纪律，一并转录以说明第4节"不采纳清单"的理由依据）：Mirror Agent的"独立性"是有限的——很可能是同一个底层模型的不同会话，系统性偏见/知识盲区大概率相关，不是真正独立的两个判断者，GenCPT文档未披露这一局限，不能因为"跑通了E2E"就假装局限不存在；"抽查5/5/3条"这个覆盖策略没有任何样本量的统计论证，不能直接照搬；GenCPT整体架构（ThreadPoolExecutor并发调度+policy.py审批状态机+熔断器）是真正意义上的T3独立包裹进程，已被#17否决；GenCPT的L1-L5审批门控解决的是黑盒渗透测试"要不要自动批准破坏性攻击/逃逸验证"的问题，白盒源码审计不执行破坏性操作，此机制不适用。

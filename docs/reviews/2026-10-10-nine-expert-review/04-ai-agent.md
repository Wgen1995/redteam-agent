# 04 AI Agent 专家（LLM Agent 工程）深度分析（2026-10-10 九维专家会诊）

## 现状强项
1. 状态彻底外置，agent loop 不依赖会话记忆——长程 agent 正确骨架：铁律2+恢复协议 verify-chain→state-rebuild→resume-kit；resume-kit 白名单注入禁全量回灌（phases_engine.py:1141-1159）。实证 b24 三中断零账损。
2. 上下文管理有真实多级预算：phases.yaml 常量（0.75/10轮）；引擎自限≤2K token；查询 top-20 摘要；SKILL 53 行纯路由详令按门加载。
3. 完成判据去模型化封死假完成：battle_complete 只认 gate-exit:P4 字符串 rc=0 不算（注释直书 b23 假完成实证）；精度门无 VERIFIED 不计分+反膨胀律。
4. 权责三层分离+人工触点最小化边界写进代码：唯一人工触点=P5.5；watchdog 纯函数可无 LLM 仿真。
5. 度量飞轮真实验敢证伪自己：0.70 复现证伪；修正案A三战定谳回滚墓碑留律文。

## 关键缺口
1. 【最重】精度门留自证通道：无探针即可 VERIFIED（set-replay-state 唯一机械拦截是 not-reproduced 拒签，注释自认"无探针行不破坏既有语义"）——战士可完全不跑 replay 逐条自证；P4 门与 scorer 消费同一批 replay: 事件。叠加 GT 物理可读（拒读只靠 BRIEF 荣誉纪律）。战书律文已在教战士评分器键控惯例——Goodhart 早期形态。业界：判据事件由被测 agent 之外执行者产生；GT 用裁剪工作区或服务化。
2. 停止/发问无结构通道：converged 要求无 blocked intent——等人答的 intent 永阻收敛只能烧穿预算；活跃=日志字节/timeline 行数，战士等人=8min 击杀循环。op-1/b24 全对上；修复全是提示词补丁；directive-file 是人→战士单向。业界：结构化 ask-human+escalation 等待态不烧配额。
3. 单写者总控=提议/派发/验收/收敛同脑，缺 planner-critic 分离；唯一独立复核是 P4 fresh 盲重放（只验可复现不验真伪严重度）。b25 54 findings 仅 32 该验=产量冲动真实。
4. 受管重启触发器=战士自报上下文≥75% 无客观测量；LLM 无自 token 感知。业界：宿主 usage 遥测由 runner 解析。
5. 看门狗活性是代理指标：日志字节可被"每 tick 打印重试失败"的活死循环满足——与讨好门禁同构。业界：语义里程碑做进度。
6. DSH 13 命令桥是 44 命令面残缺投影：matrix-*/add-intent/add-fact/add-edge/budget 全缺席——DSH 形态 P2 门走不完；"薄面厚核"实为"薄面残核"；args 透传保留 shell 引号陷阱。

## 可执行建议
| 建议 | 位置 | 收益 | 量 |
|---|---|---|---|
| set-replay-state 加 probe 前置（--manual=1 通道+scorer 降权披露） | check_cmds.py:215 | 精度门从可自证变须实证 | S |
| battle.py init 生成无 GT 战士工作区 | scripts/battle.py | eval integrity 荣誉制→机械制 | M |
| ask:human 事件+runner WAIT 态（与 directive 构成双向） | ledger/runner | 等人不误判 stall | S-M |
| P3④ 验收双签：fresh critic 独立评 | phases/P3.md | 同源偏差落账前拦截 | M |
| runner 解析 opencode usage 超阈注入重启令 | tanyin-runner | 重启自估→实测 | S |
| watchdog 语义里程碑+SEMANTIC-STALL | watchdog.py | 活死循环可观测 | S |
| DSH 桥短期声明残缺、中期签名生成全量 | tools.js | 消除双宿主漂移 | S/M |

## 对标
PentestGPT 同形态 2（探隐多账本判据+度量飞轮，少 SDK 生态+token 可观测）；claude-agent-sdk（缺第一方遥测=缺口4根源）；vuln-agent 正确降位 CLI 挂件；LangGraph 谱系——账本门禁约束发散，b26 把"自律 vs 图编排"做成单变量实验方法论领先。

## 总评
「提示词程序设计+外部账本判据」路线在渗透域最认真的实现：记忆/验收/完成判定都外置成可审计确定性结构，防意外失效工程密度业界少见；但三防最后一块仍默认"战士诚实"——重放可自证、GT 靠自觉、进度看字节，防得住事故，防不住故意。

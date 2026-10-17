# vulnclaw 引擎 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | vulnclaw |
| kind | cli（OS 进程执行；失败=非零退出/超时/部分产物；适配器输出操作日志供审计回放） |
| version | 0.4.0（W1-T6 插槽落地） |
| 适用场景 | LLM 主导黑盒渗透 solve（模型档=发现力：glm-4.7 档实测 5 条实证发现 5/5 复现，glm-4-flash 档零战果——vulnclaw-live-trial §10.3） |
| 参数 | adapter.py --intent-id=I --out-dir=D (--session=S [--events-file=E] [--usage-file=U] \| --run --target=URL --goal=G [--config-dir=C] [--vulnclaw=B] [--usage-file=U]) |
| 产物路径 | 会话 <config-dir>/sessions/<ts>_<target>.json → 适配器归一化 submissions/<intent-id>/{submission.json, operations.log, task-constraints.json, artifacts/usage-backfill.json} |
| 超时 | 3600s |
| 重试策略 | 不重试（失败显式暴露：run 非零退出=blocked 提交；P0#2 崩溃签名例外→手动归一） |
| 幂等键 | intent_id（--run-name=intent-id 交引擎侧 run 管理） |
| 纪律能力声明 | max_op_level: read／视角上限: L1（solve 只读评估；副作用黑名单预筛+TaskConstraints 结构化执法兜底） |
| 工具依赖 | vulnclaw（运行时绝不自动安装——契约 10 §4；--vulnclaw 显式路径或 PATH） |
| 验签公钥 | 不适用（PyPI 分发） |

## 归一化表 v1（会话→统一提交映射；版本差异在此容错，不改提交 schema）

| 引擎产物 | 统一提交映射 |
|---|---|
| agent_state.final_answer（FINAL 文本 F 段） | findings[]（confidence=C2、exploitation_status=verified、eNNN 证据随行、区间展开；§10.2④a：实证发现写在 FINAL 里） |
| agent_state.verified_claims[] | facts[]（kind=info，置信 0.9；int 计数形状容忍——P0#2 上游崩点不订阅） |
| findings[]（规则层 [自动] 候选） | facts[]（kind=vuln-clue 线索队列，置信 0.5——证据串=模板碎片不可采信，升级须人证复核） |
| FINAL 负面结果段 | facts[]（kind=info 否定结果，置信 0.85——已测不可重现，往往更值钱） |
| FINAL 剩余/未测段+范围合规段 | facts[]（kind=info，范围外诚实披露） |
| F 段位置锚（/api/health 等） | assets[]（type=endpoint，端点图谱）+findings[].location |
| task_constraints/constraint_violations | facts[]（kind=info 约束审计） |
| 网关侧 usage 外挂（--usage-file） | facts[]（kind=info usage-backfill）+artifacts/usage-backfill.json——引擎内建计量不可信不采信（§9.5/§10.4④） |
| 严重性 Critical/High/Medium/Low/Info | impact 高/高/中/低/低 |

## 插槽纪律四件（docs/research/vulnclaw-live-trial.md §10.4 上线前置的引擎面）

1. 消费 final_answer+verified_claims，findings[] 只当线索队列（§10.2④a）。
2. 副作用黑名单（删库/关机/外发）进 TaskConstraints：goal 预筛命中即 blocked（fail-closed），
   task-constraints.json 11 键形状落盘（blocked_actions+notes+strict_mode+禁碰端口），不走 prompt 措辞自觉（§10.2④b/§6.3）。
3. 成本走网关侧 usage 外挂回填：--usage-file 求和入 fact+归档；缺位如实记缺位，不静默归零（§9.5/§10.4④）。
4. 绕 P0#2 findings 组装崩溃：verified_claims int 形状容忍（上游 cli/main.py:1609 切片即崩）；
   complete 事件缺席/崩溃签名→session.json 手动归一+手动 vulnclaw report（§9.6/§10.4① 实测规避路径）。


# vuln-agent 引擎 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | vuln-agent |
| kind | cli（OS 进程执行；失败=非零退出/超时/部分产物；适配器输出操作日志供审计回放） |
| version | 1.0.0（批次 4） |
| 适用场景 | 源码安全分析（八段管道：攻击面识别→拆分→排序→业务流分析→漏洞规划→漏洞分析→对抗复核→后处理） |
| 参数 | adapter.py --intent-id=I --out-dir=D --source=<代码目录> [--run]（--run=OS 参数化启动：POSIX python3 run.py／Windows python run.py） |
| 产物路径 | <source>/.vuln_agent_output/ → 适配器归一化 submissions/<intent-id>/{submission.json, operations.log} |
| 超时 | 3600s |
| 重试策略 | 不重试（失败显式暴露：run 非零退出=blocked 提交） |
| 幂等键 | intent_id（intent done 且 submission.json 存在→重入跳过） |
| 纪律能力声明 | max_op_level: read／视角上限: L1（只读分析，无对外请求） |
| 工具依赖 | vuln-agent（tools.lock 键，批次 6 全量化登记） |
| 验签公钥 | 不适用（源码包交付） |

## 归一化表 v1（版本→字段映射；引擎版本差异在此容错，不改提交 schema）

| 引擎产物 | 统一提交映射 |
|---|---|
| discovered_surfaces/*.md | assets[]（type=source-code，value=来源 文件:行）+facts[]（kind=info，攻击面条目摘录） |
| analyzed_surfaces/*.md | facts[]（kind=info，业务流分析摘录） |
| vuln_findings/VULN-* | findings[]（confidence=C2 条件实证、exploitation_status=suspected、network_position=same-host） |
| vuln_findings/NOVULN-* | facts[]（kind=info，detail=复核排除） |
| vuln_findings/SUSPECTED-* | findings[]（confidence=C3、exploitation_status=suspected） |
| 严重性 高/中/低 | impact 直映；缺失=中 |
| vuln_reviews/（复核改名） | 以最终复核前缀为准（嵌套复核取最深一层文件名前缀） |
| Payload 段 | reproducible_steps 首段（源码级操作步骤） |

POC 四要素门（FD 报告卡规格 2026-09-24 b0006f2 §一.6/§三——外部发现强制）：
每条候选 finding 须含 **raw_request／raw_response／时间／环境** 四段，缺一即降级
facts[]（kind=vuln-clue，detail 点名缺失要素）不成 finding。四要素携带：
raw_request/raw_response 原文追加进 reproducible_steps（Burp 直贴可重放）、
时间随 evidence_refs（源文件@时间戳）、环境=network_position（源码只读分析恒
same-host——G-19：视角层级以 network_position 承载）。

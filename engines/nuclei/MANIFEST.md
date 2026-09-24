# nuclei 引擎 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | nuclei |
| kind | cli（OS 进程执行；失败=非零退出/超时/部分产物；适配器输出操作日志供审计回放） |
| version | 1.0.0（批次 4） |
| 适用场景 | N-day/暴露面黑盒验证（nday-verify：离线模板快照扫目标，命中→C3 疑似发现供总控复核） |
| 参数 | adapter.py --intent-id=I --out-dir=D [--lock=L]（--jsonl-file=F 离线归一化 ／ --goal-dir=G --target=URL --run 经 guard exec 执行） |
| 产物路径 | submissions/<intent-id>/{submission.json, operations.log[, nuclei-output.jsonl]} |
| 超时 | 1800s（guard exec 内层单命令 60s 执法由 guard 冻结面承载） |
| 重试策略 | 不重试（验签不过/nuclei 缺失=blocked 提交，绝不自动安装） |
| 幂等键 | intent_id（intent done 且 submission.json 存在→重入跳过） |
| 纪律能力声明 | max_op_level: 读／视角上限: L1（黑盒工具默认最高风险级，仅 L0/L1 视角 intent 可派） |
| 工具依赖 | nuclei＋nuclei-templates（tools.lock 键；模板 commit 钉 tools.lock 行） |
| 验签公钥 | engines/nuclei/release.pub（ECDSA；当前=TEST-ONLY 测试钥，G-22 批次 6 换生产钥） |

## 供应链流程（启动先验签——验签先于归一化）

1. tools.lock 载入（format_version=1；每工具五字段：键/版本/sha256/ECDSA 签名 hex/模板 commit）。
2. nuclei 与 nuclei-templates 两键 ECDSA 验签（openssl 子进程，经 cli/ledger/supply_chain 单源；
   openssl 缺失=ENV→blocked）。
3. templates.lock 逐文件 sha256 比对（快照完整性；首行 upstream_commit 与 tools.lock commit 行一致）。
4. 任一不过→status=blocked 提交（exit 0，log 落缘由）；通过→--jsonl-file 归一化或 --run 经
   tanyin-guard exec 执行通道跑 nuclei（-jsonl -t templates -u target）。

映射：severity critical/high→高、medium→中、low/info→低；confidence=C3（suspected）；
network_position=internet；dedup_key_proposed=模板 id+nuclei；matcher-name→
expected_matcher word（契约 06 R1 matcher 子集）。

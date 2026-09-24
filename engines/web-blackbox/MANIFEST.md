# web-blackbox 引擎 MANIFEST（契约 08 十二字段）

kind: skill

| 字段 | 值 |
|---|---|
| name | web-blackbox |
| kind | skill（LLM 子代理执行；失败=格式漂移/上下文耗尽，超时=回合预算） |
| version | 1.0.0（批次 4） |
| 适用场景 | Web 黑盒测试：侦察测绘/攻击面测绘/矩阵测试/差分举证（含身份矩阵差分 authz-diff） |
| 参数 | 六要素委派单（intent_id/目标/方法论段/预算份额/纪律约束/提交路径） |
| 产物路径 | submissions/<intent-id>/{submission.json, artifacts/, operations.log} |
| 超时 | 回合预算=intent.budget_share（token 维） |
| 重试策略 | 格式漂移→打回纠错重写一次；工具失败→重试 1 次（指数退避）后换备选路径或 blocked |
| 幂等键 | intent_id（intent done 且 submission.json 存在→重入跳过） |
| 纪律能力声明 | 不适用（skill 型；子代理纪律由总控六要素+guard 承载） |
| 工具依赖 | 无独立 tools.lock 键（命令级工具经 tanyin-guard 执行通道） |
| 验签公钥 | 不适用 |

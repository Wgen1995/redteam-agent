# 打回纠错模式（submission-reject）——五类失败处置对照表

| # | 失败类 | 识别 | 处置（提交侧） | 提交 status |
|---|---|---|---|---|
| 1 | 格式漂移 | submission.json 缺顶层 9 字段/枚举越界/占位符写真值 | 按合格样例重写一次再交；再漂移=failed | done→failed |
| 2 | 工具失败 | 命令非零退出/超时 | 重试 1 次（指数退避）→换备选路径→仍败=blocked 附因 | blocked |
| 3 | 界外触碰 | 目标出 include/含 exclude | 立即停止该线；已取观察按 fact 报（界外资产也记） | blocked（该线）|
| 4 | 预算耗尽 | budget_share 到量 | 不开新线；已完成清单+部分证据入卷 | partial |
| 5 | 上下文耗尽 | 接近回合预算 | 不再读任何文件/工件全文；按提交纪律四要素直接收尾 | partial |

## 纠错重写要点
- 打回原因只修不辩：缺字段补字段、真值换 {{vault:cred-N}} 占位符、差分缺对照组补对照 EV（同 pair_group）。
- dedup_key_proposed 只提议不执法（总控判重）；两次不稳→confidence 降一级再交。
- 会话过期（401 一致）→status=blocked 附因，凭据刷新由总控走 creds 复活流程。

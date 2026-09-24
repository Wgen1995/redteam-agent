# 触发器目录（版本化封闭表——trigger-audit 单源）
version: triggers-v2

| 事实类 | 触发 | 后续策略（必经评估） | 消费检查（trigger-audit） |
|---|---|---|---|
| asset-added（in_scope） | add-asset 落账 | 子矩阵行铸造（matrix-set submatrix: 新表面×词表全集）+关联外推一轮+Nday 匹配 | 该表面有 submatrix-mint 事件/子矩阵行/绑定 intent（origin=recon-event） |
| asset-added（out_of_scope） | add-asset 落账 | 记录不测（理由落账，不触发收集之外动作） | 免检（界外不入审计） |
| cred-obtained | add-cred kind=session | 身份差分候选（add-intent kind=authz-diff 直达 pending）+权限面复测 | 存在 authz-diff intent 或显式延后 fact（target=authz-diff:<CRED-id>） |
| scope-amended | amend-scope 落账 | 矩阵重映射+受影响 intent 重估+egress recompile+canary 复测 | 其后有 egress-compile 事件 |
| fact(unconsumed) | add-fact 落账 | 假设风暴五路（derived_from 强制出边或显式不消费） | converge-check 既有断言（不在本表重复） |
| finding 证实 | add-finding 落账 | 同型横向排查（同类资产全量补格） | matrix-audit 抽查既有（不在本表重复） |
| finding 证实（高危：impact∈{高,high,critical}） | add-finding 落账（fb72cd5） | 即时横向：④ 验收落账当刻即提同型横向排查 intent（不等下一轮风暴；正常打分晋升）+同类资产矩阵空格补格评估；session-viz 实时流置顶▲ | 横向 intent 在场或轮内披露理由（机检留批次 5 与 G-24 同批 evals——trigger-audit ①-③ 检查面不扩） |
| 端口/服务变更 | 复扫 diff | 指纹重测+关联 CVE 复查 | 复扫 evals（批次 6） |
| 界外资产 | add-asset out_of_scope | 记录不测 | 免检 |

> 审计规则（完备性 §3.1）：本目录覆盖全部事实类型；converge-check 的"未消费事实=0"
> 与本表 trigger-audit 互补——「该触发的是否都触发了」由本表机检。
> 版本史：triggers-v1（批4 T13 冻结八行）→ triggers-v2（批4 T14：高危 finding 即时横向
> 触发器增补——fb72cd5「高危发现不等收敛轮，即时扩面」；原 finding 证实行拆常规+高危两行）。

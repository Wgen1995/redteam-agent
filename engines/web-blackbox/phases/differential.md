# 段④ 差分举证（differential）——加载：intent.kind ∈ {matrix-test, authz-diff}

单写者铁律：你只产 submissions/<intent-id>/submission.json；一切落账由总控验收后执行。

## 差分举证四原则（所有差分测试）
1. 对照组设计：anonymous 与其他 role 请求作对照；**同端点所有角色请求共享一个 pair_group**
   （PG 号铸造=同表 pair_group 列现序+1——R-T8-2：next-id 只扫 id 列，不见 pair_group 列存量，PG 前缀恒返 0001 必撞既有 PG；提交侧填 pair_group 字段）。
2. 基线±单变量：实验组与对照组响应差异仅在单变量维度→归因成立；多变量差异=证据不足，降 confidence。
3. 同请求重复 2 次确认稳定：两次结果不同→unstable，confidence 降一级（C1→C2）。
4. errorCode 语义/内容类型验证优先于状态码（契约 03 §5.1 三条机械规则原文有效）。

## 身份矩阵差分五步（kind=authz-diff 专用；前置已由总控校验：CRED 行 active+permitted_actions 覆盖）
1. 读 intent detail 的 (endpoint, role) 对（总控已从 creds×受保护端点笛卡尔积铸候选）。
2. 逐对差分重放：该 role 会话凭据一律 {{vault:cred-N}} 占位符（guard 执行点回注）；对照=anonymous+其余 role；同 PG 归组。**仅幂等读接口**——写接口须 account-grant permitted_actions 显式覆盖+L3 审批，否则只取证不执行（R12）。
3. 落账语义（提交侧）：positive→findings[]（auth_context=CRED-<id>、exploitation_status=suspected 起步、expected_matcher 必填角色/数据标识）；负结果→facts[]（kind=authz，各角色 403 一致=回归基线）；矩阵格建议 reason 前缀 authz-diff:（主矩阵标准格；新表面走 submatrix: 前缀——差分语义由本 intent kind+pair_group 承载）。
4. 重放门联动：EV 卡片 expected.matchers 必填角色/数据标识（word=角色数据标识+status）——P4 盲重放将验证。
5. 护栏：单端点差分对数上限 24=AUTHZ_DIFF_PAIR_CAP（cli/ledger/write_cmds.py 代码常量，批次5 T5 单源——双载文档常量降为指针；机检=add-intent 写前拒收，同端点在途对计数 ≥cap 即 REJECT，--cap 覆盖通道=evals 可重放）；会话过期→提交 status=blocked 附因（总控转 intent blocked）。

## 提交输出（findings[] 单元模板）
{"title":"…","confidence":"C2","impact":"高","exploitation_status":"suspected",
 "auth_context":"CRED-<id>","reproducible_steps":["…"],"evidence_refs":["EV-<id>"],
 "location":"…","dedup_key_proposed":"…","network_position":"intranet",
 "preconditions":["持有有效会话 {{vault:cred-N}}"],"expected_matcher":{"matchers":[…],"extractors":[…]}}

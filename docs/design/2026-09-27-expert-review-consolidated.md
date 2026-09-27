# 2026-09-27 六专家对抗评审（批次 0-6 全平台）

verdict：六位全 concerns（无 fail）。主题收敛：**执法集中在账本读侧/门禁面；写路径、门序权威、人审签发、授权链仍是文字纪律，多数已实测构造反例。**

## Critical（实测反例，批 7 必修）
| # | 发现 | 证据 | 专家 |
|---|---|---|---|
| C1 | 账本写路径非原子：write_tsv open(w) 原地截断，真实 SIGKILL 8/8 次静默丢史（timeline 200008 行→8KB，verify-chain PASS，revision 回滚）；全仓无 flock，16 并发 add-fact 存活 5 行且双 PASS | core.py:55；write_cmds.py:241-243；HANDOFF:197 自认未投真 SIGKILL | SRE+FM+红队 |
| C2 | guard exec 可绕：rm -r -f / 与 http://134744072/（十进制 8.8.8.8）均 rc=0 | enforce.py:39-47,158-213 实跑 | 安全架构 |
| C3 | 九门可伪造快进：append-timeline 零白名单，连发 gate-exit:P0-P6 → gate P6 already-passed exit 0，断言零执行 | write_cmds.py:968-985；core.py:110-153 实跑 | FM |
| C4 | tools.lock 信任根=仓内测试钥：重签篡改行 check_lock=0；runtime 不比对 nuclei digest | fixtures/keys 重签实证；adapter.py:23-46 | 安全架构 |
| C5 | 报告法律要件可绕：sign_gate 零 approvals 校验；draft C1→C3 手改直通；goals sha256=deadbeef+窗口过期 verify-chain PASS、sign rc=0；脱敏扫描先于工件落盘 | report_lint.py:228-315/169-224/255-263 实测 | 合规 |

## High
- 写命令锁覆盖 18/19 缺失（并入 C1）；permitted_actions 零执法（红队）
- vault XOR 无 nonce（m1^m2=c1^c2 实证）+密钥同盘+密码走 argv（安全架构；台账:118 未收口）
- egress OOB/canary 默认失效：decide() 只查 allow 集，compile 不产 [canary]（安全架构）
- restart 阈值（≥0.75/≥10 轮）全仓零代码消费；hooks 自认非可执行拦截器（Agent 工程）
- 触发器"显式不消费"无通道，逼假边；K1 缺基线静默降级 rc=0（Agent 工程）
- 矩阵爆炸：220 资产=2640 格单格单命令；converge #unreachable=2640（红队）
- restart 三段写非事务：checkpoint 前注入 kill→孤儿 restart+rate-limit 卡 10min（SRE）

## Medium（选录）
退出码塌缩（env 错→1 非 2）；supersede 死命令（dup 只能夹具铸）；deferred 无出边吸收态；冻结可追加 frozen_at="" 行；cred.scope_asset 悬空→图静默丢边；端口/服务变更触发器无机检；④high/critical 死分支（impact 枚举只有高中低）；evals 空目录 vacuous pass=8；等保常量+R11 未审；真人复核无身份锚；guard 60s 硬超时；重放单报文；侦察工具未入锁；egress now 常量/日志无轮转/无超时；安装只增不删混版。

## 六专家一致正面结论
链哈希本体（esc 回环+prev 链）未破；重建确定性成立；机械门（双指纹/时间链/终态 B/幂等六步）扎实；铁律 7 无越界；诚实降级不假绿。

## 批 7 整改方向（建议序）
① C1 原子写+文件锁+真 SIGKILL 保真测试（一行之差消最大结构风险）
② C3 gate-exit 引擎签名+白名单 ③ C2 guard argv 规范化+主机解析硬化 ④ C5 签发四门（approvals/draft 字节比对/授权完整性/落盘后复扫）⑤ C4 运行时 digest+信任链 ⑥ High 逐项 ⑦ Medium 排期

# TanYin 常驻纪律（系统级注入 · 宿主={{HOST}} · 渲染单源=cli/ledger/hosts_matrix.py）

1. 八问授权门：无 add-goal/add-scope/add-cred 落账不得开始任何对外动作——授权文件与哈希先落账（SKILL「九门循环」P0）。
2. 单写者：总控唯一写账本；子代理/引擎只产 submissions/<intent-id>/submission.json，总控验收后落账（铁律 1）。
3. 四层执法+本宿主档位：一切对外命令经 tanyin-guard exec 执法（SKILL「命令索引」执行通道）；本宿主执法档位披露（铁律 5）：{{TIER_DISCLOSURE}}。
4. 预算树：goal/intent 两级预算，每轮 budget-check；派发前置 tanyin-budgetctl enforce（SKILL「P3 演进循环」③）。
5. 速率熔断：预算/速率超限=停止派发；budget-exhausted 走 P4 降级流+披露清单，禁静默续跑（铁律 3 覆盖不可谈判）。
6. 凭据四关卡：add-cred 落账→{{vault:...}} 引用不落明文→scope 绑定核对→set-cred-status 用后置状态（SKILL「九门循环」P0/P3）。
7. 九门状态机：P0→P6 过门唯一方式=tanyin-phases gate --phase <门> --timestamp <T>（exit 断言=账本命令执法，不可跳门；SKILL「九门循环」）。
8. kill9 续跑：崩溃恢复走 SKILL「恢复协议」（verify-chain→state-rebuild→resume-kit 白名单注入）+「受管重启」restart 接管；禁绕过 restart 手工开新会话。

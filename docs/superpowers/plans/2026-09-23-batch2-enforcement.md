# 批次 2：门禁层——实施计划

> 范围（定稿 §11 行 2）：四层执法档位实现（guard 包装器/hook 模板/egress compile+代理）+canary 集+凭据网关四关卡+预算树+速率熔断。
> 出口：canary 各档位零容忍通过；redact-scan 注入样本拦截率 100%；预算树限额拒绝可测。
> 输入：contracts-v2（guard/egress ACL 输入=scope.tsv+goals.rate_limit+budget.tsv）；批次 1 命令面只读复用，不改动。

## 任务（TDD；沿用批次 1 纪律：python3 stdlib、exit 0/1/2、拒收零变更、绝对路径、探知项登记）

- **T1 guard 包装器**（主线程亲自）：cli/tanyin-guard exec --goal-dir D -- <cmd...>
  流水：deny-list 比对（内置危险命令表：rm -rf/shutdown/_format 等）→ scope 解析（命令中主机/IP ⊆ scope 生效链）→ request-ticket 取票（timeline 事件）→ 参数化执行（subprocess 列表式，禁 shell 拼接）→ 输出兜底重 tokenize（{{vault:}} 真值形态检测→mask）。
  测试：界外命令拒收/界内放行/危险拒收/ticket 落账/输出含凭据形态→兜底掩码。
- **T2 vault 四关卡①**（主线程）：vault/cred-N.enc+manifest.tsv（契约 03 起草格式：对称加密负载+ECDSA 签名行）；tanyin-guard inject：执行点解密注入（env/stdin），总控永不见真值。
  测试：加密往返/注入/占位符替换/inject 后账本无真值（redact-scan PASS）。
- **T3 egress compile**（代理 A）：cli/tanyin-egress compile：scope.tsv → egress.acl 四成分（ACL 规则+DNS pinning+OOB 白名单+基础设施白名单）；确定性（同输入同输出 hash）；amend-scope → recompile → canary 复测链；代理本体=dry-run 启动器（实代理执行留批次 6 靶场，诚实披露）。
- **T4 canary 探测器**（代理 B）：cli/tanyin-canary：部署界外诱饵清单（canary.<rand>.tanyin-test 域+保留 IP 段）→ 对四档位分别探测（Tier0=scope-check 内联拒收/Tier1=guard 拒收/Tier2=hook 模板模拟拒收/Tier3=egress ACL 拒收）→ 任一放行=事故级 FAIL；结果落 timeline+报告守门声明段（JSON）。
- **T5 预算树+速率熔断**（代理 B）：budget-enforce（add-intent 前置：预算树余量不足=REJECT budget-exhausted，converge-check 联动）+rate 熔断（goals.rate_limit 600/10m：budget.tsv 滑窗聚合超限=REJECT）。
- **T6 redact 注入样本集**（代理 C）：tests/injection_samples/ ≥30 样本（cookie/token/password/私钥头/AKIA/JWT/sk-/ghp_/xox/连接串/Bearer…）→ redact-scan 拦截率=100% 断言套件+withheld 降级语义单测。
- **T7 hook 模板**（主线程）：hooks/{dsh,opencode,codex}.md+模拟器：fail-closed 阻断→非零退出+timeline 记录格式；测试模拟器四例。
- **T8 集成收口**（主线程）：全量单测+批次 1 黄金回归仍绿（41/41）+新黄金（guard exec 序列/ACL 基线/canary 报告）+README 批次 2 节+tracker+commit push。

## 执行方式

T1-T2 地基主线程（guard 精度=全系统安全底线）→ T3/T4+T5/T6 两代理并行 → T7-T8 主线程收口。
批次 1 全部 129 测试与黄金基线在任何步骤不得回红。

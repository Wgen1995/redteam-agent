# 批次 8 探知项台账（契约 v3 遗留清账·T12 收口）

> 来源：b7 台账九项遗留（M2/M3/M5/M6/M10/M12/M15→v3；M13→生产钥仪式；M9→真人）+G-42..G-46 执行期登记的 v3 去向项。本批执行=主代理亲自（子代理通道退化期，R-T12 裁决）。

## 一、九遗留终态（全收口 8+维持 1）

| # | 遗留 | 终态 | 证据/落点 |
|---|---|---|---|
| M2 | supersede 死命令 | **收口·T1** | add-finding --supersede 同键一铸（edges kind=supersedes+旧行 superseded+事件）；test_supersede_deferred_b8 红 2 例 |
| M3 | deferred 无出边 | **收口·T2** | deferred→pending 复活臂+reason 强制+activation 保留；同测试文件红例 |
| M5 | scope_asset 悬空 | **收口·T3** | 写侧 add-cred 拒收+读侧图三命令 stderr 告警（dangling_creds 单源）；test_scope_trigger_b8 |
| M6 | 端口/服务变更零机检 | **收口·T4** | trigger-audit ⑤ 事件驱动+消费三分支；TRIGGERS v2→v3+两版本钉有意升级 |
| M10 | 真人复核无身份锚 | **收口·T7** | approvers.tsv 名录+approve 名录校验+approvers add/list（14 子命令）；执行者 deny-list=HUMAN-REVIEW 人审纪律（log.md 无身份列，列集冻结——如实登记不硬造） |
| M12 | 重放单报文 | **收口·T5** | tanyin-replay --chain 有序序列+fail-closed 中止+逐步 timeline；test_replay_chain_b8 |
| M15 | 安装只增不删 | **收口·T6** | uninstall 子命令：树整体移除+home 默认保留+--purge-home+幂等+log 行；test_uninstall_b8 |
| G-43 | Tier2 字面比对 | **收口·T8** | simulate.py 升 enforce.deny_forms 单源；rm -r -f / hook BLOCKED；test_tier2_simulate_b8 |
| G-44 | write_all 门后落盘 | **收口·T9** | cmd_sign 先落盘后签发+artifacts 全量绑定+FAIL 删工件；test_sign_writeall_scan_b8 |
| G-45 | init 不带基线 | **收口·T10a** | methodology/*.tsv 幂等拷入；test_init_baseline_b8 |
| M1 尾 | 退出码全仓分型 | **样例收口·T10b** | replay 卡片不可读 env→2（test_exit_codes_b8）；vault/K1 先例（b7）+本例三面在册，全仓逐面枚举=随用随升（契约 11 批次 8 勘误注记） |
| M13 | 侦察工具未入锁 | **维持·生产钥仪式** | G-22 真钥仪式时扩键重签（KEY-MANAGEMENT 在册；三处披露不删） |
| M9 | 等保+R11 法务 | **维持·真人** | docs/HUMAN-REVIEW.md 移交态不变 |

## 二、G-42..G-46 复核（b7 登记项）

G-42/G-46 已收口（b7 T16/T17，维持）；G-43/G-44/G-45 本批收口（上表）；无翻案。

## 三、本批执行期新探知

| # | 终态 | 内容 |
|---|---|---|
| G-47 | **已收口·流程** | 子代理通道退化（4 连零工件）→主代理亲自执行模式+纯 edit 单发纪律（捆绑 run_code 校验失败会整体吞 edit）；HANDOFF 批 8 节在册 |
| G-48 | **已收口·T11 裁决** | schema_version 维持 2：本批零 13 表列集变更（approvers.tsv=知识库运行时文件）；升 3 推迟至首个真实列集变更——微版本纪律先例沿用 |
| G-49 | **登记·已知边界** | 链式重放消费 verdict 取自 replay/<id>/最新 json（步内单源），链摘要为包装层——跨进程并发同 EV 链写同目录时序=边界（单人交战口径不触达） |

## 四、移交清单（批次 8 收口后待办，延续）

- G-22 真钥仪式（M13 同批）/10 页人工复核（M10 名录已为其机检底座）/R11 法务/Actions 页面复核——四件真人，不代做。
- 靶场第二战（基线 v2）+扩编 20→50+飞轮喂养——目标后段，主循环继续。

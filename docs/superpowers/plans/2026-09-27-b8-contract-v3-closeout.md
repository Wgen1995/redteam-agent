# 批次 8 实施计划——契约 v3 遗留清账（亲自撰写版）

> 目标：九项遗留+执行期登记逐条收口，契约集中升 v3。基线=848 绿+54 金样面（HEAD 3a4324f）。
> 纪律：TDD 先红后绿/UTF-8+LF/[sys.executable,path]/长文件分段读+git diff 复核/金样零漂移默认/中文 commit/HANDOFF 记账。

## 文件结构图（每文件一职责）
- cli/ledger/write_cmds.py：supersede 铸行+scope_asset 拒收+deferred 复活（既有写面扩展）
- cli/ledger/replay_chain.py（新）：EV 有序多请求序列执行器
- cli/tanyin-replay：--chain 入口
- cli/ledger/graph_cmds.py：悬空 cred 告警（读侧）
- cli/ledger/phases_engine.py：触发器第九类（端口/服务变更）
- cli/ledger/knowledge.py：init 基线缺省携带
- cli/ledger/enforce→install/hooks/simulate.py：Tier2 接线单源
- cli/ledger/report_lint.py：write_all 门内复扫（G-44）
- cli/ledger/install_core.py：uninstall 面
- cli/ledger/exit_codes.py（新）：异常分型单源（env→2）
- contracts/*.md：v3 集中勘误+schema_version=3 迁移注记

## 任务（T1-T12，按依赖序）
### T1 supersede 命令面（M2）
红：tests/test_supersede_b8.py——add-finding 同键 active REJECT 后无命令可铸 dst（现状死路）。
绿：add-finding --supersede=<FD-id> 允许同键新行+旧行 status=superseded+timeline 事件；44 命令面不新增（参数扩展非新命令）。
验证：python3 -m unittest tests.test_supersede_b8；全套回归。

### T2 deferred 复活臂（M3）
红：test_deferred_revive_b8.py——deferred→pending REJECT（现状）+activation 零消费。
绿：add-intent --activate=<INT-id>（或 revive-intent 参数扩展）：deferred→pending+activation=<ts> 落列+事件；budget_share 重算披露。
验证：unittest+trigger-audit 回归。

### T3 scope_asset 悬空拒收（M5 写侧）+图悬空告警（读侧）
红：test_scope_dangling_b8.py——creds --scope-asset=AST-g1-9999 exit 0（现状）；graph-horizon 悬空静默。
绿：写侧 assets 存在性拒收 REJECT；graph_cmds._build 悬空行 stderr 告警（不中断，计数披露 dangling=<n>）。
验证：unittest+graph 三面回归。

### T4 触发器第九类（M6）
红：test_trigger_port_b8.py——端口/服务变更事件后 trigger-audit 不机检。
绿：TRIGGERS.md v3 目录加行+phases_engine trigger_audit ⑤：端口/服务变更 fact/intent 须在册（消费=fact 带 consume 或 --no-consume 标记）。
验证：unittest test_trigger_audit*全套。

### T5 链式多请求重放（M12）
红：test_replay_chain_b8.py——EV 卡多请求序列无执行通道。
绿：replay_chain.py：EV evidence 链 YAML（requests: [有序 raw_request]）逐请求执行+序号落 timeline+任一步非 2xx=env-diff；tanyin-replay --chain=<EV-id>。
验证：unittest+guard 界内链路实测。

### T6 安装卸载面（M15）
红：test_uninstall_b8.py——安装后无清理通道+只增不删混版（SRE 反例残留）。
绿：tanyin-install uninstall：--install-root 必填+install-log 对照删除+幂等（二次 rc=0 树已净）+hook/AGENTS 注入回滚。
验证：两轮 install/uninstall 后 diff 零残留。

### T7 真人复核身份锚（M10）
红：test_approver_anchor_b8.py——approver 任意非空串通过（现状）。
绿：knowledge/client-map.tsv approver 名录列+approve 校验名录成员+执行者 deny-list（log.md 既有执行者 id 集拒绝）。
验证：unittest+HUMAN-REVIEW 流程文档同步。

### T8 Tier2 接线（G-43）
红：test_tier2_simulate_b8.py——hooks/simulate.py 字面比对与 enforce 单源行为分叉（构造归一形差异用例）。
绿：simulate.py 改调 enforce.normalize_cmd/deny_forms 单源；行为等价断言。
验证：unittest+guard 51 例回归。

### T9 write_all 门内复扫（G-44）
红：test_sign_writeall_scan_b8.py——write_all 产物落盘于复扫后（时序断言）。
绿：cmd_sign 序列重排：write_all 落盘→复扫（含 findings.json/sarif/report-*.md）→FAIL 删证。
验证：unittest+test_sign_gates_b7 回归。

### T10 init 基线缺省（G-45）+退出码全仓分型（M1 尾）
红：test_init_baseline_b8.py（init 库无 k1-baseline.tsv 缺省）+test_exit_codes_b8.py（抽 3 处 env 错仍 rc=1）。
绿：init 拷贝 methodology/ 两 TSV；exit_codes.py 分型单源+三处接线（坏 TSV/缺依赖/用法错→2）。
验证：unittest+全套。

### T11 契约 v3 集中勘误
G-4 重启成本定标+G-37 token 系数回写（批 6 登记）+本批 T1-T10 全部新面回注 contracts 01/02a/04/11/13/14/15+schema_version=3 迁移注记+README 索引。
验证：test_knowledge_contract+grep 自验计数。

### T12 收口
b8 台账（G-42..G-46 终态更新+新发现续编）+HANDOFF 快照+出口清单亲跑+push。

## 出口验收清单
1. 全套 unittest 全绿（848+新增）2. 金样 54 面 PASS 零漂移 3. T1-T10 各红→绿证据在册 4. M2/M3/M5/M6/M10/M12/M15/G-43/G-44/G-45 十项终态=收口 5. 契约 v3 勘误一致性 grep 自验 6. uninstall 两轮零残留 7. 链式重放界内实测 8. 树净+禁区零触碰 9. push。

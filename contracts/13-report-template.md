# 13 报告模板章节骨架契约（接口⑯）

> 来源：定稿 §11 批次 0 契约⑯（辅引 §2.2 铁律 5/§0.3 口径 6/§3.4/§4.3-§4.4/§4.7/§4.10-§4.11/§5.2 P5/P5.5/P6.0/§8.4/§8.7/§12 R11，随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口⑯（报告模板章节骨架，中文合规段）的誊录件（定稿 §11 批次 0 行），并按任务要求并入 P5.5 签发门要求（cleanup.md 附报告）。只誊不创：六要素条目为 §11 原文；「辅引依据」列仅为定稿内既有语义的出处标注（非⑯原文）。

## 1 六要素章节骨架（§11 批次 0 契约⑯）

| # | 章节（§11 原文条目） | 辅引依据（定稿内语义出处，非⑯原文） |
|---|---|---|
| 1 | 授权与范围声明 | goals 授权结构化（授权书路径+sha256+签署方+有效窗口，§4.3）；scope 白名单含 amendments 修订史（§4.4；修订史进报告守门声明，§5.2 P3 events） |
| 2 | 方法学映射（WSTG↔章节） | vuln_class 从 shared/VOCAB.md（WSTG v4.2 全集，版本化）钉死；闭合率按 WSTG 全集报告（§4.10） |
| 3 | 覆盖度与局限性 | 矩阵空格必须消灭或走 budget-exhausted 披露；终态门禁（§2.1 铁律 3/§5.2 P5 exit ledger-terminal-gate） |
| 4 | 技术×业务风险分级 | 两维评级 confidence（C1/C2/C3/➖🛑）× impact（高/中/低）（§2.1 铁律 4/§4.7）；business_context＝P0 业务问卷摘要（P2 矩阵生成与 biz 标记输入，§4.3） |
| 5 | 整改优先级与复测建议 | FD 卡片「修复建议叙述」（LLM 撰写；进入报告的部分由聚合器裁剪引用，§4.11）；POC 独立重放门（§5.2 P4） |
| 6 | 等保占位段 | §12 R11：免责条款/等保占位段合规表述——批次 6 出口前人工法务过审一次；模板版本化留痕 |

## 2 生成方式与正文约束（§5.2 P5）

- tanyin-report 聚合器从 13 表确定性重建正文（模板＋账本数据，零 LLM 方差；**LLM 仅写执行摘要与修复建议叙述段，须引用 finding ID**）。
- 产物 report-draft.md，附「**范围外观察**」附录：out_of_scope facts 列示供客户扩授权决策（接 §5.4 边界生长闭环）。
- P5 exit 断言（3 条）：`ledger-terminal-gate`（矩阵无空格 | degraded 披露清单完备）；`tanyin-report --lint`（schema lint＋脱敏检查 PASS）；`ledger-redact-scan --target report/`（占位符零泄漏）。

## 3 固定披露段（铁律 5，§2.2/§0.3 口径 6）

- **报告守门声明固定段落**：本交战实际启用的执法层清单、每层拦截事实计数（deny-list 拦截数／hook 阻断数／egress 拒绝数）、canary 结果（3 项计数）。
- 数据出自 goals.guard_tier＋timeline（铁律 5：声明可由账本确定性重建，可实现可验证；档位事实必须披露，禁止以低档冒充高档）。
- budget-exhausted／degraded 首节强制披露（§8.7/§5.2 back_edges）：未闭合格清单＋未跑 intent 清单＋闭合率＋免责注明中期报告（诚实终止，不是事故，§2.1 铁律 3）。

## 4 P5.5 签发门要求（§5.2）

- duty：人审→ledger-approve（command_hash 绑定聚合产物文件哈希）→**report-signed.md**。
- exit 断言：`ledger-approve --verify-signoff` → approvals 存在对应 approved 行。
- **未签发报告禁止导出**（cli 层：导出命令校验签发行）。
- 交付前终检（§8.4 关卡 4，P5.5 前置）：ledger-redact-scan 对报告全文占位符扫描——任一真值残留＝阻断导出。

## 5 cleanup.md 附报告（P6.0 清理门，§5.2）

- ledger-cleanup-checklist 从 timeline 提取全部外部副作用写操作（revert_cmd 非空行）→逆序执行 revert_cmd；纯账本状态行无需回滚＋结果验证→全核销或人工豁免（approvals 落账）→**cleanup.md 清理声明附报告**。
- exit 断言：`ledger-cleanup-checklist --verify` → 全部 reverted 或豁免行齐备。
- 落位：交战区 `engagements/<goal-id>/cleanup.md`（§3.4 目录树）。

## 6 模板治理（§11 批次 6/§12 R11）

- 批次 6 出口：报告模板 lint＋法务过审（R11：批次 6 出口前人工法务过审一次；模板版本化留痕；各客户法务差异需交付时二次确认）。

## 探知项（待仲裁）

无（未发现定稿内部两处说法冲突）。

## 自验

命令实跑证据（D＝定稿路径，本文件＝contracts/13-report-template.md）：

- 六要素：`grep -o '授权与范围声明/方法学映射（WSTG↔章节）/覆盖度与局限性/技术×业务风险分级/整改优先级与复测建议/等保占位段' $D | head -1 | tr '/' '\n' | grep -c .` → **6**；本文件 §1 表 `awk '/^\| 1 \| 授权与范围声明/,/^\| 6 \| 等保占位段/' 本文件 | grep -c '^| '` → **6**（六要素齐）。
- P5 exit 断言：`awk '/^  P5:/,/^  P5.5:/' $D | grep -c 'cmd:'` → **3**（terminal-gate/report --lint/redact-scan）＝本文件 §2 所列 3 条。
- 守门声明计数项＝**3**（执法层清单/每层拦截计数/canary 结果），拦截计数细分 3（deny-list 拦截数/hook 阻断数/egress 拒绝数）（§2.2）。
- P5.5 签发门：`grep -c 'verify-signoff' $D` → **1** 条 exit 断言；未签发禁止导出＋交付前终检（§8.4 关卡 4）并入 §4。
- cleanup.md 附报告：P6.0 duty 原文「cleanup.md 清理声明附报告」＋exit 断言 **1** 条（--verify）（§5）。
- 探知项＝**0**。

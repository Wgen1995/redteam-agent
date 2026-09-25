# 契约 15 · evals 指标集 schema（批次 6 冻结；微版本勘误通道同 01-14）

> contract: 15 / version: 1 / 2026-09-24 · 来源：docs/superpowers/plans/2026-09-24-b6-evals-install-delivery.md Task 1（裁决 A）＋docs/design/2026-09-21-tanyin-v2-design.md §9.2 表逐行
> 微版本通道：勘误只加不改（历史行就地注记保留原文），语义冲突回计划意图裁决并记 docs/HANDOFF.md Ruling；机器面单源=cli/ledger/evals_schema.py＋tests/evals/metrics-v1.json。

## 1 指标条目 schema（metrics-v1.json 顶层 {format_version:1, metrics:[...], suites:{...}}）

必填字段：id(M\d\d-<kebab>) / layer(L1|L2|L3) / gate(hard|warn) /
kind(equality|threshold|zero-tolerance|checklist) / title /
baseline:{value: number|"collect-first"|checklist 定值字面量, frozen_at: iso8601|null} /
source:{runner: <注册名>, args: [...]} / desc

违例=缺字段/枚举外/id 重复/runner 未注册时 run_suite 阶段 ENV-SKIP（schema 层不绑运行时）。
checklist 定值字面量=该指标基线为固定验收值（如 "PASS"/"两侧全配对"），非数值阈值。

## 2 退出码（裁决 A；契约 09 面冻结 0/1/2 不新增）

0=本套全部硬门 PASS；1=任一硬门 FAIL（零容忍触碰/阈值回退/checklist 假）；2=存在 ENV-SKIP
且无硬门 FAIL 且无 PASS（全 skip 才 2；部分 skip+有 PASS=0 并在报告 counts 披露）。
warn 门 FAIL 不影响退出码，落 counts.warn_fail。
VulnClaw 第 3 态「仅候选」不新增退出码，落 metrics JSON counts.candidates 字段供人读+签发门披露（裁决 A）。

## 3 指标 v1 清单（12 项；来源=设计 §9.2 表逐行）

- M01-golden-byte L1 hard equality runner=golden:tests/run_golden.py 基线=collect-first(首跑入册)
  〔勘误 R-T1-1：原计划 unittest:tests.run_golden——tests/run_golden.py 为脚本非 unittest 模块，
  `-m unittest tests.run_golden` 加载 0 例=空绿假 PASS；fail-closed 改 golden runner 子进程实跑，
  rc!=0 即 FAIL，与本仓金样门「缺金样=FAIL 不落盘」同源〕
- M02-poc-replay-rate L2 hard threshold 基线=collect-first（C1 100%可重放或已降级处置；replay-summary 三态分布）
- M03-canary-zero L2 hard zero-tolerance ×4 档 基线=0
- M04-kill9-fidelity L2 hard checklist runner=unittest:tests.test_kill9_fidelity 基线=PASS
- M05-token-efficiency L2 warn→基线 v1 后升 hard threshold runner=token-usage 基线=collect-first（裁决 G）
- M06-injection-redteam L2 hard zero-tolerance runner=unittest:tests.test_redact_injection 基线=0
- M07-negative-cases L2 hard equality runner=unittest:tests.test_negative_matrix+tests.test_dryrun_p0p2 基线=全部必须失败
- M08-weak-model-protocol L2 hard checklist runner=unittest:tests.test_weak_model_protocol 基线=可检测
- M09-authz-recall L2 hard threshold runner=range-recall 基线=collect-first（首跑=基线 v1，裁决 I）
- M10-report-lint-redact L2 hard equality runner=report-scan 基线=零泄漏+lint PASS
- M11-switch-matrix L2 hard checklist runner=unittest:tests.test_switch_matrix 基线=铁律6不可裁剪清单不破
- M12-dual-anchor L2 hard checklist runner=dual-anchor 基线=两侧全配对（裁决 E）

## 4 suites 分组

static=[M01,M04,M06,M07,M08,M10,M11,M12]；dynamic=[M02,M03,M05,M09]；all=static+dynamic；
l3=[]（v1 占位空组——勘误 R-T1-2：L3 对齐 runner=manual 随 Task 3 交付，正式 L3 指标条目
随对齐数据入册，不阻塞 CI；空组不引用不存在条目，run_suite 恒全 PASS 空passthrough）。

## 5 报告工件

run 落 `<goal-dir>/evals-report-<suite>.json`：{format_version:1, suite, started_at(显式 --timestamp),
results:[{id,status(PASS|FAIL|WARN-FAIL|ENV-SKIP),actual,baseline}], counts:{pass,fail,warn_fail,env_skip,candidates}, exit}
counts.candidates=VulnClaw 第 3 态落点（仅候选数，不入退出码，裁决 A）。
list 子命令=机读指标清单人读投影；report 子命令骨架期与 run 同面（计划代码即规格，
R-T1-4；人读渲染面归批次 6 Task 12 tanyin-report）。

# 探隐开发账本 · HANDOFF（追加式，不删行；每笔交付后记账）

> 目的：会话会死，账本不死——跨会话/跨代理的唯一事实源。接手者读本文件即可零上下文续作。

## 当前状态快照（2026-09-24）
- 批次 0 契约冻结：✅ contracts-v2（13 表/41 命令/边词汇/四层档位）
- 批次 1 账本命令箱+金样：✅（金样字节级回归绿；细节待独立审计确认）
- 批次 2 门禁层：基本收官——enforce 单源化(500ae44)+Windows 兼容+CI 双平台绿(730d743/70826a5)；181/181 测试绿
- 批次 3 总控 skill+图谱循环：**计划撰写中**（子代理 c1308136，writing-plans 规范）
- 批次 0/1/2 完成度独立审计：**进行中**（子代理 865488fb，出口条款逐条实测）
- 全景图 v2：定稿（0fbab87 模拟运行；SPEC 三层契约在 docs/design/imported/TanYin/panorama/SPEC.md）
- 工程纪律：UTF-8+LF 红线/py -3 等价/双平台 CI（.github/workflows/ci.yml）

## 交战区指针
- 设计定稿：docs/design/2026-09-21-tanyin-v2-design.md（§2 铁律/§5 循环/§11 批次表）
- 契约：contracts/；CLI：cli/；测试：tests/（unittest+金样 G-g1，入口一律 [sys.executable, path]）
- 计划：docs/superpowers/plans/（2026-09-23-batch1-ledger-cli.md 已有；b3 计划在写）

## 开发流水（追加，一行一笔：日期｜代理｜动作｜证据）
2026-09-24｜总控（本会话）｜批次2 对账入库：SECW-3 执法单源化 181 测试全绿｜500ae44
2026-09-24｜子代理 df8e7216｜Windows 兼容审计+修复+双平台 CI 四 job 绿｜730d743,70826a5
2026-09-24｜子代理 6c72220c｜全景图 v2：图谱+知识库簇+生命周期+引擎层+哲学锚点+断点四步+口径13+模拟运行｜9f6c388..0fbab87（8 笔）
2026-09-24｜总控（本会话）｜建立本账本（补记：此前 panorama 马拉松期间账本纪律失守，本行起恢复）｜本文件
2026-09-24｜子代理（TDD）｜批次2 三 Critical 执法洞修复：exclude/oob 三集语义+egress 单源化、inject 同门链、stderr 双流脱敏；顺手 Important：deny-list 数据化(shared/DENYLIST.md)、主机提取强化、canary 三形态；228 测试全绿+金样零漂移｜a5b4b17
2026-09-24｜子代理 T1｜批次3 T1：phases.yaml 契约誊录+受限 YAML 子集解析器（stdlib 零依赖，fail-closed；TDD 先红后绿 6 新用例，全套 234 绿+金样 PASS）｜271e814
2026-09-24｜子代理 T2｜批次3 T2：phases schema 校验器+九门断言命令存在性（all_commands 41 基名单源）+tanyin-phases 入口(+.cmd)；phases-validate 金样接入 run_golden 既有机制；G-1 契约09/README 勘误 10→11；TDD 先红后绿 7 新用例，全套 241 绿+金样 PASS（21读+20写+1phases）｜2350924

## 探知项（实现期发现，回写设计）
- （待批次3计划/审计子代理回报后登记）

## 2026-09-24 批次 0/1/2 独立审计入账（审计员 865488fb，只读实测）
- 批次 0：完成（16/16 接口实体在；Minor×2：冻结后勘误未走版本通道/附录 A 落位与设计文字不符）
- 批次 1：基本完成（41/41 实现+金样双锁定+负向 83 处 REJECT；Important：金样实为归一化+行排序比对非严格字节级、金样未进 CI）
- 批次 2：不达出口——三 Critical 实测洞：exclude 语义缺失（被排除主机 Tier1/Tier2 放行，与 egress compile 解释矛盾）；inject 通道零执法（带凭据执行绕过 deny-list/scope/取票）；stderr 不脱敏（vault 真值回泄）。Important×5：Tier3 代理本体缺/deny-list 仅 7 条硬编码/主机提取盲区/canary 探测形态单一/金样未进 CI
- 处置：#1#2#3+#5#6#8 修复后才开工批次 3；#4 代理本体建议裁到批次 6 并守门声明披露（待用户确认）；#7 金样严格化+进 CI 随后并行；#9-#12 顺手清
- 探知项登记：vault XOR 静态密钥流无 nonce（批次 4/6 前定案）；withheld 降级未实现；INFRA 白名单硬编码应随 tools.lock

## 2026-09-24 批次 3 实施计划入账（撰写 c1308136）
- 计划：docs/superpowers/plans/2026-09-24-b3-master-skill-loop-restart.md（2757 行，13 个 TDD 任务/65 步/29 验证命令/11 条出口验收）｜commit 1761e17
- 接口缺口探知项 G-1..G-11 已在计划内登记；关键四个：G-1 需第 11 工具 tanyin-phases（契约 09 增补）；G-2 新资产子矩阵行铸造断链（P3 生长通路①，批次 4 前须裁决）；G-3/G-4 重启速率上限与 token 成本口径无契约源（10min/2000 暂代）；G-6/G-10 state.md v2 十键与 checkpoint 新参数需回注契约
- 执行前置：批次 2 三 Critical 修复（ee43438d 进行中）落地后才执行本计划

## 2026-09-24 批次 3 开工（executing via subagent-driven-development）
- Ruling: Tier3 代理本体裁到批次 6+守门声明披露 — 用户开blanket批准按建议走 — 代价：批次 2 范围注记需同步，若错可回补
- Ruling: G-1 批准契约 09 增补第 11 工具 tanyin-phases — 确定性校验器符合铁律 7 — 代价：契约版本通道走微版本
- Ruling: G-2 子矩阵行铸造路径在 T2 实现时裁决并记账 — 不阻塞 — 代价：可能返工 matrix 白名单
- 执行结构：T1-T13 每任务新子代理+TDD+全量回归；里程碑 T4/T8/T13 加代码评审

## 2026-09-24 批次 3 T2 裁决（实现者记）
- Ruling（计划↔实现偏差①）：计划 T2 Step3 的 all_commands() 参考实现按字面会剔掉四个原生名带 ledger- 前缀的校验命令（ledger-scope-coverage/tree-check/replay-summary/terminal-gate），与计划自身 Interfaces（41 基名）及 test_repo_yaml_valid 预期冲突——按计划意图裁决：只剔「有无前缀孪生键的双前缀别名」，原生带前缀四命令计入基名，实测恰 41 名（新增 test_all_commands_face_41 钉死防漂移）。
- Ruling（计划↔实现偏差②）：phases.yaml 断言首词统一带 ledger- 前缀而 known=基名集——validate_phases 存在性判定按 PROTOCOL.md §1「双前缀注册均可查」语义归一（先试原词，再试剥前缀词）。
- Ruling（金样机制）：计划 T2 Step5 的 phases-validate.norm 为孤立基线文件；按派遣指令+金样零漂移纪律接入 run_golden 既有机制（双跑确定性+缺失自动建档+漂移即 FAIL）——首跑 INIT 建档、次跑锁定 PASS。
- Ruling（G-2 建议，按预批裁决记入；不实现——批次 4 范围）：T2 未触碰 matrix-set/matrix-init 白名单语义（validate 只做断言命令存在性检查，不改写侧拒收）；裁决建议=维持计划探知项 G-2 原案：matrix-set 放行 reason 前缀 submatrix: 的新键行（新表面×词表全集），批次 4 前落地。

# 01 工程开发专家（代码质量）深度分析（2026-10-10 九维专家会诊）

> 只读分析；证据带路径行号。

## 现状强项
1. 退出码 0/1/2 分域是全仓真实纪律（write_cmds._wrap 统一映射；phases_engine.run_gate rc==2→ENV-HALT、rc!=0→gate-fail；tests/test_exit_codes_b8.py 钉测）。
2. 存储层敌防成体系：tmp+fsync+os.replace 原子写（core.py:63-83）；timeline 哈希链+保留词引擎侧单源铸造；timeline 铸造单源化（timeline.py，ts 必填）。
3. 写并发治理单源派生+论证：goal_lock（flock/msvcrt）registry 分发单点；写命令集从 HANDLERS 派生禁手抄（registry.py:19-39）；filelock.py docstring 死锁论证。
4. 测试工程远超单人水位：143 测试文件全 unittest 化；CI 双平台矩阵（ci.yml ubuntu+windows×py3.11/3.12）；sim_watchdog.sh 无 LLM 全链仿真；22 个金样钉测；全仓 TODO/FIXME 仅 4 处。
5. 编排/计算分离：watchdog/gateloop_core 纯函数核零依赖；lock_v2.probe_stale 三态保守语义教科书级（lock_v2.py:88-102）。

## 关键缺口（按严重度）
1. 【最重·b26 正踩】gateloop 门轮询=账本写放大器：每 tick（活跃期 1s）跑 gate_pass 子进程→断言失败 _append_event 落 gate-fail→goal_lock→整表重写。P3 未收敛前=每秒一次冷启动+13 表全量加载+落链+全文件重写+与战士抢锁。后果：timeline 噪声灌满、O(n²) 写放大、锁竞争。业界：廉价预检（mtime/行数）、失败事件去重（首落+计数）、反转控制由战士完工主动打门。【父代理活体验证：b26 timeline 1273 行中 gate-fail 623 行=49% 噪声，警告完全命中】
2. 读路径无锁+多表 commit 非原子=撕裂快照：query/评分器裸读，Ctx.commit 逐表写；单表原子≠快照原子。业界：epoch/版本戳文件，读者前后校验重读。
3. 双循环重复+importlib 连字符 hack：SourceFileLoader 载 tanyin-runner（模块级代码全执行、无字节码缓存、静态工具不可见）；两主循环同构手写且已漂移（runner GIVEUP 也 rc=0，gateloop 返 1）。该抽 cli/ledger/runtime.py+骨架参数化。
4. 无 lint/覆盖率/类型静态门；write_cmds 1379 行/phases_engine 1236 行/knowledge.py 1332 行巨型模块。
5. schema 只是列名清单，无集中值域校验器（枚举/引用/时间戳规则散在 handler）——无表级 lint 对外部写入校验。
6. 性能边界：每命令全量加载+整表重写；timeline 本质 append-only 却整表重写（链式哈希天然支持 O(1) 尾追加）。SQLite 是零依赖标准替代；更小改法=timeline 行级 append+fsync。

## 可执行建议
| 建议 | 位置 | 收益 | 量 |
|---|---|---|---|
| gate-fail 节流+gateloop 预检 | phases_engine:437-440+gateloop gate_pass | 消每秒写放大保信噪比 | M |
| timeline O(1) 追加通道 | core.write_tsv 分流 | 写放大 O(n)→O(1) | S-M |
| 抽 ledger/runtime.py | 新模块+两入口改 import | 删 hack 止漂移 | S |
| 读侧 epoch 文件 | commit 尾+load 校验 | 封撕裂快照 | M |
| CI 加 ruff+coverage | ci.yml | 静态门起步 | S |
| ledger-lint-all 表级校验 | 新只读面 | 外部写入可验 | M |
| tests 分包+docs 分 current/history | 目录重组 | 导航成本降 | M |

## 对标
PentestGPT：账本审计链+门禁+回归飞轮工程化反超一个量级，但无 Web UI。git：timeline=定制 git-log，单写者+flock 回避并发，gateloop 高频写逼近边界。SQLite：TSV 换 AI 直读是合理 trade-off 但无书面成本边界。BDD：phases.yaml≈渗透版可执行规格。

## 总评
用 Unix 黄金年代纪律武装 AI 战士的高完成度单人工程，账本-门禁-回归飞轮核心链路质量超过多数团队产品；真正的债集中在 gateloop 写放大、读侧无锁、双驱动重复三处——都是"实验赢了要转正"前必须还的工程税。

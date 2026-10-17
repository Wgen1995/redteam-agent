# 任务生命周期状态机设计 v1(2026-10-18 定稿)
缘起: 用户质询「任务生命周期全过程设计了吗」。脊椎已在代码(迁移=账本事件),本档把骨架正式化。
基线: ARTEX 手册:184-209(11字段/五操作/批量/归档冷存储/删除范围)+CSAI 手册:116-120(cron/并发/batch族)+ZhuLong 三态终审。

## 状态集(12)
DRAFT 草稿 → AUTH-PENDING 待授权(八问缺项) → ARMED 已授权待执行 → RUNNING 执行中 ⟷ PAUSED 暂停
→ CONVERGED 已收敛(四条件) → RETESTING 复测中 → REPORT-PENDING 待报告 → SIGN-PENDING 待签发
→ SIGNED 已签发(双签) → CLEANING 清理中 → ARCHIVED 已归档(终态)
异常终态: ABORTED 已中止(急停/预算顶/链断) / FAILED 环境失败(rc2 类,可修复回 ARMED)

## 迁移与门卫(每次迁移=timeline 一行;门不过=拒,拒绝也入账)
| 迁移 | 门卫(前置条件) |
|---|---|
| →ARMED | 八问全真(原件+sha256 真校验链) |
| ARMED→RUNNING | battle_registry admit: 端口领用(保留口禁领)+预算帽仲裁+单runner flock |
| RUNNING→PAUSED/→RUNNING | 意图租约挂起/复活(双抢互斥已在) |
| RUNNING→CONVERGED | 收敛四条件(覆盖率/无新发现/预算余/时限) |
| CONVERGED→RETESTING | verified 项≥1 |
| RETESTING→REPORT-PENDING | 重放全记录入链 |
| REPORT-PENDING→SIGN-PENDING | 报告确定性渲染通过(同输入同输出钉) |
| SIGN-PENDING→SIGNED | **双人签发**(P5.5 永久人工) |
| SIGNED→CLEANING | 签发版本锁定 |
| CLEANING→ARCHIVED | **清理核销 100%+归档 manifest(sha256 全录)**;还原=manifest 校验+依赖检查 |
| 任意→ABORTED | 急停(二次确认)/预算硬顶/断链(verify-chain fail=拒结算,先抢修) |

## 超越点(对五家)
1. **迁移全审计**: 状态史=账本史,可回放任意时刻(五家状态在 DB/内存,改库即改史/重启即丢)
2. **结算门挂链完整性**: 链断=拒结算——ARTEX/CSAI 无此概念
3. **归档带 manifest+还原校验**: 对齐并超 ARTEX B17(它无签名清单)
4. **三态终审+复测常驻**: 吸收 ZhuLong 终审+我们独有机械重放

## 吸收件(已排波次收口)
批量(暂停/归档/分类)=A:B14 W6;列表五操作=B13 W6;新建表单字段扩充=B15(不抄心跳/任务级拦截——范围单源律);cron=CSAI G8;归档冷存储=A:G9 W6;删除范围选项=G9 扩。
## 实施量
states 模块+迁移门卫+批量/cron/归档挂接 ≈ 900 行(并入 W6 界面线的后端配套),性能钉随并发浸泡票。

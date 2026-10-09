# 09 运维可观测性专家（SRE）深度分析（2026-10-10 九维专家会诊）

> 勘误采纳：b24 断网证据在 RT-0022（RT-0021 是跨运行时 A/B 复盘）。

## 现状强项
1. 状态全外置=崩溃恢复语义清晰：战毕判据 gate-exit:P4 非 rc=0；kill-9 保真度专门 eval；RT-0022 b24 三中断零账损——"账本在盘"真实故障下兑现。
2. 看门狗计算核纯函数化分级击杀：stall_grade/backoff_delay/read_directive/next_tick；12 单测+无 LLM 全链仿真双场景；进程组击杀防孤儿。
3. 事件流骨架实战功在案：runner.tsv 十类事件；battle-24 完整记录 STALL 击杀（网络断流）与三次人工 BOOT；battle.py watch 复用做存活探测。
4. 诚实复盘文化：假完成/NameError/b26 五度失明全入库，修复有 git 链。
5. gateloop 臂B 天然产出每门时长 SLI（GATE-BEGIN/PASS+per-gate 分钟数）——臂A 没有。

## 关键缺口
1. 【致命】驱动自身无人兜底：runner 裸前台进程（grep caffeinate/launchd/supervisord 零命中）；battle-24 实证 EXIT 后本应 RESTART 的位置直接跟新 BOOT——pre-b10 relaunch NameError 使 runner 自杀只能人肉三度点火；b10 修了虫但"runner 崩了谁拉起"结构性答案仍是没人。业界：launchd KeepAlive/supervisord/dead-man's switch（healthchecks.io 模式）。
2. 【高】预算 2M;50000;40 是申报制非执法制：三个驱动器中 budget 零引用（grep 实证）；budget.tsv 靠战士自报（b24 全战仅 1 行收尾补记 180k）；budgetctl-reject 事件=0；战中超支无人杀进程——真实杀手是 API 欠费→STALL 循环→GIVEUP，兜底极慢且每 restart 重读全书烧更多 token。业界：proxy 层计量硬顶/runner 周期快照超限走降级收尾。
3. 【高】心跳=fsize/行数轮询双误：假阳性=报错刷屏永远"活着"；假阴性=长静默工具被误杀。业界：语义进度（当前 phase/最近事件墙钟/工具调用序号）。
4. 【高】SLO 不可算：账本场景钟（每门真实耗时从账本永远算不出）；runner.tsv 唯一墙钟但无每门标记（臂A）；battles 连 index.tsv 都没有。
5. 【中】过夜多战缺四件套：调度/告警（GIVEUP 只写文件无通知）/防睡眠（合盖全场冻结醒后误杀无辜战士）/靶场监测（战中 Docker 死→空转烧 token 无熔断）。
6. 【中】b10 四件套从未上过真实战场：battle.py launch 不传 --directive-file/--soft-stall-min（b23/24/25 BOOT 行旧格式证实）——b26 才是首验。产物无 retention；opencode-run.log 无上限追加。

## 可执行建议
| 建议 | 位置 | 收益 | 量 |
|---|---|---|---|
| PROGRESS 带 last_gate+BOOT/DONE 追加 index.tsv | runner+settle | 战完成率/MTTR/每门耗时立即可算 | S |
| launchd KeepAlive 或 caffeinate -i 包 launch | install/RUNBOOK | runner 崩溃自拉+合盖不冻结 | S |
| 战中 budget 快照超限→DIRECTIVE 注入降级收尾 | runner 主循环 | 超支战获得确定性终态 | M |
| GIVEUP/STALL/DONE 触发 osascript/Bark 通知 | log_event 挂钩 | 过夜出事手机知道 | S-M |
| active 加第三信号 LOGONLY-ALIVE（日志活账本不动） | 心跳判据 | 堵刷屏假阳性 | M |
| settle 后 zstd 归档+index 驱动保留期 | battle.py archive | 生命周期闭环 | L |

## 对标
launchd/systemd/supervisord（工业最小标准——探隐 runner 裸跑）；healthchecks.io dead-man's switch（正对驱动自身盲区）；LiteLLM Proxy 预算硬顶（计量制 vs 申报制）；Google SRE SLI/SLO（gateloop per_gate 分钟数是天然 SLI，缺聚合面）。

## 总评
对"战士"的监护已是单人项目高水位（分级击杀/退避/指令通道/账本外置，b24 实战验证断网存活），但对"驱动自身、预算、主机环境（睡眠/Docker/告警）"三个面仍裸奔——b10 修的 NameError 正是单层看门狗的结构性症状：下一只 runner 虫，还得靠人早上起来发现。

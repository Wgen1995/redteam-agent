# hosts/adapter-opencode-posix.md —— opencode × macOS/Linux/WSL/Git Bash 适配

> 设计 §15 宿主适配（B-063/B-223/D-098/D-099/D-100/D-101/D-116）。命令载体=SKILL.md + phases/*.md 的 bash 块（平台分支见 SKILL.md）。

> 设计 §15 宿主适配（B-063/B-223/D-098/D-099/D-100/D-101/D-116）。命令载体=SKILL.md + phases/*.md 的 bash 块（平台分支见 SKILL.md）。

## 如何驱动（B-063：每步命令）

1. **发起**：用户说"使用 GenSift 审计 /abs/src"。编排器逐字执行 SKILL.md 发起 bash 块（占位符先代入）——产出 `SESSION=/…/gensift-<时间戳>`、`env.sh`、STATE=running。
2. **每命令块**：从 phases/*.md 逐字复制 bash 块执行；首行恒为 `. "$S/env.sh"`（$S=SESSION 字面路径）。含占位符的块（2b/2e-env/2f-env/3e-env/A4）先按块首说明代入 `{card_id}`/`{cand_id}`/`{FT-id}`/处置六占位。
3. **派子代理**：每卡一条 Task 消息并行派发（general-purpose，可写文件）；prompt=引用件内模板逐字+变量块代入；模板首行含"禁止调用 skill/Skill 工具"。
4. **验收**：只查分片格式与账本行——不读源码判洞（元规则：无命令的步骤=技能缺陷，终止报告）。
5. **权限/目录**：`external_directory` 对源码根/会话目录/技能目录三处放行；`doom_loop` 对主循环每轮重复形态命令设 allow（README 宿主配置节 opencode 小节）；bash 工具按 opencode 文档指定执行器（默认 PowerShell 会语法错——配 Git Bash，或改走 adapter-opencode-windows 的 pwsh 路径）。

## 三重完成检测（D-098）

| 层 | 机制 | 本宿主落法 |
|---|---|---|
| ① | 宿主 CLI 事件流完成标志 | opencode 子代理工具返回即事件流信号。**opencode 无原生 Stop hook**——"宿主收工核对"层缺位，靠 SKILL.md 主循环账本纪律（step0 前置检查+完成判定）兜底，B-065 已在 README 诚实说明；看门狗/墙钟因此在本宿主上调为**主**完成检测而非冗余层 |
| ② | idle 看门狗（不依赖对方配合） | `bash hosts/reaper.sh watch <session> <宿主进程PID> <idle_s> <wall_s>`——活性信号=会话目录文件 mtime（账本/分片在写=在干活），静默超阈值 kill 进程组 |
| ③ | 墙钟硬超时 | 同上一命令的第 5 参；超时 kill 进程组并留 watchdog 日志行 |

## idle 阈值校准记录（D-099：按最慢合法单元校准）

- **最慢合法单元**＝单卡五步分析（一个子代理：信封+读码+写分片）。实测口径（phase0 0.8 常量，README 首次运行检查单）：下界 90s、上界 900s（大文件多跳五步追踪）。
- **推导**：idle 阈值 = 3 × P95(最慢合法单元) ≈ 3 × 900s = **2700s（默认）**；墙钟 = 千文件级过夜口径 = **14400s（默认）**。
- **测量局限**：①900s 上界来自回放观察非全分布采样；②宿主侧模型排队时子代理迟迟不启动、会话目录可静默超 2700s——看门狗会把"排队"误判为死锁而 kill。误杀后果有限（断点续跑幂等，A-049/3e 去重合并），但重跑有成本；长队列环境建议 idle_s 调至 2×。
- **黄金实测参考**（2026-08-25，dvpwa）：单枚举块 1-3s；58 块 bash+ps 双跑全程 2-3 分钟——机械块远快于子代理单元，看门狗阈值由子代理单元主导是正确口径。

## 如何安全终止（D-100/D-101）

- **正常停**：让编排器跑到终态（STATE=done、EXIT_CODE 落盘）。
- **人工中断**：直接关宿主即可——状态全在盘；本宿主无 Stop hook 兜底，未终态会话保持 STATE=running，下次同源码发起被断点续跑逻辑复用（SKILL.md 发起块判定"未完成且同 SRC"）；如需立即标记中断，手工 `echo interrupted > $S/STATE; echo 2 > $S/EXIT_CODE`。
- **孤儿收尸**：`bash hosts/reaper.sh reap <session> [--all]`——清档注册表（audit/host-children.tsv）内死条目；`--all` 连活条目一并进程组 kill（TERM→2s→KILL）。长跑包装脚本建议：
  ```bash
  bash hosts/reaper.sh register "$S" $$ "orchestrator"
  trap 'bash hosts/reaper.sh reap "$S" --all; bash hosts/reaper.sh unregister "$S" $$' EXIT INT TERM
  ```
- **注册表加锁**：audit/reaper.lock（mkdir 原子锁），register/unregister/watch/reap 全部持锁读写，防并发收尸/登记互踩。

## T2/T3 执行档沙箱边界（D-116）

- T1（静态读码）无需沙箱。**T2/T3 仅在发起参数 `runtime_verification=allowed` 时解锁**（占用"至多一次人工交互"名额，A-016），且：
  - Claude Code 的 Bash 工具在宿主权限模型内执行——T2/T3 的动态验证命令继承**当前用户全权限**，本技能不自带沙箱；边界=审计目标树只读（I17 写边界实测）+ 产物只写会话目录。需要更强隔离时由操作者在宿主层先包沙箱（容器/沙箱用户）再发起，本技能不假设、不代管。
  - 宿主权限模型差异声明：opencode/Claude Code 的放行粒度不同（README 宿主配置节）——跨宿主复现 T2/T3 结果前先核对两侧的命令放行面，未放行的命令会被权限层拦下而不是静默降级。

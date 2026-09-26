# install/hooks · dsh 宿主 hook 模板（批次 6 T8 计划面；评审收尾 I-1 落库真挂载）

- 宿主：dsh（hook_mechanism=true；挂载点=会话命令策略层+bash 沙箱档位，
  AGENTS.md 常驻集注入 guard 调用约定——契约 12 §2 宿主矩阵行）。
- 判定语义单源：cli/ledger/enforce.py（deny-list 比对+scope 界外解析，与 Tier 1
  guard、hooks/simulate.py 同源）；fail-closed——阻断=非零退出码，拦截器自身
  故障亦非零（宁误拦不放过）。
- 安装器 step4 将本模板挂载至 `<install_root>/hooks/dsh.md`（幂等覆盖）；
  timeline 写入一律经 tanyin-ledger（单写者纪律）。

## 生命周期事件 → tanyin CLI 调用示例（POSIX 形；Windows 用 py -3 同参）

| 生命周期事件 | 动作 | 调用示例 |
|---|---|---|
| 会话开始（goal/scope 在账后） | 界外基线就绪确认 | `python3 cli/tanyin-ledger scope-check --goal-dir D` |
| 命令执行前（命令策略层回调） | 机械门链判定（deny-list→scope→取票） | `python3 cli/tanyin-guard exec --goal-dir D -- <命令...>`（rc 0=放行；rc 1=阻断并 REJECT 行在账） |
| 命令被阻断时（on-block） | hook-block 事件落账 | `python3 cli/tanyin-ledger append-timeline --goal-dir D --event="hook-block host=dsh deny=<命中项>" --timestamp=<ISO8601>` |
| 会话结束 | 链完整核验+拦截计数供守门声明 | `python3 cli/tanyin-ledger verify-chain --goal-dir D` |

## 占位说明（如实披露）

- 本模板=「生命周期事件→调用约定」的装载说明，不是可执行拦截器：dsh 宿主原生
  命令策略层回调的注册接线须在真宿主实测时落地；判定语义已由 tanyin-guard 单源
  冻结，接线只做事件桥接，不改门链。
- 实测回传时点（台账 G-38）：dsh=本仓可实测面（安装两轮幂等+模板在位机检+全套
  单测即 dsh 侧验证）；opencode/codex=执行期 headless/guided 通道回传
  （tanyin-selfcheck --host <name> --guided 第 4 步 probe_results 模板贴回）后
  升档；walcode/CodeBuddy 无 hook 机制=Tier 1+披露（安装日志行）。
- 时间戳纪律：全部落账命令显式传 `--timestamp`（禁墙钟入账）。

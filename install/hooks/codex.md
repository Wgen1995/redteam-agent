# install/hooks · codex 宿主 hook 模板（批次 6 T8 计划面；评审收尾 I-1 落库真挂载）

- 宿主：codex（hook_mechanism=true；挂载点=其 hook/权限机制探测挂载；无原生 API
  则降 Tier 1+披露（§10.3）——hooks/README Tier 2 差异行）。
- 判定语义单源：cli/ledger/enforce.py（deny-list 比对+scope 界外解析，与 Tier 1
  guard、hooks/simulate.py 同源）；fail-closed——阻断=非零退出码，拦截器自身
  故障亦非零（宁误拦不放过）。
- 安装器 step4 将本模板挂载至 `<install_root>/hooks/codex.md`（幂等覆盖）；
  timeline 写入一律经 tanyin-ledger（单写者纪律）。

## 生命周期事件 → tanyin CLI 调用示例（POSIX 形；Windows 用 py -3 同参）

| 生命周期事件 | 动作 | 调用示例 |
|---|---|---|
| 会话开始（goal/scope 在账后） | 界外基线就绪确认 | `python3 cli/tanyin-ledger scope-check --goal-dir D` |
| 命令执行前（hook/权限机制回调；无原生 API=降 Tier 1 沙箱白名单并披露） | 机械门链判定（deny-list→scope→取票） | `python3 cli/tanyin-guard exec --goal-dir D -- <命令...>`（rc 0=放行；rc 1=阻断并 REJECT 行在账） |
| 命令被阻断时（on-block） | hook-block 事件落账 | `python3 cli/tanyin-ledger append-timeline --goal-dir D --event="hook-block host=codex deny=<命中项>" --timestamp=<ISO8601>` |
| 会话结束 | 链完整核验+拦截计数供守门声明 | `python3 cli/tanyin-ledger verify-chain --goal-dir D` |

## 占位说明（如实披露）

- 本模板=「生命周期事件→调用约定」的装载说明，不是可执行拦截器：codex hook/
  权限机制以探测为准（tanyin-selfcheck --host codex --guided 自动探测项）；探测
  不出原生 hook API=降 Tier 1+披露，不谎称已挂载。
- 实测回传时点（台账 G-38）：codex=公开环境 CI 可测档——headless 实测命令行
  （`codex exec "用探隐自检"` 干跑，零对外请求）+guided probe_results 回传后
  升档；回传前模板挂载为静态验证面。
- 时间戳纪律：全部落账命令显式传 `--timestamp`（禁墙钟入账）。

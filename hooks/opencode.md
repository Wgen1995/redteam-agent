# Tier 2 hook 模板 · opencode

挂载点：插件与工具权限配置（命令执行前拦截回调→simulate.py 判定）

拦截逻辑：与 hooks/simulate.py 同源（deny-list 比对 + scope 解析；阻断=非零退出码 + timeline hook-block 事件；放行=0）。
fail-closed：拦截器自身故障也返回非零（宁误拦不放过）。
timeline 写入通道：经 tanyin-ledger append-timeline（单写者纪律）。
真机挂载验证=批次 6 五宿主矩阵（诚实边界）。

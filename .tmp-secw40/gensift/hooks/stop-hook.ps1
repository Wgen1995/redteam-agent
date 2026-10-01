# GenSift hooks/stop-hook.ps1 —— gensift/hooks/stop-hook.sh 的 PowerShell 7 翻译件（任务10）
# 纯 Windows 宿主的 Stop hook：会话还有未分析卡时，阻止宿主提前收工。
# 接法与已知限制见同目录 README.md；语义与 bash 版逐条对应（B-065/B-066/C-026/N1）。
# 用法：pwsh -NoProfile -File stop-hook.ps1   # 退出码 0=放行停止；2=阻止停止并继续
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }
. ($MyInvocation.MyCommand.Path | Split-Path -Parent | ForEach-Object { Join-Path (Split-Path $_ -Parent) 'phases/lib.ps1' })

# ---- 会话目录解析（两段兜底）----
# 1) 环境变量 GENSHIFT_SESSION 显式指定（最准；可在 hook command 里注入）
# 2) 否则扫描 ~/gensift-sessions/gensift-*，取 STATE 为 running 且 mtime 最新的
$S = $env:GENSHIFT_SESSION
if ($null -eq $S) { $S = '' }
if ($S -ceq '' -or -not (Test-GsFile (Join-Path $S 'checks.tsv'))) {
    $S = ''
    $roots = Join-Path $HOME 'gensift-sessions'
    if (Test-GsDir $roots) {
        $dirs = @(Get-ChildItem -LiteralPath $roots -Directory -Filter 'gensift-*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | ForEach-Object { $_.FullName })
        foreach ($d in $dirs) {
            if (-not (Test-GsFile (Join-Path $d 'STATE'))) { continue }
            if (-not (@(Get-LfLines (Join-Path $d 'STATE')) | Where-Object { $_ -ceq 'running' })) { continue }
            if (-not (Test-GsFile (Join-Path $d 'checks.tsv'))) { continue }
            $S = $d; break } } }

# 不是 GenSift 会话（无 running 会话 / 无账本）→ 不干预，放行停止
if ($S -ceq '' -or -not (Test-GsFile (Join-Path $S 'checks.tsv'))) { exit 0 }
# 只干预 running 会话（B-065/C-026）：done/aborted-l1/interrupted 均已终态化，不再逼跑
if (-not (@(Get-LfLines (Join-Path $S 'STATE')) | Where-Object { $_ -ceq 'running' })) { exit 0 }

# N1：Plateau 在案（主循环 step6 已判强制停轮）→ 放行停止——终态化由编排器按 terminal.ps1 完成
if (Test-GsFile (Join-Path $S 'audit/plateau.flag')) {
    Out-Lf 'Plateau 在案→终态化（phases/terminal.ps1）——step6 已判强制停轮，不再逼续跑'
    exit 0 }

# ---- 统计未分析卡 ----
# 数据行以 ^CK- 过滤：checks.tsv 在主循环中被整体重排序，表头行可能沉到文件末尾（与 SKILL.md 终态判定同口径）
$N = 0; $ED = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 0) -cmatch '^CK-') {
        if ((Fld $rW 1) -cne 'ext' -and (Fld $rW 4) -ceq 'unchecked') { $N++ }
        if ((Fld $rW 1) -ceq 'ext' -and (Fld $rW 4) -ceq 'deferred') { $ED++ } } }

if ($N -gt 0) {
    # B-066：返回消息自带"下一条协议命令"——跨宿主协议卡，宿主照做即续跑
    $nxt = '执行 phases/main-loop.ps1 的 step0→step1（前置检查+取卡）'
    if (Test-GsFile (Join-Path $S 'tmp/stall_lane')) { $nxt = '执行 phases/main-loop.ps1 的 step1（L3 换道：本轮全派 fw/term）' }
    $msg = "继续：剩余 $N 张卡未分析，下一条命令是 $nxt"
    Out-Lf $msg                                                                  # stdout：日志 / 人工运行可见
    [System.Console]::Error.WriteLine($msg)                                      # stderr：Claude Code 的 Stop hook 只把 stderr 回喂给模型
    exit 2                                                                       # Stop hook 语义：exit 2 = 阻止停止并继续；exit 1 不阻止
}

if ($ED -gt 0) {
    $msg = "继续：ext deferred $ED 张待终态披露，下一条命令是 执行 phases/terminal.ps1（不变量+终态报告）"
    Out-Lf $msg
    [System.Console]::Error.WriteLine($msg)
    exit 2
}

# C-026（A2 停止路径）：两个继续判据都清空、但 STATE 仍 running——宿主在终态节跑完之前停轮。
# 状态全在盘，直接记 interrupted + 退出码 2（同源路径再次发起即断点续跑）
Set-LfContent (Join-Path $S 'STATE') @('interrupted')
Set-LfContent (Join-Path $S 'EXIT_CODE') @('2')
exit 0

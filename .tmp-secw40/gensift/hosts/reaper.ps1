# GenSift hosts/reaper.ps1 —— 孤儿进程收尸 + idle 看门狗 + 墙钟硬超时（windows 侧；posix 侧用 reaper.sh）
# 设计依据：§15 宿主适配补强（D-098/D-099/D-100）。与 reaper.sh 同接口同语义（注册表/锁/三重检测逐条对应）。
# 用法：
#   pwsh -NoProfile -File reaper.ps1 register   <session> <pid> [desc]
#   pwsh -NoProfile -File reaper.ps1 unregister <session> <pid>
#   pwsh -NoProfile -File reaper.ps1 watch      <session> <pid> [idle_s] [wall_s] [poll_s]
#   pwsh -NoProfile -File reaper.ps1 reap       <session> [-All]
# 退出码：0=正常；3=watch 判 idle/墙钟超时并已 kill；4=收尸发现孤儿并已清档/kill；1=用法错
param(
    [Parameter(Mandatory)][string]$Action,
    [Parameter(Mandatory)][string]$Session,
    [string]$ProcId,
    [string]$Desc = 'child',
    [int]$IdleSeconds = 2700,
    [int]$WallSeconds = 14400,
    [int]$PollSeconds = 60,
    [switch]$All
)
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }
. (Join-Path $PSScriptRoot '..\phases\lib.ps1')

$REG = Join-Path $Session 'audit/host-children.tsv'
$LOCK = Join-Path $Session 'audit/reaper.lock'
New-GsDir (Join-Path $Session 'audit')
if (-not (Test-GsFile $REG)) {
    Set-LfContent $REG @('pid' + "`t" + 'started' + "`t" + 'desc') }

function With-Lock([scriptblock]$Body) {          # 加锁注册表（D-100）
    $i = 0
    while ($true) {
        try { [System.IO.Directory]::CreateDirectory($LOCK) | Out-Null; break }
        catch { $i++; if ($i -gt 100) { [Console]::Error.WriteLine('reaper: lock 超时'); return } ; Start-Sleep -Milliseconds 100 } }
    try { & $Body } finally { if (Test-GsDir $LOCK) { [System.IO.Directory]::Delete($LOCK) } } }
function Test-Alive([string]$procId) {
    if ($procId -cmatch '^[0-9]+$') {
        try { $null = Get-Process -Id ([int]$procId) -ErrorAction Stop; return $true } catch { return $false } }
    return $false }
function Invoke-PgKill([string]$procId) {          # 进程组 kill（Windows：进程树 kill；D-100）
    if ($procId -cmatch '^[0-9]+$') {
        try { Stop-Process -Id ([int]$procId) -Force -ErrorAction Stop } catch { } }
    return $true }

switch ($Action) {
    'register' {
        if ($ProcId -ceq '') { exit 1 }
        With-Lock { Add-LfContent $REG @($ProcId + "`t" + (Get-GsTimestamp) + "`t" + $Desc) }
        Out-Lf "registered $ProcId" }
    'unregister' {
        if ($ProcId -ceq '') { exit 1 }
        With-Lock { $rows = @(Get-LfLines $REG) | Where-Object { -not $_.StartsWith($ProcId + "`t") }
            Set-LfContent $REG $rows }
        Out-Lf "unregistered $ProcId" }
    'watch' {
        # 三重完成检测之②③（①=宿主 CLI 事件流，见 adapter 文档）：不依赖被监控方配合——
        # 活性信号=会话目录最新写入时间（账本/分片在写=在干活），墙钟=watch 起算
        if ($ProcId -ceq '') { exit 1 }
        With-Lock { Add-LfContent $REG @($ProcId + "`t" + (Get-GsTimestamp) + "`t" + 'watchdog') }
        $started = [DateTime]::UtcNow
        $lastAct = $started
        $code = 0
        while ($true) {
            Start-Sleep -Seconds $PollSeconds
            if (-not (Test-Alive $ProcId)) { break }                       # 正常退出（CLI 事件流兜底）
            $now = [DateTime]::UtcNow
            $newest = Get-ChildItem -LiteralPath $Session -Recurse -File -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
            if ($null -ne $newest -and $newest.LastWriteTimeUtc -gt $lastAct) { $lastAct = $newest.LastWriteTimeUtc }
            if (($now - $lastAct).TotalSeconds -gt $IdleSeconds) {      # idle 看门狗（阈值校准见 adapter 文档 D-099）
                [Console]::Error.WriteLine("watchdog: idle $([int](($now - $lastAct).TotalSeconds))s > $IdleSeconds`s → kill 进程树 $ProcId")
                Invoke-PgKill $ProcId; $code = 3; break }
            if (($now - $started).TotalSeconds -gt $WallSeconds) {      # 墙钟硬超时
                [Console]::Error.WriteLine("watchdog: 墙钟 $([int](($now - $started).TotalSeconds))s > $WallSeconds`s → kill 进程树 $ProcId")
                Invoke-PgKill $ProcId; $code = 3; break } }
        With-Lock { $rows = @(Get-LfLines $REG) | Where-Object { -not $_.StartsWith($ProcId + "`t") }
            Set-LfContent $REG $rows }
        exit $code }
    'reap' {
        $killed = 0
        foreach ($l in @(Get-LfLines $REG)) {
            $p3 = $l -split "`t"; $rp = $p3[0]
            if ($rp -ceq '' -or $rp -ceq 'pid') { continue }
            if (Test-Alive $rp) {
                if (-not $All) { continue }
                [Console]::Error.WriteLine("reap: kill 活条目 $rp（$($p3[2])）")
                Invoke-PgKill $rp; $killed = 1 }
            else {
                [Console]::Error.WriteLine("reap: 清档死条目 $rp（$($p3[2])）")
                $killed = 1 }
            With-Lock { $rows = @(Get-LfLines $REG) | Where-Object { -not $_.StartsWith($rp + "`t") }
                Set-LfContent $REG $rows } }
        if ($killed -eq 1) { exit 4 }
        exit 0 }
    default { [Console]::Error.WriteLine('usage: reaper.ps1 register|unregister|watch|reap <session> <pid> [args]'); exit 1 }
}

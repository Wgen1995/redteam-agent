# GenSift phases/l2.ps1 —— phases/l2.md 的 PowerShell 7 翻译件（任务10）
# 权威源 = l2.md 的 3 个 bash 块；节标题与 md 块标题一一对应。翻译总则见 phases/lib.ps1。

# ===== l2frontier: L2 发散（L1 全闭合后必跑——unknown-unknowns 的唯一合法通道） =====
. "$S/env.ps1"
$BLOCKED = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 4) -ceq 'blocked') { $BLOCKED++ } }
# 访问上限（D-102）：保险丝定位而非精调值，宁早停不空转
$V = 1; if (Test-GsFile (Join-Path $S 'audit/l2_visits')) { $V = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/l2_visits'))[0])) + 1 }
Set-LfContent (Join-Path $S 'audit/l2_visits') @("$V")
$ZS = 0; if (Test-GsFile (Join-Path $S 'audit/l2_zero_streak')) { $ZS = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/l2_zero_streak'))[0])) }
if ($V -gt 5 -or $ZS -ge 2) {
    if (-not (Test-GsFile (Join-Path $S 'audit/joins-round-done'))) {
        Out-Lf "L2 收敛/上限（visits=$V zero_streak=$ZS）→ 先执行【拼链与合并】（phases/joins.md）——其 follow-up ext 卡回主循环派发" }
    else {
        Out-Lf "L2 收敛/上限（visits=$V zero_streak=$ZS）→ 跳过派发，直接【终态】" } }
else {
    # 发散输入（B-093 全口径）：blocked 残链 + 未交付候选 + dangling joins + guard 离群源
    $fr = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -ceq 'blocked') { $fr.Add('blocked' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 2)) } }
    if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 7) -cne 'delivered' -and (Fld $rW 7) -cne 'degraded' -and -not ((Fld $rW 6)).StartsWith('merged-into')) { $fr.Add('open-cand' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 5)) } } }
    if (Test-GsFile (Join-Path $S 'joins.tsv')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 1) -ceq 'NA' -or (Fld $rW 3) -ceq 'NA') { $fr.Add('dangling-join' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 5)) } } }
    if (Test-GsFile (Join-Path $S 'inventories/source_inventory.tsv')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 6) -cmatch 'unknown') { $fr.Add('guard-outlier' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 2)) } } }
    Set-LfContent (Join-Path $S 'tmp/l2_frontier.txt') $fr
    foreach ($l in $fr) { Out-Lf $l } }

# ===== l2div: DIV 分片验收后转 ext 卡（发散通道的唯一出口是卡） =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
$f = Join-Path $S "shards/DIV-R$R.tsv"
$n = 0
if (Test-GsFile $f -and (Get-Item -LiteralPath $f).Length -gt 0) {
    foreach ($line in @(Get-LfLines $f)) {
        $cols = Get-BashRead $line 3                                          # read -r head desc sugg（IFS-TAB 折叠）
        $head = Fld $cols 0
        if (-not $head.StartsWith('DIV:')) { continue }
        if ($n -ge 20) { break }                                              # ≤20 机械封顶
        $aid = $head.Substring(4)                                             # 锚点 ID 在 DIV: 前缀里
        $has = $false                                                         # 锚点级去重：同锚点已有 ext 卡则跳过
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'ext' -and (Fld $rW 2) -ceq $aid) { $has = $true; break } }
        if ($has) { continue }
        $n++
        Add-LfContent (Join-Path $S 'checks.tsv') @(('CK-ext-{0:d5}-{1:d3}' -f [int](ConvertTo-GsNum $R), $n) + "`t" + 'ext' + "`t" + $aid + "`t" + $aid + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') } }
Out-Lf "L2: $n 张 ext 卡入账"
# 收敛账本：零新条连计 2 轮 → L2 结束（不靠编排器记忆）
if ($n -eq 0) {
    $z = 0; if (Test-GsFile (Join-Path $S 'audit/l2_zero_streak')) { $z = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/l2_zero_streak'))[0])) }
    Set-LfContent (Join-Path $S 'audit/l2_zero_streak') @("$($z + 1)") }
else { Set-LfContent (Join-Path $S 'audit/l2_zero_streak') @('0') }
Out-Lf "l2_zero_streak=$(@(Get-LfLines (Join-Path $S 'audit/l2_zero_streak'))[0])（≥2 → 跳过 L2 派发，直接终态）"

# ===== l2inv: 不变式轨（per invariant × module 发 ext 卡——B-084） =====
. "$S/env.ps1"
# module 取值域 = file_inventory.module 的语义模块（F1：只认 mod: 前缀并剥掉——dir: 机械回填与 '-' 不算）；域过滤（B-087/D-073）
$mods = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $mv = Fld $rW 4
    if ($mv -cmatch '^mod:') { $mods.Add($mv.Substring(4)) } }
$modsU = @($mods | Sort-OrdinalU) | Where-Object { $_ -cne '' }
if ($modsU.Count -eq 0) { $modsU = @('-') }
$DOM = ''
if (Test-GsFile (Join-Path $S 'recon/industry-domain.md')) {
    foreach ($l in @(Get-LfLines (Join-Path $S 'recon/industry-domain.md'))) {
        $m2 = [regex]::Match($l, '^domain: *(.*)$')
        if ($m2.Success) { $DOM = ($m2.Groups[1].Value -creplace '[ \t\r]', ''); break } } }
$SKIPPED = 0; $LOADED = 0
foreach ($invf in (Get-GsGlob (Join-Path $SK 'invariants') '*.inv')) {
    $IDOM = ''
    foreach ($l in @(Get-LfLines $invf)) {
        $m2 = [regex]::Match($l, '^# domain: *(.*)$')
        if ($m2.Success) { $IDOM = ($m2.Groups[1].Value -creplace '[ \t\r]', ''); break } }
    if ($DOM -cne '' -and $IDOM -cne '' -and $IDOM -cne $DOM) { $SKIPPED++; continue }
    $LOADED++
    foreach ($rW in (Get-Tsv $invf)) {
        $iid = Fld $rW 0
        if (-not $iid.StartsWith('INV-')) { continue }
        foreach ($mod in $modsU) {
            $cid = "CK-ext-$iid-$mod"                                        # 整字段相等比较防前缀误判
            $has = $false
            foreach ($r2 in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $r2 0) -ceq $cid) { $has = $true; break } }
            if ($has) { continue }
            Add-LfContent (Join-Path $S 'checks.tsv') @($cid + "`t" + 'ext' + "`t" + "$iid-$mod" + "`t" + $iid + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') } } }
$extN = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'ext') { $extN++ } }
Out-Lf "不变式 ext 卡总数: $extN（module 域: $($modsU -join ',')）"
$domShow = $DOM; if ($DOM -ceq '') { $domShow = '未产出（全加载+披露）' }
Out-Lf "invariants 域过滤: domain=$domShow 加载包=$LOADED 跳过包=$SKIPPED（.inv 头 # domain: 不匹配即整包跳过——B-087）"

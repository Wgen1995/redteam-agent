# GenSift phases/terminal.ps1 —— phases/terminal.md 的 PowerShell 7 翻译件（任务10）
# 权威源 = terminal.md 的 9 个 bash 块；节标题与 md 块标题一一对应。翻译总则见 phases/lib.ps1。

# ===== inv: 先跑不变量（I1-I20 全量） =====
. "$S/env.ps1"
$invF = Join-Path $S 'audit/invariants.md'
function Out-Inv { param([string]$x) Out-Lf $x; Add-LfContent $script:invF2 @($x) }
$script:invF2 = $invF
Out-Inv '═══ 不变量检查 ═══'
# I1 类 fixture 门在 dev 侧（gensift-dev/commands/golden/）——会话内不重跑，如实记边界
Out-Inv 'I1 类fixture: NEEDS-DEV（dev 侧 golden/smoke 双件对夹具——会话内不重跑）｜边界: 需 dev 门'
$i2ok = Test-GsChecksums (Join-Path $S 'inventories') (Join-Path $S 'inventories/frozen.sha256')
if ($i2ok) { Out-Inv 'I2 冻结: PASS｜边界: —' } else { Out-Inv 'I2 冻结: FAIL｜边界: —' }
# I3 三向完备（C-Inv03）
function Get-Col([string]$file, [scriptblock]$filter) {
    $res = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv $file)) { if ($first) { $first = $false; continue }; if (& $filter $rW) { $res.Add((Fld $rW 0)) } }
    , $res.ToArray() }
$allSink = Get-Col (Join-Path $S 'inventories/sink_inventory.tsv') { param($x) $true }
$bwRefs = [System.Collections.Generic.List[string]]::new()
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'bw') { $bwRefs.Add((Fld $rW 2)) } }
$fwRefs = [System.Collections.Generic.List[string]]::new()
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'fw') { $fwRefs.Add((Fld $rW 2)) } }
$tmRefs = [System.Collections.Generic.List[string]]::new()
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'term') { $tmRefs.Add((Fld $rW 2)) } }
$srcHttp = [System.Collections.Generic.List[string]]::new()
$srcPw = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $et = Fld $rW 3
    if ($et -ceq 'http' -or $et -ceq 'external_message') { $srcHttp.Add((Fld $rW 0)); $srcPw.Add((Fld $rW 0)) }
    elseif ($et -ceq 'persisted_read') { $srcPw.Add((Fld $rW 0)) } }
$appCfg = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -ceq 'app' -or (Fld $rW 5) -ceq 'config') { $appCfg.Add((Fld $rW 0)) } }
$M1 = @(Get-Comm23 $allSink $bwRefs.ToArray()).Count
$M1R = @(Get-Comm13 $allSink $bwRefs.ToArray()).Count
$M2 = @(Get-Comm23 $srcHttp.ToArray() $fwRefs.ToArray()).Count
$M2R = @(Get-Comm13 $srcPw.ToArray() $fwRefs.ToArray()).Count
$M3 = @(Get-Comm23 $appCfg.ToArray() $tmRefs.ToArray()).Count
$M3R = @(Get-Comm13 $appCfg.ToArray() $tmRefs.ToArray()).Count
$i3pass = ($M1 -eq 0 -and $M1R -eq 0 -and $M2 -eq 0 -and $M2R -eq 0 -and $M3 -eq 0 -and $M3R -eq 0)
Out-Inv ("I3 三向: $(if ($i3pass) { 'PASS' } else { "FAIL(bw:$M1/$M1R fw:$M2/$M2R term:$M3/$M3R)" })｜边界: demand 追踪卡入 fw 反向口径")
$BAD4 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 0) -cmatch '^CK-' -and (Fld $rW 4) -cnotmatch '^(unchecked|candidate|refuted|not_applicable|no_path|blocked|partial|deferred)$') { $BAD4++ } }
Out-Inv ("I4 终态: $(if ($BAD4 -eq 0) { 'PASS' } else { "FAIL($BAD4)" })｜边界: —")
# I5 候选分片（C-Inv05 四子检查）
$BAD5 = 0
foreach ($vf in (Get-GsGlob (Join-Path $S 'shards') 'V-*.tsv')) {
    $c5 = @(@(Get-LfLines $vf) | Where-Object { $_.StartsWith('SELF:') }).Count
    if ($c5 -lt 1) { $BAD5++ } }
$i5v = [System.Collections.Generic.List[string]]::new()
foreach ($vf in (Get-GsGlob (Join-Path $S 'shards') 'V-*.tsv')) {
    $bn = [IO.Path]::GetFileNameWithoutExtension($vf); $i5v.Add($bn.Substring(2)) }
Set-LfContent (Join-Path $S 'tmp/i5v.txt') $i5v                                   # bash：ls|sed 留档供对账
$BAD5A = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 1) -cne 'G1' -and -not ((Fld $rW 6)).StartsWith('merged-into') -and (Fld $rW 7) -cne 'degraded' -and -not ($i5v -ccontains (Fld $rW 0))) { $BAD5A++ } } }   # 与 bash 修复同步：前缀语义（i5v 空表无 NR==FNR 摊平层）
$BAD5B = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ((Fld $rW 1) -ceq 'G1' -and (Fld $rW 6) -cne '' -and (Fld $rW 6) -cne 'open' -and (Fld $rW 6) -cne 'closed-by-evidence' -and (Fld $rW 6) -cne 'refuted-by-evidence') { $BAD5B++ } } }
$BAD5C = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 12) -ceq '' -and (Fld $rW 2) -ceq 'confirmed') {
        $sev = Fld $rW 3
        $fpath = Join-Path $S "findings/$(Fld $rW 0).md"
        $hasCvss = $false
        if (Test-GsFile $fpath) { if (@(Get-LfLines $fpath) | Where-Object { $_ -cmatch 'CVSS: \S' }) { $hasCvss = $true } }
        if ($sev -ceq '' -or -not $hasCvss) { $BAD5C++ } } }
Out-Inv ("I5 候选分片: $(if ($BAD5 -eq 0 -and $BAD5A -eq 0 -and $BAD5B -eq 0 -and $BAD5C -eq 0) { 'PASS' } else { "FAIL(无SELF:$BAD5 缺V分片:$BAD5A 种子未闭合:$BAD5B 缺sev/cvss:$BAD5C)" })｜边界: —")
# I6 四相等（S9 新口径）
$F = @(Get-GsGlob (Join-Path $S 'findings') 'F-*.md').Count
$FA = @(Get-GsGlob (Join-Path $S 'audit') 'reversed-F-*.md').Count + @(Get-GsGlob (Join-Path $S 'audit') 'superseded-F-*.md').Count
$MF = 0; $MFA = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    $MF++
    $lc = Fld $rW 12; if ($lc -ceq '-' -or $lc.ToLower() -ceq 'n/a') { $lc = '' }
    if ($lc -ceq '') { $MFA++ } }
$logm = @{}; $canon = @{}
if (Test-GsFile (Join-Path $S 'audit/merge.log')) {
    foreach ($rW in (Get-Tsv (Join-Path $S 'audit/merge.log'))) {
        if ((Fld $rW 0) -ceq 'MERGED') { $logm[(Fld $rW 1)] = 1; $canon[(Fld $rW 3)] = 1 } } }
$BAD6 = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if (((Fld $rW 6)).StartsWith('merged-into')) {
            if (-not $logm.ContainsKey((Fld $rW 0))) { $BAD6++ }
            $t = (Fld $rW 6).Substring(12)
            if (-not $canon.ContainsKey($t)) { $BAD6++ } } } }
$i6pass = ($F -eq $MFA -and $MF -eq ($F + $FA) -and $BAD6 -eq 0)
Out-Inv ("I6 对账: $(if ($i6pass) { "PASS($F+${FA}撤档 吸收:$BAD6)" } else { "FAIL(findings:$F 在役:$MFA 总行:$MF 撤档:$FA 吸收记账:$BAD6)" })｜边界: —")
# I7 剪枝事实 confirmer 过（C-Inv07 验收侧）
$cf = @{}
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ((Fld $rW 5) -ceq 'confirmed') { $cf[(Fld $rW 0)] = 1 } }
$BAD7 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if (((Fld $rW 5)).StartsWith('k') -and (Fld $rW 5) -cmatch '^k[0-9]') {
        $fu = Fld $rW 6
        if ($fu -ceq '') { $BAD7++; continue }
        foreach ($u in ($fu -split ',')) { if (-not $cf.ContainsKey($u)) { $BAD7++ } } } }
Out-Inv ("I7 剪枝事实: $(if ($BAD7 -eq 0) { 'PASS' } else { "FAIL($BAD7)" })｜边界: —")
# I8 分片零丢失（C-Inv08 账本侧口径）
$RAW8 = 0
foreach ($f in @(@(Get-GsGlob (Join-Path $S 'shards') 'A-*.tsv') + @(Get-GsGlob (Join-Path $S 'shards') 'SUM-*.tsv'))) {   # 首操作数 @() 包裹：单元素 glob 摊平为标量时 + 变字符串拼接（任务11 终审B P0）
    # 与 bash 修复同步：守卫累加——零命中分片不再冻结计数
    $RAW8 += @(@(Get-LfLines $f) | Where-Object { $_.StartsWith('FACT:') }).Count }
$DED8 = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ($first) { $first = $false; continue }; $DED8++ }
$hit8 = $RAW8 - $DED8; if ($hit8 -lt 0) { $hit8 = 0 }
Out-Inv "I8 分片对账: 分片FACT=$RAW8 账本行=$DED8 去重命中=$hit8｜边界: 幂等去重口径（重派/换轮号不双计；逐片对账=3b manifest）"
# I9 引文（C-058/C-Inv09：转义还原后全行相等——含 FACT evidence）
$BAD9 = 0
foreach ($f in (Get-GsGlob (Join-Path $S 'shards') '*.tsv')) {
    foreach ($line in @(Get-LfLines $f)) {
        $ti = $line.IndexOf("`t")
        $ref = $line; $quote = ''
        if ($ti -ge 0) { $ref = $line.Substring(0, $ti); $quote = $line.Substring($ti + 1) }
        if ($ref -clike 'OBS:*' -or $ref -clike 'SELF:*') {
            $loc = $ref.Substring($ref.IndexOf(':') + 1)
            $file = Remove-GsSuffix1 $loc ':'; $line_no = Remove-GsPrefixL $loc ':'
            if ($line_no -cnotmatch '^[0-9]+$') { $BAD9++; continue }
            $srcL = Get-GsLine (Join-Path $SRC $file) ([int]$line_no)
            if ($srcL -cne (ConvertFrom-GsEsc $quote)) { $BAD9++ } }
        elseif ($ref -clike 'FACT:*') {
            $floc = ($quote -split "`t")[0]
            if ($null -eq $floc) { $floc = '' }
            $fev = ''; $fq = $quote -split "`t"; if ($fq.Count -gt 1) { $fev = $fq[1] }
            $file = Remove-GsSuffix1 $floc ':'; $line_no = Remove-GsPrefixL $floc ':'
            if ($line_no -cnotmatch '^[0-9]+$') { $BAD9++; continue }
            $srcL = Get-GsLine (Join-Path $SRC $file) ([int]$line_no)
            if ($srcL -cne (ConvertFrom-GsEsc $fev)) { $BAD9++ } } } }
Out-Inv ("I9 引文: $(if ($BAD9 -eq 0) { 'PASS' } else { "FAIL($BAD9)" })｜边界: —（含 FACT evidence，转义还原后全行相等）")
# I10 引用可解析（C-Inv10）
$i10refs = [System.Collections.Generic.List[string]]::new()
foreach ($file in @((Join-Path $S 'facts.tsv'), (Join-Path $S 'candidates.tsv'), (Join-Path $S 'machine-fields.tsv'))) {
    $first = $true
    foreach ($rW in (Get-Tsv $file)) {
        if ($first) { $first = $false; continue }
        $col = Fld $rW 2
        if ($file -clike '*candidates*') { $col = Fld $rW 5 }
        if ($file -clike '*machine-fields*') { $col = Fld $rW 5 }
        if ($col -ceq '' -or $col -ceq '-') { continue }
        if ($col.StartsWith($SRC + '/')) { $col = $col.Substring($SRC.Length + 1) }
        $i10refs.Add(($col -creplace ':[0-9]*$', '')) } }
$i10u = @($i10refs | Sort-OrdinalU)
Set-LfContent (Join-Path $S 'tmp/i10refs.txt') $i10u
$fiFiles = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; $fiFiles.Add((Fld $rW 1)) }
$BAD10 = @(Get-Comm23 $i10u @($fiFiles | Sort-OrdinalU)).Count
Out-Inv ("I10 引用可解析: $(if ($BAD10 -eq 0) { 'PASS' } else { "FAIL($BAD10)——悬空文件清单见 tmp/i10refs.txt 差集" })｜边界: —")
# I13 假设点必复核（C-Inv13）
$jl = @{}
if (Test-GsFile (Join-Path $S 'joins.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) { if ($first) { $first = $false; continue }; $jl[(Fld $rW 0)] = Fld $rW 5 } }
$closed = @{}
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 1) -ceq 'ext' -and $jl.ContainsKey((Fld $rW 3))) { $closed[(Fld $rW 3)] = ((Fld $rW 4) -cne 'unchecked') } }
$BAD13 = 0
foreach ($k in $jl.Keys) { if ($jl[$k] -cne '' -and -not $closed.ContainsKey($k)) { $BAD13++ } }
Out-Inv ("I13 假设点: $(if ($BAD13 -eq 0) { 'PASS' } else { "FAIL($BAD13)" })｜边界: 拼链轮未跑时为空检（0 行 joins）")
# I11 级联（C-Inv11）
$fIds = @{}
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { $fIds[(Fld $rW 0)] = 1 }
$BAD11 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 5) -cmatch '^k[0-9]') {
        $fu = Fld $rW 6
        if ($fu -ceq '') { $BAD11++; continue }
        foreach ($u in ($fu -split ',')) { if (-not $fIds.ContainsKey($u)) { $BAD11++ } } } }
Out-Inv ("I11 级联: $(if ($BAD11 -eq 0) { 'PASS' } else { "FAIL($BAD11)" })｜边界: —")
# I12 band0/1（C-Inv12）
$b12 = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -ceq '0' -or (Fld $rW 5) -ceq '1') { $b12[(Fld $rW 0)] = 1 } }
$V12 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 5) -cmatch '^k[0-9]' -and $b12.ContainsKey((Fld $rW 2))) { $V12++ } }
Out-Inv ("I12 band0: $(if ($V12 -eq 0) { 'PASS' } else { "FAIL($V12)" })｜边界: —")
# I15 恢复入口（C-Inv15）
$BAD15 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if (((Fld $rW 4) -ceq 'blocked' -or (Fld $rW 4) -ceq 'partial' -or (Fld $rW 4) -ceq 'deferred') -and (Fld $rW 5) -ceq '') { $BAD15++ } }
Out-Inv ("I15 恢复入口: $(if ($BAD15 -eq 0) { 'PASS' } else { "FAIL($BAD15)" })｜边界: 入口投影=coverage §4")
# I17 写边界（C-Inv17，mtime 口径）
$W17 = 0
$srcStamp = Join-Path $S 'SOURCE'
if (Test-GsFile $srcStamp) {
    $refT = (Get-Item -LiteralPath $srcStamp).LastWriteTimeUtc
    foreach ($f in (Find-GsFiles $SRC @())) {
        if ((Get-Item -LiteralPath $f).LastWriteTimeUtc -gt $refT) { $W17++ } } }
Out-Inv ("I17 写边界: $(if ($W17 -eq 0) { 'PASS' } else { "FAIL($W17)" })｜边界: mtime 口径（粒度=文件系统时间精度；会话外产物=OUT 目录树，天然隔离）")
# I14 ID 确定性（C-Inv14，v1.4.0-S10 按类型分派）
$DUP14 = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $allC = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ($first) { $first = $false; continue }; $allC.Add((Fld $rW 0)) }
    $DUP14 = $allC.Count - @($allC | Sort-OrdinalU).Count }
$X14 = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        $cid = Fld $rW 0
        if ($cid -cnotmatch '^CD-[0-9]{5}-[0-9]{5}$' -and $cid -cnotmatch '^CD-INV-' -and $cid -cnotmatch '^CD-F-' -and $cid -cnotmatch '^CD-SEED-') { $X14++ } } }
Out-Inv ("I14 ID反推: $(if ($DUP14 -eq 0 -and $X14 -eq 0) { 'PASS' } else { "FAIL(dup:$DUP14 X逃逸:$X14——CD-X- 锚点逃逸段，coverage 披露)" })｜边界: CD-X 逃逸段计披露不参与反推")
# I19 枚举核对（C-Inv19/A-085）
$D19 = 'NA'
if (Test-GsFile (Join-Path $S 'audit/i19.md')) { $D19 = @(@(Get-LfLines (Join-Path $S 'audit/i19.md')) | Where-Object { $_ -cmatch 'diff=-?[1-9]' }).Count }
Out-Inv ("I19 枚举对账: $(if ($D19 -ceq '0') { 'PASS' } else { "FAIL($D19)——逐行差异见 audit/i19.md" })｜边界: —")
$BAD20 = 0
foreach ($f in (Get-GsGlob (Join-Path $S 'shards') '*.tsv')) {
    $fl = @(Get-LfLines $f)
    $ftLine = 0; $loLine = 0
    for ($xi = 0; $xi -lt $fl.Count; $xi++ ) {
        if ($fl[$xi] -cmatch '^(TERM:|VERDICT:)' -and $ftLine -eq 0) { $ftLine = $xi + 1 }
        if ($fl[$xi] -cmatch '^(OBS:|SELF:)') { $loLine = $xi + 1 } }
    if ($ftLine -gt 0 -and $loLine -gt 0 -and $loLine -ge $ftLine) { $BAD20++ } }
Out-Inv ("I20 先后: $(if ($BAD20 -eq 0) { 'PASS' } else { "FAIL($BAD20)" })｜边界: —")

# ===== G2: 闭卷对账（机械——不派 LLM；A-010/C-012/C-016） =====
. "$S/env.ps1"
$cntF = { param($file, [scriptblock]$pred) $c = 0; $first = $true; foreach ($rW in (Get-Tsv $file)) { if ($first) { $first = $false; continue }; if (& $pred $rW) { $c++ } }; $c }
$N_SINK = & $cntF (Join-Path $S 'inventories/sink_inventory.tsv') { param($x) $true }
$N_BW = & $cntF (Join-Path $S 'checks.tsv') { param($x) (Fld $x 1) -ceq 'bw' }
$N_CARD = & $cntF (Join-Path $S 'checks.tsv') { param($x) $true }
$N_TERM_ST = & $cntF (Join-Path $S 'checks.tsv') { param($x) (Fld $x 4) -cne 'unchecked' }
$N_MF = & $cntF (Join-Path $S 'machine-fields.tsv') { param($x) (Fld $x 12) -ceq '' }
$N_CAND = & $cntF (Join-Path $S 'candidates.tsv') { param($x) $true }
$N_DELV = & $cntF (Join-Path $S 'candidates.tsv') { param($x) (Fld $x 7) -ceq 'delivered' }
$N_MERG = & $cntF (Join-Path $S 'candidates.tsv') { param($x) ((Fld $x 6)).StartsWith('merged-into') }
$BADG2A = & $cntF (Join-Path $S 'checks.tsv') { param($x) (Fld $x 4) -cne 'unchecked' -and (Fld $x 5) -ceq '' -and (Fld $x 6) -ceq '' }
$POLL = 0
$g2poll = [System.Collections.Generic.List[string]]::new()
foreach ($pf in @(@(Get-GsGlob (Join-Path $S 'findings') 'F-*.md') + @((Join-Path $S 'combinations.md')))) {   # 首操作数 @() 包裹：恰 1 个 finding 时摊平拼接→POLL 恒 0（任务11 终审B P0）
    if (-not (Test-GsFile $pf)) { continue }
    $lnNo = 0
    foreach ($ln in @(Get-LfLines $pf)) {
        $lnNo++
        if ($ln -cmatch 'CVE-[0-9]{4}-[0-9]{4,}|GHSA-[a-z0-9-]{4,}') {
            $g2poll.Add("$([IO.Path]::GetFileName($pf))`t$($lnNo):$ln")   # bash grep -n 前缀 N:line 对齐（任务11 终审B P2-4）
            $POLL++ } } }
Set-LfContent (Join-Path $S 'tmp/g2-poll.txt') $g2poll
$g2 = [System.Collections.Generic.List[string]]::new()
$g2.Add("# G2 闭卷对账（机械——不派 LLM；$(Get-GsTimestamp)）")
$g2.Add('## 三向计数（清单 vs 卡 vs findings——差异项逐条解释，不设相等断言：demand 追踪卡/ext 卡是合法增量）')
$g2.Add("- 清单: sink=$N_SINK ｜ 卡: 总=$N_CARD（bw=$N_BW，demand/fw 追踪卡为 fw 合法增量）｜ 已裁=$N_TERM_ST")
$g2.Add("- findings: 在役=$N_MF ｜ 候选下场: 总=$N_CAND delivered=$N_DELV merged=$N_MERG（其余=pending/degraded，coverage §8 披露）")
$le = '成立'; if (($N_DELV + $N_MERG) -gt $N_CAND) { $le = '破坏' }
$g2.Add("- 三向锚点: sink→bw 卡差=$($N_BW - $N_SINK)（0=逐 sink 一卡；I3 反向口径同源）；delivered+merged ≤ 总候选=$le")
$g2.Add('## 每卡下场可指认（state 已裁 ⇒ reason 非空 ∨ facts_used 非空）')
if ($BADG2A -eq 0) { $g2.Add('- 不可指认: 0 张') }
else {
    $g2.Add("- 不可指认: $BADG2A 张（下场无 reason 无 K 关联——账本口径缺口，逐卡如下）")
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -cne 'unchecked' -and (Fld $rW 5) -ceq '' -and (Fld $rW 6) -ceq '') { $g2.Add('  - ' + (Fld $rW 0) + ' state=' + (Fld $rW 4) + '（reason/facts_used 皆空）') } } }
$g2.Add('## CVE 编号污染剔除（闭卷红线——A-010：本地证据独立，编号出现即污染）')
if ($POLL -eq 0) { $g2.Add('- findings/combinations 命中: 0 处（闭卷干净）') }
else {
    $g2.Add("- findings/combinations 命中: $POLL 处——污染剔除：命中行不作为证据采信，相关 finding 需无编号复检")
    foreach ($l in $g2poll) { $g2.Add('  - ' + $l) } }
$g2.Add('## precision 抽检（G2 门人工侧）')
$g2.Add('- 需人工：自报 finding 抽样标注 true/false positive——机械层不出数值（门内禁声，D-091 边界声明）')
$g2.Add("结果: $(if ($BADG2A -eq 0 -and $POLL -eq 0) { 'PASS' } else { "FAIL(不可指认:$BADG2A 污染:$POLL)" })")
Set-LfContent (Join-Path $S 'audit/g2.md') $g2
foreach ($l in $g2) { Out-Lf $l }

# ===== G3: 双跑稳定（分级契约——A-004/A-041/C-013/C-024/C-Inv18） =====
. "$S/env.ps1"
# 同 SRC ≥2 done 会话才判（每目标一次）；对齐键=fingerprint（两跑 refreeze 重编号不丢行）
$PREV = ''
$sessions = @(Get-ChildItem -LiteralPath $OUT -Directory -Filter 'gensift-*' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
foreach ($d in ($sessions | Sort-OrdinalDesc)) {
    if ($d -ceq $S) { continue }
    if (-not (Test-GsFile (Join-Path $d 'STATE'))) { continue }
    if (-not (@(Get-LfLines (Join-Path $d 'STATE')) | Where-Object { $_.Contains('done') })) { continue }
    if (-not (Test-GsFile (Join-Path $d 'SOURCE'))) { continue }
    if ((@(Get-LfLines (Join-Path $d 'SOURCE')) -join '') -cne $SRC) { continue }
    $PREV = $d; break }
$PVER = 'absent'
$pf2 = @(Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')
if ($pf2.Count -gt 0) { $PVER = Get-GsHashCat16 $pf2 }
$dh1 = @(Get-GsGlob (Join-Path $SK 'feedback') '*') + @(Get-GsGlob (Join-Path $S 'feedback') '*')
$dhf = @($dh1 | Where-Object { Test-GsFile $_ })
$DHASH = Get-GsHashCat16 $dhf                                                      # bash：cat 失败 glob 产空输入——空哈希非 absent
Set-LfContent (Join-Path $S 'audit/run-state.tsv') @("pattern_version`t$PVER", "dispositions_hash`t$DHASH", "finished`t$(Get-GsTimestamp)")
if ($PREV -ceq '') {
    Out-GsTee (Join-Path $S 'audit/stability-diff.md') 'G3: N.A.（单跑）——同 SRC done 会话 <2；双跑后本块自动归因，指标层维持禁声'
    Out-GsTee (Join-Path $S 'audit/invariants.md') 'I18 双跑稳定: N.A.（单跑）｜边界: 双跑才判——机械层=分母冻结比对、语义层=confirmed 指纹重合度 ≥0.8' }
else {
    $RFN = 0
    foreach ($rl in @((Join-Path $S 'audit/refreeze.log'), (Join-Path $PREV 'audit/refreeze.log'))) {
        if (Test-GsFile $rl) { $RFN += @(Get-LfLines $rl).Count } }
    $MACHBAD = 0
    $fz1 = @(Get-LfLines (Join-Path $S 'inventories/frozen.sha256')) -join "`n"
    $fz2 = ''
    if (Test-GsFile (Join-Path $PREV 'inventories/frozen.sha256')) { $fz2 = @(Get-LfLines (Join-Path $PREV 'inventories/frozen.sha256')) -join "`n" }
    if ($fz1 -ceq $fz2) { $MACH = '一致' }
    elseif ($RFN -gt 0) { $MACH = "不一致（refreeze 在档 $RFN 行——归因第五类 refreeze 差异，fingerprint 对齐承接，披露不拦）" }
    else { $MACH = '不一致且无 refreeze 留痕（机械层分母损坏——硬门 FAIL，S14 门未过口径）'; $MACHBAD = 1 }
    function Get-G3Rows([string]$mfPath) {                                   # 在役行 fingerprint/verdict/severity/id
        $res = [System.Collections.Generic.List[string]]::new()
        if (Test-GsFile $mfPath) {
            $first = $true
            foreach ($rW in (Get-Tsv $mfPath)) {
                if ($first) { $first = $false; continue }
                if ((Fld $rW 12) -ceq '') { $res.Add((Fld $rW 1) + "`t" + (Fld $rW 2) + "`t" + (Fld $rW 3) + "`t" + (Fld $rW 0)) } } }
        , @($res | Sort-Ordinal) }
    $g3cur = Get-G3Rows (Join-Path $S 'machine-fields.tsv')
    $g3prev = Get-G3Rows (Join-Path $PREV 'machine-fields.tsv')
    Set-LfContent (Join-Path $S 'tmp/g3cur.tsv') $g3cur
    Set-LfContent (Join-Path $S 'tmp/g3prev.tsv') $g3prev
    $dispFixed = [System.Collections.Generic.List[string]]::new()             # C-046 fixed 回归检测（双跑口径）
    foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
        if (-not (Test-GsFile $df)) { continue }
        $first = $true
        foreach ($rW in (Get-Tsv $df)) { if ($first) { $first = $false; continue }; if ((Fld $rW 1) -ceq 'fixed') { $dispFixed.Add((Fld $rW 0)) } } }
    Set-LfContent (Join-Path $S 'tmp/disp-fixed.tsv') $dispFixed
    $fxSet = @{}; foreach ($x in $dispFixed) { $fxSet[$x] = 1 }
    $FIXROWS = [System.Collections.Generic.List[string]]::new()
    foreach ($l in $g3cur) { $fpG = ($l -split "`t")[0]; if ($fxSet.ContainsKey($fpG)) { $FIXROWS.Add($fpG + "`t" + ($l -split "`t")[3]) } }
    $FIXG = $FIXROWS.Count
    $pv = @{}; $psv = @{}; $cv = @{}; $csv = @{}
    foreach ($l in $g3prev) { $a = $l -split "`t"; $pv[$a[0]] = $a[1]; $psv[$a[0]] = $a[2] }
    foreach ($l in $g3cur) { $a = $l -split "`t"; $cv[$a[0]] = $a[1]; $csv[$a[0]] = $a[2] }
    $GN3 = 0; $GG3 = 0; $GR3 = 0; $GF3 = 0; $GC3 = 0; $GP3 = 0; $GB3 = 0; $bothc = 0
    foreach ($k in $cv.Keys) {
        if (-not $pv.ContainsKey($k)) { $GN3++ }
        else { if ($psv[$k] -cne $csv[$k]) { $GR3++ }; if ($pv[$k] -cne $cv[$k]) { $GF3++ } }
        $bothc++
        if ($cv[$k] -ceq 'confirmed') { $GC3++ } }
    foreach ($k in $pv.Keys) {
        if (-not $cv.ContainsKey($k)) { $GG3++ }
        if ($pv[$k] -ceq 'confirmed') { $GP3++ }
        if ($pv[$k] -ceq 'confirmed' -and $cv[$k] -ceq 'confirmed') { $GB3++ } }
    Set-LfContent (Join-Path $S 'tmp/g3stat') @("$GN3`t$GG3`t$GR3`t$GF3`t$GC3`t$GP3`t$GB3")
    $RATE = 1; $MIN = $GC3; if ($GP3 -lt $MIN) { $MIN = $GP3 }
    if ($MIN -gt 0) { $RATE = [math]::Round($GB3 / $MIN, 2, [System.MidpointRounding]::AwayFromZero).ToString('0.00') }
    $PDH = ''
    if (Test-GsFile (Join-Path $PREV 'audit/run-state.tsv')) {
        foreach ($l in @(Get-LfLines (Join-Path $PREV 'audit/run-state.tsv'))) {
            if ($l -cmatch '^dispositions_hash\t') { $PDH = $l.Substring(18) } } }   # 剥 'dispositions_hash\t'（18 字符）
    $DISP = if ($PDH -ceq $DHASH) { '否' } else { '是' }
    $VERD = if (([double]$RATE -ge 0.8) -and $MACHBAD -eq 0) { 'PASS' } else { 'FAIL' }
    $MACHX = ''; if ($MACHBAD -eq 1) { $MACHX = '｜机械层分母损坏' }
    $curMap = @{}
    foreach ($l in $g3cur) { $a = $l -split "`t"; $curMap[$a[0]] = $l }
    $prevMap = @{}
    foreach ($l in $g3prev) { $a = $l -split "`t"; $prevMap[$a[0]] = $l }
    $sd = [System.Collections.Generic.List[string]]::new()
    $sd.Add("# G3 双跑稳定（stability-diff——$(Get-GsTimestamp)）")
    $sd.Add("- 对照样: $PREV（同 SRC done）｜本次: $S")
    $sd.Add("- run 输入: pattern_version=$PVER ｜ 处置库哈希=$DHASH（对照跑=$PDH → 处置库变更: $DISP）")
    $sd.Add("- 机械层分母冻结: $MACH")
    $sd.Add('## 新增（本跑在役、对照跑无——按 fingerprint 对齐）')
    $curKeys = @($g3cur | ForEach-Object { ($_ -split "`t")[0] })
    $prevKeys = @($g3prev | ForEach-Object { ($_ -split "`t")[0] })
    $new30 = @()
    foreach ($l in (Get-Comm23 $curKeys $prevKeys)) { $a = $curMap[$l] -split "`t"; if ($l -cne '') { $new30 += '- ' + $l + ' ' + $a[1] + ' ' + $a[2] + '（新档 ' + $a[3] + '）' } }
    foreach ($x in ($new30 | Select-Object -First 30)) { $sd.Add($x) }
    if ($GN3 -eq 0) { $sd.Add('- （无）') }
    $sd.Add('## 消失（对照跑在役、本跑无——翻案/refute/合并吸收都算，逐条可追 mf 留痕行）')
    $gone30 = @()
    foreach ($l in (Get-Comm13 $curKeys $prevKeys)) { $a = $prevMap[$l] -split "`t"; if ($l -cne '') { $gone30 += '- ' + $l + ' ' + $a[2] + '（对照档 ' + $a[3] + '）' } }
    foreach ($x in ($gone30 | Select-Object -First 30)) { $sd.Add($x) }
    if ($GG3 -eq 0) { $sd.Add('- （无）') }
    $sd.Add('## 变级（两跑同 fingerprint、severity 不同——refreeze 重编号不影响本段：按 fp 对齐不按 cand_id）')
    $rec30 = 0
    foreach ($k in $csv.Keys) {
        if ($psv.ContainsKey($k) -and $psv[$k] -cne $csv[$k] -and $rec30 -lt 30) {
            $sd.Add('- ' + $k + ' ' + $psv[$k] + ' → ' + $csv[$k]); $rec30++ } }
    if ($GR3 -eq 0) { $sd.Add('- （无）') }
    $sd.Add('## 重合度（confirmed 集合，fingerprint 键）')
    $sd.Add("- 本跑 confirmed=$GC3 对照=$GP3 重合=$GB3 → $GB3/min=$MIN = $RATE（阈值 ≥0.8 起步——§10 G3 分级契约）")
    $sd.Add('## 归因（差异五分类——机械可得三类如实，其余语义层需人工）')
    $sd.Add("- 判定翻转: $GF3 条（同 fp verdict 不同）")
    $sd.Add("- refreeze 差异: $(if ($RFN -gt 0) { "在档（两跑合计 $RFN 行）——cand_id 重排不可对齐，本对账按 fingerprint 键" } else { '不在档' })")
    $sd.Add("- 处置库变更: $DISP（dispositions_hash 两跑比对——feedback/ 全局库）")
    $sd.Add('- 抽样波动 / L2 发散差异: 语义层归因需人工逐条复核（边界声明——机械层不臆造归因）')
    $sd.Add('## fixed 回归检测（C-046——本跑在役指纹 ∩ fixed 处置库）')
    if ($FIXG -gt 0) {
        $sd.Add("- NOTICE: $FIXG 条回归（已修复同指纹复现——report 处置节高亮；audit/disposition-notice.log）")
        foreach ($l in $FIXROWS) { $sd.Add('  - fp=' + $l) } }
    else { $sd.Add('- （无 fixed 处置命中——回归检测如实为空）') }
    $sd.Add('- 不追求语义层 diff 为空（LLM 非确定是已知缺陷，硬门必然自锁死——设计 §10）')
    $sd.Add("G3: $VERD（重合度 $RATE$MACHX）")
    Set-LfContent (Join-Path $S 'audit/stability-diff.md') $sd
    Out-GsTee (Join-Path $S 'audit/invariants.md') "I18 双跑稳定: $VERD(重合度 $RATE$MACHX)｜边界: 机械层=分母冻结比对（不一致且无 refreeze 留痕=FAIL）；语义层归因两类（抽样波动/L2 发散）需人工"
    foreach ($l in $sd) { Out-Lf $l } }

# ===== calibration: CALIBRATION 草案产出（知识闭环——B-057/B-118/B-212/B-231/C-048/D-060/D-096） =====
. "$S/env.ps1"
$PVER = 'absent'
$pf3 = @(Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')
if ($pf3.Count -gt 0) { $PVER = Get-GsHashCat16 $pf3 }                             # bash：cat *.pattern 恒有文件
$cdt = Join-Path $S 'calibration-drafts.tsv'
Set-LfContent $cdt @('draft_id' + "`t" + 'type' + "`t" + 'ref_entity' + "`t" + 'class_id' + "`t" + 'pattern_id' + "`t" + 'pattern_version' + "`t" + 'evidence' + "`t" + 'draft_ere' + "`t" + 'status')
$nCal = 0
# ① 真值外新发现（mf 在役 confirmed 的 (sink 侧 loc,class) ∉ sink 清单——pattern 漏报面）
$sinkKeys = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $sinkKeys[(Fld $rW 2) + "`t" + (Fld $rW 3)] = 1 }
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 12) -ceq '' -and (Fld $rW 2) -ceq 'confirmed' -and (Fld $rW 4) -cne '' -and (Fld $rW 5) -cne '') {
        if (-not $sinkKeys.ContainsKey((Fld $rW 5) + "`t" + (Fld $rW 4))) {
            $nCal++
            Add-LfContent $cdt @(('CAL-{0:d3}' -f $nCal) + "`t" + 'out-of-truth-new' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 4) + "`t" + '-' + "`t" + $PVER + "`t" + 'confirmed 在役但位置不在 sink 清单（pattern 漏报面）' + "`t" + '' + "`t" + 'pending') } } }
# ② pattern 误报（sink_inventory.api 顿号串拆分 × checks.ref_seq 逐卡计数）
$pmap = @{}; $clsOf = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    foreach ($idq in ((Fld $rW 4) -split '、')) {
        if ($idq -cne '') { $pmap[$idq + "`t" + (Fld $rW 0)] = 1; $clsOf[$idq] = Fld $rW 3 } } }
$cards = @{}; $stOf = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $rk = Fld $rW 2
    if (-not $cards.ContainsKey($rk)) { $cards[$rk] = [System.Collections.Generic.List[string]]::new() }
    $cards[$rk].Add((Fld $rW 0)); $stOf[(Fld $rW 0)] = Fld $rW 4 }
$tot = @{}; $bad = @{}
foreach ($pk in $pmap.Keys) {
    $a = $pk -split "`t", 2; $p3 = $a[0]; $s3 = $a[1]
    if (-not $cards.ContainsKey($s3)) { continue }
    foreach ($c3 in $cards[$s3]) {
        if (-not $tot.ContainsKey($p3)) { $tot[$p3] = 0 }; $tot[$p3]++
        if ($stOf[$c3] -ceq 'refuted' -or $stOf[$c3] -ceq 'no_path' -or $stOf[$c3] -ceq 'not_applicable') {
            if (-not $bad.ContainsKey($p3)) { $bad[$p3] = 0 }; $bad[$p3]++ } } }
foreach ($p3 in $tot.Keys) {
    if ($tot[$p3] -ge 5 -and [math]::Floor($bad[$p3] * 100 / $tot[$p3]) -ge 80) {
        $nCal++
        $badP = 0; if ($bad.ContainsKey($p3)) { $badP = $bad[$p3] }
        Add-LfContent $cdt @(('CAL-{0:d3}' -f $nCal) + "`t" + 'pattern-misfire' + "`t" + $p3 + "`t" + $clsOf[$p3] + "`t" + $p3 + "`t" + $PVER + "`t" + "命中 $($tot[$p3]) 卡中 $badP 被 refuted/no_path/not_applicable（≥80%——pattern 过宽面）" + "`t" + '' + "`t" + 'pending') } }
# ③ 处置晋升（C-048——false-positive 同 scope 类段 ≥3）
foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
    if (-not (Test-GsFile $df)) { continue }
    $cN = @{}
    $first = $true
    foreach ($rW in (Get-Tsv $df)) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 1) -ceq 'false-positive') { $sc = (Fld $rW 3) -split '\|'; if ($sc[0] -cne '') { if (-not $cN.ContainsKey($sc[0])) { $cN[$sc[0]] = 0 }; $cN[$sc[0]]++ } } }
    foreach ($k in $cN.Keys) {
        if ($cN[$k] -ge 3) {
            $nCal++
            Add-LfContent $cdt @(('CAL-{0:d3}' -f $nCal) + "`t" + 'disp-promotion' + "`t" + $k + "`t" + $k + "`t" + '-' + "`t" + $PVER + "`t" + "false-positive 处置同 scope 类段命中 $($cN[$k]) 次（≥3——晋升类页面 FP 卡候选，C-048）" + "`t" + '' + "`t" + 'pending') } } }
$DN = 0
$first = $true
foreach ($rW in (Get-Tsv $cdt)) { if ($first) { $first = $false; continue }; $DN++ }
Out-Lf "CALIBRATION 草案: $DN 行（$S/calibration-drafts.tsv——pattern_version=$PVER；LLM 判读一次补 draft_ere，人工批准后按 gensift-dev/registers/calibration.md 入册；写回只写默认套件 D-096）"

# ===== report: 投影终态报告 =====
. "$S/env.ps1"
# 处置 join 预计算（§10.2；两层分离 C-030：只在投影层 join，verdict 列不动）
$today = Get-GsDate
$dispRep = [System.Collections.Generic.List[string]]::new()
foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
    if (-not (Test-GsFile $df)) { continue }
    $first = $true
    foreach ($rW in (Get-Tsv $df)) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 0) -cne '') {
            $ex = 'active'; if ((Fld $rW 6) -cne '' -and ((Fld $rW 6) -clt $today)) { $ex = 'expired' }
            $dispRep.Add((Fld $rW 0) + "`t" + (Fld $rW 1) + "`t" + $ex + "`t" + (Fld $rW 6) + "`t" + (Fld $rW 4)) } } }
Set-LfContent (Join-Path $S 'tmp/disp-rep.tsv') $dispRep
$mfSet = @{}; $mfId = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; $mfSet[(Fld $rW 1)] = 1; $mfId[(Fld $rW 1)] = Fld $rW 0 }
$dCount = @{}
foreach ($l in $dispRep) { $a = $l -split "`t"; if ($mfSet.ContainsKey($a[0])) { $dCount[$a[1]] = 1 + ($(if ($dCount.ContainsKey($a[1])) { $dCount[$a[1]] } else { 0 })) } }
$rep = [System.Collections.Generic.List[string]]::new()
$rep.Add('# GenSift 审计报告')
$rep.Add("目标: $SRC")
$rep.Add('')
$rep.Add('## 概要（在役行——lifecycle 空才进分组；已翻案撤销单列披露）')
$rep.Add('| verdict | count |'); $rep.Add('|---|---|')
$vGrp = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq '') { $k2 = Fld $rW 2; if (-not $vGrp.ContainsKey($k2)) { $vGrp[$k2] = 0 }; $vGrp[$k2]++ } }
foreach ($k2 in ($vGrp.Keys | Sort-Ordinal)) { $rep.Add("| $k2 | $($vGrp[$k2]) |") }
$WD2 = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq 'withdrawn') { $WD2++ } }
$rep.Add("- 已翻案撤销 $WD2 条（lifecycle=withdrawn——mf 行留痕、文件撤 audit/reversed-*；不混入在役分组）")
$rep.Add('')
$rep.Add('## 处置（§10.2 两层分离——处置 join 投影，verdict 列不改写；标注型不抑制照常报告）')
$rep.Add('| disposition | 在役 findings |'); $rep.Add('|---|---|')
foreach ($o in @('false-positive', 'intended-behavior', 'compensating-control', 'accepted-risk', 'known-issue', 'duplicate', 'fixed')) {
    $c2 = 0; if ($dCount.ContainsKey($o)) { $c2 = $dCount[$o] }
    $rep.Add("| $o | $c2 |") }
$DMSN = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq '' -and (Fld $rW 2) -ceq 'dismissed') { $DMSN++ } }
if ($DMSN -gt 0) {
    $rep.Add('### dismissed 裁决（抑制型复核成立——引用处置 ID 见各 finding 头部 dismissed-cite 行，C-044）')
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq '' -and (Fld $rW 2) -ceq 'dismissed') { $rep.Add('- ' + (Fld $rW 0) + '（verdict=dismissed）') } } }
$rep.Add('### 标注型（accepted-risk/known-issue——不抑制，含到期日，C-045）')
$annLines = [System.Collections.Generic.List[string]]::new()
foreach ($l in $dispRep) {
    $a = $l -split "`t"
    if ($mfSet.ContainsKey($a[0]) -and ($a[1] -ceq 'accepted-risk' -or $a[1] -ceq 'known-issue')) {
        $annLines.Add('- ' + $mfId[$a[0]] + ' ' + $a[1] + '（' + $a[2] + '｜到期 ' + $a[3] + '｜批准 ' + $a[4] + '）') } }
if ($annLines.Count -gt 0) { foreach ($x in $annLines) { $rep.Add($x) } } else { $rep.Add('- （无标注型命中——处置库为空或指纹未命中在役行）') }
if (Test-GsFile (Join-Path $S 'audit/disposition-notice.log')) {
    $nr2 = @(@(Get-LfLines (Join-Path $S 'audit/disposition-notice.log')) | Where-Object { $_.StartsWith('NOTICE-REGRESSION') })
    if ($nr2.Count -gt 0) {
        $rep.Add('### fixed 回归高亮（C-046——已修复同指纹复现 → NOTICE，audit/disposition-notice.log）')
        foreach ($l in $nr2) { $rep.Add('  - ' + $l) } } }
$rep.Add('')
$rep.Add('## 验收不变量')
if (Test-GsFile (Join-Path $S 'audit/invariants.md')) {
    if (@(Get-LfLines (Join-Path $S 'audit/invariants.md')) | Where-Object { $_.Contains('FAIL') }) {
        $rep.Add('**存在 FAIL 项（如实披露，逐条见 audit/invariants.md）：**')
        foreach ($l in @(@(Get-LfLines (Join-Path $S 'audit/invariants.md')) | Where-Object { $_.Contains('FAIL') })) { $rep.Add('- ' + $l) } }
    else { $rep.Add('- 全部 PASS') } }
$rep.Add('')
$rep.Add('## 逐漏洞（severity 降序——在役行）')
$rank = @{ critical = 5; high = 4; medium = 3; low = 2; info = 1 }
$act2 = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 12) -ceq '') { $sc6 = 0; if ($rank.ContainsKey((Fld $rW 3))) { $sc6 = $rank[(Fld $rW 3)] }; $act2.Add("$sc6`t$(Join-Tsv $rW)") } }
$act2s = @(@($act2 | Sort-Ordinal) | Sort-Object -Stable -Descending -Property { [int](ConvertTo-GsNum (($_ -split "`t")[0])) })
foreach ($l in $act2s) {
    $a = (($l -split "`t", 2)[1]) -split "`t"
    $rep.Add('### [' + (Fld $a 3) + '] ' + (Fld $a 0))
    $rep.Add('- 类: ' + (Fld $a 4) + ' ｜ sink: ' + (Fld $a 5))
    $rep.Add('- 详情: findings/' + (Fld $a 0) + '.md')
    $rep.Add('') }
$rep.Add('### 已翻案撤销（withdrawn——留痕不删除，不混入上表）')
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq 'withdrawn') { $rep.Add('- ' + (Fld $rW 0) + '（' + (Fld $rW 2) + ' → 撤档 audit/reversed-' + (Fld $rW 0) + '*.md）') } }
$rep.Add('')
$rep.Add('## Human Triage（reasoning-only 类——无机械/执行 oracle，最终裁决交人工）')
$roList = [System.Collections.Generic.List[string]]::new()
foreach ($cp in (Get-GsGlob (Join-Path $SK 'classes') '*.md')) {
    if (@(Get-LfLines $cp) | Where-Object { $_.StartsWith('> oracle: none') }) { $roList.Add([IO.Path]::GetFileNameWithoutExtension($cp)) } }
$ro = ($roList | Sort-Ordinal) -join ' '
if ($ro -ceq '') { $ro = '（无——机械类全量）' }
$rep.Add("- reasoning-only 类集合: $(if ($ro -ceq '') { $ro } else { $ro + ' ' })")   # bash tr '\n' ' ' 尾空格
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 11) -ceq 'yes' -and (Fld $rW 2) -cne 'refuted' -and (Fld $rW 2) -cne 'dismissed') { $rep.Add('  - [' + (Fld $rW 3) + '] ' + (Fld $rW 0) + '（' + (Fld $rW 2) + '）→ 人工 triage') } }
$rep.Add('- 旧会话 10 列 machine-fields 无该列时上表为空——以类页面标记重新核对')
Set-LfContent (Join-Path $S 'report.md') $rep
# ── coverage.md ──
$cov = [System.Collections.Generic.List[string]]::new()
# bash：ASCII 双引号在双引号串内做相邻拼接——引号脱落，逐字对齐
$cov.Add('# Coverage（没发现必须能解释）')
$cov.Add('')
$cov.Add('## 1 卡状态分布')
$cov.Add('| state | count |'); $cov.Add('|---|---|')
$stGrp = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ($first) { $first = $false; continue }; $k3 = Fld $rW 4; if (-not $stGrp.ContainsKey($k3)) { $stGrp[$k3] = 0 }; $stGrp[$k3]++ }
foreach ($k3 in ($stGrp.Keys | Sort-Ordinal)) { $cov.Add("| $k3 | $($stGrp[$k3]) |") }
$cov.Add('')
$cov.Add('## 2 类×语言检测可得性（无 pattern 的格子=该类该语言零检测；语言列由 langpacks/ 目录自派生——协议零语言假设）')
$LANGSa = @((Get-ChildItem -LiteralPath (Join-Path $SK 'langpacks') -Directory | ForEach-Object { $_.Name } | Sort-Ordinal))
$LANGS = ($LANGSa -join ' ') + ' '                    # bash tr '\n' ' '：尾空格保留（表头/分隔行形态逐字对齐）
$cov.Add('| class | ' + ($LANGS -creplace ' ', ' | ') + ' |')
$cov.Add('|---|' + ('---|' * $LANGSa.Count))
$clsSet = [System.Collections.Generic.List[string]]::new()
foreach ($p4 in (Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')) {
    $bn = [IO.Path]::GetFileName($p4) -creplace '-[^-]*\.pattern$', ''
    if (-not ($clsSet -ccontains $bn)) { $clsSet.Add($bn) } }
foreach ($c4 in ($clsSet | Sort-OrdinalU)) {
    $line4 = "| $c4 "
    foreach ($l4 in $LANGSa) {
        if (Test-GsFile (Join-Path $SK "classes/patterns/$c4-$l4.pattern")) { $line4 += '| ✓ ' } else { $line4 += '| ✗ ' } }
    $cov.Add($line4 + '|') }
$cov.Add('')
$cov.Add("（本 run 实际扫过的语言: $LANGS）")
$cov.Add('')
$cov.Add('## 3 未覆盖文件类型（全库后缀 − 已入清单后缀 的差集——差集里的类型零卡零检测）')
$covsuf = [System.Collections.Generic.List[string]]::new()
foreach ($incf in (Get-GsGlob (Join-Path $SK 'langpacks') '*/includes.txt')) { foreach ($g5 in (Get-GsIncludes $incf)) { $covsuf.Add($g5) } }
foreach ($g5 in @('*.yml', '*.yaml', '*.jinja2', '*.xml', '*.md', '*.txt', '*.json', '*.lock', '*.log', '*.gitignore')) { $covsuf.Add($g5) }
$covSet = @{}
foreach ($g5 in ($covsuf | Sort-OrdinalU)) { $m5 = [regex]::Match($g5, '^\*\.([A-Za-z0-9]+)$'); if ($m5.Success) { $covSet[$m5.Groups[1].Value] = 1 } }
$sufCount = @{}
foreach ($f5 in (Find-GsFiles $SRC @())) {
    $m5 = [regex]::Match([IO.Path]::GetFileName($f5), '.*\.([A-Za-z0-9]+)$')
    if ($m5.Success) { $k5 = $m5.Groups[1].Value; if (-not $sufCount.ContainsKey($k5)) { $sufCount[$k5] = 0 }; $sufCount[$k5]++ } }
foreach ($k5 in ($sufCount.Keys | Sort-OrdinalDesc)) {
    if (-not $covSet.ContainsKey($k5)) { $cov.Add("- .$k5 ×$($sufCount[$k5])（零检测）") } }
$covAdd = (($covSet.Keys | Sort-Ordinal) -join ' ') + ' '        # bash tr '\n' ' '：尾空格保留
$cov.Add("- 上表为空=目标库无清单外代码类型；已入清单后缀=$covAdd")
$cov.Add('')
$cov.Add('## 3b generated 清单（A-067/A-068：role=generated 只免 term 卡，sink/source grep 照跑；命中非零须人工签字豁免）')
$cov.Add('| file | sink模式命中 | 人工签字 |')
$cov.Add('|---|---|---|')
$NG = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -ceq 'generated') {
        $gf = Fld $rW 1; $NG++
        $n6 = 0
        $first2 = $true
        foreach ($r2 in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
            if ($first2) { $first2 = $false; continue }
            if (((Fld $r2 2)).StartsWith($gf + ':')) { $n6++ } }
        $cov.Add("| $gf | $n6 | （空=未豁免） |") } }
if ($NG -eq 0) { $cov.Add('| （无 generated 文件） | - | - |') }
$cov.Add('')
$cov.Add('## 4 blocked/partial/deferred 恢复入口（C-Inv15 结构化：状态+缺口原因+重派入口；deferred 同列）')
$first = $true
$rcLines = @()
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 4) -ceq 'blocked' -or (Fld $rW 4) -ceq 'partial' -or (Fld $rW 4) -ceq 'deferred') {
        $rcLines += '- ' + (Fld $rW 0) + ' [' + (Fld $rW 4) + '] 缺口: ' + (Fld $rW 5) + ' → 重派入口: 分片 ' + (Fld $rW 0) + '（重派=2b ext/普通分支按 kind；blocked 的 at:file:line 见 reason）' } }
foreach ($x in ($rcLines | Select-Object -First 30)) { $cov.Add($x) }
$defN = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 4) -ceq 'deferred') { $defN++ } }
$cov.Add("- deferred 卡（ext 专属——证据需带外输入）: $defN 张；空=无")
$cov.Add('')
$cov.Add('## 4b K 规则分布（C-010①：refuted/no_path/not_applicable/blocked 按 K 规则归因计数）')
$kGrp = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -cmatch '^k[0-9]') { $kx = ((Fld $rW 5) -split ':')[0]; if (-not $kGrp.ContainsKey($kx)) { $kGrp[$kx] = 0 }; $kGrp[$kx]++ } }
if ($kGrp.Count -eq 0) { $cov.Add('| （无 K 消卡在案） | 0 |') }
foreach ($kx in ($kGrp.Keys | Sort-Ordinal)) { $cov.Add("| $kx | $($kGrp[$kx]) |") }
$cov.Add('（K1 uncontrolled→refuted / K1b intended→not_applicable / K2 kills→blocked / K3 no_edge / K4 dead——只关 band2 卡）')
$cov.Add('')
$cov.Add('## 4c dangling joins 与 guard 离群（B-093/B-145：发散输入全口径——无对端/未知防护段如实披露）')
$jn2 = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) { if ($first) { $first = $false; continue }; $jn2++ }
$fuN = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'ext' -and ((Fld $rW 3)) -cmatch '^JN-') { $fuN++ } }
$dgN = 0; if (Test-GsFile (Join-Path $S 'tmp/joins-dangling.txt')) { $dgN = @(Get-LfLines (Join-Path $S 'tmp/joins-dangling.txt')).Count }
$cov.Add("- joins.tsv: $jn2 行 ｜ follow-up 卡（origin_ref=JN-*）: $fuN 张 ｜ dangling: $dgN 行（egress/ingress 无对端——L2 frontier 已入发散输入）")   # 与 bash 修复同步：wc 结果经 tr 剥离=裸整数
if (Test-GsFile (Join-Path $S 'tmp/joins-dangling.txt')) { foreach ($l in (@(Get-LfLines (Join-Path $S 'tmp/joins-dangling.txt')) | Select-Object -First 20)) { $cov.Add('  - dangling ' + $l) } }
$guN = 0; $guT = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $guT++
    if ((Fld $rW 6) -cmatch 'unknown') { $guN++ } }
$cov.Add("- guard 离群源（guards 五段含 unknown）: $guN / $guT")
$first = $true
$ol = @()
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 6) -cmatch 'unknown') { $ol += '  - 离群 ' + (Fld $rW 0) + ' ' + (Fld $rW 2) + ' guards=' + (Fld $rW 6) } }
foreach ($x in ($ol | Select-Object -First 20)) { $cov.Add($x) }
$cov.Add('')
$cov.Add('## 4d 不变式评估覆盖矩阵（B-088⑬：INV 卡 × module × 终态——每格下场可查）')
$cov.Add('| inv×module | 终态分布 |'); $cov.Add('|---|---|')
$invRows = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    # bash sub(/^CK-ext-/,"",k)：剥 7 字符前缀
    if ((Fld $rW 1) -ceq 'ext' -and (Fld $rW 0) -cmatch '^CK-ext-INV-') { $invRows.Add(((Fld $rW 0).Substring(7)) + "`t" + (Fld $rW 4)) } }
$invSorted = @($invRows | Sort-Ordinal)
$invGrp = [ordered]@{}
foreach ($l in $invSorted) { $a = $l -split "`t"; $key = $a[0] + '|' + $a[1]; if (-not $invGrp.Contains($key)) { $invGrp[$key] = 0 }; $invGrp[$key]++ }
$invKeys = [ordered]@{}
foreach ($key in $invGrp.Keys) { $ik = ($key -split '\|')[0]; if (-not $invKeys.Contains($ik)) { $invKeys[$ik] = '' } }
foreach ($ik in ($invKeys.Keys | Sort-Ordinal)) {
    $lineK = ''
    foreach ($key in $invGrp.Keys) { $a = $key -split '\|'; if ($a[0] -ceq $ik) { $lineK += ' ' + $a[1] + '=' + $invGrp[$key] } }
    $cov.Add("| $ik |$lineK |") }
if ($invSorted.Count -eq 0) { $cov.Add('| （无 INV ext 卡——L2 不变式轨未发卡或已全闭合清档） | - |') }
$cov.Add('')
$cov.Add('## 5 G1 锚点与 CVE/advisory 种子行')
if (Test-GsFile (Join-Path $S 'audit/g1.md')) { foreach ($l in @(Get-LfLines (Join-Path $S 'audit/g1.md'))) { $cov.Add($l) } } else { $cov.Add('- G1 未跑') }
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 1) -ceq 'G1') { $cov.Add('- 种子行 ' + (Fld $rW 0) + ' verdict_state=' + (Fld $rW 6) + ' loc=' + (Fld $rW 5)) } } }
$cov.Add('- 种子行闭合规则（A-086）：只有本地证据独立支持/证伪才许改 state（closed-by-evidence/refuted-by-evidence）；邻近 finding 不替代闭合')
$cov.Add('')
$cov.Add('## 6 ext 卡与不变式轨')
$EXT_T = 0; $EXT_C = 0; $EXT_D = 0; $invN = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ((Fld $rW 1) -ceq 'ext') {
        $EXT_T++
        if ((Fld $rW 0) -cmatch 'INV') { $invN++ }
        if ((Fld $rW 4) -cne 'unchecked') { $EXT_C++ }
        if ((Fld $rW 4) -ceq 'deferred') { $EXT_D++ } } }
$cov.Add("- ext 卡: $EXT_T（含 INV 卡 $invN，INV 按 invariant×module 发卡）")
$cov.Add("- ext 闭合率: $EXT_C/$EXT_T（ext 不计入分母覆盖率，单独披露——A-057）｜ deferred: $EXT_D（零 deferred 为理想终态口径，非零如实披露）")
$cntS = { param($et) $c = 0; $first2 = $true; foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ($first2) { $first2 = $false; continue }; if ((Fld $rW 3) -ceq $et) { $c++ } }; $c }
$dwN = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'fw' -and (Fld $rW 0) -cmatch '^CK-fw-P') { $dwN++ } }
$cov.Add("- 弱源入账未发卡: weak=$(& $cntS 'weak') ｜ persisted_read=$(& $cntS 'persisted_read')（demand 追踪卡 $dwN 张） ｜ external_message=$(& $cntS 'external_message') ｜ lib_api=$(& $cntS 'lib_api')（库模式公共 API 面：入清单不预发 fw 卡——fw 通道只剩 demand 追踪卡，如实披露）")
$famN = 0; if (Test-GsFile (Join-Path $S 'audit/family-corrections.tsv')) { $famN = @(Get-LfLines (Join-Path $S 'audit/family-corrections.tsv')).Count }   # 与 bash 修复同步：缺失=0
$cov.Add("- family 修正 diff: $famN 行（audit/family-corrections.tsv）")
$rfN = 0; if (Test-GsFile (Join-Path $S 'audit/refreeze.log')) { $rfN = @(Get-LfLines (Join-Path $S 'audit/refreeze.log')).Count }   # 与 bash 修复同步：缺失文件=0（不再是空串）
$cov.Add("- refreeze 记录: $rfN 行（audit/refreeze.log；ext 卡不触发 refreeze）")
$cov.Add('')
$cov.Add('## 7 降级与平台缺口（如实披露）')
foreach ($l in @(Get-LfLines (Join-Path $S 'audit/coverage-degraded.log'))) { if ($l -cne '') { $cov.Add('- ' + $l) } }   # bash cat|sed：缺文件输出空、无 fallback 行
$cov.Add('- 级联收益 K1/K1b/K2/K3/K4（uncontrolled→refuted / intended→not_applicable / kills→blocked（reason 记 at:file:line 恢复入口）/ no_edge→no_path / dead(reflection_checked 非空)→no_path——只关 band2 卡，机械匹配只认 scope 两列）')
$RLOGN = 0; if (Test-GsFile (Join-Path $S 'audit/retract.log')) { $RLOGN = @(@(Get-LfLines (Join-Path $S 'audit/retract.log')) | Where-Object { $_.StartsWith('RETRACT') }).Count }
$cov.Add("- 撤销留痕: $RLOGN 行（audit/retract.log——翻案→派生事实级联撤销→K 关闭卡重置 unchecked；L1 回升仅此通道合法）")
$roleGrp = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; $rk2 = Fld $rW 5; if (-not $roleGrp.ContainsKey($rk2)) { $roleGrp[$rk2] = 0 }; $roleGrp[$rk2]++ }
$roleStr = ''
foreach ($rk2 in ($roleGrp.Keys | Sort-Ordinal)) { $roleStr += "$rk2=$($roleGrp[$rk2]) " }
$cov.Add("- role 分布: $roleStr（term 卡只发 role∈{app,config}；secrets 例外：test/vendor 路径 sink 照发 bw 卡）")
$cov.Add("- ext deferred: $EXT_D（证据需带外输入，如实披露不阻塞交付）")
$bN = 0; $uN = 0
if (Test-GsFile (Join-Path $S 'audit/guard-bind-review.log')) {
    foreach ($rW in (Get-Tsv (Join-Path $S 'audit/guard-bind-review.log'))) { if ((Fld $rW 1) -ceq 'bound') { $bN++ }; if ((Fld $rW 1) -ceq 'unbound') { $uN++ } } }
$cov.Add("- guard 三跳复核（B-082）: bound=$bN ｜ unbound=$uN（audit/guard-bind-review.log；unbound=绑定失效族如实披露，不翻账）")
$calN = 0; if (Test-GsFile $cdt) { $first = $true; foreach ($rW in (Get-Tsv $cdt)) { if ($first) { $first = $false; continue }; $calN++ } }
$cov.Add("- CALIBRATION 草案（知识闭环）: $calN 行（$S/calibration-drafts.tsv——真值外新发现/pattern 误报/处置晋升三路候补；LLM 判读一次+人工批准后按 gensift-dev/registers/calibration.md 入册）")
$rsS = 0; if (Test-GsFile (Join-Path $S 'audit/reversal-sampled.tsv')) { $rsS = @(Get-LfLines (Join-Path $S 'audit/reversal-sampled.tsv')).Count - 1 }
$rrS = 0; if (Test-GsFile (Join-Path $S 'audit/reversal-reviewed.tsv')) { $rrS = @(Get-LfLines (Join-Path $S 'audit/reversal-reviewed.tsv')).Count - 1 }
$rvS = 0
if (Test-GsFile (Join-Path $S 'audit/reversal-reviewed.tsv')) { foreach ($rW in (Get-Tsv (Join-Path $S 'audit/reversal-reviewed.tsv'))) { if ((Fld $rW 1) -ceq 'reversed') { $rvS++ } } }
$cov.Add("- 对称反转复核（B-020）: 已抽样 $rsS 张 ｜ 已复核 $rrS 张 band0/1 refuted/no_path 卡（reversed $rvS 张——卡重置 unchecked 重走五步，旧 finding 的 mf 行 lifecycle=withdrawn（行保留）+文件撤 audit/reversed-*；已抽样>已复核=派发后未回收，如实披露）")
$cov.Add('')
$cov.Add('## 7b 处置统计（§10.2——C-047/C-010：FP 率/accept 存量/过期清单）')
$NGD = 0
if (Test-GsFile (Join-Path $SK 'feedback/dispositions.tsv')) { $first = $true; foreach ($rW in (Get-Tsv (Join-Path $SK 'feedback/dispositions.tsv'))) { if ($first) { $first = $false; continue }; $NGD++ } }
$RLD = 0
if (Test-GsFile (Join-Path $S 'feedback/dispositions.tsv')) { $first = $true; foreach ($rW in (Get-Tsv (Join-Path $S 'feedback/dispositions.tsv'))) { if ($first) { $first = $false; continue }; $RLD++ } }
$cov.Add("- 处置库: 全局 $NGD 行（`$SK/feedback/）+ 本 run $RLD 行（`$S/feedback/——A4 落行，批后合并: gensift-dev/feedback-global/merge-pending.sh）")
$DTOT = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; $DTOT++ }
$g = { param($o) $(if ($dCount.ContainsKey($o)) { $dCount[$o] } else { 0 }) }
$cov.Add("- 处置命中（在役 join，含已过期）: false-positive=$(& $g 'false-positive')｜accepted-risk=$(& $g 'accepted-risk')｜known-issue=$(& $g 'known-issue')｜intended-behavior=$(& $g 'intended-behavior')｜compensating-control=$(& $g 'compensating-control')｜duplicate=$(& $g 'duplicate')｜fixed=$(& $g 'fixed')")
$fpRate = 0.0
$fpRate = '0.0'
if ($DTOT -gt 0) { $fpN = & $g 'false-positive'; $fpRate = '{0:F1}' -f ($fpN * 100.0 / $DTOT) }   # awk printf %.1f
$cov.Add("- FP 率: $fpRate%（false-positive $(& $g 'false-positive') / 在役 $DTOT——操作者反馈口径，非 ground truth；G2 抽检另计）")
$accN = (& $g 'accepted-risk') + (& $g 'known-issue')
$cov.Add("- accept 存量: $accN（accepted-risk $(& $g 'accepted-risk') + known-issue $(& $g 'known-issue')——标注型不抑制；门禁计存量不计新增，gate.json 投影 P2 二期）")
$EXPN = 0
foreach ($l in $dispRep) { $a = $l -split "`t"; if ($a[2] -ceq 'expired') { $EXPN++ } }
$cov.Add("- 过期处置: $EXPN 行（复核到期已过——降级 hint 抑制力失效，待复核不自动删除，C-043；清单如下）")
$exLines = @()
foreach ($l in $dispRep) { $a = $l -split "`t"; if ($a[2] -ceq 'expired') { $exLines += '  - ' + $a[0] + ' ' + $a[1] + ' 到期=' + $a[3] + ' 批准=' + $a[4] } }
foreach ($x in ($exLines | Select-Object -First 20)) { $cov.Add($x) }
if ($EXPN -eq 0) { $cov.Add('  - （无过期处置在库）') }
$cov.Add('')
$cov.Add('## 8 库模式与入口画像')
$LB = @((Join-Path $S 'recon/app-or-lib.md'), (Join-Path $S 'recon/lib-or-app.md')) | Where-Object { Test-GsFile $_ } | Select-Object -First 1
if ($null -ne $LB) {
    # bash `head -3 | tr '\n' '；'`：BSD tr 按字节映射——换行→全角分号首字节 0xEF（逐字对齐）
    $lbLines = @(Get-LfLines $LB) | Select-Object -First 3
    $lbTxt = ($lbLines -join [string][char]0xEF) + [string][char]0xEF
    $cov.Add("- 库/应用判定: $lbTxt") }
else { $cov.Add('- 库/应用判定: （recon 未产出——分母按应用模式计）') }
if (Test-GsFile (Join-Path $S 'recon/app-or-lib.md')) {
    if (@(Get-LfLines (Join-Path $S 'recon/app-or-lib.md')) | Where-Object { $_ -cmatch '^verdict: lib' }) { $cov.Add('- 分母强度: 机械+语义混合（库模式——source=公共 API 面/调用方传入点/共享类型，guards 语义弱，如实声明）') }
    else { $cov.Add('- 分母强度: 机械枚举（应用模式）') } }
else { $cov.Add('- 分母强度: 机械枚举（应用模式）') }
$fwN2 = 0; $siT = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $siT++
    if ((Fld $rW 4) -cne 'unknown') { $fwN2++ } }
$cov.Add("- framework 回填: $fwN2/$siT（unknown=未识别）")
$cov.Add("- guards 五段仍 unknown 的入口数: $guN / $guT")
$cov.Add('- 未交付候选（delivery_state=pending/其他）:')
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 7) -cne 'delivered' -and (Fld $rW 7) -cne 'degraded') { $cov.Add('  - ' + (Fld $rW 0) + ' verdict=' + (Fld $rW 6) + ' delivery=' + (Fld $rW 7) + ' loc=' + (Fld $rW 5)) } }
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 7) -ceq 'degraded') { $cov.Add('  - ' + (Fld $rW 0) + ' delivery=degraded（Verifier 两轮未产出合法裁决）') } } }
$cov.Add('- 平台: 双分支——bash 可用走 POSIX 块（SKILL.md 发起）/ Windows 原生走 .ps1（phases/win-init.md 发起）；黄金等价已验（gensift-dev/replays/golden 58+ 块逐块双跑）')
$cov.Add('- 战果口径（C-016）：确认修复率为最硬证据；复现已披露 CVE 仅辅助（无法排除训练记忆）——修复验证用例=finding 第 7 节验收用例（5d Reporter 纪律），修复回归以该用例重跑为准')
$modcR = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $mv = Fld $rW 4
    if ($mv -cmatch '^mod:') { $modcR.Add($mv.Substring(4)) } }                        # F1：只认 mod: 语义模块（与 J1 同口径）
$MODC2 = @($modcR | Sort-OrdinalU).Count
$cov.Add("- 组合件（D-055 存在性投影）: combinations.md $(if ((Test-GsFile (Join-Path $S 'combinations.md')) -and (Get-Item -LiteralPath (Join-Path $S 'combinations.md')).Length -gt 0) { "在档 $(@(Get-LfLines (Join-Path $S 'combinations.md')).Count) 行（W5 阶段性刷新——语义层，G3 软保证）" } else { if ($MODC2 -lt 2) { 'N/A（单模块——组合件通道未开，与 J1 同口径不记降级）' } else { '未产出（降级在案——audit/coverage-degraded.log）' } })")
$cov.Add("- 拼链账本（B-122/B-142）: joins.tsv $jn2 行（Egress=契约=Ingress；assumptions→follow-up 卡 $fuN 张；dangling 见 4c）")
$cov.Add('- 偏差记录（B-141/B-214，登记在案）：findings/*+machine-fields 由主循环 5a 机械投影产出（设计 §9 归 Reporter 单写）——骨架与证据链是纯投影非创作，语义扩写归 Reporter 5d；语义合并/joins/combinations 的语义判定归 Reporter、账本迁移归主循环协议命令（两写者分工已在 reporter.md 同步）')
$cov.Add("- 未实现机制: 基准矩阵 M2-M4 分级资产（任务11 终审联动，C-015）｜ gate.json 门禁投影（C-045 P2 二期——标注型计存量不计新增）——CALIBRATION 草案通道已落（$S/calibration-drafts.tsv 三路候补+gensift-dev/registers/calibration.md 入册格式）；处置账本 dispositions §10.2 已落（feedback/dispositions.tsv 八列账本+2e 信封 join+live/report/coverage 三处投影+批后合并通道）；G2 闭卷/G3 双跑/语义合并/joins/combinations 已落（audit/g2.md、audit/stability-diff.md、2d 合并轮、phases/joins.md）")
$cov.Add('')
$cov.Add('## 9 调度与派发口径')
$cov.Add('- band2 路径（v1.4.0-S5 已裁决入设计）: band2 bw 卡同走 2b Analyzer 五步 + 2c Summarizer 级联燃料——宁多勿漏，成本在 run-estimate 披露')
$cov.Add('- 排序保底（v1.4.0-S6 已裁决入设计）: 每轮固定补 fw/term/ext 各 1 张——band0 主导 + 完备性保底')
# D4-A 队尾降权披露（与 bash coverage §9 同式）：test/demo 角色 bw 卡数量与占比
$sfT = @{}; $first = $true
foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ($first) { $first = $false; continue }; $sfT[(Fld $sr 0)] = ((Fld $sr 2) -split ':')[0] }
$tdSet2 = @{}; $first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 5) -ceq 'test' -or (Fld $rW 5) -ceq 'demo') { $tdSet2[(Fld $rW 1)] = 1 } }
$TD_A = 0; $TD_T = 0; $first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw') { $TD_T++; if ($sfT.ContainsKey((Fld $rW 2)) -and $tdSet2.ContainsKey($sfT[(Fld $rW 2)])) { $TD_A++ } } }
$TD_P = 0; if ($TD_T -gt 0) { $TD_P = [math]::Floor($TD_A * 100 / $TD_T) }
$cov.Add("- D4-A test/demo 队尾降权（v2.1）: bw 卡中 test/demo 角色文件 $TD_A/$TD_T 张（$TD_P%）——不剔除（覆盖红线），score=-1 全局排尾；存量会话自动生效（checks 不动，step1 过滤）")
# D4-D 负向降权在案快照（终态重算同口径——step1 每轮 tmp 信号的一致性对账面）
$NNF = 0; if (Test-GsFile (Join-Path $S 'tmp/sig-negfile.tsv')) { $NNF = @(@(Get-LfLines (Join-Path $S 'tmp/sig-negfile.tsv')) | Where-Object { $_ -cne '' }).Count }
$NNC = 0; if (Test-GsFile (Join-Path $S 'tmp/sig-negcls.tsv')) { $NNC = @(@(Get-LfLines (Join-Path $S 'tmp/sig-negcls.tsv')) | Where-Object { $_ -cne '' }).Count }
$cov.Add("- D4-D 负向降权（v2.1）: 文件级证伪密度命中 $NNF 文件（refuted≥80%∧≥3 → 剩余卡 −30）｜ 同理由聚类命中 $NNC 组（同文件同类 refuted≥3 → −20）｜ suspicion uncontrolled +25（D4-D 校准）")
$PTOT = 0; $PPAR = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -cne 'ext') { $PTOT++; if ((Fld $rW 4) -ceq 'partial') { $PPAR++ } } }
$PPCT = 0; if ($PTOT -gt 0) { $PPCT = [math]::Floor($PPAR * 100 / $PTOT) }
$cov.Add("- partial/blocked 阈值（D-086）: partial $PPAR/$PTOT = $PPCT%——>10% 阻断全闭合宣称（EXIT_CODE=2）；≤10% 质量缺口如实披露不阻断；blocked 不计缺口（K2 kills 有恢复入口的合法态）")
if (Test-GsFile (Join-Path $S 'audit/plateau.flag')) {
    $cov.Add('- Plateau 强制停轮（B-074/D-087）: ' + (@(Get-LfLines (Join-Path $S 'audit/plateau.flag'))[0]) + '——剩余 unchecked 如实披露，不许谎称全绿') }
else { $cov.Add('- Plateau: 未触发（mf 指纹轨迹见 audit/mf-fp.log）') }
Set-LfContent (Join-Path $S 'coverage.md') $cov
Set-LfContent (Join-Path $S 'STATE') @('done')
# 退出码（C-017）
$EC = 0
$hasI2Fail = $false
if (Test-GsFile (Join-Path $S 'audit/invariants.md')) { $hasI2Fail = [bool](@(Get-LfLines (Join-Path $S 'audit/invariants.md')) | Where-Object { $_ -cmatch '^I2 冻结: FAIL' }) }
$g2Fail = $false
if (Test-GsFile (Join-Path $S 'audit/g2.md')) { $g2Fail = [bool](@(Get-LfLines (Join-Path $S 'audit/g2.md')) | Where-Object { $_ -cmatch '^结果: FAIL' }) }
$i18Fail = $false
if (Test-GsFile (Join-Path $S 'audit/invariants.md')) { $i18Fail = [bool](@(Get-LfLines (Join-Path $S 'audit/invariants.md')) | Where-Object { $_ -cmatch '^I18 双跑稳定: FAIL' }) }
$U_E = 0; $UE_E = 0; $DEG = 0; $TOT_E = 0; $PAR_E = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $kd2 = Fld $rW 1
    if ($kd2 -cne 'ext') { $TOT_E++; if ((Fld $rW 4) -ceq 'unchecked') { $U_E++ }; if ((Fld $rW 4) -ceq 'partial') { $PAR_E++ } }
    else { if ((Fld $rW 4) -ceq 'unchecked') { $UE_E++ } } }
if (Test-GsFile (Join-Path $S 'audit/coverage-degraded.log')) { $DEG = @(@(Get-LfLines (Join-Path $S 'audit/coverage-degraded.log')) | Where-Object { $_ -cne '' }).Count }
$PCT_E = 0; if ($TOT_E -gt 0) { $PCT_E = [math]::Floor($PAR_E * 100 / $TOT_E) }
if ($hasI2Fail) { $EC = 3 }
elseif ($g2Fail -or $i18Fail) { $EC = 3 }
elseif ((Test-GsFile (Join-Path $S 'EXIT_CODE')) -and (@(Get-LfLines (Join-Path $S 'EXIT_CODE'))[0]) -ceq '1') { $EC = 1 }
elseif ($U_E -gt 0 -or $UE_E -gt 0 -or $DEG -gt 0 -or (Test-GsFile (Join-Path $S 'audit/plateau.flag')) -or $PCT_E -gt 10) { $EC = 2 }
Set-LfContent (Join-Path $S 'EXIT_CODE') @("$EC")
Add-LfContent (Join-Path $S 'coverage.md') @("- 退出码: $EC（0=全闭合 1=L1违例 2=有披露未全闭合 3=I2 FAIL——语义见 README）")
Out-Lf "EXIT_CODE=$EC（0=全闭合 1=L1违例 2=有披露未全闭合 3=I2 FAIL——语义见 README）"

# ===== metrics: 指标计算与报告（A-018——三指标量化，门内禁声约束） =====
. "$S/env.ps1"
$SEED_T = 0; $SEED_C = 0; $SEED_R = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ((Fld $rW 1) -ceq 'G1') {
            $SEED_T++
            if ((Fld $rW 6) -ceq 'closed-by-evidence') { $SEED_C++ }
            if ((Fld $rW 6) -ceq 'refuted-by-evidence') { $SEED_R++ } } } }
$G1ST = 0
if (Test-GsFile (Join-Path $S 'audit/g1.md')) { $G1ST = @(@(Get-LfLines (Join-Path $S 'audit/g1.md')) | Where-Object { $_ -cmatch '结果: PASS' }).Count }
$met = [System.Collections.Generic.List[string]]::new()
$met.Add('')
$met.Add('## 指标（A-018 三指标量化——门内禁声约束下）')
$met.Add("- 召回（锚点事实计数）: 锚点闭合 $SEED_C/$SEED_T（另锚点证伪 $SEED_R）｜G1 门: $(if ($G1ST -gt 0) { 'PASS' } else { 'N/A（无锚点输入）' })——种子行口径，非全量召回声明")
$met.Add('- 误报: G2 闭卷抽检未跑——禁声（precision 需人工标注抽检，机械层不出数值）')
$g3There = (Test-GsFile (Join-Path $S 'audit/stability-diff.md')) -and [bool](@(Get-LfLines (Join-Path $S 'audit/stability-diff.md')) | Where-Object { $_ -cmatch '^G3: ' }) -and -not [bool](@(Get-LfLines (Join-Path $S 'audit/stability-diff.md')) | Where-Object { $_ -cmatch '^G3: N.A.' })
if ($g3There) { $met.Add('- 稳定: G3 双跑在档——diff 与 confirmed 重合度见 audit/stability-diff.md') }
else { $met.Add('- 稳定: G3 双跑未跑——禁声') }
if ($G1ST -gt 0 -and $g3There -and [bool](@(Get-LfLines (Join-Path $S 'audit/stability-diff.md')) | Where-Object { $_ -cmatch '^G3: PASS' })) {
    $met.Add('- 三门状态：G1 PASS ｜ G3 在档——指标结论按 stability-diff.md + G2 抽检记录出具（M4 基准后接指标计算）') }
else { $met.Add('- 门内禁声：G2/G3 未全绿，本报告不声称召回/误报/稳定指标（§16——设计失败可证伪）') }
Add-LfContent (Join-Path $S 'report.md') $met
# I16（C-Inv16，report 写后复核）：报告概要分组计数 == mf 在役分组计数
$mfG = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq '') { $k6 = Fld $rW 2; if (-not $mfG.ContainsKey($k6)) { $mfG[$k6] = 0 }; $mfG[$k6]++ } }
$repG = @{}
foreach ($l in @(Get-LfLines (Join-Path $S 'report.md'))) {
    if ($l -cmatch '^\| (confirmed|unconfirmed|refuted|dismissed) \| [0-9]+ \|$') {
        $a = $l -split '\|'
        $v = ($a[1]).Trim(' '); $repG[$v] = [int]$a[2] } }
$B16 = 0
foreach ($k6 in $mfG.Keys) { if (-not $repG.ContainsKey($k6) -or $repG[$k6] -cne $mfG[$k6]) { $B16++ } }
foreach ($k6 in $repG.Keys) { if (-not $mfG.ContainsKey($k6)) { $B16++ } }
Out-GsTee (Join-Path $S 'audit/invariants.md') ("I16 报告投影: $(if ($B16 -eq 0) { 'PASS' } else { "FAIL($B16)" })｜边界: —")
# C-064：完成声明=原始输出留档 report 附录
$apx = [System.Collections.Generic.List[string]]::new()
$apx.Add('')
$apx.Add('## 附录：不变量与门的原始输出（C-064——逐行原文留档，不摘要不改写）')
$apx.Add('### audit/invariants.md')
if (Test-GsFile (Join-Path $S 'audit/invariants.md')) { foreach ($l in @(Get-LfLines (Join-Path $S 'audit/invariants.md'))) { $apx.Add($l) } }
$apx.Add('### audit/g2.md（G2 闭卷对账）')
if (Test-GsFile (Join-Path $S 'audit/g2.md')) { foreach ($l in @(Get-LfLines (Join-Path $S 'audit/g2.md'))) { $apx.Add($l) } } else { $apx.Add('（未产出）') }
$apx.Add('### audit/stability-diff.md（G3——双跑时）')
if (Test-GsFile (Join-Path $S 'audit/stability-diff.md')) { foreach ($l in @(Get-LfLines (Join-Path $S 'audit/stability-diff.md'))) { $apx.Add($l) } } else { $apx.Add('（单跑未产出）') }
Add-LfContent (Join-Path $S 'report.md') $apx

# ===== mermaid: 账本→图投影（A-142——只读件，不回灌账本） =====
. "$S/env.ps1"
$mm = [System.Collections.Generic.List[string]]::new()
$mm.Add('# 账本 mermaid 投影（机械生成——仅供人读；禁止作为任何账本/判定的输入回灌）')
$mm.Add('```mermaid')
$mm.Add('flowchart LR')
$first = $true
$n8 = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 12) -ceq '') {
        $n8++
        if ($n8 -le 200) { $mm.Add('  ' + (Fld $rW 0) + '["' + (Fld $rW 0) + ' ' + (Fld $rW 3) + ' ' + (Fld $rW 4) + '"]') } } }
$n9 = 0
if (Test-GsFile (Join-Path $S 'joins.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) {
        if ($first) { $first = $false; continue }
        $n9++
        if ($n9 -le 100) {
            $e9 = Fld $rW 1; if ($e9 -ceq 'NA') { $e9 = 'dangling' }
            $i9 = Fld $rW 3; if ($i9 -ceq 'NA') { $i9 = 'dangling' }
            $w9 = ''; if ((Fld $rW 5) -cne '') { $w9 = ' ⚠' }
            $mm.Add('  ' + $e9 + ' -->|"' + (Fld $rW 0) + ' ' + (Fld $rW 4) + $w9 + '"| ' + $i9) } } }
$mm.Add('```')
Set-LfContent (Join-Path $S 'audit/graph-mermaid.md') $mm
Out-Lf "mermaid 投影: $($mm.Count) 行（audit/graph-mermaid.md——只读件）"

# ===== desensitize: 脱敏扫描（C-006） =====
. "$S/env.ps1"
$ds = [System.Collections.Generic.List[string]]::new()
$ds.Add('# 脱敏扫描（C-006——session 目录按含源码级敏感数据等级处置；归档共享前必跑）')
$ds.Add('- 扫描口径: findings/combinations/shards/audit 中 ≥32 位连续字母数字+/ 串（潜在密钥/token）')
$N7 = 0
$scanFiles = @()
foreach ($p7 in @((Get-GsGlob (Join-Path $S 'findings') '*.md') + @((Join-Path $S 'combinations.md')) + (Get-GsGlob (Join-Path $S 'shards') '*.tsv') + @((Join-Path $S 'facts.tsv'), (Join-Path $S 'machine-fields.tsv')))) {
    if (Test-GsFile $p7) { $scanFiles += $p7 } }
foreach ($df2 in $scanFiles) {
    $c7 = @(@(Get-LfLines $df2) | Where-Object { $_ -cmatch '[A-Za-z0-9+/]{32,}' }).Count
    if ($c7 -gt 0) { $ds.Add('  - ' + [IO.Path]::GetFileName($df2) + ": $c7 处"); $N7 += $c7 } }
$ds.Add("- 命中合计: $N7 处——非零时共享前逐处确认（掩码改造会破坏不变量 9 的全文相等契约，处置=按敏感等级隔离归档而非改账本）")
$ds.Add('- 处置声明: 本扫描只计数不改动；secrets 类 finding 在 5d 已掩码交付，原文仅存 session（README 敏感等级口径）')
$ds.Add('## 编码契约自检（C-057——账本文本契约 UTF-8 无 BOM、LF 行尾）')
$BOMN = 0
$bomFiles = @()
foreach ($p7 in (Get-GsGlob $S '*.tsv')) { if (Test-GsFile $p7) { $bomFiles += $p7 } }
foreach ($p7 in (Get-GsGlob (Join-Path $S 'audit') '*.tsv')) { if (Test-GsFile $p7) { $bomFiles += $p7 } }
foreach ($df2 in $bomFiles) {
    $bytes = [System.IO.File]::ReadAllBytes($df2)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $ds.Add('  - ' + [IO.Path]::GetFileName($df2) + ': BOM 命中'); $BOMN++ }
    $hasCr = $false
    foreach ($b2 in $bytes) { if ($b2 -eq 13) { $hasCr = $true; break } }
    if ($hasCr) { $ds.Add('  - ' + [IO.Path]::GetFileName($df2) + ': CR 命中（非 LF 行尾）'); $BOMN++ } }
$ds.Add("- BOM/CR 命中: $BOMN（bash 写出本无 BOM——命中=写侧污染，修写入方不改账本）")
Set-LfContent (Join-Path $S 'audit/desensitize-scan.md') $ds
$dsN = @(@(Get-LfLines (Join-Path $S 'audit/desensitize-scan.md')) | Where-Object { $_.Contains('处——') }).Count
Out-Lf "脱敏扫描: $dsN 类命中（audit/desensitize-scan.md）"

# ===== A4: 处置反馈通道（操作者动作，主循环外；读全局写本 run 批后合并——C-028） =====
. "$S/env.ps1"
# A4 落行协议（§10.1/§10.2）：占位符按实际裁决代入后执行（七值封闭枚举）
$FID = '{finding_id}'; $DVAL = '{value}'; $DREASON = '{reason}'; $DSCOPE = '{scope}'; $DAPP = '{approver}'; $DEXP = '{expiry}'
$FP7 = ''
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $FID) { $FP7 = Fld $rW 1; break } }
if ($FP7 -ceq '') { Out-Lf "❌ finding 不在册: $FID（处置对象=稳定指纹——须为 machine-fields 行）"; exit 1 }
if ($DVAL -cnotin @('false-positive', 'intended-behavior', 'compensating-control', 'accepted-risk', 'known-issue', 'duplicate', 'fixed')) {
    Out-Lf "❌ disposition 非七值封闭枚举: $DVAL"; exit 1 }
if (-not ($DREASON -cmatch ':[0-9]+|[A-Z]{2,6}-[0-9]+')) { Out-Lf '❌ reason 须引用证据 file:line 或决策记录编号（C-040）'; exit 1 }
if (-not ($DSCOPE -cmatch '\|')) { Out-Lf '❌ scope 须双段 类|触发条件（C-041）'; exit 1 }
if (-not ($DEXP -cmatch '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) { Out-Lf '❌ review_expiry 须 YYYY-MM-DD（C-043）'; exit 1 }
New-GsDir (Join-Path $S 'feedback')
if (-not (Test-GsFile (Join-Path $S 'feedback/dispositions.tsv'))) {
    Set-LfContent (Join-Path $S 'feedback/dispositions.tsv') @('fingerprint' + "`t" + 'disposition' + "`t" + 'reason' + "`t" + 'scope' + "`t" + 'source' + "`t" + 'date' + "`t" + 'review_expiry' + "`t" + 'run_origin') }
Add-LfContent (Join-Path $S 'feedback/dispositions.tsv') @($FP7 + "`t" + $DVAL + "`t" + $DREASON + "`t" + $DSCOPE + "`t" + $DAPP + "`t" + (Get-GsDate) + "`t" + $DEXP + "`t" + (Get-GsBaseName $S))
Out-Lf "DISP-ROW $FID｜fp=$FP7｜$DVAL｜到期=$DEXP（抑制型下次 2e 信封即生效且须复核理由仍成立；标注型不抑制；fixed 型同指纹复现→NOTICE——批后合并走 merge-pending.sh）"

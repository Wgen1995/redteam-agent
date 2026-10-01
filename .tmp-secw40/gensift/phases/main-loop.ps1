# GenSift phases/main-loop.ps1 —— phases/main-loop.md 的 PowerShell 7 翻译件（任务10）
# 权威源 = main-loop.md 的 27 个 bash 块；节标题与 md 块标题一一对应。翻译总则见 phases/lib.ps1。

# ═══════════ 公共小底座（本件各节内联使用；与 lib.ps1 互补）═══════════
# （无——本件只依赖 lib.ps1；节内出现的局部 function 仅在该节作用域内有效，逐节独立执行不受影响）

# ===== step0: 前置检查（上一轮投影是否完成） =====
. "$S/env.ps1"
# 旧会话 schema 迁移（断点续跑兼容——v2 两轴 schema 之前的会话；R11 回放发现，幂等：表头非旧形态即零动作；与 main-loop.md step0 同式）
$candPath = Join-Path $S 'candidates.tsv'
if (Test-GsFile $candPath) {
    $cl = @(Get-LfLines $candPath)
    if ($cl.Count -gt 0 -and $cl[0] -ceq "cand_id`tcard_id`tsink_seq`tsource_seq`tclass_id`tsummary`tstate") {
        $out = [System.Collections.Generic.List[string]]::new()
        $out.Add("cand_id`tcard_id`tsink_seq`tsource_seq`tclass_id`tloc`tverdict_state`tdelivery_state`tsummary")
        $n = 0
        foreach ($line in ($cl | Select-Object -Skip 1)) {
            $f = $line -split "`t"
            if ($f.Count -lt 7) { continue }                                    # 畸形行不计（同 bash NF>=7 口径）
            $cid = $f[0]
            if ($f[2] -cmatch '^SINK-[0-9]+$') { $cid = 'CD-{0:d5}-00000' -f ([int]$f[2].Substring(5)) }
            $dv = 'delivered'; if ($f[6] -ceq 'open') { $dv = 'pending' }
            $out.Add(($cid, $f[1], $f[2], '', $f[4], $f[3], $f[6], $dv, $f[5]) -join "`t")
            $n++ }
        Set-LfContent (Join-Path $S 'tmp/cd.mig') $out
        Move-GsItem (Join-Path $S 'tmp/cd.mig') $candPath
        Out-Lf "旧会话 candidates.tsv 已迁移至 9 列两轴 schema（$n 行——cand_id 按 sink_seq 重写为可反推形态）" } }
$ftPath = Join-Path $S 'facts.tsv'
if (Test-GsFile $ftPath) {
    $fl = @(Get-LfLines $ftPath)
    if ($fl.Count -gt 0 -and $fl[0] -ceq "fact_id`ttype`tloc`tevidence`tevidence_hash`tstatus`tscope_type`tscope_ref`treflection_checked`tused_facts`tconfirmer`trevision") {
        $out2 = [System.Collections.Generic.List[string]]::new()
        $out2.Add("fact_id`ttype`tloc`tevidence`tevidence_hash`tstatus`tscope_type`tscope_ref`treflection_checked`tused_facts`tconfirmer`trevision`torigin_card")
        foreach ($line in ($fl | Select-Object -Skip 1)) { $out2.Add($line) }
        Set-LfContent (Join-Path $S 'tmp/ft.mig') $out2
        Move-GsItem (Join-Path $S 'tmp/ft.mig') $ftPath } }
# D6 partial 回收通道（P8——与 bash step0 同式）：分片已含合法 TERM 的 partial 卡按 3c 同口径重迁移；
# attempt 保留作审计痕迹；留痕 audit/partial-recovered.log（幂等：state 离开 partial 后不再命中）
if (Test-GsFile (Join-Path $S 'checks.tsv')) {
    $parts = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -ceq 'partial') { $parts.Add((Fld $rW 0)) } }
    foreach ($ck in $parts) {
        $f = Join-Path $S "shards/A-$ck.tsv"
        if (-not (Test-GsFile $f)) { continue }
        $tline = ''
        foreach ($l in @(Get-LfLines $f)) { if ($l.StartsWith('TERM:')) { $tline = $l; break } }
        $tline = $tline -creplace '<TAB>', "`t"   # 迟到分片防御净化（与 bash step0 同规则）
        $st = ''
        if ($tline -cne '') { $st = (($tline -split "`t")[0]) -creplace '^TERM:', '' }
        if ($st -ceq '') { continue }
        $knd = ''
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $ck) { $knd = Fld $rW 1; break } }
        $okst = $false                                                    # 终态白名单与 3c/3f 同口径
        if ($st -cin @('candidate', 'refuted', 'not_applicable', 'no_path', 'blocked')) { $okst = $true }
        elseif ($st -ceq 'deferred') { if ($knd -ceq 'ext') { $okst = $true } }
        if (-not $okst) { continue }
        $tc = $tline -split "`t"
        $rs = Fld $tc 1; $fu = Fld $tc 2
        $out = [System.Collections.Generic.List[string]]::new()
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $ck) {
                $rr[4] = $st
                if ($rs -cne '') { $rr[5] = $rs }
                if ($fu -cne '') { $rr[6] = $fu } }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv')
        Add-LfContent (Join-Path $S 'audit/partial-recovered.log') @("PARTIAL-RECOVERED`t$ck`t$st`t$(Get-GsTimestamp)")
        Out-Lf "D6 partial 回收: $ck → $st（分片迟到 TERM 已入账——attempt 保留作审计痕迹）" } }
# 首轮跳过
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/round_count'))[0])) }
if ($R -gt 0) {
    foreach ($mark in @('5a', '5b', '5c', '5d')) {                            # 上一轮四个投影标记
        if (-not (Test-GsFile (Join-Path $S "audit/mark-$mark-R$($R - 1)"))) {
            Out-Lf "❌ 上一轮 R$($R - 1) 未完成 step$mark 投影——先补投影再取卡"
            Out-Lf '补法：执行下方 step5 的完整命令块'
            exit 1 } }
    # L1 单调性：分母卡（origin_ref 空）unchecked 只许不增；retract 豁免额度=RETRACT-RESET 新增行数
    $PREV = '9999999'; if (Test-GsFile (Join-Path $S 'audit/last_unchecked')) { $PREV = @(Get-LfLines (Join-Path $S 'audit/last_unchecked'))[0] }
    $CUR = 0; $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 1) -cne 'ext' -and (Fld $rW 3) -ceq '' -and (Fld $rW 4) -ceq 'unchecked') { $CUR++ } }
    $PREVR = 0; if (Test-GsFile (Join-Path $S 'audit/last_retract_count')) { $PREVR = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/last_retract_count'))[0])) }
    $CURR = 0; if (Test-GsFile (Join-Path $S 'audit/retract.log')) { $CURR = @(@(Get-LfLines (Join-Path $S 'audit/retract.log')) | Where-Object { $_.StartsWith('RETRACT-RESET') }).Count }
    $ALLOW = $CURR - $PREVR; if ($ALLOW -lt 0) { $ALLOW = 0 }
    if (($CUR - $PREV) -gt $ALLOW) {
        Out-Lf "❌ L1 单调性违反: unchecked $PREV → $CUR（retract 豁免 $ALLOW 后仍超——分母被动过）"
        Set-LfContent (Join-Path $S 'audit/last_unchecked') @("$PREV")
        Set-LfContent (Join-Path $S 'EXIT_CODE') @('1'); Set-LfContent (Join-Path $S 'STATE') @('aborted-l1')   # C-017
        exit 1 }
    Set-LfContent (Join-Path $S 'audit/last_unchecked') @("$CUR")
    Set-LfContent (Join-Path $S 'audit/last_retract_count') @("$CURR")
    # L3 卡顿换道（B-060/B-072）：近 3 轮环形记录——3 轮全相等且 >0 即换 fw/term 道
    Add-LfContent (Join-Path $S 'audit/last3.txt') @("$CUR")
    $l3 = @(Get-LfLines (Join-Path $S 'audit/last3.txt'))
    if ($l3.Count -gt 3) { $l3 = @($l3 | Select-Object -Last 3) }
    Set-LfContent (Join-Path $S 'audit/last3.txt') $l3
    $u3 = @($l3 | Sort-OrdinalU)
    if ($l3.Count -eq 3 -and $u3.Count -eq 1 -and $CUR -gt 0) {
        Set-LfContent (Join-Path $S 'tmp/stall_lane') @("$R")
        Add-LfContent (Join-Path $S 'audit/stall.log') @("STALL R$R unchecked=$CUR 近3轮不降→本轮 dispatch_list 换 fw/term 道（L3 卡顿换道）")
        Out-Lf "⚠ L3 卡顿：近 3 轮 unchecked=$CUR 不降——step1 本轮全改派 fw/term 类，audit/stall.log 已留痕"
    } else {
        Remove-GsFile (Join-Path $S 'tmp/stall_lane') }
    # 循环内周期不变量（B-077）：I2/I4 每轮快查留痕（只记不拦）
    $i2 = Test-GsChecksums (Join-Path $S 'inventories') (Join-Path $S 'inventories/frozen.sha256')
    $B4 = 0
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ((Fld $rW 0) -cmatch '^CK-' -and (Fld $rW 4) -cnotmatch '^(unchecked|candidate|refuted|not_applicable|no_path|blocked|partial|deferred)$') { $B4++ } }
    Add-LfContent (Join-Path $S 'audit/invariants-loop.log') @("R$R`t" + 'I2:' + $(if ($i2) { 'PASS' } else { 'FAIL' }) + "`tI4:" + $(if ($B4 -eq 0) { 'PASS' } else { "FAIL($B4)" }))
}

# ===== step1: 取卡（优先级排序） =====
. "$S/env.ps1"
# 首轮 facts.tsv 尚未创建——预建表头防 fatal
if (-not (Test-GsFile (Join-Path $S 'facts.tsv'))) {
    Set-LfContent (Join-Path $S 'facts.tsv') @('fact_id' + "`t" + 'type' + "`t" + 'loc' + "`t" + 'evidence' + "`t" + 'evidence_hash' + "`t" + 'status' + "`t" + 'scope_type' + "`t" + 'scope_ref' + "`t" + 'reflection_checked' + "`t" + 'used_facts' + "`t" + 'confirmer' + "`t" + 'revision' + "`t" + 'origin_card') }
# D3' 派发宽度：缺省 4（width=N 经 env.ps1 贯通；非正整数回落 4）。F4：老会话 env.ps1 无 WIDTH 行——
# 未定义变量直接插值在 StrictMode 宿主下每轮抛噪音，改 Get-Variable 探测（cmdlet 调用不受 StrictMode 约束）
$WIDv = 4
$wRaw = Get-Variable -Name WIDTH -ValueOnly -ErrorAction SilentlyContinue
if ("$wRaw" -cmatch '^[1-9][0-9]*$') { $WIDv = [int]$wRaw }
# ── 信号预计算（B-052 无净化预判：sanitizer 模式文件同类 ERE 命中 sink 文件 ⇒ 净化预判存在）──
Set-LfContent (Join-Path $S 'tmp/sig-sanit.tsv') @()
$bwUnchecked = [System.Collections.Generic.List[object]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw' -and (Fld $rW 4) -ceq 'unchecked') { $bwUnchecked.Add($rW) } }
foreach ($cr in $bwUnchecked) {
    $card = Fld $cr 0; $ref = Fld $cr 2
    $loc = ''; $cls = ''
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $ref) { $loc = Fld $sr 2; $cls = Fld $sr 3; break } }
    if ($loc -ceq '' -or $cls -ceq '') { continue }
    $fl = Remove-GsSuffix1 $loc ':'
    $found = $false
    foreach ($patf in (Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')) {
        if (-not ((@(Get-LfLines $patf)) | Where-Object { $_ -cmatch '^# role: *sanitizer' })) { continue }
        $pbase = [IO.Path]::GetFileName($patf) -creplace '\.pattern$', ''
        if ($pbase.Substring(0, $pbase.LastIndexOf('-')) -cne $cls) { continue }
        foreach ($row in (Get-Tsv $patf)) {
            $ere = Fld $row 1
            if ($ere -ceq '') { continue }
            if (Select-String -LiteralPath (Join-Path $SRC $fl) -Pattern (Convert-ToDotNetRegex $ere) -CaseSensitive -Quiet) {
                Add-LfContent (Join-Path $S 'tmp/sig-sanit.tsv') @("$card`t1"); $found = $true; break } }
        if ($found) { break } } }
# B-053 常量实参 −30：sink 行实参域（剥引号串后）无任何标识符 ⇒ 常量实参信号
Set-LfContent (Join-Path $S 'tmp/sig-const.tsv') @()
foreach ($cr in $bwUnchecked) {
    $card = Fld $cr 0; $ref = Fld $cr 2
    $loc = ''
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $ref) { $loc = Fld $sr 2; break } }
    if ($loc -ceq '') { continue }
    $fl = Remove-GsSuffix1 $loc ':'; $ln = Remove-GsPrefixL $loc ':'
    $q = Get-GsLine (Join-Path $SRC $fl) ([int](ConvertTo-GsNum $ln))
    $args = ''
    $am = [regex]::Match($q, '^.*\(([^()]*)\).*$')                           # sed -n 's/^.*(\([^()]*\)).*$/\1/p'
    if ($am.Success) { $args = $am.Groups[1].Value }
    $args2 = $args -creplace '"[^"]*"', ''
    if ($args -cne '' -and -not ($args2 -cmatch '[A-Za-z_][A-Za-z0-9_.]*')) {
        Add-LfContent (Join-Path $S 'tmp/sig-const.tsv') @("$card`t1") } }
# D4-D 负向降权预计算（P4）：①文件级证伪密度（refuted≥80%∧≥3 → 该文件剩余卡 −30）②同理由聚类（同文件同类 refuted≥3 → −20）
Set-LfContent (Join-Path $S 'tmp/sig-negfile.tsv') @()
Set-LfContent (Join-Path $S 'tmp/sig-negcls.tsv') @()
$sf = @{}; $sc = @{}
$first = $true
foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $sf[(Fld $sr 0)] = ((Fld $sr 2) -split ':')[0]; $sc[(Fld $sr 0)] = Fld $sr 3 }
$closed = @{}; $ref = @{}; $refc = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw' -and $sf.ContainsKey((Fld $rW 2))) {
        $fx = $sf[(Fld $rW 2)]
        if ((Fld $rW 4) -cne 'unchecked') { $closed[$fx] = 1 + $(if ($closed.ContainsKey($fx)) { $closed[$fx] } else { 0 }) }
        if ((Fld $rW 4) -ceq 'refuted') {
            $ref[$fx] = 1 + $(if ($ref.ContainsKey($fx)) { $ref[$fx] } else { 0 })
            $k2 = $fx + "`t" + $sc[(Fld $rW 2)]
            $refc[$k2] = 1 + $(if ($refc.ContainsKey($k2)) { $refc[$k2] } else { 0 }) } } }
$negF = [System.Collections.Generic.List[string]]::new(); $negC = [System.Collections.Generic.List[string]]::new()
foreach ($fx in @($ref.Keys)) {
    $cv = 0; if ($closed.ContainsKey($fx)) { $cv = $closed[$fx] }
    if ($ref[$fx] -ge 3 -and $cv -gt 0 -and ($ref[$fx] * 100) -ge ($cv * 80)) { $negF.Add($fx) } }
foreach ($k2 in @($refc.Keys)) { if ($refc[$k2] -ge 3) { $negC.Add($k2) } }
Set-LfContent (Join-Path $S 'tmp/sig-negfile.tsv') @($negF | Sort-Ordinal)   # 排序定序：与 bash LC_ALL=C sort 字节对齐（枚举序两侧都未定义）
Set-LfContent (Join-Path $S 'tmp/sig-negcls.tsv') @($negC | Sort-Ordinal)
# D4-B② 安全敏感模块名词典（langpacks/sensitive-modules.txt——排序信号非检测规则；命中 ⇒ +10）
$SENS = ''
$sensF = Join-Path $SK 'langpacks/sensitive-modules.txt'
if (Test-GsFile $sensF) {
    $words = [System.Collections.Generic.List[string]]::new()
    foreach ($l in @(Get-LfLines $sensF)) {
        $w = $l.Trim()
        if ($w -ceq '' -or $w.StartsWith('#')) { continue }
        $words.Add($w.ToLowerInvariant()) }
    $SENS = ($words -join '|') }
# L3 换道分支：bw 道卡顿 ⇒ 本轮全派 fw/term
if (Test-GsFile (Join-Path $S 'tmp/stall_lane')) {
    $pick = [System.Collections.Generic.List[string]]::new(); $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -ceq 'unchecked' -and ((Fld $rW 1) -ceq 'fw' -or (Fld $rW 1) -ceq 'term')) { $pick.Add((Fld $rW 0)) } }
    Set-LfContent (Join-Path $S 'tmp/dispatch_list.txt') @($pick | Select-Object -First $WIDv)
    $laneR = ''; if (Test-GsFile (Join-Path $S 'tmp/stall_lane')) { $laneR = @(Get-LfLines (Join-Path $S 'tmp/stall_lane'))[0] }
    Out-Lf "⚠ L3 换道生效（R$laneR）：本轮 dispatch_list 全为 fw/term 类"
    foreach ($l in @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))) { Out-Lf $l }
} else {
    # 四项公式（B-049）+ v2.1 增补（D4-A 队尾 / D4-B 冷启动 / D4-D 负向降权与 +25 校准——与 main-loop.md step1 同式）
    $band = @{}; $sfile = @{}; $scls = @{}
    $first = $true
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        $band[(Fld $sr 0)] = Fld $sr 5; $parts = (Fld $sr 2) -split ':'; $sfile[(Fld $sr 0)] = $parts[0]; $scls[(Fld $sr 0)] = Fld $sr 3 }
    $susp = @{}
    foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
        if ((Fld $rW 1) -ceq 'uncontrolled' -and (Fld $rW 5) -cne 'rejected' -and (Fld $rW 5) -cne 'retracted') {
            $parts = (Fld $rW 2) -split ':'; $susp[$parts[0]] = 1 } }
    $unauth = @{}; $napi = @{}
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 5) -ceq 'unauth') { $parts = (Fld $rW 2) -split ':'; $unauth[$parts[0]] = 1 }
        if ((Fld $rW 3) -ceq 'lib_api') { $parts = (Fld $rW 2) -split ':'; $napi[$parts[0]] = 1 + $(if ($napi.ContainsKey($parts[0])) { $napi[$parts[0]] } else { 0 }) } }
    $mod = @{}; $modv = @{}; $role = @{}
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -cne '-' -and (Fld $rW 4) -cne '') { $mod[(Fld $rW 1)] = 1; $modv[(Fld $rW 1)] = Fld $rW 4 }
        $role[(Fld $rW 1)] = Fld $rW 5 }
    $cvef = @{}
    if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 1) -ceq 'G1') { $fx = (Fld $rW 5) -creplace ':[0-9]*$', ''; $cvef[$fx] = 1 } } }
    $const = @{}; foreach ($l in @(Get-LfLines (Join-Path $S 'tmp/sig-const.tsv'))) { $const[($l -split "`t")[0]] = 1 }
    $sanit = @{}; foreach ($l in @(Get-LfLines (Join-Path $S 'tmp/sig-sanit.tsv'))) { $sanit[($l -split "`t")[0]] = 1 }
    $negf = @{}; foreach ($l in @(Get-LfLines (Join-Path $S 'tmp/sig-negfile.tsv'))) { if ($l -cne '') { $negf[$l] = 1 } }
    $negc = @{}; foreach ($l in @(Get-LfLines (Join-Path $S 'tmp/sig-negcls.tsv'))) { if ($l -cne '') { $negc[$l] = 1 } }
    $rows = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -ceq 'unchecked' -and (Fld $rW 1) -ceq 'bw') {
            $ref = Fld $rW 2
            $b = '1'; if ($band.ContainsKey($ref)) { $b = $band[$ref] }
            $score = if ($b -ceq '0') { 100 } elseif ($b -ceq '1') { 60 } else { 10 }
            $fl = ''; if ($sfile.ContainsKey($ref)) { $fl = $sfile[$ref] }
            $cl = ''; if ($scls.ContainsKey($ref)) { $cl = $scls[$ref] }
            if ($susp.ContainsKey($fl)) { $score += 25 }                            # D4-D：+10 → +25 校准
            if (-not $sanit.ContainsKey((Fld $rW 0))) { $score += 20 }
            if ($const.ContainsKey((Fld $rW 0))) { $score -= 30 }
            if ($unauth.ContainsKey($fl)) { $score += 20 }
            if ($mod.ContainsKey($fl)) { $score += 10 }
            if ($cvef.ContainsKey($fl)) { $score += 15 }
            if ($napi.ContainsKey($fl)) { $score += [math]::Min(20, $napi[$fl] * 5) }   # D4-B① lib_api 密度 +5/条 封顶 +20
            if ($SENS -cne '' -and (($fl.ToLowerInvariant() -cmatch $SENS) -or ($modv.ContainsKey($fl) -and $modv[$fl].ToLowerInvariant() -cmatch $SENS))) { $score += 10 }   # D4-B②
            if ($negf.ContainsKey($fl)) { $score -= 30 }                            # D4-D① 文件级证伪密度
            if ($negc.ContainsKey($fl + "`t" + $cl)) { $score -= 20 }               # D4-D② 同理由聚类
            if ($score -lt 0) { $score = 0 }                                        # F2：普通卡负分钳 0（重罚卡不沉到 test 之下）
            if ($role.ContainsKey($fl) -and ($role[$fl] -ceq 'test' -or $role[$fl] -ceq 'demo')) { $score = -1 }   # F2/D4-A：test/demo 不入公式直接 -1 绝对排尾
            $rows.Add((Fld $rW 0) + "`t" + $score) } }
    # sort -t$'\t' -k2,2rn | head -$WIDv：键数值倒排，并列按整行字节序升（GNU 末位比较）——先整行序再稳定倒排
    $sortedRows = @($rows | Sort-Ordinal)
    $next = @($sortedRows | Sort-Object -Stable -Descending -Property { [int](ConvertTo-GsNum (($_ -split "`t")[1])) } | Select-Object -First $WIDv | ForEach-Object { ($_ -split "`t")[0] })
    $nextCards = [System.Collections.Generic.List[string]]::new()
    foreach ($x in $next) { $nextCards.Add($x) }
    Set-LfContent (Join-Path $S 'tmp/next_cards.txt') $nextCards
    # 补充 fw/term/ext 各 1 张防饥饿（v1.4.0-S6）——bash 形态：>> 追加进 next_cards.txt
    foreach ($kd in @('fw', 'term', 'ext')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 4) -ceq 'unchecked' -and (Fld $rW 1) -ceq $kd) { Add-LfContent (Join-Path $S 'tmp/next_cards.txt') @((Fld $rW 0)); $nextCards.Add((Fld $rW 0)); break } } }
    # 保序去重
    $seenD = @{}; $dl = [System.Collections.Generic.List[string]]::new()
    foreach ($x in $nextCards) { if (-not $seenD.ContainsKey($x)) { $seenD[$x] = 1; $dl.Add($x) } }
    Set-LfContent (Join-Path $S 'tmp/dispatch_list.txt') $dl
    # D4-A 队尾披露（与 bash 侧同式：test/demo 角色 bw 未闭合卡计数）
    $tdSet = @{}
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 5) -ceq 'test' -or (Fld $rW 5) -ceq 'demo') { $tdSet[(Fld $rW 1)] = 1 } }
    $TDT = 0
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 1) -ceq 'bw' -and (Fld $rW 4) -ceq 'unchecked' -and $sf.ContainsKey((Fld $rW 2)) -and $tdSet.ContainsKey($sf[(Fld $rW 2)])) { $TDT++ } }
    if ($TDT -gt 0) { Out-Lf "D4-A: test/demo 角色 bw 卡 $TDT 张全局排尾（score=-1 不剔除——覆盖红线守住）" }
    foreach ($l in $dl) { Out-Lf $l }
}

# ===== step1b: demand-driven 追踪卡（persisted_read——A-080/D-028） =====
. "$S/env.ps1"
# bw 卡 blocked → 对同文件 persisted_read 回读点按需发追踪 fw 卡（幂等）
foreach ($cr in $bwUnchecked) { }   # 占位防裸 $bwUnchecked（step1 节变量不跨节——本节自取）
$blocked = [System.Collections.Generic.List[object]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw' -and (Fld $rW 4) -ceq 'blocked') { $blocked.Add($rW) } }
foreach ($cr in $blocked) {
    $bwcard = Fld $cr 0; $bwref = Fld $cr 2
    $sf = ''
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
        if ((Fld $sr 0) -ceq $bwref) { $sf = ((Fld $sr 2) -split ':')[0]; break } }
    if ($sf -ceq '') { continue }
    $first = $true
    foreach ($pr in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $pr 3) -ceq 'persisted_read' -and ((Fld $pr 2)).StartsWith($sf + ':')) {
            $ps = Fld $pr 0
            $cid = 'CK-fw-P' + $ps.Substring(4) + '-' + $bwcard.Substring(6)
            $has = $false
            foreach ($xr in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $xr 0) -ceq $cid) { $has = $true; break } }
            if (-not $has) {
                Add-LfContent (Join-Path $S 'checks.tsv') @($cid + "`t" + 'fw' + "`t" + $ps + "`t" + $bwcard + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') } } } }
$n = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 1) -ceq 'fw' -and (Fld $rW 0) -cmatch '^CK-fw-P') { $n++ } }
Out-Lf "demand-driven 追踪卡: $n 张"

# ===== 2a: 写 in-flight 记录 =====
. "$S/env.ps1"
$dlLines = @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))
$joined = ($dlLines -join ',') -creplace ',$', ''                              # tr '\n' ',' + sed 's/,$//'
Set-LfText (Join-Path $S 'audit/in_flight.txt') $joined                       # bash 形态无尾换行——Set-LfText 原样
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
Add-LfContent (Join-Path $S 'audit/dispatch-history.log') @("R$R`t$joined")

# ===== 2b: 查卡信息（每张卡执行一次；{card_id} 代入） =====
. "$S/env.ps1"
$CARD = '{card_id}'
$INFO = @()
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $CARD) { $INFO = @((Fld $rW 1), (Fld $rW 2), (Fld $rW 3)); break } }
$KIND = $INFO[0]; $REF = $INFO[1]; $ORIG = $INFO[2]
$LOC = ''; $CLS = ''; $BAND = ''; $GRD = ''; $FAM = ''; $API = ''
if ($CARD -clike 'CK-ext-*') {
    $KIND = 'ext'; $LOC = ''; $CLS = 'term'; $BAND = 1; $REF = $ORIG }
else {
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $REF) { $LOC = Fld $sr 2; $CLS = Fld $sr 3; $BAND = Fld $sr 5; $API = Fld $sr 4; break } }
    if ($LOC -ceq '' -and $KIND -ceq 'fw') {
        foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ((Fld $sr 0) -ceq $REF) { $LOC = Fld $sr 2; $GRD = Fld $sr 6; $FAM = Fld $sr 7; break } } }
    if ($LOC -ceq '') {
        foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ((Fld $sr 0) -ceq $REF) { $LOC = Fld $sr 1; break } } } }
if ($CLS -ceq '') { $CLS = 'term' }
if ($BAND -ceq '') { $BAND = 1 }
$WL = ''
if ($LOC -cne '') {
    $lfile = Remove-GsSuffix1 $LOC ':'
    $first = $true
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        if (((Fld $sr 2)).StartsWith($lfile + ':')) { $WL += (Fld $sr 0) + ' ' } } }
$WL = "$WL$CARD"
$FR = ''
$ATT = '0'
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $CARD) { $ATT = Fld $rW 7; break } }
if ((ConvertTo-GsNum $ATT) -gt 0 -and (Test-GsFile (Join-Path $S 'audit/attempt-failures.log'))) {
    $lastR = ''
    foreach ($l in @(Get-LfLines (Join-Path $S 'audit/attempt-failures.log'))) { if (($l -split "`t")[0] -ceq $CARD) { $lastR = ($l -split "`t")[1] } }
    $FR = $lastR }
# rc 对齐：bash 块尾 `[ "$ATT" -gt 0 ] && FR=...` 短路使 ATT=0 时整块 rc=1——逐字对齐
if (-not ((ConvertTo-GsNum $ATT) -gt 0)) { exit 1 }

# ===== 2c: band2 的 bw 卡 → 批量派 Summarizer =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
$b2 = [System.Collections.Generic.List[string]]::new()
foreach ($CARD in @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))) {
    if ($CARD -ceq '') { continue }
    $REF = ''
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $CARD) { $REF = Fld $rW 2; break } }
    $BAND = ''; $CLS = ''
    foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $REF) { $BAND = Fld $sr 5; $CLS = Fld $sr 3; break } }
    if ($BAND -ceq '2') { $b2.Add("$CLS $CARD") } }
$b2s = @($b2 | Sort-Ordinal)
Set-LfContent (Join-Path $S 'tmp/band2_batch.txt') $b2s
foreach ($l in $b2s) { Out-Lf $l }

# ===== 2d: 语义合并轮触发（open 候选 ≥25——B-021/D-110） =====
. "$S/env.ps1"
$PEND25 = 0
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 6) -ceq 'open' -and (Fld $rW 7) -ceq 'pending' -and (Fld $rW 1) -cne 'G1') { $PEND25++ } } }
Out-Lf "待验证候选: $PEND25（≥25 触发合并轮——B-021/D-110：先去重再验证，省的是验证派发预算）"
if ($PEND25 -ge 25) {
    $mi = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 6) -ceq 'open' -and (Fld $rW 7) -ceq 'pending' -and (Fld $rW 1) -cne 'G1') { $mi.Add((Fld $rW 0) + "`t" + (Fld $rW 4) + "`t" + (Fld $rW 5)) } }
    Set-LfContent (Join-Path $S 'tmp/merge_input.txt') $mi
    foreach ($l in $mi) { Out-Lf $l } }

# ===== 2dc: MERGE 分片消费（机械回写；幂等：已 merged 不重复记账） =====
. "$S/env.ps1"
foreach ($mgf in (Get-GsGlob (Join-Path $S 'shards') 'MERGE-*.tsv')) {
    $canon = ''
    foreach ($line in @(Get-LfLines $mgf)) {
        $head = $line; $rest = ''
        $ti = $line.IndexOf("`t"); if ($ti -ge 0) { $head = $line.Substring(0, $ti); $rest = $line.Substring($ti + 1) }
        if ($head -clike 'MERGE:*') { $canon = $head.Substring(6) }
        elseif ($head -clike 'ABSORB:*') {
            if ($canon -ceq '') { continue }
            $ac = $head.Substring(7)
            if ($ac -ceq $canon) { continue }                                   # canonical 不得吸收自身
            $ok = $false
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $ac -and -not ((Fld $rW 6)).StartsWith('merged-into')) { $ok = $true; break } }
            if (-not $ok) { continue }
            $out = [System.Collections.Generic.List[string]]::new()             # S8：verdict_axis 迁移，delivery 不动
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
                $rr = Get-Row $rW
                if ((Fld $rW 0) -ceq $ac) { $rr[6] = "merged-into-$canon" }
                $out.Add((Join-Tsv $rr)) }
            Set-LfContent (Join-Path $S 'tmp/cd.tmp') $out
            Move-GsItem (Join-Path $S 'tmp/cd.tmp') (Join-Path $S 'candidates.tsv')
            Add-LfContent (Join-Path $S 'audit/merge.log') @("MERGED`t$ac`tinto`t$canon`t$rest")
            if (Test-GsFile (Join-Path $S "shards/V-$ac.tsv")) {                # 陈旧 V 分片同批撤档
                Move-GsItem (Join-Path $S "shards/V-$ac.tsv") (Join-Path $S "audit/superseded-V-$ac.tsv") }
            $cls = ''; $loc3 = ''
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $ac) { $cls = Fld $rW 4; $loc3 = Fld $rW 5; break } }
            $fex = ''
            if ($loc3 -cne '') { $fex = Get-GsFex $loc3 }                       # C-001：与 5a 同一机械派生
            $fid = "F-$ac-$cls$fex"
            if (Test-GsFile (Join-Path $S 'machine-fields.tsv')) {
                $hit = $false
                foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $fid -and (Fld $rW 12) -ceq '') { $hit = $true; break } }
                if ($hit) {
                    $out = [System.Collections.Generic.List[string]]::new()
                    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
                        $rr = Get-Row $rW
                        if ((Fld $rW 0) -ceq $fid -and (Fld $rW 12) -ceq '') { $rr[12] = 'superseded_by' }
                        $out.Add((Join-Tsv $rr)) }
                    Set-LfContent (Join-Path $S 'tmp/mf.tmp') $out
                    Move-GsItem (Join-Path $S 'tmp/mf.tmp') (Join-Path $S 'machine-fields.tsv')
                    $fpath = Join-Path $S "findings/$fid.md"
                    if (Test-GsFile $fpath) {
                        $arc = Join-Path $S "audit/superseded-$fid.md"; $k = 1
                        while (Test-GsFile $arc) { $k++; $arc = Join-Path $S "audit/superseded-$fid-$k.md" }
                        Move-GsItem $fpath $arc
                        Add-LfText $arc "`n## 勘误（errata——只追加，原文未改写）`n- $(Get-GsTimestamp) lifecycle=superseded_by（语义合并：被 $canon 吸收——$(if ($rest -cne '') { $rest } else { '同修复点' })）——撤档留痕不蒸发；report/live 投影按 lifecycle 滤行`n" } } }
            $ccls = ''; $cloc = ''
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $canon) { $ccls = Fld $rW 4; $cloc = Fld $rW 5; break } }
            $cfex = ''
            if ($cloc -cne '') { $cfex = Get-GsFex $cloc }
            $cfid = "F-$canon-$ccls$cfex"
            if (Test-GsFile (Join-Path $S 'machine-fields.tsv')) {
                $hit = $false
                foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $cfid -and (Fld $rW 12) -ceq '') { $hit = $true; break } }
                if ($hit) {
                    $out = [System.Collections.Generic.List[string]]::new()
                    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
                        $rr = Get-Row $rW
                        if ((Fld $rW 0) -ceq $cfid -and (Fld $rW 12) -ceq '') {
                            $arb9 = Fld $rW 8
                            if ((',' + $arb9 + ',').IndexOf(',' + $ac + ',') -lt 0) { $rr[8] = $arb9 + $(if ($arb9 -cne '') { ',' }) + $ac } }
                        $out.Add((Join-Tsv $rr)) }
                    Set-LfContent (Join-Path $S 'tmp/mf.tmp') $out
                    Move-GsItem (Join-Path $S 'tmp/mf.tmp') (Join-Path $S 'machine-fields.tsv') } } } } }
if (Test-GsFile (Join-Path $S 'audit/merge.log')) {
    $mc = @(@(Get-LfLines (Join-Path $S 'audit/merge.log')) | Where-Object { $_.StartsWith('MERGED') }).Count
    Out-Lf "合并轮: 累计吸收 $mc 条（audit/merge.log——canonical 落 also-reported-by，被吸收已交付行 superseded_by 撤档）" }

# ===== 2e: 派 Verifier（上一轮 step3d 落账的候选） =====
. "$S/env.ps1"
# V 分片存在但无 VERDICT 行=空口复核，删掉重派；重派上限 2 次后转 degraded（delivery 轴）
$toVerify = [System.Collections.Generic.List[string]]::new()
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 6) -ceq 'open' -and (Fld $rW 7) -ceq 'pending' -and (Fld $rW 1) -cne 'G1') {
            $cand = Fld $rW 0
            $vf = Join-Path $S "shards/V-$cand.tsv"
            if (Test-GsFile $vf) {
                $hasV = $false; foreach ($l in @(Get-LfLines $vf)) { if ($l.StartsWith('VERDICT:')) { $hasV = $true; break } }
                if ($hasV) { continue }
                New-GsDir (Join-Path $S 'audit/verify_attempts')
                $cntF = Join-Path $S "audit/verify_attempts/$cand"
                $nA = 0; if (Test-GsFile $cntF) { $nA = [int](ConvertTo-GsNum (@(Get-LfLines $cntF)[0])) }
                $nA++; Set-LfContent $cntF @("$nA")
                if ($nA -ge 2) {
                    Move-GsItem $vf (Join-Path $S "audit/degraded-V-$cand.tsv")
                    Add-LfContent (Join-Path $S 'audit/coverage-degraded.log') @("DEGRADED-V $cand 两次空口复核")
                    $out = [System.Collections.Generic.List[string]]::new()
                    foreach ($r2 in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
                        $rr = Get-Row $r2
                        if ((Fld $r2 0) -ceq $cand) { $rr[7] = 'degraded' }
                        $out.Add((Join-Tsv $rr)) }
                    Set-LfContent (Join-Path $S 'tmp/cd.tmp') $out
                    Move-GsItem (Join-Path $S 'tmp/cd.tmp') (Join-Path $S 'candidates.tsv')
                    continue }
                Remove-GsFile $vf }
            $toVerify.Add($cand) } } }
Set-LfContent (Join-Path $S 'tmp/to_verify.txt') $toVerify
foreach ($l in $toVerify) { Out-Lf $l }

# ===== 2eenv: 派发信封构造（机器字段 + OBS 引文 + 处置行 join——S4-A/B-028/C-044） =====
. "$S/env.ps1"
$CAND = '{cand_id}'
$crow = $null
foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $CAND) { $crow = $rW; break } }
if ($null -ne $crow) { Out-Lf ("候选：" + $CAND + "｜sink=" + (Fld $crow 2) + "｜source=" + (Fld $crow 3) + "｜class=" + (Fld $crow 4) + "｜loc=" + (Fld $crow 5)) }
$CARD = ''
foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $CAND) { $CARD = Fld $rW 1; break } }
$ashard = Join-Path $S "shards/A-$CARD.tsv"
if (Test-GsFile $ashard) { foreach ($l in (@(Get-LfLines $ashard) | Where-Object { $_.StartsWith('OBS:') } | Select-Object -First 5)) { Out-Lf $l } }
if (Test-GsFile $ashard) { foreach ($l in (@(Get-LfLines $ashard) | Where-Object { $_.StartsWith('ROLE:') } | Select-Object -First 5)) { Out-Lf $l } }
$DLOC = ''; $DCLS = ''
if ($null -ne $crow) { $DLOC = Fld $crow 5; $DCLS = Fld $crow 4 }
if ($DCLS -ceq '') { $DCLS = 'term' }
$DFP = ''
if ($null -ne $crow) {
    $DLF = Remove-GsSuffix1 $DLOC ':'; $DLN = Remove-GsPrefixL $DLOC ':'
    $DQ = ''
    if ($DLN -cmatch '^[0-9]+$') { $DQ = Get-GsLine (Join-Path $SRC $DLF) ([int]$DLN) }
    $DFP = Get-GsHash16 ($DLF + "`n" + $DQ + "`n" + $DCLS + "`n") }
foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
    if (-not (Test-GsFile $df)) { continue }
    $today = Get-GsDate
    $first = $true
    foreach ($rW in (Get-Tsv $df)) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 0) -ceq $DFP) {
            $sc = (Fld $rW 3) -split '\|'
            if ($sc[0] -cne '' -and $sc[0] -cne $DCLS) { continue }
            $ex = ''
            if ((Fld $rW 6) -cne '' -and (Fld $rW 6) -clt $today) { $ex = '｜已过期待复核(降级hint——抑制失效照常裁决)' }
            Out-Lf ("DISP:" + (Fld $rW 0) + "｜" + (Fld $rW 1) + "｜reason=" + (Fld $rW 2) + "｜scope=" + (Fld $rW 3) + "｜批准=" + (Fld $rW 4) + "｜date=" + (Fld $rW 5) + "｜复核到期=" + (Fld $rW 6) + $ex) } } }
$RUNTIMEV = "$RUNTIMEV"
$TMAX = 'T1'; if ($RUNTIMEV -ceq 'allowed') { $TMAX = 'T3' } else { $RUNTIMEV = 'off' }
Out-Lf "runtime_verification=$RUNTIMEV｜tier上限=$TMAX（T2/T3 仅授权 run）"

# ===== 2f: 双向对称反转抽样（B-020） =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
if (-not (Test-GsFile (Join-Path $S 'audit/reversal-sampled.tsv'))) {
    Set-LfContent (Join-Path $S 'audit/reversal-sampled.tsv') @('card_id' + "`t" + 'round') }
$done = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'audit/reversal-sampled.tsv'))) { if ($first) { $first = $false; continue }; $done[(Fld $rW 0)] = 1 }
$band = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -ceq '0' -or (Fld $rW 5) -ceq '1') { $band[(Fld $rW 0)] = 1 } }
$pool = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw' -and ((Fld $rW 4) -ceq 'refuted' -or (Fld $rW 4) -ceq 'no_path') -and $band.ContainsKey((Fld $rW 2)) -and -not $done.ContainsKey((Fld $rW 0))) { $pool.Add((Fld $rW 0)) } }
Set-LfContent (Join-Path $S 'tmp/rs.pool') $pool
$N = $pool.Count
$n2 = [math]::Floor(($N + 5) / 10); if ($n2 -lt 1 -and $N -gt 0) { $n2 = 1 }
$sample = [System.Collections.Generic.List[string]]::new()
if ($N -gt 0) {
    $hashed = [System.Collections.Generic.List[string]]::new()
    foreach ($c in $pool) { $hashed.Add((Get-GsHash16 ($c + "`n" + $R)) + "`t" + $c) }   # 稳定哈希×轮号盐排序（确定性抽样）
    foreach ($h in @($hashed | Sort-Ordinal | Select-Object -First $n2)) { $sample.Add(($h -split "`t")[1]) }
    Set-LfContent (Join-Path $S 'tmp/reversal_sample.txt') $sample
    foreach ($c in $sample) { if ($c -cne '') { Add-LfContent (Join-Path $S 'audit/reversal-sampled.tsv') @($c + "`t" + "R$R") } } }
else { Set-LfContent (Join-Path $S 'tmp/reversal_sample.txt') @() }
Out-Lf "2f 抽样: 池=$N 取=$n2"
foreach ($l in $sample) { Out-Lf $l }

# ===== 2fenv: 复核信封构造 =====
. "$S/env.ps1"
$CARD = '{card_id}'
$INFO = @('', '', '')
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $CARD) { $INFO = @((Fld $rW 1), (Fld $rW 2), (Fld $rW 4)); break } }
$REF = $INFO[1]
$LOC = ''; $CLS = ''; $BAND = ''
foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $REF) { $LOC = Fld $sr 2; $CLS = Fld $sr 3; $BAND = Fld $sr 5; break } }
if ($CLS -ceq '') { $CLS = 'term' }
Out-Lf ("复核卡：$CARD｜kind=" + $INFO[0] + "｜loc=$LOC｜class=$CLS｜band=$BAND｜prior_state=" + $INFO[2] + "（原因叙述不提供——防锚定）")

# ===== 3a: 引文机械归一化（OBS/SELF 引文 + FACT evidence；C-058 写行前机械转义） =====
. "$S/env.ps1"
foreach ($f in @(@(Get-GsGlob (Join-Path $S 'shards') 'A-*.tsv') + @(Get-GsGlob (Join-Path $S 'shards') 'V-*.tsv') + @(Get-GsGlob (Join-Path $S 'shards') 'RV-*.tsv') + @(Get-GsGlob (Join-Path $S 'shards') 'CONF-*.tsv'))) {   # 每操作数 @() 包裹：1A+1V 等单元素态摊平→路径串接→3a 整块静默 no-op（任务11 终审B P0）
    $norm = [System.Collections.Generic.List[string]]::new()
    foreach ($line in @(Get-LfLines $f)) {
        # 真宿主摄入净化（与 bash 侧同款）：①<TAB> 记法→真实制表符 ②绝对路径→相对源码根
        # ③D6 格式方差修复（P8）：TERM/RUBRIC 无冒号补冒号保留；CARD/DEFINE 自创头行剥除（非账本行）
        if ($line -clike '*<TAB>*') { $line = $line -creplace '<TAB>', "`t" }
        # S8 变体（2026-08-27 真跑实证 CK-bw-00030/31，与 bash 侧同款）：`TERM:<TAB>state`——剥冒号后首个 TAB
        if ($line -clike "TERM:`t*" -or $line -clike "RUBRIC:`t*") { $line = $line -creplace '^(TERM|RUBRIC):`t', '$1:' }
        $head = $line; $ti = $line.IndexOf("`t")
        if ($ti -ge 0) { $head = $line.Substring(0, $ti) }
        if (($head -ceq 'TERM' -or $head -ceq 'RUBRIC') -and $ti -ge 0) {        # 分隔 TAB 置换为冒号（^TERM\t→TERM:）；
            $line = $head + ':' + $line.Substring($head.Length + 1); $head = $head + ':' }   # 裸标签行（无 TAB）不可修复——原样入 raw（F3 双侧等价）
        elseif ($head -clike 'CARD*' -or $head -clike 'DEFINE*') { continue }
        if ($head -clike 'OBS:*' -or $head -clike 'SELF:*') {
            $loc = $head.Substring($head.IndexOf(':') + 1)
            $sp = (Join-Path $SRC '') -creplace '\\', '/'
            if ($loc -clike "$sp*") { $loc = $loc.Substring($sp.Length); $head = $head.Substring(0, $head.IndexOf(':') + 1) + $loc }
            $ln = Remove-GsPrefixL $loc ':'
            $file = Remove-GsSuffix1 $loc ':'
            if ($ln -cnotmatch '^[0-9]+$') { $norm.Add($line); continue }
            $q = Get-GsLine (Join-Path $SRC $file) ([int]$ln)
            if ($q -cne '') { $norm.Add($head + "`t" + (ConvertTo-GsEsc $q)) }
            else { $norm.Add($line) } }
        elseif ($head -clike 'FACT:*') {
            $cols = $line -split "`t", 4
            $f2 = Fld $cols 1; $rest = Fld $cols 3
            $sp2 = (Join-Path $SRC '') -creplace '\\', '/'
            if ($f2 -clike "$sp2*") { $f2 = $f2.Substring($sp2.Length) }
            $fln = Remove-GsPrefixL $f2 ':'
            $ffile = Remove-GsSuffix1 $f2 ':'
            if ($fln -cnotmatch '^[0-9]+$') { $norm.Add($line); continue }
            $q = Get-GsLine (Join-Path $SRC $ffile) ([int]$fln)
            if ($q -cne '') { $norm.Add($head + "`t" + $f2 + "`t" + (ConvertTo-GsEsc $q) + "`t" + $rest) }
            else { $norm.Add($line) } }
        else { $norm.Add($line) } }
    Set-LfContent "$f.norm" $norm
    Move-GsItem "$f.norm" $f }

# ===== 3b: 行数对账（派/收对照 + in_flight 消费 + C-Inv08 行数恒等式） =====
. "$S/env.ps1"
$dlLines = @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))
$D = $dlLines.Count
$G = 0
foreach ($ck in $dlLines) { if ($ck -cne '' -and (Test-GsFile (Join-Path $S "shards/A-$ck.tsv"))) { $G++ } }
$IF = 0
if (Test-GsFile (Join-Path $S 'audit/in_flight.txt')) {
    $ift = @(Get-LfLines (Join-Path $S 'audit/in_flight.txt'))
    if ($ift.Count -gt 0 -and $ift[0] -cne '') { $IF = @(($ift[0] -split ',') | Where-Object { $_ -cne '' }).Count } }
Out-Lf "对账: 派 $D / 收 $G / in_flight $IF（缺失卡由 3f attempt 计数处置，不许静默）"
if ($IF -ne $D -or $G -ne $D) {
    Out-GsTee (Join-Path $S 'audit/reconcile.log') "⚠ in_flight 对账不一致: in_flight=$IF 派=$D 收=$G（2a 记录与实际派发漂移——audit/reconcile.log 留痕）" }
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
$manifest = Join-Path $S "audit/shard-manifest-R$R.tsv"
Set-LfContent $manifest @()
$SL = 0
foreach ($ck in $dlLines) {
    if ($ck -ceq '') { continue }
    $fp = Join-Path $S "shards/A-$ck.tsv"
    if (-not (Test-GsFile $fp)) { continue }
    $n3 = @(Get-LfLines $fp).Count
    Add-LfContent $manifest @($ck + "`t" + $n3)
    if ($n3 -eq 0) { Out-GsTee (Join-Path $S 'audit/reconcile.log') "⚠ 空分片: A-$ck.tsv 0 行（内容丢失——交 3f 计费）" }
    $SL += $n3 }
Out-Lf "行数恒等式: manifest Σ=$SL（audit/shard-manifest-R$R.tsv；逐片 wc -l 对账 cat 合计）"
Add-LfContent (Join-Path $S 'audit/reconcile.log') @("3b-lines R$R`: 派=$D 收=$G in_flight=$IF shardlines=$SL")

# ===== 3c: 状态迁移（只处理本轮派发的卡；TERM 值白名单过滤） =====
. "$S/env.ps1"
foreach ($ck in @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))) {
    if ($ck -ceq '') { continue }
    $f = Join-Path $S "shards/A-$ck.tsv"
    if (-not (Test-GsFile $f)) { continue }
    $tline = ''
    foreach ($l in @(Get-LfLines $f)) { if ($l.StartsWith('TERM:')) { $tline = $l; break } }
    $tline = $tline -creplace '<TAB>', "`t"   # 迟到分片防御净化（与 bash 3c 同规则——字面记法滞留账本实证）
    $st = ''
    if ($tline -cne '') { $st = ($tline -split "`t")[0] -creplace '^TERM:', '' }
    if ($st -ceq '') { continue }
    $knd = ''
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $ck) { $knd = Fld $rW 1; break } }
    $okst = $false
    if ($st -cin @('candidate', 'refuted', 'not_applicable', 'no_path', 'blocked', 'partial')) { $okst = $true }
    elseif ($st -ceq 'deferred') { if ($knd -ceq 'ext') { $okst = $true } }
    if (-not $okst) { continue }
    $tc = $tline -split "`t"
    $rs = Fld $tc 1; $fu = Fld $tc 2
    $out = [System.Collections.Generic.List[string]]::new()
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        $rr = Get-Row $rW
        if ((Fld $rW 0) -ceq $ck) {
            $rr[4] = $st
            if ($rs -cne '') { $rr[5] = $rs }
            if ($fu -cne '') { $rr[6] = $fu } }
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv') }

# ===== 3d: 候选落账（统一 cand_id 双命名空间可反推——B-190/B-191/B-210/C-Inv14） =====
. "$S/env.ps1"
if (-not (Test-GsFile (Join-Path $S 'candidates.tsv'))) {
    Set-LfContent (Join-Path $S 'candidates.tsv') @('cand_id' + "`t" + 'card_id' + "`t" + 'sink_seq' + "`t" + 'source_seq' + "`t" + 'class_id' + "`t" + 'loc' + "`t" + 'verdict_state' + "`t" + 'delivery_state' + "`t" + 'summary') }
if (-not (Test-GsFile (Join-Path $S 'joins.tsv'))) {
    Set-LfContent (Join-Path $S 'joins.tsv') @('join_id' + "`t" + 'egress_ref' + "`t" + 'contract_ref' + "`t" + 'ingress_ref' + "`t" + 'confidence' + "`t" + 'assumptions') }
Set-LfContent (Join-Path $S 'tmp/new_cands.txt') @()
$cands = [System.Collections.Generic.List[object]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 4) -ceq 'candidate') { $cands.Add($rW) } }
foreach ($cr in $cands) {
    $ck = Fld $cr 0; $kind = Fld $cr 1; $ref = Fld $cr 2; $orig = Fld $cr 3
    $has = $false
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 1) -ceq $ck) { $has = $true; break } }
    if ($has) { continue }
    $num = [regex]::Replace($ref, '[^0-9]', '')
    $sq = ''; $vq = ''
    if ($ck -clike 'CK-ext-*') {
        $cls = 'term'; $loc = ''
        if ($orig -cmatch '^INV-') {
            $mod = ''
            if ($orig + '-' -cne $ref -and $ref.StartsWith($orig + '-')) { $mod = $ref.Substring($orig.Length + 1) }
            if ($mod -ceq '' -or $mod -ceq '-') { $mod = 'core' }
            $cid = 'CD-INV-' + $orig.Substring(4) + '-' + $mod }
        elseif ($orig -clike 'SINK-*') { $cid = 'CD-' + (Format-Gs05 ($orig.Substring(5))) + '-00000' }
        elseif ($orig -clike 'SRC-*') { $cid = 'CD-00000-' + (Format-Gs05 ($orig.Substring(4))) }
        else { $cid = "CD-X-$orig" } }
    else {
        if ($kind -ceq 'bw') {
            $cls = ''; $loc = ''
            foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ((Fld $sr 0) -ceq $ref) { $cls = Fld $sr 3; $loc = Fld $sr 2; break } }
            $sq = Format-Gs05 $num; $cid = "CD-$sq-00000" }
        elseif ($kind -ceq 'fw') {
            $cls = 'term'; $loc = ''
            foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ((Fld $sr 0) -ceq $ref) { $loc = Fld $sr 2; break } }
            $vq = Format-Gs05 $num; $cid = "CD-00000-$vq" }
        else {
            $cls = 'term'; $loc = ''
            foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ((Fld $sr 0) -ceq $ref) { $loc = Fld $sr 1; break } }
            $cid = "CD-F-$num" } }
    if ($cls -ceq '') { $cls = 'term' }
    $has2 = $false
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $cid) { $has2 = $true; break } }
    if ($has2) { continue }
    $summ = ''
    $ap = Join-Path $S "shards/A-$ck.tsv"
    if (Test-GsFile $ap) {
        foreach ($l in @(Get-LfLines $ap)) {
            if ($l.StartsWith('TERM:')) { $l = $l -creplace '<TAB>', "`t"; $tc = $l -split "`t"; $summ = (Fld $tc 1); break } }   # radiation-lens 第三处：迟到分片净化（summary 失明防护）
        if ($summ.Length -gt 160) { $summ = $summ.Substring(0, 160) } }
    Add-LfContent (Join-Path $S 'candidates.tsv') @($cid + "`t" + $ck + "`t" + $sq + "`t" + $vq + "`t" + $cls + "`t" + $loc + "`t" + 'open' + "`t" + 'pending' + "`t" + $summ)
    Add-LfContent (Join-Path $S 'tmp/new_cands.txt') @($cid) }

# ===== 3e: 事实合并 + Confirmer 派发 + retract 翻案传播 =====
. "$S/env.ps1"
# 获取当前最大事实号（十进制安全）
$LAST_FT = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ((Fld $rW 0) -cmatch '^FT-') { $t = [int](ConvertTo-GsNum ((Fld $rW 0).Substring(3))); if ($t -gt $LAST_FT) { $LAST_FT = $t } } }
$N = $LAST_FT
New-GsDir (Join-Path $S 'audit')
$ftRaw = [System.Collections.Generic.List[string]]::new()
foreach ($f in @(@(Get-GsGlob (Join-Path $S 'shards') 'A-*.tsv') + @(Get-GsGlob (Join-Path $S 'shards') 'SUM-*.tsv'))) {   # 每操作数 @() 包裹：A=1∧SUM=1 时摊平串接→FACT 合并静默丢失（任务11 终审B P0）
    $oc = [IO.Path]::GetFileNameWithoutExtension($f); if ($oc.StartsWith('A-')) { $oc = $oc.Substring(2) }
    foreach ($l in @(Get-LfLines $f)) { if ($l.StartsWith('FACT:')) {
        # F2 迟到分片防御净化（与 bash 3e 同规则——字面 <TAB> 记法/绝对路径 loc/evidence 回读转义，幂等）
        $l = $l -creplace '<TAB>', "`t"
        $cols = $l -split "`t", 4
        $head = Fld $cols 0; $f2 = Fld $cols 1; $rest = Fld $cols 3
        $sp2 = (Join-Path $SRC '') -creplace '\\', '/'
        if ($f2 -clike "$sp2*") { $f2 = $f2.Substring($sp2.Length) }
        $fln = Remove-GsPrefixL $f2 ':'; $ffile = Remove-GsSuffix1 $f2 ':'
        if ($fln -cmatch '^[0-9]+$') { $q = Get-GsLine (Join-Path $SRC $ffile) ([int]$fln)
            if ($q -cne '') { $l = $head + "`t" + $f2 + "`t" + (ConvertTo-GsEsc $q) + "`t" + $rest } }
        $ftRaw.Add($l + "`t" + $oc) } } }
Set-LfContent (Join-Path $S 'tmp/ft.raw') $ftRaw
# per-FACT 幂等去重（D-088）：同 loc+evidence 不双计；被翻案事实不复活
$seen = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
    if ($first) { $first = $false; continue }
    $seen[(Fld $rW 2) + "`t" + (Fld $rW 3)] = 1 }
$ftNew = [System.Collections.Generic.List[string]]::new()
$n4 = 0
foreach ($l in $ftRaw) {
    $fl2 = $l -split "`t", 9
    if (-not ((Fld $fl2 0)).StartsWith('FACT:')) { continue }
    $key = (Fld $fl2 1) + "`t" + (Fld $fl2 2)
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = 1; $n4++
    $ftNew.Add(('FT-{0:d4}' -f ($N + $n4)) + "`t" + ((Fld $fl2 0).Substring(5)) + "`t" + (Fld $fl2 1) + "`t" + (Fld $fl2 2) + "`t" + '-' + "`t" + 'hint' + "`t" + (Fld $fl2 3) + "`t" + (Fld $fl2 4) + "`t" + (Fld $fl2 5) + "`t" + (Fld $fl2 6) + "`t" + 'A' + "`t" + 'r1' + "`t" + (Fld $fl2 7)) }
# evidence_hash（B-180）：入账时对 evidence 文本计算行内容哈希（前 16 位，按账本转义形态）
if ($ftNew.Count -gt 0) {
    $hashed = [System.Collections.Generic.List[string]]::new()
    foreach ($l in $ftNew) {
        # bash 修复后：整行读+显式 %%/# 切分（空 evidence 列保位）；[0..3]=FT/type/loc/evidence，[4]='-' 占位弃，[5]=第 6 列起余部
        $c = $l -split "`t", 6
        $ev4 = Fld $c 3
        if ($null -eq $ev4) { $ev4 = '' }
        $h = Get-GsHashString $ev4
        if ($h.Length -gt 16) { $h = $h.Substring(0, 16) }
        $hashed.Add((Fld $c 0) + "`t" + (Fld $c 1) + "`t" + (Fld $c 2) + "`t" + (Fld $c 3) + "`t" + $h + "`t" + (Fld $c 5)) }
    Set-LfContent (Join-Path $S 'tmp/ft.new') $hashed }
else { Set-LfContent (Join-Path $S 'tmp/ft.new') @() }
# 协议合并（C-062）：sort -m 单输入=原序追加 + 行数恒等式对账（A-134/C-Inv08）
$BEFORE = @(Get-LfLines (Join-Path $S 'facts.tsv')).Count
if (@(Get-LfLines (Join-Path $S 'tmp/ft.new')).Count -gt 0) { Add-LfContent (Join-Path $S 'facts.tsv') @(Get-LfLines (Join-Path $S 'tmp/ft.new')) }
$ADD = @(Get-LfLines (Join-Path $S 'tmp/ft.new')).Count
$AFTER = @(Get-LfLines (Join-Path $S 'facts.tsv')).Count
Add-LfContent (Join-Path $S 'audit/facts-merge.log') @("3e-merge before=$BEFORE add=$ADD after=$AFTER")
if ($AFTER -ne ($BEFORE + $ADD)) {
    Out-Lf "❌ 行数恒等式破坏: before=$BEFORE + add=$ADD ≠ after=$AFTER（账本损坏——终止）"
    exit 1 }
# Confirmer 复核结果回写（VERDICT:{state}\t{FT-id}\t{理由}）
$rtPre = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 5) -ceq 'retracted') { $rtPre.Add((Fld $rW 0)) } }
Set-LfContent (Join-Path $S 'tmp/rt.pre') $rtPre
foreach ($cf in (Get-GsGlob (Join-Path $S 'shards') 'CONF-*.tsv')) {
    foreach ($l in @(Get-LfLines $cf)) {
        if (-not $l.StartsWith('VERDICT:')) { continue }
        $vc = $l -split "`t"
        $vd = Fld $vc 0; $fid = (Fld $vc 1) -creplace '\s', ''; $reason = Fld $vc 2
        if (-not $fid -clike 'FT-*') { continue }
        $nst = ''
        if ($vd -ceq 'VERDICT:confirmed') { $nst = 'confirmed' }
        elseif ($vd -ceq 'VERDICT:rejected') { $nst = 'rejected' }
        elseif ($vd -ceq 'VERDICT:retracted') { $nst = 'retracted' }
        else { continue }
        $OLDST = ''
        foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ((Fld $rW 0) -ceq $fid) { $OLDST = Fld $rW 5; break } }
        $out = [System.Collections.Generic.List[string]]::new()                 # B-186：confirmed 回写 confirmer 列
        foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $fid) { $rr[5] = $nst; if ($nst -ceq 'confirmed') { $rr[10] = 'CONF' } }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/ft.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/ft.tmp') (Join-Path $S 'facts.tsv')
        if ($nst -ceq 'retracted' -and $OLDST -cne 'retracted') {               # 翻案留痕（A-137，幂等）
            Add-LfContent (Join-Path $S 'audit/retract.log') @("RETRACT`t$fid`t（confirmer 翻案：$reason）") } } }
# retract 级联撤销（A-135/A-136——迭代至不动点，≤10 轮）
$PASSR = 0; $CHG = 1
while ($CHG -gt 0 -and $PASSR -lt 10) {
    $PASSR++; $CHG = 0
    $rtRet = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 5) -ceq 'retracted') { $rtRet.Add((Fld $rW 0)) } }
    Set-LfContent (Join-Path $S 'tmp/rt.ret') $rtRet
    $preSet = @{}; foreach ($x in $rtPre) { $preSet[$x] = 1 }
    $retSet = @{}; foreach ($x in $rtRet) { $retSet[$x] = 1 }
    $ch1 = 0
    $out = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
        $rr = Get-Row $rW
        if (-not $first -and (Fld $rW 5) -cne 'retracted' -and (Fld $rW 9) -cne '') {
            foreach ($u in ((Fld $rW 9) -split ',')) {
                if ($retSet.ContainsKey($u)) {
                    $rr[5] = 'retracted'; $ch1++
                    if (-not $preSet.ContainsKey((Fld $rW 0))) { Add-LfContent (Join-Path $S 'audit/retract.log') @("RETRACT-DERIVED`t$(Fld $rW 0)`tuses`t$u") }
                    break } } }
        $first = $false
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/ft.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/ft.tmp') (Join-Path $S 'facts.tsv')
    Set-LfContent (Join-Path $S 'tmp/rt1.chg') @("$ch1")      # bash awk END 落盘变更计数
    $ch2 = 0
    $out = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        $rr = Get-Row $rW
        if (-not $first -and ((Fld $rW 5) -cmatch '^k[0-9]') -and (Fld $rW 6) -cne '') {
            foreach ($fu2 in ((Fld $rW 6) -split ',')) {
                if ($retSet.ContainsKey($fu2)) {
                    Add-LfContent (Join-Path $S 'audit/retract.log') @("RETRACT-RESET`t$(Fld $rW 0)`tuses`t$fu2"); $ch2++
                    $rr[4] = 'unchecked'; $rr[5] = "fact-retracted:$fu2"; $rr[6] = ''
                    break } } }
        $first = $false
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv')
    Set-LfContent (Join-Path $S 'tmp/rt2.chg') @("$ch2")
    $CHG = $ch1 + $ch2 }
# Confirmer 派发清单（status=hint 且无 CONF 分片）
$toConfirm = [System.Collections.Generic.List[string]]::new()
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
    if ((Fld $rW 5) -ceq 'hint') { if (-not (Test-GsFile (Join-Path $S "shards/CONF-$(Fld $rW 0).tsv"))) { $toConfirm.Add((Fld $rW 0)) } } }
Set-LfContent (Join-Path $S 'tmp/to_confirm.txt') $toConfirm
foreach ($l in $toConfirm) { Out-Lf $l }

# ===== 3eenv: Confirmer 信封构造（{FT-id} 代入） =====
. "$S/env.ps1"
$FT = '{FT-id}'
foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
    if ((Fld $rW 0) -ceq $FT) {
        Out-Lf ("复核事实：" + $FT + "｜type=" + (Fld $rW 1) + "｜loc=" + (Fld $rW 2) + "｜scope=" + (Fld $rW 6) + ' ' + (Fld $rW 7) + "｜reflection_checked=" + (Fld $rW 8))
        $SROW = (Fld $rW 6) + "`t" + (Fld $rW 7)
        if (($SROW -split "`t")[0] -ceq 'entry_family') {
            $famQ = ($SROW -split "`t")[1]
            $first = $true
            foreach ($sr in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
                if ($first) { $first = $false; continue }
                if ((Fld $sr 7) -ceq $famQ) { Out-Lf ("成员：" + (Fld $sr 0) + "｜loc=" + (Fld $sr 2) + "｜auth=" + (Fld $sr 5) + "｜guards=" + (Fld $sr 6)) } } }
        break } }

# ===== 3f: attempt 计数（分片缺失 / 无 TERM / TERM 非法 同等计费） =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
foreach ($ck in @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt'))) {
    if ($ck -ceq '') { continue }
    $f = Join-Path $S "shards/A-$ck.tsv"
    $reason = ''
    if (-not (Test-GsFile $f)) { $reason = '分片缺失' }
    if ($reason -ceq '') {
        $st = ''
        foreach ($l in @(Get-LfLines $f)) { if ($l.StartsWith('TERM:')) { $l = $l -creplace '<TAB>', "`t"; $st = (($l -split "`t")[0]) -creplace '^TERM:', ''; break } }   # radiation-lens 第三处：迟到分片净化（误计费/误翻 partial 防护）
        $knd = ''
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $ck) { $knd = Fld $rW 1; break } }
        $okst = $false
        if ($st -cin @('candidate', 'refuted', 'not_applicable', 'no_path', 'blocked', 'partial')) { $okst = $true }
        elseif ($st -ceq 'deferred') { if ($knd -ceq 'ext') { $okst = $true } }
        if (-not $okst) { if ($st -ceq '') { $reason = '分片无TERM行' } else { $reason = "TERM非法($st)" } } }
    if ($reason -cne '') {
        Add-LfContent (Join-Path $S 'audit/attempt-failures.log') @($ck + "`t" + $reason + "`t" + "R$R")
        $out = [System.Collections.Generic.List[string]]::new()
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $ck) { $rr[7] = [string]([int](ConvertTo-GsNum (Fld $rW 7)) + 1) }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv')
        $att = '0'
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $rW 0) -ceq $ck) { $att = Fld $rW 7; break } }
        if ((ConvertTo-GsNum $att) -ge 2) {
            $out = [System.Collections.Generic.List[string]]::new()
            foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
                $rr = Get-Row $rW
                if ((Fld $rW 0) -ceq $ck) { $rr[4] = 'partial'; $rr[5] = "两次派发失败($reason)" }
                $out.Add((Join-Tsv $rr)) }
            Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
            Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv') } } }

# ===== 3g: 复核收卡（B-020 对称反转）——REVIEW:reversed 走翻案通道 =====
. "$S/env.ps1"
if (-not (Test-GsFile (Join-Path $S 'audit/reversal-reviewed.tsv'))) {
    Set-LfContent (Join-Path $S 'audit/reversal-reviewed.tsv') @('card_id' + "`t" + 'verdict') }
foreach ($rf in (Get-GsGlob (Join-Path $S 'shards') 'RV-*.tsv')) {
    $card = [IO.Path]::GetFileNameWithoutExtension($rf); $card = $card.Substring(3)
    $has = $false
    foreach ($rW in (Get-Tsv (Join-Path $S 'audit/reversal-reviewed.tsv'))) { if ((Fld $rW 0) -ceq $card) { $has = $true; break } }
    if ($has) { continue }
    $rline = ''
    foreach ($l in @(Get-LfLines $rf)) { if ($l.StartsWith('REVIEW:')) { $rline = $l; break } }
    if ($rline -ceq '') { continue }
    $rv = (($rline -split "`t")[0]) -creplace '^REVIEW:', ''
    if ($rv -cnotin @('reversed', 'upheld')) { continue }
    $reason = ($rline -split "`t")[1]
    Add-LfContent (Join-Path $S 'audit/reversal-reviewed.tsv') @($card + "`t" + $rv)
    Add-LfContent (Join-Path $S 'audit/reversal-review.log') @("REVERSAL $rv $card（$reason）")
    if ($rv -ceq 'reversed') {
        Add-LfContent (Join-Path $S 'audit/retract.log') @("RETRACT-RESET`t$card`t（对称反转复核翻案：卡重走五步——$reason）")
        $out = [System.Collections.Generic.List[string]]::new()
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $card) { $rr[4] = 'unchecked'; $rr[5] = 'reversal-review'; $rr[6] = '' }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv')
        $cand = ''
        if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 1) -ceq $card) { $cand = Fld $rW 0; break } } }
        if ($cand -cne '') {
            $out = [System.Collections.Generic.List[string]]::new()
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
                $rr = Get-Row $rW
                if ((Fld $rW 0) -ceq $cand) { $rr[6] = 'open'; $rr[7] = 'pending' }
                $out.Add((Join-Tsv $rr)) }
            Set-LfContent (Join-Path $S 'tmp/cd.tmp') $out
            Move-GsItem (Join-Path $S 'tmp/cd.tmp') (Join-Path $S 'candidates.tsv')
            if (Test-GsFile (Join-Path $S "shards/V-$cand.tsv")) { Move-GsItem (Join-Path $S "shards/V-$cand.tsv") (Join-Path $S "audit/reversed-V-$cand.tsv") }
            $cls = ''
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $cand) { $cls = Fld $rW 4; break } }
            $loc3 = ''
            foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $cand) { $loc3 = Fld $rW 5; break } }
            $fex = ''
            if ($loc3 -cne '') { $fex = Get-GsFex $loc3 }
            $fid = "F-$cand-$cls$fex"
            if (Test-GsFile (Join-Path $S 'machine-fields.tsv')) {
                $hit = $false
                foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $fid -and (Fld $rW 12) -ceq '') { $hit = $true; break } }
                if ($hit) {
                    $out = [System.Collections.Generic.List[string]]::new()
                    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
                        $rr = Get-Row $rW
                        if ((Fld $rW 0) -ceq $fid -and (Fld $rW 12) -ceq '') { $rr[12] = 'withdrawn' }
                        $out.Add((Join-Tsv $rr)) }
                    Set-LfContent (Join-Path $S 'tmp/mf.tmp') $out
                    Move-GsItem (Join-Path $S 'tmp/mf.tmp') (Join-Path $S 'machine-fields.tsv')
                    $fpath = Join-Path $S "findings/$fid.md"
                    if (Test-GsFile $fpath) {
                        $arc = Join-Path $S "audit/reversed-$fid.md"; $k = 1
                        while (Test-GsFile $arc) { $k++; $arc = Join-Path $S "audit/reversed-$fid-$k.md" }
                        Move-GsItem $fpath $arc
                        Add-LfText $arc "`n## 勘误（errata——只追加，原文未改写）`n- $(Get-GsTimestamp) lifecycle=withdrawn（对称反转复核翻案：$reason）——撤档留痕不蒸发，身份永续；重验证再交付走新行`n" }
                    Add-LfContent (Join-Path $S 'audit/coverage-degraded.log') @("REVERSED-FINDING $fid lifecycle=withdrawn 撤至 audit/（复核翻案——待重验证再交付）") } } } } }
$rr1 = 0
if (Test-GsFile (Join-Path $S 'audit/reversal-reviewed.tsv')) { $rr1 = @(Get-LfLines (Join-Path $S 'audit/reversal-reviewed.tsv')).Count - 1 }
$rvN = 0
foreach ($rW in (Get-Tsv (Join-Path $S 'audit/reversal-reviewed.tsv'))) { if ((Fld $rW 1) -ceq 'reversed') { $rvN++ } }
Out-Lf "3g 复核收卡: 已处理 $rr1 张（reversed $rvN）"

# ===== step4: 级联（K 规则——只关 band2 卡；S4 级联引擎 K1/K1b/K2/K3/K4） =====
. "$S/env.ps1"
# 剪枝事实必须 confirmed（C-Inv07）；只认 scope_type=file；K4 需 reflection_checked 非空
function Invoke-Krun([string]$ty, [string]$stX, [string]$pfx, [bool]$atloc, [bool]$needrc) {
    $fids = @{}; $floc = @{}
    foreach ($rW in (Get-Tsv (Join-Path $S 'facts.tsv'))) {
        if ((Fld $rW 1) -ceq $ty -and (Fld $rW 5) -ceq 'confirmed' -and (Fld $rW 6) -ceq 'file' -and ((-not $needrc) -or (Fld $rW 8) -cne '')) {
            $fx2 = Fld $rW 7
            if (-not $fids.ContainsKey($fx2)) { $fids[$fx2] = @() }
            $fids[$fx2] += Fld $rW 0
            if ($atloc) { $floc[$fx2] = Fld $rW 2 } } }
    $band = @{}; $sinkfile = @{}
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        $band[(Fld $rW 0)] = Fld $rW 5; $sinkfile[(Fld $rW 0)] = ((Fld $rW 2) -split ':')[0] }
    $out = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $out.Add((Join-Tsv $rW)); $first = $false; continue }      # 表头保位（bash 原地改写不删头）
        if ((Fld $rW 4) -ceq 'unchecked' -and (Fld $rW 1) -ceq 'bw') {
            $ref = Fld $rW 2
            $bd = '1'; if ($band.ContainsKey($ref)) { $bd = $band[$ref] }
            $sf = ''; if ($sinkfile.ContainsKey($ref)) { $sf = $sinkfile[$ref] }
            if ($bd -ceq '2' -and $sf -cne '' -and $fids.ContainsKey($sf)) {
                $rs2 = $pfx; if ($atloc) { $rs2 = $rs2 + ' at:' + $floc[$sf] }
                $rr = Get-Row $rW
                $rr[4] = $stX; $rr[5] = $rs2; $rr[6] = ($fids[$sf] -join ',')
                $out.Add((Join-Tsv $rr)) }
            else { $out.Add((Join-Tsv $rW)) } }
        else { $out.Add((Join-Tsv $rW)) } }
    Set-LfContent (Join-Path $S 'checks.tsv') $out }
Invoke-Krun 'uncontrolled' 'refuted'        'k1:uncontrolled' $false $false
Invoke-Krun 'intended'     'not_applicable' 'k1b:intended'    $false $false
Invoke-Krun 'kills'        'blocked'        'k2:kills'        $true  $false
Invoke-Krun 'no_edge'      'no_path'        'k3:no_edge'      $false $false
Invoke-Krun 'dead'         'no_path'        'k4:dead'         $false $true

# ===== 5a: 处理 Verifier 结果 → finding 文件 + machine-fields + 回写卡状态 =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
$PV = 'absent'
$patFiles = @(Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')
if ($patFiles.Count -gt 0) { $PV = Get-GsHashCat16 $patFiles }
if (-not (Test-GsFile (Join-Path $S 'machine-fields.tsv'))) {
    Set-LfContent (Join-Path $S 'machine-fields.tsv') @('finding_id' + "`t" + 'fingerprint' + "`t" + 'verdict' + "`t" + 'severity' + "`t" + 'class' + "`t" + 'sink' + "`t" + 'source' + "`t" + 'tier' + "`t" + 'also-reported-by' + "`t" + 'pattern_version' + "`t" + 'known_disclosed' + "`t" + 'human_triage' + "`t" + 'lifecycle' + "`t" + 'suite') }
foreach ($vf in (Get-GsGlob (Join-Path $S 'shards') 'V-*.tsv')) {
    $vlines = @(Get-LfLines $vf)
    $vline = ''
    foreach ($l in $vlines) { if ($l.StartsWith('VERDICT:')) { $vline = $l; break } }
    $verdict = ''
    if ($vline -cne '') { $verdict = (($vline -split "`t")[0]) -creplace '^VERDICT:', '' }
    if ($vline -ceq '' -or $verdict -cnotin @('confirmed', 'unconfirmed', 'refuted', 'dismissed')) {
        $cand_id = [IO.Path]::GetFileNameWithoutExtension($vf); $cand_id = $cand_id.Substring(2)
        Move-GsItem $vf (Join-Path $S "audit/degraded-$([IO.Path]::GetFileName($vf))")
        Add-LfContent (Join-Path $S 'audit/coverage-degraded.log') @("DEGRADED-V $cand_id VERDICT缺失或非法")
        $out = [System.Collections.Generic.List[string]]::new()
        foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $cand_id) { $rr[7] = 'degraded' }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/cd.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/cd.tmp') (Join-Path $S 'candidates.tsv')
        continue }
    $vc = $vline -split "`t"
    $sev = Fld $vc 1; $cvss = Fld $vc 2; $tier = Fld $vc 3
    $kd = Fld $vc 4; if ($kd -cne 'yes') { $kd = '' }
    $gap = Fld $vc 5
    $dsp = Fld $vc 6
    $cand_id = [IO.Path]::GetFileNameWithoutExtension($vf); $cand_id = $cand_id.Substring(2)
    $sink = ''; $srcq = ''; $loc = ''; $cls = ''; $card = ''
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $rW 0) -ceq $cand_id) { $sink = Fld $rW 2; $srcq = Fld $rW 3; $loc = Fld $rW 5; $cls = Fld $rW 4; $card = Fld $rW 1; break } }
    if ($cls -ceq '') { $cls = 'term' }
    if ($card -ceq '') { $card = 'unknown' }
    $HT = ''
    $clsPage = Join-Path $SK "classes/$cls.md"
    if (Test-GsFile $clsPage) { if (@(Get-LfLines $clsPage) | Where-Object { $_.StartsWith('> oracle: none') }) { $HT = 'yes' } }
    $fid = "F-$cand_id-$cls$(Get-GsFex $loc)"
    $dup = $false
    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $fid -and (Fld $rW 12) -ceq '') { $dup = $true; break } }
    if ($dup) { continue }
    $lfile = Remove-GsSuffix1 $loc ':'; $lline = Remove-GsPrefixL $loc ':'
    $q = ''
    if ($lline -cmatch '^[0-9]+$') { $q = Get-GsLine (Join-Path $SRC $lfile) ([int]$lline) }
    $fp = Get-GsHash16 ($lfile + "`n" + $q + "`n" + $cls + "`n")
    $DNOTE = ''; $FIXHIT = ''
    $today = Get-GsDate
    foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
        if (-not (Test-GsFile $df)) { continue }
        if ($DNOTE -ceq '') {
            $first = $true
            foreach ($rW in (Get-Tsv $df)) {
                if ($first) { $first = $false; continue }
                if ((Fld $rW 0) -ceq $fp) {
                    $sc = (Fld $rW 3) -split '\|'
                    if ($sc[0] -cne '' -and $sc[0] -cne $cls) { continue }
                    $ex = ''
                    if ((Fld $rW 6) -cne '' -and ((Fld $rW 6) -clt $today)) { $ex = '（已过期待复核）' } else { $ex = '（到期 ' + (Fld $rW 6) + '）' }
                    $DNOTE = (Fld $rW 1) + $ex; break } } }
        if ($FIXHIT -ceq '') {
            $first = $true
            foreach ($rW in (Get-Tsv $df)) {
                if ($first) { $first = $false; continue }
                if ((Fld $rW 0) -ceq $fp -and (Fld $rW 1) -ceq 'fixed') { $FIXHIT = '1'; break } } } }
    if ($FIXHIT -cne '') { Add-LfContent (Join-Path $S 'audit/disposition-notice.log') @("NOTICE-REGRESSION`t$fid`t$fp`t$(Get-GsTimestamp)") }
    if ($DNOTE -cne '') { Add-LfContent (Join-Path $S 'audit/disposition-notice.log') @("NOTICE-ANNOTATED`t$fid`t$fp`t$DNOTE") }
    $fname = "$fid.md"
    $sinkpos = ''
    if ($sink -cne '') { $sinkpos = $loc }
    if ($cand_id -cmatch '^CD-[0-9]{5}-[0-9]{5}$' -and $srcq -ceq '') { $srcq = '00000' }
    $arb = ''
    if (Test-GsFile (Join-Path $S 'audit/merge.log')) {
        $first = $true
        $acc = @()
        foreach ($rW in (Get-Tsv (Join-Path $S 'audit/merge.log'))) {
            if ((Fld $rW 0) -ceq 'MERGED' -and (Fld $rW 3) -ceq $cand_id) { $acc += Fld $rW 1 } }
        $arb = $acc -join ',' }
    $ashard = Join-Path $S "shards/A-$card.tsv"
    $aObs = @(); $aFact = @()
    if (Test-GsFile $ashard) {
        $aObs = @(@(Get-LfLines $ashard) | Where-Object { $_ -cmatch '^(OBS|ROLE):' })
        $aFact = @(@(Get-LfLines $ashard) | Where-Object { $_.StartsWith('FACT:') }) }
    $vSelf = @($vlines | Where-Object { $_.StartsWith('SELF:') })
    $vRub = @($vlines | Where-Object { $_.StartsWith('RUBRIC:') })
    $vbn = [IO.Path]::GetFileName($vf)
    $md = [System.Collections.Generic.List[string]]::new()
    $md.Add("# $cls ｜ $sev")
    $md.Add('')
    $md.Add("severity: $sev ｜ CVSS: $cvss ｜ tier: $tier ｜ verdict: $verdict")
    $md.Add("sink: $sink ｜ location: $loc")
    $md.Add("card: $card ｜ shards: A-$card.tsv + $vbn")
    if ($kd -ceq 'yes') { $md.Add('known-disclosed: yes（既往披露未修复——照常报告，B-034 标注）') }
    if ($gap -cne '') { $md.Add("deferred-evidence-gap: $gap（有界邻接扫描无果——缺口不是反证，D-111）") }
    if ($HT -ceq 'yes') { $md.Add('oracle: none ｜ reasoning-only ｜ human triage: required（本类无机械/执行 oracle——最终裁决显式交人工，A-012/B-033）') }
    if ($DNOTE -cne '') { $md.Add("disposition: $DNOTE（§10.2 两层分离——处置标注，verdict 不因此改写）") }
    if ($FIXHIT -cne '') { $md.Add('regression-NOTICE: fixed 处置同指纹复现——回归检测（C-046，audit/disposition-notice.log）') }
    if ($dsp -clike 'disp:*') { $md.Add("dismissed-cite: $($dsp.Substring(5))（抑制型复核成立——Verifier 裁决 dismissed 引用处置 ID，C-044）") }
    $md.Add('')
    $md.Add('## 1 概述')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 2 证据链（机械投影，禁止删改）')
    $md.Add('')
    $md.Add("### Analyzer 观察（A-$card.tsv）")
    if ($aObs.Count -gt 0) { foreach ($l in $aObs) { $md.Add('    ' + $l) } } else { $md.Add('    （无 OBS 行）') }
    $md.Add('')
    $md.Add("### Analyzer 事实（A-$card.tsv）")
    if ($aFact.Count -gt 0) { foreach ($l in $aFact) { $md.Add('    ' + $l) } } else { $md.Add('    （无 FACT 行）') }
    $md.Add('')
    $md.Add("### Verifier 独立观察（$vbn）")
    if ($vSelf.Count -gt 0) { foreach ($l in $vSelf) { $md.Add('    ' + $l) } } else { $md.Add('    （无 SELF 行）') }
    $md.Add('')
    $md.Add("### Verifier 判定基线（$vbn）")
    if ($vRub.Count -gt 0) { foreach ($l in $vRub) { $md.Add('    ' + $l) } } else { $md.Add('    （无 RUBRIC 行）') }
    $md.Add('')
    $md.Add('### 终判')
    $md.Add("    $vline")
    $md.Add('')
    $md.Add('## 3 净化分析')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 4 利用前提')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 5 PoC（tier: ' + $tier + '）')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 6 定级')
    $md.Add("severity: $sev ｜ CVSS: $cvss ｜ tier: $tier（Verifier 终判，机械字段）")
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 7 根因修复（含验收用例）')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 8 同类横向')
    $md.Add('<!--REPORTER-->')
    $md.Add('')
    $md.Add('## 9 参考')
    $md.Add('<!--REPORTER-->')
    New-GsDir (Join-Path $S 'findings')
    Set-LfContent (Join-Path $S "findings/$fname") $md
    Add-LfContent (Join-Path $S 'machine-fields.tsv') @($fid + "`t" + $fp + "`t" + $verdict + "`t" + $sev + "`t" + $cls + "`t" + $sinkpos + "`t" + $srcq + "`t" + $tier + "`t" + $arb + "`t" + $PV + "`t" + $kd + "`t" + $HT + "`t" + '' + "`t" + 'default')
    # 回写：仅 refuted/dismissed 是卡级终态写回 checks；判定与状态分离
    if ($card -cne '' -and ($verdict -ceq 'refuted' -or $verdict -ceq 'dismissed')) {
        $new_st = if ($verdict -ceq 'refuted') { 'refuted' } else { 'not_applicable' }
        $out = [System.Collections.Generic.List[string]]::new()
        foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
            $rr = Get-Row $rW
            if ((Fld $rW 0) -ceq $card) { $rr[4] = $new_st; $rr[5] = 'verifier:' + (Fld $rW 5) }
            $out.Add((Join-Tsv $rr)) }
        Set-LfContent (Join-Path $S 'tmp/ck.tmp') $out
        Move-GsItem (Join-Path $S 'tmp/ck.tmp') (Join-Path $S 'checks.tsv') }
    $out = [System.Collections.Generic.List[string]]::new()
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        $rr = Get-Row $rW
        if ((Fld $rW 0) -ceq $cand_id) { $rr[7] = 'delivered' }
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/cd.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/cd.tmp') (Join-Path $S 'candidates.tsv') }
Set-LfContent (Join-Path $S "audit/mark-5a-R$R") @()

# ===== 5b: live_findings_index.md 刷新（五节结构：第 0 节审计脉搏 + 四节——B-046/C-021/D2） =====
. "$S/env.ps1"
$R = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $R = @(Get-LfLines (Join-Path $S 'audit/round_count'))[0] }
$mfl = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; $mfl.Add((Join-Tsv $rW)) }
$MFSHA = 'empty'; $MFCNT = 0
if ($mfl.Count -gt 0) { $MFSHA = (Get-GsHash16 (($mfl -join "`n") + "`n")); $MFCNT = $mfl.Count }
Add-LfContent (Join-Path $S 'audit/mf-fp.log') @("R$R`t$MFSHA`t$MFCNT")
$today = Get-GsDate
$dispLive = [System.Collections.Generic.List[string]]::new()
foreach ($df in @((Join-Path $SK 'feedback/dispositions.tsv'), (Join-Path $S 'feedback/dispositions.tsv'))) {
    if (-not (Test-GsFile $df)) { continue }
    $first = $true
    foreach ($rW in (Get-Tsv $df)) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 0) -cne '') {
            $ex = (Fld $rW 6); if ((Fld $rW 6) -cne '' -and ((Fld $rW 6) -clt $today)) { $ex = '已过期待复核' }
            $dispLive.Add((Fld $rW 0) + "`t" + (Fld $rW 1) + '@' + $ex) } } }
Set-LfContent (Join-Path $S 'tmp/disp-live.tsv') $dispLive
$dispMap = @{}
foreach ($l in $dispLive) { $k = $l.Substring(0, $l.IndexOf("`t")); $dispMap[$k] = $l.Substring($l.IndexOf("`t") + 1) }   # awk d[$2]：后行覆盖前行（同指纹多处置取末行）
# D2 审计脉搏（P6）：live index 第 0 节纯机械投影——零发现轮次也回答"它在干什么、为什么没有发现"。
# 五要素（与 bash 侧 5b 同式）：①闭合数 ②状态分布 ③交付面占比（近 3 轮派单 bw 卡非 test/demo 占比——
# E1 日常版）④最接近 candidate 的卡（最近 3 张 reason 摘录；零候选时披露最近闭合卡）⑤ETA+token（0.8 同参数）
$P_T = 0; $P_D = 0
$P_CN = 0; $P_RF = 0; $P_NA = 0; $P_NP = 0; $P_BL = 0; $P_PA = 0; $P_DF = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $P_T++
    $st5 = Fld $rW 4
    if ($st5 -cne 'unchecked') {
        $P_D++
        switch ($st5) {
            'candidate' { $P_CN++ } 'refuted' { $P_RF++ } 'not_applicable' { $P_NA++ }
            'no_path' { $P_NP++ } 'blocked' { $P_BL++ } 'partial' { $P_PA++ } 'deferred' { $P_DF++ } } } }
$P_S = "candidate=$P_CN refuted=$P_RF not_applicable=$P_NA no_path=$P_NP blocked=$P_BL partial=$P_PA deferred=$P_DF"
$P_SF = @{}; $P_KD = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $P_SF[(Fld $rW 0)] = Remove-GsSuffix1 (Fld $rW 2) ':'      # ${loc%:*}——ref loc 首段=文件
    $P_KD[(Fld $rW 0)] = Fld $rW 1 }
$P_TD = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 5) -ceq 'test' -or (Fld $rW 5) -ceq 'demo') { $P_TD[(Fld $rW 1)] = $true } }
$P_DEL = 0; $P_TOT = 0
if (Test-GsFile (Join-Path $S 'audit/dispatch-history.log')) {
    foreach ($dl in (@(Get-LfLines (Join-Path $S 'audit/dispatch-history.log')) | Select-Object -Last 3)) {
        $cards = ($dl -split "`t", 2)
        if ($cards.Count -lt 2) { continue }
        foreach ($c in ($cards[1] -split ',')) {
            if ($c -ceq '') { continue }
            if ($P_SF.ContainsKey($c) -and $P_KD[$c] -ceq 'bw') {
                $P_TOT++
                if (-not $P_TD.ContainsKey($P_SF[$c])) { $P_DEL++ } } } } }
$P_PCT = 0; if ($P_TOT -gt 0) { $P_PCT = [math]::Floor($P_DEL * 100 / $P_TOT) }
$P_ALLT = 0
$P_SSF = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $P_SSF[(Fld $rW 0)] = Remove-GsSuffix1 (Fld $rW 2) ':' }
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'bw' -and $P_SSF.ContainsKey((Fld $rW 2)) -and $P_TD.ContainsKey($P_SSF[(Fld $rW 2)])) { $P_ALLT++ } }
$P_CH = '最近 candidate 卡（card｜kind｜reason 摘录）'
$P_CL = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 4) -ceq 'candidate') { $P_CL.Add((Fld $rW 0) + '｜' + (Fld $rW 1) + '｜' + ((Fld $rW 5).Substring(0, [Math]::Min(60, (Fld $rW 5).Length)))) } }
$P_C3 = @($P_CL | Select-Object -Last 3)
if ($P_C3.Count -eq 0) {
    $P_CH = '当前零 candidate——最近闭合卡（为什么没有发现：状态+原因摘录）'
    $P_CList = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 4) -cne 'unchecked') { $P_CList.Add((Fld $rW 0) + '｜' + (Fld $rW 1) + '｜' + (Fld $rW 4) + '｜' + ((Fld $rW 5).Substring(0, [Math]::Min(60, (Fld $rW 5).Length)))) } }
    $P_C3 = @($P_CList | Select-Object -Last 3) }
$P_W = ''
if (Get-Variable -Name WIDTH -ErrorAction SilentlyContinue) { $P_W = [string]$WIDTH }
if ($P_W -cnotmatch '^[1-9][0-9]*$') { $P_W = '4' }
$P_WI = [int](ConvertTo-GsNum $P_W)                    # 算术用整型（PS 字符串+数字=拼接，先转 int）
$P_RI = [int](ConvertTo-GsNum $R)
$P_EST = ''
if (Test-GsFile (Join-Path $S 'run-estimate.md')) {
    foreach ($l in @(Get-LfLines (Join-Path $S 'run-estimate.md'))) {
        if ($l -cmatch '^- 预计轮次: ([0-9]*)') { $P_EST = $Matches[1]; break } } }
if ($P_EST -ceq '') { $P_EST = [string]([math]::Floor(($P_T + $P_WI - 1) / $P_WI)) }
$P_ESTI = [int](ConvertTo-GsNum $P_EST)
$P_REM = $P_ESTI - $P_RI; if ($P_REM -lt 0) { $P_REM = 0 }
$P_TKLO = $P_RI * $P_WI * 20; $P_TKHI = $P_RI * ($P_WI + 3) * 80
$P_ETALO = [math]::Floor($P_REM * 90 / 60); $P_ETAHI = [math]::Floor($P_REM * 900 / 60)
$idx = [System.Collections.Generic.List[string]]::new()
$idx.Add('# Live Findings')
$idx.Add('')
$idx.Add("## 0 审计脉搏（R$R 快照——机械投影：零发现时也回答在干什么/为什么没有）")
$idx.Add("- 闭合: $P_D/$P_T 卡｜状态分布: $P_S")
$idx.Add("- 交付面占比: 近3轮派单 $P_DEL/$P_TOT = $P_PCT%（test/demo 污染 $($P_TOT - $P_DEL) 张在队尾——D4-A；全账本 bw 卡 test/demo $P_ALLT 张）")
$idx.Add("- 最接近 candidate: $P_CH")
if ($P_C3.Count -gt 0) { foreach ($l in $P_C3) { $idx.Add('  - ' + $l) } } else { $idx.Add('  - （尚无闭合卡）') }
$idx.Add("- ETA: 剩余 ≈$P_REM 轮 × 90–900s ≈ $P_ETALO–$P_ETAHI 分钟｜token 累计 ≈ ${R}轮 × $P_W–$($P_WI + 3) 子代理 × 20k–80k ≈ ${P_TKLO}k–${P_TKHI}k（0.8 同参数量级）")
$idx.Add('')
$idx.Add('## 1 当前发现（severity 降序——在役行）')
$idx.Add('| id | severity | class | sink | verdict | disposition | 详情 |')
$idx.Add('|---|---|---|---|---|---|---|')
$rank = @{ critical = 5; high = 4; medium = 3; low = 2; info = 1 }
$act = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 12) -ceq '') { $sc5 = 0; if ($rank.ContainsKey((Fld $rW 3))) { $sc5 = $rank[(Fld $rW 3)] }; $act.Add("$sc5`t$(Join-Tsv $rW)") } }
$actSorted = @($act | Sort-Ordinal)
$actOrd = @($actSorted | Sort-Object -Stable -Descending -Property { [int](ConvertTo-GsNum (($_ -split "`t")[0])) })
foreach ($l in $actOrd) {
    $f = ($l -split "`t", 2)[1] -split "`t"
    $dv = '—'; if ($dispMap.ContainsKey((Fld $f 1))) { $dv = $dispMap[(Fld $f 1)] }
    $idx.Add('| ' + (Fld $f 0) + ' | ' + (Fld $f 3) + ' | ' + (Fld $f 4) + ' | ' + (Fld $f 5) + ' | ' + (Fld $f 2) + ' | ' + $dv + ' | [打开](findings/' + (Fld $f 0) + '.md) |') }
$WD = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 12) -ceq 'withdrawn') { $WD++ } }
if ($WD -gt 0) { $idx.Add("（已翻案撤销 $WD 条——lifecycle=withdrawn：mf 行留痕、文件撤 audit/reversed-*；不混入上表）") }
$idx.Add('')
$idx.Add('## 2 open 候选（待验证投影——B-046；delivery_state=pending）')
$idx.Add('| cand | card | class | loc | delivery |')
$idx.Add('|---|---|---|---|---|')
if (Test-GsFile (Join-Path $S 'candidates.tsv')) {
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'candidates.tsv'))) {
        if ($first) { $first = $false; continue }
        if ((Fld $rW 7) -ceq 'pending') { $idx.Add('| ' + (Fld $rW 0) + ' | ' + (Fld $rW 1) + ' | ' + (Fld $rW 4) + ' | ' + (Fld $rW 5) + ' | pending |') } } }
$idx.Add('（空=当前无待验证候选；G1 种子行保持 open 属显式披露态）')
$idx.Add('')
$idx.Add('## 3 近期活动（近 3 轮派发尾巴——dispatch-history）')
if (Test-GsFile (Join-Path $S 'audit/dispatch-history.log')) { foreach ($l in (@(Get-LfLines (Join-Path $S 'audit/dispatch-history.log')) | Select-Object -Last 3)) { $idx.Add($l) } } else { $idx.Add('（无派发记录）') }
$idx.Add('')
$idx.Add('## 4 NOTICE（plateau/卡顿/降级机械状态行——C-020/C-021）')
if (Test-GsFile (Join-Path $S 'audit/stall.log')) { $idx.Add('- ⚠ 卡顿换道在案: ' + (@(Get-LfLines (Join-Path $S 'audit/stall.log')) | Select-Object -Last 1)) } else { $idx.Add('- 卡顿: 无记录') }
if (Test-GsFile (Join-Path $S 'audit/plateau.flag')) { $idx.Add('- ⚠ Plateau 强制停轮: ' + (@(Get-LfLines (Join-Path $S 'audit/plateau.flag'))[0])) } else { $idx.Add('- Plateau: 无') }
$NDG = 0; if (Test-GsFile (Join-Path $S 'audit/coverage-degraded.log')) { $NDG = @(@(Get-LfLines (Join-Path $S 'audit/coverage-degraded.log')) | Where-Object { $_ -cne '' }).Count }
$idx.Add("- 降级记录: $NDG 行（audit/coverage-degraded.log）")
if (Test-GsFile (Join-Path $S 'audit/disposition-notice.log')) {
    $nr = @(@(Get-LfLines (Join-Path $S 'audit/disposition-notice.log')) | Where-Object { $_.StartsWith('NOTICE-REGRESSION') }).Count
    $na = @(@(Get-LfLines (Join-Path $S 'audit/disposition-notice.log')) | Where-Object { $_.StartsWith('NOTICE-ANNOTATED') }).Count
    $idx.Add("- ⚠ 处置 NOTICE: 回归 $nr 条（fixed 同指纹复现——C-046）/ 标注 $na 条（audit/disposition-notice.log）") }
$idx.Add('')
$TOTAL_CARDS = 0; $DONE = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $TOTAL_CARDS++
    if ((Fld $rW 4) -cne 'unchecked') { $DONE++ } }
$CONFIRMED = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 2) -ceq 'confirmed') { $CONFIRMED++ } }
$idx.Add("进度: $DONE/$TOTAL_CARDS ｜ confirmed: $CONFIRMED")
Set-LfContent (Join-Path $S 'live_findings_index.md') $idx
Set-LfContent (Join-Path $S "audit/mark-5b-R$R") @()

# ===== 5c: progress_board.md 追加（无守卫——每执行一次=记账一轮） =====
. "$S/env.ps1"
$ROUND = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $ROUND = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/round_count'))[0])) }
$ROUND++; Set-LfContent (Join-Path $S 'audit/round_count') @("$ROUND")
$R = $ROUND
$D = 0; if (Test-GsFile (Join-Path $S 'tmp/dispatch_list.txt')) { $D = @(Get-LfLines (Join-Path $S 'tmp/dispatch_list.txt')).Count }
$C = 0; $CL = 0; $RM = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 4) -ceq 'candidate') { $C++ }
    if ((Fld $rW 4) -cne 'unchecked') { $CL++ }
    if ((Fld $rW 4) -ceq 'unchecked') { $RM++ } }
if (-not (Test-GsFile (Join-Path $S 'progress_board.md'))) {
    Set-LfContent (Join-Path $S 'progress_board.md') @('| 轮次 | 派卡 | 候选 | 闭合 | 剩余 |', '|---|---|---|---|---|') }
Add-LfContent (Join-Path $S 'progress_board.md') @("| R$ROUND | $D | $C | $CL | $RM |")
# NOTICE 行（C-020 W2：机械阈值触发，零 LLM 判断）
$EST_R = ''
if (Test-GsFile (Join-Path $S 'run-estimate.md')) {
    foreach ($l in @(Get-LfLines (Join-Path $S 'run-estimate.md'))) {
        if ($l -cmatch '^- 预计轮次: ([0-9]*)') { $EST_R = $Matches[1]; break } } }
$RT_NOW = 0; if (Test-GsFile (Join-Path $S 'audit/retract.log')) { $RT_NOW = @(@(Get-LfLines (Join-Path $S 'audit/retract.log')) | Where-Object { $_.StartsWith('RETRACT') }).Count }
$notices = [System.Collections.Generic.List[string]]::new()
if ($EST_R -cne '' -and $ROUND -gt ([int](ConvertTo-GsNum $EST_R) * 2)) {
    $notices.Add("| NOTICE | R$ROUND | 慢于预估：已 $ROUND 轮 > 预估 ${EST_R}×2（run-estimate.md 口径） |  |  |") }
if (Test-GsFile (Join-Path $S 'tmp/stall_lane')) { $notices.Add("| NOTICE | R$ROUND | L3 卡顿换道生效（audit/stall.log——B-060/B-072） |  |  |") }
$RT_PREV = 0; if (Test-GsFile (Join-Path $S 'audit/last_retract_notify')) { $RT_PREV = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/last_retract_notify'))[0])) }
if ($RT_NOW -gt $RT_PREV) { $notices.Add("| NOTICE | R$ROUND | 级联撤销发生：retract.log 本轮 +$($RT_NOW - $RT_PREV) 行（翻案级联——A-135） |  |  |") }
Add-LfContent (Join-Path $S 'progress_board.md') $notices
Set-LfContent (Join-Path $S 'audit/last_retract_notify') @("$RT_NOW")
Set-LfContent (Join-Path $S "audit/mark-5c-R$($ROUND - 1)") @()

# ===== 5dl: 待扩写清单（含占位符即待扩写） =====
. "$S/env.ps1"
$list = [System.Collections.Generic.List[string]]::new()
foreach ($f in (Get-GsGlob (Join-Path $S 'findings') 'F-*.md')) {
    if (@(Get-LfLines $f) | Where-Object { $_.Contains('<!--REPORTER-->') }) { $list.Add($f) } }
Set-LfContent (Join-Path $S 'tmp/to_report.txt') $list
foreach ($l in $list) { Out-Lf $l }

# ===== 5dg: Reporter 格式门 =====
. "$S/env.ps1"
foreach ($f in (Get-GsGlob (Join-Path $S 'findings') 'F-*.md')) {
    $ok = 1
    $fl = @(Get-LfLines $f)
    if ($fl | Where-Object { $_.Contains('<!--REPORTER-->') }) { $ok = 0 }
    if ($fl | Where-Object { $_ -cmatch '见分片|见 V-|见 A-|见类页面' }) { $ok = 0 }
    if (-not ($fl | Where-Object { $_ -cmatch ':[0-9]+' })) { $ok = 0 }
    if (@($fl | Where-Object { $_.StartsWith('## ') }).Count -lt 9) { $ok = 0 }
    $fidq = [IO.Path]::GetFileNameWithoutExtension($f)
    $cls = ''
    foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ((Fld $rW 0) -ceq $fidq) { $cls = Fld $rW 4; break } }
    if ($cls -ceq 'secrets-crypto') {
        $sec3 = $false
        for ($xi = 0; $xi -lt $fl.Count; $xi++) { if ($fl[$xi] -cmatch '^## 3 ') { $sec3 = $true } }
        if ($sec3) {
            $start = [array]::FindIndex($fl, [Predicate[string]] { param($x) $x -cmatch '^## 3 ' })
            for ($xi = $start; $xi -lt $fl.Count; $xi++) { if ($fl[$xi] -cmatch '[A-Za-z0-9+/]{32,}') { $ok = 0; break } } } }
    $line = "GATE-$(if ($ok -eq 1) { 'PASS' } else { 'FAIL' }) $([IO.Path]::GetFileName($f))"
    $gateF = Join-Path $S 'audit/reporter-gate.md'
    $has = $false
    if (Test-GsFile $gateF) { $has = [bool](@(Get-LfLines $gateF) | Where-Object { $_ -ceq $line }) }
    if (-not $has) { Add-LfContent $gateF @($line) } }
$rc5 = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $rc5 = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/round_count'))[0])) }
Set-LfContent (Join-Path $S "audit/mark-5d-R$($rc5 - 1)") @()

# ===== step6: 完成判定 =====
. "$S/env.ps1"
$U = 0; $UE = 0; $UED = 0; $TOT = 0; $PAR = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'checks.tsv'))) {
    if ($first) { $first = $false; continue }
    $kd = Fld $rW 1
    if ($kd -cne 'ext') { $TOT++; if ((Fld $rW 4) -ceq 'unchecked') { $U++ }; if ((Fld $rW 4) -ceq 'partial') { $PAR++ } }
    else { if ((Fld $rW 4) -ceq 'unchecked') { $UE++ }; if ((Fld $rW 4) -ceq 'deferred') { $UED++ } } }
Out-Lf "unchecked=$U（另有 ext 未闭合 $UE ｜ ext deferred $UED）"
# F3 交付物自洽：continue.log 是终态清单成员——零收口 run 也预建空账本件（空文件=零收口如实）
if (-not (Test-GsFile (Join-Path $S 'audit/continue.log'))) { Set-LfContent (Join-Path $S 'audit/continue.log') @() }
$PCT = 0; if ($TOT -gt 0) { $PCT = [math]::Floor($PAR * 100 / $TOT) }
if ($U -gt 0 -or $UE -gt 0) {
    $RCUR = 0; if (Test-GsFile (Join-Path $S 'audit/round_count')) { $RCUR = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/round_count'))[0])) }
    $PLAT = 0; $PM = ''
    $STALLED = 0
    if (Test-GsFile (Join-Path $S 'audit/last3.txt')) {
        $l3 = @(Get-LfLines (Join-Path $S 'audit/last3.txt'))
        $u3 = @($l3 | Sort-OrdinalU)
        if ($l3.Count -eq 3 -and $u3.Count -eq 1 -and ((ConvertTo-GsNum $l3[0]) -gt 0)) { $STALLED = 1 } }
    if ($RCUR -gt 2 -and $STALLED -eq 1 -and (Test-GsFile (Join-Path $S 'audit/mf-fp.log'))) {
        $mfl2 = @(Get-LfLines (Join-Path $S 'audit/mf-fp.log'))
        $MFL = $mfl2.Count
        $S3 = @(@($mfl2 | Select-Object -Last 3) | ForEach-Object { ($_ -split "`t")[1] } | Sort-OrdinalU).Count
        if ($MFL -ge 3 -and $S3 -eq 1) { $PLAT = 1; $PM = '返工缺口集合 3 轮不变' }
        if ($PLAT -eq 0 -and $MFL -ge 4) {
            $last4 = @($mfl2 | Select-Object -Last 4) | ForEach-Object { ($_ -split "`t")[2] }
            $bad = 0
            for ($xi = 1; $xi -lt 4; $xi++) { if ((ConvertTo-GsNum $last4[$xi]) -gt (ConvertTo-GsNum $last4[$xi - 1])) { $bad = 1 } }
            if ($bad -eq 0) { $PLAT = 1; $PM = '返工缺口数量 4 轮非递增' } } }
    if ($PLAT -eq 1) {
        Out-Lf "⚠ Plateau 强制停轮（$PM，R$RCUR——B-074/D-087）：返工缺口停滞，不再回 step0"
        Set-LfContent (Join-Path $S 'audit/plateau.flag') @("R$RCUR $PM（mf 指纹见 audit/mf-fp.log）——强制停轮，剩余未闭合如实披露")
        Out-Lf '→ 跳过 L2，直接【终态】（phases/terminal.md）——coverage 披露 plateau，EXIT_CODE=2 口径' }
    else {
        # D1-L3 批轮（P5 防自停）：每回合连续 N 轮再收口——收口≠总结，固定输出一行 GENSIFT-CONTINUE 续跑指令
        # （末行=续跑锚点；N 经发起参数 batch=N 与 width 同法贯通 env.ps1，缺省 3；回合终结白名单=SKILL.md 纪律卡第 9 条）
        if (-not (Get-Variable -Name BATCH -ErrorAction SilentlyContinue)) { $BATCH = '' }
        if ($BATCH -cnotmatch '^[1-9][0-9]*$') { $BATCH = 3 }
        # 每轮只计一次（宿主层重试 step6 不重复计——与 5a-5d mark 同一幂等原则）
        $LASTBR = -1; if (Test-GsFile (Join-Path $S 'audit/batch_last_round')) { $LASTBR = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/batch_last_round'))[0])) }
        $BR = 0; if (Test-GsFile (Join-Path $S 'audit/batch_rounds')) { $BR = [int](ConvertTo-GsNum (@(Get-LfLines (Join-Path $S 'audit/batch_rounds'))[0])) }
        if ($LASTBR -ne $RCUR) {
            Set-LfContent (Join-Path $S 'audit/batch_last_round') @("$RCUR")
            $BR++; Set-LfContent (Join-Path $S 'audit/batch_rounds') @("$BR") }
        if ($BR -ge [int](ConvertTo-GsNum $BATCH)) {
            Set-LfContent (Join-Path $S 'audit/batch_rounds') @('0')
            $K = 0
            if (Test-GsFile (Join-Path $S 'machine-fields.tsv')) {
                $first = $true
                foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $rW 2) -ceq 'confirmed') { $K++ } } }
            # F1：剩余计数含 ext（M=分母+ext 剩余总数，ext 计数括号披露）——ext-only 场景不再显示"剩余 0 卡"误导
            $CLINE = "GENSIFT-CONTINUE: 剩余 $($U + $UE) 卡(含 ext $UE)｜已 confirmed $K｜会话 $S"
            Add-LfContent (Join-Path $S 'audit/continue.log') @("R$RCUR`t$CLINE")
            Out-Lf "→ 批轮收口（本回合已连跑 $BATCH 轮）：本轮序列到此让出回合——禁止总结，续跑=把最后一行原样发回"
            Out-Lf $CLINE }
        else {
            Out-Lf "→ 回到 step0（直接继续下一轮——批轮 $BR/$BATCH，不总结不收口；回合终结白名单见 SKILL.md 循环纪律卡）" } } }
else {
    if ($UED -gt 0) { Out-Lf "⚠ 完成(有披露)：ext deferred=$UED 待带外证据——coverage 披露，不许谎称全绿" }
    if ($PCT -gt 10) { Out-Lf "⚠ D-086 质量缺口超阈值：partial $PAR/$TOT = $PCT% > 10%——不许宣称全闭合（coverage 披露，EXIT_CODE=2 口径）" }
    else { if ($PAR -gt 0) { Out-Lf "D-086 质量缺口披露：partial $PAR/$TOT = $PCT%（≤10% 不阻断，coverage 如实披露）" } }
    Out-Lf '→ L1 完成，进【L2 发散】' }

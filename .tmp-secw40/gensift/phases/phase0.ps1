# GenSift phases/phase0.ps1 —— phases/phase0.md 的 PowerShell 7 翻译件（任务10）
# 权威源 = phase0.md 的 16 个 bash 块；本件节标题与 md 块标题一一对应（`# ===== 节id: 标题 =====`）。
# 纯 Windows 宿主：按 win-init.md 发起后，执行到 phase0 阶段时逐节复制执行（每节首行自带 env 加载）。
# 翻译总则与 .NET 改写规则表见 phases/lib.ps1 头部（D-064）。

# ===== 0.0: pattern-lint + I1 fixture 快速门（枚举前常驻——B-079/D-065/D-068/D-069/C-Inv01） =====
. "$S/env.ps1"
# I1 门（会话内口径）三件事，失败即终态 exit 3——未验证知识禁止进枚举（B-079）。
# 黄金夹具双件对（POSIX/PS）在 dev 侧 gensift-dev/commands/golden——会话内不重跑（语料归属+成本）。
$GFAIL = 0
Set-LfContent (Join-Path $S 'audit/i1-gate.md') @()
Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("# I1 pattern-lint + fixture 抽样门（枚举前——$(Get-GsTimestamp)）")
$NSYN = 0; $NLINT = 0; $NDEAD = 0; $NWIDE = 0; $NSAMP = 0; $NUNC = 0
foreach ($patf in (Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')) {
    $base = [IO.Path]::GetFileName($patf) -creplace '\.pattern$', ''
    $CLASS = $base.Substring(0, $base.LastIndexOf('-'))                    # ${base%-*}
    $PLANG = $base.Substring($base.LastIndexOf('-') + 1)                   # ${base##*-}
    if (-not (Test-GsFile (Join-Path $SK "langpacks/$PLANG/includes.txt"))) { continue }
    $INC = @(Get-GsIncludes (Join-Path $SK "langpacks/$PLANG/includes.txt"))
    $FIXD = Join-Path $SK "fixtures/enum/$CLASS/$PLANG"
    $i = 0
    foreach ($row in (Get-Tsv $patf)) {                                    # 头部健壮解析：# 头行/表头不漂移数据行
        $patId = Fld $row 0; $ere = Fld $row 1
        if ($patId -cmatch '^#' -or $patId -ceq '' -or $patId -ceq 'pattern_id') { continue }
        if ($ere -ceq '') { continue }
        $i++
        $grc = 0
        try { $null = [regex]::New((Convert-ToDotNetRegex $ere)) } catch { $grc = 2 }   # grep -E 语法检（POSIX 类先改写——与实际匹配口径一致）
        if ($grc -eq 2) {
            Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("SYNTAX-FAIL`t$base`t$patId`tERE 语法坏"); $NSYN++; $GFAIL = 1; continue }
        if ($ere -cmatch '\\[bwdWsS]|\(\?') {
            Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("LINT-FAIL`t$base`t$patId`t禁用构造（schema §3）"); $NLINT++; $GFAIL = 1; continue }
        if ((($i - 1) % 5) -ne 0) { continue }
        if ($INC.Count -eq 0) { continue }
        $posd = Join-Path $FIXD 'pos'
        if (-not (Test-GsDir $posd)) { $NUNC++; continue }
        $NSAMP++
        $rx = Convert-ToDotNetRegex $ere
        $posFiles = @(Find-GsFiles $posd $INC)
        $hitPos = $false
        foreach ($pf in $posFiles) { if (Select-String -LiteralPath $pf -Pattern $rx -CaseSensitive -List) { $hitPos = $true; break } }
        if (-not $hitPos) {
            Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("DEAD`t$base`t$patId`t抽样 pos 零命中（死 pattern 不上线——D-069①）"); $NDEAD++; $GFAIL = 1 }
        $negd = Join-Path $FIXD 'neg'
        if (Test-GsDir $negd) {
            $hitNeg = $false
            foreach ($nf in @(Find-GsFiles $negd $INC)) { if (Select-String -LiteralPath $nf -Pattern $rx -CaseSensitive -List) { $hitNeg = $true; break } }
            if ($hitNeg) {
                Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("WIDE`t$base`t$patId`t抽样 neg 命中（过宽打回——D-069②）"); $NWIDE++; $GFAIL = 1 } }
    }
}
Add-LfContent (Join-Path $S 'audit/i1-gate.md') @('## guards 转录规则段级检查（A-074/A-075——段间独立：段缺失只降级该段，不拦门）')
foreach ($langd in (Get-ChildItem -LiteralPath (Join-Path $SK 'langpacks') -Directory | ForEach-Object FullName)) {
    $lang = [IO.Path]::GetFileName($langd)
    foreach ($seg in @('authn', 'authz', 'csrf', 'upload-check', 'rate-limit')) {
        $gf = Join-Path $langd "guards-$seg.md"
        if (-not (Test-GsFile $gf)) {
            Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("SEG-DEGRADED`t$lang`t$seg`t文件缺失（该段降级——发卡时该段记 unknown）"); continue }
        $miss = ''
        $gfl = @(Get-LfLines $gf)
        if (-not ($gfl | Where-Object { $_.Contains('三跳') })) { $miss += ' 三跳' }
        if (-not ($gfl | Where-Object { $_.Contains('来源') })) { $miss += ' 来源' }
        if ($miss -ceq '') { Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("SEG-OK`t$lang`t$seg`t段级锚齐") }
        else { Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("SEG-DEGRADED`t$lang`t$seg`t缺锚:${miss}（该段降级）") }
    }
}
# D-090 schema 单源投影检查：agents 单源格式串在 main-loop 解析处逐字节复现
$fmtT = 'TERM:{state}<TAB>{reason}<TAB>{facts_used}'
$fmtV = 'VERDICT:{三态|dismissed}<TAB>{severity}<TAB>{cvss}<TAB>{tier}'
$hitT1 = [bool](@(Get-LfLines (Join-Path $SK 'agents/analyzer.md')) | Where-Object { $_.Contains($fmtT) })
$hitT2 = [bool](@(Get-LfLines (Join-Path $SK 'phases/main-loop.md')) | Where-Object { $_.Contains($fmtT) })
if (-not ($hitT1 -and $hitT2)) { Add-LfContent (Join-Path $S 'audit/i1-gate.md') @('SCHEMA-DRIFT`tTERM 格式单源漂移（analyzer.md ↔ main-loop 3c）'); $GFAIL = 1 }
$hitV1 = [bool](@(Get-LfLines (Join-Path $SK 'agents/verifier.md')) | Where-Object { $_.Contains($fmtV) })
$hitV2 = [bool](@(Get-LfLines (Join-Path $SK 'phases/main-loop.md')) | Where-Object { $_.Contains($fmtV) })
if (-not ($hitV1 -and $hitV2)) { Add-LfContent (Join-Path $S 'audit/i1-gate.md') @('SCHEMA-DRIFT`tVERDICT 格式单源漂移（verifier.md ↔ main-loop 5a）'); $GFAIL = 1 }
Add-LfContent (Join-Path $S 'audit/i1-gate.md') @("统计: 语法坏=$NSYN lint坏=$NLINT 死pattern=$NDEAD 过宽=$NWIDE 抽样=$NSAMP 无fixture披露=$NUNC（D-067 neg 档位核对表见 gensift-dev/registers/calibration.md）")
if ($GFAIL -eq 1) {
    Out-GsTee (Join-Path $S 'audit/i1-gate.md') '❌ I1 门 FAIL——未验证知识禁止进枚举（B-079；exit 3=门未过，v1.4.0-S14）'
    exit 3 }
Out-GsTee (Join-Path $S 'audit/i1-gate.md') 'I1 门: PASS（抽样 20% 快速门；全量门=dev golden/smoke——D-041；PS 双件对=任务10.2）'

# ===== 0.2: 枚举 file 清单 =====
. "$S/env.ps1"
# 后缀全部来自 langpacks/*/includes.txt（语言包可插拔）；config 载体是跨语言协议常量。
# refreeze 前置归档（A-049）：既有冻结的会话重跑枚举=显式重测绘——覆盖前先把【旧】三清单归档。
$inv = Join-Path $S 'inventories'
if ((Test-GsFile (Join-Path $inv 'frozen.sha256')) -and -not (Test-GsFile (Join-Path $S 'audit/refreeze.pending'))) {
    $ts = (Get-Date).ToString('yyyyMMdd-HHmmss') + "-$PID"
    New-GsDir (Join-Path $S "audit/refreeze/pre-$ts")
    foreach ($f in (Get-GsGlob $inv '*.tsv')) { Copy-Item -LiteralPath $f -Destination (Join-Path $S "audit/refreeze/pre-$ts") -Force }
    Set-LfContent (Join-Path $S 'audit/refreeze.pending') @((Join-Path $S "audit/refreeze/pre-$ts"))
}
$GL = [System.Collections.Generic.List[string]]::new()
foreach ($incf in (Get-GsGlob (Join-Path $SK 'langpacks') '*/includes.txt')) {
    foreach ($g in (Get-GsIncludes $incf)) { $GL.Add($g) }
}
foreach ($g in @('*.yml', '*.yaml', '*.jinja2', '*.xml')) { $GL.Add($g) }
$abs = Find-GsFiles $SRC @($GL.ToArray())                                  # find -type f -name... | LC_ALL=C sort
Set-LfContent (Join-Path $S 'tmp/raw-files-abs.txt') $abs
$prefix = $SRC.TrimEnd('/') + '/'
Set-LfContent (Join-Path $S 'shards/enum/raw-files.tsv') @($abs | ForEach-Object { $_.Substring($prefix.Length) })
$sufmap = [System.Collections.Generic.List[string]]::new()
foreach ($incf in (Get-GsGlob (Join-Path $SK 'langpacks') '*/includes.txt')) {
    $lang = [IO.Path]::GetFileName([IO.Path]::GetDirectoryName($incf))
    foreach ($g in (Get-GsIncludes $incf)) { $sufmap.Add($g.Substring($g.IndexOf('.') + 1) + '=' + $lang) }
}
Set-LfContent (Join-Path $S 'tmp/sufmap.tsv') $sufmap
$langOf = @{}
foreach ($l in $sufmap) { $k = $l.Substring(0, $l.IndexOf('=')); if (-not $langOf.ContainsKey($k)) { $langOf[$k] = $l.Substring($l.IndexOf('=') + 1) } }
$out = [System.Collections.Generic.List[string]]::new()
$out.Add('seq' + "`t" + 'path' + "`t" + 'lang' + "`t" + 'loc' + "`t" + 'module' + "`t" + 'role')
$n = 0
foreach ($a in $abs) {
    $rel = $a.Substring($prefix.Length)
    $suffix = if ($rel.LastIndexOf('.') -ge 0) { $rel.Substring($rel.LastIndexOf('.') + 1) } else { $rel }   # ${rel##*.}
    $lang = 'config'; if ($langOf.ContainsKey($suffix)) { $lang = $langOf[$suffix] }
    $role = 'app'; $p = '/' + $rel
    if     ($p -clike '*/test/*' -or $p -clike '*/tests/*' -or $p -clike '*/__tests__/*') { $role = 'test' }
    elseif ($p -clike '*/vendor/*' -or $p -clike '*/node_modules/*' -or $p -clike '*/third_party/*') { $role = 'vendor' }
    elseif ($p -clike '*/example/*' -or $p -clike '*/examples/*' -or $p -clike '*/demo/*' -or $p -clike '*/demos/*' -or $p -clike '*/samples/*') { $role = 'demo' }
    elseif ($p -clike '*/docs/*' -or $p -clike '*/doc/*') { $role = 'docs' }
    if ($role -ceq 'app' -and $lang -ceq 'config') { $role = 'config' }
    $loc = @(Get-LfLines $a).Count                                          # wc -l
    if ($role -ceq 'app' -or $role -ceq 'config') {
        $over = @([System.IO.File]::ReadAllLines($a) | Where-Object { $_.Length -gt 2048 }).Count
        if ($loc -gt 0 -and ($over * 2) -gt $loc) {
            # generated 判定附核查（A-068）：树内存在同名非压缩源（x.min.ext→x.ext）则审计源
            $d = Remove-GsSuffix1 $rel '/'          # bash ${rel%/*}：无斜杠时回整个 rel（原文口径逐字对齐）
            $b = [IO.Path]::GetFileName($rel)
            $stem = Get-GsStem $b; $ext = $b.Substring($b.LastIndexOf('.') + 1); $sib = ''
            if ($stem -cmatch '\.min$') { $sib = ($d + '/' + $stem.Substring(0, $stem.Length - 4) + '.' + $ext) }
            if ($sib -ceq '' -or -not (Test-GsFile (Join-Path $SRC $sib))) { $role = 'generated' }
        }
    }
    $n++
    $out.Add(('FILE-{0:d5}' -f $n) + "`t" + $rel + "`t" + $lang + "`t" + $loc + "`t" + '-' + "`t" + $role)
}
Set-LfContent (Join-Path $inv 'file_inventory.tsv') $out

# ===== 0.2b: module 回填 =====
. "$S/env.ps1"
# recon/modules.md 末节 `## module-map`（file<TAB>module）join 回 file_inventory.module（B-151）
$mods = Join-Path $S 'recon/modules.md'
$mapRows = @()
if (Test-GsFile $mods) {
    $on = $false
    foreach ($r in (Get-Tsv $mods)) {
        if ((Fld $r 0) -ceq '## module-map') { $on = $true; continue }
        if ($on) { if ((Fld $r 0) -cmatch '^#' -or (Fld $r 1) -ceq '') { continue }; $mapRows += , @((Fld $r 0), (Fld $r 1)) } } }
if ($mapRows.Count -gt 0) {
    Set-LfContent (Join-Path $S 'tmp/module-map.tsv') @($mapRows | ForEach-Object { $_[0] + "`t" + $_[1] })
    $m = @{}
    foreach ($x in $mapRows) { $m[$x[0]] = $x[1] }
    $out = [System.Collections.Generic.List[string]]::new(); $first = $true
    foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
        if ($first) { $out.Add((Join-Tsv $r)); $first = $false; continue }
        $rr = Get-Row $r
        if ($m.ContainsKey((Fld $r 1))) { $rr[4] = 'mod:' + $m[(Fld $r 1)] }          # F1 来源标记：语义模块 mod:
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/fi.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/fi.tmp') (Join-Path $S 'inventories/file_inventory.tsv')
    $cnt = 0; $first = $true
    foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $r 4) -cmatch '^mod:') { $cnt++ } }
    Out-Lf "module 回填: $cnt 行（mod: 语义标记）"
} else {
    Out-Lf 'module 回填: recon/modules.md 无 module-map 节（module 列保持 '-'——coverage 披露）'
}
# D4-B③ module 回填补全（与 bash 0.2b 同式）：dir: 机械回填顶层目录；角色死角（test/vendor/demo/docs/generated）不回填保持 '-'
$deadRole = '^(test|vendor|demo|docs|generated)$'
$LEFT = 0; $DEAD = 0; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $r 4) -ceq '-' -or (Fld $r 4) -ceq '') {
        if ((Fld $r 5) -cmatch $deadRole) { $DEAD++ } else { $LEFT++ } } }
if ($LEFT -gt 0 -or $DEAD -gt 0) {
    $out = [System.Collections.Generic.List[string]]::new(); $first = $true
    foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
        if ($first) { $out.Add((Join-Tsv $r)); $first = $false; continue }
        $rr = Get-Row $r
        if (((Fld $r 4) -ceq '-' -or (Fld $r 4) -ceq '') -and ((Fld $r 5) -cnotmatch $deadRole)) {
            $d = (Fld $r 1) -creplace '^\./', ''
            $slash = $d.IndexOf('/')
            $rr[4] = 'dir:' + $(if ($slash -gt 0) { $d.Substring(0, $slash) } else { 'root' }) }
        $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/fi.mod') $out
    Move-GsItem (Join-Path $S 'tmp/fi.mod') (Join-Path $S 'inventories/file_inventory.tsv')
    Out-Lf "module 补全: dir: 机械回填 $LEFT 行（顶层目录约定）｜角色死角不回填 $DEAD 行（test/vendor/demo/docs/generated 保持 '-'——不是模块）"
}

# ===== 0.3: 枚举 sink 清单 =====
. "$S/env.ps1"
$raw = [System.Collections.Generic.List[string]]::new()
foreach ($patf in (Get-GsGlob (Join-Path $SK 'classes/patterns') '*.pattern')) {
    $base = [IO.Path]::GetFileName($patf) -creplace '\.pattern$', ''
    $CLASS = $base.Substring(0, $base.LastIndexOf('-')); $PLANG = $base.Substring($base.LastIndexOf('-') + 1)
    if (-not (Test-GsFile (Join-Path $SK "langpacks/$PLANG/includes.txt"))) { continue }
    $INC = @(Get-GsIncludes (Join-Path $SK "langpacks/$PLANG/includes.txt"))
    if ($INC.Count -eq 0) { continue }                                      # 空 --include 会全树扫——跳过
    $B = '1'
    foreach ($l in @(Get-LfLines $patf)) {                                   # band 从 pattern 文件头读——单一事实源
        if ($l -cmatch '^# band:') { $B = ($l.Substring($l.IndexOf(':') + 1)) -creplace '[ \t\r]', ''; break } }
    if ($B -cnotin @('0', '1', '2')) { $B = '1' }
    $files = @(Find-GsFiles $SRC $INC)
    foreach ($row in (Get-Tsv $patf)) {
        $patId = Fld $row 0; $ere = Fld $row 1
        if ($patId -ceq '') { continue }
        $rx = Convert-ToDotNetRegex $ere
        foreach ($m in (Select-String -LiteralPath $files -Pattern $rx -CaseSensitive)) {
            $raw.Add($m.Path + "`t" + $m.LineNumber + "`t" + $CLASS + "`t" + $patId + "`t" + $B) }
    }
}
$prefix = $SRC.TrimEnd('/') + '/'
$sorted = @($raw | ForEach-Object { $_.Replace($prefix, '') } | Sort-Ordinal)  # sed "s|$SRC/||" | LC_ALL=C sort
Set-LfContent (Join-Path $S 'shards/enum/raw-sinks.tsv') $sorted
$seen = @{}; $order = [System.Collections.Generic.List[string]]::new(); $n = 0
foreach ($r in $sorted) {
    $f = $r -split "`t"; $key = $f[2] + ':' + $f[0] + ':' + $f[1]            # key=class:file:line
    if (-not $seen.ContainsKey($key)) { $seen[$key] = $f[3]; $n++
        $order.Add(('SINK-{0:d5}' -f $n) + "`t" + 'FILE-' + "`t" + $f[0] + ':' + $f[1] + "`t" + $f[2] + "`t" + $f[3] + "`t" + $f[4]) }
    else { $seen[$key] = $seen[$key] + ',' + $f[3] } }
foreach ($k in $seen.Keys) { if ($seen[$k] -cmatch ',') { [Console]::Error.WriteLine("MULTI`t$k`t$($seen[$k])") } }
$seqOf = @{}; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }; $seqOf[(Fld $r 1)] = Fld $r 0 }
$out = [System.Collections.Generic.List[string]]::new()
foreach ($r in $order) {                                                    # file_seq 回填（B-162）
    $f = $r -split "`t"; $lf = ($f[2] -split ':')[0]; $fs = '-'
    if ($seqOf.ContainsKey($lf)) { $fs = $seqOf[$lf] }
    $out.Add($f[0] + "`t" + $fs + "`t" + $f[2] + "`t" + $f[3] + "`t" + $f[4] + "`t" + $f[5]) }
Set-LfContent (Join-Path $S 'inventories/sink_inventory.tsv') (@('seq' + "`t" + 'file_seq' + "`t" + 'loc' + "`t" + 'class_id' + "`t" + 'api' + "`t" + 'band') + $out)
Remove-GsFile (Join-Path $S 'tmp/sink_data.tsv'); Remove-GsFile (Join-Path $S 'tmp/sink_inv.tsv')

# ===== 0.4: 枚举 source 清单 =====
. "$S/env.ps1"
# 库/应用判定（recon/app-or-lib.md 首行 `verdict: app|lib`）——库模式 source 语义切换（A-077）
$MODE = 'app'
$aol = Join-Path $S 'recon/app-or-lib.md'
if (Test-GsFile $aol) {
    foreach ($l in (Get-LfLines $aol)) {
        if ($l -cmatch '^verdict:') { $v = $l.Substring($l.IndexOf(':') + 1).ToLower() -creplace '[ \t\r]', ''; $MODE = $v; break } } }
if ($MODE -cne 'lib') { $MODE = 'app' }
$raw = [System.Collections.Generic.List[string]]::new()
foreach ($langd in (Get-ChildItem -LiteralPath (Join-Path $SK 'langpacks') -Directory | ForEach-Object FullName)) {
    $lang = [IO.Path]::GetFileName($langd)
    $patf = Join-Path $langd 'sources.pattern'
    if ($MODE -ceq 'lib' -and (Test-GsFile (Join-Path $langd 'sources-lib.pattern'))) { $patf = Join-Path $langd 'sources-lib.pattern' }
    if (-not (Test-GsFile $patf)) { continue }
    if (-not (Test-GsFile (Join-Path $langd 'includes.txt'))) { continue }
    $INC = @(Get-GsIncludes (Join-Path $langd 'includes.txt'))
    if ($INC.Count -eq 0) { continue }
    $files = @(Find-GsFiles $SRC $INC)
    $lnNo = 0
    foreach ($row in (Get-Tsv $patf)) {
        $lnNo++
        if ($lnNo -le 4) { continue }                                       # awk 'NR>4 && $1!=""'
        $patId = Fld $row 0; $ere = Fld $row 1; $note = Fld $row 2
        if ($patId -ceq '') { continue }
        $ET = if ($MODE -ceq 'lib') { 'lib_api' } else { 'http' }           # entry_type 通道（B-156/A-082）
        if     ($note -cmatch 'band=weak') { $ET = 'weak' }
        elseif ($note -cmatch 'external_message') { $ET = 'external_message' }
        elseif ($note -cmatch 'persisted_read') { $ET = 'persisted_read' }
        $rx = Convert-ToDotNetRegex $ere
        foreach ($m in (Select-String -LiteralPath $files -Pattern $rx -CaseSensitive)) {
            $raw.Add($m.Path + "`t" + $m.LineNumber + "`t" + $patId + "`t" + $ET) } }
    $pp = Join-Path $langd 'persisted.pattern'                              # persisted_read 通道（A-079/D-028）
    if (Test-GsFile $pp) {
        foreach ($row in (Get-Tsv $pp)) {
            $patId = Fld $row 0; $ere = Fld $row 1
            if ($patId -ceq '') { continue }
            $rx = Convert-ToDotNetRegex $ere
            foreach ($m in (Select-String -LiteralPath $files -Pattern $rx -CaseSensitive)) {
                $raw.Add($m.Path + "`t" + $m.LineNumber + "`t" + $patId + "`t" + 'persisted_read') } } }
}
$prefix = $SRC.TrimEnd('/') + '/'
$sorted = @($raw | ForEach-Object { $_.Replace($prefix, '') } | Sort-OrdinalU)
Set-LfContent (Join-Path $S 'shards/enum/raw-sources.tsv') $sorted
$fwmap = [System.Collections.Generic.List[string]]::new()                    # framework 回填单一事实源（B-154/B-157）
foreach ($ft in (Get-GsGlob (Join-Path $SK 'langpacks') '*/frameworks.tsv')) {
    foreach ($r in (Get-Tsv $ft)) { $p = Fld $r 0; if ($p -cmatch '^#' -or ((ColCount $r) -lt 2)) { continue }; $fwmap.Add($p + "`t" + (Fld $r 1)) } }
Set-LfContent (Join-Path $S 'tmp/fw-map.tsv') $fwmap
$fs = @{}; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }; $fs[(Fld $r 1)] = Fld $r 0 }
$fw = @{}
foreach ($l in $fwmap) { $k = $l.Substring(0, $l.IndexOf("`t")); if (-not $fw.ContainsKey($k)) { $fw[$k] = $l.Substring($l.IndexOf("`t") + 1) } }
$out = [System.Collections.Generic.List[string]]::new(); $n = 0
foreach ($r in $sorted) {
    $f = $r -split "`t"; $n++
    $lf = ($f[0] -split ':')[0]; $fseq = 'FILE-'
    if ($fs.ContainsKey($lf)) { $fseq = $fs[$lf] }
    $fr = 'unknown'
    if ($f[3] -ceq 'persisted_read') { if ($fw.ContainsKey($f[2])) { $fr = $fw[$f[2]] } else { $fr = 'orm' } }
    elseif ($fw.ContainsKey($f[2])) { $fr = $fw[$f[2]] }
    $out.Add(('SRC-{0:d5}' -f $n) + "`t" + $fseq + "`t" + $f[0] + ':' + $f[1] + "`t" + $f[3] + "`t" + $fr + "`t" + 'unknown' + "`t" + 'authn:unknown|authz:unknown|csrf:unknown|upload-check:unknown|rate-limit:unknown' + "`t" + '-') }
Set-LfContent (Join-Path $S 'inventories/source_inventory.tsv') (@('seq' + "`t" + 'file_seq' + "`t" + 'loc' + "`t" + 'entry_type' + "`t" + 'framework' + "`t" + 'auth' + "`t" + 'guards' + "`t" + 'family') + $out)
Remove-GsFile (Join-Path $S 'tmp/si_data.tsv')
$srcCnt = 0; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ($first) { $first = $false; continue }; $srcCnt++ }
Out-Lf "source 枚举: $srcCnt 行（mode=$MODE）"

# ===== 0.4acc: guards 列验收 =====
. "$S/env.ps1"
$BADG = 0; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((ColCount $r) -ne 8) { $BADG++ } }
Out-Lf "guards列坏行: $BADG（>0 → 让子代理修复重验；仍>0 → 终止报告）"

# ===== 0.4b: family 半机械键派生 =====
. "$S/env.ps1"
# family（B-160/A-076）= 路由前缀|方法|param_shape——机械派生只读入口行本身
if (-not (Test-GsFile (Join-Path $S 'audit/family-corrections.tsv'))) {
    Set-LfContent (Join-Path $S 'audit/family-corrections.tsv') @('seq' + "`t" + 'old' + "`t" + 'new' + "`t" + 'reason') }
$si = Join-Path $S 'inventories/source_inventory.tsv'
$out = [System.Collections.Generic.List[string]]::new(); $der = [System.Collections.Generic.List[string]]::new()
$der.Add('seq' + "`t" + 'family')
$first = $true
foreach ($r in (Get-Tsv $si)) {
    if ($first) { $out.Add((Join-Tsv $r)); $first = $false; continue }
    $f = ''; $ln = 0; $line = ''
    $parts = (Fld $r 2) -split ':'; $f = $parts[0]; $ln = 0; if ($parts.Count -gt 1) { $ln = [int](ConvertTo-GsNum $parts[1]) }
    if ($f -cne '') { $line = Get-GsLine (Join-Path $SRC $f) $ln }
    $pre = '-'
    $m = [regex]::Match($line, '"[^"]*"')
    if ($m.Success) { $pre = $m.Value.Substring(1, $m.Value.Length - 2); $pre = $pre -creplace '\{[^}]*\}', '{p}'; $pre = $pre -creplace '[0-9]+', 'n' }
    $mth = '-'
    $m = [regex]::Match($line, '[A-Za-z_][A-Za-z0-9_]*\s*\(')
    if ($m.Success) { $mth = $m.Value; $mth = $mth -creplace '\s+$', ''; $mth = $mth -creplace '\($', '' }
    $shape = '-'
    $m = [regex]::Match($line, '\([^)]*\)')
    if ($m.Success) {
        $shape = $m.Value
        $shape = $shape -creplace '"[^"]*"', '"s"'
        $shape = $shape -creplace '[A-Za-z_][A-Za-z0-9_.]*', 'a'
        $shape = $shape -creplace '[0-9]+', 'n'
        $shape = $shape -creplace '\s+', ''
        if ($shape.Length -gt 48) { $shape = $shape.Substring(0, 48) } }
    $rr = Get-Row $r
    $rr[7] = $pre + '|' + $mth + '|' + $shape
    $out.Add((Join-Tsv $rr))
    $der.Add((Fld $r 0) + "`t" + $rr[7]) }
Set-LfContent (Join-Path $S 'tmp/si.tmp') $out
Move-GsItem (Join-Path $S 'tmp/si.tmp') $si
Set-LfContent (Join-Path $S 'tmp/family-derived.tsv') $der

# ===== 0.4c: family 修正合并 + auth 回填 =====
. "$S/env.ps1"
# FAM-fix 分片合并（guards 子代理修正——逐条归档 diff；按分片名记账防重复合并产幻影行）
$MF = Join-Path $S 'audit/fam-merged.txt'; if (-not (Test-GsFile $MF)) { Set-LfContent $MF @() }
$app = [System.Collections.Generic.List[string]]::new(); $corr = [System.Collections.Generic.List[string]]::new()
$mfLines = @(Get-LfLines $MF)
foreach ($ff in (Get-GsGlob (Join-Path $S 'shards') 'FAM-fix-*.tsv')) {
    $bn = [IO.Path]::GetFileName($ff)
    if ($mfLines -ccontains $bn) { continue }
    foreach ($r in (Get-Tsv $ff)) {
        if ((Fld $r 0) -cmatch '^SRC-' -and (ColCount $r) -ge 3) { $app.Add((Fld $r 0) + "`t" + (Fld $r 2)) }
        if ((Fld $r 0) -cmatch '^SRC-' -and (ColCount $r) -ge 4) { $corr.Add((Join-Tsv $r)) } }
    Add-LfContent $MF @($bn) }
Set-LfContent (Join-Path $S 'tmp/fam-app.tsv') @($app)          # bash：`: >` 预建 + 逐分片 `>>`——空也落盘
if ($app.Count -gt 0) {
    $fx = @{}; foreach ($l in $app) { $k = $l.Substring(0, $l.IndexOf("`t")); if (-not $fx.ContainsKey($k)) { $fx[$k] = $l.Substring($l.IndexOf("`t") + 1) } }
    Add-LfContent (Join-Path $S 'audit/family-corrections.tsv') $corr
    $si = Join-Path $S 'inventories/source_inventory.tsv'
    $out = [System.Collections.Generic.List[string]]::new()
    foreach ($r in (Get-Tsv $si)) { $rr = Get-Row $r; if ($fx.ContainsKey((Fld $r 0))) { $rr[7] = $fx[(Fld $r 0)] }; $out.Add((Join-Tsv $rr)) }
    Set-LfContent (Join-Path $S 'tmp/si.tmp') $out
    Move-GsItem (Join-Path $S 'tmp/si.tmp') $si }
# auth 回填（B-158）：按 guards authn 段机械三值化
$si = Join-Path $S 'inventories/source_inventory.tsv'
$out = [System.Collections.Generic.List[string]]::new(); $first = $true
foreach ($r in (Get-Tsv $si)) {
    if ($first) { $out.Add((Join-Tsv $r)); $first = $false; continue }
    $auth = 'unknown'; $g = Fld $r 6
    if ($g -cmatch '^authn:unknown') { $auth = 'unknown' }
    elseif ($g -cmatch '^authn:') {
        $seg = $g.Substring(6); $pos = $seg.IndexOf(':')
        $srcf = if ($pos -gt 0) { $seg.Substring(0, $pos) } else { $seg }
        $auth = if ($srcf -ceq '') { 'unauth' } else { 'auth' } }
    $rr = Get-Row $r
    $rr[5] = $auth; $out.Add((Join-Tsv $rr)) }
Set-LfContent (Join-Path $S 'tmp/si.tmp') $out
Move-GsItem (Join-Path $S 'tmp/si.tmp') $si
$siRows = @(Get-Tsv $si)
$cnt = { param($v) $c = 0; $first2 = $true; foreach ($r in $siRows) { if ($first2) { $first2 = $false; continue }; if ((Fld $r 5) -ceq $v) { $c++ } }; $c }
Out-Lf ("auth 分布: auth=" + (& $cnt 'auth') + " / unauth=" + (& $cnt 'unauth') + " / unknown=" + (& $cnt 'unknown'))

# ===== 0.5: G1 锚点预检 =====
. "$S/env.ps1"
# G1（C-011/A-087/A-089）：锚点输入=用户 advisory 清单；有锚点时位置必须 ⊆ 三清单
Set-LfContent (Join-Path $S 'audit/g1.md') @("G1: $(Get-GsTimestamp)")
if ($ADVISORY -cne '' -and (Test-GsFile $ADVISORY)) {
    Add-LfContent (Join-Path $S 'audit/g1.md') @("锚点来源: 用户advisory（$ADVISORY）")
    if (-not (Test-GsFile (Join-Path $S 'candidates.tsv'))) {
        Set-LfContent (Join-Path $S 'candidates.tsv') @('cand_id' + "`t" + 'card_id' + "`t" + 'sink_seq' + "`t" + 'source_seq' + "`t" + 'class_id' + "`t" + 'loc' + "`t" + 'verdict_state' + "`t" + 'delivery_state' + "`t" + 'summary') }
    $n = 0
    foreach ($r in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { $m = [regex]::Match((Fld $r 0), '^CD-SEED-'); if ($m.Success) { $t = [int](ConvertTo-GsNum ((Fld $r 0).Substring(8))); if ($t -gt $n) { $n = $t } } }
    $MISS = 0
    $seedLocs = @{}
    foreach ($r in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $r 1) -ceq 'G1') { $seedLocs[(Fld $r 5)] = 1 } }
    foreach ($row in (Get-Tsv $ADVISORY)) {
        $cve = Fld $row 0; $loc = Fld $row 1
        if ($cve -ceq '' -or $cve -cmatch '^#') { continue }
        if ($loc -ceq '') { continue }
        $f = Remove-GsSuffix1 $loc ':'
        $hit = ''
        $first = $true
        foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $r 1) -ceq $f) { $hit = 'in:file_inventory'; break } }
        if ($hit -ceq '') { $first = $true; foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ($first) { $first = $false; continue }; if (((Fld $r 2)).StartsWith($f + ':')) { $hit = 'in:source_inventory'; break } } }
        if ($hit -ceq '') { $first = $true; foreach ($r in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ($first) { $first = $false; continue }; if (((Fld $r 2)).StartsWith($f + ':')) { $hit = 'in:sink_inventory'; break } } }
        if ($hit -ceq '') { $hit = 'MISS'; $MISS++ }
        Add-LfContent (Join-Path $S 'audit/g1.md') @($cve + "`t" + $loc + "`t" + $hit)
        if ($hit -cne 'MISS' -and -not $seedLocs.ContainsKey($loc)) {                       # CVE/advisory 种子行（A-086）
            $n++
            Add-LfContent (Join-Path $S 'candidates.tsv') @(('CD-SEED-{0:d5}' -f $n) + "`t" + 'G1' + "`t" + '' + "`t" + '' + "`t" + 'seed' + "`t" + $loc + "`t" + 'open' + "`t" + 'pending' + "`t" + '')
            $seedLocs[$loc] = 1 } }
    if ($MISS -gt 0) {
        Out-GsTee (Join-Path $S 'audit/g1.md') "❌ G1 FAIL: $MISS 个锚点不在清单内——不过不开跑（终止并报告，退出码 3=门未过——v1.4.0-S14）"
        exit 3 }
    $sc = 0; foreach ($r in (Get-Tsv (Join-Path $S 'candidates.tsv'))) { if ((Fld $r 1) -ceq 'G1') { $sc++ } }
    Add-LfContent (Join-Path $S 'audit/g1.md') @("结果: PASS（种子行 $sc 条 state=open）")
} else {
    Add-LfContent (Join-Path $S 'audit/g1.md') @('锚点来源: 无')
    Add-LfContent (Join-Path $S 'audit/g1.md') @('结果: N/A（本目标无机械召回下界——coverage.md 披露）')
}

# ===== 0.5b: guards/family 冻结前抽样比对 =====
. "$S/env.ps1"
# A-090：guards/family 列 G1 前抽样 10% 与源码逐字比对——封印后无法修
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('## guards/family 抽样比对（每 10 行抽 1，冻结前）')
$fnr = 0
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    $fnr++
    if ($fnr -eq 1) { continue }
    if (($fnr % 10) -ne 2) { continue }
    foreach ($segG in ((Fld $r 6) -split '\|', -1)) {
        $m = [regex]::Match($segG, '@[^@]*:[0-9]+$')
        if (-not $m.Success) { continue }
        $tail = $m.Value.Substring(1)
        $ln = $tail; $ln = $tail.Substring($tail.LastIndexOf(':') + 1)
        $fl = $tail.Substring(0, $tail.Length - $ln.Length - 1)
        $rest = $segG.Substring(0, $m.Index); $rest = $rest -creplace '^[a-z-]+:', ''
        $pos = $rest.IndexOf(':'); $fact = if ($pos -gt 0) { $rest.Substring($pos + 1) } else { '' }
        if ($fact -ceq '' -or $fact -ceq '-') { continue }
        $line = Get-GsLine (Join-Path $SRC $fl) ([int](ConvertTo-GsNum $ln))
        if ($line -cne $fact) { $lines.Add("GUARD-DIFF`t$(Fld $r 0)`t$segG`t$fl`:$ln") } } }
$d = @{}; $first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'tmp/family-derived.tsv'))) { if ($first) { $first = $false; continue }; $d[(Fld $r 0)] = Fld $r 1 }
$c = @{}
if (Test-GsFile (Join-Path $S 'audit/family-corrections.tsv')) {
    $first = $true
    foreach ($r in (Get-Tsv (Join-Path $S 'audit/family-corrections.tsv'))) { if ($first) { $first = $false; continue }; $c[(Fld $r 0)] = 1 } }
$fnr = 0
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    $fnr++
    if ($fnr -eq 1) { continue }
    if (($fnr % 10) -ne 2) { continue }
    if ((Fld $r 7) -cne '-' -and $d.ContainsKey((Fld $r 0)) -and (Fld $r 7) -cne $d[(Fld $r 0)] -and -not $c.ContainsKey((Fld $r 0))) {
        $lines.Add("FAM-DIFF`t$(Fld $r 0)`t机械=$($d[(Fld $r 0)])`t现值=$(Fld $r 7)") } }
$lines.Add('（GUARD-DIFF/FAM-DIFF 行>0 → 让 guards 子代理修复后重验再冻结；封印后无法修）')
Add-LfContent (Join-Path $S 'audit/g1.md') $lines

# ===== 0.5c: I19 枚举对账 =====
. "$S/env.ps1"
# I19（C-Inv19/A-085）：清单行数 == 原始枚举输出行数，三向对账；差异逐行解释留档
function Invoke-Comm3([string[]]$A, [string[]]$B) {   # comm -3：A 独无前缀、B 独 TAB 前缀（双指针归并）
    $res = [System.Collections.Generic.List[string]]::new()
    $i = 0; $j = 0; $ord = [System.StringComparer]::Ordinal
    while ($i -lt $A.Count -and $j -lt $B.Count) {
        $cmp = $ord.Compare($A[$i], $B[$j])
        if ($cmp -lt 0) { $res.Add($A[$i]); $i++ }
        elseif ($cmp -gt 0) { $res.Add("`t" + $B[$j]); $j++ }
        else { $i++; $j++ } }
    while ($i -lt $A.Count) { $res.Add($A[$i]); $i++ }
    while ($j -lt $B.Count) { $res.Add("`t" + $B[$j]); $j++ }
    , $res.ToArray() }
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# I19 枚举对账（清单行数 == 原始枚举输出；差异逐行留档）')
$lines.Add('## file')
$raw = @(Get-LfLines (Join-Path $S 'shards/enum/raw-files.tsv'))
$first = $true; $invRows = @()
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) { if ($first) { $first = $false; continue }; $invRows += ,(Fld $r 1) }
$lines.Add("raw=$($raw.Count) inv=$($invRows.Count) diff=$($raw.Count - $invRows.Count)")
foreach ($l in (Invoke-Comm3 @($raw | Sort-Ordinal) @($invRows | Sort-Ordinal))) { $lines.Add("`t" + $l) }
$lines.Add('## sink')
$rawKeys = @(); $seen = @{}
foreach ($r in (Get-Tsv (Join-Path $S 'shards/enum/raw-sinks.tsv'))) { $k = (Fld $r 2) + ':' + (Fld $r 0) + ':' + (Fld $r 1); $rawKeys += ,$k }
$rawU = @($rawKeys | Sort-OrdinalU)
$first = $true; $invKeys = @(); $seen2 = @{}
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $a = ((Fld $r 2) -split ':'); $k = (Fld $r 3) + ':' + $a[0] + ':' + $a[1]
    if (-not $seen2.ContainsKey($k)) { $seen2[$k] = 1; $invKeys += ,$k } }
$invU = @($invKeys | Sort-OrdinalU)
$lines.Add("raw=$($rawU.Count) inv=$($invU.Count) diff=$($rawU.Count - $invU.Count)（raw=去重键计数，与 0.3 同键；原始命中 $($rawKeys.Count) 行中同行同类多次命中被 0.3 合并——MULTI 警告见 0.3 stderr）")
foreach ($l in (Invoke-Comm3 $rawU $invU)) { $lines.Add("`t" + $l) }
$lines.Add('## source')
$rawS = @(); $seenS = @{}
foreach ($r in (Get-Tsv (Join-Path $S 'shards/enum/raw-sources.tsv'))) { $k = (Fld $r 0) + ':' + (Fld $r 1) + "`t" + (Fld $r 3); if (-not $seenS.ContainsKey($k)) { $seenS[$k] = 1; $rawS += ,$k } }
$rawSU = @($rawS | Sort-OrdinalU)
$first = $true; $invS = @(); $seenI = @{}
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $a = ((Fld $r 2) -split ':'); $k = $a[0] + ':' + $a[1] + "`t" + (Fld $r 3)
    if (-not $seenI.ContainsKey($k)) { $seenI[$k] = 1; $invS += ,$k } }
$invSU = @($invS | Sort-OrdinalU)
$lines.Add("raw=$($rawSU.Count) inv=$($invSU.Count) diff=$($rawSU.Count - $invSU.Count)")
foreach ($l in (Invoke-Comm3 $rawSU $invSU)) { $lines.Add("`t" + $l) }
Set-LfContent (Join-Path $S 'audit/i19.md') $lines

# ===== 0.6: 冻结 =====
. "$S/env.ps1"
Set-LfContent (Join-Path $S 'inventories/frozen.sha256') @(Get-GsHashFiles @((Join-Path $S 'inventories/file_inventory.tsv'), (Join-Path $S 'inventories/source_inventory.tsv'), (Join-Path $S 'inventories/sink_inventory.tsv')))

# ===== 0.6b: refreeze 显式通道 =====
. "$S/env.ps1"
# refreeze（A-049/A-058）：仅当用户显式要求重测绘时执行——旧清单已在 0.2 归档，本块做哈希比对+留痕
if (Test-GsFile (Join-Path $S 'inventories/frozen.sha256')) {
    $NEWHASH = (Get-GsHashFiles @((Join-Path $S 'inventories/file_inventory.tsv'), (Join-Path $S 'inventories/source_inventory.tsv'), (Join-Path $S 'inventories/sink_inventory.tsv'))) -join "`n"
    $PEND = ''
    if (Test-GsFile (Join-Path $S 'audit/refreeze.pending')) { $PEND = @(Get-LfLines (Join-Path $S 'audit/refreeze.pending'))[0] }
    if ($NEWHASH -ceq ((Get-LfLines (Join-Path $S 'inventories/frozen.sha256')) -join "`n")) {
        if ($PEND -cne '' -and (Test-GsDir $PEND)) { Remove-GsTree $PEND }   # 幂等：清单未变删归档消戳不留痕
        Remove-GsFile (Join-Path $S 'audit/refreeze.pending')
        Out-Lf 'refreeze: 清单未变（哈希一致）——不归档不留痕（幂等）'
    } else {
        $old = (Get-LfLines (Join-Path $S 'inventories/frozen.sha256'))
        $log = [System.Collections.Generic.List[string]]::new()
        $log.Add("refreeze at $(Get-GsTimestamp) reason={用户显式要求} 旧清单归档=$(if ($PEND -cne '') { $PEND } else { '（无——清单在冻结前已被外部改动）' })")
        $log.Add('old:'); $log.AddRange([string[]]$old); $log.Add('new:')
        foreach ($l in ($NEWHASH -split "`n")) { $log.Add($l) }
        Add-LfContent (Join-Path $S 'audit/refreeze.log') $log
        Set-LfContent (Join-Path $S 'inventories/frozen.sha256') @($NEWHASH -split "`n")
        Remove-GsFile (Join-Path $S 'audit/refreeze.pending')
        New-GsDir (Join-Path $S 'audit')                                     # F1：基线重算挂戳传递
        Set-LfContent (Join-Path $S 'audit/refreeze-baseline.pending') @()
    }
} else {
    Out-Lf 'refreeze: 无既有冻结（首次冻结走 0.6；本块只处理显式重测绘）'
}

# ===== 0.7: 发卡 =====
. "$S/env.ps1"
# 发卡口径：term 只发 role∈{app,config}；fw 发 http+external_message；bw 全量。幂等：增量补发。
$body = [System.Collections.Generic.List[string]]::new()
$first = $true; $nr = 0
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
    if ($first) { $first = $false; continue }; $nr++
    $body.Add(('CK-bw-{0:d5}' -f $nr) + "`t" + 'bw' + "`t" + (Fld $r 0) + "`t" + '' + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') }
$first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $r 3) -ceq 'http' -or (Fld $r 3) -ceq 'external_message') {
        $body.Add('CK-fw-' + (Fld $r 0).Substring(4) + "`t" + 'fw' + "`t" + (Fld $r 0) + "`t" + '' + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') } }
$first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $r 5) -ceq 'app' -or (Fld $r 5) -ceq 'config') {
        $body.Add('CK-term-' + (Fld $r 0).Substring(5) + "`t" + 'term' + "`t" + (Fld $r 0) + "`t" + '' + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') } }
$bodySorted = @($body | Sort-Ordinal)
Set-LfContent (Join-Path $S 'tmp/ck.body') $bodySorted
$ckPath = Join-Path $S 'checks.tsv'
if ((Test-GsFile $ckPath) -and (Get-Item -LiteralPath $ckPath).Length -gt 0) {
    $seen = @{}; foreach ($r in (Get-Tsv $ckPath)) { $seen[(Fld $r 0)] = 1 }
    $newRows = [System.Collections.Generic.List[string]]::new()
    foreach ($l in $bodySorted) { $k = $l.Substring(0, $l.IndexOf("`t")); if (-not $seen.ContainsKey($k)) { $newRows.Add($l); $seen[$k] = 1 } }
    $NEWC = $newRows.Count
    Add-LfContent $ckPath $newRows
    Out-Lf "发卡（增量）: 新增 $NEWC 张（既有卡状态不动）"
} else {
    Set-LfContent $ckPath (@('card_id' + "`t" + 'kind' + "`t" + 'ref_seq' + "`t" + 'origin_ref' + "`t" + 'state' + "`t" + 'reason' + "`t" + 'facts_used' + "`t" + 'attempt' + "`t" + 'revision') + $bodySorted) }
Remove-GsFile (Join-Path $S 'tmp/ck.body')
# F1：refreeze 基线重置——0.6b 挂戳、发卡完成后按 step0 同口径重算覆写 last_unchecked
if (Test-GsFile (Join-Path $S 'audit/refreeze-baseline.pending')) {
    $OLDU = '?'; if (Test-GsFile (Join-Path $S 'audit/last_unchecked')) { $OLDU = (Get-LfLines (Join-Path $S 'audit/last_unchecked'))[0] }
    $CURU = 0; $first = $true
    foreach ($r in (Get-Tsv $ckPath)) { if ($first) { $first = $false; continue }; if ((Fld $r 1) -cne 'ext' -and (Fld $r 3) -ceq '' -and (Fld $r 4) -ceq 'unchecked') { $CURU++ } }
    Set-LfContent (Join-Path $S 'audit/last_unchecked') @("$CURU")
    Add-LfContent (Join-Path $S 'audit/refreeze.log') @("基线已重置 ${OLDU}→${CURU}（refreeze 发卡后按 step0 同口径重算——新分母卡不是违例）")
    Remove-GsFile (Join-Path $S 'audit/refreeze-baseline.pending') }

# ===== 0.7b: guards/family 差分与三跳抽样（B-080/B-081/B-082/A-072） =====
. "$S/env.ps1"
# B 轨差分：同 family guards 不一致成员 → 差分卡；全一致族抽样 1 入口做三跳核查
$famRows = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $r 7) -cne '-' -and (Fld $r 7) -cne '') { $famRows.Add((Fld $r 7) + "`t" + (Fld $r 0) + "`t" + (Fld $r 6)) } }
Set-LfContent (Join-Path $S 'tmp/fam-rows.tsv') $famRows
$gc = [ordered]@{}; $g7 = @{}; $mem = [ordered]@{}
foreach ($l in $famRows) {
    $f = $l -split "`t", 3
    $key = $f[0] + "`t" + $f[2]
    if (-not $gc.Contains($key)) { $gc[$key] = 0 }; $gc[$key]++
    $g7[$f[1]] = $f[2]
    if (-not $mem.Contains($f[0])) { $mem[$f[0]] = [System.Collections.Generic.List[string]]::new() }
    $mem[$f[0]].Add($f[1]) }
$gd = [System.Collections.Generic.List[string]]::new()
foreach ($f in @($mem.Keys)) {
    $best = ''; $bestn = -1
    foreach ($k in $gc.Keys) { $a = $k -split "`t", 2; if ($a[0] -ceq $f -and $gc[$k] -gt $bestn) { $bestn = $gc[$k]; $best = $a[1] } }
    $first2 = ''
    foreach ($id in $mem[$f]) {
        if ($g7[$id] -cne $best) { $gd.Add("OUTLIER`t$id`t$f") }
        elseif ($first2 -ceq '') { $first2 = $id } }
    if ($first2 -cne '') { $gd.Add("SAMPLE`t$first2`t$f") } }
$gdSorted = @($gd | Sort-Ordinal)
Set-LfContent (Join-Path $S 'tmp/gd-out.tsv') $gdSorted
$outLines = [System.Collections.Generic.List[string]]::new()
$outLines.Add("# guards/family 差分（B-080/B-081）+ 三跳抽样（B-082）——$(Get-GsTimestamp)")
$ckPath = Join-Path $S 'checks.tsv'
foreach ($l in $gdSorted) {
    $g3 = $l -split "`t", 3; $tag = $g3[0]; $seq = $g3[1]; $famv = $g3[2]
    if ($seq -ceq '') { continue }
    if ($tag -ceq 'OUTLIER') {
        $cid = 'CK-ext-GD-' + $seq.Substring(4)
        $has = $false; foreach ($r in (Get-Tsv $ckPath)) { if ((Fld $r 0) -ceq $cid) { $has = $true; break } }
        if (-not $has) { Add-LfContent $ckPath @($cid + "`t" + 'ext' + "`t" + $seq + "`t" + $seq + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1') }
        $outLines.Add("GUARD-DIFF`t$seq`tfamily=`tguards 与族众数不同——差分卡 $cid 已发（裁决走五步，不预判）")   # 忠实原文：md 块此处引用未定义 $f（恒空），翻译逐字对齐
    } elseif ($tag -ceq 'SAMPLE') {
        $outLines.Add("BIND-SAMPLE`t$seq`tfamily= 全一致——抽样三跳核查（下方派发；结果入 audit/guard-bind-review.log）")   # 同上：$f 未定义恒空
        foreach ($r in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) { if ((Fld $r 0) -ceq $seq) { $outLines.Add("  入口信封：$seq｜loc=$(Fld $r 2)｜guards 五段=$(Fld $r 6)"); break } } } }
Set-LfContent (Join-Path $S 'audit/guard-family-diff.md') $outLines
# GB 分片收卡（B-082 三跳核查结果——幂等记账，unbound 只披露不翻账）
if (-not (Test-GsFile (Join-Path $S 'audit/gb-merged.txt'))) { Set-LfContent (Join-Path $S 'audit/gb-merged.txt') @() }
$gbLines = @(Get-LfLines (Join-Path $S 'audit/gb-merged.txt'))
foreach ($gf in (Get-GsGlob (Join-Path $S 'shards') 'GB-*.tsv')) {
    $seq = [IO.Path]::GetFileNameWithoutExtension($gf); $seq = $seq.Substring(3)
    if ($gbLines -ccontains "GB-$seq") { continue }
    $rline = ''
    foreach ($l in @(Get-LfLines $gf)) { if ($l.StartsWith('REVIEW:')) { $rline = $l; break } }
    $rv = $rline.Substring(0, $rline.IndexOf("`t")); $rv = $rv -creplace '^REVIEW:', ''
    if ($rv -cnotin @('bound', 'unbound')) { continue }
    Add-LfContent (Join-Path $S 'audit/guard-bind-review.log') @("GB`t$seq`t$rv`t$(Get-GsTimestamp)")
    Add-LfContent (Join-Path $S 'audit/gb-merged.txt') @("GB-$seq") }
$gdCnt = 0; foreach ($r in (Get-Tsv $ckPath)) { if ((Fld $r 0) -cmatch '^CK-ext-GD-') { $gdCnt++ } }
$bindCnt = @((Get-LfLines (Join-Path $S 'audit/guard-family-diff.md')) | Where-Object { $_.StartsWith('BIND-SAMPLE') }).Count
$gbLog = 0; if (Test-GsFile (Join-Path $S 'audit/guard-bind-review.log')) { $gbLog = @(Get-LfLines (Join-Path $S 'audit/guard-bind-review.log')).Count }
Out-Lf "0.7b 差分: OUTLIER 卡 $gdCnt 张 ｜ 一致族抽样 $bindCnt 族 ｜ 三跳已复核 $gbLog 条（audit/guard-family-diff.md）"

# ===== 0.8: 启动预估（W1——A-007/C-019） =====
. "$S/env.ps1"
$ckPath = Join-Path $S 'checks.tsv'
$TOTAL = 0; $first = $true
foreach ($r in (Get-Tsv $ckPath)) { if ($first) { $first = $false; continue }; $TOTAL++ }
$cntInv = { param($col, $val) $c = 0; $first = $true; foreach ($r in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) { if ($first) { $first = $false; continue }; if ((Fld $r $col) -ceq $val) { $c++ } }; $c }
$B0 = & $cntInv 5 '0'; $B1 = & $cntInv 5 '1'; $B2 = & $cntInv 5 '2'
$cntK = { param($k) $c = 0; $first = $true; foreach ($r in (Get-Tsv $ckPath)) { if ($first) { $first = $false; continue }; if ((Fld $r 1) -ceq $k) { $c++ } }; $c }
$PC_LO = 90; $PC_HI = 900; $TK_LO = 20000; $TK_HI = 80000
$WID = 4; $wRaw0 = Get-Variable -Name WIDTH -ValueOnly -ErrorAction SilentlyContinue   # F4：老会话无 WIDTH 行——Get-Variable 探测（StrictMode 安全）
if ("$wRaw0" -cmatch '^[1-9][0-9]*$') { $WID = [int]$wRaw0 }   # D3' 缺省 4（width=N 经 env.ps1 贯通）
$ROUNDSE = [math]::Floor(($TOTAL + $WID - 1) / $WID)
$TLO = [math]::Floor($ROUNDSE * $PC_LO / 60); $THI = [math]::Floor($ROUNDSE * $PC_HI / 60)
$TKLO = [math]::Floor($ROUNDSE * $WID * $TK_LO / 1000); $TKHI = [math]::Floor($ROUNDSE * ($WID + 3) * $TK_HI / 1000)
$est = [System.Collections.Generic.List[string]]::new()
$est.Add('# 启动预估（W1——C-019/A-007）')
$est.Add("- 总卡数: $TOTAL（bw $(& $cntK 'bw') / fw $(& $cntK 'fw') / term $(& $cntK 'term')）")
$est.Add("- 分带统计: band0 $B0 ｜ band1 $B1 ｜ band2 $B2")
$est.Add("- 预计轮次: $ROUNDSE（每轮宽度 $WID 张——出处同 step1 派发宽度变量，D3' 发起参数 width=N 可调）")
$est.Add("- 时长区间（含无级联下界）: ${TLO}–${THI} 分钟——下界按「零 K 级联收益」计（不假设 K 规则消卡，级联只会让实际更短）；单卡时延 ${PC_LO}–${PC_HI}s × 轮次")
$est.Add("- token 投影: ${TKLO}k–${TKHI}k token（轮数 × 每轮 $($WID)–$($WID + 3) 子代理（宽度+fw/term/ext 保底 3）× 每子代理 ${TK_LO}–${TK_HI} token 量级）")
$est.Add('- 参数出处: PC_LO/PC_HI/WID/TK_LO/TK_HI 见 phases/phase0.md 0.8 块内注释（README 实测口径+回放观察；局限：宿主并发与模型速度差异可达 2×，首轮后回填）')
$est.Add("- 预估签字: □ 编排器确认上述投影与参数出处（实测每轮时延超 ${THI} 分钟 ×2 时 5c NOTICE 机械披露——C-020 联动）")
Set-LfContent (Join-Path $S 'run-estimate.md') $est

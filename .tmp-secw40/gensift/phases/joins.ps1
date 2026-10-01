# GenSift phases/joins.ps1 —— phases/joins.md 的 PowerShell 7 翻译件（任务10）
# 权威源 = joins.md 的 3 个 bash 块；节标题与 md 块标题一一对应。翻译总则见 phases/lib.ps1。

# ===== J1: 拼链轮派发（多模块才拼——Egress=契约=Ingress；单模块如实 N/A） =====
. "$S/env.ps1"
# 表头兜底（3d 已预建；旧会话续跑补——A-045/B-195）
if (-not (Test-GsFile (Join-Path $S 'joins.tsv'))) {
    Set-LfContent (Join-Path $S 'joins.tsv') @('join_id' + "`t" + 'egress_ref' + "`t" + 'contract_ref' + "`t" + 'ingress_ref' + "`t" + 'confidence' + "`t" + 'assumptions') }
# 触发口径：file_inventory.module 语义模块去重 ≥2（F1：只认 mod: 前缀并剥掉——dir: 机械回填不算；单模块 N/A 不虚派）
$modj = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $mv = Fld $rW 4
    if ($mv -cmatch '^mod:') { $modj.Add($mv.Substring(4)) } }
$MODJ = @($modj | Sort-OrdinalU).Count
Out-Lf "拼链轮: modules=$MODJ（≥2 才派 Reporter 拼链；单模块 N/A 如实——coverage 披露）"
if ($MODJ -ge 2) {
    # 机械信封（Reporter 只组织不制造）：sink/source 清单行 + 在役 mf 行
    $ji = [System.Collections.Generic.List[string]]::new()
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/sink_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        $ji.Add('sink' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 2) + "`t" + (Fld $rW 3)) }
    $first = $true
    foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/source_inventory.tsv'))) {
        if ($first) { $first = $false; continue }
        $ji.Add('src' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 2) + "`t" + (Fld $rW 3)) }
    if (Test-GsFile (Join-Path $S 'machine-fields.tsv')) {
        $first = $true
        foreach ($rW in (Get-Tsv (Join-Path $S 'machine-fields.tsv'))) {
            if ($first) { $first = $false; continue }
            if ((Fld $rW 12) -ceq '') { $ji.Add('mf' + "`t" + (Fld $rW 0) + "`t" + (Fld $rW 5) + "`t" + (Fld $rW 3)) } } }
    Set-LfContent (Join-Path $S 'tmp/join-input.txt') $ji
    Out-Lf "JOIN 输入: $($ji.Count) 行 → 派 Reporter（prompt 见下）" }

# ===== J2: JOIN 分片落账 + follow-up ext 卡 + dangling 披露（B-122/B-142/B-144/A-055） =====
. "$S/env.ps1"
# JOIN 分片机械合并入账（join_id 去重追加；重派/多轮不双计）
if (-not (Test-GsFile (Join-Path $S 'joins.tsv'))) {
    Set-LfContent (Join-Path $S 'joins.tsv') @('join_id' + "`t" + 'egress_ref' + "`t" + 'contract_ref' + "`t" + 'ingress_ref' + "`t" + 'confidence' + "`t" + 'assumptions') }
$jn = [System.Collections.Generic.List[string]]::new()
foreach ($jf in (Get-GsGlob (Join-Path $S 'shards') 'JOIN-*.tsv')) {
    foreach ($l in @(Get-LfLines $jf)) { if ($l.StartsWith('JN-')) { $jn.Add($l) } } }
$seen = @{}
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) { if ($first) { $first = $false; continue }; $seen[(Fld $rW 0)] = 1 }
$newRows = [System.Collections.Generic.List[string]]::new()
foreach ($l in $jn) {
    $k = ($l -split "`t")[0]
    if (-not $seen.ContainsKey($k)) { $newRows.Add($l); $seen[$k] = 1 } }
Add-LfContent (Join-Path $S 'joins.tsv') $newRows
# assumptions 非空 → follow-up ext 卡（origin_ref=join_id——假设点必复核）
$NJ = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) {
    if ($first) { $first = $false; continue }
    $jid = Fld $rW 0
    if ($jid -ceq '') { continue }
    $as = Fld $rW 5
    if ($as -ceq '') { continue }
    $cid = "CK-ext-$jid"
    $has = $false
    foreach ($r2 in (Get-Tsv (Join-Path $S 'checks.tsv'))) { if ((Fld $r2 0) -ceq $cid) { $has = $true; break } }
    if ($has) { continue }
    Add-LfContent (Join-Path $S 'checks.tsv') @($cid + "`t" + 'ext' + "`t" + $jid + "`t" + $jid + "`t" + 'unchecked' + "`t" + '' + "`t" + '' + "`t" + '0' + "`t" + 'r1')
    $NJ++ }
# dangling 披露数据（B-145：无对端=egress/ingress 为 NA 的行）
$dg = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) {
    if ($first) { $first = $false; continue }
    if ((Fld $rW 1) -ceq 'NA' -or (Fld $rW 3) -ceq 'NA') { $dg.Add((Fld $rW 0) + "`t" + (Fld $rW 5)) } }
Set-LfContent (Join-Path $S 'tmp/joins-dangling.txt') $dg
$jcnt = 0
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'joins.tsv'))) { if ($first) { $first = $false; continue }; $jcnt++ }
Out-Lf "拼链落账: $jcnt 行｜follow-up 卡 +$NJ（I13 闭合口径）｜dangling $($dg.Count) 行"
Set-LfContent (Join-Path $S 'audit/joins-round-done') @()
if ($NJ -gt 0) {
    Out-Lf "→ follow-up ext 卡 $NJ 张回主循环派发（下轮 2b ext 分支；闭合前不得终态——I13 拦截）" }
else {
    Out-Lf '→ 无新 follow-up 卡，直接【终态】（phases/terminal.md）' }

# ===== J3: 组合分析派发 + combinations.md 存在性检查（C-009/C-023/D-055） =====
. "$S/env.ps1"
# 存在性检查（阶段/终态两处同口径——缺失=降级披露不静默不阻断；单模块 N/A 不记降级）
$modcQ = [System.Collections.Generic.List[string]]::new()
$first = $true
foreach ($rW in (Get-Tsv (Join-Path $S 'inventories/file_inventory.tsv'))) {
    if ($first) { $first = $false; continue }
    $mv = Fld $rW 4
    if ($mv -cne '-' -and $mv -cne '') { $modcQ.Add($mv) } }
$MODC = @($modcQ | Sort-OrdinalU).Count
$comb = Join-Path $S 'combinations.md'
if ($MODC -lt 2) {
    Out-Lf 'combinations: N/A（单模块——无跨模块链，组合件通道未开；与 J1 拼链同触发口径，不计降级）' }
elseif ((Test-GsFile $comb) -and (Get-Item -LiteralPath $comb).Length -gt 0) {
    Out-Lf "combinations.md 在档（$(@(Get-LfLines $comb).Count) 行）——存在性 PASS" }
else {
    Add-LfContent (Join-Path $S 'audit/coverage-degraded.log') @('COMBINATIONS 未产出（Reporter 组合轮未返回——如实披露不静默，C-009/D-055）')
    Out-Lf 'combinations.md 缺失：已记降级（audit/coverage-degraded.log；终态 coverage 再披露一次）' }

# GenSift phases/lib.ps1 —— PowerShell 翻译件公共底座（任务10，D-043/D-064）
# 权威源=gensift/phases/*.md 的 bash 块；本文件只提供等价原语与 .NET 改写规则表，
# 不含任何业务步骤。每节（phases/*.ps1 的 `# ===== 标题 =====` 分节）可独立复制执行，
# 首行 `. "$S/env.ps1"`（env.ps1 由 phases/win-init.md 发起块生成，内含 . lib.ps1）。
#
# ── .NET 等价改写规则表（D-064；R1——POSIX 字符类 → .NET 方言）──────────────────
# | POSIX 字符类 | .NET 等价 | 备注                                  |
# |--------------|-----------|---------------------------------------|
# | [:alpha:]    | a-zA-Z    | Unicode 字母用 \p{L}                  |
# | [:digit:]    | 0-9       | 或 \d（.NET \d 含 Unicode 数字）       |
# | [:alnum:]    | a-zA-Z0-9 | Unicode 版 \p{L}\p{Nd}                |
# | [:upper:]    | A-Z       |                                       |
# | [:lower:]    | a-z       |                                       |
# | [:space:]    | \s        | .NET \s 含 \t\n\r\f\v 及 Unicode 空白  |
# | [:blank:]    | \t␣       | 横向制表或空格 → [\t ]                |
# | [:xdigit:]   | 0-9A-Fa-f |                                       |
# | [:punct:]    | \p{P}     | Unicode 标点类别                      |
# | [:cntrl:]    | \p{Cc}    |                                       |
# | [:print:]    | \x20-\x7E |                                       |
# | [:graph:]    | \x21-\x7E |                                       |
# | [:word:]     | \w        | GNU 扩展                              |
# pattern 文件的 ere 列进 Select-String 前必须先过 Convert-ToDotNetRegex（机械执行本表）。
# 其余差异备忘：\b 双方词边界（.NET 按 Unicode 判词字符）；{n,m}/+?/|/分组同形；
# POSIX collating [.x.]/[=x=] .NET 不支持（现存 pattern 未使用）。
#
# ── 翻译总则（R2-R5，黄金等价前提）─────────────────────────────────────────────
# R2 行尾/编码：读=[IO.File]::ReadAllLines（剥 \n 与 \r\n）；写禁用 >/>>/Out-File/Set-Content
#    （CRLF/编码不定），统一 Set-LfContent/Add-LfContent（UTF-8 无 BOM + LF）。
#    Get-FileHash 输出大写 hex，shasum 小写——一律 .ToLower()。
# R3 排序：LC_ALL=C sort = 字节序全序 → 只允许 Sort-Ordinal/Sort-OrdinalU
#    （[StringComparer]::Ordinal）；Sort-Object 默认区域性排序（'a'<'B'）禁用。
# R4 大小写：PS 比较默认不敏感——一律 -ceq/-cne/-cmatch/-cnotmatch/-clike/-cin/-creplace；
#    cmdlet 加 -CaseSensitive。
# R5 原语映射：grep -n→Select-String；comm→Compare-Object -CaseSensitive（计数判定等等，
#    逐行输出用哈希差集）；wc -l→行数组 .Count；shasum→Get-GsHash*（小写）；
#    date +%F\ %T→Get-GsTimestamp；head/tail→Select-Object -First/-Last。
#
# ── 协议文本契约（设计 §9/B-222：跨平台字节等价的三件硬约定）────────────────────
# ① 路径正斜杠：会话产物（账本/分片/报告）中写路径一律正斜杠（'/'）。PowerShell 的
#    Join-Path 在 Windows 产出反斜杠——凡落盘路径先过 (… -creplace '\\','/')；本底座
#    的落盘函数不代改调用方内容，调用方按本契约自查（等价断言由黄金 harness 把两侧
#    会话根归一后逐字节比对保证）。
# ② UTF-8 无 BOM：一切落盘走 Set-LfContent/Set-LfText/Add-LfContent/Add-LfText
#    （UTF8Encoding($false) + LF 行尾）；禁用 >/>>/Out-File/Set-Content（行尾/编码不定）。
# ③ 排序规范化等价：凡"排序后比对/落盘"处，bash 侧 LC_ALL=C sort = 字节序全序，
#    PS 侧唯一等价物是 Sort-Ordinal/Sort-OrdinalU（[StringComparer]::Ordinal）——
#    Sort-Object 默认区域性排序（'a'<'B'）与本契约不等价，禁用于产物路径。
# 大规模逐行不变量的单遍预载（设计 §9/B-224）见 Get-GsLine 的行数组缓存。

Set-StrictMode -Version 3 -ErrorAction SilentlyContinue
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }

# ── 输出（stdout 逐字节对齐 bash echo：LF + UTF-8 无 BOM）──
function Out-Lf { param([string]$Line = '')
    [System.Console]::Out.Write($Line + "`n") }

# ── 读写（R2）──
function Get-LfLines {                    # 读文本为行数组（剥 \n 与 \r\n）
    param([Parameter(Mandatory)][string]$Path)
    [System.IO.File]::ReadAllLines($Path) }
function Test-GsFile { param([string]$Path) $null -ne $Path -and (Test-Path -LiteralPath $Path -PathType Leaf) }
function Test-GsDir  { param([string]$Path) $null -ne $Path -and (Test-Path -LiteralPath $Path -PathType Container) }
function Set-LfContent {                  # 覆盖写：行数组 → LF + UTF-8 无 BOM
    param([string]$Path, [string[]]$Lines = @())
    if (@($Lines).Count -eq 0) { [System.IO.File]::WriteAllText($Path, '', $Utf8NoBom); return }
    [System.IO.File]::WriteAllText($Path, (@($Lines) -join "`n") + "`n", $Utf8NoBom) }
function Set-LfText {                      # 覆盖写：整段文本原样落盘（不补行尾）
    param([string]$Path, [string]$Text = '')
    [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom) }
function Add-LfContent {                  # >> 追加，同 LF 规则
    param([string]$Path, [string[]]$Lines = @())
    if (@($Lines).Count -eq 0) { return }
    [System.IO.File]::AppendAllText($Path, (@($Lines) -join "`n") + "`n", $Utf8NoBom) }
function Add-LfText {                      # >> 追加整段文本原样
    param([string]$Path, [string]$Text = '')
    if ($Text -eq '') { return }
    [System.IO.File]::AppendAllText($Path, $Text, $Utf8NoBom) }
function New-GsDir  { param([string]$Path) if ($Path -and -not (Test-GsDir $Path)) { [System.IO.Directory]::CreateDirectory($Path) | Out-Null } }
function Remove-GsFile { param([string]$Path) if (Test-GsFile $Path) { Remove-Item -LiteralPath $Path -Force } }
function Remove-GsTree { param([string]$Path) if ($Path -and (Test-Path -LiteralPath $Path)) { Remove-Item -LiteralPath $Path -Recurse -Force } }
function Move-GsItem { param([string]$From, [string]$To) if (Test-Path -LiteralPath $From) { Move-Item -LiteralPath $From -Destination $To -Force } }

# ── TSV 账本（awk -F'\t' 同语义：手工切分，不走 CSV 引号规则——字段可含 "）──
function Get-Tsv {                        # awk -F'\t' 逐行读：行=包裹对象（.Row=string[]）——PS 管道会摊平裸数组，
    param([Parameter(Mandatory)][string]$Path)          # 单行文件因此漂移成字段迭代；包裹对象在 foreach/( )/@() 三种消费形态下都不漂移
    $out = [System.Collections.Generic.List[object]]::new()
    foreach ($ln in [System.IO.File]::ReadAllLines($Path)) { $out.Add([pscustomobject]@{ Row = [string[]]($ln -split "`t") }) }
    $out.ToArray() }
function Get-Row {                        # 行包裹对象解包 → string[]（逗号包裹防单字段行被摊平成标量）
    param($Row)
    if ($null -eq $Row) { return , [string[]]@() }
    if ($Row -is [string]) { return , [string[]]@($Row) }
    if ($Row.PSObject.Properties['Row']) { return , [string[]]$Row.Row }
    , [string[]]$Row }
function Get-TsvLines {                   # 逐行产出原始行（含 TAB）
    param([Parameter(Mandatory)][string]$Path)
    [System.IO.File]::ReadAllLines($Path) }
function Fld {                            # awk $N 越界 = ''（缺列忠实 awk；接受包裹行或裸 string[]）
    param($Row, [int]$Index)
    $r = Get-Row $Row
    if ($null -eq $r) { return '' }
    if ($Index -lt $r.Count) { [string]$r[$Index] } else { '' } }
function Join-Tsv { param($Row) (Get-Row $Row) -join "`t" }
function ColCount { param($Row) $r = Get-Row $Row; @($r).Count }

# ── 排序（R3）──
function Sort-Ordinal {                   # LC_ALL=C sort（管道或位置传参均可）
    param([string[]]$Items)
    $src = if ($null -ne $Items) { $Items } else { @($input) }
    $l = [System.Collections.Generic.List[string]]::new([string[]]$src)
    $l.Sort([System.StringComparer]::Ordinal); $l.ToArray() }
function Sort-OrdinalU {                  # LC_ALL=C sort -u
    param([string[]]$Items)
    $src = if ($null -ne $Items) { $Items } else { @($input) }
    $l = [System.Collections.Generic.List[string]]::new([string[]]@($src | Select-Object -Unique))
    $l.Sort([System.StringComparer]::Ordinal); $l.ToArray() }
function Sort-OrdinalDesc {               # LC_ALL=C sort -r
    param([string[]]$Items)
    $src = if ($null -ne $Items) { $Items } else { @($input) }
    $l = [System.Collections.Generic.List[string]]::new([string[]]$src)
    $l.Sort([System.StringComparer]::Ordinal)
    if ($l.Count -gt 1) { [array]($l.ToArray()[($l.Count - 1)..0]) } elseif ($l.Count -eq 1) { $l.ToArray() } else { @() } }

# ── 集合差（comm；计数判定与逐行哈希差集两种形态）──
function Get-Comm23 {                     # comm -23 A B：仅在 A 的行（保留重复、序数字节序）
    param([string[]]$A, [string[]]$B)
    $hs = [System.Collections.Generic.HashSet[string]]::new([string[]]@($B), [System.StringComparer]::Ordinal)
    foreach ($x in @($A)) { if (-not $hs.Contains([string]$x)) { $x } } }
function Get-Comm13 {                     # comm -13 A B：仅在 B 的行
    param([string[]]$A, [string[]]$B)
    $hs = [System.Collections.Generic.HashSet[string]]::new([string[]]@($A), [System.StringComparer]::Ordinal)
    foreach ($x in @($B)) { if (-not $hs.Contains([string]$x)) { $x } } }

# ── 哈希（shasum -a 256 等价：小写 hex）──
function Get-GsHashString {               # printf '%s' "$x" | shasum —— UTF-8 字节哈希（空串=空输入哈希 e3b0…，合法值）
    param([string]$Text = '')
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text)) | ForEach-Object { $_.ToString('x2') }) -join '' }
    finally { $sha.Dispose() } }
function Get-GsHash16 { param([string]$Text = '') (Get-GsHashString $Text).Substring(0, 16) }
function Get-GsHashFile {                 # shasum <file>（裸哈希，小写）
    param([Parameter(Mandatory)][string]$Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { ($sha.ComputeHash([System.IO.File]::ReadAllBytes($Path)) | ForEach-Object { $_.ToString('x2') }) -join '' }
    finally { $sha.Dispose() } }
function Get-GsHashFiles {                # shasum f1 f2 f3 —— 多文件逐行 "hash  name"（两空格，落盘序=参数序）
    param([Parameter(Mandatory)][string[]]$Paths)
    foreach ($p in $Paths) { '{0}  {1}' -f (Get-GsHashFile $p), [System.IO.Path]::GetFileName($p) } }
function Test-GsChecksums {               # shasum -c：逐行 hash  name 校验（true=全过）
    param([Parameter(Mandatory)][string]$Dir, [Parameter(Mandatory)][string]$Manifest)
    $ok = $true
    if (-not (Test-GsFile $Manifest)) { return $false }
    foreach ($ln in Get-LfLines $Manifest) {
        if ($ln -cnotmatch '^([0-9a-f]{64})  (.+)$') { $ok = $false; continue }
        $h, $n = $Matches[1], $Matches[2]
        $p = Join-Path $Dir $n
        if (-not (Test-GsFile $p) -or (Get-GsHashFile $p) -cne $h) { $ok = $false } }
    $ok }
function Get-GsHashCat16 {                # cat a b | shasum | cut -c1-16 —— 拼接字节哈希前 16
    param([Parameter(Mandatory)][string[]]$Paths)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $ms = [System.IO.MemoryStream]::new()
        foreach ($p in $Paths) { if (Test-GsFile $p) { $b = [System.IO.File]::ReadAllBytes($p); $ms.Write($b, 0, $b.Length) } }
        $h = ($sha.ComputeHash($ms.ToArray()) | ForEach-Object { $_.ToString('x2') }) -join ''
        $h.Substring(0, 16) }
    finally { $sha.Dispose() } }

# ── 日期（date '+%F %T' / +%F）──
function Get-GsTimestamp { (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') }
function Get-GsDate { (Get-Date).ToString('yyyy-MM-dd') }

# ── 行取值（sed -n "${n}p"：缺行=空）──
function Get-GsLine { param([string]$Path, [int]$N)
    # 单遍预载（设计 §9/B-224）：按调用进程缓存已读文件的行数组——逐行取行不再每行整读一次文件
    #（否则大规模逐行不变量 I9 在 PS 上是 O(行数×文件大小) 的反复整读，小时到天级）。源码树在会话内
    # 只读（I17 写边界），缓存无失效窗口。
    if ($N -lt 1) { return '' }
    if (-not $script:GsLineCache.ContainsKey($Path)) {
        if (-not (Test-GsFile $Path)) { $script:GsLineCache[$Path] = [string[]]@() }
        else { $script:GsLineCache[$Path] = [System.IO.File]::ReadAllLines($Path) } }
    $ls = $script:GsLineCache[$Path]
    if ($N -le $ls.Count) { [string]$ls[$N - 1] } else { '' } }
$script:GsLineCache = @{}

# ── 正则改写（R1 机械执行改写表）──
function Convert-ToDotNetRegex {
    param([string]$Pattern)
    if ($null -eq $Pattern) { return '' }
    $map = [ordered]@{
        '[:alpha:]' = 'a-zA-Z';   '[:digit:]' = '0-9';      '[:alnum:]' = 'a-zA-Z0-9'
        '[:upper:]' = 'A-Z';      '[:lower:]' = 'a-z';      '[:space:]' = '\s'
        '[:blank:]' = '\t ';      '[:punct:]' = '\p{P}';    '[:xdigit:]' = '0-9A-Fa-f'
        '[:cntrl:]' = '\p{Cc}';   '[:graph:]' = '\x21-\x7E'; '[:print:]' = '\x20-\x7E'
        '[:word:]'  = '\w'
    }
    foreach ($k in $map.Keys) { $Pattern = $Pattern.Replace($k, $map[$k]) }
    $Pattern }

# ── 递归枚举（find $D -type f \(-name g1 -o -name g2...\) -not -path '*/.git/*'，输出绝对路径字节序）──
function Find-GsFiles {                   # -Glob 形如 '*.py'（可多个）；全树（含隐藏），跳 .git 段
    param([Parameter(Mandatory)][string]$Dir, [string[]]$Glob = @())
    if (-not (Test-GsDir $Dir)) { return @() }
    $pats = @($Glob | Where-Object { $_ })
    $stack = [System.Collections.Generic.Stack[string]]::new()
    $stack.Push((Resolve-Path -LiteralPath $Dir).ProviderPath)
    $out = [System.Collections.Generic.List[string]]::new()
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        foreach ($e in [System.IO.Directory]::EnumerateFileSystemEntries($d)) {
            if ([System.IO.Path]::GetFileName($e) -ceq '.git') { continue }
            $ap = [System.IO.Path]::GetFullPath($e)
            if (Test-GsDir $ap) { $stack.Push($ap); continue }
            if ($pats.Count -eq 0) { $out.Add($ap); continue }
            foreach ($g in $pats) {
                $w = [System.Management.Automation.WildcardPattern]::new($g, [System.Management.Automation.WildcardOptions]::None)
                if ($w.IsMatch([System.IO.Path]::GetFileName($ap))) { $out.Add($ap); break } } } }
    $l = [System.Collections.Generic.List[string]]::new([string[]]$out)
    $l.Sort([System.StringComparer]::Ordinal); $l }

# ── 文件通配枚举（bash glob "$S"/shards/A-*.tsv：按名字节序；不存在=空）──
function Get-GsGlob {                     # -Pattern 形如 'shards/A-*.tsv' / '*/includes.txt'（相对 Base；目录段逐级通配，单层 *）
    param([Parameter(Mandatory)][string]$Base, [Parameter(Mandatory)][string]$Pattern)
    if (-not (Test-GsDir $Base)) { return @() }
    $segs = @($Pattern -split '/')
    $dirs = [System.Collections.Generic.List[string]]::new()
    $dirs.Add((Resolve-Path -LiteralPath $Base).ProviderPath)
    for ($si = 0; $si -lt $segs.Count - 1; $si++) {
        $w = [System.Management.Automation.WildcardPattern]::new($segs[$si], [System.Management.Automation.WildcardOptions]::None)
        $next = [System.Collections.Generic.List[string]]::new()
        foreach ($d in $dirs) {
            foreach ($e in [System.IO.Directory]::EnumerateDirectories($d)) {
                if ($w.IsMatch([System.IO.Path]::GetFileName($e))) { $next.Add($e) } } }
        $dirs = $next; if ($dirs.Count -eq 0) { return @() } }
    $wf = [System.Management.Automation.WildcardPattern]::new($segs[$segs.Count - 1], [System.Management.Automation.WildcardOptions]::None)
    $l = [System.Collections.Generic.List[string]]::new()
    foreach ($d in $dirs) {
        foreach ($e in [System.IO.Directory]::EnumerateFiles($d)) {
            if ($wf.IsMatch([System.IO.Path]::GetFileName($e))) { $l.Add($e) } } }
    $l.Sort([System.StringComparer]::Ordinal); $l.ToArray() }

# ── includes.txt 后缀装载（跳注释/空行）──
function Get-GsIncludes {                 # 产出 @('*.py', ...)；文件缺失=空
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-GsFile $Path)) { return @() }
    $a = foreach ($g in Get-LfLines $Path) {
        if ($g -ceq '' -or $g -cmatch '^#') { continue }; $g.TrimEnd("`r") }
    @($a | Where-Object { $_ }) }

# ── pattern 文件数据行（awk '$1!~/^#/ && $1!="" && $1!="pattern_id"'；带 -SkipHeader 时剥 #--- 后表头行）──
function Get-GsPatternRows {              # 产出 @([string[]](pid, ere, note), ...)
    param([Parameter(Mandatory)][string]$Path, [switch]$SkipHeader)
    foreach ($r in (Get-Tsv $Path)) {
        $p = Fld $r 0
        if ($p -cmatch '^#' -or $p -ceq '' -or $p -ceq 'pattern_id') { continue }
        if ($SkipHeader -and $p -ceq 'pattern_id') { continue }
        , $r } }

# ── 前后缀剥离（bash ${v#*:} / ${v%:*} / ${v##*:}——分隔符不存在时回原值）──
function Remove-GsPrefix1 { param([string]$V, [string]$Sep) # ${V#*sep}：剥到首个 sep（含）
    $i = $V.IndexOf($Sep); if ($i -lt 0) { $V } else { $V.Substring($i + $Sep.Length) } }
function Remove-GsSuffix1 { param([string]$V, [string]$Sep) # ${V%sep*}：剥末个 sep（含）
    $i = $V.LastIndexOf($Sep); if ($i -lt 0) { $V } else { $V.Substring(0, $i) } }
function Remove-GsPrefixL { param([string]$V, [string]$Sep) # ${V##*sep}
    $i = $V.LastIndexOf($Sep); if ($i -lt 0) { $V } else { $V.Substring($i + $Sep.Length) } }
function Remove-GsSuffixP { param([string]$V, [string]$Sep) # ${V%%sep*}
    $i = $V.IndexOf($Sep); if ($i -lt 0) { $V } else { $V.Substring(0, $i) } }

# ── bash read 语义（IFS=$'\t'）：TAB 串折叠、空字段吞并、首尾 TAB 剥离；尾参取余部原样 ──
function Get-BashRead {                      # 返回 @(c1..cN, rest)；rest=第 N+1 定界符后的原始余部
    param([string]$Line, [int]$N)
    $l = ($Line -creplace '^\t+', '') -creplace '\t+$', ''   # bash read：首尾 IFS-TAB 均剥离
    $res = [System.Collections.Generic.List[string]]::new()
    for ($i = 0; $i -lt $N; $i++) {
        $m = [regex]::Match($l, '\t+')
        if (-not $m.Success) { $res.Add($l); $l = ''; continue }
        $res.Add($l.Substring(0, $m.Index))
        $l = $l.Substring($m.Index + $m.Length) }
    $res.Add(($l -creplace '^\t+', ''))
    , $res.ToArray() }

# ── loc → 文件名后缀段（C-001：F-id 的 loc 机械派生，5a/2dc/3g 三处逐字节同式）──
function Get-GsFex { param([string]$Loc)
    if ($null -eq $Loc -or $Loc -ceq '') { return '' }
    $lfile = Remove-GsSuffix1 $Loc ':'
    $lline = Remove-GsPrefixL $Loc ':'
    $fb = Get-GsStem (Get-GsBaseName $lfile)                                   # basename 去扩展
    if ($lline -cmatch '^[0-9]+$') { '-' + $fb + '-L' + $lline } else { '-' + $fb } }

# ── basename/无扩展名（basename；${b%.*}——无点回原值）──
function Get-GsBaseName { param([string]$P) if ($P) { [System.IO.Path]::GetFileName($P) } else { '' } }
function Get-GsStem { param([string]$B) $i = $B.LastIndexOf('.'); if ($i -le 0) { $B } else { $B.Substring(0, $i) } }

# ── 零填充（printf '%05d'——非数字前缀剥到数字部分按 0 计，bash $((10#x)) 同口径）──
function ConvertTo-GsNum {                # $((10#$v))：剥非数字；空/纯非数字=0
    param([string]$V)
    if ($null -eq $V) { return 0 }
    $m = [regex]::Match($V, '[0-9]+'); if (-not $m.Success) { 0 } else { [int64]$m.Value } }
function Format-Gs05 { param([string]$V) '{0:d5}' -f (ConvertTo-GsNum $V) }
function Format-Gs04 { param([string]$V) '{0:d4}' -f (ConvertTo-GsNum $V) }

# ── 转义/还原（3a esc 与 I9 unesc 同源——C-058 账本文本契约）──
function ConvertTo-GsEsc { param([string]$S)   # \ → \\，TAB → \t（逐行无 \n 场景）
    if ($null -eq $S) { return '' }
    $S.Replace('\', '\\').Replace("`t", '\t') }
function ConvertFrom-GsEsc { param([string]$S) # \\ → \，\t → TAB，\n → LF（与 esc 反演同式）
    if ($null -eq $S) { return '' }
    $S.Replace('\\', [string][char]1).Replace('\t', "`t").Replace('\n', "`n").Replace([string][char]1, '\') }

# ── tee / tee -a（stdout + 落盘同发）──
function Out-GsTee { param([string]$Path, [string]$Line)
    Out-Lf $Line; Add-LfContent $Path @($Line) }

# ── 数值比较（bash [ a -gt b ] 的安全形态：非数字按 0）──
function TestGt { param([string]$A, [string]$B) (ConvertTo-GsNum $A) -gt (ConvertTo-GsNum $B) }
function TestLt { param([string]$A, [string]$B) (ConvertTo-GsNum $A) -lt (ConvertTo-GsNum $B) }
function TestGe { param([string]$A, [string]$B) (ConvertTo-GsNum $A) -ge (ConvertTo-GsNum $B) }
function TestLe { param([string]$A, [string]$B) (ConvertTo-GsNum $A) -le (ConvertTo-GsNum $B) }

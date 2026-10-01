<!-- 引用件：纯 Windows 宿主（无 bash）经 SKILL.md「平台分支」进入本件发起会话；bash 可用的宿主走 SKILL.md 的 bash 发起块，不读本件。本件不引用其他引用件。 -->

# Windows (pwsh) 发起

参数与 bash 侧相同（`{source_path}`/`{skill_dir}`/`{output_dir}`/`{advisory_path}`/`{runtime_verification}`/`{width}`/`{batch}`，编排器执行前替换占位符）。
本件产出与 bash 发起块逐字节等价的会话骨架：会话目录、STATE/SOURCE/SKILL_DIR、feedback 头、以及 `env.ps1`（每节命令块首行 `. "$S/env.ps1"` 加载；PS 变量不跨命令存活，与 bash 侧 env.sh 同一纪律）。

```powershell
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }
$SRC = '{source_path}'
$SK = '{skill_dir}'
$OUT = '{output_dir}'
$ADVISORY = '{advisory_path}'
$RUNTIMEV = '{runtime_verification}'
$WIDTH = '{width}'
if ($WIDTH -cnotmatch '^[1-9][0-9]*$') { $WIDTH = 4 }                   # D3' 缺省 4（非正整数回落；8 卡上限删）
$BATCH = '{batch}'
if ($BATCH -cnotmatch '^[1-9][0-9]*$') { $BATCH = 3 }                   # D1-L3 批轮缺省 3（N 轮一收口——防自停）
if ($OUT -ceq '') { $OUT = Join-Path $HOME 'gensift-sessions' }
. (Join-Path $SK 'phases/lib.ps1')    # 公共底座必须先于任何底座函数调用（New-GsDir/Get-LfLines/…）加载
New-GsDir $OUT
# 断点续跑：仅复用「未完成 且 源码路径相同」的 session（不同目标不得串会话）
$S = ''
$cands = @(Get-ChildItem -LiteralPath $OUT -Directory -Filter 'gensift-*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | ForEach-Object { $_.FullName })
foreach ($d in $cands) {
    if (-not (Test-GsFile (Join-Path $d 'STATE'))) { continue }
    if (@(Get-LfLines (Join-Path $d 'STATE')) | Where-Object { $_.Contains('done') }) { continue }
    if (-not (Test-GsFile (Join-Path $d 'SOURCE'))) { continue }
    if ((@(Get-LfLines (Join-Path $d 'SOURCE')) -join '') -cne $SRC) { continue }
    $S = $d; break }
if ($S -ceq '') {
    $S = Join-Path $OUT ("gensift-{0}-$PID" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    foreach ($sub in @('inventories', 'shards/enum', 'findings', 'audit', 'recon', 'tmp', 'feedback')) { New-GsDir (Join-Path $S $sub) }
    Set-LfContent (Join-Path $S 'STATE') @('running')
    Set-LfContent (Join-Path $S 'SOURCE') @($SRC)
    Set-LfContent (Join-Path $S 'SKILL_DIR') @($SK) }
# 续跑会话恢复 SK（宿主重启后不依赖记忆）
if (Test-GsFile (Join-Path $S 'SKILL_DIR')) { $SK = (@(Get-LfLines (Join-Path $S 'SKILL_DIR')) -join '') }
foreach ($sub in @('inventories', 'shards/enum', 'findings', 'audit', 'recon', 'tmp', 'feedback')) { New-GsDir (Join-Path $S $sub) }
# 本 run 处置库（§10.2——读全局写本 run 批后合并；A4 落行协议见 phases/terminal.ps1 的 A4 节）
if (-not (Test-GsFile (Join-Path $S 'feedback/dispositions.tsv'))) {
    Set-LfContent (Join-Path $S 'feedback/dispositions.tsv') @('fingerprint' + "`t" + 'disposition' + "`t" + 'reason' + "`t" + 'scope' + "`t" + 'source' + "`t" + 'date' + "`t" + 'review_expiry' + "`t" + 'run_origin') }
# 会话环境持久化：后续每节命令块首行 `. "$S/env.ps1"` 加载（每节是新 pwsh 调用，变量不跨节存活）
$envQ = { param($v) "'" + [string]$v.Replace("'", "''") + "'" }
$envLines = [System.Collections.Generic.List[string]]::new()      # 注意：@("a"+x, "b"+y) 里 + 优先于逗号会被串接成单元素——逐行 Add
$envLines.Add("`$S   = " + (& $envQ $S))
$envLines.Add("`$SK  = " + (& $envQ $SK))
$envLines.Add("`$SRC = " + (& $envQ $SRC))
$envLines.Add("`$OUT = " + (& $envQ $OUT))
$envLines.Add("`$ADVISORY = " + (& $envQ $ADVISORY))
$envLines.Add("`$RUNTIMEV = " + (& $envQ $RUNTIMEV))
$envLines.Add("`$WIDTH = " + (& $envQ $WIDTH))
$envLines.Add("`$BATCH = " + (& $envQ $BATCH))
$envLines.Add(". (Join-Path `$SK 'phases/lib.ps1')")
Set-LfContent (Join-Path $S 'env.ps1') $envLines
Out-Lf "SESSION=$S"
```

**【每节必读】后续所有命令节的第一行都是 `. "$S/env.ps1"`——`$S` 用上方 `SESSION=` 输出的字面路径代入。没有这一行，该节所有变量为空、命令写向错误路径。**

## 阶段索引（与 bash 侧同构——命令块逐节取 phases/*.ps1 同名标题节执行）

- **阶段 0 测绘与枚举** → 读 `phases/phase0.ps1`，顺序执行 `# ===== 0.0 =====` 至 `# ===== 0.8 =====` 各节（0.0 门失败 exit 3 同 bash）
- **主循环** → 读 `phases/main-loop.ps1`，按轮执行 step0–step6 各节（2b/2e-env/2f-env/3e-env 的 `{card_id}`/`{cand_id}`/`{FT-id}` 占位符按所在节说明代入后执行）
- **L2 发散** → 读 `phases/l2.ps1`（l2frontier / l2div / l2inv 三节）
- **拼链与合并** → 读 `phases/joins.ps1`（J1 / J2 / J3 三节）
- **终态** → 读 `phases/terminal.ps1`（inv / G2 / G3 / calibration / report / metrics / mermaid / desensitize / A4 九节）
- 派发 prompt 模板仍读 phases/*.md 同名块下方的模板段（模板是给子代理的文本，不是命令块，两侧共用）

如果 `$S/checks.tsv` 已存在且 `$S/STATE` 为 running，跳到【主循环】（phases/main-loop.ps1）。
角色/纪律/红线/交付物清单同 SKILL.md（单一事实源，本件不复述）。

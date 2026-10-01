<!-- 引用件：由入口 SKILL.md「阶段索引」进入，一次性顺序执行完 0.0–0.8 后进主循环。命令块逐字复制执行；本件不引用其他引用件。 -->

## 阶段 0：测绘与枚举

### 0.0 pattern-lint + I1 fixture 快速门（枚举前常驻——B-079/D-065/D-068/D-069/C-Inv01）

```bash
. "$S/env.sh"
# I1 门（会话内口径）三件事，失败即终态 exit 3——未验证知识禁止进枚举（B-079）：
#   ① 全量 pattern 语法检：每条 ERE 喂 grep -E（exit 2=语法坏）+ 禁用构造 lint（\[bwdDWsS] 与 \(?——
#      knowledge-spec/pattern-file-schema.md §3 方言白名单，只扫 ERE 列）
#   ② fixtures pos/neg 抽样 20%（确定性：类文件内数据行第 1、6、11…条）：抽样条 pos 零命中=死 pattern
#      不上线（D-069①）、neg 命中=过宽打回（D-069②）——门输出逐 pattern 命中归因行（D-068）
#   ③ guards 转录规则段级检查（A-074/A-075）：五段文件在册+结构锚（三跳/来源）；某段缺失只降级该段
#      （SEG-DEGRADED 留档、该段发卡记 unknown）不拦门——段间独立（段级噪音降级的门内形态）
# 黄金夹具双件对（POSIX/PS）在 dev 侧 gensift-dev/commands/golden——会话内不重跑（语料归属+成本），
# 全量门归 dev golden/smoke（D-041 的 PS 侧=任务10.2）；无 fixture 目录的类如实披露不豁免后续补齐义务
# D-090 schema 单源投影检查：TERM/VERDICT 行格式以 agents/*.md 为单一事实源，main-loop 解析处引用同一
# 格式串——两处文本漂移即门红（不靠记忆同步）
GFAIL=0
: > "$S/audit/i1-gate.md"
echo "# I1 pattern-lint + fixture 抽样门（枚举前——$(date '+%F %T')）" >> "$S/audit/i1-gate.md"
NSYN=0; NLINT=0; NDEAD=0; NWIDE=0; NSAMP=0; NUNC=0
for patf in "$SK"/classes/patterns/*.pattern; do
  [ -f "$patf" ] || continue
  base=$(basename "$patf" .pattern); CLASS=${base%-*}; PLANG=${base##*-}
  [ -f "$SK/langpacks/$PLANG/includes.txt" ] || continue
  INC=()
  while IFS= read -r g; do case "$g" in ''|'#'*) continue ;; esac; INC+=(--include="$g"); done < "$SK/langpacks/$PLANG/includes.txt"
  FIXD="$SK/fixtures/enum/$CLASS/$PLANG"
  i=0
  # 头部健壮解析：# version:/append-only: 头行不漂移数据行（B-204/B-115 加头后 NR 计数不再依赖）
  while IFS=$'\t' read -r pid ere note; do
    case "$pid" in ''|'#'*|pattern_id) continue ;; esac
    [ -n "$ere" ] || continue
    i=$((i+1))
    grep -E -e "$ere" /dev/null >/dev/null 2>&1; grc=$?
    if [ "$grc" -eq 2 ]; then
      echo "SYNTAX-FAIL	$base	$pid	ERE 语法坏" >> "$S/audit/i1-gate.md"; NSYN=$((NSYN+1)); GFAIL=1; continue
    fi
    if printf '%s' "$ere" | grep -qE '\\[bwdWsS]|\(\?'; then
      echo "LINT-FAIL	$base	$pid	禁用构造（schema §3）" >> "$S/audit/i1-gate.md"; NLINT=$((NLINT+1)); GFAIL=1; continue
    fi
    [ $(( (i-1) % 5 )) -eq 0 ] || continue
    [ ${#INC[@]} -gt 0 ] || continue
    if [ ! -d "$FIXD/pos" ]; then NUNC=$((NUNC+1)); continue; fi
    NSAMP=$((NSAMP+1))
    if ! grep -rlE "${INC[@]}" -e "$ere" "$FIXD/pos" 2>/dev/null | grep -q .; then
      echo "DEAD	$base	$pid	抽样 pos 零命中（死 pattern 不上线——D-069①）" >> "$S/audit/i1-gate.md"; NDEAD=$((NDEAD+1)); GFAIL=1
    fi
    if [ -d "$FIXD/neg" ] && grep -rlE "${INC[@]}" -e "$ere" "$FIXD/neg" 2>/dev/null | grep -q .; then
      echo "WIDE	$base	$pid	抽样 neg 命中（过宽打回——D-069②）" >> "$S/audit/i1-gate.md"; NWIDE=$((NWIDE+1)); GFAIL=1
    fi
  done < <(awk -F'\t' '$1!~/^#/ && $1!="" && $1!="pattern_id"' "$patf")
done
echo "## guards 转录规则段级检查（A-074/A-075——段间独立：段缺失只降级该段，不拦门）" >> "$S/audit/i1-gate.md"
for langd in "$SK"/langpacks/*/; do
  lang=$(basename "$langd")
  for seg in authn authz csrf upload-check rate-limit; do
    gf="$langd/guards-$seg.md"
    if [ ! -f "$gf" ]; then
      echo "SEG-DEGRADED	$lang	$seg	文件缺失（该段降级——发卡时该段记 unknown）" >> "$S/audit/i1-gate.md"; continue
    fi
    miss=""
    grep -q '三跳' "$gf" 2>/dev/null || miss="$miss 三跳"
    grep -q '来源' "$gf" 2>/dev/null || miss="$miss 来源"
    [ -z "$miss" ] && echo "SEG-OK	$lang	$seg	段级锚齐" >> "$S/audit/i1-gate.md" \
      || echo "SEG-DEGRADED	$lang	$seg	缺锚:${miss}（该段降级）" >> "$S/audit/i1-gate.md"
  done
done
# D-090 schema 单源投影检查：agents 单源格式串在 main-loop 解析处逐字节复现
grep -qF 'TERM:{state}<TAB>{reason}<TAB>{facts_used}' "$SK/agents/analyzer.md" \
  && grep -qF 'TERM:{state}<TAB>{reason}<TAB>{facts_used}' "$SK/phases/main-loop.md" || { echo "SCHEMA-DRIFT	TERM 格式单源漂移（analyzer.md ↔ main-loop 3c）" >> "$S/audit/i1-gate.md"; GFAIL=1; }
grep -qF 'VERDICT:{三态|dismissed}<TAB>{severity}<TAB>{cvss}<TAB>{tier}' "$SK/agents/verifier.md" \
  && grep -qF 'VERDICT:{三态|dismissed}<TAB>{severity}<TAB>{cvss}<TAB>{tier}' "$SK/phases/main-loop.md" || { echo "SCHEMA-DRIFT	VERDICT 格式单源漂移（verifier.md ↔ main-loop 5a）" >> "$S/audit/i1-gate.md"; GFAIL=1; }
echo "统计: 语法坏=$NSYN lint坏=$NLINT 死pattern=$NDEAD 过宽=$NWIDE 抽样=$NSAMP 无fixture披露=$NUNC（D-067 neg 档位核对表见 gensift-dev/registers/calibration.md）" >> "$S/audit/i1-gate.md"
if [ "$GFAIL" -eq 1 ]; then
  echo "❌ I1 门 FAIL——未验证知识禁止进枚举（B-079；exit 3=门未过，v1.4.0-S14）" | tee -a "$S/audit/i1-gate.md"
  exit 3
fi
echo "I1 门: PASS（抽样 20% 快速门；全量门=dev golden/smoke——D-041；PS 双件对=任务10.2）" | tee -a "$S/audit/i1-gate.md"
```

### 0.1 派 Recon 子代理

派一个子代理（可写通用子代理），prompt：
```
读取 {SK}/agents/recon.md 并严格遵守。源码根：{SRC}。
产出写入 {S}/recon/ 目录。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行。
```

### 0.2 枚举 file 清单

```bash
. "$S/env.sh"
# 后缀全部来自 langpacks/*/includes.txt（语言包可插拔：加语言=加目录，协议零改动）；config 载体是跨语言协议常量
# role 标注（B-152/A-065）：test/vendor/demo/docs 入清单不剔除，只免 term 卡；generated（A-067）同
# refreeze 前置归档（A-049）：既有冻结的会话重跑枚举=显式重测绘——覆盖前先把【旧】三清单归档（G3 归因数据源），
# 归档目录路径落 audit/refreeze.pending，由 0.6b 消费（哈希未变时删归档防宿主重试幻影）
if [ -f "$S/inventories/frozen.sha256" ] && [ ! -f "$S/audit/refreeze.pending" ]; then
  ts=$(date +%Y%m%d-%H%M%S)-$$
  mkdir -p "$S/audit/refreeze/pre-$ts"
  cp "$S/inventories/"*.tsv "$S/audit/refreeze/pre-$ts/" 2>/dev/null
  printf '%s\n' "$S/audit/refreeze/pre-$ts" > "$S/audit/refreeze.pending"
fi
GL=()
for incf in "$SK"/langpacks/*/includes.txt; do
  [ -f "$incf" ] || continue
  while IFS= read -r g; do
    case "$g" in ''|'#'*) continue ;; esac
    GL+=("$g")
  done < "$incf"
done
for g in '*.yml' '*.yaml' '*.jinja2' '*.xml'; do GL+=("$g"); done
FA=(); first=1
for g in "${GL[@]}"; do
  [ $first -eq 0 ] && FA+=(-o)
  FA+=(-name "$g"); first=0
done
find "$SRC" -type f \( "${FA[@]}" \) -not -path '*/.git/*' | LC_ALL=C sort > "$S/tmp/raw-files-abs.txt"
sed "s|^$SRC/||" "$S/tmp/raw-files-abs.txt" > "$S/shards/enum/raw-files.tsv"
for incf in "$SK"/langpacks/*/includes.txt; do
  [ -f "$incf" ] || continue
  lang=$(basename "$(dirname "$incf")")
  while IFS= read -r g; do
    case "$g" in ''|'#'*) continue ;; esac
    printf '%s=%s\n' "${g#*.}" "$lang"
  done < "$incf"
done > "$S/tmp/sufmap.tsv"
{ printf "seq\tpath\tlang\tloc\tmodule\trole\n"
  n=0
  while IFS= read -r abs; do
    rel=${abs#"$SRC"/}
    suffix="${rel##*.}"
    lang=$(awk -F'=' -v s="$suffix" 's==$1{print $2; exit}' "$S/tmp/sufmap.tsv")
    [ -n "$lang" ] || lang=config
    role=app
    case "/$rel" in
      */test/*|*/tests/*|*/__tests__/*) role=test ;;
      */vendor/*|*/node_modules/*|*/third_party/*) role=vendor ;;
      */example/*|*/examples/*|*/demo/*|*/demos/*|*/samples/*) role=demo ;;
      */docs/*|*/doc/*) role=docs ;;
    esac
    [ "$role" = app ] && [ "$lang" = config ] && role=config
    loc=$(wc -l < "$abs" | tr -d ' ')
    if [ "$role" = app ] || [ "$role" = config ]; then
      over=$(awk 'length($0)>2048{c++} END{print c+0}' "$abs")
      if [ "$loc" -gt 0 ] && [ $((over*2)) -gt "$loc" ]; then
        # generated 判定附核查（A-068）：树内存在同名非压缩源（x.min.ext→x.ext）则审计源，不标 generated
        d=${rel%/*}; b=${rel##*/}; stem=${b%.*}; ext=${b##*.}; sib=""
        case "$stem" in *.min) sib="$d/${stem%.min}.$ext" ;; esac
        if [ -z "$sib" ] || [ ! -f "$SRC/$sib" ]; then role=generated; fi
      fi
    fi
    n=$((n+1))
    printf 'FILE-%05d\t%s\t%s\t%s\t-\t%s\n' "$n" "$rel" "$lang" "$loc" "$role"
  done < "$S/tmp/raw-files-abs.txt"
} > "$S/inventories/file_inventory.tsv"
```

### 0.2b module 回填

```bash
. "$S/env.sh"
# recon/modules.md 末节 `## module-map`（行格式 file<TAB>module，相对路径）join 回 file_inventory.module（B-151）。
# F1 来源标记（审查修复轮）：语义模块一律带 `mod:` 前缀入列；机械目录回填带 `dir:`——
# 三个语义消费方（L2 INV×module / J1 拼链门 / 组合件门）只认 `mod:`，`dir:` 只是数据补全不是模块判定
if [ -f "$S/recon/modules.md" ] && awk -F'\t' '/^## module-map/{f=1;next} f && NF>=2 && $1!~/^#/{n++} END{exit !(n>0)}' "$S/recon/modules.md"; then
  awk -F'\t' '/^## module-map/{f=1;next} f && NF>=2 && $1!~/^#/ {print $1"\t"$2}' "$S/recon/modules.md" > "$S/tmp/module-map.tsv"
  awk -F'\t' 'NR==FNR{m[$1]=$2; next} BEGIN{OFS="\t"} {if(FNR>1 && ($2 in m)) $5="mod:" m[$2]; print}' \
    "$S/tmp/module-map.tsv" "$S/inventories/file_inventory.tsv" > "$S/tmp/fi.tmp" && mv "$S/tmp/fi.tmp" "$S/inventories/file_inventory.tsv"
  echo "module 回填: $(awk -F'\t' 'NR>1 && $5 ~ /^mod:/' "$S/inventories/file_inventory.tsv" | wc -l | tr -d ' ') 行（mod: 语义标记）"
else
  echo "module 回填: recon/modules.md 无 module-map 节（module 列保持 '-'——coverage 披露）"
fi
# D4-B③ module 回填补全（P2 冷启动：aiohttp 首跑 46/142 半覆盖不可接受——mod 信号与 coverage 模块计数全饿死）：
# recon join 后仍 '-' 的行机械回填**顶层目录**（`dir:` 前缀——机械推导非知识注入，不参与语义模块判定）。
# F1 死角目录：role∈{test,vendor,demo,docs,generated} 的文件**不回填保持 '-'**——它们是角色不是模块
# （否则 tests/ 也会领 INV 卡、J1/组合件门被目录数虚撑——与 D4-A test 降权目标背反）；
# centrality 的 mod +10 对 mod:/dir: 都加（近似常数平移，如实披露——判别力由 D4-B①② 概率信号承担）
LEFT=$(awk -F'\t' 'NR>1 && ($5=="-"||$5=="") && $6!~/^(test|vendor|demo|docs|generated)$/{n++} END{print n+0}' "$S/inventories/file_inventory.tsv")
DEAD=$(awk -F'\t' 'NR>1 && ($5=="-"||$5=="") && $6~/^(test|vendor|demo|docs|generated)$/{n++} END{print n+0}' "$S/inventories/file_inventory.tsv")
if [ "$LEFT" -gt 0 ] || [ "$DEAD" -gt 0 ]; then
  awk -F'\t' 'BEGIN{OFS="\t"} FNR==1{print; next}
    ($5=="-"||$5=="") && $6!~/^(test|vendor|demo|docs|generated)$/ {
      d=$2; sub(/^\.\//,"",d); $5="dir:" ((index(d,"/")>0)?substr(d,1,index(d,"/")-1):"root") }
    {print}' "$S/inventories/file_inventory.tsv" > "$S/tmp/fi.mod" && mv "$S/tmp/fi.mod" "$S/inventories/file_inventory.tsv"
  echo "module 补全: dir: 机械回填 $LEFT 行（顶层目录约定）｜角色死角不回填 $DEAD 行（test/vendor/demo/docs/generated 保持 '-'——不是模块）"
fi
```

### 0.3 枚举 sink 清单

```bash
. "$S/env.sh"
for patf in "$SK"/classes/patterns/*.pattern; do
  [ -f "$patf" ] || continue
  base=$(basename "$patf" .pattern)
  CLASS=${base%-*}; PLANG=${base##*-}
  # 后缀来自语言包（协议零语言假设——无 includes.txt 的语言跳过该 pattern）
  [ -f "$SK/langpacks/$PLANG/includes.txt" ] || continue
  INC=()
  while IFS= read -r g; do
    case "$g" in ''|'#'*) continue ;; esac
    INC+=(--include="$g")
  done < "$SK/langpacks/$PLANG/includes.txt"
  # includes.txt 只有注释时 INC 为空——空 --include 会全树扫（性能爆炸+域外垃圾 sink），跳过
  [ ${#INC[@]} -gt 0 ] || continue
  # band 从 pattern 文件头读取——单一事实源（硬编码表会与文件头漂移）
  B=$(awk -F': *' '/^# band:/{gsub(/[ \t\r]/,"",$2); print $2; exit}' "$patf")
  case "$B" in 0|1|2) ;; *) B=1 ;; esac
  while IFS=$'\t' read -r pid ere note; do
    [ -z "$pid" ] && continue
    grep -rnE "${INC[@]}" -e "$ere" "$SRC" 2>/dev/null | \
      awk -v cls="$CLASS" -v pid="$pid" -v bd="$B" -F: '{print $1"\t"$2"\t"cls"\t"pid"\t"bd}'
  done < <(awk -F'\t' '$1!~/^#/ && $1!="" && $1!="pattern_id"' "$patf")
done | sed "s|$SRC/||" | LC_ALL=C sort > "$S/shards/enum/raw-sinks.tsv"
awk -F'\t' '{
    # 去重口径 per (class, file, line)——同一行命中多类时每类各一张卡，禁止吞卡
    key=$3":"$1":"$2
    if(!(key in seen)){ seen[key]=$4; n++; printf "SINK-%05d\tFILE-\t%s:%s\t%s\t%s\t%s\n",n,$1,$2,$3,$4,$5 }
    else { seen[key]=seen[key]","$4 }
  }
  END{ for(k in seen) if(seen[k]~/,/) print "MULTI\t"k"\t"seen[k] > "/dev/stderr" }' \
  "$S/shards/enum/raw-sinks.tsv" > "$S/tmp/sink_data.tsv"
# file_seq 回填（B-162）：关联 file_inventory seq；清单外路径落 '-'（sink grep 的 includes 超出 file 清单时）
awk -F'\t' 'NR==FNR{ if(FNR>1) seq[$2]=$1; next }
  { f="-"; split($3,lf,":"); if(lf[1] in seq) f=seq[lf[1]]; print $1"\t"f"\t"$3"\t"$4"\t"$5"\t"$6 }' \
  "$S/inventories/file_inventory.tsv" "$S/tmp/sink_data.tsv" > "$S/tmp/sink_inv.tsv"
{ printf "seq\tfile_seq\tloc\tclass_id\tapi\tband\n"; cat "$S/tmp/sink_inv.tsv"; } > "$S/inventories/sink_inventory.tsv"
rm -f "$S/tmp/sink_data.tsv" "$S/tmp/sink_inv.tsv"
```

### 0.4 枚举 source 清单

```bash
. "$S/env.sh"
# 库/应用判定（recon/app-or-lib.md 首行 `verdict: app|lib`）——库模式 source 语义切换（A-077）：入口=公共 API 面/调用方传入点
MODE="app"
[ -f "$S/recon/app-or-lib.md" ] && MODE=$(awk -F': *' '$1=="verdict"{v=tolower($2); gsub(/[ \t\r]/,"",v); print v; exit}' "$S/recon/app-or-lib.md")
case "$MODE" in lib) MODE=lib ;; *) MODE=app ;; esac
: > "$S/shards/enum/raw-sources.tsv"
for langd in "$SK"/langpacks/*/; do
  lang=$(basename "$langd")
  patf="$langd/sources.pattern"
  [ "$MODE" = lib ] && [ -f "$langd/sources-lib.pattern" ] && patf="$langd/sources-lib.pattern"
  [ -f "$patf" ] || continue
  [ -f "$langd/includes.txt" ] || continue
  INC=()
  while IFS= read -r g; do case "$g" in ''|'#'*) continue ;; esac; INC+=(--include="$g"); done < "$langd/includes.txt"
  [ ${#INC[@]} -gt 0 ] || continue
  while IFS=$'\t' read -r pid ere note; do
    [ -z "$pid" ] && continue
    # entry_type 通道（B-156/A-082）：weak 入清单不预发卡；external_message=消息/事件消费者（auth=unknown）
    case "$note" in
      *band=weak*)        ET="weak" ;;
      *external_message*) ET="external_message" ;;
      *persisted_read*)   ET="persisted_read" ;;
      *) if [ "$MODE" = lib ]; then ET="lib_api"; else ET="http"; fi ;;
    esac
    grep -rnE "${INC[@]}" -e "$ere" "$SRC" 2>/dev/null | \
      awk -v pid="$pid" -v et="$ET" -F: '{print $1"\t"$2"\t"pid"\t"et}'
  done < <(awk -F'\t' 'NR>4 && $1!=""' "$patf")
  # persisted_read 通道（A-079/D-028）：万级弱回读点入清单不预发 fw 卡（demand-driven 见主循环 step1b）
  if [ -f "$langd/persisted.pattern" ]; then
    while IFS=$'\t' read -r pid ere note; do
      [ -z "$pid" ] && continue
      grep -rnE "${INC[@]}" -e "$ere" "$SRC" 2>/dev/null | \
        awk -v pid="$pid" -v et="persisted_read" -F: '{print $1"\t"$2"\t"pid"\t"et}'
    done < <(awk -F'\t' 'NR>4 && $1!=""' "$langd/persisted.pattern")
  fi
done | sed "s|$SRC/||" | LC_ALL=C sort -u > "$S/shards/enum/raw-sources.tsv"
# file_seq / framework 回填（B-154/B-157）：frameworks.tsv=pattern→框架单一事实源；persisted 通道缺省 orm
cat "$SK"/langpacks/*/frameworks.tsv 2>/dev/null | awk -F'\t' '$1!~/^#/ && NF>=2{print $1"\t"$2}' > "$S/tmp/fw-map.tsv"
awk -F'\t' '
  FILENAME==ARGV[1] { if(FNR>1) fs[$2]=$1; next }
  FILENAME==ARGV[2] { fw[$1]=$2; next }
  { n++; f="FILE-"; split($1,lf,":"); if(lf[1] in fs) f=fs[lf[1]]
    fr="unknown"; if($4=="persisted_read"){ fr=($3 in fw)?fw[$3]:"orm" } else if($3 in fw) fr=fw[$3]
    printf "SRC-%05d\t%s\t%s:%s\t%s\t%s\tunknown\tauthn:unknown|authz:unknown|csrf:unknown|upload-check:unknown|rate-limit:unknown\t-\n", n, f, $1, $2, $4, fr
  }' "$S/inventories/file_inventory.tsv" "$S/tmp/fw-map.tsv" "$S/shards/enum/raw-sources.tsv" > "$S/tmp/si_data.tsv"
{ printf "seq\tfile_seq\tloc\tentry_type\tframework\tauth\tguards\tfamily\n"; cat "$S/tmp/si_data.tsv"; } > "$S/inventories/source_inventory.tsv"
rm -f "$S/tmp/si_data.tsv"
echo "source 枚举: $(awk 'NR>1' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') 行（mode=$MODE）"
```

**guards 五段填充 + family 修正**（每语言派一个子代理，可并行；用可写文件的通用子代理执行，禁止其调用 skill 工具加载任何技能）：

```
读取 {SK}/langpacks/{lang}/guards-authn.md、guards-authz.md、guards-csrf.md、
guards-upload-check.md、guards-rate-limit.md 五份转录规则。
对 {S}/inventories/source_inventory.tsv 中每个入口，逐段从源码找对应事实，
把 guards 列（第 7 列）更新为五段拼接（找不到的段写 {seg}:unknown）：
authn:{来源}:{事实}@{file}:{line}|authz:...|csrf:...|upload-check:...|rate-limit:...
{事实}必须逐字转录源码行——冻结前会抽样 10% 与源码逐字比对，转述/概括会打回。
若第 8 列 family 机械键（前缀|方法|param_shape）与源码明显不符（如同文件路由前缀变体被误归一段），
可一并修正第 8 列，并把每条修正写一行到 {S}/shards/FAM-fix-{lang}.tsv
（格式：seq<TAB>旧值<TAB>新值<TAB>理由）——留 diff 是硬要求，无 diff 的改列非法。
只改第 7、8 列，不动其他列。完成后只返回一行。
```

子代理返回后验收（列数改坏则冻结/发卡全崩）：

```bash
. "$S/env.sh"
BADG=$(awk -F'\t' 'NR>1 && NF!=8' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')
echo "guards列坏行: $BADG（>0 → 让子代理修复重验；仍>0 → 终止报告）"
```

### 0.4b family 半机械键派生

```bash
. "$S/env.sh"
# family（B-160/A-076）= 路由前缀|方法|param_shape（路径参数形态归一化——IDOR 差分自然分组）
# 机械派生只读入口行本身；LLM 修正走 FAM-fix 分片（0.4c 合并留 diff）
[ -f "$S/audit/family-corrections.tsv" ] || printf "seq\told\tnew\treason\n" > "$S/audit/family-corrections.tsv"
awk -F'\t' -v src="$SRC" -v dfile="$S/tmp/family-derived.tsv" 'BEGIN{OFS="\t"; print "seq\tfamily" > dfile}
  FNR==1 { print; next }
  {
    f=""; ln=0; line=""
    split($3, a, ":"); f=a[1]; ln=a[2]+0
    if(f != ""){ cnt=0; while((getline line < (src "/" f)) > 0){ cnt++; if(cnt==ln) break; line="" } ; close(src "/" f) }
    pre="-"
    if(match(line, /"[^"]*"/)){ pre=substr(line,RSTART+1,RLENGTH-2); gsub(/\{[^}]*\}/,"{p}",pre); gsub(/[0-9]+/,"n",pre) }
    mth="-"
    if(match(line, /[A-Za-z_][A-Za-z0-9_]*[[:space:]]*\(/)){ mth=substr(line,RSTART,RLENGTH); gsub(/[[:space:]]+$/,"",mth); sub(/\($/,"",mth) }
    shape="-"
    if(match(line, /\([^)]*\)/)){
      shape=substr(line,RSTART,RLENGTH)
      gsub(/"[^"]*"/,"\"s\"",shape); gsub(/[A-Za-z_][A-Za-z0-9_.]*/,"a",shape); gsub(/[0-9]+/,"n",shape)
      gsub(/[[:space:]]+/,"",shape); if(length(shape)>48) shape=substr(shape,1,48)
    }
    $8 = pre "|" mth "|" shape
    print $0
    print $1 "\t" $8 > dfile
  }' "$S/inventories/source_inventory.tsv" > "$S/tmp/si.tmp" && mv "$S/tmp/si.tmp" "$S/inventories/source_inventory.tsv"
```

### 0.4c family 修正合并 + auth 回填

```bash
. "$S/env.sh"
# FAM-fix 分片合并（guards 子代理的 family 修正——逐条归档 diff，修正可追溯；按分片名记账防重复合并产幻影行）
MF="$S/audit/fam-merged.txt"; touch "$MF"
: > "$S/tmp/fam-app.tsv"
for ff in "$S"/shards/FAM-fix-*.tsv; do
  [ -f "$ff" ] || continue
  grep -qxF "$(basename "$ff")" "$MF" && continue
  awk -F'\t' '$1~/^SRC-/ && NF>=3{print $1"\t"$3}' "$ff" >> "$S/tmp/fam-app.tsv"
  awk -F'\t' '$1~/^SRC-/ && NF>=4' "$ff" >> "$S/audit/family-corrections.tsv"
  echo "$(basename "$ff")" >> "$MF"
done
if [ -s "$S/tmp/fam-app.tsv" ]; then
  awk -F'\t' 'NR==FNR{fx[$1]=$2; next} BEGIN{OFS="\t"} {if($1 in fx) $8=fx[$1]; print}' \
    "$S/tmp/fam-app.tsv" "$S/inventories/source_inventory.tsv" > "$S/tmp/si.tmp" && mv "$S/tmp/si.tmp" "$S/inventories/source_inventory.tsv"
fi
# auth 回填（B-158）：按 guards authn 段机械三值化 unauth/auth/unknown（有防护记录=auth；来源空=unauth；未查明=unknown）
awk -F'\t' 'BEGIN{OFS="\t"}
  FNR==1{ print; next }
  { auth="unknown"; g=$7
    if(g ~ /^authn:unknown/){ auth="unknown" }
    else if(g ~ /^authn:/){
      seg=substr(g,7); pos=index(seg,":"); srcf=(pos>0)?substr(seg,1,pos-1):seg
      auth=(srcf=="")?"unauth":"auth"
    }
    $6=auth; print
  }' "$S/inventories/source_inventory.tsv" > "$S/tmp/si.tmp" && mv "$S/tmp/si.tmp" "$S/inventories/source_inventory.tsv"
echo "auth 分布: auth=$(awk -F'\t' 'NR>1 && $6=="auth"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') / unauth=$(awk -F'\t' 'NR>1 && $6=="unauth"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') / unknown=$(awk -F'\t' 'NR>1 && $6=="unknown"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')"
```

### 0.5 G1 锚点预检

```bash
. "$S/env.sh"
# G1（C-011/A-087/A-089）：锚点输入=用户 advisory 清单（发起参数 {advisory_path}→$ADVISORY，每行 CVE-ID<TAB>file:line）
# 有锚点时位置必须 ⊆ 三清单——不过不开跑；锚点同时注入 candidates 种子行（A-086）
echo "G1: $(date '+%F %T')" > "$S/audit/g1.md"
if [ -n "$ADVISORY" ] && [ -f "$ADVISORY" ]; then
  echo "锚点来源: 用户advisory（$ADVISORY）" >> "$S/audit/g1.md"
  [ -f "$S/candidates.tsv" ] || printf "cand_id\tcard_id\tsink_seq\tsource_seq\tclass_id\tloc\tverdict_state\tdelivery_state\tsummary\n" > "$S/candidates.tsv"
  n=$(awk -F'\t' '$1~/^CD-SEED-/{t=substr($1,9)+0; if(t>m)m=t} END{print m+0}' "$S/candidates.tsv")
  MISS=0
  while IFS=$'\t' read -r cve loc; do
    case "$cve" in ''|'#'*) continue ;; esac
    [ -n "$loc" ] || continue
    f=${loc%:*}
    hit=$(awk -F'\t' -v f="$f" 'NR>1 && $2==f{print "in:file_inventory"; exit}' "$S/inventories/file_inventory.tsv" 2>/dev/null)
    [ -n "$hit" ] || hit=$(awk -F'\t' -v f="$f" 'NR>1 && index($3,f":")==1{print "in:source_inventory"; exit}' "$S/inventories/source_inventory.tsv" 2>/dev/null)
    [ -n "$hit" ] || hit=$(awk -F'\t' -v f="$f" 'NR>1 && index($3,f":")==1{print "in:sink_inventory"; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
    [ -n "$hit" ] || { hit="MISS"; MISS=$((MISS+1)); }
    printf '%s\t%s\t%s\n' "$cve" "$loc" "$hit" >> "$S/audit/g1.md"
    # CVE/advisory 种子行（A-086）：仅对清单内锚点注入，保持 open 直到本地证据独立支持/证伪——邻近 finding 不替代闭合
    if [ "$hit" != "MISS" ] && ! awk -F'\t' -v l="$loc" '$2=="G1" && $6==l{f=1} END{exit !f}' "$S/candidates.tsv"; then
      n=$((n+1)); printf 'CD-SEED-%05d\tG1\t\t\tseed\t%s\topen\tpending\t\n' "$n" "$loc" >> "$S/candidates.tsv"
    fi
  done < "$ADVISORY"
  if [ "$MISS" -gt 0 ]; then
    echo "❌ G1 FAIL: $MISS 个锚点不在清单内——不过不开跑（终止并报告，退出码 3=门未过——v1.4.0-S14）" | tee -a "$S/audit/g1.md"
    exit 3
  fi
  echo "结果: PASS（种子行 $(awk -F'\t' '$2=="G1"' "$S/candidates.tsv" | wc -l | tr -d ' ') 条 state=open）" >> "$S/audit/g1.md"
else
  echo "锚点来源: 无" >> "$S/audit/g1.md"
  echo "结果: N/A（本目标无机械召回下界——coverage.md 披露）" >> "$S/audit/g1.md"
fi
```

### 0.5b guards/family 冻结前抽样比对

```bash
. "$S/env.sh"
# A-090：guards/family 列 G1 前抽样 10% 与源码逐字比对——封印后无法修，差异行交 guards 子代理修复后重验
{
  echo "## guards/family 抽样比对（每 10 行抽 1，冻结前）"
  awk -F'\t' -v SRC="$SRC" '
    FNR==1{ next }
    (FNR%10)==2 {
      ng=split($7,segs,"|")
      for(i=1;i<=ng;i++){ s=segs[i]
        if(!match(s, /@[^@]*:[0-9]+$/)) continue
        tail=substr(s,RSTART+1,RLENGTH-1); ln=tail; sub(/.*:/,"",ln)
        fl=substr(tail,1,length(tail)-length(ln)-1)
        rest=substr(s,1,RSTART-1); sub(/^[a-z-]+:/,"",rest)
        pos=index(rest,":"); fact=(pos>0)?substr(rest,pos+1):""
        if(fact=="" || fact=="-") continue
        line=""; cnt=0
        while((getline line < (SRC"/"fl)) > 0){ cnt++; if(cnt==ln) break; line="" } ; close(SRC"/"fl)
        if(line!=fact) printf "GUARD-DIFF\t%s\t%s\t%s:%s\n",$1,s,fl,ln
      }
    }' "$S/inventories/source_inventory.tsv"
  awk -F'\t' '
    FILENAME==ARGV[1]{ if(FNR>1) d[$1]=$2; next }
    FILENAME==ARGV[2]{ c[$1]=1; next }
    FNR==1{ next }
    (FNR%10)==2 && $8!="-" && $8!=d[$1] && !($1 in c){ printf "FAM-DIFF\t%s\t机械=%s\t现值=%s\n",$1,d[$1],$8 }
  ' "$S/tmp/family-derived.tsv" "$S/audit/family-corrections.tsv" "$S/inventories/source_inventory.tsv"
  echo "（GUARD-DIFF/FAM-DIFF 行>0 → 让 guards 子代理修复后重验再冻结；封印后无法修）"
} >> "$S/audit/g1.md"
```

### 0.5c I19 枚举对账

```bash
. "$S/env.sh"
# I19（C-Inv19/A-085）：清单行数 == 原始枚举输出行数，三向对账；差异逐行解释留档
{
  echo "# I19 枚举对账（清单行数 == 原始枚举输出；差异逐行留档）"
  echo "## file"
  raw=$(wc -l < "$S/shards/enum/raw-files.tsv" | tr -d ' ')
  inv=$(awk 'NR>1' "$S/inventories/file_inventory.tsv" | wc -l | tr -d ' ')
  echo "raw=$raw inv=$inv diff=$((raw-inv))"
  comm -3 <(LC_ALL=C sort "$S/shards/enum/raw-files.tsv" | tr -d '\r') \
          <(awk -F'\t' 'NR>1{print $2}' "$S/inventories/file_inventory.tsv" | LC_ALL=C sort | tr -d '\r') | sed 's/^/	/'
  echo "## sink"
  raw=$(awk -F'\t' '{print $3":"$1":"$2}' "$S/shards/enum/raw-sinks.tsv" | LC_ALL=C sort -u | wc -l | tr -d ' ')
  rawall=$(wc -l < "$S/shards/enum/raw-sinks.tsv" | tr -d ' ')
  inv=$(awk 'NR>1' "$S/inventories/sink_inventory.tsv" | wc -l | tr -d ' ')
  echo "raw=$raw inv=$inv diff=$((raw-inv))（raw=去重键计数，与 0.3 同键；原始命中 $rawall 行中同行同类多次命中被 0.3 合并——MULTI 警告见 0.3 stderr）"
  comm -3 <(awk -F'\t' '{print $3":"$1":"$2}' "$S/shards/enum/raw-sinks.tsv" | LC_ALL=C sort -u | tr -d '\r') \
          <(awk -F'\t' 'NR>1{split($3,a,":"); print $4":"a[1]":"a[2]}' "$S/inventories/sink_inventory.tsv" | LC_ALL=C sort -u | tr -d '\r') | sed 's/^/	/'
  echo "## source"
  raw=$(wc -l < "$S/shards/enum/raw-sources.tsv" | tr -d ' ')
  inv=$(awk 'NR>1' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')
  echo "raw=$raw inv=$inv diff=$((raw-inv))"
  comm -3 <(awk -F'\t' '{print $1":"$2"\t"$4}' "$S/shards/enum/raw-sources.tsv" | LC_ALL=C sort -u | tr -d '\r') \
          <(awk -F'\t' 'NR>1{split($3,a,":"); print a[1]":"a[2]"\t"$4}' "$S/inventories/source_inventory.tsv" | LC_ALL=C sort -u | tr -d '\r') | sed 's/^/	/'
} > "$S/audit/i19.md"
```

### 0.6 冻结

```bash
. "$S/env.sh"
(cd "$S/inventories" && $HASH file_inventory.tsv source_inventory.tsv sink_inventory.tsv > frozen.sha256)
```

### 0.6b refreeze 显式通道

```bash
. "$S/env.sh"
# refreeze（A-049/A-058）：仅当用户显式要求重测绘时执行——旧清单已在 0.2 重测绘前归档（audit/refreeze/pre-*，见 pending 戳），
# 本块做哈希比对 + 留痕（G3 差异归因数据源）；ext 卡不触发 refreeze（两本账分开：分母扩充走本块，追加卡走 ext 账）
if [ -f "$S/inventories/frozen.sha256" ]; then
  NEWHASH=$(cd "$S/inventories" && $HASH file_inventory.tsv source_inventory.tsv sink_inventory.tsv)
  PEND=$(cat "$S/audit/refreeze.pending" 2>/dev/null)
  if [ "$NEWHASH" = "$(cat "$S/inventories/frozen.sha256")" ]; then
    # 清单未变：重测绘前的归档是宿主重试幻影——删除并消戳，不留痕（幂等）
    [ -n "$PEND" ] && [ -d "$PEND" ] && rm -rf "$PEND"
    rm -f "$S/audit/refreeze.pending"
    echo "refreeze: 清单未变（哈希一致）——不归档不留痕（幂等）"
  else
    { echo "refreeze at $(date '+%F %T') reason={用户显式要求} 旧清单归档=${PEND:-（无——清单在冻结前已被外部改动）}"
      echo "old:"; cat "$S/inventories/frozen.sha256"; echo "new:"; printf '%s\n' "$NEWHASH"
    } >> "$S/audit/refreeze.log"
    printf '%s\n' "$NEWHASH" > "$S/inventories/frozen.sha256"
    rm -f "$S/audit/refreeze.pending"
    # F1：refreeze 后 0.7 将发新分母卡（origin_ref 空、unchecked）——step0 L1 单调性若不刷新基线，
    # 合法新增会被判违例（refreeze 主场景自拦死）。基线须在 0.7 发卡后按 step0 同口径重算——此处挂戳传递。
    touch "$S/audit/refreeze-baseline.pending"
  fi
else
  echo "refreeze: 无既有冻结（首次冻结走 0.6；本块只处理显式重测绘）"
fi
```

### 0.7 发卡

```bash
. "$S/env.sh"
# 发卡口径：term 只发 role∈{app,config}（A-065——test/vendor/demo/docs/generated 入清单不发 term 卡；I3 对账口径同此）
# fw 发 http+external_message（weak/persisted_read 不预发——persisted 走主循环 step1b demand-driven）
# bw 全量（secrets 例外：test/vendor 路径的 sink 照发 bw 卡——测试文件里的真实密钥是生产风险）
# 先排序卡体，再补表头（直接 sort 全文会把表头沉底，首卡对 NR>1 永久不可见）
# 幂等：checks.tsv 已存在时只增量补发新清单实体的卡（refreeze 后的新分母），严禁重建抹掉既有卡状态
{ awk -F'\t' 'NR>1{print "CK-bw-"sprintf("%05d",NR-1)"\tbw\t"$1"\t\tunchecked\t\t\t0\tr1"}' "$S/inventories/sink_inventory.tsv"
  awk -F'\t' 'NR>1 && ($4=="http"||$4=="external_message"){print "CK-fw-"substr($1,5)"\tfw\t"$1"\t\tunchecked\t\t\t0\tr1"}' "$S/inventories/source_inventory.tsv"
  awk -F'\t' 'NR>1 && ($6=="app"||$6=="config"){print "CK-term-"substr($1,6)"\tterm\t"$1"\t\tunchecked\t\t\t0\tr1"}' "$S/inventories/file_inventory.tsv"
} | LC_ALL=C sort > "$S/tmp/ck.body"
if [ -s "$S/checks.tsv" ]; then
  NEWC=$(awk -F'\t' 'NR==FNR{seen[$1]=1; next} !($1 in seen)' "$S/checks.tsv" "$S/tmp/ck.body" | wc -l | tr -d ' ')
  awk -F'\t' 'NR==FNR{seen[$1]=1; next} !($1 in seen)' "$S/checks.tsv" "$S/tmp/ck.body" >> "$S/checks.tsv"
  echo "发卡（增量）: 新增 $NEWC 张（既有卡状态不动）"
else
  { printf "card_id\tkind\tref_seq\torigin_ref\tstate\treason\tfacts_used\tattempt\trevision\n"
    cat "$S/tmp/ck.body"; } > "$S/checks.tsv"
fi
rm -f "$S/tmp/ck.body"
# F1：refreeze 基线重置——0.6b 挂戳、本块发卡（增量或首建）完成后，按 step0 同口径
# （非 ext 且 origin_ref 空的 unchecked 数）重算并覆写 last_unchecked 基线，refreeze.log 留痕 N→M；
# 新分母卡是显式重测绘的合法产物，不是 L1 违例。无戳（首次冻结/非 refreeze 流程）不动作。
if [ -f "$S/audit/refreeze-baseline.pending" ]; then
  OLDU=$(cat "$S/audit/last_unchecked" 2>/dev/null || echo "?")
  CURU=$(awk -F'\t' 'NR>1 && $2!="ext" && $4=="" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  echo "$CURU" > "$S/audit/last_unchecked"
  echo "基线已重置 ${OLDU}→${CURU}（refreeze 发卡后按 step0 同口径重算——新分母卡不是违例）" >> "$S/audit/refreeze.log"
  rm -f "$S/audit/refreeze-baseline.pending"
fi
```

### 0.7b guards/family 差分与三跳抽样（B-080/B-081/B-082/A-072——0.7 发卡后、0.8 前）

```bash
. "$S/env.sh"
# B 轨差分（A-072 family 差分参照系——0.4b 机械键 + 0.4c 修正后在此收口）：
#   B-081 同 family 输入源一致性：族内 authn 来源段唯一；>1 来源 → GUARD-FAM-DIFF 留档
#   B-080 离群检测发差分卡：族内 guards 五段 ≠ 族众数的成员 → ext 卡 CK-ext-GD-{seq}（origin_ref=SRC-seq，
#     幂等不重发）——差分是"该看哪里"不是结论，终态裁决仍走五步
#   B-082 全一致族抽样 1 入口（确定性：众数成员中最小 seq）做 guard 绑定有效性三跳核查（下方派发模板）
awk -F'\t' 'NR>1 && $8!="-" && $8!=""{ print $8"\t"$1"\t"$7 }' "$S/inventories/source_inventory.tsv" > "$S/tmp/fam-rows.tsv"
awk -F'\t' '
  { key=$1"\t"$3; gc[key]++; g7[$2]=$3; fam[$1]=1; mem[$1]=mem[$1] $2 "\n" }
  END{
    for(f in fam){
      best=""; bestn=0
      for(k in gc){ split(k,a,"\t"); if(a[1]==f && gc[k]>bestn){ bestn=gc[k]; best=a[2] } }
      n=split(mem[f],m,"\n"); first=""
      for(i=1;i<=n;i++){ id=m[i]; if(id=="") continue
        if(g7[id]!=best) print "OUTLIER\t"id"\t"f
        else if(first=="") first=id
      }
      if(first!="") print "SAMPLE\t"first"\t"f
    }
  }' "$S/tmp/fam-rows.tsv" | LC_ALL=C sort > "$S/tmp/gd-out.tsv"
{ echo "# guards/family 差分（B-080/B-081）+ 三跳抽样（B-082）——$(date '+%F %T')"
  while IFS=$'\t' read -r tag seq fam; do
    [ -n "$seq" ] || continue
    case "$tag" in
      OUTLIER)
        cid="CK-ext-GD-${seq#SRC-}"
        if ! awk -F'\t' -v c="$cid" '$1==c{f=1} END{exit !f}' "$S/checks.tsv" 2>/dev/null; then
          printf '%s\text\t%s\t%s\tunchecked\t\t\t0\tr1\n' "$cid" "$seq" "$seq" >> "$S/checks.tsv"
        fi
        echo "GUARD-DIFF	$seq	family=$f	guards 与族众数不同——差分卡 $cid 已发（裁决走五步，不预判）"
        ;;
      SAMPLE)
        echo "BIND-SAMPLE	$seq	family=$f 全一致——抽样三跳核查（下方派发；结果入 audit/guard-bind-review.log）"
        awk -F'\t' -v s="$seq" '$1==s{print "  入口信封："s"｜loc="$3"｜guards 五段="$7; exit}' "$S/inventories/source_inventory.tsv"
        ;;
    esac
  done < "$S/tmp/gd-out.tsv"
} > "$S/audit/guard-family-diff.md"
# GB 分片收卡（B-082 三跳核查结果——幂等记账，unbound 只披露不翻账）
[ -f "$S/audit/gb-merged.txt" ] || : > "$S/audit/gb-merged.txt"
for gf in "$S"/shards/GB-*.tsv; do
  [ -f "$gf" ] || continue
  seq=$(basename "$gf" .tsv); seq=${seq#GB-}
  grep -qxF "GB-$seq" "$S/audit/gb-merged.txt" && continue
  rline=$(grep '^REVIEW:' "$gf" | head -1)
  rv=$(printf '%s\n' "$rline" | cut -f1 | sed 's/^REVIEW://')
  case "$rv" in bound|unbound) ;; *) continue ;; esac
  printf 'GB	%s	%s	%s\n' "$seq" "$rv" "$(date '+%F %T')" >> "$S/audit/guard-bind-review.log"
  echo "GB-$seq" >> "$S/audit/gb-merged.txt"
done
BS=$(grep -c '^BIND-SAMPLE' "$S/audit/guard-family-diff.md" 2>/dev/null); : "${BS:=0}"   # 守卫形态：缺文件时空串显示→0（任务11 终审B P2 同族，顺手同修；ps1 侧同为 0）
echo "0.7b 差分: OUTLIER 卡 $(awk -F'\t' '$1~/^CK-ext-GD-/' "$S/checks.tsv" | wc -l | tr -d ' ') 张 ｜ 一致族抽样 ${BS} 族 ｜ 三跳已复核 $( (wc -l < "$S/audit/guard-bind-review.log" 2>/dev/null || echo 0) | tr -d ' ') 条（audit/guard-family-diff.md）"
```

对 `audit/guard-family-diff.md` 的每条 BIND-SAMPLE 行（{seq} 用实际值代入；信封行取该文件「入口信封：」行）派一个复核 Verifier（可写通用子代理，同消息并行；固定前缀+尾部变量块——A-107）：

```
你是 GenSift 复核 Verifier（guard 绑定三跳核查——B-082）。读取 {SK}/agents/verifier.md 并严格遵守（分片名按本 prompt：GB-{seq}.tsv）。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：分片路径 + 行数 + REVIEW 结论。
——以上固定前缀（A-107）——
{入口信封行}｜源码根：{SRC}
任务：三跳核查 guard 绑定有效性——①guard 代码位置真实存在且生效（信封 @file:line 实读）；②guard 绑定到该入口的注册链（中间件/拦截器/过滤器/路由注册处实读）；③guard 输入源（来源字段）非请求可写。三跳各 ≥1 行 SELF。
写分片到 {S}/shards/GB-{seq}.tsv，格式：
SELF:{file}:{line}<TAB>{全文}
REVIEW:bound|unbound<TAB>{理由}
```

### 0.8 启动预估（W1——A-007/C-019：时长区间含无级联下界 + token 投影 + 参数出处 + 签字项）

```bash
. "$S/env.sh"
TOTAL=$(awk -F'\t' 'NR>1' "$S/checks.tsv" | wc -l | tr -d ' ')
B0=$(awk -F'\t' 'NR>1 && $6=="0"' "$S/inventories/sink_inventory.tsv" | wc -l | tr -d ' ')
B1=$(awk -F'\t' 'NR>1 && $6=="1"' "$S/inventories/sink_inventory.tsv" | wc -l | tr -d ' ')
B2=$(awk -F'\t' 'NR>1 && $6=="2"' "$S/inventories/sink_inventory.tsv" | wc -l | tr -d ' ')
# 参数出处（D-102 调度校准同口径）：下列常量全部为经验区间，出处=README「首次运行检查单/预期」
# 节的实测口径 + R3-R5 回放观察，不是精调值——首轮完成后以 progress_board 实测每轮时延回填校准
PC_LO=90      # 单卡时延下界（秒）：子代理读码+写分片最快形态（并发口径同 step1 宽度）
PC_HI=900     # 单卡时延上界（秒）：大文件/多跳五步追踪最慢形态（README「千文件级过夜」口径折算）
WID="${WIDTH:-4}"   # 每轮派发宽度：D3' 缺省 4，发起参数 width=N 经 env.sh 贯通（与 step1 head -"$WIDTH" 同源）
TK_LO=20000   # 每子代理 token 下界：信封+读码+分片输出的最省形态
TK_HI=80000   # 每子代理 token 上界：长上下文读码+逐行引文转录形态（README「成本量级」节）
ROUNDSE=$(( (TOTAL + WID - 1) / WID ))
TLO=$(( ROUNDSE * PC_LO / 60 )); THI=$(( ROUNDSE * PC_HI / 60 ))
TKLO=$(( ROUNDSE * WID * TK_LO / 1000 )); TKHI=$(( ROUNDSE * (WID + 3) * TK_HI / 1000 ))
cat > "$S/run-estimate.md" << EOF
# 启动预估（W1——C-019/A-007）
- 总卡数: $TOTAL（bw $(awk -F'\t' 'NR>1 && $2=="bw"' "$S/checks.tsv" | wc -l | tr -d ' ') / fw $(awk -F'\t' 'NR>1 && $2=="fw"' "$S/checks.tsv" | wc -l | tr -d ' ') / term $(awk -F'\t' 'NR>1 && $2=="term"' "$S/checks.tsv" | wc -l | tr -d ' ')）
- 分带统计: band0 $B0 ｜ band1 $B1 ｜ band2 $B2
- 预计轮次: $ROUNDSE（每轮宽度 $WID 张——出处同 step1 派发宽度变量，D3' 发起参数 width=N 可调）
- 时长区间（含无级联下界）: ${TLO}–${THI} 分钟——下界按「零 K 级联收益」计（不假设 K 规则消卡，级联只会让实际更短）；单卡时延 ${PC_LO}–${PC_HI}s × 轮次
- token 投影: ${TKLO}k–${TKHI}k token（轮数 × 每轮 ${WID}–$((WID + 3)) 子代理（宽度+fw/term/ext 保底 3）× 每子代理 ${TK_LO}–${TK_HI} token 量级）
- 参数出处: PC_LO/PC_HI/WID/TK_LO/TK_HI 见 phases/phase0.md 0.8 块内注释（README 实测口径+回放观察；局限：宿主并发与模型速度差异可达 2×，首轮后回填）
- 预估签字: □ 编排器确认上述投影与参数出处（实测每轮时延超 ${THI} 分钟 ×2 时 5c NOTICE 机械披露——C-020 联动）
EOF
```
